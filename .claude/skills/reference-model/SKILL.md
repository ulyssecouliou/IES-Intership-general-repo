---
name: reference-model
description: Builds, changes, diagnoses, or validates the programmatic Swiss reference VE model. Use for reference-model configuration, asset manifest, geometry, constructions, templates, weather, reporting, validation, or create-from-scratch workflow.
---

# Reference Model Workflow

Read `docs/project/SWISS_REFERENCE_MODEL_ARCHITECTURE.md` and the relevant files under `swiss_sia/reference_model/`.

Maintain this sequence:

1. Load source-traced configuration and create-mode asset manifest.
2. Validate schema, placeholders, ranges, references, geometry and collision policy.
3. Stop before mutation on any blocking result.
4. Provision profiles, CDB materials/constructions, optional system, gains, exchanges and thermal template.
5. Read back each object and store its runtime identifier in the provisioning receipt.
6. Generate and import deterministic gbXML geometry.
7. Assign constructions, template, optional HVAC and weather.
8. Rebuild/verify model relationships and validate the final snapshot.
9. Produce canonical JSON, JSONL audit and Excel-ready CSV outputs.

Run focused reference-model tests after each change. Run the pure-Python dry run for configuration or geometry changes. Require a disposable blank project for real-VE qualification.
