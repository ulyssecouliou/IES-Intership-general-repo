"""Unit tests for ``ve_resume_ledger``.

The ledger has three consultation outcomes: FRESH, REUSE, FAIL_CLOSED.  It
must never let a caller silently overwrite an existing entry with a
different payload fingerprint.
"""

import json
import os
import unittest
from tempfile import TemporaryDirectory

from swiss_sia.reference_model.ve_resume_ledger import (
    LEDGER_SCHEMA_VERSION,
    ResumeLedger,
    ReuseDecision,
    compute_fingerprint,
)


def _fake_clock(stamp="2026-08-11T00:00:00+00:00"):
    def _now():
        return stamp

    return _now


class ResumeLedgerTests(unittest.TestCase):

    def test_fresh_ledger_returns_fresh_decision(self) -> None:
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ledger.json")
            ledger = ResumeLedger(path, project_id="proj_A", clock=_fake_clock())
            consult = ledger.consult("materials", {"foo": 1})
            self.assertEqual(consult.decision, ReuseDecision.FRESH)
            self.assertIsNone(consult.recorded_entry)

    def test_record_then_consult_same_payload_reuses(self) -> None:
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ledger.json")
            ledger = ResumeLedger(path, project_id="proj_A", clock=_fake_clock())
            payload = {"materials": [{"key": "M_INS"}]}
            ledger.record("materials", payload)
            consult = ledger.consult("materials", payload)
            self.assertEqual(consult.decision, ReuseDecision.REUSE)
            self.assertIsNotNone(consult.recorded_entry)

    def test_record_then_consult_different_payload_is_fail_closed(self) -> None:
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ledger.json")
            ledger = ResumeLedger(path, project_id="proj_A", clock=_fake_clock())
            ledger.record("materials", {"key": "M_INS", "thickness": 0.1})
            consult = ledger.consult("materials", {"key": "M_INS", "thickness": 0.2})
            self.assertEqual(consult.decision, ReuseDecision.FAIL_CLOSED)
            self.assertIn("recorded_fingerprint", consult.mismatch_summary)
            self.assertIn("requested_fingerprint", consult.mismatch_summary)

    def test_record_refuses_silent_overwrite(self) -> None:
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ledger.json")
            ledger = ResumeLedger(path, project_id="proj_A", clock=_fake_clock())
            ledger.record("materials", {"key": "M_INS"})
            with self.assertRaises(ValueError):
                ledger.record("materials", {"key": "M_INS", "extra": 1})

    def test_discard_requires_reason_and_removes_entry(self) -> None:
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ledger.json")
            ledger = ResumeLedger(path, project_id="proj_A", clock=_fake_clock())
            ledger.record("materials", {"key": "M_INS"})
            with self.assertRaises(ValueError):
                ledger.discard("materials", reason="   ")
            removed = ledger.discard("materials", reason="operator restart on 2026-08-11")
            self.assertIsNotNone(removed)
            consult = ledger.consult("materials", {"key": "M_INS"})
            self.assertEqual(consult.decision, ReuseDecision.FRESH)

    def test_ledger_persists_across_instances(self) -> None:
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ledger.json")
            first = ResumeLedger(path, project_id="proj_A", clock=_fake_clock())
            first.record("materials", {"key": "M_INS"})
            second = ResumeLedger(path, project_id="proj_A", clock=_fake_clock())
            consult = second.consult("materials", {"key": "M_INS"})
            self.assertEqual(consult.decision, ReuseDecision.REUSE)

    def test_ledger_rejects_project_mismatch(self) -> None:
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ledger.json")
            first = ResumeLedger(path, project_id="proj_A", clock=_fake_clock())
            first.record("materials", {"key": "M_INS"})
            wrong = ResumeLedger(path, project_id="proj_B", clock=_fake_clock())
            with self.assertRaises(ValueError):
                wrong.load()

    def test_ledger_rejects_wrong_schema_version(self) -> None:
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ledger.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(
                    {
                        "schema_version": "0.9",
                        "project_id": "proj_A",
                        "entries": [],
                    },
                    handle,
                )
            ledger = ResumeLedger(path, project_id="proj_A", clock=_fake_clock())
            with self.assertRaises(ValueError):
                ledger.load()

    def test_compute_fingerprint_is_deterministic(self) -> None:
        a = compute_fingerprint({"b": 2, "a": [1, {"x": 0.5}]})
        b = compute_fingerprint({"a": [1, {"x": 0.5}], "b": 2})
        self.assertEqual(a, b)

    def test_ledger_file_carries_expected_schema(self) -> None:
        with TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "ledger.json")
            ledger = ResumeLedger(path, project_id="proj_A", clock=_fake_clock())
            ledger.record("materials", {"key": "M_INS"})
            with open(path, "r", encoding="utf-8") as handle:
                content = json.load(handle)
            self.assertEqual(content["schema_version"], LEDGER_SCHEMA_VERSION)
            self.assertEqual(content["project_id"], "proj_A")
            self.assertEqual(len(content["entries"]), 1)


if __name__ == "__main__":
    unittest.main()
