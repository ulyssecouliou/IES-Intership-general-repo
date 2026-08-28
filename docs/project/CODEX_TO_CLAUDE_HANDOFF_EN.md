> **Note:** Translated from French original. See [CODEX_TO_CLAUDE_HANDOFF.md](CODEX_TO_CLAUDE_HANDOFF.md) for the source document.

# Codex-to-Claude Handoff -- SIA 380/2 and SIA 4010

**State as of:** 2026-08-24  
**Repository:** `C:\Users\ulysse.couliou\Documents\IES Internship\IES-Intership-general-repo`  
**Observed branch:** `sia4010-evidence-hardening-20260812`  
**Observed HEAD:** `7948c21`  
**Real VE environment:** IESVE 2025, Python VE 3.12.3  
**Local test environment for this handoff:** Python 3.13  
**Detailed continuation document:** `docs/project/CLAUDE_CONTINUATION_PROMPT.md` (state as of August 24, priorities P0-P4)

## 1. Mission and claim boundary

The target product is a set of VEScripts executable inside IESVE that:

1. extracts and checks a client model to prepare a SIA 380/2:2022 assessment;
2. creates, qualifies, simulates, and compares the SIA 4010:2023 validation cases;
3. produces auditable JSON/Excel/PDF evidence;
4. fails conservatively whenever a regulatory value, a VE binding, or evidence is missing.

The software currently produces diagnostics, readiness checks, and reference results. It must never present a model as certified or officially validated by SIA without applicable criteria, a complete evidence package, independent review, and the attestation required by the SIA procedure.

## 2. Absolute rules for takeover

- Read `CLAUDE.md` first, then `docs/CLAUDE_REFERENCE.md`.
- Never invent a regulatory, climatic, or physical value, a tolerance, or an `iesve` signature.
- Missing data stays `NOT_CHECKABLE`, `WARNING`, or `FAIL` -- never `PASS`.
- Do not confuse the SIA 4010 test climate with the application climate for a Swiss SIA 380/2 project.
- Every VE mutation must be preceded by a capability check and followed by a read-back.
- Tests using Python doubles do not replace qualification inside IESVE 2025.
- Never directly modify a frozen JSON under `refs/reference-data/`: modify its producer then regenerate it.
- Do not run `git reset`, `git checkout --`, a mass cleanup, or a general rewrite.
- Do not publish, push, open a PR, or transmit licensed documents without explicit authorization.

## 3. Git state to preserve

> **Update 2026-08-12.** This section previously described 168 unclean entries.
> That is no longer the state: this work has been grouped into commits on the
> `sia4010-evidence-hardening-20260812` branch, and `main` remains intact. The
> rule below remains valid for any future takeover -- re-read
> `git status --short` instead of relying on a count frozen in a document.

Permanent rule: uncommitted changes belong to the user and represent
multiple days of Codex/Claude development. Inspect
`git status --short` and targeted diffs before any modification, then
preserve all changes unrelated to the current task. A large diff
is not an invitation to reformat the repository: a single EPW weather
file alone is 8,760 lines long.

## 4. Recommended reading order

### Doctrine and architecture

1. `CLAUDE.md`
2. `docs/CLAUDE_REFERENCE.md`
3. this file
4. `README.md`
5. `docs/project/MVP_COMPLETION_MATRIX.md`
6. `docs/project/HYBRID_EXECUTION_STATUS_20260811.md`
7. `docs/project/TONIGHT_SIA4010_EXECUTION_RUNBOOK_FR.md`

### Machine-readable sources of truth

1. `config/sia4010_all_classes.json`
2. `config/sia4010_official_input_contract.json`
3. `config/iso52016_chapter7_confirmed_inputs.json`
4. `SIA_4010_geteilter_Link/official_manifest.json`
5. `refs/reference-data/*.json`
6. `sia4010_evidence/autonomy/sia4010_case_evidence.json`

### Active Test 1 chain

1. `Run_VE_SIA4010_Test1_Fast_Start.py`
2. `Run_VE_SIA4010_Test1_Active_Case_One_Click.py`
3. `Run_VE_SIA4010_Test1_Qualify_Runtime_Inputs.py`
4. `Run_VE_SIA4010_Simulate_Active_Case.py`
5. `swiss_sia/reference_model/sia4010/mvp_bundle.py`
6. `swiss_sia/reference_model/sia4010/test1_variant_bundle.py`
7. `swiss_sia/reference_model/sia4010/test1_runtime_inputs.py`
8. `swiss_sia/reference_model/sia4010/apachesim_qualification.py`
9. `swiss_sia/reference_model/sia4010/active_case_evaluation.py`
10. corresponding tests under `tests/`

## 5. Verified state of the SIA 4010 Test 1 campaign

The central ledger `sia4010_evidence/autonomy/sia4010_case_evidence.json`, updated on 2026-08-12 at 07:49 UTC, contains:

