import logging
import os
import json
from glob import glob
from numpy import array, float32, linalg, cross, dot, reshape
from math import sqrt, pi, atan2
from ctypes import windll, byref, Structure, wintypes
from time import time, sleep
from threading import Thread
from requests import get
from pymem import Pymem
from pymem.process import is_64_bit, list_processes
from pymem.exception import ProcessError
from psutil import pid_exists
import dearpygui.dearpygui as dpg
import sys
import uuid
import pyperclip

pi180 = pi / 180

aimassist_enabled = False
aimassist_keybind = 4
aimassist_mode = "Hold"
aimassist_toggled = False
aimassist_smoothness = 0.3
aimassist_smooth_enabled = True
aimassist_hitpart = "UpperTorso"

waiting_for_aimassist_keybind = False
injected = False
license_valid = False

VK_CODES = {
    'Left Mouse': 1, 'Right Mouse': 2, 'Middle Mouse': 4, 'X1 Mouse': 5, 'X2 Mouse': 6,
    'F1': 112, 'F2': 113, 'F3': 114, 'F4': 115, 'F5': 116, 'F6': 117,
    'F7': 118, 'F8': 119, 'F9': 120, 'F10': 121, 'F11': 122, 'F12': 123,
    'A': 65, 'B': 66, 'C': 67, 'D': 68, 'E': 69, 'F': 70, 'G': 71,
    'H': 72, 'I': 73, 'J': 74, 'K': 75, 'L': 76, 'M': 77, 'N': 78,
    'O': 79, 'P': 80, 'Q': 81, 'R': 82, 'S': 83, 'T': 84, 'U': 85,
    'V': 86, 'W': 87, 'X': 88, 'Y': 89, 'Z': 90,
    'Shift': 16, 'Ctrl': 17, 'Alt': 18, 'Space': 32,
    'Enter': 13, 'Tab': 9, 'Caps Lock': 20
}

Handle = None
PID = -1
baseAddr = None
pm = Pymem()
nameOffset = 0
childrenOffset = 0

CONFIG_DIR = "configs"
os.makedirs(CONFIG_DIR, exist_ok=True)

def get_config_files():
    return [os.path.basename(f) for f in glob(os.path.join(CONFIG_DIR, "*.txt"))]

def save_config(config_name):
    if not config_name.endswith(".txt"):
        config_name += ".txt"
    config_path = os.path.join(CONFIG_DIR, config_name)
    config_data = {
        "aimassist": {
            "enabled": aimassist_enabled,
            "keybind": aimassist_keybind,
            "mode": aimassist_mode,
            "smoothness": aimassist_smoothness,
            "smooth_enabled": aimassist_smooth_enabled,
            "hitpart": aimassist_hitpart
        }
    }
    with open(config_path, "w") as f:
        json.dump(config_data, f, indent=4)
    dpg.configure_item("config_combo", items=get_config_files())
    dpg.configure_item("config_status", label="")

def load_config(config_name):
    global aimassist_enabled, aimassist_keybind, aimassist_mode, aimassist_toggled, aimassist_smoothness, aimassist_smooth_enabled, aimassist_hitpart
    config_path = os.path.join(CONFIG_DIR, config_name)
    try:
        with open(config_path, "r") as f:
            config_data = json.load(f)
        aimassist = config_data.get("aimassist", {})
        aimassist_enabled = aimassist.get("enabled", aimassist_enabled)
        aimassist_keybind = aimassist.get("keybind", aimassist_keybind)
        aimassist_mode = aimassist.get("mode", aimassist_mode)
        aimassist_toggled = False if aimassist_mode == "Hold" else aimassist_toggled
        aimassist_smoothness = aimassist.get("smoothness", aimassist_smoothness)
        aimassist_smooth_enabled = aimassist.get("smooth_enabled", aimassist_smooth_enabled)
        aimassist_hitpart = aimassist.get("hitpart", aimassist_hitpart)
        dpg.set_value("aimassist_enabled", aimassist_enabled)
        dpg.set_value("aimassist_mode_combo", aimassist_mode)
        dpg.set_value("aimassist_smooth_enabled", aimassist_smooth_enabled)
        dpg.set_value("aimassist_smoothness", aimassist_smoothness)
        dpg.set_value("aimassist_hitpart_combo", aimassist_hitpart)
        dpg.configure_item("aimassist_keybind_button", label=f"Keybind: {get_key_name(aimassist_keybind)}")
        dpg.configure_item("config_status", label="")
    except Exception as e:
        dpg.configure_item("config_status", label="")

