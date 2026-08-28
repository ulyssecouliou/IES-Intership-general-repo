"""Regression checks for the 2026-08-28 SIA authority response."""

import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "apply_sia4010_authority_response_20260828.py"
SPEC = importlib.util.spec_from_file_location("sia4010_authority_20260828", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_test7_pv_binding_transcribes_precedence_and_roof_split():
    binding = MODULE.build_pv_binding()
    parameters = {
        item["id"]: item["value"] for item in binding["resolved_parameters"]
    }
    assert binding["schema_id"] == "sia4010.authority_decision.v1"
    assert parameters["pv_authoritative_total_kwp"] == 62.62
    assert parameters["pv_superseded_specification_total_kwp"] == 60.6
    assert parameters["pv_roof_east_modules"] == 75
    assert parameters["pv_roof_west_modules"] == 75
    assert parameters["pv_roof_east_kwp"] == 22.5
    assert parameters["pv_roof_west_kwp"] == 22.5


def test_prepared_manifest_records_sources_but_keeps_workbook_fail_closed():
    payload = json.loads(MODULE.CONFIG.read_text(encoding="utf-8"))
    records = payload["inputs"]
    for input_id in MODULE.USE_DATASETS:
        record = records[input_id]
        assert record["source_sha256"] == MODULE.EXPECTED_WORKBOOK_SHA256
        assert record["normative_authorization_status"] == "CONFIRMED"
        assert record["technical_validation"]["status"] == "PENDING"
        assert record["technical_validation"]["report_path"] is None


def test_fan_and_pv_authority_records_are_ready_at_source_level():
    payload = json.loads(MODULE.CONFIG.read_text(encoding="utf-8"))
    records = payload["inputs"]
    for input_id in ("test4_fan_curve_digitization", "test5_fan_curve_digitization"):
        assert records[input_id]["normative_authorization_status"] == "CONFIRMED"
        assert records[input_id]["technical_validation"]["status"] == "PASS"
    pv = records["sia_authority_test7_pv_precedence"]
    assert pv["normative_authorization_status"] == "CONFIRMED"
    assert pv["technical_validation"]["status"] == "PASS"
