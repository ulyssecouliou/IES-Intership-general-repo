# English default and language support

Status date: 27 August 2026

## Contract

Every maintained client-facing entry point starts in English when no explicit
language has been selected. German, French and Italian remain user-selectable in
the maintained compliance interface and report workflow.

An existing project may reopen in a language that its reviewer explicitly saved.
That is persistence of a user choice, not a default-language override.

## Verified defaults

| Surface | Default mechanism | Verified value |
|---|---|---|
| Shared SIA 4010 catalogue | `ui_translations.DEFAULT_LANGUAGE` | `en` |
| Client compliance window | `initial_client_language()` | `en` for new/legacy contexts |
| Client report context | dataclass and normalization fallback | `en` |
| PDF/XLSX report launcher | `SIA_REPORT_LANGUAGE` fallback | `en` |
| Native SIA 4010 builder | empty/unknown locale normalization | `en` |
| Template-remediation UI | `SWISS_SIA_UI_LANGUAGE` fallback | `en` |
| Legacy navigator | `ui.i18n.DEFAULT_LANGUAGE` | `en` |

The maintained catalogue exposes exactly `en`, `de`, `fr` and `it`. Automated
tests verify catalogue completeness, placeholder preservation, locale
normalization, the language selector and English defaults.

The historical `ui/i18n.py` navigator contains only English and French because
that package is no longer the maintained client product. Its initial language is
nevertheless English, so no repository UI now starts in French implicitly.

## Documentation entry point

The default documentation route is also English: `README.md`,
`FINAL_TRANSMISSION_RECEIPT_2026-08-28.md`,
`NEW_MAINTAINER_START_HERE.md`, `AI_USAGE_AND_GOVERNANCE.md` and the maintained
technical guides. `docs/project/INDEX.md` is the canonical English documentation
map. The current authority addendum and the actionable Test 1–7 status are also
maintained in English.

Dated French handover notes and normative sources in French or German remain
available as historical or authoritative evidence. They are explicitly labelled
as such, are not the default starting path and must not override the later
English status records. Source quotations are not translated when translation
could alter their evidential meaning.

## Runtime checks for the incoming maintainer

On a clean disposable VE project:

1. clear `SIA_UI_LANGUAGE`, `SWISS_SIA_UI_LANGUAGE` and `SIA_REPORT_LANGUAGE`;
2. launch `Run_VE_Swiss_Compliance.py` and confirm the first screen is English;
3. switch successively to German, French and Italian;
4. close and reopen after saving an explicit choice, confirming persistence;
5. generate one report per language and inspect headings, accents and legal
   wording visually;
6. create a new project context and confirm it returns to English.

Environment-variable examples:

```powershell
$env:SIA_UI_LANGUAGE = "de"
$env:SWISS_SIA_UI_LANGUAGE = "fr"
$env:SIA_REPORT_LANGUAGE = "it"
```

Remove the variables to restore the English default. Unknown or empty values
normalize to English rather than silently selecting a national language.

## Scope limit

English-by-default and translation completeness are software properties. They do
not prove that every historical normative source or authority quotation has been
translated; such source material intentionally remains in its authoritative
language.
