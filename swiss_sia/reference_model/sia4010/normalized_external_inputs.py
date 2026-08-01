"""Validated machine bindings for delegated SIA 4010 input evidence.

The primary evidence may be a licensed PDF, workbook or authority dataset.
Generators consume only the distinct normalized artifact linked by the
technical-validation report.  This module validates the three bindings needed
by Test 2A without supplying or inferring any normative value.
"""

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

from ..exceptions import ConfigurationError
from .external_input_manifest import (
    EXTERNAL_INPUT_BINDING_SCHEMAS,
    ExternalInputEvidence,
    ExternalInputReadiness,
)
from .weather_verification import parse_tmy1


NORMALIZED_SCHEMA_VERSION = "1.0"
TEST2A_EXTERNAL_INPUT_IDS = (
    "iso52016_2017_chapter7_test_cell",
    "sia2028_dry_normal_zurich_kloten",
    "sia2024_office_3_1_standard_profiles",
)
SUPPORTED_WEATHER_FORMATS = {"EPW", "FWT", "TMY", "TMY1"}
SUPPORTED_PROFILE_TYPES = {
    "daily",
    "weekly",
    "yearly",
    "compact",
    "freeform",
}
SUPPORTED_VE_PROFILE_GRAPH_TYPES = {
    "daily",
    "weekly",
    "yearly",
}
REQUIRED_OFFICE_PROFILE_KEYS = (
    "occupancy_profile",
    "equipment_profile",
    "lighting_profile",
)


def _sha256(path: Path) -> str:
    """Return the lowercase SHA-256 digest of one file."""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _object(value: Any, context: str) -> Mapping[str, Any]:
    """Require one JSON object."""

    if not isinstance(value, Mapping):
        raise ConfigurationError("{} must be a JSON object".format(context))
    return value


def _text(value: Any, context: str) -> str:
    """Require one non-empty text value."""

    result = str(value or "").strip()
    if not result:
        raise ConfigurationError("{} must be non-empty text".format(context))
    return result


def _number(
    value: Any,
    context: str,
    *,
    minimum: float = None,
    maximum: float = None,
) -> float:
    """Require one finite numeric value within optional engineering bounds."""

    if isinstance(value, bool):
        raise ConfigurationError("{} must be numeric".format(context))
    try:
        result = float(value)
    except (TypeError, ValueError) as exc:
        raise ConfigurationError("{} must be numeric".format(context)) from exc
    if result != result or result in (float("inf"), float("-inf")):
        raise ConfigurationError("{} must be finite".format(context))
    if minimum is not None and result < minimum:
        raise ConfigurationError(
            "{} must be >= {}".format(context, minimum)
        )
    if maximum is not None and result > maximum:
        raise ConfigurationError(
            "{} must be <= {}".format(context, maximum)
        )
    return result


def _load_bound_json(evidence: ExternalInputEvidence) -> Dict[str, Any]:
    """Reload one normalized artifact and verify its immutable evidence link."""

    if not evidence.ready_for_binding:
        raise ConfigurationError(
            "External input '{}' is not READY_FOR_BINDING".format(
                evidence.input_id
            )
        )
    path = evidence.binding_artifact_path
    if path is None or not path.is_file():
        raise ConfigurationError(
            "External input '{}' binding artifact is unavailable".format(
                evidence.input_id
            )
        )
    if _sha256(path) != evidence.binding_artifact_sha256:
        raise ConfigurationError(
            "External input '{}' binding artifact changed after evidence "
            "validation".format(evidence.input_id)
        )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        raise ConfigurationError(
            "External input '{}' binding artifact is not valid UTF-8 JSON: "
            "{}".format(evidence.input_id, exc)
        ) from exc
    payload = dict(_object(payload, evidence.input_id))
    expected_schema = EXTERNAL_INPUT_BINDING_SCHEMAS[evidence.input_id]
    if str(payload.get("schema_id", "")) != expected_schema:
        raise ConfigurationError(
            "External input '{}' payload schema does not match {!r}".format(
                evidence.input_id, expected_schema
            )
        )
    if str(payload.get("schema_version", "")) != NORMALIZED_SCHEMA_VERSION:
        raise ConfigurationError(
            "External input '{}' normalized schema version is unsupported".format(
                evidence.input_id
            )
        )
    if (
        str(payload.get("primary_source_sha256", "")).strip().lower()
        != evidence.source_sha256
    ):
        raise ConfigurationError(
            "External input '{}' normalized artifact is not bound to its "
            "primary source SHA-256".format(evidence.input_id)
        )
    _text(payload.get("source_locator"), "{} source_locator".format(
        evidence.input_id
    ))
    return payload


