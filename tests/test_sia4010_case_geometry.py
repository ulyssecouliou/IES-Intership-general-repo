"""Tests for the exact common SIA 4010 Test 1/Test 2 cell geometry."""

import unittest
from pathlib import Path

from swiss_sia.reference_model.sia4010.case_geometry import (
    Sia4010CellGeometryGenerator,
    validate_cell_geometry,
)
from swiss_sia.reference_model.sia4010.case_manifest import Sia4010CaseManifest
from swiss_sia.reference_model.compliance_config import build_default_registry
from swiss_sia.reference_model.domain import SurfaceType
from swiss_sia.reference_model.validator import ReferenceModelValidator

ROOT = Path(__file__).resolve().parents[1]


class Sia4010CaseGeometryTests(unittest.TestCase):
    def setUp(self):
        manifest = Sia4010CaseManifest.load(
            ROOT / "config" / "sia4010_classes_1a_1b.json"
        )
        self.manifest = manifest
        self.model = Sia4010CellGeometryGenerator(manifest).generate()

    def test_exact_cell_dimensions_and_topology(self):
        self.assertEqual(self.model.floor_area_m2, 48.0)
        self.assertAlmostEqual(self.model.volume_m3, 129.6)
        self.assertEqual(len(self.model.spaces), 1)
        self.assertEqual(len(self.model.surfaces), 6)

    def test_two_south_windows_match_diagram(self):
        self.assertEqual(len(self.model.openings), 2)
        bounds = [opening.polygon.bounds for opening in self.model.openings]
        self.assertEqual(bounds[0], (0.5, 3.5, 0.0, 0.0, 0.2, 2.2))
        self.assertEqual(bounds[1], (4.5, 7.5, 0.0, 0.0, 0.2, 2.2))
        self.assertTrue(
            all(opening.polygon.area == 6.0 for opening in self.model.openings)
        )

    def test_dedicated_validator_passes(self):
        result = validate_cell_geometry(self.model, self.manifest)
        self.assertTrue(result.passed)
        self.assertTrue(all(result.checks.values()))

    def test_common_validator_uses_official_geometry_profile(self):
        self.assertTrue(
            any(
                surface.surface_type == SurfaceType.RAISED_FLOOR
                for surface in self.model.surfaces
            )
        )
        results = ReferenceModelValidator().validate_geometry(
            self.model, build_default_registry()
        )
        failures = [result for result in results if result.status.value == "FAIL"]
        self.assertEqual(failures, [])


if __name__ == "__main__":
    unittest.main()
