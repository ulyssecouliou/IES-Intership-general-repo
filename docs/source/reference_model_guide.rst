SIA-Compatible Reference Model
==============================

Purpose
-------

The three-room ``SIA_compatible_model`` is maintained as an internal golden
building model for SIA 380/2 readiness and regression testing. It is not a
substitute for the separate SIA 4010 prescribed test buildings and official
comparison workflow.

Current Priorities
------------------

#. Rerun the report after the APS metric-unit and project-evidence isolation
   corrections.
#. Replace the Dublin weather basis with the reviewed SIA 2028 DRY climate for
   the selected Swiss location and rerun Apache.
#. Complete project-specific SIA 2024 use mappings, SIA 387/4 lighting-control
   mappings and climate metadata.
#. Add infiltration, ventilation, people, equipment, lighting and auditable
   schedules to all three rooms.
#. Change ``STD_EXT2`` to ``bs_en_410 <= 0.50`` and ``tau_v >= 0.70``, or
   provide a reviewed active glazing-plus-shading g-total calculation.
#. Define the plant type, rated capacity, EER/SEER/SCOP, controls and auxiliary
   energy instead of relying on the generic ``SYST0000`` efficiency.
#. Export complete aligned annual temperature, occupancy and both SIA 180
   comfort-limit series, plus energy and system outputs.
#. Run separate heating and cooling design-day simulations with the prescribed
   preconditioning.
#. Complete and review the whole-project SIA 380/2 project/reference
   comparison.

Critical Product Boundary
-------------------------

One client or golden building model cannot validate every SIA 4010 class.
Tests 1 to 7 require the prescribed BESTEST cell, solar-control and lighting
variants, amphitheatre, multizone office AHU, restaurant/kitchen ventilation
and heating/cooling system models. Official specifications, evaluation
workbooks, candidate outputs, reference comparisons and class confirmation
remain mandatory before any official validation claim.

Detailed Working Document
-------------------------

The complete VE action tables, observed values, target diagnostics, evidence
filenames, APS output list and SIA 4010 test portfolio are maintained in:

``docs/project/SIA_COMPATIBLE_MODEL_REFERENCE_ACTIONS.md``

