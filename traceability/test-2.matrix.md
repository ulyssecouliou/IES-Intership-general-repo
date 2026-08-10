# Matrice de traçabilité — Test SIA 4010 n° 2

> ## Statut : **NON SIGNÉE**
>
> Motif bloquant : **0 liaison(s) sur 2** entre une grandeur du classeur et une variable de résultat VE. Aucune valeur candidate ne peut donc être produite, et aucune ligne de cette matrice ne porte de résultat reproduit.
>
> Ce document est **généré** par `scripts/build_traceability_matrix.py` : les grandeurs, les bandes et l'état des liaisons sont lus dans les référentiels figés et dans le code, jamais retapés. Une matrice rédigée à la main se périme au premier changement — et une matrice périmée affirme une couverture qui n'existe plus.
>
> **Le script ne signe pas.** La règle 5 demande une signature `qa-auditor` indépendante.

---

## 1. Ancrage normatif

| Élément | Valeur | Source |
|---|---|---|
| Classes de validation concernées | 1A, 1B, 2A, 2B, 4A, 4B | SIA 4010:2023, tableau 63 (p. 48) |
| Bâtiment / local | Testraum « ASHRAE 140 » selon EN ISO 52016-1:2017, ch. 7 | Spezifikation_Test2.pdf |
| Climat | SIA 2028 DRY normal, Zürich Kloten | idem |
| Objet du test | protection solaire — store toile (2A) et stores à lamelles avec régulations 1 à 3 de SIA 387/4:2017, tableau 9 | idem |
| Classeur d'évaluation | `SIA_4010_geteilter_Link/Test2/Resultaterfassung_Test2.xlsx` | SIA 4010:2023, §4.4 |

## 2. Critères

La spécification énonce **deux** critères, dans sa section *Testkriterien*.

### 2.1 Somme annuelle

- Formule appliquée : `moyenne ± MAX(ABS(programme − moyenne)), bornes incluses`
- Statut du critère : **ENONCE_DANS_LA_SPEC** — Spezifikation_Test2.pdf, Testkriterien : « Jahressumme der solaren Waermeeintraege oder der total transmittierten Strahlung : Mittelwert der Referenzprogramme +/- maximale Abweichung ». La formule appliquee ici est celle-la.
- Bandes figées : **8**

### 2.2 Distribution de fréquence

- Énoncé : Häufigkeitsverteilung : « muss im Streubereich der Referenzprogramme liegen » (Spezifikation_Test2.pdf, Testkriterien)
- Statut du critère : **CONFIRME_AUTORITE_2026-08-10**
- Motif : Les feuilles « Verteilung » sont des GRAPHIQUES : elles tracent les variantes de référence et le programme testé, sans calculer aucune bande. Aucune cellule du classeur ne définit le Streubereich d'une distribution. La clarification écrite du 2026-08-10 définit la règle : enveloppe min/max des programmes de référence, classe par classe.
- Distributions figées : **22**, sur **20** classes
- Les deux lectures du `Streubereich` sont calculées (`enveloppe_min_max`, `moyenne_plus_ecart_max`) et **aucune n'est retenue** : le moteur ne rend jamais de verdict conforme.

## 3. Grandeurs, bandes et chaîne d'extraction

| Grandeur (libellé du classeur) | Unité | Cas | Chaîne VE |
|---|---|---|---|
| `Jahresenergie solarer Wärmeeintrag` | kWh | 4 | candidat `Window solar gains` (RELEVE), à confirmer |
| `Jahresenergie total transmittierte Solarstrahlung` | kWh | 4 | cherché, **aucune variable ne correspond** |

## 4. Distributions de référence

| Cas | Grandeur | Classes | Programmes de référence |
|---|---|---|---|
| Alle | `Einstrahlung auf Fensterebene gesamt` | 20 | 4 |
| 2A | `Solarer Wärmeeintrag gesamt` | 20 | 6 |
| 2A | `Total transmittierte Solarstrahlung` | 20 | 7 |
| 2B | `Solarer Wärmeeintrag gesamt` | 20 | 4 |
| 2B | `Total transmittierte Solarstrahlung` | 20 | 5 |
| 2B | `Lamellenwinkel der Storen` | 20 | 6 |
| 2C | `Solarer Wärmeeintrag gesamt` | 20 | 5 |
| 2C | `Total transmittierte Solarstrahlung` | 20 | 6 |
| 2C | `Lamellenwinkel der Storen` | 20 | 6 |
| 2D | `Solarer Wärmeeintrag gesamt` | 20 | 4 |
| 2D | `Total transmittierte Solarstrahlung` | 20 | 5 |
| 2D | `Lamellenwinkel der Storen` | 20 | 6 |
| Diag 2 E1 | `Solarer Wärmeeintrag gesamt` | 20 | 6 |
| Diag 2 E1 | `Total transmittierte Solarstrahlung` | 20 | 7 |
| Diag 2 E2 | `Solarer Wärmeeintrag gesamt` | 20 | 4 |
| Diag 2 E2 | `Total transmittierte Solarstrahlung` | 20 | 5 |
| Diag 2 E3 | `Solarer Wärmeeintrag gesamt` | 20 | 6 |
| Diag 2 E3 | `Total transmittierte Solarstrahlung` | 20 | 6 |
| Diag 2 E4 | `Solarer Wärmeeintrag gesamt` | 20 | 6 |
| Diag 2 E4 | `Total transmittierte Solarstrahlung` | 20 | 6 |
| Diag 2 E5 | `Solarer Wärmeeintrag gesamt` | 20 | 6 |
| Diag 2 E5 | `Total transmittierte Solarstrahlung` | 20 | 6 |

> Totaux affichés dans les classes : 8432, 8567, 8617, 8666, 8728, 8732, 8744, 8750, 8755, 8759, 8760. La SIA a confirmé le 2026-08-10 que les écarts à 8760 ne sont pas des heures manquantes : les autres valeurs sont hors des bornes définies par les classes. Elles sont conservées comme compte hors classes et ne sont pas ajoutées à la dernière classe.
>
> Les effectifs sont des FAITS relevés cellule par cellule et réconciliés avec la ligne de totaux du classeur. La bande d'acceptation min/max par classe est confirmée par la réponse écrite du 2026-08-10.
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

1. **Aucune valeur candidate.** 0 liaison(s) sur 2 sont établies. Tant qu'elles ne le sont pas, aucun cas ne peut être évalué et le moteur les traite en `NOT_CHECKABLE` — ce qui est la vérité, mais ne vaut pas conformité.
2. **Aucune simulation.** Le test n'a jamais été construit ni simulé dans IESVE. Les bandes de référence sont vérifiées ; le comportement de VE face à elles ne l'est pas.
3. **La bande des distributions n'est pas définie.** Le classeur officiel ne la calcule nulle part. Deux lectures restent défendables et le choix appartient à la sous-commission SIA, pas à cet outil.
4. **1 grandeur(s) sans variable VE correspondante** sur le modèle sondé : `Jahresenergie total transmittierte Solarstrahlung`. Un modèle doté d'un réseau ApacheHVAC pourrait en exposer davantage — à vérifier avant de conclure.

---

## Signature

| Rôle | Nom | Date | Verdict |
|---|---|---|---|
| Producteur | `build_traceability_matrix.py` (généré) | — | non applicable |
| Vérificateur indépendant | `qa-auditor` | — | **non signé** |

