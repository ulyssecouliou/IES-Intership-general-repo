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
            "Projet jetable actif",
            project_path or "Chemin de projet indisponible",
            (
                "Continuer sur cette copie jetable."
                if disposable
                else "Ouvrir une copie jetable avant toute future correction VE."
            ),
            "Model reviewer",
        )
    )

    external_surfaces = [
        surface
        for room in rooms
        for surface in list(getattr(room, "surfaces", []) or [])
        if bool(getattr(surface, "is_external", False))
        and _has_meaningful_area(surface)
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
            "Classification des surfaces exterieures",
            (
                f"{len(unclassified)} surface(s) exterieure(s) non classee(s) "
                f"sur {len(external_surfaces)} surface(s) significative(s); "
                f"{len(ignored_surface_residues)} residu(s) numerique(s) ignore(s)."
            ),
            (
                "Dans ModelIT, corriger le type ou l'adjacence des surfaces listees "
                "puis verifier leur construction."
                if unclassified
                else "Aucune action."
            ),
            "Model reviewer",
            unclassified,
        )
    )

    windows = [
        opening
        for room in rooms
        for opening in list(getattr(room, "openings", []) or [])
        if bool(getattr(opening, "is_external", False)) and _is_window(opening)
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
            "Proprietes thermiques des fenetres",
            (
                f"{len(invalid_windows)} fenetre(s) sans Uw total ou fraction de cadre "
                f"sur {len(windows)}."
            ),
            (
                "Dans Apache Constructions, affecter une construction vitree complete "
                "aux ouvertures listees; ne pas inventer Uw ni la fraction de cadre."
                if invalid_windows
                else "Aucune action."
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
            ventilation_facade_m3_h_m2=getattr(
                room, "ventilation_facade_m3_h_m2", None
            ),
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
        if exchanges and exchange_names and all(
            "infiltration" in name for name in exchange_names
        ):
            rooms_with_only_infiltration.append(runtime_room)
    ventilation_runtime_confirmed = (
        bool(missing_ventilation)
        and len(rooms_with_only_infiltration) == len(missing_ventilation)
    )
    controls.append(
        _control(
            "MODEL-003",
            "WARNING" if missing_ventilation else "PASS",
            "VE_MODEL_EVIDENCE" if ventilation_runtime_confirmed else "VE_OR_EXTRACTION",
            "Debit de ventilation par local",
            (
                f"{len(missing_ventilation)} local(aux) ne contiennent qu'une infiltration; "
                "aucun Air Exchange de ventilation n'est defini."
                if ventilation_runtime_confirmed
                else f"{len(missing_ventilation)} local(aux) sans debit exploitable sur {len(rooms)}."
            ),
            (
                "Confirmer la strategie de ventilation du projet. Si une ventilation "
                "mecanique est prevue, renseigner ses debits et profils dans VE; sinon, "
                "documenter explicitement l'hypothese de ventilation naturelle ou nulle."
                if ventilation_runtime_confirmed
                else "Verifier les Air Exchanges / Apache Systems. Si VE contient deja les "
                "debits, conserver le modele et qualifier ensuite le chemin d'extraction."
                if missing_ventilation
                else "Aucune action."
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
    lighting_runtime_confirmed = (
        bool(missing_lighting)
        and len(rooms_without_runtime_lighting) == len(missing_lighting)
    )
    controls.append(
        _control(
            "MODEL-004",
            "WARNING" if missing_lighting else "PASS",
            "VE_MODEL_EVIDENCE" if lighting_runtime_confirmed else "VE_OR_EXTRACTION",
            "Puissance d'eclairage par local",
            (
                f"{len(missing_lighting)} local(aux) ne contiennent aucun gain VE de type Lighting; "
                "seuls d'autres types de gains sont presents."
                if lighting_runtime_confirmed
                else f"{len(missing_lighting)} local(aux) sans puissance d'eclairage sur {len(rooms)}."
            ),
            (
                "Ajouter ou affecter un gain Lighting source et profile dans le thermal "
                "template uniquement si l'eclairage fait partie du perimetre du projet; "
                "sinon documenter explicitement son exclusion."
                if lighting_runtime_confirmed
                else "Verifier les gains Lighting du thermal template. Si une puissance est "
                "presente dans VE, conserver le modele et qualifier l'extraction."
                if missing_lighting
                else "Aucune action."
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
            "Resolution des profils de gains",
            f"{len(unresolved_profiles)} local(aux) sans integration journaliere des profils.",
            (
                "Verifier les identifiants des profils journaliers/hebdomadaires et leur "
                "read-back VEScripts; ne pas remplacer un profil absent par ON."
                if unresolved_profiles
                else "Aucune action."
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
            "Fichier APS lisible",
            str(dynamic.get("selected_aps_file") or "Aucun APS selectionne"),
            "Relancer ApacheSim sur la copie et conserver le fichier APS actif."
            if not aps_available
            else "Aucune action.",
            "Simulation engineer",
        )
    )

    heating_available = _numeric(dynamic.get("total_heating_kwh")) is not None
    heating_binding = (aps.get("production_bindings") or {}).get("heating_load")
    runtime_heating_profiles = [
        str((item.get("room_conditions") or {}).get("heating_profile") or "")
        for item in runtime_rooms
    ]
    heating_profiles_off = (
        bool(runtime_heating_profiles)
        and all(profile.upper() == "OFF" for profile in runtime_heating_profiles)
    )
    heating_bound_but_inactive = (
        not heating_available and bool(heating_binding) and heating_profiles_off
    )
    controls.append(
        _control(
            "SIM-002",
            "PASS" if heating_available else "WARNING",
            "SIMULATION_OUTPUT",
            "Besoin annuel de chauffage",
            (
                f"{dynamic.get('total_heating_kwh')} kWh"
                if heating_available
                else (
                    "Variable APS trouvee, mais les profils de chauffage des locaux sont OFF; "
                    "aucune energie positive n'est disponible."
                    if heating_bound_but_inactive
                    else "Variable APS de chauffage non resolue"
                )
            ),
            (
                "Confirmer que l'absence de chauffage est intentionnelle. Si un besoin annuel "
                "de chauffage est requis, affecter le profil de chauffage correct puis resimuler."
                if heating_bound_but_inactive
                else "Activer/exporter le besoin de chauffage dans ApacheSim/Vista puis resimuler."
            )
            if not heating_available
            else "Aucune action.",
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
            "Energies terminales et auxiliaires APS",
            "Manquantes: " + ", ".join(missing_end_uses)
            + (
                "; variables APS non presentes: " + ", ".join(unresolved_aps_bindings)
                if unresolved_aps_bindings
                else ""
            )
            if missing_end_uses
            else "Toutes les familles attendues sont disponibles.",
            "Activer les sorties ApacheSim/Vista requises par le perimetre, resimuler, puis "
            "qualifier leurs noms, unites et signes; ne pas creer une valeur nulle de substitution."
            if missing_end_uses
            else "Aucune action.",
            "Simulation engineer / developer",
        )
    )

    metadata_status = str(dynamic.get("project_metadata_status") or "NOT_PROVIDED")
    weather_match = str(dynamic.get("reviewed_weather_match_status") or "NOT_CHECKABLE")
    metadata_ready = metadata_status.upper() == "AVAILABLE" and weather_match.upper() == "MATCH"
    controls.append(
        _control(
            "EVID-001",
            "PASS" if metadata_ready else "WARNING",
            "REVIEWER_EVIDENCE",
            "Metadonnees climatiques revues",
            f"metadata={metadata_status}; weather_match={weather_match}",
            "Completer le CSV project_metadata avec les donnees reelles et une revue acceptee."
            if not metadata_ready
            else "Aucune action.",
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
