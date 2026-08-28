> **Note:** Translated from French original. See [SIA_MODEL_BUILDER_GUIDE.md](SIA_MODEL_BUILDER_GUIDE.md) for the source document.

# Swiss VE Model Builder — Operator Guide

## Actual Scope

The interface covers the eight SIA 4010 classes (`1A`, `1B`, `2A`, `2B`, `3`,
`4A`, `4B`, `5`) and the 24 exact variants of the official matrix.

This coverage has three levels that must not be confused:

1. **Framework**: official specifications and workbooks verified by checksum,
   variants routed, reference bands analysed and navigator available.
2. **Preparation**: source-traced dossier, list of missing inputs, execution
   queue and validation steps produced without modifying VE.
3. **VE generation**: automated and read-back mutation in VE. To date, only
   `test_1/600` has this level proven.

Five additional cases, `test_1/640`, `test_1/600FF`, `test_1/900`,
`test_1/940` and `test_1/900FF`, have a generator in state
`RUNTIME_QUALIFICATION_READY`. The interface exposes them with the separate
button `Qualify the generator in VE`. They enter the evidence register only
after a complete run and successful read-backs in a fresh disposable project.

Cases 900, 940 and 900FF use the public high-mass definition from
ASHRAE 140-2017 Addendum a, Table 5-27: concrete-block wall, foam insulation
and wood siding, concrete slab and ideal floor insulation, with the case 600
roof unchanged. This source is marked `PUBLIC_REFERENCE`: it does not replace
the confirmation requested from SIA for the exact identity with
SN EN ISO 52016-1:2017, Chapter 7. Qualification stops if VE does not preserve
the zero density and heat-capacity values of the ideal insulation, instead of
silently introducing a minimum value.

A preparation or framework coverage is never presented as an SIA validation.

## Safety Rules

- An official case corresponds to **one saved disposable VE project**.
- A class may require several projects: one per exact case.
- The `Create in VE` button is active only if a controlled generator exists.
- The `Qualify the generator in VE` button is active only for a source-traced
  generator not yet verified; its result never constitutes a compliance
  declaration.
- Cases not yet implemented remain accessible with `Prepare and check`; the
  interface then creates a usable audit and flags the blockers.
- An unsaved temporary VE project `VEPROJ` can never be mutated.
- No absent official parameter is invented.
- A positive comparison against the official bands remains distinct from the
  external SIA attestation.

## Use in VEScripts

1. Open or create a disposable VE project, then save it.
2. Run `Run_VE_SIA_Model_Builder_UI_Probe.py`.
3. Verify `SIA MODEL BUILDER UI PROBE: READY`.
4. Run `Run_VE_SIA_Model_Builder_UI.py`.
5. Choose the class, variant and case.
6. Click `Prepare and check`.
7. Examine the status and JSON in
   `sia4010_artifacts/model_builder/`.
8. If `Create in VE` is active, launch the controlled mutation in the
   disposable project. Otherwise, address the blockers indicated by the report.

The `External normative inputs` button creates, only if absent, the file
`sia4010_external_inputs.json` at the root of the saved VE project, then opens
it. The source template is
`config/sia4010_external_inputs.example.json`. An existing file is never
overwritten.

Each delegated input must contain:

- the path and SHA-256 of the source file;
- its provenance and the authority that provided it;
- the licence or usage-authorisation reference;
- the dataset identity, format and semantic scope;
- the path and SHA-256 of an independent technical validation report;
- `normative_authorization_status = CONFIRMED` and
  `technical_validation.status = PASS`.

The technical report follows the template
`config/sia4010_external_input_validation_report.example.json`. Its content
must identify the input, reproduce the exact SHA-256 of the source, document
the validator and method, and provide at least one named check. A global `PASS`
status is refused if a single check is not `PASS`.

It also references a separate `binding_artifact`, with its path, SHA-256 and
the `schema_id` expected for that input family. This separation allows the
authorised PDF, workbook or dataset to be kept as primary evidence while
providing the generator with a controlled normalised artefact. The report is
refused if the schema, file or fingerprint of that artefact does not match.

