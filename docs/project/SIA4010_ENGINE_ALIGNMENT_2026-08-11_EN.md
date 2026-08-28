> **Note:** Translated from French original. See [SIA4010_ENGINE_ALIGNMENT_2026-08-11.md](SIA4010_ENGINE_ALIGNMENT_2026-08-11.md) for the source document.

# SIA 4010 evaluation engine alignment with official evidence 2026-08-10

**Date**: 2026-08-11
**Author**: targeted update from the official workbooks and the written clarification from Prof. Gerhard Zweifel (SIA).
**Scope**: `engine/` engine, frozen reference data `refs/reference-data/*.json`, `Haeufigkeitskassen` sheet extractor, source audits.

This note is a traceability record: for each alignment decision it lists the evidence (file, cell, or SIA correspondence) supporting it. No normative value has been invented or extended; Test 1 tolerances remain those published; Tests 4 and 6 criteria remain outside the gate in the absence of SIA feedback.

---

## 1. Cited authority sources

Three pieces of evidence received on 2026-08-10 are already integrated and re-verified on 2026-08-11:

- **Test 7 workbook correction** -- [`sia4010_evidence/source_audits/test7-corrected-workbook-20260810.json`](../../sia4010_evidence/source_audits/test7-corrected-workbook-20260810.json), supplemented by the re-inspection [`sia4010_evidence/source_audits/test7-workbook-integrity-2026-08-11.json`](../../sia4010_evidence/source_audits/test7-workbook-integrity-2026-08-11.json) (SHA-256 `24937d8f...`, identity verified between `Downloads/` and `SIA_4010_geteilter_Link/Test7/`).
- **Written `Streubereich` clarification** -- received from Prof. Gerhard Zweifel on 2026-08-10; integrated into [`engine/sia_distributions_engine.py`](../../engine/sia_distributions_engine.py) (`STATUT_CRITERE = 'CONFIRME_AUTORITE_2026-08-10'`): the Streubereich per frequency class is the **min/max envelope of the reference programs**, class by class.
- **SIA 2024 category 3.1 (office)** -- authority extract + binding + `PASS` validation under [`sia4010_evidence/source_audits/sia2024_3_1_authority_20260810/`](../../sia4010_evidence/source_audits/sia2024_3_1_authority_20260810/); no direct impact on the evaluation engines, but required for case preparation.

---

## 2. Test 7 -- "lower bound / upper bound" rule

### Decision
Use cells **`$N8` (Untere Grenze, lower bound) to `$M8` (Obere Grenze, upper bound)** as inclusive bounds on `F8:F12 F14:F18 F20`.

### Evidence read verbatim
Direct openpyxl read (`data_only=False`) on 2026-08-11 from `SIA_4010_geteilter_Link/Test7/Resultaterfassung Test7.xlsx` (SHA-256 `24937d8f421daa74a7f957025bfeb17a42fe2dc807b1a301a6752f4c0e808958`):

- `Zusammenfassung!L7 = "Mittelwert"`
- `Zusammenfassung!M7 = "Obere Grenze"`
- `Zusammenfassung!N7 = "Untere Grenze"`
- Conditional formatting `sqref=F8:F12 F14:F18 F20  type=cellIs  operator=between  formulas=['$N8', '$M8']`

### Current code conformity
- [`engine/test7_engine.py`](../../engine/test7_engine.py) loads `borne_basse` and `borne_haute` from the frozen reference data and delegates to `scatter_band.verdict()` which compares with INCLUSIVE bounds (`band.contains`).
- [`refs/reference-data/test-7.ref.json`](../../refs/reference-data/test-7.ref.json) carries `source.sha256 = "24937d8f..."` and `source.correction = "Regle conditionnelle N (borne basse) a M (borne haute)"`, freeze dates `2026-08-10`.

The numerical bounds from the corrected workbook are **identical** to those from the pre-correction (`numeric_bounds_identical: true` cf. audit 2026-08-10): only the cell referenced by the rule changed. The engine's numerical regression therefore remains `0`. This is not a re-implementation -- it is an explicit anchoring to the official columns.

