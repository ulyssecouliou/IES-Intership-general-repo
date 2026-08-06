# Matrice de traçabilité — Test SIA 4010 n° 4

> ## Statut : **NON SIGNÉE**
>
> Motif bloquant : **0 liaison(s) sur 3** entre une grandeur du classeur et une variable de résultat VE. Aucune valeur candidate ne peut donc être produite, et aucune ligne de cette matrice ne porte de résultat reproduit.
>
> Ce document est **généré** par `scripts/build_traceability_matrix.py` : les grandeurs, les bandes et l'état des liaisons sont lus dans les référentiels figés et dans le code, jamais retapés. Une matrice rédigée à la main se périme au premier changement — et une matrice périmée affirme une couverture qui n'existe plus.
>
> **Le script ne signe pas.** La règle 5 demande une signature `qa-auditor` indépendante.

---

## 1. Ancrage normatif

| Élément | Valeur | Source |
|---|---|---|
| Classes de validation concernées | 3, 4A, 4B | SIA 4010:2023, tableau 63 (p. 48) |
| Bâtiment / local | Bâtiment exemple, local « Hörsaal », 165,8 m2, sans fenêtre, sur deux niveaux | Spezifikation_Test4.pdf |
| Climat | SIA 2028 DRY normal, Zürich Kloten | idem |
| Objet du test | climatisation monozone à débit variable, récupération à plaques sans échange d'humidité (taux 0,75), régulation CO2 | idem |
| Classeur d'évaluation | `SIA_4010_geteilter_Link/Test4/Resultaterfassung Test4.xlsx` | SIA 4010:2023, §4.4 |

## 2. Critères

La spécification ne comporte **aucune** section *Testkriterien* : SIA 4010:2023 §4.4 délègue au classeur d'évaluation. Le classeur ne porte ni classes de fréquence ni feuille de distribution — la somme annuelle est donc le seul critère. C'est un constat, pas une lacune.

### 2.1 Somme annuelle

- Formule appliquée : `moyenne ± MAX(ABS(programme − moyenne)), bornes incluses`
- Statut du critère : **INFERE** — La specification de ce test n'enonce aucun critere ; SIA 4010:2023 clause 4.4 delegue la comparaison au classeur d'evaluation, qui porte les bandes. A confirmer par la sous-commission (clause 4.6.2).
- Bandes figées : **3**

### 2.2 Distribution de fréquence

**Sans objet pour ce test.** Le classeur ne porte ni feuille `Haeufigkeitsklassen` ni feuille `Verteilung`.

## 3. Grandeurs, bandes et chaîne d'extraction

| Grandeur (libellé du classeur) | Unité | Cas | Chaîne VE |
|---|---|---|---|
| `Energiebedarf Ventilatoren` | kWh | 1 | cherché, **aucune variable ne correspond** |
| `Wärmeabfuhr Luftkühler total` | kWh | 1 | candidat impossible — « total » suppose sensible + latent. VE les sépare en « Sys Mech vent cooling load » (sens |
| `Wärmezufuhr Lufterwärmer` | kWh | 1 | candidat `Sys Mech vent heating load` (RELEVE), à confirmer |

## 4. Chaîne logicielle

| Rôle | Fichier | Présent |
|---|---|---|
| adaptateur VE | `ve_adapter/bandes_adapter.py` | oui |
| extraction des distributions | `scripts/build_sia_distribution_reference.py` | oui |
| extraction des références | `scripts/build_sia_reference.py` | oui |
| moteur (distribution) | `engine/sia_distributions_engine.py` | oui |
| moteur (somme annuelle) | `engine/sia_bandes_engine.py` | oui |
| tests de l'adaptateur | `ve_adapter/tests/test_bandes_adapter.py` | oui |
| tests des références figées | `engine/tests/test_distributions_ref.py` | oui |
| tests du moteur (bandes) | `engine/tests/test_sia_bandes_engine.py` | oui |
| tests du moteur (distributions) | `engine/tests/test_distributions_engine.py` | oui |

## 5. Ce qui n'est PAS établi

1. **Aucune valeur candidate.** 0 liaison(s) sur 3 sont établies. Tant qu'elles ne le sont pas, aucun cas ne peut être évalué et le moteur les traite en `NOT_CHECKABLE` — ce qui est la vérité, mais ne vaut pas conformité.
2. **Aucune simulation.** Le test n'a jamais été construit ni simulé dans IESVE. Les bandes de référence sont vérifiées ; le comportement de VE face à elles ne l'est pas.
3. **1 grandeur(s) sans variable VE correspondante** sur le modèle sondé : `Energiebedarf Ventilatoren`. Un modèle doté d'un réseau ApacheHVAC pourrait en exposer davantage — à vérifier avant de conclure.

---

## Signature

| Rôle | Nom | Date | Verdict |
|---|---|---|---|
| Producteur | `build_traceability_matrix.py` (généré) | — | non applicable |
| Vérificateur indépendant | `qa-auditor` | — | **non signé** |

