"""Capability-gated adapter for the IESVE Python API.

No :mod:`iesve` import occurs at module import time.  Pure-Python tests and
reporting therefore remain runnable outside VE.  The adapter uses only methods
documented in the VE 2023 VEScript User Guide bundled under ``references``.
"""

from abc import ABC, abstractmethod
from enum import Enum
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .asset_manifest import AssetManifest
from .compliance_config import ParameterRegistry
from .domain import (
    ConstructionSnapshot,
    GeometryModel,
    MaterialSnapshot,
    ModelSnapshot,
    OpeningSnapshot,
    RoomSnapshot,
    SurfaceSnapshot,
    TemplateSnapshot,
)
from .exceptions import VeApiUnavailableError, VeMutationError
from .ve_asset_provisioner import IesVeAssetProvisioner, ProvisioningReceipt
from .ve_compat import thermal_templates


def _enum_or_value(value: Any) -> Any:
    """Normalize VE enums and containers into serializable values."""

    if isinstance(value, Enum):
        return value.value
    if isinstance(value, dict):
        return {str(key): _enum_or_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_enum_or_value(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _normalise_type(value: Any) -> str:
    """Normalize a VE type label for resilient matching."""

    return "".join(character for character in str(value).lower() if character.isalnum())


def _record_names(records: Iterable[Any]) -> List[str]:
    """Return stable sorted names for VE gain and air-exchange records."""

    names: List[str] = []
    for record in records:
        data: Dict[str, Any] = {}
        try:
            data = dict(record.get())
        except Exception:
            data = {}
        name = str(data.get("name") or getattr(record, "name", "") or "").strip()
        if name:
            names.append(name)
    return sorted(names)


def _values_equivalent(expected: Any, actual: Any) -> bool:
    """Compare VE read-back values without introducing compliance tolerance."""

    expected = _enum_or_value(expected)
    actual = _enum_or_value(actual)
    if isinstance(expected, bool) or isinstance(actual, bool):
        return expected == actual
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return math.isclose(
            float(expected),
            float(actual),
            rel_tol=1.0e-6,
            abs_tol=1.0e-7,
        )
    return expected == actual


def _gain_family(data: Dict[str, Any]) -> str:
    """Return the physical room-gain family used for semantic matching."""

    label = _normalise_type(data.get("type_str", ""))
    if "people" in label:
        return "people"
    if "lighting" in label:
        return "lighting"
    return "energy"


def _selected_readback(
    data: Dict[str, Any], plural_key: str, scalar_key: str
) -> Any:
    """Resolve a scalar template value or the room value in selected units."""

    if scalar_key in data:
        return data[scalar_key]
    values = data.get(plural_key)
    if not isinstance(values, dict):
        return None
    units = data.get("units_val", 0)
    try:
        index = int(units)
    except (TypeError, ValueError):
        index = 0
    return values.get(index, values.get(str(index)))


def _gain_semantic_mismatches(
    expected: Dict[str, Any], actual: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """Compare the simulation-relevant values of template and room gains."""

    mismatches: Dict[str, Dict[str, Any]] = {}
    scalar_to_plural = {
        "max_power_consumption": "max_power_consumptions",
        "max_sensible_gain": "max_sensible_gains",
        "max_latent_gain": "max_latent_gains",
        "occupancy_density": "occupancies",
    }
    compared = False
    for scalar_key, plural_key in scalar_to_plural.items():
        if scalar_key not in expected:
            continue
        compared = True
        actual_value = _selected_readback(actual, plural_key, scalar_key)
        if not _values_equivalent(expected[scalar_key], actual_value):
            mismatches[scalar_key] = {
                "expected": _enum_or_value(expected[scalar_key]),
                "actual": _enum_or_value(actual_value),
            }
    for key in (
        "units_val",
        "radiant_fraction",
        "diversity_factor",
        "variation_profile",
    ):
        if key not in expected:
            continue
        compared = True
        if not _values_equivalent(expected[key], actual.get(key)):
            mismatches[key] = {
                "expected": _enum_or_value(expected[key]),
                "actual": _enum_or_value(actual.get(key)),
            }
    if (
        not compared
        and expected.get("name")
        and expected.get("name") != actual.get("name")
    ):
        mismatches["name"] = {
            "expected": str(expected.get("name")),
            "actual": str(actual.get("name", "")),
        }
    return mismatches


def _air_exchange_semantic_mismatches(
    expected: Dict[str, Any], actual: Dict[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """Compare the effective flow and schedule of two air exchanges."""

    mismatches: Dict[str, Dict[str, Any]] = {}
    expected_flow = expected.get("max_flow")
    actual_flow = _selected_readback(actual, "max_flows", "max_flow")
    if expected_flow is not None and not _values_equivalent(expected_flow, actual_flow):
        mismatches["max_flow"] = {
            "expected": _enum_or_value(expected_flow),
            "actual": _enum_or_value(actual_flow),
        }
    for key in ("units_val", "variation_profile", "adjacent_condition_val"):
        if key in expected and not _values_equivalent(expected[key], actual.get(key)):
            mismatches[key] = {
                "expected": _enum_or_value(expected[key]),
                "actual": _enum_or_value(actual.get(key)),
            }
    return mismatches


class VeGateway(ABC):
    """Boundary used by the workflow and replaced by fakes in unit tests."""

    @property
    @abstractmethod
    def project_path(self) -> Path:
        """Return the active VE project folder."""

        raise NotImplementedError

    @property
    @abstractmethod
    def project_name(self) -> str:
        """Return the active VE project name."""

        raise NotImplementedError

    @abstractmethod
    def check_capabilities(self) -> Dict[str, bool]:
        """Verify all API capabilities required before mutation."""

        raise NotImplementedError

    def provision_assets(self, manifest: AssetManifest) -> ProvisioningReceipt:
        """Create manifest assets or report that the gateway lacks create mode."""

        raise VeApiUnavailableError("This VE gateway does not support asset create mode")

    @abstractmethod
    def assert_no_existing_generated_rooms(self, expected_names: Sequence[str]) -> None:
        """Reject an unsafe duplicate reference-model generation attempt."""

        raise NotImplementedError

    @abstractmethod
    def import_geometry(self, gbxml_path: Path) -> None:
        """Import deterministic geometry into the active VE project."""

        raise NotImplementedError

    @abstractmethod
    def rebuild_adjacencies(self) -> None:
        """Request VE to rebuild room and surface adjacencies."""

        raise NotImplementedError

    @abstractmethod
    def assign_constructions(
        self, expected_geometry: GeometryModel, parameters: ParameterRegistry
    ) -> None:
        """Assign and immediately verify all configured constructions."""

        raise NotImplementedError

    @abstractmethod
    def assign_thermal_template(
        self, expected_geometry: GeometryModel, parameters: ParameterRegistry
    ) -> None:
        """Assign and immediately verify the approved thermal template."""

        raise NotImplementedError

    @abstractmethod
    def assign_hvac_if_configured(
        self, expected_geometry: GeometryModel, parameters: ParameterRegistry
    ) -> None:
        """Assign the configured HVAC placeholder when one is supplied."""

        raise NotImplementedError

    @abstractmethod
    def assign_weather(self, weather_file: str) -> None:
        """Assign and immediately verify the configured weather file."""

        raise NotImplementedError

    def verify_construction_assignments(
        self, expected_geometry: GeometryModel, parameters: ParameterRegistry
    ) -> None:
        """Optionally re-verify surface constructions after adjacency rebuild.

        Concrete production gateways override this; the default is a safe no-op
        so preflight-only and dry-run gateways remain unaffected.
        """

    def consume_runtime_compatibility_warnings(self) -> List[Dict[str, Any]]:
        """Return and clear compatibility workarounds used during mutation."""

        return []

    @abstractmethod
    def snapshot(
        self, expected_geometry: GeometryModel, parameters: ParameterRegistry
    ) -> ModelSnapshot:
        """Read normalized state back from the current VE project."""

        raise NotImplementedError


class IesVeGateway(VeGateway):
    """Production gateway for a currently open VE project."""

    REQUIRED_CAPABILITIES = (
        "ImportGBXML",
        "VEProject",
        "VELocate",
        "WeatherFileReader",
        "VECdbDatabase",
        "VECdbProject",
    )

    def __init__(self, iesve_module: Optional[Any] = None):
        """Bind to the current project through a lazy iesve import."""

        if iesve_module is None:
            try:
                import iesve as iesve_module  # type: ignore
            except ImportError as exc:
                raise VeApiUnavailableError(
                    "The iesve module is only available inside the VE Scripts runtime"
                ) from exc
        self.iesve = iesve_module
        try:
            self.project = self.iesve.VEProject.get_current_project()
            self.model = self.project.models[0]
            self._runtime_compatibility_warnings: List[Dict[str, Any]] = []
        except Exception as exc:
            raise VeApiUnavailableError(
                "No usable current VE project/real model is available: {}".format(exc)
            ) from exc

    def consume_runtime_compatibility_warnings(self) -> List[Dict[str, Any]]:
        """Return compatibility workarounds once for the workflow audit."""

        warnings = list(self._runtime_compatibility_warnings)
        self._runtime_compatibility_warnings = []
        return warnings

    @property
    def project_path(self) -> Path:
        """Return the current project path exposed by VE."""

        return Path(str(self.project.path))

    @property
    def project_name(self) -> str:
        """Return the current project name exposed by VE."""

        return str(self.project.name)

    def check_capabilities(self) -> Dict[str, bool]:
        """Fail unless the installed VE runtime exposes every member used at mutation.

        The gate covers not only the top-level modules but each concrete member
        the mutation path later calls (import, weather, construction/opening
        assignment, template/HVAC/version accessors and the CDB enum
        containers), so a missing member is reported at preflight instead of
        surfacing as a partial mutation mid-run.
        """

        import_gbxml = getattr(self.iesve, "ImportGBXML", object)
        velocate = getattr(self.iesve, "VELocate", object)
        weather_reader = getattr(self.iesve, "WeatherFileReader", object)
        vebody = getattr(self.iesve, "VEBody", object)
        cdb_project_cls = getattr(self.iesve, "VECdbProject", object)

        def enum_container_available(name: str) -> bool:
            """Return whether an enum container exists on the CDB class or module."""

            return hasattr(cdb_project_cls, name) or hasattr(self.iesve, name)

        capabilities = {
            name: hasattr(self.iesve, name) for name in self.REQUIRED_CAPABILITIES
        }
        capabilities.update(
            {
                "ImportGBXML.import_file": hasattr(import_gbxml, "import_file"),
                "ImportGBXML.VolumeCapMode": (
                    hasattr(import_gbxml, "VolumeCapMode")
                    or hasattr(self.iesve, "VolumeCapMode")
                ),
                "VEModel.get_bodies": hasattr(self.model, "get_bodies"),
                "VEModel.rebuild_adjacencies": hasattr(
                    self.model, "rebuild_adjacencies"
                ),
                "VEModel.assign_thermal_template_to_rooms": hasattr(
                    self.model, "assign_thermal_template_to_rooms"
                ),
                # VEProject.get_version is intentionally NOT gated: it feeds
                # only the informational ModelSnapshot.ve_version field and is
                # guarded by _safe_version, so a version-less-but-otherwise-
                # capable runtime must not be rejected at preflight.
                "VEProject.thermal_templates": hasattr(self.project, "thermal_templates"),
                "VEProject.apache_systems": hasattr(self.project, "apache_systems"),
                "VELocate.open_wea_data": hasattr(velocate, "open_wea_data"),
                "VELocate.set": hasattr(velocate, "set"),
                "VELocate.save_and_close": hasattr(velocate, "save_and_close"),
                "WeatherFileReader.open_weather_file": hasattr(
                    weather_reader, "open_weather_file"
                ),
                "VEBody.assign_construction": hasattr(vebody, "assign_construction"),
                "VEBody.assign_construction_to_opening": hasattr(
                    vebody, "assign_construction_to_opening"
                ),
                "VECdbProject.construction_class": hasattr(
                    cdb_project_cls, "construction_class"
                ) or hasattr(
                    self.iesve, "construction_class"
                ),
                "VECdbProject.uvalue_types": enum_container_available("uvalue_types"),
                "VECdbProject.material_categories": enum_container_available(
                    "material_categories"
                ),
                "VECdbProject.element_categories": enum_container_available(
                    "element_categories"
                ),
            }
        )
        missing = sorted(name for name, present in capabilities.items() if not present)
        if missing:
            raise VeApiUnavailableError(
                "Required VE API capabilities are missing: {}".format(missing)
            )
        return capabilities

    def provision_assets(self, manifest: AssetManifest) -> ProvisioningReceipt:
        """Create all source-traced VE assets and return their persistent IDs."""

        provisioner = IesVeAssetProvisioner(
            self.iesve, self.project, self._cdb_project()
        )
        return provisioner.provision(manifest)

    def reconcile_existing_gain(
        self, manifest: AssetManifest, gain_key: str
    ) -> Dict[str, Any]:
        """Run one explicitly requested, read-back-verified gain repair."""

        provisioner = IesVeAssetProvisioner(
            self.iesve, self.project, self._cdb_project()
        )
        return provisioner.reconcile_existing_gain(manifest, gain_key)

    def reconcile_existing_air_exchange(
        self, manifest: AssetManifest, exchange_key: str
    ) -> Dict[str, Any]:
        """Run one explicitly requested, read-back-verified exchange repair."""

        provisioner = IesVeAssetProvisioner(
            self.iesve, self.project, self._cdb_project()
        )
        return provisioner.reconcile_existing_air_exchange(
            manifest, exchange_key
        )

    def _is_room(self, body: Any) -> bool:
        """Return whether a VE body represents a thermal room."""

        try:
            return body.type == self.iesve.VEBody.VEBody_type.room
        except Exception:
            return _normalise_type(body.type).endswith("room")

    def _room_bodies(self) -> List[Any]:
        """Return all room bodies from the active real model."""

        return [body for body in self.model.get_bodies(False) if self._is_room(body)]

    def _expected_bodies(self, expected_geometry: GeometryModel) -> List[Any]:
        """Resolve every expected generated space to an imported room."""

        expected_names = {space.name for space in expected_geometry.spaces}
        bodies = [body for body in self._room_bodies() if str(body.name) in expected_names]
        actual_names = {str(body.name) for body in bodies}
        missing = sorted(expected_names - actual_names)
        if missing:
            raise VeMutationError(
                "Imported VE model is missing expected rooms: {}".format(missing)
            )
        return bodies

    def assert_no_existing_generated_rooms(self, expected_names: Sequence[str]) -> None:
        """Fail closed when generated room names already exist."""

        expected = set(expected_names)
        existing = sorted(
            str(body.name) for body in self._room_bodies() if str(body.name) in expected
        )
        if existing:
            raise VeMutationError(
                "Generation is idempotent/fail-closed: rooms already exist: {}".format(existing)
            )

    def import_geometry(self, gbxml_path: Path) -> None:
        """Import gbXML through the documented VE import service."""

        if not gbxml_path.is_file():
            raise VeMutationError("gbXML input does not exist: {}".format(gbxml_path))
        try:
            cap_mode_container = getattr(
                self.iesve.ImportGBXML,
                "VolumeCapMode",
                getattr(self.iesve, "VolumeCapMode", None),
            )
            if cap_mode_container is None or not hasattr(cap_mode_container, "none"):
                raise VeApiUnavailableError(
                    "VE exposes no usable VolumeCapMode.none enum"
                )
            cap_mode = cap_mode_container.none
            self.iesve.ImportGBXML.import_file(
                str(gbxml_path), True, cap_mode, 0.0
            )
        except Exception as exc:
            raise VeMutationError(
                "Documented ImportGBXML.import_file call failed: {}".format(exc)
            ) from exc

    def rebuild_adjacencies(self) -> None:
        """Rebuild active-model adjacencies and wrap VE failures."""

        try:
            self.model.rebuild_adjacencies()
        except Exception as exc:
            raise VeMutationError("VE adjacency rebuild failed: {}".format(exc)) from exc

    @staticmethod
    def _construction_parameter_for_surface(surface: Any) -> str:
        """Map a VE surface type to its configuration key."""

        properties = surface.get_properties()
        surface_type = _normalise_type(properties.get("type", surface.type))
        if "ground" in surface_type or "slab" in surface_type:
            return "ground_floor_construction_id"
        if "roof" in surface_type or "externalceiling" in surface_type:
            return "roof_construction_id"
        if "internalwall" in surface_type or "intwall" in surface_type or "partition" in surface_type:
            return "internal_wall_construction_id"
        if "externalwall" in surface_type or "extwall" in surface_type or surface_type == "wall":
            return "external_wall_construction_id"
        # gbXML import may expose the slab as a generic floor before boundary
        # reconciliation.  The generated model has no intermediate floors.
        if "floor" in surface_type:
            return "ground_floor_construction_id"
        raise VeMutationError(
            "No construction mapping for VE surface type '{}'".format(surface_type)
        )

    def _cdb_project(self) -> Any:
        """Return the current editable construction-database project."""

        try:
            projects = self.iesve.VECdbDatabase.get_current_database().get_projects()
            project_candidates = projects.get(0, []) if isinstance(projects, dict) else []
            if not project_candidates:
                raise VeMutationError("Current CDB has no project database")
            return project_candidates[0]
        except VeMutationError:
            raise
        except Exception as exc:
            raise VeMutationError("Unable to access current CDB project: {}".format(exc)) from exc

    def _construction_class_none(self) -> Any:
        """Resolve the documented ``construction_class.none`` enum if present."""

        cdb_project_cls = getattr(self.iesve, "VECdbProject", None)
        construction_class = getattr(cdb_project_cls, "construction_class", None)
        if construction_class is None:
            construction_class = getattr(self.iesve, "construction_class", None)
        return getattr(construction_class, "none", None)

    def _uvalue_type_iso(self) -> Any:
        """Resolve the ISO U-value enum member defensively across VE builds."""

        cdb_project_cls = getattr(self.iesve, "VECdbProject", None)
        uvalue_types = getattr(cdb_project_cls, "uvalue_types", None)
        if uvalue_types is None:
            uvalue_types = getattr(self.iesve, "uvalue_types", None)
        member = getattr(uvalue_types, "iso", None)
        if member is None:
            raise VeMutationError("VE VECdbProject.uvalue_types.iso is unavailable")
        return member

    def _get_construction(self, construction_id: str) -> Any:
        """Resolve one construction, tolerating VE ``get_construction`` variants.

        Some VE builds expose ``get_construction(id)`` and others
        ``get_construction(id, construction_class)``.  This mirrors the tolerant
        resolution already used by the read-only extractor rather than assuming
        a single signature, but fails closed if no variant resolves.
        """

        cdb_project = self._cdb_project()
        construction_class = self._construction_class_none()
        attempts: List[Tuple[Any, ...]] = []
        if construction_class is not None:
            attempts.append((construction_id, construction_class))
        attempts.append((construction_id,))
        last_exc: Optional[Exception] = None
        for args in attempts:
            try:
                construction = cdb_project.get_construction(*args)
            except Exception as exc:  # try the next documented signature variant
                last_exc = exc
                continue
            if construction is not None:
                return construction
        raise VeMutationError(
            "Construction '{}' is unavailable: {}".format(construction_id, last_exc)
        )

    @staticmethod
    def _construction_identifier(construction: Any) -> str:
        """Normalize a construction object or ID returned by VE read-back."""

        if isinstance(construction, str):
            return construction
        value = getattr(construction, "id", None)
        if value:
            return str(value)
        if hasattr(construction, "get_properties"):
            properties = dict(construction.get_properties())
            value = properties.get("id", properties.get("construction_id", ""))
            if value:
                return str(value)
        return str(construction)

    @staticmethod
    def _construction_layer_is_resolved(construction: Any, layer: Any) -> bool:
        """Accept material layers and native glazed cavity layers only."""

        opaque = bool(construction.opaque)
        try:
            if layer.get_material(opaque) is not None:
                return True
        except Exception:
            pass
        if opaque:
            return False
        try:
            properties = dict(layer.get_properties())
        except Exception:
            return False
        # Native glazed cavities have no material handle.  They remain valid
        # only when VE reports a positive thermal property.
        return any(
            float(properties.get(name, 0.0) or 0.0) > 0.0
            for name in ("resistance", "convection_coefficient")
        )

    def assign_constructions(
        self, expected_geometry: GeometryModel, parameters: ParameterRegistry
    ) -> None:
        """Assign surface and opening constructions with immediate read-back."""

        configured_ids = {
            name: str(parameters.value(name))
            for name in (
                "external_wall_construction_id",
                "roof_construction_id",
                "ground_floor_construction_id",
                "internal_wall_construction_id",
                "door_construction_id",
                "glazing_construction_id",
            )
        }
        configured_constructions = {
            name: self._get_construction(construction_id)
            for name, construction_id in configured_ids.items()
        }
        for name, construction_id in configured_ids.items():
            construction = configured_constructions[name]
            layers = list(construction.get_layers())
            if not layers or any(
                not self._construction_layer_is_resolved(construction, layer)
                for layer in layers
            ):
                raise VeMutationError(
                    "Construction '{}' has undefined/empty material layers".format(
                        construction_id
                    )
                )

        for body in self._expected_bodies(expected_geometry):
            for surface in body.get_surfaces():
                parameter_name = self._construction_parameter_for_surface(surface)
                construction_id = configured_ids[parameter_name]
                construction = configured_constructions[parameter_name]
                body.assign_construction(construction, surface)
                assigned = [
                    self._construction_identifier(item)
                    for item in surface.get_constructions()
                ]
                if construction_id not in assigned:
                    raise VeMutationError(
                        "Construction assignment did not persist for surface {}".format(
                            surface.get_properties().get("id", surface.index)
                        )
                    )
                for opening in surface.get_openings():
                    opening_type = _normalise_type(
                        opening.get_properties().get("type", "")
                    )
                    opening_construction_id = (
                        configured_ids["door_construction_id"]
                        if "door" in opening_type
                        else configured_ids["glazing_construction_id"]
                    )
                    opening_construction = (
                        configured_constructions["door_construction_id"]
                        if "door" in opening_type
                        else configured_constructions["glazing_construction_id"]
                    )
                    body.assign_construction_to_opening(
                        opening_construction, surface, opening.get_id()
                    )
                    if self._construction_identifier(
                        opening.get_construction()
                    ) != opening_construction_id:
                        raise VeMutationError(
                            "Opening construction assignment did not persist for {}".format(
                                opening.get_id()
                            )
                        )

    def verify_construction_assignments(
        self, expected_geometry: GeometryModel, parameters: ParameterRegistry
    ) -> None:
        """Re-verify surface constructions against finalized types post-adjacency.

        gbXML import may expose a surface with a provisional boundary type that
        is only finalized by ``rebuild_adjacencies()`` (for example an internal
        partition initially presented as a generic wall).  This guard re-derives
        the expected construction from each surface's now-final type and fails
        closed if a persisted assignment no longer matches it, rather than
        trusting the assignment made before adjacency reconciliation.
        """

        configured_ids = {
            name: str(parameters.value(name))
            for name in (
                "external_wall_construction_id",
                "roof_construction_id",
                "ground_floor_construction_id",
                "internal_wall_construction_id",
            )
        }
        for body in self._expected_bodies(expected_geometry):
            for surface in body.get_surfaces():
                parameter_name = self._construction_parameter_for_surface(surface)
                expected_id = configured_ids.get(parameter_name)
                if expected_id is None:
                    continue
                assigned = [
                    self._construction_identifier(item)
                    for item in surface.get_constructions()
                ]
                if expected_id not in assigned:
                    raise VeMutationError(
                        "Post-adjacency construction mismatch on surface {}: "
                        "finalized type expects '{}' but assigned {}".format(
                            surface.get_properties().get("id", surface.index),
                            expected_id,
                            assigned,
                        )
                    )

    def _find_template(self, template_name: str) -> Tuple[Any, Any]:
        """Resolve exactly one existing template by its approved name."""

        templates = thermal_templates(self.project, assigned=False)
        matches = [
            (handle, template)
            for handle, template in templates.items()
            if str(template.name) == template_name
        ]
        if len(matches) != 1:
            raise VeMutationError(
                "Expected exactly one thermal template named '{}'; found {}".format(
                    template_name, len(matches)
                )
            )
        return matches[0]

    @staticmethod
    def _record_data(record: Any, context: str) -> Dict[str, Any]:
        """Read one native record as a dictionary with a controlled error."""

        try:
            return dict(record.get())
        except Exception as exc:
            raise VeMutationError(
                "Unable to read {}: {}".format(context, exc)
            ) from exc

    def _synchronise_room_gains(
        self, room_data: Any, template: Any, room_name: str
    ) -> List[Dict[str, Any]]:
        """Copy template gain physics when VE retains default room content."""

        expected_records = list(template.get_casual_gains())
        actual_records = list(room_data.get_internal_gains())
        expected_by_family: Dict[str, Tuple[Any, Dict[str, Any]]] = {}
        actual_by_family: Dict[str, Tuple[Any, Dict[str, Any]]] = {}
        for record in expected_records:
            data = self._record_data(record, "template gain")
            family = _gain_family(data)
            if family in expected_by_family:
                raise VeMutationError(
                    "Template has several '{}' gain records; deterministic "
                    "room synchronization is ambiguous".format(family)
                )
            expected_by_family[family] = (record, data)
        for record in actual_records:
            data = self._record_data(record, "room gain")
            family = _gain_family(data)
            if family in actual_by_family:
                raise VeMutationError(
                    "Room '{}' has several '{}' gain records; deterministic "
                    "synchronization is ambiguous".format(room_name, family)
                )
            actual_by_family[family] = (record, data)

        changes: List[Dict[str, Any]] = []
        for family, (_expected_record, expected) in expected_by_family.items():
            if family not in actual_by_family:
                raise VeMutationError(
                    "Room '{}' has no '{}' gain corresponding to template '{}'".format(
                        room_name, family, expected.get("name", "")
                    )
                )
            actual_record, before = actual_by_family[family]
            if (
                family == "energy"
                and "max_latent_gain" not in expected
                and "max_latent_gains" in before
            ):
                # VE 2025 omits a zero-valued latent field from global
                # EnergyGain read-back. RoomPowerGain exposes it explicitly,
                # so enforce and verify zero at the physical room level.
                expected = dict(expected)
                expected["max_latent_gain"] = 0.0
            mismatches = _gain_semantic_mismatches(expected, before)
            if not mismatches:
                continue
            if not hasattr(actual_record, "set"):
                raise VeMutationError(
                    "Thermal template gain content did not resolve for room '{}'; "
                    "the {} gain exposes no supported set() method: {}".format(
                        room_name, family, mismatches
                    )
                )
            payload: Dict[str, Any] = {}
            writable = (
                "allow_profile_saturate",
                "ballast",
                "dimming_profile",
                "diversity_factor",
                "max_illuminance",
                "installed_power_density",
                "max_latent_gain",
                "max_power_consumption",
                "max_sensible_gain",
                "occupancy_density",
                "radiant_fraction",
                "units_val",
                "variation_profile",
            )
            for key in writable:
                if key not in expected:
                    continue
                payload[key] = expected[key]
                flag = "{}_from_template".format(key)
                if flag in before or key in (
                    "max_latent_gain",
                    "max_sensible_gain",
                    "units_val",
                    "variation_profile",
                ):
                    payload[flag] = False
            try:
                actual_record.set(payload)
            except Exception as exc:
                raise VeMutationError(
                    "Direct room-level {} gain synchronization failed for '{}': "
                    "{}".format(family, room_name, exc)
                ) from exc
            after = self._record_data(actual_record, "synchronized room gain")
            remaining = _gain_semantic_mismatches(expected, after)
            if remaining:
                raise VeMutationError(
                    "Direct room-level {} gain synchronization did not persist "
                    "for '{}': {}".format(family, room_name, remaining)
                )
            changes.append(
                {
                    "family": family,
                    "template_record": str(expected.get("name", "")),
                    "before": mismatches,
                    "verified_after": {
                        key: _enum_or_value(expected.get(key))
                        for key in mismatches
                    },
                }
            )
        return changes

    def _synchronise_room_air_exchanges(
        self, room_data: Any, template: Any, room_name: str
    ) -> List[Dict[str, Any]]:
        """Copy non-zero template air exchanges to room-level native records."""

        expected_records = [
            (record, self._record_data(record, "template air exchange"))
            for record in template.get_air_exchanges()
        ]
        actual_records = [
            (record, self._record_data(record, "room air exchange"))
            for record in room_data.get_air_exchanges()
        ]

        def exchange_key(data: Dict[str, Any]) -> str:
            """Return the normalised air-exchange type used to match records."""

            return _normalise_type(data.get("type_val", data.get("type_str", "")))

        actual_by_type = {exchange_key(data): (record, data) for record, data in actual_records}
        changes: List[Dict[str, Any]] = []
        for _expected_record, expected in expected_records:
            key = exchange_key(expected)
            expected_flow = expected.get("max_flow", 0.0)
            match = actual_by_type.get(key)
            if match is None:
                # A zero-flow mechanical-ventilation placeholder has no
                # simulation effect and VE may legitimately omit it at room level.
                if _values_equivalent(expected_flow, 0.0):
                    continue
                raise VeMutationError(
                    "Room '{}' has no air-exchange record corresponding to "
                    "template '{}'".format(room_name, expected.get("name", ""))
                )
            actual_record, before = match
            mismatches = _air_exchange_semantic_mismatches(expected, before)
            if not mismatches:
                continue
            if not hasattr(actual_record, "set"):
                raise VeMutationError(
                    "Room '{}' air exchange differs from its template and exposes "
                    "no supported set() method: {}".format(room_name, mismatches)
                )
            payload: Dict[str, Any] = {}
            for field in (
                "max_flow",
                "units_val",
                "variation_profile",
                "adjacent_condition_val",
                "offset_temperature",
                "temperature_profile",
            ):
                if field not in expected:
                    continue
                payload[field] = expected[field]
                flag = "{}_from_template".format(field)
                if flag in before or field in (
                    "max_flow",
                    "variation_profile",
                    "adjacent_condition_val",
                ):
                    payload[flag] = False
            try:
                actual_record.set(payload)
            except Exception as exc:
                raise VeMutationError(
                    "Direct room-level air-exchange synchronization failed for "
                    "'{}': {}".format(room_name, exc)
                ) from exc
            after = self._record_data(
                actual_record, "synchronized room air exchange"
            )
            remaining = _air_exchange_semantic_mismatches(expected, after)
            if remaining:
                raise VeMutationError(
                    "Direct room-level air-exchange synchronization did not "
                    "persist for '{}': {}".format(room_name, remaining)
                )
            changes.append(
                {
                    "template_record": str(expected.get("name", "")),
                    "before": mismatches,
                    "verified_after": {
                        key_name: _enum_or_value(expected.get(key_name))
                        for key_name in mismatches
                    },
                }
            )
        return changes

    def _synchronise_room_controls(
        self, room_data: Any, template: Any, room_name: str
    ) -> Dict[str, Any]:
        """Persist and verify template setpoints and ideal-load system controls."""

        changes: Dict[str, Any] = {}
        required = (
            (template, "get_room_conditions"),
            (template, "get_apache_systems"),
            (room_data, "get_room_conditions"),
            (room_data, "set_room_conditions"),
            (room_data, "get_apache_systems"),
            (room_data, "set_apache_systems"),
        )
        if not all(hasattr(owner, member) for owner, member in required):
            # Older test doubles and read-only gateways can omit these members.
            # The production VE capability path exposes all six methods.
            return changes
        expected_conditions = dict(template.get_room_conditions())
        actual_conditions = dict(room_data.get_room_conditions())
        condition_keys = (
            "heating_setpoint",
            "cooling_setpoint",
            "heating_profile",
            "cooling_profile",
            "plant_profile",
        )
        condition_drift = {
            key: {
                "expected": _enum_or_value(expected_conditions[key]),
                "actual": _enum_or_value(actual_conditions.get(key)),
            }
            for key in condition_keys
            if key in expected_conditions
            and not _values_equivalent(
                expected_conditions[key], actual_conditions.get(key)
            )
        }
        if condition_drift:
            payload = dict(actual_conditions)
            for key in condition_drift:
                payload[key] = expected_conditions[key]
                payload["{}_from_template".format(key)] = False
            try:
                room_data.set_room_conditions(payload)
            except Exception as exc:
                raise VeMutationError(
                    "Room-condition synchronization failed for '{}': {}".format(
                        room_name, exc
                    )
                ) from exc
            verified = dict(room_data.get_room_conditions())
            remaining = {
                key: verified.get(key)
                for key in condition_drift
                if not _values_equivalent(expected_conditions[key], verified.get(key))
            }
            if remaining:
                raise VeMutationError(
                    "Room-condition synchronization did not persist for '{}': "
                    "{}".format(room_name, remaining)
                )
            changes["room_conditions"] = condition_drift

        expected_system = dict(template.get_apache_systems())
        actual_system = dict(room_data.get_apache_systems())
        system_keys = (
            "conditioned",
            "HVAC_system",
            "HVAC_methodology",
            "heating_capacity_unlimited",
            "heating_capacity_unit",
            "heating_capacity_value",
            "cooling_capacity_unlimited",
            "cooling_capacity_unit",
            "cooling_capacity_value",
        )
        system_drift = {
            key: {
                "expected": _enum_or_value(expected_system[key]),
                "actual": _enum_or_value(actual_system.get(key)),
            }
            for key in system_keys
            if key in expected_system
            and not _values_equivalent(expected_system[key], actual_system.get(key))
        }
        if system_drift:
            payload = dict(actual_system)
            for key in system_drift:
                payload[key] = expected_system[key]
                flag = "{}_from_template".format(key)
                if flag in actual_system:
                    payload[flag] = False
            try:
                room_data.set_apache_systems(payload)
            except Exception as exc:
                raise VeMutationError(
                    "Room system synchronization failed for '{}': {}".format(
                        room_name, exc
                    )
                ) from exc
            verified = dict(room_data.get_apache_systems())
            remaining = {
                key: verified.get(key)
                for key in system_drift
                if not _values_equivalent(expected_system[key], verified.get(key))
            }
            if remaining:
                raise VeMutationError(
                    "Room system synchronization did not persist for '{}': "
                    "{}".format(room_name, remaining)
                )
            changes["apache_system"] = system_drift
        return changes

    def assign_thermal_template(
        self, expected_geometry: GeometryModel, parameters: ParameterRegistry
    ) -> None:
        """Assign one approved template to every generated room."""

        template_name = str(parameters.value("thermal_template_name"))
        template_handle, template = self._find_template(template_name)
        bodies = self._expected_bodies(expected_geometry)
        room_ids = [str(body.id) for body in bodies]
        try:
            # Re-apply pending native template changes before assigning it.
            # VE documents apply_changes() as required after template mutation;
            # calling it again is idempotent for an already persisted template.
            if hasattr(template, "apply_changes"):
                template.apply_changes()
            self.model.assign_thermal_template_to_rooms(template, room_ids)
        except Exception as exc:
            raise VeMutationError(
                "Thermal template assignment failed: {}".format(exc)
            ) from exc
        fresh_bodies = {
            str(getattr(candidate, "id", "")): candidate
            for candidate in self.model.get_bodies(False)
        }
        for body in bodies:
            current_body = fresh_bodies.get(str(body.id), body)
            room_data = current_body.get_room_data()
            general = dict(room_data.get_general())
            assigned_handle = str(general.get("thermal_template", ""))
            assigned_name = str(general.get("thermal_template_name", ""))
            if not (
                assigned_name == template_name
                or assigned_handle == str(template_handle)
                or assigned_handle == template_name
            ):
                raise VeMutationError(
                    "Thermal template did not persist for room '{}': expected "
                    "name={!r}/handle={!r}, read-back name={!r}/handle={!r}".format(
                        body.name,
                        template_name,
                        str(template_handle),
                        assigned_name,
                        assigned_handle,
                    )
                )
            gain_changes = self._synchronise_room_gains(
                room_data, template, str(current_body.name)
            )
            exchange_changes = self._synchronise_room_air_exchanges(
                room_data, template, str(current_body.name)
            )
            control_changes = self._synchronise_room_controls(
                room_data, template, str(current_body.name)
            )
            if gain_changes or exchange_changes or control_changes:
                self._runtime_compatibility_warnings.append(
                    {
                        "code": "VE-TEMPLATE-CONTENT-DIRECT-SYNC",
                        "message": (
                            "VE retained default room-level content after thermal "
                            "template assignment; source-traced template physics "
                            "was copied directly and numerically verified."
                        ),
                        "room_id": str(getattr(current_body, "id", "")),
                        "room_name": str(current_body.name),
                        "gain_changes": gain_changes,
                        "air_exchange_changes": exchange_changes,
                        "control_changes": control_changes,
                    }
                )

    def assign_hvac_if_configured(
        self, expected_geometry: GeometryModel, parameters: ParameterRegistry
    ) -> None:
        """Assign an optional existing system to every generated room."""

        system_id = parameters.value("hvac_system_id")
        if not system_id:
            return
        system_id = str(system_id)
        available = []
        for system in self.project.apache_systems():
            available.extend(
                str(value)
                for value in (getattr(system, "id", ""), getattr(system, "name", ""))
                if value
            )
        if system_id not in available:
            raise VeMutationError(
                "Configured HVAC system '{}' is not available".format(system_id)
            )
        for body in self._expected_bodies(expected_geometry):
            room_data = body.get_room_data()
            system_data = dict(room_data.get_apache_systems())
            system_data["HVAC_system"] = system_id
            room_data.set_apache_systems(system_data)
            assigned = str(room_data.get_apache_systems().get("HVAC_system", ""))
            if assigned != system_id:
                raise VeMutationError(
                    "HVAC system assignment did not persist for room '{}'".format(
                        body.name
                    )
                )

    def assign_weather(self, weather_file: str) -> None:
        """Persist the weather selection and verify it remains readable."""

        locate = self.iesve.VELocate()
        try:
            if locate.open_wea_data() < 0:
                raise VeMutationError("VELocate.open_wea_data returned failure")
            locate.set({"weather_file": weather_file})
            locate.save_and_close()
        except VeMutationError:
            raise
        except Exception as exc:
            try:
                locate.close_wea_data()
            except Exception:
                pass
            raise VeMutationError("Weather assignment failed: {}".format(exc)) from exc

        assigned, readable = self._weather_state()
        if not readable or not (
            assigned == weather_file
            or assigned.replace("\\", "/").endswith(
                weather_file.replace("\\", "/").split("/")[-1]
            )
        ):
            raise VeMutationError(
                "Weather verification failed (assigned='{}', readable={})".format(
                    assigned, readable
                )
            )

    def _weather_state(self) -> Tuple[str, bool]:
        """Return the assigned weather path and readability state."""

        locate = self.iesve.VELocate()
        assigned = ""
        try:
            if locate.open_wea_data() >= 0:
                assigned = str(locate.get().get("weather_file", ""))
                locate.close_wea_data()
        except Exception:
            try:
                locate.close_wea_data()
            except Exception:
                pass
        readable = False
        if assigned:
            reader = self.iesve.WeatherFileReader()
            try:
                readable = reader.open_weather_file(assigned) > 0
            except Exception:
                readable = False
            finally:
                try:
                    reader.close()
                except Exception:
                    pass
        return assigned, readable

    def _safe_version(self) -> str:
        """Return the VE version string, tolerating a missing accessor."""

        getter = getattr(self.project, "get_version", None)
        if getter is None:
            return "unknown"
        try:
            return str(getter())
        except Exception:
            return "unknown"

    def _construction_snapshots(
        self, parameters: ParameterRegistry
    ) -> Tuple[ConstructionSnapshot, ...]:
        """Read normalized snapshots for all configured constructions."""

        identifiers = sorted(
            {
                str(parameters.value(name))
                for name in (
                    "external_wall_construction_id",
                    "roof_construction_id",
                    "ground_floor_construction_id",
                    "internal_wall_construction_id",
                    "door_construction_id",
                    "glazing_construction_id",
                )
                if parameters.value(name)
            }
        )
        snapshots = []
        for identifier in identifiers:
            try:
                construction = self._get_construction(identifier)
                layers = list(construction.get_layers())
                material_descriptions_list = []
                for layer in layers:
                    try:
                        material = layer.get_material(bool(construction.opaque))
                    except Exception:
                        material = None
                    if material is not None:
                        material_descriptions_list.append(str(material))
                    elif self._construction_layer_is_resolved(construction, layer):
                        material_descriptions_list.append("<CAVITY>")
                    else:
                        material_descriptions_list.append("")
                material_descriptions = tuple(material_descriptions_list)
                properties = _enum_or_value(dict(construction.get_properties()))
                try:
                    u_value = float(construction.get_u_factor(self._uvalue_type_iso()))
                except Exception:
                    candidate = properties.get("u_value", properties.get("u_factor"))
                    u_value = float(candidate) if candidate is not None else None
                snapshots.append(
                    ConstructionSnapshot(
                        identifier=str(construction.id),
                        reference=str(construction.reference),
                        category=str(construction.category),
                        layer_count=len(layers),
                        material_ids=material_descriptions,
                        properties=properties,
                        u_value_w_m2k=u_value,
                        valid=bool(layers) and all(material_descriptions),
                    )
                )
            except Exception:
                snapshots.append(
                    ConstructionSnapshot(
                        identifier=identifier,
                        reference="",
                        category="",
                        layer_count=0,
                        material_ids=(),
                        properties={},
                        u_value_w_m2k=None,
                        valid=False,
                    )
                )
        return tuple(snapshots)

    def _material_snapshots(self) -> Tuple[MaterialSnapshot, ...]:
        """Read normalized snapshots for available project materials."""

        project = self._cdb_project()
        snapshots = []
        try:
            cdb_project_cls = getattr(self.iesve, "VECdbProject", None)
            material_categories = getattr(
                cdb_project_cls, "material_categories", None
            )
            if material_categories is None:
                material_categories = getattr(
                    self.iesve, "material_categories", None
                )
            all_materials = getattr(material_categories, "all", None)
            if all_materials is None:
                raise VeMutationError(
                    "VE material_categories.all enum is unavailable"
                )
            identifiers = project.get_material_ids(all_materials)
        except Exception:
            identifiers = []
        for identifier in identifiers:
            try:
                material = project.get_material(identifier)
                properties = _enum_or_value(dict(material.get_properties()))
                snapshots.append(
                    MaterialSnapshot(
                        identifier=str(identifier),
                        description=str(properties.get("description", "")),
                        properties=properties,
                        valid=bool(properties),
                    )
                )
            except Exception:
                snapshots.append(
                    MaterialSnapshot(
                        identifier=str(identifier),
                        description="",
                        properties={},
                        valid=False,
                    )
                )
        return tuple(snapshots)

    def _template_snapshots(self) -> Tuple[TemplateSnapshot, ...]:
        """Read normalized snapshots for every available thermal template."""

        snapshots = []
        for handle, template in thermal_templates(
            self.project, assigned=False
        ).items():
            gains = []
            for gain in template.get_casual_gains():
                try:
                    gains.append(_enum_or_value(gain.get()))
                except Exception:
                    gains.append({"read_error": str(gain)})
            air_exchanges = []
            for exchange in template.get_air_exchanges():
                try:
                    air_exchanges.append(_enum_or_value(exchange.get()))
                except Exception:
                    air_exchanges.append({"read_error": str(exchange)})
            snapshots.append(
                TemplateSnapshot(
                    handle=str(handle),
                    name=str(template.name),
                    standard=str(template.standard),
                    room_conditions=_enum_or_value(template.get_room_conditions()),
                    system_data=_enum_or_value(template.get_apache_systems()),
                    gains=tuple(gains),
                    air_exchanges=tuple(air_exchanges),
                )
            )
        return tuple(snapshots)

    def snapshot(
        self, expected_geometry: GeometryModel, parameters: ParameterRegistry
    ) -> ModelSnapshot:
        """Read rooms, assignments, weather, CDB, and templates from VE."""

        template_name_by_handle = {
            str(handle): str(template.name)
            for handle, template in thermal_templates(
                self.project, assigned=False
            ).items()
        }
        rooms = []
        for body in self._room_bodies():
            areas = body.get_areas()
            room_data = body.get_room_data()
            general = room_data.get_general()
            system_data = room_data.get_apache_systems()
            thermal_template_name = str(
                general.get("thermal_template_name", "")
            )
            if not thermal_template_name:
                raw_template = str(general.get("thermal_template", ""))
                thermal_template_name = template_name_by_handle.get(
                    raw_template, raw_template
                )
            surfaces = []
            for surface in body.get_surfaces():
                properties = surface.get_properties()
                opening_snapshots = []
                for opening in surface.get_openings():
                    opening_construction = opening.get_construction()
                    opening_snapshots.append(
                        OpeningSnapshot(
                            identifier=str(opening.get_id()),
                            opening_type=str(
                                opening.get_properties().get("type", "")
                            ),
                            area_m2=float(
                                opening.get_properties().get("area", 0.0) or 0.0
                            ),
                            construction_id=(
                                self._construction_identifier(opening_construction)
                                if opening_construction
                                else ""
                            ),
                        )
                    )
                openings = tuple(opening_snapshots)
                adjacent = []
                for adjacency in surface.get_adjacencies():
                    try:
                        adjacent.append(str(adjacency.get_properties().get("body_id", "")))
                    except Exception:
                        continue
                surfaces.append(
                    SurfaceSnapshot(
                        identifier=str(
                            properties.get("id", properties.get("aps_handle", surface.index))
                        ),
                        surface_type=str(properties.get("type", surface.type)),
                        area_m2=float(properties.get("area", 0.0) or 0.0),
                        construction_ids=tuple(
                            self._construction_identifier(construction)
                            for construction in surface.get_constructions()
                        ),
                        adjacent_room_ids=tuple(identifier for identifier in adjacent if identifier),
                        openings=openings,
                    )
                )
            rooms.append(
                RoomSnapshot(
                    identifier=str(body.id),
                    name=str(body.name),
                    area_m2=float(areas.get("int_floor_area", 0.0) or 0.0)
                    + float(areas.get("ext_floor_area", 0.0) or 0.0),
                    volume_m3=float(areas.get("volume", 0.0) or 0.0),
                    thermal_template_name=thermal_template_name,
                    surfaces=tuple(surfaces),
                    hvac_system_id=str(system_data.get("HVAC_system", "")),
                )
            )
        weather_file, weather_readable = self._weather_state()
        return ModelSnapshot(
            project_name=self.project_name,
            project_path=str(self.project_path),
            ve_version=self._safe_version(),
            weather_file=weather_file,
            weather_readable=weather_readable,
            rooms=tuple(rooms),
            constructions=self._construction_snapshots(parameters),
            materials=self._material_snapshots(),
            templates=self._template_snapshots(),
            metadata={
                "real_model_id": str(self.model.id),
                "expected_generated_rooms": [
                    space.name for space in expected_geometry.spaces
                ],
                "source_api": "VE 2023 VEScript User Guide",
            },
        )
