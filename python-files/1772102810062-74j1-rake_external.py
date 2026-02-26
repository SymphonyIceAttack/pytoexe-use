"""
Rake External V1.0
Roblox External ESP + Aimbot
"""

import ctypes
import ctypes.wintypes
import json
import requests
import time
import math
import threading
import sys
import os
import base64
from ctypes import wintypes
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict
import tkinter as tk
from tkinter import ttk
import tkinter.simpledialog
import pyglet
from pyglet import gl
import numpy as np
import psutil
import keyboard
import mouse
import win32gui
import win32con
import win32api
import win32process
import random
from collections import OrderedDict

# ============================================
# CONFIGURATION & CONSTANTS
# ============================================

OFFSETS_URL = "https://offsets.ntgetwritewatch.workers.dev/offsets.json"
CACHE_FILE = "offsets_cache.json"
PROCESS_NAME = "RobloxPlayerBeta.exe"
WINDOW_TITLE = "Rake External V1.0"

# Colors (RGB)
COLOR_DARK_GREEN = (0, 40, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_GREY = (128, 128, 128)
COLOR_GREEN = (0, 255, 0)
COLOR_RED = (255, 0, 0)
COLOR_BLACK = (0, 0, 0)

# Assumed structure offsets for children list (common in Roblox)
CHILDREN_LIST_COUNT_OFFSET = 0x8
CHILDREN_LIST_ARRAY_OFFSET = 0x10

# ============================================
# WINDOWS API SETUP
# ============================================

class WindowsAPI:
    """Centralized Windows API access"""
    
    kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)
    user32 = ctypes.WinDLL('user32', use_last_error=True)
    gdi32 = ctypes.WinDLL('gdi32', use_last_error=True)
    
    # Constants
    PROCESS_VM_READ = 0x0010
    PROCESS_VM_WRITE = 0x0020
    PROCESS_VM_OPERATION = 0x0008
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_ALL_ACCESS = 0x1F0FFF
    
    MEM_COMMIT = 0x1000
    MEM_RESERVE = 0x2000
    PAGE_READWRITE = 0x04
    PAGE_EXECUTE_READWRITE = 0x40
    
    HWND_TOPMOST = -1
    SWP_NOMOVE = 0x0002
    SWP_NOSIZE = 0x0001
    WS_EX_LAYERED = 0x80000
    WS_EX_TRANSPARENT = 0x20
    WS_EX_TOOLWINDOW = 0x80
    WS_POPUP = 0x80000000
    WS_VISIBLE = 0x10000000
    
    @classmethod
    def open_process(cls, pid):
        """Open process with required access"""
        return cls.kernel32.OpenProcess(
            cls.PROCESS_VM_READ | cls.PROCESS_QUERY_INFORMATION,
            False,
            pid
        )
    
    @classmethod
    def read_memory(cls, handle, address, size, data_type='int'):
        """Read memory from process"""
        buffer = ctypes.create_string_buffer(size)
        bytes_read = ctypes.c_ulong(0)
        
        success = cls.kernel32.ReadProcessMemory(
            handle,
            ctypes.c_void_p(address),
            buffer,
            size,
            ctypes.byref(bytes_read)
        )
        
        if not success:
            return None
        
        if data_type == 'float':
            return ctypes.c_float.from_buffer_copy(buffer.raw).value
        elif data_type == 'int':
            return int.from_bytes(buffer.raw, byteorder='little')
        elif data_type == 'bool':
            return bool(int.from_bytes(buffer.raw, byteorder='little'))
        elif data_type == 'string':
            return buffer.raw.decode('utf-8', errors='ignore').split('\x00')[0]
        elif data_type == 'vector3':
            floats = [ctypes.c_float.from_buffer_copy(buffer.raw[i:i+4]).value 
                     for i in range(0, size, 4)]
            return Vector3(*floats[:3])
        
        return buffer.raw
    
    @classmethod
    def find_window(cls, class_name=None, window_name=None):
        """Find window by class or title"""
        return cls.user32.FindWindowW(class_name, window_name)
    
    @classmethod
    def set_window_pos(cls, hwnd, x, y, width, height, flags):
        """Set window position"""
        return cls.user32.SetWindowPos(hwnd, cls.HWND_TOPMOST, x, y, width, height, flags)
    
    @classmethod
    def set_window_long(cls, hwnd, index, value):
        """Set window long attribute"""
        return cls.user32.SetWindowLongW(hwnd, index, value)


# ============================================
# DATA STRUCTURES
# ============================================

@dataclass
class Vector2:
    x: float
    y: float
    
    def to_tuple(self):
        return (self.x, self.y)

