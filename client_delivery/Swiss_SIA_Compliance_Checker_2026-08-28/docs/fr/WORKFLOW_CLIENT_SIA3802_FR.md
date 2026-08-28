# Mode opératoire client SIA 380/2

## 1. Avant de lancer

1. Ouvrir et enregistrer le bon projet dans IESVE 2025.
2. Vérifier que le dernier APS annuel correspond au modèle actif.
3. Fermer dans Excel/PDF les anciens rapports portant le même nom.
4. Réunir les documents sources listés dans la section « À demander ».

## 2. Saisir les informations du rapport

Depuis la fenêtre Scripts de VE, lancer directement
`Run_VE_Swiss_Compliance.py`. Renseigner le client, le projet, l'adresse, la
référence, l'auteur et la stratégie propre au bâtiment : protections solaires,
fenêtres ouvrantes et refroidissement mécanique.

Ces déclarations décrivent le projet ; elles ne remplacent pas les objets détectés dans VE.

## 3. Compléter les preuves techniques

Cliquer **Project Evidence** dans l'interface. Les sept onglets sont :

1. **Projet et climat** : statut neuf/existant, base climatique, station, altitude et source approuvée.
2. **Affectation SIA 2024** : correspondance revue entre chaque pièce ou template VE et sa catégorie d'usage réelle.
3. **Comparaison globale** : indice de dépense énergétique du projet complet, référence, unité et résultat signé.
4. **Commande ventilation** : une ligne par système/zone, avec type, classe de commande, bande de débit et provenance.
5. **Générateur froid** : classe air/eau, puissance, EER et/ou SEER.
6. **Commande éclairage** : mapping pièce ou template vers SIA 387/4.
7. **Puissance électrique** : puissance requise en W/m², surface conditionnée, présence et nécessité du froid.

Laisser `review_status = pending` tant que le responsable n'a pas approuvé la ligne. Si `accepted` est choisi alors qu'un nom, une date, une valeur requise ou une source manque, le logiciel remet automatiquement la ligne à `pending`.

Les CSV sont enregistrés dans `<projet VE>/sia4010_evidence/`. Le fichier précédent est conservé en `.bak` lors d'une modification.

## 4. Générer et contrôler

Cliquer **Generate Excel + PDF**. Les livrables sont écrits dans `<projet VE>/SIA Compliance Reports/`.

- `COMPLIANT` : tous les critères décisifs du périmètre sont évalués et aucune preuve bloquante ne manque ;
- `NOT COMPLIANT` : au moins un critère évalué échoue ;
- `NOT DETERMINED` : une preuve ou une méthode indispensable manque encore.

Ne jamais présenter l'indicateur de couverture comme un verdict réglementaire.

## 5. Quand relancer ApacheSim

Relancer la simulation si le modèle, les profils, la ventilation, les systèmes, les consignes ou la météo ont changé. Une correction de nom de client, logo, source documentaire ou signature ne nécessite pas de nouveau calcul APS ; il suffit de régénérer le rapport.

## À demander et à qui

### Responsable énergie / spécialiste SIA

- statut neuf ou existant applicable ;
- base climatique approuvée, station et altitude ;
- comparaison globale SIA 380 projet/référence avec valeurs, unité et conclusion ;
- méthode de confort d'été retenue, seuil, période d'occupation et traitement de la température opérative ;
- nom, date et référence du document autorisant l'acceptation.

### Ingénieur HVAC

- correspondance entre les IDs systèmes VE et les systèmes de conception ;
- type mono/multizone, classe de commande, débit minimal, horaire, capteur de demande et bande de débit spécifique ;
- puissance et performances EER/SEER des générateurs froid ;
- fiches AHU, récupération de chaleur et pertes de charge si applicables.

### Ingénieur électricité / éclairage

- mapping des pièces/templates vers les types de commande SIA 387/4 ;
- stratégie lumière du jour et document de conception ;
- puissance électrique requise des auxiliaires/transport/conditionnement et surface conditionnée utilisée au calcul.

### Architecte / façadier

- type et commande des protections solaires ;
- fenêtres réellement ouvrantes et stratégie d'ouverture ;
- fiches vitrage, `g_total` avec protection et traitement des ponts thermiques.

### Chef de projet / client

- identité officielle du projet et du client ;
- logo autorisé, référence de rapport et destinataires ;
- documents sources approuvés et personnes habilitées à signer les preuves.

### IES / SIA ou autorité compétente

- package officiel SIA 4010 et conditions d'utilisation ;
- confirmation de la classe de validation visée ;
- procédure de soumission et attestation finale de la sous-commission.

Le logiciel peut préparer, contrôler et emballer ces informations. Il ne peut pas les approuver ni émettre l'attestation à la place de ces responsables.

## Comprendre une donnée manquante

Une donnée manquante n'indique pas nécessairement que le modèle VE est faux.
Elle peut appartenir à l'une de ces quatre familles :

1. **Non modélisée** : l'objet ou la propriété devrait exister dans VE mais n'est pas renseigné.
2. **Non exposée par l'API** : la donnée existe éventuellement dans l'interface ou ApacheHVAC, mais VEScripts ne permet pas de la lire de façon fiable.
3. **Externe au modèle** : la valeur appartient à une note de calcul, une fiche fabricant, un plan ou une décision de projet.
4. **Méthode non automatisée** : le logiciel ne met pas encore en œuvre le protocole prescrit, par exemple les jours de dimensionnement ou la simulation complète du bâtiment de référence.

Le classeur contient deux aides complémentaires :

- `CAPABILITY GUIDE` explique ce qui est automatisé, ce qui ne l'est pas, pourquoi, la preuve exacte attendue, son responsable et l'effet sur le verdict ;
- `INPUT REQUEST` filtre cette liste pour ne montrer que les éléments encore nécessaires au projet actif.

Le principe est volontairement conservateur : une information inconnue reste
`NOT_CHECKABLE` ou `NOT DETERMINED`. Elle ne devient jamais zéro, conforme ou
non conforme par supposition.

## Langue de l’interface et des rapports

L’anglais est sélectionné par défaut pour un nouveau projet. Le sélecteur de
langue propose `English`, `Deutsch`, `Français` et `Italiano`. Le changement est
appliqué immédiatement à toute la fenêtre et la sélection est enregistrée dans
le contexte du projet. Elle est ensuite réutilisée pour l’éditeur de preuves,
le classeur Excel et le rapport PDF. Les valeurs techniques et les identifiants
normatifs (`SIA 380/2`, codes VE, états `PENDING`, etc.) ne sont pas traduits.
