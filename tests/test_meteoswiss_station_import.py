"""Unit tests for ``swiss_sia.reference_model.meteoswiss_station_import``.

The tests use a small synthetic fixture (station code ``TST``) that mirrors
the exact CSV shape of the MeteoSwiss ``klimaszenarien-raumklima-*`` product
so the module is proven station-agnostic without depending on the
downloaded archives.
"""

from __future__ import annotations

import io
import json
import os
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.meteoswiss_station_import import (
    convert_meteoswiss_station_archive,
    convert_meteoswiss_station_directory,
    unpack_meteoswiss_archive,
)


_METADATA_HEADER = (
    "Station;Abk.;Stationstyp;Type de station;Tipo di stazione;Station type;"
    "Standorttyp;Type de site;Tipo di sito;Site type;Eigentuemer;Proprietaire;"
    "Proprietario;Owner;Stationshoehe m. ue. M.;KoordinatenE;KoordinatenN;"
    "Breitengrad;Laengengrad;Kanton;Parameter;Parametre;Parametro;Parameter"
)
_METADATA_ROW = (
    "Test / Station;TST;skalierte Beobachtungen;observations;osservazioni;"
    "scaled;laendlich;rural;rurale;rural;MeteoSchweiz;MeteoSuisse;"
    "MeteoSvizzera;MeteoSwiss;500;2600000;1200000;47.0;8.0;XX;"
    "Temperatur;Temperature;Temperatura;Temperature"
)


def _write_metadata(root: Path, station: str) -> None:
    text = "{}\n{}\n".format(_METADATA_HEADER, _METADATA_ROW.replace("TST", station))
    (root / "{}_Metadata.csv".format(station)).write_text(text, encoding="utf-8")


def _write_scenario(root: Path, station: str, scenario: str, year: int) -> None:
    """Write a minimal 8760-hour CSV with valid transport values."""

    header = (
        "time.yy,time.mm,time.dd,time.hh,tre200h0,ure200h0,fkl010h0,"
        "fkl010h1,dkl010h0,skycover,gls,str.diffus,str.direkt"
    )
    lines = [header]
    from datetime import datetime, timedelta

    start = datetime(year, 1, 1, 0)
    for hour in range(8760):
        moment = start + timedelta(hours=hour)
        # Non-zero direct and diffuse radiation at midday so the internal
        # controls of `_write_meteoswiss_epw_candidate` pass; the specific
        # values do not matter for the station-agnostic contract.
        is_daytime = 8 <= moment.hour <= 18
        gls = 300.0 if is_daytime else 0.0
        dif = 150.0 if is_daytime else 0.0
        dir_n = 500.0 if is_daytime else 0.0
        lines.append(
            "{yy},{mm},{dd},{hh},10.0,60,2.0,4.0,180,50,{gls},{dif},{dir_n}".format(
                yy=moment.year,
                mm=moment.month,
                dd=moment.day,
                hh=moment.hour,
                gls=gls,
                dif=dif,
                dir_n=dir_n,
            )
        )
    text = "\n".join(lines) + "\n"
    (root / "{}_{}.csv".format(station, scenario)).write_text(text, encoding="utf-8")


