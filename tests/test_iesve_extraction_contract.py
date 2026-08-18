"""Mocked contract tests for documented IESVE extraction behavior."""

from types import SimpleNamespace
import sys
import unittest
from unittest.mock import Mock, patch

from swiss_sia.data_extractor import VEDataExtractor
from swiss_sia.model_analyzer import ModelAnalyzer, RoomData


class FakeProfile:
    """Small VEProfile stand-in with explicit documented profile predicates."""

    def __init__(self, profile_id, data, kind="daily", modulating=True):
        self.id = profile_id
        self._data = data
        self._kind = kind
        self._modulating = modulating

    def get_data(self):
        """Return the profile payload exposed by VEProfile.get_data()."""
        if isinstance(self._data, Exception):
            raise self._data
        return self._data

    def is_modulating(self):
        """Report whether values are relative rather than absolute."""
        return self._modulating

    def is_weekly(self):
        """Report whether the payload contains daily profile IDs."""
        return self._kind == "weekly"

    def is_yearly(self):
        """Report whether the payload contains weekly profile periods."""
        return self._kind == "yearly"

    def is_compact(self):
        """Report the unsupported compact group form."""
        return self._kind == "compact"

    def is_freeform(self):
        """Report the unsupported free-form group form."""
        return self._kind == "freeform"


class FakeApacheSystem:
    """Minimal project-level VEApacheSystem object."""

    def __init__(self, system_id, name):
        self.id = system_id
        self.name = name

    @staticmethod
    def heating():
        """Return representative documented heating data."""
        return {"fuel": "heat-pump"}

    @staticmethod
    def cooling():
        """Return representative documented cooling data."""
        return {"seer": 4.2}


