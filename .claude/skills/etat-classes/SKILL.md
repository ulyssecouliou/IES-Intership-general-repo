---
name: etat-classes
description: Produit l'état d'avancement des huit classes de validation SIA 4010 — ce qui est acquis, ce qui bloque, et pourquoi. À utiliser dès qu'on demande « où en est-on », « que manque-t-il », ou avant un point avec la hiérarchie.
---

# État des classes de validation SIA 4010

Cette skill existe parce que la réponse a été reconstruite plusieurs fois à
grands frais. Elle fixe **où lire** plutôt que de re-fouiller le dépôt.

## Lire d'abord, dans cet ordre

1. `traceability/classes-de-validation.spec.md` — la matrice classe↔test issue
   du **tableau 63** de SIA 4010:2023, et l'état des bloqueurs. C'est la source
   de vérité ; si elle est périmée, mets-la à jour plutôt que de la contourner.
2. `refs/reference-data/` — quelles références sont figées.
3. `engine/` et `engine/tests/` — quels moteurs existent.
4. `ve_adapter/` — quels adaptateurs existent.
5. `traceability/*.matrix.md` — quelles matrices sont **signées**.

## La matrice qui fait foi — SIA 4010:2023 tableau 63

| Classe | Tests exigés | Protection solaire |
|---|---|---|
| 1A | 1 et 2A | tissu |
| 1B | 1 et 2 | lamelles |
| 2A | 1, 2A, 3A à F | tissu |
| 2B | 1 à 3 | lamelles |
| 3 | 1, 4 à 6 | — |
| 4A | 1, 2A, 3A à F, 4 à 7 | tissu |
| 4B | 1 à 7 | lamelles |
| **5** | **7 seul** | — |

**La classe 5 est la seule qui n'exige pas le Test 1** : c'est la plus facile,
et c'est par elle qu'on commence.

## Vérifier l'état réel, ne pas le supposer

Exécute et rapporte les **résultats réels** :

```bash
python -m pytest engine/ ve_adapter/ -q
```

Puis, pour chaque test dont le moteur existe, exécute-le sans candidat : il doit
renvoyer `NOT_CHECKABLE` partout, jamais un succès par défaut.

## Rendre compte en quatre blocs

**1. Acquis** — actif, source, état vérifié.

**2. État par classe** — tests exigés, données, logiciel, ce qui manque.

**3. Besoins restants** — séparer nettement :
- ce qui exige une **acquisition** (donnée qu'on n'a pas) ;
- ce qui exige un **téléchargement gratuit** ;
- ce qui ne dépend que de **notre code**.

**4. Actions** — ce que doit faire l'utilisateur, ce que je fais.

## Pièges à éviter dans la réponse

- **Ne jamais annoncer une classe validée** sans matrice de traçabilité signée,
  même si tous les nombres tombent dans les bandes. Règle 5 de `CLAUDE.md`.
- **Distinguer démonstration et validation formelle.** Reproduire les
  références est démontrable ; le verdict SIA exige la procédure complète du
  §4.6.2, sous-commission comprise.
- **Ne pas confondre climat d'application et climat de test.** SIA 4010 §3.1.1
  prescrit CH2018 RCP 8.5 « 2035 » pour *appliquer* SIA 380/2 dans un projet ;
  les sept spécifications de test demandent `SIA 2028 DRY normal, Zürich
  Kloten`. Les deux coexistent dans les mêmes documents.
- **Citer l'article** à chaque affirmation normative.
- **Dire ce qui n'a pas été vérifié** plutôt que de le masquer.
