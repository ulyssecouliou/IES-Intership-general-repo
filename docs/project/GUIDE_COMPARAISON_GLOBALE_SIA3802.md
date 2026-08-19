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

1. Calculez, hors de l'outil, l'indice SIA 380/2 du **projet** et celui du
   **projet de référence** (même métrique, même unité), et conservez le document
   de calcul.
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

## 5. Ce que ça ne fait pas

- Ça ne remplace pas un certificat : le rapport reste une **évaluation de
  preuves**.
- Ça ne concerne pas SIA 4010 : les classes de validation qualifient le
  **logiciel**, pas le bâtiment client, et n'apparaissent pas dans le rapport
  client (rapport interne séparé : `Run_VE_Swiss_Compliance_Internal_SIA4010.py`).
