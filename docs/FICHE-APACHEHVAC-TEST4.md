# Fiche de saisie — réseau ApacheHVAC du Test SIA 4010 n° 4

> **Document généré** par `scripts/build_fiche_apachehvac.py`. Les valeurs viennent de `construire_test4_dans_ve.PARAMETRES` et de `refs/reference-data/test-4.consignes.json`, tous deux tracés à la spécification officielle. Ne pas les modifier ici : corriger la source et régénérer.

## Pourquoi cette saisie est manuelle

`HVACNetwork` n'expose que `components`, `systems`, `controllers`, `get_component_by_id`, `load_network` et `path` — **aucune méthode de création**. Le réseau ne peut pas être construit par script.

Une fois saisi et enregistré, le fichier `.asp` se versionne dans le dépôt et se recharge par `HVACNetwork.load_network`. **La saisie n'est à faire qu'une fois** ; tout ce qui suit — affectation, simulation, extraction, verdict — est scriptable.

C'est aussi ce qui débloquera le Test 7, dont le réseau est dans le même cas.

## Ce que ce réseau sert à établir

Les 18 liaisons manquantes des tests SIA 4 à 6. ApacheSystems ne peut pas les porter : ses paramètres sont des rendements saisonniers (`SFP`, `SEER`, `SCoP`), et cinq exigences du Test 4 n'y ont aucune expression — puissance des batteries, bypass du récupérateur, protection antigel, consigne de soufflage régulée, débit piloté par le CO2.

---

## Composants, dans l'ordre du flux d'air

### 1. Prise d'air neuf

*Classe `iesve` attendue au relevé : `HVACInlet`*

| Paramètre | Valeur | Source |
|---|---|---|
| — | Air extérieur, appareil en toiture (« Geräteaufstellung: auf dem Dach, Aussenklima »). | Spezifikation_Test4.pdf |

### 2. Récupérateur de chaleur

*Classe `iesve` attendue au relevé : `HVACAirToAirHeatEnthalpyExchanger`*

| Paramètre | Valeur | Source |
|---|---|---|
| `recuperateur_type` | **échangeur à plaques SANS échange d'humidité** | Spezifikation_Test4.pdf, Wärmerückgewinnungsgerät / Beschreibung |
| `recuperateur_taux` | **0.75** | Spezifikation_Test4.pdf, Wärmerückgewinnungsgerät / Nominale Temperaturänderungszahl |
| — | Bypass régulé sur la consigne de température de soufflage ; 100 % de bypass en refroidissement. | Spezifikation_Test4.pdf |
| — | Protection antigel : bypass sur température d'air rejeté ≥ 0 °C. | Spezifikation_Test4.pdf |

### 3. Ventilateur de soufflage

*Classe `iesve` attendue au relevé : `HVACFan`*

| Paramètre | Valeur | Source |
|---|---|---|
| `puissance_ventilateur_soufflage_w` | **407.0** | Spezifikation_Test4.pdf, Ventilatoren / Nennleistung |
| `perte_de_charge_soufflage_pa` | **500.0** | Spezifikation_Test4.pdf, Nenn-Druckverlust |
| — | Placé APRÈS le récupérateur ; moteur dans le flux d'air. | Spezifikation_Test4.pdf |
| — | Vitesse nominale 2 790 min⁻¹. | Spezifikation_Test4.pdf |

### 4. Batterie chaude

*Classe `iesve` attendue au relevé : `HVACHeatingCoil`*

| Paramètre | Valeur | Source |
|---|---|---|
| `batterie_chaude_kw` | **11.4** | Spezifikation_Test4.pdf, Lufterhitzer / Auslegung |
| — | Air entrant +8 °C, sortant 29 °C. | Spezifikation_Test4.pdf |
| — | Eau chaude : entrée 31 °C, départ constant 40 °C. | Spezifikation_Test4.pdf |

### 5. Batterie froide

*Classe `iesve` attendue au relevé : `HVACCoolingCoil`*

| Paramètre | Valeur | Source |
|---|---|---|
| `batterie_froide_kw` | **12.8** | Spezifikation_Test4.pdf, Luftkühler / Auslegung |
| — | Rendement d'échange 0,85 ; facteur de bypass 0,065. | Spezifikation_Test4.pdf |
| — | Air entrant 29,5 °C / 22 °C humide / 14,2 g·kg⁻¹ / 52 % HR, sortant 16 °C. | Spezifikation_Test4.pdf |
| — | Eau glacée : entrée 13 °C, départ constant 13 °C. | Spezifikation_Test4.pdf |

### 6. Ventilateur de reprise

*Classe `iesve` attendue au relevé : `HVACFan`*

| Paramètre | Valeur | Source |
|---|---|---|
| `puissance_ventilateur_reprise_w` | **331.0** | Spezifikation_Test4.pdf, Ventilatoren / Nennleistung |
| `perte_de_charge_reprise_pa` | **400.0** | Spezifikation_Test4.pdf, Nenn-Druckverlust |
| — | Placé APRÈS le récupérateur ; moteur dans le flux d'air. | Spezifikation_Test4.pdf |
| — | Vitesse nominale 2 730 min⁻¹. | Spezifikation_Test4.pdf |

