"""Read-only runtime capability evidence for SIA 4010 Test 2A.

The Test 2A source bundle is intentionally not enough to authorize VE
mutation.  This module inventories the active IESVE runtime without creating,
editing or saving any VE object.  It records the exact profile proxy types,
glazed-construction shading fields and opening API members exposed by the
installed build so that a later disposable-project mutation probe can be
implemented against evidence rather than guesses.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set

from .external_input_manifest import external_input_readiness
from .normalized_external_inputs import load_test2a_external_bindings
from .official_input_contract import Sia4010OfficialInputContract
from .test2a_shading_control import (
    build_test2a_fabric_awning_control,
    build_test2a_optical_diagnostic_contract,
)
from .test2a_diagnostic_workbook import (
    load_test2a_diagnostic_workbook_binding,
)
from .qualified_aps import QualifiedApsBindings
from .test2a_diagnostic_aps import (
    build_test2a_2e1_aps_binding_contract,
)

REPORT_SCHEMA_VERSION = "1.0"
REPORT_DIRECTORY = Path("sia4010_artifacts") / "diagnostics"

PROFILE_PREDICATES = (
    "is_weekly",
    "is_yearly",
    "is_compact",
    "is_freeform",
    "is_modulating",
)

REQUIRED_PROJECT_PROFILE_METHODS = (
    "profiles",
    "create_profile",
    "save_profiles",
)

REQUIRED_EXTERNAL_SHADE_FIELDS = frozenset(
    {
        "external_shade_active",
        "external_shade_profile",
        "external_shade_radiation_to_raise",
        "external_shade_radiation_to_lower",
    }
)

RELEVANT_MEMBER_TOKENS = (
    "shade",
    "shading",
    "blind",
    "solar",
    "profile",
    "opening",
    "window",
    "glaz",
    "construction",
    "assign",
)


def _sha256(path: Path) -> str:
    """Return a lowercase SHA-256 digest."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write deterministic UTF-8 JSON through an atomic replacement."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _jsonable(value: Any, depth: int = 0) -> Any:
    """Convert bounded VE proxy values to JSON-safe diagnostic values."""

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


def _safe_call(obj: Any, method_name: str) -> Dict[str, Any]:
    """Call a parameterless read-only predicate and capture its outcome."""

    method = getattr(obj, method_name, None)
    if not callable(method):
        return {"available": False}
    try:
        return {"available": True, "value": _jsonable(method())}
    except Exception as exc:
        return {"available": True, "error": str(exc)}


def _relevant_members(obj: Any) -> List[str]:
    """Return only API member names relevant to profiles and shading."""

    if obj is None:
        return []
    try:
        names = dir(obj)
    except Exception:
        return []
    return sorted(
        name
        for name in names
        if not name.startswith("_")
        and any(token in name.lower() for token in RELEVANT_MEMBER_TOKENS)
    )


def _profile_inventory(project: Any) -> Dict[str, Any]:
    """Read every current profile proxy without creating or saving profiles."""

    result: Dict[str, Any] = {
        "project_methods": {
            name: hasattr(project, name) for name in REQUIRED_PROJECT_PROFILE_METHODS
        },
        "profiles": [],
        "errors": [],
    }
    profiles_method = getattr(project, "profiles", None)
    if not callable(profiles_method):
        return result
    try:
        collections = profiles_method()
    except Exception as exc:
        result["errors"].append("VEProject.profiles: {}".format(exc))
        return result
    for collection_index, collection in enumerate(collections or ()):
        if not isinstance(collection, Mapping):
            result["errors"].append(
                "Profile collection {} is not a mapping: {}".format(
                    collection_index, type(collection).__name__
                )
            )
            continue
        for identifier, profile in collection.items():
            row: Dict[str, Any] = {
                "collection_index": collection_index,
                "identifier": str(identifier),
                "python_type": "{}.{}".format(
                    type(profile).__module__, type(profile).__name__
                ),
                "reference": str(
                    getattr(
                        profile,
                        "reference",
                        getattr(profile, "name", ""),
                    )
                ),
                "predicates": {
                    name: _safe_call(profile, name) for name in PROFILE_PREDICATES
                },
                "relevant_members": _relevant_members(profile),
            }
            get_data = getattr(profile, "get_data", None)
            if callable(get_data):
                try:
                    data = get_data()
                    row["data_shape"] = _data_shape(data)
                    row["data_preview"] = _jsonable(data)
                except Exception as exc:
                    row["data_error"] = str(exc)
            result["profiles"].append(row)
    result["observed_python_types"] = sorted(
        {row["python_type"] for row in result["profiles"]}
    )
    return result


