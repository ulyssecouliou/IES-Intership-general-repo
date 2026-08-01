"""Source-bound Test 3 bundle tests with no IESVE dependency."""

import hashlib
import json
import shutil
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from swiss_sia.reference_model.sia4010.test3_source_bundle import (
    AUTHORITY_MAPPING_BLOCKER,
    MISSING_NATIVE_PROFILE_GRAPH_BLOCKER,
    RUNTIME_BLOCKERS,
    build_test3_source_bound_bundle,
)


ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT / ".codex_tmp" / "test3_source_bundle"


class _Record:
    def __init__(self, identifier):
        self.identifier = identifier

    def to_dict(self):
        return {"id": self.identifier}


class _Controls:
    def control(self, identifier):
        if identifier == "shade_type_4":
            raise KeyError(identifier)
        return _Record(identifier)

    def to_dict(self):
        return {"validated_control_set": True}


def _bindings(*, with_graph=True, authority=None):
    iso = SimpleNamespace(
        width_m=8.0,
        depth_m=6.0,
        height_m=2.7,
        window_count=2,
        window_width_m=3.0,
        window_height_m=2.0,
        window_sill_m=0.2,
        window_side_margin_m=0.5,
        window_gap_m=1.0,
        to_dict=lambda: {"width_m": 8.0, "depth_m": 6.0},
    )
    profiles = SimpleNamespace(
        ve_profile_graph=object() if with_graph else None,
        to_dict=lambda: {"native_ve_materialization_ready": with_graph},
    )
    common = SimpleNamespace(
        iso_cell=iso,
        weather=SimpleNamespace(to_dict=lambda: {"hour_count": 8760}),
        office_profiles=profiles,
    )
    return SimpleNamespace(
        common=common,
        controls=_Controls(),
        shading_device=SimpleNamespace(
            to_dict=lambda: {"device_id": "controlled_awning"}
        ),
        authority_decision=authority,
        evidence_sha256=(("controlled", "a" * 64),),
    )


class Test3SourceBundleTests(unittest.TestCase):
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
        self.geometry = self.project / "prepared.gbxml"
        self.geometry.write_text("<gbXML />\n", encoding="utf-8")
        self.preparation_audit = self.project / "preparation.json"
        self.preparation_audit.write_text("{}\n", encoding="utf-8")

    def tearDown(self):
        if self.project.exists():
            shutil.rmtree(self.project)

    def _build(self, case_id, bindings):
        readiness = mock.Mock(ready_for_binding=True)
        readiness.to_dict.return_value = {
            "status": "READY_FOR_BINDING",
            "ready_for_binding": True,
        }
        preparation = SimpleNamespace(
            geometry_artifact_path=self.geometry,
            audit_path=self.preparation_audit,
        )
        with mock.patch(
            "swiss_sia.reference_model.sia4010.test3_source_bundle."
            "Sia4010ExternalInputManifest.load",
            return_value=mock.Mock(),
        ), mock.patch(
            "swiss_sia.reference_model.sia4010.test3_source_bundle."
            "external_input_readiness",
            return_value=readiness,
        ), mock.patch(
            "swiss_sia.reference_model.sia4010.test3_source_bundle."
            "load_test3_external_bindings",
            return_value=bindings,
        ), mock.patch(
            "swiss_sia.reference_model.sia4010.test3_source_bundle.prepare_case",
            return_value=preparation,
        ):
            return build_test3_source_bound_bundle(
                self.project,
                ROOT,
                "2B",
                "test_{}".format(case_id),
                case_id,
            )

    def test_3a_bundle_binds_official_pair_and_both_acceptance_criteria(self):
        receipt = self._build("3A", _bindings())
        self.assertEqual(
            receipt.status, "SOURCE_BOUND_RUNTIME_QUALIFICATION_REQUIRED"
        )
        self.assertFalse(receipt.mutation_supported)
        self.assertEqual(receipt.runtime_blockers, RUNTIME_BLOCKERS)
        payload = json.loads(
            receipt.generator_input_path.read_text(encoding="utf-8")
        )
        pair = payload["selected_control_pair"]
        self.assertEqual(pair["shade_control_id"], "shade_type_1")
        self.assertEqual(pair["lighting_control_id"], "lighting_type_1")
        self.assertEqual(
            payload["official_evaluation_contract"][
                "annual_reference_band"
            ]["unit"],
            "kWh",
        )
        self.assertEqual(
            payload["official_evaluation_contract"][
                "hourly_distribution"
            ]["quantities"][0]["header_label"],
            "Beleuchtungsleistung",
        )
        runtime = payload["runtime_contract"]
        self.assertFalse(runtime["mutation_supported"])
        self.assertFalse(runtime["mutation_performed"])
        self.assertFalse(runtime["simulation_performed"])
        self.assertFalse(runtime["compliance_claim_allowed"])

    def test_missing_native_profile_graph_is_preserved_as_blocker(self):
        receipt = self._build("3A", _bindings(with_graph=False))
        self.assertEqual(receipt.status, "SOURCE_BOUND_PROFILE_GRAPH_REQUIRED")
        self.assertIn(
            MISSING_NATIVE_PROFILE_GRAPH_BLOCKER,
            receipt.runtime_blockers,
        )

    def test_3k_keeps_authority_mapping_fail_closed(self):
        decision = SimpleNamespace(
            to_dict=lambda: {
                "decision_id": "controlled_3k_3l_decision"
            }
        )
        receipt = self._build(
            "3K", _bindings(authority=decision)
        )
        self.assertIn(AUTHORITY_MAPPING_BLOCKER, receipt.runtime_blockers)
        payload = json.loads(
            receipt.generator_input_path.read_text(encoding="utf-8")
        )
        self.assertIsNone(
            payload["selected_control_pair"]["shading_control"]
        )
        self.assertEqual(
            payload["selected_control_pair"]["authority_decision"][
                "decision_id"
            ],
            "controlled_3k_3l_decision",
        )

    def test_generator_input_is_deterministic(self):
        first = self._build("3A", _bindings())
        first_bytes = first.generator_input_path.read_bytes()
        second = self._build("3A", _bindings())
        self.assertEqual(first_bytes, second.generator_input_path.read_bytes())
        self.assertEqual(
            first.generator_input_sha256,
            second.generator_input_sha256,
        )


if __name__ == "__main__":
    unittest.main()
