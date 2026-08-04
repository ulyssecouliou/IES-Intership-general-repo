"""Strict normalized external bindings for SIA 4010 Test 3.

This module validates source-traced representations only.  It deliberately
does not interpret SIA 387/4 algorithms, select a VE control object or authorize
model mutation.  Those are separate, runtime-qualified boundaries.
"""

import math
from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping, Optional, Sequence, Set, Tuple

from ..exceptions import ConfigurationError
from .external_input_manifest import (
    ExternalInputEvidence,
    ExternalInputReadiness,
    required_external_input_ids,
)
from .normalized_external_inputs import (
    CommonCellExternalBindings,
    load_common_cell_external_bindings,
    load_normalized_binding_payload,
)


CONTROL_INPUT_ID = "sia3874_2017_tables9_10_controls"
SHADING_DEVICE_INPUT_ID = "sia_example_building_fabric_awning_detail"
AUTHORITY_INPUT_ID = "sia_authority_test3_3k_3l_device_clarification"
SHADING_CONTROL_IDS = tuple(
    "shade_type_{}".format(index) for index in range(1, 4)
)
LIGHTING_CONTROL_IDS = tuple(
    "lighting_type_{}".format(index) for index in range(1, 7)
)
FORBIDDEN_PLACEHOLDERS = {
    "assumed",
    "missing",
    "n/a",
    "na",
    "tbd",
    "todo",
    "unknown",
}
SUPPORTED_AST_OPERATORS = {
    "and",
    "clamp",
    "comparison",
    "elapsed_time",
    "linear_interpolation",
    "literal",
    "not",
    "or",
    "parameter_ref",
    "piecewise",
    "previous_state",
    "signal_ref",
    "state_ref",
}


def _mapping(value: Any, context: str) -> Mapping[str, Any]:
    """Require and return a JSON mapping for one normalized field."""

    if not isinstance(value, Mapping):
        raise ConfigurationError("{} must be a JSON object".format(context))
    return value


def _array(value: Any, context: str, *, allow_empty: bool = False) -> Sequence[Any]:
    """Require and return a JSON array for one normalized field."""

    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ConfigurationError("{} must be a JSON array".format(context))
    if not allow_empty and not value:
        raise ConfigurationError("{} must not be empty".format(context))
    return value


def _text(value: Any, context: str) -> str:
    """Require non-placeholder text for one normalized source field."""

    result = str(value or "").strip()
    if not result:
        raise ConfigurationError("{} must be non-empty text".format(context))
    lowered = result.casefold()
    if (
        lowered in FORBIDDEN_PLACEHOLDERS
        or (result.startswith("<") and result.endswith(">"))
    ):
        raise ConfigurationError(
            "{} contains a forbidden placeholder".format(context)
        )
    return result


def _exact_keys(
    payload: Mapping[str, Any],
    required: Set[str],
    context: str,
    *,
    optional: Set[str] = frozenset(),
) -> None:
    """Require the exact allowed key set for one normalized object."""

    missing = sorted(required - set(payload))
    unknown = sorted(set(payload) - required - optional)
    if missing or unknown:
        raise ConfigurationError(
            "{} keys mismatch; missing={}, unknown={}".format(
                context, missing, unknown
            )
        )


def _identifier(value: Any, context: str) -> str:
    """Validate and return one stable normalized identifier."""

    result = _text(value, context)
    if not all(character.isalnum() or character in "_.-" for character in result):
        raise ConfigurationError(
            "{} contains unsupported identifier characters".format(context)
        )
    return result


