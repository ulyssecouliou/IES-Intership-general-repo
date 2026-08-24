# Swiss Compliance Workbench — Client Demo Runbook

## 1. Demo objective

Demonstrate a working IESVE-native workflow that:

1. audits an existing client VE model without changing it;
2. records missing assumptions and evidence instead of inventing values;
3. produces an auditable SIA 380/2 pre-check report;
4. prepares exact SIA 4010 verification cases from checksum-controlled sources;
5. creates, simulates, extracts and evaluates the currently qualified cases;
6. exposes every remaining blocker explicitly.

The correct product claim is:

> The client-model compliance workflow is demonstrable end to end. The SIA 4010
> verification laboratory has complete case/source coverage and a working Test 1
> execution path. Remaining work is concentrated in qualified VE engine bindings
> and official acceptance gates, not in the core architecture.

Do **not** claim SIA certification, full SIA 380/2 compliance, or completion of all
SIA 4010 software tests.

## 2. Files to use

### Primary client model

Open:

`<VE_PROJECTS>\ZOER_32_C1_TEST\ZOER_32_C1_TEST.mdl`

Purpose:

- demonstrate the real-client, read-only audit path;
- show that the tool finds both valid content and actionable gaps;
- generate fresh English diagnostic output.

Known last audited state:

- 4 rooms;
- 81 significant external surfaces correctly classified;
- 150 windows with usable whole-window thermal data;
- daily gain profiles resolved;
- readable APS and annual heating result;
- remaining warnings for ventilation definition, lighting gains, missing APS
  end-use outputs and reviewed weather metadata.

### Primary SIA 4010 model

Open:

`<VE_PROJECTS>\Test_640_Test1\Test_640_Test1.mdl`

Purpose:

- demonstrate an exact Test 1 case (`test_1/640`);
- show the model + ApacheSim + APS + evaluation evidence chain;
- open the English SIA 4010 Model Builder and its exact-case selector;
- rerun the APS evaluation safely if required.

Current local evidence includes a model audit without failing controls, an annual
APS file and 88 extracted metrics. The official material available to the tool does
not define a pass/fail acceptance band for this reference-results table, so the
correct status is `REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION`, not PASS.

### Optional free-floating model

Open only if time allows:

`<VE_PROJECTS>\SIA4010_TEST1_600FF\SIA4010_TEST1_600FF.mdl`

Purpose:

- show the free-floating Test 1 route;
- demonstrate temperature-result extraction without ideal heating/cooling;
- show that the same evidence architecture supports a different physical case.

### Model not recommended for the live demo

Do not use `test1_600` as the main demonstration model unless a fresh run replaces
its current latest `reference_model_report.json`. Its latest report is FAIL because
of an interrupted repair workflow, even though older APS evidence exists.

## 3. Main launcher

In IESVE VEScripts select and run:

`Run_VE_Swiss_Compliance_Hub.py`

The window title is **IES Swiss Compliance Workbench — MVP Demonstrator**. The UI
is English and is divided into:

- Client model workflow;
- SIA 4010 verification laboratory;
- Advanced / controlled model creation.

The VEScripts terminal remains busy while the window is open. This is normal Tk
event-loop behaviour, not a crash. Close the window or select an action to complete
the run.

## 4. Exact live-demo sequence

### Part A — client model pre-check (3 minutes)

1. Restart VE to clear any stale VEScripts interpreter state.
2. Open and save `ZOER_32_C1_TEST.mdl`.
3. Run `Run_VE_Swiss_Compliance_Hub.py`.
4. Point out the three top tiles:
   - client checker demo-ready;
   - 34/34 official cases catalogued;
   - 1 guarded generator + 9 runtime qualification routes.
5. Point out **Active Project Readiness** and the fail-closed claim boundary.
6. Click **Run audit**.
7. In the terminal, show the PASS/WARNING controls and the generated JSON/TXT paths.
8. Explain that warnings are project findings, not software failures.
9. If time allows, reopen the hub and show **Complete project evidence** and
   **Generate auditable report**. Do not invent or accept metadata during the live
   meeting.

For a controlled remediation demonstration, use only a separately backed-up
`_TEST` or `_COPY` project containing an independently reviewed thermal template.
The new **Apply reviewed room templates** action shows the copy guard, reviewer
evidence, exact room selection, immutable preview and VE read-back receipt. Do
not apply an unreviewed template merely to remove audit warnings.

### Part B — exact SIA 4010 case (4 minutes)

