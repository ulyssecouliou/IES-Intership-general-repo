# Script Video Demo -- Outil SIA 380/2 dans IESVE

**Format** : enregistrement d'ecran + voix off, traduite ensuite par IA
**Duree cible** : 6-8 minutes
**Conseil** : parle posement et articule bien pour la traduction automatique

---
---

## INTRO -- Ecran titre ou bureau vide (30s)

> **ECRAN** : bureau Windows propre, IESVE ferme

Bonjour. Je vais vous montrer l'outil d'analyse de conformite SIA 380/2 que j'ai developpe pour IESVE.

La SIA 380/2, c'est la norme suisse qui regit la performance energetique des batiments. Elle couvre six domaines : chauffage, refroidissement, ventilation, eclairage, protection solaire et ponts thermiques.

Aujourd'hui, ce travail de verification est fait a la main par les ingenieurs. Ca prend des heures, c'est source d'erreurs, et il n'y a pas de tracabilite. L'outil que je vais vous montrer automatise tout ca directement dans IESVE.

---

## PARTIE 1 -- OUVRIR LE MODELE VE (30s)

> **ACTION** : ouvrir IESVE, charger le modele de demo (SIA_compatible_model_TEST ou un vrai projet client)

On commence par ouvrir un projet IESVE avec un modele qui a deja ete simule. L'outil ne fait pas la simulation lui-meme -- il lit les resultats deja calcules.

> **MONTRER** : le modele 3D dans le Model Viewer, tourner un peu pour montrer le batiment

Ici on voit le modele du batiment. Les constructions, les systemes HVAC, le fichier meteo -- tout est deja en place dans le projet VE.

---

## PARTIE 2 -- LANCER LE SCRIPT (20s)

> **ACTION** : aller dans Python Scripts Navigator (menu Tools > Python Scripts) puis lancer le script de conformite SIA 380/2

Pour lancer l'analyse, on passe par le Python Scripts Navigator dans IESVE. On execute le script de conformite SIA 380/2.

> **ATTENDRE** : la fenetre Tkinter du navigateur client s'ouvre

L'interface de l'outil s'ouvre.

---

## PARTIE 3 -- L'INTERFACE CLIENT (60-90s)

> **ECRAN** : la fenetre ClientComplianceWindow est ouverte, on voit le bandeau navy en haut avec le titre "Swiss Compliance Report" et les infos du projet

L'interface est divisee en deux parties. A gauche, le formulaire. A droite, les resultats.

### Section 01 -- Informations du projet

> **MONTRER** : pointer vers les champs de la section 01, les remplir un par un

On commence par renseigner le contexte du rapport. Le nom du client, le nom du projet, l'adresse, la reference du rapport, et le nom du preparateur.

> **ACTION** : remplir les champs -- client name, project name, project address, etc.

On choisit aussi la langue du rapport. Les rapports peuvent etre generes en francais, allemand, anglais ou italien, parce que les verificateurs cantonaux suisses travaillent dans ces langues.

> **ACTION** : montrer le menu deroulant de langue, selectionner "Francais" ou "Deutsch"

### Section 02 -- Strategie du batiment

> **MONTRER** : descendre vers la section 02 "Model & strategy"

Ici on declare la strategie du batiment : est-ce qu'il y a de la protection solaire exterieure ? Les fenetres sont-elles ouvrables ? Y a-t-il du refroidissement mecanique ?

> **ACTION** : cliquer YES/NO sur chaque declaration (solar shading, window operability, mechanical cooling)

Ces declarations sont importantes parce qu'elles determinent quels criteres SIA s'appliquent. Par exemple, si on declare qu'il y a du refroidissement mecanique, le moteur va aussi verifier les criteres de performance du systeme de froid.

Le champ "Notes" en bas permet d'ajouter des precisions pour le verificateur -- par exemple "stores exterieurs automatises, refroidissement a 26 degres".

---

## PARTIE 4 -- LANCER L'ANALYSE (30s)

> **ACTION** : cliquer le bouton bleu "Generate Compliance Report" (en bas a droite du formulaire)

On clique sur "Generate". L'outil va maintenant :
1. Se connecter a l'API Python de VE
2. Extraire automatiquement toutes les donnees du modele -- geometrie, constructions, systemes HVAC, resultats de simulation
3. Comparer chaque parametre aux seuils de la norme SIA 380/2
4. Generer le rapport PDF et le classeur Excel

> **ATTENDRE** : le curseur passe en mode "attente", le statut change. Laisser tourner (~10-30 secondes selon le modele)

