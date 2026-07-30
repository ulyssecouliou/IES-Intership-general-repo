# CLAUDE.md — SIA 4010 Validation Navigator (IESVE)

Tu orchestres le développement d'un outil VEScripts qui vérifie les classes de
validation **SIA 4010** pour des modèles **IESVE**. Lis `PROJECT_PLAN.md` en
entier avant d'agir. Ce fichier fixe les règles que TOUS les agents suivent.

## Règles non négociables (fiabilité > vitesse)
1. **Ne jamais inventer une valeur, une tolérance, un article de norme, ni un
   symbole de l'API `iesve`.** Si tu ne l'as pas vérifié dans `/refs`, tu ne
   l'écris pas. En cas de doute : marquer `# ⚠ À VÉRIFIER` et lever le point,
   ne pas combler par supposition.
2. **Vérité = valeurs de référence publiées** (Excel d'éval SIA ; ASHRAE 140 pour
   Test 1). Le moteur n'est correct que s'il les reproduit dans la tolérance.
3. **Traçabilité obligatoire** : chaque contrôle cite son article
   (ex. `# SIA 380/2:2022, 5.2.2` / `# EN 16798-5-1:2017, tab. 11`).
4. **Séparation dur/pur** : `engine/` est du Python pur, zéro import `iesve`,
   testable en CI. Tout accès VE vit dans `ve_adapter/`.
5. **Rien n'est "done"** sans signature `qa-auditor` sur la matrice de traçabilité.

## Traiter l'existant (Codex) avec suspicion
Du code Codex peut exister. Ne lui fais aucune confiance a priori. Avant de
réutiliser une fonction : retrouver l'article de norme qu'elle prétend
implémenter, et écrire un test qui la confronte à la valeur de référence. Pas de
référence reproductible = à réécrire. Consigner dans `AUDIT.md`.

## Structure du dépôt
```
/refs/                 # référentiels FIGÉS (lecture seule) : SIA 380-2, SIA 4010,
                       #   specs de tests, Excel d'éval, docs API IESVE
/refs/reference-data/  # valeurs de référence extraites → JSON versionné
/engine/               # moteur de validation, Python PUR (pas d'iesve)
/engine/tests/         # tests unitaires : reproduisent les réf. -> vérité
/ve_adapter/           # VEScript + accès API iesve -> JSON normalisé
/ui/                   # le "navigateur" : app web locale
/traceability/         # matrice clause->code->test, par test SIA
/docs/                 # doc utilisateur + note méthodo
AUDIT.md               # audit de l'existant
PROJECT_PLAN.md        # plan (source de vérité du séquençage)
```

## Répartition des modèles
- Orchestrateur : **opus**, gardé léger.
- Interprétation norme & audit (`norm-analyst`, `qa-auditor`) : **opus**.
- Implémentation (`ve-adapter`, `validation-engine`, `ui`) : **sonnet**.
- Mécanique (`reference-data`, `docs`) : **haiku**, monter si logique.
Paralléliser le travail indépendant ; sérialiser extraction ↔ moteur ↔ audit.

## Boucle de travail par test SIA
1. `norm-analyst` → spec + tolérances + citations.
2. `reference-data-engineer` → réf. figées en JSON.
3. `validation-engine-engineer` → moteur + tests unitaires (doivent passer).
4. `ve-adapter-engineer` → extraction des grandeurs requises.
5. `ui-engineer` → câblage dans le navigateur.
6. `qa-auditor` → contrôle indépendant + signe la traçabilité.
7. `docs-writer` → entrée de doc.
Ne pas passer au test suivant tant que le courant n'est pas "done".

## Style
Français pour la doc et l'UI. Commentaires de code en français. Commits
atomiques référençant le test SIA concerné. Toujours dire ce que tu N'AS PAS
vérifié plutôt que de le masquer.