def delete_config(config_name):
    config_path = os.path.join(CONFIG_DIR, config_name)
    try:
        os.remove(config_path)
        dpg.configure_item("config_combo", items=get_config_files())
        dpg.configure_item("config_status", label="")
    except Exception as e:
        dpg.configure_item("config_status", label="")

def save_config_callback():
    config_name = dpg.get_value("config_name_input")
    if config_name:
        save_config(config_name)
    else:
        dpg.configure_item("config_status", label="")

def load_config_callback():
    config_name = dpg.get_value("config_combo")
    if config_name:
        load_config(config_name)
    else:
        dpg.configure_item("config_status", label="")

def delete_config_callback():
    config_name = dpg.get_value("config_combo")
    if config_name:
        delete_config(config_name)
    else:
        dpg.configure_item("config_status", label="")

def DRP(address: int | str) -> int:
    if isinstance(address, str):
        address = int(address, 16)
    return int.from_bytes(pm.read_bytes(address, 8), "little")

def get_raw_processes():
    return [[
        i.cntThreads, i.cntUsage, i.dwFlags, i.dwSize,
        i.pcPriClassBase, i.szExeFile, i.th32DefaultHeapID,
        i.th32ModuleID, i.th32ParentProcessID, i.th32ProcessID
    ] for i in list_processes()]

def simple_get_processes():
    return [{"Name": i[5].decode(), "Threads": i[0], "ProcessId": i[9]} for i in get_raw_processes()]

def yield_for_program(program_name: str, printInfo: bool = True) -> bool:
    global PID, Handle, baseAddr, pm
    for proc in simple_get_processes():
        if proc["Name"] == program_name:
            pm.open_process_from_id(proc["ProcessId"])
            PID = proc["ProcessId"]
            Handle = windll.kernel32.OpenProcess(0x1038, False, PID)
            if printInfo:
                print('Roblox PID:', PID)
            for module in pm.list_modules():
                if module.name == "RobloxPlayerBeta.exe":
                    baseAddr = module.lpBaseOfDll
                    break
            if printInfo:
                print(f'Roblox base addr: {baseAddr:x}')
            return True
    return False

def is_process_dead() -> bool:
    return not pid_exists(PID)

def get_base_addr() -> int:
    return baseAddr

def setOffsets(nameOffset2: int, childrenOffset2: int):
    global nameOffset, childrenOffset
    nameOffset = nameOffset2
    childrenOffset = childrenOffset2

def ReadRobloxString(expected_address: int) -> str:
    string_count = pm.read_int(expected_address + 0x10)
    if string_count > 15:
        ptr = DRP(expected_address)
        return pm.read_string(ptr, string_count)
    return pm.read_string(expected_address, string_count)

def GetClassName(instance: int) -> str:
    ptr = pm.read_longlong(instance + 0x18)
    ptr = pm.read_longlong(ptr + 0x8)
    fl = pm.read_longlong(ptr + 0x18)
    if fl == 0x1F:
        ptr = pm.read_longlong(ptr)
    return ReadRobloxString(ptr)

def GetNameAddress(instance: int) -> int:
    return DRP(instance + nameOffset)

def GetName(instance: int) -> str:
    return ReadRobloxString(GetNameAddress(instance))

def GetChildren(instance: int) -> list:
    if not instance:
        return []
    children = []
    start = DRP(instance + childrenOffset)
    if start == 0:
        return []
    end = DRP(start + 8)
    current = DRP(start)
    for _ in range(9000):
        if current == end:
            break
        children.append(pm.read_longlong(current))
        current += 0x10
    return children

