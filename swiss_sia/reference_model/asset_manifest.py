"""Strict, source-traced definitions for VE assets created from scratch.

The manifest contains no regulatory defaults. Every physical or operational
value is wrapped in a :class:`TraceableField` carrying its description, units,
source, source locator, and validation range. The loader rejects unknown
fields so that schema drift cannot silently alter a VE model.
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Sequence,
    Set,
    Tuple,
    Union,
)

from .compliance_config import ValidationRange
from .exceptions import ConfigurationError

SUPPORTED_ASSET_MANIFEST_VERSIONS = {"1.0"}
SUPPORTED_PROFILE_TYPES = {
    "daily",
    "weekly",
    "yearly",
    "compact",
    "freeform",
}
# VE 2025 returns and requires 12 daily-profile IDs for every native weekly
# profile: Monday-Sunday, Holiday, Heating-Rm, Cooling-Rm, Heating-Sys and
# Cooling-Sys.  This is confirmed by read-only runtime inspection of both
# modulating and absolute ``iesve.GroupProfile`` objects in VE 2025.
VE_WEEKLY_PROFILE_SLOT_COUNT = 12
REQUIRED_CONSTRUCTION_ASSIGNMENTS = {
    "external_wall_construction_id",
    "roof_construction_id",
    "ground_floor_construction_id",
    "internal_wall_construction_id",
    "door_construction_id",
    "glazing_construction_id",
}


def _strict_keys(
    payload: Mapping[str, Any], allowed: Iterable[str], context: str
) -> None:
    """Reject fields outside the explicit manifest contract."""

    unknown = sorted(set(payload) - set(allowed))
    if unknown:
        raise ConfigurationError("Unsupported fields in {}: {}".format(context, unknown))


def _required_text(payload: Mapping[str, Any], key: str, context: str) -> str:
    """Return one required non-empty textual manifest value."""

    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError("{}.{} must be non-empty text".format(context, key))
    return value.strip()


def _as_mapping(value: Any, context: str) -> Mapping[str, Any]:
    """Return a mapping value or raise a contextual configuration error."""

    if not isinstance(value, Mapping):
        raise ConfigurationError("{} must be a JSON object".format(context))
    return value


def _as_sequence(value: Any, context: str) -> Sequence[Any]:
    """Return a non-string sequence or raise a configuration error."""

    if not isinstance(value, list):
        raise ConfigurationError("{} must be a JSON array".format(context))
    return value


@dataclass(frozen=True)
class Evidence:
    """Provenance and purpose statement for one generated VE asset."""

    description: str
    source: str
    source_locator: str

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any], context: str) -> "Evidence":
        """Parse evidence fields from an asset definition mapping."""

        return cls(
            description=_required_text(payload, "description", context),
            source=_required_text(payload, "source", context),
            source_locator=_required_text(payload, "source_locator", context),
        )

    def validation_error(self) -> Optional[str]:
        """Return an error when provenance is still a placeholder."""

        if self.source.upper().startswith("PLACEHOLDER"):
            return "asset source is still a placeholder"
        return None

    def to_dict(self) -> Dict[str, str]:
        """Return evidence metadata as serializable data."""

        return {
            "description": self.description,
            "source": self.source,
            "source_locator": self.source_locator,
        }


@dataclass(frozen=True)
class TraceableField:
    """One typed value with complete source and range metadata."""

    value: Any
    description: str
    units: str
    source: str
    source_locator: str
    validation_range: ValidationRange
    required: bool = True

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any], context: str) -> "TraceableField":
        """Parse and structurally validate one traceable value."""

        _strict_keys(
            payload,
            {
                "value",
                "description",
                "units",
                "source",
                "source_locator",
                "validation_range",
                "required",
            },
            context,
        )
        range_payload = _as_mapping(
            payload.get("validation_range"), "{}.validation_range".format(context)
        )
        _strict_keys(
            range_payload,
            {"expected_type", "minimum", "maximum", "allowed_values", "allow_none"},
            "{}.validation_range".format(context),
        )
        expected_type = _required_text(
            range_payload, "expected_type", "{}.validation_range".format(context)
        )
        if expected_type not in {
            "number",
            "integer",
            "string",
            "path",
            "boolean",
            "array",
            "object",
            "any",
        }:
            raise ConfigurationError(
                "{}.validation_range.expected_type is unsupported".format(context)
            )
        allowed = range_payload.get("allowed_values", [])
        if not isinstance(allowed, list):
            raise ConfigurationError(
                "{}.validation_range.allowed_values must be an array".format(context)
            )
        return cls(
            value=payload.get("value"),
            description=_required_text(payload, "description", context),
            units=_required_text(payload, "units", context),
            source=_required_text(payload, "source", context),
            source_locator=_required_text(payload, "source_locator", context),
            validation_range=ValidationRange(
                expected_type=expected_type,
                minimum=range_payload.get("minimum"),
                maximum=range_payload.get("maximum"),
                allowed_values=tuple(allowed),
                allow_none=bool(range_payload.get("allow_none", False)),
            ),
            required=bool(payload.get("required", True)),
        )

    def validation_error(self) -> Optional[str]:
        """Validate value, provenance, and required-state semantics."""

        if self.value is None and not self.required:
            return None
        error = self.validation_range.validate(self.value)
        if error:
            return error
        if self.value is not None and self.source.upper().startswith("PLACEHOLDER"):
            return "populated value requires a non-placeholder source"
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Return the complete field evidence record."""

        return {
            "value": self.value,
            "description": self.description,
            "units": self.units,
            "source": self.source,
            "source_locator": self.source_locator,
            "validation_range": self.validation_range.to_dict(),
            "required": self.required,
        }


