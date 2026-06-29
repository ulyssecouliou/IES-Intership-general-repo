"""
Analyseur du modèle VE pour calculer des indicateurs (U-values, WWR, gains internes, etc.).
Ce module prépare les données du modèle pour les vérifications SIA.
"""

from __future__ import annotations

import logging
from typing import List, Dict, Optional, Any, TYPE_CHECKING
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from data_extractor import VEDataExtractor

logger = logging.getLogger(__name__)

@dataclass
class SurfaceData:
    """Données d'une surface (mur, toiture, plancher)."""
    id: str
    name: str = ""  # Nom de la surface (peut être vide)
    area: float = 0.0
    net_area: float = 0.0
    u_value: Optional[float] = None
    orientation: Optional[str] = None
    materials: List[str] = field(default_factory=list)
    is_external: bool = False
    surface_type: Optional[str] = None  # "wall", "roof", "floor", etc.
    construction_ids: List[str] = field(default_factory=list)

@dataclass
class OpeningData:
    """Données d'une ouverture (fenêtre, porte)."""
    id: str
    name: str = ""  # Nom de l'ouverture (peut être vide)
    area: float = 0.0
    u_value: Optional[float] = None
    solar_factor: Optional[float] = None
    orientation: Optional[str] = None
    opening_type: Optional[str] = None  # "window", "door", etc.
    is_external: bool = False
    construction_id: str = ""

@dataclass
class RoomData:
    """Données d'une pièce."""
    id: str
    name: str = ""  # Nom de la pièce (peut être vide)
    volume: float = 0.0
    area: float = 0.0
    surfaces: List[SurfaceData] = field(default_factory=list)
    openings: List[OpeningData] = field(default_factory=list)
    internal_gains: Dict[str, Optional[float]] = field(default_factory=dict)  # {"lighting": ..., "people": ..., "equipment": ...}
    ventilation_rate: Optional[float] = None
    infiltration_rate: Optional[float] = None
    infiltration_unit: Optional[str] = None
    infiltration_m3_h_m2: Optional[float] = None
    hvac_systems: List[Dict[str, Any]] = field(default_factory=list)
    room_conditions: Dict[str, Any] = field(default_factory=dict)

