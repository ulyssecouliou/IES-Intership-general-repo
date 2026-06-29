# Analyse complete SIA 4010:2023 pour compliance IESVE avec SIA 380/2:2022

Version: 2026-06-29  
Source analysee: `SIA 4010-2023 FR.pdf`  
Objectif: transformer SIA 4010 en exigences exploitables pour un checker Python IESVE et un rapport de compliance suisse.

## 1. Conclusion executive

SIA 4010 ne donne pas une liste de seuils simples permettant de declarer directement un modele client "conforme".

Le PDF montre que SIA 4010 sert surtout a:

| Sujet | Ce que SIA 4010 exige | Consequence pour le checker |
|---|---|---|
| Application de SIA 380/2 | Clarifier les exigences de calcul dynamique et les entrees techniques des systemes | Verifier que le modele VE contient les donnees et sorties necessaires |
| Methode/logiciel | Valider le logiciel ou la methode par 7 tests officiels | Statut `NOT_CHECKABLE` sans fichiers SIA officiels |
| Systemes techniques | Rassembler les entrees issues des normes EN/SIA pour ventilation, froid, chaud, stockage, PV, etc. | Construire une matrice d'extraction VE par sous-systeme |
| Rapport professionnel | Fournir preuves, fichiers de test, resultats de reference, classe visee | Generer un evidence pack, pas un PASS automatique |

Regle de prudence:

```text
SIA 4010 PASS = seulement si les tests officiels requis sont completes et acceptes.
Modele VE client = peut etre audite pour readiness SIA 4010, mais pas certifie SIA 4010 par le PDF seul.
```

## 2. Carte complete du PDF

| Pages PDF | Section | Contenu utile pour IESVE |
|---:|---|---|
| 5-7 | 1 But, references, abreviations | Definit le role de SIA 4010 comme aide SIA 380/2 et procedure de validation logiciel |
| 8 | 2 Application des lignes directrices | Explique les 7 tests, les fichiers externes, les resultats de reference absents du PDF |
| 9-10 | 3.1 Complements SIA 380/2 | Climat, preconditionnement, jours de reference, consignes, stores tissu |
| 10 | 3.2 Methodes systemes techniques | Exige integration des facteurs de l'annexe B et validation SIA 4010 |
| 11-17 | 3.3.1 Ventilation | Debits, fuites, AHU, ventilateurs, recuperation, humidification |
| 18-22 | 3.3.2 Refroidissement | Emission, distribution, stockage, generation, rejet de chaleur, free cooling |
| 23 | 3.3.3 Chauffage | Meme logique que froid, energie fournie par generateur et auxiliaires |
| 24-45 | 3.4 Donnees d'entree techniques | Tables 34-61: inputs produits/process pour ventilation, froid, chaud, ECS, PV |
| 46 | 4.1-4.2 Validation et tests | 7 tests officiels de validation |
| 47-49 | 4.3-4.6 Batiment exemple, classes, procedure | Fichiers externes, classes de validation, procedure SIA |
| 50-52 | Annexe A | Matrice des tests, variantes 2+3 et variantes test 5 |
| 53-56 | Bibliographie, commission | Sources et contexte documentaire |

## 3. Ce que SIA 4010 ajoute a SIA 380/2

### 3.1 Finalite

Source: SIA 4010:2023 FR, page PDF 5, section 1.1.

SIA 4010 sert a faciliter l'application de SIA 380/2:2022, a rassembler des informations eparpillees dans des normes europeennes, et a fournir une procedure de validation pour demontrer qu'un logiciel ou une methode peut realiser les calculs SIA 380/2.

Pour IESVE:

- documenter la version VE et le moteur utilise;
- prouver que les calculs couverts par SIA 380/2 sont representes;
- ne pas remplacer la validation officielle par un script local.

### 3.2 References indispensables

Source: SIA 4010:2023 FR, pages PDF 5-7.