L'extraction et l'analyse prennent quelques secondes. Pas de saisie manuelle, pas de copier-coller -- tout est automatique.

---

## PARTIE 5 -- LES RESULTATS (60s)

> **ECRAN** : les resultats apparaissent dans le panneau droit

Les resultats s'affichent dans le panneau de droite.

### Verdict global

> **MONTRER** : pointer vers le bandeau de verdict en haut du panneau droit (vert = COMPLIANT, orange = NOT DETERMINED, rouge = NOT COMPLIANT)

En haut, on a le verdict global. Ici il indique le statut de conformite du modele.

### Compteurs

> **MONTRER** : les compteurs PASS / WARNING / FAIL / NOT_CHECKABLE

En dessous, les compteurs : combien de checks ont passe, combien ont un avertissement, combien ont echoue, et combien n'ont pas pu etre verifies.

Un point important : quand une preuve est manquante, le resultat est "NOT_CHECKABLE" -- jamais un faux "PASS". C'est le principe de l'architecture fail-closed. Inconnu n'est pas egal a conforme.

### Par domaine

> **MONTRER** : les cartes par domaine (Heating, Cooling, Ventilation, Lighting, Solar, Thermal Bridges)

Et ici on voit le resultat par domaine : chauffage, refroidissement, ventilation, eclairage, protection solaire, ponts thermiques. Chaque domaine a son propre statut.

---

## PARTIE 6 -- LES RAPPORTS (2-3 min)

> **ECRAN** : les rapports s'ouvrent automatiquement (Excel et PDF)

Les rapports se sont ouverts automatiquement. Regardons-les en detail, en commencant par le PDF.

### 6A -- Le rapport PDF (11 pages)

> **ACTION** : basculer sur le PDF, montrer la page de couverture

#### Couverture

La page de couverture est brandee IES, avec le logo, le titre "SIA 380/2 compliance assessment", le nom du projet et la date de generation. C'est un rapport professionnel, pas une sortie brute.

> **ACTION** : aller a la page 2

#### Resume executif (page 2)

C'est la page la plus importante du rapport. Tout y est.

> **MONTRER** : le bandeau de verdict en haut

En haut, le verdict global : ici "NOT DETERMINED", en orange, avec les compteurs -- zero finding bloquant, quatre preuves manquantes, zero avertissement.

> **MONTRER** : le tableau d'identification

En dessous, le tableau d'identification reprend toutes les informations du projet : le client, l'adresse, le preparateur, le fichier meteo utilise -- ici c'est un fichier Geneve 2060 RCP 8.5 -- et les declarations de strategie qu'on a renseignees : protection solaire NO, fenetres ouvrables YES, refroidissement mecanique TO_CONFIRM.

> **MONTRER** : le tableau par domaine

Puis le tableau par domaine. On voit que cinq domaines sont au vert -- enveloppe, ouvertures et vitrage, gains internes, consignes d'exploitation, et systemes HVAC. Deux domaines sont en orange, "NOT DETERMINED" : la ventilation et le confort d'ete SIA 180. Ce n'est pas que le modele est mauvais -- c'est qu'il manque des preuves complementaires pour conclure.

> **MONTRER** : l'image du modele et les chiffres cles

A droite, on retrouve l'image du modele 3D extraite de VE, et les chiffres cles : 3 pieces thermiques, 50 m2 de surface nette, 140 m3 de volume, un ratio vitrage/mur de 15.9%.

> **MONTRER** : le disclaimer en bas

En bas de la page, le disclaimer rappelle que c'est une evaluation d'ingenierie, pas un certificat SIA officiel. Et le cadre de signature est vide -- c'est au verificateur de signer.

> **ACTION** : aller a la page 3

#### Logique de decision (page 3)

> **MONTRER** : le bloc "WHY THIS DECISION WAS REACHED"

Cette page explique pourquoi le verdict est "NOT DETERMINED". La raison est claire : la comparaison projet/reference du paragraphe 7.2.5.2 de SIA 380/2 est manquante. C'est cette comparaison globale qui tranche la conformite -- pas les checks individuels.

> **MONTRER** : le cadre "Decisive project / reference comparison"

On voit que les quatre champs de la comparaison decisive -- l'etat de revue, la valeur projet, la valeur reference, la source de calcul -- sont tous a NOT_CHECKABLE. Il faut un verificateur qui fournisse cette comparaison.

> **MONTRER** : les barres de domaine colorees

