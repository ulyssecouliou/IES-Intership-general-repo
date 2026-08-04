"""Source-traced runtime-qualification bundles for Test 1 variants.

Case 600 is the already exercised MVP baseline.  Cases 640 and 600FF use the
same lightweight cell, envelope, glazing, infiltration and internal gains.
Cases 900, 940 and 900FF replace the wall and floor by the source-confirmed
ISO high-mass construction while retaining the Case 600 roof. Their control deltas
are prescribed directly by the supplied SIA 4010 Test 1 specification:

* 640: heating setback to 10 degC from 23:00 to 07:00;
* 600FF: no ideal heating or cooling (free floating).
* 900: high-mass wall and raised floor;
* 940: high-mass wall/floor plus the Case 640 setback;
* 900FF: high-mass wall/floor with no conditioning.

These bundles deliberately remain ``RUNTIME_QUALIFICATION`` artifacts until a
fresh disposable VE project completes strict setter/read-back validation.  No
normative result claim is allowed until VE has persisted and read back every
source-confirmed input and ApacheSim results have been evaluated against the
official SIA workbook.
"""

import copy
from pathlib import Path
from typing import Any, Dict, Optional, Union

from ..asset_manifest import load_asset_manifest
from ..config_loader import load_configuration
from ..exceptions import ConfigurationError
from .case_manifest import Sia4010CaseManifest
from .mvp_bundle import (
    MvpBundleReceipt,
    PUBLIC_BESTEST_SOURCE,
    PUBLIC_BESTEST_URL,
    _checksum,
    _field,
    _load_json,
    _write_json,
    build_case600_mvp_bundle,
)


LIGHTWEIGHT_RUNTIME_QUALIFICATION_CASES = ("640", "600FF")
HEAVYWEIGHT_RUNTIME_QUALIFICATION_CASES = ("900", "940", "900FF")
RUNTIME_QUALIFICATION_CASES = (
    LIGHTWEIGHT_RUNTIME_QUALIFICATION_CASES
    + HEAVYWEIGHT_RUNTIME_QUALIFICATION_CASES
)
TEST1_SPECIFICATION_LOCATOR = "SIA 4010 Test 1 specification pages 1-2"
ASHRAE_HIGH_MASS_SOURCE = (
    "Addendum a to ANSI/ASHRAE Standard 140-2017, Table 5-27"
)
ASHRAE_HIGH_MASS_URL = (
    "https://www.ashrae.org/file%20library/technical%20resources/"
    "standards%20and%20guidelines/standards%20addenda/"
    "140_2017_a_galley_20200812.pdf"
)


def _by_key(items: Any) -> Dict[str, Dict[str, Any]]:
    """Index a manifest list by its stable ``key`` field."""

    return {str(item["key"]): item for item in items}


def _sia_field(
    value: Any,
    description: str,
    units: str,
    expected_type: str,
) -> Dict[str, Any]:
    """Return a manifest field traced to the supplied SIA test specification."""

    field = _field(
        value,
        description,
        units,
        TEST1_SPECIFICATION_LOCATOR,
        expected_type,
    )
    field["source"] = "SIA 4010 Test 1 specification"
    return field


def _rename_runtime_assets(assets: Dict[str, Any], case_id: str) -> None:
    """Give every reusable VE object a case-specific collision-free identity."""

    prefix = "SIA{}".format(case_id)
    for profile in assets["profiles"]:
        reference = str(profile.get("reference", ""))
        if reference.startswith("SIA600_"):
            profile["reference"] = prefix + reference[len("SIA600") :]
    for material in assets["materials"]:
        description = material.get("properties", {}).get("description", {})
        identity = str(description.get("value", ""))
        if identity.startswith("SIA600_"):
            description["value"] = prefix + identity[len("SIA600") :]
    for gain in assets["gains"]:
        name = gain.get("properties", {}).get("name", {})
        identity = str(name.get("value", ""))
        if identity.startswith("SIA600_"):
            name["value"] = prefix + identity[len("SIA600") :]
    for exchange in assets["air_exchanges"]:
        name = exchange.get("properties", {}).get("name", {})
        identity = str(name.get("value", ""))
        if identity.startswith("SIA600_"):
            name["value"] = prefix + identity[len("SIA600") :]
    assets["thermal_template"]["name"] = "SIA4010_TEST1_CASE{}".format(case_id)


