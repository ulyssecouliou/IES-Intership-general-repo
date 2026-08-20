# TODO — SIA Compliance / SIA 4010 Navigator

> Tracker actionnable unique. Détail complet dans :
> - [`AUDIT_COMPLET_2026-08-16.md`](AUDIT_COMPLET_2026-08-16.md) — audit + findings + plan P0→P3
> - [`CLIENT_MVP_IMPLEMENTATION_LIST.md`](CLIENT_MVP_IMPLEMENTATION_LIST.md) — analyse client + rapports, cité `fichier:ligne`
>
> Statut : ✅ fait · ⬜ à faire · 🔶 décision produit/normative requise

---

## 🧭 ÉTAT 2026-08-20 — chaîne client prouvée sur VE réelle

Modèle exemple `SIA_compatible_model_TEST` : **overall SIA 380/2 CONFORME (avec réserves)**, **16 critères OK**, precheck 89.7, health 77. Chaîne complète validée en VE réelle : extraction (gains lus du template) → `.aps` (confort **SIA 180 calculé** + énergie) → **porte décisive §7.2.5.2** → verdict CONFORME avec réserves → livrables (PDF 2 pages + **logo IES**, dashboard HTML + panneau limitations, JSON de critères, evidence pack).

### ✅ Fait cette session (2026-08-19/20)
- [x] Découplage **SIA 4010 hors du chemin client** (défaut 380/2-only ; launcher interne séparé) ; SIA 4010 = validation du logiciel, pas du bâtiment.
- [x] **Verdict décidé sur la porte §7.2.5.2** ; composants `NOT_CHECKABLE` = réserves affichées, plus des bloqueurs *(commit `cd11781`, **PENDING norm-analyst**)*.
- [x] **Lecture des gains/air-exchanges depuis le template assigné** (VE ne matérialise pas les gains au niveau pièce) *(b76fa56)*.
- [x] **Confort d'été SIA 180** calculé depuis θrm 48 h du `.aps` (Fig.4 vérifiée) *(6b71b0f)* — **PENDING norm-analyst** : définition T° opérative, fenêtre θrm, Fig.3.
- [x] **Météo** : match sur le *stem* (`.epw`/`.fwt` équivalents) *(97d3cce)*.
- [x] **Mapping usage SIA 2024 accepté crédité** en couverture *(4af0de1)*.
- [x] **Manifeste de critères** JSON rempli au runtime `<rapport>_compliance_criteria.json` + explain one-click.
- [x] **Rapport PDF pro 2 pages** : carte identification 2 colonnes + placeholders client, annexe (limitations justifiées + réserves + méthodologie), **logo IES** au pied.
- [x] Rechargement `compliance_verdict`/`compliance_criteria` par Run (plus de redémarrage VE requis) *(1cfcc86)*.
- [x] Probes lecture seule : gains pièce (`room_id`), variables `.aps`.

### ⬜ Réserves du modèle client — détail (intérêt · quoi faire · qui · effort outil)

- [x] ✅ **Ponts thermiques ψ/χ** — *ingestion faite* (`3a19a0c`) : CSV relecteur `SIA3802_thermal_bridges_<project>.csv` (méthode + total ψ.L+χ W/K OU référence de schéma + reviewer + source), scanné par `evidence_manager`, appliqué par `sia380_checker`, crédité en couverture ; capacité `EXTERNAL_EVIDENCE` → critère **OK** si évidence relue, sinon `NEEDS_REVIEWER_EVIDENCE`.
  - *Reste côté utilisateur* : fournir le **calcul de ponts thermiques** (ingénieur physique du bâtiment) et le saisir dans le CSV.

- ⬜ **Puissance de dimensionnement** (`NOT_AVAILABLE_IN_VE`, `config.py:1894` `NOT_IMPLEMENTED`)
  - *Intérêt* : SIA 380/2 prescrit les jours de dimensionnement (séquences chaud/froid après préconditionnement) ; ni pics annuels ni autosize ne s'y substituent.
  - *Quoi faire* : simulations design-day dédiées dans VE ; lire leurs `.aps`.
  - *Qui* : modélisateur VE (simu) + dev (extraction).
  - *Dev outil* : **implémenter le workflow design-day** (lecture `.aps` jours de dim.). Gros dev.

