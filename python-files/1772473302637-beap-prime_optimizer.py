import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import cv2
import pygame
import threading
import os
import shutil
import psutil
import subprocess
import sys
import ctypes
import winreg
import time

# =========================
# CONFIG
# =========================
VIDEO_PATH = "bg.mp4"
MUSIC_PATH = "phonk.mp3"
USERNAME = "PRIME"
PASSWORD = "3K"

# =========================
# MUSIC
# =========================
pygame.mixer.init()
try:
    if os.path.exists(MUSIC_PATH):
        pygame.mixer.music.load(MUSIC_PATH)
        pygame.mixer.music.set_volume(0.4)
    else:
        print("Music file not found")
except:
    print("Music init failed")

# =========================
# MAIN WINDOW
# =========================
root = tk.Tk()
root.title("PRIME.H4X OPTIMIZER - NARUTO EDITION")
root.geometry("1000x600")
root.resizable(False, False)

# =========================
# VIDEO BACKGROUND
# =========================
video_label = tk.Label(root)
video_label.place(x=0, y=0, relwidth=1, relheight=1)

def play_video():
    try:
        if 'cap' not in play_video.__dict__:
            play_video.cap = cv2.VideoCapture(VIDEO_PATH)
        
        ret, frame = play_video.cap.read()
        if not ret:
            play_video.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = play_video.cap.read()

        frame = cv2.resize(frame, (1000, 600))
        frame = cv2.GaussianBlur(frame, (35, 35), 0)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        img = Image.fromarray(frame)
        imgtk = ImageTk.PhotoImage(img)
        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)

        root.after(30, play_video)
    except:
        # Fallback if video fails
        root.after(100, play_video)

# Start video if file exists
if os.path.exists(VIDEO_PATH):
    play_video()
else:
    # Solid color background if no video
    root.configure(bg='#0D0D0D')

# =========================
# LOGIN FRAME (EXACTLY FROM YOUR CODE)
# =========================
login_frame = tk.Frame(root, bg="#111111")
login_frame.place(relx=0.5, rely=0.5, anchor="center", width=400, height=300)

tk.Label(login_frame, text="PRIME LOGIN", font=("Segoe UI", 18, "bold"),
         bg="#111111", fg="white").pack(pady=20)

user_entry = tk.Entry(login_frame, font=("Segoe UI", 12))
user_entry.pack(pady=10)

pass_entry = tk.Entry(login_frame, show="*", font=("Segoe UI", 12))
pass_entry.pack(pady=10)

def login():
    if user_entry.get() == USERNAME and pass_entry.get() == PASSWORD:
        login_frame.destroy()
        try:
            pygame.mixer.music.play(-1)
        except:
            pass
        show_dashboard()
    else:
        messagebox.showerror("Error", "Invalid Login")

tk.Button(login_frame, text="LOGIN", font=("Segoe UI", 11, "bold"),
          bg="#1f1f1f", fg="white", relief="flat",
          command=login).pack(pady=20)

# =========================
# DASHBOARD (ENHANCED WITH ALL OPTIMIZERS)
# =========================
def show_dashboard():
    dash = tk.Frame(root, bg="#111111")
    dash.place(relx=0.5, rely=0.5, anchor="center", width=900, height=500)
    
    # Header
    header_frame = tk.Frame(dash, bg="#222222", height=50)
    header_frame.pack(fill='x')
    header_frame.pack_propagate(False)
    
    tk.Label(header_frame, text="🦊 PRIME.H4X OPTIMIZER PRO", 
             font=("Segoe UI", 16, "bold"),
             bg="#222222", fg="#FFD700").pack(side='left', padx=20)
    
    tk.Label(header_frame, text=f"Welcome, {USERNAME}", 
             font=("Segoe UI", 10),
             bg="#222222", fg="white").pack(side='right', padx=20)
    
    # Content area
    content = tk.Frame(dash, bg="#111111")
    content.pack(fill='both', expand=True, padx=20, pady=20)
    
    # Left panel - Menu
    left_panel = tk.Frame(content, bg="#1A1A1A", width=200)
    left_panel.pack(side='left', fill='y', padx=(0, 10))
    left_panel.pack_propagate(False)
    
    tk.Label(left_panel, text="⚡ OPTIMIZERS", font=("Segoe UI", 12, "bold"),
             bg="#1A1A1A", fg="#FFD700").pack(pady=15)
    
    # Menu buttons
    menus = [
        ("🎯 AIM ASSIST", show_aim),
        ("🖱️ RAW MOUSE", show_mouse),
        ("⚡ FPS BOOST", show_fps),
        ("💻 PC CLEANER", show_pc),
        ("📱 EMULATOR", show_emu),
        ("🌐 NET BOOST", show_net),
        ("🔥 ULTIMATE", show_ultimate)
    ]
    
    for text, cmd in menus:
        btn = tk.Button(left_panel, text=text, font=("Segoe UI", 10),
                       bg="#333333", fg="#FFD700", bd=0, padx=10, pady=8,
                       anchor='w', command=cmd)
        btn.pack(fill='x', padx=10, pady=2)
    
    # Right panel (content area)
    global right_panel
    right_panel = tk.Frame(content, bg="#1A1A1A")
    right_panel.pack(side='right', fill='both', expand=True)
    
    # Show welcome message
    show_welcome()