def _data_shape(value: Any) -> Dict[str, Any]:
    """Describe nested profile data without interpreting its semantics."""

    result = {"python_type": type(value).__name__}
    if isinstance(value, (list, tuple)):
        result["length"] = len(value)
        if value:
            result["item_type"] = type(value[0]).__name__
            if isinstance(value[0], (list, tuple)):
                result["first_item_length"] = len(value[0])
    return result


def _current_cdb_project(iesve_module: Any) -> Optional[Any]:
    """Resolve the editable project CDB using the documented read-only path."""

    database_type = getattr(iesve_module, "VECdbDatabase", None)
    if database_type is None:
        return None
    try:
        database = database_type.get_current_database()
        projects = database.get_projects()
    except Exception:
        return None
    candidates = projects.get(0, []) if isinstance(projects, Mapping) else []
    return candidates[0] if candidates else None


def _glazed_class(iesve_module: Any) -> Optional[Any]:
    """Resolve the glazed-construction enum across known VE layouts."""

    for owner in (
        getattr(iesve_module, "VECdbProject", None),
        iesve_module,
    ):
        if owner is None:
            continue
        enum = getattr(owner, "construction_class", None)
        value = getattr(enum, "glazed", None) if enum is not None else None
        if value is not None:
            return value
    return None


def _get_construction(
    cdb_project: Any,
    identifier: Any,
    construction_class: Any,
) -> Optional[Any]:
    """Resolve a CDB construction across Boost.Python overload variants."""

    for arguments in (
        (identifier, construction_class),
        (identifier,),
    ):
        try:
            construction = cdb_project.get_construction(*arguments)
            if construction is not None:
                return construction
        except Exception:
            continue
    return None


def _glazed_construction_inventory(
    iesve_module: Any,
    limit: int = 100,
) -> Dict[str, Any]:
    """Inspect CDB glazing fields that could represent Test 2A shading."""

    result: Dict[str, Any] = {
        "available": False,
        "constructions": [],
        "observed_shading_fields": [],
        "required_fields": sorted(REQUIRED_EXTERNAL_SHADE_FIELDS),
        "missing_required_fields": sorted(REQUIRED_EXTERNAL_SHADE_FIELDS),
        "errors": [],
    }
    cdb_project = _current_cdb_project(iesve_module)
    construction_class = _glazed_class(iesve_module)
    if cdb_project is None or construction_class is None:
        result["errors"].append(
            "Current project CDB or glazed construction enum is unavailable"
        )
        return result
    result["available"] = True
    try:
        identifiers = list(cdb_project.get_construction_ids(construction_class))[:limit]
    except Exception as exc:
        result["errors"].append("get_construction_ids(glazed): {}".format(exc))
        return result
    observed: Set[str] = set()
    for identifier in identifiers:
        construction = _get_construction(cdb_project, identifier, construction_class)
        if construction is None:
            result["constructions"].append(
                {"identifier": str(identifier), "error": "unresolved"}
            )
            continue
        row: Dict[str, Any] = {
            "identifier": str(identifier),
            "python_type": "{}.{}".format(
                type(construction).__module__,
                type(construction).__name__,
            ),
            "relevant_members": _relevant_members(construction),
        }
        try:
            properties = dict(construction.get_properties())
            shading = {
                str(key): _jsonable(value)
                for key, value in properties.items()
                if any(
                    token in str(key).lower()
                    for token in ("shade", "shading", "blind", "solar")
                )
            }
            row["shading_properties"] = shading
            row["all_property_keys"] = sorted(str(key) for key in properties)
            observed.update(shading)
        except Exception as exc:
            row["property_error"] = str(exc)
        result["constructions"].append(row)
    result["observed_shading_fields"] = sorted(observed)
    result["missing_required_fields"] = sorted(REQUIRED_EXTERNAL_SHADE_FIELDS - observed)
    return result


def _as_sequence(value: Any) -> Sequence[Any]:
    """Return a bounded sequence for VE vector/list proxy values."""

    if value is None:
        return ()
    if isinstance(value, (str, bytes)):
        return ()
    try:
        return tuple(value)
    except Exception:
        return ()


