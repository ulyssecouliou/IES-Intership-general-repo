"""Source-traced bundles for the Test 1 diagnostic chain 1A to 1E.

The chain is cumulative and the specification states it that way: 1A is case 600
on the Zurich-Kloten climate, 1B adds the new window, 1C the adjusted
infiltration, 1D the SIA 2024 usage, and 1E the fabric awning. So each bundle is
the case-600 baseline with every earlier link applied, and a bundle for 1D is a
bundle for 1C plus one step.

EVERY VALUE COMES FROM THE FROZEN REFERENCE. This module reads
``refs/reference-data/test-1.diagnostics.ref.json``, which the producer relieved
from the official PDFs, and applies it. It contains no normative constant of its
own, so a value can only be wrong here if it is wrong in the reference, where it
carries its source locator.

WHAT IS NOT DETERMINED IS NOT APPLIED. One element of the chain still cannot be
built: the fabric awning. Its delegated input exists in the catalogue as
``sia_example_building_fabric_awning_detail`` with the schema
``sia4010.shading_device_definition.v1``, and an example template ships in
``config/external_input_examples``, but no binding is supplied and no VE shading
object is generated for Test 1. It comes out as a named blocker, and case 1E is
reported ``BLOCKED``. Filling it with a plausible number would produce a model
that runs, compares against a real reference band, and lies.

The occupant heat gain was blocked here at first, on the grounds that 1.2 met
becomes watts only through a body-area convention the specification omits. That
was true of the specification and wrong as a conclusion: the SIA 2024 authority
extract we already hold states the sensible gain directly in watts per square
metre, so no convention is needed and link 1D applies in full.

NO CLAIM. These are preparation artifacts. Cases 1A to 1D carry no acceptance
criterion at all -- the specification asks for annual hourly heating and cooling
power and states none -- so nothing here may be presented as a result. Only 1E is
judged, and only after a real VE run.
"""

import copy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from ..asset_manifest import load_asset_manifest
from ..config_loader import load_configuration
from ..exceptions import ConfigurationError
from .mvp_bundle import (
    MvpBundleReceipt,
    _checksum,
    _load_json,
    _write_json,
    build_case600_mvp_bundle,
)


#: The chain, in the order the specification reads it. Position matters: a
#: bundle applies every link up to and including the requested case.
DIAGNOSTIC_CHAIN: Tuple[str, ...] = ("1A", "1B", "1C", "1D", "1E")

#: Frozen reference, relative to the repository root.
DIAGNOSTICS_REFERENCE = Path("refs") / "reference-data" / "test-1.diagnostics.ref.json"

#: Locator cited on every field this module rewrites.
CHAIN_LOCATOR = (
    "SIA 4010 Test 1 and Test 2 specifications, frozen in "
    "refs/reference-data/test-1.diagnostics.ref.json"
)

#: Conversion from the specification's infiltration unit to the VE air-exchange
#: unit. It is NOT a guess: the case-600 baseline carries the same quantity in
#: both units, 1.107 m3/(h m2) in the configuration and 0.3075 in the asset
#: manifest, and 1.107 / 3.6 == 0.3075 exactly. Dividing m3/(h m2) by 3.6 yields
#: litres per second per square metre. ``test_the_conversion_factor_is_proven_by
#: _the_baseline`` reproduces that check rather than trusting this note.
INFILTRATION_M3_H_M2_TO_L_S_M2 = 3.6

#: The one blocker left, raised instead of inventing a shading device.
BLOCKER_AWNING = "TEST1_DIAGNOSTIC_FABRIC_AWNING_GENERATOR_NOT_IMPLEMENTED"


def _chain_index(case_id: str) -> int:
    """Return the position of one diagnostic case in the chain."""

    normalized = str(case_id).upper()
    if normalized not in DIAGNOSTIC_CHAIN:
        raise ConfigurationError(
            "Test 1 diagnostic chain covers only {}: {!r}".format(
                ", ".join(DIAGNOSTIC_CHAIN), case_id
            )
        )
    return DIAGNOSTIC_CHAIN.index(normalized)


def _releve(reference: Dict[str, Any], bloc: str, cle: str) -> Any:
    """Return one relieved value, refusing anything left to confirm.

    A field the producer could not read comes out ``null`` with a reason. Using
    it would silently substitute ``None`` for a normative value, so this fails
    closed and names the field.
    """

    try:
        champ = reference["parametres"][bloc][cle]
    except KeyError:
        raise ConfigurationError(
            "Frozen diagnostic reference has no field {}.{}".format(bloc, cle)
        ) from None
    if champ.get("statut") != "RELEVE" or champ.get("valeur") is None:
        raise ConfigurationError(
            "Frozen diagnostic reference leaves {}.{} unconfirmed: {}".format(
                bloc, cle, champ.get("raison") or "no reason recorded"
            )
        )
    return champ["valeur"]


