> **Note:** Translated from French original. See [SIA_CORRESPONDANCE_ZWEIFEL_2026-08-12.md](SIA_CORRESPONDANCE_ZWEIFEL_2026-08-12.md) for the source document.

# SIA Correspondence — Prof. Zweifel, 2026-08-12

Subject: correction of an erroneous statement on our part, and two questions
that remain open regarding the evaluation workbooks.

This document exists for one reason: the previous message contained a false
statement, identified by our contact. Before any new mailing, every sentence in
the draft is backed here by the cell or file that proves it. What cannot be
verified is not sent.

---

## 1. What we had written, and why it was wrong

We had written that "the corresponding workbooks do not include frequency
classes or distribution sheets" for Tests 4 and 6. Prof. Zweifel replied
"they do". He is right, on both halves of the sentence.

Two causes, both on our side:

| Cause | Detail |
| --- | --- |
| Wrong search criterion | We were looking for sheets prefixed `Vert.` instead of examining the sheet type. The `Verteilung` sheets in Tests 4/6/7 are **chartsheets**, not worksheets; our inventory ignored them. |
| Divergent spelling | The sheet is called `Haeufigkeitsklassen` in Tests 2, 3 and 5, but `Haeufigkeitskassen` (without the `l`) in Tests 4, 6 and 7. Our search used only the first spelling and therefore silently skipped three workbooks. |

Verification, read from `xl/workbook.xml` of each workbook:

| Workbook | Frequency-class sheet |
| --- | --- |
| Test1 | *none* |
| Test2 | `Haeufigkeitsklassen` |
| Test3 | `Haeufigkeitsklassen` |
| Test4 | `Haeufigkeitskassen` |
| Test5 | `Haeufigkeitsklassen` |
| Test6 | `Haeufigkeitskassen` |
| Test7 | `Haeufigkeitskassen` |

After fixing the reader, the distributions were captured cell by cell and
reconciled against the totals row of each workbook:

| Test | Frozen distributions | Reference |
| --- | --- | --- |
| 2 | 22 | `refs/reference-data/test-2.distributions.ref.json` |
| 3 | 16 | `refs/reference-data/test-3.distributions.ref.json` |
| 4 | **11** | `refs/reference-data/test-4.distributions.ref.json` |
| 5 | 16 | `refs/reference-data/test-5.distributions.ref.json` |
| 6 | **10** | `refs/reference-data/test-6.distributions.ref.json` |
| 7 | **17** | `refs/reference-data/test-7.distributions.ref.json` |

That is 38 additional distributions compared to what we thought we had.

---

## 2. The two questions that remain open

### 2.1 Is the Streubereich an enforceable criterion for Tests 4, 6 and 7?

Observed fact: in those three workbooks, the `Verteilung` sheets are charts.
They plot the reference variants and the tested program, **without computing
any band**; no cell defines a Streubereich.

The decisive asymmetry is elsewhere, and it lies in the **specifications**, not
in the workbooks. Verified by full-text search on 2026-08-12:

| Specification | `Testkriterien` section | What it says about the distribution |
| --- | --- | --- |
| `Spezifikation_Test2.pdf` p. 2/2 | **present** | "Haeufigkeitsverteilung ... muss im Streubereich der Referenzprogramme liegen" |
| `Spezifikation_Test3.pdf` p. 3/3 | **present** | "Haeufigkeitsverteilung innerhalb des Streubereichs der Referenzprogramme" |
| `Spezifikation_Test5.pdf` p. 5/5 | **present** | "Die Haeufigkeitsverteilungen muessen im Streubereich der Referenzprogramme liegen" |
| `Spezifikation_Test4.pdf` | **absent** — 0 occurrences | — |
| `Spezifikation_Test6.pdf` | **absent** — 0 occurrences | — |

