> **Note:** Translated from French original. See [TODO.md](TODO.md) for the source document.

# TODO — SIA Compliance / SIA 4010 Navigator

> Single actionable tracker. Full detail in:
> - [`AUDIT_COMPLET_2026-08-16.md`](AUDIT_COMPLET_2026-08-16.md) — audit + findings + P0-P3 plan
> - [`CLIENT_MVP_IMPLEMENTATION_LIST.md`](CLIENT_MVP_IMPLEMENTATION_LIST.md) — client analysis + reports, cited `file:line`
>
> Status: ✅ done · ⬜ to do · 🔶 product/regulatory decision required

---

## 🧭 STATUS 2026-08-20 — client chain proven on real VE

Example model `SIA_compatible_model_TEST`: **overall SIA 380/2 COMPLIANT (with reserves)**, **16 criteria OK**, precheck 89.7, health 77. Complete chain validated on real VE: extraction (gains read from template) → `.aps` (comfort **SIA 180 calculated** + energy) → **decisive gate §7.2.5.2** → COMPLIANT verdict with reserves → deliverables (2-page PDF + **IES logo**, HTML dashboard + limitations panel, criteria JSON, evidence pack).

### ✅ Done this session (2026-08-19/20)
- [x] Decoupling **SIA 4010 out of the client path** (default 380/2-only; separate internal launcher); SIA 4010 = software validation, not building validation.
- [x] **Verdict decided on the §7.2.5.2 gate**; `NOT_CHECKABLE` components = displayed reserves, no longer blockers *(commit `cd11781`, **PENDING norm-analyst**)*.
- [x] **Reading gains/air-exchanges from the assigned template** (VE does not materialise gains at room level) *(b76fa56)*.
- [x] **Summer comfort SIA 180** calculated from θrm 48 h of the `.aps` (Fig.4 verified) *(6b71b0f)* — **PENDING norm-analyst**: operative temperature definition, θrm window, Fig.3.
- [x] **Weather**: match on the *stem* (`.epw`/`.fwt` equivalents) *(97d3cce)*.
- [x] **SIA 2024 use mapping accepted credited** in coverage *(4af0de1)*.
- [x] **Criteria manifest** JSON populated at runtime `<report>_compliance_criteria.json` + one-click explain.
- [x] **Professional 2-page PDF report**: 2-column identification card + client placeholders, appendix (justified limitations + reserves + methodology), **IES logo** at the footer.
- [x] Reload of `compliance_verdict`/`compliance_criteria` per Run (no more VE restart required) *(1cfcc86)*.
- [x] Read-only probes: room gains (`room_id`), `.aps` variables.

### ⬜ Client model reserves — detail (value · what to do · who · tooling effort)

- [x] ✅ **Thermal bridges ψ/χ** — *direct VE read* (`595660f`, after `3a19a0c`): VE 2025.2 exposes ψ/χ per surface (`VESurface.get_thermal_bridges_non_repeating/_random`) — discovered via the official IES manager script, confirmed by probe on real VE (H_tb=24.66 W/K on the test model). `data_extractor.get_model_thermal_bridges()` computes **H_tb = Σ(ψ·L·flux) + Σ(χ·count)** in W/K; `sia380_checker`: VE-read **takes priority**, reviewer CSV as **fallback** (older VEs / model not populated). Capability `VE_AVAILABLE`.
  - ⚠️ *Honesty*: junctions with ψ=0 are flagged (possible unset default); an all-zero reading is not complete proof.
  - *Remaining on user side*: ensure that ψ values are actually **entered** in VE (otherwise 0 by default) — the quality of ψ values remains the modeller's/reviewer's responsibility.

- ⬜ **Design power** (`NOT_AVAILABLE_IN_VE`, `config.py:1894` `NOT_IMPLEMENTED`)
  - *Value*: SIA 380/2 prescribes design days (hot/cold sequences after preconditioning); neither annual peaks nor autosize are valid substitutes.
  - *What to do*: dedicated design-day simulations in VE; read their `.aps`.
  - *Who*: VE modeller (simulation) + developer (extraction).
  - *Tooling*: **implement the design-day workflow** (reading `.aps` for design days). Major development.

