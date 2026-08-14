"""Build the SIA 380/2 reference-project input specification from a VE model.

A complete SIA 380/2 conclusion compares the project's calculated demand with
the demand of the *reference project*: the same building, with the normative
reference values substituted for the envelope and system inputs. The component
checks alone are diagnostics, so this comparison is the decisive gate.

This module produces the deterministic **input specification** for that
reference run: for every construction the model actually uses, it states the
project value, the normative reference value with its SIA locator, and whether
the substitution is resolvable. It does not simulate anything and it never
produces a demand figure - the reference demand still requires a VE/ApacheSim
run of the substituted model, and the accepted comparison still requires the
reviewer gate in ``evidence_manager``.

Conservatism: a construction whose project value cannot be extracted is a
blocker, never silently substituted; a surface the model does not classify is
reported as unclassified rather than mapped to a guessed reference value. Every
reference value is read from the encoded, source-traced SIA tables - none is
computed or interpolated here.
"""

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .config import (
    SIA3802_COOLING_AIR_CHILLER_MAX_KW,
    SIA3802_GENERATION_REFERENCE,
    SIA3802_LIMIT_VALUES,
    SIA3802_SOURCE_REFERENCES,
)
from .model_analyzer import RoomData

# Normalized surface type -> reference parameter key in SIA3802_LIMIT_VALUES.
# Only externally-exposed opaque types are substituted here; internal
# partitions depend on adjacency evidence the checker treats separately.
_SURFACE_PARAMETERS: Dict[str, str] = {
    "wall": "external_wall_u",
    "roof": "flat_roof_u",
    "floor": "ground_floor_u",
}
_SURFACE_SOURCE_KEY = "table_3"

# Opening parameter -> (reference key, attribute on OpeningData, unit).
# The visible transmittance tau_v reads straight from its attribute; the glazing
# g-value g_perp needs the EN 410 comparability gate below, so it is handled
# separately rather than as a plain attribute read.
_OPENING_PARAMETERS: Tuple[Tuple[str, str, str], ...] = (
    ("window_u", "u_value", "W/(m2K)"),
    ("window_frame_fraction", "frame_fraction", "-"),
    ("glazing_light_transmittance", "visible_transmittance", "-"),
)
_OPENING_SOURCE_KEY = "table_2"

# The reference key for the glazing g-value g_perp (Table 2). Its project value
# is only substitutable when the modelled g-value is a proven EN 410 g_perp.
_GLAZING_G_PARAMETER = "glazing_g_value"

# Whole-building infiltration per net floor area (Table 2). Unlike the envelope
# and openings this is a single building input, not a per-construction value.
_INFILTRATION_PARAMETER = "infiltration_m3_h_m2"
_INFILTRATION_SOURCE_KEY = "table_2"

# Numerical residues below one square millimetre are topology artefacts, not
# physical envelope elements.  This is an engineering/API tolerance only; it
# is not a regulatory threshold and never substitutes a real SIA input.
_MIN_MEANINGFUL_AREA_M2 = 1.0e-6

SUBSTITUTABLE = "SUBSTITUTABLE"
PROJECT_VALUE_MISSING = "PROJECT_VALUE_MISSING"
UNCLASSIFIED = "UNCLASSIFIED"
# The reference project fixes this input regardless of the project (Table 2
# "valeur limite"/"valeur cible" identical and prescriptive). No project value
# is compared, so a directive is resolved, never a blocker.
REFERENCE_DIRECTIVE = "REFERENCE_DIRECTIVE"
# SIA 380/2:2022 §7.2.5.3 : les paramètres d'usage SIA 2024 sont IDENTIQUES
# au projet et au projet de référence. Ces grandeurs ne font pas l'objet d'une
# substitution différenciante ; elles sont donc résolues (jamais un bloqueur)
# avec project_value=None et reference_value = valeur du tableau SIA 2024.
STANDARD_USAGE_INPUT = "STANDARD_USAGE_INPUT"

