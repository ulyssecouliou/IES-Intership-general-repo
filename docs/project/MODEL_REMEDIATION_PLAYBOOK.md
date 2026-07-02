# Model Remediation Playbook - ZOER_32_C1

This playbook converts the current Excel readiness findings into practical
actions for the model reviewer inside IESVE. It is intentionally conservative:
do not edit a model value only to make the report pass. Correct the VE/CDB input
only when the current model is wrong or incomplete; otherwise keep the finding
open and provide auditable reviewer evidence.

Latest reviewed workbook:
`reports/Swiss_Compliance_Report__ZOER_32_C1__-__20260701_231313.xlsx`

## Current Priority Findings

| Priority | Sheet | Scope | Current value | Retained check value | Required action |
|---|---|---|---:|---:|---|
| P1 | `FRAME FRACTION AUDIT` | `STD_EXTW` | `ff = 0.30`, 99 windows | `ff <= 0.25` | Correct the frame/glass split or provide audited facade justification. |
| P1 | `FRAME FRACTION AUDIT` | `STD_EXT2` | `ff = 0.35`, 27 windows | `ff <= 0.25` | Correct the frame/glass split or provide audited facade justification. |
| P1 | `ENVELOPE U REVIEW` | `STD_EXT1, STD_PAR1, STD_WAL2` | `U = 0.222 W/(m2K)` | `U <= 0.20 W/(m2K)` | Improve/update construction assignment or provide a full SIA 380/2 reference-calculation justification. |
| P1 | `SIA4010 READINESS` | Official evidence | `2/5` evidence families present | `5/5` required before validation wording | Collect official SIA 4010 evidence and confirm target validation class. |

## Before Editing The Model

1. Save a copy of the client VE project or create a versioned revision.
2. Keep the latest Excel report as the before-change evidence.
3. Record the VE project path and model name from `PREFLIGHT`.
4. Do not change SIA constants in `swiss_sia/config.py` unless the standards
   interpretation has been reviewed and approved.
5. If the model value is technically correct but exceeds the retained readiness
   value, keep the model unchanged and provide evidence/justification instead.

## Fix 1 - Frame Fraction For `STD_EXTW` And `STD_EXT2`

### Goal

Resolve:

- `STD_EXTW`: `ff = 0.30`, 99 windows, 206.0 m2.
- `STD_EXT2`: `ff = 0.35`, 27 windows, 51.42 m2.

The retained readiness check is `ff <= 0.25`.

### IESVE/CDB Actions

1. Open the client project in IESVE, not a temporary VE copy.
2. Open the construction database / Apache constructions editor.
3. Locate the glazing/window constructions `STD_EXTW` and `STD_EXT2`.
4. Review the frame/glass definition fields:
   - frame percentage or frame fraction;
   - frame inside/outside area ratio if shown;
   - glazing area vs total window area;
   - linked frame profile or window construction definition.
5. Decide whether the current value is a modelling error:
   - if yes, correct the frame/glass split in CDB or assign the correct window construction;
   - if no, keep the value and prepare a reviewer justification.
6. Save the VE project.
7. Run `Run_VE_Swiss_Compliance.py` from the VE Run button.

### Evidence To Keep

- Screenshot or export of the CDB construction before/after.
- Manufacturer facade/window schedule showing frame fraction.
- Reviewer note explaining whether `ff` is model-corrected or intentionally
  accepted above the retained readiness value.
- Filled row in `templates/evidence/glazing_solar_protection_template.csv` if
  the evidence is external.

### Expected Report Result

After correction, `FRAME FRACTION AUDIT` should show:

- `STD_EXTW`: `PASS`, or still `FAIL` with signed justification.
- `STD_EXT2`: `PASS`, or still `FAIL` with signed justification.
- `ALERT SUMMARY`: fewer or no `SIA3802_FRAME_FRACTION` alerts.

## Fix 2 - External Wall U-Value For `STD_EXT1, STD_PAR1, STD_WAL2`

### Goal

Resolve the external wall group:

- Current value: `U = 0.2223163098096848 W/(m2K)`.
- Retained readiness limit: `U <= 0.20 W/(m2K)`.
- Gap: about `0.0223 W/(m2K)`.
- Affected surfaces: 2.
- Net affected area: about 13.00054 m2 in the detailed audit row.

### IESVE/CDB Actions

