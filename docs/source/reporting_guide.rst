Excel Reporting Guide
=====================

Workbook Structure
------------------

The generated workbook is designed for manager and reviewer use. The first
sheets are the most important:

``MANAGER DASHBOARD``
   Executive summary with key scores, alert distribution, coverage status, and
   top actions.

``CLIENT SUMMARY``
   Conservative client-facing interpretation, safe claims, and avoid statements.

``PREFLIGHT``
   Run readiness checks: active VE project, extracted rooms, envelope/openings,
   report folder, Excel writer, and SIA 4010 evidence availability.

``P1 REMEDIATION``
   Owner-ready action board for the highest priority blockers.

``ASSUMPTIONS LIMITS``
   Guardrails explaining what the report can and cannot prove.

``AUDIT LOG``
   Run metadata, report path, APS/Vista status, SIA 4010 evidence status,
   preflight counts, and certification guardrails for reviewer traceability.

``SUMMARY``
   Score summary for the automated SIA 380/2 indicator and model-health score.

``ACTION PLAN``
   Grouped remediation actions derived from the current model alerts.

``COMPLIANCE RESULTS``
   Category-level SIA 380/2 and SIA 4010 readiness results.

``SIA REQUIREMENTS``
   Source-traced requirement matrix with automation status and next actions.

``SIA DATA COVERAGE``
   Data, APS/Vista and external-evidence coverage by requirement.

``INPUT REQUEST``
   Owner-ready list of missing inputs/evidence to request from the model team,
   client or compliance reviewer.

``SIA4010 READINESS``
   Validation evidence and test readiness matrix.

``DYNAMIC RESULTS``
   APS/Vista dynamic indicators when the active VE environment exposes them.

``ALERT SUMMARY``
   Grouped alerts by construction, type, rule, severity, count, and affected
   area.

``ALERTS``
   Raw detailed alerts for technical review.

``DATA QUALITY``
   Extraction coverage and missing-data risks.

``DETAILED SCORES``
   Score components used by the dashboard.

``ROOMS``
   Extracted room data.

Scores
------

``SIA 380/2 Automated Compliance Indicator``
   Weighted indicator based only on implemented or partial SIA 380/2 checks.

``Health Score``
   Data-completeness and model-quality indicator.

``SIA 4010``
   Kept separate as an evidence-readiness status. It is not converted into a
   building pass/fail score.

Professional Wording
--------------------

Use cautious language in all manager/client communication:

* "readiness report";
* "automated checks currently implemented";
* "official evidence required";
* "not a final SIA certificate".

Avoid final-certification wording until every blocking item is resolved and
reviewed by the responsible compliance authority.
