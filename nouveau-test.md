---
description: Déroule la boucle complète d'implémentation d'un test de validation SIA 4010 (spec → réf → moteur → adaptateur → UI → audit → doc).
argument-hint: [numéro du test SIA, ex. 1]
---

Implémente le Test SIA 4010 n° $ARGUMENTS de bout en bout, en respectant la
Definition of Done de `PROJECT_PLAN.md`. Orchestre les sous-agents dans l'ordre,
en attendant le livrable de chacun avant le suivant :

1. `norm-analyst` → `traceability/test-$ARGUMENTS.spec.md` (grandeurs, tolérances, citations).
2. `reference-data-engineer` → `/refs/reference-data/test-$ARGUMENTS.ref.json` (+ .md de source).
3. `validation-engine-engineer` → moteur + tests unitaires qui reproduisent la référence.
4. `ve-adapter-engineer` → extraction des grandeurs requises (+ fixtures si VE indispo).
5. `ui-engineer` → câblage du test dans le navigateur.
6. `qa-auditor` → `traceability/test-$ARGUMENTS.matrix.md`, SIGNÉE ou renvoyée.
7. `docs-writer` → entrée de doc.

Ne déclare le test "done" que si la matrice est signée. Rapporte à la fin :
ce qui est vérifié, ce qui reste incertain, ce qui a été marqué À VÉRIFIER.
