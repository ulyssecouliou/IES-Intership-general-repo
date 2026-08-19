# -*- coding: utf-8 -*-
u"""Generates the ApacheHVAC network data entry sheet for Test 4.

WHY A SHEET, AND NOT A SCRIPT. `HVACNetwork` exposes only
`components`, `systems`, `controllers`, `get_component_by_id`, `load_network`
and `path`: **no creation method**. The network therefore cannot be built by
script — it must be built manually, once, in the ApacheHVAC editor in VE.
Only then can the `.asp` be versioned and reloaded via `load_network`, and
everything else becomes scriptable again.

WHY GENERATED, AND NOT HAND-WRITTEN. The values come from
`construire_test4_dans_ve.PARAMETRES` and from
`refs/reference-data/test-4.consignes.json`, both traced to the
specification. A manually retyped sheet would drift from the source on
the first change, and a wrong sheet would lead to building a wrong
network — with much more work to discover the error.

Usage:
    python scripts/build_fiche_apachehvac.py [--ecrire]
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

from scripts import construire_test4_dans_ve as source  # noqa: E402

_SORTIE = os.path.join(_RACINE, 'docs', 'FICHE-APACHEHVAC-TEST4.md')
_CONSIGNES = os.path.join(_RACINE, 'refs', 'reference-data',
                          'test-4.consignes.json')

#: Components to place, in airflow order. Each entry names the corresponding
#: `iesve` class — found in `ve_api_surface.json` — so that the network survey,
#: after the fact, can be compared against this sheet.
COMPOSANTS = [
    (u'Prise d\'air neuf', 'HVACInlet',
     [u'Air extérieur, appareil en toiture (« Geräteaufstellung: auf dem '
      u'Dach, Aussenklima »).']),
    (u'Récupérateur de chaleur', 'HVACAirToAirHeatEnthalpyExchanger',
     ['recuperateur_type', 'recuperateur_taux',
      u'Bypass régulé sur la consigne de température de soufflage ; '
      u'100 % de bypass en refroidissement.',
      u'Protection antigel : bypass sur température d\'air rejeté ≥ 0 °C.']),
    (u'Ventilateur de soufflage', 'HVACFan',
     ['puissance_ventilateur_soufflage_w', 'perte_de_charge_soufflage_pa',
      u'Placé APRÈS le récupérateur ; moteur dans le flux d\'air.',
      u'Vitesse nominale 2 790 min⁻¹.']),
    (u'Batterie chaude', 'HVACHeatingCoil',
     ['batterie_chaude_kw',
      u'Air entrant +8 °C, sortant 29 °C.',
      u'Eau chaude : entrée 31 °C, départ constant 40 °C.']),
    (u'Batterie froide', 'HVACCoolingCoil',
     ['batterie_froide_kw',
      u'Rendement d\'échange 0,85 ; facteur de bypass 0,065.',
      u'Air entrant 29,5 °C / 22 °C humide / 14,2 g·kg⁻¹ / 52 % HR, '
      u'sortant 16 °C.',
      u'Eau glacée : entrée 13 °C, départ constant 13 °C.']),
    (u'Ventilateur de reprise', 'HVACFan',
     ['puissance_ventilateur_reprise_w', 'perte_de_charge_reprise_pa',
      u'Placé APRÈS le récupérateur ; moteur dans le flux d\'air.',
      u'Vitesse nominale 2 730 min⁻¹.']),
    (u'Régulateur de température de soufflage', 'HVACControllerWithSensor',
     ['temperature_soufflage_refroidissement_c',
      'temperature_soufflage_chauffage_c',
      u'Régulateur PI, asservi à la consigne de température du local.']),
    (u'Régulateur de débit sur CO2', 'HVACControllerWithSensor',
     ['debit_nominal_m3_h', 'debit_variable_pourcent', 'co2_ppm',
      'co2_exterieur_ppm',
      u'Variateur de fréquence agissant directement sur le ventilateur.']),
    (u'Zone desservie', 'HVACZone',
     ['surface_nette_m2', 'occupants', 'apport_equipements_w_m2',
      'apport_eclairage_w_m2', 'infiltration_m3_h_m2',
      u'Local « Hörsaal », sans fenêtre, sur deux niveaux, toiture sur '
      u'extérieur.']),
]

#: Settings that do not relate to any particular component.
REGLAGES_GENERAUX = ['horaire_fonctionnement']

RESERVES = [
    u'Cette fiche décrit le Test 4. Les tests 5 et 6 ajoutent une '
    u'humidification (contact puis vapeur) et d\'autres variantes de '
    u'récupération : leur réseau devra être saisi séparément, depuis leurs '
    u'propres spécifications.',
    u'Le nom de classe `iesve` en regard de chaque composant sert à '
    u'CONFRONTER le réseau saisi à cette fiche, après coup, par '
    u'`HVACNetwork.components`. Ce n\'est pas un nom d\'objet à saisir dans '
    u'l\'éditeur.',
    u'Trois entrées manquent pour que ce modèle soit un cas de validation SIA '
    u'— climat SIA 2028 Kloten, constructions SIA 380/2 tableau 3, fiches '
    u'd\'usage SIA 2024. Le réseau, lui, peut être saisi sans elles : il sert '
    u'd\'abord à relever les noms de variables.',
]


def _consignes():
    u"""Loads the frozen temperature setpoint.

    Returns:
        dict | None: Reference data, or `None` if it has not been frozen.
    """
    if not os.path.exists(_CONSIGNES):
        return None
    with io.open(_CONSIGNES, encoding='utf-8') as flux:
        return json.load(flux)


def _ligne_de_parametre(cle):
    u"""Returns a table row for a parameter from the specification.

    Args:
        cle: Key in `PARAMETRES`, or free text.

    Returns:
        str: Markdown row.
    """
    entree = source.PARAMETRES.get(cle)
    if entree is None:
        # Free text: an entry instruction with no numeric value of its own.
        return u'| — | %s | %s |' % (cle, u'Spezifikation_Test4.pdf')
    valeur = entree['valeur']
    if isinstance(valeur, (tuple, list)):
        texte = u' – '.join(u'%s' % v for v in valeur)
    else:
        texte = u'%s' % valeur
    return u'| `%s` | **%s** | %s |' % (cle, texte, entree['source'])


def construire():
    u"""Writes the data entry sheet.

    Returns:
        str: Markdown document.
    """
    lignes = [
        u'# Fiche de saisie — réseau ApacheHVAC du Test SIA 4010 n° 4',
        u'',
        u'> **Document généré** par `scripts/build_fiche_apachehvac.py`. Les '
        u'valeurs viennent de `construire_test4_dans_ve.PARAMETRES` et de '
        u'`refs/reference-data/test-4.consignes.json`, tous deux tracés à la '
        u'spécification officielle. Ne pas les modifier ici : corriger la '
        u'source et régénérer.',
        u'',
        u'## Pourquoi cette saisie est manuelle',
        u'',
        u'`HVACNetwork` n\'expose que `components`, `systems`, `controllers`, '
        u'`get_component_by_id`, `load_network` et `path` — **aucune méthode '
        u'de création**. Le réseau ne peut pas être construit par script.',
        u'',
        u'Une fois saisi et enregistré, le fichier `.asp` se versionne dans le '
        u'dépôt et se recharge par `HVACNetwork.load_network`. **La saisie '
        u'n\'est à faire qu\'une fois** ; tout ce qui suit — affectation, '
        u'simulation, extraction, verdict — est scriptable.',
        u'',
        u'C\'est aussi ce qui débloquera le Test 7, dont le réseau est dans le '
        u'même cas.',
        u'',
        u'## Ce que ce réseau sert à établir',
        u'',
        u'Les 18 liaisons manquantes des tests SIA 4 à 6. ApacheSystems ne '
        u'peut pas les porter : ses paramètres sont des rendements saisonniers '
        u'(`SFP`, `SEER`, `SCoP`), et cinq exigences du Test 4 n\'y ont aucune '
        u'expression — puissance des batteries, bypass du récupérateur, '
        u'protection antigel, consigne de soufflage régulée, débit piloté par '
        u'le CO2.',
        u'',
        u'---',
        u'',
        u'## Composants, dans l\'ordre du flux d\'air',
        u'',
    ]

    for numero, (nom, classe, entrees) in enumerate(COMPOSANTS, 1):
        lignes.append(u'### %d. %s' % (numero, nom))
        lignes.append(u'')
        lignes.append(u'*Classe `iesve` attendue au relevé : `%s`*' % classe)
        lignes.append(u'')
        lignes.append(u'| Paramètre | Valeur | Source |')
        lignes.append(u'|---|---|---|')
        for entree in entrees:
            lignes.append(_ligne_de_parametre(entree))
        lignes.append(u'')

    lignes.append(u'## Réglages généraux')
    lignes.append(u'')
    lignes.append(u'| Paramètre | Valeur | Source |')
    lignes.append(u'|---|---|---|')
    for cle in REGLAGES_GENERAUX:
        lignes.append(_ligne_de_parametre(cle))
    lignes.append(u'')

    consignes = _consignes()
    if consignes:
        lignes.append(u'## Consigne de température du local')
        lignes.append(u'')
        lignes.append(u'**Attention : consigne GLISSANTE.** Elle dépend de la '
                      u'%s. Elle n\'est pas écrite dans la spécification — '
                      u'elle y est **dessinée**, et la cellule correspondante '
                      u'est vide dans la couche texte du PDF.'
                      % consignes['abscisse'])
        lignes.append(u'')
        lignes.append(u'| Rôle | Palier bas | Point 1 | Point 2 | Palier haut |')
        lignes.append(u'|---|---|---|---|---|')
        for role in sorted(consignes['consignes']):
            points = consignes['consignes'][role]['points']
            lignes.append(
                u'| %s | %.1f °C | %.1f °C ext → %.1f °C | %.1f °C ext → '
                u'%.1f °C | %.1f °C |'
                % (role, points[0][1], points[0][0], points[0][1],
                   points[1][0], points[1][1], points[1][1]))
        lignes.append(u'')
        for reserve in consignes['reserves']:
            lignes.append(u'> %s' % reserve)
            lignes.append(u'>')
        lignes.append(u'')

    lignes.append(u'## Après la saisie')
    lignes.append(u'')
    lignes.append(u'1. Enregistrer le réseau ; noter le chemin du `.asp`.')
    lignes.append(u'2. Lancer une simulation ApacheSim sur **l\'année '
                  u'complète** — un `.aps` partiel rend toute somme annuelle '
                  u'inexploitable.')
    lignes.append(u'3. Lancer `Run_VE_SIA4010_Sonde_APS.py` et renvoyer '
                  u'`outputs/sonde_aps.json`.')
    lignes.append(u'4. Le relevé donnera les noms de variables des batteries, '
                  u'du récupérateur et des ventilateurs — les 18 liaisons '
                  u'manquantes.')
    lignes.append(u'')
    lignes.append(u'## Réserves')
    lignes.append(u'')
    for reserve in RESERVES:
        lignes.append(u'- %s' % reserve)
    lignes.append(u'')
    return u'\n'.join(lignes) + u'\n'


def main(arguments=()):
    u"""Entry point.

    Args:
        arguments: `--ecrire` to write the file.

    Returns:
        int: 0.
    """
    document = construire()
    print(u'fiche : %d composants, %d lignes'
          % (len(COMPOSANTS), document.count(u'\n')))
    if '--ecrire' in arguments:
        dossier = os.path.dirname(_SORTIE)
        if not os.path.isdir(dossier):
            os.makedirs(dossier)
        with io.open(_SORTIE, 'w', encoding='utf-8') as flux:
            flux.write(document)
        print(u'écrit : %s' % os.path.relpath(_SORTIE, _RACINE))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
