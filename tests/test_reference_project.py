"""Tests for the SIA 380/2 reference-project input specification."""

import unittest

from swiss_sia.config import SIA3802_LIMIT_VALUES
from swiss_sia.model_analyzer import ModelAnalyzer, OpeningData, RoomData, SurfaceData
from swiss_sia.reference_project import (
    PROJECT_VALUE_MISSING,
    REFERENCE_DIRECTIVE,
    STANDARD_USAGE_INPUT,
    SUBSTITUTABLE,
    UNCLASSIFIED,
    build_reference_project_specification,
)


class _Analyzer:
    """Minimal analyzer exposing only the surface-type normalizer."""

    def __init__(self):
        """Reuse the production normalizer without touching the VE API."""
        self._normalize = ModelAnalyzer._normalize_surface_type

    def _normalize_surface_type(self, surface_type):
        """Normalize a surface type exactly as the production analyzer does."""
        return self._normalize(self, surface_type)


def _surface(**kwargs):
    """Build an external surface with defaults the specification reads."""
    payload = {
        "id": "s1",
        "name": "S1",
        "area": 10.0,
        "net_area": 10.0,
        "u_value": 0.25,
        "is_external": True,
        "surface_type": "wall",
        "construction_ids": ["STD_EXT1"],
    }
    payload.update(kwargs)
    return SurfaceData(**payload)


def _opening(**kwargs):
    """Build an external opening with defaults the specification reads.

    The solar factor carries a proven EN 410 source so the glazing g_perp is
    substitutable by default; tests that exercise the comparability gate
    override ``solar_factor_source`` explicitly.
    """
    payload = {
        "id": "w1",
        "name": "W1",
        "area": 2.0,
        "u_value": 1.4,
        "frame_fraction": 0.30,
        "solar_factor": 0.60,
        "solar_factor_source": "bs_en_410",
        "visible_transmittance": 0.65,
        "is_external": True,
        "opening_type": "window",
        "construction_id": "STD_GLZ",
    }
    payload.update(kwargs)
    return OpeningData(**payload)


def _room(surfaces=None, openings=None, **kwargs):
    """Build a room carrying the given surfaces and openings.

    A comparable infiltration value is set by default so envelope-only fixtures
    keep the whole-building infiltration substitutable; tests that exercise the
    infiltration path override ``infiltration_m3_h_m2``/``infiltration_rate``.
    """
    payload = {
        "id": "r1",
        "name": "Room 1",
        "surfaces": list(surfaces or []),
        "openings": list(openings or []),
        "infiltration_m3_h_m2": 0.10,
    }
    payload.update(kwargs)
    return RoomData(**payload)


def _by_parameter(spec, parameter):
    """Return the substitutions emitted for one parameter."""
    return [item for item in spec.substitutions if item.parameter == parameter]


class EmptyModelTests(unittest.TestCase):
    def test_no_rooms_is_not_checkable(self):
        spec = build_reference_project_specification([], _Analyzer())
        self.assertEqual(spec.status, "NOT_CHECKABLE")
        self.assertFalse(spec.is_complete)
        self.assertTrue(spec.blockers)


