Swiss SIA Compliance Checker
============================

Professional IESVE Run-button workflow for Swiss SIA 380/2:2022 readiness
checks and SIA 4010:2023 validation-evidence tracking.

This documentation is written in English as the canonical source. French,
Italian, and German versions can be generated from gettext translation catalogs.

.. warning::

   The checker produces readiness and audit artifacts. The generated workbook
   and evidence pack are not official SIA certificates by themselves; official
   certification or validation remains a separate decision by the responsible
   authority after reviewing the required evidence.

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: User Documentation

   user_guide
   reporting_guide
   reference_model_guide
   manager_reference_integration

.. toctree::
   :maxdepth: 2
   :caption: Technical Documentation

   architecture
   compliance_methodology
   compliance_coverage_audit
   implementation_status
   sia3802_gap_audit
   documentation_quality
   developer_guide
   api_reference
   multilingual_documentation
   glossary

Project Status
--------------

The current product level is a professional MVP:

* automated and partial SIA 380/2 checks where VE data is available;
* conservative SIA 4010 readiness tracking;
* client-facing Excel workbook with manager dashboard;
* explicit separation between automated checks, assumptions, and official
  validation evidence.

The project is not yet a complete certification engine. Missing MSP work is
tracked in the report and in the compliance methodology.