For `test_2A/2A` and the Test 3 cases, the button also copies six templates
into `sia4010_external_input_templates/`:

- ISO 52016 Chapter 7 test cell and lightweight envelope;
- SIA 2028 Zurich-Kloten hourly weather file;
- SIA 2024 category 3.1 profiles;
- SIA 387/4 Tables 9 and 10 functions;
- source-traced detail of the example-building fabric awning;
- authority decision on the 3K/3L device identity.

The corresponding published schemas are:

- `schemas/sia4010_iso_test_cell_binding.schema.json`;
- `schemas/sia4010_sia2028_weather_binding.schema.json`;
- `schemas/sia4010_sia2024_usage_profiles_binding.schema.json`;
- `schemas/sia4010_sia3874_controls_binding.schema.json`;
- `schemas/sia4010_shading_device_binding.schema.json`;
- `schemas/sia4010_authority_decision_binding.schema.json`.

When their three pieces of evidence actually reach `READY_FOR_BINDING`,
`Prepare and check` automatically produces
`sia4010_artifacts/model_builder/test2a/generator_input.json`. This contract
verifies in particular the closure of window dimensions, the consistency
between the SIA PDF geometry and the ISO transcription, the 8,760 weather hours
and the exact set of occupancy/equipment/lighting profiles.

The three SIA 2024 functional schedules and the native VE objects are two
separate contracts. A logical series of 8,760 values can never be passed to
`VEProject.create_profile("yearly", ...)`: in VE, a yearly profile contains
periods referencing weekly profiles, which reference seven daily profiles. The
SIA 2024 artefact can therefore provide an explicit `ve_profile_graph` with:

- `daily`, `weekly` and `yearly` nodes, each with a unique VE reference;
- exactly seven `profile_ref` daily entries per weekly node;
- contiguous yearly periods covering exactly days 1 to 365;
- three explicit outputs for occupancy, equipment and lighting;
- a `source_locator` on each node and on the complete graph.

The written supplement received from the authority on 10 August 2026 now
provides the standard values and the 24 displayed hourly classes for SIA 2024:2021
category `3.1 Einzel-/Gruppenbuero`. The evidence and its SHA-256-linked
transcription are kept under
`sia4010_evidence/source_audits/sia2024_3_1_authority_20260810/`. This source
notably confirms 2 rest days per week, 261 usage days per year and an annual
occupant simultaneity factor of 0.80. It does not, however, name the weekdays,
exception dates or the VE hourly boundary convention: these elements are
therefore not invented in the native graph.

Without this graph, the status is
`SOURCE_BINDINGS_READY_PROFILE_GRAPH_REQUIRED`. With a valid graph, it becomes
`SOURCE_BINDINGS_READY_VE_BINDING_REQUIRED`. In both cases, VE mutation remains
disabled as long as the fabric-awning dynamic setters/read-backs and the
SIA 2024 profile setters are not qualified. The input contract must therefore
never be presented as an executed Test 2A model.

To qualify separately the profile graph and the CDB awning setters in a
disposable project:

The recommended route is now the single script
`Run_VE_SIA4010_Test2A_Qualification_One_Click.py`. It chains the steps below,
also calibrates an equivalent thermal layer on the ISO U-factor of the base
glazing, then temporarily assigns that same candidate to a bay and verifies
restoration of the original assignment. No PASS from this chain constitutes a
compliance verdict.

1. prepare the official scenario `test_2A/2A`;
2. run `Probe the Test 2A runtime`;
3. wait for status
   `READY_FOR_DISPOSABLE_MUTATION_QUALIFICATION`;
4. click `Qualify the Test 2A profiles`;
5. on the same screen, click `Qualify the Test 2A awning setters`;
6. after its PASS, click `Qualify the fixed 2E1 optics`.

The equivalent thermal calibration targets only the base glazing U-factor
confirmed in the Test 2 contract. It qualifies neither the manufacturer
composition 4/14/4/14/4, nor the combined glazing-plus-awning U-factor, nor the
dynamic control, nor the APS results. These boundaries remain explicitly closed
in the chain report.

