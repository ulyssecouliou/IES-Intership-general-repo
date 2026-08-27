# Free-source research for pending SIA 4010 inputs

Research date: 2026-08-25

This note records legitimate public sources only. Public availability does not
by itself make a source normatively sufficient for the SIA 4010 validation
campaign.

## SIA 2024:2021 room-use data

- The SIA shop confirms that the complete SIA 2024:2021 publication is a paid
  product (CHF 130).
- SIA's freely accessible 2025 harmonisation and background reports disclose
  useful subsets of the 2021 data. They include category identifiers, selected
  equipment/process powers, ventilation rates, fan assumptions and full-load
  hours for categories 6.02 and 6.04 and several office/assembly uses.
- The official SIA 2024 leaflet states that a `SIA 2024 Raumdatenblaetter`
  Excel tool contained all inputs and all 45 use sheets and was available from
  energytools.ch. That address now redirects to the general SIA standards page;
  no current first-party download was found.
- Conclusion: the free official reports can cross-check individual values, but
  they do not expose every 24-hour profile, annual calendar rule and
  simultaneity input required by the campaign. The complete profile blockers
  cannot yet be closed.

### ETH HIVE open-source dataset

- The public ETH Zurich HIVE repository (GPL-3.0) contains room-property CSV
  files and hourly YAML/JSON schedules for SIA 2024 room types, including 3.1,
  6.2 and 6.4.
- This is useful as an independent implementation comparison, but its own
  generator describes the schedules as *inspired by* or *like* SIA 2024. It
  also creates lighting and setpoint profiles using project conventions (for
  example, lighting-hour allocation and two-hour preconditioning) rather than
  reproducing a controlled SIA workbook verbatim.
- The room-property source filename is dated 2020-10-08, and selected values do
  not match the later official harmonisation report. For example, the HIVE
  standard-value CSV gives outside-air rates of 18 and 20 m3/(h m2) for 6.2
  and 6.4, whereas the official report gives 14.50 and 9.67 respectively.
- Conclusion: HIVE is a legitimate free secondary source and a useful
  cross-check, but it must not silently replace the campaign's controlled SIA
  2024:2021 inputs. It can only become a campaign input if the validation
  authority explicitly accepts the dataset and its schedule conventions.

Secondary source:

- https://github.com/architecture-building-systems/hive

Official sources:

- https://cms.sia.ch/de/api/getMedia/940
- https://cms.sia.ch/de/api/getMedia/941
- https://shop.sia.ch/16d618e8-b0d7-41e1-b20f-926743792ed7/D/DownloadAnhang
- https://shop.sia.ch/normenwerk/architekt/2024_2021_d/D/Product

## EN 16798-5-1 Annex D rotary heat recovery

- The EPB Center publishes a free 3 MB macro-enabled demonstration workbook
  for EN 16798-5-1, authored by Gerhard Zweifel and updated on 2021-06-09.
- The downloaded package contains rotary heat-recovery variables, coefficients,
  Annex D formula references and explicit references to formula D.5 and table
  D.1.
- The publisher expressly states that the workbook supports implementation but
  does not replace the standard.
- Conclusion: this is a strong, legitimate technical implementation source and
  may substantially reduce the Test 5 blocker. It still needs deterministic
  formula/result qualification and written acceptance as a campaign authority.

Official source:

- https://epb.center/document/demo-en-16798-5-1/

## SIA 387/4 lighting control

- An open-access paper by Gerhard Zweifel describes the hourly model, its six
  daylight-control options, presence dependence and solar-protection options.
- The SIA shop provides the 2017 corrigendum free of charge, but the full 2017
  and 2023 standards remain paid products (CHF 150).
- The Swiss Federal Office of Energy publishes the free CalcuLight workbook for
  calculation according to SIA 387/4. Its current 2025 version cannot be
  assumed equivalent to the 2017 table required by the Test 3 specification.
- The current official SIA register (updated 2026-02-10) describes validation
  class 2A as calculation of lighting energy according to SIA 387/4:2023,
  section 3.4. This is stronger evidence that the current programme-level
  validation scope uses the 2023 edition, but it does not by itself amend an
  older campaign test PDF that still cites the 2017 edition.
- Conclusion: the open paper and tool are valuable cross-checks, but the exact
  governing edition and control mapping still require confirmation.

Primary sources:

- https://www.sciencedirect.com/science/article/pii/S1876610217329569
- https://www.suisseenergie.ch/tools/calculight/
- https://shop.sia.ch/15e5204a-f17a-46b9-88e8-aff053647eb3/F/DownloadAnhang
- https://cms.sia.ch/de/api/getMedia/699

## Test-specific SIA decisions

No public first-party source was found for the campaign-specific decisions on
Test 1 diagnostic 1E control semantics, Test 4/5 fan-curve digitisation
tolerance, or Test 7 PV precedence and east/west allocation. Those questions
remain with the SIA validation authority.

The SIA 4010 validation guide itself is a paid publication. A public REHVA
article by the chair of the SIA validation panel explains that the panel
answers interpretation questions and that these should feed an FAQ. No current
public SIA 4010 FAQ or controlled clarification log was located. The first
request to the authority should therefore be for the latest test package,
revision identifier and FAQ/clarification log; this may resolve several of the
case-specific questions at once.

Sources:

- https://shop.sia.ch/wegleitungen/architekt/sia%204010/d/D/Product
- https://www.rehva.eu/rehva-journal/chapter/admission-of-commercial-simulations-for-energy-calculation-and-their-validation-in-switzerland
