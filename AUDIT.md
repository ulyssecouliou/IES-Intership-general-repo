# AUDIT.md — Audit qualité indépendant du projet SIA 4010 Validation Navigator

> Doctrine : tout est supposé faux jusqu'à preuve reproductible. L'auditeur
> (`qa-auditor`) est indépendant des agents qui produisent les livrables. Aucune
> affirmation d'un `.md` ou d'un nom de champ n'est reprise sans recontrôle contre
> la source brute.

---

## Élément audité n°1 — `refs/reference-data/test-1.ref.json` (+ `test-1.ref.md`)

- **Producteur** : `reference-data-engineer`.
- **Source brute** : `SIA_4010_geteilter_Link/Test1/Resultaterfassung_Test1.xlsx`,
  feuille `Zusammenfassung Testfälle`.
- **Méthode d'audit** : réouverture indépendante du classeur via `openpyxl`
  (`data_only=True`), reconstruction des lignes d'en-tête réelles, comparaison
  exhaustive cellule par cellule (aucun échantillonnage),
  vérification label↔colonne contre les vraies lignes d'en-tête, contrôle de
  cohérence interne (métadonnées, `data_missing`, `status`, `corrections`),
  traitement des cellules d'erreur Excel, cohérence physique du cas 1E.

### VERDICT COURANT (après passe 3) : **GARDER — SIGNÉ** ✅

> Le verdict `CORRIGER` de la **passe 2** est **conservé comme historique** plus bas.
> Il est **remplacé** par le ré-audit de passe 3 (section « RÉ-AUDIT PASSE 3 » en fin
> de fichier). Les trois défauts (n°1, n°2, n°3) sont **corrigés et vérifiés
> indépendamment cellule par cellule**. Le fichier `test-1.ref.json` peut être
> **transmis à `validation-engine-engineer`**.

---

### VERDICT PASSE 2 (HISTORIQUE) : **CORRIGER** (ne pas signer, ne pas transmettre en l'état)

Le JSON est **partiellement fiable** : les Tables 28 et 29 (chauffage/refroidissement,
tous cas) et les cas **600FF/900FF** des Tables 30 et 32 sont **exacts et fidèles**.
Mais il contient **deux défauts bloquants** qui reproduisent exactement le type de bug
(décalage de colonnes) déjà rencontré, à des endroits **jamais revérifiés
indépendamment**. Le fichier ne peut pas être utilisé tel quel par
`validation-engine-engineer`.

---

## Ce qui a été VÉRIFIÉ ET CONFIRMÉ (reproductible) — passe 2

