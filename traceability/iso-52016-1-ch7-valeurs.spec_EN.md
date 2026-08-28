> **Note:** Translated from French original. See [iso-52016-1-ch7-valeurs.spec.md](iso-52016-1-ch7-valeurs.spec.md) for the source document.

# Spec — input model for SIA 4010 Test No. 1, per EN ISO 52016-1:2017 SS7.2

> Status: **SPEC FROZEN** on the values below.
> Source: **BS EN ISO 52016-1:2017**, clause **7 "Quality control"**, SS7.2
> "Hourly method: verification cases", pages 122 to 134.
> Read on 2026-07-31 from the copy consulted by the client (BSI institutional
> access). Pages captured and re-read: 122 to 134 in full.
>
> This document resolves **three of the `[REQUIS]` items** that `traceability/test-1.spec.md`
> SS10 had left open since the start of the project: construction values,
> glazing values, infiltration value.

---

## 1. What this chapter is, and why it is authoritative here

`SS7.2.2.1`, NOTE: "*The verification cases are based on the BESTEST 600 and 900
cases as described in ANSI/ASHRAE 140*".

The SIA specification for Test 1 formally refers to "ISO EN 52016:2017
Kapitel 7" for the Verglasung, the Lüftung, the Wärmeeinträge and the
Testresultate. This chapter 7 **reproduces** the values instead of merely
referring to ASHRAE 140 — that was the open question, and it is now settled.

Version point noted: the copy cites **ASHRAE 140 of 2014** in its
normative references. The ASHRAE 140:**2023** values (`refs/`) are therefore
**not** the Test 1 target: they incorporate later revisions; its
Table 7-11 itself notes "*Updates to Standard 140-2017 are highlighted in
bold*".

---

## 2. Geometry — `SS7.2.2.2`, figure 2, table 22

Single zone, **8.0 x 6.0 x 2.7 m**, volume **129.6 m3**.
Two windows of **3.0 x 2.0 m** on the facade, sill **0.2 m**, lintel **0.5 m**,
side reveals 0.5 m and centre-to-centre 1.0 m.

| Component | Area [m2] |
|---|---|
| Wall (windowed facade) | 9.6 |
| Wall (left) | 16.2 |
| Wall (right) | 16.2 |
| Wall (rear) | 21.6 |
| Window | 12.0 |
| Floor | 48.0 |
| Ceiling | 48.0 |

"*Unless otherwise stated, all constructions are external (outdoor).*"

---

## 3. Opaque constructions — `SS7.2.2.3`, tables 23 and 24

Layer order: **interior -> exterior**.

### 3.1 LIGHTWEIGHT case (table 23)

| Element | Layer | D [m] | lambda [W/(m-K)] | R [m2K/W] | kappa [J/(m2K)] | rho [kg/m3] | c [J/(kg-K)] |
|---|---|---|---|---|---|---|---|
| Ext. wall | Plasterboard | 0.012 | 0.160 | 0.075 | 9576 | 950 | 840 |
| | Fiberglass quilt | 0.066 | 0.040 | 1.650 | 665 | 12 | 840 |
| | Wood siding | 0.009 | 0.140 | 0.064 | 4293 | 530 | 900 |
| | **total surf-surf** | | | **1.789** | | | |
| Floor | Timber flooring | 0.025 | 0.140 | 0.179 | 19500 | 650 | 1200 |
| | Insulation ^a | 1.003 | 0.040 | 25.075 | 0 ^b | 0 ^b | 0 ^b |
| | **total surf-surf** | | | **25.254** | | | |
| Roof | Plasterboard | 0.010 | 0.160 | 0.063 | 7980 | 950 | 840 |
| | Fiberglass quilt | 0.1118 | 0.040 | 2.794 | 1127 | 12 | 840 |
| | Roofdeck | 0.019 | 0.140 | 0.136 | 9063 | 530 | 900 |
| | **total surf-surf** | | | **2.992** | | | |

ISO 52016-1 classes: wall "Very light / Evenly (D)", floor "Very light /
Internal (I)", roof "Very light / Evenly (D)".

### 3.2 HEAVYWEIGHT case (table 24)

| Element | Layer | D [m] | lambda | R | kappa | rho | c |
|---|---|---|---|---|---|---|---|
| Ext. wall | Concrete block | 0.100 | 0.510 | 0.196 | 140000 | 1400 | 1000 |
| | Foam insulation | 0.0615 | 0.040 | 1.537 | 861 | 10 | 1400 |
| | Wood siding | 0.009 | 0.140 | 0.064 | 4293 | 530 | 900 |
| | **total surf-surf** | | | **1.797** | | | |
| Floor | Concrete slab | 0.080 | 1.130 | 0.071 | 112000 | 1400 | 1000 |
| | Insulation ^a | 1.007 | 0.040 | 25.175 | 0 ^b | 0 ^b | 0 ^b |
| | **total surf-surf** | | | **25.246** | | | |
| Roof | *identical to lightweight case* | | | **2.992** | | | |

Classes: wall "Heavy / Internal (I)", floor "Medium / Internal (I)",
roof "Very light / Evenly (D)". Note ^c: "*For the heavyweight case wall and
floor properties are more massive and the roof properties are unchanged.*"

