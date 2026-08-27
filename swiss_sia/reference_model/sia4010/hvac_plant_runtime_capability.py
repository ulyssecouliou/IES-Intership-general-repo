"""Read-only VE runtime discovery for SIA 4010 Tests 4 to 7.

These tests require detailed air-side, control, hydronic, storage, generation
and PV capabilities.  The public VEScript surface differs between VE releases,
so no mutation is authorised until the installed runtime has been inventoried.
Only known getters and public-member discovery are used here; the probe never
creates, sets, assigns, saves or simulates anything.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from ..exceptions import ConfigurationError
from .external_input_manifest import external_input_readiness
from .model_scenario import ModelScenario
from .official_input_contract import Sia4010OfficialInputContract

REPORT_SCHEMA_VERSION = "1.0"
REPORT_DIRECTORY = Path("sia4010_artifacts") / "diagnostics"
SCENARIO_FILENAME = "sia_model_scenario.json"
EXACT_CASES = (
    ("test_4", "4"),
    ("test_5A", "5A"),
    ("test_5B", "5B"),
    ("test_5C", "5C"),
    ("test_5D", "5D"),
    ("test_6", "6"),
    ("test_7", "7"),
)
HVAC_TOKENS = (
    "apache",
    "hvac",
    "system",
    "air",
    "fan",
    "duct",
    "coil",
    "recovery",
    "humid",
    "control",
    "network",
)
PLANT_TOKENS = (
    "plant",
    "boiler",
    "chiller",
    "heat_pump",
    "storage",
    "tank",
    "photovoltaic",
    "pv",
    "energy",
    "meter",
    "system",
    "network",
)


def _sha256(path: Path) -> str:
    """Return the SHA-256 digest of one source or diagnostic artifact."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write one JSON diagnostic atomically to the requested path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _jsonable(value: Any, depth: int = 0) -> Any:
    """Convert bounded runtime API values into JSON-safe evidence."""

    if depth > 3:
        return repr(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {
            str(key): _jsonable(item, depth + 1)
            for key, item in list(value.items())[:100]
        }
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(item, depth + 1) for item in list(value)[:100]]
    return str(value)


def _as_sequence(value: Any) -> Sequence[Any]:
    """Return an iterable runtime value as a defensive immutable sequence."""

    if value is None or isinstance(value, (str, bytes)):
        return ()
    try:
        return tuple(value)
    except Exception:
        return ()


def _public_members(value: Any, tokens: Iterable[str]) -> List[str]:
    """List public runtime members whose names match relevant API tokens."""

    if value is None:
        return []
    try:
        names = dir(value)
    except Exception:
        return []
    lowered = tuple(str(token).lower() for token in tokens)
    return sorted(
        name
        for name in names
        if not name.startswith("_") and any(token in name.lower() for token in lowered)
    )


def _read_mapping(owner: Any, getter_name: str) -> Dict[str, Any]:
    """Call one explicitly allow-listed, parameterless read method."""

    getter = getattr(owner, getter_name, None)
    if not callable(getter):
        return {"available": False, "data": {}, "error": ""}
    try:
        value = getter()
        if not isinstance(value, Mapping):
            return {
                "available": True,
                "data": {},
                "error": "{} returned {}".format(getter_name, type(value).__name__),
            }
        return {
            "available": True,
            "data": _jsonable(dict(value)),
            "error": "",
        }
    except Exception as exc:
        return {
            "available": True,
            "data": {},
            "error": "{}: {}".format(type(exc).__name__, exc),
        }


def _apache_system_inventory(project: Any) -> Dict[str, Any]:
    """Inspect Apache Systems through allow-listed read-only API access."""

    result: Dict[str, Any] = {
        "collection_available": callable(getattr(project, "apache_systems", None)),
        "creation_member_observed": callable(
            getattr(project, "create_apache_system", None)
        ),
        "systems": [],
        "errors": [],
    }
    if not result["collection_available"]:
        return result
    try:
        systems = _as_sequence(project.apache_systems())
    except Exception as exc:
        result["errors"].append("VEProject.apache_systems: {}".format(exc))
        return result
    for system in systems:
        readback = _read_mapping(system, "get")
        result["systems"].append(
            {
                "identifier": str(getattr(system, "id", "")),
                "name": str(getattr(system, "name", "")),
                "python_type": "{}.{}".format(
                    type(system).__module__, type(system).__name__
                ),
                "relevant_members": sorted(
                    set(_public_members(system, HVAC_TOKENS))
                    | set(_public_members(system, PLANT_TOKENS))
                ),
                "readback": readback,
            }
        )
    return result


