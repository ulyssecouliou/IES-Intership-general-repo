"""Apply the checksum-bound SIA 4010 authority response of 2026-08-28.

This script records only decisions explicitly present in the retained email.
It does not inspect or transcribe the accompanying workbook: the four SIA 2024
records therefore remain technically PENDING until a cell-level review exists.
"""

from __future__ import print_function

import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "sia4010_external_inputs.test2a_prepared.json"
OFFICIAL_CONTRACT = ROOT / "config" / "sia4010_official_input_contract.json"
EMAIL = (
    ROOT
    / "sia4010_evidence"
    / "authority_decisions"
    / "2026-08-28_remaining_sia4010_clarifications_email.txt"
)
WORKBOOK = (
    ROOT
    / "sia4010_evidence"
    / "source_audits"
    / "sia2024_required_use_types_20260828"
    / "SIA 2024_Nutzungsdaten_SIA 4010.xlsx"
)
PV_OUTPUT = (
    ROOT
    / "sia4010_evidence"
    / "source_audits"
    / "test7_pv_authority_20260828"
)

EXPECTED_EMAIL_SHA256 = (
    "15b6892f5f26d7500b7f376cda4a2b9d588e8351a7d73fd086b8c9566a560875"
)
EXPECTED_WORKBOOK_SHA256 = (
    "f8fa52198cb9b23d8663154ca73c35b6612fcc89ec43a8db307c1710b4ab220a"
)

USE_DATASETS = {
    "sia2024_auditorium_target_profiles": {
        "identity": "SIA 2024 auditorium target-use data supplied for Test 4",
        "scope": [
            "Test 4 auditorium target schedules",
            "densities, gains, simultaneity factors and use parameters",
        ],
    },
    "sia2024_example_building_standard_profiles": {
        "identity": "SIA 2024 example-building standard-use data supplied for Test 5",
        "scope": [
            "Test 5 room-by-room standard use data",
            "schedules, densities, gains and simultaneity factors",
        ],
    },
    "sia2024_restaurant_6_2_standard_profiles": {
        "identity": "SIA 2024 category 6.2 Selbstbedienungsrestaurant standard-use data",
        "scope": [
            "Test 6 category 6.2 standard schedules and use parameters",
        ],
    },
    "sia2024_kitchen_6_4_standard_profiles": {
        "identity": "SIA 2024 category 6.4 Küche zu Selbstbedienungsrestaurant standard-use data",
        "scope": [
            "Test 6 category 6.4 standard schedules and use parameters",
        ],
    },
}


def sha256(path):
    """Return the lowercase SHA-256 of *path*."""

    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path):
    """Load one UTF-8 JSON object from *path*."""

    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, payload):
    """Write *payload* as deterministic UTF-8 JSON with a final newline."""

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def config_path(path):
    """Return a repository path relative to the prepared manifest folder."""

    return "../" + str(Path(path).relative_to(ROOT)).replace("\\", "/")


def build_pv_binding():
    """Return the normalized authority decision for Test 7 photovoltaics."""

    locator = "Email reply received 2026-08-28, answer to Test 7 PV questions"
    values = [
        ("pv_authoritative_total_kwp", 62.62, "kWp"),
        ("pv_superseded_specification_total_kwp", 60.6, "kWp"),
        ("pv_module_power_w", 310, "W"),
        ("pv_roof_total_modules", 150, "module"),
        ("pv_roof_total_kwp", 45.0, "kWp"),
        ("pv_roof_east_modules", 75, "module"),
        ("pv_roof_west_modules", 75, "module"),
        ("pv_roof_east_kwp", 22.5, "kWp"),
        ("pv_roof_west_kwp", 22.5, "kWp"),
    ]
    return {
        "schema_id": "sia4010.authority_decision.v1",
        "schema_version": "1.0",
        "primary_source_sha256": EXPECTED_EMAIL_SHA256,
        "source_locator": locator,
        "decision_id": "SIA4010_TEST7_PV_20260828",
        "issued_by": "Prof. Gerhard Zweifel",
        "issued_date": "2026-08-28",
        "document_reference": "SIA 4010 Test 7 specification and PV layout clarification",
        "question": (
            "Which PV total takes precedence, and how is the 150-module roof "
            "array divided between east and west?"
        ),
        "decision": (
            "Use 62.62 kWp as the authoritative total. The 60.6 kWp text is "
            "an error. Use 310 W modules and split the 150-module, 45.0 kWp "
            "roof equally: 75 modules and 22.5 kWp east, and the same west."
        ),
        "applicable_cases": ["test_7/7"],
        "resolved_parameters": [
            {
                "id": key,
                "value": value,
                "unit": unit,
                "source_locator": locator,
            }
            for key, value, unit in values
        ],
    }