def load_diagnostics_reference(
    repository_root: Union[str, Path]
) -> Dict[str, Any]:
    """Load the frozen chain reference, or say exactly what is missing."""

    path = Path(repository_root) / DIAGNOSTICS_REFERENCE
    if not path.is_file():
        raise ConfigurationError(
            "Frozen Test 1 diagnostic reference is missing: {}. Produce it with "
            "scripts/build_test1_diagnostics_reference.py --ecrire".format(path)
        )
    return _load_json(path)


def _set_parameter(
    config: Dict[str, Any],
    key: str,
    value: Any,
    locator: str,
) -> None:
    """Rewrite one configuration parameter, keeping its traceability."""

    parameters = config["parameters"]
    if key not in parameters:
        raise ConfigurationError(
            "Case 600 configuration has no parameter {!r} to retag".format(key)
        )
    parameters[key]["value"] = value
    parameters[key]["source"] = "SIA 4010 Test 1 diagnostic chain"
    parameters[key]["source_locator"] = locator


def _construction(assets: Dict[str, Any], key: str) -> Dict[str, Any]:
    """Return one construction of the asset manifest by its stable key."""

    for construction in assets["constructions"]:
        if str(construction.get("key")) == key:
            return construction
    raise ConfigurationError(
        "Case 600 asset manifest has no construction {!r}".format(key)
    )


def _gain(assets: Dict[str, Any], key: str) -> Dict[str, Any]:
    """Return one internal gain of the asset manifest by its stable key."""

    for gain in assets["gains"]:
        if str(gain.get("key")) == key:
            return gain
    raise ConfigurationError(
        "Case 600 asset manifest has no gain {!r}".format(key)
    )


def _air_exchange(assets: Dict[str, Any], key: str) -> Dict[str, Any]:
    """Return one air exchange of the asset manifest by its stable key."""

    for exchange in assets["air_exchanges"]:
        if str(exchange.get("key")) == key:
            return exchange
    raise ConfigurationError(
        "Case 600 asset manifest has no air exchange {!r}".format(key)
    )


def _apply_kloten_climate(
    config: Dict[str, Any],
    reference: Dict[str, Any],
    weather_file: Optional[Union[str, Path]],
) -> Dict[str, Any]:
    """Link 1A: replace the DRYCOLD climate by Zurich-Kloten.

    The weather file is not inside the reference -- it is a delegated input the
    operator supplies. Without it the link is reported blocked rather than left
    silently on DRYCOLD, which would produce a Denver result labelled Kloten.
    """

    if weather_file is None:
        return {
            "id": "TEST1_DIAGNOSTIC_KLOTEN_WEATHER_NOT_SUPPLIED",
            "severity": "BLOCKER",
            "detail": (
                "Link 1A replaces the Test 1 DRYCOLD climate by SIA 2028 DRY "
                "normal Zurich-Kloten. No Kloten weather file was supplied, so "
                "the baseline climate is left untouched: running it would "
                "produce a Denver result labelled Kloten."
            ),
        }
    path = Path(weather_file)
    if not path.is_file():
        return {
            "id": "TEST1_DIAGNOSTIC_KLOTEN_WEATHER_MISSING_FILE",
            "severity": "BLOCKER",
            "detail": "Supplied Kloten weather file does not exist: {}".format(path),
        }
    _set_parameter(config, "weather_file", str(path), CHAIN_LOCATOR)
    _set_parameter(config, "weather_dataset_type", "EPW", CHAIN_LOCATOR)
    _set_parameter(
        config,
        "weather_station",
        "Zurich-Kloten - SIA 2028 DRY normal",
        CHAIN_LOCATOR,
    )
    return {}


def _apply_new_window(
    config: Dict[str, Any],
    assets: Dict[str, Any],
    reference: Dict[str, Any],
) -> Dict[str, Any]:
    """Link 1B: the window the Test 2 specification prescribes.

    The specification states the whole-window figures directly, which is what
    the case-600 manifest models, so no layer-level derivation is needed. It also
    settles a question the example-building documentation leaves open by giving
    two total g values; the divergence on the U value is recorded in the
    reference and the specification governs.
    """

    g_value = _releve(reference, "vitrage", "g_total")
    visible = _releve(reference, "vitrage", "transmission_visible")
    u_value = _releve(reference, "vitrage", "u_vitrage_w_m2k")

    _set_parameter(config, "project_glazing_g_value", g_value, CHAIN_LOCATOR)
    _set_parameter(
        config, "project_visible_light_transmittance", visible, CHAIN_LOCATOR
    )
    _set_parameter(config, "project_window_u_w_m2k", u_value, CHAIN_LOCATOR)

    glazing = _construction(assets, "external_glazing")
    properties = glazing["properties"]
    properties["g_value"]["value"] = g_value
    properties["g_value"]["source_locator"] = CHAIN_LOCATOR
    properties["visible_light_transmittance"]["value"] = visible
    properties["visible_light_transmittance"]["source_locator"] = CHAIN_LOCATOR
    return {}