The second button remains disabled until the read-only probe passes. It calls
`Run_VE_SIA4010_Test2A_Profile_Qualification.py`, refuses any namesake before
the first creation, materialises dependencies in order, saves each level then
reads back the exact type and data. Its report
`sia2a_profiles_*.json` and its `.sha256` qualify only this boundary: no
geometry, construction, template, load, solar protection, weather or
simulation is created.

The awning button calls
`Run_VE_SIA4010_Test2A_Shading_Setter_Qualification.py`. It creates exactly one
unassigned CDB glazed construction, does not touch any layer and verifies only
the persistence of `external_shade_active`,
`external_shade_radiation_to_lower=150` and
`external_shade_radiation_to_raise=150`. An earlier report, even `STARTED`,
prohibits any repetition in the same project: the project must then be
discarded. Its PASS means only `CDB_STORAGE_AND_READBACK_ONLY`. The supplied
PDF does not specify the exact signal, activation operator or release rule;
those fields therefore remain unknown. The PASS also does not qualify timestep
state memory or the conversion from `g_total=0.059` to VE optical fields.

The last button calls
`Run_VE_SIA4010_Test2A_2E1_Optical_Setter_Qualification.py`. It requires the
previous report and its valid SHA-256, refuses a second run in the same project
and creates another unassigned CDB glazed construction. It writes and reads
back only the directly-mapped fields: activation, `ON` profile, normal solar
transmittance `0.040`, exterior solar reflectance `0.490` and exterior visible
reflectance `0.496`. Its PASS means only that VE stores those five fields. It
explicitly maintains `fixed_closed_optical_mapping_qualified=false` and
`diagnostic_candidate_generation_authorized=false`: angular values, interior
reflectance, visible transmittance, secondary gains and APS output equivalence
remain to be qualified.
After writing the report and its SHA-256, the same VEScript automatically
rebuilds `test2a/generator_input.json` and
`test2a/source_binding_audit.json`. The interface displays their status. The
expected status after all three qualifications is
`RUNTIME_STORAGE_QUALIFIED_MODEL_BINDING_REQUIRED`; it confirms the storage
boundaries but keeps `mutation_supported=false`.

The optical contract now preserves the exact identities from the
example-building documentation: `g_total=0.059 = tau_e 0.040 + qi 0.019`, with
`qi=0.006` convection + `0.013` thermal radiation + `0.000` ventilation. The
official case `Diag 2E1` — fabric awning always closed — is registered as a
prerequisite gate. Its schema is now linked to the official workbook whose
SHA-256 is checked: `Daten_Testprogramm!X5:X8764` for time, `Y5:AA8764` for
the three irradiances and `BD5:BH8764` for the five diagnostic outputs. The
reference-program sheets use the same quantity columns on rows 4 to 8763. This
binding proves where to read and write the 8,760 values; it does not prove that
the candidate cells are filled or that VE reproduces the awning. No
`g_total/g_glazing` ratio is accepted as a VE transmittance factor without a
qualified 2E1 simulation and output equivalence.

The workbook does not, however, define any bound or PASS/FAIL rule for 2E1: its
sheets are diagnostic charts. The comparator
`test2a_diagnostic_evaluation.py` therefore reproduces only the annual values
of the reference programs and their hourly distribution envelope. It can flag
`WITHIN_TECHNICAL_REFERENCE_ENVELOPE`, but its report mandatorily retains
`acceptance_criterion_available=false`, `compliance_pass=false` and
`optical_mapping_qualified=false`. A separate, reviewed technical decision
remains necessary before authorising the fixed closed optical representation.

The APS contract is intentionally incomplete at this stage: only one of the
eight series is qualified, `Window solar gains` at zone level for total solar
gain. The other seven remain blocked with
`UNBOUND_RUNTIME_EVIDENCE_REQUIRED`. A 2E1 evaluation also requires the exact
scenario `SIA4010_TEST_2A_2E1`, the awning `ALWAYS_CLOSED`, a completed
simulation and the SHA-256 of the corresponding APS file. It therefore refuses a
Case 600 APS or a dynamic-control 2A APS.

