> **Note:** Translated from French original. See [MVP_COMPLETION_MATRIX.md] for the source document.

# MVP Completion Matrix — factual state

**Date of establishment**: 2026-08-11
**Primary source of truth**: code + `config/sia4010_all_classes.json` + `refs/reference-data/*.json` + `sia4010_evidence/autonomy/sia4010_case_evidence.json` + `SIA_4010_geteilter_Link/official_manifest.json`.
**Scope**: seven SIA 4010:2023 tests (30 cases, including the separate diagnostic case 1E) + SIA 380/2:2022 readiness (eight axes).

This matrix is neither a certificate nor a commercial report. It documents the actual state of the repository, explicitly separating (a) Python tests, (b) real VE qualification, (c) recorded evidence/APS, (d) available official criterion. It is intended to serve as an executable backlog for closing out the MVP.

---

## Status vocabulary

| Status | Operational meaning |
|---|---|
| `NOT_STARTED` | No Python engine, no VE generator, no evidence. |
| `IMPLEMENTED_UNQUALIFIED` | Python engine present and tested in CI; no real VE run qualified. |
| `READY_FOR_REAL_VE` | VE generator or runtime-probe implemented and tested against fake `iesve`; only awaiting execution in VEScripts with real `iesve`. |
| `RESULTS_RECORDED_NO_CRITERION` | APS result extracted and recorded; the official acceptance criterion does not exist or has not yet been established (cases Test 1 other than 1E, Tests 4/6 without Testkriterien). |
| `READY_FOR_OFFICIAL_REVIEW` | Evidence, criterion, extraction and verdict formed; awaiting attestation by the SIA sub-commission. |
| `BLOCKED_BY_EXTERNAL_EVIDENCE` | Blocked by an external datum not provided (license, pending SIA response, value not stated by the source). The SIA 2028 climate is no longer part of this: it has been received, converted, validated and linked since 2026-08-12. |

No line can carry `PASS` / `VALIDATED`: SIA 4010 validation is an act reserved for the SIA sub-commission (SIA 4010:2023 §4.6.2).

---

## 1. SIA 4010 — Test 1 (7 cases, including 1E)

The Test 1 specification states its own criteria ([`Spezifikation_Test1.pdf`, section Testkriterien] cited verbatim in [engine/test1_engine.py:14-25](engine/test1_engine.py)). ~~Test 1 is the **only** test in this situation.~~ **False, corrected on 2026-08-12**: full-text search across the seven specifications — the `Testkriterien` section also exists in `Spezifikation_Test2.pdf` (p. 2/2), `Test3.pdf` (p. 3/3) and `Test5.pdf` (p. 5/5), and there it states the annual band **and** the distribution criterion. It is absent from the Test 4 and 6 specs (zero occurrences), and none of the seven **workbooks** contains this word — the section belongs only to the specifications. This erroneous belief had propagated into the five frozen references, into the producer, and into the interface; see resolution notes in §2, 3, and 5. Case **1E** is the only one with a pass/fail verdict (Streubereich over 4 reference programs). The six other cases are explicitly **without criterion** — the engine produces an informational delta per program. Weather = ISO 52016-1 DRYCOLD (Denver Stapleton); **not SIA 2028**. The weather file is provided and audited ([`refs/reference-data/iso-52016-1-climat-drycold.json`](refs/reference-data/iso-52016-1-climat-drycold.json)).

| Case | Requirement + source | Python implementation | Python test | VE generator (state) | APS recorded (this project) | Official criterion | Status | Next minimal action |
|---|---|---|---|---|---|---|---|---|
| **1E** *(diagnostic)* | Streubereich pass/fail over 4 programs. Source: `Spezifikation_Test1.pdf` Testkriterien | [engine/test1_engine.py](engine/test1_engine.py) — `CAS_AVEC_CRITERE=('1E',)`, `evaluer_periode_1e` | [engine/tests/test_test1_engine.py](engine/tests/test_test1_engine.py) + `test_ref_integrity.py` | `NOT_IMPLEMENTED` — no dedicated branch in [swiss_sia/reference_model/sia4010/case_registry.py:222-286](swiss_sia/reference_model/sia4010/case_registry.py); autonomy JSON confirms `mutation=False, runtime_qual=False` | No | STATED (Test 1 spec); reference FROZEN in [`refs/reference-data/test-1.ref.json`](refs/reference-data/test-1.ref.json) `CORRECTED_PASS_4` | `IMPLEMENTED_UNQUALIFIED` | **Five-link chain, now FROZEN** in [`refs/reference-data/test-1.diagnostics.ref.json`](refs/reference-data/test-1.diagnostics.ref.json) (producer: [scripts/build_test1_diagnostics_reference.py](scripts/build_test1_diagnostics_reference.py), 43 fields recorded and 0 to confirm (recounted on file on 2026-08-13), SHA-256 of three source PDFs). The spec writes: 1A = case 600 + Zurich-Kloten climate; 1B = +new window; 1C = +infiltration **0.15 m³/(h·m²)**; 1D = +SIA 2024 usage category **3.1 Einzel-Gruppenbüro**; 1E = +blind **Soltis 92-2048-Alu** (SergeFerrari), closed at **150 W/m²**, 1 cm air gap. Full window recorded with blind retracted/deployed (EN ISO 52022-3 summer and reference, EN 410): g<sub>tot</sub> 0.545 → 0.059. **SIA 2024 is NOT a blocker**: the required category is exactly the one from the authority extract of 2026-08-10 that we hold. ~~Remaining: register 1A-1D, link usage, generate.~~ **Done on 2026-08-13**: 1A through 1D are registered, generable and evaluable (see note below this table). Only **1E** remains blocked, and on a single point — the blind dynamics, request S2 to SIA. Its device and optical properties are frozen; it is the control rule that is missing |
| **600** *(6 normative cases — without criterion)* | Informational comparison to reference programs. Source: Testkriterien ("Es gibt dafuer kein Abweichungskriterium") | [engine/test1_engine.py](engine/test1_engine.py) — `comparer_periode_informative` | Same as 1E | `GUARDED_MUTATION_READY` — [case_registry.py:222](swiss_sia/reference_model/sia4010/case_registry.py) branch `case600_mvp_v1`; real APS and evaluation present in `sia4010_evidence/autonomy/sia4010_case_evidence.json` | **Yes, but pre-correction**: `switzerland\test1_600\Vista\SIA4010_test_1_600_20260809_235015.aps`, `observed_metric_count=88`, `simulation_link_status=VERIFIED` — from 2026-08-09, therefore **prior** to `c7e906b` (2026-08-12 12:55). Baseline, not citable as a result | No criterion (per spec) | `RESULTS_RECORDED_NO_CRITERION` | Requalify after ventilation correction, then **lock** the 600 pipeline as a non-regression reference |
| **640** | Informational (same as 600) | Same | Same | `RUNTIME_QUALIFICATION_READY` — generator `test1_lightweight_runtime_probe_v1`; blocker `VE_RUNTIME_QUALIFICATION_REQUIRED` | **Yes, but pre-correction**: APS `…_640_20260811_234852.aps`, from 2026-08-11, therefore **prior** to correction commit `c7e906b` (2026-08-12 12:55). `result_evidence = REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION`, but this is a **baseline to requalify**, not citable evidence | None | `READY_FOR_REAL_VE` | Requalify (runtime inputs + ApacheSim + new APS) as done for 600FF on 2026-08-12 |
| **900** | Informational (same as 600, high mass) | Same | Same | `RUNTIME_QUALIFICATION_READY` — generator `test1_heavyweight_runtime_probe_v1`. **Nothing to write**: [native_ui.py:242](swiss_sia/reference_model/sia4010/native_ui.py) already routes 900/940/900FF to `build_test1_runtime_probe_bundle`, and [test1_variant_bundle.py:277](swiss_sia/reference_model/sia4010/test1_variant_bundle.py) applies the high-mass envelope Table 24. The ledger already carries a `VERIFIED` geometry (`SIA4010_test_1_900.gbxml`) | No | None | `READY_FOR_REAL_VE` | Create a fresh VE project **saved in a folder named `..._TEST1_900`** (the case is inferred from the folder name, [Fast_Start:111-119](Run_VE_SIA4010_Test1_Fast_Start.py)) then launch Fast Start |
| **940** | Informational | Same | Same | `RUNTIME_QUALIFICATION_READY` — heavyweight | No | None | `READY_FOR_REAL_VE` | Same, folder `..._TEST1_940` |
| **600FF** *(free-float)* | Informational | Same | Same | `RUNTIME_QUALIFICATION_READY` — lightweight | **Yes, and POST-correction** — the only case in this state. Requalified on 2026-08-12: mechanical ventilation verified at zero after read-back, prescribed infiltration 0.3075 `units_val=2` preserved separately. APS `SIA4010_test_1_600FF_20260812_141823.aps`, sha256 `bcbb9deb…34f813`, 39 metrics; ledger entry written at 14:18:27 UTC, i.e. **after** correction commit `c7e906b` (12:55:25). Simulation executed, status `SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION` | None | `READY_FOR_REAL_VE` | Qualify the APS (last step of the chain for this case) |
| **900FF** | Informational | Same | Same | `RUNTIME_QUALIFICATION_READY` — heavyweight | No | None | `READY_FOR_REAL_VE` | Same, folder `..._TEST1_900FF`. Sorting by descending length ensures that `900FF` is recognized before `900` |