| Case | Model | Recorded simulation | APS evaluation | Metrics | Output scope |
| --- | --- | --- | --- | ---: | --- |
| `test_1/600` | `VERIFIED` | recorded | `REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION` | 88 | complete |
| `test_1/640` | `VERIFIED` | recorded | `REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION` | 88 | complete |
| `test_1/600FF` | `VERIFIED` | recorded | `REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION` | 39 | complete |
| `test_1/900` | missing | not started | `NOT_CHECKABLE` | -- | -- |
| `test_1/940` | missing | not started | `NOT_CHECKABLE` | -- | -- |
| `test_1/900FF` | missing | not started | `NOT_CHECKABLE` | -- | -- |

Projects and latest recorded evidence:

- 600: `C:\Users\ulysse.couliou\Documents\switzerland\test1_600`
- 640: `C:\Users\ulysse.couliou\Documents\switzerland\Test_640_Test1`
- 600FF: `C:\Users\ulysse.couliou\Documents\switzerland\SIA4010_TEST1_600FF`

The `REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION` status is intentional. The available ISO sources provide reference results for Test 1, but no decision band has been demonstrated in the project. Do not convert it to `PASS`.

## 6. Latest ongoing fix -- Test 1 mechanical ventilation

An anomaly was identified after the simulations above: the generic VE template could retain `system_air_minimum_flowrate = 10 L/s/person`, whereas Test 1 ISO has no mechanical ventilation; only the prescribed infiltration should remain active.

The current fix:

- forces the minimum system flow rate to `0.0`;
- disables template inheritance;
- verifies the read-back in the runtime qualification;
- blocks ApacheSim if the evidence or the actual VE state is no longer zero;
- preserves the separate infiltration at 0.41 ACH, approximately 14.76 L/s for the 129.6 m3 room.

Core files modified:

- `swiss_sia/reference_model/sia4010/mvp_bundle.py`
- `swiss_sia/reference_model/sia4010/test1_runtime_inputs.py`
- `Run_VE_SIA4010_Test1_Qualify_Runtime_Inputs.py`
- `swiss_sia/reference_model/sia4010/apachesim_qualification.py`
- `tests/test_sia4010_mvp_bundle.py`
- `tests/test_sia4010_test1_runtime_inputs.py`
- `tests/test_sia4010_apachesim_qualification.py`

Local verification performed during this handoff:

```text
python -m pytest -q tests/test_sia4010_mvp_bundle.py \
  tests/test_sia4010_test1_runtime_inputs.py \
  tests/test_sia4010_apachesim_qualification.py

31 passed
```

The fix has not yet been requalified by a new VE run recorded after its latest modification. The existing APS records for cases 600, 640, and 600FF are therefore technical baselines, not final evidence of this fix.

## 7. Exact next action in IESVE

> **Update 2026-08-12 -- this priority has been reached for 600FF.** The case was
> requalified after the fix: mechanical ventilation verified at zero after
> read-back, prescribed infiltration preserved, ApacheSim executed, APS
> `SIA4010_test_1_600FF_20260812_141823.aps` recorded in the ledger with its
> sha256. What remains for this case is solely the APS qualification
> (`SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION`).
>
> **Next priority**: requalify **640** then **600**, whose recorded APS records
> date from 2026-08-11 and 2026-08-09 respectively, i.e. before the fix
> `c7e906b` (2026-08-12 12:55) -- these are reference baselines, not citable
> results. Only then proceed to 900, 940, and 900FF.

Procedure, unchanged:

1. Open the corresponding saved throwaway project in IESVE 2025.
2. Execute in VEScripts:
   `Run_VE_SIA4010_Test1_Fast_Start.py`
3. Verify in the output evidence equivalent to:
   `Mechanical ventilation: 0 L/s/person, verified zero`
4. Verify that the prescribed infiltration is preserved. **To be reconciled**: this
   document announced 0.41 ACH / approximately 14.76 L/s, while the actual read-back
   of 600FF reported `max_flow = 0.3075` with `units_val = 2`. The two figures
   have not been reconciled and the unit behind `units_val = 2` is not
   demonstrated here: do not settle the matter, record the observed value and compare
   it to the specification before making it a criterion.
5. Verify that the qualified ApacheSim executes and produces a new APS.
6. Verify that the central ledger is updated with the new SHA-256 hashes.
7. Only after this run, execute cases 900, 940, and 900FF successively in separate throwaway projects.

If Fast Start fails, do not bypass the guardrail. Read the latest JSON under:

- `<project>/reference_model_artifacts/reports/`
- `<project>/sia4010_artifacts/diagnostics/`
- `<project>/sia4010_artifacts/simulation/`
- `<project>/apache/status.json`

## 8. Other Test 1 findings to preserve

- Case 640 produced significant deviations from ISO values; they are not resolved by preconditioning or by a constant setpoint.
- The continuous 200 W internal gain was verified in the model and in the APS: approximately 1,752 kWh/year.
- Infiltration was verified at approximately 14.76 L/s in the APS.
- Solar transport showed a deviation: VE south irradiation around 1,477 kWh/m2 vs. approximately 1,547.1 kWh/m2 ISO in a diagnostic; the experimental weather transport reduced but did not eliminate this gap.
- Observed APS convective coefficients differ slightly from ISO targets, and radiative coefficients were not resolved as APS variables.
- For controlled cases, the Apache input must demonstrate `RFCONT=0.5` in order to use operative/dry-resultant temperature. A 600FF run was initially blocked at `RFCONT=0`, then rerun after correction.
- The hourly convention diagnostic found better alignment with a +1 h APS offset and a +1,800 s `ResultsReader` offset; this still requires a documented binding decision before any normative hourly comparison.
- A/B experiments are diagnostics. They must not be entered as compliance evidence.

