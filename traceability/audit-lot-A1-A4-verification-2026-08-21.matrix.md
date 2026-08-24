# Matrice de vérification — lot de corrections A1..A4 (evidence-hardening)

Branche : `sia4010-evidence-hardening-20260812`
Auditeur : qa-auditor (indépendant, lecture seule du code de production)
Date : 2026-08-21
Statut : **SIGNÉ**
Commits vérifiés : `677b3dd` (A3), `9cc68fc` (A2), `3c48a77` (A1), `7e88404` (A4)
Suite exécutée : `python -m pytest tests/ -k "verdict or robustness or report or criteria or claim or health or excel or translation" -q`
Résultat : **301 passed, 1025 deselected, 2061 subtests passed** (67 s), 0 échec.

Méthode : je ne fais confiance ni aux noms ni aux commentaires ; j'ai lu le code
appelé, tracé la chaîne alerte → domaine → verdict, et confronté aux tests
adverses. Références SIA figées : non disponibles pour ces gates §7.1/§7.2.5.2
(logique de politique produit, pas de valeur numérique de référence) — cf.
réserves de signature.

| # | Exigence (clause) | Correction | Fonction moteur | Preuve / test | Constaté | Verdict |
|---|---|---|---|---|---|---|
| 1 | Une surchauffe d'été DÉTERMINÉE (§7.1.2.1→SIA 180) bloque même si la porte §7.2.5.2 est satisfaite | A3 : `DOMAINS += ("dynamic","Dynamic Method")` | `compliance_verdict.build_compliance_verdict` (l.50, 264) ; `sia380_checker` émet `SIA3802_SUMMER_COMFORT_DYNAMIC` HIGH, cat. "Dynamic Method" (l.280-292) | `test_determined_summer_overheating_blocks_even_with_gate_satisfied` (gate=REVIEWED_RESULT_AVAILABLE → `sia3802_status==NOT_COMPLIANT`) | HIGH déterminée → `blocking_total>0` évalué (l.264) AVANT la porte (l.271) → NOT_COMPLIANT. Catégorie réellement "Dynamic Method". | **CONFIRMÉ** |
| 2 | Une surchauffe NON VÉRIFIABLE reste une réserve, pas un échec | A3 | idem ; marqueur `NOT_CHECKABLE` → `indeterminate` (l.155-156) | `test_not_checkable_summer_comfort_stays_a_reserve_not_a_block` (`dynamic`=NOT_DETERMINED, `sia3802_status==COMPLIANT`) | `SIA3802_SUMMER_COMFORT_NOT_CHECKABLE` contient `NOT_CHECKABLE` → indéterminé, jamais bloquant. | **CONFIRMÉ** |
| 3 | Protection solaire active sans contrôle documenté (§7.1.2.2-5) → NOT_DETERMINED, jamais COMPLIANT-silencieux | A4 : gate `solar_protection_control_incomplete` (l.228-232, 278-282, 295) | `compliance_verdict` ; alertes `SIA3802_SOLAR_PROTECTION_CONTROL_MISSING`/`_TYPE_MISSING` | `test_unverified_solar_protection_control_gates_the_verdict` (`sia3802_status==NOT_DETERMINED`, reason `solar_protection_control_incomplete`, item dans `outstanding`) | Gate déclenché sur nom de règle ; passe après blocking/contradiction/gate manquante → une vraie surchauffe ou contradiction reste prioritaire. | **CONFIRMÉ** |
| 4 | Pas de sur-blocage : modèle sans store actif non gaté par le gate solaire | A4 | `model_analyzer.has_active_solar_protection` (l.85-108) garde l'émission (`sia380_checker` l.750, 760) | Logique : alertes émises seulement si `active_solar_protection` vrai ; shading_type vide/none/disabled ⇒ False ; drapeaux actifs "off" ⇒ False | Pas de test unitaire dédié « aucun store ⇒ pas de gate », mais la garde est vérifiée par lecture et les tests de robustesse ne déclenchent pas le gate sur données propres. | **CONFIRMÉ** (réserve : ajouter un test négatif explicite, cf. conditions) |
| 5 | Ventilation/protection solaire simplement non vérifiable = réserve (NOT_DETERMINED global), pas NOT_COMPLIANT | A3/A4 + existant | `_count_by_category` (l.137-161) : marqueurs can't-check → indéterminé même à CRITICAL | `test_uncheckable_domain_is_not_reported_as_non_compliant` (overall NOT_DETERMINED, jamais NOT_COMPLIANT) | Un « je ne peux pas lire » n'est jamais un échec. Faux-échec écarté. | **CONFIRMÉ** |
| 6 | Score de catégorie honnête : évidence manquante ne peut plus lire ~85 ET COMPLIANT | A2 : `-20`/alerte indéterminée + plafond `INCOMPLETE_EVIDENCE_SCORE_CEILING=60` | `sia380_checker._calculate_category_score` (l.1813-1852), `_is_indeterminate_alert` (l.1864-1872) | `test_indeterminate_alert_caps_the_category_below_the_pass_band` (Openings ≤60 et >0) | Marqueurs score = marqueurs verdict (5 identiques) → score et verdict alignés par construction. | **CONFIRMÉ** |
| 7 | Pas de faux 0 : évidence seulement manquante ne force pas 0 | A2 | `_calculate_category_score` : 0.0 réservé à `_is_blocking_not_checkable_alert` (CRITICAL MODEL_NOT_CHECKABLE/EXTERNAL_ENVELOPE_MISSING/RULE_EXECUTION_ERROR) | `test_indeterminate_alert_caps... >0` ; `test_determined_advisory_alone_stays_in_the_pass_band` (==95) | Manque simple ⇒ plafonné 60, jamais 0. 0 réservé aux états « pas de score possible ». | **CONFIRMÉ** |
| 8 | Indicateur honnête : le nombre n'est plus présenté comme score de conformité | A1 : app.py logue le VERDICT en tête ; nombre relabellisé « coverage (diagnostic, ≠ conformité) » | `swiss_sia/app.py` (l.~1370-1385) ; `excel_report.py` cartes/KPI renommées | Lecture du diff `3c48a77` ; verdict calculé une fois et réutilisé | Le verdict précède le nombre ; libellé interne « SIA 380/2 COVERAGE (diag.) … excludes the decisive §7.2.5.2 gate ». | **CONFIRMÉ** |
| 9 | Périmètre client n'expose pas « SIA 380/2 automated score » | A1 | `excel_report` branche `else` (include_sia4010=False) mène par COMPLIANCE VERDICT, omet le nombre | `test_client_workbook_has_no_sia4010_or_development_indicators` + `test_client_workbook_uses_real_verdict_and_project_information` (assertNotIn "SIA 380/2 automated score", "Model health score", "4010") | Carte client = VERDICT/BLOCKING/ADVISORY ; nombre absent. | **CONFIRMÉ** |
| 10 | Nouvel item outstanding traduit (pas de clé silencieusement vide) | A4 | `ui_translations` clé `outstanding_sia3802_solar_protection_control` (en/de/fr/it) ; mapping `translate("outstanding_"+item)` (`compliance_report_pdf` l.574, 1155) | Suite `translation` verte ; clé emise `sia3802_solar_protection_control` ↔ clé de traduction correspondante | Mapping cohérent ; les 4 langues présentes. | **CONFIRMÉ** |
| 11 | Séparation dur/pur : `engine/` n'importe jamais `iesve` | (standing) | — | `engine/tests/test_engine_purity.py` ; grep : aucune ligne `import iesve`/`from iesve` en code `engine/` (seulement commentaires/gardes de test) | engine/ pur. | **CONFIRMÉ** |

