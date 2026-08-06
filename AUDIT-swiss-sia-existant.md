# AUDIT — code existant `IES-Intership-general-repo` / paquet `swiss_sia`

> Complète `AUDIT.md` (qui porte sur les données de référence de ce dépôt-ci).
> Fichier séparé volontairement : il audite un **autre dépôt**,
> `C:\Users\ulysse.couliou\Documents\IES Internship\IES-Intership-general-repo`.
>
> Doctrine `CLAUDE.md` : le code existant est présumé faux jusqu'à preuve
> reproductible. Chaque verdict ci-dessous est adossé soit à une exécution réelle
> contre les classeurs officiels, soit à une citation de la spécification.
>
> Audité le 2026-07-30. Aucun fichier de ce dépôt n'a été modifié.

---

## Méthode

Le seul instrument de vérité disponible est `refs/reference-data/test-1.ref.json`,
dont la fidélité au classeur SIA est établie cellule par cellule (1336/1336, cf.
`AUDIT.md` et `engine/tests/test_ref_integrity.py`). L'audit consiste à faire
tourner le code existant sur les **classeurs officiels réels** et à confronter sa
sortie à ces références, puis à confronter ses critères au texte des
spécifications SIA.

---

## Élément n°1 — `swiss_sia/sia4010_checker.py` (1654 lignes)

### VERDICT : **HORS SUJET POUR CETTE CONFRONTATION** — ce n'est pas un moteur de validation

La cible demandée ne contient aucune comparaison numérique à confronter.
`_run_sia4010_tests()` (l. 1438-1528) dérive les sept statuts de test
**exclusivement de l'état des preuves** : présence de familles de fichiers dans
`sia4010_evidence/`, et lignes `PASS`/`VALIDATED`/`FAIL` saisies par un relecteur
dans des CSV. Les statuts émis sont `NOT_CHECKABLE`, `EVIDENCE_INCOMPLETE`,
`READY_FOR_OFFICIAL_REVIEW`, `OFFICIAL_RESULTS_RECORDED`, `FAIL` — et le `score`
vaut **0 dans toutes les branches**.

Ce n'est pas un défaut : le module est explicitement conservateur, son docstring
et le README refusent de revendiquer une conformité SIA autonome. C'est une
posture juridiquement saine.

**Mais c'est une conséquence produit majeure** : en l'état, **rien dans la chaîne
livrée ne vérifie numériquement un résultat**. Un humain déclare un PASS dans un
CSV, l'outil le compte. Le moteur de comparaison existe (élément n°2) mais n'est
pas branché sur ce chemin. C'est précisément l'écart que le MSP doit combler.

---

## Élément n°2 — `reference_model/sia4010/compliance_comparator.py`

### VERDICT : **CONFORME** — à conserver tel quel

Revue ligne à ligne de `Sia4010ComplianceComparator.compare_one()` :

1. **La bande officielle prime sur toute tolérance.** Si le classeur fournit
   `untere/obere Grenze`, le verdict est `lower <= observé <= upper`. Exactement
   le critère du cas 1E établi dans `AUDIT.md` pt 4.
2. **Aucune tolérance inventée.** Sans tolérance fournie par la source, le
   résultat est `NOT_CHECKABLE`, jamais `PASS`. C'est la bonne défaillance.
3. **Aucune conversion d'unité implicite** : unités différentes → `NOT_CHECKABLE`.
4. **Observé manquant → `NOT_CHECKABLE`**, jamais un succès par défaut.

Le docstring de `ExpectedResult` énonce correctement que `expected_value` porte le
`Mittelwert` « pour audit seulement » quand la bande existe. L'auteur avait
compris la subtilité que l'audit des données a dû redécouvrir.

---

## Élément n°3 — `reference_model/sia4010/workbook_loaders.py`

### VERDICT : **CONFORME ET PLUS COMPLET QUE NOS PROPRES RÉFÉRENCES**

Confrontation exécutée : `parse_test1_reference_bands()` lancée sur
`Test1/Resultaterfassung_Test1.xlsx`, sortie comparée une à une à
`test-1.ref.json`.

