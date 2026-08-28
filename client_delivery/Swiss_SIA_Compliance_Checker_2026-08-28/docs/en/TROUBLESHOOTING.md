# Troubleshooting

## The launcher says no active project is available

Open and save the intended model in IESVE, then rerun
`Run_VE_Swiss_Compliance.py`.

## The interface opens for the wrong model

Close the interface, activate the correct saved VE project and rerun the
launcher. Do not copy evidence files between project folders.

## The report remains NOT_DETERMINED

Open **Project Evidence** and inspect all seven tabs. Then read the workbook
`INPUT REQUEST`, `CAPABILITY GUIDE`, `PREFLIGHT`, `ALERTS` and
`ASSUMPTIONS LIMITS` sheets. Missing evidence is expected to remain
`NOT_DETERMINED`.

## An accepted row returns to pending

At least one required identity, value, date or source is missing or invalid.
Complete the row with real reviewed information; do not bypass the validation.

## Reports do not reflect recent model changes

Run a fresh annual ApacheSim simulation, confirm that the selected APS belongs
to the current model state, then regenerate the report.

## Excel or PDF cannot be replaced

Close the earlier workbook/PDF and rerun. Reports are timestamped, but an open
file or report directory can still interfere with post-generation opening.

## Model Viewer capture fails

Open Model Viewer, frame the building, return to the client interface and try
again. Use **Choose existing file** only with an authorised image of the exact
analysed model.

## Characters or accents display incorrectly

Use the maintained launcher and files from this complete delivery. Do not save
CSV evidence in a legacy ANSI encoding; use the evidence editor or UTF-8 CSV.

## A Python dependency is reported missing

Run inside IESVE 2025 first. The workflow relies on the Python environment
embedded with VE. Do not install packages into the system Python or modify the
IES installation without IES support approval. Record the exact traceback and
IESVE build number for support.
