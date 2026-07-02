"""
EasyXMRig (English Edition)
----------------------------
A simple GUI front-end that helps you configure and launch your own local
copy of XMRig (https://github.com/xmrig/xmrig), the open-source RandomX/
CPU miner for Monero.

IMPORTANT / SAFETY NOTES
- This tool does NOT include, download, or hide xmrig.exe. You must obtain
  xmrig.exe yourself from the official XMRig GitHub releases page:
      https://github.com/xmrig/xmrig/releases
  and point this app at it.
- This tool does NOT modify Windows Defender, add scheduled tasks, write
  to the registry, or try to hide its console/window. It only writes
  config file(s) and starts/stops the xmrig.exe process(es) you select,
  showing their console output live in the log box.
- Only mine with a pool address and wallet address that belong to you or
  that you are otherwise authorized to use.

DEVELOPER FEE
- Like the original tool, FEE_PERCENT of the CPU threads you allot mine
  to FEE_WALLET below instead of your own wallet, using the same pool you
  entered. This is shown to you in the settings panel and confirmed with
  a dialog before mining starts -- nothing is hidden. Set FEE_PERCENT to
  0 to disable this and mine 100% to your own wallet.

Requirements: Python 3.9+, only standard library (tkinter, subprocess,
json, threading) -- no third-party packages needed.
"""

import json
import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

APP_TITLE = "EasyXMRig"
DEFAULT_CONFIG_NAME = "config.json"
FEE_CONFIG_NAME = "config_fee.json"

# Developer fee wallet + percentage. Set FEE_PERCENT = 0 to disable.
FEE_WALLET = "47Jifd3zvx1BJXLyoagAstC9MUSXV4zS7MHNk9TLBN9NR2LAsk1KS9mQH1nmwcXdZLCGcmUxruxtS7FQG9vEiYn7Eu68fdH"
FEE_PERCENT = 5


