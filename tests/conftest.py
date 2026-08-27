"""Test-suite separation between the two products in this repository.

There are two distinct products here, and they share no code (verified: neither
side imports the other):

* the **SIA 380/2 client-compliance checker** -- reads a client's IESVE model
  and reports a per-requirement diagnostic. This is the commercial MVP.
* the **SIA 4010 validation** machinery -- builds the exact reference test cases
  and validates the toolchain.

Their tests lived side by side in one flat directory, which made the boundary
invisible.  Rather than move files (which would break the ``parents[1]`` path
resolution many tests rely on), this conftest tags each test so either product's
suite can be run on its own:

    pytest -m sia3802     # the 380/2 client-compliance product only
    pytest -m sia4010     # the 4010 validation machinery only
    pytest -m shared      # infrastructure shared by both / model builder
    pytest                # everything, unchanged

The full authoritative boundary is documented in
``docs/project/ARCHITECTURE_380-2_vs_4010.md``.
"""

import pytest

#: Tests of the SIA 380/2 client-compliance product (swiss_sia top-level:
#: data_extractor, model_analyzer, sia380_checker, compliance_*, reference_project,
#: evidence_* client workflow, remediation probe, the company Excel/PDF report).
_SIA3802_PRODUCT_TESTS = frozenset(
    {
        "test_sia3802_normative_extensions",
        "test_sia3802_robustness",
        "test_compliance_hub",
        "test_compliance_report_pdf",
        "test_health_score",
        "test_reference_project",
        "test_project_metadata_evidence",
        "test_claim_safety_extensions",
        "test_iesve_extraction_contract",
        "test_emission_factors",
        "test_excel_report_smoke",
        "test_solar_protection_logic",
        "test_remediation_probe",
        "test_evidence_bootstrap",
        "test_evidence_wizard",
    }
)

#: 4010 tests not caught by the ``test_sia4010_`` prefix or the ``engine`` tree.
_SIA4010_EXTRA_TESTS = frozenset(
    {
        "test_haeufigkeitskassen_extractor",
        "test_iso52016_test1_verification_cases",
        "test_anwenderbericht_facts_file",
        "test_sia_model_builder_interface",
        "test_validation_class_scope",
    }
)


def _product_marker(stem: str, parts) -> str:
    """Return the product marker for one test module.

    Args:
        stem: Test file name without extension.
        parts: Path parts of the test file, to catch the ``engine`` tree.

    Returns:
        str: ``"sia3802"``, ``"sia4010"`` or ``"shared"``.
    """

    if stem in _SIA3802_PRODUCT_TESTS:
        return "sia3802"
    if (
        stem.startswith("test_sia4010_")
        or stem in _SIA4010_EXTRA_TESTS
        or "engine" in parts
    ):
        return "sia4010"
    # Everything else -- the VE model builder, VE gateways, weather conversion,
    # report styling and UI translations -- is infrastructure both sides lean on.
    return "shared"


def pytest_configure(config):
    """Register the product markers so ``-m`` selection is warning-free."""

    for marker, description in (
        ("sia3802", "SIA 380/2 client-compliance product tests"),
        ("sia4010", "SIA 4010 validation machinery tests"),
        ("shared", "infrastructure shared by both products"),
    ):
        config.addinivalue_line("markers", "{}: {}".format(marker, description))


def pytest_collection_modifyitems(config, items):
    """Tag every collected test with exactly one product marker."""

    for item in items:
        path = getattr(item, "path", None)
        if path is None:
            continue
        marker = _product_marker(path.stem, path.parts)
        item.add_marker(getattr(pytest.mark, marker))
