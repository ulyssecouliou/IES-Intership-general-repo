"""Convert MeteoSwiss GVE hourly CSV scenarios to audited EPW candidates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

from swiss_sia.reference_model.client_weather_conversion import (
    convert_meteoswiss_csv_directory,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("input_directory", type=Path)
    parser.add_argument("output_directory", type=Path)
    parser.add_argument(
        "--time-zone",
        type=float,
        required=True,
        help="EPW local standard-time offset from UTC; explicit reviewer input",
    )
    arguments = parser.parse_args()
    summary = convert_meteoswiss_csv_directory(
        arguments.input_directory,
        arguments.output_directory,
        time_zone_hours=arguments.time_zone,
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
