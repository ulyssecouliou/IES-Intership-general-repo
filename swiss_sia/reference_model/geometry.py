"""Deterministic, axis-aligned reference building geometry generator."""

from typing import Dict, List, Tuple

from .compliance_config import ParameterRegistry
from .domain import (
    GeometryModel,
    OpeningSpec,
    OpeningType,
    Point3D,
    Polygon3D,
    SpaceSpec,
    SurfaceSpec,
    SurfaceType,
)
from .exceptions import GeometryError


def _polygon(*coordinates: Tuple[float, float, float]) -> Polygon3D:
    """Construct an immutable polygon from Cartesian coordinate tuples."""

    return Polygon3D(tuple(Point3D(*coordinate) for coordinate in coordinates))


def _box_faces(
    x0: float, x1: float, y0: float, y1: float, z0: float, z1: float
) -> Tuple[Polygon3D, ...]:
    """Return six outward-oriented faces for one rectangular zone."""

    return (
        _polygon((x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)),
        _polygon((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)),
        _polygon((x0, y0, z0), (x0, y0, z1), (x0, y1, z1), (x0, y1, z0)),
        _polygon((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)),
        _polygon((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)),
        _polygon((x0, y1, z0), (x0, y1, z1), (x1, y1, z1), (x1, y1, z0)),
    )


