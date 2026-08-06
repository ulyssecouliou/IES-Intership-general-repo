# -*- coding: utf-8 -*-
"""Make the repository root importable by the tests.

Without this file, `pytest engine/tests/` -- the form the CI uses, see
`.github/workflows/engine-tests.yml` -- fails with `No module named 'engine'`:
unlike `python -m pytest`, the direct invocation does not add the current
directory to `sys.path`. A conftest at the root is enough for pytest to insert
that path.

Verified: without it, collection aborts on a ModuleNotFoundError.
"""

import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
