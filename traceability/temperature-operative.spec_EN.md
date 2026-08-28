> **Note:** Translated from French original. See [temperature-operative.spec.md](temperature-operative.spec.md) for the source document.

# Spec — "Operative Temperature" Variable for Tables 30 / 32 (SIA 4010 Test No. 1)

> Status: **DECIDED CONDITIONALLY** (one blocking verification named in §8).
> Author: `norm-analyst`. Date: 2026-07-31.
> Convention: `VÉRIFIÉ` = read verbatim at the cited location / `INFÉRÉ` = explicit
> deduction, marked / `NON VÉRIFIÉ` = source absent or unreadable in this environment.

---

## 1. The Question

Among the six competing temperature definitions exposed at zone level by the
IESVE `.aps` file, **which one is the "operative Temperatur" variable required by the
SIA 4010 Test 1 specification for Table 30 (monthly averages) and Table 32
(max / min / annual average for cases 600FF and 900FF)?**

---

## 2. Verdict

### 2.1 On the Normative Variable — **DECIDED**, confidence **HIGH**

The variable for Tables 30, 32 (and 34) is **OPERATIVE temperature**, and **not**
air temperature. The SIA specification states this literally, and it **explicitly
distinguishes** the two on the same page: it requires both hourly series to be
delivered, then constructs tables 30/32/34 only from the **operative** one.

→ **Excluded**: `Air temperature` (#6), `Mean radiant temperature` (#5).
→ **Excluded**: `Environmental temperature` (#4) — see §5.3 (INFÉRÉ).

### 2.2 On the IESVE Variable — **DECIDED CONDITIONALLY**, confidence **MEDIUM-HIGH**

**Variable to bind, Table 30 AND Table 32 (and Table 34):**

| Field | Exact value |
|---|---|
| `aps_varname` | **`Comfort temperature`** |
| `display_name` (VistaPro) | **`Dry resultant temperature`** |
| `model_level` | **`z`** (zone) |
| `metric_unit` | **`°C`** |
| `metric_divisor` / `metric_offset` | **1.0 / 0.0** |

A single variable for both tables: Table 30 and Table 32 are two
different aggregations of **the same hourly series** (Test 1 spec, items 3 and 7 —
§4.1). The aggregation differs: see §6.

**Blocking condition**: the α = 0.5 check from §8.1 must pass. Until it has been
run on a real `.aps`, the binding remains **provisional**.

---

## 3. Evidence — What the SIA Specification Says (VÉRIFIÉ)

Source: `SIA_4010_geteilter_Link\Test1\Spezifikation_Test1.pdf`, text extraction reviewed
at `…\scratchpad\norme\spec_test1.txt` (123 lines, read in full).
*(umlauts are restored; the extraction renders them as `?`)*

| Line | Verbatim quote | Scope |
|---|---|---|
| 72-73 | « Jahresdatensätze, zu übertragen in die Auswertungsdatei **Resultaterfassung_Test1.xlsx**, für » | deliverables header |
| **76** | « 2) Alle Fälle ausser 1E: **Stündliche Raumluft- und operative Temperatur** » | **both hourly series are delivered, hence distinct** |
| **82** | « 3) **monatliche Mittelwerte der operativen Temperatur** » | **→ Table 30** |
| **90-91** | « 7) **stündliche max., min. und mittlere operative Temperatur pro Jahr**, 600FF, 900FF » | **→ Table 32** |
| 92-93 | « 8) stündliche Mittelwerte der operativen Temperatur, 4. Januar, 600FF, 900FF » | → Table 34 |

**Direct consequence**: the spec also requires air temperature, but **none** of the
derived outputs 3/7/8 are built from it. Binding `Air temperature` to Tables 30/32
would contradict the text. This is the decisive point, and it depends on no interpretation.

**What the spec does NOT say**: it does **not define** operative temperature (no
formula, no weighting, no article reference). This is the true origin of
the ambiguity. See §7.

---

## 4. Evidence — ASHRAE 140:2023 (VÉRIFIÉ): The Upstream Source Says the Opposite, and This Matters