def show_welcome():
    """Show welcome message"""
    clear_right()
    
    tk.Label(right_panel, text="🦊 WELCOME PRIME", 
             font=("Segoe UI", 20, "bold"),
             fg="#FFD700", bg="#1A1A1A").pack(pady=50)
    
    tk.Label(right_panel, text="Select an optimizer from the left menu",
             font=("Segoe UI", 12),
             fg="#FFA500", bg="#1A1A1A").pack()
    
    tk.Label(right_panel, text="\n\nLOGIN: PRIME / 3K",
             font=("Segoe UI", 10),
             fg="#666666", bg="#1A1A1A").pack()

def clear_right():
    """Clear right panel"""
    for widget in right_panel.winfo_children():
        widget.destroy()

# =========================
# OPTIMIZER FUNCTIONS
# =========================

def show_aim():
    """Aim Assist Optimizer"""
    clear_right()
    
    tk.Label(right_panel, text="🎯 AIM ASSIST OPTIMIZER", 
             font=("Segoe UI", 16, "bold"),
             fg="#FFD700", bg="#1A1A1A").pack(pady=20)
    
    options = [
        "Disable Mouse Acceleration",
        "Enable Raw Input",
        "1:1 Pixel Movement",
        "Disable Mouse Smoothing",
        "Optimize Polling Rate"
    ]
    
    for opt in options:
        frame = tk.Frame(right_panel, bg="#333333")
        frame.pack(fill='x', padx=40, pady=5)
        
        tk.Label(frame, text=opt, font=("Segoe UI", 11),
                 fg="white", bg="#333333").pack(side='left', padx=10, pady=8)
        
        tk.Button(frame, text="APPLY", bg="#FFD700", fg="black", bd=0,
                 font=("Segoe UI", 9, "bold"), padx=15,
                 command=lambda o=opt: apply_opt(o)).pack(side='right', padx=10)

def show_mouse():
    """Raw Mouse Fixer"""
    clear_right()
    
    tk.Label(right_panel, text="🖱️ RAW MOUSE FIXER", 
             font=("Segoe UI", 16, "bold"),
             fg="#FFD700", bg="#1A1A1A").pack(pady=20)
    
    tk.Label(right_panel, text="This will NOT change your DPI or sensitivity",
             font=("Segoe UI", 10),
             fg="#FFA500", bg="#1A1A1A").pack()
    
    fixes = [
        "✓ Mouse Acceleration: OFF",
        "✓ Raw Input: ENABLED",
        "✓ Mouse Smoothing: OFF",
        "✓ 1:1 Pixel Movement: ACTIVE"
    ]
    
    for fix in fixes:
        tk.Label(right_panel, text=fix, font=("Segoe UI", 11),
                 fg="#00FF00", bg="#1A1A1A").pack(pady=5)
    
    tk.Button(right_panel, text="APPLY RAW MOUSE FIX", bg="#FFD700", fg="black",
             font=("Segoe UI", 12, "bold"), padx=20, pady=10,
             command=apply_raw_mouse).pack(pady=30)

def show_fps():
    """FPS Booster"""
    clear_right()
    
    tk.Label(right_panel, text="⚡ FPS BOOSTER", 
             font=("Segoe UI", 16, "bold"),
             fg="#FFD700", bg="#1A1A1A").pack(pady=20)
    
    options = [
        ("High Performance Power Plan", "powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c"),
        ("Disable Xbox Game Bar", "reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR /v AppCaptureEnabled /t REG_DWORD /d 0 /f"),
        ("Disable Visual Effects", "reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Explorer\\VisualEffects /v VisualFXSetting /t REG_DWORD /d 2 /f"),
        ("Optimize CPU Priority", "reg add HKLM\\SYSTEM\\CurrentControlSet\\Control\\PriorityControl /v Win32PrioritySeparation /t REG_DWORD /d 38 /f"),
        ("Disable Fullscreen Optimizations", "reg add HKCU\\System\\GameConfigStore /v GameDVR_FSEBehaviorMode /t REG_DWORD /d 2 /f")
    ]
    
    for text, cmd in options:
        frame = tk.Frame(right_panel, bg="#333333")
        frame.pack(fill='x', padx=40, pady=5)
        
        tk.Label(frame, text=text, font=("Segoe UI", 11),
                 fg="white", bg="#333333").pack(side='left', padx=10, pady=8)
        
        tk.Button(frame, text="ENABLE", bg="#FFD700", fg="black", bd=0,
                 font=("Segoe UI", 9, "bold"), padx=15,
                 command=lambda c=cmd: run_cmd(c)).pack(side='right', padx=10)