- [x] ✅ **Cooling EER / SEER** — *ingestion + SEER comparison wired* (`92c9330`, `615e03f`): reviewer CSV `SIA3802_cooling_generators_<project>.csv` (air/water class + capacity kW + **declared SEER** or nominal EER). The **declared SEER** (ErP data sheet, EN 14825) is compared **cleanly** against the SIA Table 5 band (rule `SIA3802_COOLING_SEER_MIN_DECLARED`, without caveat), **gated air-cooled < 150 kW**; water-cooled / ≥150 kW → NOT_CHECKABLE (tables 6/7). Ref. EN 14825:2018 frozen + norm-analyst opinion.
  - *Remaining on user side*: provide the **manufacturer data sheet** (single SEER) and enter it in the CSV.
  - [x] ✅ *`seer` bands verified* against **SIA 380/2 PDF p.38** (`b711134`, PyMuPDF): Tables 5 (air) & 6 (water) match exactly; declared gate extended to air+water (only Table 7 EER+ / unclassified excluded).
  - ⬜ *Remaining qa-auditor reserve*: document the 5 Q1 conditions for the actual client project unit. Detail: `traceability/sn-en-14825-seer-froid.spec.md`.
  - ⬜ *Heating SCoP*: remains `[TO VERIFY]` (hot-side EN 14825 calculation clause not frozen; basis for tables 8/9 not confirmed).

- [x] ✅ **AHU / heat recovery** — *ingestion done* (`5671e1b`): reviewer CSV `SIA3802_ahu_heat_recovery_<project>.csv` (airtightness class + temperature recovery efficiency = Table 4 quantum; Δp and SFP optional) credits `ahu_heat_recovery` → **AVAILABLE**.
  - *Remaining on user side*: provide the **AHU data sheet** (HVAC engineer) and enter it in the CSV.

- [x] ✅ **Ventilation control** — *ingestion done* (`5671e1b`): reviewer CSV `SIA3802_ventilation_control_<project>.csv` (single/multizone system type + control class + flow rate bracket ≤3 / 3-6 / >6 m³/h·m²) credits `ventilation_control` → **AVAILABLE**.
  - *Remaining on user side*: classify the system + control (HVAC engineer) and enter it in the CSV.

- [x] ✅ **Solar protection** — *ingestion done* (`2a78bef`): the reviewer CSV `glazing_solar_protection_<project>.csv` (protection type + g_total with blind = Table 10 quantum, per facade) is now scanned and credits `solar_protection` → **AVAILABLE**, but only when VE coverage **plus** reviewed windows reach all external windows (otherwise PARTIAL, never a silent pass).
  - *Remaining on user side*: model blinds in VE **or** document the blind outside VE (architect/facade engineer + g_total engineer) and fill in the CSV.

- [x] ✅ **Lighting control** — *best-effort credit wired (under reserve)* : a reviewer mapping `SIA3874_lighting_control_mapping_<project>.csv` covering lit rooms credits `SIA3802_LIGHTING_CONTROL` → **AVAILABLE UNDER RESERVE** (reviewer attestation; SIA 387/4 control tables absent → not an independent verification); without mapping → PARTIAL.
  - ⬜ *Remaining (source)*: **SIA 387/4:2023 (lighting control tables)** to lift the reserve. Contact: SIA Shop / Yiqiao Yang. Per-room values: electrician.

- [x] ✅ **Heating SCOP → NON_APPLICABLE** — *done* (`8d441b4`): a sized heating generator that VE does not classify as a heat pump (boiler) renders `SIA3802_HEATING_SCOP` **NON_APPLICABLE** (out of scope), instead of `NOT_CHECKABLE`. A heat pump without SCOP correctly remains `NOT_CHECKABLE` (genuine gap). Non-heat-pump generation efficiency goes through the global comparison.

### ⬜ Normative sources to acquire (unlock verdicts)
- [x] ✅ **SIA 387/4:2023 — table 9 + eq. 18-20** (solar protection control X=1/2/3, angle β) received from Yiqiao (2026-08-21) and **confirmed/frozen** (`cdac467`, editorial reserve lifted). Unlocks the **solar protection control** reference (test 2/2A). ⬜ *Nuance*: the **lighting** content of SIA 387/4 (installed power + presence/daylight control) is separate — check whether more is needed for `SIA3802_LIGHTING_CONTROL`.
- ⬜ **SN EN 14825** (heating SCoP) — standard access (cooling SEER already closed, `615e03f`). · **SN EN 15316-2 / 16798-13** (system energy) — standard access.
- [x] ✅ **SIA 180 Fig.3** — provided by Yiqiao (2026-08-20), **frozen** `348479e` (`chiffre_2_3_3_figure_3`). ZOER reserve lifted.
- ❌ **SIA 380 umbrella standard — national weighting factor** (annual index aggregation/weighting): **paid (purchase only), abandoned** (user decision 2026-08-20). No impact: the §7.2.5.2 weighted global index is **provided by the reviewer** (CSV `SIA3802_global_reference_comparison`), never computed by the tool.

