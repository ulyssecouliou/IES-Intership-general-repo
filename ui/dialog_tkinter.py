# -*- coding: utf-8 -*-
"""Dialogue Tkinter -- le « navigateur » SIA 4010, lancé depuis le
*Python Scripts navigator* de VE (docs/ADR-001-architecture-MSP.md, décision
D2, ACCEPTÉE 2026-07-30).

--------------------------------------------------------------------------
STATUT D'EXÉCUTION -- corrigé en cours de session (l'hypothèse initiale
« tkinter indisponible ici » était FAUSSE sur cette machine) :
--------------------------------------------------------------------------
`tkinter` est en réalité disponible et fonctionnel sur ce poste de
développement (session graphique Windows). `ui/tests/test_dialog_tkinter.py`
construit donc RÉELLEMENT `NavigateurTest1` (fenêtre, `ttk.Treeview` complet,
liaison de sélection, panneau de détail) à partir de la fixture de
développement, et a permis de trouver + corriger un bug réel : les `iid` de
`ttk.Treeview` étaient dérivés uniquement de (grandeur, cas, période), donc
en collision dès qu'il y a plus d'une classe de validation concernée (7
classes pour le Test 1) -- corrigé en les préfixant par la classe
(`_iid_ligne`).

**Ce qui reste `# ⚠ À VÉRIFIER` -- non prouvé même par ces tests** :
1. Le rendu VISUEL réel des couleurs (`tag_configure(background=...)`) :
   dépend du thème `ttk` actif, non observable sans capture d'écran depuis
   ce sandbox. Les tests vérifient que les bons tags sont posés sur les
   bons nœuds (`item(iid, 'tags')`), pas leur rendu pixel.
2. Le comportement à l'intérieur du processus VE lui-même (thread
   principal partagé avec VE, cohabitation avec sa propre boucle
   d'événements) -- jamais testé hors VE.
3. Exécution intermittente flaky observée sur CETTE machine précise
   (Python installé via le Microsoft Store, système de fichiers
   virtualisé) : `tkinter.Tk()` échoue parfois avec `TclError: Can't find
   a usable init.tcl` alors que les fichiers existent bel et bien --
   diagnostiqué comme un artefact de cette distribution Python précise,
   PAS un défaut de ce module (cf. docstring de
   `ui/tests/test_dialog_tkinter.py`). Sans lien avec VE (dont
   l'environnement Python est totalement différent).

--------------------------------------------------------------------------
PRINCIPE (CLAUDE.md, .claude/agents/ui-engineer.md) : ce module ne fait QUE
de l'affichage. Il n'importe QUE `ui/verdict_view.py` (Python pur, testé,
cf. `ui/tests/test_verdict_view.py`) pour transformer le JSON du moteur en
lignes déjà classées/colorées/citées ; il ne recalcule et n'invente rien
lui-même. Navigation demandée : Classe de validation -> Tests requis
(matrice tableau 63) -> grandeurs -> delta vs référence + tolérance +
verdict, avec drill-down horaire si pertinent (ici : drill-down jusqu'à la
période -- mois/annuel/extrême/pointe -- pas jusqu'à l'heure : aucune série
horaire n'est transmise par `engine/test1_engine.py::evaluer_test1()`,
seulement des agrégats mensuels/annuels ; le drill-down horaire réel n'est
pas dans le périmètre MSP du Test 1, cf. ADR-001 §5 pt 3 sur le mode
Handeingabe -- pas de remplissage horaire).

--------------------------------------------------------------------------
LIMITE DOCUMENTÉE DE LA NAVIGATION « CLASSE -> TESTS » :
`ui/verdict_view.py::construire_lignes_classes` ne peut lister que les
classes déjà retournées par `evaluer_test1()['classes_concernees']`, car
aucun moteur ne produit encore la table 63 complète (tous tests × toutes
classes) -- seul le Test 1 existe à ce jour. Ce dialogue affiche donc, pour
l'instant, une arborescence à un seul niveau de test (« Test 1 ») sous
chaque classe concernée. Quand d'autres tests (`test2_engine.py`, etc.)
existeront, ce module devra être étendu pour agréger plusieurs JSON de
moteur -- pas anticipé ici pour ne pas inventer une structure multi-tests
non encore produite (cf. rapport de fin de tâche, question ouverte).
"""

