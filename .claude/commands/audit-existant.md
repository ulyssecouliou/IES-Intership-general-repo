---
description: Audite le code existant (dont le travail Codex) contre les valeurs de référence de la norme.
argument-hint: [chemin ou module à auditer]
---

Lance un audit indépendant de : $ARGUMENTS

Délègue au sous-agent `qa-auditor`. Il doit :
1. Inventorier ce qui existe dans la cible.
2. Pour chaque fonction/module, identifier l'article de norme qu'il prétend
   implémenter (via `norm-analyst` si nécessaire).
3. Chercher une valeur de référence figée qui le prouve ; sinon, écrire un test
   qui le confronte.
4. Rendre un verdict par élément : GARDER / CORRIGER / JETER, avec justification.
5. Écrire le résultat dans `AUDIT.md`.

Ne réutilise aucun code non prouvé. En cas de doute, marque JETER.
