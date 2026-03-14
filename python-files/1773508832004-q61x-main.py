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
ORIG_FILE = os.path.join(CODES_DIR, "bio4_original.exe")

# ── colors ───────────────────────────────────────────────────────────────────
BG_MAIN    = "#0d0d0d"
BG_PANEL   = "#111111"
BG_SIDEBAR = "#0a0a0a"
BG_ROW     = "#141414"
BG_ROW_ON  = "#0d1a0d"
BG_ROW_LK  = "#0d0d0d"
BG_ROW_SEL = "#1a1a0a"
BG_HEADER  = "#0f0c00"
BG_TOPBAR  = "#0f0c00"
BG_PATHBAR = "#111111"
BG_NOTICE  = "#1a1200"
BG_STATUS  = "#0a0a0a"
BG_APPLY   = "#0a1a0a"

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
BORDER_SEL = "#5a5a2a"

FONT_TITLE  = ("Courier New", 13, "bold")
FONT_NORMAL = ("Courier New", 11)
FONT_SMALL  = ("Courier New", 10)
FONT_TINY   = ("Courier New", 9)
FONT_BOLD   = ("Courier New", 11, "bold")


# ═════════════════════════════════════════════════════════════════════════════
#  Arabic RTL helper
# ═════════════════════════════════════════════════════════════════════════════

def fix_ar(text):
    if not text:
        return text
    if not any("\u0600" <= c <= "\u06ff" for c in text):
        return text
    words = text.split(" ")
    return " ".join(reversed(words))


# ═════════════════════════════════════════════════════════════════════════════
#  Data helpers
# ═════════════════════════════════════════════════════════════════════════════

def load_json(path):
    if not os.path.exists(path):
        messagebox.showerror("Missing File", "Cannot find:\n" + path)
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def scan_exe(path, codes_info, codes_data):
    """
    Scan bio4.exe for ALL codes (not just detectable flag).
    For find_replace  -> look for the REPLACE bytes in exe (means already applied).
    For offset_paste / offset_replace -> compare bytes at offset.
    For variant codes -> check first patch of first variant.
    Returns {code_id: True/False}
    """
    results = {}
    try:
        with open(path, "rb") as f:
            exe_bytes = f.read()
    except Exception:
        return results

    for code in codes_info.get("codes", []):
        cid = code["id"]
        data = codes_data.get(cid, {})

        # get first patch (handle variants)
        if "variants" in data:
            first_variant = list(data["variants"].values())[0]
            patches = first_variant.get("patches", [])
        else:
            patches = data.get("patches", [])

        if not patches:
            results[cid] = False
            continue

        first = patches[0]
        try:
            ptype = first["type"]
            if ptype == "find_replace":
                # already applied = replace bytes present
                needle = bytes.fromhex(first["replace"].replace(" ", ""))
                results[cid] = needle in exe_bytes
            elif ptype in ("offset_paste", "offset_replace"):
                offset = int(first["offset"], 16)
                needle = bytes.fromhex(first["bytes"].replace(" ", ""))
                results[cid] = exe_bytes[offset:offset + len(needle)] == needle
            else:
                results[cid] = False
        except Exception:
            results[cid] = False

    return results


def apply_patch(exe_path, code_id, codes_data, mod_expansion=None):
    data = codes_data.get(code_id)
    if not data:
        return False, "No patch data for '" + code_id + "'"

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
                    return False, "Pattern not found:\n" + patch["find"][:40] + "..."
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