def _json_value(value: Any, context: str) -> Any:
    """Reject null, placeholders, non-finite numbers and non-JSON values."""

    if value is None:
        raise ConfigurationError("{} must not be null".format(context))
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if not math.isfinite(float(value)):
            raise ConfigurationError("{} must be finite".format(context))
        return value
    if isinstance(value, str):
        return _text(value, context)
    if isinstance(value, Mapping):
        if not value:
            raise ConfigurationError("{} must not be empty".format(context))
        return {
            _identifier(key, "{} key".format(context)): _json_value(
                item, "{}.{}".format(context, key)
            )
            for key, item in value.items()
        }
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        if not value:
            raise ConfigurationError("{} must not be empty".format(context))
        return tuple(
            _json_value(item, "{}[{}]".format(context, index))
            for index, item in enumerate(value)
        )
    raise ConfigurationError(
        "{} contains unsupported JSON value {}".format(
            context, type(value).__name__
        )
    )


@dataclass(frozen=True)
class NormalizedControlSignal:
    """One explicitly sourced control input or output signal."""

    signal_id: str
    physical_quantity: str
    unit: str
    value_type: str
    source_locator: str


@dataclass(frozen=True)
class NormalizedControlParameter:
    """One normative or scenario-referenced control parameter."""

    parameter_id: str
    value_type: str
    unit: str
    source_kind: str
    value: Any
    scenario_parameter_ref: str
    source_locator: str


@dataclass(frozen=True)
class NormalizedControlFunction:
    """One closed, source-transcribed Table 9 or Table 10 function."""

    control_id: str
    normative_type: int
    source_locator: str
    input_refs: Tuple[str, ...]
    parameter_refs: Tuple[str, ...]
    states: Tuple[Mapping[str, Any], ...]
    rules: Tuple[Mapping[str, Any], ...]
    default_actions: Tuple[Mapping[str, Any], ...]
    output_refs: Tuple[str, ...]
    required_runtime_capabilities: Tuple[str, ...]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the normalized control function as audit data."""

        return asdict(self)


@dataclass(frozen=True)
class NormalizedSia3874Controls:
    """Exact Table 9 functions 1-3 and Table 10 functions 1-6."""

    standard_edition: str
    tables: Tuple[str, ...]
    conventions: Mapping[str, Any]
    signals: Tuple[NormalizedControlSignal, ...]
    parameters: Tuple[NormalizedControlParameter, ...]
    shading_controls: Tuple[NormalizedControlFunction, ...]
    lighting_controls: Tuple[NormalizedControlFunction, ...]
    source_locator: str

    def control(self, control_id: str) -> NormalizedControlFunction:
        """Return one normalized shading or lighting control by identifier."""

        for control in self.shading_controls + self.lighting_controls:
            if control.control_id == control_id:
                return control
        raise KeyError(control_id)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the complete normalized control contract for auditing."""

        parameters = []
        for parameter in self.parameters:
            row = {
                "id": parameter.parameter_id,
                "value_type": parameter.value_type,
                "unit": parameter.unit,
                "source_kind": parameter.source_kind,
                "source_locator": parameter.source_locator,
            }
            if parameter.source_kind == "SCENARIO_PARAMETER":
                row["scenario_parameter_ref"] = (
                    parameter.scenario_parameter_ref
                )
            else:
                row["value"] = parameter.value
            parameters.append(row)
        return {
            "standard_edition": self.standard_edition,
            "tables": list(self.tables),
            "conventions": dict(self.conventions),
            "signals": [
                {
                    "id": item.signal_id,
                    "physical_quantity": item.physical_quantity,
                    "unit": item.unit,
                    "value_type": item.value_type,
                    "source_locator": item.source_locator,
                }
                for item in self.signals
            ],
            "parameters": parameters,
            "shading_controls": [
                item.to_dict() for item in self.shading_controls
            ],
            "lighting_controls": [
                item.to_dict() for item in self.lighting_controls
            ],
            "source_locator": self.source_locator,
        }


@dataclass(frozen=True)
class NormalizedShadingDevice:
    """One source-defined shading device and its explicit optical states."""

    device_id: str
    device_type: str
    mounting_position: str
    states: Tuple[Mapping[str, Any], ...]
    source_locator: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the normalized shading device as audit data."""

        return asdict(self)


@dataclass(frozen=True)
class NormalizedAuthorityDecision:
    """One written authority decision, kept separate from normative controls."""

    decision_id: str
    issued_by: str
    issued_date: str
    document_reference: str
    question: str
    decision: str
    applicable_cases: Tuple[str, ...]
    resolved_parameters: Tuple[Mapping[str, Any], ...]
    source_locator: str

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the normalized authority decision as audit data."""

        return asdict(self)


