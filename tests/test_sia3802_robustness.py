"""Robustness guards for the SIA 380/2 client-model compliance path.

A client model is read live from IESVE, and the extractor degrades to empty or
``None`` rather than raising, so a real model can present a room, surface or
system this checker never anticipated.  Two failure modes must never happen, and
each is pinned below:

* one unexpected value must not crash the whole analysis and leave the user with
  no report -- the offending category fails closed, the rest still run;
* a domain the tool could not evaluate must read as NOT_DETERMINED, never as a
  compliance failure.  A false "your building fails SIA 380/2" is as dishonest as
  a false pass, and commercially worse.
"""

import logging
import unittest

from swiss_sia.compliance_verdict import build_compliance_verdict
from swiss_sia.model_analyzer import RoomData, SurfaceData
from swiss_sia.rule_engine import RuleEngine, Severity
from swiss_sia.sia380_checker import SIA3802Checker


class _UnexpectedSurface:
    """A surface shape the checker was never written to handle."""


def _checker():
    engine = RuleEngine()
    return SIA3802Checker(model_analyzer=object(), rule_engine=engine), engine


class Sia3802CategoryIsolationTests(unittest.TestCase):
    def setUp(self):
        # The category guard logs the intentional exception; keep the suite
        # output clean without hiding a real regression.
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_one_malformed_surface_does_not_crash_the_whole_analysis(self):
        checker, _engine = _checker()
        room = RoomData(id="r1", surfaces=[_UnexpectedSurface()])

        # Must not raise: before the guard, this took down check_all entirely.
        results = checker.check_all(
            rooms_data=[room], dynamic_results={}, external_mappings={}
        )

        self.assertEqual(
            results["envelope"]["status"], "RULE_EXECUTION_ERROR"
        )
        # Every other category still ran and produced its own result.
        for other in ("openings", "ventilation", "gains", "setpoints", "hvac"):
            self.assertIn(other, results)
            self.assertNotEqual(
                results[other].get("status"), "RULE_EXECUTION_ERROR", other
            )

    def test_failed_category_scores_zero_never_a_full_score(self):
        checker, _engine = _checker()
        room = RoomData(id="r1", surfaces=[_UnexpectedSurface()])
        checker.check_all(
            rooms_data=[room], dynamic_results={}, external_mappings={}
        )
        # A crashed category must never look like a clean 100.
        self.assertEqual(checker._calculate_category_score("Envelope"), 0.0)

    def test_indeterminate_alert_caps_the_category_below_the_pass_band(self):
        """Audit A2: a not-checkable input must not leave a category reading ~85.

        An indeterminate (missing / not-checkable) alert carries a heavy penalty
        and caps the category below the pass band, so the number agrees with the
        verdict marking that domain NOT_DETERMINED -- never a false 'good'."""
        checker, engine = _checker()
        engine.add_alert(
            rule="SIA3802_WINDOW_U_VALUE_MISSING",
            description="Window U-value is not available for this opening.",
            severity=Severity.LOW,
            category="Openings",
            recommendation="Expose the documented VE window U-value.",
            data=None,
        )
        score = checker._calculate_category_score("Openings")
        self.assertLessEqual(score, 60.0)  # capped: incomplete, not good
        self.assertGreater(score, 0.0)     # not a false failure either

    def test_determined_advisory_alone_stays_in_the_pass_band(self):
        """A determined (non-indeterminate) advisory only dents the score; it is
        not an unverifiable input, so it is not capped like a missing one."""
        checker, engine = _checker()
        engine.add_alert(
            rule="SIA3802_COOLING_SEER_MIN",
            description="Cooling SEER is below the SIA table band.",
            severity=Severity.LOW,
            category="HVAC",
            recommendation="Check the generator against the reference row.",
            data=None,
        )
        self.assertEqual(checker._calculate_category_score("HVAC"), 95.0)

    def test_failed_category_emits_a_fail_closed_critical_alert(self):
        checker, engine = _checker()
        room = RoomData(id="r1", surfaces=[_UnexpectedSurface()])
        checker.check_all(
            rooms_data=[room], dynamic_results={}, external_mappings={}
        )
        errors = [
            alert
            for alert in engine.alerts
            if "RULE_EXECUTION_ERROR" in str(alert.rule)
            and alert.category == "Envelope"
        ]
        self.assertTrue(errors)
        self.assertEqual(errors[0].severity, Severity.CRITICAL)
        self.assertIn("fail-closed", errors[0].description.lower())

    def test_a_clean_room_still_runs_every_category(self):
        """The guard must not swallow the normal path: no error on good data."""

        checker, _engine = _checker()
        room = RoomData(
            id="r1",
            area=20.0,
            volume=54.0,
            surfaces=[
                SurfaceData(
                    id="w1",
                    is_external=True,
                    u_value=0.18,
                    surface_type="wall",
                    area=12.0,
                )
            ],
        )
        results = checker.check_all(
            rooms_data=[room], dynamic_results={}, external_mappings={}
        )
        for category in (
            "envelope",
            "openings",
            "ventilation",
            "gains",
            "setpoints",
            "hvac",
        ):
            self.assertNotEqual(
                results[category].get("status"),
                "RULE_EXECUTION_ERROR",
                category,
            )


