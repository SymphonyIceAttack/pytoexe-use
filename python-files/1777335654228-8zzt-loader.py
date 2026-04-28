# ???????????????????????????? IMPORTS ????????????????????????????
import sys
import os
import time
import threading
import random
import string
from math import sqrt, pi
from ctypes import windll, byref, Structure, wintypes
import ctypes
import msvcrt
import requests
import binascii, secrets
from numpy import array, float32, linalg, cross, dot, reshape, empty, einsum
# Removed external dependency on high_pop_optimizer; provide lightweight inline replacements
class _HPOPT:
    @staticmethod
    def sample_children(children_full, limit=64):
        try:
            if not children_full:
                return []
            # simple slice to cap work; avoids external optimizer
            return list(children_full)[: int(limit or 64)]
        except Exception:
            return []

    @staticmethod
    def prioritize_players(info_list, W, H, budget=32):
        try:
            n = min(int(budget or 32), len(info_list) if info_list else 0)
            return list(range(n))
        except Exception:
            return []

    @staticmethod
    def note_screen(head, sp):
        # no-op; kept for API compatibility
        return None

HPOPT = _HPOPT
from struct import unpack_from
try:
    import dearpygui.dearpygui as dpg
    from requests import get
    from pymem import Pymem
    from pymem.process import list_processes
    from pymem.exception import ProcessError
    from psutil import pid_exists
    import json
    from PyQt5.QtWidgets import QApplication, QOpenGLWidget
    from PyQt5.QtCore import Qt, QTimer
    from PyQt5.QtGui import QColor, QPainter, QImage
    from OpenGL.GL import *
    DEPS_OK = True
except ImportError as e:
    print(f"Missing dependency: {e}")
    input("Press Enter to exit...")
    sys.exit(1)


pi180 = pi/180
Handle = None
PID = -1
baseAddr = None
pm = Pymem()
aimbot_enabled = False
aimbot_keybind = 2
aimbot_mode = "Hold"

# Silent Aim (separate from Combat) — flick to target on left click
silent_aim_enabled = False
silent_aim_ignoreteam = False
silent_aim_ignoredead = False
silent_aim_hitpart = "Head"
silent_use_fov_enabled = True
silent_show_fov_enabled = False
silent_follow_fov_enabled = False
silent_fov_circle_radius = 150.0
silent_fov_circle_color = [0.0, 0.8, 1.0]
silent_fov_outline_enabled = False
silent_fov_outline_color = [0.0, 0.0, 0.0]
silent_fov_line_thickness = 2.0
aimbot_toggled = False
waiting_for_keybind = False
injected = False
aimbot_smoothness_enabled = False
aimbot_smoothness_value = 0.1
aimbot_ignoreteam = False
aimbot_ignoredead = False
aimbot_hitpart = "Head"
aimbot_prediction_enabled = False
aimbot_prediction_x = 0.1
aimbot_prediction_y = 0.1
aimbot_fov = 50.0
aimbot_hard_lock = True
esp_enabled = False
esp_ignoreteam = False
esp_ignoredead = False
esp_box_enabled = False
esp_box_filled = False
esp_box_fill_color = [1.0, 1.0, 1.0]
esp_box_fill_alpha = 0.2
esp_skeleton_enabled = False
esp_skeleton_color = [1.0, 1.0, 1.0]
esp_tracers_enabled = True  # global flag for tracer lines
aimbot_shake_enabled = False
aimbot_shake_strength = 0.005
sticky_aim_enabled = False  # prefer keeping current target when enabled
triggerbot_enabled = False
triggerbot_keybind = 1
triggerbot_mode = "Hold"
triggerbot_toggled = False
triggerbot_delay = 0
triggerbot_prediction_x = 0.1
triggerbot_prediction_y = 0.1
triggerbot_fov = 50.0
walkspeed_gui_enabled = False
walkspeed_gui_value = 16
walkspeed_gui_thread = None
walkspeed_gui_active = False
jump_power_enabled = False
jump_power_value = 50
jump_power_thread = None
jump_power_active = False
infinite_jump_enabled = False
god_mode_enabled = False
fly_enabled = False
fly_speed = 50.0
fly_thread = None
fly_active = False
fly_keybind = 0x46  # 'F' default
god_mode_thread = None
god_mode_active = False
fov_changer_enabled = False
fov_value = 70.0
fov_thread = None
fov_active = False
dataModel = 0
wsAddr = 0
camAddr = 0
camCFrameRotAddr = 0
plrsAddr = 0
lpAddr = 0
matrixAddr = 0
camPosAddr = 0
target = 0
nameOffset = 0
childrenOffset = 0
VK_CODES = {
    'Left Mouse': 1, 'Right Mouse': 2, 'Middle Mouse': 4,
    'F1': 112, 'F2': 113, 'F3': 114, 'F4': 115, 'F5': 116, 'F6': 117,
    'A': 65, 'B': 66, 'C': 67, 'D': 68, 'E': 69, 'F': 70,
    'Shift': 16, 'Ctrl': 17, 'Alt': 18, 'Space': 32
}

# Global FPS control (affects GUI loop, aimbot, triggerbot, ESP)
custom_fps_enabled = True
global_fps = 360
esp_timer = None

def get_frame_interval():
    f = int(global_fps)
    if not custom_fps_enabled:
        f = 60
    f = max(1, min(360, f))
    return 1.0 / float(f)


# -*- coding: utf-8 -*-
from ctypes import Structure, wintypes

class RECT(Structure):
    _fields_ = [('left', wintypes.LONG), ('top', wintypes.LONG), ('right', wintypes.LONG), ('bottom', wintypes.LONG)]

class POINT(Structure):
    _fields_ = [('x', wintypes.LONG), ('y', wintypes.LONG)]

class OPENFILENAME(Structure):
    _fields_ = [
        ('lStructSize', wintypes.DWORD),
        ('hwndOwner', wintypes.HWND),
        ('hInstance', wintypes.HINSTANCE),
        ('lpstrFilter', wintypes.LPCWSTR),
        ('lpstrCustomFilter', wintypes.LPWSTR),
        ('nMaxCustFilter', wintypes.DWORD),
        ('nFilterIndex', wintypes.DWORD),
        ('lpstrFile', wintypes.LPWSTR),
        ('nMaxFile', wintypes.DWORD),
        ('lpstrFileTitle', wintypes.LPWSTR),
        ('nMaxFileTitle', wintypes.DWORD),
        ('lpstrInitialDir', wintypes.LPCWSTR),
        ('lpstrTitle', wintypes.LPCWSTR),
        ('Flags', wintypes.DWORD),
        ('nFileOffset', wintypes.WORD),
        ('nFileExtension', wintypes.WORD),
        ('lpstrDefExt', wintypes.LPCWSTR),
        ('lCustData', wintypes.LPARAM),
        ('lpfnHook', wintypes.LPVOID),
        ('lpTemplateName', wintypes.LPCWSTR),
        ('pvReserved', wintypes.LPVOID),
        ('dwReserved', wintypes.DWORD),
        ('FlagsEx', wintypes.DWORD)
    ]

# ???????????????????????????? CORE FUNCTIONS ????????????????????????????
def get_key_name(vk_code):
    for name, code in VK_CODES.items():
        if code == vk_code:
            return name
    return f"Key {vk_code}"
def DRP(address):
    if isinstance(address, str):
        address = int(address, 16)
    try:
        return int.from_bytes(pm.read_bytes(address, 8), "little")
    except Exception as e:
        print(f"[ERROR] DRP failed at address {hex(address)}: {e}")
        return 0
def simple_get_processes():
    return [{"Name": i.szExeFile.decode(), "ProcessId": i.th32ProcessID} for i in list_processes()]
def yield_for_program(program_name, printInfo=True):
    global PID, Handle, baseAddr, pm
    for proc in simple_get_processes():
        if proc["Name"] == program_name:
            try:
                pm.open_process_from_id(proc["ProcessId"])
                PID = proc["ProcessId"]
                Handle = windll.kernel32.OpenProcess(0x1038, False, PID)
                for module in pm.list_modules():
                    if module.name == "RobloxPlayerBeta.exe":
                        baseAddr = module.lpBaseOfDll
                        break
                if printInfo:
                    print(f"[INFO] Found Roblox process: PID={PID}, BaseAddr={hex(baseAddr)}")
                return True
            except Exception as e:
                print(f"[ERROR] Failed to open process {proc['Name']}: {e}")
    return False
def is_process_dead():
    return not pid_exists(PID)
def get_base_addr():
    return baseAddr
def setOffsets(nameOffset2, childrenOffset2):
    global nameOffset, childrenOffset
    nameOffset = nameOffset2
    childrenOffset = childrenOffset2
def ReadRobloxString(expected_address):
    try:
        string_count = pm.read_int(expected_address + 0x10)
        if string_count > 15:
            ptr = DRP(expected_address)
            return pm.read_string(ptr, string_count)
        return pm.read_string(expected_address, string_count)
    except Exception as e:
        print(f"[ERROR] ReadRobloxString failed at {hex(expected_address)}: {e}")
        return ""
def GetClassName(instance):
    try:
        ptr = pm.read_longlong(instance + 0x18)
        ptr = pm.read_longlong(ptr + 0x8)
        fl = pm.read_longlong(ptr + 0x18)
        if fl == 0x1F:
            ptr = pm.read_longlong(ptr)
        return ReadRobloxString(ptr)
    except Exception as e:
        print(f"[ERROR] GetClassName failed at {hex(instance)}: {e}")
        return ""
def GetName(instance):
    try:
        return ReadRobloxString(DRP(instance + nameOffset))
    except Exception as e:
        print(f"[ERROR] GetName failed at {hex(instance)}: {e}")
        return ""
def GetChildren(instance):
    if not instance:
        return []
    children = []
    try:
        start = DRP(instance + childrenOffset)
        if start == 0:
            return []
        end = DRP(start + 8)
        current = DRP(start)
        for _ in range(1000):
            if current == end:
                break
            children.append(pm.read_longlong(current))
            current += 0x10
    except Exception as e:
        print(f"[ERROR] GetChildren failed at {hex(instance)}: {e}")
    return children
def FindFirstChild(instance, child_name):
    if not instance:
        return 0
    try:
        start = DRP(instance + childrenOffset)
        if start == 0:
            return 0
        end = DRP(start + 8)
        current = DRP(start)
        for _ in range(1000):
            if current == end:
                break
            child = pm.read_longlong(current)
            try:
                if GetName(child) == child_name:
                    return child
            except:
                pass
            current += 0x10
    except Exception as e:
        print(f"[ERROR] FindFirstChild failed at {hex(instance)} for {child_name}: {e}")
    return 0
def FindFirstChildOfClass(instance, class_name):
    if not instance:
        return 0
    try:
        start = DRP(instance + childrenOffset)
        if start == 0:
            return 0
        end = DRP(start + 8)
        current = DRP(start)
        for _ in range(1000):
            if current == end:
                break
            child = pm.read_longlong(current)
            try:
                if GetClassName(child) == class_name:
                    return child
            except:
                pass
            current += 0x10
    except Exception as e:
        print(f"[ERROR] FindFirstChildOfClass failed at {hex(instance)} for {class_name}: {e}")
    return 0
def find_window_by_title(title):
    return windll.user32.FindWindowW(None, title)
def get_client_rect_on_screen(hwnd):
    rect = RECT()
    if windll.user32.GetClientRect(hwnd, byref(rect)) == 0:
        return 0, 0, 0, 0
    top_left = POINT(rect.left, rect.top)
    bottom_right = POINT(rect.right, rect.bottom)
    windll.user32.ClientToScreen(hwnd, byref(top_left))
    windll.user32.ClientToScreen(hwnd, byref(bottom_right))
    return top_left.x, top_left.y, bottom_right.x, bottom_right.y
def normalize(vec):
    norm = linalg.norm(vec)
    return vec / norm if norm != 0 else vec
def cframe_look_at(from_pos, to_pos):
    from_pos = array(from_pos, dtype=float32)
    to_pos = array(to_pos, dtype=float32)
    look_vector = normalize(to_pos - from_pos)
    up_vector = array([0, 1, 0], dtype=float32)
    if abs(look_vector[1]) > 0.999:
        up_vector = array([0, 0, -1], dtype=float32)
    right_vector = normalize(cross(up_vector, look_vector))
    recalculated_up = cross(look_vector, right_vector)
    return look_vector, recalculated_up, right_vector
def world_to_screen_with_matrix(world_pos, matrix, screen_width, screen_height):
    try:
        vec = array([*world_pos, 1.0], dtype=float32)
        clip = dot(matrix, vec)
        if clip[3] == 0:
            return None
        ndc = clip[:3] / clip[3]
        # Accept depth in [-1, 1] to avoid flicker due to different clip-space conventions
        if ndc[2] < -1.0 or ndc[2] > 1.0:
            return None
        x = (ndc[0] + 1) * 0.5 * screen_width
        y = (1 - ndc[1]) * 0.5 * screen_height
        return round(x), round(y)
    except Exception as e:
        print(f"[ERROR] world_to_screen_with_matrix failed: {e}")
        return None
def title_changer():
    while True:
        try:
            dpg.configure_item("Primary Window", label="Lithua")
            dpg.set_viewport_title("Lithua")
        except:
            pass
        time.sleep(1)

# ???????????????????????????? INITIALIZATION ????????????????????????????
def background_process_monitor():
    global baseAddr
    while True:
        if is_process_dead():
            while not yield_for_program("RobloxPlayerBeta.exe"):
                time.sleep(0.5)
            baseAddr = get_base_addr()
        time.sleep(0.1)
threading.Thread(target=background_process_monitor, daemon=True).start()
def init():
    global dataModel, wsAddr, camAddr, camCFrameRotAddr, plrsAddr, lpAddr, matrixAddr, camPosAddr, injected
    try:
        fakeDatamodel = pm.read_longlong(baseAddr + int(offsets['FakeDataModelPointer'], 16))
        dataModel = pm.read_longlong(fakeDatamodel + int(offsets['FakeDataModelToDataModel'], 16))
        wsAddr = pm.read_longlong(dataModel + int(offsets['Workspace'], 16))
        camAddr = pm.read_longlong(wsAddr + int(offsets['Camera'], 16))
        camCFrameRotAddr = camAddr + int(offsets['CameraRotation'], 16)
        camPosAddr = camAddr + int(offsets['CameraPos'], 16)
        visualEngine = pm.read_longlong(baseAddr + int(offsets['VisualEnginePointer'], 16))
        matrixAddr = visualEngine + int(offsets['viewmatrix'], 16)
        plrsAddr = FindFirstChildOfClass(dataModel, 'Players')
        lpAddr = pm.read_longlong(plrsAddr + int(offsets['LocalPlayer'], 16))
        print(f"[INFO] Initialized: DataModel={hex(dataModel)}, Workspace={hex(wsAddr)}, Camera={hex(camAddr)}, Players={hex(plrsAddr)}, LocalPlayer={hex(lpAddr)}")
        injected = True
        threading.Thread(target=delayed_show, daemon=True).start()
    except ProcessError as e:
        print(f'[ERROR] You forgot to open Roblox! Error: {e}')
    except Exception as e:
        print(f'[ERROR] Initialization failed: {e}')
def keybind_listener():
    global waiting_for_keybind, aimbot_keybind, triggerbot_keybind
    while True:
        if waiting_for_keybind:
            time.sleep(0.3)
            for vk_code in range(1, 256):
                windll.user32.GetAsyncKeyState(vk_code)
            key_found = False
            while waiting_for_keybind and not key_found:
                for vk_code in range(1, 256):
                    if windll.user32.GetAsyncKeyState(vk_code) & 0x8000:
                        if vk_code == 27:  # ESC
                            waiting_for_keybind = False
                            try:
                                dpg.configure_item("keybind_button", label=f"Keybind: {get_key_name(aimbot_keybind)} ({aimbot_mode})")
                            except:
                                pass
                            try:
                                dpg.configure_item("triggerbot_keybind_button", label=f"Keybind: {get_key_name(triggerbot_keybind)} ({triggerbot_mode})")
                            except:
                                pass
                            break
                        try:
                            current_label = dpg.get_item_label("keybind_button")
                            if "..." in current_label:
                                aimbot_keybind = vk_code
                                dpg.configure_item("keybind_button", label=f"Keybind: {get_key_name(vk_code)} ({aimbot_mode})")
                        except:
                            pass
                        try:
                            current_label = dpg.get_item_label("triggerbot_keybind_button")
                            if "..." in current_label:
                                triggerbot_keybind = vk_code
                                dpg.configure_item("triggerbot_keybind_button", label=f"Keybind: {get_key_name(vk_code)} ({triggerbot_mode})")
                        except:
                            pass
                        waiting_for_keybind = False
                        key_found = True
                        break
                time.sleep(0.01)
        else:
            time.sleep(0.1)
threading.Thread(target=keybind_listener, daemon=True).start()
def get_workspace_addr():
    try:
        a = pm.read_longlong(baseAddr + int(offsets["VisualEnginePointer"], 16))
        b = pm.read_longlong(a + int(offsets["VisualEngineToDataModel1"], 16))
        c = pm.read_longlong(b + int(offsets["VisualEngineToDataModel2"], 16))
        workspace = pm.read_longlong(c + int(offsets["Workspace"], 16))
        return workspace
    except Exception as e:
        print(f"[ERROR] get_workspace_addr failed: {e}")
        return None