## 9. Tests 2 through 7 and validation classes

The product matrix covers eight classes and 24 exact variants in `config/sia4010_all_classes.json`. This means the framework knows the expected coverage; it does not mean that all VE models are generated or validated.

Execution state:

- direct routes primarily developed for the six ISO cases of Test 1;
- Test 2A has probes and partial preparation;
- **2026-08-12 -- Tests 3 and 4-7 probes are unblocked.** They refused to start without `sia_model_scenario.json` for an exact official case, and the only two scripted writers of this file were hardcoded for Test 1; the generic path existed only in the Tkinter dialog. [`Run_VE_SIA4010_Prepare_Case_Scenario.py`](Run_VE_SIA4010_Prepare_Case_Scenario.py) fills this gap in `PREPARE_ONLY` mode. The chain was dry-run outside VE before being proposed: `prepare_case_bundle` succeeds for `test_3A`, `test_4`, and `test_7` with status `PREPARED_WITH_BLOCKERS`, and the two probes then pass their scenario gate. Note: preparing a case in a project that already carries another case's scenario overwrites it -- the launcher refuses by default and requires `ALLOW_SCENARIO_REPLACEMENT = True`;
- Tests 2 through 7 still require real VE bindings, qualified templates, or demonstrated ApacheHVAC topologies;
- no qualified VE template was recorded in the latest hybrid status read;
- Tests 4 through 7 cannot be declared end-to-end executable until the exact networks are either generated with verified setters, or provided then captured and reviewed.

SIA clarifications received and already integrated:

- for the distributions of Tests 2, 3, and 5, the `Streubereich` is the min/max envelope of reference programs per class;
- out-of-bounds hours for classes explain sums below 8,760 in some tables; these references must not be modified;
- the corrected Test 7 workbook uses the lower bound and the upper bound;
- the required results for Tests 4, 6, and 7 are those listed in the Excel workbooks.

## 10. SIA 380/2 state

The client chain already knows how to:

- extract geometry, zones, envelope, windows, constructions, and part of the templates/profiles;
- produce diagnostics on U-values, glazing, ventilation, gains, lighting, and APS results;
- generate an audit/readiness Excel report;
- preserve unknown values as missing evidence rather than inventing them.

It does not yet constitute a fully automatic, self-contained SIA 380/2 reference project calculation. Remaining dependencies include, among others:

- validation of SIA 2024 usage categories and native schedules;
- controlled SIA 387/4 bindings for lighting;
- system/AHU/auxiliary details when not exposed in APS;
- reviewed climatic and building metadata;
- global project/reference comparison with the canonical indicator and its SIA 380 weighting;
- human review and evidence provenance.

The client demonstrator remains `Run_VE_Swiss_Compliance_Hub.py`, but older documentation may still refer to `Run_VE_Swiss_Compliance.py`. Check the current code before modifying the guides.

## 11. Tests to run before any delivery

Start with targeted tests for the modified area, then widen:

```powershell
python -m pytest -q tests/test_sia4010_mvp_bundle.py tests/test_sia4010_test1_runtime_inputs.py tests/test_sia4010_apachesim_qualification.py
python -m unittest discover -s tests -p "test_*.py"
python -m compileall -q swiss_sia scripts Run_VE_Swiss_Compliance.py Run_VE_Swiss_Reference_Model.py
python scripts/quality/validate_release.py
git diff --check
git status --short
```

A local pass does not close an `iesve` binding change. Add the actual IESVE 2025 run evidence and the read-back JSON path.

## 12. Recommended working strategy for Claude

1. Reproduce/inspect before editing.
2. Address one runtime blocker at a time.
3. Make a minimal change and add a non-regression test.
4. Ask the user only for runs that genuinely require IESVE.
5. After each run, read the JSON, identify the exact cause, and update the ledger only through existing interfaces.
6. Do not multiply A/B scripts if a property can be verified by deterministic read-back.
7. Do not optimize results toward a reference value by modifying physical parameters without a normative source.
8. Maintain an explicit distinction between `IMPLEMENTED`, `LOCAL_TESTED`, `REAL_VE_QUALIFIED`, `RESULTS_RECORDED`, and `OFFICIALLY_ACCEPTED`.

## 13. Realistic MVP completion criterion

The demonstrable MVP is reached when:

- the Hub opens and runs client checks without crashing;
- a client model produces a conservative and traceable SIA 380/2 report;
- the SIA 4010 cases announced as supported each have a throwaway model, a VE read-back, an APS simulation, a comparison, and checksums;
- unsupported tests appear clearly blocked with the required action;
- no missing criterion or evidence is turned into compliance.

The MVP must not promise that all seven tests or all eight classes are already 100% validated: the evidence state does not yet demonstrate it.
