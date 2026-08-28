# -*- coding: utf-8 -*-
"""Build the SIA 4010 ``Anwenderbericht`` for one test from recorded evidence.

Every candidate submitting a SIA 4010 test must supply a signed user report.
Its structure was established on 2026-08-12 by reading the report the E4Tech
Excel reference program submitted for Test 1
(``221111_Anwenderbericht_EXCEL-E4Tech_Test1.docx``, dated 10.11.2022,
G. Zweifel):

    Wegleitung SIA 4010 / Validierung / Anwenderbericht
    Test Nr.            <n>
    Programm:           <program identity>
    Eingabeparameter:   <input parameters>
    Daten:              <data sources>
    Spezielle Annahmen: <special assumptions, or -->
    Feststellungen:     <observations>
    <date> / <author>

The German section labels are official form labels and are reproduced verbatim,
per the repository language rule for SIA form keys.

WHAT THIS GENERATOR DOES AND DOES NOT DO
========================================

It fills the *factual* sections from the central evidence ledger
(``sia4010_evidence/autonomy/sia4010_case_evidence.json``): which cases have a
verified model, which were simulated, which APS files exist with their
checksums, how many metrics were extracted, and whether an acceptance criterion
was available.

It never writes ``Feststellungen``. Those are engineering observations and
belong to a named human. The reference report's own findings show what they are
for: E4Tech declared *large deviations in cooling energy, particularly case
900*, and attributed part of them to the wall model and possibly to climate data
and infiltration. A deviation that is declared and explained is admissible; the
report is where that happens. A generator inventing that text would defeat the
purpose.

A report therefore carries ``ANWENDERBERICHT_DRAFT_UNSIGNED`` until a reviewer
supplies both the observations and the author, and the generator refuses to mark
it otherwise. It never emits a validation or conformity claim.

Output is Markdown: auditable, diffable, and meant to be transcribed into the
official form. This module does not attempt to reproduce another candidate's
document layout.

Pure Python: no ``iesve``, no third-party dependency.
"""

from __future__ import annotations

import json
import os
import tempfile
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

STATUS_DRAFT = "ANWENDERBERICHT_DRAFT_UNSIGNED"
STATUS_READY_FOR_REVIEW = "ANWENDERBERICHT_COMPLETE_AWAITING_SIGNATURE"

#: Official form labels, reproduced verbatim from the observed report.
LABEL_HEADER = "Wegleitung SIA 4010 / Validierung / Anwenderbericht"
LABEL_TEST_NR = "Test Nr."
LABEL_PROGRAMM = "Programm"
LABEL_EINGABEPARAMETER = "Eingabeparameter"
LABEL_DATEN = "Daten"
LABEL_SPEZIELLE_ANNAHMEN = "Spezielle Annahmen"
LABEL_FESTSTELLUNGEN = "Feststellungen"

#: The form's own marker for "no special assumptions", as used by the
#: reference report.
NO_SPECIAL_ASSUMPTIONS = "--"

PLACEHOLDER = "[TO VERIFY]"


class AnwenderberichtError(ValueError):
    """Raised when the report cannot be built from the supplied evidence."""


@dataclass(frozen=True)
class ProgramIdentity:
    """Identity of the candidate program, as it must appear under ``Programm``.

    Nothing here is derived by the software. A field left empty becomes an
    explicit placeholder in the report so a reviewer cannot overlook it.
    """

    software_name: str = ""
    software_version: str = ""
    calculation_engine: str = ""
    supplier: str = ""
    notes: str = ""

    def render(self) -> str:
        parts = [
            part.strip()
            for part in (
                self.software_name,
                self.software_version,
                self.calculation_engine,
                self.supplier,
            )
            if part and part.strip()
        ]
        if not parts:
            return PLACEHOLDER + " program identity not supplied"
        rendered = ", ".join(parts)
        if self.notes.strip():
            rendered = "{}; {}".format(rendered, self.notes.strip())
        return rendered


@dataclass(frozen=True)
class CaseEvidence:
    """Flattened evidence for one exact official case."""

    variant: str
    case_id: str
    model_status: str
    model_verification_basis: str
    simulation_status: str
    aps_path: str
    aps_sha256: str
    result_status: str
    observed_metric_count: Optional[int]
    acceptance_criterion_available: Optional[bool]
    required_output_scope_complete: Optional[bool]
    distribution_criterion_count: Optional[int]

    @property
    def has_recorded_result(self) -> bool:
        return bool(self.aps_path) and bool(self.aps_sha256)


