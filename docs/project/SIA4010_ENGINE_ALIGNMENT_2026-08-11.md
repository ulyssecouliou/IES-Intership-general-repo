# Alignement du moteur d'évaluation SIA 4010 sur les preuves officielles 2026-08-10

**Date** : 2026-08-11
**Auteur** : mise à jour ciblée à partir des classeurs officiels et de la clarification écrite de Prof. Gerhard Zweifel (SIA).
**Portée** : moteur `engine/`, référentiels figés `refs/reference-data/*.json`, extracteur des feuilles `Haeufigkeitskassen`, audits de source.

Cette note est un enregistrement de traçabilité : elle liste, pour chaque décision d'alignement, la preuve (fichier, cellule, ou correspondance SIA) qui la porte. Aucune valeur normative n'a été inventée ni élargie ; les tolérances Test 1 restent celles publiées ; les critères Tests 4 et 6 restent hors gate en l'absence de retour SIA.

---

## 1. Sources d'autorité citées

Trois preuves reçues le 2026-08-10 sont déjà intégrées et re-vérifiées le 2026-08-11 :

- **Correction du classeur Test 7** — [`sia4010_evidence/source_audits/test7-corrected-workbook-20260810.json`](../../sia4010_evidence/source_audits/test7-corrected-workbook-20260810.json), complété par la ré-inspection [`sia4010_evidence/source_audits/test7-workbook-integrity-2026-08-11.json`](../../sia4010_evidence/source_audits/test7-workbook-integrity-2026-08-11.json) (SHA-256 `24937d8f...`, identité vérifiée entre `Downloads/` et `SIA_4010_geteilter_Link/Test7/`).
- **Clarification écrite `Streubereich`** — reçue de Prof. Gerhard Zweifel le 2026-08-10 ; intégrée dans [`engine/sia_distributions_engine.py`](../../engine/sia_distributions_engine.py) (`STATUT_CRITERE = 'CONFIRME_AUTORITE_2026-08-10'`) : le Streubereich par classe de fréquence est l'**enveloppe min/max des programmes de référence**, classe par classe.
- **SIA 2024 catégorie 3.1 (bureau)** — extrait autorité + binding + validation `PASS` sous [`sia4010_evidence/source_audits/sia2024_3_1_authority_20260810/`](../../sia4010_evidence/source_audits/sia2024_3_1_authority_20260810/) ; sans impact direct sur les moteurs d'évaluation, mais requis pour la préparation des cas.

---

## 2. Test 7 — règle « borne basse / borne haute »

### Décision
Utiliser les cellules **`$N8` (Untere Grenze, borne basse) à `$M8` (Obere Grenze, borne haute)** comme bornes inclusives sur `F8:F12 F14:F18 F20`.

### Preuve lue verbatim
Lecture directe openpyxl (`data_only=False`) le 2026-08-11 sur `SIA_4010_geteilter_Link/Test7/Resultaterfassung Test7.xlsx` (SHA-256 `24937d8f421daa74a7f957025bfeb17a42fe2dc807b1a301a6752f4c0e808958`) :

- `Zusammenfassung!L7 = "Mittelwert"`
- `Zusammenfassung!M7 = "Obere Grenze"`
- `Zusammenfassung!N7 = "Untere Grenze"`
- Conditional formatting `sqref=F8:F12 F14:F18 F20  type=cellIs  operator=between  formulas=['$N8', '$M8']`

### Conformité du code actuel
- [`engine/test7_engine.py`](../../engine/test7_engine.py) charge `borne_basse` et `borne_haute` depuis le référentiel figé et délègue à `scatter_band.verdict()` qui compare avec bornes INCLUSIVES (`band.contains`).
- [`refs/reference-data/test-7.ref.json`](../../refs/reference-data/test-7.ref.json) porte `source.sha256 = "24937d8f…"` et `source.correction = "Règle conditionnelle N (borne basse) à M (borne haute)"`, dates de figeage `2026-08-10`.

Les bornes numériques du classeur corrigé sont **identiques** à celles du pré-correction (`numeric_bounds_identical: true` cf. audit 2026-08-10) : seule la cellule référencée par la règle a changé. La régression numérique du moteur reste donc `0`. Ce n'est pas une ré-implémentation — c'est un ancrage explicite sur les colonnes officielles.

### Test de non-régression
- [`tests/test_sia4010_engine_alignment_20260811.py::Test7CorrectedWorkbookIntegrityTests`](../../tests/test_sia4010_engine_alignment_20260811.py)
  - Vérifie le SHA-256 du classeur ;
  - Vérifie que `test-7.ref.json` est épinglé sur le SHA-256 corrigé ;
  - Rejoue la CF-rule au niveau du XML pour prouver `['$N8', '$M8']`.

