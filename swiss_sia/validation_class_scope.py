"""Derive the SIA 4010 validation-class scope required by an analysed VE model.

A client asks two different questions:

1. Is my model compliant with SIA 380/2? (the SIA 380/2 checker answers this)
2. Is the simulation tool validated for the kind of analysis my model needs?

SIA 4010 answers the second question through validation classes, each covering a
fixed set of official tests. This module maps the features actually present in
the analysed model to the official test families they rely on, and then to the
least-demanding validation class that covers them.

Traceability and conservatism:

- The feature -> test mapping uses the official test scope already encoded in
  ``SIA4010_VALIDATION_TESTS``; the test -> class mapping uses
  ``SIA4010_TEST_CLASS_COVERAGE``. No class membership is invented here.
- A feature that cannot be determined from the extracted model is reported as
  ``UNDETERMINED`` and is never silently treated as absent, because omitting a
  feature would understate the required class. Two results are therefore
  reported: the class required by confirmed features, and the conservative
  class that also covers every undetermined feature.
- This module states which class the analysis *requires*. It never asserts that
  the tool holds that class; official class validation still requires recorded
  official results and SIA sub-commission attestation.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .config import (
    SIA4010_CLASS_TEST_MATRIX,
    SIA4010_TEST_CLASS_COVERAGE,
    SIA4010_VALIDATION_TESTS,
)
from .model_analyzer import RoomData, has_active_solar_protection

# Detection outcomes for one model feature.
PRESENT = "PRESENT"
ABSENT = "ABSENT"
UNDETERMINED = "UNDETERMINED"

# Every thermal model exercises the envelope, so Test 1 is always required.
_ALWAYS_REQUIRED_TESTS = ("test_1",)


@dataclass(frozen=True)
class FeatureFinding:
    """One detected model feature and the official test family it relies on."""

    feature_id: str
    label: str
    state: str
    test_family: str
    test_scope: str
    evidence: str

    def to_dict(self) -> Dict[str, Any]:
        """Return the finding as serializable data."""

        return {
            "feature_id": self.feature_id,
            "label": self.label,
            "state": self.state,
            "test_family": self.test_family,
            "test_scope": self.test_scope,
            "evidence": self.evidence,
        }


@dataclass(frozen=True)
class ValidationClassScope:
    """Validation-class scope required by the analysed model."""

    status: str
    required_class: Optional[str]
    conservative_class: Optional[str]
    required_tests: Tuple[str, ...]
    undetermined_tests: Tuple[str, ...]
    findings: Tuple[FeatureFinding, ...] = ()
    notes: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        """Return the scope as serializable data."""

        return {
            "status": self.status,
            "required_class": self.required_class,
            "conservative_class": self.conservative_class,
            "required_tests": list(self.required_tests),
            "undetermined_tests": list(self.undetermined_tests),
            "findings": [finding.to_dict() for finding in self.findings],
            "notes": list(self.notes),
        }


def _text(value: Any) -> str:
    """Return a trimmed lower-case string form of a value."""

    return str(value).strip().lower() if value is not None else ""


def _has_meaningful_text(value: Any) -> bool:
    """Return whether a field carries a real identifier rather than a blank/none."""

    text = _text(value)
    return bool(text) and text not in {"none", "no", "0", "false", "-", "n/a", "na"}


def _detect_solar_protection(rooms: Sequence[RoomData]) -> Tuple[str, str]:
    """Return the solar-protection state and its evidence across all openings."""

    external_openings = [
        opening
        for room in rooms
        for opening in (room.openings or [])
        if getattr(opening, "is_external", False)
    ]
    if not external_openings:
        return UNDETERMINED, "No external opening was extracted"
    # `has_active_solar_protection` is the single product-wide authority on what
    # counts as an active device (an explicit zero activation field is inactive),
    # so this detector does not re-decide that question.
    active = [
        opening for opening in external_openings if has_active_solar_protection(opening)
    ]
    if active:
        return PRESENT, "{} of {} external openings expose an active device".format(
            len(active), len(external_openings)
        )
    return ABSENT, "No external opening exposes an active solar-protection device"


def _detect_daylight_lighting_control(rooms: Sequence[RoomData]) -> Tuple[str, str]:
    """Return the daylight-linked lighting-control state and its evidence."""

    controlled = [
        room for room in rooms if _has_meaningful_text(room.daylight_dimming_profile)
    ]
    if controlled:
        return PRESENT, "{} rooms expose a daylight-dimming profile".format(len(controlled))
    lit = [room for room in rooms if room.internal_gains.get("lighting") is not None]
    if not lit:
        return UNDETERMINED, "No lighting gain was extracted, so control cannot be ruled out"
    return ABSENT, "No room exposes a daylight-dimming profile"


def _detect_mechanical_ventilation(rooms: Sequence[RoomData]) -> Tuple[str, str]:
    """Return the mechanical-ventilation state and its evidence."""

    mechanical = [
        room
        for room in rooms
        if _has_meaningful_text(room.ventilation_installation_type)
        or _has_meaningful_text(room.fan_control)
        or (room.ventilation_m3_h_m2 or 0) > 0
    ]
    if mechanical:
        return PRESENT, "{} rooms expose a mechanical ventilation installation".format(
            len(mechanical)
        )
    return UNDETERMINED, "No ventilation installation data was extracted"


def _detect_heat_recovery(rooms: Sequence[RoomData]) -> Tuple[str, str]:
    """Return the heat-recovery state and its evidence."""

    recovery = [room for room in rooms if _has_meaningful_text(room.heat_recovery_type)]
    if recovery:
        return PRESENT, "{} rooms expose a heat-recovery device".format(len(recovery))
    return ABSENT, "No room exposes a heat-recovery device"


def _detect_generation_plant(rooms: Sequence[RoomData]) -> Tuple[str, str]:
    """Return the heating/cooling generation state and its evidence."""

    with_systems = [room for room in rooms if room.hvac_systems]
    if not with_systems:
        return UNDETERMINED, "No HVAC system was extracted"
    generators = [
        room
        for room in with_systems
        if any(
            _has_meaningful_text(system.get(key))
            for system in room.hvac_systems
            for key in (
                "heating_generator_class",
                "cooling_generator_class",
                "heating_capacity_kw",
                "cooling_capacity_kw",
            )
        )
    ]
    if generators:
        return PRESENT, "{} rooms expose a heating/cooling generator".format(
            len(generators)
        )
    return UNDETERMINED, "HVAC systems are present but expose no generator classification"


# Feature -> official test family. The scope text comes from the encoded
# official test descriptions, so the justification stays source-traced.
_FEATURE_TESTS: Tuple[Tuple[str, str, str, Any], ...] = (
    ("solar_protection", "Solar protection / shading control", "test_2", _detect_solar_protection),
    ("lighting_control", "Daylight-linked lighting control", "test_3", _detect_daylight_lighting_control),
    ("mechanical_ventilation", "Mechanical ventilation / AHU", "test_6", _detect_mechanical_ventilation),
    ("heat_recovery", "Ventilation heat recovery", "test_6", _detect_heat_recovery),
    ("generation_plant", "Heating/cooling generation", "test_7", _detect_generation_plant),
)


def _classes_covering(test_families: Sequence[str]) -> List[str]:
    """Return every validation class whose coverage includes all given families."""

    candidates: Optional[set] = None
    for family in test_families:
        covering = set(SIA4010_TEST_CLASS_COVERAGE.get(family, ()) or ())
        candidates = covering if candidates is None else (candidates & covering)
        if not candidates:
            return []
    return sorted(candidates or [])


def _least_demanding(classes: Sequence[str]) -> Optional[str]:
    """Return the class requiring the fewest official tests (deterministic tie-break)."""

    if not classes:
        return None
    return min(
        classes,
        key=lambda class_id: (len(SIA4010_CLASS_TEST_MATRIX.get(class_id, ())), class_id),
    )


def derive_validation_class_scope(
    rooms_data: Optional[Sequence[RoomData]],
) -> ValidationClassScope:
    """Return the SIA 4010 validation-class scope the analysed model relies on.

    ``required_class`` covers the features confirmed present; when a feature
    cannot be determined, ``conservative_class`` also covers it, so the reader
    never under-reads the validation the analysis depends on.
    """

    rooms = list(rooms_data or [])
    if not rooms:
        return ValidationClassScope(
            status="NOT_CHECKABLE",
            required_class=None,
            conservative_class=None,
            required_tests=(),
            undetermined_tests=(),
            notes=(
                "No usable VE thermal room was analysed, so the required "
                "validation class cannot be derived.",
            ),
        )

    findings: List[FeatureFinding] = []
    confirmed: List[str] = list(_ALWAYS_REQUIRED_TESTS)
    undetermined: List[str] = []
    for feature_id, label, family, detector in _FEATURE_TESTS:
        state, evidence = detector(rooms)
        findings.append(
            FeatureFinding(
                feature_id=feature_id,
                label=label,
                state=state,
                test_family=family,
                test_scope=SIA4010_VALIDATION_TESTS.get(family, ""),
                evidence=evidence,
            )
        )
        if state == PRESENT and family not in confirmed:
            confirmed.append(family)
        elif state == UNDETERMINED and family not in undetermined:
            undetermined.append(family)

    undetermined = [family for family in undetermined if family not in confirmed]
    required_class = _least_demanding(_classes_covering(confirmed))
    conservative_class = _least_demanding(
        _classes_covering(list(confirmed) + list(undetermined))
    )

    notes: List[str] = [
        "The required class states which SIA 4010 validation the analysis relies "
        "on. It does not assert that the tool holds that class; official class "
        "validation still requires recorded official results and SIA "
        "sub-commission attestation.",
    ]
    status = "DERIVED"
    if required_class is None:
        status = "NO_SINGLE_CLASS_COVERS"
        notes.append(
            "No single SIA 4010 validation class covers every required test "
            "family; the analysis spans more than one class."
        )
    if undetermined:
        notes.append(
            "Undetermined features were kept in the conservative class rather "
            "than assumed absent: {}.".format(", ".join(sorted(undetermined)))
        )
    return ValidationClassScope(
        status=status,
        required_class=required_class,
        conservative_class=conservative_class,
        required_tests=tuple(confirmed),
        undetermined_tests=tuple(undetermined),
        findings=tuple(findings),
        notes=tuple(notes),
    )
