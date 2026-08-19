# TODO — SIA Compliance / SIA 4010 Navigator

> Tracker actionnable unique. Détail complet dans :
> - [`AUDIT_COMPLET_2026-08-16.md`](AUDIT_COMPLET_2026-08-16.md) — audit + findings + plan P0→P3
> - [`CLIENT_MVP_IMPLEMENTATION_LIST.md`](CLIENT_MVP_IMPLEMENTATION_LIST.md) — analyse client + rapports, cité `fichier:ligne`
>
> Statut : ✅ fait · ⬜ à faire · 🔶 décision produit/normative requise

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