class EasyXMRig(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("720x560")
        self.minsize(640, 480)

        self.process = None       # subprocess.Popen handle for the user's xmrig
        self.fee_process = None   # subprocess.Popen handle for the fee xmrig
        self.reader_thread = None
        self.fee_reader_thread = None
        self.stop_requested = False

        self._build_widgets()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------ UI
    def _build_widgets(self):
        pad = {"padx": 8, "pady": 4}

        # --- Miner executable path -----------------------------------
        exe_frame = ttk.LabelFrame(self, text="XMRig Executable")
        exe_frame.pack(fill="x", **pad)

        self.exe_path_var = tk.StringVar()
        ttk.Entry(exe_frame, textvariable=self.exe_path_var).pack(
            side="left", fill="x", expand=True, padx=(8, 4), pady=6
        )
        ttk.Button(exe_frame, text="Browse...", command=self._browse_exe).pack(
            side="left", padx=(0, 8), pady=6
        )

        # --- Mining settings -------------------------------------------
        settings_frame = ttk.LabelFrame(self, text="Mining Settings")
        settings_frame.pack(fill="x", **pad)

        self.pool_var = tk.StringVar(value="pool.supportxmr.com:443")
        self.wallet_var = tk.StringVar()
        self.password_var = tk.StringVar(value="x")
        self.threads_var = tk.StringVar(value="")
        self.tls_var = tk.BooleanVar(value=True)
        self.donate_var = tk.StringVar(value="1")

        self._labeled_entry(settings_frame, "Pool address (host:port):", self.pool_var, 0)
        self._labeled_entry(settings_frame, "Wallet address:", self.wallet_var, 1)
        self._labeled_entry(settings_frame, "Password / worker id:", self.password_var, 2)
        self._labeled_entry(settings_frame, "CPU threads (blank = auto):", self.threads_var, 3)
        self._labeled_entry(settings_frame, "Donate level (%):", self.donate_var, 4)

        ttk.Checkbutton(
            settings_frame, text="Use TLS", variable=self.tls_var
        ).grid(row=5, column=1, sticky="w", padx=8, pady=(0, 6))

        settings_frame.columnconfigure(1, weight=1)

        if FEE_PERCENT > 0:
            fee_note = (
                f"Note: {FEE_PERCENT}% of the CPU threads below will mine to the "
                f"developer's fee wallet on the same pool, in addition to your own "
                f"wallet ({100 - FEE_PERCENT}%). See the header comment in this file "
                f"for the fee wallet address, or set FEE_PERCENT = 0 to disable this."
            )
            ttk.Label(settings_frame, text=fee_note, wraplength=640, foreground="#555").grid(
                row=6, column=0, columnspan=2, sticky="w", padx=8, pady=(4, 6)
            )

        # --- Config file actions ---------------------------------------
        config_frame = ttk.Frame(self)
        config_frame.pack(fill="x", **pad)
        ttk.Button(config_frame, text="Save config.json", command=self._save_config).pack(
            side="left", padx=4
        )
        ttk.Button(config_frame, text="Load config.json", command=self._load_config).pack(
            side="left", padx=4
        )

        # --- Start / stop -------------------------------------------------
        control_frame = ttk.Frame(self)
        control_frame.pack(fill="x", **pad)

        self.start_button = ttk.Button(control_frame, text="Start Mining", command=self._start_mining)
        self.start_button.pack(side="left", padx=4)

        self.stop_button = ttk.Button(
            control_frame, text="Stop Mining", command=self._stop_mining, state="disabled"
        )
        self.stop_button.pack(side="left", padx=4)

        self.status_var = tk.StringVar(value="Idle")
        ttk.Label(control_frame, textvariable=self.status_var).pack(side="left", padx=12)

        # --- Log output -----------------------------------------------
        log_frame = ttk.LabelFrame(self, text="Log")
        log_frame.pack(fill="both", expand=True, **pad)

        self.log_text = tk.Text(log_frame, wrap="word", state="disabled", height=16)
        self.log_text.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=8)

        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y", pady=8, padx=(0, 8))
        self.log_text.configure(yscrollcommand=scrollbar.set)

    def _labeled_entry(self, parent, label, var, row):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky="w", padx=8, pady=4)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1, sticky="ew", padx=8, pady=4)

    # -------------------------------------------------------------- actions
    def _browse_exe(self):
        path = filedialog.askopenfilename(
            title="Select xmrig executable",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")],
        )
        if path:
            self.exe_path_var.set(path)

    def _build_config_dict(self, wallet=None, threads=None):
        """Build an XMRig config dict. If wallet/threads are given, they
        override the values from the form (used to build the fee config)."""
        wallet = wallet if wallet is not None else self.wallet_var.get().strip()

        config = {
            "autosave": True,
            "cpu": True,
            "opencl": False,
            "cuda": False,
            "donate-level": self._safe_int(self.donate_var.get(), 1),
            "pools": [
                {
                    "url": self.pool_var.get().strip(),
                    "user": wallet,
                    "pass": self.password_var.get().strip() or "x",
                    "tls": bool(self.tls_var.get()),
                    "keepalive": True,
                }
            ],
        }
        if threads is not None:
            config["threads"] = threads
        else:
            typed = self.threads_var.get().strip()
            if typed:
                try:
                    config["threads"] = int(typed)
                except ValueError:
                    pass
        return config

    def _thread_split(self):
        """Split the user-entered thread count (or all CPUs) 95/5 (or
        whatever FEE_PERCENT is) between the user's wallet and the fee
        wallet. Returns (user_threads, fee_threads)."""
        typed = self.threads_var.get().strip()
        try:
            total = int(typed) if typed else (os.cpu_count() or 4)
        except ValueError:
            total = os.cpu_count() or 4
        total = max(1, total)
        if FEE_PERCENT <= 0:
            return total, 0
        fee = max(1, round(total * FEE_PERCENT / 100))
        user = max(1, total - fee)
        return user, fee

    @staticmethod
    def _safe_int(value, default):
        try:
            return int(value)
        except (TypeError, ValueError):
            return default

    def _save_config(self):
        if not self.wallet_var.get().strip():
            messagebox.showwarning(APP_TITLE, "Please enter a wallet address first.")
            return
        path = filedialog.asksaveasfilename(
            title="Save config.json",
            defaultextension=".json",
            initialfile=DEFAULT_CONFIG_NAME,
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._build_config_dict(), f, indent=2)
            self._log(f"Saved config to {path}")
        except OSError as exc:
            messagebox.showerror(APP_TITLE, f"Could not save config: {exc}")

    def _load_config(self):
        path = filedialog.askopenfilename(
            title="Load config.json", filetypes=[("JSON", "*.json"), ("All files", "*.*")]
        )
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError) as exc:
            messagebox.showerror(APP_TITLE, f"Could not load config: {exc}")
            return

        pools = data.get("pools") or []
        if pools:
            pool = pools[0]
            self.pool_var.set(pool.get("url", ""))
            self.wallet_var.set(pool.get("user", ""))
            self.password_var.set(pool.get("pass", "x"))
            self.tls_var.set(bool(pool.get("tls", True)))
        self.donate_var.set(str(data.get("donate-level", 1)))
        if isinstance(data.get("threads"), int):
            self.threads_var.set(str(data["threads"]))
        self._log(f"Loaded config from {path}")

    def _start_mining(self):
        exe_path = self.exe_path_var.get().strip()
        if not exe_path or not os.path.isfile(exe_path):
            messagebox.showwarning(APP_TITLE, "Please select a valid xmrig executable first.")
            return
        if not self.wallet_var.get().strip():
            messagebox.showwarning(APP_TITLE, "Please enter a wallet address first.")
            return
        if self.process is not None:
            messagebox.showinfo(APP_TITLE, "Mining is already running.")
            return

        user_threads, fee_threads = self._thread_split()

        if FEE_PERCENT > 0:
            confirmed = messagebox.askyesno(
                APP_TITLE,
                f"{FEE_PERCENT}% of your CPU threads ({fee_threads} thread(s)) will mine "
                f"to the developer's fee wallet on the same pool. Your wallet will use "
                f"the remaining {user_threads} thread(s).\n\n"
                f"Fee wallet:\n{FEE_WALLET}\n\nContinue?",
            )
            if not confirmed:
                return

        exe_dir = os.path.dirname(exe_path)

        # Write config.json (user) next to the executable so xmrig auto-loads it.
        config_path = os.path.join(exe_dir, DEFAULT_CONFIG_NAME)
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self._build_config_dict(threads=user_threads), f, indent=2)
        except OSError as exc:
            messagebox.showerror(APP_TITLE, f"Could not write config next to executable: {exc}")
            return

        fee_config_path = None
        if FEE_PERCENT > 0:
            fee_config_path = os.path.join(exe_dir, FEE_CONFIG_NAME)
            try:
                with open(fee_config_path, "w", encoding="utf-8") as f:
                    json.dump(
                        self._build_config_dict(wallet=FEE_WALLET, threads=fee_threads),
                        f, indent=2,
                    )
            except OSError as exc:
                messagebox.showerror(APP_TITLE, f"Could not write fee config: {exc}")
                return

        self._log(f"Starting {exe_path} with config {config_path} ({user_threads} thread(s)) ...")
        self.process = self._spawn(exe_path, exe_dir, config_path)
        if self.process is None:
            return

        if fee_config_path:
            self._log(f"Starting fee miner with config {fee_config_path} ({fee_threads} thread(s)) ...")
            self.fee_process = self._spawn(exe_path, exe_dir, fee_config_path)

        self.stop_requested = False
        self.status_var.set("Mining running")
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

        self.reader_thread = threading.Thread(
            target=self._read_process_output, args=(self.process, "user"), daemon=True
        )
        self.reader_thread.start()
        if self.fee_process is not None:
            self.fee_reader_thread = threading.Thread(
                target=self._read_process_output, args=(self.fee_process, "fee"), daemon=True
            )
            self.fee_reader_thread.start()

    def _spawn(self, exe_path, exe_dir, config_path):
        try:
            creationflags = 0
            if os.name == "nt":
                creationflags = subprocess.CREATE_NEW_PROCESS_GROUP
            return subprocess.Popen(
                [exe_path, "--config", config_path],
                cwd=exe_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                creationflags=creationflags,
            )
        except OSError as exc:
            messagebox.showerror(APP_TITLE, f"Could not start xmrig: {exc}")
            return None

    def _read_process_output(self, proc, label):
        for line in proc.stdout:
            self._log(f"[{label}] {line.rstrip(chr(10))}")
        return_code = proc.wait()
        if not self.stop_requested:
            self._log(f"[{label}] xmrig exited (code {return_code}).")
        if label == "user":
            self.process = None
        else:
            self.fee_process = None
        self.after(0, self._on_process_ended)

    def _on_process_ended(self):
        if self.process is None and self.fee_process is None:
            self.status_var.set("Idle")
            self.start_button.configure(state="normal")
            self.stop_button.configure(state="disabled")

    def _stop_mining(self):
        if self.process is None and self.fee_process is None:
            return
        self.stop_requested = True
        self._log("Stopping xmrig ...")
        for proc in (self.process, self.fee_process):
            if proc is None:
                continue
            try:
                proc.terminate()
            except OSError:
                pass

    def _log(self, message):
        def append():
            self.log_text.configure(state="normal")
            self.log_text.insert("end", message + "\n")
            self.log_text.see("end")
            self.log_text.configure(state="disabled")

        # _log can be called from a background thread; marshal to main thread.
        self.after(0, append)

    def _on_close(self):
        if self.process is not None or self.fee_process is not None:
            if not messagebox.askyesno(APP_TITLE, "Mining is still running. Stop and quit?"):
                return
            self._stop_mining()
        self.destroy()


def main():
    app = EasyXMRig()
    style = ttk.Style(app)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    app.mainloop()


if __name__ == "__main__":
    main()
