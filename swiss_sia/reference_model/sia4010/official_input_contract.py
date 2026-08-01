"""Validated source extraction for the supplied SIA 4010 specifications."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Union

from ..exceptions import ConfigurationError
from .model_scenario import TEST_CASES


@dataclass(frozen=True)
class OfficialTestInput:
    """Confirmed fields and explicit dependencies for one base test."""

    test_id: str
    source: str
    source_pages: tuple
    variants: tuple
    confirmed_inputs: Mapping[str, Any]
    unresolved_dependencies: tuple
    ve_generation_status: str

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe normalized record."""

        return {
            "test_id": self.test_id,
            "source": self.source,
            "source_pages": list(self.source_pages),
            "variants": list(self.variants),
            "confirmed_inputs": dict(self.confirmed_inputs),
            "unresolved_dependencies": list(self.unresolved_dependencies),
            "ve_generation_status": self.ve_generation_status,
        }


class Sia4010OfficialInputContract:
    """Strict loader for confirmed specification values and dependencies."""

    SUPPORTED_SCHEMA_VERSIONS = {"1.0"}

    def __init__(self, path: Path, payload: Mapping[str, Any]):
        """Bind a validated input contract to its source file."""

        self.path = path
        self.payload = dict(payload)
        self.common = dict(payload["common"])
        self.tests = {
            test_id: OfficialTestInput(
                test_id=test_id,
                source=str(item["source"]),
                source_pages=tuple(int(page) for page in item["source_pages"]),
                variants=tuple(str(value) for value in item["variants"]),
                confirmed_inputs=dict(item["confirmed_inputs"]),
                unresolved_dependencies=tuple(
                    str(value) for value in item["unresolved_dependencies"]
                ),
                ve_generation_status=str(item["ve_generation_status"]),
            )
            for test_id, item in payload["tests"].items()
        }

    @classmethod
    def load(
        cls, path: Union[str, Path]
    ) -> "Sia4010OfficialInputContract":
        """Load the contract and reject incomplete or overclaimed records."""

        contract_path = Path(path)
        try:
            payload = json.loads(contract_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ConfigurationError(
                "Invalid SIA 4010 official-input contract: {}".format(exc)
            ) from exc
        required = {
            "schema_version",
            "purpose",
            "claim_guardrail",
            "common",
            "tests",
        }
        missing = sorted(required - set(payload))
        if missing:
            raise ConfigurationError(
                "Official-input contract is missing fields: {}".format(missing)
            )
        if str(payload["schema_version"]) not in cls.SUPPORTED_SCHEMA_VERSIONS:
            raise ConfigurationError(
                "Unsupported official-input contract schema: {}".format(
                    payload["schema_version"]
                )
            )
        if not isinstance(payload["common"], dict) or not payload["common"]:
            raise ConfigurationError("Official-input contract has no common inputs")
        expected_tests = set("234567")
        if set(payload["tests"]) != expected_tests:
            raise ConfigurationError(
                "Official-input contract must contain Tests 2-7 exactly"
            )
        fields = {
            "variants",
            "source",
            "source_pages",
            "confirmed_inputs",
            "unresolved_dependencies",
            "ve_generation_status",
        }
        for test_id, item in payload["tests"].items():
            absent = sorted(fields - set(item))
            if absent:
                raise ConfigurationError(
                    "Official Test {} input record is missing {}".format(
                        test_id, absent
                    )
                )
            expected_variants = sorted(
                variant
                for variant in TEST_CASES
                if variant.startswith("test_{}".format(test_id))
            )
            actual_variants = sorted(
                "test_{}".format(str(value))
                for value in item["variants"]
            )
            if actual_variants != expected_variants:
                raise ConfigurationError(
                    "Official Test {} variants mismatch: expected {}, found {}"
                    .format(test_id, expected_variants, actual_variants)
                )
            if not str(item["source"] or "").strip():
                raise ConfigurationError(
                    "Official Test {} has no source".format(test_id)
                )
            if not item["source_pages"] or not all(
                isinstance(page, int) and page > 0 for page in item["source_pages"]
            ):
                raise ConfigurationError(
                    "Official Test {} has invalid source pages".format(test_id)
                )
            if not isinstance(item["confirmed_inputs"], dict) or not item[
                "confirmed_inputs"
            ]:
                raise ConfigurationError(
                    "Official Test {} has no confirmed inputs".format(test_id)
                )
            if (
                not isinstance(item["unresolved_dependencies"], list)
                or not item["unresolved_dependencies"]
            ):
                raise ConfigurationError(
                    "Official Test {} must preserve unresolved dependencies".format(
                        test_id
                    )
                )
            if item["ve_generation_status"] != "NOT_IMPLEMENTED":
                raise ConfigurationError(
                    "Official Test {} generation status is overclaimed".format(
                        test_id
                    )
                )
        return cls(contract_path, payload)

    def test(self, test_id: Union[str, int]) -> OfficialTestInput:
        """Return one normalized base-test input record."""

        normalized = str(test_id)
        if normalized not in self.tests:
            raise ConfigurationError(
                "No extracted official-input record for Test {}".format(test_id)
            )
        return self.tests[normalized]

