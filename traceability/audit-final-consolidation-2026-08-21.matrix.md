# Matrice de traçabilité — AUDIT FINAL CONSOLIDÉ (lot evidence-hardening)

Branche : `sia4010-evidence-hardening-20260812`
Auditeur : qa-auditor (indépendant, **lecture seule** du code de production ; aucune modification)
Date : 2026-08-21
Périmètre : cohérence d'ensemble de la chaîne conformité client SIA 380/2 (verdict,
indicateurs, ingestion d'évidence, diagnostic vs gate, données de référence figées,
réserves normatives, séparation dur/pur) + décision de signature globale.

Audits partiels déjà signés et ré-confirmés ici :
- `traceability/audit-lot-A1-A4-verification-2026-08-21.matrix.md` (indicateurs + verdict A1-A4) — **SIGNÉ**
- `traceability/electrical-power-7.2.4.matrix.md` (§7.2.4) — **SIGNÉ (structure de porte)**

## Suite de tests exécutée

- Commande : `python -m pytest tests/ -q`
- Résultat : **exit code 0, 0 échec**. Tests collectés : **1356** (`pytest --collect-only`),
  plus subtests. Sortie brute : task `btrmp74ll`.
- Seuls avertissements : `openpyxl` Data-Validation extension non supportée (3 fichiers
  workbook de test) — non bloquant, sans rapport avec le moteur de conformité.

---

## 1. Verdict (`swiss_sia/compliance_verdict.py`)

