---
description: Passe de vérification indépendante — exécute les tests, vérifie la séparation dur/pur et l'état de la traçabilité.
allowed-tools: Bash, Read, Grep, Glob
---

Délègue au `qa-auditor` une vérification complète de l'état du projet :

1. Exécuter toute la suite de tests du moteur (`engine/tests/`) et rapporter les échecs.
2. Vérifier qu'aucun fichier de `engine/` n'importe `iesve` (séparation dur/pur).
3. Vérifier que chaque test SIA marqué "done" possède une matrice de traçabilité
   SIGNÉE et que chaque valeur de référence citée existe bien dans `/refs/`.
4. Lister tous les marqueurs `⚠ À VÉRIFIER` restants dans le code.
5. Produire un rapport de synthèse : ce qui est certifié, ce qui ne l'est pas.

Ne « répare » rien ici — c'est un contrôle en lecture. Signale, ne corrige pas.
