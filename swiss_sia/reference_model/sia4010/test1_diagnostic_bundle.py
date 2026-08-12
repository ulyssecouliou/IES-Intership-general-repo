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

WHAT IS NOT DETERMINED IS NOT APPLIED. All five links now build, the awning
included: its control contract comes from ``test2a_shading_control``, which the
Test 1 specification prescribes by defining 1E as the diagnostic-test-2-E1
shading, fed with the deployed-state whole-window properties from the frozen
reference.

Case 1E is still reported ``BLOCKED``, and for a reason worth stating precisely,
because it is no longer "no generator exists". The device is settled; the
DYNAMICS are not. The specification confirms the 150 W/m2 threshold and states
neither the comparison operator, nor the release rule, nor the exact irradiance
signal, and VE exposes separate lower and raise thresholds that cannot be shown
equivalent to that rule from their names. Those reserves are carried through from
the module that enumerated them rather than resolved by choice: 1E is the only
pass/fail case of Test 1, so guessing the release rule would move a real
verdict.

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
    two total g values, and the reference records which normative block the
    specification's U value comes from: it is the ISO 15099 winter figure, not
    the EN ISO 52022-3 reference one, and the two documents agree once the right
    block is compared.
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


def _deployed(reference: Dict[str, Any], bloc: str, grandeur: str) -> float:
    """Return one whole-window property with the shade deployed.

    The deployed column is the awning's effect on the window, which is what the
    documentation publishes -- there is no separate fabric datasheet in the
    official package. Reading the retracted column here instead would describe a
    window with no shade at all while still looking like a shaded one.
    """

    blocs = (reference.get("fenetre_entiere") or {}).get("blocs") or {}
    grandeurs = (blocs.get(bloc) or {}).get("grandeurs") or {}
    if grandeur not in grandeurs:
        raise ConfigurationError(
            "Frozen diagnostic reference has no {}.{} whole-window "
            "property".format(bloc, grandeur)
        )
    return float(grandeurs[grandeur]["store_deploye"])


def _assert_same_device_as_test2a(reference: Dict[str, Any]) -> None:
    """Check that case 1E's awning really is the Test 2A one.

    The specification says so -- "gemaess Diagnosetest 2 E1" -- and the frozen
    reference relieved the product and threshold from the Test 2A block of the
    Test 2 specification, so they are shared by construction today. If a future
    extraction ever separated them, reusing the Test 2A contract would silently
    describe the wrong device, and that is worth failing on rather than assuming.
    """

    definition = next(
        (item for item in reference.get("chaine", []) if item["cas"] == "1E"),
        None,
    )
    if definition is None or not definition.get("definition_verbatim_de"):
        raise ConfigurationError(
            "Frozen diagnostic reference carries no verbatim definition for 1E"
        )
    verbatim = definition["definition_verbatim_de"]
    if "2 E1" not in verbatim.replace(" ", " "):
        raise ConfigurationError(
            "Case 1E no longer cites diagnostic test 2 E1, so the Test 2A "
            "fabric-awning contract may not be reused for it: {!r}".format(
                verbatim
            )
        )


