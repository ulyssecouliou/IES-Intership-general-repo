---
name: release-check
description: Runs the complete conservative repository release gate and returns a concise evidence-backed result.
disable-model-invocation: true
allowed-tools: Bash(git status *) Bash(git diff *) Bash(python -m unittest *) Bash(python -m compileall *) Bash(python scripts/quality/validate_release.py)
---

# Release Check

Run from the repository root:

1. `git status --short`
2. `python -m unittest discover -s tests -p "test_*.py"`
3. `python -m compileall -q swiss_sia scripts Run_VE_Swiss_Compliance.py Run_VE_Swiss_Reference_Model.py`
4. `python scripts/quality/validate_release.py`
5. `git diff --check`

Do not install missing dependencies automatically. Report the missing package and approved installation command instead.

Return:

- overall `PASS`, `WARNING`, or `FAIL`;
- test and release-check counts;
- exact failing controls;
- whether failures are code defects, environment prerequisites, optional evidence gaps, or real-VE qualification gaps;
- confirmation that no commit, push or artifact publication occurred.
