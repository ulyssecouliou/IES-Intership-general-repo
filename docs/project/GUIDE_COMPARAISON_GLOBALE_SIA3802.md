# Guide — la porte décisive de conformité SIA 380/2 (§ 7.2.5.2)

> **À qui s'adresse ce guide.** À la personne qui exploite le script d'analyse de
> modèle client et veut que le rapport puisse rendre un verdict **CONFORME**
> SIA 380/2. Il explique le seul levier que vous contrôlez : fournir la
> **comparaison globale projet / projet de référence** relue et acceptée.

---

## 1. Pourquoi le rapport n'affiche pas CONFORME tout seul

Les contrôles par composant du script (U des parois, vitrage, ventilation, gains,
consignes, CVC) sont des **diagnostics** : ils signalent des écarts aux entrées du
projet de référence, mais **ils ne décident pas de la conformité**. La norme
SIA 380/2:2022 tranche la conformité globale sur **une seule comparaison** :

> l'indice de dépense d'énergie du **projet** doit être **inférieur ou égal** à
> celui du **projet de référence** (SIA 380/2:2022 § 7.2.5.2).

Le script **ne calcule pas** cette comparaison automatiquement (le projet de
référence n'est pas simulé côté client). Tant qu'elle n'est pas fournie, le
domaine décisif reste `À déterminer` et le verdict global est `NOT_DETERMINED` —
**jamais** un faux CONFORME.

## 2. Les cinq conditions d'un verdict CONFORME

Le verdict `sia3802_status = COMPLIANT` exige **tout** ce qui suit
(`swiss_sia/compliance_verdict.py`) :

1. Au moins une pièce analysée.
2. Aucun constat **bloquant avéré** (CRITICAL/HIGH) dans les six domaines.
3. La comparaison globale ne **contredit pas** l'acceptation (projet ≤ référence).
4. **Aucun domaine `NOT_DETERMINED`** : chaque domaine évalué, sans un seul
   critère `Non vérifiable` / `MISSING` / `placeholder`.
5. La comparaison globale est présente et acceptée
   (`global_reference_comparison.status == "REVIEWED_RESULT_AVAILABLE"`).

Les deux leviers réels sont **(4)** — combler les entrées manquantes du modèle —
et **(5)**, objet de ce guide. Le panneau **« Pour atteindre un verdict
CONFORME »** en tête du tableau de bord HTML liste, à chaque exécution, ce qui
manque exactement.

> ⚠️ Certains critères restent `Non vérifiable` **par construction** tant que la
> source normative n'est pas acquise (p. ex. SN EN 14825 pour SEER/SCoP, ponts
> thermiques ψ/χ). Ils empêchent un CONFORME *total* mais ne rendent jamais le
> modèle `Non conforme` — c'est le garde-fou anti « faux mais crédible ».

## 3. Fournir la comparaison globale — pas à pas

1. Calculez l'indice SIA 380/2 du **projet** et celui du **projet de référence**
   (même métrique, même unité), et conservez le document de calcul. Deux voies :
   soit un calcul hors outil, soit l'outil qui **construit** le projet de
   référence à simuler (voir § 5).
2. Copiez le gabarit
   [`templates/SIA3802_global_reference_comparison_TEMPLATE.csv`](templates/SIA3802_global_reference_comparison_TEMPLATE.csv)
   dans le dossier `sia4010_evidence/` **à côté du modèle VE**, et renommez-le :

   ```
   SIA3802_global_reference_comparison_<LabelDuProjet>.csv
   ```

   `<LabelDuProjet>` = le nom du projet VE tel que l'outil le voit (nom de
   dossier `.mit`). Un suffixe qui ne correspond pas au projet actif est ignoré.
3. Remplissez la ligne (voir § 4). Une personne relit et **accepte** : c'est
   `review_status = accepted`.
4. Relancez `Run_VE_Swiss_Compliance.py`. Si les chiffres et l'acceptation sont
   cohérents, le domaine décisif passe à `Conforme` et — si les conditions 1-4
   sont réunies — le verdict global devient **CONFORME**.

## 4. Champs de la ligne (tous obligatoires pour l'acceptation)

L'acceptation est refusée si un seul champ manque ou ne correspond pas
(`swiss_sia/evidence_manager.py::_normalize_global_comparison_record`).