### Audit indicators + verdict (2026-08-20)
- [x] ✅ **A3** — summer comfort (HIGH) made **blocking if confirmed** (`677b3dd`); **validated by norm-analyst** (autonomous requirement §7.1.2.1 → SIA 180). *Remaining*: cite "§7.1.2.1 → SIA 180" in the rule.
- [x] ✅ **A2** — honest category scores: NOT_CHECKABLE caps at 60 (`9cc68fc`).
- [x] ✅ **A1** — headline indicator renamed "coverage (diagnostic, ≠ compliance)" + verdict displayed at the top (awareness gate).
- [x] ✅ **A4 (norm-analyst) — decisive gate vs autonomous requirements §7.1**: §7.2.5.2 decisive + Table 2 entries = legitimate reserves; **autonomous §7.1** requirements gated (force `NOT_DETERMINED` if not verified): ventilation + summer (`677b3dd`) + **solar protection control §7.1.2.2-5** (`7e88404`). Product decision assumed (COMPLIANT becomes rarer). Detail: `traceability/audit-A4-verdict-porte-decisive-sia3802.md`.
- [x] ✅ **§7.2.4 (required electrical power)** — implemented + **gate decided by norm-analyst A5** (`11e3808`, `3d6d790`): **conditional autonomous** gate. Thresholds 7/12 W/m² (§7.2.4.2 p32). Exceedance + cooling **desirable** → NON_COMPLIANT; cooling **necessary** → non-blocking; indeterminate category / power not provided → NOT_DETERMINED; no installation → NOT_APPLICABLE. Reviewer path `SIA3802_electrical_power_<project>.csv` (+ `cooling_category`). Detail: `traceability/audit-A5-...md`.
- ⬜ **Thermal bridges `NOT_AVAILABLE`**: corrupt the project value of the comparison → case-by-case via reviewer attestation (the global CSV must confirm their integration).

### 🔶 To validate (independent)
- 🔶 **norm-analyst**: (a) ✅ decisive gate §7.2.5.2 + autonomous requirements §7.1 (2026-08-20); (b) **operative temperature** definition SIA 180 + θrm window + Fig.3; (c) window variants Test 2 / SIA 4010 Tests 2-7 criteria; (d) ✅ **§7.2.4 conditional gate** (A5, 2026-08-21).
- 🔶 **qa-auditor**: ✅ indicators+verdict batch A1-A4 **SIGNED** (`audit-lot-A1-A4-...matrix.md`); ✅ **§7.2.4 SIGNED** (`electrical-power-7.2.4.matrix.md`). Corrected after audit: R1 (negative power rejected) + R2 (unit ≠ W/m² rejected). ⬜ R3 (W/m² vs power/area reconciliation) + R4 (heuristic installation detection) = non-blocking improvements.
- 🔶 **Real VE qualification**: capability-check + per-value readback (beyond proven functionality).

---

## ✅ Done (audit remediation)

- [x] **P0.1** Test 7 — honesty flag `attestation_sous_commission_requise` (+ test)
- [x] **P0.2** SIA 380/2 COMPLIANT gate — sanity-check `project ≤ reference` + alert `SIA3802_GLOBAL_REFERENCE_DISCREPANCY` (+ tests)
- [x] **P0.3** SN EN 14825 caveat on client SEER/SCoP rules (+ test)
- [x] **P0.4** `validate_release.py` — honest ("does not run the suite") + matrix signature check
- [x] **P1** Documentary truth — `CLAUDE.md`, `CLAUDE_REFERENCE.md`, `README`, `PROJECT_PLAN.md`, `docs/project/INDEX.md`
- [x] **P2/P3 addendum** — global `engine/` purity guard; `.gitignore` += `sia4010_artifacts/`

---

## ✅ Client MVP — analysis & reports (done since initial drafting)

> Re-evaluated on 2026-08-19 against actual code (items below were marked to do; they are done).

- [x] **1. Framed PDF verdict** — `scope="sia3802"` + `normalize_report_scope`/`scoped_verdict_status`; 380/2-only report + one-click launcher. `compliance_report_pdf.py:594-681` *(commits `d01be83`, `d778d1a`, `6168949`)*
- [x] **3. Extraction gaps filled** in fail-closed mode with status/source/placeholder: `tau_v`, `frame_fraction`, `g_total`, `ventilation_installation_type`/`control_level`, `internal_gains_wh_m2_day`. `data_extractor.py`, `model_analyzer.py`
- [x] **4. Uncited mappings traced or set to `NOT_CHECKABLE`**: opening types (`_opening_type_audit`, placeholder `OPENING_TYPE_VE_ENUM_TO_VERIFY` + rule `SIA3802_OPENING_TYPE_NOT_CHECKABLE`); generator class (`cb67512`: no SCoP comparison outside heat pumps); `_select_best_model` actually uses body counts + diagnostics; `ashae` typo removed. *(commits `7526f01`, `edb611d`)*
- [x] **5. `compliance_score` labelling** — PDF does not display the score (status verdict only); HTML "NOT a compliance rate (§7.2.5.2)"; Excel "Weighted automated indicator only; it is not a full certificate".
- [x] **Dead SIA 4010 code removed** — `_calculate_co2_emissions` + `_calculate_renewable_energy_share` (never called) deleted + orphan `EMISSION_FACTORS` import. *(2026-08-19)*
- [x] **Client gains bridged via source templates** *(commits `8e4b4a9`, `592aa3a`, `680b9cf`)*; CSV dependency lifted by frozen SIA 2024:2021.

