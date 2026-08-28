> **Note:** Translated from French original. See AUDIT_COMPLET_2026-08-16.md for the source document.

# Full Audit --- SIA Compliance / SIA 4010 Navigator

**Date:** 2026-08-16
**Branch audited:** `sia4010-evidence-hardening-20260812`
**Project resumption brief:** "as if starting from scratch, relying only on official sources, to build a Python program that, via the `iesve` library running in the VEScripts browser, generates a client report (client info + model + SIA compliance) --- and to verify the entire architecture, modularity, maintainability and optimization."

**Method.** Direct repository mapping by the lead auditor, then four independent expert audits conducted in parallel, each genuinely reading the code (no assumptions):
1. **Regulatory fidelity** (official sources, article citations, fail-closed verdicts);
2. **IESVE integration** (boundary between `iesve` and pure code, mutation safety);
3. **Architecture & dead code** (import graph, duplications, god-modules);
4. **QA / tests / traceability** (actual test suite execution, matrix signatures, claimed vs. proven).

No production file was modified during the audit itself. Pre-existing uncommitted changes were preserved.

> **Update --- remediation (2026-08-17).**
> **P0 (correctness & gates): DONE and verified** --- full suite green (exit 0).
> Honesty lock for Test 7 (`attestation_sous_commission_requise`); sanity-check
> `project <= reference` on the COMPLIANT gate + `SIA3802_GLOBAL_REFERENCE_DISCREPANCY`
> alert (M-COMP); SN EN 14825 caveat propagated on client SEER/SCoP (M-SEER); honest
> release gate ("don't run the suite") + matrix signature checks
> (C-REL). Non-regression tests added for each.
> **P1 (documentary truth): DONE** --- `CLAUDE.md`, `docs/CLAUDE_REFERENCE.md`
> section Layout, `README`, `PROJECT_PLAN.md` section 2 corrected (swiss_sia = sole production
> architecture; engine/ve_adapter = tooling; ui legacy; core dead); index
> `docs/project/INDEX.md` created.
> **P2/P3: additive gains completed** --- global `engine/` purity guard (closes the
> CI-only gap), `.gitignore` += `sia4010_artifacts/`. Remaining for a dedicated pass:
> deletion of `core/` + dead `ui/` duplicates, reorganization of the ~91 root
> scripts, god-module decomposition, and `git rm --cached` on tracked client data.
> **Minor finding discovered**: test isolation fragility --- dual import
> `config` vs `swiss_sia.config` causing `Severity` enum members to be unequal
> in certain test subsets (the full suite remains green because its
> import order canonicalizes the enum). To be fixed with the P2 pass.

---

## 0. Executive verdict

**You do not need to start from scratch. The program you describe already exists, and its regulatory core is solid and honest.** The chain `Run_VE_Swiss_Compliance.py -> swiss_sia/app.py` does exactly what you are aiming for: it opens the active VE project via `iesve`, extracts the model, runs the SIA 380/2 checks, prepares SIA 4010 readiness, computes a score, then produces **a client PDF report** (firm header, project/model identification, verdict by domain, model figures, scope block, signature --- bilingual DE/FR/IT/EN), an Excel workbook, and a ZIP evidence pack.

The #1 risk that the project's doctrine targets --- *"false but credible results"* --- is **genuinely controlled**: verdicts are fail-closed (`NOT_CHECKABLE`/`NOT_DETERMINED`, never `PASS` on missing evidence), SIA 4010 can never display "validated", no invented regulatory value drives a verdict, the `iesve`/pure boundary is clean, every VE mutation is framed by capability-check + read-back, and the suite of 2,305 tests is genuinely green (0 failures). This is serious engineering work.

**The real problem is not correctness --- it is readability and hand-over readiness.** The repository has accumulated **three parallel architectures**, **91 root scripts**, **god-modules** (up to 7,027 lines), **canonical documentation that describes the dead architecture as current**, and **~50 status documents** that overlap. An engineer taking over would be actively misled about *where the production logic lives*. On top of that, there are **four latent correctness/governance gaps** to seal before any commercial exposure (Test 7, SIA 380/2 compliance gate, release gate, "simulated != real VE" framing).

