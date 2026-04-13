# Fortnite External Cheat - ESP + Aimbot with PyQt5 GUI
# Python 3.11+, Requirements: pip install pyqt5 pymem numpy opencv-python pillow pywin32

import sys
import math
import ctypes
import threading
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple
from ctypes import wintypes

import pymem
import pymem.process
import win32gui
import win32api
import win32con
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import numpy as np

# ==================== STRUCTURES ====================
@dataclass
class Vector3:
    x: float
    y: float
    z: float
    
    def __sub__(self, other):
        return Vector3(self.x - other.x, self.y - other.y, self.z - other.z)
    
    def length(self):
        return math.sqrt(self.x**2 + self.y**2 + self.z**2)

@dataclass
class Vector2:
    x: float
    y: float

@dataclass
class Player:
    address: int
    position: Vector3
    head_position: Vector3
    health: float
    max_health: float
    shield: float
    distance: float
    is_visible: bool
    is_alive: bool
    name: str
    weapon: str
    team_id: int
    screen_pos: Optional[Vector2]
    head_screen_pos: Optional[Vector2]
    bone_positions: List[Vector3]

# ==================== CONFIGURATION ====================
class Config:
    # Aimbot
    aimbot_enabled: bool = True
    aimbot_visible_check: bool = True
    aimbot_fov: float = 100.0
    aimbot_smoothness: float = 5.0
    aimbot_bone: int = 0  # 0=head, 1=neck, 2=chest, 3=pelvis
    aimbot_key: int = 0x01  # VK_LBUTTON
    aimbot_draw_fov: bool = True
    
    # Triggerbot
    triggerbot_enabled: bool = False
    triggerbot_key: int = 0x04  # VK_MBUTTON
    
    # ESP
    esp_enabled: bool = True
    esp_box: bool = True
    esp_corner_box: bool = False
    esp_skeleton: bool = True
    esp_health: bool = True
    esp_shield: bool = True
    esp_distance: bool = True
    esp_name: bool = True
    esp_weapon: bool = True
    esp_snaplines: bool = False
    esp_head_circle: bool = False
    esp_tracer: bool = False
    esp_max_distance: float = 300.0
    
    # Colors (RGBA for PyQt5)
    enemy_color: Tuple[int, int, int, int] = (255, 0, 0, 255)
    enemy_visible_color: Tuple[int, int, int, int] = (255, 50, 50, 255)
    teammate_color: Tuple[int, int, int, int] = (0, 100, 255, 255)
    skeleton_color: Tuple[int, int, int, int] = (255, 255, 255, 255)
    aimbot_fov_color: Tuple[int, int, int, int] = (255, 255, 255, 100)
    crosshair_color: Tuple[int, int, int, int] = (255, 255, 255, 255)
    
    # Visuals
    show_menu: bool = True
    show_crosshair: bool = True
    
    # Misc
    no_recoil: bool = False
    no_spread: bool = False
    show_fps: bool = True

# ==================== MEMORY OFFSETS ====================
# Placeholder offsets - MUST be updated for current Fortnite version
OFFSETS = {
    'UWorld': 0x5F2FAF8,  # Example offset - UPDATE THIS
    'OwningGameInstance': 0x30,
    'LocalPlayers': 0x38,
    'PlayerController': 0x30,
    'AcknowledgedPawn': 0x3A8,
    'PlayerCameraManager': 0x3B0,
    'CameraCache': 0x1B0,
    'POV': 0x10,
    'Location': 0x00,
    'Rotation': 0x1C,
    'FOV': 0x38,
    'PersistentLevel': 0x30,
    'ActorArray': 0x98,
    'ActorCount': 0xA0,
    'RootComponent': 0x190,
    'RelativeLocation': 0x128,
    'ComponentToWorld': 0x1F0,
    'Mesh': 0x310,
    'BoneArray': 0x4E0,
    'ComponentVelocity': 0x1A0,
    'PlayerState': 0x2B0,
    'PlayerName': 0x350,
    'CurrentWeapon': 0x8C8,
    'WeaponName': 0x360,
    'Health': 0x1000,
    'MaxHealth': 0x1004,
    'Shield': 0x1008,
    'TeamIndex': 0x10E0,
    'bIsDBNO': 0x1230,
    'bIsDead': 0x1234,
}