# Table 2 covers the complete reference-project model.  The current automated
# specification resolves only the families below.  Keeping the remaining
# families explicit prevents a partial envelope plan from being mistaken for a
# runnable SIA 380/2 reference project.
IMPLEMENTED_REFERENCE_INPUT_FAMILIES: Tuple[str, ...] = (
    "opaque_envelope_constructions",
    "window_u_value_and_frame_fraction",
    "glazing_solar_and_visible_properties",
    "infiltration",
    "cooling_generation_and_auxiliaries",
    "heating_generation",
    "emission_system_and_unlimited_capacity",
    # SIA 380/2:2022 §7.2.5.3 : consignes et gains internes identiques
    # projet/référence — résolus depuis le JSON SIA 2024:2021.
    "sia2024_internal_gains_profiles_and_setpoints",
)
MISSING_REFERENCE_INPUT_FAMILIES: Tuple[str, ...] = (
    "thermal_bridges",
    "glazed_area_ratio_solar_protection_and_control",
    "sia3874_lighting_power_and_control",
    "ventilation_system_and_controls",
    "photovoltaic_generation",
    "sia380_annual_aggregation_and_weighting",
)

# ---------------------------------------------------------------------------
# Données SIA 2024 : loader lazy + cache module-level
# ---------------------------------------------------------------------------

# Chemin absolu vers le fichier JSON SIA 2024 dans le dépôt.
# Ne dépend d'aucun import iesve ; le fichier fait partie du dépôt et est
# lisible en CI Python pur.
_SIA2024_JSON_PATH: str = os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "refs", "reference-data", "sia-2024-2021.usage-data.json",
    )
)

# Locateur source inséré dans chaque substitution STANDARD_USAGE_INPUT.
_SIA2024_SOURCE: str = (
    "SIA 2024:2021 Raumdatenblätter V221"
    " | refs/reference-data/sia-2024-2021.usage-data.json"
)

# Symboles extraits pour chaque usage résolu.
# (paramètre engine, colonne JSON, unité de repli si colonne absente)
# Article de norme : SIA 380/2:2022 §7.2.5.3 + SIA 2024 Table 2.
# IMPORTANT : on utilise col30 (theta_i_mean, exploitation) et jamais
# col28 (theta_i_design) — cf. note du norm-analyst.
_SIA2024_USAGE_SYMBOLS: Tuple[Tuple[str, str, str], ...] = (
    ("theta_i_mean", "30", "°C"),   # Consigne exploitation (col30 — PAS col28)
    ("phi_i",        "34", "%"),    # Humidité relative
    ("A_p",          "42", "m²"),   # Surface par personne
    ("M",            "43", "met"),  # Activité métabolique
    ("p_Be",         "51", "W/m2"), # Puissance électrique équipements
    ("E_vm",         "64", "lx"),   # Éclairement moyen
)

# Cache module-level : chargé au premier appel de _load_sia2024_usage_data.
_SIA2024_DATA_CACHE: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class ReferenceSubstitution:
    """One normative substitution to apply when building the reference project."""

    parameter: str
    scope: str
    element_type: str
    project_value: Optional[float]
    reference_value: Optional[float]
    unit: str
    source: str
    status: str
    affected_elements: int
    # Set only on REFERENCE_DIRECTIVE rows: the fixed reference-run instruction
    # (e.g. convective emission, unlimited capacity) that Table 2 imposes
    # regardless of the project value. None on numeric substitutions.
    directive: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Return the substitution as serializable data."""

        return {
            "parameter": self.parameter,
            "scope": self.scope,
            "element_type": self.element_type,
            "project_value": self.project_value,
            "reference_value": self.reference_value,
            "unit": self.unit,
            "source": self.source,
            "status": self.status,
            "affected_elements": self.affected_elements,
            "directive": self.directive,
        }


@dataclass(frozen=True)
class ReferenceProjectSpecification:
    """Deterministic input set for the SIA 380/2 reference-project run."""

    status: str
    substitutions: Tuple[ReferenceSubstitution, ...]
    blockers: Tuple[str, ...]
    notes: Tuple[str, ...]
    implemented_input_families: Tuple[str, ...]
    missing_input_families: Tuple[str, ...]

    @property
    def is_complete(self) -> bool:
        """Return whether every required substitution is resolvable."""

        return self.status == "READY_FOR_REFERENCE_RUN"

    def to_dict(self) -> Dict[str, Any]:
        """Return the specification as serializable data."""

        return {
            "status": self.status,
            "substitutions": [item.to_dict() for item in self.substitutions],
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "implemented_input_families": list(self.implemented_input_families),
            "missing_input_families": list(self.missing_input_families),
            "is_complete": self.is_complete,
        }


def _source(key: str) -> str:
    """Return the SIA locator recorded for one source-reference key."""

    return str(SIA3802_SOURCE_REFERENCES.get(key, "")) or "SIA 380/2:2022"


def _float_or_none(value: Any) -> Optional[float]:
    """Return a float when the value is a real number, otherwise None."""

    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _construction_scope(construction_ids: Any, fallback: str) -> str:
    """Return a stable construction label used to group substitutions."""

    if isinstance(construction_ids, (list, tuple, set)):
        labels = sorted(str(item).strip() for item in construction_ids if str(item).strip())
        if labels:
            return ", ".join(labels)
    text = str(construction_ids or "").strip()
    return text or fallback


def _normalize_surface_type(model_analyzer: Any, surface: Any) -> str:
    """Normalize a surface type, reusing the analyzer's own classification."""

    normalizer = getattr(model_analyzer, "_normalize_surface_type", None)
    if callable(normalizer):
        return normalizer(getattr(surface, "surface_type", ""))
    return str(getattr(surface, "surface_type", "") or "").strip().lower()