import os

from ui import design_ies as design
from ui import verdict_view as vue

# `tkinter` s'est révélé disponible sur cette machine de développement (cf.
# note de statut d'exécution ci-dessus) -- ce garde `try/except` reste
# nécessaire pour les postes où il ne l'est pas (ex. certaines installations
# VE embarquées, cf. réserve n° 3 de l'ADR-001 §2 sur la version Python).
try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
except ImportError:  # pragma: no cover -- attendu hors VE / hors env graphique
    tk = None
    ttk = None
    messagebox = None
    filedialog = None


# Couleurs et symboles : lus dans `ui/design_ies.py`, qui les tient de la
# feuille de style publique d IES. Une seule source pour le navigateur et les
# rapports -- sinon les deux divergent au premier ajustement.
#
# ⚠ À VÉRIFIER -- non exécuté : le rendu effectif de `tag_configure` dépend du
# thème ttk actif sur le poste VE. Plusieurs thèmes Windows ('vista',
# 'xpnative') ignorent `background` sur les lignes de Treeview. C est
# précisément pourquoi le verdict porte AUSSI un symbole et un texte : la
# couleur ne doit jamais être seule à le dire.
COULEUR_FOND_PAR_VERDICT = dict(design.FOND_PAR_VERDICT)

SYMBOLE_PAR_VERDICT = dict(design.SYMBOLE_PAR_VERDICT)