### Non-regression test
- [`tests/test_sia4010_engine_alignment_20260811.py::Test7CorrectedWorkbookIntegrityTests`](../../tests/test_sia4010_engine_alignment_20260811.py)
  - Verifies the workbook SHA-256;
  - Verifies that `test-7.ref.json` is pinned to the corrected SHA-256;
  - Replays the CF-rule at the XML level to prove `['$N8', '$M8']`.

---

## 3. Tests 2, 3, 5 -- Streubereich = min/max envelope per class

### Decision
For each frequency class, the Streubereich is the **min/max envelope of the reference programs**. The `mean +/- max_dev` reading remains computed but **is no longer binding**. It is kept solely for comparison with previous audits.

### Evidence read verbatim
Written clarification received on 2026-08-10 from Prof. Gerhard Zweifel:

> "`Streubereich` designates the minimum/maximum envelope of the reference programs for each frequency class. Displayed totals below 8760 hours do not indicate incomplete series: some hourly values fall outside the defined bounds. They must be counted separately."

### Current code conformity
- [`engine/sia_distributions_engine.py`](../../engine/sia_distributions_engine.py)
  - `LECTURE_ENVELOPPE = 'enveloppe_min_max'` (binding) and `LECTURE_BANDE = 'moyenne_plus_ecart_max'` (audit only);
  - Verdict block: `hors[LECTURE_ENVELOPPE]` triggers `VERDICT_FAIL` (line 247). The band reading does not enter the verdict.
- Frozen reference data [`refs/reference-data/test-2.distributions.ref.json`](../../refs/reference-data/test-2.distributions.ref.json), [`test-3.distributions.ref.json`](../../refs/reference-data/test-3.distributions.ref.json), [`test-5.distributions.ref.json`](../../refs/reference-data/test-5.distributions.ref.json) carry `statut_critere: "CONFIRME_AUTORITE_2026-08-10"`.

### Non-regression test
- [`tests/test_sia4010_engine_alignment_20260811.py::DistributionEngineEnvelopeBindingTests`](../../tests/test_sia4010_engine_alignment_20260811.py)
  - Builds a block where the candidate is **outside the envelope** but inside the symmetric band -- must FAIL;
  - Verifies that a candidate at the centre passes PASS and leaves `nb_hors_lecture[LECTURE_ENVELOPPE] == 0`.

---

## 4. Out-of-class counter

### Decision
Hourly values that exceed the upper bound of the last class are **never** absorbed into the last class. They are counted separately and surfaced in an audit counter.

### Evidence
Authority 2026-08-10 (cf. section 3) explicit: "some hourly values fall outside the defined bounds. They must be counted separately."

### Current code conformity
- `sia_distributions_engine.classer_avec_hors_classes(serie, bornes)` returns `{effectifs, hors_classes_superieur, total_numerique}`.
- `sia_distributions_engine.classer(serie, bornes)` counts **only** values that find a class; excess values are not added to the last class.
- The `contributeurs_hors_classes` field is propagated into `evaluer_bloc`, with priority given to the frozen reference data field `heures_hors_classes`, falling back to `max(0, 8760 - total_heures)`.

### Non-regression tests
- [`tests/test_sia4010_engine_alignment_20260811.py::OutOfClassCounterTests`](../../tests/test_sia4010_engine_alignment_20260811.py)
  - A series of 9 values, 2 of which exceed the last bound -- `hors_classes_superieur == 2`;
  - A value of `100` well beyond the last bound -- `effectifs[-1] == 0` (never absorbed).

---

## 5. Frequency classes -- all six workbooks have them

> **Corrected on 2026-08-12.** The initial version of this section claimed that
> the frequency class sheet existed only in Tests 4, 6 and 7, and that
> Tests 2, 3 and 5 "organised their data differently". This was incorrect. The
> cause: the official workbooks use two spellings, and the extractor searched
> for only one, silently excluding three files.

### Decision
Remove any claim that some Tests among 2 to 7 would not have frequency classes.
**All six have them.** Their exact scope as an acceptance gate for Tests 4, 6
and 7 remains under review by the SIA sub-commission, but their existence is
proven by direct reading.

### Evidence read verbatim
openpyxl inspection on 2026-08-12, all workbooks:

| Workbook | Sheet | Binned quantities | Chartsheets |
|---|---|---:|---:|
| `Resultaterfassung_Test2.xlsx` | `Haeufigkeits**kl**assen` | 3 | 50 |
| `Resultaterfassung_Test3.xlsx` | `Haeufigkeits**kl**assen` | 2 | 55 |
| `Resultaterfassung Test4.xlsx` | `Haeufigkeits**k**assen` | **11** | **48** |
| `Resultaterfassung_Test5.xlsx` | `Haeufigkeits**kl**assen` | 11 | 0 |
| `Resultaterfassung_Test6.xlsx` | `Haeufigkeits**k**assen` | **11** | **37** |
| `Resultaterfassung Test7.xlsx` | `Haeufigkeits**k**assen` | 20 | 50 |

Three findings to retain:

1. **Two spellings.** Tests 4, 6 and 7 write `Haeufigkeitskassen`, without the
   `l` of `Klassen`. Tests 2, 3 and 5 write `Haeufigkeitsklassen`. Both forms
   are now accepted.
2. **Tests 4 and 6 have more binned quantities than Tests 2 and 3.** 11 versus
   3 and 2. The opposite claim, transmitted to SIA on 2026-08-07, was incorrect
   and the authority flagged it.
3. **The distribution sheets for Tests 4 and 6 exist**: 48 and 37 `Chartsheet`
   instances, one per binned quantity. They do not carry the `Vert.` prefix used
   by Tests 2/3/5/7 -- they are named directly after the quantity
   (`Zu- und Abluftvolumenstrom`, `Zulufttemperatur`, `Leistung Ventilatoren`...).
   Counting by prefix instead of sheet type is what produced the error.

`Fenstermodelle` column (Tests 2 and 3): window model legend in text, with no
unit or numerical bound. This is not a binned quantity; the extractor excludes
it by explicit rule (label + unit + at least one numerical bound required), not
by a layout accident.

`9999` cell: SIA convention for "class not used for this quantity"; never
interpreted as a bound.

### Supplementary evidence -- the annual sum criterion for Tests 4 and 6 is operative
Contrary to what the 2026-08-07 draft assumed, it does not need to be inferred:
it lives in the workbook's conditional formatting, and its range covers exactly
the `Testgrössen` block, stopping before the `Diagnosegrössen` -- same
structure as Test 7.

| Workbook | Conditional formatting | Headers | Groups |
|---|---|---|---|
| Test 4 | `D10:D12` between `$U10`,`$V10` | T8 `Mittelwert`, U8 `obere Grenze`, V8 `untere Grenze` | A9 `Testgrössen`, A13 `Diagnosegrössen` |
| Test 6 | `E10:E15` between `$L10`,`$M10` | K8 `Mittelwert`, L8 `obere Grenze`, M8 `untere Grenze` | A10 `Testgrössen`, A16 `Diagnosegrössen` |

### Evidence -- absence of `Testkriterien` in the specifications
pypdf search across all seven specifications (`testkriteri|streubereich|abweichung|häufigkeitsverteilung`):

| Spec | Occurrences |
|---|---|
| Test 1 | `Testkriterien`, `Streubereich` |
| Test 2 | all four |
| Test 3 | all four |
| **Test 4** | **none** |
| Test 5 | all four |
| **Test 6** | **none** |
| **Test 7** | **none** |

This half of the 2026-08-07 claim is therefore confirmed: Tests 4, 6 and 7 do
not state any criterion in their specification.

### Deliverable
- [`swiss_sia/reference_model/sia4010/haeufigkeitskassen_extractor.py`](../../swiss_sia/reference_model/sia4010/haeufigkeitskassen_extractor.py): pure openpyxl, no `iesve`, accepts both spellings, records the one found in `sheet_name` for provenance, and identifies a binned quantity by its intrinsic form.
- Tests: [`tests/test_haeufigkeitskassen_extractor.py`](../../tests/test_haeufigkeitskassen_extractor.py) -- all six workbooks, spelling and quantity counts frozen, `Fenstermodelle` exclusion, `9999` sentinel preservation, index monotonicity.

### Gate state
The distribution reference data producer (`scripts/build_sia_distribution_reference.py`) currently builds reference data only for Tests **2, 3, 5** -- the three whose specification states the distribution criterion.

