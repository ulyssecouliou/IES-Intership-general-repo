# État des lieux — Projet de référence SIA 380/2

## Résumé exécutif

La spécification d'entrée du **projet de référence SIA 380/2** est un composant Python automatisé qui prépare la comparaison décisive requise par `# SIA 380/2:2022 7.2.5.2` : conformité globale si la demande d'énergie du projet **est inférieure** à celle du projet de référence. Le composant est **fonctionnel, testé et livré** ; il produit une spécification déterministe des substitutions à appliquer (enveloppe, fenêtres, infiltration, génération, usage). **Huit des quatorze familles d'entrées sont automatisées** ; six restent bloquées, soit faute de norme fournie (`# SIA 380` pour l'agrégation globale), soit faute d'API pour les exposer (`# SIA 387/4` pour l'éclairage), soit par choix d'archi (sonde VE réelle requise pour la ventilation). **Deux blocages strictement exécutables en aval** barrent un verdict client : l'unité de l'indice global SIA 380 (en attente) et un constructeur de modèle de référence VE (distinct, exige VE réel).

---

## Contexte normatif

- **Pathway décisif** : `# SIA 380/2:2022 7.2.5.2` — « la performance globale est respectée lorsque la valeur de projet selon le chapitre 6 est **inférieure** à la valeur limite ou à la valeur cible correspondante du **projet de référence** ». Verdict binaire, borne calculée, pas une constante SIA.
- **Lien vers la validation SIA 4010** : `# SIA 380/2:2022 6.2.2.1` — une méthode de calcul n'est admise que si elle « peut justifier d'une **validation selon SIA 4010** pour les systèmes considérés ». La conformité 380/2 **présuppose** donc une validation SIA 4010 de l'outil (IESVE/ApacheSim).
- **Composition du projet de référence** : `# SIA 380/2:2022 7.2.5.3` — géométrie, usage et climat identiques au projet ; **seules les données du Tableau 2** (enveloppe, génération, émission, consignes/gains SIA 2024) sont substituées.

---

## État des 14 familles d'entrées — Tableau 2 + Tableaux 3-9 (SIA 380/2:2022)

