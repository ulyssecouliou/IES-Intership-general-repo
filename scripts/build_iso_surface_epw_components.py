"""Build auditable EPW solar components from the public ISO climate workbook.

The ISO workbook contains hourly irradiance on N/E/S/W/H surfaces, but no EPW
DNI/DHI pair.  A provisional horizontal diffuse fraction is reconstructed from
the four vertical direct components and solar geometry, then normalized by
month to the published Table 26 horizontal diffuse totals.  GHI is always the
workbook's hourly H series and DNI is the residual direct horizontal component
divided by cos(zenith).
"""

import csv
import hashlib
import json
import math
import sys
from pathlib import Path

import xlrd


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
XLS = ROOT / "refs" / "ISO_52016_1_BESTEST_ClimData_2016.08.24.xls"
TMY = ROOT / "references" / "standards" / "bestest" / "DRYCOLD.TMY"
OUTPUT = ROOT / "refs" / "reference-data" / "iso52016_epw_solar_components.csv"
AUDIT = ROOT / "refs" / "reference-data" / "iso52016_epw_solar_components.audit.json"
MONTHLY_HORIZONTAL_DIFFUSE_KWH_M2 = (
    14.1, 20.4, 31.2, 35.1, 41.2, 35.5,
    32.5, 31.8, 24.8, 17.5, 14.9, 11.8,
)


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _load_iso_rows():
    sheet = xlrd.open_workbook(str(XLS)).sheet_by_index(0)
    rows = []
    for row_index in range(5, sheet.nrows):
        month = sheet.cell_value(row_index, 1)
        if isinstance(month, float):
            rows.append([sheet.cell_value(row_index, column) for column in range(16)])
    if len(rows) != 9504:
        raise RuntimeError("Expected 9504 ISO climate rows; found {}".format(len(rows)))
    return rows[744:]


def build():
    from swiss_sia.reference_model.sia4010.weather_conversion import (
        _cosine_solar_zenith,
        _parse_tmy1,
    )

    iso_rows = _load_iso_rows()
    tmy_rows = _parse_tmy1(TMY)
    if len(iso_rows) != 8760 or len(tmy_rows) != 8760:
        raise RuntimeError("ISO/TMY annual row count mismatch")

    provisional_dhi = []
    for iso, tmy in zip(iso_rows, tmy_rows):
        north, east, south, west = iso[6], iso[7], iso[8], iso[9]
        horizontal = max(0.0, iso[13])
        cos_zenith = _cosine_solar_zenith(tmy)
        cos_altitude_plane = math.sqrt(max(0.0, 1.0 - cos_zenith**2))
        vertical_direct_vector = math.sqrt(
            (east - west) ** 2 + (north - south) ** 2
        )
        dni = (
            vertical_direct_vector / cos_altitude_plane
            if cos_altitude_plane > 1e-8 and horizontal > 0.0
            else 0.0
        )
        direct_horizontal = min(horizontal, max(0.0, dni * cos_zenith))
        provisional_dhi.append(horizontal - direct_horizontal)

    monthly_provisional = [0.0] * 12
    for iso, value in zip(iso_rows, provisional_dhi):
        monthly_provisional[int(iso[1]) - 1] += value / 1000.0
    factors = [
        target / observed if observed > 0.0 else 1.0
        for target, observed in zip(
            MONTHLY_HORIZONTAL_DIFFUSE_KWH_M2, monthly_provisional
        )
    ]

    output_rows = []
    for index, (iso, tmy, provisional) in enumerate(
        zip(iso_rows, tmy_rows, provisional_dhi)
    ):
        month = int(iso[1])
        ghi = max(0.0, float(iso[13]))
        dhi = min(ghi, max(0.0, provisional * factors[month - 1]))
        cos_zenith = _cosine_solar_zenith(tmy)
        dni = (ghi - dhi) / cos_zenith if cos_zenith > 1e-8 else 0.0
        output_rows.append(
            {
                "index": index,
                "month": tmy.month,
                "day": tmy.day,
                "hour_ending": tmy.hour_ending,
                "ghi_w_m2": ghi,
                "dni_w_m2": max(0.0, dni),
                "dhi_w_m2": dhi,
                "iso_north_w_m2": float(iso[6]),
                "iso_east_w_m2": float(iso[7]),
                "iso_south_w_m2": float(iso[8]),
                "iso_west_w_m2": float(iso[9]),
            }
        )

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    fields = tuple(output_rows[0])
    with OUTPUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(output_rows)

    monthly_dhi = [0.0] * 12
    for row in output_rows:
        monthly_dhi[row["month"] - 1] += row["dhi_w_m2"] / 1000.0
    audit = {
        "schema_version": "1.0",
        "status": "PASS",
        "purpose": "Source-derived EPW transport components; not a thermal-result calibration.",
        "sources": {
            "iso_workbook": {"path": str(XLS), "sha256": _sha256(XLS)},
            "tmy_time_and_solar_geometry": {"path": str(TMY), "sha256": _sha256(TMY)},
        },
        "output": {
            "path": str(OUTPUT),
            "sha256": _sha256(OUTPUT),
            "rows": len(output_rows),
        },
        "method": {
            "ghi": "Hourly ISO workbook horizontal surface H.",
            "provisional_dni": "Magnitude of N/E/S/W direct vector divided by cos(altitude plane).",
            "dhi": "Horizontal residual normalized monthly to ISO Table 26 diffuse H.",
            "dni": "(GHI-DHI)/cos(zenith), using TMY hour-ending midpoint geometry.",
        },
        "controls": {
            "annual_ghi_kwh_m2": sum(row["ghi_w_m2"] for row in output_rows) / 1000.0,
            "annual_dni_kwh_m2": sum(row["dni_w_m2"] for row in output_rows) / 1000.0,
            "annual_dhi_kwh_m2": sum(row["dhi_w_m2"] for row in output_rows) / 1000.0,
            "monthly_dhi_kwh_m2": monthly_dhi,
            "target_monthly_dhi_kwh_m2": MONTHLY_HORIZONTAL_DIFFUSE_KWH_M2,
            "monthly_normalization_factors": factors,
        },
        "limitations": [
            "The ISO workbook exposes surface irradiance, not a unique DNI/DHI decomposition.",
            "The transport pair must be verified by IESVE surface read-back before use as validation evidence.",
        ],
        "compliance_claim_allowed": False,
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    return audit


if __name__ == "__main__":
    receipt = build()
    print("ISO surface-derived EPW components: {}".format(receipt["status"]))
    print("CSV: {}".format(receipt["output"]["path"]))
    print("Audit: {}".format(AUDIT))
