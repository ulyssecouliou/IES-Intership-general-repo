# -*- coding: utf-8 -*-
"""Adaptateur VE -- SIA 4010 Test n° 7 (classe de validation 5).

Ce module est le seul endroit du dépôt (avec `test1_adapter.py`) qui importe
`iesve`. Il traduit entre l'API VE (VEScripts) et le JSON normalisé attendu
par `engine/test7_engine.py::evaluer_test7()` : un dict
`{libellé_de: valeur_annuelle_kWh}`. Le moteur ne doit jamais savoir que VE
existe (CLAUDE.md, « séparation dur/pur ») ; cet adaptateur ne doit jamais
inventer de valeur, de tolérance ou de symbole d'API non vérifié
(CLAUDE.md, règle n° 1).

--------------------------------------------------------------------------
CE QUE LE TEST 7 EXIGE, ET CE QU'IL N'EXIGE PAS (Spezifikation_Test7.pdf,
Schema.pdf, lus intégralement -- traceability/classes-de-validation.spec.md
§2.1 arrive indépendamment à la même conclusion) :
--------------------------------------------------------------------------
  - AUCUN modèle thermique de bâtiment, AUCUNE géométrie, AUCUN vitrage.
    Les profils de charge (froid, chaud, ECS) sont FOURNIS par le SIA dans
    `Lastverläufe_220607.xlsx` (feuille `Gruppen`, 8760 h). Ce fichier vit
    hors de ce dépôt (chemin externe `SIA_4010_geteilter_Link/Test7/`) ; sa
    structure est documentée mais son contenu n'est PAS vendorisé ni parsé
    ici -- voir la section « CE QUI N'EST PAS FAIT » plus bas, point 1.
  - Climat : SIA 2028 DRY normal, Zürich Kloten, période 1.1.2022-31.12.2022
    (Spezifikation_Test7.pdf p.1) -- **année différente du Test 1** (2011).
    La SEULE variable climatique qui intervient est la température d'air
    extérieur horaire (elle fixe le point de fonctionnement du
    refroidisseur sec / échangeur sur air extérieur, Spezifikation_Test7.pdf
    p.4 : « Temperaturdifferenz Aussenluft - Vorlauftemperatur 4 K bei
    Volllast »). Cette série est une source officielle déjà figée :
    `refs/reference-data/sia-2028-kloten-temperature.csv` (8760 h, colonne
    `theta_e_air_c` -- traceability/classes-de-validation.spec.md §3.0).
  - Production : PAC eau-eau réversible Climaveneta NX-W-Y/H 0182,
    2 ballons de stockage de 2000 l, distribution forfaitaire (5 % pertes,
    2 % auxiliaires), refroidisseur sec 70 kW / échangeur sur air extérieur
    76 kW, circuit eau-glycol 30 % à 19'000 kg/h -- toutes ces valeurs sont
    reprises ci-dessous EN CONSTANTES, sourcées, pour documentation et pour
    un futur montage manuel du réseau (cf. juste en dessous : leur montage
    automatique n'est PAS possible avec l'API documentée).
  - PV : toiture 150 modules (18x7 + 6x4) à 310 W = 45 kWp déclarés,
    inclinaison 10°, orientation est/ouest ; façade sud 52 modules (13x4) à
    310 W = 15.6 kWp déclarés ; onduleur 97 %. La grandeur « PV-Ertrag »
    EXIGE l'irradiance sur le plan de CES modules précis -- absente de
    toute source officielle en notre possession (idem
    traceability/classes-de-validation.spec.md §3.1). Ce module renvoie
    TOUJOURS `None` pour cette grandeur -- jamais une estimation. Voir la
    section PV plus bas : ce refus est **délibéré**, pas un manque de savoir-
    faire API.

--------------------------------------------------------------------------
CE QUI EST VÉRIFIÉ (chaque symbole `iesve` cité ci-dessous a été lu dans
`refs/VEScripts-API-VE2023.pdf`, section indiquée -- extraction texte
`pdftotext -layout`, relue intégralement) :
--------------------------------------------------------------------------
  - `iesve.ResultsReader.open(filename)`                                §6.1.14.2
  - `ResultsReader.get_variables()` -> liste de dicts `{aps_varname,
    display_name, model_level, units_type}`                            §6.1.14.2
  - `ResultsReader.get_units()` -> dict indexé par `units_type`, chaque
    entrée portant `units_metric.display_name` (exemple d'usage donné
    littéralement dans le PDF)                                          §6.1.14.2
  - `ResultsReader.get_hvac_component_results(component_id, component_type,
    var_name, start_day=-1, end_day=-1)` -- niveau de modèle `h` = « HVAC
    component level » (tableau des niveaux, §6.1.14.1)                  §6.1.14.2
  - `ResultsReader.results_per_day` (attribut)                          §6.1.14.3
  - `iesve.VELocate()` ; `.open_wea_data()` / `.set(dict)` (clé
    `weather_file`) / `.save_and_close()` -- même mécanisme, déjà vérifié
    et utilisé par `test1_adapter.py::assigner_meteo_drycold`           §6.1.36
  - Existence de la classe `HVACComponentTypes` (énumération) et de ses
    membres `awhp`, `aahp`, `wahp`, `hot_water_loop`, `chilled_water_loop`,
    `thermal_storage_tank`, `pump`, `heat_transfer_loop`, `junction`,
    `room`, `boiler`, `chiller`, `cooling_tower`, `fan`, `damper` -- lus
    dans le bloc « Enums Defined Here » qui ouvre §6.1.7 « HVAC Network ».
    ⚠ Ce bloc est un tableau à deux colonnes fusionné par l'extraction
    texte (même symptôme que `material_categories` dans
    `test1_adapter.py` : plusieurs énumérations sans rapport
    apparaissent entrelacées). Aucun de ces noms de membre n'est donc codé
    en dur comme identifiant "le" bon composant : voir plus bas pourquoi
    ce module n'a PAS besoin de trancher lui-même cette ambiguïté.
  - `HVACNetwork` (classe), méthode statique `load_network(nom) ->
    HVACNetwork`, attribut `components` (liste de `HVACComponent`)       §6.1.7.5
  - `HVACAbstractComponent.aps_component_type` (attribut, type
    `HVACComponentTypes`) -- **un composant DÉJÀ obtenu** (via
    `HVACNetwork.components` ou `get_component_by_id`) porte donc sa
    propre valeur de `component_type` déjà résolue ; il n'est jamais
    nécessaire de deviner l'orthographe d'un membre d'énum pour l'obtenir.
    §6.1.7 (bloc `HVACAbstractComponent`, juste après les énums ci-dessus)
  - Table « component types currently available » de
    `get_hvac_component_results` (liste numérotée 1-54 associant un entier
    à une classe `iesve.HVAC...`)                                        §6.1.14.2
    ⚠ Cette table est ELLE AUSSI un fusionnement à deux colonnes visible
    (ex. les entrées 30 et 31 portent toutes deux « iesve.HVACHeatPump »,
    ce qui est suspect) : elle n'est PAS utilisée ici pour deviner un code
    numérique. Voir la section suivante.

--------------------------------------------------------------------------
CE QUI N'EST PAS FAIT ICI, ET POURQUOI -- marqué `# ⚠ À VÉRIFIER API` dans
le code, jamais comblé par supposition :
--------------------------------------------------------------------------
  1. **Construction du réseau ApacheHVAC (PAC, 2 ballons, refroidisseur sec,
     échangeur air extérieur, pompes, régulation de charge) -- NON FOURNIE
     ICI, et volontairement.** `refs/VEScripts-API-VE2023.pdf` documente,
     pour `HVACNetwork`/`HVACComponent`/`HVACPrototypeSystem`, uniquement
     des méthodes de LECTURE (`load_network`, `get_component_by_id`,
     `components`, `get_node_data`, `get_peak_data`, ...) -- recherche
     explicite de `add_component|create_component|insert_component|
     new_network|create_network|macro` dans l'extraction texte complète :
     **zéro occurrence**. Aucune méthode de CRÉATION de composant ou de
     réseau macro-flow n'est documentée. Fabriquer malgré tout un appel
     `iesve.HVACSomething().create(...)` serait inventer un symbole --
     interdit par la règle n° 1. **Conséquence directe et importante** : le
     système du Test 7 (Schema.pdf) doit être monté UNE FOIS, à la main,
     dans l'éditeur ApacheHVAC d'une VE réelle, avant que ce module puisse
     lire quoi que ce soit. Ce point est renvoyé à `ve-adapter-engineer`
     (prochaine session avec VE réel) -- il n'est PAS résolu ici, exactement
     comme `test1_adapter.py` avait renvoyé la création de géométrie/pièces.
  2. **Lecture des profils de charge SIA (`Lastverläufe_220607.xlsx`) --
     NON PARSÉE ICI.** Sa structure est documentée (feuille `Gruppen` :
     8760 h x 11 colonnes de puissance en W ; feuille `Grundlagen` : détail
     par test/local -- traceability/classes-de-validation.spec.md §2.2).
     Tant que le réseau ApacheHVAC ne peut pas être construit par ce
     module (point 1), écrire un parseur pour alimenter des `VEProfile`
     qui ne seraient de toute façon reliés à rien serait du code mort et
     non vérifiable. Reporté au même point d'extension que le point 1.
  3. **Résolution du membre exact de `HVACComponentTypes` pour « pompe à
     chaleur eau-eau réversible ».** Les membres visibles dans le tableau
     documenté sont `awhp` (air-water), `aahp` (air-air), `wahp`
     (water-air/exhaust-air ?) -- AUCUN nommé explicitement pour une PAC
     EAU-EAU. `ve_adapter/ve_api_surface.json` (sonde d'introspection d'une
     VE 2025 RÉELLEMENT installée, 2026-07-31 -- **PAS un document
     `/refs`**, utilisé ici uniquement en corroboration, jamais comme seule
     justification d'un symbole) confirme l'EXISTENCE d'une classe
     `iesve.HVACWaterWaterHeatPump`, mais ce nom n'apparaît dans AUCUNE
     énumération documentée de `HVACComponentTypes`. **Ce module contourne
     le problème plutôt que de le deviner** : il exige que l'appelant lui
     fournisse un `component_type` DÉJÀ résolu (typiquement lu directement
     sur `HVACComponent.aps_component_type` d'un composant obtenu depuis
     une VE réelle -- §6.1.7 ci-dessus), jamais un nom de membre à
     interpréter ici.
  4. **Noms exacts des variables APS** (`aps_varname`) pour chaque
     grandeur du Test 7. Comme pour le Test 1 (`test1_adapter.py`, point 4
     de sa propre docstring), le PDF renvoie systématiquement à un « units
     spreadsheet »/« variables list » séparé, absent de `/refs`. **Aucun
     dépôt externe consulté ne porte de liaisons probées pour le Test 7**
     (contrairement au Test 1, où un fichier de configuration externe
     existait) : ce module ne fournit donc AUCUNE liaison candidate, pas
     même une "non confirmée" -- l'appelant doit les découvrir lui-même
     (aide fournie : `decouvrir_variables_hvac()`, lecture seule, jamais
     invoquée automatiquement) et les fournir explicitement via le
     paramètre `plan_extraction`.
  5. **`PV-Ertrag` -- refus délibéré, pas une lacune API.** `EnergyUse.
     prm_elec_gen_pv` (§6.1.14.4) EST un symbole documenté et utilisable
     avec `get_energy_results()`/`get_energy_results_ex()` ; la classe
     `VERenewables` apparaît dans le diagramme de classes du guide (aucune
     section textuelle, aucune méthode documentée -- recherche `VERenewables`
     dans l'extraction complète : zéro occurrence hors diagramme). Même si
     l'un ou l'autre produisait un nombre, ce nombre serait dérivé de
     l'irradiance du fichier météo assigné à la simulation -- PAS d'une
     source officielle vérifiée pour les plans de modules exacts déclarés
     (toit 10° est/ouest, façade sud verticale). L'utiliser reviendrait à
     blanchir une donnée non vérifiable en résultat validé. **Ce module ne
     contient donc AUCUN chemin de code touchant PV/VERenewables/
     `prm_elec_gen_pv`** : `PV-Ertrag` est absent de toute sortie produite
     ici, par construction, jamais `None` déguisé en zéro ni en moyenne.

Écrit en style prudent (pas de f-string, pas de dataclass) par cohérence
avec `test1_adapter.py`, bien que la sonde runtime (`probe_runtime_resultat.txt`,
VE 2025 réel) ait établi Python 3.12 -- aucune contrainte de compatibilité
n'est donc *nécessaire*, ce choix reste seulement sans coût.
"""

