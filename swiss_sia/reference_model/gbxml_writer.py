"""Deterministic, version-configurable gbXML serializer for IESVE import."""

from pathlib import Path
from typing import Optional, Union
from xml.etree import ElementTree as ET

from .compliance_config import ParameterRegistry
from .domain import GeometryModel, Polygon3D, SurfaceType


GBXML_NAMESPACE = "http://www.gbxml.org/schema"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
ET.register_namespace("", GBXML_NAMESPACE)
ET.register_namespace("xsi", XSI_NAMESPACE)


def _qname(name: str) -> str:
    """Return a name qualified with the configured gbXML namespace."""

    return "{{{}}}{}".format(GBXML_NAMESPACE, name)


def _child(parent: ET.Element, name: str, text: Optional[object] = None, **attrs) -> ET.Element:
    """Append and return one namespaced XML child element."""

    element = ET.SubElement(parent, _qname(name), attrs)
    if text is not None:
        element.text = str(text)
    return element


def _polyloop(parent: ET.Element, polygon: Polygon3D) -> ET.Element:
    """Append planar geometry for one surface or opening polygon."""

    planar = _child(parent, "PlanarGeometry")
    polyloop = _child(planar, "PolyLoop")
    for point in polygon.vertices:
        cartesian = _child(polyloop, "CartesianPoint")
        _child(cartesian, "Coordinate", "{:.9f}".format(point.x))
        _child(cartesian, "Coordinate", "{:.9f}".format(point.y))
        _child(cartesian, "Coordinate", "{:.9f}".format(point.z))
    return planar


def _closed_shell(parent: ET.Element, faces) -> None:
    """Append all face polygons defining a closed space shell."""

    shell = _child(parent, "ClosedShell")
    for face in faces:
        polyloop = _child(shell, "PolyLoop")
        for point in face.vertices:
            cartesian = _child(polyloop, "CartesianPoint")
            _child(cartesian, "Coordinate", "{:.9f}".format(point.x))
            _child(cartesian, "Coordinate", "{:.9f}".format(point.y))
            _child(cartesian, "Coordinate", "{:.9f}".format(point.z))


def _indent(element: ET.Element, level: int = 0) -> None:
    """Apply deterministic human-readable indentation to an XML tree."""

    spacing = "\n" + level * "  "
    child_spacing = "\n" + (level + 1) * "  "
    if len(element):
        if not element.text or not element.text.strip():
            element.text = child_spacing
        for child in element:
            _indent(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = spacing
    if level and (not element.tail or not element.tail.strip()):
        element.tail = spacing


class GbxmlWriter:
    """Serialize the pure geometry contract without embedding thermal values."""

    def __init__(self, parameters: ParameterRegistry):
        """Initialize the serializer with a validated parameter registry."""

        self.parameters = parameters

    def to_element(self, model: GeometryModel) -> ET.Element:
        """Build the complete gbXML element tree for a geometry model."""

        root = ET.Element(
            _qname("gbXML"),
            {
                "temperatureUnit": "C",
                "lengthUnit": "Meters",
                "areaUnit": "SquareMeters",
                "volumeUnit": "CubicMeters",
                "useSIUnitsForResults": "true",
                "version": str(self.parameters.value("gbxml_schema_version")),
                "SurfaceReferenceLocation": "InteriorSurface",
            },
        )
        campus = _child(root, "Campus", id="{}_CAMPUS".format(model.identifier))
        location = _child(campus, "Location")
        _child(location, "Name", self.parameters.value("weather_station") or "UNCONFIRMED_LOCATION")
        latitude = self.parameters.value("site_latitude_degrees")
        longitude = self.parameters.value("site_longitude_degrees")
        if latitude is not None:
            _child(location, "Latitude", latitude)
        if longitude is not None:
            _child(location, "Longitude", longitude)
        _child(location, "CADModelAzimuth", model.north_axis_degrees)

        building = _child(
            campus,
            "Building",
            id=model.identifier,
            buildingType=model.building_type,
        )
        _child(building, "Name", model.name)
        _child(building, "Area", "{:.9f}".format(model.floor_area_m2))
        for space in model.spaces:
            space_element = _child(
                building,
                "Space",
                id=space.identifier,
                zoneIdRef=space.zone_identifier,
            )
            _child(space_element, "Name", space.name)
            _child(space_element, "Area", "{:.9f}".format(space.floor_area_m2))
            _child(space_element, "Volume", "{:.9f}".format(space.volume_m3))
            shell_geometry = _child(
                space_element,
                "ShellGeometry",
                id="{}_SHELL".format(space.identifier),
                unit="Meters",
            )
            _closed_shell(shell_geometry, space.shell_faces)

        for surface in model.surfaces:
            surface_element = _child(
                campus,
                "Surface",
                id=surface.identifier,
                surfaceType=surface.surface_type.value,
            )
            _child(surface_element, "Name", surface.identifier)
            for space_id in surface.adjacent_space_ids:
                _child(surface_element, "AdjacentSpaceId", spaceIdRef=space_id)
            _polyloop(surface_element, surface.polygon)
            for opening in surface.openings:
                opening_element = _child(
                    surface_element,
                    "Opening",
                    id=opening.identifier,
                    openingType=opening.opening_type.value,
                    coordinatesAbsolute="true",
                )
                _child(opening_element, "Name", opening.identifier)
                _polyloop(opening_element, opening.polygon)

        # Zone definitions are intentionally skeletal: setpoints, gains,
        # schedules and flows are assigned from a source-traced VE template.
        for space in model.spaces:
            zone = _child(root, "Zone", id=space.zone_identifier)
            _child(zone, "Name", space.zone_identifier)
        return root

    def to_bytes(self, model: GeometryModel) -> bytes:
        """Serialize a geometry model as deterministic UTF-8 XML bytes."""

        root = self.to_element(model)
        _indent(root)
        return ET.tostring(root, encoding="utf-8", xml_declaration=True)

    def write(self, model: GeometryModel, path: Union[str, Path]) -> Path:
        """Write serialized geometry and return its resolved output path."""

        output_path = Path(path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(self.to_bytes(model))
        return output_path