class StationDirectoryConversionTests(unittest.TestCase):

    def test_generic_station_code_writes_expected_outputs(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source = tmp / "klimaszenarien-raumklima-TST"
            source.mkdir()
            _write_metadata(source, "TST")
            _write_scenario(source, "TST", "2035_RCP85_DRY", 2035)
            # Both scenarios use 2035 (non-leap) to satisfy the internal
            # 365-day common-year contract of _combine_meteoswiss_csv_records.
            _write_scenario(source, "TST", "2060_RCP85_DRY", 2035)

            output_root = tmp / "generated"
            summary = convert_meteoswiss_station_directory(
                station_code="TST",
                input_directory=source,
                output_directory=output_root,
                time_zone_hours=1.0,
            )
            self.assertEqual(summary["station_code"], "TST")
            self.assertEqual(len(summary["outputs"]), 2)
            self.assertFalse(summary["compliance_claim_allowed"])

            station_dir = output_root / "TST"
            expected_files = {
                "TST_2035_RCP85_DRY_IESVE_CANDIDATE.epw",
                "TST_2035_RCP85_DRY_IESVE_DERIVATION.json",
                "TST_2060_RCP85_DRY_IESVE_CANDIDATE.epw",
                "TST_2060_RCP85_DRY_IESVE_DERIVATION.json",
                "TST_IESVE_CONVERSION_SUMMARY.json",
            }
            self.assertTrue(expected_files.issubset({p.name for p in station_dir.iterdir()}))

    def test_missing_metadata_fails_closed(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source = tmp / "TST_only_scenario"
            source.mkdir()
            _write_scenario(source, "TST", "2035_RCP85_DRY", 2035)
            with self.assertRaises(ConfigurationError):
                convert_meteoswiss_station_directory(
                    station_code="TST",
                    input_directory=source,
                    output_directory=tmp / "generated",
                    time_zone_hours=1.0,
                )

    def test_zero_scenarios_fails_closed(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source = tmp / "TST_only_metadata"
            source.mkdir()
            _write_metadata(source, "TST")
            with self.assertRaises(ConfigurationError):
                convert_meteoswiss_station_directory(
                    station_code="TST",
                    input_directory=source,
                    output_directory=tmp / "generated",
                    time_zone_hours=1.0,
                )

    def test_lowercase_station_code_is_normalised(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            source = tmp / "klimaszenarien-raumklima-TST"
            source.mkdir()
            _write_metadata(source, "TST")
            _write_scenario(source, "TST", "2035_RCP85_DRY", 2035)
            summary = convert_meteoswiss_station_directory(
                station_code="tst",
                input_directory=source,
                output_directory=tmp / "generated",
                time_zone_hours=1.0,
            )
            self.assertEqual(summary["station_code"], "TST")

    def test_illegal_station_code_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            with self.assertRaises(ConfigurationError):
                convert_meteoswiss_station_directory(
                    station_code="bad code!",
                    input_directory=Path(tmp),
                    output_directory=Path(tmp) / "generated",
                    time_zone_hours=1.0,
                )


class ArchiveUnpackTests(unittest.TestCase):

    def _make_archive(self, tmp: Path, station: str) -> Path:
        archive = tmp / "klimaszenarien-raumklima-{}.zip".format(station)
        with zipfile.ZipFile(archive, "w") as z:
            z.writestr(
                "{}_Metadata.csv".format(station),
                "{}\n{}\n".format(_METADATA_HEADER, _METADATA_ROW.replace("TST", station)),
            )
            # One minimal scenario CSV.
            from datetime import datetime, timedelta

            start = datetime(2035, 1, 1)
            header = (
                "time.yy,time.mm,time.dd,time.hh,tre200h0,ure200h0,fkl010h0,"
                "fkl010h1,dkl010h0,skycover,gls,str.diffus,str.direkt"
            )
            rows = [header]
            for hour in range(8760):
                moment = start + timedelta(hours=hour)
                is_daytime = 8 <= moment.hour <= 18
                rows.append(
                    "{yy},{mm},{dd},{hh},10.0,60,2.0,4.0,180,50,{gls},{dif},{dir_n}".format(
                        yy=moment.year,
                        mm=moment.month,
                        dd=moment.day,
                        hh=moment.hour,
                        gls=300.0 if is_daytime else 0.0,
                        dif=150.0 if is_daytime else 0.0,
                        dir_n=500.0 if is_daytime else 0.0,
                    )
                )
            z.writestr(
                "{}_2035_RCP85_DRY.csv".format(station),
                "\n".join(rows) + "\n",
            )
        return archive

    def test_unpack_and_convert_round_trip(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            archive = self._make_archive(tmp, "TST")
            summary = convert_meteoswiss_station_archive(
                archive_path=archive,
                unpack_root=tmp / "unpacked",
                output_directory=tmp / "generated",
                time_zone_hours=1.0,
            )
            self.assertEqual(summary["station_code"], "TST")
            self.assertEqual(len(summary["outputs"]), 1)
            extracted = tmp / "unpacked" / "klimaszenarien-raumklima-TST"
            self.assertTrue((extracted / "TST_Metadata.csv").is_file())

    def test_archive_without_metadata_fails_closed(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            archive = tmp / "klimaszenarien-raumklima-TST.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("TST_2035_RCP85_DRY.csv", "no data")
            with self.assertRaises(ConfigurationError):
                unpack_meteoswiss_archive(archive, tmp / "unpacked")

    def test_archive_with_traversal_path_rejected(self) -> None:
        with TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            archive = tmp / "klimaszenarien-raumklima-TST.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr(
                    "TST_Metadata.csv",
                    "{}\n{}\n".format(_METADATA_HEADER, _METADATA_ROW),
                )
                z.writestr("../evil.csv", "boom")
            with self.assertRaises(ConfigurationError):
                unpack_meteoswiss_archive(archive, tmp / "unpacked")


if __name__ == "__main__":
    unittest.main()
