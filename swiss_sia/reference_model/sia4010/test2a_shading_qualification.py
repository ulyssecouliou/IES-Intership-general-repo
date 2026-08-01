"""Guarded CDB setter qualification for the SIA 4010 Test 2A awning.

The operation creates exactly one unassigned glazed construction in a saved
disposable project.  It writes and reads back only the external-shade active
flag and the two native irradiance-threshold fields.  It never edits layers,
assigns an opening, creates geometry, maps optical properties, runs ApacheSim
or claims dynamic equivalence.

This deliberately narrow probe answers one question safely: can the installed
VE build store the candidate Test 2A threshold fields through VEScripts?  The
separate equality/timestep/optical blockers remain open after a PASS.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Mapping, Optional, Sequence, Tuple

from ..exceptions import (
    ConfigurationError,
    VeApiUnavailableError,
    VeMutationError,
)
from .external_input_manifest import external_input_readiness
from .model_scenario import ModelScenario
from .normalized_external_inputs import load_test2a_external_bindings
from .official_input_contract import Sia4010OfficialInputContract
from .scenario_preflight import is_temporary_ve_project
from .test2a_shading_control import (
    DYNAMIC_EQUIVALENCE_BLOCKERS,
    FIXED_CLOSED_OUTPUT_BLOCKERS,
    FIXED_CLOSED_SETTER_FIELDS,
    SETTER_FIELDS,
    build_test2a_fabric_awning_control,
)


REPORT_SCHEMA_VERSION = "1.0"
SCENARIO_FILENAME = "sia_model_scenario.json"
REPORT_DIRECTORY = Path("sia4010_artifacts") / "diagnostics"
PROBE_MARKER = "SIA4010_TEST2A_EXTERNAL_SHADE_SETTER_PROBE"
FIXED_CLOSED_PROBE_MARKER = "SIA4010_TEST2A_2E1_OPTICAL_SETTER_PROBE"


def _sha256(path: Path) -> str:
    """Return a lowercase SHA-256 digest."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write deterministic UTF-8 JSON atomically."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _resolve_path(root: Any, path: str) -> Any:
    """Resolve one dotted attribute path."""

    current = root
    for part in path.split("."):
        if not hasattr(current, part):
            raise AttributeError(path)
        current = getattr(current, part)
    return current


def _resolve_enum(
    iesve_module: Any,
    container_paths: Sequence[str],
    member_names: Sequence[str],
    context: str,
) -> Any:
    """Resolve an enum member across supported VE 2025 layouts."""

    attempted = []
    for container_path in container_paths:
        try:
            container = _resolve_path(iesve_module, container_path)
        except AttributeError:
            attempted.append(container_path)
            continue
        for member_name in member_names:
            if hasattr(container, member_name):
                return getattr(container, member_name)
        attempted.append(
            "{}.[{}]".format(container_path, ",".join(member_names))
        )
    raise VeApiUnavailableError(
        "Unable to resolve VE enum for {} (attempted {})".format(
            context, attempted
        )
    )


def _current_cdb_project(iesve_module: Any) -> Any:
    """Return the active project CDB through the observed VE 2025 API."""

    database_type = getattr(iesve_module, "VECdbDatabase", None)
    getter = getattr(database_type, "get_current_database", None)
    if not callable(getter):
        raise VeApiUnavailableError(
            "VECdbDatabase.get_current_database is unavailable"
        )
    database = getter()
    projects_method = getattr(database, "get_projects", None)
    if not callable(projects_method):
        raise VeApiUnavailableError("VECdbDatabase.get_projects is unavailable")
    projects = projects_method()
    candidates = []
    if isinstance(projects, Mapping):
        for values in projects.values():
            if isinstance(values, (list, tuple)):
                candidates.extend(values)
            elif values is not None:
                candidates.append(values)
    elif isinstance(projects, (list, tuple)):
        candidates.extend(projects)
    if not candidates:
        raise VeApiUnavailableError("No current project CDB is exposed")
    return candidates[0]


def _get_construction(
    cdb_project: Any,
    identifier: Any,
    construction_class: Any,
) -> Optional[Any]:
    """Resolve a construction across the observed Boost.Python overloads."""

    for arguments in ((identifier, construction_class), (identifier,)):
        try:
            construction = cdb_project.get_construction(*arguments)
            if construction is not None:
                return construction
        except Exception:
            continue
    return None


