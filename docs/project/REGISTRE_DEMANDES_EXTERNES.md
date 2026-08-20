# Registre des demandes externes — rien n'est envoyé depuis ce fichier

Un seul endroit pour tout ce qui attend une réponse extérieure. Rien ici n'est
envoyé automatiquement : le registre existe pour qu'aucune question ne se perde
et pour qu'un envoi groupé remplace trois courriels séparés.

**État au 2026-08-20** : décision projet — aucun achat de norme payante ne sera
engagé. Les exigences qui dépendent exclusivement d'une norme absente restent
explicitement `NOT_CHECKABLE`/`PARTIAL`; elles ne sont ni reconstituées ni
présentées comme conformes. Une source sous licence fournie ultérieurement par
IES ou par un réviseur pourra toujours être intégrée.

---

## 1. À demander au SIA (Prof. Gerhard Zweifel)

Le brouillon rédigé et vérifié est
[`SIA_CORRESPONDANCE_ZWEIFEL_2026-08-12.md`](docs/project/SIA_CORRESPONDANCE_ZWEIFEL_2026-08-12.md).
Chaque affirmation y est adossée à la cellule ou au fichier qui la prouve.

| # | Demande | Ce qu'elle débloque | Vérifié |
|---|---|---|---|
| S1 | Le `Streubereich` min/max confirmé le 2026-08-10 s'applique-t-il aux **Tests 4 et 6**, dont les spécifications ne portent **aucune** section `Testkriterien` (0 occurrence en recherche plein texte) ? | Le critère de distribution des Tests 4, 6 et 7. Sans réponse écrite, les distributions restent consignées sans verdict. | oui |
| S2 | La **dynamique du store** du test diagnostic 2 E1 : signal d'irradiance comparé au seuil, sens de la comparaison, règle de relâche, traitement de l'état d'un pas de temps à l'autre. Et les deux seuils VE `radiation_to_lower` / `radiation_to_raise` reproduisent-ils bien cette règle ? | Le **cas 1E**, seul cas du Test 1 à porter un critère pass/fail. Le dispositif et ses propriétés optiques sont déjà figés ; seule la dynamique manque. | oui |
| S3 | Signalement, pas une question : `Resultaterfassung Test7.xlsx`, feuille `Zusammenfassung`, cellules `W32` et `W33` portent `kW` dans la cellule de grandeur et `°C` sur la ligne d'unité. Seul bloc sur dix-sept où les deux divergent. | Rien de bloquant. Nous conservons les effectifs et laissons l'unité nulle. | oui, cellule par cellule |
| S4 | Les fiches **SIA 2024** restantes que notre matrice exige : auditorium, bâtiment exemple, restaurant 6.2, cuisine 6.4. | Les Tests 3 à 6 sur ces catégories d'usage. La catégorie 3.1 est déjà en main et suffit à toute la chaîne 1A→1E. | oui |

| S5 | **CLOS — sans achat.** Le tableau 10 et l'édition 2023 de SIA 387/4 ne seront pas acquis par le projet. Nous conservons uniquement le tableau 9 de l'édition 2017 fourni par Yiqiao Yang — voir `refs/reference-data/sia-387-4-2017.blinds.json`. | Les **douze cas du Test 3** restent `NOT_CHECKABLE` tant qu'une liaison contrôlée sous licence n'est pas fournie par IES ou un réviseur. | décision projet 2026-08-20 |
| S6 | **EN 16798-5-1 annexe D**, modèle de récupérateur rotatif. Absent du dépôt : ce n'est pas une transcription à faire, c'est un document que nous n'avons pas. Question d'acquisition ou de licence, peut-être répondable en interne chez IES. | L'entrée déléguée `en16798_5_1_annex_d_rotary_recovery_model`, donc les **quatre cas du Test 5**. | oui |
| S7 | Pour la catégorie **SIA 2024 3.1**, quels jours sont les deux jours de repos hebdomadaires et comment les **261 jours d'utilisation** sont-ils placés dans l'année de calcul ? Les 24 fractions horaires sont connues, mais cette convention de calendrier ne figure pas dans l'extrait reçu. | Le graphe VE natif daily/weekly/yearly sans hypothèse inventée, nécessaire au Test 2A et à toute génération qui consomme directement ces profils. | oui |

