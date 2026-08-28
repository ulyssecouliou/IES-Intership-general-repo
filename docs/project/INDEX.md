# `docs/project/` index

> This directory contains current operating documentation and dated historical
> records accumulated during development. Use this index to distinguish the
> canonical English handover from background material that may now be stale.

## Start here — current and canonical

| Document | Purpose |
|---|---|
| `FINAL_TRANSMISSION_RECEIPT_2026-08-28.md` | **Canonical delivery state, reproducible checks, retained warnings and generated deliverables** |
| `NEW_MAINTAINER_START_HERE.md` | **First 30 minutes, workstation setup, commands, ownership and safe contribution rules** |
| `AUTHORITY_RESPONSE_2026-08-28.md` | **Latest Prof. Zweifel response, supplied SIA 2024 workbook and implementation consequences** |
| `SIA4010_TESTS_1_7_STATUS_2026-08-28.md` | **Actionable state, blockers and next executable work for every SIA 4010 test** |
| `TRANSMISSION_CHECKLIST_2026-08-28.md` | **IES handover checklist covering automation, ownership, VE, SIA and restricted data** |
| `AI_USAGE_AND_GOVERNANCE.md` | **Actual AI use, no AI runtime dependency, limits and required human supervision** |
| `ENGLISH_DEFAULT_AND_LANGUAGE_SUPPORT.md` | **English-default contract, four maintained UI languages and VE verification steps** |
| `ARCHITECTURE_AND_RUNTIME_GUIDE.md` | **Maintained architecture, client/SIA 4010 workflows and extension rules** |
| `DATA_EVIDENCE_AND_LICENSING.md` | **Data, evidence, correspondence, privacy, licensing and publication restrictions** |
| `INTERNAL_DATASET_INVENTORY.md` | **Versioned private datasets and intentionally excluded regenerable material** |
| `TESTING_RELEASE_AND_OPERATIONS.md` | **Tests, documentation builds, client package, VE smoke testing, release and rollback** |
| `GITHUB_AND_OWNERSHIP_TRANSFER.md` | **Repository access, IES ownership transfer, Actions, branch protection and visibility** |
| `../../CLAUDE.md` | Non-negotiable repository doctrine loaded for each development session |
| `../CLAUDE_REFERENCE.md` | Repository layout, workflow and coding conventions |
| `../ADR-001-architecture-MSP.md` | Architecture decision record for the single-process VE/Tkinter design |
| `CLIENT_RUN_GUIDE.md` / `CLIENT_DEMO_RUNBOOK_EN.md` | Client execution and demonstration workflow |

The production client application lives entirely in `swiss_sia/`.
`engine/` and `ve_adapter/` are independent reference-build and recomputation
tooling. `ui/` provides inherited style modules (`design.py`, `tk_theme.py`);
legacy export duplicates were removed. `core/` was deleted (confirmed dead,
August 2026 audit).

## Maintained thematic guides

- `GUIDE_MODIFICATIONS_VE.md` / `GUIDE_MODIFICATIONS_VE_EN.md`: VE model
  modifications to achieve SIA 380/2 compliance.
- `GUIDE_COMPARAISON_GLOBALE_SIA3802.md` / `GUIDE_GLOBAL_COMPARISON_SIA3802_EN.md`:
  the decisive SIA 380/2 global-comparison gate.
- `SIA3802_CLIENT_TEMPLATE_REMEDIATION_EN.md`: client template remediation.
- `SIA_MODEL_BUILDER_GUIDE.md` / `SIA_MODEL_BUILDER_GUIDE_EN.md`: SIA-compatible
  model creation.
- `RELEASE_ACCEPTANCE_CHECKLIST.md`: release review checklist.
- `REVIEW_GOVERNANCE_SIA.md`: reviewer identity, evidence ownership and legal
  claim boundary.
- `SIA_WIZARD_VALUES_DIRECTION_DEMO.md`: wizard-values direction demonstration.

## Historical and source-language records

The following files are retained for chronology or evidential continuity and
are not the current delivery truth:

- `HANDOVER_2026-08-28.md`: dated French handover, superseded as the default by
  the English final receipt and Test 1–7 status;
- `AUDIT_COMPLET_2026-08-16.md`: dated French audit;
- `SIA_CORRESPONDANCE_ZWEIFEL_2026-08-12.md`: correspondence record containing
  source-language material;
- `MVP_COMPLETION_MATRIX.md`: dated completion matrix (snapshot).

Older dated snapshots, one-time runbooks and obsolete documents have been moved
to `archive/`. French or German normative quotations are preserved when they
are evidence. They must not be silently translated and treated as authoritative
replacements. For current work, always follow the canonical English documents
listed first.
