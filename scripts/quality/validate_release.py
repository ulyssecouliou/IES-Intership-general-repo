"""Release-quality validation for the Swiss SIA Compliance Checker.

This script is intentionally independent from IESVE. It checks the local
standards PDFs, the source-traced SIA configuration, the SIA 4010 evidence
guardrails, the documentation entry points, and the signature state of the SIA
traceability matrices before a report or code snapshot is shared externally.

Scope and limits -- read before trusting a green run:

* This gate does NOT execute the automated test suite. The authoritative test
  gate is ``python -m pytest`` (run locally) plus the CI workflow
  (``.github/workflows/engine-tests.yml``), which runs the full suite and the
  engine purity check on every push. A green release validation is not evidence
  that the tests pass; run pytest as well before sharing a release.
* This gate does NOT sign, and does not enforce, the ``qa-auditor`` signature on
  the SIA traceability matrices. It REPORTS their signature state so an unsigned
  matrix is visible at release time instead of being silently treated as done.
"""

from __future__ import annotations

import ast
import importlib
import io
import sys
import tokenize
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
        """Initialize release validation counters."""
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


def check_manager_reference_documents(validator: Validator) -> None:
    """Validate manager-provided reference documents used as project guardrails."""
    pdf_reader = _load_pdf_reader()
    register_candidates = [
        PROJECT_ROOT / "SIA 4010 Register validierter Software_24-09-17.pdf",
        PROJECT_ROOT / "references" / "standards" / "SIA 4010 Register validierter Software_24-09-17.pdf",
        PROJECT_ROOT / "references" / "SIA 4010 Register validierter Software_24-09-17.pdf",
    ]
    register_path = next((path for path in register_candidates if path.exists()), register_candidates[0])
    navigator_path = PROJECT_ROOT / "Sia 380_2 Navigator – Executive Summary & Product Backlog.docx"

    validator.warn_if(
        "Manager SIA 4010 software register exists",
        register_path.exists(),
        "Optional manager reference not found in project root or references/standards.",
    )
    validator.require("Manager SIA 380/2 navigator backlog exists", navigator_path.exists(), str(navigator_path))

    if register_path.exists():
        register = pdf_reader(str(register_path))
        validator.require("Manager SIA 4010 register page count is 2", len(register.pages) == 2, str(len(register.pages)))
        register_text = " ".join(
            (page.extract_text() or "")
            for page in register.pages
        )
        validator.require(
            "Manager register contains validated software markers",
            "IDA-ICE" in register_text and "OpenStudio" in register_text and "Lesosai" in register_text,
        )

    if navigator_path.exists():
        try:
            with zipfile.ZipFile(navigator_path) as docx_zip:
                document_xml = docx_zip.read("word/document.xml").decode("utf-8", errors="ignore")
            validator.require(
                "Manager navigator contains expected backlog markers",
                "SIA 380/2 Navigator" in document_xml and "EPIC 10" in document_xml,
            )
        except Exception as exc:
            validator.require("Manager navigator opens as DOCX zip", False, str(exc))


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
    validator.require("SIA 4010 PDF prevalidation has seven tests", len(config.SIA4010_PDF_PREVALIDATION_TESTS) == 7)
    validator.require("SIA 4010 exact variant matrix has 24 variants", len(config.SIA4010_TEST_VARIANT_REQUIREMENTS) == 24)
    validator.require(
        "SIA 4010 exact variant matrix covers solar and lighting variants",
        {"test_2A", "test_2B", "test_2C", "test_2D", "test_3A", "test_3L"}
        <= set(config.SIA4010_TEST_VARIANT_REQUIREMENTS),
    )
    validator.require("SIA 4010 grouped prevalidation aliases map to base tests", set(config.SIA4010_TEST_ALIAS_ORDER) <= set(config.SIA4010_TEST_ALIAS_TO_BASE_TEST))
    validator.require("SIA 4010 register has manager software entries", len(config.SIA4010_VALIDATED_SOFTWARE_REGISTER) == 4)
    validator.require("IESVE manager-register guardrail is conservative", config.SIA4010_IESVE_REGISTER_STATUS["listed_in_manager_register"] is False)
    validator.require("SIA navigator backlog has ten epics", len(config.SIA3802_NAVIGATOR_BACKLOG) == 10)
    validator.require("SIA 4010 has five required evidence families", len(config.SIA4010_REQUIRED_EVIDENCE) == 5)
    validator.require("SIA 4010 evidence requirements cover five families", len(config.SIA4010_EVIDENCE_REQUIREMENTS) == 5)
    validator.require("SIA 4010 evidence manifest prefixes are configured", bool(config.SIA4010_EVIDENCE_MANIFEST_PREFIXES))
    validator.require(
        "SIA 4010 evidence manifest required columns include review metadata",
        {"provided_file_name", "source_authority", "tests_covered", "reviewer", "review_status"}
        <= set(config.SIA4010_EVIDENCE_MANIFEST_REQUIRED_COLUMNS),
    )
    validator.require("SIA 4010 evidence manifest accepted statuses are configured", bool(config.SIA4010_EVIDENCE_MANIFEST_ACCEPTED_REVIEW_STATUSES))
    validator.require("SIA 4010 class manifest prefixes are configured", bool(config.SIA4010_CLASS_MANIFEST_PREFIXES))
    validator.require(
        "SIA 4010 class manifest required columns include reviewer/source metadata",
        {"validation_class", "selected", "reviewer", "review_status", "source_authority", "source_reference"}
        <= set(config.SIA4010_CLASS_MANIFEST_REQUIRED_COLUMNS),
    )
    validator.require("SIA 4010 class manifest accepted statuses are configured", bool(config.SIA4010_CLASS_MANIFEST_ACCEPTED_REVIEW_STATUSES))
    validator.require("SIA 4010 official test-result prefixes are configured", bool(config.SIA4010_OFFICIAL_TEST_RESULTS_PREFIXES))
    validator.require(
        "SIA 4010 official test-result columns include comparison metadata",
        {"test_id", "status", "reference_file", "candidate_file", "reviewer", "review_date", "source_authority", "source_reference"}
        <= set(config.SIA4010_OFFICIAL_TEST_RESULTS_REQUIRED_COLUMNS),
    )
    validator.require("SIA 4010 official PASS statuses are configured", bool(config.SIA4010_OFFICIAL_TEST_RESULT_PASS_STATUSES))
    validator.require("SIA 4010 official FAIL statuses are configured", bool(config.SIA4010_OFFICIAL_TEST_RESULT_FAIL_STATUSES))
    for key, requirement in config.SIA4010_EVIDENCE_REQUIREMENTS.items():
        validator.require(f"SIA 4010 evidence requirement {key} has a label", bool(requirement.get("label")))
        validator.require(f"SIA 4010 evidence requirement {key} has strict prefixes", bool(requirement.get("required_prefixes")))
        validator.require(f"SIA 4010 evidence requirement {key} has accepted extensions", bool(requirement.get("accepted_extensions")))
        validator.require(f"SIA 4010 evidence requirement {key} has an example filename", bool(requirement.get("example_filename")))
    for class_name in config.SIA4010_VALIDATION_CLASSES:
        aliases = [
            alias for alias in config.SIA4010_TEST_ALIAS_ORDER
            if class_name in config.SIA4010_TEST_CLASS_COVERAGE.get(alias, [])
        ]
        validator.require(f"SIA 4010 class {class_name} has required test aliases", bool(aliases))

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
    from types import SimpleNamespace

    from swiss_sia.data_extractor import VEDataExtractor
    from swiss_sia.evidence_bootstrap import prepare_evidence_folder
    from swiss_sia.evidence_pack import (
        create_evidence_pack,
        matches_active_project_scope,
    )
    from swiss_sia.excel_report import ExcelReportGenerator
    from swiss_sia.rule_engine import RuleEngine
    from swiss_sia.sia380_checker import SIA3802Checker
    from swiss_sia.sia4010_checker import SIA4010Checker
    from swiss_sia.simulation_results import (
        convert_aps_series_to_metric,
        normalize_co2_series_to_ppm,
    )
    from swiss_sia.sia4010_prevalidation import build_sia4010_pdf_prevalidation
    from swiss_sia.value_integrity import add_value_integrity_alerts
    from swiss_sia.config import SIA4010_EVIDENCE_REQUIREMENTS, SIA4010_REQUIRED_EVIDENCE

    validator.require(
        "VE enum normalizer supports callable API attributes",
        VEDataExtractor._normalize_enum_name(lambda: "BodyType.room") == "room",
    )

    class FakeBody:
        """Minimal VE body fixture used to validate model selection."""

        type = "BodyType.room"
        subtype = "room"

        @staticmethod
        def get_id() -> str:
            """Return a stable room fixture identifier."""
            return "room-1"

    class FakeModel:
        """Minimal VE model fixture exposing the ``get_bodies`` API."""

        def __init__(self, model_type: str, bodies: list[Any]) -> None:
            """Store the model type and mock body collection."""
            self.model_type = model_type
            self._bodies = bodies

        def get_bodies(self, selected_only: bool = False) -> list[Any]:
            """Return mock bodies while accepting the VE selected-only flag."""
            return list(self._bodies)

    class FakeProject:
        """Minimal VE project fixture with competing model candidates."""

        def __init__(self) -> None:
            """Create a documented real model and a larger secondary model."""
            self.models = [
                FakeModel("RealBuilding", [FakeBody()]),
                FakeModel("Secondary", [FakeBody(), FakeBody()]),
            ]

    fake_project = FakeProject()
    fake_extractor = VEDataExtractor(fake_project)
    validator.require(
        "VE model selector uses the strongest relevant room-body evidence",
        fake_extractor.model is fake_project.models[1],
    )
    fake_diagnostics = fake_extractor.get_body_extraction_diagnostics()
    validator.require(
        "VE body diagnostics report selected model index",
        fake_diagnostics.get("selected_model_index") == 1
        and fake_diagnostics.get("relevant_body_count") == 2,
    )
    converted_power = convert_aps_series_to_metric(
        [3_406_347.65625],
        ("COOL", "Cooling load", "z", "W", 1000.0, 0.0),
    )
    validator.require(
        "APS metric divisor is applied before energy and peak calculations",
        converted_power == [3406.34765625],
    )
    claimed_ppm, claimed_ppm_note = normalize_co2_series_to_ppm(
        [0.0004],
        "Room CO2 concentration [unit=ppm]",
    )
    validator.require(
        "APS implausible tiny CO2 values are corrected despite a ppm display label",
        len(claimed_ppm) == 1
        and abs(claimed_ppm[0] - 400.0) < 1e-9
        and claimed_ppm_note == "converted from fraction to ppm",
    )
    validator.require(
        "Evidence helper project matching rejects overlapping project names",
        matches_active_project_scope(
            Path("SIA3802_project_metadata_Demo_Project.csv"),
            "Demo_Project",
        )
        and not matches_active_project_scope(
            Path("SIA3802_project_metadata_Demo_Project_10.csv"),
            "Demo_Project",
        ),
    )

    class EmptyModelAnalyzer:
        """Minimal analyzer fixture that reproduces a failed VE room extraction."""

        @staticmethod
        def analyze_all_rooms() -> list[Any]:
            """Return no rooms to exercise conservative not-checkable scoring."""
            return []

        @staticmethod
        def calculate_wwr(room: Any) -> float:
            """Return a neutral WWR value for the empty analyzer fixture."""
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

    en410_audit = VEDataExtractor._extract_g_value_audit({
        "g_value": 0.75,
        "g_values": {"bs_en_410": 0.47, "building_regulations": 0.62},
    })
    validator.require(
        "SIA g-value selector prefers documented EN 410 g_perp",
        en410_audit.get("selected_sia_g_value") == 0.47
        and en410_audit.get("fallback_g_value") == 0.75,
    )
    raw_g_audit = VEDataExtractor._extract_g_value_audit({"g_value": 0.75})
    validator.require(
        "Raw CDB g_value alone is not treated as SIA-comparable g_perp",
        raw_g_audit.get("selected_sia_g_value") is None
        and raw_g_audit.get("fallback_g_value") == 0.75,
    )

    value_rule_engine = RuleEngine()
    raw_only_opening = SimpleNamespace(
        id="opening-1",
        name="opening-1",
        area=3.0,
        u_value=1.0,
        solar_factor=None,
        solar_factor_source="",
        cdb_g_value=0.75,
        g_value_bs_en_410=None,
        visible_transmittance=0.7,
        frame_fraction=0.25,
        g_total=None,
    )
    integrity_room = SimpleNamespace(
        id="room-1",
        name="room-1",
        area=10.0,
        volume=30.0,
        surfaces=[],
        openings=[raw_only_opening],
        infiltration_m3_h_m2=0.1,
        ventilation_m3_h_m2=2.0,
        internal_gains={},
    )
    integrity = add_value_integrity_alerts(value_rule_engine, [integrity_room])
    integrity_rules = {str(alert.rule) for alert in integrity.get("alerts", [])}
    validator.require(
        "Value-integrity guard flags raw CDB g_value without EN 410 proof",
        "SIA_VALUE_G_SOURCE_NOT_EN410" in integrity_rules,
    )

    sia4010_results = SIA4010Checker(EmptyModelAnalyzer(), RuleEngine()).check_all()
    class_results = sia4010_results.get("classes", {})
    validator.require(
        "SIA 4010 class matrix covers all validation classes",
        set(class_results) == {"1A", "1B", "2A", "2B", "3", "4A", "4B", "5"},
    )
    validator.require(
        "SIA 4010 classes are not validated without explicit official PASS data",
        all(item.get("class_status") != "VALIDATED" for item in class_results.values()),
    )
    validator.require(
        "SIA 4010 strict evidence matcher rejects generic validation workbook",
        not SIA4010Checker._matches_evidence_requirement(
            {"name": "validation.xlsx"},
            SIA4010_EVIDENCE_REQUIREMENTS["official_evaluation_workbooks"],
        ),
    )
    validator.require(
        "SIA 4010 strict evidence matcher accepts documented workbook prefix",
        SIA4010Checker._matches_evidence_requirement(
            {"name": "SIA4010_official_evaluation_workbook_class_4B.xlsx"},
            SIA4010_EVIDENCE_REQUIREMENTS["official_evaluation_workbooks"],
        ),
    )
    validator.require(
        "SIA 4010 evidence manifest file is recognized",
        SIA4010Checker._is_evidence_manifest_file("SIA4010_evidence_index_demo.csv"),
    )
    manifest_row = {
        "evidence_family": "official_test_specifications",
        "provided_file_name": "SIA4010_official_test_specs_class_4B.pdf",
        "source_authority": "SIA official package",
        "version_or_date": "2026-07-05",
        "tests_covered": "Test 1",
        "reviewer": "Reviewer",
        "review_status": "reviewed",
    }
    SIA4010Checker._annotate_manifest_row(
        manifest_row,
        [{"name": "SIA4010_official_test_specs_class_4B.pdf", "path": "sia4010_evidence/SIA4010_official_test_specs_class_4B.pdf", "size_bytes": 16}],
    )
    validator.require(
        "SIA 4010 evidence manifest row documents referenced evidence",
        manifest_row.get("row_status") == "DOCUMENTED"
        and manifest_row.get("review_status_accepted") is True
        and manifest_row.get("provided_file_exists") is True,
    )
    validator.require(
        "SIA 4010 class manifest file is recognized",
        SIA4010Checker._is_class_manifest_file("SIA4010_class_validation_demo.csv"),
    )
    class_manifest_row = {
        "validation_class": "4B",
        "selected": "yes",
        "required_tests": "Test 1; Test 2; Test 3; Test 4; Test 5; Test 6; Test 7",
        "reviewer": "Reviewer",
        "review_status": "confirmed",
        "review_date": "2026-07-06",
        "source_authority": "Responsible compliance authority",
        "source_reference": "SIA 4010 class decision fixture",
    }
    SIA4010Checker._annotate_class_manifest_row(class_manifest_row)
    validator.require(
        "SIA 4010 class manifest row documents selected class",
        class_manifest_row.get("class_key") == "4B"
        and class_manifest_row.get("selected_bool") is True
        and class_manifest_row.get("row_status") == "SELECTED_DOCUMENTED",
    )
    validator.require(
        "SIA 4010 official test-result file is recognized",
        SIA4010Checker._is_official_test_results_file("SIA4010_official_test_results_demo.csv"),
    )
    official_result_row = {
        "test_id": "test_1",
        "status": "validated",
        "reference_file": "SIA4010_reference_comparison_class_4B.pdf",
        "candidate_file": "SIA4010_candidate_results_class_4B_test_1_to_7.xlsx",
        "deviation": "0.0",
        "tolerance": "0.0",
        "reviewer": "Reviewer",
        "review_date": "2026-07-06",
        "source_authority": "Responsible compliance authority",
        "source_reference": "SIA 4010 official test-result fixture",
    }
    official_result_files = [
        {"name": "SIA4010_reference_comparison_class_4B.pdf", "path": "sia4010_evidence/SIA4010_reference_comparison_class_4B.pdf", "size_bytes": 16},
        {"name": "SIA4010_candidate_results_class_4B_test_1_to_7.xlsx", "path": "sia4010_evidence/SIA4010_candidate_results_class_4B_test_1_to_7.xlsx", "size_bytes": 16},
    ]
    SIA4010Checker._annotate_official_test_result_row(official_result_row, official_result_files)
    validator.require(
        "SIA 4010 official test-result row can validate one test",
        official_result_row.get("test_key") == "test_1"
        and official_result_row.get("row_status") == "OFFICIAL_PASS"
        and official_result_row.get("reference_file_exists") is True
        and official_result_row.get("candidate_file_exists") is True,
    )
    official_result_missing_files = dict(official_result_row)
    official_result_missing_files["reference_file"] = "missing_reference.pdf"
    SIA4010Checker._annotate_official_test_result_row(official_result_missing_files, official_result_files)
    validator.require(
        "SIA 4010 official PASS requires referenced files to exist",
        official_result_missing_files.get("row_status") == "REFERENCED_RESULT_FILES_NOT_FOUND",
    )
    official_result_bad_id = dict(official_result_row)
    official_result_bad_id["test_id"] = "test_10"
    SIA4010Checker._annotate_official_test_result_row(official_result_bad_id, official_result_files)
    validator.require(
        "SIA 4010 official test IDs are not normalized from ambiguous digits",
        official_result_bad_id.get("row_status") == "UNKNOWN_TEST",
    )
    official_test_results = SIA4010Checker(EmptyModelAnalyzer(), RuleEngine())._run_sia4010_tests({
        "status": "READY_FOR_OFFICIAL_REVIEW",
        "official_test_result_summary": {
            "recorded_pass_by_test": {"test_1": [official_result_row]},
            "failed_by_test": {},
        },
    })
    validator.require(
        "SIA 4010 test status records explicit official PASS row without certifying",
        official_test_results["test_1"].get("status") == "OFFICIAL_RESULTS_RECORDED"
        and official_test_results["test_1"].get("score") == 0
        and official_test_results["test_2"].get("status") == "READY_FOR_OFFICIAL_REVIEW",
    )
    not_ready_test_results = SIA4010Checker(EmptyModelAnalyzer(), RuleEngine())._run_sia4010_tests({
        "status": "NOT_CHECKABLE",
        "official_test_result_summary": {
            "recorded_pass_by_test": {"test_1": [official_result_row]},
            "failed_by_test": {},
        },
    })
    validator.require(
        "SIA 4010 official PASS does not validate test when evidence pack is not ready",
        not_ready_test_results["test_1"].get("status") == "NOT_CHECKABLE"
        and not_ready_test_results["test_1"].get("score") == 0,
    )
    incomplete_class_manifest_row = dict(class_manifest_row)
    incomplete_class_manifest_row["reviewer"] = ""
    SIA4010Checker._annotate_class_manifest_row(incomplete_class_manifest_row)
    validator.require(
        "SIA 4010 selected class requires complete manifest metadata",
        incomplete_class_manifest_row.get("row_status") == "SELECTED_METADATA_INCOMPLETE",
    )
    prevalidation = build_sia4010_pdf_prevalidation([], {"alerts": []}, {"energy": {}}, {"status": "NOT_CHECKABLE"})
    validator.require(
        "SIA 4010 PDF prevalidation covers seven tests",
        len(prevalidation.get("tests", {})) == 7,
    )
    validator.require(
        "SIA 4010 PDF prevalidation covers all validation classes",
        set(prevalidation.get("classes", {})) == {"1A", "1B", "2A", "2B", "3", "4A", "4B", "5"},
    )

    evidence_without_files = {
        "candidate_results": {"present": True, "files": []},
        SIA4010_REQUIRED_EVIDENCE[2]: True,
    }
    validator.require(
        "SIA 4010 evidence helper rejects PRESENT without detected files",
        not ExcelReportGenerator._has_sia4010_evidence(
            evidence_without_files,
            SIA4010_REQUIRED_EVIDENCE[2],
        ),
    )
    evidence_with_file = {
        "candidate_results": {
            "present": True,
            "files": [{"name": "candidate_results_example.xlsx"}],
        },
        SIA4010_REQUIRED_EVIDENCE[2]: True,
    }
    validator.require(
        "SIA 4010 evidence helper accepts structured families with detected files",
        ExcelReportGenerator._has_sia4010_evidence(
            evidence_with_file,
            SIA4010_REQUIRED_EVIDENCE[2],
        ),
    )
    release_token = f"{id(validator):x}"
    release_report = PROJECT_ROOT / "reports" / f"_release_validation_report_{release_token}.xlsx"
    release_evidence_dir = PROJECT_ROOT / "sia4010_evidence"
    unsafe_zip = release_evidence_dir / f"_release_validation_unsafe_{release_token}.zip"
    unsafe_standard_pdf = release_evidence_dir / f"SIA 4010-2023 FR _release_validation_{release_token}.pdf"
    release_project_label = f"_release_validation_{release_token}"
    active_helper = release_evidence_dir / f"SIA3802_project_metadata_{release_project_label}.csv"
    colliding_helper = release_evidence_dir / f"SIA3802_project_metadata_{release_project_label}_10.csv"
    release_pack = None
    try:
        release_report.parent.mkdir(exist_ok=True)
        release_evidence_dir.mkdir(exist_ok=True)
        release_report.write_bytes(b"release validation workbook placeholder")
        unsafe_zip.write_bytes(b"unsafe zip placeholder")
        unsafe_standard_pdf.write_bytes(b"copied standard placeholder")
        active_helper.write_text("active project helper\n", encoding="utf-8")
        colliding_helper.write_text("colliding project helper\n", encoding="utf-8")
        scoped_checker = SIA4010Checker(
            EmptyModelAnalyzer(),
            RuleEngine(),
            project_label=release_project_label,
        )
        scoped_evidence = scoped_checker._scan_sia4010_evidence()
        validator.require(
            "SIA 4010 evidence scanner excludes helpers for overlapping project names",
            any(
                item.get("name") == active_helper.name
                for item in scoped_evidence.get("files", [])
            )
            and any(
                item.get("name") == colliding_helper.name
                for item in scoped_evidence.get("excluded_project_files", [])
            ),
        )
        pack_result = create_evidence_pack(
            project_root=PROJECT_ROOT,
            report_path=release_report,
            latest_report_path=None,
            sia4010_results=sia4010_results,
            preflight_checks=[],
            project_label=release_project_label,
        )
        release_pack = Path(pack_result.get("path", ""))
        with zipfile.ZipFile(release_pack) as package:
            package_names = set(package.namelist())
            manifest_text = package.read("manifest/evidence_pack_manifest.json").decode("utf-8")
        validator.require(
            "Evidence pack ZIP is generated with README and manifest",
            release_pack.exists()
            and "README_EVIDENCE_PACK.md" in package_names
            and "manifest/evidence_pack_manifest.json" in package_names
            and release_report.relative_to(PROJECT_ROOT).as_posix() in package_names
            and unsafe_zip.relative_to(PROJECT_ROOT).as_posix() not in package_names
            and unsafe_standard_pdf.relative_to(PROJECT_ROOT).as_posix() not in package_names
            and active_helper.relative_to(PROJECT_ROOT).as_posix() in package_names
            and colliding_helper.relative_to(PROJECT_ROOT).as_posix() not in package_names
            and "excluded_files" in manifest_text
            and "not an official SIA certificate" in manifest_text,
        )
    finally:
        for path in [
            release_report,
            release_pack,
            unsafe_zip,
            unsafe_standard_pdf,
            active_helper,
            colliding_helper,
        ]:
            try:
                if path and Path(path).exists():
                    Path(path).unlink()
            except Exception:
                pass

    bootstrap_result = prepare_evidence_folder(
        project_root=PROJECT_ROOT,
        project_label="_release_validation_bootstrap",
        overwrite=False,
    )
    bootstrap_targets = [
        Path(item.get("target", ""))
        for item in bootstrap_result.get("files", [])
        if item.get("status") in {"CREATED", "OVERWRITTEN"}
    ]
    try:
        validator.require(
            "Evidence bootstrap creates project-named CSV handoff files",
            bootstrap_result.get("status") == "READY"
            and bootstrap_result.get("created_count") == 16
            and all(path.exists() for path in bootstrap_targets),
        )
    finally:
        for path in bootstrap_targets:
            try:
                if path.exists():
                    path.unlink()
            except Exception:
                pass