| # | Famille d'entrées | Source SIA | Statut | Débloqueurs / Cause blocage |
|---|---|---|---|---|
| **1** | Enveloppe opaque (U murs/toits/sols) | Tableau 3, p.36-37 | **AUTOMATISÉE** | Extraction VE des U-values (API ModelAnalyzer). Tests complets. |
| **2** | Fenêtres U + fraction cadre | Tableau 2, p.32-33 | **AUTOMATISÉE** | Extraction VE des U et frame_fraction (API OpeningData). Tests complets. |
| **3** | Vitrage g⊥ (valeur solaire) + τ (transmittance visible) | Tableau 2, p.32-33 | **AUTOMATISÉE** | Extraction VE de solar_factor (EN 410 prouvé) + visible_transmittance. Tests complets. |
| **4** | Infiltration (0,15 m³/(h·m²)) | Tableau 2, p.32-33 | **AUTOMATISÉE** | Extraction VE en m³/(h·m²) net. Unité stricte, pas d'extrapolation. Tests complets. |
| **5** | Refroidissement (EER générateur air) | Tableaux 5-9, p.38-39 | **AUTOMATISÉE** | Extraction VE capacité + EER (bandes ≤150 kW SIA codées). [CAVEAT] SN EN 14825 absent de `/refs` — équivalence SEER/SCoP VE non prouvée [TO VERIFY]. Tests complets. |
| **6** | Chauffage (SCOP pompe air-eau) | Tableaux 8-9, p.38-39 | **AUTOMATISÉE** | Extraction VE capacité + SCOP (bandes ≤150 kW SIA codées). [CAVEAT] SN EN 14825 absent — équivalence SCOP VE non prouvée [TO VERIFY]. Tests complets. |
| **7** | Émission convective + capacité illimitée | Tableau 2, p.32-33 | **AUTOMATISÉE** | Directive prescriptive SIA (valeur figurée, jamais comparée), résolue en statut REFERENCE_DIRECTIVE. Tests complets. |
| **8** | Consignes θ/φ + gains internes (A_p, M, p_Be, E_vm) — SIA 2024 identiques projet/référence | Tableau 2 → SIA 2024, `# 7.2.5.3` [TRACÉ] | **AUTOMATISÉE** | Données JSON SIA 2024:2021 figées en `/refs` ; `# 7.2.5.3` garantit l'identité projet/référence → aucune substitution différenciante. Tests complets. |
| **9** | Ponts thermiques (ψ=0, χ=0) | Tableau 2, p.32-33 | **NON AUTOMATISÉE** | **Cause** : API VEScripts ne les expose pas. Preuve : API review, no capability to readback ψ/χ per construction. |
| **10** | Ratio vitré (fg) + protections solaires | Tableau 2 + Tableau 10 + SIA 387/4 | **NON AUTOMATISÉE** | **Cause** : fg est **figée à référence SIA 2024** (projet doit la justifier, norme-analyst actif). Choix non-trivial, pas d'automatisation possible ici. |
| **11** | Puissance éclairage (pLi) + contrôles | Tableau 2 → SIA 387/4 | **NON AUTOMATISÉE** | **Cause** : norme SIA 387/4 (éclairage) **absente de `/refs`**. Table d'entrée SIA 387/4 Tableau 9/10 inaccessible. Bloqueur documentaire. |
| **12** | Ventilation (εV ; classes C/L2/L1 ; U_ahu) | Tableau 2 + Tableau 4 ; `# 7.1.1` → SIA 382/1 | **NON AUTOMATISÉE** | **Cause** : contexte NCM/UK (système centralisé, profil annuel), sonde VE réelle exigée. Architecture : composant distinct requis (ne dépend pas de ce module). |
| **13** | Photovoltaïque (puissance installée, rendement) | Tableau 2, p.32-33 | **NON AUTOMATISÉE** | **Cause** : référence SIA figée (10 W/m² SRE à 90 % rendement système). Valeur projet nécessite sonde VE. Architecture : composant distinct requis. |
| **14** | Indice global SIA 380 (agrégation/pondération annuelle) | `# SIA 380/2:2022 6.1.2`, délégué à **SIA 380** | **NON AUTOMATISÉE** | **Cause** : **norme SIA 380 absente de `/refs`**. Unité/définition de l'indice global inaccessible. Bloqueur normatif majeur (cf. §Blocages). |

---

## Détail des statuts

### Familles automatisées (8)

**Composants actifs, tests validés** :

