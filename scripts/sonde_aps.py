# -*- coding: utf-8 -*-
u"""Sonde des variables de résultats d'un fichier `.aps`.

CE QU'ELLE DÉBLOQUE. Les tests SIA 2 à 6 comparent 20 grandeurs
(« Wärmezufuhr Lufterwärmer », « Energiebedarf Ventilatoren », « Hilfsenergie
WRG »…) dont **aucune n'a de nom de variable VE établi** :
`ve_adapter/bandes_adapter.py` les déclare toutes `aps_varname: None`. Tant que
ce relevé n'existe pas, l'extraction refuse de tourner — à raison : deviner un
nom produirait un nombre plausible et faux.

Cette sonde liste ce que le fichier contient RÉELLEMENT, à tous les niveaux
utiles. Elle ne lie rien : l'appariement libellé allemand → variable VE se fait
ensuite, à la main, en confrontant le relevé au classeur SIA.

CE QU'ELLE N'EST PAS. Aucune valeur produite ici n'est un résultat de
validation. La sonde lit des noms, des unités et des tailles de séries ; elle
ne juge aucun écart.

EN QUOI ELLE DIFFÈRE DE `Run_VE_SIA4010_APS_Probe.py`, qui existait déjà.
Celle-là filtre les variables sur onze jetons choisis pour les Tests 1 et 2
(`load`, `solar`, `radiation`, `gain`, `window`, `temperature`…) et écrit son
rapport dans le dossier du projet VE. **Aucun de ces jetons ne désigne un
ventilateur, un humidificateur ni une récupération de chaleur** : elle écarte
précisément ce qui manque aux tests 4 à 6. Celle-ci ne filtre rien, interroge
en plus les systèmes Apache, les postes d'énergie et les unités, et écrit sous
`outputs/`. Les deux sont en lecture seule et peuvent coexister.

Elle écrit `outputs/sonde_aps.json`. C'est ce fichier qu'il faut renvoyer.
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
    LIMITE_ELEMENTS, _dans_ve, _membres, _serialisable, dire)

#: Plafond que `_serialisable` applique à toute séquence consignée dans une
#: étape. Il a tronqué le relevé du 2026-08-06 à 500 variables, dont aucune de
#: niveau « z ». Re-exporté pour que les tests puissent viser ce seuil : c'est
#: précisément ce que la liste complète doit contourner.
LIMITE_ELEMENTS_ETAPE = LIMITE_ELEMENTS

CHEMIN_RAPPORT = os.path.join(_RACINE, 'outputs', 'sonde_aps.json')

#: Niveaux de résultat interrogés par `get_variables`. Les libellés SIA des
#: tests 4 à 6 (Lufterwärmer, Luftkühler, WRG, Ventilatoren) désignent des
#: organes de traitement d'air : ils vivent au niveau système, pas au niveau
#: du local. On interroge les trois pour ne rien présumer.
NIVEAUX = (
    ('z', u'local / zone'),
    ('v', u'systeme Apache'),
    ('w', u'meteo'),
)

#: Sous-dossiers de projet VE où cherche-t-on un `.aps`. La liste est indicative
#: et la recherche descend récursivement : on ne suppose pas l'arborescence.
PROFONDEUR_RECHERCHE = 3

#: Au-delà, on cesse d'énumérer : un projet volumineux produirait un rapport
#: illisible sans rien apprendre de plus.
LIMITE_FICHIERS = 40


def trouver_aps(racine_projet):
    u"""Cherche les fichiers `.aps` sous un dossier de projet VE.

    Args:
        racine_projet: Dossier du projet VE.

    Returns:
        list[str]: Chemins trouvés, les plus récents d'abord. Vide si aucun.
    """
    # `VEProject.path` n'est pas garanti etre une chaine : `os.path.isdir(3)`
    # interpreterait un entier comme un descripteur de fichier.
    if not isinstance(racine_projet, str) or not os.path.isdir(racine_projet):
        return []
    trouves = []
    base = racine_projet.rstrip(os.sep)
    for dossier, sous_dossiers, fichiers in os.walk(base):
        profondeur = dossier[len(base):].count(os.sep)
        if profondeur >= PROFONDEUR_RECHERCHE:
            del sous_dossiers[:]
            continue
        for nom in fichiers:
            if nom.lower().endswith('.aps'):
                trouves.append(os.path.join(dossier, nom))
        if len(trouves) >= LIMITE_FICHIERS:
            break
    trouves.sort(key=lambda c: os.path.getmtime(c), reverse=True)
    return trouves[:LIMITE_FICHIERS]


def _resume_serie(serie):
    u"""Décrit une série sans la recopier.

    Une série horaire fait 8760 points : la coucher entière dans le rapport le
    rendrait illisible. Son étendue et ses premières valeurs suffisent à
    reconnaître une grandeur et à repérer une unité aberrante.

    Args:
        serie: Séquence de nombres, ou toute autre chose.

    Returns:
        dict: Résumé, ou description de ce qui a empêché de le faire.
    """
    try:
        valeurs = [v for v in serie if isinstance(v, (int, float))]
    except TypeError:
        return {'non_iterable': repr(serie)[:200]}
    if not valeurs:
        return {'nb_points': 0, 'remarque': u'aucune valeur numerique'}
    return {
        'nb_points': len(valeurs),
        'minimum': min(valeurs),
        'maximum': max(valeurs),
        'somme': sum(valeurs),
        'premieres_valeurs': valeurs[:6],
    }


def sonder(chemin_aps=None):
    u"""Relève le contenu d'un `.aps` : variables, systèmes, postes d'énergie.

    Args:
        chemin_aps: Fichier à ouvrir. Si `None`, cherche dans le projet VE
            courant et prend le plus récent.

    Returns:
        dict: Rapport, écrit aussi sur disque.
    """
    rapport = {
        'dans_ve': _dans_ve(),
        'etapes': [],
        'avertissement': (
            u"Rapport de SONDE. Aucune valeur ici n'est un résultat de "
            u"validation : ce fichier relève des noms de variables, des "
            u"unités et des tailles de séries, rien d'autre."
        ),
    }

    def etape(nom, fonction):
        u"""Exécute une étape en consignant son issue.

        Args:
            nom: Libellé de l'étape.
            fonction: Appelable sans argument.

        Returns:
            Any: Le résultat, ou `None` en cas d'échec.
        """
        try:
            valeur = fonction()
        except Exception as erreur:  # noqa: BLE001 -- on consigne, on ne masque pas
            rapport['etapes'].append({
                'nom': nom, 'statut': 'ECHEC',
                'type_erreur': type(erreur).__name__,
                'erreur': u'%s' % erreur,
            })
            dire(u'  [ECHEC] %-42s %s' % (nom, type(erreur).__name__))
            return None
        rapport['etapes'].append({
            'nom': nom, 'statut': 'OK',
            'type': type(valeur).__name__,
            'valeur': _serialisable(valeur),
        })
        dire(u'  [OK]    %-42s %s' % (nom, repr(valeur)[:48]))
        return valeur

    dire(u'=== SONDE APS : variables de resultats ===')
    if not rapport['dans_ve']:
        dire(u'  hors VEScripts : la sonde ne peut rien apprendre ici.')
        dire(u'  a lancer au bouton Run, depuis une VE ouverte sur un projet')
        dire(u'  dont AU MOINS UNE simulation a deja tourne.')
        return rapport

    import iesve

    # --- Localiser le fichier -------------------------------------------
    if chemin_aps is None:
        projet = etape(u'projet courant',
                       lambda: iesve.VEProject.get_current_project())
        dossier = etape(u'dossier du projet',
                        lambda: getattr(projet, 'path', None))
        candidats = etape(u'fichiers .aps trouves',
                          lambda: trouver_aps(dossier)) or []
        if not candidats:
            etape(u'ouverture du .aps', lambda: _sans_aps())
            _ecrire(rapport)
            return rapport
        chemin_aps = candidats[0]
        dire(u'  -> retenu (le plus recent) : %s' % os.path.basename(chemin_aps))

    lecteur = etape(u'ResultsReader.open',
                    lambda: iesve.ResultsReader.open(chemin_aps))
    if lecteur is None:
        _ecrire(rapport)
        return rapport
    rapport['aps'] = {
        'chemin': chemin_aps,
        'nom': os.path.basename(chemin_aps),
    }

    try:
        _relever(etape, lecteur, rapport)
    finally:
        etape(u'fermeture', lambda: lecteur.close())

    _ecrire(rapport)
    return rapport


def _sans_aps():
    u"""Signale l'absence de fichier de résultats.

    Raises:
        RuntimeError: Toujours. Une étape en échec explicite vaut mieux qu'un
            rapport silencieusement vide.
    """
    raise RuntimeError(
        u'aucun .aps sous le dossier du projet. Lancer une simulation '
        u'ApacheSim dans VE, puis relancer cette sonde.')


def _relever(etape, lecteur, rapport=None):
    u"""Interroge toutes les portes d'entrée utiles du `ResultsReader`.

    Args:
        etape: Fonction d'exécution consignée.
        lecteur: `ResultsReader` ouvert.
        rapport: Rapport où déposer la liste de variables COMPLÈTE, hors du
            plafond appliqué aux étapes.
    """
    # --- Cadre temporel : sans lui, une somme annuelle n'a pas de sens.
    for nom in ('results_per_day', 'first_day', 'last_day', 'year',
                'weather_file', 'hvac_file'):
        etape(u'%s' % nom, lambda n=nom: getattr(lecteur, n))

    # --- Variables : le coeur du releve.
    #
    # TRANCHE PAR L EXECUTION, le 2026-08-06 sur ZOER_C1.aps :
    # `get_variables()` SANS argument repond ; `get_variables('z')` leve
    # ArgumentError. `swiss_sia` avait raison, `bandes_adapter` avait tort.
    # Le niveau se lit sur `model_level`, entree par entree.
    #
    # Les formes a argument restent relevees : si une version de VE les
    # acceptait, le rapport le dirait au lieu de laisser croire au contraire.
    variables = etape(u'get_variables()  [sans argument]',
                      lambda: lecteur.get_variables())
    for niveau, libelle in NIVEAUX:
        etape(u'get_variables(%r)  [%s]' % (niveau, libelle),
              lambda n=niveau: lecteur.get_variables(n))

    # La liste complete est deposee HORS des etapes : le plafond de 500
    # elements y avait tronque le releve du 2026-08-06 a 500 entrees, dont
    # aucune de niveau « z ». Un garde-fou destine a la lisibilite avait ainsi
    # coupe exactement ce que la sonde existe pour rapporter.
    if rapport is not None and variables:
        rapport['variables'] = [_variable_lisible(v) for v in variables]
        rapport['variables_par_niveau'] = _compter_par_niveau(variables)
        dire(u'  -> %d variables, par niveau : %s'
             % (len(variables),
                _en_clair(rapport['variables_par_niveau'])))

    # --- Locaux : les grandeurs de niveau z se lisent par piece.
    etape(u'get_room_list', lambda: lecteur.get_room_list())
    etape(u'get_room_ids', lambda: lecteur.get_room_ids())

    # --- Systemes Apache : c'est la que vivent Luftkuhler, Lufterwarmer et
    # --- WRG, s'ils existent dans le modele.
    systemes = etape(u'get_apache_systems', lambda: lecteur.get_apache_systems())
    if systemes:
        etape(u'get_all_apache_system_results (1er systeme)',
              lambda: _apercu_resultats(
                  lecteur.get_all_apache_system_results(systemes[0])))

    # --- Postes d'energie : piste la plus probable pour « Energiebedarf
    # --- Ventilatoren » et « Befeuchtungsenergie ».
    etape(u'get_energy_uses', lambda: lecteur.get_energy_uses())
    etape(u'get_energy_meters', lambda: lecteur.get_energy_meters())
    etape(u'get_energy_sources', lambda: lecteur.get_energy_sources())

    # --- Composants HVAC, si un reseau ApacheHVAC existe.
    etape(u'get_component_objects', lambda: lecteur.get_component_objects())

    # `get_process_variables()` sans argument leve ArgumentError : il attend un
    # processus, que `get_process_list()` fournit. Constate le 2026-08-06.
    processus = etape(u'get_process_list', lambda: lecteur.get_process_list())
    for nom_processus in list(processus or [])[:6]:
        etape(u'get_process_variables(%r)' % nom_processus,
              lambda p=nom_processus: lecteur.get_process_variables(p))

    # --- Unites : sans elles, on ne sait pas si une serie est en W ou en kW.
    etape(u'get_units', lambda: lecteur.get_units())

    # --- Surface complete, pour comparaison avec ve_api_surface.json.
    etape(u'attributs du ResultsReader', lambda: _membres(lecteur))


#: Champs conservés d'une entrée de `get_variables()`. Tout ce qui sert à
#: reconnaître une grandeur et à convertir son unité, rien de plus.
CHAMPS_VARIABLE = ('aps_varname', 'display_name', 'model_level', 'units_type',
                   'subtype', 'custom_type', 'source')


def _variable_lisible(variable):
    u"""Réduit une entrée de `get_variables()` à ce qui sert.

    Args:
        variable: Entrée telle que renvoyée par l'API.

    Returns:
        dict: Champs retenus, ou le `repr` si la forme est inattendue.
    """
    if not isinstance(variable, dict):
        return {'forme_inattendue': repr(variable)[:200]}
    return dict((champ, variable[champ])
                for champ in CHAMPS_VARIABLE if champ in variable)


def _compter_par_niveau(variables):
    u"""Compte les variables par `model_level`.

    Args:
        variables: Liste d'entrées de `get_variables()`.

    Returns:
        dict: `{niveau: nombre}`, trié par niveau.
    """
    comptes = {}
    for variable in variables:
        niveau = u'%s' % (variable.get('model_level')
                          if isinstance(variable, dict) else u'?')
        comptes[niveau] = comptes.get(niveau, 0) + 1
    return dict(sorted(comptes.items()))


def _en_clair(comptes):
    u"""Met les comptes par niveau sur une ligne de console.

    Args:
        comptes: `{niveau: nombre}`.

    Returns:
        str: Par exemple « e=274, c=184, z=61 ».
    """
    return u', '.join(u'%s=%d' % couple for couple in comptes.items())


def _apercu_resultats(resultats):
    u"""Résume un jeu de résultats sans recopier les séries.

    Args:
        resultats: Ce que renvoie un `get_all_*_results`.

    Returns:
        dict | Any: Résumé par variable, ou la valeur telle quelle si sa forme
            n'est pas reconnue — auquel cas c'est le `repr` qui renseigne.
    """
    if not isinstance(resultats, dict):
        return resultats
    return dict((u'%s' % cle, _resume_serie(serie))
                for cle, serie in list(resultats.items())[:60])


def _ecrire(rapport):
    u"""Écrit le rapport sur disque et dit où le trouver.

    Args:
        rapport: Rapport de sonde.
    """
    dossier = os.path.dirname(CHEMIN_RAPPORT)
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    with io.open(CHEMIN_RAPPORT, 'w', encoding='utf-8') as flux:
        flux.write(json.dumps(rapport, ensure_ascii=False, indent=2))
    dire()
    dire(u'rapport de sonde : %s' % CHEMIN_RAPPORT)
    dire(u'-> me renvoyer ce fichier : il contient les 20 noms de variables '
         u'qui manquent aux tests 2 a 6.')


def main(arguments=()):
    u"""Point d'entrée.

    Args:
        arguments: Chemin d'un `.aps` explicite, facultatif.

    Returns:
        int: 0 si le rapport a pu être écrit, 1 sinon.
    """
    chemins = [a for a in arguments if not a.startswith('--')]
    rapport = sonder(chemins[0] if chemins else None)
    return 0 if rapport.get('etapes') else 1
