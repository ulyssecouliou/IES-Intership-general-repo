# Matrice de traçabilité — Test SIA 4010 n° 7 (classe de validation 5)

> ## Statut : **RENVOYÉE — NON SIGNÉE**
>
> Contrôle indépendant mené le **2026-08-06** par `qa-auditor`, sans réutiliser
> le code du dépôt pour les vérifications de source (lecture directe du XML des
> classeurs et du texte des PDF).
>
> **Ce qui est certifié** : l'extraction des 11 bandes de référence. Elle est
> exacte, exhaustive et reproductible au bit près.
>
> **Pourquoi la matrice n'est pas signée** : sept motifs, §5. Le motif bloquant
> n'est pas une erreur de calcul — c'est qu'aucune ligne de la matrice ne peut
> porter de **valeur candidate reproduite** : le Test 7 n'a jamais été exécuté
> dans VE, aucun adaptateur ne l'extrait, aucune UI ne l'affiche, et la grandeur
> obligatoire `PV-Ertrag` est physiquement inatteignable faute d'irradiance.
> S'y ajoute une **divergence entre le critère implémenté et la seule règle
> exécutable que le classeur du Test 7 contient réellement** (§4), découverte
> pendant cet audit et non documentée jusqu'ici.

---

## 1. Méthode de vérification — commandes rejouables

| # | Contrôle | Commande | Résultat réel |
|---|---|---|---|
| V1 | Identité du classeur source | `sha256sum "SIA_4010_geteilter_Link/Test7/Resultaterfassung Test7.xlsx"` | `5eb5b5ba594bd61a2f791a49429eb409c7b4303ad57d1656140dc9c4d0eee0ab` — identique à la copie de `IES-Intership-general-repo` |
| V2 | Rejeu de l'extraction | `python scripts/build_test7_reference.py` | 11 grandeurs, concordance annoncée atteinte |
| V3 | Reproductibilité binaire du JSON figé | `--ecrire` puis `diff` avec la copie antérieure | **identique octet pour octet** |
| V4 | Suite complète | `python -m pytest -q` | **165 passés, 3 ignorés** + un vidage `Windows fatal exception: code 0x80010108` à la collecte (§6.3) |
| V5 | Moteur seul | `python -m pytest -q engine/tests` | **107 passés, 0 ignoré** |
| V6 | Test 7 seul | `python -m pytest -q engine/tests/test_test7_engine.py` | **17 passés** |
| V7 | Séparation dur/pur | motif CI ancré, `.py` uniquement, sur `engine/` | **0 occurrence** — conforme |
| V8 | Lecture XML brute du classeur | script d'audit indépendant, sans openpyxl | §3, §4 |
| V9 | Texte des PDF | PyMuPDF sur `Spezifikation_Test7.pdf` et `refs/SIA-4010-2023.pdf` | §2 |
| V10 | 15 contrôles adverses | script d'audit hors dépôt | §6 — 15/15 confirment le comportement décrit |

---

## 2. Ancrage normatif — vérifié mot pour mot dans `refs/SIA-4010-2023.pdf` (éd. fr.)