In a word: **the engine is sound, the bodywork is cluttered.** The plan in section 9 is consolidation and documentary truth work, not a rewrite.

---

## 1. Delivered product vs. your vision --- compliant

| Your vision | Actual state | Location |
|---|---|---|
| Python program in VEScripts (browser) | Verified --- Run-button launchers, native Tkinter dialog in VE | `Run_VE_Swiss_Compliance_Hub.py`, `swiss_sia/*_ui.py` |
| Via the `iesve` library | Verified --- `iesve` access isolated, lazy/injected, never in pure code | `swiss_sia/reference_model/ve_api.py`, `data_extractor.py` |
| Client report with **client/firm** info | Verified --- Header + signature from `company_profile.json`, never invented | `swiss_sia/compliance_report_pdf.py`, `company_profile.py` |
| ... **model** info | Verified --- Rooms, surfaces, opaque/glazed areas by orientation, WWR, diagram | `compliance_report_pdf.py::summarise_model` |
| ... **SIA compliance** | Verified --- Verdict by SIA 380/2 domain + SIA 4010 status, scope block "this is not a certificate" | `compliance_verdict.py`, `compliance_report_pdf.py` |
| Based solely on official sources | Verified --- Frozen values traced to primary SIA PDF (internal cell-by-cell audit) | `refs/SIA-380-2-2022.pdf`, `swiss_sia/config.py`, `traceability/audit-reference-project-2026-08.md` |

**Conclusion:** the functional target is met. The rest of this document addresses what makes it fragile.

---

## 2. Consolidated findings summary

Severity: **CRITICAL** = must be addressed before any commercial exposure; **MAJOR** = debt that will hurt during hand-over or for the client; **MINOR** = cleanup.

| ID | Axis | Severity | Finding | Location |
|---|---|---|---|---|
| **C-DOC** | Archi | CRITICAL | The canonical documentation (`CLAUDE.md`, `docs/CLAUDE_REFERENCE.md`, `README`) describes `engine/`+`ve_adapter/`+`ui/` as the current architecture --- but this is the **parallel/dead** architecture. It points a new maintainer to the wrong place. | `docs/CLAUDE_REFERENCE.md` section Layout, `README` |
| **C-T7** | QA/Engine | CRITICAL (latent) | The Test 7 engine sets `classe_5_validee = True` + `PASS` as soon as a candidate value exists, without any lock and without propagating the `INFERE` reservation. Neutralized only by the absence of a wired adapter --- but `ve_adapter/test7_adapter.py` (756 lines) now exists. | `engine/test7_engine.py`, test `engine/tests/test_test7_engine.py:287` |
| **C-REL** | QA/Release | CRITICAL | The documented release gate **never** runs the test suite and does not verify **any** matrix signature. A red suite or an unsigned matrix passes the gate. (Mitigated by CI, which does run everything.) | `scripts/quality/validate_release.py` |
| **M-SEER** | Regulatory | MAJOR | The client checker compares VE `SEER`/`SCoP` against SIA limits without the `[TO VERIFY]` SN EN 14825 equivalence caveat that `reference_project.py` does attach. The wording "meets the SIA limit" on an unproven basis, on a signed report. | `swiss_sia/sia380_checker.py:200-215`, `config.py:205-293` |
| **M-COMP** | Regulatory | MAJOR | The **only** gate to a `COMPLIANT` SIA 380/2 verdict trusts the reviewer flag `accepted` **without ever comparing** `project_value` to `reference_value`. A CSV with `accepted=yes` but non-compliant numbers would print "COMPLIANT". | `sia380_checker.py:404-410`, `compliance_verdict.py:204-221` |
| **M-SIM** | QA | MAJOR | All "qualification/runtime" evidence is against **hand-crafted API doubles**, never real VE. Legitimate and honestly labeled in the code, but the README ("verified guarded mutation path") could be read as real VE evidence. | `tests/test_sia4010_*_qualification.py`, `README:27-30` |
| **M-DUP** | Archi | MAJOR | Every output/UI layer is **duplicated** between the live (`swiss_sia`) and dead (`ui`/`engine`) implementations: Excel, PDF, band engine, Tkinter, i18n, Test 1/7 engines. Risk: editing the dead copy. | see section 5 duplication table |
| **M-SCRIPTS** | Archi | MAJOR | **91 `Run_VE_*.py` scripts** at the root, of which ~8-9 are real products buried among ~80 probes/throwaway scripts. `scripts/probes/` and `scripts/legacy/` conventions exist but are not enforced. | repository root |
| **M-GOD** | Archi | MAJOR | God-modules: `excel_report.py` (7,027 lines), `native_ui.py` (3,214), `ve_asset_provisioner.py` (3,179), `config.py` (blob 2,229), `app.py::main()` mixes extraction + 2 engines + APS + report + evidence. | see section 5 |
| **M-MATRIX** | QA | MAJOR | Traceability matrices stale vs. code: `test-7.matrix.md` declares the VE adapter **absent** and the files **unversioned** --- both are now false. Nothing gates their regeneration. | `traceability/test-7.matrix.md` |
| **M-DATA** | Hygiene | MAJOR | Client data tracked by git despite `.gitignore`: `sia4010_evidence/*.csv` (draft evidence `ZOER_32_C1`), `outputs/*.pptx`, `sia4010_artifacts/*.json`. Data-handling concern (client data in history). | see section 7 |
| **M-PUR** | IESVE/QA | MAJOR (robustness) | The `engine/` purity guard (0 `import iesve`) is exhaustive **only in CI**; locally each guard test covers only a single file. A new `engine` module importing `iesve` would pass the local suite. | `engine/tests/`, `.github/workflows/engine-tests.yml` |

