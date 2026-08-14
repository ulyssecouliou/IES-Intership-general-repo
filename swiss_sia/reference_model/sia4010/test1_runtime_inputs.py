"""Controlled mappings for ISO 52016-1 Test 1 room runtime inputs.

The ISO test prescribes a combined air-and-furniture capacity. IESVE exposes
furniture capacity as a multiple of room-air capacity. The calculation here is
pure and auditable; VE mutation remains in the guarded VEScripts launcher.
"""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping

from ..exceptions import ConfigurationError


ISO_AREAL_CAPACITY_J_M2K = 10000.0
ISO_HEATING_CAPACITY_W = 1000000.0
ISO_COOLING_CAPACITY_W = 1000000.0
ISO_HEATING_CONVECTIVE_FRACTION = 1.0
ISO_COOLING_CONVECTIVE_FRACTION = 1.0

# ApacheSim's public documentation defines the furniture factor relative to
# air capacity but the exact solver cp constant is not exposed by VEScripts.
# This is an engine-binding assumption, not an ISO or SIA regulatory value.
PROVISIONAL_REFERENCE_AIR_DENSITY_KG_M3 = 1.2
PROVISIONAL_DENSITY_SOURCE = (
    "PROVISIONAL IES engine-binding assumption; matches the ref_air_density "
    "shown in the installed VE 2025 VELocate API example"
)
PROVISIONAL_AIR_SPECIFIC_HEAT_J_KGK = 1005.0
PROVISIONAL_CP_SOURCE = (
    "PROVISIONAL IES engine-binding assumption; written confirmation of the "
    "ApacheSim room-air specific-heat constant is still required"
)


