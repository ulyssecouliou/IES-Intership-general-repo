# SIA 4010 - plan d'implémentation VE des Tests 6 et 7

## Statut et principe

Ce document traduit les fichiers officiels locaux en contrats de générateur. Il ne constitue pas une certification. Toute valeur non explicitement présente dans ces sources reste bloquante ou configurable avec `source`, `unit`, `validation_range` et statut `UNCONFIRMED`.

Sources principales :

- `SIA_4010_geteilter_Link/Test6/Spezifikation_Test6.pdf`, pages PDF 1-5.
- `SIA_4010_geteilter_Link/Test6/Resultaterfassung_Test6.xlsx`, feuilles `Daten Testprogramm` et `Zusammenfassung`.
- `SIA_4010_geteilter_Link/Test7/Spezifikation_Test7.pdf`, pages PDF 1-4.
- `SIA_4010_geteilter_Link/Test7/Lastverläufe_220607.xlsx`, feuille `Gruppen`.
- `SIA_4010_geteilter_Link/Test7/Resultaterfassung Test7.xlsx`, feuilles `Daten Testprogramm` et `Zusammenfassung`.
- `SIA_4010_geteilter_Link/Test7/Schema.pdf`, page PDF 1; `PV_Layout.pdf`, pages PDF 1-2.
- `SIA_4010_geteilter_Link/Test7/datenblatt-asm605_201901_5bb_v1_de.pdf`, page PDF 2.
- `SIA_4010_geteilter_Link/Beispielgebäude/Dokumentation_Beispielgebäude_V5.pdf`, pages PDF 3-10, et IFC associé.

## Test 6 - modèle et géométrie

| Paramètre | Valeur à imposer | Source |
|---|---:|---|
| Site / météo | Zürich-Kloten, SIA 2028 `DRY normal` | spécification p.1 |
| Période | 01.01.2022-31.12.2022, pas horaire | spécification p.1; classeur 8760 valeurs |
| Zone 001 | Restaurant, surface 237.4 m2, hauteur IFC 3.0 m | spécification p.1; IFC `IFCSPACE 001` |
| Zone 002 | Cuisine, surface 35.9 m2, hauteur IFC 3.0 m | spécification pp.2-3; IFC `IFCSPACE 002` |
| Empreinte 001 | `(23.032,5.979),(19.742,5.979),(19.742,10.669),(3.792,10.669),(3.792,-2.470),(23.032,-2.470)` | IFC |
| Empreinte 002 | rectangle `(29.642,10.669),(19.972,10.669),(19.972,6.959),(29.642,6.959)` | IFC |
| Autres zones | ne pas les simuler; leurs parois contiguës sont adiabatiques | spécification pp.1-3 |
| Enveloppe | constructions exactes de la documentation du bâtiment | documentation pp.6-9 |
| Infiltration | 0.15 m3/(h.m2), deux zones | spécification pp.1 et 3 |

La spécification Test 6 prévaut sur la documentation générale pour les usages : restaurant `6.2 Selbstbedienungsrestaurant` et cuisine `6.4 Küche zu Selbstbedienungsrestaurant`, selon prSIA 2024:2021. Les nombres de personnes, gains, horaires et simultanéités ne sont pas reproduits dans le PDF : ils ne doivent pas être inventés.

## Test 6 - ventilation et séquence

