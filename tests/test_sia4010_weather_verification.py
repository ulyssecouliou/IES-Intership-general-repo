"""Tests for fixed-width TMY1 parsing and ISO climate source verification."""

import unittest
from pathlib import Path

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.weather_verification import parse_tmy1

ROOT = Path(__file__).resolve().parents[1]
TEMP_ROOT = ROOT / ".codex_tmp"


def _record(
    *,
    station="23062",
    year=59,
    month=1,
    day=1,
    hour=1,
    ghi_flag="8",
    ghi_kj_h=0,
    dry_tenths=0,
    wind_tenths=28,
):
    line = list(" " * 132)

    def place(start, width, value):
        text = str(value)
        line[start : start + width] = list(text.rjust(width))

    place(0, 5, station)
    place(5, 2, year)
    place(7, 2, month)
    place(9, 2, day)
    place(11, 2, hour)
    line[53] = ghi_flag
    place(54, 4, ghi_kj_h)
    place(103, 4, dry_tenths)
    place(114, 4, wind_tenths)
    return "".join(line)


class Tmy1WeatherVerificationTests(unittest.TestCase):
    def setUp(self):
        self.folder = TEMP_ROOT / self._testMethodName
        self.folder.mkdir(parents=True, exist_ok=True)

    def test_parser_reads_hourly_identity_fields(self):
        path = self.folder / "DRYCOLD.TMY"
        path.write_text(
            _record(ghi_kj_h=360, dry_tenths=-12) + "\n",
            encoding="ascii",
        )
        records = parse_tmy1(path)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].station_id, "23062")
        self.assertEqual(records[0].source_year, 1959)
        self.assertEqual(records[0].month, 1)
        self.assertEqual(records[0].hour_ending, 1)
        self.assertEqual(records[0].dry_bulb_c, -1.2)
        self.assertEqual(records[0].wind_speed_m_s, 2.8)
        self.assertEqual(records[0].global_horizontal_w_m2, 100.0)

    def test_parser_rejects_short_records(self):
        path = self.folder / "DRYCOLD.TMY"
        path.write_text("too short\n", encoding="ascii")
        with self.assertRaises(ConfigurationError):
            parse_tmy1(path)


if __name__ == "__main__":
    unittest.main()