| Clause | Page | Citation vérifiée | Ce qu'elle établit |
|---|---|---|---|
| **§4.5, tableau 63** | 48 | classe **5** → applications « calcul des besoins en énergie de refroidissement et de chauffage pour les profils de besoins existants » → Tests : **« 7 »** | La classe 5 n'exige que le Test 7. **CONFIRMÉ** |
| **§4.4** | 47 | « Pour chaque test, un fichier d'évaluation EXCEL est disponible sur www.sia.ch/sia4010, dans lequel les résultats peuvent être transférés et **qui génère la représentation comparative des résultats avec les résultats de référence**. » | Le classeur est l'instrument de **comparaison**. La clause ne dit **pas** qu'il définit un seuil d'acceptation. |
| **§4.6.1** | 48 | « La sous-commission […] **évalue les résultats** et délivre […] l'attestation de conformité. » | La décision d'acceptation est confiée à un **jury humain**. |
| **§4.6.2** | 49 | « La sous-commission évalue les résultats et donne un feed-back […] **Si les tests nécessaires sont remplis**, une confirmation est délivrée » | « Remplis » n'est **jamais** défini numériquement. |
| **Annexe A, tableau 64** | 50 | Test 7 → objet « Émission, distribution, stockage et production de chaleur et de froid » ; secteur technique incluant **« autoproduction d'électricité (PV) »** ; normes de référence **SN EN 16798-9/-13/-15:2017, SN EN 15316-2/-3/-5:2017, SIA 384/3:2017** | Le PV est exigé par la **norme**, pas seulement par une ligne de classeur. Les 7 normes citées **ne sont pas en notre possession**. |
| `Spezifikation_Test7.pdf` | 1–4 | 15 motifs cherchés (`kriterium`, `streubereich`, `abweichung`, `toleranz`, `grenzwert`, `obere grenze`, `mittelwert`, `bestanden`, `erfüllt`, `anforderung`, `bewertung`, `excel`, …) → **0 occurrence** sur 3,6 ko de texte réellement extrait | La spécification n'énonce **aucun** critère. **CONFIRMÉ** |

**Verdict sur l'ancrage** : la mention `INFERE` portée par le moteur est
**justifiée**, et pour une raison plus forte que celle écrite dans le code : le
critère n'est pas « en attente de confirmation », il est **structurellement
absent de la norme**, qui délègue la décision à des personnes (§4.6.1).

---

## 3. Matrice principale — clause → code → test → référence → verdict

Légende : **CERTIFIÉ** = vérifié indépendamment sur pièce ; **INFÉRÉ** = raisonnement
défendable, non écrit dans une source ; **NON COUVERT** = aucun code, aucun test.