In other words: for Tests 2, 3 and 5, the specification **itself requires**
the distribution to fall within the Streubereich, and the 2026-08-10
clarification defines it. For Tests 4 and 6, no equivalent sentence exists.
Note to prevent a false argument: none of the seven workbooks contains the word
`Testkriterien` — that section belongs only to the specifications.

The written clarification of 2026-08-10 defined the rule for Tests 2, 3 and
5: min/max envelope of the reference programs, class by class. The question is
whether this rule applies identically to Tests 4, 6 and 7, or whether those
three remain "results recorded, no criterion". 

Our position until the answer is in writing: distributions are extracted and
recorded, but the engine does not turn them into a verdict. Status
`RESULTS_RECORDED_NO_CRITERION`.

### 2.2 Awning control: four unstated semantics

This is **the** blocker for case 1E, the only Test 1 case carrying a pass/fail
criterion. The specification defines 1E as "Diagnosefall 1D, jedoch mit
Stoffmarkisen-Sonnenschutz gemaess Diagnosetest 2 E1", and the device is fully
documented: Soltis 92-2048-Alu, 150 W/m2 threshold, deployed-state
whole-window properties. We built the control contract from those values.

What is missing is not the device but the **dynamics**, and none of the four
points can be deduced from the documents:

| Point | What the sources say |
| --- | --- |
| Exact irradiance signal | "Einstrahlungs-Schwellenwertregelung", without defining the measured quantity |
| Comparison operator | 150 W/m2 threshold stated, direction of inequality not stated |
| Release rule | none |
| Timestep and state treatment | none |

To this is added an API question: IESVE exposes two separate thresholds,
`external_shade_radiation_to_lower` and `external_shade_radiation_to_raise`. We
have set both to 150 W/m2, but their dynamic equivalence to the specification's
rule cannot be deduced from their names.

Until these points are in writing, we leave 1E blocked. Guessing the release
rule would shift a real verdict, on the only Test 1 case that carries one.

### 2.3 Test 7, block W: two contradictory units

File `Test7/Resultaterfassung Test7.xlsx`, sheet `Zusammenfassung`.
Quantity "Aus Kaelteerzeugung an die Waermeseite gelieferte Waerme", column
block `W`.

- the quantity cell carries `kW`;
- the unit row (row 33) carries `°C`.

Only one block out of seventeen is affected. **Verified cell by cell** on
2026-08-12: `W32` = "Aus Kaelteerzeugung an die Waermeseite gelieferte Waerme,
kW" and `W33` = "°C", while all other blocks agree — `B32`/`B33`
kW/kW, `AR32`/`AR33` °C/°C, `AK32`/`AK33` no unit and `-`. We kept the
counts, which do not depend on this label, and left the unit null: deciding
would amount to correcting a defect in the official workbook in place of its
author.

### 2.4 What we are NOT reporting, after verification

An earlier version of this file announced a contradiction between the Test 2
specification and the example-building documentation on the glazing U-value:
0.654 vs. 0.646. **That was our error, not yours.** The documentation describes
the same window under two families of standards and the U-value differs — 0.646
under EN ISO 52022-3 reference conditions, 0.654 under ISO 15099 winter
conditions. The specification uses the latter, to the exact digit. The two
documents agree; our comparison was against the wrong block. Nothing to report,
therefore, and this is recorded here so that the false finding does not
resurface.

---

## 3. What is already settled and does not need to be asked again

| Item | Response received |
| --- | --- |
| Streubereich Tests 2/3/5 | Min/max envelope per frequency class (2026-08-10). |
| Totals below 8760 | These are not missing hours: the remaining values lie outside the bounds defined by the classes (2026-08-10). We keep them as an out-of-class counter, without adding them to the last class. |
| Test 7, corrected workbook | Lower bound / upper bound, not mean / upper bound. XML check and checksum recorded. |

---

## 4. Draft message (English, to be reviewed before sending)

