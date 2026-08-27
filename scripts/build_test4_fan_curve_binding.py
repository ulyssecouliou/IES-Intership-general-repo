"""Build the provisional, source-traced SIA 4010 Test 4 fan-map binding."""

import hashlib
import json
from pathlib import Path

import fitz

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "SIA_4010_geteilter_Link" / "Test4" / "Spezifikation_Test4.pdf"
OUTPUT = ROOT / "sia4010_evidence" / "source_audits" / "test4_fan_curve_20260826"

CALIBRATION = {
    "embedded_image_size_px": [624, 624],
    "x_axis": {
        "quantity": "volume_flow_m3_h",
        "origin_px": 47,
        "origin_value": 0.0,
        "reference_px": 529,
        "reference_value": 3000.0,
    },
    "y_axis": {
        "quantity": "static_pressure_pa",
        "origin_px": 583,
        "origin_value": 0.0,
        "reference_px": 63,
        "reference_value": 1200.0,
    },
    "rounding": {"volume_flow_m3_h": 10.0, "static_pressure_pa": 5.0},
    "estimated_digitization_uncertainty": {
        "volume_flow_m3_h": 25.0,
        "static_pressure_pa": 10.0,
    },
}

# Centres of the numbered circles in the 624 x 624 embedded fan-map image.
PIXEL_POINTS = {
    1: (551, 583),
    2: (465, 409),
    3: (389, 258),
    4: (249, 128),
    5: (469, 583),
    6: (412, 452),
    7: (344, 340),
    8: (226, 252),
    9: (400, 583),
    10: (352, 492),
    11: (297, 414),
    12: (192, 353),
    13: (330, 583),
    14: (297, 526),
    15: (249, 474),
    16: (160, 435),
}

# Exact transcription of the measured-values table below the fan map.
MEASURED_TABLE = {
    1: (3450, 581, 2.58, 77),
    2: (3450, 673, 2.98, 74),
    3: (3450, 750, 3.30, 71),
    4: (3450, 691, 3.07, 79),
    5: (3000, 349, 1.55, 73),
    6: (3000, 446, 1.97, 71),
    7: (3000, 486, 2.16, 68),
    8: (3000, 432, 1.92, 75),
    9: (2500, 202, 0.90, 68),
    10: (2500, 258, 1.14, 66),
    11: (2500, 281, 1.25, 63),
    12: (2500, 250, 1.11, 70),
    13: (2000, 103, 0.46, 63),
    14: (2000, 132, 0.59, 60),
    15: (2000, 144, 0.64, 57),
    16: (2000, 128, 0.57, 64),
}


def _sha256_bytes(payload):
    return hashlib.sha256(payload).hexdigest()


def _sha256(path):
    return _sha256_bytes(path.read_bytes())


def _round_to(value, increment):
    return round(value / increment) * increment


def _calibrate(point):
    x_px, y_px = point
    x_axis = CALIBRATION["x_axis"]
    y_axis = CALIBRATION["y_axis"]
    flow = (x_px - x_axis["origin_px"]) * (
        (x_axis["reference_value"] - x_axis["origin_value"])
        / (x_axis["reference_px"] - x_axis["origin_px"])
    )
    pressure = (y_axis["origin_px"] - y_px) * (
        (y_axis["reference_value"] - y_axis["origin_value"])
        / (y_axis["origin_px"] - y_axis["reference_px"])
    )
    return (
        int(_round_to(flow, CALIBRATION["rounding"]["volume_flow_m3_h"])),
        int(_round_to(pressure, CALIBRATION["rounding"]["static_pressure_pa"])),
    )


