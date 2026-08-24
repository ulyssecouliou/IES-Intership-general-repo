# Mode opératoire client SIA 380/2

## 1. Avant de lancer

1. Ouvrir et enregistrer le bon projet dans IESVE 2025.
2. Vérifier que le dernier APS annuel correspond au modèle actif.
3. Fermer dans Excel/PDF les anciens rapports portant le même nom.
4. Réunir les documents sources listés dans la section « À demander ».

## 2. Saisir les informations du rapport

Depuis la fenêtre Scripts de VE, lancer `Run_VE_Swiss_Compliance_Hub.py`, puis l'action d'audit/rapport client. Renseigner le client, le projet, l'adresse, la référence, l'auteur et la stratégie propre au bâtiment : protections solaires, fenêtres ouvrantes et refroidissement mécanique.

Ces déclarations décrivent le projet ; elles ne remplacent pas les objets détectés dans VE.

## 3. Compléter les preuves techniques

Cliquer **Compléter les preuves…** dans l'interface. Les six onglets sont :

1. **Projet et climat** : statut neuf/existant, base climatique, station, altitude et source approuvée.
2. **Comparaison globale** : indice de dépense énergétique du projet complet, référence, unité et résultat signé.
3. **Commande ventilation** : une ligne par système/zone, avec type, classe de commande, bande de débit et provenance.
4. **Générateur froid** : classe air/eau, puissance, EER et/ou SEER.
5. **Commande éclairage** : mapping pièce ou template vers SIA 387/4.
6. **Puissance électrique** : puissance requise en W/m², surface conditionnée, présence et nécessité du froid.

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