**Minors** (detailed in the axis sections): inconsistent locator citations (`config.py:357` vs `1179`), bare QA tolerance numbers (`value_integrity.py` `1.05`, `0.02`), placeholder CO2 factors (`config.py:2169`), unguarded `assign_hvac_if_configured` (`ve_api.py:1744`), disposable guard in the launcher rather than at the mutation boundary, uncited integer-to-opening-type mapping (`data_extractor.py:1076`), stale boundary docstring (`ve_adapter/test1_adapter.py:4`), dead `core/`, 4 scratch files with literal Windows path names at the root, `sia4010_artifacts/` missing from `.gitignore`.

---

## 3. Axis 1 --- Regulatory fidelity

**Verdict: solid and honestly fail-closed. No critical findings.** No frankly invented regulatory value drives a verdict; the residuals are safeguards and honestly labeled placeholders.

**Verified strengths.**
- SIA 4010 comparator (`reference_model/sia4010/compliance_comparator.py:56-131`): `NOT_CHECKABLE` if observed value is missing, unit mismatch (no implicit conversion), or official tolerance is absent; official band takes priority; no invented tolerance.
- Fail-closed verdict (`compliance_verdict.py:122-266`): "unable to verify" alerts are indeterminate, never blocking; SIA 4010 caps at `attestation_required`.
- Global comparison required (`sia380_checker.py:412-425`): `NOT_CHECKABLE` + CRITICAL alert as long as no reviewed comparison is provided; component checks are LOW diagnostics.
- Summer comfort fail-closed (`sia380_checker.py:1081-1089`): missing `building_status` triggers an alert, no fallback to the lenient 400-hour allocation.
- Primary sources present: `refs/SIA-380-2-2022.pdf` and `refs/SIA-4010-2023.pdf` **are committed**; internal audit signing 22 values + ~110 constants cross-checked cell by cell, 0 divergence (`traceability/audit-reference-project-2026-08.md`).

**Majors: M-SEER, M-COMP** (see section 2).

