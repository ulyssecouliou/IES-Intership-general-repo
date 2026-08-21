# Matrice de traçabilité — SIA 380/2:2022 §7.2.4 « Puissance électrique requise »

Auditeur QA indépendant — 2026-08-21. **Lecture seule du code de production ;
aucune modification.** Commits audités : `11e3808` (implémentation §7.2.4),
`3d6d790` (gate conditionnel norm-analyst A5). Ruling normatif de référence :
`traceability/audit-A5-verdict-porte-7.2.4-puissance-electrique-sia3802.md`.

Modules audités :
- `swiss_sia/config.py` (`SIA3802_ELECTRICAL_POWER_LIMITS_W_M2`, `..._SOURCE`)
- `swiss_sia/sia380_checker.py::_evaluate_electrical_power` (L.1425-1511) +
  détection `has_fluid_installation` (L.393-402)
- `swiss_sia/compliance_verdict.py` gate (L.249-318)
- `swiss_sia/evidence_manager.py::_normalize_electrical_power_record` (L.520-580)

Preuves exécutées : `python -m pytest tests/ -k "electrical or robustness or
verdict or criteria or evidence" -q` → **254 passed, 22 subtests passed, 0
failed** (2026-08-21). Sondes adverses indépendantes exécutées (voir colonnes).

---

## 1. Valeurs sourcées

| Exigence de norme | Implémentation | Preuve / test | Verdict |
|---|---|---|---|
| §7.2.4.2 : neuf/remplacement = 7 W/m² ; existant/rénové = 12 W/m² (PDF p.32) | `SIA3802_ELECTRICAL_POWER_LIMITS_W_M2 = {"new":7.0,"existing":12.0}` | Extraction PyMuPDF page 32 : « … ne dépasse pas **12 W/m2, au lieu de 7 W/m2** … installations existantes et rénovées ». Correspondance exacte. | **CONFIRMÉ** |
| Citation d'article traçable | `SIA3802_ELECTRICAL_POWER_SOURCE = "SIA 380/2:2022 §7.2.4.2, page PDF 32"` | `repr()` runtime = `'SIA 380/2:2022 §7.2.4.2, page PDF 32'` (le `\2` vu par certains outils est un artefact d'affichage, pas la valeur stockée). Locator conforme. | **CONFIRMÉ** |
| Surface = surface nette de plancher conditionnée (§7.2.4.1) | Grandeur relue en W/m², champ `conditioned_area_m2` transporté, non recalculé | Cohérent (valeur fournie déjà en W/m²). L'appariement métier reste sous responsabilité relecteur. | **CONFIRMÉ (réserve, cf. §5-R3)** |

## 2. Pas de faux-pass (fail-closed du blocage)

| Exigence (A5 Q4) | Implémentation | Preuve / test | Verdict |
|---|---|---|---|
| Dépassement + froid **souhaitable** → NOT_COMPLIANT qui **bloque le verdict overall** (pas simple alerte) | `_evaluate_electrical_power` → `category=="desirable"` → `verdict_status="NOT_COMPLIANT"` + alerte HIGH ; gate L.281 `elif electrical_power_not_compliant` → `NOT_COMPLIANT` | `test_electrical_power_exceeds_with_desirable_cooling_is_not_compliant` ; `test_electrical_power_exceedance_gates_the_verdict`. Sonde adverse : NC bloque **même quand la comparaison globale est absente** (`NC + no comparison -> NOT_COMPLIANT`). Ordre du gate correct (avant `not comparison_available`). | **CONFIRMÉ** |
| Dépassement + catégorie **inconnue** ne devient **jamais COMPLIANT** | `category` non reconnu → `NOT_DETERMINED` ; gate L.298 → `NOT_DETERMINED` | `test_electrical_power_exceeds_unknown_category_is_not_determined` ; sonde `ND electrical -> NOT_DETERMINED`. Jamais COMPLIANT. | **CONFIRMÉ** |
| Exigence **autonome** : satisfaire §7.2.5.2 ne masque pas §7.2.4 | Le gate évalue `electrical_power_not_compliant` indépendamment de `comparison_available` | Sonde `NC + no comparison` confirme l'autonomie. | **CONFIRMÉ** |

## 3. Pas de faux-échec (fail-closed sans sur-blocage)

| Exigence (A5 Q4) | Implémentation | Preuve / test | Verdict |
|---|---|---|---|
| Puissance simplement **non fournie / non relue** → NOT_DETERMINED (jamais NOT_COMPLIANT) | Record non `accepted` + `has_fluid_installation` → `NOT_DETERMINED` (L.1452-1455) | Couvert par branche ; sonde normalize : tout champ manquant → `accepted=False`. Aucune branche ne produit NOT_COMPLIANT sans record accepté. | **CONFIRMÉ** |
| Dépassement + froid **nécessaire** → OK (§7.2.4 ne restreint pas la puissance) | `category=="necessary"` → `verdict_status="OK"` | `test_electrical_power_exceeds_with_necessary_cooling_is_not_blocked`. | **CONFIRMÉ** |
| Bâtiment **sans installation CVC** → NOT_APPLICABLE (non bloqué) | Pas de record + `has_fluid_installation=False` → `NOT_APPLICABLE` ; gate : NA sans effet | `test_electrical_power_no_installation_is_not_applicable` ; sonde `NA electrical -> COMPLIANT`. | **CONFIRMÉ** |
| Puissance ≤ seuil → OK | `value <= limit` → `OK` | `test_electrical_power_within_the_724_limit_passes` (10 ≤ 12). | **CONFIRMÉ** |