def _glazed_ids(cdb_project: Any, construction_class: Any) -> Tuple[str, ...]:
    """Return a stable snapshot of current glazed construction identifiers."""

    try:
        return tuple(
            str(identifier)
            for identifier in cdb_project.get_construction_ids(
                construction_class
            )
        )
    except Exception as exc:
        raise VeApiUnavailableError(
            "Unable to inspect glazed construction identifiers: {}".format(exc)
        ) from exc


def _matching_marker_ids(
    cdb_project: Any,
    construction_class: Any,
    marker: str = PROBE_MARKER,
) -> Tuple[str, ...]:
    """Return existing probe objects so reruns fail before the first setter."""

    matches = []
    for identifier in _glazed_ids(cdb_project, construction_class):
        construction = _get_construction(
            cdb_project, identifier, construction_class
        )
        if construction is None:
            continue
        try:
            properties = dict(construction.get_properties())
        except Exception:
            continue
        if str(properties.get("description", "")) == marker:
            matches.append(identifier)
    return tuple(matches)


def _coerce_active_value(current: Any) -> Any:
    """Return an enabled value with the exact primitive type exposed by VE."""

    if isinstance(current, bool):
        return True
    if isinstance(current, int):
        return 1
    if isinstance(current, float):
        return 1.0
    raise VeApiUnavailableError(
        "external_shade_active has unsupported runtime type {}".format(
            type(current).__name__
        )
    )


def _values_match(expected: Any, actual: Any) -> bool:
    """Compare primitive CDB values after one float32 storage round trip."""

    if isinstance(expected, bool):
        return bool(actual) is expected
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return math.isclose(
            float(expected),
            float(actual),
            rel_tol=1.0e-7,
            abs_tol=1.0e-9,
        )
    return expected == actual


def _assert_subset(
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
) -> None:
    """Fail if any written shade field is absent or changed on read-back."""

    mismatches = {
        key: {"expected": value, "actual": actual.get(key)}
        for key, value in expected.items()
        if key not in actual or not _values_match(value, actual.get(key))
    }
    if mismatches:
        raise VeMutationError(
            "Test 2A external-shade setter read-back mismatch: {}".format(
                mismatches
            )
        )


def _create_setter_probe(
    iesve_module: Any,
    cdb_project: Any,
    setter_plan: Mapping[str, Any],
    on_mutation_start: Optional[Callable[[], None]] = None,
) -> Dict[str, Any]:
    """Create one unassigned glazed CDB object and verify the narrow setters."""

    construction_class = _resolve_enum(
        iesve_module,
        ("VECdbProject.construction_class", "construction_class"),
        ("glazed",),
        "glazed construction class",
    )
    category = _resolve_enum(
        iesve_module,
        ("VECdbProject.element_categories", "element_categories"),
        ("ext_glazing",),
        "external glazing category",
    )
    existing_probe_ids = _matching_marker_ids(
        cdb_project, construction_class
    )
    if existing_probe_ids:
        raise VeMutationError(
            "Test 2A shade setter probe already exists: {}".format(
                list(existing_probe_ids)
            )
        )

    before_ids = _glazed_ids(cdb_project, construction_class)
    if on_mutation_start is not None:
        on_mutation_start()
    try:
        construction = cdb_project.create_construction(category)
        construction.set_const_class(construction_class)
    except Exception as exc:
        raise VeMutationError(
            "Unable to create the unassigned glazed setter probe: {}".format(exc)
        ) from exc

    try:
        before_properties = dict(construction.get_properties())
    except Exception as exc:
        raise VeApiUnavailableError(
            "Unable to read new glazed construction properties: {}".format(exc)
        ) from exc
    missing_fields = sorted(set(SETTER_FIELDS) - set(before_properties))
    if missing_fields:
        raise VeApiUnavailableError(
            "New glazed construction is missing Test 2A shade fields: {}".format(
                missing_fields
            )
        )

    properties = {
        "external_shade_active": _coerce_active_value(
            before_properties["external_shade_active"]
        ),
        "external_shade_radiation_to_lower": float(
            setter_plan["external_shade_radiation_to_lower"]
        ),
        "external_shade_radiation_to_raise": float(
            setter_plan["external_shade_radiation_to_raise"]
        ),
    }
    if "description" in before_properties:
        properties["description"] = PROBE_MARKER
    try:
        construction.set_properties(properties)
        after_properties = dict(construction.get_properties())
    except Exception as exc:
        raise VeMutationError(
            "Test 2A external-shade setter call failed: {}".format(exc)
        ) from exc
    _assert_subset(properties, after_properties)

    after_ids = _glazed_ids(cdb_project, construction_class)
    new_ids = [identifier for identifier in after_ids if identifier not in before_ids]
    identifier = str(getattr(construction, "id", ""))
    if not identifier and len(new_ids) == 1:
        identifier = new_ids[0]
    if not identifier:
        raise VeMutationError(
            "The Test 2A shade setter probe has no persistent construction ID"
        )
    try:
        layer_count = len(list(construction.get_layers()))
    except Exception:
        layer_count = None
    return {
        "construction_id": identifier,
        "before_properties": {
            key: before_properties.get(key)
            for key in sorted(set(properties) | {"external_shade_profile"})
        },
        "written_properties": properties,
        "after_properties": {
            key: after_properties.get(key)
            for key in sorted(set(properties) | {"external_shade_profile"})
        },
        "before_glazed_ids": list(before_ids),
        "after_glazed_ids": list(after_ids),
        "new_glazed_ids": new_ids,
        "default_layer_count_unchanged_by_probe": layer_count,
        "layers_edited": False,
        "opening_assignment_performed": False,
    }