**À ne pas envoyer** : la « divergence » sur le Ug du vitrage. Elle n'existe pas.
La documentation décrit la même fenêtre sous deux familles de normes — 0,646 en
conditions de référence EN ISO 52022-3, 0,654 en conditions d'hiver ISO 15099 — et
la spécification reprend la seconde, au chiffre près. C'était notre erreur de
comparaison, consignée ici pour qu'elle ne reparte pas.

---

## 1 bis. Ce qui peut aller au bout **sans attendre aucune de ces réponses**

Établi le 2026-08-13 en interrogeant `case_registry` et le manifeste d'entrées déléguées, pas la documentation.

**Les 24 cas encore non implémentés sont bloqués par des liaisons VE que nous n'avons pas écrites.** Les codes le disent : `VE_LIGHTING_CONTROL_BINDING_NOT_IMPLEMENTED` (12 cas), `VE_SOLAR_CONTROL_BINDING_NOT_IMPLEMENTED` (4), `VE_MULTIZONE_HVAC_BINDING_NOT_IMPLEMENTED` (4), puis quatre liaisons à un cas (1E, Tests 4, 6 et 7). Plusieurs cumulent aussi un besoin externe listé ci-dessous.

### Les six cas normatifs du Test 1 : rien ne les retient

| Fait | Vérifié sur |
|---|---|
| Générateur présent pour les six | `generation_status` = `GUARDED_MUTATION_READY` (600) et `RUNTIME_QUALIFICATION_READY` (640, 600FF, 900, 940, 900FF) |
| Extraction APS implémentée pour les six | `aps_evaluation_scope` = `REFERENCE_OUTPUTS_IMPLEMENTED` |
| **Aucune** entrée déléguée exigée | readiness = `NOT_REQUIRED` |
| **Aucun** critère d'acceptation, par spécification | « Es gibt dafuer kein Abweichungskriterium » |

Leur état terminal est donc « résultats enregistrés », et il est atteignable aujourd'hui. 640 et 600FF y sont déjà. Restent : requalifier 600 après correction du matériau CDB, et trois exécutions VE pour 900, 940, 900FF. **Travail VE, côté Ulysse, sans dépendance externe.**

### Les quatre cas 1A→1D : maintenant exécutables dans la campagne

Leurs entrées déléguées sont **déjà prêtes** (`READY_FOR_BINDING`, zéro bloquée), la chaîne est figée dans `refs/reference-data/test-1.diagnostics.ref.json` (43 champs relevés, 0 à confirmer), et **ils n'ont aucun critère d'acceptation**. Leur bundle, routage Fast Start, qualification runtime, simulation et livrable APS horaire sont raccordés depuis le 2026-08-13. Ils doivent encore être exécutés dans quatre projets VE jetables pour constituer la preuve réelle. Aucune réponse externe n'est nécessaire pour atteindre leur état terminal.

Le cas **1E** est à part : ses entrées sont prêtes aussi, mais la **dynamique** du store reste inconnue (S2). Il est générable, pas jugeable.

### Tests 2 à 7 : aucun n'est complétable

Chacun cumule une liaison VE non écrite **et** au moins une entrée déléguée manquante. Résidu externe exact par test :

| Test | Liaison VE (nous) | Entrées manquantes | Dont réellement externe |
|---|---|---|---|
| 2A-2D | contrôle solaire | émissivité IR | I1, ou piste BESTEST |
| 3A-3F | contrôle éclairage | SIA 387/4 tableau 10 ; détail du store du bâtiment exemple | S5 seulement — le détail du store est dans un document que nous détenons, donc transcription |
| 3G-3L | idem | + clarification d'autorité 3K/3L | S5 + clarification |
| 4 | topologie HVAC | fiche SIA 2024 auditorium ; numérisation de courbe de ventilateur | S4 seulement — la courbe est dans la spécification |
| 5A-5D | HVAC multizone | fiche SIA 2024 bâtiment exemple ; **EN 16798-5-1 annexe D** ; courbe de ventilateur | S4 + **S6** |
| 6 | séquence de ventilation | deux fiches SIA 2024 ; relevé de commande par étages | S4 seulement |
| 7 | systèmes énergétiques | tables de performance de PAC ; précédence PV | tables probablement transcriptibles ; précédence PV = autorité SIA |

