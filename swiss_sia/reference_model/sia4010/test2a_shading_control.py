"""Source-traced Test 2A fabric-awning control contract.

The supplied Test 2 specification confirms an external fabric-awning
irradiance-threshold control and a threshold value of 150 W/m2.  It does not
state the comparison operator, the release rule, the exact signal definition
or the timestep/state semantics.  IESVE exposes separate ``lower`` and
``raise`` thresholds.  Those API fields are useful setter targets, but their
dynamic equivalence cannot be inferred from the field names.

This module therefore separates:

* the confirmed normative rule;
* the narrow CDB setter values that can be tested without interpretation; and
* the dynamic/optical equivalence evidence still required before a complete
  Test 2A model may be claimed.

No VE object is created here.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping, Optional, Tuple

from ..exceptions import ConfigurationError


CONTROL_SCHEMA_VERSION = "1.1"
CONTROL_TYPE = "irradiance_threshold"

SETTER_FIELDS = (
    "external_shade_active",
    "external_shade_radiation_to_lower",
    "external_shade_radiation_to_raise",
)
FIXED_CLOSED_SETTER_FIELDS = (
    "external_shade_active",
    "external_shade_profile",
    "external_shade_transmittance_0",
    "external_shade_solar_reflectance",
    "external_shade_visible_reflectance",
)
FIXED_CLOSED_OUTPUT_BLOCKERS = (
    "VE_TEST2A_2E1_ANGULAR_SOLAR_TRANSMITTANCE_NOT_MAPPED",
    "VE_TEST2A_2E1_INSIDE_SOLAR_REFLECTANCE_NOT_MAPPED",
    "VE_TEST2A_2E1_VISIBLE_TRANSMITTANCE_NOT_MAPPED",
    "VE_TEST2A_2E1_SECONDARY_HEAT_TRANSFER_NOT_MAPPED",
    "VE_TEST2A_2E1_APS_OUTPUT_EQUIVALENCE_NOT_QUALIFIED",
)

DYNAMIC_EQUIVALENCE_BLOCKERS = (
    "SIA4010_TEST2A_EXACT_IRRADIANCE_SIGNAL_NOT_CONFIRMED",
    "SIA4010_TEST2A_THRESHOLD_COMPARISON_OPERATOR_NOT_CONFIRMED",
    "SIA4010_TEST2A_RELEASE_RULE_NOT_CONFIRMED",
    "VE_EXTERNAL_SHADE_TIMESTEP_STATE_HANDLING_NOT_QUALIFIED",
    "VE_TEST2A_COMBINED_G_TOTAL_OPTICAL_MAPPING_NOT_QUALIFIED",
)

_REQUIRED_OFFICIAL_KEYS = (
    "external_shading_activation_w_m2",
    "variant_2A_shade",
    "variant_2A_combined_g_total",
    "variant_2A_direct_solar_transmittance",
    "variant_2A_outside_solar_reflectance",
    "variant_2A_inside_solar_reflectance",
    "variant_2A_visible_transmittance",
    "variant_2A_outside_visible_reflectance",
    "variant_2A_inside_visible_reflectance",
    "variant_2A_convection_factor",
    "variant_2A_thermal_radiation_factor",
    "variant_2A_ventilation_factor",
    "variant_2A_secondary_internal_heat_transfer_factor",
    "variant_2A_uv_transmittance",
    "variant_2A_reference_combined_g_total",
    "variant_2A_reference_u_w_m2k",
    "variant_2A_iso15099_winter_u_w_m2k",
    "variant_2A_peripheral_gap_m",
    "variant_2A_screen_layer_thickness_m",
)

_FRACTION_KEYS = (
    "variant_2A_combined_g_total",
    "variant_2A_direct_solar_transmittance",
    "variant_2A_outside_solar_reflectance",
    "variant_2A_inside_solar_reflectance",
    "variant_2A_visible_transmittance",
    "variant_2A_outside_visible_reflectance",
    "variant_2A_inside_visible_reflectance",
    "variant_2A_convection_factor",
    "variant_2A_thermal_radiation_factor",
    "variant_2A_ventilation_factor",
    "variant_2A_secondary_internal_heat_transfer_factor",
    "variant_2A_uv_transmittance",
    "variant_2A_reference_combined_g_total",
)


def _required_number(
    values: Mapping[str, Any],
    key: str,
    *,
    minimum: float,
    maximum: float,
) -> float:
    """Return one finite source value inside its physical validation range."""

    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigurationError(
            "Official Test 2 shading input {!r} must be numeric".format(key)
        )
    result = float(value)
    if not minimum <= result <= maximum:
        raise ConfigurationError(
            "Official Test 2 shading input {!r}={} is outside [{}, {}]".format(
                key, result, minimum, maximum
            )
        )
    return result


@dataclass(frozen=True)
class Test2AFabricAwningControl:
    """Immutable normative rule plus a deliberately narrow VE setter plan."""

    control_type: str
    signal: Optional[str]
    active_operator: Optional[str]
    inactive_operator: Optional[str]
    threshold_w_m2: float
    device: str
    combined_g_total: float
    direct_solar_transmittance: float
    outside_solar_reflectance: float
    inside_solar_reflectance: float
    visible_transmittance: float
    outside_visible_reflectance: float
    inside_visible_reflectance: float
    convection_factor: float
    thermal_radiation_factor: float
    ventilation_factor: float
    secondary_internal_heat_transfer_factor: float
    uv_transmittance: float
    reference_combined_g_total: float
    reference_u_w_m2k: float
    iso15099_winter_u_w_m2k: float
    peripheral_gap_m: float
    screen_layer_thickness_m: float
    source: str
    source_locator: str
    optical_source: str
    optical_source_locator: str
    dynamic_equivalence_blockers: Tuple[str, ...]

    @property
    def setter_plan(self) -> Dict[str, Any]:
        """Return only fields whose storage/read-back can be qualified safely.

        Setting both VE fields to the one confirmed source value is a technical
        storage probe, not a normative mapping decision. The returned plan is
        consequently suitable only for the dedicated disposable-project setter
        qualification.
        """

        return {
            "external_shade_active": True,
            "external_shade_radiation_to_lower": self.threshold_w_m2,
            "external_shade_radiation_to_raise": self.threshold_w_m2,
        }

    @property
    def fixed_closed_candidate_setter_plan(self) -> Dict[str, Any]:
        """Return the narrow, source-matched storage probe for diagnostic 2E1.

        The plan maps only properties with a direct semantic name match in the
        runtime CDB: active state, always-on profile, normal-incidence solar
        transmittance and outside solar/visible reflectances. It deliberately
        omits angular values and properties for which VE exposes no confirmed
        equivalent field.
        """

        return {
            "external_shade_active": True,
            "external_shade_profile": "ON",
            "external_shade_transmittance_0": (
                self.direct_solar_transmittance
            ),
            "external_shade_solar_reflectance": (
                self.outside_solar_reflectance
            ),
            "external_shade_visible_reflectance": (
                self.outside_visible_reflectance
            ),
        }

    @property
    def dynamic_equivalence_qualified(self) -> bool:
        """Return False until separate runtime and output evidence is attached."""

        return not self.dynamic_equivalence_blockers

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe, explicit claim contract."""

        payload = asdict(self)
        payload["schema_version"] = CONTROL_SCHEMA_VERSION
        payload["confirmed_normative_control"] = {
            "control_type": self.control_type,
            "threshold_w_m2": self.threshold_w_m2,
            "source_wording": (
                "Einstrahlungs-Schwellenwertregelung; Extern Aktivierung: "
                "Schwellenwert 150 W/m2"
            ),
        }
        payload["unresolved_normative_semantics"] = {
            "exact_irradiance_signal": self.signal,
            "activation_comparison_operator": self.active_operator,
            "release_rule": self.inactive_operator,
            "timestep_state_handling": None,
        }
        payload["ve_cdb_setter_plan"] = self.setter_plan
        payload["setter_plan_scope"] = "CDB_STORAGE_AND_READBACK_ONLY"
        payload["fixed_closed_candidate_setter_plan"] = (
            self.fixed_closed_candidate_setter_plan
        )
        payload["fixed_closed_setter_plan_scope"] = (
            "DIRECT_NAME_MATCH_STORAGE_AND_READBACK_ONLY"
        )
        payload["fixed_closed_output_blockers"] = list(
            FIXED_CLOSED_OUTPUT_BLOCKERS
        )
        payload["dynamic_equivalence_qualified"] = (
            self.dynamic_equivalence_qualified
        )
        payload["dynamic_equivalence_blockers"] = list(
            self.dynamic_equivalence_blockers
        )
        payload["claim_guardrail"] = (
            "The VE threshold fields are candidate storage bindings. The "
            "supplied Test 2 specification does not confirm the comparison "
            "operator or release rule. A setter PASS does not prove dynamic "
            "semantics, combined-g optical equivalence, simulation results or "
            "SIA validation."
        )
        return payload


