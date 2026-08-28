> **Note:** Translated from French original. See [critere-test4.spec.md](critere-test4.spec.md) for the source document.

# Normative Ruling --- Acceptance Criterion for SIA 4010 Test No. 4

> Status: **RULING RENDERED --- high confidence on the form of the criterion,
> medium confidence on the data block to which it applies.**
> Author: `norm-analyst`, 2026-07-31.
> Scope: Test 4 only (air conditioning of a single room, all-air system,
> example building auditorium). Relevant validation classes: **3, 4A, 4B**.
> Dependency: reuses without re-deriving the ruling
> `traceability/streubereich-distributions.spec.md` (band construction,
> confidence ~92%). This document addresses only the question *where does
> Test 4 draw its criterion from*, not *how the band is computed*.

---

## 1. The question

`Spezifikation_Test4.pdf` contains no acceptance criterion; on what
authority, and under what formula, can Test 4 then be judged compliant?

---

## 2. Verdict

**The Test 4 criterion does not exist in its specification, and SIA 4010:2023
defines no generic one either. Its sole material basis is the workbook
`Resultaterfassung Test4.xlsx`, to which SIA 4010 §4.4 explicitly delegates
the comparison with reference results. The formula to apply is that of the
family (Tests 2, 3, 5), carried over to Test 4 by analogy and confirmed by
the effective presence of bands in its own workbook:**

```
Annual sums of the 3 Testgroessen: mean of reference programs
                                   +/- max |program - mean|
Hourly frequency distributions:    within the Streubereich of reference programs
                                   (same construction, cf. streubereich-distributions.spec.md)
```

| Verdict element | Level | Confidence |
|---|---|---|
| The Test 4 specification is silent (this is not an extraction artefact) | **VERIFIED** | ~97% |
| SIA 4010:2023 contains no numerical criterion, generic or otherwise | **VERIFIED** | ~95% |
| Authority is delegated by SIA 4010 §4.4 to the evaluation workbook | **VERIFIED** | ~95% |
| The band form is `mean +/- max\|deviation\|` over 4 reference programs | **ANALOGY + material evidence** | ~88% |
| It applies to the **3 annual Testgroessen** (and not to the 4 Diagnosegroessen) | **INFERRED (strong)** | ~85% |
| The band columns `T/U/V` are those of the **Jahreswerte** block and not **Maximalwerte** | **NOT VERIFIED** | ~70% |
| The frequency distribution criterion also applies to Test 4 | **ANALOGY** | ~80% |

**What is NOT acquired and blocks a full freeze: the formula of cell
`T10` in the Test 4 workbook** (§7.1). A single cell decides.

---

## 3. Evidence, citation by citation

Convention: **[V]** verified by me in a source read this session;
**[V-orch]** material fact extracted by the orchestrator from a binary I cannot
open, and which I take as established; **[I]** inference; **[A]** analogy.

