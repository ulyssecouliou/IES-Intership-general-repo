"""Fail-closed validation for configuration, geometry, and imported VE state."""

import hashlib
import json
from itertools import combinations
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .asset_manifest import AssetManifest
from .compliance_config import ParameterRegistry
from .domain import (
    ConstructionSnapshot,
    GeometryModel,
    ModelSnapshot,
    OpeningSpec,
    Polygon3D,
    SurfaceSpec,
    SurfaceType,
)
from .results import ValidationResult, ValidationStatus


def _result(
    control_id: str,
    category: str,
    status: ValidationStatus,
    message: str,
    object_id: Optional[str] = None,
    evidence: Optional[Dict[str, Any]] = None,
    source: str = "",
) -> ValidationResult:
    """Construct one consistently shaped validation control result."""

    return ValidationResult(
        control_id=control_id,
        category=category,
        status=status,
        message=message,
        object_id=object_id,
        evidence=evidence or {},
        source=source,
    )


def _duplicates(values: Iterable[str]) -> List[str]:
    """Return sorted values that occur more than once."""

    seen = set()
    duplicate_values = set()
    for value in values:
        if value in seen:
            duplicate_values.add(value)
        seen.add(value)
    return sorted(duplicate_values)


def _sha256(path: Path) -> str:
    """Return the SHA-256 of one evidence file without changing it."""

    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _weather_derivation_control(
    configured_weather: str, project_path: str
) -> Optional[ValidationResult]:
    """Qualify a converted EPW candidate's provenance and claim boundary."""

    weather = Path(configured_weather)
    if not weather.is_absolute():
        weather = Path(project_path) / weather
    if not weather.stem.endswith("_IESVE_CANDIDATE"):
        return None
    expected_name = (
        weather.stem.replace("_IESVE_CANDIDATE", "_IESVE_DERIVATION") + ".json"
    )
    candidates = [
        weather.with_name(expected_name),
        Path(project_path) / "reference_model_artifacts" / "weather" / expected_name,
    ]
    audits = []
    seen = set()
    for candidate in candidates:
        resolved = str(candidate.resolve())
        if candidate.is_file() and resolved not in seen:
            audits.append(candidate)
            seen.add(resolved)
    if not audits:
        return _result(
            "VE-WEA-002",
            "Weather provenance",
            ValidationStatus.FAIL,
            "Converted EPW candidate has no unique derivation audit",
            evidence={
                "weather": str(weather),
                "expected_audit": expected_name,
                "audit_candidates": [str(item) for item in audits],
            },
        )
    if len(audits) > 1:
        try:
            audit_hashes = {_sha256(item) for item in audits}
        except OSError as exc:
            return _result(
                "VE-WEA-002",
                "Weather provenance",
                ValidationStatus.FAIL,
                "Converted EPW derivation evidence is unreadable",
                evidence={
                    "weather": str(weather),
                    "audit_candidates": [str(item) for item in audits],
                    "error": str(exc),
                },
            )
        if len(audit_hashes) != 1:
            return _result(
                "VE-WEA-002",
                "Weather provenance",
                ValidationStatus.FAIL,
                "Converted EPW has conflicting derivation audits",
                evidence={
                    "weather": str(weather),
                    "audit_candidates": [str(item) for item in audits],
                },
            )
    audit_path = audits[-1]
    try:
        payload = json.loads(audit_path.read_text(encoding="utf-8"))
        actual_hash = _sha256(weather)
    except (OSError, ValueError) as exc:
        return _result(
            "VE-WEA-002",
            "Weather provenance",
            ValidationStatus.FAIL,
            "Converted EPW derivation evidence is unreadable or invalid",
            evidence={
                "weather": str(weather),
                "audit": str(audit_path),
                "error": str(exc),
            },
        )
    audited_hash = str(payload.get("weather", {}).get("sha256", "")).casefold()
    audit_ready = payload.get("status") == "READY_FOR_IESVE_READ_ONLY_PROBE"
    checksum_matches = bool(audited_hash) and audited_hash == actual_hash.casefold()
    claim_allowed = payload.get("compliance_claim_allowed") is True
    official_identity = payload.get("official_sia_weather_identity_confirmed") is True
    if not audit_ready or not checksum_matches:
        status = ValidationStatus.FAIL
        message = "Converted EPW does not match ready derivation evidence"
    elif claim_allowed and official_identity:
        status = ValidationStatus.PASS
        message = "Converted EPW provenance permits the declared compliance use"
    else:
        status = ValidationStatus.WARNING
        message = (
            "Converted EPW is technically qualified and checksum-bound, but its "
            "derivation audit does not permit a compliance claim"
        )
    return _result(
        "VE-WEA-002",
        "Weather provenance",
        status,
        message,
        evidence={
            "weather": str(weather),
            "weather_sha256": actual_hash,
            "derivation_audit": str(audit_path),
            "audit_status": payload.get("status"),
            "checksum_matches": checksum_matches,
            "compliance_claim_allowed": claim_allowed,
            "official_sia_weather_identity_confirmed": official_identity,
        },
        source="Project-local converted-weather derivation audit",
    )


