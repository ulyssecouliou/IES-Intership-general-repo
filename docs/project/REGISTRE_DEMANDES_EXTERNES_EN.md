> **Note:** Translated from French original. See [REGISTRE_DEMANDES_EXTERNES.md](REGISTRE_DEMANDES_EXTERNES.md) for the source document.

# External Requests Register — nothing is sent from this file

A single place for everything awaiting an external response. Nothing here is
sent automatically: the register exists so that no question gets lost and so
that a grouped mailing replaces three separate emails.

**Status as of 2026-08-20**: project decision — no paid standard will be
purchased. Requirements that depend exclusively on an absent standard remain
explicitly `NOT_CHECKABLE`/`PARTIAL`; they are neither reconstructed nor
presented as compliant. A licensed source provided later by IES or by a
reviewer can always be integrated.

---

## 1. To request from SIA (Prof. Gerhard Zweifel)

The drafted and verified message is
[`SIA_CORRESPONDANCE_ZWEIFEL_2026-08-12.md`](docs/project/SIA_CORRESPONDANCE_ZWEIFEL_2026-08-12.md).
Every statement in it is backed by the cell or file that proves it.

| # | Request | What it unblocks | Verified |
|---|---|---|---|
| S1 | Does the `Streubereich` min/max confirmed on 2026-08-10 apply to **Tests 4 and 6**, whose specifications contain **no** `Testkriterien` section (0 occurrences in full-text search)? | The distribution criterion for Tests 4, 6 and 7. Without a written answer, the distributions remain recorded without a verdict. | yes |
| S2 | The **awning control dynamics** of diagnostic test 2 E1: irradiance signal compared to the threshold, direction of the comparison, release rule, treatment of the state from one timestep to the next. And do the two VE thresholds `radiation_to_lower` / `radiation_to_raise` reproduce this rule? | **Case 1E**, the only Test 1 case carrying a pass/fail criterion. The device and its optical properties are already frozen; only the dynamics are missing. | yes |
| S3 | Report, not a question: `Resultaterfassung Test7.xlsx`, sheet `Zusammenfassung`, cells `W32` and `W33` carry `kW` in the quantity cell and `°C` on the unit row. The only block out of seventeen where the two diverge. | Nothing blocking. We keep the counts and leave the unit null. | yes, cell by cell |
| S4 | The remaining **SIA 2024** data sheets our matrix requires: auditorium, example building, restaurant 6.2, kitchen 6.4. | Tests 3 to 6 on those usage categories. Category 3.1 is already in hand and covers the entire 1A-to-1E chain. | yes |

| S5 | **CLOSED — no purchase.** Table 10 and the 2023 edition of SIA 387/4 will not be acquired by the project. We keep only Table 9 from the 2017 edition provided by Yiqiao Yang — see `refs/reference-data/sia-387-4-2017.blinds.json`. | The **twelve Test 3 cases** remain `NOT_CHECKABLE` as long as a controlled licensed link is not provided by IES or a reviewer. | project decision 2026-08-20 |
| S6 | **EN 16798-5-1 Annex D**, rotary heat-recovery model. Absent from the repository: this is not a transcription task, it is a document we do not have. A question of acquisition or licensing, possibly answerable internally at IES. | The delegated input `en16798_5_1_annex_d_rotary_recovery_model`, hence the **four Test 5 cases**. | yes |
| S7 | For **SIA 2024 category 3.1**, which days are the two weekly rest days and how are the **261 usage days** placed in the calculation year? The 24 hourly fractions are known, but this calendar convention does not appear in the extract received. | The native VE daily/weekly/yearly schedule without an invented assumption, required for Test 2A and for any generation that consumes these profiles directly. | yes |

**Do not send**: the "discrepancy" on the glazing Ug. It does not exist.
The documentation describes the same window under two families of standards —
0.646 under EN ISO 52022-3 reference conditions, 0.654 under ISO 15099 winter
conditions — and the specification uses the latter, to the exact digit. It was
our comparison error, recorded here so that it does not resurface.

---

## 1 bis. What can be completed **without waiting for any of these answers**

Established on 2026-08-13 by querying `case_registry` and the delegated-inputs manifest, not the documentation.

**The 24 cases still not implemented are blocked by VE bindings we have not written.** The codes say so: `VE_LIGHTING_CONTROL_BINDING_NOT_IMPLEMENTED` (12 cases), `VE_SOLAR_CONTROL_BINDING_NOT_IMPLEMENTED` (4), `VE_MULTIZONE_HVAC_BINDING_NOT_IMPLEMENTED` (4), then four bindings with one case each (1E, Tests 4, 6 and 7). Several also accumulate an external need listed below.