def _apply_night_setback_controls(
    assets: Dict[str, Any], case_id: str
) -> None:
    """Add the exact Test 1 Case 640/940 heating-setback contract."""

    profiles = _by_key(assets["profiles"])
    if "heating_setpoint_profile" in profiles:
        raise ConfigurationError(
            "Unexpected duplicate heating_setpoint_profile in Case {} bundle".format(
                case_id
            )
        )
    assets["profiles"].append(
        {
            "key": "heating_setpoint_profile",
            "profile_type": "daily",
            "reference": "SIA{}_HEATING_SETPOINT".format(case_id),
            "modulating": True,
            "units": -1,
            "description": (
                "Case {} daily heating setpoint: 20 degC from 07:00 to "
                "23:00 and 10 degC otherwise.".format(case_id)
            ),
            "source": "SIA 4010 Test 1 specification",
            "source_locator": TEST1_SPECIFICATION_LOCATOR,
            # Duplicate breakpoints express a step without introducing an
            # invented transition hour. The VE runtime probe must accept and
            # read back these points exactly before the case is promoted.
            "data": _sia_field(
                [
                    [0.0, 10.0, ""],
                    [7.0, 10.0, ""],
                    [7.0, 20.0, ""],
                    [23.0, 20.0, ""],
                    [23.0, 10.0, ""],
                    [24.0, 10.0, ""],
                ],
                "Exact Case {} two-level daily heating setpoint.".format(case_id),
                "degC versus hour",
                "array",
            ),
        }
    )
    conditions = assets["thermal_template"]["room_conditions"]
    conditions["heating_profile"] = _sia_field(
        {"profile_ref": "heating_setpoint_profile"},
        "VE daily-profile link for the Case {} heating setpoint.".format(case_id),
        "profile reference",
        "object",
    )
    conditions["heating_setpoint"]["description"] = (
        "Daytime heating setpoint; the linked profile prescribes the 10 degC "
        "night setback."
    )


def _apply_free_float_controls(
    assets: Dict[str, Any], case_id: str
) -> None:
    """Disable room conditioning for the official free-floating case."""

    conditioned = assets["thermal_template"]["system_data"]["conditioned"]
    conditioned.update(
        {
            "value": False,
            "description": (
                "Case {} is free floating; ideal heating and cooling are "
                "disabled.".format(case_id)
            ),
            "source": "SIA 4010 Test 1 specification",
            "source_locator": TEST1_SPECIFICATION_LOCATOR,
        }
    )


def _heavy_field(
    value: Any,
    description: str,
    units: str,
    expected_type: str,
    minimum: Optional[float] = None,
    maximum: Optional[float] = None,
) -> Dict[str, Any]:
    """Return one public-reference high-mass field with exact provenance."""

    field = _field(
        value,
        description,
        units,
        ASHRAE_HIGH_MASS_SOURCE,
        expected_type,
        minimum,
        maximum,
    )
    field["source"] = ASHRAE_HIGH_MASS_SOURCE
    return field


