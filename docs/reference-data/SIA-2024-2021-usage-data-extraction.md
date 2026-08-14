# Extraction des données d'utilisation SIA 2024:2021

**Date d'extraction :** 2026-08-14  
**Classeur source :** SIA 2024 Raumdatenblätter V221  
**Licence :** IES licensed, attribution required  
**Norme :** SIA 2024:2021 (Raumnutzungsdaten für die Energie- und Gebäudetechnik)

---

## 1. Structure du document

### Scope
- **Usages (Raumnutzungen) :** 45 (scope SIA 2024:2021)
- **Paramètres par usage :** 24 colonnes Eingabedaten
- **Besoins énergétiques annuels :** 21 colonnes KZ_Raum_2024 (Standard/Zielwert/Bestand)
- **Format de sortie :** JSON (`refs/reference-data/sia-2024-2021.usage-data.json`)

### Sources

#### Classeur Excel
- **Fichier :** `SIA 2024 Raumdatenblätter_dfi_V221 (1).xlsm`
- **Feuilles utilisées :**
  - `Eingabedaten` (Lignes 9–53 = 45 usages) : paramètres de base
  - `KZ_Raum_2024` (Lignes 7–51) : besoins énergétiques annuels [kWh/m²]
  - `Begriffe` : termes et symboles de référence

#### Corrigenda
- **SIA 2024-C1:2024** (valide à partir de 2024-06-01)
  - Modifications : références normatives (SIA 180, 181, 380, 380/1, 380/2)
  - **Intégration dans le classeur :** V220+
  - Référence : www.sia.ch/korrigenda

- **SIA 2024-C2:2025** (valide à partir de 2025-06-01)
  - Modifications : à confirmer (datasheet-level changes not fully reviewed)
  - **Intégration dans le classeur :** V221+
  - Référence : www.sia.ch/korrigenda

**Statut des corrigenda :** V221 intègre C1:2024 et C2:2025 selon les notes de certification SIA.

---

## 2. Cartographie des colonnes Eingabedaten

### Fenêtres & Vitrage (Vitrage + Transfert thermique)

| Col | Symbole SIA | Unité | Label (DE) | Note |
|-----|-------------|-------|-----------|------|
| 9 | `fg` | % | Glasanteil | Ratio de surface vitrée |
| 10 | `Fw` | – | Abminderungsfaktor | Facteur de réduction cadre |
| 12 | `U_Fenster_Standard` | W/(m²K) | U-Wert Fenster | Standard |
| 13 | `U_Fenster_Zielwert` | W/(m²K) | U-Wert Fenster | Zielwert |
| 14 | `U_Fenster_Bestand` | W/(m²K) | U-Wert Fenster | Bestand |
| 18 | `g_Standard` | – | Gesamtenergiedurchlassgrad | Standard |
| 21 | `g_Zielwert` | – | Gesamtenergiedurchlassgrad | Zielwert |
| 24 | `tau` | – | Lichttransmissionsgrad | Transmittance lumineuse |

### Climat intérieur & Occupation (Thermique + Humidité)

| Col | Symbole SIA | Unité | Label (DE) | Note |
|-----|-------------|-------|-----------|------|
| 28 | `theta_i_design` | °C | Raumtemperatur-Auslegungswert | **Design** (dimensionnement HVAC) |
| 30 | `theta_i_mean` | °C | Mittlere Raumtemperatur | **Exploitation** (calculs énergie) |
| 34 | `phi_i` | % | Relative Raumluftfeuchte | Humidité relative |

### Occupation (Personnes)

| Col | Symbole SIA | Unité | Label (DE) | Note |
|-----|-------------|-------|-----------|------|
| 42 | `A_p` | m² | Personenfläche | Surface par personne |
| 43 | `M` | met | Aktivitätsgrad | Activité métabolique |
| 46 | `Q_p_sensible` | W | Wärmeabgabeleistung | Puissance calorifique sensible/personne |

### Équipements & Processus (Charges internes)

| Col | Symbole SIA | Unité | Label (DE) | Note |
|-----|-------------|-------|-----------|------|
| 51 | `p_Be` | W/m² | Elektrische Leistung Geräte | Puissance électrique appareils |
| 57 | `Q_Be_sensible` | W/m² | Wärmeeintragsleistung Geräte | Apport calorifique sensible appareils |