@dataclass
class Vector3:
    x: float
    y: float
    z: float
    
    def to_tuple(self):
        return (self.x, self.y, self.z)
    
    def distance_to(self, other):
        """Calculate distance to another vector"""
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    def to_screen(self, viewmatrix, screen_width, screen_height):
        """Convert 3D world position to 2D screen coordinates"""
        try:
            clip_x = self.x * viewmatrix[0] + self.y * viewmatrix[4] + self.z * viewmatrix[8] + viewmatrix[12]
            clip_y = self.x * viewmatrix[1] + self.y * viewmatrix[5] + self.z * viewmatrix[9] + viewmatrix[13]
            clip_z = self.x * viewmatrix[2] + self.y * viewmatrix[6] + self.z * viewmatrix[10] + viewmatrix[14]
            clip_w = self.x * viewmatrix[3] + self.y * viewmatrix[7] + self.z * viewmatrix[11] + viewmatrix[15]
            
            if clip_w < 0.1:
                return None
            
            ndc_x = clip_x / clip_w
            ndc_y = clip_y / clip_w
            
            screen_x = (screen_width / 2) * ndc_x + (screen_x + screen_width / 2)
            screen_y = -(screen_height / 2) * ndc_y + (screen_y + screen_height / 2)
            
            return Vector2(screen_x, screen_y)
        except:
            return None

@dataclass
class Player:
    """Player data structure"""
    address: int
    name: str
    display_name: str
    health: int
    max_health: int
    position: Vector3
    team: int
    is_alive: bool
    distance: float
    user_id: int = 0
    
    def health_percent(self):
        """Get health percentage"""
        if self.max_health > 0:
            return (self.health / self.max_health) * 100
        return 0

@dataclass
class Config:
    """Configuration settings"""
    # ESP Toggles
    box_esp: bool = True
    health_esp: bool = True
    name_esp: bool = True
    distance_esp: bool = True
    
    # Aimbot Settings
    camera_aimbot: bool = False
    mouse_aimbot: bool = False
    aimbot_smoothness: float = 5.0
    aimbot_fov: float = 200.0
    aimbot_on: bool = False
    
    # Aimbot Keybind Settings
    aimbot_keybind1: str = "shift"
    aimbot_keybind2: str = "ctrl"
    aimbot_activation_mode: str = "hold"
    aimbot_toggle_active: bool = False
    
    # Visual
    menu_visible: bool = True
    overlay_visible: bool = True


# ============================================
# OFFSET MANAGER
# ============================================