import calendar
import csv
import io
import json
import os


# --------------------------------------------------------------------------
# Constantes normatives -- toutes sourcées sur `Spezifikation_Test7.pdf`
# (4 pages, lues intégralement) et `Schema.pdf`. Aucune n'est utilisée pour
# construire quoi que ce soit dans VE (cf. docstring, point « CE QUI N'EST
# PAS FAIT », n° 1) : elles documentent le système que quelqu'un devra
# monter à la main, et servent de garde-fous d'auto-cohérence ci-dessous.
# --------------------------------------------------------------------------

# Spezifikation_Test7.pdf p.1 : "Simulationsperiode 1.1.2022 bis 31.12.2022".
# Différent du Test 1 (2011) -- ne PAS réutiliser ANNEE_SIMULATION de
# test1_adapter.py par erreur.
ANNEE_SIMULATION = 2022
assert not calendar.isleap(ANNEE_SIMULATION)  # garde-fou : 8760 h supposées.
HEURES_PAR_AN = 365 * 24

CLIMAT = {
    'jeu': 'SIA 2028 DRY normal',
    'station': u'Zürich Kloten',
    'periode': '1.1.2022-31.12.2022',
}

# Spezifikation_Test7.pdf p.2 : "Climaveneta NX-W-Y /H 0182, Wasser-Wasser-
# Wärmepumpe, reversibel, Scrollverdichter, 2-stufig".
CLIMAVENETA_NX_W_Y_H_0182 = {
    'type': u'PAC eau-eau, réversible, compresseurs scroll, 2 étages '
            u'(Wasser-Wasser-Wärmepumpe, reversibel, Scrollverdichter, '
            u'2-stufig)',
    'puissance_nominale_froid_kw': 55.9,
    'puissance_nominale_chaud_kw': 60.0,
    # Champs de caractéristiques EN 14825 (tableau 5 / tableau 12,
    # Spezifikation_Test7.pdf p.2-4) : conditions d'essai à charge
    # partielle. Non reproduits en détail ici -- ce module ne construit
    # pas la PAC dans VE (docstring, point 1) ; seules les puissances
    # nominales servent de garde-fou de cohérence documentaire.
}

