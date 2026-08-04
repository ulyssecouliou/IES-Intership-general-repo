"""Future-facing SIA 4010 official test integration boundary.

No official test values, result tolerances, or acceptance rules are embedded in
this package.  They must be loaded from a checksum-verified official bundle.
"""

from .compliance_comparator import ComparisonOutcome, ComparisonStatus
from .apachesim_qualification import (
    ApacheSimQualificationReceipt,
    SIMULATION_QUALIFICATION_CASES,
    run_qualified_apachesim,
)
from .active_case_evaluation import (
    ActiveCaseEvaluationReceipt,
    evaluate_qualified_active_case,
)
from .expected_results import ExpectedResult, ObservedResult
from .evidence_registry import (
    build_all_class_navigators,
    register_case_evaluation,
    register_case_simulation,
    register_model_outcome,
)
from .external_input_manifest import (
    EXTERNAL_INPUT_CATALOG,
    EXTERNAL_INPUT_BINDING_SCHEMAS,
    EXTERNAL_INPUT_FILENAME,
    ExternalInputEvidence,
    ExternalInputReadiness,
    Sia4010ExternalInputManifest,
    build_external_input_matrix,
    external_input_readiness,
    required_external_input_ids,
)
from .navigator import NavigatorEvaluation, NavigatorGate, Sia4010ValidationNavigator
from .normalized_external_inputs import (
    CommonCellExternalBindings,
    NormalizedIsoTestCell,
    NormalizedOfficeProfiles,
    NormalizedOpaqueConstruction,
    NormalizedUsageProfile,
    NormalizedVeProfileGraph,
    NormalizedVeProfileNode,
    NormalizedWeatherBinding,
    Test2AExternalBindings,
    load_iso_test_cell,
    load_common_cell_external_bindings,
    load_normalized_binding_payload,
    load_office_profiles,
    load_test2a_external_bindings,
    load_weather_binding,
)
from .case_registry import Sia4010CaseCapability, get_case_capability
from .test1_variant_bundle import (
    HEAVYWEIGHT_RUNTIME_QUALIFICATION_CASES,
    LIGHTWEIGHT_RUNTIME_QUALIFICATION_CASES,
    RUNTIME_QUALIFICATION_CASES,
    build_test1_heavyweight_probe_bundle,
    build_test1_lightweight_probe_bundle,
    build_test1_runtime_probe_bundle,
)
from .test2a_source_bundle import (
    Test2ASourceBundleReceipt,
    build_test2a_source_bound_bundle,
)
from .test2a_profile_binding import (
    Test2AProfileDefinitionBundle,
    build_test2a_profile_definitions,
)
from .test2a_profile_qualification import qualify_test2a_profile_graph
from .test2a_shading_control import (
    Test2AFabricAwningControl,
    Test2AOpticalDiagnosticContract,
    build_test2a_fabric_awning_control,
    build_test2a_optical_diagnostic_contract,
)
from .test2a_diagnostic_workbook import (
    EXPECTED_TEST2_WORKBOOK_SHA256,
    Test2ADiagnosticWorkbookBinding,
    Test2AWorkbookSeriesBinding,
    load_test2a_diagnostic_workbook_binding,
)
from .test2a_diagnostic_evaluation import (
    REFERENCE_ONLY_STATUS as TEST2A_2E1_REFERENCE_ONLY_STATUS,
    DiagnosticAnnualReference,
    Test2A2E1DiagnosticEvaluation,
    Test2A2E1ReferenceDataset,
    evaluate_test2a_2e1_diagnostic,
    load_test2a_2e1_reference_dataset,
    write_test2a_2e1_diagnostic_evaluation,
)
from .test2a_diagnostic_aps import (
    Test2A2E1ApsBindingContract,
    Test2A2E1ApsEvaluationReceipt,
    Test2A2E1ApsSeriesBinding,
    build_test2a_2e1_aps_binding_contract,
    evaluate_test2a_2e1_qualified_aps,
    extract_test2a_2e1_candidate_series,
    write_test2a_2e1_aps_evaluation,
)
from .test2a_shading_qualification import (
    qualify_test2a_2e1_optical_setters,
    qualify_test2a_shading_setters,
)
from .test2a_optical_workflow import (
    Test2A2E1OpticalWorkflowReceipt,
    run_test2a_2e1_optical_workflow,
)
from .test3_runtime_capability import (
    build_test3_runtime_capability_report,
    write_test3_runtime_capability_report,
)
from .hvac_plant_runtime_capability import (
    build_hvac_plant_runtime_capability_report,
    write_hvac_plant_runtime_capability_report,
)
from .test3_external_bindings import (
    NormalizedAuthorityDecision,
    NormalizedControlFunction,
    NormalizedControlParameter,
    NormalizedControlSignal,
    NormalizedShadingDevice,
    NormalizedSia3874Controls,
    Test3ExternalBindings,
    load_authority_decision,
    load_shading_device,
    load_sia3874_controls,
    load_test3_external_bindings,
)
from .test3_source_bundle import (
    TEST3_VARIANTS,
    Test3SourceBundleReceipt,
    build_test3_source_bound_bundle,
)
from .official_input_contract import Sia4010OfficialInputContract
from .preparation_bundle import prepare_all_classes, prepare_case, prepare_class
from .test_loader import OfficialTestBundle, Sia4010TestLoader
from .test_runner import Sia4010TestRunner

