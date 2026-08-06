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
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak,
)

from ui import design_ies as design
from ui import verdict_view as vue


# Couleurs PDF -- même contrat que `COULEUR_FOND_PAR_VERDICT` de
# `ui/dialog_tkinter.py`, redondant avec le texte du verdict (jamais
# uniquement la couleur -- accessibilité).
_COULEUR_PDF_PAR_VERDICT = dict(
    (couleur, colors.HexColor(design.fond_verdict(couleur)))
    for couleur in ('vert', 'rouge', 'gris'))

# ASCII plutot que des glyphes : Helvetica n a pas de coche ni de croix, et
# ReportLab afficherait un carre noir. Le symbole reste la, ce qui compte
# c est de ne jamais coder le verdict par la seule couleur.
_SYMBOLE_PAR_VERDICT = dict(design.SYMBOLE_ASCII_PAR_VERDICT)

_NAVY = colors.HexColor(design.NAVY)
_ACCENT = colors.HexColor(design.ACCENT)
_TEINTE = colors.HexColor(design.TEINTE_BLEUE)
_GRIS_CLAIR = colors.HexColor(design.GRIS_CLAIR)
_BORDURE = colors.HexColor(design.GRIS_BORDURE)
_TEXTE = colors.HexColor(design.TEXTE)
_TEXTE_ATTENUE = colors.HexColor(design.TEXTE_ATTENUE)


def _style_tableau(nb_lignes, couleurs_lignes, largeurs_speciales=None):
    """Style de tableau commun a tout le rapport.

    En-tete navy, filets fins, zebrure discrete : le site d IES divise par
    l espace, pas par des traits epais. Le fond de verdict est applique
    par-dessus la zebrure, pour qu il reste lisible.

    Args:
        nb_lignes: Nombre de lignes de donnees, en-tete exclu.
        couleurs_lignes: Verdict de chaque ligne, dans l ordre.
        largeurs_speciales: Ignore ; conserve pour la lisibilite des appels.

    Returns:
        list: Commandes de TableStyle.
    """
    style = [
        ('BACKGROUND', (0, 0), (-1, 0), _NAVY),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), design.POLICE_TITRE),
        ('FONTNAME', (0, 1), (-1, -1), design.POLICE_TEXTE),
        ('FONTSIZE', (0, 0), (-1, -1), design.TAILLE_TABLEAU),
        ('TEXTCOLOR', (0, 1), (-1, -1), _TEXTE),
        ('GRID', (0, 0), (-1, -1), design.FILET_PT, _BORDURE),
        ('LINEBELOW', (0, 0), (-1, 0), design.FILET_ENTETE_PT, _NAVY),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
    ]
    for indice in range(1, nb_lignes + 1):
        if indice % 2 == 0:
            style.append(('BACKGROUND', (0, indice), (-1, indice), _GRIS_CLAIR))
    for indice, couleur in enumerate(couleurs_lignes, start=1):
        style.append(('BACKGROUND', (0, indice), (-1, indice),
                      _COULEUR_PDF_PAR_VERDICT.get(couleur, _GRIS_CLAIR)))
    return style



def _style_feuille():
    """Feuille de styles aux couleurs IES.

    Les styles de ReportLab sont noirs et serif par defaut ; on les repasse
    en Helvetica et en navy, et on ajoute deux styles propres au rapport.

    Returns:
        StyleSheet1: Feuille prete a l emploi.
    """
    styles = getSampleStyleSheet()
    styles['Title'].fontName = design.POLICE_TITRE
    styles['Title'].fontSize = design.TAILLE_TITRE
    styles['Title'].textColor = _NAVY
    styles['Title'].alignment = 0          # ferre a gauche, comme le site
    styles['Title'].spaceAfter = 4

    for nom in ('Heading2', 'Heading3'):
        styles[nom].fontName = design.POLICE_TITRE
        styles[nom].textColor = _NAVY
    styles['Heading2'].fontSize = design.TAILLE_SOUS_TITRE
    styles['Heading3'].fontSize = design.TAILLE_SECTION

    for nom in ('Normal', 'BodyText'):
        styles[nom].fontName = design.POLICE_TEXTE
        styles[nom].fontSize = design.TAILLE_TEXTE
        styles[nom].leading = design.TAILLE_TEXTE * design.INTERLIGNE
        styles[nom].textColor = _TEXTE

    styles.add(ParagraphStyle(
        'IESNote', parent=styles['Normal'],
        fontSize=design.TAILLE_NOTE,
        leading=design.TAILLE_NOTE * design.INTERLIGNE,
        textColor=_TEXTE_ATTENUE))
    styles.add(ParagraphStyle(
        'IESSousTitre', parent=styles['Normal'],
        fontSize=design.TAILLE_SOUS_TITRE, textColor=_ACCENT,
        spaceAfter=10))
    return styles