@dataclass(frozen=True)
class Test2AOpticalDiagnosticContract:
    """Fail-closed fixed-state qualification target for official case 2E1."""

    diagnostic_case_id: str
    protection_state: str
    result_series: Tuple[str, ...]
    control: Test2AFabricAwningControl
    workbook_binding_status: str
    ve_optical_mapping_status: str
    blockers: Tuple[str, ...]
    official_workbook_binding: Optional[Mapping[str, Any]] = None

    @property
    def qualification_ready(self) -> bool:
        """Return whether both official result and VE mapping gates are closed."""

        return not self.blockers

    def to_dict(self) -> Dict[str, Any]:
        """Return the exact fixed-state output-equivalence contract."""

        return {
            "schema_version": "1.0",
            "diagnostic_case_id": self.diagnostic_case_id,
            "protection_state": self.protection_state,
            "source": (
                "SIA 4010 Test 2 specification page 2: Diag 2E1, "
                "solar protection always closed, fabric awning as Test 2A"
            ),
            "result_series": list(self.result_series),
            "summer_optical_identities": {
                "g_total": self.control.combined_g_total,
                "direct_solar_transmittance": (
                    self.control.direct_solar_transmittance
                ),
                "secondary_internal_heat_transfer": (
                    self.control.secondary_internal_heat_transfer_factor
                ),
                "identity_g_total": (
                    "direct_solar_transmittance + "
                    "secondary_internal_heat_transfer"
                ),
                "convection_factor": self.control.convection_factor,
                "thermal_radiation_factor": (
                    self.control.thermal_radiation_factor
                ),
                "ventilation_factor": self.control.ventilation_factor,
                "identity_secondary": (
                    "convection_factor + thermal_radiation_factor + "
                    "ventilation_factor"
                ),
            },
            "workbook_binding_status": self.workbook_binding_status,
            "official_workbook_binding": (
                dict(self.official_workbook_binding)
                if self.official_workbook_binding is not None
                else None
            ),
            "technical_reference_comparison": {
                "available": self.official_workbook_binding is not None,
                "status": (
                    "AVAILABLE_NO_ACCEPTANCE_CRITERION"
                    if self.official_workbook_binding is not None
                    else "BLOCKED_BY_WORKBOOK_BINDING"
                ),
                "implementation": (
                    "sia4010.test2a_diagnostic_evaluation."
                    "evaluate_test2a_2e1_diagnostic"
                ),
                "acceptance_criterion_available": False,
                "compliance_pass_allowed": False,
            },
            "ve_optical_mapping_status": self.ve_optical_mapping_status,
            "blockers": list(self.blockers),
            "qualification_ready": self.qualification_ready,
            "dynamic_control_qualified": False,
            "candidate_transmission_factor": None,
            "claim_guardrail": (
                "No ratio such as g_total/base_g is accepted as a VE shade "
                "transmission factor without fixed-state 2E1 output evidence. "
                "The diagnostic does not qualify dynamic control."
            ),
        }


