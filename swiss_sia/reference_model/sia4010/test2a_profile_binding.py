"""Source-traced adapter from normalized SIA 2024 data to VE profiles.

The normalized usage schedules and native VE profile graph are deliberately
separate contracts.  This module converts only an explicitly supplied,
validated ``ve_profile_graph`` into the generic reference-model
``ProfileDefinition`` objects.  It never invents day/week/year mappings.
"""

import hashlib
import json
from dataclasses import dataclass
from typing import Any, Dict, Mapping, Tuple

from ..asset_manifest import Evidence, ProfileDefinition, TraceableField
from ..compliance_config import ValidationRange
from ..exceptions import ConfigurationError
from .normalized_external_inputs import NormalizedOfficeProfiles


def _json_value(value: Any) -> Any:
    """Convert immutable tuples and nested mappings to VE/JSON containers."""

    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_value(item) for item in value]
    return value


def _canonical_sha256(value: Mapping[str, Any]) -> str:
    """Return a deterministic SHA-256 for one normalized graph payload."""

    encoded = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True)
class Test2AProfileDefinitionBundle:
    """Native profile definitions and their three terminal output keys."""

    definitions: Tuple[ProfileDefinition, ...]
    output_profile_keys: Tuple[Tuple[str, str], ...]
    source_sha256: str
    graph_sha256: str

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe qualification input receipt."""

        return {
            "definitions": [
                definition.to_dict() for definition in self.definitions
            ],
            "output_profile_keys": dict(self.output_profile_keys),
            "source_sha256": self.source_sha256,
            "graph_sha256": self.graph_sha256,
        }


def build_test2a_profile_definitions(
    office_profiles: NormalizedOfficeProfiles,
    *,
    source_sha256: str,
) -> Test2AProfileDefinitionBundle:
    """Build exact generic profile definitions or fail before VE mutation."""

    source_digest = str(source_sha256).strip().lower()
    if (
        len(source_digest) != 64
        or any(character not in "0123456789abcdef" for character in source_digest)
    ):
        raise ConfigurationError(
            "SIA 2024 normalized source SHA-256 must be 64 lowercase "
            "hexadecimal characters"
        )
    graph = office_profiles.ve_profile_graph
    if graph is None:
        raise ConfigurationError(
            "SIA 2024 native VE profile graph is required before profile "
            "provisioning"
        )
    graph_payload = graph.to_dict()
    source_label = (
        "Authorized SIA 2024 normalized binding SHA-256 {}".format(
            source_digest
        )
    )
    definitions = []
    for node in graph.nodes:
        evidence = Evidence(
            description=(
                "Native VE {} profile transcribed from the authorized "
                "SIA 2024 calendar graph.".format(node.profile_type)
            ),
            source=source_label,
            source_locator=node.source_locator,
        )
        definitions.append(
            ProfileDefinition(
                key=node.key,
                profile_type=node.profile_type,
                reference=node.reference,
                modulating=node.modulating,
                units=node.units,
                data=TraceableField(
                    value=_json_value(node.data),
                    description=(
                        "Exact native VE {} profile payload.".format(
                            node.profile_type
                        )
                    ),
                    units="VE native profile data",
                    source=source_label,
                    source_locator=node.source_locator,
                    validation_range=ValidationRange(
                        expected_type="array",
                        allow_none=False,
                    ),
                    required=True,
                ),
                evidence=evidence,
            )
        )
    output_keys = tuple(graph.outputs)
    known_keys = {definition.key for definition in definitions}
    if any(node_key not in known_keys for _, node_key in output_keys):
        raise ConfigurationError(
            "SIA 2024 native VE profile graph has unresolved output nodes"
        )
    return Test2AProfileDefinitionBundle(
        definitions=tuple(definitions),
        output_profile_keys=output_keys,
        source_sha256=source_digest,
        graph_sha256=_canonical_sha256(graph_payload),
    )
