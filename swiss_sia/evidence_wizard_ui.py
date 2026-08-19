# -*- coding: utf-8 -*-
"""VEScripts interface for SIA 380/2 evidence collection.

Does NOTHING but display and data entry. All logic — validation,
rejection of acceptance, writing — lives in `swiss_sia/evidence_wizard.py`, in
pure Python and tested. This module decides nothing.

EXECUTION CONSTRAINTS, explicitly maintained:
    - Python 3.12 embedded in IESVE;
    - limited screen size: 980x680 window, resizable, with ALL the
      form in a scrollable area;
    - no administrator rights: nothing is written outside the VE project and
      the evidence folder;
    - NO VE MUTATION: the model is read, never modified;
    - fail-closed: the `accepted` status is RECALCULATED, never taken from
      the input.

WHAT THE INTERFACE DOES NOT DO. It pronounces neither SIA 380/2 compliance
nor SIA 4010 validation, and takes no decision in place of the reviewer. An
empty field remains empty: it is never filled with a default value.
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

#: IES brand colours. Imported when available; otherwise neutral values,
#: so the wizard remains usable even if `ui/` is missing.
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

#: Deliberately modest window: the wizard must fit on a laptop.
LARGEUR = 980
HAUTEUR = 680

# English client-facing copy. The evidence schema and persisted field names
# remain unchanged so existing CSV/JSON audit files stay compatible.
FIELD_COPY_EN = {
    'project_id': ('Project identifier', 'Must match the active VE project folder.'),
    'building_status': ('Building status', 'Selects the applicable 100 h / 400 h comfort limit.'),
    'weather_basis': ('Climate basis', 'For example SIA 2028 DRY. Cite an approved source.'),
    'weather_file': ('Reviewed weather file', 'The file the reviewer declares correct for this project.'),
    'location': ('Location', 'Municipality or station; never inferred from a filename.'),
    'altitude_m': ('Altitude (m)', 'Project altitude in metres.'),
    'review_status': ('Review status', 'Remains pending until all evidence is complete.'),
    'reviewer': ('Reviewer', 'Person taking responsibility for the supplied evidence.'),
    'review_date': ('Review date (YYYY-MM-DD)', 'Date on which the reviewer approved the evidence.'),
    'source_document': ('Source document', 'Reviewed brief, specification or approval document.'),
    'source_reference': ('Source reference', 'Clause, page or approval reference.'),
    'notes': ('Notes', 'Information useful to a later reviewer.'),
    'ventilation_strategy': ('Ventilation strategy', 'What the project actually provides.'),
    'ventilation_justification': ('Ventilation justification', 'Explain the declared strategy; required before acceptance.'),
    'ventilation_flow_source': ('Ventilation flow-rate source', 'Where the flow rates come from; never inferred.'),
    'lighting_scope': ('Lighting assessment scope', 'State whether lighting is included in the assessment.'),
    'lighting_power_source': ('Lighting power source', 'Required when lighting is in scope.'),
    'aps_outputs_required': ('Fan/pump/auxiliary/coil outputs required?', 'Select NO only when justified by the model scope.'),
    'aps_outputs_justification': ('APS output justification', 'Required when the answer above is NO.'),
}

FACT_COPY_EN = {
    'project_id': ('Project identifier', 'Read from the active VE project folder.'),
    'aps_file': ('Selected APS file', 'Results file selected by the read-only audit.'),
    'detected_weather_file': ('Detected weather file', 'Technical VE/APS match only; this is not climate approval.'),
    'total_area_m2': ('Total room area (m2)', 'Sum of room floor areas.'),
    'total_heating_kwh': ('Total heating (kWh)', 'Extracted from Room units heating load, not a steady-state series.'),
    'total_cooling_kwh': ('Total cooling (kWh)', 'Extracted from Room units cooling load.'),
}

#: Colour associated with each finding category.
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
    """Raised when the wizard cannot be opened."""


class AssistantDePreuves(object):
    """SIA 380/2 evidence entry window.

    Attributes:
        detecte: Facts gathered in VE, displayed but never copied into
            the responses.
        chemin_csv: Evidence CSV to write.
        dossier_audit: Audit JSON folder.
    """

    def __init__(self, detecte: Optional[Dict[str, Any]] = None,
                 chemin_csv: str = '', dossier_audit: str = '') -> None:
        if tk is None:
            raise AssistantIndisponible(
                "tkinter is unavailable: run this wizard from the VE Python "
                "Scripts navigator.")
        if not chemin_csv or not dossier_audit:
            raise AssistantIndisponible(
                "Evidence CSV path and audit folder are required; the wizard "
                "will not write to an inferred location.")

        self.detecte = dict(detecte or {})
        self.chemin_csv = chemin_csv
        self.dossier_audit = dossier_audit
        self._widgets: Dict[str, Any] = {}
        self._resultat: Optional[Dict[str, Any]] = None

        self._racine = tk.Tk()
        self._racine.title('IES - SIA 380/2 Evidence Collection')
        self._racine.geometry('%dx%d' % (LARGEUR, HAUTEUR))
        self._racine.minsize(760, 520)
        self._appliquer_charte()
        self._construire()

    # -- Presentation ------------------------------------------------------

    def _appliquer_charte(self) -> None:
        """Apply IES brand colours.

        The `clam` theme is the only one that honours `background` on Windows:
        the others delegate to the system and ignore the brand theme.
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
        """Build the banner, the scrollable area and the action bar."""
        self._construire_bandeau()

        corps = ttk.Frame(self._racine, style='W.TFrame', padding=8)
        corps.pack(side='top', fill='both', expand=True)

        # SCROLLABLE AREA. Without it, the 19 fields overflow a laptop screen
        # and the last ones — including the confirmation — become unreachable.
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
        """Navy banner: the active VE project, and what the wizard is not."""
        bandeau = ttk.Frame(self._racine, style='WBandeau.TFrame',
                            padding=(16, 10))
        bandeau.pack(side='top', fill='x')
        ttk.Label(bandeau, style='WTitre.TLabel',
                  text='SIA 380/2 - Evidence Collection').pack(anchor='w')
        ttk.Label(
            bandeau, style='WSous.TLabel',
            text='Active VE project: %s'
                 % (self.detecte.get('project_id') or 'NOT DETECTED')
        ).pack(anchor='w', pady=(3, 0))
        ttk.Label(
            bandeau, style='WSous.TLabel', wraplength=LARGEUR - 60,
            text=('This wizard does not modify VE data, does not certify '
                  'SIA 380/2 compliance, and is not an SIA 4010 software '
                  'validation. It collects traceable review evidence.')
        ).pack(anchor='w', pady=(6, 0))

    def _construire_faits(self, parent) -> None:
        """Facts gathered in VE, displayed without being mixed with the responses."""
        ttk.Label(parent, style='WSection.TLabel',
                  text='Facts detected in VE (read-only)').pack(
                      anchor='w', pady=(0, 6))
        for cle, fait in sorted(noyau.faits_techniques(self.detecte).items()):
            label, note = FACT_COPY_EN.get(cle, (cle, 'Read from VE.'))
            ligne = ttk.Frame(parent, style='WCarte.TFrame')
            ligne.pack(fill='x', pady=1)
            ttk.Label(ligne, style='W.TLabel', width=26,
                      text=label).pack(side='left')
            ttk.Label(ligne, style='W.TLabel', width=34,
                      text='%s' % fait['valeur']).pack(side='left')
            ttk.Label(ligne, style='WAide.TLabel', wraplength=420,
                      text='[%s] %s' % (fait['statut'], note)
                      ).pack(side='left', fill='x', expand=True)
        ttk.Label(
            parent, style='WAide.TLabel', wraplength=LARGEUR - 80,
            text=('The detected weather file is not copied into the reviewed '
                  'weather field. That field records what the reviewer '
                  'declares correct. A technical match is not climate approval.')
        ).pack(anchor='w', pady=(6, 12))

    def _construire_champs(self, parent) -> None:
        """Build one widget per field, pre-filled only when demonstrated."""
        ttk.Label(parent, style='WSection.TLabel',
                  text='Evidence to complete').pack(anchor='w', pady=(0, 6))
        prefill = noyau.prefill(self.detecte)

        for definition in noyau.CHAMPS:
            bloc = ttk.Frame(parent, style='WCarte.TFrame')
            bloc.pack(fill='x', pady=3)
            etiquette, aide = FIELD_COPY_EN.get(
                definition['nom'],
                (definition['nom'].replace('_', ' ').title(), ''))
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
                      text=aide).pack(side='left',
                                                    fill='x', expand=True)
            self._widgets[definition['nom']] = valeur

        ttk.Label(parent, style='WAide.TLabel',
                  text='*  required before status can become accepted'
                  ).pack(anchor='w', pady=(4, 10))

        self._confirmation = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            parent, style='W.TCheckbutton', variable=self._confirmation,
            text=('I confirm that I reviewed this information and accept '
                  'responsibility as the named reviewer.')).pack(anchor='w')

    def _construire_actions(self, parent) -> None:
        """Bottom bar: dry-run check, and save."""
        barre = ttk.Frame(parent, style='W.TFrame', padding=(8, 8))
        barre.pack(side='bottom', fill='x')
        self._etat = ttk.Label(barre, background=GRIS_CLAIR,
                               foreground=TEXTE, font=(POLICE, 9),
                               wraplength=LARGEUR - 320,
                               text='Status: pending')
        self._etat.pack(side='left', fill='x', expand=True)
        ttk.Button(barre, style='W.TButton', text='Validate',
                   command=self._controler).pack(side='right', padx=(6, 0))
        ttk.Button(barre, style='WAccent.TButton', text='Save evidence',
                   command=self._enregistrer).pack(side='right')

    # -- Behaviour ----------------------------------------------------------

    def reponses(self) -> Dict[str, str]:
        """Entered values, with no substitution.

        Returns:
            dict: Field -> value as entered.
        """
        return dict((nom, variable.get())
                    for nom, variable in self._widgets.items())

    def _controler(self) -> Dict[str, Any]:
        """Evaluate without writing anything, and display the rejection reason.

        Returns:
            dict: What `evaluer_acceptation` returns.
        """
        acceptation = noyau.evaluer_acceptation(
            self.reponses(), bool(self._confirmation.get()))
        if acceptation['accepte']:
            self._etat.configure(
                text='Status: accepted - all required evidence is complete.',
                foreground=VERT)
        else:
            summary = []
            if acceptation.get('manquants'):
                summary.append('%d required field(s) missing'
                               % len(acceptation['manquants']))
            if acceptation.get('erreurs'):
                summary.append('%d invalid value(s)'
                               % len(acceptation['erreurs']))
            if not self._confirmation.get():
                summary.append('reviewer confirmation missing')
            if not summary:
                summary.append('conditional evidence is incomplete')
            self._etat.configure(
                text='Status: pending - %s' % '; '.join(summary),
                foreground=ORANGE)
        return acceptation

    def _enregistrer(self) -> Optional[Dict[str, Any]]:
        """Write the CSV and audit JSON, without touching the VE model.

        Returns:
            dict | None: Written paths, or `None` if writing failed.
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
                messagebox.showerror('Save evidence', '%s' % erreur)
            return None

        self._resultat = {'csv': ecriture['chemin'],
                          'sauvegarde': ecriture['sauvegarde'],
                          'audit': chemin_audit,
                          'statut': acceptation['statut_effectif']}
        if messagebox is not None:
            messagebox.showinfo(
                'Evidence saved',
                'Recorded status: %s\n\nCSV: %s\nAudit: %s\n\n'
                'No VE data was modified.'
                % (acceptation['statut_effectif'], ecriture['chemin'],
                   chemin_audit))
        return self._resultat

    def lancer(self) -> Optional[Dict[str, Any]]:
        """Open the window and return the result after closing.

        Returns:
            dict | None: Written paths, or `None` if nothing was saved.
        """
        self._racine.mainloop()
        return self._resultat


def chemins_du_projet(dossier_projet: str, project_id: str
                      ) -> Dict[str, str]:
    """Compose the write locations, under the VE project.

    Nothing is written elsewhere: not in the repository, not in a system folder.
    This is what makes the wizard usable without administrator rights.

    Args:
        dossier_projet: VE project root.
        project_id: Project identifier.

    Returns:
        dict: `csv` and `audit`.
    """
    identifiant = (project_id or 'UNKNOWN').strip() or 'UNKNOWN'
    return {
        'csv': os.path.join(dossier_projet, 'sia4010_evidence',
                            'SIA3802_project_metadata_%s.csv' % identifiant),
        'audit': os.path.join(dossier_projet, 'sia_compliance_artifacts',
                              'evidence'),
    }
