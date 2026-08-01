---
name: sia4010-evidence
description: Reviews or extends SIA 4010 test readiness, official evidence ingestion, validation classes and comparator hooks without falsely granting certification. Use for SIA 4010 tests, classes, evidence manifests, official workbooks, expected results, or candidate comparisons.
---

# SIA 4010 Evidence

1. Distinguish published PDF prevalidation requirements from official test files and accepted execution evidence.
2. Preserve the seven-test and validation-class contracts already represented in the repository.
3. Require recognized filenames, complete manifest metadata, referenced files, checksums where available and explicit reviewer/source fields.
4. Keep loader, expected-result, runner and comparator responsibilities separate.
5. Never interpret file presence alone as test PASS or software validation.
6. An official FAIL overrides PASS; missing or contradictory evidence remains not validated.
7. Add fixtures for valid, missing, malformed, ambiguous and conflicting evidence.
8. Keep SIA 4010 readiness separate from the SIA 380/2 compliance score.

End with a matrix of what is proven, pending official input, reviewer-dependent and not checkable.
