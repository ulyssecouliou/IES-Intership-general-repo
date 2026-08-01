"""Qualified VE ResultsReader extraction for SIA 4010 Tests 1 and 2.

Only exact variables confirmed by a read-only runtime probe are accepted.
There is no token fallback in this module: a changed name, level or unit makes
the extraction NOT_CHECKABLE instead of silently selecting another quantity.
"""

import calendar
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple, Union

from ...simulation_results import (
    get_available_variables,
    get_results_per_hour,
    read_metric_room_result,
)
from ..exceptions import ConfigurationError
from .expected_results import ExpectedResult, ObservedResult
from .frequency_distribution import histogram_counts


@dataclass(frozen=True)
class QualifiedApsVariable:
    """One exact ResultsReader variable confirmed by the runtime probe."""

    quantity_id: str
    aps_varname: str
    display_name: str
    model_level: str
    metric_unit: str
    metric_divisor: float
    metric_offset: float

    @property
    def aps_tuple(self) -> Tuple[str, str, str, str, float, float]:
        """Return the tuple used by the common ResultsReader helper."""

        return (
            self.aps_varname,
            self.display_name,
            self.model_level,
            self.metric_unit,
            self.metric_divisor,
            self.metric_offset,
        )


class QualifiedApsBindings:
    """Validated view of the source-traced APS binding configuration."""

    SUPPORTED_SCHEMA_VERSIONS = {"1.0"}

    def __init__(self, path: Path, payload: Mapping[str, Any]):
        """Bind the qualified bindings to their source file and probe payload."""

        self.path = path
        self.payload = dict(payload)
        self.source_probe = dict(payload["source_probe"])
        self.variables = {
            quantity_id: QualifiedApsVariable(
                quantity_id=quantity_id,
                aps_varname=str(item["aps_varname"]),
                display_name=str(item["display_name"]),
                model_level=str(item["model_level"]),
                metric_unit=str(item["metric_unit"]),
                metric_divisor=float(item["metric_divisor"]),
                metric_offset=float(item["metric_offset"]),
            )
            for quantity_id, item in payload["bindings"].items()
        }

    @classmethod
    def load(cls, path: Union[str, Path]) -> "QualifiedApsBindings":
        """Load and validate the runtime binding contract."""

        binding_path = Path(path)
        try:
            payload = json.loads(binding_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ConfigurationError(
                "Invalid SIA 4010 APS binding configuration: {}".format(exc)
            ) from exc
        required = {"schema_version", "source_probe", "bindings"}
        missing = sorted(required - set(payload))
        if missing:
            raise ConfigurationError(
                "APS binding configuration is missing fields: {}".format(missing)
            )
        if str(payload["schema_version"]) not in cls.SUPPORTED_SCHEMA_VERSIONS:
            raise ConfigurationError(
                "Unsupported APS binding schema: {}".format(
                    payload["schema_version"]
                )
            )
        required_binding_fields = {
            "aps_varname",
            "display_name",
            "model_level",
            "metric_unit",
            "metric_divisor",
            "metric_offset",
            "status",
            "qualification_limit",
            "validation",
        }
        for quantity_id, item in payload["bindings"].items():
            absent = sorted(required_binding_fields - set(item))
            if absent:
                raise ConfigurationError(
                    "APS binding {} is missing fields: {}".format(
                        quantity_id, absent
                    )
                )
            if item["status"] != "RUNTIME_METADATA_CONFIRMED":
                raise ConfigurationError(
                    "APS binding {} is not runtime-confirmed".format(quantity_id)
                )
            permitted_units = {
                "sensible_heating_power": "kW",
                "sensible_cooling_power": "kW",
                "total_room_solar_heat_gain_power": "kW",
                "room_air_temperature": "\u00b0C",
                "operative_temperature": "\u00b0C",
            }
            required_unit = permitted_units.get(quantity_id)
            if required_unit is None:
                raise ConfigurationError(
                    "APS binding {} is not a permitted qualified quantity".format(
                        quantity_id
                    )
                )
            if item["metric_unit"] != required_unit:
                raise ConfigurationError(
                    "APS binding {} must expose qualified {}".format(
                        quantity_id, required_unit
                    )
                )
        expected_quantities = {
            "sensible_heating_power",
            "sensible_cooling_power",
            "total_room_solar_heat_gain_power",
            "room_air_temperature",
            "operative_temperature",
        }
        absent_quantities = sorted(expected_quantities - set(payload["bindings"]))
        if absent_quantities:
            raise ConfigurationError(
                "APS binding configuration lacks quantities: {}".format(
                    absent_quantities
                )
            )
        evidence_locator = str(
            payload["source_probe"].get("portable_evidence_extract", "")
            or ""
        )
        if not evidence_locator:
            raise ConfigurationError(
                "APS binding configuration lacks portable probe evidence"
            )
        evidence_path = binding_path.parent.parent / evidence_locator
        try:
            evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise ConfigurationError(
                "Invalid portable APS probe evidence: {}".format(exc)
            ) from exc
        source = evidence.get("source_diagnostic", {})
        if str(source.get("sha256", "")).upper() != str(
            payload["source_probe"].get("sha256", "")
        ).upper():
            raise ConfigurationError(
                "Portable APS probe evidence checksum does not match the "
                "binding source probe"
            )
        evidence_variables = {
            str(item.get("quantity_id", "")): item
            for item in evidence.get("variables", [])
        }
        for quantity_id in ("room_air_temperature", "operative_temperature"):
            expected = payload["bindings"][quantity_id]
            actual = evidence_variables.get(quantity_id, {})
            for field in (
                "aps_varname",
                "display_name",
                "model_level",
                "metric_unit",
                "metric_divisor",
                "metric_offset",
            ):
                if actual.get(field) != expected.get(field):
                    raise ConfigurationError(
                        "Portable APS evidence mismatch for {}.{}".format(
                            quantity_id, field
                        )
                    )
        return cls(binding_path, payload)

    def resolve_variable(
        self,
        results_file: Any,
        quantity_id: str,
    ) -> Optional[QualifiedApsVariable]:
        """Return the exact binding only when runtime metadata still matches."""

        qualified = self.variables.get(quantity_id)
        if qualified is None:
            return None
        matches = []
        for variable in get_available_variables(results_file):
            if (
                str(variable.get("aps_varname") or variable.get("name") or "")
                == qualified.aps_varname
                and str(variable.get("display_name") or "")
                == qualified.display_name
                and str(variable.get("model_level") or variable.get("level") or "")
                == qualified.model_level
                and str(variable.get("resolved_metric_unit") or "")
                == qualified.metric_unit
                and abs(
                    float(variable.get("resolved_metric_divisor", 1.0))
                    - qualified.metric_divisor
                )
                <= 1e-12
                and abs(
                    float(variable.get("resolved_metric_offset", 0.0))
                    - qualified.metric_offset
                )
                <= 1e-12
            ):
                matches.append(variable)
        return qualified if len(matches) == 1 else None


def _complete_year(values: Sequence[float], results_per_hour: float) -> bool:
    """Return whether a series is exactly one non-leap 365-day year."""

    return (
        results_per_hour > 0
        and len(values) == int(round(365 * 24 * results_per_hour))
    )


def _hourly_energy_kwh(
    power_kw: Sequence[float], results_per_hour: float
) -> Tuple[float, ...]:
    """Aggregate sub-hourly kW power to hourly integrated kWh."""

    steps = int(round(results_per_hour))
    if steps <= 0 or abs(results_per_hour - steps) > 1e-9:
        return ()
    if len(power_kw) % steps:
        return ()
    return tuple(
        sum(float(value) for value in power_kw[index : index + steps])
        / results_per_hour
        for index in range(0, len(power_kw), steps)
    )


def _hourly_average_watts(
    power_kw: Sequence[float], results_per_hour: float
) -> Tuple[float, ...]:
    """Aggregate sub-hourly kW power to hourly mean watts."""

    hourly_kwh = _hourly_energy_kwh(power_kw, results_per_hour)
    return tuple(value * 1000.0 for value in hourly_kwh)


def _hourly_means(
    values: Sequence[float], results_per_hour: float
) -> Tuple[float, ...]:
    """Aggregate one sub-hourly scalar series to hourly arithmetic means."""

    steps = int(round(results_per_hour))
    if steps <= 0 or abs(results_per_hour - steps) > 1e-9:
        return ()
    if len(values) % steps:
        return ()
    return tuple(
        sum(float(value) for value in values[index : index + steps]) / steps
        for index in range(0, len(values), steps)
    )


def _monthly_sums(hourly_kwh: Sequence[float], year: int) -> Tuple[float, ...]:
    """Return twelve calendar-month sums from one complete hourly series."""

    if len(hourly_kwh) != 365 * 24 or calendar.isleap(year):
        return ()
    sums = []
    cursor = 0
    for month in range(1, 13):
        count = calendar.monthrange(year, month)[1] * 24
        sums.append(sum(hourly_kwh[cursor : cursor + count]))
        cursor += count
    return tuple(sums)


def _monthly_means(hourly: Sequence[float], year: int) -> Tuple[float, ...]:
    """Return twelve calendar-month means from one complete hourly series."""

    if len(hourly) != 365 * 24 or calendar.isleap(year):
        return ()
    means = []
    cursor = 0
    for month in range(1, 13):
        count = calendar.monthrange(year, month)[1] * 24
        values = hourly[cursor : cursor + count]
        means.append(sum(values) / count)
        cursor += count
    return tuple(means)


def _day_slice(
    hourly: Sequence[float], year: int, month: int, day: int
) -> Tuple[float, ...]:
    """Return the 24 hourly values for one non-leap calendar date."""

    if len(hourly) != 365 * 24 or calendar.isleap(year):
        return ()
    if not 1 <= month <= 12 or not 1 <= day <= calendar.monthrange(
        year, month
    )[1]:
        return ()
    preceding_days = sum(
        calendar.monthrange(year, prior)[1]
        for prior in range(1, month)
    ) + day - 1
    start = preceding_days * 24
    return tuple(float(value) for value in hourly[start : start + 24])


class Sia4010QualifiedApsExtractor:
    """Extract official Test 1/2 metrics from one case APS result file."""

    def __init__(
        self,
        results_file: Any,
        room_id: Any,
        bindings: QualifiedApsBindings,
        evidence_locator: str,
    ):
        """Bind the extractor to one APS result file, room and qualified bindings."""

        self.results_file = results_file
        self.room_id = room_id
        self.bindings = bindings
        self.evidence_locator = str(evidence_locator)
        self.results_per_hour = get_results_per_hour(results_file)
        self._series: Dict[str, Tuple[float, ...]] = {}

    def metric_series(self, quantity_id: str) -> Tuple[float, ...]:
        """Return one exact complete-year qualified series or an empty tuple."""

        if quantity_id in self._series:
            return self._series[quantity_id]
        variable = self.bindings.resolve_variable(self.results_file, quantity_id)
        if variable is None:
            self._series[quantity_id] = ()
            return ()
        values = tuple(
            read_metric_room_result(
                self.results_file,
                self.room_id,
                variable.aps_tuple,
            )
        )
        if not _complete_year(values, self.results_per_hour):
            values = ()
        self._series[quantity_id] = values
        return values

    def power_series(self, quantity_id: str) -> Tuple[float, ...]:
        """Return one exact complete-year qualified kW series."""

        return self.metric_series(quantity_id)

    def hourly_power_watts(self, quantity_id: str) -> Tuple[float, ...]:
        """Return one complete qualified power series as hourly mean watts."""

        return _hourly_average_watts(
            self.power_series(quantity_id),
            self.results_per_hour,
        )

    def series_evidence(
        self, quantity_ids: Iterable[str]
    ) -> Dict[str, Dict[str, Any]]:
        """Return compact evidence for each complete qualified annual series."""

        evidence: Dict[str, Dict[str, Any]] = {}
        for quantity_id in quantity_ids:
            values = self.metric_series(quantity_id)
            binding = self.bindings.variables.get(quantity_id)
            if not values or binding is None:
                continue
            evidence[quantity_id] = {
                "aps_varname": binding.aps_varname,
                "display_name": binding.display_name,
                "model_level": binding.model_level,
                "unit": binding.metric_unit,
                "count": len(values),
                "minimum": float(min(values)),
                "maximum": float(max(values)),
                "mean": float(sum(values) / len(values)),
            }
        return evidence

    def test1_observed(
        self,
        expected_results: Iterable[ExpectedResult],
        year: int = 2011,
    ) -> Tuple[ObservedResult, ...]:
        """Return monthly, annual and hourly-integrated peak Test 1 values."""

        heating = _hourly_energy_kwh(
            self.power_series("sensible_heating_power"),
            self.results_per_hour,
        )
        cooling = _hourly_energy_kwh(
            self.power_series("sensible_cooling_power"),
            self.results_per_hour,
        )
        if not heating or not cooling:
            return ()
        heating_months = _monthly_sums(heating, year)
        cooling_months = _monthly_sums(cooling, year)
        if not heating_months or not cooling_months:
            return ()
        observed: List[ObservedResult] = []
        for expected in expected_results:
            if expected.test_id != "1" or expected.case_id != "1E":
                continue
            metric_lower = expected.metric.lower()
            label = expected.metric.rsplit("|", 1)[-1].strip()
            if "peak" in metric_lower:
                if label.lower() == "heating":
                    value = max(heating)
                elif label.lower() == "cooling":
                    value = max(cooling)
                else:
                    continue
            else:
                series = heating if "heating" in metric_lower else (
                    cooling if "cooling" in metric_lower else ()
                )
                months = heating_months if "heating" in metric_lower else (
                    cooling_months if "cooling" in metric_lower else ()
                )
                if not series:
                    continue
                if label.lower() == "annual":
                    value = sum(series)
                else:
                    try:
                        month = int(label)
                    except ValueError:
                        continue
                    if not 1 <= month <= 12:
                        continue
                    value = months[month - 1]
            observed.append(
                ObservedResult(
                    test_id=expected.test_id,
                    case_id=expected.case_id,
                    metric=expected.metric,
                    value=float(value),
                    unit=expected.unit,
                    evidence_locator=self.evidence_locator,
                )
            )
        return tuple(observed)

    def test1_reference_only_observed(
        self,
        case_id: str,
        year: int = 2011,
    ) -> Tuple[ObservedResult, ...]:
        """Return qualified Test 1 reference outputs without inventing bands.

        The official Test 1 workbook provides comparison tables for cases 600,
        640, 600FF, 900, 940 and 900FF but no lower/upper acceptance criterion.
        This method records the load and temperature results supported by the
        exact runtime-qualified APS variables.  It deliberately does not create
        ``ExpectedResult`` objects or tolerances.
        """

        normalized_case = str(case_id).upper()
        conditioned_cases = {"600", "640", "900", "940"}
        free_float_cases = {"600FF", "900FF"}
        supported_cases = conditioned_cases | free_float_cases
        if normalized_case not in supported_cases:
            raise ConfigurationError(
                "Reference-only Test 1 extraction is unavailable for case "
                "{!r}; supported cases are {}".format(
                    case_id, sorted(supported_cases)
                )
            )
        air_temperature = _hourly_means(
            self.metric_series("room_air_temperature"),
            self.results_per_hour,
        )
        operative_temperature = _hourly_means(
            self.metric_series("operative_temperature"),
            self.results_per_hour,
        )
        if not air_temperature or not operative_temperature:
            return ()
        operative_months = _monthly_means(operative_temperature, year)
        if not operative_months:
            return ()

        observed: List[ObservedResult] = []
        if normalized_case in conditioned_cases:
            heating = _hourly_energy_kwh(
                self.power_series("sensible_heating_power"),
                self.results_per_hour,
            )
            cooling = _hourly_energy_kwh(
                self.power_series("sensible_cooling_power"),
                self.results_per_hour,
            )
            if not heating or not cooling:
                return ()
            heating_months = _monthly_sums(heating, year)
            cooling_months = _monthly_sums(cooling, year)
            if not heating_months or not cooling_months:
                return ()
            energy_tables = (
                (
                    "Table 28 \u2014 Test results sensible energy needs for heating",
                    heating,
                    heating_months,
                ),
                (
                    "Table 29 \u2014 Test results sensible energy needs for cooling",
                    cooling,
                    cooling_months,
                ),
            )
            for table, series, monthly in energy_tables:
                for month, value in enumerate(monthly, start=1):
                    observed.append(
                        ObservedResult(
                            test_id="1",
                            case_id=normalized_case,
                            metric="{} | {}".format(table, month),
                            value=float(value),
                            unit="kWh",
                            evidence_locator=self.evidence_locator,
                        )
                    )
                observed.append(
                    ObservedResult(
                        test_id="1",
                        case_id=normalized_case,
                        metric="{} | Annual".format(table),
                        value=float(sum(series)),
                        unit="kWh",
                        evidence_locator=self.evidence_locator,
                    )
                )

            peak_table = (
                "Table 31 \u2014 Test results Annual hourly integrated peak "
                "heating and cooling load"
            )
            for label, series in (("Heating", heating), ("Cooling", cooling)):
                observed.append(
                    ObservedResult(
                        test_id="1",
                        case_id=normalized_case,
                        metric="{} | {}".format(peak_table, label),
                        value=float(max(series)),
                        unit="kWh (peak)",
                        evidence_locator=self.evidence_locator,
                    )
                )

            for month, day, table in (
                (
                    1,
                    4,
                    "Table 33 \u2014 Test results hourly sensible heating (+) "
                    "and cooling (-) load, January 4",
                ),
                (
                    7,
                    27,
                    "SIA 4010 Test 1 specification \u2014 hourly sensible "
                    "heating (+) and cooling (-) load, July 27",
                ),
            ):
                heating_day = _day_slice(heating, year, month, day)
                cooling_day = _day_slice(cooling, year, month, day)
                if len(heating_day) != 24 or len(cooling_day) != 24:
                    return ()
                for hour, (heating_value, cooling_value) in enumerate(
                    zip(heating_day, cooling_day), start=1
                ):
                    observed.append(
                        ObservedResult(
                            test_id="1",
                            case_id=normalized_case,
                            metric="{} | {}".format(table, hour),
                            value=float(heating_value - cooling_value),
                            unit="kWh",
                            evidence_locator=self.evidence_locator,
                        )
                    )

        temperature_table = (
            "Table 30 \u2014 Test results average operative temperature"
        )
        for month, value in enumerate(operative_months, start=1):
            observed.append(
                ObservedResult(
                    test_id="1",
                    case_id=normalized_case,
                    metric="{} | {}".format(temperature_table, month),
                    value=float(value),
                    unit="\u00b0C",
                    evidence_locator=self.evidence_locator,
                )
            )

        if normalized_case in free_float_cases:
            annual_table = (
                "Table 32 \u2014 Test results Annual hourly maximum, minimum "
                "and average operative temperature"
            )
            for label, value in (
                ("Maximum", max(operative_temperature)),
                ("Minimum", min(operative_temperature)),
                (
                    "Average",
                    sum(operative_temperature) / len(operative_temperature),
                ),
            ):
                observed.append(
                    ObservedResult(
                        test_id="1",
                        case_id=normalized_case,
                        metric="{} | {}".format(annual_table, label),
                        value=float(value),
                        unit="\u00b0C",
                        evidence_locator=self.evidence_locator,
                    )
                )
            january_4 = _day_slice(operative_temperature, year, 1, 4)
            if len(january_4) != 24:
                return ()
            table = (
                "Table 34 \u2014 Test results hourly operative temperature, "
                "January 4"
            )
            for hour, value in enumerate(january_4, start=1):
                observed.append(
                    ObservedResult(
                        test_id="1",
                        case_id=normalized_case,
                        metric="{} | {}".format(table, hour),
                        value=float(value),
                        unit="\u00b0C",
                        evidence_locator=self.evidence_locator,
                    )
                )
        return tuple(observed)

    def test2_observed(
        self,
        expected_results: Iterable[ExpectedResult],
    ) -> Tuple[ObservedResult, ...]:
        """Return the permitted total-solar-heat-gain annual alternative."""

        hourly = _hourly_energy_kwh(
            self.power_series("total_room_solar_heat_gain_power"),
            self.results_per_hour,
        )
        if not hourly:
            return ()
        annual = sum(hourly)
        observed = []
        for expected in expected_results:
            if (
                expected.test_id == "2"
                and "solarer wärmeeintrag" in expected.metric.lower()
            ):
                observed.append(
                    ObservedResult(
                        test_id=expected.test_id,
                        case_id=expected.case_id,
                        metric=expected.metric,
                        value=float(annual),
                        unit=expected.unit,
                        evidence_locator=self.evidence_locator,
                    )
                )
        return tuple(observed)

    def test2_solar_distribution(
        self,
        upper_edges: Sequence[float],
    ) -> Tuple[int, ...]:
        """Return official-bin counts for hourly total solar heat gain in W."""

        hourly_watts = _hourly_average_watts(
            self.power_series("total_room_solar_heat_gain_power"),
            self.results_per_hour,
        )
        return histogram_counts(hourly_watts, upper_edges) if hourly_watts else ()
