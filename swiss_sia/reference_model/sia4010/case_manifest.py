"""Load and validate source-traced inputs for every SIA 4010 class."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Tuple, Union

from ...config import SIA4010_CLASS_TEST_MATRIX
from ..exceptions import ConfigurationError


@dataclass(frozen=True)
class VariantInputReadiness:
    """Input completeness of one exact SIA 4010 variant."""

    variant: str
    status: str
    missing_parameters: Tuple[str, ...]
    provisional_parameters: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe payload."""

        return {
            "variant": self.variant,
            "status": self.status,
            "missing_parameters": list(self.missing_parameters),
            "provisional_parameters": list(self.provisional_parameters),
        }


class Sia4010CaseManifest:
    """Validated, immutable view of the case-input JSON contract."""

    SUPPORTED_SCHEMA_VERSIONS = {"1.0"}
    REQUIRED_PARAMETER_FIELDS = {
        "name",
        "description",
        "units",
        "source",
        "validation",
        "status",
        "value",
    }
    ALLOWED_PARAMETER_STATUSES = {
        "CONFIRMED",
        "CONFIRMED_NORMATIVE",
        "PUBLIC_REFERENCE",
        "PLACEHOLDER_REQUIRED",
        "UNRESOLVED",
    }
    USABLE_PARAMETER_STATUSES = {
        "CONFIRMED",
        "CONFIRMED_NORMATIVE",
        "PUBLIC_REFERENCE",
    }

    def __init__(self, path: Union[str, Path], payload: Mapping[str, Any]):
        """Bind the manifest to its source file path and validated payload."""

        self.path = Path(path)
        self.payload = dict(payload)
        self.parameters = dict(payload["parameters"])
        self.variants = dict(payload["variants"])
        self.classes = dict(payload["classes"])

    @classmethod
    def load(cls, path: Union[str, Path]) -> "Sia4010CaseManifest":
        """Load a manifest and reject missing, invented or inconsistent fields."""

        manifest_path = Path(path)
        try:
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ConfigurationError(
                "Invalid SIA 4010 case manifest: {}".format(exc)
            ) from exc
        required = {"schema_version", "classes", "variants", "parameters"}
        missing = sorted(required - set(payload))
        if missing:
            raise ConfigurationError(
                "SIA 4010 case manifest is missing fields: {}".format(missing)
            )
        if str(payload["schema_version"]) not in cls.SUPPORTED_SCHEMA_VERSIONS:
            raise ConfigurationError(
                "Unsupported SIA 4010 case-manifest schema: {}".format(
                    payload["schema_version"]
                )
            )
        if not isinstance(payload["parameters"], dict) or not payload["parameters"]:
            raise ConfigurationError("Case manifest contains no parameters")
        if not isinstance(payload["variants"], dict) or not payload["variants"]:
            raise ConfigurationError("Case manifest contains no variants")

        for parameter_id, parameter in payload["parameters"].items():
            if not isinstance(parameter, dict):
                raise ConfigurationError(
                    "Parameter {} must be an object".format(parameter_id)
                )
            missing_fields = sorted(
                cls.REQUIRED_PARAMETER_FIELDS - set(parameter)
            )
            if missing_fields:
                raise ConfigurationError(
                    "Parameter {} is missing fields: {}".format(
                        parameter_id, missing_fields
                    )
                )
            status = str(parameter["status"]).upper()
            if status not in cls.ALLOWED_PARAMETER_STATUSES:
                raise ConfigurationError(
                    "Parameter {} has unsupported status {}".format(
                        parameter_id, status
                    )
                )
            if status in cls.USABLE_PARAMETER_STATUSES and parameter["value"] is None:
                raise ConfigurationError(
                    "Usable parameter {} has no value".format(parameter_id)
                )
            if not str(parameter["source"] or "").strip():
                raise ConfigurationError(
                    "Parameter {} has no source".format(parameter_id)
                )

        for variant, definition in payload["variants"].items():
            if not isinstance(definition, dict):
                raise ConfigurationError(
                    "Variant {} must be an object".format(variant)
                )
            parameter_ids = definition.get("required_parameters")
            if not isinstance(parameter_ids, list) or not parameter_ids:
                raise ConfigurationError(
                    "Variant {} has no required_parameters".format(variant)
                )
            unknown = sorted(set(parameter_ids) - set(payload["parameters"]))
            if unknown:
                raise ConfigurationError(
                    "Variant {} references unknown parameters: {}".format(
                        variant, unknown
                    )
                )
            case_parameter_map = definition.get("case_required_parameters")
            if case_parameter_map is not None:
                if not isinstance(case_parameter_map, dict):
                    raise ConfigurationError(
                        "Variant {} case_required_parameters must be an object".format(
                            variant
                        )
                    )
                case_ids = definition.get("case_ids", [])
                if set(case_parameter_map) != set(case_ids):
                    raise ConfigurationError(
                        "Variant {} must define exact case parameter mappings for {}".format(
                            variant, case_ids
                        )
                    )
                for case_id, case_parameters in case_parameter_map.items():
                    if not isinstance(case_parameters, list) or not case_parameters:
                        raise ConfigurationError(
                            "Variant {} case {} has no required parameters".format(
                                variant, case_id
                            )
                        )
                    unknown_case_parameters = sorted(
                        set(case_parameters) - set(payload["parameters"])
                    )
                    if unknown_case_parameters:
                        raise ConfigurationError(
                            "Variant {} case {} references unknown parameters: {}".format(
                                variant, case_id, unknown_case_parameters
                            )
                        )

        if not isinstance(payload["classes"], dict) or not payload["classes"]:
            raise ConfigurationError("Case manifest contains no validation classes")
        unknown_classes = sorted(
            set(payload["classes"]) - set(SIA4010_CLASS_TEST_MATRIX)
        )
        if unknown_classes:
            raise ConfigurationError(
                "Unsupported SIA 4010 classes in case manifest: {}".format(
                    unknown_classes
                )
            )
        for class_id, configured in payload["classes"].items():
            expected = SIA4010_CLASS_TEST_MATRIX[class_id]
            if configured != expected:
                raise ConfigurationError(
                    "Class {} must require exact variants {}; found {}".format(
                        class_id, expected, configured
                    )
                )
            unknown_variants = sorted(set(configured) - set(payload["variants"]))
            if unknown_variants:
                raise ConfigurationError(
                    "Class {} references unknown variants: {}".format(
                        class_id, unknown_variants
                    )
                )
        return cls(manifest_path, payload)

    def value(self, parameter_id: str) -> Any:
        """Return one confirmed value; reject unresolved placeholders."""

        parameter = self.parameters.get(parameter_id)
        if parameter is None:
            raise ConfigurationError(
                "Unknown SIA 4010 parameter: {}".format(parameter_id)
            )
        if str(parameter["status"]).upper() not in self.USABLE_PARAMETER_STATUSES:
            raise ConfigurationError(
                "SIA 4010 parameter {} is unresolved; required source: {}".format(
                    parameter_id, parameter["source"]
                )
            )
        return parameter["value"]

    def variant_readiness(self, variant: str) -> VariantInputReadiness:
        """Return strict source completeness for one exact variant."""

        definition = self.variants.get(variant)
        if definition is None:
            raise ConfigurationError(
                "Unknown SIA 4010 variant: {}".format(variant)
            )
        missing = tuple(
            parameter_id
            for parameter_id in definition["required_parameters"]
            if str(self.parameters[parameter_id]["status"]).upper()
            not in self.USABLE_PARAMETER_STATUSES
            or self.parameters[parameter_id]["value"] is None
        )
        provisional = tuple(
            parameter_id
            for parameter_id in definition["required_parameters"]
            if str(self.parameters[parameter_id]["status"]).upper()
            == "PUBLIC_REFERENCE"
            and self.parameters[parameter_id]["value"] is not None
        )
        return VariantInputReadiness(
            variant=variant,
            status=(
                "BLOCKED_MISSING_INPUTS"
                if missing
                else "READY_PUBLIC_REFERENCE"
                if provisional
                else "READY"
            ),
            missing_parameters=missing,
            provisional_parameters=provisional,
        )

    def class_readiness(self, class_id: str) -> Dict[str, VariantInputReadiness]:
        """Return exact variant readiness for any configured validation class."""

        normalized = str(class_id or "").strip().upper()
        if normalized not in self.classes:
            raise ConfigurationError(
                "Unsupported SIA 4010 class in case manifest: {}".format(class_id)
            )
        return {
            variant: self.variant_readiness(variant)
            for variant in self.classes[normalized]
        }

    def case_readiness(
        self, variant: str, case_id: str
    ) -> VariantInputReadiness:
        """Return source completeness for one exact official test case."""

        definition = self.variants.get(variant)
        if definition is None:
            raise ConfigurationError(
                "Unknown SIA 4010 variant: {}".format(variant)
            )
        if case_id not in definition.get("case_ids", []):
            raise ConfigurationError(
                "Unknown SIA 4010 case {} for {}".format(case_id, variant)
            )
        parameter_ids = definition.get("case_required_parameters", {}).get(
            case_id, definition["required_parameters"]
        )
        missing = tuple(
            parameter_id
            for parameter_id in parameter_ids
            if str(self.parameters[parameter_id]["status"]).upper()
            not in self.USABLE_PARAMETER_STATUSES
            or self.parameters[parameter_id]["value"] is None
        )
        provisional = tuple(
            parameter_id
            for parameter_id in parameter_ids
            if str(self.parameters[parameter_id]["status"]).upper()
            == "PUBLIC_REFERENCE"
            and self.parameters[parameter_id]["value"] is not None
        )
        return VariantInputReadiness(
            variant="{}/{}".format(variant, case_id),
            status=(
                "BLOCKED_MISSING_INPUTS"
                if missing
                else "READY_PUBLIC_REFERENCE"
                if provisional
                else "READY"
            ),
            missing_parameters=missing,
            provisional_parameters=provisional,
        )

    def navigator_model_statuses(self, class_id: str) -> Dict[str, str]:
        """Return model-input statuses directly consumable by the navigator."""

        return {
            variant: readiness.status
            for variant, readiness in self.class_readiness(class_id).items()
        }