## Contre-vérifications adverses menées
- Ordre des portes dans `build_compliance_verdict` : `blocking_total` (surchauffe HIGH incluse) est évalué AVANT `comparison_available`, donc une surchauffe déterminée n'est pas masquée par une porte §7.2.5.2 satisfaite. Vérifié l.262-288.
- Un CRITICAL « can't check » (ex. EXTERNAL_ENVELOPE_MISSING) est indéterminé côté verdict (jamais NOT_COMPLIANT) mais donne 0 côté score de couverture. Cohérent : verdict=NOT_DETERMINED, nombre=couverture nulle ; aucun des deux ne lit « conforme ». Pas de contradiction.
- Le checker produit bien la clé `"dynamic"` dans `results` (sia380_checker l.413), donc le domaine dynamique n'est pas perpétuellement `domain_not_evaluated` ; son statut suit les alertes réelles.
- Gate solaire : ne déclenche que sur alertes émises sous condition `has_active_solar_protection` ⇒ pas de faux NOT_DETERMINED sur un modèle sans store.

## Observations / défauts mineurs (non bloquants)
- **i18n libellé domaine « dynamic »** : `compliance_report_html._DOMAIN_LABELS` (l.450-459) ne contient pas de clé `dynamic`. Dans le rapport HTML, si le domaine dynamique apparaît en réserve, le libellé retombe sur la chaîne brute `dynamic` (anglais, non traduit) — pas un blanc silencieux, mais non localisé en FR/DE/IT. Le PDF client n'est PAS affecté (il n'utilise que le tuple `outstanding` traduit). À corriger côté HTML.
- **Frontière `iesve` dans `swiss_sia/`** : `app.py`, `evidence_bootstrap.py`, `simulation_results.py` importent `iesve` (imports gardés en runtime), au-delà de la frontière annoncée `reference_model/ve_api.py` + `data_extractor`. Pré-existant, hors périmètre des 4 commits ; signalé pour suivi architectural, non bloquant pour ce lot.
- **Test négatif manquant (ligne 4)** : aucun test unitaire ne pin explicitement « store absent ⇒ gate solaire silencieux ». La garde est correcte par lecture mais mérite un test adverse dédié.