def write_pv_evidence():
    """Write the normalized Test 7 decision and strict validation report."""

    if sha256(EMAIL) != EXPECTED_EMAIL_SHA256:
        raise RuntimeError("The retained authority email checksum changed")
    binding = PV_OUTPUT / "sia_authority_test7_pv_precedence.binding.json"
    write_json(binding, build_pv_binding())
    report = {
        "schema_version": "1.0",
        "input_id": "sia_authority_test7_pv_precedence",
        "source_sha256": EXPECTED_EMAIL_SHA256,
        "status": "PASS",
        "validated_by": "Deterministic authority-response transcription",
        "validation_method": (
            "Checksum-bound direct transcription of the written decision, "
            "with roof module-count and installed-power arithmetic checks"
        ),
        "binding_artifact": {
            "path": binding.name,
            "sha256": sha256(binding),
            "schema_id": "sia4010.authority_decision.v1",
        },
        "checks": [
            {
                "id": "TEST7-PV-SOURCE-CHECKSUM",
                "status": "PASS",
                "detail": "The decision is bound to the retained 2026-08-28 email.",
            },
            {
                "id": "TEST7-PV-PRECEDENCE",
                "status": "PASS",
                "detail": "62.62 kWp supersedes the erroneous 60.6 kWp text.",
            },
            {
                "id": "TEST7-PV-ROOF-SPLIT",
                "status": "PASS",
                "detail": "75 + 75 = 150 modules and 22.5 + 22.5 = 45.0 kWp.",
            },
        ],
        "compliance_claim_allowed": False,
        "claim_guardrail": (
            "PASS validates this written PV decision only. It does not qualify "
            "the VE PV model, APS results or SIA Test 7."
        ),
    }
    validation = PV_OUTPUT / "sia_authority_test7_pv_precedence.validation.json"
    write_json(validation, report)
    return binding, validation


