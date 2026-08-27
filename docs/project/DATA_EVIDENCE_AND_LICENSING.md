# Data, evidence, privacy and licensing

Status date: 27 August 2026

## Purpose

This document tells a maintainer what data exists, what is authoritative, what
may be generated again, and what must not be published or copied without a
rights decision. It is an engineering inventory, not legal advice.

## Data classes

| Class | Examples | Canonical treatment |
|---|---|---|
| Source code/config | `swiss_sia/`, `config/`, launchers | Git `main` |
| Frozen reference data | `refs/reference-data/` | Generated from bound source; checksum/audit required |
| Traceability | `traceability/`, validation JSON | Git; preserve source and signature status |
| Evidence templates | `templates/evidence/` | Git; copied to active project before reviewer editing |
| Client evidence | reviewer CSV/JSON, brief, approvals | Active client project; do not mix projects |
| Runtime evidence | VE read-back, APS evaluation, receipts | Project `sia4010_artifacts/`; immutable once cited |
| Generated deliverables | PDF/XLSX/HTML/ZIP | Rebuildable output; usually ignored by Git |
| Correspondence | 60 Outlook `.msg` files | Git archive authorised for continuity; personal/internal data |
| Licensed/third-party material | SIA standards, external workbooks | Restrict and verify redistribution rights |
| Customer models/results | VE folders, APS, IFC/gbXML | Keep outside public source unless contractually authorised |

## Correspondence archive

`docs/project/emails/` contains 60 Outlook messages (50,252,800 bytes at final
audit). They include exchanges with the SIA validation authority and internal
stakeholders. The project owner explicitly authorised their inclusion in this
private IES handover repository for continuity.

This does not remove privacy obligations. Preserve originals, do not edit or
re-export casually, and re-evaluate public retention if repository ownership,
employment context or data-protection requirements change. See the directory
README for thread names and handling guidance.

## Tracked third-party documents

The final audit found 11 tracked PDFs, including duplicate repository copies of
SIA 380/2 and SIA 4010:

- `references/standards/SIA 380-2-2022 FR.pdf`;
- `references/standards/SIA 4010-2023 FR.pdf`;
- `refs/SIA-380-2-2022.pdf`;
- `refs/SIA-4010-2023.pdf`;
- IESVE API/class-structure PDFs;
- BESTEST/NREL material and other project PDFs.

It also found tracked ISO/BESTEST spreadsheets and several IES/client-facing
Word/PowerPoint files. Presence in Git is not evidence of a right to make them
public. Before changing repository visibility, the IES legal/licensing owner
must classify every third-party binary and either:

1. approve public redistribution in writing;
2. replace it with a public authoritative link plus checksum/provenance;
3. keep the repository private; or
4. remove it from current Git and, if public exposure must be prevented, purge
   it from the complete Git history using a reviewed migration plan.

Deleting a file in a new commit does **not** remove it from earlier Git history.
Do not rewrite shared history without owner approval, backups, collaborator
coordination and new clone instructions.

## Private internal datasets committed for handover

The owner confirmed that the repository remains private and is shared only with
authorised IES collaborators. The official SIA 4010 campaign folder, bounded VE
validation dataset, controlled EN 16798 workbook, complete `sia4010_evidence/`
tree, generated-weather derivations and canonical readiness artifact are
therefore versioned. See `INTERNAL_DATASET_INVENTORY.md`.

Their inclusion removes dependencies on the departing contributor's workstation.
It does not create public redistribution rights or convert historical data into
evidence for a new client.

## Files intentionally not committed

The repository ignore policy excludes or should exclude:

- active/disposable VE project folders and APS results stored outside this repo;
- generated reports and evidence packs unless explicitly selected as a release
  record;
- local dependency/caching/test directories;
- Microsoft Office lock files;
- credentials and local AI/tool settings.

Their absence is not an accidental loss when provenance, owner and retrieval
instructions are recorded. A handover must never copy a licensed source merely
to make a package appear complete.

## Evidence hierarchy

Use evidence in this order:

1. authorised normative/authority source;
2. controlled extraction/binding with checksum;
3. exact model input and VE read-back;
4. APS/raw output and deterministic comparison;
5. named reviewer declaration for non-VE assumptions;
6. generated report presentation.

A report, AI explanation or screenshot cannot replace missing upstream
evidence. A `.msg` answer is useful authority correspondence, but its scope and
sender must be read rather than inferred from the filename.

## Project-local evidence rule

Client evidence belongs with the active VE project. The program must derive the
project folder dynamically and never use an absolute path to a developer's
Desktop/Documents folder. Evidence from the internal golden model must not be
reused as if it described a client model.

## Integrity and retention

- Use Git object integrity for repository files.
- Record SHA-256 for external source bindings and delivery manifests.
- Never alter a runtime receipt after it has been cited; create a new dated run.
- Keep a recoverable backup before replacing reviewer-edited evidence.
- Keep the final handover tag and canonical `main` commit.
- Store client models/results according to IES retention and access policy, not
  in a personal account after handover.

## Public-release decision gate

The repository returned HTTP 404 to anonymous requests at final audit and was
private/access-restricted. It must remain restricted until all of the following
are complete:

- IES confirms the owner/organisation and maintainers;
- a software licence is selected and committed;
- SIA/ISO/IES/third-party redistribution rights are decided;
- personal/internal `.msg` exposure is re-confirmed by the accountable owner;
- customer/confidential content and secrets are audited;
- history-purge requirements are decided;
- security reporting and branch protection are configured.

The URL will not change merely because visibility changes, but access rights and
legal consequences will.

## Questions for IES owners

1. Which IES organisation should own the repository after Ulysse's departure?
2. Who are the primary and backup maintainers?
3. Which software licence is approved?
4. May each tracked SIA/ISO/IES PDF/spreadsheet be redistributed publicly?
5. Is public retention of the correspondence archive approved under IES privacy
   policy, or should it move to restricted document storage?
6. Where must client VE/APS/evidence packages be retained?
7. Is a full Git-history rewrite required before any public release?
