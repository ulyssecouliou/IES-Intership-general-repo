> **Note:** Translated from French original. See [SIA4010_CAMPAGNE_VALIDATION_ACCELEREE.md](SIA4010_CAMPAGNE_VALIDATION_ACCELEREE.md) for the source document.

# Accelerated SIA 4010 Validation Campaign

## Objective

The launcher `Run_VE_SIA4010_Validation_Campaign.py` rebuilds a single queue
for the eight classes. It avoids recalculating shared cases and indicates the
exact next case to process, the VE launcher to use, and the class unblocked.

A case is only marked complete if the following three pieces of evidence are
still present and valid by SHA-256:

1. verified exact model;
2. annual ApacheSim simulation linked to that model;
3. APS evaluation linked to the simulated result and not `FAIL`/`NOT_CHECKABLE`.

Preparing a file, a successful simulation or a captured template are never
sufficient individually.

## Optimal Order

| Phase | Cases | Intended effect |
|---|---|---|
| P0 | Test 1 complete, including 1E | shared foundation for all classes except 5 |
| P1 | 2A | first fast closure: class 1A |
| P2 | 2B, 2C, 2D | closure of class 1B |
| P3 | 3A to 3F | closure of class 2A |
| P4 | 3G to 3L | closure of class 2B |
| P5 | 4, 5A to 5D, 6 | closure of class 3 |
| P6 | 7 | class 5, then 4A/4B if previous phases are closed |

## Daily VE Sequence

1. Run `Run_VE_SIA4010_Validation_Campaign.py` from the VE scripts.
2. Read **NEXT CASE** and **RUN**. Work only on that case in a saved disposable
   project.
3. Run the indicated launcher.
4. Re-run the campaign. The queue automatically shifts to the next case whose
   evidence is missing or has become obsolete.

### Test 1 direct

- For 600: open the existing project and run
  `Run_VE_SIA4010_Test1_Reconcile_Floor_Insulation.py`, then the Fast Start.
- For 640, 600FF, 900, 940, 900FF and 1A to 1D: use
  `Run_VE_SIA4010_Test1_Fast_Start.py` in a separate disposable project.
- The launcher `Run_VE_SIA4010_Simulate_Active_Case.py` then performs the
  guarded simulation and APS evaluation.

### Cases without an exposed VE generator: 1E and Tests 2 to 7

1. Build or open the exact case, then run
   `Run_VE_SIA4010_Capture_Active_Template.py`.
2. Have the geometry, thermal data, controls, weather, systems and required
   outputs independently reviewed. The manifest must carry
   `status: QUALIFIED`, a reviewer, a date, the VE version, the covered cases,
   the mandatory evidence items and the captured signature.
3. Add the binding in the pilot project's `sia4010_template_bindings.json`.
4. Run `Run_VE_SIA4010_Create_Disposable_From_Template.py`.
5. Open the copied `.mdl` and run
   `Run_VE_SIA4010_Verify_Template_Model.py`. Any modification to a critical
   model file invalidates the signature and blocks registration.

For **1E and 2A to 2D**, then run
`Run_VE_SIA4010_Simulate_Qualified_Template.py`. This launcher:

- enforces January 1 to December 31 and hourly results;
- retains and records the non-prescribed calculation timestep and preconditioning;
- rejects any discrepancy on read-back of ApacheSim options;
- produces a single verified APS;
- registers the simulation;
- immediately launches the official comparison. For Test 2, both the annual
  sum and the hourly distribution are mandatory.

For **Tests 3 to 7**, the exact template already allows the model evidence to
be closed. However, the simulation must not be presented as validating as long
as the APS bindings specific to those families are not qualified. The campaign
table therefore explicitly keeps them on hold and points to the runtime
capability probes.

## Acceleration Rules Without Loss of Evidence

- One disposable project per exact case; no overwriting of an existing APS.
- Reuse a template only for the cases listed in its qualification manifest.
- Process 2A before 2B-2D, then 3A-3F before 3G-3L: this is the order that
  unblocks a complete class earliest.
- Reuse the same reviewed template family for close variants, but capture and
  sign each exact state after controlled changes.
- Archive together the campaign JSON, the model/simulation/APS reports and the
  eight-class navigator.

## Scope of Result

`TECHNICALLY_COMPLETE_AWAITING_SIA_ATTESTATION` means the internal technical
chain is complete. This does not replace the official attestation from the
competent SIA sub-commission.