class NavigateurSIA4010(object):
    """Fenêtre principale du navigateur SIA 4010 -- un ou plusieurs tests.

    Prend une LISTE de vues, chacune produite par `ui/verdict_view.py`
    (`construire_vue_test1`, `construire_vue_test7`, ...). Toutes respectent
    le même contrat `{test_id, verdict_global, classes, lignes}`, ce qui
    permet d'afficher n'importe quelle combinaison de tests dans un seul
    arbre `Classe -> Test -> Grandeur -> Cas -> Période`.

    Une classe de validation apparaît une seule fois, avec sous elle TOUS les
    tests qu'elle exige et qui sont présents dans les vues fournies. La
    couleur d'un nœud de classe est le pire verdict de ses tests : jamais un
    vert si un test requis n'est pas concluant.

    Construction et remplissage de l'arborescence testés réellement (cf.
    `ui/tests/test_dialog_tkinter.py`) ; `.lancer()` (boucle d'événements
    bloquante) et l'exécution depuis VEScripts elle-même restent
    `# ⚠ À VÉRIFIER` -- non exécutées ici.

        from ui.dialog_tkinter import NavigateurSIA4010
        from ui import verdict_view as vue
        app = NavigateurSIA4010([vue.construire_vue_test1(r1),
                                 vue.construire_vue_test7(r7)])
        app.lancer()
    """

    def __init__(self, vues):
        if tk is None:
            raise ImportError(
                "tkinter indisponible dans cet environnement -- ce dialogue "
                "doit s'exécuter depuis VEScripts (Python Scripts navigator "
                "de VE), pas en Python autonome sans affichage.")
        if not vues:
            raise ValueError(
                u'aucune vue fournie : le navigateur refuse de afficher une '
                u'fenêtre vide qui pourrait passer pour « rien à signaler ».')
        self._vues = list(vues)
        # Compatibilité ascendante : les appelants historiques (et le PDF /
        # Excel du Test 1) lisent `self._vue`.
        self._vue = self._vues[0]
        self._resultat = None
        self._racine = tk.Tk()
        self._racine.title(u'Navigateur SIA 4010 -- ' + u', '.join(
            str(v.get('test_id') or '?') for v in self._vues))
        self._racine.geometry('1100x650')
        self._construire_widgets()


    # ----------------------------------------------------------------
    # Construction de l'interface
    # ----------------------------------------------------------------

    def _construire_widgets(self):
        # Charte IES appliquee AVANT toute creation de widget : le changement
        # de theme ttk ne se propage pas retroactivement aux widgets deja
        # instancies.
        from ui import theme_ies as charte
        self._charte = charte
        charte.appliquer(self._racine)

        self._construire_bandeau(charte)

        # Corps sur fond gris clair, contenu en cartes blanches : c'est la
        # composition du site, qui divise par l'espace et non par des traits.
        corps = ttk.Frame(self._racine, style=charte.STYLE_FOND,
                          padding=charte.ECART)
        corps.pack(side='top', fill='both', expand=True)

        # Arborescence Classe -> Test -> Grandeur -> Cas -> Période.
        cadre_arbre = ttk.Frame(corps, style=charte.STYLE_CARTE,
                                padding=charte.PADDING_CARTE)
        cadre_arbre.pack(side='top', fill='both', expand=True)

        colonnes = ('valeur', 'reference_ou_plage', 'verdict', 'article')
        self._arbre = ttk.Treeview(cadre_arbre, columns=colonnes,
                                   show='tree headings',
                                   style=charte.STYLE_ARBRE)
        self._arbre.heading('#0', text=u'Classe / Test / Grandeur / Cas / Période')
        self._arbre.heading('valeur', text=u'Valeur candidate')
        self._arbre.heading('reference_ou_plage', text=u'Référence / plage')
        self._arbre.heading('verdict', text=u'Verdict')
        self._arbre.heading('article', text=u'Article de norme')
        self._arbre.column('#0', width=320, stretch=True)
        self._arbre.column('valeur', width=110, anchor='e')
        self._arbre.column('reference_ou_plage', width=180, anchor='e')
        self._arbre.column('verdict', width=110, anchor='center')
        self._arbre.column('article', width=320, stretch=True)
        self._arbre.pack(side='left', fill='both', expand=True)

        defilement = ttk.Scrollbar(cadre_arbre, orient='vertical',
                                    command=self._arbre.yview)
        defilement.pack(side='left', fill='y')
        self._arbre.configure(yscrollcommand=defilement.set)

        self._configurer_tags_couleur()
        self._remplir_arbre()

        cadre_detail = ttk.Frame(corps, style=charte.STYLE_CARTE,
                                 padding=charte.PADDING_CARTE)
        cadre_detail.pack(side='bottom', fill='x', pady=(charte.ECART, 0))
        ttk.Label(cadre_detail, style=charte.STYLE_SECTION,
                  text=u'Détail de la période sélectionnée').pack(anchor='w')
        self._texte_detail = tk.Text(
            cadre_detail, height=6, wrap='word', relief='flat',
            background=design.BLANC, foreground=design.TEXTE,
            font=(charte.POLICE_UI, charte.TAILLE_TEXTE_UI),
            highlightthickness=1, highlightbackground=design.GRIS_BORDURE)
        self._texte_detail.pack(fill='x', pady=(6, 0))
        self._texte_detail.configure(state='disabled')

        self._arbre.bind('<<TreeviewSelect>>', self._afficher_detail_selection)

    def _construire_bandeau(self, charte):
        """Bandeau navy pleine largeur : signature visuelle du site IES.

        Args:
            charte: Module `ui/theme_ies.py`.
        """
        bandeau = ttk.Frame(self._racine, style=charte.STYLE_BANDEAU,
                            padding=charte.PADDING_BANDEAU)
        bandeau.pack(side='top', fill='x')

        titres = ttk.Frame(bandeau, style=charte.STYLE_BANDEAU)
        titres.pack(side='left', anchor='w')
        ttk.Label(titres, style=charte.STYLE_TITRE,
                  text=u'Navigateur de validation SIA 4010').pack(anchor='w')

        # Un verdict par test : agrege, il masquerait lequel echoue.
        for une_vue in self._vues:
            verdict_global = une_vue['verdict_global']
            ttk.Label(
                titres, style=charte.STYLE_SOUS_TITRE,
                text=charte.libelle_de_verdict(
                    verdict_global['couleur'],
                    u'%s — %s' % (une_vue.get('test_id') or u'Test',
                                  verdict_global['texte']))
            ).pack(anchor='w', pady=(2, 0))

        ttk.Label(titres, style=charte.STYLE_SOUS_TITRE, wraplength=620,
                  text=u'Article : '
                       + self._vues[0]['verdict_global']['article']
                  ).pack(anchor='w', pady=(6, 0))

        actions = ttk.Frame(bandeau, style=charte.STYLE_BANDEAU)
        actions.pack(side='right', anchor='e')
        ttk.Button(actions, style=charte.STYLE_BOUTON_ACCENT,
                   text=u'Exporter Excel (SIA officiel)',
                   command=self._exporter_excel).pack(side='left', padx=(0, 6))
        ttk.Button(actions, style=charte.STYLE_BOUTON, text=u'Exporter PDF',
                   command=self._exporter_pdf).pack(side='left')

    def _configurer_tags_couleur(self):
        for couleur, fond in COULEUR_FOND_PAR_VERDICT.items():
            # ⚠ À VÉRIFIER -- non exécuté (cf. note de module sur le thème ttk).
            self._arbre.tag_configure(couleur, background=fond)

    def _remplir_arbre(self):
        """Construit l'arborescence Classe -> Test -> Grandeur -> Cas ->
        Période à partir de `self._vue` (déjà triée/colorée par
        `verdict_view.py`) -- aucune donnée supplémentaire n'est introduite.
        """
        # Table de correspondance iid Treeview -> ligne source, RESET a
        # chaque (re)construction de l'arbre. Necessaire car le meme
        # (grandeur, cas, periode) est repete sous CHAQUE classe concernee
        # (un test n'a qu'un seul verdict, partage par toutes ses classes --
        # cf. `verdict_view.construire_lignes_classes`) : les iids de
        # Treeview doivent donc etre scopes par classe ET par test pour
        # rester uniques dans tout l'arbre (piege reel rencontre et corrige
        # durant le developpement -- cf. `ui/tests/test_dialog_tkinter.py`).
        self._lignes_par_iid = {}

        # Regroupement par classe : une classe apparait UNE fois, avec sous
        # elle tous les tests fournis qui la concernent. L'ordre des classes
        # est alphabetique (1A, 1B, 2A, ... 5) ; celui des tests suit l'ordre
        # dans lequel les vues ont ete passees.
        tests_par_classe = {}
        for une_vue in self._vues:
            for ligne_classe in une_vue['classes']:
                tests_par_classe.setdefault(
                    ligne_classe['classe'], []).append((une_vue, ligne_classe))

        for classe in sorted(tests_par_classe):
            tests = tests_par_classe[classe]
            # Couleur de la classe = pire verdict de SES tests : une classe
            # n'est verte que si tous les tests qu'elle exige le sont.
            couleur_classe = _pire_couleur(lc['couleur'] for _, lc in tests)
            noeud_classe = self._arbre.insert(
                '', 'end',
                text=u'Classe ' + classe,
                values=('', '', SYMBOLE_PAR_VERDICT.get(couleur_classe, u'?'),
                        tests[0][1]['article']),
                tags=(couleur_classe,), open=False)

            for une_vue, ligne_classe in tests:
                test_id = str(une_vue.get('test_id') or 'Test')
                noeud_test = self._arbre.insert(
                    noeud_classe, 'end',
                    text=test_id,
                    values=('', '',
                            SYMBOLE_PAR_VERDICT.get(ligne_classe['couleur'], u'?'),
                            une_vue['verdict_global']['article']),
                    tags=(ligne_classe['couleur'],), open=False)
                self._remplir_test(noeud_test, classe, test_id, une_vue)

    def _remplir_test(self, noeud_test, classe, test_id, une_vue):
        """Remplit un noeud de test : Grandeur -> Cas -> Période.

        L'ordre des grandeurs et des cas est celui deja fixe par
        `verdict_view` -- pour le Test 7, c'est l'ordre des lignes du
        classeur SIA, pas un tri de notre invention.
        """
        lignes_par_grandeur_cas = {}
        ordre_grandeur_cas = []
        for ligne in une_vue['lignes']:
            cle = (ligne['grandeur'], ligne['cas'])
            if cle not in lignes_par_grandeur_cas:
                lignes_par_grandeur_cas[cle] = []
                ordre_grandeur_cas.append(cle)
            lignes_par_grandeur_cas[cle].append(ligne)

        prefixe = 'classe::' + classe + '::test::' + test_id

        for grandeur, cas in ordre_grandeur_cas:
            lignes_periodes = lignes_par_grandeur_cas[(grandeur, cas)]
            # Couleur du noeud "cas" = pire verdict de ses periodes
            # (rouge > gris > vert), sans jamais inventer une agregation
            # que le moteur n'a pas produite lui-meme au niveau cas.
            couleur_cas = _pire_couleur(l['couleur'] for l in lignes_periodes)

            noeud_grandeur_id = prefixe + '::grandeur::' + grandeur
            if self._arbre.exists(noeud_grandeur_id):
                noeud_grandeur = noeud_grandeur_id
            else:
                noeud_grandeur = self._arbre.insert(
                    noeud_test, 'end', iid=noeud_grandeur_id,
                    text=lignes_periodes[0]['grandeur_libelle'],
                    values=('', '', '', ''), open=False)

            noeud_cas = self._arbre.insert(
                noeud_grandeur, 'end',
                text=u'Cas ' + cas if cas else u'(ensemble)',
                values=('', '', SYMBOLE_PAR_VERDICT.get(couleur_cas, u'?'), ''),
                tags=(couleur_cas,), open=False)

            for ligne in lignes_periodes:
                reference_affichee = _resumer_reference(ligne)
                iid_periode = _iid_ligne(classe, ligne, test_id)
                self._arbre.insert(
                    noeud_cas, 'end',
                    text=ligne['periode_libelle'],
                    values=(ligne['valeur_candidate_affichee'],
                            reference_affichee,
                            SYMBOLE_PAR_VERDICT.get(ligne['couleur'], u'?') +
                            u' ' + ligne['texte_verdict'],
                            ligne['article']),
                    tags=(ligne['couleur'],),
                    iid=iid_periode)
                self._lignes_par_iid[iid_periode] = ligne

    # ----------------------------------------------------------------
    # Interactions
    # ----------------------------------------------------------------

    def _afficher_detail_selection(self, evenement):
        selection = self._arbre.selection()
        if not selection:
            return
        iid = selection[0]
        ligne = self._lignes_par_iid.get(iid)
        self._texte_detail.configure(state='normal')
        self._texte_detail.delete('1.0', 'end')
        if ligne is None:
            self._texte_detail.insert('end', u'(Nœud de regroupement -- sélectionner une période.)')
        else:
            self._texte_detail.insert('end', _texte_detail_ligne(ligne))
        self._texte_detail.configure(state='disabled')

    def _exporter_excel(self):
        # ⚠ À VÉRIFIER -- non exécuté. Délégué à `ui/export_excel_com.py`,
        # qui exige explicitement un classeur source (copie, jamais
        # l'original) et une carte de cellules Handeingabe -- non fournie
        # par défaut (cf. docstring de ce module et d'`export_excel_com.py`).
        if filedialog is None:
            return
        chemin_source = filedialog.askopenfilename(
            title=u'Copie du classeur SIA officiel (Handeingabe)',
            filetypes=[('Classeur Excel', '*.xlsx;*.xlsm')])
        if not chemin_source:
            return
        # Chaque test SIA a SON classeur d'évaluation : on ne remplit donc
        # qu'un test à la fois depuis ce bouton, celui affiché en premier.
        # Un bouton unique remplissant plusieurs classeurs demanderait autant
        # de sélections de fichier -- laissé à `remplir_classeurs_sia`, que
        # le script appelant peut piloter sans dialogue.
        try:
            from ui import export_excel_com
            rapport = export_excel_com.remplir_classeur_sia_detaille(
                chemin_source, self._vues[0])
            message = u'Classeur rempli : %s\n%d cellule(s) écrite(s).' % (
                rapport['chemin_sortie'], len(rapport['cellules_ecrites']))
            ignorees = rapport['cellules_ignorees_valeur_absente']
            if ignorees:
                # Ne jamais annoncer un succès sec quand des cases restent
                # vides : elles seraient decouvertes par le SIA, pas par nous.
                message += (u'\n\n⚠ %d cellule(s) laissée(s) VIDE(S), faute de '
                            u'valeur candidate :\n%s' % (
                                len(ignorees),
                                u'\n'.join(u'  %s → %s' % (c, a)
                                           for c, a in ignorees[:10])))
                if len(ignorees) > 10:
                    message += u'\n  … et %d autre(s).' % (len(ignorees) - 10)
            messagebox.showinfo(u'Export Excel', message)
        except Exception as erreur:  # pragma: no cover -- non exécuté ici
            messagebox.showerror(u'Export Excel', str(erreur))

    def _exporter_pdf(self):
        # ⚠ À VÉRIFIER -- non exécuté.
        if filedialog is None:
            return
        chemin_pdf = filedialog.asksaveasfilename(
            title=u'Enregistrer le rapport PDF', defaultextension='.pdf',
            filetypes=[('PDF', '*.pdf')])
        if not chemin_pdf:
            return
        # Le PDF couvre TOUS les tests affichés : sa page de tête est la
        # synthèse par classe, qui est ce que le client lit en premier.
        try:
            from ui import export_pdf_reportlab
            export_pdf_reportlab.generer_pdf_rapport_multi(
                self._vues, chemin_pdf)
            messagebox.showinfo(
                u'Export PDF',
                u'Rapport généré : %s\n%d test(s) couvert(s) : %s' % (
                    chemin_pdf, len(self._vues),
                    u', '.join(str(v.get('test_id') or '?') for v in self._vues)))
        except Exception as erreur:  # pragma: no cover -- non exécuté ici
            messagebox.showerror(u'Export PDF', str(erreur))

    def lancer(self):
        """Boucle d'événements Tkinter -- bloque jusqu'à fermeture."""
        self._racine.mainloop()