---

## 3. Tests 2, 3, 5 — Streubereich = enveloppe min/max par classe

### Décision
Sur chaque classe de fréquence, le Streubereich est l'**enveloppe min/max des programmes de référence**. La lecture `moyenne ± max_dev` reste calculée mais **n'est plus contraignante**. Elle est conservée uniquement pour la comparaison avec les anciens audits.

### Preuve lue verbatim
Clarification écrite reçue le 2026-08-10 de Prof. Gerhard Zweifel :

> « `Streubereich` désigne l'enveloppe minimum/maximum des programmes de référence pour chaque classe de fréquence. Les totaux affichés inférieurs à 8760 heures ne signifient pas des séries incomplètes : certaines valeurs horaires sont hors des bornes définies. Elles doivent être comptées séparément. »

### Conformité du code actuel
- [`engine/sia_distributions_engine.py`](../../engine/sia_distributions_engine.py)
  - `LECTURE_ENVELOPPE = 'enveloppe_min_max'` (contraignante) et `LECTURE_BANDE = 'moyenne_plus_ecart_max'` (audit uniquement) ;
  - Bloc verdict : `hors[LECTURE_ENVELOPPE]` déclenche `VERDICT_FAIL` (ligne 247). La lecture bande n'entre pas dans le verdict.
- Référentiels figés [`refs/reference-data/test-2.distributions.ref.json`](../../refs/reference-data/test-2.distributions.ref.json), [`test-3.distributions.ref.json`](../../refs/reference-data/test-3.distributions.ref.json), [`test-5.distributions.ref.json`](../../refs/reference-data/test-5.distributions.ref.json) portent `statut_critere: "CONFIRME_AUTORITE_2026-08-10"`.

### Test de non-régression
- [`tests/test_sia4010_engine_alignment_20260811.py::DistributionEngineEnvelopeBindingTests`](../../tests/test_sia4010_engine_alignment_20260811.py)
  - Construit un bloc où le candidat est **hors enveloppe** mais dedans la bande symétrique → doit FAIL ;
  - Vérifie qu'un candidat au centre passe PASS et laisse `nb_hors_lecture[LECTURE_ENVELOPPE] == 0`.

---

## 4. Compteur hors-classe

### Décision
Les valeurs horaires qui excèdent la borne supérieure de la dernière classe ne sont **jamais** absorbées dans la dernière classe. Elles sont comptées à part et remontées dans un compteur d'audit.

### Preuve
Autorité 2026-08-10 (cf. §3) explicite : « certaines valeurs horaires sont hors des bornes définies. Elles sont comptées séparément. »

### Conformité du code actuel
- `sia_distributions_engine.classer_avec_hors_classes(serie, bornes)` retourne `{effectifs, hors_classes_superieur, total_numerique}`.
- `sia_distributions_engine.classer(serie, bornes)` compte **uniquement** les valeurs qui trouvent une classe ; les excédents ne sont pas ajoutés à la dernière classe.
- Le champ `contributeurs_hors_classes` est propagé dans `evaluer_bloc`, en priorité par le champ figé `heures_hors_classes` du référentiel, avec repli sur `max(0, 8760 − total_heures)`.

### Tests de non-régression
- [`tests/test_sia4010_engine_alignment_20260811.py::OutOfClassCounterTests`](../../tests/test_sia4010_engine_alignment_20260811.py)
  - Une série de 9 valeurs dont 2 dépassent la dernière borne → `hors_classes_superieur == 2` ;
  - Une valeur `100` bien au-delà de la dernière borne → `effectifs[-1] == 0` (jamais absorbée).

---

## 5. Classes de fréquence — les six classeurs en ont

> **Corrigé le 2026-08-12.** La version initiale de cette section affirmait que
> la feuille de classes de fréquence n'existait que dans les Tests 4, 6 et 7,
> et que les Tests 2, 3 et 5 « organisaient leurs données autrement ». C'était
> faux. La cause : les classeurs officiels emploient deux orthographes, et
> l'extracteur n'en cherchait qu'une, excluant silencieusement trois fichiers.

### Décision
Supprimer toute affirmation prétendant que des Tests parmi 2 à 7 n'auraient pas
de classes de fréquence. **Les six en ont.** Leur portée exacte comme gate
d'acceptation pour les Tests 4, 6 et 7 reste en revue par la sous-commission
SIA, mais leur existence est prouvée par lecture directe.

### Preuve lue verbatim
Inspection openpyxl le 2026-08-12, tous les classeurs :

