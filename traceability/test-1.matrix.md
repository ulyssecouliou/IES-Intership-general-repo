# Matrice de traçabilité — Test SIA 4010 n° 1

> ## Statut : **NON SIGNÉE**
>
> **28 contrôle(s) sur 28 ne sont pas évalués** : aucune simulation IESVE n'a produit de valeur candidate. Aucune ligne de cette matrice ne porte donc de résultat reproduit.
>
> Document **généré** par `scripts/build_traceability_matrix.py` : les grandeurs, les cas et leur état sont lus dans le moteur et dans les référentiels figés, jamais retapés. Le script **ne signe pas** — la règle 5 demande une vérification indépendante.

---

## 1. Ancrage normatif

| Élément | Valeur | Source |
|---|---|---|
| Classes de validation concernées | 1A, 1B, 2A, 2B, 3, 4A, 4B | SIA 4010:2023, tableau 63 (p. 48) |
| Bâtiment / local | Testraum « ASHRAE 140 » selon EN ISO 52016-1:2017, ch. 7 | Spezifikation_Test1.pdf |
| Climat | ISO 52016-1 DRYCOLD pour les six cas principaux ; SIA 2028 DRY Zürich Kloten pour les cas diagnostiques | idem |
| Objet du test | besoins de chaleur et de froid, températures opératives et charge de pointe horaire, sur la cellule d'essai | idem |

## 2. Critère

- Statut : **ÉNONCÉ DANS LA SPEC**
- Le Test 1 est le seul dont la spécification énonce ses propres critères ; ils ne sont pas inférés du classeur.

## 3. Cas et nature du contrôle

**3 entrée(s) sur 19 portent le critère pass/fail**, sur le(s) cas 1E. Les autres sont informatives : les présenter à égalité laisserait croire qu'elles décident du verdict.

| Grandeur | Cas | Nature du contrôle | Périodes | Évaluées |
|---|---|---|---|---|
| `annual_hourly_peak_load_kwh` | 1E | **critère pass/fail** (`critere_pass_fail`) | 2 | 0 |
| `operative_temperature_annual_extremes_celsius` | 600FF | informatif (`informatif`) | 3 | 0 |
| `operative_temperature_annual_extremes_celsius` | 900FF | informatif (`informatif`) | 3 | 0 |
| `operative_temperature_monthly_celsius` | 600 | informatif (`informatif`) | 13 | 0 |
| `operative_temperature_monthly_celsius` | 600FF | informatif (`informatif`) | 13 | 0 |
| `operative_temperature_monthly_celsius` | 640 | informatif (`informatif`) | 13 | 0 |
| `operative_temperature_monthly_celsius` | 900 | informatif (`informatif`) | 13 | 0 |
| `operative_temperature_monthly_celsius` | 900FF | informatif (`informatif`) | 13 | 0 |
| `operative_temperature_monthly_celsius` | 940 | informatif (`informatif`) | 13 | 0 |
| `sensible_cooling_demand_kwh` | 1E | **critère pass/fail** (`critere_pass_fail`) | 13 | 0 |
| `sensible_cooling_demand_kwh` | 600 | informatif (`informatif`) | 13 | 0 |
| `sensible_cooling_demand_kwh` | 640 | informatif (`informatif`) | 13 | 0 |
| `sensible_cooling_demand_kwh` | 900 | informatif (`informatif`) | 13 | 0 |
| `sensible_cooling_demand_kwh` | 940 | informatif (`informatif`) | 13 | 0 |
| `sensible_heating_demand_kwh` | 1E | **critère pass/fail** (`critere_pass_fail`) | 13 | 0 |
| `sensible_heating_demand_kwh` | 600 | informatif (`informatif`) | 13 | 0 |
| `sensible_heating_demand_kwh` | 640 | informatif (`informatif`) | 13 | 0 |
| `sensible_heating_demand_kwh` | 900 | informatif (`informatif`) | 13 | 0 |
| `sensible_heating_demand_kwh` | 940 | informatif (`informatif`) | 13 | 0 |

## 4. Chaîne logicielle

| Rôle | Fichier | Présent |
|---|---|---|
| adaptateur VE | `ve_adapter/test1_adapter.py` | oui |
| gbXML | `ve_adapter/gbxml_test1.py` | oui |
| géométrie | `ve_adapter/geometrie_test1.py` | oui |
| import + confrontation | `scripts/importer_geometrie_test1.py` | oui |
| moteur | `engine/test1_engine.py` | oui |
| référence figée | `refs/reference-data/test-1.ref.json` | oui |
| vue du navigateur | `ui/verdict_view.py` | oui |

## 5. Ce qui n'est PAS établi

1. **Aucune valeur candidate.** 28 contrôle(s) sur 28 restent non évalués faute de simulation.
2. **Aucune simulation.** Le test n'a jamais été construit ni simulé dans IESVE.
3. **Les cas diagnostiques 1A à 1E sont hors de portée** : ils exigent le climat de Zürich-Kloten, absent du dépôt. Or le critère pass/fail repose entièrement sur le(s) cas **1E** — sans eux, aucun verdict formel du Test 1 n'est possible.

---

## Signature

| Rôle | Nom | Date | Verdict |
|---|---|---|---|
| Producteur | `build_traceability_matrix.py` (généré) | — | non applicable |
| Vérificateur indépendant | `qa-auditor` | — | **non signé** |

