"""A facts file may pre-fill the Anwenderbericht, but it may never sign it.

Retyping facts that are already recorded in artifacts invites transcription
errors into a document destined for an authority, which is why the factual
sections can come from a file. The signature cannot: the Feststellungen, the
author and the date are the engineer's answer for the submission, and a JSON
file answers for nothing. The refusal is tested rather than documented.
"""

from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_anwenderbericht.py"
TEST1_FACTS = ROOT / "config" / "anwenderbericht_test1_facts.json"


def _load_script():
    spec = importlib.util.spec_from_file_location(
        "build_anwenderbericht_script", SCRIPT
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


class FactsFileTests(unittest.TestCase):

    def setUp(self) -> None:
        self.script = _load_script()

    def test_no_facts_file_means_no_facts(self) -> None:
        self.assertEqual(self.script._load_facts(None), {})

    def test_a_missing_file_is_refused_rather_than_ignored(self) -> None:
        with self.assertRaises(SystemExit):
            self.script._load_facts(ROOT / "does_not_exist.json")

    def test_comment_keys_are_dropped(self) -> None:
        facts = self.script._load_facts(TEST1_FACTS)
        self.assertNotIn("_comment", facts)
        self.assertIn("program", facts)

    def test_a_facts_file_cannot_sign(self) -> None:
        for key in self.script.FORBIDDEN_FACT_KEYS:
            with self.subTest(key=key):
                with tempfile.TemporaryDirectory() as folder:
                    path = Path(folder) / "facts.json"
                    path.write_text(
                        json.dumps({key: ["anything"]}), encoding="utf-8"
                    )
                    with self.assertRaises(SystemExit):
                        self.script._load_facts(path)

    def test_a_non_object_file_is_refused(self) -> None:
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "facts.json"
            path.write_text(json.dumps(["not", "an", "object"]), encoding="utf-8")
            with self.assertRaises(SystemExit):
                self.script._load_facts(path)


class Test1FactsContentTests(unittest.TestCase):
    """The shipped Test 1 facts must stay facts."""

    def setUp(self) -> None:
        with TEST1_FACTS.open(encoding="utf-8") as handle:
            self.facts = json.load(handle)

    def test_it_carries_no_signature_key(self) -> None:
        script = _load_script()
        for key in script.FORBIDDEN_FACT_KEYS:
            with self.subTest(key=key):
                self.assertNotIn(key, self.facts)

    def test_the_ve_version_matches_the_recorded_snapshot(self) -> None:
        """The version is read from an artifact, so it must not be edited free-hand."""

        self.assertEqual(
            self.facts["program"]["software_version"], "2025.2.0.0"
        )

    def test_the_climate_entry_denies_being_sia_2028(self) -> None:
        """Test 1 runs on ISO 52016-1 DRYCOLD; confusing it with SIA 2028 would
        misdescribe the submission to the authority."""

        climate = [
            entry
            for entry in self.facts["data_sources"]
            if "DRYCOLD" in entry
        ]
        self.assertEqual(len(climate), 1)
        self.assertIn("NOT SIA 2028", climate[0])

    def test_the_precorrection_caveat_is_present(self) -> None:
        joined = " ".join(self.facts["special_assumptions"])
        self.assertIn("baselines to requalify", joined)
        self.assertIn("600", joined)
        self.assertIn("640", joined)


if __name__ == "__main__":
    unittest.main()