### The six normative Test 1 cases: nothing holds them back

| Done | Verified on |
|---|---|
| Generator present for all six | `generation_status` = `GUARDED_MUTATION_READY` (600) and `RUNTIME_QUALIFICATION_READY` (640, 600FF, 900, 940, 900FF) |
| APS extraction implemented for all six | `aps_evaluation_scope` = `REFERENCE_OUTPUTS_IMPLEMENTED` |
| **No** delegated input required | readiness = `NOT_REQUIRED` |
| **No** acceptance criterion, by specification | "Es gibt dafuer kein Abweichungskriterium" |

Their terminal state is therefore "results recorded", and it is reachable today. 640 and 600FF are already there. Remaining: requalify 600 after the CDB material correction, and three VE runs for 900, 940, 900FF. **VE work, on Ulysse's side, with no external dependency.**

### The four cases 1A to 1D: now executable in the campaign

Their delegated inputs are **already ready** (`READY_FOR_BINDING`, zero blocked), the chain is frozen in `refs/reference-data/test-1.diagnostics.ref.json` (43 fields captured, 0 to confirm), and **they have no acceptance criterion**. Their bundle, Fast Start routing, runtime qualification, simulation and hourly APS deliverable have been connected since 2026-08-13. They still need to be run in four disposable VE projects to produce real evidence. No external answer is needed to reach their terminal state.

Case **1E** is separate: its inputs are also ready, but the awning **dynamics** remain unknown (S2). It is generable, not judgeable.

### Tests 2 to 7: none is completable

Each accumulates an unwritten VE binding **and** at least one missing delegated input. Exact external residue per test:

| Test | VE binding (ours) | Missing inputs | Of which truly external |
|---|---|---|---|
| 2A-2D | solar control | IR emissivity | I1, or BESTEST route |
| 3A-3F | lighting control | SIA 387/4 Table 10; example-building awning detail | S5 only — the awning detail is in a document we hold, so transcription |
| 3G-3L | same | + 3K/3L authority clarification | S5 + clarification |
| 4 | HVAC topology | SIA 2024 auditorium data sheet; fan-curve digitisation | S4 only — the curve is in the specification |
| 5A-5D | multizone HVAC | SIA 2024 example-building data sheet; **EN 16798-5-1 Annex D**; fan curve | S4 + **S6** |
| 6 | ventilation sequence | two SIA 2024 data sheets; staged-control survey | S4 only |
| 7 | energy systems | heat-pump performance tables; PV precedence | tables probably transcribable; PV precedence = SIA authority |

---

## 2. Answerable internally, without email

| # | Question | Where to look | What it unblocks |
|---|---|---|---|
| I1 | What **infrared emissivities** (interior and exterior) for the opaque surfaces of the Chapter 7 test cell? And does the `opaque_solar_absorptance` of 0.6 apply to **both faces**? | **Not in the pages already captured.** See the detail below: the lead is elsewhere in ISO EN 52016-1:2017, outside pages 123-126. | The delegated input `iso52016_2017_chapter7_test_cell`, hence **Test 2A** and the entire chain of source-related cases. |

### Where to look, exactly

Corrected on 2026-08-13. The previous wording pointed to clauses 7.2.2.7
to 7.2.2.10: that was wrong, those pages have already been read and do not
answer the question.

**What the repository already knows.** `config/iso52016_chapter7_confirmed_inputs.json`
cites only pages **123, 124, 125 and 126**, and its
`unresolved_from_current_captures` block states plainly: "Numerical infrared
emittance value, because page 126 states only that a standard emittance is
implicitly assumed". Someone has therefore already looked, and page 126 says
only that a standard emittance is *implicitly assumed*.

**What this implies.** If the standard implicitly assumes it, it defines it
somewhere — and that somewhere is **outside the four captured pages**. What
needs to be found is therefore not the Chapter 7 test cell, but the place
where ISO EN 52016-1:2017 states the standard or default surface emissivity it
applies: the long-wave radiation treatment in the body of the standard, or its
default-value table in an annex. This is the **only** route that gives
normative status.

**Subsidiary route, already in the repository.** The Chapter 7 test cell
derives from BESTEST case 600, whose report is present:
`references/standards/bestest/NREL_TP_472_6231.pdf` (296 pages). Its building
specification section for case 600 gives the surface properties. **But** —
`references/standards/bestest/README.md` sets the rule: a value traced only to
this source carries `PUBLIC_REFERENCE` status, sufficient for running and
demonstrating, **never** for an SIA 4010 claim.

