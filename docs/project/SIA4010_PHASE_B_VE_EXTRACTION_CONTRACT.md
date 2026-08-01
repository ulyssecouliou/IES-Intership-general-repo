# SIA 4010 Phase B - VE result extraction contract

Purpose: define how candidate ("Testprogramm") results are extracted from a VE
simulation and turned into the `ObservedResult` records the SIA 4010 comparator
consumes. Phase A (official-band ingestion, comparison, class bridge) is
complete and pure-Python. Phase B binds real VE/APS results into that pipeline
and must be qualified inside the VE runtime.

## Boundary and principles

- Entry point: `swiss_sia/reference_model/sia4010/observed_extraction.py`
  - `build_observed_results(expected_results, resolver)` is **expected-driven**:
    it iterates the official expected metrics (from the workbook parsers) and
    asks the resolver for each one's VE value, so observed keys always align
    one-to-one with expected keys.
  - **Fail-closed**: a metric the resolver cannot supply is omitted, so the
    comparator reports it `NOT_CHECKABLE`. No value is fabricated and no unit is
    converted implicitly.
  - `DictResultSource` is the dry-run resolver (see `tests/test_sia4010_phase_b.py`
    for the full pure-Python pipeline dry run). The real resolver is a drop-in
    replacement wrapping the VE runtime and ApacheSim/APS results.

- Units MUST equal the official workbook unit for each metric (kWh, °C, W, ...);
  a mismatch is deliberately `NOT_CHECKABLE`, never silently converted.

## Real-VE resolver: to be qualified (do not invent VE variable names)

The exact VE/APS variable bindings below are **unconfirmed** and must be
verified against the installed VE 2025 runtime and the APS result contract
(`swiss_sia/data_extractor.py`, `swiss_sia/simulation_results.py`). Until a
binding is confirmed, leave it unresolved (the metric stays `NOT_CHECKABLE`).

| Test | Case scope | Quantities the resolver must supply | Candidate VE/APS source (to confirm) |
|---|---|---|---|
| 1 | Case 1E (monthly + annual) | Monthly/annual heating and cooling needs, peaks, room temperatures | ApacheSim zone heating/cooling loads and air temperatures for the BESTEST-style cell |
| 2 | Cases 2A-2D | Annual solar heat gain, total transmitted solar radiation (per window model) | APS solar gain / transmitted radiation per zone/opening |
| 3 | Cases 3A-3L | Annual lighting energy | Lighting energy from the daylight/lighting-control model (SIA 387/4) |
| 4 | Example building (single room) | Fan energy, air-heater / air-cooler energy | Apache system / AHU results |
| 5 | Cases 5A-5D | Fan / heater / cooler / heat-recovery / humidification energy | Multizone AHU results |
| 6 | Example building | Ventilation fan / heater / cooler / heat-recovery energy | Ventilation system results |
| 7 | Example building | Refrigeration and heat-pump electrical energy, PV yield, grid exchange | Plant / PV / heat-pump results |

## Wiring the real accessor (VeApsResultAccessor)

`observed_extraction.VeApsResultAccessor` is the concrete `ResultAccessor` for
Phase B. It holds the injected APS results and a registry of per-quantity
extractors, and is fail-closed by construction:

- an unregistered quantity returns None (metric stays `NOT_CHECKABLE`);
- an extractor that returns None or raises returns None.

To qualify a metric in VE, register a confirmed extractor, for example:

```python
accessor = VeApsResultAccessor(aps_results=results_reader)
accessor.register(
    "annual_fan_energy_kwh",
    lambda aps, binding, expected: _annual_sum_of(aps, find_aps_variable(...)),
)
```

The extractor bodies use `simulation_results.find_aps_variable` /
`collect_room_dynamic_results` over the APS `ResultsReader`. The `MetricBinding`
for that metric must then be marked `confirmed=True` with the source locator of
the confirmed APS variable. Nothing is registered by default, so the launcher
run stays fully `NOT_CHECKABLE` until real extractors and bindings are supplied.

## Prerequisites for a real Phase B run

1. VE 2025 runtime with a disposable blank project (per the runtime boundary).
2. The official example building imported (IFC/gbXML) for tests 4-7; the
   BESTEST-style cells built for tests 1-3.
3. The official bundle deposited and its `official_manifest.json` generated
   (`bundle_builder.write_manifest`).
4. A confirmed VE/APS variable binding for each required metric above.

## Claim boundary

Passing every band is `OFFICIAL_RESULTS_RECORDED`, never "validated". Automated
band comparison is a cross-check only; official class validation still requires
recorded results and an independent SIA sub-commission attestation.