def build_test2a_optical_diagnostic_contract(
    control: Test2AFabricAwningControl,
    official_workbook_binding: Optional[Mapping[str, Any]] = None,
) -> Test2AOpticalDiagnosticContract:
    """Build the official 2E1 gate without inventing a VE optical mapping."""

    workbook_bound = official_workbook_binding is not None
    blockers = ["VE_TEST2A_FIXED_CLOSED_OPTICAL_MAPPING_NOT_QUALIFIED"]
    if not workbook_bound:
        blockers.insert(
            0,
            "OFFICIAL_TEST2_DIAGNOSTIC_2E1_SERIES_NOT_BOUND",
        )
    return Test2AOpticalDiagnosticContract(
        diagnostic_case_id="2E1",
        protection_state="ALWAYS_CLOSED",
        result_series=(
            "hourly_incident_solar_irradiance_total_on_window_plane",
            "hourly_incident_solar_irradiance_direct_on_window_plane",
            "hourly_incident_solar_irradiance_diffuse_on_window_plane",
            "hourly_room_solar_heat_gain_total",
            "hourly_room_solar_heat_gain_direct",
            "hourly_room_solar_heat_gain_diffuse",
            "hourly_room_solar_heat_gain_secondary",
            "hourly_transmitted_solar_radiation_excluding_secondary",
        ),
        control=control,
        workbook_binding_status=(
            "OFFICIAL_2E1_SCHEMA_BOUND"
            if workbook_bound
            else "OFFICIAL_2E1_SERIES_BINDING_REQUIRED"
        ),
        ve_optical_mapping_status="VE_FIXED_CLOSED_OPTICAL_MAPPING_REQUIRED",
        blockers=tuple(blockers),
        official_workbook_binding=official_workbook_binding,
    )


