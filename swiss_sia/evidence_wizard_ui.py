# -*- coding: utf-8 -*-
"""Interface VEScripts de collecte des preuves SIA 380/2.

Ne fait QUE de l affichage et de la saisie. Toute la logique — validation,
refus d acceptation, ecriture — vit dans `swiss_sia/evidence_wizard.py`, en
Python pur et teste. Ce module ne decide de rien.

CONTRAINTES D EXECUTION, tenues explicitement :
    - Python 3.12 embarque dans IESVE ;
    - ecran de taille limitee : fenetre 980x680, redimensionnable, et TOUT le
      formulaire est dans une zone defilante ;
    - aucun droit administrateur : rien n est ecrit hors du projet VE et du
      dossier de preuves ;
    - AUCUNE mutation VE : le modele est lu, jamais modifie ;
    - fail-closed : le statut `accepted` est RECALCULE, jamais repris de la
      saisie.

CE QUE L INTERFACE NE FAIT PAS. Elle ne prononce ni conformite SIA 380/2 ni
validation SIA 4010, et ne prend aucune decision a la place du reviseur. Un
champ vide reste vide : il n est jamais comble par une valeur par defaut.
"""

from __future__ import annotations

import os
from datetime import datetime
from typing import Any, Dict, Optional

from swiss_sia import evidence_wizard as noyau

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except ImportError:  # pragma: no cover -- hors environnement graphique
    tk = None
    ttk = None
    messagebox = None

#: Couleurs de marque IES. Importees si disponibles ; sinon des valeurs
#: neutres, pour que l assistant reste utilisable meme si `ui/` manque.
try:
    from ui import design as _design
    NAVY = _design.NAVY
    ACCENT = _design.ACCENT
    GRIS_CLAIR = _design.LIGHT_GREY
    TEINTE_BLEUE = _design.BLUE_TINT
    GRIS_BORDURE = _design.BORDER_GREY
    TEXTE = _design.TEXT
    TEXTE_ATTENUE = _design.TEXT_MUTED
    BLANC = _design.WHITE
    ROUGE = _design.RED
    ORANGE = _design.AMBER
    VERT = _design.GREEN
except ImportError:  # pragma: no cover -- paquet ui absent
    NAVY, ACCENT, GRIS_CLAIR = '#1a2b4b', '#0f54e8', '#f5f7f9'
    TEINTE_BLEUE, GRIS_BORDURE = '#e8f1fb', '#dce0eb'
    TEXTE, TEXTE_ATTENUE, BLANC = '#384656', '#6b7a8f', '#ffffff'
    ROUGE, ORANGE, VERT = '#de3f3f', '#ff973f', '#11bb94'

POLICE = 'Segoe UI'

#: Fenetre volontairement modeste : l assistant doit tenir sur un portable.
LARGEUR = 980
HAUTEUR = 680

#: Couleur associee a chaque categorie de constat.
COULEUR_PAR_CATEGORIE = {
    noyau.DEFAUT_MODELE: ROUGE,
    noyau.DONNEE_CLIENT_MANQUANTE: ORANGE,
    noyau.SORTIE_NON_ACTIVEE: ORANGE,
    noyau.LIMITE_VESCRIPTS: TEXTE_ATTENUE,
    noyau.PREUVE_MANQUANTE: ORANGE,
    noyau.NON_APPLICABLE: TEXTE_ATTENUE,
    noyau.NON_VERIFIABLE: TEXTE_ATTENUE,
    noyau.PASS_TECHNIQUE: VERT,
    noyau.VERDICT_SIA_IMPOSSIBLE: ROUGE,
}


class AssistantIndisponible(RuntimeError):
    """Levee quand l assistant ne peut pas s ouvrir."""