def _aabb_overlap_volume(
    a: Tuple[float, float, float, float, float, float],
    b: Tuple[float, float, float, float, float, float],
    tolerance: float,
) -> float:
    """Return positive overlap volume for two axis-aligned boxes."""

    overlap_x = min(a[1], b[1]) - max(a[0], b[0])
    overlap_y = min(a[3], b[3]) - max(a[2], b[2])
    overlap_z = min(a[5], b[5]) - max(a[4], b[4])
    if overlap_x <= tolerance or overlap_y <= tolerance or overlap_z <= tolerance:
        return 0.0
    return overlap_x * overlap_y * overlap_z


def _varying_axes(
    bounds: Tuple[float, float, float, float, float, float], tolerance: float
) -> List[int]:
    """Return indices of dimensions with non-negligible extent."""

    extents = [bounds[1] - bounds[0], bounds[3] - bounds[2], bounds[5] - bounds[4]]
    return [index for index, extent in enumerate(extents) if extent > tolerance]


def _opening_within_surface(
    opening: OpeningSpec, surface: SurfaceSpec, tolerance: float
) -> bool:
    """Return whether an opening is contained in its parent plane."""

    opening_bounds = opening.polygon.bounds
    surface_bounds = surface.polygon.bounds
    for lower, upper, parent_lower, parent_upper in (
        (opening_bounds[0], opening_bounds[1], surface_bounds[0], surface_bounds[1]),
        (opening_bounds[2], opening_bounds[3], surface_bounds[2], surface_bounds[3]),
        (opening_bounds[4], opening_bounds[5], surface_bounds[4], surface_bounds[5]),
    ):
        if lower < parent_lower - tolerance or upper > parent_upper + tolerance:
            return False
    return _varying_axes(opening_bounds, tolerance) == _varying_axes(
        surface_bounds, tolerance
    )


def _rectangles_overlap(first: Polygon3D, second: Polygon3D, tolerance: float) -> bool:
    """Return whether two coplanar rectangles overlap by positive area."""

    a, b = first.bounds, second.bounds
    axes = _varying_axes(a, tolerance)
    if axes != _varying_axes(b, tolerance):
        return False
    intervals_a = ((a[0], a[1]), (a[2], a[3]), (a[4], a[5]))
    intervals_b = ((b[0], b[1]), (b[2], b[3]), (b[4], b[5]))
    return all(
        min(intervals_a[axis][1], intervals_b[axis][1])
        - max(intervals_a[axis][0], intervals_b[axis][0])
        > tolerance
        for axis in axes
    )


