SIA Compliance Coverage Audit
=============================

Audit date: 2026-06-30

Audited local sources:

* ``references/standards/SIA 380-2-2022 FR.pdf`` - 64 pages.
* ``references/standards/SIA 4010-2023 FR.pdf`` - 56 pages.

Audited implementation:

* ``swiss_sia/config.py``
* ``swiss_sia/sia380_checker.py``
* ``swiss_sia/sia4010_checker.py``
* ``swiss_sia/excel_report.py``

Professional Conclusion
-----------------------

The current checker is a professional readiness and audit product, not a full
certification engine yet.

The implementation correctly avoids making unsupported SIA 4010 pass/fail
claims. It also implements the main directly checkable SIA 380/2 envelope and
opening values where IESVE currently exposes reliable data.

However, the full SIA 380/2 and SIA 4010 compliance scope is not yet complete.
Several requirements depend on additional VE extraction, external SIA standards,
official SIA 4010 test packages, reference result comparisons, and reviewer
sign-off.

Coverage Snapshot
-----------------

The current ``SIA_DATA_COVERAGE_MATRIX`` contains 27 tracked compliance data
items.

.. list-table::
   :header-rows: 1
   :widths: 30 20 50

   * - Status
     - Count
     - Meaning
   * - ``AUTOMATED``
     - 4
     - Extracted and checked directly from the VE model with current code.
   * - ``PARTIAL``
     - 10
     - Partly extracted or reported, but not sufficient for a final SIA claim.
   * - ``NOT_IMPLEMENTED``
     - 8
     - Known PDF requirement or evidence family, not yet extracted/checkable.
   * - ``EVIDENCE_SCAN``
     - 5
     - Evidence can be detected, but official files are required before validation.

SIA 380/2 Direct Values
-----------------------

The following values are confirmed from the local SIA 380/2 PDF and are present
in ``config.py``.

.. list-table::
   :header-rows: 1
   :widths: 26 22 22 30

   * - Criterion
     - PDF source
     - Current value in code
     - Implementation status
   * - Window U-value ``Uw``
     - Table 2, PDF page 32
     - Limit 1.10 W/(m2.K), target 0.88 W/(m2.K)
     - ``AUTOMATED`` for extracted external windows.
   * - Glazing solar factor ``g_perp``
     - Table 2, PDF page 32
     - Limit/target 0.50
     - ``PARTIAL`` unless ``VECdbConstruction.get_g_values().bs_en_410`` is available or reviewer evidence proves comparability.
   * - Visible light transmittance
     - Table 2, PDF page 32
     - Limit/target 0.70
     - ``PARTIAL``; extracted from VE/CDB aliases when available, otherwise evidence is requested.
   * - Window frame fraction
     - Table 2, PDF page 32
     - Limit/target 0.25
     - ``PARTIAL``; extracted from VE/CDB frame aliases when available, otherwise facade evidence is requested.
   * - Glazing ratio
     - Table 2, PDF page 32
     - Delegated to SIA 2024
     - Reported only as design review, not as a SIA 380/2 pass/fail threshold.
   * - Infiltration by net floor area
     - Table 2, PDF page 32
     - 0.15 m3/(h.m2)
     - ``PARTIAL``; checkable only when VE units are comparable or converted.
   * - External wall U-value
     - Table 3, PDF page 36
     - Limit 0.20 W/(m2.K), target 0.14 W/(m2.K)
     - ``AUTOMATED`` for external wall surfaces.
   * - External wall against ground
     - Table 3, PDF page 36
     - Limit 0.30 W/(m2.K), target 0.20 W/(m2.K)
     - ``NOT_IMPLEMENTED`` as a distinct classifier; current code uses broad fallbacks.
   * - Internal partition variants
     - Table 3, PDF pages 36-37
     - Multiple limits/targets by type
     - ``NOT_IMPLEMENTED`` for full classification; not applied to external envelope checks.
   * - Ground/intermediate floor variants
     - Table 3, PDF page 37
     - Multiple limits/targets by adjacency
     - ``PARTIAL``; current code uses a conservative floor fallback.
   * - Flat roof U-value
     - Table 3, PDF page 37
     - Limit 0.20 W/(m2.K), target 0.14 W/(m2.K)
     - ``AUTOMATED`` for surfaces classified as roof.

