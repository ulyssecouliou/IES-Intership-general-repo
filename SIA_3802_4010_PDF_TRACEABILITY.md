# Traçabilite PDF - SIA 380/2:2022 et SIA 4010:2023 pour IESVE

Version: 2026-06-29  
Projet: Swiss Compliance Checker IESVE  
Sources locales:

- `SIA 380-2-2022 FR.pdf`
- `SIA 4010-2023 FR.pdf`

Document detaille associe:

- `SIA4010_FULL_COMPLIANCE_ANALYSIS.md` pour l'analyse complete du PDF SIA 4010:2023.

## 1. Position professionnelle

Ce document ne remplace pas les normes SIA sous licence. Il sert de matrice de travail pour coder un checker IESVE defensable.

Principe applique dans le code:

| Statut | Signification | Comportement attendu dans le checker |
|---|---|---|
| `DIRECT_PDF` | Valeur explicitement lisible dans SIA 380/2 ou SIA 4010 | Peut devenir un seuil code avec source table/page |
| `EXTERNAL_STANDARD` | Le PDF renvoie a SIA 2024, SIA 387/4, SIA 382/1, SIA 380, etc. | Ne pas inventer de seuil; demander la donnee/reference externe |
| `OFFICIAL_EVIDENCE_REQUIRED` | La conformite depend de fichiers/tests SIA officiels | Statut `NOT_CHECKABLE` tant que les preuves ne sont pas jointes |
| `DESIGN_REVIEW` | Indicateur utile mais non opposable directement | Alerte de revue, pas un echec normatif |

## 2. Corrections majeures appliquees

Les anciennes valeurs suivantes ne doivent plus etre traitees comme des criteres SIA directs:

| Ancien critere code | Ancien seuil | Decision |
|---|---:|---|
| WWR max | 30 % | Devient `DESIGN_REVIEW`; SIA 380/2 tableau 2 renvoie le taux de surfaces vitrees a SIA 2024 |
| Ventilation min | 0.5 h-1 | Supprime du pass/fail direct; SIA 380/2 renvoie aux debits SIA 2024 et a la commande tableau 4 |
| Eclairage max | 12 W/m2 | Supprime du pass/fail direct; SIA 380/2 renvoie a SIA 387/4 et SIA 2024 |
| Equipements max | 20 W/m2 | Supprime du pass/fail direct; SIA 380/2 renvoie a SIA 2024 |
| Rendement HVAC min | 90 % | Supprime du pass/fail direct; SIA 380/2 utilise EER/SEER/SCOP par systeme/puissance et SIA 4010 |
| Seuils SIA 4010 kWh/m2/CO2 | variables | Supprimes comme verdict normatif; SIA 4010 valide une methode via 7 tests officiels |

## 3. SIA 380/2:2022 - valeurs directement codables

Source principale: SIA 380/2:2022 FR, tableau 2, pages PDF 32-35.

| Domaine | Symbole / donnee | Valeur limite | Valeur cible | Statut code |
|---|---:|---:|---:|---|
| Fenetres, verre + cadre | Uw | 1.10 W/(m2.K) | 0.88 W/(m2.K) | `DIRECT_PDF` |
| Ponts thermiques | psi / chi | 0 | 0 | `DIRECT_PDF`, extraction VE future |
| Part du cadre fenetre | ff | 0.25 | 0.25 | `DIRECT_PDF`, extraction VE future |
| Taux surfaces vitrees | fg | SIA 2024 | SIA 2024 | `EXTERNAL_STANDARD` |
| Valeur g vitrage | g_perp | 0.50 | 0.50 | `DIRECT_PDF` si la valeur VE est bien le g SIA |
| Transmission lumineuse vitrage | tau | 0.70 | 0.70 | `DIRECT_PDF`, extraction VE future |
| Protection solaire reference | type | store a lamelles exterieur | a confirmer par categorie cible | `DIRECT_PDF`, extraction VE future |
| Categorie protection solaire | categorie | 4 | 2 | `DIRECT_PDF`, extraction VE future |
| Commande protection solaire | categorie SIA 387/4 tableau 9 | 2 | 3 | `EXTERNAL_STANDARD` |
| Infiltration par surface nette | q | 0.15 m3/(h.m2) | 0.15 m3/(h.m2) | `DIRECT_PDF`, extraction VE future |

