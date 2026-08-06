"""Modèle d'une classe de validation SIA 4010 (1A à 5)."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, model_validator

from schemas.test_result_schema import TestResult, TestStatus


class ValidationClassStatus(str, Enum):
    """Issue d'une classe de validation.

    `INCOMPLETE` est distinct de `NOT_CONCLUSIVE` : la première dit qu'un test
    exigé est ABSENT du dossier, la seconde qu'il est présent mais non
    évaluable. Les deux empêchent la validation, mais l'action à mener diffère.
    """

    VALIDATED = "VALIDATED"
    FAILED = "FAILED"
    NOT_CONCLUSIVE = "NOT_CONCLUSIVE"
    INCOMPLETE = "INCOMPLETE"


class ValidationClass(BaseModel):
    """Classe de validation et son état, tests exigés compris.

    Règle appliquée sans exception : une classe n'est `VALIDATED` que si TOUS
    les tests que SIA 4010:2023 tableau 63 lui impose sont présents ET
    conformes. Un test absent la rend `INCOMPLETE`, jamais « validée sur ce
    qu'on a ».

    Attributes:
        class_name: Nom de la classe, ex. « 4A ».
        required_tests: Alias des tests exigés par le tableau 63.
        results: Résultats disponibles, indexés par alias de test.
        source: Article dont provient la liste des tests exigés.

    Example:
        >>> from schemas import TestResult, TestStatus
        >>> ok = TestResult(test_name="test_7", status=TestStatus.PASS,
        ...                 criterion_source="classeur SIA")
        >>> ValidationClass(class_name="5", required_tests=("test_7",),
        ...                 results={"test_7": ok}).status
        <ValidationClassStatus.VALIDATED: 'VALIDATED'>
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    class_name: str = Field(min_length=1, description="Nom de la classe, ex. « 4A ».")
    required_tests: tuple[str, ...] = Field(
        min_length=1, description="Alias des tests exigés par le tableau 63."
    )
    results: dict[str, TestResult] = Field(
        default_factory=dict, description="Résultats disponibles par alias."
    )
    source: str = Field(
        default="SIA 4010:2023, §4.5, tableau 63",
        min_length=1,
        description="Article dont provient la liste des tests exigés.",
    )

    @model_validator(mode="after")
    def _resultats_coherents(self) -> "ValidationClass":
        """Vérifie que chaque résultat porte bien l'alias sous lequel il est rangé.

        Une clé qui ne correspond pas au `test_name` du résultat fausserait
        silencieusement le calcul de couverture.

        Returns:
            ValidationClass: La classe validée, inchangée.

        Raises:
            ValueError: Si une clé diverge du `test_name` du résultat.
        """
        divergences = [
            "%s != %s" % (alias, resultat.test_name)
            for alias, resultat in self.results.items()
            if alias != resultat.test_name
        ]
        if divergences:
            raise ValueError(
                "clé de résultat incohérente avec test_name : %s"
                % ", ".join(sorted(divergences))
            )
        return self

    @property
    def missing_tests(self) -> tuple[str, ...]:
        """Tests exigés dont aucun résultat n'est disponible.

        Returns:
            tuple[str, ...]: Alias manquants, dans l'ordre du tableau 63.
        """
        return tuple(alias for alias in self.required_tests if alias not in self.results)

    @property
    def covered_tests(self) -> tuple[str, ...]:
        """Tests exigés pour lesquels un résultat existe.

        Returns:
            tuple[str, ...]: Alias couverts, dans l'ordre du tableau 63.
        """
        return tuple(alias for alias in self.required_tests if alias in self.results)

    @property
    def status(self) -> ValidationClassStatus:
        """État de la classe, déduit de ses résultats.

        Un échec avéré prime sur une absence : il est plus grave, et le
        masquer derrière « incomplète » le ferait disparaître du rapport.

        Returns:
            ValidationClassStatus: État de la classe.
        """
        disponibles = [self.results[alias] for alias in self.covered_tests]
        if any(r.status is TestStatus.FAIL for r in disponibles):
            return ValidationClassStatus.FAILED
        if self.missing_tests:
            return ValidationClassStatus.INCOMPLETE
        if all(r.is_passing for r in disponibles):
            return ValidationClassStatus.VALIDATED
        return ValidationClassStatus.NOT_CONCLUSIVE

    @property
    def is_validated(self) -> bool:
        """Indique si la classe est acquise.

        Returns:
            bool: Vrai uniquement pour `VALIDATED`.
        """
        return self.status is ValidationClassStatus.VALIDATED
