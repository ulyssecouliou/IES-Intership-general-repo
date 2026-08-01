"""Atomic continuity workflow for Test 2A diagnostic 2E1 qualification.

The native CDB probe is necessarily executed inside VE.  Once its immutable
report and checksum exist, this module immediately rebuilds the source-bound
Test 2A bundle and verifies that the resulting receipt still refuses model
mutation.  A successful storage probe can therefore never be mistaken for an
authorized generator.
"""

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, Union

from ..exceptions import ConfigurationError
from .test2a_shading_qualification import (
    qualify_test2a_2e1_optical_setters,
)
from .test2a_source_bundle import build_test2a_source_bound_bundle


@dataclass(frozen=True)
class Test2A2E1OpticalWorkflowReceipt:
    """Paths and fail-closed status produced by the continuity workflow."""

    report_path: Path
    bundle_status: str
    bundle_audit_path: Path
    mutation_supported: bool

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe mapping for VEScripts and the native UI."""

        payload = asdict(self)
        payload["report_path"] = str(self.report_path)
        payload["bundle_audit_path"] = str(self.bundle_audit_path)
        return payload


def run_test2a_2e1_optical_workflow(
    iesve_module: Any,
    project: Any,
    project_path: Union[str, Path],
    repository_root: Union[str, Path],
) -> Test2A2E1OpticalWorkflowReceipt:
    """Qualify storage, rebuild the bundle and reject any mutation claim."""

    project_root = Path(project_path)
    repository = Path(repository_root)
    report_path = Path(
        qualify_test2a_2e1_optical_setters(
            iesve_module,
            project,
            repository_root=repository,
        )
    )
    if not report_path.is_file():
        raise ConfigurationError(
            "2E1 optical qualification report was not written: {}".format(
                report_path
            )
        )
    bundle = build_test2a_source_bound_bundle(
        project_root,
        repository,
    )
    audit_path = Path(bundle.audit_path)
    if not audit_path.is_file():
        raise ConfigurationError(
            "Rebuilt Test 2A bundle audit was not written: {}".format(
                audit_path
            )
        )
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    if (
        bundle.mutation_supported is not False
        or audit.get("mutation_supported") is not False
    ):
        raise ConfigurationError(
            "2E1 storage qualification must not authorize Test 2A mutation"
        )
    if audit.get("status") != bundle.status:
        raise ConfigurationError(
            "Rebuilt Test 2A audit status does not match its receipt"
        )
    return Test2A2E1OpticalWorkflowReceipt(
        report_path=report_path,
        bundle_status=bundle.status,
        bundle_audit_path=audit_path,
        mutation_supported=False,
    )
