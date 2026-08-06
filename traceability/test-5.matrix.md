# Matrice de traçabilité — Test SIA 4010 n° 5

> ## Statut : **NON SIGNÉE**
>
> Motif bloquant : **0 liaison(s) sur 8** entre une grandeur du classeur et une variable de résultat VE. Aucune valeur candidate ne peut donc être produite, et aucune ligne de cette matrice ne porte de résultat reproduit.
>
> Ce document est **généré** par `scripts/build_traceability_matrix.py` : les grandeurs, les bandes et l'état des liaisons sont lus dans les référentiels figés et dans le code, jamais retapés. Une matrice rédigée à la main se périme au premier changement — et une matrice périmée affirme une couverture qui n'existe plus.
>
> **Le script ne signe pas.** La règle 5 demande une signature `qa-auditor` indépendante.

---

## 1. Ancrage normatif

| Élément | Valeur | Source |
|---|---|---|
| Classes de validation concernées | 3, 4A, 4B | SIA 4010:2023, tableau 63 (p. 48) |
| Bâtiment / local | Bâtiment exemple | Spezifikation_Test5.pdf |
| Climat | SIA 2028 DRY normal, Zürich Kloten | idem |
| Objet du test | ventilation mécanique : batteries chaude et froide, récupération, humidification (contact 5A-5C, vapeur 5D) | idem |
| Classeur d'évaluation | `SIA_4010_geteilter_Link/Test5/Resultaterfassung_Test5.xlsx` | SIA 4010:2023, §4.4 |

## 2. Critères

La spécification énonce **deux** critères, dans sa section *Testkriterien*.

### 2.1 Somme annuelle

- Formule appliquée : `moyenne ± MAX(ABS(programme − moyenne)), bornes incluses`
- Statut du critère : **ENONCE_DANS_LA_SPEC** — Spezifikation_Test5.pdf, Testkriterien : « Zulaessiger Bereich fuer Jahressummen : Mittelwerte der Referenzprogramme +/- maximale Abweichung ».
- Bandes figées : **16**

### 2.2 Distribution de fréquence

- Énoncé : Häufigkeitsverteilung : « muss im Streubereich der Referenzprogramme liegen » (Spezifikation_Test5.pdf, Testkriterien)
- Statut du critère : **NON_ETABLI**
- Motif : Les feuilles « Verteilung » sont des GRAPHIQUES : elles tracent les variantes de référence et le programme testé, sans calculer aucune bande. Aucune cellule du classeur ne définit le Streubereich d'une distribution. Deux lectures restent possibles — enveloppe min/max des programmes, ou moyenne ± écart maximal comme pour les sommes annuelles — et le choix ne peut pas être fait ici sans inventer le critère.
- Distributions figées : **16**, sur **20** classes
- Les deux lectures du `Streubereich` sont calculées (`enveloppe_min_max`, `moyenne_plus_ecart_max`) et **aucune n'est retenue** : le moteur ne rend jamais de verdict conforme.

## 3. Grandeurs, bandes et chaîne d'extraction

