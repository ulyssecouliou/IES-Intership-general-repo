"""Read-only qualification probe for the Test 1 APS hourly convention."""

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

for module_name in tuple(sys.modules):
    if module_name == "swiss_sia.reference_model" or module_name.startswith(
        "swiss_sia.reference_model."
    ):
        del sys.modules[module_name]


def _sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def _latest_evaluated_aps(project_path):
    reports = sorted(
        (project_path / "sia4010_artifacts" / "results").glob(
            "SIA4010_test_1_*_evaluation.json"
        ),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    )
    for report_path in reports:
        try:
            report = json.loads(report_path.read_text(encoding="utf-8"))
            aps_path = Path(
                str((report.get("source_evidence") or {}).get("aps_path") or "")
            )
        except (OSError, ValueError):
            continue
        if aps_path.is_file():
            return aps_path, report_path
    raise RuntimeError("No evaluated Test 1 APS result was found in this project")


def _weather_temperature_candidates(variables):
    candidates = []
    for variable in variables:
        level = str(
            variable.get("model_level") or variable.get("level") or ""
        ).strip().lower()
        name = str(variable.get("aps_varname") or variable.get("name") or "")
        display = str(variable.get("display_name") or name)
        text = "{} {}".format(name, display).casefold()
        if level != "w" or "temperature" not in text:
            continue
        if not any(token in text for token in ("dry", "outside", "external")):
            continue
        candidates.append(variable)
    return candidates


def run():
    """Compare APS weather output with the exact project EPW without mutation."""

    try:
        import iesve  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Run this script from the IESVE VEScripts editor") from exc

    from swiss_sia.reference_model.sia4010.hour_convention import (
        build_hour_convention_diagnostic,
        read_epw_dry_bulb_c,
    )
    from swiss_sia.reference_model.sia4010.model_scenario import ModelScenario
    from swiss_sia.simulation_results import (
        convert_aps_series_to_metric,
        get_available_variables,
        get_results_per_hour,
        read_weather_result,
    )

    project = iesve.VEProject.get_current_project()
    if project is None:
        raise RuntimeError("Open the saved Test 1 project first")
    project_path = Path(str(getattr(project, "path", "") or ""))
    scenario_path = project_path / "sia_model_scenario.json"
    scenario = ModelScenario.load(scenario_path)
    if scenario.variant != "test_1":
        raise RuntimeError("The active scenario is not a Test 1 case")
    epw_path = project_path / "DRYCOLD_IESVE.epw"
    if not epw_path.is_file():
        raise RuntimeError("Project-local DRYCOLD_IESVE.epw is missing")
    aps_path, evaluation_path = _latest_evaluated_aps(project_path)

    # ResultsReader resolves files from the active project's Vista directory;
    # the documented and already qualified contract passes the APS basename.
    results = iesve.ResultsReader.open(aps_path.name)
    try:
        reader_time_metadata = {
            "first_day": int(getattr(results, "first_day", -1)),
            "last_day": int(getattr(results, "last_day", -1)),
            "results_per_day": int(getattr(results, "results_per_day", 0)),
            "plot_data_offset_secs": int(
                getattr(results, "plot_data_offset_secs", 0)
            ),
            "plot_year": int(getattr(results, "plot_year", 0)),
            "simulation_year": int(getattr(results, "simulation_year", 0)),
            "first_weekday_plot_year": int(
                getattr(results, "first_weekday_plot_year", 0)
            ),
        }
        variables = get_available_variables(results)
        candidates = _weather_temperature_candidates(variables)
        if not candidates:
            raise RuntimeError(
                "APS exposes no unique weather dry-bulb temperature candidate"
            )
        candidate_reports = []
        for variable in candidates:
            aps_name = str(
                variable.get("aps_varname") or variable.get("name") or ""
            )
            display = str(variable.get("display_name") or aps_name)
            binding = (
                aps_name,
                display,
                "w",
                str(variable.get("resolved_metric_unit") or ""),
                variable.get("resolved_metric_divisor", 1.0),
                variable.get("resolved_metric_offset", 0.0),
            )
            raw = read_weather_result(results, aps_name, display)
            metric = convert_aps_series_to_metric(raw, binding)
            if not metric:
                continue
            diagnostic = build_hour_convention_diagnostic(
                read_epw_dry_bulb_c(epw_path),
                metric,
                get_results_per_hour(results),
            )
            candidate_reports.append(
                {
                    "aps_varname": aps_name,
                    "display_name": display,
                    "model_level": "w",
                    "metric_unit": binding[3],
                    "diagnostic": diagnostic,
                }
            )
    finally:
        close = getattr(results, "close", None)
        if callable(close):
            close()

    if not candidate_reports:
        raise RuntimeError("Weather candidates returned no readable APS series")
    candidate_reports.sort(
        key=lambda item: item["diagnostic"]["best_alignment"][
            "root_mean_square_difference_c"
        ]
    )
    selected = candidate_reports[0]
    report = {
        "schema_version": "1.0",
        "status": selected["diagnostic"]["status"],
        "project": {
            "name": str(getattr(project, "name", "") or ""),
            "path": str(project_path),
        },
        "scenario": scenario.to_dict(),
        "scenario_sha256": _sha256(scenario_path),
        "aps": {"path": str(aps_path), "sha256": _sha256(aps_path)},
        "results_reader_time_metadata": reader_time_metadata,
        "evaluation": {
            "path": str(evaluation_path),
            "sha256": _sha256(evaluation_path),
        },
        "epw": {"path": str(epw_path), "sha256": _sha256(epw_path)},
        "selected_weather_variable": selected,
        "candidate_count": len(candidate_reports),
        "candidate_variables": candidate_reports,
        "claim_guardrail": (
            "Read-only time-index evidence. No compliance verdict and no ISO "
            "result re-indexing is authorized by this probe alone."
        ),
        "compliance_claim_allowed": False,
    }
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = (
        project_path
        / "sia4010_artifacts"
        / "diagnostics"
        / "sia4010_aps_hour_convention_{}.json".format(stamp)
    )
    _write_json(report_path, report)
    best = selected["diagnostic"]["best_alignment"]
    print("READ-ONLY SIA 4010 APS HOUR CONVENTION: {}".format(report["status"]))
    print("Project: {}".format(report["project"]["name"]))
    print("Case: test_1/{}".format(scenario.case_id))
    print("APS weather variable: {}".format(selected["display_name"]))
    print(
        "ResultsReader plot-data offset: {:+d} second(s)".format(
            reader_time_metadata["plot_data_offset_secs"]
        )
    )
    print(
        "APS calendar: first_day={}, last_day={}, plot_year={}, simulation_year={}".format(
            reader_time_metadata["first_day"],
            reader_time_metadata["last_day"],
            reader_time_metadata["plot_year"],
            reader_time_metadata["simulation_year"],
        )
    )
    print("Best APS index offset: {:+d} hour(s)".format(best["aps_index_offset_hours"]))
    print(
        "Best temperature RMSE: {:.6f} degC".format(
            best["root_mean_square_difference_c"]
        )
    )
    print("Report: {}".format(report_path))
    print("No VE model, weather, APS or comparison result was changed.")
    return report_path


if __name__ == "__main__":
    run()
