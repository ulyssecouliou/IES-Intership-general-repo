"""Defensive VE model data extraction through the documented IESVE API.

This module centralizes all direct IESVE calls used by the compliance checker.
It normalizes return shapes, caches repeated API calls, and keeps extraction
failures visible without crashing the VE Run-button workflow.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class VEDataExtractor:
    """Extract SIA-relevant data from the active VE project."""

    def __init__(self, project: Optional[Any] = None):
        """Initialize the extractor with a VE project or the active VE project."""
        self.project = project
        if self.project is None:
            try:
                import importlib
                iesve = importlib.import_module("iesve")
                self.project = iesve.VEProject.get_current_project()
            except Exception:
                self.project = None

        if not self.project:
            raise RuntimeError("No VE project found. Open a project in IESVE before running the checker.")

        # Cache frequently accessed VE objects to keep the Run-button workflow fast.
        self._model: Optional[Any] = None
        self._bodies: Dict[bool, List[Any]] = {}
        self._surfaces: Dict[str, List[Any]] = {}  # body_id -> surfaces
        self._openings: Dict[str, List[Any]] = {}  # surface_id -> openings
        self._templates: Dict[str, Any] = {}  # template_id -> VEThermalTemplate
        self._hvac_systems: Dict[str, Any] = {}
        self._profiles: Optional[Dict[str, Any]] = None
        self._profile_daily_hours: Dict[str, Optional[float]] = {}
        self._room_zone_membership: Optional[Dict[str, Dict[str, Any]]] = None
        self._macroflo_openings: Optional[Dict[str, Dict[str, Any]]] = None
        self._energy_sources: Dict[str, Any] = {}
        self._construction_properties: Dict[str, Dict[str, Any]] = {}
        self._cdb_projects: Optional[List[Any]] = None
        self._weather_data: Optional[Any] = None
        self._body_extraction_diagnostics: Optional[Dict[str, Any]] = None
        self._model_selection_diagnostics: Optional[Dict[str, Any]] = None
        self._room_data_cache: Dict[str, Any] = {}  # body_id -> VERoomData

        logger.info("VEDataExtractor initialized successfully.")

    @property
    def model(self) -> Any:
        """Return the selected VE model that exposes the best room body set."""
        if self._model is None:
            try:
                models = self._as_list(self.project.models)
                if models:
                    self._model = self._select_best_model(models)
                else:
                    raise RuntimeError("No model found in the VE project.")
            except Exception as e:
                logger.error("Error while retrieving the VE model: %s", e)
                raise
        return self._model

    def _select_best_model(self, models: List[Any]) -> Any:
        """Select the documented real/proposed VE building at model index zero."""
        model_rows: List[Dict[str, Any]] = []

        for index, model in enumerate(models):
            raw_bodies: List[Any] = []
            error = ""
            try:
                raw_bodies = self._as_list(model.get_bodies(False))
            except Exception as e:
                error = str(e)

            relevant_count = sum(
                1 for body in raw_bodies
                if self._is_relevant_body(body)
            )
            raw_count = len(raw_bodies)
            model_rows.append({
                "index": index,
                "model_type": self._normalize_enum_name(getattr(model, "model_type", None)),
                "raw_body_count": raw_count,
                "relevant_body_count": relevant_count,
                "error": error,
            })

        self._model_selection_diagnostics = {
            "model_count": len(models),
            "selected_model_index": 0,
            "selection_basis": "IESVE documents project.models[0] as the real/proposed building",
            "models": model_rows,
        }
        return models[0]

    def get_model_selection_diagnostics(self) -> Dict[str, Any]:
        """Return model-selection diagnostics for report preflight checks."""
        if self._model_selection_diagnostics is None:
            _ = self.model
        return dict(self._model_selection_diagnostics or {})

    def get_bodies(self, selected_only: bool = False) -> List[Any]:
        """Return relevant VE room bodies from ``VEModel.get_bodies``."""
        if selected_only not in self._bodies:
            try:
                all_bodies = self._as_list(self.model.get_bodies(selected_only))
                self._bodies[selected_only] = [
                    body for body in all_bodies
                    if self._is_relevant_body(body)
                ]
            except Exception as e:
                logger.error("Error while retrieving VE bodies: %s", e)
                self._bodies[selected_only] = []
        return self._bodies[selected_only]

    def get_body_extraction_diagnostics(self) -> Dict[str, Any]:
        """Return raw-vs-filtered VE body counts for report preflight diagnostics."""
        if self._body_extraction_diagnostics is None:
            diagnostics: Dict[str, Any] = {
                "status": "UNKNOWN",
                "raw_body_count": 0,
                "relevant_body_count": 0,
                "discarded_body_count": 0,
                "discarded_sample": [],
                "model_count": 0,
                "selected_model_index": 0,
                "model_summaries": [],
                "error": "",
            }
            try:
                model_diagnostics = self.get_model_selection_diagnostics()
                raw_bodies = self._as_list(self.model.get_bodies(False))
                relevant_bodies = [
                    body for body in raw_bodies
                    if self._is_relevant_body(body)
                ]
                discarded_bodies = [
                    body for body in raw_bodies
                    if not self._is_relevant_body(body)
                ]
                diagnostics.update({
                    "status": "OK",
                    "raw_body_count": len(raw_bodies),
                    "relevant_body_count": len(relevant_bodies),
                    "discarded_body_count": len(discarded_bodies),
                    "discarded_sample": [
                        self._body_debug_summary(body)
                        for body in discarded_bodies[:5]
                    ],
                    "model_count": model_diagnostics.get("model_count", 0),
                    "selected_model_index": model_diagnostics.get("selected_model_index", 0),
                    "model_summaries": model_diagnostics.get("models", []),
                })
            except Exception as e:
                diagnostics.update({
                    "status": "ERROR",
                    "error": str(e),
                })
            self._body_extraction_diagnostics = diagnostics
        return dict(self._body_extraction_diagnostics)

    def get_surfaces(self, body: Any) -> List[Any]:
        """Return all surfaces for one VE body through ``VEBody.get_surfaces``."""
        body_id = self.get_object_id(body)
        if body_id not in self._surfaces:
            try:
                self._surfaces[body_id] = self._as_list(body.get_surfaces())
            except Exception as e:
                logger.error("Error while retrieving surfaces for body %s: %s", body_id, e)
                self._surfaces[body_id] = []
        return self._surfaces[body_id]

    def get_openings(self, surface: Any) -> List[Any]:
        """Return all openings for one VE surface through ``VESurface.get_openings``."""
        surface_id = self.get_object_id(surface)
        if surface_id not in self._openings:
            try:
                self._openings[surface_id] = self._as_list(surface.get_openings())
            except Exception as e:
                logger.error("Error while retrieving openings for surface %s: %s", surface_id, e)
                self._openings[surface_id] = []
        return self._openings[surface_id]

    def get_thermal_templates(self) -> Dict[str, Any]:
        """Return all thermal templates from the active VE project."""
        if not self._templates:
            try:
                templates = self.project.thermal_templates(assigned=False)
                self._templates = self._as_dict(templates)
            except Exception as e:
                logger.error("Error while retrieving thermal templates: %s", e)
                self._templates = {}
        return self._templates

    def get_profiles(self) -> Dict[str, Any]:
        """Return daily and group profiles indexed by their VE identifiers."""
        if self._profiles is not None:
            return dict(self._profiles)
        profiles: Dict[str, Any] = {}
        try:
            daily_profiles, group_profiles = self.project.profiles()
            for mapping in (self._as_dict(daily_profiles), self._as_dict(group_profiles)):
                for key, profile in mapping.items():
                    profiles[str(key)] = profile
                    profile_id = self._safe_object_attr(profile, "id")
                    if profile_id not in (None, ""):
                        profiles[str(profile_id)] = profile
        except Exception as exc:
            logger.error("Error while retrieving VE profiles: %s", exc)
        self._profiles = profiles
        return dict(profiles)

    def get_profile_daily_equivalent_hours(self, profile_id: Any) -> Optional[float]:
        """Return conservative full-load hours for a representative profile day.

        Daily modulating profiles are integrated from their numeric points.
        Weekly/yearly groups use the maximum referenced day so cooling screening
        is conservative. Unsupported absolute, compact, formula-only, or freeform
        profiles remain ``None`` instead of being approximated.
        """
        key = str(profile_id or "").strip()
        if not key:
            return None
        # ``ON`` is the documented VE built-in constant profile identifier used
        # by profile-free gains and exchanges.  It is not returned by
        # ``VEProject.profiles()``, so resolve its physical 24-hour behaviour
        # explicitly instead of reporting a missing user profile.
        if key.upper() == "ON":
            return 24.0
        if key in self._profile_daily_hours:
            return self._profile_daily_hours[key]
        value = self._resolve_profile_daily_equivalent_hours(key, set())
        self._profile_daily_hours[key] = value
        return value

    def _resolve_profile_daily_equivalent_hours(self, profile_id: str, visited: set) -> Optional[float]:
        """Resolve one VE daily/group profile without following recursive loops."""
        if profile_id in visited:
            return None
        visited = set(visited)
        visited.add(profile_id)
        profile = self.get_profiles().get(profile_id)
        if profile is None:
            return None
        try:
            if hasattr(profile, "is_modulating") and not bool(profile.is_modulating()):
                return None
            data = profile.get_data()
            if hasattr(profile, "is_weekly") and profile.is_weekly():
                child_values = [
                    self._resolve_profile_daily_equivalent_hours(str(child), visited)
                    for child in self._as_list(data)
                ]
                numeric = [value for value in child_values if value is not None]
                return max(numeric) if numeric else None
            if hasattr(profile, "is_yearly") and profile.is_yearly():
                child_values = []
                for row in self._as_list(data):
                    if isinstance(row, (list, tuple)) and row:
                        child_values.append(
                            self._resolve_profile_daily_equivalent_hours(str(row[0]), visited)
                        )
                numeric = [value for value in child_values if value is not None]
                return max(numeric) if numeric else None
            if (
                hasattr(profile, "is_compact")
                and profile.is_compact()
            ) or (
                hasattr(profile, "is_freeform")
                and profile.is_freeform()
            ):
                return None
            return self._integrate_daily_profile_points(data)
        except Exception:
            return None

    @staticmethod
    def _integrate_daily_profile_points(data: Any) -> Optional[float]:
        """Integrate numeric VE daily-profile points over a 24-hour day."""
        points = []
        for row in data if isinstance(data, (list, tuple)) else []:
            if not isinstance(row, (list, tuple)) or len(row) < 2:
                continue
            formula = str(row[2] or "").strip() if len(row) > 2 else ""
            # VE serializes the absence of a point formula as ``"-"``.  It is
            # metadata, not an executable formula, and must not make an
            # otherwise numeric daily profile non-resolvable.
            if formula not in {"", "-"}:
                return None
            try:
                hour = float(row[0])
                value = float(row[1])
            except (TypeError, ValueError):
                continue
            if 0.0 <= hour <= 24.0:
                points.append((hour, value))
        if not points:
            return None
        points = sorted(set(points))
        if points[0][0] > 0.0:
            points.insert(0, (0.0, points[0][1]))
        if points[-1][0] < 24.0:
            points.append((24.0, points[-1][1]))
        integral = 0.0
        for (start_hour, start_value), (end_hour, end_value) in zip(points, points[1:]):
            integral += (end_hour - start_hour) * (start_value + end_value) / 2.0
        return max(0.0, integral)

    def get_room_data(self, body: Any) -> Optional[Any]:
        """Return ``VERoomData`` for one body."""
        body_id = self.get_object_id(body)
        if body_id not in self._room_data_cache:
            try:
                self._room_data_cache[body_id] = body.get_room_data()
            except Exception as e:
                logger.error("Error while retrieving room data for body %s: %s", body_id, e)
                self._room_data_cache[body_id] = None
        return self._room_data_cache[body_id]

    def get_room_general(self, room_data: Any) -> Dict[str, Any]:
        """Return room identity, area and thermal-template assignment data."""
        try:
            return self._as_dict(room_data.get_general())
        except Exception as exc:
            logger.error("Error while retrieving room general data: %s", exc)
            return {}

    def get_internal_gains(self, room_data: Any) -> List[Any]:
        """Return room internal gains from ``VERoomData.get_internal_gains``."""
        try:
            return self._as_list(room_data.get_internal_gains())
        except Exception as e:
            logger.error("Error while retrieving internal gains: %s", e)
            return []

    def get_air_exchanges(self, room_data: Any) -> List[Any]:
        """Return room air exchanges from ``VERoomData.get_air_exchanges``."""
        try:
            return self._as_list(room_data.get_air_exchanges())
        except Exception as e:
            logger.error("Error while retrieving air exchanges: %s", e)
            return []

    def get_apache_systems(self, room_data: Any) -> Dict[str, Any]:
        """Return room Apache Systems / ApacheHVAC assignment data."""
        try:
            return self._as_dict(room_data.get_apache_systems())
        except Exception as e:
            logger.error("Error while retrieving Apache systems: %s", e)
            return {}

    def get_room_conditions(self, room_data: Any) -> Dict[str, Any]:
        """Return room condition data such as setpoints and humidity fields."""
        try:
            return self._as_dict(room_data.get_room_conditions())
        except Exception as e:
            logger.error("Error while retrieving room conditions: %s", e)
            return {}

    def get_weather_data(self) -> Optional[Any]:
        """Return project weather metadata through the documented ``VELocate`` API."""
        if self._weather_data is None:
            locator = None
            try:
                import importlib

                iesve = importlib.import_module("iesve")
                locator = iesve.VELocate()
                if locator.open_wea_data() != -1:
                    self._weather_data = self._as_dict(locator.get())
            except Exception as e:
                logger.error("Error while retrieving weather data: %s", e)
                self._weather_data = None
            finally:
                if locator is not None:
                    try:
                        locator.close_wea_data()
                    except Exception:
                        pass
        return self._weather_data

    def get_hvac_systems(self) -> Dict[str, Any]:
        """Return project-level Apache systems."""
        if not self._hvac_systems:
            try:
                raw_systems = self.project.apache_systems()
                if isinstance(raw_systems, dict):
                    iterable = list(raw_systems.items())
                else:
                    iterable = list(enumerate(self._as_list(raw_systems)))
                systems: Dict[str, Any] = {}
                for fallback_id, system in iterable:
                    system_id = self._safe_object_attr(system, "id")
                    system_name = self._safe_object_attr(system, "name")
                    key = str(system_id or system_name or fallback_id)
                    systems[key] = system
                self._hvac_systems = systems
            except Exception as e:
                logger.error("Error while retrieving HVAC systems: %s", e)
                self._hvac_systems = {}
        return self._hvac_systems

    def get_apache_system_data(self, system_id: Any) -> Dict[str, Any]:
        """Return documented Apache-system dictionaries for one assigned ID."""
        requested = str(system_id or "").strip().lower()
        if not requested:
            return {}
        selected = None
        for key, system in self.get_hvac_systems().items():
            candidates = {
                str(key).strip().lower(),
                str(self._safe_object_attr(system, "id") or "").strip().lower(),
                str(self._safe_object_attr(system, "name") or "").strip().lower(),
            }
            if requested in candidates:
                selected = system
                break
        if selected is None:
            return {}

        def call_dict(method_name: str) -> Dict[str, Any]:
            """Call one zero-argument Apache-system method as a dictionary."""
            try:
                method = getattr(selected, method_name)
                return self._as_dict(method())
            except Exception:
                return {}

        return {
            "id": str(self._safe_object_attr(selected, "id") or system_id),
            "name": str(self._safe_object_attr(selected, "name") or ""),
            "heating": call_dict("heating"),
            "heating_ncm": call_dict("heating_ncm"),
            "cooling": call_dict("cooling"),
            "cooling_ncm": call_dict("cooling_ncm"),
            "ventilation_ncm": call_dict("ventilation_ncm"),
            "air_supply": call_dict("air_supply"),
            "control": call_dict("control"),
            "general_ncm": call_dict("general_ncm"),
            "system_controls_ncm": call_dict("system_controls_ncm"),
        }

    def get_room_zone_membership(self) -> Dict[str, Dict[str, Any]]:
        """Return documented RoomGroups HVAC-zone membership by room ID."""
        if self._room_zone_membership is not None:
            return dict(self._room_zone_membership)
        membership: Dict[str, Dict[str, Any]] = {}
        try:
            import importlib

            iesve = importlib.import_module("iesve")
            room_groups = iesve.RoomGroups()
            for zone_group in self._as_list(room_groups.get_zone_groups()):
                zone_group_id = str((zone_group or {}).get("id") or "")
                if not zone_group_id:
                    continue
                for zone in self._as_list(room_groups.get_zones(zone_group_id)):
                    zone_rooms = [str(room_id) for room_id in (zone or {}).get("rooms", [])]
                    for room_id in zone_rooms:
                        membership[room_id] = {
                            "zone_group_id": zone_group_id,
                            "zone_group_name": str((zone_group or {}).get("name") or ""),
                            "zone_id": str((zone or {}).get("id") or ""),
                            "zone_name": str((zone or {}).get("name") or ""),
                            "zone_room_count": len(zone_rooms),
                            "master_room": str((zone or {}).get("master_room") or ""),
                        }
        except Exception as exc:
            logger.info("RoomGroups HVAC-zone membership is unavailable: %s", exc)
        self._room_zone_membership = membership
        return dict(membership)

    def get_macroflo_openings(self) -> Dict[str, Dict[str, Any]]:
        """Return MacroFlo opening definitions indexed by reference ID."""
        if self._macroflo_openings is not None:
            return dict(self._macroflo_openings)
        openings: Dict[str, Dict[str, Any]] = {}
        try:
            import importlib

            iesve = importlib.import_module("iesve")
            for row in self._as_list(iesve.VEMacroFlo().get()):
                if not isinstance(row, dict):
                    continue
                reference_id = str(row.get("reference_id") or "").strip()
                if reference_id:
                    openings[reference_id] = dict(row)
        except Exception as exc:
            logger.info("MacroFlo opening definitions are unavailable: %s", exc)
        self._macroflo_openings = openings
        return dict(openings)

    def get_energy_sources(self) -> Dict[str, Any]:
        """Return project energy sources through ``iesve.EnergySources``."""
        if not self._energy_sources:
            try:
                import importlib
                iesve = importlib.import_module("iesve")
                sources = iesve.EnergySources.get_all_energy_source_data()
                self._energy_sources = {
                    str(source.get("id", index)): source
                    for index, source in enumerate(self._as_list(sources))
                    if isinstance(source, dict)
                }
            except Exception as e:
                logger.error("Error while retrieving energy sources: %s", e)
                self._energy_sources = {}
        return self._energy_sources

    def get_body_areas(self, body: Any) -> Dict[str, float]:
        """Return room area and volume values through ``VEBody.get_areas``."""
        try:
            return self._as_dict(body.get_areas())
        except Exception as e:
            logger.error("Error while retrieving body areas for %s: %s", self.get_object_id(body), e)
            return {}

    def get_surface_properties(self, surface: Any) -> Dict[str, Any]:
        """Return normalized surface properties without assuming a dict return type."""
        try:
            props = self._safe_properties(surface)
            construction_ids = self.get_constructions(surface)
            areas = self.get_surface_areas(surface)
            surface_type = self._safe_lookup(props, "type") or self._get_surface_type(surface)
            construction_props = self._select_surface_construction_properties(
                construction_ids,
                surface_type,
                areas,
            )
            area = self._safe_lookup(props, "area")
            if area is None:
                area = self._safe_lookup(areas, "total_gross") or self._safe_lookup(areas, "total_net")
            return {
                "area": area,
                "U-value": (
                    self._find_first_present(props, ("U-value", "u_value", "u", "u-value"))
                    or self._extract_u_value(construction_props)
                ),
                "orientation": self._safe_lookup(props, "orientation"),
                "tilt": self._safe_lookup(props, "tilt"),
                "type": surface_type,
                "materials": self._safe_lookup(props, "materials") or construction_props.get("materials", []) or [],
                "construction_ids": construction_ids,
                "construction_properties": construction_props,
            }
        except Exception as e:
            logger.error("Error while retrieving surface properties for %s: %s", self.get_surface_id(surface), e)
            return {}

    def get_opening_properties(self, opening: Any) -> Dict[str, Any]:
        """Return normalized opening properties and audited glazing values."""
        try:
            props = self._safe_properties(opening)
            construction_id = self.get_opening_construction(opening)
            construction_props = self.get_construction_properties(construction_id) if construction_id else {}
            g_audit = self._extract_g_value_audit(props, construction_props)
            g_total_audit = self._extract_g_total_audit(props, construction_props)
            return {
                "area": self._safe_lookup(props, "area"),
                "U-value": (
                    self._find_first_present(props, ("U-value", "u_value", "u", "u-value"))
                    or self._extract_u_value(construction_props)
                ),
                "solar_factor": g_audit["selected_sia_g_value"],
                "solar_factor_source": g_audit["selected_source"],
                "cdb_g_value": g_audit["cdb_g_value"],
                "g_value_bs_en_410": g_audit["bs_en_410"],
                "g_value_building_regulations": g_audit["building_regulations"],
                "g_value_bfrc": g_audit["bfrc"],
                "g_values": g_audit["g_values"],
                "visible_transmittance": self._extract_visible_transmittance(props, construction_props),
                "frame_fraction": self._extract_frame_fraction(props, construction_props),
                "shading_type": self._extract_shading_type(props, construction_props),
                "shading_control": self._extract_shading_control(props, construction_props),
                "shading_properties": self._extract_shading_properties(props, construction_props),
                "g_total": g_total_audit["value"],
                "g_total_source": g_total_audit["source"],
                "orientation": self._safe_lookup(props, "orientation"),
                "type": self._safe_lookup(props, "type") or self._get_opening_type(opening),
                "macroflo_id": self._safe_object_attr(opening, "get_macroflo_id"),
                "construction_id": construction_id,
                "construction_properties": construction_props,
            }
        except Exception as e:
            logger.error("Error while retrieving opening properties for %s: %s", self.get_surface_id(opening), e)
            return {}

    def get_surface_areas(self, surface: Any) -> Dict[str, float]:
        """Return documented surface areas through ``VESurface.get_areas``."""
        try:
            return self._as_dict(surface.get_areas())
        except Exception as e:
            logger.error("Error while retrieving surface areas for %s: %s", self.get_surface_id(surface), e)
            return {}

    def get_adjacencies(self, surface: Any) -> List[Any]:
        """Return surface adjacencies through ``VESurface.get_adjacencies``."""
        try:
            return self._as_list(surface.get_adjacencies())
        except Exception as e:
            logger.error("Error while retrieving adjacencies for surface %s: %s", self.get_surface_id(surface), e)
            return []

    def get_constructions(self, surface: Any) -> List[str]:
        """Return construction IDs assigned to one surface."""
        try:
            return self._as_list(surface.get_constructions())
        except Exception as e:
            logger.error("Error while retrieving constructions for surface %s: %s", self.get_surface_id(surface), e)
            return []

    def get_opening_construction(self, opening: Any) -> str:
        """Return the construction ID assigned to one ``VEGeometry`` opening."""
        try:
            construction_id = opening.get_construction()
            return str(construction_id or "")
        except Exception:
            return ""

    def get_construction_properties(self, construction_id: Any) -> Dict[str, Any]:
        """Resolve thermal/CDB properties for one construction ID."""
        construction_key = str(construction_id or "").strip()
        if not construction_key:
            return {}
        if construction_key not in self._construction_properties:
            self._construction_properties[construction_key] = self._resolve_construction_properties(construction_key)
        return self._construction_properties[construction_key]

    def _resolve_construction_properties(self, construction_id: str) -> Dict[str, Any]:
        """Query ``VECdbConstruction`` using multiple classes for VE compatibility."""
        try:
            import importlib
            iesve = importlib.import_module("iesve")
        except Exception as e:
            logger.debug("iesve is unavailable while resolving construction %s: %s", construction_id, e)
            return {}

        construction_classes = self._get_cdb_construction_classes(iesve)
        construction_classes.append(None)

        for cdb_project in self._get_cdb_projects():
            for construction_class in construction_classes:
                construction = self._safe_get_cdb_construction(cdb_project, construction_id, construction_class)
                if construction is None:
                    continue
                return self._read_cdb_construction(construction, construction_id)
        return {}

    def _get_cdb_projects(self) -> List[Any]:
        """Return CDB projects available in the current VE construction database."""
        if self._cdb_projects is not None:
            return self._cdb_projects

        projects: List[Any] = []
        try:
            import importlib
            iesve = importlib.import_module("iesve")
            database = iesve.VECdbDatabase.get_current_database()
            raw_projects = database.get_projects()
            projects = self._collect_cdb_project_objects(raw_projects)
        except Exception as e:
            logger.debug("Could not access CDB projects: %s", e)

        self._cdb_projects = projects
        return self._cdb_projects

    @staticmethod
    def _get_cdb_construction_classes(iesve_module: Any) -> List[Any]:
        """Collect construction-class enum values exposed by IESVE versions."""
        construction_classes = []
        enum_candidates = []
        for owner_name in ("VECdbProject", "VECdbConstruction", ""):
            owner = iesve_module if owner_name == "" else getattr(iesve_module, owner_name, None)
            if owner is None:
                continue
            for enum_name in (
                "construction_class",
                "construction_classes",
                "eConstructionClass",
                "ConstructionClass",
                "constructionClass",
            ):
                enum = getattr(owner, enum_name, None)
                if enum is not None:
                    enum_candidates.append(enum)

        for owner_name in ("VECdbProject", "VECdbConstruction", ""):
            owner = iesve_module if owner_name == "" else getattr(iesve_module, owner_name, None)
            if owner is None:
                continue
            for attr_name in dir(owner):
                lowered = attr_name.lower()
                if "construction" in lowered and "class" in lowered:
                    enum = getattr(owner, attr_name, None)
                    if enum is not None:
                        enum_candidates.append(enum)

        seen = set()
        for enum in enum_candidates:
            for name in ("none", "opaque", "glazed", "hard_landscaping", "soft_landscaping", "shade", "misc"):
                value = getattr(enum, name, None)
                marker = repr(value)
                if value is not None and marker not in seen:
                    construction_classes.append(value)
                    seen.add(marker)
            if isinstance(enum, dict):
                for value in enum.values():
                    marker = repr(value)
                    if value is not None and marker not in seen:
                        construction_classes.append(value)
                        seen.add(marker)

        # Some VE Python bindings do not expose enum containers but still accept
        # the underlying integer enum values in Boost.Python calls.
        for fallback_value in range(0, 8):
            marker = repr(fallback_value)
            if marker not in seen:
                construction_classes.append(fallback_value)
                seen.add(marker)
        return construction_classes

    @classmethod
    def _collect_cdb_project_objects(cls, value: Any) -> List[Any]:
        """Recursively walk ``get_projects()`` output and retain CDB projects."""
        projects: List[Any] = []
        seen: set = set()

        def visit(item: Any, depth: int = 0) -> None:
            """Visit nested project containers without looping on repeated objects."""
            if item is None or depth > 6:
                return
            marker = id(item)
            if marker in seen:
                return
            seen.add(marker)

            if hasattr(item, "get_construction"):
                projects.append(item)
                return

            if isinstance(item, dict):
                for nested in item.values():
                    visit(nested, depth + 1)
                return

            if isinstance(item, (list, tuple, set)):
                for nested in item:
                    visit(nested, depth + 1)
                return

        visit(value)
        return projects

    @staticmethod
    def _safe_get_cdb_construction(cdb_project: Any, construction_id: str, construction_class: Any) -> Optional[Any]:
        """Return a CDB construction while tolerating VE binding signature variants."""
        try:
            if construction_class is None:
                return cdb_project.get_construction(construction_id)
            return cdb_project.get_construction(construction_id, construction_class)
        except Exception:
            return None

    def _read_cdb_construction(self, construction: Any, construction_id: str) -> Dict[str, Any]:
        """Extract normalized construction, U-value, g-value, and layer metadata."""
        props: Dict[str, Any] = {
            "id": construction_id,
            "reference": self._safe_object_attr(construction, "reference"),
            "category": self._safe_object_attr(construction, "category"),
            "opaque": self._safe_object_attr(construction, "opaque"),
        }

        raw_props = self._read_construction_properties_variants(construction)
        if raw_props:
            props.update(raw_props)

        try:
            props["g_values"] = self._as_dict(construction.get_g_values())
        except Exception:
            props["g_values"] = {}

        u_values: Dict[str, Any] = {}
        try:
            import importlib
            iesve = importlib.import_module("iesve")
            uvalue_types = self._get_cdb_uvalue_types(iesve)
            for name, value in uvalue_types:
                try:
                    u_values[name] = construction.get_u_factor(value)
                except Exception:
                    pass
        except Exception:
            pass
        if u_values:
            props["u_factors"] = u_values

        try:
            layers = construction.get_layers()
            props["layers"] = [self._read_cdb_layer(layer) for layer in self._as_list(layers)]
            if props["layers"]:
                props["materials"] = [
                    layer.get("material")
                    for layer in props["layers"]
                    if layer.get("material")
                ]
        except Exception:
            props.setdefault("layers", [])

        return props

    def _read_construction_properties_variants(self, construction: Any) -> Dict[str, Any]:
        """Read construction properties with every known VE/CDB overload."""
        try:
            props = self._as_dict(construction.get_properties())
            if props:
                return props
        except Exception:
            pass

        try:
            import importlib
            iesve = importlib.import_module("iesve")
            uvalue_types = self._get_cdb_uvalue_types(iesve)
            for name, value in uvalue_types:
                try:
                    props = self._as_dict(construction.get_properties(value))
                    if props:
                        return props
                except Exception:
                    continue
        except Exception:
            pass
        return {}

    @staticmethod
    def _get_cdb_uvalue_types(iesve_module: Any) -> List[Any]:
        """Collect CDB U-value enum values, with numeric fallbacks for VE builds."""
        typed_values = []
        seen = set()
        enum_candidates = []
        for owner_name in ("VECdbConstruction", "VECdbProject", ""):
            owner = iesve_module if owner_name == "" else getattr(iesve_module, owner_name, None)
            if owner is None:
                continue
            for enum_name in ("uvalue_types", "u_value_types", "UValueTypes", "eUValueTypes"):
                enum = getattr(owner, enum_name, None)
                if enum is not None:
                    enum_candidates.append(enum)
            for attr_name in dir(owner):
                lowered = attr_name.lower()
                if "uvalue" in lowered or "u_value" in lowered:
                    enum = getattr(owner, attr_name, None)
                    if enum is not None:
                        enum_candidates.append(enum)

        for enum in enum_candidates:
            for name in ("iso", "cibse", "ashae", "ashrae", "t24"):
                value = getattr(enum, name, None)
                marker = repr(value)
                if value is not None and marker not in seen:
                    typed_values.append((name, value))
                    seen.add(marker)
            if isinstance(enum, dict):
                for name, value in enum.items():
                    marker = repr(value)
                    if value is not None and marker not in seen:
                        typed_values.append((str(name), value))
                        seen.add(marker)

        for fallback_value in range(0, 6):
            marker = repr(fallback_value)
            if marker not in seen:
                typed_values.append((f"enum_{fallback_value}", fallback_value))
                seen.add(marker)
        return typed_values

    def _read_cdb_layer(self, layer: Any) -> Dict[str, Any]:
        """Read one CDB construction layer and its material reference when available."""
        layer_props = {}
        try:
            layer_props = self._as_dict(layer.get_properties())
        except Exception:
            layer_props = {}
        for is_opaque in (True, False):
            try:
                material = layer.get_material(is_opaque=is_opaque)
                if material:
                    layer_props["material"] = material
                    break
            except Exception:
                continue
        return layer_props

    def _first_resolved_construction(self, construction_ids: List[Any]) -> Dict[str, Any]:
        """Return the first construction ID that resolves to non-empty CDB data."""
        for construction_id in construction_ids:
            props = self.get_construction_properties(construction_id)
            if props:
                return props
        return {}

    def _select_surface_construction_properties(
        self,
        construction_ids: List[Any],
        surface_type: Any,
        areas: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Select the construction relevant to the opaque parent surface.

        VE surfaces can list both the opaque construction and constructions for
        embedded glazing. For wall/roof/floor checks, use the opaque parent
        construction; openings are handled separately via VEGeometry.
        """
        resolved = [
            self.get_construction_properties(construction_id)
            for construction_id in construction_ids
        ]
        resolved = [props for props in resolved if props]
        if not resolved:
            return {}

        normalized_type = self._normalize_surface_type(surface_type)
        external_net = self._to_float_or_none((areas or {}).get("external_net"))
        total_net = self._to_float_or_none((areas or {}).get("total_net"))
        net_area = external_net if external_net is not None else total_net

        if normalized_type in {"wall", "roof", "floor", "ceiling", "partition"}:
            opaque = [props for props in resolved if props.get("opaque") is True]
            exact_category = [
                props
                for props in opaque
                if self._normalize_surface_type(props.get("category")) == normalized_type
            ]
            if exact_category:
                return exact_category[0]

            # A VE parent surface may list its openings before its own opaque
            # construction (for example DOOR, EXTW5, WALL).  Never use a door
            # or glazed-opening construction as the U-value of the opaque
            # wall/roof/floor merely because it appears first.
            non_opening_opaque = [
                props
                for props in opaque
                if self._normalize_surface_type(props.get("category"))
                not in {"door", "glazing", "window"}
            ]
            if non_opening_opaque:
                return non_opening_opaque[0]
            if opaque:
                return opaque[0]
            if net_area is not None and net_area <= 1e-6:
                return {}

        if normalized_type in {"glazing", "window"}:
            glazed = [props for props in resolved if props.get("opaque") is False]
            if glazed:
                return glazed[0]

        return resolved[0]

    def get_object_id(self, obj: Any) -> str:
        """Return a stable VE object ID across documented and observed API shapes."""
        if obj is None:
            return ""
        try:
            for method_name in ("get_id", "id"):
                method = getattr(obj, method_name, None)
                if callable(method):
                    value = method()
                    if value not in (None, ""):
                        return str(value)
            obj_id = getattr(obj, "id", None)
            if callable(obj_id):
                return str(obj_id())
            if obj_id is not None:
                return str(obj_id)
        except Exception:
            pass
        return str(id(obj))

    def get_surface_id(self, surface: Any) -> str:
        """Compatibility alias for historical project calls."""
        return self.get_object_id(surface)

    @staticmethod
    def _normalize_enum_name(value: Any) -> str:
        """Normalize an IESVE enum or callable enum attribute to a plain string."""
        if value is None:
            return ""
        if callable(value):
            try:
                value = value()
            except Exception:
                return ""
        text = str(value).strip().lower()
        if "." in text:
            text = text.split(".")[-1]
        return text.replace(" ", "_").replace("-", "_")

    def _is_relevant_body(self, body: Any) -> bool:
        """Return true when a VE body represents a usable thermal room."""
        body_type = self._normalize_enum_name(getattr(body, "type", None))
        subtype = self._normalize_enum_name(getattr(body, "subtype", None))
        if body_type != "room":
            return False
        return subtype in {"", "room", "void", "ra_plenum", "sa_plenum"}

    def _body_debug_summary(self, body: Any) -> Dict[str, str]:
        """Return a compact body summary for extraction troubleshooting."""
        try:
            props = self._safe_properties(body)
        except Exception:
            props = {}
        name = (
            self._safe_lookup(props, "name")
            or self._safe_lookup(props, "room_name")
            or getattr(body, "name", "")
        )
        if callable(name):
            try:
                name = name()
            except Exception:
                name = ""
        return {
            "id": self.get_object_id(body),
            "name": str(name or ""),
            "type": self._normalize_enum_name(getattr(body, "type", None)),
            "subtype": self._normalize_enum_name(getattr(body, "subtype", None)),
        }

    def _get_surface_type(self, surface: Any) -> str:
        """Extract and normalize the type of a ``VESurface`` object."""
        try:
            props = self._safe_properties(surface)
            surface_type = self._safe_lookup(props, "type") or getattr(surface, "type", None)
        except Exception:
            surface_type = getattr(surface, "type", None)
        return self._normalize_surface_type(surface_type)

    def _get_opening_type(self, opening: Any) -> str:
        """Extract and normalize the type of a ``VEGeometry`` opening."""
        try:
            props = self._safe_properties(opening)
            opening_type = self._safe_lookup(props, "type") or getattr(opening, "type", None)
        except Exception:
            opening_type = getattr(opening, "type", None)
        return self._normalize_opening_type(opening_type)

    @staticmethod
    def _normalize_surface_type(surface_type: Any) -> str:
        """Normalize IESVE surface-type values to reusable compliance labels."""
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
        if raw in {"wall", "roof", "floor", "ceiling", "glazing", "door", "hole"}:
            return raw
        return raw

    @staticmethod
    def _normalize_opening_type(opening_type: Any) -> str:
        """Normalize IESVE opening-type values to reusable compliance labels."""
        if opening_type in (4, "4"):
            return "window"
        if opening_type in (5, "5", 6, "6"):
            return "door"
        if opening_type in (11, "11"):
            return "hole"
        normalized = VEDataExtractor._normalize_surface_type(opening_type)
        if normalized in {"glazing", "window"}:
            return "window"
        if normalized in {"door"}:
            return "door"
        return normalized

    @staticmethod
    def _safe_lookup(mapping: Any, key: str) -> Any:
        """Read a field safely from dictionaries or VE proxy objects."""
        if isinstance(mapping, dict):
            return mapping.get(key)
        if mapping is None:
            return None
        try:
            return getattr(mapping, key)
        except Exception:
            return None

    @classmethod
    def _find_first_present(cls, mapping: Any, keys: Any) -> Any:
        """Return the first non-empty value found through possible key aliases."""
        for key in keys:
            value = cls._safe_lookup(mapping, key)
            if value not in (None, ""):
                return value
        if isinstance(mapping, dict):
            normalized = {str(k).strip().lower().replace("_", "-"): v for k, v in mapping.items()}
            for key in keys:
                value = normalized.get(str(key).strip().lower().replace("_", "-"))
                if value not in (None, ""):
                    return value
        return None

    @classmethod
    def _extract_u_value(cls, construction_props: Dict[str, Any]) -> Optional[float]:
        """Extract a construction U-value from normalized CDB properties."""
        direct = cls._find_first_present(
            construction_props,
            (
                "U-value",
                "u_value",
                "u-value",
                "u",
                "u_factor",
                "u-factor",
                "thermal_transmittance",
            ),
        )
        numeric = cls._to_float_or_none(direct)
        if numeric is not None:
            return numeric

        u_factors = construction_props.get("u_factors")
        if isinstance(u_factors, dict):
            for preferred in ("iso", "cibse", "ashae", "ashrae", "t24"):
                numeric = cls._to_float_or_none(u_factors.get(preferred))
                if numeric is not None:
                    return numeric
            for value in u_factors.values():
                numeric = cls._to_float_or_none(value)
                if numeric is not None:
                    return numeric
        return None

    @classmethod
    def _extract_g_value(cls, construction_props: Dict[str, Any]) -> Optional[float]:
        """Extract the SIA-comparable glazing solar factor when auditable."""
        return cls._extract_g_value_audit(construction_props).get("selected_sia_g_value")

    @classmethod
    def _extract_g_value_audit(cls, *mappings: Any) -> Dict[str, Any]:
        """Return audited VE g-values and the value selected for SIA comparison.

        VEScripts documents VECdbConstruction.get_g_values() entries as
        bs_en_410, building_regulations and bfrc. For SIA readiness, the EN 410
        value is the only automatically comparable g_perp candidate. Other VE
        values remain visible in the audit trail but do not generate a SIA pass
        without reviewer/manufacturer evidence.
        """
        normalized_g_values = cls._collect_normalized_g_values(*mappings)
        cdb_key, cdb_raw = cls._first_present_from_mappings(
            mappings,
            (
                "g_value",
                "g-value",
                "solar_factor",
                "solar_transmittance",
                "total_solar_energy_transmittance",
            ),
        )
        cdb_g_value = cls._normalize_unit_fraction(cls._to_float_or_none(cdb_raw))

        selected_value = normalized_g_values.get("bs_en_410")
        selected_source = (
            "VECdbConstruction.get_g_values().bs_en_410"
            if selected_value is not None
            else ""
        )

        fallback_candidates = (
            (cdb_g_value, f"VECdbConstruction.get_properties().{cdb_key or 'g_value'}"),
            (normalized_g_values.get("building_regulations"), "VECdbConstruction.get_g_values().building_regulations"),
            (normalized_g_values.get("bfrc"), "VECdbConstruction.get_g_values().bfrc"),
        )
        fallback_value: Optional[float] = None
        fallback_source = ""
        for value, source in fallback_candidates:
            if value is not None:
                fallback_value = value
                fallback_source = source
                break

        return {
            "selected_sia_g_value": selected_value,
            "selected_source": selected_source,
            "fallback_g_value": fallback_value,
            "fallback_source": fallback_source,
            "cdb_g_value": cdb_g_value,
            "bs_en_410": normalized_g_values.get("bs_en_410"),
            "building_regulations": normalized_g_values.get("building_regulations"),
            "bfrc": normalized_g_values.get("bfrc"),
            "g_values": normalized_g_values,
        }

    @classmethod
    def _collect_normalized_g_values(cls, *mappings: Any) -> Dict[str, float]:
        """Collect and normalize VECdbConstruction.get_g_values() output."""
        values: Dict[str, float] = {}
        aliases = {
            "bs_en_410": ("bs_en_410", "bs-en-410", "bs en 410", "en_410", "en-410", "en 410"),
            "building_regulations": (
                "building_regulations",
                "building-regulations",
                "building regulations",
                "building_regs",
                "building-regs",
            ),
            "bfrc": ("bfrc",),
        }
        for mapping in mappings:
            if not isinstance(mapping, dict):
                continue
            raw = mapping.get("g_values")
            if not isinstance(raw, dict):
                continue
            normalized_lookup = {
                str(key).strip().lower().replace("_", "-").replace(" ", "-"): value
                for key, value in raw.items()
            }
            for canonical, keys in aliases.items():
                if canonical in values:
                    continue
                for key in keys:
                    lookup_key = key.strip().lower().replace("_", "-").replace(" ", "-")
                    value = normalized_lookup.get(lookup_key)
                    numeric = cls._normalize_unit_fraction(cls._to_float_or_none(value))
                    if numeric is not None:
                        values[canonical] = numeric
                        break
        return values

    @classmethod
    def _extract_visible_transmittance(cls, *mappings: Any) -> Optional[float]:
        """Read visible transmittance aliases exposed by VE/CDB glazing data."""
        value = cls._first_numeric_from_mappings(
            mappings,
            (
                "visible_transmittance",
                "visible_light_transmittance",
                "light_transmittance",
                "transmission_lumineuse",
                "tau_v",
                "tau",
                "tvis",
                "vt",
            ),
        )
        return cls._normalize_unit_fraction(value)

    @classmethod
    def _extract_frame_fraction(cls, *mappings: Any) -> Optional[float]:
        """Read and normalize frame fraction from VE CDB fields."""
        for mapping in mappings:
            key, value = cls._find_first_present_with_key(
                mapping,
                (
                    "frame_fraction",
                    "frame-factor",
                    "frame_factor",
                    "frame_percent",
                    "frame_inside_surface_area_ratio",
                    "frame_outside_surface_area_ratio",
                    "ff",
                ),
            )
            numeric = cls._to_float_or_none(value)
            if numeric is None:
                continue
            if "percent" in str(key).lower() or numeric > 1.0:
                numeric = numeric / 100.0
            return numeric
        return None

    @classmethod
    def _extract_shading_type(cls, *mappings: Any) -> Optional[str]:
        """Read shading/protection type from VE CDB construction fields."""
        direct = cls._first_text_from_mappings(
            mappings,
            (
                "shading_type",
                "solar_protection",
                "blind_type",
                "shade_type",
                "external_shade_code",
                "internal_shade_code",
                "internal_shade_blind_or_curtain",
                "local_shade_code",
                "local_shade_overhang_type",
            ),
        )
        descriptions: List[str] = []
        for mapping in mappings:
            descriptions.extend(cls._active_shade_descriptions(mapping))
        if descriptions:
            return direct if direct and not cls._is_no_shading_label(direct) else "; ".join(descriptions)
        if any(cls._has_explicit_no_shading(mapping) for mapping in mappings):
            return "none declared in CDB"
        if direct and not cls._is_no_shading_label(direct):
            return direct
        return None

    @classmethod
    def _extract_shading_control(cls, *mappings: Any) -> Optional[str]:
        """Read shading control/profile data from VE CDB construction fields."""
        active_descriptions = [
            description
            for mapping in mappings
            for description in cls._active_shade_descriptions(mapping)
        ]
        if not active_descriptions and any(
            cls._has_explicit_no_shading(mapping) for mapping in mappings
        ):
            return "none declared in CDB"

        direct = cls._first_text_from_mappings(
            mappings,
            (
                "shading_control",
                "blind_control",
                "solar_protection_control",
                "external_shade_profile",
                "internal_shade_profile",
            ),
        )
        control_parts = [direct] if direct and not cls._is_no_shading_label(direct) else []

        for mapping in mappings:
            for key in (
                "external_shade_radiation_to_raise",
                "external_shade_radiation_to_lower",
                "internal_shade_radiation_to_raise",
                "internal_shade_radiation_to_lower",
                "internal_shade_frac_daylight_closed",
            ):
                value = cls._safe_lookup(mapping, key)
                if value not in (None, ""):
                    control_parts.append(f"{key}={value}")

        if control_parts:
            return "; ".join(str(item) for item in control_parts if item)
        return None

    @classmethod
    def _extract_shading_properties(cls, *mappings: Any) -> Dict[str, Any]:
        """Collect documented VE CDB shade fields for audit/reporting."""
        shade_keys = (
            "external_shade_active",
            "external_shade_code",
            "external_shade_day_resistance",
            "external_shade_ground_transmittance",
            "external_shade_ground_transmittance_default",
            "external_shade_night_resistance",
            "external_shade_profile",
            "external_shade_radiation_to_lower",
            "external_shade_radiation_to_raise",
            "external_shade_sky_transmittance",
            "external_shade_sky_transmittance_default",
            "external_shade_transmitance_15",
            "external_shade_transmitance_75",
            "external_shade_transmittance_0",
            "external_shade_transmittance_15",
            "external_shade_transmittance_30",
            "external_shade_transmittance_45",
            "external_shade_transmittance_60",
            "external_shade_transmittance_75",
            "external_shade_transmittance_90",
            "internal_shade_active",
            "internal_shade_blind_or_curtain",
            "internal_shade_code",
            "internal_shade_day_resistance",
            "internal_shade_frac_daylight_closed",
            "internal_shade_night_resistance",
            "internal_shade_profile",
            "internal_shade_radiation_to_lower",
            "internal_shade_radiation_to_raise",
            "internal_shade_shading_coefficient",
            "internal_shade_short_wave_radiant_fraction",
            "local_shade_active",
            "local_shade_balcony_depth_h",
            "local_shade_balcony_height",
            "local_shade_balcony_projection",
            "local_shade_code",
            "local_shade_left_fin_offset",
            "local_shade_left_fin_projection",
            "local_shade_overhang_type",
            "local_shade_projection_offset",
            "local_shade_projection_overhang",
            "local_shade_right_fin_offset",
            "local_shade_right_fin_projection",
            "local_shade_window_height",
            "local_shade_window_width",
            "percent_sky_blocked",
        )
        collected: Dict[str, Any] = {}
        for key in shade_keys:
            _, value = cls._first_present_from_mappings(mappings, (key,))
            if value not in (None, ""):
                collected[key] = value
        return collected

    @classmethod
    def _extract_g_total(cls, *mappings: Any) -> Optional[float]:
        """Read effective glazing-plus-shading g-value when VE exposes it."""
        return cls._extract_g_total_audit(*mappings).get("value")

    @classmethod
    def _extract_g_total_audit(cls, *mappings: Any) -> Dict[str, Any]:
        """Read direct effective glazing-plus-shading g-value aliases if present.

        VEScripts does not document a direct g_total field for VECdbConstruction,
        so any value found here is reported with its raw field name for review.
        """
        key, raw_value = cls._first_numeric_with_key_from_mappings(
            mappings,
            (
                "g_total",
                "total_g_value",
                "glazing_shading_g_value",
                "combined_g_value",
                "effective_g_value",
                "shaded_g_value",
                "g_value_with_shading",
            ),
        )
        value = cls._normalize_unit_fraction(raw_value)
        return {
            "value": value,
            "source": f"undocumented VE field: {key}" if value is not None and key else "",
        }

    @classmethod
    def _first_numeric_with_key_from_mappings(cls, mappings: Any, keys: Any) -> Any:
        """Return the first numeric alias match and the key that supplied it."""
        for mapping in mappings:
            key, value = cls._find_first_present_with_key(mapping, keys)
            numeric = cls._to_float_or_none(value)
            if numeric is not None:
                return key, numeric
            if isinstance(mapping, dict):
                for layer in mapping.get("layers", []) or []:
                    key, value = cls._find_first_present_with_key(layer, keys)
                    numeric = cls._to_float_or_none(value)
                    if numeric is not None:
                        return key, numeric
        return "", None

    @classmethod
    def _first_present_from_mappings(cls, mappings: Any, keys: Any) -> Any:
        """Return the first non-empty alias match from several mappings."""
        for mapping in mappings:
            key, value = cls._find_first_present_with_key(mapping, keys)
            if value not in (None, ""):
                return key, value
        return "", None

    @classmethod
    def _extract_g_total_legacy(cls, *mappings: Any) -> Optional[float]:
        """Backward-compatible alias kept for older internal callers."""
        value = cls._first_numeric_from_mappings(
            mappings,
            (
                "g_total",
                "total_g_value",
                "glazing_shading_g_value",
                "combined_g_value",
                "effective_g_value",
                "shaded_g_value",
                "g_value_with_shading",
            ),
        )
        return cls._normalize_unit_fraction(value)

    @classmethod
    def _first_numeric_from_mappings(cls, mappings: Any, keys: Any) -> Optional[float]:
        """Return the first numeric alias match, including nested layer mappings."""
        for mapping in mappings:
            _, value = cls._find_first_present_with_key(mapping, keys)
            numeric = cls._to_float_or_none(value)
            if numeric is not None:
                return numeric
            if isinstance(mapping, dict):
                for layer in mapping.get("layers", []) or []:
                    _, value = cls._find_first_present_with_key(layer, keys)
                    numeric = cls._to_float_or_none(value)
                    if numeric is not None:
                        return numeric
        return None

    @classmethod
    def _first_text_from_mappings(cls, mappings: Any, keys: Any) -> Optional[str]:
        """Return the first text alias match from several mappings."""
        for mapping in mappings:
            _, value = cls._find_first_present_with_key(mapping, keys)
            if value not in (None, ""):
                return str(value)
        return None

    @classmethod
    def _find_first_present_with_key(cls, mapping: Any, keys: Any) -> Any:
        """Return the first matching key/value while preserving the source key."""
        for key in keys:
            value = cls._safe_lookup(mapping, key)
            if value not in (None, ""):
                return key, value
        if isinstance(mapping, dict):
            normalized = {
                str(k).strip().lower().replace("_", "-"): (k, v)
                for k, v in mapping.items()
            }
            for key in keys:
                match = normalized.get(str(key).strip().lower().replace("_", "-"))
                if match and match[1] not in (None, ""):
                    return match
        return "", None

    @classmethod
    def _active_shade_descriptions(cls, mapping: Any) -> List[str]:
        """Build readable descriptions for active VE shading flags."""
        if not isinstance(mapping, dict):
            return []
        descriptions = []
        shade_groups = (
            ("external", "external_shade_active", ("external_shade_code", "external_shade_profile")),
            ("internal", "internal_shade_active", ("internal_shade_code", "internal_shade_blind_or_curtain", "internal_shade_profile")),
            ("local", "local_shade_active", ("local_shade_code", "local_shade_overhang_type")),
        )
        for label, active_key, detail_keys in shade_groups:
            if not cls._truthy(mapping.get(active_key)):
                continue
            details = [
                f"{key}={mapping.get(key)}"
                for key in detail_keys
                if mapping.get(key) not in (None, "")
            ]
            descriptions.append(f"{label} shade" + (f" ({', '.join(details)})" if details else ""))
        return descriptions

    @classmethod
    def _has_explicit_no_shading(cls, mapping: Any) -> bool:
        """Return true when VE exposes shade-active fields and all are disabled."""
        if not isinstance(mapping, dict):
            return False
        active_keys = ("external_shade_active", "internal_shade_active", "local_shade_active")
        present = [key for key in active_keys if key in mapping]
        return bool(present) and all(not cls._truthy(mapping.get(key)) for key in present)

    @staticmethod
    def _is_no_shading_label(value: Any) -> bool:
        """Return true for CDB labels that explicitly represent no active shade."""
        return str(value or "").strip().lower() in {
            "0",
            "false",
            "no",
            "none",
            "off",
            "disabled",
            "none declared in cdb",
        }

    @staticmethod
    def _normalize_unit_fraction(value: Optional[float]) -> Optional[float]:
        """Normalize percentage-like values into fractions when safe to do so."""
        if value is None:
            return None
        if value > 1.0 and value <= 100.0:
            return value / 100.0
        return value

    @staticmethod
    def _truthy(value: Any) -> bool:
        """Interpret VE boolean-like fields consistently."""
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value != 0
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y", "on", "active", "enabled"}
        return bool(value)

    @staticmethod
    def _to_float_or_none(value: Any) -> Optional[float]:
        """Convert VE values to float and return ``None`` when conversion fails."""
        try:
            if isinstance(value, str):
                normalized = value.strip().replace(" ", "")
                if "," in normalized and "." not in normalized:
                    normalized = normalized.replace(",", ".")
                return float(normalized)
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_object_attr(obj: Any, attribute_name: str) -> Any:
        """Read an object attribute or zero-argument callable attribute safely."""
        try:
            value = getattr(obj, attribute_name)
            if callable(value):
                return value()
            return value
        except Exception:
            return None

    @staticmethod
    def _safe_properties(obj: Any) -> Dict[str, Any]:
        """Extract VE object properties safely as a Python dictionary."""
        if obj is None:
            return {}
        try:
            if hasattr(obj, "get_properties"):
                props = obj.get_properties()
                return VEDataExtractor._as_dict(props)
        except Exception:
            pass
        return {}

    @staticmethod
    def _as_list(value: Any) -> List[Any]:
        """Normalize iterable VE return values to a Python list when possible."""
        if value is None:
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, (tuple, set)):
            return list(value)
        try:
            if not isinstance(value, (str, bytes)):
                return list(value)
        except Exception:
            pass
        return []

    @staticmethod
    def _as_dict(value: Any) -> Dict[str, Any]:
        """Normalize mapping-like VE return values to a Python dictionary."""
        if isinstance(value, dict):
            return value
        try:
            return dict(value)
        except Exception:
            return {}
