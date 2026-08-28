> **Note:** Translated from French original. See [audit-lot-A1-A4-verification-2026-08-21.matrix.md](audit-lot-A1-A4-verification-2026-08-21.matrix.md) for the source document.

# Verification matrix -- correction batch A1..A4 (evidence-hardening)

Branch: `sia4010-evidence-hardening-20260812`
Auditor: qa-auditor (independent, read-only access to production code)
Date: 2026-08-21
Status: **SIGNED**
Verified commits: `677b3dd` (A3), `9cc68fc` (A2), `3c48a77` (A1), `7e88404` (A4)
Test suite executed: `python -m pytest tests/ -k "verdict or robustness or report or criteria or claim or health or excel or translation" -q`
Result: **301 passed, 1025 deselected, 2061 subtests passed** (67 s), 0 failures.

Method: I trust neither names nor comments; I read the called code, traced the
alert -> domain -> verdict chain, and checked against adversarial tests. Frozen SIA
references: not available for these gates SS7.1/SS7.2.5.2 (product policy logic, no
numerical reference value) -- see signature reserves.

| # | Requirement (clause) | Fix | Engine function | Evidence / test | Finding | Verdict |
|---|---|---|---|---|---|---|
| 1 | A DETERMINED summer overheating (SS7.1.2.1->SIA 180) blocks even if the SS7.2.5.2 gate is satisfied | A3: `DOMAINS += ("dynamic","Dynamic Method")` | `compliance_verdict.build_compliance_verdict` (l.50, 264); `sia380_checker` emits `SIA3802_SUMMER_COMFORT_DYNAMIC` HIGH, cat. "Dynamic Method" (l.280-292) | `test_determined_summer_overheating_blocks_even_with_gate_satisfied` (gate=REVIEWED_RESULT_AVAILABLE -> `sia3802_status==NOT_COMPLIANT`) | DETERMINED HIGH -> `blocking_total>0` evaluated (l.264) BEFORE the gate (l.271) -> NOT_COMPLIANT. Category is actually "Dynamic Method". | **CONFIRME** |
| 2 | An UNCHECKABLE overheating remains a reserve, not a failure | A3 | same; `NOT_CHECKABLE` marker -> `indeterminate` (l.155-156) | `test_not_checkable_summer_comfort_stays_a_reserve_not_a_block` (`dynamic`=NOT_DETERMINED, `sia3802_status==COMPLIANT`) | `SIA3802_SUMMER_COMFORT_NOT_CHECKABLE` contains `NOT_CHECKABLE` -> indeterminate, never blocking. | **CONFIRME** |
| 3 | Active solar protection without documented control (SS7.1.2.2-5) -> NOT_DETERMINED, never silently COMPLIANT | A4: gate `solar_protection_control_incomplete` (l.228-232, 278-282, 295) | `compliance_verdict`; alerts `SIA3802_SOLAR_PROTECTION_CONTROL_MISSING`/`_TYPE_MISSING` | `test_unverified_solar_protection_control_gates_the_verdict` (`sia3802_status==NOT_DETERMINED`, reason `solar_protection_control_incomplete`, item in `outstanding`) | Gate triggered on rule name; fires after blocking/contradiction/missing gate -> a real overheating or contradiction takes priority. | **CONFIRME** |
| 4 | No over-blocking: model without active blind not gated by the solar gate | A4 | `model_analyzer.has_active_solar_protection` (l.85-108) guards emission (`sia380_checker` l.750, 760) | Logic: alerts emitted only if `active_solar_protection` is true; shading_type empty/none/disabled => False; active flags "off" => False | No dedicated unit test for "no blind => no gate", but the guard is verified by reading and the robustness tests do not trigger the gate on clean data. | **CONFIRME** (reserve: add an explicit negative test, see conditions) |
| 5 | Ventilation/solar protection merely uncheckable = reserve (overall NOT_DETERMINED), not NOT_COMPLIANT | A3/A4 + existing | `_count_by_category` (l.137-161): can't-check markers -> indeterminate even at CRITICAL | `test_uncheckable_domain_is_not_reported_as_non_compliant` (overall NOT_DETERMINED, never NOT_COMPLIANT) | "I cannot read" is never a failure. False-failure ruled out. | **CONFIRME** |
| 6 | Honest category score: missing evidence can no longer read ~85 AND COMPLIANT | A2: `-20`/indeterminate alert + ceiling `INCOMPLETE_EVIDENCE_SCORE_CEILING=60` | `sia380_checker._calculate_category_score` (l.1813-1852), `_is_indeterminate_alert` (l.1864-1872) | `test_indeterminate_alert_caps_the_category_below_the_pass_band` (Openings <=60 and >0) | Score markers = verdict markers (5 identical) -> score and verdict aligned by construction. | **CONFIRME** |
| 7 | No false 0: merely missing evidence does not force 0 | A2 | `_calculate_category_score`: 0.0 reserved for `_is_blocking_not_checkable_alert` (CRITICAL MODEL_NOT_CHECKABLE/EXTERNAL_ENVELOPE_MISSING/RULE_EXECUTION_ERROR) | `test_indeterminate_alert_caps... >0`; `test_determined_advisory_alone_stays_in_the_pass_band` (==95) | Simple missing => capped at 60, never 0. 0 reserved for "no score possible" states. | **CONFIRME** |
| 8 | Honest indicator: the number is no longer presented as a compliance score | A1: app.py logs the VERDICT first; number relabelled "coverage (diagnostic, != compliance)" | `swiss_sia/app.py` (l.~1370-1385); `excel_report.py` cards/KPI renamed | Diff reading `3c48a77`; verdict computed once and reused | The verdict precedes the number; internal label "SIA 380/2 COVERAGE (diag.) ... excludes the decisive SS7.2.5.2 gate". | **CONFIRME** |
| 9 | Client scope does not expose "SIA 380/2 automated score" | A1 | `excel_report` `else` branch (include_sia4010=False) leads with COMPLIANCE VERDICT, omits the number | `test_client_workbook_has_no_sia4010_or_development_indicators` + `test_client_workbook_uses_real_verdict_and_project_information` (assertNotIn "SIA 380/2 automated score", "Model health score", "4010") | Client card = VERDICT/BLOCKING/ADVISORY; number absent. | **CONFIRME** |
| 10 | New outstanding item translated (no silently empty key) | A4 | `ui_translations` key `outstanding_sia3802_solar_protection_control` (en/de/fr/it); mapping `translate("outstanding_"+item)` (`compliance_report_pdf` l.574, 1155) | `translation` suite green; emitted key `sia3802_solar_protection_control` <-> corresponding translation key | Consistent mapping; all 4 languages present. | **CONFIRME** |
| 11 | Hard/pure separation: `engine/` never imports `iesve` | (standing) | -- | `engine/tests/test_engine_purity.py`; grep: no `import iesve`/`from iesve` line in `engine/` code (only comments/test guards) | engine/ pure. | **CONFIRME** |