def update_prepared_manifest(validation):
    """Apply resolved authorizations without overstating technical readiness."""

    if sha256(WORKBOOK) != EXPECTED_WORKBOOK_SHA256:
        raise RuntimeError("The authority-supplied SIA 2024 workbook checksum changed")
    payload = load_json(CONFIG)
    records = payload["inputs"]

    for input_id, definition in USE_DATASETS.items():
        record = records[input_id]
        record.update(
            {
                "source_path": config_path(WORKBOOK),
                "source_sha256": EXPECTED_WORKBOOK_SHA256,
                "provenance_status": "SIA_SUPPLIED",
                "normative_authorization_status": "CONFIRMED",
                "normative_authorization_basis": (
                    "Supplied directly by Prof. Gerhard Zweifel on 2026-08-28 "
                    "for the requested SIA 4010 validation use types."
                ),
                "normative_authorization_scope": (
                    "Internal use for this SIA 4010 validation campaign; no "
                    "redistribution or broader normative claim."
                ),
                "normative_authorization_recorded_on": "2026-08-28",
                "source_authority": "SIA, supplied by Prof. Gerhard Zweifel",
                "license_reference": (
                    "Authority-supplied controlled workbook for this validation "
                    "campaign; internal traceability use only"
                ),
                "dataset_identity": definition["identity"],
                "machine_readable_format": (
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                ),
                "semantic_scope": definition["scope"],
                "technical_validation": {
                    "status": "PENDING",
                    "report_path": None,
                    "report_sha256": None,
                    "reason": (
                        "Source custody and authorization are verified, but "
                        "sheet names, cells, formulas, values and rendered "
                        "layout have not yet completed controlled cell-level "
                        "validation and no normalized binding exists."
                    ),
                },
            }
        )

    for input_id in ("test4_fan_curve_digitization", "test5_fan_curve_digitization"):
        record = records[input_id]
        family = "test4" if input_id.startswith("test4") else "test5"
        fan_report = (
            ROOT
            / "sia4010_evidence"
            / "source_audits"
            / "{}_fan_curve_20260826".format(family)
            / "{}.validation.json".format(input_id)
        )
        record.update(
            {
                "normative_authorization_status": "CONFIRMED",
                "normative_authorization_basis": (
                    "Prof. Gerhard Zweifel confirmed on 2026-08-28 that no "
                    "single numeric curve, interpolation method or tolerance "
                    "is prescribed and that candidate-specific tool "
                    "approximations are expected."
                ),
                "normative_authorization_scope": (
                    "Use the checksum-bound source digitization to develop, "
                    "document and validate an IESVE-specific approximation. "
                    "Do not call the selected approximation SIA-prescribed."
                ),
                "normative_authorization_recorded_on": "2026-08-28",
                "license_reference": (
                    "SIA 4010 test specification supplied for this validation; "
                    "candidate-specific fan approximation authorized by written "
                    "authority response dated 2026-08-28"
                ),
                "technical_validation": {
                    "status": "PASS",
                    "report_path": config_path(fan_report),
                    "report_sha256": sha256(fan_report),
                },
            }
        )

    epb = records["en16798_5_1_annex_d_rotary_recovery_model"]
    epb.update(
        {
            "normative_authorization_status": "CONFIRMED",
            "normative_authorization_basis": (
                "Prof. Gerhard Zweifel confirmed on 2026-08-28 that the existing "
                "EPB Center workbook may be used."
            ),
            "normative_authorization_scope": (
                "Internal Test 5 Annex D implementation and traceability. The "
                "newer EPB Center workbook must be retrieved and compared before "
                "any source rebinding."
            ),
            "normative_authorization_recorded_on": "2026-08-28",
            "license_reference": (
                "EPB Center demonstration workbook explicitly authorized by the "
                "SIA validation authority on 2026-08-28 for this campaign"
            ),
        }
    )

    pv = records["sia_authority_test7_pv_precedence"]
    pv.update(
        {
            "source_path": config_path(EMAIL),
            "source_sha256": EXPECTED_EMAIL_SHA256,
            "provenance_status": "SIA_SUPPLIED",
            "normative_authorization_status": "CONFIRMED",
            "normative_authorization_basis": (
                "Direct written decision from Prof. Gerhard Zweifel received "
                "2026-08-28."
            ),
            "normative_authorization_scope": (
                "Test 7 PV total precedence, current module power and roof "
                "east/west allocation only."
            ),
            "normative_authorization_recorded_on": "2026-08-28",
            "source_authority": "Prof. Gerhard Zweifel, SIA 4010 validation authority",
            "license_reference": "Direct written authority decision; internal traceability",
            "dataset_identity": "SIA 4010 Test 7 PV precedence and roof split decision",
            "machine_readable_format": "text/plain plus normalized JSON authority decision",
            "semantic_scope": [
                "authoritative installed PV total 62.62 kWp",
                "superseded specification value 60.6 kWp",
                "310 W current module power",
                "roof split: 75 modules and 22.5 kWp east and west",
            ],
            "technical_validation": {
                "status": "PASS",
                "report_path": config_path(validation),
                "report_sha256": sha256(validation),
            },
        }
    )

    payload["purpose"] = (
        "Repository-prepared SIA 4010 external-input manifest. It includes "
        "checksum-bound human authorizations through 2026-08-28. Workbook "
        "records remain PENDING until cell-level validation and normalized "
        "bindings exist; no entry implies a SIA compliance verdict."
    )
    write_json(CONFIG, payload)


