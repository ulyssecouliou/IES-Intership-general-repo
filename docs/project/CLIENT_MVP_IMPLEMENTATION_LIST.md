# Analyse des modèles clients & rapports — liste d'implémentation & corrections (MVP)

**Date :** 2026-08-17. Périmètre : le chemin client `Run_VE_Swiss_Compliance.py → swiss_sia/app.py::main → data_extractor → model_analyzer → sia380_checker + sia4010_checker → compliance_verdict → compliance_report_pdf + excel_report`, plus `reference_project.py`, `config.py`, `value_integrity.py`. Hors périmètre : le constructeur de modèle de référence (`ve_asset_provisioner`/`workflow`/`native_ui`).

Chaque item est cité `fichier:ligne` et classé : **[ÉVALUABLE]**, **[BLOQUÉ / NOT_CHECKABLE]**, **[NON IMPLÉMENTÉ]**.

---

## 0. Le `.aps` est-il utilisé ? Oui — 1 des 3 sources

| Source | Alimente |
|---|---|
| **Modèle statique** (`data_extractor.py`) — géométrie, U, vitrage, indices HVAC, infiltration | Diagnostics « projet de référence » SIA 380/2 par composant (LOW/advisory) |
| **`.aps` ApacheSim** (`simulation_results.py`, via `_collect_dynamic_results` app.py:318) — besoins chaud/froid, énergies, T° opérative + occupation | **Confort d'été dynamique SIA 380/2** (heures hors bornes SIA 180) + **readiness énergie SIA 4010** |
| **CSV relecteur** (`evidence_manager`, app.py:397) — comparaison globale projet/référence | **La porte DÉCISIVE de conformité SIA 380/2 §7.2.5.2** |