# Spezifikation_Test7.pdf p.1, blocs "Kälteverteilung" / "Wärmeverteilung".
DISTRIBUTION_FROID = {
    'pertes_pct_de_la_chaleur_absorbee': 5.0,   # "5% der aufgenommenen Wärme"
    'auxiliaire_pct_de_la_chaleur_absorbee': 2.0,  # "2% der aufgenommenen Wärme"
    'auxiliaire_recupere_comme_charge_thermique_pct': 50.0,
}
DISTRIBUTION_CHAUD = {
    'pertes_pct_de_la_chaleur_delivree': 5.0,   # "5% der abgegebenen Wärme"
    'auxiliaire_pct_de_la_chaleur_delivree': 2.0,  # "2% der abgegebenen Wärme"
    'auxiliaire_recupere_dans_circuit_chauffage_pct': 50.0,
}

# Spezifikation_Test7.pdf p.1, "Kältespeicherung"/"Wärmespeicherung" :
# "Technischer Speicher zur Vermeidung kurzer Laufzeiten, Volumen 2'000 l".
STOCKAGE_FROID_LITRES = 2000
STOCKAGE_CHAUD_LITRES = 2000

# Spezifikation_Test7.pdf p.4, bloc "Aussenluftgerät".
AEROREFROIDISSEUR_SEC_KW = 70.0          # "Luftgekühlter Trockenrückkühler"
ECHANGEUR_AIR_EXTERIEUR_KW = 76.0        # "Aussenluft-Wärmeübertrager"
VENTILATEUR_PUISSANCE_SPECIFIQUE_KW_PAR_KW = 0.045  # "Antriebsleistung Ventilator"