def _validated_threshold_setter_report(project_path: Path) -> Path:
    """Return the checksummed PASS prerequisite for the optical probe."""

    reports = sorted(
        (project_path / REPORT_DIRECTORY).glob(
            "sia2a_external_shade_setter_*.json"
        )
    )
    if len(reports) != 1:
        raise ConfigurationError(
            "The 2E1 optical setter probe requires exactly one prior threshold "
            "setter report in this disposable project; found {}".format(
                len(reports)
            )
        )
    report_path = reports[0]
    checksum_path = report_path.with_suffix(report_path.suffix + ".sha256")
    if not checksum_path.is_file():
        raise ConfigurationError(
            "Threshold setter report checksum is missing: {}".format(
                checksum_path
            )
        )
    expected_sha = checksum_path.read_text(
        encoding="ascii"
    ).split(maxsplit=1)[0].lower()
    if expected_sha != _sha256(report_path):
        raise ConfigurationError(
            "Threshold setter report checksum mismatch: {}".format(
                report_path
            )
        )
    try:
        payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConfigurationError(
            "Threshold setter report is invalid: {}".format(exc)
        ) from exc
    if (
        payload.get("status") != "PASS"
        or payload.get("cdb_setter_qualified") is not True
        or payload.get("dynamic_equivalence_qualified") is not False
    ):
        raise ConfigurationError(
            "Threshold setter prerequisite is not a narrow qualified PASS"
        )
    return report_path