def _apply_heavyweight_envelope(
    assets: Dict[str, Any],
    envelope: Dict[str, Any],
    case_id: str,
) -> None:
    """Replace the Case 600 wall/floor by Table 5-27 high-mass layers.

    Layer order in the VE asset contract is outside-to-inside.  The source
    table is published inside-to-outside, so the wall and floor sequences in
    the configuration are explicitly reversed there and verified here by
    stable material names.  The ideal floor insulation retains the published
    zero density and heat capacity.  VE must accept and read back those zeros;
    no silent positive substitute is introduced by the preparation layer.
    """

    expected_orders = {
        "wall_layers_outside_to_inside": (
            "wood_siding",
            "foam_insulation",
            "concrete_block",
        ),
        "roof_layers_outside_to_inside": (
            "roofdeck",
            "fiberglass_quilt",
            "plasterboard",
        ),
        "floor_layers_outside_to_inside": (
            "ideal_floor_insulation",
            "concrete_slab",
        ),
    }
    indexed_layers: Dict[str, Dict[str, Dict[str, Any]]] = {}
    for collection_name, expected_order in expected_orders.items():
        layers = envelope.get(collection_name)
        if not isinstance(layers, list):
            raise ConfigurationError(
                "Heavyweight envelope is missing {}".format(collection_name)
            )
        actual_order = tuple(str(item.get("material", "")) for item in layers)
        if actual_order != expected_order:
            raise ConfigurationError(
                "{} must be ordered {} but is {}".format(
                    collection_name, expected_order, actual_order
                )
            )
        indexed_layers[collection_name] = {
            str(item["material"]): item for item in layers
        }

    materials = _by_key(assets["materials"])
    material_bindings = {
        "external_plaster": (
            indexed_layers["wall_layers_outside_to_inside"]["wood_siding"],
            "WOOD_SIDING_ROOFDECK",
        ),
        "eps_wall": (
            indexed_layers["wall_layers_outside_to_inside"]["foam_insulation"],
            "FOAM_INSULATION",
        ),
        "modular_brick": (
            indexed_layers["wall_layers_outside_to_inside"]["concrete_block"],
            "CONCRETE_BLOCK",
        ),
        "eps_roof": (
            indexed_layers["roof_layers_outside_to_inside"]["fiberglass_quilt"],
            "FIBERGLASS_QUILT",
        ),
        "internal_plaster": (
            indexed_layers["roof_layers_outside_to_inside"]["plasterboard"],
            "PLASTERBOARD",
        ),
        "xps_ground": (
            indexed_layers["floor_layers_outside_to_inside"][
                "ideal_floor_insulation"
            ],
            "IDEAL_FLOOR_INSULATION",
        ),
        "reinforced_concrete": (
            indexed_layers["floor_layers_outside_to_inside"]["concrete_slab"],
            "CONCRETE_SLAB",
        ),
    }
    for material_key, (definition, identity_suffix) in material_bindings.items():
        material = materials[material_key]
        material.update(
            {
                "description": (
                    "Public-reference high-mass BESTEST material: {}.".format(
                        str(definition["material"]).replace("_", " ")
                    )
                ),
                "source": ASHRAE_HIGH_MASS_SOURCE,
                "source_locator": ASHRAE_HIGH_MASS_SOURCE,
            }
        )
        material["properties"] = {
            "description": _heavy_field(
                "SIA{}_{}".format(case_id, identity_suffix),
                "Stable case-specific VE CDB material identity.",
                "text",
                "string",
            ),
            "conductivity": _heavy_field(
                float(definition["conductivity_w_mk"]),
                "Thermal conductivity.",
                "W/(m K)",
                "number",
                0.001,
                500.0,
            ),
            "density": _heavy_field(
                float(definition["density_kg_m3"]),
                (
                    "Dry density; zero is the published ideal-insulation "
                    "value and requires exact VE runtime read-back."
                ),
                "kg/m3",
                "number",
                0.0,
                30000.0,
            ),
            "specific_heat_capacity": _heavy_field(
                float(definition["specific_heat_j_kgk"]),
                (
                    "Specific heat capacity; zero is the published "
                    "ideal-insulation value and requires exact VE runtime "
                    "read-back."
                ),
                "J/(kg K)",
                "number",
                0.0,
                10000.0,
            ),
        }

    constructions = _by_key(assets["constructions"])
    construction_bindings = {
        "external_wall": (
            "wall_layers_outside_to_inside",
            {
                "wood_siding": "external_plaster",
                "foam_insulation": "eps_wall",
                "concrete_block": "modular_brick",
            },
        ),
        "roof": (
            "roof_layers_outside_to_inside",
            {
                "roofdeck": "external_plaster",
                "fiberglass_quilt": "eps_roof",
                "plasterboard": "internal_plaster",
            },
        ),
        "ground_floor": (
            "floor_layers_outside_to_inside",
            {
                "ideal_floor_insulation": "xps_ground",
                "concrete_slab": "reinforced_concrete",
            },
        ),
    }
    for construction_key, (
        collection_name,
        material_keys,
    ) in construction_bindings.items():
        construction = constructions[construction_key]
        construction.update(
            {
                "description": (
                    "Public-reference BESTEST high-mass {} construction, "
                    "ordered outside to inside.".format(
                        construction_key.replace("_", " ")
                    )
                ),
                "source": ASHRAE_HIGH_MASS_SOURCE,
                "source_locator": ASHRAE_HIGH_MASS_SOURCE,
            }
        )
        construction["layers"] = [
            {
                "material_key": material_keys[str(layer["material"])],
                "is_cavity": False,
                "properties": {
                    "thickness": _heavy_field(
                        float(layer["thickness_m"]),
                        "Table 5-27 construction-layer thickness.",
                        "m",
                        "number",
                        0.0001,
                        5.0,
                    )
                },
            }
            for layer in envelope[collection_name]
        ]

    assets["metadata"].update(
        {
            "envelope_mass": "HIGH_MASS",
            "heavyweight_public_source": ASHRAE_HIGH_MASS_SOURCE,
            "heavyweight_public_source_url": ASHRAE_HIGH_MASS_URL,
            "ideal_floor_insulation_runtime_guardrail": (
                "Published density=0 kg/m3 and specific heat=0 J/(kg K) "
                "must be accepted and read back by VE. Any runtime-required "
                "minimum must stop qualification and be reported for review."
            ),
        }
    )