**Diagnostic cases 1A through 1D — registered on 2026-08-12, executable since 2026-08-13.** They were missing from the registry while 1E was in it, which left the only judged case of Test 1 without the base that its definition requires.

The blocker `TEST1_DIAGNOSTIC_CHAIN_GENERATOR_NOT_IMPLEMENTED` that they carried was **false**: `test1_diagnostic_bundle` was already applying the four frozen links and returning `READY_FOR_PROVISIONAL_RUNTIME_QUALIFICATION`. What was actually missing was elsewhere, and has been done:

| Actual gap | Correction |
|---|---|
| `config/sia4010_classes_1a_1b.json` did not declare the four cases or their exact parameters | Four blocks added, derived link by link: 1A = 600 with Kloten; 1B = +Test 2 glazing; 1C = +Test 2 infiltration; 1D = +SIA 2024 usage. Setpoints remain `test1_*`, no link modifies them |
| The role `zurich_kloten_dry_weather_file` remained `PLACEHOLDER_REQUIRED`, so the preflight rejected the mutation | `_bind_kloten_case_manifest_role` populates it with the resolved path and its fingerprint, in `CONFIRMED` status — not `CONFIRMED_NORMATIVE`, which would assert a line-by-line review that has not taken place |
| No APS evaluation path: the Test 1 path compares to **ISO** results, impossible here (Kloten climate, and zero reference in `test-1.ref.json`) | New scope `HOURLY_DELIVERABLE_ONLY_NO_REFERENCE` and dedicated branch that records the deliverable **without any comparison** |
| `Run_VE_SIA4010_Test1_Fast_Start.py` had a hardcoded case list | Extended to the four; 1E remains excluded, its blind dynamics are not stated |

State: `RUNTIME_QUALIFICATION_READY`, generator `test1_diagnostic_chain_probe_v1`, preflight `READY_FOR_VE_MUTATION` with zero missing parameters. They are the **only** cases whose inputs are all `CONFIRMED`: their climate comes from SIA, whereas the six ISO cases run on the public DRYCOLD.

### A compliance flag that flipped based on input quality

These four cases revealed it. `ModelScenario.readiness` computed `compliance_claim_allowed = is_official and not blockers and not provisional`: fully confirmed inputs were thus enough to authorize a compliance claim. The formula was safe only **by accident** — all cases carried at least one `PUBLIC_REFERENCE` input (the DRYCOLD climate), until the first fully confirmed case. For 1D, the scenario said `True` while its audit and asset manifest said `False`.

Two independent reasons made it wrong: these cases have **no criterion** to comply with, and complete inputs say nothing about a qualified generator, an executed simulation, or the sub-commission's attestation (§4.6.2). The field is now **always** `False` in a scenario, and the actually established fact is exposed under its true name, `official_inputs_fully_confirmed`.

| Case | APS evaluation field | Required delegated inputs | Status |
|---|---|---|---|
| **1A** | `UNAVAILABLE` — no criterion stated | ISO cell + Kloten climate | bundle `READY_FOR_PROVISIONAL_RUNTIME_QUALIFICATION` |
| **1B** | `UNAVAILABLE` | same as 1A | same |
| **1C** | `UNAVAILABLE` | + SIA 2024 (infiltration 0.15 is drawn from it) | same |
| **1D** | `UNAVAILABLE` | + SIA 2024 (usage) | same |

**Generator written and reachable from VE (2026-08-13).** [test1_diagnostic_bundle.py](swiss_sia/reference_model/sia4010/test1_diagnostic_bundle.py) applies the chain cumulatively, each value read back from the frozen reference — the module carries no normative constant. `prepare_supported_mvp_bundle` now routes the five cases; without this wiring the generator existed but nothing called it, and preparing 1A produced the generic fallback silently. Verified on 1D: climate `Zurich-Kloten - SIA 2028 DRY normal`, infiltration 0.15, glazing g 0.545 / Ug 0.654, appliances 11 W/m², lighting 12.5 W/m², occupants 68.6 W/person (4.9 W/m² × 14 m²).

