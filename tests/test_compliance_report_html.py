"""Tests for the interactive HTML client dashboard generator.

Pure Python: exercises the real requirement matrix + alert shapes, verifies the
fail-closed status mapping (missing evidence never becomes Conforme), the
decisive global-comparison row, and that the rendered file is complete.
"""

import io
import json
import os
import unittest
from pathlib import Path

from swiss_sia.compliance_report_html import (
    STATUS_A_DETERMINER,
    STATUS_CONFORME,
    STATUS_ECART,
    STATUS_NON_CONFORME,
    STATUS_NON_VERIFIABLE,
    build_criteria,
    render_compliance_report_html,
)
from swiss_sia.compliance_verdict import (
    COMPLIANT,
    NOT_DETERMINED,
    build_compliance_verdict,
)
from swiss_sia.reference_model.sia4010.ui_translations import translate
from swiss_sia.rule_engine import Alert, Severity


def _alert(rule, severity, category="Reference Project Diagnostics"):
    return Alert(
        rule=rule,
        description="Test alert for " + rule,
        severity=severity,
        category=category,
        recommendation="Do the thing.",
    )


def _by_rule(criteria, implemented_rule_fragment):
    return [
        c
        for c in criteria
        if implemented_rule_fragment in (c["id"] + c["name"] + c["article"])
    ]


class BuildCriteriaTests(unittest.TestCase):
    def _criteria(self, alerts=(), comparison=None):
        sia3802 = {"alerts": list(alerts)}
        if comparison is not None:
            sia3802["global_reference_comparison"] = comparison
        return build_criteria(sia3802, {})

    def test_matrix_criteria_are_produced(self):
        criteria = self._criteria()
        self.assertGreater(len(criteria), 5)
        # Every criterion carries the fields the front-end needs.
        for c in criteria:
            for key in (
                "id",
                "section",
                "name",
                "type",
                "status",
                "article",
                "reference",
            ):
                self.assertIn(key, c)
            self.assertIn(
                c["status"],
                {
                    STATUS_CONFORME,
                    STATUS_NON_CONFORME,
                    STATUS_A_DETERMINER,
                    STATUS_ECART,
                    STATUS_NON_VERIFIABLE,
                },
            )

    def test_missing_evidence_is_never_conforme(self):
        """Fail-closed: a *_VALUE_MISSING alert makes its criterion Non vérifiable."""
        alerts = [_alert("SIA3802_U_VALUE_WINDOW_VALUE_MISSING", Severity.LOW)]
        window = self._window(self._criteria(alerts))
        self.assertEqual(window["status"], STATUS_NON_VERIFIABLE)
        self.assertNotEqual(window["status"], STATUS_CONFORME)

    def test_reference_diagnostic_deviation_is_ecart(self):
        alerts = [_alert("SIA3802_U_VALUE_EXTERNAL_WALL", Severity.LOW)]
        wall = self._wall(self._criteria(alerts))
        self.assertEqual(wall["status"], STATUS_ECART)
        self.assertEqual(wall["type"], "diagnostic")

    def test_blocking_alert_is_non_conforme(self):
        alerts = [
            _alert("SIA3802_U_VALUE_WINDOW", Severity.CRITICAL, category="Openings")
        ]
        window = self._window(self._criteria(alerts))
        self.assertEqual(window["status"], STATUS_NON_CONFORME)

    def test_no_alert_reference_diagnostic_is_conforme(self):
        wall = self._wall(self._criteria())
        self.assertEqual(wall["status"], STATUS_CONFORME)

    def test_global_comparison_contradiction_is_non_conforme(self):
        criteria = self._criteria(
            comparison={
                "status": "REVIEWED_RESULT_CONTRADICTS_ACCEPTANCE",
                "project_value": 42.0,
                "reference_value": 40.0,
                "source": "calc.pdf",
            }
        )
        g = self._global(criteria)
        self.assertEqual(g["status"], STATUS_NON_CONFORME)
        self.assertEqual(g["type"], "decisif")

    def test_global_comparison_reviewed_is_conforme(self):
        criteria = self._criteria(
            comparison={
                "status": "REVIEWED_RESULT_AVAILABLE",
                "project_value": 40.0,
                "reference_value": 42.0,
                "source": "calc.pdf",
            }
        )
        self.assertEqual(self._global(criteria)["status"], STATUS_CONFORME)

    def test_global_comparison_missing_is_a_determiner(self):
        self.assertEqual(self._global(self._criteria())["status"], STATUS_A_DETERMINER)

    def test_sia4010_rows_never_conforme(self):
        criteria = build_criteria(
            {"alerts": []},
            {"tests": {"test_1": {"status": "OFFICIAL_RESULTS_RECORDED"}}},
        )
        rows = [c for c in criteria if c["section"] == "sia4010"]
        self.assertTrue(rows)
        for r in rows:
            self.assertNotEqual(r["status"], STATUS_CONFORME)

    def test_client_scope_omits_sia4010_criteria_entirely(self):
        """The client 380/2 report must carry no SIA 4010 row at all."""
        sia4010 = {"tests": {"test_1": {"status": "OFFICIAL_RESULTS_RECORDED"}}}
        both = build_criteria({"alerts": []}, sia4010, scope="both")
        client = build_criteria({"alerts": []}, sia4010, scope="sia3802")
        self.assertTrue([c for c in both if c["section"] == "sia4010"])
        self.assertEqual([c for c in client if c["section"] == "sia4010"], [])
        # The decisive SIA 380/2 global comparison stays in the client scope.
        self.assertTrue(
            [c for c in client if c["id"] == "SIA3802_GLOBAL_REFERENCE_COMPARISON"]
        )

    # helpers to locate specific criteria
    def _window(self, criteria):
        return next(c for c in criteria if "Window Uw" in c["name"])

    def _wall(self, criteria):
        return next(c for c in criteria if "External wall" in c["name"])

    def _global(self, criteria):
        return next(
            c for c in criteria if c["id"] == "SIA3802_GLOBAL_REFERENCE_COMPARISON"
        )