def revert_patch(exe_path, orig_path, code_id, codes_data, mod_expansion=None):
    """
    Revert a code using bio4_original.exe as reference for offset_paste patches.
    find_replace  -> swaps find/replace (apply the original bytes back).
    offset_paste / offset_replace -> reads same length from original exe.
    """
    data = codes_data.get(code_id)
    if not data:
        return False, "No patch data for '" + code_id + "'"

    # load both exes
    try:
        with open(exe_path, "rb") as f:
            exe = bytearray(f.read())
    except Exception as e:
        return False, str(e)

    orig_bytes = None
    if os.path.isfile(orig_path):
        try:
            with open(orig_path, "rb") as f:
                orig_bytes = f.read()
        except Exception:
            orig_bytes = None

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
                # reverse: find the REPLACE bytes, put FIND bytes back
                find_b    = bytes.fromhex(patch["find"].replace(" ", ""))
                replace_b = bytes.fromhex(patch["replace"].replace(" ", ""))
                idx = exe.find(replace_b)
                if idx == -1:
                    return False, "Cannot find modified bytes to revert:\n" + patch["replace"][:40] + "..."
                exe[idx:idx + len(replace_b)] = find_b

            elif ptype in ("offset_paste", "offset_replace"):
                off    = int(patch["offset"], 16)
                length = len(bytes.fromhex(patch["bytes"].replace(" ", "")))
                if orig_bytes is None:
                    return False, "bio4_original.exe not found in the_codes folder.\nCannot revert offset-based patch for:\n" + code_id
                orig_chunk = orig_bytes[off:off + length]
                if len(orig_chunk) != length:
                    return False, "Original EXE too short at offset " + patch["offset"]
                exe[off:off + length] = orig_chunk

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
#  CodeRow
# ═════════════════════════════════════════════════════════════════════════════

