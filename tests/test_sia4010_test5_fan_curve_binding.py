"""Tests for the provisional Test 5 fan-map digitization."""

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
SCRIPT = SCRIPTS / "build_test5_fan_curve_binding.py"
SPEC = importlib.util.spec_from_file_location("test5_fan_builder", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def test_test5_reuses_the_checksum_identical_fan_map_with_candidate_scope():
    payload = MODULE.build_test5_payload()
    assert payload["input_id"] == "test5_fan_curve_digitization"
    assert payload["compliance_claim_allowed"] is False
    assert payload["interpolation_authorized"] is True
    assert payload["candidate_specific_approximation_authorized"] is True
    assert len(payload["digitized_points"]) == 16
    assert payload["source"]["fan_map_embedded_image_sha256"] == (
        "0a388f6c77ed40d17ccc456f10183e283cc6f0943ff3ecc429d34eb9a748cc8e"
    )


def test_test5_nominal_points_are_transcribed_from_its_own_page():
    nominal = MODULE.build_test5_payload()["nominal_operating_points_from_page_text"]
    assert nominal["supply"] == {
        "volume_flow_m3_h": 1040,
        "static_pressure_pa": 770,
        "electrical_power_w": 420,
        "speed_rpm": 3000,
    }
    assert nominal["extract"] == {
        "volume_flow_m3_h": 1040,
        "static_pressure_pa": 520,
        "electrical_power_w": 290,
        "speed_rpm": 2500,
    }