Source: `ASHRAE 140_2023_D_86892.pdf`, text extraction
`C:\Users\ulysse.couliou\.claude\jobs\d1486f24\tmp\ashrae140.txt` (27,379 lines).

### 4.1 ASHRAE 140 Requires AIR Temperature for Free-Floating Cases

- **Definition, l. 1080-1081**: « *hourly free-floating zone air temperature: zone air
  temperature for a given hour during which heating and cooling equipment is OFF or for
  an unconditioned zone.* »
- **§7.3.6.1 to 7.3.6.3, l. 5966-5970**: « *Annual mean **zone air temperature** (°C)* » /
  « *Annual hourly integrated minimum **zone air temperature** (°C)…* » /
  « *Annual hourly integrated maximum **zone air temperature** (°C)…* »
- **Informative note, l. 5972-5975 (identical l. 4829-4835)**: « *the free-float zone air
  temperature is for the **zone air only, assuming well-mixed air with no radiant
  effects** (i.e., equivalent to what would be obtained from an aspirated temperature
  sensor perfectly shielded from solar and infrared radiation).* »
- **Table 7-47, l. 6001-6002**: hourly output for Feb 1 for 600FF/900FF =
  « *Hourly integrated free-float **zone air temperature** (°C)* ».

### 4.2 The Word "Operative" Does Not Exist in ASHRAE 140:2023

