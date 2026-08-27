"""Release-path policy: production code must not depend on one user's folders."""

from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
USER_PATH = re.compile(r"(?i)(?:[a-z]:[\\/]+users[\\/]|IES Internship)")
PRODUCTION_ROOTS = (
    ROOT / "swiss_sia",
    ROOT / "config",
    ROOT / "templates",
    ROOT / "scripts",
)


def test_production_files_do_not_embed_user_specific_absolute_paths() -> None:
    offenders = []
    for base in PRODUCTION_ROOTS:
        for path in base.rglob("*"):
            if not path.is_file() or "legacy" in path.parts:
                continue
            if path.suffix.lower() not in {
                ".py",
                ".json",
                ".yaml",
                ".yml",
                ".toml",
                ".ini",
                ".cfg",
            }:
                continue
            text = path.read_text(encoding="utf-8-sig", errors="replace")
            if USER_PATH.search(text):
                offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, "User-specific paths in production files: {}".format(
        ", ".join(sorted(offenders))
    )


def test_reference_weather_is_selected_at_runtime() -> None:
    import json

    payload = json.loads(
        (ROOT / "config" / "reference_model_config.json").read_text(encoding="utf-8")
    )
    assert payload["parameters"]["weather_file"]["value"] is None