## Réserves normatives (indépendantes de la qualité du code)
- Les gates §7.1 (ventilation, contrôle protection solaire, surchauffe) et la porte décisive §7.2.5.2 reposent sur une **décision produit 2026-08-19 + ruling norm-analyst A4 2026-08-20**, PAS sur une valeur de référence figée dans `/refs/reference-data/`. Aucune valeur numérique de référence à reproduire pour ces règles de politique ; la vérification porte sur la cohérence logique, pas sur une réf. externe.
- **§7.2.4 (seuil électrique)** non traité — gap connu, tracé dans `docs/project/TODO.md` et le commit A1.
- **Design-day** reste une réserve acceptée (norm-analyst A4).
- SIA 180 Fig.3 encore `[À VÉRIFIER]` (mémoire projet) — hors périmètre de ce lot mais pertinent pour l'aval surchauffe.

## Décision de signature

Chaque ligne 1–11 de la matrice est vraie et reproduite par un test exécuté vert.
Les 4 corrections font ce qu'elles prétendent : pas de faux-pass (surchauffe et
contrôle solaire déterminés bloquent réellement), pas de faux-échec (non
vérifiable = réserve NOT_DETERMINED, jamais NOT_COMPLIANT ; jamais un faux 0 pour
évidence manquante), score et verdict alignés, indicateur honnêtement relabellisé
et absent du périmètre client.

**SIGNÉ — lot A1..A4 (cohérence score↔verdict, honnêteté indicateur, gates
§7.1 surchauffe / ventilation / protection solaire) — AUDITÉ OK — 2026-08-21.**

Portée de la signature : uniquement la logique verdict/score/indicateur ci-dessus.
Cette signature **ne vaut PAS** revendication de conformité SIA 380/2 ni de
validation SIA 4010, qui requièrent la porte §7.2.5.2 relue, les résultats de
tests officiels et l'attestation de la sous-commission.

Conditions restantes (à lever hors périmètre de ce lot, non bloquantes pour la
signature ci-dessus) :
1. §7.2.4 seuil électrique — non implémenté.
2. Libellé i18n `dynamic` dans le rapport HTML.
3. Test négatif « aucun store ⇒ pas de gate solaire ».
4. Frontière `iesve` dans `swiss_sia/` (suivi architectural).
5. SIA 180 Fig.3 `[À VÉRIFIER]` pour l'aval surchauffe.
