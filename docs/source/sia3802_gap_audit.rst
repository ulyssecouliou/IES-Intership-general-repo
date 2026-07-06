SIA 380/2 Compliance Gap Audit
==============================

Audit date: 2026-07-06

This page summarizes the strict SIA 380/2 compliance boundary used by the
checker. The full handoff document is kept in
``docs/project/SIA3802_FULL_COMPLIANCE_GAP_AUDIT.md``.

Current Position
----------------

The checker is a professional readiness and audit workflow. It is not a final
SIA compliance certificate.

Direct automated checks currently cover the most reliable VE/CDB data:

* external rooms and envelope surfaces;
* external wall and roof U-values when classification is reliable;
* external window Uw;
* EN 410 based glazing ``g_perp`` where IESVE exposes ``bs_en_410``;
* visible transmittance and frame fraction when CDB values are available;
* APS/Vista heating, cooling, temperature and expanded optional room outputs.

Main Gaps Before Complete SIA 380/2 Compliance
----------------------------------------------

The following items remain incomplete and must be treated as blockers before a
complete compliance claim:

* room-by-room SIA 2024 use-category mapping;
* official schedule evidence for occupancy, equipment, lighting, shading and
  HVAC;
* climate/weather basis evidence for the simulation setup;
* ventilation-control class, airflow-band and AHU evidence from SIA 380/2;
* heat/moisture recovery, pressure drops, leakage and AHU heat-transfer data;
* cooling generator type, capacity band, EER/SEER and part-load evidence;
* heating/heat-pump type, capacity band and SCOP evidence;
* final energy by system/carrier and complete generation/distribution/storage
  evidence;
* official or reviewer-accepted SIA 4010 comparison evidence for tests 1 to 7.

Safe Wording
------------

Use the following wording until every blocker above is resolved:

   The workbook is a SIA 380/2 and SIA 4010 readiness and audit report based on
   available VE model data, CDB construction data, APS/Vista outputs and
   source-traced rules. It is not a final SIA compliance certificate and does
   not replace official SIA 4010 validation or reviewer acceptance.

Implementation Rule
-------------------

When SIA 380/2 delegates an input or method to another standard, the checker
must request traceable evidence instead of inventing a threshold. This applies
especially to SIA 2024 profiles, SIA 2028 climate basis, SIA 382/1 ventilation
assumptions, SIA 384/3 heating evidence, SIA 387/4 lighting control and
SIA 2056 electricity evidence.
