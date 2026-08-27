"""Fail-closed tests for the seven human-review governance domains."""

from swiss_sia.assessment_governance import (
    BLOCKED,
    DOCUMENTED,
    RESERVE,
    evaluate_assessment_governance,
    governance_summary,
    legal_wording,
    project_metadata_governance_gaps,
    report_text,
)


def complete_metadata():
    return {
        "weather_basis": "SIA 2028 DRY",
        "weather_file": "reviewed.epw",
        "weather_source_authority": "Approved SIA climate brief",
        "weather_use_case": "SIA3802_COOLING_NEED",
        "weather_scenario_period": "2035 RCP8.5 DRY",
        "location": "Geneva",
        "altitude_m": "420",
        "location_source": "Approved climate brief",
        "altitude_source": "Project survey",
        "ventilation_strategy": "MECHANICAL_PRESENT",
        "ventilation_justification": "Mechanical ventilation per design brief.",
        "ventilation_scope": "All conditioned rooms",
        "ventilation_flow_source": "HVAC design schedule",
        "lighting_scope": "IN_SCOPE",
        "lighting_power_source": "Lighting schedule",
        "lighting_scope_justification": "All assessed rooms included",
        "aps_outputs_required": "YES",
        "system_power_source": "HVAC schedule and VE readback",
        "assumptions_status": "NO_UNRESOLVED_ASSUMPTIONS",
        "assumptions_register": "Design brief, assumptions register",
        "reviewer": "A. Reviewer",
        "review_date": "2026-08-25",
        "reviewer_role": "Responsible energy specialist",
        "reviewer_organisation": "Example SA",
        "reviewer_competence_basis": "Building simulation engineer",
        "reviewer_acceptance_scope": "Weather, inputs, results and reserves",
        "report_use_acknowledgement": "ENGINEERING_ASSESSMENT_ONLY",
    }


def test_empty_metadata_blocks_every_domain():
    findings = evaluate_assessment_governance({}, {}, "en")
    assert len(findings) == 7
    assert {finding.status for finding in findings} == {BLOCKED}
    assert governance_summary(findings)["overall_status"] == BLOCKED


def test_complete_traceable_metadata_documents_every_domain_without_certifying():
    findings = evaluate_assessment_governance(
        complete_metadata(), {"reviewed_weather_match_status": "MATCH"}, "en"
    )
    assert {finding.status for finding in findings} == {DOCUMENTED}
    wording = legal_wording("en").lower()
    assert "not an official sia certificate" in wording
    assert "does not attest official software-method validation" in wording


def test_open_assumptions_are_a_named_reserve():
    metadata = complete_metadata()
    metadata["assumptions_status"] = "OPEN_ASSUMPTIONS"
    findings = evaluate_assessment_governance(
        metadata, {"reviewed_weather_match_status": "MATCH"}, "en"
    )
    assumptions = next(item for item in findings if item.domain == "external_assumptions")
    assert assumptions.status == RESERVE
    assert governance_summary(findings)["overall_status"] == RESERVE


def test_weather_mismatch_blocks_even_when_metadata_is_complete():
    findings = evaluate_assessment_governance(
        complete_metadata(), {"reviewed_weather_match_status": "MISMATCH"}, "en"
    )
    weather = next(item for item in findings if item.domain == "weather_location")
    assert weather.status == BLOCKED


def test_conditional_source_and_acknowledgement_gaps_are_explicit():
    metadata = complete_metadata()
    metadata["ventilation_flow_source"] = ""
    metadata["report_use_acknowledgement"] = "UNDER_REVIEW"
    gaps = project_metadata_governance_gaps(metadata)
    assert "ventilation_flow_source" in gaps
    assert "report_use_acknowledgement" in gaps


def test_report_headings_and_legal_wording_exist_in_all_languages():
    for language in ("en", "de", "fr", "it"):
        assert report_text("section_title", language)
        assert report_text("uncertainty", language)
        assert legal_wording(language)
    assert "Gouvernance" in report_text("section_title", "fr")
    assert "évaluation" in legal_wording("fr")
