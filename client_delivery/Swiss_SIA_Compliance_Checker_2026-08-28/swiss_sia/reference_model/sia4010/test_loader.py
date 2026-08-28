"""Checksum-verified loader for future official SIA 4010 file bundles."""

import csv
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple, Union

from ..exceptions import ConfigurationError
from .expected_results import ExpectedResult


@dataclass(frozen=True)
class BundleFile:
    """Checksum-verified file declared by an official bundle manifest."""

    path: Path
    role: str
    sha256: str
    test_ids: Tuple[str, ...]


@dataclass(frozen=True)
class OfficialTestBundle:
    """Validated manifest and files for future official test execution."""

    root: Path
    schema_version: str
    issued_by: str
    source_url: str
    files: Tuple[BundleFile, ...]
    manifest_path: Path


class Sia4010TestLoader:
    """Loads only bundles with explicit authority and file checksums."""

    MANIFEST_NAME = "official_manifest.json"
    SUPPORTED_MANIFEST_VERSIONS = {"1.0"}

    @staticmethod
    def _sha256(path: Path) -> str:
        """Calculate the hexadecimal SHA-256 checksum of one file."""

        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def load_bundle(self, root: Union[str, Path]) -> OfficialTestBundle:
        """Load and verify an authority-declared SIA 4010 test bundle."""

        bundle_root = Path(root)
        manifest_path = bundle_root / self.MANIFEST_NAME
        if not manifest_path.is_file():
            raise ConfigurationError(
                "SIA 4010 bundle has no {}".format(self.MANIFEST_NAME)
            )
        try:
            manifest: Dict[str, Any] = json.loads(
                manifest_path.read_text(encoding="utf-8")
            )
        except (OSError, ValueError) as exc:
            raise ConfigurationError("Invalid SIA 4010 manifest: {}".format(exc)) from exc

        required = {"schema_version", "issued_by", "source_url", "files"}
        missing = sorted(required - set(manifest))
        if missing:
            raise ConfigurationError(
                "SIA 4010 manifest is missing fields: {}".format(missing)
            )
        version = str(manifest["schema_version"])
        if version not in self.SUPPORTED_MANIFEST_VERSIONS:
            raise ConfigurationError(
                "Unsupported SIA 4010 manifest schema: {}".format(version)
            )
        if "SIA" not in str(manifest["issued_by"]).upper():
            raise ConfigurationError(
                "Manifest authority is not explicitly identified as SIA"
            )
        if not isinstance(manifest["files"], list) or not manifest["files"]:
            raise ConfigurationError("SIA 4010 manifest contains no files")

        files: List[BundleFile] = []
        for item in manifest["files"]:
            if not isinstance(item, dict):
                raise ConfigurationError("Manifest file entries must be objects")
            missing_fields = {"path", "role", "sha256", "test_ids"} - set(item)
            if missing_fields:
                raise ConfigurationError(
                    "Manifest file entry is missing {}".format(sorted(missing_fields))
                )
            relative = Path(str(item["path"]))
            if relative.is_absolute() or ".." in relative.parts:
                raise ConfigurationError("Bundle file path must stay within bundle root")
            path = bundle_root / relative
            if not path.is_file():
                raise ConfigurationError("Bundle file is missing: {}".format(relative))
            declared_checksum = str(item["sha256"]).lower()
            actual_checksum = self._sha256(path)
            if actual_checksum != declared_checksum:
                raise ConfigurationError("Checksum mismatch for {}".format(relative))
            files.append(
                BundleFile(
                    path=path,
                    role=str(item["role"]),
                    sha256=actual_checksum,
                    test_ids=tuple(str(test_id) for test_id in item["test_ids"]),
                )
            )
        return OfficialTestBundle(
            root=bundle_root,
            schema_version=version,
            issued_by=str(manifest["issued_by"]),
            source_url=str(manifest["source_url"]),
            files=tuple(files),
            manifest_path=manifest_path,
        )

    def load_expected_results(
        self, bundle: OfficialTestBundle
    ) -> Tuple[ExpectedResult, ...]:
        """Load normalized CSV rows explicitly marked as expected results.

        An adapter for the official Excel workbook can be added later without
        changing the comparator or workflow contracts.
        """

        result_files = [
            item for item in bundle.files if item.role == "expected_results_csv"
        ]
        if not result_files:
            return ()
        results: List[ExpectedResult] = []
        required_columns = {
            "test_id",
            "case_id",
            "metric",
            "expected_value",
            "unit",
            "absolute_tolerance",
            "relative_tolerance",
            "source_locator",
        }
        for item in result_files:
            with item.path.open("r", newline="", encoding="utf-8-sig") as handle:
                reader = csv.DictReader(handle)
                missing = required_columns - set(reader.fieldnames or [])
                if missing:
                    raise ConfigurationError(
                        "Expected-results CSV is missing columns: {}".format(
                            sorted(missing)
                        )
                    )
                for row in reader:
                    absolute = row["absolute_tolerance"].strip()
                    relative = row["relative_tolerance"].strip()
                    results.append(
                        ExpectedResult(
                            test_id=row["test_id"].strip(),
                            case_id=row["case_id"].strip(),
                            metric=row["metric"].strip(),
                            expected_value=float(row["expected_value"]),
                            unit=row["unit"].strip(),
                            absolute_tolerance=float(absolute) if absolute else None,
                            relative_tolerance=float(relative) if relative else None,
                            source_locator=row["source_locator"].strip(),
                            source_checksum=item.sha256,
                        )
                    )
        keys = [result.key for result in results]
        if len(keys) != len(set(keys)):
            raise ConfigurationError("Expected-result keys are not unique")
        return tuple(results)
