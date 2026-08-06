---
name: figer-reference
description: Extrait les valeurs de référence d'un test SIA 4010 depuis son classeur d'évaluation officiel, recalcule les bandes de dispersion, les confronte au classeur, et fige le tout en JSON tracé. À utiliser pour tout nouveau test SIA (2 à 6), ou pour re-vérifier un test déjà figé.
argument-hint: [numéro du test SIA, ex. 5]
---

# Figer les références d'un test SIA 4010

Procédure éprouvée sur les tests 1 et 7. Elle évite de re-découvrir à chaque
fois les pièges du classeur SIA, qui sont toujours les mêmes.

## Résultat attendu

- `scripts/build_test<N>_reference.py` — extracteur reproductible
- `refs/reference-data/test-<N>.ref.json` — références figées
- Une sortie console qui montre chaque bande et confirme la concordance

## Étape 1 — Localiser et lire la disposition

Le classeur est
`$SIA_4010_DOSSIER/Test<N>/Resultaterfassung*Test<N>.xlsx`, avec
`SIA_4010_DOSSIER` par défaut à
`~/Documents/IES Internship/IES-Intership-general-repo/SIA_4010_geteilter_Link`.

La feuille de synthèse s'appelle `Zusammenfassung` (parfois
`Zusammenfassung Testfälle`). **Ne suppose jamais la disposition** : dumpe les
lignes 1 à 40, colonnes A à N, et lis.

Repères constants observés :
- une ligne porte les **noms des programmes** de référence (IDA ICE, Excel,
  Energy+/OpenStudio, EDSL Tas) ;
- trois colonnes portent `Mittelwert`, `Obere Grenze`, `Untere Grenze` ;
- une colonne porte l'unité ;
- les grandeurs se répartissent en **`Testgrössen`** (avec bande) et
  **`Diagnosegrössen`** (sans bande).

## Étape 2 — Les trois pièges, toujours présents

**Piège 1 — le jeu de contributeurs varie ligne par ligne.** Observé au Test 7 :
`M8` exclut `I8`, `M14` exclut `J14`. Un programme qui n'a pas livré une
grandeur **sort** de la bande et n'est jamais compté comme zéro.

Le jeu qui fait foi est celui de la liste `MAX(ABS(...))` de la borne haute,
**pas** la plage de l'`AVERAGE` : l'`AVERAGE` porte sur une plage `G:J` dont
Excel écarte les vides à l'évaluation — équivalent, mais illisible
statiquement.

**Piège 2 — des cellules gardent une formule inter-feuilles sans valeur en
cache.** `data_only=True` renvoie alors la formule en texte, du type
`='Daten EnergyPlus'!G6`. Résous-la par simple déréférencement. **Aucune
arithmétique** : si la cellule porte autre chose qu'une référence simple,
renvoie `None` et échoue bruyamment plutôt que de deviner.

**Piège 3 — le plancher à zéro est ponctuel.** Certaines bornes basses portent
`MAX(0, ...)`, d'autres non. C'est une propriété de la ligne, jamais du
critère. Ne l'applique **jamais** par défaut : lis la formule.

## Étape 3 — Recalculer et confronter

C'est le cœur de la procédure et ce qui donne sa valeur au fichier figé.

Pour chaque grandeur, recalcule la bande avec `engine.scatter_band.build_band`
sur les seuls contributeurs, puis **compare au trio `L/M/N` mis en cache par le
classeur**. Tolérance `1e-6`. Un seul écart : le script échoue.

C'est ce contrôle qui prouve que notre moteur reproduit le critère
d'acceptation du SIA. Sans lui, le JSON n'est qu'une recopie.

## Étape 4 — Ce que le JSON doit contenir

Outre les valeurs : la source (fichier, feuille, programmes, versions), la
**formule du critère lue verbatim**, le jeu de contributeurs **par grandeur**,
le drapeau de plancher **par grandeur**, et toute réserve connue.

Modèle de référence : `scripts/build_test7_reference.py` et
`refs/reference-data/test-7.ref.json`. Copie-les et adapte.

## Étape 5 — Le critère d'acceptation

**Seul le Test 1 énonce ses critères dans sa spécification.** Vérifie-le en
cherchant `kriterium|kriterien|streubereich|abweichung|toleranz` dans le PDF de
spec : pour les tests 4 et 7, zéro occurrence.

Quand la spec est muette, l'autorité est déléguée par **SIA 4010 §4.4** au
classeur d'évaluation. Le critère est alors **`INFERE`**, jamais normatif, et
cette mention doit être propagée partout où un verdict est produit.
Cf. `traceability/critere-test4.spec.md`.

## Règles non négociables rappelées

1. Aucune valeur inventée. Doute → `# ⚠ À VÉRIFIER` et remonter le point.
2. `engine/` reste du Python pur, sans `import iesve`.
3. Commentaires en français. Allemand **uniquement** pour les libellés qui
   servent de clés d'appariement avec le classeur — là, verbatim obligatoire.
4. Rien n'est « done » sans matrice de traçabilité signée par `qa-auditor`.
