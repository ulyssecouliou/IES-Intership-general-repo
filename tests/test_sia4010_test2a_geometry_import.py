"""Pure-Python guards for the Test 2A geometry-import launcher."""

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import scripts.probes.Run_VE_SIA4010_Test2A_Import_Geometry as launcher

ROOT = Path(__file__).resolve().parents[1]


class _OpeningSurface:
    def __init__(self, count):
        self.count = count

    def get_openings(self):
        return [object() for _ in range(self.count)]


class _Body:
    def __init__(self, opening_counts):
        self.surfaces = [_OpeningSurface(count) for count in opening_counts]

    def get_surfaces(self):
        return self.surfaces


def test_opening_count_reads_all_body_surfaces():
    count, errors = launcher._opening_count([_Body([0, 1]), _Body([1, 0])])
    assert count == 2
    assert errors == []


def test_geometry_contract_requires_exact_case_and_passing_checks():
    project = ROOT / ".codex_tmp" / "test2a_geometry_contract"
    if project.exists():
        shutil.rmtree(project)
    directory = project / launcher.GEOMETRY_DIRECTORY
    directory.mkdir(parents=True)
    try:
        gbxml = directory / launcher.GEOMETRY_FILENAME
        gbxml.write_text("<gbXML/>\n", encoding="utf-8")
        audit = directory / launcher.GEOMETRY_AUDIT_FILENAME
        audit.write_text(
            json.dumps(
                {
                    "variant": "test_2A",
                    "case_id": "2A",
                    "geometry_validation": {
                        "status": "PASS",
                        "checks": {"x": True},
                    },
                    "gbxml_path": str(gbxml),
                }
            ),
            encoding="utf-8",
        )
        actual_gbxml, actual_audit, payload = launcher._load_geometry_contract(project)
        assert actual_gbxml == gbxml
        assert actual_audit == audit
        assert payload["case_id"] == "2A"
    finally:
        if project.exists():
            shutil.rmtree(project)


def test_bodies_traverses_all_models():
    first = _Body([])
    second = _Body([])
    project = SimpleNamespace(
        models=[
            SimpleNamespace(get_bodies=lambda _include: [first]),
            SimpleNamespace(get_bodies=lambda _include: [second]),
        ]
    )
    assert launcher._bodies(project) == [first, second]


def test_prior_receipt_allows_readback_without_a_second_import():
    project = ROOT / ".codex_tmp" / "test2a_prior_import"
    if project.exists():
        shutil.rmtree(project)
    reports = project / launcher.REPORT_DIRECTORY
    reports.mkdir(parents=True)
    try:
        gbxml = project / "cell.gbxml"
        gbxml.write_text("<gbXML/>\n", encoding="utf-8")
        report = reports / "sia4010_test2a_geometry_import_20260825_000000.json"
        report.write_text(
            json.dumps(
                {
                    "prepared_geometry": {
                        "gbxml_sha256": launcher._sha256(gbxml),
                    },
                    "import_call": {"forme_retenue": "native enum"},
                    "readback": {"body_count": 1, "opening_count": 2},
                }
            ),
            encoding="utf-8",
        )
        receipt = launcher._prior_import_receipt(project, gbxml)
        assert receipt is not None
        assert receipt["path"] == str(report)
        assert receipt["original_import_call"]["forme_retenue"] == "native enum"
    finally:
        if project.exists():
            shutil.rmtree(project)
