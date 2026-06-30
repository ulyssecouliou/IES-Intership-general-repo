"""
Extracteur de données du modèle VE via l'API IESVE.
Ce module centralise tous les appels à l'API IESVE et gère les erreurs.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

class VEDataExtractor:
    """
    Extrait toutes les données nécessaires du modèle VE pour le Swiss Compliance Checker.
    Utilise un cache pour éviter les appels redondants à l'API IESVE.
    """

    def __init__(self, project: Optional[Any] = None):
        """
        Initialise l'extracteur avec un projet VE.
        Si aucun projet n'est fourni, utilise le projet actif.
        """
        self.project = project
        if self.project is None:
            try:
                import importlib
                iesve = importlib.import_module("iesve")
                self.project = iesve.VEProject.get_current_project()
            except Exception:
                self.project = None

        if not self.project:
            raise RuntimeError("Aucun projet VE trouvé. Veuillez ouvrir un projet dans IESVE.")

        # Cache pour les données fréquemment utilisées
        self._model: Optional[Any] = None
        self._bodies: Dict[bool, List[Any]] = {}
        self._surfaces: Dict[str, List[Any]] = {}  # Clé: body_id, Valeur: liste de surfaces
        self._openings: Dict[str, List[Any]] = {}  # Clé: surface_id, Valeur: liste d'ouvertures
        self._templates: Dict[str, Any] = {}  # Clé: template_id, Valeur: VEThermalTemplate
        self._hvac_systems: Dict[str, Any] = {}
        self._energy_sources: Dict[str, Any] = {}
        self._construction_properties: Dict[str, Dict[str, Any]] = {}
        self._cdb_projects: Optional[List[Any]] = None
        self._weather_data: Optional[Any] = None
        self._body_extraction_diagnostics: Optional[Dict[str, Any]] = None
        self._model_selection_diagnostics: Optional[Dict[str, Any]] = None
        self._room_data_cache: Dict[str, Any] = {}  # Clé: body_id, Valeur: VERoomData

        logger.info("VEDataExtractor initialisé avec succès.")

    @property
    def model(self) -> Any:
        """Récupère le modèle VE (premier modèle du projet)."""
        if self._model is None:
            try:
                models = self._as_list(self.project.models)
                if models:
                    self._model = self._select_best_model(models)
                else:
                    raise RuntimeError("Aucun modèle trouvé dans le projet VE.")
            except Exception as e:
                logger.error(f"Erreur lors de la récupération du modèle VE: {e}")
                raise
        return self._model

    def _select_best_model(self, models: List[Any]) -> Any:
        """Select the VE model that exposes the most usable room bodies."""
        model_rows: List[Dict[str, Any]] = []
        best_model = models[0]
        best_score = (-1, -1)
        selected_index = 0

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
            score = (relevant_count, raw_count)
            if score > best_score:
                best_score = score
                best_model = model
                selected_index = index

            model_rows.append({
                "index": index,
                "model_type": self._normalize_enum_name(getattr(model, "model_type", None)),
                "raw_body_count": raw_count,
                "relevant_body_count": relevant_count,
                "error": error,
            })

        self._model_selection_diagnostics = {
            "model_count": len(models),
            "selected_model_index": selected_index,
            "models": model_rows,
        }
        if selected_index != 0:
            logger.info(
                "Selected VE model index %s because it exposes more room bodies than model 0.",
                selected_index,
            )
        return best_model

    def get_model_selection_diagnostics(self) -> Dict[str, Any]:
        """Return model-selection diagnostics for report preflight checks."""
        if self._model_selection_diagnostics is None:
            _ = self.model
        return dict(self._model_selection_diagnostics or {})

    def get_bodies(self, selected_only: bool = False) -> List[Any]:
        """
        Récupère toutes les pièces (bodies) du modèle VE.
        Filtre les éléments non pertinents (ombres, annotations, etc.).
        """
        if selected_only not in self._bodies:
            try:
                all_bodies = self._as_list(self.model.get_bodies(selected_only))
                self._bodies[selected_only] = [
                    body for body in all_bodies
                    if self._is_relevant_body(body)
                ]
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des pièces: {e}")
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
        """
        Récupère toutes les surfaces d'une pièce.
        """
        body_id = self.get_object_id(body)
        if body_id not in self._surfaces:
            try:
                self._surfaces[body_id] = self._as_list(body.get_surfaces())
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des surfaces pour la pièce {body_id}: {e}")
                self._surfaces[body_id] = []
        return self._surfaces[body_id]

    def get_openings(self, surface: Any) -> List[Any]:
        """
        Récupère toutes les ouvertures (fenêtres, portes) d'une surface.
        Les ouvertures sont retournées sous forme de liste d'objets génériques.
        """
        surface_id = self.get_object_id(surface)
        if surface_id not in self._openings:
            try:
                self._openings[surface_id] = self._as_list(surface.get_openings())
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des ouvertures pour la surface {surface_id}: {e}")
                self._openings[surface_id] = []
        return self._openings[surface_id]

    def get_thermal_templates(self) -> Dict[str, Any]:
        """Récupère tous les templates thermiques du projet."""
        if not self._templates:
            try:
                templates = self.project.thermal_templates(assigned=False)
                self._templates = self._as_dict(templates)
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des templates thermiques: {e}")
                self._templates = {}
        return self._templates

    def get_room_data(self, body: Any) -> Optional[Any]:
        """Récupère les données de la pièce (VERoomData)."""
        body_id = self.get_object_id(body)
        if body_id not in self._room_data_cache:
            try:
                self._room_data_cache[body_id] = body.get_room_data()
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des données de la pièce {body_id}: {e}")
                self._room_data_cache[body_id] = None
        return self._room_data_cache[body_id]

    def get_internal_gains(self, room_data: Any) -> List[Any]:
        """Récupère les gains internes (éclairage, occupants, équipements)."""
        try:
            return self._as_list(room_data.get_internal_gains())
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des gains internes: {e}")
            return []

    def get_air_exchanges(self, room_data: Any) -> List[Any]:
        """Récupère les échanges d'air (ventilation, infiltration)."""
        try:
            return self._as_list(room_data.get_air_exchanges())
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des échanges d'air: {e}")
            return []

    def get_apache_systems(self, room_data: Any) -> Dict[str, Any]:
        """Récupère les systèmes Apache (CVC) d'une pièce."""
        try:
            return self._as_dict(room_data.get_apache_systems())
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des systèmes Apache: {e}")
            return {}

    def get_room_conditions(self, room_data: Any) -> Dict[str, Any]:
        """Récupère les conditions de la pièce (températures, humidité)."""
        try:
            return self._as_dict(room_data.get_room_conditions())
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des conditions de la pièce: {e}")
            return {}

    def get_weather_data(self) -> Optional[Any]:
        """Récupère le fichier météo du projet."""
        if self._weather_data is None:
            try:
                self._weather_data = self.project.weather_file()
            except Exception as e:
                logger.error(f"Erreur lors de la récupération du fichier météo: {e}")
                self._weather_data = None
        return self._weather_data

    def get_hvac_systems(self) -> Dict[str, Any]:
        """Récupère tous les systèmes CVC du projet."""
        if not self._hvac_systems:
            try:
                self._hvac_systems = self._as_dict(self.project.apache_systems())
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des systèmes CVC: {e}")
                self._hvac_systems = {}
        return self._hvac_systems

    def get_energy_sources(self) -> Dict[str, Any]:
        """Récupère toutes les sources d'énergie du projet."""
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
                logger.error(f"Erreur lors de la récupération des sources d'énergie: {e}")
                self._energy_sources = {}
        return self._energy_sources

    def get_body_areas(self, body: Any) -> Dict[str, float]:
        """Récupère les aires et le volume d'une pièce via VEBody.get_areas()."""
        try:
            return self._as_dict(body.get_areas())
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des aires de la pièce {self.get_object_id(body)}: {e}")
            return {}

    def get_surface_properties(self, surface: Any) -> Dict[str, Any]:
        """Récupère les propriétés d'une surface sans supposer que c'est un dictionnaire Python."""
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
            logger.error(f"Erreur lors de la récupération des propriétés de la surface {self.get_surface_id(surface)}: {e}")
            return {}

    def get_opening_properties(self, opening: Any) -> Dict[str, Any]:
        """Récupère les propriétés d'une ouverture sans supposer que c'est un dictionnaire Python."""
        try:
            props = self._safe_properties(opening)
            construction_id = self.get_opening_construction(opening)
            construction_props = self.get_construction_properties(construction_id) if construction_id else {}
            return {
                "area": self._safe_lookup(props, "area"),
                "U-value": (
                    self._find_first_present(props, ("U-value", "u_value", "u", "u-value"))
                    or self._extract_u_value(construction_props)
                ),
                "solar_factor": (
                    self._find_first_present(props, ("solar_factor", "g_value", "g-value"))
                    or self._extract_g_value(construction_props)
                ),
                "visible_transmittance": self._find_first_present(
                    props,
                    (
                        "visible_transmittance",
                        "light_transmittance",
                        "transmission_lumineuse",
                        "tau",
                        "tvis",
                    ),
                )
                or self._find_first_present(
                    construction_props,
                    (
                        "visible_transmittance",
                        "light_transmittance",
                        "transmission_lumineuse",
                        "tau",
                        "tvis",
                    ),
                ),
                "frame_fraction": self._find_first_present(
                    props,
                    ("frame_fraction", "frame-factor", "frame_factor", "ff"),
                )
                or self._find_first_present(
                    construction_props,
                    ("frame_fraction", "frame-factor", "frame_factor", "ff"),
                ),
                "shading_type": self._find_first_present(
                    props,
                    ("shading_type", "solar_protection", "blind_type", "shade_type"),
                )
                or self._find_first_present(
                    construction_props,
                    ("shading_type", "solar_protection", "blind_type", "shade_type"),
                ),
                "shading_control": self._find_first_present(
                    props,
                    ("shading_control", "blind_control", "solar_protection_control"),
                )
                or self._find_first_present(
                    construction_props,
                    ("shading_control", "blind_control", "solar_protection_control"),
                ),
                "g_total": self._find_first_present(
                    props,
                    ("g_total", "total_g_value", "glazing_shading_g_value"),
                )
                or self._find_first_present(
                    construction_props,
                    ("g_total", "total_g_value", "glazing_shading_g_value"),
                ),
                "orientation": self._safe_lookup(props, "orientation"),
                "type": self._safe_lookup(props, "type") or self._get_opening_type(opening),
                "construction_id": construction_id,
                "construction_properties": construction_props,
            }
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des propriétés de l'ouverture {self.get_surface_id(opening)}: {e}")
            return {}

    def get_surface_areas(self, surface: Any) -> Dict[str, float]:
        """Récupère les aires d'une surface via get_areas() documentée."""
        try:
            return self._as_dict(surface.get_areas())
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des aires de la surface {self.get_surface_id(surface)}: {e}")
            return {}

    def get_adjacencies(self, surface: Any) -> List[Any]:
        """Récupère les adjacences d'une surface."""
        try:
            return self._as_list(surface.get_adjacencies())
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des adjacences de la surface {self.get_surface_id(surface)}: {e}")
            return []

    def get_constructions(self, surface: Any) -> List[str]:
        """Récupère les constructions appliquées à une surface."""
        try:
            return self._as_list(surface.get_constructions())
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des constructions de la surface {self.get_surface_id(surface)}: {e}")
            return []

    def get_opening_construction(self, opening: Any) -> str:
        """Récupère la construction assignée à une ouverture VEGeometry."""
        try:
            construction_id = opening.get_construction()
            return str(construction_id or "")
        except Exception:
            return ""

    def get_construction_properties(self, construction_id: Any) -> Dict[str, Any]:
        """Résout les propriétés thermiques d'une construction CDB à partir de son ID."""
        construction_key = str(construction_id or "").strip()
        if not construction_key:
            return {}
        if construction_key not in self._construction_properties:
            self._construction_properties[construction_key] = self._resolve_construction_properties(construction_key)
        return self._construction_properties[construction_key]

    def _resolve_construction_properties(self, construction_id: str) -> Dict[str, Any]:
        """Interroge VECdbConstruction avec plusieurs classes possibles pour rester compatible VE."""
        try:
            import importlib
            iesve = importlib.import_module("iesve")
        except Exception as e:
            logger.debug("iesve indisponible pour la résolution construction %s: %s", construction_id, e)
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
        """Retourne les projets CDB disponibles dans la base courante."""
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
            logger.debug("Impossible d'accéder aux projets CDB: %s", e)

        self._cdb_projects = projects
        return self._cdb_projects

    @staticmethod
    def _get_cdb_construction_classes(iesve_module: Any) -> List[Any]:
        """Collecte les enums construction_class exposées par les versions IESVE."""
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
        """Parcourt récursivement get_projects() pour extraire les VECdbProject."""
        projects: List[Any] = []
        seen: set = set()

        def visit(item: Any, depth: int = 0) -> None:
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
        try:
            if construction_class is None:
                return cdb_project.get_construction(construction_id)
            return cdb_project.get_construction(construction_id, construction_class)
        except Exception:
            return None

    def _read_cdb_construction(self, construction: Any, construction_id: str) -> Dict[str, Any]:
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
        """Collecte les enums uvalue_types, avec fallback numérique compatible VE."""
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
        """Récupère l'ID d'un objet VE de manière compatible avec les objets exposés par l'API."""
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
        """Compatibilité avec les appels historiques du projet."""
        return self.get_object_id(surface)

    @staticmethod
    def _normalize_enum_name(value: Any) -> str:
        """Normalise le nom d'une enum IESVE en chaîne simple."""
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
        """Vérifie si le body correspond à une pièce exploitable."""
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
        """Extrait et normalise le type d'une surface VESurface."""
        try:
            props = self._safe_properties(surface)
            surface_type = self._safe_lookup(props, "type") or getattr(surface, "type", None)
        except Exception:
            surface_type = getattr(surface, "type", None)
        return self._normalize_surface_type(surface_type)

    def _get_opening_type(self, opening: Any) -> str:
        """Extrait et normalise le type d'une ouverture VESurface opening."""
        try:
            props = self._safe_properties(opening)
            opening_type = self._safe_lookup(props, "type") or getattr(opening, "type", None)
        except Exception:
            opening_type = getattr(opening, "type", None)
        return self._normalize_opening_type(opening_type)

    @staticmethod
    def _normalize_surface_type(surface_type: Any) -> str:
        """Normalise les types de surface IESVE vers des valeurs réutilisables."""
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
        """Normalise les types d'ouverture IESVE vers des valeurs réutilisables."""
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
        """Lit une clé de manière sûre même si la valeur n'est pas un dictionnaire Python."""
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
        """Retourne la première valeur non vide pour une liste de clés possibles."""
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
        """Extrait une U-value depuis les propriétés CDB d'une construction."""
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
        """Extrait le facteur solaire depuis les propriétés CDB d'un vitrage."""
        direct = cls._find_first_present(
            construction_props,
            (
                "g_value",
                "g-value",
                "solar_factor",
                "solar_transmittance",
                "total_solar_energy_transmittance",
            ),
        )
        numeric = cls._to_float_or_none(direct)
        if numeric is not None:
            return numeric

        g_values = construction_props.get("g_values")
        if isinstance(g_values, dict):
            for preferred in ("building_regulations", "bs_en_410", "bfrc"):
                numeric = cls._to_float_or_none(g_values.get(preferred))
                if numeric is not None:
                    return numeric
            for value in g_values.values():
                numeric = cls._to_float_or_none(value)
                if numeric is not None:
                    return numeric
        return None

    @staticmethod
    def _to_float_or_none(value: Any) -> Optional[float]:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_object_attr(obj: Any, attribute_name: str) -> Any:
        try:
            value = getattr(obj, attribute_name)
            if callable(value):
                return value()
            return value
        except Exception:
            return None

    @staticmethod
    def _safe_properties(obj: Any) -> Dict[str, Any]:
        """Extrait les propriétés d'un objet VE de manière sûre."""
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
        """Normalise une valeur en liste si possible."""
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
        """Normalise une valeur en dictionnaire si possible."""
        if isinstance(value, dict):
            return value
        try:
            return dict(value)
        except Exception:
            return {}