def _parse_fields(value: Any, context: str) -> Dict[str, TraceableField]:
    """Parse a mapping of VE property names to traceable fields."""

    payload = _as_mapping(value, context)
    return {
        str(name): TraceableField.from_mapping(
            _as_mapping(field, "{}.{}".format(context, name)),
            "{}.{}".format(context, name),
        )
        for name, field in payload.items()
    }


def _raw_fields(fields: Mapping[str, TraceableField]) -> Dict[str, Any]:
    """Return populated raw values ready for a VE API setter."""

    return {
        name: field.value for name, field in fields.items() if field.value is not None
    }


@dataclass(frozen=True)
class ProfileDefinition:
    """Definition of one profile to create in the active VE project."""

    key: str
    profile_type: str
    reference: str
    modulating: bool
    units: int
    data: TraceableField
    evidence: Evidence

    def to_dict(self) -> Dict[str, Any]:
        """Return the serializable profile definition."""

        payload = self.evidence.to_dict()
        payload.update(
            {
                "key": self.key,
                "profile_type": self.profile_type,
                "reference": self.reference,
                "modulating": self.modulating,
                "units": self.units,
                "data": self.data.to_dict(),
            }
        )
        return payload


@dataclass(frozen=True)
class MaterialDefinition:
    """Definition of one opaque or glazed CDB material."""

    key: str
    category: str
    properties: Dict[str, TraceableField]
    evidence: Evidence

    def raw_properties(self) -> Dict[str, Any]:
        """Return populated material properties for ``set_properties``."""

        return _raw_fields(self.properties)

    def to_dict(self) -> Dict[str, Any]:
        """Return the serializable CDB material definition."""

        payload = self.evidence.to_dict()
        payload.update(
            {
                "key": self.key,
                "category": self.category,
                "properties": {
                    name: field.to_dict() for name, field in self.properties.items()
                },
            }
        )
        return payload