def _apply_adjusted_infiltration(
    config: Dict[str, Any],
    assets: Dict[str, Any],
    reference: Dict[str, Any],
) -> Dict[str, Any]:
    """Link 1C: infiltration per SIA 2024:2021, in the unit VE stores."""

    m3_h_m2 = _releve(reference, "infiltration", "debit_m3_h_m2")
    l_s_m2 = m3_h_m2 / INFILTRATION_M3_H_M2_TO_L_S_M2

    _set_parameter(config, "infiltration_m3_h_m2", m3_h_m2, CHAIN_LOCATOR)
    exchange = _air_exchange(assets, "infiltration")
    properties = exchange["properties"]
    properties["max_flow"]["value"] = round(l_s_m2, 6)
    properties["max_flow"]["source_locator"] = CHAIN_LOCATOR
    # The identity carries the value, as the baseline's own name does. A name
    # still saying 0P41ACH beside a different flow is how a stale object gets
    # reused in the construction database.
    properties["name"]["value"] = "SIA_DIAG_INFILTRATION_{}M3HM2".format(
        str(m3_h_m2).replace(".", "P")
    )
    return {}


def _apply_sia2024_usage(
    config: Dict[str, Any],
    assets: Dict[str, Any],
    reference: Dict[str, Any],
) -> Dict[str, Any]:
    """Link 1D: the SIA 2024 category 3.1 usage.

    The equipment and lighting power densities and the occupant density come
    from the specification. The occupant heat gain does NOT need the met-to-watt
    conversion this function once refused to make: the SIA 2024 authority
    extract states the sensible gain directly, in watts per square metre, so the
    per-person figure is that value times the floor area per person -- an
    arithmetic step on two stated numbers, not a convention.
    """

    equipment = _releve(reference, "apports", "appareils_w_m2")
    lighting = _releve(reference, "apports", "eclairage_w_m2")
    density = _releve(reference, "apports", "personnes_m2_par_personne")
    sensible_w_m2 = _releve(
        reference, "apports", "personnes_gain_sensible_w_m2"
    )
    per_person = round(sensible_w_m2 * density, 6)

    _set_parameter(config, "equipment_gain_w_m2", equipment, CHAIN_LOCATOR)
    _set_parameter(config, "lighting_gain_w_m2", lighting, CHAIN_LOCATOR)
    _set_parameter(
        config, "occupancy_density_m2_person", density, CHAIN_LOCATOR
    )
    _set_parameter(config, "people_gain_w_person", per_person, CHAIN_LOCATOR)

    for key, value in (
        ("equipment_gain", equipment),
        ("lighting_gain", lighting),
    ):
        gain = _gain(assets, key)
        consumption = gain["properties"].get("max_power_consumption")
        if consumption is None:
            raise ConfigurationError(
                "Gain {!r} has no max_power_consumption to retag".format(key)
            )
        consumption["value"] = value
        consumption["source_locator"] = CHAIN_LOCATOR

    return {}


def _apply_fabric_awning(reference: Dict[str, Any]) -> Dict[str, Any]:
    """Link 1E: the awning. Recorded as a blocker, not built."""

    produit = _releve(reference, "store", "produit")
    seuil = _releve(reference, "store", "seuil_activation_w_m2")
    return {
        "id": BLOCKER_AWNING,
        "severity": "BLOCKER",
        "detail": (
            "Link 1E adds the external fabric awning {} by {}, closing at {} "
            "W/m2 of external solar irradiance. No VE shading object is "
            "generated for Test 1, and the official documentation gives "
            "whole-window properties with the shade deployed rather than a "
            "device to build, so the deployed-state figures cannot be turned "
            "into a shading generator without a mapping decision. Case 1E "
            "carries the only pass/fail criterion of Test 1, which makes an "
            "invented mapping the most dangerous shortcut available here."
            .format(produit["type"], produit["fabricant"], seuil)
        ),
    }


