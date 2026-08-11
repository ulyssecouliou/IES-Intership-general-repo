# -*- coding: utf-8 -*-
"""Check where the project's modules were actually loaded from, under VEScripts.

THE TRAP. VEScripts keeps the **same interpreter** from one click on Run to the
next, so `sys.modules` persists. A `scripts` package imported from ANOTHER
repository stays cached there and shadows this one -- even if `sys.path` has
been corrected in between, because a module already loaded is never reloaded.

It happened on 2026-08-06:

    ImportError: cannot import name 'sonde_aps' from 'scripts'
    (C:\\Users\\ulysse.couliou\\Documents\\SIA_Compliance_Scripts\\scripts\\__init__.py)

The file existed -- in the consolidated repository, not in the one VE had in
memory.

THE VISIBLE CASE IS THE HARMLESS ONE, because it raises. The dangerous case is
silent: `ve_adapter` loaded from the old repository would run without a word,
on code from before the fixes, and produce credible results from the wrong
source. Nothing distinguishes those results from correct ones except knowing
where they came from -- which is what this module answers.

THE PURGE CANNOT LIVE HERE. It has to run *before* the first
`import scripts...`, so it belongs in the launcher itself. This module supplies
the check that comes after, once the imports are done.
"""

from __future__ import print_function

import os
import sys

#: The project's packages. A module loaded from another repository under one of
#: these names is an error, not a variant.
PACKAGES = ('scripts', 've_adapter', 'engine', 'ui', 'swiss_sia')


def prefixes_to_purge():
    """Module-name prefixes a launcher must purge.

    Returns:
        tuple[str]: Exact names, and submodule prefixes.
    """
    return PACKAGES + tuple(name + '.' for name in PACKAGES)


def modules_outside_repository(root, modules=None):
    """Project modules loaded from somewhere other than `root`.

    Args:
        root: Root of the expected repository.
        modules: Module table to inspect; `sys.modules` by default.

    Returns:
        list[tuple[str, str]]: `(name, file)`, sorted. Empty when all is well.
    """
    table = sys.modules if modules is None else modules
    expected = os.path.normcase(os.path.abspath(root))
    intruders = []
    for name, module in list(table.items()):
        if not _belongs_to_project(name):
            continue
        origin = getattr(module, '__file__', None)
        if not origin:
            # A namespace package: no file to compare, so nothing to hold
            # against it. Do not report it for want of evidence.
            continue
        path = os.path.normcase(os.path.abspath(origin))
        if not path.startswith(expected + os.sep):
            intruders.append((name, origin))
    return sorted(intruders)


def _belongs_to_project(name):
    """Whether a module name belongs to one of the project's packages.

    Args:
        name: Full module name.

    Returns:
        bool: True for a project package or any of its children.
    """
    return name in PACKAGES or name.startswith(
        tuple(package + '.' for package in PACKAGES))


def intrusion_message(root, intruders):
    """Write the diagnosis to print in the VEScripts console.

    Args:
        root: Expected root.
        intruders: What `modules_outside_repository` returns.

    Returns:
        str: Ready to print; empty when there is nothing to say.
    """
    if not intruders:
        return u''
    lines = [
        u'STOP: project modules are coming from another repository.',
        u'',
        u'  expected under: %s' % root,
    ]
    for name, origin in intruders:
        lines.append(u'  %-28s <- %s' % (name, origin))
    lines.extend([
        u'',
        u'VEScripts keeps the same interpreter from one Run to the next: a',
        u'module already loaded is never reloaded, even if sys.path changes.',
        u'Closing VE and reopening it is enough to clear the cache.',
        u'',
        u'While this message shows, no result is trustworthy: the code being',
        u'executed is not the code in this repository.',
    ])
    return u'\n'.join(lines)


def check(root):
    """Check provenance and print the diagnosis if there is one.

    Args:
        root: Root of the expected repository.

    Returns:
        bool: True when every project module really came from `root`.
    """
    intruders = modules_outside_repository(root)
    if not intruders:
        return True
    print(intrusion_message(root, intruders))
    return False
