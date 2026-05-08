"""
NetDiag — Network Diagnostics Tool
Требования: pip install tkinter (обычно встроен)
Сборка в .exe: pip install pyinstaller
              pyinstaller --onefile --noconsole netdiag.py
"""

import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import threading
import zipfile
import os
import sys
import datetime


# ─── Цвета (повторяют оригинальный HTML) ───────────────────────────────────
BG       = "#0d0f0e"
SURFACE  = "#131614"
SURFACE2 = "#1a1d1b"
BORDER   = "#2a2f2c"
ACCENT   = "#00e676"
ACCENT2  = "#69f0ae"
WARN     = "#ffab40"
ERR      = "#ff5252"
TEXT     = "#cdd8d3"
MUTED    = "#556360"
TAG_WIN  = "#4fc3f7"


# ─── Команды ───────────────────────────────────────────────────────────────
def get_commands(host, port):
    return [
        ("nslookup",    f"nslookup {host}"),
        ("ping4",       f"ping -4 -n 10 {host}"),
        ("ping6",       f"ping -6 -n 10 {host}"),
        ("tracert4",    f"tracert -4 {host}"),
        ("tracert6",    f"tracert -6 {host}"),
        ("telnet_check",f"powershell -Command \"Test-NetConnection -ComputerName {host} -Port {port}\""),
        ("ipconfig",    "ipconfig /all"),
        ("route",       "route print"),
    ]


# ─── Запуск команды ─────────────────────────────────────────────────────────
def run_cmd(cmd_str, timeout=120):
    try:
        result = subprocess.run(
            cmd_str,
            shell=True,
            capture_output=True,
            text=True,
            encoding="cp866",
            errors="replace",
            timeout=timeout,
        )
        output = result.stdout + (result.stderr if result.stderr else "")
    except subprocess.TimeoutExpired:
        output = f"[TIMEOUT] Команда превысила {timeout} сек.\n"
    except Exception as e:
        output = f"[ERROR] {e}\n"
    return output


