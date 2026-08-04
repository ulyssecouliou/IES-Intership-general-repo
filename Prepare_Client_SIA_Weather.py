"""Build an audited IESVE EPW candidate from the supplied client ZIP."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Optional, Sequence


REPOSITORY_ROOT = Path(__file__).resolve().parent
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from swiss_sia.reference_model.client_weather_conversion import (  # noqa: E402
    OUTPUT_AUDIT_NAME,
    convert_client_weather_archive,
)


def _parser() -> argparse.ArgumentParser:
    """Return the command-line contract with user-relative safe defaults."""

    parser = argparse.ArgumentParser(
        description="Create a source-traced EPW candidate without changing VE."
    )
    parser.add_argument(
        "--archive",
        type=Path,
        default=Path.home() / "Downloads" / "SIA 380_2 and SIA 4010.zip",
        help="Path to the original immutable client ZIP archive.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=REPOSITORY_ROOT.parent / "SIA_WEATHER_QUALIFIED",
        help="Output directory kept outside the Git repository.",
    )
    return parser


def run(arguments: Optional[Sequence[str]] = None) -> int:
    """Convert the archive and print the guarded next action."""

    options = _parser().parse_args(arguments)
    audit = convert_client_weather_archive(options.archive, options.output)
    print("CLIENT WEATHER CONVERSION: {}".format(audit["status"]))
    print("Weather: {}".format(audit["weather"]["path"]))
    print("SHA-256: {}".format(audit["weather"]["sha256"]))
    print("Audit: {}".format(options.output.resolve() / OUTPUT_AUDIT_NAME))
    print("Compliance claim allowed: NO")
    print("Next: copy the EPW and audit JSON to a disposable VE project, then")
    print("run Run_VE_Verify_Client_SIA_Weather.py. No VE data was changed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
