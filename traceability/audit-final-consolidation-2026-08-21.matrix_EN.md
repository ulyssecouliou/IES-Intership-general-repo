> **Note:** Translated from French original. See [audit-final-consolidation-2026-08-21.matrix.md](audit-final-consolidation-2026-08-21.matrix.md) for the source document.

# Traceability matrix -- FINAL CONSOLIDATED AUDIT (evidence-hardening batch)

Branch: `sia4010-evidence-hardening-20260812`
Auditor: qa-auditor (independent, **read-only** access to production code; no modifications)
Date: 2026-08-21
Status: **SIGNED UNDER CONDITIONS**
Scope: overall consistency of the SIA 380/2 client compliance chain (verdict,
indicators, evidence ingestion, diagnostic vs gate, frozen reference data,
normative reserves, hard/pure separation) + overall signature decision.

Partial audits already signed and re-confirmed here:
- `traceability/audit-lot-A1-A4-verification-2026-08-21.matrix.md` (indicators + verdict A1-A4) -- **SIGNED**
- `traceability/electrical-power-7.2.4.matrix.md` (SS7.2.4) -- **SIGNED (gate structure)**

## Test suite executed

- Command: `python -m pytest tests/ -q`
- Result: **exit code 0, 0 failures**. Tests collected: **1356** (`pytest --collect-only`),
  plus subtests. Raw output: task `btrmp74ll`.
- Only warnings: `openpyxl` Data-Validation extension not supported (3 test
  workbook files) -- non-blocking, unrelated to the compliance engine.

---

## 1. Verdict (`swiss_sia/compliance_verdict.py`)

