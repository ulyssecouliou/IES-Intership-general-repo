"""Tkinter editor for reviewer-owned, project-local SIA evidence."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .project_evidence import (
    FAMILIES,
    FIELD_CHOICES,
    empty_record,
    load_records,
    save_records,
)
from .project_evidence_translations import (
    family_help,
    family_title,
    field_label,
    text,
)
from .reference_model.sia4010.ui_translations import (
    LANGUAGE_LABELS,
    LANGUAGES,
    normalize_language,
)
from ui.tk_safe import bring_window_to_front

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError:  # pragma: no cover
    tk = messagebox = ttk = None


class ProjectEvidenceEditor:
    """Six-tab editor; acceptance is recalculated by the production validator."""

    def __init__(
        self,
        project_root: Path,
        project_label: str,
        weather_file: str = "",
        parent: Any = None,
        language: str = "en",
    ) -> None:
        if tk is None or ttk is None:
            raise RuntimeError("Tkinter is unavailable in this runtime.")
        self.project_root = Path(project_root)
        self.project_label = project_label
        self.weather_file = weather_file
        self.language = normalize_language(language)
        self.window = tk.Toplevel(parent) if parent is not None else tk.Tk()
        self.parent = parent
        self.window.protocol("WM_DELETE_WINDOW", self._close)
        self.window.geometry("1040x760")
        self.window.minsize(820, 620)
        self.records: Dict[str, List[Dict[str, str]]] = {}
        self.indices: Dict[str, int] = {}
        self.widgets: Dict[str, Dict[str, Any]] = {}
        self.counters: Dict[str, Any] = {}
        self.status = tk.StringVar(value=text("status_initial", self.language))
        self._build()

    def _build(self) -> None:
        for child in self.window.winfo_children():
            child.destroy()
        self.window.title(text("window_title", self.language))
        header = tk.Frame(self.window, bg="#0b2239", padx=24, pady=16)
        header.pack(fill="x")
        language_value = tk.StringVar(value=LANGUAGE_LABELS[self.language])
        language_box = ttk.Combobox(
            header,
            state="readonly",
            textvariable=language_value,
            values=tuple(LANGUAGE_LABELS[code] for code in LANGUAGES),
            width=13,
        )
        language_box.pack(side="right", anchor="ne")
        language_box.bind(
            "<<ComboboxSelected>>",
            lambda _event: self._change_language(language_value.get()),
        )
        tk.Label(
            header,
            text=text("eyebrow", self.language),
            bg="#0b2239",
            fg="#57bfd4",
            font=("Segoe UI Semibold", 9),
        ).pack(anchor="w")
        tk.Label(
            header,
            text=self.project_label,
            bg="#0b2239",
            fg="white",
            font=("Georgia", 18, "bold"),
        ).pack(anchor="w")
        tk.Label(
            header,
            text=text("intro", self.language),
            bg="#0b2239",
            fg="#d7e3eb",
            font=("Segoe UI", 9),
        ).pack(anchor="w", pady=(4, 0))
        notebook = ttk.Notebook(self.window)
        notebook.pack(fill="both", expand=True, padx=16, pady=14)
        for spec in FAMILIES:
            if spec.key not in self.records:
                self.records[spec.key] = load_records(
                    self.project_root, spec.key, self.project_label, self.weather_file
                )
                self.indices[spec.key] = 0
            tab = ttk.Frame(notebook, padding=14)
            notebook.add(tab, text=family_title(spec.key, self.language))
            ttk.Label(
                tab, text=family_help(spec.key, self.language), wraplength=930
            ).pack(anchor="w", pady=(0, 8))
            nav = ttk.Frame(tab)
            nav.pack(fill="x", pady=(0, 8))
            ttk.Button(
                nav,
                text=text("previous", self.language),
                command=lambda key=spec.key: self._move(key, -1),
            ).pack(side="left")
            ttk.Button(
                nav,
                text=text("next", self.language),
                command=lambda key=spec.key: self._move(key, 1),
            ).pack(side="left", padx=5)
            ttk.Button(
                nav,
                text=text("add", self.language),
                command=lambda key=spec.key: self._add(key),
            ).pack(side="left", padx=(12, 5))
            ttk.Button(
                nav,
                text=text("delete", self.language),
                command=lambda key=spec.key: self._delete(key),
            ).pack(side="left")
            self.counters[spec.key] = ttk.Label(nav, text="")
            self.counters[spec.key].pack(side="right")
            canvas = tk.Canvas(tab, highlightthickness=0)
            scrollbar = ttk.Scrollbar(tab, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)
            form = ttk.Frame(canvas, padding=(4, 2, 12, 8))
            form_window = canvas.create_window((0, 0), window=form, anchor="nw")
            form.bind(
                "<Configure>",
                lambda _event, c=canvas: c.configure(scrollregion=c.bbox("all")),
            )
            canvas.bind(
                "<Configure>",
                lambda event, c=canvas, item=form_window: c.itemconfigure(
                    item, width=event.width
                ),
            )
            self.widgets[spec.key] = {}
            for index, field in enumerate(spec.fields):
                row = ttk.Frame(form)
                row.pack(fill="x", pady=3)
                ttk.Label(row, text=field_label(field, self.language), width=34).pack(
                    side="left", anchor="n", pady=6
                )
                if field in FIELD_CHOICES:
                    widget = ttk.Combobox(
                        row, values=FIELD_CHOICES[field], state="readonly"
                    )
                else:
                    widget = ttk.Entry(row)
                widget.pack(side="left", fill="x", expand=True, ipady=5)
                if field == "project_id":
                    widget.configure(state="disabled")
                self.widgets[spec.key][field] = widget
            self._show(spec.key)
        footer = ttk.Frame(self.window, padding=(16, 0, 16, 14))
        footer.pack(fill="x")
        ttk.Label(footer, textvariable=self.status, wraplength=720).pack(
            side="left", fill="x", expand=True
        )
        ttk.Button(
            footer,
            text=text("save", self.language),
            command=lambda: self._save_current(notebook),
        ).pack(side="right")
        ttk.Button(
            footer,
            text=text("return_to_report", self.language),
            command=self._close,
        ).pack(side="right", padx=(0, 8))

    def _close(self) -> None:
        """Close the editor and explicitly restore its calling interface."""

        try:
            self.window.grab_release()
        except Exception:
            pass
        try:
            self.window.destroy()
        finally:
            if self.parent is not None:
                bring_window_to_front(self.parent)

    def _change_language(self, label: str) -> None:
        """Preserve unsaved values and rebuild every visible label immediately."""

        for key in tuple(self.records):
            self._capture(key)
        selected = next(
            (code for code, value in LANGUAGE_LABELS.items() if value == label),
            "en",
        )
        self.language = normalize_language(selected)
        self.status.set(text("status_initial", self.language))
        self._build()

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
        self.counters[key].configure(
            text=text(
                "row",
                self.language,
                current=self.indices[key] + 1,
                total=len(self.records[key]),
            )
        )

    def _move(self, key: str, delta: int) -> None:
        self._capture(key)
        self.indices[key] = max(
            0, min(len(self.records[key]) - 1, self.indices[key] + delta)
        )
        self._show(key)

    def _add(self, key: str) -> None:
        self._capture(key)
        self.records[key].append(empty_record(key, self.project_label, self.weather_file))
        self.indices[key] = len(self.records[key]) - 1
        self._show(key)

    def _delete(self, key: str) -> None:
        if len(self.records[key]) == 1:
            self.records[key][0] = empty_record(
                key, self.project_label, self.weather_file
            )
            self.indices[key] = 0
        else:
            self.records[key].pop(self.indices[key])
            self.indices[key] = min(self.indices[key], len(self.records[key]) - 1)
        self._show(key)

    def _save_current(self, notebook: Any) -> None:
        tab_index = notebook.index(notebook.select())
        key = FAMILIES[tab_index].key
        self._capture(key)
        result = save_records(
            self.project_root, key, self.project_label, self.records[key]
        )
        if result["forced_pending_count"]:
            message = text(
                "saved_pending", self.language, count=result["forced_pending_count"]
            )
        else:
            message = text(
                "saved_ok",
                self.language,
                rows=result["row_count"],
                accepted=result["accepted_count"],
            )
        self.status.set(message + "  " + result["path"])
        if messagebox is not None:
            messagebox.showinfo(
                text("dialog_title", self.language), message, parent=self.window
            )

    def run(self) -> None:
        self.window.mainloop()


def launch_project_evidence_editor(
    project_root: Path,
    project_label: str,
    weather_file: str = "",
    parent: Any = None,
    language: str = "en",
) -> ProjectEvidenceEditor:
    editor = ProjectEvidenceEditor(
        project_root, project_label, weather_file, parent, language
    )
    if parent is None:
        editor.run()
    else:
        editor.window.transient(parent)
        editor.window.grab_set()
        bring_window_to_front(editor.window)
        parent.wait_window(editor.window)
    return editor
