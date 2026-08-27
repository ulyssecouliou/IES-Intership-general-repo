"""Tests for deterministic reference geometry and gbXML serialization."""

import unittest
from dataclasses import replace
from xml.etree import ElementTree as ET

from swiss_sia.reference_model.compliance_config import build_default_registry
from swiss_sia.reference_model.gbxml_writer import GBXML_NAMESPACE, GbxmlWriter
from swiss_sia.reference_model.geometry import ReferenceGeometryGenerator
from swiss_sia.reference_model.results import ValidationStatus
from swiss_sia.reference_model.validator import ReferenceModelValidator


class ReferenceModelGeometryTests(unittest.TestCase):
    def setUp(self):
        self.parameters = build_default_registry()
        self.geometry = ReferenceGeometryGenerator(self.parameters).generate()

    def test_default_model_has_complete_required_object_types(self):
        self.assertEqual(len(self.geometry.spaces), 4)
        self.assertEqual(len(self.geometry.surfaces), 28)
        self.assertEqual(len(self.geometry.openings), 9)
        self.assertEqual(len(self.geometry.shades), 8)
        results = ReferenceModelValidator().validate_geometry(
            self.geometry, self.parameters
        )
        self.assertTrue(results)
        self.assertTrue(
            all(result.status == ValidationStatus.PASS for result in results),
            [(result.control_id, result.message) for result in results],
        )

    def test_zone_volumes_touch_but_do_not_overlap(self):
        first = self.geometry.spaces[0]
        duplicate = replace(
            self.geometry.spaces[1],
            bounds=first.bounds,
            shell_faces=first.shell_faces,
        )
        bad_model = replace(
            self.geometry,
            spaces=(first, duplicate) + self.geometry.spaces[2:],
        )
        result_by_id = {
            result.control_id: result
            for result in ReferenceModelValidator().validate_geometry(
                bad_model, self.parameters
            )
        }
        self.assertEqual(result_by_id["GEO-003"].status, ValidationStatus.FAIL)

    def test_gbxml_is_well_formed_deterministic_and_complete(self):
        writer = GbxmlWriter(self.parameters)
        first = writer.to_bytes(self.geometry)
        second = writer.to_bytes(self.geometry)
        self.assertEqual(first, second)
        root = ET.fromstring(first)
        namespace = {"g": GBXML_NAMESPACE}
        self.assertEqual(root.attrib["version"], "6.01")
        self.assertEqual(len(root.findall(".//g:Space", namespace)), 4)
        self.assertEqual(len(root.findall(".//g:Surface", namespace)), 28)
        self.assertEqual(len(root.findall(".//g:Opening", namespace)), 9)
        self.assertEqual(len(root.findall("./g:Zone", namespace)), 4)
        identifiers = [
            element.attrib["id"] for element in root.findall(".//*[@id]", namespace)
        ]
        self.assertEqual(len(identifiers), len(set(identifiers)))


if __name__ == "__main__":
    unittest.main()