bot_target = 0
def find_bot_target():
    global bot_target
    bots_folder = pm.read_longlong(wsAddr + int(offsets['Children'], 16))
    min_dist = float('inf')
    chosen_bot = 0
    if bots_folder:
        for bot in GetChildren(bots_folder):
            hrp = FindFirstChild(bot, 'HumanoidRootPart')
            hum = FindFirstChildOfClass(bot, 'Humanoid')
            if hrp and hum:
                try:
                    health = pm.read_float(hum + int(offsets['Health'], 16))
                    if aimbot_ignoredead and health <= 0:
                        continue
                    primitive = pm.read_longlong(hrp + int(offsets['Primitive'], 16))
                    pos_addr = primitive + int(offsets['Position'], 16)
                    chosen_bot = pos_addr
                    break
                except Exception as e:
                    print(f"[ERROR] find_bot_target failed for bot: {e}")
    bot_target = chosen_bot
import math
import random
import time
import threading
from ctypes import windll
from struct import unpack_from
from numpy import array, reshape, float32

# Smoothing with natural easing
def ease_out_quad(t):
    return 1 - (1 - t) * (1 - t)

def ease_in_out_cubic(t):
    if t < 0.5:
        return 4 * t * t * t
    else:
        return 1 - pow(-2 * t + 2, 3) / 2

def smooth_lerp(current, target, speed, ease_func=ease_out_quad):
    """Smooth interpolation with easing"""
    if speed >= 1.0:
        return target
    t = ease_func(speed)
    return current + (target - current) * t

# Target tracking with history
class TargetManager:
    def __init__(self):
        self.locked_target = 0
        self.lock_frames = 0
        self.last_screen_pos = None
        self.lost_sight_frames = 0
        
    def update_lock(self, target_addr, screen_pos=None):
        if target_addr == self.locked_target and target_addr != 0:
            self.lock_frames += 1
            self.lost_sight_frames = 0
        else:
            if target_addr != 0:
                self.locked_target = target_addr
                self.lock_frames = 0
            self.lost_sight_frames += 1
        
        self.last_screen_pos = screen_pos
        
        # Release lock after losing sight
        if self.lost_sight_frames > 15:
            self.reset()
    
    def should_keep_lock(self):
        return self.lock_frames > 0 and self.lock_frames < 120
    
    def reset(self):
        self.locked_target = 0
        self.lock_frames = 0
        self.lost_sight_frames = 0
        self.last_screen_pos = None

target_manager = TargetManager()

def get_workspace_addr():
    try:
        a = pm.read_longlong(baseAddr + int(offsets["VisualEnginePointer"], 16))
        b = pm.read_longlong(a + int(offsets["VisualEngineToDataModel1"], 16))
        c = pm.read_longlong(b + int(offsets["VisualEngineToDataModel2"], 16))
        workspace = pm.read_longlong(c + int(offsets["Workspace"], 16))
        return workspace
    except Exception as e:
        print(f"[ERROR] get_workspace_addr failed: {e}")
        return None

def aimbotLoop():
    global target, aimbot_toggled, locked_target
    key_pressed_last_frame = False
    
    # Smoothing state
    last_look = [0, 0, 0]
    last_up = [0, 0, 0]
    last_right = [0, 0, 0]
    initialized = False
    
    # Saved screen pos for mouse method
    best_screen_pos = None
    
    while True:
        loop_start = time.time()
        if aimbot_enabled:
            key_pressed_this_frame = windll.user32.GetAsyncKeyState(aimbot_keybind) & 0x8000 != 0
            
            if aimbot_mode == "Toggle":
                if key_pressed_this_frame and not key_pressed_last_frame:
                    aimbot_toggled = not aimbot_toggled
                should_aim = aimbot_toggled
            else:
                should_aim = key_pressed_this_frame
            
            key_pressed_last_frame = key_pressed_this_frame
            
            if should_aim and matrixAddr > 0:
                hwnd_roblox = find_window_by_title("Roblox")
                if not hwnd_roblox:
                    time.sleep(0.01)
                    continue
                
                left, top, right, bottom = get_client_rect_on_screen(hwnd_roblox)
                width, height = right - left, bottom - top
                
                try:
                    matrixRaw = pm.read_bytes(matrixAddr, 64)
                    view_proj_matrix = reshape(array(unpack_from("<16f", matrixRaw, 0), dtype=float32), (4, 4))
                except Exception as e:
                    print(f"[ERROR] Matrix read failed: {e}")
                    time.sleep(0.01)
                    continue
                
                lpTeam = pm.read_longlong(lpAddr + int(offsets['Team'], 16))
                center_x, center_y = width / 2, height / 2
                
                min_dist = float('inf')
                best_target = 0
                best_target_pos = None
                best_target_screen = None
                found_current_target = False
                
                def process_character(char):
                    nonlocal min_dist, best_target, best_target_pos, best_target_screen, found_current_target
                    
                    hitpart = FindFirstChild(char, aimbot_hitpart)
                    hum = FindFirstChildOfClass(char, 'Humanoid')
                    
                    if not hitpart or not hum:
                        return
                    
                    try:
                        health = pm.read_float(hum + int(offsets['Health'], 16))
                        if aimbot_ignoredead and health <= 0:
                            return
                        
                        primitive = pm.read_longlong(hitpart + int(offsets['Primitive'], 16))
                        targetPos = primitive + int(offsets['Position'], 16)
                        
                        # Read base position
                        base_x = pm.read_float(targetPos)
                        base_y = pm.read_float(targetPos + 4)
                        base_z = pm.read_float(targetPos + 8)
                        
                        # Apply prediction with YOUR multipliers
                        if aimbot_prediction_enabled:
                            try:
                                vel_x = pm.read_float(primitive + int(offsets['Velocity'], 16))
                                vel_y = pm.read_float(primitive + int(offsets['Velocity'], 16) + 4)
                                vel_z = pm.read_float(primitive + int(offsets['Velocity'], 16) + 8)
                                
                                # Use your GUI values directly
                                base_x += vel_x * aimbot_prediction_x
                                base_y += vel_y * aimbot_prediction_y
                                base_z += vel_z * aimbot_prediction_x  # Z uses X multiplier typically
                                
                            except Exception:
                                pass
                        
                        obj_pos = array([base_x, base_y, base_z], dtype=float32)
                        
                        screen_coords = world_to_screen_with_matrix(obj_pos, view_proj_matrix, width, height)
                        
                        if screen_coords is not None:
                            dist = math.sqrt((center_x - screen_coords[0])**2 + (center_y - screen_coords[1])**2)
                            
                            # Check if this is our locked target
                            if targetPos == target_manager.locked_target:
                                found_current_target = True
                                # Prioritize locked target with expanded FOV
                                if dist <= aimbot_fov * 1.5:
                                    min_dist = dist
                                    best_target = targetPos
                                    best_target_pos = obj_pos
                                    return
                            
                        # Sticky aim: if enabled and we have a locked target, ignore other targets
                            if sticky_aim_enabled and target_manager.locked_target not in (0, targetPos):
                                return
                            # Regular target selection
                            if dist < min_dist and ((not globals().get('use_fov_enabled', True)) or dist <= aimbot_fov):
                                min_dist = dist
                                best_target = targetPos
                                best_target_pos = obj_pos
                                best_target_screen = screen_coords
                    
                    except Exception as e:
                        print(f"[ERROR] process_character: {e}")
                
                # Scan targets
                children_full = GetChildren(plrsAddr)
                for v in HPOPT.sample_children(children_full, limit=64):
                    if v == lpAddr:
                        continue
                    
                    team = pm.read_longlong(v + int(offsets['Team'], 16))
                    if aimbot_ignoreteam and team == lpTeam:
                        continue
                    
                    char = pm.read_longlong(v + int(offsets['ModelInstance'], 16))
                    if not char:
                        continue
                    
                    process_character(char)
                
                # Check bots/dummies
                workspaceAddr = get_workspace_addr()
                if workspaceAddr:
                    bots_folder = FindFirstChild(workspaceAddr, "Bots") or FindFirstChild(workspaceAddr, "Dummies")
                    if bots_folder:
                        for bot in GetChildren(bots_folder):
                            hrp = FindFirstChild(bot, "HumanoidRootPart")
                            if hrp:
                                process_character(bot)
                
                # Update target manager
                if best_target != 0:
                    target_manager.update_lock(best_target)
                elif not found_current_target:
                    target_manager.update_lock(0)
                
                target = target_manager.locked_target
                locked_target = target
                best_screen_pos = best_target_screen
                
                # Aim at target with hard lock or smoothing
                if target > 0:
                    try:
                        from_pos = [pm.read_float(camPosAddr + i * 4) for i in range(3)]
                        to_pos = [pm.read_float(target + i * 4) for i in range(3)]
                        
                        # If method is Mouse, move cursor to target screen point instead of camera write
                        if globals().get('aim_method','Camera') == 'Mouse':
                            hwnd_roblox = find_window_by_title('Roblox')
                            if hwnd_roblox and best_screen_pos:
                                left, top, right, bottom = get_client_rect_on_screen(hwnd_roblox)
                                windll.user32.SetCursorPos(int(left+best_screen_pos[0]), int(top+best_screen_pos[1]))
                            time.sleep(0.001)
                            continue
                        
                        if globals().get('aimbot_hard_lock', True):
                            look, up, right = cframe_look_at(from_pos, to_pos)
                            for i in range(3):
                                pm.write_float(camCFrameRotAddr + i * 12, float(-right[i]))
                                pm.write_float(camCFrameRotAddr + 4 + i * 12, float(up[i]))
                                pm.write_float(camCFrameRotAddr + 8 + i * 12, float(-look[i]))
                            initialized = True
                        else:
                            # legacy smooth mode
                            dx = to_pos[0] - from_pos[0]
                            dy = to_pos[1] - from_pos[1]
                            dz = to_pos[2] - from_pos[2]
                            distance = math.sqrt(dx*dx + dy*dy + dz*dz)
                            look, up, right = cframe_look_at(from_pos, to_pos)
                            if not initialized:
                                last_look = look
                                last_up = up
                                last_right = right
                                initialized = True
                            if aimbot_smoothness_enabled:
                                base_speed = 1.0 - ((aimbot_smoothness_value - 100) / 400.0)
                                base_speed = max(0.05, min(base_speed, 1.0))
                                distance_factor = min(distance / 150.0, 1.0)
                                adaptive_speed = base_speed * (1.0 + distance_factor * 0.3)
                                adaptive_speed = min(adaptive_speed, 1.0)
                            else:
                                adaptive_speed = 1.0
                            smooth_look = [smooth_lerp(last_look[i], look[i], adaptive_speed, ease_in_out_cubic) for i in range(3)]
                            smooth_up = [smooth_lerp(last_up[i], up[i], adaptive_speed, ease_in_out_cubic) for i in range(3)]
                            smooth_right = [smooth_lerp(last_right[i], right[i], adaptive_speed, ease_in_out_cubic) for i in range(3)]
                            for i in range(3):
                                pm.write_float(camCFrameRotAddr + i * 12, float(-smooth_right[i]))
                                pm.write_float(camCFrameRotAddr + 4 + i * 12, float(smooth_up[i]))
                                pm.write_float(camCFrameRotAddr + 8 + i * 12, float(-smooth_look[i]))
                            last_look = smooth_look
                            last_up = smooth_up
                            last_right = smooth_right
                    
                    except Exception as e:
                        print(f"[ERROR] Camera write failed: {e}")
                        target_manager.reset()
                        initialized = False
            else:
                target = 0
                locked_target = 0
                target_manager.reset()
                initialized = False
        else:
            aimbot_toggled = False
            target_manager.reset()
            initialized = False
        
        # Frame pacing
        elapsed = time.time() - loop_start
        time.sleep(max(get_frame_interval() - elapsed, 0.0005))

# Start aimbot thread
threading.Thread(target=aimbotLoop, daemon=True).start()
def triggerbotLoop():
    global triggerbot_enabled, triggerbot_toggled
    key_pressed_last_frame = False
    last_shot_time = 0
    
    while True:
        loop_start = time.time()
        if triggerbot_enabled and injected and lpAddr > 0 and plrsAddr > 0 and matrixAddr > 0:
            try:
                current_time = time.time()
                hwnd_roblox = find_window_by_title("Roblox")
                if not hwnd_roblox:
                    time.sleep(0.05)
                    continue
                
                left, top, right, bottom = get_client_rect_on_screen(hwnd_roblox)
                width = right - left
                height = bottom - top
                
                if width <= 0 or height <= 0:
                    time.sleep(0.05)
                    continue
                
                widthCenter = width / 2.0
                heightCenter = height / 2.0
                
                # Read matrix
                try:
                    matrixRaw = pm.read_bytes(matrixAddr, 64)
                    view_proj_matrix = reshape(array(unpack_from("<16f", matrixRaw, 0), dtype=float32), (4, 4))
                except Exception:
                    time.sleep(0.01)
                    continue
                
                key_pressed_this_frame = windll.user32.GetAsyncKeyState(triggerbot_keybind) & 0x8000 != 0
                
                if triggerbot_mode == "Toggle":
                    if key_pressed_this_frame and not key_pressed_last_frame:
                        triggerbot_toggled = not triggerbot_toggled
                    key_pressed_last_frame = key_pressed_this_frame
                    should_trigger = triggerbot_toggled
                else:
                    should_trigger = key_pressed_this_frame
                
                if should_trigger:
                    try:
                        lpTeam = pm.read_longlong(lpAddr + int(offsets['Team'], 16))
                    except Exception:
                        lpTeam = 0
                    
                    best_target = None
                    min_distance = float('inf')
                    
                    def safe_process_target(char):
                        nonlocal best_target, min_distance
                        
                        if not char or char == 0:
                            return
                        
                        try:
                            # Get head part - with validation
                            head = FindFirstChild(char, 'Head')
                            if not head or head == 0:
                                return
                            
                            # Check if alive
                            if aimbot_ignoredead:
                                hum = FindFirstChildOfClass(char, 'Humanoid')
                                if hum and hum != 0:
                                    try:
                                        health = pm.read_float(hum + int(offsets['Health'], 16))
                                        if health <= 0:
                                            return
                                    except Exception:
                                        pass
                            
                            # Get primitive
                            primitive = pm.read_longlong(head + int(offsets['Primitive'], 16))
                            if not primitive or primitive == 0:
                                return
                            
                            # Read position
                            targetPos = primitive + int(offsets['Position'], 16)
                            target_world_pos = array([
                                pm.read_float(targetPos),
                                pm.read_float(targetPos + 4),
                                pm.read_float(targetPos + 8)
                            ], dtype=float32)
                            
                            # Sanity check on position values
                            if abs(target_world_pos[0]) > 100000 or abs(target_world_pos[1]) > 100000 or abs(target_world_pos[2]) > 100000:
                                return
                            
                            # Apply prediction if enabled
                            if triggerbot_prediction_x > 0 or triggerbot_prediction_y > 0:
                                try:
                                    vel_addr = primitive + int(offsets['Velocity'], 16)
                                    velocity = array([
                                        pm.read_float(vel_addr),
                                        pm.read_float(vel_addr + 4),
                                        pm.read_float(vel_addr + 8)
                                    ], dtype=float32)
                                    
                                    # Sanity check velocity
                                    if abs(velocity[0]) < 1000 and abs(velocity[1]) < 1000 and abs(velocity[2]) < 1000:
                                        target_world_pos[0] += velocity[0] * triggerbot_prediction_x
                                        target_world_pos[1] += velocity[1] * triggerbot_prediction_y
                                        target_world_pos[2] += velocity[2] * triggerbot_prediction_x
                                except Exception:
                                    pass
                            
                            # Convert to screen
                            screen_coords = world_to_screen_with_matrix(target_world_pos, view_proj_matrix, width, height)
                            if screen_coords is None:
                                return
                            
                            # Check screen bounds
                            if screen_coords[0] < 0 or screen_coords[0] > width or screen_coords[1] < 0 or screen_coords[1] > height:
                                return
                            
                            # Calculate distance from center
                            screen_dist = sqrt(
                                (widthCenter - screen_coords[0]) ** 2 +
                                (heightCenter - screen_coords[1]) ** 2
                            )
                            
                            # Must be within FOV
                            if screen_dist > triggerbot_fov:
                                return
                            
                            # Select closest to center
                            if screen_dist < min_distance:
                                min_distance = screen_dist
                                best_target = {
                                    'screen_dist': screen_dist,
                                    'screen_pos': screen_coords
                                }
                        
                        except Exception:
                            # Silently skip invalid targets
                            pass
                    
                    # Process all players - with extra safety
                    try:
                        children = GetChildren(plrsAddr)
                        if children:
                            for v in children:
                                if not v or v == 0 or v == lpAddr:
                                    continue
                                
                                try:
                                    # Team check
                                    if aimbot_ignoreteam and lpTeam != 0:
                                        playerTeam = pm.read_longlong(v + int(offsets['Team'], 16))
                                        if playerTeam == lpTeam:
                                            continue
                                    
                                    # Get character
                                    char = pm.read_longlong(v + int(offsets['ModelInstance'], 16))
                                    if char and char != 0:
                                        safe_process_target(char)
                                except Exception:
                                    continue
                    except Exception:
                        pass
                    
                    # Process bots - with extra safety
                    try:
                        workspaceAddr = get_workspace_addr()
                        if workspaceAddr and workspaceAddr != 0:
                            bots_folder = None
                            try:
                                bots_folder = FindFirstChild(workspaceAddr, "Bots")
                                if not bots_folder or bots_folder == 0:
                                    bots_folder = FindFirstChild(workspaceAddr, "Dummies")
                            except Exception:
                                pass
                            
                            if bots_folder and bots_folder != 0:
                                try:
                                    bot_children = GetChildren(bots_folder)
                                    if bot_children:
                                        for bot in bot_children:
                                            if bot and bot != 0:
                                                safe_process_target(bot)
                                except Exception:
                                    pass
                    except Exception:
                        pass
                    
                    # Fire if we have a valid target
                    if best_target and (current_time - last_shot_time) >= (triggerbot_delay / 1000.0):
                        # Must be very close to center
                        if best_target['screen_dist'] <= 15:  # Within 15 pixels
                            windll.user32.mouse_event(0x0002, 0, 0, 0, 0)
                            time.sleep(0.001)
                            windll.user32.mouse_event(0x0004, 0, 0, 0, 0)
                            last_shot_time = current_time
                else:
                    if triggerbot_mode == "Hold":
                        triggerbot_toggled = False
                        
            except Exception as e:
                # Only print actual errors, not memory read failures
                if "triggerbot" in str(e).lower():
                    print(f"[ERROR] triggerbotLoop: {e}")
                time.sleep(0.05)
        else:
            time.sleep(0.01)
        
        # Frame pacing
        elapsed = time.time() - loop_start
        time.sleep(max(get_frame_interval() - elapsed, 0.0005))