def _awning_official_inputs(reference: Dict[str, Any]) -> Dict[str, Any]:
    """Map the frozen reference onto the Test 2A fabric-awning contract.

    Reusing the Test 2A contract is not a convenience: the Test 1 specification
    defines case 1E as "Diagnosefall 1D, jedoch mit Stoffmarkisen-Sonnenschutz
    gemaess Diagnosetest 2 E1", so the device and its control ARE the Test 2A
    ones. ``_assert_same_device_as_test2a`` checks that the frozen product and
    threshold really are shared before this mapping is used.
    """

    ete = "en_iso_52022_3_conditions_ete"
    ref_conditions = "en_iso_52022_3_conditions_reference"
    en_410 = "en_410"
    hiver = "iso_15099_conditions_hiver"
    produit = _releve(reference, "store", "produit")
    return {
        "external_shading_activation_w_m2": _releve(
            reference, "store", "seuil_activation_w_m2"
        ),
        "variant_2A_shade": produit["type"],
        "variant_2A_combined_g_total": _deployed(reference, ete, "g_total"),
        "variant_2A_convection_factor": _deployed(
            reference, ete, "facteur_convection_gc"
        ),
        "variant_2A_thermal_radiation_factor": _deployed(
            reference, ete, "facteur_rayonnement_gth"
        ),
        "variant_2A_ventilation_factor": _deployed(
            reference, ete, "facteur_ventilation_gv"
        ),
        "variant_2A_secondary_internal_heat_transfer_factor": _deployed(
            reference, ete, "transfert_secondaire_qi"
        ),
        "variant_2A_direct_solar_transmittance": _deployed(
            reference, en_410, "transmission_solaire_directe_te"
        ),
        "variant_2A_outside_solar_reflectance": _deployed(
            reference, en_410, "reflexion_solaire_exterieure_re"
        ),
        "variant_2A_inside_solar_reflectance": _deployed(
            reference, en_410, "reflexion_solaire_interieure_re_prime"
        ),
        "variant_2A_visible_transmittance": _deployed(
            reference, en_410, "transmission_visible_tv"
        ),
        "variant_2A_outside_visible_reflectance": _deployed(
            reference, en_410, "reflexion_visible_exterieure_rv"
        ),
        "variant_2A_inside_visible_reflectance": _deployed(
            reference, en_410, "reflexion_visible_interieure_rv_prime"
        ),
        "variant_2A_uv_transmittance": _deployed(
            reference, en_410, "transmission_uv_tuv"
        ),
        "variant_2A_reference_combined_g_total": _deployed(
            reference, ref_conditions, "g_total"
        ),
        "variant_2A_reference_u_w_m2k": _deployed(
            reference, ref_conditions, "u_vitrage_w_m2k"
        ),
        "variant_2A_iso15099_winter_u_w_m2k": _deployed(
            reference, hiver, "u_vitrage_w_m2k"
        ),
        # Millimetres and centimetres in the documentation, metres in the
        # contract. Getting either factor wrong would give a shade a thousand
        # times too thick, which changes nothing visible in the JSON.
        "variant_2A_peripheral_gap_m": (
            _releve(reference, "store", "lame_d_air_cm") / 100.0
        ),
        "variant_2A_screen_layer_thickness_m": (
            _releve(reference, "store", "epaisseur_couche_mm") / 1000.0
        ),
    }


def _apply_fabric_awning(
    assets: Dict[str, Any], reference: Dict[str, Any]
) -> Dict[str, Any]:
    """Link 1E: build the source-traced awning control, and keep its reserves.

    The control contract is built here rather than blocked, because every value
    it needs is now frozen. What remains unresolved is not the device but the
    dynamics: the specification confirms the 150 W/m2 threshold and states
    neither the comparison operator, nor the release rule, nor the exact
    irradiance signal, and VE exposes separate lower and raise thresholds whose
    dynamic equivalence cannot be inferred from their names.

    Those reserves come from ``test2a_shading_control``, which enumerated them,
    and they are carried through instead of being resolved by choice. Case 1E is
    the only pass/fail case of Test 1, so guessing the release rule would move
    a real verdict.
    """

    from .test2a_shading_control import (
        DYNAMIC_EQUIVALENCE_BLOCKERS,
        build_test2a_fabric_awning_control,
    )

    _assert_same_device_as_test2a(reference)
    control = build_test2a_fabric_awning_control(
        _awning_official_inputs(reference)
    )
    payload = (
        control.to_dict() if hasattr(control, "to_dict") else dict(vars(control))
    )
    assets["metadata"]["diagnostic_fabric_awning_control"] = payload
    return {
        "id": BLOCKER_AWNING,
        "severity": "BLOCKER",
        "detail": (
            "The awning control contract for {} is built and source-traced: "
            "threshold {} W/m2, deployed-state whole-window properties from the "
            "official documentation. What blocks case 1E is the dynamics, not "
            "the device: the specification states neither the comparison "
            "operator, nor the release rule, nor the exact irradiance signal, "
            "and VE's separate lower and raise thresholds cannot be shown "
            "equivalent to it from their names alone. Unresolved reserves: {}."
            .format(
                control.device,
                control.threshold_w_m2,
                ", ".join(DYNAMIC_EQUIVALENCE_BLOCKERS),
            )
        ),
        "unresolved_reserves": list(DYNAMIC_EQUIVALENCE_BLOCKERS),
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
        record("1E", _apply_fabric_awning(assets, reference))

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
