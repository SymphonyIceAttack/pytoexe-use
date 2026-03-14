"""
RE4 Code Patcher Tool
=====================
Main application entry point.
Reads code definitions from the_codes/codes_info.json
Reads hex patch data  from the_codes/codes_data.json
"""

import sys
import os
import json
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk

# ── paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
CODES_DIR = os.path.join(BASE_DIR, "the_codes")
INFO_FILE = os.path.join(CODES_DIR, "codes_info.json")
DATA_FILE = os.path.join(CODES_DIR, "codes_data.json")

# ── theme ────────────────────────────────────────────────────────────────────
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

BG_MAIN   = "#0d0d0d"
BG_PANEL  = "#111111"
BG_SIDEBAR= "#0a0a0a"
BG_ROW    = "#141414"
BG_ROW_ON = "#0d1a0d"
BG_ROW_LK = "#0d0d0d"
BG_HEADER = "#0f0c00"

ACCENT    = "#c8b060"
ACCENT2   = "#e8c060"
GREEN     = "#5afc5a"
RED_SOFT  = "#fc7c7c"
ORANGE    = "#c8a060"
MUTED     = "#666666"
TEXT_MAIN = "#c8b89a"
TEXT_DIM  = "#888888"
TEXT_LOCK = "#555555"
BORDER    = "#2a2a1a"
BORDER_ON = "#2a5a2a"
BORDER_LK = "#2a1a1a"

FONT_TITLE  = ("Courier New", 13, "bold")
FONT_NORMAL = ("Courier New", 11)
FONT_SMALL  = ("Courier New", 10)
FONT_TINY   = ("Courier New", 9)


# ═════════════════════════════════════════════════════════════════════════════
#  Data helpers
# ═════════════════════════════════════════════════════════════════════════════

def load_json(path):
    if not os.path.exists(path):
        messagebox.showerror("Missing File", f"Cannot find:\n{path}")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def scan_exe(path: str, codes_info: dict) -> dict:
    """
    Quick scan of bio4.exe to detect which codes are already applied.
    Reads codes_data.json and looks for the first 'replace' bytes of each
    detectable code at the expected location.
    Returns {code_id: True/False}
    """
    results = {}
    try:
        codes_data = load_json(DATA_FILE)
        with open(path, "rb") as f:
            exe_bytes = f.read()
    except Exception:
        return results

    for code in codes_info.get("codes", []):
        cid = code["id"]
        if not code.get("detectable", False):
            results[cid] = False
            continue
        data = codes_data.get(cid, {})
        patches = data.get("patches", [])
        if not patches:
            results[cid] = False
            continue
        first = patches[0]
        try:
            if first["type"] == "find_replace":
                needle = bytes.fromhex(first["replace"].replace(" ", ""))
                results[cid] = needle in exe_bytes
            elif first["type"] == "offset_paste":
                offset = int(first["offset"], 16)
                needle = bytes.fromhex(first["bytes"].replace(" ", ""))
                results[cid] = exe_bytes[offset:offset + len(needle)] == needle
            elif first["type"] == "offset_replace":
                offset = int(first["offset"], 16)
                needle = bytes.fromhex(first["bytes"].replace(" ", ""))
                results[cid] = exe_bytes[offset:offset + len(needle)] == needle
            else:
                results[cid] = False
        except Exception:
            results[cid] = False
    return results


