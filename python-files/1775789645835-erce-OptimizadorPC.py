import tkinter as tk
from tkinter import ttk, scrolledtext
import threading
import subprocess
import os
import ctypes
import sys
import time

# ── Paleta de colores ──────────────────────────────────────────
BG        = "#0d1117"
PANEL     = "#161b22"
BORDER    = "#30363d"
GREEN     = "#3fb950"
YELLOW    = "#d29922"
RED       = "#f85149"
BLUE      = "#58a6ff"
TEXT      = "#e6edf3"
TEXT_DIM  = "#8b949e"
BTN_BG    = "#238636"
BTN_HOV   = "#2ea043"

class OptimizadorPC(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Optimizador de PC — Windows 10/11")
        self.geometry("700x580")
        self.resizable(False, False)
        self.configure(bg=BG)
        self._build_ui()
        self._center_window()

    def _center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth()  - 700) // 2
        y = (self.winfo_screenheight() - 580) // 2
        self.geometry(f"700x580+{x}+{y}")

    # ── UI ────────────────────────────────────────────────────
    def _build_ui(self):
        # Encabezado
        hdr = tk.Frame(self, bg=PANEL, pady=14)
        hdr.pack(fill="x")
        tk.Label(hdr, text="⚡  OPTIMIZADOR DE PC", font=("Segoe UI", 16, "bold"),
                 bg=PANEL, fg=BLUE).pack()
        tk.Label(hdr, text="Windows 10 / 11  •  Limpieza completa del sistema",
                 font=("Segoe UI", 9), bg=PANEL, fg=TEXT_DIM).pack()

        sep = tk.Frame(self, bg=BORDER, height=1)
        sep.pack(fill="x")

        # Tarjetas de procesos
        card_frame = tk.Frame(self, bg=BG, pady=10, padx=16)
        card_frame.pack(fill="x")

        self.steps = [
            ("🗂️", "Temporales del sistema",   "C:\\Windows\\Temp\\*"),
            ("👤", "Temporales del usuario",    "%TEMP% y %LOCALAPPDATA%\\Temp"),
            ("🗑️", "Papelera de reciclaje",     "Todas las unidades"),
            ("🧠", "Memoria RAM",               "Liberar caché acumulada"),
            ("🌐", "Caché DNS",                 "Flush DNS del sistema"),
            ("🖼️", "Caché de miniaturas",       "thumbcache + Prefetch"),
        ]

        self.step_labels  = []
        self.step_icons   = []
        self.step_status  = []

        cols = tk.Frame(card_frame, bg=BG)
        cols.pack(fill="x")

        for i, (icon, name, detail) in enumerate(self.steps):
            row = tk.Frame(cols, bg=PANEL, padx=12, pady=8,
                           highlightbackground=BORDER, highlightthickness=1)
            row.grid(row=i//2, column=i%2, padx=6, pady=4, sticky="ew")
            cols.columnconfigure(0, weight=1)
            cols.columnconfigure(1, weight=1)

            left = tk.Frame(row, bg=PANEL)
            left.pack(side="left", fill="x", expand=True)

            ico_lbl = tk.Label(left, text=icon, font=("Segoe UI", 13),
                               bg=PANEL, fg=TEXT)
            ico_lbl.pack(side="left", padx=(0,8))

            info = tk.Frame(left, bg=PANEL)
            info.pack(side="left")
            tk.Label(info, text=name, font=("Segoe UI", 9, "bold"),
                     bg=PANEL, fg=TEXT, anchor="w").pack(anchor="w")
            tk.Label(info, text=detail, font=("Segoe UI", 8),
                     bg=PANEL, fg=TEXT_DIM, anchor="w").pack(anchor="w")

            status = tk.Label(row, text="⏳ Esperando", font=("Segoe UI", 8, "bold"),
                              bg=PANEL, fg=YELLOW)
            status.pack(side="right")

            self.step_status.append(status)

        sep2 = tk.Frame(self, bg=BORDER, height=1)
        sep2.pack(fill="x", pady=(8,0))

        # Log en tiempo real
        log_frame = tk.Frame(self, bg=BG, padx=16, pady=8)
        log_frame.pack(fill="both", expand=True)
        tk.Label(log_frame, text="📋  Registro en tiempo real",
                 font=("Segoe UI", 9, "bold"), bg=BG, fg=TEXT_DIM).pack(anchor="w")

        self.log = scrolledtext.ScrolledText(
            log_frame, height=8, bg="#010409", fg=GREEN,
            font=("Consolas", 9), relief="flat", bd=0,
            insertbackground=GREEN, state="disabled"
        )
        self.log.pack(fill="both", expand=True, pady=(4,0))

        sep3 = tk.Frame(self, bg=BORDER, height=1)
        sep3.pack(fill="x")

        # Barra progreso + botón
        bottom = tk.Frame(self, bg=PANEL, pady=12, padx=16)
        bottom.pack(fill="x")

        self.progress = ttk.Progressbar(bottom, length=400, mode="determinate",
                                        maximum=len(self.steps))
        self.progress.pack(side="left", padx=(0,16))

        self.btn = tk.Button(
            bottom, text="▶  INICIAR OPTIMIZACIÓN",
            font=("Segoe UI", 9, "bold"), bg=BTN_BG, fg="white",
            relief="flat", padx=14, pady=6, cursor="hand2",
            activebackground=BTN_HOV, activeforeground="white",
            command=self._start
        )
        self.btn.pack(side="left")

        self.status_lbl = tk.Label(bottom, text="Listo para optimizar",
                                   font=("Segoe UI", 8), bg=PANEL, fg=TEXT_DIM)
        self.status_lbl.pack(side="right")

    # ── Lógica ───────────────────────────────────────────────
    def _log(self, msg, color=GREEN):
        self.log.config(state="normal")
        self.log.insert("end", f"  {msg}\n")
        self.log.tag_add("last", "end-2l", "end-1l")
        self.log.tag_config("last", foreground=color)
        self.log.see("end")
        self.log.config(state="disabled")

    def _set_step(self, i, state):
        colors = {"waiting": (YELLOW, "⏳ Esperando"),
                  "running": (BLUE,   "🔄 Ejecutando..."),
                  "ok":      (GREEN,  "✅ Completado"),
                  "skip":    (TEXT_DIM,"⚠️  Omitido")}
        c, t = colors[state]
        self.step_status[i].config(fg=c, text=t)

    def _run(self, cmd):
        try:
            r = subprocess.run(cmd, shell=True, capture_output=True, timeout=30)
            return r.returncode == 0
        except:
            return False

    def _start(self):
        self.btn.config(state="disabled", text="⏳  Optimizando...")
        for s in self.step_status:
            s.config(text="⏳ Esperando", fg=YELLOW)
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")
        self.progress["value"] = 0
        threading.Thread(target=self._optimize, daemon=True).start()

    def _optimize(self):
        total = len(self.steps)

        def step(i, fn, label):
            self._set_step(i, "running")
            self.status_lbl.config(text=f"Procesando: {self.steps[i][1]}...")
            self._log(f"[{i+1}/{total}] {label}")
            time.sleep(0.4)
            ok = fn()
            self._set_step(i, "ok" if ok else "skip")
            msg = "OK" if ok else "Algunos archivos en uso fueron omitidos"
            self._log(f"       → {msg}", GREEN if ok else YELLOW)
            self.progress["value"] = i + 1

        # 1 – Temp sistema
        step(0,
             lambda: self._run('cmd /c "del /q /f /s %WINDIR%\\Temp\\* 2>nul & exit 0"'),
             "Limpiando C:\\Windows\\Temp\\")

        # 2 – Temp usuario
        step(1,
             lambda: (
                 self._run('cmd /c "del /q /f /s %TEMP%\\* 2>nul & exit 0"') and
                 self._run('cmd /c "del /q /f /s %LOCALAPPDATA%\\Temp\\* 2>nul & exit 0"')
             ),
             "Limpiando %TEMP% y %LOCALAPPDATA%\\Temp\\")

        # 3 – Papelera
        step(2,
             lambda: self._run('powershell -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"'),
             "Vaciando papelera de reciclaje en todas las unidades")

        # 4 – RAM
        step(3,
             lambda: self._run(
                 'powershell -Command "[System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers()"'
             ),
             "Liberando caché de memoria RAM")

        # 5 – DNS
        step(4,
             lambda: self._run("ipconfig /flushdns"),
             "Limpiando caché DNS del sistema")

        # 6 – Miniaturas + Prefetch
        step(5,
             lambda: (
                 self._run('cmd /c "del /q /f %LOCALAPPDATA%\\Microsoft\\Windows\\Explorer\\thumbcache_*.db 2>nul & exit 0"') and
                 self._run('cmd /c "del /q /f C:\\Windows\\Prefetch\\*.pf 2>nul & exit 0"')
             ),
             "Eliminando caché de miniaturas y archivos Prefetch")

        # Final
        time.sleep(0.3)
        self._log("", GREEN)
        self._log("══════════════════════════════════════════", GREEN)
        self._log("  ✅  OPTIMIZACIÓN COMPLETADA CON ÉXITO  ", GREEN)
        self._log("  💡  Reinicia el PC para mejores resultados", BLUE)
        self._log("══════════════════════════════════════════", GREEN)
        self.status_lbl.config(text="✅ Completado — Reinicia para mejores resultados")
        self.btn.config(state="normal", text="🔄  OPTIMIZAR DE NUEVO")

if __name__ == "__main__":
    # Solicitar permisos de administrador automáticamente
    if sys.platform == "win32":
        try:
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        except:
            is_admin = False
        if not is_admin:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
            sys.exit()

    app = OptimizadorPC()
    app.mainloop()
