> **Note:** Translated from French original. See [CLIENT_MVP_IMPLEMENTATION_LIST.md](CLIENT_MVP_IMPLEMENTATION_LIST.md) for the source document.

# Client Model Analysis & Reports -- Implementation & Corrections List (MVP)

**Date:** 2026-08-17. Scope: the client path `Run_VE_Swiss_Compliance.py -> swiss_sia/app.py::main -> data_extractor -> model_analyzer -> sia380_checker + sia4010_checker -> compliance_verdict -> compliance_report_pdf + excel_report`, plus `reference_project.py`, `config.py`, `value_integrity.py`. Out of scope: the reference model builder (`ve_asset_provisioner`/`workflow`/`native_ui`).

Each item is cited as `file:line` and classified: **[ASSESSABLE]**, **[BLOCKED / NOT_CHECKABLE]**, **[NOT IMPLEMENTED]**.

---

## 0. Is the `.aps` used? Yes -- 1 of 3 sources

| Source | Feeds |
|---|---|
| **Static model** (`data_extractor.py`) -- geometry, U-values, glazing, HVAC indices, infiltration | SIA 380/2 "reference project" diagnostics per component (LOW/advisory) |
| **`.aps` ApacheSim** (`simulation_results.py`, via `_collect_dynamic_results` app.py:318) -- heating/cooling demands, energy, operative temperature + occupancy | **Dynamic summer comfort SIA 380/2** (hours outside SIA 180 bounds) + **SIA 4010 energy readiness** |
| **Reviewer CSV** (`evidence_manager`, app.py:397) -- global project/reference comparison | **The DECISIVE compliance gate SIA 380/2 SS7.2.5.2** |

**The decisive SIA 380/2 verdict does NOT rely on the `.aps`** but on the project/reference comparison provided by the reviewer. The `.aps` carries the simulated component (summer comfort, energy). Without `.aps` -> dynamic components become `NOT_CHECKABLE` (fail-closed).

---

## 1. Inventory verdict

**The program is safe and conservative: nothing manufactures a `PASS`, no over-assertion survives into the reports.** The MVP gaps are not about dangerous assertions but about **the ability to REACH an assessable compliant verdict**: the decisive reference gate and extraction completeness. Two structural safeguards confirmed: "cannot verify" alerts -> `NOT_DETERMINED`, never `NOT_COMPLIANT` (`compliance_verdict.py:122-146`); SIA 4010 capped at `attestation_required` (`compliance_verdict.py:252-262`).

**Already fixed (audit P0):** COMPLIANT gate that did not verify `project <= reference` (M-COMP); SN EN 14825 caveat on SEER/SCoP (M-SEER). The inventory confirms that the gate "fails correctly on contradiction" (`sia380_checker.py:438-464`).

---

## 2. P0-client -- blocking for a credible client report

- **[TO FIX] The PDF verdict is poorly scoped.** `render_compliance_report_pdf` always folds SIA 4010 into the verdict (`compliance_report_pdf.py:576`, no scope parameter). Since SIA 4010 caps at `NOT_DETERMINED`, **a perfectly clean 380/2 model still prints `NOT_DETERMINED` on the client header.** -> make the verdict scope-aware (380/2-only report). *This is the most visible client defect.*
- **[NOT IMPLEMENTED -- reviewer-only] The decisive SIA 380/2 gate (SS7.2.5.2) is not automated.** No project/reference demand is simulated; compliance requires a project/reference pair `accepted` by a reviewer, scanned from a CSV (`sia380_checker.py:390-485`). The reference project spec can never be "runnable" (`reference_project.py:927-936` only returns NOT_CHECKABLE / BLOCKED / PARTIAL). -> **product decision**: either automate the reference run, or formalize the reviewer workflow as a documented MVP deliverable.
- **[TO CLARIFY] The `compliance_score` (0-100) can be high without the decisive gate** (component checks are LOW/advisory; `health_score.py:52-65`). Currently mitigated by labels ("automated precheck indicator", app.py:1128). -> ensure no reader mistakes it for a compliance percentage.

---

## 3. P1 -- Model extraction: fill gaps that blank out real checks