| Grandeur (libellé du classeur) | Unité | Cas | Chaîne VE |
|---|---|---|---|
| `Befeuchtungsenergie` | kWh | 1 | candidat `Sys Room humidification load` (RELEVE), à confirmer |
| `Energiebedarf Ventilatoren` | kWh | 2 | cherché, **aucune variable ne correspond** |
| `Hilfsenergie WRG` | kWh | 1 | cherché, **aucune variable ne correspond** |
| `Wärmeabfuhr Luftkühler latent` | kWh | 1 | candidat `Sys Mech vent dehum load` (RELEVE), à confirmer |
| `Wärmeabfuhr Luftkühler total` | kWh | 3 | candidat impossible — « total » suppose sensible + latent. VE les sépare en « Sys Mech vent cooling load » (sens |
| `Wärmezufuhr Lufterwärmer` | kWh | 4 | candidat `Sys Mech vent heating load` (RELEVE), à confirmer |
| `Wärmezufuhr WRG` | kWh | 2 | cherché, **aucune variable ne correspond** |
| `Wärmezufuhr WRG latent` | kWh | 2 | cherché, **aucune variable ne correspond** |

## 4. Distributions de référence

| Cas | Grandeur | Classes | Programmes de référence |
|---|---|---|---|
| *(non nommé)* | `Zu-/Abluft-Volumenstrom` | 20 | 4 |
| Test 5C | `Zulufttemperatur im Betrieb` | 20 | 5 |
| Test 5A | `Leistung Zu- und Abluftventilator` | 20 | 5 |
| Test 5C | `Leistung Zu- und Abluftventilator` | 20 | 5 |
| Test 5A | `Leistung Lufterwärmer` | 20 | 4 |
| Test 5B | `Leistung Lufterwärmer` | 20 | 4 |
| Test 5C | `Leistung Lufterwärmer` | 20 | 4 |
| Test 5D | `Leistung Lufterwärmer` | 20 | 4 |
| Test 5A | `Leistung Luftkühler total` | 20 | 4 |
| Test 5B | `Leistung Luftkühler total` | 20 | 4 |
| Test 5C | `Leistung Luftkühler total` | 20 | 4 |
| Test 5C | `Leistung Luftkühler latent` | 20 | 4 |
| Test 5B | `Leistung WRG` | 20 | 4 |
| Test 5C | `Leistung WRG` | 20 | 4 |
| Test 5B | `Leistung WRG latent` | 20 | 4 |
| Test 5C | `Leistung WRG latent` | 20 | 4 |

> Bloc(s) B : le classeur ne porte AUCUN identifiant de cas sur la ligne prévue. La spécification range ces grandeurs sous un cas précis, mais le classeur ne le dit pas : le champ reste nul plutôt que d'être comblé par déduction.
>
> Totaux horaires observés : 3380, 8738, 8739, 8744, 8747, 8751, 8752, 8753, 8758, 8759, 8760. Plusieurs programmes totalisent moins de 8760 heures. Ce sont des données réelles, reproduites telles quelles : les compléter à 8760 fausserait la dispersion.
>
> Totaux très partiels (3380) sur : Zulufttemperatur im Betrieb. Vraisemblablement une grandeur définie seulement pendant le fonctionnement de l'installation — à confirmer avant tout usage comme critère.
>
> Les effectifs sont des FAITS relevés cellule par cellule et réconciliés avec la ligne de totaux du classeur. La BANDE, elle, n'est pas établie : voir statut_critere.
>

## 5. Chaîne logicielle

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

## 6. Ce qui n'est PAS établi

1. **Aucune valeur candidate.** 0 liaison(s) sur 8 sont établies. Tant qu'elles ne le sont pas, aucun cas ne peut être évalué et le moteur les traite en `NOT_CHECKABLE` — ce qui est la vérité, mais ne vaut pas conformité.
2. **Aucune simulation.** Le test n'a jamais été construit ni simulé dans IESVE. Les bandes de référence sont vérifiées ; le comportement de VE face à elles ne l'est pas.
3. **La bande des distributions n'est pas définie.** Le classeur officiel ne la calcule nulle part. Deux lectures restent défendables et le choix appartient à la sous-commission SIA, pas à cet outil.
4. **4 grandeur(s) sans variable VE correspondante** sur le modèle sondé : `Energiebedarf Ventilatoren`, `Hilfsenergie WRG`, `Wärmezufuhr WRG`, `Wärmezufuhr WRG latent`. Un modèle doté d'un réseau ApacheHVAC pourrait en exposer davantage — à vérifier avant de conclure.

---

## Signature

| Rôle | Nom | Date | Verdict |
|---|---|---|---|
| Producteur | `build_traceability_matrix.py` (généré) | — | non applicable |
| Vérificateur indépendant | `qa-auditor` | — | **non signé** |

