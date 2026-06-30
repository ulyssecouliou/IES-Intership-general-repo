"""Release-quality validation for the Swiss SIA Compliance Checker.

This script is intentionally independent from IESVE. It checks the local
standards PDFs, the source-traced SIA configuration, the SIA 4010 evidence
guardrails, and the documentation entry points before a report or code snapshot
is shared externally.
"""

from __future__ import annotations

import importlib
import sys
import zipfile
from pathlib import Path
from typing import Any, Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


class ReleaseValidationError(RuntimeError):
    """Raised when a release-quality check fails."""


class Validator:
    """Small validation harness with readable console output."""

    def __init__(self) -> None:
        self.failures: list[str] = []
        self.warnings: list[str] = []
        self.passed = 0

    def require(self, label: str, condition: bool, detail: str = "") -> None:
        """Record a required check."""
        if condition:
            self.passed += 1
            print(f"[PASS] {label}")
            return
        message = f"{label}: {detail}" if detail else label
        self.failures.append(message)
        print(f"[FAIL] {message}")

    def warn_if(self, label: str, condition: bool, detail: str = "") -> None:
        """Record a non-blocking warning."""
        if condition:
            return
        message = f"{label}: {detail}" if detail else label
        self.warnings.append(message)
        print(f"[WARN] {message}")

    def finish(self) -> None:
        """Raise if any required check failed."""
        print()
        print(f"Release validation passed checks: {self.passed}")
        if self.warnings:
            print(f"Warnings: {len(self.warnings)}")
        if self.failures:
            print(f"Failures: {len(self.failures)}")
            for failure in self.failures:
                print(f" - {failure}")
            raise ReleaseValidationError("Release validation failed.")
        print("Release validation succeeded.")


def _load_pdf_reader() -> Any:
    """Return pypdf.PdfReader with a clear error if the package is missing."""
    try:
        return importlib.import_module("pypdf").PdfReader
    except Exception as exc:  # pragma: no cover - depends on local tooling.
        raise ReleaseValidationError(
            "pypdf is required for PDF traceability checks. Install docs/quality "
            "dependencies or run with the Codex bundled Python runtime."
        ) from exc


def _page_text(reader: Any, page_number: int) -> str:
    """Return normalized text for a 1-based PDF page number."""
    text = reader.pages[page_number - 1].extract_text() or ""
    return " ".join(text.split())


def _unique(values: Iterable[Any]) -> bool:
    """Return true when all values are unique."""
    items = list(values)
    return len(items) == len(set(items))


def check_standard_pdfs(validator: Validator) -> None:
    """Validate local standards PDF presence, page count, and key markers."""
    pdf_reader = _load_pdf_reader()
    standards_dir = PROJECT_ROOT / "references" / "standards"
    sia380_path = standards_dir / "SIA 380-2-2022 FR.pdf"
    sia4010_path = standards_dir / "SIA 4010-2023 FR.pdf"

    validator.require("SIA 380/2 PDF exists", sia380_path.exists(), str(sia380_path))
    validator.require("SIA 4010 PDF exists", sia4010_path.exists(), str(sia4010_path))
    if not sia380_path.exists() or not sia4010_path.exists():
        return

    sia380 = pdf_reader(str(sia380_path))
    sia4010 = pdf_reader(str(sia4010_path))
    validator.require("SIA 380/2 page count is 64", len(sia380.pages) == 64, str(len(sia380.pages)))
    validator.require("SIA 4010 page count is 56", len(sia4010.pages) == 56, str(len(sia4010.pages)))

    text_380_32 = _page_text(sia380, 32)
    text_380_38 = _page_text(sia380, 38)
    text_380_39 = _page_text(sia380, 39)
    text_380_46 = _page_text(sia380, 46)
    text_4010_46 = _page_text(sia4010, 46)
    text_4010_48 = _page_text(sia4010, 48)
    text_4010_52 = _page_text(sia4010, 52)

    validator.require("SIA 380/2 page 32 contains window U-value markers", "Valeur U des fen" in text_380_32 and "1,1" in text_380_32 and "0,88" in text_380_32)
    validator.require("SIA 380/2 page 38 contains EER/SEER markers", "EER" in text_380_38 and "SEER" in text_380_38)
    validator.require("SIA 380/2 page 39 contains SCOP markers", "SCOP" in text_380_39)
    validator.require("SIA 380/2 page 46 contains solar protection table", "Tableau 10" in text_380_46 and "Taux de r" in text_380_46)
    validator.require("SIA 4010 page 46 contains validation markers", "VALIDATION" in text_4010_46 and "sept tests" in text_4010_46)
    validator.require("SIA 4010 page 48 contains validation classes", "Tableau 63" in text_4010_48 and "Classes de validation" in text_4010_48)
    validator.require("SIA 4010 page 52 contains variants", "Tableau 65" in text_4010_52 and "Tableau 66" in text_4010_52)


