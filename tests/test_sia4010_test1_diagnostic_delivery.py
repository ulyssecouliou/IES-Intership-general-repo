"""Tests for the Test 1 diagnostic chain 1A to 1D as a runnable generator.

Three properties matter here, and each guards against a specific way this could
go quietly wrong.

* The four cases must be *reachable*: registered with a generator, an execution
  mode and an APS evaluation path.  They were marked NOT_IMPLEMENTED while the
  bundle already built, which is a false blocker.
* They must never borrow the ISO comparison.  They run under the Zurich-Kloten
  climate, so they are not ISO cases, and ``test-1.ref.json`` holds no reference
  for them at all.  A deviation computed against the wrong object is worse than
  no deviation.
* 1E must stay out.  It is the one Test 1 case the specification judges, and its
  awning dynamics is not stated, so it must not slip into the criterion-free
  path.
"""

import importlib.util
import json
import shutil
import unittest
from pathlib import Path

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.active_case_evaluation import (
    DIAGNOSTIC_DELIVERABLE_RECORDED,
    HOURLY_DELIVERABLE_SCOPE,
    QUALIFIED_ACTIVE_CASES,
    evaluate_qualified_active_case,
)
from swiss_sia.reference_model.sia4010 import apachesim_qualification
from swiss_sia.reference_model.sia4010.case_registry import (
    TEST1_DIAGNOSTIC_CASES,
    get_case_capability,
)
from swiss_sia.reference_model.sia4010.native_ui import ModelBuilderController
from swiss_sia.reference_model.sia4010.qualified_aps import (
    QualifiedApsBindings,
    Sia4010QualifiedApsExtractor,
)

ROOT = Path(__file__).resolve().parents[1]
BINDINGS = ROOT / "config" / "sia4010_aps_bindings_ve_runtime.json"
TEMP_ROOT = ROOT / ".codex_tmp"


class _Results:
    """Half-hourly results covering one complete non-leap year."""

    results_per_day = 48

    def __init__(self, steps=17520):
        self.values = {
            "Room units heating load": [1.0] * steps,
            "Room units cooling load": [0.5] * steps,
            "Room air temperature": [20.0] * steps,
            "Comfort temperature": [22.0] * steps,
        }

    def get_variables(self):
        metadata = {
            "Room units heating load": (
                "Heating plant sensible load",
                "power",
            ),
            "Room units cooling load": (
                "Cooling plant sensible load",
                "power",
            ),
            "Room air temperature": ("Air temperature", "temperature"),
            "Comfort temperature": (
                "Dry resultant temperature",
                "temperature",
            ),
        }
        return [
            {
                "aps_varname": key,
                "display_name": value[0],
                "model_level": "z",
                "units_type": value[1],
            }
            for key, value in metadata.items()
        ]

    def get_units(self):
        return {
            "power": {
                "units_metric": {
                    "display_name": "kW",
                    "divisor": 1000.0,
                    "offset": 0.0,
                }
            },
            "temperature": {
                "units_metric": {
                    "display_name": "°C",
                    "divisor": 1.0,
                    "offset": 0.0,
                }
            },
        }

    def get_room_results(self, room_id, aps_var, vista_var, level):
        values = self.values[aps_var]
        if aps_var in {
            "Room units heating load",
            "Room units cooling load",
        }:
            return [value * 1000.0 for value in values]
        return values


class Test1DiagnosticRegistrationTests(unittest.TestCase):
    def test_four_diagnostic_cases_are_registered_as_runnable(self):
        """A bundle that builds must not be advertised as NOT_IMPLEMENTED."""

        for case_id in TEST1_DIAGNOSTIC_CASES:
            with self.subTest(case_id=case_id):
                capability = get_case_capability("test_1", case_id)
                self.assertEqual(
                    capability.generation_status,
                    "RUNTIME_QUALIFICATION_READY",
                )
                self.assertEqual(
                    capability.generator_id,
                    "test1_diagnostic_chain_probe_v1",
                )
                self.assertTrue(capability.runtime_qualification_supported)
                self.assertTrue(capability.apachesim_qualification_supported)
                self.assertIn(("test_1", case_id), QUALIFIED_ACTIVE_CASES)

    def test_diagnostic_scope_never_claims_reference_outputs_exist(self):
        """test-1.ref.json holds no reference for 1A to 1D -- zero mentions.

        So the scope value used by 600/640/900/940 would be a false claim here.
        """

        reference = json.loads(
            (ROOT / "refs" / "reference-data" / "test-1.ref.json").read_text(
                encoding="utf-8"
            )
        )
        serialized = json.dumps(reference, ensure_ascii=False)
        for case_id in TEST1_DIAGNOSTIC_CASES:
            with self.subTest(case_id=case_id):
                self.assertEqual(
                    serialized.count('"{}"'.format(case_id)),
                    0,
                    "a reference appeared for {}; the scope must change "
                    "with it".format(case_id),
                )
                capability = get_case_capability("test_1", case_id)
                self.assertEqual(
                    capability.aps_evaluation_scope,
                    HOURLY_DELIVERABLE_SCOPE,
                )
                self.assertNotEqual(
                    capability.aps_evaluation_scope,
                    "REFERENCE_OUTPUTS_IMPLEMENTED",
                )

    def test_case_1e_keeps_its_judged_scope_and_stays_unimplemented(self):
        """1E is judged against a band; its awning dynamics is still unstated."""

        capability = get_case_capability("test_1", "1E")
        self.assertEqual(capability.aps_evaluation_scope, "OFFICIAL_CRITERIA_IMPLEMENTED")
        self.assertEqual(capability.generation_status, "NOT_IMPLEMENTED")


