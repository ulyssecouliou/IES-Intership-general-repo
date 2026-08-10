# -*- coding: utf-8 -*-
"""Confront a fresh APS probe with the quantities the SIA tests declare.

WHY THIS EXISTS. Twenty quantities of tests 2 to 6 have no VE variable bound to
them. Ten carry a candidate, hand-derived from the probe of 2026-08-06 -- taken
on a model that had NO ApacheHVAC network, so the components those quantities
measure were simply not in it. Once a network is built and the model probed
again, somebody has to redo that comparison by hand, for twenty rows, reading
two files side by side. That is the kind of task that gets done once, tiredly,
and then trusted.

This script does the mechanical half so the next VE session is decisive rather
than exploratory: run the probe, run this, read one sheet.

THREE THINGS IT REFUSES TO DO, and each refusal is the point.

1. **It never binds anything.** Finding `Sys Mech vent heating load` in the
   probe does not make it the right variable for `Wärmezufuhr Lufterwärmer`. A
   name that exists and a name that is correct are different claims, and only a
   human reading the VE model can make the second. This script reports
   PRESENCE. `ve_adapter/bandes_adapter.py::LIAISONS` stays hand-edited.

2. **Absent from this probe does not mean it does not exist.** The model may
   simply not carry the component. The report says which, by showing how many
   variables the required level holds at all -- a level with nothing on it is a
   missing component, not a missing variable name.

3. **It proposes nothing of its own.** Where the adapter declares no candidate,
   this lists what the probe offers at the required level and stops. Ranking
   those by some keyword similarity would produce a plausible order with no
   basis in the standard, and a plausible order is what gets accepted without
   checking.

Usage:
    python scripts/match_aps_variables.py [probe.json] [--write]
"""

from __future__ import print_function

import io
import json
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.abspath(os.path.join(_HERE, os.pardir))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from ve_adapter import bandes_adapter as adapter  # noqa: E402

DEFAULT_PROBE = os.path.join(_ROOT, 'outputs', 'sonde_aps.json')
REPORT_JSON = os.path.join(_ROOT, 'outputs', 'aps_variable_match.json')
REPORT_SHEET = os.path.join(_ROOT, 'docs', 'FICHE-LIAISONS-APS.md')

#: States a quantity can be in against one probe. Ordered from "done" to
#: "nothing to go on", which is also the order the sheet reads in.
BOUND = 'BOUND'
CANDIDATE_PRESENT = 'CANDIDATE_PRESENT'
CANDIDATE_WRONG_LEVEL = 'CANDIDATE_WRONG_LEVEL'
CANDIDATE_ABSENT = 'CANDIDATE_ABSENT'
CANDIDATE_IMPOSSIBLE = 'CANDIDATE_IMPOSSIBLE'
NO_CANDIDATE = 'NO_CANDIDATE'

STATE_ORDER = (BOUND, CANDIDATE_PRESENT, CANDIDATE_WRONG_LEVEL,
               CANDIDATE_ABSENT, CANDIDATE_IMPOSSIBLE, NO_CANDIDATE)

#: How many of a level's variables to list for a quantity that has no
#: candidate. Enough to be useful, few enough that the reader still opens VE.
#: The count of what was NOT shown is always stated -- a truncated list that
#: does not say it is truncated reads as an exhaustive one.
OFFER_LIMIT = 12


class ProbeUnreadable(IOError):
    """Raised when the probe file is missing or is not a probe."""


def load_probe(path=None):
    """Read a probe produced by `scripts/sonde_aps.py`.

    Args:
        path: Probe file; `outputs/sonde_aps.json` by default.

    Returns:
        dict: The probe.

    Raises:
        ProbeUnreadable: If it is absent, unparseable, or carries no variable
            list. Guessing an empty list would report every quantity as
            "absent from the probe", which is a very confident way of saying
            nothing at all.
    """
    path = path or DEFAULT_PROBE
    if not os.path.exists(path):
        raise ProbeUnreadable(
            'probe absent: %s. Produce it by running '
            'Run_VE_SIA4010_Sonde_APS.py from VEScripts on a model that has '
            'been simulated over the full year.' % path)
    try:
        with io.open(path, encoding='utf-8') as stream:
            probe = json.load(stream)
    except ValueError as error:
        raise ProbeUnreadable('probe unreadable: %s (%s)' % (path, error))
    if not isinstance(probe, dict) or 'variables' not in probe:
        raise ProbeUnreadable(
            'file %s carries no `variables` list: it is not an APS probe.'
            % path)
    return probe


