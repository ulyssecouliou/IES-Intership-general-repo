# Fichiers officiels SIA 4010

Ce dossier accueille les fichiers **officiels** du SIA. Il est volontairement
vide dans le dépôt : ces fichiers ne sont pas redistribuables, et ils font foi.

> **Aucun fichier de ce dossier ne doit être reconstitué, converti ou approché.**
> The evidence registry (`swiss_sia/reference_model/sia4010/evidence_registry.py`)
> refuses to guess a path: if a file is missing, it raises an error naming it.
> A validation dossier built on an approximated file would be invalidated by the
> sub-commission.

## Structure attendue

```
data/sia4010_official/
├── test_1/
│   ├── specification.pdf      ← Spezifikation_Test1.pdf, renommé
│   └── evaluation.xlsx        ← Resultaterfassung_Test1.xlsx, renommé
├── test_2/
│   ├── specification.pdf
│   └── evaluation.xlsx
├── …
└── test_7/
    ├── specification.pdf
    ├── evaluation.xlsx
    └── (fichiers propres au test, laissés sous leur nom d'origine)
```

Les deux noms `specification.pdf` et `evaluation.xlsx` sont **imposés** : ce
sont ceux que le dépôt cherche. Tout autre fichier du dossier est conservé et
exposé via `TestAssets.extras`, sous son nom d'origine.

Le Test 7 en apporte plusieurs, à déposer tels quels :
`Lastverläufe_220607.xlsx` (profils de charge), `Schema.pdf`, `PV_Layout.pdf`,
et la fiche technique du module photovoltaïque.

## Où obtenir les fichiers

| Élément | Source | Coût |
|---|---|---|
| Spécifications et classeurs des 7 tests | `https://www.sia.ch/sia4010` | inclus |
| Documentation du bâtiment exemple, IFC, DXF | idem | inclus |
| SIA 4010:2023, SIA 380/2:2022 | SIA Shop | payant |
| Fiches d'utilisation SIA 2024 | `https://www.sia.ch/de/cms/dienstleistungen/normenundordnungen?item=15143#15152` | **gratuit** |
| Corrigenda SIA 2024 et SIA 180 | SIA Shop | **gratuit** |
| Données climatiques SIA 2028 (« Gegenwart ») | SIA Shop, formulaire de commande | payant |
| Scénarios climatiques CH2018 | `https://www.sia.ch/de/cms/dienstleistungen/normenundordnungen?item=15284#15152` | **gratuit** |

## Le piège du fichier climatique

Les sept spécifications demandent toutes `SIA 2028 DRY normal, Zürich Kloten`.
Le jeu **gratuit** CH2018 ne s'y substitue pas, pour trois raisons
indépendantes et chacune suffisante :

1. **Période.** CH2018 ne contient que 2035 et 2060 (scénarios RCP). Aucun
   fichier de période présente.
2. **Contenu.** Les quatre rapports d'application écrivent tous
   « Original-SIA-Datei » ; IDA ICE la nomme `KLO_dry_normal.PRN`. Le rapport
   EXCEL du Test 2 précise que les données SIA 2028 d'origine *contiennent le
   rayonnement solaire sur les surfaces verticales des orientations
   principales* — colonnes absentes du CSV CH2018, qui ne porte que le global
   horizontal, le diffus et le direct.
3. **Format.** `.PRN` contre `.csv`.

À ne pas confondre non plus : SIA 4010 §3.1.1 prescrit bien CH2018 RCP 8.5
période « 2035 », mais pour **appliquer** SIA 380/2 dans un projet réel — pas
pour les tests de validation. Les deux coexistent dans les mêmes documents.

## Ce qu'on possède déjà, et où

La température d'air horaire de Zürich-Kloten (8760 h, moyenne 9,469 °C) est
récupérable d'une source officielle SIA : `Test4/Resultaterfassung Test4.xlsx`,
feuille `Wetterdaten`. Elle ne contient **ni rayonnement ni humidité** ; ce
n'est donc pas un substitut au jeu SIA 2028 complet.

Le climat du Test 1 (DRYCOLD, Denver) est public et gratuit chez l'ISO :
`https://standards.iso.org/iso/52016/-1/ed-1/`. Attention, ce fichier porte
deux avertissements qu'il ne faut pas manquer — son premier mois est un mois
d'**initialisation** (décembre recopié, 744 h), et il fournit l'irradiance
**déjà calculée** sur huit surfaces nommées, sans décomposition
global/direct/diffus.

## Vérifier ce qui est présent

```python
from core.repositories import SIA4010Repository

depot = SIA4010Repository("data/sia4010_official")
print(depot.available_tests())
for test_id in depot.available_tests():
    assets = depot.get_assets(test_id)
    print(test_id, "complet" if assets.is_complete else "INCOMPLET")
```
