"""Tests for the SIA 2028 DRY normal weather importer.

The synthetic fixture reproduces the exact 29-column shape of the supplied
Kloten file so the contract is exercised without depending on the official
dataset. A second group runs against the real file when it is present.
"""

from __future__ import annotations

import json
import math
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from swiss_sia.reference_model.sia_dry_weather_import import (
    EXPECTED_COLUMNS,
    EXPECTED_HOURS,
    KLOTEN,
    SiaDryImportError,
    convert_sia_dry_to_epw,
    parse_sia_dry_file,
)


ROOT = Path(__file__).resolve().parents[1]
OFFICIAL_FILE = ROOT / "references" / "standards" / "sia2028" / "KLO_dry.txt"

HEADER = (
    "stn\ttime.yy\ttime.mm\ttime.dd\ttime.hh\ttre200h0\tprestahs\ture200h0\t"
    "rre150h0\tfkl010h0\tfkl010h1\tdkl010h0\ttso100hs\tnto000sw\tgls\t"
    "str.diffus\tstr.direkt\tstr.vert.E\tstr.vert.S\tstr.vert.W\tstr.vert.N\t"
    "bodenalbedo\tir.horizontal\tir.vertikal.S\tbodenemissivitaet\tdewpt\t"
    "enthalpy\tmixratio\twetbulb"
)


def _dew_point(dry_bulb: float, relative_humidity: float) -> float:
    a, b = 17.62, 243.12
    gamma = math.log(relative_humidity / 100.0) + (a * dry_bulb) / (b + dry_bulb)
    return (b * gamma) / (a - gamma)