# Spezifikation_Test7.pdf p.4, bloc "Rückkühl-/Aussenluftkreis". Le "?" du
# taux de glycol est repris VERBATIM de la source -- c'est le SIA lui-même
# qui laisse ce point incertain dans sa spécification, pas une omission de
# ce module.
CIRCUIT_GLYCOL = {
    'fluide': u"Wasser-Glykol-Gemisch 30%?",  # "?" présent dans la source SIA
    'massflow_kg_par_h': 19000.0,
    'spread_k': 4.0,                          # "Temperaturspreizung"
    'delta_t_air_fluide_pleine_charge_k': 4.0,  # "bei Volllast"
    'pompe_puissance_utile_dans_circuit_pct': 50.0,  # "Pumpenabwärme ... wärmewirksam"
    'pertes_pct': 5.0,
}

# Spezifikation_Test7.pdf p.4, bloc "Bivalenz" : chaudière d'appoint sous la
# température de bivalence.
BIVALENCE = {
    'vecteur_energetique': 'gaz',
    'rendement': 0.9,
}

# Spezifikation_Test7.pdf p.4, bloc "Eigenerzeugung" / "Photovoltaik".
# ⚠ RÉSERVE NON RÉSOLUE (voir `verifier_coherence_puissance_pv()` plus
# bas) : 150 x 310 W = 46.5 kWc et 52 x 310 W = 16.12 kWc, alors que la
# source annonce 45 kWc et 15.6 kWc -- 150 x 300 W = 45 kWc et
# 52 x 300 W = 15.6 kWc concordent EXACTEMENT. La puissance unitaire par
# module lue ("310 W") est donc probablement une confusion d'extraction
# avec le nom du modèle ("AEG AS-M605-310") plutôt que la vraie puissance
# ("300 W" ?). Non tranché sans relecture visuelle de la page 4 du PDF
# source. SANS INCIDENCE FONCTIONNELLE ICI : `PV-Ertrag` n'est de toute
# façon jamais calculé par ce module (cf. docstring, point 5).
PV_SYSTEME = {
    'toit_modules': 150,               # 18 x 7 + 6 x 4
    'toit_w_par_module_lu': 310.0,     # tel qu'extrait -- réserve ci-dessus
    'toit_kwp_declare': 45.0,
    'toit_inclinaison_deg': 10.0,
    'toit_orientation': 'est/ouest',
    'facade_modules': 52,              # 13 x 4, façade sud
    'facade_w_par_module_lu': 310.0,   # tel qu'extrait -- réserve ci-dessus
    'facade_kwp_declare': 15.6,
    'facade_orientation': 'sud',
    'onduleur_rendement': 0.97,
    'modele_module': 'AEG AS-M605-310',
}


def verifier_coherence_puissance_pv():
    u"""Documente (sans lever) l'écart arithmétique trouvé dans la source.

    N'affecte AUCUN calcul : `PV-Ertrag` n'est jamais produit par ce module,
    quelle que soit l'issue de ce contrôle. Sert uniquement à garder la
    réserve visible et testée plutôt que silencieuse.
    """
    toit_a_310 = PV_SYSTEME['toit_modules'] * PV_SYSTEME['toit_w_par_module_lu'] / 1000.0
    toit_a_300 = PV_SYSTEME['toit_modules'] * 300.0 / 1000.0
    facade_a_310 = PV_SYSTEME['facade_modules'] * PV_SYSTEME['facade_w_par_module_lu'] / 1000.0
    facade_a_300 = PV_SYSTEME['facade_modules'] * 300.0 / 1000.0
    return {
        'toit_kwp_declare': PV_SYSTEME['toit_kwp_declare'],
        'toit_kwp_calcule_a_310w': toit_a_310,
        'toit_coherent_a_310w': abs(toit_a_310 - PV_SYSTEME['toit_kwp_declare']) < 1e-6,
        'toit_kwp_calcule_a_300w': toit_a_300,
        'toit_coherent_a_300w': abs(toit_a_300 - PV_SYSTEME['toit_kwp_declare']) < 1e-6,
        'facade_kwp_declare': PV_SYSTEME['facade_kwp_declare'],
        'facade_kwp_calcule_a_310w': facade_a_310,
        'facade_coherent_a_310w': abs(facade_a_310 - PV_SYSTEME['facade_kwp_declare']) < 1e-6,
        'facade_kwp_calcule_a_300w': facade_a_300,
        'facade_coherent_a_300w': abs(facade_a_300 - PV_SYSTEME['facade_kwp_declare']) < 1e-6,
    }


# --------------------------------------------------------------------------
# Les 11 grandeurs du Test 7 -- libellés VERBATIM (allemand), identiques à
# `refs/reference-data/test-7.ref.json`. Un test dédié vérifie cette
# concordance mot pour mot : c'est la clé d'appariement d'
# `engine/test7_engine.py::evaluer_test7`, une faute de frappe ici rendrait
# une grandeur silencieusement NOT_CHECKABLE.
# --------------------------------------------------------------------------

