# Prompts Codex — finir le projet

> Chaque prompt est **autonome** (copier-coller). Ordre = chemin le plus court vers un MVP client livrable, puis qualité/structure. Colle le **préambule** en tête de chaque session Codex, puis un prompt de tâche.
>
> Docs de référence dans le dépôt (Codex doit les lire) :
> `CLAUDE.md`, `docs/CLAUDE_REFERENCE.md`, `docs/project/AUDIT_COMPLET_2026-08-16.md`,
> `docs/project/CLIENT_MVP_IMPLEMENTATION_LIST.md`, `docs/project/TODO.md`.

---

## PRÉAMBULE (à coller en tête de chaque session)

```
Tu travailles sur le SIA Compliance / SIA 4010 Navigator (IESVE/VEScripts). Règles absolues, non négociables :
1. N'invente/n'infère/ne mets JAMAIS de valeur par défaut réglementaire, physique, climatique, d'occupation, HVAC, vitrage ou de construction, ni de membre/signature d'API non vérifié. Vérité = sources SIA/ASHRAE140/EN publiées uniquement. Cite l'article exact par valeur/contrôle (ex. « # SIA 380/2:2022 5.2.2 »). Inconnu → « [TO VERIFY] », jamais deviné.
2. Verdicts fail-closed : NOT_CHECKABLE / WARNING / FAIL. Une preuve manquante ne devient JAMAIS un PASS. Aucune revendication de validation SIA 4010 sans paquet de test + preuve + classe + signature d'un relecteur indépendant.
3. Séparation dur/pur : la production vit dans swiss_sia/. Le code d'analyse/règles/scoring/rapport ne fait AUCUN import iesve ; l'accès VE est confiné à swiss_sia/reference_model/ve_api.py + la frontière swiss_sia/data_extractor.py. engine/ + ve_adapter/ = outillage de build des références, PAS le runtime client. core/ est mort. (La doc canonique a été corrigée le 2026-08-16.)
4. Autour de chaque mutation VE : capability-check + readback. Test sur API simulée ≠ qualification VE réelle — le dire.
5. Ajoute des tests unitaires (succès, données invalides, capacité API absente, readback échoué). Lance `python -m pytest <fichier>` sur ce que tu touches ; vise la suite verte (2305+ tests, 0 échec). Commit après chaque tâche finie.
6. Préserve les fichiers utilisateur ; pas de git/fs destructif ; préserve les changements non commités non liés.
7. UI/rapports bilingues via swiss_sia/reference_model/sia4010/ui_translations.py ; une clé manquante doit remonter, jamais disparaître en silence.
Avant de coder, lis : CLAUDE.md, docs/CLAUDE_REFERENCE.md, et docs/project/CLIENT_MVP_IMPLEMENTATION_LIST.md.
```

---

# BATCH A — MVP client (bloquant pour livrer)

## A1 — Cadrer le verdict du PDF client (petit, fort impact)
```
Problème : render_compliance_report_pdf (swiss_sia/compliance_report_pdf.py, ~ligne 576) replie toujours SIA 4010 dans le verdict via build_compliance_verdict. Comme sia4010_status plafonne à NOT_DETERMINED (attestation_required), un modèle SIA 380/2 parfaitement propre imprime quand même NOT_DETERMINED sur l'en-tête client.
Tâche : rendre le rapport conscient du périmètre. Ajoute un paramètre `scope` (« sia3802 » | « both », défaut « both ») à render_compliance_report_pdf ; en mode « sia3802 », la bannière de verdict et le statut global reflètent UNIQUEMENT sia3802_status (ne pas laisser SIA 4010 dégrader le verdict), tout en gardant une ligne d'information « SIA 4010 : readiness, attestation requise » et le bloc de portée inchangé. Ne casse pas le mode « both ».
Fais la même chose pour le tableau de bord HTML : swiss_sia/compliance_report_html.py::_verdict_banner + render_compliance_report_html (param scope), et propage depuis swiss_sia/app.py (les deux appels render_*).
Contraintes : rester fail-closed ; ne rien sur-affirmer. Tests : étends tests/test_compliance_report_pdf.py et tests/test_compliance_report_html.py — en scope « sia3802 » avec comparaison globale REVIEWED_RESULT_AVAILABLE et 0 bloqueur, le verdict = COMPLIANT même si SIA 4010 est NOT_DETERMINED. Lance ces deux fichiers de test.
```

