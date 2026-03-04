import pymem
import pymem.process
import win32gui
import win32con
import tkinter as tk
from tkinter import ttk, colorchooser
import threading
import time
import keyboard
import pyautogui
import math
import ctypes
from ctypes import wintypes
import os

class BloxStrikeCheat:
    def __init__(self):
        # ===== FRESH OFFSETS =====
        self.OFFSETS = {
            'local_player': 0x130,
            'entity_list': 0x70,
            'health': 0x194,
            'x_pos': 0xE4,
            'y_pos': 0xE8,
            'z_pos': 0xEC,
            'team': 0x290,
            'view_matrix': 0x120,
            'name': 0xB0,
            'workspace': 0x178,
            'velocity': 0xF0,
        }
        
        # Connect to Roblox FIRST (no tkinter stuff yet)
        self.pm = None
        self.connected = False
        self.base_addr = 0
        self.roblox_hwnd = None
        self.running = True
        
        # Player data
        self.local_pos = (0, 0, 0)
        self.local_health = 100
        self.players = []
        
        # Connect to Roblox
        self.connect_to_roblox()
        
        # NOW create tkinter root window
        self.root = tk.Tk()
        self.root.title("BLOXSTRIKE EXTERNAL")
        self.root.geometry("500x450")
        self.root.configure(bg='#1C1C2A')
        self.root.attributes('-topmost', True)
        
        # Bind hotkeys
        self.root.bind('<F9>', self.toggle_visibility)
        self.root.bind('<Insert>', lambda e: self.root.deiconify() if not self.root.state() == 'normal' else None)
        
        # NOW create tkinter variables (after root exists)
        self.aimbot_enabled = tk.BooleanVar(value=True)
        self.aim_on_rmb = tk.BooleanVar(value=True)
        self.aim_fov = tk.IntVar(value=90)
        self.aim_smoothness = tk.IntVar(value=5)
        self.target_bone = tk.StringVar(value="head")
        self.predict_movement = tk.BooleanVar(value=True)
        
        self.esp_enabled = tk.BooleanVar(value=True)
        self.show_names = tk.BooleanVar(value=True)
        self.show_health = tk.BooleanVar(value=True)
        self.show_distance = tk.BooleanVar(value=True)
        self.box_color = "#00FF00"
        self.enemy_color = "#FF0000"
        
        self.no_recoil_enabled = tk.BooleanVar(value=True)
        self.recoil_strength = tk.IntVar(value=2)
        
        # Setup GUI
        self.setup_ui()
        
        # Start cheat threads
        if self.connected:
            self.aimbot_running = True
            self.aimbot_thread = threading.Thread(target=self.aimbot_loop)
            self.aimbot_thread.daemon = True
            self.aimbot_thread.start()
            
            self.recoil_thread = threading.Thread(target=self.no_recoil_loop)
            self.recoil_thread.daemon = True
            self.recoil_thread.start()
            
            self.esp_thread = threading.Thread(target=self.esp_loop)
            self.esp_thread.daemon = True
            self.esp_thread.start()
        
        # Update status periodically
        self.update_status()
    
    def connect_to_roblox(self):
        try:
            self.roblox_hwnd = win32gui.FindWindow(None, "Roblox")
            if not self.roblox_hwnd:
                print("❌ Roblox not found")
                return
            
            self.pm = pymem.Pymem("RobloxPlayerBeta.exe")
            self.base_addr = pymem.process.module_from_name(
                self.pm.process_handle, 
                "RobloxPlayerBeta.exe"
            ).lpBaseOfDll
            self.connected = True
            print("✅ Connected to Roblox")
        except:
            print("❌ Connection failed")
    
    def read_player_data(self):
        if not self.connected or not self.pm:
            return []
        
        players = []
        try:
            local_addr = self.pm.read_longlong(self.base_addr + self.OFFSETS['local_player'])
            if not local_addr:
                return []
            
            self.local_pos = (
                self.pm.read_float(local_addr + self.OFFSETS['x_pos']),
                self.pm.read_float(local_addr + self.OFFSETS['y_pos']),
                self.pm.read_float(local_addr + self.OFFSETS['z_pos'])
            )
            self.local_health = self.pm.read_int(local_addr + self.OFFSETS['health'])
            
            workspace = self.pm.read_longlong(self.base_addr + self.OFFSETS['workspace'])
            if not workspace:
                return []
            
            children = self.pm.read_longlong(workspace + self.OFFSETS['entity_list'])
            if not children:
                return []
            
            current = children
            for i in range(100):
                try:
                    player_addr = self.pm.read_longlong(current)
                    if player_addr and player_addr != local_addr:
                        health = self.pm.read_int(player_addr + self.OFFSETS['health'])
                        if 0 < health <= 100:
                            x = self.pm.read_float(player_addr + self.OFFSETS['x_pos'])
                            y = self.pm.read_float(player_addr + self.OFFSETS['y_pos'])
                            z = self.pm.read_float(player_addr + self.OFFSETS['z_pos'])
                            
                            team = 0
                            try:
                                team = self.pm.read_int(player_addr + self.OFFSETS['team'])
                            except:
                                pass
                            
                            name = "Player"
                            try:
                                name_ptr = self.pm.read_longlong(player_addr + self.OFFSETS['name'])
                                if name_ptr:
                                    name = self.pm.read_string(name_ptr)
                            except:
                                pass
                            
                            vel_x = vel_y = vel_z = 0
                            if self.predict_movement.get():
                                try:
                                    vel_x = self.pm.read_float(player_addr + self.OFFSETS['velocity'])
                                    vel_y = self.pm.read_float(player_addr + self.OFFSETS['velocity'] + 4)
                                    vel_z = self.pm.read_float(player_addr + self.OFFSETS['velocity'] + 8)
                                except:
                                    pass
                            
                            players.append({
                                'health': health,
                                'x': x, 'y': y, 'z': z,
                                'team': team, 'name': name,
                                'vel_x': vel_x, 'vel_y': vel_y, 'vel_z': vel_z
                            })
                    
                    current = self.pm.read_longlong(current + 0x8)
                    if not current:
                        break
                except:
                    break
        except:
            pass
        
        return players
    
    def world_to_screen(self, x, y, z):
        try:
            view_matrix = self.pm.read_longlong(self.base_addr + self.OFFSETS['view_matrix'])
            if not view_matrix:
                return None
            
            matrix = []
            for i in range(16):
                matrix.append(self.pm.read_float(view_matrix + (i * 4)))
            
            w = (matrix[3] * x) + (matrix[7] * y) + (matrix[11] * z) + matrix[15]
            if w < 0.01:
                return None
            
            inv_w = 1.0 / w
            screen_x = (matrix[0] * x + matrix[4] * y + matrix[8] * z + matrix[12]) * inv_w
            screen_y = (matrix[1] * x + matrix[5] * y + matrix[9] * z + matrix[13]) * inv_w
            
            rect = win32gui.GetWindowRect(self.roblox_hwnd)
            screen_width = rect[2] - rect[0]
            screen_height = rect[3] - rect[1]
            
            screen_x = (screen_width / 2) + (screen_x * screen_width / 2)
            screen_y = (screen_height / 2) - (screen_y * screen_height / 2)
            
            return (int(screen_x + rect[0]), int(screen_y + rect[1]))
        except:
            return None
    
    def esp_loop(self):
        """ESP drawing using Windows GDI"""
        while self.running and self.connected:
            if self.esp_enabled.get():
                self.players = self.read_player_data()
                
                # Get window DC for drawing
                hwnd = self.roblox_hwnd
                hdc = ctypes.windll.user32.GetDC(hwnd)
                
                # Create pen and brush for drawing
                pen = ctypes.windll.gdi32.CreatePen(0, 2, 0x00FF00)  # Green box
                old_pen = ctypes.windll.gdi32.SelectObject(hdc, pen)
                
                for player in self.players:
                    screen_pos = self.world_to_screen(player['x'], player['y'], player['z'])
                    if screen_pos:
                        x, y = screen_pos
                        
                        # Calculate box size based on distance
                        dist = math.sqrt(
                            (player['x'] - self.local_pos[0])**2 +
                            (player['y'] - self.local_pos[1])**2 +
                            (player['z'] - self.local_pos[2])**2
                        )
                        
                        box_height = int(6000 / max(dist, 1))
                        box_width = int(box_height * 0.6)
                        
                        # Draw rectangle
                        ctypes.windll.gdi32.Rectangle(hdc, 
                            x - box_width//2, y - box_height,
                            x + box_width//2, y)
                
                # Cleanup
                ctypes.windll.gdi32.SelectObject(hdc, old_pen)
                ctypes.windll.gdi32.DeleteObject(pen)
                ctypes.windll.user32.ReleaseDC(hwnd, hdc)
            
            time.sleep(0.05)  # 20 FPS
    
    def aimbot_loop(self):
        while self.running and self.connected:
            if self.aimbot_enabled.get():
                if self.aim_on_rmb.get() and not pyautogui.mouse.pressed()[1]:
                    time.sleep(0.01)
                    continue
                
                # Find best target
                best_target = None
                best_score = float('inf')
                center_x, center_y = pyautogui.size()
                center_x //= 2
                center_y //= 2
                
                for player in self.players:
                    if player['team'] != 0:  # Skip teammates
                        continue
                    
                    screen_pos = self.world_to_screen(player['x'], player['y'], player['z'])
                    if screen_pos:
                        dist = math.sqrt(
                            (screen_pos[0] - center_x)**2 + 
                            (screen_pos[1] - center_y)**2
                        )
                        
                        if dist < self.aim_fov.get() * 5:
                            if dist < best_score:
                                best_score = dist
                                best_target = screen_pos
                
                if best_target:
                    move_x = (best_target[0] - center_x) / self.aim_smoothness.get()
                    move_y = (best_target[1] - center_y) / self.aim_smoothness.get()
                    pyautogui.moveRel(move_x, move_y)
            
            time.sleep(0.001)
    
    def no_recoil_loop(self):
        bullet_count = 0
        while self.running and self.connected:
            if self.no_recoil_enabled.get():
                if pyautogui.mouse.pressed()[0]:
                    pull = self.recoil_strength.get() * (1 + bullet_count * 0.1)
                    pyautogui.moveRel(0, pull, duration=0.005)
                    bullet_count += 1
                    time.sleep(0.05)
                else:
                    bullet_count = 0
            time.sleep(0.01)
    
    def setup_ui(self):
        # Header
        header = tk.Label(
            self.root, 
            text="BLOXSTRIKE EXTERNAL v2.0",
            bg='#1C1C2A',
            fg='#735C9C',
            font=("Arial", 16, "bold")
        )
        header.pack(pady=10)
        
        # Notebook for tabs
        notebook = ttk.Notebook(self.root)
        notebook.pack(expand=True, fill='both', padx=10, pady=5)
        
        # Style
        style = ttk.Style()
        style.theme_use('default')
        style.configure('TNotebook', background='#1C1C2A')
        style.configure('TNotebook.Tab', background='#2D2D3A', foreground='white')
        style.map('TNotebook.Tab', background=[('selected', '#735C9C')])
        
        # AIMBOT TAB
        aimbot_frame = tk.Frame(notebook, bg='#1C1C2A')
        notebook.add(aimbot_frame, text="  AIMBOT  ")
        
        tk.Checkbutton(
            aimbot_frame, text="Enable Aimbot",
            variable=self.aimbot_enabled,
            bg='#1C1C2A', fg='white',
            selectcolor='#1C1C2A', activebackground='#1C1C2A'
        ).pack(anchor='w', pady=5)
        
        tk.Checkbutton(
            aimbot_frame, text="On RMB Only",
            variable=self.aim_on_rmb,
            bg='#1C1C2A', fg='white',
            selectcolor='#1C1C2A', activebackground='#1C1C2A'
        ).pack(anchor='w', pady=5)
        
        tk.Label(aimbot_frame, text="FOV:", bg='#1C1C2A', fg='white').pack(anchor='w')
        tk.Scale(
            aimbot_frame, from_=1, to=180, orient='horizontal',
            variable=self.aim_fov,
            bg='#1C1C2A', fg='white',
            highlightbackground='#1C1C2A'
        ).pack(fill='x', pady=5)
        
        tk.Label(aimbot_frame, text="Smoothness:", bg='#1C1C2A', fg='white').pack(anchor='w')
        tk.Scale(
            aimbot_frame, from_=1, to=20, orient='horizontal',
            variable=self.aim_smoothness,
            bg='#1C1C2A', fg='white',
            highlightbackground='#1C1C2A'
        ).pack(fill='x', pady=5)
        
        tk.Checkbutton(
            aimbot_frame, text="Predict Movement",
            variable=self.predict_movement,
            bg='#1C1C2A', fg='white',
            selectcolor='#1C1C2A', activebackground='#1C1C2A'
        ).pack(anchor='w', pady=5)
        
        # ESP TAB
        esp_frame = tk.Frame(notebook, bg='#1C1C2A')
        notebook.add(esp_frame, text="  ESP  ")
        
        tk.Checkbutton(
            esp_frame, text="Enable ESP",
            variable=self.esp_enabled,
            bg='#1C1C2A', fg='white',
            selectcolor='#1C1C2A', activebackground='#1C1C2A'
        ).pack(anchor='w', pady=5)
        
        tk.Checkbutton(
            esp_frame, text="Show Names",
            variable=self.show_names,
            bg='#1C1C2A', fg='white',
            selectcolor='#1C1C2A', activebackground='#1C1C2A'
        ).pack(anchor='w', pady=2)
        
        tk.Checkbutton(
            esp_frame, text="Show Health Bars",
            variable=self.show_health,
            bg='#1C1C2A', fg='white',
            selectcolor='#1C1C2A', activebackground='#1C1C2A'
        ).pack(anchor='w', pady=2)
        
        tk.Checkbutton(
            esp_frame, text="Show Distance",
            variable=self.show_distance,
            bg='#1C1C2A', fg='white',
            selectcolor='#1C1C2A', activebackground='#1C1C2A'
        ).pack(anchor='w', pady=2)
        
        # MISC TAB
        misc_frame = tk.Frame(notebook, bg='#1C1C2A')
        notebook.add(misc_frame, text="  MISC  ")
        
        tk.Checkbutton(
            misc_frame, text="Enable No Recoil",
            variable=self.no_recoil_enabled,
            bg='#1C1C2A', fg='white',
            selectcolor='#1C1C2A', activebackground='#1C1C2A'
        ).pack(anchor='w', pady=5)
        
        tk.Label(misc_frame, text="Recoil Strength:", bg='#1C1C2A', fg='white').pack(anchor='w')
        tk.Scale(
            misc_frame, from_=1, to=10, orient='horizontal',
            variable=self.recoil_strength,
            bg='#1C1C2A', fg='white',
            highlightbackground='#1C1C2A'
        ).pack(fill='x', pady=5)
        
        # Hotkeys section
        hotkey_frame = tk.Frame(misc_frame, bg='#1C1C2A')
        hotkey_frame.pack(fill='x', pady=10)
        
        tk.Label(hotkey_frame, text="Hotkeys:", bg='#1C1C2A', fg='#735C9C', 
                font=("Arial", 10, "bold")).pack(anchor='w')
        tk.Label(hotkey_frame, text="INSERT - Show Menu", bg='#1C1C2A', fg='white').pack(anchor='w')
        tk.Label(hotkey_frame, text="F9 - Hide Menu", bg='#1C1C2A', fg='white').pack(anchor='w')
        tk.Label(hotkey_frame, text="RMB - Aimbot", bg='#1C1C2A', fg='white').pack(anchor='w')
        tk.Label(hotkey_frame, text="Left Click - No Recoil", bg='#1C1C2A', fg='white').pack(anchor='w')
        
        # Status bar
        status_frame = tk.Frame(self.root, bg='#2D2D3A', height=30)
        status_frame.pack(fill='x', side='bottom')
        
        self.status_label = tk.Label(
            status_frame,
            text="",
            bg='#2D2D3A',
            fg='#FFFFFF',
            anchor='w'
        )
        self.status_label.pack(side='left', padx=10, pady=5)
        
        # Initial status
        if self.connected:
            self.status_label.config(text=f"✅ Connected | Players: {len(self.players)} | Health: {self.local_health}")
        else:
            self.status_label.config(text="❌ Disconnected - Start Roblox")
    
    def update_status(self):
        if self.running and hasattr(self, 'status_label'):
            if self.connected:
                self.status_label.config(
                    text=f"✅ Connected | Players: {len(self.players)} | Health: {self.local_health}"
                )
            else:
                self.status_label.config(text="❌ Disconnected - Start Roblox")
            self.root.after(1000, self.update_status)
    
    def toggle_visibility(self, event=None):
        if self.root.state() == 'normal':
            self.root.withdraw()
        else:
            self.root.deiconify()
    
    def run(self):
        self.root.mainloop()
        self.running = False

if __name__ == "__main__":
    print("Starting BloxStrike External (Tkinter Version)")
    cheat = BloxStrikeCheat()
    cheat.run()