**Minors.** Inconsistent 400-hour locator (`config.py:357` cites 3.2.4.3-4, `config.py:1179` cites 3.2.4.5); bare QA tolerances `1.05`/`0.02` to move into a traced dict (`value_integrity.py`); SIA 4010 readiness percolates into the *health score* (not the *compliance score*, which remains properly isolated); hard-coded CO2 factors but explicitly `PLACEHOLDER` and not consumed (`sia4010_checker.py:141` forces `None`).

**Unresolved external sources to trace** (outside code scope, blocking for lifting certain `[TO VERIFY]`): SN EN 14825 (SEER/SCoP index equivalence), SN EN 15316-2, SN EN 16798-13, SIA 2024:2021 Raumdatenblatter (primary source --- reference-project family 8 is **unsigned** for lack of source), SIA 180:2014 (partial captures), and SIA 4010 Tests 2-7 acceptance criteria (INFERRED, pending the sub-commission, art. 4.6.2).

---

## 4. Axis 2 --- IESVE integration

**Verdict: clean and defensible boundary; mutation safety among the most disciplined. No critical or blocking major findings.**

- **Zero `import iesve` at load time** in `engine/`, `ui/`, or the `swiss_sia` analysis modules: all VE access is lazy/guarded, confined to launchers, `ve_adapter/`, and the `swiss_sia/reference_model/` gateways.
- **Capability-gate before every mutation** (`workflow.py:260`, `ve_asset_provisioner.py:2959`), **immediate fail-closed read-back** afterwards (`ve_api.py:764-799`, 1663-1692, 1791-1814) that raises `VeMutationError` on any drift.
- **API members confirmed on the real VE 2025 runtime** (`ve_adapter/ve_api_surface.json`: `assign_construction`, `create_construction`, `assign_thermal_template_to_rooms`, `rebuild_adjacencies`...), not just documented.
- **Simulated != real, stated in the code** (`apachesim_qualification.py:320` "... does not prove ...").

**Minors to harden.** `assign_hvac_if_configured` replays the full read-back dict into the setter, unguarded/unwrapped (`ve_api.py:1744-1755`); disposable guard in the launcher (`Run_VE_SIA3802_Build_Reference_Model.py:181`) rather than at the `IesVeGateway` boundary, with no instruction to "discard the project on failure"; uncited integer-to-opening-type mapping (`data_extractor.py:1076`); stale docstring "the ONLY place that imports iesve" (`ve_adapter/test1_adapter.py:4`, false --- there are two VE layers); two `scripts/legacy/*` scripts import `iesve` outside the canonical VE directories.

---

## 5. Axis 3 --- Architecture, modularity, optimization

**Verdict: only one architecture is live; two others coexist with no declared hierarchy. This is the main barrier to hand-over.**

### 5.1 The story: an unfinished consolidation
ADR-001 section 8 (accepted 2026-07-30) records the merger of a **clean 4-layer skeleton** (`engine/`+`ve_adapter/`+`ui/`+`core/`) into an **already functional product** (`swiss_sia/`), with the explicit instruction to *carry the skeleton's rigor into the product, not rebuild*. This port was only half-done: the skeleton's directories were copied, but SIA 4010 work continued in `swiss_sia/reference_model/sia4010/` --- resulting in **two side-by-side SIA 4010 implementations**. ADR-001 additionally invalidates two doctrines still present in the docs: **D2 removes the web UI** (Tkinter only) and the VE 2025 probe **cancels the "Python 3.4" constraint** (it is 3.12.3).

### 5.2 Package liveness
| Package | LOC excl. tests | Production importers | Status |
|---|---|---|---|
| `swiss_sia/` | **74,046** | 77 | **LIVE** --- 100% of client entry points |
| `ui/` | 4,974 | 4 | **SPLIT** --- only `design.py`+`tk_theme.py` (style tokens) are used; the rest is dead |
| `ve_adapter/` | 3,762 | 5 | **TOOLING** --- imported by `scripts/` (ref build + Test 1 probes), zero from `swiss_sia` |
| `engine/` | 2,007 | 5 | **TOOLING** --- independent recompute (ADR-001 section 4.2) + `refs/reference-data/` build |
| `core/` | 859 | 1 | **DEAD** --- sole importer = `examples/usage_repositories.py` |

