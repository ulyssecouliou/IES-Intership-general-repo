"""Feature-safe scenario contract for SIA 4010 VE model generation.

One official scenario represents exactly one disposable VE project and one
official test case.  Required features are derived from the selected case and
cannot be disabled.  A custom reference scenario may expose free feature
selection, but is never labelled as an official SIA 4010 validation case.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Tuple, Union

from ...config import SIA4010_CLASS_TEST_MATRIX
from ..exceptions import ConfigurationError
from .case_manifest import Sia4010CaseManifest


SCENARIO_PROFILES = ("SIA4010_OFFICIAL", "CUSTOM_REFERENCE")
EXECUTION_MODES = (
    "PREPARE_ONLY",
    "CREATE_IN_ACTIVE_VE_PROJECT",
    "QUALIFY_IN_ACTIVE_VE_PROJECT",
)
FEATURE_IDS = (
    "geometry",
    "opaque_envelope",
    "glazing",
    "thermal_template",
    "ideal_heating",
    "ideal_cooling",
    "infiltration",
    "internal_gains",
    "weather",
    "solar_protection",
    "lighting_controls",
    "mechanical_ventilation",
    "heat_recovery",
    "humidification",
    "energy_systems",
    "hourly_distributions",
    "aps_results",
    "audit_report",
)
TEST_CASES: Dict[str, Tuple[str, ...]] = {
    "test_1": ("600", "640", "600FF", "900", "940", "900FF", "1E"),
    "test_2A": ("2A",),
    "test_2B": ("2B",),
    "test_2C": ("2C",),
    "test_2D": ("2D",),
    **{
        "test_3{}".format(letter): ("3{}".format(letter),)
        for letter in "ABCDEFGHIJKL"
    },
    "test_4": ("4",),
    **{
        "test_5{}".format(letter): ("5{}".format(letter),)
        for letter in "ABCD"
    },
    "test_6": ("6",),
    "test_7": ("7",),
}


def official_features(variant: str, case_id: str) -> Dict[str, bool]:
    """Return the locked model features for one official test case."""

    if variant not in TEST_CASES or case_id not in TEST_CASES[variant]:
        raise ConfigurationError(
            "Unknown SIA 4010 variant/case combination: {}/{}".format(
                variant, case_id
            )
        )
    family = variant[5] if variant.startswith("test_") and len(variant) > 5 else ""
    free_float = case_id in {"600FF", "900FF"}
    envelope_case = family in {"1", "2", "3", "5", "6"}
    ideal_load_case = family in {"1", "2"}
    hvac_case = family in {"4", "5", "6"}
    return {
        "geometry": True,
        "opaque_envelope": envelope_case,
        "glazing": family in {"1", "2", "3", "5", "6"},
        "thermal_template": True,
        "ideal_heating": ideal_load_case and not free_float,
        "ideal_cooling": ideal_load_case and not free_float,
        "infiltration": family in {"1", "2", "3"},
        "internal_gains": True,
        "weather": True,
        "solar_protection": family in {"2", "3"} or case_id == "1E",
        "lighting_controls": family == "3",
        "mechanical_ventilation": hvac_case,
        "heat_recovery": family in {"4", "5", "6"},
        "humidification": family == "5",
        "energy_systems": family == "7",
        "hourly_distributions": family in {"2", "3", "5"},
        "aps_results": True,
        "audit_report": True,
    }


@dataclass(frozen=True)
class ScenarioFiles:
    """Files consumed by the scenario build launcher."""

    case_manifest_file: str
    ve_config_file: str
    ve_asset_manifest_file: str

    def to_dict(self) -> Dict[str, str]:
        """Return the generated scenario artifact paths as serializable data."""

        return {
            "case_manifest_file": self.case_manifest_file,
            "ve_config_file": self.ve_config_file,
            "ve_asset_manifest_file": self.ve_asset_manifest_file,
        }


@dataclass(frozen=True)
class ModelScenario:
    """Validated immutable model-generation selection."""

    scenario_id: str
    profile: str
    target_class: str
    variant: str
    case_id: str
    features: Mapping[str, bool]
    files: ScenarioFiles
    execution_mode: str

    SUPPORTED_SCHEMA_VERSIONS = {"1.0"}

    @classmethod
    def load(cls, path: Union[str, Path]) -> "ModelScenario":
        """Load a scenario and reject unsafe or ambiguous feature selections."""

        scenario_path = Path(path)
        try:
            payload = json.loads(scenario_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ConfigurationError(
                "Invalid model scenario configuration: {}".format(exc)
            ) from exc
        required = {
            "schema_version",
            "scenario_id",
            "profile",
            "selection",
            "features",
            "files",
            "execution",
        }
        missing = sorted(required - set(payload))
        if missing:
            raise ConfigurationError(
                "Model scenario is missing fields: {}".format(missing)
            )
        if str(payload["schema_version"]) not in cls.SUPPORTED_SCHEMA_VERSIONS:
            raise ConfigurationError(
                "Unsupported model-scenario schema: {}".format(
                    payload["schema_version"]
                )
            )

        profile = str(payload["profile"]).upper()
        if profile not in SCENARIO_PROFILES:
            raise ConfigurationError("Unsupported model profile: {}".format(profile))
        selection = payload["selection"]
        files = payload["files"]
        execution = payload["execution"]
        if not all(isinstance(item, dict) for item in (selection, files, execution)):
            raise ConfigurationError(
                "selection, files and execution must be JSON objects"
            )
        target_class = str(selection.get("target_class", "")).upper()
        variant = str(selection.get("variant", ""))
        case_id = str(selection.get("case_id", ""))
        if target_class not in SIA4010_CLASS_TEST_MATRIX:
            raise ConfigurationError(
                "Unsupported SIA 4010 target class: {}".format(target_class)
            )
        if variant not in SIA4010_CLASS_TEST_MATRIX[target_class]:
            raise ConfigurationError(
                "{} is not part of SIA 4010 class {}".format(
                    variant, target_class
                )
            )
        if case_id not in TEST_CASES.get(variant, ()):
            raise ConfigurationError(
                "{} is not a case of {}".format(case_id, variant)
            )

        features = payload["features"]
        if not isinstance(features, dict):
            raise ConfigurationError("features must be a JSON object")
        missing_features = sorted(set(FEATURE_IDS) - set(features))
        unknown_features = sorted(set(features) - set(FEATURE_IDS))
        if missing_features or unknown_features:
            raise ConfigurationError(
                "Feature contract mismatch; missing={}, unknown={}".format(
                    missing_features, unknown_features
                )
            )
        normalized_features = {
            feature_id: bool(features[feature_id]) for feature_id in FEATURE_IDS
        }
        if profile == "SIA4010_OFFICIAL":
            required_features = official_features(variant, case_id)
            changed = {
                feature_id: {
                    "required": required_features[feature_id],
                    "selected": normalized_features[feature_id],
                }
                for feature_id in FEATURE_IDS
                if normalized_features[feature_id] != required_features[feature_id]
            }
            if changed:
                raise ConfigurationError(
                    "Official SIA 4010 features are locked for {}/{}: {}".format(
                        variant, case_id, changed
                    )
                )

        execution_mode = str(execution.get("mode", "")).upper()
        if execution_mode not in EXECUTION_MODES:
            raise ConfigurationError(
                "Unsupported scenario execution mode: {}".format(execution_mode)
            )
        if profile == "CUSTOM_REFERENCE" and execution_mode != "PREPARE_ONLY":
            raise ConfigurationError(
                "Custom feature combinations are preparation-only; automated "
                "VE mutation is reserved for source-qualified official scenarios"
            )
        scenario_id = str(payload["scenario_id"] or "").strip()
        if not scenario_id:
            raise ConfigurationError("scenario_id cannot be empty")
        required_file_fields = {
            "case_manifest_file",
            "ve_config_file",
            "ve_asset_manifest_file",
        }
        missing_file_fields = sorted(required_file_fields - set(files))
        if missing_file_fields:
            raise ConfigurationError(
                "Scenario file mapping is incomplete: {}".format(
                    missing_file_fields
                )
            )
        return cls(
            scenario_id=scenario_id,
            profile=profile,
            target_class=target_class,
            variant=variant,
            case_id=case_id,
            features=normalized_features,
            files=ScenarioFiles(
                case_manifest_file=str(files["case_manifest_file"]),
                ve_config_file=str(files["ve_config_file"]),
                ve_asset_manifest_file=str(files["ve_asset_manifest_file"]),
            ),
            execution_mode=execution_mode,
        )

    @property
    def is_official(self) -> bool:
        """Return whether this scenario claims an exact official test case."""

        return self.profile == "SIA4010_OFFICIAL"

    def readiness(self, manifest: Sia4010CaseManifest) -> Dict[str, Any]:
        """Return a fail-closed build decision against the source manifest."""

        variant = manifest.case_readiness(self.variant, self.case_id)
        blockers = list(variant.missing_parameters)
        provisional = list(variant.provisional_parameters)
        if self.execution_mode != "PREPARE_ONLY" and blockers:
            decision = "BLOCKED_MISSING_OFFICIAL_INPUTS"
        elif self.execution_mode == "PREPARE_ONLY":
            decision = "READY_FOR_PREPARATION"
        elif provisional:
            decision = "READY_FOR_PROVISIONAL_VE_MUTATION"
        else:
            decision = "READY_FOR_VE_MUTATION"
        return {
            "scenario_id": self.scenario_id,
            "profile": self.profile,
            "target_class": self.target_class,
            "variant": self.variant,
            "case_id": self.case_id,
            "execution_mode": self.execution_mode,
            "decision": decision,
            "missing_parameters": blockers,
            "provisional_parameters": provisional,
            "features": dict(self.features),
            "compliance_claim_allowed": (
                self.is_official and not blockers and not provisional
            ),
        }

    def to_dict(self) -> Dict[str, Any]:
        """Return the normalized scenario as a JSON-safe object."""

        return {
            "schema_version": "1.0",
            "scenario_id": self.scenario_id,
            "profile": self.profile,
            "selection": {
                "target_class": self.target_class,
                "variant": self.variant,
                "case_id": self.case_id,
            },
            "features": dict(self.features),
            "files": self.files.to_dict(),
            "execution": {"mode": self.execution_mode},
        }


def build_feature_catalog() -> Dict[str, Any]:
    """Return the browser-interface catalog from the Python source of truth."""

    return {
        "schema_version": "1.0",
        "classes": {
            class_id: list(variants)
            for class_id, variants in SIA4010_CLASS_TEST_MATRIX.items()
        },
        "cases": {
            variant: list(case_ids) for variant, case_ids in TEST_CASES.items()
        },
        "features": [
            {
                "id": "geometry",
                "label": "Géométrie exacte de la cellule",
                "group": "Modèle",
            },
            {
                "id": "opaque_envelope",
                "label": "Enveloppe opaque",
                "group": "Modèle",
            },
            {"id": "glazing", "label": "Vitrage", "group": "Modèle"},
            {
                "id": "thermal_template",
                "label": "Template thermique",
                "group": "Conditions",
            },
            {
                "id": "ideal_heating",
                "label": "Chauffage idéal",
                "group": "Conditions",
            },
            {
                "id": "ideal_cooling",
                "label": "Refroidissement idéal",
                "group": "Conditions",
            },
            {
                "id": "infiltration",
                "label": "Infiltration",
                "group": "Conditions",
            },
            {
                "id": "internal_gains",
                "label": "Apports internes",
                "group": "Conditions",
            },
            {"id": "weather", "label": "Météo", "group": "Climat"},
            {
                "id": "solar_protection",
                "label": "Protection solaire dynamique",
                "group": "Climat",
            },
            {
                "id": "lighting_controls",
                "label": "Commande d'éclairage",
                "group": "Systèmes",
            },
            {
                "id": "mechanical_ventilation",
                "label": "Ventilation mécanique",
                "group": "Systèmes",
            },
            {
                "id": "heat_recovery",
                "label": "Récupération de chaleur",
                "group": "Systèmes",
            },
            {
                "id": "humidification",
                "label": "Humidification",
                "group": "Systèmes",
            },
            {
                "id": "energy_systems",
                "label": "Émission, distribution, stockage et génération",
                "group": "Systèmes",
            },
            {
                "id": "hourly_distributions",
                "label": "Distributions horaires obligatoires",
                "group": "Résultats",
            },
            {
                "id": "aps_results",
                "label": "Résultats APS qualifiés",
                "group": "Résultats",
            },
            {
                "id": "audit_report",
                "label": "Rapport d’audit",
                "group": "Résultats",
            },
        ],
        "official_feature_matrix": {
            variant: {
                case_id: official_features(variant, case_id)
                for case_id in case_ids
            }
            for variant, case_ids in TEST_CASES.items()
        },
    }
