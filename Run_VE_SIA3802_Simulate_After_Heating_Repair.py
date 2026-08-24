"""Run a guarded annual ApacheSim after the classroom heating repair.

The user must save the active ``_TEST`` project once before running this file.
The launcher verifies the repair receipt and live room controls, requests an
annual 30-minute APS with the outputs used by the compliance product, refuses
to overwrite an existing APS, verifies the completed ResultsReader contract,
and restores the previous ApacheSim options.  No physical model value or
weather assignment is changed.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

TEMPLATE_NAME = "SIA2024_4.01_CLASSROOM_REFERENCE"
EXPECTED_ROOM_IDS = {"SP000000", "SP000001", "SP000002"}
EXPECTED_HEATING_PROFILE = "HVSS0001"
REPAIR_PATH = PROJECT_ROOT / "outputs" / "sia3802_classroom_heating_repair.json"
RECEIPT_PATH = PROJECT_ROOT / "outputs" / "sia3802_post_repair_apachesim.json"
REPORTING_INTERVAL_30_MIN = 2
EXPECTED_RESULTS_PER_DAY = 48
EXPECTED_RESULT_POINTS = 365 * EXPECTED_RESULTS_PER_DAY


def _write(payload: dict[str, Any]) -> None:
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = RECEIPT_PATH.with_suffix(".json.tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(RECEIPT_PATH)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _normalized(path: Any) -> str:
    return str(Path(str(path or "")).resolve()).rstrip("\\/").lower()


def _load_repair(project: Any) -> dict[str, Any]:
    if not REPAIR_PATH.is_file():
        raise RuntimeError("Heating repair receipt is missing: {}".format(REPAIR_PATH))
    receipt = json.loads(REPAIR_PATH.read_text(encoding="utf-8"))
    if receipt.get("status") != "APPLIED_AND_READBACK_VERIFIED":
        raise RuntimeError("Heating repair is not read-back verified.")
    if _normalized(receipt.get("project_path")) != _normalized(project.path):
        raise RuntimeError("Heating repair receipt belongs to another VE project.")
    return receipt


def _live_controls(project: Any) -> list[dict[str, Any]]:
    model = project.models[0]
    rooms = []
    for body in model.get_bodies(False):
        room_data = body.get_room_data()
        general = dict(room_data.get_general())
        if str(general.get("thermal_template_name") or "") != TEMPLATE_NAME:
            continue
        conditions = dict(room_data.get_room_conditions())
        systems = dict(room_data.get_apache_systems())
        rooms.append(
            {
                "id": str(general.get("id") or getattr(body, "id", "")),
                "name": str(getattr(body, "name", "")),
                "heating_profile": str(conditions.get("heating_profile") or ""),
                "heating_profile_from_template": conditions.get(
                    "heating_profile_from_template"
                ),
                "heating_setpoint": conditions.get("heating_setpoint"),
                "heating_capacity_unlimited": systems.get(
                    "heating_capacity_unlimited"
                ),
                "system_air_minimum_flowrate": systems.get(
                    "system_air_minimum_flowrate"
                ),
            }
        )
    ids = {room["id"] for room in rooms}
    if ids != EXPECTED_ROOM_IDS:
        raise RuntimeError(
            "Live repair scope mismatch: expected {}, found {}.".format(
                sorted(EXPECTED_ROOM_IDS), sorted(ids)
            )
        )
    for room in rooms:
        if room["heating_profile"] != EXPECTED_HEATING_PROFILE:
            raise RuntimeError(
                "Room {!r} no longer uses {}.".format(
                    room["name"], EXPECTED_HEATING_PROFILE
                )
            )
        if room["heating_profile_from_template"] is not True:
            raise RuntimeError("Room {!r} lost template inheritance.".format(room["name"]))
        if room["heating_setpoint"] != 21.0:
            raise RuntimeError("Room {!r} setpoint drifted from 21 C.".format(room["name"]))
        if room["system_air_minimum_flowrate"] != 0.0:
            raise RuntimeError("Room {!r} has duplicate system air.".format(room["name"]))
    return rooms


def _confirm(results_name: str) -> bool:
    import tkinter as tk
    from tkinter import messagebox

    root = tk.Tk()
    root.withdraw()
    approved = messagebox.askyesno(
        "Run annual post-repair ApacheSim",
        (
            "Confirm that you pressed Ctrl+S after the heating-profile repair.\n\n"
            "ApacheSim will run 1 January through 31 December with 30-minute "
            "reporting and create:\n{}\n\n"
            "The active weather and physical model will not be changed. "
            "Run now?"
        ).format(results_name),
        parent=root,
    )
    root.destroy()
    return bool(approved)


def _wait_for_file(path: Path, timeout_seconds: float = 20.0) -> None:
    deadline = time.monotonic() + timeout_seconds
    while not (path.is_file() and path.stat().st_size > 0):
        if time.monotonic() >= deadline:
            raise RuntimeError("ApacheSim returned without an APS: {}".format(path))
        time.sleep(0.2)


def run() -> None:
    try:
        import iesve  # type: ignore
    except Exception as exc:
        raise RuntimeError("Run this file inside IESVE 2025 VEScripts.") from exc

    project = iesve.VEProject.get_current_project()
    if not project or not getattr(project, "models", None):
        raise RuntimeError("Open and save SIA_compatible_model_TEST first.")
    if "_TEST" not in (str(project.name) + str(project.path)).upper():
        raise RuntimeError("The active project is not the guarded _TEST copy.")
    project_path = Path(str(project.path)).resolve()
    if not project_path.is_dir():
        raise RuntimeError("The active VE project is not saved to disk.")

    repair = _load_repair(project)
    rooms = _live_controls(project)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_name = "SIA_compatible_model_post_heating_fix_{}.aps".format(stamp)
    results_path = project_path / "Vista" / results_name
    if results_path.exists():
        raise RuntimeError("Refusing to overwrite APS: {}".format(results_path))

    simulator = iesve.ApacheSim()
    for method in ("get_options", "set_options", "run_simulation"):
        if not callable(getattr(simulator, method, None)):
            raise RuntimeError("ApacheSim.{} is unavailable.".format(method))
    before_options = dict(simulator.get_options())
    required_option_names = {
        "start_day",
        "start_month",
        "end_day",
        "end_month",
        "reporting_interval",
        "results_filename",
    }
    missing = sorted(required_option_names - set(before_options))
    if missing:
        raise RuntimeError("Required ApacheSim options are missing: {}".format(missing))

    requested = {
        "start_day": 1,
        "start_month": 1,
        "end_day": 31,
        "end_month": 12,
        "reporting_interval": REPORTING_INTERVAL_30_MIN,
        "results_filename": results_name,
    }
    for name, value in (
        ("output_standard_outputs", True),
        ("output_sensible_internal_gains", True),
        ("output_HVAC_systems", True),
        ("detailed_rooms", sorted(EXPECTED_ROOM_IDS)),
        ("detailed_standard_outputs", True),
        ("detailed_HVAC_systems", True),
    ):
        if name in before_options:
            requested[name] = value
    restore_options = {name: before_options[name] for name in requested}
    base = {
        "schema_version": "1.0",
        "operation": "sia3802_post_repair_annual_apachesim",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "READY_FOR_CONFIRMATION",
        "project_name": str(project.name),
        "project_path": str(project_path),
        "repair_receipt": str(REPAIR_PATH),
        "repair_status": repair.get("status"),
        "live_rooms": rooms,
        "requested_options": requested,
        "options_before": before_options,
        "physical_model_mutated": False,
        "weather_mutated": False,
    }
    _write(base)
    if not _confirm(results_name):
        base["status"] = "CANCELLED_NO_SIMULATION"
        _write(base)
        print("POST-REPAIR APACHESIM: CANCELLED")
        return

    restored = False
    reader = None
    try:
        if simulator.set_options(requested) is not True:
            raise RuntimeError("ApacheSim rejected the annual options.")
        readback = dict(simulator.get_options())
        mismatch = {
            key: {"requested": value, "readback": readback.get(key)}
            for key, value in requested.items()
            if readback.get(key) != value
        }
        if mismatch:
            raise RuntimeError("ApacheSim option read-back mismatch: {}".format(mismatch))
        if simulator.run_simulation(queue_to_tasks=False) is not True:
            status_path = project_path / "apache" / "status.json"
            detail = status_path.read_text(encoding="utf-8") if status_path.is_file() else ""
            raise RuntimeError("ApacheSim failed: {}".format(detail))
        _wait_for_file(results_path)
        reader = iesve.ResultsReader.open(results_name)
        results_per_day = int(getattr(reader, "results_per_day", 0) or 0)
        first_day = int(getattr(reader, "first_day", 0) or 0)
        last_day = int(getattr(reader, "last_day", 0) or 0)
        if (results_per_day, first_day, last_day) != (
            EXPECTED_RESULTS_PER_DAY,
            1,
            365,
        ):
            raise RuntimeError(
                "APS temporal contract mismatch: results/day={}, days={}-{}.".format(
                    results_per_day, first_day, last_day
                )
            )
        weather_file = str(getattr(reader, "weather_file", "") or "")
        result = {
            **base,
            "status": "SIMULATION_AND_APS_VERIFIED",
            "options_after": readback,
            "results_path": str(results_path),
            "results_size_bytes": results_path.stat().st_size,
            "results_sha256": _sha256(results_path),
            "results_per_day": results_per_day,
            "expected_result_points_per_room": EXPECTED_RESULT_POINTS,
            "first_day": first_day,
            "last_day": last_day,
            "weather_file": weather_file,
        }
    except Exception as exc:
        result = {
            **base,
            "status": "FAIL",
            "error": "{}: {}".format(type(exc).__name__, exc),
            "results_path": str(results_path),
        }
        raise
    finally:
        if reader is not None:
            try:
                reader.close()
            except Exception:
                pass
        try:
            restored = simulator.set_options(restore_options) is True
        finally:
            result["apache_options_restored"] = restored
            _write(result)
    if not restored:
        raise RuntimeError("Simulation succeeded but ApacheSim options were not restored.")

    print("=" * 78)
    print("POST-REPAIR APACHESIM: SIMULATION_AND_APS_VERIFIED")
    print("APS: {}".format(results_path))
    print("Period: day 1 through 365")
    print("Resolution: 48 results/day (17,520 points/room)")
    print("Weather: {}".format(result["weather_file"]))
    print("ApacheSim options restored: YES")
    print("Receipt: {}".format(RECEIPT_PATH))
    print("=" * 78)


if __name__ == "__main__":
    run()