## 4. SIA 380/2:2022 - constructions de reference

Source: SIA 380/2:2022 FR, tableau 3, pages PDF 36-37.

| Element | U limite | U cible | Statut code |
|---|---:|---:|---|
| Mur exterieur | 0.20 W/(m2.K) | 0.14 W/(m2.K) | `DIRECT_PDF`, code actif |
| Mur exterieur contre terrain | 0.30 W/(m2.K) | 0.20 W/(m2.K) | `DIRECT_PDF`, classification VE future |
| Paroi interieure non porteuse | 0.30 W/(m2.K) | 0.30 W/(m2.K) | `DIRECT_PDF`, non applique aux surfaces externes |
| Paroi interieure porteuse | 2.70 W/(m2.K) | 2.70 W/(m2.K) | `DIRECT_PDF`, non applique aux surfaces externes |
| Paroi interieure contre local non conditionne | 0.28 W/(m2.K) | 0.20 W/(m2.K) | `DIRECT_PDF`, classification VE future |
| Sol contre terrain | 0.30 W/(m2.K) | 0.20 W/(m2.K) | `DIRECT_PDF`, code actif comme fallback floor |
| Plancher intermediaire | 0.64 W/(m2.K) | 0.64 W/(m2.K) | `DIRECT_PDF`, classification VE future |
| Plancher contre cave non conditionnee | 0.30 W/(m2.K) | 0.20 W/(m2.K) | `DIRECT_PDF`, classification VE future |
| Toiture plate | 0.20 W/(m2.K) | 0.14 W/(m2.K) | `DIRECT_PDF`, code actif |

Limite actuelle du checker:

- VE fournit souvent `wall`, `roof`, `floor`; le code applique donc un fallback prudent.
- Pour une certification complete, il faut enrichir la classification: terrain, cave non conditionnee, plancher intermediaire, mur contre terrain, etc.

## 5. SIA 380/2:2022 - ventilation et CTA reference

Source: SIA 380/2:2022 FR, tableau 2, pages PDF 33-35.

| Critere | Valeur limite | Valeur cible | Statut |
|---|---:|---:|---|
| Debit exige air fourni/extrait | SIA 2024 | SIA 2024 | `EXTERNAL_STANDARD` |
| Efficacite ventilation | 1.0 | 1.4 | `DIRECT_PDF`, extraction VE future |
| Classe etancheite gaines | C | C | `DIRECT_PDF`, extraction VE future |
| Classe etancheite appareil ventilation | L2 | L1 | `DIRECT_PDF`, extraction VE future |
| U CTA en zone non conditionnee | 0.70 W/(m2.K) | 0.50 W/(m2.K) | `DIRECT_PDF`, extraction VE future |
| H gaines air fourni en zone non conditionnee | 15 W/K | 10 W/K | `DIRECT_PDF`, extraction VE future |
| Perte charge air fourni | 700 Pa | 550 Pa | `DIRECT_PDF`, extraction VE future |
| Perte charge air repris | 500 Pa | 350 Pa | `DIRECT_PDF`, extraction VE future |
| Part perte charge recuperation chaleur | 300 Pa | 400 Pa | `DIRECT_PDF`, extraction VE future |
| Fan control monozone | DIRECT | DIRECT | `DIRECT_PDF`, extraction VE future |
| Fan control multizone | CONST_PRES | MIN_PRES | `DIRECT_PDF`, extraction VE future |
| Recuperation chaleur, efficacite temperature | 0.73 | 0.78 | `DIRECT_PDF`, extraction VE future |
| Recuperation humidite | 0.00 | 0.60 | `DIRECT_PDF`, extraction VE future |

## 6. SIA 380/2:2022 - commande ventilation

Source: SIA 380/2:2022 FR, tableau 4, page PDF 37.

