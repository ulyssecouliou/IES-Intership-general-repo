"""Fail-closed tests for client thermal-template remediation plans."""

from __future__ import annotations

import inspect
import unittest
from pathlib import Path
from unittest.mock import patch

from swiss_sia.client_template_remediation import (
    APPROVAL_STATUS,
    AUTOMATIC_EVIDENCE_MODE,
    ClientTemplateRemediationError,
    TECHNICAL_APPLICATION_STATUS,
    TemplateEvidence,
    apply_preview_plan,
    automatic_template_evidence,
    build_preview_plan,
    latest_remediation_evidence,
    validate_plan_hash,
)


class _Record:
    def __init__(self, **data):
        self.data = dict(data)

    def get(self):
        return dict(self.data)


class _Template:
    name = "SIA REVIEWED OFFICE"

    def __init__(self, profile="DAY_1", name=None, gains=None):
        self.profile = profile
        if name is not None:
            self.name = name
        self.gains = list(gains) if gains is not None else None

    def get_casual_gains(self):
        if self.gains is not None:
            return list(self.gains)
        return [
            _Record(
                name="Reviewed lighting",
                type_str="Lighting",
                max_power_consumption=8.0,
                variation_profile=self.profile,
                allow_profile_saturate=True,
                variation_profile_from_template=False,
            )
        ]

    def add_gain(self, gain):
        if self.gains is None:
            self.gains = self.get_casual_gains()
        self.gains.append(gain)

    def remove_gain(self, gain):
        self.gains.remove(gain)

    @staticmethod
    def apply_changes():
        return None

    def get_air_exchanges(self):
        return [
            _Record(
                name="Reviewed outside air",
                max_flow=1.2,
                variation_profile=self.profile,
            )
        ]

    def get_room_conditions(self):
        return {"heating_setpoint": 20.0}

    def get_apache_systems(self):
        return {"conditioned": True}


class _Profile:
    id = "DAY_1"


class _RoomData:
    def __init__(self, gains=None):
        self.general = {
            "thermal_template": 1,
            "thermal_template_name": "default",
        }
        self.gains = list(
            gains
            if gains is not None
            else [
                _Record(
                    name="Existing lighting",
                    type_str="Lighting",
                    max_power_consumptions={0: 5.0},
                    units_val=0,
                    variation_profile="DAY_1",
                )
            ]
        )

    def get_general(self):
        return dict(self.general)

    def get_internal_gains(self):
        return list(self.gains)

    def get_air_exchanges(self):
        return []

    def get_room_conditions(self):
        return {"heating_setpoint": 18.0}

    def get_apache_systems(self):
        return {"conditioned": False}


class _Body:
    def __init__(self, room_id="ROOM-1", name="Office 1", gains=None):
        self.id = room_id
        self.name = name
        self.data = _RoomData(gains=gains)

    def get_room_data(self):
        return self.data


class _Model:
    def __init__(self):
        self.body = _Body()

    def get_bodies(self, selected_only):
        if selected_only:
            raise AssertionError("Inventory must inspect the complete model")
        return [self.body]


class _Project:
    def __init__(self, template=None):
        self.template = template or _Template()

    def profiles(self):
        # The dictionary key is the persistent VE identifier. Some runtime
        # wrappers do not expose the same identifier on the Python object.
        return ({"DAY_1": _Profile()}, {})

    def thermal_templates(self, assigned, allow_ncm=False):
        self.last_template_arguments = (assigned, allow_ncm)
        return {5: self.template}


def _evidence(**overrides):
    data = {
        "reviewer": "A. Reviewer",
        "review_date": "2026-08-14",
        "source_document": "Approved client room data schedule rev C",
        "source_reference": "Office zones, page 8",
        "intended_use": "Office occupied zones",
        "approval_status": APPROVAL_STATUS,
    }
    data.update(overrides)
    return TemplateEvidence(**data)


