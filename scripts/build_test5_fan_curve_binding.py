"""Build the provisional, source-traced SIA 4010 Test 5 fan-map binding."""

from pathlib import Path

from build_test4_fan_curve_binding import build_payload, write_evidence

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "SIA_4010_geteilter_Link" / "Test5" / "Spezifikation_Test5.pdf"
OUTPUT = ROOT / "sia4010_evidence" / "source_audits" / "test5_fan_curve_20260826"


def build_test5_payload():
    """Return the Test 5 binding using its own source and nominal points."""

    return build_payload(
        source=SOURCE,
        input_id="test5_fan_curve_digitization",
        locator=(
            "Spezifikation_Test5.pdf, page 2/5 fan map and page 3/5 "
            "Luftleistung 50 Hz table"
        ),
        nominal_operating_points={
            "supply": {
                "volume_flow_m3_h": 1040,
                "static_pressure_pa": 770,
                "electrical_power_w": 420,
                "speed_rpm": 3000,
            },
            "extract": {
                "volume_flow_m3_h": 1040,
                "static_pressure_pa": 520,
                "electrical_power_w": 290,
                "speed_rpm": 2500,
            },
        },
        fan_page_index=1,
        fan_image_index=1,
        table_page_index=2,
        table_image_index=0,
    )


def main():
    write_evidence(build_test5_payload(), OUTPUT)


if __name__ == "__main__":
    main()
