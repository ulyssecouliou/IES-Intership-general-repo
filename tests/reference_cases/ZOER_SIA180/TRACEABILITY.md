# Matrice de traçabilité — Cas de référence SIA 180 (dossier ZOER)

Chaque ligne relie : **critère** → **source normative** → **valeur attendue** →
**provenance de la valeur attendue** → **statut** → **test**.

Oracle (vérité-terrain) : `32_ZOER_Simulationsbericht_20251208.pdf`
(§3.1, §3.2, §3.3, Abbildung 3, Abbildung 4 ; verdicts pp. 4-5).

Légende statut : **VÉRIFIÉ** = confronté à une source publiée / dessin vectoriel ;
**ORACLE** = transcrit du rapport client (cible de réplication) ; **`[À VÉRIFIER]`**
= reste à confronter à la norme publiée.

---

## A. Grandeurs et algorithme

| # | Critère | Source normative | Valeur / règle attendue | Provenance | Statut | Test |
|---|---------|------------------|-------------------------|------------|--------|------|
| A1 | Grandeur évaluée | SIA 180:2014, empfundene (operative) Temperatur | Dry resultant temperature (°C), sortie `.aps` | Rapport §3.1 ; mapping col D/F validé | VÉRIFIÉ | `test_loader_header_mapping_all_six_files` |
| A2 | Moyenne glissante θrm | Rapport §3.1 : `θrm = (1/48)·Σ_{H-48}^{H} θe` | Moyenne arithmétique simple sur 48 h (PAS l'exponentielle EN 15251) | Rapport §3.1 (formule imprimée) | ORACLE | `test_theta_rm_known_sequence` |
| A3 | Convention de bord θrm | — (non précisé par le rapport) | Fenêtre tronquée sur heures disponibles | Choix documenté ; robustesse vérifiée (48/49 termes, ±heure courante) | `[À VÉRIFIER]` (sans effet sur verdict) | `test_c1_verdicts_all_zones`, `test_c2_verdicts_all_zones` |
| A4 | Appariement horaire | — | Par (date, heure), jamais par index | Schéma relevé ; décalages HH:30/HH:00 et jour-de-semaine (C2) résolus | VÉRIFIÉ | `test_c2_verdicts_all_zones` (garde faux-PASS : `skipped_no_theta_rm == 0`) |
| A5 | Seuil d'occupation C2 | Rapport : « Zeiten mit Personenbelegung » | People gain (kW) **> 0** (strict) | Données : aucune valeur dans (0 ; 0,05] kW ; min non nul = 0,86 kW | VÉRIFIÉ | `test_people_gain_occupancy_gap` |

## B. Courbes SIA 180

| # | Critère | Source normative | Valeur attendue | Provenance | Statut | Test |
|---|---------|------------------|-----------------|------------|--------|------|
| B1 | Fig.3 courbe SUP (C1) | SIA 180 Fig.3 (Anhang C1) | `max(25 ; 0,33·θrm + 21,8)` | Étiquette imprimée sur Abbildung 3 du rapport | ORACLE ; `[À VÉRIFIER]` vs SIA 180:2014 Fig.3 publiée (plateau 25, domaine θrm) | `test_fig3_upper_plateau_and_slope` |
| B2 | Fig.3 courbe INF (C1) | SIA 180 Fig.3 (Anhang C1) | `0,33·θrm + 14,3` | Étiquette imprimée sur Abbildung 3 | ORACLE ; `[À VÉRIFIER]` vs norme publiée | `test_fig3_lower_line` |
| B3 | Fig.4 courbe SUP (C2) | SIA 180:2014 Fig.4 (§2.3.2) = SIA 380/2:2022 fig.1 (identité §5.2.2.5) | Sommets (10;24,5)(12;24,5)(17,5;26,5)(25;26,5) | Dessin vectoriel `refs/reference-data/sia-380-2-2022.figure1.json`, résidu < 0,001 °C, recoupé 8/8 contre capture SIA 180 Fig.4 | **VÉRIFIÉ** | `test_fig4_vertices_and_interpolation`, `test_fig4_vertices_match_frozen_reference_json` |
| B4 | Fig.4 courbe INF (C2) | idem B3 | Sommets (10;20,5)(19;20,5)(23,5;22,0)(25;22,0) | idem B3 | **VÉRIFIÉ** | idem B3 |
| B5 | Extrapolation hors domaine Fig.4 | — | Prolongement plat des plateaux | Choix documenté | `[À VÉRIFIER]` (sans effet) | `test_fig4_vertices_and_interpolation` (clamp) |

## C. Critères de verdict et oracle

| # | Critère | Source normative | Valeur attendue | Provenance | Statut | Test |
|---|---------|------------------|-----------------|------------|--------|------|
| C1a | Verdict C1 (règle) | Rapport §3.2 | PASS si `n_above_upper == 0` ET `n_below_lower == 0`, sur toute la période 24/7 | Rapport §3.2 | ORACLE | `test_c1_verdicts_all_zones` |
| C1b | Verdict C1 (oracle, 3 zones) | Rapport pp. 4, §7 brief | **PASS** ; Zone 1/2/3 : 0 h au-dessus, 0 h en dessous ; max opérative 29,83 / 29,49 / 29,84 °C | Recalcul indépendant reproduit le PDF | VÉRIFIÉ (reproduit) | `test_zone1_c1_non_regression`, `test_c1_verdicts_all_zones` |
| C2a | Verdict C2 (règle) | Rapport §3.3 | PASS si `n_above_fig4_upper ≤ 100 h/a` ET `n_below_fig4_lower == 0`, heures occupées | Rapport §3.3 | ORACLE | `test_c2_verdicts_all_zones` |
| C2b | Verdict C2 (oracle, 3 zones) | Rapport pp. 5, §7 brief | **PASS** ; **0 h** au-dessus de Fig.4 (< seuil 100) ; inf. non franchie ; dans Fig.3 | Recalcul indépendant reproduit le PDF | VÉRIFIÉ (reproduit) | `test_c2_verdicts_all_zones` |
| C2c | Double encodage seuil/observé | Brief §5.4 | Encoder à la fois seuil normatif (≤ 100) ET valeur observée (0) | — | VÉRIFIÉ | `test_c2_verdicts_all_zones` (asserte `== 0` et `<= 100`) |

## D. Métadonnées (non entrées du verdict)

| # | Élément | Valeur | Provenance | Statut |
|---|---------|--------|------------|--------|
| D1 | Surfaces zones | Z1=91, Z2=147, Z3=77 m² | `Luftvolumenstrom.xlsx` onglet C1 | VÉRIFIÉ (métadonnée) |
| D2 | Onglet `C2 Gastro` | **NON vide** : débits Gastro 14,5 / Bildung 6,4 m³/m²h, personnes/surfaces | `Luftvolumenstrom.xlsx` | VÉRIFIÉ (métadonnée, hors calcul) |

---

## Réserves ouvertes (bloquent le « vert plein »)

1. **B1 / B2 — Fig.3 SIA 180** : constantes transcrites de l'oracle (étiquettes
   imprimées sur Abbildung 3), non confrontées à SIA 180:2014, Figure 3 publiée.
   La doctrine interdit de déclarer le cas « vert » tant que ces constantes ne
   sont pas confirmées contre la norme. **Statut du cas : reproduit l'oracle,
   confirmation normative Fig.3 en attente.**
