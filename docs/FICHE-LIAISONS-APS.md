# Fiche de liaisons APS — confrontation d'un relevé

> **Document généré** par `scripts/match_aps_variables.py`. Il compare un relevé de sonde aux grandeurs déclarées dans `ve_adapter/bandes_adapter.py`. Il **ne lie rien** : trouver un nom dans le relevé ne prouve pas que c'est la bonne variable. Seule une lecture du modèle VE le prouve.

- Relevé : `ZOER_C1.aps`
- Variables relevées : **819**
- Grandeurs déclarées : **20**, dont **0 liées**

| État | Effectif | Ce que ça veut dire |
|---|---|---|
| `BOUND` | 0 | Liaison déjà déclarée. |
| `CANDIDATE_PRESENT` | 6 | Un candidat existe ET figure dans ce relevé. **À confirmer dans VE**, pas acquis. |
| `CANDIDATE_WRONG_LEVEL` | 1 | Le candidat existe, mais à un AUTRE niveau que celui déclaré. Le niveau décide du PÉRIMÈTRE : ce n'est pas un organe manquant, et ce n'est pas non plus une simple faute de frappe. |
| `CANDIDATE_ABSENT` | 0 | Un candidat existe mais ne figure PAS dans ce relevé : le modèle ne porte probablement pas l'organe. |
| `CANDIDATE_IMPOSSIBLE` | 3 | Aucun candidat n'est possible, et la raison est écrite. |
| `NO_CANDIDATE` | 10 | Rien de proposé. Le relevé offre la liste ci-dessous, sans classement — un classement plausible se ferait accepter sans vérification. |

## Recensement du relevé, par niveau

| Niveau | Variables |
|---|---|
| `c` | 184 |
| `e` | 274 |
| `j` | 15 |
| `l` | 88 |
| `n` | 9 |
| `o` | 6 |
| `r` | 15 |
| `s` | 22 |
| `t` | 6 |
| `v` | 35 |
| `w` | 14 |
| `z` | 151 |

## Test 2

| Grandeur (libellé du classeur) | Niveau | État | Variable | À faire |
|---|---|---|---|---|
| `Jahresenergie solarer Wärmeeintrag` | `z` (151 var.) | **CANDIDATE_PRESENT** | `Window solar gains` (Solar gain) | Confirmer dans VE que cette variable mesure bien : apport solaire et rayonnement transmis, au niveau du local |
| `Jahresenergie total transmittierte Solarstrahlung` | `z` (151 var.) | **NO_CANDIDATE** | `Room air temperature`, `CIBSE F1 factor`, `CIBSE F2 factor`, `Comfort temperature`, `CIBSE interm. heating correction`, `Environmental temperature`, `CIBSE thermal response`, `Room radiant temperature`, `CIBSE interm. plant size`, `Room air temperature&Room % saturation&Atmospheric pressure[w]`, `Heating set point`, `Cooling set point` … et 139 autres | Choisir dans VE parmi les variables du niveau : apport solaire et rayonnement transmis, au niveau du local |

## Test 3

| Grandeur (libellé du classeur) | Niveau | État | Variable | À faire |
|---|---|---|---|---|
| `Beleuchtungsenergie` | `z` (151 var.) | **CANDIDATE_WRONG_LEVEL** | `Total lights energy` (Total lights energy) | **Incohérence de périmètre.** La variable existe, mais au niveau `e` et non `z`. Le niveau décide du périmètre (local / système / bâtiment) : lire la spécification pour savoir lequel le classeur demande, PUIS corriger soit le niveau, soit la variable. Aucune simulation ne réglera cela. |

## Test 4

