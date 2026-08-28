"""Tests for the provisional Test 4 fan-map digitization."""

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_test4_fan_curve_binding.py"
SPEC = importlib.util.spec_from_file_location("test4_fan_builder", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_digitization_is_complete_monotonic_and_candidate_scoped():
    payload = MODULE.build_payload()
    MODULE.validate(payload)
    assert payload["status"] == (
        "SOURCE_TRACE_VERIFIED_CANDIDATE_APPROXIMATION_REQUIRED"
    )
    assert payload["compliance_claim_allowed"] is False
    assert payload["interpolation_authorized"] is True
    assert payload["candidate_specific_approximation_authorized"] is True
    assert payload["authority_decision"]["decision_id"] == (
        "SIA4010_REMAINING_CLARIFICATIONS_20260828"
    )
    assert len(payload["digitized_points"]) == 16


def test_nominal_operating_points_are_source_text_not_curve_inference():
    payload = MODULE.build_payload()
    assert payload["nominal_operating_points_from_page_text"]["supply"] == {
        "volume_flow_m3_h": 1700,
        "static_pressure_pa": 500,
        "electrical_power_w": 407,
        "speed_rpm": 2790,
    }
    assert payload["nominal_operating_points_from_page_text"]["extract"] == {
        "volume_flow_m3_h": 1700,
        "static_pressure_pa": 400,
        "electrical_power_w": 331,
        "speed_rpm": 2730,
    }


def test_embedded_source_images_are_checksum_bound():
    payload = MODULE.build_payload()
    assert payload["source"]["sha256"] == (
        "6ffd140972388c09cd3a92f0d178c04248140239667931d13bdd5c78aa353775"
    )
    assert payload["source"]["fan_map_embedded_image_sha256"] == (
        "0a388f6c77ed40d17ccc456f10183e283cc6f0943ff3ecc429d34eb9a748cc8e"
    )
    assert payload["source"]["measured_table_embedded_image_sha256"] == (
        "dea7b795ab46794b89a9e7a4842a68442b9840eea9fe1910d21003019d5d2f8d"
    )
