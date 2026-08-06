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
NIVEAU_ENERGIE = 'e'    # postes de consommation, tous vecteurs
NIVEAU_SURFACE = 's'    # surface d'enveloppe

#: Niveaux relevés le 2026-08-06 sur `ZOER_C1.aps`, avec leur effectif BRUT —
#: tel que `get_variables()` l'a rendu, doublons compris. Le catalogue figé
#: `refs/reference-data/iesve-aps-variables-ve2025.json` en écarte 11 doublons
#: exacts et compte donc un peu moins (c=178, e=269) : les deux chiffres sont
#: justes, ils ne comptent pas la même chose.
#:
#: Il y a DOUZE niveaux, pas trois : `c` (carbone), `j`, `l`, `n`, `o`, `r` et
#: `t` existent aussi. Aucun code ne doit supposer que les constantes ci-dessus
#: épuisent la liste — c'est en la croyant limitée à z/v/w qu'on a manqué
#: l'éclairage (niveau `e`) et le solaire incident (niveau `s`).
NIVEAUX_RELEVES = {
    'c': 184, 'e': 274, 'j': 15, 'l': 88, 'n': 9, 'o': 6,
    'r': 15, 's': 22, 't': 6, 'v': 35, 'w': 14, 'z': 151,
}


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


# ---------------------------------------------------------------------------
# Candidats issus d'une sonde APS antérieure — À CONFIRMER, jamais employés
# ---------------------------------------------------------------------------
#
# `config/sia4010_aps_bindings_ve_runtime.json` porte cinq liaisons relevées
# le 2026-07-28 sur un `.aps` réel (projet « test », 8760 pas horaires). Elles
# ne sont PAS reprises dans `LIAISONS` : ce sont des noms de variables VE
# relevés pour le Test 1, et rien n'établit qu'ils portent la grandeur que le
# classeur SIA désigne. Confondre les deux, c'est exactement produire un
# nombre plausible et faux.
#
# Deux niveaux de preuve, qu'il ne faut pas mélanger :
#
#   * `room_air_temperature` et `operative_temperature` sont étayés par
#     `references/iesve/probes/sia4010_aps_temperature_binding_evidence.json`,
#     qui contient les séries complètes. Leur authenticité se recoupe : min
#     19,999998 °C / max 27,000002 °C sur le cas 600, soit exactement les
#     consignes 20/27 d'ASHRAE 140. Aucun des deux ne sert aux tests 2 à 6.
#   * les trois autres ne sont adossés qu'à une métadonnée
#     `RUNTIME_METADATA_CONFIRMED`. **Le rapport de sonde d'origine
#     (`sia4010_aps_probe_20260728_154627.json`, sha256 F3E1338C…) est ABSENT
#     du dépôt** : la trace ne peut pas être rejouée. Statut : allégation.
#
# DEPUIS LE RELEVÉ DU 2026-08-06 sur `ZOER_C1.aps` (819 variables, cf.
# `outputs/sonde_aps.json`), la plupart des pistes ci-dessous sont adossées à
# une variable RÉELLEMENT PRÉSENTE dans un `.aps` — nom, niveau, libellé
# d'affichage et famille d'unités vérifiés contre le relevé par un test.
#
# Ce qui reste à établir n'est donc plus « ce nom existe-t-il » mais
# « désigne-t-il la grandeur que le classeur SIA désigne ». Cette seconde
# question ne se tranche pas dans VE : elle exige la définition SIA. C'est
# pourquoi rien n'est lié.
#
#   RELEVE     — la variable existe, confrontée au rapport de sonde.
#   ALLEGATION — annoncée par un fichier de configuration dont la trace
#                d'origine est absente du dépôt.
#
# Table indexée par GRANDEUR, pas par test : « Wärmezufuhr Lufterwärmer »
# figure dans les tests 4, 5 et 6 et y désigne la même chose. Indexer par test
# obligerait à répéter la piste trois fois, donc à la laisser diverger.
CANDIDATS_PAR_GRANDEUR = {
    u'Jahresenergie solarer Wärmeeintrag': {
        'aps_varname_candidat': u'Window solar gains',
        'display_name': u'Solar gain',
        'niveau': NIVEAU_LOCAL,
        'units_type': u'Gain',
        'preuve': u'outputs/sonde_aps.json, variables[model_level=z] ; '
                  u'corrobore config/sia4010_aps_bindings_ve_runtime.json '
                  u'-> bindings.total_room_solar_heat_gain_power',
        'niveau_de_preuve': u'RELEVE',
        'a_confirmer': u'Que « solarer Wärmeeintrag » au sens du classeur SIA '
                       u'désigne le gain solaire transmis par les vitrages au '
                       u'local, et non le rayonnement incident. Le Test 2 '
                       u'distingue les deux : sa seconde grandeur est '
                       u'« total transmittierte Solarstrahlung ».',
    },
    u'Beleuchtungsenergie': {
        'aps_varname_candidat': u'Total lights energy',
        'display_name': u'Total lights energy',
        'niveau': NIVEAU_ENERGIE,
        'units_type': u'Power',
        'preuve': u'outputs/sonde_aps.json, variables[model_level=e]',
        'niveau_de_preuve': u'RELEVE',
        'a_confirmer': u'Que le classeur compte l\'énergie FINALE de '
                       u'l\'éclairage, tous vecteurs confondus. VE expose '
                       u'aussi « Lights electricity » (électricité seule) et, '
                       u'au niveau du local, « Lighting gain » — qui est un '
                       u'APPORT thermique, pas une consommation.',
    },
    u'Wärmezufuhr Lufterwärmer': {
        'aps_varname_candidat': u'Sys Mech vent heating load',
        'display_name': u'System air heating load',
        'niveau': NIVEAU_SYSTEME,
        'units_type': u'Sys Load',
        'preuve': u'outputs/sonde_aps.json, variables[model_level=v]',
        'niveau_de_preuve': u'RELEVE',
        'a_confirmer': u'Que la batterie chaude du classeur corresponde au '
                       u'poste ApacheSystems « System air », et non à un '
                       u'composant d\'un réseau ApacheHVAC.',
    },
    u'Wärmeabfuhr Luftkühler latent': {
        'aps_varname_candidat': u'Sys Mech vent dehum load',
        'display_name': u'System air lat. clg. load',
        'niveau': NIVEAU_SYSTEME,
        'units_type': u'Sys Load',
        'preuve': u'outputs/sonde_aps.json, variables[model_level=v]',
        'niveau_de_preuve': u'RELEVE',
        'a_confirmer': u'Que la charge de déshumidification de VE et la part '
                       u'latente du classeur recouvrent la même grandeur.',
    },
    u'Wärmeabfuhr Luftkühler total': {
        'aps_varname_candidat': None,
        'display_name': None,
        'niveau': NIVEAU_SYSTEME,
        'units_type': u'Sys Load',
        'preuve': u'outputs/sonde_aps.json, variables[model_level=v]',
        'niveau_de_preuve': u'RELEVE — mais AUCUNE variable unique',
        'a_confirmer': u'« total » suppose sensible + latent. VE les sépare en '
                       u'« Sys Mech vent cooling load » (sensible) et '
                       u'« Sys Mech vent dehum load » (latent). Une liaison ne '
                       u'peut donc pas être un simple nom de variable : il '
                       u'faut une SOMME, que LIAISONS ne sait pas exprimer '
                       u'aujourd\'hui.',
    },
    u'Befeuchtungsenergie': {
        'aps_varname_candidat': u'Sys Room humidification load',
        'display_name': u'Room hum. plant load',
        'niveau': NIVEAU_SYSTEME,
        'units_type': u'Sys Load',
        'preuve': u'outputs/sonde_aps.json, variables[model_level=v]',
        'niveau_de_preuve': u'RELEVE',
        'a_confirmer': u'VE porte cette charge au LOCAL (« Room hum. plant '
                       u'load »), pas à la centrale. Si le classeur vise '
                       u'l\'humidification de l\'air neuf, ce n\'est pas la '
                       u'même grandeur. « Ideal humidification » existe au '
                       u'niveau énergie, mais VE le marque [obs].',
    },
}

