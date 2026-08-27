# AI use and governance

Status date: 27 August 2026
Scope: Swiss SIA compliance checker, IESVE VEScripts and SIA 4010 evidence tooling

## Executive statement

Artificial intelligence was used as a software-development assistant during the
project. It is **not** part of the shipped compliance runtime. The maintained
Python application has no OpenAI, Anthropic or other LLM inference dependency,
does not send a client model to an AI service, and does not ask a model to decide
whether a building or simulation tool complies with SIA requirements.

The application produces deterministic calculations, evidence-readiness states
and reports. Missing evidence remains missing, `NOT_CHECKABLE` never becomes a
pass, and only an authorised human reviewer or the relevant SIA body can accept
evidence or issue an official validation/certification decision.

## AI systems evidenced by the repository

Project records show work assisted by:

- OpenAI Codex, for repository inspection, implementation, refactoring, tests,
  troubleshooting, documentation, translation and Git handover;
- Anthropic Claude/Claude Code, for earlier audits, implementation sessions,
  structured prompts and handover work.

The historical records are retained in `CLAUDE.md`, `docs/CLAUDE_REFERENCE.md`,
`docs/project/CODEX_TO_CLAUDE_HANDOFF.md`, `docs/project/CODEX_PROMPTS.md`,
`docs/project/PROMPTS_CLAUDE_FIN_MVP.md` and the Git history. They describe
assistance and workflow; they are not evidence that AI output is correct.

## Activities for which AI was used

| Activity | Typical AI contribution | Required control |
|---|---|---|
| Repository audit | Locate code, tests, duplicated or obsolete paths | Verify findings against files and Git |
| Python/VEScript implementation | Draft and refactor bounded changes | Review diff and run pure-Python tests |
| IESVE troubleshooting | Interpret tracebacks and propose probes | Execute in VE 2025 and require read-back |
| Test design | Add regression and fail-closed tests | Ensure tests reflect a sourced requirement |
| Documentation | Draft guides, handovers and explanations | Human review for accuracy and audience |
| Translation | Prepare EN/FR/DE/IT UI/report strings | Native or competent reviewer checks wording |
| Normative research | Find candidate public sources and questions | Use only authorised primary evidence |
| Communication support | Draft questions and e-mails | Named sender reviews and sends them |

## Activities AI is not authorised to perform

AI output must never be used alone to:

- invent a normative value, tolerance, source, test criterion or VE API field;
- approve a client evidence declaration or sign as the reviewer;
- claim SIA certification, software accreditation or legal compliance;
- change a failed/not-checkable result merely for a demonstration;
- redistribute licensed standards or client data without authorisation;
- publish, merge, push, alter repository visibility or contact a third party
  without an explicit human instruction;
- replace an IESVE runtime read-back with a mocked Python result.

## Human accountability

The person accepting evidence in the wizard remains accountable for the source,
date, scope and interpretation. IES engineering owns software review and release
approval. The SIA validation authority owns official acceptance of the SIA 4010
campaign. AI product names must never appear in a reviewer or certifier field.

For every material AI-assisted change, the expected chain is:

1. identify the exact source or observed runtime behaviour;
2. make a bounded change;
3. inspect the diff;
4. run the relevant automated tests;
5. run an IESVE capability/read-back check when VE state is involved;
6. preserve the result, limitation and unresolved question in Git/evidence;
7. obtain human review before a release or external claim.

## Data handling and privacy

- Do not paste credentials, access tokens or private keys into an AI session.
- Use only an IES-approved enterprise AI account for client, employee or
  licensed content.
- A client VE model, APS file or licensed standard must not be uploaded unless
  IES policy and the relevant rights explicitly permit it.
- The repository contains 60 Outlook messages authorised for continuity. They
  may contain personal/internal data and must be handled according to
  `docs/project/emails/README.md`.
- Public availability of the entire repository requires a separate rights and
  privacy review; authorisation to retain useful e-mails does not automatically
  license the tracked SIA PDFs or the software itself.
- Do not assume that an AI provider may train on submitted project data. Confirm
  the organisation's current service terms and data controls before use.

## Reproducibility and auditability

AI conversations are supporting context, not the reproducible build record. The
reproducible record consists of source files, frozen reference-data provenance,
checksums, tests, runtime receipts, reports and Git commits. A later maintainer
must be able to validate a result without access to the original AI conversation.

When AI proposes a source-derived constant, place the authority, extraction
method and checksum in the relevant binding/audit file. When it proposes a VE
mutation, qualify the setter and persistence in a disposable project before any
use in a client project.

## Runtime architecture statement

The production dependency list contains deterministic Python packages such as
Pydantic, pandas and openpyxl. No OpenAI/Anthropic SDK or LLM endpoint is part of
the runtime. If a future maintainer adds an AI feature, it must be treated as a
new architecture and governance decision, with at least:

- an ADR defining purpose, inputs, outputs and failure behaviour;
- privacy/security/legal review;
- explicit user consent and clear UI disclosure;
- deterministic validation around any generated content;
- no authority to emit a compliance/certification verdict;
- cost, availability, model-version and retention controls;
- tests for prompt injection, data leakage and unavailable-service behaviour.

## Suggested disclosure text

> AI-assisted development tools were used to support coding, testing,
> troubleshooting and documentation. The delivered application does not use an
> AI model at runtime and does not delegate compliance decisions to AI. Results
> are deterministic technical assessments subject to evidence and human review;
> they are not an official SIA certificate.

## Safe continuation workflow with AI

1. Start from `main` with a clean worktree.
2. Read `CLAUDE.md`, `docs/CLAUDE_REFERENCE.md` and the final handover.
3. Give the AI one concrete outcome, named files and a completion criterion.
4. Ask for diagnosis before mutation when the cause is uncertain.
5. Preserve unrelated work and never edit frozen references by hand.
6. Require tests and report exact commands/results.
7. Run VE-specific steps manually inside IESVE 2025.
8. Have an IES colleague review material normative/runtime changes.
9. Commit a coherent task with a traceable message.

This document records how AI was used; it is not an approval of any particular
AI service for future IES confidential work. That approval remains with the IES
security, legal and data-governance owners.
