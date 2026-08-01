"""Minimal fail-closed IFC2X3 space extractor for the official SIA building.

The supplied ``abstractBIM`` IFC represents rooms as translated, vertically
extruded arbitrary closed profiles.  This module reads that qualified subset
without introducing a heavy IfcOpenShell dependency.  Unsupported rotations,
non-vertical extrusions or other representations are rejected rather than
approximated.
"""

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Tuple, Union

from ..exceptions import ConfigurationError


_ENTITY_RE = re.compile(r"^#(\d+)=([A-Z0-9_]+)\((.*)\);$")
_REF_RE = re.compile(r"#(\d+)")


def _split_args(value: str) -> Tuple[str, ...]:
    """Split STEP arguments while preserving nested lists and quoted commas."""

    fields: List[str] = []
    start = 0
    depth = 0
    quoted = False
    index = 0
    while index < len(value):
        character = value[index]
        if character == "'":
            # STEP escapes a quote inside a string as two consecutive quotes.
            if quoted and index + 1 < len(value) and value[index + 1] == "'":
                index += 2
                continue
            quoted = not quoted
        elif not quoted:
            if character == "(":
                depth += 1
            elif character == ")":
                depth -= 1
            elif character == "," and depth == 0:
                fields.append(value[start:index].strip())
                start = index + 1
        index += 1
    fields.append(value[start:].strip())
    return tuple(fields)


def _reference(value: str) -> Optional[int]:
    """Return one STEP reference or ``None`` for an unset field."""

    match = re.fullmatch(r"#(\d+)", str(value).strip())
    return int(match.group(1)) if match else None


def _references(value: str) -> Tuple[int, ...]:
    """Return all STEP references contained in one field."""

    return tuple(int(match) for match in _REF_RE.findall(value))


def _number_list(value: str) -> Tuple[float, ...]:
    """Return numeric components from an IFC coordinate/direction tuple."""

    return tuple(
        float(token)
        for token in re.findall(
            r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?", value
        )
    )


def _step_string(value: str) -> str:
    """Return one unquoted STEP string with standard IFC Unicode escapes."""

    stripped = str(value).strip()
    if len(stripped) >= 2 and stripped[0] == stripped[-1] == "'":
        stripped = stripped[1:-1].replace("''", "'")
        def decode_x2(match: re.Match) -> str:
            """Decode one IFC \\X2\\ UTF-16BE escape sequence to text."""

            try:
                return bytes.fromhex(match.group(1)).decode("utf-16-be")
            except (ValueError, UnicodeDecodeError):
                raise ConfigurationError(
                    "Invalid IFC X2 Unicode escape: {}".format(match.group(0))
                )

        return re.sub(
            r"\\X2\\([0-9A-Fa-f]+)\\X0\\",
            decode_x2,
            stripped,
        )
    return stripped


def _polygon_area(points: Tuple[Tuple[float, float], ...]) -> float:
    """Return the absolute shoelace area of one closed or open footprint."""

    return abs(
        sum(
            x0 * y1 - x1 * y0
            for (x0, y0), (x1, y1) in zip(
                points, points[1:] + points[:1]
            )
        )
    ) / 2.0


@dataclass(frozen=True)
class IfcSpaceRecord:
    """Source-traced prism extracted from one official ``IfcSpace``."""

    entity_id: int
    number: str
    long_name: str
    footprint_xy_m: Tuple[Tuple[float, float], ...]
    base_elevation_m: float
    height_m: float
    area_m2: float
    volume_m3: float
    source_path: str
    source_sha256: str

    def to_dict(self) -> Dict[str, object]:
        """Return a JSON-safe space record."""

        return {
            "entity_id": self.entity_id,
            "number": self.number,
            "long_name": self.long_name,
            "footprint_xy_m": [list(point) for point in self.footprint_xy_m],
            "base_elevation_m": self.base_elevation_m,
            "height_m": self.height_m,
            "area_m2": self.area_m2,
            "volume_m3": self.volume_m3,
            "source_path": self.source_path,
            "source_sha256": self.source_sha256,
        }


