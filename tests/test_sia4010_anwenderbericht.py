"""Tests for the SIA 4010 Anwenderbericht generator.

The generator must state what was executed and never more than that. These
tests pin the two properties that matter: it reads the factual sections from
the evidence ledger, and it refuses to produce observations, an author or a
signature of its own.
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from swiss_sia.reference_model.sia4010.anwenderbericht import (
    PLACEHOLDER,
    STATUS_DRAFT,
    STATUS_READY_FOR_REVIEW,
    AnwenderberichtError,
    ProgramIdentity,
    build_anwenderbericht,
    load_case_evidence,
    render_markdown,
    write_anwenderbericht,
)


def _ledger(path: Path) -> None:
    """Write a ledger with one executed case and one never-run case."""

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": "2.0",
                "updated_at_utc": "2026-08-12T07:49:41+00:00",
                "cases": {
                    "test_1/600": {
                        "base_test_id": "1",
                        "variant": "test_1",
                        "case_id": "600",
                        "model_evidence": {
                            "status": "VERIFIED",
                            "verification_basis": "TEST1_RUNTIME_QUALIFICATION",
                        },
                        "simulation_evidence": {
                            "status": "SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION"
                        },
                        "result_evidence": {
                            "status": (
                                "REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION"
                            ),
                            "aps_path": "C:/x/Vista/SIA4010_test_1_600_2026.aps",
                            "aps_sha256": "ABC123",
                            "observed_metric_count": 88,
                            "acceptance_criterion_available": False,
                            "required_output_scope_complete": True,
                            "distribution_criterion_count": 0,
                        },
                    },
                    "test_1/900": {
                        "base_test_id": "1",
                        "variant": "test_1",
                        "case_id": "900",
                        "model_evidence": {"status": "MISSING"},
                        "simulation_evidence": {"status": "NOT_RUN"},
                        "result_evidence": {"status": "NOT_CHECKABLE"},
                    },
                    "test_2A/2A": {
                        "base_test_id": "2",
                        "variant": "test_2A",
                        "case_id": "2A",
                        "model_evidence": {"status": "MISSING"},
                        "simulation_evidence": {"status": "NOT_RUN"},
                        "result_evidence": {"status": "NOT_CHECKABLE"},
                    },
                },
            }
        ),
        encoding="utf-8",
    )


class LedgerReadingTests(unittest.TestCase):

    def test_selects_only_the_requested_base_test(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.json"
            _ledger(ledger)
            cases = load_case_evidence(str(ledger), "1")
            self.assertEqual([c.case_id for c in cases], ["600", "900"])

    def test_keeps_cases_without_evidence(self) -> None:
        """Omitting a never-run case would misrepresent the submission scope."""

        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.json"
            _ledger(ledger)
            cases = {c.case_id: c for c in load_case_evidence(str(ledger), "1")}
            self.assertTrue(cases["600"].has_recorded_result)
            self.assertFalse(cases["900"].has_recorded_result)
            self.assertEqual(cases["900"].model_status, "MISSING")

    def test_unknown_test_fails_closed(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.json"
            _ledger(ledger)
            with self.assertRaises(AnwenderberichtError):
                load_case_evidence(str(ledger), "7")

    def test_missing_ledger_fails_closed(self) -> None:
        with self.assertRaises(AnwenderberichtError):
            load_case_evidence("nowhere/at/all.json", "1")


class DraftStatusTests(unittest.TestCase):

    def _report(self, tmp: str, **kwargs):
        ledger = Path(tmp) / "ledger.json"
        _ledger(ledger)
        return build_anwenderbericht(
            str(ledger), "1", ProgramIdentity(software_name="VE"), **kwargs
        )

    def test_report_without_observations_is_a_draft(self) -> None:
        with TemporaryDirectory() as tmp:
            report = self._report(tmp)
            self.assertEqual(report.status, STATUS_DRAFT)

    def test_observations_alone_do_not_sign_the_report(self) -> None:
        with TemporaryDirectory() as tmp:
            report = self._report(tmp, observations=["Cooling deviates by 4 percent."])
            self.assertEqual(report.status, STATUS_DRAFT)
            self.assertTrue(
                any("author" in item for item in report.missing_for_signature)
            )

    def test_complete_report_awaits_signature_but_never_claims_validation(
        self,
    ) -> None:
        with TemporaryDirectory() as tmp:
            report = self._report(
                tmp,
                input_parameters=["ISO 52016-1 clause 7 test cell, case 600"],
                data_sources=["Climate: ISO 52016-1 DRYCOLD Denver"],
                observations=["Cooling deviates by 4 percent; cause under review."],
                author="Ulysse Couliou",
                report_date="2026-08-12",
            )
            self.assertEqual(report.status, STATUS_READY_FOR_REVIEW)
            self.assertEqual(report.missing_for_signature, ())
            text = render_markdown(report)
            lowered = text.lower()
            for forbidden in ("validated", "certified", "conforms", "compliant"):
                self.assertNotIn(forbidden, lowered)

    def test_blank_observations_are_not_counted(self) -> None:
        with TemporaryDirectory() as tmp:
            report = self._report(tmp, observations=["   ", ""])
            self.assertEqual(report.observations, ())
            self.assertEqual(report.status, STATUS_DRAFT)


class RenderingTests(unittest.TestCase):

    def _rendered(self, tmp: str, **kwargs) -> str:
        ledger = Path(tmp) / "ledger.json"
        _ledger(ledger)
        report = build_anwenderbericht(
            str(ledger), "1", ProgramIdentity(software_name="VE"), **kwargs
        )
        return render_markdown(report)

    def test_uses_the_official_german_labels_verbatim(self) -> None:
        with TemporaryDirectory() as tmp:
            text = self._rendered(tmp)
            for label in (
                "Wegleitung SIA 4010 / Validierung / Anwenderbericht",
                "Test Nr.",
                "Programm",
                "Eingabeparameter",
                "Daten",
                "Spezielle Annahmen",
                "Feststellungen",
            ):
                self.assertIn(label, text)

    def test_feststellungen_is_a_placeholder_when_absent(self) -> None:
        with TemporaryDirectory() as tmp:
            text = self._rendered(tmp)
            feststellungen = text.split("## Feststellungen", 1)[1]
            self.assertIn(PLACEHOLDER, feststellungen.split("---", 1)[0])

    def test_evidence_table_reports_recorded_checksum(self) -> None:
        with TemporaryDirectory() as tmp:
            text = self._rendered(tmp)
            self.assertIn("ABC123", text)
            self.assertIn("88", text)
            self.assertIn("`test_1/600`", text)

    def test_cases_without_result_are_listed_not_hidden(self) -> None:
        with TemporaryDirectory() as tmp:
            text = self._rendered(tmp)
            self.assertIn("Cases without a recorded result", text)
            self.assertIn("`test_1/900`", text)

    def test_missing_program_identity_becomes_a_placeholder(self) -> None:
        with TemporaryDirectory() as tmp:
            ledger = Path(tmp) / "ledger.json"
            _ledger(ledger)
            report = build_anwenderbericht(str(ledger), "1", ProgramIdentity())
            self.assertIn(PLACEHOLDER, render_markdown(report))

    def test_no_special_assumptions_renders_the_form_marker(self) -> None:
        with TemporaryDirectory() as tmp:
            text = self._rendered(tmp)
            section = text.split("## Spezielle Annahmen", 1)[1]
            self.assertIn("--", section.split("##", 1)[0])


class WriteTests(unittest.TestCase):

    def test_writes_markdown_and_status_json(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            ledger = tmp_path / "ledger.json"
            _ledger(ledger)
            report = build_anwenderbericht(
                str(ledger), "1", ProgramIdentity(software_name="VE")
            )
            status = write_anwenderbericht(report, str(tmp_path / "out"))
            self.assertEqual(status["status"], STATUS_DRAFT)
            self.assertFalse(status["signed"])
            self.assertFalse(status["compliance_claim_allowed"])
            self.assertEqual(status["case_count"], 2)
            self.assertEqual(status["cases_with_recorded_result"], 1)
            self.assertTrue((tmp_path / "out" / "Anwenderbericht_Test1.md").is_file())
            written = json.loads(
                (tmp_path / "out" / "Anwenderbericht_Test1.status.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(written["test_id"], "1")
            self.assertTrue(written["missing_for_signature"])


if __name__ == "__main__":
    unittest.main()
