"""Build the source-tiered MVP files for SIA 4010 Test 1, Case 600.

The generated project files are intentionally explicit about evidence quality.
Public BESTEST inputs may drive an MVP simulation, but they never authorize a
normative compliance claim. A project-local case manifest records the exact
weather file selected for the disposable VE project.
"""

import copy
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Tuple, Union

from ..asset_manifest import load_asset_manifest
from ..config_loader import load_configuration
from ..exceptions import ConfigurationError
from .case_manifest import Sia4010CaseManifest


SUPPORTED_WEATHER_SUFFIXES = {".epw", ".fwt", ".tmy"}
PUBLIC_BESTEST_SOURCE = (
    "NREL/TP-472-6231, International Energy Agency Building Energy "
    "Simulation Test (BESTEST) and Diagnostic Method, 1995"
)
PUBLIC_BESTEST_URL = "https://doi.org/10.2172/90674"
ISO_52016_SOURCE = "BS EN ISO 52016-1:2017 licensed project evidence"
ISO_52016_OPAQUE_LOCATOR = (
    "Figure 2 and Tables 22-25, licensed evidence pages 123-127"
)
ISO_52016_GLAZING_LOCATOR = "Clause 7.2.2.6, licensed evidence page 126"
WEATHER_VERIFICATION_FILENAME = "DRYCOLD_TMY_ISO_SOURCE_VERIFICATION.json"
EPW_WEATHER_VERIFICATION_FILENAME = "DRYCOLD_IESVE_EPW_DERIVATION.json"


def _load_json(path: Path) -> Dict[str, Any]:
    """Read one JSON object, translating read/parse errors into a config error."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConfigurationError("Unable to read {}: {}".format(path, exc)) from exc
    if not isinstance(payload, dict):
        raise ConfigurationError("{} must contain a JSON object".format(path))
    return payload


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write one JSON payload atomically through a temporary file."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _checksum(path: Path) -> str:
    """Return the hexadecimal SHA-256 checksum of one file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _load_weather_verification(
    weather_file: Optional[Path],
) -> Optional[Dict[str, Any]]:
    """Return a checksum-bound source-identity report when one is adjacent."""

    if not weather_file:
        return None
    report_filename = (
        EPW_WEATHER_VERIFICATION_FILENAME
        if weather_file.suffix.casefold() == ".epw"
        else WEATHER_VERIFICATION_FILENAME
    )
    report_path = weather_file.parent / report_filename
    if not report_path.is_file():
        return None
    report = _load_json(report_path)
    expected_checksum = str(
        report.get("weather", {}).get("sha256", "")
    ).upper()
    actual_checksum = _checksum(weather_file)
    if (
        report.get("status") != "PASS"
        or report.get("source_identity_supported") is not True
        or expected_checksum != actual_checksum
    ):
        raise ConfigurationError(
            "Weather verification report is not valid for '{}': {}".format(
                weather_file, report_path
            )
        )
    return {
        "path": str(report_path.resolve()),
        "sha256": _checksum(report_path),
        "weather_sha256": actual_checksum,
        "status": "PASS",
        "scope": "SOURCE_IDENTITY_ONLY",
        "compliance_claim_allowed": False,
    }


def discover_weather_file(project_root: Union[str, Path]) -> Optional[Path]:
    """Return one unambiguous VE-readable weather file in the project root."""

    root = Path(project_root)
    candidates = sorted(
        path
        for path in root.iterdir()
        if path.is_file() and path.suffix.casefold() in SUPPORTED_WEATHER_SUFFIXES
    )
    if len(candidates) > 1:
        raise ConfigurationError(
            "Several weather files are present; retain exactly one for Case 600: "
            + ", ".join(path.name for path in candidates)
        )
    return candidates[0] if candidates else None


def _field(
    value: Any,
    description: str,
    units: str,
    source_locator: str,
    expected_type: str,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
) -> Dict[str, Any]:
    """Return one source-traced manifest field with its validation contract."""

    validation: Dict[str, Any] = {
        "expected_type": expected_type,
        "allow_none": False,
    }
    if minimum is not None:
        validation["minimum"] = minimum
    if maximum is not None:
        validation["maximum"] = maximum
    return {
        "value": value,
        "description": description,
        "units": units,
        "source": PUBLIC_BESTEST_SOURCE,
        "source_locator": source_locator,
        "validation_range": validation,
        "required": True,
    }


def _set_material(
    material: Dict[str, Any],
    *,
    identity: str,
    description: str,
    conductivity: float,
    density: float,
    specific_heat: float,
    locator: str,
) -> None:
    """Populate one asset-manifest material with source-located properties."""

    material.update(
        {
            "description": description,
            "source": PUBLIC_BESTEST_SOURCE,
            "source_locator": locator,
        }
    )
    material["properties"] = {
        "description": _field(
            identity,
            "Stable VE CDB material identity.",
            "text",
            locator,
            "string",
        ),
        "conductivity": _field(
            conductivity,
            "Thermal conductivity.",
            "W/(m K)",
            locator,
            "number",
            0.001,
            500.0,
        ),
        "density": _field(
            density,
            "Dry density.",
            "kg/m3",
            locator,
            "number",
            0.000001,
            30000.0,
        ),
        "specific_heat_capacity": _field(
            specific_heat,
            "Specific heat capacity.",
            "J/(kg K)",
            locator,
            "number",
            0.000001,
            10000.0,
        ),
    }