class CodeRow(tk.Frame):
    def __init__(self, parent, code, app, **kw):
        super().__init__(parent, bg=BG_ROW,
                         highlightthickness=1,
                         highlightbackground=BORDER, **kw)
        self.code      = code
        self.app       = app
        self._expanded = False
        self.selected  = False
        self._build()

    def _build(self):
        top = tk.Frame(self, bg=BG_ROW)
        top.pack(fill="x", padx=6, pady=4)

        # ── checkbox (queue for Apply Selected) ──
        self.sel_var = tk.IntVar(value=0)
        self.sel_chk = tk.Checkbutton(
            top, variable=self.sel_var,
            bg=BG_ROW, activebackground=BG_ROW,
            fg=ACCENT, selectcolor="#1a1a1a",
            relief="flat", bd=0,
            command=self._on_select
        )
        self.sel_chk.pack(side="left", padx=(0, 2))

        # ── ON/OFF toggle button ──
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

        # ── status badge [L] / blank ──
        self.status_var = tk.StringVar(value="")
        self.status_lbl = tk.Label(
            top, textvariable=self.status_var,
            font=FONT_TINY, fg=MUTED, bg=BG_ROW, width=3,
            anchor="center"
        )
        self.status_lbl.pack(side="left", padx=(0, 4))

        # ── name + desc ──
        info_frame = tk.Frame(top, bg=BG_ROW)
        info_frame.pack(side="left", fill="x", expand=True)

        self.name_lbl = tk.Label(
            info_frame, text=self.code["name"],
            font=FONT_NORMAL, fg=TEXT_MAIN, bg=BG_ROW,
            anchor="w", justify="left"
        )
        self.name_lbl.pack(anchor="w")

        self.desc_lbl = tk.Label(
            info_frame, text=fix_ar(self.code["desc"]),
            font=FONT_TINY, fg=MUTED, bg=BG_ROW,
            anchor="w", justify="left", wraplength=500
        )
        self.desc_lbl.pack(anchor="w")

        # ── expand arrow (only if notes) ──
        if self.code.get("notes"):
            self.arrow_btn = tk.Button(
                top, text="[v]", width=3, font=FONT_TINY,
                fg=MUTED, bg=BG_ROW,
                activeforeground=MUTED, activebackground=BG_ROW,
                relief="flat", bd=0, cursor="hand2",
                command=self._toggle_notes
            )
            self.arrow_btn.pack(side="right")

        # ── notes frame ──
        self.notes_frame = tk.Frame(self, bg="#0d0d00")
        for note in self.code.get("notes", []):
            tk.Label(
                self.notes_frame,
                text=fix_ar(note),
                font=FONT_TINY, fg=ORANGE, bg="#0d0d00",
                anchor="w", justify="left"
            ).pack(anchor="w", padx=8, pady=1)

    def _toggle_notes(self):
        self._expanded = not self._expanded
        if self._expanded:
            self.notes_frame.pack(fill="x")
            self.arrow_btn.configure(text="[^]")
        else:
            self.notes_frame.pack_forget()
            self.arrow_btn.configure(text="[v]")

    def _on_toggle(self):
        self.app.handle_toggle(self.code["id"])

    def _on_select(self):
        self.selected = bool(self.sel_var.get())
        self.app.on_row_select_change()

    def refresh(self, applied, locked, detected):
        if detected and not applied:
            applied = True

        has_arrow = hasattr(self, "arrow_btn")

        # checkbox: disabled if locked or already applied
        if locked or applied:
            self.sel_chk.configure(state="disabled")
            self.sel_var.set(0)
            self.selected = False
        else:
            self.sel_chk.configure(state="normal")

        if locked:
            bg = BG_ROW_LK
            self.configure(bg=bg, highlightbackground=BORDER_LK)
            self.toggle_btn.configure(
                text="OFF", fg=TEXT_LOCK, bg="#1a1a1a",
                highlightbackground="#333", state="disabled"
            )
            self.status_var.set("[L]")
            self.status_lbl.configure(fg="#c85a2a", bg=bg)
            self.name_lbl.configure(fg=TEXT_LOCK, bg=bg, font=FONT_NORMAL)
            self.desc_lbl.configure(bg=bg)
            self.sel_chk.configure(bg=bg, activebackground=bg)
            if has_arrow:
                self.arrow_btn.configure(bg=bg, activebackground=bg)
            self.notes_frame.configure(bg="#0d0d00")

        elif applied:
            bg = BG_ROW_ON
            self.configure(bg=bg, highlightbackground=BORDER_ON)
            self.toggle_btn.configure(
                text="ON", fg=GREEN, bg="#2a5a2a",
                highlightbackground=GREEN, state="normal"
            )
            self.status_var.set("")
            self.status_lbl.configure(fg=MUTED, bg=bg)
            self.name_lbl.configure(fg="#e8e0c0", bg=bg, font=FONT_BOLD)
            self.desc_lbl.configure(bg=bg)
            self.sel_chk.configure(bg=bg, activebackground=bg)
            if has_arrow:
                self.arrow_btn.configure(bg=bg, activebackground=bg)

        else:
            bg = BG_ROW_SEL if self.selected else BG_ROW
            border = BORDER_SEL if self.selected else BORDER
            self.configure(bg=bg, highlightbackground=border)
            self.toggle_btn.configure(
                text="OFF", fg=MUTED, bg="#1a1a1a",
                highlightbackground="#444", state="normal"
            )
            self.status_var.set("")
            self.status_lbl.configure(fg=MUTED, bg=bg)
            self.name_lbl.configure(fg=TEXT_MAIN, bg=bg, font=FONT_NORMAL)
            self.desc_lbl.configure(bg=bg)
            self.sel_chk.configure(bg=bg, activebackground=bg)
            if has_arrow:
                self.arrow_btn.configure(bg=bg, activebackground=bg)


# ═════════════════════════════════════════════════════════════════════════════
#  SidebarItem
# ═════════════════════════════════════════════════════════════════════════════