| Reference | Role pour notre checker |
|---|---|
| SIA 380/2:2022 | Norme principale de calcul dynamique du besoin, puissance et energie |
| SIA 384/3 | Pompes a chaleur / energie chauffage |
| SIA 385/2 | Eau chaude sanitaire |
| SIA 387/4:2023 | Eclairage, commandes daylight, puissance specifique |
| SIA 2024:2021 | Donnees d'utilisation des locaux |
| SIA 2028 | Donnees climatiques |
| SIA 2056 | Electricite dans les batiments |
| SN EN 16798 series | Ventilation et refroidissement |
| SN EN 15316 series | Systemes chauffage, stockage, generation, solaire, cogeneration |
| SN EN ISO 52016-1 | Enveloppe, temperature interieure, besoins chauffage/refroidissement |

Point notable:

- Le PDF SIA 4010 renvoie a SIA 387/4:2023 pour certains sujets d'eclairage, alors que SIA 380/2:2022 mentionnait encore SIA 387/4:2017.

## 4. Regles SIA 4010 liees directement a SIA 380/2

### 4.1 Climat d'ete et surchauffe

Source: SIA 4010:2023 FR, page PDF 9, section 3.1.1.

Exigence:

- les simulations de surchauffe et de besoin de refroidissement s'appuient sur les donnees DRY selon SIA 2028;
- les donnees climatiques CH2018 et le scenario RCP 8.5 periode 2035 peuvent ou doivent etre prises en compte selon l'application.

Donnees VE a extraire:

- fichier meteo;
- station climatique;
- scenario climatique;
- periode DRY;
- pas de temps;
- calendrier.

Controle rapport:

| Statut | Condition |
|---|---|
| `EVIDENCE_OK` | Meteo DRY/SIA 2028 documentee et scenario justifie |
| `EVIDENCE_MISSING` | Meteo absente ou non reliee a SIA 2028 |
| `TO_CONFIRM` | Meteo presente mais scenario RCP/2035 non etabli |

### 4.2 Puissance de chauffage dynamique

Source: SIA 4010:2023 FR, page PDF 9, section 3.1.2.

Exigence:

- utiliser la periode de 4 jours la plus froide de janvier du DRY normal;
- utiliser les 14 jours precedents du DRY normal pour le preconditionnement;
- si les 4 jours sont trop proches du debut d'annee, completer avec les derniers jours de decembre;
- eviter les weekends dans la periode de reference via le calendrier.

Exemple donne dans le PDF:

- Zurich-Kloten: reference 24-27 janvier; preconditionnement 10-23 janvier.

Donnees VE a extraire:

- fichier simulation chauffage dimensionnement;
- jours simules;
- periode de preconditionnement;
- calendrier jours ouvrables/weekend;
- consignes;
- puissances horaires.

### 4.3 Puissance de refroidissement dynamique

Source: SIA 4010:2023 FR, page PDF 9, section 3.1.3.

Exigence:

- utiliser des jours de reference chauds pour juin, aout et octobre, avec possibilite d'adapter septembre si plus pertinent;
- utiliser les 14 jours precedents du DRY normal en preconditionnement;
- eviter un jour de reference sur weekend;
- le scenario RCP 8.5 periode 2035 est recommande dans le contexte precise.

Exemple donne dans le PDF pour Zurich-Kloten:

- 21 juin avec preconditionnement 7-20 juin;
- 16 aout avec preconditionnement 2-15 aout;
- 16 octobre avec preconditionnement 2-15 octobre.

Donnees VE a extraire:

- puissance refroidissement horaire par zone;
- temperature interieure;
- gains internes;
- strategie de protection solaire;
- meteo;
- calendrier;
- preuve de preconditionnement.

### 4.4 Consignes et usages SIA 2024

Source: SIA 4010:2023 FR, page PDF 10, section 3.1.4.

Exigence:

| Usage SIA 2024 | Decalage courbe basse | Decalage courbe haute | Impact |
|---|---:|---:|---|
| 3.04 salle de guichets | +1 K | non indique | consigne / limite adaptee |
| 5.01 a 5.03 magasins | +1 K | non indique | consigne / limite adaptee |
| 6.03 et 6.04 cuisines | +1 K | +2 K | consignes chaud/froid adaptees |
| 9.01 production travail grossier | +3 K | +4 K | consignes chaud/froid adaptees |
| gymnases, fitness, piscines, vestiaires, douches | limites constantes | limites constantes | courbes non dependantes de l'habillement saisonnier |

Donnees VE a extraire:

- usage SIA 2024 de chaque zone;
- consignes chauffage/refroidissement;
- type de confort utilise;
- calendrier/profil d'occupation.

### 4.5 Stores en tissu et g total

Source: SIA 4010:2023 FR, page PDF 10, section 3.1.5.

Exigence:

- pour les stores tissu, les coefficients solaires directs/diffus sont assimiles aux valeurs globales du store;
- alternative acceptee: lorsque la protection solaire est active, remplacer le g du vitrage par le g total vitrage + protection solaire, calcule par SN EN ISO 52022-3 ou ISO 15099.

Donnees VE a extraire:

- type de protection solaire;
- etat actif/inactif;
- seuil de commande;
- g vitrage;
- g total si disponible;
- reflectance/transmittance du store.

## 5. Conditions des methodes systemes techniques

Source: SIA 4010:2023 FR, page PDF 10, section 3.2.

Pour les besoins d'energie des systemes techniques, une methode est acceptable si:

- elle integre les calculs des systemes concernes avec les facteurs d'influence de SIA 380/2 annexe B;
- elle justifie une validation SIA 4010 pour les systemes consideres;
- ses entrees atteignent au minimum les exigences de SIA 380/2 annexe A, A.3 et des normes europeennes citees;
- si le modele a d'autres parametres d'entree, il faut demontrer une precision au moins equivalente.

Implication:

```text
Un modele VE peut etre "pret pour SIA 4010" si toutes les donnees sont presentes.
Il ne peut etre "valide SIA 4010" que si le moteur/methode a passe les tests officiels requis.
```

## 6. Ventilation - exigences a respecter

Sources: SIA 4010:2023 FR, pages PDF 11-17 et 24-28; tableaux 1-23 et 34-35.

### 6.1 Energie finale ventilation

Le calcul ventilation doit couvrir:

- pertes thermiques de distribution d'air;
- energie electrique de transport d'air;
- conditionnement de l'air: chauffage, refroidissement, humidification, deshumidification;
- auxiliaires;
- etats effectifs de l'air fourni;
- bilans de flux massiques en cas de fuites.

### 6.2 Emission et controle de l'air fourni

Tables 1-2, page PDF 11.

| Identifiant | Valeurs reconnues | Ce que VE doit fournir |
|---|---|---|
| `SUP_AIR_TEMP_CTRL` | `NO_CTRL`, `CONST`, `ODA_COMP`, `LOAD_COMP` | mode de regulation temperature soufflage |
| `SUP_AIR_FLW_CTRL` | `ODA`, `LOAD` | regulation debit selon air neuf seul ou charge |

### 6.3 Fuites et etancheite

Tables 3-6, pages PDF 12-13.

| Element | Classe / valeur | Usage checker |
|---|---|---|
| Conduits inconnus | 1.45 | facteur de correction fuite conduits |
| Conduits A | 1.18 | idem |
| Conduits B | 1.06 | idem, defaut batiment neuf |
| Conduits C | 1.02 | idem |
| Conduits D | 1.00 | cas special |
| CTA L3 | 1.10 | facteur fuite caisson |
| CTA L2 | 1.04 | facteur fuite caisson |
| CTA L1 | 1.01 | defaut batiment neuf |

Statut code:

- ces valeurs sont ajoutees dans `SIA4010_LEAKAGE_FACTORS`;
- le checker doit d'abord extraire ou demander les classes d'etancheite.

