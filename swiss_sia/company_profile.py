"""Company identity used on the letterhead of the SIA compliance report.

The report is signed by an engineering office, so the office details and its
logo are project configuration, never hard-coded. A profile is loaded from
``config/company_profile.json``; when that file is absent the report still
renders, but every unset field is reported as unspecified rather than invented,
and the signature block stays visibly empty.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Union

CONFIG_NAME = "company_profile.json"
TEMPLATE_NAME = "company_profile.template.json"

_IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg"}


@dataclass(frozen=True)
class CompanyProfile:
    """Engineering-office identity printed on the report letterhead."""

    name: str = ""
    tagline: str = ""
    address_lines: Tuple[str, ...] = ()
    contact_lines: Tuple[str, ...] = ()
    logo_path: Optional[Path] = None
    author_name: str = ""
    author_role: str = ""
    report_reference: str = ""

    @property
    def is_configured(self) -> bool:
        """Return whether at least the office name is available."""

        return bool(self.name.strip())

    def to_dict(self) -> Dict[str, Any]:
        """Return the profile as serializable data."""

        return {
            "name": self.name,
            "tagline": self.tagline,
            "address_lines": list(self.address_lines),
            "contact_lines": list(self.contact_lines),
            "logo_path": str(self.logo_path) if self.logo_path else None,
            "author_name": self.author_name,
            "author_role": self.author_role,
            "report_reference": self.report_reference,
            "is_configured": self.is_configured,
        }


def _lines(payload: Dict[str, Any], key: str) -> Tuple[str, ...]:
    """Return a tuple of non-empty trimmed strings for one list-valued field."""

    value = payload.get(key)
    if isinstance(value, str):
        value = [value]
    if not isinstance(value, (list, tuple)):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def _resolve_logo(payload: Dict[str, Any], project_root: Path) -> Optional[Path]:
    """Return the logo path when it exists and is an embeddable image format."""

    raw = str(payload.get("logo_path") or "").strip()
    if not raw:
        return None
    candidate = Path(raw)
    if not candidate.is_absolute():
        candidate = project_root / candidate
    if candidate.is_file() and candidate.suffix.lower() in _IMAGE_SUFFIXES:
        return candidate
    return None


def load_company_profile(
    project_root: Union[str, Path], config_path: Optional[Union[str, Path]] = None
) -> CompanyProfile:
    """Load the office profile, returning an empty profile when unavailable.

    A malformed or missing file never raises: the report must still be produced,
    with the letterhead and signature block visibly unset so the reader can see
    that the office details were not supplied.
    """

    root = Path(project_root)
    path = Path(config_path) if config_path else root / "config" / CONFIG_NAME
    if not path.is_file():
        return CompanyProfile()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return CompanyProfile()
    if not isinstance(payload, dict):
        return CompanyProfile()
    return CompanyProfile(
        name=str(payload.get("name") or "").strip(),
        tagline=str(payload.get("tagline") or "").strip(),
        address_lines=_lines(payload, "address_lines"),
        contact_lines=_lines(payload, "contact_lines"),
        logo_path=_resolve_logo(payload, root),
        author_name=str(payload.get("author_name") or "").strip(),
        author_role=str(payload.get("author_role") or "").strip(),
        report_reference=str(payload.get("report_reference") or "").strip(),
    )
