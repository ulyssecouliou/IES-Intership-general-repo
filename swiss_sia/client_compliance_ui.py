"""Native client-facing SIA 380/2 report interface for IESVE.

The window exposes only the building compliance conclusion and its domain
statuses.  Development metrics such as model-health and weighted readiness
scores deliberately stay out of this client workflow.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Callable, Dict, Optional

from .client_report_context import (
    ClientReportContext,
    load_client_report_context,
    report_directory,
    save_client_report_context,
)
from .pdf_writer import ImageError, load_image
from .reference_model.sia4010.ui_translations import (
    LANGUAGES,
    normalize_language,
    translate,
)

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
except ImportError:  # pragma: no cover - desktop Python provides Tkinter
    tk = filedialog = messagebox = ttk = None


RunAnalysis = Callable[[ClientReportContext, Path], Dict[str, Any]]


def compliance_palette(status: str) -> tuple[str, str, str]:
    """Return background, foreground and translation key for one verdict."""

    normalized = str(status or "NOT_DETERMINED").upper()
    if normalized == "COMPLIANT":
        return "#e7f6ef", "#126143", "verdict_compliant"
    if normalized == "NOT_COMPLIANT":
        return "#fdeaea", "#9b2c2c", "verdict_not_compliant"
    return "#fff4dc", "#855600", "verdict_not_determined"


def validate_client_context(context: ClientReportContext) -> Optional[str]:
    """Return a validation issue, or ``None`` when the form can be saved."""

    normalized = context.normalized()
    if not normalized.client_name or not normalized.project_name:
        return "client_and_project_required"
    for image_path in (
        normalized.client_logo_path,
        normalized.model_viewer_image_path,
    ):
        if not image_path:
            continue
        try:
            load_image(image_path)
        except (ImageError, OSError, ValueError):
            return "client_ui_image_error"
    return None


class ClientComplianceWindow:
    """Single-purpose client form, compliance view and report launcher."""

    COLORS = {
        "navy": "#102a43",
        "blue": "#1f5f99",
        "canvas": "#f3f6f9",
        "card": "#ffffff",
        "text": "#1f3349",
        "muted": "#617286",
        "line": "#d9e2ec",
        "green": "#14805e",
    }

    def __init__(
        self,
        project_path: str,
        weather_file: str,
        runner: RunAnalysis,
    ) -> None:
        if tk is None or ttk is None:
            raise RuntimeError("Tkinter is unavailable in this runtime.")
        self.project_path = Path(project_path)
        self.runner = runner
        saved = load_client_report_context(self.project_path)
        default_project = saved.project_name or self.project_path.name
        self.language = normalize_language(saved.language or "fr")
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.configure(background=self.COLORS["canvas"])
        self.root.minsize(780, 620)
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self.vars = {
            "client_name": tk.StringVar(value=saved.client_name),
            "project_name": tk.StringVar(value=default_project),
            "project_address": tk.StringVar(value=saved.project_address),
            "client_contact": tk.StringVar(value=saved.client_contact),
            "report_reference": tk.StringVar(value=saved.report_reference),
            "prepared_by": tk.StringVar(value=saved.prepared_by),
            "language": tk.StringVar(value=self.language),
            "weather_file": tk.StringVar(value=weather_file or saved.weather_file),
            "solar_shading": tk.StringVar(value=saved.solar_shading or "TO_CONFIRM"),
            "client_logo_path": tk.StringVar(value=saved.client_logo_path),
            "model_viewer_image_path": tk.StringVar(
                value=saved.model_viewer_image_path
            ),
        }
        self.result: Dict[str, Any] = {}
        self._configure_style()
        self._build()

    def t(self, key: str) -> str:
        """Translate one label using the shared live UI catalogue."""

        return translate(key, self.language)

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Client.TFrame", background=self.COLORS["canvas"])
        style.configure("ClientCard.TFrame", background=self.COLORS["card"])
        style.configure(
            "Client.TLabel",
            background=self.COLORS["card"],
            foreground=self.COLORS["text"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "ClientSection.TLabel",
            background=self.COLORS["card"],
            foreground=self.COLORS["navy"],
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "Client.TButton", padding=(12, 8), font=("Segoe UI", 9, "bold")
        )
        style.configure(
            "ClientPrimary.TButton",
            padding=(15, 10),
            font=("Segoe UI", 10, "bold"),
            foreground="#ffffff",
            background=self.COLORS["blue"],
        )
        style.map(
            "ClientPrimary.TButton",
            background=[("active", "#174b78"), ("disabled", "#93a4b5")],
        )

    def _build(self) -> None:
        self.root.title(self.t("client_ui_window_title"))
        banner = tk.Frame(self.root, background=self.COLORS["navy"], padx=22, pady=16)
        banner.pack(fill="x")
        tk.Label(
            banner,
            text=self.t("client_ui_header"),
            background=self.COLORS["navy"],
            foreground="#ffffff",
            font=("Segoe UI", 19, "bold"),
        ).pack(anchor="w")
        tk.Label(
            banner,
            text=self.t("client_ui_subtitle"),
            background=self.COLORS["navy"],
            foreground="#dce8f5",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(4, 0))

        container = ttk.Frame(self.root, style="Client.TFrame", padding=14)
        container.pack(fill="both", expand=True)
        self.form = ttk.Frame(container, style="ClientCard.TFrame", padding=16)
        self.form.pack(fill="x")
        for column in (1, 3):
            self.form.columnconfigure(column, weight=1)

        ttk.Label(
            self.form,
            text=self.t("client_ui_section_details").upper(),
            style="ClientSection.TLabel",
        ).grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 10))
        fields = (
            ("field_client", "client_name", 1, 0),
            ("client_ui_project_name", "project_name", 1, 2),
            ("field_project_address", "project_address", 2, 0),
            ("client_ui_contact", "client_contact", 2, 2),
            ("field_reference", "report_reference", 3, 0),
            ("client_ui_prepared_by", "prepared_by", 3, 2),
        )
        for key, variable, row, column in fields:
            ttk.Label(self.form, text=self.t(key), style="Client.TLabel").grid(
                row=row, column=column, sticky="w", padx=(0, 8), pady=5
            )
            ttk.Entry(self.form, textvariable=self.vars[variable]).grid(
                row=row, column=column + 1, sticky="ew", padx=(0, 14), pady=5
            )

        ttk.Label(self.form, text=self.t("language_label"), style="Client.TLabel").grid(
            row=4, column=0, sticky="w", padx=(0, 8), pady=5
        )
        language_box = ttk.Combobox(
            self.form,
            state="readonly",
            textvariable=self.vars["language"],
            values=LANGUAGES,
            width=8,
        )
        language_box.grid(row=4, column=1, sticky="w", pady=5)
        ttk.Label(
            self.form, text=self.t("client_ui_weather"), style="Client.TLabel"
        ).grid(row=4, column=2, sticky="w", padx=(0, 8), pady=5)
        weather = ttk.Entry(
            self.form, textvariable=self.vars["weather_file"], state="readonly"
        )
        weather.grid(row=4, column=3, sticky="ew", padx=(0, 14), pady=5)

        ttk.Separator(self.form).grid(
            row=5, column=0, columnspan=4, sticky="ew", pady=14
        )
        ttk.Label(
            self.form,
            text=self.t("client_ui_section_model").upper(),
            style="ClientSection.TLabel",
        ).grid(row=6, column=0, columnspan=4, sticky="w", pady=(0, 10))
        ttk.Label(self.form, text=self.t("client_ui_shading"), style="Client.TLabel").grid(
            row=7, column=0, sticky="w", pady=5
        )
        choice = tk.Frame(self.form, background=self.COLORS["card"])
        choice.grid(row=7, column=1, columnspan=3, sticky="w", pady=5)
        for value, key in (
            ("YES", "client_ui_yes"),
            ("NO", "client_ui_no"),
            ("TO_CONFIRM", "client_ui_to_confirm"),
        ):
            tk.Radiobutton(
                choice,
                text=self.t(key),
                variable=self.vars["solar_shading"],
                value=value,
                indicatoron=False,
                relief="flat",
                borderwidth=1,
                padx=13,
                pady=5,
                background="#edf1f5",
                activebackground="#dce8f5",
                selectcolor="#cfe1f3",
                font=("Segoe UI", 9, "bold"),
            ).pack(side="left", padx=(0, 6))

        self._asset_row(
            row=8,
            label_key="client_ui_logo",
            button_key="client_ui_choose_logo",
            variable="client_logo_path",
            chooser=self._choose_logo,
        )
        self._asset_row(
            row=9,
            label_key="client_ui_viewer",
            button_key="client_ui_choose_viewer",
            variable="model_viewer_image_path",
            chooser=self._choose_viewer,
        )
        ttk.Label(
            self.form,
            text=self.t("client_ui_viewer_hint"),
            style="Client.TLabel",
        ).grid(row=10, column=1, columnspan=3, sticky="w", pady=(0, 6))

        actions = ttk.Frame(container, style="Client.TFrame")
        actions.pack(fill="x", pady=(12, 0))
        self.status_text = tk.StringVar(value="")
        tk.Label(
            actions,
            textvariable=self.status_text,
            background=self.COLORS["canvas"],
            foreground=self.COLORS["muted"],
            font=("Segoe UI", 9),
        ).pack(side="left")
        self.generate_button = ttk.Button(
            actions,
            text=self.t("client_ui_generate"),
            style="ClientPrimary.TButton",
            command=self._generate,
        )
        self.generate_button.pack(side="right")

        self.result_panel = ttk.Frame(container, style="ClientCard.TFrame", padding=16)
        self.result_panel.pack(fill="both", expand=True, pady=(12, 0))
        ttk.Label(
            self.result_panel,
            text=self.t("client_ui_result").upper(),
            style="ClientSection.TLabel",
        ).pack(anchor="w")
        self.result_body = tk.Frame(self.result_panel, background=self.COLORS["card"])
        self.result_body.pack(fill="both", expand=True, pady=(10, 0))
        self._render_empty_result()

    def _asset_row(
        self,
        *,
        row: int,
        label_key: str,
        button_key: str,
        variable: str,
        chooser: Callable[[], None],
    ) -> None:
        ttk.Label(self.form, text=self.t(label_key), style="Client.TLabel").grid(
            row=row, column=0, sticky="w", pady=5
        )
        ttk.Button(
            self.form,
            text=self.t(button_key),
            style="Client.TButton",
            command=chooser,
        ).grid(row=row, column=1, sticky="w", pady=5)
        ttk.Label(
            self.form,
            textvariable=self.vars[variable],
            style="Client.TLabel",
        ).grid(row=row, column=2, columnspan=2, sticky="w", padx=(8, 0), pady=5)

    def _choose_image(self, title: str, target: str) -> None:
        if filedialog is None:
            return
        selected = filedialog.askopenfilename(
            title=title,
            filetypes=(("PNG / JPEG", "*.png *.jpg *.jpeg"), ("All files", "*.*")),
            parent=self.root,
        )
        if selected:
            self.vars[target].set(selected)

    def _choose_logo(self) -> None:
        self._choose_image(self.t("client_ui_choose_logo"), "client_logo_path")

    def _choose_viewer(self) -> None:
        self._choose_image(
            self.t("client_ui_choose_viewer"), "model_viewer_image_path"
        )

    def _context(self) -> ClientReportContext:
        return ClientReportContext(
            **{key: variable.get() for key, variable in self.vars.items()}
        ).normalized()

    def _render_empty_result(self) -> None:
        for child in self.result_body.winfo_children():
            child.destroy()
        tk.Label(
            self.result_body,
            text="—",
            background=self.COLORS["card"],
            foreground=self.COLORS["muted"],
            font=("Segoe UI", 24, "bold"),
        ).pack(anchor="w")

    def _render_result(self, result: Dict[str, Any]) -> None:
        for child in self.result_body.winfo_children():
            child.destroy()
        status = str(result.get("verdict_status") or "NOT_DETERMINED").upper()
        background, foreground, key = compliance_palette(status)
        verdict = tk.Frame(self.result_body, background=background, padx=16, pady=12)
        verdict.pack(fill="x")
        tk.Label(
            verdict,
            text=self.t(key),
            background=background,
            foreground=foreground,
            font=("Segoe UI", 17, "bold"),
        ).pack(side="left")
        counts = "{} / {}".format(
            result.get("blocking_total", 0), result.get("advisory_total", 0)
        )
        tk.Label(
            verdict,
            text=counts,
            background=background,
            foreground=foreground,
            font=("Segoe UI", 11, "bold"),
        ).pack(side="right")

        domains = tk.Frame(self.result_body, background=self.COLORS["card"])
        domains.pack(fill="x", pady=(10, 4))
        for column in range(3):
            domains.columnconfigure(column, weight=1, uniform="domains")
        for index, item in enumerate(result.get("domains") or []):
            domain_status = str(item.get("status") or "NOT_DETERMINED")
            bg, fg, domain_key = compliance_palette(domain_status)
            card = tk.Frame(domains, background=bg, padx=9, pady=7)
            card.grid(
                row=index // 3,
                column=index % 3,
                sticky="nsew",
                padx=(0 if index % 3 == 0 else 5, 0),
                pady=(0, 5),
            )
            tk.Label(
                card,
                text=self.t("domain_" + str(item.get("domain") or "")).upper(),
                background=bg,
                foreground=self.COLORS["text"],
                font=("Segoe UI", 8, "bold"),
            ).pack(anchor="w")
            tk.Label(
                card,
                text=self.t(domain_key),
                background=bg,
                foreground=fg,
                font=("Segoe UI", 10, "bold"),
            ).pack(anchor="w", pady=(2, 0))

        buttons = tk.Frame(self.result_body, background=self.COLORS["card"])
        buttons.pack(fill="x", pady=(8, 0))
        for key, path_key in (
            ("client_ui_open_excel", "excel_path"),
            ("client_ui_open_pdf", "pdf_path"),
            ("client_ui_open_folder", "report_directory"),
        ):
            path = result.get(path_key)
            ttk.Button(
                buttons,
                text=self.t(key),
                style="Client.TButton",
                command=lambda selected=path: self._open_path(selected),
            ).pack(side="left", padx=(0, 8))

    def _generate(self) -> None:
        context = self._context()
        issue = validate_client_context(context)
        if issue:
            if messagebox is not None:
                messagebox.showwarning(
                    self.t("client_ui_header"),
                    self.t(
                        "client_ui_image_error"
                        if issue == "client_ui_image_error"
                        else "client_ui_required"
                    ),
                    parent=self.root,
                )
            return
        self.language = context.language
        self.generate_button.state(["disabled"])
        self.status_text.set(self.t("client_ui_generating"))
        self.root.configure(cursor="watch")
        self.root.update_idletasks()
        try:
            stored = save_client_report_context(self.project_path, context)
            result = self.runner(stored, report_directory(self.project_path))
            self.result = dict(result or {})
            self._render_result(self.result)
            self.status_text.set(str(self.result.get("message") or ""))
            # A report action should lead to the document, not just save it.
            self._open_path(self.result.get("pdf_path"))
        except Exception as exc:
            self.status_text.set("")
            if messagebox is not None:
                messagebox.showerror(
                    self.t("client_ui_header"), str(exc), parent=self.root
                )
        finally:
            self.root.configure(cursor="")
            self.generate_button.state(["!disabled"])

    def _open_path(self, value: Any) -> None:
        if not value:
            return
        path = Path(str(value))
        if not path.exists():
            if messagebox is not None:
                messagebox.showerror(
                    self.t("client_ui_header"), str(path), parent=self.root
                )
            return
        try:
            os.startfile(str(path))  # type: ignore[attr-defined]
        except OSError as exc:
            if messagebox is not None:
                messagebox.showerror(
                    self.t("client_ui_header"), str(exc), parent=self.root
                )

    def _close(self) -> None:
        try:
            self.root.quit()
        finally:
            self.root.destroy()

    def run(self) -> None:
        self.root.update_idletasks()
        width = min(1050, max(780, self.root.winfo_screenwidth() - 100))
        height = min(820, max(620, self.root.winfo_screenheight() - 120))
        x = max(0, (self.root.winfo_screenwidth() - width) // 2)
        y = max(0, (self.root.winfo_screenheight() - height) // 2)
        self.root.geometry("{}x{}+{}+{}".format(width, height, x, y))
        self.root.deiconify()
        self.root.lift()
        try:
            self.root.attributes("-topmost", True)
            self.root.after(700, lambda: self.root.attributes("-topmost", False))
        except tk.TclError:
            pass
        self.root.mainloop()


def launch_client_compliance_ui(
    project_path: str, weather_file: str, runner: RunAnalysis
) -> None:
    """Open the client report interface for the active VE project."""

    ClientComplianceWindow(project_path, weather_file, runner).run()