> **Important nuance (verified by the lead auditor).** `engine/`+`ve_adapter/` **cannot be deleted as-is**: `engine/*` reads `refs/reference-data/` and is imported by `scripts/build_sia_reference.py`, `build_test7_reference.py`, `build_traceability_matrix.py`, `autotest_chaine.py` which **regenerate** the frozen JSON consumed at runtime by `swiss_sia`. This is load-bearing **build & independent verification tooling** -> to be **requalified and isolated** (e.g. under `tools/reference_build/`), not discarded. Only `core/` and the non-style half of `ui/` are truly deletable.

### 5.3 Duplications (live vs. dead/parallel)
| Function | Live (`swiss_sia`) | Dead/parallel duplicate |
|---|---|---|
| Excel export | `excel_report.py` (7,027) | `ui/excel_export.py` (334) |
| PDF export | `compliance_report_pdf.py`+`pdf_writer.py` | `ui/export_pdf_reportlab.py`+`ui/verdict_view.py` |
| Band/dispersion engine | `reference_model/sia4010/distribution_reference.py`+`frequency_distribution.py` | `engine/sia_bandes_engine.py`+`sia_distributions_engine.py`+`scatter_band.py` |
| Tkinter UI | `native_ui.py`+`compliance_hub_ui.py`+... | `ui/dialog_tkinter.py`+`verdict_view.py`+... |
| i18n | `reference_model/sia4010/ui_translations.py` (2,155) | `ui/i18n.py` (321) |
| Test 1/7 evaluation | `reference_model/sia4010/test1_*` | `engine/test1_engine.py`+`ve_adapter/test1_adapter.py` |

### 5.4 The 91 root scripts (15,354 lines)
| Category | Count | Target |
|---|---|---|
| Real product launchers | ~8-9 | stay at root |
| Probes / introspection (`Probe`, `Sonde`, `Inspect`, `Diagnostic`) | ~32 | `scripts/probes/` |
| Anwenderbericht reports (`_AB.py`) | 6 | `scripts/probes/` |
| Qualification/`Verify`/`Compare`/`Reconcile`/`Calibrate` | ~15 | `scripts/probes/` or `scripts/legacy/` |
| Case600 scaffolding | 9 | `scripts/legacy/` |
| One-offs `Create_Missing`/`Repair`/`Resume`/`Prepare` | ~14 | `scripts/legacy/` |

Product launchers to keep: `Run_VE_Swiss_Compliance_Hub.py`, `Run_VE_Swiss_Compliance.py`, `Run_VE_Swiss_Compliance_Remediation_Probe.py`, `Run_VE_SIA3802_Approved_Template_Remediation.py`, `Run_VE_Swiss_Reference_Model_Setup.py`, `Run_VE_Swiss_Compliance_Evidence_Wizard.py`, `Run_VE_SIA_Model_Builder_UI.py`, `Run_VE_SIA3802_Build_Reference_Model.py`, `Install_SIA_Weather_Into_VE.py`.

### 5.5 Optimization
Execution performance is **not** the critical axis (the tool runs once per model in VE; dominant costs are VE extraction and ApacheSim simulation, outside our code). The useful "optimization" here is **structural**: decomposing the god-modules (section 2 M-GOD), extracting `_collect_dynamic_results` (~300 lines) from `app.py`, externalizing the `config.py` data blob (2,229 lines, 0 def) into traced data files, and splitting `excel_report.py` by sheet. Measured side effect on tests: the suite drops from 17 s to 4.5 s without the workbook (cell footprint) --- a good reflex already in place.

---

## 6. Axis 4 --- QA, tests, traceability

**Verdict: genuinely green suite and exceptionally honest discipline. The gap between claimed and proven is small and disclosed.**

