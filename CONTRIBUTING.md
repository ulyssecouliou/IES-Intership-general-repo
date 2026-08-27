# Contributing

This project supports IESVE technical assessment and SIA validation evidence.
Changes can affect professional reports and must remain evidence-led.

## Before changing code

1. Read `docs/project/HANDOVER_2026-08-28.md` and
   `docs/project/NEW_MAINTAINER_START_HERE.md`.
2. Start from current `main` with a clean worktree.
3. Use a bounded task branch unless the repository owner explicitly directs a
   controlled handover commit on `main`.
4. Identify the source, expected behaviour and acceptance test.

## Pull requests

- Keep one coherent purpose per pull request.
- Explain normative sources, VE runtime assumptions and claim impact.
- Add regression tests for defects and boundary/missing-evidence tests for new
  criteria.
- Include VE capability/read-back receipts when native state is changed.
- Update translations and all affected report formats.
- Do not include client models, APS files, credentials or unlicensed sources.
- Do not claim certification or convert missing evidence into pass.

## Required local checks

Follow `docs/project/TESTING_RELEASE_AND_OPERATIONS.md`. At minimum run pytest,
Black check, Flake8, the selected strict MyPy gates and the release validator.
VE-facing changes additionally require a disposable IESVE 2025 smoke/read-back
test.

## Reference data

Never hand-edit frozen files under `refs/reference-data/`. Correct the authorised
source binding/extractor, regenerate the output and retain provenance/checksums.

## Data and AI

Follow `docs/project/DATA_EVIDENCE_AND_LICENSING.md` and
`docs/project/AI_USAGE_AND_GOVERNANCE.md`. AI assistance does not remove the
author's obligation to review code, sources, tests, privacy and claims.

## Review authority

IES maintainers approve software changes. Named project reviewers accept client
evidence. Only the relevant SIA authority can grant official validation. A pull
request approval is not a certification decision.