@dataclass(frozen=True)
class Test3ExternalBindings:
    """Every normalized delegated input required by one exact Test 3 case."""

    common: CommonCellExternalBindings
    controls: NormalizedSia3874Controls
    shading_device: NormalizedShadingDevice
    authority_decision: Optional[NormalizedAuthorityDecision]
    evidence_sha256: Tuple[Tuple[str, str], ...]

    def to_dict(self) -> Dict[str, Any]:
        """Serialize all exact Test 3 delegated bindings for auditing."""

        return {
            "common": self.common.to_dict(),
            "controls": self.controls.to_dict(),
            "shading_device": self.shading_device.to_dict(),
            "authority_decision": (
                self.authority_decision.to_dict()
                if self.authority_decision is not None
                else None
            ),
            "evidence_sha256": dict(self.evidence_sha256),
        }


def _load_signals(payload: Any) -> Tuple[NormalizedControlSignal, ...]:
    """Load and validate the complete normalized control signal collection."""

    signals = []
    for index, raw in enumerate(_array(payload, "signals")):
        context = "signals[{}]".format(index)
        item = _mapping(raw, context)
        _exact_keys(
            item,
            {
                "id",
                "physical_quantity",
                "unit",
                "value_type",
                "source_locator",
            },
            context,
        )
        value_type = _text(item["value_type"], context + ".value_type")
        if value_type not in {"boolean", "integer", "number", "string"}:
            raise ConfigurationError(
                "{} has unsupported value_type".format(context)
            )
        signals.append(
            NormalizedControlSignal(
                signal_id=_identifier(item["id"], context + ".id"),
                physical_quantity=_text(
                    item["physical_quantity"], context + ".physical_quantity"
                ),
                unit=_text(item["unit"], context + ".unit"),
                value_type=value_type,
                source_locator=_text(
                    item["source_locator"], context + ".source_locator"
                ),
            )
        )
    identifiers = [item.signal_id for item in signals]
    if len(set(identifiers)) != len(identifiers):
        raise ConfigurationError("signals contain duplicate ids")
    return tuple(signals)


def _load_parameters(payload: Any) -> Tuple[NormalizedControlParameter, ...]:
    """Load and validate the complete normalized control parameter collection."""

    parameters = []
    for index, raw in enumerate(_array(payload, "parameters")):
        context = "parameters[{}]".format(index)
        item = _mapping(raw, context)
        _exact_keys(
            item,
            {
                "id",
                "value_type",
                "unit",
                "source_kind",
                "source_locator",
            },
            context,
            optional={"value", "scenario_parameter_ref"},
        )
        source_kind = _text(
            item["source_kind"], context + ".source_kind"
        )
        if source_kind not in {
            "DERIVED_NORMATIVE_VALUE",
            "NORMATIVE_CONSTANT",
            "SCENARIO_PARAMETER",
        }:
            raise ConfigurationError(
                "{} has unsupported source_kind".format(context)
            )
        has_value = "value" in item
        has_reference = "scenario_parameter_ref" in item
        if source_kind == "SCENARIO_PARAMETER":
            if has_value or not has_reference:
                raise ConfigurationError(
                    "{} scenario parameter must have only "
                    "scenario_parameter_ref".format(context)
                )
        elif not has_value or has_reference:
            raise ConfigurationError(
                "{} normative parameter must have only value".format(context)
            )
        value_type = _text(
            item["value_type"], context + ".value_type"
        )
        if value_type not in {"boolean", "integer", "number", "string"}:
            raise ConfigurationError(
                "{} has unsupported value_type".format(context)
            )
        parameters.append(
            NormalizedControlParameter(
                parameter_id=_identifier(item["id"], context + ".id"),
                value_type=value_type,
                unit=_text(item["unit"], context + ".unit"),
                source_kind=source_kind,
                value=(
                    _json_value(item["value"], context + ".value")
                    if has_value
                    else None
                ),
                scenario_parameter_ref=(
                    _identifier(
                        item["scenario_parameter_ref"],
                        context + ".scenario_parameter_ref",
                    )
                    if has_reference
                    else ""
                ),
                source_locator=_text(
                    item["source_locator"], context + ".source_locator"
                ),
            )
        )
    identifiers = [item.parameter_id for item in parameters]
    if len(set(identifiers)) != len(identifiers):
        raise ConfigurationError("parameters contain duplicate ids")
    return tuple(parameters)


