> **Note:** Translated from French original. See [anomalie-cas-900-iso-52016-1.spec.md](anomalie-cas-900-iso-52016-1.spec.md) for the source document.

# Anomaly — case 900, tables 28 and 29 of EN ISO 52016-1:2017

> Status: **ESTABLISHED**, reproducible evidence. High confidence.
> Established on 2026-08-03 by cross-checking three independent sources.
>
> **One-sentence conclusion**: the case 900 columns of tables 28 and 29
> of EN ISO 52016-1:2017 are **swapped in nature** — the table titled
> "heating" contains a cooling profile, and vice versa. The SIA
> evaluation workbook detected the error and corrected it without
> flagging it.

---

## 1. The facts

### 1.1 What the standard prints (page 131)

Read directly from `sia4010_evidence/ISO_52016_1_2017/page_131.png` in the
`IES-Intership-general-repo` repository, capture provided under licence whose
declared sha256 was recalculated and verified:
`C9B126485D50987C2E7F37F50B46C319E673612181119F228E42B5630CE5DA7E`.

**Table 28 — "Test results sensible energy needs for heating", case 900:**

```
mois   1    2    3    4    5    6    7    8    9   10   11   12   annuel
      84   53  121  147  175  308  638  656  626  418   84   48    3360
```

**Table 29 — "… for cooling", case 900:**

```
mois   1    2    3    4    5    6    7    8    9   10   11   12   annuel
      16   14   13    5    2    0    0    0    2    6    5   13      76
```

### 1.2 What the profiles tell us

| Series | Month of maximum | Season | Total |
|---|---|---|---|
| ISO tab. 28, labelled "heating" | **August** | summer | 3358 |
| ISO tab. 29, labelled "cooling" | **January** | winter | 76 |

A **heating** demand that peaks in **August** and collapses in December is
physically impossible under Denver's DRYCOLD climate. The two columns
carry the shape of the other quantity.

### 1.3 What the SIA workbook contains

`SIA_4010_geteilter_Link/Test1/Resultaterfassung_Test1.xlsx`, sheet
`Daten EN ISO 52016-1 2017`, column D (case 900):

| Quantity | Monthly values | Total |
|---|---|---|
| cooling 900 | 84, 53, 121, 147, 175, 308, 638, 656, 626, 418, 84, 48 | 3358 |
| heating 900 | 455.85 · 433.15 · 191.61 · 108.90 · 12.91 · 14.60 · 0 · 0 · 1.34 · 48.15 · 184.33 · 372.12 | 1823 |

**The SIA "cooling 900" column is IDENTICAL, month by month, to the
"heating" column of ISO table 28.** Verified: 12 out of 12 values, zero deviation.

The SIA therefore took the mislabelled ISO column and placed it where it
physically belongs.

Its **heating** 900 column, in turn, does not come from the printed standard: it
is in full precision whereas cases 600, 640 and 940 are integers copied over,
and the sheet declares in L44-L45:
`Quelle: EPBD Excel | Nov 2019`.

---

## 2. The decisive check: the four other programmes

The four reference programmes of Test 1 bracket the expected value.

**Annual heating, case 900 (kWh)**

| Programme | Value |
|---|---|
| IDA-ICE 5.0 beta 23 | 1264 |
| EXCEL SIA 380/2 | 2672 |
| EnergyPlus / OpenStudio 9.1.0 | 1229 |
| EDSL-Tas 9.5.2 | 1803 |
| **range of the four** | **1229 – 2672** |
| ISO column from SIA workbook | **1823 — within range** |
| ISO as printed | **3360 — out of range** |

**Annual cooling, case 900 (kWh)**

| Programme | Value |
|---|---|
| IDA-ICE | 3177 |
| EXCEL SIA 380/2 | 4653 |
| EnergyPlus / OpenStudio | 2515 |
| EDSL-Tas | 2326 |
| **range of the four** | **2326 – 4653** |
| ISO column from SIA workbook | **3358 — within range** |
| ISO as printed | **76 — out of range, by a factor of 30** |

The SIA workbook values fall at the heart of the four-programme cloud; the
printed ISO values fall outside it on both sides.

---

## 3. Why the other cases are not affected

For 600, 640 and 940, the printed standard and the SIA workbook agree to within
+/-2, which corresponds to the rounding between the sum of monthly values and the
printed annual total:

| Case | ISO as printed | SIA workbook |
|---|---|---|
| 600 heating | 5133 | 5134 |
| 640 heating | 3112 | 3110 |
| 940 heating | 1303 | 1301 |
| 600 cooling | 7503 | 7504 |
| 640 cooling | 7057 | 7058 |
| 940 cooling | 3261 | 3260 |

**Only case 900 diverges, and across all twelve months of both tables.** This
rules out a transcription error on our side: a reading error would affect
isolated cells, not exactly one column out of four, in two tables.

Tables 30 (operative temperature) and 32 (free-floating extremes) are
**unaffected**: 600FF max 63.5 / min -16.9 / avg 25.9 and 900FF 44.4 / -2.4 / 26.0
match exactly between the standard and the workbook.

---

## 4. Practical consequences

**For the engine**: the ground truth remains `test-1.ref.json`, i.e. the SIA
workbook. It is the one that SIA 4010 designates as the evaluation file
(SS4.4), and it is the only one of the two that is consistent with the four
programmes. **Never "correct" our data towards the printed ISO values.**

**For the Codex configuration**:
`config/iso52016_test1_verification_cases.json` faithfully transcribes the
printed standard, case 900 included. This is correct as a record of the
standard, but this file must not be used as a comparison reference for case 900.
It already carries `comparison_policy.mode = "REFERENCE_ONLY"`, which limits the
risk; an explicit note about case 900 would nonetheless be prudent.

**For the SIA sub-commission**: this is a fourth question to raise, and the
best-evidenced of the four. It does not require an interpretation ruling but the
confirmation of a fact: did the workbook knowingly correct an erratum of the
standard, and is this erratum known?

The three other questions remain: definition of the Streubereich for frequency
distributions, set of contributing variants, and number of out-of-band classes
triggering failure.

---

## 5. Reproduction

1. Recalculate the sha256 of `page_131.png` and compare it against the one
   declared in `config/iso52016_chapter7_confirmed_inputs.json` -> `evidence_sha256`.
2. Read tables 28 and 29 from the image.
3. Extract the `iso_52016_1_2017_reference` columns for case 900 from
   `refs/reference-data/test-1.ref.json`.
4. Observe the month-by-month identity between ISO table 28 and the SIA
   cooling column, and the divergence across all twelve months of heating.
5. Place both candidates within the range of the four other programmes.

## 6. What remains unverified

- The existence of a **published erratum** by ISO on this point: not investigated.
- The **exact provenance** of the "EPBD Excel, Nov 2019" from which the SIA draws
  its heating 900 column: this file is not in our possession.
- The **hourly profiles** of tables 33 and 34 for case 900: not checked;
  they only cover 600/640/900/940 for loads and 600FF/900FF for
  temperatures.

_Established on 2026-08-03. Three independent sources: the printed standard
(capture under licence, fingerprint verified), the SIA evaluation workbook, and
the four reference programmes._