### 7. Régulateur de température de soufflage

*Classe `iesve` attendue au relevé : `HVACControllerWithSensor`*

| Paramètre | Valeur | Source |
|---|---|---|
| `temperature_soufflage_refroidissement_c` | **16.0 – 22.5** | Spezifikation_Test4.pdf, Zulufttemperatur |
| `temperature_soufflage_chauffage_c` | **22.5 – 29.0** | Spezifikation_Test4.pdf, Zulufttemperatur |
| — | Régulateur PI, asservi à la consigne de température du local. | Spezifikation_Test4.pdf |

### 8. Régulateur de débit sur CO2

*Classe `iesve` attendue au relevé : `HVACControllerWithSensor`*

| Paramètre | Valeur | Source |
|---|---|---|
| `debit_nominal_m3_h` | **1700.0** | Spezifikation_Test4.pdf, Volumenstrom |
| `debit_variable_pourcent` | **20.0 – 100.0** | Spezifikation_Test4.pdf, Variabel von bis |
| `co2_ppm` | **600.0 – 1000.0** | Spezifikation_Test4.pdf, Sollwerte / CO2 |
| `co2_exterieur_ppm` | **400.0** | Spezifikation_Test4.pdf, Sollwerte / CO2 |
| — | Variateur de fréquence agissant directement sur le ventilateur. | Spezifikation_Test4.pdf |

### 9. Zone desservie

*Classe `iesve` attendue au relevé : `HVACZone`*

| Paramètre | Valeur | Source |
|---|---|---|
| `surface_nette_m2` | **165.8** | Spezifikation_Test4.pdf, Nettofläche |
| `occupants` | **55** | Spezifikation_Test4.pdf, Personen / Anzahl |
| `apport_equipements_w_m2` | **10.0** | Spezifikation_Test4.pdf, Geräte |
| `apport_eclairage_w_m2` | **6.4** | Spezifikation_Test4.pdf, Beleuchtung |
| `infiltration_m3_h_m2` | **0.15** | Spezifikation_Test4.pdf, Infiltration |
| — | Local « Hörsaal », sans fenêtre, sur deux niveaux, toiture sur extérieur. | Spezifikation_Test4.pdf |

## Réglages généraux

| Paramètre | Valeur | Source |
|---|---|---|
| `horaire_fonctionnement` | **jours ouvrés 05:00-20:00 ; arrêt en juillet** | Spezifikation_Test4.pdf, Regelung / Betriebszeit |

## Consigne de température du local

**Attention : consigne GLISSANTE.** Elle dépend de la Gleitender 48-h Mittelwert Aussenlufttemperatur, °C. Elle n'est pas écrite dans la spécification — elle y est **dessinée**, et la cellule correspondante est vide dans la couche texte du PDF.

| Rôle | Palier bas | Point 1 | Point 2 | Palier haut |
|---|---|---|---|---|
| chauffage | 22.0 °C | 19.0 °C ext → 22.0 °C | 23.5 °C ext → 23.5 °C | 23.5 °C |
| refroidissement | 23.0 °C | 12.0 °C ext → 23.0 °C | 17.0 °C ext → 25.0 °C | 25.0 °C |

> La consigne est ABSENTE de la couche texte du PDF : elle n'existe que sous forme d'image. Une extraction textuelle conclut à tort qu'il n'y a pas de consigne.
>
> L'attribution chauffage/refroidissement est DÉDUITE de la position relative des courbes, faute de légende sur le graphique. Cohérente (la bande morte passe de 1,0 K à 1,5 K) mais non certifiée.
>
> Les quatre points viennent des étiquettes portées sur le tracé, pas d'une lecture de pixels. Entre deux points, l'interpolation linéaire est supposée d'après l'allure du tracé.
>
> Hors des bornes, les deux courbes sont horizontales — palier bas avant le premier point, palier haut après le second.
>

## Après la saisie

1. Enregistrer le réseau ; noter le chemin du `.asp`.
2. Lancer une simulation ApacheSim sur **l'année complète** — un `.aps` partiel rend toute somme annuelle inexploitable.
3. Lancer `Run_VE_SIA4010_Sonde_APS.py` et renvoyer `outputs/sonde_aps.json`.
4. Le relevé donnera les noms de variables des batteries, du récupérateur et des ventilateurs — les 18 liaisons manquantes.

## Réserves

- Cette fiche décrit le Test 4. Les tests 5 et 6 ajoutent une humidification (contact puis vapeur) et d'autres variantes de récupération : leur réseau devra être saisi séparément, depuis leurs propres spécifications.
- Le nom de classe `iesve` en regard de chaque composant sert à CONFRONTER le réseau saisi à cette fiche, après coup, par `HVACNetwork.components`. Ce n'est pas un nom d'objet à saisir dans l'éditeur.
- Trois entrées manquent pour que ce modèle soit un cas de validation SIA — climat SIA 2028 Kloten, constructions SIA 380/2 tableau 3, fiches d'usage SIA 2024. Le réseau, lui, peut être saisi sans elles : il sert d'abord à relever les noms de variables.