- [x] ✅ **EER froid** — *ingestion faite* (`92c9330`) : CSV relecteur `SIA3802_cooling_generators_<project>.csv` (classe + capacité kW + EER nominal ; SEER optionnel, conditionnel SN EN 14825) scanné par `evidence_manager`, appliqué par `sia380_checker`, crédite `cooling_efficiency` → **OK**. Contourne l'autosize (capacité grisée).
  - *Reste côté utilisateur* : fournir la **fiche fabricant du groupe froid** (ingénieur CVC) et la saisir dans le CSV.

- [x] ✅ **AHU / récupération de chaleur** — *ingestion faite* (`5671e1b`) : CSV relecteur `SIA3802_ahu_heat_recovery_<project>.csv` (classe d'étanchéité + rendement température récup. = quantum Table 4 ; Δp et SFP optionnels) crédite `ahu_heat_recovery` → **AVAILABLE**.
  - *Reste côté utilisateur* : fournir la **fiche CTA** (ingénieur CVC) et la saisir dans le CSV.

- [x] ✅ **Contrôle de ventilation** — *ingestion faite* (`5671e1b`) : CSV relecteur `SIA3802_ventilation_control_<project>.csv` (type système mono/multizone + classe de contrôle + tranche de débit ≤3 / 3-6 / >6 m³/h·m²) crédite `ventilation_control` → **AVAILABLE**.
  - *Reste côté utilisateur* : classifier le système + contrôle (ingénieur CVC) et le saisir dans le CSV.

- ⬜ **Protection solaire** (`NOT_CHECKABLE`, `SIA3802_SOLAR_PROTECTION_CONTROL`)
  - *Intérêt* : SIA 380/2 Table 10 — type, g_total actif, contrôle ; anti-surchauffe estivale.
  - *Quoi faire* : modéliser les stores dans VE (type, optique, contrôle), ou note relecteur si absence justifiée.
  - *Qui* : architecte / façadier + ingénieur (g_total).
  - *Dev outil* : soit lecture VE des stores, soit CSV relecteur (le gabarit `glazing_solar_protection_*.csv` existe mais la couverture ne le crédite pas encore — **ingestion à ajouter**).

- ⬜ **Contrôle éclairage** (`PARTIAL`, `SIA3802_LIGHTING_CONTROL`)
  - *Intérêt* : SIA 387/4 — puissance installée + contrôle présence/lumière du jour.
  - *Quoi faire* : acquérir **SIA 387/4** ; renseigner puissance + contrôle par local.
  - *Qui* : SIA 387/4 → SIA Shop / contact SIA (Yiqiao Yang) ; valeurs → électricien.
  - *Dev outil* : crédit du gabarit `SIA3874_lighting_control_mapping_*.csv` (scanner présent) — **ingestion/couverture à finaliser**.

- [x] ✅ **Chauffage SCOP → NON_APPLICABLE** — *fait* (`8d441b4`) : un générateur de chauffage dimensionné que VE ne classe pas en PAC (chaudière) rend `SIA3802_HEATING_SCOP` **NON_APPLICABLE** (hors périmètre), au lieu de `NOT_CHECKABLE`. Une PAC sans SCOP reste bien `NOT_CHECKABLE` (vrai manque). L'efficacité de génération non-PAC passe par la comparaison globale.

### ⬜ Sources normatives à acquérir (débloquent des verdicts)
- ⬜ **SIA 387/4** (contrôle éclairage) · **SN EN 14825** (SEER/SCoP) · **SIA 180 complet** (Fig.3 + corrigenda) · **SIA 380 faîtière** (agrégation/pondération annuelle) · **SN EN 15316-2 / 16798-13** (énergie système). → SIA Shop / contact SIA. Sans elles : verdicts `[TO VERIFY]` par honnêteté.

### 🔶 À faire valider (indépendant)
- 🔶 **norm-analyst** : (a) « porte décisive = suffisante » (interprétation §7.2.5.2) ; (b) définition de **T° opérative** SIA 180 + fenêtre θrm + Fig.3 ; (c) variantes fenêtre Test 2 / critères SIA 4010 Tests 2-7.
- 🔶 **qa-auditor** : signer les matrices de traçabilité avant tout « done ».
- 🔶 **Qualification VE réelle** : capability-check + readback par valeur (au-delà du fonctionnel prouvé).

---

## ✅ Fait (remédiation audit)

- [x] **P0.1** Test 7 — drapeau d'honnêteté `attestation_sous_commission_requise` (+ test)
- [x] **P0.2** Porte COMPLIANT SIA 380/2 — sanity-check `projet ≤ référence` + alerte `SIA3802_GLOBAL_REFERENCE_DISCREPANCY` (+ tests)
- [x] **P0.3** Caveat SN EN 14825 sur les règles client SEER/SCoP (+ test)
- [x] **P0.4** `validate_release.py` — honnête (« ne lance pas la suite ») + contrôle des signatures de matrices
- [x] **P1** Vérité documentaire — `CLAUDE.md`, `CLAUDE_REFERENCE.md`, `README`, `PROJECT_PLAN.md`, `docs/project/INDEX.md`
- [x] **P2/P3 additif** — garde de pureté `engine/` globale ; `.gitignore` += `sia4010_artifacts/`

---

## ✅ MVP client — analyse & rapports (fait depuis la rédaction initiale)

> Réévalué le 2026-08-19 contre le code réel (les items ci-dessous étaient marqués à faire ; ils sont faits).

- [x] **1. Verdict PDF cadré** — `scope="sia3802"` + `normalize_report_scope`/`scoped_verdict_status` ; rapport 380/2-only + launcher one-click. `compliance_report_pdf.py:594-681` *(commits `d01be83`, `d778d1a`, `6168949`)*
- [x] **3. Trous d'extraction comblés** en fail-closed avec status/source/placeholder : `tau_v`, `frame_fraction`, `g_total`, `ventilation_installation_type`/`control_level`, `internal_gains_wh_m2_day`. `data_extractor.py`, `model_analyzer.py`
- [x] **4. Mappings non cités tracés ou passés `NOT_CHECKABLE`** : types d'ouverture (`_opening_type_audit`, placeholder `OPENING_TYPE_VE_ENUM_TO_VERIFY` + règle `SIA3802_OPENING_TYPE_NOT_CHECKABLE`) ; classe générateur (`cb67512` : pas de comparaison SCoP hors PAC) ; `_select_best_model` utilise vraiment les comptes de corps + diagnostics ; typo `ashae` supprimée. *(commits `7526f01`, `edb611d`)*
- [x] **5. `compliance_score` étiquetage** — PDF n'affiche pas le score (verdict de statut seul) ; HTML « PAS un taux de conformité (§7.2.5.2) » ; Excel « Weighted automated indicator only; it is not a full certificate ».
- [x] **Code mort SIA 4010 retiré** — `_calculate_co2_emissions` + `_calculate_renewable_energy_share` (jamais appelés) supprimés + import `EMISSION_FACTORS` orphelin. *(2026-08-19)*
- [x] **Gains client bridgés via templates source** *(commits `8e4b4a9`, `592aa3a`, `680b9cf`)* ; dépendance CSV levée par SIA 2024:2021 figé.

## 🔶 MVP client — reste (décision produit, pas juste du code)

- [ ] 🔶 **2. Porte décisive SIA 380/2 (§7.2.5.2)** — automatiser le run de référence **ou** formaliser le workflow relecteur comme livrable documenté. Builder de référence Phase A/B déjà en place (`b4d21b6`). `sia380_checker.py:390-485`, `reference_project.py`
- [ ] **`score` SIA 4010 inerte (=0.0)** — structurel : chaque branche pose 0 tant que la validation officielle n'est pas atteinte (plafond `OFFICIAL_RESULTS_RECORDED`). À laisser tel quel (fail-closed) ou retirer le champ.

## ✅ Interface client (fait)

- [x] **Tableau de bord de conformité client** — HTML interactif triable/par-section/justifications, style IESVE. `compliance_report_html.py` + `compliance_report_html_template.py`
- [x] Branché sur les vrais résultats (`ComplianceVerdict` + alertes) via `app.py` — export `_dashboard.html` autonome à côté du PDF/Excel
- [x] scope-aware (bannière 380/2-only) ; i18n FR/EN via `ui_translations.py`
- [ ] i18n DE/IT du dashboard (FR/EN faits)
- [ ] Vrai `ies_logo.png` (placeholder seul sur disque — **fichier à fournir**)

## 🔶 À trancher (normatif)

- [ ] **T° opérative du confort d'été** — le `.aps` expose 4 définitions ; le code lit « Dry resultant temperature » (`simulation_results.py:601`). Trancher par `norm-analyst` (risque d'erreur silencieuse). ADR-001 §3
- [ ] Variant de fenêtre Test 2 (`Fe det Spec`/`non Spec`/`einf`) ; critères SIA 4010 Tests 2-7 (INFÉRÉS, sous-commission 4.6.2)