class SidebarItem(tk.Frame):
    def __init__(self, parent, section, app, **kw):
        super().__init__(parent, bg=BG_SIDEBAR, **kw)
        self.section = section
        self.app     = app

        self.indicator = tk.Frame(self, bg=BG_SIDEBAR, width=3)
        self.indicator.pack(side="left", fill="y")

        label = section["label"]
        self.btn = tk.Button(
            self, text=label,
            font=FONT_SMALL, fg=TEXT_DIM, bg=BG_SIDEBAR,
            activeforeground=ACCENT2, activebackground="#1a1200",
            anchor="w", relief="flat", bd=0, cursor="hand2",
            command=lambda: app.select_section(section["id"])
        )
        self.btn.pack(side="left", fill="x", expand=True, ipady=6)

    def set_active(self, active):
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

        self.title("RE4 Code Patcher Tool -- Preview")
        self.geometry("1000x680")
        self.minsize(820, 560)
        self.configure(bg=BG_MAIN)

        self.exe_path       = tk.StringVar()
        self.scanned        = False
        self.detected       = {}
        self.applied        = {}
        self.active_section = None

        self.codes_info = load_json(INFO_FILE)
        self.codes_data = load_json(DATA_FILE)

        self.sections_list    = self.codes_info["sections"]
        self.all_codes        = self.codes_info["codes"]
        self.code_by_id       = {c["id"]: c for c in self.all_codes}
        self.codes_by_section = {}
        for c in self.all_codes:
            self.codes_by_section.setdefault(c["section"], []).append(c)

        self._build_ui()
        self.select_section(self.sections_list[0]["id"])

    # ── UI ────────────────────────────────────────────────────────────────────

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
        make_label(topbar, "by YEMENI",
                   fg="#888", bg=BG_TOPBAR, font=FONT_TINY
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
        make_label(
            self.notice,
            fix_ar("[!] حط مسار bio4.exe واضغط Scan عشان تشوف وتفعل الاكواد"),
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

        self.sidebar_items = {}
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

        # codes scroll area
        codes_outer = tk.Frame(right, bg=BG_PANEL)
        codes_outer.pack(fill="both", expand=True, padx=10, pady=(8, 0))

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

        # Apply Selected bar
        apply_bar = tk.Frame(right, bg=BG_APPLY,
                             highlightthickness=1,
                             highlightbackground="#2a4a2a")
        apply_bar.pack(fill="x", padx=10, pady=6)

        self.selected_count_var = tk.StringVar(value="0 selected")
        make_label(apply_bar, fg=MUTED, bg=BG_APPLY, font=FONT_TINY,
                   textvariable=self.selected_count_var
                   ).pack(side="left", padx=10, pady=6)

        make_button(apply_bar, "Select All", self._select_all,
                    fg=ACCENT, bg="#2a2a0a", active_bg="#3a3a1a", width=10
                    ).pack(side="left", padx=4, pady=4)
        make_button(apply_bar, "Clear", self._clear_selection,
                    fg=MUTED, bg="#1a1a1a", active_bg="#2a2a2a", width=8
                    ).pack(side="left", padx=4, pady=4)
        self.apply_btn = make_button(
            apply_bar, "Apply Selected", self._apply_selected,
            fg=GREEN, bg="#1a3a1a", active_bg="#2a5a2a", width=14
        )
        self.apply_btn.pack(side="right", padx=10, pady=4)

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

        self.code_rows = {}

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

        self.detected = scan_exe(path, self.codes_info, self.codes_data)
        for cid, found in self.detected.items():
            if found:
                self.applied[cid] = True

        self.scanned = True
        n_det = sum(1 for v in self.detected.values() if v)
        self.scan_btn.configure(text="Re-Scan", state="normal")
        orig_status = "  |  [orig: OK]" if os.path.isfile(ORIG_FILE) else "  |  [orig: missing - revert disabled]"
        self.scan_status_var.set("Scanned -- " + str(n_det) + " codes detected" + orig_status)
        self.notice.pack_forget()
        self._refresh_all()
        self._update_statusbar()

    def select_section(self, section_id):
        for sid, item in self.sidebar_items.items():
            item.set_active(sid == section_id)
        self.active_section = section_id

        sec = next((s for s in self.sections_list if s["id"] == section_id), None)
        if sec:
            self.section_title_var.set(sec["label"])

        for w in self.codes_inner.winfo_children():
            w.destroy()
        self.code_rows.clear()

        codes = self.codes_by_section.get(section_id, [])
        self.section_count_var.set("  " + str(len(codes)) + " codes")

        if not codes:
            make_label(self.codes_inner,
                       "-- No codes in this section yet --",
                       fg=MUTED, bg=BG_PANEL, font=FONT_SMALL
                       ).pack(pady=24)
            self._update_apply_bar()
            return

        for code in codes:
            row = CodeRow(self.codes_inner, code, self)
            row.pack(fill="x", pady=2)
            self.code_rows[code["id"]] = row
            self._refresh_row(code["id"])

        self.codes_canvas.yview_moveto(0)
        self._update_apply_bar()

    def _is_unlocked(self, code_id):
        if not self.scanned:
            return False
        code = self.code_by_id.get(code_id, {})
        for dep in code.get("requires", []):
            if not (self.applied.get(dep) or self.detected.get(dep)):
                return False
        return True

    def handle_toggle(self, code_id):
        if not self._is_unlocked(code_id):
            return
        code = self.code_by_id.get(code_id, {})

        if self.applied.get(code_id, False):
            # revert
            exe = self.exe_path.get().strip()
            if not exe or not os.path.isfile(exe):
                messagebox.showerror("Error", "EXE path is invalid.")
                return
            ok, msg = revert_patch(exe, ORIG_FILE, code_id, self.codes_data)
            if ok:
                self.applied[code_id] = False
                self._refresh_all()
                self._update_statusbar()
                self._update_apply_bar()
            else:
                messagebox.showerror("Revert Failed", msg)
            return

        if code.get("dialog") == "mod_expansion":
            self._dialog_mod_expansion(code_id)
            return
        self._do_apply(code_id)

    def _dialog_mod_expansion(self, code_id):
        dlg = tk.Toplevel(self)
        dlg.title("Enemy Spawn Persistence")
        dlg.geometry("380x180")
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()

        make_label(dlg, fix_ar("هل انت مفعل EnableModExpansion؟"),
                   fg=ACCENT2, bg="#111", font=FONT_NORMAL
                   ).pack(pady=(20, 6))
        make_label(dlg, fix_ar("سيؤثر هاذا على الكود اللي راح ينحط في EXE"),
                   fg=MUTED, bg="#111", font=FONT_TINY
                   ).pack()

        btn_frame = tk.Frame(dlg, bg="#111")
        btn_frame.pack(pady=20)

        make_button(btn_frame, "[Y] Yes",
                    lambda: [dlg.destroy(),
                             self._do_apply(code_id, mod_expansion=True)],
                    fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=9
                    ).pack(side="left", padx=8)
        make_button(btn_frame, "[N] No",
                    lambda: [dlg.destroy(),
                             self._do_apply(code_id, mod_expansion=False)],
                    fg=RED_SOFT, bg="#2a0a0a", active_bg="#4a1a1a", width=9
                    ).pack(side="left", padx=8)
        make_button(btn_frame, "Cancel", dlg.destroy,
                    fg=MUTED, bg="#1a1a1a", active_bg="#2a2a2a", width=9
                    ).pack(side="left", padx=8)

    def _do_apply(self, code_id, mod_expansion=None):
        exe = self.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "EXE path is invalid.")
            return
        ok, msg = apply_patch(exe, code_id, self.codes_data, mod_expansion)
        if ok:
            self.applied[code_id] = True
            # refresh ALL rows so dependent codes unlock immediately
            self._refresh_all()
            self._update_statusbar()
            self._update_apply_bar()
            messagebox.showinfo(
                "[+] Applied",
                "Code applied:\n" + self.code_by_id[code_id]["name"]
            )
        else:
            messagebox.showerror("Error", "Failed:\n" + msg)

    # ── Apply Selected ────────────────────────────────────────────────────────

    def on_row_select_change(self):
        self._update_apply_bar()

    def _update_apply_bar(self):
        n = sum(1 for r in self.code_rows.values() if r.selected)
        self.selected_count_var.set(str(n) + " selected")

    def _select_all(self):
        for cid, row in self.code_rows.items():
            if self._is_unlocked(cid) and not self.applied.get(cid, False):
                row.sel_var.set(1)
                row.selected = True
        self._refresh_all()
        self._update_apply_bar()

    def _clear_selection(self):
        for row in self.code_rows.values():
            row.sel_var.set(0)
            row.selected = False
        self._refresh_all()
        self._update_apply_bar()

    def _apply_selected(self):
        exe = self.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error", "Please select a valid bio4.exe first.")
            return

        queue = [cid for cid, row in self.code_rows.items()
                 if row.selected and not self.applied.get(cid, False)]

        if not queue:
            messagebox.showinfo("Info", "No codes selected.")
            return

        needs_dialog = [c for c in queue
                        if self.code_by_id.get(c, {}).get("dialog") == "mod_expansion"]
        if needs_dialog:
            self._dialog_mod_expansion_batch(queue)
        else:
            self._run_apply_queue(queue, mod_expansion=None)

    def _dialog_mod_expansion_batch(self, full_queue):
        dlg = tk.Toplevel(self)
        dlg.title("Enemy Spawn Persistence")
        dlg.geometry("380x180")
        dlg.resizable(False, False)
        dlg.configure(bg="#111")
        dlg.grab_set()

        make_label(dlg, fix_ar("هل انت مفعل EnableModExpansion؟"),
                   fg=ACCENT2, bg="#111", font=FONT_NORMAL
                   ).pack(pady=(20, 6))
        make_label(dlg, fix_ar("سيؤثر هاذا على الكود اللي راح ينحط في EXE"),
                   fg=MUTED, bg="#111", font=FONT_TINY
                   ).pack()

        btn_frame = tk.Frame(dlg, bg="#111")
        btn_frame.pack(pady=20)

        make_button(btn_frame, "[Y] Yes",
                    lambda: [dlg.destroy(),
                             self._run_apply_queue(full_queue, mod_expansion=True)],
                    fg=GREEN, bg="#1a2a0a", active_bg="#2a4a1a", width=9
                    ).pack(side="left", padx=8)
        make_button(btn_frame, "[N] No",
                    lambda: [dlg.destroy(),
                             self._run_apply_queue(full_queue, mod_expansion=False)],
                    fg=RED_SOFT, bg="#2a0a0a", active_bg="#4a1a1a", width=9
                    ).pack(side="left", padx=8)
        make_button(btn_frame, "Cancel", dlg.destroy,
                    fg=MUTED, bg="#1a1a1a", active_bg="#2a2a2a", width=9
                    ).pack(side="left", padx=8)

    def _run_apply_queue(self, queue, mod_expansion=None):
        exe = self.exe_path.get().strip()
        success, failed = [], []

        for code_id in queue:
            me = mod_expansion if self.code_by_id.get(
                code_id, {}).get("dialog") == "mod_expansion" else None
            ok, msg = apply_patch(exe, code_id, self.codes_data, me)
            if ok:
                self.applied[code_id] = True
                success.append(code_id)
            else:
                failed.append((code_id, msg))

        self._refresh_all()
        self._update_statusbar()
        self._update_apply_bar()

        summary = "Applied " + str(len(success)) + " code(s) successfully."
        if failed:
            summary += "\n\nFailed:\n"
            for cid, err in failed:
                summary += "- " + self.code_by_id[cid]["name"] + "\n  " + err + "\n"
            messagebox.showwarning("Done with errors", summary)
        else:
            messagebox.showinfo("[+] Done", summary)

    # ── refresh ───────────────────────────────────────────────────────────────

    def _refresh_row(self, code_id):
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
        self.status_applied_var.set("Applied: " + str(n_applied))
        self.status_detected_var.set("Detected: " + str(n_detected))
        self.status_exe_var.set("[OK] EXE Loaded" if self.scanned else "")


# ═════════════════════════════════════════════════════════════════════════════
#  Entry point
# ═════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    app = RE4PatcherApp()
    app.mainloop()