| Grandeur (libellé du classeur) | Niveau | État | Variable | À faire |
|---|---|---|---|---|
| `Wärmezufuhr Lufterwärmer` | `v` (35 var.) | **CANDIDATE_PRESENT** | `Sys Mech vent heating load` (System air heating load) | Confirmer dans VE que cette variable mesure bien : centrale de traitement d air du Hoersaal |
| `Wärmeabfuhr Luftkühler total` | `v` (35 var.) | **CANDIDATE_IMPOSSIBLE** | — | « total » suppose sensible + latent. VE les sépare en « Sys Mech vent cooling load » (sensible) et « Sys Mech vent dehum load » (latent). Une liaison ne peut donc pas être un simple nom de variable : il faut une SOMME, que LIAISONS ne sait pas exprimer aujourd'hui. |
| `Energiebedarf Ventilatoren` | `v` (35 var.) | **NO_CANDIDATE** | `Sys Room heating load`, `Sys Room humidification load`, `Sys Mech vent heating load`, `Sys Aux mech vent heating load`, `Sys DHW heating load`, `HIDE Sys DHW flow rate`, `Sys DHW solar heating system input`, `Sys DHW solar htg system tank temp`, `HIDE Sys DHW solar htg system panel temp`, `HIDE Sys DHW solar htg system flow rate`, `Sys DHW solar heat input`, `Sys Boiler load` … et 23 autres | Choisir dans VE parmi les variables du niveau : centrale de traitement d air du Hoersaal |

## Test 5

| Grandeur (libellé du classeur) | Niveau | État | Variable | À faire |
|---|---|---|---|---|
| `Befeuchtungsenergie` | `v` (35 var.) | **CANDIDATE_PRESENT** | `Sys Room humidification load` (Room hum. plant load) | Confirmer dans VE que cette variable mesure bien : systeme de ventilation du batiment exemple |
| `Wärmeabfuhr Luftkühler latent` | `v` (35 var.) | **CANDIDATE_PRESENT** | `Sys Mech vent dehum load` (System air lat. clg. load) | Confirmer dans VE que cette variable mesure bien : systeme de ventilation du batiment exemple |
| `Wärmezufuhr Lufterwärmer` | `v` (35 var.) | **CANDIDATE_PRESENT** | `Sys Mech vent heating load` (System air heating load) | Confirmer dans VE que cette variable mesure bien : systeme de ventilation du batiment exemple |
| `Wärmeabfuhr Luftkühler total` | `v` (35 var.) | **CANDIDATE_IMPOSSIBLE** | — | « total » suppose sensible + latent. VE les sépare en « Sys Mech vent cooling load » (sensible) et « Sys Mech vent dehum load » (latent). Une liaison ne peut donc pas être un simple nom de variable : il faut une SOMME, que LIAISONS ne sait pas exprimer aujourd'hui. |
| `Energiebedarf Ventilatoren` | `v` (35 var.) | **NO_CANDIDATE** | `Sys Room heating load`, `Sys Room humidification load`, `Sys Mech vent heating load`, `Sys Aux mech vent heating load`, `Sys DHW heating load`, `HIDE Sys DHW flow rate`, `Sys DHW solar heating system input`, `Sys DHW solar htg system tank temp`, `HIDE Sys DHW solar htg system panel temp`, `HIDE Sys DHW solar htg system flow rate`, `Sys DHW solar heat input`, `Sys Boiler load` … et 23 autres | Choisir dans VE parmi les variables du niveau : systeme de ventilation du batiment exemple |
| `Hilfsenergie WRG` | `v` (35 var.) | **NO_CANDIDATE** | `Sys Room heating load`, `Sys Room humidification load`, `Sys Mech vent heating load`, `Sys Aux mech vent heating load`, `Sys DHW heating load`, `HIDE Sys DHW flow rate`, `Sys DHW solar heating system input`, `Sys DHW solar htg system tank temp`, `HIDE Sys DHW solar htg system panel temp`, `HIDE Sys DHW solar htg system flow rate`, `Sys DHW solar heat input`, `Sys Boiler load` … et 23 autres | Choisir dans VE parmi les variables du niveau : systeme de ventilation du batiment exemple |
| `Wärmezufuhr WRG` | `v` (35 var.) | **NO_CANDIDATE** | `Sys Room heating load`, `Sys Room humidification load`, `Sys Mech vent heating load`, `Sys Aux mech vent heating load`, `Sys DHW heating load`, `HIDE Sys DHW flow rate`, `Sys DHW solar heating system input`, `Sys DHW solar htg system tank temp`, `HIDE Sys DHW solar htg system panel temp`, `HIDE Sys DHW solar htg system flow rate`, `Sys DHW solar heat input`, `Sys Boiler load` … et 23 autres | Choisir dans VE parmi les variables du niveau : systeme de ventilation du batiment exemple |
| `Wärmezufuhr WRG latent` | `v` (35 var.) | **NO_CANDIDATE** | `Sys Room heating load`, `Sys Room humidification load`, `Sys Mech vent heating load`, `Sys Aux mech vent heating load`, `Sys DHW heating load`, `HIDE Sys DHW flow rate`, `Sys DHW solar heating system input`, `Sys DHW solar htg system tank temp`, `HIDE Sys DHW solar htg system panel temp`, `HIDE Sys DHW solar htg system flow rate`, `Sys DHW solar heat input`, `Sys Boiler load` … et 23 autres | Choisir dans VE parmi les variables du niveau : systeme de ventilation du batiment exemple |