def build_test1_diagnostic_bundle(
    project_root: Union[str, Path],
    repository_root: Union[str, Path],
    case_id: str,
    weather_file: Optional[Union[str, Path]] = None,
    kloten_weather_file: Optional[Union[str, Path]] = None,
) -> MvpBundleReceipt:
    """Build the bundle of one diagnostic case, every earlier link applied.

    Args:
        project_root: Saved disposable VE project folder.
        repository_root: Repository root, holding the frozen reference.
        case_id: One of 1A, 1B, 1C, 1D, 1E.
        weather_file: Baseline Test 1 DRYCOLD file, passed through to case 600.
        kloten_weather_file: Zurich-Kloten EPW that link 1A substitutes.

    Returns:
        MvpBundleReceipt: Receipt whose status is BLOCKED when any link of the
        requested case could not be applied from published data.

    Raises:
        ConfigurationError: If the case is unknown, or the frozen reference is
            missing or leaves a needed field unconfirmed.
    """

    normalized = str(case_id).upper()
    depth = _chain_index(normalized)
    reference = load_diagnostics_reference(repository_root)

    receipt = build_case600_mvp_bundle(
        project_root,
        repository_root,
        weather_file=weather_file,
    )
    project = Path(project_root)
    assets = _load_json(receipt.asset_manifest_path)
    config = _load_json(receipt.config_path)

    blockers: List[Dict[str, Any]] = []
    applied: List[str] = []

    def record(link: str, outcome: Dict[str, Any]) -> None:
        if outcome:
            blockers.append(dict(outcome, link=link))
        else:
            applied.append(link)

    record("1A", _apply_kloten_climate(config, reference, kloten_weather_file))
    if depth >= 1:
        record("1B", _apply_new_window(config, assets, reference))
    if depth >= 2:
        record("1C", _apply_adjusted_infiltration(config, assets, reference))
    if depth >= 3:
        record("1D", _apply_sia2024_usage(config, assets, reference))
    if depth >= 4:
        record("1E", _apply_fabric_awning(reference))

    assets["metadata"].update(
        {
            "purpose": (
                "Preparation bundle for SIA 4010 Test 1 diagnostic case "
                "{}.".format(normalized)
            ),
            "sia4010_variant": "test_1",
            "sia4010_case_id": normalized,
            "evidence_tier": "NORMATIVE_INPUT_DIAGNOSTIC_CHAIN",
            "compliance_claim_allowed": False,
            "runtime_qualification_required": True,
            "diagnostic_chain_applied": list(applied),
            "diagnostic_chain_blocked": [item["link"] for item in blockers],
        }
    )
    config["metadata"].update(
        {
            "purpose": (
                "Executable configuration for SIA 4010 Test 1 diagnostic case "
                "{}.".format(normalized)
            ),
            "sia4010_variant": "test_1",
            "sia4010_case_id": normalized,
            "compliance_claim_allowed": False,
            "runtime_qualification_required": True,
        }
    )

    _write_json(receipt.asset_manifest_path, assets)
    _write_json(receipt.config_path, config)
    load_asset_manifest(receipt.asset_manifest_path)
    load_configuration(receipt.config_path)

    status = (
        "BLOCKED_DIAGNOSTIC_CHAIN"
        if blockers
        else "READY_FOR_PROVISIONAL_RUNTIME_QUALIFICATION"
    )
    audit_path = project / "sia4010_test1_diagnostic_{}_audit.json".format(
        normalized.casefold()
    )
    audit = {
        "schema_version": "1.0",
        "status": status,
        "variant": "test_1",
        "case_id": normalized,
        "compliance_claim_allowed": False,
        "runtime_qualification_required": True,
        "acceptance_criterion": (
            "NONE_STATED_BY_SPECIFICATION"
            if normalized != "1E"
            else "PASS_FAIL_STREUBEREICH"
        ),
        "criterion_note": (
            "The specification requires annual data sets with hourly heating "
            "and cooling power for cases 1A to 1D and states no comparison "
            "criterion, so no reference band exists for them and none may be "
            "invented. Only 1E is judged."
        ),
        "chain_applied": applied,
        "chain_blocked": blockers,
        "reference": {
            "path": str(DIAGNOSTICS_REFERENCE).replace("\\", "/"),
            "sha256": _checksum(
                Path(repository_root) / DIAGNOSTICS_REFERENCE
            ),
        },
        "guardrail": (
            "Preparation artifact. No VE object is created by this module, and "
            "no result may be presented until a real VE run has qualified every "
            "setter and read-back."
        ),
    }
    _write_json(audit_path, audit)

    return MvpBundleReceipt(
        status=status,
        case_manifest_path=receipt.case_manifest_path,
        config_path=receipt.config_path,
        asset_manifest_path=receipt.asset_manifest_path,
        audit_path=audit_path,
        weather_file=receipt.weather_file,
    )