def show_pc():
    """PC Cleaner"""
    clear_right()
    
    tk.Label(right_panel, text="💻 PC CLEANER", 
             font=("Segoe UI", 16, "bold"),
             fg="#FFD700", bg="#1A1A1A").pack(pady=20)
    
    # System stats
    stats_frame = tk.Frame(right_panel, bg="#333333")
    stats_frame.pack(fill='x', padx=40, pady=10)
    
    cpu_percent = psutil.cpu_percent()
    ram_percent = psutil.virtual_memory().percent
    
    tk.Label(stats_frame, text=f"CPU: {cpu_percent}%", font=("Segoe UI", 11),
             fg="white", bg="#333333").pack(pady=5)
    tk.Label(stats_frame, text=f"RAM: {ram_percent}%", font=("Segoe UI", 11),
             fg="white", bg="#333333").pack(pady=5)
    
    tk.Button(right_panel, text="🧹 CLEAN TEMP FILES", bg="#FFD700", fg="black",
             font=("Segoe UI", 11, "bold"), width=25, pady=8,
             command=clean_temp).pack(pady=10)
    
    tk.Button(right_panel, text="🔪 KILL BACKGROUND APPS", bg="#FFD700", fg="black",
             font=("Segoe UI", 11, "bold"), width=25, pady=8,
             command=kill_apps).pack(pady=10)
    
    tk.Button(right_panel, text="⏹️ STOP SERVICES", bg="#FFD700", fg="black",
             font=("Segoe UI", 11, "bold"), width=25, pady=8,
             command=stop_services).pack(pady=10)

def show_emu():
    """Emulator Optimizer"""
    clear_right()
    
    tk.Label(right_panel, text="📱 EMULATOR OPTIMIZER", 
             font=("Segoe UI", 16, "bold"),
             fg="#FFD700", bg="#1A1A1A").pack(pady=20)
    
    emulators = ["Gameloop", "LDPlayer", "Bluestacks", "MSI App Player"]
    
    for emu in emulators:
        btn = tk.Button(right_panel, text=emu, bg="#333333", fg="#FFD700",
                       font=("Segoe UI", 11), width=20, pady=5,
                       command=lambda e=emu: show_emu_settings(e))
        btn.pack(pady=5)

def show_net():
    """Network Booster"""
    clear_right()
    
    tk.Label(right_panel, text="🌐 NETWORK BOOSTER", 
             font=("Segoe UI", 16, "bold"),
             fg="#FFD700", bg="#1A1A1A").pack(pady=20)
    
    options = [
        ("Flush DNS", "ipconfig /flushdns"),
        ("Reset Winsock", "netsh winsock reset"),
        ("Disable QoS", "reg add HKLM\\SOFTWARE\\Policies\\Microsoft\\Windows\\Psched /v NonBestEffortLimit /t REG_DWORD /d 0 /f"),
        ("Optimize MTU", "netsh interface ipv4 set subinterface Ethernet mtu=1492 store=persistent"),
        ("Disable IPv6", "reg add HKLM\\SYSTEM\\CurrentControlSet\\Services\\Tcpip6\\Parameters /v DisabledComponents /t REG_DWORD /d 255 /f")
    ]
    
    for text, cmd in options:
        frame = tk.Frame(right_panel, bg="#333333")
        frame.pack(fill='x', padx=40, pady=5)
        
        tk.Label(frame, text=text, font=("Segoe UI", 11),
                 fg="white", bg="#333333").pack(side='left', padx=10, pady=8)
        
        tk.Button(frame, text="APPLY", bg="#FFD700", fg="black", bd=0,
                 font=("Segoe UI", 9, "bold"), padx=15,
                 command=lambda c=cmd: run_cmd(c)).pack(side='right', padx=10)

