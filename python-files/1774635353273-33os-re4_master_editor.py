"""
RE4 Master Editor v1.0.0
========================
Unified RE4 modding suite.
All tool modules are embedded in this single file.

Structure expected next to this EXE:
  RE4 MASTER EDITOR/
    RE4 CODE MANAGER/
      the_codes/
      the_files/
      Profiles/
      Modified files/
    OSD EDITOR/
    CNS EDITOR/
    SND EDITOR/
    AEV OPTION EDITOR/
    MDT COLOR EDITOR/
    ROOM INIT EDITOR/
    AVL EDITOR/
"""

import sys
import os
import ctypes
import json
import tkinter as tk
from tkinter import filedialog, messagebox

# ── hide console ──────────────────────────────────────────────────────────────
def _hide_console():
    try:
        if sys.platform.startswith("win"):
            ctypes.windll.user32.ShowWindow(
                ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except Exception:
        pass

_hide_console()

# ── base path (works for .py and .exe) ───────────────────────────────────────
if getattr(sys, "frozen", False):
    _ROOT = os.path.dirname(sys.executable)
else:
    _ROOT = os.path.dirname(os.path.abspath(__file__))

MASTER_DIR = os.path.join(_ROOT, "RE4 MASTER EDITOR")

# ── settings (global, shared across modules) ─────────────────────────────────
_SETTINGS_FILE = os.path.join(MASTER_DIR, "master_settings.json")

def load_master_settings():
    defaults = {"lang": "en", "remember_exe": True, "last_exe": ""}
    if os.path.isfile(_SETTINGS_FILE):
        try:
            with open(_SETTINGS_FILE, encoding="utf-8") as f:
                saved = json.load(f)
            defaults.update(saved)
        except Exception:
            pass
    return defaults

def save_master_settings(s):
    try:
        os.makedirs(os.path.dirname(_SETTINGS_FILE), exist_ok=True)
        with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(s, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

MASTER_SETTINGS = load_master_settings()
CURRENT_LANG    = MASTER_SETTINGS.get("lang", "en")

# ── colors & fonts ────────────────────────────────────────────────────────────
BG_MAIN     = "#080808"
BG_TOPBAR   = "#0c0c0c"
BG_NAV      = "#0e0e0e"
BG_CONTENT  = "#0b0b0b"
BG_WELCOME  = "#090909"
ACCENT      = "#c8a035"
ACCENT2     = "#7cfc7c"
MUTED       = "#4a4a4a"
TEXT_MAIN   = "#cccccc"
TEXT_DIM    = "#777777"
BORDER      = "#1e1e1e"
NAV_ACTIVE  = "#16110a"
NAV_BORDER  = "#c8a035"
RED         = "#e05050"

FONT_TITLE  = ("Courier New", 15, "bold")
FONT_NAV    = ("Courier New", 9,  "bold")
FONT_SMALL  = ("Courier New", 9)
FONT_TINY   = ("Courier New", 8)
FONT_NORMAL = ("Courier New", 10)
FONT_BOLD   = ("Courier New", 10, "bold")

# ── tools registry ────────────────────────────────────────────────────────────
TOOLS = [
    {"id": "code_manager",    "label": "RE4 CODE MANAGER",    "folder": "RE4 CODE MANAGER"},
    {"id": "osd_editor",      "label": "OSD EDITOR",           "folder": "OSD EDITOR"},
    {"id": "cns_editor",      "label": "CNS EDITOR",           "folder": "CNS EDITOR"},
    {"id": "snd_editor",      "label": "SND EDITOR",           "folder": "SND EDITOR"},
    {"id": "aev_editor",      "label": "AEV OPTION EDITOR",    "folder": "AEV OPTION EDITOR"},
    {"id": "mdt_editor",      "label": "MDT COLOR EDITOR",     "folder": "MDT COLOR EDITOR"},
    {"id": "room_init_editor","label": "ROOM INIT EDITOR",     "folder": "ROOM INIT EDITOR"},
    {"id": "avl_editor",      "label": "AVL EDITOR",           "folder": "AVL EDITOR"},
]

# ── helpers ───────────────────────────────────────────────────────────────────
def make_label(parent, text, fg=TEXT_MAIN, bg=BG_MAIN, font=FONT_SMALL, **kw):
    return tk.Label(parent, text=text, fg=fg, bg=bg, font=font, **kw)

def make_button(parent, text, command, fg=ACCENT2, bg="#1a2a0a",
                active_bg="#2a4a1a", font=FONT_SMALL, **kw):
    return tk.Button(parent, text=text, command=command,
                     fg=fg, bg=bg, activeforeground=fg,
                     activebackground=active_bg, font=font,
                     relief="flat", bd=0, cursor="hand2",
                     highlightthickness=1, highlightbackground=fg, **kw)

# ── Welcome Panel ─────────────────────────────────────────────────────────────
class WelcomePanel(tk.Frame):
    def __init__(self, parent, **kw):
        super().__init__(parent, bg=BG_WELCOME, **kw)
        self._build()

    def activate(self): pass

    def _build(self):
        center = tk.Frame(self, bg=BG_WELCOME)
        center.place(relx=0.5, rely=0.45, anchor="center")

        # title
        tk.Label(center, text="RE4", fg=ACCENT, bg=BG_WELCOME,
                 font=("Courier New", 36, "bold")).pack()
        tk.Label(center, text="MASTER EDITOR", fg=TEXT_MAIN, bg=BG_WELCOME,
                 font=("Courier New", 16, "bold")).pack()

        tk.Frame(center, bg=ACCENT, height=1, width=300).pack(pady=18)

        tk.Label(center,
                 text="Select a module from the navigation bar above"
                 if CURRENT_LANG == "en" else
                 "اختر القسم الذي تريده من شريط التنقل فوق",
                 fg=TEXT_DIM, bg=BG_WELCOME,
                 font=FONT_NORMAL).pack()

        # tool icons row
        icons_frame = tk.Frame(center, bg=BG_WELCOME)
        icons_frame.pack(pady=28)
        for tool in TOOLS:
            col = tk.Frame(icons_frame, bg=BG_WELCOME)
            col.pack(side="left", padx=10)
            tk.Label(col, text="◈", fg=MUTED, bg=BG_WELCOME,
                     font=("Courier New", 14)).pack()
            tk.Label(col, text=tool["label"].replace(" ", "\n"),
                     fg=MUTED, bg=BG_WELCOME,
                     font=("Courier New", 7), justify="center").pack()


# ── Coming Soon Panel ─────────────────────────────────────────────────────────
class ComingSoonPanel(tk.Frame):
    def __init__(self, parent, tool, **kw):
        super().__init__(parent, bg=BG_CONTENT, **kw)
        self.tool = tool
        self._build()

    def activate(self): pass

    def _build(self):
        f = tk.Frame(self, bg=BG_CONTENT)
        f.place(relx=0.5, rely=0.45, anchor="center")

        tk.Label(f, text=self.tool["label"], fg=ACCENT, bg=BG_CONTENT,
                 font=FONT_TITLE).pack(pady=(0, 14))

        tk.Label(f, text="[ COMING SOON ]", fg=MUTED, bg=BG_CONTENT,
                 font=("Courier New", 13, "bold")).pack()

        tk.Label(f,
                 text="This module is under development."
                 if CURRENT_LANG == "en" else
                 "هذا القسم قيد التطوير.",
                 fg=TEXT_DIM, bg=BG_CONTENT, font=FONT_SMALL).pack(pady=(10, 0))

        folder = os.path.join(MASTER_DIR, self.tool["folder"])
        tk.Label(f, text=f"Folder: {folder}",
                 fg=MUTED, bg=BG_CONTENT, font=FONT_TINY).pack(pady=(6, 0))


# ── Code Manager Panel ────────────────────────────────────────────────────────
class CodeManagerPanel(tk.Frame):
    """
    Embeds RE4 Code Manager.
    Loads main.py from RE4 MASTER EDITOR/RE4 CODE MANAGER/main.py
    and injects the shared EXE path and base dir.
    """

    def __init__(self, parent, master_app, **kw):
        super().__init__(parent, bg=BG_CONTENT, **kw)
        self.master_app = master_app
        self._loaded    = False
        self._module    = None

    def activate(self):
        if not self._loaded:
            self._load()
            self._loaded = True

    def _load(self):
        cm_dir  = os.path.join(MASTER_DIR, "RE4 CODE MANAGER")
        cm_main = os.path.join(cm_dir, "main.py")

        if not os.path.isfile(cm_main):
            self._show_missing(cm_dir)
            return

        try:
            self._embed(cm_dir, cm_main)
        except Exception as e:
            make_label(self,
                       "Error loading RE4 Code Manager:\n" + str(e),
                       fg=RED, bg=BG_CONTENT, font=FONT_SMALL
                       ).pack(pady=40, padx=20)

    def _show_missing(self, expected):
        f = tk.Frame(self, bg=BG_CONTENT)
        f.place(relx=0.5, rely=0.45, anchor="center")
        make_label(f, "RE4 Code Manager folder not found.",
                   fg=RED, bg=BG_CONTENT, font=FONT_NORMAL).pack(pady=8)
        make_label(f, f"Expected:\n{expected}",
                   fg=TEXT_DIM, bg=BG_CONTENT, font=FONT_TINY).pack()

    def _embed(self, cm_dir, cm_main):
        import importlib.util

        if cm_dir not in sys.path:
            sys.path.insert(0, cm_dir)

        spec   = importlib.util.spec_from_file_location("re4_code_manager", cm_main)
        module = importlib.util.module_from_spec(spec)

        # inject: base dir so paths resolve correctly
        module.__MASTER_BASE__ = _ROOT

        spec.loader.exec_module(module)
        self._module = module

        # create app as a Frame embedded in this panel
        try:
            app = module.RE4PatcherApp(master=self)
        except TypeError:
            # if RE4PatcherApp inherits Tk, we need to adapt
            app = self._make_embedded_app(module)
            return

        # share exe path
        app.exe_path.set(self.master_app.exe_path.get())
        self.master_app.exe_path.trace_add(
            "write",
            lambda *_: app.exe_path.set(self.master_app.exe_path.get())
        )
        app.pack(fill="both", expand=True)

    def _make_embedded_app(self, module):
        """Fallback embedded view when RE4PatcherApp is a Tk root."""
        # scan button only
        toprow = tk.Frame(self, bg=BG_CONTENT)
        toprow.pack(fill="x", padx=10, pady=8)

        make_label(toprow,
                   "bio4.exe set from top bar. Press Scan to load codes."
                   if CURRENT_LANG == "en" else
                   "مسار bio4.exe محدد من الشريط العلوي. اضغط Scan.",
                   fg=ACCENT, bg=BG_CONTENT, font=FONT_SMALL
                   ).pack(side="left")

        def do_scan():
            exe = self.master_app.exe_path.get().strip()
            if not exe or not os.path.isfile(exe):
                messagebox.showerror("Error",
                    "Select bio4.exe first (top bar)."
                    if CURRENT_LANG == "en" else
                    "حط مسار bio4.exe من الشريط العلوي أول.")
                return
            # delegate to module
            try:
                app = module._EMBEDDED_INSTANCE
                app.exe_path.set(exe)
                app._scan()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        make_button(toprow, "  SCAN EXE  ",
                    do_scan,
                    fg="#0a0a0a", bg=ACCENT,
                    active_bg="#b8902a",
                    font=("Courier New", 10, "bold"),
                    pady=4
                    ).pack(side="right")

        make_label(self,
                   "Full Code Manager UI will appear here after first scan.",
                   fg=TEXT_DIM, bg=BG_CONTENT, font=FONT_SMALL
                   ).pack(pady=40)


# ── Settings Dialog ───────────────────────────────────────────────────────────
class SettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Settings")
        self.geometry("320x240")
        self.resizable(False, False)
        self.configure(bg="#111")
        self.grab_set()
        self._build()

    def _build(self):
        global CURRENT_LANG, MASTER_SETTINGS

        make_label(self, "Settings", fg=ACCENT, bg="#111",
                   font=FONT_BOLD).pack(pady=(16, 10))

        # Language
        tk.Frame(self, bg="#333", height=1).pack(fill="x", padx=20, pady=4)
        make_label(self, "Language", fg=TEXT_DIM, bg="#111",
                   font=FONT_TINY).pack()

        lang_var = tk.StringVar(value=MASTER_SETTINGS.get("lang", "en"))
        lf = tk.Frame(self, bg="#111")
        lf.pack(pady=4)
        for val, lbl in [("en", "English"), ("ar", "العربية")]:
            tk.Radiobutton(lf, text=lbl, variable=lang_var, value=val,
                           fg=TEXT_MAIN, bg="#111",
                           activebackground="#111", selectcolor="#1a1a1a",
                           font=FONT_SMALL, relief="flat"
                           ).pack(side="left", padx=12)

        # Remember EXE
        tk.Frame(self, bg="#333", height=1).pack(fill="x", padx=20, pady=4)
        rem_var = tk.BooleanVar(value=MASTER_SETTINGS.get("remember_exe", True))
        tk.Checkbutton(self,
                       text="Remember last EXE path"
                       if CURRENT_LANG == "en" else "تذكر آخر مسار EXE",
                       variable=rem_var,
                       fg=TEXT_MAIN, bg="#111",
                       activebackground="#111", selectcolor="#1a1a1a",
                       font=FONT_SMALL, relief="flat",
                       command=lambda: (
                           MASTER_SETTINGS.update({"remember_exe": rem_var.get()}),
                           save_master_settings(MASTER_SETTINGS)
                       )).pack(padx=24, anchor="w", pady=4)

        def apply_lang():
            global CURRENT_LANG
            CURRENT_LANG = lang_var.get()
            MASTER_SETTINGS["lang"] = CURRENT_LANG
            save_master_settings(MASTER_SETTINGS)
            self.destroy()
            messagebox.showinfo("Language",
                "Restart the application to apply language change."
                if CURRENT_LANG == "en" else
                "أعد تشغيل البرنامج لتطبيق اللغة.")

        make_button(self, "Apply" if CURRENT_LANG == "en" else "تطبيق",
                    apply_lang, fg=ACCENT2, bg="#1a2a0a",
                    active_bg="#2a4a1a", width=10
                    ).pack(pady=14)


# ── Main App ──────────────────────────────────────────────────────────────────
class RE4MasterEditor(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("RE4 Master Editor")
        self.geometry("1120x730")
        self.minsize(920, 620)
        self.configure(bg=BG_MAIN)

        self.exe_path    = tk.StringVar()
        self.active_tool = None
        self.panels      = {}
        self.nav_btns    = {}

        # restore last exe
        if MASTER_SETTINGS.get("remember_exe", True):
            last = MASTER_SETTINGS.get("last_exe", "")
            if last and os.path.isfile(last):
                self.exe_path.set(last)

        self.exe_path.trace_add("write", self._on_exe_change)

        self._build_ui()
        # start on welcome — no tool selected
        self._show_welcome()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _build_ui(self):
        # top bar
        topbar = tk.Frame(self, bg=BG_TOPBAR)
        topbar.pack(fill="x")
        tk.Frame(self, bg=ACCENT, height=1).pack(fill="x")

        make_label(topbar, "RE4 ", fg=ACCENT, bg=BG_TOPBAR,
                   font=("Courier New", 12, "bold")).pack(side="left", padx=(14, 0), pady=7)
        make_label(topbar, "MASTER EDITOR", fg=TEXT_MAIN, bg=BG_TOPBAR,
                   font=("Courier New", 12, "bold")).pack(side="left", pady=7)
        make_label(topbar, "  v1.0.0", fg=MUTED, bg=BG_TOPBAR,
                   font=FONT_TINY).pack(side="left", pady=7)

        # Settings button
        make_button(topbar, "Settings",
                    self._open_settings,
                    fg=MUTED, bg=BG_TOPBAR, active_bg="#1a1a1a",
                    font=FONT_TINY
                    ).pack(side="right", padx=(0, 10), pady=6)

        # EXE path
        path_f = tk.Frame(topbar, bg=BG_TOPBAR)
        path_f.pack(side="right", padx=6, pady=5)

        make_label(path_f, "bio4.exe:", fg=TEXT_DIM, bg=BG_TOPBAR,
                   font=FONT_TINY).pack(side="left", padx=(0, 5))

        self.path_entry = tk.Entry(
            path_f, textvariable=self.exe_path,
            font=FONT_SMALL, fg=ACCENT2, bg="#0d1a0d",
            insertbackground=ACCENT2,
            relief="flat", bd=0,
            highlightthickness=1, highlightbackground="#2a5a2a",
            width=36
        )
        self.path_entry.pack(side="left", ipady=3)
        self._add_paste_menu(self.path_entry)

        make_button(path_f, "Browse",
                    self._browse_exe,
                    fg=ACCENT, bg="#1a1500", active_bg="#2a2000",
                    font=FONT_TINY, padx=6
                    ).pack(side="left", padx=5)

        # nav bar
        navbar = tk.Frame(self, bg=BG_NAV)
        navbar.pack(fill="x")
        tk.Frame(self, bg="#1a1a1a", height=1).pack(fill="x")

        nav_inner = tk.Frame(navbar, bg=BG_NAV)
        nav_inner.pack(side="left")

        for tool in TOOLS:
            tid = tool["id"]
            btn = tk.Button(
                nav_inner,
                text=tool["label"],
                font=FONT_NAV,
                fg=MUTED, bg=BG_NAV,
                activeforeground=ACCENT,
                activebackground=NAV_ACTIVE,
                relief="flat", bd=0,
                cursor="hand2",
                padx=14, pady=7,
                command=lambda t=tid: self._switch_tool(t)
            )
            btn.pack(side="left")
            self.nav_btns[tid] = btn

        tk.Frame(self, bg="#111", height=1).pack(fill="x")

        # content
        self.content = tk.Frame(self, bg=BG_CONTENT)
        self.content.pack(fill="both", expand=True)

        # welcome panel
        self._welcome_panel = WelcomePanel(self.content)
        self._welcome_panel.place(relx=0, rely=0, relwidth=1, relheight=1)

        # build tool panels
        for tool in TOOLS:
            tid = tool["id"]
            if tid == "code_manager":
                panel = CodeManagerPanel(self.content, self)
            else:
                panel = ComingSoonPanel(self.content, tool)
            panel.place(relx=0, rely=0, relwidth=1, relheight=1)
            self.panels[tid] = panel

        # status bar
        tk.Frame(self, bg="#111", height=1).pack(fill="x")
        sbar = tk.Frame(self, bg="#0d0d0d")
        sbar.pack(fill="x")
        self.status_var = tk.StringVar(value="")
        tk.Label(sbar, textvariable=self.status_var,
                 fg=TEXT_DIM, bg="#0d0d0d", font=FONT_TINY
                 ).pack(side="left", padx=12, pady=3)
        make_label(sbar, "by YEMENI", fg=MUTED, bg="#0d0d0d",
                   font=FONT_TINY).pack(side="right", padx=12, pady=3)

    # ── navigation ────────────────────────────────────────────────────────────

    def _show_welcome(self):
        for p in self.panels.values():
            p.lower()
        self._welcome_panel.lift()
        for btn in self.nav_btns.values():
            btn.configure(fg=MUTED, bg=BG_NAV,
                           highlightthickness=0)
        self.active_tool = None
        self.status_var.set("")

    def _switch_tool(self, tool_id):
        self._welcome_panel.lower()
        for tid, panel in self.panels.items():
            panel.lower()
            btn = self.nav_btns.get(tid)
            if btn:
                btn.configure(fg=MUTED, bg=BG_NAV, highlightthickness=0)

        panel = self.panels.get(tool_id)
        if panel:
            panel.lift()
            panel.activate()

        btn = self.nav_btns.get(tool_id)
        if btn:
            btn.configure(fg=ACCENT, bg=NAV_ACTIVE,
                           highlightthickness=1,
                           highlightbackground=NAV_BORDER)

        self.active_tool = tool_id
        label = next((t["label"] for t in TOOLS if t["id"] == tool_id), tool_id)
        self.status_var.set(label)

    # ── helpers ───────────────────────────────────────────────────────────────

    def _add_paste_menu(self, entry):
        menu = tk.Menu(entry, tearoff=0, bg="#1a1a1a", fg=TEXT_MAIN,
                       activebackground="#2a2a2a", font=FONT_TINY)
        menu.add_command(label="Paste",
                         command=lambda: entry.event_generate("<<Paste>>"))
        menu.add_command(label="Copy",
                         command=lambda: entry.event_generate("<<Copy>>"))
        menu.add_command(label="Select All",
                         command=lambda: entry.select_range(0, "end"))
        entry.bind("<Button-3>", lambda e: menu.tk_popup(e.x_root, e.y_root))

    def _browse_exe(self):
        path = filedialog.askopenfilename(
            title="Select bio4.exe",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
        )
        if path:
            self.exe_path.set(path)

    def _on_exe_change(self, *_):
        path = self.exe_path.get().strip()
        if path and os.path.isfile(path):
            if MASTER_SETTINGS.get("remember_exe", True):
                MASTER_SETTINGS["last_exe"] = path
                save_master_settings(MASTER_SETTINGS)
            self.status_var.set("EXE: " + os.path.basename(path)
                                + (" — " + self.active_tool if self.active_tool else ""))

    def _open_settings(self):
        SettingsDialog(self)


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = RE4MasterEditor()
    app.mainloop()