def check_internal_fixture_scenarios(validator: Validator) -> None:
    """Validate production checkers against deterministic in-memory fixtures."""
    from scripts.quality.fixtures import (
        build_problem_analyzer,
        build_reference_analyzer,
        collect_alert_rules,
        collect_high_or_critical_alert_rules,
    )
    from swiss_sia.config import SIA4010_CLASS_TEST_MATRIX
    from swiss_sia.rule_engine import RuleEngine
    from swiss_sia.sia380_checker import SIA3802Checker
    from swiss_sia.sia4010_checker import SIA4010Checker
    from swiss_sia.simulation_results import normalize_co2_series_to_ppm

    accepted_global_comparison = {
        "global_reference_comparison": {
            "accepted": True,
            "comparison_scope": "complete_sia3802_project",
            "project_value_numeric": 95.0,
            "reference_value_numeric": 100.0,
            "unit": "kWh/a",
            "source_document": "quality_fixture_review.csv",
        },
    }
    reference_results = SIA3802Checker(build_reference_analyzer(), RuleEngine()).check_all(
        dynamic_results=accepted_global_comparison,
        external_mappings={
            "sia2024_usage": {
                "accepted_records": [{
                    "room_id": "fixture-reference-room",
                    "sia2024_category": "QUALITY_FIXTURE",
                }],
            },
            "sia3874_lighting": {
                "accepted_records": [{
                    "room_id": "fixture-reference-room",
                    "sia3874_control_type": "QUALITY_FIXTURE",
                }],
            },
        },
    )
    reference_high_rules = collect_high_or_critical_alert_rules(reference_results)
    validator.require(
        "SIA 380/2 reference fixture has no high or critical alerts",
        not reference_high_rules,
        "; ".join(sorted(reference_high_rules)),
    )
    validator.require(
        "SIA 380/2 reference fixture scores complete categories and caps incomplete ventilation",
        reference_results["envelope"]["score"] == 100.0
        and reference_results["openings"]["score"] == 100.0
        and reference_results["gains"]["score"] == 100.0
        and reference_results["hvac"]["score"] == 100.0
        and reference_results["ventilation"]["score"] == 60.0,
    )
    validator.require(
        "SIA 380/2 reference fixture has no value-integrity alerts",
        reference_results["value_integrity"]["alert_count"] == 0,
    )
    co2_values, co2_note = normalize_co2_series_to_ppm(
        [0.0004, 0.0008],
        "Room CO2 concentration",
    )
    validator.require(
        "APS CO2 fraction results are normalized to ppm",
        co2_values == [400.0, 800.0] and co2_note == "converted from fraction to ppm",
        str(co2_values),
    )

    problem_results = SIA3802Checker(build_problem_analyzer(), RuleEngine()).check_all()
    problem_rules = collect_alert_rules(problem_results)
    expected_problem_rules = {
        "SIA3802_U_VALUE_EXTERNAL_WALL",
        "SIA3802_U_VALUE_ROOF",
        "SIA3802_U_VALUE_WINDOW",
        "SIA3802_G_VALUE_SOURCE_NOT_COMPARABLE",
        "SIA3802_G_TOTAL_WITH_SHADING_MISSING",
        "SIA3802_INFILTRATION_M3_H_M2",
        "SIA_VALUE_G_SOURCE_NOT_EN410",
    }
    validator.require(
        "SIA 380/2 problem fixture triggers expected rule families",
        expected_problem_rules <= problem_rules,
        "; ".join(sorted(expected_problem_rules - problem_rules)),
    )
    validator.require(
        "SIA 380/2 problem fixture keeps reference inputs diagnostic and lowers opening score",
        problem_results["envelope"]["score"] == 100.0
        and problem_results["openings"]["score"] < 100.0
        and bool(problem_results["reference_project_diagnostics"].get("alerts")),
    )

    sia4010_checker = SIA4010Checker(build_reference_analyzer(), RuleEngine())
    recorded_pass_by_test = {
        test_name: [{"test_id": test_name, "row_status": "OFFICIAL_PASS"}]
        for test_name in SIA4010_CLASS_TEST_MATRIX["4B"]
    }
    ready_summary = {
        "status": "READY_FOR_OFFICIAL_REVIEW",
        "validation_class": "4B",
        "missing_items": [],
        "official_test_result_summary": {
            "recorded_pass_by_test": recorded_pass_by_test,
            "failed_by_test": {},
        },
    }
    ready_tests = sia4010_checker._run_sia4010_tests(ready_summary)
    ready_classes = sia4010_checker._evaluate_validation_classes(ready_tests, ready_summary)
    validator.require(
        "SIA 4010 fixture records tests without granting validation",
        all(
            test.get("status") == "OFFICIAL_RESULTS_RECORDED"
            and test.get("score") == 0
            for test in ready_tests.values()
        ),
    )
    validator.require(
        "SIA 4010 fixture records the selected class pending attestation",
        ready_classes["4B"].get("class_status") == "OFFICIAL_RESULTS_RECORDED"
        and all(
            class_name == "4B" or class_data.get("class_status") == "NOT_REQUESTED"
            for class_name, class_data in ready_classes.items()
        ),
    )

    failed_summary = {
        "status": "READY_FOR_OFFICIAL_REVIEW",
        "validation_class": "4B",
        "missing_items": [],
        "official_test_result_summary": {
            "recorded_pass_by_test": recorded_pass_by_test,
            "failed_by_test": {"test_1": [{"test_id": "test_1", "row_status": "OFFICIAL_FAIL"}]},
        },
    }
    failed_tests = sia4010_checker._run_sia4010_tests(failed_summary)
    failed_classes = sia4010_checker._evaluate_validation_classes(failed_tests, failed_summary)
    validator.require(
        "SIA 4010 official FAIL overrides an official PASS row",
        failed_tests["test_1"].get("status") == "FAIL"
        and failed_classes["4B"].get("class_status") != "VALIDATED",
    )


