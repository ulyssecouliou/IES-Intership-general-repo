"""
Point d'entrée du Swiss Compliance Checker.
Ce script orchestrer l'extraction des données, la vérification SIA, et la génération du rapport.
"""

import logging
import sys
import os
import importlib
import re
import shutil
import unicodedata
from datetime import datetime
from typing import Optional

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Importer l'API IESVE
import iesve

# Importer les modules du projet
from config import OUTPUT_DIR, EXCEL_REPORT_NAME
import data_extractor as data_extractor_module
import model_analyzer as model_analyzer_module
import rule_engine as rule_engine_module
import sia380_checker as sia380_checker_module
import sia4010_checker as sia4010_checker_module
import health_score as health_score_module
import excel_report as excel_report_module

# VE Scripts can keep a Python interpreter alive between Run clicks. Force local
# modules to reload so the button always uses the latest workspace code.
data_extractor_module = importlib.reload(data_extractor_module)
model_analyzer_module = importlib.reload(model_analyzer_module)
rule_engine_module = importlib.reload(rule_engine_module)
sia380_checker_module = importlib.reload(sia380_checker_module)
sia4010_checker_module = importlib.reload(sia4010_checker_module)
health_score_module = importlib.reload(health_score_module)
excel_report_module = importlib.reload(excel_report_module)

VEDataExtractor = data_extractor_module.VEDataExtractor
ModelAnalyzer = model_analyzer_module.ModelAnalyzer
RuleEngine = rule_engine_module.RuleEngine
SIA3801Checker = sia380_checker_module.SIA3801Checker
SIA4010Checker = sia4010_checker_module.SIA4010Checker
HealthScoreCalculator = health_score_module.HealthScoreCalculator
ExcelReportGenerator = excel_report_module.ExcelReportGenerator

# Créer le dossier de sortie s'il n'existe pas
REPORTS_DIR = os.path.join(PROJECT_ROOT, OUTPUT_DIR)
os.makedirs(REPORTS_DIR, exist_ok=True)

# Configurer le logging avec un encodage compatible
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(
            os.path.join(REPORTS_DIR, "swiss_compliance_checker.log"),
            encoding='utf-8'  # Encodage UTF-8 pour les fichiers
        ),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


def _safe_filename_part(value: object, fallback: str = "VE_Project") -> str:
    """Return a Windows-safe filename fragment for VE project names."""
    text = str(value or "").strip() or fallback
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r'[<>:"/\\|?*]+', "_", text)
    text = re.sub(r"\s+", "_", text)
    text = text.strip("._ ")
    return (text or fallback)[:80]


def _object_label(value: object, fallback: str) -> str:
    """Extract a readable label from a VE API object without assuming its shape."""
    for attr in ("name", "name_attr", "id"):
        try:
            candidate = getattr(value, attr, None)
            if callable(candidate):
                candidate = candidate()
            if candidate:
                return str(candidate)
        except Exception:
            continue
    return fallback


def _build_unique_report_path(project_path: object, model: object = None) -> str:
    """Build a timestamped report path so VE runs do not overwrite each other."""
    project_name = os.path.basename(os.path.normpath(str(project_path or ""))) or "VE_Project"
    project_name = _safe_filename_part(project_name)
    model_name = _safe_filename_part(_object_label(model, "Model_01"), "Model_01")
    base_name, extension = os.path.splitext(EXCEL_REPORT_NAME)
    extension = extension or ".xlsx"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{base_name}__{project_name}__{model_name}__{timestamp}{extension}"
    candidate = os.path.join(REPORTS_DIR, filename)

    suffix = 2
    while os.path.exists(candidate):
        filename = f"{base_name}__{project_name}__{model_name}__{timestamp}_{suffix}{extension}"
        candidate = os.path.join(REPORTS_DIR, filename)
        suffix += 1
    return candidate


