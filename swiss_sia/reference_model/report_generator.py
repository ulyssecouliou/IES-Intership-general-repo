"""JSON, Excel-ready CSV, and JSONL audit report generation."""

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Union

from .compliance_config import ParameterRegistry
from .domain import GeometryModel, ModelSnapshot
from .results import AuditEvent, ValidationResult, worst_status
from .source_register import build_source_register


@dataclass(frozen=True)
class ReportArtifacts:
    """Paths of all machine-readable artifacts emitted by one run."""

    report_json: Path
    audit_jsonl: Path
    parameters_csv: Path
    validations_csv: Path
    spaces_csv: Path
    surfaces_csv: Path
    openings_csv: Path
    constructions_csv: Path
    templates_csv: Path

    def to_dict(self) -> Dict[str, str]:
        """Return artifact paths as a serializable mapping."""

        return {
            name: str(value)
            for name, value in self.__dict__.items()
        }


def _json_cell(value: Any) -> str:
    """Convert structured values into stable spreadsheet cell text."""

    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


class ReportGenerator:
    """Produces stable filenames suitable for automation and review."""

    def __init__(self, output_folder: Union[str, Path]):
        """Initialize stable report and Excel-ready output folders."""

        self.output_folder = Path(output_folder)
        self.excel_folder = self.output_folder / "excel_ready"
        self.output_folder.mkdir(parents=True, exist_ok=True)
        self.excel_folder.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _atomic_json(path: Path, payload: Any) -> None:
        """Write JSON through a temporary file before atomic replacement."""

        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        temporary.replace(path)

    @staticmethod
    def _write_csv(path: Path, fieldnames: Sequence[str], rows: Iterable[Dict[str, Any]]) -> None:
        """Write one Excel-ready UTF-8 CSV through atomic replacement."""

        temporary = path.with_suffix(path.suffix + ".tmp")
        with temporary.open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for row in rows:
                writer.writerow({name: _json_cell(row.get(name)) for name in fieldnames})
        temporary.replace(path)

    def generate(
        self,
        run_metadata: Dict[str, Any],
        parameters: ParameterRegistry,
        validations: List[ValidationResult],
        audit_events: List[AuditEvent],
        geometry: Optional[GeometryModel] = None,
        snapshot: Optional[ModelSnapshot] = None,
        additional_data: Optional[Dict[str, Any]] = None,
    ) -> ReportArtifacts:
        """Generate canonical JSON, JSONL audit, and Excel-ready tables."""

        artifacts = ReportArtifacts(
            report_json=self.output_folder / "reference_model_report.json",
            audit_jsonl=self.output_folder / "reference_model_audit.jsonl",
            parameters_csv=self.excel_folder / "parameters.csv",
            validations_csv=self.excel_folder / "validation_results.csv",
            spaces_csv=self.excel_folder / "spaces.csv",
            surfaces_csv=self.excel_folder / "surfaces.csv",
            openings_csv=self.excel_folder / "openings.csv",
            constructions_csv=self.excel_folder / "constructions.csv",
            templates_csv=self.excel_folder / "thermal_templates.csv",
        )
        parameter_payload = parameters.to_dict()
        report_payload = {
            "report_schema_version": "1.0.0",
            "overall_status": worst_status(validations).value,
            "run_metadata": run_metadata,
            "source_register": build_source_register(),
            "parameters": parameter_payload,
            "placeholders": [
                parameter.to_dict() for parameter in parameters.placeholders()
            ],
            "validation_results": [result.to_dict() for result in validations],
            "model_assumptions": geometry.assumptions if geometry else {},
            "generated_geometry": geometry.to_dict() if geometry else None,
            "ve_model_snapshot": snapshot.to_dict() if snapshot else None,
            "audit_events": [event.to_dict() for event in audit_events],
            "additional_data": additional_data or {},
            "claim_guardrail": (
                "This artifact reports readiness and evidence state. It is not an "
                "official SIA compliance certificate or SIA 4010 validation result."
            ),
        }
        self._atomic_json(artifacts.report_json, report_payload)

        temporary_audit = artifacts.audit_jsonl.with_suffix(".jsonl.tmp")
        with temporary_audit.open("w", encoding="utf-8") as handle:
            for event in audit_events:
                handle.write(
                    json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True)
                    + "\n"
                )
        temporary_audit.replace(artifacts.audit_jsonl)

        self._write_csv(
            artifacts.parameters_csv,
            (
                "name",
                "category",
                "value",
                "units",
                "description",
                "source",
                "source_locator",
                "validation_range",
                "required_for_generation",
                "compliance_relevant",
                "comparison_only",
                "is_placeholder",
            ),
            parameter_payload.values(),
        )
        self._write_csv(
            artifacts.validations_csv,
            (
                "control_id",
                "category",
                "status",
                "message",
                "object_id",
                "evidence",
                "source",
            ),
            (result.to_dict() for result in validations),
        )

        space_rows = []
        surface_rows = []
        opening_rows = []
        if geometry:
            for space in geometry.spaces:
                space_rows.append(space.to_dict())
            for surface in geometry.surfaces:
                row = surface.to_dict()
                row["openings"] = [opening.identifier for opening in surface.openings]
                surface_rows.append(row)
                for opening in surface.openings:
                    opening_row = opening.to_dict()
                    opening_row["parent_surface_id"] = surface.identifier
                    opening_rows.append(opening_row)
        self._write_csv(
            artifacts.spaces_csv,
            (
                "identifier",
                "name",
                "zone_identifier",
                "bounds",
                "floor_area_m2",
                "volume_m3",
                "shell_faces",
            ),
            space_rows,
        )
        self._write_csv(
            artifacts.surfaces_csv,
            (
                "identifier",
                "surface_type",
                "area_m2",
                "adjacent_space_ids",
                "construction_parameter",
                "openings",
                "polygon",
            ),
            surface_rows,
        )
        self._write_csv(
            artifacts.openings_csv,
            (
                "identifier",
                "parent_surface_id",
                "opening_type",
                "area_m2",
                "construction_parameter",
                "polygon",
            ),
            opening_rows,
        )

        construction_rows = []
        template_rows = []
        if snapshot:
            for construction in snapshot.constructions:
                construction_rows.append(
                    {
                        "identifier": construction.identifier,
                        "reference": construction.reference,
                        "category": construction.category,
                        "layer_count": construction.layer_count,
                        "material_ids": construction.material_ids,
                        "u_value_w_m2k": construction.u_value_w_m2k,
                        "valid": construction.valid,
                        "properties": construction.properties,
                    }
                )
            for template in snapshot.templates:
                template_rows.append(
                    {
                        "handle": template.handle,
                        "name": template.name,
                        "standard": template.standard,
                        "room_conditions": template.room_conditions,
                        "system_data": template.system_data,
                        "gains": template.gains,
                        "air_exchanges": template.air_exchanges,
                    }
                )
        self._write_csv(
            artifacts.constructions_csv,
            (
                "identifier",
                "reference",
                "category",
                "layer_count",
                "material_ids",
                "u_value_w_m2k",
                "valid",
                "properties",
            ),
            construction_rows,
        )
        self._write_csv(
            artifacts.templates_csv,
            (
                "handle",
                "name",
                "standard",
                "room_conditions",
                "system_data",
                "gains",
                "air_exchanges",
            ),
            template_rows,
        )
        return artifacts