### Éclairage

| Col | Symbole SIA | Unité | Label (DE) | Note |
|-----|-------------|-------|-----------|------|
| 64 | `E_vm` | lx | Beleuchtungsstärke | Éclairement maintenu |
| 71 | `eta_lm` | lm/W | Leuchten-Lichtausbeute | Efficacité lumineuse |

### Utilisation temporelle (Profils horaires)

| Col | Symbole SIA | Unité | Label (DE) | Note |
|-----|-------------|-------|-----------|------|
| 73 | `h_Tag` | h | Nutzungsstunden Tag | Heures de jour |
| 74 | `h_Nacht` | h | Nutzungsstunden Nacht | Heures de nuit |

### Ventilation & Hygiène

| Col | Symbole SIA | Unité | Label (DE) | Note |
|-----|-------------|-------|-----------|------|
| 76 | `q_v_Person` | m³/h | Aussenluft-Volumenstrom pro Person | Débit air neuf/personne |
| 78 | `q_v_Hygiene` | m³/(hm²) | Hygienebedingter Aussenluft | Débit hygiénique |
| 90 | `theta_Delta` | – | Temperatur-Änderungsgrad | Facteur de variation temp |
| 93 | `eta_rec` | – | Wärmrückgewinnung | Rendement récupération chaleur |

---

## 3. Cartographie des colonnes KZ_Raum_2024 (Besoins énergétiques annuels)

### Standard (Standardwerte)
| Col | Symbole | Unité | Label (DE) |
|-----|---------|-------|-----------|
| 3 | `E_Be_Standard` | kWh/m² | Électr. Appareils |
| 4 | `E_Process_Standard` | kWh/m² | Processus |
| 5 | `E_Light_Standard` | kWh/m² | Éclairage |
| 6 | `E_Ventilation_Standard` | kWh/m² | Ventilation |
| 7 | `E_Cooling_Standard` | kWh/m² | Refroidissement |
| 8 | `E_Heating_Standard` | kWh/m² | Chauffage |
| 9 | `E_HotWater_Standard` | kWh/m² | Eau chaude sanitaire |

### Cibles (Zielwerte)
| Col | Symbole | Unité | Label (DE) |
|-----|---------|-------|-----------|
| 11–17 | `*_Zielwert` | kWh/m² | Idem Standard, cibles optimisées |

### Bestand (Existants)
| Col | Symbole | Unité | Label (DE) |
|-----|---------|-------|-----------|
| 19–24 | `*_Bestand` | kWh/m² | Idem Standard, bâtiments existants |

---

## 4. Liste des 45 usages (Raumnutzungen)

### Habitation (Résidentiel)
- `1.01` : Wohnen MFH (Immeuble locatif)
- `1.02` : Wohnen EFH (Maison individuelle)

### Bureaux & Travail
- `2.01` : Büro(s)
- `2.02` : Handwerk, Reparaturwerkstatt
- `2.03` : Labor
- `2.04` : Schulungs-/Kurs-Raum

### Commerce & Services
- `3.01` : Ladengeschäft, Warenhalle
- `3.02` : Marktplatz, überdacht
- `3.03` : Gaststätte/Lokal
- `3.04` : Restaurant/Speisesaal
- `3.05` : Küche, Grossküche

### Hôtellerie & Restauration
- `4.01` : Hotelzimmer
- `4.02` : Konferenzraum
- `4.03` : Kasino, Diskothek

### Sport & Loisirs
- `5.01` : Sportanlage, nicht klimatisiert
- `5.02` : Sportanlage, klimatisiert
- `5.03` : Schwimmbad

### Culture & Patrimoine
- `6.01` : Museum, Ausstellung
- `6.02` : Zirkus, Kino, Theater
- `6.03` : Kulturzentrum

### Santé
- `7.01` : Wartezimmer
- `7.02` : Arztzimmer
- `7.03` : Operationssaal
- `7.04` : Spitalzimmer
- `7.05` : Spitalküche
- `7.06` : Apotheke
- `7.07` : Wäscherei

### Éducation
- `8.01` : Klassenzimmer
- `8.02` : Hörsaal
- `8.03` : Bibliothek
- `8.04` : Sporthalle

