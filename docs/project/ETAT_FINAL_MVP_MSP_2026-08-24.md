# État de clôture MVP / MSP au 24 août 2026

## Décision de livraison

Le produit est un **MVP livrable pour revue interne et démonstration client
encadrée**. Il exécute l'audit depuis IESVE, produit les rapports Excel/PDF,
sépare les non-conformités des preuves manquantes et conserve les limites de
revendication. Il ne constitue pas un certificat SIA.

Le **MSP est partiellement atteint**, mais ne doit pas être déclaré terminé.
Les contrôles enrichis SIA 380/2, l'ingestion de preuves, les sorties APS et le
dossier auditable sont présents. Restent hors clôture logicielle locale : les
valeurs à attester par un relecteur, les corrections physiques du modèle, les
simulations IESVE réelles et l'attestation SIA 4010.

## État du dernier parcours client réel

Le rapport IESVE régénéré le 24 août 2026 à 13:51 est techniquement valide :

- PDF de 14 pages contrôlé visuellement ;
- classeur de 27 feuilles ouvert sans erreur de formule évidente ;
- trois constats de confort d'été déterminés et auditables ;
- dix preuves manquantes séparées des constats bloquants ;
- verdict du modèle `SIA_compatible_model_TEST` : **NOT COMPLIANT**.

Ce verdict ne remet pas en cause la capacité du produit à produire un rapport.
Il décrit le modèle analysé : trois locaux dépassent la limite de confort d'été
et des preuves ventilation, éclairage, HVAC et opérabilité restent à fournir.

## État des gabarits

### Gabarits de preuves client

**Terminé côté produit : 16/16.** Tous les CSV sous `templates/evidence/` sont :

- enregistrés dans `swiss_sia.evidence_bootstrap.TEMPLATE_TARGETS` ;
- générés par l'action Run-button de préparation du dossier de preuves ;
- nommés avec l'identifiant du projet actif ;
- munis d'un état de revue et d'une provenance ;
- contrôlés automatiquement contre les dérives d'inventaire.

Ils restent volontairement remplis avec des marqueurs `pending` et des champs
relecteur. Un gabarit complet n'est pas une preuve acceptée : les valeurs,
sources, dates et signatures doivent être fournies par les responsables.

### Configurations et gabarits de modèles SIA 4010

**Structure terminée, qualification réelle non terminée.** Les huit classes et
les 24 variantes officielles sont cataloguées, les contrats d'entrée et les
manifestes de qualification existent, et les voies de vérification échouent de
manière conservative. Cependant, tous les templates/cas n'ont pas été créés,
simulés, relus et enregistrés dans IESVE 2025 avec des résultats APS qualifiés.
Ils ne peuvent donc pas être déclarés « validés SIA 4010 ».

## Périmètre MVP fermé

- lancement depuis le bouton Run de VEScripts via le Hub ;
- extraction conservatrice VE/CDB/APS ;
- contrôles SIA 380/2 et statut de readiness SIA 4010 séparés ;
- verdict fail-closed et absence de faux `PASS` ;
- rapport PDF client et classeur Excel auditable ;
- assistant de preuves et 16 gabarits synchronisés ;
- evidence pack, journal d'audit et actions de remédiation ;
- huit classes et 24 variantes SIA 4010 recensées ;
- tests Python et porte de release locale ;
- documentation d'exploitation et limites de revendication.

## Écarts restant avant MSP complet

| Écart | Nature | Condition de fermeture |
| --- | --- | --- |
| Surchauffe des trois locaux du modèle test | Modèle / simulation | Corriger le modèle, relancer ApacheSim annuel et respecter la limite applicable |
| Dix preuves client manquantes | Relecteur / projet | Remplir et accepter les CSV projet sans valeur inventée |
| Comparaison globale marquée `DEMO_illustrative_calc` | Relecteur / calcul externe | Fournir le calcul projet-référence réel et signé |
| Journées de dimensionnement chaud/froid | IESVE réel | Exécuter les runs dédiés avec préconditionnement et archiver les résultats |
| Templates/cas SIA 4010 non tous qualifiés | IESVE réel | Capability check, mutation, read-back, simulation, APS et revue pour chaque portée revendiquée |
| Attestation SIA 4010 | Autorité externe | Dossier officiel complet et décision de la sous-commission compétente |
| PV et bilan énergétique MSP étendu | Produit | Implémentation source-tracée et tests dédiés si ce périmètre est requis commercialement |

## Définition honnête de « fini » pour la fin de semaine

Le livrable logiciel peut être remis comme **MVP/MSP de readiness et d'audit**
si les tests et la porte de release sont verts et si un smoke test Run-button
IESVE est archivé. Il ne peut pas être remis comme logiciel officiellement
validé SIA 4010 ni comme preuve que le modèle test est conforme.

La checklist opérationnelle de remise est
`docs/project/RELEASE_ACCEPTANCE_CHECKLIST.md`.
