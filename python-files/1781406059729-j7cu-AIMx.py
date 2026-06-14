import tkinter as tk
from tkinter import ttk, messagebox
import random
import threading
import time

class AimXPro:
    def __init__(self, root):
        self.root = root
        self.root.title("AIMX PRO - Free Fire Tool")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        self.root.configure(bg="#1a1a2e")

        # Variabel status
        self.headshot_status = tk.BooleanVar(value=True)
        self.zero_recoil_status = tk.BooleanVar(value=True)
        self.anti_ban_status = tk.BooleanVar(value=True)
        self.sensitivity = tk.DoubleVar(value=2.5)
        self.logs = []

        # Header
        header = tk.Frame(root, bg="#0f3460", height=80)
        header.pack(fill="x")
        title = tk.Label(header, text="AIMX PRO", font=("Arial", 24, "bold"), bg="#0f3460", fg="#e94560")
        title.pack(pady=15)
        subtitle = tk.Label(header, text="Headshot Precision | Zero Recoil | Anti-Ban", font=("Arial", 10), bg="#0f3460", fg="#ffffff")
        subtitle.pack()

        # Frame utama
        main_frame = tk.Frame(root, bg="#1a1a2e")
        main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        # Fitur toggle
        features = tk.LabelFrame(main_frame, text="FITUR", font=("Arial", 12, "bold"), bg="#1a1a2e", fg="#ffffff", bd=2, relief="groove")
        features.pack(fill="x", pady=5)

        ttk.Checkbutton(features, text="Headshot Precision (Auto Head)", variable=self.headshot_status, style="TCheckbutton").grid(row=0, column=0, sticky="w", padx=10, pady=5)
        ttk.Checkbutton(features, text="Zero Recoil / No Shake", variable=self.zero_recoil_status, style="TCheckbutton").grid(row=0, column=1, sticky="w", padx=10, pady=5)
        ttk.Checkbutton(features, text="Anti-Ban (Safe Mode)", variable=self.anti_ban_status, style="TCheckbutton").grid(row=1, column=0, sticky="w", padx=10, pady=5)

        # Sensitivity slider
        sens_frame = tk.LabelFrame(main_frame, text="MOUSE SENSITIVITY", font=("Arial", 12, "bold"), bg="#1a1a2e", fg="#ffffff", bd=2, relief="groove")
        sens_frame.pack(fill="x", pady=5)

        tk.Label(sens_frame, text="Sensitivity:", bg="#1a1a2e", fg="#ffffff").grid(row=0, column=0, padx=10, pady=10, sticky="w")
        sens_slider = ttk.Scale(sens_frame, from_=1.0, to=5.0, variable=self.sensitivity, orient="horizontal", length=300)
        sens_slider.grid(row=0, column=1, padx=10, pady=10)
        tk.Label(sens_frame, textvariable=self.sensitivity, bg="#1a1a2e", fg="#e94560", width=5).grid(row=0, column=2, padx=5)

        # Tombol inject
        inject_btn = tk.Button(main_frame, text="INJECT / START", bg="#e94560", fg="white", font=("Arial", 14, "bold"), height=2, command=self.start_tool)
        inject_btn.pack(fill="x", pady=15)

        # Log area
        log_frame = tk.LabelFrame(main_frame, text="LOG STATUS", font=("Arial", 10, "bold"), bg="#1a1a2e", fg="#ffffff", bd=2)
        log_frame.pack(fill="both", expand=True, pady=5)
        self.log_text = tk.Text(log_frame, height=8, bg="#16213e", fg="#00ffcc", font=("Consolas", 9), wrap="word", bd=0)
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        scroll = tk.Scrollbar(self.log_text)
        scroll.pack(side="right", fill="y")
        self.log_text.config(yscrollcommand=scroll.set)
        scroll.config(command=self.log_text.yview)

        # Style
        style = ttk.Style()
        style.configure("TCheckbutton", background="#1a1a2e", foreground="#ffffff", font=("Arial", 10))

        # Log awal
        self.add_log("AIMX PRO v1.0 - Ready")
        self.add_log("Aktifkan fitur dan klik INJECT")

    def add_log(self, msg):
        timestamp = time.strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {msg}\n")
        self.log_text.see(tk.END)

    def start_tool(self):
        self.add_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        self.add_log("🔫 AIMX PRO - Injecting...")
        time.sleep(0.5)
        if self.headshot_status.get():
            self.add_log("✓ Headshot Precision [ACTIVE] - Target: HEAD")
        if self.zero_recoil_status.get():
            self.add_log("✓ Zero Recoil [ACTIVE] - No shake, straight bullets")
        if self.anti_ban_status.get():
            self.add_log("✓ Anti-Ban [ACTIVE] - Bypass & safe mode")
        self.add_log(f"✓ Sensitivity: {self.sensitivity.get():.1f}x")
        self.add_log("✅ AIMX PRO berhasil di-inject! Menunggu game...")
        self.add_log("⚠️ Simulasi tool - bukan cheat real. Untuk demo saja.")
        self.add_log("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        
        # Tampilkan pesan selesai
        messagebox.showinfo("AIMX PRO", "Injection selesai!\nFitur aktif sesuai log.\n(Catatan: Tool ini hanya simulasi)")

if __name__ == "__main__":
    root = tk.Tk()
    app = AimXPro(root)
    root.mainloop()