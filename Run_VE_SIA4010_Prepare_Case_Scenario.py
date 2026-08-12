"""Prepare the scenario one runtime-capability probe needs, without mutating VE.

The Test 3 and Tests 4-7 runtime-capability probes refuse to run until the
active VE project carries a validated ``sia_model_scenario.json`` for one exact
official case::

    ConfigurationError: Prepare one official Test 3 case first; missing
    scenario: ...\\sia_model_scenario.json

Until now the only route that wrote that file for a Test 3 or Tests 4-7 case
was the Tkinter Model Builder window; the two scripted writers
(``Run_VE_SIA4010_Test1_Fast_Start`` and ``Run_VE_SIA4010_Case600_One_Click``)
are hard-wired to Test 1.  This launcher closes that gap.

What it does, and only this:

* resolves the active, saved VE project,
* runs ``ModelBuilderController.prepare_case_bundle`` for the exact case, which
  verifies the official bundle and records a checksum-traced preparation
  receipt,
* writes and re-validates ``sia_model_scenario.json`` in ``PREPARE_ONLY`` mode.

``PREPARE_ONLY`` is the mode ``ModelScenario`` accepts while blockers remain
(``model_scenario.py`` line 283); no VE object is created, assigned or changed
by this script.  Preparation succeeding with blockers is the expected outcome
while the delegated external inputs are still missing: the receipt then reports
``PREPARED_WITH_BLOCKERS``, which is enough for a *read-only capability probe*
and is not a validation claim of any kind.

Operator steps inside VEScripts (VE 2025):

1. set ``CASE`` below to the exact case you want to probe,
2. open and save the VE project you want to inspect,
3. run this launcher,
4. run the probe named on the last printed line.

This launcher never overwrites a scenario that belongs to a different case
unless ``ALLOW_SCENARIO_REPLACEMENT`` is set to ``True`` deliberately.
"""

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Exact case identifier.  Both probes derive the variant from the case the same
# way -- Test 3 asserts ``scenario.case_id == scenario.variant[5:]``
# (``test3_runtime_capability.py`` line 469) and every pair in
# ``hvac_plant_runtime_capability.EXACT_CASES`` reads ``("test_<case>",
# "<case>")`` -- so the variant below is derived, never guessed.
CASE = "3A"

# Empty means: derive the class deterministically from the published class/test
# matrix.  Set it explicitly to prepare the case under another required class.
TARGET_CLASS = ""

# Safety gate.  Leave False so a scenario belonging to another case is reported
# instead of being silently replaced.
ALLOW_SCENARIO_REPLACEMENT = False

SCENARIO_FILENAME = "sia_model_scenario.json"

# Which probe consumes which prepared case.  Taken from the probes themselves.
_PROBE_BY_BASE_TEST = {
    "2": "Run_VE_SIA4010_Test2A_Runtime_Capability_Probe.py",
    "3": "Run_VE_SIA4010_Test3_Runtime_Capability_Probe.py",
    "4": "Run_VE_SIA4010_Tests4_7_Runtime_Capability_Probe.py",
    "5": "Run_VE_SIA4010_Tests4_7_Runtime_Capability_Probe.py",
    "6": "Run_VE_SIA4010_Tests4_7_Runtime_Capability_Probe.py",
    "7": "Run_VE_SIA4010_Tests4_7_Runtime_Capability_Probe.py",
}


def _reload_reference_model_package():
    """Drop cached project modules before rebuilding project-local inputs.

    VEScripts keeps one Python interpreter alive between Run-button presses.
    Removing only this repository package makes corrected bundle builders and
    schema validators load from disk, while leaving the native ``iesve``
    extension and the active VE project untouched.
    """

    for module_name in tuple(sys.modules):
        if module_name == "swiss_sia.reference_model" or module_name.startswith(
            "swiss_sia.reference_model."
        ):
            del sys.modules[module_name]


#: The three project files a scenario names, and where ``prepare_case`` reads
#: them from when a receipt does not carry them.
_REPOSITORY_SCENARIO_FILES = (
    ("case_manifest_path", "sia4010_all_classes.json"),
    ("config_path", "reference_model_config.json"),
    ("asset_manifest_path", "reference_model_assets.json"),
)


def _resolve_scenario_files(receipt):
    """Return the three project files, failing closed rather than emitting "".

    ``prepare_case_bundle`` does not return one shape. ``CasePreparationReceipt``
    carries these three paths, but ``Test3SourceBundleReceipt`` -- returned once
    the delegated Test 3 inputs are ready -- carries none of them. Reading them
    with a default of ``""`` would then write a scenario naming no files at all,
    and the failure would surface much later as a missing manifest. The fallback
    below is the same repository location ``prepare_case`` itself reads
    (``preparation_bundle.py``), not a guess, and a missing file stops the run.
    """

    resolved = []
    for attribute, filename in _REPOSITORY_SCENARIO_FILES:
        value = getattr(receipt, attribute, None)
        path = Path(str(value)) if value else PROJECT_ROOT / "config" / filename
        if not path.is_file():
            raise RuntimeError(
                "Scenario input does not exist: {} ({})".format(
                    path, attribute
                )
            )
        resolved.append(str(path))
    return resolved


