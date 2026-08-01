"""Source-geometry extraction tests against the supplied official IFC."""

import unittest
from pathlib import Path

from swiss_sia.reference_model.sia4010.ifc_space_extractor import (
    AbstractBimIfcSpaceExtractor,
)


ROOT = Path(__file__).resolve().parents[1]
IFC = (
    ROOT
    / "SIA_4010_geteilter_Link"
    / "Beispielgebäude"
    / "IFC_Beispielebäude_201106_abstractBIM.ifc"
)


@unittest.skipUnless(IFC.is_file(), "official example-building IFC not present")
class Sia4010IfcSpaceExtractorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.extractor = AbstractBimIfcSpaceExtractor(IFC)

    def test_test4_lecture_hall_geometry_matches_ifc_quantities(self):
        room = self.extractor.extract(["101"])["101"]
        self.assertEqual(room.long_name, "Hörsaal")
        self.assertAlmostEqual(room.area_m2, 165.81, places=2)
        self.assertAlmostEqual(room.height_m, 6.38, places=9)
        self.assertAlmostEqual(
            room.volume_m3,
            room.area_m2 * room.height_m,
            places=9,
        )
        self.assertAlmostEqual(room.volume_m3, 1058.0, delta=0.2)
        self.assertAlmostEqual(room.base_elevation_m, 3.38, places=9)

    def test_test5_keeps_all_eight_rooms_separate(self):
        numbers = ["100", "102", "200", "201", "202", "203", "204", "205"]
        rooms = self.extractor.extract(numbers)
        self.assertEqual(set(rooms), set(numbers))
        expected_areas = {
            "100": 31.62,
            "102": 104.94,
            "200": 31.62,
            "201": 17.14,
            "202": 17.14,
            "203": 17.14,
            "204": 17.14,
            "205": 33.13,
        }
        for number, expected in expected_areas.items():
            with self.subTest(number=number):
                self.assertAlmostEqual(rooms[number].area_m2, expected, places=2)
                self.assertAlmostEqual(rooms[number].height_m, 3.0, places=9)
        self.assertAlmostEqual(
            sum(room.area_m2 for room in rooms.values()),
            269.85942,
            places=5,
        )

    def test_test6_restaurant_and_kitchen_footprints_are_exact(self):
        rooms = self.extractor.extract(["001", "002"])
        self.assertEqual(rooms["002"].long_name, "Küche")
        self.assertAlmostEqual(rooms["001"].area_m2, 237.36, places=2)
        self.assertAlmostEqual(rooms["002"].area_m2, 35.88, places=2)
        self.assertEqual(
            rooms["002"].footprint_xy_m,
            (
                (29.642, 10.669),
                (19.972, 10.669),
                (19.972, 6.959),
                (29.642, 6.959),
            ),
        )
        self.assertEqual(rooms["001"].base_elevation_m, 0.0)

    def test_every_record_retains_source_checksum(self):
        room = self.extractor.extract(["001"])["001"]
        self.assertEqual(len(room.source_sha256), 64)
        self.assertEqual(Path(room.source_path), IFC)


if __name__ == "__main__":
    unittest.main()