The `Probe active APS outputs` button launches the read-only probe on the
latest APS. It inventories the model's surfaces and attempts surface-level
reads only with the exact `room_id` and `aps_handle` provided by VE. The status
`READY_FOR_SURFACE_BINDING_REVIEW` means series have been read; it does not
mean their physical meaning is already qualified or that they match the
official 2E1 columns.

The preparation returns `MISSING_MANIFEST`, `BLOCKED`,
`READY_FOR_BINDING` or `NOT_REQUIRED` for these inputs. Even
`READY_FOR_BINDING` declares no compliance: it only authorises development of
the corresponding binding. A checksum error, unknown identifier or manifest
from another project stops the workflow.

The `Prepare the entire class` button verifies the official package once and
produces:

- an audit per exact case;
- a class index;
- an ordered execution queue;
- the still-blocking official inputs and generators;
- the complete contract from generation to ApacheSim to APS to comparison to report.

It does not silently create multiple VE projects: the qualified API used by the
MVP modifies the active project but does not yet provide reliable creation and
saving of independent projects.

The `Prepare all 8 classes` button runs the same preparation across the entire
matrix in a single package-verification pass. It writes
`SIA4010_all_classes_preparation.json`, distinguishes the 30 unique cases from
repeated occurrences across classes and preserves each blocker. For Tests 4, 5
and 6, the required spaces are extracted from the official IFC file with their
fingerprint, altitude, height, area, volume and source checksum.

The same audit contains `external_input_matrix`: the 30 cases are associated
with the 17 catalogued delegated inputs, along with affected cases, each
evidence item's status and exact issues. Without a project manifest, the six
Test 1 cases that are autonomous with respect to this layer are `NOT_REQUIRED`
and the other 24 are `MISSING_MANIFEST`; this does not change their VE
generator status.

This command also initialises
`sia4010_evidence/autonomy/sia4010_case_evidence.json`. This central register
coordinates the disposable projects, re-verifies checksums before each gate
and rebuilds the eight reports in
`sia4010_evidence/autonomy/navigator/`.

The register's `1.1` schema distinguishes three pieces of evidence for each
exact case: model report, ApacheSim run and APS evaluation. Existing `1.0`
registers are migrated without erasing their reports. A result gate requires
the evaluated APS to be exactly the one produced by the registered simulation.

The `Open the evidence navigator` button rebuilds those eight reports before
opening them. Its log shows the number of models, simulations and APS
evaluations whose files and fingerprints are still valid.

The standalone HTML interface and the native interface both use
`config/sia4010_all_classes.json` as the default official manifest. The former
manifest `sia4010_classes_1a_1b.json` remains a specialised geometric source
for the shared test cell of Tests 1 to 3; it is no longer presented as the
global manifest to the operator.

## Test 3 Runtime Probe

After preparing an exact scenario `test_3A/3A` to `test_3L/3L` in a saved
disposable project, the `Probe Test 3 lighting runtime` button runs
`Run_VE_SIA4010_Test3_Runtime_Capability_Probe.py`.

This probe calls only getters. It captures:

- global lighting gains, in templates and in each zone;
- the presence and value of the `variation_profile`, `dimming_profile`,
  `max_illuminance` and `installed_power_density` fields;
- the availability of a setter on each proxy, without ever calling it;
- public members related to sensors, illuminance, daylight and photocells;
- the availability of external inputs required by the selected case;
- the distinct blockers of all twelve variants, including the specific 3K/3L
  clarification and still-absent APS bindings.

The report `sia4010_test3_runtime_capability_*.json` and its `.sha256` cover
all twelve variants. Even the status
`READY_FOR_DISPOSABLE_MUTATION_QUALIFICATION` authorises only the design of a
narrow setter probe in a fresh disposable copy. It retains
`mutation_authorized=false`, `simulation_performed=false` and
`compliance_claim_allowed=false`.

When all external evidence for the selected case actually reaches
`READY_FOR_BINDING`, `Prepare and check` automatically replaces the generic
preparation with a source-traced bundle:

`sia4010_artifacts/model_builder/test3/<3A-3L>/generator_input.json`.

