# -*- coding: utf-8 -*-
"""Measure how far the French-to-English conversion has got, and what is next.

WHY THIS IS A SCRIPT AND NOT A NOTE IN THE MANUAL. The conversion touches 266
tracked Python files. A count written down goes stale the same day, and a stale
count is worse than none here: someone reads "about a hundred left", converts
twenty, and has no way to tell whether they helped. This measures.

WHAT COUNTS AS FRENCH, and why the test is crude on purpose. A file is counted
when it carries accented characters outside a string literal that the string
table needs. Crude, but it has no false negatives that matter: the French in
this repository is prose -- module notes and docstrings -- and French technical
prose is never accent-free for long. A cleverer detector would be one more
thing to trust.

WHAT IS DELIBERATELY NOT COUNTED:

* `ui/i18n.py`, whose French strings ARE the product. It is bilingual by
  design, not unconverted;
* tests that assert against French documents (the manual, the matrices). Their
  French is a quotation of what they check;
* German workbook labels anywhere. Translating one breaks the lookup.

ORDER OF WORK. Files are listed cheapest first, because the conversion rule is
whole modules only -- a half-translated file is the one nobody can read -- and
the way to keep that rule is to pick modules that fit in one sitting.

Usage:
    python scripts/translation_progress.py [--all]
"""

from __future__ import print_function

import io
import os
import re
import subprocess
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, os.pardir))

#: Characters that French prose cannot avoid for long, MINUS the German
#: umlauts. The first version of this class included a-umlaut, o-umlaut
#: and u-umlaut, so every German workbook label -- `Warmezufuhr
#: Lufterwarmer` and its kin -- was counted as French, in a module whose
#: own docstring promises German is not counted. A measuring instrument
#: that contradicts its own documentation is worse than no measurement.
_ACCENTS = re.compile(u'[éèêàâùûçôî]', re.UNICODE)

#: Files whose French is the product or a quotation, not a backlog item. Each
#: entry says WHY, because an unexplained exclusion list becomes a place to
#: hide work.
EXEMPT = {
    'ui/i18n.py':
        'the French strings ARE the product; the module is bilingual by design',
    'engine/tests/test_manuel_de_reprise.py':
        'asserts against the French manual; its French is a quotation',
    'engine/tests/test_build_traceability_matrix.py':
        'asserts against French matrices; same reason',
    'scripts/translation_progress.py':
        'its own accent class is data, not prose',
    'scripts/quality/validate_release.py':
        'carries a list of French words it searches FOR; that list is data',
    'scripts/freeze_test4_consignes.py':
        'its French strings are written into a frozen reference and from '
        'there into a French sheet; prose converted 2026-08-10',
}

#: Directories excluded from the count, with the reason.
EXEMPT_DIRS = {
    'swiss_sia': 'SIA 380/2 workstream, owned separately',
    'tests': 'covers swiss_sia, owned separately',
    'scripts/legacy': 'kept for reference, not maintained',
}


def tracked_python_files():
    """Every Python file git tracks.

    Returns:
        list[str]: Repository-relative paths, slash-separated.

    Raises:
        RuntimeError: If git cannot list them -- guessing from a directory
            walk would silently count generated and vendored files.
    """
    try:
        output = subprocess.check_output(
            ['git', 'ls-files', '*.py'], cwd=_ROOT)
    except (OSError, subprocess.CalledProcessError) as error:
        raise RuntimeError('cannot list tracked files: %s' % error)
    return sorted(line.replace('\\', '/')
                  for line in output.decode('utf-8').splitlines() if line)


def _is_exempt(path):
    """Whether a path is out of scope, and why.

    Args:
        path: Repository-relative path.

    Returns:
        str | None: The reason, or `None` when the file counts.
    """
    if path in EXEMPT:
        return EXEMPT[path]
    for folder, reason in sorted(EXEMPT_DIRS.items()):
        if path.startswith(folder + '/'):
            return reason
    return None


def french_lines(path):
    """Count the lines carrying French prose in one file.

    Args:
        path: Repository-relative path.

    Returns:
        int: Number of lines with at least one accented character.
    """
    full = os.path.join(_ROOT, path.replace('/', os.sep))
    try:
        with io.open(full, encoding='utf-8') as stream:
            return sum(1 for line in stream if _ACCENTS.search(line))
    except (IOError, UnicodeDecodeError):
        return 0


def survey():
    """Measure the conversion across the repository.

    Returns:
        dict: Totals, and the remaining files ordered cheapest first.
    """
    remaining, converted, exempt = [], 0, 0
    for path in tracked_python_files():
        if _is_exempt(path):
            exempt += 1
            continue
        count = french_lines(path)
        if count == 0:
            converted += 1
            continue
        full = os.path.join(_ROOT, path.replace('/', os.sep))
        with io.open(full, encoding='utf-8') as stream:
            total = sum(1 for _ in stream)
        remaining.append({'chemin': path, 'lignes': total,
                          'lignes_francaises': count})

    remaining.sort(key=lambda entry: (entry['lignes'], entry['chemin']))
    return {
        'converti': converted,
        'restant': len(remaining),
        'hors_perimetre': exempt,
        'fichiers': remaining,
    }


def by_area(report):
    """Group what remains by top-level directory.

    Args:
        report: What `survey` returns.

    Returns:
        list[tuple]: `(area, file count, French line count)`, largest first.
    """
    areas = {}
    for entry in report['fichiers']:
        area = entry['chemin'].split('/')[0]
        count, lines = areas.get(area, (0, 0))
        areas[area] = (count + 1, lines + entry['lignes_francaises'])
    return sorted(((area, count, lines)
                   for area, (count, lines) in areas.items()),
                  key=lambda row: -row[2])


def main(arguments=()):
    """Entry point.

    Args:
        arguments: `--all` to list every remaining file.

    Returns:
        int: 0.
    """
    report = survey()
    total = report['converti'] + report['restant']
    part = (100.0 * report['converti'] / total) if total else 0.0
    print('conversion : %d / %d fichiers (%.0f %%), %d hors perimetre'
          % (report['converti'], total, part, report['hors_perimetre']))
    print()
    print('  %-14s %8s %8s' % ('aire', 'fichiers', 'lignes'))
    for area, count, lines in by_area(report):
        print('  %-14s %8d %8d' % (area, count, lines))
    print()

    montres = report['fichiers'] if '--all' in arguments \
        else report['fichiers'][:15]
    print('a faire, du moins cher au plus cher '
          '(regle : un module entier a la fois) :')
    for entry in montres:
        print('  %5d lignes  %4d fr  %s'
              % (entry['lignes'], entry['lignes_francaises'],
                 entry['chemin']))
    if len(montres) < report['restant']:
        print('  ... et %d autres (--all pour tout voir)'
              % (report['restant'] - len(montres)))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
