"""Robustness guards for the Excel report on degenerate dynamic-result data.

APS/Vista extraction can hand the report a ``dynamic_results`` payload whose
inner rows are ``None`` or otherwise malformed. The DYNAMIC RESULTS sheet reads
those rows with ``.get()``, so one bad entry must never raise and abort the
whole workbook: the offending row is dropped, every other sheet is still
produced, and a dropped row is rendered as the explicit "no readable result"
fallback -- never a silent success.

These mirror ``tests/test_sia3802_robustness.py`` for the checker: the report is
read live from data the extractor degrades rather than validates.
"""

from __future__ import annotations

import unittest
import zipfile
from pathlib import Path

from scripts.quality.fixtures import StaticModelAnalyzer, build_reference_room
from swiss_sia.excel_report import ExcelReportGenerator
from swiss_sia.health_score import HealthScoreCalculator
from swiss_sia.rule_engine import RuleEngine
from swiss_sia.sia380_checker import SIA3802Checker
from swiss_sia.sia4010_checker import SIA4010Checker


def _report_inputs():
    """Return deterministic (analyzer, score, sia3802, sia4010, rooms).

    Runs the production checkers on one clean reference room, exactly as the
    smoke test does, so the report is exercised with real normalized objects.
    """

    room = build_reference_room()
    rooms = [room]
    analyzer = StaticModelAnalyzer(rooms)
    external_mappings = {
        "sia2024_usage": {
            "accepted": [{"room_id": room.id, "sia2024_category": "FIXTURE"}]
        },
        "sia3874_lighting": {
            "accepted": [{"room_id": room.id, "sia3874_control_type": "FIXTURE"}]
        },
    }
    sia3802 = SIA3802Checker(analyzer, RuleEngine()).check_all(
        rooms_data=rooms, dynamic_results={}, external_mappings=external_mappings
    )
    sia4010 = SIA4010Checker(analyzer, RuleEngine()).check_all(rooms_data=rooms)
    score = HealthScoreCalculator().calculate_scores(sia3802, sia4010)
    return analyzer, score, sia3802, sia4010, rooms


def _generate(output_path: Path, dynamic_results):
    """Generate a workbook with the given dynamic_results and return its text."""
    analyzer, score, sia3802, sia4010, rooms = _report_inputs()
    ExcelReportGenerator(str(output_path), analyzer).generate_report(
        score,
        sia3802,
        sia4010,
        rooms_data=rooms,
        dynamic_results=dynamic_results,
    )
    with zipfile.ZipFile(output_path) as workbook:
        shared_strings = workbook.read("xl/sharedStrings.xml").decode("utf-8", "ignore")
    return shared_strings


class ExcelReportDynamicResultsRobustnessTests(unittest.TestCase):
    """The DYNAMIC RESULTS sheet must not crash on malformed inner rows."""

    def test_valid_dynamic_room_row_still_renders(self):
        """Success path: a well-formed room row reaches the sheet."""
        output_path = Path(__file__).with_name("_report_rb_valid.xlsx")
        try:
            shared_strings = _generate(
                output_path,
                {
                    "status": "AVAILABLE",
                    "rooms": [{"room_name": "ROOM_RENDER_MARKER", "room_id": "r1"}],
                    "design_power_status": "AVAILABLE",
                },
            )
            self.assertTrue(output_path.exists())
            self.assertIn("ROOM_RENDER_MARKER", shared_strings)
        finally:
            output_path.unlink(missing_ok=True)

    def test_none_and_non_dict_room_rows_do_not_crash_the_workbook(self):
        """Invalid data: None/non-dict room rows are dropped, not fatal."""
        output_path = Path(__file__).with_name("_report_rb_badrows.xlsx")
        try:
            shared_strings = _generate(
                output_path,
                {
                    "status": "AVAILABLE",
                    "rooms": [
                        {"room_name": "GOOD_ROOM"},
                        None,
                        "not-a-dict",
                        {"room_id": 2},
                    ],
                    "design_power_status": "AVAILABLE",
                },
            )
            self.assertTrue(output_path.exists())
            # The good row still rendered; the malformed rows were dropped.
            self.assertIn("GOOD_ROOM", shared_strings)
        finally:
            output_path.unlink(missing_ok=True)

    def test_malformed_skipped_aps_rows_do_not_crash_the_workbook(self):
        """Invalid data: a None entry in skipped_aps_files is not fatal."""
        output_path = Path(__file__).with_name("_report_rb_skip.xlsx")
        try:
            _generate(
                output_path,
                {
                    "status": "AVAILABLE",
                    "skipped_aps_files": [None, {"aps_file": "stale.aps"}],
                    "rooms": [],
                },
            )
            self.assertTrue(output_path.exists())
        finally:
            output_path.unlink(missing_ok=True)

    def test_non_dict_global_reference_comparison_does_not_crash(self):
        """Invalid data: a non-dict global_reference_comparison value."""
        output_path = Path(__file__).with_name("_report_rb_grc.xlsx")
        try:
            _generate(
                output_path,
                {
                    "status": "NOT_CHECKABLE",
                    "rooms": [],
                    "global_reference_comparison": "unreviewed",
                },
            )
            self.assertTrue(output_path.exists())
        finally:
            output_path.unlink(missing_ok=True)

    def test_missing_dynamic_rooms_renders_the_fallback(self):
        """Capability absent: no readable room row -> explicit fallback text."""
        output_path = Path(__file__).with_name("_report_rb_empty.xlsx")
        try:
            shared_strings = _generate(output_path, {"status": "NOT_CHECKABLE"})
            self.assertTrue(output_path.exists())
            self.assertIn("No room-level dynamic result was readable", shared_strings)
        finally:
            output_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
