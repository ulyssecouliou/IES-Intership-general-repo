"""Regression checks for the source-bound SIA 4010 Test 6 stage trace."""

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDIT_DIR = ROOT / "sia4010_evidence" / "source_audits" / "test6_stage_control_20260825"
BINDING = AUDIT_DIR / "test6_stage_control_trace.binding.json"
VALIDATION = AUDIT_DIR / "test6_stage_control_trace.validation.json"
SOURCE = ROOT / "SIA_4010_geteilter_Link" / "Test6" / "Spezifikation_Test6.pdf"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _minutes(value: str) -> int:
    hours, minutes = (int(part) for part in value.split(":"))
    return hours * 60 + minutes


def test_binding_and_validation_are_checksum_bound_to_exact_source():
    binding = json.loads(BINDING.read_text(encoding="utf-8"))
    validation = json.loads(VALIDATION.read_text(encoding="utf-8"))
    assert binding["schema_id"] == "sia4010.control_trace.v1"
    assert binding["source"]["sha256"] == _sha256(SOURCE)
    assert validation["source_sha256"] == _sha256(SOURCE)
    assert validation["binding_artifact"]["sha256"] == _sha256(BINDING)
    assert validation["status"] == "PASS"
    assert all(check["status"] == "PASS" for check in validation["checks"])


def test_daily_trace_is_contiguous_and_covers_the_whole_day():
    payload = json.loads(BINDING.read_text(encoding="utf-8"))
    trace = payload["daily_trace"]
    assert trace[0]["start"] == "00:00"
    assert trace[-1]["end"] == "24:00"
    assert all(left["end"] == right["start"] for left, right in zip(trace, trace[1:]))
    assert sum(_minutes(item["end"]) - _minutes(item["start"]) for item in trace) == 1440


def test_stage_sequence_and_airflows_match_the_source_graph():
    payload = json.loads(BINDING.read_text(encoding="utf-8"))
    trace = payload["daily_trace"]
    assert [item["stage"] for item in trace] == [0, 1, 2, 3, 2, 1, 0]
    expected = {"0": 0.0, "1": 2050.0, "2": 4100.0, "3": 6150.0}
    assert payload["controlled_system"]["nominal_stage_airflow_m3_h"] == expected
    for item in trace:
        assert item["airflow_m3_h"] == expected[str(item["stage"])]


def test_trace_scope_is_monday_through_saturday_only():
    payload = json.loads(BINDING.read_text(encoding="utf-8"))
    system = payload["controlled_system"]
    assert system["operating_days"] == [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
    ]
    assert system["non_operating_days"] == ["Sunday"]