def check_claim_safety_without_official_excel(validator: Validator) -> None:
    """Validate that readiness helpers cannot overclaim without official files."""
    from scripts.quality.fixtures import StaticModelAnalyzer, build_reference_room, collect_alert_rules
    from swiss_sia.config import SIA4010_REQUIRED_EVIDENCE
    from swiss_sia.excel_report import ExcelReportGenerator
    from swiss_sia.health_score import HealthScoreCalculator
    from swiss_sia.rule_engine import RuleEngine
    from swiss_sia.sia380_checker import SIA3802Checker

    raw_cdb_room = build_reference_room()
    raw_cdb_opening = raw_cdb_room.openings[0]
    raw_cdb_opening.solar_factor = 0.45
    raw_cdb_opening.solar_factor_source = ""
    raw_cdb_opening.cdb_g_value = 0.45
    raw_cdb_opening.g_value_bs_en_410 = None
    raw_cdb_opening.g_total = None
    raw_cdb_opening.g_total_source = None

    raw_cdb_results = SIA3802Checker(
        StaticModelAnalyzer([raw_cdb_room]),
        RuleEngine(),
    ).check_all()
    raw_cdb_rules = collect_alert_rules(raw_cdb_results)
    validator.require(
        "Raw CDB g-value below limit is not accepted as SIA g_perp",
        "SIA3802_G_VALUE_SOURCE_NOT_COMPARABLE" in raw_cdb_rules
        and "SIA_VALUE_G_SOURCE_NOT_EN410" in raw_cdb_rules
        and raw_cdb_results["openings"]["score"] < 100.0,
    )

    report_helper = ExcelReportGenerator.__new__(ExcelReportGenerator)
    raw_cdb_rows = report_helper._build_ve_g_values_audit_rows([raw_cdb_room])
    validator.require(
        "Report g-total status does not waive shading evidence without EN 410 proof",
        bool(raw_cdb_rows)
        and raw_cdb_rows[0].get("g_proof_status") != "EN410_AVAILABLE"
        and raw_cdb_rows[0].get("g_total_status") != "NOT_REQUIRED_FOR_G_LIMIT",
        str(raw_cdb_rows[0] if raw_cdb_rows else {}),
    )

    legacy_bool_evidence = {
        "candidate_results": True,
        SIA4010_REQUIRED_EVIDENCE[2]: True,
    }
    validator.require(
        "Legacy boolean evidence flags do not count as official SIA 4010 files",
        not ExcelReportGenerator._has_sia4010_evidence(
            legacy_bool_evidence,
            SIA4010_REQUIRED_EVIDENCE[2],
        ),
    )

    zero_sia3802 = {
        "envelope": {"score": 0.0},
        "openings": {"score": 0.0},
        "ventilation": {"score": 0.0},
        "gains": {"score": 0.0},
        "hvac": {"score": 0.0},
        "alerts": [],
    }
    high_readiness_sia4010 = {
        "score": 100.0,
        "readiness_score": 100.0,
        "alerts": [],
        "tests": {},
    }
    score_result = HealthScoreCalculator().calculate_scores(
        zero_sia3802,
        high_readiness_sia4010,
    )
    validator.require(
        "SIA 4010 readiness does not inflate the SIA 380/2 compliance score",
        score_result.compliance_score == 0.0
        and score_result.detailed_scores.get("SIA4010_EVIDENCE_READINESS") == 100.0,
    )