### 6.4 Ventilateurs et systemes

Tables 7-10, pages PDF 13-14.

| Sujet | Valeurs reconnues | Donnees VE attendues |
|---|---|---|
| Regulation debit | `NO_CTRL`, `ON/OFF_CTRL`, `MULTI_STAGE`, `VARIABLE` | strategie de regulation |
| Type systeme | `SINGLE_ZONE`, `MULTI_ZONE` | monozone/multizone |
| Regulation ventilateur | `NO_CTRL`, `CONST_PRES`, `MIN_PRES`, `DIRECT` | fan control |
| Position moteur | `IN_AIR`, `OUTS_AIR` | bilan thermique et energie |

### 6.5 Recuperation, gel et humidification

Tables 11-23, pages PDF 14-17.

| Sujet | Valeurs reconnues | Donnees VE attendues |
|---|---|---|
| Prechauffage sol | `NO_CTRL`, `BYPASS` | prechauffage/pre-refroidissement par sol |
| Recyclage air | `FIX`, `VARIABLE` | part air recycle |
| Recuperation chaleur | `PLATE`, `ROT_NH`, `ROT_HYG`, `ROT_SORP`, `PUMP_CIRC`, `OTHER` | type recuperateur |
| Regulation recuperation | `NO_CTRL`, `BYPASS`, `SPEED`, `HYDR` | strategie selon type |
| Protection gel | `PREH`, `BYPASS`, `RECIRC` | strategie antigel |
| Degivrage | `DIRECT`, `INDIRECT` | regulation degivrage |
| Position ventilateurs vs recuperateur | `UP_HR`, `DOWN_HR` | emplacement alimentation/extraction |
| Type humidificateur | `CONTACT`, `ROT_SPRAY`, `HI_PRES`, `HYBRID`, `STEAM`, `OTHER` | type humidification |
| Controle humidificateur | `NO_CTRL`, `ON_OFF`, `SPEED` | regulation |
| Energie vapeur | `HUM_CR_EL`, `HUM_CR_GAS`, `HUM_CR_SOL`, `HUM_CR_OTHER` | vecteur energetique |
| Emplacement CTA | `CND`, `NC` | zone conditionnee ou non |

### 6.6 Inputs techniques ventilation

Tables 34-35, pages PDF 24-28.

Familles d'entrees a obtenir:

- facteurs de fuite conduits et caisson;
- debits nominaux et par etape air fourni/air repris;
- nombre d'etapes, rapport minimal de debit;
- efficacites de recuperation chaleur/humidite;
- debits/vitesses nominales de recuperation;
- constantes de dependance a vitesse, rotation et humidite;
- efficacites batteries froid/chaud;
- rendements, pressions et puissances ventilateurs;
- surfaces et U-values de caissons;
- puissance rotor/pompe de recuperation;
- puissance regulateurs/capteurs/actionneurs;
- pertes thermiques conduits vers zones conditionnees/non conditionnees;
- debits de conception par zone;
- consignes de soufflage min/max;
- limites de degivrage et pertes de charge de conception.

Controle checker:

| Niveau | Action |
|---|---|
| Minimum | detecter si ces donnees sont absentes et produire `EVIDENCE_MISSING` |
| Avance | mapper valeurs VE vers identifiants SIA4010 |
| Officiel | exporter les donnees necessaires au test SIA 4010 correspondant |

## 7. Refroidissement - exigences a respecter

Sources: SIA 4010:2023 FR, pages PDF 18-22 et 29-36; tableaux 24-33 et 36-48.

### 7.1 Ce que le calcul doit inclure

Le refroidissement doit representer:

- pertes/gains thermiques de distribution de froid;
- energie de transport des fluides;
- conditionnement des fluides;
- emission de froid dans le local ou via batterie d'air;
- stockage de froid si present;
- generation de froid;
- rejet de chaleur;
- free cooling si disponible;
- auxiliaires et regulation.

