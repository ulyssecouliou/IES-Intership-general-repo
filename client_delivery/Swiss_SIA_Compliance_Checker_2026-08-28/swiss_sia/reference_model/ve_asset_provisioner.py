"""Capability-gated creation of VE assets from a validated manifest.

This module deliberately contains the version-sensitive API calls. The rest
of the reference-model architecture depends only on the normalized receipt.
All setters are followed by read-back checks before downstream assignment.
"""

from dataclasses import dataclass
from enum import Enum
import logging
import math
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from .asset_manifest import (
    AirExchangeDefinition,
    AssetManifest,
    ConstructionDefinition,
    GainDefinition,
    MaterialDefinition,
    ProfileDefinition,
)
from .exceptions import VeApiUnavailableError, VeMutationError
from .ve_compat import thermal_templates

# Read-back comparison only: these tolerances cover one IEEE-754 float32
# storage round trip in the VE CDB.  They are not SIA compliance tolerances.
VE_FLOAT32_RELATIVE_TOLERANCE = 1.0e-7
VE_FLOAT32_ABSOLUTE_TOLERANCE = 1.0e-9
LOGGER = logging.getLogger("swiss_sia.reference_model")


def _serializable(value: Any) -> Any:
    """Normalize VE enum and container values for comparison and reports."""

    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): _serializable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_serializable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _values_match(expected: Any, actual: Any) -> bool:
    """Compare values after a non-regulatory VE float32 storage round trip."""

    expected = _serializable(expected)
    actual = _serializable(actual)
    if isinstance(expected, bool) or isinstance(actual, bool):
        return expected == actual
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return math.isclose(
            float(expected),
            float(actual),
            rel_tol=VE_FLOAT32_RELATIVE_TOLERANCE,
            abs_tol=VE_FLOAT32_ABSOLUTE_TOLERANCE,
        )
    if isinstance(expected, list) and isinstance(actual, list):
        return len(expected) == len(actual) and all(
            _values_match(left, right) for left, right in zip(expected, actual)
        )
    if isinstance(expected, Mapping) and isinstance(actual, Mapping):
        return all(
            key in actual and _values_match(value, actual[key])
            for key, value in expected.items()
        )
    return expected == actual


def _assert_subset(
    expected: Mapping[str, Any], actual: Mapping[str, Any], context: str
) -> None:
    """Fail when any written field is absent or changed during read-back."""

    mismatches = {
        key: {"expected": _serializable(value), "actual": _serializable(actual.get(key))}
        for key, value in expected.items()
        if key not in actual or not _values_match(value, actual.get(key))
    }
    if mismatches:
        raise VeMutationError("{} read-back mismatch: {}".format(context, mismatches))


def _normalise_record_type(value: Any) -> str:
    """Return a stable alphanumeric VE type label."""

    return "".join(character for character in str(value).lower() if character.isalnum())


def _selected_record_value(
    data: Mapping[str, Any], plural_key: str, scalar_key: str
) -> Any:
    """Resolve either a scalar value or the value in the selected VE units."""

    if scalar_key in data:
        return data[scalar_key]
    values = data.get(plural_key)
    if not isinstance(values, Mapping):
        return None
    try:
        units = int(data.get("units_val", 0))
    except (TypeError, ValueError):
        units = 0
    return values.get(units, values.get(str(units)))


def _gain_record_family(data: Mapping[str, Any]) -> str:
    """Classify a template gain independently of VE's display name."""

    label = _normalise_record_type(
        "{} {} {}".format(
            data.get("type_str", ""),
            data.get("type_val", ""),
            data.get("name", ""),
        )
    )
    if "people" in label:
        return "people"
    if "light" in label:
        return "lighting"
    return "energy"


