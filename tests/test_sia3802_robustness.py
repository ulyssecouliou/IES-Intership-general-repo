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


if __name__ == "__main__":
    unittest.main()
