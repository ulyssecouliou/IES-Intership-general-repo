"""Source-bound Test 2A generator-contract tests."""

import hashlib
import json
import shutil
import unittest
from pathlib import Path
from unittest import mock

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.normalized_external_inputs import (
    NormalizedIsoTestCell,
    NormalizedLayer,
    NormalizedOfficeProfiles,
    NormalizedOpaqueConstruction,
    NormalizedUsageProfile,
    NormalizedVeProfileGraph,
    NormalizedVeProfileNode,
    NormalizedWeatherBinding,
    Test2AExternalBindings,
)
from swiss_sia.reference_model.sia4010.test2a_source_bundle import (
    MISSING_NATIVE_PROFILE_GRAPH_BLOCKER,
    RUNTIME_BLOCKERS,
    build_test2a_source_bound_bundle,
)


ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT / ".codex_tmp" / "test2a_source_bundle"


def _construction(identifier):
    return NormalizedOpaqueConstruction(
        construction_id=identifier,
        layers_outside_to_inside=(
            NormalizedLayer(
                material_id=identifier + "_material",
                thickness_m=0.1,
                conductivity_w_mk=0.1,
                density_kg_m3=100.0,
                specific_heat_j_kgk=1000.0,
            ),
        ),
        inside_ir_emissivity=0.9,
        outside_ir_emissivity=0.9,
        inside_solar_absorptance=0.6,
        outside_solar_absorptance=0.6,
    )


def _bindings(project, *, width=8.0, with_profile_graph=False):
    profiles = tuple(
        NormalizedUsageProfile(
            key=key,
            profile_type="daily",
            reference=key.upper(),
            modulating=True,
            units=-1,
            data=((0.0, 0.0, ""), (24.0, 0.0, "")),
            source_locator="controlled schedule row",
        )
        for key in (
            "occupancy_profile",
            "equipment_profile",
            "lighting_profile",
        )
    )
    profile_graph = None
    if with_profile_graph:
        profile_graph = NormalizedVeProfileGraph(
            nodes=(
                NormalizedVeProfileNode(
                    key="controlled_daily",
                    profile_type="daily",
                    reference="CONTROLLED_DAILY",
                    modulating=True,
                    units=-1,
                    data=((0.0, 0.0, ""), (24.0, 0.0, "")),
                    source_locator="controlled daily rows",
                ),
                NormalizedVeProfileNode(
                    key="controlled_weekly",
                    profile_type="weekly",
                    reference="CONTROLLED_WEEKLY",
                    modulating=True,
                    units=-1,
                    data=tuple(
                        {"profile_ref": "controlled_daily"} for _ in range(12)
                    ),
                    source_locator="controlled weekly mapping",
                ),
                NormalizedVeProfileNode(
                    key="controlled_yearly",
                    profile_type="yearly",
                    reference="CONTROLLED_YEARLY",
                    modulating=True,
                    units=-1,
                    data=(
                        (
                            {"profile_ref": "controlled_weekly"},
                            1,
                            365,
                        ),
                    ),
                    source_locator="controlled annual mapping",
                ),
            ),
            outputs=tuple(
                (role, "controlled_yearly")
                for role in (
                    "occupancy_profile",
                    "equipment_profile",
                    "lighting_profile",
                )
            ),
            source_locator="controlled VE graph",
        )
    return Test2AExternalBindings(
        iso_cell=NormalizedIsoTestCell(
            width_m=width,
            depth_m=6.0,
            height_m=2.7,
            window_count=2,
            window_width_m=3.0,
            window_height_m=2.0,
            window_sill_m=0.2,
            window_side_margin_m=0.5,
            window_gap_m=1.0,
            inside_surface_coefficient_w_m2k=8.0,
            outside_surface_coefficient_w_m2k=25.0,
            external_wall=_construction("wall"),
            roof=_construction("roof"),
            floor=_construction("floor"),
            source_locator="controlled ISO source",
        ),
        weather=NormalizedWeatherBinding(
            weather_file=project / "authorized.epw",
            weather_sha256="a" * 64,
            weather_format="EPW",
            hour_count=8760,
            station_name="controlled station",
            dataset_identity="controlled dataset",
            source_locator="controlled weather source",
        ),
        office_profiles=NormalizedOfficeProfiles(
            use_category="controlled office category",
            value_set="controlled standard set",
            calendar_basis="controlled annual calendar",
            annual_simultaneity_method="controlled method",
            profiles=profiles,
            source_locator="controlled SIA 2024 source",
            ve_profile_graph=profile_graph,
        ),
        evidence_sha256=(
            ("iso52016_2017_chapter7_test_cell", "1" * 64),
            ("sia2028_dry_normal_zurich_kloten", "2" * 64),
            ("sia2024_office_3_1_standard_profiles", "3" * 64),
        ),
    )