@dataclass(frozen=True)
class Test1RuntimeInputMapping:
    """Auditable conversion from the ISO capacity to the VE room factor."""

    floor_area_m2: float
    room_volume_m3: float
    reference_air_density_kg_m3: float
    air_specific_heat_j_kgk: float
    target_areal_capacity_j_m2k: float
    target_total_capacity_j_k: float
    ve_air_capacity_j_k: float
    furniture_mass_factor: float
    air_specific_heat_source: str
    compliance_claim_allowed: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe record."""

        return asdict(self)


def _positive_finite(value: Any, label: str) -> float:
    """Return a positive finite float or fail closed."""

    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError("{} must be numeric".format(label)) from exc
    if not math.isfinite(result) or result <= 0.0:
        raise ConfigurationError("{} must be positive and finite".format(label))
    return result


def calculate_furniture_mass_factor(
    *,
    floor_area_m2: float,
    room_volume_m3: float,
    reference_air_density_kg_m3: float,
    air_specific_heat_j_kgk: float = PROVISIONAL_AIR_SPECIFIC_HEAT_J_KGK,
    target_areal_capacity_j_m2k: float = ISO_AREAL_CAPACITY_J_M2K,
) -> Test1RuntimeInputMapping:
    """Calculate the VE factor for the ISO combined internal capacity."""

    area = _positive_finite(floor_area_m2, "floor_area_m2")
    volume = _positive_finite(room_volume_m3, "room_volume_m3")
    density = _positive_finite(
        reference_air_density_kg_m3, "reference_air_density_kg_m3"
    )
    cp_air = _positive_finite(
        air_specific_heat_j_kgk, "air_specific_heat_j_kgk"
    )
    target_areal = _positive_finite(
        target_areal_capacity_j_m2k,
        "target_areal_capacity_j_m2k",
    )
    target_total = target_areal * area
    air_capacity = density * cp_air * volume
    factor = target_total / air_capacity - 1.0
    if factor < 0.0:
        raise ConfigurationError(
            "Calculated furniture_mass_factor is negative; ISO target and "
            "VE air properties are inconsistent"
        )
    return Test1RuntimeInputMapping(
        floor_area_m2=area,
        room_volume_m3=volume,
        reference_air_density_kg_m3=density,
        air_specific_heat_j_kgk=cp_air,
        target_areal_capacity_j_m2k=target_areal,
        target_total_capacity_j_k=target_total,
        ve_air_capacity_j_k=air_capacity,
        furniture_mass_factor=factor,
        air_specific_heat_source=PROVISIONAL_CP_SOURCE,
    )


def build_furniture_condition_payload(
    before_conditions: Mapping[str, Any], furniture_mass_factor: float
) -> Dict[str, Any]:
    """Return the minimal writable VE room-condition payload.

    Getter dictionaries include read-only keys such as ``dhw_unit`` that the
    Boost.Python setter rejects. Never echo an entire getter dictionary back.
    """

    factor = _positive_finite(furniture_mass_factor, "furniture_mass_factor")
    payload = {"furniture_mass_factor": factor}
    if "furniture_mass_factor_from_template" in before_conditions:
        payload["furniture_mass_factor_from_template"] = False
    return payload


def validate_capacity_semantics(
    system_data: Mapping[str, Any], *, conditioned: bool
) -> Dict[str, Any]:
    """Validate that conditioned Test 1 rooms use VE unlimited capacities."""

    result = {
        "conditioned": bool(conditioned),
        "iso_heating_capacity_w": ISO_HEATING_CAPACITY_W,
        "iso_cooling_capacity_w": ISO_COOLING_CAPACITY_W,
        "ve_heating_capacity_unlimited": bool(
            system_data.get("heating_capacity_unlimited")
        ),
        "ve_cooling_capacity_unlimited": bool(
            system_data.get("cooling_capacity_unlimited")
        ),
        "mapping": (
            "VE unlimited capacity is functionally non-binding and therefore "
            "represents the ISO statement that 1000 kW is effectively infinite"
        ),
    }
    result["verified"] = (
        not conditioned
        or (
            result["ve_heating_capacity_unlimited"]
            and result["ve_cooling_capacity_unlimited"]
        )
    )
    if not result["verified"]:
        raise ConfigurationError(
            "Conditioned Test 1 room does not expose unlimited heating and "
            "cooling capacity; no capacity-unit mutation was attempted"
        )
    return result


def is_conditioned_state(value: Any) -> bool:
    """Interpret VE's conditioned enum without relying on enum truthiness.

    Boost.Python enumeration members are integer-like.  In particular,
    ``conditioned_flag.no_free_floating`` may be truthy even though it means
    that the room is unconditioned.  Normalise the documented symbolic value
    instead and fail closed for an unknown state.
    """

    if type(value) is bool:
        return value
    token = str(value).strip().lower().split(".")[-1]
    if token in {"yes", "true", "conditioned_yes"}:
        return True
    if token in {
        "no_free_floating",
        "no_tempered",
        "not_applicable",
        "false",
        "conditioned_no_free_floating",
        "conditioned_no_tempered",
        "conditioned_not_applicable",
    }:
        return False
    raise ConfigurationError(
        "Unrecognised VE conditioned state: {!r}".format(value)
    )


def is_off_profile(value: Any) -> bool:
    """Return whether a VE availability profile is the built-in OFF profile."""

    return str(value or "").strip().upper() == "OFF"


def build_ideal_load_system_payload(
    before_system: Mapping[str, Any],
) -> Dict[str, Any]:
    """Return the minimal VE payload for fully convective ideal loads.

    VE stores the complementary radiant fraction. ISO 52016-1 Test 1 specifies
    ``f_H;c = f_C;c = 1.00``; both VE radiant fractions must therefore be zero.
    Template-inheritance flags are disabled only when this VE release exposes
    them, so the room-level values remain explicit and auditable.
    """

    payload: Dict[str, Any] = {
        "heating_plant_radiant_fraction": 1.0
        - ISO_HEATING_CONVECTIVE_FRACTION,
        "cooling_plant_radiant_fraction": 1.0
        - ISO_COOLING_CONVECTIVE_FRACTION,
    }
    for key in tuple(payload):
        flag = "{}_from_template".format(key)
        if flag in before_system:
            payload[flag] = False
    return payload


def build_zero_mechanical_ventilation_payload(
    before_system: Mapping[str, Any],
) -> Dict[str, Any]:
    """Return the minimal room-system payload for ISO Test 1 ventilation.

    Clause 7.2.2.14 prescribes infiltration only and explicitly states that
    there is no mechanical ventilation.  The generic reference template uses
    a non-zero office outdoor-air default, so every Test 1 room must override
    the Apache system minimum flow to zero.  At zero flow the getter's unit
    selector is mathematically irrelevant and is deliberately not echoed back
    through the version-sensitive setter.
    """

    payload: Dict[str, Any] = {"system_air_minimum_flowrate": 0.0}
    inheritance = "system_air_minimum_flowrate_from_template"
    if inheritance in before_system:
        payload[inheritance] = False
    return payload


def validate_zero_mechanical_ventilation_semantics(
    system_data: Mapping[str, Any],
) -> Dict[str, Any]:
    """Prove that the live VE room has no Apache system outdoor-air flow."""

    try:
        flow = float(system_data.get("system_air_minimum_flowrate"))
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            "Test 1 Apache system minimum outdoor-air flow is unavailable"
        ) from exc
    verified = math.isclose(flow, 0.0, rel_tol=0.0, abs_tol=1.0e-9)
    receipt = {
        "iso_mechanical_ventilation": "none",
        "ve_system_air_minimum_flowrate": flow,
        "ve_system_air_minimum_flowrate_units": system_data.get(
            "system_air_minimum_flowrate_units",
            system_data.get("system_air_minimum_flowrate_unit"),
        ),
        "verified": verified,
    }
    if not verified:
        raise ConfigurationError(
            "Test 1 room still has non-zero Apache system outdoor-air flow: {}"
            .format(flow)
        )
    return receipt


def _selected_air_exchange_flow(record: Mapping[str, Any]) -> Any:
    """Resolve the effective flow of one VE air-exchange read-back record.

    VE 2025 returns a scalar ``max_flow`` on template ``AirExchange`` records
    but a ``max_flows`` dictionary indexed by the selected unit on room-level
    ``RoomAirExchange`` records (``references/iesve/IESVE_API_REFERENCE.md``
    section 11).  Both shapes are resolved here so the caller never has to
    guess which VE object it received.
    """

    if "max_flow" in record:
        return record["max_flow"]
    values = record.get("max_flows")
    if not isinstance(values, Mapping):
        return None
    try:
        index = int(record.get("units_val", 0))
    except (TypeError, ValueError):
        index = 0
    return values.get(index, values.get(str(index)))


def validate_prescribed_infiltration_preserved(
    air_exchange_records: Any,
) -> Dict[str, Any]:
    """Prove the ISO Test 1 infiltration survived the ventilation override.

    Clause 7.2.2.14 prescribes infiltration only.  Forcing the Apache system
    minimum outdoor-air flow to zero must never also remove or zero the
    prescribed infiltration air exchange, otherwise the room would simulate
    with no air change at all and the APS would silently change meaning.

    The check proves two things and invents nothing:

    * exactly one ``type_val == 0`` (Infiltration) record exists and its
      effective flow is strictly positive and finite;
    * every OTHER air exchange on the room carries exactly zero flow.  Zeroing
      the Apache system minimum outdoor-air flow is pointless if a second
      ``RoomAirExchange`` still moves air, so the guarantee is only complete
      when the whole set is inspected.  The asset manifest deliberately creates
      an ``outdoor_air`` exchange at 0.0, so a second record is expected — a
      second record with flow is not.

    No numeric target is asserted for the infiltration itself: the prescribed
    magnitude belongs to the source-traced asset manifest, not to this runtime
    guard.  Every observed record is returned verbatim for the audit trail so a
    reviewer can confront it with the manifest.
    """

    records = []
    for entry in air_exchange_records or []:
        if isinstance(entry, Mapping):
            records.append(dict(entry))
            continue
        getter = getattr(entry, "get", None)
        if not callable(getter):
            raise ConfigurationError(
                "Test 1 air-exchange read-back entry exposes no get()"
            )
        data = getter()
        if not isinstance(data, Mapping):
            raise ConfigurationError(
                "Test 1 air-exchange read-back did not return a mapping"
            )
        records.append(dict(data))

    infiltration = [
        record for record in records if _is_infiltration_record(record)
    ]
    if len(infiltration) != 1:
        raise ConfigurationError(
            "Test 1 room must expose exactly one prescribed infiltration air "
            "exchange; found {}".format(len(infiltration))
        )
    record = infiltration[0]
    flow = _selected_air_exchange_flow(record)
    try:
        flow_value = float(flow)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            "Test 1 prescribed infiltration flow is unavailable"
        ) from exc
    if not math.isfinite(flow_value) or flow_value <= 0.0:
        raise ConfigurationError(
            "Test 1 prescribed infiltration is no longer active: flow={}".format(
                flow_value
            )
        )

    # Every other exchange must be exactly zero, otherwise air still moves
    # through a path the Apache system override does not control.
    others = []
    for other in records:
        if _is_infiltration_record(other):
            continue
        other_flow = _selected_air_exchange_flow(other)
        try:
            other_value = float(other_flow)
        except (TypeError, ValueError) as exc:
            raise ConfigurationError(
                "Test 1 non-infiltration air exchange {!r} has an unreadable "
                "flow".format(str(other.get("name", "")))
            ) from exc
        if not math.isfinite(other_value) or not math.isclose(
            other_value, 0.0, rel_tol=0.0, abs_tol=1.0e-9
        ):
            raise ConfigurationError(
                "Test 1 prescribes infiltration only, but air exchange {!r} "
                "(type_val={}) carries flow {}".format(
                    str(other.get("name", "")),
                    other.get("type_val"),
                    other_value,
                )
            )
        others.append(
            {
                "name": str(other.get("name", "")),
                "type_val": other.get("type_val"),
                "units_val": other.get("units_val"),
                "max_flow": other_value,
            }
        )

    return {
        "iso_infiltration": "prescribed, retained separately from mechanical "
        "ventilation",
        "ve_infiltration_name": str(record.get("name", "")),
        "ve_infiltration_max_flow": flow_value,
        "ve_infiltration_units_val": record.get("units_val"),
        "ve_infiltration_max_flow_from_template": record.get(
            "max_flow_from_template"
        ),
        "ve_air_exchange_count": len(records),
        "ve_other_air_exchanges_all_zero": True,
        "ve_other_air_exchanges": others,
        "verified": True,
    }


def _is_infiltration_record(record: Mapping[str, Any]) -> bool:
    """Return whether one air-exchange record is VE's Infiltration type.

    ``type_val == 0`` is Infiltration in VE 2025
    (``references/iesve/IESVE_API_REFERENCE.md`` section 11).  The string form
    is accepted as a documented fallback for builds that expose only
    ``type_str``.
    """

    if "type_val" in record:
        try:
            return int(record["type_val"]) == 0
        except (TypeError, ValueError):
            return False
    type_text = str(record.get("type_str", "")).strip().lower()
    return type_text.replace(" ", "").replace("_", "") == "infiltration"


def validate_ideal_load_emission_semantics(
    system_data: Mapping[str, Any],
) -> Dict[str, Any]:
    """Verify the ISO fully convective heating/cooling mapping."""

    try:
        heating_radiant = float(system_data.get("heating_plant_radiant_fraction"))
        cooling_radiant = float(system_data.get("cooling_plant_radiant_fraction"))
    except (TypeError, ValueError) as exc:
        raise ConfigurationError(
            "Test 1 ideal heating/cooling radiant fractions are unavailable"
        ) from exc
    verified = math.isclose(heating_radiant, 0.0, abs_tol=1.0e-9) and math.isclose(
        cooling_radiant, 0.0, abs_tol=1.0e-9
    )
    result = {
        "iso_heating_convective_fraction": ISO_HEATING_CONVECTIVE_FRACTION,
        "iso_cooling_convective_fraction": ISO_COOLING_CONVECTIVE_FRACTION,
        "ve_heating_radiant_fraction": heating_radiant,
        "ve_cooling_radiant_fraction": cooling_radiant,
        "verified": verified,
    }
    if not verified:
        raise ConfigurationError(
            "Test 1 ideal heating/cooling is not fully convective in VE"
        )
    return result