The Kloten weather file is resolved **outside** the constructor — project, then VE Weather folder, then `generated_weather/KLO/` — because its location depends on the machine and a constructor whose result depends on it is not testable the same way twice. If not found, it **blocks**; it never leaves the Denver climate in place under a Kloten label.

**Normative point not to lose**: the specification requires for 1A-1D *annual datasets of hourly power* and states **no comparison criterion** — "Zu liefernde Resultate: Jahresdatensätze mit stündlicher Leistung Heizen und Kühlen". `test-1.ref.json` therefore carries no band for them, and none should be invented: these are **deliverables**, not judged cases. Only 1E is judged. Consequence on counters: 30 → **34 exact cases**, 8 classes and **24 variants unchanged** — these are `test_1` cases, not new variants.

**Incident diagnosed on 2026-08-12 — stale CDB material, not to be re-diagnosed.** The case 600 run failed on `VeMutationError: existing material xps_ground read-back mismatch: {'density': {'expected': 0.0, 'actual': 10.0}, 'specific_heat_capacity': {'expected': 0.0, 'actual': 1400.0}}`. This was **neither a code defect nor a manifest error**: the safeguard correctly refused to reuse a CDB material whose stored values no longer matched. Evidence chain: the project's local manifest declares `xps_ground` at density 0 / cp 0 (source NREL/TP-472-6231 BESTEST); the prior revision of the same file, `reference_model_assets.pre_glazing_calibration.json`, declared 10.0 / 1400.0 under the **same description** `SIA600_FLOOR_INSULATION`, and that is what created the material in the CDB. The authority settles it: [config/iso52016_chapter7_confirmed_inputs.json](config/iso52016_chapter7_confirmed_inputs.json) gives for the floor layer `ideal_floor_insulation` density 0, cp 0, surface heat capacity 0; the 10/1400 are those of `foam_insulation`, the **heavy wall** insulation. Both share conductivity 0.04, which explains the confusion. **Resolution**: correct the material in the VE construction database (density and specific heat to 0). VE persists 1e-6 and `ve_field_policy.VE_THERMAL_MASS_MINIMUM` already accepts this canonical value. No physical value was modified in the repository.

**Audit note**: the local paths in [`sia4010_evidence/autonomy/sia4010_case_evidence.json`](sia4010_evidence/autonomy/sia4010_case_evidence.json) point outside the repository (`C:\...\switzerland\test1_600\...`). Only the `test_1/600` entries have been inspected and actually carry verified artifacts; the other 29 entries carry the same field structure but the persistence of their artifacts at the same level is not guaranteed — to be confirmed by a file-existence audit before citing.

---

## 2. SIA 4010 — Test 2 (4 cases)

Class(es) covered: `1A` (case 2A), `1B` (2B, 2C, 2D), `2A` (2A), `2B` (2B-2D), `4A` (2A), `4B` (2B-2D). Kloten weather = **available and linked**: `KLO_dry.txt` carries the four solar columns (global horizontal, annual sum 1 105 564 Wh/m²; diffuse horizontal; direct normal; horizontal infrared), plus the south-facing vertical. The assertion "blocked by missing solar irradiance" that appeared here was false and had never been verified against the file; it was corrected on 2026-08-13. Criterion: annual band **+** hourly distribution; authority response `Streubereich = min/max of the programs` received on 2026-08-10 and integrated into [engine/sia_distributions_engine.py:11-19](engine/sia_distributions_engine.py).

| Case | Python implementation | Python test | VE generator | APS recorded | Official criterion | Status | Next minimal action |
|---|---|---|---|---|---|---|---|
| **2A** | [engine/sia_bandes_engine.py](engine/sia_bandes_engine.py) + [engine/sia_distributions_engine.py](engine/sia_distributions_engine.py); source-traced bundle Test 2A in [swiss_sia/reference_model/sia4010/test2a_source_bundle.py](swiss_sia/reference_model/sia4010/test2a_source_bundle.py) | `engine/tests/test_sia_bandes_engine.py`, `test_distributions_engine.py`, `test_references_bandes.py`, `test_distributions_ref.py`, `tests/test_sia4010_test2a_*` (10 files) | `NOT_IMPLEMENTED` mutation; `runtime_discovery_supported=True` + `source_bound_bundle_supported=True` ([case_registry.py:48-63](swiss_sia/reference_model/sia4010/case_registry.py)) | No | Annual band: `ENONCE_DANS_LA_SPEC` (engine); distribution: `CONFIRME_AUTORITE_2026-08-10`; reference FROZEN [`refs/reference-data/test-2.ref.json`](refs/reference-data/test-2.ref.json) + [`test-2.distributions.ref.json`](refs/reference-data/test-2.distributions.ref.json) | `IMPLEMENTED_UNQUALIFIED`; the three delegated inputs are `READY_FOR_BINDING` and the source bundle builds end-to-end, status `SOURCE_BINDINGS_PROVISIONAL_RECALCULATION_REQUIRED` with `verdict_derivation_allowed: false` | Recalculate the provisional IR emissivity from ISO EN 52016-1 clauses 7.2.2.7-7.2.2.10 (registry point I1), provide the native VE profile graph, then implement the VE 2A generator |
| **2B** | Same as 2A | Same | `NOT_IMPLEMENTED` | No | Same | Same | Same |
| **2C** | Same | Same | `NOT_IMPLEMENTED` | No | Same | Same | Same |
| **2D** | Same | Same | `NOT_IMPLEMENTED` | No | Same | Same | Same |

**Discrepancy resolved on 2026-08-12.** The frozen reference carried `critere.statut = "INFERE"` whereas the engine carried `ENONCE_DANS_LA_SPEC`. Settled from the official PDFs and not by aligning one file on the other: full-text search in `Spezifikation_Test2.pdf` — `Testkriterien` section **present**, page 2/2, stating the annual band verbatim. The engine was right; the producer `scripts/build_sia_reference.py` was writing a uniform `INFERE` and the false statement "only Test 1 states its criteria in its specification". References regenerated: only the two lines of the `critere` block change, `grandeurs` identical bit-for-bit. The same false text was displayed in the interface for all band tests ([verdict_view.py](ui/verdict_view.py)) — also corrected. Safeguard: [test_references_bandes.py](engine/tests/test_references_bandes.py) now compares reference and engine test by test, and fails if they diverge. The reference intentionally remains independent from the engine: it is the evidence against which the engine is judged.

---

## 3. SIA 4010 — Test 3 (12 cases)

Class(es): `2A` (3A-3F), `2B` (3A-3L), `4A` (3A-3F), `4B` (3A-3L). ~~Kloten weather = blocked (SIA 2028 solar).~~ **Climate received and installed on 2026-08-12** (see §10).