class SurfaceSubstitutionTests(unittest.TestCase):
    def test_external_wall_is_paired_with_the_encoded_reference_value(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface(u_value=0.25)])], _Analyzer()
        )
        walls = _by_parameter(spec, "external_wall_u")
        self.assertEqual(len(walls), 1)
        item = walls[0]
        self.assertEqual(item.status, SUBSTITUTABLE)
        self.assertEqual(item.project_value, 0.25)
        self.assertEqual(item.reference_value, SIA3802_LIMIT_VALUES["external_wall_u"])
        self.assertEqual(item.unit, "W/(m2K)")
        self.assertIn("SIA 380/2", item.source)

    def test_roof_and_floor_map_to_their_own_reference_keys(self):
        spec = build_reference_project_specification(
            [
                _room(
                    surfaces=[
                        _surface(id="r", surface_type="roof", construction_ids=["ROOF1"]),
                        _surface(id="f", surface_type="floor", construction_ids=["FLR1"]),
                    ]
                )
            ],
            _Analyzer(),
        )
        self.assertEqual(
            _by_parameter(spec, "flat_roof_u")[0].reference_value,
            SIA3802_LIMIT_VALUES["flat_roof_u"],
        )
        self.assertEqual(
            _by_parameter(spec, "ground_floor_u")[0].reference_value,
            SIA3802_LIMIT_VALUES["ground_floor_u"],
        )

    def test_surfaces_are_grouped_by_construction(self):
        spec = build_reference_project_specification(
            [
                _room(
                    surfaces=[
                        _surface(id="a", construction_ids=["STD_EXT1"]),
                        _surface(id="b", construction_ids=["STD_EXT1"]),
                        _surface(id="c", construction_ids=["STD_EXT2"]),
                    ]
                )
            ],
            _Analyzer(),
        )
        walls = {item.scope: item for item in _by_parameter(spec, "external_wall_u")}
        self.assertEqual(set(walls), {"STD_EXT1", "STD_EXT2"})
        self.assertEqual(walls["STD_EXT1"].affected_elements, 2)
        self.assertEqual(walls["STD_EXT2"].affected_elements, 1)

    def test_worst_value_is_reported_not_an_average(self):
        spec = build_reference_project_specification(
            [
                _room(
                    surfaces=[
                        _surface(id="a", u_value=0.20),
                        _surface(id="b", u_value=0.40),
                    ]
                )
            ],
            _Analyzer(),
        )
        self.assertEqual(_by_parameter(spec, "external_wall_u")[0].project_value, 0.40)

    def test_missing_project_value_blocks_rather_than_substituting(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface(u_value=None)])], _Analyzer()
        )
        item = _by_parameter(spec, "external_wall_u")[0]
        self.assertEqual(item.status, PROJECT_VALUE_MISSING)
        self.assertIsNone(item.project_value)
        self.assertEqual(spec.status, "BLOCKED_INCOMPLETE_INPUTS")
        self.assertFalse(spec.is_complete)

    def test_unclassified_surface_is_reported_not_guessed(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface(surface_type="hole", construction_ids=["ODD"])])],
            _Analyzer(),
        )
        items = _by_parameter(spec, "unclassified_external_surface")
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].status, UNCLASSIFIED)
        self.assertIsNone(items[0].reference_value)
        self.assertEqual(spec.status, "BLOCKED_INCOMPLETE_INPUTS")

    def test_internal_surfaces_are_ignored(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface(is_external=False)])], _Analyzer()
        )
        self.assertEqual(_by_parameter(spec, "external_wall_u"), [])

    def test_zero_area_surface_is_ignored(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface(net_area=0.0)])], _Analyzer()
        )
        self.assertEqual(_by_parameter(spec, "external_wall_u"), [])

    def test_floating_point_surface_residue_is_ignored(self):
        spec = build_reference_project_specification(
            [
                _room(
                    surfaces=[
                        _surface(
                            surface_type="partition",
                            area=7.8e-14,
                            net_area=7.8e-14,
                        )
                    ]
                )
            ],
            _Analyzer(),
        )
        self.assertEqual(_by_parameter(spec, "unclassified_external_surface"), [])