def update_official_contract():
    """Record the resolved decisions in the source-traced implementation contract."""

    payload = load_json(OFFICIAL_CONTRACT)
    supplements = payload["common"].setdefault("authority_supplements", {})
    supplements["sia4010_remaining_clarifications_20260828"] = {
        "status": "AUTHORITY_RESPONSE_RECORDED",
        "source": (
            "Written response from Prof. Gerhard Zweifel received 2026-08-28; "
            "checksum-bound under sia4010_evidence/authority_decisions"
        ),
        "decision_id": "SIA4010_REMAINING_CLARIFICATIONS_20260828",
        "resolved_scope": [
            "SIA 2024 source supply for Tests 4-6",
            "Test 3 edition interpretation",
            "Tests 4-5 candidate-specific fan approximation policy",
            "Test 5 EPB Center workbook authorization",
            "Test 6 category identities",
            "Test 7 PV total precedence and roof split",
        ],
        "claim_guardrail": (
            "The decisions resolve source meaning and authorization only; "
            "they do not qualify VE implementations or establish test PASS."
        ),
    }

    tests = payload["tests"]
    tests["4"]["unresolved_dependencies"] = [
        "Example-building exact auditorium geometry and constructions",
        "Cell-validated binding of the authority-supplied SIA 2024 auditorium data",
        "Documented and sensitivity-tested IESVE-specific fan approximation",
        "Exact room-temperature setpoint curve implementation",
        "Qualified Apache Systems topology, CO2/VAV controllers and APS outputs",
    ]
    tests["5"]["unresolved_dependencies"] = [
        "Example-building exact multizone geometry, areas and constructions",
        "Cell-validated room-by-room binding of the authority-supplied SIA 2024 data",
        "Technical validation of the authorized EN 16798-5-1 Annex D workbook",
        "Retrieval and formula comparison of the newer EPB Center workbook",
        "Documented and sensitivity-tested IESVE-specific fan approximation",
        "Qualified multizone Apache Systems, humidity, recovery and APS bindings",
    ]
    tests["6"]["unresolved_dependencies"] = [
        "Example-building exact restaurant/kitchen geometry and constructions",
        "Cell-validated bindings for confirmed categories 6.2 and 6.4",
        "Authority follow-up on conflicting example-building category numbering",
        "Qualified airflow imbalance, overflow, stage control, recovery and APS bindings",
    ]
    test7_inputs = tests["7"]["confirmed_inputs"]
    test7_inputs.update(
        {
            "pv_authoritative_total_kwp": 62.62,
            "pv_superseded_specification_total_kwp": 60.6,
            "pv_specification_value_is_error": True,
            "pv_authority_decision": "SIA4010_TEST7_PV_20260828",
            "pv_roof_east_modules": 75,
            "pv_roof_west_modules": 75,
            "pv_roof_east_kwp": 22.5,
            "pv_roof_west_kwp": 22.5,
        }
    )
    tests["7"]["unresolved_dependencies"] = [
        "Checksum-qualified load-profile importer",
        "Qualified VE binding of the source-traced heat-pump performance tables",
        "Exact storage hysteresis/controller implementation",
        "Bivalence temperature and simultaneous heat-recovery sequence",
        "Corrected Test 7 specification publication; retain the 60.6/62.62 discrepancy until issued",
        "Qualified VE plant, storage, distribution, PV and final-energy APS bindings",
    ]
    write_json(OFFICIAL_CONTRACT, payload)


def main():
    """Generate normalized evidence and update both repository contracts."""

    binding, validation = write_pv_evidence()
    update_prepared_manifest(validation)
    update_official_contract()
    print("Applied SIA 4010 authority response 2026-08-28")
    print("PV binding: {}".format(binding))
    print("Prepared manifest: {}".format(CONFIG))
    print("Official contract: {}".format(OFFICIAL_CONTRACT))


if __name__ == "__main__":
    main()
