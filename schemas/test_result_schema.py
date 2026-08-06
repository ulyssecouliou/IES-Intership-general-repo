"""Modèle du résultat d'un test SIA 4010."""

from __future__ import annotations

from enum import Enum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, model_validator

Score = Annotated[
    float, Field(ge=0.0, le=1.0, description="Score normalisé entre 0 et 1.")
]


class TestStatus(str, Enum):
    """Issue d'un test SIA 4010.

    `NOT_CHECKABLE` est la valeur par défaut voulue : une donnée manquante ne
    doit jamais produire un succès. `PASS_WITH_RESERVATION` existe parce que
    plusieurs critères SIA reposent sur une lecture arbitrée et non sur un
    texte explicite ; le distinguer d'un `PASS` garde la décision réversible.
    """

    PASS = "PASS"
    PASS_WITH_RESERVATION = "PASS_WITH_RESERVATION"
    FAIL = "FAIL"
    NOT_CHECKABLE = "NOT_CHECKABLE"


PASSING_STATUSES: frozenset[TestStatus] = frozenset(
    {TestStatus.PASS, TestStatus.PASS_WITH_RESERVATION}
)


class TestResult(BaseModel):
    """Résultat d'un test SIA 4010, tel qu'il sera reporté.

    Attributes:
        test_name: Alias du test, ex. « test_1 », « test_2A ».
        status: Issue du test.
        score: Score normalisé, `None` si le test n'en produit pas.
        errors: Motifs d'échec ou d'impossibilité, jamais vide si `FAIL`.
        criterion_source: Origine du critère appliqué. Obligatoire, pour
            qu'aucun verdict ne circule sans son article.
        criterion_is_inferred: Vrai si le critère est déduit et non écrit dans
            la norme -- cas des tests dont la spécification est muette.

    Example:
        >>> TestResult(test_name="test_7", status=TestStatus.NOT_CHECKABLE,
        ...            criterion_source="SIA 4010:2023 §4.4",
        ...            criterion_is_inferred=True).is_passing
        False
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    test_name: str = Field(min_length=1, description="Alias du test SIA 4010.")
    status: TestStatus = Field(
        default=TestStatus.NOT_CHECKABLE, description="Issue du test."
    )
    score: Score | None = Field(default=None, description="Score normalisé.")
    errors: tuple[str, ...] = Field(
        default=(), description="Motifs d'échec ou d'impossibilité."
    )
    criterion_source: str = Field(
        min_length=1, description="Article ou fichier d'où vient le critère."
    )
    criterion_is_inferred: bool = Field(
        default=False, description="Vrai si le critère est déduit, non écrit."
    )

    @model_validator(mode="after")
    def _echec_motive(self) -> "TestResult":
        """Impose un motif à tout échec.

        Un `FAIL` sans motif est inexploitable pour le demandeur comme pour la
        sous-commission.

        Returns:
            TestResult: Le résultat validé, inchangé.

        Raises:
            ValueError: Si `status` vaut `FAIL` et que `errors` est vide.
        """
        if self.status is TestStatus.FAIL and not self.errors:
            raise ValueError(
                "un résultat FAIL doit porter au moins un motif dans `errors`"
            )
        return self

    @property
    def is_passing(self) -> bool:
        """Indique si le test satisfait son critère.

        À préférer à `status == TestStatus.PASS` : un succès sous réserve EST
        un succès au sens de la lecture retenue, et le comparer au seul `PASS`
        le transformerait silencieusement en échec.

        Returns:
            bool: Vrai pour `PASS` et `PASS_WITH_RESERVATION`.
        """
        return self.status in PASSING_STATUSES