---

## 2. Répondable en interne, sans courriel

| # | Question | Où chercher | Ce qu'elle débloque |
|---|---|---|---|
| I1 | Quelles **émissivités infrarouges** intérieure et extérieure pour les surfaces opaques de la cellule du chapitre 7 ? Et l'`opaque_solar_absorptance` de 0,6 s'applique-t-elle aux **deux faces** ? | **Pas dans les pages déjà capturées.** Voir le détail ci-dessous : la piste est ailleurs dans ISO EN 52016-1:2017, hors des pages 123-126. | L'entrée déléguée `iso52016_2017_chapter7_test_cell`, donc le **Test 2A** et toute la chaîne des cas liés aux sources. |

### Où chercher, exactement

Corrigé le 2026-08-13. La formulation précédente envoyait aux clauses 7.2.2.7
à 7.2.2.10 : c'était faux, ces pages ont déjà été lues et ne répondent pas.

**Ce que le dépôt sait déjà.** `config/iso52016_chapter7_confirmed_inputs.json`
ne cite que les pages **123, 124, 125 et 126**, et son bloc
`unresolved_from_current_captures` énonce noir sur blanc : « Numerical infrared
emittance value, because page 126 states only that a standard emittance is
implicitly assumed ». Quelqu'un a donc déjà regardé, et la page 126 dit
seulement qu'une émittance standard est *implicitement supposée*.

**Ce que cela implique.** Si la norme la suppose implicitement, elle la définit
quelque part — et ce quelque part est **hors des quatre pages capturées**. La
chose à chercher n'est donc pas la cellule d'essai du chapitre 7, mais l'endroit
où ISO EN 52016-1:2017 énonce l'émissivité de surface standard ou par défaut
qu'elle applique : le traitement du rayonnement de grande longueur d'onde dans
le corps de la norme, ou sa table de valeurs par défaut en annexe. C'est la
**seule** voie qui donne un statut normatif.

**Voie subsidiaire, déjà dans le dépôt.** La cellule du chapitre 7 dérive du cas
600 de BESTEST, dont le rapport est présent :
`references/standards/bestest/NREL_TP_472_6231.pdf` (296 pages). Sa section de
spécification du bâtiment cas 600 donne les propriétés de surface. **Mais** —
`references/standards/bestest/README.md` fixe la règle : une valeur tracée
uniquement à cette source vaut `PUBLIC_REFERENCE`, suffisant pour faire tourner
et démontrer, **jamais** pour une revendication SIA 4010.

**Pourquoi je ne l'ai pas lu moi-même.** Ce PDF est un scan : 296 pages, **zéro**
caractère extractible, et l'environnement n'a ni OCR ni moteur de rendu de page.
Vous pouvez l'ouvrir, moi non.

En attendant l'une ou l'autre voie, la chaîne tourne sur une valeur
**provisoire dérivée** (voir §4).

**Incohérence à trancher, sans lien avec le calcul** : ce README affirme « The
source is not redistributed in this repository », alors que le PDF de 14 Mo est
bien suivi par git. Le rapport est public (DOI 10.2172/90674), donc c'est
probablement le README qui est périmé — mais c'est votre décision, pas la
mienne, et je n'ai touché ni au fichier ni au README.

---

## 3. Hors de notre portée

| Point | Nature |
|---|---|
| Attestation de la sous-commission SIA (SIA 4010:2023 §4.6.2) | Aucune classe ne peut porter `VALIDATED` avant elle. Ce n'est pas un retard de notre part, c'est le processus. |

---

## 4. Ce qui tourne sur une valeur provisoire en attendant

Une valeur provisoire sert à rendre la chaîne **exécutable**, jamais à produire
une preuve. Chaque artefact qui en porte une le déclare, et son statut interdit
d'en tirer un verdict.

| Valeur | Provisoire retenue | Comment elle est obtenue | Levée par |
|---|---|---|---|
| Émissivité IR des surfaces opaques, intérieure et extérieure | **0,90** | Dérivée des coefficients radiatifs que le fichier porte déjà : ε = h<sub>r</sub> / (4σT³). Intérieur 5,13 / 5,714 à 20 °C = 0,8978 ; extérieur 4,14 / 4,6225 à 0 °C = 0,8956. **Hypothèse à confirmer** : les températures de référence, que le fichier n'énonce pas pour ces coefficients. | I1 |

