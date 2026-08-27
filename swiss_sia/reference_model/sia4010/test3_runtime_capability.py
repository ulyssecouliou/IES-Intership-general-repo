"""Read-only VE runtime discovery for SIA 4010 Test 3 lighting controls.

The official Test 3 source contract defines twelve exact shade/lighting
combinations, but the installed IESVE Python API must be observed before any
sensor or control setter is used.  This module calls getters and parameterless
read methods only.  It never creates, sets, assigns, saves or simulates.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Set, Tuple

from ..exceptions import ConfigurationError
from ..ve_compat import thermal_templates
from .external_input_manifest import external_input_readiness
from .model_scenario import ModelScenario
from .official_input_contract import Sia4010OfficialInputContract

REPORT_SCHEMA_VERSION = "1.0"
REPORT_DIRECTORY = Path("sia4010_artifacts") / "diagnostics"
SCENARIO_FILENAME = "sia_model_scenario.json"
TEST3_VARIANTS = tuple("test_3{}".format(letter) for letter in "ABCDEFGHIJKL")
REQUIRED_LIGHTING_FIELDS = frozenset(
    {
        "variation_profile",
        "dimming_profile",
        "max_illuminance",
        "installed_power_density",
    }
)
LIGHTING_TOKENS = (
    "light",
    "lighting",
    "daylight",
    "illumin",
    "lux",
    "dimming",
    "sensor",
    "photocell",
)
SENSOR_TOKENS = (
    "daylight",
    "illumin",
    "lux",
    "sensor",
    "photocell",
)


def _sha256(path: Path) -> str:
    """Return the lowercase SHA-256 of one local artifact."""

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


def _jsonable(value: Any, depth: int = 0) -> Any:
    """Convert a bounded VE proxy value to JSON-safe evidence."""

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
    """Return one non-string VE collection as a tuple where possible."""

    if value is None or isinstance(value, (str, bytes)):
        return ()
    try:
        return tuple(value)
    except Exception:
        return ()


def _records(value: Any) -> Sequence[Any]:
    """Return record proxies from either VE sequences or ID mappings."""

    if isinstance(value, Mapping):
        return tuple(value.values())
    return _as_sequence(value)


def _public_members(value: Any, tokens: Iterable[str]) -> List[str]:
    """Return relevant public API names without invoking them."""

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


def _record_data(record: Any) -> Tuple[Dict[str, Any], str]:
    """Read one gain proxy through its getter and preserve errors."""

    getter = getattr(record, "get", None)
    if not callable(getter):
        return {}, "get() unavailable"
    try:
        value = getter()
        if not isinstance(value, Mapping):
            return {}, "get() returned {}".format(type(value).__name__)
        return dict(value), ""
    except Exception as exc:
        return {}, "{}: {}".format(type(exc).__name__, exc)


def _is_lighting_gain(record: Any, data: Mapping[str, Any]) -> bool:
    """Identify a lighting proxy from type and read-back labels only."""

    labels = (
        type(record).__name__,
        str(data.get("type_str", "")),
        str(data.get("name", "")),
    )
    return any("light" in label.lower() for label in labels)


def _lighting_record(record: Any, scope: str) -> Dict[str, Any]:
    """Return one bounded lighting-gain evidence record."""

    data, error = _record_data(record)
    row: Dict[str, Any] = {
        "scope": scope,
        "python_type": "{}.{}".format(type(record).__module__, type(record).__name__),
        "identifier": str(getattr(record, "id", "")),
        "name": str(data.get("name", getattr(record, "name", ""))),
        "is_lighting_gain": _is_lighting_gain(record, data),
        "setter_available": callable(getattr(record, "set", None)),
        "relevant_members": _public_members(record, LIGHTING_TOKENS),
        "property_keys": sorted(str(key) for key in data),
        "lighting_properties": {
            str(key): _jsonable(value)
            for key, value in data.items()
            if any(token in str(key).lower() for token in LIGHTING_TOKENS)
            or str(key) in REQUIRED_LIGHTING_FIELDS
        },
    }
    if error:
        row["read_error"] = error
    return row


def _global_gain_inventory(project: Any) -> Dict[str, Any]:
    """Inspect global casual gains without mutating their records."""

    result: Dict[str, Any] = {
        "casual_gains_available": callable(getattr(project, "casual_gains", None)),
        "create_casual_gain_available": callable(
            getattr(project, "create_casual_gain", None)
        ),
        "lighting_gains": [],
        "errors": [],
    }
    if not result["casual_gains_available"]:
        return result
    try:
        gains = _records(project.casual_gains())
    except Exception as exc:
        result["errors"].append("VEProject.casual_gains: {}".format(exc))
        return result
    for gain in gains:
        row = _lighting_record(gain, "project")
        if row["is_lighting_gain"]:
            result["lighting_gains"].append(row)
    return result


def _template_inventory(project: Any) -> Dict[str, Any]:
    """Inspect template gain contents through getter methods only."""

    result: Dict[str, Any] = {
        "templates": [],
        "lighting_gains": [],
        "errors": [],
    }
    try:
        templates = thermal_templates(project, assigned=False)
    except Exception as exc:
        result["errors"].append("VEProject.thermal_templates: {}".format(exc))
        return result
    for handle, template in templates.items():
        template_row = {
            "handle": str(handle),
            "name": str(getattr(template, "name", "")),
            "python_type": "{}.{}".format(
                type(template).__module__, type(template).__name__
            ),
            "relevant_members": _public_members(template, LIGHTING_TOKENS),
        }
        result["templates"].append(template_row)
        getter = getattr(template, "get_casual_gains", None)
        if not callable(getter):
            continue
        try:
            gains = _records(getter())
        except Exception as exc:
            result["errors"].append(
                "template {} get_casual_gains: {}".format(handle, exc)
            )
            continue
        for gain in gains:
            row = _lighting_record(gain, "template:{}".format(handle))
            if row["is_lighting_gain"]:
                result["lighting_gains"].append(row)
    return result


def _room_inventory(project: Any) -> Dict[str, Any]:
    """Inspect room-level gains and room-data members without writes."""

    result: Dict[str, Any] = {
        "rooms": [],
        "lighting_gains": [],
        "sensor_related_members": [],
        "errors": [],
    }
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
    observed_sensor_members: Set[str] = set()
    for body in bodies:
        get_room_data = getattr(body, "get_room_data", None)
        if not callable(get_room_data):
            continue
        try:
            room_data = get_room_data()
        except Exception as exc:
            result["errors"].append(
                "room {} get_room_data: {}".format(
                    getattr(body, "name", getattr(body, "id", "?")),
                    exc,
                )
            )
            continue
        members = _public_members(room_data, LIGHTING_TOKENS)
        observed_sensor_members.update(
            name
            for name in members
            if any(token in name.lower() for token in SENSOR_TOKENS)
        )
        room_name = str(getattr(body, "name", getattr(body, "id", "")))
        result["rooms"].append(
            {
                "name": room_name,
                "room_data_type": "{}.{}".format(
                    type(room_data).__module__, type(room_data).__name__
                ),
                "relevant_members": members,
            }
        )
        getter = getattr(room_data, "get_internal_gains", None)
        if not callable(getter):
            continue
        try:
            gains = _records(getter())
        except Exception as exc:
            result["errors"].append(
                "room {} get_internal_gains: {}".format(room_name, exc)
            )
            continue
        for gain in gains:
            row = _lighting_record(gain, "room:{}".format(room_name))
            if row["is_lighting_gain"]:
                result["lighting_gains"].append(row)
    result["sensor_related_members"] = sorted(observed_sensor_members)
    return result


def _module_inventory(iesve_module: Any) -> Dict[str, Any]:
    """Inventory lighting/sensor symbols exposed directly by ``iesve``."""

    members = _public_members(iesve_module, LIGHTING_TOKENS)
    sensor_members = [
        name for name in members if any(token in name.lower() for token in SENSOR_TOKENS)
    ]
    return {
        "relevant_members": members,
        "sensor_related_members": sensor_members,
        "symbols": [
            {
                "name": name,
                "python_type": "{}.{}".format(
                    type(getattr(iesve_module, name)).__module__,
                    type(getattr(iesve_module, name)).__name__,
                ),
                "relevant_members": _public_members(
                    getattr(iesve_module, name),
                    LIGHTING_TOKENS,
                ),
            }
            for name in members
        ],
    }


def _source_readiness(
    project_path: Path,
    variant: str,
    case_id: str,
) -> Dict[str, Any]:
    """Return delegated-input readiness without weakening its guards."""

    try:
        readiness = external_input_readiness(
            project_path,
            variant,
            case_id,
        )
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
    """Return exact Test 3 inputs and the twelve source combinations."""

    path = repository_root / "config" / "sia4010_official_input_contract.json"
    contract = Sia4010OfficialInputContract.load(path)
    test3 = contract.test("3")
    matrix = dict(contract.payload["tests"]["3"]["variant_matrix"])
    return {
        "path": str(path),
        "sha256": _sha256(path),
        "source": test3.source,
        "source_pages": list(test3.source_pages),
        "confirmed_inputs": dict(test3.confirmed_inputs),
        "variant_matrix": matrix,
        "unresolved_dependencies": list(test3.unresolved_dependencies),
    }


def _observed_lighting_fields(*inventories: Mapping[str, Any]) -> Set[str]:
    """Collect all property keys observed on lighting gain proxies."""

    fields: Set[str] = set()
    for inventory in inventories:
        for row in inventory.get("lighting_gains", ()):
            fields.update(str(key) for key in row.get("property_keys", ()))
    return fields


def _variant_capability_matrix(
    official: Mapping[str, Any],
    *,
    source_ready_by_case: Mapping[str, bool],
    missing_lighting_fields: Sequence[str],
    sensor_api_observed: bool,
) -> List[Dict[str, Any]]:
    """Return twelve explicit variant capability rows."""

    rows = []
    for case_id, pair in official["variant_matrix"].items():
        source_ready = source_ready_by_case.get(case_id) is True
        blockers = []
        if not source_ready:
            blockers.append("TEST3_EXTERNAL_SOURCE_BINDINGS_NOT_READY")
        if missing_lighting_fields:
            blockers.append(
                "MISSING_LIGHTING_GAIN_FIELDS:{}".format(
                    ",".join(missing_lighting_fields)
                )
            )
        if not sensor_api_observed:
            blockers.append("DAYLIGHT_SENSOR_API_NOT_OBSERVED")
        blockers.append("TEST3_APS_BINDINGS_NOT_QUALIFIED")
        if case_id in {"3K", "3L"} and not source_ready:
            blockers.append("TEST3_3K_3L_DEVICE_IDENTITY_CLARIFICATION_REQUIRED")
        rows.append(
            {
                "variant": "test_{}".format(case_id),
                "case_id": case_id,
                "shade_control": str(pair[0]),
                "lighting_control": str(pair[1]),
                "technical_blockers": blockers,
                "mutation_authorized": False,
            }
        )
    return rows


def build_test3_runtime_capability_report(
    iesve_module: Any,
    project: Any,
    repository_root: Path,
) -> Dict[str, Any]:
    """Build a fail-closed Test 3 report for the prepared exact scenario."""

    project_path = Path(str(getattr(project, "path", "")))
    scenario_path = project_path / SCENARIO_FILENAME
    if not scenario_path.is_file():
        raise ConfigurationError(
            "Prepare one official Test 3 case first; missing scenario: {}".format(
                scenario_path
            )
        )
    scenario = ModelScenario.load(scenario_path)
    if (
        not scenario.is_official
        or scenario.variant not in TEST3_VARIANTS
        or scenario.case_id != scenario.variant[5:]
    ):
        raise ConfigurationError(
            "Test 3 runtime probe requires one exact official test_3A-" "test_3L scenario"
        )
    global_gains = _global_gain_inventory(project)
    templates = _template_inventory(project)
    rooms = _room_inventory(project)
    module = _module_inventory(iesve_module)
    observed_fields = _observed_lighting_fields(
        global_gains,
        templates,
        rooms,
    )
    missing_fields = sorted(REQUIRED_LIGHTING_FIELDS - observed_fields)
    sensor_members = sorted(
        set(module["sensor_related_members"]) | set(rooms["sensor_related_members"])
    )
    official = _official_contract(Path(repository_root))
    source_matrix = {
        case_id: _source_readiness(
            project_path,
            "test_{}".format(case_id),
            case_id,
        )
        for case_id in official["variant_matrix"]
    }
    source = source_matrix[scenario.case_id]
    matrix = _variant_capability_matrix(
        official,
        source_ready_by_case={
            case_id: item["ready_for_binding"] for case_id, item in source_matrix.items()
        },
        missing_lighting_fields=missing_fields,
        sensor_api_observed=bool(sensor_members),
    )
    selected = next(row for row in matrix if row["variant"] == scenario.variant)
    technical_blockers = list(selected["technical_blockers"])
    if not global_gains["casual_gains_available"]:
        technical_blockers.append("VEPROJECT_CASUAL_GAINS_API_UNAVAILABLE")
    if not rooms["rooms"]:
        technical_blockers.append("NO_ROOM_PROXY_AVAILABLE_FOR_READBACK")
    setter_blockers = [
        blocker
        for blocker in technical_blockers
        if blocker != "TEST3_APS_BINDINGS_NOT_QUALIFIED"
    ]
    if not source["ready_for_binding"]:
        status = "SOURCE_BINDINGS_REQUIRED"
    elif setter_blockers:
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
        "official_test3_contract": official,
        "source_binding": source,
        "source_binding_matrix": source_matrix,
        "global_lighting_gain_api": global_gains,
        "thermal_template_api": templates,
        "room_lighting_api": rooms,
        "iesve_module_api": module,
        "observed_lighting_fields": sorted(observed_fields),
        "required_lighting_fields": sorted(REQUIRED_LIGHTING_FIELDS),
        "missing_lighting_fields": missing_fields,
        "sensor_related_members": sensor_members,
        "variant_capability_matrix": matrix,
        "selected_variant_capability": selected,
        "technical_blockers": technical_blockers,
        "setter_qualification_blockers": setter_blockers,
        "mutation_performed": False,
        "mutation_authorized": False,
        "simulation_performed": False,
        "compliance_claim_allowed": False,
        "next_action": (
            "Use this report to implement narrow disposable-project lighting "
            "gain and daylight-sensor setter qualifications. Do not infer "
            "sensor coordinates, control algorithms or APS variables from "
            "member names."
        ),
        "claim_guardrail": (
            "This read-only inventory is not a Test 3 model, control "
            "qualification, simulation, comparison, validation or SIA "
            "attestation."
        ),
    }


def write_test3_runtime_capability_report(
    iesve_module: Any,
    project: Any,
    repository_root: Path,
) -> Path:
    """Persist the read-only Test 3 report and its SHA-256 sidecar."""

    payload = build_test3_runtime_capability_report(
        iesve_module,
        project,
        repository_root,
    )
    project_path = Path(payload["project"]["path"])
    output_path = (
        project_path
        / REPORT_DIRECTORY
        / "sia4010_test3_runtime_capability_{}.json".format(
            datetime.now().strftime("%Y%m%d_%H%M%S")
        )
    )
    _write_json(output_path, payload)
    output_path.with_suffix(output_path.suffix + ".sha256").write_text(
        "{}  {}\n".format(_sha256(output_path), output_path.name),
        encoding="ascii",
    )
    return output_path