## Test 6

| Grandeur (libellé du classeur) | Niveau | État | Variable | À faire |
|---|---|---|---|---|
| `Wärmezufuhr Lufterwärmer` | `v` (35 var.) | **CANDIDATE_PRESENT** | `Sys Mech vent heating load` (System air heating load) | Confirmer dans VE que cette variable mesure bien : systeme de ventilation, restaurant et cuisine |
| `Wärmeabfuhr Luftkühler total` | `v` (35 var.) | **CANDIDATE_IMPOSSIBLE** | — | « total » suppose sensible + latent. VE les sépare en « Sys Mech vent cooling load » (sensible) et « Sys Mech vent dehum load » (latent). Une liaison ne peut donc pas être un simple nom de variable : il faut une SOMME, que LIAISONS ne sait pas exprimer aujourd'hui. |
| `Energiebedarf Ventilatoren` | `v` (35 var.) | **NO_CANDIDATE** | `Sys Room heating load`, `Sys Room humidification load`, `Sys Mech vent heating load`, `Sys Aux mech vent heating load`, `Sys DHW heating load`, `HIDE Sys DHW flow rate`, `Sys DHW solar heating system input`, `Sys DHW solar htg system tank temp`, `HIDE Sys DHW solar htg system panel temp`, `HIDE Sys DHW solar htg system flow rate`, `Sys DHW solar heat input`, `Sys Boiler load` … et 23 autres | Choisir dans VE parmi les variables du niveau : systeme de ventilation, restaurant et cuisine |
| `Hilfsenergie WRG` | `v` (35 var.) | **NO_CANDIDATE** | `Sys Room heating load`, `Sys Room humidification load`, `Sys Mech vent heating load`, `Sys Aux mech vent heating load`, `Sys DHW heating load`, `HIDE Sys DHW flow rate`, `Sys DHW solar heating system input`, `Sys DHW solar htg system tank temp`, `HIDE Sys DHW solar htg system panel temp`, `HIDE Sys DHW solar htg system flow rate`, `Sys DHW solar heat input`, `Sys Boiler load` … et 23 autres | Choisir dans VE parmi les variables du niveau : systeme de ventilation, restaurant et cuisine |
| `Wärmeabfuhr WRG` | `v` (35 var.) | **NO_CANDIDATE** | `Sys Room heating load`, `Sys Room humidification load`, `Sys Mech vent heating load`, `Sys Aux mech vent heating load`, `Sys DHW heating load`, `HIDE Sys DHW flow rate`, `Sys DHW solar heating system input`, `Sys DHW solar htg system tank temp`, `HIDE Sys DHW solar htg system panel temp`, `HIDE Sys DHW solar htg system flow rate`, `Sys DHW solar heat input`, `Sys Boiler load` … et 23 autres | Choisir dans VE parmi les variables du niveau : systeme de ventilation, restaurant et cuisine |
| `Wärmezufuhr WRG` | `v` (35 var.) | **NO_CANDIDATE** | `Sys Room heating load`, `Sys Room humidification load`, `Sys Mech vent heating load`, `Sys Aux mech vent heating load`, `Sys DHW heating load`, `HIDE Sys DHW flow rate`, `Sys DHW solar heating system input`, `Sys DHW solar htg system tank temp`, `HIDE Sys DHW solar htg system panel temp`, `HIDE Sys DHW solar htg system flow rate`, `Sys DHW solar heat input`, `Sys Boiler load` … et 23 autres | Choisir dans VE parmi les variables du niveau : systeme de ventilation, restaurant et cuisine |

## Ce que cette fiche ne dit pas

- Qu'une variable présente est la BONNE. Elle est présente, rien de plus.
- Qu'une variable absente n'existe pas. Ce relevé vient d'UN modèle ; un autre modèle en porterait d'autres.
- Rien sur la conformité. Une liaison résolue permet de mesurer ; elle ne décide d'aucun verdict.