def _gain_record_mismatches(
    expected: Mapping[str, Any], actual: Mapping[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """Compare simulation-relevant gain data while ignoring display names."""

    mismatches: Dict[str, Dict[str, Any]] = {}
    scalar_to_plural = {
        "max_power_consumption": "max_power_consumptions",
        "max_sensible_gain": "max_sensible_gains",
        "max_latent_gain": "max_latent_gains",
        "occupancy_density": "occupancies",
    }
    for scalar_key, plural_key in scalar_to_plural.items():
        if scalar_key not in expected:
            continue
        actual_value = _selected_record_value(actual, plural_key, scalar_key)
        if not _values_match(expected[scalar_key], actual_value):
            mismatches[scalar_key] = {
                "expected": _serializable(expected[scalar_key]),
                "actual": _serializable(actual_value),
            }
    for key in (
        "units_val",
        "radiant_fraction",
        "pc_convective_gain",
        "diversity_factor",
        "variation_profile",
    ):
        if key in expected and not _values_match(expected[key], actual.get(key)):
            mismatches[key] = {
                "expected": _serializable(expected[key]),
                "actual": _serializable(actual.get(key)),
            }
    return mismatches


def _exchange_record_mismatches(
    expected: Mapping[str, Any], actual: Mapping[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """Compare the effective flow, units, boundary and schedule."""

    mismatches: Dict[str, Dict[str, Any]] = {}
    expected_flow = expected.get("max_flow")
    actual_flow = _selected_record_value(actual, "max_flows", "max_flow")
    if expected_flow is not None and not _values_match(expected_flow, actual_flow):
        mismatches["max_flow"] = {
            "expected": _serializable(expected_flow),
            "actual": _serializable(actual_flow),
        }
    for key in ("units_val", "variation_profile", "adjacent_condition_val"):
        if key in expected and not _values_match(expected[key], actual.get(key)):
            mismatches[key] = {
                "expected": _serializable(expected[key]),
                "actual": _serializable(actual.get(key)),
            }
    return mismatches


def _exchange_record_family(data: Mapping[str, Any]) -> str:
    """Return the normalized physical family of an air-exchange record."""

    return _normalise_record_type(
        data.get("type_val", data.get("type_str", data.get("name", "")))
    )


def _template_links_semantically_match(
    expected_records: Iterable[Any], actual_records: Iterable[Any], kind: str
) -> Tuple[bool, Dict[str, Any]]:
    """Compare linked template records by physics rather than display names."""

    expected_data = [dict(record.get()) for record in expected_records]
    actual_data = [dict(record.get()) for record in actual_records]
    if kind == "gain":
        key_function = _gain_record_family
        compare = _gain_record_mismatches
    else:
        key_function = _exchange_record_family
        compare = _exchange_record_mismatches

    def index(records: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        result: Dict[str, List[Dict[str, Any]]] = {}
        for data in records:
            result.setdefault(key_function(data), []).append(data)
        return result

    expected_by_key = index(expected_data)
    actual_by_key = index(actual_data)
    if set(expected_by_key) != set(actual_by_key):
        return False, {
            "expected_keys": sorted(expected_by_key),
            "actual_keys": sorted(actual_by_key),
        }
    details: Dict[str, Any] = {}
    for key in sorted(expected_by_key):
        if len(expected_by_key[key]) != 1 or len(actual_by_key[key]) != 1:
            details[key] = {
                "expected_count": len(expected_by_key[key]),
                "actual_count": len(actual_by_key[key]),
            }
            continue
        mismatches = compare(expected_by_key[key][0], actual_by_key[key][0])
        if mismatches:
            details[key] = mismatches
    return not details, details


def _canonical_daily_profile_data(value: Any) -> Any:
    """Normalize VE's canonical marker for an unused daily-profile formula.

    VE 2025.2 persists an empty formula string as ``"-"``.  Only that third
    field is normalized; breakpoint times and values remain strictly compared.
    """

    normalized = _serializable(value)
    if not isinstance(normalized, list):
        return normalized
    result = []
    for row in normalized:
        if isinstance(row, list) and len(row) == 3 and row[2] in ("", "-"):
            result.append([row[0], row[1], "-"])
        else:
            result.append(row)
    return result


def _canonical_profile_data(profile_type: str, value: Any) -> Any:
    """Return the exact VE read-back comparison form for one profile type.

    Only daily profiles have a proven VE 2025.2 storage canonicalization: an
    empty breakpoint formula is persisted as ``"-"``.  Group, compact and
    free-form profile payloads are otherwise compared exactly after generic
    enum/container serialization.  No calendar or regulatory tolerance is
    applied here.
    """

    normalized_type = str(profile_type).strip().lower()
    if normalized_type == "daily":
        return _canonical_daily_profile_data(value)
    return _serializable(value)


def _profile_reference_keys(value: Any) -> set:
    """Collect logical ``profile_ref`` dependencies recursively."""

    references = set()
    if isinstance(value, Mapping):
        if set(value) == {"profile_ref"}:
            references.add(str(value["profile_ref"]))
        else:
            for child in value.values():
                references.update(_profile_reference_keys(child))
    elif isinstance(value, (list, tuple)):
        for child in value:
            references.update(_profile_reference_keys(child))
    return references


def _profile_dependency_layers(
    definitions: Sequence[ProfileDefinition],
) -> Tuple[Tuple[ProfileDefinition, ...], ...]:
    """Return stable topological layers before any VE profile is created."""

    by_key = {definition.key: definition for definition in definitions}
    if len(by_key) != len(definitions):
        raise VeMutationError("Duplicate logical profile keys")
    dependencies = {
        definition.key: _profile_reference_keys(definition.data.value)
        for definition in definitions
    }
    unknown = sorted(
        {
            dependency
            for values in dependencies.values()
            for dependency in values
            if dependency not in by_key
        }
    )
    if unknown:
        raise VeMutationError("Unknown runtime profile references: {}".format(unknown))
    ordered_keys = [definition.key for definition in definitions]
    remaining = set(ordered_keys)
    resolved = set()
    layers = []
    while remaining:
        ready_keys = [
            key
            for key in ordered_keys
            if key in remaining and dependencies[key] <= resolved
        ]
        if not ready_keys:
            raise VeMutationError(
                "Cyclic runtime profile references: {}".format(sorted(remaining))
            )
        layers.append(tuple(by_key[key] for key in ready_keys))
        resolved.update(ready_keys)
        remaining.difference_update(ready_keys)
    return tuple(layers)


@dataclass(frozen=True)
class ProvisioningReceipt:
    """Normalized identifiers and evidence created during one asset run."""

    manifest_path: str
    manifest_checksum: str
    parameter_overrides: Dict[str, Dict[str, Any]]
    profile_ids: Dict[str, str]
    material_ids: Dict[str, str]
    construction_ids: Dict[str, str]
    gain_ids: Dict[str, str]
    air_exchange_names: Dict[str, str]
    template_name: str
    template_handle: str
    apache_system_id: str = ""
    compatibility_warnings: Tuple[Dict[str, Any], ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        """Return the complete provisioning receipt as serializable data."""

        return {
            "manifest_path": self.manifest_path,
            "manifest_checksum": self.manifest_checksum,
            "parameter_overrides": self.parameter_overrides,
            "profile_ids": self.profile_ids,
            "material_ids": self.material_ids,
            "construction_ids": self.construction_ids,
            "gain_ids": self.gain_ids,
            "air_exchange_names": self.air_exchange_names,
            "template_name": self.template_name,
            "template_handle": self.template_handle,
            "apache_system_id": self.apache_system_id,
            "compatibility_warnings": list(self.compatibility_warnings),
        }


class IesVeAssetProvisioner:
    """Create CDB and thermal-template assets in an active VE project."""

    # Source-traced calculation assumptions that belong in the compliance
    # manifest/report but are not writable VEThermalTemplate room-condition
    # options.  Keep this list deliberately narrow: every entry needs runtime
    # evidence from VE and must emit an explicit compatibility warning.
    AUDIT_ONLY_ROOM_CONDITION_KEYS = frozenset({"solar_reflected_fraction"})

    PROFILE_UNIT_MEMBERS = {
        -1: ("none",),
        0: ("metric",),
        1: ("ip", "imperial"),
    }

    GAIN_ENUM_PATHS = {
        "people": ("PeopleGain.PeopleGain_type", "PeopleGain_type"),
        "lighting": ("LightingGain.LightingGain_type", "LightingGain_type"),
        "energy": ("EnergyGain.EnergyGain_type", "EnergyGain_type"),
    }
    GAIN_CREATE_MEMBER_ALIASES = {
        ("people", "people"): "people",
        ("lighting", "fluorescent"): "fluorescent_lighting",
        ("lighting", "tungsten"): "tungsten_lighting",
        ("lighting", "general"): "general_lighting",
        ("lighting", "task"): "task_lighting",
        ("lighting", "display"): "display_lighting",
        ("lighting", "process"): "process_lighting",
        ("energy", "data_centre_equipment"): "data_center_equipment",
    }
    GAIN_UNITS = {
        "people": {"square_metres_per_person": 0, "people": 1},
        "lighting": {"watts_per_square_metre": 0, "watts": 1, "lux": 2},
        "energy": {"watts_per_square_metre": 0, "watts": 1},
    }
    AIR_EXCHANGE_MEMBER_ALIASES = {
        "auxiliary_ventilation": "mechanical_ventilation",
    }
    AIR_UNIT_MEMBERS = {
        "ach": "ac_per_h",
        "litres_per_second": "l_per_s",
        "litres_per_second_per_square_metre": "l_per_s_per_m2",
        "litres_per_second_per_person": "l_per_s_per_person",
        "litres_per_second_per_square_metre_facade": "l_per_s_m2_facade",
    }
    AIR_ADJACENT_MEMBER_ALIASES = {
        "external_air_offset": "external_air_and_offset_temp",
        "adjacent": "from_adjacent_room",
        "profile": "temperature_from_profile",
    }

    def __init__(self, iesve_module: Any, project: Any, cdb_project: Any):
        """Bind the provisioner to VE runtime and active project objects."""

        self.iesve = iesve_module
        self.project = project
        self.cdb_project = cdb_project
        self._compatibility_warnings: List[Dict[str, Any]] = []
        self._constant_on_profile_ids: set[str] = set()

    def _verify_layer_properties(
        self,
        definition: ConstructionDefinition,
        layer_index: int,
        expected: Mapping[str, Any],
        actual: Mapping[str, Any],
    ) -> None:
        """Verify a layer while exposing narrowly observed glazed persistence gaps.

        VE can accept a positive thickness for a glazed layer during creation,
        then return ``0.0`` after the project is persisted and reopened.  This
        observed canonicalization is tolerated only for that single property
        on a glazed construction. VE also persists glazed-layer resistance at
        five decimal places. Each observed canonicalization is accepted only
        when the read-back exactly matches its native rounded representation.
        Requested values remain in the traced manifest and each mismatch
        becomes a machine-readable WARNING; all other construction, material,
        optical, and layer fields remain strict.
        """

        remaining = dict(expected)
        expected_thickness = remaining.get("thickness")
        actual_thickness = actual.get("thickness")
        native_glazed_thickness = (
            definition.construction_class == "glazed"
            and isinstance(expected_thickness, (int, float))
            and float(expected_thickness) > 0.0
            and isinstance(actual_thickness, (int, float))
            and _values_match(float(actual_thickness), 0.0)
        )
        if native_glazed_thickness:
            remaining.pop("thickness")
            warning = {
                "code": "VE-GLAZED-LAYER-THICKNESS-NOT-PERSISTED",
                "construction_key": definition.key,
                "layer_index": layer_index,
                "material_key": definition.layers[layer_index].material_key,
                "requested_thickness_m": float(expected_thickness),
                "ve_readback_thickness_m": float(actual_thickness),
                "message": (
                    "VE returned 0.0 m after persisting the glazed-layer thickness; "
                    "the requested value remains source-traced in the asset manifest, "
                    "but whole-window thermal calibration requires independent VE "
                    "U-value verification before certification"
                ),
            }
            if warning not in self._compatibility_warnings:
                self._compatibility_warnings.append(warning)
            LOGGER.warning(
                "asset_provisioning | constructions | %s | WARNING | requested "
                "glazed thickness=%s m, VE read-back=%s m",
                definition.key,
                expected_thickness,
                actual_thickness,
            )
        expected_resistance = remaining.get("resistance")
        actual_resistance = actual.get("resistance")
        canonical_resistance = None
        native_glazed_resistance = False
        if (
            definition.construction_class == "glazed"
            and isinstance(expected_resistance, (int, float))
            and isinstance(actual_resistance, (int, float))
        ):
            canonical_resistance = round(float(expected_resistance), 5)
            native_glazed_resistance = not _values_match(
                float(expected_resistance), float(actual_resistance)
            ) and _values_match(canonical_resistance, float(actual_resistance))
        if native_glazed_resistance:
            remaining.pop("resistance")
            warning = {
                "code": "VE-GLAZED-LAYER-RESISTANCE-ROUNDED-5DP",
                "construction_key": definition.key,
                "layer_index": layer_index,
                "material_key": definition.layers[layer_index].material_key,
                "requested_resistance_m2k_w": float(expected_resistance),
                "ve_readback_resistance_m2k_w": float(actual_resistance),
                "canonical_5dp": canonical_resistance,
                "message": (
                    "VE persisted glazed-layer thermal resistance at five "
                    "decimal places. The source precision remains in the asset "
                    "manifest; whole-window U-value validation remains strict "
                    "and independent."
                ),
            }
            if warning not in self._compatibility_warnings:
                self._compatibility_warnings.append(warning)
            LOGGER.warning(
                "asset_provisioning | constructions | %s | WARNING | glazed "
                "layer %s resistance rounded to five decimals: requested=%s, "
                "VE read-back=%s",
                definition.key,
                layer_index,
                expected_resistance,
                actual_resistance,
            )
        _assert_subset(
            remaining,
            actual,
            "existing construction {} layer".format(definition.key),
        )

    def _verify_material_properties(
        self,
        definition: MaterialDefinition,
        expected: Mapping[str, Any],
        actual: Mapping[str, Any],
        context: str,
    ) -> None:
        """Verify materials with VE's glass-only three-decimal optical storage."""

        remaining = dict(expected)
        minimum_fields: Dict[str, Dict[str, float]] = {}
        for key in ("density", "specific_heat_capacity"):
            requested = remaining.get(key)
            persisted = actual.get(key)
            if (
                isinstance(requested, (int, float))
                and float(requested) == 0.0
                and isinstance(persisted, (int, float))
                and _values_match(1.0e-6, float(persisted))
            ):
                remaining.pop(key)
                minimum_fields[key] = {
                    "requested": 0.0,
                    "ve_readback": float(persisted),
                    "ve_minimum": 1.0e-6,
                }
        if minimum_fields:
            warning = {
                "code": "VE-MATERIAL-ZERO-THERMAL-MASS-MINIMUM",
                "message": (
                    "VE persisted a source-traced zero thermal-mass material "
                    "property at its 1e-6 numerical minimum. The normative zero "
                    "remains in the manifest; only this exact VE canonical value "
                    "is accepted during read-back."
                ),
                "material_key": definition.key,
                "fields": minimum_fields,
            }
            if warning not in self._compatibility_warnings:
                self._compatibility_warnings.append(warning)
            LOGGER.warning(
                "asset_provisioning | materials | %s | WARNING | zero "
                "thermal-mass properties persisted at VE's 1e-6 numerical "
                "minimum: %s",
                definition.key,
                minimum_fields,
            )
        rounded_fields: Dict[str, Dict[str, float]] = {}
        if definition.category == "glass":
            for key in ("transmittance", "visible_transmittance"):
                requested = remaining.get(key)
                persisted = actual.get(key)
                if not isinstance(requested, (int, float)) or not isinstance(
                    persisted, (int, float)
                ):
                    continue
                canonical = round(float(requested), 3)
                if not _values_match(
                    float(requested), float(persisted)
                ) and _values_match(canonical, float(persisted)):
                    remaining.pop(key)
                    rounded_fields[key] = {
                        "requested": float(requested),
                        "ve_readback": float(persisted),
                        "canonical_3dp": canonical,
                    }
        if rounded_fields:
            warning = {
                "code": "VE-GLASS-OPTICAL-PROPERTY-ROUNDED-3DP",
                "message": (
                    "VE persisted glass optical material properties at three "
                    "decimal places. The source precision remains in the asset "
                    "manifest; downstream whole-window g-value validation "
                    "remains strict and independent."
                ),
                "material_key": definition.key,
                "fields": rounded_fields,
            }
            if warning not in self._compatibility_warnings:
                self._compatibility_warnings.append(warning)
            LOGGER.warning(
                "asset_provisioning | materials | %s | WARNING | glass optical "
                "properties rounded to three decimals: %s",
                definition.key,
                rounded_fields,
            )
        _assert_subset(remaining, actual, context)

    def _verify_construction_properties(
        self,
        definition: ConstructionDefinition,
        expected: Mapping[str, Any],
        actual: Mapping[str, Any],
        context: str,
    ) -> None:
        """Verify construction properties after documented VE canonicalisation.

        VE 2025 persists construction surface resistances to four decimal
        places.  This is a storage/read-back rule only: the source value stays
        in the manifest and later U-value checks remain independent and strict.
        """

        remaining = dict(expected)
        rounded_surface_resistances: Dict[str, Dict[str, float]] = {}
        for key in (
            "inside_surface_resistance",
            "outside_surface_resistance",
        ):
            requested_resistance = remaining.get(key)
            persisted_resistance = actual.get(key)
            if not isinstance(requested_resistance, (int, float)) or not isinstance(
                persisted_resistance, (int, float)
            ):
                continue
            canonical_resistance = round(float(requested_resistance), 4)
            if not _values_match(
                float(requested_resistance), float(persisted_resistance)
            ) and _values_match(canonical_resistance, float(persisted_resistance)):
                remaining.pop(key)
                rounded_surface_resistances[key] = {
                    "requested": float(requested_resistance),
                    "ve_readback": float(persisted_resistance),
                    "canonical_4dp": canonical_resistance,
                }
        if rounded_surface_resistances:
            warning = {
                "code": "VE-CONSTRUCTION-SURFACE-RESISTANCE-ROUNDED-4DP",
                "message": (
                    "VE persisted construction surface resistances at four "
                    "decimal places. The source precision remains in the asset "
                    "manifest; construction U-value validation remains strict "
                    "and independent."
                ),
                "construction_key": definition.key,
                "fields": rounded_surface_resistances,
            }
            if warning not in self._compatibility_warnings:
                self._compatibility_warnings.append(warning)
            LOGGER.warning(
                "asset_provisioning | constructions | %s | WARNING | surface "
                "resistances rounded to four decimals: %s",
                definition.key,
                rounded_surface_resistances,
            )

        requested = remaining.get("visible_light_transmittance")
        persisted = actual.get("visible_light_transmittance")
        rounded = False
        canonical = None
        if (
            definition.construction_class == "glazed"
            and isinstance(requested, (int, float))
            and isinstance(persisted, (int, float))
        ):
            canonical = round(float(requested), 4)
            rounded = not _values_match(
                float(requested), float(persisted)
            ) and _values_match(canonical, float(persisted))
        if rounded:
            remaining.pop("visible_light_transmittance")
            warning = {
                "code": "VE-GLAZED-CONSTRUCTION-VLT-ROUNDED-4DP",
                "message": (
                    "VE persisted glazed-construction visible light "
                    "transmittance at four decimal places. The source value "
                    "remains in the manifest; energy compliance does not rely "
                    "on this daylighting proxy."
                ),
                "construction_key": definition.key,
                "requested_visible_light_transmittance": float(requested),
                "ve_readback_visible_light_transmittance": float(persisted),
                "canonical_4dp": canonical,
            }
            if warning not in self._compatibility_warnings:
                self._compatibility_warnings.append(warning)
            LOGGER.warning(
                "asset_provisioning | constructions | %s | WARNING | visible "
                "light transmittance rounded to four decimals: requested=%s, "
                "VE read-back=%s",
                definition.key,
                requested,
                persisted,
            )
        _assert_subset(remaining, actual, context)

    def check_capabilities(self) -> Dict[str, bool]:
        """Verify every creation and persistence method used by create mode."""

        construction_class = getattr(self.iesve, "VECdbConstruction", object)
        layer_class = getattr(self.iesve, "VECdbLayer", object)
        capabilities = {
            "VEProject.create_profile": hasattr(self.project, "create_profile"),
            "VEProject.save_profiles": hasattr(self.project, "save_profiles"),
            "VEProject.create_casual_gain": hasattr(self.project, "create_casual_gain"),
            "VEProject.casual_gains": hasattr(self.project, "casual_gains"),
            "VEProject.create_air_exchange": hasattr(self.project, "create_air_exchange"),
            "VEProject.air_exchanges": hasattr(self.project, "air_exchanges"),
            "VEProject.create_thermal_template": hasattr(
                self.project, "create_thermal_template"
            ),
            "VECdbProject.create_material": hasattr(self.cdb_project, "create_material"),
            "VECdbProject.get_material": hasattr(self.cdb_project, "get_material"),
            "VECdbProject.get_material_ids": hasattr(
                self.cdb_project, "get_material_ids"
            ),
            "VECdbProject.create_construction": hasattr(
                self.cdb_project, "create_construction"
            ),
            "VECdbProject.get_construction": hasattr(
                self.cdb_project, "get_construction"
            ),
            "VECdbProject.get_construction_ids": hasattr(
                self.cdb_project, "get_construction_ids"
            ),
            "VECdbConstruction.delete_layer": hasattr(construction_class, "delete_layer"),
            "VECdbLayer.get_id": hasattr(layer_class, "get_id"),
        }
        missing = sorted(name for name, present in capabilities.items() if not present)
        if missing:
            raise VeApiUnavailableError(
                "VE asset create mode is unavailable; missing capabilities: {}".format(
                    missing
                )
            )
        return capabilities

    def _resolve_path(self, path: str) -> Any:
        """Resolve one dotted runtime attribute path from the iesve module."""

        current = self.iesve
        for part in path.split("."):
            if not hasattr(current, part):
                raise AttributeError(path)
            current = getattr(current, part)
        return current

    def _resolve_enum(
        self, container_paths: Sequence[str], member_names: Sequence[str], context: str
    ) -> Any:
        """Resolve an enum member across documented API layout variants."""

        attempted = []
        for container_path in container_paths:
            try:
                container = self._resolve_path(container_path)
            except AttributeError:
                attempted.append(container_path)
                continue
            for member_name in member_names:
                if hasattr(container, member_name):
                    return getattr(container, member_name)
            attempted.append("{}.[{}]".format(container_path, ",".join(member_names)))
        raise VeApiUnavailableError(
            "Unable to resolve VE enum for {} (attempted {})".format(context, attempted)
        )

    def _resolve_runtime_value(
        self, value: Any, profile_ids: Mapping[str, str], apache_system_id: str
    ) -> Any:
        """Resolve logical profile, system, and explicit enum markers recursively."""

        if isinstance(value, Mapping):
            if set(value) == {"profile_ref"}:
                key = str(value["profile_ref"])
                if key not in profile_ids:
                    raise VeMutationError(
                        "Unknown runtime profile reference: {}".format(key)
                    )
                return profile_ids[key]
            if set(value) == {"apache_system_ref"}:
                if value["apache_system_ref"] is not True or not apache_system_id:
                    raise VeMutationError("Apache system reference cannot be resolved")
                return apache_system_id
            if set(value) == {"ve_enum"}:
                path = str(value["ve_enum"])
                try:
                    return self._resolve_path(path)
                except AttributeError as exc:
                    raise VeApiUnavailableError(
                        "Manifest VE enum is unavailable: {}".format(path)
                    ) from exc
            return {
                str(key): self._resolve_runtime_value(item, profile_ids, apache_system_id)
                for key, item in value.items()
            }
        if isinstance(value, list):
            return [
                self._resolve_runtime_value(item, profile_ids, apache_system_id)
                for item in value
            ]
        return value

    def _ensure_no_existing_template(self, name: str) -> None:
        """Reject template-name collisions before creating any thermal assets."""

        matches = [
            template
            for template in thermal_templates(self.project, assigned=False).values()
            if str(template.name) == name
        ]
        if matches:
            raise VeMutationError(
                "Thermal template already exists and on_existing='fail': {}".format(name)
            )

    def _existing_profiles(self) -> Dict[str, List[Tuple[str, Any]]]:
        """Index profiles by reference while preserving safe mapping IDs.

        Existing Boost.Python profile proxies are not introspected for an ID:
        VE already supplies the persistent identifier as the collection key.
        Some VE 2025.2 builds can terminate the host process when an unsupported
        attribute is queried on an existing DailyProfile proxy.
        """

        existing: Dict[str, List[Tuple[str, Any]]] = {}
        try:
            collections = self.project.profiles()
            for collection in collections:
                for identifier, profile in collection.items():
                    for attribute in ("reference", "name"):
                        value = getattr(profile, attribute, None)
                        if value:
                            existing.setdefault(str(value), []).append(
                                (str(identifier), profile)
                            )
                            break
        except Exception as exc:
            raise VeMutationError(
                "Unable to inspect existing profiles before creation: {}".format(exc)
            ) from exc
        return existing

    def _profile_id(self, profile: Any) -> str:
        """Resolve the persistent ID of one newly created profile."""

        for attribute in ("id", "profile_id"):
            value = getattr(profile, attribute, None)
            if value:
                return str(value)
        try:
            for collection in self.project.profiles():
                for identifier, candidate in collection.items():
                    if candidate is profile:
                        return str(identifier)
        except Exception:
            pass
        raise VeMutationError("New profile has no resolvable persistent ID")

    def _profile_units(self, units: int) -> Any:
        """Return the typed ProfileUnits member required by recent VE builds.

        VE 2021 documented this argument as the integers -1/0/1.  VE 2025.2
        exposes a Boost.Python enum instead, normally at ``iesve.ProfileUnits``.
        Retain the documented integer fallback for older runtimes that do not
        expose either known enum-container layout.
        """

        if units not in self.PROFILE_UNIT_MEMBERS:
            raise VeMutationError("Unsupported VE profile-units value: {}".format(units))
        try:
            return self._resolve_enum(
                ("VEProject.ProfileUnits", "ProfileUnits"),
                self.PROFILE_UNIT_MEMBERS[units],
                "profile units {}".format(units),
            )
        except VeApiUnavailableError:
            return units

    @staticmethod
    def _profile_runtime_type(profile: Any) -> str:
        """Return the type exposed by a VE profile proxy without mutation."""

        class_name = type(profile).__name__.lower()
        for profile_type in ("daily", "weekly", "yearly", "compact", "freeform"):
            if profile_type in class_name:
                return profile_type
        predicates = (
            ("weekly", "is_weekly"),
            ("yearly", "is_yearly"),
            ("compact", "is_compact"),
            ("freeform", "is_freeform"),
        )
        observed_predicate = False
        for profile_type, predicate_name in predicates:
            predicate = getattr(profile, predicate_name, None)
            if not callable(predicate):
                continue
            observed_predicate = True
            try:
                if bool(predicate()):
                    return profile_type
            except Exception as exc:
                raise VeMutationError(
                    "Unable to inspect profile type through {}: {}".format(
                        predicate_name, exc
                    )
                ) from exc
        return "daily" if observed_predicate else "unknown"

    def _verify_profile_readback(
        self,
        definition: ProfileDefinition,
        expected_data: Any,
        profile: Any,
        context: str,
    ) -> None:
        """Verify profile proxy type and data after creation or reuse."""

        requested_type = definition.profile_type.strip().lower()
        actual_type = self._profile_runtime_type(profile)
        if actual_type != requested_type:
            raise VeMutationError(
                "{} type mismatch: requested {!r}, VE read-back {!r}".format(
                    context, requested_type, actual_type
                )
            )
        try:
            actual_data = profile.get_data()
        except Exception as exc:
            raise VeMutationError(
                "{} data read-back failed: {}".format(context, exc)
            ) from exc
        if not _values_match(
            _canonical_profile_data(requested_type, expected_data),
            _canonical_profile_data(requested_type, actual_data),
        ):
            raise VeMutationError(
                "{} data read-back mismatch: expected {!r}, actual {!r}".format(
                    context, expected_data, actual_data
                )
            )

    @staticmethod
    def _is_constant_one_daily_profile(
        definition: ProfileDefinition,
        resolved_data: Any,
    ) -> bool:
        """Return whether a source-traced daily profile is exactly one."""

        if definition.profile_type != "daily":
            return False
        if not isinstance(resolved_data, (list, tuple)) or not resolved_data:
            return False
        return all(
            isinstance(row, (list, tuple))
            and len(row) >= 2
            and _values_match(row[1], 1.0)
            for row in resolved_data
        )

    def _create_profiles(self, manifest: AssetManifest) -> Dict[str, str]:
        """Create or verify profiles in dependency order with exact read-back."""

        self._constant_on_profile_ids = set()
        existing = self._existing_profiles()
        references = [definition.reference for definition in manifest.profiles]
        if len(references) != len(set(references)):
            raise VeMutationError("Duplicate profile references in manifest")
        layers = _profile_dependency_layers(manifest.profiles)
        # Reject every collision before the first mutation.  This prevents an
        # early profile from being created before a later collision is found.
        for definition in manifest.profiles:
            matches = existing.get(definition.reference, [])
            if len(matches) > 1:
                raise VeMutationError(
                    "Profile reference is ambiguous and cannot be reused: {}".format(
                        definition.reference
                    )
                )
            if matches and manifest.on_existing == "fail":
                raise VeMutationError(
                    "Profile already exists and on_existing='fail': {}".format(
                        definition.reference
                    )
                )

        identifiers: Dict[str, str] = {}
        for layer in layers:
            created = []
            for definition in layer:
                resolved_data = self._resolve_runtime_value(
                    definition.data.value,
                    identifiers,
                    "",
                )
                matches = existing.get(definition.reference, [])
                if matches:
                    identifier, profile = matches[0]
                    self._verify_profile_readback(
                        definition,
                        resolved_data,
                        profile,
                        "existing profile {}".format(definition.key),
                    )
                    identifiers[definition.key] = identifier
                    if self._is_constant_one_daily_profile(definition, resolved_data):
                        self._constant_on_profile_ids.add(identifier)
                    continue
                try:
                    profile = self.project.create_profile(
                        definition.profile_type,
                        definition.reference,
                        definition.modulating,
                        self._profile_units(definition.units),
                    )
                    if not profile.set_data(resolved_data):
                        raise VeMutationError(
                            "VE rejected profile data for {}".format(definition.key)
                        )
                    created.append((definition, resolved_data, profile))
                except VeMutationError:
                    raise
                except Exception as exc:
                    raise VeMutationError(
                        "Profile creation failed for {}: {}".format(definition.key, exc)
                    ) from exc
            if created and not self.project.save_profiles():
                raise VeMutationError("VEProject.save_profiles returned failure")
            # VE 2025 may return a generic profile proxy from create_profile().
            # After save_profiles(), project.profiles() exposes the persistent
            # DailyProfile/GroupProfile proxy with the type predicates needed
            # for strict read-back. Always prefer that persisted object.
            persisted_by_reference = self._existing_profiles() if created else {}
            for definition, resolved_data, profile in created:
                persisted_matches = persisted_by_reference.get(definition.reference, [])
                if len(persisted_matches) > 1:
                    raise VeMutationError(
                        "Saved profile reference is ambiguous: {}".format(
                            definition.reference
                        )
                    )
                if persisted_matches:
                    persistent_id, profile = persisted_matches[0]
                else:
                    try:
                        persistent_id = self._profile_id(profile)
                    except VeMutationError as exc:
                        raise VeMutationError(
                            "Profile {} was saved but its persistent ID could "
                            "not be resolved: {}".format(definition.key, exc)
                        ) from exc
                self._verify_profile_readback(
                    definition,
                    resolved_data,
                    profile,
                    "profile {}".format(definition.key),
                )
                identifiers[definition.key] = persistent_id
                if self._is_constant_one_daily_profile(definition, resolved_data):
                    self._constant_on_profile_ids.add(identifiers[definition.key])
        return identifiers

    def provision_profiles(
        self,
        definitions: Sequence[ProfileDefinition],
        *,
        on_existing: str = "fail",
    ) -> Dict[str, str]:
        """Provision only a validated profile graph for a controlled probe.

        This narrow public boundary reuses the exact collision, dependency,
        type and read-back checks of full asset provisioning without requiring
        unrelated materials, constructions or templates.  It is intended for
        disposable-project runtime qualification and deliberately defaults to
        ``on_existing='fail'``.
        """

        if on_existing not in {"fail", "reuse_verified"}:
            raise VeMutationError(
                "Profile provisioning on_existing must be 'fail' or " "'reuse_verified'"
            )
        planned = tuple(definitions)
        if not planned:
            raise VeMutationError("At least one profile definition is required")
        for definition in planned:
            if definition.evidence.validation_error():
                raise VeMutationError(
                    "Profile {} has invalid source evidence".format(definition.key)
                )
            data_error = definition.data.validation_error()
            if data_error:
                raise VeMutationError(
                    "Profile {} data: {}".format(definition.key, data_error)
                )

        class _ProfilePlan:
            """Store the immutable source-traced plan for one VE daily profile."""

            def __init__(self, existing_mode: str):
                """Initialize a VE daily-profile creation plan from validated fields."""

                self.profiles = planned
                self.on_existing = existing_mode

        return self._create_profiles(_ProfilePlan(on_existing))

    def _material_identifier(
        self, material: Any, before_ids: Sequence[Any], category: Any
    ) -> str:
        """Resolve a created material ID using attributes or database delta."""

        for attribute in ("id", "material_id"):
            value = getattr(material, attribute, None)
            if value:
                return str(value)
        properties = dict(material.get_properties())
        for key in ("id", "material_id"):
            if properties.get(key):
                return str(properties[key])
        after_ids = list(self.cdb_project.get_material_ids(category))
        new_ids = [identifier for identifier in after_ids if identifier not in before_ids]
        if len(new_ids) == 1:
            return str(new_ids[0])
        raise VeMutationError("New material has no unambiguous persistent ID")

    def _create_materials(self, manifest: AssetManifest) -> Dict[str, str]:
        """Create missing CDB materials or strictly verify reusable ones."""

        identifiers: Dict[str, str] = {}
        enum_container = ("VECdbProject.material_categories", "material_categories")
        for definition in manifest.materials:
            category = self._resolve_enum(
                enum_container, (definition.category,), "material category"
            )
            before_ids = list(self.cdb_project.get_material_ids(category))
            properties = definition.raw_properties()
            description = str(properties.get("description", ""))
            matches = []
            for identifier in before_ids:
                try:
                    candidate = self.cdb_project.get_material(identifier)
                    actual = dict(candidate.get_properties())
                except Exception as exc:
                    raise VeMutationError(
                        "Unable to inspect existing material {}: {}".format(
                            identifier, exc
                        )
                    ) from exc
                if str(actual.get("description", "")) == description:
                    matches.append((str(identifier), actual))
            if len(matches) > 1:
                raise VeMutationError(
                    "Material description is ambiguous and cannot be reused: {}".format(
                        description
                    )
                )
            if matches:
                if manifest.on_existing == "fail":
                    raise VeMutationError(
                        "Material already exists and on_existing='fail': {}".format(
                            description
                        )
                    )
                identifier, actual = matches[0]
                # Name the description the lookup matched on and say that reuse
                # is what is being refused. On 2026-08-12 this raised for
                # xps_ground with expected 0.0 against actual 10.0/1400.0, and
                # the bare message sent the reader looking for a code defect;
                # the cause was a CDB material left by a superseded manifest
                # revision, which is a data state to reconcile, not a bug.
                self._verify_material_properties(
                    definition,
                    properties,
                    actual,
                    (
                        "existing material {key} (CDB id {identifier}, matched "
                        "on description {description!r}) cannot be reused"
                    ).format(
                        key=definition.key,
                        identifier=identifier,
                        description=description,
                    ),
                )
                identifiers[definition.key] = identifier
                continue
            try:
                material = self.cdb_project.create_material(category)
                material.set_properties(properties)
                actual = dict(material.get_properties())
                self._verify_material_properties(
                    definition,
                    properties,
                    actual,
                    "material {}".format(definition.key),
                )
                identifiers[definition.key] = self._material_identifier(
                    material, before_ids, category
                )
            except Exception as exc:
                if isinstance(exc, (VeMutationError, VeApiUnavailableError)):
                    raise
                raise VeMutationError(
                    "Material creation failed for {}: {}".format(definition.key, exc)
                ) from exc
        return identifiers

    def reconcile_existing_material(
        self, manifest: AssetManifest, material_key: str
    ) -> Dict[str, Any]:
        """Repair one exact-description CDB material with strict read-back.

        Normal ``reuse_verified`` remains non-mutating and fail-closed. This
        boundary is only for an explicitly requested recovery when a prior
        source-manifest revision left one uniquely identifiable material with
        stale properties.
        """

        if manifest.on_existing != "reuse_verified":
            raise VeMutationError(
                "Controlled material reconciliation requires "
                "on_existing='reuse_verified'"
            )
        definitions = [item for item in manifest.materials if item.key == material_key]
        if len(definitions) != 1:
            raise VeMutationError(
                "Expected exactly one material definition keyed '{}'; found {}".format(
                    material_key, len(definitions)
                )
            )
        definition = definitions[0]
        category = self._resolve_enum(
            ("VECdbProject.material_categories", "material_categories"),
            (definition.category,),
            "material category",
        )
        expected = definition.raw_properties()
        description = str(expected.get("description", ""))
        matches = []
        for identifier in self.cdb_project.get_material_ids(category):
            material = self.cdb_project.get_material(identifier)
            actual = dict(material.get_properties())
            if str(actual.get("description", "")) == description:
                matches.append((str(identifier), material, actual))
        if len(matches) != 1:
            raise VeMutationError(
                "Controlled material reconciliation requires exactly one CDB "
                "match for {!r}; found {}".format(description, len(matches))
            )
        identifier, material, before = matches[0]
        try:
            self._verify_material_properties(
                definition,
                expected,
                before,
                "existing reconciled material {}".format(material_key),
            )
            return {
                "status": "ALREADY_MATCHED",
                "material_key": material_key,
                "material_id": identifier,
                "changed": False,
                "before": _serializable(before),
                "after": _serializable(before),
                "compatibility_warnings": list(self._compatibility_warnings),
            }
        except VeMutationError:
            pass
        try:
            material.set_properties(expected)
            after = dict(material.get_properties())
            self._verify_material_properties(
                definition,
                expected,
                after,
                "reconciled material {}".format(material_key),
            )
        except Exception as exc:
            if isinstance(exc, (VeMutationError, VeApiUnavailableError)):
                raise
            raise VeMutationError(
                "Controlled material reconciliation failed for {}: {}".format(
                    material_key, exc
                )
            ) from exc
        return {
            "status": "RECONCILED_AND_VERIFIED",
            "material_key": material_key,
            "material_id": identifier,
            "changed": True,
            "before": _serializable(before),
            "after": _serializable(after),
            "compatibility_warnings": list(self._compatibility_warnings),
        }

    def reconcile_existing_construction(
        self, manifest: AssetManifest, construction_key: str
    ) -> Dict[str, Any]:
        """Repair one exact existing construction assembly and verify it.

        The assembly must be uniquely identified by construction class,
        category, layer count and the exact source-traced material IDs. No
        construction or layer is created, removed or reassigned here.
        """

        if manifest.on_existing != "reuse_verified":
            raise VeMutationError(
                "Controlled construction reconciliation requires "
                "on_existing='reuse_verified'"
            )
        definitions = [
            item for item in manifest.constructions if item.key == construction_key
        ]
        if len(definitions) != 1:
            raise VeMutationError(
                "Expected exactly one construction definition keyed '{}'; "
                "found {}".format(construction_key, len(definitions))
            )
        definition = definitions[0]

        material_ids: Dict[str, str] = {}
        material_definitions = {item.key: item for item in manifest.materials}
        for layer_definition in definition.layers:
            if layer_definition.is_cavity:
                continue
            material_definition = material_definitions.get(layer_definition.material_key)
            if material_definition is None:
                raise VeMutationError(
                    "Construction {} references missing material {}".format(
                        construction_key, layer_definition.material_key
                    )
                )
            category = self._resolve_enum(
                ("VECdbProject.material_categories", "material_categories"),
                (material_definition.category,),
                "material category",
            )
            expected_material = material_definition.raw_properties()
            description = str(expected_material.get("description", ""))
            matches = []
            for identifier in self.cdb_project.get_material_ids(category):
                material = self.cdb_project.get_material(identifier)
                actual = dict(material.get_properties())
                if str(actual.get("description", "")) == description:
                    matches.append((str(identifier), actual))
            if len(matches) != 1:
                raise VeMutationError(
                    "Construction reconciliation requires exactly one material "
                    "match for {!r}; found {}".format(description, len(matches))
                )
            identifier, actual = matches[0]
            self._verify_material_properties(
                material_definition,
                expected_material,
                actual,
                "construction reconciliation material {}".format(material_definition.key),
            )
            material_ids[layer_definition.material_key] = identifier

        category = self._resolve_enum(
            ("VECdbProject.element_categories", "element_categories"),
            (definition.category,),
            "construction category",
        )
        construction_class = self._resolve_enum(
            ("VECdbProject.construction_class", "construction_class"),
            (definition.construction_class,),
            "construction class",
        )
        expected_material_ids = [
            "" if layer.is_cavity else material_ids[layer.material_key]
            for layer in definition.layers
        ]
        matches = []
        for identifier in self.cdb_project.get_construction_ids(construction_class):
            construction = None
            for arguments in ((identifier, construction_class), (identifier,)):
                try:
                    construction = self.cdb_project.get_construction(*arguments)
                    if construction is not None:
                        break
                except Exception:
                    continue
            if construction is None:
                continue
            actual_category = getattr(construction, "category", None)
            if actual_category is None:
                actual_category = dict(construction.get_properties()).get("category")
            if not _values_match(category, actual_category):
                continue
            layers = list(construction.get_layers())
            if len(layers) != len(expected_material_ids):
                continue
            actual_material_ids = []
            for layer_definition, layer in zip(definition.layers, layers):
                if layer_definition.is_cavity:
                    actual_material_ids.append("")
                    continue
                material_id = ""
                for opaque_flag in (
                    definition.construction_class == "opaque",
                    definition.construction_class != "opaque",
                ):
                    try:
                        material = layer.get_material(opaque_flag)
                    except Exception:
                        continue
                    if material is None:
                        continue
                    material_properties = (
                        dict(material.get_properties())
                        if hasattr(material, "get_properties")
                        else {}
                    )
                    material_id = str(
                        material_properties.get(
                            "id", material_properties.get("material_id", "")
                        )
                        or getattr(material, "id", "")
                        or getattr(material, "material_id", "")
                    )
                    if material_id:
                        break
                actual_material_ids.append(material_id)
            if actual_material_ids == expected_material_ids:
                matches.append((str(identifier), construction, layers))
        if len(matches) != 1:
            raise VeMutationError(
                "Controlled construction reconciliation requires exactly one "
                "matching assembly for {}; found {}".format(
                    construction_key, len(matches)
                )
            )
        identifier, construction, layers = matches[0]
        expected = definition.raw_properties()
        before = dict(construction.get_properties())
        before_layers = [dict(layer.get_properties()) for layer in layers]
        already_matched = True
        try:
            self._verify_construction_properties(
                definition,
                expected,
                before,
                "existing reconciled construction {}".format(construction_key),
            )
            for index, (layer_definition, layer_data) in enumerate(
                zip(definition.layers, before_layers)
            ):
                self._verify_layer_properties(
                    definition,
                    index,
                    layer_definition.raw_properties(),
                    layer_data,
                )
        except VeMutationError:
            already_matched = False
        if already_matched:
            return {
                "status": "ALREADY_MATCHED",
                "construction_key": construction_key,
                "construction_id": identifier,
                "changed": False,
                "before": _serializable(before),
                "after": _serializable(before),
                "before_layers": _serializable(before_layers),
                "after_layers": _serializable(before_layers),
                "compatibility_warnings": list(self._compatibility_warnings),
            }
        try:
            if expected:
                construction.set_properties(expected)
            for layer_definition, layer in zip(definition.layers, layers):
                layer_properties = layer_definition.raw_properties()
                if layer_properties:
                    layer.set_properties(layer_properties)
            after = dict(construction.get_properties())
            after_layers = [dict(layer.get_properties()) for layer in layers]
            self._verify_construction_properties(
                definition,
                expected,
                after,
                "reconciled construction {}".format(construction_key),
            )
            for index, (layer_definition, layer_data) in enumerate(
                zip(definition.layers, after_layers)
            ):
                self._verify_layer_properties(
                    definition,
                    index,
                    layer_definition.raw_properties(),
                    layer_data,
                )
        except Exception as exc:
            if isinstance(exc, (VeMutationError, VeApiUnavailableError)):
                raise
            raise VeMutationError(
                "Controlled construction reconciliation failed for {}: {}".format(
                    construction_key, exc
                )
            ) from exc
        return {
            "status": "RECONCILED_AND_VERIFIED",
            "construction_key": construction_key,
            "construction_id": identifier,
            "changed": True,
            "before": _serializable(before),
            "after": _serializable(after),
            "before_layers": _serializable(before_layers),
            "after_layers": _serializable(after_layers),
            "compatibility_warnings": list(self._compatibility_warnings),
        }

    def _create_construction(
        self,
        manifest: AssetManifest,
        definition: ConstructionDefinition,
        material_ids: Mapping[str, str],
        allow_create: bool = True,
    ) -> Tuple[str, str]:
        """Create or verify one layered construction and return role plus ID."""

        category = self._resolve_enum(
            ("VECdbProject.element_categories", "element_categories"),
            (definition.category,),
            "construction category",
        )
        construction_class = self._resolve_enum(
            ("VECdbProject.construction_class", "construction_class"),
            (definition.construction_class,),
            "construction class",
        )
        expected_material_ids = [
            "" if layer.is_cavity else material_ids[layer.material_key]
            for layer in definition.layers
        ]
        reusable = []
        try:
            existing_ids = list(self.cdb_project.get_construction_ids(construction_class))
        except Exception as exc:
            raise VeMutationError(
                "Unable to inspect existing {} constructions: {}".format(
                    definition.construction_class, exc
                )
            ) from exc
        for identifier in existing_ids:
            construction = None
            for arguments in ((identifier, construction_class), (identifier,)):
                try:
                    construction = self.cdb_project.get_construction(*arguments)
                    if construction is not None:
                        break
                except Exception:
                    continue
            if construction is None:
                continue
            actual_category = getattr(construction, "category", None)
            if actual_category is None:
                actual_category = dict(construction.get_properties()).get("category")
            if not _values_match(category, actual_category):
                continue
            layers = list(construction.get_layers())
            if len(layers) != len(expected_material_ids):
                continue
            actual_material_ids = []
            for layer_definition, layer in zip(definition.layers, layers):
                if layer_definition.is_cavity:
                    actual_material_ids.append("")
                    continue
                material_id = ""
                for opaque_flag in (
                    definition.construction_class == "opaque",
                    definition.construction_class != "opaque",
                ):
                    try:
                        material = layer.get_material(opaque_flag)
                    except Exception:
                        continue
                    if material is None:
                        continue
                    if hasattr(material, "get_properties"):
                        material_properties = dict(material.get_properties())
                        material_id = str(
                            material_properties.get(
                                "id", material_properties.get("material_id", "")
                            )
                        )
                    if not material_id:
                        for attribute in ("id", "material_id"):
                            value = getattr(material, attribute, None)
                            if value:
                                material_id = str(value)
                                break
                    if material_id:
                        break
                actual_material_ids.append(material_id)
            if actual_material_ids == expected_material_ids:
                reusable.append((str(identifier), construction, layers))
        if len(reusable) > 1:
            raise VeMutationError(
                "Construction assembly is ambiguous and cannot be reused: {}".format(
                    definition.key
                )
            )
        if reusable:
            if manifest.on_existing == "fail":
                raise VeMutationError(
                    "Construction already exists and on_existing='fail': {}".format(
                        definition.key
                    )
                )
            identifier, construction, layers = reusable[0]
            properties = definition.raw_properties()
            self._verify_construction_properties(
                definition,
                properties,
                dict(construction.get_properties()),
                "existing construction {}".format(definition.key),
            )
            for layer_index, (layer_definition, layer) in enumerate(
                zip(definition.layers, layers)
            ):
                self._verify_layer_properties(
                    definition,
                    layer_index,
                    layer_definition.raw_properties(),
                    dict(layer.get_properties()),
                )
            return definition.assignment_parameter, identifier
        if not allow_create:
            raise VeMutationError(
                "Read-only verification found no reusable construction: {}".format(
                    definition.key
                )
            )
        try:
            construction = self.cdb_project.create_construction(category)
            construction.set_const_class(construction_class)
            # VE 2025.2 creates each new construction with one category-specific
            # default layer.  A glazed construction must never temporarily have
            # zero layers: deleting its only layer terminates VE.exe with a
            # native access violation.  Opaque defaults can be removed first;
            # glazed defaults are retained until all manifest layers exist.
            initial_layers = list(construction.get_layers())
            initial_layer_ids = []
            for initial_layer in initial_layers:
                if not hasattr(initial_layer, "get_id"):
                    raise VeApiUnavailableError(
                        "VECdbLayer.get_id is required to remove default layers"
                    )
                initial_layer_ids.append(initial_layer.get_id())
            if definition.construction_class == "opaque":
                for initial_layer_id in initial_layer_ids:
                    construction.delete_layer(initial_layer_id)
                if list(construction.get_layers()):
                    raise VeMutationError(
                        "Construction {} default layers could not be removed".format(
                            definition.key
                        )
                    )
            properties = definition.raw_properties()
            if properties:
                construction.set_properties(properties)
                self._verify_construction_properties(
                    definition,
                    properties,
                    dict(construction.get_properties()),
                    "construction {}".format(definition.key),
                )
            for layer_definition in definition.layers:
                material_id = material_ids[layer_definition.material_key]
                construction.add_layer(material_id, layer_definition.is_cavity)
                layer = list(construction.get_layers())[-1]
                layer_properties = layer_definition.raw_properties()
                if layer_properties:
                    layer.set_properties(layer_properties)
                    _assert_subset(
                        layer_properties,
                        dict(layer.get_properties()),
                        "construction {} layer".format(definition.key),
                    )
            if definition.construction_class == "glazed":
                if len(list(construction.get_layers())) <= len(initial_layers):
                    raise VeMutationError(
                        "Construction {} manifest glazing layers were not added".format(
                            definition.key
                        )
                    )
                for initial_layer_id in initial_layer_ids:
                    construction.delete_layer(initial_layer_id)
            layers = list(construction.get_layers())
            if len(layers) != len(definition.layers):
                raise VeMutationError(
                    "Construction {} layer count did not persist".format(definition.key)
                )
            identifier = str(getattr(construction, "id", ""))
            if not identifier:
                raise VeMutationError(
                    "Construction {} has no persistent ID".format(definition.key)
                )
            return definition.assignment_parameter, identifier
        except Exception as exc:
            if isinstance(exc, (VeMutationError, VeApiUnavailableError)):
                raise
            raise VeMutationError(
                "Construction creation failed for {}: {}".format(definition.key, exc)
            ) from exc

    def _create_constructions(
        self,
        manifest: AssetManifest,
        material_ids: Mapping[str, str],
        allow_create: bool = True,
    ) -> Tuple[Dict[str, str], Dict[str, str]]:
        """Create all constructions and index identifiers by key and role."""

        by_key: Dict[str, str] = {}
        by_parameter: Dict[str, str] = {}
        for definition in manifest.constructions:
            parameter, identifier = self._create_construction(
                manifest, definition, material_ids, allow_create=allow_create
            )
            by_key[definition.key] = identifier
            by_parameter[parameter] = identifier
        return by_key, by_parameter

    def _create_apache_system(self, manifest: AssetManifest) -> Tuple[str, str]:
        """Create the optional simplified Apache system and return ID and name."""

        definition = manifest.apache_system
        if definition is None:
            return "", ""
        if not hasattr(self.project, "create_apache_system"):
            raise VeApiUnavailableError(
                "Manifest requests an Apache system but create_apache_system is unavailable"
            )
        existing = []
        for system in self.project.apache_systems():
            existing.extend(
                str(value)
                for value in (getattr(system, "id", ""), getattr(system, "name", ""))
                if value
            )
        if definition.name in existing:
            raise VeMutationError(
                "Apache system already exists and on_existing='fail': {}".format(
                    definition.name
                )
            )
        try:
            system = self.project.create_apache_system(
                definition.from_id, definition.name
            )
        except Exception as exc:
            raise VeMutationError(
                "Apache system creation failed: {}".format(exc)
            ) from exc
        identifier = str(getattr(system, "id", ""))
        name = str(getattr(system, "name", definition.name))
        if not identifier or name != definition.name:
            raise VeMutationError("Apache system creation did not persist its identity")
        return identifier, name

    def _gain_enum(self, definition: GainDefinition) -> Any:
        """Resolve the specific VE gain subtype enum used in the data dict."""

        return self._resolve_enum(
            self.GAIN_ENUM_PATHS[definition.category],
            (definition.subtype,),
            "{} gain subtype".format(definition.category),
        )

    def _gain_create_enum(self, definition: GainDefinition) -> Any:
        """Resolve the general CasualGain_type required by create_casual_gain."""

        member = self.GAIN_CREATE_MEMBER_ALIASES.get(
            (definition.category, definition.subtype), definition.subtype
        )
        return self._resolve_enum(
            ("CasualGain.CasualGain_type", "CasualGain_type"),
            (member,),
            "{} gain creation type".format(definition.key),
        )

    def _verify_gain_readback(
        self,
        definition: GainDefinition,
        expected: Mapping[str, Any],
        actual: Mapping[str, Any],
        context: str,
    ) -> None:
        """Verify a gain with narrowly documented VE 2025 canonicalizations."""

        comparable = dict(actual)
        zero_gain = (
            (
                definition.category == "people"
                and _values_match(expected.get("max_sensible_gain"), 0.0)
                and _values_match(expected.get("max_latent_gain"), 0.0)
            )
            or (
                definition.category == "lighting"
                and _values_match(expected.get("max_power_consumption"), 0.0)
            )
            or (
                definition.category == "energy"
                and _values_match(expected.get("max_power_consumption"), 0.0)
                and _values_match(expected.get("max_sensible_gain"), 0.0)
                and _values_match(expected.get("max_latent_gain"), 0.0)
            )
        )
        expected_profile = str(expected.get("variation_profile", "") or "")
        actual_profile = str(comparable.get("variation_profile", "") or "")
        if (
            zero_gain
            and expected_profile
            and expected_profile != "ON"
            and actual_profile == "ON"
        ):
            warning = {
                "code": "VE-ZERO-GAIN-PROFILE-CANONICALIZED-ON",
                "message": (
                    "VE 2025 canonicalized the variation profile of a strictly "
                    "zero-valued gain to ON. The schedule is mathematically "
                    "irrelevant because every gain magnitude is zero; non-zero "
                    "gains remain subject to exact profile verification."
                ),
                "gain_key": definition.key,
                "gain_name": str(expected.get("name", "")),
                "requested_profile": expected_profile,
                "ve_readback": actual_profile,
            }
            if warning not in self._compatibility_warnings:
                self._compatibility_warnings.append(warning)
            comparable["variation_profile"] = expected_profile
        if (
            expected_profile in self._constant_on_profile_ids
            and expected_profile != "ON"
            and str(comparable.get("variation_profile", "") or "") == "ON"
        ):
            warning = {
                "code": "VE-CONSTANT-ONE-PROFILE-CANONICALIZED-ON",
                "message": (
                    "VE 2025 returned ON for a source-traced daily profile "
                    "whose every multiplier is exactly 1.0. ON is "
                    "mathematically identical for this asset; non-constant "
                    "profiles remain subject to exact verification."
                ),
                "asset_type": "gain",
                "gain_key": definition.key,
                "gain_name": str(expected.get("name", "")),
                "requested_profile": expected_profile,
                "ve_readback": "ON",
            }
            if warning not in self._compatibility_warnings:
                self._compatibility_warnings.append(warning)
            comparable["variation_profile"] = expected_profile
        if (
            definition.category == "energy"
            and "max_latent_gain" in expected
            and _values_match(expected["max_latent_gain"], 0.0)
            and "max_latent_gain" not in comparable
        ):
            warning = {
                "code": "VE-ENERGY-GAIN-ZERO-LATENT-NOT-EXPOSED",
                "message": (
                    "VE 2025 accepted max_latent_gain=0 for an EnergyGain but "
                    "omitted that zero-valued field from global gain read-back. "
                    "The room-level power gain must still be written and "
                    "numerically verified as zero latent."
                ),
                "gain_key": definition.key,
                "gain_name": str(expected.get("name", "")),
                "requested_max_latent_gain": 0.0,
                "ve_readback": "FIELD_ABSENT",
            }
            if warning not in self._compatibility_warnings:
                self._compatibility_warnings.append(warning)
            comparable["max_latent_gain"] = 0.0
        _assert_subset(expected, comparable, context)

    def reconcile_existing_gain(
        self, manifest: AssetManifest, gain_key: str
    ) -> Dict[str, Any]:
        """Repair one exact-name reusable gain and verify every written field.

        This is deliberately not called by :meth:`provision`.  It exists for a
        controlled recovery after an earlier interrupted run created an asset
        from an incomplete manifest.  Normal ``reuse_verified`` remains
        fail-closed and never updates divergent reusable objects implicitly.
        """

        if manifest.on_existing != "reuse_verified":
            raise VeMutationError(
                "Controlled gain reconciliation requires on_existing='reuse_verified'"
            )
        matches = [item for item in manifest.gains if item.key == gain_key]
        if len(matches) != 1:
            raise VeMutationError(
                "Expected exactly one gain definition keyed '{}'; found {}".format(
                    gain_key, len(matches)
                )
            )
        definition = matches[0]
        profile_ids = self._create_profiles(manifest)
        data = self._resolve_runtime_value(definition.raw_properties(), profile_ids, "")
        units = self.GAIN_UNITS.get(definition.category, {}).get(definition.units)
        if units is None:
            raise VeMutationError(
                "Unsupported {} gain units '{}'".format(
                    definition.category, definition.units
                )
            )
        data["units_val"] = units
        name = str(data.get("name", ""))
        existing = []
        for gain in self.project.casual_gains():
            actual = dict(gain.get())
            if str(actual.get("name", getattr(gain, "name", ""))) == name:
                existing.append((gain, actual))
        if not existing:
            return {
                "status": "NOT_PRESENT",
                "gain_key": gain_key,
                "name": name,
                "changed": False,
            }
        if len(existing) != 1:
            raise VeMutationError(
                "Gain name is ambiguous and cannot be reconciled: {}".format(name)
            )
        gain, before = existing[0]
        subtype = self._gain_enum(definition)
        if "type_val" not in before or not _values_match(subtype, before["type_val"]):
            raise VeMutationError(
                "Existing gain {} subtype differs from the controlled manifest".format(
                    gain_key
                )
            )
        mismatches = {
            key: {
                "expected": _serializable(value),
                "actual": _serializable(before.get(key)),
            }
            for key, value in data.items()
            if key not in before or not _values_match(value, before.get(key))
            if not (
                definition.category == "energy"
                and key == "max_latent_gain"
                and _values_match(value, 0.0)
                and key not in before
            )
        }
        if not mismatches:
            self._verify_gain_readback(
                definition,
                data,
                before,
                "existing reconciled gain {}".format(gain_key),
            )
            return {
                "status": "ALREADY_MATCHED",
                "gain_key": gain_key,
                "name": name,
                "changed": False,
                "compatibility_warnings": list(self._compatibility_warnings),
            }
        try:
            gain.set(data)
            after = dict(gain.get())
            self._verify_gain_readback(
                definition,
                data,
                after,
                "reconciled gain {}".format(gain_key),
            )
            if "type_val" not in after or not _values_match(subtype, after["type_val"]):
                raise VeMutationError(
                    "Reconciled gain {} subtype read-back mismatch".format(gain_key)
                )
            for template in thermal_templates(self.project, assigned=False).values():
                if hasattr(template, "apply_changes"):
                    template.apply_changes()
        except Exception as exc:
            if isinstance(exc, (VeMutationError, VeApiUnavailableError)):
                raise
            raise VeMutationError(
                "Controlled gain reconciliation failed for {}: {}".format(gain_key, exc)
            ) from exc
        return {
            "status": "RECONCILED_AND_VERIFIED",
            "gain_key": gain_key,
            "name": name,
            "changed": True,
            "mismatches_before": mismatches,
            "verified_after": {key: _serializable(after.get(key)) for key in mismatches},
            "compatibility_warnings": list(self._compatibility_warnings),
        }

    def _create_gains(
        self,
        manifest: AssetManifest,
        profile_ids: Mapping[str, str],
        apache_system_id: str,
    ) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """Create missing gains or strictly verify reusable gains."""

        objects: Dict[str, Any] = {}
        identifiers: Dict[str, str] = {}
        existing_by_name: Dict[str, List[Tuple[Any, Dict[str, Any]]]] = {}
        try:
            for gain in self.project.casual_gains():
                actual = dict(gain.get())
                name = str(actual.get("name", getattr(gain, "name", "")))
                if name:
                    existing_by_name.setdefault(name, []).append((gain, actual))
        except Exception as exc:
            raise VeMutationError(
                "Unable to inspect existing casual gains: {}".format(exc)
            ) from exc
        for definition in manifest.gains:
            creation_type = self._gain_create_enum(definition)
            subtype = self._gain_enum(definition)
            units = self.GAIN_UNITS.get(definition.category, {}).get(definition.units)
            if units is None:
                raise VeMutationError(
                    "Unsupported {} gain units '{}'".format(
                        definition.category, definition.units
                    )
                )
            data = self._resolve_runtime_value(
                definition.raw_properties(), profile_ids, apache_system_id
            )
            # The gain family is fixed by create_casual_gain().  VE 2025.2
            # returns a family-specific subtype enum from get()["type_val"],
            # but set() expects the general eCasualGain enum and rejects that
            # read-back subtype.  Do not rewrite type_val; verify it separately.
            data.update({"units_val": units})
            name = str(data.get("name", ""))
            matches = existing_by_name.get(name, [])
            if len(matches) > 1:
                raise VeMutationError(
                    "Gain name is ambiguous and cannot be reused: {}".format(name)
                )
            if matches:
                if manifest.on_existing == "fail":
                    raise VeMutationError(
                        "Gain already exists and on_existing='fail': {}".format(name)
                    )
                gain, actual = matches[0]
                self._verify_gain_readback(
                    definition,
                    data,
                    actual,
                    "existing gain {}".format(definition.key),
                )
                if "type_val" not in actual or not _values_match(
                    subtype, actual["type_val"]
                ):
                    raise VeMutationError(
                        "Existing gain {} subtype differs from manifest".format(
                            definition.key
                        )
                    )
                objects[definition.key] = gain
                identifiers[definition.key] = str(
                    getattr(gain, "id", actual.get("id", definition.key))
                )
                continue
            try:
                gain = self.project.create_casual_gain(creation_type)
                gain.set(data)
                actual = dict(gain.get())
                self._verify_gain_readback(
                    definition,
                    data,
                    actual,
                    "gain {}".format(definition.key),
                )
                if "type_val" not in actual or not _values_match(
                    subtype, actual["type_val"]
                ):
                    raise VeMutationError(
                        "Gain {} subtype read-back mismatch".format(definition.key)
                    )
                objects[definition.key] = gain
                identifiers[definition.key] = str(
                    getattr(gain, "id", actual.get("id", definition.key))
                )
            except Exception as exc:
                if isinstance(exc, (VeMutationError, VeApiUnavailableError)):
                    raise
                raise VeMutationError(
                    "Gain creation failed for {}: {}".format(definition.key, exc)
                ) from exc
        return objects, identifiers

    def _air_enums(self, definition: AirExchangeDefinition) -> Tuple[Any, Any, Any]:
        """Resolve all typed enums required by AirExchange create/set calls."""

        exchange_member = self.AIR_EXCHANGE_MEMBER_ALIASES.get(
            definition.exchange_type, definition.exchange_type
        )
        if definition.units not in self.AIR_UNIT_MEMBERS:
            raise VeMutationError(
                "Unsupported air-exchange units: '{}'".format(definition.units)
            )
        adjacent_member = self.AIR_ADJACENT_MEMBER_ALIASES.get(
            definition.adjacent_condition, definition.adjacent_condition
        )
        exchange_type = self._resolve_enum(
            ("AirExchange.AirExchange_type", "AirExchange_type"),
            (exchange_member,),
            "air-exchange type",
        )
        units = self._resolve_enum(
            ("AirExchange.AirChange_unit", "AirChange_unit"),
            (self.AIR_UNIT_MEMBERS[definition.units],),
            "air-exchange units",
        )
        adjacent = self._resolve_enum(
            ("AirExchange.AdjacentCondition_type", "AdjacentCondition_type"),
            (adjacent_member,),
            "air-exchange adjacent condition",
        )
        return exchange_type, units, adjacent

    def _preflight_runtime_enums(self, manifest: AssetManifest) -> None:
        """Resolve every version-sensitive runtime enum before asset mutation."""

        for definition in manifest.gains:
            self._gain_create_enum(definition)
            self._gain_enum(definition)
        for definition in manifest.air_exchanges:
            self._air_enums(definition)
        room_conditions = manifest.thermal_template.raw_room_conditions()
        for key in ("heating_setpoint_type", "cooling_setpoint_type"):
            requested = room_conditions.get(key)
            if isinstance(requested, str):
                member = requested.strip().lower()
                if member not in {"constant", "variable", "two_value"}:
                    raise VeMutationError(
                        "Unsupported {} value: {!r}".format(key, requested)
                    )
                self._resolve_enum(
                    (
                        "VERoomData.setpoint_type",
                        "VEThermalTemplate.setpoint_type",
                        "setpoint_type",
                    ),
                    (member,),
                    key,
                )
        system_data = manifest.thermal_template.raw_system_data()
        if isinstance(system_data.get("conditioned"), bool):
            self._conditioned_flag(system_data["conditioned"])

    def reconcile_existing_air_exchange(
        self, manifest: AssetManifest, exchange_key: str
    ) -> Dict[str, Any]:
        """Repair one exact-name reusable air exchange and verify read-back.

        Like :meth:`reconcile_existing_gain`, this method is an explicit
        interrupted-run recovery boundary. Normal provisioning remains
        fail-closed and never updates a divergent reusable exchange.
        """

        if manifest.on_existing != "reuse_verified":
            raise VeMutationError(
                "Controlled air-exchange reconciliation requires "
                "on_existing='reuse_verified'"
            )
        matches = [item for item in manifest.air_exchanges if item.key == exchange_key]
        if len(matches) != 1:
            raise VeMutationError(
                "Expected exactly one air-exchange definition keyed '{}'; "
                "found {}".format(exchange_key, len(matches))
            )
        definition = matches[0]
        profile_ids = self._create_profiles(manifest)
        exchange_type, units, adjacent = self._air_enums(definition)
        data = self._resolve_runtime_value(definition.raw_properties(), profile_ids, "")
        data.update(
            {
                "type_val": exchange_type,
                "units_val": units,
                "adjacent_condition_val": adjacent,
            }
        )
        name = str(data.get("name", ""))
        existing = []
        for exchange in self.project.air_exchanges():
            actual = dict(exchange.get())
            if str(actual.get("name", getattr(exchange, "name", ""))) == name:
                existing.append((exchange, actual))
        if not existing:
            return {
                "status": "NOT_PRESENT",
                "exchange_key": exchange_key,
                "name": name,
                "changed": False,
            }
        if len(existing) != 1:
            raise VeMutationError(
                "Air-exchange name is ambiguous and cannot be reconciled: "
                "{}".format(name)
            )
        exchange, before = existing[0]
        mismatches = {
            key: {
                "expected": _serializable(value),
                "actual": _serializable(before.get(key)),
            }
            for key, value in data.items()
            if key not in before or not _values_match(value, before.get(key))
        }
        if not mismatches:
            self._verify_air_exchange_readback(
                definition,
                data,
                before,
                "existing reconciled air exchange {}".format(exchange_key),
            )
            return {
                "status": "ALREADY_MATCHED",
                "exchange_key": exchange_key,
                "name": name,
                "changed": False,
            }
        try:
            exchange.set(data)
            after = dict(exchange.get())
            self._verify_air_exchange_readback(
                definition,
                data,
                after,
                "reconciled air exchange {}".format(exchange_key),
            )
            for template in thermal_templates(self.project, assigned=False).values():
                if hasattr(template, "apply_changes"):
                    template.apply_changes()
        except Exception as exc:
            if isinstance(exc, (VeMutationError, VeApiUnavailableError)):
                raise
            raise VeMutationError(
                "Controlled air-exchange reconciliation failed for {}: "
                "{}".format(exchange_key, exc)
            ) from exc
        return {
            "status": "RECONCILED_AND_VERIFIED",
            "exchange_key": exchange_key,
            "name": name,
            "changed": True,
            "mismatches_before": mismatches,
            "verified_after": {key: _serializable(after.get(key)) for key in mismatches},
        }

    def _verify_air_exchange_readback(
        self,
        definition: AirExchangeDefinition,
        expected: Mapping[str, Any],
        actual: Mapping[str, Any],
        context: str,
    ) -> None:
        """Verify an exchange with VE's zero-flow profile canonicalization."""

        comparable = dict(actual)
        expected_profile = str(expected.get("variation_profile", "") or "")
        actual_profile = str(comparable.get("variation_profile", "") or "")
        if (
            _values_match(expected.get("max_flow"), 0.0)
            and expected_profile
            and expected_profile != "ON"
            and actual_profile == "ON"
        ):
            warning = {
                "code": "VE-ZERO-AIR-FLOW-PROFILE-CANONICALIZED-ON",
                "message": (
                    "VE 2025 canonicalized the variation profile of a strictly "
                    "zero-flow air exchange to ON. The schedule is "
                    "mathematically irrelevant because max_flow is zero; "
                    "non-zero exchanges remain subject to exact profile "
                    "verification."
                ),
                "exchange_key": definition.key,
                "exchange_name": str(expected.get("name", "")),
                "requested_profile": expected_profile,
                "ve_readback": actual_profile,
                "max_flow": 0.0,
            }
            if warning not in self._compatibility_warnings:
                self._compatibility_warnings.append(warning)
            comparable["variation_profile"] = expected_profile
        if (
            expected_profile in self._constant_on_profile_ids
            and expected_profile != "ON"
            and str(comparable.get("variation_profile", "") or "") == "ON"
        ):
            warning = {
                "code": "VE-CONSTANT-ONE-PROFILE-CANONICALIZED-ON",
                "message": (
                    "VE 2025 returned ON for a source-traced daily profile "
                    "whose every multiplier is exactly 1.0. ON is "
                    "mathematically identical for this asset; non-constant "
                    "profiles remain subject to exact verification."
                ),
                "asset_type": "air_exchange",
                "exchange_key": definition.key,
                "exchange_name": str(expected.get("name", "")),
                "requested_profile": expected_profile,
                "ve_readback": "ON",
            }
            if warning not in self._compatibility_warnings:
                self._compatibility_warnings.append(warning)
            comparable["variation_profile"] = expected_profile
        _assert_subset(expected, comparable, context)

    def _create_air_exchanges(
        self,
        manifest: AssetManifest,
        profile_ids: Mapping[str, str],
        apache_system_id: str,
    ) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """Create missing exchanges or strictly verify reusable exchanges."""

        objects: Dict[str, Any] = {}
        names: Dict[str, str] = {}
        existing_by_name: Dict[str, List[Tuple[Any, Dict[str, Any]]]] = {}
        try:
            for exchange in self.project.air_exchanges():
                actual = dict(exchange.get())
                name = str(actual.get("name", getattr(exchange, "name", "")))
                if name:
                    existing_by_name.setdefault(name, []).append((exchange, actual))
        except Exception as exc:
            raise VeMutationError(
                "Unable to inspect existing air exchanges: {}".format(exc)
            ) from exc
        for definition in manifest.air_exchanges:
            exchange_type, units, adjacent = self._air_enums(definition)
            data = self._resolve_runtime_value(
                definition.raw_properties(), profile_ids, apache_system_id
            )
            data.update(
                {
                    "type_val": exchange_type,
                    "units_val": units,
                    "adjacent_condition_val": adjacent,
                }
            )
            name = str(data.get("name", ""))
            matches = existing_by_name.get(name, [])
            if len(matches) > 1:
                raise VeMutationError(
                    "Air-exchange name is ambiguous and cannot be reused: {}".format(name)
                )
            if matches:
                if manifest.on_existing == "fail":
                    raise VeMutationError(
                        "Air exchange already exists and on_existing='fail': {}".format(
                            name
                        )
                    )
                exchange, actual = matches[0]
                self._verify_air_exchange_readback(
                    definition,
                    data,
                    actual,
                    "existing air exchange {}".format(definition.key),
                )
                objects[definition.key] = exchange
                names[definition.key] = str(
                    actual.get("name", getattr(exchange, "name", definition.key))
                )
                continue
            try:
                exchange = self.project.create_air_exchange(exchange_type)
                exchange.set(data)
                actual = dict(exchange.get())
                self._verify_air_exchange_readback(
                    definition,
                    data,
                    actual,
                    "air exchange {}".format(definition.key),
                )
                objects[definition.key] = exchange
                names[definition.key] = str(
                    actual.get("name", getattr(exchange, "name", definition.key))
                )
            except Exception as exc:
                if isinstance(exc, (VeMutationError, VeApiUnavailableError)):
                    raise
                raise VeMutationError(
                    "Air-exchange creation failed for {}: {}".format(definition.key, exc)
                ) from exc
        return objects, names

    def _template_handle(self, template: Any) -> str:
        """Resolve the persistent handle of one newly created template."""

        for handle, candidate in thermal_templates(self.project, assigned=False).items():
            if candidate is template or str(candidate.name) == str(template.name):
                return str(handle)
        raise VeMutationError("New thermal template has no resolvable handle")

    def _writable_room_conditions(
        self, room_conditions: Mapping[str, Any]
    ) -> Dict[str, Any]:
        """Return only room-condition fields supported by the VE setter.

        ``solar_reflected_fraction`` records the ISO 52016-1 verification-case
        assumption that solar re-reflection losses are not taken into account.
        VE 2025.2 rejects that name in ``set_room_conditions``; it is an engine
        calculation assumption rather than an exposed thermal-template field.
        The traced value therefore remains in the manifest and audit report but
        is not passed to the version-sensitive setter.
        """

        writable = dict(room_conditions)
        for key in ("heating_setpoint_type", "cooling_setpoint_type"):
            requested = writable.get(key)
            if isinstance(requested, str):
                member = requested.strip().lower()
                if member not in {"constant", "variable", "two_value"}:
                    raise VeMutationError(
                        "Unsupported {} value: {!r}".format(key, requested)
                    )
                writable[key] = self._resolve_enum(
                    (
                        "VERoomData.setpoint_type",
                        "VEThermalTemplate.setpoint_type",
                        "setpoint_type",
                    ),
                    (member,),
                    key,
                )
        for key in sorted(self.AUDIT_ONLY_ROOM_CONDITION_KEYS & writable.keys()):
            requested = _serializable(writable.pop(key))
            warning = {
                "code": "VE-ROOM-CONDITION-AUDIT-ONLY",
                "severity": "WARNING",
                "field": key,
                "requested_value": requested,
                "ve_binding": "NOT_EXPOSED_BY_VETHERMALTEMPLATE",
                "message": (
                    "The source-traced assumption remains in the manifest and "
                    "audit evidence but is not passed to set_room_conditions; "
                    "VE 2025.2 rejects this option. Engine behaviour must be "
                    "confirmed before a certification claim."
                ),
            }
            if warning not in self._compatibility_warnings:
                self._compatibility_warnings.append(warning)
            LOGGER.warning(
                "asset_provisioning | thermal_template | %s | WARNING | "
                "source-traced room condition is audit-only because the VE "
                "setter does not expose this option; requested=%s",
                key,
                requested,
            )
        return writable

    def _conditioned_flag(self, conditioned: bool) -> Any:
        """Return VE's typed conditioned-state enum for a manifest boolean.

        ``VEThermalTemplate.set_apache_systems`` documents ``conditioned`` as
        a setter key, but VE 2025 exposes it as ``conditioned_flag`` rather
        than a Python bool.  In particular, ``False`` numerically aliases the
        enum's default/not-applicable state and is read back as ``yes``.  The
        explicit free-floating member is therefore required for Test 1 cases
        600FF and 900FF.
        """

        member = "yes" if conditioned else "no_free_floating"
        return self._resolve_enum(
            (
                "VEThermalTemplate.conditioned_flag",
                "VERoomData.conditioned_flag",
                "conditioned_flag",
            ),
            (member,),
            "thermal-template conditioned state",
        )

    def _writable_system_data(self, system_data: Mapping[str, Any]) -> Dict[str, Any]:
        """Translate source-level system values to VE setter types."""

        writable = dict(system_data)
        requested = writable.get("conditioned")
        if isinstance(requested, bool):
            if requested:
                writable["conditioned"] = self._conditioned_flag(True)
            else:
                # VE 2025.2 accepts the documented enum on the template setter
                # but reads the template back as ``yes``. VERoomData does not
                # document ``conditioned`` as a writable system field either.
                # Keep the source value in the manifest and enforce the actual
                # free-floating physics with verified OFF heating and cooling
                # availability profiles in Room Conditions.
                writable.pop("conditioned", None)
                warning = {
                    "code": "VE-TEMPLATE-FREE-FLOATING-MAPPED-TO-PROFILES",
                    "field": "conditioned",
                    "requested_value": False,
                    "ve_binding": (
                        "VEThermalTemplate/VERoomData heating_profile and "
                        "cooling_profile"
                    ),
                    "message": (
                        "VE did not persist no_free_floating through the documented "
                        "thermal-template setter. Free-floating operation is mapped "
                        "to OFF heating/cooling availability profiles and must pass "
                        "room-level read-back before simulation."
                    ),
                }
                if warning not in self._compatibility_warnings:
                    self._compatibility_warnings.append(warning)
                LOGGER.warning(
                    "asset_provisioning | thermal_template | conditioned | WARNING | "
                    "free-floating state mapped to verified OFF heating/cooling profiles"
                )
        return writable

    def _repair_template_link_physics(
        self,
        expected_records: Sequence[Any],
        actual_records: Sequence[Any],
        kind: str,
    ) -> List[Dict[str, Any]]:
        """Synchronize existing one-to-one template links through native setters.

        This recovery never adds, removes or renames a link. It is allowed only
        when expected and actual records have the same unique physical keys.
        """

        if kind == "gain":
            key_function = _gain_record_family
            writable = (
                "allow_profile_saturate",
                "ballast",
                "dimming_profile",
                "diversity_factor",
                "max_illuminance",
                "max_latent_gain",
                "max_power_consumption",
                "max_sensible_gain",
                "occupancy_density",
                "pc_convective_gain",
                "radiant_fraction",
                "units_val",
                "variation_profile",
            )
        else:
            key_function = _exchange_record_family
            writable = (
                "adjacent_condition_val",
                "max_flow",
                "offset_temperature",
                "units_val",
                "variation_profile",
            )

        def index(records: Sequence[Any]) -> Dict[str, Tuple[Any, Dict[str, Any]]]:
            indexed: Dict[str, Tuple[Any, Dict[str, Any]]] = {}
            for record in records:
                data = dict(record.get())
                key = key_function(data)
                if not key or key in indexed:
                    raise VeMutationError(
                        "Template {} link keys are empty or ambiguous: {!r}".format(
                            kind, key
                        )
                    )
                indexed[key] = (record, data)
            return indexed

        expected_by_key = index(expected_records)
        actual_by_key = index(actual_records)
        if set(expected_by_key) != set(actual_by_key):
            raise VeMutationError(
                "Template {} links cannot be synchronized: expected keys {}, "
                "actual keys {}".format(
                    kind, sorted(expected_by_key), sorted(actual_by_key)
                )
            )
        changes = []
        for key in sorted(expected_by_key):
            _expected_record, expected = expected_by_key[key]
            actual_record, before = actual_by_key[key]
            compare = (
                _gain_record_mismatches if kind == "gain" else _exchange_record_mismatches
            )
            mismatches = compare(expected, before)
            if not mismatches:
                continue
            setter = getattr(actual_record, "set", None)
            if not callable(setter):
                raise VeMutationError(
                    "Template {} link {!r} exposes no supported set() method".format(
                        kind, key
                    )
                )
            payload = {
                field: expected[field]
                for field in writable
                if field in expected and field in mismatches
            }
            if not payload:
                raise VeMutationError(
                    "Template {} link {!r} mismatch has no controlled writable "
                    "fields: {}".format(kind, key, mismatches)
                )
            try:
                setter(payload)
            except Exception as exc:
                raise VeMutationError(
                    "Template {} link {!r} synchronization failed: {}".format(
                        kind, key, exc
                    )
                ) from exc
            after = dict(actual_record.get())
            remaining = compare(expected, after)
            if remaining:
                raise VeMutationError(
                    "Template {} link {!r} synchronization did not persist: {}".format(
                        kind, key, remaining
                    )
                )
            changes.append(
                {
                    "kind": kind,
                    "key": key,
                    "before": mismatches,
                    "verified_fields": sorted(payload),
                }
            )
        return changes

    def _create_template(
        self,
        manifest: AssetManifest,
        profile_ids: Mapping[str, str],
        apache_system_id: str,
        gains: Mapping[str, Any],
        air_exchanges: Mapping[str, Any],
    ) -> Tuple[str, str]:
        """Create a template or strictly verify and reuse an existing one."""

        definition = manifest.thermal_template
        if definition.standard != "generic":
            raise VeMutationError(
                "create_thermal_template creates generic templates; requested '{}'".format(
                    definition.standard
                )
            )
        traced_room_conditions = self._resolve_runtime_value(
            definition.raw_room_conditions(), profile_ids, apache_system_id
        )
        room_conditions = self._writable_room_conditions(traced_room_conditions)
        traced_system_data = self._resolve_runtime_value(
            definition.raw_system_data(), profile_ids, apache_system_id
        )
        system_data = self._writable_system_data(traced_system_data)
        if apache_system_id:
            system_data["HVAC_system"] = apache_system_id
        matches = [
            template
            for template in thermal_templates(self.project, assigned=False).values()
            if str(getattr(template, "name", "")) == definition.name
        ]
        if len(matches) > 1:
            raise VeMutationError(
                "Thermal template name is ambiguous and cannot be reused: {}".format(
                    definition.name
                )
            )
        if matches:
            if manifest.on_existing == "fail":
                raise VeMutationError(
                    "Thermal template already exists and on_existing='fail': {}".format(
                        definition.name
                    )
                )
            template = matches[0]

            expected_gain_records = [gains[key] for key in definition.gain_keys]
            actual_gain_records = list(template.get_casual_gains())
            expected_exchange_records = [
                air_exchanges[key] for key in definition.air_exchange_keys
            ]
            actual_exchange_records = list(template.get_air_exchanges())
            gain_links_match, gain_link_details = _template_links_semantically_match(
                expected_gain_records, actual_gain_records, "gain"
            )
            exchange_links_match, exchange_link_details = (
                _template_links_semantically_match(
                    expected_exchange_records,
                    actual_exchange_records,
                    "air_exchange",
                )
            )
            try:
                _assert_subset(
                    room_conditions,
                    dict(template.get_room_conditions()),
                    "existing thermal template room conditions",
                )
                _assert_subset(
                    system_data,
                    dict(template.get_apache_systems()),
                    "existing thermal template system data",
                )
                if not gain_links_match:
                    raise VeMutationError(
                        "Existing thermal template gain physics differs from "
                        "manifest: {}".format(gain_link_details)
                    )
                if not exchange_links_match:
                    raise VeMutationError(
                        "Existing thermal template air-exchange physics differs "
                        "from manifest: {}".format(exchange_link_details)
                    )
            except VeMutationError:
                # A failed post-setter read-back can leave either an empty
                # template or a fully linked template whose links are already
                # exactly those declared by the manifest.  Both states are
                # deterministic to repair.  Partial or divergent links remain
                # fail-closed because re-adding them could duplicate data.
                links_empty = not actual_gain_records and not actual_exchange_records
                links_match = gain_links_match and exchange_links_match
                if not (links_empty or links_match):
                    link_repairs = self._repair_template_link_physics(
                        expected_gain_records,
                        actual_gain_records,
                        "gain",
                    )
                    link_repairs.extend(
                        self._repair_template_link_physics(
                            expected_exchange_records,
                            actual_exchange_records,
                            "air_exchange",
                        )
                    )
                    gain_links_match, gain_link_details = (
                        _template_links_semantically_match(
                            expected_gain_records,
                            actual_gain_records,
                            "gain",
                        )
                    )
                    exchange_links_match, exchange_link_details = (
                        _template_links_semantically_match(
                            expected_exchange_records,
                            actual_exchange_records,
                            "air_exchange",
                        )
                    )
                    links_match = gain_links_match and exchange_links_match
                    if not links_match:
                        raise VeMutationError(
                            "Existing thermal template links remain physically "
                            "divergent; gain_details={}, exchange_details={}".format(
                                gain_link_details, exchange_link_details
                            )
                        )
                    warning = {
                        "code": "VE-THERMAL-TEMPLATE-LINK-PHYSICS-RECOVERED",
                        "message": (
                            "Existing one-to-one template links had stale physical "
                            "fields. Only those fields were rewritten through the "
                            "native record setters and strictly read back."
                        ),
                        "template_name": definition.name,
                        "repairs": link_repairs,
                    }
                    if warning not in self._compatibility_warnings:
                        self._compatibility_warnings.append(warning)
                warning = {
                    "code": "VE-INCOMPLETE-THERMAL-TEMPLATE-RECOVERED",
                    "message": (
                        "An existing template with the exact manifest name was "
                        "left by an interrupted or failed setter/read-back. Its "
                        "source-traced content was reapplied only because its "
                        "gain and air-exchange links were either empty or an "
                        "exact manifest match; divergent links are never repaired."
                    ),
                    "template_name": definition.name,
                }
                if warning not in self._compatibility_warnings:
                    self._compatibility_warnings.append(warning)
                LOGGER.warning(
                    "asset_provisioning | thermal_template | %s | WARNING | "
                    "recovering a manifest-matched template left by an "
                    "interrupted or failed setter/read-back",
                    definition.name,
                )
                try:
                    template.set_room_conditions(room_conditions)
                    template.set_apache_systems(system_data)
                    if links_empty:
                        for key in definition.gain_keys:
                            template.add_gain(gains[key])
                        for key in definition.air_exchange_keys:
                            template.add_air_exchange(air_exchanges[key])
                    template.apply_changes()
                except Exception as exc:
                    raise VeMutationError(
                        "Incomplete thermal template recovery failed: {}".format(exc)
                    ) from exc
                _assert_subset(
                    room_conditions,
                    dict(template.get_room_conditions()),
                    "recovered thermal template room conditions",
                )
                _assert_subset(
                    system_data,
                    dict(template.get_apache_systems()),
                    "recovered thermal template system data",
                )
                gains_verified, gain_details_after = _template_links_semantically_match(
                    expected_gain_records,
                    template.get_casual_gains(),
                    "gain",
                )
                if not gains_verified:
                    raise VeMutationError(
                        "Recovered thermal template gain physics differs from "
                        "manifest: {}".format(gain_details_after)
                    )
                exchanges_verified, exchange_details_after = (
                    _template_links_semantically_match(
                        expected_exchange_records,
                        template.get_air_exchanges(),
                        "air_exchange",
                    )
                )
                if not exchanges_verified:
                    raise VeMutationError(
                        "Recovered thermal template air-exchange physics differs "
                        "from manifest: {}".format(exchange_details_after)
                    )
            return definition.name, self._template_handle(template)
        try:
            template = self.project.create_thermal_template(definition.name)
            if str(template.name) != definition.name:
                raise VeMutationError(
                    "VE altered the requested template name, indicating a collision"
                )
            template.set_room_conditions(room_conditions)
            template.set_apache_systems(system_data)
            for key in definition.gain_keys:
                template.add_gain(gains[key])
            for key in definition.air_exchange_keys:
                template.add_air_exchange(air_exchanges[key])
            template.apply_changes()
            _assert_subset(
                room_conditions,
                dict(template.get_room_conditions()),
                "thermal template room conditions",
            )
            _assert_subset(
                system_data,
                dict(template.get_apache_systems()),
                "thermal template system data",
            )
            if len(template.get_casual_gains()) != len(definition.gain_keys):
                raise VeMutationError("Thermal template gain count did not persist")
            if len(template.get_air_exchanges()) != len(definition.air_exchange_keys):
                raise VeMutationError(
                    "Thermal template air-exchange count did not persist"
                )
            return definition.name, self._template_handle(template)
        except Exception as exc:
            if isinstance(exc, (VeMutationError, VeApiUnavailableError)):
                raise
            raise VeMutationError(
                "Thermal template creation failed: {}".format(exc)
            ) from exc

    def provision(self, manifest: AssetManifest) -> ProvisioningReceipt:
        """Provision every manifest asset in dependency order and return a receipt."""

        self._compatibility_warnings = []
        errors = manifest.validation_errors()
        if errors:
            raise VeMutationError(
                "Asset manifest is invalid: {}".format("; ".join(errors))
            )
        self.check_capabilities()
        self._preflight_runtime_enums(manifest)
        if manifest.on_existing == "fail":
            self._ensure_no_existing_template(manifest.thermal_template.name)
        LOGGER.info("asset_provisioning | profiles | STARTED")
        profile_ids = self._create_profiles(manifest)
        LOGGER.info("asset_provisioning | profiles | PASS")
        LOGGER.info("asset_provisioning | materials | STARTED")
        material_ids = self._create_materials(manifest)
        LOGGER.info("asset_provisioning | materials | PASS")
        LOGGER.info("asset_provisioning | constructions | STARTED")
        construction_ids, construction_parameters = self._create_constructions(
            manifest, material_ids
        )
        LOGGER.info("asset_provisioning | constructions | PASS")
        LOGGER.info("asset_provisioning | apache_system | STARTED")
        apache_system_id, _ = self._create_apache_system(manifest)
        LOGGER.info("asset_provisioning | apache_system | PASS")
        LOGGER.info("asset_provisioning | gains | STARTED")
        gains, gain_ids = self._create_gains(manifest, profile_ids, apache_system_id)
        LOGGER.info("asset_provisioning | gains | PASS")
        LOGGER.info("asset_provisioning | air_exchanges | STARTED")
        exchanges, exchange_names = self._create_air_exchanges(
            manifest, profile_ids, apache_system_id
        )
        LOGGER.info("asset_provisioning | air_exchanges | PASS")
        LOGGER.info("asset_provisioning | thermal_template | STARTED")
        template_name, template_handle = self._create_template(
            manifest,
            profile_ids,
            apache_system_id,
            gains,
            exchanges,
        )
        LOGGER.info("asset_provisioning | thermal_template | PASS")
        manifest_source = manifest.thermal_template.evidence.source
        parameter_overrides = {
            parameter: {
                "value": identifier,
                "source": next(
                    definition.evidence.source
                    for definition in manifest.constructions
                    if definition.assignment_parameter == parameter
                ),
                "source_locator": "{}#sha256={}".format(
                    manifest.source_path, manifest.source_checksum
                ),
            }
            for parameter, identifier in construction_parameters.items()
        }
        parameter_overrides.update(
            {
                "thermal_template_name": {
                    "value": template_name,
                    "source": manifest_source,
                    "source_locator": manifest.source_path,
                },
                "thermal_template_source_record": {
                    "value": "sha256:{}".format(manifest.source_checksum),
                    "source": manifest_source,
                    "source_locator": manifest.source_path,
                },
            }
        )
        occupancy_profile_id = profile_ids.get("occupancy_profile")
        if occupancy_profile_id:
            occupancy_profile = next(
                item for item in manifest.profiles if item.key == "occupancy_profile"
            )
            parameter_overrides["occupancy_profile_id"] = {
                "value": occupancy_profile_id,
                "source": occupancy_profile.evidence.source,
                "source_locator": manifest.source_path,
            }
        if apache_system_id and manifest.apache_system:
            parameter_overrides["hvac_system_id"] = {
                "value": apache_system_id,
                "source": manifest.apache_system.evidence.source,
                "source_locator": manifest.source_path,
            }
        return ProvisioningReceipt(
            manifest_path=manifest.source_path,
            manifest_checksum=manifest.source_checksum,
            parameter_overrides=parameter_overrides,
            profile_ids=profile_ids,
            material_ids=material_ids,
            construction_ids=construction_ids,
            gain_ids=gain_ids,
            air_exchange_names=exchange_names,
            template_name=template_name,
            template_handle=template_handle,
            apache_system_id=apache_system_id,
            compatibility_warnings=tuple(self._compatibility_warnings),
        )

    def provision_operational_template(self, plan: Any) -> Dict[str, Any]:
        """Provision only profiles, gains, exchanges and one thermal template.

        Client-model remediation must not create or replace envelope CDB data
        merely to install a reviewed operational template.  This deliberately
        narrow boundary reuses the same enum preflight, collision policy and
        exact VE read-back checks as :meth:`provision`, while excluding all
        material and construction mutation.
        """

        if getattr(plan, "on_existing", None) not in {"fail", "reuse_verified"}:
            raise VeMutationError(
                "Operational-template on_existing must be 'fail' or " "'reuse_verified'"
            )
        profiles = tuple(getattr(plan, "profiles", ()))
        gains = tuple(getattr(plan, "gains", ()))
        exchanges = tuple(getattr(plan, "air_exchanges", ()))
        template = getattr(plan, "thermal_template", None)
        if template is None or not gains or not exchanges:
            raise VeMutationError(
                "Operational-template plan requires a template, gains and air exchanges"
            )
        for definition in profiles:
            if (
                definition.evidence.validation_error()
                or definition.data.validation_error()
            ):
                raise VeMutationError(
                    "Operational profile {} has invalid evidence or data".format(
                        definition.key
                    )
                )
        for label, definitions in (("gain", gains), ("air exchange", exchanges)):
            for definition in definitions:
                errors = [
                    "{}.{}: {}".format(label, name, error)
                    for name, field in definition.properties.items()
                    for error in [field.validation_error()]
                    if error
                ]
                if definition.evidence.validation_error() or errors:
                    raise VeMutationError(
                        "Operational {} {} is invalid: {}".format(
                            label, definition.key, "; ".join(errors)
                        )
                    )
        template_errors = []
        for group in (template.room_conditions, template.system_data):
            for name, field in group.items():
                error = field.validation_error()
                if error:
                    template_errors.append("{}: {}".format(name, error))
        gain_keys = {item.key for item in gains}
        exchange_keys = {item.key for item in exchanges}
        if set(template.gain_keys) != gain_keys:
            template_errors.append("template gain keys do not match the plan")
        if set(template.air_exchange_keys) != exchange_keys:
            template_errors.append("template air-exchange keys do not match the plan")
        if template.evidence.validation_error() or template_errors:
            raise VeMutationError(
                "Operational thermal template is invalid: {}".format(
                    "; ".join(template_errors)
                )
            )

        required_capabilities = {
            "VEProject.create_profile": hasattr(self.project, "create_profile"),
            "VEProject.save_profiles": hasattr(self.project, "save_profiles"),
            "VEProject.create_casual_gain": hasattr(self.project, "create_casual_gain"),
            "VEProject.casual_gains": hasattr(self.project, "casual_gains"),
            "VEProject.create_air_exchange": hasattr(self.project, "create_air_exchange"),
            "VEProject.air_exchanges": hasattr(self.project, "air_exchanges"),
            "VEProject.create_thermal_template": hasattr(
                self.project, "create_thermal_template"
            ),
        }
        missing = sorted(
            name for name, available in required_capabilities.items() if not available
        )
        if missing:
            raise VeApiUnavailableError(
                "Operational-template provisioning is unavailable: {}".format(missing)
            )

        self._compatibility_warnings = []
        self._preflight_runtime_enums(plan)
        if plan.on_existing == "fail":
            self._ensure_no_existing_template(template.name)
        profile_ids = self._create_profiles(plan)
        apache_system_id, _ = self._create_apache_system(plan)
        # An earlier fail-closed run may have created a correctly named gain
        # before a version-specific read-back mismatch stopped the workflow.
        # Reconcile only exact-name, exact-subtype records declared by this
        # same source-traced plan; divergent or ambiguous objects still fail.
        if plan.on_existing == "reuse_verified":
            for definition in gains:
                self.reconcile_existing_gain(plan, definition.key)
        gain_objects, gain_ids = self._create_gains(plan, profile_ids, apache_system_id)
        if plan.on_existing == "reuse_verified":
            for definition in exchanges:
                self.reconcile_existing_air_exchange(plan, definition.key)
        exchange_objects, exchange_names = self._create_air_exchanges(
            plan, profile_ids, apache_system_id
        )
        template_name, template_handle = self._create_template(
            plan,
            profile_ids,
            apache_system_id,
            gain_objects,
            exchange_objects,
        )
        return {
            "status": "OPERATIONAL_TEMPLATE_CREATED_OR_VERIFIED",
            "profile_ids": dict(profile_ids),
            "gain_ids": dict(gain_ids),
            "air_exchange_names": dict(exchange_names),
            "template_name": template_name,
            "template_handle": template_handle,
            "compatibility_warnings": list(self._compatibility_warnings),
        }