def FindFirstChild(instance: int, child_name: str) -> int:
    if not instance:
        return 0
    start = DRP(instance + childrenOffset)
    if start == 0:
        return 0
    end = DRP(start + 8)
    current = DRP(start)
    for _ in range(9000):
        if current == end:
            break
        child = pm.read_longlong(current)
        try:
            if GetName(child) == child_name:
                return child
        except:
            pass
        current += 0x10
    return 0

def FindFirstChildOfClass(instance: int, class_name: str) -> int:
    if not instance:
        return 0
    start = DRP(instance + childrenOffset)
    if start == 0:
        return 0
    end = DRP(start + 8)
    current = DRP(start)
    for _ in range(9000):
        if current == end:
            break
        child = pm.read_longlong(current)
        try:
            if GetClassName(child) == class_name:
                return child
        except:
            pass
        current += 0x10
    return 0

def get_key_name(vk_code):
    for name, code in VK_CODES.items():
        if code == vk_code:
            return name
    return f"Key {vk_code}"

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

def lerp(a, b, t):
    return a + (b - a) * min(t, 1.0)

def get_hwid():
    return str(uuid.getnode())

def load_keys():
    response = get('', timeout=5) # yo i removed my github url!
    response.raise_for_status()
    return response.json()

def validate_key(key):
    keys = load_keys()
    hwid = get_hwid()
    return keys.get(key) == hwid

def copy_hwid_callback():
    hwid = get_hwid()
    pyperclip.copy(hwid)
    dpg.configure_item("license_status", label="")

def check_license():
    global license_valid
    keys = load_keys()
    if not keys:
        dpg.configure_item("license_status", label="")
    else:
        dpg.configure_item("license_status", label="")
    dpg.show_item("License Window")
    dpg.hide_item("Primary Window")

def license_submit_callback(sender, app_data):
    global license_valid
    key = dpg.get_value("license_input")
    if validate_key(key):
        license_valid = True
        dpg.hide_item("License Window")
        dpg.show_item("Primary Window")
        dpg.configure_item("license_status", label="")
    else:
        dpg.configure_item("license_status", label="")

print('Finding Lucids offsets pal')
print('xaxaxaxaxaxaxaxa')
response = get('https://offsets.ntgetwritewatch.workers.dev/offsets.json', timeout=5)
response.raise_for_status()
offsets = response.json()
setOffsets(int(offsets['Name'], 16), int(offsets['Children'], 16))

class RECT(Structure):
    _fields_ = [('left', wintypes.LONG), ('top', wintypes.LONG), ('right', wintypes.LONG), ('bottom', wintypes.LONG)]

class POINT(Structure):
    _fields_ = [('x', wintypes.LONG), ('y', wintypes.LONG)]

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

def world_to_screen_with_matrix(world_pos, matrix, screen_width, screen_height):
    vec = array([*world_pos, 1.0], dtype=float32)
    clip = dot(matrix, vec)
    if clip[3] == 0:
        return None
    ndc = clip[:3] / clip[3]
    if ndc[2] < 0 or ndc[2] > 1:
        return None
    x = (ndc[0] + 1) * 0.5 * screen_width
    y = (1 - ndc[1]) * 0.5 * screen_height
    return round(x), round(y)

baseAddr = 0
camAddr = 0
dataModel = 0
wsAddr = 0
camCFrameRotAddr = 0
plrsAddr = 0
lpAddr = 0
matrixAddr = 0
camPosAddr = 0
aimassist_target = 0
aimassist_last_look = array([0, 0, -1], dtype=float32)
aimassist_last_up = array([0, 1, 0], dtype=float32)
aimassist_last_right = array([1, 0, 0], dtype=float32)
aimassist_last_time = time()
aimassist_target_char = 0
aimassist_last_target_pos = None

