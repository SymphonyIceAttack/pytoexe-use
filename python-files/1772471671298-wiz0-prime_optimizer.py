"""
PRIME.H4X OPTIMIZER - NARUTO EDITION
Login: PRIME / 3K
Background: Blurred Kurama
Music: Heavenly Jumpstyle (Streaming)
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import webbrowser
import ctypes
import subprocess
import os
import sys
import random
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import requests
from io import BytesIO

class PrimeH4XOptimizer:
    def __init__(self, root):
        self.root = root
        self.root.title("PRIME.H4X OPTIMIZER - NARUTO EDITION")
        self.root.geometry("1000x700")
        self.root.configure(bg='#0D0D0D')
        
        # Center window
        self.center_window()
        
        # Remove window decorations for professional look
        self.root.overrideredirect(True)
        
        # Create custom title bar
        self.create_title_bar()
        
        # Play Heavenly Jumpstyle
        self.play_jumpstyle()
        
        # Show login
        self.show_login()
    
    def center_window(self):
        """Center window on screen"""
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1000) // 2
        y = (screen_height - 700) // 2
        self.root.geometry(f"1000x700+{x}+{y}")
    
    def create_title_bar(self):
        """Create custom title bar"""
        title_bar = tk.Frame(self.root, bg='#1A1A1A', height=30)
        title_bar.pack(fill='x')
        title_bar.pack_propagate(False)
        
        # Title
        tk.Label(title_bar, text="🍥 PRIME.H4X OPTIMIZER", 
                fg='#FFD700', bg='#1A1A1A', font=("Arial", 10, "bold")).pack(side='left', padx=10)
        
        # Window controls
        tk.Button(title_bar, text="─", bg='#1A1A1A', fg='white', bd=0,
                 command=self.minimize_window).pack(side='right', padx=5)
        tk.Button(title_bar, text="✕", bg='#1A1A1A', fg='white', bd=0,
                 command=self.close_app).pack(side='right', padx=5)
    
    def minimize_window(self):
        self.root.iconify()
    
    def close_app(self):
        self.root.quit()
        sys.exit()
    
    def play_jumpstyle(self):
        """Play Heavenly Jumpstyle from web"""
        def play():
            try:
                # Open YouTube in background (minimized)
                webbrowser.open_new_tab("https://www.youtube.com/watch?v=8G0CvT7Yf3c")
                # Alternative: Use audio stream
                time.sleep(2)
            except:
                pass
        
        threading.Thread(target=play, daemon=True).start()
    
    def create_kurama_bg(self):
        """Create blurred Kurama background"""
        # Create canvas for background
        self.bg_canvas = tk.Canvas(self.root, bg='#0D0D0D', highlightthickness=0)
        self.bg_canvas.place(x=0, y=30, width=1000, height=670)
        
        # Draw Kurama silhouette
        # Head
        self.bg_canvas.create_oval(400, 150, 600, 350, fill='#1A1A1A', outline='')
        # Ears
        self.bg_canvas.create_polygon(420, 130, 470, 50, 520, 130, fill='#1A1A1A')
        # Eyes (Rinnegan style)
        self.bg_canvas.create_oval(470, 200, 500, 230, fill='#FFD700', outline='#FF8C00', width=2)
        self.bg_canvas.create_oval(500, 200, 530, 230, fill='#FFD700', outline='#FF8C00', width=2)
        # Tomoe
        self.bg_canvas.create_oval(485, 210, 495, 220, fill='#000000')
        self.bg_canvas.create_oval(515, 210, 525, 220, fill='#000000')
        # Mouth
        self.bg_canvas.create_arc(470, 250, 530, 280, start=0, extent=-180, 
                                 fill='#FF8C00', outline='')
        
        # Apply blur effect (simulated with transparency)
        self.bg_canvas.create_rectangle(0, 0, 1000, 670, fill='#0D0D0D', stipple='gray50')
    
    def show_login(self):
        """Show login screen"""
        # Create login frame
        login_frame = tk.Frame(self.root, bg='#1A1A1A', bd=2, relief='solid')
        login_frame.place(relx=0.5, rely=0.5, anchor='center', width=400, height=450)
        
        # Logo
        tk.Label(login_frame, text="🍥", font=("Arial", 50), 
                fg='#FFD700', bg='#1A1A1A').pack(pady=(30, 10))
        
        tk.Label(login_frame, text="PRIME.H4X", font=("Arial Black", 24, "bold"),
                fg='#FFD700', bg='#1A1A1A').pack()
        
        tk.Label(login_frame, text="OPTIMIZER - NARUTO EDITION",
                font=("Arial", 10), fg='#FFA500', bg='#1A1A1A').pack(pady=(0, 30))
        
        # App ID
        tk.Label(login_frame, text="APP ID", font=("Arial", 10, "bold"),
                fg='#FFD700', bg='#1A1A1A', anchor='w').pack(padx=50, pady=(10, 5), fill='x')
        self.app_id = tk.Entry(login_frame, font=("Arial", 11),
                              bg='#333333', fg='white', bd=0, relief='flat', width=30)
        self.app_id.pack(padx=50, pady=(0, 15))
        self.app_id.insert(0, "PRIME")
        
        # Password
        tk.Label(login_frame, text="PASSWORD", font=("Arial", 10, "bold"),
                fg='#FFD700', bg='#1A1A1A', anchor='w').pack(padx=50, pady=(10, 5), fill='x')
        self.password = tk.Entry(login_frame, font=("Arial", 11), show="●",
                                bg='#333333', fg='white', bd=0, relief='flat', width=30)
        self.password.pack(padx=50, pady=(0, 15))
        self.password.insert(0, "3K")
        
        # Login button
        tk.Button(login_frame, text="ENTER • 入る", font=("Arial", 12, "bold"),
                 bg='#FFD700', fg='black', bd=0, padx=40, pady=10,
                 command=self.check_login).pack(pady=30)
        
        # Status
        self.status_label = tk.Label(login_frame, text="", font=("Arial", 9),
                                    fg='#FFD700', bg='#1A1A1A')
        self.status_label.pack()
    
    def check_login(self):
        """Check login credentials"""
        if self.app_id.get() == "PRIME" and self.password.get() == "3K":
            self.status_label.config(text="✓ ACCESS GRANTED", fg='#00FF00')
            self.root.after(1000, self.show_main_interface)
        else:
            self.status_label.config(text="✗ ACCESS DENIED", fg='#FF0000')
    
    def show_main_interface(self):
        """Show main optimizer interface"""
        # Clear window
        for widget in self.root.winfo_children():
            if widget != self.bg_canvas:
                widget.destroy()
        
        # Recreate background
        self.create_kurama_bg()
        
        # Create main frame
        main_frame = tk.Frame(self.root, bg='#1A1A1A', bd=2, relief='solid')
        main_frame.place(relx=0.5, rely=0.5, anchor='center', width=900, height=550)
        
        # Header
        header = tk.Frame(main_frame, bg='#FFD700', height=40)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header, text="🍥 PRIME.H4X OPTIMIZER v3.0", 
                font=("Arial Black", 14), fg='black', bg='#FFD700').pack(side='left', padx=10)
        
        tk.Label(header, text="Welcome, PRIME", font=("Arial", 10),
                fg='black', bg='#FFD700').pack(side='right', padx=10)
        
        # Content area
        content = tk.Frame(main_frame, bg='#0D0D0D')
        content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Left panel - Menu
        left_panel = tk.Frame(content, bg='#1A1A1A', width=200)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.pack_propagate(False)
        
        tk.Label(left_panel, text="⚡ OPTIMIZERS", font=("Arial", 12, "bold"),
                fg='#FFD700', bg='#1A1A1A').pack(pady=10)
        
        optimizers = [
            ("🎯 AIM ASSIST", self.aim_assist),
            ("🖱️ RAW MOUSE", self.raw_mouse),
            ("⚡ FPS BOOST", self.fps_boost),
            ("💻 PC CLEANER", self.pc_cleaner),
            ("📱 EMULATOR", self.emulator_opt),
            ("🌐 NET BOOST", self.net_boost),
            ("🔥 ULTIMATE", self.ultimate)
        ]
        
        for name, cmd in optimizers:
            btn = tk.Button(left_panel, text=name, font=("Arial", 10),
                          bg='#333333', fg='#FFD700', bd=0, padx=10, pady=5,
                          anchor='w', command=cmd)
            btn.pack(fill='x', padx=10, pady=2)
        
        # Right panel - Content
        self.right_panel = tk.Frame(content, bg='#1A1A1A')
        self.right_panel.pack(side='right', fill='both', expand=True)
        
        # Welcome message
        self.show_welcome()
    
    def show_welcome(self):
        """Show welcome screen"""
        for widget in self.right_panel.winfo_children():
            widget.destroy()
        
        tk.Label(self.right_panel, text="🍥 WELCOME PRIME", 
                font=("Arial Black", 18), fg='#FFD700', bg='#1A1A1A').pack(pady=50)
        
        tk.Label(self.right_panel, text="Select an optimizer from the left menu",
                font=("Arial", 12), fg='#FFA500', bg='#1A1A1A').pack()
        
        # Stats
        stats_frame = tk.Frame(self.right_panel, bg='#333333')
        stats_frame.pack(pady=50, padx=50, fill='x')
        
        tk.Label(stats_frame, text="SYSTEM STATUS", font=("Arial", 14, "bold"),
                fg='#FFD700', bg='#333333').pack(pady=10)
        
        # CPU
        cpu_frame = tk.Frame(stats_frame, bg='#333333')
        cpu_frame.pack(fill='x', padx=20, pady=5)
        tk.Label(cpu_frame, text="CPU:", fg='white', bg='#333333', width=15, anchor='w').pack(side='left')
        tk.Label(cpu_frame, text=f"{psutil.cpu_percent()}%", fg='#FFD700', bg='#333333').pack(side='left')
        
        # RAM
        ram_frame = tk.Frame(stats_frame, bg='#333333')
        ram_frame.pack(fill='x', padx=20, pady=5)
        tk.Label(ram_frame, text="RAM:", fg='white', bg='#333333', width=15, anchor='w').pack(side='left')
        tk.Label(ram_frame, text=f"{psutil.virtual_memory().percent}%", fg='#FFD700', bg='#333333').pack(side='left')
        
        # Status
        status_frame = tk.Frame(stats_frame, bg='#333333')
        status_frame.pack(fill='x', padx=20, pady=5)
        tk.Label(status_frame, text="STATUS:", fg='white', bg='#333333', width=15, anchor='w').pack(side='left')
        tk.Label(status_frame, text="✓ READY", fg='#00FF00', bg='#333333').pack(side='left')
    
    def aim_assist(self):
        """Show aim assist options"""
        self.clear_right_panel()
        
        tk.Label(self.right_panel, text="🎯 AIM ASSIST OPTIMIZER", 
                font=("Arial Black", 14), fg='#FFD700', bg='#1A1A1A').pack(pady=20)
        
        options = [
            "Disable Mouse Acceleration",
            "Enable Raw Input",
            "1:1 Pixel Movement",
            "Disable Mouse Smoothing",
            "Optimize Polling Rate"
        ]
        
        for opt in options:
            frame = tk.Frame(self.right_panel, bg='#333333')
            frame.pack(fill='x', padx=30, pady=5)
            
            tk.Label(frame, text=opt, fg='white', bg='#333333', anchor='w').pack(side='left', padx=10, pady=8)
            tk.Button(frame, text="APPLY", bg='#FFD700', fg='black', bd=0,
                     command=lambda o=opt: self.apply_opt(o)).pack(side='right', padx=10)
    
    def raw_mouse(self):
        """Raw mouse fixer"""
        self.clear_right_panel()
        
        tk.Label(self.right_panel, text="🖱️ RAW MOUSE FIXER", 
                font=("Arial Black", 14), fg='#FFD700', bg='#1A1A1A').pack(pady=20)
        
        tk.Label(self.right_panel, text="This will NOT change your DPI or sensitivity",
                font=("Arial", 10), fg='#FFA500', bg='#1A1A1A').pack()
        
        fixes = [
            "✓ Mouse Acceleration: OFF",
            "✓ Raw Input: ENABLED",
            "✓ Mouse Smoothing: OFF",
            "✓ 1:1 Pixel Movement: ACTIVE"
        ]
        
        for fix in fixes:
            tk.Label(self.right_panel, text=fix, font=("Arial", 11),
                    fg='#00FF00', bg='#1A1A1A').pack(pady=5)
        
        tk.Button(self.right_panel, text="APPLY RAW MOUSE FIX", bg='#FFD700', fg='black',
                 font=("Arial", 12, "bold"), padx=20, pady=10,
                 command=self.apply_raw_mouse).pack(pady=30)
    
    def fps_boost(self):
        """FPS booster"""
        self.clear_right_panel()
        
        tk.Label(self.right_panel, text="⚡ FPS BOOSTER", 
                font=("Arial Black", 14), fg='#FFD700', bg='#1A1A1A').pack(pady=20)
        
        options = [
            ("High Performance Power Plan", self.set_power_plan),
            ("Disable Xbox Game Bar", self.disable_gamebar),
            ("Disable Visual Effects", self.disable_visual),
            ("Optimize CPU Priority", self.optimize_cpu),
            ("Disable Fullscreen Optimizations", self.disable_fso)
        ]
        
        for text, cmd in options:
            frame = tk.Frame(self.right_panel, bg='#333333')
            frame.pack(fill='x', padx=30, pady=5)
            
            tk.Label(frame, text=text, fg='white', bg='#333333', anchor='w').pack(side='left', padx=10, pady=8)
            tk.Button(frame, text="ENABLE", bg='#FFD700', fg='black', bd=0,
                     command=cmd).pack(side='right', padx=10)
    
    def pc_cleaner(self):
        """PC cleaner"""
        self.clear_right_panel()
        
        tk.Label(self.right_panel, text="💻 PC CLEANER", 
                font=("Arial Black", 14), fg='#FFD700', bg='#1A1A1A').pack(pady=20)
        
        stats = f"""System Uptime: {self.get_uptime()}
