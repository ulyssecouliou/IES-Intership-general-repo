# CLAUDE Reference — layout, workflow, commands, conventions

Companion to `CLAUDE.md`. `CLAUDE.md` carries the non-negotiable doctrine and is
loaded every turn; this file is reference detail, read on demand. Nothing here
is optional — it is exactly as binding as `CLAUDE.md`, just not re-loaded
automatically for token-cost reasons.

## Layout

> **Which architecture is live (verified 2026-08-16, see `docs/project/AUDIT_COMPLET_2026-08-16.md`).**
> The production client tool is entirely in `swiss_sia/` (100% of client entry
> points). The top-level `engine/` + `ve_adapter/` + `ui/` triptych below is NOT
> the client runtime: `engine/`+`ve_adapter/` are the independent reference-data
> build & cross-check toolchain, `ui/` is legacy (only `ui/design.py` +
> `ui/tk_theme.py` style tokens are still imported by `swiss_sia`), and `core/`
> is dead. ADR-001 (D2) removed the web UI in favour of the in-VE Tkinter dialog.

- `Run_VE_Swiss_Compliance.py` — production compliance-checker Run-button launcher.
- `Run_VE_Swiss_Reference_Model.py` — programmatic reference-model Run-button launcher.
- `swiss_sia/` — compliance extraction, rules, reports, evidence, orchestration.
- `swiss_sia/reference_model/` — config, geometry, gbXML, VE gateways, asset provisioning, validation, reporting, SIA 4010 hooks.
- `config/` — source-traced example inputs; examples intentionally fail closed until completed.
- `schemas/` — machine-readable configuration contracts.
- `engine/` — **tooling, not client runtime.** Independent SIA 4010 recompute + reference-data build logic (pure Python, no `iesve`, CI-testable). Consumed by `scripts/build_*.py` to regenerate `refs/reference-data/` and by its own tests as a cross-check; not imported by `swiss_sia`. Keep; do not wire into the client path without an ADR.
- `ve_adapter/` — **legacy Test 1/7 VE adapter** (gbXML, geometry, APS) feeding the `engine/` recompute via `scripts/`. NOTE: this is NOT the only place `iesve` is accessed — production VE access is `swiss_sia/reference_model/ve_api.py` + the `swiss_sia/data_extractor.py` boundary.
- `ui/` — **legacy parallel UI/exports.** The live Tkinter navigator, Excel workbook and PDF exports are in `swiss_sia/` (`*_ui.py`, `excel_report.py`, `compliance_report_pdf.py`); only `ui/design.py` + `ui/tk_theme.py` (style tokens) are still used. The live translation table is `swiss_sia/reference_model/sia4010/ui_translations.py`; `ui/i18n.py` is a legacy copy.
- `refs/reference-data/` — frozen reference values, recomputed and checked against source before being written. Edits blocked by `.claude/hooks/garde_refs.py`; fix the extractor that produces the file, never the output file itself.
- `traceability/` — clause -> code -> test matrices, signed by an independent audit (`qa-auditor`).
- `tests/` — pure-Python regression and API-double tests.
- `scripts/quality/validate_release.py` — repository release gate.
- `docs/project/` — architecture, status, risks, handoff records.
- `references/` — local authoritative/reference material; access subject to IES policy (see Data handling below).
- `reports/`, `outputs/`, `sia4010_evidence/` — generated or reviewer-owned artifacts, not source-code scratch space.

## Change workflow

1. Read `README.md` and only the architecture/status documents relevant to the task.
2. Inspect `git status --short`; distinguish task changes from pre-existing user changes.
3. Identify the compliance claim, API contract, input source and validation impact before editing.
4. Implement the smallest cohesive change through existing interfaces. Avoid parallel implementations and hard-coded paths.
5. Add or update focused tests, including failure and placeholder paths.
6. Run focused tests, then the full suite when shared code changes.
7. Run release validation (`scripts/quality/validate_release.py`) for compliance, report, evidence, configuration or documentation changes.
8. Report what was verified locally and what still requires a real IESVE run or expert-review gate.

## Commands

From the repository root, Windows:

```powershell
python -m unittest discover -s tests -p "test_*.py"
python -m unittest discover -s tests -p "test_reference_model*.py"
python scripts/reference_model_dry_run.py config/reference_model.example.json
python scripts/quality/validate_release.py
python -m compileall -q swiss_sia scripts Run_VE_Swiss_Compliance.py Run_VE_Swiss_Reference_Model.py
git diff --check
git status --short
```

If release validation reports `pypdf` missing, use the approved project
environment or request approval before installing `scripts/quality/requirements.txt`.

## Coding conventions

- Preserve compatibility with the confirmed IESVE Python runtime; do not introduce newer syntax or dependencies without verifying that runtime.
- Prefer typed boundaries, dataclasses for structured records, dependency injection for VE access, explicit exceptions, logging, deterministic outputs.
- Keep compliance configuration separate from geometry, VE mutation, validation and reporting.
- Use atomic writes for audit artifacts where practical.
- Add descriptive docstrings to public and internal modules, classes and functions covered by release checks.
- (Language rule for identifiers/comments/docstrings themselves is in `CLAUDE.md` — Style.)

## Definition of done

A change is done only when: its scoped tests pass; failure paths are
conservative; source traceability remains intact; generated artifacts are not
misrepresented as certification; documentation is updated when the workflow
changes; and remaining real-VE or regulatory-review work is stated explicitly.

## Data handling detail

- Before reading licensed standards or customer files with Claude Code, confirm IES policy authorizes those files for the configured enterprise service. Never reproduce long copyrighted extracts.
- Every compliance-relevant value belongs in a source-traced configuration or manifest record carrying: units, source, locator, validation range, and placeholder state — not just a bare number.

## VE API verification detail

- Do not assume an IESVE API member exists because it appears in another release. Check the local manual under `references/iesve/`, probe the installed runtime read-only, or consult current official IESVE documentation.
- VE model creation starts from an already-open and saved blank VE project, unless a documented project-creation API has been verified.

## What the frozen reference data guarantees

Every file under `refs/reference-data/` is produced by a script in `scripts/`
that extracts, recomputes, and confronts the values against the official
source before writing. The `.claude/hooks/garde_refs.py` hook blocks any
direct write under `refs/`: hand-editing one would break that chain of proof
without anything signalling it.

## Two facts that trap everyone (expanded)

- **Only Test 1 states its acceptance criteria.** For every other test the
  specification is silent; SIA 4010 clause 4.4 delegates the comparison to
  the evaluation workbook. Those criteria are marked `INFERE` wherever a
  verdict is produced, and must be confirmed by the sub-commission (4.6.2).
- **The test climate is not the application climate.** The seven test
  specifications require `SIA 2028 DRY normal, Zuerich Kloten`. SIA 4010
  clause 3.1.1 prescribes CH2018 RCP 8.5 "2035" — but for *applying* SIA
  380/2 in a real project, not for the validation tests. Both live in the
  same documents; do not conflate them.