#: Grandeurs pour lesquelles le relevé du 2026-08-06 n'a montré AUCUNE piste.
#: Les consigner vaut mieux que de laisser croire qu'on n'a pas cherché : le
#: silence se lit comme « pas encore regardé », ce qui serait faux.
SANS_CANDIDAT = {
    u'Jahresenergie total transmittierte Solarstrahlung':
        u'Au niveau surface, VE expose « Total short wave transmittance » (un '
        u'COEFFICIENT, sans unité) et « Ext/Int surface incident solar flux » '
        u'(un rayonnement INCIDENT, pas transmis). Aucune série d\'énergie '
        u'transmise. Constat identique à celui de '
        u'config/sia4010_aps_bindings_ve_runtime.json -> explicitly_unbound, '
        u'atteint ici indépendamment.',
    u'Energiebedarf Ventilatoren':
        u'Aucune variable de ventilateurs SEULS. « ApSys aux energy » agrège '
        u'fans + pumps + ctrls (libellé VE : « Ap Sys fans/pumps/ctrls '
        u'energy ») ; « Fans energy » relève d\'ApacheHVAC et VE le marque '
        u'[obs]. Les postes get_energy_uses() prm_fans_interior_central et '
        u'prm_fans_interior_local sont une piste, mais ce sont des POSTES, pas '
        u'des variables de série.',
    u'Wärmezufuhr WRG':
        u'ApacheSystems n\'expose de la récupération sur l\'air neuf qu\'une '
        u'TEMPÉRATURE (« Sys Mech vent heat recovery temp »). Les deux '
        u'variables de récupération en Power du même niveau — « Sys Process '
        u'heat recovered » et « Sys Process heat recovery heat pump » — '
        u'portent sur les PROCESS, pas sur la ventilation.',
    u'Wärmeabfuhr WRG': u'Même motif que « Wärmezufuhr WRG ».',
    u'Wärmezufuhr WRG latent': u'Même motif que « Wärmezufuhr WRG ».',
    u'Hilfsenergie WRG':
        u'« HR & spray pumps energy » (niveau énergie) est la seule piste, '
        u'mais elle agrège la récupération et les humidificateurs à '
        u'pulvérisation.',
}