class OpeningSubstitutionTests(unittest.TestCase):
    def test_window_u_and_frame_fraction_are_paired_with_table_2(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()], openings=[_opening()])], _Analyzer()
        )
        window = _by_parameter(spec, "window_u")[0]
        frame = _by_parameter(spec, "window_frame_fraction")[0]
        self.assertEqual(window.project_value, 1.4)
        self.assertEqual(window.reference_value, SIA3802_LIMIT_VALUES["window_u"])
        self.assertEqual(frame.project_value, 0.30)
        self.assertEqual(
            frame.reference_value, SIA3802_LIMIT_VALUES["window_frame_fraction"]
        )

    def test_glazing_g_perp_and_transmittance_are_paired_with_table_2(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()], openings=[_opening()])], _Analyzer()
        )
        g_perp = _by_parameter(spec, "glazing_g_value")[0]
        tau_v = _by_parameter(spec, "glazing_light_transmittance")[0]
        self.assertEqual(g_perp.status, SUBSTITUTABLE)
        self.assertEqual(g_perp.project_value, 0.60)
        self.assertEqual(g_perp.reference_value, SIA3802_LIMIT_VALUES["glazing_g_value"])
        self.assertEqual(tau_v.project_value, 0.65)
        self.assertEqual(
            tau_v.reference_value, SIA3802_LIMIT_VALUES["glazing_light_transmittance"]
        )

    def test_non_en410_g_value_blocks_rather_than_substituting(self):
        # A g-value whose source is not proven EN 410 g_perp (e.g. a g_total that
        # already includes shading) must never be substituted for the reference.
        spec = build_reference_project_specification(
            [
                _room(
                    surfaces=[_surface()],
                    openings=[_opening(solar_factor_source="building_regs", g_value_bs_en_410=None)],
                )
            ],
            _Analyzer(),
        )
        g_perp = _by_parameter(spec, "glazing_g_value")[0]
        self.assertEqual(g_perp.status, PROJECT_VALUE_MISSING)
        self.assertIsNone(g_perp.project_value)
        self.assertEqual(spec.status, "BLOCKED_INCOMPLETE_INPUTS")
        self.assertTrue(any("g_perp" in blocker for blocker in spec.blockers))

    def test_explicit_en410_field_makes_g_value_substitutable(self):
        # The solar factor source string is absent, but the explicit EN 410 field
        # is present: the gate accepts it and uses the modelled solar factor.
        spec = build_reference_project_specification(
            [
                _room(
                    surfaces=[_surface()],
                    openings=[_opening(solar_factor_source=None, g_value_bs_en_410=0.48)],
                )
            ],
            _Analyzer(),
        )
        g_perp = _by_parameter(spec, "glazing_g_value")[0]
        self.assertEqual(g_perp.status, SUBSTITUTABLE)
        self.assertEqual(g_perp.project_value, 0.60)

    def test_missing_visible_transmittance_blocks(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()], openings=[_opening(visible_transmittance=None)])],
            _Analyzer(),
        )
        self.assertEqual(
            _by_parameter(spec, "glazing_light_transmittance")[0].status,
            PROJECT_VALUE_MISSING,
        )
        self.assertEqual(spec.status, "BLOCKED_INCOMPLETE_INPUTS")

    def test_missing_opening_value_blocks(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()], openings=[_opening(u_value=None)])],
            _Analyzer(),
        )
        self.assertEqual(_by_parameter(spec, "window_u")[0].status, PROJECT_VALUE_MISSING)
        self.assertEqual(spec.status, "BLOCKED_INCOMPLETE_INPUTS")

    def test_external_door_is_not_treated_as_window(self):
        spec = build_reference_project_specification(
            [
                _room(
                    surfaces=[_surface()],
                    openings=[
                        _opening(
                            id="door-1",
                            opening_type="door",
                            u_value=None,
                            frame_fraction=None,
                        )
                    ],
                )
            ],
            _Analyzer(),
        )
        self.assertEqual(_by_parameter(spec, "window_u"), [])
        self.assertEqual(_by_parameter(spec, "window_frame_fraction"), [])
        self.assertEqual(spec.blockers, ())


class InfiltrationSubstitutionTests(unittest.TestCase):
    def test_building_infiltration_is_paired_with_table_2(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()], infiltration_m3_h_m2=0.10)], _Analyzer()
        )
        item = _by_parameter(spec, "infiltration_m3_h_m2")[0]
        self.assertEqual(item.status, SUBSTITUTABLE)
        self.assertEqual(item.scope, "building")
        self.assertEqual(item.project_value, 0.10)
        self.assertEqual(
            item.reference_value, SIA3802_LIMIT_VALUES["infiltration_m3_h_m2"]
        )
        self.assertEqual(item.unit, "m3/(h.m2)")

    def test_worst_case_infiltration_is_reported_not_an_average(self):
        spec = build_reference_project_specification(
            [
                _room(surfaces=[_surface()], infiltration_m3_h_m2=0.10),
                _room(infiltration_m3_h_m2=0.20),
            ],
            _Analyzer(),
        )
        self.assertEqual(
            _by_parameter(spec, "infiltration_m3_h_m2")[0].project_value, 0.20
        )

    def test_missing_infiltration_blocks(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()], infiltration_m3_h_m2=None)], _Analyzer()
        )
        item = _by_parameter(spec, "infiltration_m3_h_m2")[0]
        self.assertEqual(item.status, PROJECT_VALUE_MISSING)
        self.assertIsNone(item.project_value)
        self.assertEqual(spec.status, "BLOCKED_INCOMPLETE_INPUTS")

    def test_incomparable_infiltration_unit_blocks_rather_than_substituting(self):
        spec = build_reference_project_specification(
            [
                _room(
                    surfaces=[_surface()],
                    infiltration_m3_h_m2=None,
                    infiltration_rate=0.5,
                )
            ],
            _Analyzer(),
        )
        item = _by_parameter(spec, "infiltration_m3_h_m2")[0]
        self.assertEqual(item.status, PROJECT_VALUE_MISSING)
        self.assertTrue(any("unit" in blocker.lower() for blocker in spec.blockers))


