"""Standalone binder for ``str`` -> ``VECdbConstruction`` resolution.

Boost.Python setters on VE 2025 accept a ``VECdbConstruction`` object where the
caller often has only its string identifier.  Passing the raw ``str`` yields
``Boost.Python.ArgumentError`` from the setter, well after any preflight
capability check has passed.  This module isolates the resolution so the same
tolerant lookup can be used by launchers, provisioners and probes without
duplicating a private helper.

The binder:

* tolerates VE builds exposing ``get_construction(id)`` and those exposing
  ``get_construction(id, construction_class)``;
* fails closed with a machine-readable status when no known signature returns
  a construction;
* never guesses a construction class value -- it reads ``uvalue_types.iso``
  from the runtime and only falls back to the single-arg call when that
  member is unavailable.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Tuple


class BindStatus(Enum):
    """Three-state result for a binder lookup."""

    RESOLVED = "RESOLVED"
    NOT_FOUND = "NOT_FOUND"
    RUNTIME_UNAVAILABLE = "RUNTIME_UNAVAILABLE"


@dataclass(frozen=True)
class BindResult:
    """Outcome of one binder resolution attempt.

    ``construction`` is the resolved VE object (opaque) or ``None`` on failure.
    ``last_exception_repr`` records the string form of the last exception seen
    while trying documented signature variants; it is deliberately a string so
    consumers can log it without leaking VE runtime types.
    """

    status: BindStatus
    construction: Optional[Any]
    signatures_tried: Tuple[str, ...]
    last_exception_repr: Optional[str]
    identifier: str


class ConstructionBinder:
    """Resolve a construction identifier to a live VE ``VECdbConstruction``.

    The binder does **not** cache resolutions: each call is a fresh lookup so
    downstream mutations always see the current CDB state.  Callers that need
    to cache should do so explicitly with an explicit invalidation policy.
    """

    def __init__(self, iesve_module: Any, cdb_project: Any):
        self._iesve = iesve_module
        self._cdb_project = cdb_project

    # ------------------------------------------------------------------ utils

    def _iso_construction_class(self) -> Optional[Any]:
        """Return the ``uvalue_types.iso`` member if the runtime exposes it."""

        uvalue_types = getattr(self._cdb_project, "uvalue_types", None)
        if uvalue_types is None:
            uvalue_types = getattr(self._iesve, "uvalue_types", None)
        if uvalue_types is None:
            return None
        return getattr(uvalue_types, "iso", None)

    # ------------------------------------------------------------------ api

    def resolve(self, construction_id: str) -> BindResult:
        """Look up one construction, tolerating both documented signatures.

        Returns a ``BindResult``; never raises for VE-side signature drift.
        Only raises ``TypeError`` when the caller passes something that is not
        a ``str`` since that is a caller bug, not a runtime condition.
        """

        if not isinstance(construction_id, str):
            raise TypeError(
                "construction_id must be a str; got {}".format(
                    type(construction_id).__name__
                )
            )
        if self._cdb_project is None:
            return BindResult(
                status=BindStatus.RUNTIME_UNAVAILABLE,
                construction=None,
                signatures_tried=(),
                last_exception_repr="cdb_project is None",
                identifier=construction_id,
            )
        if not hasattr(self._cdb_project, "get_construction"):
            return BindResult(
                status=BindStatus.RUNTIME_UNAVAILABLE,
                construction=None,
                signatures_tried=(),
                last_exception_repr="get_construction attribute missing",
                identifier=construction_id,
            )

        attempts = []
        iso = self._iso_construction_class()
        if iso is not None:
            attempts.append(
                ("get_construction(id, construction_class)", (construction_id, iso))
            )
        attempts.append(("get_construction(id)", (construction_id,)))

        tried_labels = []
        last_exc: Optional[str] = None
        for label, args in attempts:
            tried_labels.append(label)
            try:
                construction = self._cdb_project.get_construction(*args)
            except Exception as exc:
                last_exc = repr(exc)
                continue
            if construction is not None:
                return BindResult(
                    status=BindStatus.RESOLVED,
                    construction=construction,
                    signatures_tried=tuple(tried_labels),
                    last_exception_repr=None,
                    identifier=construction_id,
                )
        return BindResult(
            status=BindStatus.NOT_FOUND,
            construction=None,
            signatures_tried=tuple(tried_labels),
            last_exception_repr=last_exc,
            identifier=construction_id,
        )

    def resolve_or_raise(self, construction_id: str) -> Any:
        """Convenience wrapper: return the object or raise ``LookupError``."""

        result = self.resolve(construction_id)
        if result.status is BindStatus.RESOLVED:
            return result.construction
        raise LookupError(
            "Cannot resolve construction '{}': status={}, tried={}, last_exception={}".format(
                construction_id,
                result.status.value,
                result.signatures_tried,
                result.last_exception_repr,
            )
        )


__all__ = ["BindStatus", "BindResult", "ConstructionBinder"]