These quantities are expected by checks but rarely extracted -> the check silently falls to `_MISSING`/`NOT_CHECKABLE`:

- **[BLOCKED]** `tau_v` (glazing visible transmittance) -- alias lookup not cited (`data_extractor.py:1244-1260`).
- **[BLOCKED]** `frame_fraction` (frame fraction) -- alias not cited (`data_extractor.py:1262-1284`).
- **[BLOCKED]** `g_total` -- "VEScripts does not document a direct g_total field" (`data_extractor.py:1421-1423`).
- **[BLOCKED]** `ventilation_installation_type` + `ventilation_control_level` -- heuristics, often `None` (`model_analyzer.py:779-820`).
- **[BLOCKED]** `window_operable` / window ventilation support -- depends on MacroFlo.
- **[BLOCKED]** `internal_gains_wh_m2_day` (daily internal gains) -- not populated.
- **[NOT IMPLEMENTED]** `RoomData.dynamic_results` never assigned in the extractor (only in app.py:661); HVAC `energy_consumption` hardcoded to `None` (`model_analyzer.py:715`).

---

## 4. P1 -- Uncited values/mappings to fix (violation of the "never infer/uncited" rule)

- **[TO CITE]** Integer-to-opening-type mapping `4->window, 5/6->door, 11->hole` -- not cited (`data_extractor.py:1076-1087`, duplicated `model_analyzer.py:1103-1108`).
- **[TO CITE]** Generator class inference from free-text tokens, fallback `heat_pump_unclassified` (`model_analyzer.py:884-918`) -- drives SCoP/EER applicability.
- **[TO CITE]** Air-exchange enums `type==2` ventilation / `==0` infiltration (`model_analyzer.py:477,511,530`).
- **[TO CITE]** Factor `x3.6` l/s->m3/h (`model_analyzer.py:574,590,625`); thresholds `_normalize_unit_fraction` 1.0/100 (`data_extractor.py:1572-1579`).
- **[TO CITE]** Window day/night threshold `>=23.5 h` (`model_analyzer.py:758`).
- **[TO FIX]** Model selection always picks `models[0]` -- `_select_best_model` computes body counts then ignores them (`data_extractor.py:80-99`).
- **[TO CITE]** Door limit aliased on `window_u=1.10` (`config.py:386`) -- conservative, not a cited gate value.
- **[TO FIX]** Typo `"ashae"` alongside `"ashrae"` in U-value preference list (`data_extractor.py:862,1137`).
- **[TO CITE]** WWR `wwr_max=0.3` (`config.py:397`) -- labeled as review indicator, not a limit: OK but keep explicit.

---

## 5. P2 -- Normative sources to acquire (unblock checks)

| Missing source | Unblocks | Cited at |
|---|---|---|
| **SN EN 14825** | SEER (cooling) & SCoP (heating) verdicts -- equivalence unproven `[TO VERIFY]` | `sia380_checker.py:72-76` |
| **SIA 2024:2021 Raumdatenblatter** (primary source) | removes dependency on reviewer CSV for Gains (JSON already frozen on reference side) | `sia380_checker.py:780-789` |
| **SIA 387/4** (lighting power/control) | lighting control + reference lighting family | `sia380_checker.py:808-826` |
| **SIA 180:2014** (comfort curves) | dynamic summer comfort per room | `sia380_checker.py:1114-1165` |
| **SIA 380 umbrella standard** | annual energy index aggregation/weighting | `reference_project.py:107` |
| **SN EN 15316-2 / 16798-13** | system energy calculations / design-day sizing power -- not implemented | (no occurrence) |

---

## 6. P2/P3 -- Unimplemented checks

- **[NOT IMPLEMENTED]** Thermal bridges (psi/chi) -- limit `0.0` placeholder (`config.py:104`); Excel always `MISSING` "the configured zero remains a placeholder, not evidence" (`excel_report.py:4637-4644`). No psi/chi ingestion path.
- **[NOT IMPLEMENTED]** Design-day sizing power (design-day workflow) -- `config.py:1894-1909` `automation:"NOT_IMPLEMENTED"`; annual peaks are explicitly rejected.
- **[CORRECTLY BLOCKED]** Cooling >=150 kW (Table 7 EER+ net of post-cooling) -- VE does not expose it -> blocker (`reference_project.py:592-600`).

