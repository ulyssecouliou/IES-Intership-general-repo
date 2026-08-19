# Audit complet — SIA Compliance / SIA 4010 Navigator

**Date :** 2026-08-16
**Branche auditée :** `sia4010-evidence-hardening-20260812`
**Commande de reprise du projet formulée :** « comme si on repartait de zéro, en ne s'appuyant que sur les sources officielles, pour faire un programme Python qui, via la bibliothèque `iesve` exécutée en navigateur VEScripts, génère un rapport client (infos client + modèle + conformité SIA) — et vérifier toute l'architecture, la modularité, la maintenabilité et l'optimisation. »

**Méthode.** Cartographie directe du dépôt par l'auditeur en chef, puis quatre audits experts indépendants menés en parallèle, chacun lisant réellement le code (aucune supposition) :
1. **Fidélité normative** (sources officielles, citations d'articles, verdicts fail-closed) ;
2. **Intégration IESVE** (frontière `iesve`/pur, sûreté des mutations) ;
3. **Architecture & code mort** (graphe d'imports, duplications, god-modules) ;
4. **QA / tests / traçabilité** (exécution réelle de la suite, signatures des matrices, revendiqué vs prouvé).

Aucun fichier de production n'a été modifié pendant l'audit lui-même. Les changements non commités préexistants ont été préservés.

> **Mise à jour — remédiation (2026-08-17).**
> **P0 (justesse & portes) : TERMINÉ et vérifié** — suite complète verte (exit 0).
> Verrou d'honnêteté Test 7 (`attestation_sous_commission_requise`) ; sanity-check
> `projet ≤ référence` sur la porte COMPLIANT + alerte `SIA3802_GLOBAL_REFERENCE_DISCREPANCY`
> (M-COMP) ; caveat SN EN 14825 propagé sur SEER/SCoP client (M-SEER) ; porte de
> release honnête (« ne lance pas la suite ») + contrôle des signatures de matrices
> (C-REL). Tests de non-régression ajoutés pour chacun.
> **P1 (vérité documentaire) : TERMINÉ** — `CLAUDE.md`, `docs/CLAUDE_REFERENCE.md`
> §Layout, `README`, `PROJECT_PLAN.md` §2 corrigés (swiss_sia = seule archi de
> production ; engine/ve_adapter = outillage ; ui hérité ; core mort) ; index
> `docs/project/INDEX.md` créé.
> **P2/P3 : gains additifs faits** — garde de pureté `engine/` globale (ferme le
> trou CI-only), `.gitignore` += `sia4010_artifacts/`. Restent en passe dédiée :
> suppression de `core/` + doublons morts `ui/`, réorganisation des ~91 scripts
> racine, découpe des god-modules, et `git rm --cached` des données client suivies.
> **Finding mineur découvert** : fragilité d'isolation de tests — double import
> `config` vs `swiss_sia.config` rendant les membres de l'enum `Severity` inégaux
> dans certains sous-ensembles de tests (la suite complète reste verte car son
> ordre d'import canonicalise l'enum). À corriger avec la passe P2.

---

## 0. Verdict exécutif

**Tu n'as pas à repartir de zéro. Le programme que tu décris existe déjà, et son cœur normatif est solide et honnête.** La chaîne `Run_VE_Swiss_Compliance.py → swiss_sia/app.py` fait exactement ce que tu vises : elle ouvre le projet VE actif via `iesve`, extrait le modèle, exécute les contrôles SIA 380/2, prépare la readiness SIA 4010, calcule un score, puis produit **un rapport client PDF** (en-tête cabinet, identification projet/modèle, verdict par domaine, figures du modèle, bloc de portée, signature — bilingue DE/FR/IT/EN), un classeur Excel et un pack de preuves ZIP.

Le risque n°1 que la doctrine du projet vise — *« des résultats faux mais crédibles »* — est **réellement maîtrisé** : les verdicts sont fail-closed (`NOT_CHECKABLE`/`NOT_DETERMINED`, jamais `PASS` sur preuve manquante), SIA 4010 ne peut jamais afficher « validé », aucune valeur normative inventée ne pilote un verdict, la frontière `iesve`/pur est propre, chaque mutation VE est encadrée par capability-check + read-back, et la suite de 2 305 tests est vraiment verte (0 échec). C'est un travail d'ingénierie sérieux.

**Le vrai problème n'est pas la justesse — c'est la lisibilité et la reprenabilité.** Le dépôt a accumulé **trois architectures parallèles**, **91 scripts à la racine**, des **god-modules** (jusqu'à 7 027 lignes), une **documentation canonique qui décrit l'architecture morte comme courante**, et **~50 documents d'état** qui se recouvrent. Un ingénieur qui reprend serait activement induit en erreur sur *où vit la logique de production*. S'ajoutent **quatre trous latents de justesse/gouvernance** à colmater avant toute mise en avant commerciale (Test 7, porte de conformité SIA 380/2, porte de release, cadrage « simulé ≠ VE réel »).

En un mot : **le moteur est bon, la carrosserie est encombrée.** Le plan §9 est un travail de *consolidation et de vérité documentaire*, pas de réécriture.

---

## 1. Le produit livré vs ta vision — conforme

| Ta vision | État réel | Emplacement |
|---|---|---|
| Programme Python dans VEScripts (navigateur) | ✅ Lanceurs bouton-Run, dialogue Tkinter natif dans VE | `Run_VE_Swiss_Compliance_Hub.py`, `swiss_sia/*_ui.py` |
| Via la bibliothèque `iesve` | ✅ Accès `iesve` isolé, lazy/injecté, jamais dans le code pur | `swiss_sia/reference_model/ve_api.py`, `data_extractor.py` |
| Rapport client avec infos **client/cabinet** | ✅ En-tête + signature depuis `company_profile.json`, jamais inventé | `swiss_sia/compliance_report_pdf.py`, `company_profile.py` |
| … infos **modèle** | ✅ Pièces, surfaces, aires opaques/vitrées par orientation, WWR, schéma | `compliance_report_pdf.py::summarise_model` |
| … **conformité SIA** | ✅ Verdict par domaine SIA 380/2 + état SIA 4010, bloc de portée « ce n'est pas un certificat » | `compliance_verdict.py`, `compliance_report_pdf.py` |
| Basé uniquement sur sources officielles | ✅ Valeurs figées tracées au PDF SIA primaire (audit interne cellule par cellule) | `refs/SIA-380-2-2022.pdf`, `swiss_sia/config.py`, `traceability/audit-reference-project-2026-08.md` |

**Conclusion :** la cible fonctionnelle est atteinte. La suite du document porte sur ce qui la fragilise.

---

## 2. Synthèse consolidée des findings

Sévérité : **CRITIQUE** = à traiter avant toute mise en avant commerciale ; **MAJEUR** = dette qui fera mal à la reprise/au client ; **MINEUR** = à nettoyer.

| ID | Axe | Sévérité | Constat | Emplacement |
|---|---|---|---|---|
| **C-DOC** | Archi | CRITIQUE | La doc canonique (`CLAUDE.md`, `docs/CLAUDE_REFERENCE.md`, `README`) décrit `engine/`+`ve_adapter/`+`ui/` comme l'archi courante — or c'est l'archi **parallèle/morte**. Pointe un repreneur vers le mauvais endroit. | `docs/CLAUDE_REFERENCE.md` §Layout, `README` |
| **C-T7** | QA/Moteur | CRITIQUE (latent) | Le moteur Test 7 pose `classe_5_validee = True` + `PASS` dès qu'une valeur candidate existe, sans verrou et sans propager la réserve `INFERE`. Neutralisé seulement par l'absence d'adaptateur câblé — mais `ve_adapter/test7_adapter.py` (756 l.) existe désormais. | `engine/test7_engine.py`, test `engine/tests/test_test7_engine.py:287` |
| **C-REL** | QA/Release | CRITIQUE | La porte de release documentée n'exécute **jamais** la suite de tests et ne vérifie **aucune** signature de matrice. Une suite rouge ou une matrice non signée passe la porte. (Atténué par la CI qui, elle, lance tout.) | `scripts/quality/validate_release.py` |
| **M-SEER** | Norme | MAJEUR | Le checker client compare `SEER`/`SCoP` VE aux limites SIA sans le caveat `[TO VERIFY]` d'équivalence SN EN 14825 que `reference_project.py` attache pourtant. Formulation « meets the SIA limit » sur base non prouvée, sur un rapport signé. | `swiss_sia/sia380_checker.py:200-215`, `config.py:205-293` |
| **M-COMP** | Norme | MAJEUR | La **seule** porte vers un verdict `COMPLIANT` SIA 380/2 fait confiance au drapeau relecteur `accepted` **sans jamais comparer** `project_value` à `reference_value`. Un CSV `accepted=yes` avec des chiffres non conformes imprimerait « COMPLIANT ». | `sia380_checker.py:404-410`, `compliance_verdict.py:204-221` |
| **M-SIM** | QA | MAJEUR | Toute la preuve « qualification/runtime » est contre des **doubles manuscrits** de l'API `iesve`, jamais VE réel. Légitime et honnêtement étiqueté dans le code, mais le README (« verified guarded mutation path ») peut se lire comme une preuve VE réelle. | `tests/test_sia4010_*_qualification.py`, `README:27-30` |
| **M-DUP** | Archi | MAJEUR | Chaque couche de sortie/UI est **dupliquée** entre le vivant (`swiss_sia`) et le mort (`ui`/`engine`) : Excel, PDF, moteur bandes, Tkinter, i18n, moteurs Test 1/7. Risque : éditer la copie morte. | cf. §5 tableau duplications |
| **M-SCRIPTS** | Archi | MAJEUR | **91 scripts `Run_VE_*.py`** à la racine, dont ~8-9 produits réels noyés dans ~80 sondes/jetables. Conventions `scripts/probes/` et `scripts/legacy/` existantes mais non appliquées. | racine du dépôt |
| **M-GOD** | Archi | MAJEUR | God-modules : `excel_report.py` (7 027 l.), `native_ui.py` (3 214), `ve_asset_provisioner.py` (3 179), `config.py` (blob 2 229), `app.py::main()` mêle extraction+2 moteurs+APS+rapport+preuves. | cf. §5 |
| **M-MATRIX** | QA | MAJEUR | Matrices de traçabilité périmées vs code : `test-7.matrix.md` déclare l'adaptateur VE **absent** et les fichiers **non versionnés** — les deux sont faux aujourd'hui. Rien ne gate leur régénération. | `traceability/test-7.matrix.md` |
| **M-DATA** | Hygiène | MAJEUR | Données client suivies par git malgré `.gitignore` : `sia4010_evidence/*.csv` (brouillons de preuves `ZOER_32_C1`), `outputs/*.pptx`, `sia4010_artifacts/*.json`. Souci data-handling (données client dans l'historique). | cf. §7 |
| **M-PUR** | IESVE/QA | MAJEUR (robustesse) | La garde de pureté `engine/` (0 `import iesve`) n'est exhaustive **qu'en CI** ; en local chaque test-garde ne couvre qu'un fichier. Un nouveau module `engine` important `iesve` passerait la suite locale. | `engine/tests/`, `.github/workflows/engine-tests.yml` |

**Mineurs** (détaillés dans les sections d'axe) : citations de locator incohérentes (`config.py:357` vs `1179`), tolérances QA en nombres nus (`value_integrity.py` `1.05`, `0.02`), facteurs CO2 placeholder (`config.py:2169`), `assign_hvac_if_configured` non gardé (`ve_api.py:1744`), garde disposable dans le lanceur et non à la frontière de mutation, mapping entier→type d'ouverture non cité (`data_extractor.py:1076`), docstring de frontière périmée (`ve_adapter/test1_adapter.py:4`), `core/` mort, 4 fichiers scratch à nom de chemin Windows à la racine, `sia4010_artifacts/` hors `.gitignore`.

---

## 3. Axe 1 — Fidélité normative

**Verdict : solide et honnêtement fail-closed. Aucun finding critique.** Aucune valeur normative franchement inventée ne pilote un verdict ; les résidus sont des garde-fous et des placeholders honnêtement étiquetés.

**Forces vérifiées.**
- Comparateur SIA 4010 (`reference_model/sia4010/compliance_comparator.py:56-131`) : `NOT_CHECKABLE` si observé manquant, unité discordante (aucune conversion implicite) ou tolérance officielle absente ; bande officielle prioritaire ; aucune tolérance inventée.
- Verdict fail-closed (`compliance_verdict.py:122-266`) : les alertes « impossible à vérifier » sont indéterminées, jamais bloquantes ; SIA 4010 plafonne à `attestation_required`.
- Comparaison globale exigée (`sia380_checker.py:412-425`) : `NOT_CHECKABLE` + alerte CRITICAL tant qu'aucune comparaison relue n'est fournie ; les contrôles composants sont des diagnostics LOW.
- Confort d'été fail-closed (`sia380_checker.py:1081-1089`) : `building_status` absent → alerte, pas de repli sur l'allocation clémente 400 h.
- Sources primaires présentes : `refs/SIA-380-2-2022.pdf` et `refs/SIA-4010-2023.pdf` **sont commités** ; audit interne signant 22 valeurs + ~110 constantes recoupées cellule par cellule, 0 divergence (`traceability/audit-reference-project-2026-08.md`).

**Majeurs : M-SEER, M-COMP** (cf. §2).

**Mineurs.** Locator 400 h incohérent (`config.py:357` cite 3.2.4.3-4, `config.py:1179` cite 3.2.4.5) ; tolérances QA nues `1.05`/`0.02` à déplacer en dict tracé (`value_integrity.py`) ; readiness SIA 4010 percole dans le *health score* (pas dans le *compliance score*, qui reste bien isolé) ; facteurs CO2 en dur mais explicitement `PLACEHOLDER` et non consommés (`sia4010_checker.py:141` force `None`).

**Sources externes non résolues à tracer** (hors périmètre code, bloquantes pour lever certains `[TO VERIFY]`) : SN EN 14825 (équivalence indice SEER/SCoP), SN EN 15316-2, SN EN 16798-13, SIA 2024:2021 Raumdatenblätter (source primaire — la famille 8 du constructeur de référence n'est **pas** signée faute de source), SIA 180:2014 (captures partielles), et les critères d'acceptation SIA 4010 Tests 2-7 (INFÉRÉS, en attente de la sous-commission, art. 4.6.2).

---

## 4. Axe 2 — Intégration IESVE

**Verdict : frontière propre et défendable ; sûreté des mutations parmi les plus disciplinées. Aucun finding critique ni majeur bloquant.**

- **Zéro `import iesve` au chargement** dans `engine/`, `ui/` ou les modules d'analyse `swiss_sia` : tout accès VE est lazy/gardé, confiné aux lanceurs, `ve_adapter/`, et les passerelles `swiss_sia/reference_model/`.
- **Capability-gate avant chaque mutation** (`workflow.py:260`, `ve_asset_provisioner.py:2959`), **read-back immédiat fail-closed** après (`ve_api.py:764-799`, 1663-1692, 1791-1814) qui lève `VeMutationError` sur toute dérive.
- **Membres d'API confirmés sur le runtime réel VE 2025** (`ve_adapter/ve_api_surface.json` : `assign_construction`, `create_construction`, `assign_thermal_template_to_rooms`, `rebuild_adjacencies`…), pas seulement documentés.
- **Simulé ≠ réel, dit dans le code** (`apachesim_qualification.py:320` « … does not prove … »).

**Mineurs à durcir.** `assign_hvac_if_configured` rejoue le dict complet de read-back dans le setter, non gardé/non enveloppé (`ve_api.py:1744-1755`) ; garde disposable dans le lanceur (`Run_VE_SIA3802_Build_Reference_Model.py:181`) plutôt qu'à la frontière `IesVeGateway`, sans consigne « jeter le projet en cas d'échec » ; mapping entier→type d'ouverture non cité (`data_extractor.py:1076`) ; docstring périmée « le SEUL endroit qui importe iesve » (`ve_adapter/test1_adapter.py:4`, faux — il y a deux couches VE) ; deux scripts `scripts/legacy/*` importent `iesve` hors des dossiers VE canoniques.

---

## 5. Axe 3 — Architecture, modularité, optimisation

**Verdict : une seule architecture est vivante ; deux autres coexistent sans hiérarchie déclarée. C'est le principal frein à la reprise.**

### 5.1 L'histoire : une consolidation inachevée
ADR-001 §8 (accepté le 2026-07-30) acte la fusion d'un **squelette 4-couches propre** (`engine/`+`ve_adapter/`+`ui/`+`core/`) dans un **produit déjà fonctionnel** (`swiss_sia/`), avec pour consigne explicite de *porter la rigueur du squelette dans le produit, pas de reconstruire*. Ce port n'a été fait qu'à moitié : les dossiers du squelette ont été copiés, mais le travail SIA 4010 a continué dans `swiss_sia/reference_model/sia4010/` — d'où **deux implémentations SIA 4010 côte à côte**. ADR-001 invalide au passage deux doctrines encore présentes dans les docs : **D2 supprime l'UI web** (Tkinter uniquement) et la sonde VE 2025 **annule la contrainte « Python 3.4 »** (c'est 3.12.3).

### 5.2 Liveness des packages
| Package | LOC hors test | Importeurs prod | Statut |
|---|---|---|---|
| `swiss_sia/` | **74 046** | 77 | **VIVANT** — 100 % des points d'entrée client |
| `ui/` | 4 974 | 4 | **SCINDÉ** — seuls `design.py`+`tk_theme.py` (tokens de style) servent ; le reste mort |
| `ve_adapter/` | 3 762 | 5 | **OUTILLAGE** — importé par `scripts/` (build réf. + sondes Test 1), zéro depuis `swiss_sia` |
| `engine/` | 2 007 | 5 | **OUTILLAGE** — recompute indépendant (ADR-001 §4.2) + build de `refs/reference-data/` |
| `core/` | 859 | 1 | **MORT** — seul importeur = `examples/usage_repositories.py` |

> **Nuance importante (vérifiée par l'auditeur en chef).** `engine/`+`ve_adapter/` **ne sont pas supprimables tels quels** : `engine/*` lit `refs/reference-data/` et est importé par `scripts/build_sia_reference.py`, `build_test7_reference.py`, `build_traceability_matrix.py`, `autotest_chaine.py` qui **régénèrent** les JSON figés consommés au runtime par `swiss_sia`. C'est de l'**outillage de build & de vérification indépendante** load-bearing → à **requalifier et isoler** (p. ex. sous `tools/reference_build/`), pas à jeter. Seuls `core/` et la moitié non-style de `ui/` sont réellement supprimables.

### 5.3 Duplications (vivant ↔ mort/parallèle)
| Fonction | Vivant (`swiss_sia`) | Doublon mort/parallèle |
|---|---|---|
| Export Excel | `excel_report.py` (7 027) | `ui/excel_export.py` (334) |
| Export PDF | `compliance_report_pdf.py`+`pdf_writer.py` | `ui/export_pdf_reportlab.py`+`ui/verdict_view.py` |
| Moteur bandes/dispersion | `reference_model/sia4010/distribution_reference.py`+`frequency_distribution.py` | `engine/sia_bandes_engine.py`+`sia_distributions_engine.py`+`scatter_band.py` |
| UI Tkinter | `native_ui.py`+`compliance_hub_ui.py`+… | `ui/dialog_tkinter.py`+`verdict_view.py`+… |
| i18n | `reference_model/sia4010/ui_translations.py` (2 155) | `ui/i18n.py` (321) |
| Éval Test 1/7 | `reference_model/sia4010/test1_*` | `engine/test1_engine.py`+`ve_adapter/test1_adapter.py` |

### 5.4 Les 91 scripts racine (15 354 lignes)
| Catégorie | Nombre | Cible |
|---|---|---|
| Vrais lanceurs produit | ~8-9 | rester à la racine |
| Sondes / introspection (`Probe`, `Sonde`, `Inspect`, `Diagnostic`) | ~32 | `scripts/probes/` |
| Rapports Anwenderbericht (`_AB.py`) | 6 | `scripts/probes/` |
| Qualification/`Verify`/`Compare`/`Reconcile`/`Calibrate` | ~15 | `scripts/probes/` ou `scripts/legacy/` |
| Échafaudage Case600 | 9 | `scripts/legacy/` |
| One-offs `Create_Missing`/`Repair`/`Resume`/`Prepare` | ~14 | `scripts/legacy/` |

Lanceurs produit à garder : `Run_VE_Swiss_Compliance_Hub.py`, `Run_VE_Swiss_Compliance.py`, `Run_VE_Swiss_Compliance_Remediation_Probe.py`, `Run_VE_SIA3802_Approved_Template_Remediation.py`, `Run_VE_Swiss_Reference_Model_Setup.py`, `Run_VE_Swiss_Compliance_Evidence_Wizard.py`, `Run_VE_SIA_Model_Builder_UI.py`, `Run_VE_SIA3802_Build_Reference_Model.py`, `Install_SIA_Weather_Into_VE.py`.

### 5.5 Optimisation
La performance d'exécution n'est **pas** l'axe critique (l'outil tourne une fois par modèle dans VE ; les coûts dominants sont l'extraction VE et la simulation ApacheSim, hors de notre code). L'« optimisation » utile ici est **structurelle** : découper les god-modules (§2 M-GOD), sortir `_collect_dynamic_results` (~300 l.) de `app.py`, externaliser le blob de données `config.py` (2 229 l., 0 def) en fichiers de données tracés, et scinder `excel_report.py` par feuille. Effet secondaire mesuré côté tests : la suite tombe de 17 s à 4,5 s sans le classeur (empreinte de cellules) — bon réflexe déjà en place.

---

## 6. Axe 4 — QA, tests, traçabilité

**Verdict : suite réellement verte et discipline exceptionnellement honnête. L'écart revendiqué/prouvé est faible et divulgué.**

- **2 305 tests distincts** (3 855 avec les subTests unittest), **3 851 passés, 0 échec, 0 erreur, 4 skips** environnementaux. 100 % tourne **sans `iesve`**. CI (`.github/workflows/engine-tests.yml`) lance toute la suite + un grep anti-`import iesve` sur `engine/`.
- **0/7 matrices SIA 4010 signées** — et c'est **assumé** : chaque `traceability/test-N.matrix.md` est explicitement « NON SIGNÉE ». La seule signature du dépôt (`audit-reference-project-2026-08.md`) couvre le **constructeur de référence SIA 380/2** (familles 1-7), **pas** les tests SIA 4010 — à ne pas confondre dans la communication.
- Discipline anti-faux-positif **testée** : aucune classe `VALIDATED` sans PASS officiel, `OFFICIAL_FAIL` écrase `OFFICIAL_PASS`, l'autotest s'assert lui-même « ne prouve rien sur IESVE ».

**Critiques : C-T7, C-REL** (cf. §2). **Majeurs : M-SIM, M-MATRIX, M-PUR.**

**Tableau des tests SIA 4010**
| Test | Matrice signée ? | Tests unitaires ? | Qualification |
|---|---|---|---|
| 1 | NON | Oui (réf-data audité) | **Simulée** (doubles) |
| 2 | NON | Oui | Simulée |
| 3 | NON | Oui | Simulée |
| 4 | NON (critère INFÉRÉ) | Oui | Simulée |
| 5 | NON | Oui | Simulée |
| 6 | NON (critère INFÉRÉ) | Oui | Simulée |
| 7 | NON (matrice **renvoyée**, bug de critère) | Oui mais 1 test tautologique + défauts ouverts | Simulée (adaptateur présent, jamais exécuté en VE) |

---

## 7. Hygiène & data-handling

- **Données client dans l'historique git** (M-DATA) : `sia4010_evidence/*.csv` (brouillons `ZOER_32_C1`), `outputs/*.pptx`, `sia4010_artifacts/*.json` restent **suivis** malgré `.gitignore` (committés avant le rattrapage). → `git rm --cached` requis ; les brouillons de preuves client dans l'historique sont sensibles.
- **4 fichiers scratch à nom de chemin Windows littéral à la racine** (non suivis, hors `.gitignore`) — écrits par erreur par un outil dans la racine. → à supprimer.
- `sia4010_artifacts/` **absent de `.gitignore`** ; `.gitignore` lui-même rétro-ajouté (commentaire « 821 Mo non ignorés ») = preuve que de grosses sorties étaient historiquement committées.
- **Documentation pléthorique** : ~50 fichiers dans `docs/project/` aux noms qui se recouvrent (`MVP_COMPLETION_MATRIX`, `MVP_MANAGER_HANDOFF`, `MVP_RUSH_RUNBOOK`, `TONIGHT_..._RUNBOOK`, `HYBRID_EXECUTION_STATUS`, `SIA_COMPLIANCE_EXECUTION_TRACKER`…). Utile historiquement, ingérable pour une reprise.

---

## 8. Ce qui est déjà excellent (à préserver, ne pas « sur-corriger »)

1. La **doctrine fail-closed** est réelle, pas cosmétique — c'est le principal actif du produit.
2. La **frontière `iesve`/pur** et la **sûreté des mutations** (capability + read-back) sont exemplaires.
3. Le **rapport client PDF** est soigné, bilingue, et refuse d'inventer.
4. Les **données de référence figées** sont tracées au PDF primaire et vérifiées cellule par cellule.
5. L'**honnêteté de la QA** (matrices non signées assumées, « simulé ≠ réel » dit dans le code) est exactement ce qu'un audit veut trouver.

---

## 9. Plan de remise en état priorisé

> Principe : **la vérité documentaire et les trous de justesse d'abord** (peu coûteux, fort effet), la structure ensuite, le cosmétique en dernier. Aucune de ces actions n'exige de repartir de zéro.

### P0 — Justesse & gouvernance (avant toute mise en avant commerciale)
- **C-T7** — Verrouiller `engine/test7_engine.py` : `classe_5_validee`/`PASS` impossibles sans critère officiel confirmé ; propager la réserve `INFERE` au booléen ; corriger les défauts m1 (candidat chaîne → rejet propre, `NaN` → `NOT_CHECKABLE`, unité confrontée). Test de non-régression qui **échoue** si un candidat nu produit `True`.
- **M-COMP** — Dans `_check_global_reference_comparison`, **comparer `project_value` à `reference_value`** après acceptation ; rétrograder en `NOT_COMPLIANT`/`WARNING` si le sens contredit `accepted` ; clarifier la sémantique de `accepted` dans le gabarit CSV et le PDF. Test de la contradiction `accepted=yes` mais `project > reference`.
- **M-SEER** — Propager le caveat `[SEER/SCoP per SN EN 14825 — VE index equivalence TO VERIFY]` dans `SIA3802_COOLING_SEER_MIN`/`SIA3802_HEATING_SCOP_MIN`, ou aligner le checker client sur `reference_project.py` (EER pleine charge). Ajouter `source`/état placeholder aux 4 tables `config.py:205-293`.
- **C-REL** — Soit faire de `validate_release.py` une vraie porte (lancer la suite + vérifier les signatures/fraîcheur des matrices), soit le renommer/documenter honnêtement pour ce qu'il fait, et **désigner la CI comme la porte de release de référence**.

### P1 — Vérité documentaire (le plus fort levier de reprenabilité, faible coût)
- **C-DOC** — Réécrire `CLAUDE.md`, `docs/CLAUDE_REFERENCE.md` §Layout et le tableau `README` pour **acter `swiss_sia/` comme unique architecture de production**. Requalifier `engine/`+`ve_adapter/` en « outillage de build des données de référence & vérification indépendante » (cf. §5.2). Retirer la « Couche 4 app web » de `PROJECT_PLAN.md` (supprimée par ADR-001 D2) et la contrainte Python 3.4.
- **M-MATRIX** — Régénérer les `traceability/*.matrix.md` périmées (Test 7 : adaptateur présent, fichiers versionnés) ou gater leur régénération ; distinguer clairement « signé » (constructeur SIA 380/2) de « non signé » (tests SIA 4010).
- **M-SIM** — Reformuler le README §27-30 : « chemins de **mutation gardés, vérifiés par read-back contre des doubles d'API** — **qualification VE réelle en attente** ». Bannir « verified » sans qualificatif dans toute communication manager/client.
- **Docs** — Créer un `docs/project/INDEX.md` unique, archiver les ~40 runbooks datés sous `docs/project/archive/`, garder 5-6 documents vivants (architecture, statut, reprise, guide client, plan).

### P2 — Structure & modularité
- **M-SCRIPTS** — Déplacer ~80 scripts racine vers `scripts/probes/` et `scripts/legacy/` ; ne garder que les ~9 lanceurs produit (§5.4). Un `README` racine listant ces 9.
- **M-DUP / core mort** — Supprimer `core/` ; extraire `ui/design.py`+`ui/tk_theme.py` vers un petit module de style dans `swiss_sia`, puis supprimer les doublons morts de `ui/` ; isoler `engine/`+`ve_adapter/` sous `tools/` avec un `README` « outillage, pas produit ».
- **M-GOD** — Découper `excel_report.py` (7 027) par feuille/section ; sortir `_collect_dynamic_results` de `app.py` vers `swiss_sia/dynamic_results.py` ; externaliser le blob `config.py` en fichiers de données tracés.
- **M-PUR** — Ajouter une garde locale unique qui parcourt **tous** les modules `engine/` (pas un par un), pour attraper une régression de pureté avant le push.

### P3 — Hygiène & data-handling
- **M-DATA** — `git rm --cached` sur `sia4010_evidence/*.csv`, `outputs/*.pptx`, `sia4010_artifacts/*.json` ; ajouter `sia4010_artifacts/` au `.gitignore` ; envisager une purge d'historique si les brouillons client sont sensibles.
- Supprimer les 4 fichiers scratch à nom de chemin Windows à la racine.
- Nettoyer les mineurs restants (locators, tolérances nues, `assign_hvac_if_configured`, mapping d'ouvertures).

---

## 10. Reproductibilité de l'audit

```powershell
python -m pytest                                  # 2305 tests, 0 échec (Python 3.13, iesve absent)
python -m unittest discover -s tests -p "test_*.py"
python scripts/quality/validate_release.py        # porte locale (voir C-REL)
git ls-files | wc -l                              # 740 fichiers suivis
```

Chiffres clés : 475 fichiers Python (hors `tmp/`), 156 fichiers de test, 91 lanceurs racine, `swiss_sia/` = 74 046 lignes, 0/7 matrices SIA 4010 signées, 2 sources SIA primaires commitées.

---

*Audit mené par une équipe de quatre auditeurs experts indépendants (fidélité normative, intégration IESVE, architecture, QA) et synthétisé par l'auditeur en chef. Aucun fichier de production modifié.*
