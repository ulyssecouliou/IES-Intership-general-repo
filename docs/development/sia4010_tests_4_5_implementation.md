# SIA 4010 Tests 4 et 5 - contrat d'implémentation VE

Statut: spécification fail-closed pour `test_4`, `test_5A`, `test_5B`, `test_5C`, `test_5D` (2026-07-29).

## Sources officielles

| Source | Usage |
|---|---|
| `Test4/Spezifikation_Test4.pdf`, pp. 1-3 | local, gains, consignes, AHU, échangeur, batteries |
| `Test4/Resultaterfassung Test4.xlsx` | bandes annuelles, transfert horaire, diagnostics |
| `Test5/Spezifikation_Test5.pdf`, pp. 1-5 | zones, réseau, AHU, variantes, critères |
| `Test5/Resultaterfassung_Test5.xlsx` | bandes annuelles et distributions horaires |
| `Beispielgebäude/Dokumentation_Beispielgebäude_V5.pdf`, pp. 4, 6-10 | plans, enveloppe, vitrages, stores, affectations |
| `Beispielgebäude/IFC_Beispielebäude_201106_abstractBIM.ifc` | polygones, niveaux, volumes, adjacences |
| `references/standards/SIA 380-2-2022 FR.pdf`, pp. 36-37 | constructions limite du Test 4 |

Les rapports utilisateurs sont diagnostiques, jamais normatifs.

## Entrées communes

| Paramètre | Valeur |
|---|---|
| météo | SIA 2028 `DRY normal, Zürich Kloten` |
| période | samedi 01.01.2022 au samedi 31.12.2022, 8760 heures |
| infiltration | 0.15 m3/(h m2) |
| CO2 extérieur | 400 ppm |
| géométrie | extraite de l'IFC, nord et adjacences conservés |
| voisins non modélisés | surfaces adiabatiques explicites |

`DRYCOLD_IESVE.epw` est interdit ici. Le classeur Test 5 utilise 2011, année
non bissextile commençant aussi un samedi: transférer par heure de l'année sans
modifier les timestamps 2022 de l'audit.

## Géométrie

### Test 4

Une zone, local IFC `101`, Hörsaal 4.4, sans fenêtre, sur deux étages, toiture
extérieure: 165.81 m2, hauteur 6.38 m, volume 1058 m3 (IFC `#2343-#2349`;
spécification p. 1). Aucun doublon, aucune ouverture, aucune surface orpheline.

### Test 5

Conserver huit zones séparées, indispensables au VAV CO2 par zone:

| Local | Usage | Aire m2 | Volume m3 |
|---|---|---:|---:|
| 100 | réunion 3.3 | 31.62 | 95 |
| 102 | grand bureau 3.2 | 104.94 | 315 |
| 200 | réunion 3.3 | 31.62 | 95 |
| 201-204 | bureau 3.1, chacun | 17.14 | 51 |
| 205 | bureau 3.1 | 33.13 | 99 |

Total: 269.87 m2, 815 m3, hauteur 3 m. Dimensions des fenêtres depuis l'IFC.
Enveloppe selon documentation pp. 6-9: vitrage Planitherm XN 4/14/4/14/4,
`Ug=0.654`, `g=0.545`, `tau_v=0.742`; cadre 15%, `Uf=1.3`, absorption 0.6;
pas de pont thermique; écran Soltis extérieur à 150 W/m2, `g_total=0.059`.

## Test 4 - paramètres machine

Constructions valeur limite SIA 380/2 tableau 3: mur/toiture `U=0.20 W/(m2K)`;
créer les couches des pp. 36-37 et vérifier le U VE. Le PDF cite FprSIA:
enregistrer un avertissement d'équivalence d'édition.

| Domaine | Valeur |
|---|---|
| usage | Hörsaal SIA 2024:2021, valeurs cibles |
| personnes | 55, 3 m2/personne, 1.2 met, profils SIA 2024 |
| appareils | 10 W/m2, profils SIA 2024 |
| éclairage | 6.4 W/m2, 07:00-18:00, éteint tout juillet |
| débit | 1700 m3/h, variable 20-100%, CO2 600-1000 ppm |
| marche | jours ouvrés 05:00-20:00, arrêt juillet |
| ventilateurs ZUL/ABL | 500/400 Pa; 407/331 W; 2790/2730 min-1 |
| implantation | toiture extérieure; moteurs dans l'air; ventilateurs après WRG |
| WRG | plaques sans humidité, efficacité 0.75, bypass sur consigne |
| WRG été/gel | bypass 100% en froid; bypass pour air rejeté >=0 C |
| air soufflé | PI local; froid 16-22.5 C; chaud 22.5-29 C |
| batterie froide | 12.8 kW; efficacité 0.85; bypass 0.065; eau 13 C |
| état air froid | entrée 29.5 C/22 C humide/14.2 g/kg/52%; sortie 16 C |
| batterie chaude | 11.4 kW; air 8->29 C; eau calcul 31 C, service 40 C |

Consignes selon moyenne extérieure glissante 48 h (p. 2): chauffage 22 C
jusqu'à 19 C, rampe vers 23.5 C à 23.5 C; refroidissement 23 C jusqu'à 12 C,
rampe vers 25 C à 17 C.

## Test 5 - paramètres communs

