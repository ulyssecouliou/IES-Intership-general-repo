Implementation Status
=====================

This page is the concise implementation contract for manager and developer
reviews. The detailed source-traced status is maintained in
``docs/project/SIA3802_SIA4010_IMPLEMENTATION_STATUS.md``.

Claim Boundary
--------------

The product performs automated checks where IESVE exposes a comparable value,
readiness checks where the standards require additional inputs, and strict
evidence tracking for official SIA 4010 validation. It does not issue an
official SIA certificate.

Implemented End-to-End Checks
-----------------------------

* VE room, surface, construction and opening extraction;
* SIA 380/2 Tables 2 to 9 reference-project input diagnostics;
* EN 410 glazing-value provenance guardrails;
* Table 1 cooling-need screening when profiles are available;
* Table 4 ventilation-control comparison when all identifiers are available;
* EER, SEER and SCOP limit checks by system class and capacity band;
* room-by-room annual SIA 180 upper/lower-curve hour counting when every required
  APS series and the window-operability state are available;
* reviewed whole-project/reference comparison evidence for the final SIA 380/2
  method gate;
* SIA 4010 readiness resolution for 24 exact variants and classes 1A through 5.

Conservative Integration Boundaries
-----------------------------------

* SIA 2024 use categories and SIA 387/4 lighting categories require reviewed
  mapping files;
* annual comfort additionally requires reviewed project metadata and an exact
  match between the approved and active VE weather filenames;
* component deviations from SIA 380/2 Tables 2 to 9 are reference-project
  diagnostics, not standalone building-compliance failures;
* Table 7 ``EER+`` is not substituted by another efficiency metric;
* design power requires dedicated design-day results;
* official SIA 4010 workbook transfer remains blocked until each official
  workbook is supplied;
* official results and class validation remain external reviewer decisions.

Allowed Readiness Statuses
--------------------------

The variant/class readiness resolver returns ``NOT_CHECKABLE``,
``EVIDENCE_INCOMPLETE``, ``READY_FOR_OFFICIAL_REVIEW`` or
``OFFICIAL_RESULTS_RECORDED``. The last status means that result rows were
ingested and checked for file traceability; it does not grant ``VALIDATED``, a
certificate or a non-zero official score without SIA sub-commission attestation.

Quality Gates
-------------

The project uses deterministic unit tests, the release validator, English-only
Python documentation checks, Sphinx builds and a final real-VE Run-button
acceptance test.