1. **Lignes d'en-tête réelles reconstruites** (contre présomption) :
   - Table 28 : titre L11, `Case id.` L13, en-têtes de colonnes **L15**, données L16–L28.
   - Table 29 : `Case id.` L34, en-têtes **L36**, données L37–L49.
   - Table 30 : `Case id.` L55, en-têtes **L57**, données L58–L70.
   - Table 32 : `Case id.` L104, `Max.`=L105, `Min.`=L106, `Average`=L107.
   (Les numéros supposés dans la consigne — 15/55/57/104 — sont confirmés ; la ligne
   d'en-tête de la Table 32 est **104**, pas une autre.)

2. **Fidélité valeur↔cellule : 1318/1318 cellules concordantes** (passe 2). Zéro
   divergence de valeur brute.

3. **Tables 28 et 29 — mapping colonne↔label correct** pour **tous** les cas
   (1E, 600, 640, 900, 940). Le cas 1E n'a pas de colonne ISO (C15 = `IDA ICE`) :
   le JSON le respecte.

4. **Cas 1E — cohérence physique et critère pass/fail : OK.**
   - `range_min ≤ mean_of_programs ≤ range_max` vérifié pour les **26** périodes.
   - **Correction d'une idée reçue** : le `Streubereich` n'est **PAS** le simple
     min/max des 4 programmes. La formule réelle est
     `range_max = moyenne + écart_max`, `range_min = max(0, moyenne − écart_max)`,
     `écart_max = max|programme − moyenne|` (bande symétrique, plancher à 0).
     Vérifiée **26/26**. L'hypothèse « range = min/max des programmes » est **fausse**.
   - `mean_of_programs` = moyenne arithmétique des 4 programmes : vérifié 26/26.

5. **Cas 600FF / 900FF, Tables 30 et 32 : mapping CORRECT** dès la passe 2.

---

## DIVERGENCES TROUVÉES en passe 2 (toutes CORRIGÉES en passe 3 — cf. section finale)

### DÉFAUT n°1 — BLOQUANT — Décalage de colonnes (+1) dans la Table 30 pour 600 / 640 / 900 / 940

Le JSON de passe 2 démarrait l'extraction **une colonne trop à droite** : il sautait la
colonne `Testprogramm` (B/J/R/Z) et décalait tous les programmes d'un cran, si bien que
`testprogramm_candidate` contenait en réalité l'ISO, `iso` contenait IDA ICE, etc., et
la colonne **EDSL-Tas était entièrement perdue** (champ `tas_edsl_9_5_2` pointait une
colonne vide). 286 cellules label↔colonne incohérentes. → **Corrigé en passe 3.**

### DÉFAUT n°2 — BLOQUANT — Entrées fantômes « 600 » et « 640 » dans la Table 32

La Table 32 ne contient que deux blocs (600FF en B–G, 900FF en J–O). Le JSON de passe 2
exposait en plus deux cas `600` et `640` qui référençaient les **mêmes cellules** que
600FF/900FF (doublons mal étiquetés ; extrêmes de 63.5 °C / −16.9 °C physiquement
impossibles pour des cas chauffés/refroidis). → **Corrigé en passe 3** (entrées supprimées).

### DÉFAUT n°3 — MINEUR mais trompeur — Métadonnées d'état incohérentes

`data_missing` déclarait faussement les Tables 30/32 « non extraites » ; `status` =
`CORRECTED` et `.md` `Statut : COMPLET` masquaient les défauts n°1/n°2. → **Corrigé en
passe 3.**

---

## Ce qui reste NON VÉRIFIABLE / hors périmètre (inchangé)

- **Tables 33 et 34** (profils horaires) et profils du 27 juillet : non extraits
  (reconnu par le producteur, déclaré dans `data_missing`). Non auditables.
- **Table 31** (charges de pointe horaires) : présente dans l'Excel, non extraite ;
  hors périmètre déclaré.
- **Données brutes horaires** (`Daten_Testprogramm`, 8760 h) : non extraites.
- **Fond normatif** (SIA 4010 / ASHRAE 140 / EN ISO 52016-1) : non réaudité ici — du
  ressort de `norm-analyst` (`traceability/test-1.spec.md` encore `BROUILLON ANCRÉ`).
- **Valeur candidat `testprogramm`** partout à 0 ou `null` (#DIV/0!) : normal (candidat
  IESVE pas encore exécuté) ; sera fourni par `ve-adapter-engineer`.

---

# RÉ-AUDIT PASSE 3 — 2026-07-30

Ré-exécution **à l'identique** du protocole de passe 2 (réouverture indépendante du
classeur via `openpyxl` `data_only=True`, reconstruction des en-têtes L15/L36/L57/L104,
comparaison exhaustive de **tous** les couples `{value, cell}`, contrôle label↔colonne
par cellule contre l'en-tête réel, réconciliation des comptes). Aucune affirmation du
rapport de correction n'a été reprise sans recontrôle contre l'Excel brut.

## En-têtes réels reconfirmés (vérité terrain, passe 3)

- **Table 30 (L57)** — blocs de colonnes réels :
  600 = **B/C/D/E/F/G**, 640 = **J/K/L/M/N/O**, 900 = **R/S/T/U/V/W**,
  940 = **Z/AA/AB/AC/AD/AE**, 600FF = **AH/AI/AJ/AK/AL/AM**, 900FF = **AP/AQ/AR/AS/AT/AU**
  (ordre : Testprogramm / `Daten Norm EN ISO 52016-1` / IDA ICE / EXCEL SIA 380/2 /
  Energy+/OpenStudio / EDSL-Tas ; la colonne `Month` précède chaque bloc : A/I/Q/Y/AG/AO).
- **Table 32 (L104)** — 600FF = **B/C/D/E/F/G**, 900FF = **J/K/L/M/N/O**
  (Max=L105, Min=L106, Average=L107). Identité 600FF/900FF confirmée par les valeurs
  (C105=63.5 = extrême FF ; K105=44.4).

## Résultats du ré-audit (script reproductible)

| Contrôle | Résultat passe 3 |
|---|---|
| Nœuds `{value, cell}` audités | **1336 / 1336** (0 non audité) |
| Divergences de **valeur** value↔cellule | **0** |
| Incohérences **label↔colonne** (par cellule, vs en-tête réel) | **0** |
| Incohérences **`_metadata.columns`** vs en-tête réel | **0** |
| `value: null` justifiés par une cellule d'erreur Excel réelle | **80 / 80** |
| `null` sans note explicative | **0** |
| Cellule d'erreur Excel convertie silencieusement en valeur | **0** |
| Cohérence 1E (`mean` = moy. arith., `range` = moy ± écart_max plancher 0, rmin ≤ mean ≤ rmax) | **26 / 26** |

**Réconciliation arithmétique des comptes** (aucun nœud manquant ni surnuméraire) :
T28 = (8×13)+(4×6×13) = 416 ; T29 = 416 ; T30 = 6×6×13 = 468 ; T32 = 2×6×3 = 36 ;
**total = 1336** (= nombre exact de nœuds trouvés). Nulls attendus = T30 (6×13) + T32
(2 `Average` #DIV/0!) = **80** (= nombre exact de nulls trouvés).

## Vérification défaut par défaut

- **DÉFAUT n°1 — CORRIGÉ ET VÉRIFIÉ.** Table 30, cas 600/640/900/940 :
  - Mapping colonne→label désormais **exact** pour les 6 cas (0 incohérence label↔colonne
    sur toutes les cellules ; 0 incohérence `_metadata.columns`).
  - `testprogramm_candidate` pointe bien la vraie colonne Testprogramm (B/J/R/Z pour
    600/640/900/940, AH/AP pour 600FF/900FF), cellule `#DIV/0!` → `value: null` **avec
    note**, pour les 13 périodes de chacun des 6 cas.
  - `tas_edsl_9_5_2` est **peuplé** (colonne G/O/W/AE/AM/AU) dans **tous** les mois **et**
    dans l'annuel des 6 cas — il n'est plus absent.
  - Structure annuelle : Table 30 range l'annuel (ligne 70) sous la clé `monthly.annual`
    (pleinement peuplé, tas inclus), et non dans un nœud `annual` de haut niveau
    (cf. remarque non bloquante ci-dessous).

- **DÉFAUT n°2 — CORRIGÉ ET VÉRIFIÉ.** Table 32
  (`operative_temperature_annual_extremes_celsius`) ne contient plus que **`600FF`** et
  **`900FF`**. Les entrées fantômes `"600"` et `"640"` sont **absentes**. Les blocs
  600FF (B–G) et 900FF (J–O) sont inchangés et exacts (valeurs value↔cellule à 1e-6 ;
  Max/Min candidat = 0 comme dans l'Excel, Average candidat = `null` car B107/J107 =
  `#DIV/0!`, avec note).

- **DÉFAUT n°3 — CORRIGÉ ET VÉRIFIÉ.**
  - `status` = `CORRECTED_PASS_3`.
  - `extraction_completeness.tables_extracted` = `[28,29,30,32]`, `cases_covered`
    conforme.
  - `data_missing` ne mentionne **plus** les Tables 30/32 comme « non extraites » ; il
    ne liste que ce qui est réellement hors périmètre (Tables 31/33/34, données brutes
    horaires).
  - `corrections[]` documente honnêtement les passes 1/2/3.
  - `test-1.ref.md` `Statut : COMPLET (CORRIGÉ - PASS 3)` + ERRATUM Pass 3 ; son tableau
    de mapping Table 30 (600=B/C/D/E/F/G, etc.) et Table 32 (600FF/900FF uniquement)
    concordent désormais avec le JSON et avec l'Excel.

## Absence de régression (recontrôle exhaustif, pas d'échantillonnage)

- Tables 28 et 29, **tous cas** (1E/600/640/900/940) : 0 divergence de valeur, 0
  incohérence label↔colonne.
- 600FF / 900FF des Tables 30 et 32 : inchangés et toujours exacts.
- Cohérence 1E (formule Streubereich réelle) : 26/26.

## Remarques NON bloquantes (pour information de `validation-engine-engineer`)

1. **Incohérence structurelle bénigne** : la Table 30 imbrique son annuel sous
   `monthly.annual` (et n'a pas de clé `annual` de haut niveau), alors que les Tables 28
   et 29 exposent l'annuel dans un nœud `annual` distinct de `monthly`. Les données sont
   **présentes et exactes** dans les deux cas ; le moteur doit simplement gérer les deux
   emplacements.
2. **Candidat Table 32** : Max/Min stockés à `0` (valeur littérale de B105/B106/J105/J106
   dans l'Excel), Average à `null` (#DIV/0!). Asymétrie **héritée fidèlement de la
   source** ; toutes les valeurs `testprogramm_*` sont de toute façon à recalculer côté
   `ve-adapter`.
3. **`Statut : COMPLET`** du `.md` s'entend au périmètre « tables de synthèse 28/29/30/32 » ;
   Tables 31/33/34 et données horaires brutes restent hors périmètre (déclaré honnêtement
   dans `data_missing`). Non bloquant pour le moteur, mais à garder en tête si un test
   ultérieur exige les profils horaires.
4. **`test-1.ref.md` §« Points pour qa-auditor » pt 1** pose encore la question « les
   limites correspondent-elles au min/max des 4 programmes ? ». La réponse auditée est
   **non** : la formule réelle est `moyenne ± écart_max` (plancher 0), vérifiée 26/26.
   À ne pas implémenter comme min/max brut dans le moteur. Nuance documentaire, non bloquante.

## Traçabilité de l'audit (reproductibilité)

Vérifications rejouables par réouverture de `Resultaterfassung_Test1.xlsx`
(`openpyxl`, `data_only=True`) : comparaison des **1336** couples `{value, cell}` ;
contrôle label↔colonne contre les lignes d'en-tête **15 / 36 / 57 / 104** ; contrôle
`_metadata.columns` ; formule `Streubereich` du cas 1E ; inventaire des 80 cellules
d'erreur Excel ; réconciliation des comptes.

- Fidélité valeur↔cellule : **1336/1336 OK**.
- Label↔colonne (toutes tables) : **0 incohérence**.
- `_metadata.columns` : **0 incohérence**.
- Cellules d'erreur : **80 capturées (null + note), 0 conversion silencieuse**.
- Table 32 : **0 cas fantôme** (600/640 supprimés).
- Cohérence 1E : **26/26 OK**.

## SIGNATURE

Les trois défauts de passe 2 sont **corrigés et vérifiés indépendamment**. Aucun défaut
nouveau, aucune régression. Le livrable de données de référence `test-1.ref.json`
(+ `test-1.ref.md`) est **conforme à la source brute** et peut être **transmis à
`validation-engine-engineer`**.

> Réserve de périmètre : cette signature porte sur la **fidélité d'extraction** des
> Tables 28/29/30/32 vis-à-vis de l'Excel d'éval SIA. Elle **ne vaut pas** validation du
> fond normatif (SIA 4010 / ASHRAE 140 / EN ISO 52016-1), qui reste ouvert côté
> `norm-analyst` (`traceability/test-1.spec.md` encore `BROUILLON ANCRÉ`), ni signature
> d'une matrice de traçabilité clause→code→test (celle-ci sera signée quand le moteur et
> ses tests existeront).

**AUDITÉ OK — 2026-07-30** (extraction des données de référence Test 1, passe 3).

_Audité par : qa-auditor._

---

## Élément audité n° 2 — `swiss_sia/` (extraction VE Test 1)

- **Producteur** : dépôt externe `C:\Users\ulysse.couliou\Documents\IES
  Internship\IES-Intership-general-repo`, paquet `swiss_sia/` (90 modules) —
  PAS produit dans ce dépôt. Ce dépôt n'est PAS consolidé ici (ADR-001 § 8,
  « décision de consolidation à prendre » — hors périmètre de cet audit).
- **Auditeur** : `ve-adapter-engineer`, dans le cadre de l'étape 4 du
  pipeline `/nouveau-test 1`.
- **Méthode** : lecture statique du code contre `refs/VEScripts-API-VE2023.pdf`
  (extraction texte `pdftotext -layout`, relue intégralement, sections
  §6.1.2/3/9/14/28/29/30/31/32/36/39/40/46 en particulier) et contre
  `traceability/test-1.spec.md` / `refs/reference-data/test-1.ref.json`.
- **⚠ NON EXÉCUTÉ — VE indisponible dans cet environnement.** Aucune ligne de
  `swiss_sia/` n'a été lancée. Le verdict ci-dessous repose UNIQUEMENT sur
  (a) la cohérence du code avec l'API documentée et (b) la cohérence
  logique avec la spec/les données de référence — jamais sur une exécution
  observée. Là où `swiss_sia/` affirme lui-même avoir été exécuté contre une
  VE réelle (§ C.2 ci-dessous), cette affirmation est rapportée comme telle,
  **non revalidée**.

### A. Géométrie de la cellule — **GARDER**

- Fichier : `swiss_sia/reference_model/sia4010/case_geometry.py` +
  configuration `config/sia4010_classes_1a_1b.json` (paramètres `cell_*`,
  `south_window_*`, statut `CONFIRMED`, source citée : « SIA 4010 Test 1 and
  Test 2 specifications, page 1, dimensioned cell diagram »).
- **Recoupement indépendant réalisé** : les valeurs (largeur facade sud
  8,0 m = 2×0,5 + 2×3,0 + 1,0 ; profondeur 6,0 m ; hauteur 2,7 m ; 2 fenêtres
  3,0×2,0 m, allège 0,2 m) concordent avec `traceability/test-1.spec.md` § 4
  (« Dimensions intérieures : 6,0 m × 8,0 m, hauteur 2,7 m … Deux fenêtres au
  Sud, 2,0 m × 3,0 m chacune … allèges 0,2 m / 0,5 m, trumeaux 0,5 m et
  1,0 m »). Le check interne du module lui-même
  (`abs((2*margin + 2*window_width + gap) - width) > 1e-9`) est correct et
  passe avec ces valeurs.
- **Verdict : GARDER** les valeurs numériques (reprises dans
  `ve_adapter/test1_adapter.py::GEOMETRIE_CELLULE`, avec le même garde-fou de
  fermeture dimensionnelle). Le CODE de construction de géométrie
  (`Sia4010CellGeometryGenerator`) n'est PAS porté : il produit un modèle
  domaine abstrait (`GeometryModel`) qui doit ensuite être traduit en objets
  VE réels par un mécanisme non retrouvé dans l'API documentée (cf. § D).

### B. Création CDB (matériaux/constructions/couches) — **GARDER le pattern, ne pas copier le code**

- Fichier : `swiss_sia/reference_model/ve_asset_provisioner.py`
  (`_create_materials`, `_create_construction`, ~2 400 lignes au total pour
  un système générique multi-tests).
- **B.1 — Symboles API utilisés, tous vérifiés présents dans
  `refs/VEScripts-API-VE2023.pdf`** : `VECdbProject.create_material()` /
  `.create_construction()` / `.get_material_ids()` / `.get_construction_ids()`
  (§6.1.32) ; `VECdbMaterial.set_properties()`/`get_properties()` (§6.1.31) ;
  `VECdbConstruction.add_layer()`/`set_const_class()`/`set_properties()`/
  `delete_layer()`/`get_layers()` (§6.1.28) ; `VECdbLayer.get_id()`/
  `set_properties()`/`get_properties()` (§6.1.30). **Aucun symbole inventé
  trouvé.**
- **B.2 — Discipline « créer puis relire et vérifier »** : le code écrit une
  propriété puis relit `get_properties()` pour confirmer la persistance
  avant de continuer (`_verify_material_properties`,
  `_verify_construction_properties`, `_verify_layer_properties`). C'est
  exactement la discipline demandée par `CLAUDE.md` (« messages d'erreur qui
  disent précisément quel objet VE manquait ») et par la doctrine du présent
  projet. **Digne d'être reproduit.**
- **B.3 — Prudence VE 2025.2 documentée en commentaire** : une construction
  neuve est créée par VE avec une couche par défaut ; la supprimer avant
  d'en ajouter une seule sur une construction **vitrée** provoque un crash
  natif de VE.exe (accès mémoire invalide) — la couche par défaut n'est donc
  supprimée qu'*après* ajout des couches définitives pour les constructions
  vitrées, et avant pour les opaques. Information non vérifiable par moi
  sans VE réelle, mais plausible et prudente ; reprise sous forme allégée
  dans `ve_adapter/test1_adapter.py::creer_construction_opaque` (variante
  opaque uniquement — le Test 1 n'a pas de construction vitrée à créer par
  ce mécanisme, la fenêtre étant hors périmètre de cette étape).
- **Verdict : GARDER le pattern** (créer → écrire → relire → vérifier,
  échouer fort sur divergence), **JETER la réutilisation verbatim** : le
  fichier source est generique multi-tests (matérialise aussi Test 2/3/…),
  couplé à une abstraction (`AssetManifest`) absente de ce dépôt, et sa
  logique de « réutilisation d'un actif existant » (désambiguïsation par
  description) est hors périmètre pour un Test 1 qui doit s'exécuter dans un
  projet VE jetable dédié à un seul cas (cf. § C.1). Réécrit en plus court,
  spécifique, dans `ve_adapter/test1_adapter.py`.

### C. Extraction des résultats APS — **GARDER l'algorithme, CORRIGER les liaisons**

- Fichier : `swiss_sia/reference_model/sia4010/qualified_aps.py` (+
  `swiss_sia/simulation_results.py` pour les primitives `ResultsReader`).
- **C.1 — Confirmation indépendante du § 6 de `traceability/test-1.spec.md`.**
  `Sia4010QualifiedApsExtractor.test1_reference_only_observed()` construit
  explicitement une extraction « sans bande, sans tolérance » pour les cas
  600/640/900/940/600FF/900FF (docstring : « It deliberately does not create
  `ExpectedResult` objects or tolerances »), et réserve le seul calcul avec
  critère (`test1_observed()`) au cas 1E. **C'est très exactement la
  correction que `norm-analyst` a apportée au § 6 de la spec** (« Es gibt
  dafür kein Abweichungskriterium » pour les 6 cas de base, Streubereich
  pour 1E seul), obtenue par une équipe différente, sur un dépôt différent,
  à une date antérieure (29/07) à la correction de spec de ce dépôt
  (30/07). **Recoupement fort, indépendant, en faveur de la lecture
  normative retenue.**
- **C.2 — Symboles API vérifiés** : `ResultsReader.open()` /
  `get_room_results(room_id, aps_var, vista_var, var_level)` (start_day/
  end_day omis, donc valeurs par défaut -1/-1 = année complète — usage
  CORRECT selon §6.1.14) / `get_variables()` / `get_units()` / `get_room_list()`
  — tous confirmés dans `refs/VEScripts-API-VE2023.pdf` §6.1.14.
- **C.3 — Agrégation mensuelle correcte.** `_monthly_sums`/`_monthly_means`
  utilisent `calendar.monthrange(year, month)` (nombre réel de jours par
  mois) et vérifient explicitement `calendar.isleap(year) == False` et
  `len(series) == 365*24` avant d'agréger — donc PAS de mois à 30 jours
  fixes ni d'année bissextile silencieuse. Algorithme rigoureux.
  **Verdict : GARDER l'algorithme** — réimplémenté (pas copié) dans
  `ve_adapter/test1_adapter.py::_agreger_mensuel_sommes` /
  `_agreger_mensuel_moyennes`, avec les mêmes garde-fous.
- **C.4 — CORRIGER : les liaisons de variables APS ne sont PAS re-vérifiables
  ici.** Le fichier `config/sia4010_aps_bindings_ve_runtime.json` (dépôt
  externe) affirme des noms de variable APS (`"Room units heating load"`,
  `"Comfort temperature"`, etc.) **confirmés par une sonde VE réelle le
  2026-07-28/29** (checksum + fichier de preuve référencés). Cette
  affirmation n'a **pas pu être revalidée** dans cet environnement (pas de
  VE). Deux réserves supplémentaires, trouvées en lisant ce fichier de
  liaisons :
  - la sonde documentée porte sur un projet et un fichier `.aps` génériques
    nommés `"test"`/`"test.aps"` — rien ne prouve qu'elle porte sur un cas
    600/640/… du Test 1 réellement construit selon la spec ;
  - la justification de `"operative_temperature"` (« IES documents dry
    resultant temperature as operative temperature ») cite une page d'aide
    **VE2025** (`https://help.iesve.com/ve2025/...`), alors que la référence
    API de ce projet est **VE2023** — même type d'écart de version que celui
    déjà documenté par `norm-analyst` pour ASHRAE 140 (2017 vs 2023,
    `traceability/test-1.spec.md` § 4/§ 8 pt 2).
  **Verdict : CORRIGER (statut abaissé)** — ces liaisons sont portées dans
  `ve_adapter/test1_adapter.py::LIAISONS_APS_CANDIDATES` avec attribution
  explicite et statut « non confirmé », et `extraire_candidat_test1()`
  refuse de s'en servir sans that l'appelant l'accepte explicitement
  (`accepter_liaisons_non_confirmees=True`).
