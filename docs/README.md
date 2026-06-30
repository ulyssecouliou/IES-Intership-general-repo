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

## Output

Generated HTML documentation is written to:

```text
docs/build/html/<language>/
```

Generated gettext templates are written to:

```text
docs/build/gettext/
```

Translation catalogs are stored in:

```text
docs/source/locales/<language>/LC_MESSAGES/
```
