# État des lieux — SIA 4010 Validation Navigator

**Date : 2026-08-01**
**Destinataire : commanditaire**
**Base : 5 revues indépendantes (produit, règles, tests, traçabilité, risques), chacune
contre-expertisée par un vérificateur adverse, plus 6 contrôles de recoupement effectués
pour la rédaction de cette note.**

Convention de citation : `(A)` = dépôt `C:\Users\ulysse.couliou\Documents\SIA_Compliance_Scripts`,
`(B)` = dépôt `C:\Users\ulysse.couliou\Documents\IES Internship\IES-Intership-general-repo`.
Les chemins sont relatifs à la racine du dépôt cité.

---

## 1. En une page

### Le constat en trois phrases

La plomberie est très avancée et la couche de vérité est réellement bonne ; le résultat de
validation est nul. Le navigateur existe dans VE, les valeurs de référence officielles sont
extraites et auditées cellule par cellule, le moteur de comparaison du Test 1 résiste à des
mutations agressives — mais **aucun cas de test SIA n'a jamais été construit puis simulé dans
IESVE**, donc **0 des 8 classes de validation** est atteinte et le classeur produit affiche un
score SIA 4010 de 0. Et **l'intégralité de ce travail n'est sauvegardée nulle part** : le dépôt A
n'a aucun dépôt distant et ne suit que 25 fichiers.

### Chiffrage de l'avancement

| Bloc | Poids retenu | Fait | Base de l'estimation |
|---|---|---|---|
| Référence officielle figée (données) | 30 % | **75 %** | Test 1 : 1352/1352 cellules concordantes, revérifiées par deux relecteurs indépendamment. Tests 2 à 7 : 84 métriques avec bande extraites des 7 classeurs, mais interprétation normative non contrôlée et aucune spec pour 2/3/5 |
| Moteur de comparaison | 15 % | **30 %** | Test 1 complet et outillé (A) ; comparateur générique fail-closed (B). 2 tests sur 7 |
| Génération + exécution des cas dans VE | 30 % | **5 %** | 1 générateur prêt sur 30 cas (Test 1 / cas 600) ; 0 modèle à checksum valide, 0 résultat ApacheSim, 0 évaluation reliée à une simulation |
| Livrables (Excel, PDF, UI) | 15 % | **60 %** | La chaîne produit réellement un classeur de 31 feuilles, un PDF et un ZIP de preuves — mais le contenu de conformité SIA 4010 est vide |
| Gouvernance (versionnement, CI, traçabilité signée) | 10 % | **25 %** | Rien n'est versionné, la CI n'a jamais tourné, la matrice de traçabilité n'existe pas |

**Total pondéré : environ 40 % de l'objectif produit.**

Réserve importante sur ce chiffre : les 40 % faits sont les 40 % les moins risqués (lire des
classeurs, comparer des nombres en Python pur). Les 60 % restants concentrent tout ce qui dépend
d'IESVE, c'est-à-dire tout ce que personne n'a encore exécuté une seule fois.

Le seul chiffre qui compte vraiment pour un dossier SIA reste : **0 classe de validation sur 8**,
et **0 cas exact sur 30** produit puis simulé.
(`sia4010_evidence/autonomy/navigator/sia4010_all_classes_navigator.json` (B) :
`exact_cases=30`, `checksum_valid_model_cases=0`, `checksum_valid_apachesim_cases=0`,
`simulation_linked_aps_evaluations=0`, `ready_for_official_review=0`.)

### Note de maturité

