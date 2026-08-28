"""Guarded disposable-project qualification of the Test 2A VE profile graph.

This operation mutates project profiles only.  It does not create geometry,
materials, constructions, templates, gains, shading controls, weather
assignments or simulations.  Every profile is created in dependency order and
read back exactly through the generic asset provisioner.  Existing reference
collisions fail before the first new object is created.
"""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Mapping, Tuple

from ..exceptions import ConfigurationError
from ..ve_asset_provisioner import IesVeAssetProvisioner
from .external_input_manifest import EXTERNAL_INPUT_FILENAME, external_input_readiness
from .model_scenario import ModelScenario
from .normalized_external_inputs import load_test2a_external_bindings
from .scenario_preflight import is_temporary_ve_project
from .test2a_profile_binding import build_test2a_profile_definitions

REPORT_SCHEMA_VERSION = "1.0"
SCENARIO_FILENAME = "sia_model_scenario.json"
REPORT_DIRECTORY = Path("sia4010_artifacts") / "diagnostics"


def _sha256(path: Path) -> str:
    """Return a lowercase SHA-256 digest."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    """Write deterministic UTF-8 JSON atomically."""

    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _profile_snapshot(project: Any) -> Tuple[Dict[str, str], ...]:
    """Return a bounded read-only identity snapshot of current profiles."""

    profiles_method = getattr(project, "profiles", None)
    if not callable(profiles_method):
        raise ConfigurationError("VEProject.profiles is unavailable")
    rows = []
    try:
        collections = profiles_method()
    except Exception as exc:
        raise ConfigurationError(
            "Unable to inspect project profiles: {}".format(exc)
        ) from exc
    for collection_index, collection in enumerate(collections or ()):
        if not isinstance(collection, Mapping):
            continue
        for identifier, profile in collection.items():
            rows.append(
                {
                    "collection_index": str(collection_index),
                    "identifier": str(identifier),
                    "reference": str(
                        getattr(
                            profile,
                            "reference",
                            getattr(profile, "name", ""),
                        )
                    ),
                    "python_type": "{}.{}".format(
                        type(profile).__module__,
                        type(profile).__name__,
                    ),
                }
            )
    return tuple(rows)


def qualify_test2a_profile_graph(
    iesve_module: Any,
    project: Any,
) -> Path:
    """Create and strictly read back the source-bound Test 2A profile graph."""

    project_path = Path(str(getattr(project, "path", "")))
    if not project_path.is_dir():
        raise ConfigurationError(
            "Test 2A profile qualification requires a saved VE project " "directory"
        )
    if is_temporary_ve_project(project_path):
        raise ConfigurationError(
            "Save a fresh disposable VE project outside the temporary VEPROJ "
            "folder before qualification"
        )
    required_methods = ("profiles", "create_profile", "save_profiles")
    missing_methods = [
        name for name in required_methods if not callable(getattr(project, name, None))
    ]
    if missing_methods:
        raise ConfigurationError(
            "Required VE profile API methods are missing: {}".format(missing_methods)
        )

    scenario_path = project_path / SCENARIO_FILENAME
    if not scenario_path.is_file():
        raise ConfigurationError(
            "Prepare test_2A/2A first; missing scenario file: {}".format(scenario_path)
        )
    scenario = ModelScenario.load(scenario_path)
    if (
        not scenario.is_official
        or scenario.variant != "test_2A"
        or scenario.case_id != "2A"
    ):
        raise ConfigurationError(
            "Profile qualification is restricted to the official " "test_2A/2A scenario"
        )

    readiness = external_input_readiness(
        project_path,
        "test_2A",
        "2A",
    )
    bindings = load_test2a_external_bindings(readiness)
    evidence_sha = dict(bindings.evidence_sha256)
    profile_binding_sha = evidence_sha["sia2024_office_3_1_standard_profiles"]
    profile_bundle = build_test2a_profile_definitions(
        bindings.office_profiles,
        source_sha256=profile_binding_sha,
    )

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    report_path = (
        project_path / REPORT_DIRECTORY / "sia2a_profiles_{}.json".format(timestamp)
    )
    external_manifest_path = project_path / EXTERNAL_INPUT_FILENAME
    before = _profile_snapshot(project)
    report: Dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "status": "STARTED",
        "project": {
            "name": str(getattr(project, "name", "")),
            "path": str(project_path),
        },
        "scenario": scenario.to_dict(),
        "source_contracts": {
            "scenario": {
                "path": str(scenario_path),
                "sha256": _sha256(scenario_path),
            },
            "external_manifest": {
                "path": str(external_manifest_path),
                "sha256": (
                    _sha256(external_manifest_path)
                    if external_manifest_path.is_file()
                    else ""
                ),
            },
            "normalized_binding_sha256": evidence_sha,
            "profile_graph_sha256": profile_bundle.graph_sha256,
        },
        "profile_plan": profile_bundle.to_dict(),
        "profiles_before": list(before),
        "profiles_after": [],
        "profile_ids": {},
        "output_profile_ids": {},
        "mutation_scope": "PROJECT_PROFILES_ONLY",
        "mutation_performed": False,
        "other_ve_objects_changed": False,
        "simulation_performed": False,
        "compliance_claim_allowed": False,
        "claim_guardrail": (
            "A PASS qualifies only native VE profile creation and read-back in "
            "this disposable project. It is not a Test 2A model, result, "
            "comparison, validation or SIA attestation."
        ),
    }
    # Leave a STARTED receipt before the first VE setter so a process crash is
    # distinguishable from a run that never entered the mutation boundary.
    _write_json(report_path, report)
    try:
        identifiers = IesVeAssetProvisioner(
            iesve_module,
            project,
            None,
        ).provision_profiles(
            profile_bundle.definitions,
            on_existing="fail",
        )
        after = _profile_snapshot(project)
        output_ids = {
            role: identifiers[node_key]
            for role, node_key in profile_bundle.output_profile_keys
        }
        report.update(
            {
                "status": "PASS",
                "profiles_after": list(after),
                "profile_ids": identifiers,
                "output_profile_ids": output_ids,
                "mutation_performed": True,
                "created_profile_count": len(identifiers),
            }
        )
    except Exception as exc:
        after_failure = _profile_snapshot(project)
        report.update(
            {
                "status": "FAIL",
                "error": "{}: {}".format(type(exc).__name__, exc),
                "profiles_after": list(after_failure),
                "mutation_performed": after_failure != before,
                "recovery_action": (
                    "Discard this project and repeat only in a fresh saved "
                    "disposable VE project after correcting the reported cause."
                ),
            }
        )
        _write_json(report_path, report)
        raise

    _write_json(report_path, report)
    checksum_path = report_path.with_suffix(report_path.suffix + ".sha256")
    checksum_path.write_text(
        "{}  {}\n".format(_sha256(report_path), report_path.name),
        encoding="ascii",
    )
    return report_path
