# Guide — The Decisive Compliance Gate for SIA 380/2 (§ 7.2.5.2)

> **Who this guide is for.** For the person operating the client model analysis script and who wants the report to render a **COMPLIANT**
> SIA 380/2 verdict. It explains the single lever you control: providing the
> **global project / reference project comparison** reviewed and accepted.

---

## 1. Why the Report Does Not Automatically Display COMPLIANT

The component-level checks performed by the script (U values of walls, glazing, ventilation, gains,
setpoints, HVAC) are **diagnostics**: they signal deviations from the reference project inputs, but **they do not decide compliance**. The SIA 380/2:2022 standard settles global compliance based on **a single comparison**:

> the energy expenditure index of the **project** must be **less than or equal to**
> that of the **reference project** (SIA 380/2:2022 § 7.2.5.2).

The script **does not calculate** this comparison automatically (the reference project is not simulated on the client side). Until it is provided, the decisive domain remains `To be determined` and the global verdict is `NOT_DETERMINED` —
**never** a false COMPLIANT.

## 2. The Five Conditions for a COMPLIANT Verdict

The verdict `sia3802_status = COMPLIANT` requires **all** of the following
(`swiss_sia/compliance_verdict.py`):

1. At least one room analyzed.
2. No **confirmed blocking** findings (CRITICAL/HIGH) in the six domains.
3. The global comparison does **not contradict** the acceptance (project ≤ reference).
4. **No domain `NOT_DETERMINED`**: each domain evaluated, without a single
   criterion marked as `Not checkable` / `MISSING` / `placeholder`.
5. The global comparison is present and accepted
   (`global_reference_comparison.status == "REVIEWED_RESULT_AVAILABLE"`).

The two real levers are **(4)** — filling in missing model inputs — and **(5)**, the subject of this guide. The **"To reach a COMPLIANT verdict"** panel at the top of the HTML dashboard lists, at each run, exactly what is missing.

> ⚠️ Some criteria remain `Not checkable` **by design** as long as the
> regulatory source is not available (e.g., SN EN 14825 for SEER/SCoP, thermal bridges
> ψ/χ). They prevent a *total* COMPLIANT but never make the
> model `Non-compliant` — this is the safeguard against "false but credible."

## 3. Providing the Global Comparison — Step by Step

1. Calculate the SIA 380/2 index of the **project** and that of the **reference project**
   (same metric, same unit), and keep the calculation document. Two routes:
   either an off-tool calculation, or the tool that **builds** the reference project
   to be simulated (see § 5).
2. Copy the template
   [`templates/SIA3802_global_reference_comparison_TEMPLATE.csv`](templates/SIA3802_global_reference_comparison_TEMPLATE.csv)
   into the `sia4010_evidence/` folder **next to the VE model**, and rename it:

   ```
   SIA3802_global_reference_comparison_<ProjectLabel>.csv
   ```

   `<ProjectLabel>` = the name of the VE project as the tool sees it (`.mit` folder name). A suffix that does not match the active project is ignored.
3. Fill in the row (see § 4). One person reviews and **accepts**: this is
   `review_status = accepted`.
4. Rerun `Run_VE_Swiss_Compliance.py`. If the figures and acceptance are
   consistent, the decisive domain shifts to `Compliant` and — if conditions 1–4
   are met — the global verdict becomes **COMPLIANT**.

## 4. Fields of the Row (All Mandatory for Acceptance)

Acceptance is refused if a single field is missing or does not match
(`swiss_sia/evidence_manager.py::_normalize_global_comparison_record`).

| Column | Expected Value | Role |
|---|---|---|
| `project_id` | the label of the VE project | attaches the row to the active project |
| `comparison_scope` | `complete_sia3802_project` | attests that the comparison covers the **complete** project, not a component |
| `comparison_metric` | `global_energy_expenditure_index_sia380` | the quantity compared is the global SIA 380 index |
| `project_value` | number | index of the project |
| `reference_value` | number | index of the reference project |
| `unit` | e.g. `MJ/m2a` | unit common to both values |
| `comparison_result` | `pass` | (or `passed`/`compliant`/`accepted`) |
| `review_status` | `accepted` | (or `approved`/`reviewed`/`signed`/`validated`) |
| `reviewer` | name | who reviewed it |
| `review_date` | date | when |
| `source_document` | calculation file | source (or `source_reference`) |
| `notes` | free text | optional |

**Logical constraint (SIA 380/2:2022 § 7.2.5.2):** `project_value ≤ reference_value`.
If `accepted` is set but `project_value > reference_value`, the report
raises the critical alert `SIA3802_GLOBAL_REFERENCE_DISCREPANCY` and becomes
**Non-compliant**: acceptance can **never** contradict the figures.

## 5. Calculate the Reference Index in VE (Alternative Route)

Section 3 assumes you calculate the project index **and** the reference project index outside the tool. Alternatively, the tool can **build** the reference project from the normative substitutions, so you only need to **simulate** both models and read the two indices. This route still does **not calculate** anything automatically: it prepares the reference model, you run ApacheSim, and a reviewer accepts the comparison.

**Step 1 — see the spec and what blocks it.**
Open the active client project and run **`Run_VE_SIA3802_Reference_Spec_Dump.py`**
(read-only). It writes a JSON file next to the project listing each substitution
(project value, reference limit and target, SIA source) and especially the
**blockers**. Possible spec statuses:
- `READY_FOR_REFERENCE_RUN` — all substitutable families are resolved.
- `BLOCKED_INCOMPLETE_INPUTS` — at least one family is missing (unclassified surface,
  reference value not entered, g_perp not proven…). **Resolve each blocker
  in the model** (classify the surface, expose the value) before building,
  otherwise the reference is incomplete. Families outside the tool scope remain to
  be handled manually by the reviewer (see the JSON `missing_input_families`).

**Step 2 — build the reference project (on a COPY).**
`Run_VE_SIA3802_Build_Reference_Model.py` **refuses** to mutate a project whose path does not contain `_TEST`, `_COPY`, or `_DISPOSABLE` — it **never** touches
the original. Work on a copy of the project. The script applies the
substitutions (infiltration, emission, unlimited capacity, SCoP/SEER generation,
opaque envelope, glazing, frame fraction) **with capability-check + immediate readback**; any family whose readback fails is marked `FAILED_READBACK` and
reported — it is **not** silently assumed to be applied. The script does **not** run ApacheSim.

**Step 3 — simulate both models.**
Run ApacheSim on the **project** and the **reference project** built,
with the **same weather** and same settings, then record the **global SIA 380
index** for each (same metric, same unit).

**Step 4 — enter in the CSV.**
Put the two indices in `SIA3802_global_reference_comparison_<project>.csv`
(§ 4), have it reviewed and accepted, rerun `Run_VE_Swiss_Compliance.py`.

> ⚠️ **This is not a qualification.** A reference model built by API
> and simulated is not certified proof: `FAILED_READBACK`, families
> outside the scope, and reviewer acceptance remain mandatory safeguards.
> Unresolved `BLOCKED_INCOMPLETE_INPUTS` ⇒ the reference is not deterministic.

## 6. What This Does Not Do

- It does not replace a certificate: the report remains an **evaluation of
  evidence**.
- It does not concern SIA 4010: validation classes qualify the
  **software**, not the client building, and do not appear in the client report
  (separate internal report: `Run_VE_Swiss_Compliance_Internal_SIA4010.py`).