---

## 7. SIA 4010 readiness state (client) -- informational

- **[SAFEGUARD verified]** Never issues a pass: cap `OFFICIAL_RESULTS_RECORDED` (`sia4010_checker.py:1581-1583`).
- **[INERT]** `score` structurally always `0.0` (every branch sets `score=0`, `:1496-1511`).
- **[NOT IMPLEMENTED / dead]** `_calculate_heating/cooling_demand` return `None` (`:1402-1408`, overwritten from APS app.py:626-637); `_calculate_co2_emissions`/`_renewable_energy_share` exist but are **never called** (`:1410-1436`).
- **[INERT on client path]** Official band cross-check not fed (`app.py:1009` -> `{}`).

---

## 8. Reports -- corrections

**PDF** (`compliance_report_pdf.py`, `pdf_writer.py`) -- one-page report, firm header, verdict, identification, model summary (facade rose), scope block "not a certificate", signature. No over-assertion. Corrections:
- **[TO FIX]** verdict scope (cf. SS2, `:576`).
- **[PLACEHOLDER]** only `office_logo.placeholder.png` exists on disk (no `ies_logo.png`) -> every cover embeds the placeholder (`:325-347`).

**Excel** (`excel_report.py`, 7,027 lines) -- **custom `xlsxwriter` workbook, NOT the official SIA form** (neither `openpyxl` nor template; docstring `:3-4`), 31 sheets. No over-assertion survives ("fully SIA compliant" only appears in *Avoid* lines, `:1239`). Corrections:
- **[NOT IMPLEMENTED]** thermal bridges = fail-closed placeholder (`:4637-4644`).
- **[DEAD]** `SUMMARY` (`:2282`) and `ACTION PLAN` (`:4101`) sheets defined but never called; stale comment `:165-168`.
- **[PRODUCT DECISION]** ADR-001 SS4 planned to *fill the official SIA 4010 workbook via COM* (maximum credibility) -- this concerns **SIA 4010 validation**, separate from the 380/2 client report. The current custom workbook is correct for the 380/2 deliverable; filling the official workbook remains to be done on the SIA 4010 side.

---

## 9. OPEN normative issue -- which operative temperature for summer comfort?

Summer comfort reads the series `("dry","resultant","temperature")` from the APS (`simulation_results.py:601`), so **"Dry resultant temperature"**. However, the `.aps` exposes several competing definitions (Operative ASHRAE, TM52/CIBSE, Dry resultant, Environmental -- ADR-001 SS3). **Choosing the wrong one produces a silent, plausible error.** -> to be resolved by `norm-analyst` (SIA 380/2 SS5 / SIA 180) before summer comfort can be considered reliable. *This is exactly the "wrong but credible" outcome that this project exists to eliminate.*

---

## 10. Prioritized shortcut (client MVP)

1. **Scope the PDF verdict** (380/2-only report not dragged to `NOT_DETERMINED` by SIA 4010). `compliance_report_pdf.py:576`.
2. **Deliver the decisive 380/2 gate** -- automate the reference run OR formalize the reviewer workflow as a deliverable. `sia380_checker.py:390-485`.
3. **Fill the extraction gaps** that blank out real checks (tau_v, frame_fraction, g_total, ventilation type/control, daily gains). SS3.
4. **Cite or replace uncited mappings** (opening types, generator class, enums, 23.5 h, `models[0]`). SS4.
5. **Resolve the operative temperature** for summer comfort (SS9) -- risk of silent error.
6. **Acquire SN EN 14825 + SIA 2024/387/4** to lift caveats and the CSV dependency. SS5.
7. **Thermal bridges (psi/chi) + design-day sizing power** -- not implemented. SS6.
8. **Report cosmetics**: real `ies_logo.png`, remove the 2 dead Excel sheets + stale comment. SS8.

*Nothing in the client path manufactures a PASS or over-asserts a validation; the tool is conservative and fail-closed end to end. The gaps concern reaching an assessable compliant verdict, not the safety of assertions.*