@dataclass(frozen=True)
class LayerDefinition:
    """Definition of one ordered construction layer."""

    material_key: str
    is_cavity: bool
    properties: Dict[str, TraceableField]

    def raw_properties(self) -> Dict[str, Any]:
        """Return populated layer properties for VE."""

        return _raw_fields(self.properties)

    def to_dict(self) -> Dict[str, Any]:
        """Return the serializable construction-layer definition."""

        return {
            "material_key": self.material_key,
            "is_cavity": self.is_cavity,
            "properties": {
                name: field.to_dict() for name, field in self.properties.items()
            },
        }


@dataclass(frozen=True)
class ConstructionDefinition:
    """Definition of one CDB construction and its assignment role."""

    key: str
    assignment_parameter: str
    category: str
    construction_class: str
    properties: Dict[str, TraceableField]
    layers: Tuple[LayerDefinition, ...]
    evidence: Evidence

    def raw_properties(self) -> Dict[str, Any]:
        """Return populated construction properties for VE."""

        return _raw_fields(self.properties)

    def to_dict(self) -> Dict[str, Any]:
        """Return the serializable CDB construction definition."""

        payload = self.evidence.to_dict()
        payload.update(
            {
                "key": self.key,
                "assignment_parameter": self.assignment_parameter,
                "category": self.category,
                "construction_class": self.construction_class,
                "properties": {
                    name: field.to_dict() for name, field in self.properties.items()
                },
                "layers": [layer.to_dict() for layer in self.layers],
            }
        )
        return payload


@dataclass(frozen=True)
class GainDefinition:
    """Definition of one people, lighting, or equipment gain."""

    key: str
    category: str
    subtype: str
    units: str
    properties: Dict[str, TraceableField]
    evidence: Evidence

    def raw_properties(self) -> Dict[str, Any]:
        """Return populated casual-gain properties for VE."""

        return _raw_fields(self.properties)

    def to_dict(self) -> Dict[str, Any]:
        """Return the serializable gain definition."""

        payload = self.evidence.to_dict()
        payload.update(
            {
                "key": self.key,
                "category": self.category,
                "subtype": self.subtype,
                "units": self.units,
                "properties": {
                    name: field.to_dict() for name, field in self.properties.items()
                },
            }
        )
        return payload


@dataclass(frozen=True)
class AirExchangeDefinition:
    """Definition of one infiltration or ventilation exchange."""

    key: str
    exchange_type: str
    units: str
    adjacent_condition: str
    properties: Dict[str, TraceableField]
    evidence: Evidence

    def raw_properties(self) -> Dict[str, Any]:
        """Return populated air-exchange properties for VE."""

        return _raw_fields(self.properties)

    def to_dict(self) -> Dict[str, Any]:
        """Return the serializable air-exchange definition."""

        payload = self.evidence.to_dict()
        payload.update(
            {
                "key": self.key,
                "exchange_type": self.exchange_type,
                "units": self.units,
                "adjacent_condition": self.adjacent_condition,
                "properties": {
                    name: field.to_dict() for name, field in self.properties.items()
                },
            }
        )
        return payload


@dataclass(frozen=True)
class ApacheSystemDefinition:
    """Optional definition of a new simplified Apache system."""

    name: str
    from_id: Optional[str]
    evidence: Evidence

    def to_dict(self) -> Dict[str, Any]:
        """Return the serializable Apache-system definition."""

        payload = self.evidence.to_dict()
        payload.update({"name": self.name, "from_id": self.from_id})
        return payload