- **C.5 — JETER pour l'extraction de confiance : la recherche de variable
  par jetons flous** (`swiss_sia/simulation_results.py::find_aps_variable`,
  utilisée par `aps_probe.py` pour la découverte). Le module source
  lui-même l'interdit explicitement pour l'extraction notée
  (`qualified_aps.py`, commentaire : « There is no token fallback in this
  module »). **Verdict cohérent avec CLAUDE.md** — repris à l'identique dans
  `ve_adapter/test1_adapter.py::decouvrir_candidats_variable()`, marqué
  utilisable UNIQUEMENT pour aider un humain à confirmer une liaison face à
  une VE réelle, jamais appelé par le chemin d'extraction de confiance.

### D. Génération de la géométrie (import gbXML) — **CORRIGER (bug potentiel non vérifié)**

- Fichier : `swiss_sia/reference_model/ve_api.py`, ligne 493 :
  `self.iesve.ImportGBXML.import_file(...)` (minuscule).
- `refs/VEScripts-API-VE2023.pdf` §6.1.9 documente la méthode avec un **I
  majuscule** : `Import_file(file_name, heal_geometry, cap_mode,
  cap_height)`. Python étant sensible à la casse, l'appel du dépôt externe
  échouerait par `AttributeError` si l'objet `iesve.ImportGBXML` respecte
  la casse documentée. **Ni le dépôt externe ni moi n'avons observé cet
  appel s'exécuter réellement** (aucune trace dans `.codex_tmp/` d'un
  import gbXML réussi pour le Test 1) — impossible de savoir si ce point a
  déjà été heurté et contourné, ou jamais exercé. **Verdict : CORRIGER /
  signaler**, pas de correction appliquée dans ce dépôt (la fonction
  d'import n'est pas appelée automatiquement par
  `ve_adapter/test1_adapter.py` — voir § suivant).
