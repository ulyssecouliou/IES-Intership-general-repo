> **Note:** Translated from French original. See [streubereich-distributions.spec.md] for the source document.

# Normative arbitration — Streubereich of the frequency distribution criterion (SIA 4010 Tests 2 to 6)

> **PRIOR DECISION SUPERSEDED — 2026-08-10.** A written clarification from
> Prof. Gerhard Zweifel confirms that the `Streubereich` for distributions is
> the **minimum-to-maximum envelope of the reference programs, class by
> class** (interpretation #1). The historical derivation `mean ± maximum
> deviation` preserved below is no longer normative; it remains only
> to explain and reproduce earlier audits. A second clarification from
> 2026-08-10 confirms that the series do contain 8,760 hours: the visible
> totals that are lower correspond only to the displayed classes, with some
> values falling outside their bounds. These hours are audited separately; they
> are neither classified as missing, nor added to the last class.
>
> The same response indicates that the Test 4 and Test 6 workbooks do contain
> classes and distributions. Local verification: both have a
> `Haeufigkeitskassen` sheet, `Stündliche Häufigkeitsverteilung`
> tables in `Zusammenfassung`, and numerous dedicated charts. The earlier
> contrary assertion is withdrawn. A subsequent written response from Yiqiao confirms that
> the deliverables for Tests 4, 6, and 7 are those indicated in the
> Excel workbooks: their **output scope is therefore confirmed**. That response
> does not, however, state that every distribution or diagnostic quantity is a
> PASS/FAIL criterion; the exact scope of the 4/6 acceptance gate remains separately
> fail-closed.

> Historical status: **SUPERSEDED BY WRITTEN CLARIFICATION.**
> Author: `norm-analyst`, 2026-07-30.
> Scope: only the criterion "Häufigkeitsverteilung … im Streubereich der
> Referenzprogramme liegen" for Tests 2, 3, 5 (Test 4: see §6.2).

---

> ## ✅ ORCHESTRATOR VERIFICATION — 2026-07-30, after delivery of the arbitration
>
> The `norm-analyst` has no tool to open a PDF or `.xlsx`. Three of the
> points left open were a matter of extraction, not standard interpretation:
> they are addressed here. **Verdict confidence rises from ~85 % to ~92 %.**
>
> **1. The load-bearing link is closed (§7.1).** `Spezifikation_Test1.pdf` was
> extracted as full text and read directly. Under the heading *Testkriterien*
> (l. 69) appears, l. 102:
> "Resultate für den Test 1E müssen im **Streubereich** der enthaltenen
> Referenz[programme] …"
> The citation attested by the prior session is therefore **confirmed first-hand**.
> The transfer of meaning from Test 1 → Tests 2-5 rests on the same word, in
> the same type of heading, and that criterion is the one the workbook computes as
> `mean ± max|deviation|` (formulas recorded: `H16`, `I16`, `H82`, `I82`).
> The fallback hypothesis "if Streubereich is not found there, revert to undecidable" is
> **dismissed**.
>
> **2. The word does not appear in ANY workbook.** Search for `Streubereich` in
> `xl/sharedStrings.xml` of all seven `Resultaterfassung`: **0 occurrences** everywhere.
> The term lives exclusively in the specifications; the workbooks render it
> under the labels `Mittelwert` / `obere Grenze` / `untere Grenze`. This **reinforces**
> the reasoning: there is no second tabulated meaning somewhere that
> would contradict the Test 1 meaning.
>
> **3. Test 4 genuinely has no criterion in its spec (§6.2 confirmed).** This
> is not an extraction artefact: the spec is 3 pages, was re-extracted in
> raw mode (208 lines) and searched via encoding-insensitive search —
> `Testkriterien`, `Streubereich`, `Mittelwert`, `Abweichung`, `Häufigkeitsverteilung`:
> **0 occurrences of each**. The document ends with the HVAC sizing parameters.
> The Test 4 criterion therefore exists only in its workbook, which
> does tabulate bands (3 metrics extracted). To be treated as a separate
> normative item.
>
> **4. The chart counter-argument is lifted (§7.2).** The 50 charts in the
> Test 2 workbook have been inventoried. The most elaborate, `chart9`, is a
> **histogram (`barChart`) with 9 series**, plotting `Zusammenfassung!$CS$32:$CX+$51`
> — i.e. the frequency class zone for case 2D. The 9 series are named in
> row 30: `Testprogramm Fe einfach`, `IDA_ICE Fe det Spec`, `IDA_ICE Fe det
> noSpec`, `IDA_ICE Fe einf`, `Excel SIA 387/4 + 380/2`, `EnergyPlus Fe det Spec`,
> `EnergyPlus Fe det nonSpec`, `EnergyPlus Fe einf`, `TAS Fe det nonSpect`.
> **No band series, no min/max envelope, no area chart.**
> The workbook simply superimposes the program histograms.
> SIA therefore materialises the distribution band **nowhere**: neither tabulated,
> nor plotted. The only definition it has ever rendered numerically for this exact word
> remains `mean ± max|deviation|`. The counter-argument loses its material support.
>
> **5. DISCOVERY — the contributing set is a normative selection, not "all
> programs".** The annual band for Test 2 averages **4** values whereas the
> workbook contains **8** reference columns. The columns retained by the
> formula `M14 = AVERAGE(E14,H14,K14,L14)` are, according to headers L9/L10:
>
> | Column | Program | Retained variant |
> |---|---|---|
> | E | IDA_ICE | **Fe det Spec** |
> | H | Excel | (single variant) |
> | K | Energy+/OpenStudio | **Fe einf** |
> | L | EDSL-Tas | **Fe det nonSpect** |
>
> Excluded: F, G (other IDA_ICE variants) and I, J (other Energy+ variants).
> **One variant per program — and not the same one across programs.** An
> implementation that averaged all 8 columns, or that chose a uniform variant,
> would produce a different band and therefore false verdicts.
> Second point confirmed: `M15 = AVERAGE(E15,H15,K15)` — for case 2B, TAS
> disappears (it did not deliver this case, cf. Anwenderbericht TAS). A missing
> program is excluded from the average, never counted as zero.
>
> **Implementation rule that follows**: the contributing set cannot be
> guessed; it must be **read from the annual band formula in the workbook**
> (the columns referenced by `AVERAGE`), then applied identically to the frequency
> classes. This is verifiable and reproducible, unlike any convention
> chosen a priori.

---

## 1. The question

The Streubereich of the reference programs, to be constructed class by frequency class
since it is not tabulated in the workbook, is it **(a)** the symmetric band
`mean ± max|program − mean|`, or **(b)** the envelope
`min(programs) .. max(programs)`?

## 2. Verdict

**(a) SYMMETRIC BAND** — `mean ± max|program − mean|`, applied per frequency class:
this is the only construction that SIA has ever rendered numerically for this exact word,
in its own workbook, for the sole Test 1 criterion that carries the same
label. **Confidence level: HIGH (~85 %)** — not absolute, because the deduction rests
on a transfer of meaning from Test 1 to Tests 2–5, and on a Test 1 citation
that I was not able to re-read myself (§7.1).

---

## 3. Evidence, citation by citation

Convention: **[V]** = verified by me in a source read this session; **[V-2e]** =
attested by an internal deliverable independently re-checked but whose primary source
is not readable by me; **[I]** = inference, marked as such.

### 3.1 The criterion wording is indeed homogeneous across Tests 2, 3, and 5 **[V]**

| Test | "Annual sum" criterion | "Distribution" criterion |
|---|---|---|
| 2 | "Mittelwert der Referenzprogramme +/- maximale Abweichung" (`spec_test2.txt` l. 108) | "Häufigkeitsverteilung … : muss im **Streubereich** der Referenzprogramme liegen" (l. 109-110) |
| 3 | "Jahressumme: Mittelwert +/- max. Abweichung der Referenzprogramme" (`spec_test3.txt` l. 153) | "Häufigkeitsverteilung innerhalb des **Streubereichs** der Referenzprogramme" (l. 155) |
| 5 | "**Zulässiger Bereich** für Jahressummen: Mittelwerte der Referenzprogramme +/- maximale Abweichung." (`spec_test5.txt` l. 274-276) | "Die Häufigkeitsverteilungen müssen im **Streubereich** der Referenzprogramme liegen." (l. 278-280) |

(Sources: `…\scratchpad\norme\spec_test2.txt`, `spec_test3.txt`, `spec_test5.txt` —
full-text extractions of the `Spezifikation_TestN.pdf`, section *Testkriterien*.)

None of the three is more explicit than the others: **Test 5, the most detailed, does
not define the term any further.** It does, however, contribute a useful vocabulary point
(§3.4).

### 3.2 SIA 4010:2023 is SILENT on the term and on the criterion **[V]**

- Search for `Streu` across all of `…\scratchpad\norme\`: **0 occurrences** in
  `sia_4010_2023.txt`. The pattern is purely ASCII; no hyphenation can
  have masked it (a hyphenated "Streu-bereich" would still contain "Streu").
- Important factual note: **the copy at hand is the FRENCH version**
  (`sia_4010_2023.txt` l. 8-15, "SNG 594010:2023 fr"). The corresponding French
  searches — `dispersion`, `fréquence`, `écart`, `critère`, `tolérance`,
  `programmes de référence` — **likewise return no relevant occurrence**
  (only "Plage pratique, à titre informatif" from EN input tables, l. 1443,
  1527, 1614, 2014, 2041).
- The reason is structural, and it is written: SIA 4010 §4.4 (l. 2695-2702) delegates
  *all* descriptions and criteria to the separate documents and to the EXCEL
  evaluation file: "Les descriptions détaillées de chaque test sont disponibles sous
  forme de documents séparés sur www.sia.ch/sia4010. Pour chaque test, un fichier
  d'évaluation EXCEL est disponible … qui génère la représentation comparative des
  résultats avec les résultats de référence."

→ **The umbrella standard will never settle this point.** The only available authority is the
pair {test specification, evaluation workbook}.

### 3.3 CENTRAL EVIDENCE — SIA has already rendered this word numerically, once, and it is (a)

Chain of four links:

1. **Test 1 uses the SAME word for its sole pass/fail criterion.** `[V-2e]`
   `traceability/test-1.spec.md` l. 299-302, citation given as verified word for word
   against `SIA_4010_geteilter_Link/Test1/Spezifikation_Test1.pdf`, heading *Testkriterien*:
   "**Resultate für den Test 1E müssen im Streubereich der enthaltenen Referenzprogramme
   liegen**". Same document l. 295-298: cases 600/640/900/940/600FF/900FF have
   **no** criterion ("Es gibt dafür kein Abweichungskriterium"). Case 1E is therefore the
   **only** place in Test 1 where the word "Streubereich" commands a verdict.

2. **The Test 1 workbook tabulates a band — and only one — for this case 1E, and it is the
   symmetric band.** `[V]` `PREUVE_classeurs.txt` l. 5-22 (formulas recorded with
   `openpyxl data_only=False` on `Resultaterfassung_Test1.xlsx`):

   ```
   Table 28 (besoins mensuels, cas 1E)      G16 = AVERAGE(C16:F16)
                                            H16 = G16 + MAX(ABS(C16-G16),…,ABS(F16-G16))
                                            I16 = MAX(0, G16 - MAX(ABS(C16-G16),…))
   Table 31 (charges de pointe hor., cas 1E) idem, lignes 82-83
   ```
   Headers: `Mittelwert` / `obere Grenze` / `untere Grenze` (G15/H15/I15, G81/H81/I81).

3. **This formula is verified numerically, independently, without sampling.**
   `[V]` `AUDIT.md` l. 60-67 and l. 142 (`qa-auditor`, pass 3): "the `Streubereich`
   is **NOT** the simple min/max of the 4 programs. The actual formula is
   `range_max = mean + max_deviation`, `range_min = max(0, mean − max_deviation)`,
   `max_deviation = max|program − mean|` (symmetric band, floored at 0). Verified
   **26/26**. The hypothesis 'range = min/max of programs' is **false**."
   Cross-checked by hand on Table 31: `AUDIT-swiss-sia-existant.md` l. 109-113
   (mean 1.75245555 = G82; max deviation 0.0913288; 1.8437844 = H82; 1.6611267 = I82).

4. **Tests 2 to 5 use the same word for the same purpose** (commanding a verdict
   "… liegen"), on reference programs of the same nature. `[V]` §3.1 above.

→ **Conclusion**: when SIA had to turn "im Streubereich … liegen" into a computable
rule, it wrote `mean ± max|deviation|`. This is the operational definition
of the term in the SIA 4010 corpus. `[I, but a short and direct inference]`

### 3.4 Two corroborating clues, weak but convergent **[I]**

- **The zero floor is itself evidence of construction.** `MAX(0, …)`
  (`PREUVE_classeurs.txt` l. 11, 19) only makes sense if the lower bound can drop
  **below** the smallest observed value, and even below zero. A min–max envelope of
  positive quantities can never be negative: the safeguard would be stillborn. Its
  presence attests that the author was indeed constructing a symmetric band detached from
  the data.
- **The choice was the costliest to write.** `MIN(C16:F16)` / `MAX(C16:F16)` was shorter
  and more natural if the envelope was intended. The author wrote
  `G16+MAX(ABS(C16-G16),ABS(D16-G16),ABS(E16-G16),ABS(F16-G16))`. A deliberate choice.
- **Test 5: "Zulässiger Bereich" = mean ± max deviation** (`spec_test5.txt` l. 274-276).
  SIA therefore names *admissible range* exactly construction (a). That the next
  sentence calls *Streubereich* the admissible range for distributions does not introduce
  a semantic break; it is the same author, the same paragraph.

### 3.5 The Anwenderberichte for Test 2: NO evidence on band construction **[V]**

All four reports were read in full (`anwender_test2_1..4.txt`). **None**
describes how the distribution was judged. They only document modelling choices
and limitations. Negative result, to be acknowledged: this avenue does not settle the matter.

However, they do contribute an element **useful for implementation** (non-contributing
programs, §5.3):
- EXCEL (`anwender_test2_1.txt` l. 19-28): ground-state-dependent albedo, hence
  "zu gewissen Zeiten mit Neuschnee erheblich höhere Einstrahlungswerte" and
  "entsprechend enthält die **Verteilung** der Einstrahlung eine beschränkte Anzahl
  Stunden mit höheren Werten". → a reference program is a **documented and accepted
  outlier in the distribution**, and SIA **kept it** in the reference set.
- TAS (`anwender_test2_3.txt` l. 10-20): no louvre model ("Kein
  Lamellenmodell"), hence "nur der Testfall 2 sowie der Testfall 4 mit einer
  Stoffmarkise gerechnet"; "Sekundärer solarer Wärmeeintrag nicht auswertbar";
  "Solare Einstrahlung nur als Summe".
- EnergyPlus (`anwender_test2_2.txt` l. 18-24): solar gains available only
  with the simple window model.
- IDA ICE (`anwender_test2_4.txt` l. 13-15): no particular assumptions.

These declarations explain exactly why the workbook averages are computed over
**variable** program sets: `M14 = AVERAGE(E14,H14,K14,L14)` (4 programs) but
`M15 = AVERAGE(E15,H15,K15)` (3), and `Z14 = AVERAGE(R14,U14,V14)` (3) for the other
quantity (`PREUVE_classeurs.txt` l. 28-39).

---

## 4. Counter-arguments to my own conclusion (presented honestly)

**C1 — The dual-label argument.** In the *same* *Testkriterien* block, the author
writes the formula out in full for the annual sum and uses a different word
for the distribution. Why switch, if not to designate something different? This is
the strongest argument in favour of (b) and it is **not refutable from the text alone**.
*My response* `[I]`: Test 1 demonstrates that "Streubereich" is, for this author, the generic
name of the band he computes as mean ± max deviation — he uses it alone, without a formula,
where the workbook applies (a). The asymmetry in wording is better explained by the
asymmetry of *tabulation*: the annual sum is a single number per case, tabulated, so
its formula is spelled out; the distribution is a vector of hundreds of classes, not
tabulated, hence designated by the generic word. This is a plausible explanation, not a proof.

**C2 — The chart argument.** The workbook tabulates no band for the
distributions (`PREUVE_classeurs.txt` l. 43-48: exhaustive scan of rows 26-308,
columns 1-239, zero `Mittelwert` / `obere Grenze` / `untere Grenze`). The judgement is
therefore, in practice, made on a **superposition of curves**. Visually, "the
candidate curve is within the Streubereich of the reference curves" reads spontaneously as
"between the lowest and the highest" — i.e. (b). This is a serious argument and I
cannot dismiss it: I was not able to open the workbook charts to see which
series are plotted there (§7.2).

**C3 — The asymmetry of risk is not one-sided.** Since `[min,max] ⊆ [mean−deviation, mean+deviation]`,
(a) is always more permissive. Choosing (a) eliminates the risk of **false failure** — but
symmetrically creates a risk of **false pass**: declaring "compliant" to a client whose
dossier the SIA sub-commission would then reject. The treatment of this risk is
incorporated in §5.5 (dual display): it is not resolved by choosing the other band; it
is resolved by **making the gap visible**.

**C4 — The final verdict does not belong to the tool.** SIA 4010 §4.6.1 (l. 2796-2799):
"La sous-commission, composée d'un président et de 2 à 4 experts neutres … évalue les
résultats et délivre, si nécessaire en échangeant avec le demandeur dans le cadre d'une
procédure itérative, l'attestation de conformité." §4.6.2 (l. 2813-2818) explicitly provides
for a back-and-forth with requests for improvements. **Our tool produces a
prognosis, not a decision.** This argues for a rich informative display rather than
a dry binary — and makes the (a) vs (b) choice less irreversible than it might appear.

---

## 5. Retained formula — ready for implementation

### 5.1 Definition

Let `c` be a test case, `q` a controlled quantity, and `b` a frequency class.
Let `P(c,q)` be the set of **contributing reference programs** for this pair
(§5.3), and `x_p(c,q,b)` the value of class `b` of the distribution from program
`p ∈ P(c,q)`.

```
n        = |P(c,q)|
moyenne  = (1/n) · Σ_{p∈P}  x_p                       # moyenne arithmétique simple, non pondérée
écart_max= max_{p∈P} | x_p − moyenne |                # écart absolu maximal à la moyenne
borne_sup= moyenne + écart_max
borne_inf= max(0, moyenne − écart_max)                # plancher à zéro : voir 5.2
VERDICT(b) : borne_inf ≤ x_candidat(c,q,b) ≤ borne_sup     # intervalle FERMÉ
```

Bounds are **inclusive** (closed interval). The text says "**im** Streubereich … **liegen**"
(`spec_test2.txt` l. 110, `spec_test5.txt` l. 278-280), with no mention of strict
inequality; inclusion is the standard reading. `[I — interpretation, uncontested by
any source]`

Floating-point comparison: if a numerical safeguard is necessary, it must be declared
an **implementation detail** (relative epsilon of a purely IEEE-754 nature), **never** a
normative tolerance, and any verdict that flips because of it must be logged.
No source authorises a tolerance on this criterion.

### 5.2 Zero floor

**To be applied** (`borne_inf = max(0, …)`), for consistency with the sole tabulated precedent
(Test 1, `PREUVE_classeurs.txt` l. 11 and 19). Test 2 does not apply it for its
**annual** values (l. 30, 33, 39: `O14 = M14 - MAX(...)` without `MAX(0,…)`) — a genuine
divergence between workbooks, which I **cannot explain normatively**.

**Impact on verdict: nil.** The frequency classes are counts (number of hours)
or fractions, hence `x_candidate ≥ 0`. Whether the lower bound equals `0` or a
negative value, the set of accepted candidates is identical. The floor is therefore
only a display question. **I recommend applying it and indicating it in the UI**
("theoretical lower bound negative, clamped to 0"), which informs the user that the
band is not constraining on the low side for that class.
`[I — arithmetic reasoning, verifiable]`

### 5.3 Non-contributing programs

**Rule: a missing program is EXCLUDED from `P(c,q)` — never counted as zero.**
Verified basis: `M15 = AVERAGE(E15,H15,K15)` vs `M14 = AVERAGE(E14,H14,K14,L14)`,
and `Z14 = AVERAGE(R14,U14,V14)` (`PREUVE_classeurs.txt` l. 28-39). The contributing set
varies **by case** *and* **by quantity**, which the Anwenderberichte explain
exactly (§3.5). `[V for annual values; I for the extension to distributions]`

Extension to distributions: **inference**, but the alternative is absurd — counting
0 hours in every class for a program that did not deliver the case would distort
mean *and* max deviation massively.

**Pitfall not to be ignored.** In the distribution zone, a non-contributing program
will probably appear as an **empty or all-zero column**, indistinguishable from a
program that genuinely delivered an all-zero distribution. **Do not deduce membership
in `P(c,q)` solely from cell emptiness.** The contributing set must be established from
the `AVERAGE` ranges of the **annual values** — which encode SIA's own decision — and
cross-checked against the Anwenderbericht declarations. It must be **frozen
explicitly in the reference JSON**, case by case and quantity by quantity, not
recomputed on the fly. `[I — engineering rule, justified]`

### 5.4 What data to compute the band from

From the **distribution values already tabulated per program in the workbook**
(`Resultaterfassung_TestN.xlsx`, `Häufigkeitsklassen` zone), and not from a home-grown
rebinning of the raw hourly series — unless it has been proven that our binning exactly
reproduces the workbook's (class bounds, open/closed intervals,
raw counts vs %, cumulative or not). These characteristics **are not established to date**
and fall under `reference-data-engineer` (§7.2).

### 5.5 Required UI output (protection against C3)

The tool computes and displays **both** constructions:
- **(a)** band `mean ± max_deviation` → **verdict basis**;
- **(b)** envelope `min..max` of programs → **displayed as overlay**, without verdict.

Three states per class, instead of two:
| State | Condition |
|---|---|
| **CONFORME** | `x_candidate ∈ [min, max]` (within the envelope, hence compliant under both readings) |
| **CONFORME — RÉSERVE** | `x_candidate ∈ [borne_inf, borne_sup] \ [min, max]`: compliant under (a), outside the program envelope |
| **HORS BANDE** | `x_candidate ∉ [borne_inf, borne_sup]` (non-compliant under both readings) |

Any class in "CONFORME — RÉSERVE" is a discussion point to prepare for the
sub-commission (SIA 4010 §4.6.2, l. 2813-2818). This output neutralises the risk
on both sides and makes the arbitration reversible without rewriting the engine.

---

## 6. DISTINCT open items revealed by the analysis (not to be confused with the settled question)

### 6.1 Severity: how many out-of-band classes cause the test to fail? — NOT SETTLED

The text says "**die** Häufigkeitsverteilung … muss … liegen": the distribution, as an
object, must be within the band. The strict reading is "**all** classes". No
source, neither specification nor workbook, authorises a quota of out-of-band classes.
**But**: applying a "one class out of band ⇒ failure" rule to a criterion that SIA has
judged visually by a sub-commission (§4.6.1) would likely be more stringent
than actual practice. **Recommendation**: the tool should **not** render a
bare "NON CONFORME"; it should render `N classes out of band out of M`, with the list, the
class involved, and the magnitude of the exceedance. A point to have the
sub-commission arbitrate, not us. `[I — flagged, not settled]`

### 6.2 Test 4: criterion wording NOT VERIFIABLE in the supplied extraction

`spec_test4.txt` (3 pages, complete to "3 / 3" l. 131) **contains no
*Testkriterien* heading**. Searches for `Testkriterien`, `Kriterium`,
`Testgrösse`, `Streu`, `Bereich`, `Häufigkeit`, `Verteilung`, `Abweichung`, `Auswertung`,
`Resultaterfassung`, `Mittelwert` were unsuccessful: **0 occurrences**. The block was lost in the
extraction (text frame not captured). **I therefore cannot confirm that Test 4 carries the same
criterion.** To be re-extracted before applying this decision to Test 4.

---

## 7. What remains UNVERIFIED

### 7.1 The load-bearing citation (maximum criticality)

The verdict rests on the fact that the **Test 1** specification literally uses
"im **Streubereich** der enthaltenen Referenzprogramme liegen". I was **not able to read
it myself** from `SIA_4010_geteilter_Link/Test1/Spezifikation_Test1.pdf` (tool `Read`: PDF
rendering unavailable, "pdftoppm is not installed"). I rely on `traceability/test-1.spec.md`
l. 299-302, which gives the citation as verified word for word by a prior
`norm-analyst` session, and on `AUDIT.md` / `AUDIT-swiss-sia-existant.md` which
use the same term for the same case.
→ **Blocking action before freezing**: extract
`SIA_4010_geteilter_Link/Test1/Spezifikation_Test1.pdf` as text (`pdftotext`) and have me
re-read the *Testkriterien* heading verbatim. **If the word "Streubereich" is not found there,
link 1 of §3.3 breaks and the verdict falls back to "undecidable, slight advantage to (b)".**

Nuance not to be masked: the Test 1 workbook columns are labelled
`Mittelwert` / `obere Grenze` / `untere Grenze` — **never** `Streubereich`
(`PREUVE_classeurs.txt` l. 6-8, 14-16, 25-27). The link between the specification word
and the workbook formula is **functional** (it is the only band, for the only case
carrying a criterion), **not lexical**.

### 7.2 Missing sources that would settle the matter, in order of yield

| # | Source | What it would settle | How to obtain it |
|---|---|---|---|
| 1 | `Spezifikation_Test1.pdf`, heading *Testkriterien*, verbatim | The load-bearing link (§7.1) | **Already in the repository** — `pdftotext` extraction |
| 2 | **Chart** definitions from the `Häufigkeitsklassen` zone of `Resultaterfassung_Test2/3/5.xlsx` (`xl/charts/chartN.xml` in the zip) | Decisive against C2: if a `Mittelwert`/`obere Grenze`/`untere Grenze` series is plotted there (even from hidden columns or named ranges) ⇒ (a) confirmed; if only per-program curves are plotted ⇒ C2 is strengthened | **Already in the repository** — unzip the `.xlsx` |
| 3 | Scan for the string `Streubereich` in **all** sheets (including hidden ones) and **all** workbooks Tests 1 to 7 | If the word appears as a header next to a calculated column, the definition is lexically nailed | **Already in the repository** — `openpyxl`, all sheets |
| 4 | `Spezifikation_Test6.pdf` and `Spezifikation_Test7.pdf` + their workbooks | Additional occurrences of the pair {word "Streubereich", tabulated formula}. Each additional occurrence confirms or breaks the rule | **Already in the repository** |
| 5 | `Spezifikation_Test4.pdf` re-extracted | §6.2 | **Already in the repository** |
| 6 | **SIA 4010 FAQ** — SIA 4010 §4.6.1 (l. 2790-2792) announces "un document FAQ sur les tests, dynamique, c'est-à-dire qu'il contient de plus en plus les questions issues des tests réalisés et les réponses à celles-ci" | This is the venue *designed* for this kind of question; it is plausible that it has already been asked there | Download from www.sia.ch/sia4010 — **outside the repository** |
| 7 | **Direct question to the sub-commission** | Definitive | SIA 4010 §4.6.2 (l. 2804-2818) establishes the iterative exchange with the applicant: this is the path provided by the standard, and the cheapest in absolute terms |

### 7.3 Other unverified elements

- **Exact structure of the distributions**: class bounds, raw counts vs
  percentages, cumulative or not, number of classes. Unknown. The scan
  `PREUVE_classeurs.txt` l. 45 mentions "rows 26 to 308" without giving their content.
  → `reference-data-engineer`.
- **`M15` excludes column `L` whereas `M14` includes it** (`PREUVE_classeurs.txt`
  l. 28-33). Since Excel ignores empty cells in `AVERAGE` anyway, this
  range narrowing is either cosmetic, or a **deliberate exclusion of a present
  value**. The two cases do not have the same meaning. → to be elucidated by reading `L15`.
- **German version of SIA 4010:2023**: not consulted (only the French version is in
  `/refs`). Expected yield low, since §4.4 delegates to the separate documents
  anyway — but not verified.
- **EN 16798-5-1:2017, EN ISO 52016-1:2017**: absent from `/refs`. Not relevant here (neither
  defines the SIA acceptance criterion), mentioned for the record.

---

## 8. What would change my mind

1. **Spezifikation_Test1.pdf does not use "Streubereich"** → verdict falls back to
   *undecidable*, with slight advantage to (b) via argument C1. **Immediate reversal.**
2. **A chart in the `Häufigkeitsklassen` zone plots only per-program curves**,
   with no computed series → strengthens C2 without being decisive; I would lower confidence from
   ~85 % to ~65 % and recommend referring to the sub-commission before any freezing.
3. **A workbook (Tests 6 or 7) tabulates a distribution band using `MIN`/`MAX`** →
   direct and contrary evidence; shift to (b).
4. **An entry in the SIA 4010 FAQ** settling the matter explicitly → higher authority than any
   inference above, regardless of direction.

None of the above calls into question §5.5: the three-state output remains
correct under (a) as well as (b), and must be implemented in both cases.
