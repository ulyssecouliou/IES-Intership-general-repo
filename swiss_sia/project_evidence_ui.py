"""Tkinter editor for reviewer-owned, project-local SIA evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .project_evidence import (
    FAMILIES, FIELD_CHOICES, empty_record, load_records, save_records,
)

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError:  # pragma: no cover
    tk = messagebox = ttk = None


LABELS = {
    "project_id": "Projet", "building_status": "Statut du bâtiment",
    "weather_basis": "Base climatique approuvée", "weather_file": "Fichier météo",
    "location": "Localité / station", "altitude_m": "Altitude (m)",
    "review_status": "Statut de revue", "reviewer": "Responsable / réviseur",
    "review_date": "Date (AAAA-MM-JJ)", "source_document": "Document source",
    "source_reference": "Page / clause / référence", "notes": "Notes",
    "comparison_scope": "Périmètre", "comparison_metric": "Indicateur",
    "project_value": "Valeur projet", "reference_value": "Valeur de référence",
    "comparison_result": "Résultat", "unit": "Unité", "system_id": "Système VE",
    "room_or_zone": "Pièce / zone", "system_type": "Type de système",
    "control_class": "Classe de commande", "airflow_band": "Bande de débit",
    "specific_airflow_m3_h_m2": "Débit spécifique (m³/h/m²)",
    "air_flow_control": "AIR_FLOW_CTRL lu dans VE", "fan_control": "FAN_CTRL lu dans VE",
    "demand_sensor": "Capteur de demande", "control_scope": "Portée de la commande",
    "minimum_airflow_percent": "Débit minimum (%)", "time_schedule": "Horaire / profil",
    "generator_class": "Classe du générateur", "capacity_kw": "Puissance nominale (kW)",
    "nominal_eer": "EER nominal", "seer": "SEER déclaré", "room_id": "ID pièce",
    "thermal_template_id": "ID template thermique", "sia3874_control_type": "Type SIA 387/4",
    "daylight_control": "Commande lumière du jour", "required_electrical_power_w_m2": "Puissance requise (W/m²)",
    "conditioned_area_m2": "Surface conditionnée (m²)", "cooling_present": "Refroidissement présent",
    "cooling_category": "Catégorie de nécessité du froid",
}


class ProjectEvidenceEditor:
    """Six-tab editor; acceptance is recalculated by the production validator."""

    def __init__(self, project_root: Path, project_label: str, weather_file: str = "", parent: Any = None) -> None:
        if tk is None or ttk is None:
            raise RuntimeError("Tkinter est indisponible dans cet environnement.")
        self.project_root = Path(project_root)
        self.project_label = project_label
        self.weather_file = weather_file
        self.window = tk.Toplevel(parent) if parent is not None else tk.Tk()
        self.window.title("IES - Preuves projet SIA 380/2")
        self.window.geometry("1040x760")
        self.window.minsize(820, 620)
        self.records: Dict[str, List[Dict[str, str]]] = {}
        self.indices: Dict[str, int] = {}
        self.widgets: Dict[str, Dict[str, Any]] = {}
        self.counters: Dict[str, Any] = {}
        self.status = tk.StringVar(value="Les champs restent en attente tant que la preuve n'est pas complète et signée.")
        self._build()

    def _build(self) -> None:
        header = tk.Frame(self.window, bg="#0b2239", padx=24, pady=16)
        header.pack(fill="x")
        tk.Label(header, text="PREUVES PROJET · SIA 380/2", bg="#0b2239", fg="#57bfd4", font=("Segoe UI Semibold", 9)).pack(anchor="w")
        tk.Label(header, text=self.project_label, bg="#0b2239", fg="white", font=("Georgia", 18, "bold")).pack(anchor="w")
        tk.Label(header, text="Saisir uniquement des valeurs traçables. Le logiciel ne valide jamais une acceptation incomplète.", bg="#0b2239", fg="#d7e3eb", font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 0))
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill="both", expand=True, padx=16, pady=14)
        for spec in FAMILIES:
            self.records[spec.key] = load_records(self.project_root, spec.key, self.project_label, self.weather_file)
            self.indices[spec.key] = 0
            tab = ttk.Frame(notebook, padding=14)
            notebook.add(tab, text=spec.title)
            ttk.Label(tab, text=spec.help_text, wraplength=930).pack(anchor="w", pady=(0, 8))
            nav = ttk.Frame(tab)
            nav.pack(fill="x", pady=(0, 8))
            ttk.Button(nav, text="‹ Précédent", command=lambda key=spec.key: self._move(key, -1)).pack(side="left")
            ttk.Button(nav, text="Suivant ›", command=lambda key=spec.key: self._move(key, 1)).pack(side="left", padx=5)
            ttk.Button(nav, text="+ Ajouter une ligne", command=lambda key=spec.key: self._add(key)).pack(side="left", padx=(12, 5))
            ttk.Button(nav, text="Supprimer cette ligne", command=lambda key=spec.key: self._delete(key)).pack(side="left")
            self.counters[spec.key] = ttk.Label(nav, text="")
            self.counters[spec.key].pack(side="right")
            canvas = tk.Canvas(tab, highlightthickness=0)
            scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)
            form = ttk.Frame(canvas, padding=(4, 2, 12, 8))
            form_window = canvas.create_window((0, 0), window=form, anchor="nw")
            form.bind("<Configure>", lambda _event, c=canvas: c.configure(scrollregion=c.bbox("all")))
            canvas.bind("<Configure>", lambda event, c=canvas, item=form_window: c.itemconfigure(item, width=event.width))
            self.widgets[spec.key] = {}
            for index, field in enumerate(spec.fields):
                row = ttk.Frame(form)
                row.pack(fill="x", pady=3)
                ttk.Label(row, text=LABELS.get(field, field.replace("_", " ").capitalize()), width=34).pack(side="left", anchor="n", pady=6)
                if field in FIELD_CHOICES:
                    widget = ttk.Combobox(row, values=FIELD_CHOICES[field], state="readonly")
                else:
                    widget = ttk.Entry(row)
                widget.pack(side="left", fill="x", expand=True, ipady=5)
                if field == "project_id":
                    widget.configure(state="disabled")
                self.widgets[spec.key][field] = widget
            self._show(spec.key)
        footer = ttk.Frame(self.window, padding=(16, 0, 16, 14))
        footer.pack(fill="x")
        ttk.Label(footer, textvariable=self.status, wraplength=720).pack(side="left", fill="x", expand=True)
        ttk.Button(footer, text="Enregistrer l'onglet actif", command=lambda: self._save_current(notebook)).pack(side="right")

    def _capture(self, key: str) -> None:
        row = self.records[key][self.indices[key]]
        for field, widget in self.widgets[key].items():
            if field == "project_id":
                continue
            row[field] = widget.get().strip()

    def _show(self, key: str) -> None:
        record = self.records[key][self.indices[key]]
        for field, widget in self.widgets[key].items():
            state = str(widget.cget("state"))
            if state == "disabled":
                widget.configure(state="normal")
            widget.delete(0, "end")
            widget.insert(0, record.get(field, ""))
            if field == "project_id":
                widget.configure(state="disabled")
        self.counters[key].configure(text="Ligne {} / {}".format(self.indices[key] + 1, len(self.records[key])))

    def _move(self, key: str, delta: int) -> None:
        self._capture(key)
        self.indices[key] = max(0, min(len(self.records[key]) - 1, self.indices[key] + delta))
        self._show(key)

    def _add(self, key: str) -> None:
        self._capture(key)
        self.records[key].append(empty_record(key, self.project_label, self.weather_file))
        self.indices[key] = len(self.records[key]) - 1
        self._show(key)

    def _delete(self, key: str) -> None:
        if len(self.records[key]) == 1:
            self.records[key][0] = empty_record(key, self.project_label, self.weather_file)
            self.indices[key] = 0
        else:
            self.records[key].pop(self.indices[key])
            self.indices[key] = min(self.indices[key], len(self.records[key]) - 1)
        self._show(key)

    def _save_current(self, notebook: Any) -> None:
        tab_index = notebook.index(notebook.select())
        key = FAMILIES[tab_index].key
        self._capture(key)
        result = save_records(self.project_root, key, self.project_label, self.records[key])
        if result["forced_pending_count"]:
            text = "Enregistré, mais {} ligne(s) demandée(s comme acceptées restent PENDING : informations ou signature incomplètes.".format(result["forced_pending_count"])
        else:
            text = "Enregistré : {} ligne(s), {} acceptée(s).".format(result["row_count"], result["accepted_count"])
        self.status.set(text + "  " + result["path"])
        if messagebox is not None:
            messagebox.showinfo("Preuves SIA 380/2", text, parent=self.window)

    def run(self) -> None:
        self.window.mainloop()


def launch_project_evidence_editor(project_root: Path, project_label: str, weather_file: str = "", parent: Any = None) -> ProjectEvidenceEditor:
    editor = ProjectEvidenceEditor(project_root, project_label, weather_file, parent)
    if parent is None:
        editor.run()
    return editor
