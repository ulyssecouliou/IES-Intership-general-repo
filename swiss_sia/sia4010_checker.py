"""SIA 4010 readiness and evidence checker.

SIA 4010 validates a calculation method or software workflow through official
test cases, evaluation workbooks, reference comparisons, and a declared
validation class. This module therefore tracks readiness and evidence quality;
it does not grant an autonomous SIA 4010 pass for a client model.
"""

import logging
import os
import csv
from pathlib import Path
from typing import List, Dict, Optional, Any

from .config import (
    PROJECT_ROOT,
    SIA4010_EVIDENCE_DIR,
    SIA4010_CLASS_MANIFEST_ACCEPTED_REVIEW_STATUSES,
    SIA4010_CLASS_MANIFEST_PREFIXES,
    SIA4010_CLASS_MANIFEST_REQUIRED_COLUMNS,
    SIA4010_EVIDENCE_MANIFEST_ACCEPTED_REVIEW_STATUSES,
    SIA4010_EVIDENCE_MANIFEST_PREFIXES,
    SIA4010_EVIDENCE_MANIFEST_REQUIRED_COLUMNS,
    SIA4010_EVIDENCE_REQUIREMENTS,
    SIA4010_CLASS_TEST_MATRIX,
    SIA4010_MODEL_REQUIREMENT_LABELS,
    SIA4010_OFFICIAL_TEST_RESULT_FAIL_STATUSES,
    SIA4010_OFFICIAL_TEST_RESULT_PASS_STATUSES,
    SIA4010_OFFICIAL_TEST_RESULTS_PREFIXES,
    SIA4010_OFFICIAL_TEST_RESULTS_REQUIRED_COLUMNS,
    SIA4010_REQUIRED_EVIDENCE,
    SIA4010_TEST_ALIAS_LABELS,
    SIA4010_TEST_WEIGHTS,
    SIA4010_TEST_VARIANT_REQUIREMENTS,
    SIA4010_IESVE_REGISTER_STATUS,
    SIA4010_VALIDATION_CLASS_DETAILS,
    SIA4010_VALIDATION_CLASSES,
    SIA4010_VALIDATION_TESTS,
)
from .model_analyzer import ModelAnalyzer, RoomData, has_active_solar_protection
from .evidence_pack import matches_active_project_scope
from .rule_engine import Rule, RuleEngine, Severity

logger = logging.getLogger(__name__)