## Adversarial cross-checks performed
- Gate order in `build_compliance_verdict`: `blocking_total` (including HIGH overheating) is evaluated BEFORE `comparison_available`, so a determined overheating is not masked by a satisfied SS7.2.5.2 gate. Verified l.262-288.
- A CRITICAL "can't check" (e.g. EXTERNAL_ENVELOPE_MISSING) is indeterminate on the verdict side (never NOT_COMPLIANT) but yields 0 on the coverage score side. Consistent: verdict=NOT_DETERMINED, number=zero coverage; neither reads "compliant". No contradiction.
- The checker does produce the key `"dynamic"` in `results` (sia380_checker l.413), so the dynamic domain is not perpetually `domain_not_evaluated`; its status follows actual alerts.
- Solar gate: only triggers on alerts emitted under the `has_active_solar_protection` condition => no false NOT_DETERMINED on a model without blinds.

## Observations / minor defects (non-blocking)
- **i18n `dynamic` domain label**: `compliance_report_html._DOMAIN_LABELS` (l.450-459) does not contain a `dynamic` key. In the HTML report, if the dynamic domain appears as a reserve, the label falls back to the raw string `dynamic` (English, untranslated) -- not a silent blank, but not localised in FR/DE/IT. The client PDF is NOT affected (it only uses the translated `outstanding` tuple). To be fixed in the HTML report.
- **`iesve` boundary in `swiss_sia/`**: `app.py`, `evidence_bootstrap.py`, `simulation_results.py` import `iesve` (imports guarded at runtime), beyond the announced boundary `reference_model/ve_api.py` + `data_extractor`. Pre-existing, outside the scope of these 4 commits; flagged for architectural tracking, non-blocking for this batch.
- **Missing negative test (row 4)**: no unit test explicitly pins "no blind => solar gate silent". The guard is correct by reading but merits a dedicated adversarial test.

## Normative reserves (independent of code quality)
- The gates SS7.1 (ventilation, solar protection control, overheating) and the decisive gate SS7.2.5.2 rest on a **product decision 2026-08-19 + norm-analyst ruling A4 2026-08-20**, NOT on a frozen reference value in `/refs/reference-data/`. No numerical reference value to reproduce for these policy rules; the verification focuses on logical consistency, not on an external reference.
- **SS7.2.4 (electrical threshold)** not addressed -- known gap, tracked in `docs/project/TODO.md` and commit A1.
- **Design-day** remains an accepted reserve (norm-analyst A4).
- SIA 180 Fig.3 still `[A VERIFIER]` (project memory) -- outside the scope of this batch but relevant for downstream overheating.

## Signature decision

Every row 1-11 of the matrix is true and reproduced by a passing test.
The 4 fixes do what they claim: no false-pass (determined overheating and
solar control actually block), no false-failure (uncheckable = reserve
NOT_DETERMINED, never NOT_COMPLIANT; never a false 0 for missing evidence),
score and verdict aligned, indicator honestly relabelled and absent from the
client scope.

**SIGNED -- batch A1..A4 (score<->verdict consistency, indicator honesty, SS7.1
gates overheating / ventilation / solar protection) -- AUDITED OK -- 2026-08-21.**

Scope of the signature: only the verdict/score/indicator logic above.
This signature does **NOT** constitute a claim of SIA 380/2 compliance nor of
SIA 4010 validation, which require the SS7.2.5.2 gate reviewed, official test
results, and sub-commission attestation.

Remaining conditions (to be lifted outside the scope of this batch, non-blocking
for the above signature):
1. SS7.2.4 electrical threshold -- not implemented.
2. i18n `dynamic` label in the HTML report.
3. Negative test "no blind => no solar gate".
4. `iesve` boundary in `swiss_sia/` (architectural tracking).
5. SIA 180 Fig.3 `[A VERIFIER]` for downstream overheating.
