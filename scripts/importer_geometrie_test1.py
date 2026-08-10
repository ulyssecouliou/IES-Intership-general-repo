# -*- coding: utf-8 -*-
u"""Importe la géométrie du Test 1 dans VE, et RELIT ce que VE en a fait.

POURQUOI UN SCRIPT SÉPARÉ DE LA SONDE. Un import **modifie le modèle**. La
sonde du Test 1 est un relevé : elle crée des matériaux d'essai et les
supprime. Y glisser un import ferait qu'un simple relevé muterait le modèle
sans qu'on l'ait demandé — exactement le genre d'effet de bord qu'on ne
remarque qu'une fois le mal fait. Cet import se lance donc **explicitement**,
sur un projet jetable.

CE QUE FAIT CE SCRIPT, DANS L'ORDRE :

    1. écrit le gbXML depuis `ve_adapter/gbxml_test1.py` — qui refuse déjà
       d'écrire une géométrie incohérente ;
    2. l'importe par `ImportGBXML.import_file`, dont la signature n'est pas
       introspectable : plusieurs formes d'appel sont essayées, et celle qui
       répond est CONSIGNÉE ;
    3. **relit `get_bodies()` puis `get_areas()`** et confronte les surfaces
       à celles de la source.

L'ÉTAPE 3 EST LA SEULE QUI PROUVE QUELQUE CHOSE. Un import qui ne lève pas ne
dit rien : les épaisseurs de couche à 1 mm ont été créées sans la moindre
erreur, et valaient un R quarante-sept fois trop faible. Une géométrie
importée de travers se comporterait pareil.

Il écrit `outputs/import_geometrie_test1.json`.
"""

from __future__ import print_function

import io
import json
import os
import sys

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

from scripts.run_test1_dans_ve import (  # noqa: E402
    _dans_ve, _membres, _serialisable, dire)

CHEMIN_RAPPORT = os.path.join(_RACINE, 'outputs', 'import_geometrie_test1.json')
CHEMIN_GBXML = os.path.join(_RACINE, 'outputs', 'test1_cellule.xml')

#: Formes d'appel essayées pour `import_file`, de la plus complète à la plus
#: simple. La documentation annonce `(file_name, heal_geometry, cap_mode,
#: cap_height)` mais s'est déjà trompée sur la casse ; la docstring réelle se
#: réduit à « cap_height ». On essaie donc, et on consigne ce qui répond.
#:
#: Chaque entrée est `(libellé, arguments après le nom de fichier)`.
FORMES_DAPPEL = (
    (u'file_name seul', ()),
    (u'file_name + heal_geometry', (True,)),
    (u'file_name + heal + cap_mode', (True, 0)),
    (u'file_name + heal + cap_mode + cap_height', (True, 0, 0.0)),
)

#: Tolérance de comparaison des surfaces relues, en m². Assez large pour
#: absorber le flottant 32 bits de VE, assez serrée pour attraper une face
#: manquante ou une cote fausse.
TOLERANCE_M2 = 1e-3

#: Correspondance entre nos faces et les clés de `get_areas()`. Elle n'est PAS
#: établie : `get_areas()` rend des agrégats (`ext_wall_area`), pas une entrée
#: par face. La comparaison porte donc sur les TOTAUX, seuls comparables.
CLES_DE_SURFACE = {
    'murs_exterieurs': ('ext_wall_area',),
    'vitrage_exterieur': ('ext_wall_glazed',),
    'plancher': ('ext_floor_area', 'int_floor_area'),
    'toiture': ('ext_ceiling_area', 'int_ceiling_area'),
}


