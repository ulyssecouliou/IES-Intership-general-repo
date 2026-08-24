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
BUILDING_STRATEGY_DECLARATIONS = frozenset({"YES", "NO", "TO_CONFIRM"})
SHADING_DECLARATIONS = BUILDING_STRATEGY_DECLARATIONS

BUILDING_STRATEGY_TEXT = {
    "client_ui_strategy_title": {
        "en": "Building strategy",
        "de": "Gebaeudestrategie",
        "fr": "Strategie du batiment",
        "it": "Strategia dell'edificio",
    },
    "client_ui_strategy_help": {
        "en": "Describe what is actually intended for this model. These declarations are saved per VE project and do not replace model evidence.",
        "de": "Beschreiben Sie, was fuer dieses Modell tatsaechlich vorgesehen ist. Diese Angaben werden je VE-Projekt gespeichert und ersetzen keine Modellnachweise.",
        "fr": "Indiquez ce qui est reellement prevu pour ce modele. Ces declarations sont enregistrees par projet VE et ne remplacent pas les preuves du modele.",
        "it": "Indicare cio che e realmente previsto per questo modello. Le dichiarazioni sono salvate per progetto VE e non sostituiscono le prove del modello.",
    },
    "client_ui_strategy_solar": {
        "en": "External solar protection / blinds",
        "de": "Aussenliegender Sonnenschutz / Storen",
        "fr": "Protections solaires exterieures / stores",
        "it": "Schermature solari esterne / tende",
    },
    "client_ui_strategy_windows": {
        "en": "Windows intended to be operable",
        "de": "Fenster sollen oeffenbar sein",
        "fr": "Fenetres prevues ouvrables",
        "it": "Finestre previste apribili",
    },
    "client_ui_strategy_cooling": {
        "en": "Mechanical cooling intended",
        "de": "Mechanische Kuehlung vorgesehen",
        "fr": "Refroidissement mecanique prevu",
        "it": "Raffrescamento meccanico previsto",
    },
    "client_ui_strategy_notes": {
        "en": "Design notes (controls, setpoints, capacities)",
        "de": "Planungshinweise (Regelung, Sollwerte, Leistungen)",
        "fr": "Notes de conception (regulation, consignes, capacites)",
        "it": "Note di progetto (controlli, setpoint, capacita)",
    },
    "field_building_strategy": {
        "en": "Building strategy",
        "de": "Gebaeudestrategie",
        "fr": "Strategie du batiment",
        "it": "Strategia dell'edificio",
    },
    "field_window_operability": {
        "en": "Operable windows",
        "de": "Oeffenbare Fenster",
        "fr": "Fenetres ouvrables",
        "it": "Finestre apribili",
    },
    "field_mechanical_cooling": {
        "en": "Mechanical cooling",
        "de": "Mechanische Kuehlung",
        "fr": "Refroidissement mecanique",
        "it": "Raffrescamento meccanico",
    },
}


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
    window_operability: str = "TO_CONFIRM"
    mechanical_cooling: str = "TO_CONFIRM"
    building_strategy_notes: str = ""
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
        shading = normalize_building_strategy_declaration(self.solar_shading)
        operability = normalize_building_strategy_declaration(
            self.window_operability
        )
        cooling = normalize_building_strategy_declaration(self.mechanical_cooling)
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
            window_operability=operability,
            mechanical_cooling=cooling,
            building_strategy_notes=str(
                self.building_strategy_notes or ""
            ).strip(),
            client_logo_path=str(self.client_logo_path or "").strip(),
            model_viewer_image_path=str(self.model_viewer_image_path or "").strip(),
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe record."""

        return asdict(self.normalized())


def normalize_building_strategy_declaration(value: Any) -> str:
    """Return one fail-closed YES/NO/TO_CONFIRM project declaration."""

    normalized = str(value or "TO_CONFIRM").strip().upper()
    if normalized not in BUILDING_STRATEGY_DECLARATIONS:
        return "TO_CONFIRM"
    return normalized


def building_strategy_text(key: str, language: str = "en") -> str:
    """Return a localized building-strategy label without changing the shared catalogue."""

    code = str(language or "en").strip().lower()
    if code not in {"de", "en", "fr", "it"}:
        code = "en"
    values = BUILDING_STRATEGY_TEXT.get(str(key or ""), {})
    return values.get(code) or values.get("en") or str(key or "")


def building_strategy_summary(context: Any, language: str = "en") -> str:
    """Return the compact strategy string printed on report cover pages."""

    labels = {
        "en": ("Shading", "Windows", "Cooling"),
        "de": ("Sonnenschutz", "Fenster", "Kuehlung"),
        "fr": ("Stores", "Fenetres", "Froid"),
        "it": ("Schermature", "Finestre", "Raffrescamento"),
    }
    code = str(language or "en").strip().lower()
    if code not in labels:
        code = "en"
    getter = (
        (lambda key: context.get(key, "TO_CONFIRM"))
        if isinstance(context, dict)
        else (lambda key: getattr(context, key, "TO_CONFIRM"))
    )
    values = (
        normalize_building_strategy_declaration(getter("solar_shading")),
        normalize_building_strategy_declaration(getter("window_operability")),
        normalize_building_strategy_declaration(getter("mechanical_cooling")),
    )
    return " | ".join(
        "{}: {}".format(label, value)
        for label, value in zip(labels[code], values)
    )


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