def _system(**kwargs):
    """Build a normalized HVAC system dict as model_analyzer emits it."""
    payload = {
        "id": "sys-1",
        "name": "System 1",
        "cooling_capacity_kw": None,
        "heating_capacity_kw": None,
        "eer": None,
        "scop": None,
    }
    payload.update(kwargs)
    return payload


class GenerationSubstitutionTests(unittest.TestCase):
    def test_cooling_below_threshold_is_paired_with_table_5_eer(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()], hvac_systems=[_system(cooling_capacity_kw=100.0, eer=3.5)])],
            _Analyzer(),
        )
        item = _by_parameter(spec, "cooling_generation_eer")[0]
        self.assertEqual(item.status, SUBSTITUTABLE)
        self.assertEqual(item.project_value, 3.5)
        self.assertEqual(item.reference_value, 3.10)  # Table 5, band >50..<=150
        self.assertEqual(item.unit, "EER")

    def test_cooling_band_is_selected_by_capacity(self):
        cases = {10.0: 2.90, 40.0: 3.00, 120.0: 3.10}
        for capacity, expected in cases.items():
            spec = build_reference_project_specification(
                [_room(surfaces=[_surface()], hvac_systems=[_system(cooling_capacity_kw=capacity, eer=4.0)])],
                _Analyzer(),
            )
            self.assertEqual(
                _by_parameter(spec, "cooling_generation_eer")[0].reference_value,
                expected,
                msg=f"capacity {capacity}",
            )

    def test_cooling_at_or_above_150kw_blocks_on_eer_plus_metric(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()], hvac_systems=[_system(cooling_capacity_kw=200.0, eer=4.5)])],
            _Analyzer(),
        )
        item = _by_parameter(spec, "cooling_generation_eer")[0]
        self.assertEqual(item.status, PROJECT_VALUE_MISSING)
        self.assertIsNone(item.reference_value)
        self.assertTrue(any("EER+" in blocker for blocker in spec.blockers))

    def test_missing_cooling_capacity_blocks(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()], hvac_systems=[_system(eer=3.5)])],
            _Analyzer(),
        )
        self.assertEqual(
            _by_parameter(spec, "cooling_generation_eer")[0].status, PROJECT_VALUE_MISSING
        )
        self.assertTrue(any("cooling capacity" in b for b in spec.blockers))

    def test_heating_is_paired_with_table_8_scop_and_carries_en14825_caveat(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()], hvac_systems=[_system(heating_capacity_kw=100.0, scop=4.0)])],
            _Analyzer(),
        )
        item = _by_parameter(spec, "heating_generation_scop")[0]
        self.assertEqual(item.status, SUBSTITUTABLE)
        self.assertEqual(item.project_value, 4.0)
        self.assertEqual(item.reference_value, 3.20)  # Table 8, band >50..<=150
        self.assertIn("SN EN 14825", item.source)

    def test_heating_above_150kw_blocks_because_table_8_stops_there(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()], hvac_systems=[_system(heating_capacity_kw=300.0, scop=4.5)])],
            _Analyzer(),
        )
        item = _by_parameter(spec, "heating_generation_scop")[0]
        self.assertEqual(item.status, PROJECT_VALUE_MISSING)
        self.assertIsNone(item.reference_value)
        self.assertTrue(any("air-water heat" in b for b in spec.blockers))

    def test_same_system_across_rooms_is_not_double_counted(self):
        system = _system(cooling_capacity_kw=100.0, eer=3.5)
        spec = build_reference_project_specification(
            [
                _room(surfaces=[_surface()], hvac_systems=[system]),
                _room(hvac_systems=[system]),
            ],
            _Analyzer(),
        )
        self.assertEqual(len(_by_parameter(spec, "cooling_generation_eer")), 1)