| Classeur | Feuille | Grandeurs binées | Chartsheets |
|---|---|---:|---:|
| `Resultaterfassung_Test2.xlsx` | `Haeufigkeits**kl**assen` | 3 | 50 |
| `Resultaterfassung_Test3.xlsx` | `Haeufigkeits**kl**assen` | 2 | 55 |
| `Resultaterfassung Test4.xlsx` | `Haeufigkeits**k**assen` | **11** | **48** |
| `Resultaterfassung_Test5.xlsx` | `Haeufigkeits**kl**assen` | 11 | 0 |
| `Resultaterfassung_Test6.xlsx` | `Haeufigkeits**k**assen` | **11** | **37** |
| `Resultaterfassung Test7.xlsx` | `Haeufigkeits**k**assen` | 20 | 50 |

Trois constats à conserver :

1. **Deux orthographes.** Les Tests 4, 6 et 7 écrivent `Haeufigkeitskassen`,
   sans le `l` de `Klassen`. Les Tests 2, 3 et 5 écrivent `Haeufigkeitsklassen`.
   Les deux formes sont désormais acceptées.
2. **Les Tests 4 et 6 ont plus de grandeurs binées que les Tests 2 et 3.**
   11 contre 3 et 2. L'affirmation inverse, transmise à la SIA le 2026-08-07,
   était fausse et l'autorité l'a relevée.
3. **Les feuilles de distribution des Tests 4 et 6 existent** : 48 et 37
   `Chartsheet`, dont une par grandeur binée. Elles ne portent pas le préfixe
   `Vert.` des Tests 2/3/5/7 — elles sont nommées directement par la grandeur
   (`Zu- und Abluftvolumenstrom`, `Zulufttemperatur`, `Leistung Ventilatoren`…).
   Compter le préfixe au lieu du type de feuille est ce qui a produit l'erreur.

Colonne `Fenstermodelle` (Tests 2 et 3) : légende de modèles de fenêtre en
texte, sans unité ni borne numérique. Ce n'est pas une grandeur binée ;
l'extracteur l'exclut par règle explicite (label + unité + au moins une borne
numérique requis), non par accident de mise en page.

Cellule `9999` : convention SIA « classe non utilisée pour cette grandeur » ;
jamais interprétée comme une borne.

### Preuve complémentaire — le critère de somme annuelle des Tests 4 et 6 est opérant
Contrairement à ce que le brouillon du 2026-08-07 supposait, il n'est pas à
inférer : il vit dans la mise en forme conditionnelle du classeur, et sa plage
couvre exactement le bloc `Testgrössen` en s'arrêtant avant les
`Diagnosegrössen` — même structure que le Test 7.

| Classeur | Mise en forme conditionnelle | En-têtes | Groupes |
|---|---|---|---|
| Test 4 | `D10:D12` between `$U10`,`$V10` | T8 `Mittelwert`, U8 `obere Grenze`, V8 `untere Grenze` | A9 `Testgrössen`, A13 `Diagnosegrössen` |
| Test 6 | `E10:E15` between `$L10`,`$M10` | K8 `Mittelwert`, L8 `obere Grenze`, M8 `untere Grenze` | A10 `Testgrössen`, A16 `Diagnosegrössen` |

### Preuve — absence de `Testkriterien` dans les spécifications
Recherche pypdf sur les sept spécifications (`testkriteri|streubereich|abweichung|häufigkeitsverteilung`) :

| Spéc | Occurrences |
|---|---|
| Test 1 | `Testkriterien`, `Streubereich` |
| Test 2 | les quatre |
| Test 3 | les quatre |
| **Test 4** | **aucune** |
| Test 5 | les quatre |
| **Test 6** | **aucune** |
| **Test 7** | **aucune** |

Cette moitié de l'affirmation du 2026-08-07 est donc confirmée : les Tests 4, 6
et 7 n'énoncent aucun critère dans leur spécification.

### Livrable
- [`swiss_sia/reference_model/sia4010/haeufigkeitskassen_extractor.py`](../../swiss_sia/reference_model/sia4010/haeufigkeitskassen_extractor.py) : pur openpyxl, sans `iesve`, accepte les deux orthographes, enregistre celle trouvée dans `sheet_name` pour la provenance, et identifie une grandeur binée par sa forme propre.
- Tests : [`tests/test_haeufigkeitskassen_extractor.py`](../../tests/test_haeufigkeitskassen_extractor.py) — les six classeurs, orthographe et nombre de grandeurs figés, exclusion de `Fenstermodelle`, conservation du sentinelle `9999`, monotonie des indices.

### État de gate
Le producteur des référentiels distributions (`scripts/build_sia_distribution_reference.py`) ne construit à ce jour que les référentiels des Tests **2, 3, 5** — les trois dont la spécification énonce le critère de distribution.