def initialize_injection():
    global baseAddr, dataModel, wsAddr, camAddr, camCFrameRotAddr, plrsAddr, lpAddr, matrixAddr, camPosAddr, injected
    while not injected:
        try:
            if is_process_dead():
                while not yield_for_program("RobloxPlayerBeta.exe", printInfo=False):
                    sleep(0.5)
                baseAddr = get_base_addr()
            pm.open_process_from_id(PID)
            fakeDatamodel = pm.read_longlong(baseAddr + int(offsets['FakeDataModelPointer'], 16))
            dataModel = pm.read_longlong(fakeDatamodel + int(offsets['FakeDataModelToDataModel'], 16))
            wsAddr = FindFirstChildOfClass(dataModel, 'Workspace')
            camAddr = FindFirstChildOfClass(wsAddr, 'Camera')
            camCFrameRotAddr = camAddr + int(offsets['CameraRotation'], 16)
            camPosAddr = camAddr + int(offsets['CameraPos'], 16)
            visualEngine = pm.read_longlong(baseAddr + int(offsets['VisualEnginePointer'], 16))
            matrixAddr = visualEngine + int(offsets['viewmatrix'], 16)
            plrsAddr = FindFirstChildOfClass(dataModel, 'Players')
            lpAddr = pm.read_longlong(plrsAddr + int(offsets['LocalPlayer'], 16))
            injected = True
            print('finished getting the offsets for lucid brotatochip')
        except ProcessError as e:
            print(f'Injection failed: {str(e)}')
            sleep(1)

def monitor_process():
    global baseAddr, injected
    while True:
        if is_process_dead():
            injected = False
            while not yield_for_program("RobloxPlayerBeta.exe", printInfo=False):
                sleep(0.5)
            baseAddr = get_base_addr()
            initialize_injection()
        sleep(0.1)

Thread(target=monitor_process, daemon=True).start()

def keybind_listener():
    global waiting_for_aimassist_keybind, aimassist_keybind
    while True:
        if waiting_for_aimassist_keybind:
            sleep(0.3)
            for vk_code in range(1, 256):
                windll.user32.GetAsyncKeyState(vk_code)
            key_found = False
            while waiting_for_aimassist_keybind and not key_found:
                for vk_code in range(1, 256):
                    if windll.user32.GetAsyncKeyState(vk_code) & 0x8000:
                        if vk_code == 27:  # ESC
                            waiting_for_aimassist_keybind = False
                            dpg.configure_item("aimassist_keybind_button", label=f"Keybind: {get_key_name(aimassist_keybind)}")
                            break
                        aimassist_keybind = vk_code
                        waiting_for_aimassist_keybind = False
                        dpg.configure_item("aimassist_keybind_button", label=f"Keybind: {get_key_name(vk_code)}")
                        key_found = True
                        break
                sleep(0.01)
        else:
            sleep(0.1)

Thread(target=keybind_listener, daemon=True).start()

