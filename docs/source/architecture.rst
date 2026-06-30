Architecture
============

High-Level Flow
---------------

.. code-block:: text

   VE Run button
      |
      v
   Run_VE_Swiss_Compliance.py
      |
      v
   swiss_sia/app.py
      |
      +--> swiss_sia/data_extractor.py
      +--> swiss_sia/model_analyzer.py
      +--> swiss_sia/sia380_checker.py
      +--> swiss_sia/sia4010_checker.py
      +--> swiss_sia/health_score.py
      +--> swiss_sia/excel_report.py

Core Modules
------------

``Run_VE_Swiss_Compliance.py``
   Thin launcher intended for the VE Scripts window.

``main.py``
   Compatibility wrapper kept at the repository root for existing shortcuts.

``swiss_sia/app.py``
   Orchestrates extraction, checks, scoring, preflight checks, and report
   generation.

``config.py``
   Centralizes SIA values, source references, requirement matrix, weights, and
   report configuration.

``data_extractor.py``
   Isolates IESVE API calls and handles defensive extraction.

``model_analyzer.py``
   Converts raw VE API objects into normalized room, surface, opening, and
   system data structures.

``rule_engine.py``
   Applies named rules and accumulates structured alerts.

``sia380_checker.py``
   Runs automated and partial SIA 380/2 checks.

``sia4010_checker.py``
   Tracks SIA 4010 readiness and official evidence presence. It intentionally
   keeps validation tests as ``NOT_CHECKABLE`` without official evidence.

``health_score.py``
   Calculates the automated SIA 380/2 indicator and model health score.

``excel_report.py``
   Generates the professional Excel workbook.

Design Principles
-----------------

* Keep VE execution simple and robust.
* Keep official SIA evidence separate from model-quality heuristics.
* Never invent a threshold when the PDF refers to another standard.
* Prefer ``NOT_CHECKABLE`` over false pass/fail decisions.
* Make the workbook actionable for managers and reviewers.