^a **Floor deliberately over-insulated** to thermally decouple from the ground:
"*the thermal resistance of the floor can be used in the calculations instead of
the effective thermal resistance (R_c;f;eff), with the outdoor air as external
environment*". The resistance of the thick layer is imposed on the
**first conductance (outermost)**, so that the thermal mass of the
actual floor is preserved; `h_1 = 0.04 W/(m2-K)`.

^b Floor insulation: rho, c and kappa **set to zero** for the purpose of this document.

---

## 4. Glazing — `SS7.2.2.6` — THIS CLOSES THE U-VALUE QUESTION

```
g_gl;n = 0,789
F_w    = 0,9   (facteur de correction, vitrage non diffusant)  →  g_gl = 0,71
U_W    = 2,984 W/(m²·K)
R_se;v = 0,04  m²K/W      (cf. tableau 25)
R_si;v = 0,13  m²K/W      (cf. tableau 25)
F_fr   = 0                (aucune fraction de cadre)
```

The text is explicit: "*For the application of this document the following
input data are **adapted***". **U_W = 2.984 is a normative input datum**,
not a value to be recalculated — hence the legitimacy of imposing it.

NOTE from the standard: "*In ANSI/ASHRAE 140 a value is given for double pane shading
reduction factor (0.907). Therefore the U_w value is adapted to obtain the same
R_c value for the window.*" And further: "*The values for R_se;v and R_si;v in
this document are different from the values in ANSI/ASHRAE 140 ... Therefore the
U_w value is adapted to obtain the same R_c value for the window.*"

### 4.1 Why three values were circulating — resolved

**One glazing, three surface resistance conventions.** The hypothesis
"convention rather than different glass" is confirmed by the standard itself.

| Convention | U [W/(m2-K)] | R total | R core |
|---|---|---|---|
| **ISO 52016-1:2017 (normative here)** | **2.984** | 0.33512 | **0.16512** |
| BESTEST 1995 / current config | 3.0 | 0.33333 | 0.16333 |
| ASHRAE 140:2023 (combined coefficients 17.8 / 4.5) | 2.10 | 0.47650 | — |
| what VE currently calculates | 2.917 | 0.34282 | 0.17282 |

The VE deviation amounts to **+0.0077 m2K/W on the core**. It matches the defect noted
in `AUDIT-swiss-sia-existant.md`: the two glass layers of
`reference_model_assets.json` carry `"properties": {}`, **with no declared
thickness**, so VE applies a default.

`WARNING NOT GIVEN BY ISO`: glass pane thickness, glass lambda, gap thickness. The
standard imposes `U_W`, `g`, `R_se;v`, `R_si;v` and `F_fr`; the layer composition
is free **provided that U_W = 2.984 is achieved** under these surface resistances.
The 3.175 mm and 6.297 gap from the config come from BESTEST 1995, a source
absent from `/refs` — to keep as a means, not as a normative value.

---

## 5. Surface exchange coefficients — `SS7.2.2.10`, table 25

ISO 13789 values, in W/(m2-K):

| Coefficient | Symbol | Upward | Horizontal | Downward |
|---|---|---|---|---|
| convective, interior surface | h_ci | 5.0 | 2.5 | 0.7 |
| convective, exterior surface | h_ce | 20 | 20 | 20 |
| radiative, interior surface | h_lr;i | 5.13 | 5.13 | 5.13 |
| radiative, exterior surface | h_lr;e | 4.14 | 4.14 | 4.14 |

This is **the answer to item SS8 pt 6 of `test-1.spec.md`** (external surface
coefficient), for the ISO path. Not to be confused with the combined coefficients
of ASHRAE 140:2023 (17.8 / 4.5), which follow a different convention.

---

## 6. Other model parameters

| Quantity | Value | Clause |
|---|---|---|
| Internal capacity, lightweight case | C_m = **3.84 MJ/K** (class "very light", 80 000-A_use) | SS7.2.2.4 |
| Internal capacity, heavyweight case | C_m = **12.48 MJ/K** (class "heavy", 260 000-A_use) | SS7.2.2.4 |
| Air + furniture capacity | kappa_m;int = **10 000 J/(m2-K)** | SS7.2.2.5 |
| Solar absorptance, opaques | alpha_sol = **0.6** | SS7.2.2.7 |
| Sky view factor | F_sky = **1.0** roof / **0.5** walls | SS7.2.2.8 |
| Convective fractions | f_int;c = **0.40**; f_sol;c = **0.10**; f_H;c = f_C;c = **1.00** | SS7.2.2.9 |
| Internal gains | **200 W continuous**, 24 h/day year-round -> q_int = **1.453 W/m2** | SS7.2.2.13 |
| Infiltration | **0.41 h^-1 continuous**, q_v = 0.0148 m3/s = **1.107 m3/(m2-h)**. **No ventilation system.** Independent of wind and temperature difference. Factor **0.822** applied for the 1609 m altitude. | SS7.2.2.14 |
| Available capacities | Phi_H;avail = Phi_C;avail = **1000 kW** (effectively infinite) | SS7.2.2.16 |
| Sky offset | Delta_theta_sky;r = **11 K** constant, all time steps | SS7.2.2.12 |
| Ground temperature | **equal to outdoor air temperature** (theta_gr;vi;m replaced by theta_e) | SS7.2.2.12 |
| Utilisation factors (monthly method) | a_H;0 = a_C;0 = 1.0; tau_H;0 = tau_C;0 = 15 h | SS7.2.2.11 |

