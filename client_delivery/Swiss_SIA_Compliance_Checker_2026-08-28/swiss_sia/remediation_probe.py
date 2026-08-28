"""Build a read-only remediation diagnosis from normalized VE model data.

The probe never changes the VE model.  It converts already extracted room,
surface, opening and APS data into a small set of actionable controls that
separate model corrections, extraction limitations, simulation outputs and
reviewer-owned evidence.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Sequence

# API geometry can contain floating-point slivers after adjacency operations.
# This is a computational tolerance, not a SIA regulatory value.
MIN_MEANINGFUL_AREA_M2 = 1.0e-6


@dataclass(frozen=True)
class RemediationControl:
    """One deterministic PASS, WARNING or FAIL control."""

    control_id: str
    status: str
    category: str
    title: str
    observed: str
    action: str
    owner: str
    affected_objects: List[Dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class RemediationDiagnosis:
    """Complete read-only remediation result for the active VE project."""

    status: str
    project_path: str
    project_label: str
    room_count: int
    controls: List[RemediationControl]
    next_actions: List[str]
    guardrail: str = (
        "Diagnostic de preparation uniquement; aucune conclusion de conformite "
        "SIA 380/2 ou de validation SIA 4010 n'est emise."
    )

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable representation."""
        return asdict(self)