# ==================== MEMORY MANAGER ====================
class FortniteMemory:
    def __init__(self):
        self.pm = None
        self.base_address = None
        self.process_id = None
        self.game_handle = None
        
    def attach(self):
        try:
            self.pm = pymem.Pymem("FortniteClient-Win64-Shipping.exe")
            self.base_address = pymem.process.module_from_name(self.pm.process_handle, "FortniteClient-Win64-Shipping.exe").lpBaseOfDll
            print(f"Attached to Fortnite at base: 0x{self.base_address:X}")
            return True
        except Exception as e:
            print(f"Failed to attach: {e}")
            return False
    
    def read_float(self, address):
        try:
            return self.pm.read_float(address)
        except:
            return 0.0
    
    def read_int(self, address):
        try:
            return self.pm.read_int(address)
        except:
            return 0
    
    def read_uint64(self, address):
        try:
            return self.pm.read_ulonglong(address)
        except:
            return 0
    
    def read_bytes(self, address, size):
        try:
            return self.pm.read_bytes(address, size)
        except:
            return b'\x00' * size
    
    def read_vector3(self, address):
        try:
            x = self.pm.read_float(address)
            y = self.pm.read_float(address + 4)
            z = self.pm.read_float(address + 8)
            return Vector3(x, y, z)
        except:
            return Vector3(0, 0, 0)
    
    def write_float(self, address, value):
        try:
            self.pm.write_float(address, value)
        except:
            pass
    
    def get_pointer_chain(self, base, offsets):
        addr = self.read_uint64(base)
        for offset in offsets[:-1]:
            if addr == 0:
                return 0
            addr = self.read_uint64(addr + offset)
        return addr + offsets[-1] if addr else 0

# ==================== WORLD TO SCREEN ====================
class WorldToScreen:
    def __init__(self):
        self.view_matrix = [0.0] * 16
        self.screen_width = 1920
        self.screen_height = 1080
        
    def update_matrix(self, memory: FortniteMemory, camera_manager):
        try:
            for i in range(16):
                self.view_matrix[i] = memory.read_float(camera_manager + 0x2E0 + (i * 4))
        except:
            pass
    
    def project(self, world_pos: Vector3) -> Optional[Vector2]:
        w = (self.view_matrix[12] * world_pos.x + 
             self.view_matrix[13] * world_pos.y + 
             self.view_matrix[14] * world_pos.z + 
             self.view_matrix[15])
        
        if w < 0.01:
            return None
        
        x = (self.view_matrix[0] * world_pos.x + 
             self.view_matrix[1] * world_pos.y + 
             self.view_matrix[2] * world_pos.z + 
             self.view_matrix[3])
        
        y = (self.view_matrix[4] * world_pos.x + 
             self.view_matrix[5] * world_pos.y + 
             self.view_matrix[6] * world_pos.z + 
             self.view_matrix[7])
        
        inv_w = 1.0 / w
        x *= inv_w
        y *= inv_w
        
        screen_x = (self.screen_width / 2) + (x * self.screen_width / 2)
        screen_y = (self.screen_height / 2) - (y * self.screen_height / 2)
        
        # Check screen bounds
        if (0 <= screen_x <= self.screen_width and 
            0 <= screen_y <= self.screen_height):
            return Vector2(screen_x, screen_y)
        return None