This bundle verifies the exact set of SIA 387/4 functions (shading 1-3,
lighting 1-6), the awning detail, the ISO cell consistency, the control pair
prescribed by the 3A-3L matrix, the official annual band and the hourly
distribution contract `Beleuchtungsleistung`. It launches neither VE nor
ApacheSim. Variants 3K/3L require a checksum-linked SIA decision and remain
blocked until that decision has been translated into a qualified runtime
mapping.

## Executable Case 600

For `test_1/600`, the interface automatically creates the local source-traced
files:

- `sia4010_case_manifest.json`;
- `reference_model_config.json`;
- `reference_model_assets.json`;
- `sia4010_case600_mvp_audit.json`.

The BESTEST DRYCOLD weather must be present and verified. The workflow:

1. creates and reads back profiles, materials, constructions, gains, air
   exchanges and thermal template;
2. imports the gbXML geometry;
3. assigns and reads back constructions, openings, template and weather;
4. runs the final validation and writes the audit report.

After creation, the model is ready for the annual calculation. The VEScript
`Run_VE_SIA4010_APS_Probe.py` can then verify the APS file in read-only mode.
Variables are used only if their metadata matches the qualified contract
`config/sia4010_aps_bindings_ve_runtime.json`.
The same operation is accessible in the interface with
`Probe active APS outputs`; the report also includes surface reads by
`aps_handle` when available.

For cases `600`, `640`, `600FF`, `900`, `940` and `900FF`, the
`Run ApacheSim + evaluate the APS` button automates this chain. It first
requires an exact-case mutation report with a single zone and a read-back
weather `VE-WEA-001 = PASS`. It sets the January 1 to December 31 period and
the hourly output prescribed by the Test 1 specification, creates a single APS
without overwriting prior evidence, registers the chain scenario to model to
ApacheSim to APS with its fingerprints, then immediately launches the qualified
evaluation.

The supplied Test 1 specification does not impose an ApacheSim calculation
timestep or preconditioning duration. These two options are therefore left as-is
in the project and recorded before/after in the audit. The success of the
ApacheSim call produces the status
`SIMULATION_EXECUTED_AWAITING_APS_QUALIFICATION`; it becomes a usable result
only after verification of the 8,760 hourly values and all required APS
bindings.

For the seven Test 1 cases (`600`, `640`, `600FF`, `900`, `940`, `900FF`,
`1E`) and for `test_2A` to `test_2D`, the
`Evaluate the active APS` button reads the latest APS, verifies the qualified
metadata, computes the official metrics and, for Test 2, the hourly
distribution. The result is registered with APS/bindings checksums in the
cross-project register. For `600`, `640`, `900` and `940`, the official
workbook provides no acceptance bound: the interface records the 28 results
with `REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION`, never with a
compliance PASS. `1E` keeps its bounded comparison. The free-float cases
`600FF`/`900FF` use the qualified annual air-temperature and operative-temperature
bindings.

An evaluation launched separately on an APS that does not match any registered
simulation remains available as a diagnostic, but carries
`simulation_link_status = NOT_LINKED` and can never satisfy the navigator.

## Cases Not Yet Generated

The interface no longer attempts to fabricate a generic geometry with unlinked
values. It returns `PREPARED_WITH_BLOCKERS` and records notably:

- the official specification PDF;
- the official evaluation workbook;
- their checksums;
- the exact variant and case;
- the structured inputs still unlinked;
- the VE generator software blocker;
- the annual criteria and, for Tests 2, 3 and 5, the mandatory hourly
  distributions.

## Statuses to Understand

| Status | Meaning |
| --- | --- |
| `READY_FOR_PREPARATION` | valid scenario for an operation without mutation |
| `PREPARED_WITH_BLOCKERS` | sources verified, but inputs/generator incomplete |
| `READY_FOR_PROVISIONAL_VE_MUTATION` | MVP mutation possible with explicitly flagged public assumptions |
| `READY_FOR_VE_MUTATION` | no unresolved required input in the contract |
| `NOT_CHECKABLE` | APS result or official criterion missing |
| `REFERENCE_RESULTS_RECORDED_NO_ACCEPTANCE_CRITERION` | results calculated and traced, but no official bound allows a verdict |
| `OFFICIAL_RESULTS_RECORDED` | criteria implemented in the bands, without SIA attestation |
| `READY_FOR_OFFICIAL_REVIEW` | complete technical dossier ready for submission |