- **Constat plus large : la création de géométrie par script n'est PAS
  couverte par l'API documentée** au-delà de l'import gbXML — aucun
  constructeur de type « créer une pièce/un corps depuis zéro » trouvé dans
  `refs/VEScripts-API-VE2023.pdf`. `case_registry.py` (dépôt externe)
  confirme indirectement cette difficulté : seul le cas 600 est
  `GUARDED_MUTATION_READY`, tous les autres cas restent
  `RUNTIME_QUALIFICATION_READY` (sonde exécutée mais non pleinement
  vérifiée) — cohérent avec une géométrie qui n'est pas fiablement
  reproductible par script pur. **Ce point reste ouvert et n'est PAS résolu
  dans ce dépôt** : `ve_adapter/test1_adapter.py` ne fournit délibérément
  aucune fonction de génération/import de géométrie (écrire un gbXML non
  vérifiable contre une VE réelle aurait été fabriquer un contenu non
  vérifiable de plus) ; seules les cotes vérifiées (§ A) sont documentées.
  Toutes les fonctions de création de matériaux/constructions/gabarit de ce
  module supposent une cellule déjà modélisée par un autre moyen.

### E. Coefficient de surface externe (Table 7-7) — **CORRIGER, contredit `test-1.spec.md`**

- Fichier : `swiss_sia/reference_model/sia4010/normalized_external_inputs.py`
  (`load_iso_test_cell`) + configuration `config/sia4010_classes_1a_1b.json`,
  paramètre `iso_lightweight_construction.value.surface_coefficients_w_m2k`
  = `{"inside": 8.29, "outside": 29.3}`.