def check_sia3802_gap_boundaries(validator: Validator) -> None:
    """Ensure SIA 380/2 gaps remain visible instead of being hidden."""
    from swiss_sia import config

    coverage_rows = [
        item for item in config.SIA_DATA_COVERAGE_MATRIX
        if str(item.get("id", "")).startswith("SIA3802")
    ]
    requirement_rows = [
        item for item in config.SIA_COMPLIANCE_REQUIREMENT_MATRIX
        if str(item.get("id", "")).startswith("SIA3802")
    ]
    automation_states = {str(item.get("automation", "")) for item in coverage_rows}
    partial_requirements = [
        item for item in requirement_rows
        if str(item.get("automation", "")) in {"PARTIAL", "READINESS_ONLY", "NOT_IMPLEMENTED"}
    ]

    validator.require("SIA 380/2 coverage matrix is populated", bool(coverage_rows))
    validator.require("SIA 380/2 requirement matrix is populated", bool(requirement_rows))
    validator.require(
        "SIA 380/2 coverage matrix keeps non-automated gaps explicit",
        "NOT_IMPLEMENTED" in automation_states and "PARTIAL" in automation_states,
        str(sorted(automation_states)),
    )
    validator.require(
        "SIA 380/2 requirement matrix keeps partial compliance requirements explicit",
        bool(partial_requirements),
        "All SIA 380/2 requirements appear fully automated, which would be unsafe without delegated-standard evidence.",
    )