class Sia3802UndeterminedNotFailedTests(unittest.TestCase):
    """A domain we could not check is NOT_DETERMINED, never NOT_COMPLIANT."""

    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def test_uncheckable_domain_is_not_reported_as_non_compliant(self):
        checker, _engine = _checker()
        room = RoomData(id="r1", surfaces=[_UnexpectedSurface()])
        results = checker.check_all(
            rooms_data=[room], dynamic_results={}, external_mappings={}
        )

        verdict = build_compliance_verdict(
            results, None, rooms_analysed=1
        ).to_dict()

        envelope = next(
            item for item in verdict["domains"] if item["domain"] == "envelope"
        )
        self.assertEqual(envelope["status"], "NOT_DETERMINED")
        self.assertEqual(envelope["reason"], "evidence_incomplete")
        # And the overall SIA 380/2 status is undetermined, not a failure.
        self.assertEqual(verdict["overall_status"], "NOT_DETERMINED")

    def test_a_real_determined_violation_still_blocks(self):
        """The honesty fix must not disarm genuine failures.

        A rule that ran and found a value out of range carries no 'cannot check'
        marker, so it still counts as blocking and yields NOT_COMPLIANT.
        """

        engine = RuleEngine()
        engine.add_alert(
            rule="SIA3802_SUMMER_COMFORT_DYNAMIC",
            description="Occupied overheating hours exceed the allowance.",
            severity=Severity.HIGH,
            category="Envelope",
            recommendation="Reduce solar gains or add operable shading.",
            data=None,
        )
        results = {
            "envelope": {"status": "EVALUATED"},
            "alerts": list(engine.alerts),
            "global_reference_comparison": {"status": "NOT_CHECKABLE"},
        }
        verdict = build_compliance_verdict(
            results, None, rooms_analysed=1
        ).to_dict()
        envelope = next(
            item for item in verdict["domains"] if item["domain"] == "envelope"
        )
        self.assertEqual(envelope["status"], "NOT_COMPLIANT")
        self.assertEqual(envelope["reason"], "blocking_findings")

    def test_determined_summer_overheating_blocks_even_with_gate_satisfied(self):
        """Audit A3: the checker emits SIA3802_SUMMER_COMFORT_DYNAMIC under the
        'Dynamic Method' category. A DETERMINED overheating failure must block the
        verdict even when the decisive global comparison is satisfied; before the
        fix that HIGH rule was outside DOMAINS and silently ignored."""
        engine = RuleEngine()
        engine.add_alert(
            rule="SIA3802_SUMMER_COMFORT_DYNAMIC",
            description="Occupied overheating hours exceed the SIA allowance.",
            severity=Severity.HIGH,
            category="Dynamic Method",
            recommendation="Reduce solar gains or add operable shading.",
            data=None,
        )
        results = {
            "dynamic": {"status": "AVAILABLE"},
            "alerts": list(engine.alerts),
            # Decisive gate satisfied on purpose: a determined overheating still fails.
            "global_reference_comparison": {"status": "REVIEWED_RESULT_AVAILABLE"},
        }
        verdict = build_compliance_verdict(results, None, rooms_analysed=1).to_dict()
        dynamic = next(
            item for item in verdict["domains"] if item["domain"] == "dynamic"
        )
        self.assertEqual(dynamic["status"], "NOT_COMPLIANT")
        self.assertEqual(verdict["sia3802_status"], "NOT_COMPLIANT")

    def test_not_checkable_summer_comfort_stays_a_reserve_not_a_block(self):
        """A summer-comfort run that could not be checked (no full-year APS /
        weather mismatch) carries an indeterminate marker: it is a reserve, never
        a blocking failure."""
        engine = RuleEngine()
        engine.add_alert(
            rule="SIA3802_SUMMER_COMFORT_NOT_CHECKABLE",
            description="Full-year dynamic comfort is not checkable.",
            severity=Severity.MEDIUM,
            category="Dynamic Method",
            recommendation="Run a full-year DRY simulation with matching weather.",
            data=None,
        )
        results = {
            # All six component domains evaluated and clean, so only the dynamic
            # comfort reserve is incomplete.
            "envelope": {}, "openings": {}, "ventilation": {}, "gains": {},
            "setpoints": {}, "hvac": {},
            "dynamic": {"status": "NOT_CHECKABLE"},
            "alerts": list(engine.alerts),
            "global_reference_comparison": {"status": "REVIEWED_RESULT_AVAILABLE"},
        }
        verdict = build_compliance_verdict(results, None, rooms_analysed=1).to_dict()
        dynamic = next(
            item for item in verdict["domains"] if item["domain"] == "dynamic"
        )
        self.assertEqual(dynamic["status"], "NOT_DETERMINED")
        # A reserve does not fail the model; overall stays COMPLIANT-with-reserves.
        self.assertEqual(verdict["sia3802_status"], "COMPLIANT")


    def test_unverified_solar_protection_control_gates_the_verdict(self):
        """Audit A4: solar-protection control is an autonomous SIA 380/2 §7.1.2.2-5
        requirement. Active shading whose control is not documented must force
        NOT_DETERMINED even when the decisive gate is satisfied, not a silent
        COMPLIANT-with-reserve."""
        engine = RuleEngine()
        engine.add_alert(
            rule="SIA3802_SOLAR_PROTECTION_CONTROL_MISSING",
            description="Solar-protection control is not available for a window.",
            severity=Severity.LOW,
            category="Openings",
            recommendation="Document the solar-protection control strategy.",
            data=None,
        )
        results = {
            "envelope": {}, "openings": {}, "ventilation": {}, "gains": {},
            "setpoints": {}, "hvac": {}, "dynamic": {},
            "alerts": list(engine.alerts),
            "global_reference_comparison": {"status": "REVIEWED_RESULT_AVAILABLE"},
        }
        verdict = build_compliance_verdict(results, None, rooms_analysed=1).to_dict()
        self.assertEqual(verdict["sia3802_status"], "NOT_DETERMINED")
        self.assertEqual(
            verdict["sia3802_reason"], "solar_protection_control_incomplete"
        )
        self.assertIn("sia3802_solar_protection_control", verdict["outstanding"])