LIBELLE_PV_ERTRAG = u'PV-Ertrag'

GRANDEURS_TEST7 = (
    {
        'libelle_de': u'Zugeführte elektrische Energie Kältemaschine',
        'unite': 'kWh',
        'role_systeme': u"Énergie électrique reçue par la production de "
                        u"froid (PAC en mode froid).",
    },
    {
        'libelle_de': u'Total abgeführte Wärme',
        'unite': 'kWh',
        'role_systeme': u"Chaleur totale évacuée côté froid (à répartir "
                        u"entre récupération chaude et rejet au "
                        u"refroidisseur sec -- cf. les deux grandeurs "
                        u"suivantes).",
    },
    {
        'libelle_de': u'Hilfsenergie Kälteerzeugung',
        'unite': 'kWh',
        'role_systeme': u"Énergie auxiliaire de la production de froid "
                        u"(2 % de la chaleur absorbée, DISTRIBUTION_FROID).",
    },
    {
        'libelle_de': u'Aus Kälteerzeugung an die Wärmeseite gelieferte W.',
        'unite': 'kWh',
        'role_systeme': u"Chaleur récupérée côté condenseur et livrée au "
                        u"circuit chaud (charge du ballon chaud) en cas de "
                        u"besoin simultané -- Schema.pdf, bloc "
                        u"« Wärmerückgewinnung ». Plancher à zéro dans le "
                        u"classeur de référence : ne peut pas être négative.",
    },
    {
        'libelle_de': u'Über Rückkühler abgeführte Wärme',
        'unite': 'kWh',
        'role_systeme': u"Chaleur rejetée via le refroidisseur sec "
                        u"(AEROREFROIDISSEUR_SEC_KW) -- le reliquat non "
                        u"récupéré côté chaud.",
    },
    {
        'libelle_de': u'Zugeführte elektrische Energie Wärmepumpe',
        'unite': 'kWh',
        'role_systeme': u"Énergie électrique reçue par la production de "
                        u"chaleur (PAC en mode chaud).",
    },
    {
        'libelle_de': u'Zugeführte Wärme der Wärmeerzeugung, Heizen',
        'unite': 'kWh',
        'role_systeme': u"Chaleur livrée par la production de chaleur pour "
                        u"le chauffage des locaux.",
    },
    {
        'libelle_de': u'Zugeführte Wärme der Wärmeerzeugung, Warmwasser',
        'unite': 'kWh',
        'role_systeme': u"Chaleur livrée par la production de chaleur pour "
                        u"l'eau chaude sanitaire (charge du ballon ECS à "
                        u"60 °C, Spezifikation_Test7.pdf p.1).",
    },
    {
        'libelle_de': u'Energie Heizkessel',
        'unite': 'kWh',
        'role_systeme': u"Énergie de la chaudière d'appoint (gaz, "
                        u"rendement 0.9, BIVALENCE), active sous la "
                        u"température de bivalence. Plancher à zéro dans "
                        u"le classeur de référence.",
    },
    {
        'libelle_de': u'Hilfsenergie Wärmeerzeugung',
        'unite': 'kWh',
        'role_systeme': u"Énergie auxiliaire de la production de chaleur "
                        u"(2 % de la chaleur délivrée, DISTRIBUTION_CHAUD).",
    },
    {
        'libelle_de': LIBELLE_PV_ERTRAG,
        'unite': 'kWh',
        'role_systeme': u"Production électrique photovoltaïque -- JAMAIS "
                        u"calculée ici. Cf. docstring de module, point 5.",
    },
)

_LIBELLES_CONNUS = frozenset(g['libelle_de'] for g in GRANDEURS_TEST7)
_LIBELLES_VERIFIABLES_SANS_IRRADIANCE = frozenset(
    g['libelle_de'] for g in GRANDEURS_TEST7 if g['libelle_de'] != LIBELLE_PV_ERTRAG)


# --------------------------------------------------------------------------
# Température d'air extérieur de Kloten -- source officielle déjà figée
# (refs/reference-data/sia-2028-kloten-temperature.csv). Lecture pure
# Python (module `csv` standard), aucune dépendance à `iesve` : ce n'est
# PAS un résultat de simulation, c'est une DONNÉE D'ENTRÉE dont la seule
# utilité ici est (a) le futur assignage météo (`assigner_meteo_kloten`)
# et (b) un contrôle croisé contre ce que VE aura effectivement simulé
# (`verifier_temperature_exterieure_simulee`), pour attraper un mauvais
# fichier météo assigné avant de faire confiance à quoi que ce soit d'autre.
# --------------------------------------------------------------------------

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir))
CHEMIN_TEMPERATURE_KLOTEN_DEFAUT = os.path.join(
    _RACINE, 'refs', 'reference-data', 'sia-2028-kloten-temperature.csv')