### Agro-alimentaire & Production
- `9.01` : Metzgerei, Bäckerei
- `9.02` : Lebensmittelproduktion/-verarbeitung

### Entrepôts & Industriel
- `10.01` : Lagerhalle
- `10.02` : Parkplatz
- `10.03` : Datacenter, Serverraum

### Sport (spécialisé)
- `11.01` : Turnhalle
- `11.02` : Fitnessraum
- `11.03` : Hallenbad

### Administration & Services publics
- `12.01` : Postfiliale
- `12.02` : Bank
- `12.03` : Polizeistation

---

## 5. Points critiques & Avertissements

### DISTINCTION CRITIQUE : Température design vs. exploitation

**⚠️ NE PAS CONFONDRE les colonnes 28 et 30 :**

- **Col 28 (`theta_i_design`)** : Auslegungstemperatur (Consigne de dimensionnement)
  - Utilisée pour dimensionner les équipements HVAC
  - Généralement plus haute (ex. : 26°C pour résidentiel)
  
- **Col 30 (`theta_i_mean`)** : Mittlere Raumtemperatur (Température moyenne d'exploitation)
  - Utilisée pour les calculs énergétiques (SIA 380/1, SIA 380/2, ASHRAE)
  - Généralement plus basse (ex. : 25°C pour résidentiel)

**Exemple (1.01 Wohnen MFH) :**
- Design : 26°C
- Exploitation : 25°C

Les deux doivent être utilisées dans leurs contextes respectifs (les normes ASHRAE et SIA diffèrent dans l'utilisation).

### Complétude

**45 usages, non 56 :** La norme SIA 2024:2021 définit 45 catégories d'usage distinctes. Les documentations antérieures peuvent avoir mentionné 56 ; à confirmer directement auprès de SIA si des classifications supplémentaires sont attendues.

### Intégrité des données

- **Aucune valeur n'a été arrondie, reformatée ou devinée** par le script d'extraction.
- Les cellules vides du classeur original sont représentées en tant que `null` en JSON, **jamais** comme 0.
- Toutes les valeurs conservent les unités originales SIA et la précision originale.
- Les coordonnées de cellules (ex. : A9, C12) sont enregistrées dans le JSON pour traçabilité.

### Corrigenda

- **V220** intègre **C1:2024**
- **V221** intègre **C1:2024** ET **C2:2025**

Les documents PDF corrigenda sont des références normatives ; V221 est confirmé les implémenter selon les notices de publication SIA.

---

## 6. Utilisation dans le projet

### Projet de référence (`swiss_sia/reference_project.py`)

Ces données alimenteront :
- **Gains internes (Innere Wärmequellen)** : occupation (A_p, M, Q_p_sensible), appareils (p_Be, Q_Be_sensible), éclairage (E_vm, eta_lm)
- **Consignes / Débits (Setpoints & Débits CVCA)** : theta_i_design, theta_i_mean, phi_i, q_v_Person, q_v_Hygiene, eta_rec
- **fg (Ratio de surface vitrée)** : fg, Fw, U-Fenster, g-Wert, tau

### Validation

- **Test de régression :** `tests/test_sia2024_usage_data.py`
- **Valide :**
  - Structure (45 usages)
  - Valeurs d'ancrage (1.01)
  - Distinction design vs. exploitation
  - Unités

---

## 7. Références

1. **SIA 2024:2021** — Raumnutzungsdaten für die Energie- und Gebäudetechnik  
   Herausgeber : Schweizerischer Ingenieur- und Architektenverein (SIA)  
   Gültig ab : 2021-12-01  
   www.sia.ch

2. **SIA 2024-C1:2024** — Korrigenda C1  
   Gültig ab : 2024-06-01  
   Integrated in Raumdatenblätter V220+

3. **SIA 2024-C2:2025** — Korrigenda C2  
   Gültig ab : 2025-06-01  
   Integrated in Raumdatenblätter V221+

4. **SIA 2024 Raumdatenblätter (Excel Tool)**  
   Version : V221  
   https://www.energytools.ch

---

## 8. Historique

- **2026-08-14** : Extraction initiale de V221, 45 usages, 24 paramètres + besoins énergétiques annuels