## Main Files

- native interface: `Run_VE_SIA_Model_Builder_UI.py`;
- UI probe: `Run_VE_SIA_Model_Builder_UI_Probe.py`;
- scenario launcher: `Run_VE_SIA_Model_Builder.py`;
- non-graphical preparation of the eight classes:
  `Run_VE_SIA4010_Prepare_All_Classes.py`;
- qualified APS analysis of the active Test 1 or Test 2A-2D case:
  `Run_VE_SIA4010_Evaluate_Active_Case.py`;
- strictly read-only zone and surface APS probe:
  `Run_VE_SIA4010_APS_Probe.py` and
  `swiss_sia/reference_model/sia4010/aps_probe.py`;
- annual Test 1 simulation and APS evaluation in a single operation:
  `Run_VE_SIA4010_Simulate_Active_Case.py`;
- scenario contract: `swiss_sia/reference_model/sia4010/model_scenario.py`;
- capability register: `swiss_sia/reference_model/sia4010/case_registry.py`;
- confirmed inputs and Tests 2 to 7 dependencies:
  `config/sia4010_official_input_contract.json`;
- external evidence template to copy into each project:
  `config/sia4010_external_inputs.example.json`;
- report template linked to each source:
  `config/sia4010_external_input_validation_report.example.json`;
- source, rights, format and external report validation:
  `swiss_sia/reference_model/sia4010/external_input_manifest.py`;
- semantic validation of the three Test 2A artefacts:
  `swiss_sia/reference_model/sia4010/normalized_external_inputs.py`;
- conditional Test 2A generator contract:
  `swiss_sia/reference_model/sia4010/test2a_source_bundle.py`;
- strictly read-only Test 2A runtime probe:
  `Run_VE_SIA4010_Test2A_Runtime_Capability_Probe.py` and
  `swiss_sia/reference_model/sia4010/test2a_runtime_capability.py`;
- controlled qualification of the Test 2A profile graph only:
  `Run_VE_SIA4010_Test2A_Profile_Qualification.py`,
  `swiss_sia/reference_model/sia4010/test2a_profile_binding.py` and
  `swiss_sia/reference_model/sia4010/test2a_profile_qualification.py`;
- source-traced binary contract and narrow awning setter qualification:
  `swiss_sia/reference_model/sia4010/test2a_shading_control.py`,
  `swiss_sia/reference_model/sia4010/test2a_shading_qualification.py` and
  `Run_VE_SIA4010_Test2A_Shading_Setter_Qualification.py`;
- all cases/classes preparation:
  `swiss_sia/reference_model/sia4010/preparation_bundle.py`;
- fail-closed preflight:
  `swiss_sia/reference_model/sia4010/scenario_preflight.py`;
- official comparison: `swiss_sia/reference_model/sia4010/test_runner.py`;
- class navigator: `swiss_sia/reference_model/sia4010/navigator.py`;
- eight-class manifest: `config/sia4010_all_classes.json`.

## HVAC and Energy Runtime Probe — Tests 4 to 7

After preparing and selecting an exact official case from test_4/4,
test_5A/5A to test_5D/5D, test_6/6 or test_7/7 in a saved disposable VE
project, use the **Probe HVAC/energy runtime Tests 4-7** button. The same
diagnostic can be launched directly with
Run_VE_SIA4010_Tests4_7_Runtime_Capability_Probe.py.

The JSON report and its .sha256 file are written under
sia4010_artifacts/diagnostics. This step is strictly read-only: it identifies
the APIs actually exposed by the installed VE version and the external sources
still missing. A status
READY_FOR_DISPOSABLE_MUTATION_QUALIFICATION authorises only the design of the
next setter test in a fresh disposable copy; it means neither model created,
nor simulation validated, nor SIA compliance.