# --------------------------------------------------------------------------
# Fonctions utilitaires de rendu (pures -- testables même si le reste du
# module ne l'est pas, car elles n'importent aucun objet `tkinter`).
# --------------------------------------------------------------------------

_ORDRE_COULEUR_GRAVITE = {'vert': 0, 'gris': 1, 'rouge': 2}


class NavigateurTest1(NavigateurSIA4010):
    """Navigateur restreint au Test 1 -- conservé tel quel pour l'existant.

    `resultat_test1_json` : le dict retourné par
    `engine/test1_engine.py::evaluer_test1(reference, candidat)`.
    """

    def __init__(self, resultat_test1_json):
        NavigateurSIA4010.__init__(
            self, [vue.construire_vue_test1(resultat_test1_json)])
        self._resultat = resultat_test1_json


def _pire_couleur(couleurs):
    """Pire couleur d'un ensemble (rouge > gris > vert), pour agréger
    visuellement un nœud de regroupement (ex. "cas") sans jamais afficher un
    vert si au moins une période enfant n'est pas verte."""
    couleurs = list(couleurs)
    if not couleurs:
        return 'gris'
    return max(couleurs, key=lambda c: _ORDRE_COULEUR_GRAVITE.get(c, 1))


def _iid_ligne(classe, ligne, test_id=''):
    """Identifiant Treeview stable pour une ligne de période -- dérivé des
    clés déjà présentes (grandeur/cas/période), jamais d'un compteur global
    qui casserait au moindre réordonnancement.

    Doit être préfixé par la CLASSE : le même (grandeur, cas, période)
    apparaît sous chaque classe concernée (`verdict_view.
    construire_lignes_classes` -- un seul verdict de Test 1, partagé par
    toutes ses classes), et `ttk.Treeview` exige des `iid` uniques dans TOUT
    l'arbre, pas seulement par sous-arbre. Sans ce préfixe, la construction
    de l'arbre échoue dès la deuxième classe (`TclError: Item ... already
    exists`) -- bug réel rencontré et corrigé pendant le développement, cf.
    `ui/tests/test_dialog_tkinter.py::test_construire_widgets_sans_exception_avec_plusieurs_classes`.

    Le `test_id` entre aussi dans la clé depuis l'ajout du Test 7 : les
    classes 4A et 4B exigent à la fois le Test 1 et le Test 7, et rien
    n'interdit à deux tests différents de porter un même triplet
    (grandeur, cas, période). Défaut vide pour rester compatible avec les
    appelants antérieurs.
    """
    return ('classe::' + classe + '::test::' + str(test_id) + '::periode::' +
            ligne['grandeur'] + '::' + ligne['cas'] + '::' + ligne['periode'])