class ReferenceModelValidator:
    """Runs stable control IDs across all workflow stages."""

    def validate_configuration(
        self,
        parameters: ParameterRegistry,
        planned_parameter_names: Optional[Iterable[str]] = None,
    ) -> List[ValidationResult]:
        """Validate configuration metadata, values, and unresolved inputs."""

        results: List[ValidationResult] = []
        planned = set(planned_parameter_names or ())
        metadata_errors = []
        for parameter in parameters:
            if not all(
                (
                    parameter.name,
                    parameter.description,
                    parameter.units,
                    parameter.source,
                    parameter.source_locator,
                    parameter.validation_range.expected_type,
                )
            ):
                metadata_errors.append(parameter.name)
        results.append(
            _result(
                "CFG-001",
                "Configuration",
                ValidationStatus.FAIL if metadata_errors else ValidationStatus.PASS,
                (
                    "All parameters have description, units, source, locator and range metadata"
                    if not metadata_errors
                    else "Parameter metadata is incomplete"
                ),
                evidence={"parameters_with_missing_metadata": metadata_errors},
            )
        )

        validation_errors = parameters.validation_errors()
        results.append(
            _result(
                "CFG-002",
                "Configuration",
                ValidationStatus.FAIL if validation_errors else ValidationStatus.PASS,
                (
                    "All populated parameter values satisfy their validation ranges"
                    if not validation_errors
                    else "One or more parameter values are invalid"
                ),
                evidence={"errors": validation_errors},
            )
        )

        unresolved = [
            parameter
            for parameter in parameters.unresolved_required()
            if parameter.name not in planned
        ]
        results.append(
            _result(
                "CFG-003",
                "Configuration",
                ValidationStatus.FAIL if unresolved else ValidationStatus.PASS,
                (
                    "All inputs required before VE mutation are resolved"
                    if not unresolved
                    else "Required inputs are unresolved; VE mutation is blocked"
                ),
                evidence={"unresolved": [item.name for item in unresolved]},
            )
        )

        placeholders = [
            item.name
            for item in parameters.placeholders()
            if not item.required_for_generation and item.name not in planned
        ]
        results.append(
            _result(
                "CFG-004",
                "Missing parameters",
                ValidationStatus.WARNING if placeholders else ValidationStatus.PASS,
                (
                    "Compliance placeholders remain and must be resolved before a compliance claim"
                    if placeholders
                    else "No optional compliance placeholders remain"
                ),
                evidence={"placeholders": placeholders},
            )
        )
        return results

    def validate_asset_manifest(self, manifest: AssetManifest) -> List[ValidationResult]:
        """Validate the source-traced create-mode asset package."""

        errors = manifest.validation_errors()
        return [
            _result(
                "ASSET-001",
                "VE asset provisioning",
                ValidationStatus.FAIL if errors else ValidationStatus.PASS,
                (
                    "Asset manifest is complete, source-traced and internally consistent"
                    if not errors
                    else "Asset manifest cannot be used for VE mutation"
                ),
                evidence={
                    "errors": errors,
                    "source_path": manifest.source_path,
                    "sha256": manifest.source_checksum,
                    "planned_parameters": sorted(manifest.planned_parameter_names),
                },
            )
        ]

    def validate_geometry(
        self, model: GeometryModel, parameters: ParameterRegistry
    ) -> List[ValidationResult]:
        """Validate geometric integrity before any VE project mutation."""

        results: List[ValidationResult] = []
        tolerance = float(parameters.value("geometry_tolerance_m"))

        space_duplicates = _duplicates(space.identifier for space in model.spaces)
        surface_duplicates = _duplicates(surface.identifier for surface in model.surfaces)
        opening_duplicates = _duplicates(opening.identifier for opening in model.openings)
        all_duplicates = space_duplicates + surface_duplicates + opening_duplicates
        results.append(
            _result(
                "GEO-001",
                "Geometry",
                ValidationStatus.FAIL if all_duplicates else ValidationStatus.PASS,
                (
                    "All generated object identifiers are unique"
                    if not all_duplicates
                    else "Duplicate object identifiers detected"
                ),
                evidence={"duplicates": all_duplicates},
            )
        )

        invalid_dimensions = [
            space.identifier
            for space in model.spaces
            if space.floor_area_m2 <= tolerance or space.volume_m3 <= tolerance
        ]
        invalid_surfaces = [
            surface.identifier
            for surface in model.surfaces
            if surface.polygon.area <= tolerance
        ]
        results.append(
            _result(
                "GEO-002",
                "Geometry",
                (
                    ValidationStatus.FAIL
                    if invalid_dimensions or invalid_surfaces
                    else ValidationStatus.PASS
                ),
                (
                    "All spaces and surfaces have positive size"
                    if not invalid_dimensions and not invalid_surfaces
                    else "Zero/negative-size geometry detected"
                ),
                evidence={
                    "invalid_spaces": invalid_dimensions,
                    "invalid_surfaces": invalid_surfaces,
                },
            )
        )

        overlaps = []
        for first, second in combinations(model.spaces, 2):
            volume = _aabb_overlap_volume(first.bounds, second.bounds, tolerance)
            if volume > 0.0:
                overlaps.append(
                    {
                        "space_a": first.identifier,
                        "space_b": second.identifier,
                        "overlap_volume_m3": volume,
                    }
                )
        results.append(
            _result(
                "GEO-003",
                "Geometry",
                ValidationStatus.FAIL if overlaps else ValidationStatus.PASS,
                (
                    "No thermal-zone volumes overlap"
                    if not overlaps
                    else "Overlapping thermal-zone volumes detected"
                ),
                evidence={"overlaps": overlaps},
            )
        )

        invalid_shells = [
            space.identifier
            for space in model.spaces
            if len(space.shell_faces) != 6
            or any(face.area <= tolerance for face in space.shell_faces)
        ]
        surface_reference_count = {
            space.identifier: sum(
                1
                for surface in model.surfaces
                if space.identifier in surface.adjacent_space_ids
            )
            for space in model.spaces
        }
        orphaned = [
            space_id for space_id, count in surface_reference_count.items() if count != 6
        ]
        results.append(
            _result(
                "GEO-004",
                "Geometry",
                (
                    ValidationStatus.FAIL
                    if invalid_shells or orphaned
                    else ValidationStatus.PASS
                ),
                (
                    "Every zone has a six-face closed shell and six boundary references"
                    if not invalid_shells and not orphaned
                    else "Closed-shell or boundary topology is incomplete"
                ),
                evidence={
                    "invalid_shells": invalid_shells,
                    "boundary_reference_counts": surface_reference_count,
                    "orphaned_spaces": orphaned,
                },
            )
        )

        bad_adjacency = []
        for surface in model.surfaces:
            expected = (
                0
                if surface.surface_type == SurfaceType.SHADE
                else (2 if surface.surface_type == SurfaceType.INTERIOR_WALL else 1)
            )
            if len(surface.adjacent_space_ids) != expected:
                bad_adjacency.append(surface.identifier)
        results.append(
            _result(
                "GEO-005",
                "Zone definitions",
                ValidationStatus.FAIL if bad_adjacency else ValidationStatus.PASS,
                (
                    "Surface adjacency cardinality is complete and unambiguous"
                    if not bad_adjacency
                    else "Invalid surface adjacency cardinality detected"
                ),
                evidence={"invalid_surfaces": bad_adjacency},
            )
        )

        out_of_bounds = []
        opening_overlaps = []
        net_area_failures = []
        for surface in model.surfaces:
            for opening in surface.openings:
                if not _opening_within_surface(opening, surface, tolerance):
                    out_of_bounds.append(opening.identifier)
            for first, second in combinations(surface.openings, 2):
                if _rectangles_overlap(first.polygon, second.polygon, tolerance):
                    opening_overlaps.append((first.identifier, second.identifier))
            if (
                sum(opening.polygon.area for opening in surface.openings)
                >= surface.polygon.area
            ):
                net_area_failures.append(surface.identifier)
        results.append(
            _result(
                "GEO-006",
                "Envelope completeness",
                (
                    ValidationStatus.FAIL
                    if out_of_bounds or opening_overlaps or net_area_failures
                    else ValidationStatus.PASS
                ),
                (
                    "All openings are contained, non-overlapping and leave positive opaque area"
                    if not out_of_bounds
                    and not opening_overlaps
                    and not net_area_failures
                    else "Opening geometry is invalid"
                ),
                evidence={
                    "out_of_bounds_openings": out_of_bounds,
                    "overlapping_openings": opening_overlaps,
                    "nonpositive_net_surface_area": net_area_failures,
                },
            )
        )

        missing_construction_keys = [
            surface.identifier
            for surface in model.surfaces
            if surface.surface_type != SurfaceType.SHADE
            and not surface.construction_parameter
        ] + [
            opening.identifier
            for opening in model.openings
            if not opening.construction_parameter
        ]
        results.append(
            _result(
                "GEO-007",
                "Constructions",
                (
                    ValidationStatus.FAIL
                    if missing_construction_keys
                    else ValidationStatus.PASS
                ),
                (
                    "Every heat-transfer surface/opening maps to a construction parameter"
                    if not missing_construction_keys
                    else "Construction mappings are missing"
                ),
                evidence={"objects": missing_construction_keys},
            )
        )

        window_count = sum(
            1 for opening in model.openings if "Window" in opening.opening_type.value
        )
        door_count = sum(
            1 for opening in model.openings if "Door" in opening.opening_type.value
        )
        object_counts = {
            "spaces": len(model.spaces),
            "external_walls": sum(
                1
                for surface in model.surfaces
                if surface.surface_type == SurfaceType.EXTERIOR_WALL
            ),
            "roofs": sum(
                1
                for surface in model.surfaces
                if surface.surface_type == SurfaceType.ROOF
            ),
            "ground_floors": sum(
                1
                for surface in model.surfaces
                if surface.surface_type
                in (SurfaceType.SLAB_ON_GRADE, SurfaceType.RAISED_FLOOR)
            ),
            "windows": window_count,
            "doors": door_count,
            "shades": len(model.shades),
        }
        required_object_types = tuple(
            model.assumptions.get(
                "required_object_types",
                (
                    "spaces",
                    "external_walls",
                    "roofs",
                    "ground_floors",
                    "windows",
                    "doors",
                    "shades",
                ),
            )
        )
        unknown_required_types = sorted(set(required_object_types) - set(object_counts))
        missing_types = [
            name for name in required_object_types if object_counts.get(name, 0) == 0
        ]
        if unknown_required_types:
            missing_types.extend(unknown_required_types)
        results.append(
            _result(
                "GEO-008",
                "Geometry",
                ValidationStatus.FAIL if missing_types else ValidationStatus.PASS,
                (
                    "The model contains every object type required by its geometry profile"
                    if not missing_types
                    else "Required geometry object types are missing"
                ),
                evidence={
                    "counts": object_counts,
                    "required_types": list(required_object_types),
                    "missing_types": missing_types,
                },
            )
        )
        return results

    def validate_model_snapshot(
        self,
        snapshot: ModelSnapshot,
        parameters: ParameterRegistry,
        expected_geometry: GeometryModel,
    ) -> List[ValidationResult]:
        """Validate normalized VE read-back state against expected geometry."""

        results: List[ValidationResult] = []
        expected_names = {space.name for space in expected_geometry.spaces}
        generated_rooms = [room for room in snapshot.rooms if room.name in expected_names]
        actual_names = {room.name for room in generated_rooms}
        missing_rooms = sorted(expected_names - actual_names)
        duplicate_room_ids = _duplicates(room.identifier for room in snapshot.rooms)
        results.append(
            _result(
                "VE-ZONE-001",
                "Zone definitions",
                (
                    ValidationStatus.FAIL
                    if missing_rooms or duplicate_room_ids
                    else ValidationStatus.PASS
                ),
                (
                    "All generated zones exist exactly once in the VE model"
                    if not missing_rooms and not duplicate_room_ids
                    else "Generated zones are missing or duplicate"
                ),
                evidence={
                    "missing_room_names": missing_rooms,
                    "duplicate_room_ids": duplicate_room_ids,
                },
            )
        )

        orphaned_rooms = [
            room.identifier
            for room in generated_rooms
            if not room.surfaces or room.area_m2 <= 0.0 or room.volume_m3 <= 0.0
        ]
        results.append(
            _result(
                "VE-ZONE-002",
                "Zone definitions",
                ValidationStatus.FAIL if orphaned_rooms else ValidationStatus.PASS,
                (
                    "No generated room is orphaned or dimensionless"
                    if not orphaned_rooms
                    else "Orphaned/dimensionless rooms detected"
                ),
                evidence={"rooms": orphaned_rooms},
            )
        )

        required_construction_ids = {
            str(parameters.value(name))
            for name in (
                "external_wall_construction_id",
                "roof_construction_id",
                "ground_floor_construction_id",
                "internal_wall_construction_id",
                "door_construction_id",
                "glazing_construction_id",
            )
            if parameters.value(name)
        }
        construction_by_id = {
            construction.identifier: construction
            for construction in snapshot.constructions
        }
        missing_constructions = sorted(
            required_construction_ids - set(construction_by_id)
        )
        invalid_constructions = sorted(
            identifier
            for identifier in required_construction_ids & set(construction_by_id)
            if not construction_by_id[identifier].valid
            or construction_by_id[identifier].layer_count <= 0
            or not construction_by_id[identifier].material_ids
        )
        results.append(
            _result(
                "VE-CON-001",
                "Constructions",
                (
                    ValidationStatus.FAIL
                    if missing_constructions or invalid_constructions
                    else ValidationStatus.PASS
                ),
                (
                    "All configured constructions exist and have valid material layers"
                    if not missing_constructions and not invalid_constructions
                    else "Missing or invalid constructions detected"
                ),
                evidence={
                    "missing": missing_constructions,
                    "invalid": invalid_constructions,
                },
            )
        )

        missing_surface_assignments = []
        missing_opening_assignments = []
        invalid_surface_properties = []
        for room in generated_rooms:
            for surface in room.surfaces:
                if not surface.construction_ids:
                    missing_surface_assignments.append(surface.identifier)
                if surface.area_m2 <= 0.0 or not surface.surface_type:
                    invalid_surface_properties.append(surface.identifier)
                for opening in surface.openings:
                    if not opening.construction_id:
                        missing_opening_assignments.append(opening.identifier)
                    if opening.area_m2 <= 0.0 or not opening.opening_type:
                        invalid_surface_properties.append(opening.identifier)
        results.append(
            _result(
                "VE-ENV-001",
                "Envelope completeness",
                (
                    ValidationStatus.FAIL
                    if missing_surface_assignments
                    or missing_opening_assignments
                    or invalid_surface_properties
                    else ValidationStatus.PASS
                ),
                (
                    "Every VE surface/opening has a construction and valid basic properties"
                    if not missing_surface_assignments
                    and not missing_opening_assignments
                    and not invalid_surface_properties
                    else "VE envelope assignments or properties are incomplete"
                ),
                evidence={
                    "surfaces_without_construction": sorted(
                        set(missing_surface_assignments)
                    ),
                    "openings_without_construction": sorted(
                        set(missing_opening_assignments)
                    ),
                    "invalid_properties": sorted(set(invalid_surface_properties)),
                },
            )
        )

        template_name = str(parameters.value("thermal_template_name") or "")
        known_template_names = {template.name for template in snapshot.templates}
        rooms_without_template = [
            room.identifier
            for room in generated_rooms
            if room.thermal_template_name != template_name
        ]
        results.append(
            _result(
                "VE-TPL-001",
                "Templates",
                (
                    ValidationStatus.FAIL
                    if template_name not in known_template_names or rooms_without_template
                    else ValidationStatus.PASS
                ),
                (
                    "The configured source-traced thermal template exists and is assigned to every generated room"
                    if template_name in known_template_names
                    and not rooms_without_template
                    else "Thermal template is missing or misassigned"
                ),
                evidence={
                    "configured_template": template_name,
                    "available_templates": sorted(known_template_names),
                    "rooms_with_wrong_template": rooms_without_template,
                },
            )
        )

        configured_templates = [
            template for template in snapshot.templates if template.name == template_name
        ]
        template_structure_invalid = bool(configured_templates) and any(
            not template.room_conditions or not template.system_data
            for template in configured_templates
        )
        results.append(
            _result(
                "VE-TPL-002",
                "Templates",
                (
                    ValidationStatus.FAIL
                    if not configured_templates or template_structure_invalid
                    else ValidationStatus.PASS
                ),
                (
                    "Configured template exposes room-condition and system data"
                    if configured_templates and not template_structure_invalid
                    else "Configured template is missing required structural data"
                ),
                evidence={
                    "template_count": len(configured_templates),
                    "room_conditions_present": [
                        bool(template.room_conditions)
                        for template in configured_templates
                    ],
                    "system_data_present": [
                        bool(template.system_data) for template in configured_templates
                    ],
                },
            )
        )
        template_content_missing = bool(configured_templates) and any(
            not template.gains or not template.air_exchanges
            for template in configured_templates
        )
        results.append(
            _result(
                "VE-TPL-003",
                "Templates",
                (
                    ValidationStatus.WARNING
                    if not configured_templates or template_content_missing
                    else ValidationStatus.PASS
                ),
                (
                    "Template gain and air-exchange objects are present"
                    if configured_templates and not template_content_missing
                    else (
                        "Template gains or air exchanges are absent; confirm intentional zero-load/zero-flow cases with evidence"
                    )
                ),
                evidence={
                    "gain_counts": [
                        len(template.gains) for template in configured_templates
                    ],
                    "air_exchange_counts": [
                        len(template.air_exchanges) for template in configured_templates
                    ],
                },
            )
        )

        weather_configured = str(parameters.value("weather_file") or "")
        weather_matches = bool(snapshot.weather_file) and (
            snapshot.weather_file == weather_configured
            or snapshot.weather_file.replace("\\", "/").endswith(
                weather_configured.replace("\\", "/").split("/")[-1]
            )
        )
        results.append(
            _result(
                "VE-WEA-001",
                "Weather assignment",
                (
                    ValidationStatus.FAIL
                    if not weather_matches or not snapshot.weather_readable
                    else ValidationStatus.PASS
                ),
                (
                    "Configured weather is assigned and readable through WeatherFileReader"
                    if weather_matches and snapshot.weather_readable
                    else "Weather assignment is missing, different, or unreadable"
                ),
                evidence={
                    "configured": weather_configured,
                    "assigned": snapshot.weather_file,
                    "readable": snapshot.weather_readable,
                },
                source="IESVE VE 2023 VEScript User Guide, VELocate and WeatherFileReader",
            )
        )
        weather_derivation = _weather_derivation_control(
            weather_configured, snapshot.project_path
        )
        if weather_derivation is not None:
            results.append(weather_derivation)

        results.extend(self._validate_thermal_properties(construction_by_id, parameters))

        hvac_system_id = parameters.value("hvac_system_id")
        hvac_missing = not hvac_system_id
        hvac_mismatch = [
            room.identifier
            for room in generated_rooms
            if hvac_system_id and room.hvac_system_id != hvac_system_id
        ]
        status = (
            ValidationStatus.WARNING
            if hvac_missing
            else (ValidationStatus.FAIL if hvac_mismatch else ValidationStatus.PASS)
        )
        results.append(
            _result(
                "VE-HVAC-001",
                "HVAC placeholders",
                status,
                (
                    "HVAC remains an explicit placeholder; system-level compliance is not checkable"
                    if hvac_missing
                    else (
                        "Configured HVAC system is assigned to every generated room"
                        if not hvac_mismatch
                        else "Configured HVAC system is not assigned consistently"
                    )
                ),
                evidence={
                    "configured_system": hvac_system_id,
                    "rooms_with_mismatch": hvac_mismatch,
                },
            )
        )
        return results

    def _validate_thermal_properties(
        self,
        constructions: Dict[str, ConstructionSnapshot],
        parameters: ParameterRegistry,
    ) -> List[ValidationResult]:
        """Reconcile declared project U-values with VE construction values."""

        results: List[ValidationResult] = []
        tolerance = float(parameters.value("construction_u_value_tolerance_w_m2k"))
        mappings = (
            ("external_wall_construction_id", "project_external_wall_u_w_m2k"),
            ("roof_construction_id", "project_roof_u_w_m2k"),
            ("ground_floor_construction_id", "project_ground_floor_u_w_m2k"),
            ("glazing_construction_id", "project_window_u_w_m2k"),
        )
        for index, (construction_key, value_key) in enumerate(mappings, 1):
            construction_id = parameters.value(construction_key)
            expected = parameters.value(value_key)
            construction = constructions.get(str(construction_id))
            if expected is None:
                results.append(
                    _result(
                        "VE-THERM-{:03d}".format(index),
                        "Thermal properties",
                        ValidationStatus.WARNING,
                        "Declared project thermal value is unresolved; CDB value cannot be reconciled",
                        object_id=str(construction_id or ""),
                        evidence={"parameter": value_key},
                    )
                )
                continue
            actual = construction.u_value_w_m2k if construction else None
            matches = (
                actual is not None and abs(float(actual) - float(expected)) <= tolerance
            )
            results.append(
                _result(
                    "VE-THERM-{:03d}".format(index),
                    "Thermal properties",
                    ValidationStatus.PASS if matches else ValidationStatus.FAIL,
                    (
                        "CDB-reported U-value matches the declared project value within QA tolerance"
                        if matches
                        else "CDB-reported U-value is missing or differs from the declared project value"
                    ),
                    object_id=str(construction_id or ""),
                    evidence={
                        "declared_w_m2k": expected,
                        "cdb_w_m2k": actual,
                        "qa_tolerance_w_m2k": tolerance,
                        "tolerance_is_regulatory": False,
                    },
                )
            )

        glazing_id = str(parameters.value("glazing_construction_id") or "")
        glazing = constructions.get(glazing_id)
        optical_tolerance = float(parameters.value("optical_property_tolerance"))
        for offset, (parameter_name, property_name) in enumerate(
            (
                ("project_glazing_g_value", "g_value"),
                ("project_visible_light_transmittance", "visible_light_transmittance"),
            ),
            5,
        ):
            expected = parameters.value(parameter_name)
            actual = glazing.properties.get(property_name) if glazing else None
            if expected is None:
                status = ValidationStatus.WARNING
                message = "Declared project optical property is unresolved"
            else:
                matches = (
                    actual is not None
                    and abs(float(actual) - float(expected)) <= optical_tolerance
                )
                status = ValidationStatus.PASS if matches else ValidationStatus.FAIL
                message = (
                    "CDB optical property matches the declared project value"
                    if matches
                    else "CDB optical property is missing or inconsistent"
                )
            results.append(
                _result(
                    "VE-THERM-{:03d}".format(offset),
                    "Glazing properties",
                    status,
                    message,
                    object_id=glazing_id,
                    evidence={
                        "parameter": parameter_name,
                        "declared": expected,
                        "cdb": actual,
                        "qa_tolerance": optical_tolerance,
                        "tolerance_is_regulatory": False,
                    },
                )
            )
        return results
