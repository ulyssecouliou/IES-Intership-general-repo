"""Fail-closed external-input evidence for SIA 4010 model generation.

The supplied SIA 4010 package delegates some normative inputs to standards,
licensed datasets and authority clarifications that are not distributed with
the test workbooks.  This module records those files without embedding their
content or treating a candidate-created conversion as authoritative.

An entry becomes ``READY_FOR_BINDING`` only when both its source and its
technical-validation report are checksum-valid, its provenance is explicit,
its use permission is documented and its normative authorization is confirmed.
That status only authorizes implementation work; it is never an SIA attestation.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple, Union

from ..exceptions import ConfigurationError
from .case_registry import base_test_id, get_case_capability
from .model_scenario import TEST_CASES


SCHEMA_VERSION = "1.0"
EXTERNAL_INPUT_FILENAME = "sia4010_external_inputs.json"

PROVENANCE_STATUSES = {
    "MISSING",
    "SIA_SUPPLIED",
    "LICENSED_STANDARD_COPY",
    "CLIENT_SUPPLIED",
    "CANDIDATE_DERIVED",
}
AUTHORIZATION_STATUSES = {"UNCONFIRMED", "CONFIRMED"}
VALIDATION_STATUSES = {"PENDING", "PASS", "FAIL"}
VALIDATION_REPORT_SCHEMA_VERSION = "1.0"


EXTERNAL_INPUT_CATALOG: Dict[str, Dict[str, str]] = {
    "iso52016_2017_chapter7_test_cell": {
        "description": (
            "Complete machine-readable ISO EN 52016-1:2017 Chapter 7 test-cell "
            "input set and independently checked transcription."
        ),
        "source_required": "ISO EN 52016-1:2017 Chapter 7",
    },
    "sia2028_dry_normal_zurich_kloten": {
        "description": (
            "Authorized hourly SIA 2028 DRY normal Zürich-Kloten climate data "
            "and validated VE conversion."
        ),
        "source_required": "SIA 2028 DRY normal, Zürich-Kloten",
    },
    "sia2024_office_3_1_standard_profiles": {
        "description": (
            "Exact schedules and annual simultaneity for SIA 2024:2021 use "
            "category 3.1 Einzel-/Gruppenbüro, standard values."
        ),
        "source_required": "SIA 2024:2021, category 3.1",
    },
    "sia3874_2017_table9_controls": {
        "description": (
            "Exact machine-readable shading control functions 1-3 from "
            "SIA 387/4:2017 Table 9."
        ),
        "source_required": "SIA 387/4:2017 Table 9",
    },
    "sia3874_2017_tables9_10_controls": {
        "description": (
            "Exact machine-readable shading and lighting control algorithms "
            "from SIA 387/4:2017 Tables 9 and 10."
        ),
        "source_required": "SIA 387/4:2017 Tables 9 and 10",
    },
    "sia_example_building_fabric_awning_detail": {
        "description": (
            "Exact source-traced fabric-awning identity, mounting and optical "
            "states referenced by SIA 4010 Test 3."
        ),
        "source_required": (
            "SIA example-building fabric-awning definition referenced by "
            "SIA 4010 Test 3"
        ),
    },
    "sia_authority_test3_3k_3l_device_clarification": {
        "description": (
            "Written authority clarification resolving the contradictory "
            "Test 3K/3L shading-device identity."
        ),
        "source_required": "SIA 4010 sub-commission clarification",
    },
    "sia2024_auditorium_target_profiles": {
        "description": (
            "Exact target-value schedules and simultaneity for the SIA 2024:2021 "
            "Hörsaal use category."
        ),
        "source_required": "SIA 2024:2021 Hörsaal target values",
    },
    "test4_fan_curve_digitization": {
        "description": (
            "Independently verified structured transcription of the normative "
            "Test 4 fan characteristic curves."
        ),
        "source_required": "SIA 4010 Test 4 specification fan-curve figures",
    },
    "sia2024_example_building_standard_profiles": {
        "description": (
            "Exact room-by-room standard SIA 2024:2021 inputs, schedules and "
            "annual simultaneity for the example building."
        ),
        "source_required": "SIA 2024:2021 example-building use categories",
    },
    "en16798_5_1_annex_d_rotary_recovery_model": {
        "description": (
            "Machine-implemented and independently checked rotary heat-recovery "
            "part-load model."
        ),
        "source_required": "EN 16798-5-1 Annex D",
    },
    "test5_fan_curve_digitization": {
        "description": (
            "Independently verified structured transcription of the normative "
            "Test 5 fan characteristic curves."
        ),
        "source_required": "SIA 4010 Test 5 specification fan-curve figures",
    },
    "sia2024_restaurant_6_2_standard_profiles": {
        "description": (
            "Exact standard schedules, gains and simultaneity for SIA 2024:2021 "
            "category 6.2 Selbstbedienungsrestaurant."
        ),
        "source_required": "SIA 2024:2021 category 6.2",
    },
    "sia2024_kitchen_6_4_standard_profiles": {
        "description": (
            "Exact standard schedules, process gains and simultaneity for "
            "SIA 2024:2021 category 6.4 Küche."
        ),
        "source_required": "SIA 2024:2021 category 6.4",
    },
    "test6_stage_control_trace": {
        "description": (
            "Independently verified machine-readable Test 6 three-stage "
            "ventilation control trace."
        ),
        "source_required": "SIA 4010 Test 6 specification control graph",
    },
    "test7_heat_pump_performance_tables": {
        "description": (
            "Structured and independently verified capacity, COP, EER, standby "
            "and crankcase inputs for the specified Test 7 generator."
        ),
        "source_required": "SIA 4010 Test 7 reference documentation",
    },
    "sia_authority_test7_pv_precedence": {
        "description": (
            "Written authority decision on the Test 7 PV total and east/west "
            "allocation inconsistency."
        ),
        "source_required": "SIA 4010 sub-commission clarification",
    },
}

EXTERNAL_INPUT_BINDING_SCHEMAS: Dict[str, str] = {
    "iso52016_2017_chapter7_test_cell": (
        "sia4010.iso52016_chapter7_test_cell.v1"
    ),
    "sia2028_dry_normal_zurich_kloten": (
        "sia4010.sia2028_hourly_weather.v1"
    ),
    "sia2024_office_3_1_standard_profiles": (
        "sia4010.sia2024_usage_profiles.v1"
    ),
    "sia3874_2017_table9_controls": (
        "sia4010.sia3874_shading_controls.v1"
    ),
    "sia3874_2017_tables9_10_controls": (
        "sia4010.sia3874_shading_lighting_controls.v1"
    ),
    "sia_example_building_fabric_awning_detail": (
        "sia4010.shading_device_definition.v1"
    ),
    "sia_authority_test3_3k_3l_device_clarification": (
        "sia4010.authority_decision.v1"
    ),
    "sia2024_auditorium_target_profiles": (
        "sia4010.sia2024_usage_profiles.v1"
    ),
    "test4_fan_curve_digitization": "sia4010.fan_curves.v1",
    "sia2024_example_building_standard_profiles": (
        "sia4010.sia2024_usage_profiles.v1"
    ),
    "en16798_5_1_annex_d_rotary_recovery_model": (
        "sia4010.rotary_recovery_model.v1"
    ),
    "test5_fan_curve_digitization": "sia4010.fan_curves.v1",
    "sia2024_restaurant_6_2_standard_profiles": (
        "sia4010.sia2024_usage_profiles.v1"
    ),
    "sia2024_kitchen_6_4_standard_profiles": (
        "sia4010.sia2024_usage_profiles.v1"
    ),
    "test6_stage_control_trace": "sia4010.control_trace.v1",
    "test7_heat_pump_performance_tables": (
        "sia4010.generator_performance_tables.v1"
    ),
    "sia_authority_test7_pv_precedence": (
        "sia4010.authority_decision.v1"
    ),
}


_COMMON_CELL_INPUTS = (
    "iso52016_2017_chapter7_test_cell",
    "sia2028_dry_normal_zurich_kloten",
    "sia2024_office_3_1_standard_profiles",
)


def required_external_input_ids(
    variant: str, case_id: str
) -> Tuple[str, ...]:
    """Return the exact delegated inputs required before generator binding."""

    # Validate the exact registry pair before deriving its base-test contract.
    # ``base_test_id`` alone would accept a syntactically plausible but
    # non-existent combination such as test_2A/2D.
    get_case_capability(variant, case_id)
    test_id = base_test_id(variant)
    if test_id == "1":
        # Les six cas ISO tournent sur la météo DRYCOLD fournie et n'ont aucune
        # entrée déléguée. La chaîne diagnostique en introduit une par maillon,
        # et l'ordre est celui de la spécification, figé dans
        # refs/reference-data/test-1.diagnostics.ref.json :
        #   1A  cellule ISO + climat Zürich-Kloten
        #   1B  idem — la nouvelle fenêtre vient de la spécification Test 2 et
        #       de la documentation du bâtiment exemple, deux fichiers
        #       officiels, pas des entrées déléguées
        #   1C  + SIA 2024 : l'infiltration ajustée y est chiffrée
        #       « 0.15 m3/(h*m2) gemäss SIA 2024:2021 »
        #   1D  idem — usage personnes/appareils/éclairage selon SIA 2024
        #   1E  idem 1D, plus le store, dont les propriétés sont dans la
        #       documentation officielle du bâtiment exemple
        # Rendre `()` pour 1A à 1D affirmerait qu'ils ne dépendent d'aucune
        # donnée déléguée, alors que le climat de Kloten en est une.
        if case_id in {"1A", "1B"}:
            return (
                "iso52016_2017_chapter7_test_cell",
                "sia2028_dry_normal_zurich_kloten",
            )
        if case_id in {"1C", "1D", "1E"}:
            return _COMMON_CELL_INPUTS
        return ()
    if test_id == "2":
        extra = (
            ("sia3874_2017_table9_controls",)
            if case_id in {"2B", "2C", "2D"}
            else ()
        )
        return _COMMON_CELL_INPUTS + extra
    if test_id == "3":
        extra = (
            ("sia_authority_test3_3k_3l_device_clarification",)
            if case_id in {"3K", "3L"}
            else ()
        )
        return _COMMON_CELL_INPUTS + (
            "sia3874_2017_tables9_10_controls",
            "sia_example_building_fabric_awning_detail",
        ) + extra
    if test_id == "4":
        return (
            "sia2028_dry_normal_zurich_kloten",
            "sia2024_auditorium_target_profiles",
            "test4_fan_curve_digitization",
        )
    if test_id == "5":
        return (
            "sia2028_dry_normal_zurich_kloten",
            "sia2024_example_building_standard_profiles",
            "en16798_5_1_annex_d_rotary_recovery_model",
            "test5_fan_curve_digitization",
        )
    if test_id == "6":
        return (
            "sia2028_dry_normal_zurich_kloten",
            "sia2024_restaurant_6_2_standard_profiles",
            "sia2024_kitchen_6_4_standard_profiles",
            "test6_stage_control_trace",
        )
    if test_id == "7":
        return (
            "sia2028_dry_normal_zurich_kloten",
            "test7_heat_pump_performance_tables",
            "sia_authority_test7_pv_precedence",
        )
    raise ConfigurationError(
        "No external-input contract exists for {}/{}".format(variant, case_id)
    )


def _sha256(path: Path) -> str:
    """Return one lowercase SHA-256 digest."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolved_path(manifest_path: Path, value: Any) -> Optional[Path]:
    """Resolve a possibly relative manifest locator."""

    text = str(value or "").strip()
    if not text:
        return None
    path = Path(text)
    return (
        path.resolve()
        if path.is_absolute()
        else (manifest_path.parent / path).resolve()
    )