def _resumer_reference(ligne):
    """Résumé texte de la référence/plage, sans recalcul : lit uniquement
    les clés déjà produites par le moteur dans `ligne['detail']`."""
    # Le Test 7 fournit deja son resume de bande (`moyenne (bas … haut) unite`)
    # depuis `verdict_view.construire_lignes_test7` : on le reprend tel quel
    # plutot que de le reconstruire ici a partir des bornes.
    if ligne.get('reference_affichee') is not None:
        return ligne['reference_affichee']

    detail = ligne.get('detail') or {}
    if ligne['type_controle'] == 'critere_pass_fail':
        plage_min = detail.get('plage_min')
        plage_max = detail.get('plage_max')
        if plage_min is None or plage_max is None:
            return u'—'
        return u'[{0} ; {1}]'.format(
            vue.formater_nombre(plage_min), vue.formater_nombre(plage_max))
    # Informatif : plusieurs programmes de reference -- on affiche la
    # moyenne si elle est presente parmi les comparaisons, sinon le nombre
    # de programmes compares (jamais une valeur choisie arbitrairement).
    comparaisons = detail.get('comparaisons') or {}
    if not comparaisons:
        return u'—'
    return u'{0} programme(s) de réf. -- voir détail'.format(len(comparaisons))


def _texte_detail_ligne(ligne):
    detail = ligne.get('detail') or {}
    morceaux = [
        u'Grandeur : ' + ligne['grandeur_libelle'],
        u'Cas : ' + ligne['cas'] + u'   Période : ' + ligne['periode_libelle'],
        u'Valeur candidate : ' + ligne['valeur_candidate_affichee'],
        u'Verdict : ' + ligne['texte_verdict'],
        u'Article : ' + ligne['article'],
        u'Source de la référence : ' + ligne['source_valeur_reference'],
    ]
    if ligne['type_controle'] == 'critere_pass_fail':
        morceaux.append(u'Moyenne des programmes de référence : ' +
                         vue.formater_nombre(detail.get('moyenne_programmes')))
        morceaux.append(u'Plage de dispersion (Streubereich) : [{0} ; {1}]'.format(
            vue.formater_nombre(detail.get('plage_min')),
            vue.formater_nombre(detail.get('plage_max'))))
        if detail.get('marge_min') is not None:
            morceaux.append(u'Marge par rapport aux bornes : min {0} / max {1}'.format(
                vue.formater_nombre(detail.get('marge_min')),
                vue.formater_nombre(detail.get('marge_max'))))
        if detail.get('coherence_reference') is False:
            morceaux.append(
                u'⚠ Incohérence détectée entre la plage recalculée par le '
                u'moteur et celle déjà stockée dans test-1.ref.json -- signaler '
                u'à qa-auditor avant de considérer ce verdict fiable.')
        if detail.get('motif'):
            morceaux.append(u'Motif : ' + detail['motif'])
    else:
        comparaisons = detail.get('comparaisons') or {}
        for nom_programme, comparaison in sorted(comparaisons.items()):
            morceaux.append(u'  -- {0} : référence {1}, delta {2} ({3} %)'.format(
                nom_programme,
                vue.formater_nombre(comparaison.get('reference')),
                vue.formater_nombre(comparaison.get('delta_absolu')),
                vue.formater_nombre(comparaison.get('delta_relatif_pct'))))
    return u'\n'.join(morceaux)


