# Comparaison SEER froid — SIA 380/2 tableau 5 × SN EN 14825:2018

Statut : **voie A câblée** (SEER déclaré fabricant), **sous conditions tracées**.
Date : 2026-08-20. Avis : `norm-analyst` (session sia4010-evidence-hardening).
Réf. figée : `refs/reference-data/sn-en-14825-2018.cooling-seer.json`
(générée par `scripts/build_sn_en_14825_seer.py`).

## Décision
Un **SEER déclaré fabricant** (fiche ErP/Ecodesign) est comparé directement à la
**bande SEER minimale de SIA 380/2:2022 tableau 5** (p. PDF 38, colonne « SEER
selon SN EN 14825 »), sans caveat `[TO VERIFY]`. Règle :
`SIA3802_COOLING_SEER_MIN_DECLARED` (`swiss_sia/sia380_checker.py`), alimentée
par le CSV relecteur `SIA3802_cooling_generators_<projet>.csv` via
`_check_declared_cooling_seer`.

Un SEER **lu du modèle VE** (calcul interne non confirmé EN 14825) garde le
caveat : règle `SIA3802_COOLING_SEER_MIN`. Étanchéité vérifiée par norm-analyst.

## Périmètre (À CORRIGER appliqué)
La voie déclarée « propre » est **restreinte au tableau 5** : refroidisseur
**refroidi par air, < 150 kW** (SIA 380/2:2022 §7.2.5.4-5 ;
`SIA3802_COOLING_AIR_CHILLER_MAX_KW = 150`). Toute unité **water_cooled** ou
**≥ 150 kW** relève des tables 6/7 (la 7 est en **EER+**, pas un SEER) → verdict
`SIA3802_COOLING_SEER_DECLARED_OUT_OF_TABLE5_SCOPE` (NOT_CHECKABLE), jamais un
pass propre.

## Conditions à tracer au dossier pour l'unité concernée (Q1, interprétations)
1. La valeur est bien un **SEER** (froid confort, tous modes), pas SEERon ni EER.
2. C'est un SEER de **refroidissement de confort** (intérieur 27 °C BS / 19 °C BH),
   pas un **SEPR** (froid de process) ni un indice côté eau.
3. Classe et puissance = ligne du tableau 5 : **air-cooled, < 150 kW**.
4. Édition EN : réf. figée = **:2018** ; une fiche peut être calculée sous une
   autre édition. Points A/B/C/D et saison « average » réputés stables entre
   éditions côté froid → **[INTERPRÉTATION]** à tracer.
5. Bande de puissance sélectionnée depuis la **puissance nominale** de la fiche
   (Pdesignc).

Base « EN 14825 par construction » (Reg. UE 206/2012 ≤12 kW ; 2016/2281 confort
> 12 kW) = **savoir externe, hors refs/** → **[INTERPRÉTATION]**, pas une citation.

## Réserves ouvertes
- **Bandes `seer` du config vs PDF p.38** : norm-analyst n'a **pas** pu confronter
  le tableau 5 au PDF (poppler absent). → à faire relire par
  `reference-data-engineer` / `qa-auditor` sur `refs/SIA-380-2-2022.pdf` p.38.
- **Saison de refroidissement de référence (2 598 h)** : cross-check seulement
  auto-cohérent (somme = total transcrit) ; non confronté à une valeur EN 14825
  publiée indépendante. **Impact nul** sur le verdict (bins utilisés seulement en
  voie B — recalcul — non implémentée). **[À VÉRIFIER]** non bloquant.
- **SCoP chaud** : reste `[TO VERIFY]` (clause de calcul chaud EN 14825 non figée ;
  base climat/température des tables 8/9 non confirmée). Ne pas ouvrir un SCoP
  déclaré au même régime sans l'établir.

## Avant sign-off « done »
Matrice de traçabilité à signer par `qa-auditor` (relecture PDF p.38 + conditions
Q1 pour l'unité réelle du projet client).