def charger_temperature_exterieure_kloten(chemin=None):
    u"""Charge la température d'air extérieure horaire de Kloten (8760 h).

    Source : `refs/reference-data/sia-2028-kloten-temperature.csv`, colonne
    `theta_e_air_c` -- traceability/classes-de-validation.spec.md §3.0
    (extraite de `Test4/Resultaterfassung Test4.xlsx`, feuille
    `Wetterdaten`, sortie du programme de référence EnergyPlus).

    Valide que les heures sont contiguës et triées 1..8760 : une source
    réordonnée ou tronquée en silence fausserait tout contrôle croisé.
    """
    chemin = chemin or CHEMIN_TEMPERATURE_KLOTEN_DEFAUT
    heures, valeurs = [], []
    with io.open(chemin, encoding='utf-8', newline='') as flux:
        for ligne in csv.DictReader(flux):
            heures.append(int(ligne['heure']))
            valeurs.append(float(ligne['theta_e_air_c']))
    if len(valeurs) != HEURES_PAR_AN:
        raise ValueError(
            u"Température Kloten : {0} valeurs lues, {1} attendues "
            u"(8760 h). Fichier tronqué ou mal formé : {2}".format(
                len(valeurs), HEURES_PAR_AN, chemin))
    if heures != list(range(1, HEURES_PAR_AN + 1)):
        raise ValueError(
            u"Température Kloten : colonne `heure` non contiguë/non triée "
            u"1..8760 dans {0} -- refus d'utiliser une série dont l'ordre "
            u"temporel n'est pas garanti.".format(chemin))
    return valeurs


def verifier_temperature_exterieure_simulee(serie_simulee, serie_reference=None,
                                             tolerance_c=0.01):
    u"""Compare une série extraite d'une VE réelle à la référence Kloten.

    Ne devine AUCUN nom de variable météo APS : l'appelant doit avoir déjà
    extrait `serie_simulee` (8760 valeurs, °C) par ses propres moyens
    (`ResultsReader.get_weather_results`, §6.1.14.2, niveau `w` -- nom de
    variable non confirmé ici, cf. docstring de module point 4). Ce
    contrôle est ensuite du calcul pur, testable sans VE.

    Retourne un dict {'coherent', 'ecart_max_c', 'heure_ecart_max',
    'nb_heures'}. Une VE mal configurée (mauvais fichier météo, décalage
    horaire) se voit ici AVANT de faire confiance à un résultat système.
    """
    serie_reference = (serie_reference if serie_reference is not None
                        else charger_temperature_exterieure_kloten())
    if len(serie_simulee) != len(serie_reference):
        raise ValueError(
            u"Comparaison météo : {0} valeurs simulées contre {1} de "
            u"référence -- séries de longueur différente, non "
            u"comparables.".format(len(serie_simulee), len(serie_reference)))
    ecarts = [abs(float(a) - float(b))
              for a, b in zip(serie_simulee, serie_reference)]
    ecart_max = max(ecarts) if ecarts else 0.0
    indice_max = ecarts.index(ecart_max) if ecarts else -1
    return {
        'coherent': ecart_max <= tolerance_c,
        'ecart_max_c': ecart_max,
        'heure_ecart_max': indice_max + 1,  # 1-based, comme la colonne `heure` du CSV
        'nb_heures': len(serie_reference),
    }


# --------------------------------------------------------------------------
# Import paresseux de `iesve` -- jamais au niveau module (même convention
# que `test1_adapter.py`), pour que ce fichier reste lisible/inspectable
# par des outils qui n'ont pas VE.
# --------------------------------------------------------------------------

def _iesve():
    """Importe `iesve` à la demande ; erreur précise si VE est indisponible."""
    try:
        import iesve
        return iesve
    except ImportError as erreur:
        raise ImportError(
            "Module 'iesve' indisponible : ce code doit s'exécuter depuis "
            "la fenêtre Scripts d'IESVE (VEScripts), pas en Python "
            "autonome. Erreur d'origine : " + str(erreur))


def assigner_meteo_kloten(chemin_fichier_meteo):
    u"""Assigne le fichier météo SIA 2028 DRY normal, Kloten, au projet
    courant (§6.1.36 -- même mécanisme, déjà vérifié, que
    `test1_adapter.py::assigner_meteo_drycold`).

    Ce module ne fournit PAS le fichier météo lui-même (conversion du
    format SIA d'origine vers un format lisible par VE -- hors périmètre,
    cf. traceability/classes-de-validation.spec.md §3.2) ; il se contente
    de le pointer.
    """
    iesve = _iesve()
    locate = iesve.VELocate()
    if locate.open_wea_data() == -1:
        raise RuntimeError('VELocate.open_wea_data() a échoué.')
    try:
        locate.set({'weather_file': chemin_fichier_meteo})
    finally:
        locate.save_and_close()


# --------------------------------------------------------------------------
# Découverte de variables HVAC -- PAS pour l'extraction de confiance (aucun
# verdict pass/fail ne doit s'appuyer dessus). À utiliser manuellement par
# `ve-adapter-engineer` face à une VE réelle pour construire `plan_extraction`
# -- jamais appelée par `extraire_candidat_test7()`.
# --------------------------------------------------------------------------

NIVEAU_HVAC_COMPOSANT = 'h'   # "HVAC component level", §6.1.14.1
NIVEAUX_APACHE_SYSTEMES = ('v', 'j', 'r')  # misc / énergie / carbone systèmes


def decouvrir_variables_hvac(results_file, jetons_requis=(), niveaux=(NIVEAU_HVAC_COMPOSANT,)):
    u"""Cherche, par jetons (sous-chaînes, insensible à la casse), les
    variables du fichier `.aps` ouvert dont le niveau de modèle appartient
    à `niveaux`. Reprend le même principe que
    `test1_adapter.py::decouvrir_candidats_variable`.
    """
    try:
        variables = results_file.get_variables()
    except Exception as erreur:
        raise RuntimeError(
            'ResultsReader.get_variables() a échoué : {0}'.format(erreur))
    jetons = [jeton.lower() for jeton in jetons_requis]
    resultats = []
    for variable in variables or []:
        niveau_variable = str(variable.get('model_level') or '')
        if niveau_variable not in niveaux:
            continue
        hay = (str(variable.get('aps_varname') or '') + ' '
               + str(variable.get('display_name') or '')).lower()
        if all(jeton in hay for jeton in jetons):
            resultats.append(variable)
    return resultats


