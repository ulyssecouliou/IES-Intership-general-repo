# -*- coding: utf-8 -*-
"""Generate the SIA 4010 Anwenderbericht for one test from recorded evidence.

Runs outside IESVE: it reads the central evidence ledger and writes a Markdown
report plus a status JSON. No ``iesve`` import, no VE project needed.

The factual sections come from the ledger. The ``Feststellungen`` section is
never generated — supply it with ``--observation`` once the engineer answering
for the submission has written it, together with ``--author`` and ``--date``.
Until then the report stays ``ANWENDERBERICHT_DRAFT_UNSIGNED``.

Examples::

    # Draft for Test 1 from whatever the ledger currently holds
    python scripts/build_anwenderbericht.py --test 1

    # Same, with the verified factual sections pre-filled from artifacts
    python scripts/build_anwenderbericht.py --test 1 \
        --facts-file config/anwenderbericht_test1_facts.json

    # Same, with the reviewer's prose supplied
    python scripts/build_anwenderbericht.py --test 1 \
        --software-name "IES Virtual Environment" --software-version "2025" \
        --calculation-engine "ApacheSim" \
        --input-parameter "ISO 52016-1 clause 7 test cell, lightweight case 600" \
        --data-source "Climate: ISO 52016-1 DRYCOLD, Denver CO, per specification" \
        --observation "Cooling energy deviates by X percent; cause under review." \
        --author "Ulysse Couliou" --date 2026-08-12
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

DEFAULT_LEDGER = (
    PROJECT_ROOT / "sia4010_evidence" / "autonomy" / "sia4010_case_evidence.json"
)
DEFAULT_OUTPUT = PROJECT_ROOT / "sia4010_evidence" / "anwenderberichte"


#: Keys a facts file may never carry. Observations, the author and the date are
#: the engineer's signature on the submission; a JSON file cannot sign anything.
FORBIDDEN_FACT_KEYS = ("observations", "author", "report_date", "date")


def _load_facts(path):
    """Load the verified factual pre-fill, refusing anything that would sign."""

    if path is None:
        return {}
    if not path.is_file():
        raise SystemExit("Facts file does not exist: {}".format(path))
    with path.open(encoding="utf-8") as handle:
        facts = json.load(handle)
    if not isinstance(facts, dict):
        raise SystemExit("Facts file must hold a JSON object: {}".format(path))
    present = [key for key in FORBIDDEN_FACT_KEYS if key in facts]
    if present:
        raise SystemExit(
            "A facts file may not supply {}: the Feststellungen, the author "
            "and the date must be given deliberately on the command line by "
            "the engineer answering for the submission.".format(", ".join(present))
        )
    return {key: value for key, value in facts.items() if not key.startswith("_")}


def main() -> int:
    """Build one source-traced Anwenderbericht from command-line arguments."""

    from swiss_sia.reference_model.sia4010.anwenderbericht import (
        AnwenderberichtError,
        ProgramIdentity,
        STATUS_READY_FOR_REVIEW,
        build_anwenderbericht,
        write_anwenderbericht,
    )

    parser = argparse.ArgumentParser(
        description=__doc__.strip().splitlines()[0],
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--test", required=True, help="Base test id, e.g. 1")
    parser.add_argument("--ledger", type=Path, default=DEFAULT_LEDGER)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--software-name", default="")
    parser.add_argument("--software-version", default="")
    parser.add_argument("--calculation-engine", default="")
    parser.add_argument("--supplier", default="")
    parser.add_argument("--program-note", default="")
    parser.add_argument(
        "--input-parameter",
        action="append",
        default=[],
        help="Repeatable. One Eingabeparameter entry.",
    )
    parser.add_argument(
        "--data-source",
        action="append",
        default=[],
        help="Repeatable. One Daten entry, with its provenance.",
    )
    parser.add_argument(
        "--special-assumption",
        action="append",
        default=[],
        help="Repeatable. Omit entirely when there are none.",
    )
    parser.add_argument(
        "--observation",
        action="append",
        default=[],
        help=(
            "Repeatable. One Feststellungen entry. Never generated: declare "
            "and explain every deviation here."
        ),
    )
    parser.add_argument("--author", default="")
    parser.add_argument("--date", default="", help="Report date, e.g. 2026-08-12")
    parser.add_argument(
        "--facts-file",
        type=Path,
        default=None,
        help=(
            "JSON holding the verified factual pre-fill (program identity, "
            "Eingabeparameter, Daten, Spezielle Annahmen), so a reviewer does "
            "not retype facts already recorded in artifacts. Explicit command "
            "line values win over the file. The file may NOT supply "
            "observations, author or date: see config/"
            "anwenderbericht_test1_facts.json."
        ),
    )
    args = parser.parse_args()

    facts = _load_facts(args.facts_file)
    program_facts = facts.get("program", {})

    try:
        report = build_anwenderbericht(
            str(args.ledger),
            args.test,
            ProgramIdentity(
                software_name=args.software_name
                or program_facts.get("software_name", ""),
                software_version=args.software_version
                or program_facts.get("software_version", ""),
                calculation_engine=args.calculation_engine
                or program_facts.get("calculation_engine", ""),
                supplier=args.supplier or program_facts.get("supplier", ""),
                notes=args.program_note or program_facts.get("notes", ""),
            ),
            input_parameters=(args.input_parameter or facts.get("input_parameters", [])),
            data_sources=args.data_source or facts.get("data_sources", []),
            special_assumptions=(
                args.special_assumption or facts.get("special_assumptions", [])
            ),
            observations=args.observation,
            author=args.author,
            report_date=args.date,
        )
    except AnwenderberichtError as exc:
        print("Cannot build the report: {}".format(exc), file=sys.stderr)
        return 2

    status = write_anwenderbericht(report, str(args.output))

    print("Anwenderbericht Test {}: {}".format(status["test_id"], status["status"]))
    print(
        "Cases: {} recorded result(s) of {}".format(
            status["cases_with_recorded_result"], status["case_count"]
        )
    )
    print("Report: {}".format(status["markdown_path"]))
    if status["missing_for_signature"]:
        print("Outstanding before signature:")
        for item in status["missing_for_signature"]:
            print("  - {}".format(item))
    if status["status"] != STATUS_READY_FOR_REVIEW:
        print(
            "This is a draft. It carries no validation claim and must not be "
            "submitted as it stands."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
