"""VEScripts launcher that safely prepares then runs the reference model."""

from __future__ import annotations

import runpy
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Pick up setup fixes between VEScripts Run clicks without requiring a VE
# restart. The generator already performs the same refresh for its own modules.
for module_name in tuple(sys.modules):
    if module_name in {
        "swiss_sia.reference_model_setup",
        "swiss_sia.reference_model_setup_ui",
    }:
        del sys.modules[module_name]


def run():
    print("SWISS REFERENCE MODEL SETUP: STARTED")
    try:
        import iesve  # type: ignore
    except Exception as exc:
        raise RuntimeError("Run this launcher inside IESVE VEScripts.") from exc

    project = iesve.VEProject.get_current_project()
    raw_project_path = str(getattr(project, "path", "") or "") if project else ""
    if not raw_project_path:
        raise RuntimeError("Open and save a disposable VE project first.")
    project_path = Path(raw_project_path)

    from swiss_sia.reference_model_setup_ui import launch_reference_model_setup

    def generate(_receipt):
        print("Reference-model input bundle: READY")
        reader = iesve.WeatherFileReader()
        try:
            opened = int(reader.open_weather_file(str(_receipt.weather_path)))
            if opened <= 0:
                raise RuntimeError(
                    "IESVE WeatherFileReader rejected {}".format(_receipt.weather_path)
                )
            number_of_days = 366 if int(reader.feb29) else 365
            dry_bulb = reader.get_results(3, 1, number_of_days)
            if len(dry_bulb) != 8760:
                raise RuntimeError(
                    "IESVE weather read-back returned {} records; expected 8760".format(
                        len(dry_bulb)
                    )
                )
            print("IESVE read-only weather qualification: PASS (8760 records)")
        finally:
            try:
                reader.close()
            except Exception:
                pass
        print("Starting the existing fail-closed VE generator...")
        return runpy.run_path(
            str(PROJECT_ROOT / "Run_VE_Swiss_Reference_Model.py"),
            run_name="__main__",
        )

    return launch_reference_model_setup(project_path, PROJECT_ROOT, generate)


if __name__ == "__main__":
    run()
