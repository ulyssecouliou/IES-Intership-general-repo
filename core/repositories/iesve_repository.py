"""Accès au modèle IESVE, derrière une interface stable et testable.

Deux implémentations partagent le même contrat :

* :class:`LiveIESVERepository` interroge un modèle VE ouvert. Elle n'importe
  ``iesve`` qu'à l'appel, jamais au chargement du module, afin que ce fichier
  reste importable en intégration continue.
* :class:`JsonIESVERepository` relit un instantané normalisé sur disque. C'est
  elle qui rend les checkers testables sans licence VE.

Exemple:
    >>> depot = JsonIESVERepository.from_mapping(
    ...     {"rooms": [{"id": "R1", "volume": 30.0}]})
    >>> depot.get_room("R1").volume
    30.0
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Mapping, Sequence

from pydantic import ValidationError

from schemas.room_schema import Room

#: Clé racine attendue dans un instantané JSON.
ROOMS_KEY = "rooms"


class RoomNotFoundError(KeyError):
    """Levée quand un local demandé n'existe pas dans la source."""


class IESVERepository(ABC):
    """Contrat d'accès aux locaux d'un modèle IESVE."""

    @abstractmethod
    def get_rooms(self) -> tuple[Room, ...]:
        """Retourne tous les locaux de la source.

        Returns:
            tuple[Room, ...]: Locaux validés, éventuellement vide.
        """

    def get_room(self, room_id: str) -> Room:
        """Retourne un local par son identifiant.

        Args:
            room_id: Identifiant du local recherché.

        Returns:
            Room: Le local correspondant.

        Raises:
            RoomNotFoundError: Si aucun local ne porte cet identifiant.
        """
        for local in self.get_rooms():
            if local.id == room_id:
                return local
        raise RoomNotFoundError(
            "aucun local d'identifiant %r ; disponibles : %s"
            % (room_id, ", ".join(sorted(r.id for r in self.get_rooms())) or "(aucun)")
        )

    def get_rooms_by_usage(self, usage: str) -> tuple[Room, ...]:
        """Retourne les locaux portant un code d'usage donné.

        Args:
            usage: Code d'usage SIA 2024, par exemple « 4.04 ».

        Returns:
            tuple[Room, ...]: Locaux correspondants, éventuellement vide.
        """
        return tuple(local for local in self.get_rooms() if local.usage == usage)

    def total_volume(self) -> float:
        """Somme des volumes de tous les locaux, en m3.

        Returns:
            float: Volume total, 0.0 si la source est vide.
        """
        return sum(local.volume for local in self.get_rooms())


class JsonIESVERepository(IESVERepository):
    """Dépôt lisant un instantané JSON normalisé.

    Attributes:
        rooms: Locaux déjà validés au moment de la construction.
    """

    def __init__(self, rooms: Sequence[Room]) -> None:
        """Construit le dépôt à partir de locaux déjà validés.

        Args:
            rooms: Locaux à exposer.
        """
        self._rooms: tuple[Room, ...] = tuple(rooms)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "JsonIESVERepository":
        """Construit le dépôt depuis un dictionnaire déjà chargé.

        Args:
            payload: Dictionnaire contenant la clé ``rooms``.

        Returns:
            JsonIESVERepository: Dépôt prêt à l'emploi.

        Raises:
            ValueError: Si la clé ``rooms`` manque ou si un local est invalide.
        """
        if ROOMS_KEY not in payload:
            raise ValueError("instantané sans clé %r" % ROOMS_KEY)
        try:
            locaux = [Room.model_validate(brut) for brut in payload[ROOMS_KEY]]
        except ValidationError as erreur:
            raise ValueError("local invalide dans l'instantané : %s" % erreur) from erreur
        return cls(locaux)

    @classmethod
    def from_path(cls, chemin: Path | str) -> "JsonIESVERepository":
        """Construit le dépôt depuis un fichier JSON.

        Args:
            chemin: Chemin de l'instantané.

        Returns:
            JsonIESVERepository: Dépôt prêt à l'emploi.

        Raises:
            FileNotFoundError: Si le fichier n'existe pas.
            ValueError: Si le contenu n'est pas un instantané valide.
        """
        chemin_reel = Path(chemin)
        if not chemin_reel.is_file():
            raise FileNotFoundError("instantané introuvable : %s" % chemin_reel)
        return cls.from_mapping(json.loads(chemin_reel.read_text(encoding="utf-8")))

    def get_rooms(self) -> tuple[Room, ...]:
        """Retourne les locaux de l'instantané.

        Returns:
            tuple[Room, ...]: Locaux validés.
        """
        return self._rooms


class LiveIESVERepository(IESVERepository):
    """Dépôt interrogeant un modèle VE réellement ouvert.

    L'extraction concrète n'est PAS implémentée ici : la correspondance entre
    les attributs ``iesve`` et nos schémas doit être établie sur une VE réelle
    et vérifiée, pas devinée. La classe existe pour figer le contrat et le
    point d'extension.
    """

    def __init__(self, model: Any | None = None) -> None:
        """Construit le dépôt autour d'un modèle VE.

        Args:
            model: Objet modèle ``iesve`` déjà ouvert. Si `None`, il sera
                demandé à l'API au premier accès.
        """
        self._model = model

    def _ensure_model(self) -> Any:
        """Retourne le modèle VE, en l'ouvrant au besoin.

        Returns:
            Any: Le modèle VE courant.

        Raises:
            RuntimeError: Si le module ``iesve`` n'est pas disponible, c'est-à-
                dire hors d'une session VEScripts.
        """
        if self._model is not None:
            return self._model
        try:
            import iesve  # noqa: PLC0415 -- import différé : CI sans licence VE
        except ImportError as erreur:
            raise RuntimeError(
                "le module `iesve` est indisponible : ce dépôt ne fonctionne que "
                "dans une session VEScripts. Utiliser JsonIESVERepository hors VE."
            ) from erreur
        self._model = iesve.VEProject.get_current_project().models[0]
        return self._model

    def get_rooms(self) -> tuple[Room, ...]:
        """Retourne les locaux du modèle VE.

        Returns:
            tuple[Room, ...]: Locaux extraits et validés.

        Raises:
            NotImplementedError: Toujours, tant que la correspondance
                attribut ``iesve`` -> schéma n'a pas été établie sur une VE
                réelle. Renvoyer une liste vide ferait passer un modèle non lu
                pour un modèle sans locaux.
        """
        self._ensure_model()
        raise NotImplementedError(
            "correspondance attribut `iesve` -> schéma Room non encore établie. "
            "Elle doit être relevée sur une VE ouverte, puis figée avec sa "
            "source ; la deviner produirait des valeurs plausibles et fausses."
        )
