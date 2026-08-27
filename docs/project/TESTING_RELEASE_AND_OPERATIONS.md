# Testing, release and operations

## Quality gates

Run all pure-Python gates outside IESVE from the repository root:

```powershell
python -m pytest -q
python -m black --check --line-length 90 core engine schemas swiss_sia ui scripts tests ve_adapter
python -m flake8 swiss_sia ui scripts core schemas engine ve_adapter tests --jobs 1 --config .flake8
python -m mypy --strict --show-error-codes core schemas
python -m mypy --strict --show-error-codes --exclude '^$' swiss_sia/assessment_governance.py swiss_sia/client_report_context.py swiss_sia/project_evidence_translations.py swiss_sia/value_integrity.py
python scripts/quality/validate_release.py
```

The release validator complements pytest; it does not replace it. It checks
normative source presence/markers, configuration traceability, claim-safety
guardrails, documentation, latest workbook structure and matrix signatures.

## Documentation build

Build each supported language when documentation dependencies are available:

```powershell
python docs/tools/build_docs.py --language en --builder html
python docs/tools/build_docs.py --language fr --builder html
python docs/tools/build_docs.py --language de --builder html
python docs/tools/build_docs.py --language it --builder html
```

English is the baseline. A successful build is not enough: open each index and
sample pages to check encoding, links, tables and untranslated/raw keys.

## Source delivery package

Build the bounded MVP ZIP and SHA-256 manifest with:

```powershell
python scripts/quality/build_mvp_delivery.py
```

The ZIP intentionally excludes client evidence, reports, licensed standards,
local company configuration, test outputs and Git metadata. It is a software
delivery convenience, not a complete legal/evidence archive. The canonical full
handover remains Git `main` plus separately governed project/model evidence.

Record the ZIP checksum before copying it:

```powershell
Get-FileHash outputs/release/Swiss_SIA_Compliance_MVP_*.zip -Algorithm SHA256
```

## IESVE smoke test

The following steps require a licensed IESVE 2025 session and cannot be replaced
by CI:

1. Open a known disposable/reference project.
2. Run `Run_VE_Swiss_Compliance.py`.
3. Verify the main interface, model-view capture return and evidence-wizard
   return-to-front behaviour.
4. Switch EN -> FR -> DE -> IT -> EN and inspect accents/labels.
5. Generate PDF and XLSX reports.
6. Open both files and inspect the cover, navigation, headers/footers, verdict
   wording, tables and page breaks.
7. Confirm incomplete evidence remains pending/not-checkable.
8. Confirm output paths are derived from the active project.
9. Run one safe read-only probe and preserve its JSON receipt.

For SIA 4010, use an exact disposable case and the dedicated guarded launcher.
Do not use a client model or claim official pass from a diagnostic equivalent.

## Expected warnings and skips

At final handover the configured full pytest suite passed with four skips.
Openpyxl emitted non-blocking warnings about unsupported Data Validation
extensions. Restricted Windows sandboxes may create false `PermissionError`
failures for temporary folders; re-run with a normal accessible `%TEMP%`.

Any new skip must state why it cannot run and what external/runtime evidence is
needed. Never hide a failing normative assertion by skipping it.

## Release procedure

1. Start from a clean, updated `main` or a review branch based on it.
2. Review `git status`, staged paths and binary/data implications.
3. Run all pure-Python quality gates.
4. Run the IESVE smoke test for VE-facing changes.
5. Build and visually inspect documentation/reports.
6. Update the handover/status/blocker documents.
7. Commit one coherent change and obtain IES review.
8. Fast-forward/merge to `main` according to repository policy.
9. Push and verify local HEAD equals `origin/main` and the remote reference.
10. Create an annotated handover/release tag.
11. Build the bounded ZIP and record its SHA-256.
12. Check GitHub Actions and retain a link/screenshot or run identifier.
13. Publish only after licensing/privacy/security gates are satisfied.

## Git verification commands

```powershell
git fetch origin
git status --short --branch
git rev-parse HEAD
git rev-parse origin/main
git branch --no-merged main
git branch -r --no-merged main
git fsck --full
```

`git fsck` may report dangling blobs/trees from previous index operations. They
are normal recoverable unreachable objects unless the command also reports
missing or corrupt objects.

## Rollback and incident handling

- Do not use `git reset --hard` on a shared or dirty worktree.
- Preserve evidence and create a corrective commit where possible.
- If a release is wrong, document the affected commit/tag/report and why.
- Never amend a runtime receipt cited externally; issue a new run.
- If confidential/licensed content is published, restrict repository access,
  notify the IES owner/security/legal contact and plan a coordinated history
  purge. Deleting only the latest file is insufficient.
- If a compliance claim is wrong, notify recipients and issue a corrected report
  with explicit supersession wording.

## Operational ownership

Repository ownership, branch protection, Actions and release approval belong to
IES. Client evidence approval belongs to the named reviewer. Official SIA 4010
acceptance belongs to the SIA authority. The application and an AI assistant do
not own any of these decisions.
