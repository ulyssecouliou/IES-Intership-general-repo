"""Accès aux fichiers officiels SIA 4010 (spécifications, classeurs, données).

Ce dépôt ne fabrique jamais un chemin plausible : si un fichier officiel
manque, il lève une erreur qui NOMME le fichier attendu et rappelle où
l'obtenir. Un dossier de validation construit sur un fichier deviné serait
invalidé par la sous-commission, et bien plus tard.

Exemple:
    >>> depot = SIA4010Repository(racine="data/sia4010_official")
    >>> depot.available_tests()          # doctest: +SKIP
    ('test_1', 'test_7')
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

#: Sous-dossier attendu pour un test donné, relatif à la racine officielle.
TEST_DIR_TEMPLATE = "test_{numero}"

#: Noms de fichiers attendus dans chaque dossier de test.
SPECIFICATION_FILENAME = "specification.pdf"
EVALUATION_FILENAME = "evaluation.xlsx"

#: Page d'où proviennent les fichiers, citée dans les messages d'erreur.
SIA_DOWNLOAD_PAGE = "https://www.sia.ch/sia4010"


class OfficialFileMissingError(FileNotFoundError):
    """Levée quand un fichier officiel SIA requis est absent du dépôt."""


@dataclass(frozen=True)
class TestAssets:
    """Fichiers officiels rattachés à un test SIA 4010.

    Attributes:
        test_id: Alias du test, ex. « test_1 ».
        specification: Chemin de la spécification PDF, `None` si absente.
        evaluation: Chemin du classeur d'évaluation, `None` si absent.
        extras: Autres fichiers présents dans le dossier du test.
    """

    test_id: str
    specification: Path | None
    evaluation: Path | None
    extras: tuple[Path, ...] = ()

    @property
    def is_complete(self) -> bool:
        """Indique si la spécification ET le classeur sont présents.

        Returns:
            bool: Vrai si les deux fichiers attendus existent.
        """
        return self.specification is not None and self.evaluation is not None


class SIA4010Repository:
    """Dépôt des fichiers officiels SIA 4010.

    Attributes:
        root: Racine du dossier des fichiers officiels.
    """

    def __init__(self, racine: Path | str) -> None:
        """Construit le dépôt autour d'une racine.

        Args:
            racine: Dossier contenant les sous-dossiers ``test_N``. Il n'a pas
                besoin d'exister : son absence sera signalée à la lecture,
                avec un message actionnable.
        """
        self.root = Path(racine)

    def test_dir(self, test_id: str) -> Path:
        """Chemin du dossier d'un test.

        Args:
            test_id: Alias du test, ex. « test_1 » ou « 1 ».

        Returns:
            Path: Chemin du dossier, existant ou non.
        """
        numero = test_id.removeprefix("test_")
        return self.root / TEST_DIR_TEMPLATE.format(numero=numero)

    def available_tests(self) -> tuple[str, ...]:
        """Alias des tests dont le dossier existe.

        Returns:
            tuple[str, ...]: Alias triés, vide si la racine n'existe pas.
        """
        if not self.root.is_dir():
            return ()
        trouves = (
            chemin.name
            for chemin in self.root.iterdir()
            if chemin.is_dir() and chemin.name.startswith("test_")
        )
        return tuple(sorted(trouves))

    def get_assets(self, test_id: str) -> TestAssets:
        """Inventorie les fichiers officiels d'un test, sans exiger leur présence.

        Args:
            test_id: Alias du test, ex. « test_7 ».

        Returns:
            TestAssets: Inventaire, avec `None` pour les fichiers absents.
        """
        dossier = self.test_dir(test_id)
        if not dossier.is_dir():
            return TestAssets(test_id=test_id, specification=None, evaluation=None)
        specification = dossier / SPECIFICATION_FILENAME
        evaluation = dossier / EVALUATION_FILENAME
        attendus = {specification, evaluation}
        extras = tuple(
            sorted(c for c in dossier.iterdir() if c.is_file() and c not in attendus)
        )
        return TestAssets(
            test_id=test_id,
            specification=specification if specification.is_file() else None,
            evaluation=evaluation if evaluation.is_file() else None,
            extras=extras,
        )

    def require_specification(self, test_id: str) -> Path:
        """Chemin de la spécification d'un test, ou erreur explicite.

        Args:
            test_id: Alias du test.

        Returns:
            Path: Chemin de la spécification.

        Raises:
            OfficialFileMissingError: Si la spécification est absente.
        """
        assets = self.get_assets(test_id)
        if assets.specification is None:
            raise self._absence(test_id, SPECIFICATION_FILENAME)
        return assets.specification

    def require_evaluation(self, test_id: str) -> Path:
        """Chemin du classeur d'évaluation d'un test, ou erreur explicite.

        Args:
            test_id: Alias du test.

        Returns:
            Path: Chemin du classeur.

        Raises:
            OfficialFileMissingError: Si le classeur est absent.
        """
        assets = self.get_assets(test_id)
        if assets.evaluation is None:
            raise self._absence(test_id, EVALUATION_FILENAME)
        return assets.evaluation

    def _absence(self, test_id: str, nom_fichier: str) -> OfficialFileMissingError:
        """Construit une erreur d'absence nommant le fichier et sa provenance.

        Args:
            test_id: Alias du test concerné.
            nom_fichier: Nom du fichier attendu.

        Returns:
            OfficialFileMissingError: Erreur prête à être levée.
        """
        return OfficialFileMissingError(
            "fichier officiel absent : %s\n"
            "Ce fichier ne peut pas être reconstitué ni approché : il fait foi. "
            "Le télécharger depuis %s et le déposer sous ce nom exact."
            % (self.test_dir(test_id) / nom_fichier, SIA_DOWNLOAD_PAGE)
        )