def _resolve_target_class(variant):
    """Return one validation class that really requires this variant."""

    from swiss_sia.config import SIA4010_CLASS_TEST_MATRIX

    if str(TARGET_CLASS).strip():
        class_id = str(TARGET_CLASS).strip().upper()
        if variant not in SIA4010_CLASS_TEST_MATRIX.get(class_id, ()):  # noqa: E501
            raise RuntimeError(
                "SIA 4010 class {} does not require {}".format(
                    class_id, variant
                )
            )
        return class_id
    candidates = sorted(
        class_id
        for class_id, variants in SIA4010_CLASS_TEST_MATRIX.items()
        if variant in variants
    )
    if not candidates:
        raise RuntimeError(
            "No SIA 4010 validation class requires {}".format(variant)
        )
    return candidates[0]


def run():
    """Prepare one official case scenario in the active VE project."""

    try:
        import iesve  # type: ignore[import-not-found]
    except ImportError:
        print(
            "READY_FOR_REAL_VE_QUALIFICATION: iesve is unavailable outside "
            "VEScripts. Launch this script from inside VE 2025."
        )
        return 2

    _reload_reference_model_package()
    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.reference_model.sia4010.native_ui import (
        ModelBuilderController,
    )
    from swiss_sia.reference_model.sia4010.scenario_preflight import (
        is_temporary_ve_project,
    )

    case_id = str(CASE).strip().upper()
    variant = "test_{}".format(case_id)
    base_test_id = case_id[0]
    if base_test_id not in _PROBE_BY_BASE_TEST:
        print(
            "FAIL - no runtime-capability probe consumes case {}".format(
                case_id
            )
        )
        return 1

    project = iesve.VEProject.get_current_project()
    if project is None:
        raise RuntimeError("Open and save the VE project to probe first")
    project_path = Path(str(getattr(project, "path", "") or ""))
    if not project_path.is_dir() or is_temporary_ve_project(project_path):
        raise RuntimeError("Save the VE project before preparing a scenario")

    target_class = _resolve_target_class(variant)
    print("SIA 4010 CASE SCENARIO PREPARATION")
    print("Project: {}".format(project_path))
    print("Case: {}/{} under class {}".format(variant, case_id, target_class))

    scenario_path = project_path / SCENARIO_FILENAME
    if scenario_path.is_file():
        existing = ModelScenario.load(scenario_path)
        same_case = (existing.variant, existing.case_id) == (variant, case_id)
        if same_case:
            print(
                "Existing scenario already targets this case, rewriting it."
            )
        elif not ALLOW_SCENARIO_REPLACEMENT:
            print(
                "BLOCKED - the project already carries a scenario for {}/{}. "
                "Preparing {}/{} here would discard it. Use a separate "
                "project, or set ALLOW_SCENARIO_REPLACEMENT = True in this "
                "launcher.".format(
                    existing.variant, existing.case_id, variant, case_id
                )
            )
            return 1
        else:
            print(
                "WARNING - replacing the scenario of {}/{} as explicitly "
                "authorized.".format(existing.variant, existing.case_id)
            )

    controller = ModelBuilderController()
    # Exposing the delegated-input contract is useful but never required for a
    # read-only probe: preparation is proven to succeed without it, reporting
    # PREPARED_WITH_BLOCKERS. A failure here is therefore audited, not fatal.
    try:
        manifest_path, created = controller.ensure_external_input_manifest(
            project_path, PROJECT_ROOT
        )
        print(
            "External-input contract: {} (created={})".format(
                manifest_path.name, created
            )
        )
    except Exception as exc:
        print(
            "WARNING - delegated-input templates not exposed: {}: {}".format(
                type(exc).__name__, exc
            )
        )

    receipt = controller.prepare_case_bundle(
        project_path,
        PROJECT_ROOT,
        "SIA4010_OFFICIAL",
        target_class,
        variant,
        case_id,
    )
    if receipt is None:
        print("FAIL - no preparation receipt was produced")
        return 1
    print("Preparation status: {}".format(getattr(receipt, "status", None)))
    audit_path = getattr(receipt, "audit_path", None)
    if audit_path is not None:
        print("Preparation audit: {}".format(audit_path))

    case_manifest, ve_config, ve_assets = _resolve_scenario_files(receipt)
    payload = controller.build_payload(
        "probe_{}".format(case_id.lower()),
        "SIA4010_OFFICIAL",
        target_class,
        variant,
        case_id,
        "PREPARE_ONLY",
        case_manifest,
        ve_config,
        ve_assets,
    )
    scenario = controller.write_and_validate(project_path, payload)
    print(
        "Scenario written and re-validated: {}/{} official={}".format(
            scenario.variant, scenario.case_id, scenario.is_official
        )
    )
    print("Scenario file: {}".format(scenario_path))
    print(
        "No VE object was created, assigned or changed by this launcher. This "
        "is not a SIA 4010 validation and not an IES certification claim."
    )
    print("NEXT: run {}".format(_PROBE_BY_BASE_TEST[base_test_id]))
    return 0


if __name__ == "__main__":
    sys.exit(run())
