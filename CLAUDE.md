# Swiss SIA Compliance Checker - Claude Code Instructions

## Mission

Develop a production-quality IESVE/VEScripts workflow for conservative Swiss SIA 380/2 readiness assessment and future SIA 4010 validation. The software produces auditable evidence and readiness results; it does not issue certification.

## Non-negotiable guardrails

- Never invent, infer, or silently default a regulatory, physical, climatic, occupancy, ventilation, HVAC, glazing, or construction value.
- Keep every compliance-relevant value in a source-traced configuration or manifest record with units, source, locator, validation range, and placeholder state.
- Report unavailable official evidence as `NOT_CHECKABLE`, `WARNING`, or `FAIL` as defined by the current architecture. Never convert missing evidence into `PASS`.
- Do not claim SIA 4010 validation without the official test package, accepted result evidence, selected class, and reviewer confirmation.
- Treat project reports, evidence CSV files, standards, customer models, and manager documents as user-owned data. Preserve them unless the task explicitly authorizes changes.
- Before reading licensed standards or customer files with Claude Code, confirm that IES policy authorizes those files for the configured enterprise service. Never reproduce long copyrighted extracts.
- Do not publish, push, create a PR, upload files, install dependencies, or contact external systems unless the user explicitly authorizes that action.
- Do not use destructive Git or filesystem commands. Preserve unrelated changes in a dirty worktree.

## Runtime boundary

- The `iesve` module is available only inside the IESVE VEScripts runtime. Normal Python tests must use gateways, fakes, fixtures, or pure-Python dry runs.
- Do not assume an IESVE API member exists because it appears in another release. Check the local manual under `references/iesve/`, the installed runtime with a read-only probe, or current official IESVE documentation.
- Keep capability checks before VE mutation. Validate every created object by immediate readback.
- A simulated API test is not a real-VE qualification. State this boundary in every relevant handoff.
- VE model creation starts from an already open and saved blank VE project unless a documented project-creation API is verified.

## Architecture map

- `Run_VE_Swiss_Compliance.py`: production compliance-checker Run-button launcher.
- `Run_VE_Swiss_Reference_Model.py`: programmatic reference-model Run-button launcher.
- `swiss_sia/`: compliance extraction, rules, reports, evidence and orchestration.
- `swiss_sia/reference_model/`: configuration, geometry, gbXML, VE gateways, asset provisioning, validation, reporting and SIA 4010 hooks.
- `config/`: source-traced example inputs; examples intentionally fail closed until completed.
- `schemas/`: machine-readable configuration contracts.
- `engine/`: SIA 4010 validation engines. PURE Python, no `iesve`, CI-testable.
- `ve_adapter/`: IESVE extraction into normalised JSON. All `iesve` access lives here.
- `ui/`: Tkinter navigator inside VE, plus Excel (official SIA workbook) and PDF exports.
- `refs/reference-data/`: frozen reference values, recomputed and checked against source.
- `traceability/`: clause -> code -> test matrices, signed by an independent audit.
- `tests/`: pure-Python regression and API-double tests.
- `scripts/quality/validate_release.py`: repository release gate.
- `docs/project/`: architecture, status, risks and handoff records.
- `references/`: local authoritative/reference material; access remains subject to IES policy.
- `reports/`, `outputs/`, `sia4010_evidence/`: generated or reviewer-owned artifacts, not source-code scratch space.

## Change workflow

1. Read `README.md` and only the architecture/status documents relevant to the task.
2. Inspect `git status --short`; distinguish task changes from pre-existing user changes.
3. Identify the compliance claim, API contract, input source and validation impact before editing.
4. Implement the smallest cohesive change through existing interfaces. Avoid parallel implementations and hard-coded paths.
5. Add or update focused tests, including failure and placeholder paths.
6. Run focused tests, then the full suite when shared code changes.
7. Run release validation for compliance, report, evidence, configuration or documentation changes.
8. Report what was verified locally and what still requires a real IESVE or expert-review gate.

## Commands

From the repository root on Windows:

