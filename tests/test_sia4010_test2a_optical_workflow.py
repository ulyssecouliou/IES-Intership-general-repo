"""Tests for the fail-closed Test 2A / 2E1 continuity workflow."""

import json
import shutil
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.test2a_optical_workflow import (
    run_test2a_2e1_optical_workflow,
)


ROOT = Path(__file__).resolve().parents[1]
WORK_ROOT = ROOT / ".codex_tmp" / "test2a_optical_workflow"


class Test2A2E1OpticalWorkflowTests(unittest.TestCase):
    """A storage PASS must rebuild, but never authorize, the model bundle."""

    def setUp(self):
        self.project = WORK_ROOT / self._testMethodName
        if self.project.exists():
            shutil.rmtree(self.project)
        self.project.mkdir(parents=True)
        self.report = self.project / "optical.json"
        self.report.write_text('{"status":"PASS"}\n', encoding="utf-8")
        self.audit = self.project / "source_binding_audit.json"

    def tearDown(self):
        if self.project.exists():
            shutil.rmtree(self.project)

    def _bundle(self, *, status="STORAGE_READY", mutation=False):
        self.audit.write_text(
            json.dumps(
                {
                    "status": status,
                    "mutation_supported": mutation,
                }
            )
            + "\n",
            encoding="utf-8",
        )
        return SimpleNamespace(
            status=status,
            audit_path=self.audit,
            mutation_supported=mutation,
        )

    @mock.patch(
        "swiss_sia.reference_model.sia4010.test2a_optical_workflow."
        "build_test2a_source_bound_bundle"
    )
    @mock.patch(
        "swiss_sia.reference_model.sia4010.test2a_optical_workflow."
        "qualify_test2a_2e1_optical_setters"
    )
    def test_pass_rebuilds_bundle_and_returns_non_mutating_receipt(
        self,
        qualify,
        build,
    ):
        qualify.return_value = self.report
        build.return_value = self._bundle(
            status="RUNTIME_STORAGE_QUALIFIED_MODEL_BINDING_REQUIRED"
        )
        receipt = run_test2a_2e1_optical_workflow(
            object(),
            object(),
            self.project,
            ROOT,
        )
        self.assertEqual(receipt.report_path, self.report)
        self.assertEqual(
            receipt.bundle_status,
            "RUNTIME_STORAGE_QUALIFIED_MODEL_BINDING_REQUIRED",
        )
        self.assertFalse(receipt.mutation_supported)
        qualify.assert_called_once()
        build.assert_called_once_with(self.project, ROOT)

    @mock.patch(
        "swiss_sia.reference_model.sia4010.test2a_optical_workflow."
        "build_test2a_source_bound_bundle"
    )
    @mock.patch(
        "swiss_sia.reference_model.sia4010.test2a_optical_workflow."
        "qualify_test2a_2e1_optical_setters"
    )
    def test_bundle_mutation_claim_fails_closed(self, qualify, build):
        qualify.return_value = self.report
        build.return_value = self._bundle(mutation=True)
        with self.assertRaisesRegex(
            ConfigurationError,
            "must not authorize",
        ):
            run_test2a_2e1_optical_workflow(
                object(),
                object(),
                self.project,
                ROOT,
            )

    @mock.patch(
        "swiss_sia.reference_model.sia4010.test2a_optical_workflow."
        "build_test2a_source_bound_bundle"
    )
    @mock.patch(
        "swiss_sia.reference_model.sia4010.test2a_optical_workflow."
        "qualify_test2a_2e1_optical_setters"
    )
    def test_audit_receipt_status_mismatch_fails_closed(
        self,
        qualify,
        build,
    ):
        qualify.return_value = self.report
        bundle = self._bundle(status="AUDIT_STATUS")
        bundle.status = "RECEIPT_STATUS"
        build.return_value = bundle
        with self.assertRaisesRegex(
            ConfigurationError,
            "status does not match",
        ):
            run_test2a_2e1_optical_workflow(
                object(),
                object(),
                self.project,
                ROOT,
            )


if __name__ == "__main__":
    unittest.main()
