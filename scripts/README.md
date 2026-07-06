# `scripts`

Developer and diagnostic scripts.

## Folders

- `probes/`: VE API diagnostic probes used to discover real model data and
  refine extraction mappings.
- `quality/`: local release-quality checks for PDF traceability, SIA
  configuration, documentation entry points and latest Excel report smoke tests.
- `legacy/`: older exploratory scripts kept for reference. They are not part of
  the production compliance workflow.

The production Run-button workflow is `Run_VE_Swiss_Compliance.py` at the
repository root.

If the reviewer evidence CSV files need to be initialized from inside VE, run
`Prepare_SIA4010_Evidence_Folder.py` first. It copies project-named templates
into `sia4010_evidence/` without overwriting existing reviewer files.

Run the release validator outside VE before sharing a report/code snapshot:

```powershell
python -m pip install -r scripts/quality/requirements.txt
python scripts/quality/validate_release.py
```
