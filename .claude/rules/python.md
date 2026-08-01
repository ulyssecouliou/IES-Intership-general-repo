---
paths:
  - "**/*.py"
---

# Python Rules

- Preserve compatibility with the Python version embedded in the target IESVE release.
- Keep imports of `iesve` behind runtime boundaries so normal Python tests remain executable.
- Use type hints and dataclasses where they clarify contracts, without adding an unsupported runtime dependency.
- Catch exceptions only where the code can add context, translate an API boundary, or fail conservatively.
- Log stage, action and outcome without exposing proprietary input data or secrets.
- Add focused unit tests for success, invalid data, unavailable API capabilities and failed readback.
- Do not use Python scripts as an indirect way to delete, overwrite or mass-rewrite user files.
