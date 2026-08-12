"""Unit tests for ``ui.tk_safe``.

The real ``run_dialog`` needs a display; these tests focus on the
``HeadlessDialogRunner`` path used by unit tests and ``--probe`` launcher
runs, plus the graceful-degradation branches of ``run_dialog`` when Tkinter
is missing or ``Tk()`` raises.
"""

import sys
import unittest

from ui.tk_safe import DialogHandle, HeadlessDialogRunner, run_dialog


class HeadlessRunnerTests(unittest.TestCase):

    def test_headless_runner_captures_result_dict(self) -> None:
        def build(handle: DialogHandle):
            handle.root.title("noop")
            return {"choice": "OK"}

        runner = HeadlessDialogRunner()
        result = runner.run(build)
        self.assertEqual(result.result, {"choice": "OK"})
        self.assertEqual(result.closed_by, "HEADLESS_COMPLETED")
        self.assertIsNone(result.error)

    def test_headless_runner_records_stub_calls(self) -> None:
        def build(handle: DialogHandle):
            handle.root.title("t")
            handle.root.pack()
            handle.root.geometry("400x300")
            return None

        runner = HeadlessDialogRunner()
        result = runner.run(build)
        method_names = [c["method"] for c in result.root.calls]
        self.assertIn("title", method_names)
        self.assertIn("pack", method_names)
        self.assertIn("geometry", method_names)

    def test_headless_runner_captures_exceptions_without_reraising(self) -> None:
        def build(handle: DialogHandle):
            raise RuntimeError("boom")

        runner = HeadlessDialogRunner()
        result = runner.run(build)
        self.assertIsNotNone(result.error)
        self.assertIn("boom", result.error)
        self.assertEqual(result.closed_by, "HEADLESS_RAISED")

    def test_headless_runner_forwards_events(self) -> None:
        runner = HeadlessDialogRunner(events=[{"press": "OK"}])

        def build(handle: DialogHandle):
            return {"seen": handle.events}

        result = runner.run(build)
        self.assertEqual(result.result, {"seen": [{"press": "OK"}]})


class RunDialogGracefulDegradationTests(unittest.TestCase):

    def test_run_dialog_records_error_when_tkinter_import_fails(self) -> None:
        # Simulate the "no display" case by masking the tkinter module.
        saved = sys.modules.pop("tkinter", None)
        # Prevent re-import from finding the real module.
        sys.modules["tkinter"] = None  # type: ignore[assignment]
        try:
            handle = run_dialog(lambda h: None)
            self.assertEqual(handle.closed_by, "TK_UNAVAILABLE")
            self.assertIsNotNone(handle.error)
        finally:
            del sys.modules["tkinter"]
            if saved is not None:
                sys.modules["tkinter"] = saved


if __name__ == "__main__":
    unittest.main()