# ==================== AIMBOT ====================
class Aimbot:
    def __init__(self, memory: FortniteMemory, w2s: WorldToScreen):
        self.memory = memory
        self.w2s = w2s
        self.target = None
        
    def get_bone_position(self, player: Player, bone_index: int) -> Vector3:
        mesh = self.memory.read_uint64(player.address + OFFSETS['Mesh'])
        if not mesh:
            return player.head_position
        
        bone_array = self.memory.read_uint64(mesh + OFFSETS['BoneArray'])
        if not bone_array:
            return player.head_position
        
        bone_offset = bone_index * 48
        return self.memory.read_vector3(bone_array + bone_offset + 0x20)
    
    def calculate_fov(self, target_screen: Vector2, center: Vector2) -> float:
        dx = target_screen.x - center.x
        dy = target_screen.y - center.y
        return math.sqrt(dx*dx + dy*dy)
    
    def smooth_aim(self, target_angle: Vector2, current_angle: Vector2, smoothness: float) -> Vector2:
        delta_x = target_angle.x - current_angle.x
        delta_y = target_angle.y - current_angle.y
        
        return Vector2(
            current_angle.x + delta_x / smoothness,
            current_angle.y + delta_y / smoothness
        )
    
    def move_mouse(self, angle: Vector2):
        try:
            win32api.SetCursorPos((int(angle.x), int(angle.y)))
        except:
            pass
    
    def find_best_target(self, players: List[Player], center: Vector2) -> Optional[Player]:
        best_target = None
        best_fov = Config.aimbot_fov
        
        for player in players:
            if not player.is_alive or not player.head_screen_pos:
                continue
            if Config.aimbot_visible_check and not player.is_visible:
                continue
            
            fov = self.calculate_fov(player.head_screen_pos, center)
            if fov < best_fov:
                best_fov = fov
                best_target = player
        
        return best_target
    
    def run(self, players: List[Player], center: Vector2):
        if not Config.aimbot_enabled:
            return
        
        if not (win32api.GetAsyncKeyState(Config.aimbot_key) & 0x8000):
            return
        
        target = self.find_best_target(players, center)
        if target and target.head_screen_pos:
            self.move_mouse(target.head_screen_pos)

# ==================== ESP RENDERER ====================
class ESPRenderer(QWidget):
    def __init__(self, memory: FortniteMemory, w2s: WorldToScreen):
        super().__init__()
        self.memory = memory
        self.w2s = w2s
        self.players = []
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setWindowFlags(Qt.FramelessWindowHint | 
                          Qt.WindowStaysOnTopHint | 
                          Qt.Tool | 
                          Qt.WindowTransparentForInput)
        self.setStyleSheet("background: transparent;")
        self.last_fps_time = time.time()
        self.fps = 0
        
    def update_players(self, players):
        self.players = players
        self.update()
    
    def paintEvent(self, event):
        if not Config.esp_enabled:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Draw crosshair and FOV circle first (background)
        self.draw_crosshair(painter)
        self.draw_fov_circle(painter)
        
        # Draw players
        for player in self.players:
            if player.distance > Config.esp_max_distance:
                continue
            self.draw_player(painter, player)
    
    def draw_player(self, painter: QPainter, player: Player):
        if player.screen_pos is None or player.head_screen_pos is None:
            return
        
        # Calculate box dimensions
        height = abs(player.head_screen_pos.y - player.screen_pos.y)
        width = height * 0.6
        x = player.head_screen_pos.x - width / 2
        y = player.head_screen_pos.y
        
        # Choose color based on team and visibility
        if player.team_id == 0:  # Enemy
            color = QColor(*Config.enemy_visible_color) if player.is_visible else QColor(*Config.enemy_color)
        else:
            color = QColor(*Config.teammate_color)
        
        # Box ESP
        if Config.esp_box:
            painter.setPen(QPen(color, 2))
            painter.drawRect(int(x), int(y), int(width), int(height))
        
        # Health bar
        if Config.esp_health and player.max_health > 0:
            health_percent = min(player.health / player.max_health, 1.0)
            bar_height = height * health_percent
            bar_x = x - 8
            bar_y = y + height - bar_height
            
            painter.fillRect(int(bar_x), int(bar_y), 4, int(bar_height), QColor(0, 255, 0))
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.drawRect(int(bar_x), int(y), 4, int(height))
        
        # Shield bar
        if Config.esp_shield and player.shield > 0:
            shield_percent = min(player.shield / 100.0, 1.0)
            bar_height = height * shield_percent
            bar_x = x - 13
            bar_y = y + height - bar_height
            
            painter.fillRect(int(bar_x), int(bar_y), 4, int(bar_height), QColor(0, 100, 255))
        
        # Name
        if Config.esp_name and player.name:
            font = QFont("Arial", 10, QFont.Bold)
            painter.setFont(font)
            painter.setPen(QPen(QColor(255, 255, 255)))
            text_width = painter.fontMetrics().width(player.name)
            painter.drawText(int(x + width/2 - text_width/2), int(y - 5), player.name)
        
        # Distance
        if Config.esp_distance:
            dist_text = f"{int(player.distance)}m"
            font = QFont("Arial", 9)
            painter.setFont(font)
            painter.setPen(QPen(QColor(200, 200, 200)))
            text_width = painter.fontMetrics().width(dist_text)
            painter.drawText(int(x + width/2 - text_width/2), int(y + height + 15), dist_text)
        
        # Weapon
        if Config.esp_weapon and player.weapon:
            font = QFont("Arial", 8)
            painter.setFont(font)
            painter.setPen(QPen(QColor(255, 255, 0)))
            text_width = painter.fontMetrics().width(player.weapon)
            painter.drawText(int(x + width/2 - text_width/2), int(y + height + 28), player.weapon)
    
    def draw_crosshair(self, painter: QPainter):
        if not Config.show_crosshair:
            return
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        
        painter.setPen(QPen(QColor(*Config.crosshair_color), 1))
        painter.drawLine(int(center_x - 10), int(center_y), int(center_x + 10), int(center_y))
        painter.drawLine(int(center_x), int(center_y - 10), int(center_x), int(center_y + 10))
    
    def draw_fov_circle(self, painter: QPainter):
        if not Config.aimbot_draw_fov:
            return
        
        center_x = self.width() / 2
        center_y = self.height() / 2
        radius = Config.aimbot_fov
        
        painter.setPen(QPen(QColor(*Config.aimbot_fov_color), 2))
        painter.drawEllipse(int(center_x - radius), int(center_y - radius), 
                           int(radius * 2), int(radius * 2))

