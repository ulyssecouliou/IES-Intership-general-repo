"""
Client launcher for the Swiss SIA 380/2 compliance checker interface.

Use this file from the IESVE Scripts window with the Run button. It is the
default client deliverable: an SIA 380/2-only report. SIA 4010 validation
classes qualify the toolchain, not a client building, so they never appear
in this client report.

For the full internal report (SIA 380/2 + SIA 4010 readiness), use
Run_VE_Swiss_Compliance_Internal_SIA4010.py instead.
"""

import os
import sys
import importlib

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


if __name__ == "__main__":
    # VE can keep the Python interpreter alive between Run clicks. Reload the
    # package app so every Run uses the latest workspace code.
    module_name = "swiss_sia.app"
    if module_name in sys.modules:
        app = importlib.reload(sys.modules[module_name])
    else:
        app = importlib.import_module(module_name)
    if app.iesve is None:
        raise RuntimeError("Run this launcher inside IESVE VEScripts.")
    project = app.iesve.VEProject.get_current_project()
    if not project or not str(getattr(project, "path", "") or ""):
        raise RuntimeError("Open and save a VE project before launching the report interface.")

    ui_name = "swiss_sia.client_compliance_ui"
    if ui_name in sys.modules:
        client_ui = importlib.reload(sys.modules[ui_name])
    else:
        client_ui = importlib.import_module(ui_name)

    def run_client_reports(context, output_dir):
        """Run the client-only analysis requested by the native interface."""

        return app.main(
            include_sia4010=False,
            report_context=context,
            output_dir=output_dir,
            generate_html=False,
            raise_errors=True,
        )

    client_ui.launch_client_compliance_ui(
        str(project.path),
        app._current_project_weather_label(project),
        run_client_reports,
        capture_model_viewer=app.capture_model_viewer_image,
    )