The open question is no longer "do distributions exist" but rather
**"does the distribution criterion apply to Tests 4, 6 and 7, whose
specifications state no criterion even though their workbooks carry the same
machinery as Tests 2/3/5?"**. Asked to SIA on 2026-08-07 on a false premise;
the authority flagged the error without answering the substance. Needs to be
re-asked. If the answer is yes, `sia_distributions_engine.TESTS_SUPPORTES`
will need to be extended from `(2, 3, 5)` to `(2, 3, 4, 5, 6, 7)` and four
additional reference data sets built.

---

## 6. Test 1 -- no criterion invented for the six normative cases

### Decision
The six normative Test 1 cases (`600, 640, 900, 940, 600FF, 900FF`) remain **without a pass/fail criterion**. Only the diagnostic case `1E` carries a verdict (Streubereich over 4 reference programs). No tolerance is added by default; no PASS status is produced for the six normative cases. Engagement status preserved: `RESULTS_RECORDED_NO_CRITERION`.

### Evidence
[`engine/test1_engine.py`](../../engine/test1_engine.py) -- line 86: `CAS_AVEC_CRITERE = ('1E',)`. Docstring lines 14-25 quote verbatim the Testkriterien from `Spezifikation_Test1.pdf`:
> "Es gibt dafuer kein Abweichungskriterium."

### Non-regression tests
- [`tests/test_sia4010_engine_alignment_20260811.py::Test1SixNormativeCasesRemainInformativeTests`](../../tests/test_sia4010_engine_alignment_20260811.py)
  - `CAS_AVEC_CRITERE == ('1E',)`;
  - Each of the 6 normative cases is absent from the criterion set.

---

## 7. What this note does NOT do

- **Does not modify** the `engine/*.py` engines: the existing code (M) is consistent with the evidence; only the `haeufigkeitskassen_extractor.py` extractor is an addition.
- **Does not modify** the frozen JSON files under `refs/reference-data/`: the `garde_refs.py` hook protects them; any update goes through an audited producer (`scripts/build_*.py`).
- **Does not modify** the official SIA workbooks under `SIA_4010_geteilter_Link/`: they are treated as read-only evidence.
- **Does not pronounce** a SIA 4010 conformity verdict: the sub-commission (SIA 4010:2023 section 4.6.2) remains the sole legitimate authority.
- **Does not replace** question 3 from the 2026-08-07 email (missing Testkriterien for Tests 4 and 6). Until SIA responds, these two tests remain `INFERE` on the criterion side and without an executable gate on the distribution side.
- **Does not invent any tolerance** for Test 1 or for the Test 7 Testgroessen: the bounds come verbatim from the workbook.

---

## 8. Files touched in this pass

**Created:**
- `docs/project/SIA4010_ENGINE_ALIGNMENT_2026-08-11.md` (this note)
- `sia4010_evidence/source_audits/test7-workbook-integrity-2026-08-11.json`
- `swiss_sia/reference_model/sia4010/haeufigkeitskassen_extractor.py`
- `tests/test_haeufigkeitskassen_extractor.py`
- `tests/test_sia4010_engine_alignment_20260811.py`

**Not modified (by explicit choice, already consistent):**
- `engine/test1_engine.py`, `engine/test7_engine.py`, `engine/sia_distributions_engine.py`, `engine/scatter_band.py`, `engine/sia_bandes_engine.py`
- All `refs/reference-data/*.json`
- All official workbooks under `SIA_4010_geteilter_Link/`

---

## 9. Exact VE action for Ulysse

Nothing to do in VE 2025 for this pass: it deals exclusively with traceability and the pure Python engine. The next useful VE milestone remains:

1. Confirm with Johan whether IES already has the SIA 2028 solar data (question 1 from the draft email of 2026-08-10). Without them, no Test 2-7 case can progress beyond `IMPLEMENTED_UNQUALIFIED`.
2. Once unblocked: run the 5 Test 1 runtime probes (`640, 600FF, 900, 940, 900FF`) in a disposable VE 2025 project, as documented in `docs/project/MVP_COMPLETION_MATRIX.md`.