### 7.2 Identifiants de controle froid

Tables 24-33, pages PDF 18-22.

| Sujet | Valeurs reconnues |
|---|---|
| Temperature generation froid | `CONST`, `VARIABLE` |
| Temperature distribution froid | `CONST`, `ODA_COMP`, `MAX_TMP` |
| Debit distribution froid | `CONST`, `VARIABLE` |
| Distribution energie en manque de capacite | `NO_CTRL`, `PRIO` |
| Pompes | codes 0 a 4: non regulee, marche/arret, multi-etages, vitesse variable selon pression constante/variable |
| Type generateur froid | `COMP`, `ABS`, `OTHER` |
| Rejet chaleur | `AIR_C_COND`, `DRY`, `WET`, `HYBRID`, `OTHER` |
| Free cooling | `YES`, `NO` |
| Rejet hybride | `TEMP`, `MAX_POWER` |

### 7.3 Inputs froid

Tables 36-48, pages PDF 29-36.

Familles d'entrees a obtenir:

- consignes temperature generation et distribution;
- courbes/limites de compensation exterieure;
- facteur de ponderation electricite;
- caracteristiques d'emission et regulation;
- donnees de distribution hydraulique et pompes;
- stockage froid: type, volume, pertes, emplacement, temperature, pompes, echangeurs;
- generation froid: puissance nominale, EER nominal, EER part-load A-D, temperatures evaporateur/condenseur, auxiliaires;
- rejet chaleur: limites, puissance specifique, temperature humide/sec, free cooling;
- nombre de generateurs et logique de pilotage.

Controle checker:

- verifier si VE expose le type de production froid;
- extraire EER/SEER ou courbe part-load si disponible;
- produire `NOT_CHECKABLE` si les donnees ne peuvent pas etre reliees aux tables 36-48;
- ne jamais utiliser un rendement HVAC unique.

## 8. Chauffage - exigences a respecter

Sources: SIA 4010:2023 FR, pages PDF 23 et 36-44; tableaux 49-59.

### 8.1 Logique generale

Le PDF indique que l'emission, la distribution et le stockage suivent la meme logique que le refroidissement. Le generateur de chaleur fournit l'energie thermique necessaire aux reseaux de chauffage et, le cas echeant, a l'ECS.

### 8.2 Identifiants BACS / regulation

Table 49, page PDF 37.

| Identifiant | Domaine |
|---|---|
| `HEAT_EM_CTRL_DEF` | regulation emission chaleur |
| `HEAT_EM_CTRL_TABS` | activation thermique en chauffage |
| `HEAT_DIS_CTRL_TMP` | regulation temperature distribution chaleur |
| `HEAT_DIS_CTRL_PMP` | regulation pompes distribution |
| `HEAT_DIS_CTRL` | intermittence emission/distribution |
| `HEAT_GEN_CTRL_CD` | generateurs combustion / chauffage urbain |
| `HEAT_GEN_CTRL_HP` | pompe a chaleur |
| `HEAT_GEN_CTRL_OU` | unite exterieure |
| `HEAT_GEN_CTRL_SEQ` | cascade generateurs |
| `HEAT_TES_CTRL` | stockage energie thermique |

### 8.3 Inputs chauffage

Tables 50-59, pages PDF 37-44.

Familles d'entrees a obtenir:

- stockage chaud: type, usage, combustible, volume, pertes, regulation, temperatures;
- localisation stockage, connexion au generateur, nombre d'unites;
- generateurs: combustible, type, bruleur, emplacement, regulation, circuit;
- charges et puissances par chauffage/froid/ventilation/ECS;
- periodes et durees de fonctionnement;
- temperatures exterieures, ambiantes, eau depart/retour;
- energie recue par generateur;
- puissance pleine charge et charge partielle;
- rendements a pleine charge/part load si chaudiere;
- PAC calculee selon methode detaillee SIA 384/3 avec pas horaire;
- solaire thermique: surface, rendement, coefficients de pertes, debit, pompes, orientation;
- cogeneration: chaleur utile, puissance electrique, auxiliaires, rendements, veille, regulation.

