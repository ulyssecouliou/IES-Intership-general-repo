# Clean Code Baseline

Status: active from 2026-08-25.

## Enforced quality gates

All tracked Python in `core/`, `engine/`, `schemas/`, `swiss_sia/`, `ui/`,
`scripts/`, `tests/`, `ve_adapter/` and `examples/` is formatted by Black with
a 90-character target. Flake8 blocks functional and style defects that are not
handled by Black. The local pre-commit configuration and the Ubuntu CI workflow
apply the same rules.

Flake8 intentionally ignores E501 because Black does not split long strings or
comments. It also ignores E203 and W503, which conflict with Black's formatting.
The two E402 exceptions cover bootstrap modules that must alter the runtime
environment before importing the application.

Mypy remains strict for `core/` and `schemas/`. The progressive strict boundary
currently also covers:

- `swiss_sia.client_report_context`
- `swiss_sia.assessment_governance`
- `swiss_sia.project_evidence_translations`
- `swiss_sia.value_integrity`

Add a `swiss_sia` module to this list only after it passes strict mypy without
suppression.

## Current debt baseline

The initial cleanup removed all reported F-class Flake8 defects, including
undefined Python 2 names, unused imports and variables, and a duplicate Excel
helper. Black reformatted 349 files. The report evidence formatter was split
into focused helpers; its McCabe complexity fell from 41 to below 20.

The remaining historical debt is measured, not hidden:

- 134 functions exceed McCabe complexity 10.
- 392 broad `except Exception` handlers remain across the complete product,
  engine, adapter and script scope.
- the largest modules (`excel_report.py`, `native_ui.py`, `ui_translations.py`,
  `ve_asset_provisioner.py`, `ve_api.py`) still require staged extraction.

These figures are a migration baseline, not an accepted end state. Complexity
is not yet a blocking Flake8 rule because enabling C901 globally would make the
quality gate permanently red. New work should not add to either count.

## Refactoring order

Use this order to reduce risk while improving the client workflow:

1. split `_coverage_status_for_key` into domain-specific coverage evaluators;
2. extract the client report sheets from `excel_report.py`;
3. split UI construction from controller actions in `native_ui.py` and `app.py`;
4. replace broad exceptions at I/O and VE API boundaries with explicit exception
   families while retaining an auditable final safety boundary;
5. add each stabilized module to the strict mypy boundary;
6. lower the permitted complexity baseline until C901 can become blocking.

## Product, diagnostics and history

- `swiss_sia/`, `core/`, `engine/`, `ui/` and `ve_adapter/` are product code.
- `scripts/probes/` contains read-only runtime diagnostics.
- `scripts/quality/` contains delivery and release checks.
- `scripts/legacy/` is historical and must not be imported by product code.
- generated reports and runtime receipts belong in project-local output folders,
  never as source modules or hard-coded workstation paths.

The legacy folder is retained only when a file still provides traceability or a
documented recovery path. Obsolete duplicate launchers and ad-hoc inspection
scripts should be removed rather than kept as alternative product entry points.

## Verification note

The complete local collection reached 2,423 passing and 3 skipped tests. Tests
that create temporary directories cannot complete on the current Windows host
because its Python temporary directories are denied by local ACLs. The CI runs
the same suite on Ubuntu and is the authoritative full-suite check. Targeted
client UI, translation, Excel/PDF report, portability and source-contract tests
pass locally after this cleanup.