def _validate_technical_report(
    path: Path,
    *,
    input_id: str,
    source_sha256: str,
    expected_status: str,
    expected_binding_schema: str,
) -> Tuple[Path, str, str]:
    """Validate a technical report and its binding to the exact source file."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConfigurationError(
            "External input '{}' has an invalid technical validation report: "
            "{}".format(input_id, exc)
        ) from exc
    if not isinstance(payload, dict):
        raise ConfigurationError(
            "External input '{}' technical validation report must be a JSON "
            "object".format(input_id)
        )
    if str(payload.get("schema_version", "")) != (
        VALIDATION_REPORT_SCHEMA_VERSION
    ):
        raise ConfigurationError(
            "External input '{}' validation-report schema is unsupported: "
            "{!r}".format(input_id, payload.get("schema_version"))
        )
    if str(payload.get("input_id", "")) != input_id:
        raise ConfigurationError(
            "External input '{}' validation report identifies {!r}".format(
                input_id, payload.get("input_id")
            )
        )
    if str(payload.get("source_sha256", "")).strip().lower() != source_sha256:
        raise ConfigurationError(
            "External input '{}' validation report is not bound to the exact "
            "source SHA-256".format(input_id)
        )
    report_status = str(payload.get("status", "")).strip().upper()
    if report_status != expected_status:
        raise ConfigurationError(
            "External input '{}' validation-report status {!r} does not match "
            "the manifest status {!r}".format(
                input_id, report_status, expected_status
            )
        )
    for field in ("validated_by", "validation_method"):
        if not str(payload.get(field, "") or "").strip():
            raise ConfigurationError(
                "External input '{}' validation report is missing {}".format(
                    input_id, field
                )
            )
    checks = payload.get("checks")
    if not isinstance(checks, list) or not checks:
        raise ConfigurationError(
            "External input '{}' validation report requires a non-empty checks "
            "list".format(input_id)
        )
    for index, check in enumerate(checks, start=1):
        if not isinstance(check, dict):
            raise ConfigurationError(
                "External input '{}' validation check {} must be an object".format(
                    input_id, index
                )
            )
        check_id = str(check.get("id", "") or "").strip()
        check_status = str(check.get("status", "")).strip().upper()
        if not check_id or check_status not in VALIDATION_STATUSES:
            raise ConfigurationError(
                "External input '{}' validation check {} has an invalid id or "
                "status".format(input_id, index)
            )
        if report_status == "PASS" and check_status != "PASS":
            raise ConfigurationError(
                "External input '{}' cannot have PASS report status while "
                "check {!r} is {}".format(input_id, check_id, check_status)
            )
    binding = payload.get("binding_artifact")
    if not isinstance(binding, dict):
        raise ConfigurationError(
            "External input '{}' validation report requires a "
            "binding_artifact object".format(input_id)
        )
    binding_path_text = str(binding.get("path", "") or "").strip()
    binding_sha256 = str(binding.get("sha256", "") or "").strip().lower()
    binding_schema = str(binding.get("schema_id", "") or "").strip()
    if not binding_path_text:
        raise ConfigurationError(
            "External input '{}' binding artifact path is missing".format(
                input_id
            )
        )
    binding_path = Path(binding_path_text)
    if not binding_path.is_absolute():
        binding_path = path.parent / binding_path
    binding_path = binding_path.resolve()
    if not binding_path.is_file():
        raise ConfigurationError(
            "External input '{}' binding artifact does not exist: {}".format(
                input_id, binding_path
            )
        )
    if not binding_sha256 or _sha256(binding_path) != binding_sha256:
        raise ConfigurationError(
            "External input '{}' binding artifact checksum mismatch: {}".format(
                input_id, binding_path
            )
        )
    if binding_schema != expected_binding_schema:
        raise ConfigurationError(
            "External input '{}' requires binding schema {!r}, received "
            "{!r}".format(input_id, expected_binding_schema, binding_schema)
        )
    return binding_path, binding_sha256, binding_schema


@dataclass(frozen=True)
class ExternalInputEvidence:
    """Checksum and authorization state of one delegated input."""

    input_id: str
    description: str
    source_required: str
    status: str
    source_path: Optional[Path]
    source_sha256: str
    provenance_status: str
    normative_authorization_status: str
    source_authority: str
    license_reference: str
    dataset_identity: str
    machine_readable_format: str
    semantic_scope: Tuple[str, ...]
    validation_status: str
    validation_report_path: Optional[Path]
    validation_report_sha256: str
    binding_artifact_path: Optional[Path]
    binding_artifact_sha256: str
    binding_schema_id: str
    issues: Tuple[str, ...]

    @property
    def ready_for_binding(self) -> bool:
        """Return whether this evidence can enter implementation binding."""

        return self.status == "READY_FOR_BINDING"

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe audit record."""

        payload = asdict(self)
        payload["source_path"] = (
            str(self.source_path) if self.source_path is not None else None
        )
        payload["validation_report_path"] = (
            str(self.validation_report_path)
            if self.validation_report_path is not None
            else None
        )
        payload["binding_artifact_path"] = (
            str(self.binding_artifact_path)
            if self.binding_artifact_path is not None
            else None
        )
        payload["semantic_scope"] = list(self.semantic_scope)
        payload["issues"] = list(self.issues)
        payload["ready_for_binding"] = self.ready_for_binding
        return payload