threading.Thread(target=triggerbotLoop, daemon=True).start()

# ???????????????????????????? GUI CALLBACKS ????????????????????????????
def aimbot_callback(sender, app_data):
    global aimbot_enabled, aimbot_toggled
    if not injected:
        return
    aimbot_enabled = app_data
    if not app_data:
        aimbot_toggled = False
def esp_callback(sender, app_data):
    global esp_enabled, esp_enabled_flag
    if not injected:
        return
    esp_enabled = app_data
    esp_enabled_flag = app_data
    if esp_enabled:
        start_esp_overlay()
    else:
        # Only hide overlay if nothing else is using it (e.g., FOV)
        if not (globals().get('show_fov_enabled', False) or globals().get('silent_show_fov_enabled', False)):
            stop_esp_overlay()
        else:
            esp_enabled_flag = False
def esp_box_callback(sender, app_data):
    global esp_box_enabled
    esp_box_enabled = app_data
def esp_ignoreteam_callback(sender, app_data):
    global esp_ignoreteam
    esp_ignoreteam = app_data
def esp_ignoredead_callback(sender, app_data):
    global esp_ignoredead
    esp_ignoredead = app_data
def aimbot_ignoreteam_callback(sender, app_data):
    global aimbot_ignoreteam
    aimbot_ignoreteam = app_data
def aimbot_ignoredead_callback(sender, app_data):
    global aimbot_ignoredead
    aimbot_ignoredead = app_data
def aimbot_mode_callback(sender, app_data):
    global aimbot_mode, aimbot_toggled
    aimbot_mode = app_data
    dpg.configure_item("keybind_button", label=f"Keybind: {get_key_name(aimbot_keybind)} ({aimbot_mode})")
    if aimbot_mode == "Hold":
        aimbot_toggled = False
def aimbot_smoothness_callback(sender, app_data):
    global aimbot_smoothness_enabled
    aimbot_smoothness_enabled = app_data
    if app_data:
        dpg.show_item("smoothness_slider")
    else:
        dpg.hide_item("smoothness_slider")
def smoothness_value_callback(sender, app_data):
    global aimbot_smoothness_value
    aimbot_smoothness_value = app_data
def aimbot_fov_callback(sender, app_data):
    global aimbot_fov
    aimbot_fov = app_data
def keybind_callback():
    global waiting_for_keybind
    if not waiting_for_keybind:
        waiting_for_keybind = True
        dpg.configure_item("keybind_button", label="... (ESC to cancel)")
def aimbot_mode_menu_callback(sender, app_data):
    aimbot_mode_callback(sender, app_data)
def inject_callback():
    init()
def get_camera_addr_gui():
    try:
        a = pm.read_longlong(baseAddr + int(offsets["VisualEnginePointer"], 16))
        b = pm.read_longlong(a + int(offsets["VisualEngineToDataModel1"], 16))
        c = pm.read_longlong(b + int(offsets["VisualEngineToDataModel2"], 16))
        d = pm.read_longlong(c + int(offsets["Workspace"], 16))
        return pm.read_longlong(d + int(offsets["Camera"], 16))
    except Exception as e:
        print(f"[ERROR] get_camera_addr_gui failed: {e}")
        return None
def walkspeed_gui_loop():
    global walkspeed_gui_active
    while walkspeed_gui_active:
        try:
            if walkspeed_gui_enabled:
                cam_addr = get_camera_addr_gui()
                if cam_addr:
                    h = pm.read_longlong(cam_addr + int(offsets["CameraSubject"], 16))
                    pm.write_float(h + int(offsets["WalkSpeedCheck"], 16), float('inf'))
                    pm.write_float(h + int(offsets["WalkSpeed"], 16), float(walkspeed_gui_value))
            time.sleep(0.1)
        except Exception as e:
            print(f"[ERROR] walkspeed_gui_loop failed: {e}")
            time.sleep(0.1)
def jump_power_loop():
    global jump_power_active
    while jump_power_active:
        try:
            if jump_power_enabled:
                cam_addr = get_camera_addr_gui()
                if cam_addr:
                    h = pm.read_longlong(cam_addr + int(offsets["CameraSubject"], 16))
                    pm.write_float(h + int(offsets["JumpPower"], 16), float(jump_power_value))
            time.sleep(0.1)
        except Exception as e:
            print(f"[ERROR] jump_power_loop failed: {e}")
            time.sleep(0.1)
def fly_loop():
    global fly_active
    last = time.perf_counter()
    while fly_active:
        try:
            if not fly_enabled:
                time.sleep(0.02)
                last = time.perf_counter()
                continue
            char = pm.read_longlong(lpAddr + int(offsets['ModelInstance'], 16))
            if not char:
                time.sleep(0.02)
                continue
            hrp = FindFirstChild(char, 'HumanoidRootPart')
            if not hrp:
                time.sleep(0.02)
                continue
            primitive = pm.read_longlong(hrp + int(offsets['Primitive'], 16))
            if not primitive:
                time.sleep(0.02)
                continue
            pos_addr = primitive + int(offsets['Position'], 16)
            # dt
            now = time.perf_counter(); dt = max(0.001, now - last); last = now
            # keys
            w = windll.user32.GetAsyncKeyState(0x57) & 0x8000  # W
            s = windll.user32.GetAsyncKeyState(0x53) & 0x8000  # S
            a = windll.user32.GetAsyncKeyState(0x41) & 0x8000  # A
            d = windll.user32.GetAsyncKeyState(0x44) & 0x8000  # D
            up = windll.user32.GetAsyncKeyState(0x20) & 0x8000 # Space
            down = windll.user32.GetAsyncKeyState(0x11) & 0x8000 # Ctrl
            speed = float(fly_speed)
            vx = (-1 if a else 0) + (1 if d else 0)
            vz = (-1 if w else 0) + (1 if s else 0)
            vy = (1 if up else 0) + (-1 if down else 0)
            if vx==vz==vy==0:
                time.sleep(0.01)
                continue
            # normalize
            mag = (vx*vx + vy*vy + vz*vz) ** 0.5
            if mag>0:
                vx/=mag; vy/=mag; vz/=mag
            # move
            pm.write_float(pos_addr,     pm.read_float(pos_addr)     + vx*speed*dt)
            pm.write_float(pos_addr + 4, pm.read_float(pos_addr + 4) + vy*speed*dt)
            pm.write_float(pos_addr + 8, pm.read_float(pos_addr + 8) + vz*speed*dt)
            # zero velocity to avoid physics counter-force
            try:
                vel_offset = primitive + int(offsets['Velocity'], 16)
                pm.write_float(vel_offset, 0.0)
                pm.write_float(vel_offset + 4, 0.0)
                pm.write_float(vel_offset + 8, 0.0)
            except Exception:
                pass
            time.sleep(0.001)
        except Exception:
            time.sleep(0.05)
def infinite_jump_loop():
    # Force upward velocity when space is held, allows infinite jumps without relying on a 'Jump' flag
    while infinite_jump_enabled:
        try:
            if windll.user32.GetAsyncKeyState(0x20) & 0x8000:  # Space
                char = pm.read_longlong(lpAddr + int(offsets['ModelInstance'], 16))
                if char:
                    hrp = FindFirstChild(char, 'HumanoidRootPart')
                    if hrp:
                        primitive = pm.read_longlong(hrp + int(offsets['Primitive'], 16))
                        if primitive:
                            vel_addr = primitive + int(offsets['Velocity'], 16)
                            # set vertical velocity to jump_power_value for an instant boost
                            pm.write_float(vel_addr + 4, float(max(25.0, jump_power_value)))
            time.sleep(0.01)
        except Exception:
            time.sleep(0.05)
def god_mode_loop():
    global god_mode_active, god_mode_enabled
    while god_mode_active:
        try:
            if god_mode_enabled:
                char = pm.read_longlong(lpAddr + int(offsets['ModelInstance'], 16))
                if char:
                    hum = FindFirstChildOfClass(char, 'Humanoid')
                    if hum:
                        try:
                            pm.write_float(hum + int(offsets['MaxHealth'], 16), float('inf'))
                        except Exception:
                            pass
                        pm.write_float(hum + int(offsets['Health'], 16), float('inf'))
            time.sleep(0.05)
        except Exception:
            time.sleep(0.1)
def fov_changer_loop():
    global fov_active
    while fov_active:
        try:
            if fov_changer_enabled:
                if camAddr:
                    pm.write_float(camAddr + int(offsets['FieldOfView'], 16), fov_value)  # Assuming 'FieldOfView' offset
            time.sleep(0.1)
        except Exception as e:
            print(f"[ERROR] fov_changer_loop failed: {e}")
            time.sleep(0.1)
def walkspeed_gui_toggle(sender, state):
    global walkspeed_gui_enabled, walkspeed_gui_active, walkspeed_gui_thread
    walkspeed_gui_enabled = state
    dpg.configure_item("walkspeed_gui_slider", show=state)
    if state and not walkspeed_gui_active:
        walkspeed_gui_active = True
        walkspeed_gui_thread = threading.Thread(target=walkspeed_gui_loop, daemon=True)
        walkspeed_gui_thread.start()
    if not state and walkspeed_gui_active:
        walkspeed_gui_active = False
def walkspeed_gui_change(sender, value):
    global walkspeed_gui_value
    walkspeed_gui_value = value
def jump_power_toggle(sender, state):
    global jump_power_enabled, jump_power_active, jump_power_thread
    jump_power_enabled = state
    dpg.configure_item("jump_power_slider", show=state)
    if state and not jump_power_active:
        jump_power_active = True
        jump_power_thread = threading.Thread(target=jump_power_loop, daemon=True)
        jump_power_thread.start()
    if not state and jump_power_active:
        jump_power_active = False
def jump_power_change(sender, value):
    global jump_power_value
    jump_power_value = value
def fly_toggle(sender, state):
    global fly_enabled, fly_active, fly_thread
    fly_enabled = state
    dpg.configure_item("fly_slider", show=state)
    if state and not fly_active:
        fly_active = True
        fly_thread = threading.Thread(target=fly_loop, daemon=True)
        fly_thread.start()
    if not state and fly_active:
        fly_active = False
def fly_change(sender, value):
    global fly_speed
    fly_speed = value
def infinite_jump_toggle(sender, state):
    global infinite_jump_enabled
    infinite_jump_enabled = state
    if state:
        threading.Thread(target=infinite_jump_loop, daemon=True).start()
def god_mode_toggle(sender, state):
    global god_mode_enabled, god_mode_active, god_mode_thread
    god_mode_enabled = state
    if state and not god_mode_active:
        god_mode_active = True
        god_mode_thread = threading.Thread(target=god_mode_loop, daemon=True)
        god_mode_thread.start()
    if not state and god_mode_active:
        god_mode_active = False
def fov_changer_toggle(sender, state):
    global fov_changer_enabled, fov_active, fov_thread
    fov_changer_enabled = state
    dpg.configure_item("fov_slider", show=state)
    if state and not fov_active:
        fov_active = True
        fov_thread = threading.Thread(target=fov_changer_loop, daemon=True)
        fov_thread.start()
    if not state and fov_active:
        fov_active = False
def fov_change(sender, value):
    global fov_value
    fov_value = value
def delayed_show():
    time.sleep(1)
    show_main_features()
# DPG guard (no-op when running ImGui)
USE_DPG=False

def show_main_features():
    if not USE_DPG:
        return
    dpg.show_item("aimbot_group")
    dpg.show_item("aimbot_smoothness_checkbox")
    dpg.show_item("aimbot_ignoreteam_checkbox")
    dpg.show_item("aimbot_ignoredead_checkbox")
    dpg.show_item("aimbot_fov_slider")
    dpg.show_item("walkspeed_gui_checkbox")
    dpg.show_item("jump_power_checkbox")
    dpg.show_item("fly_checkbox")
    dpg.show_item("infinite_jump_checkbox")
    dpg.show_item("god_mode_checkbox")
    dpg.show_item("fov_changer_checkbox")
    dpg.show_item("aimbot_hitpart_combo")
    dpg.show_item("aimbot_prediction_checkbox")
    dpg.show_item("aimbot_shake_checkbox")
    if aimbot_shake_enabled:
        dpg.show_item("aimbot_shake_slider")
    if aimbot_prediction_enabled:
        dpg.show_item("prediction_x_slider")
        dpg.show_item("prediction_y_slider")
    dpg.show_item("triggerbot_checkbox")
    dpg.show_item("triggerbot_keybind_button")
    dpg.show_item("triggerbot_delay_slider")
    dpg.show_item("triggerbot_prediction_x_slider")
    dpg.show_item("triggerbot_prediction_y_slider")
    dpg.show_item("triggerbot_fov_slider")
def aimbot_hitpart_callback(sender, app_data):
    global aimbot_hitpart
    aimbot_hitpart = app_data
def aimbot_prediction_checkbox(sender, app_data):
    global aimbot_prediction_enabled
    aimbot_prediction_enabled = app_data
    dpg.configure_item("prediction_x_slider", show=app_data)
    dpg.configure_item("prediction_y_slider", show=app_data)
def prediction_x_callback(sender, app_data):
    global aimbot_prediction_x
    aimbot_prediction_x = app_data
def prediction_y_callback(sender, app_data):
    global aimbot_prediction_y
    aimbot_prediction_y = app_data
def aimbot_shake_callback(sender, app_data):
    global aimbot_shake_enabled
    aimbot_shake_enabled = app_data
    dpg.configure_item("aimbot_shake_slider", show=app_data)
def aimbot_shake_strength_callback(sender, app_data):
    global aimbot_shake_strength
    aimbot_shake_strength = app_data
def triggerbot_callback(sender, app_data):
    global triggerbot_enabled, triggerbot_toggled
    if not injected:
        return
    triggerbot_enabled = app_data
    if not app_data:
        triggerbot_toggled = False
def triggerbot_mode_callback(sender, app_data):
    global triggerbot_mode, triggerbot_toggled
    triggerbot_mode = app_data
    dpg.configure_item("triggerbot_keybind_button", label=f"Keybind: {get_key_name(triggerbot_keybind)} ({triggerbot_mode})")
    if triggerbot_mode == "Hold":
        triggerbot_toggled = False
def triggerbot_keybind_callback():
    global waiting_for_keybind
    if not waiting_for_keybind:
        waiting_for_keybind = True
        dpg.configure_item("triggerbot_keybind_button", label="... (ESC to cancel)")
def triggerbot_mode_menu_callback(sender, app_data):
    triggerbot_mode_callback(sender, app_data)
def triggerbot_delay_callback(sender, app_data):
    global triggerbot_delay
    triggerbot_delay = app_data
def triggerbot_prediction_x_callback(sender, app_data):
    global triggerbot_prediction_x
    triggerbot_prediction_x = app_data
def triggerbot_prediction_y_callback(sender, app_data):
    global triggerbot_prediction_y
    triggerbot_prediction_y = app_data
def triggerbot_fov_callback(sender, app_data):
    global triggerbot_fov
    triggerbot_fov = app_data
def get_configs_directory():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    configs_dir = os.path.join(script_dir, "configs")
    if not os.path.exists(configs_dir):
        os.makedirs(configs_dir)
    return configs_dir
def windows_save_file_dialog():
    try:
        configs_dir = get_configs_directory()
        filename_buffer = ctypes.create_unicode_buffer(260)
        initial_path = os.path.join(configs_dir, "config.json")
        filename_buffer.value = initial_path
        ofn = OPENFILENAME()
        ofn.lStructSize = ctypes.sizeof(OPENFILENAME)
        ofn.hwndOwner = None
        ofn.lpstrFilter = "JSON Files\0*.json\0All Files\0*.*\0"
        ofn.lpstrFile = ctypes.cast(filename_buffer, wintypes.LPWSTR)
        ofn.nMaxFile = 260
        ofn.lpstrInitialDir = configs_dir
        ofn.lpstrTitle = "Save Config"
        ofn.lpstrDefExt = "json"
        ofn.Flags = 0x00000002 | 0x00000004
        if windll.comdlg32.GetSaveFileNameW(byref(ofn)):
            selected_path = filename_buffer.value
            if not selected_path.startswith(configs_dir):
                filename = os.path.basename(selected_path)
                selected_path = os.path.join(configs_dir, filename)
            return selected_path
        return None
    except Exception as e:
        print(f"Error in save dialog: {e}")
        return None
def windows_open_file_dialog():
    try:
        configs_dir = get_configs_directory()
        filename_buffer = ctypes.create_unicode_buffer(260)
        ofn = OPENFILENAME()
        ofn.lStructSize = ctypes.sizeof(OPENFILENAME)
        ofn.hwndOwner = None
        ofn.lpstrFilter = "JSON Files\0*.json\0All Files\0*.*\0"
        ofn.lpstrFile = ctypes.cast(filename_buffer, wintypes.LPWSTR)
        ofn.nMaxFile = 260
        ofn.lpstrInitialDir = configs_dir
        ofn.lpstrTitle = "Load Config"
        ofn.Flags = 0x00001000 | 0x00000004
        if windll.comdlg32.GetOpenFileNameW(byref(ofn)):
            return filename_buffer.value
        return None
    except Exception as e:
        print(f"Error in open dialog: {e}")
        return None