def check_config_traceability(validator: Validator) -> None:
    """Validate source-traced constants and coverage matrices."""
    from swiss_sia import config

    validator.require("SIA 380/2 window limit", config.SIA3802_LIMIT_VALUES["window_u"] == 1.10)
    validator.require("SIA 380/2 window target", config.SIA3802_TARGET_VALUES["window_u"] == 0.88)
    validator.require("SIA 380/2 glazing g-value", config.SIA3802_LIMIT_VALUES["glazing_g_value"] == 0.50)
    validator.require("SIA 380/2 light transmittance", config.SIA3802_LIMIT_VALUES["glazing_light_transmittance"] == 0.70)
    validator.require("SIA 380/2 infiltration limit", config.SIA3802_LIMIT_VALUES["infiltration_m3_h_m2"] == 0.15)
    validator.require("SIA 380/2 external wall limit/target", config.SIA3802_LIMIT_VALUES["external_wall_u"] == 0.20 and config.SIA3802_TARGET_VALUES["external_wall_u"] == 0.14)
    validator.require("SIA 380/2 flat roof limit/target", config.SIA3802_LIMIT_VALUES["flat_roof_u"] == 0.20 and config.SIA3802_TARGET_VALUES["flat_roof_u"] == 0.14)
    validator.require("SIA 4010 has seven tests", len(config.SIA4010_VALIDATION_TESTS) == 7)
    validator.require("SIA 4010 has all validation classes", set(config.SIA4010_VALIDATION_CLASSES) == {"1A", "1B", "2A", "2B", "3", "4A", "4B", "5"})
    validator.require("SIA 4010 has five required evidence families", len(config.SIA4010_REQUIRED_EVIDENCE) == 5)

    coverage = config.SIA_DATA_COVERAGE_MATRIX
    requirement_matrix = config.SIA_COMPLIANCE_REQUIREMENT_MATRIX
    allowed_automation = {"AUTOMATED", "PARTIAL", "NOT_IMPLEMENTED", "EVIDENCE_SCAN", "READINESS_ONLY"}
    required_coverage_keys = {
        "id",
        "standard",
        "validation_scope",
        "domain",
        "criterion",
        "expected_value",
        "data_needed",
        "expected_source",
        "coverage_key",
        "automation",
        "preferred_format",
        "destination",
        "source",
        "owner",
        "next_action",
    }

    validator.require("Coverage matrix IDs are unique", _unique(item.get("id") for item in coverage))
    validator.require("Requirement matrix IDs are unique", _unique(item.get("id") for item in requirement_matrix))
    for item in coverage:
        missing = required_coverage_keys - set(item)
        validator.require(f"Coverage item {item.get('id')} has required fields", not missing, ", ".join(sorted(missing)))
        validator.require(f"Coverage item {item.get('id')} has valid automation", item.get("automation") in allowed_automation, str(item.get("automation")))
        validator.require(f"Coverage item {item.get('id')} is source traced", bool(item.get("source")), "missing source")

    for item in requirement_matrix:
        validator.require(f"Requirement item {item.get('id')} is source traced", bool(item.get("source")), "missing source")


def check_scoring_guardrails(validator: Validator) -> None:
    """Validate conservative scoring for non-checkable VE models."""
    from swiss_sia.data_extractor import VEDataExtractor
    from swiss_sia.rule_engine import RuleEngine
    from swiss_sia.sia380_checker import SIA3802Checker

    validator.require(
        "VE enum normalizer supports callable API attributes",
        VEDataExtractor._normalize_enum_name(lambda: "BodyType.room") == "room",
    )

    class FakeBody:
        type = "BodyType.room"
        subtype = "room"

        @staticmethod
        def get_id() -> str:
            return "room-1"

    class FakeModel:
        def __init__(self, model_type: str, bodies: list[Any]) -> None:
            self.model_type = model_type
            self._bodies = bodies

        def get_bodies(self, selected_only: bool = False) -> list[Any]:
            return list(self._bodies)

    class FakeProject:
        def __init__(self) -> None:
            self.models = [
                FakeModel("VEModels_NA", []),
                FakeModel("RealBuilding", [FakeBody()]),
            ]

    fake_project = FakeProject()
    fake_extractor = VEDataExtractor(fake_project)
    validator.require(
        "VE model selector prefers model with retained rooms",
        fake_extractor.model is fake_project.models[1],
    )
    fake_diagnostics = fake_extractor.get_body_extraction_diagnostics()
    validator.require(
        "VE body diagnostics report selected model index",
        fake_diagnostics.get("selected_model_index") == 1
        and fake_diagnostics.get("relevant_body_count") == 1,
    )

    class EmptyModelAnalyzer:
        """Minimal analyzer fixture that reproduces a failed VE room extraction."""

        @staticmethod
        def analyze_all_rooms() -> list[Any]:
            return []

        @staticmethod
        def calculate_wwr(room: Any) -> float:
            return 0.0

    checker = SIA3802Checker(EmptyModelAnalyzer(), RuleEngine())
    results = checker.check_all()
    score_categories = ["envelope", "openings", "ventilation", "gains", "hvac"]
    blocking_rules = {str(alert.rule) for alert in results.get("alerts", [])}

    validator.require(
        "No-room SIA 380/2 categories score zero",
        all(results.get(category, {}).get("score") == 0.0 for category in score_categories),
    )
    for rule in [
        "SIA3802_MODEL_NOT_CHECKABLE_ENVELOPE",
        "SIA3802_MODEL_NOT_CHECKABLE_OPENINGS",
        "SIA3802_MODEL_NOT_CHECKABLE_VENTILATION",
        "SIA3802_MODEL_NOT_CHECKABLE_GAINS",
        "SIA3802_MODEL_NOT_CHECKABLE_HVAC",
    ]:
        validator.require(f"No-room guard emits {rule}", rule in blocking_rules)