## A2 — Porte décisive SIA 380/2 (§7.2.5.2) — formaliser le workflow relecteur
```
Contexte : la seule voie vers un verdict COMPLIANT SIA 380/2 est _check_global_reference_comparison (swiss_sia/sia380_checker.py) qui exige une comparaison projet/référence relue et acceptée, scannée depuis un CSV par swiss_sia/evidence_manager.py. Aujourd'hui ce workflow n'est pas documenté comme livrable et le gabarit CSV n'est pas fourni au client. (Le sens projet ≤ référence est déjà vérifié — ne pas y toucher.)
Tâche (option rapide, PAS d'automatisation du run de référence) : (a) génère un gabarit CSV documenté `config/SIA3802_global_reference_comparison.template.csv` avec les colonnes attendues par evidence_manager (project_id, comparison_scope, comparison_metric, project_value, reference_value, unit, comparison_result, reviewer, review_date, review_status, source_document, source_reference, notes) + une ligne d'exemple commentée ; (b) documente le workflow dans docs/project/CLIENT_RUN_GUIDE.md (comment produire le run de référence, remplir et faire relire le CSV, où le déposer) ; (c) dans le rapport (PDF + HTML), quand la comparaison est absente, affiche explicitement « Comparaison globale de référence requise — fournir le CSV relu » avec le chemin attendu.
Contraintes : ne jamais dériver une valeur projet d'une limite réglementaire ; le relecteur atteste que projet ≤ référence. Tests : un test evidence_manager qui charge le gabarit et confirme les colonnes ; un test que l'absence de comparaison → NOT_DETERMINED + message d'action. Lance pytest sur les fichiers touchés.
```

## A3 — Combler les trous d'extraction qui blanchissent des checks
```
Contexte : plusieurs critères tombent en _MISSING/NOT_CHECKABLE faute d'extraction fiable, dans swiss_sia/data_extractor.py et swiss_sia/model_analyzer.py : tau_v (transmission lumineuse), frame_fraction (fraction de cadre), g_total, ventilation_installation_type + ventilation_control_level, internal_gains_wh_m2_day.
Tâche : pour CHAQUE grandeur, cherche un membre iesve documenté qui l'expose (croise refs/VEScripts-API-VE2023.pdf ET ve_adapter/ve_api_surface.json qui liste la surface réelle VE 2025). Si un membre existe et est vérifié → extrais-le (avec capability-check hasattr + fallback fail-closed). Si AUCUN membre documenté n'existe → NE DEVINE PAS : laisse la grandeur en placeholder nommé + verdict NOT_CHECKABLE visible, et note « [TO VERIFY] membre VE absent » dans un commentaire cité.
Contraintes : aucun import iesve hors de la frontière ; capability-check + readback ; ne fabrique aucune valeur. Tests : pour chaque grandeur, un test avec un double d'API exposant le membre (extraction OK) et un test sans le membre (→ NOT_CHECKABLE, jamais 0/valeur inventée). Lance pytest sur les tests d'extraction.
```

## A4 — Citer ou remplacer les mappings codés en dur non cités (règle « jamais inférer »)
```
Contexte : violations de la règle 1 dans swiss_sia/data_extractor.py et model_analyzer.py :
- mapping entier→type d'ouverture 4→window, 5/6→door, 11→hole (data_extractor.py ~1076-1087, dupliqué model_analyzer.py ~1103-1108) ;
- inférence de la classe de générateur par tokens de texte libre, repli "heat_pump_unclassified" (model_analyzer.py ~884-918) ;
- enums air-exchange type==2 ventilation / ==0 infiltration (model_analyzer.py ~477,511,530) ;
- facteur ×3.6 l/s→m³/h (~574,590,625) ; seuils fraction 1.0/100 (data_extractor.py ~1572) ; seuil jour/nuit fenêtre >=23.5 h (model_analyzer.py ~758) ;
- limite porte aliasée sur window_u=1.10 (config.py ~386) ; faute de frappe "ashae" vs "ashrae" (data_extractor.py ~862,1137) ;
- _select_best_model calcule des comptes de corps puis renvoie toujours models[0] (data_extractor.py ~80-99).
Tâche : pour chaque item, soit CITE la source qui justifie la valeur (dans un dict tracé de config.py avec locator exact + unité + rationale), soit, si non citable, marque-le [TO VERIFY] et fais-le remonter dans un contrôle visible. Corrige la faute "ashae". Corrige _select_best_model pour utiliser réellement les comptes calculés (ou documente pourquoi models[0]).
Contraintes : ne change aucune valeur normative sans source + test de régression + note d'audit. Tests : un test qui vérifie que chaque enum/seuil provient d'un dict tracé et non d'un littéral nu ; un test _select_best_model. Lance pytest.
```