def _layer(material_key: str, thickness: float, locator: str) -> Dict[str, Any]:
    """Return one source-located construction layer definition."""

    return {
        "material_key": material_key,
        "is_cavity": False,
        "properties": {
            "thickness": _field(
                thickness,
                "BESTEST construction-layer thickness.",
                "m",
                locator,
                "number",
                0.0001,
                5.0,
            )
        },
    }


def _set_parameter(
    config: Dict[str, Any],
    name: str,
    value: Any,
    source: str,
    source_locator: str,
) -> None:
    """Set one case-manifest parameter value together with its source."""

    parameter = config["parameters"][name]
    parameter["value"] = value
    parameter["source"] = source
    parameter["source_locator"] = source_locator


def _by_key(items: Iterable[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """Index manifest items by their ``key`` field."""

    return {str(item["key"]): item for item in items}


def _preserve_runtime_glazing_calibration(
    generated: Dict[str, Any],
    previous: Optional[Mapping[str, Any]],
    target_u_w_m2k: float,
) -> bool:
    """Carry forward a verified VE calibration across deterministic rebuilds.

    The Case 600 bundle starts from the published air-gap conductance. VE's
    native ISO U-factor algorithm can require a slightly different equivalent
    cavity resistance to reproduce the published whole-window U-value. A
    calibration is preserved only when its metadata, target, verified result,
    and traced cavity value agree. Invalid or unrelated prior data are ignored.
    """

    if not isinstance(previous, Mapping):
        return False
    metadata = previous.get("metadata")
    if not isinstance(metadata, Mapping):
        return False
    calibration = metadata.get("external_glazing_runtime_calibration")
    if not isinstance(calibration, Mapping):
        return False
    try:
        recorded_target = float(calibration["target_u_w_m2k"])
        verified_u = float(calibration["verified_u_w_m2k"])
        calibrated_resistance = float(
            calibration["cavity_resistance_m2k_w"]
        )
    except (KeyError, TypeError, ValueError):
        return False
    if (
        abs(recorded_target - float(target_u_w_m2k)) > 1.0e-9
        or abs(verified_u - float(target_u_w_m2k)) > 0.005
        or calibrated_resistance <= 0.0
    ):
        return False
    try:
        previous_glazing = _by_key(previous["constructions"])[
            "external_glazing"
        ]
        previous_cavity = next(
            layer
            for layer in previous_glazing["layers"]
            if layer.get("is_cavity") is True
        )
        resistance_field = previous_cavity["properties"]["resistance"]
        traced_resistance = float(resistance_field["value"])
        generated_glazing = _by_key(generated["constructions"])[
            "external_glazing"
        ]
        generated_cavity = next(
            layer
            for layer in generated_glazing["layers"]
            if layer.get("is_cavity") is True
        )
    except (KeyError, StopIteration, TypeError, ValueError):
        return False
    if abs(traced_resistance - calibrated_resistance) > 1.0e-9:
        return False
    generated_cavity["properties"]["resistance"] = copy.deepcopy(
        resistance_field
    )
    generated["metadata"]["external_glazing_runtime_calibration"] = (
        copy.deepcopy(dict(calibration))
    )
    generated["metadata"]["external_glazing_runtime_calibration"][
        "preserved_by_bundle_rebuild"
    ] = True
    return True


def _build_assets(
    base: Mapping[str, Any], envelope: Mapping[str, Any], glazing: Mapping[str, Any]
) -> Dict[str, Any]:
    """Return the asset manifest with the MVP envelope and glazing applied."""

    assets = copy.deepcopy(dict(base))
    assets["on_existing"] = "reuse_verified"
    assets["metadata"] = {
        "purpose": "MVP VE asset package for SIA 4010 Test 1 Case 600.",
        "compliance_scope": "SIA4010_OFFICIAL",
        "sia4010_variant": "test_1",
        "sia4010_case_id": "600",
        "evidence_tier": "NORMATIVE_ISO_WITH_PUBLIC_REFERENCE_REMAINDERS",
        "compliance_claim_allowed": False,
        "guardrail": (
            "ISO 52016-1:2017 geometry, opaque fabric, glazing targets and "
            "boundary coefficients are source-confirmed. Runtime VE read-back "
            "and the remaining source items still gate any compliance claim."
        ),
        "auxiliary_asset_policy": (
            "The generic provisioning contract still requires internal-wall "
            "and door roles. They are created as unused auxiliary assets and "
            "are not present in the Case 600 geometry."
        ),
        "public_source": PUBLIC_BESTEST_SOURCE,
        "public_source_url": PUBLIC_BESTEST_URL,
        "profile_persistence_policy": (
            "Case 600 schedules are constant. They are represented by VE's "
            "persistent built-in ON profile so the saved model does not "
            "depend on session-local DAY_* identifiers. Zero-valued loads "
            "remain exactly zero because their magnitudes are zero."
        ),
    }

    # VE stores custom daily profiles as non-portable DAY_#### references.
    # Case 600 only needs constant schedules, so native ON is exact: zero
    # gains/flows stay zero through their magnitude and non-zero values remain
    # constant. No project profile therefore needs to be created or persisted.
    assets["profiles"] = []

    materials = _by_key(assets["materials"])
    material_specs = {
        "external_plaster": (
            "SIA600_WOOD_SIDING",
            "ISO 52016-1 lightweight wood siding / roof deck.",
            0.14,
            530.0,
            900.0,
        ),
        "eps_wall": (
            "SIA600_FIBERGLASS_QUILT",
            "ISO 52016-1 lightweight fiberglass quilt.",
            0.04,
            12.0,
            840.0,
        ),
        "internal_plaster": (
            "SIA600_PLASTERBOARD",
            "ISO 52016-1 lightweight plasterboard.",
            0.16,
            950.0,
            840.0,
        ),
        "xps_ground": (
            "SIA600_FLOOR_INSULATION",
            "ISO 52016-1 ideal raised-floor insulation.",
            0.04,
            0.0,
            0.0,
        ),
        "linoleum": (
            "SIA600_TIMBER_FLOORING",
            "ISO 52016-1 timber flooring.",
            0.14,
            650.0,
            1200.0,
        ),
    }
    for key, spec in material_specs.items():
        _set_material(
            materials[key],
            identity=spec[0],
            description=spec[1],
            conductivity=spec[2],
            density=spec[3],
            specific_heat=spec[4],
            locator=ISO_52016_OPAQUE_LOCATOR,
        )
    # ISO Table 23 explicitly specifies zero thermal mass for the artificial
    # floor-insulation layer. The generic material helper normally rejects
    # zero values, so this one controlled ideal layer widens only those two
    # lower bounds. VE must still set and read back the values or report the
    # minimum non-negative substitute it requires.
    for field_name in ("density", "specific_heat_capacity"):
        materials["xps_ground"]["properties"][field_name]["validation_range"]["minimum"] = 0.0

    glass = materials["equivalent_glazing_layer"]
    _set_material(
        glass,
        identity="SIA600_CLEAR_GLASS",
        description="BESTEST Case 600 clear glazing layer.",
        conductivity=float(glazing["glass_conductivity_w_mk"]),
        density=float(glazing["glass_density_kg_m3"]),
        specific_heat=float(glazing["glass_specific_heat_j_kgk"]),
        locator="NREL/TP-472-6231 Part I, Tables 1-7 and 1-8",
    )
    # VE 2025 exposes a reduced property schema for ``glass`` CDB materials.
    # Density and specific heat remain source-traced in the case manifest but
    # cannot be set/read back on VECdbMaterial and must not be treated as a
    # failed persistence check.
    glass["properties"].pop("density", None)
    glass["properties"].pop("specific_heat_capacity", None)
    glass["properties"]["transmittance"] = _field(
        float(glazing["normal_single_pane_solar_transmittance"]),
        "Normal direct-beam transmittance through one pane in air.",
        "fraction",
        "NREL/TP-472-6231 Part I, Tables 1-7 and 1-8",
        "number",
        0.0,
        1.0,
    )
    glass["properties"]["visible_transmittance"] = _field(
        float(glazing["normal_single_pane_solar_transmittance"]),
        (
            "MVP proxy equal to the published single-pane solar transmittance; "
            "daylighting is not evaluated in Case 600."
        ),
        "fraction",
        "IMPLEMENTATION_PROXY - replace if ISO optical data are obtained",
        "number",
        0.0,
        1.0,
    )

    constructions = _by_key(assets["constructions"])
    construction_layers = {
        "external_wall": [
            ("external_plaster", 0.009),
            ("eps_wall", 0.066),
            ("internal_plaster", 0.012),
        ],
        "roof": [
            ("external_plaster", 0.019),
            ("eps_wall", 0.1118),
            ("internal_plaster", 0.01),
        ],
        "ground_floor": [
            ("xps_ground", 1.003),
            ("linoleum", 0.025),
        ],
    }
    for key, layers in construction_layers.items():
        construction = constructions[key]
        construction["description"] = (
            "ISO 52016-1 Case 600 {} construction.".format(
                key.replace("_", " ")
            )
        )
        construction["source"] = ISO_52016_SOURCE
        construction["source_locator"] = ISO_52016_OPAQUE_LOCATOR
        construction["layers"] = [
            _layer(material_key, thickness, construction["source_locator"])
            for material_key, thickness in layers
        ]

    coefficients = envelope["surface_coefficients_w_m2k"]
    inside_coefficients = {
        "external_wall": float(coefficients["wall_inside_horizontal"]),
        "roof": float(coefficients["roof_inside_upwards"]),
        "ground_floor": float(coefficients["floor_inside_downwards"]),
    }
    outside_coefficient = float(coefficients["external_all_directions"])
    solar_absorptance = float(
        envelope["opaque_surface_properties"]["outside_solar_absorptance"]
    )
    for key in ("external_wall", "roof", "ground_floor"):
        construction = constructions[key]
        construction["properties"] = {
            "inside_surface_resistance": _field(
                1.0 / inside_coefficients[key],
                "ISO combined internal radiative-convective resistance.",
                "m2 K/W",
                ISO_52016_OPAQUE_LOCATOR,
                "number",
                0.0,
                10.0,
            ),
            "outside_surface_resistance": _field(
                1.0 / outside_coefficient,
                "ISO combined external radiative-convective resistance.",
                "m2 K/W",
                ISO_52016_OPAQUE_LOCATOR,
                "number",
                0.0,
                10.0,
            ),
            "inside_surface_solar_absorptivity": _field(
                solar_absorptance, "ISO opaque solar absorptance.", "fraction",
                ISO_52016_OPAQUE_LOCATOR, "number", 0.0, 1.0,
            ),
            "outside_surface_solar_absorptivity": _field(
                solar_absorptance, "ISO opaque solar absorptance.", "fraction",
                ISO_52016_OPAQUE_LOCATOR, "number", 0.0, 1.0,
            ),
        }
        for property_field in construction["properties"].values():
            property_field["source"] = ISO_52016_SOURCE

    external_glazing = constructions["external_glazing"]
    external_glazing.update(
        {
            "description": "ISO 52016-1 Case 600 double-pane glazing.",
            "source": ISO_52016_SOURCE,
            "source_locator": ISO_52016_GLAZING_LOCATOR,
        }
    )
    external_glazing["properties"] = {
        "g_value": _field(
            float(glazing["normal_solar_heat_gain_coefficient"]),
            "ISO corrected solar energy transmittance after Fw=0.9.",
            "fraction",
            external_glazing["source_locator"],
            "number",
            0.0,
            1.0,
        ),
        "visible_light_transmittance": _field(
            float(glazing["normal_single_pane_solar_transmittance"]),
            "MVP optical proxy; daylighting is outside Case 600 outputs.",
            "fraction",
            "IMPLEMENTATION_PROXY - replace if ISO optical data are obtained",
            "number",
            0.0,
            1.0,
        ),
        "frame_percent": _field(
            0.0,
            "BESTEST aperture is represented without a separate frame fraction.",
            "percent",
            external_glazing["source_locator"],
            "number",
            0.0,
            100.0,
        ),
        "frame_resistance": _field(
            0.0,
            "Unused because the modelled frame fraction is zero.",
            "m2 K/W",
            external_glazing["source_locator"],
            "number",
            0.0,
            20.0,
        ),
    }
    cavity_resistance = 1.0 / float(glazing["air_gap_conductance_w_m2k"])
    external_glazing["layers"] = [
        {
            "material_key": "equivalent_glazing_layer",
            "is_cavity": False,
            "properties": {},
        },
        {
            "material_key": "equivalent_glazing_layer",
            "is_cavity": True,
            "properties": {
                "resistance": _field(
                    cavity_resistance,
                    "Combined radiative and convective air-gap resistance.",
                    "m2 K/W",
                    external_glazing["source_locator"],
                    "number",
                    0.000001,
                    100.0,
                )
            },
        },
        {
            "material_key": "equivalent_glazing_layer",
            "is_cavity": False,
            "properties": {},
        },
    ]

    gains = _by_key(assets["gains"])
    for key, name in (
        ("people_gain", "SIA600_PEOPLE_ZERO"),
        ("lighting_gain", "SIA600_LIGHTING_ZERO"),
        ("equipment_gain", "SIA600_EQUIPMENT_200W"),
    ):
        gain = gains[key]
        gain["description"] = "BESTEST Case 600 gain definition."
        gain["source"] = PUBLIC_BESTEST_SOURCE
        gain["source_locator"] = "Case 600 internal gains"
        gain["properties"]["name"]["value"] = name
        for prop in gain["properties"].values():
            prop["source"] = PUBLIC_BESTEST_SOURCE
            prop["source_locator"] = "Case 600 internal gains"
        gain["properties"]["variation_profile"] = _field(
            "ON",
            (
                "VE built-in constant multiplier. Zero-valued Case 600 loads "
                "remain zero through their explicitly zero magnitudes."
            ),
            "VE built-in profile ID",
            "Case 600 constant schedules; portable VE ON representation",
            "string",
        )
    gains["people_gain"]["properties"]["max_sensible_gain"]["value"] = 0.0
    gains["people_gain"]["properties"]["max_latent_gain"]["value"] = 0.0
    gains["lighting_gain"]["properties"]["max_power_consumption"]["value"] = 0.0
    equipment_power_density = 200.0 / 48.0
    equipment_properties = gains["equipment_gain"]["properties"]
    equipment_properties["max_power_consumption"]["value"] = equipment_power_density
    equipment_properties["max_sensible_gain"] = _field(
        equipment_power_density,
        "Constant whole-room sensible gain of 200 W divided by 48 m2.",
        "W/m2",
        "NREL/TP-472-6231 Part I, Case 600 internal gains",
        "number",
        0.0,
        1000.0,
    )
    equipment_properties["max_latent_gain"] = _field(
        0.0,
        "Case 600 internal gain is 100 percent sensible and has no latent part.",
        "W/m2",
        "NREL/TP-472-6231 Part I, Case 600 internal gains",
        "number",
        0.0,
        1000.0,
    )
    equipment_properties["radiant_fraction"] = _field(
        0.6,
        "Radiative fraction of the Case 600 internal sensible gain.",
        "fraction",
        "NREL/TP-472-6231 Part I, Case 600 internal gains",
        "number",
        0.0,
        1.0,
    )
    for property_name in (
        "max_power_consumption", "max_sensible_gain",
        "max_latent_gain", "radiant_fraction",
    ):
        equipment_properties[property_name]["source"] = ISO_52016_SOURCE
        equipment_properties[property_name]["source_locator"] = "Clause 7.2.2.13, page 129"

    exchanges = _by_key(assets["air_exchanges"])
    infiltration = exchanges["infiltration"]
    infiltration["description"] = "ISO Test 1 constant 0.41 ACH infiltration."
    infiltration["source"] = ISO_52016_SOURCE
    infiltration["source_locator"] = "Clause 7.2.2.14, page 129"
    infiltration["properties"]["name"]["value"] = "SIA600_INFILTRATION_0P41ACH"
    infiltration["properties"]["max_flow"]["value"] = 0.3075
    infiltration["properties"]["max_flow"]["description"] = (
        "0.41 ACH x 129.6 m3 / 3600 x 1000 / 48 m2; equivalent "
        "to the published 1.107 m3/(h m2)."
    )
    infiltration["properties"]["max_flow"]["source"] = ISO_52016_SOURCE
    infiltration["properties"]["max_flow"]["source_locator"] = (
        "Clause 7.2.2.14, page 129 and exact unit conversion"
    )
    outdoor_air = exchanges["outdoor_air"]
    outdoor_air["description"] = "No mechanical ventilation in ISO Test 1."
    outdoor_air["source"] = ISO_52016_SOURCE
    outdoor_air["source_locator"] = "Clause 7.2.2.14, page 129"
    outdoor_air["properties"]["name"]["value"] = "SIA600_OUTDOOR_AIR_ZERO"
    outdoor_air["properties"]["max_flow"]["value"] = 0.0
    for prop in outdoor_air["properties"].values():
        prop["source"] = PUBLIC_BESTEST_SOURCE
        prop["source_locator"] = "Case 600 ventilation specification"
    for exchange in (infiltration, outdoor_air):
        exchange["properties"]["variation_profile"] = _field(
            "ON",
            (
                "VE built-in constant multiplier. The zero outdoor-air case "
                "remains zero through its explicitly zero flow magnitude."
            ),
            "VE built-in profile ID",
            "Case 600 constant schedules; portable VE ON representation",
            "string",
        )

    template = assets["thermal_template"]
    template.update(
        {
            "name": "SIA4010_TEST1_CASE600",
            # ``standard`` is the technical VE creation type, not an evidence
            # tier. VEProject.create_thermal_template only creates ``generic``
            # templates; the SIA/BESTEST status remains in source metadata.
            "standard": "generic",
            "description": "ISO Test 1 ideal-loads thermal template for Case 600.",
            "source": ISO_52016_SOURCE,
            "source_locator": "Clauses 7.2.2.15 and 7.2.2.16, pages 129-130",
        }
    )
    template["room_conditions"]["heating_setpoint"] = _field(
        20.0,
        "Ideal heating setpoint.",
        "degC",
        "SIA 4010 Test 1 specification page 1",
        "number",
        0.0,
        40.0,
    )
    template["room_conditions"]["cooling_setpoint"] = _field(
        27.0,
        "Ideal cooling setpoint.",
        "degC",
        "SIA 4010 Test 1 specification page 1",
        "number",
        0.0,
        50.0,
    )
    for setpoint_name in ("heating_setpoint", "cooling_setpoint"):
        template["room_conditions"][setpoint_name]["source"] = ISO_52016_SOURCE
        template["room_conditions"][setpoint_name]["source_locator"] = (
            "Clause 7.2.2.15, pages 129-130"
        )
    template["room_conditions"]["solar_reflected_fraction"] = _field(
        0.0,
        "ISO assumes no solar radiation is lost by re-reflection through the window.",
        "fraction",
        "BS EN ISO 52016-1:2017 clause 7.2.2.9, page 127",
        "number",
        0.0,
        1.0,
    )
    template["room_conditions"]["solar_reflected_fraction"]["source"] = (
        ISO_52016_SOURCE
    )
    template["system_data"]["conditioned"]["source"] = ISO_52016_SOURCE
    template["system_data"]["conditioned"]["source_locator"] = (
        "Clauses 7.2.2.15 and 7.2.2.16, pages 129-130"
    )
    template["system_data"]["system_air_minimum_flowrate"] = _field(
        0.0,
        (
            "ISO Test 1 has no mechanical ventilation. The Apache system "
            "minimum outdoor-air flow is therefore explicitly zero instead "
            "of inheriting the generic office-template assumption."
        ),
        "L/(s person)",
        "Clause 7.2.2.14, page 129",
        "number",
        0.0,
        0.0,
    )
    template["system_data"]["system_air_minimum_flowrate"]["source"] = (
        ISO_52016_SOURCE
    )
    template["system_data"]["system_air_minimum_flowrate_units"] = _field(
        3,
        (
            "VE unit selector for litres per second per person; the associated "
            "ISO Test 1 flow is exactly zero."
        ),
        "VE enum index",
        "IESVE Room/System Air API mapping and clause 7.2.2.14, page 129",
        "integer",
        0,
        4,
    )
    template["system_data"]["system_air_minimum_flowrate_units"]["source"] = (
        ISO_52016_SOURCE
    )
    template["system_data"]["system_air_variation_profile"] = _field(
        "ON",
        (
            "VE built-in constant multiplier for the Apache system air "
            "schedule. ISO Test 1 has no mechanical ventilation, so the "
            "explicitly zero outdoor-air magnitude remains zero."
        ),
        "VE built-in profile ID",
        "Case 600 constant schedules; portable VE ON representation",
        "string",
    )
    template["system_data"]["system_air_variation_profile"]["source"] = (
        ISO_52016_SOURCE
    )
    template["system_data"]["system_air_variation_profile"][
        "source_locator"
    ] = "Clause 7.2.2.14, page 129"
    template["system_data"]["heating_plant_radiant_fraction"] = _field(
        0.0,
        "Ideal heating is fully convective (f_H;c = 1.00).",
        "fraction",
        "BS EN ISO 52016-1:2017 clause 7.2.2.9, page 127",
        "number",
        0.0,
        1.0,
    )
    template["system_data"]["cooling_plant_radiant_fraction"] = _field(
        0.0,
        "Ideal cooling is fully convective (f_C;c = 1.00).",
        "fraction",
        "BS EN ISO 52016-1:2017 clause 7.2.2.9, page 127",
        "number",
        0.0,
        1.0,
    )
    for fraction_name in (
        "heating_plant_radiant_fraction",
        "cooling_plant_radiant_fraction",
    ):
        template["system_data"][fraction_name]["source"] = ISO_52016_SOURCE
        template["system_data"][fraction_name]["source_locator"] = (
            "Clause 7.2.2.9, page 127"
        )
    if assets.get("apache_system"):
        assets["apache_system"].update(
            {
                "name": "SIA4010_CASE600_IDEAL_LOADS",
                "description": "Ideal heating and cooling system for Case 600.",
                "source": PUBLIC_BESTEST_SOURCE,
                "source_locator": "Case 600 operating conditions",
            }
        )
    return assets


def _build_config(
    base: Mapping[str, Any],
    project_root: Path,
    asset_path: Path,
    weather_file: Optional[Path],
) -> Dict[str, Any]:
    """Return the VE configuration with the MVP case settings applied."""

    config = copy.deepcopy(dict(base))
    config["metadata"] = {
        "purpose": "Executable MVP configuration for SIA 4010 Test 1 Case 600.",
        "evidence_tier": "NORMATIVE_ISO_WITH_PUBLIC_REFERENCE_REMAINDERS",
        "compliance_claim_allowed": False,
        "missing_normative_confirmation": [
            "Exact IESVE furniture_mass_factor mapping for 10000 J/(m2 K)",
        ],
    }
    source = ISO_52016_SOURCE
    locator = "Licensed evidence pages 123-127 and SIA 4010 Test 1 specification"
    values = {
        "model_identifier": "SIA4010_1A_600",
        "building_name": "SIA 4010 Test 1 Case 600 - MVP",
        "building_width_m": 8.0,
        "building_depth_m": 6.0,
        "storey_height_m": 2.7,
        "zone_columns": 1,
        "zone_rows": 1,
        "north_axis_degrees": 0.0,
        "asset_provisioning_mode": "create",
        "asset_manifest_file": str(asset_path),
        "project_external_wall_u_w_m2k": 0.509743145366237,
        "project_roof_u_w_m2k": 0.319146628514692,
        "project_ground_floor_u_w_m2k": 0.0392672371721148,
        "project_window_u_w_m2k": 2.984,
        "project_glazing_g_value": 0.71,
        "project_visible_light_transmittance": 0.86156,
        "solar_protection_control_category": "None - Case 600",
        "linear_thermal_bridge_psi_w_mk": 0.0,
        "point_thermal_bridge_chi_w_k": 0.0,
        "weather_file": str(weather_file) if weather_file else None,
        "weather_station": "Denver, Colorado - BESTEST DRYCOLD",
        "weather_dataset_type": (
            weather_file.suffix.lstrip(".").upper() if weather_file else "UNRESOLVED"
        ),
        "climate_scenario": "SIA 4010 Test 1 / BESTEST DRYCOLD",
        "site_latitude_degrees": 39.74,
        "site_longitude_degrees": -104.99,
        "infiltration_m3_h_m2": 1.107,
        "outdoor_air_l_s_person": 0.0,
        "heat_recovery_temperature_efficiency": 0.0,
        "sia2024_use_category": "Not applicable - BESTEST validation cell",
        "occupancy_density_m2_person": 1000.0,
        "occupancy_profile_id": "ON",
        "people_gain_w_person": 0.0,
        "lighting_gain_w_m2": 0.0,
        "equipment_gain_w_m2": 200.0 / 48.0,
        "sia4010_official_bundle_path": str(project_root),
        "sia4010_target_validation_class": "1A",
    }
    for name, value in values.items():
        _set_parameter(config, name, value, source, locator)
    _set_parameter(
        config,
        "project_visible_light_transmittance",
        0.86156,
        "MVP implementation proxy",
        "Replace if ISO 52016-1 optical data are obtained; Case 600 has no daylighting output",
    )
    if not weather_file:
        _set_parameter(
            config,
            "weather_file",
            None,
            "Unresolved client input",
            "Place exactly one .epw, .fwt or .tmy file in the VE project root",
        )
    return config


@dataclass(frozen=True)
class MvpBundleReceipt:
    """Paths and evidence status of one generated Case 600 MVP bundle."""

    case_manifest_path: Path
    config_path: Path
    asset_manifest_path: Path
    audit_path: Path
    weather_file: Optional[Path]
    status: str

    def to_dict(self) -> Dict[str, Any]:
        """Return the bundle receipt as serializable data."""

        return {
            "status": self.status,
            "case_manifest_path": str(self.case_manifest_path),
            "config_path": str(self.config_path),
            "asset_manifest_path": str(self.asset_manifest_path),
            "audit_path": str(self.audit_path),
            "weather_file": str(self.weather_file) if self.weather_file else None,
        }


def build_case600_mvp_bundle(
    project_root: Union[str, Path],
    repository_root: Union[str, Path],
    weather_file: Optional[Union[str, Path]] = None,
) -> MvpBundleReceipt:
    """Create and validate project-local Case 600 inputs without touching VE."""

    project = Path(project_root)
    repository = Path(repository_root)
    project.mkdir(parents=True, exist_ok=True)
    selected_weather = (
        Path(weather_file) if weather_file else discover_weather_file(project)
    )
    if selected_weather:
        selected_weather = selected_weather.resolve()
        if not selected_weather.is_file():
            raise ConfigurationError(
                "Weather file does not exist: {}".format(selected_weather)
            )
        if selected_weather.suffix.casefold() not in SUPPORTED_WEATHER_SUFFIXES:
            raise ConfigurationError(
                "Weather file must be .epw, .fwt or .tmy: {}".format(
                    selected_weather
                )
            )
    weather_verification = _load_weather_verification(selected_weather)

    base_case_path = repository / "config" / "sia4010_classes_1a_1b.json"
    base_config_path = repository / "config" / "reference_model_config.json"
    base_assets_path = repository / "config" / "reference_model_assets.json"
    case_payload = _load_json(base_case_path)
    config_payload = _load_json(base_config_path)
    assets_payload = _load_json(base_assets_path)
    manifest = Sia4010CaseManifest.load(base_case_path)
    envelope = manifest.value("iso_lightweight_construction")
    glazing = manifest.value("iso_test1_glazing")

    case_manifest_path = project / "sia4010_case_manifest.json"
    config_path = project / "reference_model_config.json"
    asset_path = project / "reference_model_assets.json"
    audit_path = project / "sia4010_case600_mvp_audit.json"

    weather_parameter = case_payload["parameters"]["denver_drycold_weather_file"]
    if selected_weather:
        weather_parameter.update(
            {
                "status": "PUBLIC_REFERENCE",
                "value": str(selected_weather),
                "source": (
                    "Public BESTEST TMY1 source identity verified against "
                    "the supplied ISO climate workbook"
                    if weather_verification
                    else "Client-supplied BESTEST weather candidate"
                ),
                "source_locator": (
                    "{}; SHA256={}{}".format(
                        selected_weather.name,
                        _checksum(selected_weather),
                        (
                            "; verification={}".format(
                                weather_verification["path"]
                            )
                            if weather_verification
                            else ""
                        ),
                    )
                ),
            }
        )
    else:
        weather_parameter.update(
            {
                "status": "UNRESOLVED",
                "value": None,
                "source": "Client weather file pending",
                "source_locator": (
                    "Place exactly one .epw, .fwt or .tmy in the VE project root"
                ),
            }
        )

    previous_assets = None
    if asset_path.is_file():
        try:
            previous_assets = _load_json(asset_path)
        except ConfigurationError:
            # A deterministic rebuild remains possible when an old project
            # artifact is malformed; only verified calibration data are
            # eligible for carry-forward.
            previous_assets = None
    generated_assets = _build_assets(assets_payload, envelope, glazing)
    calibration_preserved = _preserve_runtime_glazing_calibration(
        generated_assets,
        previous_assets,
        float(glazing["whole_window_u_w_m2k"]),
    )

    _write_json(case_manifest_path, case_payload)
    _write_json(asset_path, generated_assets)
    _write_json(
        config_path,
        _build_config(config_payload, project, asset_path, selected_weather),
    )

    generated_manifest = Sia4010CaseManifest.load(case_manifest_path)
    case_readiness = generated_manifest.case_readiness("test_1", "600")
    required_parameters = generated_manifest.variants["test_1"][
        "case_required_parameters"
    ]["600"]
    load_asset_manifest(asset_path)
    load_configuration(config_path)
    unresolved = list(case_readiness.missing_parameters)
    provisional = list(case_readiness.provisional_parameters)
    confirmed = [
        parameter_id
        for parameter_id in required_parameters
        if parameter_id not in unresolved and parameter_id not in provisional
    ]
    status = (
        "BLOCKED_WEATHER"
        if "denver_drycold_weather_file" in unresolved
        else "READY_FOR_PROVISIONAL_DEMONSTRATION"
    )
    audit = {
        "schema_version": "1.0",
        "status": status,
        "scenario": "SIA4010_1A_600",
        "compliance_claim_allowed": False,
        "evidence_summary": {
            "confirmed_from_supplied_sia_test_specification": confirmed,
            "public_reference": provisional,
            "unresolved": unresolved,
        },
        "known_uncertainties": [
            {
                "id": "ISO_HOURLY_INTERNAL_CAPACITY_MAPPING",
                "severity": "WARNING",
                "detail": (
                    "ISO requires 10000 J/(m2 K) for air and furniture in the "
                    "hourly method. IES defines furniture_mass_factor relative "
                    "to the ApLocate reference air capacity; the exact factor "
                    "must be calculated and read back before result qualification."
                ),
            },
            {
                "id": "WEATHER_DATASET_IDENTITY",
                "severity": "FAIL" if not selected_weather else "WARNING",
                "detail": (
                    "No weather file is available."
                    if not selected_weather
                    else (
                        (
                            "Hourly calendar, dry-bulb and wind-speed identity "
                            "match the supplied ISO climate workbook. "
                            "Acquisition provenance still requires approval."
                        )
                        if weather_verification
                        else (
                            "The checksum identifies the exact client file, "
                            "but an authorized source record must still confirm "
                            "that it is the required Denver DRYCOLD dataset."
                        )
                    )
                ),
            },
            {
                "id": "VISIBLE_TRANSMITTANCE_PROXY",
                "severity": "WARNING",
                "detail": (
                    "Visible transmittance is an explicit implementation proxy; "
                    "it does not affect the requested Case 600 energy outputs."
                ),
            },
            {
                "id": "VE_GLAZING_RUNTIME_CALIBRATION",
                "severity": "WARNING",
                "detail": (
                    (
                        "A checksum-traced VE runtime cavity calibration was "
                        "preserved; post-mutation read-back must still confirm "
                        "U=2.984 W/(m2 K) and corrected g=0.71."
                    )
                    if calibration_preserved
                    else (
                        "VE read-back must confirm U=2.984 W/(m2 K) and corrected g=0.71; "
                        "run-time cavity calibration may be required."
                    )
                ),
            },
            {
                "id": "VE_RAISED_FLOOR_IMPORT",
                "severity": "WARNING",
                "detail": (
                    "The gbXML floor is RaisedFloor, not SlabOnGrade. VE "
                    "read-back must confirm an exterior/decoupled floor "
                    "boundary after import."
                ),
            },
            {
                "id": "UNUSED_GENERIC_ASSET_ROLES",
                "severity": "WARNING",
                "detail": (
                    "The current generic asset contract provisions internal-wall "
                    "and door roles although Case 600 contains neither object. "
                    "They must remain unassigned and are outside result physics."
                ),
            },
        ],
        "weather_source_identity_verification": weather_verification,
        "weather": {
            "path": str(selected_weather) if selected_weather else None,
            "sha256": _checksum(selected_weather) if selected_weather else None,
            "identity_confirmation_required": not bool(weather_verification),
            "acquisition_provenance_approval_required": True,
        },
        "files": {
            "case_manifest": str(case_manifest_path),
            "configuration": str(config_path),
            "asset_manifest": str(asset_path),
        },
        "public_sources": [
            {"title": PUBLIC_BESTEST_SOURCE, "url": PUBLIC_BESTEST_URL},
            {
                "title": "SIA 4010 Test 1 specification",
                "path": str(
                    repository
                    / "SIA_4010_geteilter_Link"
                    / "Test1"
                    / "Spezifikation_Test1.pdf"
                ),
            },
        ],
    }
    _write_json(audit_path, audit)
    return MvpBundleReceipt(
        case_manifest_path=case_manifest_path,
        config_path=config_path,
        asset_manifest_path=asset_path,
        audit_path=audit_path,
        weather_file=selected_weather,
        status=status,
    )
