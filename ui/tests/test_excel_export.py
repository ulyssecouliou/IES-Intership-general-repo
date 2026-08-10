# -*- coding: utf-8 -*-
"""Test d'intégration RÉEL de `ui/export_excel_com.py`.

Ce fichier pilote un VRAI processus Excel (Office 16, présent sur cette
machine de développement -- confirmé par
`reg query "HKLM\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App
Paths\\EXCEL.EXE"`) via `pywin32`, réellement installable ici
(`pip install pywin32`). Il ne s'exécute QUE si `win32com` est importable
(`pytest.importorskip`) -- sur une machine sans Pywin32/Excel, ces tests
sont ignorés plutôt que de faire échouer toute la collecte `ui/tests/`.

**Portée volontairement limitée** (cf. docstring de
`ui/export_excel_com.py`) : ce test construit un classeur JETABLE minimal
(une feuille nommée comme `FEUILLE_DONNEES`), PAS le vrai
`Resultaterfassung_Test1.xlsx` (absent de ce dépôt de développement -- 130
Mo, ADR-001 §7 bis). Il prouve que le CODE COM (ouverture, écriture,
relecture, recalcul, sauvegarde, fermeture) fonctionne, pas que la structure
réelle du classeur SIA officiel correspond à ce que ce module suppose.

Aucun fichier de `SIA_4010_geteilter_Link/` n'est touché par ce test.

--------------------------------------------------------------------------
CONSTAT FAIT DURANT CETTE SESSION -- Excel COM automatisé est BLOQUÉ sur
cette machine de développement précise, malgré Excel installé et `Dispatch`
fonctionnel :
--------------------------------------------------------------------------
`excel.Workbooks.Add()` réussit, mais tout `SaveAs`/`Open` échoue avec une
erreur Trust Center explicite (reproduit aussi en VBScript pur via
`cscript`, donc PAS un artefact de `pywin32` : « You are attempting to open
a file type that is blocked by your File Block settings in the Trust
Center » -- et un échec `SaveAs` générique, code 1004, sans fichier
bloqué). C'est une politique de sécurité du poste (Trust Center / GPO
Office), pas un bug de ce module. Je n'ai PAS tenté de contourner cette
politique (désactiver le File Block/Trust Center serait une modification de
configuration de sécurité, hors de mon périmètre et non demandée).
Conséquence : `_excel_disponible()` ci-dessous fait une sonde COMPLÈTE
(Add + SaveAs + Open + Close), pas seulement `Dispatch`, pour que ces tests
soient **ignorés (skip)** plutôt que rapportés en échec sur CE poste --
mais ils sont écrits pour s'exécuter réellement sur un poste où
l'automatisation Excel est autorisée (ex. VE réel, ou un poste dev sans
cette restriction). `# ⚠ À VÉRIFIER` : rejouer ces tests sur un poste où
`_excel_disponible()` renvoie `True`.
"""

import os
import sys

import pytest

win32com_client = pytest.importorskip('win32com.client')

_ICI = os.path.dirname(os.path.abspath(__file__))
_RACINE = os.path.abspath(os.path.join(_ICI, os.pardir, os.pardir))
if _RACINE not in sys.path:
    sys.path.insert(0, _RACINE)

from engine import test1_engine as moteur  # noqa: E402
from ve_adapter import test1_adapter as adapter  # noqa: E402
from ui import verdict_view as vue  # noqa: E402
from ui import export_excel_com  # noqa: E402


def _excel_disponible():
    """Sonde COMPLÈTE (pas seulement `Dispatch`) : Excel peut-il réellement
    créer, sauvegarder puis rouvrir un classeur via COM sur cette machine ?
    Nécessaire car `Dispatch` seul réussit même quand le Trust Center bloque
    ensuite `SaveAs`/`Open` (constat fait durant cette session, cf.
    docstring de module) -- une sonde partielle ferait passer ces tests en
    ERREUR plutôt qu'en SKIP sur un poste restreint. Ne lève jamais, ne
    laisse aucun fichier ni processus Excel derrière elle."""
    excel = None
    chemin_sonde = None
    try:
        import tempfile
        excel = win32com_client.Dispatch(u'Excel.Application')
        excel.Visible = False
        excel.DisplayAlerts = False
        classeur = excel.Workbooks.Add()
        descripteur, chemin_sonde = tempfile.mkstemp(suffix='.xlsx')
        os.close(descripteur)
        os.remove(chemin_sonde)  # SaveAs exige que le fichier n'existe pas deja ici
        classeur.SaveAs(chemin_sonde, FileFormat=51)
        classeur.Close(SaveChanges=False)
        classeur_relu = excel.Workbooks.Open(chemin_sonde)
        classeur_relu.Close(SaveChanges=False)
        return True
    except Exception:
        return False
    finally:
        if chemin_sonde and os.path.isfile(chemin_sonde):
            try:
                os.remove(chemin_sonde)
            except OSError:
                pass
        if excel is not None:
            try:
                excel.Quit()
            except Exception:
                pass


pytestmark = pytest.mark.skipif(
    not _excel_disponible(),
    reason=u'Excel indisponible via COM sur cette machine -- export_excel_com '
           u'non testable ici (voir docstring du module).')


@pytest.fixture(scope='module')
def vue_test1():
    reference = moteur.charger_reference()
    candidat = adapter.charger_fixture_test1()
    resultat = moteur.evaluer_test1(reference, candidat)
    return vue.construire_vue_test1(resultat)


