---
description: Déroule la Phase 0 (mise au sol) — inventaire, audit du code existant, décision d'archi, squelette de dépôt. S'arrête pour validation avant toute grosse écriture.
argument-hint: (optionnel) chemin du code existant à auditer, ex. ./ ou legacy/
---

Objectif : exécuter la Phase 0 de PROJECT_PLAN.md de façon sûre et traçable.
Procède par étapes et **n'écris rien de structurel avant mon feu vert explicite**.

## Étape A — Lecture des règles (aucune écriture)
Lis `CLAUDE.md` et `PROJECT_PLAN.md` en entier. Résume en 5 lignes la doctrine
(vérité = valeurs de référence, séparation dur/pur, traçabilité, signature QA).

## Étape B — Inventaire (aucune écriture)
1. Inventorie le dépôt : liste les fichiers existants (dont le code Codex en
   $ARGUMENTS ou à la racine s'il n'est pas précisé) et le contenu de `refs/`.
2. Pour `refs/` : dis précisément ce qui est présent et ce qui MANQUE parmi :
   SIA 380/2, SIA 4010, specs des 7 tests, Excel d'évaluation, bâtiment exemple,
   **doc de l'API IESVE**. Ne devine aucun contenu absent.

## Étape C — Audit de l'existant (délègue à qa-auditor)
Invoque le sous-agent `qa-auditor` pour auditer le code existant contre la
doctrine : pour chaque script/fonction, quel article de norme il prétend
implémenter, existe-t-il une valeur de référence qui le prouve, verdict
GARDER / CORRIGER / JETER. Écris le résultat dans `AUDIT.md`. C'est le seul
livrable écrit autorisé à cette étape.

## Étape D — Décision d'architecture (aucune écriture)
À partir de la doc API IESVE de `refs/` (si présente), propose la voie
d'hébergement du navigateur dans VEScripts et la surface utile du module `iesve`.
Si la doc est absente, dis-le et marque la décision comme BLOQUÉE.

## Étape E — Proposition de réorganisation + squelette (STOP AVANT ÉCRITURE)
Propose (sans exécuter) :
- la mise en quarantaine du code Codex jugé non réutilisable (ex. vers `legacy/`),
- le squelette de dépôt (`engine/`, `ve_adapter/`, `ui/`, `refs/reference-data/`,
  `traceability/`, `docs/`),
- une CI qui exécute les tests du moteur pur SANS VE.
**Arrête-toi ici et demande-moi de valider** avant de créer/déplacer quoi que ce soit.

## Rapport final
Termine par : ce qui est prêt, ce qui MANQUE (surtout la doc API et l'Excel de
référence), et ce qui a été marqué BLOQUÉ ou À VÉRIFIER. Pas de vernis : dis la vérité.