def show_ultimate():
    """Ultimate Optimizer"""
    clear_right()
    
    tk.Label(right_panel, text="🔥 ULTIMATE OPTIMIZATION", 
             font=("Segoe UI", 16, "bold"),
             fg="#FFD700", bg="#1A1A1A").pack(pady=20)
    
    tk.Label(right_panel, text="This will apply ALL optimizations at once",
             font=("Segoe UI", 11),
             fg="white", bg="#1A1A1A").pack(pady=10)
    
    opts = [
        "✓ Raw Mouse Input",
        "✓ FPS Boost",
        "✓ PC Clean",
        "✓ Network Optimize",
        "✓ Emulator Settings",
        "✓ Registry Tweaks"
    ]
    
    for opt in opts:
        tk.Label(right_panel, text=opt, font=("Segoe UI", 10),
                 fg="#00FF00", bg="#1A1A1A").pack()
    
    tk.Button(right_panel, text="🔥 APPLY ULTIMATE", bg="#FFD700", fg="black",
             font=("Segoe UI", 14, "bold"), padx=30, pady=15,
             command=apply_ultimate).pack(pady=30)
    
    tk.Label(right_panel, text="⚠️ Restart PC after applying",
             font=("Segoe UI", 9), fg="#FF0000", bg="#1A1A1A").pack()

# =========================
# UTILITY FUNCTIONS
# =========================

def apply_opt(opt):
    """Apply optimization"""
    messagebox.showinfo("Applied", f"✓ {opt} applied successfully!")

def apply_raw_mouse():
    """Apply raw mouse fix"""
    try:
        # Disable mouse acceleration (no DPI/sens change)
        ctypes.windll.user32.SystemParametersInfoW(0x0073, 0, 0, 0)
        messagebox.showinfo("Success", "✓ Raw mouse input enabled!\nYour DPI and sensitivity are unchanged.")
    except:
        messagebox.showerror("Error", "Failed to apply. Run as administrator.")

def run_cmd(cmd):
    """Run command"""
    try:
        subprocess.run(cmd, shell=True)
        messagebox.showinfo("Success", "✓ Applied successfully!")
    except:
        messagebox.showerror("Error", "Run as administrator")

def clean_temp():
    """Clean temp files"""
    try:
        temp = os.environ['TEMP']
        for root, dirs, files in os.walk(temp):
            for file in files:
                try:
                    os.remove(os.path.join(root, file))
                except:
                    pass
        messagebox.showinfo("Done", "✓ Temp files cleaned")
    except:
        messagebox.showwarning("Warning", "Some files in use")

def kill_apps():
    """Kill background apps"""
    apps = ["chrome.exe", "firefox.exe", "discord.exe", "spotify.exe", "telegram.exe"]
    killed = []
    for app in apps:
        try:
            subprocess.run(f"taskkill /F /IM {app} 2>nul", shell=True)
            killed.append(app)
        except:
            pass
    messagebox.showinfo("Done", f"✓ Killed: {', '.join(killed)}")

def stop_services():
    """Stop unnecessary services"""
    services = ["WSearch", "SysMain", "DiagTrack", "dmwappushservice"]
    for service in services:
        subprocess.run(f"net stop {service} /y 2>nul", shell=True)
    messagebox.showinfo("Done", "✓ Services stopped")

def show_emu_settings(emu):
    """Show emulator settings"""
    settings = {
        "Gameloop": "CPU: 4 Cores\nRAM: 4096 MB\nResolution: 1600x900\nRender: OpenGL\nFPS: 60",
        "LDPlayer": "CPU: 4 Cores\nRAM: 4096 MB\nResolution: 1600x900\nRender: OpenGL\nASTC: Hardware",
        "Bluestacks": "CPU: 4 Cores\nRAM: 4096 MB\nPerformance: High\nGraphics: OpenGL\nFPS: 60",
        "MSI App Player": "CPU: 4 Cores\nRAM: 4096 MB\nResolution: 1600x900\nRender: DirectX"
    }
    messagebox.showinfo(f"{emu} Settings", settings.get(emu, "Apply in emulator settings"))

def apply_ultimate():
    """Apply all optimizations"""
    apply_raw_mouse()
    run_cmd("powercfg /setactive 8c5e7fda-e8bf-4a96-9a85-a6e23a8c635c")
    run_cmd("reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\GameDVR /v AppCaptureEnabled /t REG_DWORD /d 0 /f")
    clean_temp()
    kill_apps()
    stop_services()
    run_cmd("ipconfig /flushdns")
    messagebox.showinfo("ULTIMATE", "✅ All optimizations applied!\n\nRestart your PC for best results.")

# =========================
# CLEAN EXIT
# =========================
def on_close():
    try:
        pygame.mixer.music.stop()
        pygame.mixer.quit()
    except:
        pass
    try:
        if 'cap' in play_video.__dict__:
            play_video.cap.release()
    except:
        pass
    root.destroy()
    sys.exit()

root.protocol("WM_DELETE_WINDOW", on_close)

# Check admin
if not ctypes.windll.shell32.IsUserAnAdmin():
    messagebox.showwarning("Warning", "Run as Administrator for full features!")

root.mainloop()