| # | Clause / source | Fonction du moteur | Test unitaire | Référence reproduite | Verdict |
|---|---|---|---|---|---|
| 1 | SIA 4010 §4.5 tab. 63 | `test7_engine.CLASSES_CONCERNEES = ('5',)` | *(aucun test ne confronte cette constante à la norme)* | tab. 63 p. 48 lu mot pour mot | **CERTIFIÉ** sur la source ; **non testé** dans le code |
| 2 | Classeur `Zusammenfassung` L7/M7/N7 | `scatter_band.build_band` | `test_les_bandes_du_json_sont_coherentes_avec_leurs_contributeurs` | 33 valeurs L/M/N, écart max **7,276e-12 kWh** (1,3e-16 relatif) | **CERTIFIÉ** |
| 3 | Formules `M8:M20` (liste `MAX(ABS(...))`) | `build_test7_reference._contributeurs` | `test_le_jeu_de_contributeurs_varie_reellement` | jeux GHJ / GHIJ / GHI ; concordance **triple** : ensemble de M = ensemble de N = cellules numériques de G:J, sur les 11 lignes | **CERTIFIÉ** (§3.1) |
| 4 | Formules `N11`, `N17` (`MAX(0,…)`) | argument `floor_at_zero` | `test_le_plancher_a_zero_est_ponctuel_pas_general` | plancher présent sur **2 lignes exactement**, absent des 9 autres | **CERTIFIÉ** |
| 5 | Lignes 8-12, 14-18, 20 portent une bande ; 21-26 n'en portent pas | boucle `extraire()` filtrant sur `AVERAGE` | `test_onze_grandeurs_a_bande` | **0 formule `AVERAGE` ailleurs** dans les 367 lignes × 121 colonnes de la feuille → les 11 bandes sont **exhaustives** | **CERTIFIÉ** |
| 6 | Un programme non contributeur ne vaut pas zéro | `test7_engine.valeurs_contributrices` | `test_un_programme_non_contributeur_nest_pas_compte_comme_zero` | Excel ignore les cellules **texte** ; `L` mis en cache = moyenne des seules cellules numériques, écart ≤ 3,6e-12 sur les 11 lignes | **CERTIFIÉ pour le jeu figé** ; réserve §6.1 |
| 7 | Zéros réels ≠ absences | idem | *(aucun test dédié)* | `I17 = 0` (EnergyPlus, chaudière) et `J11 = 0` (Tas) sont des **zéros numériques contributeurs** ; `I8/I10/I11/J14/J17/J18/J20` sont des **chaînes** non contributrices | **CERTIFIÉ** sur la source ; **non testé** |
| 8 | Bornes incluses | `ScatterBand.contains` | `test_les_bornes_sont_inclusives` | le classeur n'écrit aucune exclusion stricte | **INFÉRÉ** (absence de preuve contraire) |
| 9 | Critère « moyenne ± max(écart) » comme **seuil d'acceptation** | `scatter_band.verdict` | `test_le_critere_est_annonce_comme_infere` | **aucune** — et la seule règle exécutable du classeur Test 7 dit autre chose (§4) | **INFÉRÉ — contesté** |
| 10 | `PV-Ertrag` obligatoire (tab. 64 + bande L20/M20/N20) | aucune fonction dédiée | `test_le_pv_porte_une_bande_donc_il_est_obligatoire` | bande présente ; **irradiance absente de toute source officielle** | **BLOQUÉ** — §5.4 |
| 11 | Diagnosegrössen hors verdict | `GROUPE_AVEC_CRITERE` | `test_les_diagnosegroessen_nentrent_pas_dans_le_verdict` | **aucune** : le JSON figé ne contient **aucune** Diagnosegrösse | **TEST TAUTOLOGIQUE** — §6.2 |
| 12 | Distributions horaires de fréquence (`Zusammenfassung` l. 31+, 17 feuilles `Vert.*`) | — | — | pas de bande, mais présentes dans la « représentation comparative » du §4.4 | **NON COUVERT** |
| 13 | Semaines type hiver/été (31 feuilles) | — | — | idem | **NON COUVERT** |
| 14 | 6 Diagnosegrössen (l. 21-26) | — | — | valeurs présentes au classeur, absentes du JSON | **NON COUVERT** |
| 15 | Physique du test (PAC, ballons, distribution, PV) — SN EN 15316-2/-3/-5, EN 16798-9/-13/-15, SIA 384/3 | — | — | **aucune de ces 7 normes n'est dans `/refs`** | **NON TRAÇABLE** |
| 16 | Extraction VE des 11 grandeurs | — | — | `ve_adapter/` ne contient que `test1_adapter.py` | **ABSENT** |
| 17 | Affichage navigateur | — | — | aucune référence au Test 7 dans `ui/` | **ABSENT** |
| 18 | Séparation dur/pur (CLAUDE.md règle 4) | `engine/test7_engine.py`, `engine/scatter_band.py` | `test_no_iesve_import` | motif CI ancré : **0 occurrence** dans tout `engine/` | **CERTIFIÉ** |

### 3.1 Les 11 bandes, reproduction ligne par ligne

Écart entre le JSON figé et la valeur mise en cache par le classeur, en kWh.

