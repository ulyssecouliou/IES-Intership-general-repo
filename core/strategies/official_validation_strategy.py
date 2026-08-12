"""Validation officielle : confrontation aux classeurs d'évaluation du SIA.

C'est la seule stratégie qui fasse autorité, et elle refuse de conclure tant
que le classeur officiel du test n'est pas présent. Un verdict rendu sans lui
n'aurait aucune valeur devant la sous-commission.

Exemple:
    >>> from core.repositories import SIA4010Repository
    >>> depot = SIA4010Repository("data/sia4010_official")
    >>> OfficialValidationStrategy(depot).validate("test_7", {}).status.value
    'NOT_CHECKABLE'
"""

from __future__ import annotations

from typing import Any, Mapping

from core.repositories.sia4010_repository import (
    OfficialFileMissingError,
    SIA4010Repository,
)
from core.strategies.validation_strategy import ValidationStrategy
from schemas.test_result_schema import TestResult, TestStatus

#: Origine du critère. Voir la réserve `criterion_is_inferred` ci-dessous.
CRITERION_SOURCE = (
    "SIA 4010:2023 §4.4 — la comparaison aux résultats de référence est "
    "déléguée au classeur d'évaluation officiel du test."
)

#: Tests dont la spécification énonce ses critères dans une section
#: « Testkriterien ». Pour les autres, le critère est déduit de la présence de
#: bandes dans le classeur : il est marqué comme inféré.
#:
#: Ce jeu ne contenait que `test_1`, sur la croyance que le Test 1 était le seul
#: dans ce cas. C'est faux : la recherche plein texte du 2026-08-12 trouve la
#: section dans `Spezifikation_Test2.pdf` (p. 2/2), `Test3.pdf` (p. 3/3) et
#: `Test5.pdf` (p. 5/5), chacune énonçant la bande annuelle et le critère de
#: distribution. Elle est absente des specs des Tests 4, 6 et 7.
#:
#: L'erreur n'était pas cosmétique : ce jeu pilote `criterion_is_inferred` dans
#: la voie autoritative, donc trois tests annonçaient un critère déduit alors
#: que la spécification l'écrit — une preuve affaiblie sans raison, exactement
#: ce qui se défend mal devant la sous-commission. Le statut équivalent côté
#: moteur est `sia_bandes_engine.CRITERE_PAR_TEST`, tenu indépendamment et
#: confronté par `engine/tests/test_references_bandes.py`.
TESTS_WITH_WRITTEN_CRITERION = frozenset(
    {"test_1", "test_2", "test_3", "test_5"}
)


class OfficialValidationStrategy(ValidationStrategy):
    """Validation contre les classeurs d'évaluation officiels du SIA."""

    name = "official"
    is_authoritative = True

    def __init__(self, repository: SIA4010Repository) -> None:
        """Construit la stratégie autour du dépôt de fichiers officiels.

        Args:
            repository: Dépôt donnant accès aux classeurs SIA.
        """
        self._repository = repository

    def validate(self, test_id: str, context: Any) -> TestResult:
        """Confronte les grandeurs candidates aux bandes du classeur officiel.

        Args:
            test_id: Alias du test, ex. « test_7 ».
            context: Mapping ``{libellé de grandeur: valeur}`` produit par
                l'adaptateur IESVE. Un mapping vide signifie « pas encore
                simulé » et donne `NOT_CHECKABLE`, jamais un succès.

        Returns:
            TestResult: Résultat du test.
        """
        inferre = test_id not in TESTS_WITH_WRITTEN_CRITERION
        try:
            self._repository.require_evaluation(test_id)
        except OfficialFileMissingError as erreur:
            return self.build_result(
                test_id=test_id,
                status=TestStatus.NOT_CHECKABLE,
                criterion_source=CRITERION_SOURCE,
                errors=(str(erreur),),
                criterion_is_inferred=inferre,
            )

        if not _valeurs_candidates(context):
            return self.build_result(
                test_id=test_id,
                status=TestStatus.NOT_CHECKABLE,
                criterion_source=CRITERION_SOURCE,
                errors=("aucune valeur candidate : le test n'a pas été simulé",),
                criterion_is_inferred=inferre,
            )

        raise NotImplementedError(
            "la comparaison aux bandes du classeur %s n'est pas encore branchée "
            "sur cette stratégie. Le moteur qui la réalise existe déjà "
            "(engine/test7_engine.py et engine/scatter_band.py du dépôt "
            "SIA_Compliance_Scripts) ; l'y raccorder est une tâche de câblage, "
            "pas de réimplémentation." % test_id
        )


def _valeurs_candidates(context: Any) -> Mapping[str, float]:
    """Extrait le mapping de valeurs candidates d'un contexte quelconque.

    Args:
        context: Contexte fourni à la stratégie.

    Returns:
        Mapping[str, float]: Valeurs candidates, vide si le contexte n'en
        contient pas.
    """
    if isinstance(context, Mapping):
        return context
    return {}