# ==================== GAME DATA MANAGER ====================
class GameDataManager:
    def __init__(self, memory: FortniteMemory, w2s: WorldToScreen):
        self.memory = memory
        self.w2s = w2s
        self.local_player = None
        
    def get_uworld(self) -> int:
        return self.memory.read_uint64(self.memory.base_address + OFFSETS['UWorld'])
    
    def get_persistent_level(self, uworld: int) -> int:
        return self.memory.read_uint64(uworld + OFFSETS['PersistentLevel'])
    
    def get_actor_array(self, level: int) -> Tuple[int, int]:
        actor_array = self.memory.read_uint64(level + OFFSETS['ActorArray'])
        actor_count = self.memory.read_int(level + OFFSETS['ActorCount'])
        return actor_array, max(0, actor_count)
    
    def get_local_player(self) -> Optional[int]:
        uworld = self.get_uworld()
        if not uworld:
            return None
        
        game_instance = self.memory.read_uint64(uworld + OFFSETS['OwningGameInstance'])
        if not game_instance:
            return None
        
        local_players = self.memory.read_uint64(game_instance + OFFSETS['LocalPlayers'])
        if not local_players:
            return None
        
        return self.memory.read_uint64(local_players)
    
    def get_player_controller(self, local_player: int) -> int:
        return self.memory.read_uint64(local_player + OFFSETS['PlayerController'])
    
    def get_camera_manager(self, player_controller: int) -> int:
        return self.memory.read_uint64(player_controller + OFFSETS['PlayerCameraManager'])
    
    def get_players(self) -> List[Player]:
        players = []
        
        uworld = self.get_uworld()
        if not uworld:
            return players
        
        level = self.get_persistent_level(uworld)
        if not level:
            return players
        
        actor_array, actor_count = self.get_actor_array(level)
        if not actor_array:
            return players
        
        local_player_addr = self.get_local_player()
        if local_player_addr:
            player_controller = self.get_player_controller(local_player_addr)
            camera_manager = self.get_camera_manager(player_controller)
            self.w2s.update_matrix(self.memory, camera_manager)
        
        for i in range(min(actor_count, 100)):
            actor = self.memory.read_uint64(actor_array + (i * 8))
            if not actor or actor == local_player_addr:
                continue
            
            root_component = self.memory.read_uint64(actor + OFFSETS['RootComponent'])
            if not root_component:
                continue
            
            position = self.memory.read_vector3(root_component + OFFSETS['RelativeLocation'])
            health = self.memory.read_float(actor + OFFSETS['Health'])
            
            if health <= 0:
                continue
            
            player = Player(
                address=actor,
                position=position,
                head_position=position,  # Will be updated with bone pos later
                health=health,
                max_health=100.0,
                shield=self.memory.read_float(actor + OFFSETS['Shield']),
                distance=0.0,
                is_visible=True,
                is_alive=health > 0,
                name="Player",
                weapon="Unknown",
                team_id=self.memory.read_int(actor + OFFSETS['TeamIndex']),
                screen_pos=None,
                head_screen_pos=None,
                bone_positions=[]
            )
            
            # World to screen
            screen_pos = self.w2s.project(player.position)
            if screen_pos:
                player.screen_pos = screen_pos
            
            # Calculate distance from local player
            if local_player_addr:
                local_root = self.memory.read_uint64(local_player_addr + OFFSETS['RootComponent'])
                if local_root:
                    local_pos = self.memory.read_vector3(local_root + OFFSETS['RelativeLocation'])
                    player.distance = (player.position - local_pos).length()
            
            players.append(player)
        
        return players

