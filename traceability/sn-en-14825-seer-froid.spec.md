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

## Périmètre (corrigé après lecture directe du PDF p.38)
**Vérification PDF faite** (PyMuPDF, 2026-08-20) : la page 38 confirme
**Tableau 5 (air)** ET **Tableau 6 (eau)**, tous deux avec une colonne
« valeur minimale SEER **selon SN EN 14825** » sur toute leur plage. Les bandes
`SIA3802_COOLING_EER_SEER_LIMITS`/`_TARGETS` correspondent **exactement** :
- Air (Table 5) limites EER/SEER : 2,90/3,80 · 3,00/3,90 · 3,10/4,00 · 3,20/4,20 · 3,40/4,40 ✓
- Eau (Table 6) limites EER/SEER : 4,05/4,50 · 4,25/4,80 · 4,65/5,50 · 5,05/6,10 · 5,50/6,70 ✓

**Réserve Q4 norm-analyst LEVÉE** : les bandes `water_cooled` viennent du
**Tableau 6 (vrai SEER)**, PAS du Tableau 7 (EER+). Le gate déclaré couvre donc
**air (Table 5) + eau (Table 6)**, pleine plage. Seul **l'unité eau à
refroidissement sec (Table 7, EER+)** ou un générateur **non classé** est hors
périmètre → `SIA3802_COOLING_SEER_DECLARED_OUT_OF_TABLE_SCOPE` (NOT_CHECKABLE).
La résolution de bande hors plage reste gérée par `_hvac_metric`
(BAND_NOT_CHECKABLE). Le commentaire config §GENERATION_REFERENCE (« eau ≥150 kW
= Table 7 ») concerne une **autre structure** (projet de référence), pas
`COOLING_EER_SEER_LIMITS`.

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
- ~~Bandes `seer` du config vs PDF p.38~~ **LEVÉE** (2026-08-20, PyMuPDF) :
  Tables 5 & 6 confrontées, valeurs identiques (voir « Périmètre » ci-dessus).
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
