"""Fail-closed APS binding and evaluation hook for Test 2 diagnostic 2E1.

The current runtime evidence qualifies only the zone-level ``Window solar
gains`` series.  Surface irradiance candidates were visible in the probe, but
no surface identity/read path was qualified, and no direct/diffuse/secondary
or transmitted-power series was confirmed.  This module records that exact
1-of-8 coverage and extracts nothing by token similarity.

The evaluation entry point also requires checksummed simulation evidence for
the exact fixed-closed 2E1 scenario.  A Case 600 or dynamic 2A APS file cannot
be evaluated accidentally as 2E1.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple, Union

from ..exceptions import ConfigurationError
from .qualified_aps import QualifiedApsBindings, Sia4010QualifiedApsExtractor
from .test2a_diagnostic_evaluation import (
    Test2A2E1DiagnosticEvaluation,
    Test2A2E1ReferenceDataset,
    evaluate_test2a_2e1_diagnostic,
)
from .test2a_diagnostic_workbook import Test2ADiagnosticWorkbookBinding

APS_CONTRACT_SCHEMA_VERSION = "1.0"
EXPECTED_SCENARIO_ID = "SIA4010_TEST_2A_2E1"
EXPECTED_VARIANT = "test_2A"
EXPECTED_CASE_ID = "2E1"
EXPECTED_FIXED_STATE = "ALWAYS_CLOSED"

_TOTAL_GAIN_SERIES = "hourly_room_solar_heat_gain_total"
_TOTAL_GAIN_QUANTITY = "total_room_solar_heat_gain_power"


def _sha256(path: Path) -> str:
    """Return the lowercase SHA-256 of one artifact."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


@dataclass(frozen=True)
class Test2A2E1ApsSeriesBinding:
    """Evidence status for one official 2E1 workbook series."""

    series_id: str
    status: str
    quantity_id: Optional[str]
    aps_varname: Optional[str]
    display_name: Optional[str]
    model_level: Optional[str]
    metric_unit: Optional[str]
    reason: str