| Type installation | Debit air neuf | Valeur limite | Valeur cible |
|---|---:|---|---|
| Monozone | <= 3 m3/(h.m2) | 1 vitesse, commande horaires | 2 vitesses 67/100 %, commande horaires |
| Monozone | 3-6 m3/(h.m2) | 2 vitesses 67/100 %, commande horaires | Vitesse variable >= 25 %, demande selon personnes |
| Monozone | > 6 m3/(h.m2) | Vitesse variable >= 25 %, demande selon personnes | Vitesse variable >= 25 %, demande selon detecteur de gaz |
| Multizone | <= 3 m3/(h.m2) | 2 vitesses 67/100 %, horaires par zone | 2 vitesses 67/100 %, occupation par zone |
| Multizone | 3-6 m3/(h.m2) | 2 vitesses 67/100 %, occupation par zone | Vitesse variable >= 25 %, demande personnes par local |
| Multizone | > 6 m3/(h.m2) | Vitesse variable >= 25 %, detecteur gaz par zone | Vitesse variable >= 25 %, detecteur gaz par local |

Impact code:

- Le simple seuil `ACH >= 0.5` n'est pas SIA 380/2.
- Il faut extraire depuis VE: type monozone/multizone, debit air neuf par surface, strategie de commande, type capteur/personnes/gaz.

## 7. SIA 380/2:2022 - froid, chauffage, PV

Sources: SIA 380/2:2022 FR, tableaux 5-9 pages PDF 38-39 et tableau 2 page PDF 35.

### Froid - machines a compresseur air

| Puissance | EER limite | SEER limite | EER cible | SEER cible |
|---|---:|---:|---:|---:|
| <= 12 kW | 2.90 | 3.80 | 3.10 | 4.20 |
| 12-50 kW | 3.00 | 3.90 | 3.15 | 4.35 |
| 50-150 kW | 3.10 | 4.00 | 3.20 | 4.50 |
| 150-450 kW | 3.20 | 4.20 | 3.40 | 4.80 |
| 450-1000 kW | 3.40 | 4.40 | 3.60 | 5.00 |

### Froid - machines a compresseur eau

| Puissance | EER limite | SEER limite | EER cible | SEER cible |
|---|---:|---:|---:|---:|
| 12-50 kW | 4.05 | 4.50 | 4.45 | 5.90 |
| 50-150 kW | 4.25 | 4.80 | 4.65 | 6.10 |
| 150-450 kW | 4.65 | 5.50 | 5.05 | 6.90 |
| 450-1000 kW | 5.05 | 6.10 | 5.50 | 7.40 |
| > 1000 kW | 5.50 | 6.70 | 6.00 | 8.00 |

### Chauffage - pompes a chaleur

| Generateur | Puissance | SCOP limite | SCOP cible |
|---|---:|---:|---:|
| PAC air-eau | <= 12 kW | 3.00 | non donne dans la table extraite |
| PAC air-eau | 12-50 kW | 3.10 | non donne dans la table extraite |
| PAC air-eau | 50-150 kW | 3.20 | non donne dans la table extraite |
| PAC sonde geothermique | 12-50 kW | 4.00 | 4.40 |
| PAC sonde geothermique | 50-150 kW | 4.20 | 4.60 |
| PAC sonde geothermique | 150-450 kW | 4.60 | 5.00 |
| PAC sonde geothermique | 450-1000 kW | 5.00 | 5.50 |
| PAC sonde geothermique | > 1000 kW | 5.50 | 6.00 |

### PV

| Critere | Valeur limite | Valeur cible |
|---|---:|---:|
| Dimensionnement PV | 10 W/m2 SRE | Toute surface appropriee equipee de modules avec eta = 0.17 |
| Rendement conversion | 0.90 | 0.90 |

Impact code:

- Le checker ne peut pas utiliser un rendement HVAC unique de 90 %.
- Il doit d'abord identifier: type de systeme, puissance, regime, EER/SEER/SCOP disponible, et source de donnee.

## 8. SIA 380/2:2022 - categories de protection solaire

Source: SIA 380/2:2022 FR, tableau 10, page PDF 46.

| Categorie | Type | Reflectance solaire | Transmission solaire |
|---|---|---:|---:|
| 1 | Lamelles | 0.70 | 0.00 |
| 1 | Store tissu | 0.50 | 0.25 |
| 2 | Lamelles | 0.70 | 0.00 |
| 3 | Lamelles | 0.50 | 0.00 |
| 3 | Store tissu | 0.35 | 0.25 |
| 4 | Lamelles | 0.30 | 0.00 |
| 4 | Store tissu | 0.25 | 0.10 |
| 5 | Store tissu | 0.20 | 0.05 |