- **2,305 distinct tests** (3,855 with unittest subTests), **3,851 passed, 0 failures, 0 errors, 4 environmental skips**. 100% runs **without `iesve`**. CI (`.github/workflows/engine-tests.yml`) runs the full suite + an anti-`import iesve` grep on `engine/`.
- **0/7 SIA 4010 matrices signed** --- and this is **acknowledged**: each `traceability/test-N.matrix.md` is explicitly "UNSIGNED". The only signature in the repository (`audit-reference-project-2026-08.md`) covers the **SIA 380/2 reference-project builder** (families 1-7), **not** the SIA 4010 tests --- do not confuse these in communications.
- Anti-false-positive discipline **tested**: no `VALIDATED` class without official PASS, `OFFICIAL_FAIL` overrides `OFFICIAL_PASS`, the autotest self-asserts "does not prove anything about IESVE".

**Criticals: C-T7, C-REL** (see section 2). **Majors: M-SIM, M-MATRIX, M-PUR.**

**SIA 4010 test table**
| Test | Matrix signed? | Unit tests? | Qualification |
|---|---|---|---|
| 1 | NO | Yes (ref-data audited) | **Simulated** (doubles) |
| 2 | NO | Yes | Simulated |
| 3 | NO | Yes | Simulated |
| 4 | NO (criterion INFERRED) | Yes | Simulated |
| 5 | NO | Yes | Simulated |
| 6 | NO (criterion INFERRED) | Yes | Simulated |
| 7 | NO (matrix **returned**, criterion bug) | Yes but 1 tautological test + open defects | Simulated (adapter present, never executed in VE) |

---

## 7. Hygiene & data-handling

- **Client data in git history** (M-DATA): `sia4010_evidence/*.csv` (draft evidence `ZOER_32_C1`), `outputs/*.pptx`, `sia4010_artifacts/*.json` remain **tracked** despite `.gitignore` (committed before the catch-up). -> `git rm --cached` required; draft client evidence in the history is sensitive.
- **4 scratch files with literal Windows path names at the root** (untracked, not in `.gitignore`) --- written by mistake by a tool into the root. -> to be deleted.
- `sia4010_artifacts/` **missing from `.gitignore`**; `.gitignore` itself was retroactively added (comment "821 MB not ignored") = evidence that large outputs were historically committed.
- **Excessive documentation**: ~50 files in `docs/project/` with overlapping names (`MVP_COMPLETION_MATRIX`, `MVP_MANAGER_HANDOFF`, `MVP_RUSH_RUNBOOK`, `TONIGHT_..._RUNBOOK`, `HYBRID_EXECUTION_STATUS`, `SIA_COMPLIANCE_EXECUTION_TRACKER`...). Historically useful, unmanageable for a hand-over.

---

## 8. What is already excellent (to preserve, do not "over-correct")

1. The **fail-closed doctrine** is real, not cosmetic --- this is the product's main asset.
2. The **`iesve`/pure boundary** and **mutation safety** (capability + read-back) are exemplary.
3. The **client PDF report** is polished, bilingual, and refuses to invent.
4. The **frozen reference data** is traced to the primary PDF and verified cell by cell.
5. The **QA honesty** (unsigned matrices acknowledged, "simulated != real" stated in the code) is exactly what an audit wants to find.

---

## 9. Prioritized remediation plan

> Principle: **documentary truth and correctness gaps first** (low cost, high impact), structure next, cosmetics last. None of these actions require starting from scratch.