Usages, gains, horaires et simultanéités: valeurs standard SIA 2024:2021 par
zone. Air neuf 25 m3/h/personne. Plafonds chauffants/rafraîchissants actifs
selon horaire ventilation; leur énergie n'est pas un critère Test 5.
Consignes température identiques au Test 4; CO2 950-1200 ppm; humidification
minimum 30% HR.

| AHU/régulation | Valeur |
|---|---|
| système | multizone, VAV CO2 zonal, AHU en U102 non conditionné |
| débit | 1040 m3/h, 30-100%, jours ouvrés 06:00-19:00 |
| ventilateurs ZUL/ABL | 770/520 Pa; 420/290 W; 3000/2500 min-1 |
| commande | VFD à pression différentielle; moteurs dans l'air; après WRG |
| soufflage | 20 C si Text<=12; rampe à 18 C si Text=20; puis 18 C |
| WRG | rotatif, 20 min-1, auxiliaire 120 W, vitesse modulée |
| WRG été | arrêté si Text > consigne soufflage; aucune récupération froide |
| batterie froide | 8.6 kW; efficacité 0.765; bypass 0.065; air 29.5->17 C |
| eau froide | 18 C si Text<=12, rampe à 13 C à Text=20, min. 10 C pour HR<=60% |
| batterie chaude | 3.5 kW; air 10.5->19 C |
| eau chaude | 40 C si Text<=-10, rampe à 18 C à Text=20, puis 18 C |

Réseau (p. 2): 14 m en 0.3x0.3 m + 5 m en 0.3x0.15 m, `U=0.6`;
20 m en 0.3x0.15 m, `U=1.1`; 24 m diamètre 0.125 m + 40 m diamètre 0.10 m,
`U=1.1`. Ambiance gaine: 15 C oct-mars, 28 C avr-sept. Étanchéité réseau B,
AHU L1.

## Variantes Test 5

| Cas | Pression constante ZUL+ABL | Rotor (sensible/latent) | Humidificateur |
|---|---:|---|---|
| 5A | 50+50 Pa | hygroscopique 0.67/0.42 | contact |
| 5B | 270+270 Pa | hygroscopique 0.67/0.42 | contact |
| 5C | 270+270 Pa | non hygroscopique 0.69/0.30 | contact |
| 5D | 270+270 Pa | non hygroscopique 0.69/0.30 | vapeur électrique |

Rotor selon EN 16798-5-1 annexe D. Contact 5A-C: 4.9 kg/h, pompe
0.01 Wh/m3, vanne régulée, pompe active avec ventilation et besoin.
Vapeur 5D: 4.9 kg/h, énergie électrique.

## Critères officiels

Test 4, bandes annuelles kWh: ventilateurs `688.458-970.500`; réchauffeur
`2442.426-3252.073`; refroidisseur total `1287.652-1400.008`. Les séries
horaires AA-AR du classeur sont transferts/diagnostics, pas un critère
histogramme autonome confirmé.

Test 5, bandes annuelles kWh:

- 5A: ventilateurs 426.029-592.790; chaud 537.583-1239.733; froid 521.404-1483.122.
- 5B: ventilateurs 590.778-739.407; chaud 535.613-1159.517; froid
  533.047-1494.639; WRG total 4481.814-4911.595; latent 301.952-965.774.
- 5C: chaud 607.035-1097.952; froid total 569.513-1424.518; latent 0-281.557;
  WRG total 4161.449-4693.191; latent 30.863-169.113; auxiliaire 215.935-329.031.
- 5D: chaud 314.395-888.059; humidification 137.757-329.786.

Histogrammes obligatoires: 5A ventilateurs/chaud/froid; 5B chaud/froid/WRG
total/latent; 5C débit, ventilateurs, chaud, froid total/latent, WRG
total/latent, auxiliaire WRG; 5D chaud. Chaque bin doit rester dans la bande
officielle. Aucun bin officiel pour la puissance vapeur: ne pas l'inventer.

## API, workflow et bloqueurs

API recommandée: `Sia4010Test45ScenarioFactory.create_test4/create_test5`,
contrats immuables `IfcRoomSelection`, `QualifiedFanCurve`, `DuctSegmentInput`,
`HeatRecoveryInput`, `CoilInput`; adaptateurs `VeApacheHvacCapabilityProbe`,
`VeApacheHvacAdapter.provision/verify_readback`,
`Sia4010Test45ApsExtractor`, `OfficialWorkbookExporter.export_copy`.

Workflow: vérifier sources/checksums -> parser IFC -> valider géométrie ->
probe VE sans mutation -> créer enveloppe/templates -> créer réseau HVAC ->
read-back complet -> météo qualifiée -> 8760 h -> qualifier APS
identité/unité/signe -> bandes annuelles -> histogrammes Test 5 -> JSON/CSV et
copie du classeur. Un projet jetable par variante, fingerprint obligatoire.

Bloqueurs explicites: profils SIA 2024 absents; météo DRY-normal absente;
annexe D EN 16798-5-1 absente; courbes ventilateurs seulement graphiques;
création/read-back ApacheHVAC détaillé non prouvés; VAV CO2 zonal, pertes de
gaines, latent WRG/batterie et puissance humidificateur APS à qualifier. Toute
absence donne `NOT_CHECKABLE` ou bloque la mutation, jamais `PASS`.