def aimAssistLoop():
    global aimassist_target, aimassist_toggled, aimassist_last_look, aimassist_last_up, aimassist_last_right, aimassist_last_time, aimassist_target_char, aimassist_last_target_pos
    key_pressed_last_frame = False
    parts = ["Head", "UpperTorso", "HumanoidRootPart", "LowerTorso", "LeftHand", "RightHand", "LeftFoot", "RightFoot"]
    aimassist_fov = 300
    deadzone = 5
    while True:
        if aimassist_enabled and license_valid:
            key_pressed_this_frame = windll.user32.GetAsyncKeyState(aimassist_keybind) & 0x8000 != 0
            if aimassist_mode == "Toggle":
                if key_pressed_this_frame and not key_pressed_last_frame:
                    aimassist_toggled = not aimassist_toggled
                key_pressed_last_frame = key_pressed_this_frame
                should_aim = aimassist_toggled
            else:
                should_aim = key_pressed_this_frame
            if should_aim:
                hwnd_roblox = find_window_by_title("Roblox")
                if hwnd_roblox and matrixAddr > 0:
                    left, top, right, bottom = get_client_rect_on_screen(hwnd_roblox)
                    matrix_flat = [pm.read_float(matrixAddr + i * 4) for i in range(16)]
                    view_proj_matrix = reshape(array(matrix_flat, dtype=float32), (4, 4))
                    width = right - left
                    height = bottom - top
                    widthCenter = width / 2
                    heightCenter = height / 2
                    minDistance = float('inf')
                    aimassist_target = 0
                    aimassist_target_char = 0
                    for v in GetChildren(plrsAddr):
                        if v != lpAddr:
                            char = pm.read_longlong(v + int(offsets['ModelInstance'], 16))
                            hum = FindFirstChildOfClass(char, 'Humanoid')
                            if not hum:
                                continue
                            target_part = aimassist_hitpart if aimassist_hitpart != "Closest Part" else None
                            if target_part:
                                part = FindFirstChild(char, target_part)
                                if part:
                                    primitive = pm.read_longlong(part + int(offsets['Primitive'], 16))
                                    targetPos = primitive + int(offsets['Position'], 16)
                                    obj_pos = array([
                                        pm.read_float(targetPos),
                                        pm.read_float(targetPos + 4),
                                        pm.read_float(targetPos + 8)
                                    ], dtype=float32)
                                    screen_coords = world_to_screen_with_matrix(obj_pos, view_proj_matrix, width, height)
                                    if screen_coords is not None:
                                        distance = sqrt((widthCenter - screen_coords[0])**2 + (heightCenter - screen_coords[1])**2)
                                        if distance < aimassist_fov and distance < minDistance:
                                            minDistance = distance
                                            aimassist_target = targetPos
                                            aimassist_target_char = char
                            else:
                                part_distances = []
                                for part_name in parts:
                                    part = FindFirstChild(char, part_name)
                                    if part:
                                        primitive = pm.read_longlong(part + int(offsets['Primitive'], 16))
                                        targetPos = primitive + int(offsets['Position'], 16)
                                        obj_pos = array([
                                            pm.read_float(targetPos),
                                            pm.read_float(targetPos + 4),
                                            pm.read_float(targetPos + 8)
                                        ], dtype=float32)
                                        screen_coords = world_to_screen_with_matrix(obj_pos, view_proj_matrix, width, height)
                                        if screen_coords is not None:
                                            distance = sqrt((widthCenter - screen_coords[0])**2 + (heightCenter - screen_coords[1])**2)
                                            if distance < aimassist_fov:
                                                part_distances.append((part_name, distance, targetPos, char))
                                if part_distances:
                                    part_distances.sort(key=lambda x: x[1])
                                    _, distance, targetPos, char = part_distances[0]
                                    if distance < minDistance:
                                        minDistance = distance
                                        aimassist_target = targetPos
                                        aimassist_target_char = char
                    if aimassist_target > 0:
                        try:
                            from_pos = [pm.read_float(camPosAddr), pm.read_float(camPosAddr+4), pm.read_float(camPosAddr+8)]
                            to_pos = [pm.read_float(aimassist_target), pm.read_float(aimassist_target+4), pm.read_float(aimassist_target+8)]
                            aimassist_last_target_pos = to_pos
                        except:
                            to_pos = aimassist_last_target_pos if aimassist_last_target_pos else [0, 0, 0]
                        target_look, target_up, target_right = cframe_look_at(from_pos, to_pos)
                        current_right = array([
                            -pm.read_float(camCFrameRotAddr),
                            -pm.read_float(camCFrameRotAddr+12),
                            -pm.read_float(camCFrameRotAddr+24)
                        ], dtype=float32)
                        current_up = array([
                            pm.read_float(camCFrameRotAddr+4),
                            pm.read_float(camCFrameRotAddr+16),
                            pm.read_float(camCFrameRotAddr+28)
                        ], dtype=float32)
                        current_look = array([
                            -pm.read_float(camCFrameRotAddr+8),
                            -pm.read_float(camCFrameRotAddr+20),
                            -pm.read_float(camCFrameRotAddr+32)
                        ], dtype=float32)
                        distance = linalg.norm(array(to_pos) - array(from_pos))
                        smooth_factor = aimassist_smoothness * (1 + min(distance / 50, 2))
                        if aimassist_smooth_enabled:
                            current_time = time()
                            delta_time = min(current_time - aimassist_last_time, 0.016)
                            t = smooth_factor * delta_time * 15.0
                            look = lerp(current_look, target_look, t)
                            up = lerp(current_up, target_up, t)
                            right = lerp(current_right, target_right, t)
                            aimassist_last_time = current_time
                        else:
                            look, up, right = target_look, target_up, target_right
                            aimassist_last_time = time()
                        angle_diff = abs(atan2(look[1], look[0]) - atan2(current_look[1], current_look[0])) * 180 / pi
                        if angle_diff > deadzone / 1000:
                            aimassist_last_look, aimassist_last_up, aimassist_last_right = look, up, right
                            pm.write_float(camCFrameRotAddr, float(-right[0]))
                            pm.write_float(camCFrameRotAddr+4, float(up[0]))
                            pm.write_float(camCFrameRotAddr+8, float(-look[0]))
                            pm.write_float(camCFrameRotAddr+12, float(-right[1]))
                            pm.write_float(camCFrameRotAddr+16, float(up[1]))
                            pm.write_float(camCFrameRotAddr+20, float(-look[1]))
                            pm.write_float(camCFrameRotAddr+24, float(-right[2]))
                            pm.write_float(camCFrameRotAddr+28, float(up[2]))
                            pm.write_float(camCFrameRotAddr+32, float(-look[2]))
            else:
                aimassist_target = 0
                aimassist_target_char = 0
                aimassist_last_target_pos = None
            sleep(0.005)
        else:
            aimassist_toggled = False
            aimassist_last_target_pos = None
            sleep(0.05)

