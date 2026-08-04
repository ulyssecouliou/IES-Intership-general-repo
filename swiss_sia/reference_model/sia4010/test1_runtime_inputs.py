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
