"""Pure domain objects used by generation, validation, and reporting."""

from dataclasses import asdict, dataclass, field
from enum import Enum
from math import sqrt
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True, order=True)
class Point3D:
    """Immutable Cartesian point expressed in model metres."""

    x: float
    y: float
    z: float

    def to_list(self) -> List[float]:
        """Return coordinates in gbXML axis order."""

        return [self.x, self.y, self.z]


@dataclass(frozen=True)
class Polygon3D:
    """Immutable planar polygon used by the geometry contract."""

    vertices: Tuple[Point3D, ...]

    def __post_init__(self) -> None:
        """Reject vertex sequences that cannot form a polygon."""

        if len(self.vertices) < 3:
            raise ValueError("A polygon requires at least three vertices")

    @property
    def bounds(self) -> Tuple[float, float, float, float, float, float]:
        """Return the polygon axis-aligned three-dimensional bounds."""

        xs = [point.x for point in self.vertices]
        ys = [point.y for point in self.vertices]
        zs = [point.z for point in self.vertices]
        return min(xs), max(xs), min(ys), max(ys), min(zs), max(zs)

    @property
    def area(self) -> float:
        """Return polygon area using Newell's method."""

        nx = ny = nz = 0.0
        vertices = self.vertices
        for index, current in enumerate(vertices):
            following = vertices[(index + 1) % len(vertices)]
            nx += (current.y - following.y) * (current.z + following.z)
            ny += (current.z - following.z) * (current.x + following.x)
            nz += (current.x - following.x) * (current.y + following.y)
        return 0.5 * sqrt(nx * nx + ny * ny + nz * nz)

    def to_list(self) -> List[List[float]]:
        """Return all polygon vertices as serializable coordinates."""

        return [vertex.to_list() for vertex in self.vertices]


class SurfaceType(str, Enum):
    """Supported semantic surface types for generated reference geometry."""

    EXTERIOR_WALL = "ExteriorWall"
    INTERIOR_WALL = "InteriorWall"
    ROOF = "Roof"
    SLAB_ON_GRADE = "SlabOnGrade"
    RAISED_FLOOR = "RaisedFloor"
    SHADE = "Shade"


class OpeningType(str, Enum):
    """Supported semantic opening types for generated envelope elements."""

    FIXED_WINDOW = "FixedWindow"
    OPERABLE_WINDOW = "OperableWindow"
    NON_SLIDING_DOOR = "NonSlidingDoor"


@dataclass(frozen=True)
class OpeningSpec:
    """Pure geometry and assignment metadata for one opening."""

    identifier: str
    opening_type: OpeningType
    polygon: Polygon3D
    construction_parameter: str

    def to_dict(self) -> Dict[str, Any]:
        """Return a machine-readable opening description."""

        return {
            "identifier": self.identifier,
            "opening_type": self.opening_type.value,
            "polygon": self.polygon.to_list(),
            "area_m2": self.polygon.area,
            "construction_parameter": self.construction_parameter,
        }