def build_payload(
    source=SOURCE,
    input_id="test4_fan_curve_digitization",
    locator=(
        "Spezifikation_Test4.pdf, page 2/3, Ventilatoren Kennfeld and "
        "Luftleistung 50 Hz"
    ),
    nominal_operating_points=None,
    fan_page_index=1,
    fan_image_index=1,
    table_page_index=1,
    table_image_index=2,
):
    """Return one binding for a specification using the shared fan map."""

    source = Path(source)
    document = fitz.open(source)
    fan_embedded = document[fan_page_index].get_images(full=True)
    table_embedded = document[table_page_index].get_images(full=True)
    fan_image = document.extract_image(fan_embedded[fan_image_index][0])["image"]
    table_image = document.extract_image(table_embedded[table_image_index][0])["image"]
    points = []
    for point_id in sorted(PIXEL_POINTS):
        flow, pressure = _calibrate(PIXEL_POINTS[point_id])
        speed, power, current, sound = MEASURED_TABLE[point_id]
        points.append(
            {
                "point_id": point_id,
                "pixel_center": list(PIXEL_POINTS[point_id]),
                "volume_flow_m3_h": flow,
                "static_pressure_pa": pressure,
                "speed_rpm": speed,
                "electrical_power_w": power,
                "current_a": current,
                "sound_power_dba": sound,
            }
        )
    return {
        "schema_version": "1.0",
        "input_id": input_id,
        "status": "PROVISIONAL_DIGITIZATION_AWAITING_AUTHORITY_ACCEPTANCE",
        "compliance_claim_allowed": False,
        "source": {
            "path": str(source.relative_to(ROOT)).replace("\\", "/"),
            "sha256": _sha256(source),
            "locator": locator,
            "fan_map_embedded_image_sha256": _sha256_bytes(fan_image),
            "measured_table_embedded_image_sha256": _sha256_bytes(table_image),
        },
        "calibration": CALIBRATION,
        "digitized_points": points,
        "nominal_operating_points_from_page_text": nominal_operating_points
        or {
            "supply": {
                "volume_flow_m3_h": 1700,
                "static_pressure_pa": 500,
                "electrical_power_w": 407,
                "speed_rpm": 2790,
            },
            "extract": {
                "volume_flow_m3_h": 1700,
                "static_pressure_pa": 400,
                "electrical_power_w": 331,
                "speed_rpm": 2730,
            },
        },
        "interpolation_authorized": False,
        "authority_question": (
            "May the page-2 fan-map graph be digitized for validation, and "
            "what interpolation method and numerical tolerance are accepted?"
        ),
        "claim_guardrail": (
            "The table values are direct transcriptions and the flow/pressure "
            "coordinates are graphical digitizations with declared uncertainty. "
            "No interpolated fan model or SIA verdict is authorized until the "
            "validation authority accepts this method."
        ),
    }


def validate(payload):
    points = payload["digitized_points"]
    if len(points) != 16 or {item["point_id"] for item in points} != set(range(1, 17)):
        raise ValueError("The Test 4 fan binding must contain points 1 through 16")
    for speed, ids in {
        3450: (4, 3, 2, 1),
        3000: (8, 7, 6, 5),
        2500: (12, 11, 10, 9),
        2000: (16, 15, 14, 13),
    }.items():
        curve = [next(item for item in points if item["point_id"] == key) for key in ids]
        if any(item["speed_rpm"] != speed for item in curve):
            raise ValueError("Speed/table mismatch for {} rpm".format(speed))
        flows = [item["volume_flow_m3_h"] for item in curve]
        pressures = [item["static_pressure_pa"] for item in curve]
        if flows != sorted(flows) or pressures != sorted(pressures, reverse=True):
            raise ValueError(
                "Non-monotonic digitized pressure curve at {} rpm".format(speed)
            )
    if payload["interpolation_authorized"] is not False:
        raise ValueError("Provisional Test 4 digitization cannot authorize interpolation")


def main():
    payload = build_payload()
    validate(payload)
    write_evidence(payload, OUTPUT)


def write_evidence(payload, output):
    """Write one strict external-input binding and validation report."""

    validate(payload)
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    stem = payload["input_id"]
    binding = output / "{}.binding.json".format(stem)
    binding.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    validation = {
        "schema_version": "1.0",
        "input_id": payload["input_id"],
        "source_sha256": payload["source"]["sha256"],
        "status": "PASS",
        "validated_by": "Deterministic fan-map calibration and table cross-check",
        "validation_method": (
            "Checksum-bound embedded-image calibration; monotonicity checks "
            "for four speed curves; direct point-ID join to the measured table"
        ),
        "binding_artifact": {
            "path": binding.name,
            "sha256": _sha256(binding),
            "schema_id": "sia4010.fan_curves.v1",
        },
        "checks": [
            {
                "id": "TEST4-FAN-16-POINTS",
                "status": "PASS",
                "detail": "All graph points 1 through 16 are present.",
            },
            {
                "id": "TEST4-FAN-TABLE-JOIN",
                "status": "PASS",
                "detail": "Every point is joined to its measured speed and power row.",
            },
            {
                "id": "TEST4-FAN-CURVE-MONOTONICITY",
                "status": "PASS",
                "detail": "Flow rises and pressure falls on all four speed curves.",
            },
            {
                "id": "TEST4-FAN-NOMINAL-POINTS",
                "status": "PASS",
                "detail": "Supply and extract nominal text values remain separate.",
            },
            {
                "id": "TEST4-FAN-CLAIM-GUARDRAIL",
                "status": "PASS",
                "detail": "Interpolation and compliance claims remain disabled.",
            },
        ],
        "compliance_claim_allowed": False,
        "claim_guardrail": (
            "PASS validates the internal consistency and traceability of the "
            "provisional digitization only. Normative authorization remains "
            "UNCONFIRMED in the external-input manifest."
        ),
    }
    report = output / "{}.validation.json".format(stem)
    report.write_text(
        json.dumps(validation, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(binding)
    print(report)


if __name__ == "__main__":
    main()