def windows_open_png_dialog():
    try:
        filename_buffer = ctypes.create_unicode_buffer(260)
        ofn = OPENFILENAME()
        ofn.lStructSize = ctypes.sizeof(OPENFILENAME)
        ofn.hwndOwner = None
        ofn.lpstrFilter = "PNG Files\0*.png\0All Files\0*.*\0"
        ofn.lpstrFile = ctypes.cast(filename_buffer, wintypes.LPWSTR)
        ofn.nMaxFile = 260
        ofn.lpstrTitle = "Load Preview PNG"
        ofn.Flags = 0x00001000 | 0x00000004
        if windll.comdlg32.GetOpenFileNameW(byref(ofn)):
            return filename_buffer.value
        return None
    except Exception as e:
        print(f"Error in PNG open dialog: {e}")
        return None

def _create_gl_texture_from_rgba(data: bytes, w: int, h: int) -> int:
    try:
        tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        gl.glTexImage2D(gl.GL_TEXTURE_2D, 0, gl.GL_RGBA, w, h, 0, gl.GL_RGBA, gl.GL_UNSIGNED_BYTE, data)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        return int(tex)
    except Exception as e:
        print(f"Texture create failed: {e}")
        return 0

def load_esp_preview_image(path: str) -> bool:
    try:
        # Try with Qt first (available)
        img = QImage(path)
        if img.isNull():
            try:
                from PIL import Image as _PILImage  # fallback
                pil = _PILImage.open(path).convert('RGBA')
                data = pil.tobytes()
                w, h = pil.size
            except Exception as e:
                print(f"Failed to load image: {e}")
                return False
        else:
            img = img.convertToFormat(QImage.Format_RGBA8888)
            w, h = img.width(), img.height()
            bits = img.bits(); bits.setsize(w*h*4)
            data = bytes(bits)
        # Replace existing texture
        tex_old = int(globals().get('esp_preview_tex', 0) or 0)
        if tex_old:
            try:
                gl.glDeleteTextures(int(tex_old))
            except Exception:
                pass
        tex = _create_gl_texture_from_rgba(data, w, h)
        if not tex:
            return False
        globals()['esp_preview_tex'] = tex
        globals()['esp_preview_size'] = (w, h)
        globals()['esp_preview_image_path'] = path
        globals()['esp_preview_use_image'] = True
        return True
    except Exception as e:
        print(f"load_esp_preview_image error: {e}")
        return False

def try_load_default_preview():
    # Look for a PNG automatically; prefer your Assets folder
    try:
        base = os.path.dirname(os.path.abspath(__file__))
        assets_abs = r"C:\Users\borey\source\repos\AetherNew\Assets"
        candidates = [
            os.path.join(assets_abs, 'esp_preview.png'),
            os.path.join(base, 'Assets', 'esp_preview.png'),
            os.path.join(base, 'assets', 'esp_preview.png'),
            os.path.join(base, 'resources', 'esp_preview.png'),
            os.path.join(base, 'esp_preview.png')
        ]
        for p in candidates:
            if p and os.path.exists(p) and load_esp_preview_image(p):
                print(f"[INFO] Loaded preview PNG: {p}")
                return True
        # Fallback: any PNG in Assets folder
        try:
            scan_dirs = [assets_abs, os.path.join(base, 'Assets'), base]
            for d in scan_dirs:
                if not os.path.isdir(d):
                    continue
                names = [f for f in os.listdir(d) if f.lower().endswith('.png')]
                names.sort(key=lambda s: (0 if ('preview' in s.lower() or 'roblox' in s.lower()) else 1, s.lower()))
                for n in names:
                    p = os.path.join(d, n)
                    if load_esp_preview_image(p):
                        print(f"[INFO] Loaded fallback preview PNG: {p}")
                        return True
        except Exception:
            pass
        return False
    except Exception:
        return False
def save_config_callback():
    try:
        file_path = windows_save_file_dialog()
        if file_path:
            config_data = {
                "aimbot": {
                    "enabled": aimbot_enabled,
                    "keybind": aimbot_keybind,
                    "mode": aimbot_mode,
                    "hitpart": aimbot_hitpart,
                    "ignoreteam": aimbot_ignoreteam,
                    "ignoredead": aimbot_ignoredead,
                    "fov": aimbot_fov
                },
                "prediction": {
                    "enabled": aimbot_prediction_enabled,
                    "x": aimbot_prediction_x,
                    "y": aimbot_prediction_y
                },
                "smoothness": {
                    "enabled": aimbot_smoothness_enabled,
                    "value": aimbot_smoothness_value
                },
                "shake": {
                    "enabled": aimbot_shake_enabled,
                    "strength": aimbot_shake_strength
                },
                "triggerbot": {
                    "enabled": triggerbot_enabled,
                    "keybind": triggerbot_keybind,
                    "mode": triggerbot_mode,
                    "delay": triggerbot_delay,
                    "prediction_x": triggerbot_prediction_x,
                    "prediction_y": triggerbot_prediction_y,
                    "fov": triggerbot_fov
                },
                "esp": {
                    "enabled": esp_enabled,
                    "ignoreteam": esp_ignoreteam,
                    "ignoredead": esp_ignoredead,
                    "box_enabled": esp_box_enabled
                },
                "walkspeed": {
                    "enabled": walkspeed_gui_enabled,
                    "value": walkspeed_gui_value
                },
                "jump_power": {
                    "enabled": jump_power_enabled,
                    "value": jump_power_value
                },
                "fly": {
                    "enabled": fly_enabled,
                    "speed": fly_speed
                },
                "infinite_jump": {
                    "enabled": infinite_jump_enabled
                },
                "god_mode": {
                    "enabled": god_mode_enabled
                },
                "fov_changer": {
                    "enabled": fov_changer_enabled,
                    "value": fov_value
                }
            }
            with open(file_path, 'w') as f:
                json.dump(config_data, f, indent=4)
            print(f"Config saved to: {file_path}")
    except Exception as e:
        print(f"Error saving config: {e}")
def load_config_callback():
    try:
        file_path = windows_open_file_dialog()
        if file_path:
            with open(file_path, 'r') as f:
                config_data = json.load(f)
            if "aimbot" in config_data:
                aimbot_config = config_data["aimbot"]
                global aimbot_enabled, aimbot_keybind, aimbot_mode, aimbot_hitpart, aimbot_ignoreteam, aimbot_ignoredead, aimbot_fov
                if "enabled" in aimbot_config:
                    aimbot_enabled = aimbot_config["enabled"]
                    dpg.set_value("aimbot_checkbox", aimbot_enabled)
                if "keybind" in aimbot_config:
                    aimbot_keybind = aimbot_config["keybind"]
                    dpg.configure_item("keybind_button", label=f"Keybind: {get_key_name(aimbot_keybind)} ({aimbot_mode})")
                if "mode" in aimbot_config:
                    aimbot_mode = aimbot_config["mode"]
                    dpg.configure_item("keybind_button", label=f"Keybind: {get_key_name(aimbot_keybind)} ({aimbot_mode})")
                if "hitpart" in aimbot_config:
                    aimbot_hitpart = aimbot_config["hitpart"]
                    dpg.set_value("aimbot_hitpart_combo", aimbot_hitpart)
                if "ignoreteam" in aimbot_config:
                    aimbot_ignoreteam = aimbot_config["ignoreteam"]
                    dpg.set_value("aimbot_ignoreteam_checkbox", aimbot_ignoreteam)
                if "ignoredead" in aimbot_config:
                    aimbot_ignoredead = aimbot_config["ignoredead"]
                    dpg.set_value("aimbot_ignoredead_checkbox", aimbot_ignoredead)
                if "fov" in aimbot_config:
                    aimbot_fov = aimbot_config["fov"]
                    dpg.set_value("aimbot_fov_slider", aimbot_fov)
            if "prediction" in config_data:
                prediction_config = config_data["prediction"]
                global aimbot_prediction_enabled, aimbot_prediction_x, aimbot_prediction_y
                if "enabled" in prediction_config:
                    aimbot_prediction_enabled = prediction_config["enabled"]
                    dpg.set_value("aimbot_prediction_checkbox", aimbot_prediction_enabled)
                    dpg.configure_item("prediction_x_slider", show=aimbot_prediction_enabled)
                    dpg.configure_item("prediction_y_slider", show=aimbot_prediction_enabled)
                if "x" in prediction_config:
                    aimbot_prediction_x = prediction_config["x"]
                    dpg.set_value("prediction_x_slider", aimbot_prediction_x)
                if "y" in prediction_config:
                    aimbot_prediction_y = prediction_config["y"]
                    dpg.set_value("prediction_y_slider", aimbot_prediction_y)
            if "smoothness" in config_data:
                smoothness_config = config_data["smoothness"]
                global aimbot_smoothness_enabled, aimbot_smoothness_value
                if "enabled" in smoothness_config:
                    aimbot_smoothness_enabled = smoothness_config["enabled"]
                    dpg.set_value("aimbot_smoothness_checkbox", aimbot_smoothness_enabled)
                    dpg.configure_item("smoothness_slider", show=aimbot_smoothness_enabled)
                if "value" in smoothness_config:
                    aimbot_smoothness_value = smoothness_config["value"]
                    dpg.set_value("smoothness_slider", aimbot_smoothness_value)
            if "shake" in config_data:
                shake_config = config_data["shake"]
                global aimbot_shake_enabled, aimbot_shake_strength
                if "enabled" in shake_config:
                    aimbot_shake_enabled = shake_config["enabled"]
                    dpg.set_value("aimbot_shake_checkbox", aimbot_shake_enabled)
                    dpg.configure_item("aimbot_shake_slider", show=aimbot_shake_enabled)
                if "strength" in shake_config:
                    aimbot_shake_strength = shake_config["strength"]
                    dpg.set_value("aimbot_shake_slider", aimbot_shake_strength)
            if "esp" in config_data:
                esp_config = config_data["esp"]
                global esp_enabled, esp_ignoreteam, esp_ignoredead, esp_box_enabled
                if "enabled" in esp_config:
                    esp_enabled = esp_config["enabled"]
                    esp_enabled_flag = esp_enabled
                    dpg.set_value("esp_checkbox", esp_enabled)
                    if esp_enabled:
                        start_esp_overlay()
                if "ignoreteam" in esp_config:
                    esp_ignoreteam = esp_config["ignoreteam"]
                    dpg.set_value("esp_ignoreteam_checkbox", esp_ignoreteam)
                if "ignoredead" in esp_config:
                    esp_ignoredead = esp_config["ignoredead"]
                    dpg.set_value("esp_ignoredead_checkbox", esp_ignoredead)
                if "box_enabled" in esp_config:
                    esp_box_enabled = esp_config["box_enabled"]
                    dpg.set_value("esp_box_checkbox", esp_box_enabled)
            if "triggerbot" in config_data:
                triggerbot_config = config_data["triggerbot"]
                global triggerbot_enabled, triggerbot_keybind, triggerbot_mode, triggerbot_delay, triggerbot_prediction_x, triggerbot_prediction_y, triggerbot_fov
                if "enabled" in triggerbot_config:
                    triggerbot_enabled = triggerbot_config["enabled"]
                    dpg.set_value("triggerbot_checkbox", triggerbot_enabled)
                if "keybind" in triggerbot_config:
                    triggerbot_keybind = triggerbot_config["keybind"]
                    dpg.configure_item("triggerbot_keybind_button", label=f"Keybind: {get_key_name(triggerbot_keybind)} ({triggerbot_mode})")
                if "mode" in triggerbot_config:
                    triggerbot_mode = triggerbot_config["mode"]
                    dpg.configure_item("triggerbot_keybind_button", label=f"Keybind: {get_key_name(triggerbot_keybind)} ({triggerbot_mode})")
                if "delay" in triggerbot_config:
                    triggerbot_delay = triggerbot_config["delay"]
                    dpg.set_value("triggerbot_delay_slider", triggerbot_delay)
                if "prediction_x" in triggerbot_config:
                    triggerbot_prediction_x = triggerbot_config["prediction_x"]
                    dpg.set_value("triggerbot_prediction_x_slider", triggerbot_prediction_x)
                if "prediction_y" in triggerbot_config:
                    triggerbot_prediction_y = triggerbot_config["prediction_y"]
                    dpg.set_value("triggerbot_prediction_y_slider", triggerbot_prediction_y)
                if "fov" in triggerbot_config:
                    triggerbot_fov = triggerbot_config["fov"]
                    dpg.set_value("triggerbot_fov_slider", triggerbot_fov)
            if "walkspeed" in config_data:
                walkspeed_config = config_data["walkspeed"]
                global walkspeed_gui_enabled, walkspeed_gui_value
                if "enabled" in walkspeed_config:
                    walkspeed_gui_enabled = walkspeed_config["enabled"]
                    dpg.set_value("walkspeed_gui_checkbox", walkspeed_gui_enabled)
                    dpg.configure_item("walkspeed_gui_slider", show=walkspeed_gui_enabled)
                if "value" in walkspeed_config:
                    walkspeed_gui_value = walkspeed_config["value"]
                    dpg.set_value("walkspeed_gui_slider", walkspeed_gui_value)
            if "jump_power" in config_data:
                jump_power_config = config_data["jump_power"]
                global jump_power_enabled, jump_power_value
                if "enabled" in jump_power_config:
                    jump_power_enabled = jump_power_config["enabled"]
                    dpg.set_value("jump_power_checkbox", jump_power_enabled)
                    dpg.configure_item("jump_power_slider", show=jump_power_enabled)
                if "value" in jump_power_config:
                    jump_power_value = jump_power_config["value"]
                    dpg.set_value("jump_power_slider", jump_power_value)
            if "fly" in config_data:
                fly_config = config_data["fly"]
                global fly_enabled, fly_speed
                if "enabled" in fly_config:
                    fly_enabled = fly_config["enabled"]
                    dpg.set_value("fly_checkbox", fly_enabled)
                    dpg.configure_item("fly_slider", show=fly_enabled)
                if "speed" in fly_config:
                    fly_speed = fly_config["speed"]
                    dpg.set_value("fly_slider", fly_speed)
            if "infinite_jump" in config_data:
                infinite_jump_config = config_data["infinite_jump"]
                global infinite_jump_enabled
                if "enabled" in infinite_jump_config:
                    infinite_jump_enabled = infinite_jump_config["enabled"]
                    dpg.set_value("infinite_jump_checkbox", infinite_jump_enabled)
            if "god_mode" in config_data:
                god_mode_config = config_data["god_mode"]
                global god_mode_enabled
                if "enabled" in god_mode_config:
                    god_mode_enabled = god_mode_config["enabled"]
                    dpg.set_value("god_mode_checkbox", god_mode_enabled)
            if "fov_changer" in config_data:
                fov_changer_config = config_data["fov_changer"]
                global fov_changer_enabled, fov_value
                if "enabled" in fov_changer_config:
                    fov_changer_enabled = fov_changer_config["enabled"]
                    dpg.set_value("fov_changer_checkbox", fov_changer_enabled)
                    dpg.configure_item("fov_slider", show=fov_changer_enabled)
                if "value" in fov_changer_config:
                    fov_value = fov_changer_config["value"]
                    dpg.set_value("fov_slider", fov_value)
            print(f"Config loaded from: {file_path}")
    except Exception as e:
        print(f"Error loading config: {e}")

# ???????????????????????????? ESP OVERLAY ????????????????????????????
esp_instance = None
esp_app = None
esp_enabled_flag = False
heads = []
colors = []
players_info = []  # list of dicts: { 'head':addr, 'char':addr, 'name':str }

# ESP configuration colors (RGB 0..1)
esp_tracer_color = [1.0, 1.0, 1.0]
esp_box_color = [1.0, 1.0, 1.0]
esp_name_enabled = False
esp_name_color = [1.0, 1.0, 1.0]
name_esp_mode = 'DisplayName'  # 'DisplayName' | 'Username' | 'UserId'
name_esp_include_self = False

# Outlines per-visual
esp_tracer_outline_enabled = False
esp_tracer_outline_color = [0.0, 0.0, 0.0]
esp_box_outline_enabled = False
esp_box_outline_color = [0.0, 0.0, 0.0]
esp_fill_outline_enabled = False
esp_fill_outline_color = [0.0, 0.0, 0.0]
esp_skeleton_outline_enabled = False
esp_skeleton_outline_color = [0.0, 0.0, 0.0]

# ESP preview image (for ESP tab preview panel)
esp_preview_use_image = True  # auto-use if found
esp_preview_image_path = ""
esp_preview_tex = 0
esp_preview_size = (0, 0)

# FOV overlay and aimbot settings
show_fov_enabled = False
use_fov_enabled = True
fov_circle_radius = 150.0
fov_circle_color = [0.9, 0.9, 0.0]
fov_outline_enabled = False
fov_outline_color = [0.0, 0.0, 0.0]
fov_line_thickness = 2.0
follow_fov_enabled = False

# Snowflakes overlay (removed)


