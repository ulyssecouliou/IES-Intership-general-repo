# -*- coding: utf-8 -*-
"""Export PDF (ReportLab) -- résumé des verdicts du Test SIA 4010 n° 1 par
classe de validation, pour dossier SIA (CLAUDE.md, "Export d'un rapport
PDF/HTML résumant les verdicts par classe").

--------------------------------------------------------------------------
STATUT D'EXÉCUTION -- IMPORTANT, À LIRE AVANT DE FAIRE CONFIANCE À CE MODULE
--------------------------------------------------------------------------
Contrairement à `ui/dialog_tkinter.py` et `ui/export_excel_com.py`, CE
MODULE A ÉTÉ RÉELLEMENT EXÉCUTÉ dans cet environnement de développement :
`pip install reportlab` a réussi (reportlab 5.0.0) et
`ui/tests/test_export_pdf_reportlab.py` génère un vrai PDF à partir de la
fixture de développement, vérifié non vide et syntaxiquement valide
(en-tête `%PDF-`).

**Réserve qui reste entière** : docs/ADR-001-architecture-MSP.md §2 cite
**ReportLab 3.2** comme version réellement embarquée dans VEScripts
(VEScripts-API-VE2023.pdf §1.3) -- un écart de plusieurs versions majeures
avec la 5.0.0 testée ici. L'API Platypus utilisée ci-dessous
(`SimpleDocTemplate`, `Table`, `TableStyle`, `Paragraph`, `colors.HexColor`)
est stable depuis les toutes premières versions de ReportLab (documentée
ainsi dans le "User Guide" ReportLab depuis les années 2000) et n'utilise
aucune fonctionnalité récente identifiée -- mais ceci reste une
présomption, PAS une preuve contre la 3.2 réelle. `# ⚠ À VÉRIFIER` : rejouer
`ui/tests/test_export_pdf_reportlab.py` depuis une session VEScripts réelle
avant tout usage client.

Ce module ne recalcule rien : il lit exclusivement la structure déjà
produite par `ui/verdict_view.py::construire_vue_test1()`, elle-même un
reflet fidèle du JSON de `engine/test1_engine.py::evaluer_test1()`.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak,
)

from ui import verdict_view as vue


# Couleurs PDF -- même contrat que `COULEUR_FOND_PAR_VERDICT` de
# `ui/dialog_tkinter.py`, redondant avec le texte du verdict (jamais
# uniquement la couleur -- accessibilité).
_COULEUR_PDF_PAR_VERDICT = {
    'vert': colors.HexColor('#d9f2d9'),
    'rouge': colors.HexColor('#f7d6d6'),
    'gris': colors.HexColor('#e6e6e6'),
}

_SYMBOLE_PAR_VERDICT = {'vert': u'OK', 'rouge': u'NON', 'gris': u'--'}


def _style_feuille():
    styles = getSampleStyleSheet()
    return styles


def _entete(vue_test1, styles):
    verdict_global = vue_test1['verdict_global']
    elements = [
        Paragraph(u'Rapport de validation SIA 4010 -- ' +
                  (vue_test1.get('test_id') or 'Test 1'), styles['Title']),
        Spacer(1, 0.3 * cm),
        Paragraph(
            u'Verdict global : <b>{0}</b> -- {1}'.format(
                verdict_global['texte'], _SYMBOLE_PAR_VERDICT.get(
                    verdict_global['couleur'], u'?')),
            styles['Normal']),
        Paragraph(u'Article : ' + verdict_global['article'], styles['Normal']),
        Spacer(1, 0.5 * cm),
    ]
    return elements


def _tableau_classes(vue_test1, styles):
    elements = [Paragraph(u'Classes de validation concernées', styles['Heading2'])]
    donnees = [[u'Classe', u'Test requis', u'Verdict']]
    couleurs_lignes = []
    for ligne in vue_test1['classes']:
        donnees.append([
            ligne['classe'],
            u'Oui' if ligne['test_requis'] else u'Non',
            _SYMBOLE_PAR_VERDICT.get(ligne['couleur'], u'?') + u' ' + ligne['texte_verdict'],
        ])
        couleurs_lignes.append(ligne['couleur'])

    tableau = Table(donnees, colWidths=[3 * cm, 3 * cm, 10 * cm], repeatRows=1)
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
    ]
    for indice, couleur in enumerate(couleurs_lignes, start=1):
        style.append(('BACKGROUND', (0, indice), (-1, indice),
                       _COULEUR_PDF_PAR_VERDICT.get(couleur, colors.white)))
    tableau.setStyle(TableStyle(style))
    elements.append(tableau)
    if vue_test1['classes']:
        elements.append(Paragraph(
            u'Article (classes concernées) : ' + vue_test1['classes'][0]['article'],
            styles['Normal']))
    else:
        elements.append(Paragraph(
            u'Aucune classe concernée trouvée dans le JSON du moteur.',
            styles['Normal']))
    elements.append(Spacer(1, 0.5 * cm))
    return elements


def _tableau_lignes_par_grandeur_cas(vue_test1, styles):
    """Un tableau par (grandeur, cas), dans l'ordre déjà fixé par
    `verdict_view.construire_lignes_test1` (pas de retri ici)."""
    elements = []
    groupes = []
    index_par_cle = {}
    for ligne in vue_test1['lignes']:
        cle = (ligne['grandeur'], ligne['cas'])
        if cle not in index_par_cle:
            index_par_cle[cle] = len(groupes)
            groupes.append([])
        groupes[index_par_cle[cle]].append(ligne)

    for groupe in groupes:
        premiere = groupe[0]
        elements.append(Paragraph(
            premiere['grandeur_libelle'] + u' -- cas ' + premiere['cas'],
            styles['Heading3']))
        donnees = [[u'Période', u'Valeur candidate', u'Verdict']]
        couleurs_lignes = []
        for ligne in groupe:
            donnees.append([
                ligne['periode_libelle'],
                ligne['valeur_candidate_affichee'],
                _SYMBOLE_PAR_VERDICT.get(ligne['couleur'], u'?') + u' ' + ligne['texte_verdict'],
            ])
            couleurs_lignes.append(ligne['couleur'])
        tableau = Table(donnees, colWidths=[4 * cm, 4 * cm, 8 * cm], repeatRows=1)
        style = [
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTSIZE', (0, 0), (-1, -1), 7),
        ]
        for indice, couleur in enumerate(couleurs_lignes, start=1):
            style.append(('BACKGROUND', (0, indice), (-1, indice),
                           _COULEUR_PDF_PAR_VERDICT.get(couleur, colors.white)))
        tableau.setStyle(TableStyle(style))
        elements.append(tableau)
        elements.append(Paragraph(u'Article : ' + premiere['article'], styles['Normal']))
        elements.append(Paragraph(
            u'Source de la référence : ' + premiere['source_valeur_reference'],
            styles['Normal']))
        elements.append(Spacer(1, 0.4 * cm))
    return elements


def generer_pdf_rapport(vue_test1, chemin_pdf):
    """Génère le rapport PDF complet à partir de la structure d'affichage
    déjà construite par `ui/verdict_view.py::construire_vue_test1()`.

    Exécuté réellement dans cet environnement (voir docstring de module) --
    reste soumis à la réserve de version ReportLab 3.2 (VE) vs 5.0.0 (ici).
    """
    styles = _style_feuille()
    document = SimpleDocTemplate(
        chemin_pdf, pagesize=A4,
        leftMargin=1.5 * cm, rightMargin=1.5 * cm,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm)

    elements = []
    elements.extend(_entete(vue_test1, styles))
    elements.extend(_tableau_classes(vue_test1, styles))
    elements.append(PageBreak())
    elements.extend(_tableau_lignes_par_grandeur_cas(vue_test1, styles))

    document.build(elements)
    return chemin_pdf
