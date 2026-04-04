import tkinter as tk
from tkinter import messagebox, ttk
import json
import threading
import time
import MetaTrader5 as mt5
import os

# ------------------ CONFIGURATION ------------------
SERVER_URL = "https://yourserver.com/login"  # Replace with real endpoint
ACCOUNTS_FILE = "accounts.json"
# ---------------------------------------------------


# ------------------ SERVER LOGIN ------------------
def server_login(username, password):
    """
    Replace this stub with a real requests.post() call to your auth server.
    Example:
        import requests
        res = requests.post(SERVER_URL, json={"username": username, "password": password})
        return res.json()
    """
    # WARNING: Remove hardcoded credentials before deploying
    if username == "prouser" and password == "password123":
        return {"status": "success", "message": "Login successful"}
    return {"status": "fail", "message": "Invalid credentials"}


# ------------------ ACCOUNT MANAGEMENT ------------------
def load_accounts():
    if os.path.exists(ACCOUNTS_FILE):
        with open(ACCOUNTS_FILE, "r") as f:
            return json.load(f)
    return []


def save_accounts(accounts):
    with open(ACCOUNTS_FILE, "w") as f:
        json.dump(accounts, f, indent=4)


# ------------------ SIGNAL COPYING ------------------
def copy_signal_to_accounts(signal, log_callback=None):
    """
    Execute a signal across all stored accounts.
    signal format: {"symbol": "EURUSD", "lot": 0.1, "action": "buy", "sl": 1.0800, "tp": 1.0900}
    """
    accounts = load_accounts()

    if not accounts:
        if log_callback:
            log_callback("[WARN] No accounts configured.")
        return

    for acc in accounts:
        login = acc.get("login")
        server = acc.get("server")
        password = acc.get("password")
        platform = acc.get("platform", "").upper()

        if platform != "MT5":
            if log_callback:
                log_callback(f"[SKIP] {login} — only MT5 supported currently.")
            continue

        # Connect to this account
        if not mt5.initialize(login=int(login), server=server, password=password):
            err = mt5.last_error()
            if log_callback:
                log_callback(f"[ERROR] MT5 connect failed for {login}: {err}")
            continue

        try:
            symbol = signal["symbol"]
            lot = float(signal["lot"])
            action = signal["action"].lower()
            sl = signal.get("sl", 0.0)
            tp = signal.get("tp", 0.0)

            # Validate symbol exists on this broker
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                if log_callback:
                    log_callback(f"[ERROR] Symbol {symbol} not found on account {login}.")
                continue

            price = tick.ask if action == "buy" else tick.bid
            order_type = mt5.ORDER_TYPE_BUY if action == "buy" else mt5.ORDER_TYPE_SELL

            # Validate lot size
            symbol_info = mt5.symbol_info(symbol)
            if symbol_info:
                min_lot = symbol_info.volume_min
                max_lot = symbol_info.volume_max
                lot = max(min_lot, min(lot, max_lot))

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": lot,
                "type": order_type,
                "price": price,
                "sl": sl,
                "tp": tp,
                "deviation": 20,
                "magic": 123456,
                "comment": "Lord Beerus Copier",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }

            result = mt5.order_send(request)

            if result is None or result.retcode != mt5.TRADE_RETCODE_DONE:
                err_msg = result.comment if result else "No response"
                if log_callback:
                    log_callback(f"[FAIL] {symbol} on {login}: {err_msg}")
            else:
                if log_callback:
                    log_callback(
                        f"[OK] {action.upper()} {lot} {symbol} @ {price:.5f} "
                        f"| SL:{sl} TP:{tp} | Account {login} | Ticket #{result.order}"
                    )

        except Exception as e:
            if log_callback:
                log_callback(f"[EXCEPTION] {login}: {e}")

        finally:
            mt5.shutdown()  # Always disconnect, even on error


def simulate_signal_stream(log_callback=None):
    """Simulates incoming signals for testing. Replace with real Telegram listener."""
    signals = [
        {"symbol": "EURUSD", "lot": 0.1, "action": "buy",  "sl": 1.07800, "tp": 1.09200},
        {"symbol": "GBPUSD", "lot": 0.2, "action": "sell", "sl": 1.28500, "tp": 1.26000},
    ]
    for sig in signals:
        if log_callback:
            log_callback(f"[SIGNAL] Received: {sig}")
        copy_signal_to_accounts(sig, log_callback=log_callback)
        time.sleep(5)