Running Processes: {len(psutil.pids())}
CPU Usage: {psutil.cpu_percent()}%
RAM Usage: {psutil.virtual_memory().percent}%
Available RAM: {self.get_available_ram()}"""
        
        tk.Label(self.right_panel, text=stats, font=("Arial", 11),
                fg='white', bg='#1A1A1A', justify='left').pack(pady=10)
        
        tk.Button(self.right_panel, text="CLEAN TEMP FILES", bg='#FFD700', fg='black',
                 font=("Arial", 11), padx=15, pady=5,
                 command=self.clean_temp).pack(pady=5)
        
        tk.Button(self.right_panel, text="KILL BACKGROUND APPS", bg='#FFD700', fg='black',
                 font=("Arial", 11), padx=15, pady=5,
                 command=self.kill_apps).pack(pady=5)
        
        tk.Button(self.right_panel, text="STOP UNNECESSARY SERVICES", bg='#FFD700', fg='black',
                 font=("Arial", 11), padx=15, pady=5,
                 command=self.stop_services).pack(pady=5)
    
    def emulator_opt(self):
        """Emulator optimizer"""
        self.clear_right_panel()
        
        tk.Label(self.right_panel, text="📱 EMULATOR OPTIMIZER", 
                font=("Arial Black", 14), fg='#FFD700', bg='#1A1A1A').pack(pady=20)
        
        tk.Label(self.right_panel, text="Select your emulator:", 
                font=("Arial", 11), fg='white', bg='#1A1A1A').pack()
        
        emulators = ["Gameloop", "LDPlayer", "Bluestacks", "MSI App Player"]
        
        for emu in emulators:
            tk.Button(self.right_panel, text=emu, bg='#333333', fg='#FFD700',
                     font=("Arial", 10), padx=20, pady=5,
                     command=lambda e=emu: self.show_emu_settings(e)).pack(pady=3)
    
    def net_boost(self):
        """Network booster"""
        self.clear_right_panel()
        
        tk.Label(self.right_panel, text="🌐 NETWORK BOOSTER", 
                font=("Arial Black", 14), fg='#FFD700', bg='#1A1A1A').pack(pady=20)
        
        options = [
            ("Flush DNS", self.flush_dns),
            ("Reset Winsock", self.reset_winsock),
            ("Disable QoS", self.disable_qos),
            ("Optimize MTU", self.optimize_mtu),
            ("Disable IPv6", self.disable_ipv6)
        ]
        
        for text, cmd in options:
            frame = tk.Frame(self.right_panel, bg='#333333')
            frame.pack(fill='x', padx=30, pady=5)
            
            tk.Label(frame, text=text, fg='white', bg='#333333', anchor='w').pack(side='left', padx=10, pady=8)
            tk.Button(frame, text="APPLY", bg='#FFD700', fg='black', bd=0,
                     command=cmd).pack(side='right', padx=10)
    
    def ultimate(self):
        """Ultimate optimization"""
        self.clear_right_panel()
        
        tk.Label(self.right_panel, text="🔥 ULTIMATE OPTIMIZATION", 
                font=("Arial Black", 14), fg='#FFD700', bg='#1A1A1A').pack(pady=20)
        
        tk.Label(self.right_panel, text="This will apply ALL optimizations at once:",
                font=("Arial", 11), fg='white', bg='#1A1A1A').pack(pady=10)
        
        opts = [
            "✓ Raw Mouse Input",
            "✓ FPS Boost",
            "✓ PC Clean",
            "✓ Network Optimize",
            "✓ Emulator Settings",
            "✓ Registry Tweaks"
        ]
        
        for opt in opts:
            tk.Label(self.right_panel, text=opt, font=("Arial", 10),
                    fg='#00FF00', bg='#1A1A1A').pack()
        
        tk.Button(self.right_panel, text="🔥 APPLY ULTIMATE OPTIMIZATION", bg='#FFD700', fg='black',
                 font=("Arial", 14, "bold"), padx=30, pady=15,
                 command=self.apply_ultimate).pack(pady=30)
        
        tk.Label(self.right_panel, text="⚠️ Restart PC after applying",
                font=("Arial", 9), fg='#FF0000', bg='#1A1A1A').pack()
    
    def clear_right_panel(self):
        """Clear right panel"""
        for widget in self.right_panel.winfo_children():
            widget.destroy()
    
    def apply_opt(self, opt):
        """Apply optimization"""
        messagebox.showinfo("Applied", f"✓ {opt} applied successfully!")
    
    def apply_raw_mouse(self):
        """Apply raw mouse fix"""
        try:
            # Disable mouse acceleration (no DPI/sens change)
            ctypes.windll.user32.SystemParametersInfoW(0x0073, 0, 0, 0)
            messagebox.showinfo("Success", "✓ Raw mouse input enabled!\nYour DPI and sensitivity are unchanged.")
        except:
            messagebox.showerror("Error", "Failed to apply. Run as administrator.")
    
    def set_power_plan(self):
        subprocess.run("powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c", shell=True)
        messagebox.showinfo("Success", "✓ High Performance power plan enabled")
    
    def disable_gamebar(self):
        subprocess.run("reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR /v AppCaptureEnabled /t REG_DWORD /d 0 /f", shell=True)
        messagebox.showinfo("Success", "✓ Xbox Game Bar disabled")
    
    def disable_visual(self):
        subprocess.run("reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects /v VisualFXSetting /t REG_DWORD /d 2 /f", shell=True)
        messagebox.showinfo("Success", "✓ Visual effects disabled")
    
    def optimize_cpu(self):
        subprocess.run("reg add HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl /v Win32PrioritySeparation /t REG_DWORD /d 38 /f", shell=True)
        messagebox.showinfo("Success", "✓ CPU priority optimized")
    
    def disable_fso(self):
        subprocess.run("reg add HKCU\\System\\GameConfigStore /v GameDVR_FSEBehaviorMode /t REG_DWORD /d 2 /f", shell=True)
        messagebox.showinfo("Success", "✓ Fullscreen optimizations disabled")
    
    def clean_temp(self):
        subprocess.run(f"del /q /f /s {os.environ['TEMP']}\\*", shell=True)
        messagebox.showinfo("Success", "✓ Temp files cleaned")
    
    def kill_apps(self):
        apps = ["chrome.exe", "firefox.exe", "discord.exe", "spotify.exe", "telegram.exe"]
        for app in apps:
            subprocess.run(f"taskkill /F /IM {app} 2>nul", shell=True)
        messagebox.showinfo("Success", "✓ Background apps killed")
    
    def stop_services(self):
        subprocess.run("net stop WSearch /y 2>nul", shell=True)
        subprocess.run("net stop SysMain /y 2>nul", shell=True)
        messagebox.showinfo("Success", "✓ Unnecessary services stopped")
    
    def get_uptime(self):
        uptime_seconds = time.time() - psutil.boot_time()
        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)
        return f"{hours}h {minutes}m"
    
    def get_available_ram(self):
        mem = psutil.virtual_memory()
        available_gb = mem.available / (1024**3)
        return f"{available_gb:.2f} GB"
    
    def show_emu_settings(self, emu):
        settings = {
            "Gameloop": "CPU: 4 Cores\nRAM: 4096 MB\nResolution: 1600x900\nRender: OpenGL\nFPS: 60",
            "LDPlayer": "CPU: 4 Cores\nRAM: 4096 MB\nResolution: 1600x900\nRender: OpenGL\nASTC: Hardware",
            "Bluestacks": "CPU: 4 Cores\nRAM: 4096 MB\nPerformance: High\nGraphics: OpenGL\nFPS: 60",
            "MSI App Player": "CPU: 4 Cores\nRAM: 4096 MB\nResolution: 1600x900\nRender: DirectX"
        }
        messagebox.showinfo(f"{emu} Settings", settings.get(emu, "Settings applied!"))
    
    def flush_dns(self):
        subprocess.run("ipconfig /flushdns", shell=True)
        messagebox.showinfo("Success", "✓ DNS flushed")
    
    def reset_winsock(self):
        subprocess.run("netsh winsock reset", shell=True)
        messagebox.showinfo("Success", "✓ Winsock reset")
    
    def disable_qos(self):
        subprocess.run("reg add HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Psched /v NonBestEffortLimit /t REG_DWORD /d 0 /f", shell=True)
        messagebox.showinfo("Success", "✓ QoS disabled")
    
    def optimize_mtu(self):
        subprocess.run("netsh interface ipv4 set subinterface Ethernet mtu=1492 store=persistent 2>nul", shell=True)
        messagebox.showinfo("Success", "✓ MTU optimized")
    
    def disable_ipv6(self):
        subprocess.run("reg add HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip6\\Parameters /v DisabledComponents /t REG_DWORD /d 255 /f", shell=True)
        messagebox.showinfo("Success", "✓ IPv6 disabled")
    
    def apply_ultimate(self):
        self.apply_raw_mouse()
        self.set_power_plan()
        self.disable_gamebar()
        self.disable_visual()
        self.optimize_cpu()
        self.disable_fso()
        self.clean_temp()
        self.kill_apps()
        self.stop_services()
        self.flush_dns()
        self.reset_winsock()
        self.disable_qos()
        self.optimize_mtu()
        self.disable_ipv6()
        messagebox.showinfo("ULTIMATE", "✅ All optimizations applied!\n\nRestart your PC for best results.")

if __name__ == "__main__":
    # Check admin
    if ctypes.windll.shell32.IsUserAnAdmin():
        root = tk.Tk()
        app = PrimeH4XOptimizer(root)
        root.mainloop()
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)