def candidats_a_confirmer(numero_test):
    u"""Pistes relevées dans un `.aps` réel, à confirmer contre la norme.

    Ce ne sont PAS des liaisons. `extraire_candidat` les ignore intégralement.
    Elles n'existent que pour qu'un opérateur devant une VE ouverte sache quoi
    contrôler en premier, au lieu de reparcourir 819 variables.

    Args:
        numero_test: Numéro du test SIA.

    Returns:
        dict: `{libellé allemand: piste}` pour les grandeurs de ce test,
            vide si aucune.
    """
    return _projeter(CANDIDATS_PAR_GRANDEUR, numero_test)


def sans_candidat(numero_test):
    u"""Grandeurs de ce test pour lesquelles le relevé n'a montré aucune piste.

    Args:
        numero_test: Numéro du test SIA.

    Returns:
        dict: `{libellé allemand: motif}`, vide si aucune.
    """
    return _projeter(SANS_CANDIDAT, numero_test)


def _projeter(table_par_grandeur, numero_test):
    u"""Restreint une table indexée par grandeur aux grandeurs d'un test.

    Args:
        table_par_grandeur: `{libellé: valeur}`.
        numero_test: Numéro du test SIA.

    Returns:
        dict: Sous-ensemble correspondant aux grandeurs déclarées du test.
    """
    grandeurs = LIAISONS.get(numero_test, {})
    return dict((libelle, valeur)
                for libelle, valeur in table_par_grandeur.items()
                if libelle in grandeurs)


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


#: Champs d'une entrée de `get_variables()` où chercher un motif. `name`
#: n'existe pas : c'était une supposition, corrigée le 2026-08-06.
CHAMPS_NOMMANTS = ('aps_varname', 'display_name')


def decouvrir_variables(results_file, niveau=None, motif=None):
    u"""Liste les variables disponibles dans un `.aps`, pour établir les liaisons.

    C'est l'outil qui remplace la devinette : on lit ce que le fichier
    contient réellement, puis on renseigne `LIAISONS`.

    CORRIGÉ le 2026-08-06, contre une VE réelle (`ZOER_C1.aps`). Cette
    fonction appelait `get_variables(niveau)` ; VE répond `ArgumentError`.
    **`get_variables()` ne prend aucun argument** et rend TOUTES les variables,
    chacune portant son niveau dans `model_level`. Le filtrage est donc fait
    ici, pas par l'API.

    Args:
        results_file: Objet `ResultsReader` déjà ouvert.
        niveau: Niveau à retenir (`'z'` local, `'v'` système, `'w'` météo).
            `None` les rend tous.
        motif: Sous-chaîne filtrante sur le nom, insensible à la casse.

    Returns:
        list[dict]: Variables, telles que l'API les décrit.
    """
    variables = list(results_file.get_variables() or [])
    if niveau is not None:
        variables = [v for v in variables if _niveau_de(v) == niveau]
    if not motif:
        return variables
    cible = motif.lower()
    return [v for v in variables if cible in _nom_de(v).lower()]