def _is_window_opening(opening: Any) -> bool:
    """Return whether an external opening is a window/glazed element."""

    opening_type = str(getattr(opening, "opening_type", "") or "").strip().lower()
    return any(token in opening_type for token in ("window", "glaz", "rooflight"))


def _comparable_g_perp(opening: Any) -> Optional[float]:
    """Return the glazing g_perp only when it is a proven EN 410 value.

    Table 2 substitutes the glazing g-value g_perp (verre seul, incidence
    normale). A modelled solar factor is comparable to that reference only when
    its source is proven as EN 410 g_perp; otherwise it may be a g_total that
    already includes shading, which must never be silently substituted. This
    mirrors ``SIA3802Checker._is_sia_comparable_g_value`` so the reference
    specification and the component check agree on what counts as a g_perp.
    """

    source = str(getattr(opening, "solar_factor_source", "") or "").lower()
    en410_value = _float_or_none(getattr(opening, "g_value_bs_en_410", None))
    if "bs_en_410" not in source and en410_value is None:
        return None
    # Prefer the value the component check compares (solar_factor); fall back to
    # the explicit EN 410 field when the solar factor is not populated.
    return _float_or_none(getattr(opening, "solar_factor", None)) if getattr(
        opening, "solar_factor", None
    ) is not None else en410_value


