> **Note:** Translated from French original. See [RESERVES_NORMATIVES.md](RESERVES_NORMATIVES.md) for the source document.

# Normative reserves — SIA 380/2 client compliance ("we proceed without, under reserve")

This register lists the points where a **licensed standard** is not in our
possession, **where to find it**, how the tool **operates without it**, and the
**explicit reserve** attached to the corresponding verdict.

> **Policy (project decision 2026-08-20).** No purchase of paid standards is
> committed. The tool remains **usable** without these documents: the relevant
> criterion is rendered **VALIDATED UNDER RESERVE** or `[À VÉRIFIER]` / `NOT_DETERMINED`,
> never a silent `PASS` (rule 2 of CLAUDE.md: "missing evidence never becomes
> PASS"). Upon receipt of the document, the reserve is lifted and the verdict confirmed.
> See also `docs/project/REGISTRE_DEMANDES_EXTERNES.md` (for SIA 4010 tests).

## Where to find the documents

| Document | Where to obtain it | Already in hand? |
|---|---|---|
| **SN EN 14825:2018** (SEER/SCoP) | SNV (snv.ch) / EN standards — standard access; SIA Shop relay | **Cooling: yes** (frozen, `sn-en-14825-2018.cooling-seer.json`). Heating (SCoP): no |
| **SIA 387/4:2023** (lighting + solar protection) | shop.sia.ch; contact **Yiqiao Yang** (SIA) | **Table 9 solar protection: yes** (`sia-387-4-2017.blinds.json`, eq. 18-20 confirmed). **Lighting content: no** |
| **SIA 180:2014** (comfort / operative temperature) | shop.sia.ch; Yiqiao Yang | **Fig. 3 & 4 + chiffre 2.3.1: yes**. Exact operative temperature / θrm window definition: to be confirmed |
| **SIA 2024:2021** (usage data, cooling demand) | shop.sia.ch | **Category 3.1: yes**. Other categories: partial |
| **SIA 2056** (building cooling) | shop.sia.ch | no |
| **SIA 380:2022** (umbrella standard — weighting, threshold matching) | shop.sia.ch (paid); `term.sia.ch/?id=1894` (factor, paid) | **no — abandoned (no purchase)** |

## Reserves by criterion — "validated under reserve" status

| Criterion (tool) | What is missing | How the tool works without it | Verdict rendered | Reserve to lift with |
|---|---|---|---|---|
| **Heating SCoP** `SIA3802_HEATING_SCOP` | Seasonal equivalence EN 14825 (heating) | **Diagnostic** (reference project input, NOT a requirement: SIA 380/2 note ⁶ "tables 5 to 9 do not constitute requirements"). Compares SCoP against the SIA band (tables 8/9), with caveat | **INDICATIVE DIAGNOSTIC** `[TO VERIFY]` — non-blocking; compliance is decided at §7.2.5.2. No "gate" to build. | **SN EN 14825 (heating part)** — only to lift the indicative caveat; partial load / bin conditions are NOT needed (no recalculation) |
| **Lighting control** `SIA3802_LIGHTING_CONTROL` | SIA 387/4 numerical tables (lighting control) | **Best effort without the document**: a SIA 387/4 reviewer mapping (`SIA3874_lighting_control_mapping_<project>.csv`) covering lit rooms credits the criterion **UNDER RESERVE** (reviewer attestation, not an independent verification). Without mapping → PARTIAL | **AVAILABLE UNDER RESERVE** (with mapping) / PARTIAL (without) — non-blocking | **SIA 387/4:2023 (lighting control tables)** to lift the reserve |
| **§7.2.4 — cooling demand classification** | Necessary / desirable rule (§3.2) | Takes the `cooling_category` provided by the reviewer; otherwise indeterminate | §7.2.4 lock applied **under reserve**; unknown category → `NOT_DETERMINED` | **SIA 180 / SIA 2024 / SIA 2056** |
| **§7.2.4 — threshold matching 7/12 ↔ application case** | Exact case ↔ threshold correspondence | Applies 7 W/m² (new build) / 12 (existing) based on the reviewed status | Thresholds applied **under reserve** `[À VÉRIFIER]` | **SIA 380 umbrella standard** (abandoned) |
| **Summer comfort SIA 180** `SIA3802_SUMMER_COMFORT_*` | Exact operative temperature + θrm window definition | Calculation from 48 h θrm and frozen Fig. 3/4 | Blocking if overheating is **confirmed**; otherwise reserve — **under reserve** of the definition | **SIA 180:2014 (operative temperature)** → norm-analyst |
| **Cooling SEER** `SIA3802_COOLING_EER_SEER` | — (nothing: SN EN 14825 cooling frozen) | Compares declared SEER against Table 5/6 band | **VALIDATED (clean pass)** ✅ | *(reserve lifted)* |

## In practice
- A report can therefore **conclude** (COMPLIANT / NOT_DETERMINED / NOT_COMPLIANT) without
  these documents; the lines above remain **explicitly reserved** in the
  deliverables (caveats `[TO VERIFY]` / `outstanding` notes).
- Upon receipt of a document, update the corresponding frozen reference
  (via its `scripts/…` script) and lift the reserve in this table + in the code
  (remove the relevant caveat), with a non-regression test.
- **Never** convert one of these reserves to `PASS` without the document or a
  reviewer attestation.