# ------------------ GUI ------------------
class BeerusCopierGUI:
    def __init__(self, root):
        self.root = root
        root.title("Lord Beerus Signal Copier")
        root.geometry("560x480")
        root.resizable(False, False)

        self.notebook = ttk.Notebook(root)
        self.notebook.pack(expand=True, fill="both")

        self._build_login_tab()
        self._build_accounts_tab()
        self._build_signals_tab()

        self.refresh_accounts_list()

    # ── LOGIN TAB ──────────────────────────────────────────
    def _build_login_tab(self):
        self.login_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.login_frame, text="Login")

        ttk.Label(self.login_frame, text="Username:").pack(pady=(20, 2))
        self.username_entry = ttk.Entry(self.login_frame, width=30)
        self.username_entry.pack(pady=2)

        ttk.Label(self.login_frame, text="Password:").pack(pady=(10, 2))
        self.password_entry = ttk.Entry(self.login_frame, show="*", width=30)
        self.password_entry.pack(pady=2)

        ttk.Button(self.login_frame, text="Login", command=self.login).pack(pady=20)

    def login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get().strip()
        if not username or not password:
            messagebox.showwarning("Login", "Please enter username and password.")
            return
        res = server_login(username, password)
        messagebox.showinfo("Login Status", res["message"])

    # ── ACCOUNTS TAB ───────────────────────────────────────
    def _build_accounts_tab(self):
        self.accounts_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.accounts_frame, text="Accounts")

        self.accounts_listbox = tk.Listbox(self.accounts_frame, height=10)
        self.accounts_listbox.pack(expand=True, fill="both", padx=10, pady=10)

        btn_frame = ttk.Frame(self.accounts_frame)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Add Account", command=self.add_account_popup).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Remove Selected", command=self.remove_selected_account).pack(side="left", padx=5)

    def refresh_accounts_list(self):
        self.accounts_listbox.delete(0, tk.END)
        for acc in load_accounts():
            self.accounts_listbox.insert(
                tk.END,
                f"{acc.get('platform','?')} | {acc.get('login','?')} | {acc.get('server','?')}"
            )

    def add_account_popup(self):
        popup = tk.Toplevel(self.root)
        popup.title("Add MT5 Account")
        popup.geometry("300x280")
        popup.grab_set()  # Modal

        fields = {}
        labels = [("Platform (MT4/MT5):", "platform"),
                  ("Login (Account #):", "login"),
                  ("Password:", "password"),
                  ("Server:", "server")]

        for label_text, key in labels:
            ttk.Label(popup, text=label_text).pack(pady=(8, 0))
            entry = ttk.Entry(popup, width=28, show="*" if key == "password" else "")
            entry.pack()
            fields[key] = entry

        def save():
            acc = {k: v.get().strip() for k, v in fields.items()}
            if not all(acc.values()):
                messagebox.showwarning("Missing Fields", "All fields are required.", parent=popup)
                return
            accounts = load_accounts()
            accounts.append(acc)
            save_accounts(accounts)
            self.refresh_accounts_list()
            popup.destroy()
            messagebox.showinfo("Account Added", f"Account {acc['login']} saved.")

        ttk.Button(popup, text="Save Account", command=save).pack(pady=14)

    def remove_selected_account(self):
        selected = self.accounts_listbox.curselection()
        if not selected:
            messagebox.showwarning("Remove Account", "No account selected.")
            return
        idx = selected[0]
        accounts = load_accounts()
        removed = accounts.pop(idx)
        save_accounts(accounts)
        self.refresh_accounts_list()
        messagebox.showinfo("Removed", f"Account {removed.get('login')} removed.")

    # ── SIGNALS TAB ────────────────────────────────────────
    def _build_signals_tab(self):
        self.signals_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.signals_frame, text="Signals")

        ttk.Button(
            self.signals_frame,
            text="▶  Start Signal Stream",
            command=self.start_signal_thread
        ).pack(pady=14)

        ttk.Label(self.signals_frame, text="Log:").pack(anchor="w", padx=10)

        log_frame = ttk.Frame(self.signals_frame)
        log_frame.pack(expand=True, fill="both", padx=10, pady=4)

        self.log_box = tk.Text(log_frame, height=14, state="disabled", bg="#111", fg="#00ff88",
                               font=("Courier", 9), wrap="word")
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_box.yview)
        self.log_box.configure(yscrollcommand=scrollbar.set)
        self.log_box.pack(side="left", expand=True, fill="both")
        scrollbar.pack(side="right", fill="y")

    def log(self, message):
        """Thread-safe log to the text box."""
        def _write():
            self.log_box.config(state="normal")
            self.log_box.insert(tk.END, f"{time.strftime('%H:%M:%S')}  {message}\n")
            self.log_box.see(tk.END)
            self.log_box.config(state="disabled")
        self.root.after(0, _write)  # Schedule on main thread

    def start_signal_thread(self):
        """Run signal stream in background thread so UI stays responsive."""
        t = threading.Thread(
            target=simulate_signal_stream,
            kwargs={"log_callback": self.log},
            daemon=True
        )
        t.start()
        self.log("[INFO] Signal stream started.")


# ------------------ ENTRY POINT ------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = BeerusCopierGUI(root)
    root.mainloop()
