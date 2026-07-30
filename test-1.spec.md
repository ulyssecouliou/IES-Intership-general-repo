# Spec — Test SIA 4010 n° 1 : Tests de base de l'enveloppe du bâtiment

> Statut : **BROUILLON ANCRÉ**. Rédigé par `norm-analyst`.
> Sources en main : SIA 4010:2023 (intégral). Sources requises pour finaliser :
> spécification Test 1 du SIA + fichier d'évaluation Excel + EN ISO 52016-1:2017 §7.
> Provenance de chaque élément indiquée : `[SIA4010]` vérifié / `[STD]` connaissance
> standard à confirmer / `[REQUIS]` valeur à obtenir des fichiers manquants.

## 1. Objet
Vérifier que le moteur de simulation thermique dynamique reproduit correctement la
physique de l'enveloppe (transmission, inertie thermique, gains solaires par les
vitrages, infiltration/ventilation, flottement libre de la température) sur une
série de cas normalisés en cellule de test. C'est le socle : il ne fait intervenir
aucun système technique. `[SIA4010]`

## 2. Classes de validation concernées
Le Test 1 est requis dans **toutes les classes sauf la classe 5**. `[SIA4010 §4.5, tab. 63]`

| Classe | Tests requis | Test 1 requis ? |
|---|---|---|
| 1A | 1 + 2A | ✅ |
| 1B | 1 + 2 | ✅ |
| 2A | 1, 2A, 3A–F | ✅ |
| 2B | 1 à 3 | ✅ |
| 3 | 1, 4 à 6 | ✅ |
| 4A | 1, 2A, 3A–F, 4 à 7 | ✅ |
| 4B | 1 à 7 | ✅ |
| 5 | 7 | ❌ |

Conséquence produit : le Test 1 est le premier à implémenter (tranche verticale
Phase 1) car il conditionne 7 des 8 classes.

## 3. Référentiel normatif
- Cas de test = cellule de test selon **SN EN ISO 52016-1:2017, §7.2.2**, qui
  correspond à **ASHRAE 140:2017**. `[SIA4010 §4.2 tab. 62 ; Annexe A tab. 64, ligne 1]`
- Étendue : cas de base selon **EN ISO 52016-1:2017, chapitre 7, tableau 27** ;
  tests complémentaires de l'ASHRAE 140 possibles « si les aspects souhaités ne
  sont pas couverts ». `[SIA4010 tab. 64, ligne 1]`
- Module DPEB associé : **M2-2**. `[SIA4010 tab. 64]`
- ⚠ Question ouverte soulevée par la norme elle-même dans le tableau 64 :
  « **Coefficient de transfert thermique externe ?** » — voir §7 (incertitudes).

## 4. Grandeurs d'entrée (définition de la cellule de test)
La cellule de test ASHRAE 140 / EN ISO 52016-1 est une zone unique paramétrée. Jeux
d'entrée à reproduire à l'identique dans le modèle VE `[STD — à confirmer contre le
tableau 27 / la spec SIA]` :
- Géométrie de la zone (dimensions, orientation, surface vitrée sud).
- Constructions en variante **légère** et **lourde** (inertie), U et propriétés
  thermophysiques imposés.
- Propriétés du vitrage (transmission solaire, U).
- Apports internes imposés.
- Infiltration / renouvellement d'air imposé.
- Consignes de chauffage/refroidissement (cas « conditionnés ») ou absence de
  consigne (cas en **flottement libre**, « free-float »).
- Fichier météo imposé par le référentiel.
  ⚠ `[REQUIS]` identité exacte du fichier météo (le classique ASHRAE 140 utilise un
  jeu type ; EN ISO 52016-1 §7 peut imposer le sien). À figer depuis la spec.

## 5. Grandeurs de sortie contrôlées
Ensemble type des tests d'enveloppe `[STD — à confirmer contre tab. 27 + Excel]` :
- Besoin **annuel** de chauffage (par cas).
- Besoin **annuel** de refroidissement (par cas).
- **Puissance de pointe** de chauffage.
- **Puissance de pointe** de refroidissement.
- Cas en flottement libre : **températures horaires** de la zone (min, max, moyenne),
  y compris dates/heures des extrêmes.

Le mapping précis (liste exacte des cas × grandeurs) est donné par le fichier
d'évaluation Excel du SIA. `[REQUIS]`

## 6. Critère d'acceptation / tolérance
⚠ Point méthodologique important : l'ASHRAE 140 / EN ISO 52016-1 ne définit pas une
tolérance en pourcentage fixe. Le critère est que le résultat du candidat tombe
**dans la plage (min–max) des résultats des programmes de référence** fournie dans
le fichier d'évaluation. `[STD]` La ligne directrice confirme ce mode opératoire :
les résultats du candidat sont transférés dans le fichier d'évaluation qui produit
la comparaison aux résultats de référence. `[SIA4010 §2.5, §4.4]`

→ Le moteur (`engine/`) implémentera donc un test « valeur ∈ [borne_min, borne_max]
de la référence » par grandeur et par cas — **pas** un écart en % arbitraire. Les
bornes viennent de `[REQUIS]` le fichier d'évaluation.

## 7. Zones d'incertitude (à lever avant "done")
1. **Coefficient de transfert thermique externe** : convention à retenir (valeur
   constante vs variable selon le vent). Explicitement pointé comme question dans
   SIA 4010 tab. 64. Impacte directement les résultats en cellule de test. `[SIA4010]`
2. **Étendue exacte des cas** : sous-ensemble du tableau 27 d'EN ISO 52016-1 vs cas
   complémentaires ASHRAE 140. `[REQUIS]`
3. **Fichier météo** de référence exact. `[REQUIS]`
4. **Bornes de référence** (min–max par grandeur/cas). `[REQUIS — Excel d'éval]`
5. **Réglages ApacheSim/VE** à imposer pour respecter les conventions de la cellule
   (algorithme de convection de surface, distribution du rayonnement solaire
   intérieur, couplage au sol) — à cadrer avec `ve-adapter-engineer` une fois 1–4 levés.

## 8. Citations
- SIA 4010:2023 : §2.5 (documents de test), §4.2 tab. 62 (séquence), §4.4 (résultats),
  §4.5 tab. 63 (classes), Annexe A tab. 64 ligne 1 (caractérisation Test 1).
- SN EN ISO 52016-1:2017 : §7.2.2 (cellule de test), ch. 7 tab. 27 (cas de base).
- ASHRAE 140:2017 (équivalent référencé).

## 9. Fichiers à fournir pour passer de BROUILLON à SPEC FIGÉE
- [ ] Spécification du Test 1 (document SIA téléchargeable sur sia.ch/sia4010).
- [ ] Fichier d'évaluation Excel du Test 1 (bornes de référence).
- [ ] Idéalement EN ISO 52016-1:2017 §7 + tableau 27 (définition des cas).
