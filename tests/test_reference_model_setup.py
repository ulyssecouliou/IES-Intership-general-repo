"""Pure tests for project-local reference-model setup."""

from __future__ import annotations

import unittest
from pathlib import Path

from swiss_sia.reference_model_setup import (
    EpwMetadata,
    ReferenceModelSetupError,
    build_project_configuration,
    read_epw_metadata,
)


class ReferenceModelSetupTests(unittest.TestCase):
    def setUp(self) -> None:
        self.repository = Path(__file__).resolve().parents[1]

    def test_repository_weather_header_is_read_without_scenario_inference(self) -> None:
        weather = Path(
            r"C:\Users\ulysse.couliou\Documents\switzerland\SMA_2035_RCP85_DRY.epw"
        )
        if not weather.is_file():
            self.skipTest("Local qualified EPW fixture is unavailable")
        metadata = read_epw_metadata(weather)
        self.assertTrue(metadata.station)
        self.assertIsNotNone(metadata.latitude)

    def test_configuration_removes_stale_client_weather_metadata(self) -> None:
        import json

        source = json.loads(
            (self.repository / "config" / "reference_model_config.json").read_text(
                encoding="utf-8"
            )
        )
        epw = EpwMetadata(
            station="Test Station",
            region="Region",
            country="CH",
            data_source="Source",
            station_id="123",
            latitude=46.2,
            longitude=7.1,
            time_zone=1.0,
            elevation_m=500.0,
        )
        result = build_project_configuration(
            source, Path(r"C:\MODEL_TEST\selected.epw"), "abc123", epw
        )
        parameters = result["parameters"]
        self.assertEqual(parameters["weather_station"]["value"], "Test Station")
        self.assertEqual(parameters["site_latitude_degrees"]["value"], 46.2)
        self.assertEqual(
            parameters["climate_scenario"]["value"],
            "UNCONFIRMED_REVIEW_REQUIRED",
        )
        self.assertEqual(result["metadata"]["weather_compliance_review"], "PENDING")
        self.assertNotIn("RCP8.5", parameters["climate_scenario"]["value"])

    def test_invalid_epw_is_rejected(self) -> None:
        with self.assertRaises(ReferenceModelSetupError):
            read_epw_metadata(self.repository / "README.md")


if __name__ == "__main__":
    unittest.main()