def _collect_surface_substitutions(
    rooms: Sequence[RoomData], model_analyzer: Any
) -> Tuple[List[ReferenceSubstitution], List[str]]:
    """Group external opaque surfaces by construction and pair them with Table 3."""

    # scope -> {parameter, values, count, unclassified}
    grouped: Dict[Tuple[str, str], Dict[str, Any]] = {}
    unclassified: Dict[str, int] = {}
    for room in rooms:
        for surface in room.surfaces or []:
            if not getattr(surface, "is_external", False):
                continue
            net_area = _float_or_none(getattr(surface, "net_area", surface.area))
            if net_area is None or abs(net_area) <= _MIN_MEANINGFUL_AREA_M2:
                continue
            surface_type = _normalize_surface_type(model_analyzer, surface)
            parameter = _SURFACE_PARAMETERS.get(surface_type)
            scope = _construction_scope(
                getattr(surface, "construction_ids", None),
                getattr(surface, "name", "") or getattr(surface, "id", "") or "unnamed",
            )
            if parameter is None:
                unclassified[scope] = unclassified.get(scope, 0) + 1
                continue
            entry = grouped.setdefault(
                (scope, parameter),
                {"values": [], "count": 0, "element_type": surface_type},
            )
            entry["count"] += 1
            value = _float_or_none(getattr(surface, "u_value", None))
            if value is not None:
                entry["values"].append(value)

    substitutions: List[ReferenceSubstitution] = []
    blockers: List[str] = []
    for (scope, parameter), entry in sorted(grouped.items()):
        values = entry["values"]
        # A construction must expose one consistent project value; the maximum
        # is reported when VE returns per-surface variations, and the spread is
        # never averaged away silently.
        project_value = max(values) if values else None
        status = SUBSTITUTABLE if project_value is not None else PROJECT_VALUE_MISSING
        if status == PROJECT_VALUE_MISSING:
            blockers.append(
                "No project U-value could be extracted for {} ({} surfaces)".format(
                    scope, entry["count"]
                )
            )
        substitutions.append(
            ReferenceSubstitution(
                parameter=parameter,
                scope=scope,
                element_type=entry["element_type"],
                project_value=project_value,
                reference_value=_float_or_none(SIA3802_LIMIT_VALUES.get(parameter)),
                unit="W/(m2K)",
                source=_source(_SURFACE_SOURCE_KEY),
                status=status,
                affected_elements=entry["count"],
            )
        )
    for scope, count in sorted(unclassified.items()):
        substitutions.append(
            ReferenceSubstitution(
                parameter="unclassified_external_surface",
                scope=scope,
                element_type="unclassified",
                project_value=None,
                reference_value=None,
                unit="",
                source=_source(_SURFACE_SOURCE_KEY),
                status=UNCLASSIFIED,
                affected_elements=count,
            )
        )
        blockers.append(
            "{} external surfaces of {} are not classified as wall/roof/floor".format(
                count, scope
            )
        )
    return substitutions, blockers


def _collect_opening_substitutions(
    rooms: Sequence[RoomData],
) -> Tuple[List[ReferenceSubstitution], List[str]]:
    """Group external openings by construction and pair them with Table 2."""

    grouped: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for room in rooms:
        for opening in room.openings or []:
            if not getattr(opening, "is_external", False):
                continue
            area = _float_or_none(getattr(opening, "area", None))
            if area is None or abs(area) <= _MIN_MEANINGFUL_AREA_M2:
                continue
            if not _is_window_opening(opening):
                continue
            scope = _construction_scope(
                getattr(opening, "construction_id", None),
                getattr(opening, "name", "") or getattr(opening, "id", "") or "unnamed",
            )
            for parameter, attribute, unit in _OPENING_PARAMETERS:
                entry = grouped.setdefault(
                    (scope, parameter),
                    {"values": [], "count": 0, "unit": unit},
                )
                entry["count"] += 1
                value = _float_or_none(getattr(opening, attribute, None))
                if value is not None:
                    entry["values"].append(value)

            # g_perp is gated on EN 410 provenance, so it cannot share the plain
            # attribute loop above: a non-comparable g-value leaves no project
            # value and is reported as a blocker, never substituted.
            g_entry = grouped.setdefault(
                (scope, _GLAZING_G_PARAMETER),
                {"values": [], "count": 0, "unit": "-"},
            )
            g_entry["count"] += 1
            g_value = _comparable_g_perp(opening)
            if g_value is not None:
                g_entry["values"].append(g_value)

    substitutions: List[ReferenceSubstitution] = []
    blockers: List[str] = []
    for (scope, parameter), entry in sorted(grouped.items()):
        values = entry["values"]
        project_value = max(values) if values else None
        status = SUBSTITUTABLE if project_value is not None else PROJECT_VALUE_MISSING
        if status == PROJECT_VALUE_MISSING:
            if parameter == _GLAZING_G_PARAMETER:
                blockers.append(
                    "No EN 410-comparable g_perp could be extracted for glazing "
                    "{} ({} openings); a g_total including shading must not be "
                    "substituted for the Table 2 g_perp".format(scope, entry["count"])
                )
            else:
                blockers.append(
                    "No project {} could be extracted for glazing {} ({} openings)".format(
                        parameter, scope, entry["count"]
                    )
                )
        substitutions.append(
            ReferenceSubstitution(
                parameter=parameter,
                scope=scope,
                element_type="opening",
                project_value=project_value,
                reference_value=_float_or_none(SIA3802_LIMIT_VALUES.get(parameter)),
                unit=entry["unit"],
                source=_source(_OPENING_SOURCE_KEY),
                status=status,
                affected_elements=entry["count"],
            )
        )
    return substitutions, blockers