def _numeric(value: Any) -> Optional[float]:
    """Return a finite numeric value without treating booleans as numbers."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        number = float(value)
        if number == number and number not in (float("inf"), float("-inf")):
            return number
    return None


def _object_record(item: Any, **extra: Any) -> Dict[str, Any]:
    """Return a compact object record suitable for the audit JSON."""
    record: Dict[str, Any] = {
        "id": str(getattr(item, "id", "") or ""),
        "name": str(getattr(item, "name", "") or ""),
    }
    record.update(extra)
    return record


def _is_classified_external_surface(surface: Any) -> bool:
    """Return whether an external surface has a usable envelope type."""
    surface_type = str(getattr(surface, "surface_type", "") or "").lower()
    return any(token in surface_type for token in ("wall", "roof", "floor", "ceiling"))


def _is_window(opening: Any) -> bool:
    """Return whether an opening is a window/glazed element."""
    opening_type = str(getattr(opening, "opening_type", "") or "").lower()
    return any(token in opening_type for token in ("window", "glaz", "rooflight"))


def _has_meaningful_area(item: Any) -> bool:
    """Return whether an extracted geometry item is larger than API noise."""
    area = _numeric(getattr(item, "area", None))
    return area is not None and abs(area) > MIN_MEANINGFUL_AREA_M2


def _status_from_controls(controls: Sequence[RemediationControl]) -> str:
    """Return the conservative aggregate status for the diagnosis."""
    statuses = {control.status.upper() for control in controls}
    if "FAIL" in statuses:
        return "FAIL"
    if "WARNING" in statuses:
        return "WARNING"
    return "PASS"


def _control(
    control_id: str,
    status: str,
    category: str,
    title: str,
    observed: str,
    action: str,
    owner: str,
    affected: Optional[Iterable[Dict[str, Any]]] = None,
) -> RemediationControl:
    """Create one normalized remediation control."""
    return RemediationControl(
        control_id=control_id,
        status=status,
        category=category,
        title=title,
        observed=observed,
        action=action,
        owner=owner,
        affected_objects=list(affected or []),
    )


def build_remediation_diagnosis(
    rooms: Sequence[Any],
    dynamic_results: Optional[Dict[str, Any]],
    project_path: str,
    runtime_inventory: Optional[Dict[str, Any]] = None,
    aps_inventory: Optional[Dict[str, Any]] = None,
) -> RemediationDiagnosis:
    """Build an actionable diagnosis without accessing or changing VE objects."""
    dynamic = dict(dynamic_results or {})
    runtime = dict(runtime_inventory or {})
    aps = dict(aps_inventory or {})
    runtime_rooms = list(runtime.get("rooms", []) or [])
    project_label = project_path.rstrip("/\\").replace("/", "\\").split("\\")[-1]
    controls: List[RemediationControl] = []

    disposable = project_label.upper().endswith(("_TEST", "_COPY", "_DISPOSABLE"))
    controls.append(
        _control(
            "RUN-001",
            "PASS" if disposable else "WARNING",
            "RUN_GUARD",
            "Active disposable project",
            project_path or "Project path unavailable",
            (
                "Continue on this disposable copy."
                if disposable
                else "Open a disposable copy before making any future VE correction."
            ),
            "Model reviewer",
        )
    )

    external_surfaces = [
        surface
        for room in rooms
        for surface in list(getattr(room, "surfaces", []) or [])
        if bool(getattr(surface, "is_external", False)) and _has_meaningful_area(surface)
    ]
    ignored_surface_residues = [
        surface
        for room in rooms
        for surface in list(getattr(room, "surfaces", []) or [])
        if bool(getattr(surface, "is_external", False))
        and not _has_meaningful_area(surface)
    ]
    unclassified = [
        _object_record(
            surface,
            room_id=str(getattr(room, "id", "") or ""),
            room_name=str(getattr(room, "name", "") or ""),
            surface_type=str(getattr(surface, "surface_type", "") or ""),
            construction_ids=list(getattr(surface, "construction_ids", []) or []),
            area_m2=_numeric(getattr(surface, "area", None)),
        )
        for room in rooms
        for surface in list(getattr(room, "surfaces", []) or [])
        if bool(getattr(surface, "is_external", False))
        and _has_meaningful_area(surface)
        and not _is_classified_external_surface(surface)
    ]
    controls.append(
        _control(
            "MODEL-001",
            "FAIL" if unclassified else "PASS",
            "VE_MODEL",
            "External surface classification",
            (
                f"{len(unclassified)} unclassified external surface(s) out of "
                f"{len(external_surfaces)} significant surface(s); "
                f"{len(ignored_surface_residues)} numerical residue(s) ignored."
            ),
            (
                "In ModelIT, correct the type or adjacency of the listed surfaces, "
                "then verify their construction."
                if unclassified
                else "No action required."
            ),
            "Model reviewer",
            unclassified,
        )
    )

    windows = [
        opening
        for room in rooms
        for opening in list(getattr(room, "openings", []) or [])
        if bool(getattr(opening, "is_external", False))
        and _is_window(opening)
        and _has_meaningful_area(opening)
    ]
    invalid_windows = [
        _object_record(
            opening,
            room_id=str(getattr(room, "id", "") or ""),
            room_name=str(getattr(room, "name", "") or ""),
            construction_id=str(getattr(opening, "construction_id", "") or ""),
            area_m2=_numeric(getattr(opening, "area", None)),
            u_value_w_m2k=_numeric(getattr(opening, "u_value", None)),
            frame_fraction=_numeric(getattr(opening, "frame_fraction", None)),
        )
        for room in rooms
        for opening in list(getattr(room, "openings", []) or [])
        if bool(getattr(opening, "is_external", False))
        and _is_window(opening)
        and _has_meaningful_area(opening)
        and (
            _numeric(getattr(opening, "u_value", None)) is None
            or _numeric(getattr(opening, "frame_fraction", None)) is None
        )
    ]
    controls.append(
        _control(
            "MODEL-002",
            "FAIL" if invalid_windows else "PASS",
            "VE_MODEL",
            "Window thermal properties",
            (
                f"{len(invalid_windows)} window(s) without whole-window U-value or "
                f"frame fraction out of {len(windows)}."
            ),
            (
                "In Apache Constructions, assign a complete glazed construction to "
                "the listed openings; do not invent Uw or the frame fraction."
                if invalid_windows
                else "No action required."
            ),
            "Facade / model reviewer",
            invalid_windows,
        )
    )

    missing_ventilation = [
        _object_record(
            room,
            ventilation_rate=getattr(room, "ventilation_rate", None),
            ventilation_m3_h_m2=getattr(room, "ventilation_m3_h_m2", None),
            ventilation_facade_m3_h_m2=getattr(room, "ventilation_facade_m3_h_m2", None),
        )
        for room in rooms
        if not any(
            _numeric(value) is not None
            for value in (
                getattr(room, "ventilation_rate", None),
                getattr(room, "ventilation_m3_h_m2", None),
                getattr(room, "ventilation_facade_m3_h_m2", None),
            )
        )
    ]
    rooms_with_only_infiltration = []
    for runtime_room in runtime_rooms:
        exchanges = list(runtime_room.get("air_exchanges", []) or [])
        exchange_names = [
            str(exchange.get("name") or exchange.get("type_str") or "").lower()
            for exchange in exchanges
            if isinstance(exchange, dict)
        ]
        if (
            exchanges
            and exchange_names
            and all("infiltration" in name for name in exchange_names)
        ):
            rooms_with_only_infiltration.append(runtime_room)
    ventilation_runtime_confirmed = bool(missing_ventilation) and len(
        rooms_with_only_infiltration
    ) == len(missing_ventilation)
    controls.append(
        _control(
            "MODEL-003",
            "WARNING" if missing_ventilation else "PASS",
            "VE_MODEL_EVIDENCE" if ventilation_runtime_confirmed else "VE_OR_EXTRACTION",
            "Room ventilation flow",
            (
                f"{len(missing_ventilation)} room(s) contain infiltration only; no "
                "ventilation Air Exchange is defined."
                if ventilation_runtime_confirmed
                else f"{len(missing_ventilation)} room(s) without a usable flow out of {len(rooms)}."
            ),
            (
                "Confirm the project ventilation strategy. If mechanical ventilation "
                "is intended, enter its flows and profiles in VE; otherwise document "
                "the natural-ventilation or zero-ventilation assumption explicitly."
                if ventilation_runtime_confirmed
                else (
                    "Review Air Exchanges / Apache Systems. If VE already contains the "
                    "flows, preserve the model and qualify the extraction path."
                    if missing_ventilation
                    else "No action required."
                )
            ),
            "HVAC engineer / developer",
            missing_ventilation,
        )
    )

    missing_lighting = [
        _object_record(
            room,
            thermal_template_id=str(getattr(room, "thermal_template_id", "") or ""),
            extracted_internal_gains=dict(getattr(room, "internal_gains", {}) or {}),
        )
        for room in rooms
        if _numeric((getattr(room, "internal_gains", {}) or {}).get("lighting")) is None
    ]
    rooms_without_runtime_lighting = []
    for runtime_room in runtime_rooms:
        gains = list(runtime_room.get("internal_gains", []) or [])
        gain_types = " ".join(
            "{} {}".format(gain.get("type_str", ""), gain.get("name", ""))
            for gain in gains
            if isinstance(gain, dict)
        ).lower()
        if gains and not any(
            token in gain_types for token in ("lighting", "fluorescent", "tungsten")
        ):
            rooms_without_runtime_lighting.append(runtime_room)
    lighting_runtime_confirmed = bool(missing_lighting) and len(
        rooms_without_runtime_lighting
    ) == len(missing_lighting)
    controls.append(
        _control(
            "MODEL-004",
            "WARNING" if missing_lighting else "PASS",
            "VE_MODEL_EVIDENCE" if lighting_runtime_confirmed else "VE_OR_EXTRACTION",
            "Room lighting power",
            (
                f"{len(missing_lighting)} room(s) contain no VE Lighting gain; only "
                "other gain types are present."
                if lighting_runtime_confirmed
                else f"{len(missing_lighting)} room(s) without lighting power out of {len(rooms)}."
            ),
            (
                "Add or assign a source-traced, profiled Lighting gain in the thermal "
                "template only if lighting is in scope; otherwise document its exclusion."
                if lighting_runtime_confirmed
                else (
                    "Review Lighting gains in the thermal template. If power is present "
                    "in VE, preserve the model and qualify its extraction."
                    if missing_lighting
                    else "No action required."
                )
            ),
            "Lighting engineer / developer",
            missing_lighting,
        )
    )

    unresolved_profiles = [
        _object_record(
            room,
            daily_method=str(getattr(room, "internal_gains_daily_method", "") or ""),
            gain_details=list(getattr(room, "internal_gain_details", []) or []),
        )
        for room in rooms
        if _numeric(getattr(room, "internal_gains_wh_m2_day", None)) is None
    ]
    controls.append(
        _control(
            "API-001",
            "WARNING" if unresolved_profiles else "PASS",
            "VESCRIPT_EXTRACTION",
            "Internal-gain profile resolution",
            f"{len(unresolved_profiles)} room(s) without daily profile integration.",
            (
                "Verify daily/weekly profile identifiers and their VEScripts read-back; "
                "do not replace a missing profile with ON."
                if unresolved_profiles
                else "No action required."
            ),
            "Developer",
            unresolved_profiles,
        )
    )

    aps_available = str(dynamic.get("status") or "").upper() == "AVAILABLE"
    controls.append(
        _control(
            "SIM-001",
            "PASS" if aps_available else "WARNING",
            "SIMULATION_OUTPUT",
            "Readable APS file",
            str(dynamic.get("selected_aps_file") or "No APS selected"),
            (
                "Run ApacheSim again on the copy and retain the active APS file."
                if not aps_available
                else "No action required."
            ),
            "Simulation engineer",
        )
    )

    heating_available = _numeric(dynamic.get("total_heating_kwh")) is not None
    heating_binding = (aps.get("production_bindings") or {}).get("heating_load")
    runtime_heating_profiles = [
        str((item.get("room_conditions") or {}).get("heating_profile") or "")
        for item in runtime_rooms
    ]
    heating_profiles_off = bool(runtime_heating_profiles) and all(
        profile.upper() == "OFF" for profile in runtime_heating_profiles
    )
    heating_bound_but_inactive = (
        not heating_available and bool(heating_binding) and heating_profiles_off
    )
    controls.append(
        _control(
            "SIM-002",
            "PASS" if heating_available else "WARNING",
            "SIMULATION_OUTPUT",
            "Annual heating need",
            (
                f"{dynamic.get('total_heating_kwh')} kWh"
                if heating_available
                else (
                    "APS variable found, but room heating profiles are OFF; no positive "
                    "energy value is available."
                    if heating_bound_but_inactive
                    else "APS heating variable unresolved"
                )
            ),
            (
                (
                    "Confirm that the absence of heating is intentional. If annual heating "
                    "need is required, assign the correct heating profile and resimulate."
                    if heating_bound_but_inactive
                    else "Enable/export heating need in ApacheSim/Vista and resimulate."
                )
                if not heating_available
                else "No action required."
            ),
            "Simulation engineer / developer",
        )
    )

    end_use_keys = (
        "total_lighting_kwh",
        "total_fan_kwh",
        "total_pump_kwh",
        "total_auxiliary_kwh",
        "total_coil_heating_kwh",
        "total_coil_cooling_kwh",
    )
    missing_end_uses = [key for key in end_use_keys if _numeric(dynamic.get(key)) is None]
    unresolved_aps_bindings = list(aps.get("unresolved_bindings", []) or [])
    controls.append(
        _control(
            "SIM-003",
            "WARNING" if missing_end_uses else "PASS",
            "SIMULATION_OUTPUT",
            "APS end-use and auxiliary energy",
            (
                "Missing: "
                + ", ".join(missing_end_uses)
                + (
                    "; APS variables not present: " + ", ".join(unresolved_aps_bindings)
                    if unresolved_aps_bindings
                    else ""
                )
                if missing_end_uses
                else "All expected output families are available."
            ),
            (
                "Enable the ApacheSim/Vista outputs required by the scope, resimulate, then "
                "qualify their names, units and signs; do not create zero-value substitutes."
                if missing_end_uses
                else "No action required."
            ),
            "Simulation engineer / developer",
        )
    )

    metadata_status = str(dynamic.get("project_metadata_status") or "NOT_PROVIDED")
    weather_match = str(dynamic.get("reviewed_weather_match_status") or "NOT_CHECKABLE")
    metadata_ready = (
        metadata_status.upper() == "AVAILABLE" and weather_match.upper() == "MATCH"
    )
    controls.append(
        _control(
            "EVID-001",
            "PASS" if metadata_ready else "WARNING",
            "REVIEWER_EVIDENCE",
            "Reviewed climate metadata",
            f"metadata={metadata_status}; weather_match={weather_match}",
            (
                "Complete project_metadata.csv with actual data and an accepted review."
                if not metadata_ready
                else "No action required."
            ),
            "Compliance reviewer",
        )
    )

    next_actions: List[str] = []
    for control in controls:
        if control.status == "FAIL":
            next_actions.append(f"{control.control_id}: {control.action}")
    for control in controls:
        if control.status == "WARNING":
            next_actions.append(f"{control.control_id}: {control.action}")

    return RemediationDiagnosis(
        status=_status_from_controls(controls),
        project_path=project_path,
        project_label=project_label or "VE_Project",
        room_count=len(rooms),
        controls=controls,
        next_actions=next_actions,
    )
