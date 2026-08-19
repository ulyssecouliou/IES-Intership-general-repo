# -*- coding: utf-8 -*-
u"""Prepares the Test 2A delegated-inputs manifest without attesting anything.

WHY. The Test 2A runtime probe returns `SOURCE_BINDINGS_REQUIRED`, and one might
think data was missing. That is wrong: all three inputs the case requires are in
the repository. What is missing is the **declaration** that we are authorised to
use them as normative sources, and a transcription check for one of the three.

WHAT THIS SCRIPT FILLS IN. Everything that is verifiable from the files: path,
recalculated SHA-256 fingerprint, dataset identity, format, semantic scope,
authority and licence reference, and the technical validation report when it
exists.

WHAT IT DOES NOT FILL IN, AND THAT IS THE POINT.
`normative_authorization_status` remains `UNCONFIRMED` for all three. This field
is not technical data: it is an attestation that the use of the source is
authorised. For ISO EN 52016-1:2017 and SIA 2028, this is a licensing question,
and a script has no standing to answer it. Setting it to `CONFIRMED` would flip
`ready_for_binding` and open model generation on an authorisation nobody has given.

Likewise, `technical_validation` only reaches `PASS` if a report genuinely exists
and its fingerprint matches. The ISO 52016 entry has none — the catalogue requires
« independently checked transcription » and that check has not been produced —
so it comes out as `PENDING` with the reason, not as `PASS`.

USAGE. The file produced is a template: the operator copies it into their VE
project as `sia4010_external_inputs.json`, after resolving the authorisation.
"""

from __future__ import print_function

import hashlib
import io
import json
import os
import sys


_RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODELE = os.path.join(_RACINE, 'config', 'sia4010_external_inputs.example.json')
#: Schema version a validation report must carry, as the manifest reader
#: requires it (`VALIDATION_REPORT_SCHEMA_VERSION`).
_SCHEMA_RAPPORT = '1.0'
_SORTIE = os.path.join(
    _RACINE, 'config', 'sia4010_external_inputs.test2a_prepared.json')

#: The three inputs that `required_external_input_ids("test_2A", "2A")` requires.
#: Each entry describes its source, its validation report, and what characterises it.
#: `provenance` must belong to `PROVENANCE_STATUSES`.
ENTREES = {
    'iso52016_2017_chapter7_test_cell': {
        'source': os.path.join('config', 'iso52016_chapter7_confirmed_inputs.json'),
        'validation': os.path.join(
            'refs', 'reference-data',
            'iso52016_chapter7_test_cell.validation.json'),
        'validation_raison': (
            u"Le catalogue exige une transcription vérifiée indépendamment de "
            u"l'ensemble des entrées du chapitre 7. Aucun rapport de ce contrôle "
            u"n'existe dans le dépôt : le produire est un travail à faire, pas "
            u"une case à cocher."
        ),
        'provenance': 'LICENSED_STANDARD_COPY',
        'autorite': u'ISO / CEN, via la copie licenciée du projet',
        'licence': (
            u'ISO EN 52016-1:2017 — copie licenciée du projet ; usage interne '
            u'de traçabilité uniquement, aucune redistribution'
        ),
        'identite': u'ISO EN 52016-1:2017 chapitre 7, cellule d\'essai',
        'format': 'application/json',
        'autorisation': {
            'base': (
                u"Autorisé par Ulysse Couliou le 2026-08-13 : la norme est "
                u"détenue sous copie licenciée du projet, et l'usage est la "
                u"traçabilité interne du candidat à la validation."
            ),
            'portee': (
                u"Transcription et citation de localisateurs pour la "
                u"traçabilité interne. Aucune redistribution du texte normatif."
            ),
            'date': '2026-08-13',
        },
        'portee': [
            u'geometrie de la cellule',
            u'couches opaques legeres et lourdes',
            u'vitrage',
            u'capacite thermique interne',
            u'conditions solaires et limites',
        ],
    },
    'sia2028_dry_normal_zurich_kloten': {
        'source': os.path.join('references', 'standards', 'sia2028', 'KLO_dry.txt'),
        'validation': os.path.join(
            'references', 'standards', 'sia2028', 'KLO_dry.validation.json'),
        'provenance': 'SIA_SUPPLIED',
        'autorite': u'SIA — fourni par le Prof. Gerhard Zweifel',
        'licence': (
            u'SIA 2028 — fichier fourni à titre privé. IES ne détient PAS de '
            u'licence SIA 2028 : la portée d\'usage autorisée doit être établie '
            u'avant toute confirmation'
        ),
        'identite': u'SIA 2028 DRY normal, Zürich-Kloten, 8760 heures',
        'format': 'text/tab-separated-values',
        # The reasoning is the same as already documented for the SIA 2024 entry:
        # direct supply by the validation contact, for this validation.
        # The absence of a general licence does not cancel it, but it bounds
        # the use to this context — and the bound is stated, not assumed.
        'autorisation': {
            'base': (
                u"Autorisé par Ulysse Couliou le 2026-08-13, après examen avec "
                u"Johan : IES n'obtiendra pas de licence SIA 2028, et n'en a pas "
                u"besoin ici parce que le fichier a été fourni directement par "
                u"le Prof. Gerhard Zweifel, responsable de la validation SIA "
                u"4010, en réponse à la demande du candidat et pour cette "
                u"validation. Même base que l'entrée SIA 2024 catégorie 3.1."
            ),
            'portee': (
                u"Usage limité à la campagne de validation SIA 4010 de ce "
                u"candidat, comme preuve contrôlée du projet. Aucune "
                u"redistribution du jeu de données, et aucun usage commercial "
                u"dérivé : l'absence de licence SIA 2028 rend ces deux bornes "
                u"des conditions de l'autorisation, pas des recommandations."
            ),
            'date': '2026-08-13',
        },
        'portee': [
            u'temperature seche horaire',
            u'point de rosee',
            u'rayonnement global, direct et diffus',
            u'pression de station',
        ],
    },
}

