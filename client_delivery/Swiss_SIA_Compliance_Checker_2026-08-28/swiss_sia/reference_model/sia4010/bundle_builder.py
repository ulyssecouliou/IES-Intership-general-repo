"""Build a checksum-verified manifest for an official SIA 4010 test bundle.

This is a preparation utility: given a directory containing the official SIA
4010 files (example building plus per-test specifications, evaluation workbooks
and reference reports), it emits the ``official_manifest.json`` that
:class:`Sia4010TestLoader` verifies. It never fabricates results or tolerances;
it only records provenance (path, role, test ids and SHA-256) so the loader can
authenticate the bundle before any comparison.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from .test_loader import Sia4010TestLoader

MANIFEST_NAME = Sia4010TestLoader.MANIFEST_NAME
SCHEMA_VERSION = "1.0"
DEFAULT_ISSUED_BY = "SIA (Swiss Society of Engineers and Architects)"
DEFAULT_SOURCE_URL = "https://www.sia.ch/sia4010"

# Example-building artifacts are shared by the system tests (4-7).
_EXAMPLE_BUILDING_TEST_IDS = ("4", "5", "6", "7")
_TEST_ID_PATTERN = re.compile(r"test\s*([1-7])", re.IGNORECASE)


def infer_role(relative_path: Path) -> str:
    """Classify one bundle file into a stable, source-descriptive role."""

    name = relative_path.name.lower()
    parts = [part.lower() for part in relative_path.parts]
    if "resultaterfassung" in name:
        return "evaluation_workbook"
    if "spezifikation" in name:
        return "test_specification"
    if "anwenderbericht" in name or "anwenderberichte" in parts:
        return "reference_report"
    if "lastverl" in name:  # German "Lastverlaeufe" (load profiles)
        return "load_profile"
    if name.endswith(".ifc"):
        return "example_building_ifc"
    if name.endswith(".dwg"):
        return "example_building_drawing"
    if "dokumentation" in name:
        return "example_building_documentation"
    if name.endswith(".pdf"):
        return "reference_document"
    return "supporting_file"


def infer_test_ids(relative_path: Path) -> Tuple[str, ...]:
    """Infer applicable SIA 4010 test ids from a file's path."""

    match = _TEST_ID_PATTERN.search(str(relative_path))
    if match:
        return (match.group(1),)
    if any("beispielgeb" in part.lower() for part in relative_path.parts):
        return _EXAMPLE_BUILDING_TEST_IDS
    return ()


def build_manifest(
    root: Union[str, Path],
    issued_by: str = DEFAULT_ISSUED_BY,
    source_url: str = DEFAULT_SOURCE_URL,
) -> Dict[str, Any]:
    """Return a manifest dict for every file under ``root`` (excluding the manifest)."""

    bundle_root = Path(root)
    if not bundle_root.is_dir():
        raise NotADirectoryError("Bundle root does not exist: {}".format(bundle_root))
    files: List[Dict[str, Any]] = []
    for path in sorted(bundle_root.rglob("*")):
        if not path.is_file() or path.name == MANIFEST_NAME:
            continue
        relative = path.relative_to(bundle_root)
        files.append(
            {
                "path": relative.as_posix(),
                "role": infer_role(relative),
                "sha256": Sia4010TestLoader._sha256(path),
                "test_ids": list(infer_test_ids(relative)),
            }
        )
    if not files:
        raise ValueError("No official files found under {}".format(bundle_root))
    return {
        "schema_version": SCHEMA_VERSION,
        "issued_by": issued_by,
        "source_url": source_url,
        "files": files,
    }


def write_manifest(
    root: Union[str, Path],
    issued_by: str = DEFAULT_ISSUED_BY,
    source_url: str = DEFAULT_SOURCE_URL,
) -> Path:
    """Build and atomically write ``official_manifest.json`` into ``root``."""

    bundle_root = Path(root)
    manifest = build_manifest(bundle_root, issued_by, source_url)
    manifest_path = bundle_root / MANIFEST_NAME
    tmp_path = manifest_path.with_suffix(".json.tmp")
    tmp_path.write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    tmp_path.replace(manifest_path)
    return manifest_path
