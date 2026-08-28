"""English client-facing Tk cockpit for Swiss compliance workflows in IESVE."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Dict

from .compliance_hub import (
    ACTIONS,
    HubAction,
    build_project_snapshot,
    is_disposable_project,
)

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError:  # pragma: no cover - only relevant outside desktop Python
    tk = None
    messagebox = None
    ttk = None


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
PRESENTER_GUIDE = REPOSITORY_ROOT / "docs" / "project" / "CLIENT_DEMO_RUNBOOK_EN.md"
EVIDENCE_DASHBOARD = (
    REPOSITORY_ROOT
    / "sia4010_evidence"
    / "autonomy"
    / "navigator"
    / "sia4010_all_classes_navigator.html"
)


class ComplianceHubUnavailable(RuntimeError):
    """Raised when the native cockpit cannot be displayed."""


def _centred_geometry(
    width: int, height: int, screen_width: int, screen_height: int
) -> str:
    """Return a visible centred Tk geometry string for the current display."""
    visible_width = max(720, min(int(width), max(720, int(screen_width) - 80)))
    visible_height = max(500, min(int(height), max(500, int(screen_height) - 100)))
    x = max(0, (int(screen_width) - visible_width) // 2)
    y = max(0, (int(screen_height) - visible_height) // 2)
    return "{}x{}+{}+{}".format(visible_width, visible_height, x, y)


def _status_palette(status: str) -> tuple[str, str]:
    """Return background and foreground colours for a fail-closed status."""
    normalized = str(status or "").upper()
    if normalized in {"PASS", "READY", "AVAILABLE", "WARNING"}:
        if normalized == "WARNING":
            return "#fff4dc", "#855600"
        return "#e7f6ef", "#126143"
    if "FAIL" in normalized or "BLOCK" in normalized:
        return "#fdeaea", "#9b2c2c"
    if "RECORDED" in normalized or "QUALIF" in normalized:
        return "#e8f0fa", "#24527a"
    return "#edf1f5", "#58687a"


class ComplianceHub:
    """Scrollable client cockpit delegating to guarded production launchers."""

    COLORS = {
        "navy": "#102a43",
        "blue": "#1f5f99",
        "blue_soft": "#e8f0fa",
        "canvas": "#f3f6f9",
        "card": "#ffffff",
        "text": "#1f3349",
        "muted": "#617286",
        "line": "#d9e2ec",
        "green": "#14805e",
        "green_soft": "#e7f6ef",
        "amber": "#b7791f",
        "amber_soft": "#fff4dc",
    }

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
        self.snapshot = build_project_snapshot(self.project_path)
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title("IES Swiss Compliance Workbench - MVP Demonstrator")
        self.root.minsize(720, 500)
        self.root.configure(background=self.COLORS["canvas"])
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
        """Place the cockpit visibly above VE, then release the topmost flag."""
        self.root.update_idletasks()
        self.root.geometry(
            _centred_geometry(
                1040,
                760,
                self.root.winfo_screenwidth(),
                self.root.winfo_screenheight(),
            )
        )
        self.root.deiconify()
        self.root.lift()
        try:
            self.root.attributes("-topmost", True)
            self.root.after(800, lambda: self.root.attributes("-topmost", False))
        except tk.TclError:
            pass
        self.root.after_idle(self.root.focus_force)

    def _configure_style(self) -> None:
        """Configure a deterministic IES-inspired visual theme."""
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Hub.TFrame", background=self.COLORS["canvas"])
        style.configure("Card.TFrame", background=self.COLORS["card"])
        style.configure(
            "Title.TLabel",
            background=self.COLORS["navy"],
            foreground="#ffffff",
            font=("Segoe UI", 18, "bold"),
        )
        style.configure(
            "Subtitle.TLabel",
            background=self.COLORS["navy"],
            foreground="#dce8f5",
            font=("Segoe UI", 9),
        )
        style.configure(
            "Section.TLabel",
            background=self.COLORS["canvas"],
            foreground=self.COLORS["navy"],
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "CardTitle.TLabel",
            background=self.COLORS["card"],
            foreground=self.COLORS["navy"],
            font=("Segoe UI", 10, "bold"),
        )
        style.configure(
            "CardText.TLabel",
            background=self.COLORS["card"],
            foreground=self.COLORS["muted"],
            font=("Segoe UI", 9),
        )
        style.configure("Hub.TButton", padding=(11, 7), font=("Segoe UI", 9, "bold"))
        style.configure("Quiet.TButton", padding=(9, 5), font=("Segoe UI", 8))

    def _build(self) -> None:
        """Build the header, live snapshot and grouped workflow cards."""
        self._build_header()

        holder = ttk.Frame(self.root, style="Hub.TFrame", padding=(12, 8, 12, 0))
        holder.pack(fill="both", expand=True)
        canvas = tk.Canvas(holder, background=self.COLORS["canvas"], highlightthickness=0)
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

        self._build_mvp_summary(interior)
        self._build_project_snapshot(interior)

        current_section = ""
        for action in ACTIONS:
            if action.section != current_section:
                current_section = action.section
                ttk.Label(
                    interior,
                    text=current_section.upper(),
                    style="Section.TLabel",
                ).pack(fill="x", pady=(16, 4))
            self._add_action(interior, action)

        self._build_guardrail(interior)
        self._build_footer()

    def _build_header(self) -> None:
        """Build the branded client-facing header."""
        banner = tk.Frame(self.root, background=self.COLORS["navy"], padx=20, pady=14)
        banner.pack(fill="x")
        top = tk.Frame(banner, background=self.COLORS["navy"])
        top.pack(fill="x")
        ttk.Label(top, text="Swiss Compliance Workbench", style="Title.TLabel").pack(
            side="left", anchor="w"
        )
        tk.Label(
            top,
            text="MVP DEMONSTRATOR  /  FAIL-CLOSED",
            background="#1f5f99",
            foreground="#ffffff",
            font=("Segoe UI", 8, "bold"),
            padx=9,
            pady=4,
        ).pack(side="right", anchor="e")
        ttk.Label(
            banner,
            text="SIA 380/2 client pre-check + SIA 4010 software verification laboratory",
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(4, 0))
        ttk.Label(
            banner,
            text="Active project: {}".format(self.snapshot.project_name),
            style="Subtitle.TLabel",
        ).pack(anchor="w", pady=(2, 0))

    def _build_mvp_summary(self, parent: Any) -> None:
        """Show scope-specific progress without presenting certification."""
        frame = ttk.Frame(parent, style="Hub.TFrame")
        frame.pack(fill="x", pady=(2, 8))
        for column in range(3):
            frame.columnconfigure(column, weight=1, uniform="summary")
        exact = self.capabilities.get("exact_cases", 0)
        guarded = self.capabilities.get("guarded_mutation_cases", 0)
        runtime = self.capabilities.get("runtime_qualification_cases", 0)
        tiles = (
            (
                "CLIENT CHECKER",
                "DEMO READY",
                "Read-only audit, evidence capture and auditable reporting",
                self.COLORS["green"],
            ),
            (
                "OFFICIAL COVERAGE",
                "{}/{}".format(exact, exact),
                "Exact SIA 4010 cases catalogued and source-traced",
                self.COLORS["blue"],
            ),
            (
                "AUTOMATION ROUTES",
                "{}/{}".format(guarded + runtime, exact),
                "{} guarded generator + {} runtime qualification paths".format(
                    guarded, runtime
                ),
                self.COLORS["amber"],
            ),
        )
        for column, (eyebrow, value, detail, accent) in enumerate(tiles):
            card = tk.Frame(
                frame,
                background=self.COLORS["card"],
                highlightbackground=self.COLORS["line"],
                highlightthickness=1,
                padx=13,
                pady=10,
            )
            card.grid(
                row=0, column=column, sticky="nsew", padx=(0 if column == 0 else 5, 0)
            )
            tk.Label(
                card,
                text=eyebrow,
                background=self.COLORS["card"],
                foreground=self.COLORS["muted"],
                font=("Segoe UI", 8, "bold"),
            ).pack(anchor="w")
            tk.Label(
                card,
                text=value,
                background=self.COLORS["card"],
                foreground=accent,
                font=("Segoe UI", 16, "bold"),
            ).pack(anchor="w", pady=(2, 1))
            tk.Label(
                card,
                text=detail,
                background=self.COLORS["card"],
                foreground=self.COLORS["muted"],
                font=("Segoe UI", 8),
                wraplength=190,
                justify="left",
            ).pack(anchor="w")

    def _build_project_snapshot(self, parent: Any) -> None:
        """Render evidence already present in the active project folder."""
        snapshot = self.snapshot
        card = tk.Frame(
            parent,
            background=self.COLORS["card"],
            highlightbackground=self.COLORS["line"],
            highlightthickness=1,
            padx=14,
            pady=11,
        )
        card.pack(fill="x", pady=(0, 4))
        title_row = tk.Frame(card, background=self.COLORS["card"])
        title_row.pack(fill="x")
        tk.Label(
            title_row,
            text="ACTIVE PROJECT READINESS",
            background=self.COLORS["card"],
            foreground=self.COLORS["navy"],
            font=("Segoe UI", 10, "bold"),
        ).pack(side="left")
        kind_bg, kind_fg = (
            (self.COLORS["blue_soft"], self.COLORS["blue"])
            if snapshot.project_kind.startswith("Disposable")
            else ("#edf1f5", self.COLORS["muted"])
        )
        tk.Label(
            title_row,
            text=snapshot.project_kind.upper(),
            background=kind_bg,
            foreground=kind_fg,
            font=("Segoe UI", 8, "bold"),
            padx=8,
            pady=3,
        ).pack(side="right")

        facts = (
            ("Model", "{} .mdl".format(snapshot.model_files)),
            ("APS", str(snapshot.aps_files)),
            ("Client audit", snapshot.client_audit_status),
            ("Template remediation", snapshot.template_remediation_status),
            ("Model audit", snapshot.model_audit_status),
            ("Selected lab case", snapshot.scenario),
            ("APS evaluation", snapshot.result_status),
        )
        facts_frame = tk.Frame(card, background=self.COLORS["card"])
        facts_frame.pack(fill="x", pady=(9, 6))
        for column in range(3):
            facts_frame.columnconfigure(column, weight=1, uniform="facts")
        for index, (label, value) in enumerate(facts):
            row, column = divmod(index, 3)
            block = tk.Frame(facts_frame, background=self.COLORS["card"])
            block.grid(
                row=row,
                column=column,
                sticky="nsew",
                padx=(0, 8),
                pady=(0 if row == 0 else 8, 0),
            )
            tk.Label(
                block,
                text=label,
                background=self.COLORS["card"],
                foreground=self.COLORS["muted"],
                font=("Segoe UI", 8),
            ).pack(anchor="w")
            bg, fg = _status_palette(value)
            tk.Label(
                block,
                text=value,
                background=bg,
                foreground=fg,
                font=("Segoe UI", 8, "bold"),
                padx=5,
                pady=2,
                wraplength=205,
                justify="left",
            ).pack(anchor="w", pady=(2, 0))

        tk.Label(
            card,
            text="Recommended next action: {}".format(snapshot.recommended_action),
            background=self.COLORS["green_soft"],
            foreground="#126143",
            font=("Segoe UI", 9, "bold"),
            padx=9,
            pady=6,
            anchor="w",
        ).pack(fill="x", pady=(4, 0))

    def _add_action(self, parent: Any, action: HubAction) -> None:
        """Add one workflow card and a project-aware launch button."""
        card = ttk.Frame(parent, style="Card.TFrame", padding=11)
        card.pack(fill="x", pady=4)
        card.columnconfigure(0, weight=1)
        ttk.Label(card, text=action.title, style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        badge_bg, badge_fg = _status_palette(action.badge)
        tk.Label(
            card,
            text=action.badge,
            background=badge_bg,
            foreground=badge_fg,
            font=("Segoe UI", 8, "bold"),
            padx=7,
            pady=3,
        ).grid(row=0, column=1, padx=(10, 0), sticky="e")
        ttk.Label(
            card,
            text=action.description,
            style="CardText.TLabel",
            wraplength=480,
            justify="left",
        ).grid(row=1, column=0, sticky="w", pady=(5, 0))
        button_text = action.button_label
        blocked = action.requires_disposable_project and not is_disposable_project(
            self.project_path
        )
        if blocked:
            button_text = "Disposable project required"
        button = ttk.Button(
            card,
            text=button_text,
            style="Hub.TButton",
            command=lambda item=action: self._launch(item),
        )
        button.grid(row=1, column=1, padx=(12, 0), sticky="e")
        if blocked:
            button.state(["disabled"])

    def _build_guardrail(self, parent: Any) -> None:
        """State the exact claim boundary in the interface itself."""
        box = tk.Frame(parent, background=self.COLORS["amber_soft"], padx=12, pady=9)
        box.pack(fill="x", pady=(16, 8))
        tk.Label(
            box,
            text="CLAIM BOUNDARY",
            background=self.COLORS["amber_soft"],
            foreground="#855600",
            font=("Segoe UI", 8, "bold"),
        ).pack(anchor="w")
        tk.Label(
            box,
            text=(
                "This workbench supports engineering pre-checks and software "
                "verification evidence. It does not issue SIA certification. "
                "PASS is shown only for an implemented control with traceable input; "
                "unresolved official criteria remain NOT CHECKABLE."
            ),
            background=self.COLORS["amber_soft"],
            foreground="#6f4b00",
            font=("Segoe UI", 8),
            wraplength=650,
            justify="left",
        ).pack(anchor="w", pady=(3, 0))

    def _build_footer(self) -> None:
        """Build persistent navigation controls outside the scroll area."""
        footer = tk.Frame(self.root, background=self.COLORS["canvas"], padx=14, pady=8)
        footer.pack(fill="x")
        ttk.Button(
            footer,
            text="Open project folder",
            style="Quiet.TButton",
            command=lambda: self._open_path(Path(self.project_path)),
        ).pack(side="left")
        ttk.Button(
            footer,
            text="Open presenter guide",
            style="Quiet.TButton",
            command=lambda: self._open_path(PRESENTER_GUIDE),
        ).pack(side="left", padx=(7, 0))
        ttk.Button(
            footer,
            text="Refresh status",
            style="Quiet.TButton",
            command=self._refresh,
        ).pack(side="left", padx=(7, 0))
        ttk.Button(footer, text="Close", command=self._close).pack(side="right")

    def _open_path(self, path: Path) -> None:
        """Open an existing local artifact through the Windows shell."""
        if not path.exists():
            if messagebox is not None:
                messagebox.showerror(
                    "Artifact unavailable",
                    "The requested path does not exist:\n{}".format(path),
                    parent=self.root,
                )
            return
        try:
            os.startfile(str(path))  # type: ignore[attr-defined]
        except OSError as exc:
            if messagebox is not None:
                messagebox.showerror(
                    "Unable to open artifact", str(exc), parent=self.root
                )

    def _refresh(self) -> None:
        """Rebuild the cockpit from fresh project-local evidence."""
        self.snapshot = build_project_snapshot(self.project_path)
        for child in self.root.winfo_children():
            child.destroy()
        self._build()

    def _launch(self, action: HubAction) -> None:
        """Apply disposable-project and explicit-confirmation guards."""
        if action.requires_disposable_project and not is_disposable_project(
            self.project_path
        ):
            if messagebox is not None:
                messagebox.showerror(
                    "Disposable project required",
                    "This workflow can change VE. Open a saved disposable copy whose "
                    "name ends in _TEST, _COPY or _DISPOSABLE.",
                    parent=self.root,
                )
            return
        if action.mutates_ve and messagebox is not None:
            confirmed = messagebox.askyesno(
                "Controlled VE operation",
                "Continue only in the saved disposable project shown above. The "
                "workflow remains fail-closed and may stop when a binding is not "
                "qualified. Run now?",
                parent=self.root,
            )
            if not confirmed:
                return
        launcher = action.launcher
        self._close()
        self.executor(launcher)
        if action.action_id == "navigator" and EVIDENCE_DASHBOARD.is_file():
            try:
                os.startfile(str(EVIDENCE_DASHBOARD))  # type: ignore[attr-defined]
            except OSError as exc:
                print("Evidence dashboard could not be opened: {}".format(exc))

    def run(self) -> None:
        """Enter the Tk event loop."""
        self._show_in_foreground()
        print(
            "SWISS COMPLIANCE WORKBENCH: WINDOW_OPEN - close the window or choose "
            "an action to complete this VEScripts run.",
            flush=True,
        )
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            try:
                self._close()
            except Exception:
                pass
            print("SWISS COMPLIANCE WORKBENCH: CLOSED_AFTER_USER_INTERRUPT", flush=True)


def launch_hub(
    project_path: str,
    capabilities: Dict[str, int],
    executor: Callable[[str], Any],
) -> None:
    """Create and display the native Swiss Compliance Workbench."""
    ComplianceHub(project_path, capabilities, executor).run()