def index_by_level(probe):
    """Group the probe's variables by their model level.

    Args:
        probe: What `load_probe` returns.

    Returns:
        dict: `{level: [variable, ...]}`.
    """
    by_level = {}
    for variable in probe.get('variables') or []:
        by_level.setdefault(variable.get('model_level'), []).append(variable)
    return by_level


def _find(by_level, level, name):
    """Find a variable by name at one level.

    Args:
        by_level: What `index_by_level` returns.
        level: Model level, `'v'`, `'z'`, ...
        name: `aps_varname` to look for.

    Returns:
        dict | None: The variable, or `None`.
    """
    for variable in by_level.get(level) or []:
        if variable.get('aps_varname') == name:
            return variable
    return None


def _levels_carrying(by_level, name):
    """Every level at which a variable name appears.

    A candidate that exists at ANOTHER level than the one declared is a
    declaration error, not a missing component -- and the two call for
    opposite actions. Reporting it as merely "absent" would send someone to
    build a component that is already there.

    Args:
        by_level: What `index_by_level` returns.
        name: `aps_varname` to look for.

    Returns:
        list[str]: Levels carrying it, sorted.
    """
    return sorted(level for level, variables in by_level.items()
                  if any(v.get('aps_varname') == name for v in variables))


def confront(probe, test_number):
    """Compare one test's declared quantities with what the probe holds.

    Args:
        probe: What `load_probe` returns.
        test_number: SIA test number.

    Returns:
        list[dict]: One row per declared quantity.
    """
    by_level = index_by_level(probe)
    declared = adapter.LIAISONS.get(test_number, {})
    candidates = adapter.candidats_a_confirmer(test_number)
    rows = []

    for label in sorted(declared):
        binding = declared[label]
        level = binding.get('niveau')
        at_level = by_level.get(level) or []
        row = {
            'test': test_number,
            'libelle_de': label,
            'niveau': level,
            'variables_au_niveau': len(at_level),
            'piste': binding.get('piste'),
        }

        if binding.get('aps_varname'):
            found = _find(by_level, level, binding['aps_varname'])
            row.update({
                'etat': BOUND,
                'aps_varname': binding['aps_varname'],
                # A bound name that this probe does not carry is worth saying:
                # either the model changed, or the binding was wrong.
                'present_dans_le_releve': found is not None,
            })
            rows.append(row)
            continue

        candidate = candidates.get(label)
        if candidate is None:
            row.update({
                'etat': NO_CANDIDATE,
                'offre_du_niveau': [
                    v.get('aps_varname') for v in at_level[:OFFER_LIMIT]],
                'offre_non_montree': max(0, len(at_level) - OFFER_LIMIT),
            })
            rows.append(row)
            continue

        name = candidate.get('aps_varname_candidat')
        if name is None:
            row.update({
                'etat': CANDIDATE_IMPOSSIBLE,
                'a_confirmer': candidate.get('a_confirmer'),
            })
            rows.append(row)
            continue

        found = _find(by_level, level, name)
        elsewhere = [] if found else _levels_carrying(by_level, name)
        if found:
            state = CANDIDATE_PRESENT
        elif elsewhere:
            state = CANDIDATE_WRONG_LEVEL
        else:
            state = CANDIDATE_ABSENT
        row.update({
            'etat': state,
            'niveaux_portant_le_candidat': elsewhere,
            'aps_varname_candidat': name,
            'display_name': candidate.get('display_name'),
            'niveau_de_preuve': candidate.get('niveau_de_preuve'),
            'a_confirmer': candidate.get('a_confirmer'),
        })
        rows.append(row)

    return rows


def confront_all(probe):
    """Run the confrontation over every test the adapter declares.

    Args:
        probe: What `load_probe` returns.

    Returns:
        dict: Rows, a per-state tally and the level census.
    """
    rows = []
    for test_number in sorted(adapter.LIAISONS):
        rows.extend(confront(probe, test_number))

    tally = dict((state, 0) for state in STATE_ORDER)
    for row in rows:
        tally[row['etat']] = tally.get(row['etat'], 0) + 1

    by_level = index_by_level(probe)
    return {
        'releve': probe.get('aps', {}).get('nom'),
        'nb_variables_relevees': len(probe.get('variables') or []),
        'recensement_par_niveau': dict(
            (level, len(variables))
            for level, variables in sorted(by_level.items())),
        'lignes': rows,
        'effectifs': tally,
        'resolues': tally.get(BOUND, 0),
        'total': len(rows),
    }


