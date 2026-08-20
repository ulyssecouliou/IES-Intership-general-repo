"""Tests for the project-local client report interface contract."""

from __future__ import annotations

import struct
import unittest
import zlib
from pathlib import Path

from pypdf import PdfReader

from swiss_sia.client_compliance_ui import (
    compliance_palette,
    validate_client_context,
)
from swiss_sia.client_report_context import (
    ClientReportContext,
    load_client_report_context,
    report_directory,
    save_client_report_context,
)
from swiss_sia.company_profile import CompanyProfile
from swiss_sia.compliance_report_pdf import render_compliance_report_pdf


ROOT = Path(__file__).resolve().parents[1]
TMP_ROOT = ROOT / ".codex_tmp" / "client_report_interface_tests"


def _write_rgb_png(path: Path, width: int = 10, height: int = 6) -> Path:
    """Write a tiny RGB PNG accepted by the dependency-free PDF writer."""

    raw = bytearray()
    for row in range(height):
        raw.append(0)
        for column in range(width):
            raw += bytes((column * 20 % 256, row * 30 % 256, 120))

    def chunk(tag: bytes, body: bytes) -> bytes:
        return (
            struct.pack(">I", len(body))
            + tag
            + body
            + struct.pack(">I", zlib.crc32(tag + body) & 0xFFFFFFFF)
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(bytes(raw)))
        + chunk(b"IEND", b"")
    )
    return path


class ClientContextTests(unittest.TestCase):
    def test_required_fields_are_explicit(self) -> None:
        self.assertEqual(
            validate_client_context(ClientReportContext()),
            "client_and_project_required",
        )
        self.assertIsNone(
            validate_client_context(
                ClientReportContext(client_name="Client", project_name="Project")
            )
        )

    def test_unusable_report_image_is_rejected_before_generation(self) -> None:
        self.assertEqual(
            validate_client_context(
                ClientReportContext(
                    client_name="Client",
                    project_name="Project",
                    client_logo_path=str(TMP_ROOT / "missing-logo.png"),
                )
            ),
            "client_ui_image_error",
        )

    def test_context_and_selected_images_are_saved_inside_the_project(self) -> None:
        root = TMP_ROOT / "context_case"
        project = root / "VE Project"
        project.mkdir(parents=True, exist_ok=True)
        source_logo = _write_rgb_png(root / "logo.png")
        source_view = _write_rgb_png(root / "viewer.png", 20, 12)
        stored = save_client_report_context(
            project,
            ClientReportContext(
                client_name="Client",
                project_name="Project",
                weather_file="weather.fwt",
                solar_shading="YES",
                client_logo_path=str(source_logo),
                model_viewer_image_path=str(source_view),
            ),
        )
        loaded = load_client_report_context(project)
        self.assertEqual(loaded.client_name, "Client")
        self.assertEqual(loaded.weather_file, "weather.fwt")
        self.assertEqual(loaded.solar_shading, "YES")
        self.assertTrue(Path(stored.client_logo_path).is_file())
        self.assertTrue(Path(stored.model_viewer_image_path).is_file())
        self.assertTrue(Path(stored.client_logo_path).is_relative_to(project))
        self.assertEqual(report_directory(project), project / "SIA Compliance Reports")

    def test_palette_exposes_only_compliance_statuses(self) -> None:
        self.assertEqual(compliance_palette("COMPLIANT")[2], "verdict_compliant")
        self.assertEqual(compliance_palette("NOT_COMPLIANT")[2], "verdict_not_compliant")
        self.assertEqual(compliance_palette("anything")[2], "verdict_not_determined")


class ClientPdfContextTests(unittest.TestCase):
    def test_pdf_contains_client_weather_shading_logo_and_viewer_image(self) -> None:
        root = TMP_ROOT / "pdf_case"
        root.mkdir(parents=True, exist_ok=True)
        logo = _write_rgb_png(root / "client.png")
        viewer = _write_rgb_png(root / "viewer.png", 20, 12)
        output = root / "client_report.pdf"
        context = ClientReportContext(
            client_name="Client Alpine SA",
            project_name="School North",
            project_address="1 Test Street, Lausanne",
            report_reference="SIA-26-014",
            prepared_by="U. Engineer",
            weather_file="CHE_GVE_2060_RCP85_DRY.fwt",
            solar_shading="YES",
            client_logo_path=str(logo),
            model_viewer_image_path=str(viewer),
        )
        render_compliance_report_pdf(
            output,
            project_label="fallback",
            rooms_data=[],
            sia3802_results={},
            sia4010_results={},
            profile=CompanyProfile(name="IES"),
            language="en",
            scope="sia3802",
            report_context=context,
        )
        reader = PdfReader(str(output))
        text = reader.pages[0].extract_text()
        full_text = "\n".join(page.extract_text() for page in reader.pages)
        self.assertIn("Client Alpine SA", text)
        self.assertIn("School North", text)
        self.assertIn("CHE_GVE_2060_RCP85_DRY.fwt", text)
        self.assertIn("YES", text)
        self.assertNotIn("SIA 4010", full_text)
        images = reader.pages[0]["/Resources"]["/XObject"]
        self.assertGreaterEqual(len(images), 2)


if __name__ == "__main__":
    unittest.main()