```powershell
python -m unittest discover -s tests -p "test_*.py"
python -m unittest discover -s tests -p "test_reference_model*.py"
python scripts/reference_model_dry_run.py config/reference_model.example.json
python scripts/quality/validate_release.py
python -m compileall -q swiss_sia scripts Run_VE_Swiss_Compliance.py Run_VE_Swiss_Reference_Model.py
git diff --check
git status --short
```

If release validation reports that `pypdf` is missing, use the approved project environment or request approval before installing `scripts/quality/requirements.txt`.

## Coding conventions

- Use English for code, identifiers, comments, docstrings and committed technical documentation. User-facing explanations may be French.
- Preserve compatibility with the confirmed IESVE Python runtime; do not introduce newer syntax or dependencies without verifying that runtime.
- Prefer typed boundaries, dataclasses for structured records, dependency injection for VE access, explicit exceptions, logging and deterministic outputs.
- Keep compliance configuration separate from geometry, VE mutation, validation and reporting.
- Use atomic writes for audit artifacts where practical.
- Add descriptive docstrings to public and internal modules, classes and functions covered by release checks.

## Definition of done

A change is done only when its scoped tests pass, failure paths are conservative, source traceability remains intact, generated artifacts are not misrepresented as certification, documentation is updated when the workflow changes, and remaining real-VE or regulatory-review work is explicit.

## SIA 4010 validation navigator

Merged in on 2026-08-06 from its own repository, with its history. This is the
MVP deliverable: **reports on the validation classes**. The compliant-model
builder (`Run_VE_Swiss_Reference_Model.py`) is a bonus, not part of the MVP.

### What the reference data guarantees

Every file under `refs/reference-data/` is produced by a script in `scripts/`
that extracts, **recomputes and confronts** the values against the official
source before writing. A `.claude/hooks/garde_refs.py` hook blocks any direct
write under `refs/`: editing one by hand would break that chain of proof
without anything signalling it. Fix the extractor, never its output.

### Two facts that trap everyone

- **Only Test 1 states its acceptance criteria.** For every other test the
  specification is silent; SIA 4010 clause 4.4 delegates the comparison to the
  evaluation workbook. Those criteria are therefore marked `INFERE` wherever a
  verdict is produced, and must be confirmed by the sub-commission (4.6.2).
- **The test climate is not the application climate.** The seven test
  specifications require `SIA 2028 DRY normal, Zuerich Kloten`. SIA 4010
  clause 3.1.1 prescribes CH2018 RCP 8.5 "2035" — but for *applying* SIA 380/2
  in a real project, not for the validation tests. Both live in the same
  documents.

### Per-test working loop

`norm-analyst` -> `reference-data-engineer` -> `validation-engine-engineer` ->
`ve-adapter-engineer` -> `ui-engineer` -> `qa-auditor` -> `docs-writer`.
Nothing is "done" without a traceability matrix signed by `qa-auditor`.
The `/figer-reference` skill encodes the reference-freezing procedure, with the
three traps of the SIA workbooks; `/etat-classes` reports class status.

### Style

**Code is English.** Identifiers, comments, docstrings, commit messages, test
names, log lines -- all English. This changed on 2026-08-10 by the owner's
decision: the previous rule was French comments, and the repository is being
converted pass by pass. Two consequences that matter while the conversion is
in flight:

* a module you touch gets converted whole, not line by line. Half-translated
  files are the ones nobody can read;
* renaming a public name means updating its callers in the same commit, with
  the suite green. A shim that keeps the old French name alive "for now" is
  how a codebase stays bilingual for years.

**User-facing text is bilingual, French by default.** Every label shown in the
dialog or printed in a report goes through `ui/i18n.py` -- never a literal in a
widget. French is the default because the tool serves Swiss practice; English
exists because the rest of IES works in English. A missing translation is
loud, never silent: see `i18n.translate`.

**Documentation stays French** (`docs/`, `traceability/`, `AUDIT.md`,
`PROJECT_PLAN.md`). It is read by the same people who read the SIA standards.

**German only** for labels that serve as lookup keys against the official SIA
workbooks -- there it must be verbatim, or the match breaks. Never translate
one of those, not even in a comment that quotes it.