All cited lines `spec_testN.txt`, `sia_*.txt`, `anwender_*.txt`,
`PREUVE_*.txt` refer to the session extraction directory
`...\scratchpad\norme\`. Corresponding primary sources:
`SIA_4010_geteilter_Link/Test<N>/Spezifikation_Test<N>.pdf`,
`Resultaterfassung Test4.xlsx`, `refs/` (SIA 4010:2023 fr, SIA 380/2:2022 fr).

### 3.1 The Test 4 specification is silent --- and not only about the criterion **[V]**

`spec_test4_raw.txt` (208 ll., raw extraction) and `spec_test4.txt` (131 ll.,
`-layout`): search for `Resultat`, `Testgr`, `Diagnose`, `liefern`,
`Auswertung` -> **0 occurrences in both extractions**. It is therefore not just
the *Testkriterien* section that is missing: **the entire final block
"Zu liefernde Resultate / Testresultate / Testkriterien / Diagnoseresultate" is
absent**, whereas it is present in the four other specifications read
(`spec_test1.txt` ll. 64--69; `spec_test2.txt` ll. 70, 101--110;
`spec_test3.txt` ll. 148--155; `spec_test5.txt` ll. 238--241, 272--280).

The document declares itself complete: footers `2 / 3` (`spec_test4.txt` l. 87) and
`3 / 3` (l. 131), page 3 ending with the Lufterhitzer parameters
(`Heizwasser-Vorlauftemperatur konstant 40 degC`, l. 129). For comparison,
Test 3 places its criteria on page 3/3 and Test 5 on page 5/5: in both cases the
block fits on the last page. **For Test 4, there is no page for it.**

-> **[I]** This is very likely an **editorial omission by SIA** (the
last lines of the table template were not printed), not a decision
not to judge Test 4: a test from which no results are requested would be
purposeless, yet `Resultaterfassung Test4.xlsx` exists, defines the quantities
to deliver, and **four** reference programs have filled it in (§3.6).

**Honest caveat**: I cannot rule out that page 3 might contain, visually,
line labels without extractable text content (vectorised text frame,
image). A visual rendering of page 3 would be needed to fully exclude this.

### 3.2 SIA 4010:2023 defines no criterion, neither specific nor generic **[V]**

The copy in `/refs` is the **French version** (`sia_4010_2023.txt` ll. 8--15,
"SNG 594010:2023 fr"). Searches across the full text (3109 ll.):

| Pattern | Occurrences |
|---|---|
| `tol.rance`, `crit.re`, `dispersion`, `.cart` | **0** |
| `moyenne` | 14, **all** in EN input data tables (ll. 1767, 2290--2419: "Temperature moyenne de l'eau...") --- **none** related to a criterion |
| `Streu` (purely ASCII pattern, case-insensitive) | **0** |

The four articles named in the question were read in full:

- **§4.4 "Test descriptions and results"** (ll. 2695--2702) --- **this is
  the key article**: "Detailed descriptions of each test are
  available as separate documents at www.sia.ch/sia4010. For each
  test, an EXCEL evaluation file is available at www.sia.ch/sia4010, into
  which results can be transferred and **which generates the comparative
  display of results with the reference results**." -> explicit delegation,
  both to the specifications and to the **workbook**.
- **§4.5 / table 63 "Validation classes"** (ll. 2704--2781) --- assigns only
  **tests to classes**, no tolerance. Test 4 appears in three
  entries of the "Tests" column: `1, 4 to 6`, `1, 2A, 3A to F, 4 to 7`, `1 to 7`.
  By positional correspondence with the "Class No." column
  (`1A, 1B, 2A, 2B, 3, 4A, 4B, 5`, ll. 2743--2779): **classes 3, 4A and 4B**.
  `[I]` --- the line/column alignment of the table is degraded by extraction;
  reconstruction is positional and **requires visual confirmation**.
- **§4.6.1 "Infrastructure"** (ll. 2783--2799) --- announces the instruments
  (Excel workbooks, **FAQ document**, price list, list of validated tools) then:
  "The sub-commission, composed of a chair and 2 to 4 neutral experts... **evaluates
  the results** and delivers, if necessary through exchange with the applicant in
  an iterative process, the conformity certificate."
- **§4.6.2 "Procedure"** (ll. 2802--2818) --- iterative back-and-forth, no threshold.
- **Annex A / table 64** (ll. 2821--2892) --- gives for Test 4 the **list of
  result quantities** (§5), but **no criterion**.

Upstream: **SIA 380/2:2022 §2.2.2.5** (`sia_380_2_2022.txt` ll. 1048--1049) "all
calculation methods may be used provided they meet the requirements
of SN EN ISO 52016-1:2017, clause 7.2, as well as the validation per SIA 4010" and
**§6.2.2.4** (ll. 1556--1561) "They can demonstrate validation per
SIA 4010 for the systems considered". The standard **requires** validation and
does not quantify it anywhere.

-> **The chain of authority is closed and documented**:
`SIA 380/2 §2.2.2.5 / §6.2.2.4 -> SIA 4010 §4.4 -> {test specification, evaluation
workbook} -> SIA 4010 §4.6.1 (sub-commission judgement)`.
For Test 4, the first terminal link is empty; **the second alone carries the weight**.

### 3.3 The criterion wording is identical in three out of four specifications **[V]**

| Test | Annual sums | Frequency distributions |
|---|---|---|
| 1 | cases 600/640/900/940/600FF/900FF: "Es gibt dafuer **kein Abweichungskriterium**" (`spec_test1.txt` ll. 98--100) | case 1E: "Resultate fuer den Test 1E muessen im **Streubereich** der enthaltenen Referenzprogramme liegen" (ll. 102--104) |
| 2 | "Jahressumme...: **Mittelwert der Referenzprogramme +/- maximale Abweichung**" (`spec_test2.txt` ll. 107--108) | "muss im **Streubereich** der Referenzprogramme liegen" (ll. 109--110) |
| 3 | "Jahressumme: **Mittelwert +/- max. Abweichung der Referenzprogramme**" (`spec_test3.txt` l. 153) | "**Haeufigkeitsverteilung innerhalb des Streubereichs** der Referenzprogramme" (l. 155) |
| **4** | **absent** | **absent** |
| 5 | "**Zulaessiger Bereich fuer Jahressummen: Mittelwerte der Referenzprogramme +/- maximale Abweichung.**" (`spec_test5.txt` ll. 274--276) | "Die **Haeufigkeitsverteilungen** muessen im **Streubereich** der Referenzprogramme liegen." (ll. 278--280) |

Key point for reading the silence: **SIA knows how to write "no criterion"
when it wants to** (Test 1, l. 100). Test 4 writes neither one nor the other. Its
silence is therefore a **document defect**, not an exemption. `[I]`

### 3.4 The Test 4 workbook does tabulate a band, and on exactly 3 rows **[V-orch]**

`PREUVE_classeur_test4.txt`, sheet `Zusammenfassung` (307 x 90):

| Cell | Content | Evidence line |
|---|---|---|
| `T8` / `U8` / `V8` | `Mittelwert` / `obere Grenze` / `untere Grenze` | l. 11 |
| `A8` / `J8` | `Jahreswerte` / `Maximalwerte` (block titles) | l. 11 |
| `A9` / `J9` | `Testgroessen` / `Diagnosegroessen` (subtitles) | l. 12 |
| `A10`--`A12` | `Energiebedarf Ventilatoren`, `Waermezufuhr Lufterwaermer`, `Waermeabfuhr Luftkuehler total` | ll. 13--15 |
| `A13` | `Diagnosegroessen` | l. 16 |
| `A14`--`A17` | `Energiebedarf Zuluftventilator`, `Energiebedarf Abluftventilator`, `Waermezufuhr WRG`, `Waermeabfuhr Luftkuehler latent` | ll. 17--20 |
| `A19` | `Stuendliche Haeufigkeitsverteilung` | l. 21 |
| `D8`--`H8` | program names: `Daten Testprogramm`, `Daten IDA_ICE`, `Daten Excel`, `Daten EnergyPlus`, `Daten TAS` | l. 11 |

The Test 4 band headers are **exactly the three labels** whose
formula was recorded in the Test 1 and Test 2 workbooks (`PREUVE_classeurs.txt`
ll. 6--8, 14--16, 25--27, 34--36):

```
Test 1, case 1E    G16 = AVERAGE(C16:F16)
                   H16 = G16 + MAX(ABS(C16-G16),ABS(D16-G16),ABS(E16-G16),ABS(F16-G16))
                   I16 = MAX(0, G16 - MAX(ABS(C16-G16),...))            (PREUVE_classeurs.txt ll. 9-11)
