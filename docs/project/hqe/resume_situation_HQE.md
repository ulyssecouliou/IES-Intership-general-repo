HQE Energy Compliance Report – Traduction française complète
Objet du document
Ce document étudie la possibilité d'utiliser IESVE dans le cadre des projets français soumis à la réglementation HQE / RE2020.
L'objectif n'est pas de remplacer les outils réglementaires français certifiés mais d'évaluer comment VE pourrait :

aider à la conception,
vérifier des critères de conformité,
réaliser des simulations avancées,
produire des rapports HQE,
faciliter l'export vers un logiciel certifié RE2020. [CodeInterpreter | Undefined]


Résumé exécutif
VE pourrait potentiellement contribuer à plusieurs domaines de la conformité HQE :
Énergie
Vérification des performances énergétiques du bâtiment. [CodeInterpreter | Undefined]
Confort d'été
Analyse de la surchauffe estivale sans recours excessif à la climatisation. [CodeInterpreter | Undefined]
Éclairage naturel
Évaluation de l'autonomie lumineuse (sDA). [CodeInterpreter | Undefined]
Vue vers l'extérieur
Évaluation de la qualité de la vue grâce à des techniques de ray tracing. [CodeInterpreter | Undefined]

Cependant la RE2020 impose l'utilisation du moteur officiel :
Th-BCE 2020
Ce moteur est développé par le CSTB.
Tous les calculs réglementaires d'énergie et de confort doivent être effectués par ce moteur. [CodeInterpreter | Undefined]

Seuls les logiciels certifiés qui intègrent nativement Th-BCE peuvent produire :

les attestations RE2020,
les justificatifs réglementaires,
les documents officiels nécessaires aux permis de construire. [CodeInterpreter | Undefined]

Exemples :

ClimaWin
Pleiades
Perrenoud
Visual TTH

 [CodeInterpreter | Undefined]

Les trois piliers de la RE2020
1. Performance énergétique
Réduction importante de la consommation énergétique du bâtiment. [CodeInterpreter | Undefined]

2. Impact carbone
Évaluation du cycle de vie complet :

matériaux,
construction,
exploitation,
démolition. [CodeInterpreter | Undefined]


3. Confort d'été
Capacité à résister aux vagues de chaleur sans climatisation intensive. [CodeInterpreter | Undefined]

Partie Énergie
La RE2020 adopte une philosophie :

Fabric First

Autrement dit :
Avant d'optimiser les équipements techniques, il faut optimiser :

l'enveloppe,
les vitrages,
l'isolation,
l'étanchéité,
l'orientation,
la protection solaire. [CodeInterpreter | Undefined]


Critère Bbio
Définition
Bbio = Besoin bioclimatique.
Mesure les besoins intrinsèques du bâtiment indépendamment des systèmes HVAC. [CodeInterpreter | Undefined]
Prend en compte :

chauffage,
refroidissement,
éclairage artificiel. [CodeInterpreter | Undefined]


Condition :
Plain TextBbio ≤ Bbio_maxShow more lines
La RE2020 a réduit ce seuil d'environ 30 % comparé à la RT2012. [CodeInterpreter | Undefined]

Critère Cep
Définition
Cep = Consommation d'énergie primaire.
Inclut :

chauffage,
refroidissement,
eau chaude sanitaire,
éclairage,
ventilation,
auxiliaires. [CodeInterpreter | Undefined]


Condition :
Plain TextCep ≤ Cep_maxShow more lines
Valeur cible typique :
Plain Text≈ 100 kWhEP/m².anShow more lines
 [CodeInterpreter | Undefined]

Critère Cep,nr
Définition
Part de la consommation provenant d'énergies non renouvelables. [CodeInterpreter | Undefined]

Condition :
Plain TextCep,nr ≤ Cep,nr_maxShow more lines
Valeur typique :
Plain Text≈ 55 kWhEP/m².anShow more lines
 [CodeInterpreter | Undefined]

Conséquence :
Les chaudières gaz deviennent très difficiles à justifier dans les logements neufs. [CodeInterpreter | Undefined]

Exigence de vitrage
Obligation réglementaire :
Plain TextSurface vitrée ≥ 1/6 de la surface habitableShow more lines
soit :
Plain Text16,7 %Show more lines
minimum. [CodeInterpreter | Undefined]

Étanchéité à l'air
Maison individuelle :
Plain TextQ4Pa-surf < 0.60 m³/(h.m²)Show more lines
Logement collectif :
Plain TextQ4Pa-surf < 1.00 m³/(h.m²)Show more lines
 [CodeInterpreter | Undefined]

Ponts thermiques
Coefficient global :
Plain TextΨ9 ≤ 0.28 W/(m².K)Show more lines
 [CodeInterpreter | Undefined]

Pourquoi VE n'est pas accepté directement ?
Parce que :
Th-BCE
Impose :

profils d'occupation fixes,
gains internes fixes,
météo imposée,
hypothèses carbone imposées. [CodeInterpreter | Undefined]


VE / EnergyPlus
Permettent :

modifier les horaires,
modifier les occupants,
modifier la ventilation,
modifier les scénarios. [CodeInterpreter | Undefined]