@dataclass
class Anwenderbericht:
    """One assembled report, still unsigned."""

    test_id: str
    program: ProgramIdentity
    cases: Tuple[CaseEvidence, ...]
    input_parameters: Tuple[str, ...] = ()
    data_sources: Tuple[str, ...] = ()
    special_assumptions: Tuple[str, ...] = ()
    observations: Tuple[str, ...] = ()
    author: str = ""
    report_date: str = ""
    ledger_path: str = ""

    @property
    def status(self) -> str:
        if self.observations and self.author.strip() and self.report_date.strip():
            return STATUS_READY_FOR_REVIEW
        return STATUS_DRAFT

    @property
    def missing_for_signature(self) -> Tuple[str, ...]:
        missing: List[str] = []
        if not self.observations:
            missing.append(
                "Feststellungen: at least one observation, written by a named "
                "engineer. Declare and explain every deviation from the "
                "reference results here."
            )
        if not self.author.strip():
            missing.append("author: the person answering for these observations")
        if not self.report_date.strip():
            missing.append("report_date: the date the observations were made")
        if not self.input_parameters:
            missing.append(
                "Eingabeparameter: the model choices that determined the result"
            )
        if not self.data_sources:
            missing.append("Daten: the source of every input dataset used")
        return tuple(missing)


def _as_mapping(value: Any) -> Dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _optional_int(value: Any) -> Optional[int]:
    if isinstance(value, bool) or value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_bool(value: Any) -> Optional[bool]:
    return value if isinstance(value, bool) else None


def load_case_evidence(
    ledger_path: str,
    test_id: str,
) -> Tuple[CaseEvidence, ...]:
    """Read every case of one base test from the central evidence ledger.

    Cases are returned in ledger key order so a report is reproducible. A case
    with no recorded evidence is still returned: an honest report shows which
    cases were not run rather than omitting them.
    """

    if not os.path.isfile(ledger_path):
        raise AnwenderberichtError("Evidence ledger not found: {}".format(ledger_path))
    with open(ledger_path, "r", encoding="utf-8") as handle:
        ledger = json.load(handle)
    cases = ledger.get("cases")
    if not isinstance(cases, Mapping):
        raise AnwenderberichtError(
            "Evidence ledger has no 'cases' mapping: {}".format(ledger_path)
        )

    wanted = str(test_id)
    collected: List[CaseEvidence] = []
    for key in sorted(cases):
        record = _as_mapping(cases[key])
        if str(record.get("base_test_id", "")) != wanted:
            continue
        model = _as_mapping(record.get("model_evidence"))
        simulation = _as_mapping(record.get("simulation_evidence"))
        result = _as_mapping(record.get("result_evidence"))
        collected.append(
            CaseEvidence(
                variant=str(record.get("variant", "")),
                case_id=str(record.get("case_id", "")),
                model_status=str(model.get("status", "MISSING")),
                model_verification_basis=str(model.get("verification_basis", "")),
                simulation_status=str(simulation.get("status", "NOT_RUN")),
                aps_path=str(result.get("aps_path", "") or ""),
                aps_sha256=str(result.get("aps_sha256", "") or ""),
                result_status=str(result.get("status", "NOT_CHECKABLE")),
                observed_metric_count=_optional_int(result.get("observed_metric_count")),
                acceptance_criterion_available=_optional_bool(
                    result.get("acceptance_criterion_available")
                ),
                required_output_scope_complete=_optional_bool(
                    result.get("required_output_scope_complete")
                ),
                distribution_criterion_count=_optional_int(
                    result.get("distribution_criterion_count")
                ),
            )
        )
    if not collected:
        raise AnwenderberichtError(
            "Evidence ledger holds no case for base test {!r}".format(test_id)
        )
    return tuple(collected)