def _validate_ast(
    node: Any,
    context: str,
    *,
    signal_ids: Set[str],
    parameter_ids: Set[str],
    state_ids: Set[str],
) -> Mapping[str, Any]:
    """Validate one source-transcribed control expression syntax tree."""

    payload = _mapping(node, context)
    operator = _text(payload.get("op"), context + ".op")
    if operator not in SUPPORTED_AST_OPERATORS:
        raise ConfigurationError(
            "{} uses unsupported operator {!r}".format(context, operator)
        )
    required_by_operator = {
        "literal": {"op", "value"},
        "signal_ref": {"op", "signal_ref"},
        "parameter_ref": {"op", "parameter_ref"},
        "state_ref": {"op", "state_ref"},
        "previous_state": {"op", "state_ref"},
        "elapsed_time": {"op", "state_ref", "unit"},
        "comparison": {"op", "operator", "left", "right"},
        "and": {"op", "args"},
        "or": {"op", "args"},
        "not": {"op", "arg"},
        "clamp": {"op", "value", "minimum", "maximum"},
        "linear_interpolation": {"op", "input", "points"},
        "piecewise": {"op", "branches", "default"},
    }
    _exact_keys(
        payload,
        required_by_operator[operator],
        context,
    )
    for key, valid in (
        ("signal_ref", signal_ids),
        ("parameter_ref", parameter_ids),
        ("state_ref", state_ids),
    ):
        if key in payload:
            reference = _identifier(payload[key], context + "." + key)
            if reference not in valid:
                raise ConfigurationError(
                    "{} references unknown {}".format(context, reference)
                )
    if operator == "comparison":
        comparison = _text(
            payload["operator"], context + ".operator"
        )
        if comparison not in {"<", "<=", "==", "!=", ">=", ">"}:
            raise ConfigurationError(
                "{} has unsupported comparison operator".format(context)
            )
    for key in (
        "arg",
        "default",
        "input",
        "left",
        "maximum",
        "minimum",
        "right",
        "value",
    ):
        value = payload.get(key)
        if isinstance(value, Mapping):
            _validate_ast(
                value,
                context + "." + key,
                signal_ids=signal_ids,
                parameter_ids=parameter_ids,
                state_ids=state_ids,
            )
    if operator in {"and", "or"}:
        for index, child in enumerate(
            _array(payload["args"], context + ".args")
        ):
            _validate_ast(
                child,
                "{}.args[{}]".format(context, index),
                signal_ids=signal_ids,
                parameter_ids=parameter_ids,
                state_ids=state_ids,
            )
    if operator == "linear_interpolation":
        for index, point_raw in enumerate(
            _array(payload["points"], context + ".points")
        ):
            point_context = "{}.points[{}]".format(context, index)
            point = _mapping(point_raw, point_context)
            _exact_keys(point, {"x", "y"}, point_context)
            for coordinate in ("x", "y"):
                value = point[coordinate]
                if isinstance(value, Mapping):
                    _validate_ast(
                        value,
                        point_context + "." + coordinate,
                        signal_ids=signal_ids,
                        parameter_ids=parameter_ids,
                        state_ids=state_ids,
                    )
                else:
                    _json_value(value, point_context + "." + coordinate)
    if operator == "piecewise":
        for index, branch_raw in enumerate(
            _array(payload["branches"], context + ".branches")
        ):
            branch_context = "{}.branches[{}]".format(context, index)
            branch = _mapping(branch_raw, branch_context)
            _exact_keys(branch, {"when", "value"}, branch_context)
            for key in ("when", "value"):
                _validate_ast(
                    branch[key],
                    branch_context + "." + key,
                    signal_ids=signal_ids,
                    parameter_ids=parameter_ids,
                    state_ids=state_ids,
                )
    return dict(_json_value(payload, context))