**Le verdict décisif SIA 380/2 ne repose PAS sur le `.aps`** mais sur la comparaison au projet de référence fournie par le relecteur. Le `.aps` porte le volet simulé (confort d'été, énergie). Sans `.aps` → volets dynamiques `NOT_CHECKABLE` (fail-closed).

---

## 1. Verdict de l'inventaire

**Le programme est sûr et conservateur : rien ne fabrique un `PASS`, aucune sur-affirmation ne survit dans les rapports.** Les manques MVP ne portent pas sur des affirmations dangereuses mais sur **la capacité à ATTEINDRE un verdict conforme évaluable** : la porte de référence décisive et la complétude de l'extraction. Deux garde-fous structurels confirmés : les alertes « impossible à vérifier » → `NOT_DETERMINED`, jamais `NOT_COMPLIANT` (`compliance_verdict.py:122-146`) ; SIA 4010 plafonné à `attestation_required` (`compliance_verdict.py:252-262`).

**Déjà corrigé (P0 de l'audit) :** porte COMPLIANT qui ne vérifiait pas `projet ≤ référence` (M-COMP) ; caveat SN EN 14825 sur SEER/SCoP (M-SEER). L'inventaire confirme que la porte « échoue bien en cas de contradiction » (`sia380_checker.py:438-464`).

---

## 2. P0-client — bloquant pour un rapport client crédible

- **[À CORRIGER] Le verdict PDF est mal cadré.** `render_compliance_report_pdf` replie toujours SIA 4010 dans le verdict (`compliance_report_pdf.py:576`, pas de paramètre de scope). Comme SIA 4010 plafonne à `NOT_DETERMINED`, **un modèle 380/2 parfaitement propre imprime quand même `NOT_DETERMINED` sur l'en-tête client.** → rendre le verdict conscient du périmètre (rapport 380/2-only). *C'est le défaut client le plus visible.*
- **[NON IMPLÉMENTÉ — reviewer-only] La porte décisive SIA 380/2 (§7.2.5.2) n'est pas automatisée.** Aucun besoin projet/référence n'est simulé ; la conformité exige une paire projet/référence `accepted` par un relecteur, scannée depuis un CSV (`sia380_checker.py:390-485`). Le spec du projet de référence ne peut jamais être « runnable » (`reference_project.py:927-936` ne renvoie que NOT_CHECKABLE / BLOCKED / PARTIAL). → **décision produit** : soit automatiser le run de référence, soit formaliser le workflow relecteur comme livrable documenté du MVP.
- **[À CLARIFIER] Le `compliance_score` (0-100) peut être élevé sans la porte décisive** (les checks composants sont LOW/advisory ; `health_score.py:52-65`). Aujourd'hui atténué par des étiquettes (« automated precheck indicator », app.py:1128). → s'assurer qu'aucun lecteur ne le prenne pour un % de conformité.

---

## 3. P1 — Extraction modèle : combler les trous qui blanchissent des checks réels

Ces grandeurs sont attendues par des checks mais rarement extraites → le check tombe en `_MISSING`/`NOT_CHECKABLE` en silence :

- **[BLOQUÉ]** `tau_v` (transmission lumineuse vitrage) — chasse d'alias non citée (`data_extractor.py:1244-1260`).
- **[BLOQUÉ]** `frame_fraction` (fraction de cadre) — alias non citée (`data_extractor.py:1262-1284`).
- **[BLOQUÉ]** `g_total` — « VEScripts ne documente pas de champ g_total direct » (`data_extractor.py:1421-1423`).
- **[BLOQUÉ]** `ventilation_installation_type` + `ventilation_control_level` — heuristiques, souvent `None` (`model_analyzer.py:779-820`).
- **[BLOQUÉ]** `window_operable` / support ventilation fenêtre — dépend de MacroFlo.
- **[BLOQUÉ]** `internal_gains_wh_m2_day` (gains internes journaliers) — non peuplé.
- **[NON IMPLÉMENTÉ]** `RoomData.dynamic_results` jamais assigné dans l'extracteur (seulement dans app.py:661) ; hvac `energy_consumption` codé `None` (`model_analyzer.py:715`).

---

## 4. P1 — Valeurs/mappings NON CITÉS à corriger (violation règle « jamais inférer/non cité »)

- **[À CITER]** Mapping entier→type d'ouverture `4→window, 5/6→door, 11→hole` — non cité (`data_extractor.py:1076-1087`, dupliqué `model_analyzer.py:1103-1108`).
- **[À CITER]** Inférence de la classe de générateur par tokens de texte libre, repli `heat_pump_unclassified` (`model_analyzer.py:884-918`) — pilote l'applicabilité SCoP/EER.
- **[À CITER]** Enums air-exchange `type==2` ventilation / `==0` infiltration (`model_analyzer.py:477,511,530`).
- **[À CITER]** Facteur `×3.6` l/s→m³/h (`model_analyzer.py:574,590,625`) ; seuils `_normalize_unit_fraction` 1.0/100 (`data_extractor.py:1572-1579`).
- **[À CITER]** Seuil jour/nuit fenêtre `>=23.5 h` (`model_analyzer.py:758`).
- **[À CORRIGER]** Sélection modèle toujours `models[0]` — `_select_best_model` calcule des comptes de corps puis les ignore (`data_extractor.py:80-99`).
- **[À CITER]** Limite porte aliasée sur `window_u=1.10` (`config.py:386`) — conservateur, pas une valeur porte citée.
- **[À CORRIGER]** Faute de frappe `"ashae"` à côté de `"ashrae"` dans la liste de préférence U (`data_extractor.py:862,1137`).
- **[À CITER]** WWR `wwr_max=0.3` (`config.py:397`) — étiqueté indicateur de revue, pas une limite : OK mais à garder explicite.

---

## 5. P2 — Sources normatives à acquérir (débloquent des checks)

| Source manquante | Débloque | Cite |
|---|---|---|
| **SN EN 14825** | verdicts SEER (froid) & SCoP (chaud) — équivalence non prouvée `[TO VERIFY]` | `sia380_checker.py:72-76` |
| **SIA 2024:2021 Raumdatenblätter** (source primaire) | supprime la dépendance au CSV relecteur pour les Gains (JSON déjà figé côté référence) | `sia380_checker.py:780-789` |
| **SIA 387/4** (puissances/contrôle éclairage) | contrôle éclairage + famille éclairage de référence | `sia380_checker.py:808-826` |
| **SIA 180:2014** (courbes de confort) | confort d'été dynamique par pièce | `sia380_checker.py:1114-1165` |
| **SIA 380 faîtière** | agrégation/pondération annuelle de l'indice énergétique | `reference_project.py:107` |
| **SN EN 15316-2 / 16798-13** | calculs énergie système / puissance de dimensionnement — non implémentés | (aucune occurrence) |

---

## 6. P2/P3 — Checks non implémentés

- **[NON IMPLÉMENTÉ]** Ponts thermiques (ψ/χ) — limite `0.0` placeholder (`config.py:104`) ; Excel toujours `MISSING` « le zéro configuré reste un placeholder, pas une preuve » (`excel_report.py:4637-4644`). Aucun chemin d'ingestion ψ/χ.
- **[NON IMPLÉMENTÉ]** Puissance de dimensionnement (workflow design-day) — `config.py:1894-1909` `automation:"NOT_IMPLEMENTED"` ; les pics annuels sont explicitement rejetés.
- **[BLOQUÉ correctement]** Froid ≥150 kW (Table 7 EER+ net de post-refroidissement) — VE ne l'expose pas → bloqueur (`reference_project.py:592-600`).

---

## 7. État SIA 4010 readiness (client) — informatif

- **[GARDE-FOU vérifié]** Ne donne jamais de pass : plafond `OFFICIAL_RESULTS_RECORDED` (`sia4010_checker.py:1581-1583`).
- **[INERTE]** `score` structurellement toujours `0.0` (chaque branche pose `score=0`, `:1496-1511`).
- **[NON IMPLÉMENTÉ / mort]** `_calculate_heating/cooling_demand` renvoient `None` (`:1402-1408`, écrasés depuis l'APS app.py:626-637) ; `_calculate_co2_emissions`/`_renewable_energy_share` existent mais **jamais appelés** (`:1410-1436`).
- **[INERTE sur chemin client]** cross-check des bandes officielles non alimenté (`app.py:1009` → `{}`).

---

## 8. Rapports — corrections

**PDF** (`compliance_report_pdf.py`, `pdf_writer.py`) — rapport une page, en-tête cabinet, verdict, identification, résumé modèle (rose des façades), bloc de portée « pas un certificat », signature. Aucune sur-affirmation. Corrections :
- **[À CORRIGER]** scope du verdict (cf. §2, `:576`).
- **[PLACEHOLDER]** seul `office_logo.placeholder.png` existe sur disque (pas de `ies_logo.png`) → chaque couverture embarque le placeholder (`:325-347`).

**Excel** (`excel_report.py`, 7 027 l.) — **classeur `xlsxwriter` custom, PAS le formulaire SIA officiel** (ni `openpyxl`, ni template ; docstring `:3-4`), 31 feuilles. Aucune sur-affirmation ne survit (« fully SIA compliant » n'apparaît qu'en lignes *Avoid*, `:1239`). Corrections :
- **[NON IMPLÉMENTÉ]** ponts thermiques = placeholder fail-closed (`:4637-4644`).
- **[MORT]** feuilles `SUMMARY` (`:2282`) et `ACTION PLAN` (`:4101`) définies mais jamais appelées ; commentaire périmé `:165-168`.
- **[DÉCISION PRODUIT]** ADR-001 §4 prévoyait de *remplir le classeur SIA 4010 officiel par COM* (crédibilité max) — cela concerne la **validation SIA 4010**, séparée du rapport client 380/2. Le classeur custom actuel est correct pour le livrable 380/2 ; le remplissage du classeur officiel reste à faire côté SIA 4010.

---

## 9. Point normatif OUVERT — quelle T° opérative pour le confort d'été ?

Le confort d'été lit la série `("dry","resultant","temperature")` de l'APS (`simulation_results.py:601`), donc **« Dry resultant temperature »**. Or l'`.aps` expose plusieurs définitions concurrentes (Operative ASHRAE, TM52/CIBSE, Dry resultant, Environmental — ADR-001 §3). **Choisir la mauvaise produit une erreur silencieuse et plausible.** → à trancher par `norm-analyst` (SIA 380/2 §5 / SIA 180) avant de considérer le confort d'été comme fiable. *C'est exactement le « faux mais crédible » que le projet existe pour éliminer.*

---

## 10. Raccourci priorisé (MVP client)

1. **Cadrer le verdict PDF** (rapport 380/2-only pas tiré à `NOT_DETERMINED` par SIA 4010). `compliance_report_pdf.py:576`.
2. **Livrer la porte décisive 380/2** — automatiser le run de référence OU formaliser le workflow relecteur comme livrable. `sia380_checker.py:390-485`.
3. **Combler les trous d'extraction** qui blanchissent des checks réels (τv, frame_fraction, g_total, ventilation type/contrôle, gains journaliers). §3.
4. **Citer ou remplacer les mappings non cités** (types d'ouverture, classe générateur, enums, 23.5 h, `models[0]`). §4.
5. **Trancher la T° opérative** du confort d'été (§9) — risque d'erreur silencieuse.
6. **Acquérir SN EN 14825 + SIA 2024/387/4** pour lever les caveats et la dépendance CSV. §5.
7. **Ponts thermiques (ψ/χ) + puissance de dimensionnement** — non implémentés. §6.
8. **Cosmétique rapports** : vrai `ies_logo.png`, retirer les 2 feuilles Excel mortes + commentaire périmé. §8.

*Rien dans le chemin client ne fabrique un PASS ni ne sur-affirme une validation ; l'outil est conservateur et fail-closed de bout en bout. Les manques concernent l'atteinte d'un verdict conforme évaluable, pas la sûreté des affirmations.*