def totaux_attendus(cotes):
    u"""Totaux de surface attendus, agrégés comme `get_areas()` les rend.

    `get_areas()` ne donne pas une entrée par face : il agrège les murs
    extérieurs, le vitrage, le plancher, la toiture. La comparaison se fait
    donc sur ces mêmes agrégats — comparer face à face serait comparer ce que
    VE ne sépare pas.

    Args:
        cotes: Bloc `geometry` de la source.

    Returns:
        dict: `{poste: surface en m²}`.
    """
    from ve_adapter import geometrie_test1 as geometrie
    surfaces = geometrie.surfaces_attendues(cotes)
    return {
        'murs_exterieurs': (surfaces['front_wall'] + surfaces['back_wall']
                            + surfaces['left_wall'] + surfaces['right_wall']),
        'vitrage_exterieur': surfaces['windows'],
        'plancher': surfaces['floor'],
        'toiture': surfaces['ceiling'],
    }


def totaux_releves(corps):
    u"""Additionne les surfaces relues sur tous les corps du modèle.

    Args:
        corps: Liste de `VEBody`.

    Returns:
        dict: `{poste: surface}`, un poste absent restant à `None`.
    """
    cumul = dict((poste, None) for poste in CLES_DE_SURFACE)
    for objet in corps:
        try:
            aires = objet.get_areas() or {}
        except Exception:  # noqa: BLE001 -- l absence est un resultat
            continue
        for poste, cles in CLES_DE_SURFACE.items():
            for cle in cles:
                valeur = aires.get(cle)
                if valeur is None:
                    continue
                cumul[poste] = (cumul[poste] or 0.0) + float(valeur)
    return cumul


def comparer(attendus, releves):
    u"""Confronte les surfaces relues aux surfaces attendues.

    Args:
        attendus: Ce que rend `totaux_attendus`.
        releves: Ce que rend `totaux_releves`.

    Returns:
        dict: Un verdict par poste — jamais un booléen global, qui masquerait
        quel poste diverge.
    """
    verdicts = {}
    for poste, attendu in sorted(attendus.items()):
        obtenu = releves.get(poste)
        if obtenu is None:
            verdicts[poste] = {
                'attendu_m2': attendu, 'releve_m2': None,
                'statut': 'NON_RELEVE',
                'note': u'VE n expose pas ce poste sur les corps lus. '
                        u'Ne PAS le lire comme zero.',
            }
            continue
        ecart = obtenu - attendu
        verdicts[poste] = {
            'attendu_m2': attendu, 'releve_m2': obtenu, 'ecart_m2': ecart,
            'statut': 'CONCORDE' if abs(ecart) <= TOLERANCE_M2 else 'DIVERGE',
            'note': (u'' if abs(ecart) <= TOLERANCE_M2 else
                     u'La geometrie importee ne reproduit pas la source. '
                     u'L import a pu reussir en produisant une cellule fausse.'),
        }
    return verdicts


def _essayer_import(importeur, chemin):
    u"""Essaie les formes d'appel connues jusqu'à ce que l'une réponde.

    La signature n'est pas introspectable : sa docstring se réduit à
    « cap_height ». On essaie donc, du plus complet au plus simple, et on
    consigne ce qui a marché — ce relevé vaudra pour tous les imports
    suivants.

    Args:
        importeur: `iesve.ImportGBXML`.
        chemin: Fichier gbXML.

    Returns:
        dict: Forme retenue et résultat, ou les échecs de chaque essai.
    """
    essais = []
    for libelle, arguments in FORMES_DAPPEL:
        try:
            resultat = importeur.import_file(chemin, *arguments)
        except Exception as erreur:  # noqa: BLE001 -- un refus est un resultat
            essais.append({'forme': libelle, 'statut': 'ECHEC',
                           'erreur': u'%s: %s' % (type(erreur).__name__,
                                                  erreur)})
            continue
        essais.append({'forme': libelle, 'statut': 'OK',
                       'retour': _serialisable(resultat)})
        return {'forme_retenue': libelle, 'essais': essais}
    return {'forme_retenue': None, 'essais': essais}


