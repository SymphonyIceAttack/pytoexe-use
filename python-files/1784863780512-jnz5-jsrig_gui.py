import customtkinter
import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import os
import sys

# Google-like Minimalist Theme Colors
GOOGLE_BLUE = "#1a73e8"
GOOGLE_WHITE = "#ffffff"
GOOGLE_GRAY = "#f8f9fa"
GOOGLE_TEXT = "#3c4043"
GOOGLE_BORDER = "#dadce0"

class JSRigGUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("jsrig - High Performance Miner")
        self.geometry("600(450")
        self.configure(fg_color=GOOGLE_WHITE)

        # Center the window
        self.grid_columnconfigure(0, weight=1)
        
        # Header (jsrig Logo)
        self.header_label = customtkinter.CTkLabel(
            self, text="jsrig", font=customtkinter.CTkFont(family="Product Sans", size=50, weight="bold"),
            text_color=GOOGLE_BLUE
        )
        self.header_label.grid(row=0, column=0, pady=(40, 5))
        
        self.sub_header = customtkinter.CTkLabel(
            self, text="Next-Gen Monero Mining Engine", font=customtkinter.CTkFont(size=14),
            text_color=GOOGLE_TEXT
        )
        self.sub_header.grid(row=1, column=0, pady=(0, 30))

        # Main Input Container
        self.input_frame = customtkinter.CTkFrame(self, fg_color=GOOGLE_WHITE, border_width=0)
        self.input_frame.grid(row=2, column=0, padx=50, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)

        # Wallet Entry
        self.wallet_entry = customtkinter.CTkEntry(
            self.input_frame, placeholder_text="Monero Wallet Address",
            height=45, corner_radius=22, border_color=GOOGLE_BORDER,
            fg_color=GOOGLE_WHITE, text_color=GOOGLE_TEXT,
            placeholder_text_color="#9aa0a6", font=customtkinter.CTkFont(size=14)
        )
        self.wallet_entry.grid(row=0, column=0, pady=10, sticky="ew")

        # Pool & Port Row
        self.config_frame = customtkinter.CTkFrame(self.input_frame, fg_color=GOOGLE_WHITE)
        self.config_frame.grid(row=1, column=0, pady=5, sticky="ew")
        self.config_frame.grid_columnconfigure((0, 1), weight=1)

        self.pool_entry = customtkinter.CTkEntry(
            self.config_frame, placeholder_text="Pool Host",
            height=40, corner_radius=20, border_color=GOOGLE_BORDER,
            fg_color=GOOGLE_WHITE, text_color=GOOGLE_TEXT
        )
        self.pool_entry.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        self.pool_entry.insert(0, "pool.supportxmr.com")

        self.port_entry = customtkinter.CTkEntry(
            self.config_frame, placeholder_text="Port",
            height=40, corner_radius=20, border_color=GOOGLE_BORDER,
            fg_color=GOOGLE_WHITE, text_color=GOOGLE_TEXT
        )
        self.port_entry.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        self.port_entry.insert(0, "3333")

        # Action Buttons
        self.button_frame = customtkinter.CTkFrame(self, fg_color=GOOGLE_WHITE)
        self.button_frame.grid(row=3, column=0, pady=30)

        self.start_button = customtkinter.CTkButton(
            self.button_frame, text="Start Mining", command=self.toggle_mining,
            fg_color=GOOGLE_GRAY, text_color=GOOGLE_TEXT, hover_color="#f1f3f4",
            height=36, width=120, corner_radius=4, border_width=1, border_color=GOOGLE_GRAY
        )
        self.start_button.grid(row=0, column=0, padx=10)

        self.status_label = customtkinter.CTkLabel(
            self, text="jsrig engine ready", font=customtkinter.CTkFont(size=12),
            text_color="#70757a"
        )
        self.status_label.grid(row=4, column=0, pady=(0, 20))

        self.miner_process = None
        self.mining_active = False

    def toggle_mining(self):
        if not self.mining_active:
            self.start_mining()
        else:
            self.stop_mining()

    def start_mining(self):
        wallet = self.wallet_entry.get()
        pool = self.pool_entry.get()
        port = self.port_entry.get()

        if not wallet:
            messagebox.showwarning("jsrig", "Please enter a wallet address.")
            return

        if getattr(sys, 'frozen', False):
            miner_path = os.path.join(sys._MEIPASS, "monero_miner")
        else:
            miner_path = "./miner/build/monero_miner"

        try:
            self.miner_process = subprocess.Popen(
                [miner_path, wallet, pool, port],
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1
            )
            self.mining_active = True
            self.start_button.configure(text="Stop Mining", fg_color="#ea4335", text_color=GOOGLE_WHITE)
            self.status_label.configure(text="jsrig is working...", text_color=GOOGLE_BLUE)
            threading.Thread(target=self.monitor_miner, daemon=True).start()
        except Exception as e:
            messagebox.showerror("Error", f"jsrig failed to start: {e}")

    def stop_mining(self):
        if self.miner_process:
            self.miner_process.terminate()
            self.miner_process = None
        self.mining_active = False
        self.start_button.configure(text="Start Mining", fg_color=GOOGLE_GRAY, text_color=GOOGLE_TEXT)
        self.status_label.configure(text="jsrig stopped", text_color="#70757a")

    def monitor_miner(self):
        for line in iter(self.miner_process.stdout.readline, ''):
            if "Submitting share" in line:
                self.after(0, lambda l=line: self.status_label.configure(text=f"Last Share: {l.strip()}"))
        self.after(0, self.stop_mining)

if __name__ == "__main__":
    customtkinter.set_appearance_mode("light")
    app = JSRigGUI()
    app.mainloop()
