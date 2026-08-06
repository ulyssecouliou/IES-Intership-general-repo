# -*- coding: utf-8 -*-
"""Jetons de design IES -- source unique pour le navigateur et les rapports.

PROVENANCE. Les couleurs ne sont pas choisies : elles sont RELEVÉES sur la
feuille de style publique d'IES, `https://www.iesve.com/assets/css/styles.css`
(692 Ko, lue le 2026-08-06), en retenant les valeurs les plus fréquentes et
celles portées par une variable CSS nommée.

    --ha-accent      #0f54e8      26 occurrences
    --lightblue      #00abde      variable nommée
    --lightblue-fade #e8f1fb      variable nommée
    --light-grey     #f5f7f9      variable nommée
    navy             #1a2b4b      13 occurrences
    bleu vif         #4162fd      31 occurrences
    texte            #384656      7 occurrences
    vert             #11bb94      13 occurrences
    rouge            #de3f3f       5 occurrences

TYPOGRAPHIE — réserve à connaître. Le site compose en **Camphor Pro**, une
police commerciale que nous n'avons pas le droit d'embarquer dans un PDF sans
licence. Les rapports utilisent donc **Helvetica**, présente d'origine dans
ReportLab et la plus proche des sans-serif géométriques. Si IES dispose d'une
licence Camphor Pro pour la diffusion de documents, il suffira de changer
`POLICE_TITRE` et `POLICE_TEXTE` ici : rien d'autre n'est à toucher.

ACCESSIBILITÉ. Un verdict n'est JAMAIS porté par la seule couleur. Chaque
statut a aussi son symbole (`SYMBOLE_PAR_VERDICT`) et son texte. C'est une
exigence de `CLAUDE.md`, et la seule façon de rester lisible sur un thème ttk
qui ignore `background`, ou pour un lecteur daltonien.
"""

# ---------------------------------------------------------------------------
# Palette de marque
# ---------------------------------------------------------------------------

NAVY = '#1a2b4b'          #: Bandeaux, titres, en-têtes de tableau.
NAVY_PROFOND = '#193054'  #: Variante plus sombre, filets et pieds de page.
ACCENT = '#0f54e8'        #: --ha-accent : liens, mises en évidence.
ACCENT_VIF = '#4162fd'    #: Accent secondaire.
BLEU_CLAIR = '#00abde'    #: --lightblue.
TEINTE_BLEUE = '#e8f1fb'  #: --lightblue-fade : fond d'en-tête de tableau.
GRIS_CLAIR = '#f5f7f9'    #: --light-grey : zébrure des lignes.
GRIS_BORDURE = '#dce0eb'  #: Filets de tableau, discrets.
TEXTE = '#384656'         #: Corps de texte.
TEXTE_ATTENUE = '#6b7a8f'  #: Légendes, notes de bas de tableau.
BLANC = '#ffffff'

VERT = '#11bb94'          #: Conforme.
ROUGE = '#de3f3f'         #: Non conforme.
ORANGE = '#ff973f'        #: Réserve, attention.
GRIS_NEUTRE = '#8b98aa'   #: Non évalué.

# ---------------------------------------------------------------------------
# Sémantique des verdicts
# ---------------------------------------------------------------------------

#: Fond des lignes, assez pâle pour rester lisible sous du texte foncé.
FOND_PAR_VERDICT = {
    'vert': '#e6f7f1',
    'rouge': '#fdeaea',
    'gris': GRIS_CLAIR,
}

#: Couleur de trait, pour les filets et les pastilles.
TRAIT_PAR_VERDICT = {
    'vert': VERT,
    'rouge': ROUGE,
    'gris': GRIS_NEUTRE,
}

#: Redondance délibérée avec la couleur -- jamais d'information par la seule
#: couleur. Repris tel quel par le navigateur et par le PDF.
SYMBOLE_PAR_VERDICT = {
    'vert': u'✔',   # ✔
    'rouge': u'✘',  # ✘
    'gris': u'—',   # —
}

#: Variante ASCII, pour la console de VEScripts qui n'est pas en UTF-8.
SYMBOLE_ASCII_PAR_VERDICT = {
    'vert': 'OK',
    'rouge': 'NON',
    'gris': '--',
}

# ---------------------------------------------------------------------------
# Typographie
# ---------------------------------------------------------------------------

#: Voir la réserve en tête de module : Camphor Pro n'est pas embarquable.
POLICE_TITRE = 'Helvetica-Bold'
POLICE_TEXTE = 'Helvetica'
POLICE_TEXTE_GRAS = 'Helvetica-Bold'

TAILLE_TITRE = 20
TAILLE_SOUS_TITRE = 13
TAILLE_SECTION = 11
TAILLE_TEXTE = 9
TAILLE_TABLEAU = 7.5
TAILLE_NOTE = 7

#: Interlignage, en multiple de la taille de police.
INTERLIGNE = 1.35

# ---------------------------------------------------------------------------
# Mise en page
# ---------------------------------------------------------------------------

MARGE_CM = 1.6
ESPACE_SECTION_CM = 0.55
ESPACE_PARAGRAPHE_CM = 0.25

#: Épaisseur des filets de tableau, en points. Fin : le site divise par
#: l'espace, pas par des traits épais.
FILET_PT = 0.4
FILET_ENTETE_PT = 0.8


def fond_verdict(couleur):
    """Fond associé à un verdict.

    Args:
        couleur: `'vert'`, `'rouge'` ou `'gris'`.

    Returns:
        str: Code hexadécimal ; le gris neutre si la couleur est inconnue,
        jamais du vert -- une couleur inattendue ne doit pas se lire comme un
        succès.
    """
    return FOND_PAR_VERDICT.get(couleur, GRIS_CLAIR)


def trait_verdict(couleur):
    """Couleur de trait associée à un verdict.

    Args:
        couleur: `'vert'`, `'rouge'` ou `'gris'`.

    Returns:
        str: Code hexadécimal ; le gris neutre par défaut.
    """
    return TRAIT_PAR_VERDICT.get(couleur, GRIS_NEUTRE)


def symbole(couleur, ascii_seulement=False):
    """Symbole associé à un verdict.

    Args:
        couleur: `'vert'`, `'rouge'` ou `'gris'`.
        ascii_seulement: Vrai pour la console de VEScripts.

    Returns:
        str: Symbole, `'?'` si la couleur est inconnue.
    """
    table = SYMBOLE_ASCII_PAR_VERDICT if ascii_seulement else SYMBOLE_PAR_VERDICT
    return table.get(couleur, '?')
