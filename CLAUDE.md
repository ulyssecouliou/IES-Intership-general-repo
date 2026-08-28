# SIA Compliance / SIA 4010 Navigator

Mission: IESVE/VEScripts SIA 380/2 readiness + SIA 4010 validation. Evidence, not certification. Full reference: `docs/CLAUDE_REFERENCE.md` (layout, workflow, commands, conventions, data-handling detail).

Current Codex handoff (read when resuming this project): `docs/project/CODEX_TO_CLAUDE_HANDOFF.md`. Copy-ready continuation prompt: `docs/project/archive/CLAUDE_CONTINUATION_PROMPT.md`.

## Absolute rules
- Never invent/infer/default any regulatory, physical, climatic, occupancy, HVAC, glazing, construction value/tolerance, or unverified API member/signature. Truth = published SIA/ASHRAE140/EN sources only.
- Cite exact article per check/value: `# SIA 380/2:2022 5.2.2`. Unclear/missing -> `[TO VERIFY]`, never guessed.
- Verdicts `NOT_CHECKABLE`/`WARNING`/`FAIL`; missing evidence never becomes `PASS`. No SIA 4010 validation claim without test package + evidence + class + reviewer sign-off.
- Pure/hard separation: analysis, rules, scoring, reporting stay `iesve`-free and CI-testable via gateways/fakes/fixtures/dry-runs; real VE access isolated behind an injected handle. **Production lives in `swiss_sia/`** (VE access confined to `reference_model/ve_api.py` + the `data_extractor` boundary). Top-level `engine/`+`ve_adapter/` are the **independent reference-data build & cross-check toolchain** (they regenerate `refs/reference-data/` and recompute verdicts independently), NOT the client runtime; `core/` is dead. See `docs/CLAUDE_REFERENCE.md` §Layout and `docs/project/AUDIT_COMPLET_2026-08-16.md`.
- Nothing "done" without traceability matrix signed by independent `qa-auditor`.
- User files = owned data, preserve. No publish/push/PR/upload/install/external contact without explicit user OK. No destructive git/fs; preserve unrelated dirty-worktree changes.
- `iesve` only inside VEScripts. Capability-check + readback around every VE mutation. Simulated-API test != real-VE qualification -- say so.

## SIA 4010 specifics
Only Test 1 states its own criteria; others `INFERE` (4.4 delegates to workbook), pending sub-commission (4.6.2). Test climate (SIA 2028 DRY normal, Zuerich Kloten) != application climate (CH2018 RCP8.5 "2035", 3.1.1).
Loop: `norm-analyst` -> `reference-data-engineer` -> `validation-engine-engineer` -> `ve-adapter-engineer` -> `ui-engineer` -> `qa-auditor` -> `docs-writer`. Skills `/figer-reference`, `/etat-classes`.

## Style
Code: English, whole module per pass, no compat shims for renamed names -- update callers same commit. UI/reports: bilingual, live translation table in `swiss_sia/reference_model/sia4010/ui_translations.py` (`ui/i18n.py` is a legacy parallel copy); a missing key must surface, never silently blank. Docs (`docs/`, `traceability/`, `AUDIT.md`, `PROJECT_PLAN.md`) French. German SIA-workbook keys verbatim.

## Model routing
- **Opus 4.7 (xhigh effort)**: normative analysis, architectural decisions, code review, ambiguous norm interpretation.
- **Sonnet 4.6 (high effort)**: implementation (engine, adapters, UI, tests, refactors).
- **max effort**: only when genuinely blocked, or for final QA review pre-signature.
- **Haiku**: only for mechanical, non-normative tasks (reformatting, bulk renames, plain ref extraction).

## Hygiene
`/clear` between unrelated tasks | `/compact` past ~1h | read targeted line ranges | commit after each finished task | read source PDFs under `refs/` on demand rather than in bulk.