class ClientTemplateRemediationTests(unittest.TestCase):
    def _plan(self, root, project=None, model=None, **overrides):
        arguments = {
            "project_path": str(root),
            "project_name": Path(root).name,
            "project": project or _Project(),
            "model": model or _Model(),
            "template_name": "SIA REVIEWED OFFICE",
            "room_ids": ["ROOM-1"],
            "evidence": _evidence(),
            "copy_confirmed": True,
        }
        arguments.update(overrides)
        return build_preview_plan(**arguments)

    def test_preview_contains_exact_target_and_before_state(self):
        plan = self._plan(Path("C:/Models/CLIENT_COPY"))

        self.assertEqual(plan["status"], "READY_FOR_APPLY")
        self.assertEqual(len(plan["template"]["content"]["casual_gains"]), 1)
        self.assertEqual(len(plan["template"]["content"]["air_exchanges"]), 1)
        self.assertTrue(
            plan["template"]["review_observations"]["lighting_gain_detected"]
        )
        self.assertTrue(
            plan["template"]["review_observations"][
                "non_infiltration_air_exchange_detected"
            ]
        )
        self.assertEqual(plan["rooms"][0]["current_template_name"], "default")
        self.assertIn("state_fingerprint_sha256", plan["rooms"][0])
        self.assertEqual(
            plan["capability_assessment"]["room_gain_structure"]["status"],
            "COMPATIBLE_EXISTING_ROOM_GAIN_STRUCTURE",
        )
        validate_plan_hash(plan)

    def test_missing_room_gain_family_blocks_before_any_gateway_write(self):
        class _PeopleAndLightingTemplate(_Template):
            def get_casual_gains(self):
                return super().get_casual_gains() + [
                    _Record(
                        name="Reviewed people",
                        type_str="People",
                        occupancy_density=4.0,
                        variation_profile=self.profile,
                    )
                ]

        plan = self._plan(
            Path("C:/Models/CLIENT_COPY"),
            project=_Project(_PeopleAndLightingTemplate()),
        )

        self.assertEqual(
            plan["status"], "BLOCKED_UNSUPPORTED_ROOM_GAIN_STRUCTURE"
        )
        assessment = plan["capability_assessment"]["room_gain_structure"]
        self.assertEqual(assessment["room_gain_creation_api"],
                         "NOT_AVAILABLE_IN_DOCUMENTED_VERoomData_API")
        self.assertEqual(
            assessment["rooms"][0]["missing_gain_families"], ["people"]
        )
        self.assertIn("TO VERIFY", assessment["message"])
        with self.assertRaisesRegex(ClientTemplateRemediationError, "not ready"):
            apply_preview_plan(object(), plan)

    def test_missing_gain_families_use_scope_safe_documented_template_bridge(self):
        target = _Template(
            gains=[
                _Record(name="Target people", type_str="People"),
                _Record(name="Target lighting", type_str="Lighting"),
                _Record(name="Target equipment", type_str="Computers"),
            ]
        )
        source = _Template(
            name="SOURCE TEMPLATE",
            gains=[_Record(name="Existing equipment", type_str="Miscellaneous")],
        )
        project = _Project(target)
        project.thermal_templates = lambda assigned, allow_ncm=False: {
            1: source,
            5: target,
        }
        model = _Model()
        model.body = _Body(
            gains=[_Record(name="Existing equipment", type_str="Miscellaneous")]
        )
        plan = self._plan(
            Path("C:/Models/CLIENT_COPY"), project=project, model=model
        )

        assessment = plan["capability_assessment"]["room_gain_structure"]
        self.assertEqual(plan["status"], "READY_FOR_APPLY")
        self.assertEqual(
            assessment["status"],
            "TRANSIENT_SOURCE_TEMPLATE_GAIN_BRIDGE_AVAILABLE",
        )
        bridge = assessment["transient_template_bridges"][0]
        self.assertEqual(bridge["source_template_handle"], "1")
        self.assertEqual(
            [item["family"] for item in bridge["target_gain_records"]],
            ["lighting", "people"],
        )

    def test_gain_bridge_is_blocked_when_source_template_has_unselected_rooms(self):
        target = _Template(
            gains=[
                _Record(name="Target people", type_str="People"),
                _Record(name="Target equipment", type_str="Computers"),
            ]
        )
        source = _Template(
            name="SOURCE TEMPLATE",
            gains=[_Record(name="Existing equipment", type_str="Miscellaneous")],
        )
        project = _Project(target)
        project.thermal_templates = lambda assigned, allow_ncm=False: {
            1: source,
            5: target,
        }
        model = _Model()
        model.body = _Body(
            gains=[_Record(name="Existing equipment", type_str="Miscellaneous")]
        )
        second = _Body(
            room_id="ROOM-2",
            name="Office 2",
            gains=[_Record(name="Existing equipment", type_str="Miscellaneous")],
        )
        model.get_bodies = lambda selected_only: [model.body, second]

        plan = self._plan(
            Path("C:/Models/CLIENT_COPY"), project=project, model=model
        )
        assessment = plan["capability_assessment"]["room_gain_structure"]
        self.assertEqual(
            plan["status"], "BLOCKED_UNSUPPORTED_ROOM_GAIN_STRUCTURE"
        )
        self.assertEqual(
            assessment["rooms"][0][
                "unselected_rooms_sharing_source_template"
            ],
            ["ROOM-2"],
        )

    def test_unknown_gain_type_never_becomes_a_known_family(self):
        class _UnknownTemplate(_Template):
            def get_casual_gains(self):
                return [
                    _Record(
                        name="Unknown load",
                        type_str="Unverified VE gain type",
                        variation_profile=self.profile,
                    )
                ]

        plan = self._plan(
            Path("C:/Models/CLIENT_COPY"), project=_Project(_UnknownTemplate())
        )
        assessment = plan["capability_assessment"]["room_gain_structure"]
        self.assertEqual(
            plan["status"], "BLOCKED_UNSUPPORTED_ROOM_GAIN_STRUCTURE"
        )
        self.assertEqual(
            assessment["unknown_target_gain_type_labels"],
            ["Unverified VE gain type"],
        )

    def test_ordinary_client_project_is_never_mutated(self):
        with self.assertRaisesRegex(
            ClientTemplateRemediationError, "saved project copy"
        ):
            self._plan(Path("C:/Models/LIVE_CLIENT"))

    def test_incomplete_approval_evidence_blocks_preview(self):
        with self.assertRaisesRegex(
            ClientTemplateRemediationError, "reviewer is required"
        ):
            self._plan(
                Path("C:/Models/CLIENT_TEST"), evidence=_evidence(reviewer="")
            )

    def test_automatic_evidence_requires_no_free_text_and_never_grants_claim(self):
        source = Path("C:/Sources/source.json")
        receipt_path = Path("C:/Models/CLIENT_COPY/receipt.json")
        with patch(
            "swiss_sia.client_template_remediation."
            "_latest_template_provisioning_receipt",
            return_value=(
                receipt_path,
                {
                    "template_name": "SIA REVIEWED OFFICE",
                    "source_path": str(source),
                    "source_sha256": "abc123",
                    "automatic_compliance_claim": False,
                },
            ),
        ):
            evidence = automatic_template_evidence(
                "C:/Models/CLIENT_COPY",
                "CLIENT_COPY",
                {
                    "name": "SIA REVIEWED OFFICE",
                    "fingerprint_sha256": "template-fingerprint",
                },
                ["ROOM-1"],
                True,
            )

        self.assertEqual(evidence.evidence_mode, AUTOMATIC_EVIDENCE_MODE)
        self.assertEqual(
            evidence.approval_status, TECHNICAL_APPLICATION_STATUS
        )
        self.assertEqual(
            evidence.source_trace_status,
            "SOURCE_TRACED_PROVISIONING_RECEIPT",
        )
        self.assertEqual(evidence.source_document, str(source))
        self.assertIn("ROOM-1", evidence.intended_use)
        self.assertNotIn("APPROVED", evidence.reviewer)

    def test_automatic_evidence_without_receipt_stays_not_checkable(self):
        with patch(
            "swiss_sia.client_template_remediation."
            "_latest_template_provisioning_receipt",
            return_value=(None, {}),
        ):
            evidence = automatic_template_evidence(
                "C:/Models/CLIENT_COPY",
                "CLIENT_COPY",
                {
                    "name": "UNTRACED TEMPLATE",
                    "fingerprint_sha256": "template-fingerprint",
                },
                ["ROOM-1"],
                True,
            )

        self.assertEqual(evidence.source_trace_status, "NOT_CHECKABLE")
        self.assertIn("TO VERIFY", evidence.source_document)
        self.assertIn("template-fingerprint", evidence.source_reference)

    def test_product_ui_contains_no_manual_evidence_entry_fields(self):
        from swiss_sia import client_template_remediation_ui

        source = inspect.getsource(client_template_remediation_ui)
        for obsolete in (
            "ttk.Entry",
            "reviewer_var",
            "source_var",
            "reference_var",
            "use_var",
            "approval_confirmed",
        ):
            self.assertNotIn(obsolete, source)
        self.assertIn("automatic_template_evidence", source)
        self.assertIn("application_confirmed", source)

    def test_review_only_candidate_can_be_previewed_but_not_applied(self):
        plan = self._plan(
            Path("C:/Models/CLIENT_TEST"),
            evidence=_evidence(approval_status="CANDIDATE_FOR_REVIEW"),
        )
        self.assertEqual(plan["status"], "REVIEW_ONLY")
        with self.assertRaisesRegex(ClientTemplateRemediationError, "not ready"):
            apply_preview_plan(object(), plan)

    def test_template_with_missing_profile_is_blocked(self):
        with self.assertRaisesRegex(
            ClientTemplateRemediationError, "missing profiles"
        ):
            self._plan(
                Path("C:/Models/CLIENT_TEST"),
                project=_Project(_Template(profile="MISSING")),
            )

    def test_ve_profile_dash_sentinel_is_not_a_missing_profile(self):
        template = _Template(profile="-")
        plan = self._plan(Path("C:/Models/CLIENT_TEST"), project=_Project(template))
        self.assertEqual(plan["template"]["referenced_profiles"], [])

    def test_any_plan_edit_invalidates_checksum(self):
        plan = self._plan(Path("C:/Models/CLIENT_TEST"))
        plan["rooms"][0]["room_name"] = "Changed after approval"
        with self.assertRaisesRegex(
            ClientTemplateRemediationError, "checksum mismatch"
        ):
            validate_plan_hash(plan)

    def test_room_drift_after_preview_blocks_apply_before_gateway_write(self):
        project = _Project()
        model = _Model()
        plan = self._plan(
            Path("C:/Models/CLIENT_TEST"), project=project, model=model
        )
        model.body.data.general["thermal_template_name"] = "Changed in VE"

        class _Gateway:
            project_path = Path(plan["project"]["path"])

            def __init__(self, _iesve):
                self.project = project
                self.model = model

            def apply_existing_thermal_template_to_rooms(self, *_arguments, **_keywords):
                raise AssertionError("No VE write is permitted after room drift")

        with patch("swiss_sia.reference_model.ve_api.IesVeGateway", _Gateway):
            with self.assertRaisesRegex(
                ClientTemplateRemediationError, "changed after preview"
            ):
                apply_preview_plan(object(), plan)

    def test_unchanged_plan_returns_verified_non_compliance_receipt(self):
        project = _Project()
        model = _Model()
        plan = self._plan(
            Path("C:/Models/CLIENT_TEST"), project=project, model=model
        )

        class _Gateway:
            project_path = Path(plan["project"]["path"])

            def __init__(self, _iesve):
                self.project = project
                self.model = model

            @staticmethod
            def apply_existing_thermal_template_to_rooms(
                template_name, room_ids, structure_bridge=()
            ):
                return {
                    "template_name": template_name,
                    "room_ids": list(room_ids),
                    "structure_bridge": list(structure_bridge),
                    "after": [{"readback": "verified"}],
                }

        with patch("swiss_sia.reference_model.ve_api.IesVeGateway", _Gateway):
            receipt = apply_preview_plan(object(), plan)

        self.assertEqual(receipt["status"], "APPLIED_AND_READBACK_VERIFIED")
        self.assertEqual(receipt["compliance_claim"], "NOT_GRANTED")
        self.assertEqual(receipt["ve_receipt"]["room_ids"], ["ROOM-1"])

    def test_latest_evidence_requires_a_newer_post_mutation_audit(self):
        plan = self._plan(Path("C:/Models/CLIENT_TEST"))
        receipt = {
            "status": "APPLIED_AND_READBACK_VERIFIED",
            "plan_sha256": plan["plan_sha256"],
            "template": plan["template"],
            "evidence": plan["evidence"],
            "compliance_claim": "NOT_GRANTED",
        }

        class _Artifact:
            def __init__(self, label, modified):
                self.label = label
                self.modified = modified

            def stat(self):
                return type("Stat", (), {"st_mtime": self.modified})()

            def __str__(self):
                return self.label

        plan_path = _Artifact("plan.json", 1)
        receipt_path = _Artifact("receipt.json", 3)
        stale_audit = _Artifact("audit.json", 2)
        artifacts = iter([plan_path, receipt_path, stale_audit])

        def read(path):
            return plan if path is plan_path else receipt if path is receipt_path else {}

        with patch(
            "swiss_sia.client_template_remediation._latest_artifact",
            side_effect=lambda *_arguments: next(artifacts),
        ), patch(
            "swiss_sia.client_template_remediation._read_json_artifact",
            side_effect=read,
        ):
            summary = latest_remediation_evidence("C:/Models/CLIENT_TEST")

        self.assertEqual(summary["integrity_status"], "PASS")
        self.assertEqual(summary["post_remediation_audit"], "REQUIRED")
        self.assertEqual(summary["compliance_claim"], "NOT_GRANTED")
        self.assertEqual(summary["evidence_mode"], "MANUAL_REVIEW_EVIDENCE")


if __name__ == "__main__":
    unittest.main()