class OffsetManager:
    """Manages Roblox memory offsets"""
    
    _instance = None
    _offsets = {}
    _version = ""
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def fetch_offsets(self):
        """Fetch latest offsets from API"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(OFFSETS_URL, headers=headers, timeout=5)
            data = response.json()
            
            self._version = data.get('RobloxVersion', 'unknown')
            self._offsets = {k: int(v, 16) if isinstance(v, str) and v.startswith('0x') else v 
                           for k, v in data.items() if k != 'RobloxVersion' and k != 'ByfronVersion'}
            
            with open(CACHE_FILE, 'w') as f:
                json.dump(data, f)
            
            print(f"[+] Loaded offsets for version: {self._version}")
            return True
        except Exception as e:
            print(f"[-] Failed to fetch offsets: {e}")
            return self.load_cached()
    
    def load_cached(self):
        """Load cached offsets from file"""
        try:
            if os.path.exists(CACHE_FILE):
                with open(CACHE_FILE, 'r') as f:
                    data = json.load(f)
                    self._version = data.get('RobloxVersion', 'unknown')
                    self._offsets = {k: int(v, 16) if isinstance(v, str) and v.startswith('0x') else v 
                                   for k, v in data.items() if k != 'RobloxVersion' and k != 'ByfronVersion'}
                print(f"[+] Loaded cached offsets for version: {self._version}")
                return True
        except:
            pass
        return False
    
    def get(self, name, default=0):
        """Get offset by name"""
        return self._offsets.get(name, default)


# ============================================
# ROBLOX MEMORY READER - FULLY FUNCTIONAL
# ============================================

class RobloxMemory:
    """Handles all Roblox memory operations"""
    
    def __init__(self):
        self.offsets = OffsetManager()
        self.pid = None
        self.handle = None
        self.process = None
        self.module_base = None
        
        # Cached addresses
        self.players_service_addr = 0
        self.last_players_service_check = 0
        
    def find_process(self):
        """Find Roblox process"""
        for proc in psutil.process_iter(['pid', 'name']):
            if proc.info['name'] == PROCESS_NAME:
                self.pid = proc.info['pid']
                self.process = proc
                print(f"[+] Found Roblox (PID: {self.pid})")
                return True
        return False
    
    def open(self):
        """Open process handle"""
        if not self.pid and not self.find_process():
            return False
        
        self.handle = WindowsAPI.open_process(self.pid)
        if not self.handle:
            print("[-] Failed to open process")
            return False
        
        # Get module base address
        try:
            for module in self.process.memory_maps(grouped=False):
                if module.path and PROCESS_NAME in module.path:
                    self.module_base = int(module.addr, 16)
                    print(f"[+] Module base: 0x{self.module_base:X}")
                    break
        except:
            pass
        
        return True
    
    def close(self):
        """Close process handle"""
        if self.handle:
            WindowsAPI.kernel32.CloseHandle(self.handle)
            self.handle = None
    
    def read_ptr(self, address):
        """Read pointer at address"""
        val = WindowsAPI.read_memory(self.handle, address, 8, 'int')
        return val if val else 0
    
    def read_float(self, address):
        """Read float at address"""
        return WindowsAPI.read_memory(self.handle, address, 4, 'float')
    
    def read_int(self, address):
        """Read int at address"""
        return WindowsAPI.read_memory(self.handle, address, 4, 'int')
    
    def read_bool(self, address):
        """Read bool at address"""
        return WindowsAPI.read_memory(self.handle, address, 1, 'bool')
    
    def read_string(self, address, max_length=50):
        """Read string at address"""
        return WindowsAPI.read_memory(self.handle, address, max_length, 'string')
    
    def read_vector3(self, address):
        """Read Vector3 at address"""
        return WindowsAPI.read_memory(self.handle, address, 12, 'vector3')
    
    def get_children(self, instance_addr):
        """
        Get children of an instance using the Children offset.
        Returns list of child addresses.
        """
        if not instance_addr:
            return []
        
        children_ptr = self.read_ptr(instance_addr + self.offsets.get("Children", 0))
        if not children_ptr:
            return []
        
        # Assume children list structure: count at +0x8, array at +0x10
        count = self.read_int(children_ptr + CHILDREN_LIST_COUNT_OFFSET)
        array_ptr = self.read_ptr(children_ptr + CHILDREN_LIST_ARRAY_OFFSET)
        
        if not array_ptr or count <= 0 or count > 500:  # sanity
            return []
        
        children = []
        for i in range(count):
            child = self.read_ptr(array_ptr + i * 8)
            if child:
                children.append(child)
        return children
    
    def get_instance_name(self, addr):
        """Get name of an instance"""
        name_addr = self.read_ptr(addr + self.offsets.get("Name", 0))
        if name_addr:
            return self.read_string(name_addr)
        return ""
    
    def get_local_player(self):
        """Get local player object address"""
        workspace_addr = self.module_base + self.offsets.get("Workspace", 0)
        if not workspace_addr:
            return 0
        local_player_addr = self.read_ptr(workspace_addr + self.offsets.get("LocalPlayer", 0))
        return local_player_addr
    
    def get_players_service(self):
        """
        Find the Players service by traversing DataModel children.
        Cached for 5 seconds.
        """
        current_time = time.time()
        if self.players_service_addr and current_time - self.last_players_service_check < 5:
            return self.players_service_addr
        
        # Get DataModel (parent of Workspace)
        workspace_addr = self.module_base + self.offsets.get("Workspace", 0)
        if not workspace_addr:
            return 0
        
        datamodel_addr = self.read_ptr(workspace_addr + self.offsets.get("Parent", 0))
        if not datamodel_addr:
            return 0
        
        # Iterate children of DataModel to find "Players"
        for child in self.get_children(datamodel_addr):
            name = self.get_instance_name(child)
            if name == "Players":
                self.players_service_addr = child
                self.last_players_service_check = current_time
                print(f"[+] Found Players service at 0x{child:X}")
                return child
        
        print("[!] Players service not found")
        return 0
    
    def get_all_players(self, local_player_addr=None):
        """
        Enumerate all players from the Players service.
        Returns list of Player objects.
        """
        players_dict = OrderedDict()
        
        if not local_player_addr:
            local_player_addr = self.get_local_player()
        if not local_player_addr:
            return []
        
        # Add local player
        local_player = self._read_player_data(local_player_addr)
        if local_player:
            players_dict[local_player_addr] = local_player
        
        # Get Players service
        players_service = self.get_players_service()
        if not players_service:
            # Fallback to scanning
            print("[!] Using fallback player scan")
            return self._scan_for_players(local_player_addr)
        
        # Iterate children of Players service
        for child in self.get_children(players_service):
            if child == local_player_addr:
                continue
            # Verify it's a player (has health, name, etc.)
            player = self._read_player_data(child)
            if player:
                players_dict[child] = player
        
        print(f"[+] Found {len(players_dict)} players")
        return list(players_dict.values())
    
    def _scan_for_players(self, local_player_addr):
        """Fallback: scan memory for potential player objects"""
        players_dict = {local_player_addr: self._read_player_data(local_player_addr)}
        scan_start = self.module_base
        scan_size = 0x1000000  # 16MB
        step = 0x1000
        
        for offset in range(0, scan_size, step):
            addr = scan_start + offset
            name_addr = self.read_ptr(addr + self.offsets.get("Name", 0))
            if not name_addr:
                continue
            name = self.read_string(name_addr)
            if not name or len(name) > 20 or len(name) < 2:
                continue
            
            health = self.read_float(addr + self.offsets.get("Health", 0))
            if health is None or health < 0 or health > 100:
                continue
            
            player = self._read_player_data(addr)
            if player and player.name not in ("", "Unknown") and player.address not in players_dict:
                players_dict[addr] = player
        
        print(f"[+] Fallback scan found {len(players_dict)} players")
        return list(players_dict.values())
    
    def _read_player_data(self, player_addr):
        """Read all player data from a player object address"""
        try:
            name_addr = self.read_ptr(player_addr + self.offsets.get("Name", 0))
            name = self.read_string(name_addr) if name_addr else "Unknown"
            
            display_name_addr = self.read_ptr(player_addr + self.offsets.get("DisplayName", 0))
            display_name = self.read_string(display_name_addr) if display_name_addr else name
            
            user_id = self.read_int(player_addr + self.offsets.get("UserId", 0))
            
            char_addr = self.read_ptr(player_addr + self.offsets.get("Character", 0))
            if not char_addr:
                return None
            
            health = self.read_float(char_addr + self.offsets.get("Health", 0))
            max_health = self.read_float(char_addr + self.offsets.get("MaxHealth", 0))
            if health is None or max_health is None:
                return None
            
            root_part = self.read_ptr(char_addr + self.offsets.get("RootPartR6", 0))
            if not root_part:
                root_part = self.read_ptr(char_addr + self.offsets.get("RootPartR15", 0))
            if not root_part:
                return None
            
            position = self.read_vector3(root_part + self.offsets.get("Position", 0))
            
            is_alive = health > 0 and max_health > 0
            
            team_addr = self.read_ptr(player_addr + self.offsets.get("Team", 0))
            team = self.read_int(team_addr) if team_addr else 0
            
            return Player(
                address=player_addr,
                name=name,
                display_name=display_name,
                health=health,
                max_health=max_health,
                position=position,
                team=team,
                is_alive=is_alive,
                distance=0,
                user_id=user_id
            )
        except:
            return None
    
    def get_camera(self):
        """Get camera object and view matrix"""
        camera_addr = self.module_base + self.offsets.get("Camera", 0)
        if not camera_addr:
            return None, None
        
        camera_obj = self.read_ptr(camera_addr)
        if not camera_obj:
            return None, None
        
        viewmatrix_addr = camera_obj + self.offsets.get("viewmatrix", 0)
        viewmatrix = [self.read_float(viewmatrix_addr + i * 4) for i in range(16)]
        return camera_obj, viewmatrix


# ============================================
# AIMBOT LOGIC
# ============================================

class Aimbot:
    """Aimbot functionality with keybinds and toggle/hold modes"""
    
    def __init__(self, memory, config):
        self.memory = memory
        self.config = config
        self.target = None
        self.screen_center = Vector2(960, 540)
        self.last_toggle_time = 0
        
    def update_screen_center(self):
        """Update screen center from window size"""
        try:
            hwnd = WindowsAPI.find_window(None, "Roblox")
            if hwnd:
                rect = win32gui.GetWindowRect(hwnd)
                self.screen_center = Vector2(
                    (rect[0] + rect[2]) // 2,
                    (rect[1] + rect[3]) // 2
                )
        except:
            pass
    
    def should_aim(self):
        """Check if aimbot should be active based on keybind mode"""
        if not self.config.aimbot_on:
            return False
        
        key1_pressed = keyboard.is_pressed(self.config.aimbot_keybind1)
        key2_pressed = keyboard.is_pressed(self.config.aimbot_keybind2)
        any_key_pressed = key1_pressed or key2_pressed
        
        if self.config.aimbot_activation_mode == "hold":
            return any_key_pressed
        else:
            if any_key_pressed:
                current_time = time.time()
                if current_time - self.last_toggle_time > 0.3:
                    self.last_toggle_time = current_time
                    self.config.aimbot_toggle_active = not self.config.aimbot_toggle_active
            return self.config.aimbot_toggle_active
    
    def find_target(self, players, viewmatrix, screen_size):
        """Find best target within FOV"""
        if not players or not self.should_aim():
            return None
        
        best_target = None
        best_distance = float('inf')
        
        local_player = None
        for p in players:
            if p.address == self.memory.get_local_player():
                local_player = p
                break
        
        for player in players:
            if player.address == (local_player.address if local_player else 0):
                continue
            if not player.is_alive:
                continue
            
            screen_pos = player.position.to_screen(viewmatrix, screen_size[0], screen_size[1])
            if not screen_pos:
                continue
            
            dist = math.sqrt(
                (screen_pos.x - self.screen_center.x) ** 2 + 
                (screen_pos.y - self.screen_center.y) ** 2
            )
            
            if dist < self.config.aimbot_fov and dist < best_distance:
                best_distance = dist
                best_target = (player, screen_pos)
        
        return best_target
    
    def smooth_aim(self, target_pos, current_pos, smoothness):
        """Smooth aim movement"""
        if smoothness <= 0:
            return target_pos
        
        dx = target_pos.x - current_pos.x
        dy = target_pos.y - current_pos.y
        
        return Vector2(
            current_pos.x + dx / smoothness,
            current_pos.y + dy / smoothness
        )
    
    def aim_mouse(self, target_pos):
        """Aim using mouse movement"""
        try:
            current = Vector2(*win32api.GetCursorPos())
            smooth_pos = self.smooth_aim(target_pos, current, self.config.aimbot_smoothness)
            win32api.SetCursorPos(int(smooth_pos.x), int(smooth_pos.y))
        except:
            pass


# ============================================
# ESP OVERLAY
# ============================================

class ESPOverlay:
    """Transparent overlay for drawing ESP"""
    
    def __init__(self, config):
        self.config = config
        self.window = None
        self.width = 1920
        self.height = 1080
        self.hwnd = None
        self.running = True
        self.players = []
        self.viewmatrix = None
        self.local_player = None
        
        self.setup_window()
        
    def setup_window(self):
        """Create transparent overlay window"""
        try:
            self.window = pyglet.window.Window(
                width=self.width,
                height=self.height,
                caption="Rake External V1.0",
                style=pyglet.window.Window.WINDOW_STYLE_OVERLAY,
                fullscreen=False
            )
            
            self.hwnd = self.window._hwnd
            
            ex_style = WindowsAPI.WS_EX_LAYERED | WindowsAPI.WS_EX_TRANSPARENT | WindowsAPI.WS_EX_TOOLWINDOW
            WindowsAPI.set_window_long(self.hwnd, win32con.GWL_EXSTYLE, ex_style)
            
            WindowsAPI.user32.SetLayeredWindowAttributes(
                self.hwnd, 
                0, 
                255, 
                win32con.LWA_ALPHA
            )
            
            WindowsAPI.set_window_pos(
                self.hwnd, 
                0, 0, self.width, self.height,
                WindowsAPI.SWP_NOMOVE | WindowsAPI.SWP_NOSIZE
            )
            
            self.window.on_draw = self.on_draw
            self.window.on_close = self.on_close
            
        except Exception as e:
            print(f"[-] Failed to setup overlay: {e}")
    
    def on_draw(self):
        """Draw ESP elements"""
        self.window.clear()
        
        if not self.config.overlay_visible or not self.players:
            return
        
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        
        for player in self.players:
            if player.address == (self.local_player.address if self.local_player else 0):
                continue
            if not player.is_alive:
                continue
            
            screen_pos = player.position.to_screen(self.viewmatrix, self.width, self.height)
            if not screen_pos:
                continue
            
            distance = player.position.distance_to(self.local_player.position) if self.local_player else 0
            box_height = 6000 / distance if distance > 0 else 100
            box_height = max(30, min(200, box_height))
            box_width = box_height * 0.6
            
            if self.config.box_esp:
                self.draw_box(
                    screen_pos.x - box_width/2,
                    screen_pos.y - box_height,
                    box_width,
                    box_height,
                    COLOR_RED if player.team != (self.local_player.team if self.local_player else 0) else COLOR_GREEN
                )
            
            if self.config.health_esp and player.max_health > 0:
                health_percent = player.health / player.max_health
                self.draw_health_bar(
                    screen_pos.x - box_width/2,
                    screen_pos.y - box_height - 5,
                    box_width,
                    3,
                    health_percent
                )
            
            if self.config.name_esp:
                self.draw_text(
                    screen_pos.x,
                    screen_pos.y - box_height - 20,
                    player.display_name,
                    COLOR_WHITE
                )
            
            if self.config.distance_esp:
                self.draw_text(
                    screen_pos.x,
                    screen_pos.y,
                    f"{int(distance)}m",
                    COLOR_WHITE
                )
    
    def draw_box(self, x, y, width, height, color):
        """Draw a box outline"""
        gl.glColor4f(color[0]/255, color[1]/255, color[2]/255, 1.0)
        gl.glLineWidth(2.0)
        
        pyglet.graphics.draw(4, gl.GL_LINE_LOOP,
            ('v2f', [x, y, x+width, y, x+width, y+height, x, y+height])
        )
        
        gl.glColor4f(0, 0, 0, 1.0)
        gl.glLineWidth(1.0)
        pyglet.graphics.draw(4, gl.GL_LINE_LOOP,
            ('v2f', [x-1, y-1, x+width+1, y-1, x+width+1, y+height+1, x-1, y+height+1])
        )
    
    def draw_health_bar(self, x, y, width, height, percent):
        """Draw health bar"""
        gl.glColor4f(0, 0, 0, 0.8)
        pyglet.graphics.draw(4, gl.GL_QUADS,
            ('v2f', [x, y, x+width, y, x+width, y+height, x, y+height])
        )
        
        if percent > 0.5:
            r = 1 - (percent - 0.5) * 2
            g = 1
        else:
            r = 1
            g = percent * 2
        b = 0
        
        gl.glColor4f(r, g, b, 0.8)
        pyglet.graphics.draw(4, gl.GL_QUADS,
            ('v2f', [x, y, x + width * percent, y, x + width * percent, y+height, x, y+height])
        )
    
    def draw_text(self, x, y, text, color):
        """Draw text with outline"""
        label = pyglet.text.Label(
            text,
            font_name='Arial',
            font_size=12,
            bold=True,
            x=x, y=y,
            anchor_x='center', anchor_y='center',
            color=(0, 0, 0, 255)
        )
        for dx in [-1, 1]:
            for dy in [-1, 1]:
                label.x = x + dx
                label.y = y + dy
                label.draw()
        
        label.x = x
        label.y = y
        label.color = (color[0], color[1], color[2], 255)
        label.draw()
    
    def update(self, players, viewmatrix, local_player):
        """Update ESP data"""
        self.players = players
        self.viewmatrix = viewmatrix
        self.local_player = local_player
    
    def on_close(self):
        """Handle window close"""
        self.running = False
    
    def run(self):
        """Run overlay loop"""
        if self.window:
            pyglet.app.run()
    
    def hide(self):
        """Hide overlay"""
        if self.window:
            self.window.set_visible(False)
            self.config.overlay_visible = False
    
    def show(self):
        """Show overlay"""
        if self.window:
            self.window.set_visible(True)
            self.config.overlay_visible = True


# ============================================
# MENU UI
# ============================================

class MenuUI:
    """Menu interface using tkinter"""
    
    def __init__(self, config):
        self.config = config
        self.root = None
        self.running = True
        self.setup_ui()
        
    def setup_ui(self):
        """Create menu window"""
        self.root = tk.Tk()
        self.root.title("Rake External V1.0")
        self.root.geometry("400x650")
        self.root.configure(bg='#002800')
        
        self.root.attributes('-topmost', True)
        self.root.overrideredirect(True)
        
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 200
        y = (self.root.winfo_screenheight() // 2) - 325
        self.root.geometry(f'400x650+{x}+{y}')
        
        title_bar = tk.Frame(self.root, bg='#001800', relief='raised', bd=0)
        title_bar.pack(fill='x')
        
        title_label = tk.Label(
            title_bar, 
            text="  Rake External V1.0", 
            bg='#001800', 
            fg='white',
            font=('Arial', 12, 'bold')
        )
        title_label.pack(side='left', pady=5)
        
        close_btn = tk.Button(
            title_bar,
            text=' X ',
            bg='#001800',
            fg='white',
            bd=0,
            font=('Arial', 10, 'bold'),
            command=self.hide_menu
        )
        close_btn.pack(side='right', padx=5)
        
        title_label.bind('<Button-1>', self.start_move)
        title_label.bind('<B1-Motion>', self.on_move)
        title_bar.bind('<Button-1>', self.start_move)
        title_bar.bind('<B1-Motion>', self.on_move)
        
        main_frame = tk.Frame(self.root, bg='#002800')
        main_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # ESP Section
        esp_label = tk.Label(
            main_frame,
            text="ESP Settings",
            bg='#002800',
            fg='white',
            font=('Arial', 14, 'bold')
        )
        esp_label.pack(pady=10)
        
        self.box_esp_var = tk.BooleanVar(value=self.config.box_esp)
        self.create_toggle(main_frame, "Box ESP", self.box_esp_var, 
                          lambda: self.toggle_setting('box_esp', self.box_esp_var))
        
        self.health_esp_var = tk.BooleanVar(value=self.config.health_esp)
        self.create_toggle(main_frame, "Health ESP", self.health_esp_var,
                          lambda: self.toggle_setting('health_esp', self.health_esp_var))
        
        self.name_esp_var = tk.BooleanVar(value=self.config.name_esp)
        self.create_toggle(main_frame, "Name ESP", self.name_esp_var,
                          lambda: self.toggle_setting('name_esp', self.name_esp_var))
        
        self.distance_esp_var = tk.BooleanVar(value=self.config.distance_esp)
        self.create_toggle(main_frame, "Distance ESP", self.distance_esp_var,
                          lambda: self.toggle_setting('distance_esp', self.distance_esp_var))
        
        separator = tk.Frame(main_frame, height=2, bd=1, relief='sunken', bg='#004000')
        separator.pack(fill='x', pady=15)
        
        # Aimbot Section
        aimbot_label = tk.Label(
            main_frame,
            text="Aimbot Settings",
            bg='#002800',
            fg='white',
            font=('Arial', 14, 'bold')
        )
        aimbot_label.pack(pady=10)
        
        self.aimbot_var = tk.BooleanVar(value=self.config.aimbot_on)
        self.create_toggle(main_frame, "Aimbot Master", self.aimbot_var,
                          lambda: self.toggle_setting('aimbot_on', self.aimbot_var))
        
        self.camera_aimbot_var = tk.BooleanVar(value=self.config.camera_aimbot)
        self.create_toggle(main_frame, "Camera Aimbot", self.camera_aimbot_var,
                          lambda: self.toggle_setting('camera_aimbot', self.camera_aimbot_var))
        
        self.mouse_aimbot_var = tk.BooleanVar(value=self.config.mouse_aimbot)
        self.create_toggle(main_frame, "Mouse Aimbot", self.mouse_aimbot_var,
                          lambda: self.toggle_setting('mouse_aimbot', self.mouse_aimbot_var))
        
        # Keybind 1 selection
        keybind1_frame = tk.Frame(main_frame, bg='#002800')
        keybind1_frame.pack(fill='x', pady=5)
        
        tk.Label(keybind1_frame, text="Keybind 1:", bg='#002800', fg='white').pack(side='left')
        self.keybind1_label = tk.Label(keybind1_frame, text=f"  {self.config.aimbot_keybind1}  ", 
                                      bg='#004000', fg='white', relief='sunken', width=8)
        self.keybind1_label.pack(side='right')
        self.keybind1_label.bind('<Button-1>', lambda e: self.choose_keybind(1))
        
        # Keybind 2 selection
        keybind2_frame = tk.Frame(main_frame, bg='#002800')
        keybind2_frame.pack(fill='x', pady=5)
        
        tk.Label(keybind2_frame, text="Keybind 2:", bg='#002800', fg='white').pack(side='left')
        self.keybind2_label = tk.Label(keybind2_frame, text=f"  {self.config.aimbot_keybind2}  ", 
                                      bg='#004000', fg='white', relief='sunken', width=8)
        self.keybind2_label.pack(side='right')
        self.keybind2_label.bind('<Button-1>', lambda e: self.choose_keybind(2))
        
        # Activation mode selection
        mode_frame = tk.Frame(main_frame, bg='#002800')
        mode_frame.pack(fill='x', pady=5)
        
        tk.Label(mode_frame, text="Activation Mode:", bg='#002800', fg='white').pack(side='left')
        
        self.mode_var = tk.StringVar(value=self.config.aimbot_activation_mode)
        mode_dropdown = ttk.Combobox(mode_frame, textvariable=self.mode_var, 
                                    values=["hold", "toggle"], width=8, state="readonly")
        mode_dropdown.pack(side='right')
        mode_dropdown.bind('<<ComboboxSelected>>', self.change_mode)
        
        # Smoothness slider
        smooth_frame = tk.Frame(main_frame, bg='#002800')
        smooth_frame.pack(fill='x', pady=5)
        
        smooth_label = tk.Label(
            smooth_frame,
            text="Smoothness:",
            bg='#002800',
            fg='white'
        )
        smooth_label.pack(side='left')
        
        self.smooth_value = tk.Label(
            smooth_frame,
            text=f"{self.config.aimbot_smoothness:.1f}",
            bg='#002800',
            fg='white'
        )
        self.smooth_value.pack(side='right')
        
        smooth_slider = tk.Scale(
            main_frame,
            from_=1.0,
            to=10.0,
            resolution=0.1,
            orient='horizontal',
            bg='#002800',
            fg='white',
            highlightbackground='#004000',
            troughcolor='#004000',
            command=self.update_smoothness
        )
        smooth_slider.set(self.config.aimbot_smoothness)
        smooth_slider.pack(fill='x', pady=5)
        
        # FOV slider
        fov_frame = tk.Frame(main_frame, bg='#002800')
        fov_frame.pack(fill='x', pady=5)
        
        fov_label = tk.Label(
            fov_frame,
            text="FOV:",
            bg='#002800',
            fg='white'
        )
        fov_label.pack(side='left')
        
        self.fov_value = tk.Label(
            fov_frame,
            text=f"{self.config.aimbot_fov:.0f}",
            bg='#002800',
            fg='white'
        )
        self.fov_value.pack(side='right')
        
        fov_slider = tk.Scale(
            main_frame,
            from_=50.0,
            to=500.0,
            resolution=10.0,
            orient='horizontal',
            bg='#002800',
            fg='white',
            highlightbackground='#004000',
            troughcolor='#004000',
            command=self.update_fov
        )
        fov_slider.set(self.config.aimbot_fov)
        fov_slider.pack(fill='x', pady=5)
        
        # Footer
        footer_frame = tk.Frame(self.root, bg='#001800', height=60)
        footer_frame.pack(fill='x', side='bottom')
        
        hide_label = tk.Label(
            footer_frame,
            text="Press INSERT to hide",
            bg='#001800',
            fg='white',
            font=('Arial', 10)
        )
        hide_label.pack(pady=5)
        
        exit_label = tk.Label(
            footer_frame,
            text="Press + to exit",
            bg='#001800',
            fg='white',
            font=('Arial', 10, 'bold')
        )
        exit_label.pack(pady=5)
    
    def create_toggle(self, parent, text, variable, command):
        """Create a toggle button"""
        frame = tk.Frame(parent, bg='#002800')
        frame.pack(fill='x', pady=5)
        
        label = tk.Label(frame, text=text, bg='#002800', fg='white')
        label.pack(side='left')
        
        btn = tk.Button(
            frame,
            bg='#808080',
            width=2,
            height=1,
            bd=1,
            relief='raised',
            command=command
        )
        btn.pack(side='right')
        
        setattr(self, f"{text.lower().replace(' ', '_')}_btn", btn)
        self.update_toggle_button(btn, variable.get())
    
    def update_toggle_button(self, btn, state):
        """Update toggle button appearance"""
        if state:
            btn.config(bg='#00FF00')
        else:
            btn.config(bg='#808080')
    
    def toggle_setting(self, setting_name, var):
        """Toggle a setting"""
        current = var.get()
        var.set(not current)
        setattr(self.config, setting_name, not current)
        
        btn = getattr(self, f"{setting_name}_btn", None)
        if btn:
            self.update_toggle_button(btn, not current)
    
    def choose_keybind(self, bind_num):
        """Open dialog to choose keybind"""
        current = self.config.aimbot_keybind1 if bind_num == 1 else self.config.aimbot_keybind2
        new_key = tk.simpledialog.askstring(
            "Select Keybind", 
            f"Enter a key (current: {current}):\nExamples: shift, ctrl, alt, e, q, r, f, etc.",
            parent=self.root
        )
        
        if new_key and len(new_key) > 0:
            new_key = new_key.lower().strip()
            if bind_num == 1:
                self.config.aimbot_keybind1 = new_key
                self.keybind1_label.config(text=f"  {new_key}  ")
            else:
                self.config.aimbot_keybind2 = new_key
                self.keybind2_label.config(text=f"  {new_key}  ")
    
    def change_mode(self, event=None):
        """Change activation mode"""
        self.config.aimbot_activation_mode = self.mode_var.get()
    
    def update_smoothness(self, value):
        """Update smoothness value"""
        self.config.aimbot_smoothness = float(value)
        self.smooth_value.config(text=f"{float(value):.1f}")
    
    def update_fov(self, value):
        """Update FOV value"""
        self.config.aimbot_fov = float(value)
        self.fov_value.config(text=f"{float(value):.0f}")
    
    def start_move(self, event):
        """Start dragging window"""
        self.x = event.x
        self.y = event.y
    
    def on_move(self, event):
        """Handle window dragging"""
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.root.winfo_x() + deltax
        y = self.root.winfo_y() + deltay
        self.root.geometry(f"+{x}+{y}")
    
    def show_menu(self):
        """Show menu"""
        self.root.deiconify()
        self.config.menu_visible = True
    
    def hide_menu(self):
        """Hide menu"""
        self.root.withdraw()
        self.config.menu_visible = False
    
    def toggle_menu(self):
        """Toggle menu visibility"""
        if self.config.menu_visible:
            self.hide_menu()
        else:
            self.show_menu()
    
    def run(self):
        """Run menu loop"""
        if self.root:
            self.root.mainloop()
    
    def destroy(self):
        """Destroy menu"""
        if self.root:
            self.root.quit()
            self.root.destroy()


# ============================================
# MAIN APPLICATION
# ============================================

class RakeExternal:
    """Main application class"""
    
    def __init__(self):
        self.config = Config()
        self.offsets = OffsetManager()
        self.memory = RobloxMemory()
        self.aimbot = None
        self.overlay = None
        self.menu = None
        self.running = True
        self.hidden = False
        self.last_player_update = 0
        self.cached_players = []
        
    def initialize(self):
        """Initialize all components"""
        print("[*] Initializing Rake External V1.0")
        
        if not self.offsets.fetch_offsets():
            print("[-] Failed to load offsets")
            return False
        
        if not self.memory.open():
            print("[-] Failed to connect to Roblox")
            return False
        
        self.aimbot = Aimbot(self.memory, self.config)
        self.overlay = ESPOverlay(self.config)
        self.menu = MenuUI(self.config)
        
        print("[+] Initialization complete")
        return True
    
    def setup_hotkeys(self):
        """Setup keyboard hotkeys"""
        keyboard.on_press_key('+', lambda _: self.exit())
        keyboard.on_press_key('insert', lambda _: self.toggle_hide())
    
    def toggle_hide(self):
        """Toggle hide/show"""
        self.hidden = not self.hidden
        if self.hidden:
            self.overlay.hide()
            self.menu.hide_menu()
        else:
            self.overlay.show()
            self.menu.show_menu()
    
    def exit(self):
        """Exit application"""
        print("[*] Exiting...")
        self.running = False
    
    def update_players(self):
        """Update player list (called every frame)"""
        current_time = time.time()
        if current_time - self.last_player_update > 0.5:
            try:
                local_player_addr = self.memory.get_local_player()
                if local_player_addr:
                    new_players = self.memory.get_all_players(local_player_addr)
                    if len(new_players) != len(self.cached_players):
                        print(f"[!] Player count changed: {len(self.cached_players)} → {len(new_players)}")
                    self.cached_players = new_players
                    self.last_player_update = current_time
            except Exception as e:
                print(f"[-] Player update error: {e}")
    
    def main_loop(self):
        """Main application loop"""
        print("[*] Main loop started")
        
        last_update = time.time()
        update_rate = 1/60
        
        while self.running:
            try:
                current_time = time.time()
                if current_time - last_update < update_rate:
                    time.sleep(0.001)
                    continue
                
                last_update = current_time
                
                self.update_players()
                camera_obj, viewmatrix = self.memory.get_camera()
                
                local_player = None
                for p in self.cached_players:
                    if p.address == self.memory.get_local_player():
                        local_player = p
                        break
                
                if local_player and self.cached_players:
                    for player in self.cached_players:
                        if player.address != local_player.address:
                            player.distance = player.position.distance_to(local_player.position)
                    self.cached_players.sort(key=lambda p: p.distance if p.address != local_player.address else float('inf'))
                
                if self.config.aimbot_on and viewmatrix and len(self.cached_players) > 1:
                    target = self.aimbot.find_target(self.cached_players, viewmatrix, (1920, 1080))
                    if target and self.config.mouse_aimbot:
                        self.aimbot.aim_mouse(target[1])
                
                if self.overlay and not self.hidden:
                    self.overlay.update(self.cached_players, viewmatrix, local_player)
                
                if self.overlay.window:
                    pyglet.clock.tick()
                
            except Exception as e:
                print(f"[-] Error in main loop: {e}")
                time.sleep(0.1)
    
    def run(self):
        """Run the application"""
        if not self.initialize():
            input("Press Enter to exit...")
            return
        
        self.setup_hotkeys()
        
        menu_thread = threading.Thread(target=self.menu.run, daemon=True)
        menu_thread.start()
        
        overlay_thread = threading.Thread(target=self.overlay.run, daemon=True)
        overlay_thread.start()
        
        try:
            self.main_loop()
        except KeyboardInterrupt:
            print("\n[*] Interrupted by user")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Cleanup resources"""
        print("[*] Cleaning up...")
        if self.memory:
            self.memory.close()
        if self.menu:
            self.menu.destroy()
        sys.exit(0)


# ============================================
# ENTRY POINT
# ============================================

def check_admin():
    """Check if running as admin"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def main():
    """Main entry point"""
    print("""
    ╔════════════════════════════════════════╗
    ║     Rake External V1.0                 ║
    ║     Roblox ESP + Aimbot                ║
    ╚════════════════════════════════════════╝
    """)
    
    if not check_admin():
        print("[!] Not running as administrator")
        print("[!] Some features may not work properly")
    
    app = RakeExternal()
    app.run()

if __name__ == "__main__":
    main()