Impact code:

- Extraire depuis VE le type de protection solaire, sa reflectance/transmission ou le g_total active.
- Controler la categorie seulement si les donnees sont disponibles.

## 9. SIA 380/2:2022 - methodes et calculs a respecter

Sources: SIA 380/2:2022 FR, chapitres 4-7 et annexe A.

### 9.1 Donnees climatiques

Le calcul dynamique utilise des donnees horaires. Pour les justifications, le PDF renvoie a une Design Reference Year selon SIA 2028. SIA 4010 ajoute des precisions climatiques sur le scenario RCP 8.5 periode 2035 pour l'evaluation de surchauffe estivale selon le contexte.

Champs VE a extraire:

- fichier meteo;
- station climatique;
- pas de temps simulation;
- periode simulee;
- presence/absence de preconditionnement.

### 9.2 Puissance chauffage

Regle de methode:

```text
Phi_H = puissance thermique horaire necessaire pour maintenir la consigne basse.
```

Conditions a verifier:

- climat de dimensionnement chauffage selon SIA 2028;
- phase de stabilisation/preconditionnement de 14 jours;
- consignes selon SIA 2024 ou consignes variables selon le cas;
- apports internes non pris en compte sauf justification acceptee.

### 9.3 Puissance refroidissement

Regle de methode:

```text
Phi_C = puissance thermique horaire a extraire pour maintenir la consigne haute.
```

Conditions a verifier:

- donnees de dimensionnement refroidissement selon SIA 2028;
- 3 jours de reference estivaux;
- 14 jours de stabilisation avant chaque jour de reference;
- apports internes selon SIA 2024/SIA 387/4;
- protection solaire selon strategie prevue et SIA 387/4.

### 9.4 Besoins annuels chauffage/refroidissement

Calcul attendu:

```text
Q_H,k = somme_sur_annee(max(Phi_H,k,t, 0) * delta_t)
Q_C,k = somme_sur_annee(max(Phi_C,k,t, 0) * delta_t)
```

Pour zone/batiment:

```text
Q_H,batiment = superposition/somme des courbes horaires des locaux concernes
Q_C,batiment = superposition/somme des courbes horaires des locaux concernes
```

Points d'audit:

- seules les puissances positives utiles sont sommees;
- les valeurs mensuelles et annuelles doivent etre exportables;
- les courbes horaires doivent rester disponibles comme preuve.

### 9.5 Besoin d'energie

Regle de methode:

- les profils d'energie finale doivent etre reportes par agent energetique;
- la resolution temporelle doit suivre le bilan SIA 380, generalement 1 heure;
- aggregation annuelle et ponderation selon SIA 380;
- le calcul part du besoin aval vers la production;
- pertes thermiques et energie auxiliaire des sous-systemes doivent etre identifiables.

## 10. Calculs internes du checker IESVE

Ces calculs ne sont pas tous des criteres SIA directs, mais ils structurent le rapport.

### 10.1 U-value moyenne opaque

```text
U_moy = somme(U_i * A_net_i) / somme(A_net_i)
```

Conditions:

- exclure les surfaces nettes quasi nulles;
- ne pas melanger surfaces opaques et vitrages;
- regrouper par construction CDB pour produire des actions correctives.

### 10.2 WWR - indicateur de revue

```text
WWR = surface_fenetres_exterieures / surface_brute_murs_exterieurs
```

Statut:

- utile pour detecter un risque solaire;
- pas un critere SIA 380/2 direct;
- la valeur normative doit venir de SIA 2024 ou du calcul de reference.

### 10.3 Donnees manquantes

Regle:

```text
donnee_absente => alerte explicite
donnee_absente != PASS
```

## 11. SIA 4010:2023 - nature de la compliance

Source: SIA 4010:2023 FR, clauses 2.3-2.6 page PDF 8.

SIA 4010 ne certifie pas directement qu'un modele client est bon. Elle encadre la validation d'une methode ou d'un logiciel capable de faire les calculs couverts par SIA 380/2.

La procedure repose sur:

- une specification de test;
- des resultats de reference;
- un fichier d'evaluation Excel officiel;
- des modeles/plans/donnees numeriques externes pour certains tests;
- une evaluation par la sous-commission SIA.

