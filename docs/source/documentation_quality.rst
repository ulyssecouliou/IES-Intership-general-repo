Documentation Quality Audit
===========================

This page documents the quality gate used to make the codebase maintainable
after handover. The canonical documentation language is English. French,
Italian, and German documentation can be generated through Sphinx gettext
translation catalogs, but Python comments and docstrings remain English-only so
the API reference has one stable source of truth.

Audit Scope
-----------

The release validation checks the Python files owned by this project:

.. list-table::
   :header-rows: 1
   :widths: 30 45 25

   * - Area
     - Files
     - Documentation purpose
   * - Run-button launchers
     - ``main.py``, ``Run_VE_Swiss_Compliance.py``, ``Prepare_SIA4010_Evidence_Folder.py``, ``RUN_IESVE_EXTRACTION_PROBE.py``
     - Explain how a VE user starts the checker, prepares evidence, or runs diagnostics.
   * - Core package
     - ``swiss_sia/*.py``
     - Document extraction, normalization, SIA 380/2 checks, SIA 4010 evidence checks, scoring, Excel reporting, and evidence packaging.
   * - Quality tools
     - ``scripts/quality/*.py``
     - Document deterministic fixtures and release validation guardrails.
   * - Probe scripts
     - ``scripts/probes/*.py``
     - Document diagnostic scripts used to inspect available IESVE API functions.
   * - Legacy references
     - ``scripts/legacy/*.py``
     - Preserve older dashboard scripts as documented reference material.
   * - Documentation tooling
     - ``docs/source/conf.py`` and ``docs/tools/build_docs.py``
     - Document the Sphinx build configuration and developer documentation command.

Quality Rules
-------------

The release validator enforces the following documentation checks:

* every maintained Python file has a module docstring;
* every class, function, and method has a docstring;
* docstrings must be descriptive enough for generated API pages;
* comments and docstrings must be English-only;
* Sphinx entry points and manager-facing documentation files must exist;
* built HTML documentation should be available before a manager review.

API Documentation Strategy
--------------------------

The API reference uses Sphinx autodoc with full signatures and type hints.
Function parameters are therefore visible even when a function is documented by
a concise operational docstring. Public and private members are both included
because this project is intended for internal handover, auditability, and future
maintenance.

Presentation Outputs
--------------------

The recommended presentation artifacts are:

* ``docs/build/html/en/index.html`` for the full multi-page site;
* ``docs/build/singlehtml/en/index.html`` for a single-page manager handout;
* ``docs/build/gettext/*.pot`` for translation preparation.

Regeneration Commands
---------------------

Run these commands from the project root on a developer machine:

.. code-block:: powershell

   python docs/tools/build_docs.py --language en --builder html
   python docs/tools/build_docs.py --language en --builder singlehtml
   python docs/tools/build_docs.py --builder gettext

The VE run-button workflow does not depend on Sphinx. Documentation tooling is
kept outside the VE execution path so client-side compliance runs remain simple
and robust.
