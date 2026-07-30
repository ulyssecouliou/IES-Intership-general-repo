# SIA 4010 Validation Navigator (IESVE) — Scaffold Claude Code

Structure prête à l'emploi pour développer, dans Claude Code, un outil VEScripts
qui vérifie les classes de validation SIA 4010 pour des modèles IESVE.

## État Phase 0 (voir `PROJECT_PLAN.md`)
`refs/` contient à ce jour SIA 380/2:2022, SIA 4010:2023 et la doc API
VEScript/`iesve` (VE2023). **Manquent encore** : les spécifications des
tests 2 à 7 (seul le Test 1 a un brouillon dans `traceability/`), le ou les
fichiers d'évaluation Excel du SIA (aucune valeur de référence ne peut être
figée sans eux), le bâtiment exemple (Test 7), et les normes complémentaires
(387/4, 384/3, 385/2, EN 16798-x, ISO 52016-1). Le squelette de dépôt
(`engine/`, `ve_adapter/`, `ui/`, `refs/reference-data/`, `traceability/`,
`docs/`) est en place.

## Démarrage
1. Ouvre Claude Code à la racine, sur le modèle **opus** pour la session
   principale : `claude --model opus`.
2. Dépose dans `refs/` les référentiels encore manquants listés ci-dessus.
3. Enchaîne avec `/nouveau-test 1` pour lever les `[REQUIS]` du Test 1 puis
   dérouler la boucle complète (voir `PROJECT_PLAN.md`).

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
