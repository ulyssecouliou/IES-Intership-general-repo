Multilingual Documentation
==========================

Recommended Strategy
--------------------

Use English as the canonical source language and generate translations through
Sphinx gettext catalogs.

This avoids duplicated Markdown or reStructuredText files drifting out of sync.

Supported Languages
-------------------

The intended language set is:

``en``
   English canonical documentation.

``fr``
   French translation.

``it``
   Italian translation.

``de``
   German translation.

Workflow
--------

1. Build gettext templates:

   .. code-block:: powershell

      python docs/tools/build_docs.py --builder gettext

2. Initialize or update translation catalogs with ``sphinx-intl``:

   .. code-block:: powershell

      sphinx-intl update -p docs/build/gettext -d docs/source/locales -l fr -l it -l de

3. Translate the ``.po`` files in:

   .. code-block:: text

      docs/source/locales/fr/LC_MESSAGES/
      docs/source/locales/it/LC_MESSAGES/
      docs/source/locales/de/LC_MESSAGES/

4. Build translated HTML:

   .. code-block:: powershell

      python docs/tools/build_docs.py --language fr --builder html
      python docs/tools/build_docs.py --language it --builder html
      python docs/tools/build_docs.py --language de --builder html

Glossary Control
----------------

Compliance terms should be translated through a controlled glossary, not ad hoc.
Examples:

* readiness report;
* official evidence;
* validation class;
* not checkable;
* automated precheck indicator;
* reference calculation.

Runtime Report Localization
---------------------------

The Sphinx translation system handles documentation. Excel report localization
should be implemented separately through a Python i18n layer, for example:

.. code-block:: text

   locales/
     en.json
     fr.json
     it.json
     de.json

   i18n.py

The report generator would then call ``tr("dashboard.title")`` instead of
hardcoding labels in ``excel_report.py``.