Conclusion code:

- sans fichiers officiels SIA 4010, le statut doit rester `NOT_CHECKABLE`;
- le checker peut collecter les preuves, mais ne doit pas inventer un PASS.

## 12. SIA 4010:2023 - 7 tests de validation

Source: SIA 4010:2023 FR, tableau 62, page PDF 46.

| Test | Champ | Preuves attendues cote IESVE |
|---|---|---|
| 1 | Enveloppe de base selon EN ISO 52016-1 / ASHRAE 140 | Cas officiel importe, resultats horaires/charges compares au fichier officiel |
| 2 | Regulation protection solaire selon SIA 387/4 et SIA 380/2 annexe A | Strategie stores, climat CH, usage CH, infiltration, angles et apports solaires |
| 3 | Regulation eclairage selon SIA 387/4 | Puissance/energie eclairage, daylight control, variantes 3A-3L |
| 4 | Climatisation mono-piece, air seul | Amphitheatre sans fenetre, VAV/CO2, batteries, temperatures, CO2, puissances |
| 5 | CTA multizone complexe | Bureaux/salles reunion, rotor chaleur/humidite, humidification, variantes 5A-5D |
| 6 | Ventilation trois niveaux | Restaurant/cuisine, recuperation chaleur, debit constant, debordement |
| 7 | Emission/distribution/stockage/production chaud/froid | Energies finales chaud/froid, pompes, stockage, generateurs, PV si present |

## 13. SIA 4010:2023 - classes de validation

Source: SIA 4010:2023 FR, tableau 63, page PDF 48.

| Classe | Application | Tests requis |
|---|---|---|
| 1A | Besoin de refroidissement + puissance thermique de base, stores simples sans suivi position soleil | 1 et 2A |
| 1B | Meme usage avec stores a lamelles | 1 et 2 |
| 2A | Energie eclairage SIA 387/4 + besoin chauffage/refroidissement, stores simples | 1, 2A, 3A a 3F |
| 2B | Meme usage avec stores a lamelles | 1 a 3 |
| 3 | Humidification/deshumidification | 1, 4 a 6 |
| 4A | Puissance systeme + energie chauffage/refroidissement, stores simples | 1, 2A, 3A a 3F, 4 a 7 |
| 4B | Meme usage avec stores a lamelles | 1 a 7 |
| 5 | Besoins energie chauffage/refroidissement sur profils de besoins existants | 7 |

## 14. SIA 4010:2023 - variantes de tests

Source: SIA 4010:2023 FR, tableaux 65-66, page PDF 52.

### Tests 2 + 3

| Variante | Protection solaire | Regulation protection solaire | Regulation eclairage |
|---|---|---:|---:|
| 3A | Store tissu | aucune | 1 |
| 3B | Store tissu | aucune | 2 |
| 3C | Store tissu | aucune | 3 |
| 3D | Store tissu | aucune | 4 |
| 3E | Store tissu | aucune | 5 |
| 3F | Store tissu | aucune | 6 |
| 3G | Stores a lamelles | 1 | 1 |
| 3H | Stores a lamelles | 1 | 3 |
| 3I | Stores a lamelles | 2 | 1 |
| 3J | Stores a lamelles | 2 | 3 |
| 3K | Stores a lamelles | 3 | 1 |
| 3L | Stores a lamelles | 3 | 3 |

### Test 5

| Variante | FAN_CTRL | Recuperateur chaleur | Humidificateur |
|---|---|---|---|
| 5A | MIN_PRES | hygroscopique | adiabatique |
| 5B | CONST_PRES | hygroscopique | adiabatique |
| 5C | CONST_PRES | non hygroscopique | adiabatique |
| 5D | CONST_PRES | non hygroscopique | vapeur |

## 15. SIA 4010:2023 - valeurs techniques extractibles utiles

Sources: SIA 4010:2023 FR, pages PDF 11-16 et suivantes.