def _niveau_de(variable):
    u"""Niveau de modèle porté par une entrée de `get_variables()`.

    Args:
        variable: Entrée de l'API.

    Returns:
        str | None: Valeur de `model_level`, ou `None` si absente.
    """
    if not isinstance(variable, dict):
        return None
    return variable.get('model_level')


def _nom_de(variable):
    u"""Texte où chercher un motif, pour une entrée de `get_variables()`.

    Args:
        variable: Entrée de l'API.

    Returns:
        str: Nom APS et libellé d'affichage concaténés.
    """
    if not isinstance(variable, dict):
        return u'%s' % (variable,)
    return u' '.join(u'%s' % variable.get(champ, u'')
                     for champ in CHAMPS_NOMMANTS)


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
        candidats = candidats_a_confirmer(numero)
        muettes = sans_candidat(numero)
        for libelle in sorted(set(declarees) - set(resolues)):
            lignes.append(u'      non resolue : %s%s'
                          % (libelle, _mention(libelle, candidats, muettes)))
    lignes.append(u'')
    lignes.append(u'Les noms de variables se relevent sur un .aps reel avec '
                  u'decouvrir_variables(), jamais par supposition.')
    lignes.append(u'Un candidat n est PAS une liaison : il indique quoi '
                  u'controler en premier, rien de plus.')
    return u'\n'.join(lignes)


def _mention(libelle, candidats, muettes):
    u"""Complément de ligne décrivant l'état d'une grandeur non résolue.

    Trois états, distincts et à ne pas confondre : une piste existe ; on a
    cherché et rien ne correspond ; on n'a pas encore cherché. Le troisième ne
    doit jamais se lire comme le deuxième.

    Args:
        libelle: Libellé allemand de la grandeur.
        candidats: Pistes du test.
        muettes: Grandeurs du test sans piste, avec leur motif.

    Returns:
        str: Texte à concaténer, éventuellement vide.
    """
    piste = candidats.get(libelle)
    if piste:
        nom = piste['aps_varname_candidat']
        if nom is None:
            return u'  [pas de variable unique -- cf. a_confirmer]'
        return u'  [candidat a confirmer : %s]' % nom
    if libelle in muettes:
        return u'  [cherche, aucune variable ne correspond]'
    return u'  [pas encore cherche]'


# ---------------------------------------------------------------------------
# Second critère : la série horaire, et sa distribution
# ---------------------------------------------------------------------------
#
# Les spécifications des tests 2, 3 et 5 exigent des « Jahresdatensätze in
# stündlicher Auflösung » : le classeur calcule LUI-MÊME la somme annuelle et
# la distribution à partir des 8760 valeurs. Livrer un agrégat ne satisfait
# donc que la moitié des critères.
#
# LES DEUX CRITÈRES NE NOMMENT PAS LES GRANDEURS PAREIL. Le bloc annuel parle
# d'ÉNERGIE (« Jahresenergie solarer Wärmeeintrag », kWh) ; le bloc de
# distribution parle de PUISSANCE (« Solarer Wärmeeintrag gesamt », W). C'est
# la même grandeur physique à deux stades : le classeur somme la puissance
# horaire pour obtenir l'énergie annuelle. La correspondance est donc établie
# ici, explicitement, plutôt que devinée par ressemblance de chaîne.
#
# `None` signale une grandeur de DIAGNOSTIC : elle a une distribution dans le
# classeur mais aucune contrepartie annuelle, et les spécifications la rangent
# sous « Diagnoseresultate » / « Diagnosegrössen ». Ce n'est pas un critère.
CORRESPONDANCE_DISTRIBUTIONS = {
    2: {
        u'Solarer Wärmeeintrag gesamt':
            u'Jahresenergie solarer Wärmeeintrag',
        u'Total transmittierte Solarstrahlung':
            u'Jahresenergie total transmittierte Solarstrahlung',
        u'Einstrahlung auf Fensterebene gesamt': None,
        u'Lamellenwinkel der Storen': None,
    },
    3: {
        u'Beleuchtungsleistung': u'Beleuchtungsenergie',
        u'Beleuchtungsstärke': None,
    },
    5: {
        u'Leistung Lufterwärmer': u'Wärmezufuhr Lufterwärmer',
        u'Leistung Luftkühler total': u'Wärmeabfuhr Luftkühler total',
        u'Leistung Luftkühler latent': u'Wärmeabfuhr Luftkühler latent',
        u'Leistung WRG': u'Wärmezufuhr WRG',
        u'Leistung WRG latent': u'Wärmezufuhr WRG latent',
        u'Leistung Zu- und Abluftventilator': u'Energiebedarf Ventilatoren',
        u'Zu-/Abluft-Volumenstrom': None,
        u'Zulufttemperatur im Betrieb': None,
    },
}