class ModelAnalyzer:
    """
    Analyse le modèle VE pour calculer des indicateurs utiles pour la conformité SIA.
    """

    def __init__(self, data_extractor: "VEDataExtractor"):
        self.data_extractor = data_extractor
        self._rooms_data: Dict[str, RoomData] = {}

    def analyze_all_rooms(self) -> List[RoomData]:
        """Analyse toutes les pièces du modèle et retourne leurs données."""
        rooms_data = []
        bodies = self.data_extractor.get_bodies()
        for body in bodies:
            room_data = self.analyze_room(body)
            if room_data:
                rooms_data.append(room_data)
                self._rooms_data[self.data_extractor.get_object_id(body)] = room_data
        return rooms_data

    def analyze_room(self, body: Any) -> Optional[RoomData]:
        """Analyse une pièce et retourne ses données structurées."""
        try:
            room_data_obj = self.data_extractor.get_room_data(body)
            raw_surfaces = self.data_extractor.get_surfaces(body) or []
            surfaces = self._analyze_surfaces(raw_surfaces)
            openings = self._analyze_openings(raw_surfaces)
            internal_gains = self._analyze_internal_gains(room_data_obj) if room_data_obj else {}
            air_exchange_summary = self._analyze_air_exchanges(room_data_obj) if room_data_obj else {}
            ventilation_rate = air_exchange_summary.get("ventilation_rate")
            infiltration_rate = air_exchange_summary.get("infiltration_rate")
            infiltration_unit = air_exchange_summary.get("infiltration_unit")
            infiltration_m3_h_m2 = air_exchange_summary.get("infiltration_m3_h_m2")
            hvac_systems = self._analyze_hvac_systems(room_data_obj) if room_data_obj else []
            room_conditions = self._analyze_room_conditions(room_data_obj) if room_data_obj else {}

            body_areas = self._get_body_areas(body)
            return RoomData(
                id=self.data_extractor.get_object_id(body),
                name=self._get_body_name(body),
                volume=float(body_areas.get("volume", 0.0) or 0.0),
                area=float(body_areas.get("int_floor_area", 0.0) or 0.0) + float(body_areas.get("ext_floor_area", 0.0) or 0.0),
                surfaces=surfaces,
                openings=openings,
                internal_gains=internal_gains,
                ventilation_rate=ventilation_rate,
                infiltration_rate=infiltration_rate,
                infiltration_unit=infiltration_unit,
                infiltration_m3_h_m2=infiltration_m3_h_m2,
                hvac_systems=hvac_systems,
                room_conditions=room_conditions,
            )
        except Exception as e:
            logger.debug("Pièce ignorée lors de l'analyse: %s", e)
            return None

    def _analyze_surfaces(self, surfaces: List[Any]) -> List[SurfaceData]:
        """Analyse les surfaces d'une pièce via les méthodes documentées de VESurface."""
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

                external_net = self._to_float(areas.get("external_net"))
                total_net = self._to_float(areas.get("total_net"))
                net_area = external_net if external_gross > 0 else total_net
                if net_area <= 0 and gross_area > 0 and self._to_float(areas.get("total_gross_openings")) <= 1e-6:
                    net_area = gross_area
                u_value = props.get("U-value")
                orientation = props.get("orientation")
                materials = list(props.get("materials", []) or [])
                surface_type = str(props.get("type", "") or "").lower()
                construction_ids = [str(item) for item in props.get("construction_ids", []) or []]

                is_external = self._is_external_surface(surface_type) or float(areas.get("external_gross", 0.0) or 0.0) > 0
                if not is_external:
                    try:
                        adjacencies = self.data_extractor.get_adjacencies(surface) or []
                        is_external = any(self._get_adjacency_type(adj) == "external_air" for adj in adjacencies)
                    except Exception:
                        is_external = False

                surfaces_data.append(SurfaceData(
                    id=surface_id,
                    name=self._get_surface_name(surface),
                    area=gross_area,
                    net_area=net_area,
                    u_value=u_value,
                    orientation=orientation,
                    materials=materials,
                    is_external=is_external,
                    surface_type=surface_type,
                    construction_ids=construction_ids,
                ))
            except Exception:
                continue
        return surfaces_data

    def _analyze_openings(self, surfaces: List[Any]) -> List[OpeningData]:
        """Analyse les ouvertures d'une pièce via get_openings() sur les surfaces."""
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
                    orientation = props.get("orientation") or surface_orientation
                    opening_type = self._normalize_opening_type(props.get("type"))
                    construction_id = str(props.get("construction_id", "") or "")

                    openings_data.append(OpeningData(
                        id=opening_id,
                        name=self._get_opening_name(opening),
                        area=area,
                        u_value=u_value,
                        solar_factor=solar_factor,
                        orientation=orientation,
                        opening_type=opening_type,
                        is_external=is_external,
                        construction_id=construction_id,
                    ))
                except Exception:
                    continue
        return openings_data

    def _analyze_internal_gains(self, room_data: Any) -> Dict[str, Optional[float]]:
        """Analyse les gains internes (éclairage, occupants, équipements) d'une pièce."""
        gains = {"lighting": None, "people": None, "equipment": None}
        if not room_data:
            return gains

        internal_gains = self.data_extractor.get_internal_gains(room_data)
        for gain in internal_gains:
            try:
                gain_data = self._safe_get_data(gain)
                gain_type = str(gain_data.get("type_str", "")).lower()
                density = self._extract_first_numeric(gain_data.get("max_power_consumptions"))
                if density is None:
                    density = self._extract_first_numeric(gain_data.get("max_sensible_gains"))
                if "lighting" in gain_type or "fluorescent" in gain_type or "tungsten" in gain_type:
                    gains["lighting"] = density or gains["lighting"]
                elif "people" in gain_type:
                    gains["people"] = self._extract_first_numeric(gain_data.get("occupancies")) or gains["people"]
                elif any(token in gain_type for token in ("machinery", "misc", "cooking", "computer", "equipment")):
                    gains["equipment"] = density or gains["equipment"]
            except Exception as e:
                logger.error(f"Erreur lors de l'analyse des gains internes: {e}")
        return gains

    def _analyze_ventilation(self, room_data: Any) -> Optional[float]:
        """Analyse le débit de ventilation d'une pièce."""
        if not room_data:
            return None

        air_exchanges = self.data_extractor.get_air_exchanges(room_data)
        for exchange in air_exchanges:
            try:
                exchange_data = self._safe_get_data(exchange)
                if exchange_data.get("type_val") == 2 and exchange_data.get("units_val") == 0:
                    return self._extract_first_numeric(exchange_data.get("max_flows"))
            except Exception as e:
                logger.error(f"Erreur lors de l'analyse de la ventilation: {e}")
        return None

    def _analyze_air_exchanges(self, room_data: Any) -> Dict[str, Optional[float]]:
        """Analyse ventilation et infiltration depuis les echanges d'air VE."""
        summary: Dict[str, Any] = {
            "ventilation_rate": None,
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

                if exchange_type == 2 or "ventilation" in exchange_name:
                    summary["ventilation_rate"] = active_rate

                if exchange_type == 0 or "infiltration" in exchange_name:
                    summary["infiltration_rate"] = active_rate
                    summary["infiltration_unit"] = self._lookup_unit_label(units, units_val)
                    summary["infiltration_m3_h_m2"] = self._derive_m3_h_m2_from_flow_table(max_flows, units)
            except Exception as e:
                logger.error(f"Erreur lors de l'analyse des echanges d'air: {e}")
        return summary

    @staticmethod
    def _lookup_unit_label(units: Any, units_val: Any) -> Optional[str]:
        if not isinstance(units, dict):
            return None
        for key in (units_val, str(units_val)):
            if key in units:
                return str(units[key])
        return None

    @staticmethod
    def _extract_flow_for_unit(max_flows: Any, units_val: Any) -> Optional[float]:
        if isinstance(max_flows, dict):
            for key in (units_val, str(units_val)):
                if key in max_flows:
                    return ModelAnalyzer._to_float_or_none(max_flows.get(key))
        return ModelAnalyzer._extract_first_numeric(max_flows)

    @staticmethod
    def _derive_m3_h_m2_from_flow_table(max_flows: Any, units: Any) -> Optional[float]:
        """Convertit l/(s.m2) en m3/(h.m2) quand VE expose cette unite."""
        if not isinstance(max_flows, dict) or not isinstance(units, dict):
            return None
        preferred = []
        fallback = []
        for key, unit_label in units.items():
            label = str(unit_label or "").lower()
            if "l/(s" in label and "m" in label:
                if "fac" in label:
                    preferred.append(key)
                else:
                    fallback.append(key)
        for key in preferred + fallback:
            value = ModelAnalyzer._to_float_or_none(max_flows.get(key))
            if value is not None:
                return value * 3.6
        return None

    def _analyze_hvac_systems(self, room_data: Any) -> List[Dict[str, Any]]:
        """Analyse les systèmes CVC d'une pièce."""
        hvac_systems = []
        if not room_data:
            return hvac_systems

        system_data = self.data_extractor.get_apache_systems(room_data)
        hvac_id = system_data.get("HVAC_system") or ""
        if hvac_id:
            hvac_systems.append({
                "id": hvac_id,
                "type": system_data.get("HVAC_methodology"),
                "conditioned": system_data.get("conditioned"),
                "efficiency": None,
                "energy_consumption": None,
            })
        return hvac_systems

    def _analyze_room_conditions(self, room_data: Any) -> Dict[str, Any]:
        """Analyse les conditions de la pièce (températures, humidité)."""
        if not room_data:
            return {}
        try:
            return self.data_extractor.get_room_conditions(room_data)
        except Exception as e:
            logger.error(f"Erreur lors de l'analyse des conditions de la pièce: {e}")
            return {}

    def _safe_get_attribute(self, obj: Any, attribute_name: str) -> Any:
        """Lit un attribut VE de manière totalement tolérante."""
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
        """Récupère les aires documentées de VEBody.get_areas()."""
        if hasattr(self.data_extractor, "get_body_areas"):
            return self.data_extractor.get_body_areas(body)
        try:
            return self.data_extractor._as_dict(body.get_areas())
        except Exception:
            return {}

    @staticmethod
    def _safe_get_data(obj: Any) -> Dict[str, Any]:
        """Lit les dictionnaires renvoyés par les objets VERoomData enfants."""
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
        """Extrait une valeur numérique depuis les dictionnaires VE indexés par unités."""
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
        try:
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    @staticmethod
    def _to_float_or_none(value: Any) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def _get_body_name(self, body: Any) -> str:
        """Récupère le nom d'un VEBody via les attributs réellement exposés."""
        if body is None:
            return ""
        name = self._safe_get_attribute(body, "name")
        if name not in (None, ""):
            return str(name)
        return self.data_extractor.get_object_id(body)

    def _get_surface_name(self, surface: Any) -> str:
        """Récupère le nom d'un VESurface via les méthodes documentées et les propriétés."""
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
        """Récupère le nom d'une ouverture via ses propriétés si elle n'expose pas d'attribut name."""
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

    def _get_adjacency_type(self, adjacency: Any) -> str:
        """Retourne le type d'une adjacence via les propriétés documentées de VEAdjacency."""
        if adjacency is None:
            return ""

        if isinstance(adjacency, dict):
            return str(adjacency.get("type") or adjacency.get("name") or "")

        adjacency_type = self._safe_get_attribute(adjacency, "type")
        if adjacency_type is not None:
            return str(adjacency_type)

        try:
            props = self.data_extractor._as_dict(adjacency.get_properties())
            if props:
                return str(props.get("type") or props.get("name") or "")
        except Exception:
            pass

        return ""

    def _normalize_surface_type(self, surface_type: Any) -> str:
        """Normalise les types de surface IESVE vers des catégories réutilisables."""
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
        """Normalise les types d'ouverture IESVE vers des catégories réutilisables."""
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
        """Détermine si une surface VESurface est externe à partir de son type."""
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
    # MÉTHODES DE CALCUL
    # =============================================================================

    def calculate_wwr(self, room_data: RoomData) -> float:
        """Calcule le Window-to-Wall Ratio (WWR) pour une pièce."""
        external_walls = [s for s in room_data.surfaces if s.is_external and self._normalize_surface_type(s.surface_type) in {"wall", "ext_wall"}]
        wall_area = sum(s.area for s in external_walls)
        window_area = sum(o.area for o in room_data.openings if o.is_external and o.opening_type == "window")
        return window_area / wall_area if wall_area > 0 else 0.0

    def calculate_average_u_value(self, room_data: RoomData, surface_type: str) -> float:
        """Calcule la U-value moyenne pour un type de surface donné."""
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

    def calculate_total_energy_consumption(self, energy_sources: Dict[str, Any]) -> float:
        """Calcule la consommation énergétique totale (kWh/an)."""
        total_energy = 0.0
        for source in energy_sources.values():
            try:
                total_energy += source.get_annual_consumption()
            except Exception as e:
                logger.error(f"Erreur lors du calcul de la consommation énergétique: {e}")
        return total_energy

    def calculate_total_area(self, rooms_data: List[RoomData]) -> float:
        """Calcule la surface totale du bâtiment (m²)."""
        return sum(room.area for room in rooms_data)

    def calculate_total_volume(self, rooms_data: List[RoomData]) -> float:
        """Calcule le volume total du bâtiment (m³)."""
        return sum(room.volume for room in rooms_data)

    def calculate_compacity(self, rooms_data: List[RoomData]) -> float:
        """Calcule la compacité du bâtiment (Volume / Surface)."""
        total_volume = self.calculate_total_volume(rooms_data)
        total_area = self.calculate_total_area(rooms_data)
        return total_volume / total_area if total_area > 0 else 0.0

    def get_external_surfaces(self, room_data: RoomData) -> List[SurfaceData]:
        """Retourne les surfaces externes d'une pièce."""
        return [s for s in room_data.surfaces if s.is_external]

    def get_windows(self, room_data: RoomData) -> List[OpeningData]:
        """Retourne les fenêtres d'une pièce."""
        return [o for o in room_data.openings if self._normalize_opening_type(o.opening_type) == "window"]

    def get_external_walls(self, room_data: RoomData) -> List[SurfaceData]:
        """Retourne les murs extérieurs d'une pièce."""
        return [s for s in room_data.surfaces if s.is_external and self._normalize_surface_type(s.surface_type) == "wall"]