def _create_fixed_closed_optical_probe(
    iesve_module: Any,
    cdb_project: Any,
    setter_plan: Mapping[str, Any],
    on_mutation_start: Optional[Callable[[], None]] = None,
) -> Dict[str, Any]:
    """Create one unassigned 2E1 candidate and verify direct-name fields."""

    construction_class = _resolve_enum(
        iesve_module,
        ("VECdbProject.construction_class", "construction_class"),
        ("glazed",),
        "glazed construction class",
    )
    category = _resolve_enum(
        iesve_module,
        ("VECdbProject.element_categories", "element_categories"),
        ("ext_glazing",),
        "external glazing category",
    )
    existing_probe_ids = _matching_marker_ids(
        cdb_project,
        construction_class,
        FIXED_CLOSED_PROBE_MARKER,
    )
    if existing_probe_ids:
        raise VeMutationError(
            "Test 2A 2E1 optical setter probe already exists: {}".format(
                list(existing_probe_ids)
            )
        )
    before_ids = _glazed_ids(cdb_project, construction_class)
    if on_mutation_start is not None:
        on_mutation_start()
    try:
        construction = cdb_project.create_construction(category)
        construction.set_const_class(construction_class)
        before_properties = dict(construction.get_properties())
    except Exception as exc:
        raise VeMutationError(
            "Unable to create/read the unassigned 2E1 optical probe: {}".format(
                exc
            )
        ) from exc
    missing_fields = sorted(
        set(FIXED_CLOSED_SETTER_FIELDS) - set(before_properties)
    )
    if missing_fields:
        raise VeApiUnavailableError(
            "New glazed construction is missing 2E1 optical fields: {}".format(
                missing_fields
            )
        )
    if not isinstance(before_properties["external_shade_profile"], str):
        raise VeApiUnavailableError(
            "external_shade_profile has unsupported runtime type {}".format(
                type(before_properties["external_shade_profile"]).__name__
            )
        )
    properties = {
        "external_shade_active": _coerce_active_value(
            before_properties["external_shade_active"]
        ),
        "external_shade_profile": str(
            setter_plan["external_shade_profile"]
        ),
        "external_shade_transmittance_0": float(
            setter_plan["external_shade_transmittance_0"]
        ),
        "external_shade_solar_reflectance": float(
            setter_plan["external_shade_solar_reflectance"]
        ),
        "external_shade_visible_reflectance": float(
            setter_plan["external_shade_visible_reflectance"]
        ),
    }
    if "description" in before_properties:
        properties["description"] = FIXED_CLOSED_PROBE_MARKER
    try:
        construction.set_properties(properties)
        after_properties = dict(construction.get_properties())
    except Exception as exc:
        raise VeMutationError(
            "Test 2A 2E1 optical setter call failed: {}".format(exc)
        ) from exc
    _assert_subset(properties, after_properties)
    after_ids = _glazed_ids(cdb_project, construction_class)
    new_ids = [
        identifier for identifier in after_ids if identifier not in before_ids
    ]
    identifier = str(getattr(construction, "id", ""))
    if not identifier and len(new_ids) == 1:
        identifier = new_ids[0]
    if not identifier:
        raise VeMutationError(
            "The Test 2A 2E1 optical probe has no persistent construction ID"
        )
    try:
        layer_count = len(list(construction.get_layers()))
    except Exception:
        layer_count = None
    return {
        "construction_id": identifier,
        "before_properties": {
            key: before_properties.get(key)
            for key in sorted(properties)
        },
        "written_properties": properties,
        "after_properties": {
            key: after_properties.get(key)
            for key in sorted(properties)
        },
        "before_glazed_ids": list(before_ids),
        "after_glazed_ids": list(after_ids),
        "new_glazed_ids": new_ids,
        "default_layer_count_unchanged_by_probe": layer_count,
        "layers_edited": False,
        "opening_assignment_performed": False,
    }