class Test2ASourceBundleTests(unittest.TestCase):
    """The conditional bundle is source-complete but never overclaims VE."""

    def setUp(self):
        self.project = WORK_ROOT / hashlib.sha256(
            self._testMethodName.encode("utf-8")
        ).hexdigest()[:12]
        if self.project.exists():
            shutil.rmtree(self.project)
        self.project.mkdir(parents=True)
        (self.project / "sia4010_external_inputs.json").write_text(
            '{"schema_version":"1.0","inputs":{}}\n',
            encoding="utf-8",
        )

    def tearDown(self):
        if self.project.exists():
            shutil.rmtree(self.project)

    def _build(self, bindings):
        readiness = mock.Mock()
        readiness.to_dict.return_value = {
            "status": "READY_FOR_BINDING",
            "ready_for_binding": True,
        }
        with mock.patch(
            "swiss_sia.reference_model.sia4010.test2a_source_bundle."
            "Sia4010ExternalInputManifest.load",
            return_value=mock.Mock(),
        ), mock.patch(
            "swiss_sia.reference_model.sia4010.test2a_source_bundle."
            "external_input_readiness",
            return_value=readiness,
        ), mock.patch(
            "swiss_sia.reference_model.sia4010.test2a_source_bundle."
            "load_test2a_external_bindings",
            return_value=bindings,
        ):
            return build_test2a_source_bound_bundle(self.project, ROOT)

    def _write_qualification(self, filename, fields):
        diagnostics = (
            self.project / "sia4010_artifacts" / "diagnostics"
        )
        diagnostics.mkdir(parents=True, exist_ok=True)
        payload = {
            "status": "PASS",
            "project": {"path": str(self.project.resolve())},
            "scenario": {"variant": "test_2A", "case_id": "2A"},
        }
        payload.update(fields)
        report = diagnostics / filename
        report.write_text(
            json.dumps(payload, indent=2) + "\n",
            encoding="utf-8",
        )
        checksum = hashlib.sha256(report.read_bytes()).hexdigest()
        report.with_suffix(report.suffix + ".sha256").write_text(
            "{}  {}\n".format(checksum, report.name),
            encoding="utf-8",
        )

    def test_writes_deterministic_generator_contract_without_mutation_claim(self):
        receipt = self._build(_bindings(self.project))
        self.assertEqual(
            receipt.status,
            "SOURCE_BINDINGS_READY_PROFILE_GRAPH_REQUIRED",
        )
        self.assertFalse(receipt.mutation_supported)
        self.assertEqual(
            receipt.runtime_blockers,
            RUNTIME_BLOCKERS + (MISSING_NATIVE_PROFILE_GRAPH_BLOCKER,),
        )
        payload = json.loads(
            receipt.generator_input_path.read_text(encoding="utf-8")
        )
        self.assertEqual(payload["variant"], "test_2A")
        self.assertEqual(payload["case_id"], "2A")
        self.assertFalse(payload["runtime_contract"]["mutation_supported"])
        self.assertEqual(
            payload["official_test2_parameters"]["glazing_g_value"], 0.545
        )
        optical = payload["fabric_awning_optical_diagnostic"]
        self.assertEqual(
            optical["workbook_binding_status"],
            "OFFICIAL_2E1_SCHEMA_BOUND",
        )
        self.assertNotIn(
            "OFFICIAL_TEST2_DIAGNOSTIC_2E1_SERIES_NOT_BOUND",
            optical["blockers"],
        )
        aps_binding = payload[
            "fabric_awning_aps_diagnostic_binding"
        ]
        self.assertEqual(aps_binding["bound_count"], 1)
        self.assertEqual(aps_binding["required_count"], 8)
        self.assertFalse(aps_binding["complete"])
        self.assertEqual(len(aps_binding["blockers"]), 7)
        self.assertIn(
            "VE_TEST2A_FIXED_CLOSED_OPTICAL_MAPPING_NOT_QUALIFIED",
            optical["blockers"],
        )
        self.assertEqual(
            payload["source_contracts"]["official_test2_result_workbook"][
                "binding_status"
            ],
            "OFFICIAL_2E1_SCHEMA_BOUND",
        )
        self.assertTrue(receipt.audit_path.is_file())

    def test_native_profile_graph_removes_only_the_source_graph_blocker(self):
        receipt = self._build(
            _bindings(self.project, with_profile_graph=True)
        )
        self.assertEqual(
            receipt.status,
            "SOURCE_BINDINGS_READY_VE_BINDING_REQUIRED",
        )
        self.assertEqual(receipt.runtime_blockers, RUNTIME_BLOCKERS)
        payload = json.loads(
            receipt.generator_input_path.read_text(encoding="utf-8")
        )
        profile_contract = payload["runtime_contract"][
            "sia2024_native_profile_graph"
        ]
        self.assertTrue(profile_contract["present"])
        self.assertEqual(
            profile_contract["required_profile_types"],
            ["daily", "weekly", "yearly"],
        )

    def test_three_checksum_valid_storage_receipts_advance_honest_status(self):
        self._write_qualification(
            "sia2a_profiles_controlled.json",
            {
                "mutation_performed": True,
                "other_ve_objects_changed": False,
                "simulation_performed": False,
                "compliance_claim_allowed": False,
            },
        )
        self._write_qualification(
            "sia2a_external_shade_setter_controlled.json",
            {
                "cdb_setter_qualified": True,
                "dynamic_equivalence_qualified": False,
                "full_test2a_mutation_authorized": False,
                "compliance_claim_allowed": False,
            },
        )
        self._write_qualification(
            "sia2a_2e1_optical_setter_controlled.json",
            {
                "fixed_closed_storage_qualified": True,
                "fixed_closed_optical_mapping_qualified": False,
                "diagnostic_candidate_generation_authorized": False,
                "compliance_claim_allowed": False,
            },
        )
        receipt = self._build(
            _bindings(self.project, with_profile_graph=True)
        )
        self.assertEqual(
            receipt.status,
            "RUNTIME_STORAGE_QUALIFIED_MODEL_BINDING_REQUIRED",
        )
        payload = json.loads(
            receipt.generator_input_path.read_text(encoding="utf-8")
        )
        evidence = payload["runtime_contract"][
            "qualification_evidence"
        ]
        self.assertTrue(evidence["all_storage_boundaries_qualified"])
        self.assertFalse(
            payload["runtime_contract"]["mutation_supported"]
        )
        audit = json.loads(receipt.audit_path.read_text(encoding="utf-8"))
        self.assertIn(
            "dynamic shade semantics",
            audit["next_action"],
        )

    def test_tampered_qualification_receipt_never_advances_status(self):
        self._write_qualification(
            "sia2a_profiles_controlled.json",
            {
                "mutation_performed": True,
                "other_ve_objects_changed": False,
                "simulation_performed": False,
                "compliance_claim_allowed": False,
            },
        )
        report = next(
            (
                self.project / "sia4010_artifacts" / "diagnostics"
            ).glob("sia2a_profiles_*.json")
        )
        report.write_text("{}\n", encoding="utf-8")
        receipt = self._build(
            _bindings(self.project, with_profile_graph=True)
        )
        self.assertEqual(
            receipt.status,
            "SOURCE_BINDINGS_READY_VE_BINDING_REQUIRED",
        )
        payload = json.loads(
            receipt.generator_input_path.read_text(encoding="utf-8")
        )
        evidence = payload["runtime_contract"][
            "qualification_evidence"
        ]
        self.assertEqual(
            evidence["native_profiles"]["status"],
            "INVALID_REPORT",
        )

    def test_conflicting_iso_and_supplied_specification_geometry_fails(self):
        with self.assertRaisesRegex(ConfigurationError, "source conflict"):
            self._build(_bindings(self.project, width=7.0))

    def test_missing_project_manifest_fails_before_binding(self):
        (self.project / "sia4010_external_inputs.json").unlink()
        with self.assertRaisesRegex(
            ConfigurationError, "requires project external-input manifest"
        ):
            build_test2a_source_bound_bundle(self.project, ROOT)


if __name__ == "__main__":
    unittest.main()