**Why I have not read it myself.** This PDF is a scan: 296 pages, **zero**
extractable characters, and the environment has neither OCR nor a page renderer.
You can open it, I cannot.

In the meantime, the chain runs on a **provisional derived value** (see section 4).

**Inconsistency to resolve, unrelated to the calculation**: this README states
"The source is not redistributed in this repository", while the 14 MB PDF is
tracked by git. The report is public (DOI 10.2172/90674), so it is probably the
README that is outdated — but that is your decision, not mine, and I have
touched neither the file nor the README.

---

## 3. Beyond our reach

| Item | Nature |
|---|---|
| SIA sub-commission attestation (SIA 4010:2023 section 4.6.2) | No class can carry `VALIDATED` before it. This is not a delay on our part; it is the process. |

---

## 4. What runs on a provisional value in the meantime

A provisional value makes the chain **executable**, never produces evidence.
Every artefact carrying one declares it, and its status prevents deriving a
verdict from it.

| Value | Provisional value used | How it is obtained | Lifted by |
|---|---|---|---|
| IR emissivity of opaque surfaces, interior and exterior | **0.90** | Derived from the radiative coefficients the file already carries: epsilon = h<sub>r</sub> / (4 sigma T cubed). Interior 5.13 / 5.714 at 20 degrees C = 0.8978; exterior 4.14 / 4.6225 at 0 degrees C = 0.8956. **Assumption to confirm**: the reference temperatures, which the file does not state for these coefficients. | I1 |

This is not 0.90 chosen by convention: it is 0.90 reproduced to within 0.005
by the file's data, at two different reference temperatures. The convention
would have given the same number without demonstrating it.

### How to show Test 2A today

Use a saved disposable copy containing at least one glazed opening, then select
`test_2A / 2A` in the interface and click **Launch the guarded Test 2A chain**.
The same workflow can be run directly with
[`Run_VE_SIA4010_Test2A_Qualification_One_Click.py`](../../Run_VE_SIA4010_Test2A_Qualification_One_Click.py).

The launcher explicitly installs the prepared input contract, displays each
inherited authorisation, first runs the read-only probe then stops **before the
first setter** if its status is not
`READY_FOR_DISPOSABLE_MUTATION_QUALIFICATION`. If it proceeds, it strictly
qualifies the profile graph, the awning threshold fields and the fixed optical
storage 2E1 in two unassigned CDB constructions. Every report and its checksum
are linked in a single continuity audit.

The expected terminal status is
`RUNTIME_STORAGE_BOUNDARIES_QUALIFIED_MODEL_BINDING_REQUIRED`. It does not mean
the Test 2A model is generated: no opening is assigned, no simulation is
launched and no APS equivalence is claimed. In case of failure after the
mutation boundary, the project must be discarded and restarted in a fresh copy.

The prepared manifest carries **absolute** paths: this is functionally
required, because the reader resolves its paths relative to the manifest
directory, and this manifest is copied into an arbitrary VE project folder. It
is therefore valid on this machine only, and must be regenerated elsewhere by
[`scripts/build_test2a_external_inputs.py`](scripts/build_test2a_external_inputs.py).
The evidence artefacts carry none.

The console then states each installed authorisation with its written basis,
then `prepare_case_bundle` returns a `Test2ASourceBundleReceipt` with status
`SOURCE_BINDINGS_PROVISIONAL_RECALCULATION_REQUIRED`, five blockers,
`mutation_supported: false` and `verdict_derivation_allowed: false`. This is
exactly what there is to show: the source and native-storage chain reaches its
currently provable boundary and refuses the verdict by itself.

**This is the only provisional value in the chain**, and it cannot go
unnoticed. The loader refuses an artefact that would declare provisional while
authorising a compliance claim; the Test 2A generator contract raises the
blocker `DELEGATED_INPUT_CARRIES_PROVISIONAL_VALUE`, moves to
`SOURCE_BINDINGS_PROVISIONAL_RECALCULATION_REQUIRED` and carries
`verdict_derivation_allowed: false`. Test 2A has a published criterion, unlike
cases 1A to 1D: the bundle and storage boundaries are preparable, but complete
VE generation and the verdict remain blocked.

### A value that was thought to be provisional but was not

The interior surface coefficient was initially listed here as provisional. This
was a diagnostic error: the source **states** the three interior coefficients,
one per orientation (horizontal wall 7.63; roof upward 10.13; floor downward
5.83), and it was the normalised contract that was flattening them into a single
value. The already-proven case 600 path (`mvp_bundle.py:501`) had been consuming
them correctly from the start. The contract was therefore corrected to keep all
three, instead of declaring provisional a value the source provides. No
external request is necessary.
