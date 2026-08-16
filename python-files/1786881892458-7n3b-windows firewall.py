import tkinter as tk
import subprocess
import random
import time
import os

BG = "#050505"
RED = "#ff1f1f"
DARK_RED = "#5a0000"
GREEN = "#39ff14"
WHITE = "#f2f2f2"

DURATION_SECONDS = 30
OPEN_CAMERA_AT_END = True

fake_lines = [
    "[SCAN] Analisi processi in corso...",
    "[WARN] Attivita sospetta rilevata",
    "[TRACE] Lettura configurazione schede di rete...",
    "[INFO] Firewall: ATTIVO",
    "[ALERT] Accesso non autorizzato rilevato",
    "[SCAN] Verifica integrita sistema...",
    "[WARN] Connessione sconosciuta intercettata",
    "[TRACE] Analisi indirizzi IP locali...",
    "[CRITICAL] Evento di sicurezza ad alta priorita",
]

fake_alerts = [
    "Minaccia critica rilevata.\n\nAzione consigliata: isolamento immediato.",
    "Attivita di rete sospetta.\n\nControllo configurazione IP in corso.",
    "Accesso non autorizzato rilevato.\n\nOrigine: sconosciuta.",
    "Protezione sistema compromessa.\n\nAnalisi in corso...",
    "Connessione remota sospetta.\n\nVerifica firewall richiesta.",
]


class PrankWindow:
    def __init__(self, root):
        self.root = root
        self.running = True
        self.line_count = 0
        self.start_time = time.time()

        self.root.title("Security Center Demo")
        self.root.configure(bg=BG)
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-topmost", True)

        self.build_ui()

        self.root.bind("<Escape>", self.exit_app)
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)

        self.root.after(600, self.open_ipconfig_cmd)
        self.root.after(900, self.add_terminal_line)
        self.root.after(1300, self.open_alert_burst)
        self.root.after(6000, self.alert_loop)
        self.root.after(DURATION_SECONDS * 1000, self.finish)

    def build_ui(self):
        tk.Label(
            self.root,
            text="WINDOWS SECURITY CENTER",
            bg=BG,
            fg=RED,
            font=("Consolas", 34, "bold"),
        ).pack(pady=25)

        self.timer_label = tk.Label(
            self.root,
            text="30",
            bg=BG,
            fg=WHITE,
            font=("Consolas", 18, "bold"),
        )
        self.timer_label.pack()

        self.status = tk.Label(
            self.root,
            text="THREAT LEVEL: CRITICAL",
            bg=BG,
            fg=RED,
            font=("Consolas", 24, "bold"),
        )
        self.status.pack(pady=20)

        self.terminal = tk.Text(
            self.root,
            bg="#000000",
            fg=GREEN,
            insertbackground=GREEN,
            font=("Consolas", 13),
            width=115,
            height=25,
            borderwidth=2,
            relief="solid",
        )
        self.terminal.pack(pady=15)
        self.terminal.configure(state="disabled")

        self.update_timer()

    def update_timer(self):
        if not self.running:
            return

        elapsed = int(time.time() - self.start_time)
        remaining = max(0, DURATION_SECONDS - elapsed)
        self.timer_label.configure(text=f"AUTO CLOSE IN: {remaining}s")

        if remaining > 0:
            self.root.after(250, self.update_timer)

    def write_line(self, text):
        timestamp = time.strftime("%H:%M:%S")
        self.terminal.configure(state="normal")
        self.terminal.insert("end", f"{timestamp}  {text}\n")
        self.terminal.see("end")
        self.terminal.configure(state="disabled")

    def add_terminal_line(self):
        if not self.running:
            return

        self.write_line(random.choice(fake_lines))
        self.line_count += 1

        if self.line_count % 4 == 0:
            self.status.configure(
                text=random.choice([
                    "THREAT LEVEL: CRITICAL",
                    "SYSTEM BREACH DETECTED",
                    "FIREWALL WARNING",
                    "NETWORK EVENT DETECTED",
                ])
            )

        self.root.after(random.randint(180, 550), self.add_terminal_line)

    def open_fake_alert(self):
        if not self.running:
            return

        win = tk.Toplevel(self.root)
        win.title("Security Alert")
        win.configure(bg="#111111")
        win.geometry(f"430x190+{random.randint(60, 950)}+{random.randint(60, 560)}")
        win.attributes("-topmost", True)

        tk.Label(
            win,
            text="SECURITY ALERT",
            bg="#111111",
            fg=RED,
            font=("Consolas", 18, "bold"),
        ).pack(pady=12)

        tk.Label(
            win,
            text=random.choice(fake_alerts),
            bg="#111111",
            fg=WHITE,
            font=("Consolas", 11),
            justify="center",
            wraplength=370,
        ).pack(pady=8)

        win.after(random.randint(3500, 7000), win.destroy)

    def open_alert_burst(self):
        for i in range(10):
            self.root.after(i * 220, self.open_fake_alert)

    def alert_loop(self):
        if not self.running:
            return

        for i in range(random.randint(3, 7)):
            self.root.after(i * 220, self.open_fake_alert)

        self.root.after(random.randint(2500, 4500), self.alert_loop)

    def open_ipconfig_cmd(self):
        try:
            subprocess.Popen(
                ["cmd", "/k", "ipconfig"],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
            )
            self.write_line("[CMD] ipconfig avviato")
        except Exception as e:
            self.write_line(f"[ERROR] Impossibile aprire CMD: {e}")

    def open_camera_app(self):
        if not OPEN_CAMERA_AT_END:
            return

        try:
            os.startfile("microsoft.windows.camera:")
        except Exception:
            try:
                subprocess.Popen(["start", "microsoft.windows.camera:"], shell=True)
            except Exception:
                pass

    def finish(self):
        self.open_camera_app()
        self.exit_app()

    def exit_app(self, event=None):
        self.running = False
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = PrankWindow(root)
    root.mainloop()