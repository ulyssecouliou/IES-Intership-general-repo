"""Fail-closed navigation through the SIA 4010 class-validation workflow.

The navigator does not issue certification. It makes the technical workflow
explicit and prevents an incomplete annual result, a generic base-test result,
or an unattested comparison from being presented as class compliance.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping, Tuple

from ...config import SIA4010_CLASS_TEST_MATRIX
from ..exceptions import ConfigurationError


PASS_STATUS = "PASS"
BLOCKED_STATUS = "BLOCKED"
FAIL_STATUS = "FAIL"

_MODEL_READY = {"PASS", "READY", "VERIFIED"}
_BAND_PASS = {"OFFICIAL_RESULTS_RECORDED"}
_BAND_FAIL = {"FAIL", "FAILED"}


@dataclass(frozen=True)
class NavigatorGate:
    """One auditable workflow gate shown by the SIA 4010 navigator."""

    gate_id: str
    label: str
    status: str
    message: str
    next_action: str
    missing_variants: Tuple[str, ...] = ()
    failed_variants: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe representation."""

        return asdict(self)


@dataclass(frozen=True)
class NavigatorEvaluation:
    """Conservative class-level result produced by the navigator."""

    target_class: str
    required_variants: Tuple[str, ...]
    overall_status: str
    technical_status: str
    gates: Tuple[NavigatorGate, ...]
    claim_guardrail: str

    def to_dict(self) -> Dict[str, Any]:
        """Return a machine-readable audit payload."""

        return {
            "schema_version": "1.0",
            "target_class": self.target_class,
            "required_variants": list(self.required_variants),
            "overall_status": self.overall_status,
            "technical_status": self.technical_status,
            "gates": [gate.to_dict() for gate in self.gates],
            "claim_guardrail": self.claim_guardrail,
        }


