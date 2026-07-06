# SIA Compliance Execution Tracker

## Purpose

This file is the project control log for the Swiss SIA 380/2 and SIA 4010
workflow. It tracks what is being improved, what has been verified, what is
still blocked, and which evidence is needed before stronger compliance wording
can be used.

The tracker is intentionally conservative. It must help the team move fast
without creating false SIA 4010 validation claims.

## Current Baseline

Latest reviewed workbook:

- `reports/Swiss_Compliance_Report__ZOER_32_C1__-__20260706_145738.xlsx`

Observed status:

- SIA 380/2 automated readiness score: `45.6/100`.
- Model health score: `65.8/100`.
- Rooms analysed: `4`.
- Analysed floor area: `392.5 m2`.
- SIA 4010 evidence families detected: `0/5`.
- APS/Vista status: `AVAILABLE`.
- Selected APS file: `ZOER_C1.aps`.
- Project weather file: `Not exposed by VE`.
- Old weather reference `SMA_2035-RCP85_DRY.epw`: not present in the reviewed
  workbook.
- Workbook charts and drawing XML parts: present.
- Obvious Excel formula errors: none detected.
- Release validation: `245` checks passed, `2` non-blocking warnings.

Current safe wording:

- The tool provides a professional readiness and audit report.
- The tool does not yet provide a final SIA compliance certificate.
- SIA 4010 remains evidence-dependent until official evidence families and
  reviewer acceptance are available.

## Working Method

Each implementation round must have:

- one narrow objective;
- one verified baseline;
- one change set;
- one release-validation run;
- one short decision log entry;
- one explicit next step.

Credit discipline:

- use at most two sub-agents for independent audits unless a new bottleneck
  clearly justifies more;
- keep implementation local when files overlap;
- prefer targeted code changes over broad rewrites;
- avoid re-reading the same PDFs or docs unless the target changed;
- record unresolved items here instead of repeatedly rediscovering them.

## Active Agent Roles

| Agent | Scope | Expected output | Status |
| --- | --- | --- | --- |
| Evidence SIA 4010 | Evidence scanner, templates, report evidence UX | Missing evidence map and MVP fixes | In progress |
| Tests 1-7 / Classes | SIA 4010 test/class implementation | Coverage, blockers and next code priorities | In progress |
| Integrator | Main implementation and release validation | Code/doc changes, QA, next steps | Active |

## Part 1 Objective - Evidence and Official Validation Blockers

Goal:

- turn the current `0/5` SIA 4010 evidence status into an actionable,
  manager-ready workflow;
- make it obvious which files are needed, where to place them, and why they do
  or do not count as official validation evidence;
- keep all tests/classes conservative until official evidence is present.

Acceptance criteria:

- The evidence workflow is documented in one clear handoff location.
- The generated report keeps the `0/5` state visible and actionable.
- Missing official evidence is never treated as `PASS`.
- The project explains what can be done with only the SIA 380/2 and SIA 4010
  PDFs, and what still requires official SIA execution/evaluation files.
- Release validation still passes.

## Part 2 Objective - Highest-Value Model Corrections

Focus after Part 1:

- frame-fraction remediation for `STD_EXTW` and `STD_EXT2`;
- external wall U-value remediation for `STD_EXT1`, `STD_PAR1`, `STD_WAL2`;
- SIA 380/2 justification workflow for retained deviations;
- report wording that clearly separates model remediation from official SIA
  method validation.

## Part 3 Objective - MSP Data Coverage

Focus after Part 2:

- SIA 2024 room/use mapping;
- lighting/SIA 387/4 readiness fields;
- ventilation and AHU controls;
- fan, pump, heat recovery, humidification and generator efficiency evidence;
- APS/Vista output expansion for SIA 4010 tests 4 to 7.

## Decision Log