@dataclass(frozen=True)
class ThermalTemplateDefinition:
    """Definition of the new thermal template and its linked assets."""

    name: str
    standard: str
    room_conditions: Dict[str, TraceableField]
    system_data: Dict[str, TraceableField]
    gain_keys: Tuple[str, ...]
    air_exchange_keys: Tuple[str, ...]
    evidence: Evidence

    def raw_room_conditions(self) -> Dict[str, Any]:
        """Return populated template room-condition fields."""

        return _raw_fields(self.room_conditions)

    def raw_system_data(self) -> Dict[str, Any]:
        """Return populated template system fields."""

        return _raw_fields(self.system_data)

    def to_dict(self) -> Dict[str, Any]:
        """Return the serializable thermal-template definition."""

        payload = self.evidence.to_dict()
        payload.update(
            {
                "name": self.name,
                "standard": self.standard,
                "room_conditions": {
                    name: field.to_dict() for name, field in self.room_conditions.items()
                },
                "system_data": {
                    name: field.to_dict() for name, field in self.system_data.items()
                },
                "gain_keys": list(self.gain_keys),
                "air_exchange_keys": list(self.air_exchange_keys),
            }
        )
        return payload


def _profile_references(value: Any) -> Set[str]:
    """Collect logical profile references from nested field values."""

    references: Set[str] = set()
    if isinstance(value, Mapping):
        if set(value) == {"profile_ref"} and isinstance(value["profile_ref"], str):
            references.add(value["profile_ref"])
        else:
            for child in value.values():
                references.update(_profile_references(child))
    elif isinstance(value, (list, tuple)):
        for child in value:
            references.update(_profile_references(child))
    return references


