"""SIA 4010 readiness and evidence checker.

SIA 4010 validates a calculation method or software workflow through official
test cases, evaluation workbooks, reference comparisons, and a declared
validation class. This module therefore tracks readiness and evidence quality;
it does not grant an autonomous SIA 4010 pass for a client model.
"""

import logging
import os
from typing import List, Dict, Optional, Any

from .config import (
    EMISSION_FACTORS,
    PROJECT_ROOT,
    SIA4010_EVIDENCE_DIR,
    SIA4010_EVIDENCE_FILE_PATTERNS,
    SIA4010_REQUIRED_EVIDENCE,
    SIA4010_TEST_WEIGHTS,
    SIA4010_IESVE_REGISTER_STATUS,
    SIA4010_VALIDATION_CLASSES,
    SIA4010_VALIDATION_TESTS,
)
from .model_analyzer import ModelAnalyzer, RoomData
from .rule_engine import Rule, RuleEngine, Severity

logger = logging.getLogger(__name__)


class SIA4010Checker:
    """Assess SIA 4010 validation readiness without issuing false certification."""

    def __init__(self, model_analyzer: ModelAnalyzer, rule_engine: RuleEngine):
        """Initialize the SIA 4010 checker."""
        self.model_analyzer = model_analyzer
        self.rule_engine = rule_engine
        self._setup_rules()

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

    def check_all(self) -> Dict[str, Any]:
        """Run all SIA 4010 readiness checks and return report-ready results."""
        rooms_data = self.model_analyzer.analyze_all_rooms()

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

        return {
            "energy": energy_data,
            "alerts": self.rule_engine.alerts,
            "tests": test_results,
            "score": self._calculate_sia4010_score(test_results),
            "readiness_score": self._calculate_evidence_readiness_score(evidence_summary),
            "evidence": evidence,
            "validation_class": evidence.get("validation_class"),
        }

    def _scan_sia4010_evidence(self) -> Dict[str, Any]:
        """Scan local SIA 4010 evidence files without granting official validation."""
        repo_dir = str(PROJECT_ROOT)
        evidence_dir = os.path.join(repo_dir, SIA4010_EVIDENCE_DIR)
        files: List[Dict[str, Any]] = []
        if os.path.isdir(evidence_dir):
            for root, _dirs, filenames in os.walk(evidence_dir):
                for filename in filenames:
                    path = os.path.join(root, filename)
                    rel_path = os.path.relpath(path, repo_dir)
                    try:
                        size_bytes = os.path.getsize(path)
                    except Exception:
                        size_bytes = None
                    files.append({
                        "name": filename,
                        "path": rel_path,
                        "size_bytes": size_bytes,
                    })

        evidence: Dict[str, Any] = {
            "evidence_dir": evidence_dir,
            "files": files,
            "classified_files": [],
            "classified_file_count": 0,
            "validation_class": None,
            "manager_reference_files": self._scan_manager_reference_files(repo_dir),
            "software_register_status": dict(SIA4010_IESVE_REGISTER_STATUS),
        }
        candidate_files = [
            file_data
            for file_data in files
            if not self._is_evidence_folder_note(file_data.get("name", ""))
        ]
        filenames_blob = " ".join(file_data["name"].lower() for file_data in candidate_files)
        for key, patterns in SIA4010_EVIDENCE_FILE_PATTERNS.items():
            matched = [
                file_data
                for file_data in candidate_files
                if any(pattern.lower() in file_data["name"].lower() for pattern in patterns)
            ]
            evidence[key] = {
                "present": bool(matched),
                "files": matched,
            }
            for file_data in matched:
                if file_data not in evidence["classified_files"]:
                    evidence["classified_files"].append(file_data)

        evidence["classified_file_count"] = len(evidence["classified_files"])

        class_markers = ["4b", "4a", "3", "2b", "2a", "1b", "1a", "5"]
        for marker in class_markers:
            if f"class_{marker}" in filenames_blob or f"classe_{marker}" in filenames_blob or f"class{marker}" in filenames_blob:
                evidence["validation_class"] = marker.upper()
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
        validation_class = evidence.get("validation_class")
        class_is_known = validation_class in SIA4010_VALIDATION_CLASSES
        all_required_present = len(missing_items) == 0
        classified_count = int(evidence.get("classified_file_count", 0) or 0)

        if all_required_present and class_is_known:
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
            "validation_class": validation_class,
            "validation_class_known": class_is_known,
            "classified_file_count": classified_count,
            "software_register_status": evidence.get("software_register_status", {}),
            "manager_reference_files": evidence.get("manager_reference_files", []),
        }

    def _add_evidence_status_alert(self, evidence_summary: Dict[str, Any]) -> None:
        """Add one precise alert describing current official evidence status."""
        status = evidence_summary["status"]
        missing_items = evidence_summary["missing_items"]
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
            self.rule_engine.add_alert(
                rule="SIA4010_VALIDATION_EVIDENCE_INCOMPLETE",
                description=f"SIA 4010 evidence is partial: {present_count}/{required_count} required evidence families detected.",
                severity=Severity.MEDIUM,
                category="SIA4010 Validation",
                recommendation="Complete the missing official evidence families before any SIA 4010 validation wording: "
                + "; ".join(missing_items),
                data=evidence_summary,
            )
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
            self.rule_engine.add_alert(
                rule=f"SIA4010_EVIDENCE_FAMILY_MISSING_{slug[:48]}",
                description=f"Missing SIA 4010 evidence family: {item}.",
                severity=severity,
                category="SIA4010 Evidence",
                recommendation="Place the corresponding official evidence file in sia4010_evidence/ using the documented filename prefixes, then rerun the checker.",
                data={"missing_evidence_family": item},
            )

    @staticmethod
    def _is_evidence_folder_note(filename: str) -> bool:
        """Exclude local README/docs from SIA 4010 evidence classification."""
        normalized = str(filename or "").strip().lower()
        return normalized in {"readme.md", "readme.txt", ".gitkeep"} or normalized.startswith("readme.")

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

    def _calculate_co2_emissions(self, energy_sources: Dict[str, Any], total_area: float) -> float:
        """Calculate project CO2 emissions as a separate non-SIA4010 indicator."""
        total_co2 = 0.0
        for source in energy_sources.values():
            try:
                consumption = source.get_annual_consumption()
                emission_factor = EMISSION_FACTORS.get(source.type, 0.0)
                total_co2 += consumption * emission_factor
            except Exception as e:
                logger.error("Error while calculating CO2 emissions: %s", e)
        return total_co2 / total_area if total_area > 0 else 0.0

    def _calculate_renewable_energy_share(self, energy_sources: Dict[str, Any], total_energy: float) -> float:
        """Calculate renewable energy share as a separate project indicator."""
        renewable_energy = 0.0
        for source in energy_sources.values():
            try:
                if source.type in ["solar", "wind", "biomass"]:
                    renewable_energy += source.get_annual_consumption()
            except Exception as e:
                logger.error("Error while calculating renewable energy share: %s", e)
        return renewable_energy / total_energy if total_energy > 0 else 0.0

    def _run_sia4010_tests(self, evidence_summary: Dict[str, Any]) -> Dict[str, Any]:
        """Return the seven SIA 4010 test statuses from official evidence state."""
        status = evidence_summary.get("status", "NOT_CHECKABLE")
        if status == "READY_FOR_OFFICIAL_REVIEW":
            test_status = "READY_FOR_OFFICIAL_REVIEW"
            note = "All evidence families are detected; official reviewer acceptance is still required before VALIDATED."
        elif status == "EVIDENCE_INCOMPLETE":
            test_status = "EVIDENCE_INCOMPLETE"
            note = "Some official evidence is detected, but at least one required evidence family is missing."
        else:
            test_status = "NOT_CHECKABLE"
            note = "Official SIA 4010 test specifications, workbooks, reference comparisons and validation class confirmation are required."

        return {
            test_name: {
                "status": test_status,
                "score": 0,
                "description": description,
                "official_validation_note": note,
            }
            for test_name, description in SIA4010_VALIDATION_TESTS.items()
        }

    def _calculate_sia4010_score(self, test_results: Dict[str, Any]) -> float:
        """Calculate an official SIA 4010 score only from validated tests."""
        total_score = 0.0
        total_weight = 0.0
        for test_name, test_data in test_results.items():
            weight = SIA4010_TEST_WEIGHTS.get(test_name, 0.0)
            total_score += test_data["score"] * weight
            total_weight += weight
        return total_score / total_weight if total_weight > 0 else 0.0

    @staticmethod
    def _calculate_evidence_readiness_score(evidence_summary: Dict[str, Any]) -> float:
        """Return a non-certification evidence completeness score."""
        required = float(evidence_summary.get("required_count", 0) or 0)
        if required <= 0:
            return 0.0
        present = float(evidence_summary.get("present_count", 0) or 0)
        class_bonus = 10.0 if evidence_summary.get("validation_class_known") else 0.0
        return min(100.0, (present / required) * 90.0 + class_bonus)
