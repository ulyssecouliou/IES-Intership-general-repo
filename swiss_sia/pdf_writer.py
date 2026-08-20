"""Minimal dependency-free PDF writer for the SIA compliance report.

The IESVE Python runtime ships no PDF library, and adding one would have to be
qualified against that runtime first, so this module writes PDF 1.4 directly
using the standard library only. It covers exactly what the compliance report
needs: text in the built-in Helvetica family, vector lines and rectangles, and
embedded JPEG or PNG images for a company logo.

Coordinates are expressed from the top-left corner in millimetres, which matches
how the report is laid out; the writer converts to PDF points and the PDF
bottom-left origin. Text is encoded as WinAnsi (cp1252) so French, German and
Italian accents render without embedding a font.
"""

import struct
import zlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

MM_TO_PT = 72.0 / 25.4
A4_MM = (210.0, 297.0)

FONT_REGULAR = "Helvetica"
FONT_BOLD = "Helvetica-Bold"
FONT_OBLIQUE = "Helvetica-Oblique"
_FONT_RESOURCES = {
    FONT_REGULAR: "F1",
    FONT_BOLD: "F2",
    FONT_OBLIQUE: "F3",
}

# Approximate Helvetica advance widths (per 1000 units) for the ASCII range,
# used only to measure text for centring and truncation. Non-ASCII characters
# fall back to the average width, which is accurate enough for layout.
_AVERAGE_WIDTH = 500
_WIDTHS = {
    " ": 278, "!": 278, '"': 355, "#": 556, "$": 556, "%": 889, "&": 667,
    "'": 191, "(": 333, ")": 333, "*": 389, "+": 584, ",": 278, "-": 333,
    ".": 278, "/": 278, ":": 278, ";": 278, "<": 584, "=": 584, ">": 584,
    "?": 556, "@": 1015, "[": 278, "\\": 278, "]": 278, "^": 469, "_": 556,
    "`": 333, "{": 334, "|": 260, "}": 334, "~": 584,
}
for _character in "0123456789":
    _WIDTHS[_character] = 556
for _character, _width in zip(
    "abcdefghijklmnopqrstuvwxyz",
    (556, 556, 500, 556, 556, 278, 556, 556, 222, 222, 500, 222, 833,
     556, 556, 556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500),
):
    _WIDTHS[_character] = _width
for _character, _width in zip(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ",
    (667, 667, 722, 722, 667, 611, 778, 722, 278, 500, 667, 556, 833,
     722, 778, 667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611),
):
    _WIDTHS[_character] = _width


def text_width_mm(text: str, size_pt: float, bold: bool = False) -> float:
    """Return the approximate rendered width of one string, in millimetres."""

    total = sum(_WIDTHS.get(character, _AVERAGE_WIDTH) for character in str(text))
    if bold:
        total *= 1.06  # bold advances are slightly wider than the regular face
    return (total / 1000.0) * size_pt / MM_TO_PT


def truncate_to_width(text: str, size_pt: float, max_mm: float, bold: bool = False) -> str:
    """Return the text shortened with an ellipsis so it fits the given width."""

    value = str(text)
    if text_width_mm(value, size_pt, bold) <= max_mm:
        return value
    ellipsis = "..."
    while value and text_width_mm(value + ellipsis, size_pt, bold) > max_mm:
        value = value[:-1]
    return value + ellipsis