@dataclass(frozen=True)
class AssetManifest:
    """Complete source-traced package for creating VE project assets."""

    schema_version: str
    on_existing: str
    profiles: Tuple[ProfileDefinition, ...]
    materials: Tuple[MaterialDefinition, ...]
    constructions: Tuple[ConstructionDefinition, ...]
    gains: Tuple[GainDefinition, ...]
    air_exchanges: Tuple[AirExchangeDefinition, ...]
    thermal_template: ThermalTemplateDefinition
    apache_system: Optional[ApacheSystemDefinition]
    source_path: str
    source_checksum: str

    @property
    def planned_parameter_names(self) -> Set[str]:
        """Return configuration fields populated by successful provisioning."""

        planned = {
            construction.assignment_parameter for construction in self.constructions
        }
        planned.update({"thermal_template_name", "thermal_template_source_record"})
        if any(profile.key == "occupancy_profile" for profile in self.profiles):
            planned.add("occupancy_profile_id")
        if self.apache_system is not None:
            planned.add("hvac_system_id")
        return planned

    def validation_errors(self) -> List[str]:
        """Return all structural, provenance, range, and reference errors."""

        errors: List[str] = []
        collections = {
            "profile": self.profiles,
            "material": self.materials,
            "construction": self.constructions,
            "gain": self.gains,
            "air_exchange": self.air_exchanges,
        }
        for label, records in collections.items():
            keys = [record.key for record in records]
            if len(keys) != len(set(keys)):
                errors.append("duplicate {} keys".format(label))
            for record in records:
                evidence_error = record.evidence.validation_error()
                if evidence_error:
                    errors.append("{} {}: {}".format(label, record.key, evidence_error))

        profile_keys = {profile.key for profile in self.profiles}
        profile_references = [profile.reference for profile in self.profiles]
        if len(profile_references) != len(set(profile_references)):
            errors.append("duplicate profile references")
        material_keys = {material.key for material in self.materials}
        gain_keys = {gain.key for gain in self.gains}
        exchange_keys = {exchange.key for exchange in self.air_exchanges}
        assignments = {
            construction.assignment_parameter for construction in self.constructions
        }
        missing_assignments = sorted(REQUIRED_CONSTRUCTION_ASSIGNMENTS - assignments)
        extra_assignments = sorted(assignments - REQUIRED_CONSTRUCTION_ASSIGNMENTS)
        if missing_assignments:
            errors.append(
                "missing construction assignment roles: {}".format(missing_assignments)
            )
        if extra_assignments:
            errors.append(
                "unsupported construction assignment roles: {}".format(extra_assignments)
            )
        # A manifest may intentionally use only VE's persistent built-in
        # profiles. Logical ``profile_ref`` values are still checked below and
        # therefore cannot silently resolve when ``profiles`` is empty. This
        # avoids manufacturing volatile DAY_* IDs for constant schedules.
        if not self.profiles:
            invalid_builtin_profiles = []
            for label, records in (
                ("gain", self.gains),
                ("air_exchange", self.air_exchanges),
            ):
                for record in records:
                    field = record.properties.get("variation_profile")
                    if field is None or field.value != "ON":
                        invalid_builtin_profiles.append("{} {}".format(label, record.key))
            if invalid_builtin_profiles:
                errors.append(
                    "manifests without project profiles require explicit VE "
                    "built-in ON variation profiles: {}".format(
                        sorted(invalid_builtin_profiles)
                    )
                )
        if not self.materials:
            errors.append("at least one CDB material is required")
        if not self.constructions:
            errors.append("all required CDB constructions are required")
        required_gain_categories = {"people", "lighting", "energy"}
        actual_gain_categories = {gain.category for gain in self.gains}
        if required_gain_categories - actual_gain_categories:
            errors.append(
                "people, lighting and energy gains are required for completeness"
            )
        if not self.air_exchanges:
            errors.append("at least one source-traced air exchange is required")
        if self.thermal_template.evidence.validation_error():
            errors.append("thermal template source is still a placeholder")
        if self.apache_system and self.apache_system.evidence.validation_error():
            errors.append("Apache system source is still a placeholder")

        for profile in self.profiles:
            profile_type = profile.profile_type.lower()
            if profile_type not in SUPPORTED_PROFILE_TYPES:
                errors.append(
                    "profile {} has unsupported profile_type {!r}".format(
                        profile.key, profile.profile_type
                    )
                )
            error = profile.data.validation_error()
            if error:
                errors.append("profile {} data: {}".format(profile.key, error))
            dependencies = _profile_references(profile.data.value)
            if profile_type == "daily" and dependencies:
                errors.append(
                    "daily profile {} cannot reference other profiles".format(profile.key)
                )
            if profile_type in {"weekly", "yearly"} and not dependencies:
                errors.append(
                    "{} profile {} must use logical profile_ref dependencies".format(
                        profile_type, profile.key
                    )
                )
            if profile_type == "weekly":
                weekly_data = profile.data.value
                if (
                    not isinstance(weekly_data, (list, tuple))
                    or len(weekly_data) != VE_WEEKLY_PROFILE_SLOT_COUNT
                ):
                    errors.append(
                        "weekly profile {} must contain exactly {} daily-profile "
                        "slots for VE 2025".format(
                            profile.key,
                            VE_WEEKLY_PROFILE_SLOT_COUNT,
                        )
                    )
        for material in self.materials:
            errors.extend(
                _field_errors("material {}".format(material.key), material.properties)
            )
        for construction in self.constructions:
            errors.extend(
                _field_errors(
                    "construction {}".format(construction.key), construction.properties
                )
            )
            if not construction.layers:
                errors.append("construction {} has no layers".format(construction.key))
            for index, layer in enumerate(construction.layers, 1):
                if layer.material_key not in material_keys:
                    errors.append(
                        "construction {} layer {} references unknown material {}".format(
                            construction.key, index, layer.material_key
                        )
                    )
                errors.extend(
                    _field_errors(
                        "construction {} layer {}".format(construction.key, index),
                        layer.properties,
                    )
                )
        for gain in self.gains:
            errors.extend(_field_errors("gain {}".format(gain.key), gain.properties))
        for exchange in self.air_exchanges:
            errors.extend(
                _field_errors("air exchange {}".format(exchange.key), exchange.properties)
            )
        errors.extend(
            _field_errors(
                "thermal template room conditions", self.thermal_template.room_conditions
            )
        )
        errors.extend(
            _field_errors(
                "thermal template system data", self.thermal_template.system_data
            )
        )

        missing_gains = sorted(set(self.thermal_template.gain_keys) - gain_keys)
        missing_exchanges = sorted(
            set(self.thermal_template.air_exchange_keys) - exchange_keys
        )
        if missing_gains:
            errors.append(
                "thermal template references unknown gains: {}".format(missing_gains)
            )
        if missing_exchanges:
            errors.append(
                "thermal template references unknown air exchanges: {}".format(
                    missing_exchanges
                )
            )
        if set(self.thermal_template.gain_keys) != gain_keys:
            errors.append("every defined gain must be linked to the thermal template")
        if set(self.thermal_template.air_exchange_keys) != exchange_keys:
            errors.append(
                "every defined air exchange must be linked to the thermal template"
            )

        referenced_profiles: Set[str] = set()
        for profile in self.profiles:
            referenced_profiles.update(_profile_references(profile.data.value))
        for record in list(self.gains) + list(self.air_exchanges):
            for field in record.properties.values():
                referenced_profiles.update(_profile_references(field.value))
        for field in list(self.thermal_template.room_conditions.values()) + list(
            self.thermal_template.system_data.values()
        ):
            referenced_profiles.update(_profile_references(field.value))
        unknown_profiles = sorted(referenced_profiles - profile_keys)
        if unknown_profiles:
            errors.append(
                "unknown logical profile references: {}".format(unknown_profiles)
            )
        profile_dependencies = {
            profile.key: _profile_references(profile.data.value) & profile_keys
            for profile in self.profiles
        }
        resolved_profiles: Set[str] = set()
        remaining_profiles = set(profile_dependencies)
        while remaining_profiles:
            ready = {
                key
                for key in remaining_profiles
                if profile_dependencies[key] <= resolved_profiles
            }
            if not ready:
                errors.append(
                    "cyclic logical profile references: {}".format(
                        sorted(remaining_profiles)
                    )
                )
                break
            resolved_profiles.update(ready)
            remaining_profiles -= ready
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Return the canonical serializable asset manifest."""

        return {
            "schema_version": self.schema_version,
            "on_existing": self.on_existing,
            "profiles": [item.to_dict() for item in self.profiles],
            "materials": [item.to_dict() for item in self.materials],
            "constructions": [item.to_dict() for item in self.constructions],
            "gains": [item.to_dict() for item in self.gains],
            "air_exchanges": [item.to_dict() for item in self.air_exchanges],
            "thermal_template": self.thermal_template.to_dict(),
            "apache_system": self.apache_system.to_dict() if self.apache_system else None,
            "source_path": self.source_path,
            "source_checksum": self.source_checksum,
        }


def _field_errors(context: str, fields: Mapping[str, TraceableField]) -> List[str]:
    """Return validation errors for a group of traceable fields."""

    errors = []
    for name, field in fields.items():
        error = field.validation_error()
        if error:
            errors.append("{}.{}: {}".format(context, name, error))
    return errors


def _parse_profile(payload: Mapping[str, Any], context: str) -> ProfileDefinition:
    """Parse one profile definition from JSON data."""

    _strict_keys(
        payload,
        {
            "key",
            "profile_type",
            "reference",
            "modulating",
            "units",
            "data",
            "description",
            "source",
            "source_locator",
        },
        context,
    )
    data = TraceableField.from_mapping(
        _as_mapping(payload.get("data"), "{}.data".format(context)),
        "{}.data".format(context),
    )
    return ProfileDefinition(
        key=_required_text(payload, "key", context),
        profile_type=_required_text(payload, "profile_type", context),
        reference=_required_text(payload, "reference", context),
        modulating=bool(payload.get("modulating", True)),
        units=int(payload.get("units", -1)),
        data=data,
        evidence=Evidence.from_mapping(payload, context),
    )


def _parse_material(payload: Mapping[str, Any], context: str) -> MaterialDefinition:
    """Parse one CDB material definition from JSON data."""

    _strict_keys(
        payload,
        {"key", "category", "properties", "description", "source", "source_locator"},
        context,
    )
    return MaterialDefinition(
        key=_required_text(payload, "key", context),
        category=_required_text(payload, "category", context),
        properties=_parse_fields(
            payload.get("properties"), "{}.properties".format(context)
        ),
        evidence=Evidence.from_mapping(payload, context),
    )


def _parse_layer(payload: Mapping[str, Any], context: str) -> LayerDefinition:
    """Parse one ordered CDB construction-layer definition."""

    _strict_keys(payload, {"material_key", "is_cavity", "properties"}, context)
    return LayerDefinition(
        material_key=_required_text(payload, "material_key", context),
        is_cavity=bool(payload.get("is_cavity", False)),
        properties=_parse_fields(
            payload.get("properties", {}), "{}.properties".format(context)
        ),
    )


def _parse_construction(
    payload: Mapping[str, Any], context: str
) -> ConstructionDefinition:
    """Parse one CDB construction definition from JSON data."""

    _strict_keys(
        payload,
        {
            "key",
            "assignment_parameter",
            "category",
            "construction_class",
            "properties",
            "layers",
            "description",
            "source",
            "source_locator",
        },
        context,
    )
    layers = tuple(
        _parse_layer(
            _as_mapping(item, "{} layer".format(context)),
            "{}.layers[{}]".format(context, index),
        )
        for index, item in enumerate(
            _as_sequence(payload.get("layers"), "{}.layers".format(context))
        )
    )
    return ConstructionDefinition(
        key=_required_text(payload, "key", context),
        assignment_parameter=_required_text(payload, "assignment_parameter", context),
        category=_required_text(payload, "category", context),
        construction_class=_required_text(payload, "construction_class", context),
        properties=_parse_fields(
            payload.get("properties", {}), "{}.properties".format(context)
        ),
        layers=layers,
        evidence=Evidence.from_mapping(payload, context),
    )


def _parse_gain(payload: Mapping[str, Any], context: str) -> GainDefinition:
    """Parse one source-traced internal-gain definition."""

    _strict_keys(
        payload,
        {
            "key",
            "category",
            "subtype",
            "units",
            "properties",
            "description",
            "source",
            "source_locator",
        },
        context,
    )
    category = _required_text(payload, "category", context)
    if category not in {"people", "lighting", "energy"}:
        raise ConfigurationError("{}.category is unsupported".format(context))
    return GainDefinition(
        key=_required_text(payload, "key", context),
        category=category,
        subtype=_required_text(payload, "subtype", context),
        units=_required_text(payload, "units", context),
        properties=_parse_fields(
            payload.get("properties"), "{}.properties".format(context)
        ),
        evidence=Evidence.from_mapping(payload, context),
    )


def _parse_air_exchange(
    payload: Mapping[str, Any], context: str
) -> AirExchangeDefinition:
    """Parse one source-traced air-exchange definition."""

    _strict_keys(
        payload,
        {
            "key",
            "exchange_type",
            "units",
            "adjacent_condition",
            "properties",
            "description",
            "source",
            "source_locator",
        },
        context,
    )
    return AirExchangeDefinition(
        key=_required_text(payload, "key", context),
        exchange_type=_required_text(payload, "exchange_type", context),
        units=_required_text(payload, "units", context),
        adjacent_condition=_required_text(payload, "adjacent_condition", context),
        properties=_parse_fields(
            payload.get("properties"), "{}.properties".format(context)
        ),
        evidence=Evidence.from_mapping(payload, context),
    )


def _parse_template(
    payload: Mapping[str, Any], context: str
) -> ThermalTemplateDefinition:
    """Parse the one thermal-template definition in a manifest."""

    _strict_keys(
        payload,
        {
            "name",
            "standard",
            "room_conditions",
            "system_data",
            "gain_keys",
            "air_exchange_keys",
            "description",
            "source",
            "source_locator",
        },
        context,
    )
    return ThermalTemplateDefinition(
        name=_required_text(payload, "name", context),
        standard=_required_text(payload, "standard", context),
        room_conditions=_parse_fields(
            payload.get("room_conditions"), "{}.room_conditions".format(context)
        ),
        system_data=_parse_fields(
            payload.get("system_data"), "{}.system_data".format(context)
        ),
        gain_keys=tuple(
            str(value)
            for value in _as_sequence(
                payload.get("gain_keys"), "{}.gain_keys".format(context)
            )
        ),
        air_exchange_keys=tuple(
            str(value)
            for value in _as_sequence(
                payload.get("air_exchange_keys"), "{}.air_exchange_keys".format(context)
            )
        ),
        evidence=Evidence.from_mapping(payload, context),
    )


def _parse_apache_system(value: Any, context: str) -> Optional[ApacheSystemDefinition]:
    """Parse an optional simplified Apache-system definition."""

    if value is None:
        return None
    payload = _as_mapping(value, context)
    _strict_keys(
        payload,
        {"name", "from_id", "description", "source", "source_locator"},
        context,
    )
    from_id = payload.get("from_id")
    if from_id is not None and (not isinstance(from_id, str) or not from_id.strip()):
        raise ConfigurationError(
            "{}.from_id must be null or non-empty text".format(context)
        )
    return ApacheSystemDefinition(
        name=_required_text(payload, "name", context),
        from_id=from_id.strip() if isinstance(from_id, str) else None,
        evidence=Evidence.from_mapping(payload, context),
    )


def load_asset_manifest(path: Union[str, Path]) -> AssetManifest:
    """Load, checksum, parse, and validate a VE asset manifest."""

    manifest_path = Path(path)
    if not manifest_path.is_file():
        raise ConfigurationError("Asset manifest not found: {}".format(manifest_path))
    raw = manifest_path.read_bytes()
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise ConfigurationError("Unable to read asset manifest: {}".format(exc)) from exc
    payload = _as_mapping(payload, "asset manifest")
    _strict_keys(
        payload,
        {
            "schema_version",
            "on_existing",
            "profiles",
            "materials",
            "constructions",
            "gains",
            "air_exchanges",
            "thermal_template",
            "apache_system",
            "metadata",
        },
        "asset manifest",
    )
    schema_version = str(payload.get("schema_version", ""))
    if schema_version not in SUPPORTED_ASSET_MANIFEST_VERSIONS:
        raise ConfigurationError(
            "Unsupported asset manifest schema_version '{}'".format(schema_version)
        )
    on_existing = str(payload.get("on_existing", ""))
    if on_existing not in {"fail", "reuse_verified"}:
        raise ConfigurationError(
            "Asset manifest on_existing must be 'fail' or 'reuse_verified'"
        )

    def parse_list(name: str, parser):
        """Parse one homogeneous list with stable contextual locations."""

        return tuple(
            parser(
                _as_mapping(item, "{}[{}]".format(name, index)),
                "{}[{}]".format(name, index),
            )
            for index, item in enumerate(_as_sequence(payload.get(name), name))
        )

    manifest = AssetManifest(
        schema_version=schema_version,
        on_existing=on_existing,
        profiles=parse_list("profiles", _parse_profile),
        materials=parse_list("materials", _parse_material),
        constructions=parse_list("constructions", _parse_construction),
        gains=parse_list("gains", _parse_gain),
        air_exchanges=parse_list("air_exchanges", _parse_air_exchange),
        thermal_template=_parse_template(
            _as_mapping(payload.get("thermal_template"), "thermal_template"),
            "thermal_template",
        ),
        apache_system=_parse_apache_system(payload.get("apache_system"), "apache_system"),
        source_path=str(manifest_path.resolve()),
        source_checksum=hashlib.sha256(raw).hexdigest(),
    )
    errors = manifest.validation_errors()
    if errors:
        raise ConfigurationError(
            "Asset manifest validation failed: {}".format("; ".join(errors))
        )
    return manifest
