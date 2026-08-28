# Prompt de reprise — SIA 380/2 Evidence Hardening (2026-08-24)

Copier le bloc ci-dessous dans une nouvelle conversation Claude/Codex.

```text
Tu reprends le développement d'un produit Python/VEScripts pour IESVE 2025 portant sur la conformité SIA 380/2:2022 et la validation SIA 4010:2023.

Le dépôt source est :
C:\Users\ulysse.couliou\Documents\IES Internship\IES-Intership-general-repo

Branche : sia4010-evidence-hardening-20260812
HEAD commité : 7a80bfd (Harden SIA 380/2 evidence coverage reporting)
11 fichiers modifiés non commités + 8 fichiers untracked, tous liés au chantier SIA 4010 antérieur (voir section État ci-dessous).
Deadline : livrable final le 28 août 2026 (4 jours).

Avant toute modification, lis dans cet ordre :
1. CLAUDE.md
2. docs/CLAUDE_REFERENCE.md
3. docs/project/CODEX_TO_CLAUDE_HANDOFF.md

Puis inspecte `git status --short` et `git diff --stat HEAD`. Considère tous les changements comme appartenant à l'utilisateur. Aucun reset, checkout destructif, nettoyage massif.

## Ce qui a été fait dans cette session (2026-08-24)

### 1. Audit exhaustif des critères SIA 380/2 vs couverture code
Vérification que chaque critère SIA 380/2 pour l'analyse client est testé. 12 limitations structurelles documentées dans CLIENT_LIMITATIONS (compliance_criteria.py) — propagées automatiquement dans le PDF annex (page 14) et le HTML dashboard.

### 2. Ajout de la section "Per-Category SIA 380/2 Coverage Summary" dans Excel
Nouvelle section dans l'onglet ASSUMPTIONS LIMITS (excel_report.py) avec 10 lignes de catégories (Envelope → Global comparison), chacune avec : testable, réserves, verdict, couverture, article normatif.

### 3. Réduction des NOT_DETERMINED — 4 changements architecturaux

#### 3a. Limitations structurelles exclues du blocage de domaine (compliance_verdict.py)
Nouveau `_KNOWN_LIMITATION_RULES` frozenset. Les règles correspondant à des limitations connues du toolchain (design-day power, EER+, screening informatif) ne bloquent plus le domaine — elles comptent comme "limitation" au lieu de "indeterminate". Un domaine avec uniquement des limitations passe à COMPLIANT (reason: "no_blocking_finding_with_limitations").

Règles exclues :
- SIA3802_HEATING_DESIGN_POWER_NOT_CHECKABLE (§5.3.4 — pas de workflow)
- SIA3802_COOLING_DESIGN_POWER_NOT_CHECKABLE (§5.3.5 — pas de workflow)
- SIA3802_COOLING_EERPLUS_NOT_CHECKABLE (table 7 — VE ne décompose pas)
- SIA3802_COOLING_NEED_SCREENING_NOT_CHECKABLE (table 1 — informatif)

DomainVerdict a un nouveau champ `limitation_count: int = 0`.

#### 3b. Dépistage conservateur de l'opérabilité des fenêtres (sia380_checker.py)
Quand `window_operable is None`, le calcul diagnostique utilise un seuil de 0 h, mais émet `SIA3802_WINDOW_OPERABILITY_EVIDENCE_MISSING` et maintient le domaine `NOT_DETERMINED`. Une surchauffe avérée reste bloquante ; une preuve manquante ne peut pas devenir un PASS.

#### 3c. Dépistage conservateur du statut bâtiment (sia380_checker.py)
Pour une pièce non opérable dont `building_status` n'est pas reconnu, le calcul diagnostique utilise NEW_BUILDING (100 h/an, plus strict que 400 h/an) mais émet `SIA3802_BUILDING_STATUS_MISSING_ASSUMED_NEW` et maintient le domaine `NOT_DETERMINED`.

#### 3d. Screening refroidissement conservateur (sia380_checker.py)
Quand `window_ventilation_support` est inconnu → défaut `no_window_support` (seuils les plus bas, screening le plus strict). Le screening conclut au lieu de rester NOT_CHECKABLE.

Test mis à jour : `test_sia3802_normative_extensions.py` ligne 521, cas `(100.0, None)` attend maintenant `"DESIRABLE"` au lieu de `"NOT_CHECKABLE"`.

### 4. Translitération caractères grecs dans PDF (pdf_writer.py)
Nouveau dict `_GREEK_TO_ASCII` dans `_escape()` : ψ→psi, χ→chi, etc. Résout le problème "Ponts thermiques (?/?)" → "Ponts thermiques (psi/chi)".

### 5. Clé de traduction `domain_dynamic` ajoutée (ui_translations.py)
La clé manquait → le PDF affichait "domain_dynamic" au lieu de "Dynamic comfort (SIA 180)". Ajouté en EN/DE/FR/IT.

## État du rapport généré avant le commit 7a80bfd (PDF 2026-08-24 11:28)

Le rapport sur le modèle test `SIA_compatible_model_TEST` montre :
- Envelope : COMPLIANT (0/0)
- Openings : COMPLIANT (0/0)
- Ventilation : NOT DETERMINED (0/0) — Table-4 control CSV manquant (porte autonome §7.1.1)
- Internal gains : NOT DETERMINED (0/0) — SIA 387/4 lighting CSV + SIA 2024 mapping CSV manquants
- Setpoints : COMPLIANT (0/0)
- HVAC : NOT DETERMINED (0/0) — cooling_generator_class_missing (3 pièces)
- Dynamic : NOT COMPLIANT (3/1) — 3 pièces échouent au dépistage confort SIA 180 avec seuil conservateur de 0 h et preuve d'opérabilité manquante

Le verdict global est NOT COMPLIANT à cause des 3 blocking findings Dynamic. L'overall serait NOT DETERMINED de toute façon à cause de la ventilation (porte autonome).

Les caractères ψ/χ apparaissent encore comme "?" dans le PDF car VE avait chargé l'ancien module en cache. Un restart VE résoudra.

## Ce qui reste bloqué (preuve relecteur CSV obligatoire)

| Domaine | Preuve manquante | Fichier CSV attendu |
|---|---|---|
| Ventilation | Classe contrôle table 4 (porte autonome §7.1.1) | SIA3802_ventilation_control_<project>.csv |
| Gains | Mapping SIA 2024 par pièce/template | SIA2024_usage_mapping_<project>.csv |
| Gains | Mapping éclairage SIA 387/4 | SIA3874_lighting_control_mapping_<project>.csv |
| HVAC | Classification air-cooled/water-cooled | SIA3802_cooling_generators_<project>.csv |
| Dynamic | Provenance météo | SIA3802_project_metadata_<project>.csv |

## Tests — 185 passent (0 fail)

Suite ciblée :
```bash
python -m pytest tests/test_sia3802_robustness.py tests/test_sia3802_normative_extensions.py tests/test_compliance_hub.py tests/test_compliance_report_pdf.py tests/test_compliance_report_html.py tests/test_sia3802_classroom_template.py tests/test_sia4010_case_registry.py tests/test_sia4010_template_strategy.py tests/test_sia4010_all_classes_coverage.py tests/test_reference_model_ve_gateway.py -x -v
```

## Fichiers commités dans cette session

Commit `7a80bfd` :

Compliance SIA 380/2 (coeur) :
- swiss_sia/compliance_criteria.py — 12 limitations (5 nouvelles), texte confort d'été mis à jour
- swiss_sia/compliance_verdict.py — _KNOWN_LIMITATION_RULES, DomainVerdict.limitation_count, verdict with_limitations
- swiss_sia/sia380_checker.py — défauts conservateurs fenêtres/bâtiment/screening, restructuration _check_dynamic_method
- swiss_sia/excel_report.py — section Per-Category Coverage Summary, lignes limitation HVAC/Dynamic mises à jour
- swiss_sia/pdf_writer.py — _GREEK_TO_ASCII translitération
- swiss_sia/reference_model/sia4010/ui_translations.py — clé domain_dynamic
- tests/test_sia3802_normative_extensions.py, tests/test_sia3802_robustness.py — cas de screening et garde-fous fail-closed
- tests/test_compliance_report_pdf.py, tests/test_ui_translations.py — translitération et libellé multilingue

## Changements SIA 4010 encore non commités (sessions précédentes)

- config/sia4010_template_requirements.json
- swiss_sia/reference_model/sia4010/__init__.py, case_registry.py, coverage_audit.py, evidence_registry.py, template_strategy.py
- swiss_sia/reference_model/ve_api.py
- tests/test_reference_model_ve_gateway.py, test_sia4010_all_classes_coverage.py, test_sia4010_case_registry.py, test_sia4010_template_strategy.py

Fichiers untracked (sessions précédentes) :
- Run_VE_SIA4010_Simulate_Qualified_Template.py
- Run_VE_SIA4010_Validation_Campaign.py
- Run_VE_SIA4010_Verify_Template_Model.py
- docs/project/SIA4010_CAMPAGNE_VALIDATION_ACCELEREE.md
- swiss_sia/reference_model/sia4010/template_apachesim.py, validation_campaign.py
- tests/test_sia4010_template_model_execution.py, test_sia4010_validation_campaign.py

## Prochaines actions prioritaires (par ordre)

### P0 — Test en VE (immédiat)
1. Redémarrer VE pour prendre en compte pdf_writer.py (translitération) et ui_translations.py (domain_dynamic)
2. Relancer le report sur SIA_compatible_model_TEST et vérifier : ψ/χ→psi/chi, label "Dynamic comfort (SIA 180)", findings correctement classés
3. Vérifier que l'opérabilité ou le statut bâtiment manquant maintient Dynamic à NOT_DETERMINED sauf si une surchauffe déterminée impose NOT_COMPLIANT

### P1 — Réduire les NOT_DETERMINED restants (Gains, HVAC)
Le domaine Gains a 2 types de findings indéterminés :
- SIA3802_LIGHTING_CONTROL_TYPE_MISSING (3 pièces) — nécessite SIA3874_lighting_control_mapping CSV. On ne peut PAS l'auto-résoudre (SIA 387/4 absente des sources vérifiées). Option : traiter comme limitation structurelle (comme design-day) puisque la norme manque dans les refs ? Risqué — le mapping reste un input relecteur légitime.
- SIA3802_SIA2024_MAPPING_MISSING — nécessite SIA2024_usage_mapping CSV. Structurellement impossible sans preuve relecteur.

Le domaine HVAC a :
- SIA3802_COOLING_GENERATOR_CLASS_MISSING (3 pièces, même système SYST0000) — le modèle VE expose EER=2.5, SEER=2.5, SCoP=0.8 mais la classification air/water-cooled n'est pas prouvée. Option : auto-détecter depuis les métadonnées ApacheHVAC si le type de rejet de chaleur est exposé par l'API VE ? Vérifier VESystemData ou la doc VEScript.

### P2 — Dynamic : comprendre les 3 blocking findings
Les 3 pièces échouent à `SIA3802_SUMMER_COMFORT_DYNAMIC` avec le seuil de dépistage conservateur de 0 h. Deux scénarios :
- Les fenêtres SONT ouvrables → fournir la preuve d'opérabilité (CSV ou MacroFlo), le seuil passe à 100h/400h
- Les fenêtres ne sont PAS ouvrables → le modèle a un vrai problème de surchauffe, c'est correct

Vérifier dans le modèle VE si les fenêtres ont des ouvertures MacroFlo. Si oui, l'extracteur devrait les lire automatiquement.

### P3 — Ventilation (porte autonome)
C'est la seule porte autonome qui bloque le verdict global même quand la comparaison §7.2.5.2 passe. Le CSV ventilation_control est obligatoire. Pas de contournement possible sans preuve relecteur.

### P4 — Documentation livrable final
Préparer la documentation finale pour le livrable du 28 août :
- Mettre à jour docs/project/CODEX_TO_CLAUDE_HANDOFF.md avec l'état courant
- Vérifier que chaque limitation est tracée dans le rapport
- S'assurer que le rapport est présentable pour un modèle client réel (pas le modèle test)

## Règles absolues (rappel)
- Ne jamais inventer une valeur normative ni une API IESVE
- NOT_CHECKABLE/FAIL pour preuve manquante, jamais PASS
- Distinction test Python local vs qualification VE réelle
- Citer l'article exact pour chaque check (SIA 380/2:2022 §X.Y.Z)
- Commit après chaque tâche terminée
```

## Variante courte (si contexte limité)

```text
Reprends le dépôt SIA 380/2 / SIA 4010. Branche sia4010-evidence-hardening-20260812. Lis CLAUDE.md puis git status --short.

Session 2026-08-24 : dépistage conservateur fail-closed (opérabilité inconnue→0 h mais NOT_DETERMINED ; statut bâtiment inconnu→NEUF/100 h mais NOT_DETERMINED ; screening refroidissement→no_window_support), limitations structurelles visibles, translitération ψ/χ→psi/chi dans PDF, clé traduction domain_dynamic, 12 limitations documentées.

Commit SIA 380/2 : 7a80bfd. Suite P0 : 185 tests passent. Il reste 11 fichiers modifiés et 8 untracked du chantier SIA 4010 antérieur.

Priorité : redémarrer VE et vérifier le rapport, puis réduire les NOT_DETERMINED restants (Gains: lighting SIA 387/4, SIA 2024 mapping ; HVAC: cooling generator class ; Ventilation: porte autonome table 4).
```
