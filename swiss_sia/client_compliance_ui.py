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
CaptureModelViewer = Callable[[Path], Path]


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
        "navy": "#0b2239",
        "navy_soft": "#153a59",
        "blue": "#246ca6",
        "accent": "#57bfd4",
        "canvas": "#f3f1ec",
        "paper": "#fbfaf7",
        "card": "#ffffff",
        "text": "#172b3d",
        "muted": "#657584",
        "line": "#d9e0e5",
        "green": "#16745b",
        "chip": "#e8eef3",
    }

    def __init__(
        self,
        project_path: str,
        weather_file: str,
        runner: RunAnalysis,
        capture_model_viewer: Optional[CaptureModelViewer] = None,
    ) -> None:
        if tk is None or ttk is None:
            raise RuntimeError("Tkinter is unavailable in this runtime.")
        self.project_path = Path(project_path)
        self.runner = runner
        self.capture_model_viewer = capture_model_viewer
        saved = load_client_report_context(self.project_path)
        default_project = saved.project_name or self.project_path.name
        self.language = normalize_language(saved.language or "fr")
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.configure(background=self.COLORS["canvas"])
        self.root.minsize(1020, 700)
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
        """Translate one label and never expose an internal translation key."""

        label = translate(key, self.language)
        if label != key:
            return label
        # A partially updated live IESVE session can keep an older translation
        # catalogue in memory.  The UI must still show a human label rather than
        # leaking implementation names such as ``client_ui_shading``.
        readable = str(key or "").strip()
        for prefix in ("client_ui_", "field_", "domain_", "verdict_"):
            if readable.startswith(prefix):
                readable = readable[len(prefix):]
                break
        return readable.replace("_", " ").strip().capitalize() or "-"

    def _configure_style(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Client.TFrame", background=self.COLORS["canvas"])
        style.configure("ClientCard.TFrame", background=self.COLORS["card"])
        style.configure("ClientPaper.TFrame", background=self.COLORS["paper"])
        style.configure(
            "Client.TLabel",
            background=self.COLORS["card"],
            foreground=self.COLORS["text"],
            font=("Segoe UI", 9),
        )
        style.configure(
            "ClientMuted.TLabel",
            background=self.COLORS["card"],
            foreground=self.COLORS["muted"],
            font=("Segoe UI", 8),
        )
        style.configure(
            "ClientSection.TLabel",
            background=self.COLORS["card"],
            foreground=self.COLORS["navy"],
            font=("Segoe UI Semibold", 11),
        )
        style.configure(
            "Client.TEntry",
            padding=(9, 8),
            fieldbackground="#ffffff",
            foreground=self.COLORS["text"],
            bordercolor=self.COLORS["line"],
            lightcolor=self.COLORS["line"],
            darkcolor=self.COLORS["line"],
        )
        style.configure(
            "Client.TButton",
            padding=(12, 8),
            font=("Segoe UI Semibold", 9),
            foreground=self.COLORS["navy"],
            background="#eef2f5",
        )
        style.map("Client.TButton", background=[("active", "#dfe8ee")])
        style.configure(
            "ClientPrimary.TButton",
            padding=(18, 12),
            font=("Segoe UI Semibold", 10),
            foreground="#ffffff",
            background=self.COLORS["blue"],
        )
        style.map(
            "ClientPrimary.TButton",
            background=[("active", "#174b78"), ("disabled", "#93a4b5")],
        )

    def _build(self) -> None:
        self.root.title(self.t("client_ui_window_title"))
        banner = tk.Frame(self.root, background=self.COLORS["navy"], padx=30, pady=20)
        banner.pack(fill="x")
        heading = tk.Frame(banner, background=self.COLORS["navy"])
        heading.pack(fill="x")
        title_block = tk.Frame(heading, background=self.COLORS["navy"])
        title_block.pack(side="left", fill="x", expand=True)
        tk.Label(
            title_block,
            text=self.t("client_ui_eyebrow").upper(),
            background=self.COLORS["navy"],
            foreground=self.COLORS["accent"],
            font=("Segoe UI Semibold", 8),
        ).pack(anchor="w")
        tk.Label(
            title_block,
            text=self.t("client_ui_header"),
            background=self.COLORS["navy"],
            foreground="#ffffff",
            font=("Georgia", 22, "bold"),
        ).pack(anchor="w")
        tk.Label(
            title_block,
            text=self.t("client_ui_subtitle"),
            background=self.COLORS["navy"],
            foreground="#d7e3eb",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(5, 0))
        tk.Label(
            heading,
            text="SIA 380/2  /  CLIENT",
            background=self.COLORS["navy_soft"],
            foreground="#ffffff",
            padx=13,
            pady=8,
            font=("Consolas", 9, "bold"),
        ).pack(side="right", anchor="n", padx=(24, 0))

        metadata = tk.Frame(self.root, background=self.COLORS["navy_soft"], padx=30, pady=9)
        metadata.pack(fill="x")
        output_location = str(report_directory(self.project_path))
        if len(output_location) > 58:
            output_location = "..." + output_location[-55:]
        weather_label = self.vars["weather_file"].get() or self.t("value_unavailable")
        if len(weather_label) > 48:
            weather_label = "..." + weather_label[-45:]
        meta_items = (
            ("client_ui_active_project", self.project_path.name),
            ("client_ui_weather_short", weather_label),
            ("client_ui_output_short", output_location),
        )
        for index, (label_key, value) in enumerate(meta_items):
            block = tk.Frame(metadata, background=self.COLORS["navy_soft"])
            block.pack(side="left", fill="x", expand=True, padx=(0, 24 if index < 2 else 0))
            tk.Label(
                block, text=self.t(label_key).upper(),
                background=self.COLORS["navy_soft"], foreground="#8fb0c8",
                font=("Segoe UI Semibold", 7),
            ).pack(anchor="w")
            tk.Label(
                block, text=value, background=self.COLORS["navy_soft"],
                foreground="#ffffff", font=("Segoe UI", 8), anchor="w",
            ).pack(anchor="w")

        container = ttk.Frame(self.root, style="Client.TFrame", padding=(22, 18))
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=7, uniform="workspace")
        container.columnconfigure(1, weight=5, uniform="workspace")
        container.rowconfigure(0, weight=1)

        left_border = tk.Frame(
            container, background=self.COLORS["card"], highlightthickness=1,
            highlightbackground=self.COLORS["line"],
        )
        left_border.grid(row=0, column=0, sticky="nsew", padx=(0, 9))
        form_canvas = tk.Canvas(
            left_border,
            background=self.COLORS["card"],
            borderwidth=0,
            highlightthickness=0,
        )
        form_scroll = ttk.Scrollbar(
            left_border, orient="vertical", command=form_canvas.yview
        )
        form_canvas.configure(yscrollcommand=form_scroll.set)
        form_scroll.pack(side="right", fill="y")
        form_canvas.pack(side="left", fill="both", expand=True)
        self.form = ttk.Frame(form_canvas, style="ClientCard.TFrame", padding=20)
        form_window = form_canvas.create_window((0, 0), window=self.form, anchor="nw")
        self.form.bind(
            "<Configure>",
            lambda _event: form_canvas.configure(scrollregion=form_canvas.bbox("all")),
        )
        form_canvas.bind(
            "<Configure>",
            lambda event: form_canvas.itemconfigure(form_window, width=event.width),
        )

        def _scroll_form(event: Any) -> None:
            form_canvas.yview_scroll(int(-event.delta / 120), "units")

        form_canvas.bind(
            "<Enter>", lambda _event: self.root.bind_all("<MouseWheel>", _scroll_form)
        )
        form_canvas.bind(
            "<Leave>", lambda _event: self.root.unbind_all("<MouseWheel>")
        )
        for column in (0, 1):
            self.form.columnconfigure(column, weight=1, uniform="fields")

        self._section_heading(self.form, 0, "01", "client_ui_section_details")
        fields = (
            ("client_ui_client_name", "client_name", 1, 0),
            ("client_ui_project_name_required", "project_name", 1, 1),
            ("client_ui_project_address", "project_address", 2, 0),
            ("client_ui_contact_details", "client_contact", 2, 1),
            ("client_ui_report_reference", "report_reference", 3, 0),
            ("client_ui_prepared_by", "prepared_by", 3, 1),
        )
        for key, variable, row, column in fields:
            field = tk.Frame(self.form, background=self.COLORS["card"])
            field.grid(row=row, column=column, sticky="ew", padx=(0, 10 if column == 0 else 0), pady=(0, 10))
            tk.Label(
                field, text=self.t(key), background=self.COLORS["card"],
                foreground=self.COLORS["text"], font=("Segoe UI Semibold", 8),
            ).pack(anchor="w", pady=(0, 4))
            ttk.Entry(field, textvariable=self.vars[variable], style="Client.TEntry").pack(fill="x")

        locale_row = tk.Frame(self.form, background=self.COLORS["card"])
        locale_row.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 13))
        locale_row.columnconfigure(1, weight=1)
        tk.Label(
            locale_row, text=self.t("client_ui_report_language"),
            background=self.COLORS["card"], foreground=self.COLORS["text"],
            font=("Segoe UI Semibold", 8),
        ).grid(row=0, column=0, sticky="w", pady=(0, 4))
        language_box = ttk.Combobox(
            locale_row,
            state="readonly",
            textvariable=self.vars["language"],
            values=LANGUAGES,
            width=6,
        )
        language_box.grid(row=1, column=0, sticky="w")
        tk.Label(
            locale_row, text=self.t("client_ui_weather_detected"),
            background=self.COLORS["card"], foreground=self.COLORS["text"],
            font=("Segoe UI Semibold", 8),
        ).grid(row=0, column=1, sticky="w", padx=(18, 0), pady=(0, 4))
        weather = ttk.Entry(
            locale_row, textvariable=self.vars["weather_file"], state="readonly",
            style="Client.TEntry",
        )
        weather.grid(row=1, column=1, sticky="ew", padx=(18, 0))

        self._section_heading(self.form, 5, "02", "client_ui_section_model")
        shading = tk.Frame(self.form, background=self.COLORS["paper"], padx=12, pady=10)
        shading.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 10))
        tk.Label(
            shading, text=self.t("client_ui_shading_question"),
            background=self.COLORS["paper"], foreground=self.COLORS["text"],
            font=("Segoe UI Semibold", 9),
        ).pack(anchor="w")
        tk.Label(
            shading, text=self.t("client_ui_shading_help"),
            background=self.COLORS["paper"], foreground=self.COLORS["muted"],
            font=("Segoe UI", 8),
        ).pack(anchor="w", pady=(2, 7))
        choice = tk.Frame(shading, background=self.COLORS["paper"])
        choice.pack(anchor="w")
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
                padx=15,
                pady=6,
                background=self.COLORS["chip"],
                activebackground="#d8e6ef",
                selectcolor="#c7e5ed",
                font=("Segoe UI Semibold", 9),
            ).pack(side="left", padx=(0, 6))

        self._asset_row(
            row=7,
            label_key="client_ui_logo_report",
            button_key="client_ui_choose_logo",
            variable="client_logo_path",
            chooser=self._choose_logo,
        )
        self._viewer_asset_row(row=8)
        ttk.Label(
            self.form,
            text=self.t("client_ui_viewer_hint"),
            style="ClientMuted.TLabel",
            wraplength=570,
        ).grid(row=9, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.status_text = tk.StringVar(value="")
        tk.Label(
            self.form,
            textvariable=self.status_text,
            background=self.COLORS["card"],
            foreground=self.COLORS["muted"],
            font=("Segoe UI", 9),
        ).grid(row=10, column=0, sticky="w")
        self.generate_button = ttk.Button(
            self.form,
            text=self.t("client_ui_generate"),
            style="ClientPrimary.TButton",
            command=self._generate,
        )
        self.generate_button.grid(row=10, column=1, sticky="e")

        right_border = tk.Frame(
            container, background=self.COLORS["card"], highlightthickness=1,
            highlightbackground=self.COLORS["line"],
        )
        right_border.grid(row=0, column=1, sticky="nsew", padx=(9, 0))
        self.result_panel = ttk.Frame(right_border, style="ClientCard.TFrame", padding=20)
        self.result_panel.pack(fill="both", expand=True)
        self._section_heading(self.result_panel, 0, "03", "client_ui_result", pack=True)
        self.result_body = tk.Frame(self.result_panel, background=self.COLORS["card"])
        self.result_body.pack(fill="both", expand=True, pady=(13, 0))
        self._render_empty_result()

    def _section_heading(
        self, parent: Any, row: int, number: str, key: str, pack: bool = False
    ) -> None:
        """Draw one numbered document-style section heading."""

        heading = tk.Frame(parent, background=self.COLORS["card"])
        if pack:
            heading.pack(fill="x")
        else:
            heading.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 12))
        tk.Label(
            heading, text=number, background=self.COLORS["navy"], foreground="#ffffff",
            padx=7, pady=4, font=("Consolas", 8, "bold"),
        ).pack(side="left")
        tk.Label(
            heading, text=self.t(key).upper(), background=self.COLORS["card"],
            foreground=self.COLORS["navy"], font=("Segoe UI Semibold", 10),
        ).pack(side="left", padx=(9, 0))
        tk.Frame(heading, height=1, background=self.COLORS["line"]).pack(
            side="left", fill="x", expand=True, padx=(10, 0)
        )

    def _asset_row(
        self,
        *,
        row: int,
        label_key: str,
        button_key: str,
        variable: str,
        chooser: Callable[[], None],
    ) -> None:
        box = tk.Frame(self.form, background=self.COLORS["paper"], padx=12, pady=9)
        box.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        box.columnconfigure(1, weight=1)
        tk.Label(
            box, text=self.t(label_key), background=self.COLORS["paper"],
            foreground=self.COLORS["text"], font=("Segoe UI Semibold", 8),
        ).grid(row=0, column=0, sticky="w")
        ttk.Label(
            box, textvariable=self.vars[variable], style="ClientMuted.TLabel",
            background=self.COLORS["paper"],
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))
        ttk.Button(
            box,
            text=self.t(button_key),
            style="Client.TButton",
            command=chooser,
        ).grid(row=0, column=1, sticky="e", padx=(12, 0))

    def _viewer_asset_row(self, row: int) -> None:
        """Draw automatic capture plus manual-file fallback for Model Viewer."""

        box = tk.Frame(self.form, background=self.COLORS["paper"], padx=12, pady=9)
        box.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 5))
        box.columnconfigure(0, weight=1)
        tk.Label(
            box, text=self.t("client_ui_viewer_report"),
            background=self.COLORS["paper"], foreground=self.COLORS["text"],
            font=("Segoe UI Semibold", 8),
        ).grid(row=0, column=0, sticky="w")
        actions = tk.Frame(box, background=self.COLORS["paper"])
        actions.grid(row=0, column=1, sticky="e", padx=(12, 0))
        ttk.Button(
            actions,
            text=self.t("client_ui_capture_viewer"),
            style="Client.TButton",
            command=self._capture_viewer,
        ).pack(side="left", padx=(0, 6))
        ttk.Button(
            actions,
            text=self.t("client_ui_choose_viewer"),
            style="Client.TButton",
            command=self._choose_viewer,
        ).pack(side="left")
        tk.Label(
            box,
            textvariable=self.vars["model_viewer_image_path"],
            background=self.COLORS["paper"], foreground=self.COLORS["muted"],
            font=("Segoe UI", 8), wraplength=440,
        ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(5, 0))

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

    def _capture_viewer(self) -> None:
        """Capture the active VE Model Viewer and select the resulting image."""

        if self.capture_model_viewer is None:
            if messagebox is not None:
                messagebox.showinfo(
                    self.t("client_ui_viewer"),
                    self.t("client_ui_capture_unavailable"),
                    parent=self.root,
                )
            return
        self.status_text.set(self.t("client_ui_capturing_viewer"))
        self.root.update_idletasks()
        try:
            image_path = self.capture_model_viewer(self.project_path)
            self.vars["model_viewer_image_path"].set(str(image_path))
            self.status_text.set(self.t("client_ui_capture_done"))
        except Exception as exc:
            self.status_text.set("")
            if messagebox is not None:
                messagebox.showerror(
                    self.t("client_ui_viewer"),
                    "{}\n\n{}".format(self.t("client_ui_capture_failed"), exc),
                    parent=self.root,
                )

    def _context(self) -> ClientReportContext:
        return ClientReportContext(
            **{key: variable.get() for key, variable in self.vars.items()}
        ).normalized()

    def _render_empty_result(self) -> None:
        for child in self.result_body.winfo_children():
            child.destroy()
        placeholder = tk.Frame(
            self.result_body,
            background=self.COLORS["paper"],
            padx=20,
            pady=20,
        )
        placeholder.pack(fill="x")
        tk.Label(
            placeholder,
            text="SIA 380/2",
            background=self.COLORS["paper"],
            foreground=self.COLORS["blue"],
            font=("Consolas", 9, "bold"),
        ).pack(anchor="w")
        tk.Label(
            placeholder,
            text=self.t("client_ui_result_pending"),
            background=self.COLORS["paper"],
            foreground=self.COLORS["text"],
            font=("Georgia", 16, "bold"),
        ).pack(anchor="w", pady=(7, 4))
        tk.Label(
            placeholder,
            text=self.t("client_ui_result_pending_help"),
            background=self.COLORS["paper"],
            foreground=self.COLORS["muted"],
            font=("Segoe UI", 9),
            justify="left",
            wraplength=370,
        ).pack(anchor="w")

        checklist = tk.Frame(self.result_body, background=self.COLORS["card"])
        checklist.pack(fill="x", pady=(18, 0))
        for number, key in (
            ("1", "client_ui_check_client"),
            ("2", "client_ui_check_model"),
            ("3", "client_ui_check_generate"),
        ):
            row = tk.Frame(checklist, background=self.COLORS["card"])
            row.pack(fill="x", pady=(0, 10))
            tk.Label(
                row, text=number, background=self.COLORS["chip"],
                foreground=self.COLORS["navy"], width=2, pady=3,
                font=("Consolas", 8, "bold"),
            ).pack(side="left")
            tk.Label(
                row, text=self.t(key), background=self.COLORS["card"],
                foreground=self.COLORS["muted"], font=("Segoe UI", 9),
            ).pack(side="left", padx=(9, 0))

    def _render_result(self, result: Dict[str, Any]) -> None:
        for child in self.result_body.winfo_children():
            child.destroy()
        status = str(result.get("verdict_status") or "NOT_DETERMINED").upper()
        background, foreground, key = compliance_palette(status)
        verdict = tk.Frame(self.result_body, background=background, padx=18, pady=15)
        verdict.pack(fill="x")
        tk.Label(
            verdict,
            text=self.t("client_ui_decision").upper(),
            background=background,
            foreground=foreground,
            font=("Segoe UI Semibold", 7),
        ).pack(anchor="w")
        tk.Label(
            verdict,
            text=self.t(key),
            background=background,
            foreground=foreground,
            font=("Georgia", 18, "bold"),
        ).pack(anchor="w", pady=(3, 0))

        counters = tk.Frame(self.result_body, background=self.COLORS["card"])
        counters.pack(fill="x", pady=(11, 3))
        counter_items = (
            (result.get("blocking_total", 0), "client_ui_blocking_findings", "#9b2c2c"),
            (result.get("advisory_total", 0), "client_ui_advisory_findings", self.COLORS["blue"]),
        )
        for index, (value, label_key, colour) in enumerate(counter_items):
            card = tk.Frame(counters, background=self.COLORS["paper"], padx=11, pady=8)
            card.pack(side="left", fill="x", expand=True, padx=(0, 5 if index == 0 else 0))
            tk.Label(
                card, text=str(value), background=self.COLORS["paper"],
                foreground=colour, font=("Georgia", 16, "bold"),
            ).pack(anchor="w")
            tk.Label(
                card, text=self.t(label_key), background=self.COLORS["paper"],
                foreground=self.COLORS["muted"], font=("Segoe UI", 8),
            ).pack(anchor="w")

        domains = tk.Frame(self.result_body, background=self.COLORS["card"])
        domains.pack(fill="x", pady=(9, 4))
        for column in range(2):
            domains.columnconfigure(column, weight=1, uniform="domains")
        for index, item in enumerate(result.get("domains") or []):
            domain_status = str(item.get("status") or "NOT_DETERMINED")
            bg, fg, domain_key = compliance_palette(domain_status)
            card = tk.Frame(domains, background=bg, padx=9, pady=7)
            card.grid(
                row=index // 2,
                column=index % 2,
                sticky="nsew",
                padx=(0 if index % 2 == 0 else 5, 0),
                pady=(0, 5),
            )
            tk.Label(
                card,
                text=self.t("domain_" + str(item.get("domain") or "")).upper(),
                background=bg,
                foreground=self.COLORS["text"],
                font=("Segoe UI Semibold", 8),
            ).pack(anchor="w")
            tk.Label(
                card,
                text=self.t(domain_key),
                background=bg,
                foreground=fg,
                font=("Segoe UI Semibold", 9),
            ).pack(anchor="w", pady=(2, 0))

        ttk.Label(
            self.result_body,
            text=self.t("client_ui_current_reports").upper(),
            style="ClientSection.TLabel",
        ).pack(anchor="w", pady=(8, 4))
        buttons = tk.Frame(self.result_body, background=self.COLORS["card"])
        buttons.pack(fill="x")
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
            # Open the exact timestamped deliverables from this run. Excel is
            # launched first, then the PDF, so neither button can accidentally
            # lead the user to a stale "latest" alias from an earlier run.
            self._open_current_reports()
        except Exception as exc:
            self.status_text.set("")
            if messagebox is not None:
                messagebox.showerror(
                    self.t("client_ui_header"), str(exc), parent=self.root
                )
        finally:
            self.root.configure(cursor="")
            self.generate_button.state(["!disabled"])

    def _open_current_reports(self) -> None:
        """Open the Excel and PDF deliverables produced by the current run."""

        for key in ("excel_path", "pdf_path"):
            self._open_path(self.result.get(key))

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
        width = min(1240, max(1020, self.root.winfo_screenwidth() - 90))
        height = min(860, max(700, self.root.winfo_screenheight() - 100))
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
    project_path: str,
    weather_file: str,
    runner: RunAnalysis,
    capture_model_viewer: Optional[CaptureModelViewer] = None,
) -> None:
    """Open the client report interface for the active VE project."""

    ClientComplianceWindow(
        project_path,
        weather_file,
        runner,
        capture_model_viewer=capture_model_viewer,
    ).run()