def empty_levels(report):
    """Levels a quantity needs that the probe holds nothing at.

    This is the actionable finding. A level with no variables does not mean a
    name is missing -- it means the COMPONENT is not in the model, and no
    amount of searching the probe will help.

    Args:
        report: What `confront_all` returns.

    Returns:
        list[tuple]: `(level, number of quantities needing it)`.
    """
    needed = {}
    for row in report['lignes']:
        if row['variables_au_niveau'] == 0:
            needed[row['niveau']] = needed.get(row['niveau'], 0) + 1
    return sorted(needed.items())


def build_sheet(report):
    """Write the confrontation as a sheet to read beside VE.

    Args:
        report: What `confront_all` returns.

    Returns:
        str: Markdown.
    """
    lines = [
        u'# Fiche de liaisons APS — confrontation d\'un relevé',
        u'',
        u'> **Document généré** par `scripts/match_aps_variables.py`. Il '
        u'compare un relevé de sonde aux grandeurs déclarées dans '
        u'`ve_adapter/bandes_adapter.py`. Il **ne lie rien** : trouver un nom '
        u'dans le relevé ne prouve pas que c\'est la bonne variable. Seule '
        u'une lecture du modèle VE le prouve.',
        u'',
        u'- Relevé : `%s`' % (report['releve'] or u'(sans nom)'),
        u'- Variables relevées : **%d**' % report['nb_variables_relevees'],
        u'- Grandeurs déclarées : **%d**, dont **%d liées**'
        % (report['total'], report['resolues']),
        u'',
        u'| État | Effectif | Ce que ça veut dire |',
        u'|---|---|---|',
        u'| `BOUND` | %d | Liaison déjà déclarée. |'
        % report['effectifs'].get(BOUND, 0),
        u'| `CANDIDATE_PRESENT` | %d | Un candidat existe ET figure dans ce '
        u'relevé. **À confirmer dans VE**, pas acquis. |'
        % report['effectifs'].get(CANDIDATE_PRESENT, 0),
        u'| `CANDIDATE_WRONG_LEVEL` | %d | Le candidat existe, mais à un '
        u'AUTRE niveau que celui déclaré. Erreur de déclaration, pas organe '
        u'manquant — les deux appellent des actions opposées. |'
        % report['effectifs'].get(CANDIDATE_WRONG_LEVEL, 0),
        u'| `CANDIDATE_ABSENT` | %d | Un candidat existe mais ne figure PAS '
        u'dans ce relevé : le modèle ne porte probablement pas l\'organe. |'
        % report['effectifs'].get(CANDIDATE_ABSENT, 0),
        u'| `CANDIDATE_IMPOSSIBLE` | %d | Aucun candidat n\'est possible, et '
        u'la raison est écrite. |'
        % report['effectifs'].get(CANDIDATE_IMPOSSIBLE, 0),
        u'| `NO_CANDIDATE` | %d | Rien de proposé. Le relevé offre la liste '
        u'ci-dessous, sans classement — un classement plausible se ferait '
        u'accepter sans vérification. |'
        % report['effectifs'].get(NO_CANDIDATE, 0),
        u'',
    ]

    vides = empty_levels(report)
    if vides:
        lines.extend([
            u'## ⚠ Niveaux vides — l\'organe manque, pas le nom',
            u'',
            u'Un niveau sans aucune variable ne veut pas dire qu\'un nom est '
            u'introuvable : il veut dire que **le composant n\'est pas dans '
            u'le modèle**. Chercher davantage dans le relevé n\'y changera '
            u'rien.',
            u'',
        ])
        for level, count in vides:
            lines.append(u'- Niveau `%s` : **0 variable**, alors que %d '
                         u'grandeur(s) en dépendent.' % (level, count))
        lines.append(u'')

    lines.extend([u'## Recensement du relevé, par niveau', u'',
                  u'| Niveau | Variables |', u'|---|---|'])
    for level, count in sorted(report['recensement_par_niveau'].items()):
        lines.append(u'| `%s` | %d |' % (level, count))
    lines.append(u'')

    for test_number in sorted(set(row['test'] for row in report['lignes'])):
        lines.append(u'## Test %d' % test_number)
        lines.append(u'')
        lines.append(u'| Grandeur (libellé du classeur) | Niveau | État | '
                     u'Variable | À faire |')
        lines.append(u'|---|---|---|---|---|')
        for row in sorted(
                (r for r in report['lignes'] if r['test'] == test_number),
                key=lambda r: (STATE_ORDER.index(r['etat']), r['libelle_de'])):
            lines.append(u'| `%s` | `%s` (%d var.) | **%s** | %s | %s |'
                         % (row['libelle_de'], row['niveau'],
                            row['variables_au_niveau'], row['etat'],
                            _variable_cell(row), _action_cell(row)))
        lines.append(u'')

    lines.extend([
        u'## Ce que cette fiche ne dit pas',
        u'',
        u'- Qu\'une variable présente est la BONNE. Elle est présente, rien '
        u'de plus.',
        u'- Qu\'une variable absente n\'existe pas. Ce relevé vient d\'UN '
        u'modèle ; un autre modèle en porterait d\'autres.',
        u'- Rien sur la conformité. Une liaison résolue permet de mesurer ; '
        u'elle ne décide d\'aucun verdict.',
        u'',
    ])
    return u'\n'.join(lines) + u'\n'