| Élément | Contrat machine |
|---|---|
| Restaurant | soufflage 3000 m3/h, reprise 2650 m3/h à 100 %; surpression 350 m3/h vers cuisine |
| Cuisine | soufflage 3150 m3/h, extraction 3500 m3/h à 100 %; reçoit 350 m3/h du restaurant |
| Centrale | débit total 6150 m3/h; niveau 1 = 2050 (33.3 %), niveau 2 = 4100 (66.7 %), niveau 3 = 6150 (100 %) |
| Profil lundi-samedi | 00:00-07:00=0; 07:00-08:00=0.333; 08:00-10:00=0.667; 10:00-12:00=1; 12:00-13:00=0.667; 13:00-16:00=0.333; 16:00-24:00=0 |
| Dimanche | 0 toute la journée |
| Pressions nominales | soufflage 750 Pa; extraction 550 Pa |
| Ventilateurs | soufflage 2021 W à 1865 min-1; extraction 1460 W à 1700 min-1; moteurs dans le flux, après récupération |
| Réseau | gaines et longueurs de la spécification p.3; étanchéité réseau D, centrale L1 |
| Récupération | boucle eau-glycol 30 %, efficacité thermique nominale 0.71, 2100 l/h, pompe 185 W |
| Régulation récupération | vitesse pompe modulée sur consigne soufflage; antigel sur air rejeté >= 5 °C; débit pompe minimum 50 % |
| Consigne soufflage | 20 °C jusqu'à Text=12 °C; interpolation vers 18 °C à Text=20 °C; 18 °C au-dessus |
| Batterie froide | 30 kW; efficacité échange 0.7; air 26.3/22 °C humide, 14.2 g/kg, 52 % HR vers 17 °C; eau entrée 13 °C |
| Eau froide | 18 °C jusqu'à Text=12 °C; interpolation vers 13 °C à Text=20 °C; 13 °C au-dessus |
| Batterie chaude | 35 kW; air +2 vers 19 °C; eau entrée 40 °C |
| Eau chaude | 40 °C jusqu'à Text=-8 °C; interpolation vers 20 °C à Text=20 °C; 20 °C au-dessus |
| Émission restaurant | convecteurs actifs pendant la ventilation; courbe eau 40 °C à -8 °C vers 20 °C à 20 °C extérieur |
| Refroidissement restaurant | plafond froid actif pendant la ventilation; consigne d'ambiance basée sur moyenne extérieure glissante 48 h, courbes de la p.2 |
| Cuisine | aucune émission chauffage/refroidissement; consigne chauffage 21 °C |

## Test 6 - sorties et acceptation

Exporter chaque heure : débit soufflage/extraction, puissance totale et séparée des ventilateurs, batteries chaude/froide (dont latent/sensible), récupération chauffage/refroidissement, auxiliaire récupération, températures soufflage/retour/après récupération et diagnostic d'occupation. Les 6 bandes annuelles officielles sont :

| Grandeur | Bas | Référence | Haut | kWh |
|---|---:|---:|---:|---|
| Ventilateurs | 3320.807 | 3853.655 | 4386.504 | kWh |
| Batterie chaude | 1397.590 | 1788.934 | 2180.278 | kWh |
| Batterie froide totale | 2447.749 | 3619.145 | 4790.542 | kWh |
| Récupération chaleur | 27315.566 | 28311.310 | 29307.054 | kWh |
| Récupération froid | -332.370 | -222.217 | -112.063 | kWh |
| Auxiliaire récupération | 131.770 | 205.465 | 279.160 | kWh |

## Test 7 - entrées et chaîne énergétique

Le Test 7 peut être exécuté sans régénérer les zones : importer strictement les 8760 valeurs horaires en W de `Lastverläufe_220607.xlsx`, feuille `Gruppen`, lignes 6-8765.

| Colonne | Charge |
|---|---|
| B | froid plafonds T5+T6 |
| C/D/E | froid ventilation T4/T5/T6 |
| F | chaleur eau chaude sanitaire à l'entrée du ballon, consigne 60 °C |
| G/H/I | chaleur ventilation T4/T5/T6 |
| J/K | chaleur plafond T5 / convecteurs T6 |

Distribution froid : pertes 5 % de la chaleur absorbée; auxiliaires 2 %; 50 % des auxiliaires deviennent charge du circuit froid. Distribution chaleur : pertes 5 % de la chaleur livrée; auxiliaires 2 %; 50 % récupérés dans le circuit chaleur. Stockages chaud et froid : eau, 2000 l chacun; appliquer exactement les commandes haut/bas décrites en p.1. Le schéma p.1 fixe les connexions, débits et lois de température et doit être traité comme source graphique de référence.

Générateur : Climaveneta NX-W-Y/H 0182, eau-eau réversible, deux compresseurs Scroll/étages; 55.9 kW froid et 60.0 kW chaleur (spécification pp.2-3). Modélisation séparée chaud/froid autorisée. Implémenter les tables de capacité/EER/COP des pages 2-3, y compris consommations arrêt/thermostat/veille/carter, température bivalente -7 °C et limite -10 °C; ne pas remplacer par un COP constant.