def wrap_to_width(
    text: str, size_pt: float, max_mm: float, bold: bool = False
) -> List[str]:
    """Return the text split into lines that each fit within ``max_mm``.

    Used for statements that must stay readable in full - a scope or limitation
    clause is never truncated, because dropping its end would change its meaning.
    """

    words = str(text).split()
    if not words:
        return [""]
    lines: List[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = current + " " + word
        if text_width_mm(candidate, size_pt, bold) <= max_mm:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def _escape(text: str) -> bytes:
    """Return a PDF string body, WinAnsi encoded with the reserved bytes escaped."""

    encoded = str(text).encode("cp1252", errors="replace")
    for source, target in ((b"\\", b"\\\\"), (b"(", b"\\("), (b")", b"\\)")):
        encoded = encoded.replace(source, target)
    return encoded


def _number(value: float) -> str:
    """Return a compact fixed-point number acceptable to PDF operators."""

    return "{:.3f}".format(float(value)).rstrip("0").rstrip(".") or "0"


class ImageError(ValueError):
    """Raised when an image cannot be embedded without a decoding library."""


def _read_jpeg(data: bytes) -> Dict[str, Any]:
    """Return the PDF image dictionary for a JPEG, embedded without re-encoding."""

    index = 2
    while index < len(data) - 1:
        if data[index] != 0xFF:
            index += 1
            continue
        marker = data[index + 1]
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            index += 2
            continue
        segment_length = struct.unpack(">H", data[index + 2:index + 4])[0]
        if marker in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                      0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
            height, width = struct.unpack(">HH", data[index + 5:index + 9])
            components = data[index + 9]
            colour = {1: "/DeviceGray", 3: "/DeviceRGB", 4: "/DeviceCMYK"}.get(components)
            if colour is None:
                raise ImageError("Unsupported JPEG component count: {}".format(components))
            return {
                "width": width,
                "height": height,
                "colour_space": colour,
                "filter": "/DCTDecode",
                "decode_parms": None,
                "data": data,
            }
        index += 2 + segment_length
    raise ImageError("No JPEG frame header found")


def _read_png(data: bytes) -> Dict[str, Any]:
    """Return the PDF image dictionary for a PNG.

    The compressed scanlines are passed through unchanged: PDF understands the
    PNG per-scanline predictors natively through ``/DecodeParms``, so no pixel
    filtering has to be reimplemented here. Palette and alpha PNGs are refused
    rather than silently flattened.
    """

    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ImageError("Not a PNG file")
    width = height = bit_depth = colour_type = None
    idat = bytearray()
    offset = 8
    while offset < len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        chunk = data[offset + 4:offset + 8]
        body = data[offset + 8:offset + 8 + length]
        if chunk == b"IHDR":
            width, height, bit_depth, colour_type = struct.unpack(">IIBB", body[:10])
            interlace = body[12]
            if interlace:
                raise ImageError("Interlaced PNG is not supported")
        elif chunk == b"IDAT":
            idat += body
        elif chunk == b"IEND":
            break
        offset += 12 + length
    if width is None or not idat:
        raise ImageError("PNG has no image data")
    if bit_depth != 8:
        raise ImageError("Only 8-bit PNG is supported (got {})".format(bit_depth))
    colours = {0: 1, 2: 3}.get(colour_type)
    if colours is None:
        raise ImageError(
            "Only greyscale or RGB PNG is supported; palette and alpha PNGs must "
            "be exported as RGB or JPEG (colour type {})".format(colour_type)
        )
    return {
        "width": width,
        "height": height,
        "colour_space": "/DeviceGray" if colours == 1 else "/DeviceRGB",
        "filter": "/FlateDecode",
        "decode_parms": (
            "<< /Predictor 15 /Colors {} /BitsPerComponent 8 /Columns {} >>".format(
                colours, width
            )
        ),
        "data": bytes(idat),
    }


def load_image(path: Union[str, Path]) -> Dict[str, Any]:
    """Return the embeddable image dictionary for a JPEG or PNG file."""

    payload = Path(path).read_bytes()
    if payload[:2] == b"\xff\xd8":
        return _read_jpeg(payload)
    return _read_png(payload)


class PdfPage:
    """One page whose content is built with millimetre, top-left coordinates."""

    def __init__(self, document: "PdfDocument", width_mm: float, height_mm: float):
        """Bind the page to its document and record its size in millimetres."""

        self.document = document
        self.width_mm = width_mm
        self.height_mm = height_mm
        self._operations: List[str] = []

    # ---------------------------------------------------------------- helpers
    def _x(self, value_mm: float) -> float:
        """Convert a millimetre x coordinate to PDF points."""

        return value_mm * MM_TO_PT

    def _y(self, value_mm: float) -> float:
        """Convert a top-left millimetre y coordinate to PDF points."""

        return (self.height_mm - value_mm) * MM_TO_PT

    @staticmethod
    def _colour(rgb: Sequence[float]) -> str:
        """Return the three normalized components of an RGB colour."""

        return " ".join(_number(component) for component in rgb)

    # ----------------------------------------------------------------- drawing
    def text(
        self,
        x_mm: float,
        y_mm: float,
        value: str,
        size_pt: float = 9.0,
        bold: bool = False,
        italic: bool = False,
        colour: Sequence[float] = (0, 0, 0),
        align: str = "left",
        width_mm: Optional[float] = None,
    ) -> None:
        """Draw one line of text; ``y_mm`` is the text baseline from the top."""

        font = FONT_BOLD if bold else (FONT_OBLIQUE if italic else FONT_REGULAR)
        resource = _FONT_RESOURCES[font]
        self.document.used_fonts.add(font)
        start = x_mm
        if align in ("center", "right") and width_mm:
            rendered = text_width_mm(value, size_pt, bold)
            spare = max(0.0, width_mm - rendered)
            start = x_mm + (spare / 2.0 if align == "center" else spare)
        self._operations.append(
            "BT /{} {} Tf {} rg {} {} Td ({}) Tj ET".format(
                resource,
                _number(size_pt),
                self._colour(colour),
                _number(self._x(start)),
                _number(self._y(y_mm)),
                _escape(value).decode("latin-1"),
            )
        )

    def line(
        self,
        x1_mm: float,
        y1_mm: float,
        x2_mm: float,
        y2_mm: float,
        width_pt: float = 0.6,
        colour: Sequence[float] = (0, 0, 0),
    ) -> None:
        """Draw one straight stroked segment."""

        self._operations.append(
            "{} w {} RG {} {} m {} {} l S".format(
                _number(width_pt),
                self._colour(colour),
                _number(self._x(x1_mm)),
                _number(self._y(y1_mm)),
                _number(self._x(x2_mm)),
                _number(self._y(y2_mm)),
            )
        )

    def rect(
        self,
        x_mm: float,
        y_mm: float,
        width_mm: float,
        height_mm: float,
        fill: Optional[Sequence[float]] = None,
        stroke: Optional[Sequence[float]] = None,
        width_pt: float = 0.6,
    ) -> None:
        """Draw a rectangle, filled and/or stroked, from its top-left corner."""

        if fill is None and stroke is None:
            return
        parts = []
        if fill is not None:
            parts.append("{} rg".format(self._colour(fill)))
        if stroke is not None:
            parts.append("{} RG {} w".format(self._colour(stroke), _number(width_pt)))
        parts.append(
            "{} {} {} {} re".format(
                _number(self._x(x_mm)),
                _number(self._y(y_mm + height_mm)),
                _number(width_mm * MM_TO_PT),
                _number(height_mm * MM_TO_PT),
            )
        )
        if fill is not None and stroke is not None:
            parts.append("B")
        elif fill is not None:
            parts.append("f")
        else:
            parts.append("S")
        self._operations.append(" ".join(parts))

    def polygon(
        self,
        points_mm: Sequence[Tuple[float, float]],
        fill: Optional[Sequence[float]] = None,
        stroke: Optional[Sequence[float]] = None,
        width_pt: float = 0.6,
    ) -> None:
        """Draw a closed polygon through the given top-left millimetre points."""

        if len(points_mm) < 2 or (fill is None and stroke is None):
            return
        parts = []
        if fill is not None:
            parts.append("{} rg".format(self._colour(fill)))
        if stroke is not None:
            parts.append("{} RG {} w".format(self._colour(stroke), _number(width_pt)))
        first_x, first_y = points_mm[0]
        parts.append("{} {} m".format(_number(self._x(first_x)), _number(self._y(first_y))))
        for point_x, point_y in points_mm[1:]:
            parts.append("{} {} l".format(_number(self._x(point_x)), _number(self._y(point_y))))
        parts.append("h")
        if fill is not None and stroke is not None:
            parts.append("B")
        elif fill is not None:
            parts.append("f")
        else:
            parts.append("S")
        self._operations.append(" ".join(parts))

    def image(
        self, x_mm: float, y_mm: float, width_mm: float, height_mm: float, path
    ) -> None:
        """Draw a JPEG or PNG image stretched to the given top-left box."""

        name = self.document.register_image(path)
        self._operations.append(
            "q {} 0 0 {} {} {} cm /{} Do Q".format(
                _number(width_mm * MM_TO_PT),
                _number(height_mm * MM_TO_PT),
                _number(self._x(x_mm)),
                _number(self._y(y_mm + height_mm)),
                name,
            )
        )

    def image_contain(
        self,
        x_mm: float,
        y_mm: float,
        width_mm: float,
        height_mm: float,
        path: Union[str, Path],
    ) -> Tuple[float, float, float, float]:
        """Fit an image inside a box without cropping or changing its ratio.

        The fitted image is centred on both axes.  Returning its actual drawing
        box makes the geometry directly testable and lets callers align nearby
        content when needed.
        """

        image = self.document.image_info(path)
        source_width = float(image["width"])
        source_height = float(image["height"])
        if source_width <= 0 or source_height <= 0:
            raise ImageError("Image dimensions must be positive")
        source_ratio = source_width / source_height
        box_ratio = float(width_mm) / float(height_mm)
        if source_ratio >= box_ratio:
            draw_width = float(width_mm)
            draw_height = draw_width / source_ratio
        else:
            draw_height = float(height_mm)
            draw_width = draw_height * source_ratio
        draw_x = float(x_mm) + (float(width_mm) - draw_width) / 2.0
        draw_y = float(y_mm) + (float(height_mm) - draw_height) / 2.0
        self.image(draw_x, draw_y, draw_width, draw_height, path)
        return draw_x, draw_y, draw_width, draw_height

    def content(self) -> bytes:
        """Return the page content stream."""

        return "\n".join(self._operations).encode("latin-1")


class PdfDocument:
    """An A4 PDF document assembled in memory and written atomically."""

    def __init__(self, page_size_mm: Tuple[float, float] = A4_MM, title: str = ""):
        """Create an empty document with the given page size and title."""

        self.page_size_mm = page_size_mm
        self.title = title
        self.pages: List[PdfPage] = []
        self.used_fonts = set()
        self._images: Dict[str, Dict[str, Any]] = {}
        self._image_names: Dict[str, str] = {}

    def add_page(self) -> PdfPage:
        """Append and return a new page."""

        page = PdfPage(self, self.page_size_mm[0], self.page_size_mm[1])
        self.pages.append(page)
        return page

    def register_image(self, path) -> str:
        """Load an image once and return its PDF resource name."""

        key = str(Path(path).resolve())
        if key not in self._image_names:
            self._images[key] = load_image(path)
            self._image_names[key] = "Im{}".format(len(self._image_names) + 1)
        return self._image_names[key]

    def image_info(self, path: Union[str, Path]) -> Dict[str, Any]:
        """Return registered image metadata, loading the asset only once."""

        key = str(Path(path).resolve())
        self.register_image(path)
        return self._images[key]

    def save(self, path: Union[str, Path]) -> Path:
        """Write the document, atomically replacing any existing file."""

        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = self._render()
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_bytes(payload)
        temporary.replace(target)
        return target

    # ---------------------------------------------------------------- assembly
    def _render(self) -> bytes:
        """Return the complete PDF byte stream with a valid cross-reference table."""

        objects: List[bytes] = []

        def add(body: bytes) -> int:
            """Append one indirect object body and return its object number."""

            objects.append(body)
            return len(objects)

        font_numbers = {}
        for font in sorted(self.used_fonts) or [FONT_REGULAR]:
            font_numbers[font] = add(
                (
                    "<< /Type /Font /Subtype /Type1 /BaseFont /{} "
                    "/Encoding /WinAnsiEncoding >>"
                ).format(font).encode("latin-1")
            )
        image_numbers = {}
        for key, image in self._images.items():
            stream = image["data"]
            parts = [
                "<< /Type /XObject /Subtype /Image",
                "/Width {} /Height {}".format(image["width"], image["height"]),
                "/ColorSpace {}".format(image["colour_space"]),
                "/BitsPerComponent 8",
                "/Filter {}".format(image["filter"]),
            ]
            if image["decode_parms"]:
                parts.append("/DecodeParms {}".format(image["decode_parms"]))
            parts.append("/Length {} >>".format(len(stream)))
            image_numbers[key] = add(
                " ".join(parts).encode("latin-1")
                + b"\nstream\n"
                + stream
                + b"\nendstream"
            )

        # The page tree is written after every content and page object, so its
        # object number is known in advance: two objects per page, then itself.
        pages_number = len(objects) + 2 * len(self.pages) + 1
        page_numbers = []
        for page in self.pages:
            body = zlib.compress(page.content())
            content_number = add(
                "<< /Length {} /Filter /FlateDecode >>".format(len(body)).encode("latin-1")
                + b"\nstream\n"
                + body
                + b"\nendstream"
            )
            resources = ["/Font << {} >>".format(
                " ".join(
                    "/{} {} 0 R".format(_FONT_RESOURCES[font], number)
                    for font, number in sorted(font_numbers.items())
                )
            )]
            if image_numbers:
                resources.append(
                    "/XObject << {} >>".format(
                        " ".join(
                            "/{} {} 0 R".format(self._image_names[key], number)
                            for key, number in image_numbers.items()
                        )
                    )
                )
            page_numbers.append(
                add(
                    (
                        "<< /Type /Page /Parent {} 0 R /MediaBox [0 0 {} {}] "
                        "/Resources << {} >> /Contents {} 0 R >>"
                    ).format(
                        pages_number,
                        _number(self.page_size_mm[0] * MM_TO_PT),
                        _number(self.page_size_mm[1] * MM_TO_PT),
                        " ".join(resources),
                        content_number,
                    ).encode("latin-1")
                )
            )

        add(
            "<< /Type /Pages /Count {} /Kids [{}] >>".format(
                len(page_numbers),
                " ".join("{} 0 R".format(number) for number in page_numbers),
            ).encode("latin-1")
        )
        info_number = add(
            "<< /Title ({}) /Producer (Swiss SIA Compliance Checker) >>".format(
                _escape(self.title).decode("latin-1")
            ).encode("latin-1")
        )
        catalog_number = add(
            "<< /Type /Catalog /Pages {} 0 R >>".format(pages_number).encode("latin-1")
        )

        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        offsets = []
        for number, body in enumerate(objects, start=1):
            offsets.append(len(out))
            out += "{} 0 obj\n".format(number).encode("latin-1")
            out += body
            out += b"\nendobj\n"
        xref_offset = len(out)
        out += "xref\n0 {}\n".format(len(objects) + 1).encode("latin-1")
        out += b"0000000000 65535 f \n"
        for offset in offsets:
            out += "{:010d} 00000 n \n".format(offset).encode("latin-1")
        out += (
            "trailer\n<< /Size {} /Root {} 0 R /Info {} 0 R >>\nstartxref\n{}\n"
            "%%EOF\n".format(
                len(objects) + 1, catalog_number, info_number, xref_offset
            ).encode("latin-1")
        )
        return bytes(out)