def _opening_inventory(project: Any, limit: int = 100) -> Dict[str, Any]:
    """Inspect opening proxies through read-only model traversal."""

    result: Dict[str, Any] = {
        "openings": [],
        "errors": [],
        "observed_python_types": [],
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
    for body in bodies:
        get_surfaces = getattr(body, "get_surfaces", None)
        if not callable(get_surfaces):
            continue
        try:
            surfaces = _as_sequence(get_surfaces())
        except Exception as exc:
            result["errors"].append(
                "VEBody.get_surfaces({}): {}".format(
                    getattr(body, "name", getattr(body, "id", "?")), exc
                )
            )
            continue
        for surface in surfaces:
            get_openings = getattr(surface, "get_openings", None)
            if not callable(get_openings):
                continue
            try:
                openings = _as_sequence(get_openings())
            except Exception as exc:
                result["errors"].append("VESurface.get_openings: {}".format(exc))
                continue
            for opening in openings:
                result["openings"].append(
                    {
                        "body": str(getattr(body, "name", getattr(body, "id", ""))),
                        "surface": str(
                            getattr(
                                surface,
                                "name",
                                getattr(surface, "id", ""),
                            )
                        ),
                        "opening": str(
                            getattr(
                                opening,
                                "name",
                                getattr(opening, "id", ""),
                            )
                        ),
                        "python_type": "{}.{}".format(
                            type(opening).__module__,
                            type(opening).__name__,
                        ),
                        "relevant_members": _relevant_members(opening),
                    }
                )
                if len(result["openings"]) >= limit:
                    break
            if len(result["openings"]) >= limit:
                break
        if len(result["openings"]) >= limit:
            break
    result["observed_python_types"] = sorted(
        {row["python_type"] for row in result["openings"]}
    )
    return result


def _module_symbol_inventory(iesve_module: Any) -> List[Dict[str, Any]]:
    """List relevant public types/functions exposed by the injected module."""

    rows = []
    for name in _relevant_members(iesve_module):
        try:
            value = getattr(iesve_module, name)
            rows.append(
                {
                    "name": name,
                    "python_type": "{}.{}".format(
                        type(value).__module__, type(value).__name__
                    ),
                    "relevant_members": _relevant_members(value),
                }
            )
        except Exception as exc:
            rows.append({"name": name, "error": str(exc)})
    return rows


def _source_binding_status(project_path: Path) -> Dict[str, Any]:
    """Read Test 2A delegated-input readiness without weakening its guards."""

    try:
        readiness = external_input_readiness(
            project_path,
            "test_2A",
            "2A",
        )
        result = {
            "available": True,
            "ready_for_binding": readiness.ready_for_binding,
            "status": readiness.status,
            "details": readiness.to_dict(),
            "native_ve_profile_graph_present": False,
            "required_native_ve_profile_types": [],
        }
        if readiness.ready_for_binding:
            bindings = load_test2a_external_bindings(readiness)
            graph = bindings.office_profiles.ve_profile_graph
            result["native_ve_profile_graph_present"] = graph is not None
            if graph is not None:
                result["required_native_ve_profile_types"] = list(
                    graph.required_profile_types
                )
                result["native_ve_profile_outputs"] = dict(graph.outputs)
        return result
    except Exception as exc:
        return {
            "available": False,
            "ready_for_binding": False,
            "status": "UNAVAILABLE",
            "error": str(exc),
            "native_ve_profile_graph_present": False,
            "required_native_ve_profile_types": [],
        }


def _official_shading_control_status() -> Dict[str, Any]:
    """Return the repository's source-traced Test 2A awning contract."""

    contract_path = (
        Path(__file__).resolve().parents[3]
        / "config"
        / "sia4010_official_input_contract.json"
    )
    try:
        contract = Sia4010OfficialInputContract.load(contract_path)
        control = build_test2a_fabric_awning_control(contract.test("2").confirmed_inputs)
        workbook_path = (
            Path(__file__).resolve().parents[3]
            / "SIA_4010_geteilter_Link"
            / "Test2"
            / "Resultaterfassung_Test2.xlsx"
        )
        workbook_binding = load_test2a_diagnostic_workbook_binding(workbook_path)
        diagnostic = build_test2a_optical_diagnostic_contract(
            control,
            workbook_binding.to_dict(),
        )
        aps_binding_path = (
            Path(__file__).resolve().parents[3]
            / "config"
            / "sia4010_aps_bindings_ve_runtime.json"
        )
        try:
            aps_bindings = QualifiedApsBindings.load(aps_binding_path)
            aps_contract = build_test2a_2e1_aps_binding_contract(
                aps_bindings,
                workbook_binding,
            )
            aps_diagnostic_binding = {
                "available": True,
                **aps_contract.to_dict(),
            }
        except Exception as aps_exc:
            aps_diagnostic_binding = {
                "available": False,
                "binding_path": str(aps_binding_path),
                "error": str(aps_exc),
                "claim_guardrail": (
                    "No 2E1 APS output binding may be inferred from names."
                ),
            }
        return {
            "available": True,
            "contract_path": str(contract_path),
            "contract_sha256": _sha256(contract_path),
            "result_workbook_path": str(workbook_path),
            "result_workbook_sha256": workbook_binding.workbook_sha256,
            "control": control.to_dict(),
            "optical_diagnostic": diagnostic.to_dict(),
            "aps_diagnostic_binding": aps_diagnostic_binding,
        }
    except Exception as exc:
        return {
            "available": False,
            "contract_path": str(contract_path),
            "error": str(exc),
        }


def build_test2a_runtime_capability_report(
    iesve_module: Any,
    project: Any,
) -> Dict[str, Any]:
    """Return a fail-closed read-only Test 2A runtime evidence report."""

    project_path = Path(str(getattr(project, "path", "")))
    profiles = _profile_inventory(project)
    constructions = _glazed_construction_inventory(iesve_module)
    openings = _opening_inventory(project)
    source_binding = _source_binding_status(project_path)
    shading_control = _official_shading_control_status()
    missing_project_methods = sorted(
        name for name, available in profiles["project_methods"].items() if not available
    )
    technical_blockers = []
    if missing_project_methods:
        technical_blockers.append(
            "MISSING_PROFILE_API:{}".format(",".join(missing_project_methods))
        )
    if constructions["missing_required_fields"]:
        technical_blockers.append(
            "MISSING_EXTERNAL_SHADE_FIELDS:{}".format(
                ",".join(constructions["missing_required_fields"])
            )
        )
    if not openings["openings"]:
        technical_blockers.append("NO_OPENING_PROXY_AVAILABLE_FOR_READBACK")
    if not source_binding["ready_for_binding"]:
        technical_blockers.append("TEST2A_SOURCE_BINDINGS_NOT_READY")
    elif not source_binding["native_ve_profile_graph_present"]:
        technical_blockers.append("SIA2024_NATIVE_VE_PROFILE_GRAPH_NOT_SUPPLIED")
    if not shading_control["available"]:
        technical_blockers.append("TEST2A_OFFICIAL_SHADING_CONTROL_CONTRACT_UNAVAILABLE")

    if not source_binding["ready_for_binding"]:
        status = "SOURCE_BINDINGS_REQUIRED"
    elif not source_binding["native_ve_profile_graph_present"]:
        status = "NATIVE_PROFILE_GRAPH_REQUIRED"
    elif technical_blockers:
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
                if hasattr(project, "get_version")
                else "unavailable"
            ),
        },
        "variant": "test_2A",
        "case_id": "2A",
        "source_binding": source_binding,
        "official_shading_control": shading_control,
        "profile_api": profiles,
        "glazed_construction_api": constructions,
        "opening_api": openings,
        "iesve_module_symbols": _module_symbol_inventory(iesve_module),
        "technical_blockers": technical_blockers,
        "mutation_performed": False,
        "mutation_authorized": False,
        "next_action": (
            "Run the profile-only and one-object CDB shade-setter "
            "qualifications only after this report is "
            "READY_FOR_DISPOSABLE_MUTATION_QUALIFICATION. A setter PASS "
            "does not close the dynamic equality, timestep or optical "
            "equivalence blockers."
        ),
        "claim_guardrail": (
            "Runtime capability evidence is not a generated Test 2A model, "
            "simulation result, SIA comparison, validation or attestation."
        ),
    }


def write_test2a_runtime_capability_report(
    iesve_module: Any,
    project: Any,
) -> Path:
    """Build and persist the read-only report beside the active VE project."""

    payload = build_test2a_runtime_capability_report(iesve_module, project)
    project_path = Path(payload["project"]["path"])
    output_directory = project_path / REPORT_DIRECTORY
    output_path = output_directory / (
        "sia4010_test2a_runtime_capability_{}.json".format(
            datetime.now().strftime("%Y%m%d_%H%M%S")
        )
    )
    _write_json(output_path, payload)
    payload_sha = _sha256(output_path)
    checksum_path = output_path.with_suffix(output_path.suffix + ".sha256")
    checksum_path.write_text(
        "{}  {}\n".format(payload_sha, output_path.name),
        encoding="ascii",
    )
    return output_path