1. Open and save `Test_640_Test1.mdl`.
2. Run the hub again.
3. Show that the active case is `test_1/640`, APS files are detected and the prior
   evaluation status is displayed verbatim.
4. Click **Open SIA 4010 Model Builder**.
5. In the Model Builder keep the language set to English.
6. Show:
   - the eight validation classes;
   - exact variants/cases;
   - locked normative features;
   - preparation, qualification, simulation and APS controls;
   - the operation log and fail-closed statuses.
7. Do not start a new model-generation campaign during the presentation.
8. Close the builder, reopen the hub, then click **Evaluate latest linked APS**.
9. Explain the result status:
   - output scope complete;
   - result values traceable to the APS;
   - no invented acceptance criterion;
   - therefore recorded results, not a false PASS.

### Part C — evidence and roadmap (2 minutes)

1. Run the hub and click **Evidence dashboard — all validation classes**.
2. Show that every case has a stable identity, source contract, model/simulation/
   result gates and checksums.
3. State the current execution evidence exactly: 2/34 model cases, 2/34
   ApacheSim cases and 2 linked APS evaluations are checksum-valid. This is the
   execution baseline, while the larger 10/34 figure shown in the cockpit is the
   number of implemented or runtime-qualification automation routes.
4. Explain the remaining engineering groups:
   - Test 2 solar-protection control and APS binding;
   - Test 3 lighting/daylight control binding;
   - Tests 4–6 HVAC topology and multizone sequences;
   - Test 7 plant/energy-system binding;
   - official acceptance review where the workbook does not define a criterion.

## 5. Actions to avoid during the live meeting

- Do not run **Create parametric Swiss reference model**.
- Do not run **Continue a Test 1 runtime qualification**.
- Do not run a fresh all-year ApacheSim calculation unless the pre-demo rehearsal
  succeeded on the same project after the last save.
- Do not modify the client model.
- Do not say “SIA certified”, “all tests pass” or “100% compliant”.
- Do not interpret `REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION` as PASS.
- Do not hide warnings; explain that visible uncertainty is a deliberate product
  requirement.

## 6. Presenter wording

### Opening

> Today I am demonstrating an IESVE-native Swiss compliance workbench. It combines
> a read-only SIA 380/2 client-model pre-check with a source-traced SIA 4010 software
> verification laboratory. The product is designed to fail closed: unresolved
> regulatory inputs remain visible and cannot silently become compliance claims.

### Client audit

> This is a copy of a real client model. The tool reads geometry, envelope,
> templates, profiles and APS outputs. It confirms what is usable, identifies what
> is missing, and writes machine-readable evidence without changing VE.

### SIA 4010 laboratory

> All 34 exact cases across the eight validation classes are catalogued against the
> official files. One guarded generation route is verified and nine further routes
> are in controlled runtime qualification. Test 1 already demonstrates the complete
> model-to-ApacheSim-to-APS evidence chain.

### Status interpretation

> A recorded result is not automatically a pass. When an official workbook does
> not define an acceptance criterion, the workbench reports that fact instead of
> inventing a tolerance. This is essential for a defensible compliance product.

### Closing

> The MVP client workflow is operational. The remaining work is bounded: qualify
> the outstanding VE control and HVAC bindings, complete the official result gates,
> and package the reviewed evidence. The architecture, case registry, audit trail,
> interface and core execution chain are already in place.

## 7. Pre-demo checklist

- [ ] Restart VE.
- [ ] Confirm `ZOER_32_C1_TEST.mdl` opens without missing-profile warnings.
- [ ] Run the client audit once and confirm the new output is English.
- [ ] Confirm the cockpit opens fully and scrolls on the presentation display.
- [ ] Open `Test_640_Test1.mdl` and confirm the active case is `test_1/640`.
- [ ] Run **Evaluate latest linked APS** once.
- [ ] Rebuild the evidence dashboard once.
- [ ] Keep the three project paths in a text file for quick copy/paste.
- [ ] Close unrelated VE projects and terminal windows.
- [ ] Rehearse the nine-minute sequence once with a timer.
- [ ] Keep the latest JSON, APS evaluation and navigator HTML open as fallback.

## 8. Definition of “near MVP” used in the presentation

The near-MVP statement applies to the **client-facing compliance workflow**:

`open client model -> inspect -> collect evidence -> report -> expose limitations`

It does not mean that all 34 SIA 4010 cases currently pass. Full validation-suite
completion requires the remaining VE engine bindings and case-specific official
acceptance evidence.