| Ligne | Grandeur (libellé du classeur) | Contrib. | Moyenne | Borne basse | Borne haute | Δ max |
|---|---|---|---|---|---|---|
| 8 | Zugeführte elektrische Energie Kältemaschine | GHJ | 3 928,779 | 3 373,784 | 4 483,774 | 0 |
| 9 | Total abgeführte Wärme | GHIJ | 23 762,689 | 22 468,020 | 25 057,357 | 7,3e-12 |
| 10 | Hilfsenergie Kälteerzeugung | GHJ | 2 187,597 | 1 088,723 | 3 286,470 | 0 |
| 11 | Aus Kälteerzeugung an die Wärmeseite gelieferte W. | GHJ | 331,788 | **0,000** ⌊0⌋ | 935,926 | 0 |
| 12 | Über Rückkühler abgeführte Wärme | GHIJ | 28 122,460 | 27 293,358 | 28 951,562 | 7,3e-12 |
| 14 | Zugeführte elektrische Energie Wärmepumpe | GHI | 8 727,624 | 8 081,321 | 9 373,927 | 0 |
| 15 | Zugeführte Wärme der Wärmeerzeugung, Heizen | GHIJ | 7 847,662 | 7 415,879 | 8 279,446 | 0 |
| 16 | Zugeführte Wärme der Wärmeerzeugung, Warmwasser | GHIJ | 23 707,189 | 22 871,194 | 24 543,183 | 0 |
| 17 | Energie Heizkessel | GHI | 44,150 | **0,000** ⌊0⌋ | 126,399 | 0 |
| 18 | Hilfsenergie Wärmeerzeugung | GHI | 1 228,061 | 595,881 | 1 860,240 | 0 |
| 20 | PV-Ertrag | GHI | 56 975,555 | 54 069,923 | 59 881,188 | 0 |

29 des 33 valeurs sont **exactes au bit près** ; les 4 autres diffèrent d'un ULP
(≤ 7,3e-12 kWh). La concordance annoncée à 1e-6 est **vraie et sous-estimée**.
Unité : **kWh** pour les 11 grandeurs, lue en colonne K.

### 3.2 Le mécanisme d'exclusion — description corrigée

`scripts/build_test7_reference.py` (lignes 26-28) écrit :

> « Des cellules gardent une formule inter-feuilles sans valeur en cache
> (`='Daten EnergyPlus'!G6`). `data_only=True` renvoie alors la formule en texte. »

**C'est faux.** Lecture du XML brut : ces cellules portent `t="s"`, c'est-à-dire
qu'elles sont des **chaînes partagées** — du texte qui *ressemble* à une formule.
Il n'y a ni formule, ni cache manquant.

```
I8   t='s'    f=None   v='8865'  -> "='Daten EnergyPlus'!G6"      (texte)
I9   t=None   f="'Daten EnergyPlus'!G7"   v='24437.992207150128'  (vraie formule)
```

La conséquence est **favorable** et rend la référence plus solide que ne le dit
la docstring : `AVERAGE` **ignore le texte**, donc le `Mittelwert` mis en cache
est bien la moyenne des seuls contributeurs, et il **resterait identique après
un recalcul** dans Excel. La bande figée n'est pas suspendue à un cache périmé.

Effet secondaire à connaître : `_resoudre()` **déréférence** ce texte et inscrit
la valeur du programme écarté dans `par_programme` (p. ex. `Energy+/OpenStudio =
6918,225` ligne 8). C'est une **reconstruction de l'auditeur du classeur**, pas
une valeur publiée à cet emplacement — le SIA a précisément coupé le lien. Elle
n'entre dans aucune bande, mais le JSON ne la distingue pas d'une valeur lue.

---

## 4. Constat central : le classeur du Test 7 contient une règle exécutable, et elle diverge du moteur

Recherche exhaustive dans le classeur : **0 chaîne de verdict** sur 8 883
(`bestanden`, `erfüllt`, `Kriterium`, `innerhalb`, `Toleranz`, …). **50
graphiques**, tous alimentés par `Zusammenfassung` — dont le graphique principal
`chart1` (« Energien in kWh ») qui trace **uniquement** les colonnes F à J des
programmes, **jamais** les colonnes L/M/N de la bande.

Le **seul** endroit du classeur où la bande sert à quelque chose est une mise en
forme conditionnelle :

```xml
<conditionalFormatting sqref="F8:F12 F14:F18 F20">
  <cfRule type="cellIs" dxfId="0" priority="1" operator="between">
    <formula>$L8</formula><formula>$M8</formula>
  </cfRule>
</conditionalFormatting>
```

