"""Read-only persistence verification for the assigned equivalent glazing."""

import hashlib
import json
import math
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
_SCRIPT_DIR = str(Path(__file__).resolve().parent)
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

EXPECTED_PROJECT_PREFIX = "sia4010_test1_1e_equivalent_glazing_disposable"
ASSIGNMENT_REPORT = Path("sia4010_artifacts/diagnostics/sia4010_test1e_equivalent_5layer_assignment.json")
PERSISTENCE_REPORT = Path("sia4010_artifacts/diagnostics/sia4010_test1e_equivalent_5layer_persistence.json")


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _close(expected, actual, tolerance):
    return math.isclose(float(expected), float(actual), abs_tol=tolerance, rel_tol=0.0)


def run():
    import iesve  # type: ignore

    from swiss_sia.reference_model.sia4010.test1e_awning_qualification import _live_targets
    from swiss_sia.reference_model.sia4010.test2a_shading_qualification import _assert_subset
    from swiss_sia.reference_model.ve_api import IesVeGateway

    project = iesve.VEProject.get_current_project()
    project_path = Path(str(getattr(project, "path", "") or "")).resolve()
    if not project_path.name.casefold().startswith(EXPECTED_PROJECT_PREFIX):
        raise RuntimeError("Open the saved equivalent-glazing disposable project first")

    assignment_path = project_path / ASSIGNMENT_REPORT
    checksum_path = assignment_path.with_suffix(assignment_path.suffix + ".sha256")
    if not assignment_path.is_file() or not checksum_path.is_file():
        raise RuntimeError("The checksum-bound assignment receipt is missing")
    expected_checksum = checksum_path.read_text(encoding="ascii").split()[0].lower()
    if expected_checksum != _sha256(assignment_path):
        raise RuntimeError("The assignment receipt checksum does not match")
    assignment = json.loads(assignment_path.read_text(encoding="utf-8"))
    if assignment.get("status") != "EQUIVALENT_5LAYER_ASSIGNED_AND_READBACK_VERIFIED":
        raise RuntimeError("The assignment receipt is not eligible for persistence verification")

    gateway = IesVeGateway(iesve)
    targets = _live_targets(gateway)
    construction_id = str(assignment["candidate_construction_id"])
    if any(target["construction_id"] != construction_id for target in targets):
        raise RuntimeError("The two target windows did not retain the equivalent construction")
    construction = gateway._get_construction(construction_id)
    properties = dict(construction.get_properties())
    shade_plan = dict(assignment["shade_plan"])
    # VE serializes its built-in NONE profile as either "NONE" or an empty
    # string.  The dynamic threshold expressions remain authoritative, so the
    # profile spelling itself is deliberately normalized here.
    comparable_shade_plan = {
        key: value for key, value in shade_plan.items()
        if key not in {
            "external_shade_profile",
            "external_shade_transmittance_90",
        }
    }
    try:
        _assert_subset(comparable_shade_plan, properties)
    except Exception as exc:
        reapplication_path = project_path / Path(
            "sia4010_artifacts/diagnostics/"
            "sia4010_test1e_equivalent_shade_reapplication.json"
        )
        reapplication_succeeded = False
        if reapplication_path.is_file():
            try:
                reapplication = json.loads(
                    reapplication_path.read_text(encoding="utf-8")
                )
                reapplication_succeeded = (
                    reapplication.get("status")
                    == "PERSISTED_CONSTRUCTION_SHADE_REAPPLIED_AND_READBACK_VERIFIED"
                )
            except (OSError, ValueError):
                pass
        if reapplication_succeeded:
            raise RuntimeError(
                "VE retained EXTW1 and both opening assignments, but reset the "
                "shade fields after both the initial write and the guarded "
                "second-session reapplication. Do not rerun either Python "
                "mutation. Open EXTW1 in APcdb, configure its External Shade "
                "dialog manually, save/close APcdb and the VE project, reopen, "
                "then run this verifier again. Details: {}".format(exc)
            ) from exc
        raise RuntimeError(
            "VE retained the equivalent glazing assignment but reset one or "
            "more shade fields. Run "
            "Run_VE_SIA4010_Test1E_Reapply_Equivalent_Shade_After_Reload.py, "
            "save, close, reopen, and verify again. Details: {}".format(exc)
        ) from exc
    actual_profile = str(properties.get("external_shade_profile", ""))
    if actual_profile.strip().casefold() not in {"", "none", "off"}:
        raise RuntimeError(
            "Dynamic shade requires an OFF/NONE profile; read back {!r}".format(
                actual_profile
            )
        )
    transmittance_90 = float(
        properties.get("external_shade_transmittance_90", -1.0)
    )
    if not (
        _close(0.0, transmittance_90, 1.0e-6)
        or _close(0.04, transmittance_90, 1.0e-6)
    ):
        raise RuntimeError(
            "The diagnostic 90-degree shade transmittance must be either 0.00 "
            "or 0.04; read back {}".format(transmittance_90)
        )

    layers = list(construction.get_layers())
    thicknesses = [float(dict(layer.get_properties())["thickness"]) for layer in layers]
    expected_thicknesses = [0.004, 0.014, 0.004, 0.014, 0.004]
    glass_thicknesses = thicknesses[0::2]
    cavity_thicknesses = thicknesses[1::2]
    glass_storage_is_explicit = all(
        _close(0.004, value, 1.0e-6) for value in glass_thicknesses
    )
    glass_storage_is_apcdb_zero = all(
        _close(0.0, value, 1.0e-6) for value in glass_thicknesses
    )
    cavities_are_exact = all(
        _close(0.014, value, 1.0e-6) for value in cavity_thicknesses
    )
    if (
        len(layers) != 5
        or not cavities_are_exact
        or not (glass_storage_is_explicit or glass_storage_is_apcdb_zero)
    ):
        raise RuntimeError(
            "The equivalent 4/14/4/14/4 layer stack did not persist exactly: "
            "layer_count={}, thicknesses_m={}, thicknesses_mm={}".format(
                len(layers),
                thicknesses,
                [value * 1000.0 for value in thicknesses],
            )
        )
    u_value = float(construction.get_u_factor(gateway._uvalue_type_iso()))
    g_value = float(properties["g_value"])
    visible_transmittance = float(properties["visible_light_transmittance"])
    if not _close(0.654, u_value, 0.001) or not _close(0.545, g_value, 1.0e-6) or not _close(0.742, visible_transmittance, 1.0e-6):
        raise RuntimeError(
            "Equivalent U/g/VT targets did not persist: U={}, g={}, VT={}, "
            "layer_thicknesses_mm={}".format(
                u_value,
                g_value,
                visible_transmittance,
                [value * 1000.0 for value in thicknesses],
            )
        )

    report_path = project_path / PERSISTENCE_REPORT
    report = {
        "schema_version": "1.0",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "EQUIVALENT_5LAYER_ASSIGNMENT_PERSISTENCE_VERIFIED",
        "project": str(project_path),
        "assignment_report": str(assignment_path),
        "assignment_report_sha256": expected_checksum,
        "construction_id": construction_id,
        "opening_ids": [target["opening_id"] for target in targets],
        "layer_thicknesses_m": thicknesses,
        "glass_layer_storage": (
            "EXPLICIT_4_MM"
            if glass_storage_is_explicit
            else "APCDB_ZERO_THICKNESS_WITH_DERIVED_PERFORMANCE_VERIFIED"
        ),
        "u_w_m2k": u_value,
        "g_value": g_value,
        "visible_light_transmittance": visible_transmittance,
        "shade_readback": {key: properties.get(key) for key in shade_plan},
        "angular_diagnostic_convention": (
            "The 90-degree value persisted as {:.6g}. Both 0.00 and 0.04 are "
            "accepted only as bounded diagnostic conventions because no "
            "authority-confirmed angular curve is available."
        ).format(transmittance_90),
        "model_changed_by_script": False,
        "project_saved_by_script": False,
        "compliance_claim_allowed": False,
        "next_action": "Capture and independently review this diagnostic template before ApacheSim.",
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    print("SIA 4010 TEST 1E EQUIVALENT GLAZING PERSISTENCE: {}".format(report["status"]))
    print("Construction: {}; openings: {}".format(construction_id, len(targets)))
    print("Layers: 4/14/4/14/4 mm")
    print("U: {}; g: {}; VT: {}".format(u_value, g_value, visible_transmittance))
    print("No VE object was changed and the project was not saved by the script.")
    print("Report: {}".format(report_path))
    print("NEXT: send this complete output before template capture and simulation.")
    print("This remains a diagnostic equivalent, not a Test 1 PASS.")
    return report_path


if __name__ == "__main__":
    run()