En dessous, les barres de domaine reprennent les statuts avec un code couleur -- vert pour COMPLIANT, orange pour NOT DETERMINED. Et un resume de la ventilation : les 3 pieces sont ventilees mecaniquement, les debits normalises sont disponibles, mais le controle selon le tableau 4 de SIA 380/2 n'a pas ete valide.

> **ACTION** : aller aux pages 4-5

#### Findings detailles (pages 4-7)

> **MONTRER** : un finding "Evidence incomplete" -- par exemple le finding 03 sur la provenance climatique

Chaque finding est numerote et structure de la meme maniere. Prenons celui-ci : "Le fichier meteo actif n'est pas lie a un enregistrement de metadonnees climatiques SIA accepte par le verificateur."

> **MONTRER** : les champs du finding un par un

On a : le constat, l'effet sur la conformite -- ici "Missing evidence is never treated as a pass" -- la valeur de reference, la valeur lue dans le modele, la source normative, et surtout l'action corrective requise. L'outil ne se contente pas de dire "il manque quelque chose" -- il dit exactement quoi faire.

> **MONTRER** : un finding "Point to review" -- par exemple le finding 09 sur l'infiltration

Certains findings ne bloquent pas la conclusion mais restent documentes. Par exemple l'infiltration : la valeur de reference est 0.15 m3/(h.m2) selon le tableau 2 de SIA 380/2:2022. L'action requise est de confirmer l'unite d'infiltration dans VE et de documenter la conversion.

> **ACTION** : defiler rapidement les pages 5-7 pour montrer qu'il y a 11 findings au total

Au total on a 11 findings. L'outil documente tout, meme les points qui passent -- tout est tracable.

> **ACTION** : aller a la page 8

#### Annexe -- reserves et methodologie (pages 8-9)

> **MONTRER** : la liste des 13 elements non verifiables automatiquement

L'annexe liste tout ce que l'outil ne peut pas verifier automatiquement, et explique pourquoi. Par exemple : les ponts thermiques -- VE expose les psi et chi par surface mais un defaut a zero pourrait etre un oubli de saisie. Ou les puissances de dimensionnement : le workflow design-day prescrit par SIA n'est pas le pic annuel de la simulation.

Cette transparence est fondamentale : l'outil ne fait pas semblant de tout couvrir. Il dit exactement ce qu'il sait et ce qu'il ne sait pas.

> **ACTION** : aller aux pages 10-11

#### Gouvernance et preuves (pages 10-11)

> **MONTRER** : les blocs de preuves avec leur statut "Blocked"

Les deux dernieres pages listent chaque categorie de preuves : meteo et localisation, strategie de ventilation, eclairage, puissances, hypotheses hors VE, identite du verificateur, et perimetre legal du rapport. Chaque categorie indique ce qui a ete enregistre, ce qui manque, l'action requise, et qui en est responsable.

Ce sont exactement les champs que l'on retrouve dans l'assistant de preuves -- la boucle est bouclee.

### 6B -- Le classeur Excel

> **ACTION** : basculer sur le fichier Excel, montrer la COVER sheet

#### Page de couverture

Le classeur Excel reprend les memes informations que le PDF : logo IES, informations du projet, verdict global, et disclaimer. C'est le meme contenu dans un format different.

> **ACTION** : cliquer sur un onglet de domaine (par ex. HEATING ou COOLING)

#### Onglets par domaine

Chaque domaine SIA a son propre onglet. C'est ici que le classeur apporte une vraie valeur ajoutee par rapport au PDF : chaque ligne contient le parametre extrait du modele, la valeur de reference SIA, le verdict, et la reference normative exacte -- article, tableau, page.

> **MONTRER** : pointer sur une ligne avec la reference SIA

Par exemple ici, le check du besoin de chauffage reference l'article SIA 380/2:2022 correspondant. Un verificateur cantonal peut ouvrir la norme et verifier directement, ligne par ligne.

> **ACTION** : montrer l'onglet INDEX si present

L'onglet INDEX permet de naviguer entre toutes les sections. C'est ce classeur que l'ingenieur transmet au verificateur cantonal comme justificatif detaille.

---

## PARTIE 7 -- L'ASSISTANT DE PREUVES (60-90s)

> **ACTION** : revenir sur la fenetre de l'outil, cliquer sur le bouton "Project Evidence"

Certains criteres ne peuvent pas etre verifies automatiquement par l'API de VE. Par exemple : l'EER d'un groupe froid, les specifications d'une CTA, la strategie de ventilation, ou les donnees d'eclairage. Pour ces elements, on utilise l'assistant de preuves.

> **ECRAN** : la fenetre de l'assistant s'ouvre (980x680), avec le bandeau navy en haut

