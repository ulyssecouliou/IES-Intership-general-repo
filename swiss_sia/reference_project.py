"""Build the SIA 380/2 reference-project input specification from a VE model.

A complete SIA 380/2 conclusion compares the project's calculated demand with
the demand of the *reference project*: the same building, with the normative
reference values substituted for the envelope and system inputs. The component
checks alone are diagnostics, so this comparison is the decisive gate.

This module produces the deterministic **input specification** for that
reference run: for every construction the model actually uses, it states the
project value, the normative reference value with its SIA locator, and whether
the substitution is resolvable. It does not simulate anything and it never
produces a demand figure - the reference demand still requires a VE/ApacheSim
run of the substituted model, and the accepted comparison still requires the
reviewer gate in ``evidence_manager``.

Conservatism: a construction whose project value cannot be extracted is a
blocker, never silently substituted; a surface the model does not classify is
reported as unclassified rather than mapped to a guessed reference value. Every
reference value is read from the encoded, source-traced SIA tables - none is
computed or interpolated here.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .config import SIA3802_LIMIT_VALUES, SIA3802_SOURCE_REFERENCES
from .model_analyzer import RoomData

# Normalized surface type -> reference parameter key in SIA3802_LIMIT_VALUES.
# Only externally-exposed opaque types are substituted here; internal
# partitions depend on adjacency evidence the checker treats separately.
_SURFACE_PARAMETERS: Dict[str, str] = {
    "wall": "external_wall_u",
    "roof": "flat_roof_u",
    "floor": "ground_floor_u",
}
_SURFACE_SOURCE_KEY = "table_3"

# Opening parameter -> (reference key, attribute on OpeningData, unit).
_OPENING_PARAMETERS: Tuple[Tuple[str, str, str], ...] = (
    ("window_u", "u_value", "W/(m2K)"),
    ("window_frame_fraction", "frame_fraction", "-"),
)
_OPENING_SOURCE_KEY = "table_2"

SUBSTITUTABLE = "SUBSTITUTABLE"
PROJECT_VALUE_MISSING = "PROJECT_VALUE_MISSING"
UNCLASSIFIED = "UNCLASSIFIED"


@dataclass(frozen=True)
class ReferenceSubstitution:
    """One normative substitution to apply when building the reference project."""

    parameter: str
    scope: str
    element_type: str
    project_value: Optional[float]
    reference_value: Optional[float]
    unit: str
    source: str
    status: str
    affected_elements: int

    def to_dict(self) -> Dict[str, Any]:
        """Return the substitution as serializable data."""

        return {
            "parameter": self.parameter,
            "scope": self.scope,
            "element_type": self.element_type,
            "project_value": self.project_value,
            "reference_value": self.reference_value,
            "unit": self.unit,
            "source": self.source,
            "status": self.status,
            "affected_elements": self.affected_elements,
        }


@dataclass(frozen=True)
class ReferenceProjectSpecification:
    """Deterministic input set for the SIA 380/2 reference-project run."""

    status: str
    substitutions: Tuple[ReferenceSubstitution, ...]
    blockers: Tuple[str, ...]
    notes: Tuple[str, ...]

    @property
    def is_complete(self) -> bool:
        """Return whether every required substitution is resolvable."""

        return self.status == "READY_FOR_REFERENCE_RUN"

    def to_dict(self) -> Dict[str, Any]:
        """Return the specification as serializable data."""

        return {
            "status": self.status,
            "substitutions": [item.to_dict() for item in self.substitutions],
            "blockers": list(self.blockers),
            "notes": list(self.notes),
            "is_complete": self.is_complete,
        }


def _source(key: str) -> str:
    """Return the SIA locator recorded for one source-reference key."""

    return str(SIA3802_SOURCE_REFERENCES.get(key, "")) or "SIA 380/2:2022"


def _float_or_none(value: Any) -> Optional[float]:
    """Return a float when the value is a real number, otherwise None."""

    if isinstance(value, bool) or value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _construction_scope(construction_ids: Any, fallback: str) -> str:
    """Return a stable construction label used to group substitutions."""

    if isinstance(construction_ids, (list, tuple, set)):
        labels = sorted(str(item).strip() for item in construction_ids if str(item).strip())
        if labels:
            return ", ".join(labels)
    text = str(construction_ids or "").strip()
    return text or fallback


def _normalize_surface_type(model_analyzer: Any, surface: Any) -> str:
    """Normalize a surface type, reusing the analyzer's own classification."""

    normalizer = getattr(model_analyzer, "_normalize_surface_type", None)
    if callable(normalizer):
        return normalizer(getattr(surface, "surface_type", ""))
    return str(getattr(surface, "surface_type", "") or "").strip().lower()