Controle checker:

- extraire systeme chauffage et generateur depuis VE;
- identifier si chauffage alimente ventilation/ECS;
- demander preuve externe si VE ne contient pas les courbes/rendements requis;
- separer chauffage, ECS, ventilation et auxiliaires dans le rapport.

## 9. Eau chaude, electricite generale, eclairage, PV

Sources: SIA 4010:2023 FR, pages PDF 44-45; tableaux 60-61.

### 9.1 Eau chaude sanitaire

Le besoin de chaleur et d'energie auxiliaire ECS est calcule selon SIA 385/2.

Pour IESVE:

- identifier si ECS est couplee au systeme chauffage;
- si oui, fournir cycles de charge horaires au systeme de distribution;
- tracer source SIA 385/2.

### 9.2 Electricite generale et usages

Le PDF renvoie:

- a SIA 2056 pour les installations techniques generales;
- a SIA 2024 pour appareils et usages;
- a SIA 387/4 pour l'eclairage.

Pour IESVE:

- ne pas utiliser de seuil universel W/m2;
- extraire puissance, profils et type de commande;
- lier chaque zone a un usage SIA 2024.

### 9.3 Photovoltaique

Tables 60-61, page PDF 45.

Donnees PV a extraire:

- nombre de modules;
- aire totale des modules;
- azimut;
- inclinaison;
- coefficient de puissance crete;
- facteur de performance systeme.

## 10. Validation officielle SIA 4010

Sources: SIA 4010:2023 FR, pages PDF 46-49; tableaux 62-63.

### 10.1 Les 7 tests

| Test | Domaine | Ce que le checker doit preparer |
|---|---|---|
| 1 | Enveloppe de base EN ISO 52016-1 / ASHRAE 140 | Cas test officiel, sorties horaires, comparaison reference |
| 2 | Protection solaire SIA 387/4 + SIA 380/2 annexe A | Store, commande, climat CH, usage CH, infiltration |
| 3 | Eclairage SIA 387/4 | daylight control, puissance, energie eclairage |
| 4 | Climatisation mono-piece air seul | amphitheatre, VAV/CO2, batteries, air fourni, temperatures |
| 5 | CTA multizone complexe | bureaux/salles reunion, rotor, humidification, variantes |
| 6 | Ventilation trois niveaux | restaurant/cuisine, recuperation chaleur, debit constant, debordement |
| 7 | Emission/distribution/stockage/production chaud/froid | energies finales, pompes, stockages, generateurs, besoins totaux |

### 10.2 Classes de validation

| Classe | Usage couvert | Tests requis |
|---|---|---|
| 1A | besoin froid + puissance thermique de base, stores simples sans suivi solaire | 1 + 2A |
| 1B | meme usage avec stores a lamelles | 1 + 2 |
| 2A | eclairage SIA 387/4 + besoins chaud/froid, stores simples | 1 + 2A + 3A a 3F |
| 2B | meme usage avec stores a lamelles | 1 a 3 |
| 3 | humidification / deshumidification | 1 + 4 a 6 |
| 4A | puissance systeme + energie chaud/froid, stores simples | 1 + 2A + 3A a 3F + 4 a 7 |
| 4B | meme usage avec stores a lamelles | 1 a 7 |
| 5 | energie chaud/froid sur profils de besoins existants | 7 |

### 10.3 Infrastructure officielle obligatoire

Sources: pages PDF 8, 47-49.

Preuves indispensables:

- specifications officielles de chaque test;
- resultats de reference;
- fichier Excel officiel d'evaluation;
- documentation du batiment exemple;
- plans DXF, modeles IFC et charge du test 7 pour tests 4 a 7;
- fichier d'evaluation rempli par le candidat;
- feedback ou confirmation de la sous-commission;
- classe de validation visee.