def check_documentation_entry_points(validator: Validator) -> None:
    """Validate manager/audit documentation entry points."""
    required_files = [
        PROJECT_ROOT / "docs" / "source" / "index.rst",
        PROJECT_ROOT / "docs" / "source" / "manager_multilingual_brief_sphinx.rst",
        PROJECT_ROOT / "docs" / "source" / "compliance_coverage_audit.rst",
        PROJECT_ROOT / "docs" / "source" / "compliance_methodology.rst",
        PROJECT_ROOT / "docs" / "README.md",
        PROJECT_ROOT / "docs" / "project" / "RELEASE_ACCEPTANCE_CHECKLIST.md",
    ]
    for path in required_files:
        validator.require(f"Documentation file exists: {path.relative_to(PROJECT_ROOT)}", path.exists())

    html_index = PROJECT_ROOT / "docs" / "build" / "html" / "en" / "index.html"
    validator.warn_if(
        "Built HTML documentation is available",
        html_index.exists(),
        "Run python docs/tools/build_docs.py --language en --builder html before a manager review.",
    )


def check_latest_excel_report(validator: Validator) -> None:
    """Run a lightweight smoke test on the newest generated Excel report."""
    reports_dir = PROJECT_ROOT / "reports"
    reports = sorted(
        reports_dir.glob("Swiss_Compliance_Report*.xlsx"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    ) if reports_dir.exists() else []
    if not reports:
        validator.warn_if(
            "Excel smoke test skipped",
            False,
            "No Swiss_Compliance_Report*.xlsx file found in reports/.",
        )
        return

    latest = reports[0]
    generator_path = PROJECT_ROOT / "swiss_sia" / "excel_report.py"
    report_is_older_than_generator = (
        generator_path.exists()
        and latest.stat().st_mtime < generator_path.stat().st_mtime
    )
    required_sheets = [
        "MANAGER DASHBOARD",
        "CLIENT SUMMARY",
        "PREFLIGHT",
        "P1 REMEDIATION",
        "ASSUMPTIONS LIMITS",
        "AUDIT LOG",
        "SIA DATA COVERAGE",
        "INPUT REQUEST",
        "SIA4010 READINESS",
        "DYNAMIC RESULTS",
    ]
    error_markers = ["#REF!", "#DIV/0!", "#VALUE!", "#NAME?", "#N/A"]
    try:
        with zipfile.ZipFile(latest) as workbook_zip:
            names = set(workbook_zip.namelist())
            workbook_xml = workbook_zip.read("xl/workbook.xml").decode("utf-8", errors="ignore")
            shared_strings = (
                workbook_zip.read("xl/sharedStrings.xml").decode("utf-8", errors="ignore")
                if "xl/sharedStrings.xml" in names
                else ""
            )
            sheet_text = workbook_xml + shared_strings
            charts = [name for name in names if name.startswith("xl/charts/chart") and name.endswith(".xml")]
            drawings = [name for name in names if name.startswith("xl/drawings/drawing") and name.endswith(".xml")]

        validator.require("Latest Excel report opens as XLSX zip", True, str(latest))
        for sheet_name in required_sheets:
            present = sheet_name in sheet_text
            if present or not report_is_older_than_generator:
                validator.require(f"Excel report contains sheet {sheet_name}", present, str(latest))
            else:
                validator.warn_if(
                    f"Excel report contains sheet {sheet_name}",
                    False,
                    f"{latest} was generated before the current workbook generator; rerun inside VE.",
                )
        validator.require("Excel report contains chart XML parts", len(charts) > 0, str(latest))
        validator.require("Excel report contains drawing XML parts", len(drawings) > 0, str(latest))
        validator.require(
            "Excel report contains no obvious formula error markers",
            not any(marker in sheet_text for marker in error_markers),
            str(latest),
        )
    except Exception as exc:
        validator.require("Latest Excel report opens as XLSX zip", False, f"{latest}: {exc}")


def main() -> int:
    """Run all release-quality checks."""
    validator = Validator()
    check_standard_pdfs(validator)
    check_config_traceability(validator)
    check_scoring_guardrails(validator)
    check_documentation_entry_points(validator)
    check_latest_excel_report(validator)
    validator.finish()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ReleaseValidationError as exc:
        print(f"[FAIL] {exc}")
        raise SystemExit(1)