def _load_control(
    raw: Any,
    context: str,
    *,
    signal_ids: Set[str],
    parameter_ids: Set[str],
) -> NormalizedControlFunction:
    """Load one normalized control function with strict references."""

    item = _mapping(raw, context)
    _exact_keys(
        item,
        {
            "id",
            "normative_type",
            "source_locator",
            "inputs",
            "parameters",
            "states",
            "rules",
            "default_actions",
            "outputs",
            "required_runtime_capabilities",
        },
        context,
    )
    normative_type = item["normative_type"]
    if isinstance(normative_type, bool) or not isinstance(normative_type, int):
        raise ConfigurationError(
            "{}.normative_type must be an integer".format(context)
        )
    inputs = tuple(
        _identifier(value, context + ".inputs")
        for value in _array(item["inputs"], context + ".inputs")
    )
    outputs = tuple(
        _identifier(value, context + ".outputs")
        for value in _array(item["outputs"], context + ".outputs")
    )
    parameters = tuple(
        _identifier(value, context + ".parameters")
        for value in _array(
            item["parameters"], context + ".parameters", allow_empty=True
        )
    )
    unknown_signals = sorted((set(inputs) | set(outputs)) - signal_ids)
    unknown_parameters = sorted(set(parameters) - parameter_ids)
    if unknown_signals or unknown_parameters:
        raise ConfigurationError(
            "{} has unknown references; signals={}, parameters={}".format(
                context, unknown_signals, unknown_parameters
            )
        )
    states = []
    for index, state_raw in enumerate(
        _array(item["states"], context + ".states", allow_empty=True)
    ):
        state_context = "{}.states[{}]".format(context, index)
        state = _mapping(state_raw, state_context)
        _exact_keys(
            state,
            {"id", "initial_value", "unit", "source_locator"},
            state_context,
        )
        states.append(
            {
                "id": _identifier(state["id"], state_context + ".id"),
                "initial_value": _json_value(
                    state["initial_value"],
                    state_context + ".initial_value",
                ),
                "unit": _text(state["unit"], state_context + ".unit"),
                "source_locator": _text(
                    state["source_locator"],
                    state_context + ".source_locator",
                ),
            }
        )
    state_ids = {item["id"] for item in states}
    if len(state_ids) != len(states):
        raise ConfigurationError("{} has duplicate state ids".format(context))
    rules = []
    priorities = []
    for index, rule_raw in enumerate(_array(item["rules"], context + ".rules")):
        rule_context = "{}.rules[{}]".format(context, index)
        rule = _mapping(rule_raw, rule_context)
        _exact_keys(
            rule,
            {"priority", "when", "actions", "source_locator"},
            rule_context,
        )
        priority = rule["priority"]
        if isinstance(priority, bool) or not isinstance(priority, int):
            raise ConfigurationError(
                "{}.priority must be an integer".format(rule_context)
            )
        priorities.append(priority)
        actions = []
        for action_index, action_raw in enumerate(
            _array(rule["actions"], rule_context + ".actions")
        ):
            action_context = "{}.actions[{}]".format(
                rule_context, action_index
            )
            action = _mapping(action_raw, action_context)
            _exact_keys(
                action, {"target_ref", "value"}, action_context
            )
            target = _identifier(
                action["target_ref"], action_context + ".target_ref"
            )
            if target not in set(outputs) | state_ids:
                raise ConfigurationError(
                    "{} references unknown target {}".format(
                        action_context, target
                    )
                )
            actions.append(
                {
                    "target_ref": target,
                    "value": _validate_ast(
                        action["value"],
                        action_context + ".value",
                        signal_ids=signal_ids,
                        parameter_ids=parameter_ids,
                        state_ids=state_ids,
                    ),
                }
            )
        rules.append(
            {
                "priority": priority,
                "when": _validate_ast(
                    rule["when"],
                    rule_context + ".when",
                    signal_ids=signal_ids,
                    parameter_ids=parameter_ids,
                    state_ids=state_ids,
                ),
                "actions": tuple(actions),
                "source_locator": _text(
                    rule["source_locator"],
                    rule_context + ".source_locator",
                ),
            }
        )
    if len(set(priorities)) != len(priorities):
        raise ConfigurationError(
            "{} has ambiguous duplicate rule priorities".format(context)
        )
    default_actions = []
    for index, action_raw in enumerate(
        _array(item["default_actions"], context + ".default_actions")
    ):
        action_context = "{}.default_actions[{}]".format(context, index)
        action = _mapping(action_raw, action_context)
        _exact_keys(action, {"target_ref", "value"}, action_context)
        target = _identifier(
            action["target_ref"], action_context + ".target_ref"
        )
        if target not in set(outputs) | state_ids:
            raise ConfigurationError(
                "{} references unknown target {}".format(
                    action_context, target
                )
            )
        default_actions.append(
            {
                "target_ref": target,
                "value": _validate_ast(
                    action["value"],
                    action_context + ".value",
                    signal_ids=signal_ids,
                    parameter_ids=parameter_ids,
                    state_ids=state_ids,
                ),
            }
        )
    capabilities = tuple(
        _identifier(value, context + ".required_runtime_capabilities")
        for value in _array(
            item["required_runtime_capabilities"],
            context + ".required_runtime_capabilities",
        )
    )
    return NormalizedControlFunction(
        control_id=_identifier(item["id"], context + ".id"),
        normative_type=normative_type,
        source_locator=_text(
            item["source_locator"], context + ".source_locator"
        ),
        input_refs=inputs,
        parameter_refs=parameters,
        states=tuple(states),
        rules=tuple(rules),
        default_actions=tuple(default_actions),
        output_refs=outputs,
        required_runtime_capabilities=capabilities,
    )