- **Enveloppe, fenêtres, vitrage** (1-3) : extraction déterministe des U et propriétés depuis le modèle VE, pareille aux `# SIA 380/2:2022 Tableau 3, p.36-37` et `# Tableau 2, p.32-33`. Substitution directe, aucune interpolation.
- **Infiltration** (4) : substitution différenciante — valeur projet (max des zones, m³/(h·m²) net, unité stricte) comparée à la référence `# SIA 380/2:2022 Tableau 2` de 0,15 m³/(h·m²). Une valeur projet dans une autre unité est un blocage de conversion, jamais substituée silencieusement.
- **Génération** (5-6) : capacité du projet détermine la bande de tableau SIA 5-9. EER/SCOP encodés, jamais extrapolés. **Caveat important** : SN EN 14825 (définition de SEER/SCOP) est absente ; les propriétés VE nommées `eer` et `scop` sont acceptées en l'état, équivalence non prouvée [TO VERIFY].
- **Émission + capacité** (7) : prescriptive SIA (pas de projet value), résolue en directive.
- **SIA 2024 — usage standard** (8) : `# SIA 380/2:2022 7.2.5.3` garantit que consignes, débits, gains de SIA 2024 sont **identiques** projet/référence. JSON SIA 2024:2021 figé en `/refs`. Pas de substitution différenciante (même si elle passe dans la spécification, elle n'affecte aucun delta).

**Tous testés** (`tests/test_reference_project.py`, classes `SurfaceSubstitutionTests`, `OpeningSubstitutionTests`, `InfiltrationSubstitutionTests`, `GenerationSubstitutionTests`, `ReferenceDirectiveTests`, `UsageStandardInputTests`).

### Familles non-automatisées (6)

**Causes et débloqueurs explicites** :

#### Ponts thermiques (9)
- **SIA 380/2:2022 Tableau 2, p.32-33** : ψ = 0 W/(m·K), χ = 0 W/K (limite et cible identiques).
- **Blocage** : API IESVE/VEScripts ne les expose pas (revue des capacités en amont).
- **Débloqueur** : extension API VEScripts pour readback ψ/χ par construction.

#### Ratio vitré + protections solaires (10)
- **SIA 380/2:2022 Tableau 2, p.32-33** : fg (fraction vitrée) figée à la **valeur de référence SIA 2024**.
- **Blocage** : fg est une donnée d'**exploitation** du projet (choix architectural, orientation, latitude, scénario été). Elle n'est pas libre : le projet doit la justifier. Norme-analyst actif pour cette décision.
- **Débloqueur** : décision de la voie de consigne (art. SIA 2024 ou simplifiée `# 5.2.2.6`) ; fg du projet est ensuite une justification métier, non une donnée d'API.

#### Éclairage (11)
- **SIA 380/2:2022 Tableau 2, p.32-33** : pLi (puissance nominale éclairage) et contrôles (catégories 4/2, commandes 2/3) → **SIA 387/4**.
- **Blocage** : norme **SIA 387/4 absente de `/refs`**. Table d'entrée éclairage non localisée.
- **Débloqueur** : acquisition SIA 387/4 (édition actuelle, chargée en `/refs`, parsing des Tableaux 9-10).

#### Ventilation (12)
- **SIA 380/2:2022 Tableau 2 + Tableau 4, p.32-33 et p.37 ; `# 7.1.1` → SIA 382/1**.
- **Blocage** : conception système (efficacité εV, classes d'étanchéité C/L2/L1, U_ahu). Contexte NCM/UK (réseau centralisé) requiert sonde VE réelle (air_handler.efficiency, duct_classes, annual_profile).
- **Débloqueur** : composant VE distinct pour ventilation (indépendant de ce module). Exige VE réel.

#### Photovoltaïque (13)
- **SIA 380/2:2022 Tableau 2, p.32-33** : puissance installée nominale, rendement système.
- **Blocage** : valeur **référence figée** (10 W/m² SRE, rend. 90 %). Valeur projet nécessite sonde VE (toiture, inclinaison, ombrage, modèle panneaux).
- **Débloqueur** : composant VE distinct pour PV (indépendant de ce module). Exige VE réel.

#### Agrégation globale SIA 380 (14)
- **SIA 380/2:2022 6.1.2** : « l'agrégation en valeurs annuelles et la pondération s'effectuent **selon SIA 380** » (norme absente).
- **Blocage majeur** : **unité de l'indice de dépense d'énergie** (SIA 380/2:2022 6.1.4) non définie dans 380/2 (délégué SIA 380). Pas de kWh/m² fixe : c'est un indice pondéré calculé. Formule inconnue.
- **Débloqueur** : acquisition SIA 380 (édition actuelle, chargée en `/refs`, extraction formule/pondérations).

---

## Deux blocages strictement exécutables en aval

Le composant `swiss_sia/reference_project.py` produit une **spécification d'entrée**, jamais un verdict. Deux étapes aval restent **nécessaires** pour un verdict client exécutable :

### Blocage 1 : Unité de l'indice SIA 380 [EN ATTENTE NORMATIF]

**Description** : Le critère `# SIA 380/2:2022 7.2.5.2` compare deux indices : `indice_projet < indice_référence`. Ces deux indices sont construits per `# 6.1.4` (« indice de dépense d'énergie **selon SIA 380** »). Mais SIA 380 est **absente** (non fournie au 2026-08-14).

**Impact** : Impossible d'exprimer le verdict en unité/échelle compréhensible (kWh/m²/an ? points ? classe de consommation ?). La comparaison numérique est exécutable en code, mais **non communicable** à un client sans unité.

**Débloqueur** : Acquisition SIA 380 ; extraction formule d'agrégation/pondération. Task orthogonale au composant reference_project.

### Blocage 2 : Constructeur de modèle de référence VE [DÉPENDANCE ARCHITECTURE]

**Description** : Le composant `reference_project.py` produit une **spécification** (liste de substitutions). Reste à :
1. **Construire** le modèle VE de référence (copier le projet + appliquer les substitutions Tableau 2).
2. **Lancer** la simulation VE/ApacheSim (run d'énergie).
3. **Extraire** la demande d'énergie (indice SIA 380 du projet de référence).

Ce constructeur est un **composant distinct**, nécessite une **sonde VE réelle** (IESVE.exe ou VEScripts.IVEProject), et échappe à ce module (pure Python).

**Impact** : Sans ce constructeur, le run de référence ne sera pas lancé automatiquement. Même avec une spécification complète, le verdict SIA 380/2 reste bloqué.

**Débloqueur** : Développement du composant VE-builder (hors scope du moteur pur `engine/`). À placer en `ve_adapter/` ou UI-script dédié.

---

## Réserves documentées

### Caveat SN EN 14825 — Définition SEER/SCOP

`# SIA 380/2:2022 Tableaux 5-9, p.38-39` spécifient EER (air chiller <150 kW) et SCOP (pompes air-eau ≤150 kW) selon **SN EN 14825** (édition non déterminée ici), standard absente de `/refs`.

**Conséquence** : Les grandeurs nommées `eer` et `scop` dans le modèle VE sont acceptées *in extenso*. Aucune vérification d'équivalence entre :
- Définitions SN EN 14825 (normes EN).
- Implémentation IESVE/ApacheSim.

**Marqué** : `[TO VERIFY]` dans le code, inscrit dans la source de chaque substitution SCOP de génération (`reference_project.py`, `_generation_substitution`).

### Licence des données SIA

Les fichiers `sia-2024-2021.usage-data.json` et tableaux SIA 380/2 codés en `config.py` sont fournis sous **licence IES**. Aucune rediffusion ne dépasse l'usage interne du dépôt.

### Ces spécifications ne sont pas une conclusion de conformité

`# SIA 380/2:2022 7.2.5.1-7.2.5.3` : le projet de référence est un **calcul de borne** (la limite). La conformité ne découle que si :
1. Le **run projet** a été lancé (demande calculée, chapitre 6).
2. Le **run référence** a été lancé (demande de la borne, Tableau 2 appliqué).
3. Les deux ont été **comparés** (`indice_projet < indice_référence`).
4. Une **revue** gate a accepté le résultat (evidence_manager, qa-auditor).

La spécification `reference_project.py` = étape 1 de 4. Jamais un verdict seul.

---

## Résumé pour la hiérarchie

| Aspect | Statut |
|---|---|
| **Composant `reference_project.py`** | **Livré, testé, actif** — exporte une spécification déterministe. |
| **Automatisation famille / 14** | **8 / 14** — enveloppe, fenêtres, vitrage, infiltration, génération, émission, SIA 2024 usage. |
| **Obstacles API VEScripts** | **1** : ponts thermiques (ψ/χ non exposés). |
| **Obstacles normatifs documentaires** | **2** : SIA 387/4 (éclairage) + SIA 380 (indice global) absentes. |
| **Obstacles conception** | **3** : fg (choix client, norme-analyst) ; ventilation (sonde réelle) ; PV (sonde réelle). |
| **Verdict client exécutable ?** | **NON** — 2 blocages aval : (1) unité SIA 380 en attente ; (2) VE-builder distinct requis. |
| **Délai libération ?** | Dépend de (1) SIA 380 + (2) VE-builder + tests complets. Aucune dépendance technique sur reference_project.py. |

---

## Références

- `# SIA 380/2:2022 7.2.5` — Pathway B, comparaison projet/référence (pages PDF 33-35).
- `# SIA 380/2:2022 7.2.5.3` — Composition identique projet/référence, Tableau 2 substitué (page PDF 34).
- `# SIA 380/2:2022 6.1.2, 6.1.4` — Agrégation et indice global, délégué SIA 380.
- `# SIA 380/2:2022 6.2.2.1` — Exigence validation SIA 4010 (page PDF 25).
- `traceability/sia380-2-pathway.spec.md` — Analyse approfondie pathways SIA 380/2 (16 questions [TO VERIFY] listées).
- `swiss_sia/reference_project.py` — Implémentation des collecteurs de substitution (un par famille).
- `tests/test_reference_project.py` — suite couvrant surfaces, fenêtres, vitrage, infiltration, génération, directives et usage SIA 2024.

---

**Auteur** : Claude Code, pour revue hiérarchie IES  
**Date** : 2026-08-14  
**Audience** : Management, non-spécialistes code  
**Statut** : Traçable, honnête, lisible
