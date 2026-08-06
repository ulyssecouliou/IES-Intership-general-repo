# -*- coding: utf-8 -*-
u"""Adaptateur IESVE des tests SIA 4010 à bandes — tests 2 à 6.

Un seul module pour cinq tests : leurs références partagent la forme
« grandeur → cas » (cf. `engine/sia_bandes_engine.py`), et leur extraction
partage la même mécanique — ouvrir le `.aps`, lire une série, l'agréger,
assembler le candidat.

CE QUI EST VÉRIFIÉ, ET COMMENT. Les symboles `iesve` utilisés ici sont
présents dans `ve_adapter/ve_api_surface.json`, une introspection d'une
VE 2025 réellement installée (309 symboles, Python 3.12.3). `verifier_api()`
le contrôle à l'exécution et échoue bruyamment si un symbole a disparu — ce
qui est déjà arrivé : `element_categories` avait été cherché sur
`VECdbProject` alors qu'il appartient au MODULE `iesve`, et la sonde du
Test 1 l'a révélé.

CE QUI N'EST PAS VÉRIFIABLE ICI, ET N'EST DONC PAS DEVINÉ. Les
**`aps_varname`** — les noms de variables de résultat — ne sont pas des
symboles de l'API : ce sont des données de runtime, propres au modèle simulé.
Aucun ne peut être établi depuis le poste de développement. Les liaisons de
`LIAISONS` sont donc déclarées **non résolues**, et l'adaptateur REFUSE de
produire une valeur pour une liaison non résolue plutôt que d'en inventer une.

    Marche à suivre, dans VE :
        1. `decouvrir_variables(results_file)` liste ce que le `.aps` contient.
        2. On y relève le nom exact correspondant à chaque grandeur du SIA.
        3. On le déclare dans `LIAISONS`, avec sa source.
        4. `extraire_candidat()` devient alors exploitable.

Python pur au chargement : `iesve` n'est importé qu'à l'appel, de sorte que
ce module reste importable en intégration continue, sans licence VE.
"""

from __future__ import print_function

import io
import json
import os

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))

#: Introspection d'une VE 2025 réellement installée. Sert de garde-fou : on
#: n'écrit pas contre la documentation, on écrit contre ce qui existe.
CHEMIN_SURFACE_API = os.path.join(_ICI, 've_api_surface.json')

#: Méthodes de `ResultsReader` que cet adaptateur emploie. Toutes présentes
#: dans la surface relevée ; `verifier_api()` le confirme à l'exécution.
METHODES_REQUISES = (
    'close',
    'get_all_room_results',
    'get_all_weather_results',
    'get_room_results',
    'get_results',
    'get_variables',
)

TESTS_COUVERTS = (2, 3, 4, 5, 6)

#: Niveaux de résultat de l'API, tels que nommés par `get_variables`.
NIVEAU_LOCAL = 'z'      # room / zone
NIVEAU_SYSTEME = 'v'    # apache system
NIVEAU_METEO = 'w'      # weather


class LiaisonNonResolue(RuntimeError):
    u"""Levée quand une grandeur n'a pas de nom de variable établi.

    Volontairement une erreur : produire `None` en silence laisserait croire
    que la grandeur a été cherchée et n'existe pas, alors qu'elle n'a jamais
    été cherchée.
    """


class ApiIncompatible(RuntimeError):
    u"""Levée quand l'API `iesve` ne présente pas les symboles attendus."""


# ---------------------------------------------------------------------------
# Liaisons grandeur -> variable de résultat
# ---------------------------------------------------------------------------
#
# `None` signifie NON RÉSOLU, pas « absent ». Chaque entrée porte le libellé
# EXACT du classeur SIA, qui sert de clé d'appariement avec la référence
# figée : il est en allemand et doit le rester, sinon l'appariement casse.
#
# Le champ `piste` dit où chercher dans le `.aps`. C'est une indication de
# recherche, PAS une valeur : il ne doit jamais être utilisé comme nom de
# variable.
# Genere depuis les references figees par un script, JAMAIS retape a la
# main : les libelles allemands sont les cles d appariement, et une
# espace de trop suffit a rendre une liaison introuvable une fois resolue.
LIAISONS = {
    2: {
        u'Jahresenergie solarer Wärmeeintrag': {
            'aps_varname': None, 'niveau': NIVEAU_LOCAL,
            'agregation': 'somme_annuelle',
            'piste': u'apport solaire et rayonnement transmis, au niveau du local',
        },
        u'Jahresenergie total transmittierte Solarstrahlung': {
            'aps_varname': None, 'niveau': NIVEAU_LOCAL,
            'agregation': 'somme_annuelle',
            'piste': u'apport solaire et rayonnement transmis, au niveau du local',
        },
    },
    3: {
        u'Beleuchtungsenergie': {
            'aps_varname': None, 'niveau': NIVEAU_LOCAL,
            'agregation': 'somme_annuelle',
            'piste': u"puissance d'eclairage du local",
        },
    },
    4: {
        u'Energiebedarf Ventilatoren': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'centrale de traitement d air du Hoersaal',
        },
        u'Wärmeabfuhr Luftkühler total': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'centrale de traitement d air du Hoersaal',
        },
        u'Wärmezufuhr Lufterwärmer': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'centrale de traitement d air du Hoersaal',
        },
    },
    5: {
        u'Befeuchtungsenergie': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation du batiment exemple',
        },
        u'Energiebedarf Ventilatoren': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation du batiment exemple',
        },
        u'Hilfsenergie WRG': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation du batiment exemple',
        },
        u'Wärmeabfuhr Luftkühler latent': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation du batiment exemple',
        },
        u'Wärmeabfuhr Luftkühler total': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation du batiment exemple',
        },
        u'Wärmezufuhr Lufterwärmer': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation du batiment exemple',
        },
        u'Wärmezufuhr WRG': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation du batiment exemple',
        },
        u'Wärmezufuhr WRG latent': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation du batiment exemple',
        },
    },
    6: {
        u'Energiebedarf Ventilatoren': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation, restaurant et cuisine',
        },
        u'Hilfsenergie WRG': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation, restaurant et cuisine',
        },
        u'Wärmeabfuhr Luftkühler total': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation, restaurant et cuisine',
        },
        u'Wärmeabfuhr WRG': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation, restaurant et cuisine',
        },
        u'Wärmezufuhr Lufterwärmer': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation, restaurant et cuisine',
        },
        u'Wärmezufuhr WRG': {
            'aps_varname': None, 'niveau': NIVEAU_SYSTEME,
            'agregation': 'somme_annuelle',
            'piste': u'systeme de ventilation, restaurant et cuisine',
        },
    },
}