| # | Exigence | file:line | Preuve | Verdict |
|---|---|---|---|---|
| V1 | Porte décisive §7.2.5.2 : COMPLIANT seulement si comparaison relue satisfaite | `compliance_verdict.py:286-308` (`not comparison_available` → NOT_DETERMINED ; sinon COMPLIANT) | Signé lot A1-A4 ; ré-lu. Sans comparaison relue ⇒ NOT_DETERMINED, jamais COMPLIANT silencieux. | **CONFIRMÉ** |
| V2 | Exigences autonomes §7.1 (ventilation, contrôle protection solaire, confort d'été) sont des gates, pas des réserves | `:288-297` (ventilation, solar-protection) ; `:50,155-156` (dynamic → blocking si HIGH déterminée) | Signé A3/A4. Surchauffe DÉTERMINÉE → `blocking_total` évalué (`:274`) AVANT la porte ; non vérifiable → `indeterminate` → NOT_DETERMINED. | **CONFIRMÉ** |
| V3 | §7.2.4 porte conditionnelle autonome | `:249-258, 281-285, 298-302` | Signé §7.2.4. NC-souhaitable bloque (`:281`, avant `not comparison_available`) ; inconnu/manquant → NOT_DETERMINED. | **CONFIRMÉ** |
| V4 | Aucun faux-pass : exigence autonome non vérifiée ⇒ jamais COMPLIANT | ordre des gates `:272-308` | Chaque gate autonome force NOT_DETERMINED/NOT_COMPLIANT avant la branche COMPLIANT finale. | **CONFIRMÉ** |
| V5 | Aucun faux-échec : non vérifiable ⇒ NOT_DETERMINED, jamais NOT_COMPLIANT | `_count_by_category` `:137-161` (marqueurs can't-check → `indeterminate` même à CRITICAL) | Signé A1-A4 (`test_uncheckable_domain_is_not_reported_as_non_compliant`). | **CONFIRMÉ** |
| V6 | Ordre des gates : déterminé (blocking + contradiction + §7.2.4 NC) AVANT « comparaison manquante » AVANT gates d'évidence incomplète | `:272-308` | Un vrai échec prime sur une porte manquante ; une porte manquante prime sur une réserve. Cohérent. | **CONFIRMÉ** |

## 2. Indicateurs (`health_score.py`, `excel_report.py`, `app.py`)

| # | Exigence | file:line | Preuve | Verdict |
|---|---|---|---|---|
| I1 | Le nombre = diagnostic de couverture (≠ conformité) ; le verdict est en tête | A1 (`app.py`, `excel_report.py`), signé A1-A4 (lignes 8-9 de la matrice A1-A4) | Ré-confirmé : score client omis (`include_sia4010=False`), carte menée par le VERDICT. | **CONFIRMÉ** |
| I2 | NOT_CHECKABLE plafonne le score de catégorie | `sia380_checker._calculate_category_score` (plafond `INCOMPLETE_EVIDENCE_SCORE_CEILING=60`) ; `health_score.py:130-148` marqueurs missing | Signé A2 (`test_indeterminate_alert_caps_the_category_below_the_pass_band`). Marqueurs score ≡ marqueurs verdict. | **CONFIRMÉ** |
| I3 | Score de conformité pondéré n'inclut que catégories implémentées | `health_score.py:60-73` (envelope/openings/ventilation/gains/hvac) | Cohérent ; diagnostics (EER/SEER/SCoP) hors pondération. | **CONFIRMÉ** |

## 3. Ingestion d'évidence (fail-closed)

| # | Exigence | file:line | Preuve | Verdict |
|---|---|---|---|---|
| E1 | Ponts thermiques : lecture VE directe H_tb (W/K) | `sia380_checker.py:330-339` (`_read_ve_thermal_bridges`, `find_accepted_thermal_bridges`) | Lecture VE ψ/χ→H_tb ; CSV relu en repli. Conforme mémoire projet. | **CONFIRMÉ** |
| E2 | SEER froid déclaré (Voie A) comparé proprement à la bande SIA table 5 | `sia380_checker.py:90-105` ; réf `sn-en-14825-2018.cooling-seer.json` | SEER déclaré = EN 14825 par construction ; réserve levée pour le froid. | **CONFIRMÉ** |
| E3 | §7.2.4 acceptation fail-closed (reviewer+date+source+quantum) | `evidence_manager.py:584-593` | Accepté seulement si review_status∈ACCEPTED ∧ project ∧ building_status_key ∧ power valide ∧ unité W/m² ∧ reviewer ∧ date ∧ source. | **CONFIRMÉ** |
| E4 | §7.2.4 garde R1 : puissance négative rejetée | `evidence_manager.py:576-577` (`power_is_valid = power is not None and power >= 0.0`) | **RÉSERVE R1 CORRIGÉE** (commit 294739a). Vérifié sur disque. | **CONFIRMÉ (corrigé)** |
| E5 | §7.2.4 garde R2 : unité ≠ W/m² rejetée | `evidence_manager.py:578-583` (`unit_is_w_m2` ; rejette kW/mW) | **RÉSERVE R2 CORRIGÉE** (commit 294739a). Unité vide acceptée (colonne nommée `_w_m2`). | **CONFIRMÉ (corrigé)** |
| E6 | Rien inféré d'un champ vide ; jamais un PASS silencieux | `_normalize_electrical_power_record` `:528-594`, `_normalize_solar_protection_record` `:597+` | Tout champ manquant → `accepted=False`. Catégorie froid inconnue → `""` → NOT_DETERMINED. | **CONFIRMÉ** |
| E7 | Checker expose un `verdict_status` unique lu par le gate | `sia380_checker.py:1450-1466, 476` | Le gate `compliance_verdict.py:254-258` lit `electrical_power.verdict_status`. Chaîne complète. | **CONFIRMÉ** |

## 4. Diagnostic vs gate (SIA 380/2 note ⁶)

| # | Exigence | file:line | Preuve | Verdict |
|---|---|---|---|---|
| D1 | EER/SEER/SCoP = entrées du projet de référence, non bloquantes | `compliance_criteria.py:83-102` ; `compliance_verdict.py:11-14, 259-268` (diagnostics = réserves dans `outstanding`) | SCoP `[TO VERIFY]` indicatif ; ne dégrade pas le verdict. Commit a9ca3e4 (note ⁶). | **CONFIRMÉ** |
| D2 | Décisif = §7.2.5.2 + §7.1 + §7.2.4 uniquement | `compliance_verdict.py:272-308` | Seuls ces gates changent le statut ; le reste va en `outstanding`. | **CONFIRMÉ** |

## 5. Données de référence figées (`refs/reference-data/`)

| # | Fichier | Source / cross-check | Statut | Verdict |
|---|---|---|---|---|
| R-SEER | `sn-en-14825-2018.cooling-seer.json` | Captures document publié (utilisateur, 2026-08-20) ; lié à SIA 380/2 table 5 p.38 ; script `build_sn_en_14825_seer.py` | FIGÉ (froid) ; SCoP chaud NON figé | **CONFIRMÉ (froid)** |
| R-COMFORT | `sia-180-2014.comfort.json` | Fig.3 fournie par Yiqiao Yang 2026-08-20 ; points de rupture recalculés depuis intersections + confrontés à la figure publiée | FIGÉ sous réserve des rectificatifs ; Fig.3 désormais présente (n'est plus `[À VÉRIFIER]`) | **CONFIRMÉ** |
| R-BLINDS | `sia-387-4-2017.blinds.json` | SIA 387/4:2023 tableau 9 + éq. 18-20, capture Yiqiao Yang 2026-08-21 ; réserve d'édition levée | FIGÉ (protection solaire) ; contenu éclairage NON figé | **CONFIRMÉ (protection solaire)** |

Les trois fichiers portent provenance, script générateur et lien SIA. Aucune valeur inventée constatée.

## 6. Réserves normatives (`docs/project/RESERVES_NORMATIVES.md`)

| # | Exigence | Preuve | Verdict |
|---|---|---|---|
| N1 | Politique « validé sous réserve, jamais un PASS » fidèlement reflétée par le code | SCoP → DIAGNOSTIC/`[TO VERIFY]` non bloquant (`compliance_criteria.py:96-102`) ; éclairage → PARTIAL non clôturé ; §7.2.4 catégorie inconnue → NOT_DETERMINED ; SEER froid → réserve levée | Registre ↔ code cohérents ligne à ligne. | **CONFIRMÉ** |

## 7. Séparation dur/pur

| # | Contrôle | Preuve | Verdict |
|---|---|---|---|
| S1 | `engine/` n'importe jamais `iesve` | `grep -rn "import iesve\|from iesve" engine/` → uniquement commentaires + tests de pureté (`test_engine_purity.py`) ; aucun import réel | `engine/` pur. | **CONFIRMÉ** |
| S2 | Modules §7.2.4/verdict/évidence `iesve`-free | grep = 0 occurrence dans `compliance_verdict.py`, `evidence_manager.py`, `sia380_checker.py` | Conforme. | **CONFIRMÉ** |

---

## Fichiers non committés d'une session parallèle (signalés, HORS périmètre client SIA 380/2)

Côté SIA 4010 (campagne de validation / template ApacheSim), sans effet sur la
chaîne conformité client SIA 380/2 auditée ci-dessus. Ils passent la suite complète
(1356 tests, exit 0) :
- `swiss_sia/reference_model/sia4010/template_apachesim.py`, `validation_campaign.py`
  (nouveaux) — ne contiennent pas d'`import iesve` au niveau module.
- `Run_VE_SIA4010_*.py` (3), `docs/project/SIA4010_CAMPAGNE_VALIDATION_ACCELEREE.md`,
  `tests/test_sia4010_*` (2 nouveaux), et modifs `reference_model/sia4010/*`.

Ces éléments relèvent de la boucle SIA 4010 (attestation sous-commission requise) et
ne sont PAS couverts par la présente signature.

---

## Défauts mineurs hérités (non bloquants, déjà listés par les audits partiels)

1. i18n libellé domaine `dynamic` non localisé dans le rapport **HTML** (`compliance_report_html._DOMAIN_LABELS`) — PDF client non affecté. Défaut de localisation, pas de blanc silencieux.
2. Frontière `iesve` dans `swiss_sia/` : `app.py`, `evidence_bootstrap.py`, `simulation_results.py` importent `iesve` (imports gardés runtime), au-delà de la frontière annoncée. Pré-existant, suivi architectural.
3. §7.2.4 R3 (réconciliation `conditioned_area_m2`) et R4 (heuristique `has_fluid_installation`) : réserves documentées, pas des faux-pass du gate.
4. Test négatif « aucun store ⇒ pas de gate solaire » : garde correcte par lecture, test adverse dédié encore souhaitable.

---

## DÉCISION DE SIGNATURE GLOBALE

**SIGNÉ SOUS CONDITIONS** — la chaîne logique de conformité client SIA 380/2
(verdict, indicateurs, ingestion d'évidence fail-closed, diagnostic vs gate,
séparation dur/pur) est **cohérente d'ensemble, sans faux-pass ni faux-échec
constaté**, la suite complète passe (1356 tests, 0 échec), les réserves §7.2.4 R1
(puissance négative) et R2 (unité ≠ W/m²) sont **effectivement corrigées** sur disque
(`evidence_manager.py:576-583`, commit 294739a), et les données de référence figées
sont sourcées avec cross-check.

La signature est **conditionnelle** car elle repose sur des **décisions produit /
rulings norm-analyst (A4, A5)**, PAS sur des valeurs de référence numériques figées
pour les gates de politique §7.1/§7.2.4/§7.2.5.2 (aucune réf. externe à reproduire
pour ces règles de structure), et parce que des réserves normatives subsistent.

### Réserves restantes et caractère bloquant

| Réserve | Source manquante | Effet code | Bloquant pour usage commercial ? |
|---|---|---|---|
| **SN EN 14825 chaud (SCoP)** | Partie chaud EN 14825 | SCoP `[TO VERIFY]` indicatif, non bloquant (note ⁶) | **NON bloquant** — diagnostic, pas un gate |
| **Contenu éclairage SIA 387/4** | Partie éclairage (contrôle présence/lumière) | Verdict éclairage PARTIAL non clôturé | **NON bloquant** pour le verdict global (§7.2.5.2 décisif) ; à compléter |
| **SIA 180/2024/2056 (classification froid §7.2.4)** | Règle nécessaire/souhaitable | Catégorie relue par le relecteur ; inconnue → NOT_DETERMINED | **NON bloquant** structurellement, mais la *justification* de la classification n'est pas vérifiable par l'outil → renvoi norm-analyst/reference-data-engineer |
| **SIA 380 faîtière (appariement seuil 7/12)** | Correspondance cas ↔ seuil | Seuils appliqués sous réserve `[À VÉRIFIER]` selon statut relu | **NON bloquant** structurellement ; réserve documentée |
| **SIA 180 T° opérative exacte (confort d'été)** | Définition T° opérative / fenêtre θrm | Calcul depuis Fig.3/4 figées | **NON bloquant** ; bloque si surchauffe avérée, sinon réserve |

Aucune de ces réserves n'est bloquante pour la **structure logique** signée ; toutes
restent **explicitement réservées** dans les livrables (`outstanding`, caveats
`[TO VERIFY]`) et **ne peuvent jamais** être converties en `PASS` sans le document
ou une attestation relecteur.

### Portée de la signature

Cette signature couvre **uniquement** la cohérence verdict/score/indicateur, les
gates §7.1 / §7.2.4 / §7.2.5.2, l'ingestion d'évidence fail-closed (incl. gardes R1/R2
corrigées) et la séparation dur/pur. Elle **ne vaut PAS** :
- revendication de conformité SIA 380/2 (requiert la comparaison §7.2.5.2 relue par
  projet réel + les réserves normatives ci-dessus levées) ;
- validation SIA 4010 (requiert résultats de tests officiels + attestation
  sous-commission ; les fichiers de campagne non committés sont hors périmètre).

**AUDITÉ OK (structure de conformité client SIA 380/2, sous conditions ci-dessus)
— 2026-08-21.**