# --------------------------------------------------------------------------
# Point d'entrée attendu depuis le Python Scripts navigator de VE.
# --------------------------------------------------------------------------

def lancer_depuis_ve(chemin_reference=None, chemin_candidat_fixture=None):
    """Fonction d'appel prévue pour un script enregistré dans le *Python
    Scripts navigator* (docs/ADR-001-architecture-MSP.md §2/§3).

    # ⚠ À VÉRIFIER -- NON EXÉCUTÉ. Cette fonction suppose que l'appelant VE a
    déjà produit le candidat réel via
    `ve_adapter/test1_adapter.py::extraire_candidat_test1()` -- ou, en mode
    développement/démonstration sans VE, charge la fixture explicitement non
    qualifiée (`charger_fixture_test1()`, cf. son avertissement
    `_provenance`). Ne lance JAMAIS silencieusement la fixture comme si
    c'était un résultat réel : le bandeau `_provenance` doit être affiché
    tel quel si présent (non fait ici faute de maquette validée -- laissé à
    une prochaine itération, cf. rapport de fin de tâche).
    """
    from engine import test1_engine as moteur
    reference = moteur.charger_reference(chemin_reference)

    if chemin_candidat_fixture is not None:
        import json
        with open(chemin_candidat_fixture, encoding='utf-8') as flux:
            candidat = json.load(flux)
    else:
        candidat = None  # aucune simulation encore lancee -> tout gris.

    resultat = moteur.evaluer_test1(reference, candidat)
    app = NavigateurTest1(resultat)
    app.lancer()