| Date | Decision | Reason | Verification |
| --- | --- | --- | --- |
| 2026-07-05 | Keep SIA 4010 as readiness/evidence workflow, not certificate wording | Official evidence families are still `0/5` | Latest workbook reviewed |
| 2026-07-05 | Add APS/weather stale-result guardrails | Avoid reopening stale APS files after weather changes | Release validation passed |
| 2026-07-05 | Display `Not exposed by VE` when VE does not expose the project weather file | Avoid blank report cells and manager confusion | Latest workbook reviewed |
| 2026-07-05 | Move `DYNAMIC RESULTS` room table below the full overview block | Prevent the `Notes` row from being overwritten | Latest workbook reviewed |
| 2026-07-05 | Classify SIA 4010 evidence only with documented filename prefixes and accepted extensions | Avoid false positives from generic files such as `validation.xlsx` or `report.pdf` | Release validation passed: 216 checks |
| 2026-07-05 | Parse `SIA4010_evidence_index_<project>.csv` as manifest metadata | Separate file presence from documented source/reviewer/test coverage | Release validation passed: 221 checks |
| 2026-07-06 | Parse `SIA4010_class_validation_<project>.csv` as the target-class manifest | Make the requested SIA 4010 class explicit instead of inferred only from filenames | Release validation passed: 226 checks |
| 2026-07-06 | Parse `SIA4010_official_test_results_<project>.csv` as explicit test outcomes | Allow tests 1-7 to become `VALIDATED` only from reviewer-documented PASS rows | Release validation passed: 234 checks |
| 2026-07-06 | Harden official result validation after sub-agent audit | Require ready evidence pack, complete class manifest, real referenced files and strict test IDs before validation | Release validation passed: 238 checks |
| 2026-07-06 | Generate timestamped evidence-pack ZIP after each successful report | Provide manager/reviewer handoff package without requiring PowerShell | Release validation passed: 241 checks |
| 2026-07-06 | Add Run-button evidence-folder preparation helper | Let VE users initialize reviewer CSV files without PowerShell or manual renaming | Release validation passed: 245 checks |
| 2026-07-06 | Add documentation dependency file and clearer Sphinx preflight | Make manager documentation build setup explicit when Sphinx is missing | Release validation passed: 246 checks |
| 2026-07-06 | Harden evidence-pack ZIP after sub-agent audit | Exclude unsafe/licensed evidence-folder files, write ZIP atomically and avoid fixed release-test filenames | Release validation passed: 246 checks |
| 2026-07-06 | Enforce English-only Python code documentation | Make the codebase maintainable after handover with module/class/function docstrings and English comments checked automatically | Release validation passed: 249 checks |
| 2026-07-06 | Add internal fixture and claim-safety checks while waiting for official Excel files | Keep improving without official workbooks while preventing false `PASS`/`VALIDATED` outcomes | Release validation passed: 262 checks |
| 2026-07-06 | Add surface tilt and adjacency metadata to normalized VE surfaces | Improve envelope traceability and prepare SIA 4010 geometry/readiness diagnostics | Release validation passed: 262 checks |
| 2026-07-06 | Expand APS/Vista optional outputs and add a strict SIA 380/2 gap audit | Improve tests 3-7 readiness while keeping full compliance blockers explicit | Release validation passed: 268 checks |
| 2026-07-06 | Normalize APS CO2 fractions to ppm and prepare the ZOER 32 C1 remediation handoff | Make the latest report blockers actionable while avoiding misleading CO2 units or false evidence acceptance | Release validation passed: 245 checks |

## Open Risks

| Risk | Impact | Current mitigation | Next action |
| --- | --- | --- | --- |
| SIA 4010 official evidence is missing | No official validation claim can be made | Report states `0/5` evidence and blocks validation wording | Improve evidence handoff and scanner UX |
| VE does not expose current weather file through the tested API | APS weather matching can only use APS references when exposed | Report states `Not exposed by VE`; stale APS references are scanned where visible | Document rerun procedure after weather changes |
| Official SIA execution/evaluation package is unavailable | Tests 1-7 cannot become official validation results | PDF-based prevalidation remains clearly labelled as non-official | Keep prevalidation useful but conservative |
| Raw CDB glazing values are misread as EN 410 g_perp | False SIA 380/2 opening pass could be claimed | Claim-safety fixtures and report helpers now block this interpretation | Keep collecting EN 410/manufacturer evidence |
| Some SIA 380/2 values require reviewer justification | Readiness score remains low until fixed or justified | `SIA3802 JUSTIFICATIONS` workflow exists | Provide filled justification evidence where appropriate |
| SIA 380/2 delegated inputs are not fully available in VE | A complete compliance claim could be overstated | `SIA3802_FULL_COMPLIANCE_GAP_AUDIT.md` separates automated checks from gaps | Collect SIA 2024, schedules, AHU, EER/SEER, SCOP and final-energy evidence |
| Sphinx is missing from the available Python runtime | HTML documentation could not be rebuilt in this pass | Sphinx source pages and release checks were updated successfully | Install `docs/requirements-docs.txt` before the next manager-facing HTML build |
| ZOER 32 C1 still contains model-level P1 blockers | Readiness score remains low even if the reporting workflow is robust | A dedicated remediation action pack and draft evidence CSV files are prepared | Correct VE/CDB values or complete reviewer justifications, then rerun VE scripts |

## Next Implementation Candidates

| Priority | Candidate | Expected benefit | Risk |
| --- | --- | --- | --- |
| P1 | Evidence folder handoff manifest and examples | Helps move from `0/5` to actionable evidence collection | Low |
| P1 | Report sheet or docs explaining exact file-name prefixes counted by scanner | Reduces confusion for manager/client handoff | Implemented in code; verify on next VE Run |
| P1 | Stronger validation of evidence files before counting them | Avoids false positives from placeholder files | Implemented in code; verify on next VE Run |
| P2 | Import reviewer-filled SIA 4010 evidence manifest CSV | Distinguishes detected files from documented evidence | Implemented in code; verify on next VE Run |
| P2 | Import reviewer-filled SIA 4010 class tracker CSV | Makes class selection explicit in reports | Implemented in code; verify on next VE Run |
| P2 | Import reviewer-filled SIA 4010 official test-result CSV | Separates `READY_FOR_OFFICIAL_REVIEW`, `VALIDATED` and `FAIL` for tests 1-7 | Implemented in code; verify on next VE Run |
| P2 | Expand APS/Vista dynamic output extraction for tests 3-7 | Improves MSP readiness | Implemented for optional lighting, fans, pumps, auxiliaries, coils, CO2 and humidity; verify on next VE Run |
| P2 | Expand HVAC/AHU extraction for airflow, fans, pumps, heat recovery and humidification | Improves SIA 380/2 and SIA 4010 tests 4-7 readiness | Medium |
| P3 | Export zipped evidence pack | Better client delivery package | Implemented in code; verify on next VE Run |
| P1 | Verify ZOER 32 C1 after the next VE model edit | Confirms that the action pack closes real blockers rather than only documenting them | Requires a regenerated report and probe |
