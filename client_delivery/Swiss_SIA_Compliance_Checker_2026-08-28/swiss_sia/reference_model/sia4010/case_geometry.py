"""Deterministic geometry for the common SIA 4010 Tests 1-3 cell."""

from dataclasses import dataclass
from typing import Dict, Tuple

from ..domain import (
    GeometryModel,
    OpeningSpec,
    OpeningType,
    Point3D,
    Polygon3D,
    SpaceSpec,
    SurfaceSpec,
    SurfaceType,
)
from ..exceptions import GeometryError
from .case_manifest import Sia4010CaseManifest


def _polygon(*coordinates: Tuple[float, float, float]) -> Polygon3D:
    """Build one immutable polygon."""

    return Polygon3D(tuple(Point3D(*coordinate) for coordinate in coordinates))


def _box_faces(width: float, depth: float, height: float) -> Tuple[Polygon3D, ...]:
    """Return the six outward-oriented faces of the single-zone test cell."""

    return (
        _polygon((0, 0, 0), (0, depth, 0), (width, depth, 0), (width, 0, 0)),
        _polygon(
            (0, 0, height),
            (width, 0, height),
            (width, depth, height),
            (0, depth, height),
        ),
        _polygon((0, 0, 0), (0, 0, height), (0, depth, height), (0, depth, 0)),
        _polygon(
            (width, 0, 0),
            (width, depth, 0),
            (width, depth, height),
            (width, 0, height),
        ),
        _polygon((0, 0, 0), (width, 0, 0), (width, 0, height), (0, 0, height)),
        _polygon(
            (0, depth, 0),
            (0, depth, height),
            (width, depth, height),
            (width, depth, 0),
        ),
    )


@dataclass(frozen=True)
class CellGeometryValidation:
    """Strict validation result for the source-traced test-cell geometry."""

    status: str
    checks: Dict[str, bool]

    @property
    def passed(self) -> bool:
        """Return whether every check passed."""

        return self.status == "PASS"


class Sia4010CellGeometryGenerator:
    """Generate the exact common test-cell geometry used by Tests 1-3."""

    def __init__(self, manifest: Sia4010CaseManifest):
        """Bind the generator to the source-traced case manifest."""

        self.manifest = manifest

    def generate(self, identifier: str = "SIA4010_CELL") -> GeometryModel:
        """Generate the one-zone cell and two south-facing windows."""

        width = float(self.manifest.value("cell_width_m"))
        depth = float(self.manifest.value("cell_depth_m"))
        height = float(self.manifest.value("cell_height_m"))
        count = int(self.manifest.value("south_window_count"))
        window_width = float(self.manifest.value("south_window_width_m"))
        window_height = float(self.manifest.value("south_window_height_m"))
        sill = float(self.manifest.value("south_window_sill_m"))
        margin = float(self.manifest.value("south_window_side_margin_m"))
        gap = float(self.manifest.value("south_window_gap_m"))
        if count != 2:
            raise GeometryError("SIA 4010 Tests 1/2 require exactly two windows")
        if abs((2.0 * margin + 2.0 * window_width + gap) - width) > 1e-9:
            raise GeometryError("South-window horizontal dimensions do not close")
        if sill + window_height >= height:
            raise GeometryError("South windows do not fit within the facade")

        faces = _box_faces(width, depth, height)
        space_id = "{}_SPACE".format(identifier)
        space = SpaceSpec(
            identifier=space_id,
            name="{}_ZONE".format(identifier),
            zone_identifier="{}_THERMAL_ZONE".format(identifier),
            bounds=(0.0, width, 0.0, depth, 0.0, height),
            shell_faces=faces,
        )
        windows = []
        for index, x0 in enumerate(
            (margin, margin + window_width + gap),
            start=1,
        ):
            x1 = x0 + window_width
            windows.append(
                OpeningSpec(
                    identifier="{}_WINDOW_{:02d}".format(identifier, index),
                    opening_type=OpeningType.FIXED_WINDOW,
                    polygon=_polygon(
                        (x0, 0.0, sill),
                        (x1, 0.0, sill),
                        (x1, 0.0, sill + window_height),
                        (x0, 0.0, sill + window_height),
                    ),
                    construction_parameter="glazing_construction_id",
                )
            )
        surfaces = (
            SurfaceSpec(
                "{}_FLOOR".format(identifier),
                SurfaceType.RAISED_FLOOR,
                faces[0],
                (space_id,),
                "ground_floor_construction_id",
            ),
            SurfaceSpec(
                "{}_ROOF".format(identifier),
                SurfaceType.ROOF,
                faces[1],
                (space_id,),
                "roof_construction_id",
            ),
            SurfaceSpec(
                "{}_WALL_WEST".format(identifier),
                SurfaceType.EXTERIOR_WALL,
                faces[2],
                (space_id,),
                "external_wall_construction_id",
            ),
            SurfaceSpec(
                "{}_WALL_EAST".format(identifier),
                SurfaceType.EXTERIOR_WALL,
                faces[3],
                (space_id,),
                "external_wall_construction_id",
            ),
            SurfaceSpec(
                "{}_WALL_SOUTH".format(identifier),
                SurfaceType.EXTERIOR_WALL,
                faces[4],
                (space_id,),
                "external_wall_construction_id",
                tuple(windows),
            ),
            SurfaceSpec(
                "{}_WALL_NORTH".format(identifier),
                SurfaceType.EXTERIOR_WALL,
                faces[5],
                (space_id,),
                "external_wall_construction_id",
            ),
        )
        return GeometryModel(
            identifier="{}_BUILDING".format(identifier),
            name="SIA 4010 Tests 1-3 Cell",
            building_type="Office",
            north_axis_degrees=0.0,
            spaces=(space,),
            surfaces=surfaces,
            assumptions={
                "source": (
                    "SIA 4010 Tests 1-3 specifications, page 1, "
                    "dimensioned cell diagram"
                ),
                "coordinate_system": "positive X east, positive Y north, positive Z up",
                "south_facade": "y=0",
                "shading_capable": True,
                "shading_representation": (
                    "Dynamic VE opening/shading system; no fixed shade surface "
                    "is added to the common geometry."
                ),
                "required_object_types": (
                    "spaces",
                    "external_walls",
                    "roofs",
                    "ground_floors",
                    "windows",
                ),
            },
        )


