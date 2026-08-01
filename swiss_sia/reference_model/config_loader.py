"""JSON configuration loading with strict provenance checks."""

import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

from .compliance_config import ParameterRegistry, build_default_registry
from .exceptions import ConfigurationError


SUPPORTED_SCHEMA_VERSIONS = {"1.0"}


def load_configuration(
    path: Optional[Union[str, Path]] = None,
    base_registry: Optional[ParameterRegistry] = None,
) -> ParameterRegistry:
    """Load a strict JSON override document onto the default registry."""

    registry = base_registry or build_default_registry()
    if path is None:
        return registry

    config_path = Path(path)
    if not config_path.is_file():
        raise ConfigurationError("Configuration file not found: {}".format(config_path))
    try:
        payload: Dict[str, Any] = json.loads(config_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConfigurationError("Unable to read configuration: {}".format(exc)) from exc

    unknown_top_level = set(payload) - {"schema_version", "parameters", "metadata"}
    if unknown_top_level:
        raise ConfigurationError(
            "Unsupported top-level configuration fields: {}".format(
                sorted(unknown_top_level)
            )
        )
    schema_version = str(payload.get("schema_version", ""))
    if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ConfigurationError(
            "Unsupported schema_version '{}'; expected one of {}".format(
                schema_version, sorted(SUPPORTED_SCHEMA_VERSIONS)
            )
        )
    overrides = payload.get("parameters")
    if not isinstance(overrides, dict):
        raise ConfigurationError("'parameters' must be a JSON object")
    return registry.with_overrides(overrides)