class SIA4010Checker:
    """Assess SIA 4010 validation readiness without issuing false certification."""

    def __init__(
        self,
        model_analyzer: ModelAnalyzer,
        rule_engine: RuleEngine,
        project_label: Optional[str] = None,
        project_root: Optional[Path] = None,
    ):
        """Initialize the checker with an optional active VE project scope."""
        self.model_analyzer = model_analyzer
        self.rule_engine = rule_engine
        self.project_label = project_label or self._derive_project_label(model_analyzer)
        self.project_root = Path(project_root or PROJECT_ROOT)
        self._setup_rules()

    @staticmethod
    def _derive_project_label(model_analyzer: ModelAnalyzer) -> Optional[str]:
        """Derive the active project folder name from a production model analyzer."""
        extractor = getattr(model_analyzer, "data_extractor", None)
        project = getattr(extractor, "project", None)
        project_path = str(getattr(project, "path", "") or "").strip()
        if not project_path:
            return None
        return os.path.basename(os.path.normpath(project_path)) or None

    def _setup_rules(self):
        """Register SIA 4010 project indicators in the rule engine."""
        # SIA 4010 does not define standalone building kWh/m2 or CO2 limits.
        # These rules only document available project indicators.
        self.rule_engine.add_rule(Rule(
            name="SIA4010_HEATING_DEMAND",
            description="Heating demand is available; SIA 4010 requires official tests/files, not an autonomous kWh/m2.year threshold.",
            check=lambda data: True,
            severity=Severity.LOW,
            category="Energy",
            recommendation="Compare only through the official SIA 4010 evaluation workbook or through project-specific SIA 380 requirements.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA4010_COOLING_DEMAND",
            description="Cooling demand is available; SIA 4010 requires official tests/files, not an autonomous kWh/m2.year threshold.",
            check=lambda data: True,
            severity=Severity.LOW,
            category="Energy",
            recommendation="Compare only through the official SIA 4010 evaluation workbook or through project-specific SIA 380 requirements.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA4010_PRIMARY_ENERGY",
            description="Primary energy is available; SIA 4010 does not provide a standalone threshold in the PDF.",
            check=lambda data: True,
            severity=Severity.LOW,
            category="Energy",
            recommendation="Assess primary energy under SIA 380 or project requirements, then attach SIA 4010 validation evidence if the calculation method is claimed.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA4010_CO2_EMISSIONS",
            description="CO2 emissions are available; SIA 4010 does not provide a standalone threshold in the PDF.",
            check=lambda data: True,
            severity=Severity.LOW,
            category="Energy",
            recommendation="Treat CO2 as a separate client/cantonal indicator, not as a SIA 4010 validation verdict.",
        ))

        self.rule_engine.add_rule(Rule(
            name="SIA4010_RENEWABLE_ENERGY",
            description="Renewable energy share is available; SIA 4010 does not provide a standalone threshold in the PDF.",
            check=lambda data: True,
            severity=Severity.LOW,
            category="Energy",
            recommendation="Treat renewable share under project/cantonal requirements; do not use it as SIA 4010 validation.",
        ))

    def check_all(
        self,
        rooms_data: Optional[List[RoomData]] = None,
        official_band_evaluations: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Run all SIA 4010 readiness checks and return report-ready results.

        ``official_band_evaluations`` (the runner's ``to_test_results_map`` output)
        is surfaced as a separate automated cross-check. It never drives official
        class validation, which still requires recorded results and SIA
        sub-commission attestation; merging it into the gate would overclaim.
        """
        rooms_data = rooms_data if rooms_data is not None else self.model_analyzer.analyze_all_rooms()

        # SIA 4010 validates a method/software workflow via seven official tests.
        # Without official SIA files and comparisons, validation remains blocked.
        energy_data = {
            "heating_demand": self._calculate_heating_demand(rooms_data),
            "cooling_demand": self._calculate_cooling_demand(rooms_data),
            "primary_energy": None,
            "co2_emissions": None,
            "renewable_energy_share": None,
        }
        evidence = self._scan_sia4010_evidence()
        evidence_summary = self._summarize_evidence(evidence)
        evidence["summary"] = evidence_summary

        # Check only actually available project indicators. They never replace
        # official SIA 4010 files.
        self.rule_engine.clear_alerts()
        rule_by_metric = {
            "heating_demand": "SIA4010_HEATING_DEMAND",
            "cooling_demand": "SIA4010_COOLING_DEMAND",
            "primary_energy": "SIA4010_PRIMARY_ENERGY",
            "co2_emissions": "SIA4010_CO2_EMISSIONS",
            "renewable_energy_share": "SIA4010_RENEWABLE_ENERGY",
        }
        for metric, rule_name in rule_by_metric.items():
            if energy_data.get(metric) is None:
                continue
            self.rule_engine.check_rules([rule_name], energy_data)

        self._add_evidence_status_alert(evidence_summary)
        self._add_software_register_guardrail_alert(evidence_summary)

        test_results = self._run_sia4010_tests(evidence_summary)
        class_results = self._evaluate_validation_classes(test_results, evidence_summary)
        if official_band_evaluations:
            class_results = self._annotate_classes_with_band_crosscheck(
                class_results, official_band_evaluations
            )
        class_readiness = {
            class_name: self._resolve_class_readiness_from_summary(
                class_name,
                rooms_data,
                evidence_summary,
            )
            for class_name in SIA4010_CLASS_TEST_MATRIX
        }

        return {
            "energy": energy_data,
            "alerts": self.rule_engine.alerts,
            "tests": test_results,
            "classes": class_results,
            "class_readiness": class_readiness,
            "score": self._calculate_sia4010_score(test_results),
            "readiness_score": self._calculate_evidence_readiness_score(evidence_summary),
            "evidence": evidence,
            "validation_class": evidence.get("validation_class"),
            "official_band_crosscheck": official_band_evaluations or {},
        }

    @staticmethod
    def _annotate_classes_with_band_crosscheck(
        class_results: Dict[str, Any],
        band_map: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Attach the automated official-band cross-check to each class result.

        This is an informational automated indicator derived from comparing VE
        results to the official reference bands. It deliberately does NOT change
        ``class_status`` (which remains driven by recorded results and reviewer
        attestation), so it cannot turn an unattested result into a pass.
        """

        for result in class_results.values():
            required = (
                result.get("required_test_aliases")
                or result.get("required_tests", [])
                or []
            )
            per_test = {
                test: band_map.get(test, {}).get("status", "NOT_EVALUATED")
                for test in required
            }
            statuses = set(per_test.values())
            if not per_test:
                summary = "NO_TESTS"
            elif "FAILED" in statuses:
                summary = "BAND_FAILED"
            elif statuses == {"OFFICIAL_RESULTS_RECORDED"}:
                summary = "BAND_WITHIN_RANGE"
            else:
                summary = "BAND_NOT_CHECKABLE"
            result["band_crosscheck"] = {"per_test": per_test, "summary": summary}
        return class_results

    def resolve_class_readiness(
        self,
        validation_class: str,
        rooms_data: List[RoomData],
    ) -> Dict[str, Any]:
        """Resolve VE-data and evidence readiness for one SIA 4010 class.

        The returned vocabulary is deliberately limited to ``NOT_CHECKABLE``,
        ``EVIDENCE_INCOMPLETE`` and ``READY_FOR_OFFICIAL_REVIEW`` for official
        status. This method never grants PASS, VALIDATED or certification.
        """
        evidence = self._scan_sia4010_evidence()
        evidence_summary = self._summarize_evidence(evidence)
        return self._resolve_class_readiness_from_summary(
            validation_class,
            rooms_data,
            evidence_summary,
        )

    def _resolve_class_readiness_from_summary(
        self,
        validation_class: str,
        rooms_data: List[RoomData],
        evidence_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build one class-readiness payload from a pre-scanned evidence state."""
        class_name = str(validation_class or "").strip().upper()
        if class_name not in SIA4010_CLASS_TEST_MATRIX:
            raise ValueError(f"Unsupported SIA 4010 validation class: {validation_class}")
        facts = self._build_variant_readiness_facts(rooms_data)
        evidence_status = str(evidence_summary.get("status") or "NOT_CHECKABLE").upper()
        if evidence_status not in {
            "NOT_CHECKABLE",
            "EVIDENCE_INCOMPLETE",
            "READY_FOR_OFFICIAL_REVIEW",
        }:
            evidence_status = "NOT_CHECKABLE"

        variant_rows = []
        blocking_variants = []
        for variant in SIA4010_CLASS_TEST_MATRIX[class_name]:
            requirement = SIA4010_TEST_VARIANT_REQUIREMENTS[variant]
            model_requirements = list(requirement.get("model_requirements", []) or [])
            present = [key for key in model_requirements if bool(facts.get(key))]
            missing = [key for key in model_requirements if not bool(facts.get(key))]
            identifier_results = self._evaluate_variant_identifiers(
                requirement.get("system_identifiers", {}) or {},
                rooms_data,
            )
            matching_identifiers = [
                row["identifier"] for row in identifier_results if row["matches"]
            ]
            mismatching_identifiers = [
                row["identifier"] for row in identifier_results if not row["matches"]
            ]
            total_checks = len(model_requirements) + len(identifier_results)
            passed_checks = len(present) + len(matching_identifiers)
            ratio = passed_checks / total_checks if total_checks else 0.0
            if ratio >= 0.85 and not mismatching_identifiers:
                ve_status = "READY"
            elif ratio > 0:
                ve_status = "PARTIAL"
            else:
                ve_status = "MISSING"
            if ve_status != "READY":
                blocking_variants.append(variant)
            variant_rows.append({
                "variant": variant,
                "domain": requirement.get("domain", ""),
                "object": requirement.get("object", ""),
                "system_identifiers": dict(requirement.get("system_identifiers", {}) or {}),
                "identifier_results": identifier_results,
                "matching_identifiers": matching_identifiers,
                "mismatching_identifiers": mismatching_identifiers,
                "model_requirements": model_requirements,
                "present_requirements": present,
                "missing_requirements": missing,
                "present_labels": [SIA4010_MODEL_REQUIREMENT_LABELS.get(key, key) for key in present],
                "missing_labels": [SIA4010_MODEL_REQUIREMENT_LABELS.get(key, key) for key in missing],
                "readiness_ratio": ratio,
                "ve_status": ve_status,
                "official_status": evidence_status,
                "source": requirement.get("source", ""),
            })

        overall_ratio = (
            sum(float(row["readiness_ratio"]) for row in variant_rows) / len(variant_rows)
            if variant_rows
            else 0.0
        )
        if evidence_status == "READY_FOR_OFFICIAL_REVIEW":
            overall_status = (
                "READY_FOR_OFFICIAL_REVIEW"
                if not blocking_variants
                else "EVIDENCE_INCOMPLETE"
            )
        else:
            overall_status = evidence_status
        return {
            "validation_class": class_name,
            "required_variants": list(SIA4010_CLASS_TEST_MATRIX[class_name]),
            "variant_rows": variant_rows,
            "overall_ve_readiness_ratio": overall_ratio,
            "blocking_variants": blocking_variants,
            "evidence_status": evidence_status,
            "official_status": overall_status,
            "missing_official_evidence": list(evidence_summary.get("missing_items", []) or []),
            "claim_guardrail": (
                "Readiness only. Official SIA 4010 workbooks, reference comparisons and "
                "sub-commission review remain required."
            ),
        }

    @classmethod
    def _evaluate_variant_identifiers(
        cls,
        required_identifiers: Dict[str, Any],
        rooms_data: List[RoomData],
    ) -> List[Dict[str, Any]]:
        """Compare prescribed SIA 4010 identifiers with explicit VE metadata."""
        rooms = list(rooms_data or [])
        openings = [
            opening
            for room in rooms
            for opening in (getattr(room, "openings", []) or [])
            if getattr(opening, "is_external", False)
        ]
        systems = [
            system
            for room in rooms
            for system in (getattr(room, "hvac_systems", []) or [])
            if isinstance(system, dict)
        ]

        values_by_identifier = {
            "SHADING_TYPE": [
                getattr(opening, "shading_type", None)
                for opening in openings
                if has_active_solar_protection(opening)
            ],
            "SHADING_CONTROL_VARIANT": [
                getattr(opening, "shading_control", None)
                for opening in openings
                if has_active_solar_protection(opening)
            ],
            "LIGHTING_CONTROL_VARIANT": [getattr(room, "lighting_control_type", None) for room in rooms],
            "SYS_TYPE": [system.get("system_type") for system in systems],
            "FAN_CTRL": [system.get("fan_control") for system in systems],
            "HEAT_REC_TYPE": (
                [system.get("heat_recovery_type") for system in systems]
                + [getattr(room, "heat_recovery_type", None) for room in rooms]
            ),
            "FROST_PROTECTION": [system.get("frost_protection") for system in systems],
            "HEAT_RECOVERY_CHARACTERISTIC": [
                system.get("heat_recovery_characteristic") for system in systems
            ],
            "HUMIDIFIER_TYPE": [
                system.get("humidifier_type") or system.get("humidifier_control")
                for system in systems
            ],
            "AIR_FLOW_CTRL": (
                [system.get("ventilation_control") for system in systems]
                + [getattr(room, "ventilation_control", None) for room in rooms]
            ),
            "CLG_STORAGE_TYPE": [system.get("cooling_storage_type") for system in systems],
            "HEAT_REJECTION_TYPE": [system.get("heat_rejection_type") for system in systems],
        }
        ventilation_levels = [
            getattr(room, "ventilation_control_level", None) for room in rooms
        ]
        rows = []
        for identifier, expected in required_identifiers.items():
            actual_values = [
                value
                for value in values_by_identifier.get(str(identifier).upper(), [])
                if value not in (None, "")
            ]
            matches = any(
                cls._identifier_value_matches(expected, actual)
                for actual in actual_values
            )
            if str(identifier).upper() == "SHADING_CONTROL_VARIANT" and str(expected).upper() == "NONE":
                matches = bool(openings) and (
                    not actual_values
                    or any(
                        cls._identifier_value_matches("NONE", actual)
                        for actual in actual_values
                    )
                )
            if str(identifier).upper() == "AIR_FLOW_CTRL" and str(expected).upper() == "MULTI_STAGE":
                matches = matches or any(
                    isinstance(level, (int, float)) and level >= 1
                    for level in ventilation_levels
                )
            rows.append({
                "identifier": str(identifier),
                "expected": str(expected),
                "actual_values": [str(value) for value in actual_values],
                "matches": bool(matches),
            })
        return rows

    @staticmethod
    def _identifier_value_matches(expected: Any, actual: Any) -> bool:
        """Match one explicit VE identifier using conservative aliases."""
        def normalize(value: Any) -> str:
            """Return an uppercase alphanumeric identifier."""
            return "".join(
                character for character in str(value or "").upper()
                if character.isalnum()
            )

        expected_token = normalize(expected)
        actual_token = normalize(actual)
        if not expected_token or not actual_token:
            return False
        aliases = {
            "FABRIC": ("FABRIC", "TEXTILE", "AWNING"),
            "LAMELLAE": ("LAMELLA", "VENETIAN", "BLIND"),
            "NONE": ("NONE", "NO", "FIXED", "MANUAL"),
            "SINGLEZONE": ("SINGLEZONE", "MONOZONE"),
            "MULTIZONE": ("MULTIZONE",),
            "DIRECT": ("DIRECT",),
            "MINPRES": ("MINPRES", "MINIMUMPRESSURE"),
            "CONSTPRES": ("CONSTPRES", "CONSTANTPRESSURE"),
            "PLATE": ("PLATE", "PLATEHEATEXCHANGER"),
            "BYPASS": ("BYPASS",),
            "HYGROSCOPIC": ("HYGROSCOPIC",),
            "NONHYGROSCOPIC": ("NONHYGROSCOPIC",),
            "ADIABATIC": ("ADIABATIC", "SPRAY"),
            "STEAM": ("STEAM",),
            "MULTISTAGE": ("MULTISTAGE", "TWOSTAGE", "THREESTAGE"),
            "STOTYPECW": ("STOTYPECW", "CHILLEDWATER"),
            "DRY": ("DRY", "DRYCOOLER"),
        }
        candidates = aliases.get(expected_token, (expected_token,))
        return any(candidate in actual_token for candidate in candidates)

    @staticmethod
    def _build_variant_readiness_facts(rooms_data: List[RoomData]) -> Dict[str, Any]:
        """Summarize VE fields used by variant-level readiness requirements."""
        rooms = list(rooms_data or [])
        surfaces = [surface for room in rooms for surface in getattr(room, "surfaces", [])]
        openings = [opening for room in rooms for opening in getattr(room, "openings", [])]
        external_surfaces = [surface for surface in surfaces if getattr(surface, "is_external", False)]
        external_openings = [opening for opening in openings if getattr(opening, "is_external", False)]
        external_windows = [
            opening
            for opening in external_openings
            if str(getattr(opening, "opening_type", "") or "").lower() in {
                "window",
                "glazing",
                "ext_glazing",
                "4",
            }
        ]
        dynamic_rows = []
        for room in rooms:
            dynamic_row = getattr(room, "dynamic_results", None)
            if isinstance(dynamic_row, dict):
                dynamic_rows.append(dynamic_row)
        hvac_systems = [system for room in rooms for system in getattr(room, "hvac_systems", [])]
        return {
            "rooms": len(rooms),
            "external_surfaces": len(external_surfaces),
            "surface_u_values": sum(1 for surface in external_surfaces if getattr(surface, "u_value", None) is not None),
            "external_openings": len(external_openings),
            "external_windows": len(external_windows),
            "en410_g_values": sum(1 for opening in external_windows if getattr(opening, "g_value_bs_en_410", None) is not None),
            "solar_protection_types": sum(
                1 for opening in external_windows if has_active_solar_protection(opening)
            ),
            "solar_protection_controls": sum(
                1
                for opening in external_windows
                if has_active_solar_protection(opening)
                and getattr(opening, "shading_control", None)
            ),
            "window_operability": sum(1 for room in rooms if getattr(room, "window_operable", None) is not None),
            "rooms_with_lighting": sum(1 for room in rooms if (getattr(room, "internal_gains", {}) or {}).get("lighting") is not None),
            "daylight_dimming_profiles": sum(1 for room in rooms if getattr(room, "daylight_dimming_profile", "")),
            "lighting_control_mappings": sum(1 for room in rooms if getattr(room, "lighting_control_type", "")),
            "dynamic_lighting_rows": sum(1 for row in dynamic_rows if row.get("lighting_kwh") is not None),
            "rooms_with_hvac": sum(1 for room in rooms if getattr(room, "hvac_systems", [])),
            "rooms_with_ventilation": sum(1 for room in rooms if getattr(room, "ventilation_m3_h_m2", None) is not None),
            "fan_controls": sum(1 for system in hvac_systems if system.get("fan_control")),
            "heat_recovery_types": sum(1 for room in rooms if getattr(room, "heat_recovery_type", None)),
            "humidifier_controls": sum(1 for system in hvac_systems if system.get("humidifier_control")),
            "dynamic_coil_rows": sum(1 for row in dynamic_rows if row.get("coil_heating_kwh") is not None or row.get("coil_cooling_kwh") is not None),
            "dynamic_temperature_rows": sum(1 for row in dynamic_rows if row.get("occupied_hours_above_26") is not None),
            "dynamic_co2_rows": sum(1 for row in dynamic_rows if row.get("peak_co2_ppm") is not None),
            "ventilation_stages": sum(1 for room in rooms if getattr(room, "ventilation_control_level", None) is not None),
            "overflow_paths": sum(1 for system in hvac_systems if system.get("overflow_paths")),
            "dynamic_demand_rows": sum(1 for row in dynamic_rows if row.get("heating_kwh") is not None or row.get("cooling_kwh") is not None),
            "final_energy_available": any(system.get("final_energy") is not None for system in hvac_systems),
            "dynamic_auxiliary_rows": sum(1 for row in dynamic_rows if any(row.get(key) is not None for key in ("fan_kwh", "pump_kwh", "auxiliary_kwh"))),
            "storage_generation_data": sum(1 for system in hvac_systems if system.get("storage_generation_data")),
        }

    def _scan_sia4010_evidence(self) -> Dict[str, Any]:
        """Scan local SIA 4010 evidence files without granting official validation."""
        repo_dir = str(self.project_root)
        evidence_dir = os.path.join(repo_dir, SIA4010_EVIDENCE_DIR)
        files: List[Dict[str, Any]] = []
        excluded_project_files: List[Dict[str, Any]] = []
        if os.path.isdir(evidence_dir):
            for root, _dirs, filenames in os.walk(evidence_dir):
                for filename in filenames:
                    path = os.path.join(root, filename)
                    rel_path = os.path.relpath(path, repo_dir)
                    try:
                        size_bytes = os.path.getsize(path)
                    except Exception:
                        size_bytes = None
                    file_data = {
                        "name": filename,
                        "path": rel_path,
                        "size_bytes": size_bytes,
                    }
                    if matches_active_project_scope(path, self.project_label):
                        files.append(file_data)
                    else:
                        excluded_project_files.append(dict(
                            file_data,
                            reason=(
                                "Project-scoped evidence helper belongs to another VE project; "
                                f"active project is {self.project_label}."
                            ),
                        ))

        manifest_scan = self._scan_evidence_manifests(evidence_dir, repo_dir, files)
        class_manifest_scan = self._scan_class_manifests(evidence_dir, repo_dir, files)
        official_test_result_scan = self._scan_official_test_results(evidence_dir, repo_dir, files)
        evidence: Dict[str, Any] = {
            "evidence_dir": evidence_dir,
            "project_label": self.project_label or "",
            "files": files,
            "excluded_project_files": excluded_project_files,
            "classified_files": [],
            "classified_file_count": 0,
            "ignored_files": [],
            "unclassified_files": [],
            "manifest_files": manifest_scan["manifest_files"],
            "manifest_rows": manifest_scan["manifest_rows"],
            "manifest_summary": manifest_scan["summary"],
            "class_manifest_files": class_manifest_scan["manifest_files"],
            "class_manifest_rows": class_manifest_scan["manifest_rows"],
            "class_manifest_summary": class_manifest_scan["summary"],
            "official_test_result_files": official_test_result_scan["result_files"],
            "official_test_result_rows": official_test_result_scan["result_rows"],
            "official_test_result_summary": official_test_result_scan["summary"],
            "validation_class": None,
            "validation_class_source": "not_selected",
            "validation_class_selection_status": "NOT_SELECTED",
            "manager_reference_files": self._scan_manager_reference_files(repo_dir),
            "software_register_status": dict(SIA4010_IESVE_REGISTER_STATUS),
        }
        evidence["ignored_files"] = [
            dict(file_data, reason="Folder note/documentation file ignored by the SIA 4010 evidence scanner.")
            for file_data in files
            if self._is_evidence_folder_note(file_data.get("name", ""))
        ]
        evidence["ignored_files"].extend(
            dict(file_data, reason="Evidence manifest parsed for metadata; it is not counted as an official evidence file by itself.")
            for file_data in files
            if self._is_evidence_manifest_file(file_data.get("name", ""))
        )
        evidence["ignored_files"].extend(
            dict(file_data, reason="Class validation manifest parsed for class selection; it is not counted as an official evidence file by itself.")
            for file_data in files
            if self._is_class_manifest_file(file_data.get("name", ""))
        )
        evidence["ignored_files"].extend(
            dict(file_data, reason="Official test-result manifest parsed for test statuses; it is not counted as an evidence-family file by itself.")
            for file_data in files
            if self._is_official_test_results_file(file_data.get("name", ""))
        )
        candidate_files = [
            file_data
            for file_data in files
            if not self._is_evidence_folder_note(file_data.get("name", ""))
            and not self._is_evidence_manifest_file(file_data.get("name", ""))
            and not self._is_class_manifest_file(file_data.get("name", ""))
            and not self._is_official_test_results_file(file_data.get("name", ""))
        ]
        manifest_blob = " ".join(
            " ".join(str(row.get(key, "") or "") for key in ("provided_file_name", "notes", "required_for_classes"))
            for row in manifest_scan["manifest_rows"]
        )
        filenames_blob = " ".join(file_data["name"].lower() for file_data in candidate_files) + " " + manifest_blob.lower()
        for key, requirement in SIA4010_EVIDENCE_REQUIREMENTS.items():
            matched = [
                file_data
                for file_data in candidate_files
                if self._matches_evidence_requirement(file_data, requirement)
            ]
            manifest_rows = [
                row for row in manifest_scan["manifest_rows"]
                if row.get("evidence_key") == key
            ]
            documented_rows = [
                row for row in manifest_rows
                if row.get("row_status") == "DOCUMENTED"
                and any(
                    str(file_data.get("name", "")).lower() == str(row.get("provided_file_name", "")).lower()
                    for file_data in matched
                )
            ]
            evidence[key] = {
                "present": bool(matched),
                "files": matched,
                "manifest_rows": manifest_rows,
                "manifest_documented": bool(documented_rows),
                "manifest_documented_rows": documented_rows,
                "label": requirement.get("label", key),
                "required_prefixes": list(requirement.get("required_prefixes", [])),
                "accepted_extensions": list(requirement.get("accepted_extensions", [])),
                "example_filename": requirement.get("example_filename", ""),
                "description": requirement.get("description", ""),
            }
            for file_data in matched:
                if file_data not in evidence["classified_files"]:
                    evidence["classified_files"].append(file_data)

        unclassified_files = [
            file_data
            for file_data in candidate_files
            if file_data not in evidence["classified_files"]
        ]
        evidence["unclassified_files"] = unclassified_files
        evidence["ignored_files"].extend(
            dict(
                file_data,
                reason="Filename does not match any documented SIA 4010 evidence prefix or accepted extension.",
            )
            for file_data in unclassified_files
        )
        evidence["classified_file_count"] = len(evidence["classified_files"])

        selected_class = class_manifest_scan["summary"].get("selected_class")
        if selected_class:
            evidence["validation_class"] = selected_class
            evidence["validation_class_source"] = "class_manifest"
            evidence["validation_class_selection_status"] = class_manifest_scan["summary"].get("selection_status", "SELECTED")
        else:
            class_markers = ["4b", "4a", "3", "2b", "2a", "1b", "1a", "5"]
            for marker in class_markers:
                if f"class_{marker}" in filenames_blob or f"classe_{marker}" in filenames_blob or f"class{marker}" in filenames_blob:
                    evidence["detected_validation_class"] = marker.upper()
                    evidence["detected_validation_class_source"] = "filename_marker"
                    break

        item_key_map = {
            SIA4010_REQUIRED_EVIDENCE[0]: "official_test_specifications",
            SIA4010_REQUIRED_EVIDENCE[1]: "official_evaluation_workbooks",
            SIA4010_REQUIRED_EVIDENCE[2]: "candidate_results",
            SIA4010_REQUIRED_EVIDENCE[3]: "reference_comparisons",
            SIA4010_REQUIRED_EVIDENCE[4]: "validation_class_confirmation",
        }
        for item, key in item_key_map.items():
            evidence[item] = bool(evidence.get(key, {}).get("present"))
        return evidence

    @staticmethod
    def _summarize_evidence(evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Return a normalized evidence completeness summary."""
        present_items = [
            item for item in SIA4010_REQUIRED_EVIDENCE
            if bool(evidence.get(item))
        ]
        missing_items = [
            item for item in SIA4010_REQUIRED_EVIDENCE
            if not bool(evidence.get(item))
        ]
        manifest_documented_items = []
        manifest_missing_documentation_items = []
        for item in SIA4010_REQUIRED_EVIDENCE:
            key = SIA4010Checker._requirement_key_for_evidence_item(item)
            if bool(evidence.get(key, {}).get("manifest_documented")):
                manifest_documented_items.append(item)
            else:
                manifest_missing_documentation_items.append(item)
        validation_class = evidence.get("validation_class")
        class_is_known = validation_class in SIA4010_VALIDATION_CLASSES
        all_required_present = len(missing_items) == 0
        all_required_documented = len(manifest_missing_documentation_items) == 0
        classified_count = int(evidence.get("classified_file_count", 0) or 0)

        if all_required_present and all_required_documented and class_is_known:
            status = "READY_FOR_OFFICIAL_REVIEW"
        elif classified_count > 0 or present_items:
            status = "EVIDENCE_INCOMPLETE"
        else:
            status = "NOT_CHECKABLE"

        return {
            "status": status,
            "present_count": len(present_items),
            "required_count": len(SIA4010_REQUIRED_EVIDENCE),
            "present_items": present_items,
            "missing_items": missing_items,
            "manifest_documented_count": len(manifest_documented_items),
            "manifest_documented_items": manifest_documented_items,
            "manifest_missing_documentation_items": manifest_missing_documentation_items,
            "manifest_summary": evidence.get("manifest_summary", {}),
            "validation_class": validation_class,
            "validation_class_source": evidence.get("validation_class_source", "not_selected"),
            "validation_class_selection_status": evidence.get("validation_class_selection_status", "NOT_SELECTED"),
            "detected_validation_class": evidence.get("detected_validation_class"),
            "detected_validation_class_source": evidence.get("detected_validation_class_source"),
            "class_manifest_summary": evidence.get("class_manifest_summary", {}),
            "official_test_result_summary": evidence.get("official_test_result_summary", {}),
            "official_test_result_rows": evidence.get("official_test_result_rows", []),
            "validation_class_known": class_is_known,
            "classified_file_count": classified_count,
            "software_register_status": evidence.get("software_register_status", {}),
            "manager_reference_files": evidence.get("manager_reference_files", []),
        }

    def _add_evidence_status_alert(self, evidence_summary: Dict[str, Any]) -> None:
        """Add one precise alert describing current official evidence status."""
        status = evidence_summary["status"]
        missing_items = evidence_summary["missing_items"]
        manifest_missing_items = evidence_summary.get("manifest_missing_documentation_items", [])
        present_count = evidence_summary["present_count"]
        required_count = evidence_summary["required_count"]

        if status == "READY_FOR_OFFICIAL_REVIEW":
            self.rule_engine.add_alert(
                rule="SIA4010_OFFICIAL_REVIEW_REQUIRED",
                description="SIA 4010 evidence families are present, but official reviewer acceptance is still required before any VALIDATED claim.",
                severity=Severity.LOW,
                category="SIA4010 Validation",
                recommendation="Submit the official SIA evaluation package for reviewer/sub-commission confirmation; keep the report wording as readiness until accepted.",
                data=evidence_summary,
            )
            return

        if status == "EVIDENCE_INCOMPLETE":
            if missing_items:
                recommendation = (
                    "Complete the missing official evidence families before any SIA 4010 validation wording: "
                    + "; ".join(missing_items)
                )
            else:
                recommendation = (
                    "Complete the SIA 4010 evidence manifest metadata for each detected family, including "
                    "provided_file_name, source_authority, tests_covered, reviewer and an accepted review_status. "
                    "Missing manifest documentation: " + "; ".join(manifest_missing_items)
                )
            self.rule_engine.add_alert(
                rule="SIA4010_VALIDATION_EVIDENCE_INCOMPLETE",
                description=(
                    f"SIA 4010 evidence is partial: {present_count}/{required_count} required evidence families detected; "
                    f"{evidence_summary.get('manifest_documented_count', 0)}/{required_count} families documented in the manifest."
                ),
                severity=Severity.MEDIUM,
                category="SIA4010 Validation",
                recommendation=recommendation,
                data=evidence_summary,
            )
            if missing_items:
                self._add_missing_evidence_family_alerts(missing_items, Severity.LOW)
            return

        self.rule_engine.add_alert(
            rule="SIA4010_VALIDATION_EVIDENCE_MISSING",
            description="SIA 4010 validation is not checkable without official test specifications, evaluation workbooks and reference comparisons.",
            severity=Severity.HIGH,
            category="SIA4010 Validation",
            recommendation="Attach official SIA 4010 test specifications, official evaluation workbooks, candidate results, reference comparisons and validation class confirmation before any PASS claim.",
            data=evidence_summary,
        )
        self._add_missing_evidence_family_alerts(missing_items, Severity.LOW)

    def _add_software_register_guardrail_alert(self, evidence_summary: Dict[str, Any]) -> None:
        """Add a non-scoring guardrail from the manager-provided software register."""
        status = evidence_summary.get("software_register_status", {}) or {}
        if status.get("listed_in_manager_register"):
            return
        self.rule_engine.add_alert(
            rule="SIA4010_IESVE_NOT_IN_MANAGER_REGISTER",
            description=(
                "IESVE is not listed in the manager-provided SIA 4010 validated-software register "
                f"dated {status.get('register_date', 'unknown')}."
            ),
            severity=Severity.LOW,
            category="SIA4010 Software Register",
            recommendation=status.get(
                "guardrail",
                "Do not claim software-level SIA 4010 validation without separate official evidence.",
            ),
            data=status,
        )

    def _add_missing_evidence_family_alerts(
        self,
        missing_items: List[str],
        severity: Severity,
    ) -> None:
        """Add one actionable alert per missing official evidence family."""
        for item in missing_items:
            slug = "".join(ch if ch.isalnum() else "_" for ch in item.upper()).strip("_")
            requirement = self._requirement_for_evidence_item(item)
            prefixes = ", ".join(requirement.get("required_prefixes", []) or [])
            extensions = ", ".join(requirement.get("accepted_extensions", []) or [])
            example = requirement.get("example_filename", "")
            recommendation = (
                "Place the corresponding official evidence file in sia4010_evidence/ "
                f"using the required prefix {prefixes or 'documented in the evidence template'}"
            )
            if extensions:
                recommendation += f" and one of these extensions: {extensions}."
            else:
                recommendation += "."
            if example:
                recommendation += f" Example: {example}."
            self.rule_engine.add_alert(
                rule=f"SIA4010_EVIDENCE_FAMILY_MISSING_{slug[:48]}",
                description=f"Missing SIA 4010 evidence family: {item}.",
                severity=severity,
                category="SIA4010 Evidence",
                recommendation=recommendation,
                data={
                    "missing_evidence_family": item,
                    "required_prefixes": requirement.get("required_prefixes", []),
                    "accepted_extensions": requirement.get("accepted_extensions", []),
                    "example_filename": example,
                },
            )

    @staticmethod
    def _is_evidence_folder_note(filename: str) -> bool:
        """Exclude local README/docs from SIA 4010 evidence classification."""
        normalized = str(filename or "").strip().lower()
        return normalized in {"readme.md", "readme.txt", ".gitkeep"} or normalized.startswith("readme.")

    @staticmethod
    def _is_evidence_manifest_file(filename: str) -> bool:
        """Return true for SIA 4010 evidence manifest CSV files."""
        normalized = str(filename or "").strip().lower()
        if not normalized.endswith(".csv"):
            return False
        return any(normalized.startswith(prefix.lower()) for prefix in SIA4010_EVIDENCE_MANIFEST_PREFIXES)

    @staticmethod
    def _is_class_manifest_file(filename: str) -> bool:
        """Return true for SIA 4010 validation-class manifest CSV files."""
        normalized = str(filename or "").strip().lower()
        if not normalized.endswith(".csv"):
            return False
        return any(normalized.startswith(prefix.lower()) for prefix in SIA4010_CLASS_MANIFEST_PREFIXES)

    @staticmethod
    def _is_official_test_results_file(filename: str) -> bool:
        """Return true for official SIA 4010 test-result CSV manifests."""
        normalized = str(filename or "").strip().lower()
        if not normalized.endswith(".csv"):
            return False
        return any(normalized.startswith(prefix.lower()) for prefix in SIA4010_OFFICIAL_TEST_RESULTS_PREFIXES)

    @classmethod
    def _scan_evidence_manifests(
        cls,
        evidence_dir: str,
        repo_dir: str,
        files: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Read SIA 4010 evidence manifest CSV files without counting them as evidence."""
        manifest_files = [
            file_data for file_data in files
            if cls._is_evidence_manifest_file(file_data.get("name", ""))
        ]
        manifest_rows: List[Dict[str, Any]] = []
        missing_columns: Dict[str, List[str]] = {}

        for file_data in manifest_files:
            path = os.path.join(repo_dir, file_data.get("path", ""))
            try:
                with open(path, newline="", encoding="utf-8-sig") as handle:
                    reader = csv.DictReader(handle)
                    fieldnames = list(reader.fieldnames or [])
                    missing = [
                        column for column in SIA4010_EVIDENCE_MANIFEST_REQUIRED_COLUMNS
                        if column not in fieldnames
                    ]
                    if missing:
                        missing_columns[file_data.get("path", file_data.get("name", ""))] = missing
                    for row_index, raw_row in enumerate(reader, start=2):
                        normalized_row = {
                            str(key or "").strip(): str(value or "").strip()
                            for key, value in (raw_row or {}).items()
                        }
                        normalized_row["manifest_file"] = file_data.get("name", "")
                        normalized_row["manifest_path"] = file_data.get("path", "")
                        normalized_row["row_index"] = row_index
                        cls._annotate_manifest_row(normalized_row, files)
                        manifest_rows.append(normalized_row)
            except Exception as exc:
                manifest_rows.append({
                    "manifest_file": file_data.get("name", ""),
                    "manifest_path": file_data.get("path", ""),
                    "row_index": None,
                    "evidence_key": "",
                    "row_status": "READ_ERROR",
                    "row_status_reason": str(exc),
                })

        documented_count = sum(1 for row in manifest_rows if row.get("row_status") == "DOCUMENTED")
        return {
            "manifest_files": manifest_files,
            "manifest_rows": manifest_rows,
            "summary": {
                "manifest_file_count": len(manifest_files),
                "manifest_row_count": len(manifest_rows),
                "documented_row_count": documented_count,
                "missing_columns": missing_columns,
            },
        }

    @classmethod
    def _scan_official_test_results(
        cls,
        evidence_dir: str,
        repo_dir: str,
        files: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Read official SIA 4010 test-result rows without granting implicit validation."""
        result_files = [
            file_data for file_data in files
            if cls._is_official_test_results_file(file_data.get("name", ""))
        ]
        result_rows: List[Dict[str, Any]] = []
        missing_columns: Dict[str, List[str]] = {}

        for file_data in result_files:
            path = os.path.join(repo_dir, file_data.get("path", ""))
            try:
                with open(path, newline="", encoding="utf-8-sig") as handle:
                    reader = csv.DictReader(handle)
                    fieldnames = list(reader.fieldnames or [])
                    missing = [
                        column for column in SIA4010_OFFICIAL_TEST_RESULTS_REQUIRED_COLUMNS
                        if column not in fieldnames
                    ]
                    if missing:
                        missing_columns[file_data.get("path", file_data.get("name", ""))] = missing
                    for row_index, raw_row in enumerate(reader, start=2):
                        normalized_row = {
                            str(key or "").strip(): str(value or "").strip()
                            for key, value in (raw_row or {}).items()
                        }
                        normalized_row["result_file"] = file_data.get("name", "")
                        normalized_row["result_path"] = file_data.get("path", "")
                        normalized_row["row_index"] = row_index
                        cls._annotate_official_test_result_row(normalized_row, files)
                        result_rows.append(normalized_row)
            except Exception as exc:
                result_rows.append({
                    "result_file": file_data.get("name", ""),
                    "result_path": file_data.get("path", ""),
                    "row_index": None,
                    "test_key": "",
                    "row_status": "READ_ERROR",
                    "row_status_reason": str(exc),
                })

        recorded_pass_by_test: Dict[str, List[Dict[str, Any]]] = {}
        failed_by_test: Dict[str, List[Dict[str, Any]]] = {}
        for row in result_rows:
            test_key = row.get("test_key", "")
            if not test_key:
                continue
            if row.get("row_status") == "OFFICIAL_PASS":
                recorded_pass_by_test.setdefault(test_key, []).append(row)
            elif row.get("row_status") == "OFFICIAL_FAIL":
                failed_by_test.setdefault(test_key, []).append(row)

        return {
            "result_files": result_files,
            "result_rows": result_rows,
            "summary": {
                "result_file_count": len(result_files),
                "result_row_count": len(result_rows),
                "official_pass_count": sum(len(rows) for rows in recorded_pass_by_test.values()),
                "official_fail_count": sum(len(rows) for rows in failed_by_test.values()),
                "recorded_pass_tests": sorted(recorded_pass_by_test),
                "failed_tests": sorted(failed_by_test),
                "recorded_pass_by_test": recorded_pass_by_test,
                "failed_by_test": failed_by_test,
                "missing_columns": missing_columns,
            },
        }

    @classmethod
    def _scan_class_manifests(
        cls,
        evidence_dir: str,
        repo_dir: str,
        files: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Read SIA 4010 class-selection manifests without counting them as evidence."""
        manifest_files = [
            file_data for file_data in files
            if cls._is_class_manifest_file(file_data.get("name", ""))
        ]
        manifest_rows: List[Dict[str, Any]] = []
        missing_columns: Dict[str, List[str]] = {}

        for file_data in manifest_files:
            path = os.path.join(repo_dir, file_data.get("path", ""))
            try:
                with open(path, newline="", encoding="utf-8-sig") as handle:
                    reader = csv.DictReader(handle)
                    fieldnames = list(reader.fieldnames or [])
                    missing = [
                        column for column in SIA4010_CLASS_MANIFEST_REQUIRED_COLUMNS
                        if column not in fieldnames
                    ]
                    if missing:
                        missing_columns[file_data.get("path", file_data.get("name", ""))] = missing
                    for row_index, raw_row in enumerate(reader, start=2):
                        normalized_row = {
                            str(key or "").strip(): str(value or "").strip()
                            for key, value in (raw_row or {}).items()
                        }
                        normalized_row["manifest_file"] = file_data.get("name", "")
                        normalized_row["manifest_path"] = file_data.get("path", "")
                        normalized_row["row_index"] = row_index
                        cls._annotate_class_manifest_row(normalized_row)
                        manifest_rows.append(normalized_row)
            except Exception as exc:
                manifest_rows.append({
                    "manifest_file": file_data.get("name", ""),
                    "manifest_path": file_data.get("path", ""),
                    "row_index": None,
                    "validation_class": "",
                    "class_key": "",
                    "row_status": "READ_ERROR",
                    "row_status_reason": str(exc),
                })

        selected_rows = [
            row for row in manifest_rows
            if row.get("selected_bool") and row.get("class_key") in SIA4010_VALIDATION_CLASSES
        ]
        documented_selected_rows = [
            row for row in selected_rows
            if row.get("row_status") == "SELECTED_DOCUMENTED"
        ]
        if len(documented_selected_rows) == 1:
            selected_class = documented_selected_rows[0].get("class_key")
            selection_status = documented_selected_rows[0].get("row_status", "SELECTED_DOCUMENTED")
        elif len(selected_rows) > 1:
            selected_class = None
            selection_status = "MULTIPLE_CLASSES_SELECTED"
        elif len(selected_rows) == 1:
            selected_class = None
            selection_status = selected_rows[0].get("row_status", "SELECTED_NOT_DOCUMENTED")
        else:
            selected_class = None
            selection_status = "NOT_SELECTED"

        return {
            "manifest_files": manifest_files,
            "manifest_rows": manifest_rows,
            "summary": {
                "manifest_file_count": len(manifest_files),
                "manifest_row_count": len(manifest_rows),
                "selected_row_count": len(selected_rows),
                "documented_selected_row_count": len(documented_selected_rows),
                "selected_class": selected_class,
                "selection_status": selection_status,
                "missing_columns": missing_columns,
            },
        }

    @classmethod
    def _annotate_manifest_row(cls, row: Dict[str, Any], files: List[Dict[str, Any]]) -> None:
        """Add normalized keys and validation state to one manifest row."""
        evidence_key = cls._evidence_key_from_manifest_family(row.get("evidence_family", ""))
        provided_file_name = str(row.get("provided_file_name", "") or "").strip()
        review_status = cls._normalize_review_status(row.get("review_status", ""))
        source_authority = str(row.get("source_authority", "") or "").strip()
        version_or_date = str(row.get("version_or_date", "") or "").strip()
        reviewer = str(row.get("reviewer", "") or "").strip()
        tests_covered = str(row.get("tests_covered", "") or "").strip()

        referenced_file = next(
            (
                file_data for file_data in files
                if str(file_data.get("name", "") or "").lower() == provided_file_name.lower()
            ),
            None,
        )
        requirement = SIA4010_EVIDENCE_REQUIREMENTS.get(evidence_key, {})
        file_matches_requirement = bool(
            referenced_file and cls._matches_evidence_requirement(referenced_file, requirement)
        )
        review_status_accepted = review_status in SIA4010_EVIDENCE_MANIFEST_ACCEPTED_REVIEW_STATUSES

        row["evidence_key"] = evidence_key
        row["review_status_normalized"] = review_status
        row["provided_file_exists"] = bool(referenced_file)
        row["provided_file_path"] = referenced_file.get("path", "") if referenced_file else ""
        row["file_matches_requirement"] = file_matches_requirement
        row["review_status_accepted"] = review_status_accepted

        if not evidence_key:
            row["row_status"] = "UNKNOWN_FAMILY"
            row["row_status_reason"] = "The evidence_family value does not map to a configured SIA 4010 evidence family."
        elif not provided_file_name:
            row["row_status"] = "MISSING_FILE_REFERENCE"
            row["row_status_reason"] = "The manifest row does not provide a file name."
        elif not referenced_file:
            row["row_status"] = "REFERENCED_FILE_NOT_FOUND"
            row["row_status_reason"] = "The file named in provided_file_name was not found in sia4010_evidence/."
        elif not file_matches_requirement:
            row["row_status"] = "FILE_NAMING_MISMATCH"
            row["row_status_reason"] = "The referenced file does not match the configured prefix or accepted extension."
        elif not review_status_accepted:
            row["row_status"] = "NOT_REVIEWED"
            row["row_status_reason"] = "The manifest review_status is not one of the accepted documented statuses."
        elif not source_authority or not version_or_date or not reviewer or not tests_covered:
            row["row_status"] = "METADATA_INCOMPLETE"
            row["row_status_reason"] = "source_authority, version_or_date, reviewer and tests_covered are required for documented evidence."
        else:
            row["row_status"] = "DOCUMENTED"
            row["row_status_reason"] = "Referenced evidence file exists and the manifest row is documented."

    @classmethod
    def _annotate_class_manifest_row(cls, row: Dict[str, Any]) -> None:
        """Add normalized selection state to one SIA 4010 class manifest row."""
        class_key = cls._normalize_validation_class(row.get("validation_class", ""))
        selected_bool = cls._normalize_selected_value(row.get("selected", ""))
        review_status = cls._normalize_review_status(row.get("review_status", ""))
        source_authority = str(row.get("source_authority", "") or "").strip()
        source_reference = str(row.get("source_reference", "") or "").strip()
        reviewer = str(row.get("reviewer", "") or "").strip()
        required_tests = str(row.get("required_tests", "") or "").strip()
        review_date = str(row.get("review_date", "") or "").strip()

        row["class_key"] = class_key
        row["selected_bool"] = selected_bool
        row["review_status_normalized"] = review_status
        row["review_status_accepted"] = review_status in SIA4010_CLASS_MANIFEST_ACCEPTED_REVIEW_STATUSES

        if not class_key:
            row["row_status"] = "UNKNOWN_CLASS"
            row["row_status_reason"] = "validation_class does not match one of the supported SIA 4010 classes."
        elif not selected_bool:
            row["row_status"] = "NOT_SELECTED"
            row["row_status_reason"] = "Class is listed for coverage but not selected."
        elif not row["review_status_accepted"]:
            row["row_status"] = "SELECTED_NOT_REVIEWED"
            row["row_status_reason"] = "Class is selected, but review_status is not an accepted documented status."
        elif not source_authority or not source_reference or not reviewer or not required_tests or not review_date:
            row["row_status"] = "SELECTED_METADATA_INCOMPLETE"
            row["row_status_reason"] = "Selected class requires required_tests, reviewer, review_date, source_authority and source_reference metadata."
        else:
            row["row_status"] = "SELECTED_DOCUMENTED"
            row["row_status_reason"] = "Selected class is documented by the class manifest."

    @classmethod
    def _annotate_official_test_result_row(cls, row: Dict[str, Any], files: Optional[List[Dict[str, Any]]] = None) -> None:
        """Add normalized state to one official SIA 4010 test-result row."""
        test_key = cls._normalize_test_id(row.get("test_id", ""))
        status = cls._normalize_review_status(row.get("status", ""))
        reviewer = str(row.get("reviewer", "") or "").strip()
        review_date = str(row.get("review_date", "") or "").strip()
        source_authority = str(row.get("source_authority", "") or "").strip()
        source_reference = str(row.get("source_reference", "") or "").strip()
        reference_file = str(row.get("reference_file", "") or "").strip()
        candidate_file = str(row.get("candidate_file", "") or "").strip()
        deviation = str(row.get("deviation", "") or "").strip()
        tolerance = str(row.get("tolerance", "") or "").strip()
        reference_file_match = cls._find_evidence_file_reference(files or [], reference_file)
        candidate_file_match = cls._find_evidence_file_reference(files or [], candidate_file)
        reference_family_match = bool(
            reference_file_match
            and cls._matches_evidence_requirement(
                reference_file_match,
                SIA4010_EVIDENCE_REQUIREMENTS["reference_comparisons"],
            )
        )
        candidate_family_match = bool(
            candidate_file_match
            and cls._matches_evidence_requirement(
                candidate_file_match,
                SIA4010_EVIDENCE_REQUIREMENTS["candidate_results"],
            )
        )

        row["test_key"] = test_key
        row["status_normalized"] = status
        row["status_is_pass"] = status in SIA4010_OFFICIAL_TEST_RESULT_PASS_STATUSES
        row["status_is_fail"] = status in SIA4010_OFFICIAL_TEST_RESULT_FAIL_STATUSES
        row["reference_file_exists"] = bool(reference_file_match)
        row["reference_file_path"] = reference_file_match.get("path", "") if reference_file_match else ""
        row["candidate_file_exists"] = bool(candidate_file_match)
        row["candidate_file_path"] = candidate_file_match.get("path", "") if candidate_file_match else ""
        row["reference_file_family_matches"] = reference_family_match
        row["candidate_file_family_matches"] = candidate_family_match
        metadata_complete = all([reviewer, review_date, source_authority, source_reference, reference_file, candidate_file, deviation, tolerance])
        row["metadata_complete"] = metadata_complete

        if not test_key:
            row["row_status"] = "UNKNOWN_TEST"
            row["row_status_reason"] = "test_id does not map to one of test_1 ... test_7."
        elif row["status_is_pass"] and not metadata_complete:
            row["row_status"] = "PASS_METADATA_INCOMPLETE"
            row["row_status_reason"] = "PASS/VALIDATED status requires reference_file, candidate_file, deviation, tolerance, reviewer, review_date, source_authority and source_reference."
        elif row["status_is_pass"] and (not reference_file_match or not candidate_file_match):
            row["row_status"] = "REFERENCED_RESULT_FILES_NOT_FOUND"
            row["row_status_reason"] = "PASS/VALIDATED status requires reference_file and candidate_file to match files present in sia4010_evidence/."
        elif row["status_is_pass"] and not reference_family_match:
            row["row_status"] = "REFERENCE_FILE_FAMILY_MISMATCH"
            row["row_status_reason"] = "reference_file must match the configured SIA4010_reference_comparison_ evidence family."
        elif row["status_is_pass"] and not candidate_family_match:
            row["row_status"] = "CANDIDATE_FILE_FAMILY_MISMATCH"
            row["row_status_reason"] = "candidate_file must match the configured SIA4010_candidate_results_ evidence family."
        elif row["status_is_pass"] and metadata_complete:
            row["row_status"] = "OFFICIAL_PASS"
            row["row_status_reason"] = "Official test result is PASS/VALIDATED with required metadata and referenced files present."
        elif row["status_is_fail"]:
            row["row_status"] = "OFFICIAL_FAIL"
            row["row_status_reason"] = "Official test result is FAIL/REJECTED."
        else:
            row["row_status"] = "NOT_REVIEWED"
            row["row_status_reason"] = "status is not an accepted official PASS/VALIDATED or FAIL value."

    @staticmethod
    def _normalize_review_status(value: Any) -> str:
        """Normalize reviewer status values from the evidence manifest."""
        return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")

    @staticmethod
    def _normalize_selected_value(value: Any) -> bool:
        """Return true when a class manifest selected field means yes."""
        normalized = str(value or "").strip().lower()
        return normalized in {"yes", "y", "true", "1", "selected", "x", "oui", "ja", "si"}

    @staticmethod
    def _normalize_validation_class(value: Any) -> str:
        """Normalize SIA 4010 validation class labels."""
        normalized = str(value or "").strip().upper().replace(" ", "")
        return normalized if normalized in SIA4010_VALIDATION_CLASSES else ""

    @staticmethod
    def _normalize_test_id(value: Any) -> str:
        """Normalize SIA 4010 test identifiers without collapsing variants."""
        raw = str(value or "").strip().lower()
        compact = raw.replace(" ", "_").replace("-", "_")
        compact = compact.replace("sia4010_", "").replace("test__", "test_")
        compact_no_underscore = compact.replace("_", "")
        supported = set(SIA4010_VALIDATION_TESTS) | set(SIA4010_TEST_VARIANT_REQUIREMENTS)
        normalized_map = {test_id.lower(): test_id for test_id in supported}
        normalized_map.update({
            test_id.lower().replace("_", ""): test_id
            for test_id in supported
        })
        if compact in normalized_map:
            return normalized_map[compact]
        if compact_no_underscore in normalized_map:
            return normalized_map[compact_no_underscore]
        prefixed = compact if compact.startswith("test_") else f"test_{compact}"
        if prefixed in normalized_map:
            return normalized_map[prefixed]
        prefixed_compact = prefixed.replace("_", "")
        if prefixed_compact in normalized_map:
            return normalized_map[prefixed_compact]
        return ""

    @staticmethod
    def _base_test_for_variant(test_id: str) -> str:
        """Return the base test key for one exact SIA 4010 variant key."""
        normalized = str(test_id or "")
        if not normalized.startswith("test_"):
            return ""
        suffix = normalized[5:]
        return f"test_{suffix[0]}" if suffix and suffix[0] in "1234567" else ""

    @staticmethod
    def _find_evidence_file_reference(files: List[Dict[str, Any]], reference: str) -> Optional[Dict[str, Any]]:
        """Return the scanned evidence file matching a manifest file reference."""
        normalized_reference = str(reference or "").strip().replace("\\", "/").lower()
        if not normalized_reference:
            return None
        reference_name = os.path.basename(normalized_reference)
        for file_data in files:
            name = str(file_data.get("name", "") or "").strip().lower()
            path = str(file_data.get("path", "") or "").strip().replace("\\", "/").lower()
            if normalized_reference in {name, path} or reference_name == name:
                return file_data
        return None

    @staticmethod
    def _evidence_key_from_manifest_family(value: str) -> str:
        """Map a manifest evidence_family value to an internal evidence key."""
        normalized = str(value or "").strip().lower()
        if normalized in SIA4010_EVIDENCE_REQUIREMENTS:
            return normalized
        compact = "".join(ch for ch in normalized if ch.isalnum())
        for key, requirement in SIA4010_EVIDENCE_REQUIREMENTS.items():
            label = "".join(ch for ch in str(requirement.get("label", "")).lower() if ch.isalnum())
            if compact and (compact == label or compact == "".join(ch for ch in key.lower() if ch.isalnum())):
                return key
        return ""

    @staticmethod
    def _matches_evidence_requirement(file_data: Dict[str, Any], requirement: Dict[str, Any]) -> bool:
        """Return true when a file follows one documented evidence naming rule."""
        filename = str(file_data.get("name", "") or "").strip()
        if not filename:
            return False

        normalized = filename.lower()
        accepted_extensions = [
            str(extension).lower()
            for extension in requirement.get("accepted_extensions", []) or []
        ]
        if accepted_extensions and not any(normalized.endswith(extension) for extension in accepted_extensions):
            return False

        required_prefixes = [
            str(prefix).lower()
            for prefix in requirement.get("required_prefixes", []) or []
        ]
        return any(normalized.startswith(prefix) for prefix in required_prefixes)

    @staticmethod
    def _requirement_for_evidence_item(evidence_item: str) -> Dict[str, Any]:
        """Return the configured evidence requirement for a required evidence label."""
        for requirement in SIA4010_EVIDENCE_REQUIREMENTS.values():
            if requirement.get("label") == evidence_item:
                return requirement
        return {}

    @staticmethod
    def _requirement_key_for_evidence_item(evidence_item: str) -> str:
        """Return the internal evidence key for a required evidence label."""
        for key, requirement in SIA4010_EVIDENCE_REQUIREMENTS.items():
            if requirement.get("label") == evidence_item:
                return key
        return ""

    @staticmethod
    def _scan_manager_reference_files(repo_dir: str) -> List[Dict[str, Any]]:
        """Detect manager-provided reference files without counting them as evidence."""
        reference_markers = (
            "sia 4010 register validierter software",
            "sia 380_2 navigator",
            "navigator",
        )
        matches: List[Dict[str, Any]] = []
        try:
            for filename in os.listdir(repo_dir):
                normalized = filename.lower()
                if not any(marker in normalized for marker in reference_markers):
                    continue
                path = os.path.join(repo_dir, filename)
                if not os.path.isfile(path):
                    continue
                matches.append({
                    "name": filename,
                    "path": os.path.relpath(path, repo_dir),
                    "size_bytes": os.path.getsize(path),
                    "role": "manager_reference_not_official_evidence",
                })
        except Exception:
            return []
        return matches

    def _calculate_heating_demand(self, rooms_data: List[RoomData]) -> Optional[float]:
        """Return annual heating demand if an official source is available."""
        return None

    def _calculate_cooling_demand(self, rooms_data: List[RoomData]) -> Optional[float]:
        """Return annual cooling demand if an official source is available."""
        return None

    def _run_sia4010_tests(self, evidence_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Return the seven SIA 4010 test statuses from official evidence state."""
        status = evidence_summary.get("status", "NOT_CHECKABLE")
        official_summary = evidence_summary.get("official_test_result_summary", {}) or {}
        recorded_pass_by_test = official_summary.get("recorded_pass_by_test", {}) or {}
        failed_by_test = official_summary.get("failed_by_test", {}) or {}
        evidence_ready = status == "READY_FOR_OFFICIAL_REVIEW"
        selected_class = self._normalize_validation_class(
            evidence_summary.get("validation_class")
        )
        selected_variants = SIA4010_CLASS_TEST_MATRIX.get(selected_class, [])

        if status == "READY_FOR_OFFICIAL_REVIEW":
            fallback_status = "READY_FOR_OFFICIAL_REVIEW"
            fallback_score = 0
            fallback_note = "All evidence families are detected; traceable PASS/VALIDATED result rows are still required before results can be recorded."
        elif status == "EVIDENCE_INCOMPLETE":
            fallback_status = "EVIDENCE_INCOMPLETE"
            fallback_score = 0
            fallback_note = "Some official evidence is detected, but at least one required evidence family is missing."
        else:
            fallback_status = "NOT_CHECKABLE"
            fallback_score = 0
            fallback_note = "Official SIA 4010 test specifications, workbooks, reference comparisons and validation class confirmation are required."

        results: Dict[str, Any] = {}
        for test_name, description in SIA4010_VALIDATION_TESTS.items():
            required_variants = [
                variant
                for variant in selected_variants
                if self._base_test_for_variant(variant) == test_name
            ]
            if not required_variants:
                required_variants = [test_name]

            pass_rows = [
                row
                for variant in required_variants
                for row in list(recorded_pass_by_test.get(variant, []) or [])
            ]
            fail_rows = [
                row
                for variant in required_variants
                for row in list(failed_by_test.get(variant, []) or [])
            ]
            recorded_pass_variants = [
                variant
                for variant in required_variants
                if recorded_pass_by_test.get(variant)
            ]
            failed_variants = [
                variant
                for variant in required_variants
                if failed_by_test.get(variant)
            ]
            all_variants_passed = len(recorded_pass_variants) == len(required_variants)
            if fail_rows:
                test_status = "FAIL"
                score = 0
                note = "At least one required exact variant is marked FAIL/REJECTED."
                official_rows = fail_rows
            elif all_variants_passed and evidence_ready:
                test_status = "OFFICIAL_RESULTS_RECORDED"
                score = 0
                note = "Every exact variant required by the selected class has a documented result row; sub-commission attestation is still required for validation."
                official_rows = pass_rows
            elif pass_rows:
                test_status = fallback_status
                score = 0
                note = "Some exact variants have PASS/VALIDATED rows, but required variants or the complete evidence package are still missing."
                official_rows = pass_rows
            else:
                test_status = fallback_status
                score = fallback_score
                note = fallback_note
                official_rows = []

            results[test_name] = {
                "status": test_status,
                "score": score,
                "description": description,
                "official_validation_note": note,
                "official_result_count": len(official_rows),
                "official_result_rows": official_rows,
                "official_result_summary": self._summarize_official_result_rows(official_rows),
                "required_variants": required_variants,
                "recorded_pass_variants": recorded_pass_variants,
                "failed_variants": failed_variants,
            }
        return results

    def _evaluate_validation_classes(
        self,
        test_results: Dict[str, Any],
        evidence_summary: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Evaluate all SIA 4010 validation classes without claiming certification."""
        selected_class = str(evidence_summary.get("validation_class") or "").upper()
        evidence_status = str(evidence_summary.get("status") or "NOT_CHECKABLE").upper()
        missing_items = evidence_summary.get("missing_items", []) or []

        class_results: Dict[str, Any] = {}
        official_summary = evidence_summary.get("official_test_result_summary", {}) or {}
        recorded_pass_by_test = official_summary.get("recorded_pass_by_test", {}) or {}
        failed_by_test = official_summary.get("failed_by_test", {}) or {}

        for class_name, tests_label in SIA4010_VALIDATION_CLASSES.items():
            required_variants = list(SIA4010_CLASS_TEST_MATRIX.get(class_name, []))
            base_tests = [self._base_test_for_variant(variant) for variant in required_variants]
            unique_base_tests = []
            for base_test in base_tests:
                if base_test and base_test not in unique_base_tests:
                    unique_base_tests.append(base_test)

            required_statuses = {
                variant: (
                    "FAIL"
                    if failed_by_test.get(variant)
                    else "OFFICIAL_RESULT_RECORDED"
                    if recorded_pass_by_test.get(variant)
                    else test_results.get(
                        self._base_test_for_variant(variant), {}
                    ).get("status", "NOT_CHECKABLE")
                )
                for variant in required_variants
            }
            recorded_pass_variants = [
                variant for variant in required_variants if recorded_pass_by_test.get(variant)
            ]
            failed_variants = [
                variant for variant in required_variants if failed_by_test.get(variant)
            ]

            is_selected = selected_class == class_name
            if selected_class and not is_selected:
                class_status = "NOT_REQUESTED"
                reason = f"Class {selected_class} is currently selected; class {class_name} is shown for full matrix coverage only."
            elif not selected_class:
                class_status = "CLASS_NOT_SELECTED"
                reason = "No validation class confirmation file was detected."
            elif failed_variants:
                class_status = "OFFICIAL_TEST_FAILED"
                reason = "At least one exact test variant required by the selected class has an official FAIL/REJECTED result."
            elif len(recorded_pass_variants) == len(required_variants) and evidence_status == "READY_FOR_OFFICIAL_REVIEW":
                class_status = "OFFICIAL_RESULTS_RECORDED"
                reason = "All exact result rows are recorded, but SIA sub-commission attestation is not independently demonstrated."
            elif evidence_status == "READY_FOR_OFFICIAL_REVIEW":
                class_status = "READY_FOR_OFFICIAL_REVIEW"
                reason = "All evidence families are present, but one or more exact class variants still lack an official result."
            elif evidence_status == "EVIDENCE_INCOMPLETE":
                class_status = "EVIDENCE_INCOMPLETE"
                reason = "The selected class is detected, but at least one official evidence family is missing."
            else:
                class_status = "NOT_CHECKABLE"
                reason = "Official SIA 4010 evidence is missing or insufficient."

            details = SIA4010_VALIDATION_CLASS_DETAILS.get(class_name, {})
            class_results[class_name] = {
                "class": class_name,
                "selected": is_selected,
                "class_status": class_status,
                "status_reason": reason,
                "required_test_aliases": required_variants,
                "required_tests": unique_base_tests,
                "required_tests_label": tests_label,
                "required_test_labels": [SIA4010_TEST_ALIAS_LABELS.get(variant, variant) for variant in required_variants],
                "required_test_statuses": required_statuses,
                "ready_required_tests": len(recorded_pass_variants),
                "recorded_pass_required_tests": len(recorded_pass_variants),
                "failed_required_tests": len(failed_variants),
                "required_test_count": len(required_variants),
                "missing_official_evidence": list(missing_items),
                "application": details.get("applications", ""),
                "solar_protection": details.get("solar_protection", ""),
                "source": details.get("source", ""),
            }
        return class_results

    def _calculate_sia4010_score(self, test_results: Dict[str, Any]) -> float:
        """Calculate the conservative SIA 4010 score from test result weights."""
        total_score = 0.0
        total_weight = 0.0
        for test_name, test_data in test_results.items():
            weight = SIA4010_TEST_WEIGHTS.get(test_name, 0.0)
            total_score += test_data["score"] * weight
            total_weight += weight
        return total_score / total_weight if total_weight > 0 else 0.0

    @staticmethod
    def _summarize_official_result_rows(rows: List[Dict[str, Any]]) -> str:
        """Return a compact audit note for official SIA 4010 test-result rows."""
        if not rows:
            return ""
        notes = []
        for row in rows[:3]:
            parts = [
                str(row.get("status", "") or row.get("row_status", "")).strip(),
                str(row.get("reference_file", "")).strip(),
                str(row.get("candidate_file", "")).strip(),
                str(row.get("reviewer", "")).strip(),
                str(row.get("review_date", "")).strip(),
                str(row.get("source_reference", "")).strip(),
            ]
            notes.append(" | ".join(part for part in parts if part))
        if len(rows) > 3:
            notes.append(f"+{len(rows) - 3} additional row(s)")
        return "; ".join(notes)

    @staticmethod
    def _calculate_evidence_readiness_score(evidence_summary: Dict[str, Any]) -> float:
        """Return a non-certification evidence completeness score."""
        required = float(evidence_summary.get("required_count", 0) or 0)
        if required <= 0:
            return 0.0
        present = float(evidence_summary.get("present_count", 0) or 0)
        class_bonus = 10.0 if evidence_summary.get("validation_class_known") else 0.0
        return min(100.0, (present / required) * 90.0 + class_bonus)