def build_anwenderbericht(
    ledger_path: str,
    test_id: str,
    program: ProgramIdentity,
    *,
    input_parameters: Sequence[str] = (),
    data_sources: Sequence[str] = (),
    special_assumptions: Sequence[str] = (),
    observations: Sequence[str] = (),
    author: str = "",
    report_date: str = "",
) -> Anwenderbericht:
    """Assemble one report from the ledger plus reviewer-supplied prose."""

    cases = load_case_evidence(ledger_path, test_id)
    return Anwenderbericht(
        test_id=str(test_id),
        program=program,
        cases=cases,
        input_parameters=tuple(x for x in input_parameters if str(x).strip()),
        data_sources=tuple(x for x in data_sources if str(x).strip()),
        special_assumptions=tuple(x for x in special_assumptions if str(x).strip()),
        observations=tuple(x for x in observations if str(x).strip()),
        author=author,
        report_date=report_date,
        ledger_path=os.path.abspath(ledger_path),
    )


def _tri_state(value: Optional[bool]) -> str:
    if value is True:
        return "yes"
    if value is False:
        return "no"
    return "not recorded"


def _bullets(items: Sequence[str], empty_marker: str) -> List[str]:
    if not items:
        return ["> {}".format(empty_marker)]
    return ["- {}".format(str(item).strip()) for item in items]


def render_markdown(report: Anwenderbericht) -> str:
    """Render the report for review and transcription into the official form."""

    recorded = [case for case in report.cases if case.has_recorded_result]
    lines: List[str] = []
    lines.append("# {}".format(LABEL_HEADER))
    lines.append("")
    lines.append("**{}** {}".format(LABEL_TEST_NR, report.test_id))
    lines.append("")
    lines.append("> Status: `{}`".format(report.status))
    lines.append(">")
    lines.append(
        "> This report states what was executed and observed. It is not a "
        "validation claim, and it carries no SIA or IES conformity statement. "
        "Only the SIA sub-commission can attest a validation."
    )
    lines.append("")
    lines.append("---")
    lines.append("")

    lines.append("## {}".format(LABEL_PROGRAMM))
    lines.append("")
    lines.append(report.program.render())
    lines.append("")

    lines.append("## {}".format(LABEL_EINGABEPARAMETER))
    lines.append("")
    lines.extend(
        _bullets(
            report.input_parameters,
            "{} to be completed by the reviewer: state the model choices that "
            "determined the result.".format(PLACEHOLDER),
        )
    )
    lines.append("")

    lines.append("## {}".format(LABEL_DATEN))
    lines.append("")
    lines.extend(
        _bullets(
            report.data_sources,
            "{} to be completed by the reviewer: state the source of every "
            "input dataset, with its provenance.".format(PLACEHOLDER),
        )
    )
    lines.append("")

    lines.append("## {}".format(LABEL_SPEZIELLE_ANNAHMEN))
    lines.append("")
    if report.special_assumptions:
        lines.extend(_bullets(report.special_assumptions, ""))
    else:
        lines.append(NO_SPECIAL_ASSUMPTIONS)
    lines.append("")

    lines.append("## {}".format(LABEL_FESTSTELLUNGEN))
    lines.append("")
    if report.observations:
        lines.extend(_bullets(report.observations, ""))
    else:
        lines.append(
            "> {} This section is never generated. It must be written by the "
            "engineer answering for the submission.".format(PLACEHOLDER)
        )
        lines.append(">")
        lines.append(
            "> Declare and explain every deviation from the reference results "
            "here. A documented deviation is admissible: the E4Tech reference "
            "program itself declared large deviations in cooling energy for "
            "case 900, attributing them to the wall model and possibly to "
            "climate data and infiltration. An undeclared deviation is not."
        )
    lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Recorded evidence")
    lines.append("")
    lines.append(
        "Read from the central evidence ledger. This section is generated and "
        "must not be edited by hand; correct the ledger instead."
    )
    lines.append("")
    lines.append(
        "| Case | Model | Simulation | Result | Metrics | Criterion available | "
        "Output scope complete |"
    )
    lines.append("|---|---|---|---|---:|---|---|")
    for case in report.cases:
        lines.append(
            "| `{variant}/{case}` | {model} | {sim} | {result} | {metrics} | "
            "{criterion} | {scope} |".format(
                variant=case.variant,
                case=case.case_id,
                model=case.model_status,
                sim=case.simulation_status,
                result=case.result_status,
                metrics=(
                    case.observed_metric_count
                    if case.observed_metric_count is not None
                    else "—"
                ),
                criterion=_tri_state(case.acceptance_criterion_available),
                scope=_tri_state(case.required_output_scope_complete),
            )
        )
    lines.append("")

    lines.append("### Result files and checksums")
    lines.append("")
    if recorded:
        lines.append("| Case | APS file | SHA-256 |")
        lines.append("|---|---|---|")
        for case in recorded:
            lines.append(
                "| `{}/{}` | `{}` | `{}` |".format(
                    case.variant,
                    case.case_id,
                    os.path.basename(case.aps_path),
                    case.aps_sha256,
                )
            )
    else:
        lines.append(
            "No simulation result is recorded for this test. Nothing may be "
            "submitted until at least one case has a verified model, an "
            "executed simulation and an extracted result."
        )
    lines.append("")

    not_run = [case for case in report.cases if not case.has_recorded_result]
    if not_run:
        lines.append("### Cases without a recorded result")
        lines.append("")
        lines.append(
            "Listed rather than omitted, so the scope of the submission is "
            "unambiguous."
        )
        lines.append("")
        for case in not_run:
            lines.append(
                "- `{}/{}` — model {}, simulation {}".format(
                    case.variant,
                    case.case_id,
                    case.model_status,
                    case.simulation_status,
                )
            )
        lines.append("")

    if report.missing_for_signature:
        lines.append("---")
        lines.append("")
        lines.append("## Outstanding before this report can be signed")
        lines.append("")
        for item in report.missing_for_signature:
            lines.append("- {}".format(item))
        lines.append("")

    lines.append("---")
    lines.append("")
    if report.report_date.strip() and report.author.strip():
        lines.append("{} / {}".format(report.report_date.strip(), report.author.strip()))
    else:
        lines.append(
            "{} date / author — the form is signed by a person, never by the "
            "software.".format(PLACEHOLDER)
        )
    lines.append("")
    lines.append("<sub>Evidence ledger: `{}`</sub>".format(report.ledger_path))
    lines.append("")
    return "\n".join(lines)


