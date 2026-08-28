"""Authoritative and project source register used in generated audits."""

from typing import Any, Dict


def build_source_register() -> Dict[str, Dict[str, Any]]:
    """Return the authoritative source index embedded in every report."""

    return {
        "IESVE_API_2023": {
            "title": "VE 2023 VEScript User Guide",
            "local_path": "references/iesve/VEScripts.pdf",
            "relevant_sections": {
                "gbxml_import": "6.1.9, PDF page 143",
                "body_assignment": "6.1.27, PDF pages 195-197",
                "cdb": "6.1.28-6.1.32, PDF pages 198-206",
                "location_weather": "6.1.36 and 6.1.47, PDF pages 213-214 and 246-247",
                "model": "6.1.38, PDF pages 216-217",
                "thermal_template": "6.1.46, PDF pages 242-245",
            },
            "authority": "Integrated Environmental Solutions Limited",
        },
        "IESVE_API_2025_ASSET_CREATION": {
            "title": "VE 2025 Python API - project and thermal-template creation methods",
            "url": "https://help.iesve.com/ve2025/6_1_42_1_methods_defined_here.htm",
            "relevant_sections": {
                "project_assets": "create_profile, create_casual_gain, create_air_exchange, create_apache_system, create_thermal_template",
                "thermal_template": "https://help.iesve.com/ve2025/6_1_48_1_methods_defined_here.htm",
                "cdb_project": "https://help.iesve.com/ve2025/6_1_33_1_methods_defined_here.htm",
            },
            "authority": "Integrated Environmental Solutions Limited",
            "compatibility_note": "Create mode is capability-gated because these project creation methods are not documented in the bundled VE 2023 guide.",
        },
        "SIA_380_2_2022_FR": {
            "title": "SIA 380/2:2022 Calculs energetiques des batiments",
            "local_path": "references/standards/SIA 380-2-2022 FR.pdf",
            "relevant_sections": {
                "referenced_standards": "PDF pages 5, 8, 12, 19, 24-32",
                "reference_project_envelope": "Table 3, PDF pages 36-37",
                "solar_protection": "Table 10, PDF page 46",
                "summer_simulation": "Normative Annex C, Table 11, PDF page 59",
            },
            "authority": "Swiss Society of Engineers and Architects (SIA)",
        },
        "SIA_4010_2023_FR": {
            "title": "SIA 4010:2023 Guide relatif a la norme SIA 380/2",
            "local_path": "references/standards/SIA 4010-2023 FR.pdf",
            "relevant_sections": {
                "official_test_files": "Sections 2.5 and 4.3-4.4, PDF pages 8 and 47",
                "seven_tests": "Section 4.2, Table 62, PDF page 46",
                "validation_classes": "Section 4.5, Table 63, PDF page 48",
                "procedure": "Section 4.6, PDF pages 48-49",
            },
            "authority": "Swiss Society of Engineers and Architects (SIA)",
        },
        "GBXML_SCHEMA": {
            "title": "GreenBuildingXML schema (configured serialization profile)",
            "url": "https://www.gbxml.org/Schema_Archived_GreenBuildingXML_gbXML",
            "relevant_sections": [
                "Building",
                "Space",
                "ShellGeometry",
                "Surface",
                "Opening",
                "Zone",
            ],
            "authority": "gbXML.org",
        },
    }