@dataclass(frozen=True)
class NormalizedLayer:
    """One source-transcribed opaque material layer in SI units."""

    material_id: str
    thickness_m: float
    conductivity_w_mk: float
    density_kg_m3: float
    specific_heat_j_kgk: float


@dataclass(frozen=True)
class NormalizedOpaqueConstruction:
    """One ordered opaque construction and its source surface properties."""

    construction_id: str
    layers_outside_to_inside: Tuple[NormalizedLayer, ...]
    inside_ir_emissivity: float
    outside_ir_emissivity: float
    inside_solar_absorptance: float
    outside_solar_absorptance: float


@dataclass(frozen=True)
class NormalizedIsoTestCell:
    """Exact geometry and lightweight opaque definition from the ISO source."""

    width_m: float
    depth_m: float
    height_m: float
    window_count: int
    window_width_m: float
    window_height_m: float
    window_sill_m: float
    window_side_margin_m: float
    window_gap_m: float
    inside_surface_coefficient_w_m2k: float
    outside_surface_coefficient_w_m2k: float
    external_wall: NormalizedOpaqueConstruction
    roof: NormalizedOpaqueConstruction
    floor: NormalizedOpaqueConstruction
    source_locator: str

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe immutable binding record."""

        return asdict(self)


@dataclass(frozen=True)
class NormalizedWeatherBinding:
    """One authorized SIA weather file and its verified identity."""

    weather_file: Path
    weather_sha256: str
    weather_format: str
    hour_count: int
    station_name: str
    dataset_identity: str
    source_locator: str

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe immutable binding record."""

        payload = asdict(self)
        payload["weather_file"] = str(self.weather_file)
        return payload


@dataclass(frozen=True)
class NormalizedUsageProfile:
    """One exact source schedule, not implicitly a native VE profile.

    ``profile_type`` records the representation used by the independently
    validated normalized source artifact.  In particular, the legacy
    ``yearly`` representation is an 8760-value logical schedule; it must never
    be passed to ``VEProject.create_profile("yearly", ...)`` because a native
    VE yearly profile stores references to weekly profiles.
    """

    key: str
    profile_type: str
    reference: str
    modulating: bool
    units: int
    data: Tuple[Any, ...]
    source_locator: str


@dataclass(frozen=True)
class NormalizedVeProfileNode:
    """One native VE profile node with logical, collision-safe dependencies."""

    key: str
    profile_type: str
    reference: str
    modulating: bool
    units: int
    data: Tuple[Any, ...]
    source_locator: str


@dataclass(frozen=True)
class NormalizedVeProfileGraph:
    """A complete daily/weekly/yearly VE profile dependency graph."""

    nodes: Tuple[NormalizedVeProfileNode, ...]
    outputs: Tuple[Tuple[str, str], ...]
    source_locator: str

    @property
    def required_profile_types(self) -> Tuple[str, ...]:
        """Return the distinct native VE types required by this graph."""

        return tuple(sorted({node.profile_type for node in self.nodes}))

    def output_node_key(self, role: str) -> str:
        """Return the graph node selected for one logical office role."""

        outputs = dict(self.outputs)
        if role not in outputs:
            raise KeyError(role)
        return outputs[role]

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe graph with an explicit output mapping."""

        return {
            "nodes": [asdict(node) for node in self.nodes],
            "outputs": dict(self.outputs),
            "source_locator": self.source_locator,
            "required_profile_types": list(self.required_profile_types),
        }


@dataclass(frozen=True)
class NormalizedOfficeProfiles:
    """The three SIA 2024 office profiles and their calendar contract."""

    use_category: str
    value_set: str
    calendar_basis: str
    annual_simultaneity_method: str
    profiles: Tuple[NormalizedUsageProfile, ...]
    source_locator: str
    ve_profile_graph: Optional[NormalizedVeProfileGraph] = None

    @property
    def native_ve_materialization_ready(self) -> bool:
        """Whether an explicit native VE graph accompanies the source data."""

        return self.ve_profile_graph is not None

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe immutable binding record."""

        payload = asdict(self)
        payload["native_ve_materialization_ready"] = (
            self.native_ve_materialization_ready
        )
        if self.ve_profile_graph is not None:
            payload["ve_profile_graph"] = self.ve_profile_graph.to_dict()
        return payload