Deux enseignements, de signe opposé.

**a) Confirmation forte du périmètre.** La plage `F8:F12 F14:F18 F20` est
**exactement** l'ensemble des 11 lignes retenues par l'extracteur, sauts de
lignes 13 et 19 compris. Les Diagnosegrössen (21-26) en sont exclues. Le choix
des 11 grandeurs est donc corroboré par une seconde source, indépendante des
formules `AVERAGE`.

**b) Les bornes ne sont pas celles du moteur.** Or `L7 = Mittelwert`,
`M7 = Obere Grenze`, `N7 = Untere Grenze`. La règle porte donc sur
**[moyenne ; borne haute]**, et non sur **[borne basse ; borne haute]**.

Comparaison des six classeurs, colonnes identifiées **par leurs formules** :

| Classeur | moyenne | b. haute | b. basse | colonnes citées par la MFC | correspond à |
|---|---|---|---|---|---|
| Test 1 | G | H | I | `$I16`, `$H16` | basse, haute ✔ |
| Test 2 | M | N | O | `$N14`, `$O14` | haute, basse ✔ |
| Test 3 | O | P | Q | `$Q11`, `$P11` | basse, haute ✔ |
| Test 4 | T | U | V | `$U10`, `$V10` | haute, basse ✔ |
| Test 6 | K | L | M | `$L10`, `$M10` | haute, basse ✔ |
| **Test 7** | **L** | **M** | **N** | **`$L8`, `$M8`** | **moyenne, haute ✘** |

Cinq classeurs sur cinq comparables visent les deux bornes. Le Test 7 est le
seul à viser la moyenne. Le mécanisme est visible : dans le Test 6 le couple
`$L,$M` **est** (haute, basse) ; dans le Test 7 les colonnes ont glissé d'un
rang vers la droite et les lettres n'ont pas suivi.

**Lecture retenue** : erreur de recopie dans le classeur du SIA, quasi certaine
mais **non prouvée**. Le critère `[borne basse ; borne haute]` implémenté par
`scatter_band` est presque sûrement l'intention. Conséquences pour la matrice :

1. Le moteur implémente le critère **intentionnel**, pas le critère **littéral**
   du classeur du Test 7. C'est une inférence supplémentaire, **non documentée**
   dans `engine/test7_engine.py`, dans `test-7.ref.json` ni dans la spec.
2. Elle est **matérielle** : contrôle adverse A13 — un candidat à 3 651,3 kWh
   ligne 8 (entre borne basse 3 373,8 et moyenne 3 928,8) est déclaré
   **CONFORME** par le moteur et **ne serait pas surligné** par le classeur.
3. L'affirmation de `engine/test7_engine.py` l. 21-26 — « that delegation is
   backed by direct material evidence rather than analogy […] the bands exist
   exactly where the criterion must bite » — est **surinterprétée**. Ce qui est
   observable, c'est **où les bandes existent**, pas **ce qu'elles signifient**.
   Là où le classeur dit observablement quelque chose du seuil, il dit autre
   chose que le moteur.

**Ceci ne remet pas en cause les 11 bandes**, qui sont exactes. Cela remet en
cause la phrase qui présente le classeur comme la source du critère.

---

## 5. Motifs du renvoi

