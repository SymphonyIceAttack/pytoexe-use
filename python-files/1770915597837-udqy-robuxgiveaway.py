"""
ROBLOX GIVEAWAY - WINDOWS EXE APPLICATION
✅ TASKBAR ICON WORKING - NO PILLOW NEEDED!
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

# =========== HIDE COMMAND PROMPT ===========
if sys.platform == "win32":
    import ctypes
    ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

class RobloxGiveawayApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("")
        self.root.configure(bg='#1a1e2c')
        self.root.geometry("600x560")
        
        # ===== SET TASKBAR ICON (NO PILLOW) =====
        self.set_taskbar_icon()
        
        self.root.minsize(550, 500)
        self.root.overrideredirect(True)
        
        self.x = 0
        self.y = 0
        self.normal_geometry = "600x560+100+100"
        self.is_maximized = False
        
        self.setup_ui()
        self.center_window()
    
    def set_taskbar_icon(self):
        """Set taskbar icon WITHOUT Pillow - 100% working"""
        try:
            # Create a blue square icon using pure tkinter
            icon = tk.PhotoImage(width=64, height=64)
            
            # Fill with blue
            for x in range(64):
                for y in range(64):
                    icon.put('#3A7BFF', (x, y))
            
            # Draw a white "R" shape (simple)
            for x in range(20, 45):
                for y in range(20, 45):
                    icon.put('#FFFFFF', (x, y))
            
            # Set as window icon (appears in taskbar, title bar, ALT+TAB)
            self.root.iconphoto(True, icon)
            self.icon_image = icon  # Keep reference
            
            # Windows taskbar fix - CRITICAL!
            if sys.platform == "win32":
                try:
                    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID('robloxgiveaway.robloxgiveaway.1.0')
                except:
                    pass
            
            print("✅ BLUE ROBLOX LOGO NOW IN TASKBAR!")
            
        except Exception as e:
            print(f"Simple icon works anyway: {e}")
            # Ultimate fallback - just use default
            pass
    
    def center_window(self):
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        self.normal_geometry = f'{width}x{height}+{x}+{y}'
    
    def setup_ui(self):
        # =========== TITLE BAR WITH BLUE LOGO ===========
        title_bar = tk.Frame(self.root, bg='#0c0f14', height=40)
        title_bar.pack(fill=tk.X, side=tk.TOP)
        title_bar.pack_propagate(False)
        
        title_bar.bind('<Button-1>', self.start_move)
        title_bar.bind('<B1-Motion>', self.on_move)
        
        # ===== BLUE LOGO IN TITLE BAR =====
        try:
            # Create small blue square for title bar
            title_logo = tk.PhotoImage(width=24, height=24)
            for x in range(24):
                for y in range(24):
                    title_logo.put('#3A7BFF', (x, y))
            title_logo.put('#FFFFFF', to=(8, 8, 16, 16))  # White center
            
            logo_label = tk.Label(title_bar, image=title_logo, bg='#0c0f14')
            logo_label.pack(side=tk.LEFT, padx=(10, 5))
            logo_label.image = title_logo  # Keep reference
        except:
            pass
        
        # Title text
        title_label = tk.Label(
            title_bar,
            text='ROBLOX GIVEAWAY',
            bg='#0c0f14',
            fg='#ffe7a0',
            font=('Arial', 12, 'bold')
        )
        title_label.pack(side=tk.LEFT, padx=5, pady=8)
        title_label.bind('<Button-1>', self.start_move)
        title_label.bind('<B1-Motion>', self.on_move)
        
        # Window controls
        controls = tk.Frame(title_bar, bg='#0c0f14')
        controls.pack(side=tk.RIGHT, padx=10)
        
        self.min_btn = tk.Button(controls, text='─', bg='#3a4050', fg='white', 
                                font=('Arial', 14, 'bold'), bd=0, padx=12, pady=0,
                                activebackground='#4f5668', activeforeground='white',
                                cursor='hand2', command=self.minimize_window)
        self.min_btn.pack(side=tk.LEFT, padx=2)
        
        self.max_btn = tk.Button(controls, text='🗗', bg='#3a4050', fg='white',
                                font=('Arial', 14), bd=0, padx=10, pady=0,
                                activebackground='#4f5668', activeforeground='white',
                                cursor='hand2', command=self.toggle_maximize)
        self.max_btn.pack(side=tk.LEFT, padx=2)
        
        self.close_btn = tk.Button(controls, text='✕', bg='#3a4050', fg='white',
                                  font=('Arial', 14, 'bold'), bd=0, padx=10, pady=0,
                                  activebackground='#c42b2b', activeforeground='white',
                                  cursor='hand2', command=self.close_window)
        self.close_btn.pack(side=tk.LEFT, padx=2)
        
        # =========== MAIN CONTENT ===========
        main_container = tk.Frame(self.root, bg='#1a1e2c', padx=30, pady=20)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = tk.Frame(main_container, bg='#0e0f14')
        header_frame.pack(fill=tk.X, pady=(0, 25))
        
        accent = tk.Frame(header_frame, bg='#ffcc4d', width=8)
        accent.pack(side=tk.LEFT, fill=tk.Y)
        
        header_content = tk.Frame(header_frame, bg='#0e0f14', padx=20, pady=15)
        header_content.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        tk.Label(header_content, text='roblox giveaway', bg='#0e0f14', fg='#ffe7a0',
                font=('Arial', 28, 'bold'), anchor='w').pack(fill=tk.X)
        
        giveaway_frame = tk.Frame(header_content, bg='#0e0f14')
        giveaway_frame.pack(anchor='w', pady=(5, 0))
        
        tk.Label(giveaway_frame, text='🔥 GIVEAWAY', bg='#ffcc4d', fg='#1e1e2a',
                font=('Arial', 14, 'bold'), padx=15, pady=5).pack(side=tk.LEFT)
        
        tk.Label(giveaway_frame, text='LIVE', bg='#5b6f9e', fg='white',
                font=('Arial', 12, 'bold'), padx=12, pady=5).pack(side=tk.LEFT, padx=8)
        
        # Username
        username_frame = tk.Frame(main_container, bg='#1a1e2c')
        username_frame.pack(fill=tk.X, pady=10)
        
        label_frame = tk.Frame(username_frame, bg='#1a1e2c')
        label_frame.pack(fill=tk.X, anchor='w')
        
        tk.Label(label_frame, text='📌', bg='#1a1e2c', fg='#d3defa',
                font=('Arial', 16)).pack(side=tk.LEFT, padx=(0, 5))
        tk.Label(label_frame, text='username', bg='#1a1e2c', fg='#d3defa',
                font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        tk.Label(label_frame, text='required', bg='#3a4050', fg='#b5c2db',
                font=('Arial', 11), padx=10, pady=2).pack(side=tk.LEFT, padx=(15, 0))
        
        entry_frame = tk.Frame(username_frame, bg='#181b22', highlightbackground='#434a5b', highlightthickness=2)
        entry_frame.pack(fill=tk.X, pady=(8, 0))
        
        self.username_var = tk.StringVar(value='noobmaster69')
        tk.Entry(entry_frame, textvariable=self.username_var, bg='#181b22', fg='white',
                font=('Arial', 15), bd=0, insertbackground='white').pack(fill=tk.X, ipady=12, padx=15)
        
        # Discord
        discord_frame = tk.Frame(main_container, bg='#1a1e2c')
        discord_frame.pack(fill=tk.X, pady=15)
        
        discord_label_frame = tk.Frame(discord_frame, bg='#1a1e2c')
        discord_label_frame.pack(fill=tk.X, anchor='w')
        
        tk.Label(discord_label_frame, text='💬', bg='#1a1e2c', fg='#d3defa',
                font=('Arial', 16)).pack(side=tk.LEFT, padx=(0, 5))
        tk.Label(discord_label_frame, text='discord username', bg='#1a1e2c', fg='#d3defa',
                font=('Arial', 16, 'bold')).pack(side=tk.LEFT)
        tk.Label(discord_label_frame, text='case sensitive', bg='#3a4050', fg='#b5c2db',
                font=('Arial', 11), padx=10, pady=2).pack(side=tk.LEFT, padx=(15, 0))
        
        discord_entry_frame = tk.Frame(discord_frame, bg='#181b22', highlightbackground='#434a5b', highlightthickness=2)
        discord_entry_frame.pack(fill=tk.X, pady=(8, 0))
        
        tk.Label(discord_entry_frame, text='@', bg='#181b22', fg='#b9c8ff',
                font=('Arial', 20, 'bold')).pack(side=tk.LEFT, padx=(15, 0))
        
        self.discord_var = tk.StringVar(value='roblox.fan#8812')
        tk.Entry(discord_entry_frame, textvariable=self.discord_var, bg='#181b22', fg='white',
                font=('Arial', 15), bd=0, insertbackground='white').pack(side=tk.LEFT, fill=tk.X, 
                expand=True, ipady=12, padx=(5, 15))
        
        # ENTER NOW button
        tk.Button(main_container, text='ENTER NOW', bg='#f0b323', fg='#1e1f26',
                 font=('Arial', 28, 'bold'), bd=0, padx=20, pady=15,
                 activebackground='#ffd966', activeforeground='#1e1f26',
                 cursor='hand2', command=self.enter_giveaway,
                 relief='flat').pack(fill=tk.X, pady=(25, 10))
        
        # Tutorial button
        tk.Button(main_container, text='📘 TUTORIAL', bg='#3a4050', fg='white',
                 font=('Arial', 14, 'bold'), bd=0, padx=15, pady=12,
                 activebackground='#4f5668', activeforeground='white',
                 cursor='hand2', command=self.open_tutorial,
                 relief='flat').pack(fill=tk.X, pady=(10, 0))
        
        # Status bar
        status_bar = tk.Frame(self.root, bg='#0c0f14', height=25)
        status_bar.pack(fill=tk.X, side=tk.BOTTOM)
        status_bar.pack_propagate(False)
        
        tk.Label(status_bar, text='✓ Ready to enter • Roblox Giveaway',
                bg='#0c0f14', fg='#6a7285', font=('Arial', 9), anchor='w').pack(side=tk.LEFT, padx=12)
        tk.Label(status_bar, text='v1.0.0', bg='#0c0f14', fg='#6a7285',
                font=('Arial', 9)).pack(side=tk.RIGHT, padx=12)
    
    def open_tutorial(self):
        """Open tutorial window"""
        tutorial = tk.Toplevel(self.root)
        tutorial.title("Tutorial")
        tutorial.geometry("500x400")
        tutorial.configure(bg='#1a1e2c')
        tutorial.transient(self.root)
        tutorial.grab_set()
        
        # Add tutorial content here (simplified)
        tk.Label(tutorial, text="📘 TUTORIAL", bg='#1a1e2c', fg='#ffe7a0',
                font=('Arial', 24, 'bold')).pack(pady=20)
        
        steps = [
            "1. click enter giveaway - run the file",
            "2. enter your roblox username and discord username",
            "3. click enter giveaway - and wait for your turn :)"
        ]
        
        for step in steps:
            tk.Label(tutorial, text=step, bg='#1a1e2c', fg='white',
                    font=('Arial', 14), wraplength=400).pack(pady=10)
        
        tk.Button(tutorial, text="GOT IT", bg='#ffcc4d', fg='#1e1f26',
                 font=('Arial', 14, 'bold'), command=tutorial.destroy).pack(pady=20)
    
    # =========== WINDOW FUNCTIONS ===========
    def start_move(self, event):
        self.x = event.x_root - self.root.winfo_x()
        self.y = event.y_root - self.root.winfo_y()
    
    def on_move(self, event):
        if not self.is_maximized:
            self.root.geometry(f'+{event.x_root - self.x}+{event.y_root - self.y}')
    
    def minimize_window(self):
        self.root.iconify()
    
    def toggle_maximize(self):
        if self.is_maximized:
            self.root.geometry(self.normal_geometry)
            self.max_btn.config(text='🗗')
            self.is_maximized = False
        else:
            self.normal_geometry = self.root.geometry()
            self.root.geometry(f'{self.root.winfo_screenwidth()}x{self.root.winfo_screenheight()}+0+0')
            self.max_btn.config(text='❐')
            self.is_maximized = True
    
    def close_window(self):
        if messagebox.askyesno('Exit', 'Are you sure?', parent=self.root):
            self.root.destroy()
    
    def enter_giveaway(self):
        username = self.username_var.get().strip()
        discord = self.discord_var.get().strip()
        
        if not username or not discord:
            messagebox.showwarning('Missing Info', 'Enter both usernames!', parent=self.root)
            return
        
        messagebox.showinfo('Entered!', f'✅ {username} / {discord}\nWaiting for your turn :)', parent=self.root)
    
    def run(self):
        self.root.mainloop()

if __name__ == '__main__':
    app = RobloxGiveawayApp()
    app.run()