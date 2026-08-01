"""Central configuration contract for the Swiss reference model.

Every parameter carries its description, units, source field, and validation
range.  Values sourced from SIA 380/2 are comparison/reference-project inputs;
they are never silently substituted for project design values.  Parameters
that require SIA 2024, SIA 2028, SIA 387/4, an approved project construction
catalog, or official SIA 4010 files remain explicit placeholders.
"""

from dataclasses import asdict, dataclass, replace
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple

from .exceptions import ConfigurationError


class ParameterCategory(str, Enum):
    """Stable categories for grouping all reference-model parameters."""

    BUILDING = "Building Parameters"
    ENVELOPE = "Envelope Parameters"
    WINDOW = "Window Parameters"
    CLIMATE = "Climate Parameters"
    VENTILATION = "Ventilation Parameters"
    OCCUPANCY = "Occupancy Parameters"
    INTERNAL_GAINS = "Internal Gains Parameters"
    THERMAL_BRIDGES = "Thermal Bridge Parameters"
    TEMPLATE = "Thermal Template Parameters"
    HVAC = "HVAC Placeholder Parameters"
    REGULATORY = "Placeholder Regulatory Parameters"


@dataclass(frozen=True)
class ValidationRange:
    """Machine-readable range and type constraint for one value."""

    expected_type: str
    minimum: Optional[float] = None
    maximum: Optional[float] = None
    allowed_values: Tuple[Any, ...] = ()
    allow_none: bool = False

    def validate(self, value: Any) -> Optional[str]:
        """Return a validation error message, or ``None`` when valid."""

        if value is None:
            return None if self.allow_none else "value is required"

        valid_type = True
        if self.expected_type == "number":
            valid_type = isinstance(value, (int, float)) and not isinstance(value, bool)
        elif self.expected_type == "integer":
            valid_type = isinstance(value, int) and not isinstance(value, bool)
        elif self.expected_type in ("string", "path"):
            valid_type = isinstance(value, str) and bool(value.strip())
        elif self.expected_type == "boolean":
            valid_type = isinstance(value, bool)
        elif self.expected_type == "array":
            valid_type = isinstance(value, (list, tuple))
        elif self.expected_type == "object":
            valid_type = isinstance(value, Mapping)
        elif self.expected_type == "any":
            valid_type = True

        if not valid_type:
            return "expected {}".format(self.expected_type)
        if self.allowed_values and value not in self.allowed_values:
            return "value must be one of {}".format(list(self.allowed_values))
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            if self.minimum is not None and value < self.minimum:
                return "value must be >= {}".format(self.minimum)
            if self.maximum is not None and value > self.maximum:
                return "value must be <= {}".format(self.maximum)
        return None

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-serializable representation of this constraint."""

        data = asdict(self)
        data["allowed_values"] = list(self.allowed_values)
        return data


@dataclass(frozen=True)
class ComplianceParameter:
    """A traceable configuration parameter and its current value."""

    name: str
    category: ParameterCategory
    description: str
    units: str
    source: str
    source_locator: str
    validation_range: ValidationRange
    value: Any = None
    required_for_generation: bool = False
    compliance_relevant: bool = True
    comparison_only: bool = False

    @property
    def is_placeholder(self) -> bool:
        """Return whether the parameter still lacks authoritative evidence."""

        return self.value is None or self.source.upper().startswith("PLACEHOLDER")

    def validate(self) -> Optional[str]:
        """Validate the current value against its declared constraint."""

        return self.validation_range.validate(self.value)

    def to_dict(self) -> Dict[str, Any]:
        """Return the complete machine-readable parameter evidence record."""

        return {
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "units": self.units,
            "source": self.source,
            "source_locator": self.source_locator,
            "validation_range": self.validation_range.to_dict(),
            "value": self.value,
            "required_for_generation": self.required_for_generation,
            "compliance_relevant": self.compliance_relevant,
            "comparison_only": self.comparison_only,
            "is_placeholder": self.is_placeholder,
        }


class ParameterRegistry:
    """Validated, immutable-value registry with controlled overrides."""

    def __init__(self, parameters: Iterable[ComplianceParameter]):
        """Initialize the registry after rejecting duplicate parameter names."""

        items = list(parameters)
        names = [item.name for item in items]
        if len(names) != len(set(names)):
            raise ConfigurationError("Duplicate parameter names are not permitted")
        self._parameters = {item.name: item for item in items}

    def __contains__(self, name: str) -> bool:
        """Return whether a parameter name exists in this registry."""

        return name in self._parameters

    def __iter__(self):
        """Iterate over parameters in stable name order."""

        for name in sorted(self._parameters):
            yield self._parameters[name]

    def get_parameter(self, name: str) -> ComplianceParameter:
        """Return one named parameter or raise a configuration error."""

        try:
            return self._parameters[name]
        except KeyError as exc:
            raise ConfigurationError("Unknown parameter: {}".format(name)) from exc

    def value(self, name: str) -> Any:
        """Return the current value of one named parameter."""

        return self.get_parameter(name).value

    def with_overrides(self, overrides: Mapping[str, Any]) -> "ParameterRegistry":
        """Return a validated registry containing source-traced overrides."""

        updated = dict(self._parameters)
        for name, override in overrides.items():
            if name not in updated:
                raise ConfigurationError("Unknown parameter override: {}".format(name))
            original = updated[name]
            if isinstance(override, Mapping):
                unknown = set(override) - {"value", "source", "source_locator"}
                if unknown:
                    raise ConfigurationError(
                        "Unsupported fields for {}: {}".format(name, sorted(unknown))
                    )
                value = override.get("value")
                source = override.get("source", original.source)
                source_locator = override.get("source_locator", original.source_locator)
            else:
                value = override
                source = original.source
                source_locator = original.source_locator

            if original.compliance_relevant and value is not None:
                if not source or source.upper().startswith("PLACEHOLDER"):
                    raise ConfigurationError(
                        "Compliance-relevant override '{}' requires a non-placeholder source".format(
                            name
                        )
                    )
            candidate = replace(
                original,
                value=value,
                source=str(source),
                source_locator=str(source_locator),
            )
            error = candidate.validate()
            if error:
                raise ConfigurationError("{}: {}".format(name, error))
            updated[name] = candidate
        return ParameterRegistry(updated.values())

    def unresolved_required(self) -> List[ComplianceParameter]:
        """Return required generation inputs that remain without values."""

        return [
            parameter
            for parameter in self
            if parameter.required_for_generation and parameter.value is None
        ]

    def placeholders(self) -> List[ComplianceParameter]:
        """Return every parameter still identified as a placeholder."""

        return [parameter for parameter in self if parameter.is_placeholder]

    def validation_errors(self) -> Dict[str, str]:
        """Return value validation errors indexed by parameter name."""

        errors: Dict[str, str] = {}
        for parameter in self:
            error = parameter.validate()
            if error and (parameter.value is not None or parameter.required_for_generation):
                errors[parameter.name] = error
        return errors

    def to_dict(self) -> Dict[str, Dict[str, Any]]:
        """Return the complete registry as a serializable mapping."""

        return {parameter.name: parameter.to_dict() for parameter in self}


PLACEHOLDER = "PLACEHOLDER - authoritative project or referenced-standard input required"
PROJECT_ASSUMPTION = "Reference-model geometry assumption; non-regulatory"
PROJECT_CATALOG = "PLACEHOLDER - approved project CDB catalog identifier required"
SIA3802_TABLE2 = "SIA 380/2:2022 FR, Table 2 reference-project value"
SIA3802_TABLE3 = "SIA 380/2:2022 FR, Table 3 reference-project value"
SIA3802_TABLE11 = "SIA 380/2:2022 FR, normative Annex C, Table 11"
IESVE_API = "IESVE VE 2023 VEScript User Guide"


def _range(
    expected_type: str,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
    allowed_values: Tuple[Any, ...] = (),
    allow_none: bool = False,
) -> ValidationRange:
    """Build a compact validation-range declaration for the registry."""

    return ValidationRange(
        expected_type=expected_type,
        minimum=minimum,
        maximum=maximum,
        allowed_values=allowed_values,
        allow_none=allow_none,
    )


def _parameter(
    name: str,
    category: ParameterCategory,
    description: str,
    units: str,
    source: str,
    source_locator: str,
    validation_range: ValidationRange,
    value: Any = None,
    required: bool = False,
    compliance_relevant: bool = True,
    comparison_only: bool = False,
) -> ComplianceParameter:
    """Build one compliance parameter from explicit metadata fields."""

    return ComplianceParameter(
        name=name,
        category=category,
        description=description,
        units=units,
        source=source,
        source_locator=source_locator,
        validation_range=validation_range,
        value=value,
        required_for_generation=required,
        compliance_relevant=compliance_relevant,
        comparison_only=comparison_only,
    )


def build_default_registry() -> ParameterRegistry:
    """Return the fail-closed reference configuration.

    Geometry assumptions have explicit non-regulatory defaults.  All inputs
    that determine Swiss compliance or VE construction/template/weather data
    remain unset until a traceable override is supplied.
    """

    p = _parameter
    c = ParameterCategory
    parameters = [
        p("model_identifier", c.BUILDING, "Stable model namespace and room-name prefix.", "text", PROJECT_ASSUMPTION, "Architecture decision RM-001", _range("string"), "SIA_REF", compliance_relevant=False),
        p("model_schema_version", c.BUILDING, "Reference-model configuration schema version.", "text", PROJECT_ASSUMPTION, "Architecture decision RM-002", _range("string"), "1.0.0", compliance_relevant=False),
        p("gbxml_schema_version", c.BUILDING, "gbXML serialization profile; 6.01 is the conservative VE 2023 interoperability baseline and must be confirmed for the installed VE release.", "version", PROJECT_ASSUMPTION, "gbXML/VE interoperability decision RM-006", _range("string", allowed_values=("5.12", "6.01", "7.03")), "6.01", compliance_relevant=False),
        p("building_name", c.BUILDING, "Human-readable name of the generated reference building.", "text", PROJECT_ASSUMPTION, "Reference model brief", _range("string"), "Swiss SIA Reference Building", compliance_relevant=False),
        p("gbxml_building_type", c.BUILDING, "gbXML building classification; not a SIA 2024 use category.", "enum", PROJECT_ASSUMPTION, "gbXML 7.03 Building contract", _range("string", allowed_values=("Office", "School", "Retail", "Other")), "Office", compliance_relevant=False),
        p("building_width_m", c.BUILDING, "Overall east-west reference-model dimension.", "m", PROJECT_ASSUMPTION, "Reference geometry contract", _range("number", 4.0, 200.0), 20.0, compliance_relevant=False),
        p("building_depth_m", c.BUILDING, "Overall north-south reference-model dimension.", "m", PROJECT_ASSUMPTION, "Reference geometry contract", _range("number", 4.0, 200.0), 12.0, compliance_relevant=False),
        p("storey_height_m", c.BUILDING, "Clear height of the single reference storey.", "m", PROJECT_ASSUMPTION, "Reference geometry contract", _range("number", 2.0, 8.0), 3.0, compliance_relevant=False),
        p("zone_columns", c.BUILDING, "Number of deterministic east-west thermal-zone divisions.", "count", PROJECT_ASSUMPTION, "Reference geometry contract", _range("integer", 1, 10), 2, compliance_relevant=False),
        p("zone_rows", c.BUILDING, "Number of deterministic north-south thermal-zone divisions.", "count", PROJECT_ASSUMPTION, "Reference geometry contract", _range("integer", 1, 10), 2, compliance_relevant=False),
        p("north_axis_degrees", c.BUILDING, "Clockwise rotation of model north from positive Y.", "degrees", PROJECT_ASSUMPTION, "gbXML coordinate convention", _range("number", 0.0, 360.0), 0.0, compliance_relevant=False),
        p("geometry_tolerance_m", c.BUILDING, "Tolerance used for coplanarity, overlap and containment checks.", "m", PROJECT_ASSUMPTION, "Geometry QA decision RM-003", _range("number", 1.0e-9, 0.01), 1.0e-6, compliance_relevant=False),
        p("construction_u_value_tolerance_w_m2k", c.BUILDING, "QA tolerance for comparing declared and CDB-reported U-values; not a SIA acceptance tolerance.", "W/(m2 K)", PROJECT_ASSUMPTION, "Software QA decision RM-004", _range("number", 0.0, 0.1), 0.005, compliance_relevant=False),
        p("optical_property_tolerance", c.BUILDING, "QA tolerance for comparing declared and CDB-reported unitless glazing properties; not a SIA acceptance tolerance.", "fraction", PROJECT_ASSUMPTION, "Software QA decision RM-005", _range("number", 0.0, 0.05), 0.001, compliance_relevant=False),
        p("asset_provisioning_mode", c.BUILDING, "Controls whether VE assets are created from a manifest or resolved from existing project objects.", "enum", PROJECT_ASSUMPTION, "Architecture decision RM-007", _range("string", allowed_values=("existing", "create")), "existing", compliance_relevant=False),
        p("asset_manifest_file", c.BUILDING, "Absolute or active-project-relative path to the source-traced VE asset manifest used in create mode.", "path", PROJECT_ASSUMPTION, "Architecture decision RM-008", _range("path", allow_none=True), None, compliance_relevant=False),
        p("external_wall_construction_id", c.ENVELOPE, "Runtime-created CDB ID in create mode, or exact approved existing ID for external walls.", "VE CDB ID", PROJECT_CATALOG, "IESVE CDB project or provisioning receipt", _range("string", allow_none=True), None, True),
        p("roof_construction_id", c.ENVELOPE, "Runtime-created CDB ID in create mode, or exact approved existing ID for roofs.", "VE CDB ID", PROJECT_CATALOG, "IESVE CDB project or provisioning receipt", _range("string", allow_none=True), None, True),
        p("ground_floor_construction_id", c.ENVELOPE, "Runtime-created CDB ID in create mode, or exact approved existing ID for the ground floor.", "VE CDB ID", PROJECT_CATALOG, "IESVE CDB project or provisioning receipt", _range("string", allow_none=True), None, True),
        p("internal_wall_construction_id", c.ENVELOPE, "Runtime-created CDB ID in create mode, or exact approved existing ID for partitions.", "VE CDB ID", PROJECT_CATALOG, "IESVE CDB project or provisioning receipt", _range("string", allow_none=True), None, True),
        p("door_construction_id", c.ENVELOPE, "Runtime-created CDB ID in create mode, or exact approved existing ID for the door.", "VE CDB ID", PROJECT_CATALOG, "IESVE CDB project or provisioning receipt", _range("string", allow_none=True), None, True),
        p("project_external_wall_u_w_m2k", c.ENVELOPE, "Project-design external wall U-value; never inferred from a limit value.", "W/(m2 K)", PLACEHOLDER, "Project construction schedule / calculation", _range("number", 0.01, 6.0, allow_none=True)),
        p("project_roof_u_w_m2k", c.ENVELOPE, "Project-design roof U-value.", "W/(m2 K)", PLACEHOLDER, "Project construction schedule / calculation", _range("number", 0.01, 6.0, allow_none=True)),
        p("project_ground_floor_u_w_m2k", c.ENVELOPE, "Project-design ground-floor U-value including declared methodology.", "W/(m2 K)", PLACEHOLDER, "Project construction schedule / SIA 380 method", _range("number", 0.01, 6.0, allow_none=True)),
        p("linear_thermal_bridge_psi_w_mk", c.THERMAL_BRIDGES, "Project-specific linear thermal bridge coefficient or approved aggregate method.", "W/(m K)", PLACEHOLDER, "Thermal bridge calculation / SIA 380 evidence", _range("number", -0.5, 5.0, allow_none=True)),
        p("point_thermal_bridge_chi_w_k", c.THERMAL_BRIDGES, "Project-specific point thermal bridge coefficient.", "W/K", PLACEHOLDER, "Thermal bridge calculation / SIA 380 evidence", _range("number", -1.0, 20.0, allow_none=True)),
        p("glazing_construction_id", c.WINDOW, "Runtime-created CDB ID in create mode, or exact approved existing glazed-construction ID.", "VE CDB ID", PROJECT_CATALOG, "IESVE CDB project or provisioning receipt", _range("string", allow_none=True), None, True),
        p("window_width_m", c.WINDOW, "Width of each deterministic reference window.", "m", PROJECT_ASSUMPTION, "Reference geometry contract", _range("number", 0.3, 5.0), 1.5, compliance_relevant=False),
        p("window_height_m", c.WINDOW, "Height of each deterministic reference window.", "m", PROJECT_ASSUMPTION, "Reference geometry contract", _range("number", 0.3, 3.0), 1.2, compliance_relevant=False),
        p("window_sill_height_m", c.WINDOW, "Window sill height above zone floor.", "m", PROJECT_ASSUMPTION, "Reference geometry contract", _range("number", 0.0, 3.0), 0.9, compliance_relevant=False),
        p("door_width_m", c.WINDOW, "Width of the south external reference door.", "m", PROJECT_ASSUMPTION, "Reference geometry contract", _range("number", 0.6, 3.0), 1.0, compliance_relevant=False),
        p("door_height_m", c.WINDOW, "Height of the south external reference door.", "m", PROJECT_ASSUMPTION, "Reference geometry contract", _range("number", 1.5, 3.0), 2.1, compliance_relevant=False),
        p("overhang_depth_m", c.WINDOW, "Projection depth of each generated shade/overhang surface.", "m", PROJECT_ASSUMPTION, "Reference shading geometry contract", _range("number", 0.0, 5.0), 0.6, compliance_relevant=False),
        p("overhang_vertical_offset_m", c.WINDOW, "Vertical offset of overhang above window head.", "m", PROJECT_ASSUMPTION, "Reference shading geometry contract", _range("number", 0.0, 2.0), 0.15, compliance_relevant=False),
        p("project_window_u_w_m2k", c.WINDOW, "Project-design whole-window U-value including frame convention.", "W/(m2 K)", PLACEHOLDER, "Glazing supplier/CDB evidence", _range("number", 0.1, 8.0, allow_none=True)),
        p("project_glazing_g_value", c.WINDOW, "Project-design total solar energy transmittance and stated calculation basis.", "fraction", PLACEHOLDER, "Glazing supplier/CDB EN 410 evidence", _range("number", 0.0, 1.0, allow_none=True)),
        p("project_visible_light_transmittance", c.WINDOW, "Project-design visible light transmittance.", "fraction", PLACEHOLDER, "Glazing supplier/CDB evidence", _range("number", 0.0, 1.0, allow_none=True)),
        p("solar_protection_control_category", c.WINDOW, "Confirmed solar-protection type/control mapping.", "text", PLACEHOLDER, "SIA 387/4 project mapping", _range("string", allow_none=True)),
        p("weather_file", c.CLIMATE, "Absolute or VE-resolvable approved simulation weather-file path.", "path", PLACEHOLDER, "SIA 2028 / project climate decision", _range("path", allow_none=True), None, True),
        p("weather_station", c.CLIMATE, "Most representative confirmed climate station.", "text", PLACEHOLDER, "SIA 2028 / project climate decision", _range("string", allow_none=True)),
        p("weather_dataset_type", c.CLIMATE, "Declared weather dataset type and edition (for example DRY).", "text", PLACEHOLDER, "SIA 2028 dataset evidence", _range("string", allow_none=True)),
        p("climate_scenario", c.CLIMATE, "Declared present/future climate scenario and horizon where applicable.", "text", PLACEHOLDER, "Project brief / SIA guidance", _range("string", allow_none=True)),
        p("site_latitude_degrees", c.CLIMATE, "Site or weather-file latitude used for geometry metadata.", "degrees", PLACEHOLDER, "Weather-file metadata", _range("number", -90.0, 90.0, allow_none=True)),
        p("site_longitude_degrees", c.CLIMATE, "Site or weather-file longitude used for geometry metadata.", "degrees", PLACEHOLDER, "Weather-file metadata", _range("number", -180.0, 180.0, allow_none=True)),
        p("infiltration_m3_h_m2", c.VENTILATION, "Project infiltration assumption and reference area basis.", "m3/(h m2)", PLACEHOLDER, "Project airtightness evidence / applicable SIA method", _range("number", 0.0, 20.0, allow_none=True)),
        p("outdoor_air_l_s_person", c.VENTILATION, "Occupied outdoor-air flow assumption.", "L/(s person)", PLACEHOLDER, "SIA 2024/project ventilation design", _range("number", 0.0, 100.0, allow_none=True)),
        p("heat_recovery_temperature_efficiency", c.VENTILATION, "Declared heat-recovery temperature efficiency.", "fraction", PLACEHOLDER, "Approved AHU design data", _range("number", 0.0, 1.0, allow_none=True)),
        p("sia2024_use_category", c.OCCUPANCY, "Confirmed SIA 2024 room-use category.", "SIA 2024 category", PLACEHOLDER, "SIA 2024:2021 / project use mapping", _range("string", allow_none=True)),
        p("occupancy_density_m2_person", c.OCCUPANCY, "Confirmed occupied floor area per person.", "m2/person", PLACEHOLDER, "SIA 2024/project usage evidence", _range("number", 0.1, 1000.0, allow_none=True)),
        p("occupancy_profile_id", c.OCCUPANCY, "Exact VE profile ID implementing confirmed occupancy schedule.", "VE profile ID", PLACEHOLDER, "Approved thermal-template evidence", _range("string", allow_none=True)),
        p("people_gain_w_person", c.INTERNAL_GAINS, "Sensible/latent people-gain basis; fractions documented separately.", "W/person", PLACEHOLDER, "SIA 180/SIA 2024/project evidence", _range("number", 0.0, 1000.0, allow_none=True)),
        p("lighting_gain_w_m2", c.INTERNAL_GAINS, "Installed lighting power density and control basis.", "W/m2", PLACEHOLDER, "SIA 387/4/project lighting design", _range("number", 0.0, 100.0, allow_none=True)),
        p("equipment_gain_w_m2", c.INTERNAL_GAINS, "Equipment/process gain density and diversity basis.", "W/m2", PLACEHOLDER, "SIA 2024/project use evidence", _range("number", 0.0, 1000.0, allow_none=True)),
        p("thermal_template_name", c.TEMPLATE, "Runtime-created template name in create mode, or exact existing name in existing mode.", "VE template name", PLACEHOLDER, "Approved asset manifest or project template package", _range("string", allow_none=True), None, True),
        p("thermal_template_source_record", c.TEMPLATE, "Manifest checksum in create mode, or document/checksum identifying existing approved content.", "text", PLACEHOLDER, "Asset manifest or project evidence register", _range("string", allow_none=True), None, True),
        p("hvac_system_id", c.HVAC, "Optional exact Apache System or ApacheHVAC system ID.", "VE system ID", PLACEHOLDER, "Approved HVAC design", _range("string", allow_none=True)),
        p("hvac_methodology", c.HVAC, "VE room HVAC methodology when a system is assigned.", "enum", IESVE_API, "VE 2023 VEScript User Guide, VEBody", _range("string", allowed_values=("apache_system", "apache_hvac")), "apache_system"),
        p("sia3802_reference_external_wall_u_w_m2k", c.REGULATORY, "SIA 380/2 reference-project external wall value; comparison only.", "W/(m2 K)", SIA3802_TABLE3, "SIA 380/2:2022 FR, PDF pp. 36-37", _range("number", 0.01, 6.0), 0.20, comparison_only=True),
        p("sia3802_reference_roof_u_w_m2k", c.REGULATORY, "SIA 380/2 reference-project flat roof value; comparison only.", "W/(m2 K)", SIA3802_TABLE3, "SIA 380/2:2022 FR, PDF pp. 36-37", _range("number", 0.01, 6.0), 0.20, comparison_only=True),
        p("sia3802_reference_ground_floor_u_w_m2k", c.REGULATORY, "SIA 380/2 reference-project ground-floor value; comparison only.", "W/(m2 K)", SIA3802_TABLE3, "SIA 380/2:2022 FR, PDF pp. 36-37", _range("number", 0.01, 6.0), 0.30, comparison_only=True),
        p("sia3802_reference_window_u_w_m2k", c.REGULATORY, "SIA 380/2 reference-project window U-value (glass and frame); Table 2 limit-case value, target value 0.88; comparison only.", "W/(m2 K)", SIA3802_TABLE2, "SIA 380/2:2022 FR, Table 2, PDF p. 32", _range("number", 0.01, 8.0), 1.10, comparison_only=True),
        p("sia3802_reference_glazing_g_value", c.REGULATORY, "SIA 380/2 reference-project glazing g-value (g-perp); comparison only.", "fraction", SIA3802_TABLE2, "SIA 380/2:2022 FR, Table 2, PDF p. 32", _range("number", 0.0, 1.0), 0.50, comparison_only=True),
        p("sia3802_reference_light_transmittance", c.REGULATORY, "SIA 380/2 reference-project glazing light-transmittance factor; comparison only.", "fraction", SIA3802_TABLE2, "SIA 380/2:2022 FR, Table 2, PDF p. 32", _range("number", 0.0, 1.0), 0.70, comparison_only=True),
        p("sia4010_official_bundle_path", c.REGULATORY, "Future drop-zone path for official test specifications, models and evaluation workbooks.", "path", PLACEHOLDER, "SIA 4010:2023 FR, sections 4.3-4.6", _range("path", allow_none=True)),
        p("sia4010_target_validation_class", c.REGULATORY, "Requested SIA 4010 validation class; no class is assumed.", "enum", PLACEHOLDER, "SIA 4010:2023 FR, Table 63", _range("string", allowed_values=("1A", "1B", "2A", "2B", "3", "4A", "4B", "5"), allow_none=True)),
    ]
    return ParameterRegistry(parameters)