2. **Marge mince (0,03–0,12 °C)** : le verdict PASS est reproduit et robuste aux
   conventions θrm testées, mais la marge n'est pas « large ». Les conventions
   d'appariement/fenêtre sont porteuses.

---

## Signature QA

> Auditeur indépendant (`qa-auditor`) — vérification réalisée le **2026-08-19** :
>
> - [x] **Sources B3/B4 re-confrontées au JSON figé.** `FIG4_UPPER_VERTICES` /
>   `FIG4_LOWER_VERTICES` de `sia180_curves.py` sont **identiques** aux sommets
>   de `refs/reference-data/sia-380-2-2022.figure1.json`
>   (`courbes.limite_superieure.sommets` = [10;24,5][12;24,5][17,5;26,5][25;26,5] ;
>   `limite_inferieure.sommets` = [10;20,5][19;20,5][23,5;22,0][25;22,0]).
>   `test_fig4_vertices_match_frozen_reference_json` verrouille cette égalité.
> - [x] **Recalcul des 6 verdicts reproduit indépendamment.** Réimplémentation
>   séparée (courbes + θrm réécrites, sans importer `sia180_curves`/`theta_rm`/
>   `evaluate`, loader utilisé seulement pour l'extraction brute) : C1 Z1/Z2/Z3
>   → 0 h au-dessus, 0 h en dessous, max opérative 29,83 / 29,49 / 29,84 °C ;
>   C2 Z1/Z2/Z3 → occ. évaluées 2379 / 2379 / 2013, 0 h au-dessus de Fig.4,
>   0 h sous Fig.4, 0 h hors Fig.3. Les 6 cas = **PASS**, conforme à l'oracle.
> - [x] **Garde anti-faux-PASS (C2, appariement) vérifiée.** `evaluate_c2`
>   n'écarte **aucune** heure occupée (`skipped_no_theta_rm == 0` recalculé
>   indépendamment pour les 3 zones) et `test_c2_verdicts_all_zones` l'asserte
>   explicitement (`assert r.skipped_no_theta_rm == 0`). Le bug historique
>   (appariement sur le libellé complet → 100 % des heures écartées, θrm=None,
>   PASS trompeur) est bien neutralisé : l'appariement se fait sur (date, heure).
> - [x] **Réserves B1/B2 et marge acceptées comme `[À VÉRIFIER]` explicites.**
>   Confirmé par lecture visuelle de l'Abbildung 3 du rapport (p. 11) : les
>   étiquettes imprimées sont bien `0,33·θrm + 21,8` (sup.) et `0,33·θrm + 14,3`
>   (inf.), avec un plateau bas lu graphiquement à 25 °C. La fixture transcrit
>   ces valeurs de l'oracle et les marque honnêtement ORACLE / `[À VÉRIFIER]`
>   (non confrontées à SIA 180:2014 Figure 3 publiée) ; elle ne revendique PAS
>   le « vert plein ». Marge minimale recalculée indépendamment : Zone 1 C1
>   `min(courbe_sup − opérative) = 0,095 °C` ; Zone 1 C2 `min(Fig.4_sup − opérative)
>   = 0,119 °C` — mince (~0,03–0,12 °C selon la convention θrm), PAS « large ».
> - [x] **Additivité vérifiée.** Aucun fichier hors
>   `tests/reference_cases/ZOER_SIA180/` n'est modifié par la fixture (ajout
>   pur ; les fichiers `swiss_sia/*` en `M` préexistaient à la fixture et sont
>   du code de production sans rapport). La fixture est `iesve`-free (aucun
>   `import iesve`).
> - [x] **pytest** : `python -m pytest tests/reference_cases/ZOER_SIA180/test_reference.py -v`
>   → **15 passés / 0 sauté** (les 6 classeurs `.xlsx` étant présents localement,
>   les tests d'intégration ont bien été EXÉCUTÉS, pas sautés).
>
> **Verdict d'audit — AUDITÉ OK — qa-auditor — 2026-08-19.**
> Le cas **REPRODUIT fidèlement l'oracle** (les 6 verdicts PASS, 0 h de
> dépassement) par un recalcul indépendant, et sa **traçabilité est honnête** :
> Fig.4 (B3/B4) est VÉRIFIÉ contre le JSON figé, la garde anti-faux-PASS est
> réelle et testée, l'appariement horaire est correct, et les réserves sont
> documentées sans complaisance.
> **MAIS** le cas reste `[À VÉRIFIER]` sur les constantes de Fig.3 (B1/B2),
> transcrites des étiquettes du rapport et NON confrontées à SIA 180:2014
> Figure 3 publiée ; la marge est mince, pas large. **En conséquence : PAS de
> statut « vert plein ».** Statut : *golden reference reproduisant l'oracle,
> confirmation normative Fig.3 en attente* — à renvoyer au `norm-analyst` pour
> lever B1/B2.
