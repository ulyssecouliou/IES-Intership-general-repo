# Fiche de saisie — réseau ApacheHVAC du Test SIA 4010 n° 5

> **Document généré** par `scripts/build_fiche_apachehvac_56.py`, depuis `refs/reference-data/test-5.reseau.json` — lui-même extrait de `SIA_4010_geteilter_Link/Test5/Spezifikation_Test5.pdf`. Ne rien corriger ici : corriger l'extracteur et régénérer.

> **29 paramètres relevés, 3 lus sur un graphique, 6 À TRANCHER avant toute saisie.**

- Portée : Quatre variantes (5A à 5D) : type de récupérateur, taux d'échange, part de pression constante et type d'humidificateur en dépendent.
- Classes visées : Test 5 — classes de validation 2B, 4A et 4B

## Pourquoi cette saisie est manuelle

`HVACNetwork` n'expose que `components`, `systems`, `controllers`, `get_component_by_id`, `load_network` et `path` — **aucune méthode de création**. Le réseau ne peut pas être construit par script. Une fois saisi, le `.asp` se versionne et se recharge par `load_network` ; tout le reste redevient scriptable.

---

## ⚠ À trancher AVANT de saisir quoi que ce soit

Ces 6 points ne sont pas dans la couche texte du PDF. Les combler au jugé produirait un réseau plausible et faux — le genre d'erreur qui ne se voit qu'à la comparaison finale, après une simulation annuelle.

| Champ | Où regarder dans le PDF | Pourquoi il manque |
|---|---|---|
| `humidificateur.type_par_variante` | Luftbefeuchter / Variante 5A 5B 5C 5D / Typ | Deux cellules (« Kontaktbefeuchter », « Dampf ») pour quatre colonnes. Le dépôt suppose ailleurs « contact 5A-5C, vapeur 5D » (build_traceability_matrix.ANCRAGE) : cette supposition n'est PAS confirmée par la couche texte et doit être tranchée. |
| `recuperateur.taux_humidite_par_variante` | Nominale Feuchteänderungszahl | Deux cellules (0.42, 0.3) pour quatre colonnes. |
| `recuperateur.taux_temperature_par_variante` | Nominale Temperaturänderungszahl | Deux cellules (0.67, 0.69) pour quatre colonnes. |
| `recuperateur.type_par_variante` | Variante 5A 5B 5C 5D / Typ | Deux cellules (« Hygroskopisch », « Nicht hygroskopisch ») pour quatre colonnes. |
| `ventilateurs.kennfeld` | Ventilatoren / Kennfeld | Courbe caractéristique : graphique SANS étiquette de données. Aucun point n'en est extractible. Sans elle, la puissance des ventilateurs à charge partielle n'est pas reproductible — et c'est une des grandeurs à livrer. |
| `ventilateurs.part_pression_constante_pa` | Variante 5A 5B 5C 5D / Konstantdruckanteil (ZUL+ABL) | Deux cellules (« 50+50 Pa », « 270+270 Pa ») pour QUATRE colonnes de variantes. Le point de partage n'est pas dans la couche texte. |

---

## Composants

### Réseau et conditions générales

| Paramètre | Valeur | Source (section du PDF) |
|---|---|---|
| `co2_exterieur_ppm` | **400** | Sollwerte / CO2 |
| `debit_nominal_m3_h` | **1040** | Volumenstrom / Nennvolumenstrom |
| `debit_par_personne_m3_h` | **25** | Lüftung — « abweichend von SIA 2024:2021 » |
| `debit_variable_min_pourcent` | **30** | Volumenstrom / Variabel von bis |
| `horaire_fonctionnement` | **Werktags 06:00 bis 19:00** | Regelung / Betriebszeit |
| `humidite_relative_min_pourcent` | **30** | Sollwerte / Rel. Feuchte |
| `infiltration_m3_h_m2` | **0.15** | Infiltration |
| `perte_de_charge_reprise_pa` | **520** | Nenn-Druckverlust / Abluft |
| `perte_de_charge_soufflage_pa` | **770** | Nenn-Druckverlust / Zuluft |

### Ventilateurs

*Classe `iesve` attendue au relevé : `HVACFan`*

| Paramètre | Valeur | Source (section du PDF) |
|---|---|---|
| `kennfeld` | **À TRANCHER** | Ventilatoren / Kennfeld |
| `part_pression_constante_pa` | **À TRANCHER** | Variante 5A 5B 5C 5D / Konstantdruckanteil (ZUL+ABL) |
| `puissance_reprise_w` | **290** | Ventilatoren / Nennleistung |
| `puissance_soufflage_w` | **420** | Ventilatoren / Nennleistung |
| `vitesse_reprise_min_1` | **2500** | Ventilatoren / Drehzahl |
| `vitesse_soufflage_min_1` | **3000** | Ventilatoren / Drehzahl |