class ESPOverlay(QOpenGLWidget):
    def __init__(self):
        super().__init__()

        # Always-on-top, click-through, transparent overlay
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_NoSystemBackground)
        self.resize(1920, 1080)

        # state
        self.time = 0.0
        self.plr_data = []   # [(x, y, col)]
        self.box_data = []   # [(center_x, center_y, half_w, half_h, col)]
        self.box_fill_data = []  # [(center_x, center_y, half_w, half_h, col, alpha)]
        self.skeleton_data = []  # [[(x1,y1),(x2,y2)], ...] list of line segments
        self.last_matrix = None
        self.prev_geometry = (0, 0, 0, 0)
        self.startLineX = 0
        self.startLineY = 0
        self.name_data = []  # [(x,y,text,(r,g,b,a))]
        self.last_update = 0.0
        self.batch_toggle = 0  # alternate subsets on heavy visuals

        # Make window click-through
        hwnd = self.winId().__int__()
        ex_style = windll.user32.GetWindowLongW(hwnd, -20)
        ex_style |= 0x80000 | 0x20  # WS_EX_LAYERED | WS_EX_TRANSPARENT
        windll.user32.SetWindowLongW(hwnd, -20, ex_style)

    def initializeGL(self):
        glClearColor(0.0, 0.0, 0.0, 0.0)
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glLineWidth(2.0)
        glEnable(GL_LINE_SMOOTH)
        glHint(GL_LINE_SMOOTH_HINT, GL_NICEST)
        try:
            glEnable(GL_POINT_SMOOTH)
        except Exception:
            pass

    def resizeGL(self, w, h):
        glViewport(0, 0, w, h)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, w, h, 0, -1, 1)  # origin at top-left
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT)
        glLoadIdentity()
        # Ensure blending stays enabled (QPainter may change GL state)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # Snaplines
        for x, y, col in self.plr_data:
            try:
                qcol = QColor(col)
                r, g, b, a = qcol.redF(), qcol.greenF(), qcol.blueF(), qcol.alphaF()
            except Exception:
                r, g, b, a = 1.0, 1.0, 1.0, 1.0
            # Outline pass
            if globals().get('esp_tracer_outline_enabled', False):
                oc = globals().get('esp_tracer_outline_color', [0.0,0.0,0.0])
                glLineWidth(4.0)
                glColor4f(float(oc[0]), float(oc[1]), float(oc[2]), 1.0)
                glBegin(GL_LINES)
                glVertex2f(self.startLineX, self.startLineY)
                glVertex2f(x, y)
                glEnd()
            # Main pass
            glLineWidth(2.0)
            glColor4f(r, g, b, a)
            glBegin(GL_LINES)
            glVertex2f(self.startLineX, self.startLineY)
            glVertex2f(x, y)
            glEnd()

        # FOV circle
        # Combat FOV circle
        if globals().get('show_fov_enabled', False):
            W, H = self.width(), self.height()
            # Center either screen center or cursor (follow)
            cx, cy = W/2.0, H/2.0
            if globals().get('follow_fov_enabled', False):
                try:
                    pt = POINT()
                    windll.user32.GetCursorPos(byref(pt))
                    # convert to overlay coords using last geometry (left, top, w, h)
                    left, top, _, _ = self.prev_geometry
                    cx = max(0, min(W, pt.x - left))
                    cy = max(0, min(H, pt.y - top))
                except Exception:
                    pass
            r = float(globals().get('fov_circle_radius', 150.0))
            thickness = max(1, int(float(globals().get('fov_line_thickness', 2.0))))
            if r > 2:
                segments = 128
                # Draw main ring with thickness (multiple concentric loops)
                col = globals().get('fov_circle_color', [1.0,1.0,1.0])
                glColor4f(col[0], col[1], col[2], 1.0)
                for t in range(thickness):
                    rt = r - thickness/2.0 + t
                    glBegin(GL_LINE_LOOP)
                    for i in range(segments):
                        ang = 2.0*3.14159265*i/segments
                        glVertex2f(cx + rt*float(math.cos(ang)), cy + rt*float(math.sin(ang)))
                    glEnd()
                # Outline outside and inside
                if globals().get('fov_outline_enabled', False):
                    ocol = globals().get('fov_outline_color', [0.0,0.0,0.0])
                    glColor4f(ocol[0], ocol[1], ocol[2], 1.0)
                    for delta in (-thickness, thickness):
                        ro = r + delta
                        glBegin(GL_LINE_LOOP)
                        for i in range(segments):
                            ang = 2.0*3.14159265*i/segments
                            glVertex2f(cx + ro*float(math.cos(ang)), cy + ro*float(math.sin(ang)))
                        glEnd()

        # Silent Aim FOV circle
        if globals().get('silent_show_fov_enabled', False):
            W, H = self.width(), self.height()
            cx, cy = W/2.0, H/2.0
            if globals().get('silent_follow_fov_enabled', False):
                try:
                    pt = POINT(); windll.user32.GetCursorPos(byref(pt))
                    left, top, _, _ = self.prev_geometry
                    cx = max(0, min(W, pt.x - left)); cy = max(0, min(H, pt.y - top))
                except Exception: pass
            r = float(globals().get('silent_fov_circle_radius', 150.0))
            thickness = max(1, int(float(globals().get('silent_fov_line_thickness', 2.0))))
            if r > 2:
                segments = 128
                col = globals().get('silent_fov_circle_color', [0.0,0.8,1.0])
                glColor4f(col[0], col[1], col[2], 1.0)
                for t in range(thickness):
                    rt = r - thickness/2.0 + t
                    glBegin(GL_LINE_LOOP)
                    for i in range(segments):
                        ang = 2.0*3.14159265*i/segments
                        glVertex2f(cx + rt*float(math.cos(ang)), cy + rt*float(math.sin(ang)))
                    glEnd()
                if globals().get('silent_fov_outline_enabled', False):
                    ocol = globals().get('silent_fov_outline_color', [0.0,0.0,0.0])
                    glColor4f(ocol[0], ocol[1], ocol[2], 1.0)
                    for delta in (-thickness, thickness):
                        ro = r + delta
                        glBegin(GL_LINE_LOOP)
                        for i in range(segments):
                            ang = 2.0*3.14159265*i/segments
                            glVertex2f(cx + ro*float(math.cos(ang)), cy + ro*float(math.sin(ang)))
                        glEnd()

        # Filled Boxes (draw first, behind everything)
        for cx, cy, half_w, half_h, col, alpha in self.box_fill_data:
            if half_w <= 0 or half_h <= 0:
                continue
            try:
                qcol = QColor(col)
                r, g, b = qcol.redF(), qcol.greenF(), qcol.blueF()
            except Exception:
                r, g, b = 1.0, 1.0, 1.0
            glColor4f(r, g, b, alpha)
            glBegin(GL_QUADS)
            glVertex2f(cx - half_w, cy - half_h)
            glVertex2f(cx + half_w, cy - half_h)
            glVertex2f(cx + half_w, cy + half_h)
            glVertex2f(cx - half_w, cy + half_h)
            glEnd()
            # Optional outline around filled box
            if globals().get('esp_fill_outline_enabled', False):
                oc = globals().get('esp_fill_outline_color', [0.0,0.0,0.0])
                glLineWidth(3.0)
                glColor4f(float(oc[0]), float(oc[1]), float(oc[2]), 1.0)
                glBegin(GL_LINE_LOOP)
                glVertex2f(cx - half_w, cy - half_h)
                glVertex2f(cx + half_w, cy - half_h)
                glVertex2f(cx + half_w, cy + half_h)
                glVertex2f(cx - half_w, cy + half_h)
                glEnd()

        # Boxes (outline)
        for cx, cy, half_w, half_h, col in self.box_data:
            if half_w <= 0 or half_h <= 0:
                continue
            try:
                qcol = QColor(col)
                r, g, b, a = qcol.redF(), qcol.greenF(), qcol.blueF(), qcol.alphaF()
            except Exception:
                r, g, b, a = 1.0, 1.0, 1.0, 1.0
            # Optional box outline behind main box
            if globals().get('esp_box_outline_enabled', False):
                oc = globals().get('esp_box_outline_color', [0.0,0.0,0.0])
                glLineWidth(4.0)
                glColor4f(float(oc[0]), float(oc[1]), float(oc[2]), 1.0)
                glBegin(GL_LINE_LOOP)
                glVertex2f(cx - half_w, cy - half_h)
                glVertex2f(cx + half_w, cy - half_h)
                glVertex2f(cx + half_w, cy + half_h)
                glVertex2f(cx - half_w, cy + half_h)
                glEnd()
            # Main box
            glLineWidth(2.0)
            glColor4f(r, g, b, a)
            glBegin(GL_LINE_LOOP)
            glVertex2f(cx - half_w, cy - half_h)
            glVertex2f(cx + half_w, cy - half_h)
            glVertex2f(cx + half_w, cy + half_h)
            glVertex2f(cx - half_w, cy + half_h)
            glEnd()

        # Skeleton
        for line_seg in self.skeleton_data:
            if len(line_seg) < 2:
                continue
            try:
                col = line_seg[2] if len(line_seg) > 2 else "#FFFFFF"
                qcol = QColor(col)
                r, g, b, a = qcol.redF(), qcol.greenF(), qcol.blueF(), qcol.alphaF()
            except Exception:
                r, g, b, a = 1.0, 1.0, 1.0, 1.0
            # Outline pass
            if globals().get('esp_skeleton_outline_enabled', False):
                oc = globals().get('esp_skeleton_outline_color', [0.0,0.0,0.0])
                glLineWidth(4.0)
                glColor4f(float(oc[0]), float(oc[1]), float(oc[2]), 1.0)
                glBegin(GL_LINES)
                glVertex2f(line_seg[0][0], line_seg[0][1])
                glVertex2f(line_seg[1][0], line_seg[1][1])
                glEnd()
            # Main pass
            glLineWidth(2.0)
            glColor4f(r, g, b, a)
            glBegin(GL_LINES)
            glVertex2f(line_seg[0][0], line_seg[0][1])
            glVertex2f(line_seg[1][0], line_seg[1][1])
            glEnd()

        # Names via QPainter (crisp text on top)
        if self.name_data:
            painter = QPainter(self)
            try:
                for x, y, txt, col in self.name_data:
                    qcol = QColor(int(col[0]*255), int(col[1]*255), int(col[2]*255)) if isinstance(col, tuple) else QColor(col)
                    painter.setPen(qcol)
                    painter.drawText(int(x), int(y), txt)
            finally:
                painter.end()


    def _update_overlay_geometry(self):
        hwnd_roblox = find_window_by_title("Roblox")
        if not hwnd_roblox:
            # Keep previous geometry to avoid flicker when window lookup fails momentarily
            return True
        left, top, right, bottom = get_client_rect_on_screen(hwnd_roblox)
        left, top, right, bottom = get_client_rect_on_screen(hwnd_roblox)
        new_geom = (left, top, right - left, bottom - top)
        if new_geom != self.prev_geometry:
            self.setGeometry(*new_geom)
            self.prev_geometry = new_geom
            self.startLineX = self.width() / 2
            self.startLineY = self.height() - max(10, self.height() // 20)
        return True


    def update_players(self):
        # Manage visibility based on any active visuals
        active_visuals = esp_enabled_flag or globals().get('show_fov_enabled', False) or globals().get('silent_show_fov_enabled', False)
        if not active_visuals:
            self.plr_data.clear(); self.box_data.clear(); self.box_fill_data.clear(); self.skeleton_data.clear(); self.name_data.clear();
            try:
                self.hide()
            except Exception:
                pass
            self.update();
            return
        else:
            try:
                self.show()
            except Exception:
                pass
        # When ESP itself is disabled, skip heavy memory work but still draw FOV
        if not esp_enabled_flag:
            self.plr_data.clear(); self.box_data.clear(); self.box_fill_data.clear(); self.skeleton_data.clear(); self.name_data.clear();
            self.update();
            return
        if lpAddr == 0 or plrsAddr == 0 or matrixAddr == 0:
            self.plr_data.clear(); self.box_data.clear(); self.box_fill_data.clear(); self.skeleton_data.clear(); self.name_data.clear(); self.update(); return

        now = time.time()
        # Throttle using global FPS
        if now - self.last_update < get_frame_interval():
            return
        self.last_update = now

        if now - self.time > 0.1:
            if not self._update_overlay_geometry():
                return
            self.time = now

        # Read matrix
        try:
            matrixRaw = pm.read_bytes(matrixAddr, 64)
            view_proj_matrix = array(unpack_from("<16f", matrixRaw, 0), dtype=float32).reshape(4, 4)
            self.last_matrix = view_proj_matrix
        except Exception:
            if self.last_matrix is None:
                return
            view_proj_matrix = self.last_matrix

        self.plr_data.clear()
        self.box_data.clear()
        self.box_fill_data.clear()
        self.skeleton_data.clear()
        self.name_data.clear()

        vecs = []
        W, H = self.width(), self.height()
        
        # Snapshot players_info to avoid race with background updater
        info_list = list(players_info) if isinstance(players_info, list) else []
        if not info_list:
            self.update();
            return
        # Prioritize and clamp indices safely
        raw_idx = HPOPT.prioritize_players(info_list, W, H, budget=64) if hasattr(HPOPT, 'prioritize_players') else list(range(min(64, len(info_list))))
        idx_list = [i for i in raw_idx if 0 <= i < len(info_list)]
        for idx in idx_list:
            info = info_list[idx]
            try:
                head = info.get('head', 0)
                char = info.get('char', 0)
                hrp_cached = info.get('hrp', 0)
                # Select name based on mode
                mode = globals().get('name_esp_mode','DisplayName')
                if mode == 'Username':
                    pname = info.get('username','')
                elif mode == 'UserId':
                    pname = info.get('userid','')
                else:
                    pname = info.get('display','')
                if (not globals().get('name_esp_include_self', False)) and info.get('is_self', False):
                    pname = ''
                if not head:
                    continue
                primitive = pm.read_longlong(head + int(offsets['Primitive'], 16))
                if not primitive:
                    continue
                pos_addr = primitive + int(offsets['Position'], 16)
                head_pos = unpack_from("<fff", pm.read_bytes(pos_addr, 12), 0)
                vecs.append((head_pos, idx))
                # notify optimizer of current screen pos when available later

                # Box, skeleton and name
                if (esp_box_enabled or esp_box_filled or esp_skeleton_enabled or esp_name_enabled) and char:
                    # Collect a small set of parts to bound the whole body
                    part_names = ['Head','HumanoidRootPart','UpperTorso','Torso','LeftHand','RightHand','LeftFoot','RightFoot']
                    screen_pts = []
                    part_screen_pos = {}  # store screen pos for skeleton
                    # use cached hrp if present
                    if hrp_cached:
                        try:
                            pr = pm.read_longlong(hrp_cached + int(offsets['Primitive'], 16))
                            if pr:
                                pa = pr + int(offsets['Position'], 16)
                                wp = unpack_from('<fff', pm.read_bytes(pa, 12), 0)
                                sp = world_to_screen_with_matrix(wp, view_proj_matrix, W, H)
                                if sp is not None:
                                    screen_pts.append(sp)
                                    part_screen_pos['HumanoidRootPart'] = sp
                        except Exception:
                            pass
                    for pn in part_names:
                        p = FindFirstChild(char, pn)
                        if not p:
                            continue
                        try:
                            pr = pm.read_longlong(p + int(offsets['Primitive'], 16))
                            if not pr:
                                continue
                            pa = pr + int(offsets['Position'], 16)
                            wp = unpack_from('<fff', pm.read_bytes(pa, 12), 0)
                            sp = world_to_screen_with_matrix(wp, view_proj_matrix, W, H)
                            if sp is not None:
                                screen_pts.append(sp)
                                part_screen_pos[pn] = sp
                                try:
                                    HPOPT.note_screen(head, sp)
                                except Exception:
                                    pass
                        except Exception:
                            continue
                    if len(screen_pts) >= 2:
                        xs = [p[0] for p in screen_pts]
                        ys = [p[1] for p in screen_pts]
                        min_x, max_x = max(0, min(xs)), min(W, max(xs))
                        min_y, max_y = max(0, min(ys)), min(H, max(ys))
                        # padding to fully surround
                        min_x = max(0, min_x - 2); max_x = min(W, max_x + 2)
                        min_y = max(0, min_y - 2); max_y = min(H, max_y + 2)
                        box_w_full = max(2, max_x - min_x)
                        box_h_full = max(2, max_y - min_y)
                        cx = (min_x + max_x) * 0.5
                        cy = (min_y + max_y) * 0.5
                        half_w = box_w_full * 0.5
                        half_h = box_h_full * 0.5
                        if esp_box_enabled:
                            col = QColor(int(esp_box_color[0]*255), int(esp_box_color[1]*255), int(esp_box_color[2]*255)).name()
                            self.box_data.append((cx, cy, half_w, half_h, col))
                        if esp_box_filled:
                            fill_col = QColor(int(esp_box_fill_color[0]*255), int(esp_box_fill_color[1]*255), int(esp_box_fill_color[2]*255)).name()
                            self.box_fill_data.append((cx, cy, half_w, half_h, fill_col, esp_box_fill_alpha))
                        if esp_skeleton_enabled:
                            # Draw skeleton lines connecting body parts
                            skel_col = QColor(int(esp_skeleton_color[0]*255), int(esp_skeleton_color[1]*255), int(esp_skeleton_color[2]*255)).name()
                            # Head to torso
                            if 'Head' in part_screen_pos and 'UpperTorso' in part_screen_pos:
                                self.skeleton_data.append([part_screen_pos['Head'], part_screen_pos['UpperTorso'], skel_col])
                            elif 'Head' in part_screen_pos and 'Torso' in part_screen_pos:
                                self.skeleton_data.append([part_screen_pos['Head'], part_screen_pos['Torso'], skel_col])
                            # Torso to HRP
                            if 'UpperTorso' in part_screen_pos and 'HumanoidRootPart' in part_screen_pos:
                                self.skeleton_data.append([part_screen_pos['UpperTorso'], part_screen_pos['HumanoidRootPart'], skel_col])
                            elif 'Torso' in part_screen_pos and 'HumanoidRootPart' in part_screen_pos:
                                self.skeleton_data.append([part_screen_pos['Torso'], part_screen_pos['HumanoidRootPart'], skel_col])
                            # Arms
                            torso_pos = part_screen_pos.get('UpperTorso') or part_screen_pos.get('Torso')
                            if torso_pos:
                                if 'LeftHand' in part_screen_pos:
                                    self.skeleton_data.append([torso_pos, part_screen_pos['LeftHand'], skel_col])
                                if 'RightHand' in part_screen_pos:
                                    self.skeleton_data.append([torso_pos, part_screen_pos['RightHand'], skel_col])
                            # Legs
                            hrp_pos = part_screen_pos.get('HumanoidRootPart')
                            if hrp_pos:
                                if 'LeftFoot' in part_screen_pos:
                                    self.skeleton_data.append([hrp_pos, part_screen_pos['LeftFoot'], skel_col])
                                if 'RightFoot' in part_screen_pos:
                                    self.skeleton_data.append([hrp_pos, part_screen_pos['RightFoot'], skel_col])
                        if esp_name_enabled:
                            self.name_data.append((cx, max(0, int(min_y) - 4), pname, tuple(esp_name_color)))
            except Exception:
                continue

        if not vecs:
            self.update()
            return

        # Snaplines projection
        vecs_np = empty((len(vecs), 4), dtype=float32)
        for i, (vec, idx) in enumerate(vecs):
            vecs_np[i] = (vec[0], vec[1], vec[2], 1.0)

        clip_coords = einsum('ij,nj->ni', view_proj_matrix, vecs_np)
        for out_i, clip in enumerate(clip_coords):
            w_comp = clip[3]
            if w_comp == 0:
                continue
            ndc = clip[:3] / w_comp
            if 0.0 <= ndc[2] <= 1.0:
                x = int((ndc[0] + 1.0) * 0.5 * W)
                y = int((1.0 - ndc[1]) * 0.5 * H)
                # use globally selected tracer color
                if 0 <= x < W and 0 <= y < H and esp_tracers_enabled:
                    col_hex = QColor(int(esp_tracer_color[0]*255), int(esp_tracer_color[1]*255), int(esp_tracer_color[2]*255)).name()
                    self.plr_data.append((x, y, col_hex))
        # Names drawn in paintGL; just trigger repaint
        self.update()



def headAndHumFinder():
    global heads, colors
    while True:
        if not esp_enabled_flag or lpAddr == 0 or plrsAddr == 0 or matrixAddr == 0:
            time.sleep(1)
            continue

        tempColors = []
        tempHeads = []
        tempInfos = []
        try:
            lpTeam = pm.read_longlong(lpAddr + int(offsets["Team"], 16))
        except:
            time.sleep(1)
            continue

        ignore_team = globals().get('esp_ignoreteam', False)
        ignore_dead = globals().get('esp_ignoredead', False)
        include_self = globals().get('name_esp_include_self', False)

        for v in GetChildren(plrsAddr):
            if (not include_self) and v == lpAddr:
                continue
            try:
                team = pm.read_longlong(v + int(offsets["Team"], 16))
                if ignore_team and (team == lpTeam or team <= 0):
                    continue
                char = pm.read_longlong(v + int(offsets["ModelInstance"], 16))
                if not char:
                    continue
                head = FindFirstChild(char, 'Head')
                if not head:
                    continue
                hum = FindFirstChildOfClass(char, 'Humanoid')
                if not hum:
                    continue
                hrp = FindFirstChild(char, 'HumanoidRootPart')
                if ignore_dead:
                    health = pm.read_float(hum + int(offsets["Health"], 16))
                    if health <= 0:
                        continue
                tempHeads.append(head)
                tempColors.append("#FFFFFF")
                # Resolve name fields
                try:
                    uname = GetName(v)
                except Exception:
                    uname = ''
                try:
                    # DisplayName stored inline at Player + 0x130 (Roblox string struct)
                    dname = ReadRobloxString(v + int(offsets.get('DisplayName','0x130'), 16))
                    if not dname:
                        dname = uname
                except Exception:
                    dname = uname
                try:
                    uid_val = pm.read_int(v + int(offsets.get('UserId','0x298'), 16))
                    uid = str(uid_val)
                except Exception:
                    uid = '0'
                tempInfos.append({'head': head, 'char': char, 'hrp': hrp, 'display': dname, 'username': uname, 'userid': uid, 'is_self': v==lpAddr})
            except:
                continue

        heads = tempHeads
        colors = tempColors
        globals()['players_info'] = tempInfos
        time.sleep(max(0.02, get_frame_interval()))


def start_esp_overlay():
    global esp_instance, esp_app, esp_enabled_flag

    def qt_loop():
        global esp_instance, esp_app
        try:
            esp_app = QApplication([])
            esp_instance = ESPOverlay()
            esp_instance.hide()  # start hidden; shown when enabled

            # Timer uses global FPS
            global esp_timer
            esp_timer = QTimer()
            esp_timer.setInterval(max(1, int(1000 * get_frame_interval())))
            esp_timer.timeout.connect(esp_instance.update_players)
            esp_timer.start()

            esp_app.exec_()
        except Exception as e:
            print(f"[ERROR] ESP overlay failed to start: {e}")

    # Start only once; toggling just flips flag
    if esp_instance is None:
        threading.Thread(target=qt_loop, daemon=True).start()
        threading.Thread(target=headAndHumFinder, daemon=True).start()

def stop_esp_overlay():
    # Do not destroy Qt; just disable and hide to avoid crashes
    global esp_instance, esp_enabled_flag
    esp_enabled_flag = False
    try:
        if esp_instance is not None:
            def _do_hide():
                try:
                    esp_instance.plr_data.clear(); esp_instance.box_data.clear(); esp_instance.box_fill_data.clear(); esp_instance.skeleton_data.clear(); esp_instance.name_data.clear();
                    esp_instance.hide(); esp_instance.update()
                except Exception:
                    pass
            # Post to Qt thread
            QTimer.singleShot(0, _do_hide)
    except Exception:
        pass

# ???????????????????????????? GUI CREATION ????????????????????????????
import os
import time
import msvcrt
import ctypes
import random
import string
import threading

# Dark Blue ANSI color
BLUE = "\033[38;5;18m"

RESET_COLOR = "\033[0m"

ASCII_TEXT = r"""
                      $$\                                   $$\   $$\                   $$\                 $$\       
                      $$ |                                  \__|  $$ |                  $$ |                $$ |      
 $$$$$$\  $$\   $$\ $$$$$$\    $$$$$$\   $$$$$$\  $$$$$$$\  $$\ $$$$$$\   $$\   $$\     $$ |  $$\  $$$$$$\  $$ |  $$\ 
$$  __$$\ \$$\ $$  |\_$$  _|  $$  __$$\ $$  __$$\ $$  __$$\ $$ |\_$$  _|  $$ |  $$ |    $$ | $$  |$$  __$$\ $$ | $$  |
$$$$$$$$ | \$$$$  /   $$ |    $$$$$$$$ |$$ |  \__|$$ |  $$ |$$ |  $$ |    $$ |  $$ |    $$$$$$  / $$$$$$$$ |$$$$$$  / 
$$   ____| $$  $$<    $$ |$$\ $$   ____|$$ |      $$ |  $$ |$$ |  $$ |$$\ $$ |  $$ |    $$  _$$<  $$   ____|$$  _$$<  
\$$$$$$$\ $$  /\$$\   \$$$$  |\$$$$$$$\ $$ |      $$ |  $$ |$$ |  \$$$$  |\$$$$$$$ |$$\ $$ | \$$\ \$$$$$$$\ $$ | \$$\ 
 \_______|\__/  \__|   \____/  \_______|\__|      \__|  \__|\__|   \____/  \____$$ |\__|\__|  \__| \_______|\__|  \__|
                                                                          $$\   $$ |                                  
                                                                          \$$$$$$  |                                  
                                                                           \______/                                   
"""


def set_console_opacity(opacity_percent: int):
    """Set console window opacity (0-100%)."""
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    GWL_EXSTYLE = -20
    WS_EX_LAYERED = 0x00080000
    LWA_ALPHA = 0x2
    
    style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
    ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED)
    
    alpha = int(255 * (opacity_percent / 100))
    ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0, alpha, LWA_ALPHA)

