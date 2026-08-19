"""Guarded application of reviewed VE thermal templates to client-model copies.

This module deliberately does not decide which values are compliant.  It applies
an *existing* VE thermal template only after the user has confirmed an exact
technical preview in a disposable project.  Evidence already available from VE
and source-traced provisioning receipts is captured automatically; no free-text
form is required.  Every write is bound to an immutable preview plan and verified
through VE read-back.  The technical application never grants a compliance claim.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .compliance_hub import is_disposable_project
from .reference_model.ve_compat import thermal_templates


SCHEMA_VERSION = "1.1"
OPERATION = "ASSIGN_EXISTING_THERMAL_TEMPLATE"
APPROVAL_STATUS = "APPROVED_FOR_PROJECT_USE"
REVIEW_ONLY_STATUS = "CANDIDATE_FOR_REVIEW"
TECHNICAL_APPLICATION_STATUS = "TECHNICAL_APPLICATION_CONFIRMED"
AUTOMATIC_EVIDENCE_MODE = "AUTOMATIC_TECHNICAL_EVIDENCE"

# Documented VE gain labels used only to compare the *structure* already
# present in a room with the structure of the selected template.  This is not
# a regulatory mapping.  Sources:
# - references/iesve/IESVE_API_REFERENCE.md, "RoomInternalGain";
# - official IESVE help, "Space Data" and
#   "Appendix A. Known Limitations" (room gains must be added/removed through
#   the assigned template or Query Room; VERoomData exposes no add_gain API).
# Unknown labels are never folded into a known family.
_GAIN_FAMILY_BY_TYPE_STR = {
    "people": "people",
    "lighting": "lighting",
    "general lighting": "lighting",
    "fluorescent lighting": "lighting",
    "tungsten lighting": "lighting",
    "machinery": "energy",
    "miscellaneous": "energy",
    "cooking": "energy",
    "computers": "energy",
}
_ROOM_GAIN_CREATION_API_STATUS = "NOT_AVAILABLE_IN_DOCUMENTED_VERoomData_API"


class ClientTemplateRemediationError(RuntimeError):
    """Raised when a client-template operation cannot be proven safe."""


@dataclass(frozen=True)
class TemplateEvidence:
    """Evidence captured for one checksum-bound template assignment.

    The manual fields remain supported for API compatibility, but the product UI
    now creates them automatically from project and VE read-back data.  Automatic
    technical evidence is not independent approval and cannot grant compliance.
    """

    reviewer: str
    review_date: str
    source_document: str
    source_reference: str
    intended_use: str
    approval_status: str = REVIEW_ONLY_STATUS
    evidence_mode: str = "MANUAL_REVIEW_EVIDENCE"
    source_trace_status: str = "USER_PROVIDED"

    def validate(self) -> List[str]:
        """Return fail-closed evidence errors without guessing missing values."""

        errors: List[str] = []
        for field_name in (
            "reviewer",
            "review_date",
            "source_document",
            "source_reference",
            "intended_use",
        ):
            if not str(getattr(self, field_name) or "").strip():
                errors.append("{} is required".format(field_name))
        try:
            date.fromisoformat(str(self.review_date))
        except (TypeError, ValueError):
            errors.append("review_date must use YYYY-MM-DD")
        if self.approval_status not in {
            APPROVAL_STATUS,
            REVIEW_ONLY_STATUS,
            TECHNICAL_APPLICATION_STATUS,
        }:
            errors.append(
                "approval_status must be '{}', '{}' or '{}'".format(
                    APPROVAL_STATUS,
                    REVIEW_ONLY_STATUS,
                    TECHNICAL_APPLICATION_STATUS,
                )
            )
        return errors


def _latest_template_provisioning_receipt(
    project_path: str,
    template_name: str,
) -> Tuple[Optional[Path], Dict[str, Any]]:
    """Return the newest matching source-traced provisioning receipt.

    Absence or unreadable content is represented by an empty result.  It is
    never converted into a successful source review.
    """

    folder = (
        Path(project_path)
        / "sia_compliance_artifacts"
        / "template_provisioning"
    )
    try:
        candidates = sorted(
            (
                path
                for path in folder.glob("*_template_receipt_*.json")
                if path.is_file()
            ),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        return None, {}
    for path in candidates:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError, TypeError):
            continue
        if not isinstance(payload, Mapping):
            continue
        if str(payload.get("template_name") or "") == str(template_name):
            return path, dict(payload)
    return None, {}


def automatic_template_evidence(
    project_path: str,
    project_name: str,
    template: Mapping[str, Any],
    room_ids: Iterable[str],
    application_confirmed: bool,
) -> TemplateEvidence:
    """Build deterministic technical evidence without asking for free text.

    Project identity, selected rooms and the live VE template fingerprint are
    factual runtime data.  When a matching provisioning receipt exists, its
    source path and checksum are recorded.  Missing source evidence remains
    explicitly ``NOT_CHECKABLE`` and never blocks a disposable technical apply
    because the resulting receipt still grants no compliance verdict.
    """

    template_name = str(template.get("name") or "")
    fingerprint = str(template.get("fingerprint_sha256") or "")
    selected = sorted(str(room_id) for room_id in room_ids if str(room_id))
    receipt_path, receipt = _latest_template_provisioning_receipt(
        project_path, template_name
    )
    source_path = str(receipt.get("source_path") or "").strip()
    source_sha256 = str(receipt.get("source_sha256") or "").strip()
    source_trace_status = (
        "SOURCE_TRACED_PROVISIONING_RECEIPT"
        if receipt_path is not None and source_path and source_sha256
        else "NOT_CHECKABLE"
    )
    source_document = (
        source_path
        if source_path
        else "[TO VERIFY] No matching source-traced template provisioning receipt"
    )
    source_reference = (
        "SHA256:{}; RECEIPT:{}".format(source_sha256, receipt_path)
        if source_trace_status == "SOURCE_TRACED_PROVISIONING_RECEIPT"
        else "VE_TEMPLATE_SHA256:{}".format(fingerprint or "NOT_CHECKABLE")
    )
    return TemplateEvidence(
        reviewer="NOT_COLLECTED_BY_TECHNICAL_APPLICATION_UI",
        review_date=date.today().isoformat(),
        source_document=source_document,
        source_reference=source_reference,
        intended_use=(
            "Technical assignment of template '{}' to explicit room IDs: {}"
            .format(template_name, ", ".join(selected))
        ),
        approval_status=(
            TECHNICAL_APPLICATION_STATUS
            if application_confirmed
            else REVIEW_ONLY_STATUS
        ),
        evidence_mode=AUTOMATIC_EVIDENCE_MODE,
        source_trace_status=source_trace_status,
    )


def _json_safe(value: Any) -> Any:
    """Return deterministic JSON-safe VE read-back data."""

    if isinstance(value, Mapping):
        return {
            str(key): _json_safe(item)
            for key, item in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    enum_value = getattr(value, "value", None)
    if isinstance(enum_value, (str, int, float, bool)):
        return enum_value
    return str(value)


def _canonical_json(payload: Mapping[str, Any]) -> str:
    """Serialize a mapping for hashing and evidence comparison."""

    return json.dumps(
        _json_safe(payload),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _sha256(payload: Mapping[str, Any]) -> str:
    """Return a canonical SHA-256 checksum for a mapping."""

    return hashlib.sha256(_canonical_json(payload).encode("utf-8")).hexdigest()


def _record_data(record: Any) -> Dict[str, Any]:
    """Read a VE record without mutating it."""

    try:
        return dict(record.get())
    except Exception as exc:
        raise ClientTemplateRemediationError(
            "Unable to read VE template record: {}".format(exc)
        ) from exc


def _records(owner: Any, method_name: str) -> List[Dict[str, Any]]:
    """Read an optional list of native VE records."""

    method = getattr(owner, method_name, None)
    if method is None:
        return []
    try:
        return [_json_safe(_record_data(item)) for item in list(method())]
    except ClientTemplateRemediationError:
        raise
    except Exception as exc:
        raise ClientTemplateRemediationError(
            "Unable to read {}: {}".format(method_name, exc)
        ) from exc


def _mapping(owner: Any, method_name: str) -> Dict[str, Any]:
    """Read an optional VE mapping through one getter."""

    method = getattr(owner, method_name, None)
    if method is None:
        return {}
    try:
        return _json_safe(dict(method()))
    except Exception as exc:
        raise ClientTemplateRemediationError(
            "Unable to read {}: {}".format(method_name, exc)
        ) from exc


def _profile_references(payload: Any) -> List[str]:
    """Collect profile identifiers embedded in a normalized template snapshot."""

    references: List[str] = []

    def visit(value: Any, parent_key: str = "") -> None:
        if isinstance(value, Mapping):
            for key, item in value.items():
                visit(item, str(key))
            return
        if isinstance(value, (list, tuple)):
            for item in value:
                visit(item, parent_key)
            return
        if "profile" not in parent_key.lower():
            return
        # VE record getters also expose boolean inheritance/saturation flags
        # whose key contains ``profile``. They are metadata, not identifiers.
        if not isinstance(value, str):
            return
        text = str(value or "").strip()
        # ``-`` is emitted by VE in daily-profile breakpoint rows as the
        # interpolation/option sentinel.  It is not a persistent profile ID.
        if text and text.upper() not in {"-", "ON", "OFF", "NONE"}:
            references.append(text)

    visit(payload)
    return sorted(set(references))


def _available_profile_ids(project: Any) -> List[str]:
    """Return all persistent profile identifiers exposed by the active project."""

    try:
        collections = project.profiles()
    except Exception:
        return []
    identifiers = set()
    for collection in collections if isinstance(collections, tuple) else (collections,):
        if isinstance(collection, Mapping):
            identifiers.update(
                str(key).strip() for key in collection if str(key).strip()
            )
            values = collection.values()
        else:
            values = collection
        try:
            records = list(values)
        except TypeError:
            continue
        for record in records:
            identifier = str(getattr(record, "id", "") or "").strip()
            if identifier:
                identifiers.add(identifier)
    return sorted(identifiers)


def _room_state(body: Any) -> Dict[str, Any]:
    """Return the exact room-level state covered by template remediation."""

    room_data = body.get_room_data()
    state: Dict[str, Any] = {
        "general": _json_safe(dict(room_data.get_general())),
        "casual_gains": [
            _json_safe(_record_data(record))
            for record in list(room_data.get_internal_gains())
        ],
        "air_exchanges": [
            _json_safe(_record_data(record))
            for record in list(room_data.get_air_exchanges())
        ],
        "room_conditions": _mapping(room_data, "get_room_conditions"),
        "apache_systems": _mapping(room_data, "get_apache_systems"),
    }
    return state


def template_snapshot(
    handle: Any, template: Any, available_profiles: Sequence[str]
) -> Dict[str, Any]:
    """Return the simulation-relevant, fingerprinted content of one VE template."""

    content = {
        "name": str(getattr(template, "name", "") or "").strip(),
        "handle": str(handle),
        "casual_gains": _records(template, "get_casual_gains"),
        "air_exchanges": _records(template, "get_air_exchanges"),
        "room_conditions": _mapping(template, "get_room_conditions"),
        "apache_systems": _mapping(template, "get_apache_systems"),
    }
    referenced = _profile_references(content)
    available = set(str(item) for item in available_profiles)
    missing = sorted(item for item in referenced if item not in available)
    fingerprint_payload = dict(content)
    fingerprint_payload["referenced_profiles"] = referenced
    fingerprint = _sha256(fingerprint_payload)
    return {
        **content,
        "referenced_profiles": referenced,
        "missing_profile_references": missing,
        "fingerprint_sha256": fingerprint,
        "capabilities": {
            "add_gain": callable(getattr(template, "add_gain", None)),
            "remove_gain": callable(getattr(template, "remove_gain", None)),
            "apply_changes": callable(getattr(template, "apply_changes", None)),
        },
        "review_observations": _template_review_observations(content),
    }


def _record_label(record: Mapping[str, Any]) -> str:
    """Return normalized descriptive text for a template-record observation."""

    return " ".join(
        str(record.get(key) or "")
        for key in ("name", "type_str", "type_val")
    ).casefold()


def _gain_family(record: Mapping[str, Any]) -> Optional[str]:
    """Return a documented gain family, or ``None`` for an unknown label."""

    label = " ".join(str(record.get("type_str") or "").split()).casefold()
    return _GAIN_FAMILY_BY_TYPE_STR.get(label)


def _gain_structure_assessment(
    template: Mapping[str, Any],
    rooms: Sequence[Mapping[str, Any]],
    inventory: Mapping[str, Any],
) -> Dict[str, Any]:
    """Assess whether VE can synchronize target gains without creating rows.

    Runtime evidence from VE 2025 showed that
    ``assign_thermal_template_to_rooms`` persists the template handle but does
    not necessarily materialize missing room-level gain families.  The
    documented ``VERoomData`` API has no ``add_gain``/``remove_gain`` member.
    Therefore a missing or ambiguous family must block before the first write.
    """

    target_records = [
        item
        for item in template.get("casual_gains", [])
        if isinstance(item, Mapping)
    ]
    target_families = [_gain_family(item) for item in target_records]
    unknown_targets = [
        str(item.get("type_str") or item.get("name") or "<unknown>")
        for item, family in zip(target_records, target_families)
        if family is None
    ]
    known_targets = [family for family in target_families if family is not None]
    duplicate_targets = sorted(
        family for family in set(known_targets) if known_targets.count(family) > 1
    )

    room_results: List[Dict[str, Any]] = []
    blocked = bool(unknown_targets or duplicate_targets)
    for room in rooms:
        state = room.get("current_state")
        state = state if isinstance(state, Mapping) else {}
        actual_records = [
            item
            for item in state.get("casual_gains", [])
            if isinstance(item, Mapping)
        ]
        actual_families = [_gain_family(item) for item in actual_records]
        unknown_actual = [
            str(item.get("type_str") or item.get("name") or "<unknown>")
            for item, family in zip(actual_records, actual_families)
            if family is None
        ]
        known_actual = [family for family in actual_families if family is not None]
        duplicate_actual = sorted(
            family for family in set(known_actual) if known_actual.count(family) > 1
        )
        missing = sorted(set(known_targets) - set(known_actual))
        room_blocked = bool(unknown_actual or duplicate_actual)
        blocked = blocked or room_blocked
        room_results.append(
            {
                "room_id": str(room.get("room_id") or ""),
                "room_name": str(room.get("room_name") or ""),
                "existing_gain_families": sorted(set(known_actual)),
                "missing_gain_families": missing,
                "duplicate_gain_families": duplicate_actual,
                "unknown_gain_type_labels": unknown_actual,
                "status": (
                    "BLOCKED"
                    if room_blocked
                    else "MISSING_GAIN_FAMILIES"
                    if missing
                    else "COMPATIBLE"
                ),
            }
        )

    selected_ids = {str(room.get("room_id") or "") for room in rooms}
    templates_by_handle = {
        str(item.get("handle") or ""): item
        for item in inventory.get("templates", [])
        if isinstance(item, Mapping)
    }
    all_rooms_by_template: Dict[str, List[str]] = {}
    for room in inventory.get("rooms", []):
        if not isinstance(room, Mapping):
            continue
        handle = str(room.get("current_template_handle") or "")
        all_rooms_by_template.setdefault(handle, []).append(
            str(room.get("room_id") or "")
        )

    bridge_by_source: Dict[str, Dict[str, Any]] = {}
    target_by_family = {
        family: record
        for family, record in zip(target_families, target_records)
        if family is not None
    }
    target_handle = str(template.get("handle") or "")
    for room_result, room in zip(room_results, rooms):
        missing = list(room_result["missing_gain_families"])
        if not missing:
            continue
        source_handle = str(room.get("current_template_handle") or "")
        source = templates_by_handle.get(source_handle)
        source_capabilities = (
            source.get("capabilities", {}) if isinstance(source, Mapping) else {}
        )
        source_records = (
            [
                item
                for item in source.get("casual_gains", [])
                if isinstance(item, Mapping)
            ]
            if isinstance(source, Mapping)
            else []
        )
        source_families = [_gain_family(item) for item in source_records]
        source_unknown = [family for family in source_families if family is None]
        source_duplicates = [
            family
            for family in set(source_families)
            if family is not None and source_families.count(family) > 1
        ]
        unselected = sorted(
            set(all_rooms_by_template.get(source_handle, [])) - selected_ids
        )
        bridge_possible = bool(
            source
            and source_handle != target_handle
            and not source_unknown
            and not source_duplicates
            and not (set(missing) & set(source_families))
            and not unselected
            and all(
                bool(source_capabilities.get(member))
                for member in ("add_gain", "remove_gain", "apply_changes")
            )
        )
        if not bridge_possible:
            blocked = True
            room_result["status"] = "BLOCKED"
            room_result["bridge_status"] = "NOT_AVAILABLE"
            room_result["unselected_rooms_sharing_source_template"] = unselected
            continue
        room_result["bridge_status"] = "AVAILABLE_DOCUMENTED_TEMPLATE_API"
        room_result["status"] = "BRIDGE_AVAILABLE"
        bridge = bridge_by_source.setdefault(
            source_handle,
            {
                "source_template_handle": source_handle,
                "source_template_name": str(source.get("name") or ""),
                "source_template_fingerprint_sha256": str(
                    source.get("fingerprint_sha256") or ""
                ),
                "original_gain_record_names": [
                    str(item.get("name") or "") for item in source_records
                ],
                "room_ids": [],
                "target_gain_records": [],
            },
        )
        bridge["room_ids"].append(str(room.get("room_id") or ""))
        existing_bridge_families = {
            str(item.get("family") or "") for item in bridge["target_gain_records"]
        }
        for family in missing:
            if family in existing_bridge_families:
                continue
            record = target_by_family[family]
            bridge["target_gain_records"].append(
                {
                    "family": family,
                    "name": str(record.get("name") or ""),
                }
            )
            existing_bridge_families.add(family)

    requires_bridge = any(
        room.get("missing_gain_families") for room in room_results
    )
    if blocked:
        status = "BLOCKED_UNSUPPORTED_ROOM_GAIN_STRUCTURE"
    elif requires_bridge:
        status = "TRANSIENT_SOURCE_TEMPLATE_GAIN_BRIDGE_AVAILABLE"
    else:
        status = "COMPATIBLE_EXISTING_ROOM_GAIN_STRUCTURE"

    return {
        "status": status,
        "target_gain_families": sorted(set(known_targets)),
        "unknown_target_gain_type_labels": unknown_targets,
        "duplicate_target_gain_families": duplicate_targets,
        "rooms": room_results,
        "transient_template_bridges": list(bridge_by_source.values()),
        "room_gain_creation_api": _ROOM_GAIN_CREATION_API_STATUS,
        "source": (
            "references/iesve/IESVE_API_REFERENCE.md: VERoomData and "
            "RoomInternalGain; IESVE help: Appendix A. Known Limitations"
        ),
        "message": (
            "[TO VERIFY] The documented VERoomData API cannot create missing "
            "room-level gain families, and a scope-safe transient source-template "
            "bridge is unavailable. Add the missing gain rows through VE Query "
            "Room, or select every room sharing the affected source template."
            if blocked
            else (
                "Missing room gain families will be materialized through documented "
                "VEThermalTemplate add_gain/remove_gain/apply_changes operations, "
                "verified, and the source template will be restored."
                if requires_bridge
                else "Every target gain family already exists exactly once in each room."
            )
        ),
    }


def _template_review_observations(template: Mapping[str, Any]) -> Dict[str, Any]:
    """Expose likely gap coverage without turning heuristics into a verdict."""

    gains = [
        item
        for item in template.get("casual_gains", [])
        if isinstance(item, Mapping)
    ]
    exchanges = [
        item
        for item in template.get("air_exchanges", [])
        if isinstance(item, Mapping)
    ]
    lighting = [item for item in gains if "light" in _record_label(item)]
    infiltration = [
        item for item in exchanges if "infiltrat" in _record_label(item)
    ]
    non_infiltration = [
        item for item in exchanges if "infiltrat" not in _record_label(item)
    ]
    return {
        "lighting_gain_detected": bool(lighting),
        "lighting_gain_names": [str(item.get("name") or "") for item in lighting],
        "infiltration_exchange_count": len(infiltration),
        "non_infiltration_air_exchange_detected": bool(non_infiltration),
        "non_infiltration_air_exchange_names": [
            str(item.get("name") or "") for item in non_infiltration
        ],
        "interpretation": (
            "Descriptive review aid only. The responsible engineer must confirm "
            "whether lighting and mechanical/natural ventilation belong to the "
            "project scope; these observations are not compliance criteria."
        ),
    }


def _body_identity(body: Any) -> Tuple[str, str]:
    """Return stable room identifier and display name."""

    body_id = str(getattr(body, "id", "") or "").strip()
    name = str(getattr(body, "name", "") or "").strip()
    if not body_id and hasattr(body, "get_properties"):
        try:
            properties = dict(body.get_properties())
            body_id = str(properties.get("id") or "").strip()
            name = name or str(properties.get("name") or "").strip()
        except Exception:
            pass
    return body_id, name or body_id


def collect_inventory(project: Any, model: Any) -> Dict[str, Any]:
    """Collect templates and rooms without changing the active VE project."""

    available_profiles = _available_profile_ids(project)
    try:
        templates = thermal_templates(project, assigned=False)
    except Exception as exc:
        raise ClientTemplateRemediationError(
            "Thermal templates cannot be read: {}".format(exc)
        ) from exc
    template_rows = [
        template_snapshot(handle, template, available_profiles)
        for handle, template in templates.items()
    ]
    template_rows.sort(key=lambda item: (item["name"], item["handle"]))
    name_by_handle = {item["handle"]: item["name"] for item in template_rows}

    try:
        bodies = list(model.get_bodies(False))
    except Exception as exc:
        raise ClientTemplateRemediationError(
            "VE rooms cannot be read: {}".format(exc)
        ) from exc
    rooms: List[Dict[str, Any]] = []
    for body in bodies:
        room_id, room_name = _body_identity(body)
        if not room_id:
            continue
        try:
            state = _room_state(body)
            general = dict(state["general"])
        except Exception:
            continue
        handle = str(
            general.get("thermal_template")
            or general.get("template")
            or ""
        ).strip()
        template_name = str(general.get("thermal_template_name") or "").strip()
        if not template_name:
            template_name = name_by_handle.get(handle, "")
        rooms.append(
            {
                "room_id": room_id,
                "room_name": room_name,
                "current_template_handle": handle,
                "current_template_name": template_name,
                "current_state": state,
                "state_fingerprint_sha256": _sha256(state),
            }
        )
    rooms.sort(key=lambda item: (item["room_name"], item["room_id"]))
    return {
        "templates": template_rows,
        "rooms": rooms,
        "available_profile_ids": available_profiles,
    }


def _find_unique_template(
    inventory: Mapping[str, Any], template_name: str
) -> Dict[str, Any]:
    matches = [
        dict(item)
        for item in inventory.get("templates", [])
        if str(item.get("name") or "") == template_name
    ]
    if len(matches) != 1:
        raise ClientTemplateRemediationError(
            "Expected exactly one template named '{}'; found {}".format(
                template_name, len(matches)
            )
        )
    return matches[0]


def _selected_rooms(
    inventory: Mapping[str, Any], room_ids: Iterable[str]
) -> List[Dict[str, Any]]:
    requested = [str(item).strip() for item in room_ids if str(item).strip()]
    if not requested:
        raise ClientTemplateRemediationError("Select at least one VE room")
    if len(requested) != len(set(requested)):
        raise ClientTemplateRemediationError("Room identifiers must be unique")
    by_id = {
        str(item.get("room_id") or ""): dict(item)
        for item in inventory.get("rooms", [])
    }
    missing = sorted(set(requested) - set(by_id))
    if missing:
        raise ClientTemplateRemediationError(
            "Selected rooms are not present in the active model: {}".format(missing)
        )
    return [by_id[item] for item in requested]


def build_preview_plan(
    project_path: str,
    project_name: str,
    project: Any,
    model: Any,
    template_name: str,
    room_ids: Iterable[str],
    evidence: TemplateEvidence,
    copy_confirmed: bool,
) -> Dict[str, Any]:
    """Build a checksum-bound preview plan; no VE object is changed."""

    normalized_path = str(Path(project_path).resolve())
    if not is_disposable_project(normalized_path):
        raise ClientTemplateRemediationError(
            "Template remediation is allowed only in a saved project copy whose "
            "name ends with _TEST, _COPY or _DISPOSABLE"
        )
    if not copy_confirmed:
        raise ClientTemplateRemediationError(
            "Explicit confirmation that this is a disposable copy is required"
        )
    evidence_errors = evidence.validate()
    if evidence_errors:
        raise ClientTemplateRemediationError(
            "Template evidence is incomplete: {}".format("; ".join(evidence_errors))
        )

    inventory = collect_inventory(project, model)
    template = _find_unique_template(inventory, str(template_name).strip())
    if template.get("missing_profile_references"):
        raise ClientTemplateRemediationError(
            "The selected template references missing profiles: {}".format(
                template["missing_profile_references"]
            )
        )
    selected = _selected_rooms(inventory, room_ids)
    gain_structure = _gain_structure_assessment(template, selected, inventory)
    generated_at = datetime.now().isoformat(timespec="seconds")
    ready_for_technical_apply = evidence.approval_status in {
        APPROVAL_STATUS,
        TECHNICAL_APPLICATION_STATUS,
    } and gain_structure["status"] in {
        "COMPATIBLE_EXISTING_ROOM_GAIN_STRUCTURE",
        "TRANSIENT_SOURCE_TEMPLATE_GAIN_BRIDGE_AVAILABLE",
    }
    if gain_structure["status"] == "BLOCKED_UNSUPPORTED_ROOM_GAIN_STRUCTURE":
        plan_status = "BLOCKED_UNSUPPORTED_ROOM_GAIN_STRUCTURE"
    elif ready_for_technical_apply:
        plan_status = "READY_FOR_APPLY"
    else:
        plan_status = "REVIEW_ONLY"
    plan: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "operation": OPERATION,
        "status": plan_status,
        "generated_at": generated_at,
        "project": {
            "name": str(project_name),
            "path": normalized_path,
            "copy_confirmed": True,
        },
        "template": {
            "name": template["name"],
            "handle": template["handle"],
            "fingerprint_sha256": template["fingerprint_sha256"],
            "referenced_profiles": template["referenced_profiles"],
            "content": {
                "casual_gains": template["casual_gains"],
                "air_exchanges": template["air_exchanges"],
                "room_conditions": template["room_conditions"],
                "apache_systems": template["apache_systems"],
            },
            "review_observations": template["review_observations"],
        },
        "rooms": selected,
        "capability_assessment": {
            "room_gain_structure": gain_structure,
        },
        "evidence": asdict(evidence),
        "guardrails": {
            "explicit_room_selection": True,
            "template_content_not_created_by_script": True,
            "post_assignment_readback_required": True,
            "missing_room_gain_family_blocks_before_mutation": True,
            "rerun_sia3802_audit_before_saving": True,
            "automatic_compliance_claim": False,
            "technical_application_confirmation_required": True,
            "independent_project_approval_required_for_apply": False,
            "independent_review_required_for_compliance_claim": True,
        },
    }
    plan["plan_sha256"] = _sha256(plan)
    return plan


def validate_plan_hash(plan: Mapping[str, Any]) -> None:
    """Reject edited or corrupt preview plans."""

    expected = str(plan.get("plan_sha256") or "")
    payload = dict(plan)
    payload.pop("plan_sha256", None)
    actual = _sha256(payload)
    if not expected or expected != actual:
        raise ClientTemplateRemediationError(
            "Preview-plan checksum mismatch; create a new preview"
        )


def apply_preview_plan(iesve_module: Any, plan: Mapping[str, Any]) -> Dict[str, Any]:
    """Apply one unchanged preview plan and verify all room assignments."""

    validate_plan_hash(plan)
    if plan.get("schema_version") != SCHEMA_VERSION or plan.get("operation") != OPERATION:
        raise ClientTemplateRemediationError("Unsupported remediation plan")
    if plan.get("status") != "READY_FOR_APPLY":
        raise ClientTemplateRemediationError("The remediation plan is not ready")

    from .reference_model.ve_api import IesVeGateway

    gateway = IesVeGateway(iesve_module)
    active_path = str(gateway.project_path.resolve())
    planned_project = dict(plan.get("project") or {})
    if active_path.casefold() != str(planned_project.get("path") or "").casefold():
        raise ClientTemplateRemediationError(
            "The active VE project no longer matches the preview plan"
        )
    if not is_disposable_project(active_path):
        raise ClientTemplateRemediationError(
            "The active project is not an explicitly named disposable copy"
        )

    current = collect_inventory(gateway.project, gateway.model)
    planned_template = dict(plan.get("template") or {})
    current_template = _find_unique_template(
        current, str(planned_template.get("name") or "")
    )
    if current_template.get("fingerprint_sha256") != planned_template.get(
        "fingerprint_sha256"
    ):
        raise ClientTemplateRemediationError(
            "The selected template changed after preview; create a new preview"
        )
    gain_assessment = dict(plan.get("capability_assessment") or {}).get(
        "room_gain_structure", {}
    )
    current_templates_by_handle = {
        str(item.get("handle") or ""): item
        for item in current.get("templates", [])
        if isinstance(item, Mapping)
    }
    for bridge in gain_assessment.get("transient_template_bridges", []):
        source = current_templates_by_handle.get(
            str(bridge.get("source_template_handle") or "")
        )
        if source is None or str(source.get("fingerprint_sha256") or "") != str(
            bridge.get("source_template_fingerprint_sha256") or ""
        ):
            raise ClientTemplateRemediationError(
                "A source template required by the gain bridge changed after "
                "preview; create a new preview"
            )
    current_rooms = _selected_rooms(
        current,
        [str(item.get("room_id") or "") for item in plan.get("rooms", [])],
    )
    before_by_id = {
        str(item.get("room_id") or ""): item for item in plan.get("rooms", [])
    }
    for room in current_rooms:
        before = before_by_id[room["room_id"]]
        for key in (
            "current_template_handle",
            "current_template_name",
            "state_fingerprint_sha256",
        ):
            if str(room.get(key) or "") != str(before.get(key) or ""):
                raise ClientTemplateRemediationError(
                    "Room '{}' changed after preview; create a new preview".format(
                        room["room_name"]
                    )
                )

    receipt = gateway.apply_existing_thermal_template_to_rooms(
        str(planned_template["name"]),
        [room["room_id"] for room in current_rooms],
        structure_bridge=gain_assessment.get("transient_template_bridges", []),
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "operation": OPERATION,
        "status": "APPLIED_AND_READBACK_VERIFIED",
        "applied_at": datetime.now().isoformat(timespec="seconds"),
        "project": planned_project,
        "template": planned_template,
        "evidence": dict(plan.get("evidence") or {}),
        "plan_sha256": plan["plan_sha256"],
        "ve_receipt": _json_safe(receipt),
        "next_required_action": (
            "Rerun the read-only SIA 380/2 audit. Save the VE copy only after "
            "the post-mutation findings have been reviewed."
        ),
        "compliance_claim": "NOT_GRANTED",
    }


def write_json_artifact(path: Path, payload: Mapping[str, Any]) -> Path:
    """Write one project-local UTF-8 JSON artifact atomically."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(_json_safe(payload), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return path


