"""Project-local client information used by the SIA report interface.

The client-facing fields are descriptive evidence, not normative inputs.  In
particular, the user's solar-shading declaration is printed in the reports but
never replaces the shading objects read from the VE model.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import asdict, dataclass, replace
from pathlib import Path
from typing import Any, Dict, Optional, Union


CONTEXT_DIR_NAME = ".sia_compliance"
CONTEXT_FILE_NAME = "client_report_context.json"
REPORT_DIR_NAME = "SIA Compliance Reports"
ASSET_DIR_NAME = "report_assets"
IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg"})
SHADING_DECLARATIONS = frozenset({"YES", "NO", "TO_CONFIRM"})


@dataclass(frozen=True)
class ClientReportContext:
    """User-entered identification and presentation data for one VE project."""

    client_name: str = ""
    project_name: str = ""
    project_address: str = ""
    client_contact: str = ""
    report_reference: str = ""
    prepared_by: str = ""
    language: str = "en"
    language_selected: bool = False
    weather_file: str = ""
    solar_shading: str = "TO_CONFIRM"
    client_logo_path: str = ""
    model_viewer_image_path: str = ""

    @property
    def report_directory_name(self) -> str:
        """Return the fixed, readable report folder name."""

        return REPORT_DIR_NAME

    def normalized(self) -> "ClientReportContext":
        """Return trimmed, validated values without inventing missing fields."""

        language = str(self.language or "en").strip().lower()
        if language not in {"de", "en", "fr", "it"}:
            language = "en"
        shading = str(self.solar_shading or "TO_CONFIRM").strip().upper()
        if shading not in SHADING_DECLARATIONS:
            shading = "TO_CONFIRM"
        return ClientReportContext(
            client_name=str(self.client_name or "").strip(),
            project_name=str(self.project_name or "").strip(),
            project_address=str(self.project_address or "").strip(),
            client_contact=str(self.client_contact or "").strip(),
            report_reference=str(self.report_reference or "").strip(),
            prepared_by=str(self.prepared_by or "").strip(),
            language=language,
            language_selected=self.language_selected is True,
            weather_file=str(self.weather_file or "").strip(),
            solar_shading=shading,
            client_logo_path=str(self.client_logo_path or "").strip(),
            model_viewer_image_path=str(self.model_viewer_image_path or "").strip(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe record."""

        return asdict(self.normalized())


def context_path(project_path: Union[str, Path]) -> Path:
    """Return the project-local context file path."""

    return Path(project_path) / CONTEXT_DIR_NAME / CONTEXT_FILE_NAME


def report_directory(project_path: Union[str, Path]) -> Path:
    """Return the project-local directory holding the two client reports."""

    return Path(project_path) / REPORT_DIR_NAME


def _usable_image(path: Union[str, Path, None]) -> Optional[Path]:
    """Return an existing supported raster image path, if supplied."""

    if not path:
        return None
    candidate = Path(path)
    if candidate.is_file() and candidate.suffix.lower() in IMAGE_SUFFIXES:
        return candidate
    return None


def _copy_asset(source: Optional[Path], destination_dir: Path, stem: str) -> str:
    """Copy one selected image beside the project reports and return its path."""

    if source is None:
        return ""
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / (stem + source.suffix.lower())
    if source.resolve() != destination.resolve():
        shutil.copy2(source, destination)
    return str(destination)


def save_client_report_context(
    project_path: Union[str, Path], context: ClientReportContext
) -> ClientReportContext:
    """Persist client information and project-local copies of selected images."""

    root = Path(project_path)
    normalized = context.normalized()
    assets = root / CONTEXT_DIR_NAME / ASSET_DIR_NAME
    local_logo = _copy_asset(
        _usable_image(normalized.client_logo_path), assets, "client_logo"
    )
    local_viewer = _copy_asset(
        _usable_image(normalized.model_viewer_image_path),
        assets,
        "model_viewer",
    )
    stored = replace(
        normalized,
        client_logo_path=local_logo,
        model_viewer_image_path=local_viewer,
    )
    destination = context_path(root)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(stored.to_dict(), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return stored


def load_client_report_context(
    project_path: Union[str, Path]
) -> ClientReportContext:
    """Load saved project information, degrading safely on malformed content."""

    path = context_path(project_path)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError):
        return ClientReportContext()
    if not isinstance(payload, dict):
        return ClientReportContext()
    allowed = ClientReportContext.__dataclass_fields__
    values = {key: value for key, value in payload.items() if key in allowed}
    return ClientReportContext(**values).normalized()