# ==================== MAIN WINDOW ====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.memory = FortniteMemory()
        self.w2s = WorldToScreen()
        self.game_data = GameDataManager(self.memory, self.w2s)
        self.aimbot = Aimbot(self.memory, self.w2s)
        self.running = False
        
        self.init_ui()
        self.init_overlay()
        
    def init_ui(self):
        self.setWindowTitle("Fortnite External Cheat")
        self.setGeometry(100, 100, 400, 500)
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        # Tabs
        tabs = QTabWidget()
        self.create_aimbot_tab(tabs)
        self.create_esp_tab(tabs)
        self.create_visuals_tab(tabs)
        self.create_misc_tab(tabs)
        
        layout.addWidget(tabs)
        
        # Status bar
        self.status_label = QLabel("Status: Idle")
        self.statusBar().addPermanentWidget(self.status_label)
        
        # Connect button
        connect_btn = QPushButton("Connect to Fortnite")
        connect_btn.clicked.connect(self.toggle_game)
        layout.addWidget(connect_btn)
    
    def create_aimbot_tab(self, tabs):
        aimbot_tab = QWidget()
        layout = QVBoxLayout(aimbot_tab)
        
        self.aimbot_check = QCheckBox("Enable Aimbot")
        self.aimbot_check.setChecked(Config.aimbot_enabled)
        self.aimbot_check.toggled.connect(lambda v: setattr(Config, 'aimbot_enabled', v))
        
        self.visible_check = QCheckBox("Visible Check")
        self.visible_check.setChecked(Config.aimbot_visible_check)
        self.visible_check.toggled.connect(lambda v: setattr(Config, 'aimbot_visible_check', v))
        
        fov_layout = QHBoxLayout()
        fov_layout.addWidget(QLabel("FOV:"))
        self.fov_slider = QSlider(Qt.Horizontal)
        self.fov_slider.setRange(10, 360)
        self.fov_slider.setValue(int(Config.aimbot_fov))
        self.fov_slider.valueChanged.connect(lambda v: setattr(Config, 'aimbot_fov', float(v)))
        fov_layout.addWidget(self.fov_slider)
        fov_layout.addWidget(QLabel("100"))
        
        smooth_layout = QHBoxLayout()
        smooth_layout.addWidget(QLabel("Smooth:"))
        self.smooth_slider = QSlider(Qt.Horizontal)
        self.smooth_slider.setRange(1, 20)
        self.smooth_slider.setValue(int(Config.aimbot_smoothness))
        self.smooth_slider.valueChanged.connect(lambda v: setattr(Config, 'aimbot_smoothness', float(v)))
        smooth_layout.addWidget(self.smooth_slider)
        
        self.bone_combo = QComboBox()
        self.bone_combo.addItems(["Head", "Neck", "Chest", "Pelvis"])
        self.bone_combo.currentIndexChanged.connect(lambda i: setattr(Config, 'aimbot_bone', i))
        
        layout.addWidget(self.aimbot_check)
        layout.addWidget(self.visible_check)
        layout.addLayout(fov_layout)
        layout.addLayout(smooth_layout)
        layout.addWidget(QLabel("Target Bone:"))
        layout.addWidget(self.bone_combo)
        layout.addStretch()
        
        tabs.addTab(aimbot_tab, "Aimbot")
    
    def create_esp_tab(self, tabs):
        esp_tab = QWidget()
        layout = QVBoxLayout(esp_tab)
        
        self.esp_check = QCheckBox("Enable ESP")
        self.esp_check.setChecked(Config.esp_enabled)
        self.esp_check.toggled.connect(lambda v: setattr(Config, 'esp_enabled', v))
        
        self.box_check = QCheckBox("Box ESP")
        self.box_check.setChecked(True)
        self.box_check.toggled.connect(lambda v: setattr(Config, 'esp_box', v))
        
        self.skeleton_check = QCheckBox("Skeleton")
        self.skeleton_check.setChecked(Config.esp_skeleton)
        self.skeleton_check.toggled.connect(lambda v: setattr(Config, 'esp_skeleton', v))
        
        self.health_check = QCheckBox("Health Bar")
        self.health_check.setChecked(True)
        self.health_check.toggled.connect(lambda v: setattr(Config, 'esp_health', v))
        
        self.distance_check = QCheckBox("Distance")
        self.distance_check.setChecked(True)
        self.distance_check.toggled.connect(lambda v: setattr(Config, 'esp_distance', v))
        
        layout.addWidget(self.esp_check)
        layout.addWidget(self.box_check)
        layout.addWidget(self.skeleton_check)
        layout.addWidget(self.health_check)
        layout.addWidget(self.distance_check)
        layout.addStretch()
        
        tabs.addTab(esp_tab, "ESP")
    
    def create_visuals_tab(self, tabs):
        visuals_tab = QWidget()
        layout = QVBoxLayout(visuals_tab)
        
        self.crosshair_check = QCheckBox("Show Crosshair")
        self.crosshair_check.setChecked(True)
        self.crosshair_check.toggled.connect(lambda v: setattr(Config, 'show_crosshair', v))
        
        self.fov_circle_check = QCheckBox("Show FOV Circle")
        self.fov_circle_check.setChecked(True)
        self.fov_circle_check.toggled.connect(lambda v: setattr(Config, 'aimbot_draw_fov', v))
        
        layout.addWidget(self.crosshair_check)
        layout.addWidget(self.fov_circle_check)
        layout.addStretch()
        
        tabs.addTab(visuals_tab, "Visuals")
    
    def create_misc_tab(self, tabs):
        misc_tab = QWidget()
        layout = QVBoxLayout(misc_tab)
        
        self.triggerbot_check = QCheckBox("Triggerbot")
        self.triggerbot_check.setChecked(False)
        self.triggerbot_check.toggled.connect(lambda v: setattr(Config, 'triggerbot_enabled', v))
        
        layout.addWidget(self.triggerbot_check)
        layout.addStretch()
        
        tabs.addTab(misc_tab, "Misc")
    
    def init_overlay(self):
        screen = QApplication.primaryScreen().geometry()
        self.w2s.screen_width = screen.width()
        self.w2s.screen_height = screen.height()
        
        self.overlay = ESPRenderer(self.memory, self.w2s)
        self.overlay.resize(self.w2s.screen_width, self.w2s.screen_height)
        self.overlay.move(0, 0)
        self.overlay.show()
    
    def toggle_game(self):
        if not self.memory.pm:
            if self.memory.attach():
                self.status_label.setText("Status: Connected ✓")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
                self.running = True
                self.game_thread = threading.Thread(target=self.game_loop, daemon=True)
                self.game_thread.start()
            else:
                self.status_label.setText("Status: Failed to connect")
                self.status_label.setStyleSheet("color: red;")
        else:
            self.running = False
            self.status_label.setText("Status: Disconnected")
            self.status_label.setStyleSheet("color: orange;")
    
    def game_loop(self):
        while self.running and self.memory.pm:
            try:
                players = self.game_data.get_players()
                self.overlay.update_players(players)
                
                center = Vector2(self.w2s.screen_width / 2, self.w2s.screen_height / 2)
                self.aimbot.run(players, center)
            except:
                pass
            
            time.sleep(0.016)  # ~60 FPS

# ==================== ENTRY POINT ====================
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    # Dark theme
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(45, 45, 48))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 28))
    palette.setColor(QPalette.AlternateBase, QColor(35, 35, 38))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