def aimassist_callback(sender, app_data):
    global aimassist_enabled, aimassist_toggled
    aimassist_enabled = app_data
    aimassist_toggled = False if not aimassist_enabled else aimassist_toggled

def aimassist_mode_callback(sender, app_data):
    global aimassist_mode, aimassist_toggled
    aimassist_mode = app_data
    if aimassist_mode == "Hold":
        aimassist_toggled = False

def aimassist_smoothness_callback(sender, app_data):
    global aimassist_smoothness
    aimassist_smoothness = app_data

def aimassist_smooth_enabled_callback(sender, app_data):
    global aimassist_smooth_enabled
    aimassist_smooth_enabled = app_data

def aimassist_hitpart_callback(sender, app_data):
    global aimassist_hitpart
    aimassist_hitpart = app_data

def aimassist_keybind_callback():
    global waiting_for_aimassist_keybind
    if not waiting_for_aimassist_keybind:
        waiting_for_aimassist_keybind = True
        dpg.configure_item("aimassist_keybind_button", label="... (ESC to cancel)")

Thread(target=aimAssistLoop, daemon=True).start()

dpg.create_context()

with dpg.theme() as global_theme:
    with dpg.theme_component(dpg.mvAll):
        dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (10, 10, 13, 255))
        dpg.add_theme_color(dpg.mvThemeCol_Text, (235, 235, 240, 255))
        dpg.add_theme_color(dpg.mvThemeCol_MenuBarBg, (25, 25, 30, 230))
        dpg.add_theme_color(dpg.mvThemeCol_Header, (220, 70, 150, 120))
        dpg.add_theme_color(dpg.mvThemeCol_HeaderHovered, (230, 80, 160, 160))
        dpg.add_theme_color(dpg.mvThemeCol_HeaderActive, (240, 90, 170, 200))
        dpg.add_theme_color(dpg.mvThemeCol_Button, (45, 25, 40, 220))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonHovered, (230, 80, 160, 200))
        dpg.add_theme_color(dpg.mvThemeCol_ButtonActive, (240, 90, 170, 255))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (25, 25, 35, 255))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgHovered, (40, 25, 45, 255))
        dpg.add_theme_color(dpg.mvThemeCol_FrameBgActive, (60, 30, 60, 255))
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrab, (230, 80, 160, 255))
        dpg.add_theme_color(dpg.mvThemeCol_SliderGrabActive, (240, 100, 180, 255))
        dpg.add_theme_color(dpg.mvThemeCol_Border, (40, 40, 50, 255))
        dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, (0, 0, 0, 0))
        dpg.add_theme_color(dpg.mvThemeCol_TitleBg, (40, 25, 40, 255))
        dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, (230, 80, 160, 255))
        dpg.add_theme_color(dpg.mvThemeCol_TitleBgCollapsed, (30, 20, 30, 255))
        dpg.add_theme_color(dpg.mvThemeCol_Tab, (45, 30, 50, 255))
        dpg.add_theme_color(dpg.mvThemeCol_TabHovered, (230, 80, 160, 200))
        dpg.add_theme_color(dpg.mvThemeCol_TabActive, (240, 100, 180, 255))
        dpg.add_theme_color(dpg.mvThemeCol_CheckMark, (240, 100, 180, 255))
        dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6)
        dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 7)
        dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 9)
        dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 10, 6)
        dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 10, 8)
        dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 10, 10)
        dpg.add_theme_style(dpg.mvStyleVar_GrabRounding, 8)
        dpg.add_theme_color(dpg.mvThemeCol_NavHighlight, (240, 100, 180, 200))
        dpg.add_theme_color(dpg.mvThemeCol_NavWindowingHighlight, (240, 100, 180, 120))
        dpg.add_theme_color(dpg.mvThemeCol_NavWindowingDimBg, (0, 0, 0, 80))

