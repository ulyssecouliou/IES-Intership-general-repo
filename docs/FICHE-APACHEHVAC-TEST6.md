# Fiche de saisie — réseau ApacheHVAC du Test SIA 4010 n° 6

> **Document généré** par `scripts/build_fiche_apachehvac_56.py`, depuis `refs/reference-data/test-6.reseau.json` — lui-même extrait de `SIA_4010_geteilter_Link/Test6/Spezifikation_Test6.pdf`. Ne rien corriger ici : corriger l'extracteur et régénérer.

> **28 paramètres relevés, 1 lus sur un graphique, 5 À TRANCHER avant toute saisie.**

- Portée : Une seule configuration : récupération par boucle à eau glycolée (« Kreislaufverbund »), ventilation à trois étages.
- Classes visées : Test 6 — classes de validation 3, 4A et 4B

## Pourquoi cette saisie est manuelle

`HVACNetwork` n'expose que `components`, `systems`, `controllers`, `get_component_by_id`, `load_network` et `path` — **aucune méthode de création**. Le réseau ne peut pas être construit par script. Une fois saisi, le `.asp` se versionne et se recharge par `load_network` ; tout le reste redevient scriptable.

---

## ⚠ À trancher AVANT de saisir quoi que ce soit

Ces 5 points ne sont pas dans la couche texte du PDF. Les combler au jugé produirait un réseau plausible et faux — le genre d'erreur qui ne se voit qu'à la comparaison finale, après une simulation annuelle.

| Champ | Où regarder dans le PDF | Pourquoi il manque |
|---|---|---|
| `courbes.temperature_eau_chaude` | — | « 20; 2018 » : ordonnée 2018 hors des graduations [-15 ; 42] du graphique — l'extraction a probablement collé deux nombres. « 20; 2018 » : ordonnée 2018 hors des graduations [-15 ; 42] du graphique — l'extraction a probablement collé deux nombres. |
| `courbes.temperature_soufflage` | — | 2 groupes d'étiquettes se disputent ce graphique : [17.5; 25, 19; 22, 23.5; 23.5] / [12; 20, 20; 18]. Un graphique voisin sans titre propre a été capté. Lire le PDF et retenir le bon groupe. |
| `reseau.debit_du_local_restaurant_m3_h` | Lüftung (p. 1) contre RLT-Anlage / Volumenstrom (p. 3) | CONTRADICTION APPARENTE : la page 1 annonce « Zuluft 3'000 m3/h, Abluft 2'650 m3/h » et la section RLT un nominal de 6'150 m3/h en étage 3. Les deux ne se rapportent probablement pas au même périmètre (local seul / centrale desservant aussi la cuisine), mais la spécification ne le dit pas. Saisir l'un pour l'autre fausserait tout le bilan aéraulique. |
| `reseau.profil_stufenbetrieb` | Regelung / Stufenbetrieb | Le profil horaire des trois étages est un GRAPHIQUE (débit relatif 0 / 0.33 / 0.67 / 1.00 sur 24 h). Les paliers y sont lisibles mais pas les heures de bascule. |
| `ventilateurs.kennfeld` | Ventilatoren / Kennfeld | Courbe caractéristique : graphique sans étiquette de données. |

---

## Composants

### Réseau et conditions générales

| Paramètre | Valeur | Source (section du PDF) |
|---|---|---|
| `debit_du_local_restaurant_m3_h` | **À TRANCHER** | Lüftung (p. 1) contre RLT-Anlage / Volumenstrom (p. 3) |
| `debit_nominal_stufe1_m3_h` | **2050** | Volumenstrom / Stufe 1 |
| `debit_nominal_stufe2_m3_h` | **4100** | Volumenstrom / Stufe 2 |
| `debit_nominal_stufe3_m3_h` | **6150** | Volumenstrom / Nennvolumenstrom Stufe 3 |
| `horaire_fonctionnement` | **Montag - Samstag 07:00 bis 16:00** | Regelung / Betriebszeit |
| `infiltration_m3_h_m2` | **0.15** | Infiltration |
| `perte_de_charge_reprise_pa` | **550** | Nenn-Druckverlust / Abluft |
| `perte_de_charge_soufflage_pa` | **750** | Nenn-Druckverlust / Zuluft |
| `profil_stufenbetrieb` | **À TRANCHER** | Regelung / Stufenbetrieb |
| `surface_nette_m2` | **237.4** | Räume / Nettofläche |