## 🔶 Client MVP — remaining (product decision, not just code)

- [ ] 🔶 **2. SIA 380/2 decisive gate (§7.2.5.2)** — automate the reference run **or** formalise the reviewer workflow as a documented deliverable. Phase A/B reference builder already in place (`b4d21b6`). `sia380_checker.py:390-485`, `reference_project.py`
- [ ] **SIA 4010 `score` inert (=0.0)** — structural: each branch sets 0 as long as official validation has not been achieved (ceiling `OFFICIAL_RESULTS_RECORDED`). Leave as-is (fail-closed) or remove the field.

## ✅ Client interface (done)

- [x] **Client compliance dashboard** — interactive sortable/by-section/justifications HTML, IESVE-styled. `compliance_report_html.py` + `compliance_report_html_template.py`
- [x] Wired to real results (`ComplianceVerdict` + alerts) via `app.py` — standalone `_dashboard.html` export alongside PDF/Excel
- [x] scope-aware (380/2-only banner); i18n FR/EN via `ui_translations.py`
- [ ] i18n DE/IT for the dashboard (FR/EN done)
- [ ] Real `ies_logo.png` (placeholder only on disk — **file to be provided**)

## 🔶 To decide (regulatory)

- [ ] **Summer comfort operative temperature** — the `.aps` exposes 4 definitions; the code reads "Dry resultant temperature" (`simulation_results.py:601`). To be decided by `norm-analyst` (risk of silent error). ADR-001 §3
- [ ] Window variant Test 2 (`Fe det Spec`/`non Spec`/`einf`); SIA 4010 Tests 2-7 criteria (INFERRED, sub-commission 4.6.2)

## ⬜ Normative sources to acquire (unlock checks)

- [ ] **SN EN 14825** → lifts the SEER/SCoP caveat
- [ ] **SIA 2024:2021 Raumdatenblätter** (primary source) → removes the reviewer CSV dependency for gains
- [ ] **SIA 387/4** → lighting control
- [ ] **SIA 180:2014** (complete, with corrigenda) → summer comfort
- [ ] **SIA 380 umbrella standard** → annual aggregation/weighting
- [ ] **SN EN 15316-2 / 16798-13** → system energy / design power

## ⬜ Unimplemented checks

- [ ] Thermal bridges (ψ/χ ingestion) — zero placeholder (`config.py:104`, `excel_report.py:4637`)
- [ ] Design power (design-day workflow) — `config.py:1894`

## ⬜ Structure & modularity (P2) — dedicated pass, ideally on branch after commit

- [ ] Remove `core/` (dead) + `examples/usage_repositories.py`
- [ ] Extract `ui/design.py`+`ui/tk_theme.py` to `swiss_sia`, remove dead duplicates from `ui/` (+ their tests)
- [ ] Tidy the ~91 root scripts → `scripts/probes/`, `scripts/legacy/` (keep ~9 production launchers)
- [ ] Break up god-modules: `excel_report.py` (7,027 lines), `native_ui.py`, `ve_asset_provisioner.py`, `config.py` (blob), `app.py::main`
- [ ] Isolate `engine/`+`ve_adapter/` under `tools/` with a README "tooling"
- [ ] Fix test isolation brittleness (double import `config` vs `swiss_sia.config` → unequal `Severity` enum)

## ⬜ Hygiene & data-handling (P3)

- [ ] `git rm --cached` tracked client data: `sia4010_evidence/*ZOER_32_C1_draft*.csv`, `outputs/*.pptx`, `sia4010_artifacts/*.json` *(already in history — a purge would be a separate decision)*
- [ ] Remove the 4 root files with Windows path names *(contain real SIA 2024 analysis — key finding preserved in memory; to be removed after confirmation)*
- [ ] Reports: real `ies_logo.png`; remove the 2 dead Excel sheets (`SUMMARY`, `ACTION PLAN`) + outdated comment
- [ ] Regenerate stale traceability matrices (`test-7.matrix.md` says the adapter is missing — false)