Les cinq relecteurs ont noté 4 / 8 / 6 / 5,5 / 5. Les contre-expertises ont fait baisser deux de
ces notes (tests : 6 → 5 ; règles : 8 est intenable une fois su que le cas 1E, seul porteur d'un
verdict, n'est modélisable par rien dans le dépôt). **Note retenue : 5/10.** Un produit dont
l'ingénierie est meilleure que sa gestion.

---

## 2. Ce qui est solide

Ces acquis ont été vérifiés par exécution, souvent deux fois par deux personnes différentes.
Vous pouvez vous appuyer dessus.

### 2.1 La couche de vérité du Test 1 est irréprochable

- **1352 cellules sur 1352 concordent** avec le classeur officiel. Deux relecteurs ont écrit
  chacun leur script de parcours récursif de `refs/reference-data/test-1.ref.json` (A) contre
  `SIA_4010_geteilter_Link/Test1/Resultaterfassung_Test1.xlsx` : 1272 valeurs numériques
  identiques, 80 cellules `#DIV/0!` correctement propagées en `null` **avec note**, 0 cellule vide
  transformée en valeur, 0 divergence.
- **La chaîne de garantie tient** : sha256 recalculé du classeur =
  `7f7d2bc829ea0bb21ae7c98b4f01b6216150476e9eb9893d286829ffffac6c4c`, identique au champ
  `source.sha256` de `refs/reference-data/test-1.cells.json` (A) **et** présent dans
  `SIA_4010_geteilter_Link/official_manifest.json`. L'empreinte ne peut pas être un faux témoin.
- **L'empreinte n'est pas circulaire** : `scripts/build_cell_fingerprint.py:88-96` (A) lit le
  **classeur**, pas le JSON. Mesuré : sans classeur ni empreinte, 3 corruptions de données sur 4
  passent inaperçues ; avec l'empreinte seule, 4/4 sont détectées.
- **Le mapping libellé↔colonne est correct**, y compris les blocs décalés
  (1E = A..I, 600 = L..Q, 640 = T..Y, 900 = AB..AG, 940 = AJ..AO). Le bug historique n°1 est bien
  mort.

### 2.2 La formule du Streubereich est prouvée, pas supposée

Lue verbatim dans le classeur (`data_only=False`) :
`H16 = '=G16+MAX(ABS(C16-G16),ABS(D16-G16),ABS(E16-G16),ABS(F16-G16))'`,
`I16 = '=MAX(0,G16-MAX(...))'`. La nuance la plus fine du dossier est vraie aussi : le plancher à
zéro est une propriété **du Test 1 seulement** — `Resultaterfassung_Test2.xlsx` `O14 = '=M14-MAX(...)'`
et `Resultaterfassung Test4.xlsx` `V10 = '=T10-MAX(...)'` ne le portent pas.
`engine/scatter_band.py:27-29` (A) le documente et exige `floor_at_zero` explicite. Piège réel,
réellement évité.

### 2.3 Le moteur pur du dépôt A a un vrai pouvoir de détection

- **13 mutations tuées sur 15** (mesure par injection de bugs réalistes sur copies, reproduite
  par le contre-expert avec des chiffres identiques) : bande remplacée par min/max brut → 10 tests
  tombent ; écart max → moyenne des écarts → 11 ; plancher à zéro ignoré → 5 ; verdict forcé à
  conforme → 2 ; décembre oublié → 3 ; un programme de référence retiré → 4.
- **`engine/tests/test_scatter_band.py:228`** (A) est le seul test des deux dépôts qui confronte
  le code au classeur SIA **sans intermédiaire** : il localise les triplets par leurs *formules*,
  extrait les contributeurs de la formule `=AVERAGE(...)` elle-même (aucune colonne codée en dur)
  et reproduit **48 bandes officielles** à 1e-6 (28 pour le Test 1, 8 pour le Test 2, 12 pour le
  Test 5), Table 31 incluse.
- Séparation dur/pur tenue : `grep -rnE "^\s*(import|from)\s+iesve" --include=*.py engine/`
  → **aucun résultat** (vérifié pour cette note). Les 4 occurrences du mot sont des commentaires.

### 2.4 Le navigateur dans VE existe vraiment, et il est câblé de bout en bout

`Run_VE_SIA_Model_Builder_UI.py:44-57` (B) passe 9 callbacks à `launch_native_ui` : exécuteur,
évaluateur APS, sonde APS, lanceur ApacheSim, 4 qualificateurs Test 2A, sonde Test 3.
`swiss_sia/reference_model/sia4010/native_ui.py` fait 2 516 lignes de Tk.
L'environnement est confirmé : Python 3.12.3 dans VE 2025, avec tkinter, pywin32, reportlab,
openpyxl et le module `iesve` (309 symboles) — `ve_adapter/probe_runtime_resultat.txt` (A).

### 2.5 La chaîne client produit de vrais livrables

`reports/Swiss_Compliance_Report__ZOER_32_C1__-__20260731_012844.xlsx` (B) : 31 feuilles,
105 Ko, ouvert et parcouru. PDF 1 page. ZIP de preuves 136 Ko. La feuille `ENVELOPE U REVIEW`
compare 6 constructions réelles aux valeurs SIA 380/2:2022 tab. 3. Le volet SIA 380/2 rend de
vrais jugements (sous-scores : enveloppe 100, ouvertures 100, ventilation 60, CVC 80, dynamique
80, intégrité des valeurs 100).

### 2.6 Les garde-fous anti-sur-déclaration sont sérieux et présents dans le livrable

Feuille `CLIENT SUMMARY` du classeur, lignes 23-24, verbatim :
« Avoid | This model is fully SIA compliant. » et
« Avoid | The software/model is SIA 4010 validated. »
`navigator.py:1-3` (B) : « Fail-closed navigation… The navigator does not issue certification. »
`compliance_comparator.py:1` (B) : « Comparison engine that refuses to invent SIA 4010 tolerances. »
Le comparateur tue **4/4 mutations**, y compris « observation manquante traitée comme PASS »
(11 tests tombent). C'est la couche la mieux gardée des deux dépôts.

### 2.7 Le refus d'inventer est appliqué à l'exécution, pas seulement documenté

`ve_adapter/test1_adapter.py:368-375` (A) : `creer_materiau()` lève `ValueError` dès qu'une des
quatre propriétés est `None` — « création refusée plutôt que d'inventer une valeur ». Les cp de
toiture (l. 227-233) et les ρ/c d'isolant (l. 239, 270) restent `None`. L'infiltration sans valeur
explicite est refusée (l. 608-626). C'est exactement le comportement exigé par la règle n°1.

### 2.8 Trois points favorables que les revues initiales avaient manqués

- **Le blocage météo est levé et attesté.**
  `references/standards/bestest/DRYCOLD_IESVE_EPW_DERIVATION.json` (B) : status PASS, source
  DRYCOLD.TMY sha256 `C33778B4…`, EPW dérivé sha256 `C30E1EC…`, 8760 enregistrements,
  `dry_bulb_preserved` et `wind_speed_preserved` à 0,0 d'écart. Le sha256 des deux copies du
  fichier a été recalculé et concorde. L'artefact `sia4010_case600_mvp_audit.json` qui affiche
  encore `BLOCKED_WEATHER` a simplement deux jours de retard.
- **Les 15 symboles `VE*` cités dans `ve_adapter/test1_adapter.py` (A) existent tous** dans la
  surface d'API réellement mesurée dans VE (`ve_adapter/ve_api_surface.json`, 309 symboles).
  Zéro symbole inventé. La règle n°1 tient au niveau des classes (les signatures de méthodes
  n'ont pas été vérifiées une à une).
- **Les deux copies du paquet officiel SIA sont cohérentes.** Hachage fichier par fichier :
  57 fichiers dans (A), 114 dans (B), 57 communs, **zéro différence**. (A) est un sous-ensemble
  strict de (B). Il n'y a pas de risque de valider contre deux versions différentes des classeurs.

### 2.9 Les suites de tests existent et passent

- (B) : `pytest tests/ -q` → **532 passed, 11 skipped, 1158 subtests** (reproduit 4 fois, 92 à 163 s).
- (A) : `pytest -q` → **96 passed, 3 skipped** en 26 s (reproduit deux fois pour cette note).
- Le style d'assertion de (B) est sain : 893 `assertEqual`, 172 `assertTrue`, 55 `assertRaisesRegex`,
  contre seulement 7 `assertIsNotNone`. Aucun `assert True`.

---

## 3. Ce qui est fragile ou faux

Seuls figurent ici les points qui ont **survécu à la contre-expertise**. Les points requalifiés
ou réfutés sont regroupés au §3.4, pour que vous sachiez qu'ils ont été examinés.

### 3.1 Bloquants

#### B1 — Rien n'est versionné, et le dépôt A n'a aucun dépôt distant

*Vérifié pour cette note.* (A) : `git remote -v` → **sortie vide** ; `git ls-files` → **25 fichiers**,
dont `engine/.gitkeep`, `ui/.gitkeep`, `ve_adapter/.gitkeep`, `refs/reference-data/.gitkeep` — les
répertoires porteurs sont **vides côté git** ; le seul fichier de livrable suivi est
`traceability/test-1.spec.md` ; `git status --porcelain` → 49 entrées ; **il n'existe aucun
`.gitignore`**.
(B) : remote GitHub présent mais `git ls-files tests/` → **0**, `git ls-files swiss_sia/reference_model`
→ **0**, 16 modules suivis sur ~90, dernier commit `e231033` du **2026-07-06** (3,5 semaines de
retard), `git count-objects -vH` → pack de 3,86 Kio.

**Conséquence.** Les ~5 500 lignes du dépôt A (moteur, adaptateur, UI, 99 tests), les données de
référence auditées, les 7 specs de traçabilité et l'ADR n'existent que sur un disque, dans un
répertoire **non synchronisé** (vérifié : `MyDocuments` = `C:\Users\ulysse.couliou\Documents`,
OneDrive pointe ailleurs). Un `git clean -fd` — réflexe courant devant 49 fichiers non suivis —
une panne disque ou un vol de portable efface le projet. Côté B, les 32 428 lignes du cœur
SIA 4010 et les 532 tests ne sont sur aucun remote : un collègue qui clone obtient un produit
amputé de son cœur et de tous ses tests. Corollaire : aucun statut « FIGÉ », « SIGNÉ » ou
« CORRECTED_PASS_4 » n'a d'ancrage vérifiable, ce qui vide de sens les règles n°2 et n°5.

**Correctif.** Créer le remote privé de (A) ; écrire les deux `.gitignore` **avant** tout
`git add` ; committer par lots. Attention à trois pièges relevés :
`conftest.py` (A), non suivi, est **indispensable** à la forme d'invocation de la CI
(`pytest engine/tests/` échoue sans lui) ; le `.gitignore` de (B), qui fait pourtant 230 lignes,
**ne couvre aucun** des six répertoires lourds (`git check-ignore -v .codex_tmp .codex_spreadsheet
reports sia4010_evidence outputs SIA_4010_geteilter_Link` → rien) ; et le paquet
`SIA_4010_geteilter_Link` (118 Mo / 236 Mo) ne doit pas entrer dans l'historique.
**Effort : heures.**

#### B2 — Aucun cas SIA n'a jamais été simulé : 0/30 cas, 0/8 classes

Registre réexécuté (`case_registry.all_case_capabilities()`, B) : 30 cas exacts →
**1 `GUARDED_MUTATION_READY`** (Test 1 / cas 600), 5 `RUNTIME_QUALIFICATION_READY`,
**24 `NOT_IMPLEMENTED`**. Les 8 fichiers `sia4010_navigator_*.json` sont tous en
`MODEL_SETUP_REQUIRED` / `TECHNICAL_VALIDATION_INCOMPLETE`. Recherche exhaustive : 8 fichiers `.aps`
sous `Documents\switzerland`, tous des modèles clients, **aucun cas SIA**.

Nuance de la contre-expertise, à conserver : « rien n'a été construit » est trop absolu — 24
fichiers `.gbxml` existent dans `ZOER_32_C1\sia4010_artifacts\model_builder\geometry\` (les 7 cas
du Test 1, 2A-2D, 3A-3L). **Ce qui n'a jamais eu lieu, c'est l'import VE + ApacheSim + preuve à
checksum.** La gravité tient.

**Conséquence.** L'objectif « faire les tests de validation SIA 4010 n° 1 à 5 » n'est atteint pour
aucun test. Le produit ne peut aujourd'hui produire aucun résultat comparé à une valeur de
référence officielle, sur aucune classe.

**Correctif.** Arrêter d'élargir la couche de préparation et livrer **une** boucle fermée sur le
cas 600 : générer, importer, ApacheSim, extraire, comparer aux bandes officielles, archiver la
preuve. Prendre ce cycle comme définition du « done ». Point favorable : la météo DRYCOLD est
désormais attestée (§2.8) et l'UI est câblée — le cas 600 semble à **une exécution dans VE** de la
boucle fermée. **Effort : jours.**

#### B3 — Le cas 1E, seul cas portant un verdict, n'est modélisable par rien et son modèle d'entrée n'est spécifié nulle part

Fait établi et recontrôlé contre le PDF : `Spezifikation_Test1.pdf`, rubrique *Testkriterien*,
verbatim — « Die Resultate für die Fälle 600, 640, 900, 940, 600FF und 900FF werden zum Vergleich
mit den Referenzresultaten dargestellt. **Es gibt dafür kein Abweichungskriterium.** » puis
« **Resultate für den Test 1E müssen im Streubereich der enthaltenen Referenzprogramme liegen.** »
Le moteur en tire la bonne conclusion : `engine/test1_engine.py:384-392` (A) n'agrège le verdict
que sur 1E. Et le Test 1 est requis par 7 des 8 classes (`config.py:1028`, B, recoupé avec le
tableau 63 de `refs/SIA-4010-2023.pdf` p. 48).

Or : `ve_adapter/test1_adapter.py:661-665` (A) lève `NotImplementedError` pour `1E`, et le registre
(B) le donne `NOT_IMPLEMENTED`. **Surtout**, la spec ne comble pas le trou : d'après le PDF,
1E = « Diagnosefall 1D, jedoch mit Stoffmarkisen-Sonnenschutz gemäss Diagnosetest 2 E1 », et la
chaîne amont est Diag 1A = cas 600 sous climat Zürich-Kloten → 1B = 1A + fenêtre du Test 2 →
1C = 1B + infiltration du Test 2 → 1D = 1C + usage SIA 2024. **Aucune de ces cinq grandeurs n'est
décrite** dans `traceability/test-1.spec.md` §4 ni dans `traceability/iso-52016-1-ch7-valeurs.spec.md`,
qui ne décrivent que la cellule BESTEST de Denver.

**Conséquence.** « SPEC FIGÉE sur le modèle d'entrée » est faux exactement là où un verdict est
rendu. Le chemin pass/fail du moteur ne peut être alimenté par rien aujourd'hui, et il ne le
pourra pas tant que les spécifications amont (Test 2 : fenêtre et infiltration ; SIA 2024 : usage)
n'auront pas été écrites. C'est le vrai chemin critique du projet, plus lourd que tous les
correctifs de détail.

**Correctif.** Ne **pas** essayer de prioriser 1E avant 600 (c'est arithmétiquement impossible :
1E est strictement en aval). Séquencer : boucle fermée 600 → spec Test 2 (fenêtre, infiltration)
→ diagnostics 1A à 1D → 1E. **Effort : semaines.**

#### B4 — La couche qui produit les nombres n'a aucun test

`ve_adapter/test1_adapter.py` (A) : 1 137 lignes, **17 % de couverture** (310 instructions, 257 non
couvertes), **aucun répertoire `ve_adapter/tests`**. Trois mutations injectées, suite complète
relancée à chaque fois : (a) curseur d'agrégation figé, janvier répété 12 fois → **aucune
détection** ; (b) `moyenne_des_mensuelles` remplacée par la moyenne horaire → **aucune détection** ;
(c) garde-fou `len != 8760` désactivé → **aucune détection**.

Le cas (b) est précisément le biais que la docstring de la ligne 950 dit vouloir empêcher. Le
contre-expert l'a quantifié en exécutant les deux fonctions : sur une série rampe,
`moyenne_des_mensuelles = 4360,5` contre `moyenne_horaire = 4379,5`. Les deux moyennes diffèrent
bel et bien, et rien ne le vérifie.

**Conséquence.** Le moteur vérifie que le candidat tombe dans le Streubereich ; **rien ne vérifie
que le candidat lui-même est correctement calculé**. Un Test 1 entièrement vert avec des valeurs
fausses est possible. C'est l'un des deux seuls endroits mesurés où une erreur produit un résultat
**faux et vert** (l'autre est M1).

**Correctif.** Ces fonctions sont du Python pur (`calendar`, pas d'`iesve` — l'import d'`iesve` est
paresseux, l. 311). Créer `ve_adapter/tests/test_agregation.py` : série de 8760 valeurs à 1,0 →
chaque mois = 24 × nb_jours ; série = indice horaire → sommes mensuelles connues à la main ;
assertion explicite que `moyenne_des_mensuelles != moyenne_horaire` sur une série non uniforme ;
`ValueError` sur 8759 valeurs et sur une année bissextile. **Effort : heures.**

### 3.2 Majeurs

#### M1 — Le verdict client du classeur Excel n'est testé par aucun des 532 tests

`swiss_sia/excel_report.py:5425` `_dashboard_verdict` et `:5415` `_count_blocked_sia4010_tests` (B).
4 mutations, suite complète relancée à chaque fois avec comparaison des **ensembles** d'échecs :
**0 détection dans les 4 cas**. Mesure refaite indépendamment sur l'arbre propre, par plugin
pytest avec compteur d'interception prouvant que la mutation s'applique : `_dashboard_verdict`
forcé à la constante « READY FOR DETAILED REVIEW » → 3 interceptions effectives, et la suite rend
**532 passed / 11 skipped / 1158 subtests, strictement identique à la baseline**.
Aggravant : ce verdict n'est appelé que **3 fois dans toute la suite**, depuis un unique fichier
(`tests/test_excel_report_smoke.py`, 1 test) ; la branche BLOCKER de la ligne 5431 n'est jamais
exécutée. Les « 83 % de couverture » d'`excel_report.py` mesurent l'exécution, pas la vérification.

**Conséquence.** Le classeur peut afficher « READY FOR DETAILED REVIEW » à un client alors que des
alertes critiques subsistent ou que des tests SIA 4010 sont bloqués, sans qu'aucun test ne s'en
aperçoive. C'est la phrase que le client lit en premier.
**Correctif.** Tests unitaires directs : matrice (critical, high, blocked_tests, rooms_data) →
sous-chaîne attendue, plus un test que FAIL reste FAIL dans `official_status`. **Effort : heures.**

#### M2 — Le garde CI « pas d'import iesve » est faux dans les deux sens, et il bloquera le correctif B1

*Vérifié pour cette note.* `.github/workflows/engine-tests.yml` (A) exécute
`if grep -rl "import iesve" engine/; then exit 1; fi`. Le grep remonte **10 chemins** :
`engine/requirements.txt`, `engine/scatter_band.py`, `engine/test1_engine.py`,
`engine/tests/test_ref_integrity.py`, `engine/tests/test_test1_engine.py` et 5 `.pyc` — tous des
commentaires qui affirment respecter la règle. Faux négatif confirmé aussi :
`echo "from iesve import foo" | grep -c "import iesve"` → 0.

Arbitrage entre deux relecteurs qui se contredisent : **la CI n'est pas rouge aujourd'hui à cause
de ce grep** (sur le checkout réel, `engine/` ne contient qu'un `.gitkeep`, le grep ne trouve rien),
elle est rouge à cause de `pytest engine/tests/` qui sort en code 5. **Mais** elle deviendra rouge
à cause du grep **à la seconde où l'on committe `engine/`**, c'est-à-dire au moment exact où l'on
applique le correctif B1. Et de toute façon, sans remote, ce workflow **n'a jamais tourné une
seule fois**.

**Correctif.** Corriger le garde **dans le même commit** que B1 : remplacer le grep par un test
pytest dans `engine/tests/` qui parcourt les `.py` avec `ast` et échoue sur tout `Import`/`ImportFrom`
dont le module racine est `iesve` — vérifiable en local comme en CI, insensible à la forme
d'écriture. Aligner au passage la CI sur Python 3.12 (le runtime réel de VE est 3.12.3 ; la CI est
sur 3.11, la machine de dev sur 3.13). **Effort : minutes.**

#### M3 — La source ISO 52016-1:2017 n'est nulle part dans le dépôt

`traceability/iso-52016-1-ch7-valeurs.spec.md:6-7` (A) revendique une lecture « sur l'exemplaire
consulté par le commanditaire (accès institutionnel BSI), pages 122 à 134 ». Recherche :
`find . -iname '*52016*'` → un seul résultat, la spec elle-même ; aucune capture d'écran.
`traceability/batiment-exemple-zonage.spec.md:39` liste toujours cette norme comme absente de `/refs`.

**Conséquence.** Contrevient directement à la règle n°1 (« non vérifié dans /refs = non écrit »).
Toutes les valeurs du modèle d'entrée du Test 1 reposent sur une transcription qu'aucun tiers ne
peut recontrôler. L'auto-cohérence arithmétique — vérifiée et bonne (κ = ρ·c·D juste sur 10 couches
sur 10, 1/2,984 = 0,335121, décomposition du noyau exacte) — **ne détecte pas une lecture
systématiquement décalée d'une colonne**, ce qui est exactement le défaut n°1 déjà survenu sur la
Table 30.

**Atténuation trouvée par la contre-expertise, importante.** Le PDF `ASHRAE 140_2023_D_86892.pdf`
**est** à la racine du dépôt A, et sa **Table 7-2** (p. ~40) donne **exactement les mêmes valeurs
matériaux**, cp de toiture inclus (Plasterboard 0,16/0,012/950/840 ; Fiberglass quilt 0,04/0,066/12/840 ;
Wood siding 0,14/0,009/530/900 ; Timber flooring 0,14/0,025/650/1200 ; dalle 1,13/0,080/1400/1000).
Il existe donc une **source corroborante déposée** pour les matériaux — pas pour tout le reste.

**Correctif.** Deux options, à arbitrer par vous : déposer les captures des pages 122-134 dans
`/refs` (même sous manifeste de hachages si le droit d'auteur l'interdit), **ou** acter par écrit
qu'ASHRAE 140:2023 Table 7-2 sert de source corroborante pour les matériaux et documenter ce qui
reste non corroboré. **Effort : heures (vous), minutes (dev).**

#### M4 — Une spec déclarée « FIGÉE » prescrit au moteur la formule pass/fail fausse

`traceability/test-1.spec.md:330-331` (A) : « Implémenter le seul test binaire sur le cas 1E :
« valeur ∈ [min, max] des programmes de référence » … `[REQUIS — Excel d'éval absent]` ». Répété
l. 376. Or la vraie formule est `moyenne ± max|programme − moyenne|`, plancher à 0 (§2.2), et le
classeur n'est pas absent.

Contrôle chiffré : Table 28, cas 1E, mois 1 → programmes = [543,386 ; 588,871 ; 481,162 ; 508,898],
donc min/max = **[481,162 ; 588,871]** alors que la vraie bande est **[472,287 ; 588,871]**. La
formule prescrite est **plus stricte** que la norme : quiconque « aligne le code sur la spec figée »
fabrique des échecs faux — l'erreur la plus coûteuse pour ce produit.

**Arbitrage entre les deux relecteurs.** L'un classe le point majeur, l'autre exagéré. Je tranche
**majeur, mais différé** : le document se contredit lui-même (§8 périmé vs §10 qui donne la bonne
réponse), l'en-tête borne le figeage « **sur le modèle d'entrée** », aucun code ne lit ce document,
et le moteur est protégé par un test anti-régression nommément dirigé contre cette formule
(`engine/tests/test_test1_engine.py:97 test_plage_dispersion_nest_pas_le_min_max_brut`). Le risque
n'est pas actif aujourd'hui ; il se déclenche à la première réécriture, ou pour les tests 2 à 5.
**Correctif : minutes** (réécrire §6 et §8, citer H16/I16, retirer « Excel absent »).

#### M5 — La signature qa-auditor porte sur la passe 3 ; le fichier livré est en passe 4

`refs/reference-data/test-1.ref.json` (A) : `status = "CORRECTED_PASS_4"`,
`tables_extracted = [28,29,30,31,32]`, 1352 feuilles, `corrections[3]` datée 2026-07-31 (ajout de
la Table 31). `AUDIT.md` ne contient **aucune** section passe 4, chiffre « 1336/1336 » (l. 135, 212,
217) et affirme encore **l. 102** : « Table 31 (charges de pointe horaires) : présente dans l'Excel,
**non extraite** ; hors périmètre déclaré » — l'inverse de la réalité. Le compte périmé est même
recopié dans le code (`engine/test1_engine.py:105-107`).

Ces 16 nœuds portent le **troisième critère pass/fail** du cas 1E et sont déjà consommés par
`_perioder_pointe` (l. 334-346).

**Atténuation.** La contre-expertise établit qu'ils **ont** été vérifiés, même si la signature ne
les couvre pas : `test_fidelite_valeur_cellule` itère les 1352 feuilles sans filtre, et
`test_correspondance_libelle_colonne` inclut `annual_hourly_peak_load_kwh`. Les deux relecteurs ont
recalculé la bande à la main (H82 = 1,8437843983 ; I82 = 1,6611267049) et elle est juste.
**Ce qui manque est la signature et la correction de la ligne 102, pas la vérification.**
**Effort : minutes à heures.**

#### M6 — La matrice de traçabilité clause→code→test n'existe pas

`CLAUDE.md` décrit `/traceability/` comme « matrice clause→code→test, par test SIA », et la règle
n°5 exige une signature qa-auditor **sur cette matrice**. Le répertoire contient **7 notes
d'analyse normative et zéro matrice**. `AUDIT.md:234-236` le reconnaît et diffère : « celle-ci sera
signée quand le moteur et ses tests existeront » — or le moteur et ses 96 tests existent depuis.

**Conséquence.** La règle n°5 est structurellement insatisfaisable pour le Test 1 : **l'objet à
signer n'existe pas**. Aucun test ne peut donc être déclaré « done » au sens du projet.
**Correctif.** Créer `traceability/matrice-test-1.md` à trois colonnes, l'alimenter depuis les
citations déjà présentes dans `engine/*.py`, la faire signer. **Effort : heures.**

#### M7 — Le classeur livré ne vérifie pas la conformité SIA 4010

Feuille `COMPLIANCE RESULTS` : « SIA 4010 / Overall score | **0** », test_1 à test_7 tous
`NOT_CHECKABLE`. Feuille `SIA REQUIREMENTS` : « Requirements listed 13 | Automated PASS/CHECK **1** ».
PDF client : « ASSESSED RESULT / **NOT DETERMINED** ».

**Requalification par la contre-expertise, à retenir.** Le constat est vrai pour SIA 4010 et faux
en général : la même feuille donne 6 sous-scores non nuls pour le volet SIA 380/2 (§2.5), et sur
13 lignes de `SIA REQUIREMENTS`, 11 sont `REFERENCE_DIAGNOSTIC`, 1 `REFERENCE_DEVIATION`,
1 `PARTIAL_CHECK`. Le classeur **juge** l'enveloppe SIA 380/2 ; il ne juge **rien** en SIA 4010.
**Correctif.** Séparer explicitement dans le classeur ce qui est *vérifié* (comparé à une valeur de
référence citée) de ce qui est seulement *relevé*, et afficher le compte en tête de rapport
(« n contrôles vérifiés / m relevés »). **Effort : heures.**

#### M8 — Le travail SIA 4010 se fait dans le projet client, et il a détruit la seule démo qui marchait

Rapport du 31/07, feuille `DYNAMIC RESULTS` : Status=`NOT_CHECKABLE`, « Selected APS file: None »,
« Project weather file: DRYCOLD_IESVE.epw », « Skipped stale APS files: 2 ». Rapport du 23/07 :
Status=`AVAILABLE` mais sous météo `BirminghamEWY.fwt`, avec seulement le refroidissement renseigné.
24 `.gbxml` et 154 `.json` de cas SIA 4010 sont écrits dans `ZOER_32_C1\sia4010_artifacts`, et la
météo du **projet client** a été passée à DRYCOLD.

**Requalification importante.** Le correctif naïf (« bloquer si le climat n'est pas suisse ») est
**faux** : DRYCOLD est le climat **normatif** du Test 1 (`Spezifikation_Test1.pdf` : Denver, CO /
DRYCOLD.TMY BESTEST). Le vrai problème n'est pas le climat, c'est le **mélange des deux parcours
dans un même projet VE**.
**Correctif.** Séparer physiquement le projet VE de mise au point SIA 4010 du projet client. Le
contrôle de climat suisse ne doit s'appliquer qu'au parcours client. **Effort : heures.**

#### M9 — Le `source_locator` du dépôt B désigne systématiquement la mauvaise cellule

*Vérifié pour cette note* : `swiss_sia/reference_model/sia4010/workbook_loaders.py:262-264` (B)
construit `source_locator="{}!{}{}".format(prefix, get_column_letter(upper_col), row)` alors que
`expected_value` vient de la colonne **mean**. Exemple réel : `expected_value=530,5790800883958`
avec `source_locator='…Zusammenfassung Testfälle!H16'`, or H16 = 588,87 et c'est **G16** qui vaut
530,579. Motif répété aux lignes 264, 356, 438, 689 — **4 parseurs, donc les 84 records des
tests 1 à 7**. Le docstring l. 31-32 affirme l'inverse.

**Requalification.** Un relecteur y voit une violation de la règle n°3 au cœur du dispositif de
preuve ; le contre-expert objecte que H16 n'est pas une cellule quelconque mais celle qui porte
`upper_bound`, champ présent dans le même enregistrement. **Je tranche : défaut réel, gravité
moyenne** — c'est un locator *imprécis*, pas un pointeur aléatoire, et les valeurs elles-mêmes sont
justes (28/28 concordantes). Mais c'est le champ qui sert à défendre le résultat devant la
sous-commission, et un auditeur qui ouvre H16 n'y trouve pas le nombre cité.
**Correctif.** Émettre trois locators (`mean_locator`, `upper_locator`, `lower_locator`), corriger le
docstring, ajouter un test qui relit la cellule citée. **Effort : heures.**

#### M10 — Aucune valeur « figée » d'ISO 52016-1 n'est propagée dans le code ou la configuration

`grep -rn '2\.984|0\.41|1\.453|4\.167' --include=*.py --include=*.json .` → **zéro occurrence**.
Concrètement : le modèle qui tourne pose encore l'infiltration à **0,5 h⁻¹**
(`C:\Users\ulysse.couliou\Documents\switzerland\test\sia4010_case_manifest.json`,
`"air_changes_per_hour": 0.5`, avec un `source_locator` qui dit lui-même « ISO 52016-1:2017
Chapter 7 identity **remains to be confirmed** »), contre 0,41 h⁻¹ dans la spec figée.

**Requalification à ne pas rater.** « L'écart est de +22 %, il faut propager 0,41 » est trop rapide.
La contre-expertise a lu `ASHRAE 140:2023 §7.2.1.6` et sa Table 7-4 : la valeur à saisir **dépend du
comportement du logiciel** — programmes qui corrigent l'altitude automatiquement → saisir 0,5 ;
programmes qui ne le font pas → saisir 0,414 (facteur 0,829, altitude 1650 m). **Si ApacheSim
corrige déjà l'altitude et qu'on lui donne 0,41, la correction est appliquée deux fois et
l'infiltration est sous-estimée d'environ 18 %** — biais direct sur les besoins de chauffage,
c'est-à-dire sur la grandeur même sous test. Au passage, c'est le seul endroit où une divergence
numérique réelle ISO(2017) / ASHRAE(2023) a été constatée : 0,41 / 0,822 / 1609 m contre
0,414 / 0,829 / 1650 m. La spec « figée » ne mentionne aucune conditionnalité.
**Correctif.** Ne pas propager mécaniquement. Trancher d'abord, par sonde dans VE, si ApacheSim
applique la correction d'altitude, puis écrire la valeur **et** sa justification. **Effort : heures.**

#### M11 — Deux dépôts réimplémentent le même Test 1 sans passerelle ni test croisé

(A) : `refs/reference-data/test-1.ref.json`, `engine/test1_engine.py`, `ve_adapter/test1_adapter.py`
(1 137 lignes, avec son propre `generer_cas_test1()` couvrant 6 cas), `ui/*` = 5 472 lignes.
(B) : `workbook_loaders.py` + `expected_results.py` + `compliance_comparator.py` +
`frequency_distribution.py`, 53 589 lignes dans `swiss_sia`. Les deux lisent le même onglet du même
classeur, avec des conventions différentes (A stocke les valeurs brutes par programme et recalcule
la bande ; B lit directement Mittelwert/obere/untere Grenze).

**Atténuation mesurée.** La divergence actuelle est **nulle** : deux relecteurs ont importé les deux
dépôts dans le même interpréteur et comparé `build_band` (A) à `build_scatter_band` (B) →
identiques à 1e-9 sur trois jeux de valeurs et **au bit près sur les vraies valeurs annuelles du
cas 1E** (2228,3564999999994 / 2995,373). L'absence de plancher à zéro côté B est un arbitrage
**motivé et documenté** (`frequency_distribution.py:270-273`), pas un oubli. Le risque est donc
**différé** : le jour où l'arbitrage du Streubereich évolue (la spec l'annonce réversible, confiance
~92 %), il faudra corriger deux bases indépendantes, et si une seule l'est, deux exécutions du même
test rendront deux verdicts différents sans signal.

Aggravant relevé : `frequency_distribution.py:53-55` (B) délègue sa justification normative à
`traceability/streubereich-distributions.spec.md` **du dépôt A** — un fichier non suivi par git,
sur aucun remote. Le seul lien de traçabilité inter-dépôts pointe vers un document introuvable.
**Correctif.** Décider laquelle est la source de vérité (décision commanditaire), puis ajouter un
test de non-régression croisé — il tient en quinze lignes. **Effort : heures.**

#### M12 — L'export vers le classeur officiel est impossible, et le mode visé n'est probablement pas le bon

`ui/export_excel_com.py:31-37` (A) refuse explicitement de deviner les adresses de la zone
`Handeingabe` faute d'un descripteur `refs/reference-data/testN.map.json` — vérifié : aucun fichier
`*.map.json` n'existe. Le refus est le bon comportement, mais la fonctionnalité est absente.

**Deux requalifications qui changent le correctif.**
1. La carte n'est **pas** un travail de recherche : elle est écrite dans les formules du classeur.
   `Zusammenfassung Testfälle!B16 = '=IF(Daten_Testprogramm!$H$3="Handeingabe",Daten_Testprogramm!N28,
   Daten_Testprogramm!F28)'`, et `Daten_Testprogramm` ligne 27 donne l'entête `Case id. | 600 | 640 |
   900 | 940 | 1E` en colonnes J:N. Parcourir la colonne B produit la carte mécaniquement (~1 h).
2. **Mais le mode visé est probablement le mauvais.** `Daten_Testprogramm!H3` vaut aujourd'hui
   `'Berechnet durch Stundentabelle'`, pas `'Handeingabe'`, et `Spezifikation_Test1.pdf` exige
   « Jahresdatensätze, zu übertragen in die Auswertungsdatei » et « Die Auswertung erfolgt
   automatisch aus den Jahresdatensätzen ». **Le livrable normatif est le jeu de 8760 heures**, pas
   les agrégats mensuels de `Handeingabe`. Construire une carte mensuelle J:N vise le mode de repli.

Par ailleurs, ce point est en aval de B2 : il n'y a rien à écrire tant qu'aucun cas n'est simulé.
**Correctif.** Trancher d'abord 8760 h vs Handeingabe (décision), puis établir la carte
correspondante. **Effort : heures, après décision.**

### 3.3 Mineurs (regroupés)

| # | Point | Preuve | Effort |
|---|---|---|---|
| m1 | L'export Excel COM n'est exécuté par personne | Les 3 seuls tests skippés de (A) sont `ui/tests/test_export_excel_com.py:143/:149/:187` (« Excel indisponible via COM ») ; couverture 20 % | heures |
| m2 | Suite (A) instable ~20 % | *Vérifié pour cette note* : `Windows fatal exception: code 0x80010108` (RPC_E_DISCONNECTED) imprimé à `test_export_excel_com.py:103`, **à l'import du module pendant la collecte**, parce que le `pytestmark` de niveau module lance Excel en COM. Une occurrence a produit « Interrupted: 5 errors during collection », c'est-à-dire que **les 60 tests du moteur n'ont pas tourné du tout** | heures |
| m3 | Le meilleur test ne pourra jamais tourner en CI | `test_reproduces_the_tabulated_bands` a besoin de `SIA_4010_geteilter_Link` (118 Mo). Sans classeur il skip proprement → la seule confrontation directe au classeur SIA reste locale **par construction**. À arbitrer (Git LFS ? job manuel ? empreinte étendue ?) | heures |
| m4 | Le même test a un garde-fou faible | Ses seules bornes sont `assert triplets` et `assert reproduced > 0`, avec 3 `continue` d'échappement. Une régression faisant tomber la localisation de 48 à 1 bande passerait en vert. Un plancher par classeur (≥ 28 / 8 / 12) coûte 3 lignes | minutes |
| m5 | `WORKBOOKS` ne couvre que les Tests 1, 2 et 5 | `engine/tests/test_scatter_band.py:51-56` (A). Les Tests 3, 4, 6, 7 sont sur disque et non couverts. Ajouter Test 4 verrouillerait la propriété « pas de plancher à zéro » et sécuriserait l'arbitrage de `critere-test4.spec.md` | minutes |
| m6 | Retirer `test-1.cells.json` rend la suite **verte**, pas rouge | Mesuré : 53 passed / 7 skipped, corruption non détectée. Le filet de sécurité disparaît **en silence**. Ajouter un test qui échoue (et non skip) si l'empreinte est absente | minutes |
| m7 | Le générateur du JSON de référence n'est pas versionné | `update_json.py`, `generate_corrected_ref.py`, `inspect_extremes.py`, `inspect_zone3.py` sont à la racine de (A), non suivis, avec 7 chemins absolus `C:\Users\ulysse.couliou\…`. Le JSON audité existe sans son générateur | heures |
| m8 | Intermédiaires non audités dans un répertoire déclaré « figé, lecture seule » | `refs/reference-data/table_30_corrected.json` et `table_32_corrected.json` (A). Pire : `traceability/temperature-operative.spec.md:211` et `:380` citent `table_32_corrected.json` comme **source de preuve** d'un arbitrage, au lieu du JSON audité | minutes |
| m9 | Contrainte « Python 3.4 » appliquée alors qu'`ADR-001:64` l'annule | 4 fichiers : `engine/test1_engine.py:4-5`, `engine/tests/test_test1_engine.py:11`, `ui/verdict_view.py:11`, et `ve_adapter/test1_adapter.py:10-15` qui affirme que l'ADR « n'a PAS tranché » — faux depuis `ADR-001:46` (3.12.3 mesuré dans VE) | minutes |
| m10 | Tolérance non citée dans le chemin pass/fail | `engine/test1_engine.py:92 TOLERANCE_DEFAUT = 1e-6`, utilisée l. 245 pour **élargir** la bande d'acceptation. Effet physique négligeable, mais c'est une tolérance absolue non sourcée sur le seul verdict du Test 1. `scatter_band.contains()` a déjà le bon défaut (0.0) | minutes |
| m11 | Signe du delta non vérifié | Mutation `delta = valeur - reference` inversée : aucune détection. Or pour les 6 cas sans critère, ce delta **est** la seule sortie utile affichée au client | minutes |
| m12 | 11 marqueurs `[REQUIS]` périmés dans une spec « FIGÉE » | `traceability/test-1.spec.md` l. 212, 250, 261, 265, 272, 331, 369, 372, 374, 376, 425. Le §8 « Zones d'incertitude à lever avant done » liste 4 faux bloquants ; les l. 331/376 disent « Excel absent » et les l. 408/425 « ISO 52016-1 absente, non vérifiable » — contredits par l'en-tête du même fichier | minutes |
| m13 | Trois autres documents périmés | `ADR-001:176` prescrit encore `ApacheSim.save_options` alors que l. 122-124 du même fichier disent qu'il n'existe plus ; `test-1.ref.md:20` annonce 4 cas pour la Table 32 au lieu de 2, `:205/:211` localise le bloc ASHRAE en « AZ-BG » (réel : **AY106:BM120**), `:219-223` donne un chemin JSON faux et `:236` une clé fausse ; `test_ref_integrity.py:19-25` décrit l'angle mort CI comme non corrigé alors que les l. 70-76 du même fichier utilisent déjà le correctif | minutes |
| m14 | Erreur arithmétique dans une spec figée | `iso-52016-1-ch7-valeurs.spec.md:177` : « 200 W en continu → q_int = 1,453 W/m² ». Le plancher fait 48,0 m² : 200/48 = **4,167**. Aucune aire du §2 ne donne 1,453. Latent (aucun code ne le consomme) mais c'est le type de nombre qu'on recopie dans un thermal template | minutes |
| m15 | `build_band` n'a pas de garde « ≥ 2 programmes » | `build_band([42.0])` → bande dégénérée `[42,42]`, `verdict(41.9, [42.0])` → FAIL. Inatteignable sur les données figées (216 séries, toutes à 4 programmes) et (B) est dégénéré au même niveau | minutes |
| m16 | Un mécanisme de sécurité implémenté n'est câblé nulle part | `engine/scatter_band.py:119-142` expose un verdict à trois états (PASS / PASS_WITH_RESERVATION / FAIL) conçu comme parade au risque de faux échec des tests 2 à 5. Aucun appelant : `engine/test1_engine.py` n'importe que `build_band` | heures |
| m17 | Test 4 : périmètre des grandeurs non arrêté | `critere-test4.spec.md:359` (statut de l'annexe A non vérifié), `:390` (libellé BM21 tronqué), `:512` (version allemande non consultée). L'adaptateur ne peut pas être écrit : on ne sait pas quoi extraire | heures |
| m18 | Critère de distribution absent pour les tests 4, 6, 7 | `DISTRIBUTION_CRITERIA` (B) → clés `['2','3','5']` seulement. Pour le **Test 1 l'absence est correcte** (le PDF ne prévoit aucun critère de distribution) ; la question reste ouverte pour 4, 6 et 7 | jours |
| m19 | 42 scripts `Run_VE_*.py` en façade | L'objectif « un point d'entrée avec deux parcours » n'est pas tenu. **Attention au correctif naïf** : 10 des 42 sont importés comme bibliothèques (`Run_VE_SIA_Model_Builder_UI.py:26-34` en importe 9 à lui seul) — les déplacer casse le navigateur tant que les imports ne sont pas réécrits en modules du paquet | heures |
| m20 | Un seul des 42 scripts est nommé par un test | Une erreur d'import ou un chemin cassé ne se voit qu'au clic de l'utilisateur dans VE. Un test de compilation collectif avec stub `iesve` coûte une heure | heures |
| m21 | Style : `engine/scatter_band.py` et `engine/tests/test_scatter_band.py` sont en anglais | `CLAUDE.md` impose « Commentaires de code en français ». Les 8 autres modules le respectent | minutes |
| m22 | Fichiers lourds mêlés aux sources | (A) : PDF ASHRAE 26 Mo à la racine au lieu de `refs/`, 7 `__pycache__`, sorties de sonde dans `ve_adapter/`. (B) : `.codex_tmp` 271 Mo, `.codex_spreadsheet` 13 Mo, total 1,2 Go, **aucun** couvert par le `.gitignore` existant | heures |

### 3.4 Points examinés puis requalifiés ou réfutés

Ces points ont été soulevés par un relecteur et **écartés** par la contre-expertise. Ils sont
listés pour que vous sachiez qu'ils ont été instruits, et pour éviter qu'on les ressorte.

**Réfutés (le constat est faux) :**

1. **« 1E est le seul cas du Test 1 sans générateur, il faut le prioriser avant 600/640/900/940 »**
   → Faux dans les deux moitiés. **600 est le seul cas AVEC un générateur** ; 6 cas sur 7 n'en ont
   pas. Et 1E est **strictement en aval** de 600 et de trois spécifications du Test 2 : le prioriser
   est arithmétiquement impossible. Ce qui survit du point : 1E est bien le seul cas à critère
   (voir B3).
2. **« La formule du Streubereich de la Table 31 n'est asservie par aucun test »**
   → Faux. `test_reproduces_the_tabulated_bands` balaie la feuille jusqu'à 400 lignes et découvre
   les triplets `G82/H82/I82` et `G83/H83/I83`, plancher à zéro compris. Le correctif proposé
   (ajouter la grandeur aux boucles de `test_ref_integrity`) lèverait en plus un `KeyError`, la
   structure du nœud étant `peak.{heating,cooling}` et non `monthly`.
3. **« Les deux copies du paquet officiel SIA peuvent porter des versions différentes »**
   → Faux. Hachage sha256 fichier par fichier : 57 fichiers communs, **zéro différence**.
4. **« `engine/requirements.txt` sur-déclare openpyxl »**
   → Faux. Le fichier s'intitule « DEVELOPMENT / CI dependencies » et explicite que les **tests**
   relisent les classeurs. Le retirer ferait perdre silencieusement trois tests.
5. **« Le PDF client est dans le même angle mort de test que l'Excel »**
   → Faux. Mutation de `compliance_report_pdf.py::_status_label` en constante « PASS » → 1 test
   tombe. Faible, mais non nul, contrairement au classeur.
6. **« La CI est bloquée aujourd'hui par le garde iesve »**
   → Faux aujourd'hui (sur le checkout, `engine/` est vide, le grep ne trouve rien), vrai demain
   (au premier commit d'`engine/`). Voir M2, qui intègre l'arbitrage.
7. **« Le point normatif du Streubereich est encore bloquant »**
   → Levé. Le mot `Streubereich` figure verbatim p. 2 de `Spezifikation_Test1.pdf`. L'« action
   bloquante avant figeage » de `streubereich-distributions.spec.md:396` est close.
8. **« La liste `CLASSES_REQUERANT_TEST1` reste non recontrôlée »**
   → Levé. Vérifiée contre `refs/SIA-4010-2023.pdf` p. 48, tableau 63 : le tuple
   `('1A','1B','2A','2B','3','4A','4B')` de `engine/test1_engine.py:90` est **correct**, commentaire
   compris (seule la classe 5 n'exige pas le Test 1).
9. **« Les deux documents d'audit se contredisent sur le critère de distribution »**
   → Non. `AUDIT-swiss-sia-existant.md:154` et `streubereich-distributions.spec.md:344-345`
   concordent : bande moyenne ± écart_max pour le verdict, enveloppe min..max affichée en surcouche
   sans verdict.

**Requalifiés (le constat est vrai, la gravité ou le correctif ne l'est pas) :**

10. **Mutation `#DIV/0!` → `0.0` non détectée** : de *majeur* à **mineur**. C'est un mutant
    **équivalent** : les 80 valeurs nulles portent **toutes** sur `testprogramm_candidate`, champ
    exclu du calcul (`test1_engine.py:270`). Aucun `#DIV/0!` ne peut entrer dans une moyenne
    aujourd'hui. Le risque résiduel est la perte d'un garde-fou si les données changent.
11. **`source_locator` décalé** : de *majeur* à **moyen** (voir M9).
12. **Scripts jetables produisant la référence** : de *majeur* à **mineur** (m7). La chaîne
    d'**audit** est propre et reproductible (`scripts/build_cell_fingerprint.py` + sha256 chaîné au
    manifeste officiel) ; seule la chaîne de **génération** du `.ref.json` est sale.
13. **`build_band` sans garde n ≥ 2** : de *majeur* à **mineur** (m15).
14. **« L'Excel ne vérifie rien »** : requalifié — le volet SIA 380/2 juge réellement (M7).
15. **« Ajouter un contrôle bloquant climat suisse »** : correctif **dangereux** — DRYCOLD est le
    climat normatif du Test 1 (M8).
16. **« Remplacer les coefficients ASHRAE Table 7-7 par le tableau 25 d'ISO (h_ce = 20) »** :
    correctif **techniquement faux**. `ASHRAE §7.2.1.9.3(a)` dit qu'un programme calculant convection
    extérieure **et** échange IR variables au pas de temps « shall apply those calculations; skip the
    remaining instructions » — pour IESVE la bonne réponse est probablement **aucun coefficient
    forcé**. Substituer h_ce = 20 mélangerait précisément les deux conventions qu'on veut séparer.
    Le vrai défaut est la contradiction interne de `test-1.spec.md` (l. 12-17 retire ASHRAE 2023,
    §8 pt 1 et pt 6 le prescrivent toujours), et le risque est nul en l'état (`appliquer=False`,
    fonction jamais appelée).
17. **« Reporter les cp de toiture débloque le Test 1 en VE »** : faux. `creer_materiau()` lève sur
    **toute** propriété `None`, et les ρ/c de l'isolant de plancher restent `None` sans qu'aucune
    source ne fournisse de nombre (ISO dit « 0 », ASHRAE dit « le minimum que le programme
    autorise ») — c'est une décision à prendre côté VE.
18. **« Le Test 4 est le seul point normatif qui bloque une classe »** : inversé. Le Test 4 est le
    seul test inachevé qui dispose déjà d'une spec de 529 lignes ; **aucune spec n'existe pour les
    tests 2, 3 et 5**.
19. **« Le critère de distribution manque pour 4 tests sur 7 »** : pour le **Test 1**, l'absence est
    correcte et documentée par le PDF. Reste ouvert pour 4, 6, 7 (m18).
20. **« La couche de référence donne 84 métriques annuelles »** : ce ne sont pas des métriques
    annuelles. Pour le Test 1, les 28 records sont 12 mensuels + 1 annuel pour le chauffage, idem
    pour le refroidissement, + 2 pics — et tous portent `case_id='1E'`, aucun autre cas.

**Contradiction tranchée par mesure :** les relecteurs annonçaient 96 et 95 tests passants pour (A).
J'ai relancé deux fois : **96 passed / 3 skipped** les deux fois — mais avec le
`Windows fatal exception: code 0x80010108` imprimé à la collecte. Les deux relecteurs ont donc
raison à des moments différents : **la suite est instable, pas déterministe** (m2).

---

## 4. Ce qui reste à faire

### 4.1 Ce qui dépend de vous (décisions, achats, exécutions dans VE)

| # | Action | Pourquoi c'est vous | Effort |
|---|---|---|---|
| C1 | **Créer le dépôt distant privé de (A)** | Seul vous pouvez créer le repo sous votre compte | minutes |
| C2 | **Exécuter la boucle 600 dans IESVE** : importer le modèle généré, lancer ApacheSim, produire l'`.aps` | Aucun agent n'a accès à VE. C'est le verrou de tout le reste | heures |
| C3 | **Décider quel dépôt est la source de vérité** (A = moteur pur audité ; B = produit qui tourne) et si on fusionne | Décision d'architecture et de propriété du code | décision |
| C4 | **Déposer ISO 52016-1:2017 (p. 122-134) dans `/refs`**, ou acter par écrit qu'ASHRAE 140:2023 Table 7-2 sert de source corroborante pour les matériaux | Accès institutionnel BSI + arbitrage droit d'auteur | heures |
| C5 | **Trancher : jeu de 8760 h ou agrégats `Handeingabe`** pour le rendu au SIA | Détermine tout le format de sortie, et donc M12 | décision |
| C6 | **Séparer le projet VE de mise au point SIA du projet client ZOER_32_C1** | Manipulation de vos projets VE | heures |
| C7 | **Statuer le caractère normatif de l'annexe A de SIA 4010:2023** (version allemande) et relire la ligne 21 du classeur Test 4 au-delà de BM | Achat/consultation de la version allemande | heures |
| C8 | **Trancher : ApacheSim applique-t-il la correction d'altitude sur l'infiltration ?** (0,5 vs 0,41 h⁻¹) | Sonde à exécuter dans VE | heures |
| C9 | **Vérifier ce que la sous-commission SIA exige comme dossier d'attestation** | Personne n'a vérifié que les 5 « familles de preuves » codées correspondent à la demande réelle | jours |

### 4.2 Ce qui dépend du développement, dans l'ordre

| Lot | Contenu | Dépend de | Effort |
|---|---|---|---|
| **L0** | **Mise en sécurité.** Écrire les deux `.gitignore` ; corriger le garde `iesve` en test AST (M2) **dans le même commit** ; committer (A) par lots atomiques — `refs/reference-data/*.json`, `engine/` + `engine/tests/` + **`conftest.py`**, `traceability/` + `docs/`, `AUDIT*.md`, `ve_adapter/` + `ui/` + `scripts/` ; committer (B) — `swiss_sia/reference_model/` et `tests/` ; aligner la CI sur Python 3.12 ; ajouter `pytest ui/tests/` au workflow | C1 | **1 jour** |
| **L1** | **Boucle fermée cas 600.** Générer, importer, ApacheSim, extraire, comparer aux bandes officielles, archiver la preuve à checksum. Définition du « done » | C2, L0 | **3 à 5 jours** |
| **L2** | **Tester `ve_adapter`** (B4) : agrégation mensuelle, 8760 h, bissextile, `_resoudre_liaison`, `decouvrir_candidats_variable`, `_verifier_fermeture_geometrie`. Python pur, testable hors VE | — | **2 jours** |
| **L3** | **Tester `_dashboard_verdict` et `official_status`** côté B (M1) | — | **1 jour** |
| **L4** | **Hygiène documentaire** : réécrire `test-1.spec.md` §6 et §8 (M4, m12) ; signer la passe 4 et corriger `AUDIT.md:102` (M5) ; corriger `ADR-001:176`, `test-1.ref.md` l. 20/205/219/236, les 4 mentions « Python 3.4 », le `q_int` (m13, m14, m9) | — | **1 jour** |
| **L5** | **Matrice de traçabilité clause→code→test du Test 1**, puis signature qa-auditor (M6). Sans elle, rien ne peut être déclaré « done » | L1 | **1 jour** |
| **L6** | **Durcissement des tests** : plancher par classeur sur `test_reproduces_the_tabulated_bands` (m4), Test 4 dans `WORKBOOKS` (m5), échec (et non skip) si l'empreinte manque (m6), signe du delta (m11), `couleur_depuis_conforme` (m2 des tests), corriger le `pytestmark` COM de niveau module (m2) | L0 | **1 jour** |
| **L7** | **`source_locator`** : trois locators + test de relecture de cellule (M9) ; test de non-régression croisé A↔B (M11) | C3 | **1 jour** |
| **L8** | **Chemin 1E** : spec du Test 2 (fenêtre, infiltration) → diagnostics 1A à 1D → 1E → premier verdict pass/fail réel (B3) | L1, C4, C8 | **3 à 5 semaines** |
| **L9** | **Specs manquantes Tests 2, 3, 5** (inexistantes aujourd'hui), puis moteur et adaptateur correspondants | L8 | **4 à 8 semaines** |
| **L10** | **Carte de cellules du classeur officiel** (M12), une fois C5 tranché | C5, L1 | **1 jour** |
| **L11** | **Ergonomie** : 2 lanceurs au lieu de 42, en réécrivant d'abord les 10 imports en modules du paquet (m19, m20) | — | **2 jours** |

**Ordre de grandeur.** Premier verdict SIA 4010 crédible sur une classe (1A = tests 1 et 2A) :
**2 à 3 mois de développement à temps plein**, dont une part non compressible d'exécutions dans VE
qui dépendent de vous. Les lots L0 à L7 représentent **environ 8 jours** et couvrent la totalité des
risques de perte et de faux verts. (Agrégation des efforts individuels chiffrés par les revues ;
c'est mon estimation, pas une donnée des rapports.)

---

## 5. Les trois choses à faire en premier

### 1. Mettre le travail en sécurité — aujourd'hui (L0, quelques heures)

**Pourquoi celle-là.** C'est le seul point sur lequel **les cinq relecteurs et les cinq
contre-experts sont d'accord**, et c'est le seul risque de perte **totale**. Le dépôt A n'a aucun
remote, suit 25 fichiers dont 4 `.gitkeep`, n'a pas de `.gitignore`, et vit dans un répertoire non
synchronisé. Le dépôt B n'a versionné **ni ses 532 tests ni son cœur SIA 4010**. Tout ce qui est
décrit de bon au §2 peut disparaître avec un `git clean -fd`. Coût : quelques heures. Bénéfice :
tout le reste devient possible.
**Piège à ne pas rater :** corriger le garde `iesve` **dans le même commit**, sinon la CI passe de
« jamais exécutée » à « rouge en permanence pour une faute de frappe » — et le réflexe sera de
désactiver le seul contrôle automatique de la règle n°4.

### 2. Fermer une boucle complète sur le cas 600 (L1, 3 à 5 jours)

**Pourquoi celle-là.** C'est la seule action qui fait bouger le compteur qui compte : 0/30 → 1/30.
Et c'est **atteignable maintenant** : le générateur du cas 600 est le seul marqué prêt, la météo
DRYCOLD est attestée par un fichier de dérivation à sha256 (§2.8, découverte de la contre-expertise
que les revues initiales avaient manquée), l'UI est câblée jusqu'à ApacheSim. C'est aussi le seul
moyen de savoir si `ve_adapter` fonctionne : aujourd'hui son moteur tourne sur une fixture dont le
propre code dit qu'elle « n'a jamais été produite par une simulation IESVE réelle »
(`ve_adapter/test1_adapter.py:1128-1133`).
**Ce que cette boucle prouvera ou infirmera d'un coup :** l'import du modèle, ApacheSim,
l'extraction, l'agrégation, la comparaison, l'archivage de preuve — six maillons jamais exercés
ensemble.

### 3. Tester les deux fonctions qui produisent et qui affichent les nombres (L2 + L3, 3 jours)

**Pourquoi celles-là et pas d'autres.** Sur l'ensemble des défauts recensés, **seuls deux
produisent un résultat faux ET vert** : l'agrégation mensuelle de `ve_adapter` (B4) et le verdict de
tableau de bord d'`excel_report` (M1). Tous les autres défauts produisent soit du bruit
documentaire, soit un refus explicite (le dispositif est fail-closed presque partout, ce qui est un
vrai acquis). Ce sont les deux endroits où le produit peut mentir silencieusement à un client ou à
la sous-commission — l'un sur la valeur calculée, l'autre sur la phrase « READY FOR DETAILED
REVIEW ». Les deux sont du Python testable sans VE. 3 jours pour supprimer la seule catégorie de
risque qui ne se voit pas.

**Ce qui n'est délibérément pas dans les trois premiers :** la carte de cellules du classeur
officiel (en aval de la boucle 600 et d'une décision de format), les specs des Tests 2/3/5 (en aval
de la boucle 600), le nettoyage documentaire (réel mais sans effet sur un verdict), la réduction des
42 scripts (ergonomie). Tous restent au plan, aucun ne bloque.

---

## 6. Ce que la revue n'a pas pu vérifier

Angles morts assumés. Ils sont importants : plusieurs recouvrent exactement la partie du produit
qui n'a jamais fonctionné.

1. **Rien n'a été exécuté DANS IESVE, par aucun des dix relecteurs.** Toute la partie `iesve` de
   `ve_adapter/test1_adapter.py` (l. 308 à 1046 : création de matériaux, constructions, profils,
   `assigner_meteo_drycold()`, `lancer_apachesim_cas()`, lecture `.aps`), le comportement réel de
   l'interface Tk dans VE, la génération de modèle et l'écriture COM dans le vrai classeur sont
   **non vérifiés**. On peut dire « non testé », pas « faux ».
2. **L'export Excel par COM n'a jamais été exécuté nulle part** : 3 tests, 3 skippés, sur cette
   machine comme en CI. Le premier essai réel se fera chez le client. C'est l'un des deux livrables
   que vous avez nommés.
3. **La source primaire ISO 52016-1:2017 est invérifiable** (M3). Ce qui a été contrôlé est
   l'auto-cohérence arithmétique de la transcription, qui ne détecte pas un décalage systématique.
4. **72 des 84 bandes officielles** sont extraites correctement **au sens du format**, mais leur
   interprétation normative (quelle grandeur est Testgrösse, laquelle est Diagnosegrösse) n'a été
   contrôlée par personne. 12 bandes seulement ont été recalculées et confirmées manuellement
   (48 par le test automatisé, sur 3 classeurs).
5. **Le gros du dépôt B n'a pas été audité** : `excel_report.py` (6 787 l.), `sia4010_checker.py`
   (1 654 l.), `sia380_checker.py`, `ve_asset_provisioner.py` (~2 400 l.), `data_extractor.py`,
   `model_analyzer.py`, `ve_api.py`. Leur **pouvoir de détection est inconnu** — et l'expérience de
   cette revue est qu'il ne se déduit pas de la couverture (83 % de couverture pour 0 % de détection
   sur `excel_report.py`).
6. **Les tables SIA 380/2 du `config.py`** (U, g, tau_v, infiltration) n'ont pas été confrontées au
   PDF de la norme.
7. **La procédure d'attestation SIA elle-même** n'a été vérifiée par personne : on ne sait pas si les
   5 « familles de preuves » que le code produit correspondent à ce que la sous-commission demande.
8. **Un défaut d'isolation existe dans la suite du dépôt B** : le même monkeypatch de niveau module
   donne 98 interceptions lancé seul et 0 lancé dans la suite complète — quelque chose recharge les
   modules `swiss_sia`. Sans conséquence sur les verdicts, mais **toute mesure de mutation faite de
   cette façon est potentiellement un artefact**.
9. **Les specs des Tests 5, 6 et 7 n'ont pas été auditées au fond**, ni le détail de
   `batiment-exemple-zonage.spec.md` (967 lignes, 4 points marqués indécidables).
10. **La cohérence d'unité de la Table 31** n'est pas tranchée : l'en-tête du classeur porte
    `0,001 ΦH/C;ld` (un flux) et `kWh (peak)`. Les ordres de grandeur (~1,75) sont compatibles avec
    les deux lectures.
11. **Personne n'a cherché de travaux ailleurs** : branches non fusionnées, autre machine, autre
    compte. Ce constat porte sur l'état des deux disques au 1er août 2026.
12. **Un élément matériel non tranché, à verser au dossier avant de figer la liaison « température
    opérative » :** le classeur Test 1 juxtapose en `AY106:BM120` les valeurs ASHRAE 140 et les
    colonnes SIA, sous des en-têtes qui parlent de température **d'air** de zone, tandis que la
    colonne SIA correspondante est étiquetée « operativ ». Le SIA compare donc directement sa
    colonne opérative à des températures d'air ASHRAE. Cela ne tranche pas le débat, mais cela
    pousse dans le sens contraire de l'arbitrage actuel.
