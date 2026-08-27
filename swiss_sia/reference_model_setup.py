"""Fail-closed preparation of a project-local reference-model input bundle.

This module does not import :mod:`iesve` and does not mutate a VE model.  It
copies the maintained reference inputs into an explicitly disposable project,
binds a user-selected EPW file, and records enough provenance to audit that
preparation step before the existing generator is run.
"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .compliance_hub import is_disposable_project


class ReferenceModelSetupError(RuntimeError):
    """Raised when a safe project-local bundle cannot be prepared."""


@dataclass(frozen=True)
class EpwMetadata:
    """Weather metadata that is stated by the EPW LOCATION header."""

    station: str
    region: str
    country: str
    data_source: str
    station_id: str
    latitude: Optional[float]
    longitude: Optional[float]
    time_zone: Optional[float]
    elevation_m: Optional[float]


@dataclass(frozen=True)
class SetupReceipt:
    """Auditable result of preparing, but not yet generating, a model."""

    project_path: str
    config_path: str
    asset_manifest_path: str
    weather_path: str
    weather_sha256: str
    weather_derivation_audit: Optional[str]
    audit_path: str
    config_backup: Optional[str]
    asset_manifest_backup: Optional[str]

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe receipt."""
        return asdict(self)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _number(value: str) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def read_epw_metadata(weather_file: Path) -> EpwMetadata:
    """Read only the standard EPW LOCATION header; never infer a scenario."""
    try:
        with weather_file.open("r", encoding="utf-8-sig", errors="replace") as stream:
            fields = stream.readline().strip().split(",")
    except OSError as exc:
        raise ReferenceModelSetupError(
            "Cannot read selected EPW file: {}".format(weather_file)
        ) from exc
    if len(fields) < 10 or fields[0].strip().upper() != "LOCATION":
        raise ReferenceModelSetupError(
            "Selected weather file has no valid EPW LOCATION header: {}".format(
                weather_file
            )
        )
    return EpwMetadata(
        station=fields[1].strip(),
        region=fields[2].strip(),
        country=fields[3].strip(),
        data_source=fields[4].strip(),
        station_id=fields[5].strip(),
        latitude=_number(fields[6]),
        longitude=_number(fields[7]),
        time_zone=_number(fields[8]),
        elevation_m=_number(fields[9]),
    )


def build_project_configuration(
    source_configuration: Dict[str, Any],
    local_weather: Path,
    weather_sha256: str,
    epw: EpwMetadata,
    climate_scenario: str = "",
) -> Dict[str, Any]:
    """Return a project configuration without stale client climate metadata."""
    configuration = json.loads(json.dumps(source_configuration))
    parameters = configuration.get("parameters")
    if not isinstance(parameters, dict):
        raise ReferenceModelSetupError(
            "Reference configuration has no parameters object."
        )

    def assign(name: str, value: Any, source: str, locator: str) -> None:
        record = parameters.get(name)
        if not isinstance(record, dict):
            raise ReferenceModelSetupError(
                "Reference configuration is missing parameter: {}".format(name)
            )
        record["value"] = value
        record["source"] = source
        record["source_locator"] = locator

    locator = "{}; SHA-256 {}".format(local_weather, weather_sha256)
    station = epw.station or "UNCONFIRMED_FROM_EPW"
    scenario = climate_scenario.strip() or "UNCONFIRMED_REVIEW_REQUIRED"
    assign(
        "asset_manifest_file",
        "reference_model_assets.json",
        "Project-local reference-model setup",
        "Active VE project folder",
    )
    assign(
        "weather_file",
        str(local_weather),
        "User-selected EPW; regulatory suitability not reviewed",
        locator,
    )
    assign("weather_station", station, "EPW LOCATION header", locator)
    assign(
        "weather_dataset_type",
        "EPW; regulatory suitability not reviewed",
        "Selected file format",
        locator,
    )
    assign(
        "climate_scenario",
        scenario,
        (
            "Reviewer-entered climate declaration"
            if climate_scenario.strip()
            else "Unresolved placeholder; reviewer confirmation required"
        ),
        locator,
    )
    if epw.latitude is not None:
        assign("site_latitude_degrees", epw.latitude, "EPW LOCATION header", locator)
    if epw.longitude is not None:
        assign("site_longitude_degrees", epw.longitude, "EPW LOCATION header", locator)

    metadata = configuration.setdefault("metadata", {})
    metadata["weather_compliance_review"] = "PENDING"
    metadata["prepared_from_repository_template"] = True
    metadata["setup_guardrail"] = (
        "Bundle preparation and model generation do not constitute SIA certification."
    )
    return configuration


def _backup(path: Path, stamp: str) -> Optional[Path]:
    if not path.exists():
        return None
    backup = path.with_name("{}.pre_setup_{}{}".format(path.stem, stamp, path.suffix))
    shutil.copy2(path, backup)
    return backup


