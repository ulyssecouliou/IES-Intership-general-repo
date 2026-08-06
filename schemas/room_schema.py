"""Modèle d'un local conditionné, agrégat de surfaces et d'ouvertures."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

from schemas.opening_schema import Opening
from schemas.surface_schema import Surface

VolumeM3 = Annotated[float, Field(gt=0.0, description="Volume net en m3, > 0.")]


class Room(BaseModel):
    """Local du modèle IESVE.

    L'usage est une chaîne libre et NON un énuméré : les codes de SIA 2024:2021
    (« 4.04 Hörsaal », « 3.01 Einzel-, Gruppenbüro ») ne sont pas tous en notre
    possession, et figer une liste partielle rejetterait des usages valides.

    Attributes:
        id: Identifiant du local dans le modèle IESVE.
        volume: Volume net en m3, strictement positif.
        surfaces: Surfaces opaques délimitant le local.
        openings: Ouvertures pratiquées dans ces surfaces.
        usage: Code d'usage SIA 2024, par exemple « 4.04 ». `None` si inconnu.
        floor_area: Surface nette de plancher en m2, si le modèle la fournit.

    Example:
        >>> from schemas import Surface
        >>> mur = Surface(id="S1", area=10.0, u_value=0.2)
        >>> Room(id="R1", volume=25.0, surfaces=[mur]).opaque_area
        10.0
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1, description="Identifiant IESVE du local.")
    volume: VolumeM3
    surfaces: tuple[Surface, ...] = Field(
        default=(), description="Surfaces opaques du local."
    )
    openings: tuple[Opening, ...] = Field(default=(), description="Ouvertures du local.")
    usage: str | None = Field(
        default=None, description="Code d'usage SIA 2024, ex. « 4.04 »."
    )
    floor_area: float | None = Field(
        default=None, gt=0.0, description="Surface nette de plancher en m2."
    )

    @model_validator(mode="after")
    def _identifiants_uniques(self) -> "Room":
        """Vérifie l'unicité des identifiants de surfaces et d'ouvertures.

        Un doublon d'identifiant fait disparaître silencieusement une surface
        lors de tout regroupement par clé ; mieux vaut le refuser à la lecture.

        Returns:
            Room: Le local validé, inchangé.

        Raises:
            ValueError: Si un identifiant de surface ou d'ouverture est répété.
        """
        _refuser_doublons([s.id for s in self.surfaces], "surface")
        _refuser_doublons([o.id for o in self.openings], "ouverture")
        return self

    @property
    def opaque_area(self) -> float:
        """Somme des aires des surfaces opaques, en m2.

        Returns:
            float: Aire opaque totale, 0.0 si le local n'a aucune surface.
        """
        return sum(surface.area for surface in self.surfaces)

    @property
    def opening_area(self) -> float:
        """Somme des aires des ouvertures, en m2.

        Returns:
            float: Aire d'ouverture totale, 0.0 si le local n'en a aucune.
        """
        return sum(opening.area for opening in self.openings)

    @property
    def external_surfaces(self) -> tuple[Surface, ...]:
        """Surfaces en contact avec l'extérieur.

        Returns:
            tuple[Surface, ...]: Sous-ensemble des surfaces externes.
        """
        return tuple(s for s in self.surfaces if s.is_external)


def _refuser_doublons(identifiants: list[str], nature: str) -> None:
    """Lève si la liste d'identifiants contient un doublon.

    Args:
        identifiants: Identifiants à contrôler.
        nature: Mot employé dans le message d'erreur, ex. « surface ».

    Raises:
        ValueError: Si au moins un identifiant apparaît plusieurs fois.
    """
    vus: set[str] = set()
    doublons: set[str] = set()
    for identifiant in identifiants:
        if identifiant in vus:
            doublons.add(identifiant)
        vus.add(identifiant)
    if doublons:
        raise ValueError(
            "identifiant(s) de %s en doublon : %s" % (nature, ", ".join(sorted(doublons)))
        )