Test 2, annual     M14 = AVERAGE(E14,H14,K14,L14)
                   N14 = M14 + MAX(ABS(E14-M14),...)
                   O14 = M14 - MAX(ABS(E14-M14),...)                    (ll. 28-30)
```

-> **[A + I]** Same headers, same workbook template, same author, same test
family: the Test 4 band uses the same construction. This is the only construction
SIA has ever rendered numerically under these labels.

### 3.5 KEY ARGUMENT --- in this corpus, "the workbook tabulates a band" <=> "a criterion applies" **[V-orch]**

`AUDIT-swiss-sia-existant.md` ll. 174--182, actual execution of the seven loaders on the
seven official workbooks:

| Test | Metrics | With band | Cases covered |
|---|---|---|---|
| 1 | 28 | 28 | **1E only** |
| 4 | 3 | 3 | Test 4 |

Test 1 has six cases **explicitly without criterion** (§3.3) and a single case
with criterion: **the workbook tabulates a band only for that case**. The columns
`Mittelwert / obere Grenze / untere Grenze` are therefore, in this corpus, a **reliable
marker for the existence of a pass/fail criterion**. The Test 4 workbook tabulates
three -> **Test 4 has a criterion, applying to three quantities.** This is the
strongest argument at my disposal, and it relies on no textual analogy.

Independent convergence on the **number 3**: the loader stops at the first
labelled row without a band (`workbook_loaders.py` ll. 660--661, "a labelled non-band
row ends the obligatory block"), i.e. `A13 = Diagnosegroessen`. It thus returns
exactly rows 10--12. Two distinct facts point to the same place: the
**label** `Testgroessen` (l. 12 of the evidence) and the **numerical absence** of a band
on rows 14--17.

### 3.6 The 4 Test 4 reference programs are identified and consistent **[V]**

Columns `E`, `F`, `G`, `H` of the workbook (`PREUVE_classeur_test4.txt` l. 11) <-> the
four Test 4 Anwenderberichte:

| Col. | Program | Report | Version |
|---|---|---|---|
| E | IDA-ICE | `anwender_test4_4.txt` l. 7 | 5.0 Beta 22 |
| F | Excel (EN ISO 52016-1 + EN 16798-7 + EN 16798-5-1 sheets) | `anwender_test4_1.txt` ll. 7--21 | iterative, 3--5 loops (ll. 39--42) |
| G | EnergyPlus / OpenStudio | `anwender_test4_2.txt` l. 7 | 9.1.0 |
| H | TAS (EDSL) | `anwender_test4_3.txt` l. 7 | --- |

Column `D` (`Daten Testprogramm`) is the **candidate** program: it must be
excluded from the mean, consistent with the Test 1 and Test 2 formulas which average
only the reference columns (`PREUVE_classeurs.txt` ll. 9, 28).

### 3.7 The Test 4 Anwenderberichte give NO criterion --- but two useful clues **[V]**

Negative result to record: all four reports were read in full; **none**
states how results were judged. They document only modelling choices and
qualitative observations. Two exploitable clues:

1. **The Test 4 judgement did involve frequency distributions.**
   `anwender_test4_1.txt` ll. 77--80: "Die erwarteten Abweichungen bei den
   Volumenstroemen treten v.a. in den Anfangsstunden auf und fuehren zu fehlenden
   Volumenstroemen im sehr tiefen Bereich und zu einer **hoeheren Anzahl in der naechst
   hoeheren Kategorie**. Ansonsten ist die Uebereinstimmung sehr gut." The author
   reasons in **counts per category**: this is the distribution criterion.
   `[I --- strong clue, but not a citation of the criterion]`
2. **Two reference programs diverge strongly on latent cooler power**
   --- in opposite directions: "Die latente Luftkuehlerleistung ist
   betraechtlich **hoeher** als bei anderen Programmen" (`anwender_test4_1.txt`
   ll. 86--87); "Latente Luftkuehlerleistung deutlich **tiefer** als bei anderen
   Programmen" (`anwender_test4_3.txt` l. 15). Yet `Waermeabfuhr Luftkuehler latent`
   is precisely classified as **Diagnosegroesse** (`A17`, under `A13`). Consistent: SIA
   does not impose a band where its own programs contradict each other. `[I]`
3. **Missing contributor to anticipate.** `anwender_test4_3.txt` l. 14: "Bei
   Anlagensimulationen wertet TAS **nur die Raumlufttemperatur** aus." -> TAS does
   not deliver **operative temperature**: it must be **excluded** from the
   contributor set for that distribution, never counted as zero
   (rule §5.3 of `streubereich-distributions.spec.md`). `[V for the declaration,
   I for the consequence]`

**Source defect to flag**: `anwender_test4_3.txt` ll. 10--12 (TAS report,
Test 4) mentions "Test 3", solar protection cases, and
"Sonnenschutzregelung 2 und 4" --- content manifestly **copied from the Test 2/3 report**.
This report is partially unusable; do not infer anything about Test 4
from it beyond ll. 14--15.

### 3.8 Test 5: the analogy is legitimate but remains an ANALOGY **[A]**

Test 5 shares with Test 4: the same example building (SIA 4010 §4.3,
`sia_4010_2023.txt` ll. 2680--2687 "For tests 4 to 7, an example building was
defined"), the same climate and period (`spec_test4.txt` ll. 5--7 /
`spec_test5.txt` ll. 5--7: SIA 2028 DRY normal Zurich Kloten, 1.1.2022--31.12.2022),
the same reference standards (SN EN 16798-7:2017 and SN EN 16798-5-1:2017, tab. 64
ll. 2880--2884 for Test 4 and ll. 2915--2921 for Test 5), the same family of
quantities (air flows, fan energy, heating/cooling coils, WRG) and the same
workbook template `Resultaterfassung`.

**What the analogy authorises**: carrying the *wording* of the criterion
(`spec_test5.txt` ll. 274--280) over to Test 4.
**What it does not authorise**: presenting that wording as a citation
applicable to Test 4. No SIA text says the Test 5 criteria apply to
Test 4. **This is an analogy, not a citation.**

Structural reinforcement element: Test 5 uses **the same partition
`Testgroessen` / `Diagnosegroessen`** in its workbook --- a partition already exploited by
existing code (`swiss_sia/reference_model/sia4010/distribution_reference.py`
ll. 607--608: `"scored_section": "Testgroessen"`, `"diagnostic_section":
"Diagnosegroessen"`). The interpretive framework applied to Test 4 in §3.5 is therefore the one
SIA uses in the neighbouring test whose criterion is written.

---

## 4. Counter-arguments to my own conclusion

**C1 --- The silence could be intentional: Test 4 = purely comparative test.**
Test 1 shows that SIA sometimes displays results "zum Vergleich" without
a criterion (`spec_test1.txt` ll. 96--100). Perhaps Test 4 is in that regime.
*Response*: refuted by §3.5 --- the Test 1 workbook **does not tabulate any band** for
the cases without criterion, while the Test 4 workbook tabulates three. A "no
criterion" regime with a tabulated band would be unprecedented in the corpus. **Counter-argument
lifted, but by structural evidence rather than textual.**

**C2 --- The `T/U/V` band could apply to `Maximalwerte`, not to
`Jahreswerte`. REAL RISK, NOT LIFTED.**
Column geometry (`PREUVE_classeur_test4.txt` l. 11): block 1 = `A` (label)
+ `D:H` (5 programs); block 2 = `J` (label `Maximalwerte`) + `M:Q` (5 programs);
then `T/U/V`. In the Test 2 workbook, the band columns follow
**immediately** after the program columns of their own block
(`M/N/O` after `D:L`; `Z/AA/AB` after `R:V` --- `PREUVE_classeurs.txt` ll. 24--39).
Applied as-is, this convention would attach `T/U/V` to the
`Maximalwerte` block --- meaning the Test 4 criterion applies to
**peak power** and not to annual sums, breaking from Tests 2/3/5.
*Partial response*: `J9 = Diagnosegroessen` (l. 12) qualifies the **entire**
`Maximalwerte` block as diagnostic; a pass/fail band on a block declared
diagnostic would be contradictory. Moreover the sheet's regular column step is
9 columns (labels at `A`, `J`, then `S`), making `S:V` a **third autonomous block**
rather than an appendix to the `J` block.
*Status*: argued, **not proven**. See §7.1 --- the formula of `T10` decides.
Under C2, class **4A** ("system-related required thermal capacity
calculation", tab. 63 ll. 2767--2769) would remain covered, but the controlled
quantity would change units (kW instead of kWh): **the stake is not cosmetic.**

**C3 --- The zero floor differs from one workbook to another.**
Test 1: `MAX(0, mean - deviation)` (`PREUVE_classeurs.txt` ll. 11, 19); Test 2: no
floor (ll. 30, 33, 39). I do not know which variant Test 4 applies, and I
**cannot normatively explain** this divergence. Impact on the verdict:
nil for energies and counts (positive), but the display of the lower
bound depends on it.

**C4 --- The final verdict does not belong to the tool.**
SIA 4010 §4.6.1 (ll. 2796--2799) entrusts evaluation to a sub-commission of 2 to
4 neutral experts, §4.6.2 (ll. 2813--2818) organises an iterative back-and-forth with
improvement requests. **Our tool produces a prognosis, not a decision.**
For a test whose specification is incomplete, this is one more argument for a
rich display (band, min-max envelope, magnitude of exceedance) rather than a
bare binary --- cf. §5.5 of `streubereich-distributions.spec.md`.

**C5 --- Table 64 lists 6 test quantities, the workbook bounds only 3.**
My reconstruction (the other 3 are judged by frequency distribution, §5.2) is
**consistent but not attested**: no text distributes the Test 4 quantities
between "annual criterion" and "distribution criterion".

---

## 5. Quantities required by Test 4

### 5.1 Normative reference list --- SIA 4010:2023, Annex A, tab. 64 **[V]**

`sia_4010_2023.txt` ll. 2880--2892, line "4 Air conditioning for a single
room (all-air system)", columns "**Test** results" and
"**Diagnostic** results":

| # | Quantity (tab. 64, fr) | Workbook correspondence | Unit |
|---|---|---|---|
| 1 | air flow rate | `Zu-/Abluft-Volumenstrom` | **m3/h** [V] |
| 2 | fan energy | `Energiebedarf Ventilatoren` | kWh [I] |
| 3 | supply air temperature | `Zulufttemperatur (im Betrieb)` | degC [I] |
| 4 | indoor air temperature | `Mittlere Raumlufttemperatur` | degC [I] |
| 5 | air heater power | `Lufterwaermerleistung` / `Waermezufuhr Lufterwaermer` | kW / kWh [I] |
| 6 | air cooler power | `Luftkuehlerleistung total` / `Waermeabfuhr Luftkuehler total` | kW / kWh [I] |
| D1 | operative indoor temperature | `Operative Temperatur` | degC [I] |
| D2 | CO2 concentration | `CO2 Konzentration` | ppm [I] |
| D3 | latent air cooler power | `Luftkuehlerleistung latent` / `Waermeabfuhr Luftkuehler latent` | kW / kWh [I] |

**Test 4 therefore requires 9 quantities** (6 test + 3 diagnostic) --- and not 3.
`Warning` Normative status of Annex A (normative or informative) **not verified**:
the extraction does not carry the designation, and §4.2 l. 2676 says only "a matrix with
a more detailed characterisation... is found in Annex A".

### 5.2 Operational breakdown as the workbook organises it **[V-orch]**

**(a) Annual sums --- `Testgroessen`, WITH band (the criterion) --- 3 quantities**
| Row | Quantity | Unit |
|---|---|---|
| `A10` | Energiebedarf Ventilatoren | kWh `[I]` |
| `A11` | Waermezufuhr Lufterwaermer | kWh `[I]` |
| `A12` | Waermeabfuhr Luftkuehler total | kWh `[I]` |

**(b) Annual sums --- `Diagnosegroessen`, WITHOUT band --- 4 quantities**
`A14` Energiebedarf Zuluftventilator - `A15` Energiebedarf Abluftventilator -
`A16` Waermezufuhr WRG - `A17` Waermeabfuhr Luftkuehler latent (kWh `[I]`).

**(c) Peak values --- `Maximalwerte` block, declared `Diagnosegroessen` (`J9`) ---
7 quantities**: `J10` Leistungsbedarf Ventilatoren - `J11` Waermezufuhr Lufterwaermer -
`J12` Leistung Luftkuehler - `J14` Leistungsbedarf Zuluftventilator -
`J15` Leistungsbedarf Abluftventilator - `J16` Leistung WRG -
`J17` Leistung Luftkuehler latent (kW `[I]`). **Under C2, this block becomes the criterion
bearer.**

**(d) Hourly frequency distributions --- `Stuendliche Haeufigkeitsverteilung`
(`A19`), blocks of 7 columns starting at row 21 --- >= 10 quantities**
`B21` Zu-/Abluft-Volumenstrom (**m3/h**, `B22` [V]) - `I21` Zulufttemperatur im
Betrieb - `P21` Mittlere Raumlufttemperatur - `W21` Operative Temperatur -
`AD21` CO2 Konzentration - `AK21` Leistung Zuluftventilator -
`AR21` Leistung Abluftventilator - `AY21` Leistung Zu- und Abluftventilator -
`BF21` Lufterwaermerleistung - `BM21` Luftkuehler... (**label truncated in the evidence;
at least one additional block likely beyond `BM`** --- not verified).
20 frequency classes per quantity (rows 24--43, total in row 44:
`C44 = SUM(C24:C43)`), bounds read from a dedicated sheet `Haeufigkeitsklassen`
(`B24 = Haeufigkeitskassen!B4`, sic --- sheet name misspelled in the workbook).

**(e) Hourly diagnostic profiles** --- `A53` "Daten fuer stuendliche Verlaeufe",
`A54` winter week (working week 4, 24.--28.1.), quantities at row 57:
Zu-/Abluft-Volumenstrom (m3/h), Zulufttemperatur, Mittlere Raumlufttemperatur,
Leistung Ventilatoren, Lufterwaermerleistung, Luftkuehlerleistung total, Operative
Temperatur, CO2 Konzentration, Leistung Zuluftventilator, Leistung Abluftventilator,
Luftkuehl... (truncated). A column in **mg/s** exists (`S58`, `AI58`, `AZ58`, `BQ58`,
`CI58`): **unidentified** quantity (emitted CO2 flow rate?) --- to be elucidated.

### 5.3 Answer to the sub-question "the loader only finds 3: bug or reality?"

**Both, depending on what is being measured.**
- For the **annual band criterion**: 3 is **exact** --- it is the number of
  `Testgroessen` (§3.5), confirmed by two independent facts. **Not a coverage
  defect.**
- For **Test 4 coverage**: 3 out of 9 required quantities (tab. 64). The
  **frequency distribution criterion is not implemented at all** for
  Test 4: the key `"4"` is **absent** from `DISTRIBUTION_CRITERIA`
  (`distribution_reference.py` ll. 520--610, which covers only `"2"`, `"3"`, `"5"`).
  **That is the real gap**, not the number of bands.
- **The Test 5 mystery (16 metrics for 8 annual quantities) is resolved in
  passing**: Test 5 does not require all 8 quantities in all 4 variants, but a
  **different subset per variant** (`spec_test5.txt` ll. 250--271: 5A
  fans + Lufterwaermer + Luftkuehler total; 5B adds WRG total/latent;
  5C air flows + WRG + Luftkuehler latent; 5D Lufterwaermer + Befeuchter), i.e. 4 per
  variant x 4 = 16. **The Test 5 loader is therefore not in coverage deficit
  either** on annual bands. `[V]`

---

## 6. Retained formula --- ready for implementation

### 6.1 Criterion A --- annual sums (the 3 `Testgroessen`)

```
P            = { IDA-ICE, Excel, EnergyPlus, TAS }        # columns E,F,G,H -- NEVER D
               minus any program that did not deliver the quantity (excluded, not counted as 0)