@dataclass(frozen=True)
class Test2A2E1ApsBindingContract:
    """Exact APS coverage of all eight official diagnostic series."""

    source_binding_path: Path
    source_probe_filename: str
    source_probe_sha256: str
    series: Tuple[Test2A2E1ApsSeriesBinding, ...]

    @property
    def bound_count(self) -> int:
        """Return the number of runtime-qualified series."""

        return sum(item.status == "RUNTIME_METADATA_CONFIRMED" for item in self.series)

    @property
    def complete(self) -> bool:
        """Return whether all official series have qualified APS bindings."""

        return self.bound_count == len(self.series)

    @property
    def blockers(self) -> Tuple[str, ...]:
        """Return one stable blocker per unbound official series."""

        return tuple(
            "APS_2E1_BINDING_REQUIRED:{}".format(item.series_id)
            for item in self.series
            if item.status != "RUNTIME_METADATA_CONFIRMED"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return an audit-ready binding matrix."""

        return {
            "schema_version": APS_CONTRACT_SCHEMA_VERSION,
            "diagnostic_case_id": EXPECTED_CASE_ID,
            "source_binding_path": str(self.source_binding_path),
            "source_probe_filename": self.source_probe_filename,
            "source_probe_sha256": self.source_probe_sha256,
            "series": [asdict(item) for item in self.series],
            "bound_count": self.bound_count,
            "required_count": len(self.series),
            "complete": self.complete,
            "blockers": list(self.blockers),
            "claim_guardrail": (
                "Only exact runtime-confirmed metadata is bound. Surface-level "
                "or similarly named variables are not selected without a "
                "qualified surface/opening identity and complete annual read."
            ),
        }


@dataclass(frozen=True)
class Test2A2E1ApsEvaluationReceipt:
    """Checksummed APS provenance plus the conservative diagnostic outcome."""

    aps_path: Path
    aps_sha256: str
    binding_contract: Test2A2E1ApsBindingContract
    extracted_series_ids: Tuple[str, ...]
    evaluation: Test2A2E1DiagnosticEvaluation

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe evaluation receipt."""

        return {
            "scenario_id": EXPECTED_SCENARIO_ID,
            "variant": EXPECTED_VARIANT,
            "case_id": EXPECTED_CASE_ID,
            "fixed_shade_state": EXPECTED_FIXED_STATE,
            "aps_path": str(self.aps_path),
            "aps_sha256": self.aps_sha256,
            "binding_contract": self.binding_contract.to_dict(),
            "extracted_series_ids": list(self.extracted_series_ids),
            "evaluation": self.evaluation.to_dict(),
            "claim_guardrail": (
                "This receipt is a non-scored 2E1 technical comparison. It is "
                "not a SIA PASS and cannot qualify the dynamic 2A controller."
            ),
        }


def build_test2a_2e1_aps_binding_contract(
    bindings: QualifiedApsBindings,
    workbook_binding: Test2ADiagnosticWorkbookBinding,
) -> Test2A2E1ApsBindingContract:
    """Map only runtime-qualified APS quantities to the eight workbook series."""

    qualified_total = bindings.variables.get(_TOTAL_GAIN_QUANTITY)
    rows = []
    for item in workbook_binding.series:
        if item.series_id == _TOTAL_GAIN_SERIES and qualified_total is not None:
            rows.append(
                Test2A2E1ApsSeriesBinding(
                    series_id=item.series_id,
                    status="RUNTIME_METADATA_CONFIRMED",
                    quantity_id=_TOTAL_GAIN_QUANTITY,
                    aps_varname=qualified_total.aps_varname,
                    display_name=qualified_total.display_name,
                    model_level=qualified_total.model_level,
                    metric_unit=qualified_total.metric_unit,
                    reason=(
                        "Exact zone-level ResultsReader identity and units are "
                        "confirmed; physical equivalence remains the purpose of "
                        "the 2E1 diagnostic."
                    ),
                )
            )
            continue
        if item.series_id.startswith("hourly_incident_"):
            reason = (
                "The probe exposed surface-level irradiance candidates, but "
                "no exact exterior window surface identity and complete "
                "surface-series read-back were qualified."
            )
        elif item.series_id == ("hourly_transmitted_solar_radiation_excluding_secondary"):
            reason = (
                "The existing binding file explicitly leaves transmitted "
                "solar radiation unbound because no qualified power series "
                "was demonstrated."
            )
        else:
            reason = (
                "No exact runtime-confirmed APS variable exists for this "
                "direct, diffuse or secondary diagnostic component."
            )
        rows.append(
            Test2A2E1ApsSeriesBinding(
                series_id=item.series_id,
                status="UNBOUND_RUNTIME_EVIDENCE_REQUIRED",
                quantity_id=None,
                aps_varname=None,
                display_name=None,
                model_level=None,
                metric_unit=None,
                reason=reason,
            )
        )
    return Test2A2E1ApsBindingContract(
        source_binding_path=bindings.path.resolve(),
        source_probe_filename=str(bindings.source_probe.get("filename", "")),
        source_probe_sha256=str(bindings.source_probe.get("sha256", "")),
        series=tuple(rows),
    )


def extract_test2a_2e1_candidate_series(
    extractor: Sia4010QualifiedApsExtractor,
    contract: Test2A2E1ApsBindingContract,
) -> Dict[str, Tuple[float, ...]]:
    """Extract only complete hourly series authorized by the contract."""

    result: Dict[str, Tuple[float, ...]] = {}
    for item in contract.series:
        if item.status != "RUNTIME_METADATA_CONFIRMED" or item.quantity_id is None:
            continue
        values = extractor.hourly_power_watts(item.quantity_id)
        if len(values) == 8760:
            result[item.series_id] = values
    return result


def _validate_simulation_evidence(
    aps_path: Path,
    evidence: Mapping[str, Any],
) -> str:
    """Require the exact completed fixed-closed scenario and APS checksum."""

    expected = {
        "scenario_id": EXPECTED_SCENARIO_ID,
        "variant": EXPECTED_VARIANT,
        "case_id": EXPECTED_CASE_ID,
        "fixed_shade_state": EXPECTED_FIXED_STATE,
        "simulation_completed": True,
    }
    mismatches = {
        key: {"expected": value, "actual": evidence.get(key)}
        for key, value in expected.items()
        if evidence.get(key) != value
    }
    if mismatches:
        raise ConfigurationError(
            "2E1 simulation evidence mismatch: {}".format(mismatches)
        )
    evidence_path = Path(str(evidence.get("aps_path", ""))).resolve()
    if evidence_path != aps_path.resolve():
        raise ConfigurationError(
            "2E1 simulation evidence APS path does not match the evaluated file"
        )
    actual_sha = _sha256(aps_path)
    if str(evidence.get("aps_sha256", "")).lower() != actual_sha:
        raise ConfigurationError("2E1 simulation evidence APS SHA-256 does not match")
    return actual_sha


def evaluate_test2a_2e1_qualified_aps(
    *,
    results_file: Any,
    room_id: Any,
    aps_path: Union[str, Path],
    bindings: QualifiedApsBindings,
    workbook_binding: Test2ADiagnosticWorkbookBinding,
    reference: Test2A2E1ReferenceDataset,
    simulation_evidence: Mapping[str, Any],
) -> Test2A2E1ApsEvaluationReceipt:
    """Extract and technically compare one exact, evidenced 2E1 APS file."""

    aps = Path(aps_path)
    if not aps.is_file():
        raise ConfigurationError("2E1 APS evidence does not exist: {}".format(aps))
    aps_sha = _validate_simulation_evidence(aps, simulation_evidence)
    contract = build_test2a_2e1_aps_binding_contract(
        bindings,
        workbook_binding,
    )
    extractor = Sia4010QualifiedApsExtractor(
        results_file,
        room_id,
        bindings,
        "{}#sha256={}".format(aps, aps_sha),
    )
    candidate = extract_test2a_2e1_candidate_series(extractor, contract)
    required_series_ids = tuple(item.series_id for item in workbook_binding.series)
    evaluation = evaluate_test2a_2e1_diagnostic(
        candidate,
        reference,
        required_series_ids,
    )
    return Test2A2E1ApsEvaluationReceipt(
        aps_path=aps.resolve(),
        aps_sha256=aps_sha,
        binding_contract=contract,
        extracted_series_ids=tuple(sorted(candidate)),
        evaluation=evaluation,
    )


def write_test2a_2e1_aps_evaluation(
    output_path: Union[str, Path],
    receipt: Test2A2E1ApsEvaluationReceipt,
    reference: Test2A2E1ReferenceDataset,
) -> Path:
    """Write checksummed APS provenance and the technical 2E1 comparison."""

    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = receipt.to_dict()
    payload["reference_dataset"] = reference.to_dict()
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    checksum = _sha256(path)
    path.with_suffix(path.suffix + ".sha256").write_text(
        "{}  {}\n".format(checksum, path.name),
        encoding="ascii",
    )
    return path
