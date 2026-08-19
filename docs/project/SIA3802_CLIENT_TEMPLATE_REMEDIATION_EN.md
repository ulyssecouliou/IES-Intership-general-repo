# SIA 380/2 Client Template Remediation

## Product boundary

The remediation workflow can now create one source-traced fallback template for
SIA 2024 usage category 4.01 (Classroom), then apply a reviewed template that
exists in the active VE project. It does not decide that a fallback is correct
for a client room and it never labels the resulting model automatically
compliant.

The 4.01 generator reads the curated cell-level record
`refs/reference-data/sia-2024-2021.classroom-4.01.json`. That record includes
the SHA-256 of `2024_Raumdatenblätter_dfi_V221.xlsm`, the exact source cells,
the SIA 380/2 clauses authorising use of SIA 2024 fallback data, and every VE
mapping that still requires engineering review. Actual project data always
take precedence.

The workflow is intended for a responsible engineer who has reviewed a room-use
template against the applicable project brief and source documents. A verified
assignment receipt is evidence of a software operation, not a SIA compliance
certificate.

## What can be corrected

Subject to the fields exposed by the installed VE runtime, a reviewed thermal
template can correct and verify room-level:

- occupancy, lighting and equipment gains;
- gain and setpoint profile references;
- infiltration and outside-air exchanges;
- heating and cooling setpoint controls;
- Apache system and ideal-load room settings contained in the template;
- the thermal-template identity assigned to each selected room.

The existing read-only audit must be rerun after the assignment. It determines
whether the original room-level findings have actually been resolved.

## What is deliberately outside this operation

A room template does not correct:

- geometry, adjacencies or surface classification;
- opaque or glazed constructions and their U-values;
- frame fraction, glazing g-value or solar-protection evidence;
- thermal bridges;
- weather-file identity and climate-scenario approval;
- ApacheSim output-variable selection or missing simulation results;
- missing project decisions or reviewer evidence.

Those findings remain visible in the SIA 380/2 audit and report. Separate,
source-reviewed remediation operations are required for them.

## Mandatory safety contract

1. Use `Save As` to create a project folder ending in `_TEST`, `_COPY` or
   `_DISPOSABLE`.
2. Keep an independent backup of the original client project.
3. Run the read-only client audit and retain its JSON report.
4. Select an existing thermal template and the target rooms explicitly.
5. Confirm that the active project is the disposable copy and authorize only
   the exact checksum-bound technical application. No free-text fields are used.
6. Create the read-only preview. Inspect the exact target content and the
   current room state in the generated JSON plan. No free-text evidence form is
   required: project identity, template fingerprint, room identifiers, date and
   a matching source-traced provisioning receipt are captured automatically.
7. Confirm the technical application and apply the unchanged preview. The plan
   checksum, template fingerprint and room-state fingerprints must still match.
8. The VE API assigns the template and reads back its identity, gains, air
   exchanges and supported controls.
9. Rerun the read-only client audit before saving VE.
10. If assignment or read-back fails, close VE without saving and reopen the
    disposable copy.

## VEScripts launch sequence

Run `Run_VE_Swiss_Compliance_Hub.py`, then use the client-model section:

1. **Inspect active client model**
2. If actual approved classroom data are unavailable, **Create SIA 2024
   classroom reference template** and review its receipt
3. **Apply reviewed room templates**
4. **Inspect active client model** again
5. **Complete project evidence**
6. **Generate auditable report**

The direct launchers are:

- `Run_VE_SIA3802_Create_Classroom_Reference_Template.py`
- `Run_VE_SIA3802_Approved_Template_Remediation.py`

The creation launcher changes no room and does not save VE. It creates or
strictly verifies 51 native daily/weekly/yearly profiles, three gains, two air
exchanges and `SIA2024_4.01_CLASSROOM_REFERENCE`.

## Review-required VE mappings in the 4.01 fallback

- SIA moisture generation (51 g/h per person) is mapped to 35.4167 W/person
  latent heat using an explicitly documented 2500 kJ/kg engineering conversion.
- The people schedule is used as a temporary lighting schedule because the
  room-data workbook gives installed power and annual full-load hours, not a
  directly importable VE hourly lighting-control profile.
- The people schedule is used as a temporary ventilation schedule; actual
  control logic and operating hours must replace it when known.
- 21/26 degC are SIA 2024 Table 11 design fallbacks. The responsible engineer
  must select and document the applicable SIA 380/2 Figure 1 / actual-control
  path.

These mappings are deliberately present in the machine-readable review and
receipt artifacts. They prevent the source template from being mistaken for a
project-specific approval.

## Evidence captured without manual fields

The technical application UI records the following automatically:

- active disposable project identity and path;
- VE template name, handle and immutable content fingerprint;
- exact selected room identifiers and their pre-mutation fingerprints;
- generation date;
- matching source-traced provisioning receipt, source path and source SHA-256
  when available;
- confirmation that every referenced profile exists in the project;
- initial audit, immutable preview plan, verified mutation receipt and required
  post-mutation audit.

Missing source evidence remains `NOT_CHECKABLE`; it is never replaced by a
default or user-entered assertion. A single explicit confirmation authorizes the
technical change in the disposable copy. Application always records
`compliance_claim: NOT_GRANTED`. Independent project review may be attached later
through the evidence workflow and remains necessary before any final compliance
claim, but it is not a form-entry prerequisite for the technical mutation.

If any item is unknown, the operation is blocked. No default regulatory value is
substituted.

## Artifact locations

Plans and receipts are stored beside the copied VE project:

```text
sia_compliance_artifacts/
  template_provisioning/
    sia2024_classroom_template_review_YYYYMMDD_HHMMSS.json
    sia2024_classroom_template_receipt_YYYYMMDD_HHMMSS.json
  template_remediation/
    sia3802_template_plan_YYYYMMDD_HHMMSS.json
    sia3802_template_receipt_YYYYMMDD_HHMMSS.json
```

The Compliance Hub displays the latest remediation status. When a verified
receipt is newer than the last audit, the required next action is explicitly
shown as a post-remediation audit.

## Definition of done for today's client-model scope

- the original client model is never mutated;
- a copy-only mutation guard is active;
- template and rooms are explicitly selected;
- available source provenance is captured automatically and missing provenance
  remains `NOT_CHECKABLE`;
- independent review remains mandatory for a later compliance claim, not for
  the non-claiming technical application;
- referenced profiles are checked;
- exact before/target state is recorded;
- preview integrity is checksum-bound;
- template and room drift invalidate the preview;
- VE assignment and simulation-relevant room content are read back;
- failed operations provide a close-without-saving rollback instruction;
- the SIA 380/2 audit is required after mutation;
- the final report continues to expose every non-template finding.