def check_documentation_entry_points(validator: Validator) -> None:
    """Validate manager/audit documentation entry points."""
    required_files = [
        PROJECT_ROOT / "Prepare_SIA4010_Evidence_Folder.py",
        PROJECT_ROOT / "Run_VE_Swiss_Compliance.py",
        PROJECT_ROOT / "Run_VE_SIA3802_Approved_Template_Remediation.py",
        PROJECT_ROOT / "docs" / "source" / "index.rst",
        PROJECT_ROOT / "docs" / "source" / "manager_multilingual_brief_sphinx.rst",
        PROJECT_ROOT / "docs" / "source" / "manager_reference_integration.rst",
        PROJECT_ROOT / "docs" / "source" / "compliance_coverage_audit.rst",
        PROJECT_ROOT / "docs" / "source" / "implementation_status.rst",
        PROJECT_ROOT / "docs" / "source" / "sia3802_gap_audit.rst",
        PROJECT_ROOT / "docs" / "source" / "compliance_methodology.rst",
        PROJECT_ROOT / "docs" / "source" / "documentation_quality.rst",
        PROJECT_ROOT / "docs" / "source" / "user_guide.rst",
        PROJECT_ROOT / "docs" / "source" / "reference_model_guide.rst",
        PROJECT_ROOT / "docs" / "requirements-docs.txt",
        PROJECT_ROOT / "docs" / "README.md",
        PROJECT_ROOT / "docs" / "project" / "RELEASE_ACCEPTANCE_CHECKLIST.md",
        PROJECT_ROOT / "docs" / "project" / "ETAT_FINAL_MVP_MSP_2026-08-24.md",
        PROJECT_ROOT / "docs" / "project" / "GLAZING_EVIDENCE_GUIDE.md",
        PROJECT_ROOT / "docs" / "project" / "MANAGER_REFERENCE_INTEGRATION.md",
        PROJECT_ROOT / "docs" / "project" / "SIA4010_PDF_PREVALIDATION_STRATEGY.md",
        PROJECT_ROOT / "docs" / "project" / "SIA4010_TESTS_AND_CLASSES_IMPLEMENTATION.md",
        PROJECT_ROOT / "docs" / "project" / "SIA3802_FULL_COMPLIANCE_GAP_AUDIT.md",
        PROJECT_ROOT / "docs" / "project" / "SIA3802_CLIENT_TEMPLATE_REMEDIATION_EN.md",
        PROJECT_ROOT / "docs" / "project" / "SIA3802_SIA4010_IMPLEMENTATION_STATUS.md",
        PROJECT_ROOT / "docs" / "project" / "SIA_COMPATIBLE_MODEL_REFERENCE_ACTIONS.md",
        PROJECT_ROOT / "docs" / "project" / "WAITING_FOR_OFFICIAL_EXCEL_ACTION_PLAN.md",
        PROJECT_ROOT / "swiss_sia" / "evidence_bootstrap.py",
        PROJECT_ROOT / "swiss_sia" / "evidence_manager.py",
        PROJECT_ROOT / "swiss_sia" / "evidence_pack.py",
        PROJECT_ROOT / "swiss_sia" / "client_template_remediation.py",
        PROJECT_ROOT / "swiss_sia" / "client_template_remediation_ui.py",
        PROJECT_ROOT / "swiss_sia" / "sia4010_test_adapters.py",
        PROJECT_ROOT / "templates" / "evidence" / "README.md",
        PROJECT_ROOT / "templates" / "evidence" / "glazing_solar_protection_template.csv",
        PROJECT_ROOT / "templates" / "evidence" / "g_values_audit_template.csv",
        PROJECT_ROOT / "templates" / "evidence" / "sia3802_justifications_template.csv",
        PROJECT_ROOT / "templates" / "evidence" / "sia2024_usage_mapping_template.csv",
        PROJECT_ROOT / "templates" / "evidence" / "sia3874_lighting_control_mapping_template.csv",
        PROJECT_ROOT / "templates" / "evidence" / "sia3802_project_metadata_template.csv",
        PROJECT_ROOT / "templates" / "evidence" / "sia3802_global_reference_comparison_template.csv",
        PROJECT_ROOT / "templates" / "evidence" / "sia3802_thermal_bridges_template.csv",
        PROJECT_ROOT / "templates" / "evidence" / "sia3802_cooling_generators_template.csv",
        PROJECT_ROOT / "templates" / "evidence" / "sia3802_ahu_heat_recovery_template.csv",
        PROJECT_ROOT / "templates" / "evidence" / "sia3802_ventilation_control_template.csv",
        PROJECT_ROOT / "templates" / "evidence" / "sia3802_electrical_power_template.csv",
        PROJECT_ROOT / "templates" / "evidence" / "sia4010_evidence_index_template.csv",
        PROJECT_ROOT / "templates" / "evidence" / "sia4010_class_validation_template.csv",
        PROJECT_ROOT / "templates" / "evidence" / "sia4010_official_test_results_template.csv",
        PROJECT_ROOT / "templates" / "evidence" / "sia4010_software_register_review_template.csv",
    ]
    for path in required_files:
        validator.require(f"Documentation file exists: {path.relative_to(PROJECT_ROOT)}", path.exists())

    html_index = PROJECT_ROOT / "docs" / "build" / "html" / "en" / "index.html"
    validator.warn_if(
        "Built HTML documentation is available",
        html_index.exists(),
        "Run python docs/tools/build_docs.py --language en --builder html before a manager review.",
    )