def _collect_infiltration_substitution(
    rooms: Sequence[RoomData],
) -> Tuple[List[ReferenceSubstitution], List[str]]:
    """Pair the whole-building infiltration with the Table 2 reference value.

    Infiltration is a single building input in m3/(h.m2) of net floor area, so
    one substitution is emitted for the whole model. The worst (maximum) room
    value is reported, never an average, matching the conservatism used for the
    envelope. Only ``infiltration_m3_h_m2`` is directly comparable; a room that
    exposes infiltration in another unit is a blocker for unit conversion, not a
    silent substitution -- the same comparability rule the component check uses.
    """

    values: List[float] = []
    unit_incomparable = 0
    for room in rooms:
        value = _float_or_none(getattr(room, "infiltration_m3_h_m2", None))
        if value is not None:
            values.append(value)
        elif getattr(room, "infiltration_rate", None) is not None:
            unit_incomparable += 1

    reference_value = _float_or_none(SIA3802_LIMIT_VALUES.get(_INFILTRATION_PARAMETER))
    project_value = max(values) if values else None
    status = SUBSTITUTABLE if project_value is not None else PROJECT_VALUE_MISSING
    blockers: List[str] = []
    if project_value is None:
        if unit_incomparable:
            blockers.append(
                "Infiltration is present for {} room(s) but not in a comparable "
                "m3/(h.m2) unit; provide the conversion before substituting the "
                "Table 2 reference".format(unit_incomparable)
            )
        else:
            blockers.append(
                "No comparable project infiltration in m3/(h.m2) could be "
                "extracted for the building"
            )
    substitution = ReferenceSubstitution(
        parameter=_INFILTRATION_PARAMETER,
        scope="building",
        element_type="infiltration",
        project_value=project_value,
        reference_value=reference_value,
        unit="m3/(h.m2)",
        source=_source(_INFILTRATION_SOURCE_KEY),
        status=status,
        affected_elements=len(values) + unit_incomparable,
    )
    return [substitution], blockers


def _reference_band(table_key: str, capacity: float) -> Optional[Dict[str, Any]]:
    """Return the SIA 380/2 tableau 5-9 band whose power range holds capacity.

    Bands are ordered by ascending inclusive upper bound; the first band whose
    ``upper_kw`` is None (open top) or >= capacity matches. Returns None when
    the capacity is above every encoded band (e.g. an air-water heat pump above
    150 kW, which Table 8 does not tabulate -- a blocker, never an extrapolation).
    """

    for band in SIA3802_GENERATION_REFERENCE[table_key]["bands"]:
        upper = band["upper_kw"]
        if upper is None or capacity <= upper:
            return band
    return None


def _generation_substitution(
    parameter: str,
    scope: str,
    element_type: str,
    unit: str,
    table_key: str,
    reference_value: Optional[float],
    project_value: Optional[float],
) -> ReferenceSubstitution:
    """Build one generation substitution, tagging the SN EN 14825 caveat."""

    source = SIA3802_GENERATION_REFERENCE[table_key]["source"]
    if SIA3802_GENERATION_REFERENCE[table_key]["grandeur"] == "SCOP":
        # SCOP is defined per SN EN 14825, which is not in refs/, so the
        # equivalence with the VE SCoP output is not proven here.
        source += " [SCOP per SN EN 14825 - VE index equivalence TO VERIFY]"
    status = (
        SUBSTITUTABLE
        if reference_value is not None and project_value is not None
        else PROJECT_VALUE_MISSING
    )
    return ReferenceSubstitution(
        parameter=parameter,
        scope=scope,
        element_type=element_type,
        project_value=project_value,
        reference_value=reference_value,
        unit=unit,
        source=source,
        status=status,
        affected_elements=1,
    )