def load_sia3874_controls(
    evidence: ExternalInputEvidence,
) -> NormalizedSia3874Controls:
    """Load a complete, checksum-bound Tables 9/10 transcription."""

    if evidence.input_id != CONTROL_INPUT_ID:
        raise ConfigurationError("Wrong evidence supplied for SIA 387/4 controls")
    payload = load_normalized_binding_payload(evidence)
    _exact_keys(
        payload,
        {
            "schema_id",
            "schema_version",
            "primary_source_sha256",
            "source_locator",
            "standard_edition",
            "tables",
            "conventions",
            "signals",
            "parameters",
            "controls",
        },
        "SIA 387/4 controls",
    )
    tables = tuple(
        _text(value, "SIA 387/4 tables")
        for value in _array(payload["tables"], "SIA 387/4 tables")
    )
    if tables != ("9", "10"):
        raise ConfigurationError(
            "SIA 387/4 controls must bind exactly Tables 9 and 10"
        )
    conventions = _mapping(
        payload["conventions"], "SIA 387/4 conventions"
    )
    required_conventions = {
        "angle_convention",
        "boundary_comparisons",
        "rule_evaluation_order",
        "signal_sampling",
        "time_basis",
    }
    _exact_keys(
        conventions,
        required_conventions,
        "SIA 387/4 conventions",
    )
    normalized_conventions = {
        key: _json_value(value, "conventions." + key)
        for key, value in conventions.items()
    }
    signals = _load_signals(payload["signals"])
    parameters = _load_parameters(payload["parameters"])
    signal_ids = {item.signal_id for item in signals}
    parameter_ids = {item.parameter_id for item in parameters}
    controls = _mapping(payload["controls"], "controls")
    _exact_keys(controls, {"shading", "lighting"}, "controls")
    shading = tuple(
        _load_control(
            raw,
            "controls.shading[{}]".format(index),
            signal_ids=signal_ids,
            parameter_ids=parameter_ids,
        )
        for index, raw in enumerate(
            _array(controls["shading"], "controls.shading")
        )
    )
    lighting = tuple(
        _load_control(
            raw,
            "controls.lighting[{}]".format(index),
            signal_ids=signal_ids,
            parameter_ids=parameter_ids,
        )
        for index, raw in enumerate(
            _array(controls["lighting"], "controls.lighting")
        )
    )
    shading_ids = tuple(item.control_id for item in shading)
    lighting_ids = tuple(item.control_id for item in lighting)
    if set(shading_ids) != set(SHADING_CONTROL_IDS) or len(shading_ids) != 3:
        raise ConfigurationError(
            "SIA 387/4 shading function set must be exactly {}".format(
                SHADING_CONTROL_IDS
            )
        )
    if set(lighting_ids) != set(LIGHTING_CONTROL_IDS) or len(lighting_ids) != 6:
        raise ConfigurationError(
            "SIA 387/4 lighting function set must be exactly {}".format(
                LIGHTING_CONTROL_IDS
            )
        )
    for control in shading:
        if control.normative_type != int(control.control_id.rsplit("_", 1)[1]):
            raise ConfigurationError(
                "{} normative_type does not match its id".format(
                    control.control_id
                )
            )
    for control in lighting:
        if control.normative_type != int(control.control_id.rsplit("_", 1)[1]):
            raise ConfigurationError(
                "{} normative_type does not match its id".format(
                    control.control_id
                )
            )
    return NormalizedSia3874Controls(
        standard_edition=_text(
            payload["standard_edition"], "standard_edition"
        ),
        tables=tables,
        conventions=normalized_conventions,
        signals=signals,
        parameters=parameters,
        shading_controls=shading,
        lighting_controls=lighting,
        source_locator=_text(payload["source_locator"], "source_locator"),
    )