@dataclass(frozen=True)
class CommonCellExternalBindings:
    """The three delegated cell, weather and office-profile bindings."""

    iso_cell: NormalizedIsoTestCell
    weather: NormalizedWeatherBinding
    office_profiles: NormalizedOfficeProfiles
    evidence_sha256: Tuple[Tuple[str, str], ...]

    def to_dict(self) -> Dict[str, Any]:
        """Return one JSON-safe source receipt."""

        return {
            "iso_cell": self.iso_cell.to_dict(),
            "weather": self.weather.to_dict(),
            "office_profiles": self.office_profiles.to_dict(),
            "evidence_sha256": dict(self.evidence_sha256),
        }


@dataclass(frozen=True)
class Test2AExternalBindings:
    """All delegated, normalized inputs required before Test 2A generation."""

    iso_cell: NormalizedIsoTestCell
    weather: NormalizedWeatherBinding
    office_profiles: NormalizedOfficeProfiles
    evidence_sha256: Tuple[Tuple[str, str], ...]

    def to_dict(self) -> Dict[str, Any]:
        """Return a JSON-safe generator input receipt."""

        return {
            "iso_cell": self.iso_cell.to_dict(),
            "weather": self.weather.to_dict(),
            "office_profiles": self.office_profiles.to_dict(),
            "evidence_sha256": dict(self.evidence_sha256),
        }


def load_normalized_binding_payload(
    evidence: ExternalInputEvidence,
) -> Dict[str, Any]:
    """Load one checksum-bound normalized JSON payload.

    Domain-specific loaders should call this boundary rather than reopening an
    artifact themselves.  A successful return confirms identity and immutable
    source linkage only; semantic validation remains the caller's duty.
    """

    return _load_bound_json(evidence)


def _load_layer(value: Any, context: str) -> NormalizedLayer:
    """Validate one normalized opaque layer."""

    payload = _object(value, context)
    return NormalizedLayer(
        material_id=_text(payload.get("material_id"), context + ".material_id"),
        thickness_m=_number(
            payload.get("thickness_m"),
            context + ".thickness_m",
            minimum=0.000001,
            maximum=10.0,
        ),
        conductivity_w_mk=_number(
            payload.get("conductivity_w_mk"),
            context + ".conductivity_w_mk",
            minimum=0.000001,
            maximum=1000.0,
        ),
        density_kg_m3=_number(
            payload.get("density_kg_m3"),
            context + ".density_kg_m3",
            minimum=0.0,
            maximum=100000.0,
        ),
        specific_heat_j_kgk=_number(
            payload.get("specific_heat_j_kgk"),
            context + ".specific_heat_j_kgk",
            minimum=0.0,
            maximum=100000.0,
        ),
    )


def _load_construction(
    value: Any, context: str
) -> NormalizedOpaqueConstruction:
    """Validate one outside-to-inside opaque construction."""

    payload = _object(value, context)
    raw_layers = payload.get("layers_outside_to_inside")
    if not isinstance(raw_layers, Sequence) or isinstance(
        raw_layers, (str, bytes)
    ) or not raw_layers:
        raise ConfigurationError(
            "{}.layers_outside_to_inside must be a non-empty array".format(
                context
            )
        )
    layers = tuple(
        _load_layer(item, "{}.layers[{}]".format(context, index))
        for index, item in enumerate(raw_layers)
    )
    if len({item.material_id for item in layers}) != len(layers):
        raise ConfigurationError(
            "{} contains duplicate material_id values".format(context)
        )
    surface = _object(
        payload.get("surface_properties"), context + ".surface_properties"
    )
    return NormalizedOpaqueConstruction(
        construction_id=_text(
            payload.get("construction_id"), context + ".construction_id"
        ),
        layers_outside_to_inside=layers,
        inside_ir_emissivity=_number(
            surface.get("inside_ir_emissivity"),
            context + ".inside_ir_emissivity",
            minimum=0.0,
            maximum=1.0,
        ),
        outside_ir_emissivity=_number(
            surface.get("outside_ir_emissivity"),
            context + ".outside_ir_emissivity",
            minimum=0.0,
            maximum=1.0,
        ),
        inside_solar_absorptance=_number(
            surface.get("inside_solar_absorptance"),
            context + ".inside_solar_absorptance",
            minimum=0.0,
            maximum=1.0,
        ),
        outside_solar_absorptance=_number(
            surface.get("outside_solar_absorptance"),
            context + ".outside_solar_absorptance",
            minimum=0.0,
            maximum=1.0,
        ),
    )


