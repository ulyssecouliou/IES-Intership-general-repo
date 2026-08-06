# SCHEMA.md — Contrat JSON de l'adaptateur VE, Test SIA 4010 n° 1

> Statut : **CONFIRMÉ** côté `ve_adapter/` pour la forme du candidat (lève le
> `⚠ À VÉRIFIER` laissé par `engine/test1_engine.py::evaluer_test1`, docstring).
> Reste `⚠ À VÉRIFIER` : le contenu physique de certains champs — cf. réserves
> renvoyées explicitement plus bas et dans `ve_adapter/test1_adapter.py`
> (docstring de module, sections « CE QUI N'EST PAS VÉRIFIÉ »).
>
> Ce document décrit UNE seule forme de JSON : le **candidat** produit par
> `ve_adapter/test1_adapter.py::extraire_candidat_test1()`. Il est le miroir
> structurel de `refs/reference-data/test-1.ref.json` (`reference_values`),
> mais avec des feuilles terminales scalaires au lieu de dicts par programme.
> Consommateur : `engine/test1_engine.py::evaluer_test1(reference, candidat)`.

---

## 1. Principe général

Le candidat est un dict Python (JSON) à quatre clés de premier niveau — une
par grandeur contrôlée du Test 1 — plus une clé `_provenance` optionnelle et
informative (ignorée par le moteur). **Chaque grandeur ne contient QUE les
cas pour lesquels elle est définie** (vérifié directement contre
`test-1.ref.json`, pas supposé) :

| Grandeur                                            | Cas présents                              |
|------------------------------------------------------|--------------------------------------------|
| `sensible_heating_demand_kwh`                         | `1E`, `600`, `640`, `900`, `940`            |
| `sensible_cooling_demand_kwh`                         | `1E`, `600`, `640`, `900`, `940`            |
| `operative_temperature_monthly_celsius`               | `600`, `640`, `900`, `940`, `600FF`, `900FF` |
| `operative_temperature_annual_extremes_celsius`       | `600FF`, `900FF`                            |

Un cas absent d'une grandeur (ex. `1E` absent de
`operative_temperature_monthly_celsius`, car la Table 30 de
`Resultaterfassung_Test1.xlsx` n'a pas de colonne pour 1E — AUDIT.md) est
**omis**, jamais représenté par `null`. Le moteur gère l'absence via
`candidat.get(grandeur, {}).get(cas)` → `None` → chaque période de ce cas est
évaluée avec `valeur_candidate=None` (`conforme=None`, motif explicite) —
aucune exception levée.

## 2. Feuilles terminales — forme scalaire

Chaque feuille terminale (une période : un mois, l'annuel, ou un extrême) est
soit :
- un nombre (`float`), soit
- `None` (grandeur non simulée / non disponible pour cette période).

**Jamais** un dict `{"value": ..., "unit": ..., "cell": ...}` (forme des
feuilles de *référence* dans `test-1.ref.json`, PAS celle attendue du
candidat). `engine/test1_engine.py::_valeur_candidate` accepte aussi cette
seconde forme par tolérance, mais l'adaptateur VE ne la produit jamais : la
forme scalaire brute est plus simple et suffisante.

## 3. `sensible_heating_demand_kwh` / `sensible_cooling_demand_kwh`

Cas : `1E`, `600`, `640`, `900`, `940` (Tables 28/29 de
`Resultaterfassung_Test1.xlsx` — pas de colonne pour 600FF/900FF, confirmé
contre `test-1.ref.json`).

```json
{
  "sensible_heating_demand_kwh": {
    "600": {
      "monthly": {
        "month_01": 1005.3, "month_02": 812.1, "...": "...", "month_12": 1120.4
      },
      "annual": 5134.0
    },
    "640": { "monthly": { "...": "..." }, "annual": 4780.2 },
    "900": { "monthly": { "...": "..." }, "annual": 4650.9 },
    "940": { "monthly": { "...": "..." }, "annual": 4402.1 },
    "1E":  { "monthly": { "...": "..." }, "annual": 2700.0 }
  }
}
```

- `monthly` : dict à exactement les 12 clés `month_01` … `month_12`
  (mêmes clés que `engine/test1_engine.py::MOIS`), énergie sensible
  **mensuelle** [kWh].
- `annual` : **frère** de `monthly` (PAS imbriqué dedans) — énergie sensible
  **annuelle** [kWh]. Convention différente de la Table 30 (§ suivant) :
  vérifiée contre `test-1.ref.json` où les Tables 28/29 exposent bien
  `annual` au niveau racine du cas (`AUDIT.md`, « remarques non
  bloquantes » pt 1).
- Unité : kWh — cohérente avec `test-1.ref.json` (`unit: "kWh"`).
- Signe : valeurs **positives** (énergie fournie), jamais négatives —
  cohérent avec le fait que ce sont des besoins de chauffage/refroidissement
  distincts (pas une puissance signée +chauffage/−refroidissement comme
  dans la Table 33/34 horaire, hors périmètre de ce contrat).

## 4. `operative_temperature_monthly_celsius`

Cas : `600`, `640`, `900`, `940`, `600FF`, `900FF` (Table 30 — pas de colonne
pour `1E`, confirmé : `test-1.ref.json` ne contient pas `1E` sous cette
grandeur ; `AUDIT.md`, § « Ce qui a été vérifié », pt 3).

```json
{
  "operative_temperature_monthly_celsius": {
    "600": {
      "monthly": {
        "month_01": 22.4, "...": "...", "month_12": 23.9,
        "annual": 23.3
      }
    },
    "600FF": { "monthly": { "...": "...", "annual": 25.1 } }
  }
}
```

- **`annual` est IMBRIQUÉ sous `monthly`** — contrairement à la section 3 !
  Ce n'est **pas une incohérence de l'adaptateur** : c'est le reflet
  volontaire de la structure déjà actée dans `test-1.ref.json` pour la
  Table 30 (`AUDIT.md`, « remarques non bloquantes » pt 1) et déjà gérée
  telle quelle par `engine/test1_engine.py::_perioder_temperature_
  mensuelle`. Ne PAS « corriger » cette asymétrie sans changer le moteur en
  même temps.
- Valeurs en °C — moyenne mensuelle/annuelle de la température opérative
  horaire (traceability/test-1.spec.md § 5, point 3).

## 5. `operative_temperature_annual_extremes_celsius`

Cas : `600FF`, `900FF` **uniquement** (Table 32 — cas en régime conditionné
non pertinents : la spec ne demande les extrêmes annuels que pour les cas en
flottement libre, traceability/test-1.spec.md § 5 point 7).

```json
{
  "operative_temperature_annual_extremes_celsius": {
    "600FF": { "extremes": { "max": 61.2, "min": -8.4, "average": 25.8 } },
    "900FF": { "extremes": { "max": 44.4, "min": -2.1, "average": 22.6 } }
  }
}
```

- `extremes.max` / `extremes.min` / `extremes.average` : les trois clés
  attendues par `engine/test1_engine.py::_perioder_extremes`, en °C, sur la
  série horaire annuelle complète (8760 valeurs) de température opérative.

## 6. Clé `_provenance` (optionnelle, informative)

Non lue par `evaluer_test1()` (ignorée : le moteur ne parcourt que les clés
présentes dans `reference['reference_values']`). Ajoutée par
`extraire_candidat_test1()` pour audit / traçabilité :

```json
{
  "_provenance": {
    "source": "ve_adapter.test1_adapter.extraire_candidat_test1",
    "liaisons_confirmees": false,
    "fichiers_aps": { "600": "chemin/vers/600.aps", "...": "..." },
    "annee_simulation": 2011
  }
}
```

- `liaisons_confirmees` : `true` seulement si l'appelant a fourni ses propres
  liaisons APS (confirmées contre une VE réelle), `false` si
  `LIAISONS_APS_CANDIDATES` (non confirmées, cf. § 7) a été utilisé avec
  `accepter_liaisons_non_confirmees=True`. **Tout consommateur de ce JSON
  (UI, rapport) doit afficher un avertissement visible si ce champ est
  `false`.**

## 7. Réserves qui accompagnent tout candidat réel (non levées par ce module)

Ces points ne sont **pas** résolus par la confirmation de forme ci-dessus —
ils portent sur le **contenu physique**, pas sur la structure JSON :

1. **Noms de variables APS non re-vérifiés dans cet environnement**
   (`LIAISONS_APS_CANDIDATES` dans `test1_adapter.py`, portés depuis un
   dépôt externe non consolidé — `IES-Intership-general-repo`). Toute
   extraction utilisant ces liaisons sans confirmation VE réelle doit être
   traitée comme **non qualifiée**, quelle que soit la validité de la
   *forme* du JSON produit.
2. **Coefficient de surface externe (Table 7-7 ASHRAE 140:2023)** —
   `traceability/test-1.spec.md` § 3.1/§ 8 pt 6 : le choix de branche
   dépend de l'algorithme de convection d'ApacheSim, non tranché.
3. **Valeurs numériques des matériaux légers/lourds** — statut
   `PUBLIC_REFERENCE` (présomption forte, pas une preuve), en attente de
   confirmation contre EN ISO 52016-1:2017 ch. 7 (absent de `/refs`).
4. **Vitrage et infiltration** — toujours `[REQUIS]`, aucune valeur fournie
   par ce module (`creer_infiltration()` refuse explicitement de deviner un
   taux).
5. **Grandeur manquante potentielle — charges de pointe horaires (Table 31),
   cas 1E.** Un audit parallèle (`AUDIT-swiss-sia-existant.md`, fichier non
   suivi par git au moment de la rédaction de ce document, élément n° 3) a
   trouvé, en exécutant `workbook_loaders.py` du dépôt externe contre
   `Resultaterfassung_Test1.xlsx`, que la Table 31 (« Test results Annual
   hourly integrated peak heating and cooling load », lignes 78-83, cas 1E
   uniquement) porte **elle aussi** un triplet `Mittelwert`/`obere Grenze`/
   `untere Grenze` — donc un **troisième critère pass/fail réel** pour 1E,
   non présent dans `refs/reference-data/test-1.ref.json` à ce jour et donc
   **absent du contrat candidat ci-dessus**. Ce contrat (§ 3-5) ne couvre que
   les quatre grandeurs demandées par la mission de cette étape ; si
   `reference-data-engineer` ajoute la Table 31 à `test-1.ref.json`, ce
   schéma et `extraire_candidat_test1()` devront être étendus d'une
   cinquième grandeur (ex. `annual_peak_load_kwh`, cas `1E` uniquement,
   feuilles `{"heating": <float>, "cooling": <float>}`) — non anticipée ici
   pour ne pas inventer une clé dont la référence figée n'existe pas encore.

Un candidat produit par `extraire_candidat_test1()` respecte donc le
**contrat de forme** ci-dessus de façon fiable, mais son exactitude
**physique** reste conditionnée aux quatre réserves ci-dessus — à lever
avant tout usage du verdict `evaluer_test1()` pour un rapport client.

## 8. Fixture de développement

`ve_adapter/fixtures/test1_candidat.exemple.json` respecte exactement ce
contrat. Il **n'est pas issu d'une simulation IESVE réelle** — généré à
partir de la moyenne des programmes de référence de `test-1.ref.json`,
volontairement perturbée (+2 % énergie, +0.3 °C température) pour rester
visuellement distinguable de la référence. Son champ `_provenance.source`
le rappelle explicitement (`"FIXTURE DE DÉVELOPPEMENT — AUCUNE SIMULATION
IESVE RÉELLE"`). Chargeable via
`ve_adapter/test1_adapter.py::charger_fixture_test1()`.

Vérifié par exécution réelle (ce document, session 2026-07-30) :
`evaluer_test1(charger_reference(), charger_fixture_test1())` s'exécute sans
exception, produit un `verdict_test1.conforme == True` pour le cas 1E (la
fixture reste dans la bande de dispersion recalculée, par construction), et
des comparaisons informatives exploitables pour tous les autres cas.