def _collect_generation_substitutions(
    rooms: Sequence[RoomData],
) -> Tuple[List[ReferenceSubstitution], List[str]]:
    """Pair heating/cooling generation efficiencies with SIA 380/2 tableaux 5-9.

    The reference project substitutes a standard generator: below 150 kW cooling
    an air chiller (Table 5, full-load EER); heating an air-water heat pump as
    the limit case (Table 8, SCOP). The reference value is selected by the
    project's generation capacity band. Cases the norm routes to a metric the VE
    model does not expose -- water chillers >= 150 kW (Table 7's EER+) and
    air-water heat pumps above 150 kW (Table 8 stops there) -- are reported as
    blockers, never substituted with a non-comparable figure.
    """

    substitutions: List[ReferenceSubstitution] = []
    blockers: List[str] = []
    seen: set = set()
    for room in rooms:
        for system in getattr(room, "hvac_systems", None) or []:
            if not isinstance(system, dict):
                continue
            scope = str(system.get("id") or system.get("name") or "system").strip() or "system"

            # Cooling generation (Table 5 air chiller below the water threshold).
            cooling_capacity = _float_or_none(system.get("cooling_capacity_kw"))
            cooling_eer = _float_or_none(system.get("eer"))
            if (cooling_capacity is not None or cooling_eer is not None) and ("cooling", scope) not in seen:
                seen.add(("cooling", scope))
                if cooling_capacity is None:
                    substitutions.append(_generation_substitution(
                        "cooling_generation_eer", scope, "cooling_generator", "EER",
                        "cooling_air_chiller", None, cooling_eer))
                    blockers.append(
                        "No cooling capacity to select the SIA 380/2 reference "
                        "chiller band for {}".format(scope))
                elif cooling_capacity >= SIA3802_COOLING_AIR_CHILLER_MAX_KW:
                    substitutions.append(_generation_substitution(
                        "cooling_generation_eer", scope, "cooling_generator", "EER",
                        "cooling_air_chiller", None, cooling_eer))
                    blockers.append(
                        "Cooling >= {:.0f} kW for {} references the Table 7 EER+ "
                        "metric (net of post-cooling), which the VE EER does not "
                        "expose; not auto-comparable".format(
                            SIA3802_COOLING_AIR_CHILLER_MAX_KW, scope))
                else:
                    band = _reference_band("cooling_air_chiller", cooling_capacity)
                    reference = band["limit"] if band else None
                    substitutions.append(_generation_substitution(
                        "cooling_generation_eer", scope, "cooling_generator", "EER",
                        "cooling_air_chiller", reference, cooling_eer))
                    if cooling_eer is None:
                        blockers.append(
                            "No project EER could be extracted for cooling "
                            "generator {}".format(scope))

            # Heating generation (Table 8 air-water heat pump, the limit case).
            heating_capacity = _float_or_none(system.get("heating_capacity_kw"))
            heating_scop = _float_or_none(system.get("scop"))
            if (heating_capacity is not None or heating_scop is not None) and ("heating", scope) not in seen:
                seen.add(("heating", scope))
                band = (
                    _reference_band("heating_air_water_hp", heating_capacity)
                    if heating_capacity is not None
                    else None
                )
                reference = band["limit"] if band else None
                substitutions.append(_generation_substitution(
                    "heating_generation_scop", scope, "heating_generator", "SCOP",
                    "heating_air_water_hp", reference, heating_scop))
                if heating_capacity is None:
                    blockers.append(
                        "No heating capacity to select the SIA 380/2 reference "
                        "heat-pump band for {}".format(scope))
                elif reference is None:
                    blockers.append(
                        "Heating > {:.0f} kW for {}: the SIA 380/2 air-water heat "
                        "pump limit table (Table 8) is not tabulated above that "
                        "power".format(150.0, scope))
                elif heating_scop is None:
                    blockers.append(
                        "No project SCOP could be extracted for heating generator "
                        "{}".format(scope))

    return substitutions, blockers


