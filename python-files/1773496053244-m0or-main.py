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

# ── paths ────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(sys.argv[0]))
CODES_DIR = os.path.join(BASE_DIR, "the_codes")
INFO_FILE = os.path.join(CODES_DIR, "codes_info.json")
DATA_FILE = os.path.join(CODES_DIR, "codes_data.json")

# ── colors ───────────────────────────────────────────────────────────────────
BG_MAIN    = "#0d0d0d"
BG_PANEL   = "#111111"
BG_SIDEBAR = "#0a0a0a"
BG_ROW     = "#141414"
BG_ROW_ON  = "#0d1a0d"
BG_ROW_LK  = "#0d0d0d"
BG_HEADER  = "#0f0c00"
BG_TOPBAR  = "#0f0c00"
BG_PATHBAR = "#111111"
BG_NOTICE  = "#1a1200"
BG_STATUS  = "#0a0a0a"

ACCENT     = "#c8b060"
ACCENT2    = "#e8c060"
GREEN      = "#5afc5a"
RED_SOFT   = "#fc7c7c"
ORANGE     = "#c8a060"
MUTED      = "#666666"
TEXT_MAIN  = "#c8b89a"
TEXT_DIM   = "#888888"
TEXT_LOCK  = "#555555"
BORDER     = "#2a2a1a"
BORDER_ON  = "#2a5a2a"
BORDER_LK  = "#2a1a1a"

FONT_TITLE  = ("Courier New", 13, "bold")
FONT_NORMAL = ("Courier New", 11)
FONT_SMALL  = ("Courier New", 10)
FONT_TINY   = ("Courier New", 9)
FONT_BOLD   = ("Courier New", 11, "bold")


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
            elif first["type"] in ("offset_paste", "offset_replace"):
                offset = int(first["offset"], 16)
                needle = bytes.fromhex(first["bytes"].replace(" ", ""))
                results[cid] = exe_bytes[offset:offset + len(needle)] == needle
            else:
                results[cid] = False
        except Exception:
            results[cid] = False
    return results


def apply_patch(exe_path: str, code_id: str, codes_data: dict,
                mod_expansion: bool = None):
    data = codes_data.get(code_id)
    if not data:
        return False, f"No patch data for '{code_id}'"

    try:
        with open(exe_path, "rb") as f:
            exe = bytearray(f.read())
    except Exception as e:
        return False, str(e)

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
                off    = int(patch["offset"], 16)
                data_b = bytes.fromhex(patch["bytes"].replace(" ", ""))
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
#  Helpers
# ═════════════════════════════════════════════════════════════════════════════

def make_label(parent, text="", fg=TEXT_MAIN, bg=BG_MAIN,
               font=FONT_SMALL, **kw):
    return tk.Label(parent, text=text, fg=fg, bg=bg, font=font, **kw)


def make_button(parent, text, command, fg=ACCENT, bg="#2a2a1a",
                active_bg="#3a3a2a", font=FONT_SMALL, width=10, **kw):
    return tk.Button(
        parent, text=text, command=command,
        fg=fg, bg=bg,
        activeforeground=fg, activebackground=active_bg,
        font=font, width=width,
        relief="flat", bd=0, cursor="hand2",
        highlightthickness=1, highlightbackground=BORDER,
        **kw
    )


# ═════════════════════════════════════════════════════════════════════════════
#  CodeRow widget
# ═════════════════════════════════════════════════════════════════════════════