class VentilationSubstitutionTests(unittest.TestCase):
    def test_heat_recovery_efficiency_is_paired_with_table_2(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()], hvac_systems=[_system(heat_recovery_efficiency=0.60)])],
            _Analyzer(),
        )
        item = _by_parameter(spec, "ventilation_heat_recovery_efficiency")[0]
        self.assertEqual(item.status, SUBSTITUTABLE)
        self.assertEqual(item.project_value, 0.60)
        self.assertEqual(item.reference_value, 0.73)   # Table 2 eta_rec,theta limit
        self.assertEqual(item.reference_target_value, 0.78)  # target
        self.assertIn("TO VERIFY", item.source)  # NCM<->SIA index caveat

    def test_zero_heat_recovery_is_still_compared(self):
        # A system without heat recovery reports 0.0 -- a real project value to
        # compare against the reference, not a reason to skip.
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()], hvac_systems=[_system(heat_recovery_efficiency=0.0)])],
            _Analyzer(),
        )
        self.assertEqual(
            _by_parameter(spec, "ventilation_heat_recovery_efficiency")[0].project_value, 0.0
        )

    def test_missing_heat_recovery_value_emits_no_substitution(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()], hvac_systems=[_system()])], _Analyzer()
        )
        self.assertEqual(_by_parameter(spec, "ventilation_heat_recovery_efficiency"), [])


class ReferenceDirectiveTests(unittest.TestCase):
    def test_emission_and_capacity_directives_are_emitted_without_blocking(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()])], _Analyzer()
        )
        emission = _by_parameter(spec, "emission_system_type")[0]
        capacity = _by_parameter(spec, "max_heating_cooling_capacity")[0]
        self.assertEqual(emission.status, REFERENCE_DIRECTIVE)
        self.assertEqual(emission.reference_value, 0.0)
        self.assertIn("onvective", emission.directive)
        self.assertEqual(capacity.status, REFERENCE_DIRECTIVE)
        self.assertIn("nlimited", capacity.directive)

    def test_directives_do_not_count_as_blockers(self):
        # A fully resolvable envelope + directives must stay PARTIAL, not BLOCKED:
        # a directive has no project value by design and is not a missing input.
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()], openings=[_opening()])], _Analyzer()
        )
        self.assertEqual(spec.status, "PARTIAL_REFERENCE_INPUT_SPECIFICATION")
        directives = [s for s in spec.substitutions if s.status == REFERENCE_DIRECTIVE]
        self.assertEqual(len(directives), 2)
        self.assertEqual(spec.blockers, ())


class ReferenceTargetValueTests(unittest.TestCase):
    def test_envelope_and_window_carry_both_limit_and_target(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()], openings=[_opening()])], _Analyzer()
        )
        wall = _by_parameter(spec, "external_wall_u")[0]
        self.assertEqual(wall.reference_value, SIA3802_LIMIT_VALUES["external_wall_u"])
        self.assertEqual(wall.reference_target_value, 0.14)
        self.assertEqual(_by_parameter(spec, "window_u")[0].reference_target_value, 0.88)

    def test_cooling_target_comes_from_the_same_table_5_band(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()], hvac_systems=[_system(cooling_capacity_kw=100.0, eer=3.5)])],
            _Analyzer(),
        )
        item = _by_parameter(spec, "cooling_generation_eer")[0]
        self.assertEqual(item.reference_value, 3.10)   # Table 5 limit
        self.assertEqual(item.reference_target_value, 3.20)  # Table 5 target

    def test_heating_target_is_the_brine_water_table_9_not_air_water(self):
        # SIA 380/2:2022 7.2.5.8-9: the limit is the air-water HP (Table 8, no
        # target column) and the target is the brine-water HP (Table 9).
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()], hvac_systems=[_system(heating_capacity_kw=100.0, scop=4.0)])],
            _Analyzer(),
        )
        item = _by_parameter(spec, "heating_generation_scop")[0]
        self.assertEqual(item.reference_value, 3.20)   # Table 8 air-water limit
        self.assertEqual(item.reference_target_value, 4.60)  # Table 9 brine-water target

    def test_heating_target_is_undefined_below_the_table_9_range(self):
        # Table 9 (brine-water) starts at 12 kW; a smaller heat pump has an
        # air-water limit but no brine-water target -- reported as None, not guessed.
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()], hvac_systems=[_system(heating_capacity_kw=8.0, scop=3.5)])],
            _Analyzer(),
        )
        item = _by_parameter(spec, "heating_generation_scop")[0]
        self.assertEqual(item.reference_value, 3.00)   # Table 8 <=12 limit
        self.assertIsNone(item.reference_target_value)

    def test_identity_and_directive_rows_have_no_target(self):
        room = _room(surfaces=[_surface()])
        # The checker sets this attribute (sia380_checker.py:726); mirror it.
        setattr(room, "sia2024_category", "1.01")
        spec = build_reference_project_specification([room], _Analyzer())
        directives = [s for s in spec.substitutions if s.status == REFERENCE_DIRECTIVE]
        identities = [s for s in spec.substitutions if s.status == STANDARD_USAGE_INPUT]
        self.assertTrue(directives and identities)
        self.assertTrue(all(s.reference_target_value is None for s in directives))
        self.assertTrue(all(s.reference_target_value is None for s in identities))

    def test_to_dict_exposes_the_target(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()])], _Analyzer()
        )
        self.assertIn("reference_target_value", spec.to_dict()["substitutions"][0])