@pytest.fixture
def classeur_jetable(tmp_path):
    """Construit, via COM, un classeur .xlsx minimal reproduisant UNIQUEMENT
    ce qu'ADR-001 §4 confirme (une feuille `Daten_Testprogramm`) -- pas le
    vrai classeur SIA. Fermé avant d'être rendu au test (le test rouvrira sa
    propre copie via `remplir_classeur_sia`, comme un appelant réel le
    ferait)."""
    chemin = str(tmp_path / 'classeur_jetable_test.xlsx')
    excel = win32com_client.Dispatch(u'Excel.Application')
    excel.Visible = False
    excel.DisplayAlerts = False
    try:
        classeur = excel.Workbooks.Add()
        feuille = classeur.Worksheets(1)
        feuille.Name = export_excel_com.FEUILLE_DONNEES
        # Deux cellules de "colonnes calculees" fictives, pour verifier que
        # CalculateFullRebuild() ne casse rien (formule simple = 2x la
        # cellule Handeingabe).
        feuille.Range('N28').Value = 0
        feuille.Range('B28').Formula = '=N28*2'
        classeur.SaveAs(chemin, FileFormat=51)  # 51 = xlOpenXMLWorkbook (.xlsx)
        classeur.Close(SaveChanges=False)
    finally:
        excel.Quit()
    return chemin


def test_remplir_classeur_sia_sans_carte_cellules_leve_une_erreur_precise(
        classeur_jetable, vue_test1):
    with pytest.raises(export_excel_com.CarteCellulesManquante):
        export_excel_com.remplir_classeur_sia(classeur_jetable, vue_test1, None)


def test_remplir_classeur_sia_ecrit_active_handeingabe_et_recalcule(
        classeur_jetable, vue_test1, tmp_path):
    cle_periode = ('sensible_heating_demand_kwh', '1E', 'annual')
    valeur_attendue = export_excel_com._valeur_ligne(vue_test1, cle_periode)
    assert valeur_attendue is not None  # verifie l'hypothese du test

    carte_cellules = {cle_periode: 'N28'}
    chemin_sortie = str(tmp_path / 'classeur_rempli.xlsx')

    resultat = export_excel_com.remplir_classeur_sia(
        classeur_jetable, vue_test1, carte_cellules, chemin_sortie=chemin_sortie)

    assert resultat == chemin_sortie
    assert os.path.isfile(chemin_sortie)
    # Le classeur SOURCE (jetable) ne doit pas avoir ete modifie -- defense
    # en profondeur (ADR-001 §4 : jamais ecrire sur la source).
    assert os.path.getmtime(classeur_jetable) <= os.path.getmtime(chemin_sortie)

    # Reouverture independante pour verifier ce qui a reellement ete
    # persiste sur disque (pas seulement en memoire COM).
    excel = win32com_client.Dispatch(u'Excel.Application')
    excel.Visible = False
    excel.DisplayAlerts = False
    try:
        classeur = excel.Workbooks.Open(chemin_sortie)
        try:
            feuille = classeur.Worksheets(export_excel_com.FEUILLE_DONNEES)
            assert feuille.Range(export_excel_com.CELLULE_MODE_SAISIE).Value == \
                export_excel_com.VALEUR_MODE_HANDEINGABE
            assert abs(feuille.Range('N28').Value - valeur_attendue) < 1e-6
            # La "colonne calculee" doit refleter le recalcul complet.
            assert abs(feuille.Range('B28').Value - 2 * valeur_attendue) < 1e-6
        finally:
            classeur.Close(SaveChanges=False)
    finally:
        excel.Quit()


def test_remplir_classeur_sia_ignore_les_valeurs_absentes_sans_ecrire_zero(
        classeur_jetable, vue_test1, tmp_path):
    """Une cle (grandeur, cas, periode) absente de vue_test1['lignes'] ne
    doit jamais provoquer l'ecriture d'un faux 0 (CLAUDE.md, "jamais de
    fausse valeur par donnee manquante").

    Pour distinguer un VRAI "non ecrit" d'une coincidence (N28 vaut deja 0
    par defaut dans le classeur jetable), on place d'abord une valeur
    sentinelle non nulle (999) dans N28 : si `remplir_classeur_sia` ecrivait
    un faux 0 a la place d'une valeur candidate absente, ce test le
    detecterait (999 != 0)."""
    cle_periode_inexistante = ('grandeur_qui_nexiste_pas', 'cas_x', 'annual')
    valeur_avant = export_excel_com._valeur_ligne(vue_test1, cle_periode_inexistante)
    assert valeur_avant is None

    excel = win32com_client.Dispatch(u'Excel.Application')
    excel.Visible = False
    excel.DisplayAlerts = False
    try:
        classeur = excel.Workbooks.Open(classeur_jetable)
        try:
            classeur.Worksheets(export_excel_com.FEUILLE_DONNEES).Range('N28').Value = 999
            classeur.Save()
        finally:
            classeur.Close(SaveChanges=False)
    finally:
        excel.Quit()

    carte_cellules = {cle_periode_inexistante: 'N28'}
    chemin_sortie = str(tmp_path / 'classeur_ignore.xlsx')
    export_excel_com.remplir_classeur_sia(
        classeur_jetable, vue_test1, carte_cellules, chemin_sortie=chemin_sortie)

    excel = win32com_client.Dispatch(u'Excel.Application')
    excel.Visible = False
    excel.DisplayAlerts = False
    try:
        classeur = excel.Workbooks.Open(chemin_sortie)
        try:
            feuille = classeur.Worksheets(export_excel_com.FEUILLE_DONNEES)
            # La sentinelle doit etre restee INTACTE : preuve directe que
            # la valeur candidate absente n'a PAS ete remplacee par 0.
            assert feuille.Range('N28').Value == 999
        finally:
            classeur.Close(SaveChanges=False)
    finally:
        excel.Quit()
