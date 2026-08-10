# Matrice de traçabilité — Test SIA 4010 n° 7

> ## Statut : **NON SIGNÉE**
>
> **11 contrôle(s) sur 11 ne sont pas évalués** : aucune simulation IESVE n'a produit de valeur candidate. Aucune ligne de cette matrice ne porte donc de résultat reproduit.
>
> Document **généré** par `scripts/build_traceability_matrix.py` : les grandeurs, les cas et leur état sont lus dans le moteur et dans les référentiels figés, jamais retapés. Le script **ne signe pas** — la règle 5 demande une vérification indépendante.

---

## 1. Ancrage normatif

| Élément | Valeur | Source |
|---|---|---|
| Classes de validation concernées | 4A, 4B, 5 | SIA 4010:2023, tableau 63 (p. 48) |
| Bâtiment / local | Bâtiment exemple | Spezifikation_Test7.pdf |
| Climat | SIA 2028 DRY normal, Zürich Kloten | idem |
| Objet du test | besoins de chaleur et de froid pour profils existants, production photovoltaïque comprise | idem |

## 2. Critère

- Statut : **CLASSEUR_CORRIGE_VERIFIE_2026-08-10**
- La specification du Test 7 ne definit aucun critere ; SIA 4010:2023 clause 4.4 delegue la comparaison au classeur d'evaluation, qui porte des bandes sur les seules Testgroessen. Le classeur corrige recu le 2026-08-10 a ete controle par checksum et lecture XML : la mise en forme conditionnelle compare bien la borne basse a la borne haute. Cette evaluation logicielle ne remplace pas l'attestation de la sous-commission.

## 3. Grandeurs

| Grandeur | Unité | Statut | Candidat |
|---|---|---|---|
| `Zugeführte elektrische Energie Kältemaschine` | kWh | NOT_CHECKABLE | — |
| `Total abgeführte Wärme` | kWh | NOT_CHECKABLE | — |
| `Hilfsenergie Kälteerzeugung` | kWh | NOT_CHECKABLE | — |
| `Aus Kälteerzeugung an die Wärmeseite gelieferte W.` | kWh | NOT_CHECKABLE | — |
| `Über Rückkühler abgeführte Wärme` | kWh | NOT_CHECKABLE | — |
| `Zugeführte elektrische Energie Wärmepumpe` | kWh | NOT_CHECKABLE | — |
| `Zugeführte Wärme der Wärmeerzeugung, Heizen` | kWh | NOT_CHECKABLE | — |
| `Zugeführte Wärme der Wärmeerzeugung, Warmwasser` | kWh | NOT_CHECKABLE | — |
| `Energie Heizkessel` | kWh | NOT_CHECKABLE | — |
| `Hilfsenergie Wärmeerzeugung` | kWh | NOT_CHECKABLE | — |
| `PV-Ertrag` | kWh | NOT_CHECKABLE | — |

- Source d'irradiance : `AUCUNE`

## 4. Chaîne logicielle

| Rôle | Fichier | Présent |
|---|---|---|
| moteur | `engine/test7_engine.py` | oui |
| référence figée | `refs/reference-data/test-7.ref.json` | oui |
| vue du navigateur | `ui/verdict_view.py` | oui |

## 5. Ce qui n'est PAS établi

1. **Aucune valeur candidate.** 11 contrôle(s) sur 11 restent non évalués faute de simulation.
2. **Aucune simulation.** Le test n'a jamais été construit ni simulé dans IESVE.
3. **La divergence de mise en forme conditionnelle est résolue.** Le classeur corrigé reçu le 2026-08-10 utilise `$N8` / `$M8`, soit `[borne basse ; borne haute]`. Son SHA-256 est `24937d8f421daa74a7f957025bfeb17a42fe2dc807b1a301a6752f4c0e808958` ; le contrôle XML et l'ancienne identité sont consignés dans `traceability/sia4010-authority-clarification-2026-08-10.json`.

---

## Signature

| Rôle | Nom | Date | Verdict |
|---|---|---|---|
| Producteur | `build_traceability_matrix.py` (généré) | — | non applicable |
| Vérificateur indépendant | `qa-auditor` | — | **non signé** |