| # | Motif | Renvoyé à | Bloquant ? |
|---|---|---|---|
| **M1** | Divergence §4 non documentée entre le critère implémenté `[N;M]` et la règle exécutable du classeur `[L;M]`. À consigner dans la spec, le JSON et la docstring, et à porter à la sous-commission (SIA 4010 §4.6.2) avec les questions déjà ouvertes. | `norm-analyst` | **oui** |
| **M2** | Description fausse du mécanisme d'exclusion dans `build_test7_reference.py` (§3.2). Le résultat est bon, la raison écrite est fausse. | `reference-data-engineer` | non |
| **M3** | `INFERE` non propagé : absent de `evaluer_grandeur()` (fonction publique) et de `classe_5_validee` (booléen nu). Un consommateur qui ne lit pas `resultat['critere']` perd la réserve. | `validation-engine-engineer` | **oui** |
| **M4** | `PV-Ertrag` : aucun verrou de code. La seule protection est l'absence d'entrée — le moteur retourne `PASS` et `classe_5_validee = True` dès qu'une valeur est fournie (A3). `reserve_pv` existe dans le JSON et n'est lue par personne (A3bis). | `validation-engine-engineer` | **oui** |
| **M5** | DoD PROJECT_PLAN §5 : adaptateur VE **absent**, UI **absente**, entrée de doc utilisateur **absente**. Aucune ligne ne peut porter de valeur candidate. | orchestrateur | **oui** |
| **M6** | Aucun fichier n'est versionné : `test-7.ref.json`, `engine/test7_engine.py`, `engine/tests/test_test7_engine.py`, `scripts/build_test7_reference.py` sont tous en `??` dans git. « Figé et versionné » (DoD) n'est pas satisfait. | orchestrateur | **oui** |
| **M7** | Pas de `traceability/test-7.spec.md` : la spec du Test 7 est diluée dans `classes-de-validation.spec.md`, qui traite les huit classes. Le Test 1 a la sienne. | `norm-analyst` | non |

---

## 6. Contrôles adverses — 15 constats, tous reproduits

### 6.1 Sur le moteur