def _copy_latest_report_alias(source_path: str) -> Optional[str]:
    """Keep Swiss_Compliance_Report.xlsx as a convenience alias when possible."""
    latest_path = os.path.join(REPORTS_DIR, EXCEL_REPORT_NAME)
    if os.path.abspath(source_path) == os.path.abspath(latest_path):
        return latest_path
    temp_path = latest_path + ".tmp"
    try:
        shutil.copy2(source_path, temp_path)
        os.replace(temp_path, latest_path)
        return latest_path
    except PermissionError:
        logger.warning(
            "Impossible de mettre a jour %s car le fichier est probablement ouvert. "
            "Le rapport archive reste disponible: %s",
            latest_path,
            source_path,
        )
    except Exception as exc:
        logger.warning("Impossible de copier le rapport latest %s: %s", latest_path, exc)
    try:
        if os.path.exists(temp_path):
            os.remove(temp_path)
    except Exception:
        pass
    return None


def main():
    """
    Exécute l'analyse de conformité SIA et génère le rapport.
    """
    try:
        logger.info("Debut de l'analyse du modele VE...")

        # 1. Charger le projet VE actif
        project = iesve.VEProject.get_current_project()
        if not project:
            raise RuntimeError("Aucun projet VE actif trouve. Veuillez ouvrir un projet dans IESVE.")

        logger.info(f"Projet VE charge: {project.path}")

        # 2. Extraire les données du modèle
        logger.info("Extraction des donnees du modele VE...")
        data_extractor = VEDataExtractor(project)
        model_analyzer = ModelAnalyzer(data_extractor)
        logger.info(f"Module model_analyzer charge depuis: {model_analyzer_module.__file__}")

        # 3. Vérifier SIA 380/2 avec un moteur de règles dédié
        logger.info("Verification SIA 380/2...")
        sia3801_checker = SIA3801Checker(model_analyzer, RuleEngine())
        sia3801_results = sia3801_checker.check_all()

        # 4. Vérifier SIA 4010 avec un moteur séparé pour éviter le mélange de règles
        logger.info("Verification SIA 4010...")
        sia4010_checker = SIA4010Checker(model_analyzer, RuleEngine())
        sia4010_results = sia4010_checker.check_all()

        # 5. Calculer les scores
        logger.info("Calcul des scores de conformite...")
        score_calculator = HealthScoreCalculator()
        score_result = score_calculator.calculate_scores(sia3801_results, sia4010_results)

        # 7. Générer le rapport Excel
        logger.info("Generation du rapport Excel...")
        unique_report_path = _build_unique_report_path(project.path, data_extractor.model)
        report_generator = ExcelReportGenerator(output_path=unique_report_path, model_analyzer=model_analyzer)
        rooms_data = model_analyzer.analyze_all_rooms()
        report_generator.generate_report(score_result, sia3801_results, sia4010_results, rooms_data)
        latest_report_path = _copy_latest_report_alias(report_generator.output_path)

        # 8. Afficher les résultats
        logger.info("Analyse terminee avec succes !")
        logger.info(f"Compliance Score: {score_result.compliance_score:.1f}/100")
        logger.info(f"Health Score: {score_result.health_score:.1f}/100")
        logger.info(f"Rapport Excel genere: {report_generator.output_path}")
        if latest_report_path:
            logger.info(f"Alias dernier rapport mis a jour: {latest_report_path}")

        # 9. Afficher les alertes critiques
        critical_alerts = [alert for alert in score_result.alerts if alert.severity.value == "Critical"]
        if critical_alerts:
            logger.warning(f"{len(critical_alerts)} erreurs critiques detectees:")
            for alert in critical_alerts:
                logger.warning(f"   - {alert.description} (Recommandation: {alert.recommendation})")

        # 10. Afficher un résumé des scores détaillés
        logger.info("Scores detailles par categorie:")
        for category, score in score_result.detailed_scores.items():
            logger.info(f"   - {category}: {score:.1f}/100")

    except Exception as e:
        logger.error(f"Erreur critique lors de l'analyse: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
