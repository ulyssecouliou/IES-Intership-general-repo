"""Fail-closed semantic tests for normalized SIA 4010 Test 3 bindings."""

import json
import unittest
from pathlib import Path
from unittest import mock

from swiss_sia.reference_model.exceptions import ConfigurationError
from swiss_sia.reference_model.sia4010.external_input_manifest import (
    ExternalInputReadiness,
    required_external_input_ids,
)
from swiss_sia.reference_model.sia4010.test3_external_bindings import (
    AUTHORITY_INPUT_ID,
    CONTROL_INPUT_ID,
    SHADING_DEVICE_INPUT_ID,
    load_authority_decision,
    load_shading_device,
    load_sia3874_controls,
    load_test3_external_bindings,
)

ROOT = Path(__file__).resolve().parents[1]


def _ast_literal(value):
    return {"op": "literal", "value": value}


def _control(identifier, normative_type, output):
    return {
        "id": identifier,
        "normative_type": normative_type,
        "source_locator": "controlled table row",
        "inputs": ["input_signal"],
        "parameters": ["threshold"],
        "states": [],
        "rules": [
            {
                "priority": 1,
                "when": {
                    "op": "comparison",
                    "left": {"op": "signal_ref", "signal_ref": "input_signal"},
                    "right": {
                        "op": "parameter_ref",
                        "parameter_ref": "threshold",
                    },
                    "operator": ">=",
                },
                "actions": [{"target_ref": output, "value": _ast_literal(1.0)}],
                "source_locator": "controlled table rule",
            }
        ],
        "default_actions": [{"target_ref": output, "value": _ast_literal(0.0)}],
        "outputs": [output],
        "required_runtime_capabilities": ["hourly_control"],
    }


def _controls_payload():
    return {
        "schema_id": "sia4010.sia3874_shading_lighting_controls.v1",
        "schema_version": "1.0",
        "primary_source_sha256": "a" * 64,
        "source_locator": "controlled SIA 387/4 source",
        "standard_edition": "controlled edition",
        "tables": ["9", "10"],
        "conventions": {
            "time_basis": {"description": "controlled hourly basis"},
            "boundary_comparisons": {"description": "controlled boundaries"},
            "angle_convention": {"description": "controlled angle basis"},
            "signal_sampling": {"description": "controlled sampling"},
            "rule_evaluation_order": {"description": "controlled order"},
        },
        "signals": [
            {
                "id": "input_signal",
                "physical_quantity": "controlled input",
                "unit": "W/m2",
                "value_type": "number",
                "source_locator": "controlled signal row",
            },
            {
                "id": "shade_output",
                "physical_quantity": "controlled shade state",
                "unit": "1",
                "value_type": "number",
                "source_locator": "controlled output row",
            },
            {
                "id": "lighting_output",
                "physical_quantity": "controlled lighting fraction",
                "unit": "1",
                "value_type": "number",
                "source_locator": "controlled output row",
            },
        ],
        "parameters": [
            {
                "id": "threshold",
                "value_type": "number",
                "unit": "W/m2",
                "source_kind": "SCENARIO_PARAMETER",
                "scenario_parameter_ref": ("external_shading_activation_w_m2"),
                "source_locator": "controlled parameter row",
            }
        ],
        "controls": {
            "shading": [
                _control("shade_type_{}".format(index), index, "shade_output")
                for index in range(1, 4)
            ],
            "lighting": [
                _control(
                    "lighting_type_{}".format(index),
                    index,
                    "lighting_output",
                )
                for index in range(1, 7)
            ],
        },
    }


