---
name: sia-compliance-change
description: Implements or reviews Swiss SIA 380/2 compliance logic with strict source traceability and conservative claims. Use for regulatory parameters, limits, SIA rules, readiness status, compliance scoring, or Swiss energy modelling assumptions.
---

# SIA Compliance Change

1. Identify whether the requested item is normative, informative, project-specific, comparison-only, or still unknown.
2. Verify the exact source edition and locator. Prefer approved local sources; do not read licensed material until enterprise use is authorized.
3. Record name, description, units, source, source locator, validation range and placeholder state in the configuration layer.
4. Never turn a limit or target into a project assumption. Keep missing values unresolved and visible.
5. Implement the rule through the existing extraction/configuration/checker/reporting boundaries.
6. Add tests for valid evidence, missing evidence, invalid units/ranges and conservative status behavior.
7. Update requirement/coverage matrices and documentation when scope or claim wording changes.
8. State which result is automated, partial, reviewer-dependent or not checkable.

Before finishing, check that no new value is embedded in geometry, VE mutation or report formatting code.