class Test1DiagnosticDeliverableTests(unittest.TestCase):
    def setUp(self):
        self.bindings = QualifiedApsBindings.load(BINDINGS)

    def _extractor(self, steps=17520):
        return Sia4010QualifiedApsExtractor(
            _Results(steps), "R1", self.bindings, "case.aps#sha256=x"
        )

    def test_deliverable_is_two_complete_annual_hourly_power_series(self):
        """The specification asks for hourly heating and cooling power only."""

        deliverable = self._extractor().test1_diagnostic_hourly_deliverable("1A")
        self.assertIsNotNone(deliverable)
        self.assertEqual(deliverable.hour_count, 8760)
        self.assertEqual(len(deliverable.cooling_power_w), 8760)
        # 1 kW half-hourly, integrated to hourly mean watts.
        self.assertEqual(deliverable.heating_power_w[0], 1000.0)
        self.assertEqual(deliverable.cooling_power_w[0], 500.0)
        payload = deliverable.to_dict()
        self.assertEqual(payload["unit"], "W")
        self.assertEqual(payload["acceptance_criterion"], "NONE_STATED_BY_SPECIFICATION")
        self.assertFalse(payload["reference_results_available"])
        self.assertIn(
            "Jahresdatensaetze",
            payload["specification_requirement_verbatim_de"],
        )
        # Room temperatures are the deliverable of the MAIN cases, not of the
        # diagnostic ones. Adding them would widen the normative scope.
        self.assertEqual(
            sorted(payload["quantities"]),
            ["sensible_cooling_power", "sensible_heating_power"],
        )

    def test_case_1e_is_refused_on_the_criterion_free_path(self):
        with self.assertRaisesRegex(
            ConfigurationError, "judged against the reference band"
        ):
            self._extractor().test1_diagnostic_hourly_deliverable("1E")

    def test_an_iso_case_is_refused_on_the_diagnostic_path(self):
        with self.assertRaisesRegex(ConfigurationError, "unavailable for case"):
            self._extractor().test1_diagnostic_hourly_deliverable("600")

    def test_a_partial_year_is_not_delivered_as_if_it_were_whole(self):
        """An incomplete series yields nothing rather than a shorter dataset."""

        partial = self._extractor(steps=17519)
        self.assertIsNone(partial.test1_diagnostic_hourly_deliverable("1B"))


class Test1DiagnosticEvaluationTests(unittest.TestCase):
    def setUp(self):
        self.project = TEMP_ROOT / "diag_eval"
        if self.project.exists():
            shutil.rmtree(self.project)
        self.project.mkdir(parents=True)
        self.aps = self.project / "case.aps"
        self.aps.write_text("controlled aps evidence\n", encoding="utf-8")

    def tearDown(self):
        if self.project.exists():
            shutil.rmtree(self.project)

    def test_evaluation_records_the_deliverable_and_attaches_no_verdict(self):
        output = self.project / "receipt.json"
        receipt = evaluate_qualified_active_case(
            variant="test_1",
            case_id="1C",
            results_file=_Results(),
            room_id="R1",
            aps_path=self.aps,
            bundle_root=ROOT / "SIA_4010_geteilter_Link",
            bindings_path=BINDINGS,
            output_path=output,
        )
        self.assertEqual(receipt.status, DIAGNOSTIC_DELIVERABLE_RECORDED)
        self.assertFalse(receipt.acceptance_criterion_available)
        self.assertEqual(receipt.distribution_criterion_count, 0)
        # 8760 hours on each of the two required series.
        self.assertEqual(receipt.observed_metric_count, 17520)
        # No evaluation object: nothing was evaluated, and an empty one would
        # read as "evaluated, found nothing".
        self.assertIsNone(receipt.evaluation)
        self.assertIsNone(receipt.to_dict()["evaluation"])

        payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertFalse(payload["reference_results_available"])
        self.assertFalse(payload["acceptance_criterion_available"])
        self.assertFalse(payload["compliance_claim_allowed"])
        self.assertIsNone(payload["incompleteness"])
        self.assertEqual(payload["deliverable"]["hour_count"], 8760)

    def test_incomplete_year_is_not_checkable_and_says_why(self):
        output = self.project / "partial.json"
        receipt = evaluate_qualified_active_case(
            variant="test_1",
            case_id="1D",
            results_file=_Results(steps=17519),
            room_id="R1",
            aps_path=self.aps,
            bundle_root=ROOT / "SIA_4010_geteilter_Link",
            bindings_path=BINDINGS,
            output_path=output,
        )
        self.assertEqual(receipt.status, "NOT_CHECKABLE")
        self.assertFalse(receipt.required_output_scope_complete)
        payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertIsNone(payload["deliverable"])
        self.assertIn("365-day year", payload["incompleteness"])