def load_iso_test_cell(
    evidence: ExternalInputEvidence,
) -> NormalizedIsoTestCell:
    """Load the ISO Chapter 7 cell artifact without fallback values."""

    if evidence.input_id != "iso52016_2017_chapter7_test_cell":
        raise ConfigurationError("Wrong evidence supplied for ISO test cell")
    payload = _load_bound_json(evidence)
    cell = _object(payload.get("cell"), "ISO cell")
    openings = _object(cell.get("south_windows"), "ISO south_windows")
    constructions = _object(
        payload.get("lightweight_opaque_constructions"),
        "ISO lightweight_opaque_constructions",
    )
    width = _number(cell.get("width_m"), "ISO cell.width_m", minimum=0.1)
    height = _number(cell.get("height_m"), "ISO cell.height_m", minimum=0.1)
    window_count_raw = _number(
        openings.get("count"), "ISO south_windows.count", minimum=1
    )
    if not window_count_raw.is_integer():
        raise ConfigurationError("ISO south_windows.count must be an integer")
    window_count = int(window_count_raw)
    window_width = _number(
        openings.get("width_m"), "ISO south_windows.width_m", minimum=0.01
    )
    window_height = _number(
        openings.get("height_m"), "ISO south_windows.height_m", minimum=0.01
    )
    sill = _number(
        openings.get("sill_m"), "ISO south_windows.sill_m", minimum=0.0
    )
    margin = _number(
        openings.get("side_margin_m"),
        "ISO south_windows.side_margin_m",
        minimum=0.0,
    )
    gap = _number(
        openings.get("gap_m"), "ISO south_windows.gap_m", minimum=0.0
    )
    if abs((2.0 * margin + window_count * window_width + gap) - width) > 1e-9:
        raise ConfigurationError(
            "ISO south-window dimensions do not close against cell width"
        )
    if sill + window_height >= height:
        raise ConfigurationError(
            "ISO south windows do not fit within the cell height"
        )
    surface_coefficients = _object(
        payload.get("surface_coefficients_w_m2k"),
        "ISO surface_coefficients_w_m2k",
    )
    return NormalizedIsoTestCell(
        width_m=width,
        depth_m=_number(
            cell.get("depth_m"), "ISO cell.depth_m", minimum=0.1
        ),
        height_m=height,
        window_count=window_count,
        window_width_m=window_width,
        window_height_m=window_height,
        window_sill_m=sill,
        window_side_margin_m=margin,
        window_gap_m=gap,
        inside_surface_coefficient_w_m2k=_number(
            surface_coefficients.get("inside"),
            "ISO surface coefficient inside",
            minimum=0.000001,
        ),
        outside_surface_coefficient_w_m2k=_number(
            surface_coefficients.get("outside"),
            "ISO surface coefficient outside",
            minimum=0.000001,
        ),
        external_wall=_load_construction(
            constructions.get("external_wall"), "ISO external_wall"
        ),
        roof=_load_construction(constructions.get("roof"), "ISO roof"),
        floor=_load_construction(constructions.get("floor"), "ISO floor"),
        source_locator=_text(
            payload.get("source_locator"), "ISO source_locator"
        ),
    )


