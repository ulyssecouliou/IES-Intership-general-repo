"""Tests for the SIA 380/2 reference-project input specification."""

import unittest

from swiss_sia.config import SIA3802_LIMIT_VALUES
from swiss_sia.model_analyzer import ModelAnalyzer, OpeningData, RoomData, SurfaceData
from swiss_sia.reference_project import (
    PROJECT_VALUE_MISSING,
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
    """Build an external opening with defaults the specification reads."""
    payload = {
        "id": "w1",
        "name": "W1",
        "area": 2.0,
        "u_value": 1.4,
        "frame_fraction": 0.30,
        "is_external": True,
        "opening_type": "window",
        "construction_id": "STD_GLZ",
    }
    payload.update(kwargs)
    return OpeningData(**payload)


def _room(surfaces=None, openings=None):
    """Build a room carrying the given surfaces and openings."""
    return RoomData(
        id="r1",
        name="Room 1",
        surfaces=list(surfaces or []),
        openings=list(openings or []),
    )


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
        self.assertTrue(
            all(item.status == SUBSTITUTABLE for item in spec.substitutions)
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


if __name__ == "__main__":
    unittest.main()