def load_shading_device(
    evidence: ExternalInputEvidence,
) -> NormalizedShadingDevice:
    """Load the separately sourced Test 3 fabric-awning definition."""

    if evidence.input_id != SHADING_DEVICE_INPUT_ID:
        raise ConfigurationError("Wrong evidence supplied for shading device")
    payload = load_normalized_binding_payload(evidence)
    _exact_keys(
        payload,
        {
            "schema_id",
            "schema_version",
            "primary_source_sha256",
            "source_locator",
            "device_id",
            "device_type",
            "mounting_position",
            "states",
        },
        "shading device",
    )
    states = []
    for index, raw in enumerate(_array(payload["states"], "shading device.states")):
        context = "shading device.states[{}]".format(index)
        state = _mapping(raw, context)
        _exact_keys(
            state,
            {"id", "properties", "source_locator"},
            context,
        )
        properties = _mapping(state["properties"], context + ".properties")
        states.append(
            {
                "id": _identifier(state["id"], context + ".id"),
                "properties": _json_value(
                    properties, context + ".properties"
                ),
                "source_locator": _text(
                    state["source_locator"], context + ".source_locator"
                ),
            }
        )
    state_ids = {item["id"] for item in states}
    if len(states) < 2 or len(state_ids) != len(states):
        raise ConfigurationError(
            "Shading device requires at least two uniquely identified states"
        )
    return NormalizedShadingDevice(
        device_id=_identifier(payload["device_id"], "device_id"),
        device_type=_text(payload["device_type"], "device_type"),
        mounting_position=_text(
            payload["mounting_position"], "mounting_position"
        ),
        states=tuple(states),
        source_locator=_text(payload["source_locator"], "source_locator"),
    )