class Sia4010ValidationNavigator:
    """Evaluate the exact variants required by every SIA 4010 validation class."""

    SUPPORTED_CLASSES = tuple(SIA4010_CLASS_TEST_MATRIX)

    @staticmethod
    def _status(payload: Any) -> str:
        """Extract a normalized status from a result payload or scalar."""

        if isinstance(payload, Mapping):
            payload = payload.get("status", "")
        return str(payload or "").strip().upper()

    @classmethod
    def evaluate(
        cls,
        target_class: str,
        *,
        bundle_verified: bool,
        model_case_statuses: Mapping[str, Any],
        candidate_result_locators: Mapping[str, str],
        test_results_map: Mapping[str, Any],
        attestation_locator: str = "",
    ) -> NavigatorEvaluation:
        """Evaluate all workflow gates for one validation class.

        ``test_results_map`` must use exact keys such as ``test_2A``. A generic
        ``test_2`` entry never satisfies 2A, 2B, 2C or 2D.
        """

        class_id = str(target_class or "").strip().upper()
        if class_id not in cls.SUPPORTED_CLASSES:
            raise ConfigurationError(
                "Unsupported SIA 4010 validation class {!r}; expected one of {}."
                .format(target_class, ", ".join(cls.SUPPORTED_CLASSES))
            )
        required = tuple(SIA4010_CLASS_TEST_MATRIX[class_id])
        gates = []

        if bundle_verified:
            gates.append(
                NavigatorGate(
                    "official_bundle",
                    "Official SIA package",
                    PASS_STATUS,
                    "The package manifest and file checksums are verified.",
                    "Keep the immutable manifest with the validation evidence.",
                )
            )
        else:
            gates.append(
                NavigatorGate(
                    "official_bundle",
                    "Official SIA package",
                    BLOCKED_STATUS,
                    "The official package has not been checksum-verified.",
                    "Load the official package and verify every file against its manifest.",
                )
            )

        missing_models = tuple(
            variant
            for variant in required
            if cls._status(model_case_statuses.get(variant)) not in _MODEL_READY
        )
        gates.append(
            NavigatorGate(
                "model_cases",
                "VE reference cases",
                PASS_STATUS if not missing_models else BLOCKED_STATUS,
                (
                    "Every exact VE case required by the class is verified."
                    if not missing_models
                    else "One or more exact VE cases are absent or not verified."
                ),
                (
                    "Freeze the verified model inputs and case fingerprints."
                    if not missing_models
                    else "Generate and validate: {}.".format(", ".join(missing_models))
                ),
                missing_variants=missing_models,
            )
        )

        missing_results = tuple(
            variant
            for variant in required
            if not str(candidate_result_locators.get(variant, "") or "").strip()
        )
        gates.append(
            NavigatorGate(
                "candidate_results",
                "VE/APS candidate results",
                PASS_STATUS if not missing_results else BLOCKED_STATUS,
                (
                    "Traceable candidate result artifacts exist for every variant."
                    if not missing_results
                    else "At least one variant has no traceable VE/APS result artifact."
                ),
                (
                    "Retain the APS extracts and their checksums."
                    if not missing_results
                    else "Run APS and extract the official metrics for: {}.".format(
                        ", ".join(missing_results)
                    )
                ),
                missing_variants=missing_results,
            )
        )

        failed_bands = tuple(
            variant
            for variant in required
            if cls._status(test_results_map.get(variant)) in _BAND_FAIL
        )
        incomplete_bands = tuple(
            variant
            for variant in required
            if cls._status(test_results_map.get(variant)) not in _BAND_PASS | _BAND_FAIL
        )
        band_status = (
            FAIL_STATUS
            if failed_bands
            else BLOCKED_STATUS
            if incomplete_bands
            else PASS_STATUS
        )
        gates.append(
            NavigatorGate(
                "official_comparison",
                "Official acceptance comparisons",
                band_status,
                (
                    "At least one exact variant is outside an official acceptance band."
                    if failed_bands
                    else "At least one mandatory comparison is missing or not checkable."
                    if incomplete_bands
                    else "Every exact variant meets all implemented official criteria."
                ),
                (
                    "Correct the model or result mapping, rerun APS, and compare again."
                    if failed_bands
                    else "Complete annual and hourly-distribution comparisons for: {}.".format(
                        ", ".join(incomplete_bands)
                    )
                    if incomplete_bands
                    else "Prepare the evidence package for official review."
                ),
                missing_variants=incomplete_bands,
                failed_variants=failed_bands,
            )
        )

        attestation = str(attestation_locator or "").strip()
        gates.append(
            NavigatorGate(
                "official_attestation",
                "SIA/sub-commission attestation",
                PASS_STATUS if attestation else BLOCKED_STATUS,
                (
                    "A traceable official attestation is recorded."
                    if attestation
                    else "No official attestation is recorded."
                ),
                (
                    "Archive the attestation with the immutable evidence package."
                    if attestation
                    else "Submit the complete package to the responsible SIA body."
                ),
            )
        )

        technical_ready = (
            bundle_verified
            and not missing_models
            and not missing_results
            and not failed_bands
            and not incomplete_bands
        )
        technical_status = (
            "TECHNICALLY_WITHIN_OFFICIAL_BANDS"
            if technical_ready
            else "TECHNICAL_VALIDATION_INCOMPLETE"
        )
        if not bundle_verified:
            overall = "BLOCKED_OFFICIAL_BUNDLE"
        elif missing_models:
            overall = "MODEL_SETUP_REQUIRED"
        elif missing_results:
            overall = "SIMULATION_REQUIRED"
        elif failed_bands:
            overall = "OFFICIAL_BAND_FAILED"
        elif incomplete_bands:
            overall = "RESULTS_INCOMPLETE"
        elif not attestation:
            overall = "READY_FOR_OFFICIAL_REVIEW"
        else:
            overall = "OFFICIAL_ATTESTATION_RECORDED"

        return NavigatorEvaluation(
            target_class=class_id,
            required_variants=required,
            overall_status=overall,
            technical_status=technical_status,
            gates=tuple(gates),
            claim_guardrail=(
                "The navigator verifies technical readiness and records evidence. "
                "Only the responsible SIA body can grant official SIA 4010 validation."
            ),
        )
