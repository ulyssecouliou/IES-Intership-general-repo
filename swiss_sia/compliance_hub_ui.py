"""Compact scrollable Tk interface for the Swiss Compliance Hub."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from .compliance_hub import ACTIONS, HubAction, is_disposable_project

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError:  # pragma: no cover - only relevant outside desktop Python
    tk = None
    messagebox = None
    ttk = None


class ComplianceHubUnavailable(RuntimeError):
    """Raised when the native hub cannot be displayed."""


def _centred_geometry(
    width: int, height: int, screen_width: int, screen_height: int
) -> str:
    """Return a visible centred Tk geometry string for the current display."""

    visible_width = max(720, min(int(width), max(720, int(screen_width) - 80)))
    visible_height = max(500, min(int(height), max(500, int(screen_height) - 100)))
    x = max(0, (int(screen_width) - visible_width) // 2)
    y = max(0, (int(screen_height) - visible_height) // 2)
    return "{}x{}+{}+{}".format(visible_width, visible_height, x, y)


class ComplianceHub:
    """Scrollable workflow selector that delegates to existing launchers."""

    def __init__(
        self,
        project_path: str,
        capabilities: Dict[str, int],
        executor: Callable[[str], Any],
    ) -> None:
        if tk is None or ttk is None:
            raise ComplianceHubUnavailable("Tkinter is unavailable in this runtime.")
        self.project_path = str(project_path or "")
        self.capabilities = dict(capabilities or {})
        self.executor = executor
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("IES Swiss Compliance Hub")
        self.root.minsize(720, 500)
        self.root.configure(background="#f3f6f9")
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self._configure_style()
        self._build()

    def _close(self) -> None:
        """Close the window without leaving a hidden Tk event loop in VE."""

        try:
            self.root.quit()
        finally:
            self.root.destroy()

    def _show_in_foreground(self) -> None:
        """Place the hub visibly above VE, then release the topmost flag."""

        self.root.update_idletasks()
        self.root.geometry(
            _centred_geometry(
                940,
                680,
                self.root.winfo_screenwidth(),
                self.root.winfo_screenheight(),
            )
        )
        self.root.deiconify()
        self.root.lift()
        try:
            self.root.attributes("-topmost", True)
            self.root.after(900, lambda: self.root.attributes("-topmost", False))
        except tk.TclError:
            pass
        self.root.after_idle(self.root.focus_force)

    def _configure_style(self) -> None:
        """Configure a small deterministic IES-like visual theme."""
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Hub.TFrame", background="#f3f6f9")
        style.configure("Card.TFrame", background="#ffffff")
        style.configure(
            "Title.TLabel", background="#142b4a", foreground="#ffffff",
            font=("Segoe UI", 16, "bold"),
        )
        style.configure(
            "Subtitle.TLabel", background="#142b4a", foreground="#dce8f5",
            font=("Segoe UI", 9),
        )
        style.configure(
            "CardTitle.TLabel", background="#ffffff", foreground="#142b4a",
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "CardText.TLabel", background="#ffffff", foreground="#45566a",
            font=("Segoe UI", 9),
        )
        style.configure(
            "Hub.TButton", padding=(12, 7), font=("Segoe UI", 9, "bold")
        )

    def _build(self) -> None:
        """Build header, capability banner and scrollable action cards."""
        header = ttk.Frame(self.root, style="Card.TFrame")
        header.configure(style="Card.TFrame")
        header.pack(fill="x")
        banner = tk.Frame(header, background="#142b4a", padx=18, pady=13)
        banner.pack(fill="x")
        ttk.Label(
            banner, text="Swiss Compliance Hub", style="Title.TLabel"
        ).pack(anchor="w")
        ttk.Label(
            banner,
            text="Projet actif : {}".format(self.project_path or "NON DETECTE"),
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        summary = tk.Frame(self.root, background="#e8f0f8", padx=16, pady=9)
        summary.pack(fill="x")
        message = (
            "SIA 380/2 : audit et preuves disponibles; generateur encore partiel.   "
            "SIA 4010 : {guarded}/{exact} cas avec mutation VE verifiee, "
            "{runtime} cas en qualification runtime."
        ).format(
            guarded=self.capabilities.get("guarded_mutation_cases", 0),
            exact=self.capabilities.get("exact_cases", 0),
            runtime=self.capabilities.get("runtime_qualification_cases", 0),
        )
        tk.Label(
            summary, text=message, background="#e8f0f8", foreground="#263b52",
            font=("Segoe UI", 9, "bold"), wraplength=890, justify="left",
        ).pack(anchor="w")

        holder = ttk.Frame(self.root, style="Hub.TFrame", padding=10)
        holder.pack(fill="both", expand=True)
        canvas = tk.Canvas(
            holder, background="#f3f6f9", highlightthickness=0
        )
        scrollbar = ttk.Scrollbar(holder, orient="vertical", command=canvas.yview)
        interior = ttk.Frame(canvas, style="Hub.TFrame")
        window = canvas.create_window((0, 0), window=interior, anchor="nw")
        interior.bind(
            "<Configure>",
            lambda _event: canvas.configure(scrollregion=canvas.bbox("all")),
        )
        canvas.bind(
            "<Configure>", lambda event: canvas.itemconfigure(window, width=event.width)
        )
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all(
            "<MouseWheel>",
            lambda event: canvas.yview_scroll(int(-event.delta / 120), "units"),
        )

        for action in ACTIONS:
            self._add_action(interior, action)

        footer = tk.Frame(self.root, background="#f3f6f9", padx=14, pady=8)
        footer.pack(fill="x")
        tk.Label(
            footer,
            text=(
                "Ce hub orchestre les workflows existants. Il ne delivre ni "
                "certification SIA ni attestation officielle."
            ),
            background="#f3f6f9", foreground="#6b7888", font=("Segoe UI", 8),
        ).pack(side="left")
        ttk.Button(footer, text="Fermer", command=self._close).pack(side="right")

    def _add_action(self, parent: Any, action: HubAction) -> None:
        """Add one workflow card and its guarded launch button."""
        card = ttk.Frame(parent, style="Card.TFrame", padding=12)
        card.pack(fill="x", pady=5)
        card.columnconfigure(0, weight=1)
        ttk.Label(card, text=action.title, style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        tk.Label(
            card, text=action.badge, background="#edf3f8", foreground="#234a70",
            font=("Segoe UI", 8, "bold"), padx=7, pady=3,
        ).grid(row=0, column=1, padx=(10, 0), sticky="e")
        ttk.Label(
            card, text=action.description, style="CardText.TLabel", wraplength=690
        ).grid(row=1, column=0, sticky="w", pady=(5, 0))
        ttk.Button(
            card, text="Ouvrir", style="Hub.TButton",
            command=lambda item=action: self._launch(item),
        ).grid(row=1, column=1, padx=(12, 0), sticky="e")

    def _launch(self, action: HubAction) -> None:
        """Apply disposable-project and confirmation guards before delegation."""
        if action.requires_disposable_project and not is_disposable_project(
            self.project_path
        ):
            if messagebox is not None:
                messagebox.showerror(
                    "Projet jetable requis",
                    "Cette action peut modifier VE. Ouvrez un projet sauvegarde dont "
                    "le nom se termine par _TEST, _COPY ou _DISPOSABLE.",
                    parent=self.root,
                )
            return
        if action.mutates_ve and messagebox is not None:
            confirmed = messagebox.askyesno(
                "Mutation VE controlee",
                "Continuer uniquement dans un projet jetable sauvegarde. Les controles "
                "du workflow resteront fail-closed. Lancer maintenant ?",
                parent=self.root,
            )
            if not confirmed:
                return
        launcher = action.launcher
        self._close()
        self.executor(launcher)

    def run(self) -> None:
        """Enter the Tk event loop."""
        self._show_in_foreground()
        print(
            "SWISS COMPLIANCE HUB: WINDOW_OPEN - close the window or choose an action "
            "to complete this VEScripts run.",
            flush=True,
        )
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            try:
                self._close()
            except Exception:
                pass
            print("SWISS COMPLIANCE HUB: CLOSED_AFTER_USER_INTERRUPT", flush=True)


def launch_hub(
    project_path: str,
    capabilities: Dict[str, int],
    executor: Callable[[str], Any],
) -> None:
    """Create and display the native Swiss Compliance Hub."""
    ComplianceHub(project_path, capabilities, executor).run()