| Contrôle | Résultat |
|---|---|
| Métriques produites | 28, toutes avec bande |
| Cas couverts | `1E` uniquement |
| Confrontées aux références vérifiées | **26 / 26** |
| Écarts sur `Mittelwert`, `obere`, `untere Grenze` (tol. 1e-9) | **0** |
| Références vérifiées non couvertes par le loader | **0** |

Trois points de conception à porter au crédit du code :

1. **Les colonnes sont localisées par leur libellé** (`_UPPER = "obere grenze"`,
   `_LOWER = "untere grenze"`, `_MEAN = "mittelwert"`), jamais codées en dur. Le
   loader est donc **structurellement immunisé** contre le défaut n°1 d'`AUDIT.md`
   (décalage de colonnes), qui est le bug qui s'est réellement produit côté
   extraction.
2. **Il ne retient que le cas 1E**, conformément à `Spezifikation_Test1.pdf` :
   les cas 600/640/900/940/600FF/900FF n'ont aucun critère de déviation. Le
   docstring du module cite explicitement ce point. Cohérent avec
   `traceability/test-1.spec.md` §6.
3. **Il trouve une bande que nos références ratent** (ci-dessous).

### Écart trouvé — mais du côté de NOS données, pas du sien

Les 2 métriques excédentaires (`H82`, `H83`) correspondent à la **Table 31**,
lignes 78-83 de la feuille : *Test results Annual hourly integrated peak*
(`0,001 ΦH/C;ld`, kWh peak), cas 1E, quantités `Heating` et `Cooling`, avec
`Mittelwert` / `obere Grenze` / `untere Grenze` en G/H/I.

C'est un **troisième critère pass/fail réel du cas 1E**. `AUDIT.md` l'avait classé
« présente dans l'Excel, ni extraite ni mentionnée ; hors périmètre déclaré ; à
confirmer si requise » : la réponse est **oui, requise**.

Formule vérifiée à la main sur la ligne 82 (chauffage) :
moyenne des 4 programmes = 1.75245555 (= G82) ; écart max = 0.0913288 ;
`mean + écart_max` = 1.8437844 (= H82) ; `mean − écart_max` = 1.6611267 (= I82).
La formule `Streubereich = moyenne ± max|programme − moyenne|` tient donc aussi
pour la Table 31.

→ **Action pour `reference-data-engineer`** : ajouter la Table 31 à
`test-1.ref.json`, puis relever `CELLULES_MINIMUM` dans le test d'intégrité.

---

## Élément n°4 — `reference_model/sia4010/distribution_reference.py`

### VERDICT : **À ARBITRER — critère probablement PLUS STRICT que la norme**

C'est le point le plus sérieux de cet audit.

**Ce que fait le code.** Le docstring est explicite : *« the band is the per-bin
min/max of those series »*. La bande de dispersion par classe de fréquence est
construite comme l'**enveloppe min/max** des séries horaires des programmes de
référence.

**Ce que dit la norme.** `Spezifikation_Test2.pdf`, section *Testkriterien*,
distingue deux critères :

- somme annuelle : « *Mittelwert der Referenzprogramme +/- maximale Abweichung* » ;
- distribution de fréquence : « *muss im **Streubereich** der Referenzprogramme
  liegen* ».

**Ce que dit le classeur.** Vérifié par balayage de la zone
`Häufigkeitsklassen` de `Resultaterfassung_Test2.xlsx` (lignes 26 à 308,
239 colonnes) : **aucune** cellule `Mittelwert` / `obere Grenze` /
`untere Grenze`. La bande des distributions n'est **pas tabulée** — elle doit
être dérivée. Le choix de la formule est donc une **interprétation normative**,
pas une lecture.

**Pourquoi le choix actuel est douteux.** Partout où le SIA tabule lui-même un
`Streubereich` (Tables 28, 29 et 31 du Test 1), il vaut `moyenne ± max|écart|`.
Or, pour tout jeu de programmes :

```
max|p − moyenne| ≥ max − moyenne   et   max|p − moyenne| ≥ moyenne − min
⟹  [min, max]  ⊆  [moyenne − écart_max, moyenne + écart_max]
```

