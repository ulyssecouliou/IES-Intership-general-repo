# `swiss_sia`

Production Python package for the Swiss SIA Compliance Checker.

## Modules

- `app.py`: orchestration entry point used by the VE launcher.
- `config.py`: SIA values, source references, requirement matrix and output settings.
- `data_extractor.py`: defensive IESVE API extraction layer.
- `model_analyzer.py`: normalized room/surface/opening/system data model.
- `rule_engine.py`: generic rule and alert engine.
- `sia380_checker.py`: automated and partial SIA 380/2 checks.
- `sia4010_checker.py`: SIA 4010 readiness and evidence scanning.
- `health_score.py`: automated indicator and model health scoring.
- `excel_report.py`: professional Excel workbook generation.
- `simulation_results.py`: APS/Vista result-reading helpers.

The repository root keeps thin launchers only. New production code should live
in this package.