#: Grandeurs annuelles SANS distribution correspondante. Leur seul critère est
#: la somme annuelle — non par oubli du classeur, mais parce qu'il ne porte
#: aucune feuille de distribution pour elles.
SANS_DISTRIBUTION = {
    5: (u'Befeuchtungsenergie', u'Hilfsenergie WRG'),
}


def libelle_annuel(numero_test, grandeur_distribution):
    u"""Grandeur annuelle correspondant à une grandeur de distribution.

    Args:
        numero_test: Numéro du test SIA.
        grandeur_distribution: Libellé tel qu'il figure dans le référentiel de
            distributions.

    Returns:
        str | None: Libellé de `LIAISONS`, ou `None` si la grandeur est un
            diagnostic.

    Raises:
        KeyError: Si la grandeur n'est pas déclarée. Rendre `None` en silence
            la confondrait avec un diagnostic, et ferait disparaître un
            critère sans le dire.
    """
    correspondance = CORRESPONDANCE_DISTRIBUTIONS.get(numero_test, {})
    if grandeur_distribution not in correspondance:
        raise KeyError(
            u'grandeur de distribution non déclarée pour le test %r : %r. '
            u'La déclarer dans CORRESPONDANCE_DISTRIBUTIONS, en diagnostic '
            u'(None) ou en grandeur de LIAISONS.'
            % (numero_test, grandeur_distribution))
    return correspondance[grandeur_distribution]


def extraire_serie(numero_test, results_file, libelle, room_id=None):
    u"""Lit la série horaire BRUTE d'une grandeur, sans l'agréger.

    C'est ce que les spécifications exigent : le classeur veut les 8760
    valeurs et calcule lui-même la somme annuelle et la distribution.

    Args:
        numero_test: Numéro du test SIA.
        results_file: `ResultsReader` ouvert.
        libelle: Libellé allemand de la grandeur, clé de `LIAISONS`.
        room_id: Local, pour une grandeur de niveau local.

    Returns:
        list | None: Série horaire, ou `None` si la lecture échoue.

    Raises:
        LiaisonNonResolue: Si la grandeur n'a pas de nom de variable établi.
            Rendre une série vide se lirait comme « la grandeur vaut zéro ».
    """
    liaison = LIAISONS.get(numero_test, {}).get(libelle)
    if liaison is None:
        raise LiaisonNonResolue(
            u'grandeur inconnue du test %d : %r' % (numero_test, libelle))
    if not liaison.get('aps_varname'):
        raise LiaisonNonResolue(
            u'liaison non résolue pour %r. Les noms de variables se relèvent '
            u'sur un .aps réel avec `decouvrir_variables()`.' % libelle)
    return _lire_serie(results_file, liaison, room_id)


def _lire_serie(results_file, liaison, room_id):
    u"""Lit une série, au niveau local ou global selon la liaison.

    Args:
        results_file: `ResultsReader` ouvert.
        liaison: Entrée de `LIAISONS` résolue.
        room_id: Local, si la grandeur est de niveau local.

    Returns:
        list | None: Série, ou `None` si l'API refuse.
    """
    varname, niveau = liaison['aps_varname'], liaison['niveau']
    try:
        if room_id is not None and niveau == NIVEAU_LOCAL:
            return results_file.get_room_results(room_id, varname, niveau)
        return results_file.get_results(varname, niveau)
    except Exception:  # noqa: BLE001 -- l'absence est un resultat, pas un plantage
        return None