def validate_cell_geometry(
    model: GeometryModel, manifest: Sia4010CaseManifest
) -> CellGeometryValidation:
    """Validate the exact dimensions, topology and opening placement."""

    tolerance = 1e-9
    width = float(manifest.value("cell_width_m"))
    depth = float(manifest.value("cell_depth_m"))
    height = float(manifest.value("cell_height_m"))
    sill = float(manifest.value("south_window_sill_m"))
    window_width = float(manifest.value("south_window_width_m"))
    window_height = float(manifest.value("south_window_height_m"))
    expected_window_area = window_width * window_height
    south = [
        surface for surface in model.surfaces if surface.identifier.endswith("WALL_SOUTH")
    ]
    windows = tuple(south[0].openings) if len(south) == 1 else ()
    checks = {
        "one_space": len(model.spaces) == 1,
        "six_boundaries": len(model.surfaces) == 6,
        "floor_area_48_m2": abs(model.floor_area_m2 - width * depth) <= tolerance,
        "volume_matches": abs(model.volume_m3 - width * depth * height) <= tolerance,
        "two_south_windows": len(windows) == 2,
        "window_areas_match": all(
            abs(window.polygon.area - expected_window_area) <= tolerance
            for window in windows
        ),
        "window_sills_match": all(
            abs(window.polygon.bounds[4] - sill) <= tolerance for window in windows
        ),
        "unique_ids": len(
            {
                *(space.identifier for space in model.spaces),
                *(surface.identifier for surface in model.surfaces),
                *(opening.identifier for opening in model.openings),
            }
        )
        == len(model.spaces) + len(model.surfaces) + len(model.openings),
        "construction_keys_present": all(
            surface.construction_parameter for surface in model.surfaces
        )
        and all(opening.construction_parameter for opening in model.openings),
        "floor_is_ground_decoupled": any(
            surface.surface_type == SurfaceType.RAISED_FLOOR for surface in model.surfaces
        ),
    }
    return CellGeometryValidation(
        status="PASS" if all(checks.values()) else "FAIL",
        checks=checks,
    )
