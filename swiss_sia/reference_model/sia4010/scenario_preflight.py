"""Fail-closed preflight for scenario-driven SIA 4010 model creation."""

import hashlib
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Union

from ..exceptions import ConfigurationError
from .case_manifest import Sia4010CaseManifest
from .model_scenario import ModelScenario


def _sha256(path: Path) -> str:
    """Return the uppercase hexadecimal SHA-256 checksum of one file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def resolve_scenario_path(value: str, project_root: Path, repository_root: Path) -> Path:
    """Resolve a configured path without silently searching arbitrary folders."""

    path = Path(value)
    if path.is_absolute():
        return path
    project_candidate = project_root / path
    repository_candidate = repository_root / path
    if project_candidate.is_file():
        return project_candidate
    if repository_candidate.is_file():
        return repository_candidate
    return project_candidate


def is_temporary_ve_project(project_root: Union[str, Path]) -> bool:
    """Return whether VE is using its unsaved-project temporary directory."""

    project = Path(project_root)
    try:
        project_text = str(project.resolve()).casefold()
        temp_text = str(Path(tempfile.gettempdir()).resolve()).casefold()
    except OSError:
        project_text = str(project).casefold()
        temp_text = str(Path(tempfile.gettempdir())).casefold()
    return project_text.startswith(temp_text) and "\\veproj\\" in project_text


@dataclass(frozen=True)
class ScenarioPreflight:
    """Machine-readable decision before geometry generation or VE mutation."""

    status: str
    scenario: Dict[str, Any]
    files: Dict[str, Dict[str, Any]]
    blockers: List[str]
    warnings: List[str]

    @property
    def allows_mutation(self) -> bool:
        """Return whether the preflight cleared the scenario for VE mutation."""

        return self.status in {
            "READY_FOR_VE_MUTATION",
            "READY_FOR_PROVISIONAL_VE_MUTATION",
        }

    def to_dict(self) -> Dict[str, Any]:
        """Return the preflight outcome as serializable data."""

        return {
            "status": self.status,
            "scenario": self.scenario,
            "files": self.files,
            "blockers": list(self.blockers),
            "warnings": list(self.warnings),
            "allows_mutation": self.allows_mutation,
        }


def evaluate_scenario(
    scenario: ModelScenario,
    project_root: Union[str, Path],
    repository_root: Union[str, Path],
) -> ScenarioPreflight:
    """Evaluate official inputs and asset provenance before any VE write."""

    project = Path(project_root)
    repository = Path(repository_root)
    configured_paths = {
        "case_manifest_file": scenario.files.case_manifest_file,
        "ve_config_file": scenario.files.ve_config_file,
        "ve_asset_manifest_file": scenario.files.ve_asset_manifest_file,
    }
    files: Dict[str, Dict[str, Any]] = {}
    blockers: List[str] = []
    warnings: List[str] = []
    temporary_project = is_temporary_ve_project(project)
    if temporary_project:
        warnings.append(
            "The active VE project is unsaved and uses the temporary VEPROJ "
            "folder. Save it as a disposable permanent project before mutation."
        )
    resolved: Dict[str, Path] = {}
    for key, value in configured_paths.items():
        path = resolve_scenario_path(value, project, repository)
        resolved[key] = path
        exists = path.is_file()
        files[key] = {
            "configured": value,
            "resolved": str(path),
            "exists": exists,
            "sha256": _sha256(path) if exists else None,
        }

    manifest_path = resolved["case_manifest_file"]
    if not manifest_path.is_file():
        blockers.append("Missing SIA 4010 case manifest: {}".format(manifest_path))
        return ScenarioPreflight(
            status="BLOCKED_CONFIGURATION",
            scenario=scenario.to_dict(),
            files=files,
            blockers=blockers,
            warnings=warnings,
        )
    manifest = Sia4010CaseManifest.load(manifest_path)
    readiness = scenario.readiness(manifest)
    if readiness["missing_parameters"]:
        blockers.append(
            "Official parameters remain unresolved: {}".format(
                ", ".join(readiness["missing_parameters"])
            )
        )
    if readiness["provisional_parameters"]:
        warnings.append(
            "Public-reference parameters are usable for MVP demonstration but "
            "do not permit a normative compliance claim: {}".format(
                ", ".join(readiness["provisional_parameters"])
            )
        )

    if scenario.execution_mode == "PREPARE_ONLY":
        if not resolved["ve_config_file"].is_file():
            warnings.append(
                "VE configuration is not needed for geometry preparation but "
                "will be required for project creation."
            )
        if not resolved["ve_asset_manifest_file"].is_file():
            warnings.append(
                "VE asset manifest is not needed for geometry preparation but "
                "will be required for project creation."
            )
        return ScenarioPreflight(
            status="READY_FOR_PREPARATION",
            scenario={**scenario.to_dict(), "input_readiness": readiness},
            files=files,
            blockers=blockers,
            warnings=warnings,
        )

    for key in ("ve_config_file", "ve_asset_manifest_file"):
        if not resolved[key].is_file():
            blockers.append("Missing required file: {}".format(resolved[key]))
    if temporary_project:
        blockers.append("VE mutation is forbidden in the unsaved temporary VEPROJ folder")

    asset_path = resolved["ve_asset_manifest_file"]
    if scenario.is_official and asset_path.is_file():
        try:
            asset_payload = json.loads(asset_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ConfigurationError(
                "Invalid VE asset manifest for scenario: {}".format(exc)
            ) from exc
        metadata = asset_payload.get("metadata", {})
        expected = {
            "compliance_scope": "SIA4010_OFFICIAL",
            "sia4010_variant": scenario.variant,
            "sia4010_case_id": scenario.case_id,
        }
        mismatches = {
            key: {"expected": value, "actual": metadata.get(key)}
            for key, value in expected.items()
            if metadata.get(key) != value
        }
        if mismatches:
            blockers.append(
                "VE asset manifest is not provenance-tagged for this exact "
                "official case: {}".format(mismatches)
            )

    if blockers:
        status = "BLOCKED_CONFIGURATION"
    elif readiness["provisional_parameters"]:
        status = "READY_FOR_PROVISIONAL_VE_MUTATION"
    else:
        status = "READY_FOR_VE_MUTATION"
    return ScenarioPreflight(
        status=status,
        scenario={**scenario.to_dict(), "input_readiness": readiness},
        files=files,
        blockers=blockers,
        warnings=warnings,
    )