### P0 --- Correctness & governance (before any commercial exposure)
- **C-T7** --- Lock `engine/test7_engine.py`: `classe_5_validee`/`PASS` impossible without confirmed official criterion; propagate the `INFERE` reservation to the boolean; fix defects m1 (string candidate -> proper rejection, `NaN` -> `NOT_CHECKABLE`, unit confronted). Non-regression test that **fails** if a bare candidate produces `True`.
- **M-COMP** --- In `_check_global_reference_comparison`, **compare `project_value` to `reference_value`** after acceptance; downgrade to `NOT_COMPLIANT`/`WARNING` if the direction contradicts `accepted`; clarify the semantics of `accepted` in the CSV template and the PDF. Test the contradiction `accepted=yes` but `project > reference`.
- **M-SEER** --- Propagate the caveat `[SEER/SCoP per SN EN 14825 --- VE index equivalence TO VERIFY]` into `SIA3802_COOLING_SEER_MIN`/`SIA3802_HEATING_SCOP_MIN`, or align the client checker with `reference_project.py` (full-load EER). Add `source`/placeholder status to the 4 `config.py:205-293` tables.
- **C-REL** --- Either make `validate_release.py` a real gate (run the suite + verify matrix signatures/freshness), or rename/document it honestly for what it does, and **designate CI as the authoritative release gate**.

### P1 --- Documentary truth (highest hand-over leverage, low cost)
- **C-DOC** --- Rewrite `CLAUDE.md`, `docs/CLAUDE_REFERENCE.md` section Layout, and the `README` table to **acknowledge `swiss_sia/` as the sole production architecture**. Requalify `engine/`+`ve_adapter/` as "reference-data build & independent verification tooling" (see section 5.2). Remove the "Layer 4 web app" from `PROJECT_PLAN.md` (removed by ADR-001 D2) and the Python 3.4 constraint.
- **M-MATRIX** --- Regenerate the stale `traceability/*.matrix.md` files (Test 7: adapter present, files versioned) or gate their regeneration; clearly distinguish "signed" (SIA 380/2 builder) from "unsigned" (SIA 4010 tests).
- **M-SIM** --- Rephrase README sections 27-30: "**guarded mutation paths, verified by read-back against API doubles** --- **real VE qualification pending**". Ban "verified" without qualifier in any manager/client communication.
- **Docs** --- Create a single `docs/project/INDEX.md`, archive the ~40 dated runbooks under `docs/project/archive/`, keep 5-6 living documents (architecture, status, hand-over, client guide, plan).

### P2 --- Structure & modularity
- **M-SCRIPTS** --- Move ~80 root scripts to `scripts/probes/` and `scripts/legacy/`; keep only the ~9 product launchers (section 5.4). A root `README` listing these 9.
- **M-DUP / dead core** --- Delete `core/`; extract `ui/design.py`+`ui/tk_theme.py` into a small style module in `swiss_sia`, then delete the dead `ui/` duplicates; isolate `engine/`+`ve_adapter/` under `tools/` with a `README` saying "tooling, not product".
- **M-GOD** --- Decompose `excel_report.py` (7,027) by sheet/section; extract `_collect_dynamic_results` from `app.py` into `swiss_sia/dynamic_results.py`; externalize the `config.py` blob into traced data files.
- **M-PUR** --- Add a single local guard that scans **all** `engine/` modules (not one by one), to catch a purity regression before push.

### P3 --- Hygiene & data-handling
- **M-DATA** --- `git rm --cached` on `sia4010_evidence/*.csv`, `outputs/*.pptx`, `sia4010_artifacts/*.json`; add `sia4010_artifacts/` to `.gitignore`; consider a history purge if the client drafts are sensitive.
- Delete the 4 scratch files with Windows path names at the root.
- Clean up the remaining minors (locators, bare tolerances, `assign_hvac_if_configured`, opening-type mapping).

---

## 10. Audit reproducibility

```powershell
python -m pytest                                  # 2305 tests, 0 failures (Python 3.13, iesve absent)
python -m unittest discover -s tests -p "test_*.py"
python scripts/quality/validate_release.py        # local gate (see C-REL)
git ls-files | wc -l                              # 740 tracked files
```

Key figures: 475 Python files (excl. `tmp/`), 156 test files, 91 root launchers, `swiss_sia/` = 74,046 lines, 0/7 SIA 4010 matrices signed, 2 primary SIA sources committed.

---

*Audit conducted by a team of four independent expert auditors (regulatory fidelity, IESVE integration, architecture, QA) and synthesized by the lead auditor. No production file modified.*
