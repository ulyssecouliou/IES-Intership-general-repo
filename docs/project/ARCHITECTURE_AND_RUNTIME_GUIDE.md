# Architecture and runtime guide

## System boundary

The repository supports two related but legally and technically distinct
workflows:

1. a SIA 380/2 technical assessment of an active client IESVE model;
2. preparation and evidence collection for SIA 4010 validation of simulation
   software through controlled reference cases.

The first assesses a building model. The second assesses the behaviour of the
simulation tool. Their evidence, statuses and claims must not be merged.

## Maintained architecture

```text
IESVE 2025 / VEScript launcher
        |
        v
swiss_sia application and orchestration
        |
        +-- data_extractor / VE gateway ----> active VE model + APS
        |
        +-- evidence manager --------------> project-local reviewer CSV/JSON
        |
        +-- deterministic criteria --------> findings and fail-closed verdicts
        |
        +-- PDF / Excel / HTML writers ----> timestamped reports
        |
        `-- reference_model/sia4010 -------> disposable test-case workflows
```

### `swiss_sia/`

This is the production application. It owns the client workflow, extraction,
evidence wizard, criteria, report context, translations and report generation.
New client-facing functionality belongs here.

### `swiss_sia/reference_model/`

This package owns reference-model construction, controlled VE access and SIA
4010 preparation/qualification workflows. Native IESVE operations must be
isolated behind explicit gateway or launcher boundaries and verified by
read-back.

### `engine/` and `ve_adapter/`

These are independent build/cross-check tools for reference data and verdict
recomputation. They are not the production client runtime. Their purity provides
an independent check that normative computation does not silently depend on an
IESVE session.

### `ui/`

This contains retained UI components and tests. The production entry point still
routes through `swiss_sia`; do not assume every historical module under `ui/`
is active.

### `core/`

This is historical/dead architecture for current production purposes. Preserve
it while references/tests still depend on it, but do not add new production
features without an explicit architecture decision.

## Client assessment data flow

1. The VEScript launcher obtains the active VE project.
2. Extraction reads rooms, templates, constructions, gains, ventilation,
   systems and available APS variables without inventing unavailable values.
3. Project evidence is loaded from the active model folder, not from another
   client project or an absolute developer path.
4. Deterministic criteria combine observed values, scope, source quality and
   reviewer evidence.
5. Governance converts the result into `PASS`, `FAIL`, `NOT_CHECKABLE`, missing
   evidence or advisory states without optimistic coercion.
6. PDF/XLSX/HTML writers receive one shared report context so claims and counts
   remain aligned across formats.
7. Reports state that they are technical assessments, not official SIA
   certificates.

## SIA 4010 validation flow

1. Select an official class, variant and case from controlled configuration.
2. Install/verify authorised external inputs and their checksums.
3. Create or open a fresh disposable VE project.
4. Prepare the exact case scenario and geometry.
5. Probe native runtime capability before mutation.
6. Apply only qualified setters; read back immediately and after reload when
   persistence matters.
7. Capture/review the exact template or diagnostic equivalent.
8. Run guarded ApacheSim with a qualified weather/input configuration.
9. Extract the APS output scope and compare only against an available official
   acceptance criterion.
10. Record results and blockers without converting diagnostic evidence into an
    official pass.

## State and evidence locations

- Source/configuration: repository-relative under `config/`, `refs/`,
  `references/`, `templates/` and `traceability/`.
- Client evidence: under the active VE project folder.
- VE runtime receipts: under that disposable/project model's
  `sia4010_artifacts/` tree.
- Generated reports/release packages: `reports/` and `outputs/`; normally not
  canonical source and often ignored by Git.
- Raw correspondence: `docs/project/emails/`.

Absolute developer paths may appear in historical audits/receipts, but runtime
logic must derive the repository or active project path.

## Internationalisation

English is the default interface/report language. French, German and Italian
are supported. User-visible text should use translation keys or the maintained
translation layer; raw keys and mojibake must never reach a delivered report.
French accents and German/Italian characters must be retained as UTF-8.

## Failure design

The architecture is deliberately fail-closed:

- unavailable input -> missing/not-checkable, not zero;
- unsupported API field -> capability blocker, not assumed setter success;
- unverified persistence -> blocker;
- missing official criterion -> diagnostic result only;
- incomplete reviewer declaration -> pending, not accepted;
- report disagreement -> release blocker;
- AI suggestion -> untrusted until source/test/read-back review.

## Extending the system

For a new criterion or test:

1. bind the source and exact scope;
2. define typed/internal data structures;
3. implement deterministic logic outside VE access;
4. add unit/boundary/missing-evidence tests;
5. add a VE adapter/capability probe only if needed;
6. verify mutation and persistence in a disposable project;
7. update all report formats and translations;
8. update traceability and handover/status documentation;
9. run the full release procedure.

More detailed historical architecture rationale remains in
`ARCHITECTURE_380-2_vs_4010.md`, `SWISS_REFERENCE_MODEL_ARCHITECTURE.md` and
`../ADR-001-architecture-MSP.md`.