def _room_system_inventory(project: Any) -> Dict[str, Any]:
    """Inspect room-level Apache system assignments without changing VE."""

    result: Dict[str, Any] = {"rooms": [], "errors": []}
    models = _as_sequence(getattr(project, "models", ()))
    if not models:
        result["errors"].append("No active VE model is exposed")
        return result
    get_bodies = getattr(models[0], "get_bodies", None)
    if not callable(get_bodies):
        result["errors"].append("VEModel.get_bodies is unavailable")
        return result
    try:
        bodies = _as_sequence(get_bodies(False))
    except Exception as exc:
        result["errors"].append("VEModel.get_bodies(False): {}".format(exc))
        return result
    for body in bodies:
        get_room_data = getattr(body, "get_room_data", None)
        if not callable(get_room_data):
            continue
        room_name = str(getattr(body, "name", getattr(body, "id", "")))
        try:
            room_data = get_room_data()
        except Exception as exc:
            result["errors"].append("room {} get_room_data: {}".format(room_name, exc))
            continue
        result["rooms"].append(
            {
                "name": room_name,
                "room_data_type": "{}.{}".format(
                    type(room_data).__module__, type(room_data).__name__
                ),
                "relevant_members": sorted(
                    set(_public_members(room_data, HVAC_TOKENS))
                    | set(_public_members(room_data, PLANT_TOKENS))
                ),
                "apache_systems": _read_mapping(room_data, "get_apache_systems"),
                "room_conditions": _read_mapping(room_data, "get_room_conditions"),
            }
        )
    return result


def _module_inventory(iesve_module: Any) -> Dict[str, Any]:
    """Inventory HVAC and plant symbols exposed by the loaded iesve module."""

    hvac_members = _public_members(iesve_module, HVAC_TOKENS)
    plant_members = _public_members(iesve_module, PLANT_TOKENS)
    return {
        "hvac_related_members": hvac_members,
        "plant_related_members": plant_members,
        "symbols": [
            {
                "name": name,
                "python_type": "{}.{}".format(
                    type(getattr(iesve_module, name)).__module__,
                    type(getattr(iesve_module, name)).__name__,
                ),
                "relevant_members": sorted(
                    set(_public_members(getattr(iesve_module, name), HVAC_TOKENS))
                    | set(_public_members(getattr(iesve_module, name), PLANT_TOKENS))
                ),
            }
            for name in sorted(set(hvac_members) | set(plant_members))
        ],
    }


def _source_readiness(project_path: Path, variant: str, case_id: str) -> Dict[str, Any]:
    """Return delegated-source readiness for one exact official case."""

    try:
        readiness = external_input_readiness(project_path, variant, case_id)
        return {
            "available": True,
            "ready_for_binding": readiness.ready_for_binding,
            "status": readiness.status,
            "details": readiness.to_dict(),
        }
    except Exception as exc:
        return {
            "available": False,
            "ready_for_binding": False,
            "status": "UNAVAILABLE",
            "error": "{}: {}".format(type(exc).__name__, exc),
        }


def _official_contract(repository_root: Path) -> Dict[str, Any]:
    """Load the source-traced official input contract for Tests 4 to 7."""

    path = repository_root / "config" / "sia4010_official_input_contract.json"
    contract = Sia4010OfficialInputContract.load(path)
    tests = {}
    for test_id in ("4", "5", "6", "7"):
        record = contract.test(test_id)
        tests[test_id] = {
            "source": record.source,
            "source_pages": list(record.source_pages),
            "confirmed_inputs": dict(record.confirmed_inputs),
            "unresolved_dependencies": list(record.unresolved_dependencies),
        }
    return {"path": str(path), "sha256": _sha256(path), "tests": tests}


def _case_matrix(
    source_matrix: Mapping[str, Mapping[str, Any]],
    *,
    apache_system_api_observed: bool,
    room_system_api_observed: bool,
    plant_api_observed: bool,
) -> List[Dict[str, Any]]:
    """Build fail-closed runtime capability rows for Tests 4 to 7."""

    rows = []
    for variant, case_id in EXACT_CASES:
        source_ready = source_matrix[case_id]["ready_for_binding"] is True
        blockers = []
        if not source_ready:
            blockers.append(
                "TEST{}_EXTERNAL_SOURCE_BINDINGS_NOT_READY".format(case_id[0])
            )
        if case_id[0] in {"4", "5", "6"}:
            if not apache_system_api_observed:
                blockers.append("VEPROJECT_APACHE_SYSTEMS_API_NOT_OBSERVED")
            if not room_system_api_observed:
                blockers.append("ROOM_APACHE_SYSTEM_READBACK_NOT_OBSERVED")
            blockers.append("APACHEHVAC_TOPOLOGY_SETTERS_NOT_QUALIFIED")
        else:
            if not plant_api_observed:
                blockers.append("VE_PLANT_ENERGY_API_NOT_OBSERVED")
            blockers.append("PLANT_STORAGE_PV_SETTERS_NOT_QUALIFIED")
        blockers.append("APS_RESULT_BINDINGS_NOT_QUALIFIED")
        rows.append(
            {
                "variant": variant,
                "case_id": case_id,
                "technical_blockers": blockers,
                "mutation_authorized": False,
            }
        )
    return rows