1. Open the construction database / Apache constructions editor.
2. Locate the wall constructions listed in the report:
   - `STD_EXT1`;
   - `STD_PAR1`;
   - `STD_WAL2`.
3. Identify whether the failing external wall surface is using a compound
   construction assignment or a layer stack derived from these IDs.
4. Check the wall build-up and U-factor:
   - insulation layer thickness;
   - material conductivity;
   - air gaps/cavities;
   - internal/external surface resistance method;
   - whether the surface should actually be classified as external wall,
     ground-contact wall or another SIA category.
5. If the model assignment is wrong, assign the correct external wall construction.
6. If the wall build-up is wrong, update the construction so the U-factor is
   `<= 0.20 W/(m2K)`.
7. If the real project wall is intentionally `0.222 W/(m2K)`, keep the model and
   prepare a full SIA 380/2 reference-calculation justification instead of
   forcing a pass.
8. Save the VE project and rerun the compliance script from the VE Run button.

### Evidence To Keep

- CDB construction export or screenshots showing the wall layer stack.
- U-factor calculation source from VE/CDB.
- If changed, a before/after note with the reason for the correction.
- If unchanged, a full reviewer reference-calculation note explaining why the
  project remains acceptable despite the retained readiness comparison.

### Expected Report Result

After correction, `ENVELOPE U REVIEW` should show:

- `STD_EXT1, STD_PAR1, STD_WAL2`: `PASS`, with `U <= 0.20 W/(m2K)`;
  or
- `FAIL`, but with an external justification tracked in the evidence pack.

## Fix 3 - SIA 4010 Evidence

### Important Guardrail

SIA 4010 is not a simple building threshold. It is an official software/method
validation evidence workflow. The current report must remain `NOT_CHECKABLE`
until the required official evidence is available and reviewed.

The manager-provided software register does not list IESVE as validated. Do not
claim "IESVE is SIA 4010 validated" from the current register alone.

### Decide The Target Class First

Before collecting files, confirm the intended validation class:

- `1A` or `1B`: envelope / cooling-need classes with solar-protection variants.
- `2A` or `2B`: adds lighting-control validation.
- `3`: humidification/dehumidification and AHU-related tests.
- `4A` or `4B`: broad system-related thermal load and energy validation.
- `5`: test 7 only, for heating/cooling energy demand with existing demand profiles.

### Evidence Folder

Place reviewed files in:

```text
sia4010_evidence/
```

Recommended filename prefixes:

```text
SIA4010_official_test_specs_*
SIA4010_official_evaluation_workbook_*
SIA4010_candidate_results_APS_Vista_*
SIA4010_reference_comparison_plots_*
SIA4010_validation_class_confirmation_*
```

### Minimum Evidence Families

The report currently expects five families:

1. Official SIA test specifications.
2. Official SIA Excel evaluation workbooks.
3. Candidate IESVE/model results transferred into the official files.
4. Reference-result graphs/comparisons generated by the official files.
5. Validation class requested and confirmed by SIA or the responsible authority.

### Expected Report Result

After adding evidence and rerunning from VE:

- `PREFLIGHT` should show `5/5 evidence families detected`.
- `SIA4010 READINESS` should no longer treat every test as blocked only because
  the evidence folder is incomplete.
- The final wording still requires manual reviewer acceptance of the official
  comparison results.

## After Every VE Run

Check these sheets first:

1. `MANAGER DASHBOARD`: executive readiness statement.
2. `P1 REMEDIATION`: remaining owner-ready blockers.
3. `FRAME FRACTION AUDIT`: frame fraction status by construction.
4. `ENVELOPE U REVIEW`: U-value status by opaque construction.
5. `VE G-VALUES AUDIT`: confirmation that `bs_en_410` is the SIA g-value
   candidate and raw `CDB g_value = 0.75` is not being used incorrectly.
6. `SIA4010 READINESS`: official evidence status.
7. `OPEN ITEMS BACKLOG`: items that remain open after the run.

## Safe Manager Wording

Use:

> The model has been reviewed with an automated SIA 380/2 readiness workflow.
> Remaining P1 items are frame-fraction evidence/correction, one external wall
> U-value group, and incomplete SIA 4010 official evidence.

Avoid:

> The model is fully SIA compliant.

Avoid:

> IESVE or this model is SIA 4010 validated.