**Runtime probe executed in real VE 2025 on 2026-08-12** — first execution of this probe. Project `ZOER_32_C1_TEST`, scenario `test_3A/3A` prepared by [Run_VE_SIA4010_Prepare_Case_Scenario.py](Run_VE_SIA4010_Prepare_Case_Scenario.py). Verdict `SOURCE_BINDINGS_REQUIRED`: **20 observed lighting fields**, 4 sensor-related members, 12 exact variants audited. Report `sia4010_artifacts/diagnostics/sia4010_test3_runtime_capability_20260812_170256.json`. No model data modified. What this establishes: the VE API does expose the necessary surface; what is missing is not a VE capability but the **external source bindings** (SIA 2024 in particular). This is neither a validation nor a compliance claim.

| Case | Python implementation | Python test | VE generator | APS recorded | Official criterion | Status | Next minimal action |
|---|---|---|---|---|---|---|---|
| **3A**..**3L** (12 cases) | `sia_bandes_engine.py` + `sia_distributions_engine.py`; Test 3 bundle in [test3_source_bundle.py](swiss_sia/reference_model/sia4010/test3_source_bundle.py), runtime probe in [test3_runtime_capability.py](swiss_sia/reference_model/sia4010/test3_runtime_capability.py) | `engine/tests/test_sia_bandes_engine.py` (`(3, 12)`), `test_distributions_engine.py`, `test_references_bandes.py`, `tests/test_sia4010_test3_*` (3 files) | `NOT_IMPLEMENTED` mutation; `runtime_discovery_supported=True` + `source_bound_bundle_supported=True` | No | Annual band: `ENONCE_DANS_LA_SPEC`; distribution: `CONFIRME_AUTORITE_2026-08-10`; reference FROZEN in [`refs/reference-data/test-3.ref.json`](refs/reference-data/test-3.ref.json) (12 cases) + [`test-3.distributions.ref.json`](refs/reference-data/test-3.distributions.ref.json) (12 individual + 4 aggregates A-F, G-H, I-J, K-L) | `IMPLEMENTED_UNQUALIFIED` + `BLOCKED_BY_EXTERNAL_EVIDENCE` | VE Test 3 generator (lighting + internal gains + control factors) — climate is no longer a blocker |

**Discrepancy resolved on 2026-08-12.** The frozen reference carried `critere.statut = "INFERE"` whereas the engine carried `ENONCE_DANS_LA_SPEC`. Settled from the official PDFs and not by aligning one file on the other: full-text search in `Spezifikation_Test3.pdf` — `Testkriterien` section **present**, page 3/3, stating the annual band verbatim. The engine was right; the producer `scripts/build_sia_reference.py` was writing a uniform `INFERE` and the false statement "only Test 1 states its criteria in its specification". References regenerated: only the two lines of the `critere` block change, `grandeurs` identical bit-for-bit. The same false text was displayed in the interface for all band tests ([verdict_view.py](ui/verdict_view.py)) — also corrected. Safeguard: [test_references_bandes.py](engine/tests/test_references_bandes.py) now compares reference and engine test by test, and fails if they diverge. The reference intentionally remains independent from the engine: it is the evidence against which the engine is judged.

---

## 4. SIA 4010 — Test 4 (1 case)

Class(es): `3`, `4A`, `4B`. **No Testkriterien section** in `Spezifikation_Test4.pdf` — question 3 of the 2026-08-07 email (draft not sent) remains open. Kloten weather = blocked solar.

**Runtime probe Tests 4-7 executed in real VE 2025 on 2026-08-12** — first execution. Project `ZOER_32_C1_TEST`, scenarios `test_4/4` then `test_7/7` prepared by [Run_VE_SIA4010_Prepare_Case_Scenario.py](Run_VE_SIA4010_Prepare_Case_Scenario.py). Verdict `SOURCE_BINDINGS_REQUIRED` for both: Apache system collection observed, per-room system read-back observed, **29 HVAC-specific members**, 7 exact cases audited. Reports under `sia4010_artifacts/diagnostics/sia4010_tests4_7_runtime_capability_20260812_170438.json` and `..._170514.json`. No model data modified. What this establishes: the required ApacheHVAC surface is present in VE; the remaining blocker is external source binding and the distribution criterion, not a missing VE capability.

| Case | Python implementation | Python test | VE generator | APS | Official criterion | Status | Next action |
|---|---|---|---|---|---|---|---|
| **4** | `engine/sia_bandes_engine.py` (annual band only — no distribution: `TESTS_SUPPORTES=(2,3,5)`); temperature setpoints FROZEN in [`refs/reference-data/test-4.consignes.json`](refs/reference-data/test-4.consignes.json) | `engine/tests/test_references_bandes.py` (`(4, 3, 3)`), `test_construire_test4.py` (script outside engine) | `NOT_IMPLEMENTED` — blocker `VE_HEATING_COOLING_SETPOINT_BINDING_NOT_IMPLEMENTED` ([case_registry.py](swiss_sia/reference_model/sia4010/case_registry.py)) | No | `INFERE` (SIA 4010 §4.4 delegates to workbook); reference FROZEN [`refs/reference-data/test-4.ref.json`](refs/reference-data/test-4.ref.json) 3 quantities | `IMPLEMENTED_UNQUALIFIED` + `BLOCKED_BY_EXTERNAL_EVIDENCE` | (a) Send the 2026-08-07 email to confirm annual-band-only criterion; (b) implement VE generator (heating/cooling + SIA 380/2 fig. 1 setpoint curve) |

---

## 5. SIA 4010 — Test 5 (4 cases)

Class(es): `3`, `4A`, `4B`. Effective nomenclature **5A, 5B, 5C, 5D** — the identifiers "5.1..5.4" do not exist anywhere in the repository.

| Case | Python implementation | Python test | VE generator | APS | Criterion | Status | Next action |
|---|---|---|---|---|---|---|---|
| **5A**..**5D** (4 cases) | `sia_bandes_engine.py` + `sia_distributions_engine.py`; ventilation network frozen in [`refs/reference-data/test-5.reseau.json`](refs/reference-data/test-5.reseau.json) (statuses `RELEVE/A_CONFIRMER/RELEVE_SUR_GRAPHIQUE`) | `engine/tests/test_references_bandes.py` (`(5, 8, 16)`), `test_distributions_engine.py`, `test_reseau_ventilation.py` | `NOT_IMPLEMENTED` — blocker `VE_MECHANICAL_VENTILATION_BINDING_NOT_IMPLEMENTED` | No | Annual band: `ENONCE_DANS_LA_SPEC` (engine); distribution: `CONFIRME_AUTORITE_2026-08-10`; FROZEN [`refs/reference-data/test-5.ref.json`](refs/reference-data/test-5.ref.json) (16 quantity×case lines) + [`test-5.distributions.ref.json`](refs/reference-data/test-5.distributions.ref.json) (16 distributions; 1 without `cas` — documented reservation in the ref) | `IMPLEMENTED_UNQUALIFIED` + `BLOCKED_BY_EXTERNAL_EVIDENCE` | Implement ApacheHVAC bindings (heat recovery, coils, humidifier); qualify with dedicated probe `test4_7_runtime_capability_probe` |