def _write_fixture(
    path: Path,
    *,
    hours: int = EXPECTED_HOURS,
    sky_cover_every: int = 8,
    break_continuity_at: int | None = None,
    dew_point_offset: float = 0.0,
    diffuse_above_global: bool = False,
) -> None:
    from datetime import datetime, timedelta

    start = datetime(2001, 1, 1)
    lines = [HEADER]
    for position in range(hours):
        moment = start + timedelta(hours=position)
        month, day, hour = moment.month, moment.day, moment.hour
        if break_continuity_at is not None and position == break_continuity_at:
            hour = (hour + 3) % 24
        dry_bulb = 10.0
        relative_humidity = 70.0
        dew = _dew_point(dry_bulb, relative_humidity) + dew_point_offset
        daytime = 8 <= moment.hour <= 17
        global_h = 300 if daytime else 0
        diffuse = (global_h + 50) if diffuse_above_global and daytime else (
            120 if daytime else 0
        )
        direct = 400 if daytime else 0
        # 40 percent -> exactly 4 tenths, avoiding a rounding tie so the test
        # subject stays the sentinel behaviour rather than tie-breaking.
        sky = "40" if position % sky_cover_every == 0 else "NA"
        lines.append(
            "\t".join(
                [
                    "KLO",
                    str(moment.year),
                    "{:02d}".format(month),
                    "{:02d}".format(day),
                    "{:02d}".format(hour),
                    "{:.1f}".format(dry_bulb),
                    "974.0",
                    "{:.1f}".format(relative_humidity),
                    "0.0",
                    "2.0",
                    "4.0",
                    "180",
                    "NA",
                    sky,
                    str(global_h),
                    str(diffuse),
                    str(direct),
                    "10",
                    "20",
                    "10",
                    "5",
                    "30",
                    "300",
                    "310",
                    "98",
                    "{:.1f}".format(dew),
                    "20.0",
                    "5.50",
                    "7.0",
                ]
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


class SiaDryParseTests(unittest.TestCase):

    def test_parses_a_well_formed_year(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "KLO_dry.txt"
            _write_fixture(source)
            rows, audit = parse_sia_dry_file(str(source))
            self.assertEqual(len(rows), EXPECTED_HOURS)
            self.assertEqual(audit["row_count"], EXPECTED_HOURS)
            self.assertEqual(audit["station_codes"], ["KLO"])
            self.assertEqual(len(audit["header"]), EXPECTED_COLUMNS)

    def test_records_provisional_column_availability(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "KLO_dry.txt"
            _write_fixture(source, sky_cover_every=8)
            _rows, audit = parse_sia_dry_file(str(source))
            sky = audit["provisional_column_availability"]["nto000sw"]
            self.assertEqual(sky["hours_present"], EXPECTED_HOURS // 8)
            self.assertEqual(sky["legend_status"], "TO_VERIFY")
            self.assertEqual(
                audit["provisional_column_availability"]["prestahs"]["hours_present"],
                EXPECTED_HOURS,
            )

    def test_rejects_wrong_hour_count(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "KLO_dry.txt"
            _write_fixture(source, hours=100)
            with self.assertRaises(SiaDryImportError):
                parse_sia_dry_file(str(source))

    def test_rejects_discontinuous_year(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "KLO_dry.txt"
            _write_fixture(source, break_continuity_at=4000)
            with self.assertRaisesRegex(SiaDryImportError, "continuous 365-day"):
                parse_sia_dry_file(str(source))

    def test_rejects_missing_required_column(self) -> None:
        with TemporaryDirectory() as tmp:
            source = Path(tmp) / "KLO_dry.txt"
            _write_fixture(source)
            text = source.read_text(encoding="utf-8").splitlines()
            text[0] = text[0].replace("\tdewpt", "\tsomething_else")
            source.write_text("\n".join(text) + "\n", encoding="utf-8")
            with self.assertRaisesRegex(SiaDryImportError, "lacks required columns"):
                parse_sia_dry_file(str(source))


class SiaDryConversionTests(unittest.TestCase):

    def test_writes_epw_and_audit_with_supplied_values(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "KLO_dry.txt"
            _write_fixture(source)
            audit = convert_sia_dry_to_epw(str(source), str(tmp_path / "out"))
            self.assertEqual(audit["status"], "READY_FOR_IESVE_READ_ONLY_PROBE")
            self.assertFalse(audit["compliance_claim_allowed"])
            self.assertTrue(audit["official_sia_weather_identity_confirmed"])
            self.assertEqual(audit["weather"]["record_count"], EXPECTED_HOURS)
            self.assertIn("dew_point", audit["supplied_rather_than_derived"])
            self.assertIn("station_pressure", audit["supplied_rather_than_derived"])
            self.assertIn("horizontal_infrared", audit["supplied_rather_than_derived"])
            epw = Path(audit["weather"]["path"])
            self.assertTrue(epw.is_file())
            lines = epw.read_text(encoding="ascii").splitlines()
            self.assertTrue(lines[0].startswith("LOCATION,"))
            self.assertEqual(len(lines) - 8, EXPECTED_HOURS)

    def test_epw_hours_run_one_to_twentyfour(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "KLO_dry.txt"
            _write_fixture(source)
            audit = convert_sia_dry_to_epw(str(source), str(tmp_path / "out"))
            rows = [
                line.split(",")
                for line in Path(audit["weather"]["path"])
                .read_text(encoding="ascii")
                .splitlines()[8:]
                if line.strip()
            ]
            self.assertEqual(rows[0][3], "1")
            self.assertEqual(rows[23][3], "24")
            self.assertEqual(rows[24][3], "1")

    def test_absent_sky_cover_becomes_the_epw_sentinel(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "KLO_dry.txt"
            # Sky cover present only on the very first hour.
            _write_fixture(source, sky_cover_every=EXPECTED_HOURS)
            audit = convert_sia_dry_to_epw(str(source), str(tmp_path / "out"))
            rows = [
                line.split(",")
                for line in Path(audit["weather"]["path"])
                .read_text(encoding="ascii")
                .splitlines()[8:]
                if line.strip()
            ]
            # Field 23 (index 22) is total sky cover.
            self.assertEqual(rows[0][22], "4")  # 40 percent -> 4 tenths
            self.assertEqual(rows[1][22], "99")  # sentinel, never estimated
            self.assertIn("total_sky_cover", audit["written_as_epw_missing"])

    def test_inconsistent_dew_point_fails_closed(self) -> None:
        """A wrong column legend must abort, not produce a usable EPW."""

        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "KLO_dry.txt"
            _write_fixture(source, dew_point_offset=6.0)
            with self.assertRaisesRegex(SiaDryImportError, "column legend"):
                convert_sia_dry_to_epw(str(source), str(tmp_path / "out"))

    def test_diffuse_above_global_fails_closed(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "KLO_dry.txt"
            _write_fixture(source, diffuse_above_global=True)
            with self.assertRaisesRegex(SiaDryImportError, "diffuse exceeds global"):
                convert_sia_dry_to_epw(str(source), str(tmp_path / "out"))


@unittest.skipUnless(OFFICIAL_FILE.is_file(), "official KLO_dry.txt not imported")
class OfficialKlotenFileTests(unittest.TestCase):
    """Pins what the supplied Zuerich Kloten dataset actually contains."""

    OFFICIAL_SHA256 = (
        "aa3f3853300ceb55293c418d75ebfa36ef74353693acbaf369703c65bd337ffd"
    )

    def test_official_file_checksum(self) -> None:
        import hashlib

        digest = hashlib.sha256(OFFICIAL_FILE.read_bytes()).hexdigest()
        self.assertEqual(digest, self.OFFICIAL_SHA256)

    def test_official_file_parses_and_matches_recorded_aggregates(self) -> None:
        rows, audit = parse_sia_dry_file(str(OFFICIAL_FILE))
        self.assertEqual(len(rows), EXPECTED_HOURS)
        self.assertEqual(audit["station_codes"], ["KLO"])
        temperatures = [row.dry_bulb_c for row in rows]
        self.assertAlmostEqual(min(temperatures), -13.1, places=4)
        self.assertAlmostEqual(max(temperatures), 34.1, places=4)
        self.assertAlmostEqual(
            sum(temperatures) / len(temperatures), 9.4692, places=3
        )

    def test_official_file_has_full_pressure_and_infrared_but_sparse_sky_cover(
        self,
    ) -> None:
        _rows, audit = parse_sia_dry_file(str(OFFICIAL_FILE))
        availability = audit["provisional_column_availability"]
        self.assertEqual(availability["prestahs"]["hours_present"], EXPECTED_HOURS)
        self.assertEqual(
            availability["ir.horizontal"]["hours_present"], EXPECTED_HOURS
        )
        self.assertEqual(availability["nto000sw"]["hours_present"], 1095)

    def test_official_dew_point_column_holds_across_the_whole_year(self) -> None:
        """The identification of ``dewpt`` is not a one-row coincidence."""

        rows, _audit = parse_sia_dry_file(str(OFFICIAL_FILE))
        worst = 0.0
        for row in rows:
            computed = _dew_point(row.dry_bulb_c, row.relative_humidity_percent)
            worst = max(worst, abs(computed - row.dew_point_c))
        self.assertLess(worst, 1.0, msg="max deviation {:.3f} K".format(worst))


if __name__ == "__main__":
    unittest.main()