- Ce couple de valeurs est appliqué de façon **constante, identique pour
  mur/toit/plancher**, sans distinction de type de surface, sans citation
  de source (le `source_locator` du paramètre cite uniquement
  `NREL/TP-472-6231` pour les propriétés de COUCHE, pas pour ce couple de
  coefficients).
- **Contradiction directe avec `traceability/test-1.spec.md` § 3.1**
  (ASHRAE 140:2023 Table 7-7, vérifiée mot pour mot par `norm-analyst`) :
  mur 11,9/21,6 W/(m²·K), toit 14,4/21,8, plancher surélevé 0,8/5,2,
  fenêtre 8,0/17,8 — AUCUNE de ces quatre paires ne vaut `(8,29 ; 29,3)`, et
  la Table 7-7 différencie explicitement par type de surface, ce que le
  dépôt externe ne fait pas. Le code externe n'implémente pas non plus le
  choix de branche §7.2.1.9.3 (a)/(b.1)/(b.2).
- **Deuxième point trouvé en lisant §6.1.28 de l'API pour cet audit** (non
  mentionné par ADR-001 § 3, qui ne cite que `VECdbLayer.convection_
  coefficient`) : `VECdbConstruction.set_properties()` accepte AUSSI
  `outside_surface_resistance` / `outside_surface_emissivity` /
  `inside_surface_resistance` / `inside_surface_emissivity` **au niveau de
  la construction entière**. Deux mécanismes API distincts existent donc
  pour influencer le comportement de surface externe, et rien ne prouve
  lequel (ou aucun des deux) pilote réellement le calcul dynamique
  d'ApacheSim au pas de temps.
