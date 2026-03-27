"""
RE4 Master Editor - Main launcher
Integrates all RE4 modding tools in one unified interface.
"""

import sys
import os
import ctypes
import tkinter as tk
from tkinter import filedialog, messagebox

# ── hide console on Windows ───────────────────────────────────────────────────
def _hide_console():
    try:
        if sys.platform.startswith("win"):
            ctypes.windll.user32.ShowWindow(
                ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass

_hide_console()

# ── paths ─────────────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

TOOLS = [
    {"id": "code_manager",  "label": "RE4 CODE MANAGER",  "folder": "RE4 Code Manager"},
    {"id": "osd_tool",      "label": "OSD TOOL",           "folder": "OSD Tool"},
    {"id": "aev_option",    "label": "AEV OPTION",         "folder": "AEV Option"},
    {"id": "mdt_color",     "label": "MDT COLOR",          "folder": "MDT Color"},
    {"id": "room_init",     "label": "ROOM INIT",          "folder": "Room Init"},
    {"id": "avl_editor",    "label": "AVL EDITOR",         "folder": "AVL Editor"},
]

# ── colors ────────────────────────────────────────────────────────────────────
BG_MAIN    = "#0a0a0a"
BG_TOPBAR  = "#0d0d0d"
BG_NAV     = "#0f0f0f"
BG_CONTENT = "#0c0c0c"
ACCENT     = "#c8a035"       # gold
ACCENT2    = "#7cfc7c"       # green
MUTED      = "#555555"
TEXT_MAIN  = "#d0d0d0"
TEXT_DIM   = "#888888"
BORDER     = "#222222"
NAV_ACTIVE = "#1a1500"
NAV_BORDER = "#c8a035"

FONT_TITLE  = ("Courier New", 14, "bold")
FONT_NAV    = ("Courier New", 9,  "bold")
FONT_SMALL  = ("Courier New", 9)
FONT_TINY   = ("Courier New", 8)
FONT_NORMAL = ("Courier New", 10)


# ── helpers ───────────────────────────────────────────────────────────────────
def make_label(parent, text, fg=TEXT_MAIN, bg=BG_MAIN,
               font=FONT_SMALL, **kw):
    return tk.Label(parent, text=text, fg=fg, bg=bg, font=font, **kw)


def make_button(parent, text, command, fg=ACCENT2, bg="#1a2a0a",
                active_bg="#2a4a1a", font=FONT_SMALL, **kw):
    return tk.Button(parent, text=text, command=command,
                     fg=fg, bg=bg, activeforeground=fg,
                     activebackground=active_bg, font=font,
                     relief="flat", bd=0, cursor="hand2",
                     highlightthickness=1,
                     highlightbackground=fg, **kw)


# ── Code Manager embedded panel ───────────────────────────────────────────────
class CodeManagerPanel(tk.Frame):
    """Embeds the RE4 Code Manager inside the Master Editor."""

    def __init__(self, parent, master_app, **kw):
        super().__init__(parent, bg=BG_CONTENT, **kw)
        self.master_app = master_app
        self._app = None
        self._built = False

    def activate(self):
        """Called when this panel becomes visible."""
        if not self._built:
            self._build()
            self._built = True

    def _build(self):
        # locate code manager main.py
        cm_dir  = os.path.join(BASE_DIR, "RE4 Code Manager")
        cm_main = os.path.join(cm_dir, "main.py")

        if not os.path.isdir(cm_dir) or not os.path.isfile(cm_main):
            self._show_missing(cm_dir)
            return

        # inject the EXE path and embed
        try:
            self._embed_code_manager(cm_dir, cm_main)
        except Exception as e:
            tk.Label(self, text="Error loading Code Manager:\n" + str(e),
                     fg="#ff6060", bg=BG_CONTENT,
                     font=FONT_SMALL).pack(pady=40)

    def _show_missing(self, expected_dir):
        f = tk.Frame(self, bg=BG_CONTENT)
        f.pack(expand=True)
        make_label(f, "RE4 Code Manager folder not found.",
                   fg="#ff6060", bg=BG_CONTENT, font=FONT_NORMAL).pack(pady=8)
        make_label(f, f"Expected: {expected_dir}",
                   fg=TEXT_DIM, bg=BG_CONTENT, font=FONT_TINY).pack()

    def _embed_code_manager(self, cm_dir, cm_main):
        """Run Code Manager's main.py in embedded mode."""
        import importlib.util, sys as _sys

        # inject shared exe_path from master
        _sys.path.insert(0, cm_dir)

        spec   = importlib.util.spec_from_file_location("cm_main", cm_main)
        module = importlib.util.module_from_spec(spec)

        # patch: tell the module it's embedded + pass exe getter
        module.__EMBEDDED__       = True
        module.__MASTER_EXE_VAR__ = self.master_app.exe_path
        module.__MASTER_FRAME__   = self

        spec.loader.exec_module(module)

        # build the app inside our frame
        app = module.RE4PatcherApp.__new__(module.RE4PatcherApp)
        app.__class__.__bases__ = (tk.Frame,)   # rebind parent to Frame

        # proper embedded init — just build UI into self
        self._fallback_embed(module)

    def _fallback_embed(self, module):
        """Fallback: show scan button + forward exe from master."""
        # status label
        status = make_label(self,
                            "[!] Select bio4.exe above and press Scan",
                            fg=ACCENT, bg=BG_CONTENT, font=FONT_SMALL)
        status.pack(pady=(10, 4), padx=16, anchor="w")

        # scan button centered
        btn_frame = tk.Frame(self, bg=BG_CONTENT)
        btn_frame.pack(pady=4)
        make_button(btn_frame, "  ▶  SCAN EXE  ",
                    command=self._do_scan,
                    fg="#0a0a0a", bg=ACCENT,
                    active_bg="#b8902a",
                    font=("Courier New", 11, "bold"),
                    width=18, pady=6
                    ).pack()

        # placeholder content area
        self._content = tk.Frame(self, bg=BG_CONTENT)
        self._content.pack(fill="both", expand=True, padx=8, pady=4)

        make_label(self._content,
                   "Code Manager will appear here after scanning.",
                   fg=TEXT_DIM, bg=BG_CONTENT, font=FONT_SMALL
                   ).pack(pady=40)

    def _do_scan(self):
        exe = self.master_app.exe_path.get().strip()
        if not exe or not os.path.isfile(exe):
            messagebox.showerror("Error",
                "Please select bio4.exe first (top bar).")
            return
        messagebox.showinfo("Scan", "Scanning: " + exe)


# ── Coming Soon panel ─────────────────────────────────────────────────────────
class ComingSoonPanel(tk.Frame):
    def __init__(self, parent, tool_name, **kw):
        super().__init__(parent, bg=BG_CONTENT, **kw)
        self.tool_name = tool_name
        self._build()

    def activate(self): pass

    def _build(self):
        f = tk.Frame(self, bg=BG_CONTENT)
        f.place(relx=0.5, rely=0.5, anchor="center")

        make_label(f, self.tool_name,
                   fg=ACCENT, bg=BG_CONTENT, font=FONT_TITLE).pack(pady=(0, 16))

        make_label(f, "[ COMING SOON ]",
                   fg=MUTED, bg=BG_CONTENT,
                   font=("Courier New", 12, "bold")).pack()

        make_label(f, "This module is under development.",
                   fg=TEXT_DIM, bg=BG_CONTENT, font=FONT_SMALL).pack(pady=(12, 0))


# ── Main App ──────────────────────────────────────────────────────────────────
class RE4MasterEditor(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("RE4 Master Editor")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(bg=BG_MAIN)

        self.exe_path      = tk.StringVar()
        self.active_tool   = tk.StringVar(value="")
        self.panels        = {}
        self.nav_buttons   = {}

        self._build_ui()
        self._switch_tool("code_manager")

    def _build_ui(self):
        # ── top bar ──────────────────────────────────────────────────────────
        topbar = tk.Frame(self, bg=BG_TOPBAR,
                          highlightthickness=1,
                          highlightbackground="#1a1500")
        topbar.pack(fill="x")

        # logo
        make_label(topbar, "RE4",
                   fg=ACCENT, bg=BG_TOPBAR,
                   font=("Courier New", 13, "bold")
                   ).pack(side="left", padx=(14, 0), pady=8)
        make_label(topbar, " MASTER EDITOR",
                   fg=TEXT_MAIN, bg=BG_TOPBAR,
                   font=("Courier New", 13, "bold")
                   ).pack(side="left", pady=8)
        make_label(topbar, "  v1.0.0",
                   fg=MUTED, bg=BG_TOPBAR,
                   font=FONT_TINY
                   ).pack(side="left", pady=8)

        # EXE path bar (right side)
        path_frame = tk.Frame(topbar, bg=BG_TOPBAR)
        path_frame.pack(side="right", padx=10, pady=6)

        make_label(path_frame, "bio4.exe:",
                   fg=TEXT_DIM, bg=BG_TOPBAR,
                   font=FONT_TINY).pack(side="left", padx=(0, 6))

        self.path_entry = tk.Entry(
            path_frame, textvariable=self.exe_path,
            font=FONT_SMALL, fg=ACCENT2, bg="#0d1a0d",
            insertbackground=ACCENT2,
            relief="flat", bd=0,
            highlightthickness=1, highlightbackground="#2a5a2a",
            width=38
        )
        self.path_entry.pack(side="left", ipady=3)

        make_button(path_frame, " Browse ",
                    self._browse_exe,
                    fg=ACCENT, bg="#1a1500",
                    active_bg="#2a2000",
                    font=FONT_TINY
                    ).pack(side="left", padx=6)

        # ── nav bar ───────────────────────────────────────────────────────────
        navbar = tk.Frame(self, bg=BG_NAV,
                          highlightthickness=1,
                          highlightbackground="#1a1a1a")
        navbar.pack(fill="x")

        # separator line under topbar
        tk.Frame(self, bg=ACCENT, height=1).pack(fill="x")

        nav_inner = tk.Frame(navbar, bg=BG_NAV)
        nav_inner.pack(side="left", pady=0)

        for tool in TOOLS:
            tid   = tool["id"]
            label = tool["label"]
            btn   = tk.Button(
                nav_inner,
                text=label,
                font=FONT_NAV,
                fg=MUTED,
                bg=BG_NAV,
                activeforeground=ACCENT,
                activebackground=NAV_ACTIVE,
                relief="flat", bd=0,
                cursor="hand2",
                padx=18, pady=8,
                command=lambda t=tid: self._switch_tool(t)
            )
            btn.pack(side="left")
            self.nav_buttons[tid] = btn

        # vertical separator
        tk.Frame(nav_inner, bg="#1a1a1a", width=1).pack(side="left", fill="y")

        # bottom border of nav
        tk.Frame(self, bg="#1a1a1a", height=1).pack(fill="x")

        # ── content area ──────────────────────────────────────────────────────
        self.content = tk.Frame(self, bg=BG_CONTENT)
        self.content.pack(fill="both", expand=True)

        # build all panels
        for tool in TOOLS:
            tid = tool["id"]
            if tid == "code_manager":
                panel = CodeManagerPanel(self.content, self)
            else:
                panel = ComingSoonPanel(self.content, tool["label"])
            panel.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.panels[tid] = panel

        # ── status bar ────────────────────────────────────────────────────────
        tk.Frame(self, bg="#111", height=1).pack(fill="x")
        statusbar = tk.Frame(self, bg="#0d0d0d")
        statusbar.pack(fill="x")

        self.status_var = tk.StringVar(value="Ready")
        make_label(statusbar, "",  # spacer
                   fg=MUTED, bg="#0d0d0d",
                   font=FONT_TINY).pack(side="left", padx=10, pady=3)
        tk.Label(statusbar, textvariable=self.status_var,
                 fg=TEXT_DIM, bg="#0d0d0d",
                 font=FONT_TINY).pack(side="left")

        make_label(statusbar, "by YEMENI",
                   fg=MUTED, bg="#0d0d0d",
                   font=FONT_TINY).pack(side="right", padx=12, pady=3)

    def _switch_tool(self, tool_id):
        # hide all
        for tid, panel in self.panels.items():
            panel.lower()
            btn = self.nav_buttons.get(tid)
            if btn:
                btn.configure(fg=MUTED, bg=BG_NAV,
                               relief="flat",
                               highlightthickness=0)

        # show selected
        panel = self.panels.get(tool_id)
        if panel:
            panel.lift()
            panel.activate()

        btn = self.nav_buttons.get(tool_id)
        if btn:
            btn.configure(fg=ACCENT, bg=NAV_ACTIVE,
                           relief="flat",
                           highlightthickness=1,
                           highlightbackground=NAV_BORDER)

        self.active_tool.set(tool_id)
        label = next((t["label"] for t in TOOLS if t["id"] == tool_id), tool_id)
        self.status_var.set("Module: " + label)

    def _browse_exe(self):
        path = filedialog.askopenfilename(
            title="Select bio4.exe",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
        )
        if path:
            self.exe_path.set(path)
            self.status_var.set("EXE: " + os.path.basename(path))


if __name__ == "__main__":
    app = RE4MasterEditor()
    app.mainloop()
