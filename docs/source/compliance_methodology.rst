Compliance Methodology
======================

Scope
-----

The checker currently supports a professional readiness review for:

* SIA 380/2:2022 automated and partial checks;
* SIA 4010:2023 validation-evidence readiness.

It does not replace the licensed SIA standards, official test files, or the
responsible review authority.

SIA 380/2 Approach
------------------

The checker distinguishes four types of criteria:

``AUTOMATED``
   The criterion has a value in ``config.py``, a confirmed extraction path, and
   a rule implemented in Python.

``PARTIAL``
   The criterion is source-traced and useful data is available, but a final
   verdict still depends on a mapping, external standard, or additional
   evidence.

``NOT_IMPLEMENTED``
   The criterion is known and traceable but not automated yet.

``EXTERNAL_STANDARD_REQUIRED``
   The SIA PDF refers to another standard such as SIA 2024, SIA 387/4,
   SIA 382/1, SIA 384/3, SIA 2028, SIA 385/2, or SIA 2056. The checker must not
   invent a single threshold.

SIA 4010 Approach
-----------------

SIA 4010 validates a method or software capability through official tests and
evaluation files. It is not treated as a set of standalone building thresholds.

Therefore:

* all seven validation tests remain ``NOT_CHECKABLE`` without official evidence;
* evidence file presence is treated as readiness only;
* file content, official source, comparison validity, and validation class must
  still be reviewed manually.

Certification Guardrail
-----------------------

The report can support a readiness review. It cannot support a complete
certification claim until:

* all automated SIA 380/2 failures are resolved or justified;
* all partial checks are mapped and documented;
* all required external-standard inputs are available;
* official SIA 4010 tests and comparison files are complete;
* the responsible compliance authority signs off.