def _latest_artifact(folder: Path, pattern: str) -> Optional[Path]:
    """Return the newest project-local artifact without raising on I/O errors."""

    try:
        paths = [path for path in folder.glob(pattern) if path.is_file()]
        return max(paths, key=lambda path: path.stat().st_mtime) if paths else None
    except OSError:
        return None


def _read_json_artifact(path: Optional[Path]) -> Dict[str, Any]:
    """Read one JSON object for reporting, returning an empty mapping on error."""

    if path is None:
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return {}
    return payload if isinstance(payload, dict) else {}


def latest_remediation_evidence(project_path: str) -> Dict[str, Any]:
    """Summarize the latest template operation for the client audit workbook."""

    root = Path(project_path).resolve()
    folder = root / "sia_compliance_artifacts" / "template_remediation"
    plan_path = _latest_artifact(folder, "sia3802_template_plan_*.json")
    receipt_path = _latest_artifact(folder, "sia3802_template_receipt_*.json")
    plan = _read_json_artifact(plan_path)
    receipt = _read_json_artifact(receipt_path)
    status = str(receipt.get("status") or "").upper()
    if not status and plan:
        status = "PREVIEW_READY_NOT_APPLIED"
    if not status:
        status = "NOT_RUN"

    integrity_status = "NOT_CHECKABLE"
    if plan:
        try:
            validate_plan_hash(plan)
            plan_hash = str(plan.get("plan_sha256") or "")
            receipt_hash = str(receipt.get("plan_sha256") or "")
            integrity_status = (
                "PASS"
                if not receipt or (plan_hash and receipt_hash == plan_hash)
                else "FAIL"
            )
        except ClientTemplateRemediationError:
            integrity_status = "FAIL"

    audit_path = _latest_artifact(
        root / "sia_compliance_artifacts" / "diagnostics",
        "swiss_sia_remediation_probe_*.json",
    )
    post_audit_status = "NOT_APPLICABLE"
    if status == "APPLIED_AND_READBACK_VERIFIED":
        if audit_path is None or receipt_path is None:
            post_audit_status = "REQUIRED"
        else:
            try:
                post_audit_status = (
                    "CURRENT"
                    if audit_path.stat().st_mtime > receipt_path.stat().st_mtime
                    else "REQUIRED"
                )
            except OSError:
                post_audit_status = "NOT_CHECKABLE"

    template = receipt.get("template") or plan.get("template") or {}
    evidence = receipt.get("evidence") or plan.get("evidence") or {}
    rooms = plan.get("rooms") or []
    return {
        "status": status,
        "integrity_status": integrity_status,
        "post_remediation_audit": post_audit_status,
        "template_name": str(template.get("name") or ""),
        "template_fingerprint_sha256": str(
            template.get("fingerprint_sha256") or ""
        ),
        "room_count": len(rooms) if isinstance(rooms, list) else 0,
        "reviewer": str(evidence.get("reviewer") or ""),
        "review_date": str(evidence.get("review_date") or ""),
        "source_document": str(evidence.get("source_document") or ""),
        "source_reference": str(evidence.get("source_reference") or ""),
        "evidence_mode": str(evidence.get("evidence_mode") or "NOT_PROVIDED"),
        "source_trace_status": str(
            evidence.get("source_trace_status") or "NOT_CHECKABLE"
        ),
        "application_confirmation_status": str(
            evidence.get("approval_status") or REVIEW_ONLY_STATUS
        ),
        "plan_path": str(plan_path) if plan_path else "",
        "receipt_path": str(receipt_path) if receipt_path else "",
        "compliance_claim": str(receipt.get("compliance_claim") or "NOT_GRANTED"),
    }