def load_authority_decision(
    evidence: ExternalInputEvidence,
) -> NormalizedAuthorityDecision:
    """Load one written 3K/3L decision without interpreting its prose."""

    if evidence.input_id != AUTHORITY_INPUT_ID:
        raise ConfigurationError("Wrong evidence supplied for authority decision")
    payload = load_normalized_binding_payload(evidence)
    _exact_keys(
        payload,
        {
            "schema_id",
            "schema_version",
            "primary_source_sha256",
            "source_locator",
            "decision_id",
            "issued_by",
            "issued_date",
            "document_reference",
            "question",
            "decision",
            "applicable_cases",
            "resolved_parameters",
        },
        "authority decision",
    )
    cases = tuple(
        _text(value, "authority decision applicable_cases")
        for value in _array(
            payload["applicable_cases"], "authority decision applicable_cases"
        )
    )
    if not {"test_3K/3K", "test_3L/3L"} <= set(cases):
        raise ConfigurationError(
            "Test 3 authority decision must cover test_3K/3K and test_3L/3L"
        )
    resolved = []
    for index, raw in enumerate(
        _array(payload["resolved_parameters"], "resolved_parameters")
    ):
        context = "resolved_parameters[{}]".format(index)
        item = _mapping(raw, context)
        _exact_keys(
            item, {"id", "value", "unit", "source_locator"}, context
        )
        resolved.append(
            {
                "id": _identifier(item["id"], context + ".id"),
                "value": _json_value(item["value"], context + ".value"),
                "unit": _text(item["unit"], context + ".unit"),
                "source_locator": _text(
                    item["source_locator"], context + ".source_locator"
                ),
            }
        )
    if "test3_3k_3l_shading_device_identity" not in {
        item["id"] for item in resolved
    }:
        raise ConfigurationError(
            "Authority decision does not resolve the 3K/3L shading device identity"
        )
    return NormalizedAuthorityDecision(
        decision_id=_identifier(payload["decision_id"], "decision_id"),
        issued_by=_text(payload["issued_by"], "issued_by"),
        issued_date=_text(payload["issued_date"], "issued_date"),
        document_reference=_text(
            payload["document_reference"], "document_reference"
        ),
        question=_text(payload["question"], "question"),
        decision=_text(payload["decision"], "decision"),
        applicable_cases=cases,
        resolved_parameters=tuple(resolved),
        source_locator=_text(payload["source_locator"], "source_locator"),
    )


def load_test3_external_bindings(
    readiness: ExternalInputReadiness,
) -> Test3ExternalBindings:
    """Load the exact delegated input set for one Test 3 variant."""

    if (
        not readiness.variant.startswith("test_3")
        or readiness.case_id != readiness.variant[5:]
    ):
        raise ConfigurationError(
            "Test 3 bindings require an exact test_3A-test_3L readiness pair"
        )
    if not readiness.ready_for_binding:
        raise ConfigurationError(
            "Test 3 external inputs are not READY_FOR_BINDING: {}".format(
                readiness.blocked_input_ids
            )
        )
    expected = required_external_input_ids(
        readiness.variant, readiness.case_id
    )
    indexed = {item.input_id: item for item in readiness.evidence}
    if set(indexed) != set(expected) or len(indexed) != len(expected):
        raise ConfigurationError(
            "Test 3 evidence set mismatch; expected {}, received {}".format(
                expected, tuple(indexed)
            )
        )
    authority = (
        load_authority_decision(indexed[AUTHORITY_INPUT_ID])
        if AUTHORITY_INPUT_ID in indexed
        else None
    )
    return Test3ExternalBindings(
        common=load_common_cell_external_bindings(readiness),
        controls=load_sia3874_controls(indexed[CONTROL_INPUT_ID]),
        shading_device=load_shading_device(
            indexed[SHADING_DEVICE_INPUT_ID]
        ),
        authority_decision=authority,
        evidence_sha256=tuple(
            (input_id, indexed[input_id].binding_artifact_sha256)
            for input_id in expected
        ),
    )
