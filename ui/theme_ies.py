# -*- coding: utf-8 -*-
u"""Applique la charte IES à une fenêtre ttk.

`ui/design_ies.py` porte les jetons — relevés sur la feuille de style publique
d'iesve.com. Ce module les APPLIQUE : sans lui, les jetons existent et le
dialogue reste en ttk par défaut, gris système.

LE POINT TECHNIQUE QUI DÉCIDE DE TOUT. Sur Windows, ttk démarre sur le thème
`vista` (ou `winnative`), qui délègue le rendu au système et **ignore
purement et simplement `background`, `foreground` et `fieldbackground`** sur
la plupart des widgets. Une note de `dialog_tkinter.py` le signalait déjà :
« ⚠ À VÉRIFIER — le rendu visuel réel des couleurs ». C'est vérifié : sans
changer de thème, les couleurs de marque n'apparaissent pas.

Le thème `clam` les honore. C'est pourquoi `appliquer()` en change, et c'est
la seule raison — pas une préférence esthétique.

CE QUE LA CHARTE DIT, ET QU'ON SUIT ICI. Le site divise par l'espace, pas par
des traits épais : bandeau navy pleine largeur, fond gris très clair, cartes
blanches, filets fins, accent bleu réservé aux actions. Les aplats de couleur
vive sont rares et petits.

ACCESSIBILITÉ. Aucun verdict n'est porté par la seule couleur : le symbole et
le texte l'accompagnent toujours (`design_ies.symbole`). Cette règle survit au
changement de thème, et c'est elle qui rend l'interface lisible pour un
lecteur daltonien — ou sur un poste où le thème refuserait encore les fonds.
"""

from __future__ import print_function

from ui import design_ies as design

#: Thème ttk qui honore les couleurs. Voir la note de module : ce n'est pas un
#: choix de style, c'est la condition pour que la charte s'affiche.
THEME_REQUIS = 'clam'

#: Noms de styles exposés. Les préfixer évite d'écraser les styles d'un autre
#: dialogue VEScripts tournant dans le même interpréteur — qui persiste d'un
#: clic sur Run au suivant.
PREFIXE = 'IES.'

STYLE_FOND = PREFIXE + 'TFrame'
STYLE_CARTE = PREFIXE + 'Carte.TFrame'
STYLE_BANDEAU = PREFIXE + 'Bandeau.TFrame'
STYLE_TITRE = PREFIXE + 'Titre.TLabel'
STYLE_SOUS_TITRE = PREFIXE + 'SousTitre.TLabel'
STYLE_TEXTE = PREFIXE + 'TLabel'
STYLE_ATTENUE = PREFIXE + 'Attenue.TLabel'
STYLE_SECTION = PREFIXE + 'Section.TLabel'
STYLE_BOUTON = PREFIXE + 'TButton'
STYLE_BOUTON_ACCENT = PREFIXE + 'Accent.TButton'
STYLE_ARBRE = PREFIXE + 'Treeview'
STYLE_ETIQUETTE_CADRE = PREFIXE + 'TLabelframe'

#: Police d'interface. Camphor Pro (celle du site) est commerciale ; Segoe UI
#: est la plus proche disponible d'origine sous Windows, où tourne VE.
POLICE_UI = 'Segoe UI'

TAILLE_TITRE_UI = 15
TAILLE_SOUS_TITRE_UI = 10
TAILLE_TEXTE_UI = 9
TAILLE_TABLEAU_UI = 9

#: Hauteur de ligne du tableau, en pixels. Le site respire ; une ligne serrée
#: trahirait la charte plus sûrement qu'une couleur approximative.
HAUTEUR_LIGNE = 26

PADDING_BANDEAU = (16, 12)
PADDING_CARTE = 12
ECART = 8


def appliquer(racine):
    u"""Applique la charte IES à une fenêtre et rend le style configuré.

    Args:
        racine: Fenêtre `tkinter.Tk` ou `Toplevel`.

    Returns:
        ttk.Style: Style configuré, pour un réglage complémentaire éventuel.

    Raises:
        ImportError: Si tkinter est indisponible — ce module n'a de sens que
            dans VEScripts.
    """
    try:
        from tkinter import ttk
    except ImportError as erreur:
        raise ImportError(
            u'tkinter indisponible : la charte ne peut être appliquée qu\'à '
            u'une interface réelle (%s)' % erreur)

    style = ttk.Style(racine)
    _forcer_le_theme(style)
    racine.configure(background=design.GRIS_CLAIR)
    for configurer in (_styles_de_fond, _styles_de_texte, _styles_de_bouton,
                       _style_du_tableau):
        configurer(style)
    return style


def _forcer_le_theme(style):
    u"""Bascule sur un thème qui honore les couleurs.

    Args:
        style: `ttk.Style`.

    Returns:
        str: Nom du thème effectivement retenu.
    """
    if THEME_REQUIS in style.theme_names():
        style.theme_use(THEME_REQUIS)
    # Si `clam` manquait — cas non observé mais pas impossible sur une
    # installation minimale — on garde le thème courant : une interface aux
    # couleurs du système reste utilisable, contrairement à une exception.
    return style.theme_use()