def random_title_loop():
    """Changes the console title every minute to a random string."""
    while True:
        rand_title = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))
        ctypes.windll.kernel32.SetConsoleTitleW(rand_title)
        time.sleep(60)

# Set opacity to 70% (adjust as needed)
set_console_opacity(70)

# Show ASCII immediately on start
os.system('cls' if os.name == 'nt' else 'clear')
try:
    columns = os.get_terminal_size().columns
except OSError:
    columns = 80
for line in ASCII_TEXT.splitlines():
    print(BLUE + line.center(columns) + RESET_COLOR)

# Start title randomizer in background
threading.Thread(target=random_title_loop, daemon=True).start()


# ???????????????????????????? GUI CREATION ????????????????????????????
def check_license():
    """Shows console-style license verification with masked input."""
    print("\n (+) key: ", end="", flush=True)
   
    while True:
        try:
            license_key = "allah"
           
            while True:
                char = msvcrt.getch().decode('utf-8')
               
                if char == '\r':  # Enter
                    print()
                    break
                elif char == '\b':  # Backspace
                    if license_key:
                        license_key = license_key[:-1]
                        print('\b \b', end="", flush=True)
                elif char.isprintable():
                    license_key += char
                    print('*', end="", flush=True)  # Show * instead of actual char
           
            if license_key == "kankan":
                os.system('cls' if os.name == 'nt' else 'clear')
                print("[warning] updater: checking if directory exists", end="", flush=True)
                time.sleep(3)
                return True
            else:
                print("[ERROR] Invalid license key!")
                print("[logs] License key: ", end="", flush=True)
        except (EOFError, KeyboardInterrupt):
            print("\n[INFO] License verification cancelled")
            return False

# main entry moved to end of file after all definitions

# (Removed legacy DPG drag handlers and viewport code)
import importlib
try:
    import imgui
    import glfw
    from imgui.integrations.glfw import GlfwRenderer
    from OpenGL import GL as gl
    _IMGUI_IMPORTS_OK = True
except Exception as _e:
    # Will be handled at main entry
    _IMGUI_IMPORTS_OK = False
    imgui = None
    glfw = None
    GlfwRenderer = None
    gl = None

# Simple token/whitelist store (same logic as earlier loader, no GUI deps)
APP_NAME = 'shitware'
APP_DIR = os.path.join(os.getenv('APPDATA', os.getcwd()), APP_NAME)
CONFIG_PATH = os.path.join(APP_DIR, 'loader_config.json')
ADMIN_UUIDS = {'8982C130-7EB6-74A1-5710-5811228F62D9'}
DEFAULT_CFG = {'instance_uuid': None,'token_hashes': [],'whitelist': [],'blacklist_uuids': [],'blacklist_tokens': []}

def _ensure_dirs(): os.makedirs(APP_DIR, exist_ok=True)

def _write_cfg(cfg): _ensure_dirs(); tmp=CONFIG_PATH+'.tmp'; open(tmp,'w',encoding='utf-8').write(json.dumps(cfg,indent=2)); os.replace(tmp,CONFIG_PATH)

def _machine_uuid():
    try:
        out = __import__('subprocess').check_output(['wmic','csproduct','get','uuid'], creationflags=0x08000000).decode(errors='ignore')
        for ln in out.splitlines():
            s=ln.strip().upper()
            if len(s)==36 and s.count('-')==4 and 'UUID' not in s: return s
    except Exception: pass
    return str(__import__('uuid').uuid4()).upper()

def _load_cfg():
    _ensure_dirs()
    if not os.path.exists(CONFIG_PATH):
        cfg=DEFAULT_CFG.copy(); cfg['instance_uuid']=_machine_uuid(); _write_cfg(cfg); return cfg
    try: cfg=json.load(open(CONFIG_PATH,'r',encoding='utf-8'))
    except Exception: cfg=DEFAULT_CFG.copy()
    for k,v in DEFAULT_CFG.items(): cfg.setdefault(k, v if not isinstance(v,list) else [])
    if not cfg.get('instance_uuid'): cfg['instance_uuid']=_machine_uuid(); _write_cfg(cfg)
    return cfg

def _hash_token(tok:str)->str:
    salt=os.urandom(16)
    dk=__import__('hashlib').pbkdf2_hmac('sha256', tok.encode(), salt, 200_000)
    return 'pbkdf2$'+binascii.hexlify(salt).decode()+'$'+binascii.hexlify(dk).decode()

def _verify_hash(h:str,tok:str)->bool:
    try:
        if not h.startswith('pbkdf2$'): return False
        _,salt_hex,dk_hex=h.split('$'); salt=binascii.unhexlify(salt_hex)
        dk=__import__('hashlib').pbkdf2_hmac('sha256', tok.encode(), salt, 200_000)
        return binascii.hexlify(dk).decode()==dk_hex
    except Exception: return False

def generate_token()->str:
    tok=secrets.token_urlsafe(48)
    cfg=_load_cfg(); cfg['token_hashes'].append({'hash':_hash_token(tok)}); _write_cfg(cfg); return tok

def verify_token_get_hash(tok:str):
    cfg=_load_cfg()
    for it in cfg.get('token_hashes',[]):
        h = it['hash'] if isinstance(it,dict) else it
        if _verify_hash(h,tok): return h
    return None

def is_valid_uuid(s:str)->bool:
    try: __import__('uuid').UUID((s or '').strip()); return True
    except Exception: return False

def is_current_uuid_whitelisted()->bool:
    cfg=_load_cfg(); inst=(cfg.get('instance_uuid','') or '').strip().upper()
    return any(inst==(u or '').strip().upper() for u in cfg.get('whitelist',[]) if is_valid_uuid(u))

# ImGui app
_loader_token=''
_show_admin=False
_authed=False
_status_msg=''

# Auto-setup: generate token and whitelist UUID on first run
def _auto_setup():
    cfg = _load_cfg()
    inst_uuid = cfg.get('instance_uuid', '').strip().upper()
    
    # Auto-whitelist current UUID if not already whitelisted
    if inst_uuid and is_valid_uuid(inst_uuid):
        whitelist = cfg.get('whitelist', [])
        if inst_uuid not in [u.strip().upper() for u in whitelist if is_valid_uuid(u)]:
            whitelist.append(inst_uuid)
            cfg['whitelist'] = whitelist
            _write_cfg(cfg)
    
    # Auto-generate token if none exist
    token_hashes = cfg.get('token_hashes', [])
    if not token_hashes:
        tok = generate_token()
        print(f'[INFO] Auto-generated token: {tok}')
        print('[INFO] Token saved to config. UUID auto-whitelisted.')
    
    # Auto-authenticate if UUID is whitelisted
    if is_current_uuid_whitelisted():
        global _authed
        _authed = True
        _status_msg = 'Auto-authenticated'

_auto_setup()

active_tab='Combat'

# Async inject
inject_in_progress=False
inject_status=''

def _inject_worker():
    global inject_in_progress, inject_status
    try:
        ok = init()
        inject_status = 'Injected' if ok is None or ok else 'Inject failed'
    except Exception as e:
        inject_status = f'inject error: {e}'
    finally:
        inject_in_progress=False

# Keybind capture
kb_capture=None  # 'aimbot' or 'trigger' or 'fly'

# Fly key toggle listener
def fly_key_listener():
    global fly_enabled
    last_state = False
    while True:
        try:
            pressed = (windll.user32.GetAsyncKeyState(fly_keybind) & 0x8000) != 0
            if pressed and not last_state:
                fly_enabled = not fly_enabled
            last_state = pressed
            time.sleep(0.08)
        except Exception:
            time.sleep(0.2)


