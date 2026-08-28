# SIA review governance: required evidence and responsibility

This product provides an engineering assessment of an IESVE model and its supplied evidence. It does not issue an official SIA certificate, validate the software method, or replace the decision of the competent project authority.

## Fail-closed rule

Each review domain is reported as `DOCUMENTED`, `RESERVE`, or `BLOCKED`. `DOCUMENTED` means only that traceable evidence was supplied and accepted by the named reviewer; it is not a compliance verdict. Missing, contradictory, placeholder, or under-review information can never become a pass.

## The seven review domains

1. **Weather and location.** Record the climate basis, exact reviewed weather file, intended calculation use, scenario and period, station or municipality, altitude, and the authoritative source for each. A filename match only proves identity; it does not prove that the station or climate scenario is suitable.
2. **Ventilation strategy.** Declare natural, mechanical, mixed-mode, or absent ventilation; state the rooms and systems covered; provide the design justification and flow-rate source. Reconcile this declaration with VE assignments, schedules, controls, and simulated results.
3. **Lighting scope.** State whether lighting is included, which rooms and exclusions apply, and the source of installed or design power and controls. A miscellaneous gain must never be silently reclassified as lighting.
4. **Flow-rate and power sources.** Reference the calculation, schedule, manufacturer data, or approved model readback used for ventilation flows, lighting power, fans, pumps, auxiliaries, and coils. Values present in VE remain model inputs until their design provenance is documented.
5. **Assumptions outside VE.** Maintain a named assumptions register. Every open assumption must have its impact, owner, and due date; it remains a visible report reserve until resolved.
6. **Reviewer and acceptance.** Record name, role, organisation, competence basis, review date, and the precise acceptance scope. The software records these declarations but does not authenticate identity or professional competence.
7. **Legal scope.** The reviewer must explicitly accept that the output is an engineering assessment, not an official certificate or an authority decision. This wording is injected into PDF, Excel, HTML, and JSON exports.

## Weather standard boundary

The climate dataset must be selected for the actual calculation purpose. SIA 2028 C2:2023 distinguishes applications and scenarios; for example, the SIA 380/2 cooling-need verification and the SIA 180 summer thermal-protection assessment do not automatically use the same future scenario. The wizard therefore asks for both `weather_use_case` and `weather_scenario_period` and does not infer either from an EPW filename.

Primary references:

- SIA 380/2:2022 product record: <https://shop.sia.ch/normenwerk/architekt/380-2_2022_d/D/Product>
- SIA 2028 C2:2023 climate-data guidance: <https://shop.sia.ch/09ba1bdd-d8dd-43a6-bc82-9b9b3382a453/D/DownloadAnhang>
- SIA 4010 software validation guidance: <https://www.shop.sia.ch/453bb184-649f-4dbb-89c6-c02b08ad82fe/D/DownloadAnhang>

## Who must provide what

- The project authority or client approves the intended assessment scope and source documents.
- The HVAC designer owns ventilation strategy, flow calculations, systems, schedules, and controls.
- The lighting designer owns lighting scope, powers, exclusions, and control assumptions.
- The model author maps approved values into VE and records any modelling simplification.
- The named competent reviewer resolves contradictions, accepts explicit reserves, and signs the defined review scope.
- The software may compare, trace, and report these items; it must not invent or silently approve them.
