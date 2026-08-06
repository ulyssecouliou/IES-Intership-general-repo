# Lancer les scripts dans IESVE

Le dépôt contient **50 fichiers `Run_VE_*.py`** à la racine, dont **24 portent
`SIA4010`** dans leur nom. La plupart viennent du travail antérieur et ne sont
pas décrits ici. Les deux à lancer aujourd'hui sont :

| Fichier | Ce qu'il fait | Ce qu'il exige |
|---|---|---|
| `Run_VE_SIA4010_Sonde_Test1.py` | Déroule le Test 1 pas à pas et relève ce que l'API renvoie réellement | Une VE ouverte sur un projet |
| `Run_VE_SIA4010_Sonde_APS.py` | Relève **sans filtre** les variables de résultats d'un `.aps` | Une VE ouverte **et au moins une simulation ApacheSim déjà passée** |

> **À ne pas confondre avec `Run_VE_SIA4010_APS_Probe.py`**, qui existait déjà.
> Celui-là filtre les variables sur onze jetons choisis pour les Tests 1 et 2
> (`load`, `solar`, `radiation`, `gain`, `window`, `temperature`…) et écrit
> dans le dossier du projet VE. Aucun de ces jetons ne désigne un ventilateur,
> un humidificateur ni une récupération de chaleur : il écarte exactement ce
> qui manque aux tests 4 à 6. Les deux sont en lecture seule ; lancer l'un
> n'empêche pas l'autre.

## Comment lancer

Dans VE : **Applications → Python Scripts** (le *Python Scripts navigator*),
sélectionner le fichier, cliquer **Run**.

Il n'y a pas de terminal dans VEScripts, seulement ce bouton. Les deux scripts
en tiennent compte : ils fonctionnent **sans argument** et détectent seuls ce
qu'ils ont à faire. Aucun `sys.exit` n'est appelé — il remonterait comme une
erreur dans la fenêtre de script alors que tout s'est bien passé.

La console de VEScripts n'est pas en UTF-8 : les accents y sortent en
charabia. Les scripts les retirent **à l'affichage seulement**. Les fichiers
écrits restent en UTF-8 accentué.

## Ce qu'il faut me renvoyer

Chaque sonde écrit un rapport sous `outputs/` :

- `outputs/sonde_test1_600.json`
- `outputs/sonde_aps.json`

**C'est ce fichier qu'il faut me renvoyer**, pas ce qui s'affiche à l'écran :
la console tronque, le fichier non — et c'est justement la partie coupée qui
contient d'ordinaire le nom qu'on cherche.

## Ce que les sondes ne font pas

Elles ne produisent **aucun résultat de validation**. Elles relèvent des noms
d'objets, des signatures et des tailles de séries. Une étape en échec est un
résultat utile, pas un problème : elle dit ce que l'API refuse, et c'est
exactement ce qu'on cherche à apprendre.

Elles ne modifient pas le modèle, à une exception près, signalée dans le
rapport : `Run_VE_SIA4010_Sonde_Test1.py` **affecte le fichier météo DRYCOLD**
au projet, parce que c'est le seul moyen de vérifier que cette affectation
fonctionne.

## Pourquoi la sonde APS est le point bloquant du moment

Les tests SIA 2 à 6 comparent 20 grandeurs — « Wärmezufuhr Lufterwärmer »,
« Energiebedarf Ventilatoren », « Hilfsenergie WRG »… — dont **aucune n'a de
nom de variable VE établi**. `ve_adapter/bandes_adapter.py` les déclare toutes
`aps_varname: None`, et l'extraction refuse de tourner tant que c'est le cas.

C'est délibéré : deviner un nom de variable produirait un nombre plausible et
faux, c'est-à-dire le pire résultat possible pour un dossier de validation.

`Run_VE_SIA4010_Sonde_APS.py` liste ce que le fichier contient réellement, aux
trois niveaux (local `z`, système `v`, météo `w`), plus les systèmes Apache,
les postes d'énergie et les unités. Un seul passage suffit à lever les
20 liaisons.

Il tranche aussi un désaccord interne au dépôt : `swiss_sia` appelle
`get_variables()` **sans argument** et lit `model_level` sur chaque entrée,
tandis que `ve_adapter/bandes_adapter.py` appelle `get_variables(niveau)`. Les
deux ne peuvent pas être justes et aucune documentation ne tranche. La sonde
relève les deux formes ; le rapport dira laquelle répond.

Pour l'état courant, en Python :

```python
from ve_adapter import bandes_adapter
print(bandes_adapter.etat_des_liaisons())
```