def _draw_esp_preview_panel():
    try:
        # Right-side preview panel inside ESP tab (fixed size)
        imgui.begin_child('esp_preview', 340, 420, border=True, flags=imgui.WINDOW_NO_SCROLLBAR | imgui.WINDOW_NO_SCROLL_WITH_MOUSE)
        pos_x, pos_y = imgui.get_window_position()
        w, h = 340.0, 420.0
        dl = imgui.get_window_draw_list()
        # Background
        bg = imgui.get_color_u32_rgba(0.08, 0.08, 0.10, 1.0)
        dl.add_rect_filled(pos_x, pos_y, pos_x + w, pos_y + h, bg, 6)
        # Draw a Roblox-style block character (no image dependency)
        pad = 10.0
        x1, y1 = pos_x + pad, pos_y + pad
        x2, y2 = pos_x + w - pad, pos_y + h - pad
        cw, ch = x2 - x1, y2 - y1
        scale = 1.0  # fixed scale so preview never changes size
        cx = x1 + cw*0.5; cy = y1 + ch*0.62
        def rect_fill(rx1, ry1, rx2, ry2, col, round=4, thick=2.0, outline=(0,0,0,1)):
            dl.add_rect_filled(rx1, ry1, rx2, ry2, imgui.get_color_u32_rgba(*col), round)
            if outline:
                dl.add_rect(rx1, ry1, rx2, ry2, imgui.get_color_u32_rgba(*outline), round, 0, thick)
        head_w = 60*scale; head_h = 60*scale
        torso_w = 80*scale; torso_h = 80*scale
        limb_w = 28*scale; limb_h = 70*scale
        # Positions
        head_x1 = cx - head_w/2; head_y1 = cy - torso_h - head_h - 8*scale
        torso_x1 = cx - torso_w/2; torso_y1 = cy - torso_h
        l_arm_x1 = torso_x1 - limb_w - 6*scale; l_arm_y1 = torso_y1 + 6*scale
        r_arm_x1 = torso_x1 + torso_w + 6*scale; r_arm_y1 = torso_y1 + 6*scale
        l_leg_x1 = cx - limb_w - 6*scale; l_leg_y1 = cy + 2*scale
        r_leg_x1 = cx + 6*scale;           r_leg_y1 = cy + 2*scale
        skin = (0.90,0.80,0.70,1.0); shirt=(0.85,0.85,0.90,1.0); pants=(0.45,0.45,0.50,1.0); out=(0,0,0,0.9)
        # Draw blocks
        rect_fill(head_x1, head_y1, head_x1+head_w, head_y1+head_h, skin, round=6, thick=2.0, outline=out)
        rect_fill(torso_x1, torso_y1, torso_x1+torso_w, torso_y1+torso_h, shirt, round=4, thick=2.0, outline=out)
        rect_fill(l_arm_x1, l_arm_y1, l_arm_x1+limb_w, l_arm_y1+limb_h, skin, round=4, thick=2.0, outline=out)
        rect_fill(r_arm_x1, r_arm_y1, r_arm_x1+limb_w, r_arm_y1+limb_h, skin, round=4, thick=2.0, outline=out)
        rect_fill(l_leg_x1, l_leg_y1, l_leg_x1+limb_w, l_leg_y1+limb_h, pants, round=4, thick=2.0, outline=out)
        rect_fill(r_leg_x1, r_leg_y1, r_leg_x1+limb_w, r_leg_y1+limb_h, pants, round=4, thick=2.0, outline=out)
        # Simple face
        eye_col = imgui.get_color_u32_rgba(0,0,0,1)
        dl.add_circle_filled(head_x1+head_w*0.35, head_y1+head_h*0.45, 2.8*scale, eye_col, 12)
        dl.add_circle_filled(head_x1+head_w*0.65, head_y1+head_h*0.45, 2.8*scale, eye_col, 12)
        dl.add_line(head_x1+head_w*0.35, head_y1+head_h*0.65, head_x1+head_w*0.65, head_y1+head_h*0.65, eye_col, 2.0)
        # Geometry for overlays based on the drawn block character
        head_c = (head_x1 + head_w*0.5, head_y1 + head_h*0.5)
        torso_top = (cx, torso_y1)
        torso_bot = (cx, torso_y1 + torso_h)
        l_hand = (l_arm_x1 + limb_w*0.5, l_arm_y1 + limb_h*0.6)
        r_hand = (r_arm_x1 + limb_w*0.5, r_arm_y1 + limb_h*0.6)
        l_foot = (l_leg_x1 + limb_w*0.5, l_leg_y1 + limb_h)
        r_foot = (r_leg_x1 + limb_w*0.5, r_leg_y1 + limb_h)
        hrp = (cx, torso_y1 + torso_h*0.6)
        # Bounding box for ESP
        bb_left = min(l_arm_x1, head_x1, torso_x1, l_leg_x1)
        bb_right = max(r_arm_x1+limb_w, head_x1+head_w, torso_x1+torso_w, r_leg_x1+limb_w)
        bb_top = head_y1
        bb_bottom = max(torso_y1+torso_h, l_leg_y1+limb_h, r_leg_y1+limb_h)
        # ESP previews according to toggles
        # Tracer
        if globals().get('esp_tracers_enabled', True):
            c = globals().get('esp_tracer_color', [1.0,1.0,1.0])
            col = imgui.get_color_u32_rgba(float(c[0]), float(c[1]), float(c[2]), 1.0)
            if globals().get('esp_tracer_outline_enabled', False):
                oc = globals().get('esp_tracer_outline_color', [0.0,0.0,0.0])
                ocol = imgui.get_color_u32_rgba(float(oc[0]), float(oc[1]), float(oc[2]), 1.0)
                dl.add_line(pos_x + w*0.5, pos_y + h - 12, hrp[0], hrp[1], ocol, 4.0)
            dl.add_line(pos_x + w*0.5, pos_y + h - 12, hrp[0], hrp[1], col, 2.0)
        # Filled Box
        if globals().get('esp_box_filled', False):
            c = globals().get('esp_box_fill_color', [1.0,1.0,1.0])
            a = float(globals().get('esp_box_fill_alpha', 0.2))
            col = imgui.get_color_u32_rgba(float(c[0]), float(c[1]), float(c[2]), max(0.0, min(1.0, a)))
            dl.add_rect_filled(bb_left, bb_top, bb_right, bb_bottom, col, 3)
            if globals().get('esp_fill_outline_enabled', False):
                oc = globals().get('esp_fill_outline_color', [0.0,0.0,0.0])
                ocol = imgui.get_color_u32_rgba(float(oc[0]), float(oc[1]), float(oc[2]), 1.0)
                dl.add_rect(bb_left, bb_top, bb_right, bb_bottom, ocol, 3, 0, 3.0)
        # Box outline
        if globals().get('esp_box_enabled', False):
            c = globals().get('esp_box_color', [1.0,1.0,1.0])
            col = imgui.get_color_u32_rgba(float(c[0]), float(c[1]), float(c[2]), 1.0)
            if globals().get('esp_box_outline_enabled', False):
                oc = globals().get('esp_box_outline_color', [0.0,0.0,0.0])
                ocol = imgui.get_color_u32_rgba(float(oc[0]), float(oc[1]), float(oc[2]), 1.0)
                dl.add_rect(bb_left, bb_top, bb_right, bb_bottom, ocol, 3, 0, 4.0)
            dl.add_rect(bb_left, bb_top, bb_right, bb_bottom, col, 3, 0, 2.0)
        # Skeleton
        if globals().get('esp_skeleton_enabled', False):
            c = globals().get('esp_skeleton_color', [1.0,1.0,1.0])
            col = imgui.get_color_u32_rgba(float(c[0]), float(c[1]), float(c[2]), 1.0)
            if globals().get('esp_skeleton_outline_enabled', False):
                oc = globals().get('esp_skeleton_outline_color', [0.0,0.0,0.0])
                ocol = imgui.get_color_u32_rgba(float(oc[0]), float(oc[1]), float(oc[2]), 1.0)
                dl.add_line(head_c[0], head_c[1]+0.5, torso_top[0], torso_top[1]+2, ocol, 4.0)
                dl.add_line(torso_top[0], torso_top[1]+2, torso_bot[0], torso_bot[1]-2, ocol, 4.0)
                dl.add_line(torso_top[0], torso_top[1]+6, l_hand[0], l_hand[1], ocol, 3.5)
                dl.add_line(torso_top[0], torso_top[1]+6, r_hand[0], r_hand[1], ocol, 3.5)
                dl.add_line(torso_bot[0], torso_bot[1]-2, l_foot[0], l_foot[1], ocol, 3.5)
                dl.add_line(torso_bot[0], torso_bot[1]-2, r_foot[0], r_foot[1], ocol, 3.5)
            dl.add_line(head_c[0], head_c[1]+0.5, torso_top[0], torso_top[1]+2, col, 2.5)
            dl.add_line(torso_top[0], torso_top[1]+2, torso_bot[0], torso_bot[1]-2, col, 2.5)
            dl.add_line(torso_top[0], torso_top[1]+6, l_hand[0], l_hand[1], col, 2.0)
            dl.add_line(torso_top[0], torso_top[1]+6, r_hand[0], r_hand[1], col, 2.0)
            dl.add_line(torso_bot[0], torso_bot[1]-2, l_foot[0], l_foot[1], col, 2.0)
            dl.add_line(torso_bot[0], torso_bot[1]-2, r_foot[0], r_foot[1], col, 2.0)
        # Name
        if globals().get('esp_name_enabled', False):
            c = globals().get('esp_name_color', [1.0,1.0,1.0])
            col = imgui.get_color_u32_rgba(float(c[0]), float(c[1]), float(c[2]), 1.0)
            dl.add_text(head_x1, head_y1 - 16*scale, col, 'Preview')
        imgui.end_child()
    except Exception:
        try:
            imgui.end_child()
        except Exception:
            pass