La question ouverte n'est plus « les distributions existent-elles » mais
**« le critère de distribution s'applique-t-il aux Tests 4, 6 et 7, dont les
spécifications n'énoncent aucun critère alors que leurs classeurs portent la
même machinerie que les Tests 2/3/5 ? »**. Posée à la SIA le 2026-08-07 sur une
prémisse fausse ; l'autorité a relevé l'erreur sans répondre au fond. À
reposer. Si la réponse est oui, il faudra étendre
`sia_distributions_engine.TESTS_SUPPORTES` de `(2, 3, 5)` à `(2, 3, 4, 5, 6, 7)`
et construire quatre référentiels supplémentaires.

---

## 6. Test 1 — aucun critère inventé pour les six cas normatifs

### Décision
Les six cas normatifs Test 1 (`600, 640, 900, 940, 600FF, 900FF`) restent **sans critère pass/fail**. Seul le cas diagnostique `1E` porte un verdict (Streubereich sur 4 programmes de référence). Aucune tolérance n'est ajoutée par défaut ; aucun statut PASS n'est produit pour les six cas normatifs. Statut d'engagement conservé : `RESULTS_RECORDED_NO_CRITERION`.

### Preuve
[`engine/test1_engine.py`](../../engine/test1_engine.py) — ligne 86 : `CAS_AVEC_CRITERE = ('1E',)`. Docstring lignes 14-25 cite verbatim la Testkriterien du `Spezifikation_Test1.pdf` :
> « Es gibt dafür kein Abweichungskriterium. »

### Tests de non-régression
- [`tests/test_sia4010_engine_alignment_20260811.py::Test1SixNormativeCasesRemainInformativeTests`](../../tests/test_sia4010_engine_alignment_20260811.py)
  - `CAS_AVEC_CRITERE == ('1E',)` ;
  - Chacun des 6 cas normatifs est absent de l'ensemble à critère.

---

## 7. Ce que cette note ne fait PAS

- **Ne modifie pas** les moteurs `engine/*.py` : le code déjà présent (M) est cohérent avec les preuves ; seul l'extracteur `haeufigkeitskassen_extractor.py` est un ajout.
- **Ne modifie pas** les fichiers JSON figés sous `refs/reference-data/` : le hook `garde_refs.py` les protège ; toute mise à jour passe par un producteur audité (`scripts/build_*.py`).
- **Ne modifie pas** les classeurs officiels SIA sous `SIA_4010_geteilter_Link/` : ils sont traités comme des preuves en lecture seule.
- **Ne prononce pas** de verdict de conformité SIA 4010 : la sous-commission (SIA 4010:2023 §4.6.2) reste seule légitime.
- **Ne remplace pas** la question 3 du courriel du 2026-08-07 (Testkriterien manquants pour Tests 4 et 6). Tant que la SIA n'a pas répondu, ces deux tests restent `INFERE` côté critère et sans gate exécutable côté distribution.
- **N'invente aucune tolérance** pour Test 1 ni pour les Testgrößen du Test 7 : les bornes viennent verbatim du classeur.

---

## 8. Fichiers touchés dans cette passe

**Créés :**
- `docs/project/SIA4010_ENGINE_ALIGNMENT_2026-08-11.md` (cette note)
- `sia4010_evidence/source_audits/test7-workbook-integrity-2026-08-11.json`
- `swiss_sia/reference_model/sia4010/haeufigkeitskassen_extractor.py`
- `tests/test_haeufigkeitskassen_extractor.py`
- `tests/test_sia4010_engine_alignment_20260811.py`

**Non modifiés (par choix explicite, déjà cohérents) :**
- `engine/test1_engine.py`, `engine/test7_engine.py`, `engine/sia_distributions_engine.py`, `engine/scatter_band.py`, `engine/sia_bandes_engine.py`
- Tous les `refs/reference-data/*.json`
- Tous les classeurs officiels sous `SIA_4010_geteilter_Link/`

---

## 9. Action VE exacte à faire par Ulysse

Rien à faire dans VE 2025 pour cette passe : elle porte exclusivement sur la traçabilité et le moteur pur Python. Le prochain jalon utile côté VE reste :

1. Confirmer avec Johan si IES dispose déjà des données SIA 2028 solaires (question 1 du courriel brouillon du 2026-08-10). Sans elles, aucun cas Test 2-7 ne peut avancer au-delà de `IMPLEMENTED_UNQUALIFIED`.
2. Une fois débloqué : exécuter les 5 runtime-probes Test 1 (`640, 600FF, 900, 940, 900FF`) dans un projet VE 2025 jetable, comme documenté dans `docs/project/MVP_COMPLETION_MATRIX.md`.