| Id | Constat | Comportement réel |
|---|---|---|
| A1 | Contributeur **déclaré** mais de valeur nulle | **Écarté en silence.** Ligne 9 : 4 déclarés → 3 retenus, moyenne 23 762,7 → 24 194,2 (+431,6 kWh), borne basse 22 468,0 → 23 813,7. Aucun `NOT_CHECKABLE`, aucune alerte. Le moteur calculerait une bande différente de celle du classeur sans le dire. |
| A2 | Nom de contributeur inconnu du dictionnaire | Écarté en silence, aucune exception. |
| A3 | `PV-Ertrag` avec valeur fournie | `PASS`, verdict global `PASS`, `classe_5_validee = True`. |
| A3bis | `reserve_pv` | Jamais lue par `evaluer_grandeur`. |
| A4 | Marqueur `INFERE` au niveau de la grandeur | Absent. |
| A4bis | `classe_5_validee` | Booléen nu, sans réserve attachée. |
| A5 | Candidat de type chaîne (`"3928.8"`) | `TypeError: '<=' not supported between instances of 'float' and 'str'` — plantage, pas de rejet propre. Risque réel dès qu'un JSON d'adaptateur sera branché. |
| A6 | Candidat `NaN` | Rapporté `FAIL`, pas `NOT_CHECKABLE`. Une extraction ratée se présente comme un échec physique. |
| A7 | Unités | `unite` transporté, jamais confronté. Un candidat en MWh donnerait un `FAIL` silencieux. |
| A11 | Bornes | Inclusives ; borne − 0,001 kWh → 1 échec. La tolérance `1e-6` du moteur n'est issue d'aucune norme (elle est négligeable, mais c'est une valeur non sourcée au sens de CLAUDE.md règle 1). |
| A12 | Signes | Aucune borne basse négative après plancher. Les 6 grandeurs de signe négatif du classeur (`Einspeisung`) sont des Diagnosegrössen, hors périmètre. |
| A13 | Divergence avec la MFC du classeur | §4. |
| — | Clé candidate mal orthographiée | Ignorée en silence → `NOT_CHECKABLE`, **sans diagnostic** sur la clé non reconnue. Échoue du bon côté, mais indébogable. L'appariement se fait sur du texte libre allemand ; les libellés diffèrent d'ailleurs entre `Zusammenfassung` (« Zugeführte Wärme der Wärmeerzeugung, Heizen ») et `Daten IDA_ICE` (« Zugeführte Wärme Heizen »). |

### 6.2 Sur les tests existants

- `test_les_diagnosegroessen_nentrent_pas_dans_le_verdict` est **tautologique** :
  le JSON figé ne contient aucune Diagnosegrösse, l'assertion compare 11 à 11 et
  passerait même sans filtre de groupe.
- A9 : en étiquetant les 11 grandeurs `Diagnosagrössen` (l'orthographe **réelle**
  du classeur, cellule A21 — avec un « a »), le repli `if not soumises:
  soumises = resultats` juge quand même les 11 et conclut `PASS`. Le filtre est
  neutralisé par son propre repli. Le repli est défendable ; le test qui prétend
  le couvrir ne le couvre pas.
- La docstring du moteur affirme que les Diagnosegrössen « sont rapportées pour
  information ». Elles ne sont **pas** dans le JSON, donc **pas rapportées** du
  tout.
- Aucun test ne confronte `CLASSES_CONCERNEES` au tableau 63, ni ne distingue un
  **zéro réel contributeur** (`I17`, `J11`) d'une **absence** — pourtant les deux
  coexistent dans ce jeu de données et c'est le piège annoncé par la docstring.

### 6.3 Sur la suite

`python -m pytest -q` → **165 passés, 3 ignorés**. Un vidage
`Windows fatal exception: code 0x80010108` (`RPC_E_DISCONNECTED`) est émis à la
**collecte** de `ui/tests/test_export_excel_com.py` ligne 103 : du COM Excel
s'exécute au **niveau module**. Non fatal, la suite se termine — mais tout
lecteur du journal CI verra une trace d'exception sur une suite verte. Hors
périmètre du Test 7, à traiter par `ui-engineer`.

---

## 7. Ce que cet audit n'a **pas** vérifié

- La **physique** du Test 7 : PAC Climaveneta, champs de caractéristiques EN 14825,
  ballons, forfaits de distribution, rendement onduleur. Aucun code ne l'implémente
  encore, et **aucune** des 7 normes citées au tableau 64 n'est dans `/refs`.
- Le contenu de `Lastverläufe_220607.xlsx` : non rouvert ici ; l'affirmation de
  `classes-de-validation.spec.md` (« aucune donnée météo dedans ») n'a **pas** été
  recontrôlée.
- La **température de Kloten** figée dans `sia-2028-kloten-temperature.{json,csv}`
  et le **climat DRYCOLD** — hors périmètre de cette matrice.
- Si Excel normalise l'ordre des deux formules d'une règle `between` : sans effet
  sur le constat §4, qui porte sur l'identité des **colonnes**.
- Le classeur du **Test 5**, dont la mise en forme conditionnelle a une structure
  différente (plusieurs règles) et n'entre pas dans la comparaison §4.
- `engine/scatter_band.py` n'apparaît **nulle part** dans `AUDIT.md`, alors que
  tout le critère du Test 7 repose dessus.
- `date_extraction: "2026-08-05"` est une constante en dur du script : elle ne
  reflétera jamais la date réelle d'un rejeu (cosmétique).

---

## 8. Signature

> **AUDITÉ — RENVOYÉ. NON SIGNÉ.**
>
> Les lignes 2, 3, 4, 5, 6, 7 et 18 de la matrice §3 sont vraies et vérifiées
> sur pièce ; l'extraction des références du Test 7 peut être considérée comme
> **acquise**. Les lignes 9, 10, 12, 13, 14, 15, 16 et 17 ne le sont pas.
>
> La signature `AUDITÉ OK` sera apposée lorsque les motifs **M1, M3, M4, M5 et
> M6** seront levés. Elle ne pourra de toute façon pas couvrir l'acceptation
> réelle du Test 7 tant que la sous-commission SIA n'aura pas tranché le critère
> — ce qui, au vu du §4.6.1, est une décision qui ne nous appartient pas.
>
> `qa-auditor` — 2026-08-06
