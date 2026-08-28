"""Every operator-facing launcher must purge stale VE-cached modules.

VEScripts keeps one Python interpreter alive across Run-button presses. A
module imported by an earlier run stays in ``sys.modules`` after its source
file changes on disk, so a launcher pressed on its own can import a stale
version of the repository package and fail with ``ImportError`` on a helper
that exists on disk.

This was observed on 2026-08-12: ``Run_VE_SIA4010_Test1_Qualify_Runtime_Inputs``
raised ``ImportError: cannot import name
'build_zero_mechanical_ventilation_payload'`` while the function was present in
``test1_runtime_inputs.py``, because VE still held the pre-correction module.

The purge is a property of the launcher, not of the caller: a launcher that can
be pressed directly must not depend on a parent having purged for it.
"""

from __future__ import annotations

import ast
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROBES = ROOT / "scripts" / "probes"

#: Launchers an operator can press directly in the VE Python navigator.
#: Paths are (directory, filename) pairs; the first group lives at the repo
#: root, the second under scripts/probes/.
OPERATOR_FACING_LAUNCHERS = (
    (ROOT, "Run_VE_SIA4010_Test1_Fast_Start.py"),
    (ROOT, "Run_VE_SIA4010_Test1_Active_Case_One_Click.py"),
    (ROOT, "Run_VE_SIA4010_Test1_Qualify_Runtime_Inputs.py"),
    (ROOT, "Run_VE_SIA4010_Simulate_Active_Case.py"),
    (ROOT, "Run_VE_SIA4010_Capture_Active_Template.py"),
    (PROBES, "Run_VE_SIA4010_Verify_Template_Model.py"),
    (PROBES, "Run_VE_SIA4010_Test1E_Optical_Readback.py"),
    (PROBES, "Run_VE_SIA4010_Test1E_Apply_Provisional_Angular_Diagnostic.py"),
    (PROBES, "Run_VE_SIA4010_Test1E_Apply_Bracketed_Sensitivity.py"),
    (PROBES, "Run_VE_SIA4010_Test1E_Envelope_Readback.py"),
    # Not a Test 1 launcher, but it rebuilds project-local inputs from this
    # package for Tests 2A/3/4-7, so it carries the identical hazard.
    (ROOT, "Run_VE_SIA4010_Prepare_Case_Scenario.py"),
)

PACKAGE = "swiss_sia.reference_model"


def _deletes_sys_modules(tree: ast.AST) -> bool:
    """Return whether the tree contains a real ``del sys.modules[...]``."""

    for node in ast.walk(tree):
        if not isinstance(node, ast.Delete):
            continue
        for target in node.targets:
            if not isinstance(target, ast.Subscript):
                continue
            value = target.value
            if (
                isinstance(value, ast.Attribute)
                and value.attr == "modules"
                and isinstance(value.value, ast.Name)
                and value.value.id == "sys"
            ):
                return True
    return False


def _names_the_package(tree: ast.AST) -> bool:
    """Return whether the tree references the repository package by name."""

    return any(
        isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and node.value == PACKAGE
        for node in ast.walk(tree)
    )


def _purges_reference_model_package(source: str) -> bool:
    """Return whether the module effectively purges the cached package.

    The purge must be *reachable when the operator runs the launcher*, not
    merely present in the file.  Two shapes are accepted:

    * module-level statements performing the deletion directly;
    * a helper performing the deletion that is called from ``run()``.

    A helper that is defined but never called does not count: on 2026-08-12 a
    module-level purge had to be moved into ``run()`` because executing it at
    import time invalidated classes that already-imported test modules held.
    An unreachable helper would reintroduce the original ImportError silently.
    """

    tree = ast.parse(source)

    module_level = [
        node
        for node in tree.body
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
    ]
    if any(
        _deletes_sys_modules(node) and _names_the_package(node) for node in module_level
    ):
        return True

    purging_helpers = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and _deletes_sys_modules(node)
        and _names_the_package(node)
    }
    if not purging_helpers:
        return False

    run_functions = [
        node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "run"
    ]
    for run_function in run_functions:
        for node in ast.walk(run_function):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in purging_helpers
            ):
                return True
    return False


class LauncherModulePurgeTests(unittest.TestCase):

    def test_every_operator_facing_launcher_purges_cached_package(self) -> None:
        missing = []
        for directory, name in OPERATOR_FACING_LAUNCHERS:
            path = directory / name
            if not path.is_file():
                self.skipTest("Launcher missing: {}".format(name))
            if not _purges_reference_model_package(path.read_text(encoding="utf-8")):
                missing.append(name)
        self.assertEqual(
            missing,
            [],
            msg=(
                "These launchers can be pressed directly in VE but do not drop "
                "the cached '{}' package, so a corrected module would not be "
                "re-imported: {}".format(PACKAGE, missing)
            ),
        )

    def test_detector_rejects_a_comment_only_mention(self) -> None:
        """A launcher that merely mentions the purge must not pass."""

        self.assertFalse(
            _purges_reference_model_package(
                "# del sys.modules['swiss_sia.reference_model']\n" "import sys\n"
            )
        )

    def test_detector_accepts_the_module_level_loop_shape(self) -> None:
        self.assertTrue(
            _purges_reference_model_package(
                "import sys\n"
                "for name in tuple(sys.modules):\n"
                "    if name == 'swiss_sia.reference_model':\n"
                "        del sys.modules[name]\n"
            )
        )

    def test_detector_accepts_a_helper_called_from_run(self) -> None:
        self.assertTrue(
            _purges_reference_model_package(
                "import sys\n"
                "def _purge():\n"
                "    for name in tuple(sys.modules):\n"
                "        if name == 'swiss_sia.reference_model':\n"
                "            del sys.modules[name]\n"
                "def run():\n"
                "    _purge()\n"
            )
        )

    def test_detector_rejects_a_helper_that_run_never_calls(self) -> None:
        """An unreachable purge would silently reintroduce the ImportError."""

        self.assertFalse(
            _purges_reference_model_package(
                "import sys\n"
                "def _purge():\n"
                "    for name in tuple(sys.modules):\n"
                "        if name == 'swiss_sia.reference_model':\n"
                "            del sys.modules[name]\n"
                "def run():\n"
                "    return None\n"
            )
        )


if __name__ == "__main__":
    unittest.main()