def _valeur_unite_declaree(results_file, aps_varname, niveau):
    u"""Nom d'unité (métrique) déclaré par le fichier `.aps` pour une
    variable donnée -- via `get_variables()` (`units_type`) puis
    `get_units()` (exemple d'usage donné littéralement par le PDF,
    §6.1.14.2, fonction `get_units`). Ne devine AUCUNE unité : si la
    variable ou son `units_type` est introuvable, lève une erreur précise
    plutôt que de supposer kW/kWh.
    """
    variables = results_file.get_variables() or []
    for variable in variables:
        if (str(variable.get('aps_varname') or '') == aps_varname
                and str(variable.get('model_level') or '') == niveau):
            type_unite = variable.get('units_type')
            unites = results_file.get_units() or {}
            bloc = unites.get(type_unite)
            if not bloc or 'units_metric' not in bloc:
                raise RuntimeError(
                    u"get_units() ne définit pas l'unité '{0}' pour la "
                    u"variable '{1}' (niveau '{2}').".format(
                        type_unite, aps_varname, niveau))
            return bloc['units_metric'].get('display_name')
    raise RuntimeError(
        u"Variable APS '{0}' (niveau '{1}') introuvable dans ce fichier "
        u".aps -- impossible de vérifier son unité.".format(aps_varname, niveau))


def _serie_horaire_composant(results_file, component_id, component_type,
                             aps_varname, resultats_par_jour):
    u"""Lit la série annuelle complète d'un composant HVAC
    (`get_hvac_component_results`, §6.1.14.2) et la ramène à un pas HORAIRE
    (moyenne des sous-pas), quel que soit le pas de simulation réel. Même
    logique, éprouvée par les tests de mutation, que
    `test1_adapter.py::_lire_serie_horaire` -- réimplémentée ici pour que ce
    fichier reste autonome (chaque `*_adapter.py` du dépôt est chargé
    indépendamment par ses propres tests, `ve_adapter/` n'étant pas un
    paquet).
    """
    brute = results_file.get_hvac_component_results(
        component_id, component_type, aps_varname)
    if hasattr(brute, 'tolist'):
        brute = brute.tolist()
    valeurs = [float(v) for v in brute]
    pas_par_jour = float(resultats_par_jour)
    pas_par_heure = pas_par_jour / 24.0
    if pas_par_heure <= 0:
        raise RuntimeError('results_per_day invalide ({0}).'.format(resultats_par_jour))
    pas_entiers = int(round(pas_par_heure))
    if abs(pas_par_heure - pas_entiers) > 1e-9 or pas_entiers <= 0:
        raise RuntimeError(
            'Pas de simulation non multiple entier de l heure '
            '(results_per_day={0}) -- agrégation horaire non fiable.'
            .format(resultats_par_jour))
    if len(valeurs) % pas_entiers != 0:
        raise RuntimeError(
            'Série de {0} valeurs non divisible par {1} pas/heure -- '
            'année incomplète ?'.format(len(valeurs), pas_entiers))
    horaire = []
    for debut in range(0, len(valeurs), pas_entiers):
        fenetre = valeurs[debut:debut + pas_entiers]
        horaire.append(sum(fenetre) / pas_entiers)
    if len(horaire) != HEURES_PAR_AN:
        raise RuntimeError(
            'Série horaire de {0} valeurs != 8760 (année {1} non complète '
            'ou non standard).'.format(len(horaire), ANNEE_SIMULATION))
    return horaire


def _energie_annuelle_kwh(serie_puissance_kw):
    u"""Somme annuelle [kWh] d'une série horaire de puissance [kW].

    Valide (kW moyen sur l'heure) x (1 h) = kWh : la sommation directe est
    donc correcte UNIQUEMENT parce que la série est déjà horaire (garanti
    par `_serie_horaire_composant`). Fonction séparée pour rester
    testable/mutable indépendamment de la lecture .aps (ex. mutation
    plausible : moyenner au lieu de sommer, qui donnerait un nombre
    plausible et faux).
    """
    if len(serie_puissance_kw) != HEURES_PAR_AN:
        raise ValueError(
            'Série de {0} valeurs != 8760 : agrégation annuelle refusée.'
            .format(len(serie_puissance_kw)))
    return float(sum(serie_puissance_kw))


# --------------------------------------------------------------------------
# Plan d'extraction -- CE MODULE NE FOURNIT AUCUNE LIAISON CANDIDATE (cf.
# docstring, point 4). L'appelant doit construire, face à une VE réelle,
# un dict :
#   plan_extraction = {
#       libelle_de: {
#           'component_id': <str, HVACComponent.id>,
#           'component_type': <valeur HVACComponentTypes DÉJÀ résolue,
#                              typiquement HVACComponent.aps_component_type>,
#           'aps_varname': <str, confirmé via get_variables()>,
#           'unite_attendue': <str, ex. 'kW' -- confronté à
#                              _valeur_unite_declaree() avant lecture>,
#       },
#       ...
#   }
# --------------------------------------------------------------------------