def construire_vues_disponibles(candidat_test1=None, candidat_test7=None,
                                 candidats_par_test=None):
    """Construit les vues de TOUS les tests dont la référence est figée.

    Un test dont le référentiel est absent est SAUTÉ, pas remplacé par un
    substitut : mieux vaut une classe absente de l'arbre qu'une classe
    affichée sur des données inventées.

    `candidats_par_test` : `{numero: candidat}` pour les tests à bandes (2, 3).

    Retourne `(vues, avertissements)`.
    """
    vues, avertissements = [], []

    try:
        from engine import test1_engine as moteur1
        reference1 = moteur1.charger_reference()
        vues.append(vue.construire_vue_test1(
            moteur1.evaluer_test1(reference1, candidat_test1)))
    except Exception as erreur:  # référentiel absent ou illisible
        avertissements.append(u'Test 1 non chargé : %s' % erreur)

    # Tests 2 a 6 : meme moteur, leurs references partagent une forme
    # « grandeur -> cas ». Un test dont la reference manque est SAUTE.
    for numero in (2, 3, 4, 5, 6):
        try:
            from engine import sia_bandes_engine as moteur_bandes
            reference = moteur_bandes.charger_reference(numero)
            candidat = (candidats_par_test or {}).get(numero)
            vues.append(vue.construire_vue_bandes(
                moteur_bandes.evaluer(reference, candidat)))
        except Exception as erreur:
            avertissements.append(u'Test %d non chargé : %s' % (numero, erreur))

    try:
        from engine import test7_engine as moteur7
        reference7 = moteur7.charger_reference()
        vues.append(vue.construire_vue_test7(
            moteur7.evaluer_test7(reference7, candidat_test7)))
    except Exception as erreur:
        avertissements.append(u'Test 7 non chargé : %s' % erreur)

    # Ordre d'affichage : par numéro de test, pas par ordre de chargement.
    vues.sort(key=lambda v: _rang_test(v.get('numero_test')))
    return vues, avertissements