def _project_python_files() -> list[Path]:
    """Return the Python files owned by this project, excluding dependencies."""
    root_files = [
        PROJECT_ROOT / "main.py",
        PROJECT_ROOT / "Prepare_SIA4010_Evidence_Folder.py",
        PROJECT_ROOT / "RUN_IESVE_EXTRACTION_PROBE.py",
        PROJECT_ROOT / "Run_VE_Swiss_Compliance.py",
    ]
    scanned_folders = [
        PROJECT_ROOT / "swiss_sia",
        PROJECT_ROOT / "scripts",
        PROJECT_ROOT / "docs" / "source",
        PROJECT_ROOT / "docs" / "tools",
    ]
    paths = [path for path in root_files if path.exists()]
    for folder in scanned_folders:
        if folder.exists():
            paths.extend(
                path
                for path in folder.rglob("*.py")
                if "__pycache__" not in path.parts
            )
    return sorted(set(paths))


def _looks_non_english_documentation(text: str) -> bool:
    """Return true when a comment or docstring looks non-English."""
    lowered = f" {text.lower()} "
    french_markers = [
        " le ",
        " la ",
        " les ",
        " des ",
        " une ",
        " un ",
        " et ",
        " avec ",
        " dans ",
        " pour ",
        " correspond ",
        " pièce",
        " vérifie",
        " paramètres",
        " rapport",
        " fichier",
        " dossier",
        " fenêtres",
        " portes",
        " poids",
        " chauffage",
        " solaire",
        " bois",
        " fioul",
        " gaz naturel",
        " valeurs directes",
        " indicateurs de revue",
        " ajuster ",
    ]
    return any(ord(char) > 127 for char in text) or any(
        marker in lowered for marker in french_markers
    )