def _write_json(path: Path, payload: Dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def prepare_reference_model_bundle(
    project_path: Path,
    repository_root: Path,
    weather_file: Path,
    climate_scenario: str = "",
) -> SetupReceipt:
    """Prepare source-traced local inputs and leave the VE model untouched."""
    project = Path(project_path).resolve()
    repository = Path(repository_root).resolve()
    selected_weather = Path(weather_file).resolve()
    if not project.is_dir():
        raise ReferenceModelSetupError("Active VE project folder does not exist.")
    if not is_disposable_project(str(project)):
        raise ReferenceModelSetupError(
            "Reference-model generation requires a project ending in _TEST, _COPY "
            "or _DISPOSABLE."
        )
    if not selected_weather.is_file():
        raise ReferenceModelSetupError("Selected weather file does not exist.")
    if selected_weather.suffix.casefold() != ".epw":
        raise ReferenceModelSetupError(
            "Select an EPW file. Other transports require a separate VE qualification."
        )

    source_config = repository / "config" / "reference_model_config.json"
    source_assets = repository / "config" / "reference_model_assets.json"
    if not source_config.is_file() or not source_assets.is_file():
        raise ReferenceModelSetupError(
            "Maintained reference configuration or asset manifest is missing."
        )
    try:
        config_payload = json.loads(source_config.read_text(encoding="utf-8"))
        assets_payload = json.loads(source_assets.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ReferenceModelSetupError("Maintained reference JSON is invalid.") from exc

    epw = read_epw_metadata(selected_weather)
    weather_hash = _sha256(selected_weather)
    local_weather = project / selected_weather.name
    if local_weather != selected_weather:
        if local_weather.exists() and _sha256(local_weather) != weather_hash:
            raise ReferenceModelSetupError(
                "A different weather file already has this name in the VE project."
            )
        if not local_weather.exists():
            shutil.copy2(selected_weather, local_weather)

    derivation_audit: Optional[Path] = None
    if selected_weather.stem.endswith("_IESVE_CANDIDATE"):
        expected_audit_name = (
            selected_weather.stem.replace("_IESVE_CANDIDATE", "_IESVE_DERIVATION")
            + ".json"
        )
        candidate_audit = selected_weather.with_name(expected_audit_name)
        if not candidate_audit.is_file():
            maintained_root = repository / "generated_weather"
            maintained_matches = (
                list(maintained_root.rglob(expected_audit_name))
                if maintained_root.is_dir()
                else []
            )
            if len(maintained_matches) == 1:
                candidate_audit = maintained_matches[0]
            else:
                raise ReferenceModelSetupError(
                    "Converted EPW candidate has no unique derivation audit beside "
                    "the file or under the repository generated_weather folder."
                )
        try:
            derivation_payload = json.loads(candidate_audit.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ReferenceModelSetupError(
                "Weather derivation audit is invalid."
            ) from exc
        audited_hash = str(
            derivation_payload.get("weather", {}).get("sha256", "")
        ).casefold()
        if derivation_payload.get("status") != "READY_FOR_IESVE_READ_ONLY_PROBE":
            raise ReferenceModelSetupError(
                "Weather derivation audit is not ready for an IESVE probe."
            )
        if not audited_hash or audited_hash != weather_hash.casefold():
            raise ReferenceModelSetupError(
                "Converted EPW checksum does not match its derivation audit."
            )
        weather_evidence_dir = project / "reference_model_artifacts" / "weather"
        weather_evidence_dir.mkdir(parents=True, exist_ok=True)
        derivation_audit = weather_evidence_dir / candidate_audit.name
        shutil.copy2(candidate_audit, derivation_audit)

    config_payload = build_project_configuration(
        config_payload,
        local_weather,
        weather_hash,
        epw,
        climate_scenario=climate_scenario,
    )
    destination_config = project / "reference_model_config.json"
    destination_assets = project / "reference_model_assets.json"
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    config_backup = _backup(destination_config, stamp)
    assets_backup = _backup(destination_assets, stamp)
    _write_json(destination_config, config_payload)
    _write_json(destination_assets, assets_payload)

    audit_dir = project / "reference_model_artifacts" / "setup"
    audit_dir.mkdir(parents=True, exist_ok=True)
    audit_path = audit_dir / "reference_model_setup_{}.json".format(stamp)
    receipt = SetupReceipt(
        project_path=str(project),
        config_path=str(destination_config),
        asset_manifest_path=str(destination_assets),
        weather_path=str(local_weather),
        weather_sha256=weather_hash,
        weather_derivation_audit=(str(derivation_audit) if derivation_audit else None),
        audit_path=str(audit_path),
        config_backup=str(config_backup) if config_backup else None,
        asset_manifest_backup=str(assets_backup) if assets_backup else None,
    )
    audit_payload = receipt.to_dict()
    audit_payload.update(
        {
            "status": "READY_FOR_FAIL_CLOSED_GENERATION",
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "epw_location_header": asdict(epw),
            "climate_scenario": climate_scenario.strip() or None,
            "weather_compliance_review": "PENDING",
            "ve_model_mutated": False,
            "claim_guardrail": (
                "This setup receipt is not an SIA certificate or SIA 4010 validation."
            ),
        }
    )
    _write_json(audit_path, audit_payload)
    return receipt