- **Verdict : CORRIGER — ne pas porter ces valeurs (8,29/29,3), ni le choix
  d'un seul mécanisme API sans preuve.**
  `ve_adapter/test1_adapter.py::COEFFICIENTS_SURFACE_TABLE_7_7` reprend les
  quatre paires de la Table 7-7 (mot pour mot, comme `test-1.spec.md`), et
  `appliquer_coefficient_surface_externe_table_7_7()` est fournie
  **désactivée par défaut**, isolée, documentant explicitement les deux
  mécanismes API et l'absence de décision. Point renvoyé à
  `norm-analyst`/`ve-adapter-engineer` (session avec VE réelle).

### F. Matériaux légers/lourds (Tables 7-2/7-27) — **GARDER comme candidat concordant, statut inchangé**

- Fichier : `config/sia4010_classes_1a_1b.json`, paramètres
  `iso_lightweight_construction` / `iso_heavyweight_construction`, statut
  **`PUBLIC_REFERENCE`** (pas `CONFIRMED`) — le dépôt externe lui-même
  n'élève pas ces valeurs au rang de confirmées.
- **Recoupement : les valeurs de couches (conductivité, épaisseur, masse
  volumique, capacité thermique) concordent avec `traceability/test-1.spec.md`
  § 4** (Table 7-2/7-27 ASHRAE 140:2023), bien que la source citée par le
  dépôt externe soit différente (`NREL/TP-472-6231, Judkoff & Neymark 1995`
  — le rapport BESTEST original — plutôt qu'ASHRAE 140:2023). **Ce
  recoupement, obtenu par deux généalogies documentaires différentes qui
  convergent sur les mêmes chiffres, renforce la présomption sans lever la
  réserve** (SIA 4010 cite formellement EN ISO 52016-1:2017, ni l'un ni
  l'autre document en main ici).
- **Écart trouvé et NON reproduit** : le dépôt externe fixe la masse
  volumique/capacité thermique de l'isolant de plancher à des valeurs
  non nulles (`10 kg/m³` / `1400 J/(kg·K)`) sans le documenter comme un
  choix délibéré, alors qu'ASHRAE 140:2023 note (a)/(b) dit « minimum que le
  logiciel testé autorise, mais pas < 0 » — une formulation qui laisse la
  valeur exacte dépendante d'IESVE, pas d'une valeur fixe universelle.
  **Verdict : CORRIGER ce point précis** — `ve_adapter/test1_adapter.py`
  laisse `masse_volumique`/`capacite_thermique` de l'isolant de plancher à
  `None` et **refuse** de créer le matériau tant que la valeur n'est pas
  fixée avec `ve-adapter-engineer` (contre ce qu'IESVE accepte réellement).
- **Verdict global : GARDER les chiffres de couche** (repris à l'identique
  dans `ve_adapter/test1_adapter.py::MATERIAUX_LEGERS`/`MATERIAUX_LOURDS`,
  même statut de réserve que `test-1.spec.md`), **CORRIGER l'isolant de
  plancher** (valeur non fixée, refus explicite plutôt que copie aveugle).

### G. Simulation ApacheSim — **CORRIGER une citation d'ADR-001, GARDER le code externe**

- Fichier : `swiss_sia/reference_model/sia4010/apachesim_qualification.py`.
- Utilise `sim.set_options(options)` / `sim.get_options()` (avec relecture
  et comparaison stricte de chaque option écrite) / `sim.run_simulation
  (queue_to_tasks=False)`.
- **Incohérence trouvée dans le PDF source lui-même** :
  `refs/VEScripts-API-VE2023.pdf` §6.1.3 montre, dans son exemple « Basic
  usage », `s.save_options({...})`, mais la table formelle « Methods
  Defined Here » du **même paragraphe** ne définit PAS `save_options` — elle
  définit `set_options()`/`get_options()`/`reset_options()`. `ADR-001
  -architecture-MSP.md` § 3 cite `save_options` (repris de l'exemple, pas de
  la table de méthodes). **Le dépôt externe utilise `set_options`/
  `get_options`, qui EST dans la table formelle, avec relecture stricte en
  plus.** Je retiens `set_options`/`get_options` comme la version la plus
  fiable des deux, et signale l'incohérence pour correction d'ADR-001 § 3.
- **Verdict : GARDER le choix de méthode ApacheSim du dépôt externe** ;
  repris dans `ve_adapter/test1_adapter.py::lancer_apachesim_cas` (avec la
  même discipline de relecture/vérification).

### Synthèse

| Élément | Verdict | Porté dans ce dépôt |
|---|---|---|
| Géométrie (dimensions) | GARDER | `test1_adapter.py::GEOMETRIE_CELLULE` |
| Géométrie (code de génération) | JETER (hors périmètre API vérifiée) | non porté |
| Pattern création CDB (créer→écrire→relire→vérifier) | GARDER (pattern) | réécrit, `test1_adapter.py::creer_materiau`/`creer_construction_opaque` |
| Code CDB verbatim (`ve_asset_provisioner.py`) | JETER (copie) | non porté |
| Algorithme d'agrégation mensuelle (`calendar.monthrange`) | GARDER | réécrit, `test1_adapter.py::_agreger_mensuel_*` |
| Séparation 1E (critère) / autres cas (informatif) | GARDER (confirme la spec) | `test1_adapter.py::extraire_candidat_cas` |
| Liaisons de variables APS nommées | CORRIGER (non re-vérifiable) | portées comme *candidates non confirmées*, `LIAISONS_APS_CANDIDATES` |
| Recherche de variable par jetons flous | JETER pour l'extraction notée, GARDER pour la découverte | `decouvrir_candidats_variable` (discovery only) |
| Import gbXML (casse `import_file`) | CORRIGER (bug potentiel, non vérifié) | signalé, non appelé automatiquement |
| Coefficient de surface externe (8,29/29,3 constant) | CORRIGER (contredit Table 7-7) | NON porté ; Table 7-7 reprise, application désactivée par défaut |
| Matériaux légers/lourds (couches) | GARDER (concordant, même réserve) | `test1_adapter.py::MATERIAUX_LEGERS`/`MATERIAUX_LOURDS` |
| Isolant de plancher (densité/cp) | CORRIGER (valeur non fixée sans le dire) | laissé `None`, création refusée tant que non fixé |
| Méthode ApacheSim (`set_options` vs `save_options`) | GARDER le choix externe ; CORRIGER ADR-001 § 3 | `test1_adapter.py::lancer_apachesim_cas` |

**Aucun symbole `iesve` cité dans ce dépôt (`ve_adapter/test1_adapter.py`)
n'est absent de `refs/VEScripts-API-VE2023.pdf`.** Chaque symbole non
totalement confirmé (orthographe d'énum, existence d'un constructeur sans
argument pour `AirExchange`/`EnergyGain`, mécanisme de coefficient de
surface) est marqué `# ⚠ À VÉRIFIER API` dans le code et listé explicitement
dans la docstring de module.

**AUDITÉ — 2026-07-30** (extraction VE Test 1, ⚠ non exécuté contre une VE
réelle — audit statique uniquement, cf. réserve en tête de section).

_Audité par : ve-adapter-engineer._

---

# Élément audité n° 3 — Confrontation de `test1_adapter.py` à une VE réelle (sonde v2)

**Date : 2026-08-06. Nature : audit d'EXÉCUTION**, le premier de ce dépôt. Il
lève la réserve en tête de l'élément n° 2 (« ⚠ non exécuté contre une VE
réelle — audit statique uniquement »), mais **pour les seuls symboles
effectivement atteints par la sonde** : la création de constructions n'a
toujours pas abouti, elle a seulement échoué plus loin.

Source : `outputs/sonde_test1_600.json`, produit par
`Run_VE_SIA4010_Sonde_Test1.py` dans une VE 2025 ouverte sur le cas 600.
11 étapes OK, 1 échec attendu.

## DÉFAUT n° 4 — BLOQUANT — Énumérés cherchés sur la mauvaise classe

`creer_materiau` et `creer_construction_opaque` résolvaient
`element_categories`, `construction_class` et `material_categories` sur
`iesve.VECdbProject`. VE répond :

> `Enum 'iesve.<class 'iesve.VECdbProject'>.element_categories' introuvable`

Ces énumérés sont portés par le **module** `iesve`.

**Ce que la synthèse de l'élément n° 2 affirmait** : « Aucun symbole `iesve`
cité dans ce dépôt n'est absent de `refs/VEScripts-API-VE2023.pdf`. » L'énoncé
reste exact — et c'est précisément sa limite. **Un symbole présent dans la
documentation n'est pas un symbole atteignable sur l'objet qu'on interroge.**
Le contrôle statique portait sur l'existence du nom, pas sur son conteneur.

La documentation a sa part : le titre « 6.1.32.4 Enums Defined Here » range ces
énumérés sous `VECdbProject`. Mais **la prose de la même section écrit
`'iesve.construction_class.none'`**, c'est-à-dire le chemin module. L'indice
contredisait le titre, sur la même page ; il n'a pas été lu.

**CORRIGÉ** : trois sites d'appel dans `ve_adapter/test1_adapter.py` passent de
`iesve.VECdbProject` à `iesve`. Verrouillé par
`ve_adapter/tests/test_enums_iesve.py::test_les_enums_vivent_sur_le_module_pas_sur_vecdbproject`.

## DÉFAUT n° 5 — BLOQUANT — `material_categories.opaque` n'existe pas

`creer_materiau` demandait le membre `opaque` à `material_categories`. Cet
énuméré n'a que **20 familles de bibliothèque** (`all`, `asphalts`, `boards`,
`bricks`, `carpets`, `concretes`, `gravels`, `insulating`, `metals`, `plaster`,
`screeds`, `sands`, `titles`, `timber`, `index_glass`, `other`, `floor_finish`,
`susp_ceiling`, `composite_layer`, `glass`). `opaque` appartient à
`construction_class`. Les deux énumérés avaient été confondus.

**Ici la documentation était correcte et complète** : §6.1.32.4 liste ces
20 membres et n'a jamais fait figurer `opaque` parmi eux. L'erreur est
entièrement de notre fait. L'appel aurait échoué même une fois le conteneur
corrigé.

**CORRIGÉ** : `'opaque'` → `'other'`, avec la justification en commentaire —
`material_categories` est un **classement de bibliothèque sans effet sur la
simulation**, les propriétés physiques étant portées par `definition`. Le dire
explicitement évite qu'un relecteur le prenne pour un paramètre physique.

## DÉFAUT n° 6 — MINEUR — La sonde a introspecté une liste, pas un projet

`cdb.get_projects()` renvoie un **dictionnaire**
`{'project': [...], 'system': [...], 'manufacturer': [...]}` — ce que
§6.1.32.4 documente d'ailleurs sous `project_types`. La sonde faisait
`projets[0]`, ce qui rend la **clé** `'project'`, une chaîne. Elle a donc
rapporté `['append', 'clear', 'copy', 'count', 'extend', 'index', 'insert',
'pop', 'remove', 'reverse', 'sort']` comme étant les attributs de
`VECdbProject`.

Un dictionnaire est vrai, itérable et indexable : **rien n'a levé, et le
rapport paraissait valide.** Seule la lecture des attributs relevés l'a
démasqué. C'est le mode de défaillance le plus dangereux pour ce projet — un
résultat faux mais crédible.

**CORRIGÉ** : `scripts/run_test1_dans_ve.py::_premier_projet_cdb`, qui indexe
par type de projet et **refuse** de rendre une liste, un dict ou une chaîne à
la place d'un projet. Une étape en échec explicite remplace le relevé faux.
Sept tests dans `engine/tests/test_run_test1_preflight.py`.

## Ce que la sonde a CONFIRMÉ

- `iesve.VEProject.get_current_project()`, `.models`,
  `iesve.VECdbDatabase.get_current_database()`, `.get_projects()` : présents,
  signatures conformes.
- **L'affectation de la météo DRYCOLD fonctionne** (`assigner_meteo_drycold`),
  ce qui était le point le plus incertain de l'élément n° 2 § A.
- 149 énumérés relevés sur le module, figés pour les 4 employés dans
  `refs/reference-data/iesve-enums-ve2025.json` via
  `scripts/freeze_iesve_enums.py`. **Le fichier est produit par script, jamais
  saisi à la main** : une première version rédigée affirmait que la valeur 3
  était absente de `construction_class`, alors que
  `soft_landscaping = 3`. Le hook `.claude/hooks/garde_refs.py` a bloqué cette
  écriture directe — il a joué son rôle.

## Dérive d'API VE 2023 → VE 2025, mesurée

Comparaison membre par membre du relevé d'exécution contre §6.1.32.4, par test
reproductible (`test_les_membres_releves_concordent_avec_la_documentation`) :

| Énuméré | Écart |
|---|---|
| `construction_class` (7) | aucun |
| `material_categories` (20) | aucun |
| `AirExchange_type` (3) | aucun (documenté § 6.1.2, p. 23 — pas sous `VECdbProject`) |
| `element_categories` (39) | +`struct_fram` (alias de `struct_frame`, 26) ; +`surface_tile` (37) |

**Aucun membre documenté n'a disparu.** `surface_tile` est le seul ajout réel.
La documentation VE 2023 reste donc utilisable pour ces énumérés — le test
échouera si une version future s'en écarte.

## Ce qui reste NON VÉRIFIÉ

- **`create_material` / `create_construction` / `add_layer` / `set_properties`
  n'ont jamais été exécutés avec succès** : la sonde échouait avant. Le
  pattern « créer → écrire → relire → vérifier » retenu en § B.2 reste un
  audit statique.
- La réserve VE 2025.2 sur la suppression de la couche par défaut d'une
  construction **vitrée** (§ B.2) n'est ni confirmée ni infirmée.
- Le coefficient de surface externe (§ E) et les liaisons APS (§ C) sont hors
  de portée de cette sonde.

**AUDITÉ — 2026-08-06** (exécution réelle, VE 2025, cas 600).
_Défauts 4 et 5 corrigés dans `ve_adapter/test1_adapter.py` ; défaut 6 dans
`scripts/run_test1_dans_ve.py`. Non signé : la création de constructions doit
d'abord aboutir dans VE._

---

## DÉFAUT n° 7 — BLOQUANT — Les lanceurs importaient depuis l'ANCIEN dépôt

**Trouvé en usage réel, le 2026-08-06**, au premier lancement de la sonde APS
dans VE :

```
ImportError: cannot import name 'sonde_aps' from 'scripts'
(C:\Users\ulysse.couliou\Documents\SIA_Compliance_Scripts\scripts\__init__.py)
```

VEScripts garde le **même interpréteur** d'un clic sur Run au suivant :
`sys.modules` persiste. Le paquet `scripts` de l'ancien dépôt y était en
cache. `sys.path.insert(0, _RACINE)` n'y change rien — **un module déjà chargé
n'est jamais rechargé.**

**Le cas visible était le moins grave.** `sonde_aps` n'existe que dans le dépôt
consolidé, donc l'import a levé. Mais `run_test1_dans_ve` **existe dans les
deux** : pour `Run_VE_SIA4010_Sonde_Test1.py`, l'import aurait **réussi**, en
chargeant la version antérieure aux corrections des défauts 4 et 5 — donc en
rejouant les mêmes échecs d'énumérés, sur du code qu'on croyait corrigé, sans
le moindre avertissement. C'est le mode de défaillance déjà rencontré au
défaut n° 6 : rien ne lève, et le résultat paraît valide.

`Run_VE_SIA4010_APS_Probe.py`, écrit avant, connaissait ce piège et purgeait
`swiss_sia.reference_model`. Cette précaution n'a pas été reprise dans les
nouveaux lanceurs — elle aurait dû l'être.

**CORRIGÉ** dans les deux lanceurs, en trois temps :

1. purge de `sys.modules` pour `scripts`, `ve_adapter`, `engine`, `ui` et
   `swiss_sia` — **avant** le premier import du projet, ce qui interdit de
   placer ce code dans un module du projet (duplication assumée) ;
2. la racine du dépôt passe **en tête** de `sys.path`, retirée puis
   réinsérée — `if _RACINE not in sys.path` laissait un autre dépôt devant ;
3. `scripts/amorcage.py::controler` confronte le `__file__` de chaque module
   du projet à la racine attendue et **refuse de lancer** (code 2) en nommant
   le fichier fautif, plutôt que de produire un résultat issu de la mauvaise
   source.

28 tests dans `engine/tests/test_amorcage.py`, dont la détection du cas
silencieux et la vérification que la purge précède bien le premier import.

**Portée, mesurée et non supposée.** L'ancien dépôt contient `scripts`,
`ve_adapter`, `engine` et `ui` — mais **pas** `swiss_sia`. Or les 22 autres
lanceurs `Run_VE_SIA4010_*.py` n'importent que `swiss_sia`, et le purgent
déjà. Seuls les deux lanceurs ajoutés le 2026-08-06 importaient les quatre
paquets en collision :

```
$ grep -lE "^\s*(from|import) (scripts|ve_adapter|engine|ui)\b" Run_VE_*.py
Run_VE_SIA4010_Sonde_APS.py
Run_VE_SIA4010_Sonde_Test1.py
```

L'exposition était donc limitée à ces deux fichiers, tous deux corrigés. Rien
à reprendre sur les 22 autres.

**Cause racine non traitée** : l'ancien dépôt `SIA_Compliance_Scripts` est
toujours sur disque et VE le trouve. La purge rend chaque run sûr, mais ne
supprime pas la source de confusion, et un futur lanceur qui importerait
`scripts` sans amorçage retomberait dedans. L'archivage du dépôt A reste à
décider.