__all__ = [
    "ComparisonOutcome",
    "ComparisonStatus",
    "ApacheSimQualificationReceipt",
    "SIMULATION_QUALIFICATION_CASES",
    "ActiveCaseEvaluationReceipt",
    "ExpectedResult",
    "EXTERNAL_INPUT_CATALOG",
    "EXTERNAL_INPUT_BINDING_SCHEMAS",
    "EXTERNAL_INPUT_FILENAME",
    "ExternalInputEvidence",
    "ExternalInputReadiness",
    "build_all_class_navigators",
    "build_external_input_matrix",
    "Sia4010CaseCapability",
    "Sia4010ExternalInputManifest",
    "Sia4010OfficialInputContract",
    "ObservedResult",
    "NavigatorEvaluation",
    "NavigatorGate",
    "CommonCellExternalBindings",
    "NormalizedIsoTestCell",
    "NormalizedOfficeProfiles",
    "NormalizedOpaqueConstruction",
    "NormalizedUsageProfile",
    "NormalizedVeProfileGraph",
    "NormalizedVeProfileNode",
    "NormalizedWeatherBinding",
    "NormalizedAuthorityDecision",
    "NormalizedControlFunction",
    "NormalizedControlParameter",
    "NormalizedControlSignal",
    "NormalizedShadingDevice",
    "NormalizedSia3874Controls",
    "OfficialTestBundle",
    "Sia4010ValidationNavigator",
    "Test2AExternalBindings",
    "Test2AProfileDefinitionBundle",
    "Test2AFabricAwningControl",
    "Test2AOpticalDiagnosticContract",
    "Test2ADiagnosticWorkbookBinding",
    "Test2AWorkbookSeriesBinding",
    "DiagnosticAnnualReference",
    "Test2A2E1DiagnosticEvaluation",
    "Test2A2E1ReferenceDataset",
    "Test2A2E1ApsBindingContract",
    "Test2A2E1ApsEvaluationReceipt",
    "Test2A2E1ApsSeriesBinding",
    "Test2ASourceBundleReceipt",
    "Test3ExternalBindings",
    "Test3SourceBundleReceipt",
    "Sia4010TestLoader",
    "Sia4010TestRunner",
    "get_case_capability",
    "load_iso_test_cell",
    "load_common_cell_external_bindings",
    "load_normalized_binding_payload",
    "load_office_profiles",
    "load_test2a_external_bindings",
    "load_weather_binding",
    "load_authority_decision",
    "load_shading_device",
    "load_sia3874_controls",
    "load_test3_external_bindings",
    "RUNTIME_QUALIFICATION_CASES",
    "LIGHTWEIGHT_RUNTIME_QUALIFICATION_CASES",
    "HEAVYWEIGHT_RUNTIME_QUALIFICATION_CASES",
    "build_test1_lightweight_probe_bundle",
    "build_test1_heavyweight_probe_bundle",
    "build_test1_runtime_probe_bundle",
    "build_test2a_source_bound_bundle",
    "build_test3_source_bound_bundle",
    "TEST3_VARIANTS",
    "build_test2a_profile_definitions",
    "build_test2a_fabric_awning_control",
    "build_test2a_optical_diagnostic_contract",
    "load_test2a_diagnostic_workbook_binding",
    "EXPECTED_TEST2_WORKBOOK_SHA256",
    "evaluate_test2a_2e1_diagnostic",
    "load_test2a_2e1_reference_dataset",
    "write_test2a_2e1_diagnostic_evaluation",
    "TEST2A_2E1_REFERENCE_ONLY_STATUS",
    "build_test2a_2e1_aps_binding_contract",
    "evaluate_test2a_2e1_qualified_aps",
    "extract_test2a_2e1_candidate_series",
    "write_test2a_2e1_aps_evaluation",
    "qualify_test2a_profile_graph",
    "qualify_test2a_shading_setters",
    "qualify_test2a_2e1_optical_setters",
    "Test2A2E1OpticalWorkflowReceipt",
    "run_test2a_2e1_optical_workflow",
    "build_test3_runtime_capability_report",
    "write_test3_runtime_capability_report",
    "build_hvac_plant_runtime_capability_report",
    "write_hvac_plant_runtime_capability_report",
    "evaluate_qualified_active_case",
    "external_input_readiness",
    "prepare_all_classes",
    "prepare_case",
    "prepare_class",
    "register_case_evaluation",
    "register_case_simulation",
    "register_model_outcome",
    "required_external_input_ids",
    "run_qualified_apachesim",
]
