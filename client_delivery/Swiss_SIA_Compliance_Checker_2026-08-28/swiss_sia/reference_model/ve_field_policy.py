"""Centralised read-back / normalisation / capability policy for VE mutations.

This module gathers the field-level canonicalisation rules that are today
scattered across ``ve_asset_provisioner.py`` (materials, layers, constructions,
gains, air-exchanges) and adds a formal option-filter contract so unknown
keys never reach ``set()`` blindly.

Design constraints:

* Pure Python -- no ``iesve`` import, no I/O, no logging side-effects.
* No global permissive tolerance: every allowed float divergence is bound to
  a specific documented VE canonicalisation and produces an auditable warning
  carrying the requested and observed values.
* Every exposed function is a stateless mapping ``expected + actual -> verdict``
  so callers keep full control over side-effects (logging, ledger writes,
  UI notification).
* The audit codes intentionally mirror the strings already emitted by
  ``IesVeAssetProvisioner`` so consumers can wire this module in progressively
  without changing downstream evidence formats.

The policy does not run compliance checks. It only guards the mutation/read-back
loop against known VE storage quirks.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import (
    Any,
    Dict,
    FrozenSet,
    Iterable,
    List,
    Mapping,
    Optional,
    Tuple,
)

# ---------------------------------------------------------------------------
# Tolerances (IEEE-754 float32 round-trip only; NOT a compliance tolerance)
# ---------------------------------------------------------------------------

VE_FLOAT32_RELATIVE_TOLERANCE = 1.0e-7
VE_FLOAT32_ABSOLUTE_TOLERANCE = 1.0e-9

# VE 2025 numerical floor observed on thermal-mass properties written as 0.
VE_THERMAL_MASS_MINIMUM = 1.0e-6


# ---------------------------------------------------------------------------
# Audit codes (mirrors ve_asset_provisioner; central source of truth)
# ---------------------------------------------------------------------------

CODE_MATERIAL_ZERO_THERMAL_MASS_MINIMUM = "VE-MATERIAL-ZERO-THERMAL-MASS-MINIMUM"
CODE_GLASS_OPTICAL_PROPERTY_ROUNDED_3DP = "VE-GLASS-OPTICAL-PROPERTY-ROUNDED-3DP"
CODE_GLAZED_CONSTRUCTION_VLT_ROUNDED_4DP = "VE-GLAZED-CONSTRUCTION-VLT-ROUNDED-4DP"
CODE_CONSTRUCTION_SURFACE_RESISTANCE_ROUNDED_4DP = (
    "VE-CONSTRUCTION-SURFACE-RESISTANCE-ROUNDED-4DP"
)
CODE_GLAZED_LAYER_RESISTANCE_ROUNDED_5DP = "VE-GLAZED-LAYER-RESISTANCE-ROUNDED-5DP"
CODE_GLAZED_LAYER_THICKNESS_NOT_PERSISTED = "VE-GLAZED-LAYER-THICKNESS-NOT-PERSISTED"
CODE_ZERO_GAIN_PROFILE_CANONICALIZED_ON = "VE-ZERO-GAIN-PROFILE-CANONICALIZED-ON"
CODE_CONSTANT_ONE_PROFILE_CANONICALIZED_ON = "VE-CONSTANT-ONE-PROFILE-CANONICALIZED-ON"
CODE_ZERO_AIR_FLOW_PROFILE_CANONICALIZED_ON = "VE-ZERO-AIR-FLOW-PROFILE-CANONICALIZED-ON"
CODE_ROOM_CONDITION_AUDIT_ONLY = "VE-ROOM-CONDITION-AUDIT-ONLY"
CODE_OPTION_NOT_EXPOSED = "VE-OPTION-NOT-EXPOSED"
CODE_OPTION_REQUIRED_MISSING = "VE-OPTION-REQUIRED-MISSING"


# ---------------------------------------------------------------------------
# Verdict types
# ---------------------------------------------------------------------------


class ReadbackStatus(Enum):
    """Three-state outcome for a single VE read-back or option-filter step."""

    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


@dataclass(frozen=True)
class ReadbackVerdict:
    """Result of comparing expected vs. actual after policy rules apply.

    ``mismatches`` is only populated on ``FAIL``. ``warnings`` is a tuple of
    dicts using the ``code``/``message`` shape already emitted by
    ``IesVeAssetProvisioner._compatibility_warnings``.
    """

    status: ReadbackStatus
    context: str
    warnings: Tuple[Dict[str, Any], ...] = ()
    mismatches: Dict[str, Dict[str, Any]] = field(default_factory=dict)


@dataclass(frozen=True)
class OptionFilterResult:
    """Partition of a payload after capability-based filtering.

    ``writable`` is the only subset that should be handed to ``set()``.
    ``audit_only`` stays in the manifest as source-traced context but must
    never leave this module toward the VE writer.  ``dropped_unknown`` records
    keys the runtime does not expose; they yield ``WARNING`` warnings unless
    listed in ``required_keys`` in which case ``missing_required`` fires and
    the caller must fail closed BEFORE any mutation.
    """

    writable: Dict[str, Any]
    audit_only: Dict[str, Any]
    dropped_unknown: Dict[str, Any]
    missing_required: Tuple[str, ...]
    warnings: Tuple[Dict[str, Any], ...] = ()

    @property
    def status(self) -> ReadbackStatus:
        if self.missing_required:
            return ReadbackStatus.FAIL
        if self.dropped_unknown or self.audit_only:
            return ReadbackStatus.WARNING
        return ReadbackStatus.PASS


# ---------------------------------------------------------------------------
# Numeric helpers (mirrors ve_asset_provisioner private helpers)
# ---------------------------------------------------------------------------


def serializable(value: Any) -> Any:
    """Normalise VE enum/container values into plain JSON-compatible form."""

    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        return {str(key): serializable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serializable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def values_match(
    expected: Any,
    actual: Any,
    rel_tol: float = VE_FLOAT32_RELATIVE_TOLERANCE,
    abs_tol: float = VE_FLOAT32_ABSOLUTE_TOLERANCE,
) -> bool:
    """Compare after a non-regulatory float32 storage round trip only."""

    expected = serializable(expected)
    actual = serializable(actual)
    if isinstance(expected, bool) or isinstance(actual, bool):
        return expected == actual
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return math.isclose(
            float(expected), float(actual), rel_tol=rel_tol, abs_tol=abs_tol
        )
    if isinstance(expected, list) and isinstance(actual, list):
        return len(expected) == len(actual) and all(
            values_match(left, right, rel_tol=rel_tol, abs_tol=abs_tol)
            for left, right in zip(expected, actual)
        )
    if isinstance(expected, Mapping) and isinstance(actual, Mapping):
        return all(
            key in actual
            and values_match(value, actual[key], rel_tol=rel_tol, abs_tol=abs_tol)
            for key, value in expected.items()
        )
    return expected == actual


def _diff(
    expected: Mapping[str, Any], actual: Mapping[str, Any]
) -> Dict[str, Dict[str, Any]]:
    """Return per-key mismatch report for a subset comparison."""

    return {
        key: {
            "expected": serializable(value),
            "actual": serializable(actual.get(key)) if key in actual else None,
            "present_in_actual": key in actual,
        }
        for key, value in expected.items()
        if key not in actual or not values_match(value, actual.get(key))
    }


# ---------------------------------------------------------------------------
# Per-asset canonicalisation rules
# ---------------------------------------------------------------------------


def apply_material_readback_rules(
    category: str,
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Peel VE-specific canonicalisations off a material readback.

    Returns a residual expected mapping that must still match ``actual``
    exactly, plus the list of warnings the caller must persist.  Applies:

    * ``VE-MATERIAL-ZERO-THERMAL-MASS-MINIMUM`` on ``density`` and
      ``specific_heat_capacity`` when the request is exactly zero and VE
      persists ``1e-6``.
    * ``VE-GLASS-OPTICAL-PROPERTY-ROUNDED-3DP`` on glass ``transmittance``
      / ``visible_transmittance`` when VE returns the 3-decimal rounded form.
    """

    residual = dict(expected)
    warnings: List[Dict[str, Any]] = []

    minimum_fields: Dict[str, Dict[str, Any]] = {}
    for key in ("density", "specific_heat_capacity"):
        requested = residual.get(key)
        persisted = actual.get(key)
        if (
            isinstance(requested, (int, float))
            and float(requested) == 0.0
            and isinstance(persisted, (int, float))
            and values_match(VE_THERMAL_MASS_MINIMUM, float(persisted))
        ):
            residual.pop(key)
            minimum_fields[key] = {
                "requested": 0.0,
                "ve_readback": float(persisted),
                "ve_minimum": VE_THERMAL_MASS_MINIMUM,
            }
    if minimum_fields:
        warnings.append(
            {
                "code": CODE_MATERIAL_ZERO_THERMAL_MASS_MINIMUM,
                "message": (
                    "VE persisted a source-traced zero thermal-mass material "
                    "property at its 1e-6 numerical minimum. The normative zero "
                    "remains in the manifest; only this exact VE canonical value "
                    "is accepted during read-back."
                ),
                "category": category,
                "fields": minimum_fields,
            }
        )

    if category == "glass":
        rounded_fields: Dict[str, Dict[str, Any]] = {}
        for key in ("transmittance", "visible_transmittance"):
            requested = residual.get(key)
            persisted = actual.get(key)
            if not isinstance(requested, (int, float)) or not isinstance(
                persisted, (int, float)
            ):
                continue
            canonical = round(float(requested), 3)
            if not values_match(float(requested), float(persisted)) and values_match(
                canonical, float(persisted)
            ):
                residual.pop(key)
                rounded_fields[key] = {
                    "requested": float(requested),
                    "ve_readback": float(persisted),
                    "canonical_3dp": canonical,
                }
        if rounded_fields:
            warnings.append(
                {
                    "code": CODE_GLASS_OPTICAL_PROPERTY_ROUNDED_3DP,
                    "message": (
                        "VE persisted glass optical material properties at "
                        "three decimal places. The source precision remains "
                        "in the asset manifest; downstream whole-window "
                        "g-value validation remains strict and independent."
                    ),
                    "fields": rounded_fields,
                }
            )
    return residual, warnings