class RenderTests(unittest.TestCase):
    @staticmethod
    def _payload(path):
        text = path.read_text(encoding="utf-8")
        marker = "window.__SIA_DATA__ = "
        start = text.index(marker) + len(marker)
        end = text.index(";\n(function()", start)
        return text, json.loads(text[start:end])

    def test_render_writes_complete_html(self):
        out = Path(__file__).with_name("_sia_dashboard_test.html")
        try:
            path = render_compliance_report_html(
                out,
                project_label="Demo Project",
                rooms_data=[],
                sia3802_results={
                    "alerts": [],
                    "global_reference_comparison": {"status": "NOT_CHECKABLE"},
                },
                sia4010_results={"tests": {"test_1": {"status": "EVIDENCE_INCOMPLETE"}}},
                language="fr",
                model_name="Demo.mit",
            )
            text = path.read_text(encoding="utf-8")
            # No template token survives.
            self.assertNotIn("__DATA_JSON__", text)
            self.assertNotIn("__PAGE_TITLE__", text)
            # Payload injected and parseable.
            self.assertIn("window.__SIA_DATA__", text)
            self.assertIn("Navigateur de conformit", text)
            # Payload is valid JSON and carries criteria.
            marker = "window.__SIA_DATA__ = "
            start = text.index(marker) + len(marker)
            end = text.index(";\n(function()", start)
            payload = json.loads(text[start:end])
            self.assertGreater(len(payload["criteria"]), 5)
            governance = payload["meta"]["governance"]
            self.assertEqual(len(governance["findings"]), 7)
            self.assertEqual(governance["overall_status"], "BLOCKED")
            self.assertIn("évaluation", governance["legal_wording"])
            # The scope clause / not-a-certificate framing is present.
            self.assertIn("certificat", text)
        finally:
            out.unlink(missing_ok=True)

    def test_sia3802_scope_ignores_sia4010_attestation_ceiling_in_banner(self):
        sia3802 = {
            "envelope": {},
            "openings": {},
            "ventilation": {},
            "gains": {},
            "setpoints": {},
            "hvac": {},
            "alerts": [],
            "global_reference_comparison": {"status": "REVIEWED_RESULT_AVAILABLE"},
        }
        sia4010 = {
            "tests": {"test_1": {"status": "OFFICIAL_RESULTS_RECORDED"}},
            "validation_class": "1A",
            "class_readiness": {"1A": {}},
        }
        verdict = build_compliance_verdict(sia3802, sia4010, rooms_analysed=1)
        self.assertEqual(verdict.sia3802_status, COMPLIANT)
        self.assertEqual(verdict.sia4010_status, NOT_DETERMINED)
        self.assertEqual(verdict.overall_status, NOT_DETERMINED)

        scoped_out = Path(__file__).with_name("_sia_dashboard_sia3802.html")
        combined_out = Path(__file__).with_name("_sia_dashboard_both.html")
        try:
            render_compliance_report_html(
                scoped_out,
                project_label="Demo Project",
                rooms_data=[object()],
                sia3802_results=sia3802,
                sia4010_results=sia4010,
                language="fr",
                model_name="Demo.mit",
                generated_at="2026-08-18 12:00",
                scope="sia3802",
            )
            _, scoped_payload = self._payload(scoped_out)
            self.assertEqual(scoped_payload["meta"]["verdict"]["tone"], "ok")
            self.assertIn(
                translate("verdict_compliant", "fr"),
                scoped_payload["meta"]["verdict"]["title"],
            )
            self.assertIn(
                translate("sia4010_readiness_attestation_required", "fr"),
                scoped_payload["meta"]["verdict"]["detail"],
            )
            render_compliance_report_html(
                combined_out,
                project_label="Demo Project",
                rooms_data=[object()],
                sia3802_results=sia3802,
                sia4010_results=sia4010,
                language="fr",
                model_name="Demo.mit",
                generated_at="2026-08-18 12:00",
                scope="both",
            )
            _, combined_payload = self._payload(combined_out)
            self.assertEqual(combined_payload["meta"]["verdict"]["tone"], "warn")
            self.assertIn(
                translate("verdict_not_determined", "fr"),
                combined_payload["meta"]["verdict"]["title"],
            )
            self.assertEqual(
                scoped_payload["meta"]["ui"]["scope"],
                combined_payload["meta"]["ui"]["scope"],
            )
        finally:
            scoped_out.unlink(missing_ok=True)
            combined_out.unlink(missing_ok=True)

    def test_client_scope_drops_the_sia4010_section_from_the_order(self):
        scoped_out = Path(__file__).with_name("_sia_dashboard_sect_client.html")
        combined_out = Path(__file__).with_name("_sia_dashboard_sect_both.html")
        base = {"alerts": [], "global_reference_comparison": {"status": "NOT_CHECKABLE"}}
        sia4010 = {"tests": {"test_1": {"status": "EVIDENCE_INCOMPLETE"}}}
        try:
            render_compliance_report_html(
                scoped_out,
                project_label="Demo",
                rooms_data=[],
                sia3802_results=base,
                sia4010_results=sia4010,
                language="fr",
                model_name="Demo.mit",
                scope="sia3802",
            )
            render_compliance_report_html(
                combined_out,
                project_label="Demo",
                rooms_data=[],
                sia3802_results=base,
                sia4010_results=sia4010,
                language="fr",
                model_name="Demo.mit",
                scope="both",
            )
            _, scoped = self._payload(scoped_out)
            _, combined = self._payload(combined_out)
            self.assertNotIn("sia4010", scoped["meta"]["sectionOrder"])
            self.assertIn("sia4010", combined["meta"]["sectionOrder"])
        finally:
            scoped_out.unlink(missing_ok=True)
            combined_out.unlink(missing_ok=True)

    def test_outstanding_panel_names_the_missing_global_comparison(self):
        out = Path(__file__).with_name("_sia_dashboard_outstanding.html")
        try:
            render_compliance_report_html(
                out,
                project_label="Demo",
                rooms_data=[object()],
                sia3802_results={
                    "envelope": {},
                    "openings": {},
                    "ventilation": {},
                    "gains": {},
                    "setpoints": {},
                    "hvac": {},
                    "alerts": [],
                    "global_reference_comparison": {"status": "NOT_CHECKABLE"},
                },
                sia4010_results={},
                language="fr",
                model_name="Demo.mit",
                scope="sia3802",
            )
            _, payload = self._payload(out)
            outstanding = payload["meta"]["outstanding"]
            self.assertTrue(outstanding)
            self.assertTrue(
                any("7.2.5.2" in item["label"] for item in outstanding),
                outstanding,
            )
        finally:
            out.unlink(missing_ok=True)

    def test_outstanding_panel_is_empty_when_sia3802_is_compliant(self):
        out = Path(__file__).with_name("_sia_dashboard_clear.html")
        sia3802 = {
            "envelope": {},
            "openings": {},
            "ventilation": {},
            "gains": {},
            "setpoints": {},
            "hvac": {},
            "dynamic": {},
            "alerts": [],
            "global_reference_comparison": {"status": "REVIEWED_RESULT_AVAILABLE"},
        }
        try:
            render_compliance_report_html(
                out,
                project_label="Demo",
                rooms_data=[object()],
                sia3802_results=sia3802,
                sia4010_results={},
                language="fr",
                model_name="Demo.mit",
                scope="sia3802",
            )
            _, payload = self._payload(out)
            self.assertEqual(payload["meta"]["outstanding"], [])
        finally:
            out.unlink(missing_ok=True)

    def test_unknown_report_scope_is_rejected(self):
        out = Path(__file__).with_name("_sia_dashboard_invalid_scope.html")
        try:
            with self.assertRaises(ValueError):
                render_compliance_report_html(
                    out,
                    project_label="Demo Project",
                    rooms_data=[],
                    sia3802_results={},
                    sia4010_results={},
                    scope="automatic",
                )
        finally:
            out.unlink(missing_ok=True)

    def test_no_iesve_import(self):
        for name in ("compliance_report_html.py", "compliance_report_html_template.py"):
            chemin = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "swiss_sia",
                name,
            )
            with io.open(chemin, encoding="utf-8") as f:
                for numero, ligne in enumerate(f, 1):
                    nu = ligne.strip()
                    self.assertFalse(nu.startswith("import iesve"), (name, numero))
                    self.assertFalse(nu.startswith("from iesve"), (name, numero))


if __name__ == "__main__":
    unittest.main()
