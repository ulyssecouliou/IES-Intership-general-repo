# Swiss Compliance Checker

**Outil de vérification de conformité aux normes suisses SIA 380/2 et SIA 4010 pour les modèles IESVE.**

---

## 📌 Description
Le **Swiss Compliance Checker** est un outil conçu pour :
- **Scanner automatiquement** le projet VE actif dans IESVE.
- **Extraire toutes les données** accessibles via l'API IESVE.
- **Analyser le modèle** (enveloppe, ouvertures, systèmes CVC, etc.).
- **Vérifier la conformité** aux normes **SIA 380/2** et **SIA 4010**.
- **Détecter les erreurs**, **avertissements**, et **recommandations**.
- **Produire un score de conformité global** (0-100).
- **Générer un rapport Excel professionnel** avec :
  - Onglets dédiés (Résumé, Résultats SIA, Alertes, etc.).
  - Mise en forme conditionnelle (couleurs pour PASS/WARNING/FAIL).
  - Graphiques et indicateurs visuels.

---

## 📁 Structure du Projet
```
SwissComplianceChecker/
│
├── config.py                  # Configuration des seuils SIA et poids des scores.
├── data_extractor.py          # Extraction des données du modèle VE.
├── model_analyzer.py          # Analyse du modèle (géométrie, U-values, WWR, etc.).
├── rule_engine.py             # Moteur de règles pour SIA 380/2 et SIA 4010.
├── sia380_checker.py          # Vérification des règles SIA 380/2.
├── sia4010_checker.py         # Vérification des règles SIA 4010 (7 tests).
├── health_score.py            # Calcul des scores (Compliance Score et Health Score).
├── excel_report.py            # Génération du rapport Excel.
├── main.py                    # Point d'entrée du script.
│
├── requirements.txt           # Dépendances Python.
└── README.md                  # Ce fichier.
```

---

## 🚀 Installation
1. **Copier le dossier `SwissComplianceChecker`** dans le répertoire des scripts IESVE :
   - Exemple : `C:\Program Files\Integrated Environmental Solutions\Virtual Environment 2023\Scripts\`
2. **Installer les dépendances** (si nécessaire) :
   ```bash
   pip install -r requirements.txt
   ```
   > **Note** : utiliser `xlsxwriter` dans l'environnement VEScripts IESVE. `openpyxl` n'est pas retenu pour les scripts VE.

---

## 🎯 Utilisation
### **Méthode 1 : Exécution via l'Éditeur de Scripts IESVE**
1. Ouvrir **IESVE** et charger un **projet VE**.
2. Ouvrir l'**Éditeur de Scripts** (`Tools > Scripting > Script Editor`).
3. Charger le fichier `main.py` depuis le dossier `SwissComplianceChecker`.
4. Exécuter le script (`Run > Run Script`).
5. Le rapport Excel sera généré dans le dossier `reports/`.

### **Méthode 2 : Exécution en Ligne de Commande (si Python est disponible)**
```bash
cd SwissComplianceChecker
python main.py
```
> **Note** : Cette méthode nécessite que **IESVE soit ouvert** avec un projet VE actif.

---

## 📊 Sorties
- **Fichier Excel** : `reports/Swiss_Compliance_Report.xlsx`
  - **SUMMARY** : Résumé des scores et KPI.
  - **COMPLIANCE RESULTS** : Résultats détaillés des vérifications SIA 380/2 et SIA 4010.
  - **ALERTS** : Liste des alertes (erreurs, avertissements, informations).
  - **DETAILED SCORES** : Scores détaillés par catégorie.
  - **ROOMS** : Données des pièces (surfaces, volumes, WWR, etc.).
- **Fichier Log** : `reports/swiss_compliance_checker.log` (pour le débogage).

---

## 🔧 Configuration
- **`config.py`** : Modifier les **seuils SIA** et **poids des scores** selon vos besoins.
  - Exemple : adapter les seuils SIA 380/2 ou la matrice de référence validée.
- **`excel_report.py`** : Personnaliser le **format du rapport Excel** (couleurs, styles, etc.).

---

## 📌 Exigences
- **IESVE 2023+** (avec API Python activée).
- **Python 3.8+** (inclus dans IESVE).
- **Modules Python** :
  - `xlsxwriter` (inclus dans IESVE).
  - `iesve` (API IESVE, inclus).

---

## 🛠️ Développement
### **Ajouter une Nouvelle Règle SIA**
1. **Dans `rule_engine.py`** :
   - Définir une nouvelle `Rule` et l'ajouter au `RuleEngine`.
2. **Dans `sia380_checker.py` ou `sia4010_checker.py`** :
   - Ajouter la règle au validateur correspondant.

### **Étendre les Fonctionnalités**
- **Ajouter un nouvel onglet Excel** :
  - Modifier `excel_report.py` pour ajouter un nouvel onglet (ex: `HVAC`).
- **Ajouter un nouveau calcul** :
  - Modifier `model_analyzer.py` pour ajouter une nouvelle méthode (ex: calcul du **WWR moyen**).

---

## 📞 Support
Pour toute question ou problème, consulter :
- **Documentation IESVE** : [VEScripts User Guide](https://www.iesve.com/support/faq/pdf/vescriptsguide)
- **Normes SIA** :
  - [SIA 380/2](https://www.sia.ch/)
  - [SIA 4010](https://www.sia.ch/fr/normes/sia-4010/)

---

## 📜 Licence
Ce projet est **libre d'utilisation** pour les utilisateurs de IESVE.
© 2026 - Swiss Compliance Checker
