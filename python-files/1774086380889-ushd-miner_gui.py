import tkinter as tk
from tkinter import messagebox
import subprocess, json, os, sys, threading, time
import urllib.request

# ── Cesty fungujú aj v .exe (PyInstaller) aj ako .py skript ──────────────
def resource_path(filename):
    """Vráti absolútnu cestu k súboru – funguje aj v --onefile EXE."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, filename)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

def writable_path(filename):
    """Cesta pre súbory ktoré sa zapisujú (config, bat) – vedľa EXE, nie v temp."""
    return os.path.join(os.path.dirname(sys.executable if getattr(sys, 'frozen', False)
                                        else os.path.abspath(__file__)), filename)

CONFIG_FILE  = writable_path("miner_config.json")
BAT_FILE     = writable_path("miner.bat")
SRBMINER_EXE = resource_path("SRBMiner-MULTI.exe")

SRBMINER_API_PORT = 21550   # SRBMiner default API port

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {"server": "stratum-eu.rplant.xyz:7068",
            "wallet": "RAUZBTMcFK6tsc6nAJGiMgh3AzEPYA8Ztu",
            "password": "x",
            "algorithm": "minotaurx"}

def save_config(server, wallet, password, algorithm):
    with open(CONFIG_FILE, "w") as f:
        json.dump({"server": server, "wallet": wallet,
                   "password": password, "algorithm": algorithm}, f, indent=2)

def write_bat(server, wallet, password, algorithm):
    content = (
        "@echo off\n"
        "echo Spustam SRBMiner...\n"
        f'"{SRBMINER_EXE}" --disable-gpu '
        f"--algorithm {algorithm} "
        f"--pool stratum+tcp://{server} "
        f"--wallet {wallet} "
        f"--password {password} "
        f"--api-enable --api-port {SRBMINER_API_PORT}\n"
    )
    with open(BAT_FILE, "w") as f:
        f.write(content)

miner_process = None
polling = False

def fetch_hashrate():
    try:
        url = f"http://127.0.0.1:{SRBMINER_API_PORT}/"
        with urllib.request.urlopen(url, timeout=2) as r:
            data = json.loads(r.read().decode())
        algorithms = data.get("algorithms", [])
        if algorithms:
            algo = algorithms[0]
            hr     = algo.get("hashrate_total_now", 0)
            name   = algo.get("name", "?")
            sh_ok  = algo.get("shares_accepted_total", 0)
            sh_bad = algo.get("shares_rejected_total", 0)
            return hr, name, sh_ok, sh_bad
    except Exception:
        pass
    return None, None, None, None

def fmt_hashrate(hr):
    if hr is None:
        return "N/A", ""
    if hr >= 1_000_000_000:
        return f"{hr/1_000_000_000:.2f}", "GH/s"
    if hr >= 1_000_000:
        return f"{hr/1_000_000:.2f}", "MH/s"
    if hr >= 1_000:
        return f"{hr/1_000:.2f}", "kH/s"
    return f"{hr:.2f}", "H/s"

def poll_loop():
    global polling
    start = time.time()
    while polling:
        hr, algo_name, sh_ok, sh_bad = fetch_hashrate()
        val, unit = fmt_hashrate(hr)
        elapsed = int(time.time() - start)
        h = elapsed // 3600
        m = (elapsed % 3600) // 60
        s = elapsed % 60
        uptime_str = f"{h:02d}:{m:02d}:{s:02d}"
        root.after(0, lambda v=val, u=unit, a=algo_name, ok=sh_ok, bad=sh_bad, ut=uptime_str:
                   update_stats(v, u, a, ok, bad, ut))
        time.sleep(3)

def update_stats(val, unit, algo_name, sh_ok, sh_bad, uptime_str):
    lbl_hr_val.config(text=val)
    lbl_hr_unit.config(text=unit)
    if algo_name:
        lbl_algo.config(text=algo_name.upper())
    if sh_ok is not None:
        lbl_shares.config(text=f"{sh_ok} / {sh_bad or 0}")
    lbl_uptime.config(text=uptime_str)

def start_miner():
    global miner_process, polling
    if miner_process and miner_process.poll() is None:
        messagebox.showinfo("Info", "Miner už beží!")
        return

    server    = entry_server.get().strip()
    wallet    = entry_wallet.get().strip()
    password  = entry_password.get().strip()
    algorithm = entry_algo.get().strip()

    if not server or not wallet or not algorithm:
        messagebox.showwarning("Chyba", "Server, Wallet a Algoritmus musia byť vyplnené!")
        return

    save_config(server, wallet, password, algorithm)
    write_bat(server, wallet, password, algorithm)

    try:
        miner_process = subprocess.Popen(
            [BAT_FILE], shell=True,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
        )
    except Exception as e:
        messagebox.showerror("Chyba pri spustení", str(e))
        return

    status_var.set("● MINER BEŽÍ")
    lbl_status.config(fg="#00e676")
    btn_start.config(state="disabled")
    btn_stop.config(state="normal")
    frame_stats.pack(fill="x", padx=22, pady=(0, 6))
    lbl_algo.config(text=algorithm.upper())

    polling = True
    threading.Thread(target=poll_loop, daemon=True).start()

def stop_miner():
    global miner_process, polling
    polling = False
    if miner_process:
        try:
            miner_process.terminate()
        except Exception:
            pass
        miner_process = None
    status_var.set("● MINER ZASTAVENÝ")
    lbl_status.config(fg="#ff5252")
    btn_start.config(state="normal")
    btn_stop.config(state="disabled")
    frame_stats.pack_forget()

def save_and_update():
    server    = entry_server.get().strip()
    wallet    = entry_wallet.get().strip()
    password  = entry_password.get().strip()
    algorithm = entry_algo.get().strip()
    if not server or not wallet:
        messagebox.showwarning("Chyba", "Server a Wallet musia byť vyplnené!")
        return
    save_config(server, wallet, password, algorithm)
    write_bat(server, wallet, password, algorithm)
    messagebox.showinfo("Uložené", "Konfigurácia uložená a miner.bat aktualizovaný.")

# ─── GUI ───────────────────────────────────────────────────────────────
root = tk.Tk()
root.title("Miner Control Panel — SRBMiner")
root.geometry("540x580")
root.resizable(False, False)

BG    = "#1a1a2e"
CARD  = "#16213e"
ACCENT= "#0f3460"
GREEN = "#00e676"
RED   = "#ff5252"
ORANGE= "#ff9100"
BLUE  = "#64b5f6"
FG    = "#e0e0e0"
FG2   = "#546e7a"
FONT  = ("Consolas", 10)

root.configure(bg=BG)

tk.Label(root, text="⛏  MINER CONTROL PANEL", bg=BG, fg=GREEN,
         font=("Consolas", 14, "bold")).pack(pady=(18, 2))
tk.Label(root, text="SRBMiner-MULTI — nakonfigurujte a ovládajte",
         bg=BG, fg=FG2, font=("Consolas", 9)).pack(pady=(0, 14))

# Config card
card = tk.Frame(root, bg=CARD, padx=18, pady=14)
card.pack(fill="x", padx=22)

def make_row(parent, label, show=""):
    row = tk.Frame(parent, bg=CARD)
    row.pack(fill="x", pady=4)
    tk.Label(row, text=label, bg=CARD, fg=FG2, font=FONT,
             width=16, anchor="w").pack(side="left")
    e = tk.Entry(row, bg=ACCENT, fg=FG, font=FONT, bd=0,
                 insertbackground=GREEN, relief="flat", show=show)
    e.pack(side="left", fill="x", expand=True, ipady=5, padx=(6, 0))
    return e

entry_server   = make_row(card, "Pool / Server:")
entry_wallet   = make_row(card, "Wallet adresa:")
entry_password = make_row(card, "Heslo:")
entry_algo     = make_row(card, "Algoritmus:")

cfg = load_config()
entry_server.insert(0,   cfg.get("server",    "stratum-eu.rplant.xyz:7068"))
entry_wallet.insert(0,   cfg.get("wallet",    "RAUZBTMcFK6tsc6nAJGiMgh3AzEPYA8Ztu"))
entry_password.insert(0, cfg.get("password",  "x"))
entry_algo.insert(0,     cfg.get("algorithm", "minotaurx"))

tk.Button(root, text="💾  Uložiť konfiguráciu", bg=ACCENT, fg=ORANGE,
          font=("Consolas", 10, "bold"), bd=0, padx=10, pady=6,
          activebackground="#1a3a6e", activeforeground=ORANGE,
          cursor="hand2", command=save_and_update).pack(pady=(10, 0))

# Status
status_var = tk.StringVar(value="● MINER ZASTAVENÝ")
lbl_status = tk.Label(root, textvariable=status_var, bg=BG, fg=RED,
                      font=("Consolas", 11, "bold"))
lbl_status.pack(pady=(12, 4))

# Start / Stop buttons
bf = tk.Frame(root, bg=BG)
bf.pack(pady=4)
btn_start = tk.Button(bf, text="▶  START MINER", bg=GREEN, fg="#0a0a0a",
                      font=("Consolas", 11, "bold"), bd=0, padx=16, pady=9,
                      activebackground="#00c853", cursor="hand2", command=start_miner)
btn_start.grid(row=0, column=0, padx=8)
btn_stop = tk.Button(bf, text="■  STOP MINER", bg=RED, fg="#0a0a0a",
                     font=("Consolas", 11, "bold"), bd=0, padx=16, pady=9,
                     activebackground="#d32f2f", cursor="hand2", command=stop_miner,
                     state="disabled")
btn_stop.grid(row=0, column=1, padx=8)

# Hashrate stats panel (zobrazí sa až keď miner beží)
frame_stats = tk.Frame(root, bg=CARD, padx=16, pady=14)

lbl_algo = tk.Label(frame_stats, text="MINOTAURX", bg=ACCENT, fg=BLUE,
                    font=("Consolas", 9, "bold"), padx=10, pady=3)
lbl_algo.pack(pady=(0, 10))

metrics_row = tk.Frame(frame_stats, bg=CARD)
metrics_row.pack(fill="x")

def metric_card(parent, label):
    f = tk.Frame(parent, bg=ACCENT, padx=10, pady=8)
    f.pack(side="left", expand=True, fill="x", padx=4)
    tk.Label(f, text=label, bg=ACCENT, fg=FG2, font=("Consolas", 8)).pack()
    val = tk.Label(f, text="—", bg=ACCENT, fg=GREEN, font=("Consolas", 13, "bold"))
    val.pack()
    return val

lbl_hr_val = metric_card(metrics_row, "Hashrate")
lbl_shares = metric_card(metrics_row, "Shares ok/bad")
lbl_uptime = metric_card(metrics_row, "Uptime")

lbl_hr_unit = tk.Label(frame_stats, text="", bg=CARD, fg=FG2, font=("Consolas", 8))
lbl_hr_unit.pack(pady=(2, 0))

tk.Label(frame_stats, text=f"SRBMiner API: http://127.0.0.1:{SRBMINER_API_PORT}/",
         bg=CARD, fg=FG2, font=("Consolas", 8)).pack(pady=(6, 0))

tk.Label(root, text=f"BAT: {BAT_FILE}", bg=BG, fg="#263238",
         font=("Consolas", 8)).pack(pady=(10, 0))

root.mainloop()