def extraire_grandeur_test7(results_file, libelle_de, entree_plan,
                            resultats_par_jour=None):
    u"""Extrait l'énergie annuelle [kWh] d'UNE grandeur du Test 7, depuis un
    fichier `.aps` déjà ouvert.

    Refuse explicitement `PV-Ertrag` (jamais un chemin de code pour cette
    grandeur, cf. docstring de module point 5) et toute grandeur inconnue
    (protection contre une faute de frappe qui romprait l'appariement avec
    `engine/test7_engine.py`).
    """
    if libelle_de == LIBELLE_PV_ERTRAG:
        raise ValueError(
            u"'PV-Ertrag' ne peut pas figurer dans un plan d'extraction : "
            u"cette grandeur exige l'irradiance sur le plan des modules, "
            u"absente de toute source officielle. Ce module la renvoie "
            u"toujours absente -- voir docstring, point 5.")
    if libelle_de not in _LIBELLES_CONNUS:
        raise KeyError(
            u"Grandeur Test 7 inconnue : {0!r}. Grandeurs attendues : "
            u"{1}".format(libelle_de, sorted(_LIBELLES_CONNUS)))
    for cle in ('component_id', 'component_type', 'aps_varname', 'unite_attendue'):
        if cle not in entree_plan:
            raise KeyError(
                u"Plan d'extraction incomplet pour {0!r} : clé '{1}' "
                u"manquante.".format(libelle_de, cle))

    resultats_par_jour = resultats_par_jour or getattr(results_file, 'results_per_day', 24)

    unite_declaree = _valeur_unite_declaree(
        results_file, entree_plan['aps_varname'], NIVEAU_HVAC_COMPOSANT)
    if unite_declaree != entree_plan['unite_attendue']:
        raise RuntimeError(
            u"Grandeur {0!r} : unité déclarée par le fichier .aps "
            u"({1!r}) != unité attendue par le plan d'extraction "
            u"({2!r}). Refus de lire une série dont l'unité n'est pas "
            u"celle supposée.".format(
                libelle_de, unite_declaree, entree_plan['unite_attendue']))

    serie = _serie_horaire_composant(
        results_file, entree_plan['component_id'], entree_plan['component_type'],
        entree_plan['aps_varname'], resultats_par_jour)
    return _energie_annuelle_kwh(serie)


def extraire_candidat_test7_depuis_fichier(results_file, plan_extraction,
                                            resultats_par_jour=None):
    u"""Construit le candidat `{libellé: valeur_annuelle}` attendu par
    `engine/test7_engine.py::evaluer_test7()`, depuis un fichier `.aps` déjà
    ouvert. Ne remplit QUE les grandeurs présentes dans `plan_extraction` --
    une grandeur absente du plan reste absente du candidat (jamais `0.0`,
    jamais une valeur moyenne) : le moteur la traite alors NOT_CHECKABLE,
    jamais un succès par défaut.
    """
    candidat = {}
    for libelle_de, entree in plan_extraction.items():
        candidat[libelle_de] = extraire_grandeur_test7(
            results_file, libelle_de, entree, resultats_par_jour)
    candidat['_provenance'] = {
        'source': 've_adapter.test7_adapter.extraire_candidat_test7',
        'grandeurs_extraites': sorted(plan_extraction.keys()),
        'pv_ertrag_disponible': False,
        'annee_simulation': ANNEE_SIMULATION,
    }
    return candidat


def extraire_candidat_test7(chemin_aps, plan_extraction, resultats_par_jour=None):
    u"""Point d'entrée principal : ouvre le fichier `.aps`, extrait, ferme.

    `plan_extraction` : voir la section « Plan d'extraction » ci-dessus.
    Aucun plan par défaut n'est fourni -- l'appelant doit l'avoir construit
    contre une VE réelle (cf. docstring de module, point 4).
    """
    iesve = _iesve()
    results_file = iesve.ResultsReader.open(chemin_aps)
    try:
        return extraire_candidat_test7_depuis_fichier(
            results_file, plan_extraction, resultats_par_jour)
    finally:
        results_file.close()


# --------------------------------------------------------------------------
# Mode fixture -- fonctionnement SANS licence VE (PROJECT_PLAN.md §5).
# JSON PLAUSIBLE, PAS issu d'une simulation IESVE réelle -- pour que
# `ui-engineer`/`validation-engine-engineer` câblent le Test 7 sans VE.
# --------------------------------------------------------------------------

CHEMIN_FIXTURE_DEFAUT = os.path.join(_ICI, 'fixtures', 'test7_candidat.exemple.json')


def charger_fixture_test7(chemin=None):
    u"""Charge la fixture JSON d'exemple du Test 7 (mode sans VE).

    Ce JSON N'A JAMAIS été produit par une simulation IESVE réelle -- ses
    dix valeurs checkable sont dérivées de la moyenne des programmes de
    référence (`refs/reference-data/test-7.ref.json`), perturbée de +1 %
    pour rester visuellement distinguable de la référence (même principe
    que `test1_adapter.py::charger_fixture_test1`, qui perturbe de +2 %).
    `PV-Ertrag` est ABSENT (jamais fabriqué), y compris dans la fixture.
    Le champ `_provenance.source` le rappelle explicitement.
    """
    chemin = chemin or CHEMIN_FIXTURE_DEFAUT
    with io.open(chemin, encoding='utf-8') as flux:
        return json.load(flux)
