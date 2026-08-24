# Guide des modifications VE — rendre un modèle client conforme SIA 380/2

Ce guide liste, critère par critère, **quoi modifier** pour lever les verdicts
`NOT_CHECKABLE` / `PARTIAL` d'un modèle client, avec **deux voies** :

- **Voie VE** — édition du modèle dans l'interface IESVE (améliore réellement le modèle).
- **Voie CSV** — évidence relecteur dans `sia4010_evidence/` (voie garantie, supportée par l'outil).

Les libellés de menus VE peuvent varier selon la version — vérifie-les à l'écran ;
les emplacements ci-dessous sont indicatifs (validés sur VE 2025.2).

> **Règle d'honnêteté.** Un critère ne passe **OK** qu'avec (1) de **vraies valeurs**
> (VE ou fiche fabricant) et (2) pour la voie CSV, `review_status=accepted` **signé
> par un relecteur**. Des valeurs d'exemple en `pending` restent `NOT_CHECKABLE` :
> c'est voulu — l'outil ne fabrique jamais de conformité.

Après chaque lot de modifications : relance **`Run_VE_Swiss_Compliance.py`** et
regarde le *tally* du manifeste évoluer.

---

## 0. Stratégie du bâtiment propre à chaque modèle

Avant de générer les rapports, ouvrir l'interface client avec
`Run_VE_Swiss_Compliance.py` et compléter le bloc **Stratégie du bâtiment** :

1. protections solaires extérieures / stores ;
2. fenêtres prévues ouvrables ;
3. refroidissement mécanique prévu ;
4. notes de conception : régulation, consignes et capacités réelles.

Ces valeurs sont enregistrées dans le projet VE actif sous
`.sia_compliance/client_report_context.json`. Deux modèles peuvent donc porter
des stratégies différentes. Les déclarations apparaissent dans les rapports,
mais ne remplacent jamais la lecture des objets VE, les résultats APS ni les
preuves relecteur. Une réponse `TO_CONFIRM` reste explicitement indéterminée.

---

## 1. Ponts thermiques ψ/χ — `SIA3802_THERMAL_BRIDGES`

**Lecture VE directe** (VE 2025.2 : `VESurface.get_thermal_bridges_non_repeating/_random`).
Le critère est **OK** dès qu'au moins une jonction a un ψ non nul ; l'outil calcule
`H_tb = Σ(ψ·L·flux) + Σ(χ·count)` en W/K. Les jonctions laissées à **ψ=0** sont
signalées (défaut non saisi possible) — à corriger pour ne pas sous-estimer.

**Voie VE** :
1. `Apache` → **Construction Database Manager** → onglet **Thermal Bridges**
   (ou le dialogue Thermal Bridges au niveau modèle).
2. Pour chaque **type de jonction à ψ=0** (linteau, tableau/jamb, allège/sill,
   mur-toiture, mur-refend…), saisis le ψ (W/m·K) depuis un **catalogue SIA** ou
   un calcul (ingénieur physique du bâtiment).
3. Sauvegarde. Contrôle avec le probe read-only
   `Run_VE_SIA3802_Probe_Thermal_Bridges.py` (liste chaque ψ + H_tb total).

**Voie CSV (repli, vieilles VE)** : `SIA3802_thermal_bridges_<projet>.csv`
(méthode + total ψ.L+χ W/K OU référence de schéma + reviewer + date + source).

---

## 2. Groupe froid — SEER — `SIA3802_COOLING_EER_SEER`

Autosize grise la capacité → la bande SIA 380/2 tables 5/6 ne se résout pas depuis
le modèle. Un **SEER déclaré** (fiche ErP/Ecodesign, SN EN 14825:2018) est comparé
proprement à la bande.

**Voie VE** :
1. `Apache` → **Apache Systems / ApacheHVAC** → générateur de froid (chiller).
2. **Désactive l'autosize** de la capacité → saisis la **capacité nominale (kW)**.
3. Si un champ **Seasonal EER / SEER** existe, saisis le SEER de la fiche
   (sinon → voie CSV).

**Voie CSV** : `SIA3802_cooling_generators_<projet>.csv`
- `generator_class` = `air_cooled` ou `water_cooled`
- `capacity_kw`, `seer` (fiche fabricant), `nominal_eer` optionnel
- `review_status` : `pending` → **`accepted`** (relecteur + date + source réelle)

**Seuils SEER (SIA 380/2:2022 tableaux 5 & 6, valeurs limites)** :

| Puissance kW | ≤12 | >12–50 | >50–150 | >150–450 | >450–1000 | >1000 |
|---|---|---|---|---|---|---|
| **Air** (Table 5) | 3,80 | 3,90 | 4,00 | 4,20 | 4,40 | — |
| **Eau** (Table 6) | — | 4,50 | 4,80 | 5,50 | 6,10 | 6,70 |

*(Refroidisseur à eau + refroidissement sec = Table 7 EER+, hors périmètre SEER.)*

---

## 3. AHU / récupération de chaleur — `SIA3802_AHU_HEAT_RECOVERY`

**Voie VE** :
1. `Apache` → **Apache Systems / ApacheHVAC** → l'**AHU**.
2. Sur l'**échangeur de récupération** : **rendement de température** (η, ex. 0,78),
   **type** (plaques / roue).
3. Renseigne **pertes de charge** et **SFP** si les champs existent.

**Voie CSV** : `SIA3802_ahu_heat_recovery_<projet>.csv`
(classe d'étanchéité + η récup = quantum Table 4 ; Δp et SFP optionnels ;
`pending` → `accepted`).

---

## 4. Contrôle de ventilation — `SIA3802_VENTILATION_CONTROL`

**Voie VE** :
1. `Apache` → système de ventilation de l'AHU (ou par pièce).
2. Renseigne **type de système** (monozone/multizone) + **stratégie de contrôle**
   (constant / à la demande / CO₂). Le tool lit les identifiants de contrôle de
   l'Apache system.

**Voie CSV** : `SIA3802_ventilation_control_<projet>.csv`
(type + classe de contrôle + tranche de débit ≤3 / 3-6 / >6 m³/h·m² ;
`pending` → `accepted`).

---

## 5. Protection solaire — `SIA3802_SOLAR_PROTECTION_CONTROL`

**Voie VE (recommandée)** :
1. `Apache` → **Construction Database Manager** → construction **vitrage** →
   sections **External / Internal / Local shade**.
2. Active un **store** (ex. store vénitien externe), renseigne ses propriétés
   optiques et le **g_total avec store**.
3. Attache une **stratégie de contrôle** (profil / seuil d'irradiance) aux fenêtres.

**Voie CSV** : `glazing_solar_protection_<projet>.csv`
(type + g_total + contrôle, par façade). ⚠️ Le crédit exige que les fenêtres
relues **couvrent toutes les fenêtres externes** vues par VE (sinon PARTIAL).

---

## 6 & 7. Hors d'atteinte par édition du modèle

- **Éclairage** — `SIA3802_LIGHTING_CONTROL` (PARTIAL) : bloqué par l'absence de
  **SIA 387/4** (source normative). Aucune édition VE ne le débloque tant que la
  norme n'est pas acquise.
- **Puissance de dimensionnement** — `SIA3802_DESIGN_POWER_DAYS` (NOT_AVAILABLE) :
  nécessite des simulations design-day dédiées + un développement outil (lecture
  des `.aps` des jours de dimensionnement). Pas une simple édition de modèle.

---

## Décisif vs diagnostic

La conformité SIA 380/2 se décide sur la **comparaison globale projet/référence
(§ 7.2.5.2)**, fournie et acceptée par un relecteur
(`SIA3802_global_reference_comparison_<projet>.csv`). Les critères ci-dessus sont
des **diagnostics** : ils enrichissent le dossier, mais ne décident pas seuls de la
conformité. Voir `docs/project/GUIDE_COMPARAISON_GLOBALE_SIA3802.md`.
