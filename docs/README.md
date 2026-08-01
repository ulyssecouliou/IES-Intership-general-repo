# Swiss SIA Compliance Checker Documentation

This folder contains the Sphinx documentation source for the Swiss SIA Compliance
Checker.

The canonical documentation language is English. Translated documentation can be
generated through Sphinx gettext catalogs for French, Italian, and German.

## Quick Start

Install the documentation dependencies in a Python environment:

```powershell
python -m pip install -r docs/requirements-docs.txt
```

Build the English HTML documentation:

```powershell
python docs/tools/build_docs.py --language en --builder html
```

If an earlier HTML directory is locked by a browser or synchronization client,
build into a clean stable output root:

```powershell
python docs/tools/build_docs.py --language en --builder html --output-root docs/build/latest
```

Build a single-page English handout for manager reviews:

```powershell
python docs/tools/build_docs.py --language en --builder singlehtml
```

Extract translatable strings:

```powershell
python docs/tools/build_docs.py --builder gettext
```

Build another language after `.po` files have been translated:

```powershell
python docs/tools/build_docs.py --language fr --builder html
python docs/tools/build_docs.py --language it --builder html
python docs/tools/build_docs.py --language de --builder html
```

## Manager Multilingual Brief

The latest manager-facing English/French/German/Italian brief is available at:

```text
docs/source/manager_multilingual_brief.md
```

The Sphinx-native version used in the generated HTML documentation is:

```text
docs/source/manager_multilingual_brief_sphinx.rst
```

It summarizes the current product status, latest verified report, safe compliance
wording, blockers, evidence needs, and recommended manager discussion agenda.

## Documentation Quality Audit

The code handover audit is documented in:

```text
docs/source/documentation_quality.rst
```

It explains the files covered by the release validator, the English-only
docstring policy, and the generated API reference strategy.

## Manager Reference Integration

The manager-provided SIA 4010 software register and SIA 380/2 navigator backlog
are summarized in:

```text
docs/project/MANAGER_REFERENCE_INTEGRATION.md
docs/source/manager_reference_integration.rst
```

The generated Excel workbook also includes `SIA3802 JUSTIFICATIONS`,
`SIA4010 READINESS`, `SIA4010 PREVALIDATION`, `SIA4010 CLASS MATRIX`,
`SIA4010 SOFTWARE REGISTER` and `NAVIGATOR BACKLOG` sheets.

## Three-Room Reference Model

The current `SIA_compatible_model` VE remediation and regression workflow is
documented in:

```text
docs/project/SIA_COMPATIBLE_MODEL_REFERENCE_ACTIONS.md
docs/source/reference_model_guide.rst
```

## Output

Generated HTML documentation is written to:

```text
docs/build/html/<language>/
```

The current verified multilingual build is written to:

```text
docs/build/latest/html/<language>/
```

Generated single-page documentation is written to:

```text
docs/build/singlehtml/<language>/
```

Generated gettext templates are written to:

```text
docs/build/gettext/
```

Translation catalogs are stored in:

```text
docs/source/locales/<language>/LC_MESSAGES/
```