class Sia3802GlobalReferenceComparisonRobustnessTests(unittest.TestCase):
    """The reviewed project/reference gate must survive a degenerate payload.

    Unlike the seven category checks, ``_check_global_reference_comparison``
    runs outside the per-category fail-closed guard, so an unexpected shape in
    ``dynamic_results`` (a non-dict payload, or a non-dict
    ``global_reference_comparison`` value) would otherwise raise and abort the
    whole analysis. It must instead degrade to NOT_CHECKABLE -- never crash, and
    never read as a reviewed pass.
    """

    def setUp(self):
        logging.disable(logging.CRITICAL)

    def tearDown(self):
        logging.disable(logging.NOTSET)

    def _run(self, dynamic_results):
        engine = RuleEngine()
        checker = SIA3802Checker(model_analyzer=object(), rule_engine=engine)
        return checker.check_all(
            rooms_data=[], dynamic_results=dynamic_results, external_mappings={}
        )

    def test_valid_reviewed_comparison_is_still_accepted(self):
        """Success path: a complete reviewed comparison in the compliant sense
        (project value at or below the reference) is unchanged."""
        results = self._run(
            {
                "global_reference_comparison": {
                    "accepted": True,
                    "project_value_numeric": 40.0,
                    "reference_value_numeric": 42.0,
                    "source_document": "Reviewed calc.pdf",
                }
            }
        )
        comparison = results["global_reference_comparison"]
        self.assertEqual(comparison["status"], "REVIEWED_RESULT_AVAILABLE")
        self.assertEqual(comparison["project_value"], 40.0)

    def test_accepted_but_project_exceeds_reference_is_a_contradiction(self):
        """Acceptance must never override the figures. When an accepted
        comparison reports a project value ABOVE the reference (SIA 380/2:2022
        7.2.5.2 requires project <= reference), the gate must NOT read as a
        reviewed pass and must raise a discrepancy blocker."""
        results = self._run(
            {
                "global_reference_comparison": {
                    "accepted": True,
                    "project_value_numeric": 42.0,
                    "reference_value_numeric": 40.0,
                    "source_document": "Reviewed calc.pdf",
                }
            }
        )
        comparison = results["global_reference_comparison"]
        self.assertEqual(
            comparison["status"], "REVIEWED_RESULT_CONTRADICTS_ACCEPTANCE"
        )
        self.assertTrue(
            any(
                "GLOBAL_REFERENCE_DISCREPANCY" in str(alert.rule)
                for alert in results["alerts"]
            )
        )

    def test_non_dict_comparison_value_degrades_to_not_checkable(self):
        """Invalid data: a string where a comparison dict is expected."""
        results = self._run({"global_reference_comparison": "accepted"})
        self.assertEqual(
            results["global_reference_comparison"]["status"], "NOT_CHECKABLE"
        )

    def test_non_dict_dynamic_results_degrades_to_not_checkable(self):
        """Invalid data: the whole dynamic_results payload is not a dict."""
        results = self._run([1, 2, 3])
        self.assertEqual(
            results["global_reference_comparison"]["status"], "NOT_CHECKABLE"
        )

    def test_degenerate_comparison_emits_a_blocking_alert_never_a_pass(self):
        """A non-checkable comparison stays a hard blocker, not a silent pass."""
        results = self._run({"global_reference_comparison": ["not", "a", "dict"]})
        self.assertEqual(
            results["global_reference_comparison"]["status"], "NOT_CHECKABLE"
        )
        self.assertTrue(
            any(
                "GLOBAL_REFERENCE_COMPARISON_NOT_CHECKABLE" in str(alert.rule)
                for alert in results["alerts"]
            )
        )


if __name__ == "__main__":
    unittest.main()