def apply_layer_readback_rules(
    construction_class: str,
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Peel VE glazed-layer canonicalisations.

    On glazed layers only:

    * ``VE-GLAZED-LAYER-THICKNESS-NOT-PERSISTED`` when a positive requested
      thickness is stored as 0.0 after a persist/reopen cycle.
    * ``VE-GLAZED-LAYER-RESISTANCE-ROUNDED-5DP`` when VE returns the exact
      5-decimal rounded form of the requested resistance.
    """

    residual = dict(expected)
    warnings: List[Dict[str, Any]] = []
    if construction_class != "glazed":
        return residual, warnings

    expected_thickness = residual.get("thickness")
    actual_thickness = actual.get("thickness")
    if (
        isinstance(expected_thickness, (int, float))
        and float(expected_thickness) > 0.0
        and isinstance(actual_thickness, (int, float))
        and values_match(float(actual_thickness), 0.0)
    ):
        residual.pop("thickness")
        warnings.append(
            {
                "code": CODE_GLAZED_LAYER_THICKNESS_NOT_PERSISTED,
                "message": (
                    "VE returned 0.0 m after persisting the glazed-layer "
                    "thickness; the requested value remains source-traced in "
                    "the asset manifest, but whole-window thermal calibration "
                    "requires independent VE U-value verification before "
                    "certification."
                ),
                "requested_thickness_m": float(expected_thickness),
                "ve_readback_thickness_m": float(actual_thickness),
            }
        )

    expected_resistance = residual.get("resistance")
    actual_resistance = actual.get("resistance")
    if isinstance(expected_resistance, (int, float)) and isinstance(
        actual_resistance, (int, float)
    ):
        canonical = round(float(expected_resistance), 5)
        if not values_match(
            float(expected_resistance), float(actual_resistance)
        ) and values_match(canonical, float(actual_resistance)):
            residual.pop("resistance")
            warnings.append(
                {
                    "code": CODE_GLAZED_LAYER_RESISTANCE_ROUNDED_5DP,
                    "message": (
                        "VE persisted glazed-layer thermal resistance at "
                        "five decimal places. The source precision remains "
                        "in the asset manifest; whole-window U-value "
                        "validation remains strict and independent."
                    ),
                    "requested_resistance_m2k_w": float(expected_resistance),
                    "ve_readback_resistance_m2k_w": float(actual_resistance),
                    "canonical_5dp": canonical,
                }
            )
    return residual, warnings


def apply_construction_readback_rules(
    construction_class: str,
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Peel documented VE construction-property canonicalisations."""

    residual = dict(expected)
    warnings: List[Dict[str, Any]] = []

    rounded_surface_resistances: Dict[str, Dict[str, float]] = {}
    for key in ("inside_surface_resistance", "outside_surface_resistance"):
        requested = residual.get(key)
        persisted = actual.get(key)
        if not isinstance(requested, (int, float)) or not isinstance(
            persisted, (int, float)
        ):
            continue
        canonical = round(float(requested), 4)
        if not values_match(float(requested), float(persisted)) and values_match(
            canonical, float(persisted)
        ):
            residual.pop(key)
            rounded_surface_resistances[key] = {
                "requested": float(requested),
                "ve_readback": float(persisted),
                "canonical_4dp": canonical,
            }
    if rounded_surface_resistances:
        warnings.append(
            {
                "code": CODE_CONSTRUCTION_SURFACE_RESISTANCE_ROUNDED_4DP,
                "message": (
                    "VE persisted construction surface resistances at four "
                    "decimal places. The source precision remains in the "
                    "manifest; U-value checks remain strict."
                ),
                "fields": rounded_surface_resistances,
            }
        )

    if construction_class != "glazed":
        return residual, warnings

    for key in ("visible_light_transmittance",):
        requested = residual.get(key)
        persisted = actual.get(key)
        if not isinstance(requested, (int, float)) or not isinstance(
            persisted, (int, float)
        ):
            continue
        canonical = round(float(requested), 4)
        if not values_match(float(requested), float(persisted)) and values_match(
            canonical, float(persisted)
        ):
            residual.pop(key)
            warnings.append(
                {
                    "code": CODE_GLAZED_CONSTRUCTION_VLT_ROUNDED_4DP,
                    "message": (
                        "VE persisted glazed-construction visible-light "
                        "transmittance at four decimal places. Downstream "
                        "whole-window checks remain strict."
                    ),
                    "field": key,
                    "requested": float(requested),
                    "ve_readback": float(persisted),
                    "canonical_4dp": canonical,
                }
            )
    return residual, warnings


def _profile_would_be_neutralised(
    gain_category: str, expected: Mapping[str, Any]
) -> bool:
    """Return True when every magnitude in the payload is exactly zero."""

    if gain_category == "people":
        return values_match(expected.get("max_sensible_gain"), 0.0) and values_match(
            expected.get("max_latent_gain"), 0.0
        )
    if gain_category == "lighting":
        return values_match(expected.get("max_power_consumption"), 0.0)
    if gain_category == "energy":
        return (
            values_match(expected.get("max_power_consumption"), 0.0)
            and values_match(expected.get("max_sensible_gain"), 0.0)
            and values_match(expected.get("max_latent_gain"), 0.0)
        )
    return False


def apply_gain_readback_rules(
    category: str,
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
    constant_on_profile_ids: FrozenSet[str] = frozenset(),
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Peel the two ``variation_profile -> ON`` canonicalisations on gains.

    * ``VE-ZERO-GAIN-PROFILE-CANONICALIZED-ON`` -- when every gain magnitude
      is exactly zero, VE 2025 rewrites the schedule to ``ON``.  Accepted
      because the schedule is mathematically irrelevant.
    * ``VE-CONSTANT-ONE-PROFILE-CANONICALIZED-ON`` -- when the source-traced
      daily profile has every multiplier equal to 1.0, VE reads it back as
      ``ON``.  Accepted only when the profile id is explicitly declared in
      ``constant_on_profile_ids``.
    """

    residual = dict(actual)
    warnings: List[Dict[str, Any]] = []
    expected_profile = str(expected.get("variation_profile", "") or "")
    actual_profile = str(residual.get("variation_profile", "") or "")

    if (
        expected_profile
        and expected_profile != "ON"
        and actual_profile == "ON"
        and _profile_would_be_neutralised(category, expected)
    ):
        warnings.append(
            {
                "code": CODE_ZERO_GAIN_PROFILE_CANONICALIZED_ON,
                "message": (
                    "VE 2025 canonicalised the variation profile of a "
                    "strictly zero-valued gain to ON. The schedule is "
                    "mathematically irrelevant because every gain magnitude "
                    "is zero; non-zero gains remain subject to exact "
                    "profile verification."
                ),
                "requested_profile": expected_profile,
                "ve_readback": actual_profile,
                "category": category,
            }
        )
        residual["variation_profile"] = expected_profile
    elif (
        expected_profile
        and expected_profile != "ON"
        and actual_profile == "ON"
        and expected_profile in constant_on_profile_ids
    ):
        warnings.append(
            {
                "code": CODE_CONSTANT_ONE_PROFILE_CANONICALIZED_ON,
                "message": (
                    "VE 2025 returned ON for a source-traced daily profile "
                    "whose every multiplier is exactly 1.0. ON is "
                    "mathematically identical for this asset; non-constant "
                    "profiles remain subject to exact verification."
                ),
                "requested_profile": expected_profile,
                "ve_readback": actual_profile,
                "category": category,
            }
        )
        residual["variation_profile"] = expected_profile
    return residual, warnings


def apply_air_exchange_readback_rules(
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
    constant_on_profile_ids: FrozenSet[str] = frozenset(),
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    """Peel the two ``variation_profile -> ON`` canonicalisations on air exchanges."""

    residual = dict(actual)
    warnings: List[Dict[str, Any]] = []
    expected_profile = str(expected.get("variation_profile", "") or "")
    actual_profile = str(residual.get("variation_profile", "") or "")
    max_flow = expected.get("max_flow")
    is_zero_flow = (
        values_match(max_flow, 0.0) if isinstance(max_flow, (int, float)) else False
    )

    if (
        expected_profile
        and expected_profile != "ON"
        and actual_profile == "ON"
        and is_zero_flow
    ):
        warnings.append(
            {
                "code": CODE_ZERO_AIR_FLOW_PROFILE_CANONICALIZED_ON,
                "message": (
                    "VE 2025 canonicalised the variation profile of a "
                    "strictly zero air-flow exchange to ON. Non-zero "
                    "flows remain subject to exact profile verification."
                ),
                "requested_profile": expected_profile,
                "ve_readback": actual_profile,
            }
        )
        residual["variation_profile"] = expected_profile
    elif (
        expected_profile
        and expected_profile != "ON"
        and actual_profile == "ON"
        and expected_profile in constant_on_profile_ids
    ):
        warnings.append(
            {
                "code": CODE_CONSTANT_ONE_PROFILE_CANONICALIZED_ON,
                "message": (
                    "VE 2025 returned ON for a source-traced daily profile "
                    "whose every multiplier is exactly 1.0."
                ),
                "asset_type": "air_exchange",
                "requested_profile": expected_profile,
                "ve_readback": actual_profile,
            }
        )
        residual["variation_profile"] = expected_profile
    return residual, warnings


# ---------------------------------------------------------------------------
# Option / capability filter
# ---------------------------------------------------------------------------


def _capability_probe_supports(probe: Any, key: str) -> bool:
    """Decide whether the runtime exposes ``key`` on the target VE object.

    ``probe`` is either a Mapping, a callable ``(key) -> bool``, or an object
    whose attributes represent the target setter surface.
    """

    if probe is None:
        return True  # No probe = permissive; callers should probe explicitly
    if isinstance(probe, Mapping):
        value = probe.get(key)
        return bool(value)
    if callable(probe):
        try:
            return bool(probe(key))
        except Exception:  # pragma: no cover -- defensive
            return False
    return hasattr(probe, key)


def partition_options(
    payload: Mapping[str, Any],
    *,
    capability_probe: Any = None,
    audit_only_keys: Iterable[str] = (),
    required_keys: Iterable[str] = (),
    known_writable_keys: Optional[Iterable[str]] = None,
) -> OptionFilterResult:
    """Split ``payload`` into writable / audit-only / unknown / missing-required.

    Args:
        payload: The full source-traced payload the caller wants to send.
        capability_probe: A Mapping/callable/object exposing whether a key is
            actually supported by the current VE runtime object.  ``None``
            means "no runtime check" (only structural filtering happens).
        audit_only_keys: Keys that stay in the manifest (source-traced) but
            must NEVER reach ``set()``.  Example: ``solar_reflected_fraction``.
        required_keys: Keys whose absence from ``writable`` triggers
            ``missing_required`` and forces the caller to fail-closed before
            any mutation.
        known_writable_keys: Optional whitelist. When provided, keys outside
            this set (and not in ``audit_only_keys``) are treated as
            structurally unknown and dropped with an audit warning.

    The status derived from the result is:

    * ``FAIL`` if any required key ends up missing.
    * ``WARNING`` if any key is audit-only or unknown-dropped.
    * ``PASS`` otherwise.
    """

    audit_only_set = frozenset(audit_only_keys)
    required_set = frozenset(required_keys)
    known_set = None if known_writable_keys is None else frozenset(known_writable_keys)

    writable: Dict[str, Any] = {}
    audit_only: Dict[str, Any] = {}
    dropped_unknown: Dict[str, Any] = {}
    warnings: List[Dict[str, Any]] = []

    for key, value in payload.items():
        if key in audit_only_set:
            audit_only[key] = value
            warnings.append(
                {
                    "code": CODE_ROOM_CONDITION_AUDIT_ONLY,
                    "message": (
                        "Key '{}' is source-traced in the manifest but is "
                        "not a writable VE setter and was withheld from the "
                        "mutation payload.".format(key)
                    ),
                    "key": key,
                }
            )
            continue
        if known_set is not None and key not in known_set:
            dropped_unknown[key] = value
            warnings.append(
                {
                    "code": CODE_OPTION_NOT_EXPOSED,
                    "message": (
                        "Option '{}' is not in the declared writable set; "
                        "dropped before set() to protect the mutation.".format(key)
                    ),
                    "key": key,
                    "reason": "STRUCTURALLY_UNKNOWN",
                }
            )
            continue
        if not _capability_probe_supports(capability_probe, key):
            dropped_unknown[key] = value
            warnings.append(
                {
                    "code": CODE_OPTION_NOT_EXPOSED,
                    "message": (
                        "Option '{}' is not exposed by the active VE runtime; "
                        "dropped before set() to protect the mutation.".format(key)
                    ),
                    "key": key,
                    "reason": "RUNTIME_NOT_EXPOSED",
                }
            )
            continue
        writable[key] = value

    missing_required = tuple(sorted(k for k in required_set if k not in writable))
    for key in missing_required:
        warnings.append(
            {
                "code": CODE_OPTION_REQUIRED_MISSING,
                "message": (
                    "Required option '{}' is missing from the writable "
                    "payload; the caller must fail-closed before mutation.".format(key)
                ),
                "key": key,
            }
        )
    return OptionFilterResult(
        writable=writable,
        audit_only=audit_only,
        dropped_unknown=dropped_unknown,
        missing_required=missing_required,
        warnings=tuple(warnings),
    )


# ---------------------------------------------------------------------------
# Aggregating verdict
# ---------------------------------------------------------------------------


def evaluate_readback(
    context: str,
    residual_expected: Mapping[str, Any],
    actual: Mapping[str, Any],
    warnings: Iterable[Mapping[str, Any]] = (),
) -> ReadbackVerdict:
    """Return a ``ReadbackVerdict`` after any policy rules already applied.

    The caller is expected to have peeled off canonicalisations with the
    ``apply_*_readback_rules`` helpers and passed the resulting residual
    mapping here.  Any remaining difference is a genuine FAIL.
    """

    mismatches = _diff(residual_expected, actual)
    warning_tuple = tuple(dict(w) for w in warnings)
    if mismatches:
        return ReadbackVerdict(
            status=ReadbackStatus.FAIL,
            context=context,
            warnings=warning_tuple,
            mismatches=mismatches,
        )
    if warning_tuple:
        return ReadbackVerdict(
            status=ReadbackStatus.WARNING, context=context, warnings=warning_tuple
        )
    return ReadbackVerdict(status=ReadbackStatus.PASS, context=context)


# ---------------------------------------------------------------------------
# High-level convenience wrappers
# ---------------------------------------------------------------------------


def verify_material(
    category: str,
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
    *,
    context: str = "material",
) -> ReadbackVerdict:
    residual, warnings = apply_material_readback_rules(category, expected, actual)
    return evaluate_readback(context, residual, actual, warnings)


def verify_layer(
    construction_class: str,
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
    *,
    context: str = "layer",
) -> ReadbackVerdict:
    residual, warnings = apply_layer_readback_rules(construction_class, expected, actual)
    return evaluate_readback(context, residual, actual, warnings)


def verify_construction(
    construction_class: str,
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
    *,
    context: str = "construction",
) -> ReadbackVerdict:
    residual, warnings = apply_construction_readback_rules(
        construction_class, expected, actual
    )
    return evaluate_readback(context, residual, actual, warnings)


def verify_gain(
    category: str,
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
    *,
    constant_on_profile_ids: FrozenSet[str] = frozenset(),
    context: str = "gain",
) -> ReadbackVerdict:
    normalised_actual, warnings = apply_gain_readback_rules(
        category, expected, actual, constant_on_profile_ids
    )
    return evaluate_readback(context, expected, normalised_actual, warnings)


def verify_air_exchange(
    expected: Mapping[str, Any],
    actual: Mapping[str, Any],
    *,
    constant_on_profile_ids: FrozenSet[str] = frozenset(),
    context: str = "air_exchange",
) -> ReadbackVerdict:
    normalised_actual, warnings = apply_air_exchange_readback_rules(
        expected, actual, constant_on_profile_ids
    )
    return evaluate_readback(context, expected, normalised_actual, warnings)


__all__ = [
    "VE_FLOAT32_RELATIVE_TOLERANCE",
    "VE_FLOAT32_ABSOLUTE_TOLERANCE",
    "VE_THERMAL_MASS_MINIMUM",
    "CODE_MATERIAL_ZERO_THERMAL_MASS_MINIMUM",
    "CODE_GLASS_OPTICAL_PROPERTY_ROUNDED_3DP",
    "CODE_GLAZED_CONSTRUCTION_VLT_ROUNDED_4DP",
    "CODE_CONSTRUCTION_SURFACE_RESISTANCE_ROUNDED_4DP",
    "CODE_GLAZED_LAYER_RESISTANCE_ROUNDED_5DP",
    "CODE_GLAZED_LAYER_THICKNESS_NOT_PERSISTED",
    "CODE_ZERO_GAIN_PROFILE_CANONICALIZED_ON",
    "CODE_CONSTANT_ONE_PROFILE_CANONICALIZED_ON",
    "CODE_ZERO_AIR_FLOW_PROFILE_CANONICALIZED_ON",
    "CODE_ROOM_CONDITION_AUDIT_ONLY",
    "CODE_OPTION_NOT_EXPOSED",
    "CODE_OPTION_REQUIRED_MISSING",
    "ReadbackStatus",
    "ReadbackVerdict",
    "OptionFilterResult",
    "serializable",
    "values_match",
    "apply_material_readback_rules",
    "apply_layer_readback_rules",
    "apply_construction_readback_rules",
    "apply_gain_readback_rules",
    "apply_air_exchange_readback_rules",
    "partition_options",
    "evaluate_readback",
    "verify_material",
    "verify_layer",
    "verify_construction",
    "verify_gain",
    "verify_air_exchange",
]
