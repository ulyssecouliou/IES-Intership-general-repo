> **Note:** Translated from French original. See [PROJECT_PLAN.md](PROJECT_PLAN.md) for the source document.

# SIA 4010 Validation Navigator for IESVE -- Project Plan

> Objective: a deployable tool within VEScripts (IESVE's VE) that verifies
> SIA 4010 validation classes for a VE model, with a polished interface
> and quality documentation. Target: MSP (Minimum **Sellable** Product)
> as fast as possible, without sacrificing reliability.

---

## 1. Doctrine (read before any code)

The number one risk in this project is not coding -- it is producing results
that are *wrong but plausible*. That is precisely the concern you have about
the Codex work. The entire organisation below exists to make it impossible
to hide falsehoods.

Three non-negotiable rules:

1. **Truth comes from published reference values, never from the model.**
   Each SIA 4010 test has reference results (SIA evaluation Excel workbooks;
   for Test 1, the ASHRAE 140 / EN ISO 52016-1 ranges). The validation
   engine is "correct" only when it reproduces those values.
2. **Traceability from clause to code to test.** Every implemented check cites
   the exact article from SIA 380/2:2022, SIA 4010 or the relevant EN standard.
   No "orphan" checks.
3. **Hard/pure separation.** The validation logic is **pure** Python, testable
   outside VE, with no dependency on `iesve`. VE access is isolated in a thin
   adapter. This allows the engine to be tested in CI without a VE licence.

Nothing is "done" until the `qa-auditor` agent has signed the corresponding
traceability matrix.

---

## 2. Target architecture (4 layers)

> **WARNING: OUTDATED -- superseded by ADR-001 (2026-07-30) and the 2026-08-16 audit.**
> This diagram is an initial plan, not the current state. **(D2)** the local web
> app from "Layer 4" is **removed**: the UI is a Tkinter dialog within VE. **Production
> is consolidated into `swiss_sia/`**; `engine/`+`ve_adapter/`+`ui/` are
> tooling/legacy, not the client runtime. The VE 2025 probe also invalidates
> the "Python 3.4" constraint (actual: 3.12.3). See
> `docs/ADR-001-architecture-MSP.md` and `docs/project/AUDIT_COMPLET_2026-08-16.md`.
> The diagram below is kept as a historical record.

```
+-  Layer 4: NAVIGATOR (UI) --------------------------------+
|  Local web app (HTML/JS): Classes -> Tests -> quantities,  |
|  deltas vs reference, red/green, drill-down, export.       |
+---------------^--------------------------------------------+
                | JSON (results + verdicts)
+-  Layer 3: VALIDATION ENGINE (pure Python) ----------------+
|  Implements the logic of each test + tolerances +          |
|  verdict per class. 100% testable outside VE. Cites norm.  |
+---------------^-------------------^------------------------+
                | normalised inputs   | reference values
+-  Layer 2: VE ADAPTER --------+  +-  Layer 1bis: REF. DATA -----+
|  VEScript via the `iesve` API |  |  SIA eval Excel + specs      |
|  -> normalised JSON (model,   |  |  -> frozen, versioned JSON.  |
|  systems, .aps results).      |  +-------------------------------+
|  Caution: depends on API docs.|
+-------------------------------+
```

**Blocking architecture decision (Phase 0)**: how VEScripts hosts the
"navigator". Recommended approach = the VEScript extracts data then **generates
and opens a local web app** (enables a "very good interface", impossible
with a native VE GUI). To be confirmed upon receipt of the IESVE API docs
(surface of the `iesve` module, embedded Python version, access to `.aps`
results / ApacheHVAC).

---

## 3. Phases (sequencing, no fictitious dates)

### Phase 0 -- Foundations & grounding in truth *(short, top priority)*
- Ingest all reference materials into the repository (`/refs`), frozen and versioned.
- **Audit of existing Codex work**: honest inventory of what exists, what is
  correct, what must be discarded. Deliverable = `AUDIT.md`. (qa-auditor + norm-analyst)
- Resolve the VEScripts hosting question using API docs. (ve-adapter-engineer)
- Repository skeleton + CI that runs the pure engine tests **without VE**.

### Phase 1 -- Vertical slice: Test 1 / Class 1A end-to-end *(the heart of the MSP)*
The thinnest path that crosses all 4 layers and proves the full pipeline:
VE extraction -> engine -> comparison against ASHRAE 140 refs -> display in
the navigator. When this works, the product skeleton exists.

### Phase 2 -- Classes 1 & 2 complete (Tests 2 & 3)
Solar protection (SIA 387/4) + lighting. Highest and most achievable value
(confirmed: this is what Lesosai validated first).

### Phase 3 -- System classes (Tests 4->6, then 7)
ApacheHVAC extraction, EN 16798 comparisons, then the big Test 7. Incremental,
each test behind a QA sign-off. **Hardest point to isolate early**: the detailed
heat pump method SIA 384/3 at hourly time-step (ch. 3.4.3.5.2).

### Phase 4 -- Hardening & documentation
Deployable packaging within VEScripts, user guide, methodological note with
complete traceability matrix, FAQ.

---

## 4. Team (Claude Code sub-agents) and model allocation

| Agent (file) | Model | Mission | Why this model |
|---|---|---|---|
| `norm-analyst` | **opus** | Reads SIA/EN, produces machine-readable specs + tolerances + citations | A misreading of the standard is costly downstream |
| `qa-auditor` | **opus** | Verifies implementation against the standard, maintains the traceability matrix | Independence = antidote to the Codex doubt |
| `ve-adapter-engineer` | **sonnet** | `iesve` layer / VEScript extraction | Robust implementation |
| `validation-engine-engineer` | **sonnet** | Pure engine + unit tests | Implementation + testing rigour |
| `ui-engineer` | **sonnet** | The "navigator" (local web app) | Polished front-end |
| `reference-data-engineer` | **haiku->sonnet** | Parses SIA eval Excel + specs -> JSON | Mechanical; escalate model if logic needed |
| `docs-writer` | **haiku** | User & methodology documentation | Structured writing, low cost |

Policy: main session (orchestrator) on **opus** but kept lightweight;
implementation delegated to **sonnet**; mechanical tasks to **haiku**. Sub-agents
run in their own context and can run in parallel; note that a heavily
"sub-agent" workflow can consume ~7x the tokens of a single-thread session --
so parallelise *independent work*, serialise risk-prone steps
(extraction <-> engine <-> audit).

---

## 5. Definition of Done (per SIA test)
A test is delivered only when ALL of the following are true:
- [ ] Machine-readable spec produced by `norm-analyst` with article citations.
- [ ] Reference data frozen in `/refs/reference-data/` (versioned).
- [ ] Pure engine implemented + unit tests that reproduce the reference within tolerance.
- [ ] VE adapter extracts the required quantities (or documented stub if VE unavailable).
- [ ] Navigator displays the test with deltas and verdict.
- [ ] Traceability matrix updated and **signed by `qa-auditor`**.
- [ ] User documentation entry added.