class IESVEExtractionContractTests(unittest.TestCase):
    """Pin the extraction contract without importing the proprietary API."""

    @staticmethod
    def make_extractor(**project_attributes):
        """Build an extractor around a truthy project stand-in."""
        return VEDataExtractor(SimpleNamespace(**project_attributes))

    def make_profile_extractor(self):
        """Build daily, weekly, yearly, and unsupported profile fixtures."""
        daily_profiles = {
            "daily-long-key": FakeProfile(
                "daily-long",
                [(0, 0, ""), (8, 0, ""), (10, 1, ""),
                 (18, 1, ""), (20, 0, ""), (24, 0, "")],
            ),
            "daily-short": FakeProfile(
                "daily-short",
                [(0, 0, ""), (8, 0, ""), (9, 1, ""),
                 (12, 1, ""), (13, 0, ""), (24, 0, "")],
            ),
            "daily-ve-marker": FakeProfile(
                "daily-ve-marker",
                [(0, 0, "-"), (8, 0, "-"), (9, 1, "-"),
                 (17, 1, "-"), (18, 0, "-"), (24, 0, "-")],
            ),
            "formula": FakeProfile("formula", [(0, 0, "weekday formula")]),
            "absolute": FakeProfile(
                "absolute", [(0, 18, ""), (24, 18, "")], modulating=False
            ),
            "broken": FakeProfile("broken", RuntimeError("profile unavailable")),
        }
        group_profiles = {
            "weekly": FakeProfile(
                "weekly",
                ["daily-short", "missing-child", "compact", "daily-long"],
                kind="weekly",
            ),
            "yearly": FakeProfile(
                "yearly",
                [["missing-week", 1, 31], ["weekly", 32, 365]],
                kind="yearly",
            ),
            "compact": FakeProfile("compact", [[[1, 1]]], kind="compact"),
            "freeform": FakeProfile("freeform", [], kind="freeform"),
            "recursive": FakeProfile("recursive", ["recursive"], kind="weekly"),
        }
        profiles = Mock(return_value=(daily_profiles, group_profiles))
        return self.make_extractor(profiles=profiles), profiles

    def test_model_with_most_relevant_room_bodies_is_selected(self):
        first_body = SimpleNamespace(type="BodyType.room", subtype="room")
        second_bodies = [
            SimpleNamespace(type="BodyType.room", subtype="room"),
            SimpleNamespace(type="BodyType.room", subtype="room"),
        ]
        first_model = SimpleNamespace(
            model_type="RealBuilding",
            get_bodies=Mock(return_value=[first_body]),
        )
        larger_model = SimpleNamespace(
            model_type="Secondary",
            get_bodies=Mock(return_value=second_bodies),
        )
        project = SimpleNamespace(models=[first_model, larger_model])
        extractor = VEDataExtractor(project)

        self.assertIs(extractor.model, larger_model)
        self.assertIs(extractor.model, larger_model)
        diagnostics = extractor.get_model_selection_diagnostics()
        self.assertEqual(diagnostics["selected_model_index"], 1)
        self.assertEqual(diagnostics["model_count"], 2)
        self.assertIn("maximum relevant room-body count", diagnostics["selection_basis"])
        first_model.get_bodies.assert_called_once_with(False)
        larger_model.get_bodies.assert_called_once_with(False)

    def test_profile_groups_use_maximum_supported_daily_equivalent_hours(self):
        extractor, profiles = self.make_profile_extractor()

        self.assertAlmostEqual(
            extractor.get_profile_daily_equivalent_hours("daily-long"), 10.0
        )
        self.assertAlmostEqual(
            extractor.get_profile_daily_equivalent_hours("daily-short"), 4.0
        )
        self.assertAlmostEqual(
            extractor.get_profile_daily_equivalent_hours("daily-ve-marker"), 9.0
        )
        self.assertAlmostEqual(
            extractor.get_profile_daily_equivalent_hours("weekly"), 10.0
        )
        self.assertAlmostEqual(
            extractor.get_profile_daily_equivalent_hours("yearly"), 10.0
        )
        profiles.assert_called_once_with()

    def test_missing_and_unsupported_profiles_are_not_approximated(self):
        extractor, _ = self.make_profile_extractor()

        unsupported_ids = (
            None,
            "",
            "missing",
            "formula",
            "absolute",
            "compact",
            "freeform",
            "recursive",
            "broken",
        )
        for profile_id in unsupported_ids:
            with self.subTest(profile_id=profile_id):
                self.assertIsNone(
                    extractor.get_profile_daily_equivalent_hours(profile_id)
                )

    def test_undocumented_on_profile_is_not_converted_to_24_hours(self):
        """An undocumented special profile identifier must remain fail-closed."""
        extractor, profiles = self.make_profile_extractor()

        audit = extractor.get_profile_daily_equivalent_hours_audit("ON")

        self.assertIsNone(audit["value"])
        self.assertEqual(audit["status"], "NOT_CHECKABLE")
        self.assertNotEqual(audit["value"], 0)
        profiles.assert_called_once_with()

    def test_documented_cdb_glazing_members_are_extracted_with_evidence(self):
        """Use only fields documented on VECdbConstruction.get_properties()."""
        construction = SimpleNamespace(
            get_properties=Mock(return_value={
                "visible_light_transmittance": 0.72,
                "frame_percent": 30.0,
                "g_total": 0.41,
            })
        )

        audits = VEDataExtractor._documented_cdb_glazing_audits(construction)

        self.assertEqual(audits["tau_v_audit"]["status"], "OK")
        self.assertAlmostEqual(audits["tau_v_audit"]["value"], 0.72)
        self.assertEqual(audits["frame_fraction_audit"]["status"], "OK")
        self.assertAlmostEqual(audits["frame_fraction_audit"]["value"], 0.30)
        self.assertEqual(audits["g_total_audit"]["status"], "NOT_CHECKABLE")
        self.assertIsNone(audits["g_total_audit"]["value"])
        self.assertNotEqual(audits["g_total_audit"]["value"], 0)

    def test_missing_cdb_member_returns_named_not_checkable_placeholders(self):
        """A double without the documented member must never produce zero."""
        audits = VEDataExtractor._documented_cdb_glazing_audits(SimpleNamespace())

        for name in ("tau_v_audit", "frame_fraction_audit", "g_total_audit"):
            with self.subTest(name=name):
                self.assertEqual(audits[name]["status"], "NOT_CHECKABLE")
                self.assertIsNone(audits[name]["value"])
                self.assertNotEqual(audits[name]["value"], 0)
                self.assertTrue(audits[name]["placeholder"])
                self.assertIn("[TO VERIFY] membre VE absent", audits[name]["note"])

    def test_daily_internal_gains_use_documented_gain_and_profile_members(self):
        """Integrate a gain only when gain, profile and diversity read-back exist."""
        gain = SimpleNamespace(get=Mock(return_value={
            "name": "Lighting",
            "type_str": "Fluorescent Lighting",
            "units_val": 0,
            "max_sensible_gains": {0: 10.0},
            "variation_profile": "DAY-1",
            "diversity_factor": 1.0,
        }))
        extractor = SimpleNamespace(
            get_internal_gains_audit=lambda room: {
                "items": [gain], "status": "OK", "placeholder": "", "note": ""
            },
            get_profile_daily_equivalent_hours_audit=lambda profile_id: {
                "value": 8.0,
                "status": "OK",
                "placeholder": "",
                "note": "",
            },
        )

        result = ModelAnalyzer(extractor)._analyze_internal_gains(object(), 50.0)

        self.assertEqual(result["daily_status"], "OK")
        self.assertAlmostEqual(result["daily_wh_m2"], 80.0)
        self.assertEqual(result["daily_placeholder"], "")

    def test_missing_daily_gain_member_is_not_checkable_and_never_zero(self):
        """A room double without get_internal_gains is not evidence of zero gain."""
        extractor = self.make_extractor()
        analyzer = ModelAnalyzer(extractor)

        result = analyzer._analyze_internal_gains(SimpleNamespace(), 50.0)

        self.assertEqual(result["daily_status"], "NOT_CHECKABLE")
        self.assertIsNone(result["daily_wh_m2"])
        self.assertNotEqual(result["daily_wh_m2"], 0)
        self.assertIn("[TO VERIFY] membre VE absent", result["daily_method"])

    def test_ventilation_sia_classifications_are_not_inferred_from_labels(self):
        """System labels and zone counts are context, not direct SIA members."""
        extractor = SimpleNamespace(
            get_room_zone_membership=lambda: {"R1": {"zone_room_count": 3}}
        )
        room = RoomData(
            id="R1",
            hvac_systems=[{"system_type": "MULTIZONE", "fan_control": "gas_sensor variable"}],
            fan_control="gas_sensor variable",
        )

        ModelAnalyzer(extractor)._annotate_hvac_zoning_and_controls([room])

        self.assertIsNone(room.ventilation_installation_type)
        self.assertEqual(room.ventilation_installation_type_status, "NOT_CHECKABLE")
        self.assertIsNone(room.ventilation_control_level)
        self.assertEqual(room.ventilation_control_level_status, "NOT_CHECKABLE")
        self.assertTrue(room.ventilation_installation_type_placeholder)
        self.assertTrue(room.ventilation_control_level_placeholder)

    def test_project_apache_systems_list_is_indexed_by_documented_ids(self):
        primary = FakeApacheSystem("SYS-01", "Primary")
        secondary = FakeApacheSystem("SYS-02", "Secondary")
        apache_systems = Mock(return_value=[primary, secondary])
        extractor = self.make_extractor(apache_systems=apache_systems)

        systems = extractor.get_hvac_systems()

        self.assertEqual(list(systems), ["SYS-01", "SYS-02"])
        self.assertIs(systems["SYS-01"], primary)
        self.assertIs(systems["SYS-02"], secondary)
        self.assertEqual(
            extractor.get_apache_system_data("sys-01")["heating"],
            {"fuel": "heat-pump"},
        )
        self.assertEqual(
            extractor.get_apache_system_data("Primary")["cooling"],
            {"seer": 4.2},
        )
        apache_systems.assert_called_once_with()

    def test_surface_construction_selection_prefers_matching_parent_category(self):
        """Do not use a door construction as the U-value of its parent wall."""
        extractor = self.make_extractor()
        construction_data = {
            "DOOR": {"id": "DOOR", "opaque": True, "category": "door", "u_value": 0.63},
            "EXTW": {"id": "EXTW", "opaque": False, "category": "ext_glazing", "u_value": 1.1},
            "WALL": {"id": "WALL", "opaque": True, "category": "wall", "u_value": 0.20},
        }
        extractor.get_construction_properties = lambda identifier: construction_data[str(identifier)]

        selected = extractor._select_surface_construction_properties(
            ["DOOR", "EXTW", "WALL"],
            "ext_wall",
            {"external_net": 20.0},
        )

        self.assertEqual(selected["id"], "WALL")

    def test_roomgroups_maps_hvac_zone_metadata_to_each_room_id(self):
        room_groups = Mock()
        room_groups.get_zone_groups.return_value = [
            {"id": "GROUP-1", "name": "HVAC zoning"},
            {"id": "", "name": "ignored"},
        ]
        room_groups.get_zones.return_value = [
            {
                "id": "ZONE-1",
                "name": "North zone",
                "rooms": ["ROOM-1", 2],
                "master_room": "ROOM-1",
            }
        ]
        iesve_module = SimpleNamespace(RoomGroups=Mock(return_value=room_groups))
        extractor = self.make_extractor()

        with patch.dict(sys.modules, {"iesve": iesve_module}):
            membership = extractor.get_room_zone_membership()
            cached_membership = extractor.get_room_zone_membership()

        expected = {
            "zone_group_id": "GROUP-1",
            "zone_group_name": "HVAC zoning",
            "zone_id": "ZONE-1",
            "zone_name": "North zone",
            "zone_room_count": 2,
            "master_room": "ROOM-1",
        }
        self.assertEqual(membership["ROOM-1"], expected)
        self.assertEqual(membership["2"], expected)
        self.assertEqual(cached_membership, membership)
        iesve_module.RoomGroups.assert_called_once_with()
        room_groups.get_zones.assert_called_once_with("GROUP-1")

    def test_macroflo_definitions_and_opening_assignments_preserve_ids(self):
        macroflo = Mock()
        macroflo.get.return_value = [
            {"reference_id": " MF-01 ", "description": "Operable window"},
            {"reference_id": "MF-02", "description": "Door"},
            {"reference_id": "", "description": "No ID"},
            ("not", "a mapping"),
        ]
        iesve_module = SimpleNamespace(VEMacroFlo=Mock(return_value=macroflo))
        extractor = self.make_extractor()

        with patch.dict(sys.modules, {"iesve": iesve_module}):
            definitions = extractor.get_macroflo_openings()
            self.assertEqual(extractor.get_macroflo_openings(), definitions)

        self.assertEqual(set(definitions), {"MF-01", "MF-02"})
        self.assertEqual(definitions["MF-01"]["description"], "Operable window")
        iesve_module.VEMacroFlo.assert_called_once_with()
        macroflo.get.assert_called_once_with()

        opening = SimpleNamespace(
            get_properties=Mock(return_value={"area": 2.5, "type": "window"}),
            get_construction=Mock(return_value=""),
            get_macroflo_id=Mock(return_value="MF-01"),
        )
        self.assertEqual(
            extractor.get_opening_properties(opening)["macroflo_id"], "MF-01"
        )
        opening.get_macroflo_id.assert_called_once_with()

    def test_optional_roomgroups_and_macroflo_apis_fail_closed(self):
        iesve_module = SimpleNamespace(
            RoomGroups=Mock(side_effect=RuntimeError("RoomGroups unavailable")),
            VEMacroFlo=Mock(side_effect=RuntimeError("MacroFlo unavailable")),
        )
        extractor = self.make_extractor()

        with patch.dict(sys.modules, {"iesve": iesve_module}):
            self.assertEqual(extractor.get_room_zone_membership(), {})
            self.assertEqual(extractor.get_macroflo_openings(), {})

    def test_zero_shade_activation_is_extracted_as_explicitly_disabled(self):
        """Do not turn zero-valued CDB shade fields into active evidence."""
        properties = {
            "external_shade_active": 0,
            "internal_shade_active": 0,
            "local_shade_active": 0,
            "external_shade_code": 0,
            "external_shade_radiation_to_raise": 250,
        }

        self.assertEqual(
            VEDataExtractor._extract_shading_type(properties),
            "none declared in CDB",
        )
        self.assertEqual(
            VEDataExtractor._extract_shading_control(properties),
            "none declared in CDB",
        )

    def test_weather_metadata_uses_documented_velocate_and_closes(self):
        """Read weather metadata through VELocate and always close its data handle."""
        locator = Mock()
        locator.open_wea_data.return_value = 0
        locator.get.return_value = {"weather_file": "current.fwt"}
        iesve_module = SimpleNamespace(VELocate=Mock(return_value=locator))
        extractor = self.make_extractor()

        with patch.dict(sys.modules, {"iesve": iesve_module}):
            result = extractor.get_weather_data()

        self.assertEqual(result["weather_file"], "current.fwt")
        locator.open_wea_data.assert_called_once_with()
        locator.get.assert_called_once_with()
        locator.close_wea_data.assert_called_once_with()

    def test_results_reader_is_closed_when_dynamic_extraction_raises(self):
        from swiss_sia import app

        results_file = Mock()
        simulation_results = Mock()
        simulation_results.list_aps_files.return_value = ["results.aps"]
        simulation_results.get_aps_path.return_value = "project/Vista/results.aps"
        simulation_results.extract_epw_references_from_aps.return_value = []
        simulation_results.open_results_reader.return_value = results_file
        simulation_results.collect_room_dynamic_results.side_effect = RuntimeError(
            "mock extraction failure"
        )

        with patch.object(app, "simulation_results_module", simulation_results), patch.object(
            app, "_current_project_weather_label", return_value=""
        ), patch.object(app, "_select_latest_aps_file", return_value="results.aps"):
            summary = app._collect_dynamic_results(SimpleNamespace())

        results_file.close.assert_called_once_with()
        self.assertEqual(summary["status"], "NOT_CHECKABLE")
        self.assertIn("mock extraction failure", summary["notes"])

    def test_results_reader_weather_accepts_aps_when_binary_scan_is_empty(self):
        """Use the documented reader weather attribute as the authoritative source."""
        from swiss_sia import app

        results_file = Mock(weather_file="current.fwt")
        simulation_results = Mock()
        simulation_results.list_aps_files.return_value = ["results.aps"]
        simulation_results.get_aps_path.return_value = "project/Vista/results.aps"
        simulation_results.extract_epw_references_from_aps.return_value = []
        simulation_results.open_results_reader.return_value = results_file
        simulation_results.collect_room_dynamic_results.return_value = []

        with (
            patch.object(app, "simulation_results_module", simulation_results),
            patch.object(app, "_current_project_weather_label", return_value="current.fwt"),
            patch.object(app, "_rank_aps_files_by_mtime", return_value=["results.aps"]),
        ):
            summary = app._collect_dynamic_results(SimpleNamespace())

        self.assertEqual(summary["selected_aps_file"], "results.aps")
        self.assertEqual(summary["selected_aps_weather_references"], ["current.fwt"])
        simulation_results.collect_room_dynamic_results.assert_called_once_with(results_file)
        results_file.close.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