def _update_config(
    config: Dict[str, Any],
    *,
    case_id: str,
    asset_path: Path,
) -> None:
    """Retag the executable configuration for one exact lightweight case."""

    parameters = config["parameters"]
    replacements = {
        "model_identifier": "SIA4010_TEST1_{}".format(case_id),
        "building_name": "SIA 4010 Test 1 Case {} - runtime qualification".format(
            case_id
        ),
        "asset_manifest_file": str(asset_path),
    }
    for key, value in replacements.items():
        parameters[key]["value"] = value
        parameters[key]["source"] = "SIA 4010 Test 1 runtime qualification"
        parameters[key]["source_locator"] = TEST1_SPECIFICATION_LOCATOR
    config["metadata"].update(
        {
            "purpose": (
                "Executable runtime-qualification configuration for SIA 4010 "
                "Test 1 Case {}.".format(case_id)
            ),
            "sia4010_variant": "test_1",
            "sia4010_case_id": case_id,
            "compliance_claim_allowed": False,
            "runtime_qualification_required": True,
        }
    )


def build_test1_runtime_probe_bundle(
    project_root: Union[str, Path],
    repository_root: Union[str, Path],
    case_id: str,
    weather_file: Optional[Union[str, Path]] = None,
) -> MvpBundleReceipt:
    """Build a guarded, unqualified VE bundle for one supported Test 1 case.

    The function is preparation-only. It writes JSON files and validates their
    schemas but never imports geometry or mutates VE.
    """

    normalized_case = str(case_id).upper()
    if normalized_case not in RUNTIME_QUALIFICATION_CASES:
        raise ConfigurationError(
            "Test 1 runtime qualification supports only {}: {!r}".format(
                ", ".join(RUNTIME_QUALIFICATION_CASES), case_id
            )
        )
    receipt = build_case600_mvp_bundle(
        project_root,
        repository_root,
        weather_file=weather_file,
    )
    project = Path(project_root)
    repository = Path(repository_root)
    case_manifest = _load_json(receipt.case_manifest_path)
    assets = _load_json(receipt.asset_manifest_path)
    config = _load_json(receipt.config_path)
    is_heavyweight = normalized_case in HEAVYWEIGHT_RUNTIME_QUALIFICATION_CASES

    assets["metadata"].update(
        {
            "purpose": (
                "Runtime-qualification VE asset package for SIA 4010 Test 1 "
                "Case {}.".format(normalized_case)
            ),
            "sia4010_variant": "test_1",
            "sia4010_case_id": normalized_case,
            "evidence_tier": "NORMATIVE_INPUT_RUNTIME_QUALIFICATION",
            "compliance_claim_allowed": False,
            "runtime_qualification_required": True,
            "guardrail": (
                "The exact Test 1 control delta is source-traced, but this "
                "bundle cannot be called a verified generator until a fresh "
                "VE project completes all setter/read-back checks."
            ),
        }
    )
    _rename_runtime_assets(assets, normalized_case)
    if is_heavyweight:
        heavyweight = case_manifest["parameters"][
            "iso_heavyweight_construction"
        ].get("value")
        if not isinstance(heavyweight, dict):
            raise ConfigurationError(
                "iso_heavyweight_construction must contain a structured value"
            )
        _apply_heavyweight_envelope(
            assets,
            heavyweight,
            normalized_case,
        )
    else:
        assets["metadata"]["envelope_mass"] = "LIGHTWEIGHT"
    if normalized_case in {"640", "940"}:
        _apply_night_setback_controls(assets, normalized_case)
    elif normalized_case in {"600FF", "900FF"}:
        _apply_free_float_controls(assets, normalized_case)
    _update_config(
        config,
        case_id=normalized_case,
        asset_path=receipt.asset_manifest_path,
    )

    _write_json(receipt.case_manifest_path, case_manifest)
    _write_json(receipt.asset_manifest_path, assets)
    _write_json(receipt.config_path, config)
    load_asset_manifest(receipt.asset_manifest_path)
    load_configuration(receipt.config_path)

    manifest = Sia4010CaseManifest.load(receipt.case_manifest_path)
    readiness = manifest.case_readiness("test_1", normalized_case)
    required = manifest.variants["test_1"]["case_required_parameters"][
        normalized_case
    ]
    unresolved = list(readiness.missing_parameters)
    provisional = list(readiness.provisional_parameters)
    confirmed = [
        parameter_id
        for parameter_id in required
        if parameter_id not in unresolved and parameter_id not in provisional
    ]
    selected_weather = receipt.weather_file
    status = (
        "BLOCKED_WEATHER"
        if "denver_drycold_weather_file" in unresolved
        else "READY_FOR_PROVISIONAL_RUNTIME_QUALIFICATION"
    )
    case_specific_uncertainties = []
    if is_heavyweight:
        case_specific_uncertainties.append(
            {
                "id": "VE_HIGH_MASS_ENVELOPE_RUNTIME_QUALIFICATION",
                "severity": "WARNING",
                "detail": (
                    "VE must set and read back the Table 5-27 wall, roof and "
                    "raised-floor layer order and thermal properties. The "
                    "ideal floor insulation must preserve zero density and "
                    "specific heat; any required program minimum fails this "
                    "qualification for explicit review."
                ),
            }
        )
    if normalized_case in {"640", "940"}:
        case_specific_uncertainties.append(
            {
            "id": "VE_HEATING_PROFILE_RUNTIME_QUALIFICATION",
            "severity": "WARNING",
            "detail": (
                "VE must accept and read back the two-level setpoint profile "
                "and the room must resolve its heating_profile to that exact ID."
            ),
            }
        )
    elif normalized_case in {"600FF", "900FF"}:
        case_specific_uncertainties.append(
            {
            "id": "VE_FREE_FLOAT_RUNTIME_QUALIFICATION",
            "severity": "WARNING",
            "detail": (
                "VE must read back conditioned=False and ApacheSim must prove "
                "zero ideal heating/cooling delivery for the free-floating room."
            ),
            }
        )
    else:
        case_specific_uncertainties.append(
            {
                "id": "VE_CONDITIONED_HIGH_MASS_RUNTIME_QUALIFICATION",
                "severity": "WARNING",
                "detail": (
                    "VE must verify the high-mass fabric while preserving the "
                    "Case 600 ideal heating/cooling controls."
                ),
            }
        )
    audit_path = project / "sia4010_test1_{}_qualification_audit.json".format(
        normalized_case.casefold()
    )
    audit = {
        "schema_version": "1.0",
        "status": status,
        "scenario": "SIA4010_TEST1_{}".format(normalized_case),
        "variant": "test_1",
        "case_id": normalized_case,
        "compliance_claim_allowed": False,
        "runtime_qualification_required": True,
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
                    "The {} ISO fabric is source-confirmed, but the exact "
                    "IESVE furniture_mass_factor mapping for the ISO hourly "
                    "air-and-furniture capacity must still be set and read back."
                    .format("high-mass" if is_heavyweight else "lightweight")
                ),
            },
            *case_specific_uncertainties,
        ],
        "weather": {
            "path": str(selected_weather) if selected_weather else None,
            "sha256": _checksum(selected_weather) if selected_weather else None,
        },
        "files": {
            "case_manifest": str(receipt.case_manifest_path),
            "configuration": str(receipt.config_path),
            "asset_manifest": str(receipt.asset_manifest_path),
        },
        "sources": [
            {
                "title": "SIA 4010 Test 1 specification",
                "path": str(
                    repository
                    / "SIA_4010_geteilter_Link"
                    / "Test1"
                    / "Spezifikation_Test1.pdf"
                ),
                "locator": TEST1_SPECIFICATION_LOCATOR,
            },
            {
                "title": PUBLIC_BESTEST_SOURCE,
                "url": PUBLIC_BESTEST_URL,
                "scope": (
                    "Public-reference Case 600 physics and BESTEST lineage"
                ),
            },
            *(
                [
                    {
                        "title": ASHRAE_HIGH_MASS_SOURCE,
                        "url": ASHRAE_HIGH_MASS_URL,
                        "scope": (
                            "Public-reference wall, roof and raised-floor "
                            "material properties for Cases 900/940/900FF"
                        ),
                    }
                ]
                if is_heavyweight
                else []
            ),
        ],
    }
    _write_json(audit_path, audit)
    return MvpBundleReceipt(
        case_manifest_path=receipt.case_manifest_path,
        config_path=receipt.config_path,
        asset_manifest_path=receipt.asset_manifest_path,
        audit_path=audit_path,
        weather_file=selected_weather,
        status=status,
    )