La RE2020 considère donc VE comme un :
Plain TextOutil de conceptionShow more lines
et non comme un :
Plain TextOutil réglementaireShow more lines
 [CodeInterpreter | Undefined]

Titre V
Le Titre V permet d'introduire des solutions innovantes non prévues par la réglementation. [CodeInterpreter | Undefined]

Titre V Opération
Appliqué à un projet unique. [CodeInterpreter | Undefined]

Titre V Système
Pour un produit ou un système commercial. [CodeInterpreter | Undefined]

Titre V Réseau
Pour les réseaux de chaleur et de froid. [CodeInterpreter | Undefined]

Temps d'approbation :

3 à 6 mois minimum,
parfois plus d'un an. [CodeInterpreter | Undefined]


Confort d'été RE2020
La RE2020 repose sur l'indicateur :
DH
Degrés-heures d'inconfort. [CodeInterpreter | Undefined]

Le moteur calcule heure par heure :
Plain TextTempérature intérieure-Température limite``Show more lines
 [CodeInterpreter | Undefined]

Limites utilisées :
Nuit :
Plain Text26°CShow more lines
Jour :
Plain Text26 à 28°CShow more lines
selon les conditions météorologiques précédentes. [CodeInterpreter | Undefined]

Critères de conformité
DH < 350
Conforme. [CodeInterpreter | Undefined]

350 ≤ DH ≤ DHmax
Conforme avec pénalité énergétique fictive. [CodeInterpreter | Undefined]

DH > DHmax
Non conforme.
Le permis peut être refusé. [CodeInterpreter | Undefined]

Particularités du calcul DH
Le moteur impose :
Canicule fictive
Séquence extrême de 8 jours ajoutée dans le calcul. [CodeInterpreter | Undefined]

Stores et protections solaires
Les utilisateurs ne peuvent pas définir librement leur fonctionnement.
Des règles automatiques sont appliquées. [CodeInterpreter | Undefined]

Ventilation nocturne
Prise en compte avec réduction de performance si le contexte urbain empêche l'ouverture des fenêtres. [CodeInterpreter | Undefined]

Éclairage naturel (Daylighting)
Exigence par défaut :
Plain TextSurface vitrée ≥ 1/6 de la surface habitableShow more lines
 [CodeInterpreter | Undefined]

Méthode alternative
Simulation d'autonomie lumineuse.
Deux objectifs :
Critère 300 Lux
Au moins :
Plain Text50 % de la surfaceShow more lines
doit recevoir :
Plain Text300 luxShow more lines
pendant plus de :
Plain Text50 % des heures de jourShow more lines
 [CodeInterpreter | Undefined]

Critère 100 Lux
Au moins :
Plain Text95 % de la surfaceShow more lines
doit recevoir :
Plain Text100 luxShow more lines
pendant plus de :
Plain Text50 % des heures de jourShow more lines
 [CodeInterpreter | Undefined]

Le rapport indique que RadianceIES semble déjà capable de réaliser la majorité de ces calculs. [CodeInterpreter | Undefined]

Vue extérieure (Clear View)
Nouvelle exigence RE2020.
Un occupant situé à au moins :
Plain Text1 mètre de la façade intérieure``Show more lines
doit disposer d'une vue directe vers l'extérieur depuis une pièce principale. [CodeInterpreter | Undefined]

Paramètres évalués
Transmission lumineuse
Quantité de lumière passant à travers le vitrage. [CodeInterpreter | Undefined]

Facteur solaire g
Part de l'énergie solaire traversant le vitrage. [CodeInterpreter | Undefined]

Ray Tracing
Le rapport conclut que l'utilisation du ray tracing est pertinente pour :

la vue vers l'extérieur,
l'éclairage naturel,
les ombres,
l'éblouissement,
le confort visuel. [CodeInterpreter | Undefined]


Ce qui est le plus intéressant pour ton Navigator VE
Si j'étais en train de développer le Navigator HQE/RE2020 chez IESVE, je construirais les modules suivants :
Plain TextHQE Navigator│├── Energy Compliance│   ├── Bbio│   ├── Cep│   ├── Cep,nr│   ├── Glazing Ratio│   ├── Airtightness│   └── Thermal Bridges│├── Summer Comfort│   ├── DH│   ├── Overheating│   ├── Solar Shading│   └── Night Ventilation│├── Daylight│   ├── 100 Lux│   ├── 300 Lux│   ├── DA│   └── sDA│├── Clear View│   ├── View Out│   ├── Ray Tracing│   └── Visibility Checks│└── Reporting    ├── Excel    ├── PDF    ├── Pass/Fail    └── RecommendationsShow more lines

Conclusion du rapport
La conclusion implicite du document est très claire :

IESVE ne peut pas remplacer le moteur réglementaire français Th‑BCE 2020.

Mais :

IESVE pourrait devenir une plateforme extrêmement intéressante de pré-vérification HQE/RE2020, d'optimisation de conception, de daylighting, de confort d'été et de génération de rapports de conformité destinés aux équipes de conception. [CodeInterpreter | Undefined]

Pour ton stage, cette conclusion est probablement la plus importante : le meilleur produit n'est pas un clone du moteur RE2020, mais un Navigator HQE/RE2020 intelligent qui automatise les vérifications réalisables à partir des données du modèle VE. [CodeInterpreter | Undefined]