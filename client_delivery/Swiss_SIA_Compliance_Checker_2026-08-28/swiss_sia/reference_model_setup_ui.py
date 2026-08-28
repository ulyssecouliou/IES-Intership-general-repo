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
    from ui import design, tk_theme
except ImportError:  # pragma: no cover
    tk = filedialog = messagebox = ttk = None
    design = tk_theme = None


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
        # One call brings this window onto the shared IES house style, instead
        # of the ad-hoc font and colour it carried before.
        self.fonts = tk_theme.apply_ies_theme(self.root)
        tk_theme.centre_on_screen(self.root, 780, 470)
        self.root.minsize(700, 430)
        self.weather = tk.StringVar()
        self.station = tk.StringVar(value="Non selectionne")
        self.scenario = tk.StringVar()
        self._build()

    def _build(self) -> None:
        # Navy heading band: the house style opens every surface the same way.
        band = ttk.Frame(self.root, style="Band.TFrame", padding=design.PAD_BAND)
        band.pack(fill="x")
        ttk.Label(
            band,
            text="Modele de reference SIA 380/2",
            style="BandTitle.TLabel",
        ).pack(anchor="w")
        ttk.Label(
            band,
            text=(
                "Preparation fail-closed. Cette etape lie un EPW choisi ; elle "
                "ne certifie ni le modele ni le climat."
            ),
            style="BandSubtitle.TLabel",
            wraplength=700,
        ).pack(anchor="w", pady=(design.SPACE["xs"], 0))

        # White card body, generous margin -- the house divides by space.
        outer = ttk.Frame(self.root, style="TFrame", padding=design.PAD_CARD)
        outer.pack(fill="both", expand=True)
        card = ttk.Frame(outer, style="Card.TFrame", padding=design.SPACE["xl"])
        card.pack(fill="both", expand=True)
        card.columnconfigure(1, weight=1)
        pad_y = (design.SPACE["md"], 0)

        ttk.Label(card, text="Projet jetable", style="Card.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(card, text=str(self.project_path), style="Card.TLabel").grid(
            row=0, column=1, columnspan=2, sticky="w", padx=(design.SPACE["md"], 0)
        )

        ttk.Label(card, text="Fichier meteo EPW", style="Card.TLabel").grid(
            row=1, column=0, sticky="w", pady=pad_y
        )
        ttk.Entry(card, textvariable=self.weather).grid(
            row=1, column=1, sticky="ew", padx=design.SPACE["md"], pady=pad_y
        )
        ttk.Button(
            card,
            text="Parcourir...",
            style="Secondary.TButton",
            command=self._browse,
        ).grid(row=1, column=2, pady=pad_y)

        ttk.Label(card, text="Station EPW detectee", style="Card.TLabel").grid(
            row=2, column=0, sticky="w", pady=pad_y
        )
        ttk.Label(card, textvariable=self.station, style="Card.TLabel").grid(
            row=2,
            column=1,
            columnspan=2,
            sticky="w",
            padx=(design.SPACE["md"], 0),
            pady=pad_y,
        )

        ttk.Label(card, text="Scenario/horizon (facultatif)", style="Card.TLabel").grid(
            row=3, column=0, sticky="w", pady=pad_y
        )
        ttk.Entry(card, textvariable=self.scenario).grid(
            row=3,
            column=1,
            columnspan=2,
            sticky="ew",
            padx=(design.SPACE["md"], 0),
            pady=pad_y,
        )

        ttk.Label(
            card,
            text=(
                "Laisser vide conserve un marqueur UNCONFIRMED_REVIEW_REQUIRED. "
                "Aucune valeur reglementaire ne sera inventee."
            ),
            style="CardCaption.TLabel",
            wraplength=680,
        ).grid(row=4, column=0, columnspan=3, sticky="w", pady=(design.SPACE["lg"], 0))

        # Footer: quiet Cancel, then the one accent-blue primary action.
        buttons = ttk.Frame(self.root, style="TFrame", padding=design.PAD_CARD)
        buttons.pack(fill="x")
        ttk.Button(
            buttons,
            text="Preparer puis lancer",
            style="Primary.TButton",
            command=self._prepare,
        ).pack(side="right")
        ttk.Button(
            buttons,
            text="Annuler",
            style="Secondary.TButton",
            command=self.root.destroy,
        ).pack(side="right", padx=(0, design.SPACE["sm"]))

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
            label = ", ".join(
                item for item in (epw.station, epw.region, epw.country) if item
            )
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