| Colonne | Valeur attendue | Rôle |
|---|---|---|
| `project_id` | le label du projet VE | rattache la ligne au projet actif |
| `comparison_scope` | `complete_sia3802_project` | atteste que la comparaison porte sur le projet **complet**, pas un composant |
| `comparison_metric` | `global_energy_expenditure_index_sia380` | la grandeur comparée est bien l'indice global SIA 380 |
| `project_value` | nombre | indice du projet |
| `reference_value` | nombre | indice du projet de référence |
| `unit` | p. ex. `MJ/m2a` | unité commune aux deux valeurs |
| `comparison_result` | `pass` | (ou `passed`/`compliant`/`accepted`) |
| `review_status` | `accepted` | (ou `approved`/`reviewed`/`signed`/`validated`) |
| `reviewer` | nom | qui a relu |
| `review_date` | date | quand |
| `source_document` | fichier de calcul | provenance (ou `source_reference`) |
| `notes` | libre | facultatif |

**Contrainte de sens (SIA 380/2:2022 § 7.2.5.2) :** `project_value ≤ reference_value`.
Si `accepted` est posé mais que `project_value > reference_value`, le rapport
lève l'alerte critique `SIA3802_GLOBAL_REFERENCE_DISCREPANCY` et devient
**Non conforme** : l'acceptation ne peut **jamais** contredire les chiffres.

## 5. Calculer l'indice de référence dans VE (voie alternative)

Le § 3 suppose que vous calculez l'indice du projet **et** celui du projet de
référence hors de l'outil. En alternative, l'outil sait **construire** le projet
de référence à partir des substitutions normatives, pour que vous n'ayez plus
qu'à **simuler** les deux modèles et lire les deux indices. Cette voie ne calcule
toujours **rien** toute seule : elle prépare le modèle de référence, vous lancez
ApacheSim, et un relecteur accepte la comparaison.

**Étape 1 — voir le spec et ce qui bloque.**
Ouvrez le projet client actif et lancez **`Run_VE_SIA3802_Reference_Spec_Dump.py`**
(lecture seule). Il écrit, à côté du projet, un JSON listant chaque substitution
(valeur projet, limite et cible de référence, source SIA) et surtout les
**blockers**. Statuts possibles du spec :
- `READY_FOR_REFERENCE_RUN` — toutes les familles substituables sont résolues.
- `BLOCKED_INCOMPLETE_INPUTS` — au moins une famille manque (surface non classée,
  valeur de référence non encodée, g_perp non prouvé…). **Résolvez chaque blocker
  dans le modèle** (classer la surface, exposer la valeur) avant de construire,
  sinon la référence est incomplète. Les familles hors périmètre outil restent à
  traiter à la main par le relecteur (voir le JSON `missing_input_families`).

**Étape 2 — construire le projet de référence (sur une COPIE).**
`Run_VE_SIA3802_Build_Reference_Model.py` **refuse** de muter un projet dont le
chemin ne contient pas `_TEST`, `_COPY` ou `_DISPOSABLE` — il ne touche **jamais**
l'original. Travaillez donc sur une copie du projet. Le script applique les
substitutions (infiltration, émission, capacité illimitée, génération SCoP/SEER,
enveloppe opaque, vitrage, frame fraction) **avec capability-check + readback**
immédiat ; toute famille dont le readback échoue est marquée `FAILED_READBACK` et
signalée — elle **n'est pas** silencieusement supposée appliquée. Le script ne
lance **pas** ApacheSim.

**Étape 3 — simuler les deux modèles.**
Lancez ApacheSim sur le **projet** et sur le **projet de référence** construit,
avec la **même météo** et les mêmes réglages, puis relevez l'**indice global
SIA 380** de chacun (même métrique, même unité).

**Étape 4 — reporter dans le CSV.**
Mettez les deux indices dans `SIA3802_global_reference_comparison_<projet>.csv`
(§ 4), faites relire/accepter, relancez `Run_VE_Swiss_Compliance.py`.

> ⚠️ **Ce n'est pas une qualification.** Un modèle de référence construit par API
> et simulé n'est pas une preuve certifiée : les `FAILED_READBACK`, les familles
> hors périmètre et l'acceptation relecteur restent des garde-fous obligatoires.
> `BLOCKED_INCOMPLETE_INPUTS` non résolu ⇒ la référence n'est pas déterministe.

## 6. Ce que ça ne fait pas

- Ça ne remplace pas un certificat : le rapport reste une **évaluation de
  preuves**.
- Ça ne concerne pas SIA 4010 : les classes de validation qualifient le
  **logiciel**, pas le bâtiment client, et n'apparaissent pas dans le rapport
  client (rapport interne séparé : `Run_VE_Swiss_Compliance_Internal_SIA4010.py`).