class CompleteSpecificationTests(unittest.TestCase):
    def test_resolvable_envelope_remains_partial_until_all_table2_families_exist(self):
        spec = build_reference_project_specification(
            [
                _room(
                    surfaces=[
                        _surface(id="w", surface_type="wall"),
                        _surface(id="r", surface_type="roof", construction_ids=["ROOF1"]),
                    ],
                    openings=[_opening()],
                )
            ],
            _Analyzer(),
        )
        self.assertEqual(spec.status, "PARTIAL_REFERENCE_INPUT_SPECIFICATION")
        self.assertFalse(spec.is_complete)
        self.assertEqual(spec.blockers, ())
        self.assertIn("sia380_annual_aggregation_and_weighting", spec.missing_input_families)
        # Every emitted input is resolved: numeric substitutions are SUBSTITUTABLE,
        # reference-run directives are REFERENCE_DIRECTIVE, and SIA 2024 usage
        # inputs are STANDARD_USAGE_INPUT; none is a blocker.
        self.assertTrue(
            all(
                item.status in (SUBSTITUTABLE, REFERENCE_DIRECTIVE, STANDARD_USAGE_INPUT)
                for item in spec.substitutions
            )
        )

    def test_notes_refuse_to_read_as_a_compliance_conclusion(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()])], _Analyzer()
        )
        joined = " ".join(spec.notes).lower()
        self.assertIn("not a compliance conclusion", joined)
        self.assertIn("reviewer acceptance", joined)

    def test_to_dict_is_serializable_and_complete(self):
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()])], _Analyzer()
        )
        payload = spec.to_dict()
        self.assertEqual(
            set(payload),
            {
                "status",
                "substitutions",
                "blockers",
                "notes",
                "implemented_input_families",
                "missing_input_families",
                "is_complete",
            },
        )
        self.assertIn("reference_value", payload["substitutions"][0])