## 4. Fail-closed evidence (acceptation CSV relecteur)

| Exigence | Implémentation (`_normalize_electrical_power_record`) | Preuve / test (sonde adverse) | Verdict |
|---|---|---|---|
| Accepté **seulement** avec statut bâtiment + puissance numérique + reviewer + date + source + statut relu + projet | `accepted = review_status ∈ ACCEPTED & project_id & building_status_key & numeric power ≠ None & reviewer & review_date & (source_document ∨ source_reference)` | Sondes : full→True ; no reviewer→False ; no date→False ; no source→False ; source_reference seule→True ; building_status vide/inconnu→False ; power vide/non-numérique→False ; review_status pending→False ; project vide→False. | **CONFIRMÉ** |
| Statut bâtiment mappé fail-safe | `new/neuf/…`→new ; `existant/renovated/rénové/sanierung/…`→existing ; sinon `""` (rejet) | Sonde : variantes existant→`existing` ; `mixed`→`""`→rejet. | **CONFIRMÉ** |
| Catégorie froid indéterminée par défaut | `cooling_category` non reconnu → `cooling_category_key=""` → NOT_DETERMINED en aval | Cohérent avec branche « unknown ». | **CONFIRMÉ** |

## 5. Réserves / points à corriger (n'invalident pas la logique de porte)

- **R1 — Pas de contrôle de signe.** Une puissance négative (`-5`) est acceptée
  (`numeric=-5.0`, `accepted=True`) et donne `meets_limit=True` → OK. Valeur
  physiquement absurde non rejetée. Impact faible (donnée relecteur signée), mais
  aucun garde-fou `value >= 0`. **À CORRIGER (durcissement mineur).**
- **R2 — Pas de contrôle d'unité.** `unit="kW"` est stocké mais **ignoré** ; la
  valeur numérique est comparée au seuil W/m² telle quelle. Si le relecteur
  fournit une grandeur dans une autre unité, la comparaison est silencieusement
  fausse. **À CORRIGER (valider `unit ∈ {W/m2,...}` ou rejeter).**
- **R3 — `conditioned_area_m2` non réconcilié.** La cohérence entre W/m² fourni et
  (puissance / surface conditionnée) n'est pas re-vérifiée ; on fait confiance au
  W/m² relu. Réserve documentée (A5 §Zones d'incertitude, méthode de relevé).
- **R4 — Détection `has_fluid_installation` heuristique.** Fondée sur
  `hvac_systems / mechanical_ventilation_present / ventilation_rate` par pièce.
  Si le modèle a du froid mais aucun de ces attributs et aucune evidence, le
  résultat est NOT_APPLICABLE (non bloquant). Conservateur mais dépend de la
  fidélité de l'extraction VE. Réserve, pas un faux-pass du gate (le gate ne
  s'appuie que sur le `verdict_status`).

## 6. Séparation dur/pur

| Contrôle | Résultat |
|---|---|
| `engine/` n'importe jamais `iesve` | **CONFIRMÉ** — aucun `import iesve` réel (uniquement commentaires + tests de pureté). |
| Modules §7.2.4 (`sia380_checker`, `compliance_verdict`, `evidence_manager`) `iesve`-free | **CONFIRMÉ** — grep = aucune occurrence. |

---

## Décision de signature

**SIGNÉ — pour la logique de porte §7.2.4 (structure décisionnelle et
fail-closed).** Les six exigences de l'arbre A5 (NOT_APPLICABLE / NOT_DETERMINED /
OK / NOT_COMPLIANT-souhaitable / OK-nécessaire / NOT_DETERMINED-inconnu), le
caractère bloquant et autonome du NOT_COMPLIANT, la retombée NOT_DETERMINED pour
preuve manquante, et l'acceptation fail-closed du CSV relecteur sont **vérifiés,
reproduits et conformes** au ruling A5 et au texte §7.2.4.2 (PDF p.32). Seuils
7/12 W/m² sourcés et exacts.

**Conditions restantes (héritées, non levables par cet audit) :**
1. **Classification froid nécessaire/souhaitable** repose sur une saisie relecteur
   dont la *justification* normative dépend de **SIA 180 / SIA 2024 / SIA 2056**,
   **absents de `/refs`** (A5 §Zones d'incertitude). Le code traite correctement
   la catégorie fournie, mais ne peut pas *vérifier* le classement lui-même.
   → renvoi `norm-analyst` / `reference-data-engineer` (figer la source de
   classification).
2. **Appariement cas d'application ↔ seuil 7 vs 12** dépend de **SIA 380
   (faîtière), absente de `/refs`** ([TO VERIFY] A5 Q3). Le statut new/existing
   est saisi par le relecteur, non dérivé de la norme faîtière.
3. **Durcissements R1/R2** (signe, unité) recommandés avant usage commercial —
   `validation-engine-engineer`. Non bloquants pour la structure de porte.

**AUDITÉ OK (structure de porte §7.2.4) — 2026-08-21.** La signature ne porte
**pas** sur la justification normative de la classification du refroidissement ni
sur l'appariement de seuil, tous deux suspendus aux sources SIA absentes ci-dessus.