class CodeRow(tk.Frame):
    def __init__(self, parent, code: dict, app, **kw):
        super().__init__(parent, bg=BG_ROW,
                         highlightthickness=1,
                         highlightbackground=BORDER, **kw)
        self.code      = code
        self.app       = app
        self._expanded = False
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=BG_ROW)
        top.pack(fill="x", padx=6, pady=4)

        # Toggle button
        self.toggle_btn = tk.Button(
            top, text="OFF", width=5, font=FONT_TINY,
            fg=MUTED, bg="#1a1a1a",
            activeforeground=MUTED, activebackground="#222",
            relief="flat", bd=0,
            highlightthickness=1, highlightbackground="#444",
            cursor="hand2",
            command=self._on_toggle
        )
        self.toggle_btn.pack(side="left", padx=(0, 6))

        # Badge
        self.badge_var = tk.StringVar(value="")
        self.badge_lbl = tk.Label(
            top, textvariable=self.badge_var,
            font=FONT_TINY, fg=ORANGE, bg=BG_ROW, width=2
        )
        self.badge_lbl.pack(side="left", padx=(0, 4))

        # Name + desc
        info_frame = tk.Frame(top, bg=BG_ROW)
        info_frame.pack(side="left", fill="x", expand=True)

        self.name_lbl = tk.Label(
            info_frame, text=self.code["name"],
            font=FONT_NORMAL, fg=TEXT_MAIN, bg=BG_ROW,
            anchor="w", justify="left"
        )
        self.name_lbl.pack(anchor="w")

        self.desc_lbl = tk.Label(
            info_frame, text=self.code["desc"],
            font=FONT_TINY, fg=MUTED, bg=BG_ROW,
            anchor="w", justify="left", wraplength=500
        )
        self.desc_lbl.pack(anchor="w")

        # Expand arrow
        if self.code.get("notes"):
            self.arrow_btn = tk.Button(
                top, text="▼", width=2, font=FONT_TINY,
                fg=MUTED, bg=BG_ROW,
                activeforeground=MUTED, activebackground=BG_ROW,
                relief="flat", bd=0, cursor="hand2",
                command=self._toggle_notes
            )
            self.arrow_btn.pack(side="right")

        # Notes frame (hidden by default)
        self.notes_frame = tk.Frame(self, bg="#0d0d00")
        for note in self.code.get("notes", []):
            tk.Label(
                self.notes_frame,
                text=f"  ⚠  {note}",
                font=FONT_TINY, fg=ORANGE, bg="#0d0d00",
                anchor="w", justify="left"
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
            applied = True

        has_arrow = hasattr(self, "arrow_btn")

        if locked:
            self.configure(bg=BG_ROW_LK, highlightbackground=BORDER_LK)
            self.toggle_btn.configure(
                text="OFF", fg=TEXT_LOCK, bg="#1a1a1a",
                highlightbackground="#333", state="disabled"
            )
            self.name_lbl.configure(fg=TEXT_LOCK, bg=BG_ROW_LK, font=FONT_NORMAL)
            self.desc_lbl.configure(bg=BG_ROW_LK)
            self.badge_var.set("🔒")
            self.badge_lbl.configure(fg="#c85a2a", bg=BG_ROW_LK)
            if has_arrow:
                self.arrow_btn.configure(bg=BG_ROW_LK,
                                         activebackground=BG_ROW_LK)

        elif applied:
            self.configure(bg=BG_ROW_ON, highlightbackground=BORDER_ON)
            self.toggle_btn.configure(
                text="ON", fg=GREEN, bg="#2a5a2a",
                highlightbackground=GREEN, state="normal"
            )
            self.name_lbl.configure(fg="#e8e0c0", bg=BG_ROW_ON, font=FONT_BOLD)
            self.desc_lbl.configure(bg=BG_ROW_ON)
            self.badge_var.set("●" if detected else "")
            self.badge_lbl.configure(
                fg=GREEN if detected else BG_ROW_ON, bg=BG_ROW_ON
            )
            if has_arrow:
                self.arrow_btn.configure(bg=BG_ROW_ON,
                                         activebackground=BG_ROW_ON)

        else:
            self.configure(bg=BG_ROW, highlightbackground=BORDER)
            self.toggle_btn.configure(
                text="OFF", fg=MUTED, bg="#1a1a1a",
                highlightbackground="#444", state="normal"
            )
            self.name_lbl.configure(fg=TEXT_MAIN, bg=BG_ROW, font=FONT_NORMAL)
            self.desc_lbl.configure(bg=BG_ROW)
            self.badge_var.set("")
            self.badge_lbl.configure(bg=BG_ROW)
            if has_arrow:
                self.arrow_btn.configure(bg=BG_ROW, activebackground=BG_ROW)


# ═════════════════════════════════════════════════════════════════════════════
#  SidebarItem widget
# ═════════════════════════════════════════════════════════════════════════════

class SidebarItem(tk.Frame):
    def __init__(self, parent, section: dict, app, **kw):
        super().__init__(parent, bg=BG_SIDEBAR, **kw)
        self.section = section
        self.app     = app

        self.indicator = tk.Frame(self, bg=BG_SIDEBAR, width=3)
        self.indicator.pack(side="left", fill="y")

        self.btn = tk.Button(
            self,
            text=f"  {section['icon']}  {section['label']}",
            font=FONT_SMALL, fg=TEXT_DIM, bg=BG_SIDEBAR,
            activeforeground=ACCENT2, activebackground="#1a1200",
            anchor="w", relief="flat", bd=0, cursor="hand2",
            command=lambda: app.select_section(section["id"])
        )
        self.btn.pack(side="left", fill="x", expand=True, ipady=6)

    def set_active(self, active: bool):
        if active:
            self.btn.configure(fg=ACCENT2, bg="#1a1200",
                               activebackground="#1a1200")
            self.indicator.configure(bg=ACCENT)
        else:
            self.btn.configure(fg=TEXT_DIM, bg=BG_SIDEBAR,
                               activebackground="#1a1200")
            self.indicator.configure(bg=BG_SIDEBAR)


# ═════════════════════════════════════════════════════════════════════════════
#  Main App
# ═════════════════════════════════════════════════════════════════════════════

class RE4PatcherApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("RE4 Code Patcher Tool — Preview")
        self.geometry("1000x680")
        self.minsize(820, 560)
        self.configure(bg=BG_MAIN)

        # ── state ──
        self.exe_path       = tk.StringVar()
        self.scanned        = False
        self.detected       : dict = {}
        self.applied        : dict = {}
        self.active_section = None

        # ── load data ──
        self.codes_info = load_json(INFO_FILE)
        self.codes_data = load_json(DATA_FILE)

        self.sections_list    = self.codes_info["sections"]
        self.all_codes        = self.codes_info["codes"]
        self.code_by_id       = {c["id"]: c for c in self.all_codes}
        self.codes_by_section : dict = {}
        for c in self.all_codes:
            self.codes_by_section.setdefault(c["section"], []).append(c)

        self._build_ui()
        self.select_section(self.sections_list[0]["id"])

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        # top bar
        topbar = tk.Frame(self, bg=BG_TOPBAR)
        topbar.pack(fill="x")
        make_label(topbar, "RE4 Code Patcher Tool",
                   fg=ACCENT2, bg=BG_TOPBAR, font=FONT_TITLE
                   ).pack(side="left", padx=14, pady=6)
        make_label(topbar, "v0.1.0",
                   fg=MUTED, bg=BG_TOPBAR, font=FONT_TINY
                   ).pack(side="left")
        make_label(topbar, "by Player7z",
                   fg="#444", bg=BG_TOPBAR, font=FONT_TINY
                   ).pack(side="right", padx=14)

        # exe path row
        path_bar = tk.Frame(self, bg=BG_PATHBAR)
        path_bar.pack(fill="x")
        make_label(path_bar, "Game Executable (bio4.exe):",
                   fg=TEXT_DIM, bg=BG_PATHBAR
                   ).pack(side="left", padx=(12, 6), pady=5)
        self.path_entry = tk.Entry(
            path_bar, textvariable=self.exe_path,
            font=FONT_SMALL, fg="#7cfc7c", bg="#0d1a0d",
            insertbackground="#7cfc7c",
            relief="flat", bd=0,
            highlightthickness=1, highlightbackground="#2a5a2a",
            width=48
        )
        self.path_entry.pack(side="left", pady=5, ipady=3)
        make_button(path_bar, "Browse...", self._browse,
                    fg=ACCENT, bg="#2a2a1a", active_bg="#3a3a2a", width=9
                    ).pack(side="left", padx=6, pady=5)
        self.scan_btn = make_button(
            path_bar, "Scan EXE", self._scan,
            fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=9
        )
        self.scan_btn.pack(side="left", padx=2, pady=5)
        self.scan_status_var = tk.StringVar(value="")
        make_label(path_bar, fg=GREEN, bg=BG_PATHBAR, font=FONT_TINY,
                   textvariable=self.scan_status_var
                   ).pack(side="left", padx=8)

        # notice bar
        self.notice = tk.Frame(self, bg=BG_NOTICE)
        make_label(self.notice,
                   "  ⚠  حط مسار bio4.exe واضغط Scan عشان تشوف وتفعل الأكواد",
                   fg=ACCENT, bg=BG_NOTICE
                   ).pack(side="left", padx=10, pady=4)
        self.notice.pack(fill="x")

        # main body
        body = tk.Frame(self, bg=BG_MAIN)
        body.pack(fill="both", expand=True)

        # sidebar
        sidebar_outer = tk.Frame(body, bg=BG_SIDEBAR, width=210)
        sidebar_outer.pack(side="left", fill="y")
        sidebar_outer.pack_propagate(False)

        sb_canvas = tk.Canvas(sidebar_outer, bg=BG_SIDEBAR,
                              highlightthickness=0, width=210)
        sb_scroll = tk.Scrollbar(sidebar_outer, orient="vertical",
                                 command=sb_canvas.yview)
        sb_canvas.configure(yscrollcommand=sb_scroll.set)
        sb_scroll.pack(side="right", fill="y")
        sb_canvas.pack(side="left", fill="both", expand=True)

        self.sidebar_inner = tk.Frame(sb_canvas, bg=BG_SIDEBAR)
        sb_canvas.create_window((0, 0), window=self.sidebar_inner, anchor="nw")
        self.sidebar_inner.bind(
            "<Configure>",
            lambda e: sb_canvas.configure(
                scrollregion=sb_canvas.bbox("all"))
        )

        self.sidebar_items: dict = {}
        for sec in self.sections_list:
            item = SidebarItem(self.sidebar_inner, sec, self)
            item.pack(fill="x")
            self.sidebar_items[sec["id"]] = item

        # right panel
        right = tk.Frame(body, bg=BG_PANEL)
        right.pack(side="left", fill="both", expand=True)

        # section header
        sec_header = tk.Frame(right, bg=BG_HEADER)
        sec_header.pack(fill="x")
        self.section_title_var = tk.StringVar(value="")
        make_label(sec_header, fg=ACCENT2, bg=BG_HEADER,
                   font=("Courier New", 14, "bold"),
                   textvariable=self.section_title_var
                   ).pack(side="left", padx=14, pady=6)
        self.section_count_var = tk.StringVar(value="")
        make_label(sec_header, fg=MUTED, bg=BG_HEADER, font=FONT_TINY,
                   textvariable=self.section_count_var
                   ).pack(side="left", pady=6)

        # codes scrollable area
        codes_outer = tk.Frame(right, bg=BG_PANEL)
        codes_outer.pack(fill="both", expand=True, padx=10, pady=8)

        self.codes_canvas = tk.Canvas(codes_outer, bg=BG_PANEL,
                                      highlightthickness=0)
        codes_scroll = tk.Scrollbar(codes_outer, orient="vertical",
                                    command=self.codes_canvas.yview)
        self.codes_canvas.configure(yscrollcommand=codes_scroll.set)
        codes_scroll.pack(side="right", fill="y")
        self.codes_canvas.pack(side="left", fill="both", expand=True)

        self.codes_inner = tk.Frame(self.codes_canvas, bg=BG_PANEL)
        self._codes_win = self.codes_canvas.create_window(
            (0, 0), window=self.codes_inner, anchor="nw"
        )
        self.codes_inner.bind(
            "<Configure>",
            lambda e: self.codes_canvas.configure(
                scrollregion=self.codes_canvas.bbox("all"))
        )
        self.codes_canvas.bind(
            "<Configure>",
            lambda e: self.codes_canvas.itemconfig(
                self._codes_win, width=e.width)
        )
        self.codes_canvas.bind_all(
            "<MouseWheel>",
            lambda e: self.codes_canvas.yview_scroll(
                int(-1 * (e.delta / 120)), "units")
        )

        # status bar
        statusbar = tk.Frame(self, bg=BG_STATUS, height=24)
        statusbar.pack(fill="x")
        statusbar.pack_propagate(False)

        self.status_applied_var  = tk.StringVar(value="Applied: 0")
        self.status_detected_var = tk.StringVar(value="Detected: 0")
        self.status_exe_var      = tk.StringVar(value="")

        make_label(statusbar, fg=MUTED, bg=BG_STATUS, font=FONT_TINY,
                   textvariable=self.status_applied_var
                   ).pack(side="left", padx=12)
        make_label(statusbar, fg=MUTED, bg=BG_STATUS, font=FONT_TINY,
                   textvariable=self.status_detected_var
                   ).pack(side="left", padx=8)
        make_label(statusbar, fg=GREEN, bg=BG_STATUS, font=FONT_TINY,
                   textvariable=self.status_exe_var
                   ).pack(side="left", padx=8)

        self.code_rows: dict = {}

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
        for cid, found in self.detected.items():
            if found:
                self.applied[cid] = True

        self.scanned = True
        n_det = sum(1 for v in self.detected.values() if v)
        self.scan_btn.configure(text="Re-Scan", state="normal")
        self.scan_status_var.set(f"✓ Scanned — {n_det} codes detected")
        self.notice.pack_forget()
        self._refresh_all()
        self._update_statusbar()

    def select_section(self, section_id: str):
        for sid, item in self.sidebar_items.items():
            item.set_active(sid == section_id)
        self.active_section = section_id

        sec = next((s for s in self.sections_list if s["id"] == section_id), None)
        if sec:
            self.section_title_var.set(f"{sec['icon']}  {sec['label']}")

        for w in self.codes_inner.winfo_children():
            w.destroy()
        self.code_rows.clear()

        codes = self.codes_by_section.get(section_id, [])
        self.section_count_var.set(f"  {len(codes)} codes")

        if not codes:
            make_label(self.codes_inner,
                       "— لا يوجد أكواد في هاذا القسم بعد —",
                       fg=MUTED, bg=BG_PANEL, font=FONT_SMALL
                       ).pack(pady=24)
            return

        for code in codes:
            row = CodeRow(self.codes_inner, code, self)
            row.pack(fill="x", pady=2)
            self.code_rows[code["id"]] = row
            self._refresh_row(code["id"])

        self.codes_canvas.yview_moveto(0)

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
        if self.applied.get(code_id, False):
            messagebox.showinfo("Info",
                                "إزاله الكود قريباً في إصدار لاحق.\n"
                                "استخدم ملف النسخه الاحتياطيه.")
            return
        if code.get("dialog") == "mod_expansion":
            self._dialog_mod_expansion(code_id)
            return
        self._do_apply(code_id)

    def _dialog_mod_expansion(self, code_id: str):
        dlg = tk.Toplevel(self)
        dlg.title("Enemy Spawn Persistence")
        dlg.geometry("380x180")
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()

        make_label(dlg, "هل انت مفعل EnableModExpansion؟",
                   fg=ACCENT2, bg="#111", font=FONT_NORMAL
                   ).pack(pady=(20, 6))
        make_label(dlg, "سيؤثر هاذا على الكود اللي راح ينحط في EXE",
                   fg=MUTED, bg="#111", font=FONT_TINY
                   ).pack()

        btn_frame = tk.Frame(dlg, bg="#111")
        btn_frame.pack(pady=20)

        make_button(btn_frame, "✓  Yes",
                    lambda: [dlg.destroy(),
                             self._do_apply(code_id, mod_expansion=True)],
                    fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=9
                    ).pack(side="left", padx=8)
        make_button(btn_frame, "✗  No",
                    lambda: [dlg.destroy(),
                             self._do_apply(code_id, mod_expansion=False)],
                    fg=RED_SOFT, bg="#2a0a0a", active_bg="#4a1a1a", width=9
                    ).pack(side="left", padx=8)
        make_button(btn_frame, "Cancel", dlg.destroy,
                    fg=MUTED, bg="#1a1a1a", active_bg="#2a2a2a", width=9
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
            messagebox.showinfo(
                "✓ Applied",
                f"تم تطبيق الكود بنجاح:\n{self.code_by_id[code_id]['name']}"
            )
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
        self.status_applied_var.set(f"Applied: {n_applied}")
        self.status_detected_var.set(f"Detected: {n_detected}")
        self.status_exe_var.set("● EXE Loaded" if self.scanned else "")


# ═════════════════════════════════════════════════════════════════════════════
#  Entry point
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = RE4PatcherApp()
    app.mainloop()
