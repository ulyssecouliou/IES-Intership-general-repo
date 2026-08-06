"""Prévalidation d'après les spécifications PDF, sans les classeurs officiels.

Cette stratégie répond à « le modèle a-t-il une chance de passer ? », pas à
« le modèle passe-t-il ? ». Elle ne fait donc jamais autorité, et son meilleur
verdict possible est ``PASS_WITH_RESERVATION`` — imposé par
:meth:`ValidationStrategy.build_result`, pas par convention.

Exemple:
    >>> from core.repositories import JsonIESVERepository
    >>> depot = JsonIESVERepository.from_mapping({"rooms": []})
    >>> PdfValidationStrategy().validate("test_7", depot).status.value
    'NOT_CHECKABLE'
"""

from __future__ import annotations

from typing import Any

from core.strategies.validation_strategy import ValidationStrategy
from schemas.test_result_schema import TestResult, TestStatus

#: Origine du critère appliqué. La prévalidation ne cite aucun seuil chiffré :
#: elle constate la présence ou l'absence de données, rien de plus.
CRITERION_SOURCE = (
    "Prévalidation interne — aucun article normatif. SIA 4010:2023 ne définit "
    "aucun critère numérique générique ; seul le Test 1 énonce le sien, et il "
    "porte sur la bande des programmes de référence, pas sur un seuil fixe."
)


class PdfValidationStrategy(ValidationStrategy):
    """Prévalidation fondée sur la complétude du modèle IESVE."""

    name = "pdf_prevalidation"
    is_authoritative = False

    def validate(self, test_id: str, context: Any) -> TestResult:
        """Évalue la complétude du modèle pour un test donné.

        Args:
            test_id: Alias du test, ex. « test_1 ».
            context: Un :class:`core.repositories.IESVERepository`.

        Returns:
            TestResult: `NOT_CHECKABLE` si le modèle ne fournit aucun local,
            sinon un succès **sous réserve** — jamais un `PASS` sec.
        """
        manques = self._manques(context)
        if manques:
            return self.build_result(
                test_id=test_id,
                status=TestStatus.NOT_CHECKABLE,
                criterion_source=CRITERION_SOURCE,
                errors=manques,
            )
        return self.build_result(
            test_id=test_id,
            status=TestStatus.PASS,
            criterion_source=CRITERION_SOURCE,
        )

    def _manques(self, depot: Any) -> tuple[str, ...]:
        """Recense ce qui empêche même une prévalidation.

        Args:
            depot: Dépôt IESVE à interroger.

        Returns:
            tuple[str, ...]: Motifs, vide si le modèle est exploitable.
        """
        try:
            locaux = depot.get_rooms()
        except Exception as erreur:  # noqa: BLE001 -- on rapporte, on ne masque pas
            return ("modèle illisible : %s: %s" % (type(erreur).__name__, erreur),)
        if not locaux:
            return ("le modèle ne contient aucun local exploitable",)
        sans_usage = [local.id for local in locaux if not local.usage]
        if sans_usage:
            return (
                "usage SIA 2024 absent pour %d local/locaux : %s"
                % (len(sans_usage), ", ".join(sorted(sans_usage)[:5])),
            )
        return ()