**Discrepancy resolved on 2026-08-12.** The frozen reference carried `critere.statut = "INFERE"` whereas the engine carried `ENONCE_DANS_LA_SPEC`. Settled from the official PDFs and not by aligning one file on the other: full-text search in `Spezifikation_Test5.pdf` — `Testkriterien` section **present**, page 5/5, stating the annual band verbatim. The engine was right; the producer `scripts/build_sia_reference.py` was writing a uniform `INFERE` and the false statement "only Test 1 states its criteria in its specification". References regenerated: only the two lines of the `critere` block change, `grandeurs` identical bit-for-bit. The same false text was displayed in the interface for all band tests ([verdict_view.py](ui/verdict_view.py)) — also corrected. Safeguard: [test_references_bandes.py](engine/tests/test_references_bandes.py) now compares reference and engine test by test, and fails if they diverge. The reference intentionally remains independent from the engine: it is the evidence against which the engine is judged.
**Documented reservation**: one T5 distribution has no `cas` label in the workbook; the reservation appears in the JSON, do not "correct" it silently.

---

## 6. SIA 4010 — Test 6 (1 case)

Class(es): `3`, `4A`, `4B`. No Testkriterien section (same as Test 4 — question 3 of the 2026-08-07 email open).

| Case | Python implementation | Python test | VE generator | APS | Criterion | Status | Next action |
|---|---|---|---|---|---|---|---|
| **6** | `sia_bandes_engine.py` (annual band only); network frozen [`refs/reference-data/test-6.reseau.json`](refs/reference-data/test-6.reseau.json) | `engine/tests/test_references_bandes.py` (`(6, 6, 6)`), `test_reseau_ventilation.py` | `NOT_IMPLEMENTED` — blocker `VE_HVAC_HYDRAULIC_BINDING_NOT_IMPLEMENTED` | No | `INFERE`; reference FROZEN [`refs/reference-data/test-6.ref.json`](refs/reference-data/test-6.ref.json) 6 quantities | `IMPLEMENTED_UNQUALIFIED` + `BLOCKED_BY_EXTERNAL_EVIDENCE` | (a) Confirm annual-band-only criterion via SIA; (b) implement VE generator (network + hydraulic circuit) |

---

## 7. SIA 4010 — Test 7 (1 case)

Class(es): `4A`, `4B`, `5` (Test 7 is the only test for class `5`). PV + chiller + network.

| Case | Python implementation | Python test | VE generator | APS | Criterion | Status | Next action |
|---|---|---|---|---|---|---|---|
| **7** | [engine/test7_engine.py](engine/test7_engine.py) — dedicated engine 11 bands (5 cooling + 5 heating + 1 PV), Testgrössen vs Diagnosegrössen, PV/irradiance lock | `engine/tests/test_test7_engine.py`, `test_references_bandes.py`, `scripts/build_test7_reference.py` | `NOT_IMPLEMENTED` — blocker `VE_ENERGY_SYSTEM_BINDING_NOT_IMPLEMENTED` | No | `INFERE` per spec (no Testkriterien) **but** official workbook corrected by SIA on 2026-08-10 (conditional rule L8→N8) and audit recorded [`sia4010_evidence/source_audits/test7-corrected-workbook-20260810.json`](sia4010_evidence/source_audits/test7-corrected-workbook-20260810.json): `VERIFIED_CORRECTION_READY_FOR_TEST7_EVALUATION`. Reference FROZEN [`refs/reference-data/test-7.ref.json`](refs/reference-data/test-7.ref.json) dated 2026-08-10 (11 quantities, bands numerically identical after correction) | `IMPLEMENTED_UNQUALIFIED` + `BLOCKED_BY_EXTERNAL_EVIDENCE` | Implement the VE emission/distribution/storage/generation chain; extract the 11 annual quantities from APS |

---

## 8. SIA 4010 — view by validation class

Executive summary derived from [`config/sia4010_all_classes.json`](config/sia4010_all_classes.json). A class is never "validated" without sub-commission attestation — the "State" column only summarizes software coverage.

| Class | Required variants | VE-executed cases | VE generators ready | Overall state |
|---|---|---|---|---|
| **1A** | `test_1` + `test_2A` | 1 out of 8 (T1/600) | 6/8 (T1/600 mutation + 5 T1 runtime-probe) | Partial: Test 1 progressing; Test 2A has its three inputs linked, VE generator and emissivity recalculation remain |
| **1B** | `test_1` + `test_2B..2D` | 1 out of 10 | 6/10 | Same |
| **2A** | `test_1` + `test_2A` + `test_3A..3F` | 1 out of 14 | 6/14 | Delegated inputs linked; VE generators 2A and 3x to implement |
| **2B** | `test_1` + `test_2B..2D` + `test_3A..3L` | 1 out of 22 | 6/22 | Same |
| **3** | `test_1` + `test_4` + `test_5A..5D` + `test_6` | 1 out of 13 | 6/13 | Testkriterien 4/6 open (request S1); VE generators 4/5/6 to implement |
| **4A** | 15 variants | 1 out of 21 | 6/21 | Test 7 awaiting energy systems chain |
| **4B** | 23 variants | 1 out of 30 | 6/30 | Same |
| **5** | `test_7` | 0 out of 1 | 0/1 | Test 7 awaiting energy systems chain (emission, distribution, storage, generation) |

---

## 9. SIA 380/2 — readiness (eight axes)

All logic is carried by `swiss_sia/sia380_checker.py` (unit checks) + `swiss_sia/reference_project.py` (reference building specification). The application climate (CH2018 RCP 8.5 "2035" — SIA 4010 §3.1.1) remains **rule text** in the checker (no binary binding), and the question of the imposed choice on the SIA 380/2 compliance side is open (question 2 of the 2026-08-10 draft email). Each axis below has Python coverage tested in CI; none can be declared "qualified" without real VE execution + filled project CSVs.