Exhaustive searches across all 27,379 lines: `operative` → **0 occurrences**;
`operative temperature` → **0**; `mean radiant` → **0**; `radiant temperature` → **0**.
(`radiant` only appears for IR emittance, solar absorptance, the "Radiant Time
Series" and the "no radiant effects" notes.)

### 4.3 Normative Consequence — Not to Be Missed

**SIA 4010 Test 1 DELIBERATELY DEVIATES from ASHRAE 140 on this output.** ASHRAE requires
air; SIA requires operative (and collects air additionally). **ASHRAE 140 therefore CANNOT
be invoked to justify binding `Air temperature` to Tables 30/32** — that is
precisely the "false but plausible" error the question sought to avoid.

### 4.4 Adjacent Point Resolved in Passing: The CONTROL Temperature IS Air

- **§7.2.1.13 a/b, l. 3395-3396**: « *a. 100% convective air system. b. **The thermostat
  senses only the air temperature.*** »
- **Informative note §7.2.1.13.1.1, l. 3410**: « *"Temperature" refers to conditioned-zone
  air temperature.* »

There is therefore **no contradiction**: we **control on air** (20 / 27 °C) and we
**report operative**. The IESVE model probed (§5.2) does exactly this — that is a
conformance indicator, not a proof.

---

## 5. Evidence — Reference Programs and IESVE Side

### 5.1 Anwenderberichte: No Evidence of Usage (VÉRIFIÉ, negative result)

All **4** Test 1 reports were read in full:
`…\scratchpad\norme\anwender_test1_1.txt` (EXCEL SN EN ISO 52016-1, 31 l.),
`…_2.txt` (EnergyPlus 9.1.0/OpenStudio, 25 l.), `…_3.txt` (TAS EDSL, 18 l.),
`…_4.txt` (IDA ICE 5.0 Beta 23, 21 l.).

- **`operativ` → 0 occurrences across all 4 files.**
- None of them names the exported output variable or its definition.
- The only related statement: EnergyPlus report l. 18-19, « *Auch sind die **Free-Float
  Temperaturen** beim Case 600FF und 900FF bei den höheren Werten im Programmvergleich* »
  — without definition.

→ **The hypothesis "a reference program states which variable it exported" is
false.** This avenue is closed.

### 5.2 IESVE Runtime Probe on a Case 600 (VÉRIFIÉ, real data)

Source: `C:\Users\ulysse.couliou\Documents\IES Internship\IES-Intership-general-repo\references\iesve\probes\sia4010_aps_temperature_binding_evidence.json`
(zone `SIA4010_TEST_1_600_ZONE`, 48 m², 8760 timesteps, l. 18-68).

| Variable | `aps_varname` | min | max | sum | **annual average** |
|---|---|---|---|---|---|
| `Air temperature` | `Room air temperature` | 19.999998 | 27.000002 | 202 936.11790 | **23.1662 °C** |
| `Dry resultant temperature` | `Comfort temperature` | 18.137789 | 32.525875 | 207 347.09587 | **23.6698 °C** |

Two immediate readings:
1. Air is **clipped exactly** at 20.000 / 27.000 → control on air, consistent with
   ASHRAE 140 §7.2.1.13 b (§4.4).
2. Dry resultant **floats** (18.14 … 32.53) → it is not the controlled variable; it
   therefore does contain a radiant component.

### 5.3 Numerical Discriminant Against Table 30 Reference Values (INFÉRÉ, strong)

Reference values, **Table 30, case 600, annual row (row 70)** —
`refs\reference-data\test-1.ref.json` l. 5199-5223:

| Program | annual [°C] | cell |
|---|---|---|
| Daten Norm EN ISO 52016-1 | 23.3083 | C70 |
| IDA ICE 5.0 β23 | 23.9159 | D70 |
| EXCEL SIA 380/2 | 23.2630 | E70 |
| EnergyPlus 9.1.0 | 23.6425 | F70 |
| EDSL-Tas 9.5.2 | 23.9188 | G70 |
| — band — | **[23.2630 ; 23.9188]** | |
| — mean of 5 — | **23.6097** | |

Comparison with the IESVE probe (§5.2):

| IESVE candidate | annual average | position |
|---|---|---|
| **`Dry resultant temperature`** | **23.6698** | **WITHIN the band**, at **+0.060 K** from the 5-program mean |
| `Air temperature` | 23.1662 | **OUTSIDE the band**, **−0.097 K below the minimum** |

→ Clear corroboration of the §2 verdict. **This is not a proof**: see the
counter-arguments in §7.

### 5.4 Pre-existing Binding in the Repository (context, not probative)

- `ve_adapter\test1_adapter.py` l. 835-843 already binds `operative_temperature` →
  `Comfort temperature` / `Dry resultant temperature`, but itself flags
  the inconsistency of its justification's version.
- `…\IES-Intership-general-repo\config\sia4010_aps_bindings_ve_runtime.json` l. 75-84:
  same binding, `"status": "RUNTIME_METADATA_CONFIRMED"`, semantic justification
  « *IES documents dry resultant temperature as operative temperature in still-air
  conditions* », `"source_reference": "https://help.iesve.com/ve2025/hot_water_radiator_control_.htm"`.
  → **VE2025 web source, absent from `/refs` (which is VE2023): NOT VERIFIED by me.**
  `AUDIT.md` l. 358-369 had already downgraded the status of this binding for this reason.
  The present document **does not validate it through this path**; it takes it up for other
  reasons (§3, §4, §5.3) and conditions it (§8.1).

---

## 6. Table 30 ≠ Table 32: They Are Not the Same Average (INFÉRÉ, strong — code impact)

Discovered by comparing the two tables from the same workbook:

| Program | Table 30, annual (600FF) | Table 32, "Average" (600FF) | gap |
|---|---|---|---|
| ISO 52016-1 | 25.875 (AI70) | 25.9 (C107) | +0.025 |
| IDA ICE | 27.21592 (AJ70) | 27.25330 (D107) | +0.0374 |
| EXCEL SIA 380/2 | 26.00222 (AK70) | 26.04944 (E107) | +0.0472 |
| EnergyPlus | 26.14802 (AL70) | 26.18676 (F107) | +0.0388 |
| EDSL-Tas | 25.21285 (AM70) | 25.25604 (G107) | +0.0431 |

Sources: `refs\reference-data\test-1.ref.json` l. 7031-7055;
`refs\reference-data\table_32_corrected.json` l. 86-119.

**Inference**:
- **Table 30, "annual" row = UNWEIGHTED average of the 12 monthly averages.**
  Exact reconstruction on the ISO column (published to 1 decimal):
  23.3083333…× 12 = **279.7** (case 600); 25.875 × 12 = **310.5** (600FF);
  25.9083333…× 12 = **310.9** (900FF). Three times an exact multiple of 0.1 → the cell
  is indeed an `AVERAGE` of 12 values at 1 decimal.
- **Table 32, "Average" = hour-weighted average (8760 values).**
  The gap is systematically **positive and on the order of 0.04 K**: the expected signature
  of reweighting 31-day months (July, August) against February (28 days).

**Code consequence — anomaly to fix**:
`ve_adapter\test1_adapter.py` l. 962 computes `moyenne_annuelle = sum(serie)/len(serie)`
(**hour-weighted**) and places it at l. 1006 in `monthly['annual']`, i.e. against
**Table 30**. But Table 30 expects the average of the 12 monthly values. Latent bias ≈ **0.04 K**,
invisible to the eye, systematic. Line 1016 (Table 32) is, on the other hand, correct.
→ **INFÉRÉ, to be confirmed by the Excel formula** (§8.2) before any correction.

---

## 7. Counter-Arguments to My Own Conclusion

1. **The SIA spec never defines "operative Temperatur".** Neither the Test 1 spec
   (`spec_test1.txt`, read in full), nor SIA 4010:2023 (full French text:
   `…\scratchpad\norme\sia_4010_2023.txt`, **0 occurrences of "température"**), nor the
   Anwenderberichte. The §2.2 verdict therefore relies on an **external** definition that I
   was unable to read (§8.1). This is the main weakness.
2. **Each reference program may have used ITS OWN definition of operative temperature.**
   Nothing in the corpus rules this out. The Table 30 band could then mix
   multiple weightings. Fitting within this band therefore does not prove identity of
   definition.
3. **The numerical discriminant §5.3 is weak in margin.** Gap Ta↔Tdr = 0.50 K against
   an inter-program band width of 0.66 K. A poorly constructed IESVE model
   could shift both candidates and reverse the conclusion.
4. **The probe §5.2 is based on an unqualified `.aps`.** Project `"test"`, file
   `"test.aps"`; nothing proves the geometry/constructions follow the spec
   (reservation already recorded in `AUDIT.md` l. 361-363, and §8 pt 2-4 of
   `traceability\test-1.spec.md`: constructions, glazing, infiltration still `[REQUIS]`).
5. **`Dry resultant temperature` is not a physical constant: its weighting depends on
   a model setting** (template air speed). A silent change to this
   setting changes the value without changing the variable name. Hence the safeguard §8.1,
   which is not optional.
6. **Serious opposing argument in favour of air**: the test cell comes
   from ASHRAE 140, which explicitly requires air and prohibits radiant effects (§4.1).
   If it were demonstrated that the SIA workbook actually feeds Tables 30/32 from the
   "Raumlufttemperatur" column, the "operativ" label would be a misnomer and
   the verdict would reverse. **This check is named in §8.2; it has not been done.**

---

## 8. What Remains NOT VERIFIED — and How to Resolve It

### 8.1 BLOCKING — weighting definition, and associated empirical check

**Missing source no. 1: `refs\SIA-380-2-2022.pdf`.** The PDF is present but
**unreadable in this session**: page rendering fails (`pdftoppm` absent) and text
streams are compressed (`Grep` → 0 occurrences). This is the parent standard (SIA 4010 is its
"Wegleitung"): that is where the definition of θ_op / operative
temperature must be found. **Action: `pdftotext` extraction by the orchestrator, then re-reading.**

**Missing source no. 2: EN ISO 52016-1:2017** — completely absent from `/refs`, although
it is the source formally cited by the Test 1 spec for the test cell.

**Missing source no. 3: IESVE documentation for the 6 variables.** `refs\VEScripts-API-VE2023.pdf`
(reviewed extract: `…\jobs\d1486f24\tmp\vescripts_api.txt`) contains **no** occurrences
of `operative`, `dry resultant`, `environmental temp`, `mean radiant`, `comfort temp`.
The exact formulas for the 6 variables **cannot be verified in `/refs`.**

**Empirical check that replaces these sources in the meantime** — it assumes no
formula: on a `.aps` from case 600FF, extract the 6 hourly series (8760 values) and,
for each candidate `C`, solve for α in `C(h) = α·Ta(h) + (1−α)·Tmr(h)` (least
squares on the 8760 points, plus max residual).

| α measured | Reading |
|---|---|
| **α = 0.500 ± 0.001, max residual < 0.01 K** | the candidate is the arithmetic mean of air/radiant → **this is the one to bind** |
| α ≠ 0.5 but low residual | non-50/50 weighting → **escalate**, do not bind before reading SIA 380/2 |
| high residual | the candidate is not a linear combination of Ta and Tmr → **exclude** |

Expectation (INFÉRÉ, to be confirmed): `Dry resultant temperature`,
`Operative temperature (ASHRAE)` and `Operative temperature (TM 52/CIBSE)` should
**all three yield α = 0.5 in still air** and then be numerically interchangeable;
`Environmental temperature` should yield α ≈ 1/3 (CIBSE admittance method, not an
operative temperature). **These expected values are NOT sourced**: they are
the object of the test, not its hypothesis.

**Permanent safeguard to implement in `ve_adapter/`** (not just once): at each
extraction, verify `|Tdr(h) − 0.5·(Ta(h)+Tmr(h))| ≤ 0.01 K` across all 8760 hours and
**refuse to write the candidate JSON** if the check fails, with an explicit message.
Reason: a change in air speed in the template would otherwise produce a false
and perfectly plausible result.

### 8.2 BLOCKING for traceability — read the SIA workbook itself

`SIA_4010_geteilter_Link\Test1\Resultaterfassung_Test1.xlsx` is **present** but I
cannot open a `.xlsx`. To be extracted (openpyxl, `data_only=False`), sheet
"Zusammenfassung Testfälle":

1. **Exact German labels** of rows 53 (Table 30) and 104 (Table 32) → do they say
   "operative Temperatur" or "Raumlufttemperatur"? *(resolves counter-argument §7.6)*
2. **Formulas** of `C70`, `AI70`, `AQ70` (annual Table 30) and `C107`, `K107` (Average
   Table 32) → confirm or refute the inference in §6.
3. **Columns AZ-BG** flagged as "ASHRAE 140 data" by
   `refs\reference-data\test-1.ref.md` l. 205/211: what header, what values? If the
   workbook juxtaposes ASHRAE 140 air temperatures and its own "operativ" columns,
   their gap directly quantifies the deviation in §4.3.
4. On the per-program input sheets: are the hourly input columns
   "Raumlufttemperatur" and "operative Temperatur" two **distinct** columns with
   **different** values? If they are identical for a given program, that program
   delivered the same series twice → to be documented.

### 8.3 Non-blocking, to be recorded

- The α check has **never** been run: the repository's current binding (§5.4) relies
  on an unversioned VE2025 help page. Not to be confused with a verification.
- The available `.aps` probe covers only **2** of the 6 variables (air + dry resultant) and
  a case **600**, not **600FF**. A new probe covering all 6 variables on 600FF is
  needed for §8.1.

---

## 9. Summary of the Binding to Implement

```
Table 30 (monthly averages, cases 600/640/900/940/600FF/900FF)
Table 32 (annual max/min/average, cases 600FF/900FF)
Table 34 (hourly profile of January 4, 600FF/900FF)
    ← a single zone hourly series, 8760 values:
        aps_varname   = "Comfort temperature"
        display_name  = "Dry resultant temperature"
        model_level   = "z"
        unité         = "°C"   (divisor 1.0, offset 0.0)
    ← subject to the α = 0.5 check (§8.1), otherwise ESCALATE.

Agrégations (INFÉRÉ §6, à confirmer §8.2) :
    Table 30 mensuel  = moyenne des heures du mois
    Table 30 annuel   = moyenne NON pondérée des 12 moyennes mensuelles   ← ≠ code actuel
    Table 32 max/min  = max/min des 8760 valeurs horaires
    Table 32 average  = moyenne des 8760 valeurs horaires                 ← code actuel OK

À NE PAS lier : "Air temperature", "Mean radiant temperature",
                "Environmental temperature".
Acceptables SEULEMENT si α = 0.5 mesuré, et alors équivalentes :
                "Operative temperature (ASHRAE)", "Operative temperature (TM 52/CIBSE)".
```

**No tolerance is associated with these tables**: cases 600/640/900/940/600FF/900FF
have **no deviation criterion** (`spec_test1.txt` l. 96-100, « *Es gibt dafür kein
Abweichungskriterium* »). The choice of variable is no less critical: it is the
published visual comparison that would be wrong.

---

## 10. Citations — Exact Locations

| Assertion | Location |
|---|---|
| SIA requires operative for Tables 30/32/34, distinct from air | `…\scratchpad\norme\spec_test1.txt` l. 76, 82, 90-93 (PDF: `SIA_4010_geteilter_Link\Test1\Spezifikation_Test1.pdf`) |
| No deviation criterion for 600…900FF | `spec_test1.txt` l. 96-100 |
| ASHRAE 140: FF output = zone air temperature | `…\jobs\d1486f24\tmp\ashrae140.txt` l. 1080-1081, 5966-5970, 5972-5975, 4829-4835, 6001-6004 |
| ASHRAE 140: thermostat on air | idem, l. 3395-3396, 3410 |
| ASHRAE 140: 0 occurrences of "operative" / "mean radiant" | exhaustive search across all 27,379 lines of the same file |
| Anwenderberichte: 0 occurrences of "operativ" | `…\scratchpad\norme\anwender_test1_1..4.txt` (read in full) |
| SIA 4010:2023 (fr): 0 occurrences of "température" | `…\scratchpad\norme\sia_4010_2023.txt` |
| IESVE probe case 600 (2 variables, 8760 timesteps) | `…\IES-Intership-general-repo\references\iesve\probes\sia4010_aps_temperature_binding_evidence.json` l. 18-68; semantic qualification l. 70-75 |
| Pre-existing binding + VE2025 justification | `…\IES-Intership-general-repo\config\sia4010_aps_bindings_ve_runtime.json` l. 75-84; `ve_adapter\test1_adapter.py` l. 835-843; `AUDIT.md` l. 358-369 |
| Table 30 case 600 annual (5 programs) | `refs\reference-data\test-1.ref.json` l. 5199-5223 |
| Table 30 cases 600FF/900FF annual | idem l. 7031-7055 and l. 7489-7513 |
| Table 32 cases 600FF/900FF | `refs\reference-data\table_32_corrected.json` l. 86-119 and l. 206-239 |
| ASHRAE 140 columns AZ-BG flagged in workbook | `refs\reference-data\test-1.ref.md` l. 205, 211 (**not verified by me**) |
| Annual aggregation in code | `ve_adapter\test1_adapter.py` l. 950-963 (l. 962), l. 1004-1018 |
| VEScripts API VE2023: none of the 6 variables documented | `…\jobs\d1486f24\tmp\vescripts_api.txt` (0 occurrences) |
| SIA 380/2:2022 unreadable in this session | `refs\SIA-380-2-2022.pdf` — rendering impossible (`pdftoppm` absent), Grep → 0 |
| EN ISO 52016-1:2017 | **absent from `/refs`** |

---

## 11. What Would Change My Mind

1. SIA 380/2:2022 (or EN ISO 52016-1:2017) defining θ_op with a weighting **≠
   50/50** → it would then be necessary to construct a derived variable from `Room air
   temperature` + `Room radiant temperature`, and **no** native IESVE variable would
   be suitable.
2. The workbook `Resultaterfassung_Test1.xlsx` showing that Tables 30/32 are
   fed from the air column → verdict reversed to `Air temperature`.
3. An α check (§8.1) yielding α ≠ 0.5 for `Dry resultant temperature` on the
   Test 1 model → the binding would fall in favour of the variable that gives α = 0.5, or an
   explicit derivation.
4. A SIA note (rectification `www.sia.ch/rectificatif`, or SIA 4010 FAQ) defining the
   variable → takes precedence over everything above.

---

## 12. Log

| Date | Author | Change |
|---|---|---|
| 2026-07-31 | norm-analyst | Creation. Verdict: operative confirmed (VÉRIFIÉ); binding `Comfort temperature` / `Dry resultant temperature` **conditional** on the α = 0.5 check. Ancillary findings: ASHRAE 140 requires air (SIA deviation acknowledged); Table 30 annual ≠ Table 32 average (0.04 K bias in current code). |