# ─── Основное окно ──────────────────────────────────────────────────────────
class NetDiagApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("NetDiag")
        self.geometry("820x640")
        self.minsize(700, 520)
        self.configure(bg=BG)
        self._running = False
        self._build_ui()

    # ── UI ──────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # Header
        hdr = tk.Frame(self, bg=SURFACE, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="Net", font=("Consolas", 20, "bold"),
                 bg=SURFACE, fg=ACCENT).pack(side="left", padx=(20, 0), pady=10)
        tk.Label(hdr, text="Diag", font=("Consolas", 20, "bold"),
                 bg=SURFACE, fg=MUTED).pack(side="left", pady=10)
        tk.Label(hdr, text="WINDOWS", font=("Consolas", 9, "bold"),
                 bg="#0d2a3a", fg=TAG_WIN, padx=8, pady=2).pack(side="right", padx=16, pady=14)

        # Body
        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        # ── Sidebar
        sidebar = tk.Frame(body, bg=SURFACE, width=280)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)
        sidebar_inner = tk.Frame(sidebar, bg=SURFACE)
        sidebar_inner.pack(fill="both", expand=True, padx=18, pady=18)

        self._section(sidebar_inner, "Целевой хост")
        self.host_var = tk.StringVar(value="example.com")
        host_entry = tk.Entry(sidebar_inner, textvariable=self.host_var,
                              bg=BG, fg=TEXT, insertbackground=TEXT,
                              font=("Consolas", 11), relief="flat",
                              highlightthickness=1, highlightcolor=ACCENT,
                              highlightbackground=BORDER)
        host_entry.pack(fill="x", pady=(0, 14), ipady=6)

        self._section(sidebar_inner, "Порт")
        port_frame = tk.Frame(sidebar_inner, bg=SURFACE)
        port_frame.pack(fill="x", pady=(0, 14))
        self.port_var = tk.StringVar(value="80")
        for p, lbl in [("80","HTTP"), ("443","HTTPS"), ("22","SSH")]:
            b = tk.Button(port_frame, text=f"{p}\n{lbl}",
                          font=("Consolas", 9), bg=BG, fg=MUTED,
                          relief="flat", bd=0, activebackground=SURFACE2,
                          command=lambda pv=p: self._set_port(pv))
            b.pack(side="left", expand=True, fill="x", padx=2, ipady=4)
            b.config(highlightthickness=1, highlightbackground=BORDER)
        self._port_buttons = port_frame.winfo_children()
        self._set_port("80")

        self._section(sidebar_inner, "Статус")
        self.status_var = tk.StringVar(value="Ожидание")
        tk.Label(sidebar_inner, textvariable=self.status_var,
                 bg=SURFACE, fg=MUTED, font=("Consolas", 9),
                 wraplength=240, justify="left").pack(anchor="w", pady=(0, 14))

        # Run button — прижат к низу
        btn_frame = tk.Frame(sidebar, bg=SURFACE)
        btn_frame.pack(side="bottom", fill="x", padx=18, pady=18)
        self.run_btn = tk.Button(btn_frame, text="▶  ЗАПУСТИТЬ ДИАГНОСТИКУ",
                                 font=("Consolas", 13, "bold"),
                                 bg=ACCENT, fg="#001a09",
                                 relief="flat", bd=0,
                                 activebackground=ACCENT2,
                                 cursor="hand2",
                                 command=self._start)
        self.run_btn.pack(fill="x", ipady=10)

        # ── Output
        out_frame = tk.Frame(body, bg=BG)
        out_frame.pack(side="left", fill="both", expand=True)

        top_bar = tk.Frame(out_frame, bg=SURFACE, height=36)
        top_bar.pack(fill="x")
        top_bar.pack_propagate(False)
        tk.Label(top_bar, text="ВЫВОД", font=("Consolas", 9, "bold"),
                 bg=SURFACE, fg=MUTED).pack(side="left", padx=14, pady=8)
        self.progress = ttk.Progressbar(top_bar, mode="indeterminate", length=160)
        self.progress.pack(side="right", padx=14, pady=10)

        self.log = tk.Text(out_frame, bg=BG, fg=TEXT,
                           font=("Consolas", 9), relief="flat",
                           wrap="word", state="disabled",
                           selectbackground=SURFACE2, insertbackground=TEXT,
                           bd=0, padx=10, pady=10)
        sb = tk.Scrollbar(out_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        self.log.pack(fill="both", expand=True)

        self.log.tag_config("cmd",    foreground=ACCENT,  font=("Consolas", 9, "bold"))
        self.log.tag_config("ok",     foreground=ACCENT2)
        self.log.tag_config("err",    foreground=ERR)
        self.log.tag_config("warn",   foreground=WARN)
        self.log.tag_config("muted",  foreground=MUTED)
        self.log.tag_config("output", foreground=TEXT)

        self._log("Задай хост и порт, затем нажми «Запустить диагностику».\n", "muted")

    # ── Хелперы UI ──────────────────────────────────────────────────────────
    def _section(self, parent, text):
        tk.Label(parent, text=text.upper(), font=("Consolas", 8),
                 bg=SURFACE, fg=MUTED).pack(anchor="w", pady=(0, 4))

    def _set_port(self, val):
        self.port_var.set(val)
        for btn in self._port_buttons:
            port_in_btn = btn["text"].split("\n")[0]
            if port_in_btn == val:
                btn.config(fg=ACCENT, highlightbackground=ACCENT, bg="#001f0f")
            else:
                btn.config(fg=MUTED, highlightbackground=BORDER, bg=BG)

    def _log(self, text, tag="output"):
        self.log.configure(state="normal")
        self.log.insert("end", text, tag)
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clear_log(self):
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    # ── Запуск ──────────────────────────────────────────────────────────────
    def _start(self):
        host = self.host_var.get().strip()
        if not host:
            messagebox.showerror("Ошибка", "Введи имя хоста или IP-адрес")
            return
        if self._running:
            return
        self._running = True
        self.run_btn.config(state="disabled", bg=MUTED, fg=SURFACE)
        self.progress.start(12)
        self._clear_log()
        threading.Thread(target=self._worker, args=(host, self.port_var.get()), daemon=True).start()

    def _worker(self, host, port):
        ts = datetime.datetime.now()
        ts_str = ts.strftime("%Y-%m-%d %H:%M:%S")
        safe_host = "".join(c if c.isalnum() or c in "-_." else "_" for c in host)
        date_str  = ts.strftime("%Y%m%d_%H%M%S")
        desktop   = os.path.join(os.path.expanduser("~"), "Desktop")
        work_dir  = os.path.join(desktop, f"netdiag_{safe_host}_{date_str}")
        os.makedirs(work_dir, exist_ok=True)

        commands = get_commands(host, port)
        results  = {}

        self.after(0, self._log,
            f"═══════════════════════════════════════════════\n"
            f"  NetDiag  |  host: {host}  port: {port}\n"
            f"  {ts_str}\n"
            f"═══════════════════════════════════════════════\n\n", "cmd")

        total = len(commands)
        for idx, (name, cmd) in enumerate(commands, 1):
            self.after(0, self.status_var.set, f"[{idx}/{total}] {name}…")
            self.after(0, self._log, f"┌─ [{idx}/{total}] {cmd}\n", "cmd")

            output = run_cmd(cmd)
            results[name] = (cmd, output)

            # Записываем в отдельный .txt
            txt_path = os.path.join(work_dir, f"{idx:02d}_{name}.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"Command: {cmd}\n")
                f.write(f"Executed: {ts_str}\n")
                f.write("=" * 60 + "\n\n")
                f.write(output)

            self.after(0, self._log, output + "\n", "output")
            self.after(0, self._log, f"└─ сохранено: {os.path.basename(txt_path)}\n\n", "ok")

        # Сводный файл
        summary_path = os.path.join(work_dir, "00_summary.txt")
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write(f"NetDiag Summary\nHost: {host}  Port: {port}\nDate: {ts_str}\n\n")
            for name, (cmd, out) in results.items():
                f.write(f"\n{'='*60}\n[{name}]  {cmd}\n{'='*60}\n{out}\n")

        # Пакуем в .zip
        zip_path = os.path.join(desktop, f"netdiag_{safe_host}_{date_str}.zip")
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname in os.listdir(work_dir):
                zf.write(os.path.join(work_dir, fname), arcname=fname)

        # Удаляем временную папку
        import shutil
        shutil.rmtree(work_dir, ignore_errors=True)

        self.after(0, self._finish, zip_path)

    def _finish(self, zip_path):
        self._running = False
        self.progress.stop()
        self.run_btn.config(state="normal", bg=ACCENT, fg="#001a09")
        self.status_var.set("Готово ✓")
        self._log(
            f"═══════════════════════════════════════════════\n"
            f"  ГОТОВО!\n"
            f"  Архив сохранён на рабочий стол:\n"
            f"  {os.path.basename(zip_path)}\n"
            f"═══════════════════════════════════════════════\n", "ok")
        messagebox.showinfo(
            "NetDiag — готово",
            f"Диагностика завершена.\n\nАрхив сохранён:\n{zip_path}"
        )


# ─── Точка входа ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = NetDiagApp()
    app.mainloop()