### 6.1 Thermostat setpoints — `SS7.2.2.15`

**Continuous**: theta_int;set;H = **20 °C**, theta_int;set;C = **27 °C**.

**Intermittent**: from 07:00 to 23:00 -> 20 / 27 °C; from 23:00 to 07:00 ->
**10** / 27 °C. "*(no night time set back for cooling)*".

### 6.2 Climate — `SS7.2.2.12`

Data converted **per ISO 52010-1**. Hourly values (temperature,
direct and diffuse radiation by orientation, solar height and azimuth) are
in the workbook published at `http://standards.iso.org/iso/52016/-1/ed-1`.
Monthly values in table 26.

> This **confirms** the caveat recorded in the project config: the ISO
> workbook carries radiation already projected by orientation, converted per
> ISO 52010-1, whereas our EPW **reconstructs** the diffuse from the TMY1. The
> two series are not the same thing; per-orientation checking becomes possible
> (column `S` against the south-facing window of case 600).

---

## 7. Test cases — table 27, `SS7.2.3`

**This is the "table 27" that SIA 4010 cites in Annex A, tab. 64.** It is not
a table of values: it is the definition of the Test 1 scope.

| Test | BESTEST | Construction | Thermostat |
|---|---|---|---|
| 1 | 600 | Lightweight | Continuous |
| 2 | 640 | Lightweight | Intermittent |
| 3 | 900 | Heavyweight | Continuous |
| 4 | 940 | Heavyweight | Intermittent |
| 5 | 600FF | Lightweight | Free floating |
| 6 | 900FF | Heavyweight | Free floating |

Case **1E** in the SIA workbook does not belong to this list: it is a SIA
addition, and the only case with a pass/fail criterion (cf. `test-1.spec.md` SS6).

## 8. Reference results — tables 28 to 34, `SS7.2.4`

Quantities to calculate and report: monthly and annual heating demand
`Q_H;nd` and cooling demand `Q_C;nd`; for the hourly method, additionally: monthly
average operative temperature `theta_op;av`, hourly demands and operative
temperatures for **4 January** and **27 July**.

**These tables ARE the `Daten EN ISO 52016-1 2017` column of the SIA workbook.**
Verified by direct cross-check: table 32 gives 600FF **Max 63.5 / Min -16.9 /
Average 25.9** and 900FF **44.4 / -2.4 / 26.0** — identical to
`refs/reference-data/test-1.ref.json`. Table 30, case 600 month 1 = **22.0**,
also identical.

Table correspondence:

| ISO 52016-1 | Content | SIA workbook table |
|---|---|---|
| 28 | heating demand | 28 |
| 29 | cooling demand | 29 |
| 30 | average operative temperature | 30 |
| 31 | annual peak hourly loads | 31 |
| 32 | annual operative temperature extremes | 32 |
| 33 | hourly loads for 4 January | 33 |
| 34 | hourly operative temperatures for 4 January | 34 |

The SIA workbook numbering **mirrors that of ISO 52016-1**. That is why
`test-1.ref.json` carries "Table 28/29/30/31/32" labels: they are the ISO tables.

---

## 9. Explicit limitations — `SS7.2.1`

These cases **do not include**:

- ground-coupled floor heat transfer (covered by ISO/TR 52016-2);
- thermal coupling between two or more zones;
- the effect of thermal bridges;
- conservatories and other unconditioned spaces;
- solar shading by external obstructions (nearby or distant);
- complex control schemes (weekend interruption, free-cooling night
  ventilation, heat recovery bypass, etc.);
- **latent** loads — "*the equation is straightforward and can be easily
  checked analytically*".

Useful to avoid attempting to validate what the standard does not test.

---

## 10. What remains unverified

- **Annex E** (normative), *Heat transfer and solar heat gains of windows and
  special elements*, pages 176-183: not captured. It would clarify window
  treatment, but the blocking point is resolved without it.
- `SS6.5.9 Temperature of adjacent thermally unconditioned zone` (p. 78-80): not
  captured. It pertains to the open item of **Test 6** (basement temperature),
  not Test 1.
- **Glass pane thickness and lambda**: not given by ISO (cf. SS4 above).
- **Visible light transmittance**: not given by ISO. The 0.86156 value from the
  config remains an `IMPLEMENTATION_PROXY`, with no effect on Test 1 outputs.
- **NREL/TP-472-6231** (BESTEST 1995) and **ASHRAE 140-2014** remain absent from
  `/refs`. They are no longer blocking for Test 1, as ISO 52016-1 SS7.2 is
  self-sufficient.

_Established on 2026-07-31 after direct reading of pages 122 to 134._
