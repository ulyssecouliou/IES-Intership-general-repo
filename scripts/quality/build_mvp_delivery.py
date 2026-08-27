"""Build a clean, auditable Swiss SIA MVP delivery ZIP.

The archive intentionally excludes reports, client evidence, licensed standards,
local company profiles, caches and test outputs.  A SHA-256 manifest makes the
delivered source set reviewable.
"""

from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Iterable, List

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_DIR = ROOT / "outputs" / "release"
PACKAGE_PREFIX = "Swiss_SIA_Compliance_MVP"

INCLUDED_DIRECTORIES = (
    "swiss_sia",
    "ui",
    "core",
    "engine",
    "ve_adapter",
    "assets",
    "data",
    "schemas",
    "templates",
    "config",
)
INCLUDED_DOCS = (
    "docs/user/WORKFLOW_CLIENT_SIA3802_FR.md",
    "docs/project/CLIENT_RUN_GUIDE.md",
    "docs/project/RELEASE_ACCEPTANCE_CHECKLIST.md",
    "docs/project/ETAT_FINAL_MVP_MSP_2026-08-24.md",
    "docs/project/GLAZING_EVIDENCE_GUIDE.md",
)
SKIP_SUFFIXES = (".pyc", ".pyo")
SKIP_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache"}


def _files() -> Iterable[Path]:
    roots: List[Path] = []
    for directory in INCLUDED_DIRECTORIES:
        candidate = ROOT / directory
        if candidate.is_dir():
            roots.extend(path for path in candidate.rglob("*") if path.is_file())
    roots.extend(ROOT.glob("Run_VE_*.py"))
    roots.extend(ROOT / path for path in INCLUDED_DOCS)
    for name in ("README.md", "requirements.txt", "LICENSE", "main.py"):
        roots.append(ROOT / name)
    unique = sorted({path.resolve() for path in roots if path.is_file()})
    for path in unique:
        relative = path.relative_to(ROOT)
        if relative.as_posix() == "config/company_profile.json":
            continue
        if any(part in SKIP_NAMES for part in relative.parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        yield path


def build() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = OUTPUT_DIR / "{}_{}.zip".format(PACKAGE_PREFIX, stamp)
    entries = []
    files = list(_files())
    for path in files:
        payload = path.read_bytes()
        entries.append(
            {
                "path": path.relative_to(ROOT).as_posix(),
                "size_bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
        )
    manifest = {
        "product": "Swiss SIA Compliance Checker",
        "scope": "MVP readiness/audit tooling; not an SIA certificate",
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "file_count": len(entries),
        "excluded": [
            "client evidence and reports",
            "licensed standards",
            "local company_profile.json",
            "test outputs and caches",
            ".git metadata",
        ],
        "files": entries,
    }
    temporary = target.with_suffix(".zip.tmp")
    with zipfile.ZipFile(temporary, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "DELIVERY_MANIFEST.json",
            json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        )
        for path in files:
            archive.write(path, path.relative_to(ROOT).as_posix())
    temporary.replace(target)
    return target


if __name__ == "__main__":
    result = build()
    print(result)