def load_weather_binding(
    evidence: ExternalInputEvidence,
) -> NormalizedWeatherBinding:
    """Load one SIA 2028 weather binding and recheck its assignable file."""

    if evidence.input_id != "sia2028_dry_normal_zurich_kloten":
        raise ConfigurationError("Wrong evidence supplied for SIA 2028 weather")
    payload = _load_bound_json(evidence)
    weather = _object(payload.get("weather_file"), "SIA 2028 weather_file")
    locator = _text(weather.get("path"), "SIA 2028 weather_file.path")
    path = Path(locator)
    if not path.is_absolute():
        path = evidence.binding_artifact_path.parent / path
    path = path.resolve()
    expected_sha = _text(
        weather.get("sha256"), "SIA 2028 weather_file.sha256"
    ).lower()
    if not path.is_file() or _sha256(path) != expected_sha:
        raise ConfigurationError(
            "SIA 2028 assignable weather file is missing or changed: {}".format(
                path
            )
        )
    weather_format = _text(
        weather.get("format"), "SIA 2028 weather_file.format"
    ).upper()
    if weather_format not in SUPPORTED_WEATHER_FORMATS:
        raise ConfigurationError(
            "Unsupported SIA 2028 weather format: {}".format(weather_format)
        )
    hour_count = int(
        _number(
            weather.get("hour_count"),
            "SIA 2028 weather_file.hour_count",
            minimum=8760,
            maximum=8760,
        )
    )
    if weather_format == "EPW":
        try:
            epw_lines = path.read_text(
                encoding="utf-8-sig"
            ).splitlines()
        except (OSError, UnicodeError) as exc:
            raise ConfigurationError(
                "Unable to read SIA 2028 EPW file: {}".format(exc)
            ) from exc
        actual_hours = len(
            [line for line in epw_lines[8:] if line.strip()]
        )
        if actual_hours != hour_count:
            raise ConfigurationError(
                "SIA 2028 EPW contains {} hourly records; expected {}".format(
                    actual_hours, hour_count
                )
            )
    elif weather_format in {"TMY", "TMY1"}:
        actual_hours = len(parse_tmy1(path))
        if actual_hours != hour_count:
            raise ConfigurationError(
                "SIA 2028 TMY contains {} hourly records; expected {}".format(
                    actual_hours, hour_count
                )
            )
    return NormalizedWeatherBinding(
        weather_file=path,
        weather_sha256=expected_sha,
        weather_format=weather_format,
        hour_count=hour_count,
        station_name=_text(payload.get("station_name"), "station_name"),
        dataset_identity=_text(
            payload.get("dataset_identity"), "dataset_identity"
        ),
        source_locator=_text(
            payload.get("source_locator"), "weather source_locator"
        ),
    )


def _profile_data(value: Any, profile_type: str, context: str) -> Tuple[Any, ...]:
    """Validate logical source schedule data without claiming VE semantics."""

    if not isinstance(value, list) or not value:
        raise ConfigurationError("{} must be a non-empty array".format(context))
    if profile_type == "daily":
        previous_hour = None
        normalized = []
        for index, point in enumerate(value):
            if not isinstance(point, list) or len(point) not in {2, 3}:
                raise ConfigurationError(
                    "{} daily point {} must contain hour, value and optional "
                    "interpolation marker".format(context, index)
                )
            hour = _number(
                point[0],
                "{}[{}].hour".format(context, index),
                minimum=0.0,
                maximum=24.0,
            )
            fraction = _number(
                point[1],
                "{}[{}].value".format(context, index),
                minimum=0.0,
                maximum=1.0,
            )
            if previous_hour is not None and hour < previous_hour:
                raise ConfigurationError(
                    "{} daily hours must be non-decreasing".format(context)
                )
            previous_hour = hour
            normalized.append((hour, fraction) + tuple(point[2:]))
        if float(value[0][0]) != 0.0 or float(value[-1][0]) != 24.0:
            raise ConfigurationError(
                "{} daily profile must span 00:00 to 24:00".format(context)
            )
        return tuple(normalized)
    if profile_type == "yearly":
        if len(value) != 8760:
            raise ConfigurationError(
                "{} yearly profile must contain exactly 8760 values".format(
                    context
                )
            )
        return tuple(
            _number(
                item,
                "{}[{}]".format(context, index),
                minimum=0.0,
                maximum=1.0,
            )
            for index, item in enumerate(value)
        )
    # Weekly, compact and freeform remain source representations only.  Native
    # VE materialization is permitted exclusively through ``ve_profile_graph``
    # below, whose dependency and calendar semantics are validated separately.
    return tuple(value)


def _profile_reference(value: Any, context: str) -> str:
    """Require one unambiguous logical profile reference marker."""

    payload = _object(value, context)
    if set(payload) != {"profile_ref"}:
        raise ConfigurationError(
            "{} must contain only profile_ref".format(context)
        )
    return _text(payload.get("profile_ref"), context + ".profile_ref")


def _profile_references(value: Any) -> Set[str]:
    """Collect logical profile references recursively from native graph data."""

    if isinstance(value, Mapping):
        if set(value) == {"profile_ref"}:
            reference = str(value.get("profile_ref", "")).strip()
            return {reference} if reference else set()
        result: Set[str] = set()
        for item in value.values():
            result.update(_profile_references(item))
        return result
    if isinstance(value, (list, tuple)):
        result = set()
        for item in value:
            result.update(_profile_references(item))
        return result
    return set()


