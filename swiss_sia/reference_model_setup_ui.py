"""Small native setup dialog used before reference-model generation."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from .reference_model_setup import (
    ReferenceModelSetupError,
    SetupReceipt,
    prepare_reference_model_bundle,
    read_epw_metadata,
)

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except ImportError:  # pragma: no cover
    tk = filedialog = messagebox = ttk = None


class ReferenceModelSetupDialog:
    """Collect the only external input that must not be guessed: weather."""

    def __init__(self, project_path: Path, repository_root: Path) -> None:
        if tk is None or ttk is None:
            raise ReferenceModelSetupError("Tkinter is unavailable in this runtime.")
        self.project_path = Path(project_path)
        self.repository_root = Path(repository_root)
        self.receipt: Optional[SetupReceipt] = None
        self.root = tk.Tk()
        self.root.title("Preparation du modele de reference suisse")
        self.root.geometry("760x430")
        self.root.minsize(680, 390)
        self.weather = tk.StringVar()
        self.station = tk.StringVar(value="Non selectionne")
        self.scenario = tk.StringVar()
        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self.root, padding=18)
        frame.pack(fill="both", expand=True)
        frame.columnconfigure(1, weight=1)
        ttk.Label(
            frame,
            text="Modele de reference SIA 380/2 - preparation fail-closed",
            font=("Segoe UI", 14, "bold"),
        ).grid(row=0, column=0, columnspan=3, sticky="w")
        ttk.Label(
            frame,
            text=(
                "Cette etape copie les JSON maintenus dans le projet jetable et "
                "lie un EPW choisi. Elle ne certifie ni le modele ni le climat."
            ),
            wraplength=700,
        ).grid(row=1, column=0, columnspan=3, sticky="w", pady=(8, 18))
        ttk.Label(frame, text="Projet jetable").grid(row=2, column=0, sticky="w")
        ttk.Label(frame, text=str(self.project_path)).grid(
            row=2, column=1, columnspan=2, sticky="w", padx=(12, 0)
        )
        ttk.Label(frame, text="Fichier meteo EPW").grid(
            row=3, column=0, sticky="w", pady=(14, 0)
        )
        ttk.Entry(frame, textvariable=self.weather).grid(
            row=3, column=1, sticky="ew", padx=12, pady=(14, 0)
        )
        ttk.Button(frame, text="Parcourir...", command=self._browse).grid(
            row=3, column=2, pady=(14, 0)
        )
        ttk.Label(frame, text="Station EPW detectee").grid(
            row=4, column=0, sticky="w", pady=(12, 0)
        )
        ttk.Label(frame, textvariable=self.station).grid(
            row=4, column=1, columnspan=2, sticky="w", padx=(12, 0), pady=(12, 0)
        )
        ttk.Label(frame, text="Scenario/horizon (facultatif)").grid(
            row=5, column=0, sticky="w", pady=(12, 0)
        )
        ttk.Entry(frame, textvariable=self.scenario).grid(
            row=5, column=1, columnspan=2, sticky="ew", padx=(12, 0), pady=(12, 0)
        )
        ttk.Label(
            frame,
            text=(
                "Laisser vide conserve un marqueur UNCONFIRMED_REVIEW_REQUIRED. "
                "Aucune valeur reglementaire ne sera inventee."
            ),
            foreground="#6b4e16",
            wraplength=700,
        ).grid(row=6, column=0, columnspan=3, sticky="w", pady=(10, 20))
        buttons = ttk.Frame(frame)
        buttons.grid(row=7, column=0, columnspan=3, sticky="e")
        ttk.Button(buttons, text="Annuler", command=self.root.destroy).pack(
            side="right", padx=(8, 0)
        )
        ttk.Button(
            buttons, text="Preparer puis lancer", command=self._prepare
        ).pack(side="right")

    def _browse(self) -> None:
        selected = filedialog.askopenfilename(
            parent=self.root,
            title="Choisir le fichier meteo EPW",
            filetypes=(("EnergyPlus Weather", "*.epw"), ("Tous les fichiers", "*.*")),
        )
        if not selected:
            return
        self.weather.set(selected)
        try:
            epw = read_epw_metadata(Path(selected))
            label = ", ".join(item for item in (epw.station, epw.region, epw.country) if item)
            self.station.set(label or "LOCATION presente, station non renseignee")
        except ReferenceModelSetupError as exc:
            self.station.set("EPW invalide")
            messagebox.showerror("Fichier meteo refuse", str(exc), parent=self.root)

    def _prepare(self) -> None:
        try:
            receipt = prepare_reference_model_bundle(
                self.project_path,
                self.repository_root,
                Path(self.weather.get().strip()),
                climate_scenario=self.scenario.get(),
            )
        except (ReferenceModelSetupError, OSError) as exc:
            messagebox.showerror("Preparation bloquee", str(exc), parent=self.root)
            return
        self.receipt = receipt
        messagebox.showinfo(
            "Bundle pret",
            "JSON et meteo prepares dans le projet. Le generateur fail-closed va demarrer.",
            parent=self.root,
        )
        self.root.destroy()

    def run(self) -> Optional[SetupReceipt]:
        self.root.mainloop()
        return self.receipt


def launch_reference_model_setup(
    project_path: Path,
    repository_root: Path,
    on_ready: Callable[[SetupReceipt], object],
) -> Optional[SetupReceipt]:
    """Open the dialog and invoke the generator only after successful setup."""
    receipt = ReferenceModelSetupDialog(project_path, repository_root).run()
    if receipt is not None:
        on_ready(receipt)
    return receipt