## A5 — Trancher la T° opérative du confort d'été (question normative — à faire relire)
```
Contexte : swiss_sia/simulation_results.py (~ligne 601) lit la série ("dry","resultant","temperature") de l'.aps pour le confort d'été. Or l'.aps expose 4 définitions concurrentes (Operative ASHRAE, TM52/CIBSE, Dry resultant, Environmental). Choisir la mauvaise produit une erreur silencieuse et plausible.
Tâche : produis une note normative traçée `traceability/operative-temperature.spec.md` qui détermine, sources à l'appui (SIA 380/2 §5, SIA 180:2014, et l'ASHRAE 140 dont le Test 1 dérive), QUELLE définition de température opérative s'applique au contrôle de confort d'été SIA. Cite les articles. Tant que ce n'est pas tranché avec certitude, garde le code tel quel mais ajoute un caveat [TO VERIFY] visible sur le critère confort d'été (déjà présent dans le dashboard) ET dans le code (docstring + le résultat). N'implémente le changement de variable QUE si la source le prouve.
Contraintes : ne devine pas ; c'est un choix normatif, pas d'ingénierie. Livrable = la spec tracée + le caveat. Pas de test de valeur tant que non tranché.
```

---

# BATCH B — Rapports (finitions client)

## B1 — Logo réel + nettoyage Excel
```
Contexte : seul config/office_logo.placeholder.png existe → chaque couverture Excel/PDF embarque le placeholder (excel_report.py ~325-347 ; compliance_report_pdf.py letterhead). Deux feuilles Excel mortes : SUMMARY (excel_report.py ~2282) et ACTION PLAN (~4101) définies mais jamais appelées ; commentaire périmé ~165-168.
Tâche : (a) permets un vrai logo cabinet configurable (chemin dans config/company_profile.json), avec repli sur le placeholder si absent — ne rien coder en dur ; (b) supprime les deux constructeurs de feuilles morts et le commentaire périmé APRÈS avoir confirmé par grep qu'ils ne sont appelés nulle part.
Tests : test que le PDF/Excel embarque le logo configuré s'il existe, le placeholder sinon ; lance tests/test_excel_report_*.py.
```

## B2 — i18n complet du tableau de bord (DE/IT)
```
Contexte : swiss_sia/compliance_report_html.py contient _UI, _SECTION_LABELS, _STATUS_LABELS pour fr + en seulement. Le produit doit être bilingue+ (DE/FR/IT/EN).
Tâche : ajoute les entrées "de" et "it" à ces trois dicts, en réutilisant/alignant les clés de swiss_sia/reference_model/sia4010/ui_translations.py (source de vérité des traductions ; ne pas diverger). Une clé manquante doit lever, pas disparaître.
Tests : un test qui, pour chaque langue de {fr,en,de,it}, appelle render_compliance_report_html et vérifie qu'aucune clé n'est absente et que le HTML ne contient pas "undefined". Lance tests/test_compliance_report_html.py.
```

---

# BATCH C — Structure & hygiène (P2/P3 — après le MVP)

> ⚠ Faire ces tâches sur une branche dédiée, après avoir commité le travail en cours (gros diff destructif).

## C1 — Supprimer le code mort (core/ + doublons ui/)
```
Contexte (vérifié 2026-08-16) : core/ n'est importé que par examples/usage_repositories.py (mort). ui/ est scindé : seuls ui/design.py + ui/tk_theme.py sont importés par swiss_sia ; le reste (dialog_tkinter, verdict_view, i18n, layout, theme, excel_export, export_pdf_reportlab, class_selection) est mort (importé seulement par ui/tests + scripts/autotest_chaine.py).
Tâche : (a) supprime core/ + examples/usage_repositories.py ; (b) déplace ui/design.py + ui/tk_theme.py vers un petit module de style sous swiss_sia/ et mets à jour les imports ; (c) supprime les modules morts de ui/ ET leurs tests, et adapte scripts/autotest_chaine.py. Confirme chaque suppression par grep préalable (aucun importeur de production).
Contraintes : git reversible ; ne casse pas la suite. Tests : `python -m pytest` complet vert après. Commit.
```

## C2 — Ranger les 91 scripts racine
```
Contexte : ~91 Run_VE_*.py à la racine ; ~8-9 sont des lanceurs produit, ~80 des sondes/jetables. Conventions existantes : scripts/probes/, scripts/legacy/.
Tâche : garde à la racine UNIQUEMENT les lanceurs produit (Run_VE_Swiss_Compliance_Hub.py, Run_VE_Swiss_Compliance.py, Run_VE_Swiss_Compliance_Remediation_Probe.py, Run_VE_SIA3802_Approved_Template_Remediation.py, Run_VE_Swiss_Reference_Model_Setup.py, Run_VE_Swiss_Compliance_Evidence_Wizard.py, Run_VE_SIA_Model_Builder_UI.py, Run_VE_SIA3802_Build_Reference_Model.py, Install_SIA_Weather_Into_VE.py). Déplace les sondes vers scripts/probes/, les jetables/one-offs vers scripts/legacy/. Mets à jour les renvois par chemin dans la doc (README, docs/). Ajoute un README racine listant les lanceurs produit.
Contraintes : `git mv` (préserve l'historique) ; vérifie qu'aucun import ne casse. Tests : suite complète verte. Commit.
```