def check_python_documentation_quality(validator: Validator) -> None:
    """Audit Python documentation without blocking an executable MVP release.

    Syntax and tokenization failures remain blocking because they indicate
    unusable source. Documentation coverage and language are reported as
    technical-debt warnings: the repository intentionally contains historical
    French source-audit utilities, and translating them is unrelated to the
    correctness or claim safety of the compliance engine.
    """
    paths = _project_python_files()
    missing_docstrings: list[str] = []
    thin_docstrings: list[str] = []
    language_issues: list[str] = []

    validator.require("Python documentation quality scope is not empty", bool(paths))

    for path in paths:
        relative_path = path.relative_to(PROJECT_ROOT)
        try:
            source = path.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source)
        except SyntaxError as exc:
            validator.require(
                f"Python file parses for documentation checks: {relative_path}",
                False,
                str(exc),
            )
            continue

        module_docstring = ast.get_docstring(tree)
        if not module_docstring:
            missing_docstrings.append(f"{relative_path}:1 module")
        elif len(module_docstring.strip().split()) < 4:
            thin_docstrings.append(f"{relative_path}:1 module")

        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                docstring = ast.get_docstring(node)
                node_name = getattr(node, "name", type(node).__name__)
                if not docstring:
                    missing_docstrings.append(
                        f"{relative_path}:{node.lineno} {node_name}"
                    )
                elif len(docstring.strip().split()) < 4:
                    thin_docstrings.append(
                        f"{relative_path}:{node.lineno} {node_name}"
                    )
                elif _looks_non_english_documentation(docstring):
                    language_issues.append(
                        f"{relative_path}:{node.lineno} docstring {node_name}"
                    )

        if module_docstring and _looks_non_english_documentation(module_docstring):
            language_issues.append(f"{relative_path}:1 module docstring")

        try:
            tokens = tokenize.generate_tokens(io.StringIO(source).readline)
            for token in tokens:
                if token.type == tokenize.COMMENT and _looks_non_english_documentation(token.string):
                    language_issues.append(f"{relative_path}:{token.start[0]} comment")
        except tokenize.TokenError as exc:
            validator.require(
                f"Python comments tokenize for documentation checks: {relative_path}",
                False,
                str(exc),
            )

    validator.warn_if(
        "Python modules/classes/functions have docstrings",
        not missing_docstrings,
        "{} item(s): {}".format(
            len(missing_docstrings), "; ".join(missing_docstrings[:12])
        ),
    )
    validator.warn_if(
        "Python docstrings are descriptive enough for generated API docs",
        not thin_docstrings,
        "{} item(s): {}".format(
            len(thin_docstrings), "; ".join(thin_docstrings[:12])
        ),
    )
    validator.warn_if(
        "Python comments and docstrings are English-only",
        not language_issues,
        "{} item(s): {}".format(
            len(language_issues), "; ".join(language_issues[:12])
        ),
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
        "FACADE GLAZING REVIEW",
        "FRAME FRACTION AUDIT",
        "ENVELOPE U REVIEW",
        "VE G-VALUES AUDIT",
        "COMPLIANCE RESULTS",
        "REFERENCE PROJECT",
        "SIA REQUIREMENTS",
        "ASSUMPTIONS LIMITS",
        "AUDIT LOG",
        "SIA DATA COVERAGE",
        "INPUT REQUEST",
        "SIA3802 JUSTIFICATIONS",
        "OPEN ITEMS BACKLOG",
        "SIA4010 READINESS",
        "SIA4010 PREVALIDATION",
        "SIA4010 CLASS MATRIX",
        "SIA4010 SOFTWARE REGISTER",
        "NAVIGATOR BACKLOG",
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


def check_traceability_matrix_signatures(validator: Validator) -> None:
    """Report the qa-auditor signature state of the SIA traceability matrices.

    The Definition of Done requires an independent ``qa-auditor`` signature on
    each SIA test matrix. This gate never signs and never silently treats an
    unsigned matrix as done: it requires every matrix to DECLARE a signature
    status, then surfaces the unsigned ones as a warning so a reviewer preparing
    a release sees exactly what is not yet validated.
    """
    matrices = sorted((PROJECT_ROOT / "traceability").glob("*.matrix.md"))
    validator.require(
        "Traceability matrices present",
        bool(matrices),
        "no traceability/*.matrix.md found under the project root",
    )
    unsigned: list[str] = []
    for matrix in matrices:
        text = matrix.read_text(encoding="utf-8", errors="replace")
        upper = text.upper()
        validator.require(
            f"Matrix declares a signature status: {matrix.name}",
            "STATUT :" in upper or "STATUT:" in upper,
            "no 'Statut :' signature declaration found in the matrix header",
        )
        # A matrix counts as signed only with an explicit signed status and no
        # 'NON SIGNE' marker (accented and unaccented forms are both matched).
        is_unsigned = "NON SIGN" in upper
        is_signed = (not is_unsigned) and (
            "STATUT : **SIGN" in upper or "AUDITE OK" in upper or "AUDITÉ OK" in upper
        )
        if not is_signed:
            unsigned.append(matrix.name)
    validator.warn_if(
        "All SIA traceability matrices are independently signed",
        not unsigned,
        (
            "{} matrix/matrices are not qa-auditor-signed: {}. Per the Definition "
            "of Done these tests are not 'done'; a release must not present them "
            "as validated.".format(len(unsigned), ", ".join(unsigned))
        ),
    )


def main() -> int:
    """Run all release-quality checks."""
    print(
        "Release-quality gate. NOTE: this does NOT run the test suite -- run "
        "`python -m pytest` (and rely on CI) for the authoritative test gate."
    )
    validator = Validator()
    check_standard_pdfs(validator)
    check_manager_reference_documents(validator)
    check_config_traceability(validator)
    check_scoring_guardrails(validator)
    check_internal_fixture_scenarios(validator)
    check_claim_safety_without_official_excel(validator)
    check_sia3802_gap_boundaries(validator)
    check_documentation_entry_points(validator)
    check_python_documentation_quality(validator)
    check_latest_excel_report(validator)
    check_traceability_matrix_signatures(validator)
    validator.finish()
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ReleaseValidationError as exc:
        print(f"[FAIL] {exc}")
        raise SystemExit(1)