def build_test1_lightweight_probe_bundle(
    project_root: Union[str, Path],
    repository_root: Union[str, Path],
    case_id: str,
    weather_file: Optional[Union[str, Path]] = None,
) -> MvpBundleReceipt:
    """Backward-compatible lightweight-only wrapper for Cases 640 and 600FF."""

    normalized_case = str(case_id).upper()
    if normalized_case not in LIGHTWEIGHT_RUNTIME_QUALIFICATION_CASES:
        raise ConfigurationError(
            "Lightweight Test 1 runtime qualification supports only {}: {!r}".format(
                ", ".join(LIGHTWEIGHT_RUNTIME_QUALIFICATION_CASES), case_id
            )
        )
    return build_test1_runtime_probe_bundle(
        project_root,
        repository_root,
        normalized_case,
        weather_file=weather_file,
    )


def build_test1_heavyweight_probe_bundle(
    project_root: Union[str, Path],
    repository_root: Union[str, Path],
    case_id: str,
    weather_file: Optional[Union[str, Path]] = None,
) -> MvpBundleReceipt:
    """Build a high-mass runtime probe for Case 900, 940 or 900FF."""

    normalized_case = str(case_id).upper()
    if normalized_case not in HEAVYWEIGHT_RUNTIME_QUALIFICATION_CASES:
        raise ConfigurationError(
            "Heavyweight Test 1 runtime qualification supports only {}: {!r}".format(
                ", ".join(HEAVYWEIGHT_RUNTIME_QUALIFICATION_CASES),
                case_id,
            )
        )
    return build_test1_runtime_probe_bundle(
        project_root,
        repository_root,
        normalized_case,
        weather_file=weather_file,
    )
