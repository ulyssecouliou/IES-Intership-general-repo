# Registre des demandes externes — rien n'est envoyé depuis ce fichier

Un seul endroit pour tout ce qui attend une réponse extérieure. Rien ici n'est
envoyé automatiquement : le registre existe pour qu'aucune question ne se perde
et pour qu'un envoi groupé remplace trois courriels séparés.

**État au 2026-08-13** : une réponse est déjà en attente sur un envoi antérieur.
Rien ne part avant elle.

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

**À ne pas envoyer** : la « divergence » sur le Ug du vitrage. Elle n'existe pas.
La documentation décrit la même fenêtre sous deux familles de normes — 0,646 en
conditions de référence EN ISO 52022-3, 0,654 en conditions d'hiver ISO 15099 — et
la spécification reprend la seconde, au chiffre près. C'était notre erreur de
comparaison, consignée ici pour qu'elle ne reparte pas.

---

## 2. Répondable en interne, sans courriel

| # | Question | Où chercher | Ce qu'elle débloque |
|---|---|---|---|
| I1 | Quelles **émissivités infrarouges** intérieure et extérieure pour les surfaces opaques de la cellule du chapitre 7 ? Et l'`opaque_solar_absorptance` de 0,6 s'applique-t-elle aux **deux faces** ? | La copie licenciée d'**ISO EN 52016-1:2017**, clauses 7.2.2.7 à 7.2.2.10, pages 126-127 — celles que `iso52016_chapter7_confirmed_inputs.json` cite déjà pour les autres valeurs du même bloc. | L'entrée déléguée `iso52016_2017_chapter7_test_cell`, donc le **Test 2A** et toute la chaîne des cas liés aux sources. |

C'est la demande la plus rentable du registre : deux valeurs, dans un document
que nous détenons, et elle ferme la dernière entrée déléguée du Test 2A. En
attendant, la chaîne tourne sur une valeur **provisoire dérivée** (voir §4).

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

Le contrat préparé porte des **décisions humaines d'autorisation**, donc il n'est
pas installé par défaut : un projet neuf hériterait d'autorisations que personne
dans ce projet n'a prises. Pour la démonstration, dans
[`Run_VE_SIA4010_Prepare_Case_Scenario.py`](Run_VE_SIA4010_Prepare_Case_Scenario.py) :

```
CASE = "2A"
INSTALL_PREPARED_EXTERNAL_INPUTS = True
```

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
exactement ce qu'il y a à montrer : la chaîne de preuve va jusqu'au bout et
refuse le verdict d'elle-même.

**C'est la seule valeur provisoire de la chaîne**, et elle ne peut pas passer
inaperçue. Le chargeur refuse un artefact qui déclarerait du provisoire tout en
autorisant une revendication de conformité ; le contrat générateur du Test 2A
lève le bloqueur `DELEGATED_INPUT_CARRIES_PROVISIONAL_VALUE`, passe en
`SOURCE_BINDINGS_PROVISIONAL_RECALCULATION_REQUIRED` et porte
`verdict_derivation_allowed: false`. Le Test 2A a un critère publié,
contrairement aux cas 1A→1D : la génération reste possible, le verdict non.

### Une valeur qu'on a cru provisoire et qui ne l'était pas

Le coefficient de surface intérieur a d'abord été inscrit ici comme provisoire.
C'était une erreur de diagnostic : la source **énonce** les trois coefficients
intérieurs, un par orientation (mur horizontal 7,63 ; toit vers le haut 10,13 ;
plancher vers le bas 5,83), et c'est le contrat normalisé qui les aplatissait en
une seule valeur. Le chemin du cas 600 déjà éprouvé (`mvp_bundle.py:501`) les
consommait correctement depuis le début. Le contrat a donc été corrigé pour
conserver les trois, au lieu de déclarer provisoire une valeur que la source
donne. Aucune demande externe n'est nécessaire.
