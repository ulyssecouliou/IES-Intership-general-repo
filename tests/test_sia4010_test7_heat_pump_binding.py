"""Regression checks for the source-bound SIA 4010 Test 7 heat-pump tables."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "sia4010_evidence" / "source_audits" / "test7_heat_pump_20260825"
BINDING = AUDIT_DIR / "test7_heat_pump_performance_tables.binding.json"
VALIDATION = AUDIT_DIR / "test7_heat_pump_performance_tables.validation.json"
SOURCE = ROOT / "SIA_4010_geteilter_Link" / "Test7" / "Spezifikation_Test7.pdf"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_binding_and_validation_are_checksum_bound_to_exact_sources():
    binding = json.loads(BINDING.read_text(encoding="utf-8"))
    validation = json.loads(VALIDATION.read_text(encoding="utf-8"))
    assert binding["schema_id"] == "sia4010.generator_performance_tables.v1"
    assert binding["source"]["sha256"] == _sha256(SOURCE)
    assert validation["source_sha256"] == _sha256(SOURCE)
    assert validation["binding_artifact"]["sha256"] == _sha256(BINDING)
    assert validation["status"] == "PASS"
    assert all(check["status"] == "PASS" for check in validation["checks"])


def test_nominal_and_bivalent_values_reconcile_with_the_source_tables():
    payload = json.loads(BINDING.read_text(encoding="utf-8"))
    assert payload["equipment"]["rated_cooling_capacity_kw"] == 55.9
    assert payload["equipment"]["rated_heating_capacity_kw"] == 60.0
    cooling = payload["cooling_low_temperature_application"]
    assert cooling["declared_points"][0] == {
        "outdoor_temperature_c": 35.0,
        "capacity_kw": 55.9,
        "eer": 4.96,
    }
    for key in (
        "heating_low_temperature_application",
        "heating_medium_temperature_application",
    ):
        table = payload[key]
        at_minus_7 = table["declared_points"][0]
        at_bivalent = table["declared_points"][4]
        assert table["bivalent_temperature_c"] == -7.0
        assert at_bivalent["capacity_kw"] == at_minus_7["capacity_kw"]
        assert at_bivalent["cop"] == at_minus_7["cop"]


def test_all_three_tables_carry_the_required_inactive_mode_powers():
    payload = json.loads(BINDING.read_text(encoding="utf-8"))
    tables = (
        payload["cooling_low_temperature_application"],
        payload["heating_low_temperature_application"],
        payload["heating_medium_temperature_application"],
    )
    for table in tables:
        powers = table["inactive_mode_power_kw"]
        assert powers["off"] == 0.0
        assert powers["standby"] == 0.023
        assert powers["crankcase_heater"] == 0.140