SIA 380/2 Ventilation And AHU
-----------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 28 42

   * - Requirement family
     - PDF source
     - Current implementation status
   * - Required supply/extract airflow
     - Table 2, PDF page 33
     - ``PARTIAL``. The code checks data presence, but final values depend on SIA 2024 use categories.
   * - Ventilation efficiency
     - Table 2, PDF page 33
     - Configured, not yet automatically validated.
   * - Duct airtightness class
     - Table 2, PDF page 33
     - Configured, not yet extracted from VE.
   * - AHU airtightness class
     - Table 2, PDF page 33
     - Configured, not yet extracted from VE.
   * - AHU and duct heat transfer values
     - Table 2, PDF pages 33-34
     - Configured, not yet extracted from VE.
   * - Supply/extract pressure drops
     - Table 2, PDF page 34
     - Configured, not yet extracted from VE.
   * - Heat recovery pressure drop and efficiency
     - Table 2, PDF page 34
     - Configured, not yet extracted from VE.
   * - Fan control and mono/multizone control class
     - Table 2 and Table 4, PDF pages 34 and 37
     - ``NOT_IMPLEMENTED`` as a final check. Requires VE HVAC control mapping.

SIA 380/2 Cooling, Heating, PV, And Shading
-------------------------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 28 42

   * - Requirement family
     - PDF source
     - Current implementation status
   * - Air-cooled chiller EER/SEER
     - Table 5, PDF page 38
     - Values are configured, but generator type/power/EER extraction is ``NOT_IMPLEMENTED``.
   * - Water-cooled chiller EER/SEER
     - Table 6, PDF page 38
     - Values are configured, but generator type/power/EER extraction is ``NOT_IMPLEMENTED``.
   * - Auxiliary cooling/fan/pump shares
     - Text around PDF page 39
     - Not yet represented as a checker requirement.
   * - Air-water heat pump SCOP
     - Table 8, PDF page 39
     - Values are configured, but generator type/power/SCOP extraction is ``NOT_IMPLEMENTED``.
   * - Ground-source heat pump SCOP
     - Table 9, PDF page 39
     - Values are configured, but generator type/power/SCOP extraction is ``NOT_IMPLEMENTED``.
   * - PV sizing and conversion efficiency
     - Table 2, PDF page 35
     - Values are configured, but PV extraction is not yet automated.
   * - Solar protection categories
     - Table 10, PDF page 46
     - Values are configured, but shading type/control extraction is ``NOT_IMPLEMENTED``.

SIA 380/2 Method Requirements
-----------------------------

The PDF scope is not limited to single component thresholds. Full compliance
also needs auditable dynamic simulation assumptions and results.

.. list-table::
   :header-rows: 1
   :widths: 32 28 40

   * - Method requirement
     - Source
     - Current implementation status
   * - Climate/weather evidence
     - SIA 380/2 method sections; SIA 4010 climate complements
     - ``PARTIAL``. The report can request evidence, but weather metadata extraction is incomplete.
   * - SIA 2024 use category mapping
     - SIA 380/2 Table 2 references
     - ``PARTIAL``. Needs explicit room-to-SIA-use mapping.
   * - Internal gains and schedules
     - SIA 2024 / SIA 387/4 references
     - ``PARTIAL`` for gains, ``NOT_IMPLEMENTED`` for full schedule export.
   * - Annual heating/cooling demand from dynamic results
     - SIA 380/2 method; SIA 4010 Test 7
     - ``PARTIAL``. APS/Vista results are read, but official class/test export is not complete.
   * - Hourly temperatures and overheating indicators
     - SIA 380/2 method; SIA 4010 tests 4-6
     - ``PARTIAL``. Current report reads available values but does not complete all official scenarios.

SIA 4010 Coverage
-----------------

SIA 4010 is handled conservatively and correctly as validation readiness.
The standard validates software/method workflows through official tests; it
does not give enough standalone tolerances to let this checker declare a final
SIA 4010 pass without official evidence.

