# Deux produits, une frontière — SIA 380/2 vs SIA 4010

Ce dépôt porte **deux produits distincts** qu'il ne faut pas confondre. Ce
document trace la frontière, une fois pour toutes, et donne les commandes pour
travailler sur chacun sans l'autre.

Établi le 2026-08-13, après vérification directe dans le code.

## Le fait qui fonde la séparation

**Les deux produits ne partagent aucun code.** Vérifié : le cœur 380/2 n'importe
aucun module 4010, et aucun module 4010 n'importe le cœur 380/2. La seule
occurrence croisée est une chaîne de caractères (`"formal_compliance_verdict"`
dans `test1_campaign.py`), pas un import. La frontière existe déjà dans le code ;
ce document la rend visible.

```
grep -rE "^(from|import) .*(sia380_checker|compliance_verdict|reference_project)" \
     swiss_sia/reference_model/ engine/     # -> vide
grep -rE "^(from|import) .*(sia4010|reference_model)" \
     swiss_sia/sia380_checker.py swiss_sia/compliance_verdict.py \
     swiss_sia/app.py swiss_sia/data_extractor.py                # -> vide
```

---

## Produit 1 — Vérificateur de conformité SIA 380/2 (le MVP commercial)

Lit un **modèle client** IESVE et produit un **diagnostic par exigence**. Ne
prononce jamais la conformité globale tout seul : la comparaison au bâtiment de
référence reste une entrée révisée, comme l'exige la méthode de la norme.

**Ce qu'il fait, et sa limite exacte** : voir [MVP_COMPLETION_MATRIX.md §9](MVP_COMPLETION_MATRIX.md).

### Lanceurs (dans VEScripts)

| Script | Rôle |
|---|---|
| `Run_VE_Swiss_Compliance.py` | Analyse complète + rapport Excel/PDF. C'est le point d'entrée principal. |
| `Run_VE_Swiss_Compliance_Hub.py` | Cockpit : audit client → preuves → rapport. |
| `Run_VE_Swiss_Compliance_Remediation_Probe.py` | Audit **lecture seule**, ne mute jamais le modèle. |
| `Run_VE_Swiss_Compliance_Evidence_Wizard.py` | Assistant de collecte des preuves révisées. |

### Modules cœur (`swiss_sia/`)

`app.py` (orchestration) · `data_extractor.py` (la **seule** frontière `iesve` :
géométrie, constructions, U-values, systèmes, résultats APS) · `model_analyzer.py`
(normalisation en `RoomData`/`SurfaceData`/`OpeningData`) · `sia380_checker.py`
(les dix familles de contrôles) · `compliance_verdict.py` (verdict fail-closed) ·
`reference_project.py` (spéc. du bâtiment de référence) · `evidence_manager.py`,
`evidence_bootstrap.py`, `evidence_wizard.py` (preuves révisées) ·
`remediation_probe.py` · `excel_report.py`, `compliance_report_pdf.py`,
`health_score.py` (sorties) · `config.py` (valeurs limites 380/2, **partagé**).

### Tests — 197, isolables

```bash
pytest -m sia3802
```

---

## Produit 2 — Validation SIA 4010 (le bonus)

Construit les **34 cas de test exacts** figés par la norme, les exécute dans VE
et compare aux références des classeurs officiels. Valide **le logiciel**, pas un
bâtiment client.

### Lanceurs

Tous préfixés `Run_VE_SIA4010_*.py` (Fast Start, campagne Test 1, sondes APS,
Test 2A…). Le préfixe **est** la séparation côté lanceurs.

### Modules cœur

`swiss_sia/reference_model/sia4010/*` (registre des cas, bundles, extraction APS
qualifiée, évaluation) · `swiss_sia/reference_model/*` (constructeur de modèle VE)
· `engine/*` (moteurs de bandes/distributions Python purs, testables en CI sans
`iesve`).

### Tests — 569, isolables

```bash
pytest -m sia4010
```

---

## Base partagée (295 tests, `-m shared`)

Ce que les deux produits utilisent : le constructeur de modèle VE
(`reference_model/`), les passerelles VE (`ve_*`), la conversion météo
(le climat d'essai 4010 **et** le climat d'application 380/2), le style de
rapport et les traductions UI, l'inventaire APS. `config.py` porte les valeurs
des deux normes.

```bash
pytest -m shared
```

---

## Comment travailler séparément

| But | Commande |
|---|---|
| Développer / démontrer le produit 380/2 | `pytest -m sia3802` |
| Travailler la validation 4010 | `pytest -m sia4010` |
| Toucher l'infra partagée | `pytest -m shared` |
| Tout (inchangé) | `pytest` |

Le mécanisme est dans [`tests/conftest.py`](tests/conftest.py) : chaque test est
marqué à la collecte, **aucun fichier n'a été déplacé** — les chemins relatifs
des tests restent valides. Pour reclasser un test, éditer les ensembles en tête
de ce conftest.

## Ce qui reste à faire si on veut une séparation physique complète

Non fait, et volontairement : déplacer les modules 380/2 sous un paquet dédié
(`swiss_sia/compliance_3802/`) imposerait de mettre à jour tous les imports des
lanceurs dans le même commit, dans une worktree déjà chargée. Le couplage étant
nul, ce déplacement est possible proprement plus tard ; il n'apporte rien de
fonctionnel, seulement de la clarté de rangement. La frontière logique, elle, est
déjà nette et documentée ici.
