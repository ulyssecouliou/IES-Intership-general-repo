"""English VEScripts UI for guarded client thermal-template remediation."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .client_template_remediation import (
    ClientTemplateRemediationError,
    apply_preview_plan,
    automatic_template_evidence,
    build_preview_plan,
    collect_inventory,
    write_json_artifact,
)
from .reference_model.sia4010.ui_translations import normalize_language, translate

try:
    import tkinter as tk
    from tkinter import messagebox, ttk
except ImportError:  # pragma: no cover - VE provides tkinter
    tk = None
    ttk = None
    messagebox = None


NAVY = "#1A2B4B"
BLUE = "#0F54E8"
PALE_BLUE = "#E8F1FB"
LIGHT = "#F5F7F9"
WHITE = "#FFFFFF"
TEXT = "#28384D"
MUTED = "#66758A"
AMBER = "#B86A00"
GREEN = "#0A7D63"
RED = "#B42318"


class ClientTemplateRemediationUI:
    """Preview and apply one checksum-bound template assignment plan."""

    def __init__(
        self,
        iesve_module: Any,
        project: Any,
        model: Any,
        project_path: str,
    ) -> None:
        if tk is None:
            raise RuntimeError("tkinter is unavailable in this VE runtime")
        self.iesve = iesve_module
        self.project = project
        self.model = model
        self.project_path = str(Path(project_path).resolve())
        self.project_name = str(getattr(project, "name", "") or Path(project_path).name)
        self.language = normalize_language(
            os.environ.get("SWISS_SIA_UI_LANGUAGE", "en")
        )
        self.inventory = collect_inventory(project, model)
        self.plan: Optional[Dict[str, Any]] = None
        self.plan_path: Optional[Path] = None
        self.preview_signature: Optional[Tuple[Any, ...]] = None

        self.root = tk.Tk()
        self.root.title("IES Swiss Compliance - Approved Template Remediation")
        self.root.geometry("1100x760")
        self.root.minsize(850, 600)
        self.root.configure(background=LIGHT)
        self.root.protocol("WM_DELETE_WINDOW", self._close)
        self._configure_styles()
        self._build()

    def _t(self, key: str) -> str:
        """Return one shared-catalogue UI message for the configured language."""

        return translate(key, self.language)

    def _configure_styles(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Page.TFrame", background=LIGHT)
        style.configure("Card.TFrame", background=WHITE)
        style.configure("Header.TFrame", background=NAVY)
        style.configure(
            "Header.TLabel",
            background=NAVY,
            foreground=WHITE,
            font=("Segoe UI", 16, "bold"),
        )
        style.configure(
            "HeaderSub.TLabel",
            background=NAVY,
            foreground=PALE_BLUE,
            font=("Segoe UI", 9),
        )
        style.configure(
            "Section.TLabel",
            background=WHITE,
            foreground=NAVY,
            font=("Segoe UI", 11, "bold"),
        )
        style.configure(
            "Body.TLabel", background=WHITE, foreground=TEXT, font=("Segoe UI", 9)
        )
        style.configure(
            "Help.TLabel", background=WHITE, foreground=MUTED, font=("Segoe UI", 8)
        )
        style.configure(
            "Primary.TButton",
            background=BLUE,
            foreground=WHITE,
            font=("Segoe UI", 9, "bold"),
            padding=(12, 7),
        )
        style.configure("Secondary.TButton", padding=(12, 7))
        style.configure("Body.TCheckbutton", background=WHITE, foreground=TEXT)

    def _build(self) -> None:
        header = ttk.Frame(self.root, style="Header.TFrame", padding=(18, 12))
        header.pack(fill="x")
        ttk.Label(
            header,
            style="Header.TLabel",
            text="SIA 380/2 - Approved Thermal Template Remediation",
        ).pack(anchor="w")
        ttk.Label(
            header,
            style="HeaderSub.TLabel",
            text="Active project copy: {}".format(self.project_path),
        ).pack(anchor="w", pady=(3, 0))
        ttk.Label(
            header,
            style="HeaderSub.TLabel",
            wraplength=1020,
            text=(
                "The script never creates regulatory values. It assigns an existing, "
                "reviewed VE template to explicitly selected rooms, verifies VE "
                "read-back, and grants no automatic compliance verdict."
            ),
        ).pack(anchor="w", pady=(6, 0))

        outer = ttk.Frame(self.root, style="Page.TFrame", padding=10)
        outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(
            outer, background=WHITE, highlightbackground="#D8DEE8", highlightthickness=1
        )
        scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        self.content = ttk.Frame(canvas, style="Card.TFrame", padding=16)
        window = canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.content.bind(
            "<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        canvas.bind(
            "<Configure>", lambda event: canvas.itemconfigure(window, width=event.width)
        )
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind_all(
            "<MouseWheel>",
            lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"),
        )

        self._build_selection()
        self._build_evidence()
        self._build_preview()
        self._build_actions()

    def _build_selection(self) -> None:
        ttk.Label(
            self.content, style="Section.TLabel", text="1. Select reviewed template"
        ).pack(anchor="w")
        template_names = [row["name"] for row in self.inventory["templates"]]
        self.template_var = tk.StringVar(value="")
        self.template_combo = ttk.Combobox(
            self.content,
            textvariable=self.template_var,
            values=template_names,
            state="readonly",
            width=70,
        )
        self.template_combo.pack(anchor="w", pady=(6, 2))
        self.template_combo.bind("<<ComboboxSelected>>", self._invalidate_preview)
        ttk.Label(
            self.content,
            style="Help.TLabel",
            text="Only templates already present in the active VE project are listed.",
        ).pack(anchor="w", pady=(0, 12))

        ttk.Label(
            self.content, style="Section.TLabel", text="2. Select target rooms explicitly"
        ).pack(anchor="w")
        self.rooms = list(self.inventory["rooms"])
        list_frame = ttk.Frame(self.content, style="Card.TFrame")
        list_frame.pack(fill="x", pady=(6, 4))
        self.room_list = tk.Listbox(
            list_frame,
            selectmode="extended",
            exportselection=False,
            height=min(10, max(4, len(self.rooms))),
            font=("Consolas", 9),
        )
        room_scroll = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.room_list.yview
        )
        self.room_list.configure(yscrollcommand=room_scroll.set)
        for room in self.rooms:
            self.room_list.insert(
                "end",
                "{:<16} | {:<38} | current: {}".format(
                    room["room_id"][:16],
                    room["room_name"][:38],
                    room["current_template_name"] or "<none>",
                ),
            )
        self.room_list.pack(side="left", fill="x", expand=True)
        room_scroll.pack(side="right", fill="y")
        self.room_list.bind("<<ListboxSelect>>", self._invalidate_preview)
        buttons = ttk.Frame(self.content, style="Card.TFrame")
        buttons.pack(fill="x", pady=(0, 12))
        ttk.Button(
            buttons,
            text="Select all rooms",
            style="Secondary.TButton",
            command=self._select_all,
        ).pack(side="left")
        ttk.Button(
            buttons,
            text="Clear selection",
            style="Secondary.TButton",
            command=self._clear_selection,
        ).pack(side="left", padx=(6, 0))

    def _build_evidence(self) -> None:
        ttk.Label(
            self.content,
            style="Section.TLabel",
            text=self._t("template_remediation_technical_section"),
        ).pack(anchor="w", pady=(8, 4))
        ttk.Label(
            self.content,
            style="Help.TLabel",
            wraplength=980,
            text=self._t("template_remediation_automatic_evidence_help"),
        ).pack(anchor="w", fill="x", pady=(0, 8))
        self.copy_confirmed = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.content,
            style="Body.TCheckbutton",
            variable=self.copy_confirmed,
            command=self._invalidate_preview,
            text=self._t("template_remediation_copy_confirmation"),
        ).pack(anchor="w", pady=(8, 12))
        self.application_confirmed = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            self.content,
            style="Body.TCheckbutton",
            variable=self.application_confirmed,
            command=self._invalidate_preview,
            text=self._t("template_remediation_apply_confirmation"),
        ).pack(anchor="w", pady=(0, 12))

    def _build_preview(self) -> None:
        ttk.Label(
            self.content, style="Section.TLabel", text="4. Preview and controlled apply"
        ).pack(anchor="w")
        self.status_var = tk.StringVar(
            value="No preview exists. VE has not been changed."
        )
        self.status_label = ttk.Label(
            self.content,
            style="Body.TLabel",
            textvariable=self.status_var,
            wraplength=1000,
        )
        self.status_label.pack(anchor="w", fill="x", pady=(6, 4))
        self.preview_text = tk.Text(
            self.content,
            height=10,
            wrap="word",
            font=("Consolas", 9),
            background="#F8FAFC",
            foreground=TEXT,
        )
        self.preview_text.pack(fill="x", pady=(0, 10))
        self.preview_text.configure(state="disabled")

    def _build_actions(self) -> None:
        bar = ttk.Frame(self.content, style="Card.TFrame")
        bar.pack(fill="x", pady=(2, 8))
        ttk.Button(
            bar,
            text="Create read-only preview",
            style="Secondary.TButton",
            command=self._preview,
        ).pack(side="left")
        self.apply_button = ttk.Button(
            bar,
            text="Apply previewed template",
            style="Primary.TButton",
            command=self._apply,
            state="disabled",
        )
        self.apply_button.pack(side="left", padx=(8, 0))
        ttk.Button(
            bar,
            text="Close without saving VE",
            style="Secondary.TButton",
            command=self._close,
        ).pack(side="right")

    def _selected_room_ids(self) -> List[str]:
        return [self.rooms[index]["room_id"] for index in self.room_list.curselection()]

    def _form_signature(self) -> Tuple[Any, ...]:
        return (
            self.template_var.get(),
            tuple(self._selected_room_ids()),
            bool(self.copy_confirmed.get()),
            bool(self.application_confirmed.get()),
        )

    def _evidence(self):
        template_name = self.template_var.get()
        template = next(
            (
                item
                for item in self.inventory["templates"]
                if item["name"] == template_name
            ),
            {"name": template_name, "fingerprint_sha256": ""},
        )
        return automatic_template_evidence(
            self.project_path,
            self.project_name,
            template,
            self._selected_room_ids(),
            bool(self.application_confirmed.get()),
        )

    def _invalidate_preview(self, _event: Any = None) -> None:
        if self.plan is not None and self._form_signature() != self.preview_signature:
            self.plan = None
            self.plan_path = None
            self.preview_signature = None
            self.apply_button.configure(state="disabled")
            self.status_var.set(self._t("template_remediation_confirmation_changed"))

    def _select_all(self) -> None:
        self.room_list.select_set(0, "end")
        self._invalidate_preview()

    def _clear_selection(self) -> None:
        self.room_list.selection_clear(0, "end")
        self._invalidate_preview()

    def _set_preview_text(self, text: str) -> None:
        self.preview_text.configure(state="normal")
        self.preview_text.delete("1.0", "end")
        self.preview_text.insert("1.0", text)
        self.preview_text.configure(state="disabled")

    def _preview(self) -> None:
        try:
            plan = build_preview_plan(
                self.project_path,
                self.project_name,
                self.project,
                self.model,
                self.template_var.get(),
                self._selected_room_ids(),
                self._evidence(),
                bool(self.copy_confirmed.get()),
            )
        except Exception as exc:
            self.plan = None
            self.apply_button.configure(state="disabled")
            self.status_var.set("Preview blocked: {}".format(exc))
            if messagebox is not None:
                messagebox.showerror("Preview blocked", str(exc))
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        folder = (
            Path(self.project_path)
            / "sia_compliance_artifacts"
            / "template_remediation"
        )
        path = folder / "sia3802_template_plan_{}.json".format(timestamp)
        write_json_artifact(path, plan)
        self.plan = plan
        self.plan_path = path
        self.preview_signature = self._form_signature()
        ready_to_apply = plan["status"] == "READY_FOR_APPLY"
        self.apply_button.configure(state="normal" if ready_to_apply else "disabled")
        structure = plan.get("capability_assessment", {}).get(
            "room_gain_structure", {}
        )
        blocked_rooms = [
            room
            for room in structure.get("rooms", [])
            if room.get("status") == "BLOCKED"
        ]
        bridge_required = structure.get("status") == (
            "TRANSIENT_SOURCE_TEMPLATE_GAIN_BRIDGE_AVAILABLE"
        )
        lines = [
            "STATUS: {}".format(plan["status"]),
            "Template: {}".format(plan["template"]["name"]),
            "Template fingerprint: {}".format(plan["template"]["fingerprint_sha256"]),
            "Selected rooms: {}".format(len(plan["rooms"])),
            "Target gains: {}".format(
                len(plan["template"]["content"]["casual_gains"])
            ),
            "Target air exchanges: {}".format(
                len(plan["template"]["content"]["air_exchanges"])
            ),
            "Room-condition fields: {}".format(
                len(plan["template"]["content"]["room_conditions"])
            ),
            "Apache-system fields: {}".format(
                len(plan["template"]["content"]["apache_systems"])
            ),
            "Lighting gain detected (review aid): {}".format(
                plan["template"]["review_observations"][
                    "lighting_gain_detected"
                ]
            ),
            "Non-infiltration air exchange detected (review aid): {}".format(
                plan["template"]["review_observations"][
                    "non_infiltration_air_exchange_detected"
                ]
            ),
            "Plan checksum: {}".format(plan["plan_sha256"]),
            "Plan file: {}".format(path),
            "Evidence mode: {}".format(plan["evidence"]["evidence_mode"]),
            "Source trace: {}".format(plan["evidence"]["source_trace_status"]),
            "{}: {}".format(
                self._t("template_remediation_gain_structure_status"),
                structure.get("status", "NOT_CHECKABLE"),
            ),
        ]
        for room in blocked_rooms:
            lines.append(
                "{} | {}: {}".format(
                    room.get("room_name") or room.get("room_id"),
                    self._t("template_remediation_missing_gain_families"),
                    ", ".join(room.get("missing_gain_families", [])) or "[TO VERIFY]",
                )
            )
        lines.extend([
            "",
            "No VE object was changed by this preview.",
            (
                self._t("template_remediation_gain_structure_bridge")
                if ready_to_apply and bridge_required
                else "Applying will change only the selected rooms in the active copy."
                if ready_to_apply
                else (
                    self._t("template_remediation_gain_structure_blocked")
                    if plan["status"]
                    == "BLOCKED_UNSUPPORTED_ROOM_GAIN_STRUCTURE"
                    else self._t("template_remediation_apply_locked")
                )
            ),
        ])
        self._set_preview_text("\n".join(lines))
        if ready_to_apply:
            status_text = self._t("template_remediation_preview_ready")
        elif plan["status"] == "BLOCKED_UNSUPPORTED_ROOM_GAIN_STRUCTURE":
            status_text = self._t("template_remediation_gain_structure_blocked")
        else:
            status_text = "Review-only preview ready. No application is permitted."
        self.status_var.set(status_text)

    def _apply(self) -> None:
        if self.plan is None or self.preview_signature != self._form_signature():
            self.status_var.set("Create a new preview before applying.")
            self.apply_button.configure(state="disabled")
            return
        if messagebox is not None and not messagebox.askyesno(
            "Apply reviewed template",
            (
                "Apply '{}' to {} selected room(s) in this disposable copy?\n\n"
                "If the operation fails, close VE without saving and reopen the copy."
            ).format(self.plan["template"]["name"], len(self.plan["rooms"])),
        ):
            return
        folder = (
            Path(self.project_path)
            / "sia_compliance_artifacts"
            / "template_remediation"
        )
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        receipt_path = folder / "sia3802_template_receipt_{}.json".format(timestamp)
        try:
            receipt = apply_preview_plan(self.iesve, self.plan)
            write_json_artifact(receipt_path, receipt)
        except Exception as exc:
            failure = {
                "status": "FAIL",
                "error": str(exc),
                "failed_at": datetime.now().isoformat(timespec="seconds"),
                "plan_sha256": self.plan.get("plan_sha256"),
                "rollback_action": (
                    "Close VE without saving and reopen the disposable project copy."
                ),
                "compliance_claim": "NOT_GRANTED",
            }
            write_json_artifact(receipt_path, failure)
            self.status_var.set("Application failed: {}".format(exc))
            self._set_preview_text(
                "APPLICATION FAILED\n{}\n\nReceipt: {}\n\nClose VE without saving."
                .format(exc, receipt_path)
            )
            self.apply_button.configure(state="disabled")
            if messagebox is not None:
                messagebox.showerror(
                    "Application failed",
                    "{}\n\nClose VE without saving.\nReceipt: {}".format(
                        exc, receipt_path
                    ),
                )
            return
        self.apply_button.configure(state="disabled")
        self.status_var.set(
            "Template applied and read-back verified. Rerun the SIA 380/2 audit before saving VE."
        )
        self._set_preview_text(
            "APPLICATION VERIFIED\nTemplate: {}\nRooms: {}\nReceipt: {}\n\n"
            "Required next step: rerun the read-only SIA 380/2 audit.\n"
            "This receipt does not grant a compliance verdict.".format(
                receipt["template"]["name"],
                len(receipt["ve_receipt"]["room_ids"]),
                receipt_path,
            )
        )
        if messagebox is not None:
            messagebox.showinfo(
                "Read-back verified",
                (
                    "The template assignment was verified.\n\n"
                    "Now rerun the read-only SIA 380/2 audit. Save the VE copy only "
                    "after reviewing the post-mutation findings.\n\nReceipt: {}"
                ).format(receipt_path),
            )

    def run(self) -> None:
        """Open the modal VEScripts window."""

        self.root.update_idletasks()
        self.root.attributes("-topmost", True)
        self.root.after(350, lambda: self.root.attributes("-topmost", False))
        print(
            "SIA 380/2 TEMPLATE REMEDIATION: WINDOW_OPEN - close the window "
            "to complete this VEScripts run.",
            flush=True,
        )
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self._close()
            print(
                "SIA 380/2 TEMPLATE REMEDIATION: CLOSED_AFTER_USER_INTERRUPT",
                flush=True,
            )

    def _close(self) -> None:
        """Leave the Tk loop cleanly without saving the VE project."""

        try:
            self.root.quit()
        finally:
            try:
                self.root.destroy()
            except tk.TclError:
                pass


def launch_client_template_remediation(
    iesve_module: Any, project: Any, model: Any, project_path: str
) -> None:
    """Create and run the guarded remediation window."""

    ClientTemplateRemediationUI(
        iesve_module, project, model, project_path
    ).run()
