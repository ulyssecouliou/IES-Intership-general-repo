"""Tests for the source-traced SIA 2024 classroom template bundle."""

from pathlib import Path

from swiss_sia.sia3802_classroom_template import (
    TEMPLATE_NAME,
    build_classroom_operational_plan,
    load_classroom_reference,
)


ROOT = Path(__file__).resolve().parents[1]


def test_classroom_reference_contains_verified_direct_values():
    reference = load_classroom_reference(ROOT)
    values = reference["values"]
    assert values["area_per_person_m2"] == {"value": 4.0, "cell": "AP17"}
    assert values["equipment_standard_w_m2"] == {"value": 8.0, "cell": "AY17"}
    assert values["outdoor_air_standard_m3_h_m2"] == {
        "value": 7.25,
        "cell": "CB17",
    }
    assert reference["claims"]["automatic_compliance_claim"] is False


def test_operational_plan_is_complete_and_preserves_review_boundaries():
    plan, summary = build_classroom_operational_plan(ROOT)
    assert plan.thermal_template.name == TEMPLATE_NAME
    assert len(plan.profiles) == 51
    assert {item.key for item in plan.gains} == {
        "people_gain",
        "lighting_gain",
        "equipment_gain",
    }
    assert {item.key for item in plan.air_exchanges} == {
        "infiltration",
        "outdoor_air",
    }
    assert summary["automatic_compliance_claim"] is False
    statuses = {
        item["status"]
        for item in summary["ve_mappings_requiring_review"].values()
    }
    assert "ENGINEERING_MAPPING_REQUIRES_REVIEW" in statuses
    assert "IMPLEMENTATION_PROXY_REQUIRES_PROJECT_OVERRIDE" in statuses


def test_operational_fields_have_valid_traceability_and_exact_unit_conversion():
    plan, _ = build_classroom_operational_plan(ROOT)
    for profile in plan.profiles:
        assert profile.evidence.validation_error() is None
        assert profile.data.validation_error() is None
    for definition in (*plan.gains, *plan.air_exchanges):
        assert definition.evidence.validation_error() is None
        assert all(field.validation_error() is None for field in definition.properties.values())
    assert all(
        field.validation_error() is None
        for field in plan.thermal_template.room_conditions.values()
    )
    assert all(
        field.validation_error() is None
        for field in plan.thermal_template.system_data.values()
    )
    exchanges = {item.key: item for item in plan.air_exchanges}
    gains = {item.key: item for item in plan.gains}
    assert gains["people_gain"].properties["pc_convective_gain"].value == 50.0
    assert "radiant_fraction" not in gains["people_gain"].properties
    assert exchanges["outdoor_air"].properties["max_flow"].value == 7.25 / 3.6
    assert exchanges["infiltration"].properties["max_flow"].value == 0.15 / 3.6


def test_weekly_profiles_use_ve_2025_twelve_slot_contract():
    plan, _ = build_classroom_operational_plan(ROOT)
    weekly = [item for item in plan.profiles if item.profile_type == "weekly"]
    assert len(weekly) == 24
    assert all(len(item.data.value) == 12 for item in weekly)
    assert all(
        item.data.value[5]["profile_ref"] == "sia4010_classroom_off_day"
        and item.data.value[6]["profile_ref"] == "sia4010_classroom_off_day"
        for item in weekly
    )