def _integer_day(value: Any, context: str) -> int:
    """Require an integer day-of-year in the non-leap 8760-hour calendar."""

    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigurationError("{} must be an integer".format(context))
    if value < 1 or value > 365:
        raise ConfigurationError("{} must be between 1 and 365".format(context))
    return value


def _native_ve_profile_data(
    value: Any,
    profile_type: str,
    context: str,
) -> Tuple[Any, ...]:
    """Validate one proven native VE daily/weekly/yearly payload shape."""

    if profile_type == "daily":
        data = _profile_data(value, "daily", context)
        if _profile_references(data):
            raise ConfigurationError(
                "{} daily data cannot reference another profile".format(context)
            )
        return data
    if not isinstance(value, list) or not value:
        raise ConfigurationError("{} must be a non-empty array".format(context))
    if profile_type == "weekly":
        if len(value) != 7:
            raise ConfigurationError(
                "{} weekly data must contain exactly seven daily "
                "profile_ref entries".format(context)
            )
        return tuple(
            {"profile_ref": _profile_reference(
                item, "{}[{}]".format(context, index)
            )}
            for index, item in enumerate(value)
        )
    if profile_type == "yearly":
        normalized: List[Any] = []
        expected_start = 1
        for index, raw_period in enumerate(value):
            period_context = "{}[{}]".format(context, index)
            if not isinstance(raw_period, list) or len(raw_period) != 3:
                raise ConfigurationError(
                    "{} must contain profile_ref, start_day and end_day".format(
                        period_context
                    )
                )
            reference = _profile_reference(
                raw_period[0], period_context + "[0]"
            )
            start_day = _integer_day(
                raw_period[1], period_context + ".start_day"
            )
            end_day = _integer_day(
                raw_period[2], period_context + ".end_day"
            )
            if start_day != expected_start:
                raise ConfigurationError(
                    "{} yearly periods must be contiguous from day 1; "
                    "expected start {}, found {}".format(
                        context, expected_start, start_day
                    )
                )
            if end_day < start_day:
                raise ConfigurationError(
                    "{} end_day must be >= start_day".format(period_context)
                )
            normalized.append(
                ({"profile_ref": reference}, start_day, end_day)
            )
            expected_start = end_day + 1
        if expected_start != 366:
            raise ConfigurationError(
                "{} yearly periods must cover days 1 through 365".format(
                    context
                )
            )
        return tuple(normalized)
    raise ConfigurationError(
        "Unsupported native VE profile_type for {}: {}".format(
            context, profile_type
        )
    )


