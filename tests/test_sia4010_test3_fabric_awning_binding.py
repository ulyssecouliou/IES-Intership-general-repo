"""Regression checks for the source-bound Test 3 fabric-awning definition."""

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "sia4010_evidence" / "source_audits" / "test3_fabric_awning_20260825"
BINDING = AUDIT_DIR / "sia_example_building_fabric_awning_detail.binding.json"
VALIDATION = AUDIT_DIR / "sia_example_building_fabric_awning_detail.validation.json"
SOURCE = (
    ROOT
    / "SIA_4010_geteilter_Link"
    / "Beispielgebäude"
    / "Dokumentation_Beispielgebäude_V5.pdf"
)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_binding_and_validation_are_bound_to_the_exact_source():
    binding = json.loads(BINDING.read_text(encoding="utf-8"))
    validation = json.loads(VALIDATION.read_text(encoding="utf-8"))
    assert binding["schema_id"] == "sia4010.shading_device_definition.v1"
    assert binding["sources"][0]["sha256"] == _sha256(SOURCE)
    assert validation["source_sha256"] == _sha256(SOURCE)
    assert validation["binding_artifact"]["sha256"] == _sha256(BINDING)
    assert validation["status"] == "PASS"


def test_summer_energy_and_secondary_heat_balances_are_exact():
    payload = json.loads(BINDING.read_text(encoding="utf-8"))
    summer = payload["summer_en_iso_52022_3"]
    optical = payload["en_410_optical"]
    for state in ("unshaded", "shaded"):
        assert summer[state]["g_total"] == pytest.approx(
            optical[state]["direct_solar_transmittance"]
            + summer[state]["secondary_internal_heat_transfer_factor"]
        )
        assert summer[state]["secondary_internal_heat_transfer_factor"] == pytest.approx(
            summer[state]["convection_factor"]
            + summer[state]["thermal_radiation_factor"]
            + summer[state]["ventilation_factor"]
        )


def test_dynamic_control_unknowns_are_not_claimed_as_qualified():
    payload = json.loads(BINDING.read_text(encoding="utf-8"))
    device = payload["device"]
    assert device["closure_irradiance_threshold_w_m2"] == 150.0
    assert "PENDING" in device["dynamic_semantics_status"]
    assert "does not resolve" in payload["claim_guardrail"]