| Axis | Carrying module | Python test | Required APS/data | Criterion | Status | Next minimal action |
|---|---|---|---|---|---|---|
| **Model / metadata / climate** | [swiss_sia/evidence_manager.py](swiss_sia/evidence_manager.py) `scan_sia3802_project_metadata` + [reference_model/client_weather_conversion.py](swiss_sia/reference_model/client_weather_conversion.py) | [tests/test_project_metadata_evidence.py](tests/test_project_metadata_evidence.py), `test_client_weather_conversion.py`, `test_sia4010_weather_conversion.py`, `test_sia4010_weather_verification.py` | CSV `SIA3802_project_metadata_<project>.csv` filled + CH2018 weather identified | New/existing status, altitude, weather file non-quantified tolerance | `IMPLEMENTED_UNQUALIFIED` + `BLOCKED_BY_EXTERNAL_EVIDENCE` (question 2 SIA on 380/2 climate) | Fill ZOER metadata, send 2026-08-10 email, generate the 4 ZOER climates via `generated_weather/GVE/` |
| **Envelope** (U, ff, thermal bridges) | `sia380_checker._check_envelope` + [reference_project.py](swiss_sia/reference_project.py) `build_reference_project_specification` | `tests/test_sia3802_normative_extensions.py`, `test_reference_project.py`, `test_reference_model_asset_provisioning.py` | VE constructions + `bs_en_410` glazing | Diagnostic vs Tables 2/3 SIA 380/2:2022; never standalone `FAIL` (design decided on global) | `IMPLEMENTED_UNQUALIFIED` (ZOER reports generated) | Post-real-VE: lock remaining `ff` (`STD_EXTW` ff=0.30, `STD_EXT2` ff=0.35 flagged in `OPEN_ITEMS_BACKLOG.md`) |
| **Ventilation** (flow rates, controls, recovery) | `sia380_checker._check_ventilation` + rule `SIA3802_VENTILATION_CONTROL_CLASS` | `tests/test_sia3802_normative_extensions.py::test_table_4_ventilation_control_pass_fail_and_missing` | Airflow, Table 4 control, recovery | Table 4 diagnostic | `IMPLEMENTED_UNQUALIFIED` | Complete `SIA2024_usage_mapping_<project>.csv` + AHU evidence (pressure drops, airtightness, verified recovery efficiency) |
| **Lighting** | `sia380_checker._check_gains` + rule `SIA3802_LIGHTING_POWER` + `evidence_manager.scan_sia3874_lighting_mappings` | `tests/test_sia3802_normative_extensions.py`, `test_solar_protection_logic.py` | VE lighting power + SIA 3874 control mapping | Readiness only (SIA 387/4 delegated) | `IMPLEMENTED_UNQUALIFIED` | Fill reviewer `SIA3874_lighting_control_mapping_<project>.csv`; attach Test 3 results after real VE |
| **Dynamic comfort** | `sia380_checker._check_dynamic_method` + rule `SIA3802_SUMMER_COMFORT_DYNAMIC` | `tests/test_sia3802_normative_extensions.py` | Annual APS temperature/occupancy series + SIA 180 upper/lower curves | 0 h upper for operable windows, otherwise 100 h new/400 h existing, 0 h lower | `IMPLEMENTED_UNQUALIFIED` | Fill metadata CSV, verify complete annual series per room, rule on window operability |
| **HVAC/DHW systems** | `sia380_checker._check_hvac`, `_check_hvac_metric`, `_check_setpoints` | `tests/test_sia3802_normative_extensions.py::test_hvac_eer_seer_and_scop_pass_fail_and_missing` | Generator class, capacity, EER/SEER/SCOP, Table 7 EER+ | Tables 5-9 SIA 380/2:2022 bands | `IMPLEMENTED_UNQUALIFIED` | Post-real-VE: complete EER+, auxiliaries, part-load; remove `SYST0000` unclassified on SIA_compatible_model |
| **APS results** | [swiss_sia/simulation_results.py](swiss_sia/simulation_results.py) + [runtime_inventory.py](swiss_sia/runtime_inventory.py) (untracked) | `test_iesve_extraction_contract.py`, `test_runtime_inventory.py`, `test_sia4010_aps_probe.py`, `test_sia4010_qualified_aps.py` | Complete `.aps` file, room-level variables | Extraction with units and conversions | `IMPLEMENTED_UNQUALIFIED` | On next VE Run, confirm exposed APS variables and probes `Run_VE_SIA4010_APS_Probe.py` + `Run_VE_SIA4010_Qualify_APS_Hour_Convention.py` |
| **Reference building comparison + evidence** | `reference_project.py` (spec) + `sia380_checker._check_global_reference_comparison` + `evidence_manager.find_accepted_global_comparison` | `tests/test_reference_project.py`, `test_project_metadata_evidence.py`, `test_evidence_bootstrap.py`, `test_claim_safety_extensions.py` | CSV `SIA3802_global_reference_comparison_<project>.csv` filled and signed | Compliance gate (never inferred from components) | `BLOCKED_BY_EXTERNAL_EVIDENCE` | Fill + have the CSV reviewed for ZOER; annual aggregation/weighting SIA 380 remains external |

**Design-day power** — appended: the 14-day preconditioning + 4-day heating / 3-day cooling selection is encoded but **`NOT_CHECKABLE` from annual peaks** (`OPEN_ITEMS_BACKLOG.md`). Status: `NOT_STARTED` for a real run — separate design-day APS files and variable mapping to produce.

---

## 10. Cross-cutting external blockers

| Blocker | Impact | Status | Origin |
|---|---|---|---|
| ~~**SIA 2028 DRY normal solar Zurich Kloten**~~ | ~~Blocks all 8 SIA 4010 classes~~ | **LIFTED on 2026-08-12.** `KLO_dry.txt` provided by SIA, imported as source-traced (`references/standards/sia2028/`, SHA-256 `aa3f3853…37ffd`), authenticated on four independent axes (annual mean 9.4692 °C and max 34.1 °C identical to an independent extraction, offset 0; dew point 0.538 K over 8760 lines; enthalpy 0.131 kJ/kg; absolute humidity 0.109 g/kg), converted to EPW and installed in VE. **Reservation**: 11 out of 24 columns remain `[TO VERIFY]` for lack of a published legend — see `KLO_dry.provenance.json`. IES does **not** hold a SIA 2028 license: this file is our only source. | External SIA — received |
| **380/2 climate basis for real building** | Blocks SIA 380/2 compliance on real building (Meteonorm/IWEC/TMY acceptable?) | Question 2 of same draft | External SIA |
| **Machine-readable SIA 2024** | Slows tests 2-6 (usage sheets transcribed from PDF) | Question 3 of same draft; partial workaround: authority extract cat. 3.1 (office) dated 2026-08-10 in [`sia4010_evidence/source_audits/sia2024_3_1_authority_20260810/`](sia4010_evidence/source_audits/sia2024_3_1_authority_20260810/) | External SIA |
| **Distribution criterion Tests 4, 6 and 7** | Distributions are extracted but produce no verdict: status `RESULTS_RECORDED_NO_CRITERION` | **Question reformulated on 2026-08-12.** Our previous assertion — "these workbooks have neither frequency classes nor distribution sheets" — was **false**, flagged by Prof. Zweifel. They do have them: sheet `Haeufigkeitskassen` (without the `l`, versus `Haeufigkeitsklassen` in Tests 2/3/5, which explains our blind spot), and the `Verteilung` sheets in them are **graphs** rather than spreadsheets. 38 distributions now frozen (T4 = 11, T6 = 10, T7 = 17). The remaining question: is the min/max rule confirmed on 2026-08-10 for Tests 2/3/5 enforceable here, when these workbooks carry no `Testkriterien` section and no cell computes a band? Verified draft: [`SIA_CORRESPONDANCE_ZWEIFEL_2026-08-12.md`](docs/project/SIA_CORRESPONDANCE_ZWEIFEL_2026-08-12.md) — **not sent** | External SIA |
| **Sub-commission attestation** | No class can carry `VALIDATED` before attestation | SIA 4010:2023 §4.6.2 | External SIA |
| **Real VE 2025 execution** | All T1/(640..900FF) cases and all Tests 2-7 not executable without real `iesve` | Every `RUNTIME_QUALIFICATION_READY` → `READY_FOR_REAL_VE` qualification | Internal, Ulysse's responsibility |
| **VE energy systems (Test 7)** | Emission/distribution/storage/generation not linked to a tested VE mutation pattern | Blocker `VE_ENERGY_SYSTEM_BINDING_NOT_IMPLEMENTED` | Internal, not scheduled |
| **ISO chapter 7 cell IR emissivity** | A provisional value of 0.90 makes Test 2A generable but not judgeable: blocker `DELEGATED_INPUT_CARRIES_PROVISIONAL_VALUE`, `verdict_derivation_allowed: false` | Answerable **internally** from the licensed copy of ISO EN 52016-1:2017, clauses 7.2.2.7 to 7.2.2.10 — see [`REGISTRE_DEMANDES_EXTERNES.md`](docs/project/REGISTRE_DEMANDES_EXTERNES.md) point I1 | Internal, Ulysse's responsibility |