#: Entry already prepared by a person, to be REUSED, not rebuilt.
#: `sia4010_evidence/source_audits/.../sia4010_external_inputs.office_3_1.json`
#: carries the complete SIA 2024 entry, including authorisation, with its
#: written justification: direct supply by email of 2026-08-10, retained as
#: controlled evidence and not redistributable. This decision belongs to a
#: human; rebuilding it would overwrite it with a less informed version.
#: Only the paths are recalculated as absolute, because they are relative to
#: the evidence folder whereas this manifest lives elsewhere.
FRAGMENT_PREPARE = {
    'sia2024_office_3_1_standard_profiles': os.path.join(
        'sia4010_evidence', 'source_audits', 'sia2024_3_1_authority_20260810',
        'sia4010_external_inputs.office_3_1.json'),
}


def _empreinte(chemin):
    u"""Returns the SHA-256 of a file.

    Args:
        chemin: Absolute path to the file.

    Returns:
        str: Lowercase hexadecimal fingerprint.
    """
    digest = hashlib.sha256()
    with open(chemin, 'rb') as flux:
        for bloc in iter(lambda: flux.read(65536), b''):
            digest.update(bloc)
    return digest.hexdigest()


def _relatif(chemin_relatif):
    u"""Returns the absolute path of a repository source.

    Args:
        chemin_relatif: Path relative to the repository root.

    Returns:
        str: Absolute path.
    """
    return os.path.join(_RACINE, chemin_relatif)


def _rapport_conforme(chemin, identifiant, source_sha256):
    u"""Says whether a validation report genuinely satisfies the contract.

    Checking that a file exists is not enough: the manifest reader requires
    a specific schema, the entry identifier, and the exact fingerprint of the
    source. `KLO_dry.provenance.json` exists and describes the climate
    provenance well, but it is not a validation report — declaring it `PASS`
    was causing the reader to raise at runtime instead of outputting an honest
    `PENDING` here.

    Args:
        chemin: Absolute path to the report, or `None`.
        identifiant: Delegated-input identifier.
        source_sha256: Fingerprint of the source the report must be linked to.

    Returns:
        tuple[bool, unicode]: Compliance, and the reason for refusal if applicable.
    """
    if not chemin:
        return False, u'aucun rapport de validation technique déclaré'
    if not os.path.exists(chemin):
        return False, u'le rapport de validation déclaré est absent du dépôt'
    try:
        with io.open(chemin, encoding='utf-8') as flux:
            charge = json.load(flux)
    except ValueError as erreur:
        return False, u'rapport de validation illisible : %s' % erreur
    if not isinstance(charge, dict):
        return False, u'le rapport de validation n\'est pas un objet JSON'
    if str(charge.get('schema_version', '')) != _SCHEMA_RAPPORT:
        return False, (
            u"ce fichier ne porte pas le schéma de rapport de validation "
            u"attendu (%s) : c'est un autre artefact, utile mais pas celui-ci"
            % _SCHEMA_RAPPORT)
    if str(charge.get('input_id', '')) != identifiant:
        return False, u'le rapport identifie une autre entrée déléguée'
    if str(charge.get('source_sha256', '')).strip().lower() != source_sha256:
        return False, (
            u"le rapport n'est pas lié à l'empreinte exacte de cette source")
    if str(charge.get('status', '')) != 'PASS':
        return False, (
            u'le rapport conclut %r et non PASS' % charge.get('status'))
    return True, u''