def _variable_cell(row):
    """Cell naming the variable, or saying there is none.

    Args:
        row: One confrontation row.

    Returns:
        str: Markdown cell.
    """
    if row['etat'] == BOUND:
        marque = u'' if row.get('present_dans_le_releve') \
            else u' — **absente de ce relevé**'
        return u'`%s`%s' % (row['aps_varname'], marque)
    if row.get('aps_varname_candidat'):
        return u'`%s` (%s)' % (row['aps_varname_candidat'],
                               row.get('display_name') or u'—')
    if row['etat'] == NO_CANDIDATE and row.get('offre_du_niveau'):
        offre = u', '.join(u'`%s`' % nom for nom in row['offre_du_niveau'])
        if row.get('offre_non_montree'):
            offre += u' … et %d autres' % row['offre_non_montree']
        return offre
    return u'—'


def _action_cell(row):
    """Cell saying what to do next for this quantity.

    Args:
        row: One confrontation row.

    Returns:
        str: Markdown cell.
    """
    if row['etat'] == BOUND:
        if row.get('present_dans_le_releve'):
            return u'Rien.'
        return (u'Vérifier : la liaison déclarée ne figure pas dans ce '
                u'relevé.')
    if row['etat'] == CANDIDATE_PRESENT:
        return u'Confirmer dans VE que cette variable mesure bien : %s' \
            % (row.get('piste') or u'la grandeur attendue')
    if row['etat'] == CANDIDATE_WRONG_LEVEL:
        return (u'**Le niveau déclaré est faux.** La variable existe, au(x) '
                u'niveau(x) `%s`. Corriger `niveau` dans l\'adaptateur : '
                u'aucune simulation ne réglera cela.'
                % u'`, `'.join(row.get('niveaux_portant_le_candidat') or []))
    if row['etat'] == CANDIDATE_ABSENT:
        return (u'Le modèle ne porte pas cet organe. Le construire, '
                u'simuler, re-sonder.')
    if row['etat'] == CANDIDATE_IMPOSSIBLE:
        return row.get('a_confirmer') or u'Voir l\'adaptateur.'
    if row['variables_au_niveau'] == 0:
        return (u'Niveau vide : construire l\'organe avant de chercher un '
                u'nom.')
    return u'Choisir dans VE parmi les variables du niveau : %s' \
        % (row.get('piste') or u'—')


def main(arguments=()):
    """Entry point.

    Args:
        arguments: Optional probe path, and `--write` to write the outputs.

    Returns:
        int: 0 when the confrontation ran, 1 when the probe is unusable.
    """
    paths = [a for a in arguments if not a.startswith('--')]
    try:
        probe = load_probe(paths[0] if paths else None)
    except ProbeUnreadable as error:
        print(u'%s' % error)
        return 1

    report = confront_all(probe)
    print(u'relevé : %d variables, %d grandeurs déclarées'
          % (report['nb_variables_relevees'], report['total']))
    for state in STATE_ORDER:
        print(u'    %-22s %d' % (state, report['effectifs'].get(state, 0)))
    for level, count in empty_levels(report):
        print(u'    niveau `%s` VIDE — %d grandeur(s) en dépendent : '
              u'l\'organe manque au modèle, pas le nom.' % (level, count))

    if '--write' in arguments:
        for path, payload in (
                (REPORT_JSON, json.dumps(report, ensure_ascii=False,
                                         indent=2, sort_keys=True)),
                (REPORT_SHEET, build_sheet(report))):
            folder = os.path.dirname(path)
            if not os.path.isdir(folder):
                os.makedirs(folder)
            with io.open(path, 'w', encoding='utf-8') as stream:
                stream.write(payload)
            print(u'    écrit : %s' % os.path.relpath(path, _ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
