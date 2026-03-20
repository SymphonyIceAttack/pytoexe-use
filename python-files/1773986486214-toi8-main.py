import customtkinter as ctk
import psutil
import os
import subprocess
import time
import tkinter as tk

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

ACCENT = "#8a2be2"


# ================= FPS ENGINE =================

class FPSOptimizerEngine:

    def __init__(self):
        self.safe_close = [
            "chrome.exe",          # Chrome consumes a lot of resources
            "discord.exe",         # Discord with overlay
            "spotify.exe",         # Spotify can take CPU/RAM
            "teams.exe",           # Teams takes a lot of memory
            "onedrive.exe",        # OneDrive sync takes system resources
            "steamwebhelper.exe",  # Steam Web Helper
            "dropbox.exe",         # Dropbox background process
            "skype.exe",           # Skype background process
            "windowsupdate.exe",   # Windows update process (takes CPU)
            "wuauserv",            # Windows Update Service
            "svchost.exe"          # Some of these services can be disabled temporarily
        ]
        
        self.fps_mode = False

    # ================= 1. CLOSE NON-ESSENTIAL PROCESSES =================
    def cleanup(self):
        for p in psutil.process_iter(["name"]):
            try:
                name = p.info["name"].lower()
                if name in self.safe_close:
                    print(f"[FPS] Terminating {name} to free up system resources.")
                    p.terminate()
            except Exception as e:
                print(f"[FPS] Error terminating process: {e}")

    # ================= 2. DISABLE SYSTEM SERVICES =================
    def disable_system_services(self):
        services_to_stop = [
            "wuauserv",  # Windows Update Service
            "bits",      # Background Intelligent Transfer Service
            "superfetch",  # Windows Superfetch
            "services.exe",  # Sometimes, this takes a lot of CPU
            "TaskHostW.exe"  # Task Scheduler background task
        ]
        for service in services_to_stop:
            try:
                subprocess.call(f"sc stop {service}")
                print(f"[FPS] Disabled {service} service")
            except Exception as e:
                print(f"[FPS] Failed to disable {service}: {e}")

    # ================= 3. SET CPU TO MAX PERFORMANCE =================
    def set_cpu_performance(self):
        os.system("powercfg -setactive SCHEME_MIN")
        print("[FPS] CPU power settings set to maximum performance.")

    # ================= 4. DISABLE VISUAL EFFECTS =================
    def disable_visual_effects(self):
        print("[FPS] Disabling Windows visual effects (animations, transparency)")
        subprocess.call('SystemPropertiesPerformance.exe /pagefile')  # Open the settings window

    # ================= 5. FORCE GAME TO HIGH PRIORITY =================
    def game_boost(self, proc):
        try:
            proc.nice(psutil.HIGH_PRIORITY_CLASS)  # Set the game's priority to High
            print(f"[FPS] Game process priority set to high.")
        except Exception as e:
            print(f"[FPS] Error boosting game process priority: {e}")

    # ================= 6. ENABLE FPS MODE =================
    def enable_fps_mode(self):
        self.fps_mode = True
        self.set_cpu_performance()
        self.cleanup()  # Close unnecessary background processes
        self.disable_system_services()  # Disable unnecessary system services
        self.disable_visual_effects()  # Disable visual effects for smoother experience
        print("[FPS] Full FPS optimization activated!")

    def disable_fps_mode(self):
        self.fps_mode = False
        os.system("powercfg -setactive SCHEME_BALANCED")
        print("[FPS] Disabled FPS Mode and reverted to balanced power settings.")

    # ================= GAME LAUNCH =================
    def launch_game(self, game):
        self.enable_fps_mode()
        if game == "cs2":
            os.system('start "" "steam://rungameid/730"')
        elif game == "r6":
            os.system('start "" "steam://rungameid/359550"')
        elif game == "rust":
            os.system('start "" "steam://rungameid/252490"')


# ================= MAIN UI =================

class App(ctk.CTk):

    def __init__(self):
        super().__init__()

        self.engine = FPSOptimizerEngine()

        self.geometry("1000x600")
        self.title("FPS Optimizer Pro")

        self.sidebar = ctk.CTkFrame(self, width=220)
        self.sidebar.pack(side="left", fill="y")

        self.main = ctk.CTkFrame(self)
        self.main.pack(side="right", expand=True, fill="both")

        self.build_sidebar()
        self.dashboard()

        self.update_stats()

    # ================= SIDEBAR =================

    def build_sidebar(self):

        ctk.CTkLabel(self.sidebar, text="FPS OPTIMIZER", font=("Arial", 18, "bold")).pack(pady=20)

        ctk.CTkButton(self.sidebar, text="Dashboard", command=self.dashboard).pack(fill="x", pady=5)

        ctk.CTkButton(self.sidebar, text="CS2", command=lambda: self.engine.launch_game("cs2")).pack(fill="x", pady=2)
        ctk.CTkButton(self.sidebar, text="R6", command=lambda: self.engine.launch_game("r6")).pack(fill="x", pady=2)
        ctk.CTkButton(self.sidebar, text="Rust", command=lambda: self.engine.launch_game("rust")).pack(fill="x", pady=2)

        ctk.CTkButton(
            self.sidebar,
            text="⚡ Enable FPS Mode",
            fg_color=ACCENT,
            command=self.engine.enable_fps_mode
        ).pack(fill="x", pady=10)

        ctk.CTkButton(
            self.sidebar,
            text="🛑 Disable FPS Mode",
            command=self.engine.disable_fps_mode
        ).pack(fill="x", pady=5)

    # ================= DASHBOARD =================

    def dashboard(self):
        for w in self.main.winfo_children():
            w.destroy()

        self.cpu = ctk.CTkLabel(self.main, text="CPU: 0%")
        self.cpu.pack(pady=10)

        self.ram = ctk.CTkLabel(self.main, text="RAM: 0%")
        self.ram.pack(pady=10)

        self.fps_tip = ctk.CTkLabel(
            self.main,
            text="Tip: Lower shadows + disable overlays = biggest FPS gain"
        )
        self.fps_tip.pack(pady=20)

    # ================= LIVE STATS =================

    def update_stats(self):
        if hasattr(self, "cpu"):
            self.cpu.configure(text=f"CPU: {psutil.cpu_percent()}%")
            self.ram.configure(text=f"RAM: {psutil.virtual_memory().percent}%")

        self.after(1000, self.update_stats)


# ================= RUN =================

App().mainloop()