def build_hvac_plant_runtime_capability_report(
    iesve_module: Any,
    project: Any,
    repository_root: Path,
) -> Dict[str, Any]:
    """Build a fail-closed capability report for one prepared Test 4-7 case."""

    project_path = Path(str(getattr(project, "path", "")))
    scenario_path = project_path / SCENARIO_FILENAME
    if not scenario_path.is_file():
        raise ConfigurationError(
            "Prepare one official Test 4-7 case first; missing scenario: {}".format(
                scenario_path
            )
        )
    scenario = ModelScenario.load(scenario_path)
    if (
        not scenario.is_official
        or (scenario.variant, scenario.case_id) not in EXACT_CASES
    ):
        raise ConfigurationError(
            "HVAC/plant runtime probe requires one exact official Test 4, "
            "5A-5D, 6 or 7 scenario"
        )

    systems = _apache_system_inventory(project)
    rooms = _room_system_inventory(project)
    module = _module_inventory(iesve_module)
    project_members = sorted(
        set(_public_members(project, HVAC_TOKENS))
        | set(_public_members(project, PLANT_TOKENS))
    )
    apache_observed = bool(
        systems["collection_available"] or "apache_systems" in project_members
    )
    room_system_observed = any(
        row["apache_systems"]["available"] for row in rooms["rooms"]
    )
    plant_specific = {
        name
        for name in module["plant_related_members"] + project_members
        if any(token in name.lower() for token in PLANT_TOKENS[:-2])
    }
    source_matrix = {
        case_id: _source_readiness(project_path, variant, case_id)
        for variant, case_id in EXACT_CASES
    }
    matrix = _case_matrix(
        source_matrix,
        apache_system_api_observed=apache_observed,
        room_system_api_observed=room_system_observed,
        plant_api_observed=bool(plant_specific),
    )
    selected = next(row for row in matrix if row["case_id"] == scenario.case_id)
    blockers = list(selected["technical_blockers"])
    qualification_blockers = [
        item
        for item in blockers
        if item
        not in {
            "APS_RESULT_BINDINGS_NOT_QUALIFIED",
            "APACHEHVAC_TOPOLOGY_SETTERS_NOT_QUALIFIED",
            "PLANT_STORAGE_PV_SETTERS_NOT_QUALIFIED",
        }
    ]
    source = source_matrix[scenario.case_id]
    if not source["ready_for_binding"]:
        status = "SOURCE_BINDINGS_REQUIRED"
    elif qualification_blockers:
        status = "READ_ONLY_EVIDENCE_INCOMPLETE"
    else:
        status = "READY_FOR_DISPOSABLE_MUTATION_QUALIFICATION"

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": status,
        "project": {
            "name": str(getattr(project, "name", "")),
            "path": str(project_path),
            "version": (
                str(project.get_version())
                if callable(getattr(project, "get_version", None))
                else "unavailable"
            ),
        },
        "scenario": scenario.to_dict(),
        "official_contract": _official_contract(Path(repository_root)),
        "source_binding": source,
        "source_binding_matrix": source_matrix,
        "project_relevant_members": project_members,
        "apache_system_api": systems,
        "room_system_api": rooms,
        "iesve_module_api": module,
        "observed_capabilities": {
            "apache_system_collection": apache_observed,
            "room_apache_system_readback": room_system_observed,
            "plant_specific_members": sorted(plant_specific),
        },
        "case_capability_matrix": matrix,
        "selected_case_capability": selected,
        "technical_blockers": blockers,
        "setter_qualification_blockers": qualification_blockers,
        "mutation_performed": False,
        "mutation_authorized": False,
        "simulation_performed": False,
        "compliance_claim_allowed": False,
        "next_action": (
            "Use this evidence to design narrow disposable-project setter "
            "qualifications for the selected topology. Do not infer support "
            "for ducts, controls, hydronic plant, storage or PV from names alone."
        ),
        "claim_guardrail": (
            "This getter-only inventory is not a model, simulation, result "
            "comparison, validation or SIA compliance attestation."
        ),
    }


def write_hvac_plant_runtime_capability_report(
    iesve_module: Any,
    project: Any,
    repository_root: Path,
) -> Path:
    """Persist the report and a SHA-256 sidecar in the active VE project."""

    payload = build_hvac_plant_runtime_capability_report(
        iesve_module, project, repository_root
    )
    project_path = Path(payload["project"]["path"])
    output_path = (
        project_path
        / REPORT_DIRECTORY
        / "sia4010_tests4_7_runtime_capability_{}.json".format(
            datetime.now().strftime("%Y%m%d_%H%M%S")
        )
    )
    _write_json(output_path, payload)
    output_path.with_suffix(output_path.suffix + ".sha256").write_text(
        "{}  {}\n".format(_sha256(output_path), output_path.name),
        encoding="ascii",
    )
    return output_path