def _styles_de_fond(style):
    u"""Cadres : fond de page, cartes blanches, bandeau navy.

    Args:
        style: `ttk.Style`.
    """
    style.configure(STYLE_FOND, background=design.GRIS_CLAIR)
    style.configure(STYLE_CARTE, background=design.BLANC,
                    relief='flat', borderwidth=0)
    style.configure(STYLE_BANDEAU, background=design.NAVY)
    style.configure(STYLE_ETIQUETTE_CADRE, background=design.BLANC,
                    bordercolor=design.GRIS_BORDURE, relief='solid',
                    borderwidth=1)
    style.configure(STYLE_ETIQUETTE_CADRE + '.Label',
                    background=design.BLANC, foreground=design.NAVY,
                    font=(POLICE_UI, TAILLE_TEXTE_UI, 'bold'))


def _styles_de_texte(style):
    u"""Libellés : titre sur bandeau, corps, texte atténué.

    Args:
        style: `ttk.Style`.
    """
    style.configure(STYLE_TITRE, background=design.NAVY,
                    foreground=design.BLANC,
                    font=(POLICE_UI, TAILLE_TITRE_UI, 'bold'))
    style.configure(STYLE_SOUS_TITRE, background=design.NAVY,
                    foreground=design.TEINTE_BLEUE,
                    font=(POLICE_UI, TAILLE_SOUS_TITRE_UI))
    style.configure(STYLE_TEXTE, background=design.BLANC,
                    foreground=design.TEXTE,
                    font=(POLICE_UI, TAILLE_TEXTE_UI))
    style.configure(STYLE_ATTENUE, background=design.BLANC,
                    foreground=design.TEXTE_ATTENUE,
                    font=(POLICE_UI, TAILLE_TEXTE_UI))
    style.configure(STYLE_SECTION, background=design.BLANC,
                    foreground=design.NAVY,
                    font=(POLICE_UI, TAILLE_TEXTE_UI, 'bold'))


def _styles_de_bouton(style):
    u"""Boutons : neutre bordé, et accent bleu pour l'action principale.

    Args:
        style: `ttk.Style`.
    """
    style.configure(STYLE_BOUTON, background=design.BLANC,
                    foreground=design.NAVY, bordercolor=design.GRIS_BORDURE,
                    focuscolor=design.ACCENT, relief='flat', borderwidth=1,
                    padding=(14, 7), font=(POLICE_UI, TAILLE_TEXTE_UI))
    style.map(STYLE_BOUTON,
              background=[('active', design.TEINTE_BLEUE)],
              bordercolor=[('active', design.ACCENT)])

    style.configure(STYLE_BOUTON_ACCENT, background=design.ACCENT,
                    foreground=design.BLANC, bordercolor=design.ACCENT,
                    focuscolor=design.BLANC, relief='flat', borderwidth=0,
                    padding=(14, 7),
                    font=(POLICE_UI, TAILLE_TEXTE_UI, 'bold'))
    style.map(STYLE_BOUTON_ACCENT,
              background=[('active', design.ACCENT_VIF),
                          ('disabled', design.GRIS_NEUTRE)])


def _style_du_tableau(style):
    u"""Tableau : en-tête en teinte bleue, lignes aérées, filets fins.

    Args:
        style: `ttk.Style`.
    """
    style.configure(STYLE_ARBRE, background=design.BLANC,
                    fieldbackground=design.BLANC, foreground=design.TEXTE,
                    bordercolor=design.GRIS_BORDURE, borderwidth=0,
                    rowheight=HAUTEUR_LIGNE,
                    font=(POLICE_UI, TAILLE_TABLEAU_UI))
    style.configure(STYLE_ARBRE + '.Heading', background=design.TEINTE_BLEUE,
                    foreground=design.NAVY, relief='flat',
                    borderwidth=0, padding=(8, 8),
                    font=(POLICE_UI, TAILLE_TABLEAU_UI, 'bold'))
    style.map(STYLE_ARBRE + '.Heading',
              background=[('active', design.TEINTE_BLEUE)])
    # La selection reprend l'accent de la marque plutot que le bleu systeme.
    style.map(STYLE_ARBRE,
              background=[('selected', design.ACCENT)],
              foreground=[('selected', design.BLANC)])


def libelle_de_verdict(couleur, texte):
    u"""Compose un libellé de verdict : symbole PUIS texte.

    Le symbole d'abord, toujours : c'est lui qui reste lisible quand la
    couleur ne s'affiche pas.

    Args:
        couleur: `'vert'`, `'rouge'` ou `'gris'`.
        texte: Libellé du verdict.

    Returns:
        str: Libellé composé.
    """
    return u'%s  %s' % (design.symbole(couleur), texte)


def couleurs_de_ligne(couleur):
    u"""Fond et texte d'une ligne de tableau, pour un verdict donné.

    Args:
        couleur: `'vert'`, `'rouge'` ou `'gris'`.

    Returns:
        tuple[str, str]: `(fond, texte)`.
    """
    return design.fond_verdict(couleur), design.TEXTE