def _collect_reference_directives(
    rooms: Sequence[RoomData],
) -> List[ReferenceSubstitution]:
    """Emit the whole-building emission and capacity reference-run directives.

    SIA 380/2:2022 Table 2 (p33) fixes, for the reference project irrespective
    of the project design, a convective emission system and unlimited heating
    and cooling capacity. These are prescriptive reference-run settings, not
    comparisons, so they are emitted as resolved directives with no project
    value. They complete the reference-run recipe without ever reading as a
    missing-input blocker.
    """

    source = _source(_OPENING_SOURCE_KEY)  # SIA 380/2:2022, tableau 2
    return [
        ReferenceSubstitution(
            parameter="emission_system_type",
            scope="building",
            element_type="emission",
            project_value=None,
            reference_value=0.0,
            unit="radiant_fraction",
            source=source,
            status=REFERENCE_DIRECTIVE,
            affected_elements=len(rooms),
            directive="Convective emission (radiant fraction 0)",
        ),
        ReferenceSubstitution(
            parameter="max_heating_cooling_capacity",
            scope="building",
            element_type="capacity",
            project_value=None,
            reference_value=None,
            unit="-",
            source=source,
            status=REFERENCE_DIRECTIVE,
            affected_elements=len(rooms),
            directive="Unlimited heating and cooling capacity",
        ),
    ]


def _load_sia2024_usage_data() -> Dict[str, Any]:
    """Charge le JSON SIA 2024 une seule fois (lazy + caché).

    Le fichier est lu depuis le dépôt ; aucun import iesve n'est requis.
    En cas d'absence du fichier (CI partiel), retourne un dict vide : les
    codes d'usage ne pourront pas être résolus et les pièces avec une
    catégorie définie seront comptées comme non résolues.
    """

    global _SIA2024_DATA_CACHE
    if _SIA2024_DATA_CACHE is None:
        try:
            with open(_SIA2024_JSON_PATH, encoding="utf-8") as fh:
                _SIA2024_DATA_CACHE = json.load(fh)
        except OSError:
            _SIA2024_DATA_CACHE = {}
    return _SIA2024_DATA_CACHE


def _collect_usage_standard_inputs(
    rooms: Sequence[RoomData],
) -> Tuple[List[ReferenceSubstitution], List[str]]:
    """Émet les entrées SIA 2024 identiques projet et référence (§7.2.5.3).

    Conformément à SIA 380/2:2022 §7.2.5.3, les consignes de température
    (theta_i_mean col30 — exploitation, jamais col28 design), d'humidité,
    les surfaces par personne, l'activité métabolique, la puissance équipements
    et l'éclairement sont définis par l'usage SIA 2024 et s'appliquent de manière
    IDENTIQUE au projet ET au projet de référence. Ces grandeurs ne font donc
    pas l'objet d'une substitution différenciante.

    Statut STANDARD_USAGE_INPUT :
    - project_value = None (identité → pas de comparaison projet/référence)
    - reference_value = valeur du tableau SIA 2024 pour l'usage résolu
    - jamais un bloqueur individuel

    La déduplication est faite par code d'usage : un jeu de 6 substitutions
    est émis par usage distinct présent, pas une par pièce.

    Si des pièces ont une ``sia2024_category`` définie mais non reconnue dans
    le JSON, un bloqueur agrégé unique est émis. Les pièces sans attribut
    ``sia2024_category`` (ou attribut vide) sont ignorées silencieusement :
    elles n'ont pas encore été traitées par le checker.
    """

    data = _load_sia2024_usage_data()
    usages_data = data.get("usages", {})

    # Déduplication : code_usage -> nombre de pièces portant cet usage
    seen_codes: Dict[str, int] = {}
    unresolved_count = 0

    for room in rooms:
        code = (getattr(room, "sia2024_category", "") or "").strip()
        if not code:
            # Attribut absent ou vide → ignoré silencieusement
            continue
        if code not in usages_data:
            # Catégorie définie mais inconnue du JSON SIA 2024
            unresolved_count += 1
            continue
        seen_codes[code] = seen_codes.get(code, 0) + 1

    substitutions: List[ReferenceSubstitution] = []
    blockers: List[str] = []

    for code in sorted(seen_codes):
        params = usages_data[code].get("parameters", {})
        room_count = seen_codes[code]
        for parameter, col, fallback_unit in _SIA2024_USAGE_SYMBOLS:
            col_data = params.get(col, {})
            ref_value = _float_or_none(col_data.get("value"))
            unit = col_data.get("unit") or fallback_unit
            substitutions.append(
                ReferenceSubstitution(
                    parameter=parameter,
                    scope=code,
                    element_type="sia2024_usage",
                    project_value=None,
                    reference_value=ref_value,
                    unit=unit,
                    source=_SIA2024_SOURCE,
                    status=STANDARD_USAGE_INPUT,
                    affected_elements=room_count,
                )
            )

    if unresolved_count:
        blockers.append(
            "SIA 2024 usage not resolved for {} room(s): set sia2024_category "
            "to a valid SIA 2024 code (e.g. \"1.01\") before building the "
            "reference project.".format(unresolved_count)
        )

    return substitutions, blockers