Statut a appliquer:

| Situation | Statut rapport |
|---|---|
| Aucun fichier officiel joint | `NOT_CHECKABLE` |
| Fichiers joints mais incomplets | `EVIDENCE_INCOMPLETE` |
| Resultats exportes sans comparaison officielle | `REFERENCE_COMPARISON_MISSING` |
| Comparaison officielle favorable et classe confirmee | `VALIDATED` |

## 11. Variantes officielles de tests

Source: SIA 4010:2023 FR, page PDF 52, tableaux 65-66.

### 11.1 Tests 2 + 3

| Variante | Protection solaire | Regulation solaire | Regulation eclairage |
|---|---|---:|---:|
| 3A | store tissu | aucune | 1 |
| 3B | store tissu | aucune | 2 |
| 3C | store tissu | aucune | 3 |
| 3D | store tissu | aucune | 4 |
| 3E | store tissu | aucune | 5 |
| 3F | store tissu | aucune | 6 |
| 3G | stores a lamelles | 1 | 1 |
| 3H | stores a lamelles | 1 | 3 |
| 3I | stores a lamelles | 2 | 1 |
| 3J | stores a lamelles | 2 | 3 |
| 3K | stores a lamelles | 3 | 1 |
| 3L | stores a lamelles | 3 | 3 |

### 11.2 Test 5

| Variante | FAN_CTRL | Recuperateur chaleur | Humidificateur |
|---|---|---|---|
| 5A | `MIN_PRES` | hygroscopique | adiabatique |
| 5B | `CONST_PRES` | hygroscopique | adiabatique |
| 5C | `CONST_PRES` | non hygroscopique | adiabatique |
| 5D | `CONST_PRES` | non hygroscopique | vapeur |

## 12. Index des tableaux et action checker

| Table | Pages | Domaine | Action checker |
|---:|---:|---|---|
| 1-2 | 11 | temperature/debit air fourni | mapper controles ventilation |
| 3-4 | 12 | fuites conduits | extraire classe et appliquer facteur |
| 5-6 | 13 | fuites caisson ventilation | extraire classe AHU et appliquer facteur |
| 7-10 | 13-14 | debits, type systeme, fan control, moteur | mapper regulation ventilateur |
| 11-13 | 14-15 | temperature soufflage, prechauffage sol, recyclage | mapper controls AHU |
| 14-19 | 15-16 | recuperation chaleur, gel, position ventilateurs | mapper recuperateur/degivrage |
| 20-23 | 16-17 | humidification, vecteur, emplacement CTA | mapper humidification |
| 24-29 | 18-20 | controles froid, distribution, pompes | mapper froid hydraulique |
| 30-33 | 21-22 | generateur froid, rejet chaleur, free cooling | mapper production froid |
| 34-35 | 24-28 | inputs produit/design ventilation | evidence pack ventilation |
| 36-38 | 29-31 | froid et emission/regulation | evidence pack froid |
| 39-42 | 32 | ECS/distribution, pompes, stockage froid | evidence pack distribution/stockage |
| 43-48 | 33-36 | stockage froid et generation froid | evidence pack stockage/generation |
| 49-53 | 37-42 | chauffage, stockage chaud, chaudiere/generateur | evidence pack chauffage |
| 54-55 | 42-43 | solaire thermique | evidence pack solaire thermique |
| 56-59 | 43-44 | cogeneration | evidence pack CHP |
| 60-61 | 45 | photovoltaique | evidence pack PV |
| 62 | 46 | tests validation | structure SIA4010 checker |
| 63 | 48 | classes validation | mapping classe -> tests |
| 64 | 50-51 | matrice detaillee tests | documentation resultats attendus |
| 65 | 52 | variantes tests 2+3 | mapping protection/eclairage |
| 66 | 52 | variantes test 5 | mapping AHU multizone |

## 13. Architecture de controle recommandee dans le script

### 13.1 Trois couches de verdict