class Test3ExternalBindingTests(unittest.TestCase):
    def test_complete_tables9_10_control_set_is_loaded(self):
        evidence = mock.Mock(input_id=CONTROL_INPUT_ID)
        with mock.patch(
            "swiss_sia.reference_model.sia4010.test3_external_bindings."
            "load_normalized_binding_payload",
            return_value=_controls_payload(),
        ):
            controls = load_sia3874_controls(evidence)
        self.assertEqual(len(controls.shading_controls), 3)
        self.assertEqual(len(controls.lighting_controls), 6)
        self.assertEqual(controls.control("lighting_type_6").normative_type, 6)

    def test_missing_table10_function_is_rejected(self):
        payload = _controls_payload()
        payload["controls"]["lighting"].pop()
        evidence = mock.Mock(input_id=CONTROL_INPUT_ID)
        with (
            mock.patch(
                "swiss_sia.reference_model.sia4010.test3_external_bindings."
                "load_normalized_binding_payload",
                return_value=payload,
            ),
            self.assertRaisesRegex(ConfigurationError, "exactly"),
        ):
            load_sia3874_controls(evidence)

    def test_unknown_ast_reference_is_rejected(self):
        payload = _controls_payload()
        payload["controls"]["shading"][0]["rules"][0]["when"] = {
            "op": "signal_ref",
            "signal_ref": "not_declared",
        }
        evidence = mock.Mock(input_id=CONTROL_INPUT_ID)
        with (
            mock.patch(
                "swiss_sia.reference_model.sia4010.test3_external_bindings."
                "load_normalized_binding_payload",
                return_value=payload,
            ),
            self.assertRaisesRegex(ConfigurationError, "unknown not_declared"),
        ):
            load_sia3874_controls(evidence)

    def test_unknown_ast_field_is_rejected(self):
        payload = _controls_payload()
        payload["controls"]["shading"][0]["rules"][0]["when"]["candidate_guess"] = 1
        evidence = mock.Mock(input_id=CONTROL_INPUT_ID)
        with (
            mock.patch(
                "swiss_sia.reference_model.sia4010.test3_external_bindings."
                "load_normalized_binding_payload",
                return_value=payload,
            ),
            self.assertRaisesRegex(ConfigurationError, "unknown"),
        ):
            load_sia3874_controls(evidence)

    def test_shading_device_requires_two_unique_states(self):
        evidence = mock.Mock(input_id=SHADING_DEVICE_INPUT_ID)
        payload = {
            "schema_id": "sia4010.shading_device_definition.v1",
            "schema_version": "1.0",
            "primary_source_sha256": "b" * 64,
            "source_locator": "controlled device source",
            "device_id": "device",
            "device_type": "controlled type",
            "mounting_position": "controlled mounting",
            "states": [
                {
                    "id": "closed",
                    "properties": {"solar_transmittance": 0.1},
                    "source_locator": "controlled state",
                }
            ],
        }
        with (
            mock.patch(
                "swiss_sia.reference_model.sia4010.test3_external_bindings."
                "load_normalized_binding_payload",
                return_value=payload,
            ),
            self.assertRaisesRegex(ConfigurationError, "at least two"),
        ):
            load_shading_device(evidence)

    def test_authority_decision_must_resolve_device_identity(self):
        evidence = mock.Mock(input_id=AUTHORITY_INPUT_ID)
        payload = {
            "schema_id": "sia4010.authority_decision.v1",
            "schema_version": "1.0",
            "primary_source_sha256": "c" * 64,
            "source_locator": "controlled decision source",
            "decision_id": "decision",
            "issued_by": "controlled authority",
            "issued_date": "2026-01-01",
            "document_reference": "controlled reference",
            "question": "controlled question",
            "decision": "controlled decision",
            "applicable_cases": ["test_3K/3K", "test_3L/3L"],
            "resolved_parameters": [
                {
                    "id": "unrelated",
                    "value": "controlled",
                    "unit": "text",
                    "source_locator": "controlled row",
                }
            ],
        }
        with (
            mock.patch(
                "swiss_sia.reference_model.sia4010.test3_external_bindings."
                "load_normalized_binding_payload",
                return_value=payload,
            ),
            self.assertRaisesRegex(ConfigurationError, "does not resolve"),
        ):
            load_authority_decision(evidence)

    def test_exact_case_evidence_set_is_enforced(self):
        expected = required_external_input_ids("test_3A", "3A")
        evidence = tuple(
            mock.Mock(
                input_id=input_id,
                binding_artifact_sha256=str(index) * 64,
            )
            for index, input_id in enumerate(expected, start=1)
        )
        readiness = ExternalInputReadiness(
            variant="test_3A",
            case_id="3A",
            manifest_path=None,
            status="READY_FOR_BINDING",
            required_input_ids=expected,
            ready_input_ids=expected,
            blocked_input_ids=(),
            evidence=evidence,
        )
        with (
            mock.patch(
                "swiss_sia.reference_model.sia4010.test3_external_bindings."
                "load_common_cell_external_bindings",
                return_value=mock.Mock(),
            ),
            mock.patch(
                "swiss_sia.reference_model.sia4010.test3_external_bindings."
                "load_sia3874_controls",
                return_value=mock.Mock(),
            ),
            mock.patch(
                "swiss_sia.reference_model.sia4010.test3_external_bindings."
                "load_shading_device",
                return_value=mock.Mock(),
            ),
        ):
            bindings = load_test3_external_bindings(readiness)
        self.assertIsNone(bindings.authority_decision)
        self.assertEqual(tuple(dict(bindings.evidence_sha256)), expected)

    def test_3k_requires_and_loads_authority_decision(self):
        expected = required_external_input_ids("test_3K", "3K")
        evidence = tuple(
            mock.Mock(
                input_id=input_id,
                binding_artifact_sha256=str(index) * 64,
            )
            for index, input_id in enumerate(expected, start=1)
        )
        readiness = ExternalInputReadiness(
            variant="test_3K",
            case_id="3K",
            manifest_path=None,
            status="READY_FOR_BINDING",
            required_input_ids=expected,
            ready_input_ids=expected,
            blocked_input_ids=(),
            evidence=evidence,
        )
        decision = mock.Mock()
        with (
            mock.patch(
                "swiss_sia.reference_model.sia4010.test3_external_bindings."
                "load_common_cell_external_bindings",
                return_value=mock.Mock(),
            ),
            mock.patch(
                "swiss_sia.reference_model.sia4010.test3_external_bindings."
                "load_sia3874_controls",
                return_value=mock.Mock(),
            ),
            mock.patch(
                "swiss_sia.reference_model.sia4010.test3_external_bindings."
                "load_shading_device",
                return_value=mock.Mock(),
            ),
            mock.patch(
                "swiss_sia.reference_model.sia4010.test3_external_bindings."
                "load_authority_decision",
                return_value=decision,
            ) as loader,
        ):
            bindings = load_test3_external_bindings(readiness)
        self.assertIs(bindings.authority_decision, decision)
        loader.assert_called_once()

    def test_published_test3_schema_ids_match_runtime_contracts(self):
        expected = {
            "sia4010_sia3874_controls_binding.schema.json": (
                "sia4010.sia3874_shading_lighting_controls.v1"
            ),
            "sia4010_shading_device_binding.schema.json": (
                "sia4010.shading_device_definition.v1"
            ),
            "sia4010_authority_decision_binding.schema.json": (
                "sia4010.authority_decision.v1"
            ),
        }
        for filename, schema_id in expected.items():
            with self.subTest(filename=filename):
                payload = json.loads(
                    (ROOT / "schemas" / filename).read_text(encoding="utf-8")
                )
                self.assertEqual(payload["$id"], schema_id)


if __name__ == "__main__":
    unittest.main()
