"""Semantic validation tests for normalized Test 2A external inputs."""

import hashlib
import json
import shutil
import unittest
from pathlib import Path

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.external_input_manifest import (
    EXTERNAL_INPUT_BINDING_SCHEMAS,
    EXTERNAL_INPUT_FILENAME,
    Sia4010ExternalInputManifest,
    external_input_readiness,
)
from swiss_sia.reference_model.sia4010.normalized_external_inputs import (
    TEST2A_EXTERNAL_INPUT_IDS,
    load_test2a_external_bindings,
)


ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT / ".codex_tmp" / "normalized_external_inputs"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _layer(material_id):
    return {
        "material_id": material_id,
        "thickness_m": 0.1,
        "conductivity_w_mk": 0.1,
        "density_kg_m3": 100.0,
        "specific_heat_j_kgk": 1000.0,
    }


def _construction(construction_id, material_id):
    return {
        "construction_id": construction_id,
        "layers_outside_to_inside": [_layer(material_id)],
        "surface_properties": {
            "inside_ir_emissivity": 0.9,
            "outside_ir_emissivity": 0.9,
            "inside_solar_absorptance": 0.6,
            "outside_solar_absorptance": 0.6,
        },
    }


class NormalizedExternalInputTests(unittest.TestCase):
    """Only fully linked and semantically coherent inputs reach a generator."""

    def setUp(self):
        self.project = WORK_ROOT / self._testMethodName
        if self.project.exists():
            shutil.rmtree(self.project)
        self.project.mkdir(parents=True)

    def tearDown(self):
        if self.project.exists():
            shutil.rmtree(self.project)

    def _iso_payload(self):
        return {
            "schema_id": EXTERNAL_INPUT_BINDING_SCHEMAS[
                "iso52016_2017_chapter7_test_cell"
            ],
            "schema_version": "1.0",
            "primary_source_sha256": "",
            "source_locator": "controlled source chapter and table",
            "cell": {
                "width_m": 8.0,
                "depth_m": 6.0,
                "height_m": 2.7,
                "south_windows": {
                    "count": 2,
                    "width_m": 3.0,
                    "height_m": 2.0,
                    "sill_m": 0.2,
                    "side_margin_m": 0.5,
                    "gap_m": 1.0,
                },
            },
            "surface_coefficients_w_m2k": {
                "inside": 8.0,
                "outside": 25.0,
            },
            "lightweight_opaque_constructions": {
                "external_wall": _construction("wall", "wall_layer"),
                "roof": _construction("roof", "roof_layer"),
                "floor": _construction("floor", "floor_layer"),
            },
        }

    def _weather_payload(self, weather_name):
        return {
            "schema_id": EXTERNAL_INPUT_BINDING_SCHEMAS[
                "sia2028_dry_normal_zurich_kloten"
            ],
            "schema_version": "1.0",
            "primary_source_sha256": "",
            "source_locator": "authorized dataset release",
            "station_name": "controlled station identity",
            "dataset_identity": "controlled dataset identity",
            "weather_file": {
                "path": weather_name,
                "sha256": "",
                "format": "EPW",
                "hour_count": 8760,
            },
        }

    def _profiles_payload(self):
        profiles = []
        for key in (
            "occupancy_profile",
            "equipment_profile",
            "lighting_profile",
        ):
            profiles.append(
                {
                    "key": key,
                    "profile_type": "daily",
                    "reference": key.upper(),
                    "modulating": True,
                    "units": -1,
                    "data": [[0.0, 0.0, ""], [24.0, 0.0, ""]],
                    "source_locator": "controlled schedule row",
                }
            )
        return {
            "schema_id": EXTERNAL_INPUT_BINDING_SCHEMAS[
                "sia2024_office_3_1_standard_profiles"
            ],
            "schema_version": "1.0",
            "primary_source_sha256": "",
            "source_locator": "controlled use-category table",
            "use_category": "controlled category identity",
            "value_set": "controlled value-set identity",
            "calendar_basis": "documented annual calendar",
            "annual_simultaneity_method": "documented source method",
            "profiles": profiles,
        }

    def _ve_profile_graph(self):
        nodes = []
        outputs = {}
        for role in (
            "occupancy_profile",
            "equipment_profile",
            "lighting_profile",
        ):
            prefix = role.replace("_profile", "")
            daily = prefix + "_daily"
            weekly = prefix + "_weekly"
            yearly = prefix + "_yearly"
            nodes.extend(
                [
                    {
                        "key": daily,
                        "profile_type": "daily",
                        "reference": daily.upper(),
                        "modulating": True,
                        "units": -1,
                        "data": [[0.0, 0.0, ""], [24.0, 0.0, ""]],
                        "source_locator": "controlled daily rows",
                    },
                    {
                        "key": weekly,
                        "profile_type": "weekly",
                        "reference": weekly.upper(),
                        "modulating": True,
                        "units": -1,
                        "data": [{"profile_ref": daily}] * 12,
                        "source_locator": "controlled weekday mapping",
                    },
                    {
                        "key": yearly,
                        "profile_type": "yearly",
                        "reference": yearly.upper(),
                        "modulating": True,
                        "units": -1,
                        "data": [[{"profile_ref": weekly}, 1, 365]],
                        "source_locator": "controlled annual mapping",
                    },
                ]
            )
            outputs[role] = yearly
        return {
            "nodes": nodes,
            "outputs": outputs,
            "source_locator": "controlled VE calendar transcription",
        }

    def _write_fixture(
        self,
        *,
        mutate_iso=None,
        weather_hours=8760,
        mutate_profiles=None,
    ):
        weather_file = self.project / "authorized.epw"
        weather_file.write_text(
            "\n".join(
                ["HEADER"] * 8 + ["2021,1,1,1"] * weather_hours
            )
            + "\n",
            encoding="utf-8",
        )
        bindings = {
            "iso52016_2017_chapter7_test_cell": self._iso_payload(),
            "sia2028_dry_normal_zurich_kloten": self._weather_payload(
                weather_file.name
            ),
            "sia2024_office_3_1_standard_profiles": (
                self._profiles_payload()
            ),
        }
        if mutate_iso is not None:
            mutate_iso(bindings["iso52016_2017_chapter7_test_cell"])
        if mutate_profiles is not None:
            mutate_profiles(
                bindings["sia2024_office_3_1_standard_profiles"]
            )
        bindings["sia2028_dry_normal_zurich_kloten"]["weather_file"][
            "sha256"
        ] = _sha256(weather_file)

        manifest_inputs = {}
        for input_id in TEST2A_EXTERNAL_INPUT_IDS:
            source = self.project / "{}_source.txt".format(input_id)
            source.write_text(
                "controlled primary source for {}\n".format(input_id),
                encoding="utf-8",
            )
            source_sha = _sha256(source)
            binding_payload = bindings[input_id]
            binding_payload["primary_source_sha256"] = source_sha
            binding = self.project / "{}_binding.json".format(input_id)
            binding.write_text(
                json.dumps(binding_payload, indent=2) + "\n",
                encoding="utf-8",
            )
            report = self.project / "{}_validation.json".format(input_id)
            report.write_text(
                json.dumps(
                    {
                        "schema_version": "1.0",
                        "input_id": input_id,
                        "source_sha256": source_sha,
                        "status": "PASS",
                        "validated_by": "controlled independent reviewer",
                        "validation_method": "schema and source comparison",
                        "binding_artifact": {
                            "path": binding.name,
                            "sha256": _sha256(binding),
                            "schema_id": EXTERNAL_INPUT_BINDING_SCHEMAS[
                                input_id
                            ],
                        },
                        "checks": [
                            {
                                "id": "SOURCE-TRANSCRIPTION",
                                "status": "PASS",
                                "detail": "fixture transcription checked",
                            }
                        ],
                    },
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            manifest_inputs[input_id] = {
                "source_path": source.name,
                "source_sha256": source_sha,
                "provenance_status": "SIA_SUPPLIED",
                "normative_authorization_status": "CONFIRMED",
                "source_authority": "SIA",
                "license_reference": "controlled test authorization",
                "dataset_identity": input_id,
                "machine_readable_format": "normalized JSON",
                "semantic_scope": ["complete Test 2A delegated input"],
                "technical_validation": {
                    "status": "PASS",
                    "report_path": report.name,
                    "report_sha256": _sha256(report),
                },
            }
        manifest_path = self.project / EXTERNAL_INPUT_FILENAME
        manifest_path.write_text(
            json.dumps(
                {"schema_version": "1.0", "inputs": manifest_inputs},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        manifest = Sia4010ExternalInputManifest.load(manifest_path)
        return external_input_readiness(
            self.project,
            "test_2A",
            "2A",
            manifest=manifest,
        )

    def test_complete_test2a_bindings_load_without_fallback(self):
        bindings = load_test2a_external_bindings(self._write_fixture())
        self.assertEqual(bindings.iso_cell.window_count, 2)
        self.assertEqual(bindings.weather.hour_count, 8760)
        self.assertEqual(
            tuple(item.key for item in bindings.office_profiles.profiles),
            (
                "occupancy_profile",
                "equipment_profile",
                "lighting_profile",
            ),
        )
        self.assertEqual(len(bindings.evidence_sha256), 3)
        self.assertFalse(
            bindings.office_profiles.native_ve_materialization_ready
        )

    def test_explicit_native_ve_profile_graph_is_validated_and_exposed(self):
        readiness = self._write_fixture(
            mutate_profiles=lambda payload: payload.update(
                {"ve_profile_graph": self._ve_profile_graph()}
            )
        )
        profiles = load_test2a_external_bindings(readiness).office_profiles
        self.assertTrue(profiles.native_ve_materialization_ready)
        self.assertEqual(
            profiles.ve_profile_graph.required_profile_types,
            ("daily", "weekly", "yearly"),
        )
        self.assertEqual(
            profiles.ve_profile_graph.output_node_key("equipment_profile"),
            "equipment_yearly",
        )

    def test_native_ve_yearly_profile_rejects_8760_scalar_schedule(self):
        def inject_invalid_graph(payload):
            graph = self._ve_profile_graph()
            graph["nodes"][-1]["data"] = [0.0] * 8760
            payload["ve_profile_graph"] = graph

        readiness = self._write_fixture(mutate_profiles=inject_invalid_graph)
        with self.assertRaisesRegex(
            ConfigurationError,
            "must contain profile_ref, start_day and end_day",
        ):
            load_test2a_external_bindings(readiness)

    def test_native_ve_profile_graph_requires_complete_365_day_calendar(self):
        def inject_incomplete_graph(payload):
            graph = self._ve_profile_graph()
            graph["nodes"][-1]["data"] = [
                [{"profile_ref": "lighting_weekly"}, 1, 364]
            ]
            payload["ve_profile_graph"] = graph

        readiness = self._write_fixture(mutate_profiles=inject_incomplete_graph)
        with self.assertRaisesRegex(
            ConfigurationError, "cover days 1 through 365"
        ):
            load_test2a_external_bindings(readiness)

    def test_iso_geometry_must_close_exactly(self):
        readiness = self._write_fixture(
            mutate_iso=lambda payload: payload["cell"]["south_windows"].update(
                {"gap_m": 0.9}
            )
        )
        with self.assertRaisesRegex(
            ConfigurationError, "dimensions do not close"
        ):
            load_test2a_external_bindings(readiness)

    def test_weather_file_must_have_8760_epw_records(self):
        readiness = self._write_fixture(weather_hours=8759)
        with self.assertRaisesRegex(
            ConfigurationError, "contains 8759 hourly records"
        ):
            load_test2a_external_bindings(readiness)

    def test_office_profile_set_must_be_exact(self):
        def remove_lighting(payload):
            payload["profiles"] = [
                item
                for item in payload["profiles"]
                if item["key"] != "lighting_profile"
            ]

        readiness = self._write_fixture(mutate_profiles=remove_lighting)
        with self.assertRaisesRegex(
            ConfigurationError, "profile keys mismatch"
        ):
            load_test2a_external_bindings(readiness)

    def test_binding_change_after_evidence_validation_is_rejected(self):
        readiness = self._write_fixture()
        evidence = next(
            item
            for item in readiness.evidence
            if item.input_id == "iso52016_2017_chapter7_test_cell"
        )
        evidence.binding_artifact_path.write_text(
            '{"changed": true}\n', encoding="utf-8"
        )
        with self.assertRaisesRegex(
            ConfigurationError, "changed after evidence validation"
        ):
            load_test2a_external_bindings(readiness)

    def test_wrong_case_readiness_is_rejected(self):
        readiness = external_input_readiness(
            self.project, "test_1", "600"
        )
        with self.assertRaisesRegex(
            ConfigurationError, "test_2A/2A"
        ):
            load_test2a_external_bindings(readiness)

    def test_published_json_schema_ids_match_runtime_contract(self):
        schema_files = {
            "iso52016_2017_chapter7_test_cell": (
                "sia4010_iso_test_cell_binding.schema.json"
            ),
            "sia2028_dry_normal_zurich_kloten": (
                "sia4010_sia2028_weather_binding.schema.json"
            ),
            "sia2024_office_3_1_standard_profiles": (
                "sia4010_sia2024_usage_profiles_binding.schema.json"
            ),
        }
        for input_id, filename in schema_files.items():
            with self.subTest(input_id=input_id):
                payload = json.loads(
                    (ROOT / "schemas" / filename).read_text(encoding="utf-8")
                )
                self.assertEqual(
                    payload["$id"],
                    EXTERNAL_INPUT_BINDING_SCHEMAS[input_id],
                )


if __name__ == "__main__":
    unittest.main()