def qualify_test2a_shading_setters(
    iesve_module: Any,
    project: Any,
    repository_root: Optional[Path] = None,
) -> Path:
    """Create and read back one source-bound Test 2A CDB setter probe."""

    project_path = Path(str(getattr(project, "path", "")))
    if not project_path.is_dir():
        raise ConfigurationError(
            "Test 2A shade qualification requires a saved VE project directory"
        )
    if is_temporary_ve_project(project_path):
        raise ConfigurationError(
            "Save a fresh disposable VE project outside the temporary VEPROJ "
            "folder before shade qualification"
        )

    scenario_path = project_path / SCENARIO_FILENAME
    if not scenario_path.is_file():
        raise ConfigurationError(
            "Prepare test_2A/2A first; missing scenario file: {}".format(
                scenario_path
            )
        )
    scenario = ModelScenario.load(scenario_path)
    if (
        not scenario.is_official
        or scenario.variant != "test_2A"
        or scenario.case_id != "2A"
    ):
        raise ConfigurationError(
            "Shade qualification is restricted to the official test_2A/2A "
            "scenario"
        )
    prior_reports = sorted(
        (
            project_path / REPORT_DIRECTORY
        ).glob("sia2a_external_shade_setter_*.json")
    )
    if prior_reports:
        raise ConfigurationError(
            "A Test 2A shade setter qualification was already started in this "
            "project. Discard it and use a fresh disposable project: {}".format(
                prior_reports[-1]
            )
        )

    readiness = external_input_readiness(project_path, "test_2A", "2A")
    bindings = load_test2a_external_bindings(readiness)
    root = (
        Path(repository_root)
        if repository_root is not None
        else Path(__file__).resolve().parents[3]
    )
    official_contract_path = (
        root / "config" / "sia4010_official_input_contract.json"
    )
    official_contract = Sia4010OfficialInputContract.load(
        official_contract_path
    )
    official_inputs = official_contract.test("2").confirmed_inputs
    control = build_test2a_fabric_awning_control(official_inputs)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    report_path = (
        project_path
        / REPORT_DIRECTORY
        / "sia2a_external_shade_setter_{}.json".format(timestamp)
    )
    report: Dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "qualification_kind": "SIA4010_TEST2A_EXTERNAL_SHADE_CDB_SETTER",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "STARTED",
        "project": {
            "name": str(getattr(project, "name", "")),
            "path": str(project_path),
        },
        "scenario": scenario.to_dict(),
        "source_contracts": {
            "scenario": {
                "path": str(scenario_path),
                "sha256": _sha256(scenario_path),
            },
            "official_test2_contract": {
                "path": str(official_contract_path),
                "sha256": _sha256(official_contract_path),
            },
            "normalized_binding_sha256": dict(bindings.evidence_sha256),
        },
        "fabric_awning_control": control.to_dict(),
        "setter_result": {},
        "mutation_scope": "ONE_UNASSIGNED_GLAZED_CDB_CONSTRUCTION",
        "mutation_performed": False,
        "geometry_changed": False,
        "opening_assignment_performed": False,
        "layers_changed": False,
        "optical_mapping_performed": False,
        "simulation_performed": False,
        "cdb_setter_qualified": False,
        "dynamic_equivalence_qualified": False,
        "full_test2a_mutation_authorized": False,
        "compliance_claim_allowed": False,
        "remaining_blockers": list(DYNAMIC_EQUIVALENCE_BLOCKERS),
        "claim_guardrail": (
            "A PASS qualifies only storage/read-back of the active flag and "
            "two threshold fields in this installed VE build. It does not "
            "qualify equality behaviour, timestep state handling, Soltis "
            "optics, a Test 2A model, a simulation result or SIA validation."
        ),
    }
    _write_json(report_path, report)
    try:
        cdb_project = _current_cdb_project(iesve_module)

        def mark_mutation_started() -> None:
            report.update(
                {
                    "status": "MUTATION_STARTED",
                    "mutation_boundary_entered": True,
                }
            )
            _write_json(report_path, report)

        setter_result = _create_setter_probe(
            iesve_module,
            cdb_project,
            control.setter_plan,
            on_mutation_start=mark_mutation_started,
        )
        report.update(
            {
                "status": "PASS",
                "setter_result": setter_result,
                "mutation_performed": True,
                "cdb_setter_qualified": True,
            }
        )
    except Exception as exc:
        report.update(
            {
                "status": "FAIL",
                "error": "{}: {}".format(type(exc).__name__, exc),
                "mutation_performed": bool(
                    report.get("mutation_boundary_entered", False)
                ),
                "mutation_state": (
                    "UNKNOWN_AFTER_MUTATION_BOUNDARY"
                    if report.get("mutation_boundary_entered", False)
                    else "NO_MUTATION_BOUNDARY_ENTERED"
                ),
                "recovery_action": (
                    "Discard this project and repeat only in a fresh saved "
                    "disposable VE project after correcting the reported cause."
                ),
            }
        )
        _write_json(report_path, report)
        raise

    _write_json(report_path, report)
    checksum_path = report_path.with_suffix(report_path.suffix + ".sha256")
    checksum_path.write_text(
        "{}  {}\n".format(_sha256(report_path), report_path.name),
        encoding="ascii",
    )
    return report_path