class AssistantDePreuves(object):
    """Fenetre de saisie des preuves SIA 380/2.

    Attributes:
        detecte: Faits releves dans VE, affiches mais jamais recopies dans
            les reponses.
        chemin_csv: CSV de preuves a ecrire.
        dossier_audit: Dossier du JSON d audit.
    """

    def __init__(self, detecte: Optional[Dict[str, Any]] = None,
                 chemin_csv: str = '', dossier_audit: str = '') -> None:
        if tk is None:
            raise AssistantIndisponible(
                "tkinter indisponible : cet assistant doit s executer depuis "
                "le Python Scripts navigator de VE.")
        if not chemin_csv or not dossier_audit:
            raise AssistantIndisponible(
                "chemin du CSV de preuves et dossier d audit exiges : "
                "l assistant refuse d ecrire a un emplacement devine.")

        self.detecte = dict(detecte or {})
        self.chemin_csv = chemin_csv
        self.dossier_audit = dossier_audit
        self._widgets: Dict[str, Any] = {}
        self._resultat: Optional[Dict[str, Any]] = None

        self._racine = tk.Tk()
        self._racine.title('IES — Preuves SIA 380/2')
        self._racine.geometry('%dx%d' % (LARGEUR, HAUTEUR))
        self._racine.minsize(760, 520)
        self._appliquer_charte()
        self._construire()

    # -- Presentation ------------------------------------------------------

    def _appliquer_charte(self) -> None:
        """Applique les couleurs IES.

        Le theme `clam` est le seul qui honore `background` sous Windows : les
        autres delegent au systeme et ignorent la charte.
        """
        style = ttk.Style(self._racine)
        if 'clam' in style.theme_names():
            style.theme_use('clam')
        self._racine.configure(background=GRIS_CLAIR)
        style.configure('W.TFrame', background=GRIS_CLAIR)
        style.configure('WCarte.TFrame', background=BLANC)
        style.configure('WBandeau.TFrame', background=NAVY)
        style.configure('WTitre.TLabel', background=NAVY, foreground=BLANC,
                        font=(POLICE, 14, 'bold'))
        style.configure('WSous.TLabel', background=NAVY,
                        foreground=TEINTE_BLEUE, font=(POLICE, 9))
        style.configure('W.TLabel', background=BLANC, foreground=TEXTE,
                        font=(POLICE, 9))
        style.configure('WAide.TLabel', background=BLANC,
                        foreground=TEXTE_ATTENUE, font=(POLICE, 8))
        style.configure('WSection.TLabel', background=BLANC, foreground=NAVY,
                        font=(POLICE, 10, 'bold'))
        style.configure('W.TButton', background=BLANC, foreground=NAVY,
                        bordercolor=GRIS_BORDURE, relief='flat',
                        borderwidth=1, padding=(12, 6), font=(POLICE, 9))
        style.configure('WAccent.TButton', background=ACCENT, foreground=BLANC,
                        relief='flat', borderwidth=0, padding=(12, 6),
                        font=(POLICE, 9, 'bold'))
        style.map('WAccent.TButton',
                  background=[('disabled', TEXTE_ATTENUE)])
        style.configure('W.TCheckbutton', background=BLANC, foreground=TEXTE,
                        font=(POLICE, 9))
        style.configure('W.TEntry', fieldbackground=BLANC)

    def _construire(self) -> None:
        """Monte le bandeau, la zone defilante et la barre d actions."""
        self._construire_bandeau()

        corps = ttk.Frame(self._racine, style='W.TFrame', padding=8)
        corps.pack(side='top', fill='both', expand=True)

        # ZONE DEFILANTE. Sans elle, les 19 champs debordent d un portable et
        # les derniers — dont la confirmation — deviennent inatteignables.
        toile = tk.Canvas(corps, background=BLANC, highlightthickness=1,
                          highlightbackground=GRIS_BORDURE)
        ascenseur = ttk.Scrollbar(corps, orient='vertical',
                                  command=toile.yview)
        self._interieur = ttk.Frame(toile, style='WCarte.TFrame', padding=12)

        self._interieur.bind(
            '<Configure>',
            lambda _e: toile.configure(scrollregion=toile.bbox('all')))
        fenetre = toile.create_window((0, 0), window=self._interieur,
                                      anchor='nw')
        toile.bind('<Configure>',
                   lambda e: toile.itemconfigure(fenetre, width=e.width))
        toile.configure(yscrollcommand=ascenseur.set)
        toile.pack(side='left', fill='both', expand=True)
        ascenseur.pack(side='right', fill='y')
        toile.bind_all('<MouseWheel>', lambda e: toile.yview_scroll(
            int(-1 * (e.delta / 120)), 'units'))

        self._construire_faits(self._interieur)
        self._construire_champs(self._interieur)
        self._construire_actions(self._racine)

    def _construire_bandeau(self) -> None:
        """Bandeau navy : le projet VE actif, et ce que l assistant n est pas."""
        bandeau = ttk.Frame(self._racine, style='WBandeau.TFrame',
                            padding=(16, 10))
        bandeau.pack(side='top', fill='x')
        ttk.Label(bandeau, style='WTitre.TLabel',
                  text='Preuves SIA 380/2 — collecte').pack(anchor='w')
        ttk.Label(
            bandeau, style='WSous.TLabel',
            text='Projet VE actif : %s'
                 % (self.detecte.get('project_id') or 'NON DETECTE')
        ).pack(anchor='w', pady=(3, 0))
        ttk.Label(
            bandeau, style='WSous.TLabel', wraplength=LARGEUR - 60,
            text=('Cet assistant NE modifie aucune donnee VE, NE prononce '
                  'aucune conformite SIA 380/2 et NE vaut pas validation '
                  'SIA 4010 du logiciel. Il collecte des preuves.')
        ).pack(anchor='w', pady=(6, 0))

    def _construire_faits(self, parent) -> None:
        """Faits releves dans VE, presentes sans etre melanges aux reponses."""
        ttk.Label(parent, style='WSection.TLabel',
                  text='Faits releves dans VE (lecture seule)').pack(
                      anchor='w', pady=(0, 6))
        for cle, fait in sorted(noyau.faits_techniques(self.detecte).items()):
            ligne = ttk.Frame(parent, style='WCarte.TFrame')
            ligne.pack(fill='x', pady=1)
            ttk.Label(ligne, style='W.TLabel', width=26,
                      text=cle).pack(side='left')
            ttk.Label(ligne, style='W.TLabel', width=34,
                      text='%s' % fait['valeur']).pack(side='left')
            ttk.Label(ligne, style='WAide.TLabel', wraplength=420,
                      text='[%s] %s' % (fait['statut'], fait['note'])
                      ).pack(side='left', fill='x', expand=True)
        ttk.Label(
            parent, style='WAide.TLabel', wraplength=LARGEUR - 80,
            text=('Le fichier meteo detecte n est PAS recopie dans le champ '
                  '« Fichier meteo revu » : ce champ porte ce que VOUS '
                  'declarez correct. Une correspondance technique ne vaut pas '
                  'approbation du climat.')
        ).pack(anchor='w', pady=(6, 12))

    def _construire_champs(self, parent) -> None:
        """Monte un widget par champ, pre-rempli seulement si demontre."""
        ttk.Label(parent, style='WSection.TLabel',
                  text='Preuves a completer').pack(anchor='w', pady=(0, 6))
        prefill = noyau.prefill(self.detecte)

        for definition in noyau.CHAMPS:
            bloc = ttk.Frame(parent, style='WCarte.TFrame')
            bloc.pack(fill='x', pady=3)
            etiquette = definition['libelle']
            if definition['obligatoire_pour_accepter']:
                etiquette += '  *'
            ttk.Label(bloc, style='W.TLabel', width=38,
                      text=etiquette).pack(side='left', anchor='n')

            valeur = tk.StringVar(value=prefill.get(definition['nom'], ''))
            if definition['type'] == 'choix':
                widget = ttk.Combobox(bloc, textvariable=valeur, width=42,
                                      values=list(definition['choix']),
                                      state='readonly')
            elif definition['type'] == 'texte_long':
                widget = ttk.Entry(bloc, textvariable=valeur, width=60,
                                   style='W.TEntry')
            else:
                widget = ttk.Entry(bloc, textvariable=valeur, width=45,
                                   style='W.TEntry')
            widget.pack(side='left', padx=(0, 8))
            ttk.Label(bloc, style='WAide.TLabel', wraplength=300,
                      text=definition['aide']).pack(side='left',
                                                    fill='x', expand=True)
            self._widgets[definition['nom']] = valeur

        ttk.Label(parent, style='WAide.TLabel',
                  text='*  exige pour passer le statut a « accepted »'
                  ).pack(anchor='w', pady=(4, 10))

        self._confirmation = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            parent, style='W.TCheckbutton', variable=self._confirmation,
            text=('Je confirme avoir verifie ces informations et engager ma '
                  'responsabilite de reviseur.')).pack(anchor='w')

    def _construire_actions(self, parent) -> None:
        """Barre du bas : controle a blanc, et enregistrement."""
        barre = ttk.Frame(parent, style='W.TFrame', padding=(8, 8))
        barre.pack(side='bottom', fill='x')
        self._etat = ttk.Label(barre, background=GRIS_CLAIR,
                               foreground=TEXTE, font=(POLICE, 9),
                               wraplength=LARGEUR - 320,
                               text='Statut : pending')
        self._etat.pack(side='left', fill='x', expand=True)
        ttk.Button(barre, style='W.TButton', text='Controler',
                   command=self._controler).pack(side='right', padx=(6, 0))
        ttk.Button(barre, style='WAccent.TButton', text='Enregistrer',
                   command=self._enregistrer).pack(side='right')

    # -- Comportement ------------------------------------------------------

    def reponses(self) -> Dict[str, str]:
        """Valeurs saisies, sans aucune substitution.

        Returns:
            dict: Champ -> valeur telle que saisie.
        """
        return dict((nom, variable.get())
                    for nom, variable in self._widgets.items())

    def _controler(self) -> Dict[str, Any]:
        """Evalue sans rien ecrire, et affiche le motif de refus.

        Returns:
            dict: Ce que rend `evaluer_acceptation`.
        """
        acceptation = noyau.evaluer_acceptation(
            self.reponses(), bool(self._confirmation.get()))
        if acceptation['accepte']:
            self._etat.configure(
                text='Statut : accepted — toutes les preuves sont completes.',
                foreground=VERT)
        else:
            self._etat.configure(
                text='Statut : pending — %s'
                     % ' ; '.join(acceptation['motifs_de_refus']),
                foreground=ORANGE)
        return acceptation

    def _enregistrer(self) -> Optional[Dict[str, Any]]:
        """Ecrit le CSV et le JSON d audit, sans toucher au modele VE.

        Returns:
            dict | None: Chemins ecrits, ou `None` si l ecriture a echoue.
        """
        acceptation = self._controler()
        horodatage = datetime.now().strftime('%Y%m%d_%H%M%S')
        try:
            ecriture = noyau.ecrire_csv(
                self.chemin_csv, self.reponses(),
                acceptation['statut_effectif'], horodatage)
            actions = noyau.actions_restantes(
                self.reponses(), self.detecte, acceptation)
            audit = noyau.construire_audit(
                self.reponses(), self.detecte, acceptation, actions,
                ecriture['chemin'], ecriture['sauvegarde'], horodatage)
            chemin_audit = noyau.ecrire_audit(
                self.dossier_audit, audit,
                self.reponses().get('project_id') or 'UNKNOWN', horodatage)
        except OSError as erreur:
            if messagebox is not None:
                messagebox.showerror('Enregistrement', '%s' % erreur)
            return None

        self._resultat = {'csv': ecriture['chemin'],
                          'sauvegarde': ecriture['sauvegarde'],
                          'audit': chemin_audit,
                          'statut': acceptation['statut_effectif']}
        if messagebox is not None:
            messagebox.showinfo(
                'Enregistrement',
                'Statut ecrit : %s\n\nCSV : %s\nAudit : %s\n\n'
                'Aucune donnee VE n a ete modifiee.'
                % (acceptation['statut_effectif'], ecriture['chemin'],
                   chemin_audit))
        return self._resultat

    def lancer(self) -> Optional[Dict[str, Any]]:
        """Ouvre la fenetre et rend le resultat apres fermeture.

        Returns:
            dict | None: Chemins ecrits, ou `None` si rien n a ete enregistre.
        """
        self._racine.mainloop()
        return self._resultat


def chemins_du_projet(dossier_projet: str, project_id: str
                      ) -> Dict[str, str]:
    """Compose les emplacements d ecriture, sous le projet VE.

    Rien n est ecrit ailleurs : ni dans le depot, ni dans un dossier systeme.
    C est ce qui rend l assistant utilisable sans droits administrateur.

    Args:
        dossier_projet: Racine du projet VE.
        project_id: Identifiant du projet.

    Returns:
        dict: `csv` et `audit`.
    """
    identifiant = (project_id or 'UNKNOWN').strip() or 'UNKNOWN'
    return {
        'csv': os.path.join(dossier_projet, 'sia4010_evidence',
                            'SIA3802_project_metadata_%s.csv' % identifiant),
        'audit': os.path.join(dossier_projet, 'sia_compliance_artifacts',
                              'evidence'),
    }
