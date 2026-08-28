# Package contents

## Client entry points

- `Run_VE_Swiss_Compliance.py` — maintained client launcher;
- `Run_VE_Swiss_Compliance_Remediation_Probe.py` — optional read-only diagnosis;
- `Prepare_Client_SIA_Weather.py` — optional audited weather conversion;
- `Run_VE_Verify_Client_SIA_Weather.py` — optional weather read-back in VE.

Experimental builders, SIA 4010 campaign launchers, disposable-model mutation
scripts and automated test suites are intentionally excluded. They belong to
the internal development repository, not to the client operating surface.

## Runtime folders

- `swiss_sia/` — deterministic analysis, evidence and report code;
- `ui/` — shared interface and report-view components;
- `config/` — runtime configuration and company-profile files;
- `assets/` — IES report branding assets;
- `refs/reference-data/` — machine-readable, source-traced implementation data;
- `templates/evidence/` — blank evidence templates;
- `docs/` — client/operator documentation;
- `training/` — video, narration and presentation material.

## Deliberately excluded

- official SIA standards and other licensed PDFs;
- client VE projects, APS files and generated reports;
- private correspondence and internal handover e-mails;
- source-code tests, development probes and disposable mutation scripts;
- credentials, API keys and local machine paths;
- SIA 4010 validation claims or attestations.

The client supplies its own authorised model, results and controlled source
documents. The software creates project-local evidence and reports during use.