def _load_ve_profile_graph(
    value: Any,
) -> Optional[NormalizedVeProfileGraph]:
    """Load an optional, source-traced native VE dependency graph."""

    if value is None:
        return None
    payload = _object(value, "ve_profile_graph")
    raw_nodes = payload.get("nodes")
    if not isinstance(raw_nodes, list) or not raw_nodes:
        raise ConfigurationError(
            "ve_profile_graph.nodes must be a non-empty array"
        )
    nodes: List[NormalizedVeProfileNode] = []
    node_keys: Set[str] = set()
    references: Set[str] = set()
    for index, raw_node in enumerate(raw_nodes):
        context = "ve_profile_graph.nodes[{}]".format(index)
        node = _object(raw_node, context)
        key = _text(node.get("key"), context + ".key")
        if key in node_keys:
            raise ConfigurationError(
                "Duplicate ve_profile_graph node key: {}".format(key)
            )
        node_keys.add(key)
        reference = _text(node.get("reference"), context + ".reference")
        if reference in references:
            raise ConfigurationError(
                "Duplicate ve_profile_graph VE reference: {}".format(reference)
            )
        references.add(reference)
        profile_type = _text(
            node.get("profile_type"), context + ".profile_type"
        ).lower()
        if profile_type not in SUPPORTED_VE_PROFILE_GRAPH_TYPES:
            raise ConfigurationError(
                "Unsupported native VE profile_type for {}: {}".format(
                    key, profile_type
                )
            )
        units_raw = node.get("units")
        if (
            not isinstance(units_raw, int)
            or isinstance(units_raw, bool)
            or units_raw < -1
            or units_raw > 1
        ):
            raise ConfigurationError(
                "{} units must be an integer from -1 to 1".format(key)
            )
        nodes.append(
            NormalizedVeProfileNode(
                key=key,
                profile_type=profile_type,
                reference=reference,
                modulating=bool(node.get("modulating", True)),
                units=units_raw,
                data=_native_ve_profile_data(
                    node.get("data"),
                    profile_type,
                    context + ".data",
                ),
                source_locator=_text(
                    node.get("source_locator"),
                    context + ".source_locator",
                ),
            )
        )

    indexed = {node.key: node for node in nodes}
    dependencies = {
        node.key: _profile_references(node.data)
        for node in nodes
    }
    unknown_dependencies = sorted(
        {
            dependency
            for node_dependencies in dependencies.values()
            for dependency in node_dependencies
            if dependency not in indexed
        }
    )
    if unknown_dependencies:
        raise ConfigurationError(
            "ve_profile_graph has unknown profile_ref dependencies: {}".format(
                unknown_dependencies
            )
        )
    for node in nodes:
        expected_child_type = {
            "weekly": "daily",
            "yearly": "weekly",
        }.get(node.profile_type)
        child_types = {
            indexed[child].profile_type
            for child in dependencies[node.key]
        }
        if node.profile_type == "daily" and child_types:
            raise ConfigurationError(
                "Daily VE profile {} cannot have dependencies".format(node.key)
            )
        if expected_child_type is not None and child_types != {
            expected_child_type
        }:
            raise ConfigurationError(
                "{} VE profile {} must reference only {} profiles".format(
                    node.profile_type, node.key, expected_child_type
                )
            )

    resolved: Set[str] = set()
    remaining = set(indexed)
    while remaining:
        ready = {
            key for key in remaining if dependencies[key] <= resolved
        }
        if not ready:
            raise ConfigurationError(
                "ve_profile_graph contains cyclic profile_ref dependencies: "
                "{}".format(sorted(remaining))
            )
        resolved.update(ready)
        remaining -= ready

    raw_outputs = _object(payload.get("outputs"), "ve_profile_graph.outputs")
    missing_outputs = sorted(
        set(REQUIRED_OFFICE_PROFILE_KEYS) - set(raw_outputs)
    )
    unknown_outputs = sorted(
        set(raw_outputs) - set(REQUIRED_OFFICE_PROFILE_KEYS)
    )
    if missing_outputs or unknown_outputs:
        raise ConfigurationError(
            "ve_profile_graph output keys mismatch; missing={}, unknown={}".format(
                missing_outputs, unknown_outputs
            )
        )
    outputs = []
    for role in REQUIRED_OFFICE_PROFILE_KEYS:
        node_key = _text(
            raw_outputs.get(role),
            "ve_profile_graph.outputs.{}".format(role),
        )
        if node_key not in indexed:
            raise ConfigurationError(
                "ve_profile_graph output {} references unknown node {}".format(
                    role, node_key
                )
            )
        outputs.append((role, node_key))
    return NormalizedVeProfileGraph(
        nodes=tuple(nodes),
        outputs=tuple(outputs),
        source_locator=_text(
            payload.get("source_locator"),
            "ve_profile_graph.source_locator",
        ),
    )