def _rang_test(numero):
    """Rang de tri d'un numéro de test, pour un ordre d'affichage stable.

    Args:
        numero: Numéro déclaré par une vue, ex. « 2 » ou `None`.

    Returns:
        tuple: Clé de tri ; les vues sans numéro passent en fin.
    """
    if numero is None:
        return (1, u'')
    try:
        return (0, u'%03d' % int(numero))
    except (TypeError, ValueError):
        return (0, u'%s' % numero)


def lancer_navigateur(candidat_test1=None, candidat_test7=None):
    """Point d'entrée du navigateur complet, depuis le Python Scripts
    navigator de VE.

    # ⚠ À VÉRIFIER -- NON EXÉCUTÉ hors VE. Les candidats sont produits par
    `ve_adapter/test1_adapter.py` et `ve_adapter/test7_adapter.py`. Passer
    `None` affiche l'état « avant première simulation » : tout gris, aucun
    verdict -- jamais un faux vert par donnée manquante.

        from ui.dialog_tkinter import lancer_navigateur
        lancer_navigateur(candidat_test1=c1, candidat_test7=c7)
    """
    vues, avertissements = construire_vues_disponibles(
        candidat_test1, candidat_test7)
    for avertissement in avertissements:
        print(u'⚠ ' + avertissement)
    if not vues:
        raise RuntimeError(
            u'aucun test chargeable : %s' % u' | '.join(avertissements))
    NavigateurSIA4010(vues).lancer()


if __name__ == '__main__':  # pragma: no cover -- usage manuel hors VE, non teste
    # ⚠ À VÉRIFIER -- non exécuté. Permet un essai manuel avec la fixture de
    # développement si jamais un environnement graphique est disponible.
    _ICI = os.path.dirname(os.path.abspath(__file__))
    _RACINE = os.path.dirname(_ICI)
    lancer_depuis_ve(chemin_candidat_fixture=os.path.join(
        _RACINE, 've_adapter', 'fixtures', 'test1_candidat.exemple.json'))
