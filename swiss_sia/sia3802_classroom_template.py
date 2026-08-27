"""Source-traced SIA 2024 usage 4.01 operational template for VE review.

The generated template is a fallback when actual project design data are not
available.  It is not an automatic SIA 380/2 verdict: every non-direct VE
mapping remains visible in the receipt and actual project data take priority.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .reference_model.asset_manifest import (
    AirExchangeDefinition,
    Evidence,
    GainDefinition,
    ProfileDefinition,
    ThermalTemplateDefinition,
    TraceableField,
    VE_WEEKLY_PROFILE_SLOT_COUNT,
)
from .reference_model.compliance_config import ValidationRange

TEMPLATE_NAME = "SIA2024_4.01_CLASSROOM_REFERENCE"
SOURCE_RELATIVE_PATH = Path("refs/reference-data/sia-2024-2021.classroom-4.01.json")
MONTH_DAY_RANGES = (
    (1, 31),
    (32, 59),
    (60, 90),
    (91, 120),
    (121, 151),
    (152, 181),
    (182, 212),
    (213, 243),
    (244, 273),
    (274, 304),
    (305, 334),
    (335, 365),
)


@dataclass(frozen=True)
class OperationalTemplatePlan:
    """Minimal plan accepted by the operational-only VE provisioner."""

    on_existing: str
    profiles: Tuple[ProfileDefinition, ...]
    gains: Tuple[GainDefinition, ...]
    air_exchanges: Tuple[AirExchangeDefinition, ...]
    thermal_template: ThermalTemplateDefinition
    apache_system: None = None


def _source_path(repo_root: Path) -> Path:
    path = repo_root / SOURCE_RELATIVE_PATH
    if not path.is_file():
        raise RuntimeError("SIA 2024 classroom reference is missing: {}".format(path))
    return path


def load_classroom_reference(repo_root: Path) -> Dict[str, Any]:
    """Load and structurally verify the curated cell-level reference."""

    path = _source_path(repo_root)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "1.0":
        raise RuntimeError("Unsupported classroom-reference schema")
    if str((payload.get("usage_category") or {}).get("code")) != "4.01":
        raise RuntimeError("Classroom reference is not SIA usage category 4.01")
    required = {
        "area_per_person_m2",
        "people_sensible_cooling_w_person",
        "equipment_standard_w_m2",
        "lighting_standard_power_w_m2",
        "outdoor_air_standard_m3_h_m2",
        "infiltration_standard_m3_h_m2",
        "design_heating_setpoint_c",
        "design_cooling_setpoint_c",
    }
    missing = sorted(required - set(payload.get("values") or {}))
    if missing:
        raise RuntimeError("Classroom reference fields are missing: {}".format(missing))
    return payload


def _range(
    kind: str, minimum: float | None = None, maximum: float | None = None
) -> ValidationRange:
    return ValidationRange(kind, minimum, maximum, (), False)


def _field(
    value: Any,
    description: str,
    units: str,
    source: str,
    locator: str,
    kind: str = "number",
    minimum: float | None = None,
    maximum: float | None = None,
) -> TraceableField:
    return TraceableField(
        value=value,
        description=description,
        units=units,
        source=source,
        source_locator=locator,
        validation_range=_range(kind, minimum, maximum),
    )


def _evidence(description: str, locator: str) -> Evidence:
    return Evidence(description, "SIA 2024:2021 / SIA 380/2:2022", locator)


def _hourly_step_points(hourly: Sequence[float], multiplier: float) -> List[List[Any]]:
    """Translate 24 hourly multipliers to an unambiguous VE step profile."""

    if len(hourly) != 24:
        raise RuntimeError("A SIA daily profile must contain 24 values")
    values = [float(value) * float(multiplier) for value in hourly]
    points: List[List[Any]] = [[0.0, values[0], ""]]
    for hour in range(1, 24):
        if values[hour] != values[hour - 1]:
            points.append([float(hour), values[hour - 1], ""])
            points.append([float(hour), values[hour], ""])
    points.append([24.0, values[-1], ""])
    return points


def _profile_graph(
    reference: Mapping[str, Any],
) -> Tuple[Tuple[ProfileDefinition, ...], str, str]:
    source = "SIA 2024:2021"
    profiles = reference["profiles"]
    monthly = profiles["monthly_multipliers"]
    definitions: List[ProfileDefinition] = []

    off_key = "sia4010_classroom_off_day"
    definitions.append(
        ProfileDefinition(
            off_key,
            "daily",
            "SIA4010_CLASSROOM_OFF_DAY",
            True,
            -1,
            _field(
                [[0.0, 0.0, ""], [24.0, 0.0, ""]],
                "Unoccupied day used in the SIA classroom weekly graph.",
                "fraction versus hour",
                source,
                "Eingabedaten!HS17:HY17",
                "array",
            ),
            _evidence("SIA classroom unoccupied day.", "Eingabedaten!HS17:HY17"),
        )
    )

    yearly_keys: Dict[str, str] = {}
    for role, hourly, cells in (
        ("people", profiles["people_hourly_multipliers"], profiles["people_cells"]),
        (
            "equipment",
            profiles["equipment_hourly_multipliers"],
            profiles["equipment_cells"],
        ),
    ):
        periods = []
        for month_index, (factor, day_range) in enumerate(
            zip(monthly, MONTH_DAY_RANGES), 1
        ):
            daily_key = "sia4010_classroom_{}_day_{:02d}".format(role, month_index)
            weekly_key = "sia4010_classroom_{}_week_{:02d}".format(role, month_index)
            definitions.append(
                ProfileDefinition(
                    daily_key,
                    "daily",
                    "SIA4010_CLASSROOM_{}_DAY_{:02d}".format(role.upper(), month_index),
                    True,
                    -1,
                    _field(
                        _hourly_step_points(hourly, float(factor)),
                        "SIA 4.01 {} daily multipliers scaled by month {}.".format(
                            role, month_index
                        ),
                        "fraction versus hour",
                        source,
                        "Eingabedaten!{} and FM17:FX17".format(cells),
                        "array",
                    ),
                    _evidence(
                        "SIA classroom {} daily schedule.".format(role),
                        "Eingabedaten!{}".format(cells),
                    ),
                )
            )
            slots = (
                [{"profile_ref": daily_key}] * 5
                + [{"profile_ref": off_key}] * 2
                + [{"profile_ref": daily_key}] * (VE_WEEKLY_PROFILE_SLOT_COUNT - 7)
            )
            definitions.append(
                ProfileDefinition(
                    weekly_key,
                    "weekly",
                    "SIA4010_CLASSROOM_{}_WEEK_{:02d}".format(role.upper(), month_index),
                    True,
                    -1,
                    _field(
                        slots,
                        "Monday-Friday use with Saturday/Sunday rest days; VE design-day slots use the working day.",
                        "daily profile references",
                        source,
                        "Eingabedaten!HS17:HY17; VE weekly 12-slot contract",
                        "array",
                    ),
                    _evidence("SIA classroom weekly schedule.", "Eingabedaten!HS17:HY17"),
                )
            )
            periods.append([{"profile_ref": weekly_key}, day_range[0], day_range[1]])
        yearly_key = "sia4010_classroom_{}_year".format(role)
        definitions.append(
            ProfileDefinition(
                yearly_key,
                "yearly",
                "SIA4010_CLASSROOM_{}_YEAR".format(role.upper()),
                True,
                -1,
                _field(
                    periods,
                    "Non-leap annual SIA classroom profile graph.",
                    "weekly profile periods",
                    source,
                    "Eingabedaten!FM17:FX17",
                    "array",
                ),
                _evidence("SIA classroom annual schedule.", "Eingabedaten!FM17:FX17"),
            )
        )
        yearly_keys[role] = yearly_key
    return tuple(definitions), yearly_keys["people"], yearly_keys["equipment"]


def build_classroom_operational_plan(
    repo_root: Path,
) -> Tuple[OperationalTemplatePlan, Dict[str, Any]]:
    """Build the VE operational plan and a machine-readable review summary."""

    reference = load_classroom_reference(repo_root)
    values = reference["values"]
    mappings = reference["ve_mappings"]
    profiles, people_profile, equipment_profile = _profile_graph(reference)
    source = "SIA 2024:2021"

    def value(name: str) -> float:
        return float(values[name]["value"])

    def cell(name: str) -> str:
        return str(values[name].get("cell") or values[name].get("source"))

    people = GainDefinition(
        "people_gain",
        "people",
        "people",
        "square_metres_per_person",
        {
            "name": _field(
                "SIA2024_4P01_PEOPLE",
                "Stable VE name.",
                "text",
                source,
                "usage 4.01",
                "string",
            ),
            "occupancy_density": _field(
                value("area_per_person_m2"),
                "Floor area per person.",
                "m2/person",
                source,
                cell("area_per_person_m2"),
                "number",
                0.1,
                1000,
            ),
            "max_sensible_gain": _field(
                value("people_sensible_cooling_w_person"),
                "Sensible gain per person for cooling calculations.",
                "W/person",
                source,
                cell("people_sensible_cooling_w_person"),
                "number",
                0,
                1000,
            ),
            "max_latent_gain": _field(
                float(mappings["people_latent_w_person"]["value"]),
                "VE latent-heat mapping of the SIA moisture generation value; independent review required.",
                "W/person",
                "Engineering conversion of SIA 2024 moisture source",
                mappings["people_latent_w_person"]["formula"],
                "number",
                0,
                1000,
            ),
            "pc_convective_gain": _field(
                (1.0 - value("people_radiant_fraction")) * 100.0,
                "VE PeopleGain stores the complementary convective share as a percentage; derived exactly from the SIA radiant fraction.",
                "percent",
                source,
                "100 * (1 - {})".format(cell("people_radiant_fraction")),
                "number",
                0,
                100,
            ),
            "variation_profile": _field(
                {"profile_ref": people_profile},
                "SIA classroom annual people profile.",
                "VE profile reference",
                source,
                "Eingabedaten profile cells",
                "object",
            ),
        },
        _evidence("SIA 2024 classroom people gain fallback.", "Eingabedaten row 17"),
    )
    lighting = GainDefinition(
        "lighting_gain",
        "lighting",
        "general",
        "watts_per_square_metre",
        {
            "name": _field(
                "SIA2024_4P01_LIGHTING",
                "Stable VE name.",
                "text",
                source,
                "usage 4.01",
                "string",
            ),
            "max_power_consumption": _field(
                value("lighting_standard_power_w_m2"),
                "SIA standard installed lighting power.",
                "W/m2",
                source,
                cell("lighting_standard_power_w_m2"),
                "number",
                0,
                100,
            ),
            "radiant_fraction": _field(
                value("lighting_radiant_fraction"),
                "Radiant fraction of lighting gains.",
                "fraction",
                source,
                cell("lighting_radiant_fraction"),
                "number",
                0,
                1,
            ),
            "variation_profile": _field(
                {"profile_ref": people_profile},
                "Occupancy-shaped VE proxy; project lighting controls must replace it.",
                "VE profile reference",
                "Implementation proxy, not a SIA hourly lighting profile",
                mappings["lighting_profile"]["note"],
                "object",
            ),
        },
        _evidence(
            "SIA 2024 classroom lighting fallback with disclosed schedule proxy.",
            "Eingabedaten row 17; Resultate Standard row 14",
        ),
    )
    equipment = GainDefinition(
        "equipment_gain",
        "energy",
        "computers",
        "watts_per_square_metre",
        {
            "name": _field(
                "SIA2024_4P01_EQUIPMENT",
                "Stable VE name.",
                "text",
                source,
                "usage 4.01",
                "string",
            ),
            "max_power_consumption": _field(
                value("equipment_standard_w_m2"),
                "SIA standard equipment power density.",
                "W/m2",
                source,
                cell("equipment_standard_w_m2"),
                "number",
                0,
                1000,
            ),
            "max_sensible_gain": _field(
                value("equipment_standard_w_m2"),
                "Equipment load treated as sensible.",
                "W/m2",
                source,
                cell("equipment_standard_w_m2"),
                "number",
                0,
                1000,
            ),
            "max_latent_gain": _field(
                0.0,
                "No equipment moisture source is specified in the SIA usage row.",
                "W/m2",
                source,
                "Eingabedaten row 17 equipment fields",
                "number",
                0,
                1000,
            ),
            "radiant_fraction": _field(
                value("equipment_radiant_fraction"),
                "Radiant fraction of equipment gains.",
                "fraction",
                source,
                cell("equipment_radiant_fraction"),
                "number",
                0,
                1,
            ),
            "variation_profile": _field(
                {"profile_ref": equipment_profile},
                "SIA classroom annual equipment profile.",
                "VE profile reference",
                source,
                "Eingabedaten equipment profile cells",
                "object",
            ),
        },
        _evidence("SIA 2024 classroom equipment fallback.", "Eingabedaten row 17"),
    )
    ventilation_flow = value("outdoor_air_standard_m3_h_m2") / 3.6
    infiltration_flow = value("infiltration_standard_m3_h_m2") / 3.6
    ventilation = AirExchangeDefinition(
        "outdoor_air",
        "mechanical_ventilation",
        "litres_per_second_per_square_metre",
        "external_air",
        {
            "name": _field(
                "SIA2024_4P01_OUTDOOR_AIR",
                "Stable VE name.",
                "text",
                source,
                "usage 4.01",
                "string",
            ),
            "max_flow": _field(
                ventilation_flow,
                "SIA standard outdoor airflow converted exactly from m3/(h m2).",
                "L/(s m2)",
                source,
                "{} / 3.6".format(cell("outdoor_air_standard_m3_h_m2")),
                "number",
                0,
                20,
            ),
            "variation_profile": _field(
                {"profile_ref": people_profile},
                "Occupancy-shaped ventilation proxy; actual controls take precedence.",
                "VE profile reference",
                "Implementation proxy using the SIA usage profile",
                mappings["ventilation_profile"]["note"],
                "object",
            ),
        },
        _evidence("SIA 2024 classroom outdoor-air fallback.", "Eingabedaten row 17"),
    )
    infiltration = AirExchangeDefinition(
        "infiltration",
        "infiltration",
        "litres_per_second_per_square_metre",
        "external_air",
        {
            "name": _field(
                "SIA2024_4P01_INFILTRATION",
                "Stable VE name.",
                "text",
                source,
                "usage 4.01",
                "string",
            ),
            "max_flow": _field(
                infiltration_flow,
                "SIA standard infiltration converted exactly from m3/(h m2).",
                "L/(s m2)",
                source,
                "{} / 3.6".format(cell("infiltration_standard_m3_h_m2")),
                "number",
                0,
                20,
            ),
            "variation_profile": _field(
                "ON",
                "Constant SIA standard infiltration magnitude.",
                "VE built-in profile",
                source,
                cell("infiltration_standard_m3_h_m2"),
                "string",
            ),
        },
        _evidence("SIA 2024 classroom infiltration fallback.", "Eingabedaten row 17"),
    )
    template = ThermalTemplateDefinition(
        TEMPLATE_NAME,
        "generic",
        {
            "heating_setpoint": _field(
                value("design_heating_setpoint_c"),
                "SIA 2024 Table 11 design heating setpoint; project control path must be confirmed.",
                "degC",
                source,
                cell("design_heating_setpoint_c"),
                "number",
                0,
                40,
            ),
            "cooling_setpoint": _field(
                value("design_cooling_setpoint_c"),
                "SIA 2024 Table 11 design cooling setpoint; project control path must be confirmed.",
                "degC",
                source,
                cell("design_cooling_setpoint_c"),
                "number",
                0,
                50,
            ),
            "heating_profile": _field(
                "ON",
                "Heating availability fallback.",
                "VE built-in profile",
                "Project-review fallback",
                "SIA 380/2 actual controls take precedence",
                "string",
            ),
            "cooling_profile": _field(
                "ON",
                "Cooling availability fallback.",
                "VE built-in profile",
                "Project-review fallback",
                "SIA 380/2 actual controls take precedence",
                "string",
            ),
        },
        {
            "conditioned": _field(
                True,
                "Classroom is conditioned.",
                "boolean",
                source,
                "usage category 4.01",
                "boolean",
            ),
            "system_air_minimum_flowrate": _field(
                0.0,
                "Avoid duplicate system-air flow; outdoor air is represented by the linked Air Exchange.",
                "L/(s person)",
                "VE implementation mapping",
                "linked SIA2024_4P01_OUTDOOR_AIR",
                "number",
                0,
                0,
            ),
            "system_air_minimum_flowrate_units": _field(
                3,
                "VE unit selector for L/(s person); associated flow is zero.",
                "VE enum index",
                "VE API mapping",
                "VEThermalTemplate system data",
                "integer",
                0,
                4,
            ),
            "system_air_variation_profile": _field(
                "ON",
                "Zero system-air fallback remains zero.",
                "VE built-in profile",
                "VE implementation mapping",
                "linked Air Exchange carries SIA flow",
                "string",
            ),
        },
        (people.key, lighting.key, equipment.key),
        (infiltration.key, ventilation.key),
        _evidence(
            "Source-traced SIA 2024 classroom reference template for project review.",
            "SIA 380/2 clauses 4.2.4, 4.2.7, 4.3.1.5, 4.3.2.1 and SIA 2024 usage 4.01",
        ),
    )
    plan = OperationalTemplatePlan(
        "reuse_verified",
        profiles,
        (people, lighting, equipment),
        (infiltration, ventilation),
        template,
    )
    source_path = _source_path(repo_root)
    summary = {
        "schema_version": "1.0",
        "status": "READY_FOR_CONTROLLED_VE_PROVISIONING",
        "template_name": TEMPLATE_NAME,
        "source_path": str(source_path),
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "usage_category": reference["usage_category"],
        "direct_sia_values": values,
        "ve_mappings_requiring_review": mappings,
        "profile_count": len(profiles),
        "automatic_compliance_claim": False,
        "next_action": "Review mappings, create/verify the template in a disposable VE copy, then use the separate checksum-bound room-assignment preview.",
    }
    return plan, summary