## C3 — Découper les god-modules
```
Contexte : excel_report.py (7027 l.), native_ui.py (3214), ve_asset_provisioner.py (3179), config.py (blob de 2229 l., 0 def), app.py::main (mêle extraction+2 moteurs+APS+rapport+preuves).
Tâche (une à la fois, avec tests verts entre chaque) : commence par excel_report.py — découpe par feuille/section en sous-modules cohérents sans changer le comportement. Puis sors _collect_dynamic_results de app.py vers swiss_sia/dynamic_results.py. Puis externalise le blob de données de config.py en fichiers de données tracés chargés au démarrage.
Contraintes : refactor pur (aucun changement de comportement) ; la suite doit rester identiquement verte à chaque étape. Commit par sous-découpe.
```

## C4 — Hygiène git + isolation des tests
```
Tâche : (a) `git rm --cached` les données client suivies : sia4010_evidence/*ZOER_32_C1_draft*.csv, outputs/*.pptx, sia4010_artifacts/*.json (elles restent sur disque ; elles sont déjà ignorées par .gitignore mais encore trackées) ; NE PAS réécrire l'historique sans décision explicite. (b) Supprime les 4 fichiers racine à nom de chemin Windows littéral (ils contiennent une analyse SIA 2024 déjà préservée ailleurs — confirme avant). (c) Corrige la fragilité d'isolation de tests : le double import `config` vs `swiss_sia.config` crée deux copies de l'enum Severity qui comparent inégal dans certains sous-ensembles — force un chemin d'import unique (toujours `swiss_sia.config`) et ajoute un test qui l'assure. (d) Régénère les matrices de traçabilité périmées (traceability/test-7.matrix.md dit l'adaptateur absent — faux).
Tests : suite complète verte ; test d'isolation d'enum. Commit.
```

---

# BATCH D — Checks non implémentés (plus lourds)

## D1 — Ponts thermiques (ψ/χ)
```
Contexte : limite ponts thermiques = 0.0 placeholder (config.py ~104) ; Excel toujours MISSING « le zéro reste un placeholder, pas une preuve » (excel_report.py ~4637). Aucun chemin d'ingestion.
Tâche : ajoute un chemin d'ingestion des ψ (linéaires) / χ (ponctuels) — soit depuis un membre VE documenté (croise ve_api_surface.json ; l'adaptateur note qu'ils sont reviewer-only), soit depuis une preuve relue (CSV) comme la comparaison globale. Cite SIA 380/2 pour la méthode. Tant qu'aucune source de valeur n'existe → reste NOT_CHECKABLE (ne jamais mettre 0 comme preuve).
Tests : ingestion depuis un double ; absence → NOT_CHECKABLE. pytest.
```

## D2 — Puissance de dimensionnement (design-day)
```
Contexte : config.py ~1894-1909 automation="NOT_IMPLEMENTED" ; les pics annuels sont explicitement rejetés (il faut un calcul design-day dédié).
Tâche : implémente le workflow design-day (run de dimensionnement ApacheSim dédié) OU, si l'API ne l'expose pas de façon vérifiée, garde NOT_IMPLEMENTED et documente précisément pourquoi + ce qu'il faudrait. Ne substitue jamais un pic annuel à une puissance de dimensionnement.
Tests : selon l'issue. pytest.
```

---

# Actions HORS CODE (à mener en parallèle)

- **Acquérir les normes** (débloquent des checks, cf. CLIENT_MVP_IMPLEMENTATION_LIST §5) : SN EN 14825 (SEER/SCoP), SIA 2024:2021 Raumdatenblätter (gratuit sur sia.ch item=15143), SIA 387/4, SIA 180:2014 (complet), SIA 380 faîtière, SN EN 15316-2 / 16798-13. Une fois en main → figer les valeurs (skill /figer-reference) avec locator exact.
- **Signature indépendante** des matrices de traçabilité SIA 4010 (qa-auditor) — condition « done » de chaque test.
- **Qualification VE réelle** : rejouer les chemins de mutation/lecture dans une vraie VE (les tests actuels sont contre des doubles d'API ; API simulée ≠ qualification VE).

---

## Ordre conseillé pour finir vite
A1 → A3 → A4 → A2 → B2 → B1 → A5 (relecture) → C1 → C2 → C4 → C3 → D1 → D2.
A1/A3/A4 rendent le rapport client crédible et complet ; A2/B* le rendent livrable ; C*/D* sont la dette et les manques de fond.
```