### Ventilateurs

*Classe `iesve` attendue au relevé : `HVACFan`*

| Paramètre | Valeur | Source (section du PDF) |
|---|---|---|
| `kennfeld` | **À TRANCHER** | Ventilatoren / Kennfeld |
| `puissance_reprise_w` | **1460** | Ventilatoren / Nennleistung |
| `puissance_soufflage_w` | **2021** | Ventilatoren / Nennleistung |
| `vitesse_reprise_min_1` | **1700** | Ventilatoren / Drehzahl |
| `vitesse_soufflage_min_1` | **1865** | Ventilatoren / Drehzahl |

### Récupérateur de chaleur

*Classe `iesve` attendue au relevé : `HVACAirToAirHeatEnthalpyExchanger`*

| Paramètre | Valeur | Source (section du PDF) |
|---|---|---|
| `debit_pompe_l_h` | **2100** | Nominaler Volumenstrom Pumpkreis |
| `debit_pompe_min_pourcent` | **50** | Minimaler Volumenstrom Pumpkreis |
| `fluide` | **Wasser-Glycol 30%** | Transportmedium |
| `protection_antigel` | **Mit Pumpendrehzahl-Anpassung auf Fortlufttemperatur ≥** | Vereisungsschutz |
| `puissance_pompe_w` | **185** | Nominale Pumpen-Antriebsleistung |
| `taux_temperature` | **0.71** | Kreislaufverbund / Nominale Temperaturänderungszahl |

### Batterie chaude

*Classe `iesve` attendue au relevé : `HVACHeatingCoil`*

| Paramètre | Valeur | Source (section du PDF) |
|---|---|---|
| `air_entrant_c` | **2** | Lufterhitzer / Eintritts-Lufttemperatur |
| `air_sortant_c` | **19** | Lufterhitzer / Austrittstemperatur |
| `eau_chaude_entree_c` | **40** | Heizwasser-Eintrittstemperatur |
| `puissance_kw` | **35** | Lufterhitzer / Auslegungsleistung |

### Batterie froide

*Classe `iesve` attendue au relevé : `HVACCoolingCoil`*

| Paramètre | Valeur | Source (section du PDF) |
|---|---|---|
| `air_entrant_c` | **26.3** | Luftkühler / Eintritts-Lufttemperatur |
| `air_entrant_g_kg` | **14.2** | Feuchtegehalt |
| `air_sortant_c` | **17** | Luftkühler / Austrittstemperatur |
| `eau_glacee_entree_c` | **13** | Kaltwasser-Eintrittstemperatur |
| `puissance_kw` | **30** | Luftkühler / Auslegungsleistung |
| `rendement_echange` | **0.7** | Wärmeübertragungswirkungsgrad |

## Consignes glissantes

Elles sont **dessinées** dans la spécification. Les points ci-dessous viennent des étiquettes de données du graphique. **Les paliers au-delà de ces points ne sont pas étiquetés** : le tracé les suggère constants, la spécification ne l'écrit pas.

| Consigne | Points (θ extérieure → consigne) | Lecture |
|---|---|---|
| `temperature_eau_chaude` | **À TRANCHER** | relevé refusé |
| `temperature_eau_glacee` | 12 °C → 18 °C ; 20 °C → 13 °C | étiquettes du graphique |
| `temperature_soufflage` | **À TRANCHER** | relevé refusé |

## Après la saisie

1. Enregistrer le réseau ; noter le chemin du `.asp` et le versionner.
2. Lancer ApacheSim sur **l'année complète** — un `.aps` partiel rend toute somme annuelle inexploitable.
3. Lancer `Run_VE_SIA4010_Sonde_APS.py` et renvoyer `outputs/sonde_aps.json`.
4. Le relevé donnera les noms de variables des batteries, du récupérateur, des ventilateurs et de l'humidificateur — les liaisons encore manquantes du Test 6.

## Ce que cette fiche ne dit pas

- Elle ne déclare rien conforme. Elle décrit une SAISIE ; le verdict vient de la comparaison aux valeurs de référence publiées.
- Les charges internes et l'occupation renvoient à SIA 2024:2021, absent du dépôt sous forme exploitable.
- Le climat SIA 2028 DRY Zürich-Kloten reste absent : sans lui, aucune simulation de ce test n'est un cas de validation SIA.