def verifier_api(symboles=None):
    u"""Contrôle que l'API `iesve` présente les symboles employés ici.

    Args:
        symboles: Surface d'API déjà chargée ; sinon lue sur disque.

    Returns:
        dict: `{methode: True}` pour chaque méthode requise et présente.

    Raises:
        ApiIncompatible: Si la surface est illisible ou s'il manque une
            méthode. Mieux vaut échouer au chargement qu'au milieu d'une
            extraction, sur un modèle ouvert.
    """
    if symboles is None:
        if not os.path.isfile(CHEMIN_SURFACE_API):
            raise ApiIncompatible(
                u'surface d\'API introuvable : %s. La régénérer avec '
                u've_adapter/Run_VE_Probe_API_Surface.py depuis VE.'
                % CHEMIN_SURFACE_API)
        with io.open(CHEMIN_SURFACE_API, encoding='utf-8') as flux:
            symboles = json.load(flux).get('symbols', {})

    lecteur = symboles.get('ResultsReader') or {}
    membres = set(lecteur.get('members') or ())
    manquantes = [m for m in METHODES_REQUISES if m not in membres]
    if manquantes:
        raise ApiIncompatible(
            u'ResultsReader ne présente pas : %s. L\'API a changé depuis la '
            u'surface relevée ; relancer la sonde avant d\'aller plus loin.'
            % u', '.join(manquantes))
    return dict((m, True) for m in METHODES_REQUISES)


def decouvrir_variables(results_file, niveau=NIVEAU_LOCAL, motif=None):
    u"""Liste les variables disponibles dans un `.aps`, pour établir les liaisons.

    C'est l'outil qui remplace la devinette : on lit ce que le fichier
    contient réellement, puis on renseigne `LIAISONS`.

    Args:
        results_file: Objet `ResultsReader` déjà ouvert.
        niveau: Niveau de résultat, `'z'` local, `'v'` système, `'w'` météo.
        motif: Sous-chaîne filtrante, insensible à la casse.

    Returns:
        list[dict]: Variables, telles que l'API les décrit.
    """
    variables = results_file.get_variables(niveau) or []
    if not motif:
        return list(variables)
    cible = motif.lower()
    retenues = []
    for variable in variables:
        texte = u'%s' % (variable if not isinstance(variable, dict)
                         else variable.get('name', variable))
        if cible in texte.lower():
            retenues.append(variable)
    return retenues


def agreger(serie, methode):
    u"""Agrège une série horaire selon la méthode demandée.

    Args:
        serie: Valeurs horaires.
        methode: `'somme_annuelle'`, `'moyenne'`, `'maximum'` ou `'minimum'`.

    Returns:
        float | None: Valeur agrégée, `None` si la série est vide.

    Raises:
        ValueError: Si la méthode est inconnue -- jamais un repli silencieux
            sur la somme, qui donnerait un nombre plausible et faux.
    """
    valeurs = [float(v) for v in (serie or []) if v is not None]
    if not valeurs:
        return None
    if methode == 'somme_annuelle':
        # Les puissances de VE sont en W au pas horaire : la somme des W sur
        # 8760 h vaut des Wh, que le SIA attend en kWh.
        return sum(valeurs) / 1000.0
    if methode == 'moyenne':
        return sum(valeurs) / len(valeurs)
    if methode == 'maximum':
        return max(valeurs)
    if methode == 'minimum':
        return min(valeurs)
    raise ValueError(u'méthode d\'agrégation inconnue : %r' % (methode,))