def apply_patch(exe_path: str, code_id: str, codes_data: dict,
                mod_expansion: bool = None) -> tuple[bool, str]:
    """Apply a code's patches to bio4.exe. Returns (success, message)."""
    data = codes_data.get(code_id)
    if not data:
        return False, f"No patch data for '{code_id}'"

    try:
        with open(exe_path, "rb") as f:
            exe = bytearray(f.read())
    except Exception as e:
        return False, str(e)

    # Handle variant codes (e.g. enemy_persistence)
    if "variants" in data:
        if mod_expansion is True:
            patches = data["variants"]["with_mod_expansion"]["patches"]
        else:
            patches = data["variants"]["without_mod_expansion"]["patches"]
    else:
        patches = data.get("patches", [])

    for patch in patches:
        try:
            ptype = patch["type"]
            if ptype == "find_replace":
                find_b    = bytes.fromhex(patch["find"].replace(" ", ""))
                replace_b = bytes.fromhex(patch["replace"].replace(" ", ""))
                idx = exe.find(find_b)
                if idx == -1:
                    return False, f"Pattern not found:\n{patch['find'][:40]}..."
                exe[idx:idx + len(find_b)] = replace_b

            elif ptype in ("offset_paste", "offset_replace"):
                key   = "bytes" if ptype == "offset_replace" else "bytes"
                off   = int(patch["offset"], 16)
                data_b= bytes.fromhex(patch[key].replace(" ", ""))
                exe[off:off + len(data_b)] = data_b

        except Exception as e:
            return False, str(e)

    try:
        with open(exe_path, "wb") as f:
            f.write(exe)
    except Exception as e:
        return False, str(e)

    return True, "OK"


# ═════════════════════════════════════════════════════════════════════════════
#  Widgets
# ═════════════════════════════════════════════════════════════════════════════

