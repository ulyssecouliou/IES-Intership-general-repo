IESVE User Guide
================

Purpose
-------

The user workflow is intentionally simple: open the target VE project, run one
script from the VE Scripts window, then review the generated Excel workbook.

Run Workflow
------------

1. Open the client VE project in IESVE.
2. Open the VE Scripts window.
3. Select ``Run_VE_Swiss_Compliance.py``.
4. Click ``Run``.
5. Open the latest workbook in the ``reports`` folder.

The script does not require PowerShell for the end user.

Generated Files
---------------

Each run creates a timestamped workbook in ``reports`` and updates the latest
alias when possible:

* ``Swiss_Compliance_Report__<project>__<model>__<timestamp>.xlsx``
* ``Swiss_Compliance_Report.xlsx``

If the latest alias is locked by Excel, the timestamped workbook remains the
source of truth.

Safe Interpretation
-------------------

The workbook can support these statements:

* automated SIA 380/2 readiness review for directly extracted VE data;
* SIA 4010 evidence readiness matrix;
* model-quality and data-completeness review.

The workbook must not support these statements:

* the model is fully SIA compliant;
* IESVE or the model is officially SIA 4010 validated;
* every SIA 380/2 criterion has been fully automated.

Common Issues
-------------

``NOT_CHECKABLE``
   The script cannot decide without external evidence, official files, or a
   confirmed VE mapping.

``NOT_IMPLEMENTED``
   The criterion is known and traceable, but automation is not implemented yet.

``FAIL``
   A currently automated or partial check found a value outside the retained
   limit.

``PARTIAL_CHECK``
   The report has useful evidence, but the current data is not enough for a
   complete compliance verdict.