def _collect_surface_substitutions(
    rooms: Sequence[RoomData], model_analyzer: Any
) -> Tuple[List[ReferenceSubstitution], List[str]]:
    """Group external opaque surfaces by construction and pair them with Table 3."""

    # scope -> {parameter, values, count, unclassified}
    grouped: Dict[Tuple[str, str], Dict[str, Any]] = {}
    unclassified: Dict[str, int] = {}
    for room in rooms:
        for surface in room.surfaces or []:
            if not getattr(surface, "is_external", False):
                continue
            if _float_or_none(getattr(surface, "net_area", surface.area)) in (None, 0.0):
                continue
            surface_type = _normalize_surface_type(model_analyzer, surface)
            parameter = _SURFACE_PARAMETERS.get(surface_type)
            scope = _construction_scope(
                getattr(surface, "construction_ids", None),
                getattr(surface, "name", "") or getattr(surface, "id", "") or "unnamed",
            )
            if parameter is None:
                unclassified[scope] = unclassified.get(scope, 0) + 1
                continue
            entry = grouped.setdefault(
                (scope, parameter),
                {"values": [], "count": 0, "element_type": surface_type},
            )
            entry["count"] += 1
            value = _float_or_none(getattr(surface, "u_value", None))
            if value is not None:
                entry["values"].append(value)

    substitutions: List[ReferenceSubstitution] = []
    blockers: List[str] = []
    for (scope, parameter), entry in sorted(grouped.items()):
        values = entry["values"]
        # A construction must expose one consistent project value; the maximum
        # is reported when VE returns per-surface variations, and the spread is
        # never averaged away silently.
        project_value = max(values) if values else None
        status = SUBSTITUTABLE if project_value is not None else PROJECT_VALUE_MISSING
        if status == PROJECT_VALUE_MISSING:
            blockers.append(
                "No project U-value could be extracted for {} ({} surfaces)".format(
                    scope, entry["count"]
                )
            )
        substitutions.append(
            ReferenceSubstitution(
                parameter=parameter,
                scope=scope,
                element_type=entry["element_type"],
                project_value=project_value,
                reference_value=_float_or_none(SIA3802_LIMIT_VALUES.get(parameter)),
                unit="W/(m2K)",
                source=_source(_SURFACE_SOURCE_KEY),
                status=status,
                affected_elements=entry["count"],
            )
        )
    for scope, count in sorted(unclassified.items()):
        substitutions.append(
            ReferenceSubstitution(
                parameter="unclassified_external_surface",
                scope=scope,
                element_type="unclassified",
                project_value=None,
                reference_value=None,
                unit="",
                source=_source(_SURFACE_SOURCE_KEY),
                status=UNCLASSIFIED,
                affected_elements=count,
            )
        )
        blockers.append(
            "{} external surfaces of {} are not classified as wall/roof/floor".format(
                count, scope
            )
        )
    return substitutions, blockers


