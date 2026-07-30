# SIA 4010 Validation Navigator (IESVE) — Scaffold Claude Code

Structure prête à l'emploi pour développer, dans Claude Code, un outil VEScripts
qui vérifie les classes de validation SIA 4010 pour des modèles IESVE.

## Démarrage
1. Copie ce dossier à la racine de ton dépôt (garde `.claude/`, `CLAUDE.md`,
   `PROJECT_PLAN.md`).
2. Dépose les référentiels dans `/refs/` :
   - `SIA 380/2:2022`, `SIA 4010:2023` (+ 387/4, 384/3, 385/2 si dispo)
   - les spécifications des 7 tests + les fichiers d'évaluation Excel du SIA
   - le bâtiment exemple (DXF/IFC + charges du test 7)
   - **la documentation de l'API IESVE** (`iesve` / VEScripts)
3. Ouvre Claude Code à la racine, sur le modèle **opus** pour la session
   principale : `claude --model opus`
4. Première action recommandée :
   `/audit-existant <chemin de ton travail Codex>`
   puis laisse la Phase 0 se dérouler (voir `PROJECT_PLAN.md`).

## Commandes fournies
- `/audit-existant [cible]` — auditer le code existant contre la norme.
- `/nouveau-test [N]` — implémenter un test SIA de bout en bout.
- `/verifier` — passe de vérification indépendante.

## Équipe (sous-agents, dans `.claude/agents/`)
`norm-analyst` (opus), `qa-auditor` (opus), `ve-adapter-engineer` (sonnet),
`validation-engine-engineer` (sonnet), `ui-engineer` (sonnet),
`reference-data-engineer` (haiku), `docs-writer` (haiku).

## Note importante
Les définitions d'agents fichier sont chargées au démarrage : après édition d'un
fichier `.claude/agents/*.md`, redémarre Claude Code pour qu'elle soit prise en
compte. Le point d'architecture bloquant (hébergement de l'UI dans VEScripts,
surface de l'API `iesve`) se tranche en Phase 0 dès réception des docs API.