def load_office_profiles(
    evidence: ExternalInputEvidence,
) -> NormalizedOfficeProfiles:
    """Load exact SIA 2024 category 3.1 profiles with calendar provenance."""

    if evidence.input_id != "sia2024_office_3_1_standard_profiles":
        raise ConfigurationError("Wrong evidence supplied for SIA 2024 profiles")
    payload = _load_bound_json(evidence)
    raw_profiles = payload.get("profiles")
    if not isinstance(raw_profiles, list):
        raise ConfigurationError("SIA 2024 profiles must be an array")
    indexed = {}
    normalized = []
    for index, value in enumerate(raw_profiles):
        item = _object(value, "SIA 2024 profile {}".format(index))
        key = _text(item.get("key"), "SIA 2024 profile key")
        if key in indexed:
            raise ConfigurationError(
                "Duplicate SIA 2024 profile key: {}".format(key)
            )
        indexed[key] = item
        profile_type = _text(
            item.get("profile_type"), "{}.profile_type".format(key)
        ).lower()
        if profile_type not in SUPPORTED_PROFILE_TYPES:
            raise ConfigurationError(
                "Unsupported profile_type for {}: {}".format(key, profile_type)
            )
        units_raw = item.get("units")
        if not isinstance(units_raw, int) or isinstance(units_raw, bool):
            raise ConfigurationError("{} units must be an integer".format(key))
        if units_raw < -1 or units_raw > 1:
            raise ConfigurationError("{} units must be -1, 0 or 1".format(key))
        normalized.append(
            NormalizedUsageProfile(
                key=key,
                profile_type=profile_type,
                reference=_text(
                    item.get("reference"), "{}.reference".format(key)
                ),
                modulating=bool(item.get("modulating", True)),
                units=units_raw,
                data=_profile_data(
                    item.get("data"),
                    profile_type,
                    "{}.data".format(key),
                ),
                source_locator=_text(
                    item.get("source_locator"),
                    "{}.source_locator".format(key),
                ),
            )
        )
    missing = sorted(set(REQUIRED_OFFICE_PROFILE_KEYS) - set(indexed))
    unknown = sorted(set(indexed) - set(REQUIRED_OFFICE_PROFILE_KEYS))
    if missing or unknown:
        raise ConfigurationError(
            "SIA 2024 office profile keys mismatch; missing={}, unknown={}".format(
                missing, unknown
            )
        )
    normalized.sort(key=lambda item: REQUIRED_OFFICE_PROFILE_KEYS.index(item.key))
    return NormalizedOfficeProfiles(
        use_category=_text(payload.get("use_category"), "use_category"),
        value_set=_text(payload.get("value_set"), "value_set"),
        calendar_basis=_text(
            payload.get("calendar_basis"), "calendar_basis"
        ),
        annual_simultaneity_method=_text(
            payload.get("annual_simultaneity_method"),
            "annual_simultaneity_method",
        ),
        profiles=tuple(normalized),
        source_locator=_text(
            payload.get("source_locator"), "profiles source_locator"
        ),
        ve_profile_graph=_load_ve_profile_graph(
            payload.get("ve_profile_graph")
        ),
    )


def load_test2a_external_bindings(
    readiness: ExternalInputReadiness,
) -> Test2AExternalBindings:
    """Load all three exact external bindings required by ``test_2A/2A``."""

    if (readiness.variant, readiness.case_id) != ("test_2A", "2A"):
        raise ConfigurationError(
            "Test 2A bindings require readiness for test_2A/2A"
        )
    if not readiness.ready_for_binding:
        raise ConfigurationError(
            "Test 2A external inputs are not READY_FOR_BINDING: {}".format(
                readiness.blocked_input_ids
            )
        )
    indexed = {item.input_id: item for item in readiness.evidence}
    if set(indexed) != set(TEST2A_EXTERNAL_INPUT_IDS):
        raise ConfigurationError(
            "Test 2A evidence set mismatch; expected {}, received {}".format(
                TEST2A_EXTERNAL_INPUT_IDS, tuple(indexed)
            )
        )
    common = load_common_cell_external_bindings(readiness)
    return Test2AExternalBindings(
        iso_cell=common.iso_cell,
        weather=common.weather,
        office_profiles=common.office_profiles,
        evidence_sha256=common.evidence_sha256,
    )


def load_common_cell_external_bindings(
    readiness: ExternalInputReadiness,
) -> CommonCellExternalBindings:
    """Load the shared ISO cell, SIA weather and SIA office-profile subset."""

    if not readiness.ready_for_binding:
        raise ConfigurationError(
            "Common cell external inputs are not READY_FOR_BINDING: {}".format(
                readiness.blocked_input_ids
            )
        )
    indexed = {item.input_id: item for item in readiness.evidence}
    missing = sorted(set(TEST2A_EXTERNAL_INPUT_IDS) - set(indexed))
    if missing:
        raise ConfigurationError(
            "Common cell evidence is incomplete: {}".format(missing)
        )
    return CommonCellExternalBindings(
        iso_cell=load_iso_test_cell(
            indexed["iso52016_2017_chapter7_test_cell"]
        ),
        weather=load_weather_binding(
            indexed["sia2028_dry_normal_zurich_kloten"]
        ),
        office_profiles=load_office_profiles(
            indexed["sia2024_office_3_1_standard_profiles"]
        ),
        evidence_sha256=tuple(
            (
                input_id,
                indexed[input_id].binding_artifact_sha256,
            )
            for input_id in TEST2A_EXTERNAL_INPUT_IDS
        ),
    )