n            = |P|
mean(q)      = (1/n) * Sum_{p in P} x_p(q)                # simple arithmetic mean
max_dev(q)   = max_{p in P} | x_p(q) - mean(q) |
upper(q)     = mean(q) + max_dev(q)
lower(q)     = mean(q) - max_dev(q)                       # zero floor: see C3
VERDICT(q)   : lower(q) <= x_candidate(q) <= upper(q)     # CLOSED interval

q in { Energiebedarf Ventilatoren,
       Waermezufuhr Lufterwaermer,
       Waermeabfuhr Luftkuehler total }                    # rows A10..A12
```

**No additional tolerance.** No source authorises one. An IEEE-754
floating-point comparison epsilon is an **implementation detail**, never a
normative tolerance, and any verdict that would flip because of it must be
logged.

**The bounds must NOT be recomputed if the workbook tabulates them**: read
`U10:V12` (or the homologous columns resolved by header) and **verify** that the
recomputation reproduces them. A discrepancy signals a reading error, not a tolerance.

### 6.2 Criterion B --- hourly frequency distributions

Apply **identically** `traceability/streubereich-distributions.spec.md` §5
(symmetric band per frequency class, contributor set read from the `AVERAGE` ranges,
three-state output). Quantities: the row-21 blocks (§5.2 d).
**Status: ANALOGY** --- the word `Streubereich` appears nowhere in the Test 4
sources; it is carried over from Tests 2/3/5. Corroborated by
`anwender_test4_1.txt` ll. 77--80 (§3.7).

### 6.3 Quantities without criterion --- display only, never sanction

The 4 annual `Diagnosegroessen` (§5.2 b) and the `Maximalwerte` block (§5.2 c) are to
be displayed comparatively, **without verdict**, as long as C2 is not lifted. If C2 is
overturned (band on `Maximalwerte`), reverse: the peak block becomes the criterion
bearer and the annual sums become display-only.

### 6.4 Mandatory mention in UI and report

> "Test 4: the SIA specification contains no acceptance criterion. The
> criterion applied is the one tabulated by the official workbook
> `Resultaterfassung Test4.xlsx`, using the construction employed by Tests 2, 3
> and 5. Verdict to be confirmed with the SIA 4010 sub-commission (§4.6.1)."

Do not hide this caveat: this is the only test of the seven whose criterion has no
textual support of its own.

---

## 7. What remains NOT VERIFIED

### 7.1 BLOCKING --- the formula of `T10` (maximum criticality)

What must be extracted from `Resultaterfassung Test4.xlsx`, sheet `Zusammenfassung`,
with `openpyxl(data_only=False)`:

| To extract | What it decides |
|---|---|
| **formula of `T10`, `U10`, `V10`** | **C2**: if `AVERAGE(E10:H10)` -> **annual** band, §6.1 verdict confirmed. If `AVERAGE(N10:Q10)` -> band on **Maximalwerte**, §6.1 to rewrite in kW. |
| the exact range of the `AVERAGE` | the contributor set, and **whether column `D` (candidate) is included** --- it must not be |
| presence or absence of `MAX(0, ...)` in `V10` | C3, zero floor |
| `T14:V17` (empty or not) | confirms that `Diagnosegroessen` have no band |
| `R8`, `S8`, `S9`, `J13` | block geometry, anti-C2 argument |

Without `T10`, confidence on *which quantity* is bounded plateaus at ~70%.
**A single `openpyxl` call suffices.**

### 7.2 Other open points

| # | Point | How to resolve |
|---|---|---|
| 1 | Actual units of rows 10--17 (kWh? MJ? kWh/m2?) | unit cell per row of the workbook (`_first_unit_in_row`, `workbook_loaders.py` ll. 606--613) --- **not extracted** |
| 2 | Labels beyond `BM21` (missing distribution blocks) | full scan of row 21 up to column 90 |
| 3 | Bounds of the 20 frequency classes | sheet `Haeufigkeitskassen` (sic), columns `B` and `C`, rows 4--23 |
| 4 | Quantity in **mg/s** (`S58`) | row 57 of the workbook, columns `S` and beyond |
| 5 | Page 3 of `Spezifikation_Test4.pdf` as **visual rendering** | definitively rules out the hypothesis "block present but not extractable" |
| 6 | Class-to-test alignment of tab. 63 (classes 3, 4A, 4B) | visual reading of p. 48 of SIA 4010:2023 |
| 7 | Normative/informative status of **Annex A** | first page of Annex A in the PDF |
| 8 | **SIA 4010 FAQ** --- announced by §4.6.1 ll. 2790--2792 as containing "increasingly the questions arising from completed tests and the answers thereto" | download from www.sia.ch/sia4010 --- **not in repository**. This is the venue *designed* for this question: a truncated specification is exactly the kind of point a previous candidate must have raised. |
| 9 | **Direct question to the sub-commission** | procedure provided for by §4.6.2 ll. 2804--2818. Only definitive answer for a test whose specification is incomplete. **Recommended before any real validation dossier.** |
| 10 | **German** version of SIA 4010:2023 | not consulted. Expected yield low (§4.4 delegates regardless), but not verified. |
| 11 | `SN EN 16798-5-1:2017`, `SN EN 16798-7:2017`, `SN EN ISO 52016-1:2017` | **absent from `/refs`**. They define the Test 4 *models* (tab. 64 ll. 2880--2892), **not** the acceptance criterion. No value or table was cited from them here. |

### 7.3 What would change my mind

1. **`T10 = AVERAGE(N10:Q10)`** (or any range from the `M:Q` block) -> C2 is confirmed, the
   criterion applies to peak power; §6.1 must be rewritten. **Immediate
   reversal.**
2. **`T14:V17` non-empty** -> the `Diagnosegroessen` also carry a band; the
   loader is then in coverage deficit and the number 3 is wrong.
3. **A page 4 of `Spezifikation_Test4.pdf`**, or a *Testkriterien* block visible
   on page 3 -> Test 4 recovers its own criterion; the analogy becomes unnecessary and
   confidence rises to the level of Tests 2/3/5.
4. **An entry in the SIA FAQ** explicitly deciding -> authority superior to
   any inference above, regardless of direction.
5. **`Spezifikation_Test6/7.pdf` also without a *Testkriterien* section** -> the
   silence would become a recurring pattern rather than an accident, weakening
   the "editorial omission" hypothesis (§3.1) without restoring a criterion.