.. list-table::
   :header-rows: 1
   :widths: 18 38 44

   * - Test
     - PDF source
     - Current implementation status
   * - Test 1
     - Table 62, PDF page 46
     - ``NOT_CHECKABLE`` until the official base-envelope test, reference outputs, and evaluation file are provided.
   * - Test 2
     - Table 62 and Table 65, PDF pages 46 and 52
     - ``NOT_CHECKABLE`` until solar protection control variants and official comparisons are provided.
   * - Test 3
     - Table 62 and Table 65, PDF pages 46 and 52
     - ``NOT_CHECKABLE`` until lighting control variants and official comparisons are provided.
   * - Test 4
     - Table 62, PDF page 46
     - ``NOT_CHECKABLE`` until the official single-room air-system test evidence is provided.
   * - Test 5
     - Table 62 and Table 66, PDF pages 46 and 52
     - ``NOT_CHECKABLE`` until multizone AHU variant evidence is provided.
   * - Test 6
     - Table 62, PDF page 46
     - ``NOT_CHECKABLE`` until three-level ventilation evidence is provided.
   * - Test 7
     - Table 62, PDF page 46
     - ``NOT_CHECKABLE`` until heating/cooling system energy evidence and official comparisons are provided.

Validation Classes
------------------

The class mapping in the code matches SIA 4010 Table 63, PDF page 48.

.. list-table::
   :header-rows: 1
   :widths: 12 28 60

   * - Class
     - Required tests
     - Current status
   * - ``1A``
     - Tests 1 and 2A
     - Evidence scan only; no official validation without files.
   * - ``1B``
     - Tests 1 and 2
     - Evidence scan only; no official validation without files.
   * - ``2A``
     - Tests 1, 2A, 3A-3F
     - Evidence scan only; no official validation without files.
   * - ``2B``
     - Tests 1-3
     - Evidence scan only; no official validation without files.
   * - ``3``
     - Tests 1 and 4-6
     - Evidence scan only; no official validation without files.
   * - ``4A``
     - Tests 1, 2A, 3A-3F, 4-7
     - Evidence scan only; no official validation without files.
   * - ``4B``
     - Tests 1-7
     - Evidence scan only; no official validation without files.
   * - ``5``
     - Test 7
     - Evidence scan only; no official validation without files.

Known Gaps Before A Full Certification Claim
--------------------------------------------

The following gaps must be closed before the tool can support a full
professional compliance claim:

1. Extract or import SIA 2024 room-use mapping.
2. Extract weather file, DRY/SIA 2028 metadata, scenario, timestep, and
   preconditioning evidence.
3. Extract visible transmittance, frame fraction, shading type, shading category,
   and shading controls.
4. Replace broad floor/wall fallbacks with full adjacency classification.
5. Extract ventilation system type, airflow bands, fan control, duct/AHU leakage,
   pressure drops, heat recovery, humidification, and AHU location.
6. Extract cooling generator type, power band, EER/SEER, part-load data, pumps,
   storage, heat rejection, and free cooling.
7. Extract heating generator type, power band, SCOP or SIA 384/3 evidence,
   storage, distribution, auxiliary energy, solar thermal, and CHP where present.
8. Extract lighting power and SIA 387/4 lighting/daylight/presence control class.
9. Extract PV module count/area/orientation/tilt/peak coefficient/performance
   factor when PV is relevant.
10. Read and classify official SIA 4010 evidence files by selected validation
    class, then parse official workbook statuses without inventing tolerances.
11. Keep the final wording as readiness/audit until the official SIA evidence
    pack is complete and reviewed.

Acceptance Rule For Reports
---------------------------

The report may say:

* the model has been audited against available SIA 380/2 direct checks;
* missing or partial evidence has been identified;
* APS/Vista dynamic outputs were read when available;
* SIA 4010 validation evidence is incomplete or not checkable unless official
  evidence exists.

The report must not say:

* the model is fully SIA certified;
* all SIA 380/2 requirements are complete;
* IESVE or the model has passed SIA 4010 only because this checker ran.