dpg.bind_theme(global_theme)

with dpg.window(label="License Validation", tag="License Window", width=250, height=300, no_close=True):
    dpg.add_text("Enter License Key:", color=(200, 200, 200))
    dpg.add_input_text(tag="license_input", hint="License Key")
    dpg.add_button(label="Submit", tag="license_submit", callback=license_submit_callback)
    dpg.add_button(label="Copy HWID", callback=copy_hwid_callback)
    dpg.add_text("", tag="license_status")

with dpg.window(label="Chumpz Early Build", tag="Primary Window", width=800, height=700, show=False, no_title_bar=True, no_resize=True, no_move=True, no_collapse=True):
    dpg.add_text("Chumpzzz on top also lmk how you like the gui", color=(200, 200, 200))
    dpg.add_spacer()
    with dpg.tab_bar():
        with dpg.tab(label="Aim Assist"):
            with dpg.group(horizontal=True):
                dpg.add_checkbox(label="Enable Aim Assist", tag="aimassist_enabled", default_value=aimassist_enabled, callback=aimassist_callback)
                dpg.add_spacer(width=10)
                dpg.add_button(label=f"Keybind: {get_key_name(aimassist_keybind)}", tag="aimassist_keybind_button", callback=aimassist_keybind_callback)
            dpg.add_combo(["Hold", "Toggle"], default_value=aimassist_mode, tag="aimassist_mode_combo", callback=aimassist_mode_callback, width=100)
            dpg.add_checkbox(label="Enable Smoothness", default_value=aimassist_smooth_enabled, tag="aimassist_smooth_enabled", callback=aimassist_smooth_enabled_callback)
            dpg.add_slider_float(label="Smoothness", default_value=aimassist_smoothness, min_value=0.0, max_value=1.0, tag="aimassist_smoothness", callback=aimassist_smoothness_callback, width=100)
            dpg.add_combo(["Closest Part", "Head", "UpperTorso", "HumanoidRootPart", "LowerTorso", "LeftHand", "RightHand", "LeftFoot", "RightFoot"], default_value=aimassist_hitpart, tag="aimassist_hitpart_combo", callback=aimassist_hitpart_callback, width=100)
        with dpg.tab(label="Configs"):
            dpg.add_text("Configuration", color=(200, 200, 200))
            dpg.add_combo(get_config_files(), label="Select Config", tag="config_combo", width=200)
            dpg.add_input_text(label="Config Name", tag="config_name_input", hint="Enter config name")
            with dpg.group(horizontal=True):
                dpg.add_button(label="Save Config", callback=save_config_callback)
                dpg.add_button(label="Load Config", callback=load_config_callback)
                dpg.add_button(label="Delete Config", callback=delete_config_callback)
            dpg.add_text("", tag="config_status")
    dpg.add_spacer()
    dpg.add_separator()
    dpg.add_spacer()
    dpg.add_button(label="Close", callback=lambda: dpg.hide_item("Primary Window"))

dpg.create_viewport(title="Chumpz Early Build", width=800, height=700)
dpg.setup_dearpygui()
check_license()
Thread(target=initialize_injection, daemon=True).start()
dpg.show_viewport()
dpg.start_dearpygui()
dpg.destroy_context()