### Two blockers that did not exist

Recorded because both would have been presented as real during a demonstration.

1. **"Kloten weather blocked by missing solar irradiance"** — false. `KLO_dry.txt`
   carries the four solar columns: global horizontal (annual sum
   1 105 564 Wh/m²), diffuse horizontal, direct normal, horizontal infrared,
   plus the south-facing vertical. The blocker had been lifted for Test 3 on 2026-08-12
   but the mention persisted in **twelve** other locations of this document —
   lines 20, 67, 84, 98, 108, 121, 131, 141, 143, 145, 146, 148 — including
   the status vocabulary legend itself. Corrected everywhere on 2026-08-13.
2. **"Interior surface coefficient not stated by the source"** — also false,
   and my doing this time. The source gives the three coefficients
   per orientation; it was the normalized contract that flattened them. Corrected by
   extending the contract, not by declaring a provisional value.

Both share the same cause as the previous errors in this project:
concluding from a comparison without verifying that it was about the right object.

### Two evidence-chain defects, in my own 2026-08-13 work

Neither would have been visible on this machine: both broke only
on another clone, i.e. at the time of third-party review.

| Defect | What would have happened | Correction |
|---|---|---|
| The weather binding artifact had been written to `generated_weather/`, excluded by `.gitignore:276` | On a fresh clone, Test 2A failed on `binding artifact is unavailable` — the binding was not in the repository | Moved to `references/standards/sia2028/`, with the report and the source. Reproducible producer added: [scripts/build_sia2028_kloten_binding.py](scripts/build_sia2028_kloten_binding.py) — it had been written by hand |
| The four artifacts carried absolute paths containing the username, where the already-tracked references carry **zero** | Unresolvable on any other machine | Relative paths everywhere. The reader resolves the binding relative to the **report** and the EPW relative to the **binding**: relative is thus the exact form, not a fallback |

The EPW itself remains outside the repository, and this is the intended convention
(`.gitignore`: regenerable derived artifacts). The binding now declares it
explicitly, with the command that regenerates it, instead of letting someone
discover a missing file.

---

## 11. SIA responses received (2026-08-10) — not to be forgotten

Three authority proofs were **received and integrated**; to be distinguished from the two unsent drafts:

- **Streubereich = min/max envelope of the programs** — written clarification from Prof. Gerhard Zweifel integrated into [engine/sia_distributions_engine.py:11-19](engine/sia_distributions_engine.py) and into each `test-*.distributions.ref.json` (`statut_critere = "CONFIRME_AUTORITE_2026-08-10"`).
- **Corrected Test 7 workbook** — the conditional rule changes from `$L8..$M8` to `$N8..$M8` (inclusive band `lower..upper`); numerical bounds identical; audit in [`sia4010_evidence/source_audits/test7-corrected-workbook-20260810.json`](sia4010_evidence/source_audits/test7-corrected-workbook-20260810.json). `.pre-correction` file preserved in `superseded_sources/Test7/`.
- **SIA 2024 category 3.1 (office)** — authority extract + binding + `PASS` validation in [`sia4010_evidence/source_audits/sia2024_3_1_authority_20260810/`](sia4010_evidence/source_audits/sia2024_3_1_authority_20260810/). Other categories remain to be manually transcribed from the SIA 2024:2021 PDF data sheets.

---

## 12. Documents that have become obsolete or incomplete since the receipt of official workbooks and the three authorities of 2026-08-10

These documents are preserved **as-is** (they retain historical and audit value), but must no longer be cited as source of truth for an implementation decision.