## ⬜ Sources normatives à acquérir (débloquent des checks)

- [ ] **SN EN 14825** → lève le caveat SEER/SCoP
- [ ] **SIA 2024:2021 Raumdatenblätter** (source primaire) → supprime la dépendance CSV relecteur pour les gains
- [ ] **SIA 387/4** → contrôle éclairage
- [ ] **SIA 180:2014** (complet, corrigenda) → confort d'été
- [ ] **SIA 380 faîtière** → agrégation/pondération annuelle
- [ ] **SN EN 15316-2 / 16798-13** → énergie système / puissance de dimensionnement

## ⬜ Checks non implémentés

- [ ] Ponts thermiques (ingestion ψ/χ) — placeholder zéro (`config.py:104`, `excel_report.py:4637`)
- [ ] Puissance de dimensionnement (workflow design-day) — `config.py:1894`

## ⬜ Structure & modularité (P2) — passe dédiée, idéalement sur branche après commit

- [ ] Supprimer `core/` (mort) + `examples/usage_repositories.py`
- [ ] Extraire `ui/design.py`+`ui/tk_theme.py` vers `swiss_sia`, supprimer les doublons morts de `ui/` (+ leurs tests)
- [ ] Ranger les ~91 scripts racine → `scripts/probes/`, `scripts/legacy/` (garder ~9 lanceurs produit)
- [ ] Découper les god-modules : `excel_report.py` (7 027 l.), `native_ui.py`, `ve_asset_provisioner.py`, `config.py` (blob), `app.py::main`
- [ ] Isoler `engine/`+`ve_adapter/` sous `tools/` avec README « outillage »
- [ ] Corriger la fragilité d'isolation de tests (double import `config` vs `swiss_sia.config` → enum `Severity` inégal)

## ⬜ Hygiène & data-handling (P3)

- [ ] `git rm --cached` des données client suivies : `sia4010_evidence/*ZOER_32_C1_draft*.csv`, `outputs/*.pptx`, `sia4010_artifacts/*.json` *(déjà dans l'historique — un purge serait une décision séparée)*
- [ ] Retirer les 4 fichiers racine à nom de chemin Windows *(contiennent de la vraie analyse SIA 2024 — fait clé préservé en mémoire ; à retirer après confirmation)*
- [ ] Rapports : vrai `ies_logo.png` ; retirer les 2 feuilles Excel mortes (`SUMMARY`, `ACTION PLAN`) + commentaire périmé
- [ ] Régénérer les matrices de traçabilité périmées (`test-7.matrix.md` dit l'adaptateur absent — faux)