> Dear Professor Zweifel,
>
> Thank you for the correction — you are right, and I was wrong. The Test 4 and
> Test 6 workbooks do contain frequency classes. Two mistakes on my side caused
> it: I was looking for worksheets and the `Verteilung` sheets in those files
> are chartsheets, and the frequency-class sheet is spelled
> `Haeufigkeitsklassen` in Tests 2, 3 and 5 but `Haeufigkeitskassen` in Tests 4,
> 6 and 7, so my reader silently skipped three workbooks.
>
> After fixing it we have read the classes cell by cell and reconciled them
> against each workbook's own totals row: 11 distributions in Test 4, 10 in Test
> 6 and 17 in Test 7, in addition to the 22, 16 and 16 of Tests 2, 3 and 5.
>
> Three points remain open, and I would rather ask than assume.
>
> First, the acceptance criterion for Tests 4 and 6. Your clarification of
> 10 August defined the Streubereich for Tests 2, 3 and 5 as the min/max
> envelope of the reference programs, class by class. For those three the
> specification itself requires the distribution to lie in that range —
> `Spezifikation_Test2.pdf` states "Haeufigkeitsverteilung ... muss im Streubereich
> der Referenzprogramme liegen", and Tests 3 and 5 carry the equivalent
> sentence. The specifications of Tests 4 and 6 contain no `Testkriterien`
> section at all. In their workbooks the `Verteilung` sheets are charts that
> plot the reference variants against the tested program without computing any
> band, so no cell defines a range either.
>
> Does the same min/max rule apply to Tests 4 and 6, or are their distributions
> recorded without an acceptance criterion pending the sub-commission? Until we
> have this in writing our engine records the distributions but issues no
> verdict from them.
>
> Second, the fabric-awning control of diagnostic test 2 E1. This is what
> currently blocks Test 1 case 1E, the only case of Test 1 carrying a pass/fail
> criterion, since the specification defines it as case 1D with the 2 E1
> shading. The device itself is fully documented and we have built its control
> contract from your figures: Soltis 92-2048-Alu, 150 W/m2 threshold, and the
> deployed-state whole-window properties from the example-building
> documentation. What we cannot derive is the control dynamics — the exact
> irradiance signal the threshold is compared against, the direction of the
> comparison, the release rule, and how the state is carried across a timestep.
> IESVE exposes two separate thresholds, "radiation to lower" and "radiation to
> raise"; we have set both to 150 W/m2, but we cannot show from their names that
> this reproduces the rule you intend. Could you confirm those four points, or
> tell us where they are specified?
>
> Third, a small defect I would like to report rather than silently resolve. In
> `Resultaterfassung Test7.xlsx`, sheet `Zusammenfassung`, the quantity "Aus
> Kaelteerzeugung an die Waermeseite gelieferte Waerme" (column block W) carries
> `kW` in the quantity cell and `°C` on the unit row, cells W32 and W33. It is
> the only one of the seventeen blocks where the two disagree; the others match,
> for example B32/B33 both kW and AR32/AR33 both °C. We have kept the hourly
> counts, which do not depend on the label, and left the unit unset.
>
> Finally, on the SIA 2024 usage data you mentioned would follow: the category
> 3.1 extract you sent on 10 August turned out to cover more than we expected —
> it is exactly the category the Test 2 specification prescribes, and it gives
> the occupant sensible gain directly, so it has unblocked the whole 1A to 1D
> diagnostic chain. Thank you for that. What we still lack are the other
> categories our test matrix needs: the auditorium and example-building
> profiles, and restaurant 6.2 and kitchen 6.4.
>
> To be explicit about what we are and are not claiming: this work is a
> readiness and evidence exercise on our side. We make no claim that our
> software is SIA 4010 validated, and none that SIA has reviewed or endorsed it.
>
> With thanks for your patience,

---

## 5. What this message does not claim

- no claim of SIA 4010 validation;
- no claim of review or endorsement by SIA or IES;
- no normative value inferred: the three reported points are facts observed in
  the official files, or questions.
