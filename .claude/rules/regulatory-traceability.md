---
paths:
  - "swiss_sia/config.py"
  - "swiss_sia/sia*.py"
  - "swiss_sia/value_integrity.py"
  - "swiss_sia/reference_model/compliance_config.py"
  - "swiss_sia/reference_model/asset_manifest.py"
  - "config/**/*.json"
  - "schemas/**/*.json"
  - "docs/project/**/*SIA*"
---

# Regulatory Traceability Rules

- Separate normative requirements, project inputs, comparison-only reference values and software QA tolerances.
- Record standard edition, clause/table/page locator, units and interpretation for every regulatory value.
- Never derive a project value from a regulatory limit or target.
- Keep unknown or unavailable inputs as named placeholders and emit a visible validation result.
- Preserve conservative wording: readiness, evidence state and prevalidation are not certification.
- Any changed regulatory constant requires a source check, a regression test and an audit/documentation update.
- Do not quote or redistribute licensed standards beyond what is necessary for an internal traceability locator.