Ce n'est pas 0,90 choisi par convention : c'est 0,90 reproduit à 0,005 près par
les données du fichier, à deux températures de référence différentes. La
convention aurait donné le même nombre sans le démontrer.

### Comment montrer le Test 2A aujourd'hui

Utiliser une copie jetable enregistrée qui contient au moins une ouverture
vitrée, puis choisir `test_2A / 2A` dans l'interface et cliquer sur **Lancer la
chaîne gardée Test 2A**. Le même parcours est exécutable directement avec
[`Run_VE_SIA4010_Test2A_Qualification_One_Click.py`](../../Run_VE_SIA4010_Test2A_Qualification_One_Click.py).

Le lanceur installe explicitement le contrat d'entrées préparé, affiche chaque
autorisation héritée, exécute d'abord la sonde read-only puis s'arrête **avant le
premier setter** si son statut n'est pas
`READY_FOR_DISPOSABLE_MUTATION_QUALIFICATION`. S'il poursuit, il qualifie
strictement le graphe de profils, les champs de seuil du store et le stockage
optique fixe 2E1 dans deux constructions CDB non affectées. Chaque rapport et
son checksum sont liés dans un audit de continuité unique.

Le statut terminal attendu est
`RUNTIME_STORAGE_BOUNDARIES_QUALIFIED_MODEL_BINDING_REQUIRED`. Il ne signifie
pas que le modèle Test 2A est généré : aucune ouverture n'est affectée, aucune
simulation n'est lancée et aucune équivalence APS n'est revendiquée. En cas
d'échec après la frontière de mutation, il faut jeter le projet et recommencer
dans une copie neuve.

Le manifeste préparé porte des chemins **absolus** : c'est fonctionnellement
requis, parce que le lecteur résout ses chemins relativement au répertoire du
manifeste, et que ce manifeste est copié dans un dossier de projet VE
quelconque. Il est donc valable sur cette machine seulement, et doit être
régénéré ailleurs par
[`scripts/build_test2a_external_inputs.py`](scripts/build_test2a_external_inputs.py).
Les artefacts de preuve, eux, n'en portent aucun.

La console énonce alors chaque autorisation installée avec sa base écrite, puis
`prepare_case_bundle` rend un `Test2ASourceBundleReceipt` en statut
`SOURCE_BINDINGS_PROVISIONAL_RECALCULATION_REQUIRED`, cinq bloqueurs,
`mutation_supported: false` et `verdict_derivation_allowed: false`. C'est
exactement ce qu'il y a à montrer : la chaîne de sources et de stockage natif
va jusqu'à sa frontière actuellement prouvable et refuse le verdict d'elle-même.

**C'est la seule valeur provisoire de la chaîne**, et elle ne peut pas passer
inaperçue. Le chargeur refuse un artefact qui déclarerait du provisoire tout en
autorisant une revendication de conformité ; le contrat générateur du Test 2A
lève le bloqueur `DELEGATED_INPUT_CARRIES_PROVISIONAL_VALUE`, passe en
`SOURCE_BINDINGS_PROVISIONAL_RECALCULATION_REQUIRED` et porte
`verdict_derivation_allowed: false`. Le Test 2A a un critère publié,
contrairement aux cas 1A→1D : le bundle et les frontières de stockage sont
préparables, mais la génération VE complète et le verdict restent bloqués.

### Une valeur qu'on a cru provisoire et qui ne l'était pas

Le coefficient de surface intérieur a d'abord été inscrit ici comme provisoire.
C'était une erreur de diagnostic : la source **énonce** les trois coefficients
intérieurs, un par orientation (mur horizontal 7,63 ; toit vers le haut 10,13 ;
plancher vers le bas 5,83), et c'est le contrat normalisé qui les aplatissait en
une seule valeur. Le chemin du cas 600 déjà éprouvé (`mvp_bundle.py:501`) les
consommait correctement depuis le début. Le contrat a donc été corrigé pour
conserver les trois, au lieu de déclarer provisoire une valeur que la source
donne. Aucune demande externe n'est nécessaire.