class CodeRow(ctk.CTkFrame):
    """One code row in the right panel."""

    def __init__(self, parent, code: dict, app, **kw):
        super().__init__(parent, fg_color=BG_ROW, corner_radius=0, **kw)
        self.code = code
        self.app  = app
        self._expanded = False
        self._build()

    def _build(self):
        self.configure(border_width=1, border_color=BORDER)

        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=6, pady=4)

        # Toggle button
        self.toggle_btn = ctk.CTkButton(
            top, text="OFF", width=46, height=22,
            fg_color="#1a1a1a", hover_color="#222",
            text_color=MUTED, font=FONT_TINY,
            border_width=1, border_color="#444",
            corner_radius=2,
            command=self._on_toggle
        )
        self.toggle_btn.pack(side="left", padx=(0, 6))

        # Lock / detected badge
        self.badge_var = tk.StringVar(value="")
        self.badge_lbl = ctk.CTkLabel(top, textvariable=self.badge_var,
                                      font=FONT_TINY, text_color=ORANGE, width=16)
        self.badge_lbl.pack(side="left", padx=(0, 4))

        # Name + desc
        info_frame = ctk.CTkFrame(top, fg_color="transparent")
        info_frame.pack(side="left", fill="x", expand=True)

        self.name_lbl = ctk.CTkLabel(
            info_frame, text=self.code["name"],
            font=FONT_NORMAL, text_color=TEXT_MAIN,
            anchor="w"
        )
        self.name_lbl.pack(anchor="w")

        self.desc_lbl = ctk.CTkLabel(
            info_frame, text=self.code["desc"],
            font=FONT_TINY, text_color=MUTED,
            anchor="w", wraplength=500, justify="left"
        )
        self.desc_lbl.pack(anchor="w")

        # Expand arrow (only if notes exist)
        if self.code.get("notes"):
            self.arrow_btn = ctk.CTkButton(
                top, text="▼", width=24, height=22,
                fg_color="transparent", hover_color="#1a1a1a",
                text_color=MUTED, font=FONT_TINY,
                command=self._toggle_notes
            )
            self.arrow_btn.pack(side="right")

        # Notes frame (hidden by default)
        self.notes_frame = ctk.CTkFrame(self, fg_color="#0d0d00", corner_radius=0)
        for note in self.code.get("notes", []):
            ctk.CTkLabel(
                self.notes_frame, text=f"  ⚠  {note}",
                font=FONT_TINY, text_color=ORANGE,
                anchor="w"
            ).pack(anchor="w", padx=8, pady=1)

    def _toggle_notes(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.notes_frame.pack(fill="x")
            self.arrow_btn.configure(text="▲")
        else:
            self.notes_frame.pack_forget()
            self.arrow_btn.configure(text="▼")

    def _on_toggle(self):
        self.app.handle_toggle(self.code["id"])

    def refresh(self, applied: bool, locked: bool, detected: bool):
        if detected and not applied:
            # Mark as applied if detected
            applied = True

        if locked:
            self.configure(fg_color=BG_ROW_LK, border_color=BORDER_LK)
            self.toggle_btn.configure(
                text="OFF", fg_color="#1a1a1a", text_color=TEXT_LOCK,
                border_color="#333", state="disabled"
            )
            self.name_lbl.configure(text_color=TEXT_LOCK)
            self.badge_var.set("🔒")
            self.badge_lbl.configure(text_color="#c85a2a")
        elif applied:
            self.configure(fg_color=BG_ROW_ON, border_color=BORDER_ON)
            self.toggle_btn.configure(
                text="ON", fg_color="#2a5a2a", text_color=GREEN,
                border_color=GREEN, state="normal"
            )
            self.name_lbl.configure(text_color="#e8e0c0", font=("Courier New", 11, "bold"))
            if detected:
                self.badge_var.set("●")
                self.badge_lbl.configure(text_color=GREEN)
            else:
                self.badge_var.set("")
        else:
            self.configure(fg_color=BG_ROW, border_color=BORDER)
            self.toggle_btn.configure(
                text="OFF", fg_color="#1a1a1a", text_color=MUTED,
                border_color="#444", state="normal"
            )
            self.name_lbl.configure(text_color=TEXT_MAIN, font=FONT_NORMAL)
            self.badge_var.set("")


class SidebarItem(ctk.CTkFrame):
    """One section button in the sidebar."""

    def __init__(self, parent, section: dict, app, **kw):
        super().__init__(parent, fg_color="transparent", corner_radius=0, **kw)
        self.section = section
        self.app = app
        self._active = False

        self.btn = ctk.CTkButton(
            self, text=f"  {section['icon']}  {section['label']}",
            fg_color="transparent", hover_color="#1a1200",
            text_color=TEXT_DIM, font=FONT_SMALL,
            anchor="w", height=34, corner_radius=0,
            border_width=0,
            command=lambda: app.select_section(section["id"])
        )
        self.btn.pack(fill="x")

        self.indicator = ctk.CTkFrame(self, fg_color="transparent",
                                      width=2, height=34, corner_radius=0)
        self.indicator.place(x=0, y=0)

    def set_active(self, active: bool):
        self._active = active
        if active:
            self.btn.configure(fg_color="#1a1200", text_color=ACCENT2)
            self.indicator.configure(fg_color=ACCENT)
        else:
            self.btn.configure(fg_color="transparent", text_color=TEXT_DIM)
            self.indicator.configure(fg_color="transparent")


# ═════════════════════════════════════════════════════════════════════════════
#  Main App
# ═════════════════════════════════════════════════════════════════════════════

class RE4PatcherApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.title("RE4 Code Patcher Tool — Preview")
        self.geometry("1000x680")
        self.minsize(820, 560)
        self.configure(fg_color=BG_MAIN)

        # ── state ──
        self.exe_path     = tk.StringVar()
        self.scanned      = False
        self.detected     : dict[str, bool] = {}   # code_id -> found in exe
        self.applied      : dict[str, bool] = {}   # code_id -> applied this session
        self.active_section = None

        # ── load data ──
        self.codes_info = load_json(INFO_FILE)
        self.codes_data = load_json(DATA_FILE)

        # Build lookup dicts
        self.sections_list = self.codes_info["sections"]
        self.all_codes     = self.codes_info["codes"]
        self.code_by_id    = {c["id"]: c for c in self.all_codes}
        self.codes_by_section = {}
        for c in self.all_codes:
            self.codes_by_section.setdefault(c["section"], []).append(c)

        self._build_ui()
        self.select_section(self.sections_list[0]["id"])

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # ── top bar ──
        topbar = ctk.CTkFrame(self, fg_color="#0f0c00", corner_radius=0,
                              border_width=0)
        topbar.pack(fill="x")

        ctk.CTkLabel(topbar, text="RE4 Code Patcher Tool",
                     font=("Courier New", 13, "bold"), text_color=ACCENT2
                     ).pack(side="left", padx=14, pady=6)
        ctk.CTkLabel(topbar, text="v0.1.0",
                     font=FONT_TINY, text_color=MUTED
                     ).pack(side="left")
        ctk.CTkLabel(topbar, text="by Player7z",
                     font=FONT_TINY, text_color="#444"
                     ).pack(side="right", padx=14)

        # ── exe path row ──
        path_bar = ctk.CTkFrame(self, fg_color="#111111", corner_radius=0)
        path_bar.pack(fill="x")

        ctk.CTkLabel(path_bar, text="Game Executable (bio4.exe):",
                     font=FONT_SMALL, text_color=TEXT_DIM
                     ).pack(side="left", padx=(12, 6), pady=5)

        self.path_entry = ctk.CTkEntry(
            path_bar, textvariable=self.exe_path,
            placeholder_text="Select bio4.exe...",
            font=FONT_SMALL, text_color="#7cfc7c",
            fg_color="#0d1a0d", border_color="#2a5a2a",
            width=420
        )
        self.path_entry.pack(side="left", pady=5)

        ctk.CTkButton(path_bar, text="Browse...", width=80,
                      font=FONT_SMALL, fg_color="#2a2a1a",
                      hover_color="#3a3a2a", text_color=ACCENT,
                      border_width=1, border_color=ACCENT,
                      corner_radius=2, command=self._browse
                      ).pack(side="left", padx=6)

        self.scan_btn = ctk.CTkButton(
            path_bar, text="Scan EXE", width=90,
            font=FONT_SMALL, fg_color="#1a2a0a",
            hover_color="#2a4a1a", text_color=GREEN,
            border_width=1, border_color=GREEN,
            corner_radius=2, command=self._scan
        )
        self.scan_btn.pack(side="left", padx=2)

        self.scan_status = ctk.CTkLabel(path_bar, text="",
                                        font=FONT_TINY, text_color=GREEN)
        self.scan_status.pack(side="left", padx=8)

        # ── notice bar (hidden until scanned) ──
        self.notice = ctk.CTkFrame(self, fg_color="#1a1200", corner_radius=0)
        ctk.CTkLabel(self.notice,
                     text="  ⚠  حط مسار bio4.exe واضغط Scan عشان تشوف وتفعل الأكواد",
                     font=FONT_SMALL, text_color=ACCENT
                     ).pack(side="left", padx=10, pady=4)
        self.notice.pack(fill="x")

        # ── main body ──
        body = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        body.pack(fill="both", expand=True)

        # Sidebar
        sidebar_outer = ctk.CTkFrame(body, fg_color=BG_SIDEBAR, corner_radius=0,
                                     width=210)
        sidebar_outer.pack(side="left", fill="y")
        sidebar_outer.pack_propagate(False)

        self.sidebar_scroll = ctk.CTkScrollableFrame(
            sidebar_outer, fg_color=BG_SIDEBAR, corner_radius=0,
            scrollbar_button_color="#333", scrollbar_button_hover_color="#444"
        )
        self.sidebar_scroll.pack(fill="both", expand=True)

        self.sidebar_items: dict[str, SidebarItem] = {}
        for sec in self.sections_list:
            item = SidebarItem(self.sidebar_scroll, sec, self)
            item.pack(fill="x")
            self.sidebar_items[sec["id"]] = item

        # Right panel
        right = ctk.CTkFrame(body, fg_color=BG_PANEL, corner_radius=0)
        right.pack(side="left", fill="both", expand=True)

        # Section header
        self.section_header = ctk.CTkFrame(right, fg_color=BG_HEADER,
                                           corner_radius=0)
        self.section_header.pack(fill="x")
        self.section_title_lbl = ctk.CTkLabel(
            self.section_header, text="",
            font=("Courier New", 14, "bold"), text_color=ACCENT2
        )
        self.section_title_lbl.pack(side="left", padx=14, pady=6)
        self.section_count_lbl = ctk.CTkLabel(
            self.section_header, text="",
            font=FONT_TINY, text_color=MUTED
        )
        self.section_count_lbl.pack(side="left", pady=6)

        # Codes list
        self.codes_scroll = ctk.CTkScrollableFrame(
            right, fg_color=BG_PANEL, corner_radius=0,
            scrollbar_button_color="#333", scrollbar_button_hover_color="#444"
        )
        self.codes_scroll.pack(fill="both", expand=True, padx=10, pady=8)

        # Status bar
        statusbar = ctk.CTkFrame(self, fg_color="#0a0a0a", corner_radius=0,
                                 height=24)
        statusbar.pack(fill="x")
        statusbar.pack_propagate(False)

        self.status_applied = ctk.CTkLabel(statusbar, text="Applied: 0",
                                           font=FONT_TINY, text_color=MUTED)
        self.status_applied.pack(side="left", padx=12)

        self.status_detected = ctk.CTkLabel(statusbar, text="Detected: 0",
                                            font=FONT_TINY, text_color=MUTED)
        self.status_detected.pack(side="left", padx=8)

        self.status_exe = ctk.CTkLabel(statusbar, text="",
                                       font=FONT_TINY, text_color=GREEN)
        self.status_exe.pack(side="left", padx=8)

        # ── code rows dict ──
        self.code_rows: dict[str, CodeRow] = {}

    # ── logic ─────────────────────────────────────────────────────────────────

    def _browse(self):
        path = filedialog.askopenfilename(
            title="Select bio4.exe",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
        )
        if path:
            self.exe_path.set(path)

    def _scan(self):
        path = self.exe_path.get().strip()
        if not path or not os.path.isfile(path):
            messagebox.showerror("Error", "Please select a valid bio4.exe file.")
            return

        self.scan_btn.configure(text="Scanning...", state="disabled")
        self.update_idletasks()

        self.detected = scan_exe(path, self.codes_info)
        # Pre-mark detected codes as applied
        for cid, found in self.detected.items():
            if found:
                self.applied[cid] = True

        self.scanned = True
        n_det = sum(1 for v in self.detected.values() if v)
        self.scan_btn.configure(text="Re-Scan", state="normal")
        self.scan_status.configure(text=f"✓ Scanned — {n_det} codes detected")
        self.notice.pack_forget()
        self._refresh_all()
        self._update_statusbar()

    def select_section(self, section_id: str):
        # Update sidebar highlights
        for sid, item in self.sidebar_items.items():
            item.set_active(sid == section_id)

        self.active_section = section_id

        # Find section label
        sec = next((s for s in self.sections_list if s["id"] == section_id), None)
        if sec:
            self.section_title_lbl.configure(
                text=f"{sec['icon']}  {sec['label']}"
            )

        # Clear code rows
        for w in self.codes_scroll.winfo_children():
            w.destroy()
        self.code_rows.clear()

        codes = self.codes_by_section.get(section_id, [])
        self.section_count_lbl.configure(text=f"  {len(codes)} codes")

        if not codes:
            ctk.CTkLabel(
                self.codes_scroll,
                text="— لا يوجد أكواد في هاذا القسم بعد —",
                font=FONT_SMALL, text_color=MUTED
            ).pack(pady=24)
            return

        for code in codes:
            row = CodeRow(self.codes_scroll, code, self)
            row.pack(fill="x", pady=2)
            self.code_rows[code["id"]] = row
            self._refresh_row(code["id"])

    def _is_unlocked(self, code_id: str) -> bool:
        if not self.scanned:
            return False
        code = self.code_by_id.get(code_id, {})
        for dep in code.get("requires", []):
            if not (self.applied.get(dep) or self.detected.get(dep)):
                return False
        return True

    def handle_toggle(self, code_id: str):
        if not self._is_unlocked(code_id):
            return

        code = self.code_by_id.get(code_id, {})
        already_applied = self.applied.get(code_id, False)

        if already_applied:
            # TODO: unapply support
            messagebox.showinfo("Info", "إزاله الكود قريباً في إصدار لاحق.\n"
                                        "استخدم ملف النسخه الاحتياطيه.")
            return

        # Special dialog for enemy_persistence
        if code.get("dialog") == "mod_expansion":
            self._dialog_mod_expansion(code_id)
            return

        self._do_apply(code_id)

    def _dialog_mod_expansion(self, code_id: str):
        dlg = ctk.CTkToplevel(self)
        dlg.title("Enemy Spawn Persistence")
        dlg.geometry("380x180")
        dlg.resizable(False, False)
        dlg.configure(fg_color="#111")
        dlg.grab_set()

        ctk.CTkLabel(dlg, text="هل انت مفعل EnableModExpansion؟",
                     font=FONT_NORMAL, text_color=ACCENT2
                     ).pack(pady=(20, 6))
        ctk.CTkLabel(dlg,
                     text="سيؤثر هاذا على الكود اللي راح ينحط في EXE",
                     font=FONT_TINY, text_color=MUTED
                     ).pack()

        btn_frame = ctk.CTkFrame(dlg, fg_color="transparent")
        btn_frame.pack(pady=20)

        ctk.CTkButton(btn_frame, text="✓  Yes", width=90,
                      fg_color="#1a2a0a", hover_color="#2a4a1a",
                      text_color=GREEN, border_width=1, border_color=GREEN,
                      corner_radius=2,
                      command=lambda: [dlg.destroy(),
                                       self._do_apply(code_id, mod_expansion=True)]
                      ).pack(side="left", padx=8)

        ctk.CTkButton(btn_frame, text="✗  No", width=90,
                      fg_color="#2a0a0a", hover_color="#4a1a1a",
                      text_color=RED_SOFT, border_width=1, border_color=RED_SOFT,
                      corner_radius=2,
                      command=lambda: [dlg.destroy(),
                                       self._do_apply(code_id, mod_expansion=False)]
                      ).pack(side="left", padx=8)

        ctk.CTkButton(btn_frame, text="Cancel", width=80,
                      fg_color="#1a1a1a", hover_color="#2a2a2a",
                      text_color=MUTED, border_width=1, border_color="#444",
                      corner_radius=2,
                      command=dlg.destroy
                      ).pack(side="left", padx=8)

    def _do_apply(self, code_id: str, mod_expansion: bool = None):
        exe = self.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "EXE path غير صحيح.")
            return

        ok, msg = apply_patch(exe, code_id, self.codes_data, mod_expansion)
        if ok:
            self.applied[code_id] = True
            self._refresh_row(code_id)
            self._update_statusbar()
            messagebox.showinfo("✓ Applied", f"تم تطبيق الكود بنجاح:\n{self.code_by_id[code_id]['name']}")
        else:
            messagebox.showerror("Error", f"فشل تطبيق الكود:\n{msg}")

    def _refresh_row(self, code_id: str):
        row = self.code_rows.get(code_id)
        if not row:
            return
        row.refresh(
            applied  = self.applied.get(code_id, False),
            locked   = not self._is_unlocked(code_id),
            detected = self.detected.get(code_id, False)
        )

    def _refresh_all(self):
        for cid in self.code_rows:
            self._refresh_row(cid)

    def _update_statusbar(self):
        n_applied  = sum(1 for v in self.applied.values() if v)
        n_detected = sum(1 for v in self.detected.values() if v)
        self.status_applied.configure(text=f"Applied: {n_applied}")
        self.status_detected.configure(text=f"Detected: {n_detected}")
        if self.scanned:
            self.status_exe.configure(text="● EXE Loaded")
        else:
            self.status_exe.configure(text="")


# ═════════════════════════════════════════════════════════════════════════════
#  Entry point
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = RE4PatcherApp()
    app.mainloop()