class ReferenceGeometryGenerator:
    """Generate non-overlapping zones, envelope surfaces, openings, and shades."""

    def __init__(self, parameters: ParameterRegistry):
        """Initialize generation from one validated configuration registry."""

        self.parameters = parameters

    def generate(self) -> GeometryModel:
        """Generate a deterministic closed-shell reference building model."""

        width = float(self.parameters.value("building_width_m"))
        depth = float(self.parameters.value("building_depth_m"))
        height = float(self.parameters.value("storey_height_m"))
        columns = int(self.parameters.value("zone_columns"))
        rows = int(self.parameters.value("zone_rows"))
        window_width = float(self.parameters.value("window_width_m"))
        window_height = float(self.parameters.value("window_height_m"))
        sill = float(self.parameters.value("window_sill_height_m"))
        door_width = float(self.parameters.value("door_width_m"))
        door_height = float(self.parameters.value("door_height_m"))
        overhang_depth = float(self.parameters.value("overhang_depth_m"))
        overhang_offset = float(self.parameters.value("overhang_vertical_offset_m"))

        if sill + window_height + overhang_offset > height:
            raise GeometryError("Window and overhang exceed the storey height")
        if door_height > height:
            raise GeometryError("Door height exceeds the storey height")

        dx = width / columns
        dy = depth / rows
        minimum_wall = window_width + 0.5
        if dx < minimum_wall or dy < minimum_wall:
            raise GeometryError(
                "Zone divisions leave insufficient facade length for configured windows"
            )
        if dx < door_width + window_width + 1.0:
            raise GeometryError(
                "South-west facade is too short for non-overlapping door and window"
            )

        prefix = str(self.parameters.value("model_identifier"))
        spaces: List[SpaceSpec] = []
        space_by_grid: Dict[Tuple[int, int], SpaceSpec] = {}
        for row in range(rows):
            for column in range(columns):
                x0, x1 = column * dx, (column + 1) * dx
                y0, y1 = row * dy, (row + 1) * dy
                identifier = "{}_SPACE_R{}_C{}".format(prefix, row + 1, column + 1)
                space = SpaceSpec(
                    identifier=identifier,
                    name="{}_ZONE_R{}_C{}".format(prefix, row + 1, column + 1),
                    zone_identifier="{}_THERMAL_ZONE_R{}_C{}".format(
                        prefix, row + 1, column + 1
                    ),
                    bounds=(x0, x1, y0, y1, 0.0, height),
                    shell_faces=_box_faces(x0, x1, y0, y1, 0.0, height),
                )
                spaces.append(space)
                space_by_grid[(row, column)] = space

        surfaces: List[SurfaceSpec] = []
        shade_index = 0
        window_index = 0

        def window_and_shade(
            side: str,
            wall_id: str,
            fixed_coordinate: float,
            segment_start: float,
            segment_end: float,
            include_door: bool = False,
        ) -> Tuple[Tuple[OpeningSpec, ...], SurfaceSpec]:
            """Create contained facade openings and their matching overhang."""

            nonlocal shade_index, window_index
            margin = 0.25
            openings: List[OpeningSpec] = []
            door_end = segment_start
            if include_door:
                door_start = segment_start + margin
                door_end = door_start + door_width
                if side != "south":
                    raise GeometryError("Reference door is only defined on south facade")
                door_polygon = _polygon(
                    (door_start, fixed_coordinate, 0.0),
                    (door_end, fixed_coordinate, 0.0),
                    (door_end, fixed_coordinate, door_height),
                    (door_start, fixed_coordinate, door_height),
                )
                openings.append(
                    OpeningSpec(
                        identifier="{}_DOOR_001".format(prefix),
                        opening_type=OpeningType.NON_SLIDING_DOOR,
                        polygon=door_polygon,
                        construction_parameter="door_construction_id",
                    )
                )

            available_start = (
                door_end + margin if include_door else segment_start + margin
            )
            available_end = segment_end - margin
            if available_end - available_start < window_width:
                raise GeometryError(
                    "Facade segment cannot contain configured opening geometry"
                )
            start = (available_start + available_end - window_width) / 2.0
            end = start + window_width
            z0, z1 = sill, sill + window_height

            if side == "south":
                window_polygon = _polygon(
                    (start, fixed_coordinate, z0),
                    (end, fixed_coordinate, z0),
                    (end, fixed_coordinate, z1),
                    (start, fixed_coordinate, z1),
                )
                shade_polygon = _polygon(
                    (start, fixed_coordinate, z1 + overhang_offset),
                    (end, fixed_coordinate, z1 + overhang_offset),
                    (end, fixed_coordinate - overhang_depth, z1 + overhang_offset),
                    (start, fixed_coordinate - overhang_depth, z1 + overhang_offset),
                )
            elif side == "north":
                window_polygon = _polygon(
                    (start, fixed_coordinate, z0),
                    (start, fixed_coordinate, z1),
                    (end, fixed_coordinate, z1),
                    (end, fixed_coordinate, z0),
                )
                shade_polygon = _polygon(
                    (start, fixed_coordinate, z1 + overhang_offset),
                    (start, fixed_coordinate + overhang_depth, z1 + overhang_offset),
                    (end, fixed_coordinate + overhang_depth, z1 + overhang_offset),
                    (end, fixed_coordinate, z1 + overhang_offset),
                )
            elif side == "west":
                window_polygon = _polygon(
                    (fixed_coordinate, start, z0),
                    (fixed_coordinate, start, z1),
                    (fixed_coordinate, end, z1),
                    (fixed_coordinate, end, z0),
                )
                shade_polygon = _polygon(
                    (fixed_coordinate, start, z1 + overhang_offset),
                    (fixed_coordinate - overhang_depth, start, z1 + overhang_offset),
                    (fixed_coordinate - overhang_depth, end, z1 + overhang_offset),
                    (fixed_coordinate, end, z1 + overhang_offset),
                )
            elif side == "east":
                window_polygon = _polygon(
                    (fixed_coordinate, start, z0),
                    (fixed_coordinate, end, z0),
                    (fixed_coordinate, end, z1),
                    (fixed_coordinate, start, z1),
                )
                shade_polygon = _polygon(
                    (fixed_coordinate, start, z1 + overhang_offset),
                    (fixed_coordinate, end, z1 + overhang_offset),
                    (fixed_coordinate + overhang_depth, end, z1 + overhang_offset),
                    (fixed_coordinate + overhang_depth, start, z1 + overhang_offset),
                )
            else:
                raise GeometryError("Unsupported facade side: {}".format(side))

            window_index += 1
            openings.append(
                OpeningSpec(
                    identifier="{}_WINDOW_{:03d}".format(prefix, window_index),
                    opening_type=OpeningType.FIXED_WINDOW,
                    polygon=window_polygon,
                    construction_parameter="glazing_construction_id",
                )
            )
            shade_index += 1
            shade = SurfaceSpec(
                identifier="{}_SHADE_{:03d}".format(prefix, shade_index),
                surface_type=SurfaceType.SHADE,
                polygon=shade_polygon,
                construction_parameter=None,
            )
            return tuple(openings), shade

        for row in range(rows):
            for column in range(columns):
                space = space_by_grid[(row, column)]
                x0, x1, y0, y1, z0, z1 = space.bounds
                token = "R{}_C{}".format(row + 1, column + 1)

                surfaces.append(
                    SurfaceSpec(
                        identifier="{}_GROUND_{}".format(prefix, token),
                        surface_type=SurfaceType.SLAB_ON_GRADE,
                        polygon=space.shell_faces[0],
                        adjacent_space_ids=(space.identifier,),
                        construction_parameter="ground_floor_construction_id",
                    )
                )
                surfaces.append(
                    SurfaceSpec(
                        identifier="{}_ROOF_{}".format(prefix, token),
                        surface_type=SurfaceType.ROOF,
                        polygon=space.shell_faces[1],
                        adjacent_space_ids=(space.identifier,),
                        construction_parameter="roof_construction_id",
                    )
                )

                external_definitions = []
                if column == 0:
                    external_definitions.append(
                        ("west", x0, y0, y1, space.shell_faces[2])
                    )
                if column == columns - 1:
                    external_definitions.append(
                        ("east", x1, y0, y1, space.shell_faces[3])
                    )
                if row == 0:
                    external_definitions.append(
                        ("south", y0, x0, x1, space.shell_faces[4])
                    )
                if row == rows - 1:
                    external_definitions.append(
                        ("north", y1, x0, x1, space.shell_faces[5])
                    )

                for side, fixed, start, end, polygon in external_definitions:
                    wall_id = "{}_WALL_{}_{}".format(prefix, side.upper(), token)
                    include_door = row == 0 and column == 0 and side == "south"
                    openings, shade = window_and_shade(
                        side, wall_id, fixed, start, end, include_door
                    )
                    surfaces.append(
                        SurfaceSpec(
                            identifier=wall_id,
                            surface_type=SurfaceType.EXTERIOR_WALL,
                            polygon=polygon,
                            adjacent_space_ids=(space.identifier,),
                            construction_parameter="external_wall_construction_id",
                            openings=openings,
                        )
                    )
                    surfaces.append(shade)

        # One shared surface per adjacency.  The first adjacent space is always
        # on the negative-normal side, matching the gbXML right-hand rule.
        for row in range(rows):
            for boundary in range(1, columns):
                left = space_by_grid[(row, boundary - 1)]
                right = space_by_grid[(row, boundary)]
                x = boundary * dx
                y0, y1 = row * dy, (row + 1) * dy
                surfaces.append(
                    SurfaceSpec(
                        identifier="{}_INT_WALL_X_R{}_B{}".format(
                            prefix, row + 1, boundary
                        ),
                        surface_type=SurfaceType.INTERIOR_WALL,
                        polygon=_polygon(
                            (x, y0, 0.0),
                            (x, y1, 0.0),
                            (x, y1, height),
                            (x, y0, height),
                        ),
                        adjacent_space_ids=(left.identifier, right.identifier),
                        construction_parameter="internal_wall_construction_id",
                    )
                )
        for column in range(columns):
            for boundary in range(1, rows):
                south = space_by_grid[(boundary - 1, column)]
                north = space_by_grid[(boundary, column)]
                y = boundary * dy
                x0, x1 = column * dx, (column + 1) * dx
                surfaces.append(
                    SurfaceSpec(
                        identifier="{}_INT_WALL_Y_C{}_B{}".format(
                            prefix, column + 1, boundary
                        ),
                        surface_type=SurfaceType.INTERIOR_WALL,
                        polygon=_polygon(
                            (x0, y, 0.0),
                            (x0, y, height),
                            (x1, y, height),
                            (x1, y, 0.0),
                        ),
                        adjacent_space_ids=(south.identifier, north.identifier),
                        construction_parameter="internal_wall_construction_id",
                    )
                )

        return GeometryModel(
            identifier="{}_BUILDING".format(prefix),
            name=str(self.parameters.value("building_name")),
            building_type=str(self.parameters.value("gbxml_building_type")),
            north_axis_degrees=float(self.parameters.value("north_axis_degrees")),
            spaces=tuple(spaces),
            surfaces=tuple(surfaces),
            assumptions={
                "coordinate_system": "positive X east, positive Y north, positive Z up",
                "storeys": 1,
                "zoning": "{} by {} orthogonal grid".format(columns, rows),
                "surface_reference_location": "InteriorSurface",
                "geometry_is_regulatory_value": False,
            },
        )
