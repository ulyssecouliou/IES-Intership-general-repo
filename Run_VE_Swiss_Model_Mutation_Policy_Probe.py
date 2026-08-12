"""VEScripts read-only launcher for the VE mutation-policy capability probe.

This launcher performs NO mutation.  It inspects the active VE project and
its CDB handle to prove that the runtime exposes every capability the
mutation policy assumes.  Its purpose is to move the "policy correctness"
claim from ``IMPLEMENTED_UNQUALIFIED`` to
``READY_FOR_REAL_VE_QUALIFICATION`` for a specific VE version, without
touching any model.

Usage inside VEScripts (VE 2025):

* open the client project as usual (read-only is fine)
* run this launcher via the Python Scripts navigator
* review the printed summary and the JSON report written under
  ``sia4010_evidence/model_mutation_probe/``.

The launcher never writes to the client project; it writes only to the
repository-local ``sia4010_evidence/`` folder and returns exit code 0
(overall PASS or WARNING) or 1 (overall FAIL).
"""

import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def run() -> int:
    """Run the probe against the currently open VE project."""

    try:
        import iesve  # type: ignore[import-not-found]
    except ImportError:
        print(
            "READY_FOR_REAL_VE_QUALIFICATION: iesve is unavailable outside "
            "VEScripts. Launch this script from inside VE 2025."
        )
        return 2

    from swiss_sia.reference_model.ve_mutation_policy_probe import (
        ProbeStatus,
        run_probe,
        write_probe_report,
    )

    project = getattr(iesve, "VEProject", None)
    if callable(project):
        try:
            project = iesve.VEProject()
        except Exception as exc:
            print("READY_FOR_REAL_VE_QUALIFICATION: cannot open VEProject: {}".format(exc))
            return 2
    if project is None:
        print("READY_FOR_REAL_VE_QUALIFICATION: no active VE project detected.")
        return 2

    project_id = getattr(project, "name", None) or getattr(project, "id", None)

    cdb_project = None
    for candidate in ("get_cdb_project", "cdb_project"):
        member = getattr(project, candidate, None)
        try:
            cdb_project = member() if callable(member) else member
        except Exception:
            cdb_project = None
        if cdb_project is not None:
            break

    report = run_probe(
        iesve_module=iesve,
        project=project,
        cdb_project=cdb_project,
        project_id=str(project_id) if project_id is not None else None,
    )
    output_dir = PROJECT_ROOT / "sia4010_evidence" / "model_mutation_probe"
    report_path = write_probe_report(report, str(output_dir))

    print("VE mutation-policy probe overall: {}".format(report.overall.value))
    print("Report written to: {}".format(report_path))
    for finding in report.findings:
        print(" - [{status}] {cid}: {detail}".format(
            status=finding.status.value,
            cid=finding.capability_id,
            detail=finding.detail,
        ))
    print(
        "This is a READY_FOR_REAL_VE_QUALIFICATION artifact. It does not "
        "constitute a SIA 4010 validation or an IES certification claim."
    )
    if report.overall is ProbeStatus.FAIL:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(run())