L'assistant s'ouvre dans une fenetre dediee. En haut, le bandeau affiche le projet VE actif et un rappel important : cet assistant ne modifie pas les donnees du modele VE, ne certifie pas la conformite, et ne constitue pas une validation SIA 4010. Il sert uniquement a collecter les preuves de revue de maniere tracable.

### Faits detectes

> **MONTRER** : la section "Facts detected in VE" en haut du formulaire

La premiere section affiche les faits detectes automatiquement dans VE : l'identifiant du projet, le fichier APS selectionne, le fichier meteo detecte, la surface totale des pieces, et les besoins de chauffage et de refroidissement. Ces valeurs sont en lecture seule -- elles viennent directement du modele.

### Champs de preuves

> **MONTRER** : defiler le formulaire pour montrer les differentes categories de champs

En dessous, on retrouve tous les champs de preuves que le verificateur doit renseigner. Ils sont organises par categorie :

> **ACTION** : pointer vers chaque groupe en defilant

- **Meteo et climat** : la base meteo utilisee, le fichier meteo, la localisation, l'altitude, la source et le scenario climatique. Le fichier meteo detecte dans VE n'est pas copie automatiquement -- c'est volontaire. Le verificateur doit declarer lui-meme quelle base meteo il considere correcte. Une correspondance technique n'est pas une approbation climatique.

- **Identification du verificateur** : nom, role, organisation, base de competence, perimetre d'acceptation et date de revue. C'est la tracabilite de qui a verifie quoi.

- **Documents source et hypotheses** : les documents de reference, les notes, et le registre des hypotheses du projet.

- **Ventilation** : la strategie de ventilation, sa justification, la source des debits, et le perimetre couvert.

- **Eclairage** : le perimetre d'evaluation, la source des puissances, et la justification si l'eclairage est exclu.

- **Puissances systemes** : les donnees de dimensionnement des ventilateurs, pompes, auxiliaires et batteries.

### Validation et sauvegarde

> **MONTRER** : defiler jusqu'en bas du formulaire, montrer la case a cocher et les boutons

En bas du formulaire, une case a cocher oblige le verificateur a confirmer : "I confirm that I reviewed this information and accept responsibility as the named reviewer." Sans cette confirmation, les preuves ne peuvent pas etre acceptees.

> **ACTION** : cliquer sur "Validate"

Le bouton "Validate" fait une verification a blanc. Il indique combien de champs obligatoires sont manquants, combien de valeurs sont invalides, et si la confirmation est absente. Le statut passe au vert uniquement quand tout est complet.

> **ACTION** : cliquer sur "Save evidence"

Le bouton "Save evidence" enregistre les preuves dans un fichier CSV et un dossier d'audit JSON. Aucune donnee du modele VE n'est modifiee. On peut ensuite relancer l'analyse depuis l'interface principale : les checks qui etaient "NOT_CHECKABLE" sont maintenant evalues avec les preuves fournies, et deviennent "PASS" ou "FAIL" selon les valeurs.

---

## CONCLUSION (30s)

> **ECRAN** : revenir sur la fenetre de l'outil avec les resultats affiches, ou retour au bureau

Pour resumer : a partir d'un modele VE ouvert avec une simulation terminee, l'outil extrait automatiquement toutes les donnees, verifie la conformite SIA 380/2 sur les six domaines, et genere un rapport PDF et un classeur Excel prets pour le verificateur cantonal.

Tout le processus prend quelques minutes. Chaque resultat est tracable jusqu'a l'article de la norme. Et aucune preuve manquante ne peut devenir un faux positif.

Merci.

> **FIN** -- couper l'enregistrement

---
---

## CHECKLIST AVANT D'ENREGISTRER

- [ ] Modele VE de demo ouvert et simule
- [ ] VEScripts accessible (menu Tools > Python Scripts)
- [ ] Le script SIA 380/2 est dans le Navigator
- [ ] Champs a remplir prepares (nom client, projet, adresse...)
- [ ] Deuxieme ecran avec ce script affiche
- [ ] Resolution d'ecran correcte (1920x1080 de preference)
- [ ] Notifications Windows desactivees
- [ ] Micro teste

## CHIFFRES CLES (si question)

| Metrique | Valeur |
|----------|--------|
| Verifications automatisees | 50+ |
| Domaines SIA 380/2 couverts | 6 / 6 |
| Formats de rapport | PDF + Excel |
| Langues | FR / DE / EN / IT |
| Code production | ~86 000 lignes |
| Tests automatises | 2 305 |
| Architecture | fail-closed (inconnu != conforme) |
