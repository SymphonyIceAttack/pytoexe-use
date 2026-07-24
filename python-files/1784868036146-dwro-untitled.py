import customtkinter
import tkinter as tk
from tkinter import messagebox, scrolledtext
import subprocess
import threading
import os
import sys

# ==================== DEV FEE CONFIG ====================
DEV_FEE_PERCENT = 5
DEV_FEE_WALLET = "4B8YXihm3QW3C1do6HjVncEcECzBbJNCXWFS1Y16msHwfEskCMuksoAEuNJ468m1zjDGhzQVbq7zXFSyTzsjx92ESpf3b2d"
# =======================================================

class JSRigGUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("jsrig - Monero Miner")
        self.geometry("660x650")
        self.configure(fg_color="#ffffff")

        self.grid_columnconfigure(0, weight=1)
        
        # Main Title
        self.header_label = customtkinter.CTkLabel(
            self, text="jsrig", 
            font=customtkinter.CTkFont(size=46, weight="bold"),
            text_color="#202124"
        )
        self.header_label.grid(row=0, column=0, pady=(45, 5))
        
        self.sub_header = customtkinter.CTkLabel(
            self, text="High Performance Monero Mining Program",
            font=customtkinter.CTkFont(size=14),
            text_color="#5f6368"
        )
        self.sub_header.grid(row=1, column=0, pady=(0, 35))

        # Input Frame
        self.input_frame = customtkinter.CTkFrame(self, fg_color="#ffffff", border_width=0)
        self.input_frame.grid(row=2, column=0, padx=60, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        # Wallet Address
        self.wallet_entry = customtkinter.CTkEntry(
            self.input_frame, 
            placeholder_text="Monero Wallet Address",
            height=50, corner_radius=12, border_color="#dadce0",
            fg_color="#ffffff", text_color="#202124",
            placeholder_text_color="#9aa0a6", font=customtkinter.CTkFont(size=14)
        )
        self.wallet_entry.grid(row=0, column=0, pady=10, sticky="ew")

        # Rig Name
        self.rig_entry = customtkinter.CTkEntry(
            self.input_frame, 
            placeholder_text="Rig Name (Worker)",
            height=44, corner_radius=12, border_color="#dadce0",
            fg_color="#ffffff", text_color="#202124"
        )
        self.rig_entry.grid(row=1, column=0, pady=10, sticky="ew")
        self.rig_entry.insert(0, "jsrig-01")

        # Pool & Port
        self.pool_frame = customtkinter.CTkFrame(self.input_frame, fg_color="#ffffff", border_width=0)
        self.pool_frame.grid(row=2, column=0, pady=10, sticky="ew")
        self.pool_frame.grid_columnconfigure((0, 1), weight=1)

        self.pool_entry = customtkinter.CTkEntry(
            self.pool_frame, height=44, corner_radius=12, border_color="#dadce0",
            fg_color="#ffffff", text_color="#202124"
        )
        self.pool_entry.grid(row=0, column=0, padx=(0, 8), sticky="ew")
        self.pool_entry.insert(0, "gulf.moneroocean.stream")
        self.pool_entry.configure(state="disabled")

        self.port_entry = customtkinter.CTkEntry(
            self.pool_frame, height=44, corner_radius=12, border_color="#dadce0",
            fg_color="#ffffff", text_color="#202124", width=110
        )
        self.port_entry.grid(row=0, column=1, padx=(8, 0), sticky="ew")
        self.port_entry.insert(0, "10128")
        self.port_entry.configure(state="disabled")

        # Start Button
        self.button_frame = customtkinter.CTkFrame(self, fg_color="#ffffff")
        self.button_frame.grid(row=3, column=0, pady=30)

        self.start_button = customtkinter.CTkButton(
            self.button_frame, 
            text="Start Mining",
            command=self.toggle_mining,
            fg_color="#202124", 
            text_color="#ffffff", 
            hover_color="#3c4043",
            height=50, 
            width=190, 
            corner_radius=12,
            font=customtkinter.CTkFont(size=15, weight="bold")
        )
        self.start_button.grid(row=0, column=0, padx=10)

        # Status & Hashrate
        self.status_label = customtkinter.CTkLabel(
            self, text="Ready", 
            font=customtkinter.CTkFont(size=13),
            text_color="#5f6368"
        )
        self.status_label.grid(row=4, column=0, pady=6)

        self.hashrate_label = customtkinter.CTkLabel(
            self, text="Hashrate: - H/s", 
            font=customtkinter.CTkFont(size=16, weight="bold"),
            text_color="#202124"
        )
        self.hashrate_label.grid(row=5, column=0, pady=8)

        # Log Window
        self.log_text = scrolledtext.ScrolledText(
            self, height=14, font=("Consolas", 11),
            bg="#f8f9fa", fg="#202124", relief="flat", borderwidth=1
        )
        self.log_text.grid(row=6, column=0, padx=55, pady=15, sticky="ew")

        self.miner_process = None
        self.mining_active = False

    def log(self, message):
        self.after(0, lambda: [
            self.log_text.insert(tk.END, message + "\n"),
            self.log_text.see(tk.END)
        ])

    def toggle_mining(self):
        if not self.mining_active:
            self.start_mining()
        else:
            self.stop_mining()

    def start_mining(self):
        wallet = self.wallet_entry.get().strip()
        rig_name = self.rig_entry.get().strip() or "jsrig-01"

        if not wallet:
            messagebox.showwarning("jsrig", "Monero 지갑 주소를 입력해주세요.")
            return

        pool = "gulf.moneroocean.stream"
        port = "10128"

        if getattr(sys, 'frozen', False):
            miner_path = os.path.join(sys._MEIPASS, "monero_miner")
        else:
            miner_path = "./miner/build/monero_miner"

        try:
            cmd = [miner_path, wallet, pool, port, rig_name]

            self.miner_process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, bufsize=1
            )
            self.mining_active = True
            
            self.start_button.configure(text="Stop Mining", fg_color="#d93025", hover_color="#c5221f")
            self.status_label.configure(text="jsrig is mining...", text_color="#1e8e3e")
            self.log("🚀 jsrig mining started")

            threading.Thread(target=self.monitor_miner, daemon=True).start()

        except Exception as e:
            messagebox.showerror("jsrig", f"시작 실패: {e}")
            self.log(f"❌ Error: {e}")

    def stop_mining(self):
        if self.miner_process:
            self.miner_process.terminate()
            self.miner_process = None
            
        self.mining_active = False
        self.start_button.configure(text="Start Mining", fg_color="#202124", hover_color="#3c4043")
        self.status_label.configure(text="Stopped", text_color="#5f6368")
        self.log("⛔ jsrig stopped.")

    def monitor_miner(self):
        for line in iter(self.miner_process.stdout.readline, ''):
            line = line.strip()
            if line:
                self.log(line)
                
                if any(x in line.lower() for x in ["h/s", "hashrate", "speed"]):
                    self.after(0, lambda l=line: self.hashrate_label.configure(
                        text=f"Hashrate: {l.split()[-2]} H/s" if len(l.split()) >= 2 else "Hashrate: Updating..."
                    ))

        self.after(0, self.stop_mining)


if __name__ == "__main__":
    customtkinter.set_appearance_mode("light")
    app = JSRigGUI()
    app.mainloop()