#!/usr/bin/env python3
"""
Shutdown GUI - a plain, no-frills front end for the Windows `shutdown.exe`
command line tool. Exposes every flag the CLI supports:

    /s /r /g /h /hybrid /l /sg /a
    /o /e /f /p
    /t xxx
    /c "comment"
    /m \\computer
    /d [p|u:]xx:yy

Runs on Windows to actually execute; on any other OS it still lets you
build/preview/copy the command (useful for testing, remote scripting, etc.)
since it's plain Python + tkinter (both ship with a normal Python install).
"""

import platform
import subprocess
import sys
import tkinter as tk
from tkinter import ttk, messagebox

IS_WINDOWS = platform.system() == "Windows"

# (label, planned?, major, minor)
REASON_PRESETS = [
    ("Custom / none", None, None, None),
    ("Other (Unplanned)", False, 0, 0),
    ("Other (Planned)", True, 0, 0),
    ("Hardware: Maintenance (Planned)", True, 1, 1),
    ("Hardware: Installation (Unplanned)", False, 1, 2),
    ("Operating System: Recovery (Planned)", True, 2, 2),
    ("Operating System: Upgrade (Planned)", True, 2, 4),
    ("Application: Maintenance (Planned)", True, 2, 17),
    ("Application: Installation (Planned)", True, 2, 16),
    ("Application: Unresponsive", False, 2, 19),
    ("Security issue", False, 2, 18),
]

ACTIONS = [
    ("Shut down", "s"),
    ("Restart", "r"),
    ("Restart + restart registered apps", "g"),
    ("Shut down apps, then restart + restart apps", "sg"),
    ("Hibernate", "h"),
    ("Hybrid shutdown (shutdown + hibernate)", "hybrid"),
    ("Log off", "l"),
    ("Full power off (/p, local only, no timer)", "p"),
    ("Abort a pending shutdown/restart", "a"),
]


class ShutdownGUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Shutdown GUI" + ("" if IS_WINDOWS else "  (preview only - not Windows)"))
        self.resizable(False, False)
        self.configure(padx=10, pady=10)

        self.action_var = tk.StringVar(value="r")
        self.o_var = tk.BooleanVar(value=False)      # /o advanced boot (needs /r or /g)
        self.f_var = tk.BooleanVar(value=False)       # /f force close apps
        self.e_var = tk.BooleanVar(value=False)       # /e document reason (no shutdown)
        self.t_var = tk.StringVar(value="30")          # /t seconds
        self.c_var = tk.StringVar(value="")            # /c comment
        self.m_var = tk.StringVar(value="")            # /m \\computer
        self.reason_var = tk.StringVar(value=REASON_PRESETS[0][0])
        self.planned_var = tk.BooleanVar(value=False)
        self.major_var = tk.StringVar(value="")
        self.minor_var = tk.StringVar(value="")

        self._build_ui()
        self._update_preview()

    # ---------- UI ----------
    def _build_ui(self):
        row = 0

        ttk.Label(self, text="Action", font=("", 9, "bold")).grid(row=row, column=0, sticky="w")
        row += 1
        action_frame = ttk.Frame(self)
        action_frame.grid(row=row, column=0, columnspan=2, sticky="w")
        for i, (label, val) in enumerate(ACTIONS):
            ttk.Radiobutton(
                action_frame, text=label, value=val, variable=self.action_var,
                command=self._update_preview
            ).grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 12), pady=1)
        row += (len(ACTIONS) // 2) + 1

        ttk.Separator(self).grid(row=row, column=0, columnspan=2, sticky="ew", pady=6)
        row += 1

        ttk.Label(self, text="Options", font=("", 9, "bold")).grid(row=row, column=0, sticky="w")
        row += 1
        opt_frame = ttk.Frame(self)
        opt_frame.grid(row=row, column=0, columnspan=2, sticky="w")
        ttk.Checkbutton(opt_frame, text="/o  Advanced boot options (needs Restart)",
                         variable=self.o_var, command=self._update_preview).grid(row=0, column=0, sticky="w")
        ttk.Checkbutton(opt_frame, text="/f  Force close running apps",
                         variable=self.f_var, command=self._update_preview).grid(row=1, column=0, sticky="w")
        ttk.Checkbutton(opt_frame, text="/e  Document reason only (no actual shutdown)",
                         variable=self.e_var, command=self._update_preview).grid(row=2, column=0, sticky="w")
        row += 3

        ttk.Separator(self).grid(row=row, column=0, columnspan=2, sticky="ew", pady=6)
        row += 1

        grid = ttk.Frame(self)
        grid.grid(row=row, column=0, columnspan=2, sticky="w")

        ttk.Label(grid, text="/t  Timeout (sec):").grid(row=0, column=0, sticky="w")
        ttk.Entry(grid, textvariable=self.t_var, width=10).grid(row=0, column=1, sticky="w", padx=4)

        ttk.Label(grid, text="/c  Comment:").grid(row=1, column=0, sticky="w")
        ttk.Entry(grid, textvariable=self.c_var, width=32).grid(row=1, column=1, sticky="w", padx=4)

        ttk.Label(grid, text="/m  Remote computer (\\\\name):").grid(row=2, column=0, sticky="w")
        ttk.Entry(grid, textvariable=self.m_var, width=20).grid(row=2, column=1, sticky="w", padx=4)

        for var in (self.t_var, self.c_var, self.m_var):
            var.trace_add("write", lambda *_: self._update_preview())

        row += 3
        ttk.Separator(self).grid(row=row, column=0, columnspan=2, sticky="ew", pady=6)
        row += 1

        ttk.Label(self, text="/d  Reason code", font=("", 9, "bold")).grid(row=row, column=0, sticky="w")
        row += 1
        reason_frame = ttk.Frame(self)
        reason_frame.grid(row=row, column=0, columnspan=2, sticky="w")
        preset_menu = ttk.Combobox(reason_frame, textvariable=self.reason_var, width=38,
                                    values=[p[0] for p in REASON_PRESETS], state="readonly")
        preset_menu.grid(row=0, column=0, columnspan=4, sticky="w")
        preset_menu.bind("<<ComboboxSelected>>", self._apply_preset)

        ttk.Checkbutton(reason_frame, text="Planned", variable=self.planned_var,
                         command=self._update_preview).grid(row=1, column=0, sticky="w")
        ttk.Label(reason_frame, text="Major:").grid(row=1, column=1, sticky="e")
        ttk.Entry(reason_frame, textvariable=self.major_var, width=5).grid(row=1, column=2, sticky="w")
        ttk.Label(reason_frame, text="Minor:").grid(row=1, column=3, sticky="e")
        ttk.Entry(reason_frame, textvariable=self.minor_var, width=6).grid(row=1, column=4, sticky="w")
        for var in (self.major_var, self.minor_var):
            var.trace_add("write", lambda *_: self._update_preview())
        row += 2

        ttk.Separator(self).grid(row=row, column=0, columnspan=2, sticky="ew", pady=6)
        row += 1

        ttk.Label(self, text="Command preview:").grid(row=row, column=0, sticky="w")
        row += 1
        self.preview = tk.Entry(self, width=60, state="readonly")
        self.preview.grid(row=row, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        row += 1

        btn_frame = ttk.Frame(self)
        btn_frame.grid(row=row, column=0, columnspan=2, sticky="ew")
        ttk.Button(btn_frame, text="Copy command", command=self._copy).pack(side="left")
        run_text = "Run" if IS_WINDOWS else "Run (Windows only)"
        run_btn = ttk.Button(btn_frame, text=run_text, command=self._run)
        run_btn.pack(side="right")
        if not IS_WINDOWS:
            run_btn.state(["disabled"])

    # ---------- logic ----------
    def _apply_preset(self, _event=None):
        label = self.reason_var.get()
        for name, planned, major, minor in REASON_PRESETS:
            if name == label:
                if planned is None:
                    self.major_var.set("")
                    self.minor_var.set("")
                else:
                    self.planned_var.set(planned)
                    self.major_var.set(str(major))
                    self.minor_var.set(str(minor))
                break
        self._update_preview()

    def build_args(self):
        action = self.action_var.get()
        args = ["shutdown.exe" if IS_WINDOWS else "shutdown"]

        if action == "a":
            args.append("/a")
            if self.m_var.get().strip():
                args += ["/m", self.m_var.get().strip()]
            return args

        flag_map = {
            "s": "/s", "r": "/r", "g": "/g", "sg": "/sg",
            "h": "/h", "hybrid": "/hybrid", "l": "/l", "p": "/p",
        }
        args.append(flag_map[action])

        if self.o_var.get() and action in ("r", "g"):
            args.append("/o")
        if self.f_var.get() and action != "l":
            args.append("/f")
        if self.e_var.get():
            args.append("/e")

        # /p and /l don't take a timeout
        if action not in ("p", "l") and not self.e_var.get():
            t = self.t_var.get().strip()
            if t:
                args += ["/t", t]

        if self.m_var.get().strip() and action != "l":
            args += ["/m", self.m_var.get().strip()]

        if self.c_var.get().strip():
            args += ["/c", self.c_var.get().strip()]

        major, minor = self.major_var.get().strip(), self.minor_var.get().strip()
        if major and minor:
            prefix = "p" if self.planned_var.get() else "u"
            args += ["/d", f"{prefix}:{major}:{minor}"]

        return args

    def _quoted(self, args):
        out = []
        for a in args:
            out.append(f'"{a}"' if " " in a else a)
        return " ".join(out)

    def _update_preview(self):
        try:
            args = self.build_args()
            cmd = self._quoted(args)
        except Exception as exc:
            cmd = f"<error building command: {exc}>"
        self.preview.config(state="normal")
        self.preview.delete(0, tk.END)
        self.preview.insert(0, cmd)
        self.preview.config(state="readonly")

    def _copy(self):
        self.clipboard_clear()
        self.clipboard_append(self.preview.get())

    def _run(self):
        if not IS_WINDOWS:
            messagebox.showinfo("Not Windows", "shutdown.exe only exists on Windows.")
            return
        args = self.build_args()
        action = self.action_var.get()
        if action != "a":
            if not messagebox.askyesno(
                "Confirm",
                f"About to run:\n\n{self._quoted(args)}\n\nProceed?"
            ):
                return
        try:
            subprocess.run(args, check=True)
        except subprocess.CalledProcessError as exc:
            messagebox.showerror("Error", f"shutdown.exe returned an error:\n{exc}")
        except FileNotFoundError:
            messagebox.showerror("Error", "shutdown.exe was not found on this system.")


if __name__ == "__main__":
    app = ShutdownGUI()
    app.mainloop()