@dataclass(frozen=True)
class ExternalInputReadiness:
    """Readiness of all delegated inputs for one exact SIA 4010 case."""

    variant: str
    case_id: str
    manifest_path: Optional[Path]
    status: str
    required_input_ids: Tuple[str, ...]
    ready_input_ids: Tuple[str, ...]
    blocked_input_ids: Tuple[str, ...]
    evidence: Tuple[ExternalInputEvidence, ...]

    @property
    def ready_for_binding(self) -> bool:
        """Return whether every delegated source is implementation-ready."""

        return self.status in {"NOT_REQUIRED", "READY_FOR_BINDING"}

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe case-level readiness record."""

        return {
            "variant": self.variant,
            "case_id": self.case_id,
            "manifest_path": (
                str(self.manifest_path)
                if self.manifest_path is not None
                else None
            ),
            "status": self.status,
            "required_input_ids": list(self.required_input_ids),
            "ready_input_ids": list(self.ready_input_ids),
            "blocked_input_ids": list(self.blocked_input_ids),
            "ready_for_binding": self.ready_for_binding,
            "evidence": [item.to_dict() for item in self.evidence],
            "claim_guardrail": (
                "READY_FOR_BINDING validates delegated input provenance and "
                "technical transcription only. It does not prove a VE generator, "
                "a passing result or an SIA attestation."
            ),
        }


class Sia4010ExternalInputManifest:
    """Strict loader for project-supplied delegated input evidence."""

    def __init__(
        self,
        path: Path,
        entries: Mapping[str, Mapping[str, Any]],
    ):
        """Initialize a validated manifest from normalized evidence entries."""

        self.path = path
        self.entries = dict(entries)

    @classmethod
    def load(
        cls, path: Union[str, Path]
    ) -> "Sia4010ExternalInputManifest":
        """Load one external-input manifest and reject typos or bad schemas."""

        manifest_path = Path(path).resolve()
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ConfigurationError(
                "Invalid SIA 4010 external-input manifest: {}".format(exc)
            ) from exc
        if not isinstance(payload, dict):
            raise ConfigurationError(
                "SIA 4010 external-input manifest must contain a JSON object"
            )
        if str(payload.get("schema_version", "")) != SCHEMA_VERSION:
            raise ConfigurationError(
                "Unsupported SIA 4010 external-input schema: {}".format(
                    payload.get("schema_version")
                )
            )
        entries = payload.get("inputs")
        if not isinstance(entries, dict):
            raise ConfigurationError(
                "SIA 4010 external-input manifest requires an inputs object"
            )
        unknown = sorted(set(entries) - set(EXTERNAL_INPUT_CATALOG))
        if unknown:
            raise ConfigurationError(
                "Unknown SIA 4010 external input IDs: {}".format(unknown)
            )
        for input_id, value in entries.items():
            if not isinstance(value, dict):
                raise ConfigurationError(
                    "External input '{}' must be a JSON object".format(input_id)
                )
        return cls(manifest_path, entries)

    def evidence(self, input_id: str) -> ExternalInputEvidence:
        """Validate and return one catalogued evidence entry."""

        if input_id not in EXTERNAL_INPUT_CATALOG:
            raise ConfigurationError(
                "Unknown SIA 4010 external input ID: {}".format(input_id)
            )
        catalog = EXTERNAL_INPUT_CATALOG[input_id]
        record = self.entries.get(input_id)
        if record is None:
            evidence = ExternalInputEvidence(
                input_id=input_id,
                description=catalog["description"],
                source_required=catalog["source_required"],
                status="MISSING",
                source_path=None,
                source_sha256="",
                provenance_status="MISSING",
                normative_authorization_status="UNCONFIRMED",
                source_authority="",
                license_reference="",
                dataset_identity="",
                machine_readable_format="",
                semantic_scope=(),
                validation_status="PENDING",
                validation_report_path=None,
                validation_report_sha256="",
                binding_artifact_path=None,
                binding_artifact_sha256="",
                binding_schema_id=EXTERNAL_INPUT_BINDING_SCHEMAS[input_id],
                issues=("manifest entry is missing",),
            )
            return evidence

        provenance = str(
            record.get("provenance_status", "MISSING")
        ).strip().upper()
        authorization = str(
            record.get("normative_authorization_status", "UNCONFIRMED")
        ).strip().upper()
        validation = record.get("technical_validation") or {}
        if not isinstance(validation, Mapping):
            raise ConfigurationError(
                "External input '{}' technical_validation must be an object".format(
                    input_id
                )
            )
        validation_status = str(
            validation.get("status", "PENDING")
        ).strip().upper()
        if provenance not in PROVENANCE_STATUSES:
            raise ConfigurationError(
                "External input '{}' has unsupported provenance_status {!r}".format(
                    input_id, provenance
                )
            )
        if authorization not in AUTHORIZATION_STATUSES:
            raise ConfigurationError(
                "External input '{}' has unsupported authorization status {!r}".format(
                    input_id, authorization
                )
            )
        if validation_status not in VALIDATION_STATUSES:
            raise ConfigurationError(
                "External input '{}' has unsupported validation status {!r}".format(
                    input_id, validation_status
                )
            )

        source_path = _resolved_path(self.path, record.get("source_path"))
        expected_source_sha = str(
            record.get("source_sha256", "") or ""
        ).strip().lower()
        validation_report_path = _resolved_path(
            self.path, validation.get("report_path")
        )
        expected_report_sha = str(
            validation.get("report_sha256", "") or ""
        ).strip().lower()
        binding_artifact_path = None
        binding_artifact_sha256 = ""
        binding_schema_id = EXTERNAL_INPUT_BINDING_SCHEMAS[input_id]
        issues = []
        if source_path is None:
            issues.append("source_path is missing")
        elif not source_path.is_file():
            issues.append("source file does not exist")
        elif not expected_source_sha:
            issues.append("source_sha256 is missing")
        elif _sha256(source_path) != expected_source_sha:
            raise ConfigurationError(
                "External input '{}' source checksum mismatch: {}".format(
                    input_id, source_path
                )
            )
        if provenance == "MISSING":
            issues.append("provenance is missing")
        if authorization != "CONFIRMED":
            issues.append("normative authorization is unconfirmed")
        source_authority = str(record.get("source_authority", "") or "").strip()
        license_reference = str(
            record.get("license_reference", "") or ""
        ).strip()
        dataset_identity = str(
            record.get("dataset_identity", "") or ""
        ).strip()
        machine_format = str(
            record.get("machine_readable_format", "") or ""
        ).strip()
        semantic_scope_value = record.get("semantic_scope") or []
        if not isinstance(semantic_scope_value, list) or not all(
            isinstance(item, str) and item.strip()
            for item in semantic_scope_value
        ):
            raise ConfigurationError(
                "External input '{}' semantic_scope must be a list of strings".format(
                    input_id
                )
            )
        semantic_scope = tuple(item.strip() for item in semantic_scope_value)
        for value, label in (
            (source_authority, "source_authority"),
            (license_reference, "license_reference"),
            (dataset_identity, "dataset_identity"),
            (machine_format, "machine_readable_format"),
            (semantic_scope, "semantic_scope"),
        ):
            if not value:
                issues.append("{} is missing".format(label))
        if validation_status != "PASS":
            issues.append(
                "technical validation status is {}".format(validation_status)
            )
        if validation_report_path is None:
            issues.append("technical validation report_path is missing")
        elif not validation_report_path.is_file():
            issues.append("technical validation report does not exist")
        elif not expected_report_sha:
            issues.append("technical validation report_sha256 is missing")
        elif _sha256(validation_report_path) != expected_report_sha:
            raise ConfigurationError(
                "External input '{}' validation-report checksum mismatch: {}".format(
                    input_id, validation_report_path
                )
            )
        else:
            (
                binding_artifact_path,
                binding_artifact_sha256,
                binding_schema_id,
            ) = _validate_technical_report(
                validation_report_path,
                input_id=input_id,
                source_sha256=expected_source_sha,
                expected_status=validation_status,
                expected_binding_schema=EXTERNAL_INPUT_BINDING_SCHEMAS[
                    input_id
                ],
            )

        evidence = ExternalInputEvidence(
            input_id=input_id,
            description=catalog["description"],
            source_required=catalog["source_required"],
            status="READY_FOR_BINDING" if not issues else "BLOCKED",
            source_path=source_path,
            source_sha256=expected_source_sha,
            provenance_status=provenance,
            normative_authorization_status=authorization,
            source_authority=source_authority,
            license_reference=license_reference,
            dataset_identity=dataset_identity,
            machine_readable_format=machine_format,
            semantic_scope=semantic_scope,
            validation_status=validation_status,
            validation_report_path=validation_report_path,
            validation_report_sha256=expected_report_sha,
            binding_artifact_path=binding_artifact_path,
            binding_artifact_sha256=binding_artifact_sha256,
            binding_schema_id=binding_schema_id,
            issues=tuple(issues),
        )
        return evidence

    def readiness(self, variant: str, case_id: str) -> ExternalInputReadiness:
        """Evaluate every delegated input needed by one exact case."""

        required = required_external_input_ids(variant, case_id)
        evidence = tuple(self.evidence(input_id) for input_id in required)
        ready = tuple(
            item.input_id for item in evidence if item.ready_for_binding
        )
        blocked = tuple(
            item.input_id for item in evidence if not item.ready_for_binding
        )
        return ExternalInputReadiness(
            variant=variant,
            case_id=case_id,
            manifest_path=self.path,
            status=(
                "NOT_REQUIRED"
                if not required
                else "READY_FOR_BINDING"
                if not blocked
                else "BLOCKED"
            ),
            required_input_ids=required,
            ready_input_ids=ready,
            blocked_input_ids=blocked,
            evidence=evidence,
        )


def external_input_readiness(
    project_root: Union[str, Path],
    variant: str,
    case_id: str,
    *,
    manifest: Optional[Sia4010ExternalInputManifest] = None,
) -> ExternalInputReadiness:
    """Return delegated-input readiness, including an absent-manifest result."""

    required = required_external_input_ids(variant, case_id)
    if not required:
        return ExternalInputReadiness(
            variant=variant,
            case_id=case_id,
            manifest_path=None,
            status="NOT_REQUIRED",
            required_input_ids=(),
            ready_input_ids=(),
            blocked_input_ids=(),
            evidence=(),
        )
    manifest_path = Path(project_root) / EXTERNAL_INPUT_FILENAME
    selected = manifest
    if selected is None and manifest_path.is_file():
        selected = Sia4010ExternalInputManifest.load(manifest_path)
    if selected is None:
        evidence = tuple(
            ExternalInputEvidence(
                input_id=input_id,
                description=EXTERNAL_INPUT_CATALOG[input_id]["description"],
                source_required=EXTERNAL_INPUT_CATALOG[input_id][
                    "source_required"
                ],
                status="MISSING",
                source_path=None,
                source_sha256="",
                provenance_status="MISSING",
                normative_authorization_status="UNCONFIRMED",
                source_authority="",
                license_reference="",
                dataset_identity="",
                machine_readable_format="",
                semantic_scope=(),
                validation_status="PENDING",
                validation_report_path=None,
                validation_report_sha256="",
                binding_artifact_path=None,
                binding_artifact_sha256="",
                binding_schema_id=EXTERNAL_INPUT_BINDING_SCHEMAS[input_id],
                issues=("project external-input manifest is missing",),
            )
            for input_id in required
        )
        return ExternalInputReadiness(
            variant=variant,
            case_id=case_id,
            manifest_path=manifest_path,
            status="MISSING_MANIFEST",
            required_input_ids=required,
            ready_input_ids=(),
            blocked_input_ids=required,
            evidence=evidence,
        )
    if selected.path.resolve() != manifest_path.resolve():
        raise ConfigurationError(
            "Cached SIA 4010 external-input manifest does not match the "
            "active project: {} != {}".format(
                selected.path.resolve(), manifest_path.resolve()
            )
        )
    return selected.readiness(variant, case_id)


def build_external_input_matrix(
    project_root: Union[str, Path],
    *,
    manifest: Optional[Sia4010ExternalInputManifest] = None,
) -> Dict[str, Any]:
    """Build a concise 30-case delegated-input implementation matrix."""

    project = Path(project_root)
    manifest_path = project / EXTERNAL_INPUT_FILENAME
    selected = manifest
    if selected is None and manifest_path.is_file():
        selected = Sia4010ExternalInputManifest.load(manifest_path)
    if selected is not None and selected.path.resolve() != manifest_path.resolve():
        raise ConfigurationError(
            "Cached SIA 4010 external-input manifest does not match the "
            "active project: {} != {}".format(
                selected.path.resolve(), manifest_path.resolve()
            )
        )

    cases = []
    input_usage: Dict[str, list] = {
        input_id: [] for input_id in EXTERNAL_INPUT_CATALOG
    }
    status_counts: Dict[str, int] = {}
    evidence_by_id: Dict[str, ExternalInputEvidence] = {}
    for variant, case_ids in TEST_CASES.items():
        for case_id in case_ids:
            readiness = external_input_readiness(
                project,
                variant,
                case_id,
                manifest=selected,
            )
            status_counts[readiness.status] = (
                status_counts.get(readiness.status, 0) + 1
            )
            case_ref = "{}/{}".format(variant, case_id)
            for input_id in readiness.required_input_ids:
                input_usage[input_id].append(case_ref)
            for evidence in readiness.evidence:
                evidence_by_id[evidence.input_id] = evidence
            cases.append(
                {
                    "variant": variant,
                    "case_id": case_id,
                    "status": readiness.status,
                    "ready_for_binding": readiness.ready_for_binding,
                    "required_input_ids": list(readiness.required_input_ids),
                    "blocked_input_ids": list(readiness.blocked_input_ids),
                }
            )

    inputs = []
    for input_id, catalog in EXTERNAL_INPUT_CATALOG.items():
        evidence = evidence_by_id.get(input_id)
        if evidence is None and selected is not None:
            evidence = selected.evidence(input_id)
        inputs.append(
            {
                "input_id": input_id,
                "description": catalog["description"],
                "source_required": catalog["source_required"],
                "binding_schema_id": EXTERNAL_INPUT_BINDING_SCHEMAS[input_id],
                "status": (
                    evidence.status if evidence is not None else "MISSING"
                ),
                "affected_cases": input_usage[input_id],
                "issues": (
                    list(evidence.issues)
                    if evidence is not None
                    else ["project external-input manifest is missing"]
                ),
            }
        )
    return {
        "schema_version": "1.0",
        "manifest_path": str(manifest_path),
        "manifest_present": manifest_path.is_file(),
        "exact_case_count": len(cases),
        "catalog_input_count": len(EXTERNAL_INPUT_CATALOG),
        "status_counts": status_counts,
        "cases": cases,
        "inputs": inputs,
        "claim_guardrail": (
            "This matrix reports delegated-input readiness only. It does not "
            "prove VE generator, ApacheSim, APS comparison or SIA attestation "
            "readiness."
        ),
    }