Circuit extérieur : dry cooler 70 kW en froid, échangeur air 76 kW en chaud, ventilateur 0.045 kW/kW, eau-glycol 30 % à confirmer, 19000 kg/h, delta T 4 K, approche air-départ 4 K à pleine charge; 50 % de la chaleur pompe agit sur le circuit; pertes 5 %. En refroidissement simultané avec demande chaleur, charger le ballon chaud par le condenseur. Sous la bivalence, appoint gaz, rendement 0.9 (spécification p.4).

PV : modules AEG AS-M605-310, rendement onduleur 97 %. Toit 150 modules, pente 10°, est/ouest; façade sud 52 modules. Le layout donne 46.5 + 16.12 = 62.62 kWp, tandis que la spécification p.4 indique 45 + 15.6 = 60.6 kWp : bloquer la mutation tant qu'une règle de préséance n'est pas approuvée. Le partage exact est/ouest n'est pas chiffré. Le datasheet p.2 fournit notamment Pmax 310 W, Vmp 32.6 V, Imp 9.51 A, Voc 40.1 V, Isc 10.04 A, efficacité 19.1 %, NOCT 45 °C et coefficient Pmax -0.40 %/K.

## Test 7 - bandes annuelles officielles

| Grandeur (kWh) | Bas | Référence | Haut |
|---|---:|---:|---:|
| Électricité machine froide | 3373.784 | 3928.779 | 4483.774 |
| Chaleur totale rejetée | 22468.020 | 23762.689 | 25057.357 |
| Auxiliaires froid | 1088.723 | 2187.597 | 3286.470 |
| Froid vers côté chaud | 0 | 331.788 | 935.926 |
| Chaleur dry cooler | 27293.358 | 28122.460 | 28951.562 |
| Électricité PAC | 8081.321 | 8727.624 | 9373.927 |
| Chaleur chauffage | 7415.879 | 7847.662 | 8279.446 |
| Chaleur ECS | 22871.194 | 23707.189 | 24543.183 |
| Gaz chaudière | 0 | 44.150 | 126.399 |
| Auxiliaires chaleur | 595.881 | 1228.061 | 1860.240 |
| Production PV | 54069.923 | 56975.555 | 59881.188 |

## Bloqueurs VE et API recommandée

- Aucun générateur VE contrôlé n'existe actuellement pour `test_6/6` ou `test_7/7`; l'interface doit rester `PREPARE_ONLY`.
- Le package ne contient pas le fichier météo SIA 2028 `DRY normal` Zürich-Kloten : exigence bloquante avec checksum et contrôle 8760.
- Les valeurs prSIA 2024:2021 des usages 6.2/6.4 manquent : injecter un fichier de paramètres source-tracé, jamais des valeurs arbitraires.
- VEScripts sait créer/assigner un système Apache simplifié, mais la création fiable d'un réseau ApacheHVAC complet, des circuits hydrauliques, stockages, récupération en cascade, bivalence et PV n'est pas démontrée. Prévoir soit un template VE/APHVAC signé à cloner et paramétrer, soit un solveur Test 7 Python horaire indépendant dont les résultats sont audités.
- Les conversions horaires doivent préserver signes, unités et conventions : Test 6 exporte des W; Test 7 demande des kWh par pas dans le classeur; faire un contrôle de bilan annuel avant comparaison.

API recommandée : `prepare(case, sources) -> PreflightReceipt`, `build_geometry(Test6GeometryConfig)`, `bind_official_usage(UsageDataset)`, `build_test6_airside(Test6AirsideConfig)`, `load_test7_profiles(ProfileWorkbookBinding)`, `build_test7_plant(Test7PlantConfig)`, `run_or_export()`, `extract_hourly(OutputBindingMap)`, `compare(OfficialBandSet)`. Chaque étape doit être idempotente, posséder un `source_locator`/checksum, relire les objets VE après mutation et refuser toute revendication `PASS` si météo, usages, table machine, réseau hydraulique ou PV restent non résolus.
