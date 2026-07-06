Developer Guide
===============

Code Language Policy
--------------------

All source-code documentation must be written in English:

* module docstrings;
* class and function docstrings;
* inline comments;
* developer-facing exceptions;
* test names;
* Sphinx documentation pages.

Every project-owned Python module, class, and function must have a meaningful
docstring. Comments should explain intent, evidence handling, API constraints,
or non-obvious compliance logic; they should not restate each assignment line by
line.

The release validator enforces this policy for the project Python files under
``swiss_sia/``, ``scripts/``, ``docs/tools/`` and the root run-button launchers.

User-facing workbook labels can later be localized through an i18n layer. They
should not be translated directly in multiple places.

Adding a SIA 380/2 Rule
-----------------------

1. Add the value and source reference to ``config.py``.
2. Add or update the requirement row in ``SIA_COMPLIANCE_REQUIREMENT_MATRIX``.
3. Add the rule in ``sia380_checker.py`` only when the VE mapping is reliable.
4. Use ``PARTIAL`` or ``NOT_CHECKABLE`` when the mapping is not final.
5. Add report logic in ``excel_report.py`` only if the new rule needs a
   specific action, limit, or evidence message.
6. Run Python compilation and a smoke test.

Adding SIA 4010 Evidence Support
--------------------------------

SIA 4010 support must remain conservative:

* detect official evidence files;
* classify evidence families;
* never mark a validation test as passed without official comparison results;
* keep validation class selection explicit.

Recommended Checks Before Delivery
----------------------------------

.. code-block:: powershell

   python -m py_compile main.py Run_VE_Swiss_Compliance.py swiss_sia/*.py scripts/probes/*.py

For Excel output:

* open the workbook;
* check the dashboard visually;
* scan for formula errors;
* confirm ``NOT_CHECKABLE`` is not shown as a red failure.

Repository Hygiene
------------------

Generated workbooks, logs, probes, and temporary rendering folders should not be
committed unless specifically requested.
