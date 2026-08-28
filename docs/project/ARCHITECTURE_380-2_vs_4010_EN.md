> **Note:** Translated from French original. See [ARCHITECTURE_380-2_vs_4010.md](ARCHITECTURE_380-2_vs_4010.md) for the source document.

# Two Products, One Boundary -- SIA 380/2 vs SIA 4010

This repository carries **two distinct products** that must not be confused. This
document draws the boundary, once and for all, and provides the commands to
work on each one independently.

Established 2026-08-13, after direct verification in the code.

## The fact that grounds the separation

**The two products share no code.** Verified: the 380/2 core imports no 4010
module, and no 4010 module imports the 380/2 core. The only cross-reference is a
string (`"formal_compliance_verdict"` in `test1_campaign.py`), not an import.
The boundary already exists in the code; this document makes it visible.

```
grep -rE "^(from|import) .*(sia380_checker|compliance_verdict|reference_project)" \
     swiss_sia/reference_model/ engine/     # -> empty
grep -rE "^(from|import) .*(sia4010|reference_model)" \
     swiss_sia/sia380_checker.py swiss_sia/compliance_verdict.py \
     swiss_sia/app.py swiss_sia/data_extractor.py                # -> empty
```

---

## Product 1 -- SIA 380/2 Compliance Checker (the commercial MVP)

Reads a **client** IESVE model and produces a **per-requirement diagnostic**. Never
pronounces overall compliance on its own: the comparison against the reference
building remains a reviewed input, as required by the standard's method.

**What it does, and its exact limitation**: see [MVP_COMPLETION_MATRIX.md SS9](MVP_COMPLETION_MATRIX.md).

### Launchers (in VEScripts)

| Script | Role |
|---|---|
| `Run_VE_Swiss_Compliance.py` | Full analysis + Excel/PDF report. This is the main entry point. |
| `Run_VE_Swiss_Compliance_Hub.py` | Cockpit: client audit -> evidence -> report. |
| `Run_VE_Swiss_Compliance_Remediation_Probe.py` | **Read-only** audit, never mutates the model. |
| `Run_VE_Swiss_Compliance_Evidence_Wizard.py` | Reviewed evidence collection assistant. |

### Core modules (`swiss_sia/`)

`app.py` (orchestration) . `data_extractor.py` (the **only** `iesve` boundary:
geometry, constructions, U-values, systems, APS results) . `model_analyzer.py`
(normalization into `RoomData`/`SurfaceData`/`OpeningData`) . `sia380_checker.py`
(the ten check families) . `compliance_verdict.py` (fail-closed verdict) .
`reference_project.py` (reference building spec) . `evidence_manager.py`,
`evidence_bootstrap.py`, `evidence_wizard.py` (reviewed evidence) .
`remediation_probe.py` . `excel_report.py`, `compliance_report_pdf.py`,
`health_score.py` (outputs) . `config.py` (380/2 limit values, **shared**).

### Tests -- 197, isolatable

```bash
pytest -m sia3802
```

---

## Product 2 -- SIA 4010 Validation (the bonus)

Builds the **34 exact test cases** frozen by the standard, runs them in VE,
and compares against the references from the official workbooks. Validates
**the software**, not a client building.

### Launchers

All prefixed `Run_VE_SIA4010_*.py` (Fast Start, Test 1 campaign, APS probes,
Test 2A...). The prefix **is** the separation on the launcher side.

### Core modules

`swiss_sia/reference_model/sia4010/*` (case registry, bundles, qualified APS
extraction, evaluation) . `swiss_sia/reference_model/*` (VE model builder)
. `engine/*` (pure Python band/distribution engines, CI-testable without
`iesve`).

### Tests -- 569, isolatable

```bash
pytest -m sia4010
```

---

## Shared base (295 tests, `-m shared`)

What both products use: the VE model builder (`reference_model/`), the VE
gateways (`ve_*`), weather conversion (the 4010 test climate **and** the
380/2 application climate), report styling and UI translations, the APS
inventory. `config.py` carries values for both standards.

```bash
pytest -m shared
```

---

## How to work separately

| Goal | Command |
|---|---|
| Develop / demonstrate the 380/2 product | `pytest -m sia3802` |
| Work on 4010 validation | `pytest -m sia4010` |
| Touch shared infrastructure | `pytest -m shared` |
| Everything (unchanged) | `pytest` |

The mechanism is in [`tests/conftest.py`](tests/conftest.py): each test is
marked at collection time, **no files were moved** -- test relative paths
remain valid. To reclassify a test, edit the sets at the top of that conftest.

## What remains to be done for a full physical separation

Not done, and intentionally so: moving the 380/2 modules under a dedicated
package (`swiss_sia/compliance_3802/`) would require updating all launcher
imports in the same commit, in an already loaded worktree. Since the coupling
is zero, this move can be done cleanly later; it adds nothing functional,
only organizational clarity. The logical boundary is already clean and
documented here.
