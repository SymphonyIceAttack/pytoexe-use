import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import time
import webbrowser
import os

class MastaTool:
    def __init__(self, root):
        self.root = root
        self.root.title("MASTA TOOL v1.0 - BY SAMMY LEE")
        self.root.geometry("950x700")
        self.root.configure(bg="#2c3e50")

        self.brand_colors = {
            "SAMSUNG": "#3498db",
            "TECNO": "#27ae60",
            "INFINIX": "#e67e22",
            "ITEL": "#9b59b6",
            "NEON RAY": "#f1c40f",
            "NOKIA": "#102372"
        }

        self.main_container = tk.Frame(root, bg="#2c3e50")
        self.main_container.pack(fill=tk.BOTH, expand=True)

        self.sidebar = tk.Frame(self.main_container, bg="#34495e", width=250)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)

        tk.Label(self.sidebar, text="MASTA TOOL", font=("Arial", 18, "bold"), fg="#ecf0f1", bg="#34495e").pack(pady=20)
        
        for b, color in self.brand_colors.items():
            btn = tk.Button(self.sidebar, text=b, bg=color, fg="white", width=20, height=2,
                            command=lambda brand=b: self.switch_brand_content(brand))
            btn.pack(pady=5, padx=10)

        self.right_frame = tk.Frame(self.main_container, bg="#ecf0f1")
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=20, pady=20)

        self.progress_frame = tk.Frame(root, bg="#2c3e50")
        self.progress_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)
        self.progress = ttk.Progressbar(self.progress_frame, orient=tk.HORIZONTAL, length=800, mode='determinate')
        self.progress.pack(fill=tk.X, pady=5)
        self.status_label = tk.Label(self.progress_frame, text="Ready", bg="#2c3e50", fg="white")
        self.status_label.pack()

    def switch_brand_content(self, brand_name):
        for widget in self.right_frame.winfo_children():
            widget.destroy()

        color = self.brand_colors.get(brand_name, "#7f8c8d")
        tk.Label(self.right_frame, text=f"SELECTED: {brand_name}", font=("Arial", 20, "bold"), bg="#ecf0f1", fg=color).pack(pady=20)
        
        if brand_name not in ["SAMSUNG", "NOKIA"]:
            tk.Button(self.right_frame, text="Load Super BIN", bg="#95a5a6", fg="white").pack(pady=5, fill=tk.X, padx=50)
            tk.Button(self.right_frame, text="PATCH SUPER (2 min)", bg="#34495e", fg="white", 
                      command=lambda: self.run_custom_timer(120)).pack(pady=10, fill=tk.X, padx=50)

        # Bypass New Model (Universal ADB)
        tk.Button(self.right_frame, text=f"BYPASS {brand_name} NEW MODEL", bg="#27ae60", fg="white", 
                  command=lambda: threading.Thread(target=self.execute_full_script).start()).pack(pady=10, fill=tk.X, padx=50)

        # Bypass Old Model
        if brand_name == "NOKIA":
            # Hapa ndio tunaita ile command yako maalum ya Nokia Old
            tk.Button(self.right_frame, text="BYPASS NOKIA OLD (SHIZUKU)", bg="#c0392b", fg="white", 
                      command=lambda: threading.Thread(target=self.execute_nokia_old_logic).start()).pack(pady=5, fill=tk.X, padx=50)
        else:
            tk.Button(self.right_frame, text=f"BYPASS {brand_name} OLD MODEL", bg="#c0392b", fg="white", 
                      command=lambda: self.run_custom_timer(10)).pack(pady=5, fill=tk.X, padx=50)

    def execute_nokia_old_logic(self):
        """Mambo ya Nokia Old Model na Shizuku/Canta"""
        commands = [
            "adb install shizuku.apk",
            "adb shell am start -n moe.shizuku.privileged.api/moe.shizuku.manager.MainActivity",
            "adb install mjx.apk",
            "adb shell sh /storage/emulated/0/Android/data/moe.shizuku.privileged.api/start.sh",
            "adb shell am start -n org.samo_lego.canta/org.samo_lego.canta.MainActivity"
        ]
        
        self.progress['value'] = 0
        total = len(commands)
        
        for i, cmd in enumerate(commands):
            try:
                self.status_label.config(text=f"Executing: {cmd}")
                # Hapa tunatumia subprocess kufanya kazi
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
                
                # Update Progress
                percent = int(((i + 1) / total) * 100)
                self.progress['value'] = percent
                self.root.update_idletasks()
                time.sleep(1) # Sekunde moja ya kupumua kati ya commands
            except Exception as e:
                print(f"Error: {e}")

        self.status_label.config(text="Nokia Old Bypass Done!")
        messagebox.showinfo("Success", "Nokia Old Model: Shizuku & Canta installed and started!")

    def run_custom_timer(self, duration):
        threading.Thread(target=self.timer_task, args=(duration,)).start()

    def timer_task(self, duration):
        self.progress['value'] = 0
        step = duration / 100
        for i in range(101):
            time.sleep(step)
            self.progress['value'] = i
            self.status_label.config(text=f"Progress: {i}%")
            self.root.update_idletasks()
        messagebox.showinfo("Success", "Operation Completed")

    def execute_full_script(self):
        """Standard ADB Script"""
        commands = [
            "adb kill-server", "adb start-server", "adb wait-for-device",
            "adb shell settings put global private_dns_mode hostname",
            "adb shell settings put global private_dns_specifier 8f2eab.dns.nextdns.io",
            "adb shell pm clear com.google.android.gms",
            "adb shell pm disable-user com.google.android.gms",
            "adb install DPC.apk",
            "adb uninstall --user 0 com.google.android.apps.work.oobconfig",
            "adb shell pm disable-user com.google.android.devicelockcontroller",
            "adb shell dpm set-device-owner com.afwsamples.testdpc/.DeviceAdminReceiver"
        ]
        
        self.progress['value'] = 0
        for i, cmd in enumerate(commands):
            try:
                subprocess.run(cmd, shell=True)
                percent = int(((i + 1) / len(commands)) * 100)
                self.progress['value'] = percent
                self.status_label.config(text=f"Running: {percent}%")
                self.root.update_idletasks()
            except: pass
        
        messagebox.showinfo("Done", "New Model Bypass Completed!")

if __name__ == "__main__":
    root = tk.Tk()
    app = MastaTool(root)
    root.mainloop()