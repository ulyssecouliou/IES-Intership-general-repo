"""Contrat commun aux stratégies de validation d'un test SIA 4010.

Deux algorithmes coexistent et ne se remplacent pas :

* la **prévalidation PDF**, qui dit si le modèle a une chance de passer ;
* la **validation officielle**, qui confronte les résultats aux classeurs SIA.

Le premier ne peut jamais conclure à la place du second. Le contrat impose
donc à chaque stratégie de déclarer si elle fait autorité
(:attr:`ValidationStrategy.is_authoritative`), et la fabrique de résultat
force le marquage en conséquence.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from schemas.test_result_schema import TestResult, TestStatus


class ValidationStrategy(ABC):
    """Algorithme de validation d'un test SIA 4010."""

    #: Nom court, repris dans les rapports.
    name: str = "abstract"

    #: Vrai si le verdict de cette stratégie peut être présenté au SIA.
    is_authoritative: bool = False

    @abstractmethod
    def validate(self, test_id: str, context: Any) -> TestResult:
        """Évalue un test et retourne son résultat.

        Args:
            test_id: Alias du test, ex. « test_7 ».
            context: Données nécessaires à la stratégie. Sa forme dépend de
                l'implémentation ; chacune documente ce qu'elle attend.

        Returns:
            TestResult: Résultat du test, jamais `None`.
        """

    def build_result(
        self,
        test_id: str,
        status: TestStatus,
        criterion_source: str,
        errors: tuple[str, ...] = (),
        score: float | None = None,
        criterion_is_inferred: bool = False,
    ) -> TestResult:
        """Fabrique un résultat en imposant les invariants de la stratégie.

        Une stratégie non faisant autorité ne peut PAS produire de `PASS` sec :
        son succès est ramené à `PASS_WITH_RESERVATION`. C'est ce qui empêche
        une prévalidation PDF d'être lue comme une validation.

        Args:
            test_id: Alias du test.
            status: Issue brute calculée par la stratégie.
            criterion_source: Article ou fichier d'où vient le critère.
            errors: Motifs d'échec ou d'impossibilité.
            score: Score normalisé éventuel.
            criterion_is_inferred: Vrai si le critère est déduit, non écrit.

        Returns:
            TestResult: Résultat cohérent avec le statut de la stratégie.
        """
        statut_effectif = status
        if status is TestStatus.PASS and not self.is_authoritative:
            statut_effectif = TestStatus.PASS_WITH_RESERVATION
        return TestResult(
            test_name=test_id,
            status=statut_effectif,
            score=score,
            errors=errors,
            criterion_source=criterion_source,
            criterion_is_inferred=criterion_is_inferred,
        )