### Récupérateur de chaleur

*Classe `iesve` attendue au relevé : `HVACAirToAirHeatEnthalpyExchanger`*

| Paramètre | Valeur | Source (section du PDF) |
|---|---|---|
| `charge_partielle` | **Gemäss EN 16798-5-1, Anhang D** | Teillastverhalten |
| `puissance_entrainement_w` | **120** | Nominale Antriebsleistung |
| `taux_humidite_par_variante` | **À TRANCHER** | Nominale Feuchteänderungszahl |
| `taux_temperature_par_variante` | **À TRANCHER** | Nominale Temperaturänderungszahl |
| `type_par_variante` | **À TRANCHER** | Variante 5A 5B 5C 5D / Typ |
| `vitesse_nominale_min_1` | **20** | Nominale Drehzahl |

### Batterie chaude

*Classe `iesve` attendue au relevé : `HVACHeatingCoil`*

| Paramètre | Valeur | Source (section du PDF) |
|---|---|---|
| `air_entrant_c` | **10.5** | Lufterhitzer / Eintritts-Lufttemperatur |
| `air_sortant_c` | **19** | Lufterhitzer / Austrittstemperatur |
| `eau_chaude_entree_c` | **40** | Heizwasser-Eintrittstemperatur |
| `puissance_kw` | **3.5** | Lufterhitzer / Auslegungsleistung |

### Batterie froide

*Classe `iesve` attendue au relevé : `HVACCoolingCoil`*

| Paramètre | Valeur | Source (section du PDF) |
|---|---|---|
| `air_entrant_c` | **29.5** | Luftkühler / Eintritts-Lufttemperatur |
| `air_entrant_g_kg` | **14.2** | Feuchtegehalt |
| `air_sortant_c` | **17** | Luftkühler / Austrittstemperatur |
| `eau_glacee_entree_c` | **10** | Kaltwasser-Eintrittstemperatur |
| `facteur_bypass` | **0.065** | Bypassfaktor |
| `puissance_kw` | **8.6** | Luftkühler / Auslegungsleistung |
| `rendement_echange` | **0.765** | Wärmeübertragungswirkungsgrad |

### Humidificateur

| Paramètre | Valeur | Source (section du PDF) |
|---|---|---|
| `debit_eau_kg_h` | **4.9** | Nenn-Massenstrom Wasser |
| `energie_pompe_wh_m3` | **0.01** | Spez. Pumpenenergie des Befeuchters |
| `type_par_variante` | **À TRANCHER** | Luftbefeuchter / Variante 5A 5B 5C 5D / Typ |

## Consignes glissantes

Elles sont **dessinées** dans la spécification. Les points ci-dessous viennent des étiquettes de données du graphique. **Les paliers au-delà de ces points ne sont pas étiquetés** : le tracé les suggère constants, la spécification ne l'écrit pas.

| Consigne | Points (θ extérieure → consigne) | Lecture |
|---|---|---|
| `temperature_eau_chaude` | -10 °C → 40 °C ; 20 °C → 18 °C | étiquettes du graphique |
| `temperature_eau_glacee` | 12 °C → 18 °C ; 20 °C → 13 °C | étiquettes du graphique |
| `temperature_soufflage` | 12 °C → 20 °C ; 20 °C → 18 °C | étiquettes du graphique |

## Après la saisie

1. Enregistrer le réseau ; noter le chemin du `.asp` et le versionner.
2. Lancer ApacheSim sur **l'année complète** — un `.aps` partiel rend toute somme annuelle inexploitable.
3. Lancer `Run_VE_SIA4010_Sonde_APS.py` et renvoyer `outputs/sonde_aps.json`.
4. Le relevé donnera les noms de variables des batteries, du récupérateur, des ventilateurs et de l'humidificateur — les liaisons encore manquantes du Test 5.

## Ce que cette fiche ne dit pas

- Elle ne déclare rien conforme. Elle décrit une SAISIE ; le verdict vient de la comparaison aux valeurs de référence publiées.
- Les charges internes et l'occupation renvoient à SIA 2024:2021, absent du dépôt sous forme exploitable.
- Le climat SIA 2028 DRY Zürich-Kloten reste absent : sans lui, aucune simulation de ce test n'est un cas de validation SIA.

