"""Load the ISO 52016-1 Clause 7.2 Test 1 published reference values.

The source tables provide comparison values but no acceptance tolerance.  The
records returned here intentionally carry no tolerance or band, so the common
comparator reports signed evidence as ``NOT_CHECKABLE`` instead of inventing a
PASS/FAIL criterion.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple, Union

from ..exceptions import ConfigurationError
from .expected_results import ExpectedResult


CATALOG_RELATIVE_PATH = Path("config/iso52016_test1_verification_cases.json")
CONDITIONED_CASES = frozenset({"600", "640", "900", "940"})
FREE_FLOAT_CASES = frozenset({"600FF", "900FF"})
SUPPORTED_CASES = CONDITIONED_CASES | FREE_FLOAT_CASES


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest().upper()


def _load_catalog(path: Path) -> Dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConfigurationError(
            "Unable to read ISO Test 1 reference catalog '{}': {}".format(
                path, exc
            )
        ) from exc
    if not isinstance(payload, dict):
        raise ConfigurationError("ISO Test 1 reference catalog must be an object")
    policy = payload.get("reference_results", {}).get("comparison_policy", {})
    if policy.get("mode") != "REFERENCE_ONLY":
        raise ConfigurationError(
            "ISO Test 1 catalog must remain REFERENCE_ONLY without a source tolerance"
        )
    return payload


def _expected(
    *,
    case_id: str,
    metric: str,
    value: float,
    unit: str,
    locator: str,
    checksum: str,
) -> ExpectedResult:
    return ExpectedResult(
        test_id="1",
        case_id=case_id,
        metric=metric,
        expected_value=float(value),
        unit=unit,
        absolute_tolerance=None,
        relative_tolerance=None,
        source_locator=locator,
        source_checksum=checksum,
    )


def _monthly_and_annual(
    output: List[ExpectedResult],
    *,
    case_id: str,
    table: str,
    values: Mapping[str, Any],
    unit: str,
    locator: str,
    checksum: str,
) -> None:
    months = values.get("months")
    if not isinstance(months, list) or len(months) != 12:
        raise ConfigurationError(
            "{} {} must provide twelve monthly values".format(table, case_id)
        )
    for month, value in enumerate(months, start=1):
        output.append(
            _expected(
                case_id=case_id,
                metric="{} | {}".format(table, month),
                value=value,
                unit=unit,
                locator=locator,
                checksum=checksum,
            )
        )
    if "annual" in values:
        output.append(
            _expected(
                case_id=case_id,
                metric="{} | Annual".format(table),
                value=values["annual"],
                unit=unit,
                locator=locator,
                checksum=checksum,
            )
        )


def load_test1_iso_reference_results(
    repository_root: Union[str, Path],
    case_id: str,
) -> Tuple[ExpectedResult, ...]:
    """Return published ISO comparison values matching the APS metric keys."""

    normalized = str(case_id).upper()
    if normalized not in SUPPORTED_CASES:
        raise ConfigurationError(
            "ISO Test 1 reference values are unavailable for {!r}".format(case_id)
        )
    path = Path(repository_root) / CATALOG_RELATIVE_PATH
    payload = _load_catalog(path)
    checksum = _sha256(path)
    results = payload["reference_results"]
    output: List[ExpectedResult] = []

    temperature_table = "Table 30 — Test results average operative temperature"
    temperature = results["monthly_average_operative_temperature_c"]
    # The APS extractor emits monthly values but not the differently weighted
    # annual average from Table 30, so only the twelve one-to-one metrics enter.
    monthly_temperature = dict(temperature[normalized])
    monthly_temperature.pop("annual", None)
    _monthly_and_annual(
        output,
        case_id=normalized,
        table=temperature_table,
        values=monthly_temperature,
        unit="°C",
        locator=temperature["source_locator"],
        checksum=checksum,
    )

    if normalized in CONDITIONED_CASES:
        for result_key, table in (
            (
                "monthly_heating_need_kwh",
                "Table 28 — Test results sensible energy needs for heating",
            ),
            (
                "monthly_cooling_need_kwh",
                "Table 29 — Test results sensible energy needs for cooling",
            ),
        ):
            block = results[result_key]
            _monthly_and_annual(
                output,
                case_id=normalized,
                table=table,
                values=block[normalized],
                unit="kWh",
                locator=block["source_locator"],
                checksum=checksum,
            )

        peak = results["annual_hourly_integrated_peak_kwh"]
        peak_table = (
            "Table 31 — Test results Annual hourly integrated peak heating "
            "and cooling load"
        )
        for source_key, label in (("heating", "Heating"), ("cooling", "Cooling")):
            output.append(
                _expected(
                    case_id=normalized,
                    metric="{} | {}".format(peak_table, label),
                    value=peak[normalized][source_key],
                    unit="kWh (peak)",
                    locator=peak["source_locator"],
                    checksum=checksum,
                )
            )

        hourly = results["january_4_hourly_sensible_load"]
        scale = float(hourly["published_integer_scale_to_kwh"])
        table = (
            "Table 33 — Test results hourly sensible heating (+) and cooling "
            "(-) load, January 4"
        )
        values = hourly[normalized]["published_values"]
        if len(values) != 24:
            raise ConfigurationError("Table 33 must contain 24 hourly values")
        for hour, value in enumerate(values, start=1):
            output.append(
                _expected(
                    case_id=normalized,
                    metric="{} | {}".format(table, hour),
                    value=float(value) * scale,
                    unit="kWh",
                    locator=hourly["source_locator"],
                    checksum=checksum,
                )
            )
    else:
        annual = results["free_float_annual_operative_temperature_c"]
        annual_table = (
            "Table 32 — Test results Annual hourly maximum, minimum and "
            "average operative temperature"
        )
        for source_key, label in (
            ("maximum", "Maximum"),
            ("minimum", "Minimum"),
            ("average", "Average"),
        ):
            output.append(
                _expected(
                    case_id=normalized,
                    metric="{} | {}".format(annual_table, label),
                    value=annual[normalized][source_key],
                    unit="°C",
                    locator=annual["source_locator"],
                    checksum=checksum,
                )
            )
        hourly = results["january_4_hourly_free_float_operative_temperature_c"]
        values = hourly[normalized]
        if len(values) != 24:
            raise ConfigurationError("Table 34 must contain 24 hourly values")
        table = "Table 34 — Test results hourly operative temperature, January 4"
        for hour, value in enumerate(values, start=1):
            output.append(
                _expected(
                    case_id=normalized,
                    metric="{} | {}".format(table, hour),
                    value=value,
                    unit="°C",
                    locator=hourly["source_locator"],
                    checksum=checksum,
                )
            )
    return tuple(output)
