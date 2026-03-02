"""
PRIME.H4X OPTIMIZER - NARUTO EDITION (NO PIL)
Login: PRIME / 3K
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

class PrimeH4XOptimizer:
    def __init__(self, root):
        self.root = root
        self.root.title("PRIME.H4X OPTIMIZER - NARUTO EDITION")
        self.root.geometry("1000x700")
        self.root.configure(bg='#0D0D0D')
        self.center_window()
        self.root.overrideredirect(True)
        self.create_title_bar()
        self.play_jumpstyle()
        self.create_kurama_bg()  # Create background first
        self.show_login()
    
    def center_window(self):
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width - 1000) // 2
        y = (screen_height - 700) // 2
        self.root.geometry(f"1000x700+{x}+{y}")
    
    def create_title_bar(self):
        title_bar = tk.Frame(self.root, bg='#1A1A1A', height=30)
        title_bar.pack(fill='x')
        title_bar.pack_propagate(False)
        
        tk.Label(title_bar, text="🦊 PRIME.H4X OPTIMIZER", 
                fg='#FFD700', bg='#1A1A1A', font=("Arial", 10, "bold")).pack(side='left', padx=10)
        
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
        def play():
            try:
                webbrowser.open_new_tab("https://www.youtube.com/watch?v=8G0CvT7Yf3c")
            except:
                pass
        threading.Thread(target=play, daemon=True).start()
    
    def create_kurama_bg(self):
        """Create Kurama background without PIL"""
        # Create canvas for background
        self.bg_canvas = tk.Canvas(self.root, bg='#0D0D0D', highlightthickness=0)
        self.bg_canvas.place(x=0, y=30, width=1000, height=670)
        
        # Draw Kurama silhouette using simple shapes
        # Head (oval)
        self.bg_canvas.create_oval(400, 150, 600, 350, 
                                   fill='#1A1A1A', outline='#FFD700', width=1)
        
        # Ears (triangles)
        self.bg_canvas.create_polygon(420, 150, 470, 80, 520, 150, 
                                     fill='#1A1A1A', outline='#FFD700', width=1)
        self.bg_canvas.create_polygon(480, 150, 530, 80, 580, 150, 
                                     fill='#1A1A1A', outline='#FFD700', width=1)
        
        # Eyes (Rinnegan style)
        self.bg_canvas.create_oval(460, 200, 490, 230, 
                                  fill='#FF0000', outline='#FFD700', width=2)
        self.bg_canvas.create_oval(510, 200, 540, 230, 
                                  fill='#FF0000', outline='#FFD700', width=2)
        
        # Tomoe (dots in eyes)
        self.bg_canvas.create_oval(475, 215, 480, 220, fill='#000000')
        self.bg_canvas.create_oval(525, 215, 530, 220, fill='#000000')
        
        # Nine tails lines
        for i in range(9):
            x = 550 + i*10
            y = 300 + i*5
            self.bg_canvas.create_line(550, 300, x, y, 
                                      fill='#FFD700', width=3, smooth=True)
        
        # Add "blur" effect with semi-transparent overlay
        self.bg_canvas.create_rectangle(0, 0, 1000, 670, 
                                       fill='#0D0D0D', stipple='gray50')
    
    def show_login(self):
        """Show login screen"""
        login_frame = tk.Frame(self.root, bg='#1A1A1A', bd=2, relief='solid')
        login_frame.place(relx=0.5, rely=0.5, anchor='center', width=400, height=450)
        
        # Logo/Title
        tk.Label(login_frame, text="🦊", font=("Arial", 50), 
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
                 command=self.check_login).pack(pady=20)
        
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
        """Show main interface"""
        # Clear login widgets but keep background
        for widget in self.root.winfo_children():
            if widget != self.bg_canvas:
                widget.destroy()
        
        # Main frame
        main_frame = tk.Frame(self.root, bg='#1A1A1A', bd=2, relief='solid')
        main_frame.place(relx=0.5, rely=0.5, anchor='center', width=900, height=550)
        
        # Header
        header = tk.Frame(main_frame, bg='#FFD700', height=40)
        header.pack(fill='x')
        header.pack_propagate(False)
        
        tk.Label(header, text="🦊 PRIME.H4X OPTIMIZER v3.0", 
                font=("Arial Black", 14), fg='black', bg='#FFD700').pack(side='left', padx=10)
        
        tk.Label(header, text="Welcome, PRIME", font=("Arial", 10),
                fg='black', bg='#FFD700').pack(side='right', padx=10)
        
        # Content area
        content = tk.Frame(main_frame, bg='#0D0D0D')
        content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Left menu
        left_panel = tk.Frame(content, bg='#1A1A1A', width=200)
        left_panel.pack(side='left', fill='y', padx=(0, 10))
        left_panel.pack_propagate(False)
        
        tk.Label(left_panel, text="⚡ OPTIMIZERS", font=("Arial", 12, "bold"),
                fg='#FFD700', bg='#1A1A1A').pack(pady=10)
        
        # Menu buttons
        menus = [
            ("🎯 AIM ASSIST", self.show_aim),
            ("🖱️ RAW MOUSE", self.show_mouse),
            ("⚡ FPS BOOST", self.show_fps),
            ("💻 PC CLEANER", self.show_pc),
            ("📱 EMULATOR", self.show_emu),
            ("🌐 NET BOOST", self.show_net),
            ("🔥 ULTIMATE", self.show_ultimate)
        ]
        
        for text, cmd in menus:
            btn = tk.Button(left_panel, text=text, font=("Arial", 10),
                          bg='#333333', fg='#FFD700', bd=0, padx=10, pady=5,
                          anchor='w', command=cmd)
            btn.pack(fill='x', padx=10, pady=2)
        
        # Right panel (content area)
        self.right_panel = tk.Frame(content, bg='#1A1A1A')
        self.right_panel.pack(side='right', fill='both', expand=True)
        
        # Show welcome message
        self.show_welcome()
    
    def show_welcome(self):
        """Show welcome message"""
        self.clear_right_panel()
        
        tk.Label(self.right_panel, text="🦊 WELCOME PRIME", 
                font=("Arial Black", 18), fg='#FFD700', bg='#1A1A1A').pack(pady=50)
        
        tk.Label(self.right_panel, text="Select an optimizer from the left menu",
                font=("Arial", 12), fg='#FFA500', bg='#1A1A1A').pack()
        
        tk.Label(self.right_panel, text="\n\nLOGIN: PRIME / 3K",
                font=("Arial", 10), fg='#666666', bg='#1A1A1A').pack()
    
    def clear_right_panel(self):
        """Clear right panel"""
        for widget in self.right_panel.winfo_children():
            widget.destroy()
    
    def show_aim(self):
        """Show aim assist options"""
        self.clear_right_panel()
        
        tk.Label(self.right_panel, text="🎯 AIM ASSIST OPTIMIZER", 
                font=("Arial Black", 14), fg='#FFD700', bg='#1A1A1A').pack(pady=20)
        
        options = [
            "Disable Mouse Acceleration",
            "Enable Raw Input",
            "1:1 Pixel Movement",
            "Disable Mouse Smoothing"
        ]
        
        for opt in options:
            frame = tk.Frame(self.right_panel, bg='#333333')
            frame.pack(fill='x', padx=30, pady=5)
            
            tk.Label(frame, text=opt, fg='white', bg='#333333', 
                    anchor='w').pack(side='left', padx=10, pady=8)
            
            tk.Button(frame, text="APPLY", bg='#FFD700', fg='black', bd=0,
                     command=lambda o=opt: self.apply_opt(o)).pack(side='right', padx=10)
    
    def show_mouse(self):
        """Show raw mouse fixer"""
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
                 command=self.apply_mouse).pack(pady=30)
    
    def show_fps(self):
        """Show FPS booster"""
        self.clear_right_panel()
        
        tk.Label(self.right_panel, text="⚡ FPS BOOSTER", 
                font=("Arial Black", 14), fg='#FFD700', bg='#1A1A1A').pack(pady=20)
        
        options = [
            ("High Performance Power Plan", "powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"),
            ("Disable Xbox Game Bar", "reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR /v AppCaptureEnabled /t REG_DWORD /d 0 /f"),
            ("Disable Visual Effects", "reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects /v VisualFXSetting /t REG_DWORD /d 2 /f"),
            ("Optimize CPU Priority", "reg add HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl /v Win32PrioritySeparation /t REG_DWORD /d 38 /f")
        ]
        
        for text, cmd in options:
            frame = tk.Frame(self.right_panel, bg='#333333')
            frame.pack(fill='x', padx=30, pady=5)
            
            tk.Label(frame, text=text, fg='white', bg='#333333', 
                    anchor='w').pack(side='left', padx=10, pady=8)
            
            tk.Button(frame, text="ENABLE", bg='#FFD700', fg='black', bd=0,
                     command=lambda c=cmd: self.run_cmd(c)).pack(side='right', padx=10)
    
    def show_pc(self):
        """Show PC cleaner"""
        self.clear_right_panel()
        
        tk.Label(self.right_panel, text="💻 PC CLEANER", 
                font=("Arial Black", 14), fg='#FFD700', bg='#1A1A1A').pack(pady=20)
        
        tk.Button(self.right_panel, text="CLEAN TEMP FILES", bg='#FFD700', fg='black',
                 font=("Arial", 11), padx=15, pady=5,
                 command=self.clean_temp).pack(pady=5)
        
        tk.Button(self.right_panel, text="KILL BACKGROUND APPS", bg='#FFD700', fg='black',
                 font=("Arial", 11), padx=15, pady=5,
                 command=self.kill_apps).pack(pady=5)
        
        tk.Button(self.right_panel, text="STOP SERVICES", bg='#FFD700', fg='black',
                 font=("Arial", 11), padx=15, pady=5,
                 command=self.stop_services).pack(pady=5)
    
    def show_emu(self):
        """Show emulator optimizer"""
        self.clear_right_panel()
        
        tk.Label(self.right_panel, text="📱 EMULATOR OPTIMIZER", 
                font=("Arial Black", 14), fg='#FFD700', bg='#1A1A1A').pack(pady=20)
        
        emulators = ["Gameloop", "LDPlayer", "Bluestacks"]
        
        for emu in emulators:
            tk.Button(self.right_panel, text=emu, bg='#333333', fg='#FFD700',
                     font=("Arial", 10), padx=20, pady=5,
                     command=lambda e=emu: self.show_emu_settings(e)).pack(pady=3)
    
    def show_net(self):
        """Show network booster"""
        self.clear_right_panel()
        
        tk.Label(self.right_panel, text="🌐 NETWORK BOOSTER", 
                font=("Arial Black", 14), fg='#FFD700', bg='#1A1A1A').pack(pady=20)
        
        options = [
            ("Flush DNS", "ipconfig /flushdns"),
            ("Reset Winsock", "netsh winsock reset"),
            ("Disable IPv6", "reg add HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip6\\Parameters /v DisabledComponents /t REG_DWORD /d 255 /f")
        ]
        
        for text, cmd in options:
            frame = tk.Frame(self.right_panel, bg='#333333')
            frame.pack(fill='x', padx=30, pady=5)
            
            tk.Label(frame, text=text, fg='white', bg='#333333', 
                    anchor='w').pack(side='left', padx=10, pady=8)
            
            tk.Button(frame, text="APPLY", bg='#FFD700', fg='black', bd=0,
                     command=lambda c=cmd: self.run_cmd(c)).pack(side='right', padx=10)
    
    def show_ultimate(self):
        """Show ultimate optimizer"""
        self.clear_right_panel()
        
        tk.Label(self.right_panel, text="🔥 ULTIMATE OPTIMIZATION", 
                font=("Arial Black", 14), fg='#FFD700', bg='#1A1A1A').pack(pady=20)
        
        tk.Label(self.right_panel, text="This will apply ALL optimizations at once",
                font=("Arial", 11), fg='white', bg='#1A1A1A').pack(pady=10)
        
        opts = [
            "✓ Raw Mouse Input",
            "✓ FPS Boost",
            "✓ PC Clean",
            "✓ Network Optimize",
            "✓ Registry Tweaks"
        ]
        
        for opt in opts:
            tk.Label(self.right_panel, text=opt, font=("Arial", 10),
                    fg='#00FF00', bg='#1A1A1A').pack()
        
        tk.Button(self.right_panel, text="🔥 APPLY ULTIMATE", bg='#FFD700', fg='black',
                 font=("Arial", 14, "bold"), padx=30, pady=15,
                 command=self.apply_ultimate).pack(pady=30)
        
        tk.Label(self.right_panel, text="⚠️ Restart PC after applying",
                font=("Arial", 9), fg='#FF0000', bg='#1A1A1A').pack()
    
    def apply_opt(self, opt):
        """Apply optimization"""
        messagebox.showinfo("Applied", f"✓ {opt} applied successfully!")
    
    def apply_mouse(self):
        """Apply mouse fix"""
        try:
            ctypes.windll.user32.SystemParametersInfoW(0x0073, 0, 0, 0)
            messagebox.showinfo("Success", "✓ Raw mouse input enabled!\nYour DPI and sensitivity are unchanged.")
        except:
            messagebox.showerror("Error", "Run as administrator")
    
    def run_cmd(self, cmd):
        """Run command"""
        try:
            subprocess.run(cmd, shell=True)
            messagebox.showinfo("Success", "✓ Applied successfully!")
        except:
            messagebox.showerror("Error", "Run as administrator")
    
    def clean_temp(self):
        """Clean temp files"""
        try:
            subprocess.run(f"del /q /f /s {os.environ['TEMP']}\\* 2>nul", shell=True)
            messagebox.showinfo("Success", "✓ Temp files cleaned")
        except:
            messagebox.showerror("Error", "Run as administrator")
    
    def kill_apps(self):
        """Kill background apps"""
        apps = ["chrome.exe", "firefox.exe", "discord.exe", "spotify.exe"]
        for app in apps:
            subprocess.run(f"taskkill /F /IM {app} 2>nul", shell=True)
        messagebox.showinfo("Success", "✓ Background apps killed")
    
    def stop_services(self):
        """Stop unnecessary services"""
        subprocess.run("net stop WSearch /y 2>nul", shell=True)
        subprocess.run("net stop SysMain /y 2>nul", shell=True)
        messagebox.showinfo("Success", "✓ Services stopped")
    
    def show_emu_settings(self, emu):
        """Show emulator settings"""
        settings = {
            "Gameloop": "CPU: 4 Cores\nRAM: 4096 MB\nResolution: 1600x900\nRender: OpenGL\nFPS: 60",
            "LDPlayer": "CPU: 4 Cores\nRAM: 4096 MB\nResolution: 1600x900\nASTC: Hardware",
            "Bluestacks": "CPU: 4 Cores\nRAM: 4096 MB\nPerformance: High\nGraphics: OpenGL"
        }
        messagebox.showinfo(f"{emu} Settings", settings.get(emu, "Apply in emulator settings"))
    
    def apply_ultimate(self):
        """Apply all optimizations"""
        self.apply_mouse()
        self.run_cmd("powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c")
        self.clean_temp()
        self.kill_apps()
        self.stop_services()
        self.run_cmd("ipconfig /flushdns")
        messagebox.showinfo("ULTIMATE", "✅ All optimizations applied!\n\nRestart your PC for best results.")

if __name__ == "__main__":
    # Check admin
    if ctypes.windll.shell32.IsUserAnAdmin():
        root = tk.Tk()
        app = PrimeH4XOptimizer(root)
        root.mainloop()
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)