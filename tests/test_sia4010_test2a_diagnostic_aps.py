"""Tests for fail-closed Test 2A diagnostic APS extraction."""

import hashlib
import json
import shutil
import unittest
from pathlib import Path

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.frequency_distribution import (
    DistributionBand,
)
from swiss_sia.reference_model.sia4010.qualified_aps import (
    QualifiedApsBindings,
)
from swiss_sia.reference_model.sia4010.test2a_diagnostic_aps import (
    EXPECTED_CASE_ID,
    EXPECTED_FIXED_STATE,
    EXPECTED_SCENARIO_ID,
    EXPECTED_VARIANT,
    build_test2a_2e1_aps_binding_contract,
    evaluate_test2a_2e1_qualified_aps,
    write_test2a_2e1_aps_evaluation,
)
from swiss_sia.reference_model.sia4010.test2a_diagnostic_evaluation import (
    DiagnosticAnnualReference,
    REFERENCE_ONLY_STATUS,
    Test2A2E1ReferenceDataset,
)
from swiss_sia.reference_model.sia4010.test2a_diagnostic_workbook import (
    load_test2a_diagnostic_workbook_binding,
)

ROOT = Path(__file__).resolve().parents[1]
BINDINGS = ROOT / "config" / "sia4010_aps_bindings_ve_runtime.json"
WORKBOOK = ROOT / "SIA_4010_geteilter_Link" / "Test2" / "Resultaterfassung_Test2.xlsx"
WORK_ROOT = ROOT / ".codex_tmp" / "test2a_diagnostic_aps"
TOTAL_GAIN = "hourly_room_solar_heat_gain_total"
TRANSMITTED = "hourly_transmitted_solar_radiation_excluding_secondary"


class _Results:
    results_per_day = 48

    @staticmethod
    def get_variables():
        return [
            {
                "aps_varname": "Window solar gains",
                "display_name": "Solar gain",
                "model_level": "z",
                "units_type": "power",
            }
        ]

    @staticmethod
    def get_units():
        return {
            "power": {
                "units_metric": {
                    "display_name": "kW",
                    "divisor": 1000.0,
                    "offset": 0.0,
                }
            }
        }

    @staticmethod
    def get_room_results(_room_id, _aps_var, _display_name, _level):
        return [200.0] * 17520


def _sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _reference(workbook_binding):
    annual = (
        DiagnosticAnnualReference(
            series_id=TOTAL_GAIN,
            unit="kWh",
            program_values=(("LOW", 1000.0), ("HIGH", 2000.0)),
            minimum=1000.0,
            maximum=2000.0,
            mean=1500.0,
            source_locator="controlled total-gain reference",
        ),
        DiagnosticAnnualReference(
            series_id=TRANSMITTED,
            unit="kWh",
            program_values=(("LOW", 500.0), ("HIGH", 1000.0)),
            minimum=500.0,
            maximum=1000.0,
            mean=750.0,
            source_locator="controlled transmitted reference",
        ),
    )
    distribution = DistributionBand(
        quantity="Solarer Wärmeeintrag gesamt",
        unit="W",
        upper_edges=(100.0, 300.0),
        lower_counts=(0.0, 0.0, 0.0),
        upper_counts=(8760.0, 8760.0, 8760.0),
        program_count=2,
        source_locator="controlled distribution",
    )
    return Test2A2E1ReferenceDataset(
        workbook_path=WORKBOOK,
        workbook_sha256=workbook_binding.workbook_sha256,
        annual_references=annual,
        total_gain_distribution=distribution,
    )


