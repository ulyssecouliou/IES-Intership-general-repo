# scripts/legacy — outils de génération historiques, À NE PAS RÉUTILISER TEL QUEL

Ces fichiers sont versionnés pour une seule raison : **ils sont la provenance
réelle de `refs/reference-data/test-1.ref.json`**, et sans eux cette provenance
n'est pas reproductible. Ils ne sont pas des outils du projet.

## Ce qu'ils sont

| Fichier | Rôle |
|---|---|
| `generate_corrected_ref.py` | a produit les corrections des Tables 30 et 32 après le défaut n°1 de l'audit |
| `update_json.py` | **écrit** `refs/reference-data/test-1.ref.json` |
| `inspect_extremes.py`, `inspect_zone3.py` | sondes ponctuelles d'inspection du classeur |
| `table_30_corrected.json`, `table_32_corrected.json` | intermédiaires produits par `generate_corrected_ref.py`, **jamais audités ni signés** |

Les deux `.json` vivaient dans `refs/reference-data/`, que `CLAUDE.md` déclare
« référentiels FIGÉS (lecture seule) ». Ils y étaient déplacés à tort : leur
contenu a été absorbé dans `test-1.ref.json`, qui est la seule référence
auditée. Ils sont conservés ici comme pièces d'historique.

## Pourquoi ils ne sont pas réutilisables

**Chemins absolus.** Sept occurrences de `C:\Users\ulysse.couliou\...` réparties
dans `generate_corrected_ref.py` (l. 5, 215), `update_json.py` (l. 7, 10, 246),
`inspect_extremes.py` (l. 3) et `inspect_zone3.py` (l. 3). Ils ne tournent sur
aucune autre machine.

**Aucun test, aucune idempotence.** `update_json.py` réécrit le fichier de
référence sans vérification préalable ni sauvegarde.

## Ce qu'il faut faire à la place

Toute régénération des données de référence doit passer par un outil neuf,
paramétré par chemins relatifs, testé, et suivi de :

1. `python scripts/build_cell_fingerprint.py` — régénère l'empreinte de cellules ;
2. `pytest engine/tests/test_ref_integrity.py` — rejoue l'audit intégralement ;
3. une nouvelle signature `qa-auditor` dans `AUDIT.md`.

Tant que cet outil n'existe pas, la chaîne de provenance de `test-1.ref.json`
repose sur les fichiers de ce répertoire — c'est un défaut connu, consigné dans
`docs/ETAT-DES-LIEUX.md` (majeur M7).