def start_imgui_app():
    global _authed, _loader_token, _show_admin, _status_msg, active_tab, kb_capture, inject_in_progress, inject_status
    if not _IMGUI_IMPORTS_OK or glfw is None:
        print('[ERROR] Required packages not installed. Please install: pip install imgui[glfw] glfw PyOpenGL')
        input("Press Enter to exit...")
        sys.exit(1)
    
    # Auto-authenticate on startup
    if not _authed:
        _authed = True
        _status_msg = 'Auto-authenticated'
    if not glfw.init():
        print('glfw init failed'); return
    glfw.window_hint(glfw.RESIZABLE, True)
    try:
        glfw.window_hint(glfw.TRANSPARENT_FRAMEBUFFER, False)
    except Exception:
        pass
    win = glfw.create_window(800, 600, 'shitware v1337', None, None)
    if not win:
        glfw.terminate(); print('window create failed'); return
    glfw.make_context_current(win)
    imgui.create_context(); impl=GlfwRenderer(win); glfw.swap_interval(1)
    # Auto-load preview PNG if present
    try_load_default_preview()
    io=imgui.get_io(); io.ini_file_name=None
    last_vsync = 1
    threading.Thread(target=fly_key_listener, daemon=True).start()
    while not glfw.window_should_close(win):
        # Manage vsync based on custom FPS
        desired_vsync = 0 if custom_fps_enabled and global_fps > 60 else 1
        if desired_vsync != last_vsync:
            glfw.swap_interval(desired_vsync)
            last_vsync = desired_vsync
        loop_start = time.time()
        glfw.poll_events(); impl.process_inputs()
        gl.glClearColor(0.06,0.06,0.06,1.0); gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        imgui.new_frame()
        # Transparent window without full-screen black background
        imgui.set_next_window_size(760, 520, condition=imgui.ONCE)
        imgui.begin('shitware v1337', flags=imgui.WINDOW_NO_COLLAPSE)
        if not _authed:
            imgui.text('TOKEN:'); changed, _loader_token = imgui.input_text('##token', _loader_token, 256, imgui.INPUT_TEXT_PASSWORD)
            if imgui.button('Login'):
                h=verify_token_get_hash((_loader_token or '').strip())
                if not h: _status_msg='Invalid token'
                else:
                    cfg=_load_cfg(); inst=(cfg.get('instance_uuid','') or '').strip().upper()
                    if not is_current_uuid_whitelisted(): _status_msg='UUID not whitelisted'
                    elif inst in [ (u or '').strip().upper() for u in cfg.get('blacklist_uuids',[]) ]: _status_msg='UUID blacklisted'
                    elif h in cfg.get('blacklist_tokens',[]): _status_msg='Token blacklisted'
                    else:
                        _authed=True; _status_msg='Authenticated'
            # Admin panel access (button only visible if admin)
            cfg=_load_cfg(); inst=(cfg.get('instance_uuid','') or '').strip().upper()
            is_admin=any(inst==a.strip().upper() for a in ADMIN_UUIDS if is_valid_uuid(a))
            if is_admin:
                imgui.same_line()
                if imgui.button('Admin Panel'): _show_admin = not _show_admin
                if _show_admin:
                    if imgui.button('Generate Token'):
                        tok=generate_token();
                        try:
                            import importlib.util
                            __import__('pyperclip').copy(tok) if importlib.util.find_spec('pyperclip') else None
                        except Exception:
                            pass
                        _status_msg='Token generated'
                    imgui.separator(); imgui.text('Tokens:')
                    toks=list(cfg.get('token_hashes', []))
                    imgui.begin_child('toklist', 0, 120, border=True)
                    for i,item in enumerate(toks):
                        h = item['hash'] if isinstance(item,dict) else str(item)
                        imgui.text(h[:28]+'...'); imgui.same_line()
                        if imgui.button(f'X##tok{i}'):
                            cfg=_load_cfg(); rem=list(cfg.get('token_hashes', []));
                            if 0<=i<len(rem): rem.pop(i); cfg['token_hashes']=rem; _write_cfg(cfg)
                    imgui.end_child()
                    imgui.separator(); imgui.text('Whitelisted UUIDs:')
                    # List with remove buttons
                    wl = list(cfg.get('whitelist', []))
                    for i,u in enumerate(wl):
                        imgui.bullet_text(u); imgui.same_line()
                        if imgui.button(f'X##wl{i}'):
                            cfg=_load_cfg(); cfg['whitelist']=[x for x in cfg.get('whitelist',[]) if x!=u]; _write_cfg(cfg)
                    imgui.separator();
                    # Add UUID to whitelist
                    changed, new_uuid = imgui.input_text('Add UUID', '', 64)
                    if imgui.button('Add to whitelist'):
                        if is_valid_uuid(new_uuid):
                            cfg=_load_cfg();
                            if new_uuid not in cfg['whitelist']: cfg['whitelist'].append(new_uuid); _write_cfg(cfg)
                        else: _status_msg='Invalid UUID'
                    imgui.separator(); imgui.text('Blacklisted UUIDs:')
                    bl = list(cfg.get('blacklist_uuids', []))
                    for i,u in enumerate(bl):
                        imgui.bullet_text(u); imgui.same_line()
                        if imgui.button(f'X##bl{i}'):
                            cfg=_load_cfg(); cfg['blacklist_uuids']=[x for x in cfg.get('blacklist_uuids',[]) if x!=u]; _write_cfg(cfg)
                    changed, bl_uuid = imgui.input_text('Blacklist UUID', '', 64)
                    if imgui.button('Add to blacklist'):
                        if is_valid_uuid(bl_uuid):
                            cfg=_load_cfg();
                            if bl_uuid not in cfg.get('blacklist_uuids',[]): cfg.setdefault('blacklist_uuids',[]).append(bl_uuid)
                            # also remove from whitelist if present
                            cfg['whitelist']=[x for x in cfg.get('whitelist',[]) if x!=bl_uuid]
                            _write_cfg(cfg)
                        else: _status_msg='Invalid UUID'
            if _status_msg: imgui.text_colored(_status_msg,0.9,0.85,0.2)
        else:
            # Top toolbar
            if imgui.button('Inject') and not inject_in_progress:
                inject_in_progress=True; inject_status='Injecting...'
                threading.Thread(target=_inject_worker, daemon=True).start()
            imgui.same_line()
            if imgui.button('Rescan') and not inject_in_progress:
                try: init(); _status_msg='Rescanned'
                except Exception as e: _status_msg=f'rescan error: {e}'
            if inject_status:
                imgui.same_line(); imgui.text(inject_status)
            # Tabs
            if imgui.begin_tab_bar('tabs'):
                if imgui.begin_tab_item('Combat')[0]:
                    changed, val = imgui.checkbox('Enable Aimbot', aimbot_enabled); globals()['aimbot_enabled']=val if changed else aimbot_enabled
                    # Keybind capture
                    imgui.same_line()
                    if kb_capture=='aimbot': imgui.text_colored('Press any key...', 0.9,0.8,0.2)
                    elif imgui.button(f'Key: {get_key_name(aimbot_keybind)}'): kb_capture='aimbot'
                    imgui.same_line()
                    if imgui.button(f'Mode: {aimbot_mode}'):
                        globals()['aimbot_mode'] = 'Toggle' if aimbot_mode=='Hold' else 'Hold'
                    # Body part
                    imgui.text('Body part: ')
                    imgui.same_line()
                    is_head = (aimbot_hitpart=='Head')
                    if imgui.radio_button('Head', is_head): globals()['aimbot_hitpart']='Head'
                    imgui.same_line()
                    if imgui.radio_button('Body', not is_head): globals()['aimbot_hitpart']='UpperTorso'
                    # FOV usage & draw
                    chuf, vuf = imgui.checkbox('Use FOV', use_fov_enabled)
                    if chuf: globals()['use_fov_enabled']=vuf
                    chsf, vsf = imgui.checkbox('Show FOV', show_fov_enabled)
                    if chsf:
                        globals()['show_fov_enabled']=vsf
                        if vsf:
                            try: start_esp_overlay()
                            except Exception: pass
                    if show_fov_enabled or use_fov_enabled:
                        chrad, r = imgui.slider_float('FOV Radius', float(fov_circle_radius), 20.0, 600.0)
                        if chrad:
                            globals()['fov_circle_radius']=r
                            globals()['aimbot_fov']=r
                        chc, c = imgui.color_edit3('FOV Color', *fov_circle_color)
                        if chc: globals()['fov_circle_color']=list(c)
                        chout, o = imgui.checkbox('Outline FOV', fov_outline_enabled)
                        if chout: globals()['fov_outline_enabled']=o
                        if fov_outline_enabled:
                            cho, co = imgui.color_edit3('Outline Color', *fov_outline_color)
                            if cho: globals()['fov_outline_color']=list(co)
                        cht, th = imgui.slider_float('FOV Thickness', float(fov_line_thickness), 1.0, 8.0)
                        if cht: globals()['fov_line_thickness']=th
                        chf, fv = imgui.checkbox('Follow FOV (cursor)', follow_fov_enabled)
                        if chf: globals()['follow_fov_enabled']=fv

                    # Aimbot method
                    imgui.text('Aim Method: ')
                    imgui.same_line()
                    aim_camera = (globals().get('aim_method','Camera')=='Camera')
                    if imgui.radio_button('Camera', aim_camera): globals()['aim_method']='Camera'
                    imgui.same_line()
                    if imgui.radio_button('Mouse', not aim_camera): globals()['aim_method']='Mouse'

                    # Smoothness and shake
                    changed, val = imgui.checkbox('Smoothness', aimbot_smoothness_enabled); globals()['aimbot_smoothness_enabled']=val if changed else aimbot_smoothness_enabled
                    if aimbot_smoothness_enabled:
                        ch2, sval = imgui.slider_float('Smooth Amount', float(aimbot_smoothness_value), 100.0, 500.0)
                        if ch2: globals()['aimbot_smoothness_value']=sval
                    changed, val = imgui.checkbox('Shake', aimbot_shake_enabled); globals()['aimbot_shake_enabled']=val if changed else aimbot_shake_enabled
                    if aimbot_shake_enabled:
                        ch3, sval = imgui.slider_float('Shake Strength', float(aimbot_shake_strength), 0.0, 0.05)
                        if ch3: globals()['aimbot_shake_strength']=sval
                    changed, val = imgui.checkbox('Sticky Aim', sticky_aim_enabled); globals()['sticky_aim_enabled']=val if changed else sticky_aim_enabled
                    changed, val = imgui.checkbox('Ignore Team', aimbot_ignoreteam); globals()['aimbot_ignoreteam']=val if changed else aimbot_ignoreteam
                    changed, val = imgui.checkbox('Ignore Dead', aimbot_ignoredead); globals()['aimbot_ignoredead']=val if changed else aimbot_ignoredead
                    imgui.end_tab_item()
                if imgui.begin_tab_item('ESP')[0]:
                    # Two-column layout: left controls, right live preview
                    imgui.columns(2, 'esplayout', True)
                    try:
                        imgui.set_column_width(0, 420)
                        imgui.set_column_width(1, 360)
                    except Exception:
                        pass
                    # Left column (controls)
                    ch, val = imgui.checkbox('Enable ESP', esp_enabled); 
                    if ch:
                        globals()['esp_enabled']=val
                        if val:
                            globals()['esp_enabled_flag']=True
                            try: start_esp_overlay()
                            except Exception as e: _status_msg=f'esp start: {e}'
                        else:
                            try: stop_esp_overlay()
                            except Exception as e: _status_msg=f'esp stop: {e}'
                    ch, val = imgui.checkbox('Box ESP', esp_box_enabled); globals()['esp_box_enabled']=val if ch else esp_box_enabled
                    if esp_box_enabled:
                        chc, c = imgui.color_edit3('Box Color', *esp_box_color)
                        if chc: globals()['esp_box_color'] = list(c)
                        cbo, bo = imgui.checkbox('Outline (Box)', esp_box_outline_enabled)
                        if cbo: globals()['esp_box_outline_enabled']=bo
                        if esp_box_outline_enabled:
                            cbo2, boc = imgui.color_edit3('Outline Color (Box)', *esp_box_outline_color)
                            if cbo2: globals()['esp_box_outline_color']=list(boc)
                    ch, val = imgui.checkbox('Filled Box ESP', esp_box_filled); globals()['esp_box_filled']=val if ch else esp_box_filled
                    if esp_box_filled:
                        chfc, fc = imgui.color_edit3('Fill Color', *esp_box_fill_color)
                        if chfc: globals()['esp_box_fill_color'] = list(fc)
                        chalpha, alpha = imgui.slider_float('Fill Alpha', float(esp_box_fill_alpha), 0.0, 1.0)
                        if chalpha: globals()['esp_box_fill_alpha'] = alpha
                        cfo, fo = imgui.checkbox('Outline (Filled)', esp_fill_outline_enabled)
                        if cfo: globals()['esp_fill_outline_enabled']=fo
                        if esp_fill_outline_enabled:
                            cfo2, foc = imgui.color_edit3('Outline Color (Filled)', *esp_fill_outline_color)
                            if cfo2: globals()['esp_fill_outline_color']=list(foc)
                    ch, val = imgui.checkbox('Skeleton ESP', esp_skeleton_enabled); globals()['esp_skeleton_enabled']=val if ch else esp_skeleton_enabled
                    if esp_skeleton_enabled:
                        chsc, sc = imgui.color_edit3('Skeleton Color', *esp_skeleton_color)
                        if chsc: globals()['esp_skeleton_color'] = list(sc)
                        cso, so = imgui.checkbox('Outline (Skeleton)', esp_skeleton_outline_enabled)
                        if cso: globals()['esp_skeleton_outline_enabled']=so
                        if esp_skeleton_outline_enabled:
                            cso2, soc = imgui.color_edit3('Outline Color (Skeleton)', *esp_skeleton_outline_color)
                            if cso2: globals()['esp_skeleton_outline_color']=list(soc)
                    ch, val = imgui.checkbox('Tracers', esp_tracers_enabled); globals()['esp_tracers_enabled']=val if ch else esp_tracers_enabled
                    if esp_tracers_enabled:
                        chc, c = imgui.color_edit3('Tracer Color', *esp_tracer_color)
                        if chc: globals()['esp_tracer_color'] = list(c)
                        cho, o = imgui.checkbox('Outline (Tracer)', esp_tracer_outline_enabled)
                        if cho: globals()['esp_tracer_outline_enabled']=o
                        if esp_tracer_outline_enabled:
                            cho2, oc = imgui.color_edit3('Outline Color (Tracer)', *esp_tracer_outline_color)
                            if cho2: globals()['esp_tracer_outline_color']=list(oc)
                    ch, val = imgui.checkbox('Name ESP', esp_name_enabled); globals()['esp_name_enabled']=val if ch else esp_name_enabled
                    if esp_name_enabled:
                        # Name source options
                        imgui.text('Name Source:')
                        imgui.same_line()
                        if imgui.radio_button('DisplayName', name_esp_mode=='DisplayName'):
                            globals()['name_esp_mode']='DisplayName'
                        imgui.same_line()
                        if imgui.radio_button('Username', name_esp_mode=='Username'):
                            globals()['name_esp_mode']='Username'
                        imgui.same_line()
                        if imgui.radio_button('UserId', name_esp_mode=='UserId'):
                            globals()['name_esp_mode']='UserId'
                        chs, c = imgui.color_edit3('Name Color', *esp_name_color)
                        if chs: globals()['esp_name_color'] = list(c)
                        chs, inc = imgui.checkbox('Show ESP on self', name_esp_include_self)
                        if chs: globals()['name_esp_include_self']=inc
                    ch, val = imgui.checkbox('Ignore Team', esp_ignoreteam); globals()['esp_ignoreteam']=val if ch else esp_ignoreteam
                    ch, val = imgui.checkbox('Ignore Dead', esp_ignoredead); globals()['esp_ignoredead']=val if ch else esp_ignoredead
                    # Right column (preview)
                    imgui.next_column()
                    _draw_esp_preview_panel()
                    # Back to single column and end tab
                    imgui.columns(1)
                    imgui.end_tab_item()
                if imgui.begin_tab_item('Misc')[0]:
                    # Walkspeed
                    ch, val = imgui.checkbox('Walkspeed Changer', walkspeed_gui_enabled)
                    if ch:
                        globals()['walkspeed_gui_enabled']=val
                        if val and not walkspeed_gui_active:
                            globals()['walkspeed_gui_active']=True
                            threading.Thread(target=walkspeed_gui_loop, daemon=True).start()
                        if not val:
                            globals()['walkspeed_gui_active']=False
                    if walkspeed_gui_enabled:
                        chs, sval = imgui.slider_float('Walkspeed', float(walkspeed_gui_value), 16.0, 500.0)
                        if chs: globals()['walkspeed_gui_value']=sval
                    # Jump Power
                    ch, val = imgui.checkbox('Jump Power Changer', jump_power_enabled)
                    if ch:
                        globals()['jump_power_enabled']=val
                        if val and not jump_power_active:
                            globals()['jump_power_active']=True
                            threading.Thread(target=jump_power_loop, daemon=True).start()
                        if not val:
                            globals()['jump_power_active']=False
                    if jump_power_enabled:
                        chs, sval = imgui.slider_float('Jump Power', float(jump_power_value), 50.0, 500.0)
                        if chs: globals()['jump_power_value']=sval
                    # Fly
                    ch, val = imgui.checkbox('Fly', fly_enabled)
                    if ch:
                        globals()['fly_enabled']=val
                    imgui.same_line()
                    if kb_capture=='fly':
                        imgui.text_colored('Press key...', 0.9,0.8,0.2)
                    elif imgui.button(f'Fly Key: {get_key_name(fly_keybind)}'):
                        kb_capture='fly'
                        if val and not fly_active:
                            globals()['fly_active']=True
                            threading.Thread(target=fly_loop, daemon=True).start()
                        if not val:
                            globals()['fly_active']=False
                    if fly_enabled:
                        chs, sval = imgui.slider_float('Fly Speed', float(fly_speed), 10.0, 200.0)
                        if chs: globals()['fly_speed']=sval
                    # Infinite Jump
                    ch, val = imgui.checkbox('Infinite Jump', infinite_jump_enabled)
                    if ch:
                        globals()['infinite_jump_enabled']=val
                        if val:
                            threading.Thread(target=infinite_jump_loop, daemon=True).start()
                    # God Mode
                    ch, val = imgui.checkbox('God Mode', god_mode_enabled)
                    if ch:
                        globals()['god_mode_enabled']=val
                        if val and not god_mode_active:
                            globals()['god_mode_active']=True
                            threading.Thread(target=god_mode_loop, daemon=True).start()
                        if not val:
                            globals()['god_mode_active']=False
                    # FOV
                    ch, val = imgui.checkbox('FOV Changer', fov_changer_enabled)
                    if ch:
                        globals()['fov_changer_enabled']=val
                        if val and not fov_active:
                            globals()['fov_active']=True
                            threading.Thread(target=fov_changer_loop, daemon=True).start()
                        if not val:
                            globals()['fov_active']=False
                    if fov_changer_enabled:
                        chs, sval = imgui.slider_float('FOV Value', float(fov_value), 30.0, 120.0)
                        if chs: globals()['fov_value']=sval
                    imgui.end_tab_item()
                if imgui.begin_tab_item('Logs')[0]:
                    if _status_msg: imgui.text(_status_msg)
                    imgui.end_tab_item()
                if imgui.begin_tab_item('Silent Aim (FLICK-BETA)')[0]:
                    ch, val = imgui.checkbox('Enable Silent Aim', silent_aim_enabled)
                    if ch: globals()['silent_aim_enabled']=val
                    # Hitpart
                    imgui.text('Body part: '); imgui.same_line()
                    is_head_sa = (silent_aim_hitpart=='Head')
                    if imgui.radio_button('Head##sa', is_head_sa): globals()['silent_aim_hitpart']='Head'
                    imgui.same_line()
                    if imgui.radio_button('Body##sa', not is_head_sa): globals()['silent_aim_hitpart']='UpperTorso'
                    # Filters
                    ch, val = imgui.checkbox('Ignore Team##sa', silent_aim_ignoreteam); 
                    if ch: globals()['silent_aim_ignoreteam']=val
                    ch, val = imgui.checkbox('Ignore Dead##sa', silent_aim_ignoredead); 
                    if ch: globals()['silent_aim_ignoredead']=val
                    # FOV
                    chuf, vuf = imgui.checkbox('Use FOV##sa', silent_use_fov_enabled)
                    if chuf: globals()['silent_use_fov_enabled']=vuf
                    chsf, vsf = imgui.checkbox('Show FOV##sa', silent_show_fov_enabled)
                    if chsf:
                        globals()['silent_show_fov_enabled']=vsf
                        if vsf:
                            try: start_esp_overlay()
                            except Exception: pass
                    if silent_show_fov_enabled or silent_use_fov_enabled:
                        chrad, r = imgui.slider_float('FOV Radius##sa', float(silent_fov_circle_radius), 20.0, 600.0)
                        if chrad: globals()['silent_fov_circle_radius']=r
                        chc, c = imgui.color_edit3('FOV Color##sa', *silent_fov_circle_color)
                        if chc: globals()['silent_fov_circle_color']=list(c)
                        chout, o = imgui.checkbox('Outline FOV##sa', silent_fov_outline_enabled)
                        if chout: globals()['silent_fov_outline_enabled']=o
                        if silent_fov_outline_enabled:
                            cho, co = imgui.color_edit3('Outline Color##sa', *silent_fov_outline_color)
                            if cho: globals()['silent_fov_outline_color']=list(co)
                        cht, th = imgui.slider_float('FOV Thickness##sa', float(silent_fov_line_thickness), 1.0, 8.0)
                        if cht: globals()['silent_fov_line_thickness']=th
                        chf, fv = imgui.checkbox('Follow FOV (cursor)##sa', silent_follow_fov_enabled)
                        if chf: globals()['silent_follow_fov_enabled']=fv
                    imgui.end_tab_item()

                if imgui.begin_tab_item('Configs')[0]:
                    if imgui.button('Save Config'):
                        try:
                            save_config_callback()
                        except Exception as e:
                            _status_msg=f'save failed: {e}'
                    imgui.same_line()
                    if imgui.button('Load Config'):
                        try:
                            load_config_callback()
                        except Exception as e:
                            _status_msg=f'load failed: {e}'
                    imgui.end_tab_item()
                imgui.end_tab_bar()
        # Process keybind capture after drawing controls
        if kb_capture=='aimbot':
            for vk in range(1,256):
                try:
                    if windll.user32.GetAsyncKeyState(vk) & 0x8000:
                        globals()['aimbot_keybind']=vk; kb_capture=None; break
                except Exception:
                    pass
        elif kb_capture=='fly':
            for vk in range(1,256):
                try:
                    if windll.user32.GetAsyncKeyState(vk) & 0x8000:
                        globals()['fly_keybind']=vk; kb_capture=None; break
                except Exception:
                    pass
        elif kb_capture=='silent':
            for vk in range(1,256):
                try:
                    if windll.user32.GetAsyncKeyState(vk) & 0x8000:
                        globals()['silent_aim_keybind']=vk; kb_capture=None; break
                except Exception:
                    pass
        imgui.end(); imgui.render(); impl.render(imgui.get_draw_data()); glfw.swap_buffers(win)
        # Pace GUI loop
        elapsed = time.time() - loop_start
        time.sleep(max(get_frame_interval() - elapsed, 0.0005))
    impl.shutdown(); glfw.terminate()
# (DPG UI removed)

# Silent Aim loop (flick camera to target on left click)
def silentAimLoop():
    prev_lmb = False
    while True:
        loop_start = time.time()
        try:
            if silent_aim_enabled and injected and lpAddr > 0 and plrsAddr > 0 and matrixAddr > 0:
                lmb = (windll.user32.GetAsyncKeyState(0x01) & 0x8000) != 0
                do_flick = lmb and not prev_lmb
                prev_lmb = lmb
                if not do_flick:
                    time.sleep(0.005)
                    continue
                hwnd_roblox = find_window_by_title('Roblox')
                if not hwnd_roblox:
                    time.sleep(0.005)
                    continue
                left, top, right, bottom = get_client_rect_on_screen(hwnd_roblox)
                width, height = right-left, bottom-top
                try:
                    matrixRaw = pm.read_bytes(matrixAddr, 64)
                    view_proj_matrix = reshape(array(unpack_from('<16f', matrixRaw, 0), dtype=float32), (4, 4))
                except Exception:
                    time.sleep(0.005)
                    continue
                lpTeam = pm.read_longlong(lpAddr + int(offsets['Team'], 16))
                center_x, center_y = width/2, height/2
                min_dist = float('inf')
                best_world = None
                def scan_char(char):
                    nonlocal min_dist, best_world
                    if not char:
                        return
                    head = FindFirstChild(char, silent_aim_hitpart if silent_aim_hitpart else 'Head')
                    if not head:
                        return
                    hum = FindFirstChildOfClass(char, 'Humanoid')
                    if not hum:
                        return
                    if silent_aim_ignoredead:
                        try:
                            if pm.read_float(hum + int(offsets['Health'],16)) <= 0:
                                return
                        except Exception:
                            pass
                    prim = pm.read_longlong(head + int(offsets['Primitive'],16))
                    if not prim:
                        return
                    pos = prim + int(offsets['Position'],16)
                    wx, wy, wz = pm.read_float(pos), pm.read_float(pos+4), pm.read_float(pos+8)
                    obj = array([wx, wy, wz], dtype=float32)
                    sc = world_to_screen_with_matrix(obj, view_proj_matrix, width, height)
                    if sc is None:
                        return
                    dist = math.hypot(center_x - sc[0], center_y - sc[1])
                    if globals().get('silent_use_fov_enabled', True) and dist > float(globals().get('silent_fov_circle_radius', 150.0)):
                        return
                    if dist < min_dist:
                        min_dist = dist
                        best_world = (wx, wy, wz)
                # scan all players (still cheap at click-time)
                for v in GetChildren(plrsAddr):
                    if v == lpAddr:
                        continue
                    try:
                        if silent_aim_ignoreteam and pm.read_longlong(v + int(offsets['Team'],16)) == lpTeam:
                            continue
                        char = pm.read_longlong(v + int(offsets['ModelInstance'],16))
                        scan_char(char)
                    except Exception:
                        continue
                if best_world:
                    # hard flick: write orientation twice for stability
                    from_pos = [pm.read_float(camPosAddr + i * 4) for i in range(3)]
                    to_pos = [best_world[0], best_world[1], best_world[2]]
                    look, up, right = cframe_look_at(from_pos, to_pos)
                    for _ in range(2):
                        for i in range(3):
                            pm.write_float(camCFrameRotAddr + i * 12, float(-right[i]))
                            pm.write_float(camCFrameRotAddr + 4 + i * 12, float(up[i]))
                            pm.write_float(camCFrameRotAddr + 8 + i * 12, float(-look[i]))
                        time.sleep(0.001)
            else:
                prev_lmb = False
                time.sleep(0.01)
        except Exception:
            time.sleep(0.02)
        elapsed = time.time() - loop_start
        time.sleep(max(get_frame_interval() - elapsed, 0.0005))

threading.Thread(target=silentAimLoop, daemon=True).start()
tab_selected = (40, 40, 45, 255)  # Slightly lighter gray for selected tab
tab_default = (0.10 * 255, 0.09 * 255, 0.12 * 255, 1.00 * 255)  # Default dark color

# Final main entry (after all definitions)
if __name__ == '__main__':
    try:
        offsets = get('https://offsets.ntgetwritewatch.workers.dev/offsets.json').json()
        setOffsets(int(offsets['Name'], 16), int(offsets['Children'], 16))
    except Exception as e:
        print(f'[ERROR] Failed to load offsets: {e}')
        offsets = {}
    # Ensure defaults per user
    offsets.setdefault('DisplayName', '0x130')
    offsets.setdefault('JumpPower', '0x1B0')
    offsets.setdefault('WalkSpeed', '0x1D4')
    offsets.setdefault('WalkSpeedCheck', offsets['WalkSpeed'])
    threading.Thread(target=background_process_monitor, daemon=True).start()
    start_imgui_app()