def build_reference_project_specification(
    rooms_data: Optional[Sequence[RoomData]],
    model_analyzer: Any = None,
) -> ReferenceProjectSpecification:
    """Return the reference-project input specification for an analysed model.

    ``READY_FOR_REFERENCE_RUN`` means every construction the model uses has both
    a project value and a normative reference value, so the reference variant
    can be built deterministically. It does not mean the comparison is done: the
    reference demand still requires a VE run, and the accepted project/reference
    result still requires the reviewer gate.
    """

    rooms = list(rooms_data or [])
    if not rooms:
        return ReferenceProjectSpecification(
            status="NOT_CHECKABLE",
            substitutions=(),
            blockers=("No usable VE thermal room was analysed.",),
            notes=(
                "The SIA 380/2 reference-project comparison cannot be prepared "
                "without an extracted model.",
            ),
            implemented_input_families=IMPLEMENTED_REFERENCE_INPUT_FAMILIES,
            missing_input_families=MISSING_REFERENCE_INPUT_FAMILIES,
        )

    surface_items, surface_blockers = _collect_surface_substitutions(rooms, model_analyzer)
    opening_items, opening_blockers = _collect_opening_substitutions(rooms)
    infiltration_items, infiltration_blockers = _collect_infiltration_substitution(rooms)
    generation_items, generation_blockers = _collect_generation_substitutions(rooms)
    directive_items = _collect_reference_directives(rooms)
    # SIA 380/2:2022 §7.2.5.3 : consignes et gains SIA 2024 identiques projet/référence.
    usage_items, usage_blockers = _collect_usage_standard_inputs(rooms)
    substitutions = tuple(
        surface_items + opening_items + infiltration_items + generation_items
        + directive_items + usage_items
    )
    blockers = tuple(
        surface_blockers + opening_blockers + infiltration_blockers
        + generation_blockers + usage_blockers
    )

    missing_reference = [
        item.parameter
        for item in substitutions
        if item.status == SUBSTITUTABLE and item.reference_value is None
    ]
    blockers = blockers + tuple(
        "No encoded SIA reference value for {}".format(parameter)
        for parameter in sorted(set(missing_reference))
    )

    notes = [
        "Reference values are read from the encoded SIA 380/2 tables with their "
        "locators; none is computed or interpolated here.",
        "This specification prepares the reference run. It is not a compliance "
        "conclusion: the reference demand requires a VE/ApacheSim run, and the "
        "project/reference comparison still requires reviewer acceptance.",
        "Opaque-envelope constructions, window U-value/frame fraction, glazing "
        "solar/visible properties (g_perp, tau_v), whole-building infiltration, "
        "heating/cooling generation efficiencies (tableaux 5-9), the "
        "convective-emission / unlimited-capacity directives, and the SIA 2024 "
        "usage standard inputs (theta_i_mean col30, phi_i, A_p, M, p_Be, E_vm — "
        "identical project/reference per §7.2.5.3) are currently automated. "
        "Every other SIA 380/2 Table 2 family remains an explicit "
        "implementation blocker.",
    ]
    if not substitutions:
        status = "NOT_CHECKABLE"
        blockers = blockers + (
            "No external surface or opening was available for substitution.",
        )
    elif blockers:
        status = "BLOCKED_INCOMPLETE_INPUTS"
    else:
        status = "PARTIAL_REFERENCE_INPUT_SPECIFICATION"
    return ReferenceProjectSpecification(
        status=status,
        substitutions=substitutions,
        blockers=blockers,
        notes=tuple(notes),
        implemented_input_families=IMPLEMENTED_REFERENCE_INPUT_FAMILIES,
        missing_input_families=MISSING_REFERENCE_INPUT_FAMILIES,
    )