def qualify_test2a_2e1_optical_setters(
    iesve_module: Any,
    project: Any,
    repository_root: Optional[Path] = None,
) -> Path:
    """Qualify only direct-name fixed-closed CDB storage for diagnostic 2E1."""

    project_path = Path(str(getattr(project, "path", "")))
    if not project_path.is_dir():
        raise ConfigurationError(
            "Test 2A 2E1 optical qualification requires a saved project"
        )
    if is_temporary_ve_project(project_path):
        raise ConfigurationError(
            "Save a fresh disposable VE project outside the temporary VEPROJ "
            "folder before 2E1 optical qualification"
        )
    scenario_path = project_path / SCENARIO_FILENAME
    if not scenario_path.is_file():
        raise ConfigurationError(
            "Prepare test_2A/2A first; missing scenario file: {}".format(
                scenario_path
            )
        )
    scenario = ModelScenario.load(scenario_path)
    if (
        not scenario.is_official
        or scenario.variant != "test_2A"
        or scenario.case_id != "2A"
    ):
        raise ConfigurationError(
            "2E1 optical setter qualification is restricted to test_2A/2A"
        )
    prior_optical_reports = sorted(
        (project_path / REPORT_DIRECTORY).glob(
            "sia2a_2e1_optical_setter_*.json"
        )
    )
    if prior_optical_reports:
        raise ConfigurationError(
            "A 2E1 optical setter qualification was already started in this "
            "project. Discard it before another attempt: {}".format(
                prior_optical_reports[-1]
            )
        )
    threshold_report = _validated_threshold_setter_report(project_path)
    readiness = external_input_readiness(project_path, "test_2A", "2A")
    bindings = load_test2a_external_bindings(readiness)
    root = (
        Path(repository_root)
        if repository_root is not None
        else Path(__file__).resolve().parents[3]
    )
    official_contract_path = (
        root / "config" / "sia4010_official_input_contract.json"
    )
    official_contract = Sia4010OfficialInputContract.load(
        official_contract_path
    )
    control = build_test2a_fabric_awning_control(
        official_contract.test("2").confirmed_inputs
    )
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    report_path = (
        project_path
        / REPORT_DIRECTORY
        / "sia2a_2e1_optical_setter_{}.json".format(timestamp)
    )
    report: Dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "qualification_kind": (
            "SIA4010_TEST2A_2E1_FIXED_CLOSED_OPTICAL_CDB_SETTER"
        ),
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "STARTED",
        "project": {
            "name": str(getattr(project, "name", "")),
            "path": str(project_path),
        },
        "scenario": scenario.to_dict(),
        "diagnostic_case_id": "2E1",
        "protection_state": "ALWAYS_CLOSED",
        "source_contracts": {
            "scenario": {
                "path": str(scenario_path),
                "sha256": _sha256(scenario_path),
            },
            "official_test2_contract": {
                "path": str(official_contract_path),
                "sha256": _sha256(official_contract_path),
            },
            "threshold_setter_report": {
                "path": str(threshold_report),
                "sha256": _sha256(threshold_report),
            },
            "normalized_binding_sha256": dict(bindings.evidence_sha256),
        },
        "candidate_setter_plan": (
            control.fixed_closed_candidate_setter_plan
        ),
        "setter_plan_scope": (
            "DIRECT_NAME_MATCH_STORAGE_AND_READBACK_ONLY"
        ),
        "setter_result": {},
        "mutation_scope": "ONE_UNASSIGNED_GLAZED_CDB_CONSTRUCTION",
        "mutation_performed": False,
        "geometry_changed": False,
        "opening_assignment_performed": False,
        "layers_changed": False,
        "simulation_performed": False,
        "fixed_closed_storage_qualified": False,
        "fixed_closed_optical_mapping_qualified": False,
        "dynamic_equivalence_qualified": False,
        "diagnostic_candidate_generation_authorized": False,
        "compliance_claim_allowed": False,
        "remaining_blockers": list(FIXED_CLOSED_OUTPUT_BLOCKERS),
        "claim_guardrail": (
            "A PASS qualifies storage/read-back only for the direct-name "
            "normal-incidence/outside-reflectance fields and ON profile. "
            "Angular optics, inside reflectance, visible transmission, "
            "secondary heat transfer and 2E1 APS equivalence remain open."
        ),
    }
    _write_json(report_path, report)
    try:
        cdb_project = _current_cdb_project(iesve_module)

        def mark_mutation_started() -> None:
            report.update(
                {
                    "status": "MUTATION_STARTED",
                    "mutation_boundary_entered": True,
                }
            )
            _write_json(report_path, report)

        result = _create_fixed_closed_optical_probe(
            iesve_module,
            cdb_project,
            control.fixed_closed_candidate_setter_plan,
            on_mutation_start=mark_mutation_started,
        )
        report.update(
            {
                "status": "PASS",
                "setter_result": result,
                "mutation_performed": True,
                "fixed_closed_storage_qualified": True,
            }
        )
    except Exception as exc:
        report.update(
            {
                "status": "FAIL",
                "error": "{}: {}".format(type(exc).__name__, exc),
                "mutation_performed": bool(
                    report.get("mutation_boundary_entered", False)
                ),
                "mutation_state": (
                    "UNKNOWN_AFTER_MUTATION_BOUNDARY"
                    if report.get("mutation_boundary_entered", False)
                    else "NO_MUTATION_BOUNDARY_ENTERED"
                ),
                "recovery_action": (
                    "Discard this project and repeat the full threshold then "
                    "2E1 optical qualification in a fresh saved project."
                ),
            }
        )
        _write_json(report_path, report)
        raise
    _write_json(report_path, report)
    report_path.with_suffix(report_path.suffix + ".sha256").write_text(
        "{}  {}\n".format(_sha256(report_path), report_path.name),
        encoding="ascii",
    )
    return report_path