L'enveloppe min/max est donc **toujours incluse** dans la bande
`moyenne ± écart max` : strictement plus étroite, sauf cas dégénéré. Le code
applique un critère **plus sévère que celui de la norme**.

**Conséquence commerciale** : risque de **faux échec** — déclarer IESVE non
conforme sur un test qu'il passe selon le critère officiel. C'est l'erreur la
plus coûteuse possible pour ce produit.

**Réserve d'honnêteté** : la spécification emploie délibérément deux formulations
différentes pour les deux critères. On peut soutenir que « Streubereich » désigne
littéralement l'étendue min–max. Les deux lectures se défendent sur le texte seul ;
l'arithmétique du classeur SIA tranche en faveur de `moyenne ± écart max`, mais le
classeur ne tabule rien pour ce critère précis. **Ce point relève de
`norm-analyst`, pas d'une correction unilatérale.** Ne pas « corriger » avant
arbitrage.

---

## Couverture des loaders — exécution réelle sur les sept classeurs officiels

| Test | Métriques | Avec bande | Cas couverts |
|---|---|---|---|
| 1 | 28 | 28 | 1E |
| 2 | 8 | 8 | 2A, 2B, 2C, 2D |
| 3 | 12 | 12 | 3A → 3G |
| 4 | 3 | 3 | Test 4 |
| 5 | 16 | 16 | 5A, 5B, 5C, 5D |
| 6 | 6 | 6 | Test 6 |
| 7 | 11 | 11 | Test 7 |

Les sept loaders s'exécutent sans erreur et produisent des bandes. C'est un actif
substantiel et fonctionnel.

`⚠ À CONFIRMER` : le Test 5 rend 16 métriques pour 4 cas (4 par cas) alors que sa
feuille `Zusammenfassung` liste **8** grandeurs annuelles (ventilateurs, batterie
chaude, batterie froide totale et latente, WRG total et latent, auxiliaire WRG,
humidification). Le Test 4 n'en rend que 3. Il faut confronter cette couverture
aux `Spezifikation_Test4/5.pdf` pour savoir s'il s'agit d'une couverture partielle
ou du fait que toutes les grandeurs n'ont pas de bande. **Non tranché ici.**

---

## Ce qui n'a PAS été audité

- `sia380_checker.py` (66 Ko) — périmètre différent (contrôle de modèles clients
  SIA 380/2), sans valeurs de référence disponibles pour le confronter.
- `data_extractor.py`, `model_analyzer.py`, `ve_api.py`, `ve_asset_provisioner.py`
  — exigent une session IESVE ouverte ; non exécutables ici.
- `excel_report.py` (345 Ko) et la génération PDF — non exécutés.
- `native_ui.py`, `navigator.py` — non exécutés.
- Les 538 tests du dépôt — collectés (1,4 s), **non exécutés**.
- La correction effective des séries horaires candidates (`Daten_Testprogramm`) :
  aucun résultat IESVE n'a encore été produit, donc aucun verdict de bout en bout
  n'a pu être observé.

---

## Actions

1. **`norm-analyst`** — trancher la définition de `Streubereich` pour les
   distributions de fréquence (min/max vs moyenne ± écart max), avec citation.
   Bloquant pour les tests 2 à 5. C'est l'action la plus prioritaire de cet audit.
2. **`reference-data-engineer`** — ajouter la Table 31 (cas 1E, charges de pointe
   horaires, G/H/I lignes 82-83) à `test-1.ref.json`.
3. **Consolidation** — le comparateur et les loaders sont sains et reproductibles :
   ils constituent la base à conserver. Ce dépôt-ci apporte en retour les données
   de référence vérifiées et les tests d'intégrité exécutables.
4. **Brancher le comparateur** sur le chemin produit : aujourd'hui `sia4010_checker`
   compte des déclarations humaines pendant que `compliance_comparator` sait
   comparer. Les relier est le cœur du MSP.

_Audité par : Claude (session orchestrateur) — 2026-07-30. Aucun fichier du dépôt
audité n'a été modifié._