class Test1DiagnosticLauncherTests(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location(
            "_fast_start", ROOT / "Run_VE_SIA4010_Test1_Fast_Start.py"
        )
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

        active_spec = importlib.util.spec_from_file_location(
            "_active_case",
            ROOT / "Run_VE_SIA4010_Test1_Active_Case_One_Click.py",
        )
        self.active_module = importlib.util.module_from_spec(active_spec)
        active_spec.loader.exec_module(self.active_module)

        qualifier_spec = importlib.util.spec_from_file_location(
            "_runtime_qualifier",
            ROOT / "Run_VE_SIA4010_Test1_Qualify_Runtime_Inputs.py",
        )
        self.qualifier_module = importlib.util.module_from_spec(qualifier_spec)
        qualifier_spec.loader.exec_module(self.qualifier_module)

    def test_launchers_keep_1e_on_its_guarded_template_workflow(self):
        for case_id in TEST1_DIAGNOSTIC_CASES:
            with self.subTest(case_id=case_id):
                self.assertIn(case_id, self.module.TEST1_CASES)
                self.assertIn(case_id, self.active_module.TEST1_CASES)
                self.assertIn(case_id, self.qualifier_module.TEST1_CASES)
                self.assertIn(
                    case_id,
                    apachesim_qualification.SIMULATION_QUALIFICATION_CASES,
                )
                self.assertEqual(
                    self.module._execution_mode(case_id),
                    "QUALIFY_IN_ACTIVE_VE_PROJECT",
                )
        self.assertNotIn("1E", self.module.TEST1_CASES)
        self.assertNotIn("1E", self.active_module.TEST1_CASES)
        # Test 1E shares the controlled room-runtime input qualification, but
        # remains excluded from the generic Fast Start/active-case simulation
        # launchers. Its awning model is handled by the guarded template path.
        self.assertIn("1E", self.qualifier_module.TEST1_CASES)
        self.assertNotIn("1E", apachesim_qualification.SIMULATION_QUALIFICATION_CASES)

    def test_folder_name_selection_stays_unambiguous(self):
        class _Path:
            def __init__(self, name):
                self.name = name

        cases = {
            "SIA4010_TEST1_1A_DISPOSABLE": "1A",
            "SIA4010_TEST1_1D": "1D",
            # The longest-first ordering must keep protecting the free-float
            # identifiers now that shorter names exist.
            "SIA4010_TEST1_600FF_X": "600FF",
            "SIA4010_TEST1_900FF": "900FF",
        }
        for name, expected in cases.items():
            with self.subTest(folder=name):
                self.assertEqual(self.module._select_case(_Path(name)), expected)


class Test1DiagnosticBundleTests(unittest.TestCase):
    def test_all_four_links_apply_and_only_1e_blocks(self):
        """The chain data is frozen, so 1A to 1D must build without blockers."""

        for case_id, expected_applied in (
            ("1A", ["1A"]),
            ("1B", ["1A", "1B"]),
            ("1C", ["1A", "1B", "1C"]),
            ("1D", ["1A", "1B", "1C", "1D"]),
        ):
            project = TEMP_ROOT / "diag_bundle_{}".format(case_id)
            if project.exists():
                shutil.rmtree(project)
            project.mkdir(parents=True)
            try:
                with self.subTest(case_id=case_id):
                    receipt = ModelBuilderController.prepare_supported_mvp_bundle(
                        project,
                        ROOT,
                        "SIA4010_OFFICIAL",
                        "test_1",
                        case_id,
                    )
                    self.assertEqual(
                        receipt.status,
                        "READY_FOR_PROVISIONAL_RUNTIME_QUALIFICATION",
                    )
                    audit = json.loads(receipt.audit_path.read_text(encoding="utf-8"))
                    self.assertEqual(audit["chain_applied"], expected_applied)
                    self.assertEqual(audit["chain_blocked"], [])
                    self.assertEqual(
                        audit["acceptance_criterion"],
                        "NONE_STATED_BY_SPECIFICATION",
                    )
                    self.assertFalse(audit["compliance_claim_allowed"])
            finally:
                if project.exists():
                    shutil.rmtree(project)


if __name__ == "__main__":
    unittest.main()
