# -*- coding: utf-8 -*-
u"""Construit un système de ventilation dans VE, d'après la spécification du Test 4.

BUT : RELEVER DES NOMS DE VARIABLES, PAS VALIDER. Ce modèle sert à découvrir
quelles grandeurs VE expose pour une centrale de traitement d'air — batteries
chaude et froide, récupérateur, ventilateurs. C'est le seul moyen de lever les
18 liaisons manquantes des tests SIA 4 à 6.

Il **ne peut pas** être un cas de validation SIA, et trois entrées obligatoires
manquent au dépôt pour cela (cf. `MANQUANTS`). Aucun résultat issu de ce modèle
ne doit être présenté comme un candidat SIA.

CE QUE LA RECONNAISSANCE A ÉTABLI, le 2026-08-07. Les signatures sont
connues : tous les setters de `VEApacheSystem` prennent un **dictionnaire**,
dont les clés sont relevées dans `CLES_DES_SETTERS`.

Et ces clés répondent à une question plus large que la leur. `SFP`, `SEER`,
`SCoP`, `gen_seasonal_eff`, `CHP_ranking`, `meter_cef` : **ApacheSystems est
un modèle de rendements saisonniers**, orienté conformité NCM. Ce n'est pas un
modèle de composants.

Cinq exigences du Test 4 n'y ont donc aucune expression — puissance des
batteries, bypass du récupérateur, protection antigel, consigne de soufflage
régulée, débit variable piloté par le CO2 (cf.
`INEXPRIMABLE_EN_APACHESYSTEMS`). `construire()` refuse pour cette raison, qui
est un résultat et non un report.

CONSÉQUENCE POUR LE PROJET. Les tests 4, 5 et 6 exigent un réseau
**ApacheHVAC**. Or `HVACNetwork` n'expose que `components`, `systems`,
`controllers`, `get_component_by_id`, `load_network` et `path` — aucune
méthode de création. Le réseau doit être construit **à la main** dans VE, une
fois, puis son fichier `.asp` versionné et rechargé par `load_network`.

UN PIÈGE DE L'API, relevé au passage. `set_heating()` appelé **sans argument**
ne lève pas : il rend `None`. Un appel fautif ne se signale donc pas. Toute
configuration écrite ici devra être **relue** après écriture, comme le fait
déjà `test1_adapter` pour les matériaux.
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

CHEMIN_RAPPORT = os.path.join(_RACINE, 'outputs', 'reconnaissance_test4.json')

_SPEC = u'Spezifikation_Test4.pdf'

#: Paramètres de la centrale, TOUS lus dans la spécification du Test 4. Chaque
#: entrée porte sa source ; aucune n'est arrondie, complétée ni convertie.
PARAMETRES = {
    u'debit_nominal_m3_h': {'valeur': 1700.0, 'source': _SPEC + u', Volumenstrom'},
    u'debit_variable_pourcent': {'valeur': (20.0, 100.0),
                                 'source': _SPEC + u', Variabel von bis'},
    u'perte_de_charge_soufflage_pa': {'valeur': 500.0,
                                      'source': _SPEC + u', Nenn-Druckverlust'},
    u'perte_de_charge_reprise_pa': {'valeur': 400.0,
                                    'source': _SPEC + u', Nenn-Druckverlust'},
    u'puissance_ventilateur_soufflage_w': {
        'valeur': 407.0, 'source': _SPEC + u', Ventilatoren / Nennleistung'},
    u'puissance_ventilateur_reprise_w': {
        'valeur': 331.0, 'source': _SPEC + u', Ventilatoren / Nennleistung'},
    u'recuperateur_taux': {
        'valeur': 0.75,
        'source': _SPEC + u', Wärmerückgewinnungsgerät / Nominale '
                          u'Temperaturänderungszahl'},
    u'recuperateur_type': {
        'valeur': u'échangeur à plaques SANS échange d\'humidité',
        'source': _SPEC + u', Wärmerückgewinnungsgerät / Beschreibung'},
    u'batterie_froide_kw': {'valeur': 12.8,
                            'source': _SPEC + u', Luftkühler / Auslegung'},
    u'batterie_chaude_kw': {'valeur': 11.4,
                            'source': _SPEC + u', Lufterhitzer / Auslegung'},
    u'temperature_soufflage_refroidissement_c': {
        'valeur': (16.0, 22.5), 'source': _SPEC + u', Zulufttemperatur'},
    u'temperature_soufflage_chauffage_c': {
        'valeur': (22.5, 29.0), 'source': _SPEC + u', Zulufttemperatur'},
    u'horaire_fonctionnement': {
        'valeur': u'jours ouvrés 05:00-20:00 ; arrêt en juillet',
        'source': _SPEC + u', Regelung / Betriebszeit'},
    u'surface_nette_m2': {'valeur': 165.8, 'source': _SPEC + u', Nettofläche'},
    u'infiltration_m3_h_m2': {'valeur': 0.15, 'source': _SPEC + u', Infiltration'},
    u'occupants': {'valeur': 55, 'source': _SPEC + u', Personen / Anzahl'},
    u'apport_equipements_w_m2': {'valeur': 10.0,
                                 'source': _SPEC + u', Geräte'},
    u'apport_eclairage_w_m2': {'valeur': 6.4,
                               'source': _SPEC + u', Beleuchtung'},
    u'co2_ppm': {'valeur': (600.0, 1000.0),
                 'source': _SPEC + u', Sollwerte / CO2'},
    u'co2_exterieur_ppm': {'valeur': 400.0,
                           'source': _SPEC + u', Sollwerte / CO2'},
}

#: Entrées obligatoires pour un CAS DE VALIDATION, absentes du dépôt. Elles
#: n'empêchent pas de relever des noms de variables ; elles interdisent de
#: présenter un résultat comme un candidat SIA.
MANQUANTS = {
    u'climat': u'SIA 2028 DRY normal, Zürich Kloten — fichier non disponible. '
               u'Le relevé de variables fonctionne avec un autre climat ; le '
               u'résultat chiffré, non.',
    u'constructions': u'FprSIA 380/2:2022, tableau 3 « Grenzwert » — valeurs '
                      u'non extraites du PDF.',
    u'usage': u'Standardnutzung « Hörsaal » selon SIA 2024:2021, Zielwerte — '
              u'fiches d\'utilisation non disponibles (téléchargement libre, '
              u'action utilisateur).',
}

#: Méthodes de `VEApacheSystem` dont la signature doit être relevée avant de
#: pouvoir appliquer les paramètres.
SETTERS_A_RELEVER = (
    'set_air_supply', 'set_auxiliary_energy', 'set_control', 'set_cooling',
    'set_heating', 'set_name', 'set_ventilation_ncm',
)

#: Propriétés à relever telles qu'elles sortent d'un système neuf : elles
#: montrent les structures que les setters attendent en retour.
PROPRIETES_A_RELEVER = (
    'air_supply', 'auxiliary_energy', 'control', 'cooling', 'heating',
    'hot_water', 'id', 'name', 'ventilation_ncm',
)


class ConstructionRefusee(RuntimeError):
    u"""Levée quand la construction ne peut pas se faire sans supposer."""


def reconnaitre():
    u"""Crée un système ApacheSystems et relève ce que son API attend.

    Ne configure RIEN : le système créé reste aux valeurs par défaut de VE.
    C'est un relevé, pas une construction.

    Returns:
        dict: Rapport, écrit aussi sur disque.
    """
    rapport = {
        'dans_ve': _dans_ve(),
        'but': u'Relever la signature des setters de VEApacheSystem avant de '
               u'leur appliquer les valeurs de la spécification du Test 4.',
        'avertissement':
            u'Aucune valeur de ce rapport n\'est un résultat de validation. Le '
            u'système créé ici est un objet de RECONNAISSANCE : il porte les '
            u'valeurs par défaut de VE, pas celles de la norme.',
        'parametres_de_la_spec': dict(
            (cle, {'valeur': _serialisable(entree['valeur']),
                   'source': entree['source']})
            for cle, entree in PARAMETRES.items()),
        'manquants_pour_une_validation': MANQUANTS,
        'etapes': [],
    }

    def etape(nom, fonction):
        u"""Exécute une étape en consignant son issue.

        Args:
            nom: Libellé de l'étape.
            fonction: Appelable sans argument.

        Returns:
            Any: Résultat, ou `None` en cas d'échec.
        """
        try:
            valeur = fonction()
        except Exception as erreur:  # noqa: BLE001 -- on consigne, on ne masque pas
            rapport['etapes'].append({
                'nom': nom, 'statut': 'ECHEC',
                'type_erreur': type(erreur).__name__,
                'erreur': u'%s' % erreur,
            })
            dire(u'  [ECHEC] %-40s %s' % (nom, type(erreur).__name__))
            return None
        rapport['etapes'].append({
            'nom': nom, 'statut': 'OK', 'type': type(valeur).__name__,
            'valeur': _serialisable(valeur),
        })
        dire(u'  [OK]    %-40s %s' % (nom, repr(valeur)[:44]))
        return valeur

    dire(u'=== RECONNAISSANCE : systeme de ventilation, Test 4 ===')
    dire(u'  but : relever ce que l API attend, pas construire un cas SIA.')
    if not rapport['dans_ve']:
        dire(u'  hors VEScripts : rien a apprendre ici.')
        return rapport

    import iesve

    projet = etape(u'projet courant',
                   lambda: iesve.VEProject.get_current_project())
    etape(u'systemes existants', lambda: projet.apache_systems)

    systeme = etape(u'create_apache_system',
                    lambda: projet.create_apache_system())
    if systeme is None:
        _ecrire(rapport)
        return rapport

    etape(u'attributs du systeme', lambda: _membres(systeme))

    # CORRIGE le 2026-08-07. `heating`, `cooling`, `air_supply`... sont des
    # METHODES, pas des attributs : le premier releve n a capture que des
    # `<bound method ...>` et n a donc jamais obtenu les dictionnaires par
    # defaut. Ce sont eux qui montrent les types attendus par les setters.
    for nom in PROPRIETES_A_RELEVER:
        etape(u'%s() (valeur par defaut)' % nom,
              lambda n=nom: _appeler_si_possible(getattr(systeme, n)))

    for nom in SETTERS_A_RELEVER:
        etape(u'%s (signature)' % nom,
              lambda n=nom: _signature(getattr(systeme, n)))

    _ecrire(rapport)
    return rapport


def _appeler_si_possible(valeur):
    u"""Rend la valeur, ou le résultat de son appel si c'est une méthode.

    `VEApacheSystem` expose `heating`, `cooling`, `air_supply`… en méthodes et
    non en attributs. Les relever sans les appeler ne donne qu'un
    `<bound method …>` — c'est l'erreur du premier relevé.

    Args:
        valeur: Attribut relevé sur l'objet.

    Returns:
        Any: Le résultat de l'appel, ou la valeur telle quelle.
    """
    if not callable(valeur):
        return valeur
    return valeur()


def _signature(methode):
    u"""Décrit une méthode : docstring et signature si elle en expose une.

    Args:
        methode: Méthode liée.

    Returns:
        dict: Ce qui a pu être relevé.
    """
    import inspect
    releve = {'doc': (getattr(methode, '__doc__', None) or u'')[:400]}
    try:
        releve['signature'] = u'%s' % (inspect.signature(methode),)
    except (TypeError, ValueError) as erreur:
        # Les methodes natives n exposent souvent pas de signature : c est le
        # cas normal, pas une anomalie.
        releve['signature'] = u'non exposee (%s)' % type(erreur).__name__
    return releve


#: Clés que chaque setter accepte, RELEVÉES dans leur docstring le
#: 2026-08-07. Elles disent ce qu'ApacheSystems est : un modèle de RENDEMENTS
#: saisonniers, orienté conformité NCM.
CLES_DES_SETTERS = {
    'set_heating': ('fuel', 'gen_seasonal_eff', 'SCoP', 'gen_size',
                    'HR_effectiveness', 'HR_return_temp', 'used_with_CHP',
                    'CHP_ranking', 'CHP_heat_output', 'is_heat_pump',
                    'meter_cef', 'meter_pef'),
    'set_cooling': ('cool_vent_mechanism', 'has_absorption_chiller', 'fuel',
                    'SEER', 'del_eff', 'SSEER', 'gen_size',
                    'pump_and_fan_power_perc', 'nominal_eer', 'free_cooling'),
    'set_air_supply': ('condition', 'profile', 'OA_max_flow',
                       'temperature_difference', 'cooling_max_flow'),
    'set_auxiliary_energy': ('method', 'SFP', 'AEV', 'off_schedule_AEV',
                             'fan_fraction', 'air_supply_mechanism'),
    'set_ventilation_ncm': ('air_supply_mechanism', 'heat_recovery_type',
                            'heat_recovery_efficiency_known',
                            'heat_recovery_efficiency',
                            'variable_heat_recovery'),
}

#: Exigences de la spécification du Test 4 qu'AUCUNE clé ci-dessus ne permet
#: d'exprimer. C'est la raison pour laquelle ApacheSystems ne convient pas.
INEXPRIMABLE_EN_APACHESYSTEMS = {
    u'puissance des batteries':
        u'Luftkühler 12,8 kW et Lufterhitzer 11,4 kW. `gen_size` dimensionne '
        u'le GÉNÉRATEUR, pas la batterie de traitement d\'air.',
    u'bypass du récupérateur':
        u'« Mit Bypass auf Zulufttemperatur-Sollwert, Kühlfall 100 % Bypass ». '
        u'`heat_recovery_efficiency` est un rendement constant : il n\'a pas '
        u'de régulation.',
    u'protection antigel':
        u'« Regelung mit Bypass auf Fortlufttemperatur ≥ 0 °C ». Aucune clé.',
    u'consigne de température de soufflage':
        u'16–22,5 °C en refroidissement, 22,5–29 °C en chauffage, régulateur '
        u'PI. `temperature_difference` est un écart fixe, pas une consigne '
        u'régulée.',
    u'régulation CO2 du débit variable':
        u'20–100 % du débit nominal, pilotés par la concentration en CO2. '
        u'Aucune clé.',
}


def construire(projet=None):
    u"""Applique les paramètres de la spécification à un système.

    Args:
        projet: `VEProject`, ou `None` pour le projet courant.

    Raises:
        ConstructionRefusee: Toujours. La raison a CHANGÉ le 2026-08-07, et
            c'est un résultat, pas un report.

            Les signatures sont désormais connues : tous les setters prennent
            un dictionnaire, dont les clés sont relevées dans
            `CLES_DES_SETTERS`. Ces clés montrent qu'ApacheSystems est un
            modèle de **rendements saisonniers** orienté conformité NCM — SFP,
            SEER, SCoP, rendement de génération — et non un modèle de
            composants.

            Cinq exigences de la spécification du Test 4 n'y ont aucune
            expression (cf. `INEXPRIMABLE_EN_APACHESYSTEMS`). Construire quand
            même produirait un système qui simule, qui donne des nombres, et
            qui ne représente pas le test — le pire des trois cas.
    """
    raise ConstructionRefusee(
        u'construction refusée : ApacheSystems ne peut pas représenter le '
        u'Test 4. Les %d setters sont désormais connus (ils prennent des '
        u'dictionnaires, clés relevées dans CLES_DES_SETTERS), mais aucune de '
        u'leurs clés n\'exprime : %s. ApacheSystems modélise des RENDEMENTS '
        u'saisonniers (SFP, SEER, SCoP), pas des composants. Le Test 4 exige '
        u'un réseau ApacheHVAC, qui doit être construit à la main dans VE puis '
        u'chargé par `HVACNetwork.load_network` depuis un `.asp`.'
        % (len(CLES_DES_SETTERS),
           u', '.join(sorted(INEXPRIMABLE_EN_APACHESYSTEMS))))


def _ecrire(rapport):
    u"""Écrit le rapport et dit où le trouver.

    Args:
        rapport: Rapport de reconnaissance.
    """
    dossier = os.path.dirname(CHEMIN_RAPPORT)
    if not os.path.isdir(dossier):
        os.makedirs(dossier)
    with io.open(CHEMIN_RAPPORT, 'w', encoding='utf-8') as flux:
        flux.write(json.dumps(rapport, ensure_ascii=False, indent=2))
    dire()
    dire(u'rapport : %s' % CHEMIN_RAPPORT)
    dire(u'-> me renvoyer ce fichier : il contient les signatures qui '
         u'manquent pour appliquer les valeurs de la specification.')


def main(arguments=()):
    u"""Point d'entrée.

    Args:
        arguments: `--construire` pour tenter la construction.

    Returns:
        int: 0 si le rapport a pu être écrit, 1 sinon.
    """
    if '--construire' in arguments:
        try:
            construire()
        except ConstructionRefusee as erreur:
            dire(u'REFUS : %s' % erreur)
            return 1
    rapport = reconnaitre()
    return 0 if rapport.get('etapes') else 1