| Sujet | Valeur / liste utile | Usage checker |
|---|---|---|
| Fuites conduits | inconnue 1.45, A 1.18, B 1.06, C 1.02, D 1.00 | Verifier etancheite ventilation si VE expose la classe |
| Classe conduits par defaut | neuf B, existant/inconnu | Hypothese a documenter |
| Fuites CTA | L3 1.10, L2 1.04, L1 1.01 | Verifier classe CTA |
| Classe CTA par defaut | neuf L1, existant L3 | Hypothese a documenter |
| AIR_FLOW_CTRL | NO_CTRL, ON/OFF_CTRL, MULTI_STAGE, VARIABLE | Mapping regulation ventilateur |
| SYS_TYPE | SINGLE_ZONE, MULTI_ZONE | Mapping monozone/multizone |
| FAN_CTRL | NO_CTRL, CONST_PRES, MIN_PRES, DIRECT | Mapping fan control |
| Moteur ventilateur | IN_AIR, OUTS_AIR | Energie ventilateur et bilan air |
| Humidificateur | CONTACT, ROT_SPRAY, HI_PRES, HYBRID, STEAM, OTHER | Mapping test 5 et systemes |

## 16. Preuves minimales a collecter pour un rapport professionnel

| Famille preuve | Donnees attendues |
|---|---|
| Projet | chemin projet, modele actif, version VE, date run, script version |
| Geometrie | zones, surfaces, ouvertures, surfaces nettes/brutes, orientation |
| Constructions | CDB id, nom, U-value, g-value, couches si possible |
| Usage | SIA 2024 usage, surface/personne, profils personnes/appareils, consignes |
| Eclairage | puissance, commande SIA 387/4, daylight control, profil |
| Ventilation | debit fourni/extrait, infiltration, type systeme, fan control, etancheite, recuperation |
| HVAC | type generateur, puissance, EER/SEER/SCOP, pertes, auxiliaires |
| Meteo | fichier DRY, station, scenario, calendrier, pas de temps |
| Resultats dynamiques | APS/Vista horaires: chauffage, froid, temperatures, CO2, debits, puissances, energies |
| SIA 4010 | specs tests, fichiers Excel officiels, resultats exportes, comparaison reference, classe visee |

## 17. Roadmap technique pour atteindre une certification defendable

### Phase A - Base fiable deja lancee

- Extraire U-values et g-values depuis CDB VE.
- Produire alertes de donnees manquantes.
- Generer rapport Excel et nom unique.
- Centraliser les valeurs SIA 380/2 extraites des PDF.
- Mettre SIA 4010 en `NOT_CHECKABLE` sans preuve officielle.

### Phase B - Extraction normative manquante

- Extraire / mapper les usages SIA 2024 par zone.
- Extraire consignes chauffage/refroidissement et humidite.
- Extraire puissances eclairage et types de commande SIA 387/4.
- Extraire debits air fourni/extrait en m3/h et convertir par personne/surface.
- Extraire infiltration en m3/(h.m2) ou convertir depuis ach si volume/surface fiables.
- Extraire types de systemes HVAC, puissances, EER/SEER/SCOP.

### Phase C - Resultats dynamiques

- Localiser et lire les fichiers APS/Vista disponibles.
- Exporter courbes horaires chauffage/refroidissement.
- Calculer Q_H et Q_C annuels selon pas de temps.
- Verifier meteo, calendrier, preconditionnement.
- Produire onglet Excel "Dynamic Results".

### Phase D - SIA 4010 evidence pack

- Ajouter un dossier `sia4010_evidence/`.
- Permettre a l'utilisateur de joindre fichiers Excel officiels.
- Lire les statuts/graphes/resultats des fichiers officiels si format stable.
- Mapper classe de validation visee -> tests requis.
- Generer un onglet "SIA4010 Evidence".

### Phase E - Rapport client

- Differencier score qualite modele, score SIA 380/2 direct, preuves externes et SIA 4010.
- Ajouter une synthese manager: "certifiable maintenant / bloque par preuves / corrections modele".
- Garder chaque alerte liee a sa source PDF/table/page.

## 18. Regles de prudence a conserver

- Ne jamais transformer une absence de donnee en PASS.
- Ne jamais appeler "SIA 4010 compliant" un modele sans fichiers officiels de validation.
- Ne jamais utiliser un seuil client/projet comme s'il venait du PDF.
- Toujours distinguer valeur limite et valeur cible.
- Toujours conserver la source: norme, tableau, page PDF, champ VE et valeur extraite.