| # | Requirement | file:line | Evidence | Verdict |
|---|---|---|---|---|
| V1 | Decisive gate SS7.2.5.2: COMPLIANT only if reviewed comparison satisfied | `compliance_verdict.py:286-308` (`not comparison_available` -> NOT_DETERMINED; otherwise COMPLIANT) | Signed batch A1-A4; re-read. Without reviewed comparison => NOT_DETERMINED, never silently COMPLIANT. | **CONFIRME** |
| V2 | Autonomous requirements SS7.1 (ventilation, solar protection control, summer comfort) are gates, not reserves | `:288-297` (ventilation, solar-protection); `:50,155-156` (dynamic -> blocking if DETERMINED HIGH) | Signed A3/A4. DETERMINED overheating -> `blocking_total` evaluated (`:274`) BEFORE the gate; uncheckable -> `indeterminate` -> NOT_DETERMINED. | **CONFIRME** |
| V3 | SS7.2.4 autonomous conditional gate | `:249-258, 281-285, 298-302` | Signed SS7.2.4. NC-desirable blocks (`:281`, before `not comparison_available`); unknown/missing -> NOT_DETERMINED. | **CONFIRME** |
| V4 | No false-pass: unverified autonomous requirement => never COMPLIANT | gate order `:272-308` | Each autonomous gate forces NOT_DETERMINED/NOT_COMPLIANT before the final COMPLIANT branch. | **CONFIRME** |
| V5 | No false-failure: uncheckable => NOT_DETERMINED, never NOT_COMPLIANT | `_count_by_category` `:137-161` (can't-check markers -> `indeterminate` even at CRITICAL) | Signed A1-A4 (`test_uncheckable_domain_is_not_reported_as_non_compliant`). | **CONFIRME** |
| V6 | Gate order: determined (blocking + contradiction + SS7.2.4 NC) BEFORE "missing comparison" BEFORE incomplete evidence gates | `:272-308` | A real failure takes priority over a missing gate; a missing gate takes priority over a reserve. Consistent. | **CONFIRME** |

## 2. Indicators (`health_score.py`, `excel_report.py`, `app.py`)

| # | Requirement | file:line | Evidence | Verdict |
|---|---|---|---|---|
| I1 | The number = coverage diagnostic (not equal to compliance); the verdict comes first | A1 (`app.py`, `excel_report.py`), signed A1-A4 (rows 8-9 of the A1-A4 matrix) | Re-confirmed: client score omitted (`include_sia4010=False`), card led by the VERDICT. | **CONFIRME** |
| I2 | NOT_CHECKABLE caps the category score | `sia380_checker._calculate_category_score` (ceiling `INCOMPLETE_EVIDENCE_SCORE_CEILING=60`); `health_score.py:130-148` missing markers | Signed A2 (`test_indeterminate_alert_caps_the_category_below_the_pass_band`). Score markers = verdict markers. | **CONFIRME** |
| I3 | Weighted compliance score only includes implemented categories | `health_score.py:60-73` (envelope/openings/ventilation/gains/hvac) | Consistent; diagnostics (EER/SEER/SCoP) outside the weighting. | **CONFIRME** |

## 3. Evidence ingestion (fail-closed)

| # | Requirement | file:line | Evidence | Verdict |
|---|---|---|---|---|
| E1 | Thermal bridges: direct VE reading H_tb (W/K) | `sia380_checker.py:330-339` (`_read_ve_thermal_bridges`, `find_accepted_thermal_bridges`) | VE reading psi/chi->H_tb; CSV reviewed as fallback. Consistent with project memory. | **CONFIRME** |
| E2 | Declared cooling SEER (Path A) properly compared to SIA table 5 band | `sia380_checker.py:90-105`; ref. `sn-en-14825-2018.cooling-seer.json` | Declared SEER = EN 14825 by construction; reserve lifted for cooling. | **CONFIRME** |
| E3 | SS7.2.4 fail-closed acceptance (reviewer+date+source+quantum) | `evidence_manager.py:584-593` | Accepted only if review_status in ACCEPTED and project and building_status_key and valid power and unit W/m2 and reviewer and date and source. | **CONFIRME** |
| E4 | SS7.2.4 guard R1: negative power rejected | `evidence_manager.py:576-577` (`power_is_valid = power is not None and power >= 0.0`) | **RESERVE R1 FIXED** (commit 294739a). Verified on disk. | **CONFIRME (fixed)** |
| E5 | SS7.2.4 guard R2: unit != W/m2 rejected | `evidence_manager.py:578-583` (`unit_is_w_m2`; rejects kW/mW) | **RESERVE R2 FIXED** (commit 294739a). Empty unit accepted (column named `_w_m2`). | **CONFIRME (fixed)** |
| E6 | Nothing inferred from an empty field; never a silent PASS | `_normalize_electrical_power_record` `:528-594`, `_normalize_solar_protection_record` `:597+` | Any missing field -> `accepted=False`. Unknown cooling category -> `""` -> NOT_DETERMINED. | **CONFIRME** |
| E7 | Checker exposes a single `verdict_status` read by the gate | `sia380_checker.py:1450-1466, 476` | The gate `compliance_verdict.py:254-258` reads `electrical_power.verdict_status`. Complete chain. | **CONFIRME** |

## 4. Diagnostic vs gate (SIA 380/2 note 6)

| # | Requirement | file:line | Evidence | Verdict |
|---|---|---|---|---|
| D1 | EER/SEER/SCoP = reference project inputs, non-blocking | `compliance_criteria.py:83-102`; `compliance_verdict.py:11-14, 259-268` (diagnostics = reserves in `outstanding`) | SCoP `[TO VERIFY]` informational; does not degrade the verdict. Commit a9ca3e4 (note 6). | **CONFIRME** |
| D2 | Decisive = SS7.2.5.2 + SS7.1 + SS7.2.4 only | `compliance_verdict.py:272-308` | Only these gates change the status; the rest goes to `outstanding`. | **CONFIRME** |

## 5. Frozen reference data (`refs/reference-data/`)

| # | File | Source / cross-check | Status | Verdict |
|---|---|---|---|---|
| R-SEER | `sn-en-14825-2018.cooling-seer.json` | Published document captures (user, 2026-08-20); linked to SIA 380/2 table 5 p.38; script `build_sn_en_14825_seer.py` | FROZEN (cooling); heating SCoP NOT frozen | **CONFIRME (cooling)** |
| R-COMFORT | `sia-180-2014.comfort.json` | Fig.3 provided by Yiqiao Yang 2026-08-20; breakpoints recalculated from intersections + compared against the published figure | FROZEN subject to corrigenda; Fig.3 now present (no longer `[A VERIFIER]`) | **CONFIRME** |
| R-BLINDS | `sia-387-4-2017.blinds.json` | SIA 387/4:2023 table 9 + eq. 18-20, capture Yiqiao Yang 2026-08-21; edition reserve lifted | FROZEN (solar protection); lighting content NOT frozen | **CONFIRME (solar protection)** |

All three files carry provenance, generator script, and SIA link. No invented values found.

## 6. Normative reserves (`docs/project/RESERVES_NORMATIVES.md`)

| # | Requirement | Evidence | Verdict |
|---|---|---|---|
| N1 | "Validated under reserve, never a PASS" policy faithfully reflected in code | SCoP -> DIAGNOSTIC/`[TO VERIFY]` non-blocking (`compliance_criteria.py:96-102`); lighting -> PARTIAL not closed; SS7.2.4 unknown category -> NOT_DETERMINED; cooling SEER -> reserve lifted | Register <-> code consistent line by line. | **CONFIRME** |

## 7. Hard/pure separation

| # | Check | Evidence | Verdict |
|---|---|---|---|
| S1 | `engine/` never imports `iesve` | `grep -rn "import iesve\|from iesve" engine/` -> only comments + purity tests (`test_engine_purity.py`); no actual import | `engine/` pure. | **CONFIRME** |
| S2 | SS7.2.4/verdict/evidence modules `iesve`-free | grep = 0 occurrences in `compliance_verdict.py`, `evidence_manager.py`, `sia380_checker.py` | Compliant. | **CONFIRME** |

---

## Uncommitted files from a parallel session (flagged, OUTSIDE SIA 380/2 client scope)

On the SIA 4010 side (validation campaign / ApacheSim template), with no effect on the
SIA 380/2 client compliance chain audited above. They pass the full suite
(1356 tests, exit 0):
- `swiss_sia/reference_model/sia4010/template_apachesim.py`, `validation_campaign.py`
  (new) -- do not contain `import iesve` at module level.
- `Run_VE_SIA4010_*.py` (3), `docs/project/SIA4010_CAMPAGNE_VALIDATION_ACCELEREE.md`,
  `tests/test_sia4010_*` (2 new), and `reference_model/sia4010/*` modifications.

These items fall under the SIA 4010 loop (sub-commission attestation required) and
are NOT covered by this signature.

---

## Inherited minor defects (non-blocking, already listed in the partial audits)

1. i18n `dynamic` domain label not localised in the **HTML** report (`compliance_report_html._DOMAIN_LABELS`) -- client PDF not affected. Localisation defect, not a silent blank.
2. `iesve` boundary in `swiss_sia/`: `app.py`, `evidence_bootstrap.py`, `simulation_results.py` import `iesve` (imports guarded at runtime), beyond the announced boundary. Pre-existing, architectural tracking.
3. SS7.2.4 R3 (`conditioned_area_m2` reconciliation) and R4 (`has_fluid_installation` heuristic): documented reserves, not gate false-passes.
4. Negative test "no blind => no solar gate": guard correct by reading, dedicated adversarial test still desirable.

---

## OVERALL SIGNATURE DECISION

**SIGNED UNDER CONDITIONS** -- the SIA 380/2 client compliance logic chain
(verdict, indicators, fail-closed evidence ingestion, diagnostic vs gate,
hard/pure separation) is **consistent overall, with no false-pass or false-failure
found**, the full suite passes (1356 tests, 0 failures), the SS7.2.4 R1
(negative power) and R2 (unit != W/m2) reserves are **effectively fixed** on disk
(`evidence_manager.py:576-583`, commit 294739a), and the frozen reference data
is sourced with cross-checks.

The signature is **conditional** because it rests on **product decisions /
norm-analyst rulings (A4, A5)**, NOT on frozen numerical reference values
for the policy gates SS7.1/SS7.2.4/SS7.2.5.2 (no external reference to reproduce
for these structural rules), and because normative reserves remain.

### Remaining reserves and blocking character

| Reserve | Missing source | Code effect | Blocking for commercial use? |
|---|---|---|---|
| **SN EN 14825 heating (SCoP)** | EN 14825 heating part | SCoP `[TO VERIFY]` informational, non-blocking (note 6) | **NOT blocking** -- diagnostic, not a gate |
| **SIA 387/4 lighting content** | Lighting part (presence/light control) | Lighting verdict PARTIAL not closed | **NOT blocking** for the overall verdict (SS7.2.5.2 decisive); to be completed |
| **SIA 180/2024/2056 (SS7.2.4 cooling classification)** | Required/desirable rule | Category read by the reviewer; unknown -> NOT_DETERMINED | **NOT blocking** structurally, but the classification *justification* is not verifiable by the tool -> referral to norm-analyst/reference-data-engineer |
| **SIA 380 umbrella standard (7/12 threshold matching)** | Case-to-threshold correspondence | Thresholds applied under `[A VERIFIER]` reserve per reviewed status | **NOT blocking** structurally; documented reserve |
| **SIA 180 exact operative temp. (summer comfort)** | Operative temp. definition / theta_rm window | Calculation from frozen Fig.3/4 | **NOT blocking**; blocks if overheating confirmed, otherwise reserve |

None of these reserves is blocking for the **logical structure** signed; all
remain **explicitly reserved** in the deliverables (`outstanding`, `[TO VERIFY]`
caveats) and can **never** be converted to `PASS` without the document
or a reviewer attestation.

### Scope of the signature

This signature covers **only** verdict/score/indicator consistency, the
SS7.1 / SS7.2.4 / SS7.2.5.2 gates, fail-closed evidence ingestion (incl. fixed
R1/R2 guards), and hard/pure separation. It does **NOT** constitute:
- a claim of SIA 380/2 compliance (requires the SS7.2.5.2 comparison reviewed per
  actual project + the normative reserves above lifted);
- SIA 4010 validation (requires official test results + sub-commission
  attestation; uncommitted campaign files are outside scope).

**AUDITED OK (SIA 380/2 client compliance structure, under the above conditions)
-- 2026-08-21.**
