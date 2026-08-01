---
paths:
  - "Run_VE_Swiss_Reference_Model.py"
  - "swiss_sia/reference_model/**"
  - "scripts/reference_model_dry_run.py"
  - "config/reference_model*"
  - "schemas/reference_model*"
  - "tests/test_reference_model*"
  - "docs/project/SWISS_REFERENCE_MODEL_ARCHITECTURE.md"
---

# Reference Model Rules

- Keep the workflow deterministic: configuration -> manifest -> validated geometry -> capability gate -> asset creation -> gbXML import -> assignment -> readback -> report.
- Run every validation that can be completed before the first VE mutation.
- In create mode, reject incomplete manifests and object-name collisions before provisioning.
- Validate each profile, material, layer, construction, gain, exchange, template, room and surface immediately after creation or assignment.
- Keep geometry creation independent from compliance values and VE API implementation details.
- Do not replace a documented API gap with UI automation or an undocumented guessed method.
- Preserve future `sia4010/` integration contracts and avoid coupling official test loaders to core generation.
- A failed partially mutated VE project is not safe for rerun unless rollback is proven; instruct the user to discard the test project.