def _write_atomic(path: str, content: str) -> None:
    directory = os.path.dirname(path) or "."
    os.makedirs(directory, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=directory,
        prefix=".anwenderbericht-",
        suffix=".tmp",
        delete=False,
        newline="\n",
    ) as handle:
        handle.write(content)
        temporary = handle.name
    os.replace(temporary, path)


def write_anwenderbericht(
    report: Anwenderbericht,
    output_directory: str,
) -> Dict[str, Any]:
    """Write the report plus a machine-readable status record.

    A new timestamp-free filename per test is used deliberately: the report is
    a living document until signed, and a reviewer should see one current file
    rather than a pile of near-identical drafts.
    """

    stem = "Anwenderbericht_Test{}".format(report.test_id)
    markdown_path = os.path.join(output_directory, "{}.md".format(stem))
    status_path = os.path.join(output_directory, "{}.status.json".format(stem))
    _write_atomic(markdown_path, render_markdown(report))
    status = {
        "schema_version": "1.0",
        "test_id": report.test_id,
        "status": report.status,
        "compliance_claim_allowed": False,
        "signed": report.status == STATUS_READY_FOR_REVIEW,
        "missing_for_signature": list(report.missing_for_signature),
        "case_count": len(report.cases),
        "cases_with_recorded_result": sum(
            1 for case in report.cases if case.has_recorded_result
        ),
        "cases": [
            {
                "variant": case.variant,
                "case_id": case.case_id,
                "model_status": case.model_status,
                "simulation_status": case.simulation_status,
                "result_status": case.result_status,
                "aps_sha256": case.aps_sha256,
                "observed_metric_count": case.observed_metric_count,
                "acceptance_criterion_available": (case.acceptance_criterion_available),
            }
            for case in report.cases
        ],
        "ledger_path": report.ledger_path,
        "markdown_path": os.path.abspath(markdown_path),
        "form_note": (
            "Markdown is the reviewable source. Transcribe into the official "
            "SIA Anwenderbericht form before submission; the German section "
            "labels are reproduced verbatim to make that direct."
        ),
    }
    _write_atomic(status_path, json.dumps(status, indent=2, ensure_ascii=False) + "\n")
    return status


__all__ = [
    "STATUS_DRAFT",
    "STATUS_READY_FOR_REVIEW",
    "NO_SPECIAL_ASSUMPTIONS",
    "PLACEHOLDER",
    "AnwenderberichtError",
    "ProgramIdentity",
    "CaseEvidence",
    "Anwenderbericht",
    "load_case_evidence",
    "build_anwenderbericht",
    "render_markdown",
    "write_anwenderbericht",
]