| Couche | Verdicts autorises | Exemple |
|---|---|---|
| Readiness modele VE | `OK`, `MISSING`, `INCOMPLETE`, `INCONSISTENT` | classe AHU absente |
| SIA 380/2 direct | `PASS`, `FAIL`, `NOT_APPLICABLE`, `EXTERNAL_STANDARD_REQUIRED` | Uw fenetre, g vitrage |
| SIA 4010 validation | `NOT_CHECKABLE`, `EVIDENCE_INCOMPLETE`, `VALIDATED` | fichiers Excel officiels manquants |

### 13.2 Pseudo-logique

```text
if no official SIA4010 evaluation files:
    SIA4010 status = NOT_CHECKABLE
else:
    determine requested validation class
    list required tests
    verify official files exist for each test
    verify candidate results were transferred
    verify official comparison status
    only then mark VALIDATED
```

### 13.3 Ce que le checker doit exporter de VE

| Famille | Sorties minimales |
|---|---|
| Geometrie | zones, surfaces, vitrages, orientations |
| Enveloppe | U-values, g-values, ombrages, constructions |
| Meteo | DRY, station, scenario, calendrier |
| Simulation | pas de temps, preconditionnement, courbes horaires |
| Ventilation | debits, controles, fuites, recuperation, humidification |
| Froid | puissance, EER/SEER/part-load, distribution, stockage, rejet |
| Chauffage | generateur, PAC/chaudiere, stockage, distribution, auxiliaires |
| ECS | demande, cycles horaires, couplage chauffage |
| Eclairage | puissance, commande daylight, profils |
| PV | modules, orientation, inclinaison, performance |
| SIA4010 | classe visee, tests requis, fichiers officiels, resultats |

## 14. Impacts immediats dans notre code

Deja fait:

- `config.py` contient `SIA4010_VALIDATION_TESTS`, `SIA4010_VALIDATION_CLASSES`, `SIA4010_REQUIRED_EVIDENCE`.
- `config.py` contient maintenant les complements climatiques, identifiants techniques et facteurs de fuite extraits du PDF.
- `sia4010_checker.py` garde les tests en `NOT_CHECKABLE` sans preuve officielle.
- `excel_report.py` genere maintenant l'onglet `SIA4010 READINESS` avec readiness modele VE, statuts officiels, preuves requises et sources PDF.

A faire ensuite:

- ajouter un dossier attendu `sia4010_evidence/`;
- ajouter un mapping classe -> tests requis dans le rapport;
- detecter les champs VE disponibles par sous-systeme;
- produire une checklist de preuves manquantes par test;
- si fichiers Excel officiels sont fournis, lire leur statut sans inventer les tolerances.

## 15. Checklist manager

Pour pouvoir presenter un dossier SIA 4010 professionnel, il faudra:

1. Choisir la classe de validation visee.
2. Obtenir les specifications officielles des tests requis.
3. Importer ou reconstruire les modeles de test officiels dans IESVE.
4. Executer les simulations VE avec meteo, calendrier et preconditionnement corrects.
5. Exporter les resultats horaires/agreges demandes.
6. Remplir les fichiers Excel officiels SIA.
7. Joindre les comparaisons aux resultats de reference.
8. Joindre la confirmation ou le statut de validation.
9. Dans le rapport modele client, distinguer clairement readiness modele et validation officielle.

## 16. Decision a retenir

Le present PDF donne une excellente base pour definir:

- les donnees a extraire;
- les controles de coherence;
- les tests requis;
- les preuves a demander;
- les classes de validation;
- les variantes de tests.

Mais il ne donne pas:

- les fichiers officiels d'evaluation;
- les resultats de reference;
- les tolerances numeriques d'acceptation;
- une certification automatique du modele client.

Donc notre checker doit etre ferme:

```text
SIA 380/2 = controle modele/projet avec valeurs directes + preuves externes.
SIA 4010 = validation methode/logiciel avec preuves officielles.
```
