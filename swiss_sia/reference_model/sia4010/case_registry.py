"""Single source of truth for SIA 4010 case-generation capabilities.

The official workbooks, parsers and navigator cover every exact validation
variant.  VE model generation is a separate capability and must never be
inferred from that coverage.  This registry makes the distinction explicit for
the user interface, launchers, audits and tests.
"""

from dataclasses import asdict, dataclass
from typing import Any, Dict, Tuple

from ..exceptions import ConfigurationError
from .model_scenario import TEST_CASES


PREPARATION_READY = "PREPARATION_READY"
GUARDED_MUTATION_READY = "GUARDED_MUTATION_READY"
RUNTIME_QUALIFICATION_READY = "RUNTIME_QUALIFICATION_READY"

#: Diagnostic cases of the Test 1 → Test 2 transition. The specification
#: requires annual hourly power datasets for them and states NO comparison
#: criterion; `refs/reference-data/test-1.ref.json` therefore carries no
#: band for them, and none may be invented. They are deliverables, not
#: judged cases. Case 1E, however, is judged: it is handled separately.
TEST1_DIAGNOSTIC_CASES = ("1A", "1B", "1C", "1D")


@dataclass(frozen=True)
class Sia4010CaseCapability:
    """Auditable implementation state of one exact official model case."""

    variant: str
    case_id: str
    base_test_id: str
    preparation_status: str
    generation_status: str
    generator_id: str
    blocker_code: str
    blocker_detail: str
    required_source_roles: Tuple[str, ...]

    @property
    def mutation_supported(self) -> bool:
        """Return whether a tested guarded VE mutation path is implemented."""

        return self.generation_status == GUARDED_MUTATION_READY

    @property
    def runtime_qualification_supported(self) -> bool:
        """Return whether a guarded disposable-project probe is implemented."""

        return self.generation_status == RUNTIME_QUALIFICATION_READY

    @property
    def runtime_discovery_supported(self) -> bool:
        """Return whether a read-only VE API discovery probe is implemented."""

        return (
            (self.variant == "test_2A" and self.case_id == "2A")
            or self.base_test_id in {"3", "4", "5", "6", "7"}
        )

    @property
    def source_bound_bundle_supported(self) -> bool:
        """Return whether exact delegated inputs can build a generator contract."""

        return (
            (self.variant == "test_2A" and self.case_id == "2A")
            or self.base_test_id == "3"
        )

    @property
    def geometry_artifact_supported(self) -> bool:
        """Return whether PREPARE_ONLY can write source-qualified gbXML."""

        return self.base_test_id in {"1", "2", "3"}

    @property
    def aps_evaluation_supported(self) -> bool:
        """Return whether exact runtime-qualified APS bindings cover this case."""

        return self.aps_evaluation_scope != "UNAVAILABLE"

    @property
    def apachesim_qualification_supported(self) -> bool:
        """Return whether the direct guarded annual ApacheSim route exists."""

        return (
            self.variant == "test_1"
            and self.case_id
            in set(TEST1_DIAGNOSTIC_CASES)
            | {"600", "640", "600FF", "900", "940", "900FF"}
            and (
                self.mutation_supported
                or self.runtime_qualification_supported
            )
        )

    @property
    def qualified_template_simulation_supported(self) -> bool:
        """Return whether an exact reviewed template can run and be evaluated."""

        return (self.variant, self.case_id) in {
            ("test_1", "1E"),
            ("test_2A", "2A"),
            ("test_2B", "2B"),
            ("test_2C", "2C"),
            ("test_2D", "2D"),
        }

    @property
    def aps_evaluation_scope(self) -> str:
        """Return the exact completeness of the qualified APS evaluation."""

        if self.variant == "test_1":
            if self.case_id == "1E":
                return "OFFICIAL_CRITERIA_IMPLEMENTED"
            if self.case_id in TEST1_DIAGNOSTIC_CASES:
                # Deliberately NOT REFERENCE_OUTPUTS_IMPLEMENTED: that value
                # would assert reference outputs exist, and test-1.ref.json
                # holds none for 1A to 1D -- zero mentions of them. The
                # specification asks for an annual hourly deliverable and states
                # no comparison criterion, so there is nothing to compare to and
                # nothing may be invented.
                return "HOURLY_DELIVERABLE_ONLY_NO_REFERENCE"
            if self.case_id in {
                "600",
                "640",
                "600FF",
                "900",
                "940",
                "900FF",
            }:
                return "REFERENCE_OUTPUTS_IMPLEMENTED"
        if self.base_test_id == "2":
            return "OFFICIAL_CRITERIA_IMPLEMENTED"
        return "UNAVAILABLE"

    @property
    def aps_full_evaluation_supported(self) -> bool:
        """Return whether every implemented official criterion is available."""

        return self.aps_evaluation_scope in {
            "OFFICIAL_CRITERIA_IMPLEMENTED",
            "REFERENCE_OUTPUTS_IMPLEMENTED",
        }

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe capability record."""

        return {
            **asdict(self),
            "mutation_supported": self.mutation_supported,
            "runtime_qualification_supported": (
                self.runtime_qualification_supported
            ),
            "runtime_discovery_supported": self.runtime_discovery_supported,
            "source_bound_bundle_supported": (
                self.source_bound_bundle_supported
            ),
            "geometry_artifact_supported": self.geometry_artifact_supported,
            "aps_evaluation_supported": self.aps_evaluation_supported,
            "apachesim_qualification_supported": (
                self.apachesim_qualification_supported
            ),
            "qualified_template_simulation_supported": (
                self.qualified_template_simulation_supported
            ),
            "aps_evaluation_scope": self.aps_evaluation_scope,
            "aps_full_evaluation_supported": (
                self.aps_full_evaluation_supported
            ),
        }


def base_test_id(variant: str) -> str:
    """Return the official base-test number for one exact variant key."""

    normalized = str(variant)
    if not normalized.startswith("test_") or len(normalized) < 6:
        raise ConfigurationError(
            "Unsupported SIA 4010 variant identifier: {!r}".format(variant)
        )
    test_id = normalized[5]
    if test_id not in "1234567":
        raise ConfigurationError(
            "Unsupported SIA 4010 variant identifier: {!r}".format(variant)
        )
    return test_id


def _blocker_for_test(test_id: str) -> Tuple[str, str]:
    """Return the honest software blocker for a not-yet-generated test."""

    blockers = {
        "1": (
            "VE_CASE_GENERATOR_NOT_IMPLEMENTED",
            "Only Test 1 Case 600 currently has a verified guarded VE generator. "
            "The remaining Test 1 case-specific envelope, glazing, shading and "
            "free-floating settings still require source-bound generator rules.",
        ),
        "2": (
            "VE_SOLAR_CONTROL_BINDING_NOT_IMPLEMENTED",
            "The official solar-protection inputs and dynamic SIA 387/4 control "
            "logic are parsed for validation but are not yet bound to a tested "
            "VE mutation strategy.",
        ),
        "3": (
            "VE_LIGHTING_CONTROL_BINDING_NOT_IMPLEMENTED",
            "The read-only VE lighting/template/sensor discovery probe is "
            "implemented for all twelve variants. When every delegated source "
            "is READY_FOR_BINDING, a checksum-traced Test 3 generator contract "
            "is also produced. Its controls are not yet bound to a tested VE "
            "mutation strategy.",
        ),
        "4": (
            "VE_HVAC_TOPOLOGY_BINDING_NOT_IMPLEMENTED",
            "The official single-zone all-air system topology and controls are "
            "not yet bound to a tested Apache Systems mutation strategy.",
        ),
        "5": (
            "VE_MULTIZONE_HVAC_BINDING_NOT_IMPLEMENTED",
            "The official multizone air-handling, recovery and humidification "
            "variants are not yet bound to a tested Apache Systems mutation "
            "strategy.",
        ),
        "6": (
            "VE_VENTILATION_SEQUENCE_BINDING_NOT_IMPLEMENTED",
            "The official staged ventilation, heat-recovery and overflow "
            "sequence is not yet bound to a tested VE mutation strategy.",
        ),
        "7": (
            "VE_ENERGY_SYSTEM_BINDING_NOT_IMPLEMENTED",
            "The official emission, distribution, storage and generation chain "
            "is not yet bound to a tested VE plant/energy-system mutation "
            "strategy.",
        ),
    }
    return blockers[test_id]


def get_case_capability(variant: str, case_id: str) -> Sia4010CaseCapability:
    """Return the registered capability for one exact variant/case pair."""

    cases = TEST_CASES.get(variant)
    if cases is None or case_id not in cases:
        raise ConfigurationError(
            "Unknown SIA 4010 variant/case combination: {}/{}".format(
                variant, case_id
            )
        )
    test_id = base_test_id(variant)
    if variant == "test_1" and case_id == "600":
        return Sia4010CaseCapability(
            variant=variant,
            case_id=case_id,
            base_test_id=test_id,
            preparation_status=PREPARATION_READY,
            generation_status=GUARDED_MUTATION_READY,
            generator_id="case600_mvp_v1",
            blocker_code="",
            blocker_detail="",
            required_source_roles=(
                "test_specification",
                "evaluation_workbook",
            ),
        )
    if variant == "test_1" and case_id in TEST1_DIAGNOSTIC_CASES:
        return Sia4010CaseCapability(
            variant=variant,
            case_id=case_id,
            base_test_id=test_id,
            preparation_status=PREPARATION_READY,
            generation_status=RUNTIME_QUALIFICATION_READY,
            generator_id="test1_diagnostic_chain_probe_v1",
            blocker_code="VE_RUNTIME_QUALIFICATION_REQUIRED",
            blocker_detail=(
                "Diagnostic case of the Test 1 to Test 2 transition. The chain "
                "and every parameter it adds are frozen in "
                "refs/reference-data/test-1.diagnostics.ref.json, read from the "
                "official PDFs, and test1_diagnostic_bundle applies the four "
                "links cumulatively from that frozen reference. Run it only in "
                "a fresh saved disposable project; the generator remains "
                "unverified until every VE setter, read-back and post-mutation "
                "check passes. The specification requires annual data sets with "
                "hourly heating and cooling power for these cases and states NO "
                "comparison criterion, so no reference band exists and none may "
                "be invented: they are deliverables, not judged cases."
            ),
            required_source_roles=(
                "test_specification",
                "evaluation_workbook",
            ),
        )
    if variant == "test_1" and case_id in {
        "640",
        "600FF",
        "900",
        "940",
        "900FF",
    }:
        mass = "high-mass" if case_id in {"900", "940", "900FF"} else "lightweight"
        return Sia4010CaseCapability(
            variant=variant,
            case_id=case_id,
            base_test_id=test_id,
            preparation_status=PREPARATION_READY,
            generation_status=RUNTIME_QUALIFICATION_READY,
            generator_id=(
                "test1_heavyweight_runtime_probe_v1"
                if mass == "high-mass"
                else "test1_lightweight_runtime_probe_v1"
            ),
            blocker_code="VE_RUNTIME_QUALIFICATION_REQUIRED",
            blocker_detail=(
                "A source-traced {} Test 1 bundle and guarded VE "
                "qualification path are implemented. Run it only in a fresh "
                "saved disposable project; the generator remains unverified "
                "until every VE setter/read-back and post-mutation check passes."
            ).format(mass),
            required_source_roles=(
                "test_specification",
                "evaluation_workbook",
            ),
        )
    blocker_code, blocker_detail = _blocker_for_test(test_id)
    roles = ["test_specification", "evaluation_workbook"]
    if test_id in {"4", "5", "6", "7"}:
        roles.extend(
            ("example_building_documentation", "example_building_ifc")
        )
    if test_id == "7":
        roles.extend(("load_profile", "reference_document"))
    return Sia4010CaseCapability(
        variant=variant,
        case_id=case_id,
        base_test_id=test_id,
        preparation_status=PREPARATION_READY,
        generation_status="NOT_IMPLEMENTED",
        generator_id="source_traced_preparation_v1",
        blocker_code=blocker_code,
        blocker_detail=blocker_detail,
        required_source_roles=tuple(roles),
    )


def all_case_capabilities() -> Tuple[Sia4010CaseCapability, ...]:
    """Return deterministic capability records for every registered case."""

    return tuple(
        get_case_capability(variant, case_id)
        for variant, case_ids in TEST_CASES.items()
        for case_id in case_ids
    )