def _collect_opening_substitutions(
    rooms: Sequence[RoomData],
) -> Tuple[List[ReferenceSubstitution], List[str]]:
    """Group external openings by construction and pair them with Table 2."""

    grouped: Dict[Tuple[str, str], Dict[str, Any]] = {}
    for room in rooms:
        for opening in room.openings or []:
            if not getattr(opening, "is_external", False):
                continue
            scope = _construction_scope(
                getattr(opening, "construction_id", None),
                getattr(opening, "name", "") or getattr(opening, "id", "") or "unnamed",
            )
            for parameter, attribute, unit in _OPENING_PARAMETERS:
                entry = grouped.setdefault(
                    (scope, parameter),
                    {"values": [], "count": 0, "unit": unit},
                )
                entry["count"] += 1
                value = _float_or_none(getattr(opening, attribute, None))
                if value is not None:
                    entry["values"].append(value)

    substitutions: List[ReferenceSubstitution] = []
    blockers: List[str] = []
    for (scope, parameter), entry in sorted(grouped.items()):
        values = entry["values"]
        project_value = max(values) if values else None
        status = SUBSTITUTABLE if project_value is not None else PROJECT_VALUE_MISSING
        if status == PROJECT_VALUE_MISSING:
            blockers.append(
                "No project {} could be extracted for glazing {} ({} openings)".format(
                    parameter, scope, entry["count"]
                )
            )
        substitutions.append(
            ReferenceSubstitution(
                parameter=parameter,
                scope=scope,
                element_type="opening",
                project_value=project_value,
                reference_value=_float_or_none(SIA3802_LIMIT_VALUES.get(parameter)),
                unit=entry["unit"],
                source=_source(_OPENING_SOURCE_KEY),
                status=status,
                affected_elements=entry["count"],
            )
        )
    return substitutions, blockers


def build_reference_project_specification(
    rooms_data: Optional[Sequence[RoomData]],
    model_analyzer: Any = None,
) -> ReferenceProjectSpecification:
    """Return the reference-project input specification for an analysed model.

    ``READY_FOR_REFERENCE_RUN`` means every construction the model uses has both
    a project value and a normative reference value, so the reference variant
    can be built deterministically. It does not mean the comparison is done: the
    reference demand still requires a VE run, and the accepted project/reference
    result still requires the reviewer gate.
    """

    rooms = list(rooms_data or [])
    if not rooms:
        return ReferenceProjectSpecification(
            status="NOT_CHECKABLE",
            substitutions=(),
            blockers=("No usable VE thermal room was analysed.",),
            notes=(
                "The SIA 380/2 reference-project comparison cannot be prepared "
                "without an extracted model.",
            ),
        )

    surface_items, surface_blockers = _collect_surface_substitutions(rooms, model_analyzer)
    opening_items, opening_blockers = _collect_opening_substitutions(rooms)
    substitutions = tuple(surface_items + opening_items)
    blockers = tuple(surface_blockers + opening_blockers)

    missing_reference = [
        item.parameter
        for item in substitutions
        if item.status == SUBSTITUTABLE and item.reference_value is None
    ]
    blockers = blockers + tuple(
        "No encoded SIA reference value for {}".format(parameter)
        for parameter in sorted(set(missing_reference))
    )

    notes = [
        "Reference values are read from the encoded SIA 380/2 tables with their "
        "locators; none is computed or interpolated here.",
        "This specification prepares the reference run. It is not a compliance "
        "conclusion: the reference demand requires a VE/ApacheSim run, and the "
        "project/reference comparison still requires reviewer acceptance.",
    ]
    if not substitutions:
        status = "NOT_CHECKABLE"
        blockers = blockers + (
            "No external surface or opening was available for substitution.",
        )
    elif blockers:
        status = "BLOCKED_INCOMPLETE_INPUTS"
    else:
        status = "READY_FOR_REFERENCE_RUN"
    return ReferenceProjectSpecification(
        status=status,
        substitutions=substitutions,
        blockers=blockers,
        notes=tuple(notes),
    )