def liaisons_resolues(numero_test):
    u"""Grandeurs dont le nom de variable est établi.

    Args:
        numero_test: Numéro du test SIA.

    Returns:
        dict: Sous-ensemble de `LIAISONS[numero_test]`.
    """
    return dict((libelle, liaison)
                for libelle, liaison in LIAISONS.get(numero_test, {}).items()
                if liaison.get('aps_varname'))


def liaisons_manquantes(numero_test, reference=None):
    u"""Grandeurs du test dont la liaison reste à établir.

    Args:
        numero_test: Numéro du test SIA.
        reference: Référentiel figé, pour confronter la liste des grandeurs à
            celle des liaisons. Sans lui, seules les liaisons déclarées sont
            examinées.

    Returns:
        list[str]: Libellés non résolus, triés.
    """
    declarees = LIAISONS.get(numero_test, {})
    attendues = set(declarees)
    if reference is not None:
        attendues |= set(g['libelle_de'] for g in reference['grandeurs'])
    return sorted(libelle for libelle in attendues
                  if not declarees.get(libelle, {}).get('aps_varname'))


def extraire_candidat(numero_test, results_file, reference,
                      resolveur_local=None):
    u"""Assemble le candidat d'un test, au format attendu par le moteur.

    Args:
        numero_test: Numéro du test SIA, entre 2 et 6.
        results_file: `ResultsReader` ouvert sur le `.aps` du cas.
        reference: Référentiel figé du test.
        resolveur_local: Appelable `(cas) -> room_id`, quand le test porte sur
            plusieurs locaux. `None` si un seul local est concerné.

    Returns:
        dict: `{libellé grandeur: {cas: valeur}}`, ne contenant QUE les
        grandeurs dont la liaison est résolue et la lecture réussie.

    Raises:
        ValueError: Si le test n'est pas couvert par cet adaptateur.
        LiaisonNonResolue: Si AUCUNE liaison n'est résolue -- retourner un
            candidat vide se lirait comme « rien ne passe », alors que rien
            n'a été cherché.
    """
    if numero_test not in TESTS_COUVERTS:
        raise ValueError(
            u'test %r hors de portée ; couverts : %s'
            % (numero_test, list(TESTS_COUVERTS)))

    resolues = liaisons_resolues(numero_test)
    if not resolues:
        raise LiaisonNonResolue(
            u'aucune liaison résolue pour le test %d. Les noms de variables '
            u'ne sont pas des symboles de l\'API : ils se relèvent sur un '
            u'.aps réel avec `decouvrir_variables()`, puis se déclarent dans '
            u'`LIAISONS`. Grandeurs concernées : %s'
            % (numero_test, u', '.join(liaisons_manquantes(numero_test, reference))))

    candidat = {}
    for grandeur in reference['grandeurs']:
        libelle = grandeur['libelle_de']
        liaison = resolues.get(libelle)
        if liaison is None:
            continue
        par_cas = {}
        for cas in grandeur['cas']:
            valeur = _lire_un_cas(results_file, liaison, cas, resolveur_local)
            if valeur is not None:
                par_cas[cas['cas']] = valeur
        if par_cas:
            candidat[libelle] = par_cas
    return candidat


def _lire_un_cas(results_file, liaison, cas, resolveur_local):
    u"""Lit et agrège la série d'un cas.

    Args:
        results_file: `ResultsReader` ouvert.
        liaison: Entrée de `LIAISONS`.
        cas: Entrée de cas du référentiel.
        resolveur_local: Appelable `(cas) -> room_id`, ou `None`.

    Returns:
        float | None: Valeur agrégée, `None` si la série est absente.
    """
    room_id = resolveur_local(cas) if resolveur_local else None
    try:
        if room_id is None:
            serie = results_file.get_results(
                liaison['aps_varname'], liaison.get('niveau', NIVEAU_LOCAL))
        else:
            serie = results_file.get_room_results(
                room_id, liaison['aps_varname'],
                liaison.get('niveau', NIVEAU_LOCAL))
    except Exception:  # noqa: BLE001 -- une série absente n'est pas un plantage
        return None
    return agreger(serie, liaison.get('agregation', 'somme_annuelle'))


def etat_des_liaisons():
    u"""Résumé de ce qui est prêt et de ce qui ne l'est pas.

    Returns:
        str: Tableau texte, lisible dans la console de VEScripts.
    """
    lignes = [u'Liaisons grandeur -> variable de resultat', u'']
    for numero in TESTS_COUVERTS:
        declarees = LIAISONS.get(numero, {})
        resolues = liaisons_resolues(numero)
        lignes.append(u'  Test %d : %d/%d resolue(s)'
                      % (numero, len(resolues), len(declarees)))
        for libelle in sorted(set(declarees) - set(resolues)):
            lignes.append(u'      non resolue : %s' % libelle)
    lignes.append(u'')
    lignes.append(u'Les noms de variables se relevent sur un .aps reel avec '
                  u'decouvrir_variables(), jamais par supposition.')
    return u'\n'.join(lignes)