| Document | Reason for obsolescence |
|---|---|
| [docs/project/SIA3802_SIA4010_IMPLEMENTATION_STATUS.md](docs/project/SIA3802_SIA4010_IMPLEMENTATION_STATUS.md) | Prescribes `swiss_sia.sia4010_test_adapters` as the workbook integration boundary; the actual code now lives in `swiss_sia/reference_model/sia4010/` (52 modules, of which 12 modified and 2 untracked). The class table uniformly reports "Variant readiness only" whereas `case_registry.all_case_capabilities()` now distinguishes `GUARDED_MUTATION_READY`, `RUNTIME_QUALIFICATION_READY`, `NOT_IMPLEMENTED` per case. Completely ignores the untracked surface (`compliance_hub*`, `evidence_wizard*`, `remediation_probe`, `runtime_inventory`, `reference_model_setup*`, `hour_convention`, `test1_campaign`). |
| [docs/project/SIA4010_TESTS_AND_CLASSES_IMPLEMENTATION.md](docs/project/SIA4010_TESTS_AND_CLASSES_IMPLEMENTATION.md) | Cites `swiss_sia/sia4010_checker.py`, `swiss_sia/sia4010_prevalidation.py` as the implementation modules; the actual per-case logic has moved to `swiss_sia/reference_model/sia4010/*` (documented in `OPEN_ITEMS_BACKLOG.md:7` recently-closed 2026-07-23) but this document was never updated. Predates the arrival of official workbooks. |
| [docs/project/CLIENT_RUN_GUIDE.md](docs/project/CLIENT_RUN_GUIDE.md) | Designates `Run_VE_Swiss_Compliance.py` as the sole client entry point. The current strategy (cf. [`swiss_sia/compliance_hub.py`](swiss_sia/compliance_hub.py) and prompt 11 of `PROMPTS_CLAUDE_FIN_MVP.md`) makes `Run_VE_Swiss_Compliance_Hub.py` (untracked) the final demonstrator aggregating 6 workflows. The guide has not been updated. |
| [docs/project/SIA_MODEL_BUILDER_GUIDE.md](docs/project/SIA_MODEL_BUILDER_GUIDE.md) | The paragraph (§appendix config files) declares `config/sia4010_classes_1a_1b.json` "specialized Tests 1-3, plus global manifest" and points to `config/sia4010_all_classes.json`. The latter file does exist and covers the 8 classes. **Contradictory** with [docs/project/PROMPTS_CLAUDE_FIN_MVP.md](docs/project/PROMPTS_CLAUDE_FIN_MVP.md) which re-lists `sia4010_classes_1a_1b.json` as source of truth. Align by pointing to `sia4010_all_classes.json`. |
| [docs/project/OPEN_ITEMS_BACKLOG.md](docs/project/OPEN_ITEMS_BACKLOG.md) | Last "Recently Closed" entry dated 2026-07-23. Predates the reference freeze (2026-08-06), the Test 7 corrigendum (2026-08-10), the Streubereich clarification (2026-08-10) and the entire set of untracked launchers (Hub, Evidence Wizard, Remediation Probe, Reference Model Setup, Test 1 One-Click / Campaign Status / Weather AB / Convective AB, Compare Weather Transports, Qualify APS Hour Convention). Requires a "Recently Closed 2026-08" pass and an update of "Current High-Value Open Items". |
| [docs/project/SIA4010_FULL_COMPLIANCE_ANALYSIS.md](docs/project/SIA4010_FULL_COMPLIANCE_ANALYSIS.md), [SIA3802_FULL_COMPLIANCE_GAP_AUDIT.md](docs/project/SIA3802_FULL_COMPLIANCE_GAP_AUDIT.md), [WAITING_FOR_OFFICIAL_EXCEL_ACTION_PLAN.md](docs/project/WAITING_FOR_OFFICIAL_EXCEL_ACTION_PLAN.md), [SIA4010_OFFICIAL_PACKAGE_ACQUISITION_CHECKLIST.md](docs/project/SIA4010_OFFICIAL_PACKAGE_ACQUISITION_CHECKLIST.md) | Written before the arrival of the official SIA package (the 55 files listed in [`SIA_4010_geteilter_Link/official_manifest.json`](SIA_4010_geteilter_Link/official_manifest.json) are now present locally). Their scope "to do in order to obtain the package" is superseded. The pre-correction Test 7 workbook is in `sia4010_evidence/superseded_sources/`. |
| [docs/project/SIA4010_PDF_PREVALIDATION_STRATEGY.md](docs/project/SIA4010_PDF_PREVALIDATION_STRATEGY.md) | "Pre-qualification from PDFs alone" strategy developed before workbook receipt. Since then, values are extracted and FROZEN from the official xlsx files in `refs/reference-data/*.json` (status `FROZEN — bands recalculated and checked against workbook`). The PDF pre-qualification mechanism remains usable as a safety net, but is no longer the primary path. |
| [docs/project/SIA4010_CASE600_MVP_DEMO.md](docs/project/SIA4010_CASE600_MVP_DEMO.md), [SIA4010_TEST1_SIX_CASES_EXECUTION_GUIDE.md](docs/project/SIA4010_TEST1_SIX_CASES_EXECUTION_GUIDE.md) | To be verified line by line against the current `case_registry.py` and `sia4010_case_evidence.json`: the status nomenclature has evolved (`GUARDED_MUTATION_READY` / `RUNTIME_QUALIFICATION_READY`) and the APS content of `test_1/600` is now recorded in the autonomy ledger. |
| [docs/project/SIA_COMPLIANCE_MATRIX.md](docs/project/SIA_COMPLIANCE_MATRIX.md) | SIA 380/2 compliance matrix predating the per-case SIA 4010 engine and the clear distinction between readiness and validation. The present document (`MVP_COMPLETION_MATRIX.md`) takes over **on the MVP side**; the old matrix remains available for the detailed 380/2 axis. |

**What is NOT obsolete and remains a machine-readable source of truth**:
- [config/sia4010_all_classes.json](config/sia4010_all_classes.json) — 8 classes × 24 variants × cases.
- [config/sia4010_official_input_contract.json](config/sia4010_official_input_contract.json) — confirmed official inputs per test.
- [config/iso52016_chapter7_confirmed_inputs.json](config/iso52016_chapter7_confirmed_inputs.json) — Test 1 climate + geometry.
- [SIA_4010_geteilter_Link/official_manifest.json](SIA_4010_geteilter_Link/official_manifest.json) — 55 official SIA 4010 files with SHA-256.
- All JSON files under `refs/reference-data/` dated 2026-08-06 or 2026-08-10.
- Three authority proofs from 2026-08-10 (see §11).

---

## 13. Suggested battle plan for closing the MVP

This order is not prescriptive; it follows from the external/internal dependencies visible above.

1. **Send the two SIA draft letters** (`2026-08-07-questions-sia4010-EN.md` and `2026-08-10-donnees-sia-2028-EN.md`) after Johan's verification on the IES SIA 2028 license. Without a response, Tests 2-7 remain blocked.
2. **Align criterion statuses in `refs/reference-data/`**: `test-2.ref.json`, `test-3.ref.json`, `test-5.ref.json` carry `INFERE` whereas the engine categorizes them as `ENONCE_DANS_LA_SPEC`. Correct the producer (script under `scripts/`), not the output file.
3. **Execute the 5 Test 1 runtime-probes** (`640, 600FF, 900, 940, 900FF`) in a throwaway VE 2025 project, which depends on no SIA response (DRYCOLD Denver climate available).
4. **Update `SIA3802_SIA4010_IMPLEMENTATION_STATUS.md` and `OPEN_ITEMS_BACKLOG.md`** to incorporate the untracked surface (Hub, Evidence Wizard, Remediation Probe, Reference Model Setup, Hour Convention, Test 1 Campaign) and the 3 authority proofs from 2026-08-10.
5. **Align `SIA_MODEL_BUILDER_GUIDE.md` and `PROMPTS_CLAUDE_FIN_MVP.md`** to `config/sia4010_all_classes.json` as the single source of truth for the classes/variants/cases matrix.
6. **Subject to items 1 and 3**, implement in order: Test 2A (has the source bundle), then Test 3, then Test 5, then Tests 4/6, then Test 7.

*End of matrix. Any cell flagged `TO VERIFY` or any new SIA response must be reflected here at the same time as in the corresponding reference producer.*
