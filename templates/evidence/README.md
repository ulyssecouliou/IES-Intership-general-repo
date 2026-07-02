# Evidence Templates

These templates define the minimum evidence fields needed to move from a
readiness report toward a defensible Swiss SIA review.

Use them as client/model-reviewer handoff files. Filled files can be stored in
`sia4010_evidence/` and referenced from the generated Excel report.

## Templates

- `glazing_solar_protection_template.csv`: glazing, frame and shading evidence
  needed for SIA 380/2 opening and solar-protection checks.
- `g_values_audit_template.csv`: VE/CDB g-value traceability template for
  proving whether a raw `g_value` is the same value as EN 410 `g_perp`, and for
  documenting any `g_total_with_shading` calculation/evidence.
- `sia4010_evidence_index_template.csv`: official validation-evidence tracker
  for SIA 4010 tests, workbooks, candidate outputs, reference comparisons and
  validation class confirmation.
- `sia4010_software_register_review_template.csv`: manager-register review
  template. This is a guardrail file only; it must not be counted as official
  SIA 4010 validation evidence for the active IESVE workflow.

## Glazing Retrieval Guide

Use `docs/project/GLAZING_EVIDENCE_GUIDE.md` before filling the glazing template.
It explains which fields are retrieved automatically from IESVE/CDB through the
documented VEScript API and which fields still need external reviewer evidence.

## Important Guardrail

Evidence templates do not create official SIA validation by themselves. The
responsible reviewer must confirm source, applicability, version and acceptance.
