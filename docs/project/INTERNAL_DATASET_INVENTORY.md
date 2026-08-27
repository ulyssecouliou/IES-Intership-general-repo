# Private IES dataset inventory

Status date: 27 August 2026

The repository is a private handover archive available only to authorised IES
collaborators. The following internal datasets are intentionally versioned so a
new maintainer does not depend on Ulysse's workstation.

| Dataset | Audit size | Purpose | Handling |
|---|---:|---|---|
| `docs/project/emails/` | 60 messages / 50.25 MB | Authority and internal correspondence | Private IES evidence |
| `SIA_4010_geteilter_Link/` | 57 files / 117.61 MB | Test 1–7 specifications, result workbooks and example building | Licensed/internal campaign source |
| `VE - Validation for Swiss Building Regs/` | 10 files / 50.78 MB | Bounded prior validation models/results | Internal validation dataset |
| `sia4010_evidence/` | 194 files / 15.35 MB | Source audits, authority decisions, runtime limitations and campaign evidence | Preserve provenance and status |
| `generated_weather/` | 55 files / 29.94 MB | EPW candidates and derivation receipts | Derived; retain audit JSON |
| `references/standards/en16798/` controlled workbook | 1 workbook / 3.12 MB | EN 16798 validation reference | Private/internal use with provenance |
| `sia4010_artifacts/templates/` | 1 small JSON | Canonical hybrid-readiness record | Technical handover evidence |

Sizes are informational audit values; Git object hashes are the canonical
integrity mechanism after commit.

## Intentionally not versioned

- Python/tool caches, temporary directories and Office lock files;
- repetitive generated reports and logs under `reports/`;
- transient outputs under `outputs/`, including delivery ZIPs and Git bundles;
- disposable VE project folders and APS files that live outside this repository;
- local Codex/Claude settings and credentials.

Those exclusions prevent workstation noise and recursive archives. Rebuildable
delivery artifacts are described by the handover receipt and are supplied
separately when required.

## Rules

- Keep the repository private unless IES completes a separate publication and
  licensing review.
- Do not treat inclusion as permission to redistribute a normative document.
- Do not replace a source workbook or message without preserving its history.
- Never reuse the bounded validation dataset as evidence for a different client.
- Record new external inputs with origin, date, scope, checksum and authority.
