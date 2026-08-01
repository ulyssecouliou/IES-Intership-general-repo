"""Compliance-ready Swiss reference-model generation for IESVE.

The package intentionally separates pure-Python geometry/configuration logic
from the :mod:`iesve` runtime adapter.  Importing this package outside IESVE is
therefore safe and is used by the unit-test suite.
"""

from .asset_manifest import AssetManifest, load_asset_manifest
from .compliance_config import ParameterRegistry, build_default_registry
from .workflow import ReferenceModelWorkflow, WorkflowOutcome

__all__ = [
    "AssetManifest",
    "ParameterRegistry",
    "ReferenceModelWorkflow",
    "WorkflowOutcome",
    "build_default_registry",
    "load_asset_manifest",
]

__version__ = "0.2.0"
