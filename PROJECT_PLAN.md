# SIA 4010 Validation Navigator pour IESVE — Plan de projet

> Objectif : un outil déployable dans VEScripts (VE de IESVE) qui vérifie les
> classes de validation SIA 4010 pour un modèle VE, avec une interface soignée
> et une documentation de qualité. Cible : MSP (Minimum **Sellable** Product)
> le plus vite possible, sans sacrifier la fiabilité.

---

## 1. Doctrine (à lire avant tout code)

Le risque n°1 de ce projet n'est pas de coder — c'est de produire des résultats
*faux mais crédibles*. C'est précisément le doute que tu as sur le travail Codex.
Toute l'organisation ci-dessous existe pour rendre le faux impossible à cacher.

Trois règles non négociables :

1. **La vérité vient des valeurs de référence publiées, jamais du modèle.**
   Chaque test SIA 4010 possède des résultats de référence (fichiers d'évaluation
   Excel du SIA ; pour le Test 1, les plages ASHRAE 140 / EN ISO 52016-1). Le
   moteur de validation n'est « correct » que lorsqu'il reproduit ces valeurs.
2. **Traçabilité clause → code → test.** Chaque contrôle implémenté cite l'article
   exact de SIA 380/2:2022, SIA 4010 ou de la norme EN concernée. Aucun contrôle
   « orphelin ».
3. **Séparation dur/pur.** La logique de validation est du Python **pur**,
   testable hors de VE, sans dépendance à `iesve`. L'accès à VE est isolé dans un
   adaptateur mince. On peut ainsi tester le moteur en CI, sans licence VE.

Rien n'est « fait » tant que l'agent `qa-auditor` n'a pas signé la matrice de
traçabilité correspondante.

---

## 2. Architecture cible (4 couches)

```
┌─ Couche 4 : NAVIGATEUR (UI) ──────────────────────────────┐
│  App web locale (HTML/JS) : Classes → Tests → grandeurs,   │
│  deltas vs référence, rouge/vert, drill-down, export.      │
└───────────────▲────────────────────────────────────────────┘
                │ JSON (résultats + verdicts)
┌─ Couche 3 : MOTEUR DE VALIDATION (Python pur) ────────────┐
│  Implémente la logique de chaque test + tolérances +       │
│  verdict par classe. 100% testable hors VE. Cite la norme. │
└───────────────▲───────────────────────▲────────────────────┘
                │ entrées normalisées     │ valeurs de référence
┌─ Couche 2 : ADAPTATEUR VE ─┐  ┌─ Couche 1bis : DONNÉES RÉF. ┐
│  VEScript via l'API `iesve`│  │  Excel d'éval SIA + specs   │
│  → JSON normalisé (modèle, │  │  → JSON figé, versionné.    │
│  systèmes, résultats .aps).│  └─────────────────────────────┘
│  ⚠ dépend des docs API.    │
└────────────────────────────┘
```

**Décision d'architecture bloquante (Phase 0)** : comment VEScripts héberge le
« navigateur ». Piste recommandée = le VEScript extrait les données puis **génère
et ouvre une app web locale** (permet une « très bonne interface », impossible
avec une GUI native VE). À confirmer dès réception des docs de l'API IESVE
(surface du module `iesve`, version Python embarquée, accès aux résultats `.aps`
/ ApacheHVAC).

---

## 3. Phases (séquençage, pas de dates fictives)

### Phase 0 — Fondations & mise au sol de la vérité *(court, prioritaire)*
- Ingestion de tous les référentiels dans le dépôt (`/refs`), figés et versionnés.
- **Audit du travail Codex existant** : inventaire honnête de ce qui existe,
  ce qui est juste, ce qui est à jeter. Livrable = `AUDIT.md`. (qa-auditor + norm-analyst)
- Trancher l'hébergement VEScripts à partir des docs API. (ve-adapter-engineer)
- Squelette de dépôt + CI qui exécute les tests du moteur pur **sans VE**.

### Phase 1 — Tranche verticale : Test 1 / Classe 1A de bout en bout *(le cœur du MSP)*
Le chemin le plus mince qui traverse les 4 couches et prouve tout le pipeline :
extraction VE → moteur → comparaison aux réf. ASHRAE 140 → affichage dans le
navigateur. Quand ceci marche, le squelette du produit existe.

### Phase 2 — Classes 1 & 2 complètes (Tests 2 & 3)
Protection solaire (SIA 387/4) + éclairage. Valeur la plus élevée et la plus
atteignable (confirmé : c'est ce que Lesosai a validé en premier).

### Phase 3 — Classes systèmes (Tests 4→6, puis 7)
Extraction ApacheHVAC, comparaisons EN 16798, puis le gros Test 7. Incrémental,
chaque test derrière une signature QA. **Point le plus dur à isoler tôt** : la
méthode PAC détaillée SIA 384/3 au pas horaire (ch. 3.4.3.5.2).

### Phase 4 — Durcissement & documentation
Packaging déployable dans VEScripts, guide utilisateur, note méthodologique avec
matrice de traçabilité complète, FAQ.

---

## 4. Équipe (sous-agents Claude Code) et répartition des modèles

| Agent (fichier) | Modèle | Mission | Pourquoi ce modèle |
|---|---|---|---|
| `norm-analyst` | **opus** | Lit SIA/EN, produit les specs machine-lisibles + tolérances + citations | Une mauvaise lecture de la norme coûte cher en aval |
| `qa-auditor` | **opus** | Vérifie l'implémentation contre la norme, tient la matrice de traçabilité | Indépendance = antidote au doute Codex |
| `ve-adapter-engineer` | **sonnet** | Couche `iesve` / extraction VEScript | Implémentation robuste |
| `validation-engine-engineer` | **sonnet** | Moteur pur + tests unitaires | Implémentation + rigueur test |
| `ui-engineer` | **sonnet** | Le « navigateur » (app web locale) | Front-end soigné |
| `reference-data-engineer` | **haiku→sonnet** | Parse Excel d'éval + specs → JSON | Mécanique ; monter en modèle si logique |
| `docs-writer` | **haiku** | Doc utilisateur & méthodo | Rédaction cadrée, peu coûteuse |

Politique : session principale (orchestrateur) sur **opus** mais tenue légère ;
implémentation déléguée à **sonnet** ; tâches mécaniques à **haiku**. Les
sous-agents s'exécutent dans leur propre contexte et peuvent tourner en
parallèle ; attention, un flux très « sous-agents » peut consommer ~7× les
tokens d'une session mono-thread — donc paralléliser le *travail indépendant*,
sérialiser les étapes à risque (extraction ↔ moteur ↔ audit).

---

## 5. Definition of Done (par test SIA)
Un test n'est livré que si TOUS ces points sont vrais :
- [ ] Spec machine-lisible produite par `norm-analyst` avec citations d'articles.
- [ ] Données de référence figées dans `/refs/reference-data/` (versionnées).
- [ ] Moteur pur implémenté + tests unitaires qui reproduisent la référence dans tolérance.
- [ ] Adaptateur VE extrait les grandeurs requises (ou stub documenté si VE indispo).
- [ ] Navigateur affiche le test avec deltas et verdict.
- [ ] Matrice de traçabilité mise à jour et **signée par `qa-auditor`**.
- [ ] Entrée de doc utilisateur ajoutée.
