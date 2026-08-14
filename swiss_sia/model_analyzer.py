"""Normalize VE model data into SIA-ready analytical objects.

The analyzer converts raw IESVE API objects into stable room, surface, opening,
air-exchange and HVAC structures used by the SIA 380/2 and SIA 4010 checkers.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from .data_extractor import VEDataExtractor

logger = logging.getLogger(__name__)

@dataclass
class SurfaceData:
    """Normalized data for one VE surface such as a wall, roof or floor."""

    id: str
    name: str = ""  # Surface name when exposed by VE.
    area: float = 0.0
    net_area: float = 0.0
    u_value: Optional[float] = None
    orientation: Optional[str] = None
    tilt: Optional[float] = None
    materials: List[str] = field(default_factory=list)
    is_external: bool = False
    surface_type: Optional[str] = None  # Normalized type such as wall, roof or floor.
    construction_ids: List[str] = field(default_factory=list)
    adjacency_room_ids: List[str] = field(default_factory=list)

@dataclass
class OpeningData:
    """Normalized opening data extracted from VE."""
    id: str
    name: str = ""  # Opening name when exposed by VE.
    area: float = 0.0
    u_value: Optional[float] = None
    solar_factor: Optional[float] = None
    solar_factor_source: Optional[str] = None
    cdb_g_value: Optional[float] = None
    g_value_bs_en_410: Optional[float] = None
    g_value_building_regulations: Optional[float] = None
    g_value_bfrc: Optional[float] = None
    g_values: Dict[str, Any] = field(default_factory=dict)
    visible_transmittance: Optional[float] = None
    frame_fraction: Optional[float] = None
    shading_type: Optional[str] = None
    shading_control: Optional[str] = None
    shading_properties: Dict[str, Any] = field(default_factory=dict)
    g_total: Optional[float] = None
    g_total_source: Optional[str] = None
    orientation: Optional[str] = None
    opening_type: Optional[str] = None  # Normalized type such as window or door.
    is_external: bool = False
    construction_id: str = ""
    macroflo_id: str = ""


def has_active_solar_protection(opening: Any) -> bool:
    """Return whether an opening has an explicitly active solar-protection device."""
    properties = getattr(opening, "shading_properties", {}) or {}
    active_keys = (
        "external_shade_active",
        "internal_shade_active",
        "local_shade_active",
    )
    active_values = [properties[key] for key in active_keys if key in properties]
    if active_values:
        return any(_is_enabled_marker(value) for value in active_values)

    shading_type = str(getattr(opening, "shading_type", "") or "").strip().lower()
    disabled_types = {
        "",
        "0",
        "false",
        "no",
        "none",
        "off",
        "disabled",
        "none declared in cdb",
    }
    return shading_type not in disabled_types


def _is_enabled_marker(value: Any) -> bool:
    """Interpret VE boolean-like activation fields without treating zero as active."""
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value != 0
    return str(value or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
        "active",
        "enabled",
    }

@dataclass
class RoomData:
    """Normalized data for one thermal room or zone."""

    id: str
    name: str = ""  # Room name when exposed by VE.
    volume: float = 0.0
    area: float = 0.0
    surfaces: List[SurfaceData] = field(default_factory=list)
    openings: List[OpeningData] = field(default_factory=list)
    internal_gains: Dict[str, Optional[float]] = field(default_factory=dict)  # Lighting, people and equipment values.
    internal_gain_details: List[Dict[str, Any]] = field(default_factory=list)
    internal_gains_wh_m2_day: Optional[float] = None
    internal_gains_daily_method: str = ""
    occupancy_density_m2_per_person: Optional[float] = None
    thermal_template_id: str = ""
    daylight_dimming_profile: str = ""
    window_operable: Optional[bool] = None
    window_ventilation_support: Optional[str] = None
    ventilation_rate: Optional[float] = None
    ventilation_m3_h_m2: Optional[float] = None
    ventilation_facade_m3_h_m2: Optional[float] = None
    infiltration_rate: Optional[float] = None
    infiltration_unit: Optional[str] = None
    infiltration_m3_h_m2: Optional[float] = None
    hvac_systems: List[Dict[str, Any]] = field(default_factory=list)
    room_conditions: Dict[str, Any] = field(default_factory=dict)
    hvac_zone: Dict[str, Any] = field(default_factory=dict)
    ventilation_installation_type: Optional[str] = None
    ventilation_control: Optional[str] = None
    ventilation_control_level: Optional[int] = None
    fan_control: Optional[str] = None
    heat_recovery_type: Optional[str] = None
    dynamic_results: Dict[str, Any] = field(default_factory=dict)

class ModelAnalyzer:
    """Analyze the VE model and expose normalized indicators for SIA checks."""

    def __init__(self, data_extractor: "VEDataExtractor"):
        """Initialize the analyzer with a VE data extractor."""
        self.data_extractor = data_extractor
        self._rooms_data: Dict[str, RoomData] = {}

    def analyze_all_rooms(self) -> List[RoomData]:
        """Analyze all relevant VE rooms and return normalized room data."""
        rooms_data = []
        bodies = self.data_extractor.get_bodies()
        for body in bodies:
            room_data = self.analyze_room(body)
            if room_data:
                rooms_data.append(room_data)
                self._rooms_data[self.data_extractor.get_object_id(body)] = room_data
        self._annotate_hvac_zoning_and_controls(rooms_data)
        return rooms_data

    def analyze_room(self, body: Any) -> Optional[RoomData]:
        """Analyze one VE body and return normalized room data when usable."""
        try:
            room_data_obj = self.data_extractor.get_room_data(body)
            raw_surfaces = self.data_extractor.get_surfaces(body) or []
            surfaces = self._analyze_surfaces(raw_surfaces)
            openings = self._analyze_openings(raw_surfaces)
            body_areas = self._get_body_areas(body)
            room_area = float(body_areas.get("int_floor_area", 0.0) or 0.0) + float(body_areas.get("ext_floor_area", 0.0) or 0.0)
            room_general = self.data_extractor.get_room_general(room_data_obj) if room_data_obj else {}
            gain_summary = self._analyze_internal_gains(room_data_obj, room_area) if room_data_obj else {}
            internal_gains = {
                key: gain_summary.get(key)
                for key in ("lighting", "people", "equipment")
            }
            occupancy_density = self._to_float_or_none(
                gain_summary.get("occupancy_density_m2_per_person")
            )
            air_exchange_summary = (
                self._analyze_air_exchanges(room_data_obj, occupancy_density)
                if room_data_obj
                else {}
            )
            ventilation_rate = air_exchange_summary.get("ventilation_rate")
            ventilation_m3_h_m2 = air_exchange_summary.get("ventilation_m3_h_m2")
            infiltration_rate = air_exchange_summary.get("infiltration_rate")
            infiltration_unit = air_exchange_summary.get("infiltration_unit")
            infiltration_m3_h_m2 = air_exchange_summary.get("infiltration_m3_h_m2")
            room_conditions = self._analyze_room_conditions(room_data_obj) if room_data_obj else {}
            hvac_systems = self._analyze_hvac_systems(room_data_obj, room_conditions) if room_data_obj else []
            window_summary = self._analyze_window_ventilation(openings)

            return RoomData(
                id=self.data_extractor.get_object_id(body),
                name=self._get_body_name(body),
                volume=float(body_areas.get("volume", 0.0) or 0.0),
                area=room_area,
                surfaces=surfaces,
                openings=openings,
                internal_gains=internal_gains,
                internal_gain_details=list(gain_summary.get("details", []) or []),
                internal_gains_wh_m2_day=self._to_float_or_none(gain_summary.get("daily_wh_m2")),
                internal_gains_daily_method=str(gain_summary.get("daily_method") or ""),
                occupancy_density_m2_per_person=occupancy_density,
                thermal_template_id=str(
                    room_general.get("thermal_template")
                    or room_general.get("template")
                    or ""
                ),
                daylight_dimming_profile=str(gain_summary.get("daylight_dimming_profile") or ""),
                window_operable=window_summary.get("window_operable"),
                window_ventilation_support=window_summary.get("window_ventilation_support"),
                ventilation_rate=ventilation_rate,
                ventilation_m3_h_m2=ventilation_m3_h_m2,
                ventilation_facade_m3_h_m2=air_exchange_summary.get("ventilation_facade_m3_h_m2"),
                infiltration_rate=infiltration_rate,
                infiltration_unit=infiltration_unit,
                infiltration_m3_h_m2=infiltration_m3_h_m2,
                hvac_systems=hvac_systems,
                room_conditions=room_conditions,
                fan_control=self._first_hvac_value(hvac_systems, "fan_control"),
                heat_recovery_type=(
                    self._normalize_identifier(room_conditions.get("heat_recovery"))
                    or self._first_hvac_value(hvac_systems, "heat_recovery_type")
                ),
            )
        except Exception as e:
            logger.debug("Room ignored during analysis: %s", e)
            return None

    def _analyze_surfaces(self, surfaces: List[Any]) -> List[SurfaceData]:
        """Analyze room surfaces through documented ``VESurface`` methods."""
        surfaces_data = []
        for surface in surfaces:
            try:
                props = self.data_extractor.get_surface_properties(surface) or {}
                areas = self.data_extractor.get_surface_areas(surface) or {}
                surface_id = self.data_extractor.get_object_id(surface)
                external_gross = self._to_float(areas.get("external_gross"))
                total_gross = self._to_float(areas.get("total_gross"))
                gross_area = external_gross if external_gross > 0 else total_gross
                if gross_area <= 0:
                    gross_area = self._to_float(areas.get("area")) or self._to_float(props.get("area"))

                # Select net area by whether external_net itself is present (mirrors
                # data_extractor); keying on external_gross could zero a real
                # external surface when external_net is missing/None.
                external_net = self._to_float_or_none(areas.get("external_net"))
                total_net = self._to_float(areas.get("total_net"))
                net_area = external_net if external_net is not None else total_net
                if net_area <= 0 and gross_area > 0 and self._to_float(areas.get("total_gross_openings")) <= 1e-6:
                    net_area = gross_area
                u_value = props.get("U-value")
                orientation = props.get("orientation")
                tilt = self._to_float_or_none(props.get("tilt"))
                materials = list(props.get("materials", []) or [])
                surface_type = str(props.get("type", "") or "").lower()
                construction_ids = [str(item) for item in props.get("construction_ids", []) or []]

                is_external = self._is_external_surface(surface_type) or float(areas.get("external_gross", 0.0) or 0.0) > 0
                adjacency_room_ids: List[str] = []
                try:
                    adjacencies = self.data_extractor.get_adjacencies(surface) or []
                    adjacency_room_ids = [
                        body_id
                        for body_id in (
                            self._get_adjacency_body_id(adjacency)
                            for adjacency in adjacencies
                        )
                        if body_id
                    ]
                except Exception:
                    if not is_external:
                        is_external = False

                surfaces_data.append(SurfaceData(
                    id=surface_id,
                    name=self._get_surface_name(surface),
                    area=gross_area,
                    net_area=net_area,
                    u_value=u_value,
                    orientation=orientation,
                    tilt=tilt,
                    materials=materials,
                    is_external=is_external,
                    surface_type=surface_type,
                    construction_ids=construction_ids,
                    adjacency_room_ids=adjacency_room_ids,
                ))
            except Exception:
                continue
        return surfaces_data

    def _analyze_openings(self, surfaces: List[Any]) -> List[OpeningData]:
        """Analyze room openings through ``VESurface.get_openings()``."""
        openings_data = []
        for surface in surfaces:
            try:
                surface_props = self.data_extractor.get_surface_properties(surface) or {}
                surface_areas = self.data_extractor.get_surface_areas(surface) or {}
                is_external = self._is_external_surface(surface_props.get("type")) or float(surface_areas.get("external_gross", 0.0) or 0.0) > 0
                surface_orientation = surface_props.get("orientation")
                openings = self.data_extractor.get_openings(surface) or []
            except Exception:
                is_external = False
                surface_orientation = None
                openings = []

            for opening in openings:
                try:
                    props = self.data_extractor.get_opening_properties(opening) or {}
                    opening_id = self.data_extractor.get_object_id(opening)
                    area = float(props.get("area", 0.0) or 0.0)
                    u_value = props.get("U-value")
                    solar_factor = props.get("solar_factor")
                    g_values = props.get("g_values") if isinstance(props.get("g_values"), dict) else {}
                    shading_properties = props.get("shading_properties") if isinstance(props.get("shading_properties"), dict) else {}
                    visible_transmittance = self._to_float_or_none(props.get("visible_transmittance"))
                    frame_fraction = self._to_float_or_none(props.get("frame_fraction"))
                    orientation = props.get("orientation") or surface_orientation
                    opening_type = self._normalize_opening_type(props.get("type"))
                    construction_id = str(props.get("construction_id", "") or "")

                    openings_data.append(OpeningData(
                        id=opening_id,
                        name=self._get_opening_name(opening),
                        area=area,
                        u_value=u_value,
                        solar_factor=solar_factor,
                        solar_factor_source=str(props.get("solar_factor_source") or "") or None,
                        cdb_g_value=self._to_float_or_none(props.get("cdb_g_value")),
                        g_value_bs_en_410=self._to_float_or_none(props.get("g_value_bs_en_410")),
                        g_value_building_regulations=self._to_float_or_none(props.get("g_value_building_regulations")),
                        g_value_bfrc=self._to_float_or_none(props.get("g_value_bfrc")),
                        g_values=dict(g_values),
                        visible_transmittance=visible_transmittance,
                        frame_fraction=frame_fraction,
                        shading_type=str(props.get("shading_type") or "") or None,
                        shading_control=str(props.get("shading_control") or "") or None,
                        shading_properties=dict(shading_properties),
                        g_total=self._to_float_or_none(props.get("g_total")),
                        g_total_source=str(props.get("g_total_source") or "") or None,
                        orientation=orientation,
                        opening_type=opening_type,
                        is_external=is_external,
                        construction_id=construction_id,
                        macroflo_id=str(props.get("macroflo_id") or ""),
                    ))
                except Exception:
                    continue
        return openings_data

    def _analyze_internal_gains(self, room_data: Any, room_area: float) -> Dict[str, Any]:
        """Extract gain densities and integrate a representative occupied day."""
        gains: Dict[str, Any] = {
            "lighting": None,
            "people": None,
            "equipment": None,
            "details": [],
            "daily_wh_m2": None,
            "daily_method": "",
            "daylight_dimming_profile": "",
            "occupancy_density_m2_per_person": None,
        }
        if not room_data:
            return gains

        internal_gains = self.data_extractor.get_internal_gains(room_data)
        daily_components: List[float] = []
        daily_complete = True
        for gain in internal_gains:
            try:
                gain_data = self._safe_get_data(gain)
                gain_type = str(gain_data.get("type_str", "")).lower()
                units_val = gain_data.get("units_val")
                density = self._gain_density_w_m2(gain_data, room_area)
                variation_profile = str(gain_data.get("variation_profile") or "")
                profile_hours = (
                    self.data_extractor.get_profile_daily_equivalent_hours(variation_profile)
                    if variation_profile
                    and hasattr(self.data_extractor, "get_profile_daily_equivalent_hours")
                    else None
                )
                diversity = self._to_float_or_none(gain_data.get("diversity_factor"))
                diversity = diversity if diversity is not None else 1.0
                category = ""
                if "lighting" in gain_type or "fluorescent" in gain_type or "tungsten" in gain_type:
                    category = "lighting"
                    gains["daylight_dimming_profile"] = str(
                        gain_data.get("dimming_profile")
                        or gains["daylight_dimming_profile"]
                        or ""
                    )
                elif "people" in gain_type:
                    category = "people"
                    occupancies = gain_data.get("occupancies")
                    density_m2_per_person = None
                    if isinstance(occupancies, dict):
                        density_m2_per_person = self._to_float_or_none(
                            occupancies.get(0, occupancies.get("0"))
                        )
                    if density_m2_per_person is None:
                        density_m2_per_person = self._to_float_or_none(
                            gain_data.get("occupancy_density")
                        )
                    if density_m2_per_person is not None and density_m2_per_person > 0:
                        gains["occupancy_density_m2_per_person"] = density_m2_per_person
                elif any(token in gain_type for token in ("machinery", "misc", "cooking", "computer", "equipment")):
                    category = "equipment"
                if not category:
                    continue
                if density is not None:
                    previous = self._to_float_or_none(gains.get(category)) or 0.0
                    gains[category] = previous + density
                if density is None or profile_hours is None:
                    daily_complete = False
                else:
                    daily_components.append(density * diversity * profile_hours)
                gains["details"].append({
                    "name": str(gain_data.get("name") or ""),
                    "category": category,
                    "type": str(gain_data.get("type_str") or ""),
                    "units_val": units_val,
                    "density_w_m2": density,
                    "variation_profile": variation_profile,
                    "profile_full_load_hours": profile_hours,
                    "diversity_factor": diversity,
                    "dimming_profile": str(gain_data.get("dimming_profile") or ""),
                })
            except Exception as e:
                logger.error("Error while analyzing internal gains: %s", e)
                daily_complete = False
        if gains["details"] and daily_complete and len(daily_components) == len(gains["details"]):
            gains["daily_wh_m2"] = sum(daily_components)
            gains["daily_method"] = (
                "Sum of VE gain densities multiplied by diversity and the maximum representative "
                "daily full-load hours resolved from modulating VE profiles"
            )
        elif gains["details"]:
            gains["daily_method"] = "NOT_CHECKABLE: at least one gain density or VE daily profile could not be resolved"
        return gains

    @classmethod
    def _gain_density_w_m2(cls, gain_data: Dict[str, Any], room_area: float) -> Optional[float]:
        """Return a gain density only when the VE unit conversion is defensible."""
        units_val = gain_data.get("units_val")
        value_table = gain_data.get("max_power_consumptions")
        if value_table in (None, {}):
            value_table = gain_data.get("max_sensible_gains")
        if isinstance(value_table, dict):
            if 0 in value_table or "0" in value_table:
                return cls._to_float_or_none(value_table.get(0, value_table.get("0")))
            active = value_table.get(units_val, value_table.get(str(units_val)))
        else:
            active = value_table
        value = cls._to_float_or_none(active)
        if value is None:
            return None
        units_text = str(
            gain_data.get("units_str")
            or (gain_data.get("units_strs") or {}).get(units_val, "")
        ).lower()
        if "w/m" in units_text or units_val == 0:
            return value
        if ("w" in units_text or units_val == 1) and room_area > 0:
            return value / room_area
        return None

    def _analyze_ventilation(self, room_data: Any) -> Optional[float]:
        """Extract a basic room ventilation flow indicator when available."""
        if not room_data:
            return None

        air_exchanges = self.data_extractor.get_air_exchanges(room_data)
        for exchange in air_exchanges:
            try:
                exchange_data = self._safe_get_data(exchange)
                if exchange_data.get("type_val") == 2 and exchange_data.get("units_val") == 0:
                    return self._extract_first_numeric(exchange_data.get("max_flows"))
            except Exception as e:
                logger.error("Error while analyzing ventilation: %s", e)
        return None

    def _analyze_air_exchanges(
        self,
        room_data: Any,
        occupancy_density_m2_per_person: Optional[float] = None,
    ) -> Dict[str, Optional[float]]:
        """Analyze ventilation and infiltration from VE room air exchanges."""
        summary: Dict[str, Any] = {
            "ventilation_rate": None,
            "ventilation_m3_h_m2": None,
            "ventilation_facade_m3_h_m2": None,
            "infiltration_rate": None,
            "infiltration_unit": None,
            "infiltration_m3_h_m2": None,
        }
        if not room_data:
            return summary

        air_exchanges = self.data_extractor.get_air_exchanges(room_data)
        for exchange in air_exchanges:
            try:
                exchange_data = self._safe_get_data(exchange)
                exchange_name = str(exchange_data.get("name", "") or "").lower()
                exchange_type = exchange_data.get("type_val")
                max_flows = exchange_data.get("max_flows")
                units = exchange_data.get("units_strs") or {}
                units_val = exchange_data.get("units_val")
                active_rate = self._extract_flow_for_unit(max_flows, units_val)

                if exchange_type == 2 or (exchange_type is None and "ventilation" in exchange_name):
                    summary["ventilation_rate"] = active_rate
                    floor_flow = self._derive_m3_h_m2_from_flow_table(max_flows, units)
                    if floor_flow is None:
                        floor_flow = self._derive_m3_h_m2_from_person_flow(
                            max_flows,
                            units,
                            occupancy_density_m2_per_person,
                        )
                    facade_flow = self._derive_facade_m3_h_m2_from_flow_table(max_flows, units)
                    if floor_flow is not None:
                        summary["ventilation_m3_h_m2"] = (
                            float(summary["ventilation_m3_h_m2"] or 0.0) + floor_flow
                        )
                    if facade_flow is not None:
                        summary["ventilation_facade_m3_h_m2"] = (
                            float(summary["ventilation_facade_m3_h_m2"] or 0.0) + facade_flow
                        )

                if exchange_type == 0 or "infiltration" in exchange_name:
                    summary["infiltration_rate"] = active_rate
                    summary["infiltration_unit"] = self._lookup_unit_label(units, units_val)
                    summary["infiltration_m3_h_m2"] = self._derive_m3_h_m2_from_flow_table(max_flows, units)
            except Exception as e:
                logger.error("Error while analyzing air exchanges: %s", e)
        return summary

    @staticmethod
    def _lookup_unit_label(units: Any, units_val: Any) -> Optional[str]:
        """Return the VE unit label matching a unit index/value."""

        if not isinstance(units, dict):
            return None
        for key in (units_val, str(units_val)):
            if key in units:
                return str(units[key])
        return None

    @staticmethod
    def _extract_flow_for_unit(max_flows: Any, units_val: Any) -> Optional[float]:
        """Extract the active flow value for the selected VE unit."""

        if isinstance(max_flows, dict):
            for key in (units_val, str(units_val)):
                if key in max_flows:
                    return ModelAnalyzer._to_float_or_none(max_flows.get(key))
        return ModelAnalyzer._extract_first_numeric(max_flows)

    @staticmethod
    def _derive_m3_h_m2_from_flow_table(max_flows: Any, units: Any) -> Optional[float]:
        """Convert floor-area l/(s.m2) values to m3/(h.m2)."""
        if not isinstance(max_flows, dict) or not isinstance(units, dict):
            return None
        for key, unit_label in units.items():
            label = str(unit_label or "").lower().replace("²", "2")
            compact = "".join(character for character in label if not character.isspace())
            is_floor_area_rate = (
                "fac" not in compact
                and any(token in compact for token in ("l/(s.m2)", "l/(s*m2)", "l/s/m2", "l/sm2"))
            )
            if is_floor_area_rate:
                value = ModelAnalyzer._to_float_or_none(max_flows.get(key, max_flows.get(str(key))))
                if value is not None:
                    return value * 3.6
        return None

    @staticmethod
    def _derive_facade_m3_h_m2_from_flow_table(max_flows: Any, units: Any) -> Optional[float]:
        """Convert facade-area airflow separately from floor-area ventilation."""
        if not isinstance(max_flows, dict) or not isinstance(units, dict):
            return None
        for key, unit_label in units.items():
            label = str(unit_label or "").lower().replace("²", "2")
            compact = "".join(character for character in label if not character.isspace())
            if "fac" in compact and any(
                token in compact for token in ("l/(s.m2)", "l/(s*m2)", "l/s/m2", "l/sm2")
            ):
                value = ModelAnalyzer._to_float_or_none(max_flows.get(key, max_flows.get(str(key))))
                if value is not None:
                    return value * 3.6
        return None

    @staticmethod
    def _derive_m3_h_m2_from_person_flow(
        max_flows: Any,
        units: Any,
        occupancy_density_m2_per_person: Optional[float],
    ) -> Optional[float]:
        """Convert l/(s.person) to m3/(h.m2) using explicit occupancy evidence."""
        density = ModelAnalyzer._to_float_or_none(occupancy_density_m2_per_person)
        if (
            density is None
            or density <= 0.0
            or not isinstance(max_flows, dict)
            or not isinstance(units, dict)
        ):
            return None
        for key, unit_label in units.items():
            label = str(unit_label or "").lower().replace("Â²", "2")
            compact = "".join(character for character in label if not character.isspace())
            if any(
                token in compact
                for token in (
                    "l/(s.person)",
                    "l/(s.personne)",
                    "l/s/person",
                    "l/s/personne",
                    "l/s/pers",
                )
            ):
                value = ModelAnalyzer._to_float_or_none(
                    max_flows.get(key, max_flows.get(str(key)))
                )
                if value is not None:
                    return value * 3.6 / density
        return None

    def _analyze_hvac_systems(
        self,
        room_data: Any,
        room_conditions: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Extract documented Apache-system efficiencies and control metadata."""
        hvac_systems = []
        if not room_data:
            return hvac_systems

        system_data = self.data_extractor.get_apache_systems(room_data)
        hvac_id = system_data.get("HVAC_system") or ""
        if hvac_id:
            apache_data = (
                self.data_extractor.get_apache_system_data(hvac_id)
                if hasattr(self.data_extractor, "get_apache_system_data")
                else {}
            )
            heating = apache_data.get("heating", {}) or {}
            cooling = apache_data.get("cooling", {}) or {}
            cooling_ncm = apache_data.get("cooling_ncm", {}) or {}
            heating_ncm = apache_data.get("heating_ncm", {}) or {}
            ventilation_ncm = apache_data.get("ventilation_ncm", {}) or {}
            system_controls = apache_data.get("system_controls_ncm", {}) or {}
            text_blob = self._mapping_text(
                apache_data,
                system_data,
                room_conditions or {},
            )
            cooling_class = self._classify_cooling_generator(cooling, cooling_ncm, text_blob)
            heating_class = self._classify_heating_generator(heating, heating_ncm, text_blob)
            fan_control = self._extract_control_identifier(
                (ventilation_ncm, system_controls, apache_data.get("control", {})),
                ("fan_ctrl", "fan_control", "fancontrol"),
            )
            heat_recovery = self._extract_control_identifier(
                (ventilation_ncm, room_conditions or {}),
                ("heat_rec_type", "heat_recovery_type", "heat_recovery"),
            )
            ventilation_control = self._extract_control_identifier(
                (ventilation_ncm, room_conditions or {}),
                (
                    "air_flow_ctrl",
                    "airflow_control",
                    "demand_controlled_ventilation",
                    "ventilation_control",
                ),
            )
            system_type = self._extract_control_identifier(
                (ventilation_ncm, system_controls, apache_data.get("control", {})),
                ("sys_type", "system_type"),
            )
            eer = self._to_float_or_none(cooling.get("nominal_eer"))
            seer = self._to_float_or_none(cooling.get("SEER"))
            sseer = self._to_float_or_none(cooling.get("SSEER"))
            scop = self._to_float_or_none(heating.get("SCoP"))
            hvac_systems.append({
                "id": hvac_id,
                "name": apache_data.get("name", ""),
                "type": system_data.get("HVAC_methodology"),
                "conditioned": system_data.get("conditioned"),
                "cooling_generator_class": cooling_class,
                "heating_generator_class": heating_class,
                "cooling_capacity_kw": self._to_float_or_none(
                    cooling.get("gen_size") or system_data.get("cooling_unit_size")
                ),
                "heating_capacity_kw": self._to_float_or_none(
                    heating.get("gen_size") or system_data.get("heating_unit_size")
                ),
                "eer": eer,
                "seer": seer,
                "sseer": sseer,
                "scop": scop,
                "efficiency": seer if seer is not None else (eer if eer is not None else scop),
                "fan_control": self._normalize_identifier(fan_control),
                "system_type": self._normalize_identifier(system_type),
                "ventilation_control": self._normalize_identifier(ventilation_control),
                "heat_recovery_type": self._normalize_identifier(heat_recovery),
                # NCM seasonal heat-recovery efficiency (VEApacheSystem.ventilation_ncm),
                # confirmed extractable on real projects. Compared to the SIA 380/2
                # reference eta_rec in the reference-project family.
                "heat_recovery_efficiency": self._to_float_or_none(
                    ventilation_ncm.get("heat_recovery_efficiency")
                ),
                "cooling_raw": dict(cooling),
                "heating_raw": dict(heating),
                "ventilation_ncm_raw": dict(ventilation_ncm),
                "energy_consumption": None,
            })
        return hvac_systems

    def _analyze_window_ventilation(self, openings: List[OpeningData]) -> Dict[str, Any]:
        """Classify window ventilation support from MacroFlo assignments."""
        external_windows = [
            opening
            for opening in openings
            if opening.is_external
            and self._normalize_opening_type(opening.opening_type) == "window"
        ]
        if not external_windows:
            return {"window_operable": None, "window_ventilation_support": None}
        macroflo_rows = (
            self.data_extractor.get_macroflo_openings()
            if hasattr(self.data_extractor, "get_macroflo_openings")
            else {}
        )
        matched_rows = [
            macroflo_rows.get(opening.macroflo_id)
            for opening in external_windows
            if opening.macroflo_id and macroflo_rows.get(opening.macroflo_id)
        ]
        explicitly_operable = [
            row
            for row in matched_rows
            if (self._to_float_or_none((row or {}).get("openable_area")) or 0.0) > 0.0
        ]
        if not explicitly_operable and not any(opening.macroflo_id for opening in external_windows):
            return {"window_operable": False, "window_ventilation_support": "no_window_support"}
        if not explicitly_operable:
            return {"window_operable": None, "window_ventilation_support": None}

        profile_hours = []
        for row in explicitly_operable:
            profile_id = str((row or {}).get("profile") or "")
            if profile_id and hasattr(self.data_extractor, "get_profile_daily_equivalent_hours"):
                hours = self.data_extractor.get_profile_daily_equivalent_hours(profile_id)
                if hours is not None:
                    profile_hours.append(hours)
        support = (
            "day_and_night_window_support"
            if profile_hours and max(profile_hours) >= 23.5
            else "occupied_hours_window_support"
        )
        return {"window_operable": True, "window_ventilation_support": support}

    def _annotate_hvac_zoning_and_controls(self, rooms_data: List[RoomData]) -> None:
        """Add monozone/multizone and comparable control levels after room extraction."""
        zone_membership = (
            self.data_extractor.get_room_zone_membership()
            if hasattr(self.data_extractor, "get_room_zone_membership")
            else {}
        )
        for room in rooms_data:
            zone = dict(zone_membership.get(str(room.id), {}) or {})
            room.hvac_zone = zone
            system_types = {
                str(system.get("system_type") or "").upper()
                for system in room.hvac_systems
                if system.get("system_type")
            }
            if any(value in {"MULTI_ZONE", "MULTIZONE"} for value in system_types):
                room.ventilation_installation_type = "multizone"
            elif any(value in {"SINGLE_ZONE", "SINGLEZONE"} for value in system_types):
                room.ventilation_installation_type = "monozone"
            elif zone.get("zone_room_count") not in (None, ""):
                # Use the tolerant float conversion so a non-numeric zone room
                # count cannot crash the whole model analysis (report generation).
                room.ventilation_installation_type = (
                    "multizone"
                    if self._to_float(zone.get("zone_room_count")) > 1
                    else "monozone"
                )
            else:
                room.ventilation_installation_type = None
            control_label, control_level = self._derive_ventilation_control(room)
            room.ventilation_control = control_label
            room.ventilation_control_level = control_level

    def _derive_ventilation_control(self, room: RoomData) -> Any:
        """Map VE fan/demand-control evidence to the ordered table-4 strategies."""
        tokens = self._mapping_text(
            room.room_conditions,
            room.hvac_systems,
            room.fan_control or "",
        )
        fan_control = self._normalize_identifier(room.fan_control)
        variable_speed = any(token in tokens for token in ("variable", "min_pres", "const_pres"))
        gas_control = any(token in tokens for token in ("gas_sensor", "gas sensor", "co2"))
        occupancy_control = any(token in tokens for token in ("occupancy", "occupant", "people_count"))
        staged = any(token in tokens for token in ("multi_stage", "two_speed", "two speed", "67/100"))
        schedule = any(token in tokens for token in ("schedule", "time_control", "on_off"))

        if gas_control and variable_speed:
            return "variable speed >=25%, demand control by gas sensor", 4
        if occupancy_control and variable_speed:
            return "variable speed >=25%, demand control by occupancy", 3
        if occupancy_control and staged:
            return "two speeds 67/100%, occupancy control", 2
        if staged:
            return "two speeds 67/100%, time schedule control", 1
        if schedule or fan_control == "DIRECT":
            return "one speed, time schedule control", 0
        return None, None

    @staticmethod
    def _first_hvac_value(hvac_systems: List[Dict[str, Any]], key: str) -> Optional[str]:
        """Return the first non-empty normalized HVAC metadata value."""
        for system in hvac_systems:
            value = system.get(key)
            if value not in (None, ""):
                return str(value)
        return None

    @classmethod
    def _mapping_text(cls, *values: Any) -> str:
        """Flatten nested VE dictionaries into lowercase text for identifier matching."""
        parts: List[str] = []

        def has_value(value: Any) -> bool:
            """Return true when a nested value contains explicit non-empty data."""
            if isinstance(value, dict):
                return any(has_value(child) for child in value.values())
            if isinstance(value, (list, tuple, set)):
                return any(has_value(child) for child in value)
            return value not in (None, "", False)

        def visit(value: Any) -> None:
            """Append nested mapping keys and scalar values to the text buffer."""
            if isinstance(value, dict):
                for key, child in value.items():
                    if has_value(child):
                        parts.append(str(key))
                        visit(child)
            elif isinstance(value, (list, tuple, set)):
                for child in value:
                    visit(child)
            elif value not in (None, ""):
                parts.append(str(value))

        for value in values:
            visit(value)
        return " ".join(parts).lower()

    @classmethod
    def _extract_control_identifier(cls, mappings: Any, keys: Any) -> Optional[str]:
        """Read a control identifier from nested VE dictionaries by normalized key."""
        wanted = {cls._normalize_identifier(key) for key in keys}

        def visit(value: Any) -> Optional[str]:
            """Search nested mappings for the first requested control key."""
            if isinstance(value, dict):
                for key, child in value.items():
                    if cls._normalize_identifier(key) in wanted and child not in (None, ""):
                        return str(child)
                    nested = visit(child)
                    if nested:
                        return nested
            elif isinstance(value, (list, tuple)):
                for child in value:
                    nested = visit(child)
                    if nested:
                        return nested
            return None

        return visit(mappings)

    @classmethod
    def _classify_cooling_generator(
        cls,
        cooling: Dict[str, Any],
        cooling_ncm: Dict[str, Any],
        text_blob: str,
    ) -> Optional[str]:
        """Classify a cooling generator only from explicit VE metadata."""
        if bool(cooling.get("has_absorption_chiller")):
            return "absorption_chiller"
        text = cls._mapping_text(cooling_ncm, text_blob)
        if any(token in text for token in ("dry post", "post_cooling", "post cooling", "dry_cooler")):
            return "water_cooled_post_cooling"
        if any(token in text for token in ("water_cooled", "water cooled", "water condenser")):
            return "water_cooled"
        if any(token in text for token in ("air_cooled", "air cooled", "air condenser")):
            return "air_cooled"
        return None

    @classmethod
    def _classify_heating_generator(
        cls,
        heating: Dict[str, Any],
        heating_ncm: Dict[str, Any],
        text_blob: str,
    ) -> Optional[str]:
        """Classify a heat pump only when its source/sink is explicit in VE data."""
        if not bool(heating.get("Is_heat_pump")):
            return None
        text = cls._mapping_text(heating_ncm, text_blob)
        if any(token in text for token in ("ground_source", "ground source", "brine", "geothermal")):
            return "ground_source_heat_pump"
        if any(token in text for token in ("air_water", "air water", "air-to-water", "air to water")):
            return "air_water_heat_pump"
        return "heat_pump_unclassified"

    @staticmethod
    def _normalize_identifier(value: Any) -> str:
        """Normalize VE enum/control labels to uppercase underscore identifiers."""
        text = str(value or "").strip().upper()
        return "_".join(part for part in text.replace("-", " ").split() if part)

    def _analyze_room_conditions(self, room_data: Any) -> Dict[str, Any]:
        """Extract room setpoint, schedule and humidity condition data."""
        if not room_data:
            return {}
        try:
            return self.data_extractor.get_room_conditions(room_data)
        except Exception as e:
            logger.error("Error while analyzing room conditions: %s", e)
            return {}

    def _safe_get_attribute(self, obj: Any, attribute_name: str) -> Any:
        """Read a VE attribute defensively, including callable attributes."""
        if obj is None:
            return None
        try:
            value = getattr(obj, attribute_name)
        except Exception:
            return None
        if callable(value):
            try:
                return value()
            except TypeError:
                return None
            except Exception:
                return None
        return value

    def _get_body_areas(self, body: Any) -> Dict[str, float]:
        """Return documented ``VEBody.get_areas()`` values."""
        if hasattr(self.data_extractor, "get_body_areas"):
            return self.data_extractor.get_body_areas(body)
        try:
            return self.data_extractor._as_dict(body.get_areas())
        except Exception:
            return {}

    @staticmethod
    def _safe_get_data(obj: Any) -> Dict[str, Any]:
        """Read dictionaries returned by child ``VERoomData`` objects."""
        if obj is None:
            return {}
        if isinstance(obj, dict):
            return obj
        try:
            if hasattr(obj, "get"):
                data = obj.get()
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}
        return {}

    @staticmethod
    def _extract_first_numeric(value: Any) -> Optional[float]:
        """Extract the first numeric value from VE unit-indexed dictionaries."""
        if value is None:
            return None
        if isinstance(value, dict):
            for preferred_key in (0, "0", 1, "1"):
                if preferred_key in value:
                    try:
                        return float(value[preferred_key])
                    except (TypeError, ValueError):
                        pass
            iterable = value.values()
        elif isinstance(value, (list, tuple)):
            iterable = value
        else:
            iterable = (value,)
        for item in iterable:
            try:
                return float(item)
            except (TypeError, ValueError):
                continue
        return None

    @staticmethod
    def _to_float(value: Any) -> float:
        """Convert a value to float, returning ``0.0`` when conversion fails."""

        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _to_float_or_none(value: Any) -> Optional[float]:
        """Convert a value to float, returning ``None`` when conversion fails."""

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _get_body_name(self, body: Any) -> str:
        """Return the best available ``VEBody`` name or ID."""
        if body is None:
            return ""
        name = self._safe_get_attribute(body, "name")
        if name not in (None, ""):
            return str(name)
        return self.data_extractor.get_object_id(body)

    def _get_surface_name(self, surface: Any) -> str:
        """Return the best available ``VESurface`` name or ID."""
        if surface is None:
            return ""

        name = self._safe_get_attribute(surface, "name")
        if name not in (None, ""):
            return str(name)

        try:
            props = self.data_extractor._as_dict(surface.get_properties())
            for key in ("name", "id"):
                value = props.get(key)
                if value not in (None, ""):
                    return str(value)
        except Exception:
            pass

        return self.data_extractor.get_object_id(surface)

    def _get_opening_name(self, opening: Any) -> str:
        """Return the best available opening name or ID."""
        if opening is None:
            return ""

        name = self._safe_get_attribute(opening, "name")
        if name not in (None, ""):
            return str(name)

        try:
            props = self.data_extractor._as_dict(opening.get_properties())
            for key in ("name", "id"):
                value = props.get(key)
                if value not in (None, ""):
                    return str(value)
        except Exception:
            pass

        return self.data_extractor.get_object_id(opening)

    def _get_adjacency_body_id(self, adjacency: Any) -> str:
        """Return the adjacent room ID from documented ``VEAdjacency`` properties."""
        if adjacency is None:
            return ""

        if isinstance(adjacency, dict):
            return str(adjacency.get("body_id") or "")

        try:
            props = self.data_extractor._as_dict(adjacency.get_properties())
            if props:
                return str(props.get("body_id") or "")
        except Exception:
            pass

        return ""

    def _normalize_surface_type(self, surface_type: Any) -> str:
        """Normalize IESVE surface types to reusable categories."""
        raw = str(surface_type or "").strip().lower()
        if not raw:
            return ""
        if "." in raw:
            raw = raw.split(".")[-1]
        raw = raw.replace(" ", "_").replace("-", "_")
        if raw.startswith("ext_"):
            raw = raw[4:]
        elif raw.startswith("int_"):
            raw = raw[4:]
        if raw.startswith("ground_"):
            raw = raw[7:]
        return raw if raw in {"wall", "roof", "floor", "ceiling", "glazing", "door", "hole"} else raw

    def _normalize_opening_type(self, opening_type: Any) -> str:
        """Normalize IESVE opening types to reusable categories."""
        if opening_type in (4, "4"):
            return "window"
        if opening_type in (5, "5", 6, "6"):
            return "door"
        if opening_type in (11, "11"):
            return "hole"
        normalized = self._normalize_surface_type(opening_type)
        if normalized in {"glazing", "window"}:
            return "window"
        if normalized == "door":
            return "door"
        return normalized

    def _is_external_surface(self, surface_type: Any) -> bool:
        """Return whether a ``VESurface`` type should be treated as external."""
        raw = str(surface_type or "").strip().lower()
        if not raw:
            return False
        if "." in raw:
            raw = raw.split(".")[-1]
        raw = raw.replace(" ", "_").replace("-", "_")
        if raw.startswith("ext_") or "external" in raw:
            return True
        if raw.startswith("int_"):
            return False
        return raw in {"roof", "ground_floor"}

    # =============================================================================
    # Calculation helpers
    # =============================================================================

    def calculate_wwr(self, room_data: RoomData) -> float:
        """Calculate the window-to-wall ratio for one room."""
        external_walls = [s for s in room_data.surfaces if s.is_external and self._normalize_surface_type(s.surface_type) in {"wall", "ext_wall"}]
        wall_area = sum(s.area for s in external_walls)
        window_area = sum(o.area for o in room_data.openings if o.is_external and o.opening_type == "window")
        return window_area / wall_area if wall_area > 0 else 0.0

    def calculate_average_u_value(self, room_data: RoomData, surface_type: str) -> float:
        """Calculate the area-weighted average U-value for one surface type."""
        normalized_target = self._normalize_surface_type(surface_type)
        surfaces = [
            s for s in room_data.surfaces
            if self._normalize_surface_type(s.surface_type) == normalized_target
            and s.u_value is not None
            and getattr(s, "net_area", s.area) > 1e-6
        ]
        weighted_sum = sum(float(s.u_value) * float(getattr(s, "net_area", s.area)) for s in surfaces)
        total_area = sum(float(getattr(s, "net_area", s.area)) for s in surfaces)
        return weighted_sum / total_area if total_area > 0 else 0.0

    def calculate_total_energy_consumption(self, energy_sources: Dict[str, Any]) -> Optional[float]:
        """Return annual consumption only for explicit consumption objects."""
        total_energy = 0.0
        supported_count = 0
        for source in energy_sources.values():
            try:
                total_energy += source.get_annual_consumption()
                supported_count += 1
            except Exception as e:
                logger.debug("Energy-source metadata has no annual consumption result: %s", e)
        return total_energy if supported_count else None

    def calculate_total_area(self, rooms_data: List[RoomData]) -> float:
        """Calculate the total analyzed floor area."""
        return sum(room.area for room in rooms_data)

    def calculate_total_volume(self, rooms_data: List[RoomData]) -> float:
        """Calculate the total analyzed room volume."""
        return sum(room.volume for room in rooms_data)

    def calculate_compacity(self, rooms_data: List[RoomData]) -> float:
        """Calculate the volume-to-area compactness indicator."""
        total_volume = self.calculate_total_volume(rooms_data)
        total_area = self.calculate_total_area(rooms_data)
        return total_volume / total_area if total_area > 0 else 0.0

    def get_external_surfaces(self, room_data: RoomData) -> List[SurfaceData]:
        """Return external surfaces for one room."""
        return [s for s in room_data.surfaces if s.is_external]

    def get_windows(self, room_data: RoomData) -> List[OpeningData]:
        """Return window openings for one room."""
        return [o for o in room_data.openings if self._normalize_opening_type(o.opening_type) == "window"]

    def get_external_walls(self, room_data: RoomData) -> List[SurfaceData]:
        """Return external wall surfaces for one room."""
        return [s for s in room_data.surfaces if s.is_external and self._normalize_surface_type(s.surface_type) == "wall"]
