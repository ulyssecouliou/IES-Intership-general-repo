# -*- coding: utf-8 -*-
u"""Prépare le manifeste d'entrées déléguées du Test 2A, sans rien attester.

POURQUOI. La probe runtime du Test 2A rend `SOURCE_BINDINGS_REQUIRED`, et on
pouvait croire qu'il manquait des données. C'est faux : les trois entrées que le
cas exige sont dans le dépôt. Ce qui manque est la **déclaration** que nous
sommes autorisés à les utiliser comme sources normatives, et un contrôle de
transcription pour l'une des trois.

CE QUE CE SCRIPT REMPLIT. Tout ce qui se vérifie sur les fichiers : chemin,
empreinte SHA-256 recalculée, identité du jeu de données, format, portée
sémantique, autorité et référence de licence, et le rapport de validation
technique quand il existe.

CE QU'IL NE REMPLIT PAS, ET C'EST LE POINT.
`normative_authorization_status` reste `UNCONFIRMED` pour les trois. Ce champ
n'est pas une donnée technique : c'est une attestation que l'usage de la source
est autorisé. Pour ISO EN 52016-1:2017 et SIA 2028, c'est une question de
licence, et un script n'a pas qualité à y répondre. Le mettre à `CONFIRMED`
ferait basculer `ready_for_binding` et ouvrirait la génération du modèle sur une
autorisation que personne n'a donnée.

De même, `technical_validation` ne passe à `PASS` que si un rapport existe
réellement et que son empreinte concorde. L'entrée ISO 52016 n'en a aucun — le
catalogue exige « independently checked transcription » et ce contrôle n'a pas
été produit — donc elle sort en `PENDING` avec la raison, pas en `PASS`.

USAGE. Le fichier produit est un modèle : l'opérateur le copie dans son projet
VE sous `sia4010_external_inputs.json`, après avoir tranché l'autorisation.
"""

from __future__ import print_function

import hashlib
import io
import json
import os
import sys


_RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MODELE = os.path.join(_RACINE, 'config', 'sia4010_external_inputs.example.json')
#: Version de schéma qu'un rapport de validation doit porter, telle que le
#: lecteur du manifeste l'exige (`VALIDATION_REPORT_SCHEMA_VERSION`).
_SCHEMA_RAPPORT = '1.0'
_SORTIE = os.path.join(
    _RACINE, 'config', 'sia4010_external_inputs.test2a_prepared.json')

#: Les trois entrées que `required_external_input_ids("test_2A", "2A")` exige.
#: Chaque entrée décrit sa source, son rapport de validation et ce qui la
#: caractérise. `provenance` doit appartenir à `PROVENANCE_STATUSES`.
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
        # Le raisonnement est celui déjà documenté pour l'entrée SIA 2024 :
        # fourniture directe par le responsable de la validation, pour cette
        # validation. L'absence de licence générale ne l'annule pas, mais elle
        # borne l'usage à ce cadre — et la borne est inscrite, pas supposée.
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

#: Entrée déjà préparée par une personne, à REPRENDRE et non à refaire.
#: `sia4010_evidence/source_audits/.../sia4010_external_inputs.office_3_1.json`
#: porte l'entrée SIA 2024 complète, autorisation comprise, avec sa
#: justification écrite : fourniture directe par courriel du 2026-08-10,
#: conservée comme preuve contrôlée et non redistribuable. Cette décision
#: appartient à un humain ; la reconstruire l'écraserait par une version moins
#: informée. Seuls les chemins sont recalculés en absolu, parce qu'ils y sont
#: relatifs au dossier de preuves alors que ce manifeste vit ailleurs.
FRAGMENT_PREPARE = {
    'sia2024_office_3_1_standard_profiles': os.path.join(
        'sia4010_evidence', 'source_audits', 'sia2024_3_1_authority_20260810',
        'sia4010_external_inputs.office_3_1.json'),
}


def _empreinte(chemin):
    u"""Renvoie le SHA-256 d'un fichier.

    Args:
        chemin: Chemin absolu du fichier.

    Returns:
        str: Empreinte hexadécimale minuscule.
    """
    digest = hashlib.sha256()
    with open(chemin, 'rb') as flux:
        for bloc in iter(lambda: flux.read(65536), b''):
            digest.update(bloc)
    return digest.hexdigest()


def _relatif(chemin_relatif):
    u"""Renvoie le chemin absolu d'une source du dépôt.

    Args:
        chemin_relatif: Chemin relatif à la racine du dépôt.

    Returns:
        str: Chemin absolu.
    """
    return os.path.join(_RACINE, chemin_relatif)


def _rapport_conforme(chemin, identifiant, source_sha256):
    u"""Dit si un rapport de validation satisfait vraiment le contrat.

    Vérifier qu'un fichier existe ne suffit pas : le lecteur du manifeste exige
    un schéma précis, l'identifiant de l'entrée et l'empreinte exacte de la
    source. `KLO_dry.provenance.json` existe et décrit bien la provenance du
    climat, mais ce n'est pas un rapport de validation — le déclarer `PASS`
    faisait lever le lecteur à l'exécution au lieu de sortir un `PENDING`
    honnête ici.

    Args:
        chemin: Chemin absolu du rapport, ou `None`.
        identifiant: Identifiant de l'entrée déléguée.
        source_sha256: Empreinte de la source, à laquelle le rapport doit être lié.

    Returns:
        tuple[bool, unicode]: Conformité, et la raison du refus le cas échéant.
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
    u"""Assemble le manifeste préparé, en laissant l'autorisation ouverte.

    Returns:
        tuple[dict, list]: Manifeste et journal des décisions par entrée.
    """
    with io.open(_MODELE, encoding='utf-8') as flux:
        manifeste = json.load(flux)

    journal = []

    # D'abord les entrées déjà préparées : on les reprend telles quelles.
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
        # Les empreintes du fragment sont VÉRIFIÉES, pas recopiées : un fichier
        # modifié depuis sa préparation doit se voir ici, pas à l'exécution.
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

        # L'autorisation vient d'une personne, jamais du script. Ce qui est
        # inscrit ici est la décision prise et sa base, telles qu'énoncées.
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
    u"""Point d'entrée en ligne de commande.

    Args:
        arguments: Arguments sans le nom du script. `--ecrire` écrit le JSON.

    Returns:
        int: 0 si tout s'est bien passé.
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