class UsageStandardInputTests(unittest.TestCase):
    """Tests pour les entrées d'usage SIA 2024 identiques projet/référence.

    Article de norme : SIA 380/2:2022 §7.2.5.3.
    Données de référence : refs/reference-data/sia-2024-2021.usage-data.json.
    """

    def _room_with_usage(self, code: str) -> RoomData:
        """Construit une pièce avec sia2024_category positionné.

        Reproduit exactement ce que le checker fait à la ligne 726 de
        swiss_sia/sia380_checker.py : setattr(room, "sia2024_category", ...).
        """
        r = _room(surfaces=[_surface()])
        setattr(r, "sia2024_category", code)
        return r

    def test_resolved_usage_emits_six_substitutions_with_standard_usage_input_status(self):
        # Usage "1.01" (Wohnen MFH) : 6 grandeurs SIA 2024 émises.
        spec = build_reference_project_specification(
            [self._room_with_usage("1.01")], _Analyzer()
        )
        usage_items = [s for s in spec.substitutions if s.element_type == "sia2024_usage"]
        self.assertEqual(len(usage_items), 6)
        for item in usage_items:
            self.assertEqual(item.status, STANDARD_USAGE_INPUT)
            self.assertIsNone(item.project_value)
            self.assertIsNotNone(item.reference_value)
            self.assertEqual(item.scope, "1.01")
            self.assertIn("SIA 2024:2021", item.source)

    def test_reference_values_match_json_anchors_for_1_01(self):
        # Valeurs d'ancrage lues dans le JSON pour usage 1.01.
        # theta_i_mean col30=25°C, phi_i col34=60%, A_p col42=35m², M col43=1.2met.
        spec = build_reference_project_specification(
            [self._room_with_usage("1.01")], _Analyzer()
        )
        by_param = {
            s.parameter: s
            for s in spec.substitutions
            if s.scope == "1.01"
        }
        self.assertEqual(by_param["theta_i_mean"].reference_value, 25.0)
        self.assertEqual(by_param["phi_i"].reference_value, 60.0)
        self.assertEqual(by_param["A_p"].reference_value, 35.0)
        self.assertEqual(by_param["M"].reference_value, 1.2)

    def test_theta_i_mean_uses_col30_exploitation_not_col28_design(self):
        # La norme impose theta_i_mean (col30=25) ; theta_i_design (col28=26)
        # ne doit jamais être utilisé comme consigne énergie.
        spec = build_reference_project_specification(
            [self._room_with_usage("1.01")], _Analyzer()
        )
        by_param = {
            s.parameter: s
            for s in spec.substitutions
            if s.scope == "1.01"
        }
        # 25 = col30 exploitation ; 26 = col28 design (interdit ici)
        self.assertEqual(by_param["theta_i_mean"].reference_value, 25.0)
        self.assertNotEqual(by_param["theta_i_mean"].reference_value, 26.0)

    def test_dedup_two_rooms_same_usage_emits_one_set_of_six_substitutions(self):
        # Deux pièces avec le même usage → 1 jeu de 6 substitutions, 2 pièces.
        spec = build_reference_project_specification(
            [self._room_with_usage("1.01"), self._room_with_usage("1.01")],
            _Analyzer(),
        )
        usage_items = [s for s in spec.substitutions if s.scope == "1.01"]
        self.assertEqual(len(usage_items), 6)
        for item in usage_items:
            self.assertEqual(item.affected_elements, 2)

    def test_unresolved_usage_code_emits_one_aggregated_blocker_not_one_per_room(self):
        # Code inconnu dans le JSON → bloqueur agrégé (pas un par pièce).
        r1 = _room(surfaces=[_surface()])
        r2 = _room(surfaces=[_surface()])
        setattr(r1, "sia2024_category", "9.99")
        setattr(r2, "sia2024_category", "9.99")
        spec = build_reference_project_specification([r1, r2], _Analyzer())
        usage_blockers = [b for b in spec.blockers if "SIA 2024 usage not resolved" in b]
        self.assertEqual(len(usage_blockers), 1)
        self.assertIn("2 room", usage_blockers[0])

    def test_missing_sia2024_category_emits_no_substitution_and_no_blocker(self):
        # Pièces sans sia2024_category (tests existants) → ignorées silencieusement.
        spec = build_reference_project_specification(
            [_room(surfaces=[_surface()])], _Analyzer()
        )
        usage_items = [s for s in spec.substitutions if s.element_type == "sia2024_usage"]
        self.assertEqual(usage_items, [])
        usage_blockers = [b for b in spec.blockers if "SIA 2024 usage" in b]
        self.assertEqual(usage_blockers, [])

    def test_standard_usage_input_does_not_cause_blocked_status(self):
        # STANDARD_USAGE_INPUT est résolu → le statut global n'est pas BLOCKED.
        spec = build_reference_project_specification(
            [self._room_with_usage("1.01")], _Analyzer()
        )
        usage_items = [s for s in spec.substitutions if s.status == STANDARD_USAGE_INPUT]
        self.assertGreater(len(usage_items), 0)
        self.assertNotEqual(spec.status, "BLOCKED_INCOMPLETE_INPUTS")
        self.assertEqual(spec.blockers, ())


if __name__ == "__main__":
    unittest.main()