@dataclass(frozen=True)
class SurfaceSpec:
    """Pure geometry and adjacency metadata for one surface."""

    identifier: str
    surface_type: SurfaceType
    polygon: Polygon3D
    adjacent_space_ids: Tuple[str, ...] = ()
    construction_parameter: Optional[str] = None
    openings: Tuple[OpeningSpec, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        """Return a machine-readable surface description."""

        return {
            "identifier": self.identifier,
            "surface_type": self.surface_type.value,
            "polygon": self.polygon.to_list(),
            "area_m2": self.polygon.area,
            "adjacent_space_ids": list(self.adjacent_space_ids),
            "construction_parameter": self.construction_parameter,
            "openings": [opening.to_dict() for opening in self.openings],
        }


@dataclass(frozen=True)
class SpaceSpec:
    """Closed thermal-space shell and its deterministic identifiers."""

    identifier: str
    name: str
    zone_identifier: str
    bounds: Tuple[float, float, float, float, float, float]
    shell_faces: Tuple[Polygon3D, ...]

    @property
    def floor_area_m2(self) -> float:
        """Return plan area derived from the rectangular bounds."""

        x0, x1, y0, y1, _, _ = self.bounds
        return (x1 - x0) * (y1 - y0)

    @property
    def volume_m3(self) -> float:
        """Return enclosed volume derived from the rectangular bounds."""

        x0, x1, y0, y1, z0, z1 = self.bounds
        return (x1 - x0) * (y1 - y0) * (z1 - z0)

    def to_dict(self) -> Dict[str, Any]:
        """Return a machine-readable thermal-space description."""

        return {
            "identifier": self.identifier,
            "name": self.name,
            "zone_identifier": self.zone_identifier,
            "bounds": list(self.bounds),
            "floor_area_m2": self.floor_area_m2,
            "volume_m3": self.volume_m3,
            "shell_faces": [face.to_list() for face in self.shell_faces],
        }


@dataclass(frozen=True)
class GeometryModel:
    """Complete implementation-neutral geometry contract for one building."""

    identifier: str
    name: str
    building_type: str
    north_axis_degrees: float
    spaces: Tuple[SpaceSpec, ...]
    surfaces: Tuple[SurfaceSpec, ...]
    assumptions: Dict[str, Any] = field(default_factory=dict)

    @property
    def floor_area_m2(self) -> float:
        """Return total generated floor area across every space."""

        return sum(space.floor_area_m2 for space in self.spaces)

    @property
    def volume_m3(self) -> float:
        """Return total generated volume across every space."""

        return sum(space.volume_m3 for space in self.spaces)

    @property
    def openings(self) -> Tuple[OpeningSpec, ...]:
        """Return all openings flattened from their parent surfaces."""

        return tuple(
            opening for surface in self.surfaces for opening in surface.openings
        )

    @property
    def shades(self) -> Tuple[SurfaceSpec, ...]:
        """Return all surfaces explicitly classified as shades."""

        return tuple(
            surface
            for surface in self.surfaces
            if surface.surface_type == SurfaceType.SHADE
        )

    def to_dict(self) -> Dict[str, Any]:
        """Return the complete serializable geometry contract."""

        return {
            "identifier": self.identifier,
            "name": self.name,
            "building_type": self.building_type,
            "north_axis_degrees": self.north_axis_degrees,
            "floor_area_m2": self.floor_area_m2,
            "volume_m3": self.volume_m3,
            "spaces": [space.to_dict() for space in self.spaces],
            "surfaces": [surface.to_dict() for surface in self.surfaces],
            "assumptions": dict(self.assumptions),
        }


@dataclass(frozen=True)
class MaterialSnapshot:
    """Normalized read-back state for one VE material."""

    identifier: str
    description: str
    properties: Dict[str, Any]
    valid: bool


@dataclass(frozen=True)
class ConstructionSnapshot:
    """Normalized read-back state for one VE construction."""

    identifier: str
    reference: str
    category: str
    layer_count: int
    material_ids: Tuple[str, ...]
    properties: Dict[str, Any]
    u_value_w_m2k: Optional[float]
    valid: bool


@dataclass(frozen=True)
class OpeningSnapshot:
    """Normalized read-back state for one imported VE opening."""

    identifier: str
    opening_type: str
    area_m2: float
    construction_id: str


@dataclass(frozen=True)
class SurfaceSnapshot:
    """Normalized read-back state for one imported VE surface."""

    identifier: str
    surface_type: str
    area_m2: float
    construction_ids: Tuple[str, ...]
    adjacent_room_ids: Tuple[str, ...]
    openings: Tuple[OpeningSnapshot, ...]


@dataclass(frozen=True)
class RoomSnapshot:
    """Normalized read-back state for one imported VE room."""

    identifier: str
    name: str
    area_m2: float
    volume_m3: float
    thermal_template_name: str
    surfaces: Tuple[SurfaceSnapshot, ...]
    hvac_system_id: str = ""


@dataclass(frozen=True)
class TemplateSnapshot:
    """Normalized read-back state for one VE thermal template."""

    handle: str
    name: str
    standard: str
    room_conditions: Dict[str, Any]
    system_data: Dict[str, Any]
    gains: Tuple[Dict[str, Any], ...]
    air_exchanges: Tuple[Dict[str, Any], ...]


@dataclass(frozen=True)
class ModelSnapshot:
    """Normalized VE project state consumed by post-mutation validation."""

    project_name: str
    project_path: str
    ve_version: str
    weather_file: str
    weather_readable: bool
    rooms: Tuple[RoomSnapshot, ...]
    constructions: Tuple[ConstructionSnapshot, ...]
    materials: Tuple[MaterialSnapshot, ...]
    templates: Tuple[TemplateSnapshot, ...]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Return the complete snapshot as nested serializable data."""

        return asdict(self)