def build_test2a_fabric_awning_control(
    official_inputs: Mapping[str, Any],
) -> Test2AFabricAwningControl:
    """Build the exact source-traced fabric-awning rule or fail closed."""

    missing = [
        key
        for key in _REQUIRED_OFFICIAL_KEYS
        if key not in official_inputs or official_inputs[key] is None
    ]
    if missing:
        raise ConfigurationError(
            "Official Test 2 contract is missing fabric-awning inputs: {}".format(
                missing
            )
        )

    device = official_inputs["variant_2A_shade"]
    if not isinstance(device, str) or not device.strip():
        raise ConfigurationError(
            "Official Test 2 fabric-awning device must be non-empty text"
        )

    fractions = {
        key: _required_number(
            official_inputs,
            key,
            minimum=0.0,
            maximum=1.0,
        )
        for key in _FRACTION_KEYS
    }
    threshold = _required_number(
        official_inputs,
        "external_shading_activation_w_m2",
        minimum=0.0,
        maximum=1200.0,
    )
    if threshold <= 0.0:
        raise ConfigurationError(
            "Test 2A activation threshold must be greater than zero"
        )
    reference_u = _required_number(
        official_inputs,
        "variant_2A_reference_u_w_m2k",
        minimum=0.01,
        maximum=20.0,
    )
    winter_u = _required_number(
        official_inputs,
        "variant_2A_iso15099_winter_u_w_m2k",
        minimum=0.01,
        maximum=20.0,
    )
    peripheral_gap = _required_number(
        official_inputs,
        "variant_2A_peripheral_gap_m",
        minimum=0.0,
        maximum=1.0,
    )
    screen_thickness = _required_number(
        official_inputs,
        "variant_2A_screen_layer_thickness_m",
        minimum=0.000001,
        maximum=0.1,
    )
    direct_plus_secondary = (
        fractions["variant_2A_direct_solar_transmittance"]
        + fractions["variant_2A_secondary_internal_heat_transfer_factor"]
    )
    if not abs(
        direct_plus_secondary - fractions["variant_2A_combined_g_total"]
    ) <= 1.0e-12:
        raise ConfigurationError(
            "Test 2A summer optical identity failed: direct transmittance + "
            "secondary internal heat transfer must equal g_total"
        )
    secondary_components = (
        fractions["variant_2A_convection_factor"]
        + fractions["variant_2A_thermal_radiation_factor"]
        + fractions["variant_2A_ventilation_factor"]
    )
    if not abs(
        secondary_components
        - fractions["variant_2A_secondary_internal_heat_transfer_factor"]
    ) <= 1.0e-12:
        raise ConfigurationError(
            "Test 2A secondary-gain identity failed: convection + thermal "
            "radiation + ventilation must equal qi"
        )

    return Test2AFabricAwningControl(
        control_type=CONTROL_TYPE,
        signal=None,
        active_operator=None,
        inactive_operator=None,
        threshold_w_m2=threshold,
        device=device.strip(),
        combined_g_total=fractions["variant_2A_combined_g_total"],
        direct_solar_transmittance=fractions[
            "variant_2A_direct_solar_transmittance"
        ],
        outside_solar_reflectance=fractions[
            "variant_2A_outside_solar_reflectance"
        ],
        inside_solar_reflectance=fractions[
            "variant_2A_inside_solar_reflectance"
        ],
        visible_transmittance=fractions[
            "variant_2A_visible_transmittance"
        ],
        outside_visible_reflectance=fractions[
            "variant_2A_outside_visible_reflectance"
        ],
        inside_visible_reflectance=fractions[
            "variant_2A_inside_visible_reflectance"
        ],
        convection_factor=fractions["variant_2A_convection_factor"],
        thermal_radiation_factor=fractions[
            "variant_2A_thermal_radiation_factor"
        ],
        ventilation_factor=fractions["variant_2A_ventilation_factor"],
        secondary_internal_heat_transfer_factor=fractions[
            "variant_2A_secondary_internal_heat_transfer_factor"
        ],
        uv_transmittance=fractions["variant_2A_uv_transmittance"],
        reference_combined_g_total=fractions[
            "variant_2A_reference_combined_g_total"
        ],
        reference_u_w_m2k=reference_u,
        iso15099_winter_u_w_m2k=winter_u,
        peripheral_gap_m=peripheral_gap,
        screen_layer_thickness_m=screen_thickness,
        source="SIA 4010:2023 Test 2 specification",
        source_locator=(
            "SIA_4010_geteilter_Link/Test2/Spezifikation_Test2.pdf, "
            "page 1 description and page 2 solar-protection table"
        ),
        optical_source=(
            "SIA 4010 example-building documentation, Soltis "
            "92-2048-Alu detailed glazing and shading properties"
        ),
        optical_source_locator=(
            "SIA_4010_geteilter_Link/Beispielgebäude/"
            "Dokumentation_Beispielgebäude_V5.pdf, pages 8-9, "
            "Figure 14 and Table 3"
        ),
        dynamic_equivalence_blockers=DYNAMIC_EQUIVALENCE_BLOCKERS,
    )