class AbstractBimIfcSpaceExtractor:
    """Read the translated vertical-prism subset used by the supplied IFC."""

    def __init__(self, path: Union[str, Path]):
        """Parse one IFC file into an entity map."""

        self.path = Path(path)
        try:
            raw = self.path.read_text(encoding="utf-8", errors="strict")
        except OSError as exc:
            raise ConfigurationError(
                "Cannot read official example-building IFC: {}".format(exc)
            ) from exc
        self.source_sha256 = hashlib.sha256(
            self.path.read_bytes()
        ).hexdigest()
        entities: Dict[int, Tuple[str, Tuple[str, ...]]] = {}
        for raw_line in raw.splitlines():
            line = raw_line.strip()
            match = _ENTITY_RE.match(line)
            if not match:
                continue
            entity_id = int(match.group(1))
            entities[entity_id] = (
                match.group(2),
                _split_args(match.group(3)),
            )
        if not entities:
            raise ConfigurationError("Official IFC contains no STEP entities")
        self.entities = entities
        self._placements: Dict[int, Tuple[float, float, float]] = {}

    def _entity(
        self, entity_id: int, expected_type: Optional[str] = None
    ) -> Tuple[str, Tuple[str, ...]]:
        """Return one entity and optionally enforce its IFC type."""

        entity = self.entities.get(entity_id)
        if entity is None:
            raise ConfigurationError(
                "IFC references missing entity #{}".format(entity_id)
            )
        if expected_type and entity[0] != expected_type:
            raise ConfigurationError(
                "IFC entity #{} is {}, expected {}".format(
                    entity_id, entity[0], expected_type
                )
            )
        return entity

    def _point(self, entity_id: int) -> Tuple[float, float, float]:
        """Return a Cartesian point padded to three dimensions."""

        _, args = self._entity(entity_id, "IFCCARTESIANPOINT")
        values = _number_list(args[0])
        if len(values) not in {2, 3}:
            raise ConfigurationError(
                "Unsupported IFC point dimension at #{}".format(entity_id)
            )
        return (
            float(values[0]),
            float(values[1]),
            float(values[2]) if len(values) == 3 else 0.0,
        )

    def _direction(self, entity_id: int) -> Tuple[float, float, float]:
        """Return a direction ratio padded to three dimensions."""

        _, args = self._entity(entity_id, "IFCDIRECTION")
        values = _number_list(args[0])
        if len(values) not in {2, 3}:
            raise ConfigurationError(
                "Unsupported IFC direction at #{}".format(entity_id)
            )
        return (
            float(values[0]),
            float(values[1]),
            float(values[2]) if len(values) == 3 else 0.0,
        )

    def _axis_translation(self, entity_id: int) -> Tuple[float, float, float]:
        """Return a placement translation and reject non-default rotations."""

        _, args = self._entity(entity_id, "IFCAXIS2PLACEMENT3D")
        point_id = _reference(args[0])
        if point_id is None:
            raise ConfigurationError(
                "IFC axis placement #{} has no origin".format(entity_id)
            )
        if len(args) > 1 and args[1] != "$":
            axis_id = _reference(args[1])
            if axis_id is None or self._direction(axis_id) != (0.0, 0.0, 1.0):
                raise ConfigurationError(
                    "Rotated IFC Z axis is not supported at #{}".format(entity_id)
                )
        if len(args) > 2 and args[2] != "$":
            direction_id = _reference(args[2])
            if (
                direction_id is None
                or self._direction(direction_id) != (1.0, 0.0, 0.0)
            ):
                raise ConfigurationError(
                    "Rotated IFC X axis is not supported at #{}".format(entity_id)
                )
        return self._point(point_id)

    def _placement(self, entity_id: int) -> Tuple[float, float, float]:
        """Resolve a nested local-placement translation."""

        if entity_id in self._placements:
            return self._placements[entity_id]
        _, args = self._entity(entity_id, "IFCLOCALPLACEMENT")
        parent_id = _reference(args[0])
        axis_id = _reference(args[1])
        if axis_id is None:
            raise ConfigurationError(
                "IFC local placement #{} has no relative placement".format(
                    entity_id
                )
            )
        parent = self._placement(parent_id) if parent_id is not None else (0.0, 0.0, 0.0)
        relative = self._axis_translation(axis_id)
        resolved = tuple(parent[index] + relative[index] for index in range(3))
        self._placements[entity_id] = resolved
        return resolved

    def _solid_for_shape(self, shape_id: int) -> int:
        """Resolve a product definition shape to exactly one extruded solid."""

        _, shape_args = self._entity(shape_id, "IFCPRODUCTDEFINITIONSHAPE")
        representation_ids = _references(shape_args[2])
        solids = []
        for representation_id in representation_ids:
            _, representation_args = self._entity(
                representation_id, "IFCSHAPEREPRESENTATION"
            )
            for item_id in _references(representation_args[3]):
                if self._entity(item_id)[0] == "IFCEXTRUDEDAREASOLID":
                    solids.append(item_id)
        if len(solids) != 1:
            raise ConfigurationError(
                "IFC shape #{} must resolve to one extruded solid; found {}".format(
                    shape_id, len(solids)
                )
            )
        return solids[0]

    def _extract_space(
        self, entity_id: int, args: Tuple[str, ...]
    ) -> IfcSpaceRecord:
        """Extract one ``IfcSpace`` prism and verify its representation."""

        if len(args) < 8:
            raise ConfigurationError(
                "IFC space #{} has an incomplete field list".format(entity_id)
            )
        number = _step_string(args[2])
        placement_id = _reference(args[5])
        shape_id = _reference(args[6])
        if placement_id is None or shape_id is None:
            raise ConfigurationError(
                "IFC space {} lacks placement or shape".format(number)
            )
        solid_id = self._solid_for_shape(shape_id)
        _, solid_args = self._entity(solid_id, "IFCEXTRUDEDAREASOLID")
        profile_id = _reference(solid_args[0])
        solid_axis_id = _reference(solid_args[1])
        direction_id = _reference(solid_args[2])
        if None in {profile_id, solid_axis_id, direction_id}:
            raise ConfigurationError(
                "IFC space {} has an incomplete extrusion".format(number)
            )
        direction = self._direction(direction_id)
        if direction != (0.0, 0.0, 1.0):
            raise ConfigurationError(
                "IFC space {} does not use a vertical extrusion".format(number)
            )
        try:
            height = float(solid_args[3])
        except (IndexError, ValueError) as exc:
            raise ConfigurationError(
                "IFC space {} has invalid extrusion depth".format(number)
            ) from exc
        _, profile_args = self._entity(
            profile_id, "IFCARBITRARYCLOSEDPROFILEDEF"
        )
        polyline_id = _reference(profile_args[2])
        if polyline_id is None:
            raise ConfigurationError(
                "IFC space {} profile has no polyline".format(number)
            )
        _, polyline_args = self._entity(polyline_id, "IFCPOLYLINE")
        point_ids = _references(polyline_args[0])
        points = [self._point(point_id) for point_id in point_ids]
        if len(points) >= 2 and points[0] == points[-1]:
            points.pop()
        if len(points) < 3:
            raise ConfigurationError(
                "IFC space {} footprint has fewer than three vertices".format(
                    number
                )
            )
        placement = self._placement(placement_id)
        solid_translation = self._axis_translation(solid_axis_id)
        footprint = tuple(
            (
                point[0] + placement[0] + solid_translation[0],
                point[1] + placement[1] + solid_translation[1],
            )
            for point in points
        )
        base = placement[2] + solid_translation[2]
        area = _polygon_area(footprint)
        return IfcSpaceRecord(
            entity_id=entity_id,
            number=number,
            long_name=_step_string(args[7]),
            footprint_xy_m=footprint,
            base_elevation_m=base,
            height_m=height,
            area_m2=area,
            volume_m3=area * height,
            source_path=str(self.path),
            source_sha256=self.source_sha256,
        )

    def extract(
        self, space_numbers: Optional[Iterable[str]] = None
    ) -> Mapping[str, IfcSpaceRecord]:
        """Return requested spaces by room number, rejecting missing/duplicates."""

        requested = (
            {str(value) for value in space_numbers}
            if space_numbers is not None
            else None
        )
        records: Dict[str, IfcSpaceRecord] = {}
        for entity_id, (entity_type, args) in self.entities.items():
            if entity_type != "IFCSPACE" or len(args) < 3:
                continue
            number = _step_string(args[2])
            if requested is not None and number not in requested:
                continue
            if number in records:
                raise ConfigurationError(
                    "Duplicate IFC space number: {}".format(number)
                )
            records[number] = self._extract_space(entity_id, args)
        if requested is not None:
            missing = sorted(requested - set(records))
            if missing:
                raise ConfigurationError(
                    "Official IFC lacks requested spaces: {}".format(missing)
                )
        return records
