# Security policy

## Reporting

Do not open a public issue containing a vulnerability, credential, client model,
personal correspondence or licensed source. Report it privately to the current
IES repository owner and IES security/data-governance contact through approved
internal channels. The permanent contact must be added when repository
ownership is transferred.

Include the affected commit/version, reproduction steps, impact, data involved
and any temporary containment already applied. Do not attach customer or
licensed files unless the recipient and channel are approved.

## Supported version

Until IES defines a formal release policy, only the current protected `main`
branch and the latest annotated release/handover tag are supported.

## High-priority incidents

- committed or exposed credentials/secrets;
- public exposure of client, personal or licensed content;
- a report that overstates compliance/certification;
- unsafe mutation of an active VE client model;
- evidence accepted without reviewer authority;
- dependency or generated-document vulnerability affecting delivery.

For accidental public data exposure, restrict access first, preserve an audit
record, notify IES security/legal/data owners and plan a coordinated history
purge if required. Deleting a file only from the latest commit is insufficient.

## Secure engineering expectations

- Keep secrets and local tool settings out of Git.
- Treat all model/evidence/import paths as untrusted input.
- Use project-relative paths and validate destructive targets.
- Keep missing evidence fail-closed.
- Pin/review delivery dependencies and run the full quality gates.
- Qualify VE mutations in disposable models with read-back/persistence checks.
- Follow the AI and data-governance documents under `docs/project/`.