def construire():
    u"""Assembles the prepared manifest, leaving the authorisation open.

    Returns:
        tuple[dict, list]: Manifest and per-entry decision log.
    """
    with io.open(_MODELE, encoding='utf-8') as flux:
        manifeste = json.load(flux)

    journal = []

    # First the already-prepared entries: reuse them as-is.
    for identifiant, fragment_relatif in sorted(FRAGMENT_PREPARE.items()):
        chemin = _relatif(fragment_relatif)
        if not os.path.exists(chemin):
            journal.append((identifiant, 'FRAGMENT_ABSENT', fragment_relatif))
            continue
        with io.open(chemin, encoding='utf-8') as flux:
            prepare = json.load(flux)['inputs'][identifiant]
        dossier = os.path.dirname(chemin)
        entree = dict(prepare)
        entree['source_path'] = os.path.join(dossier, prepare['source_path'])
        validation = dict(prepare['technical_validation'])
        validation['report_path'] = os.path.join(
            dossier, prepare['technical_validation']['report_path'])
        entree['technical_validation'] = validation
        # The fragment fingerprints are VERIFIED, not copied: a file modified
        # since its preparation must show up here, not at runtime.
        divergence = None
        for chemin_verifie, attendu, etiquette in (
            (entree['source_path'], prepare['source_sha256'], 'source'),
            (validation['report_path'], validation['report_sha256'], 'rapport'),
        ):
            if _empreinte(chemin_verifie) != str(attendu).lower():
                divergence = etiquette
                break
        if divergence is not None:
            journal.append((identifiant, 'EMPREINTE_DIVERGENTE', divergence))
        else:
            manifeste['inputs'][identifiant] = entree
            journal.append((identifiant, 'REPRIS_DEJA_AUTORISE', ''))

    for identifiant, plan in sorted(ENTREES.items()):
        entree = manifeste['inputs'][identifiant]
        source = _relatif(plan['source'])
        if not os.path.exists(source):
            journal.append((identifiant, 'SOURCE_ABSENTE', plan['source']))
            continue

        entree['source_path'] = source
        entree['source_sha256'] = _empreinte(source)
        entree['provenance_status'] = plan['provenance']
        entree['source_authority'] = plan['autorite']
        entree['license_reference'] = plan['licence']
        entree['dataset_identity'] = plan['identite']
        entree['machine_readable_format'] = plan['format']
        entree['semantic_scope'] = list(plan['portee'])

        # The authorisation comes from a person, never from the script. What is
        # recorded here is the decision taken and its basis, as stated.
        autorisation = plan.get('autorisation')
        if autorisation is None:
            entree['normative_authorization_status'] = 'UNCONFIRMED'
            entree['normative_authorization_note'] = (
                u"À trancher par une personne : ce champ atteste que l'usage de "
                u"cette source comme référence normative est autorisé. Le "
                u"passer à CONFIRMED fait basculer ready_for_binding et ouvre "
                u"la génération du modèle."
            )
        else:
            entree['normative_authorization_status'] = 'CONFIRMED'
            entree['normative_authorization_basis'] = autorisation['base']
            entree['normative_authorization_scope'] = autorisation['portee']
            entree['normative_authorization_recorded_on'] = autorisation['date']

        validation = plan.get('validation')
        conforme, raison_non_conforme = _rapport_conforme(
            _relatif(validation) if validation else None,
            identifiant,
            entree['source_sha256'],
        )
        if conforme:
            rapport = _relatif(validation)
            entree['technical_validation'] = {
                'status': 'PASS',
                'report_path': rapport,
                'report_sha256': _empreinte(rapport),
            }
            journal.append((identifiant, 'PRET_SAUF_AUTORISATION', ''))
        else:
            plan = dict(plan)
            plan['validation_raison'] = (
                plan.get('validation_raison') or raison_non_conforme)
            entree['technical_validation'] = {
                'status': 'PENDING',
                'report_path': None,
                'report_sha256': None,
                'reason': plan.get('validation_raison') or (
                    u'aucun rapport de validation technique dans le dépôt'),
            }
            journal.append((identifiant, 'VALIDATION_A_PRODUIRE', ''))

    manifeste['purpose'] = (
        u"Manifeste préparé pour le cas test_2A/2A. Chaque champ vérifiable est "
        u"rempli et recalculé ; l'autorisation normative reste UNCONFIRMED pour "
        u"les trois entrées et doit être tranchée par une personne."
    )
    return manifeste, journal


def main(arguments=()):
    u"""Command-line entry point.

    Args:
        arguments: Arguments without the script name. `--ecrire` writes the JSON.

    Returns:
        int: 0 if everything went well.
    """
    manifeste, journal = construire()

    print(u'Entrées déléguées du cas test_2A/2A :')
    for identifiant, etat, detail in journal:
        print(u'  %-46s %s%s'
              % (identifiant, etat, (u' — ' + detail) if detail else u''))
    print()
    autorisees = sum(
        1 for entree in manifeste['inputs'].values()
        if entree.get('normative_authorization_status') == 'CONFIRMED')
    print(u'  %d entrée(s) portent une autorisation CONFIRMED, chacune avec sa '
          u'base écrite et sa portée.' % autorisees)
    print(u'  Aucune n\'a été confirmée par ce script : il inscrit des '
          u'décisions humaines, il n\'en prend pas.')

    if '--ecrire' in arguments:
        with io.open(_SORTIE, 'w', encoding='utf-8') as flux:
            flux.write(json.dumps(manifeste, ensure_ascii=False, indent=2))
            flux.write(u'\n')
        print(u'  écrit : %s' % _SORTIE)
    else:
        print(u'  (ajouter --ecrire pour produire le manifeste)')
    return 0


if __name__ == '__main__':
    sys.exit(main(tuple(sys.argv[1:])))
