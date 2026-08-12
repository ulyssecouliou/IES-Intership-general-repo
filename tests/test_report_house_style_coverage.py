"""Guard the sheets already converted to the IES house style, and ratchet down.

The workbook generator carried 285 colour literals in its own palette, so a
client opening the report met a second visual identity next to the PDF and the
in-VE interface. The conversion is incremental: the sheets a manager or a client
opens first are done, the deep data sheets are not.

Two things are worth testing rather than trusting. A converted sheet must not
quietly acquire a new literal, and the total must not grow while the conversion
is unfinished. The ratchet below is deliberately an inequality: it lets the next
pass lower the number without editing the test, and fails the moment a change
raises it.
"""

from __future__ import annotations

import ast
import re
import unittest
from pathlib import Path

from swiss_sia import report_style
from ui import design


ROOT = Path(__file__).resolve().parents[1]
GENERATOR = ROOT / "swiss_sia" / "excel_report.py"

HEX_LITERAL = re.compile(r"#[0-9A-Fa-f]{6}")
WORKSHEET_CALL = re.compile(r"add_worksheet\(\"([A-Z0-9 /]+)\"\)")

#: Sheets whose builders are fully on the house style. Extend as passes land.
CONVERTED_SHEETS = (
    "COVER",
    "INDEX",
    "MANAGER DASHBOARD",
    "ACTION DASHBOARD",
    "CLIENT SUMMARY",
    "PREFLIGHT",
    "P1 REMEDIATION",
)

#: Literals left in the unconverted sheet builders on 2026-08-12. This number
#: may only ever go down.
REMAINING_LITERAL_BUDGET = 193


def _source() -> str:
    return GENERATOR.read_text(encoding="utf-8")


def _builders_by_sheet(source: str) -> dict:
    """Map each sheet name to the source of the function that writes it."""

    tree = ast.parse(source)
    builders = {}
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        segment = ast.get_source_segment(source, node) or ""
        for name in WORKSHEET_CALL.findall(segment):
            builders[name] = segment
    return builders


class HouseStyleCoverageTests(unittest.TestCase):

    def setUp(self) -> None:
        self.source = _source()
        self.builders = _builders_by_sheet(self.source)

    def test_the_converted_sheets_are_all_present(self) -> None:
        for name in CONVERTED_SHEETS:
            with self.subTest(sheet=name):
                self.assertIn(name, self.builders)

    def test_a_converted_sheet_holds_no_colour_literal(self) -> None:
        offenders = {}
        for name in CONVERTED_SHEETS:
            found = sorted(set(HEX_LITERAL.findall(self.builders[name])))
            if found:
                offenders[name] = found
        self.assertEqual(
            offenders,
            {},
            "These converted sheets grew colour literals again; route them "
            "through swiss_sia.report_style instead: {}".format(offenders),
        )

    def test_the_literal_count_never_grows(self) -> None:
        remaining = len(HEX_LITERAL.findall(self.source))
        self.assertLessEqual(
            remaining,
            REMAINING_LITERAL_BUDGET,
            "The workbook gained colour literals ({} > {}). Use "
            "swiss_sia.report_style for new formats.".format(
                remaining, REMAINING_LITERAL_BUDGET
            ),
        )

    def test_only_finalize_colours_a_tab(self) -> None:
        """Fifteen builders set a tab colour that finalize then overwrote.

        Nine of them used an off-palette literal, and none of the fifteen had
        any effect: finalize runs afterwards and colours every sheet it knows.
        """

        builders_setting_colour = sorted(
            name
            for name, segment in self.builders.items()
            if "set_tab_color(" in segment
        )
        self.assertEqual(builders_setting_colour, [])
        self.assertIn("set_tab_color(", self.source)

    def test_every_section_tab_colour_is_a_house_token(self) -> None:
        tokens = {
            token.upper()
            for name, token in vars(design).items()
            if isinstance(token, str)
            and name.isupper()
            and HEX_LITERAL.fullmatch(token)
        }
        for section, colour in report_style.XW_SECTION_TAB_COLORS.items():
            with self.subTest(section=section):
                self.assertIn(colour.upper(), tokens)

    def test_every_severity_fill_is_a_house_token(self) -> None:
        tokens = {
            token.upper()
            for name, token in vars(design).items()
            if isinstance(token, str)
            and name.isupper()
            and HEX_LITERAL.fullmatch(token)
        }
        for severity, colour in report_style.XW_SEVERITY_FILLS.items():
            with self.subTest(severity=severity):
                self.assertIn(colour.upper(), tokens)

    def test_the_section_map_covers_the_workbook_sections(self) -> None:
        """A section absent from the map would raise at import, not at runtime."""

        from swiss_sia.excel_report import ExcelReportGenerator

        declared = [
            section
            for section, _colour, _sheets
            in ExcelReportGenerator._REPORT_SECTIONS
        ]
        self.assertEqual(
            sorted(declared), sorted(report_style.XW_SECTION_TAB_COLORS)
        )

    def test_a_table_link_is_not_marked_by_colour_alone(self) -> None:
        self.assertTrue(report_style.xw_table_link().get("underline"))

    def test_the_shared_roles_left_the_normative_config(self) -> None:
        """Presentation does not belong in swiss_sia/config.py."""

        from swiss_sia import config

        self.assertFalse(hasattr(config, "EXCEL_FORMATS"))
        self.assertEqual(
            sorted(report_style.xw_shared_roles()),
            [
                "critical",
                "fail",
                "header",
                "pass",
                "score",
                "subheader",
                "warning",
            ],
        )

    def test_critical_escalates_fail_by_inversion_not_by_a_new_hue(self) -> None:
        roles = report_style.xw_shared_roles()
        failed = report_style.status_presentation("fail")
        self.assertEqual(
            roles["critical"]["bg_color"], report_style.xw_hex(failed.text)
        )
        self.assertNotEqual(
            roles["critical"]["bg_color"], roles["fail"]["bg_color"]
        )

    def test_every_shared_role_clears_wcag_aa(self) -> None:
        """A verdict a reader cannot read is not a verdict."""

        for role, spec in report_style.xw_shared_roles().items():
            background = spec.get("bg_color")
            if background is None:
                continue
            with self.subTest(role=role):
                # The emitted values are already #RRGGBB, which the contrast
                # helpers parse; a token lookup would miss the status grounds,
                # which live in a dict rather than in module constants.
                foreground = spec["font_color"]
                large = float(spec.get("font_size", 0)) >= 14
                self.assertTrue(
                    report_style.meets_aa(
                        foreground, background, large=large
                    ),
                    "{} measures {:.2f}:1".format(
                        role,
                        report_style.contrast_ratio(foreground, background),
                    ),
                )


if __name__ == "__main__":
    unittest.main()
