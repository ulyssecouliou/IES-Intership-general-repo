"""Tests for the read-only per-project MacroFlo strategy probe."""

from __future__ import annotations

from pathlib import Path

from Run_VE_SIA3802_Probe_MacroFlo_Strategy import _strategy_status


ROOT = Path(__file__).resolve().parents[1]


def test_strategy_status_requires_real_window_assignments() -> None:
    windows = [{"opening_id": "WIN-1", "macroflo_id": ""}]

    assert _strategy_status("YES", windows, []) == "MISSING_MACROFLO_ASSIGNMENTS"
    assert _strategy_status("NO", windows, []) == "OPERABLE_WINDOWS_NOT_DECLARED"
    assert (
        _strategy_status("YES", [{"macroflo_id": "MF-1"}], [{"id": "MF-1"}])
        == "MACROFLO_ASSIGNMENTS_PRESENT_REVIEW_PAYLOAD"
    )


def test_probe_source_never_invokes_the_macroflo_setter_or_project_save() -> None:
    source = (
        ROOT / "Run_VE_SIA3802_Probe_MacroFlo_Strategy.py"
    ).read_text(encoding="utf-8")

    assert "macroflo.set(" not in source
    assert ".save_project(" not in source
    assert '"mutation_performed": False' in source
    assert '"project_saved": False' in source