def _bandeau(canevas, document):
    """Dessine le bandeau de marque et le pied de page, sur chaque page.

    Un filet navy en tete et le rappel de provenance en pied : c est ce qui
    rend un document identifiable sans l alourdir. Le site d IES divise par
    l espace, pas par des aplats.

    Args:
        canevas: Canevas ReportLab.
        document: Document en cours de rendu.
    """
    canevas.saveState()
    largeur, hauteur = A4

    # Filet de tete, aux couleurs de marque.
    canevas.setFillColor(_NAVY)
    canevas.rect(0, hauteur - 0.42 * cm, largeur, 0.42 * cm, stroke=0, fill=1)
    canevas.setFillColor(_ACCENT)
    canevas.rect(0, hauteur - 0.52 * cm, largeur, 0.10 * cm, stroke=0, fill=1)

    # Pied : provenance a gauche, pagination a droite.
    canevas.setFont(design.POLICE_TEXTE, design.TAILLE_NOTE)
    canevas.setFillColor(_TEXTE_ATTENUE)
    canevas.drawString(
        design.MARGE_CM * cm, 0.85 * cm,
        u'IES — Validation SIA 4010 — document genere, non certifie')
    canevas.drawRightString(
        largeur - design.MARGE_CM * cm, 0.85 * cm, u'page %d' % document.page)
    canevas.setStrokeColor(_BORDURE)
    canevas.setLineWidth(design.FILET_PT)
    canevas.line(design.MARGE_CM * cm, 1.15 * cm,
                 largeur - design.MARGE_CM * cm, 1.15 * cm)
    canevas.restoreState()


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
    style = _style_tableau(len(donnees) - 1, couleurs_lignes)
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
        tableau.setStyle(TableStyle(
            _style_tableau(len(donnees) - 1, couleurs_lignes)))
        elements.append(tableau)
        # Article et provenance en style de note : présents et vérifiables,
        # sans concurrencer les chiffres à la lecture.
        elements.append(Paragraph(u'Article : ' + premiere['article'],
                                  styles['IESNote']))
        elements.append(Paragraph(
            u'Source de la référence : ' + premiere['source_valeur_reference'],
            styles['IESNote']))
        elements.append(Spacer(1, 0.4 * cm))
    return elements


def _synthese_classes(vues, styles):
    """Page de tête du rapport client : le verdict par CLASSE, tous tests
    confondus.

    C'est la seule page qui réponde à « quelles classes ce logiciel a-t-il ? ».
    Elle nomme donc explicitement les tests exigés qui MANQUENT au dossier :
    une classe dont un test requis est absent n'est jamais verte, et le
    lecteur doit pouvoir vérifier pourquoi sans nous croire sur parole.
    """
    lignes_synthese = vue.construire_synthese_classes(vues)

    elements = [
        Paragraph(u'Validation SIA 4010 — synthèse par classe', styles['Title']),
        Spacer(1, 0.3 * cm),
        Paragraph(
            u'Tests présents dans ce dossier : ' +
            u', '.join(str(v.get('test_id') or '?') for v in vues),
            styles['Normal']),
        Spacer(1, 0.4 * cm),
    ]

    donnees = [[u'Classe', u'Tests exigés', u'Couverts', u'Verdict']]
    couleurs_lignes = []
    for ligne in lignes_synthese:
        donnees.append([
            ligne['classe'],
            u', '.join(ligne['tests_exiges']),
            u', '.join(ligne['tests_couverts']) or u'—',
            Paragraph(ligne['texte_verdict'], styles['BodyText']),
        ])
        couleurs_lignes.append(ligne['couleur'])

    tableau = Table(donnees, colWidths=[1.8 * cm, 4.6 * cm, 2.2 * cm, 9.4 * cm],
                    repeatRows=1)
    style = _style_tableau(len(donnees) - 1, couleurs_lignes)
    tableau.setStyle(TableStyle(style))
    elements.append(tableau)

    elements.append(Spacer(1, 0.4 * cm))
    elements.append(Paragraph(u'Article : ' + vue.CITATION_TABLEAU_63,
                              styles['Normal']))
    elements.append(Paragraph(
        u'Une classe n\'est déclarée conforme que si <b>tous</b> les tests que '
        u'le tableau 63 lui impose sont présents dans ce dossier et conformes. '
        u'Un test absent rend la classe non concluante — il n\'est jamais '
        u'ignoré.', styles['Normal']))
    return elements


def generer_pdf_rapport_multi(vues, chemin_pdf):
    """Rapport PDF couvrant plusieurs tests.

    Page 1 : synthèse par classe, tous tests confondus. Puis une section par
    test, dans l'ordre reçu.

    Exécuté réellement dans cet environnement (voir docstring de module) --
    reste soumis à la réserve de version ReportLab 3.2 (VE) vs 5.0.0 (ici).
    """
    if not vues:
        raise ValueError(
            u'aucune vue fournie : un rapport vide pourrait passer pour un '
            u'dossier sans anomalie.')

    styles = _style_feuille()
    document = SimpleDocTemplate(
        chemin_pdf, pagesize=A4,
        leftMargin=design.MARGE_CM * cm, rightMargin=design.MARGE_CM * cm,
        # Le haut laisse la place au bandeau de marque, le bas au pied.
        topMargin=1.5 * cm, bottomMargin=1.6 * cm,
        title=u'Validation SIA 4010', author=u'IES')

    elements = _synthese_classes(vues, styles)
    for une_vue in vues:
        elements.append(PageBreak())
        elements.extend(_entete(une_vue, styles))
        elements.extend(_tableau_classes(une_vue, styles))
        elements.extend(_tableau_lignes_par_grandeur_cas(une_vue, styles))

    document.build(elements, onFirstPage=_bandeau, onLaterPages=_bandeau)
    return chemin_pdf


def generer_pdf_rapport(vue_test1, chemin_pdf):
    """Rapport d'un seul test -- conservé pour les appelants existants.

    Délègue à `generer_pdf_rapport_multi` : le rapport commence donc lui aussi
    par la synthèse par classe, qui signalera les tests absents du dossier.
    """
    return generer_pdf_rapport_multi([vue_test1], chemin_pdf)