@unittest.skipUnless(WORKBOOK.is_file(), "official Test 2 workbook unavailable")
class Test2A2E1ApsTests(unittest.TestCase):
    """Only runtime-proven APS identities may enter the 2E1 comparator."""

    @classmethod
    def setUpClass(cls):
        cls.bindings = QualifiedApsBindings.load(BINDINGS)
        cls.workbook_binding = load_test2a_diagnostic_workbook_binding(WORKBOOK)
        cls.reference = _reference(cls.workbook_binding)

    def setUp(self):
        self.output_dir = (
            WORK_ROOT
            / hashlib.sha256(self._testMethodName.encode("utf-8")).hexdigest()[:12]
        )
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)
        self.output_dir.mkdir(parents=True)
        self.aps_path = self.output_dir / "test2a_2e1.aps"
        self.aps_path.write_bytes(b"controlled 2E1 APS evidence")

    def tearDown(self):
        if self.output_dir.exists():
            shutil.rmtree(self.output_dir)

    def _evidence(self):
        return {
            "scenario_id": EXPECTED_SCENARIO_ID,
            "variant": EXPECTED_VARIANT,
            "case_id": EXPECTED_CASE_ID,
            "fixed_shade_state": EXPECTED_FIXED_STATE,
            "simulation_completed": True,
            "aps_path": str(self.aps_path.resolve()),
            "aps_sha256": _sha256(self.aps_path),
        }

    def test_contract_records_exactly_one_of_eight_runtime_bindings(self):
        contract = build_test2a_2e1_aps_binding_contract(
            self.bindings,
            self.workbook_binding,
        )
        self.assertEqual(contract.bound_count, 1)
        self.assertEqual(len(contract.series), 8)
        self.assertFalse(contract.complete)
        self.assertEqual(len(contract.blockers), 7)
        bound = [
            item
            for item in contract.series
            if item.status == "RUNTIME_METADATA_CONFIRMED"
        ]
        self.assertEqual(bound[0].series_id, TOTAL_GAIN)
        self.assertEqual(
            bound[0].quantity_id,
            "total_room_solar_heat_gain_power",
        )

    def test_evaluation_extracts_only_qualified_total_gain(self):
        receipt = evaluate_test2a_2e1_qualified_aps(
            results_file=_Results(),
            room_id="R1",
            aps_path=self.aps_path,
            bindings=self.bindings,
            workbook_binding=self.workbook_binding,
            reference=self.reference,
            simulation_evidence=self._evidence(),
        )
        self.assertEqual(receipt.extracted_series_ids, (TOTAL_GAIN,))
        self.assertEqual(receipt.evaluation.status, REFERENCE_ONLY_STATUS)
        self.assertEqual(
            receipt.evaluation.technical_alignment,
            "WITHIN_TECHNICAL_REFERENCE_ENVELOPE",
        )
        self.assertAlmostEqual(
            dict(receipt.evaluation.candidate_annual_kwh)[TOTAL_GAIN],
            1752.0,
        )
        self.assertFalse(receipt.evaluation.required_eight_series_complete)
        self.assertFalse(receipt.evaluation.engineering_review_ready)
        self.assertFalse(receipt.evaluation.compliance_pass)
        self.assertFalse(receipt.evaluation.optical_mapping_qualified)

    def test_wrong_simulation_identity_is_rejected_before_reading_aps(self):
        evidence = self._evidence()
        evidence["scenario_id"] = "SIA4010_TEST_1_600"
        with self.assertRaisesRegex(
            ConfigurationError,
            "simulation evidence mismatch",
        ):
            evaluate_test2a_2e1_qualified_aps(
                results_file=_Results(),
                room_id="R1",
                aps_path=self.aps_path,
                bindings=self.bindings,
                workbook_binding=self.workbook_binding,
                reference=self.reference,
                simulation_evidence=evidence,
            )

    def test_writes_checksummed_provenance_without_sia_pass(self):
        receipt = evaluate_test2a_2e1_qualified_aps(
            results_file=_Results(),
            room_id="R1",
            aps_path=self.aps_path,
            bindings=self.bindings,
            workbook_binding=self.workbook_binding,
            reference=self.reference,
            simulation_evidence=self._evidence(),
        )
        output = self.output_dir / "evaluation.json"
        write_test2a_2e1_aps_evaluation(
            output,
            receipt,
            self.reference,
        )
        payload = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(payload["binding_contract"]["bound_count"], 1)
        self.assertFalse(payload["evaluation"]["compliance_pass"])
        checksum = output.with_suffix(".json.sha256")
        self.assertTrue(checksum.read_text(encoding="ascii").startswith(_sha256(output)))


if __name__ == "__main__":
    unittest.main()
