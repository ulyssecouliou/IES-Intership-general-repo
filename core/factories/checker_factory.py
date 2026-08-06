"""Fabrique de checkers et de stratégies, pour découpler l'appelant du concret.

Les checkers de ``swiss_sia`` sont importés **à la demande** : ils tirent
``config.py`` et ses dépendances, et un appelant qui ne veut qu'une stratégie
n'a pas à payer ce coût — ni à échouer si un checker est momentanément cassé.

Exemple:
    >>> CheckerFactory.available_strategies()
    ('official', 'pdf_prevalidation')
    >>> CheckerFactory.create_strategy("pdf_prevalidation").is_authoritative
    False
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, cast

from core.repositories.sia4010_repository import SIA4010Repository
from core.strategies.official_validation_strategy import OfficialValidationStrategy
from core.strategies.pdf_validation_strategy import PdfValidationStrategy
from core.strategies.validation_strategy import ValidationStrategy

#: Racine par défaut des fichiers officiels, relative à la racine du dépôt.
DEFAULT_OFFICIAL_ROOT = "data/sia4010_official"


class UnknownCheckerError(KeyError):
    """Levée quand un nom de checker ou de stratégie est inconnu."""


def _import_sia4010_checker() -> type:
    """Importe `SIA4010Checker` à la demande.

    Returns:
        type: La classe `swiss_sia.sia4010_checker.SIA4010Checker`.
    """
    from swiss_sia.sia4010_checker import SIA4010Checker  # noqa: PLC0415

    # `swiss_sia` est en follow_imports=skip (cf. pyproject) : mypy voit `Any`.
    return cast(type, SIA4010Checker)


def _import_sia3802_checker() -> type:
    """Importe `SIA3802Checker` à la demande.

    Returns:
        type: La classe `swiss_sia.sia380_checker.SIA3802Checker`.
    """
    from swiss_sia.sia380_checker import SIA3802Checker  # noqa: PLC0415

    return cast(type, SIA3802Checker)


#: Nom public -> importateur différé. Ajouter un checker ici, nulle part ailleurs.
CHECKER_IMPORTERS: dict[str, Callable[[], type]] = {
    "sia4010": _import_sia4010_checker,
    "sia3802": _import_sia3802_checker,
}


class CheckerFactory:
    """Instancie checkers et stratégies à partir de leur nom public."""

    @staticmethod
    def available_checkers() -> tuple[str, ...]:
        """Noms des checkers connus de la fabrique.

        Returns:
            tuple[str, ...]: Noms triés.
        """
        return tuple(sorted(CHECKER_IMPORTERS))

    @staticmethod
    def available_strategies() -> tuple[str, ...]:
        """Noms des stratégies connues de la fabrique.

        Returns:
            tuple[str, ...]: Noms triés.
        """
        return tuple(
            sorted({OfficialValidationStrategy.name, PdfValidationStrategy.name})
        )

    @staticmethod
    def create_checker(nom: str, *args: Any, **kwargs: Any) -> Any:
        """Instancie un checker par son nom public.

        Args:
            nom: Nom du checker, ex. « sia4010 ».
            *args: Arguments positionnels passés au constructeur.
            **kwargs: Arguments nommés passés au constructeur.

        Returns:
            Any: Instance du checker demandé.

        Raises:
            UnknownCheckerError: Si le nom est inconnu.
        """
        cle = nom.strip().lower()
        if cle not in CHECKER_IMPORTERS:
            raise UnknownCheckerError(
                "checker inconnu %r ; disponibles : %s"
                % (nom, ", ".join(CheckerFactory.available_checkers()))
            )
        return CHECKER_IMPORTERS[cle]()(*args, **kwargs)

    @staticmethod
    def create_strategy(
        nom: str, racine_officielle: Path | str | None = None
    ) -> ValidationStrategy:
        """Instancie une stratégie de validation par son nom public.

        Args:
            nom: « pdf_prevalidation » ou « official ».
            racine_officielle: Racine des fichiers SIA, utilisée par la
                stratégie officielle uniquement.

        Returns:
            ValidationStrategy: Stratégie prête à l'emploi.

        Raises:
            UnknownCheckerError: Si le nom est inconnu.
        """
        cle = nom.strip().lower()
        if cle == PdfValidationStrategy.name:
            return PdfValidationStrategy()
        if cle == OfficialValidationStrategy.name:
            racine = racine_officielle or DEFAULT_OFFICIAL_ROOT
            return OfficialValidationStrategy(SIA4010Repository(racine))
        raise UnknownCheckerError(
            "stratégie inconnue %r ; disponibles : %s"
            % (nom, ", ".join(CheckerFactory.available_strategies()))
        )