def importer(chemin_gbxml=None):
    u"""Déroule l'import et la relecture.

    Args:
        chemin_gbxml: gbXML à importer ; écrit depuis la source si absent.

    Returns:
        dict: Rapport, écrit aussi sur disque.
    """
    from ve_adapter import gbxml_test1 as gbxml
    from ve_adapter import geometrie_test1 as geometrie

    rapport = {
        'dans_ve': _dans_ve(),
        'avertissement': (
            u"Ce script MODIFIE le modele VE : il y importe une geometrie. "
            u"A lancer sur un projet JETABLE, jamais sur un modele client."),
        'etapes': [],
    }

    def etape(nom, fonction):
        try:
            valeur = fonction()
        except Exception as erreur:  # noqa: BLE001 -- on consigne
            rapport['etapes'].append({
                'nom': nom, 'statut': 'ECHEC',
                'type_erreur': type(erreur).__name__,
                'erreur': u'%s' % erreur})
            dire(u'  [ECHEC] %-40s %s' % (nom, type(erreur).__name__))
            return None
        rapport['etapes'].append({'nom': nom, 'statut': 'OK',
                                  'valeur': _serialisable(valeur)})
        dire(u'  [OK]    %-40s %s' % (nom, repr(valeur)[:44]))
        return valeur

    dire(u'=== IMPORT DE LA GEOMETRIE DU TEST 1 ===')
    dire(u'  ATTENTION : ce script modifie le modele. Projet jetable requis.')

    cotes = etape(u'cotes de la source', lambda: geometrie.charger_cotes())
    if cotes is None:
        _ecrire(rapport)
        return rapport

    chemin = chemin_gbxml or CHEMIN_GBXML
    etape(u'ecriture du gbXML', lambda: gbxml.ecrire(chemin, cotes))
    attendus = etape(u'surfaces attendues', lambda: totaux_attendus(cotes))

    if not rapport['dans_ve']:
        dire(u'  hors VEScripts : le gbXML est ecrit, l import ne peut pas')
        dire(u'  se faire ici. Relancer depuis VE.')
        _ecrire(rapport)
        return rapport

    import iesve
    etape(u'attributs de ImportGBXML',
          lambda: _membres(iesve.ImportGBXML))
    import_fait = etape(u'import_file : formes essayees',
                        lambda: _essayer_import(iesve.ImportGBXML, chemin))

    if not (import_fait or {}).get('forme_retenue'):
        dire(u'  aucune forme d appel n a repondu : voir le rapport.')
        _ecrire(rapport)
        return rapport

    corps = etape(u'corps du modele apres import',
                  lambda: _corps_apres_import(iesve))
    if corps is not None and attendus is not None:
        etape(u'CONFRONTATION des surfaces',
              lambda: comparer(attendus, totaux_releves(corps)))

    _ecrire(rapport)
    return rapport


def _corps_apres_import(module_iesve):
    u"""Relit les corps du modèle courant.

    Args:
        module_iesve: Module `iesve`.

    Returns:
        list: Corps du premier modèle.
    """
    projet = module_iesve.VEProject.get_current_project()
    modeles = list(projet.models or [])
    if not modeles:
        return []
    return list(modeles[0].get_bodies(False) or [])


def _ecrire(rapport):
    u"""Écrit le rapport et dit où le trouver.

    Args:
        rapport: Rapport d'import.
    """
    dossier = os.path.dirname(CHEMIN_RAPPORT)
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    with io.open(CHEMIN_RAPPORT, 'w', encoding='utf-8') as flux:
        flux.write(json.dumps(rapport, ensure_ascii=False, indent=2))
    dire()
    dire(u'rapport : %s' % CHEMIN_RAPPORT)
    dire(u'-> la seule etape qui prouve quelque chose est la CONFRONTATION.')


def main(arguments=()):
    u"""Point d'entrée.

    Args:
        arguments: Chemin gbXML explicite, facultatif.

    Returns:
        int: 0 si le rapport a pu être écrit, 1 sinon.
    """
    chemins = [a for a in arguments if not a.startswith('--')]
    rapport = importer(chemins[0] if chemins else None)
    return 0 if rapport.get('etapes') else 1
