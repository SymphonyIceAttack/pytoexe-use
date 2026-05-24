"""
BlueStacks Customizer - PRIMEx Edition
Complete all-in-one tool with all Pro features unlocked.
Branding: PRIMEx | YouTube: @PRIME_H.4X | Discord: https://discord.gg/mj6RjjZCmA
"""

# ----------------------------------------------------------------------
# Imports
# ----------------------------------------------------------------------
import glfw
from OpenGL.GL import *
import imgui
from imgui.integrations.glfw import GlfwRenderer
import shutil
import os
import hashlib
import json
import webbrowser
import subprocess
from tkinter import Tk, filedialog
import sys
import time
import psutil
import re
import ctypes
from ctypes import wintypes

# ----------------------------------------------------------------------
# PRO VERSION UNLOCKED
# ----------------------------------------------------------------------
PRO_VERSION = True   # <-- All Pro features enabled

# ----------------------------------------------------------------------
# Branding
# ----------------------------------------------------------------------
BRAND_NAME = "PRIMEx"
YT_CHANNEL = "https://www.youtube.com/@PRIME_H.4X/videos"
DISCORD_INVITE = "https://discord.gg/mj6RjjZCmA"

# ----------------------------------------------------------------------
# Constants & Configuration
# ----------------------------------------------------------------------
DEFAULT_PATHS = {
    'MSI5': {
        'exe': r'C:\Program Files\BlueStacks_msi5\HD-Player.exe',
        'conf': r'C:\ProgramData\BlueStacks_msi5\bluestacks.conf',
        'opengl_dll': r'C:\Program Files\BlueStacks_msi5\libOpenglRender.dll',
        'native_dll': r'C:\Program Files\BlueStacks_msi5\HD-Opengl-Native.dll'
    },
    'NXT': {
        'exe': r'C:\Program Files\BlueStacks_nxt\HD-Player.exe',
        'conf': r'C:\ProgramData\BlueStacks_nxt\bluestacks.conf',
        'opengl_dll': r'C:\Program Files\BlueStacks_nxt\libOpenglRender.dll',
        'native_dll': r'C:\Program Files\BlueStacks_nxt\HD-Opengl-Native.dll'
    }
}

ROUND_CORNER_DLL = 'version.dll'

if getattr(sys, 'frozen', False):
    APP_DIR = os.path.dirname(sys.executable)
else:
    APP_DIR = os.path.dirname(os.path.abspath(__file__))

BACKUP_DIR = os.path.join(APP_DIR, 'backup')
DLL_BACKUP_DIR = os.path.join(APP_DIR, 'dll_backups')
ORIG_BACKUP_DIR = os.path.join(APP_DIR, 'original_backup')
COLOR_CACHE_FILE = os.path.join(APP_DIR, 'color_cache.json')
FPS_CACHE_FILE = os.path.join(APP_DIR, 'fps_cache.json')
THEME_CACHE_FILE = os.path.join(APP_DIR, 'theme_cache.json')
SETTINGS_EXPORT_FILE = os.path.join(APP_DIR, 'settings.json')

KNOWN_VERSIONS = ['5.9.300.6315', '5.11.100.6311', '5.12.120.6303',
                  '5.21.151.6303', '5.21.152.6301']

INSTANCE_PATTERNS = {
    'Nougat32':   {'pattern': 'N32', 'display': 'N32', 'max_len': 3, 'conf_key': 'Nougat32'},
    'Pie64':      {'pattern': 'P64', 'display': 'P64', 'max_len': 3, 'conf_key': 'Pie64'},
    'Nougat64':   {'pattern': 'N64', 'display': 'N64', 'max_len': 3, 'conf_key': 'Nougat64'},
    'Rvc64':      {'pattern': 'Android 11', 'display': 'Android 11', 'max_len': 10, 'conf_key': 'Rvc64'},
    'Tiramisu64': {'pattern': 'Tiramisu64', 'display': 'Tiramisu64', 'max_len': 11, 'conf_key': 'Tiramisu64'}
}

ANDROID_VERSIONS = {
    'N32': 'Android 7.1.2',
    'N64': 'Android 7.1.2 64 bit',
    'P64': 'Android 9 Pie',
    'Rvc64': 'Android 11',
    'Android 11': 'Android 11',
    'Tiramisu64': 'Android 13 (Beta)'
}

# Removal patterns (hex strings converted to bytes)
REMOVE_STRINGS_HEX = {
    'Titlebar Help': '54 00 69 00 74 00 6C 00 65 00 62 00 61 00 72 00 48 00 65 00 6C 00 70 00',
    'Sidebar InstanceManager': '53 00 69 00 64 00 65 00 62 00 61 00 72 00 49 00 6E 00 73 00 74 00 61 00 6E 00 63 00 65 00 4D 00 61 00 6E 00 61 00 67 00 65 00 72 00 2E 00 73 00 76 00 67 00',
    'Sidebar Rotate': '53 00 69 00 64 00 65 00 62 00 61 00 72 00 52 00 6F 00 74 00 61 00 74 00 65 00 2E 00 73 00 76 00 67 00',
    'Sidebar Location': '53 00 69 00 64 00 65 00 62 00 61 00 72 00 4C 00 6F 00 63 00 61 00 74 00 69 00 6F 00 6E 00 2E 00 73 00 76 00 67 00',
    'Sidebar Shake': '53 00 69 00 64 00 65 00 62 00 61 00 72 00 53 00 68 00 61 00 6B 00 65 00 2E 00 73 00 76 00 67 00',
    'Sidebar Macro': '53 00 69 00 64 00 65 00 62 00 61 00 72 00 4D 00 61 00 63 00 72 00 6F 00 2E 00 73 00 76 00 67 00',
    'Sidebar Screenshot': '53 00 69 00 64 00 65 00 62 00 61 00 72 00 53 00 63 00 72 00 65 00 65 00 6E 00 73 00 68 00 6F 00 74 00 2E 00 73 00 76 00 67 00',
    'Sidebar MediaFolder': '53 00 69 00 64 00 65 00 62 00 61 00 72 00 4D 00 65 00 64 00 69 00 61 00 46 00 6F 00 6C 00 64 00 65 00 72 00 2E 00 73 00 76 00 67 00',
    'Sidebar Fullscreen': '53 00 69 00 64 00 65 00 62 00 61 00 72 00 46 00 75 00 6C 00 6C 00 53 00 63 00 72 00 65 00 65 00 6E 00 2E 00 73 00 76 00 67 00',
    'Sidebar Airplane Mode': '41 00 69 00 72 00 70 00 6C 00 61 00 6E 00 65 00 4D 00 6F 00 64 00 65 00 4F 00 66 00 66 00 2E 00 73 00 76 00 67 00',
    'Sidebar Sync Mode': '53 00 69 00 64 00 65 00 62 00 61 00 72 00 53 00 79 00 6E 00 63 00 2E 00 73 00 76 00 67 00',
    'Sidebar Lock Cursor': '53 00 69 00 64 00 65 00 62 00 61 00 72 00 4C 00 6F 00 63 00 6B 00 43 00 75 00 72 00 73 00 6F 00 72 00 2E 00 73 00 76 00 67 00',
    'Sidebar Eco Mode': '53 00 69 00 64 00 65 00 62 00 61 00 72 00 45 00 63 00 6F 00 4D 00 6F 00 64 00 65 00 2E 00 73 00 76 00 67 00',
    'Titlebar Logo': '42 00 6C 00 75 00 65 00 53 00 74 00 61 00 63 00 6B 00 73 00 4C 00 6F 00 67 00 6F 00 2E 00 73 00 76 00 67 00',
    'Sidebar Side Panel': '53 00 69 00 64 00 65 00 62 00 61 00 72 00 53 00 69 00 64 00 65 00 50 00 61 00 6E 00 65 00 6C',
    'Sidebar Screen Record': '53 00 69 00 64 00 65 00 62 00 61 00 72 00 53 00 63 00 72 00 65 00 65 00 6E 00 52 00 65 00 63 00 6F 00 72 00 64 00 2E 00 73 00 76 00 67 00',
    'Titlebar Menu': '54 00 69 00 74 00 6C 00 65 00 62 00 61 00 72 00 4D 00 65 00 6E 00 75 00 2E 00 73 00 76 00 67 00',
    'Titlebar Version': '76 00 65 00 72 00 73 00 69 00 6F 00 6E 00'
}
REMOVE_STRINGS = {k: bytes.fromhex(v) for k, v in REMOVE_STRINGS_HEX.items()}
remove_state = {k: False for k in REMOVE_STRINGS}

CONTEXTUAL_REMOVALS = [
    {'name': 'Clean Boot Screen',
     'search_hex': '5A 00 6F 00 6F 00 6D 00 20 00 49 00 6E 00 2F 00 4F 00 75 00 74 00 20 00 69 00 6E 00 2D 00 67 00 61 00 6D 00 65 00 2C 00 20 00 70 00 72 00 65 00 73 00 73 00 20 00 43 00 54 00 52 00 4C 00 2B 00 4D 00 6F 00 75 00 73 00 65 00 77 00 68 00 65 00 65 00 6C 00 20 00 55 00 70 00 2F 00 44 00 6F 00 77 00 6E 00',
     'target_hex': '71 00 73 00 54 00 72 00 61 00 6E 00 73 00 6C 00 61 00 74 00 65 00',
     'replace_with': 'spaces'},
    {'name': 'Titlebar Home',
     'search_hex': '69 00 48 00 6F 00 6D 00 65 00 42 00 74 00 6E 00',
     'target_hex': '53 00 69 00 64 00 65 00 62 00 61 00 72 00 48 00 6F 00 6D 00 65 00',
     'replace_with': 'null'},
    {'name': 'Titlebar Recents',
     'search_hex': '69 00 52 00 65 00 63 00 65 00 6E 00 74 00 42 00 74 00 6E 00',
     'target_hex': '53 00 69 00 64 00 65 00 62 00 61 00 72 00 52 00 65 00 63 00 65 00 6E 00 74 00 73 00',
     'replace_with': 'null'},
    {'name': 'Titlebar Back',
     'search_hex': '69 00 42 00 61 00 63 00 6B 00 42 00 74 00 6E 00',
     'target_hex': '53 00 69 00 64 00 65 00 62 00 61 00 72 00 42 00 61 00 63 00 6B 00',
     'replace_with': 'null'}
]
for item in CONTEXTUAL_REMOVALS:
    item['search_hex'] = bytes.fromhex(item['search_hex'])
    item['target_hex'] = bytes.fromhex(item['target_hex'])

contextual_remove_state = {item['name']: False for item in CONTEXTUAL_REMOVALS}
FREE_REMOVALS = {'Titlebar Version', 'Titlebar Logo', 'Clean Boot Screen'}

# Color targets
COLOR_TARGETS_MSI5 = {
    'Sidebar (#000000)': ('#000000', 'utf16'),
    'Settings Window': ('#21242C', 'utf16'),
    'Toggle Button': ('#ED1C24', 'ascii'),
    'Toggle Hover': ('#FF333B', 'ascii'),
    'Cursor/Slider/Border': ('#EB2C43', 'both'),
    'Hover Accent': ('#454954', 'both'),
    'Click Color': ('#17181C', 'both'),
    'Shadow Color': ('#0B0C0E', 'both'),
    'Keymap Item Hover': ('#5C6170', 'both'),
    'Close Button Click': ('#C61017', 'both'),
    'Close Button Hover': ('#131621', 'utf16')
}

COLOR_TARGETS_NXT = {
    'Sidebar/Topbar': ('#232642', 'utf16'),
    'Slider': ('#1a90ff', 'utf16'),
    'Toggle Button': ('#1a90ff', 'ascii'),
    'Toggle Button Hover': ('#2ea4ff', 'ascii'),
    'Combobox': ('#1b1e38', 'utf16')
}

COLOR_PRESETS_MSI5 = {
    'Neon': {
        'Sidebar (#000000)': '#0d0d0d',
        'Settings Window': '#1a1a2e',
        'Toggle Button': '#ff007f',
        'Toggle Hover': '#ff3399',
        'Cursor/Slider/Border': '#ff007f',
        'Hover Accent': '#2a2a4a',
        'Click Color': '#111122',
        'Shadow Color': '#050510',
        'Keymap Item Hover': '#2a2a4a',
        'Close Button Click': '#cc0066',
        'Close Button Hover': '#1a1a2e'
    },
    'Ocean': {
        'Sidebar (#000000)': '#0a192f',
        'Settings Window': '#112240',
        'Toggle Button': '#64ffda',
        'Toggle Hover': '#9effe6',
        'Cursor/Slider/Border': '#64ffda',
        'Hover Accent': '#233554',
        'Click Color': '#1d3461',
        'Shadow Color': '#020c1b',
        'Keymap Item Hover': '#233554',
        'Close Button Click': '#52d1b2',
        'Close Button Hover': '#112240'
    },
    'Sunset': {
        'Sidebar (#000000)': '#0a1f0a',
        'Settings Window': '#1a2e1a',
        'Toggle Button': '#ff5722',
        'Toggle Hover': '#ff7043',
        'Cursor/Slider/Border': '#ff5722',
        'Hover Accent': '#2a4a2a',
        'Click Color': '#112211',
        'Shadow Color': '#050a05',
        'Keymap Item Hover': '#2a4a2a',
        'Close Button Click': '#cc4411',
        'Close Button Hover': '#1a2e1a'
    }
}
COLOR_PRESETS_NXT = {
    'Neon': {
        'Sidebar/Topbar': '#0d0d0d',
        'Slider': '#ff007f',
        'Toggle Button': '#ff007f',
        'Toggle Button Hover': '#ff3399',
        'Combobox': '#1a1a2e'
    },
    'Ocean': {
        'Sidebar/Topbar': '#0a192f',
        'Slider': '#64ffda',
        'Toggle Button': '#64ffda',
        'Toggle Button Hover': '#9effe6',
        'Combobox': '#112240'
    },
    'Sunset': {
        'Sidebar/Topbar': '#1f0a0a',
        'Slider': '#ff5722',
        'Toggle Button': '#ff5722',
        'Toggle Button Hover': '#ff7043',
        'Combobox': '#2d1810'
    }
}

# GUI Themes
THEMES = {
    'Glacier': {
        'window_bg': (0.04, 0.06, 0.08, 0.95),
        'child_bg': (0.06, 0.08, 0.1, 0.95),
        'frame_bg': (0.12, 0.15, 0.18, 0.95),
        'frame_hovered': (0.18, 0.22, 0.26, 0.95),
        'frame_active': (0.24, 0.28, 0.32, 0.95),
        'text': (0.88, 0.9, 0.93, 1.0),
        'text_disabled': (0.5, 0.5, 0.5, 1.0),
        'check_mark': (0.26, 0.3, 0.34, 1.0),
        'button': (0.12, 0.15, 0.18, 1.0),
        'button_hovered': (0.18, 0.22, 0.26, 1.0),
        'button_active': (0.36, 0.4, 0.44, 1.0),
        'header': (0.08, 0.1, 0.12, 1.0),
        'header_hovered': (0.12, 0.15, 0.18, 1.0),
        'header_active': (0.18, 0.22, 0.26, 1.0),
        'border': (0.12, 0.15, 0.18, 0.5),
        'title_bg': (0.24, 0.18, 0.88, 1.0),
        'title_bg_active': (0.3, 0.22, 1.0, 1.0)
    },
    'Light': {
        'window_bg': (0.95, 0.95, 0.98, 0.95),
        'child_bg': (0.98, 0.98, 1.0, 0.95),
        'frame_bg': (0.9, 0.9, 0.93, 0.95),
        'frame_hovered': (0.85, 0.85, 0.88, 0.95),
        'frame_active': (0.8, 0.8, 0.83, 0.95),
        'text': (0.1, 0.1, 0.13, 1.0),
        'text_disabled': (0.5, 0.5, 0.5, 1.0),
        'check_mark': (0.2, 0.2, 0.25, 1.0),
        'button': (0.9, 0.9, 0.93, 1.0),
        'button_hovered': (0.85, 0.85, 0.88, 1.0),
        'button_active': (0.75, 0.75, 0.78, 1.0),
        'header': (0.9, 0.9, 0.93, 1.0),
        'header_hovered': (0.85, 0.85, 0.88, 1.0),
        'header_active': (0.8, 0.8, 0.83, 1.0),
        'border': (0.6, 0.6, 0.65, 0.5),
        'title_bg': (0.8, 0.8, 0.9, 1.0),
        'title_bg_active': (0.7, 0.7, 0.8, 1.0)
    },
    'Forest': {
        'window_bg': (0.05, 0.1, 0.05, 0.95),
        'child_bg': (0.07, 0.12, 0.07, 0.95),
        'frame_bg': (0.1, 0.18, 0.1, 0.95),
        'frame_hovered': (0.15, 0.25, 0.15, 0.95),
        'frame_active': (0.2, 0.3, 0.2, 0.95),
        'text': (0.85, 0.95, 0.85, 1.0),
        'text_disabled': (0.5, 0.6, 0.5, 1.0),
        'check_mark': (0.3, 0.7, 0.3, 1.0),
        'button': (0.1, 0.2, 0.1, 1.0),
        'button_hovered': (0.15, 0.28, 0.15, 1.0),
        'button_active': (0.2, 0.35, 0.2, 1.0),
        'header': (0.08, 0.15, 0.08, 1.0),
        'header_hovered': (0.12, 0.22, 0.12, 1.0),
        'header_active': (0.18, 0.3, 0.18, 1.0),
        'border': (0.2, 0.4, 0.2, 0.5),
        'title_bg': (0.1, 0.2, 0.1, 1.0),
        'title_bg_active': (0.15, 0.3, 0.15, 1.0)
    }
}

THEMES_KEY_MAP = {
    imgui.COLOR_WINDOW_BACKGROUND: 'window_bg',
    imgui.COLOR_CHILD_BACKGROUND: 'child_bg',
    imgui.COLOR_FRAME_BACKGROUND: 'frame_bg',
    imgui.COLOR_FRAME_BACKGROUND_HOVERED: 'frame_hovered',
    imgui.COLOR_FRAME_BACKGROUND_ACTIVE: 'frame_active',
    imgui.COLOR_TEXT: 'text',
    imgui.COLOR_TEXT_DISABLED: 'text_disabled',
    imgui.COLOR_CHECK_MARK: 'check_mark',
    imgui.COLOR_BUTTON: 'button',
    imgui.COLOR_BUTTON_HOVERED: 'button_hovered',
    imgui.COLOR_BUTTON_ACTIVE: 'button_active',
    imgui.COLOR_HEADER: 'header',
    imgui.COLOR_HEADER_HOVERED: 'header_hovered',
    imgui.COLOR_HEADER_ACTIVE: 'header_active',
    imgui.COLOR_BORDER: 'border',
    imgui.COLOR_TITLE_BACKGROUND: 'title_bg',
    imgui.COLOR_TITLE_BACKGROUND_ACTIVE: 'title_bg_active'
}

# ----------------------------------------------------------------------
# Global State Variables
# ----------------------------------------------------------------------
active_profile = 'MSI5'
profile_paths = {'MSI5': dict(DEFAULT_PATHS['MSI5']), 'NXT': dict(DEFAULT_PATHS['NXT'])}
instance_conf_inputs = {}
logs = []
current_tab = 0
log_filter_text = ''
show_backup_manager = False
ui_scale_value = '1.00'
window_maximized = False
dragging = False
drag_start_x = drag_start_y = 0

version_state = {
    'MSI5': {'found': '', 'offset': -1, 'encoding': 'ascii', 'text': '', 'max_len': 0, 'original': ''},
    'NXT':  {'found': '', 'offset': -1, 'encoding': 'ascii', 'text': '', 'max_len': 0, 'original': ''}
}

available_instances = {'MSI5': [], 'NXT': []}
instance_states = {'MSI5': {}, 'NXT': {}}
original_instance_names = {'MSI5': {}, 'NXT': {}}

opengl_version = '3.3'
round_corners_status = False

fps_dll_names = ['libOpenglRender.dll', 'HD-Opengl-Native.dll']
fps_max_len = 7
fps_last_text = ''
fps_text_user = ''
fps_status = {'found': {}, 'custom': False}

current_theme = 'Glacier'
prev_theme = current_theme
next_theme = current_theme
theme_transition_time = 0.0
transition_duration = 0.5

# ----------------------------------------------------------------------
# Helper Functions
# ----------------------------------------------------------------------
def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def add_log(text, level='info'):
    timestamp = time.strftime('%H:%M:%S')
    prefix = '[OK]' if level == 'success' else \
             '[ERROR]' if level == 'error' else \
             '[WARN]' if level == 'warning' else '[INFO]'
    logs.append(f'{timestamp} {prefix} {text}')
    if len(logs) > 200:
        logs.pop(0)

def get_file_version(file_path):
    try:
        size = ctypes.windll.version.GetFileVersionInfoSizeW(file_path, None)
        if not size:
            return ''
        res = ctypes.create_string_buffer(size)
        ctypes.windll.version.GetFileVersionInfoW(file_path, 0, size, res)
        lptr = ctypes.c_void_p()
        uLen = wintypes.UINT()
        ctypes.windll.version.VerQueryValueW(res, '\\', ctypes.byref(lptr), ctypes.byref(uLen))
        if uLen.value == 0:
            return ''
        class VS_FIXEDFILEINFO(ctypes.Structure):
            _fields_ = [
                ('dwSignature', wintypes.DWORD),
                ('dwStrucVersion', wintypes.DWORD),
                ('dwFileVersionMS', wintypes.DWORD),
                ('dwFileVersionLS', wintypes.DWORD),
                ('dwProductVersionMS', wintypes.DWORD),
                ('dwProductVersionLS', wintypes.DWORD),
                ('dwFileFlagsMask', wintypes.DWORD),
                ('dwFileFlags', wintypes.DWORD),
                ('dwFileOS', wintypes.DWORD),
                ('dwFileType', wintypes.DWORD),
                ('dwFileSubtype', wintypes.DWORD),
                ('dwFileDateMS', wintypes.DWORD),
                ('dwFileDateLS', wintypes.DWORD)
            ]
        ff_info = ctypes.cast(lptr, ctypes.POINTER(VS_FIXEDFILEINFO)).contents
        ms = ff_info.dwFileVersionMS
        ls = ff_info.dwFileVersionLS
        major = (ms >> 16) & 0xFFFF
        minor = ms & 0xFFFF
        build = (ls >> 16) & 0xFFFF
        revision = ls & 0xFFFF
        return f'{major}.{minor}.{build}.{revision}'
    except:
        return ''

def is_process_running(name):
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] and proc.info['name'].lower() == name.lower():
                return True
        except:
            continue
    return False

def browse_file():
    root = Tk()
    root.withdraw()
    path = filedialog.askopenfilename(filetypes=[('Executable Files', '*.exe')])
    root.destroy()
    return path

def browse_conf_file():
    root = Tk()
    root.withdraw()
    path = filedialog.askopenfilename(filetypes=[('Config Files', '*.conf'), ('All Files', '*.*')])
    root.destroy()
    return path

def rgb_to_hex(rgb):
    return '#{:02X}{:02X}{:02X}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))

def get_exe_path():
    return profile_paths[active_profile]['exe']

def resolve_dll_path(key):
    path = profile_paths[active_profile][key]
    if not os.path.isabs(path):
        path = os.path.join(os.path.dirname(get_exe_path()), path)
    return path

def get_opengl_dll_path():
    return resolve_dll_path('opengl_dll')

def get_native_dll_path():
    return resolve_dll_path('native_dll')

# ----------------------------------------------------------------------
# Backup Management
# ----------------------------------------------------------------------
def create_original_backup():
    os.makedirs(ORIG_BACKUP_DIR, exist_ok=True)
    for prof in ['MSI5', 'NXT']:
        exe = profile_paths[prof]['exe']
        if os.path.exists(exe):
            base = os.path.basename(exe)
            backup_path = os.path.join(ORIG_BACKUP_DIR, f'{prof}_original_{base}')
            if not os.path.exists(backup_path):
                try:
                    shutil.copy2(exe, backup_path)
                    add_log(f'Original backup created for {prof}: {base}', 'success')
                except Exception as e:
                    add_log(f'Backup failed for {prof}: {e}', 'error')
        dll = profile_paths[prof]['opengl_dll']
        if os.path.exists(dll):
            dll_base = os.path.basename(dll)
            dll_backup = os.path.join(ORIG_BACKUP_DIR, f'{prof}_original_{dll_base}')
            if not os.path.exists(dll_backup):
                try:
                    shutil.copy2(dll, dll_backup)
                except Exception as e:
                    add_log(f'DLL backup failed: {e}', 'error')

def ensure_backup_for_profile(exe_path, profile):
    if not exe_path or not os.path.exists(exe_path):
        return False
    base = os.path.basename(exe_path)
    backup_name = f'{profile}_original_{base}'
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        backup = os.path.join(BACKUP_DIR, backup_name)
        if not os.path.exists(backup):
            shutil.copy2(exe_path, backup)
            add_log(f'Original backup created for {profile}: {backup_name}', 'success')
        return True
    except:
        return False

def ensure_backup(exe_path):
    return ensure_backup_for_profile(exe_path, active_profile)

def ensure_dll_backup(dll_path):
    try:
        os.makedirs(DLL_BACKUP_DIR, exist_ok=True)
        backup = os.path.join(DLL_BACKUP_DIR, f'backup_{int(time.time())}.bak')
        shutil.copy2(dll_path, backup)
        return backup
    except:
        return False

def list_backups():
    exe = get_exe_path()
    base = os.path.basename(exe)
    prefix = f'{active_profile}_{base}'
    if not os.path.exists(BACKUP_DIR):
        return []
    files = [f for f in os.listdir(BACKUP_DIR) if f.startswith(prefix) and f.endswith('.bak')]
    files.sort(reverse=True)
    return files

def create_backup_now():
    exe = get_exe_path()
    if not os.path.exists(exe):
        add_log('EXE not found', 'error')
        return None
    profile = active_profile
    base = os.path.basename(exe)
    timestamp = int(time.time())
    backup_name = f'{profile}_{base}.{timestamp}.bak'
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        backup_path = os.path.join(BACKUP_DIR, backup_name)
        shutil.copy2(exe, backup_path)
        add_log(f'Manual backup created: {backup_name}', 'success')
        return backup_path
    except Exception as e:
        add_log(f'Backup failed: {e}', 'error')
        return None

def restore_backup(backup_filename):
    global color_state
    exe = get_exe_path()
    src = os.path.join(BACKUP_DIR, backup_filename)
    if os.path.exists(src):
        try:
            shutil.copy2(src, exe)
            add_log(f'Restored from {backup_filename}', 'success')
            clear_color_cache_file()
            color_state = init_color_state()
            add_log('Color cache cleared', 'info')
            return True
        except Exception as e:
            add_log(f'Restore failed: {e}', 'error')
    return False

def delete_backup(backup_filename):
    path = os.path.join(BACKUP_DIR, backup_filename)
    if os.path.exists(path):
        try:
            os.remove(path)
            add_log(f'Backup {backup_filename} deleted', 'success')
        except Exception as e:
            add_log(f'Delete failed: {e}', 'error')

def restore_all_original():
    global color_state
    restored = False
    for prof in ['MSI5', 'NXT']:
        exe = profile_paths[prof]['exe']
        if os.path.exists(exe):
            base = os.path.basename(exe)
            backup = os.path.join(ORIG_BACKUP_DIR, f'{prof}_original_{base}')
            if os.path.exists(backup):
                try:
                    shutil.copy2(backup, exe)
                    restored = True
                    add_log(f'{prof} EXE restored to original', 'success')
                except Exception as e:
                    add_log(f'Failed to restore {prof} EXE: {e}', 'error')
        dll = profile_paths[prof]['opengl_dll']
        if os.path.exists(dll):
            dll_base = os.path.basename(dll)
            dll_backup = os.path.join(ORIG_BACKUP_DIR, f'{prof}_original_{dll_base}')
            if os.path.exists(dll_backup):
                try:
                    shutil.copy2(dll_backup, dll)
                    add_log(f'{prof} OpenGL DLL restored to original', 'success')
                except Exception as e:
                    add_log(f'Failed to restore DLL: {e}', 'error')
    if restored:
        clear_color_cache_file()
        color_state = init_color_state()
        add_log('Color cache cleared', 'info')

# ----------------------------------------------------------------------
# Color Management
# ----------------------------------------------------------------------
def load_color_cache():
    if os.path.exists(COLOR_CACHE_FILE):
        with open(COLOR_CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_color_cache(cache):
    with open(COLOR_CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)

def init_color_state():
    cache = load_color_cache()
    state = {}
    for profile, targets in [('MSI5', COLOR_TARGETS_MSI5), ('NXT', COLOR_TARGETS_NXT)]:
        state[profile] = {}
        for name, (default_hex, mode) in targets.items():
            cur = cache.get(profile, {}).get(name, default_hex)
            state[profile][name] = {
                'enabled': False,
                'color': [1.0, 0.0, 0.0],   # placeholder, will be set from hex if needed
                'current_hex': cur
            }
    return state

color_state = init_color_state()

def clear_color_cache_file():
    if os.path.exists(COLOR_CACHE_FILE):
        os.remove(COLOR_CACHE_FILE)

def reset_single_color(name_to_reset):
    profile = active_profile
    targets = COLOR_TARGETS_MSI5 if profile == 'MSI5' else COLOR_TARGETS_NXT
    if name_to_reset not in color_state[profile]:
        add_log(f'Color not found: {name_to_reset}', 'error')
        return
    default_hex, _ = targets[name_to_reset]
    color_state[profile][name_to_reset]['current_hex'] = default_hex
    color_state[profile][name_to_reset]['enabled'] = False
    cache = load_color_cache()
    if profile in cache and name_to_reset in cache[profile]:
        del cache[profile][name_to_reset]
        save_color_cache(cache)
    add_log(f"Reset '{name_to_reset}' to default ({default_hex})", 'success')

def reset_colors_to_default():
    profile = active_profile
    targets = COLOR_TARGETS_MSI5 if profile == 'MSI5' else COLOR_TARGETS_NXT
    for name, item in color_state[profile].items():
        item['current_hex'] = targets[name][0]
        item['enabled'] = False
    cache = load_color_cache()
    if profile in cache:
        del cache[profile]
    save_color_cache(cache)
    add_log('All colors reset to default', 'success')

def apply_color_preset(preset_name):
    profile = active_profile
    presets = COLOR_PRESETS_MSI5 if profile == 'MSI5' else COLOR_PRESETS_NXT
    if preset_name not in presets:
        return
    for name, hex_val in presets[preset_name].items():
        if name in color_state[profile]:
            color_state[profile][name]['enabled'] = True
            r = int(hex_val[1:3], 16) / 255.0
            g = int(hex_val[3:5], 16) / 255.0
            b = int(hex_val[5:7], 16) / 255.0
            color_state[profile][name]['color'] = [r, g, b]
    add_log(f'Preset \'{preset_name}\' applied (ready to Apply)', 'success')

def get_old_patterns(old_hex, mode):
    patterns = []
    if mode in ['ascii', 'both']:
        patterns.append((old_hex.encode('ascii'), 'ascii'))
        patterns.append((old_hex.lower().encode('ascii'), 'ascii'))
        patterns.append((old_hex.upper().encode('ascii'), 'ascii'))
    if mode in ['utf16', 'both']:
        patterns.append((old_hex.encode('utf-16le'), 'utf-16le'))
        patterns.append((old_hex.lower().encode('utf-16le'), 'utf-16le'))
        patterns.append((old_hex.upper().encode('utf-16le'), 'utf-16le'))
    return patterns

def collect_color_replacements(data, profile, targets, enabled_colors):
    replacements = []
    for name, item in enabled_colors:
        old_hex = item['current_hex']
        new_hex = rgb_to_hex(item['color'])
        if old_hex.upper() == new_hex.upper():
            continue
        _, mode = targets[name]
        for pat, enc in get_old_patterns(old_hex, mode):
            new_bytes = new_hex.encode('ascii' if enc == 'ascii' else 'utf-16le')
            idx = 0
            while True:
                idx = data.find(pat, idx)
                if idx == -1:
                    break
                if len(new_bytes) != len(pat):
                    new_bytes = new_bytes.ljust(len(pat), b'\x00')[:len(pat)]
                replacements.append((idx, len(pat), new_bytes))
                idx += len(pat)
    return replacements

def get_all_replacements(data):
    profile = active_profile
    replacements = []
    targets = COLOR_TARGETS_MSI5 if profile == 'MSI5' else COLOR_TARGETS_NXT
    enabled = [(name, item) for name, item in color_state[profile].items() if item['enabled']]
    replacements.extend(collect_color_replacements(data, profile, targets, enabled))

    for name, enabled in remove_state.items():
        if enabled:
            pat = REMOVE_STRINGS[name]
            idx = 0
            while (idx := data.find(pat, idx)) != -1:
                replacements.append((idx, len(pat), b'\x00' * len(pat)))
                idx += len(pat)

    for item in CONTEXTUAL_REMOVALS:
        if not contextual_remove_state[item['name']]:
            continue
        search_bytes = item['search_hex']
        target_bytes = item['target_hex']
        idx = data.find(search_bytes)
        if idx != -1:
            target_pos = data.find(target_bytes, idx + len(search_bytes))
            if target_pos != -1:
                if item.get('replace_with', 'null') == 'spaces':
                    replace = b' ' * len(target_bytes)
                else:
                    replace = b'\x00' * len(target_bytes)
                replacements.append((target_pos, len(target_bytes), replace))
    replacements.sort(key=lambda x: x[0], reverse=True)
    return replacements

def preview_all_selected():
    exe_path = get_exe_path()
    if not os.path.exists(exe_path):
        add_log('EXE not found', 'error')
        return
    try:
        with open(exe_path, 'rb') as f:
            data = f.read()
    except Exception as e:
        add_log(f'Read error: {e}', 'error')
        return
    repls = get_all_replacements(data)
    add_log(f'Preview: {len(repls)} changes would be made', 'info')
    color_count = len([c for name, item in color_state[active_profile].items() if item['enabled']])
    removal_count = len([r for r in remove_state.values() if r])
    contextual_count = len([c for c in contextual_remove_state.values() if c])
    if color_count > 0:
        add_log(f'  - {color_count} color(s) to change', 'info')
    if removal_count > 0:
        add_log(f'  - {removal_count} removal(s) to apply', 'info')
    if contextual_count > 0:
        add_log(f'  - {contextual_count} contextual removal(s) to apply', 'info')

def apply_all_colors_safely():
    profile = active_profile
    targets = COLOR_TARGETS_MSI5 if profile == 'MSI5' else COLOR_TARGETS_NXT
    enabled = [(name, item) for name, item in color_state[profile].items() if item['enabled']]
    if not enabled:
        add_log('No colors selected', 'info')
        return
    exe_path = get_exe_path()
    if not os.path.exists(exe_path):
        add_log('EXE not found', 'error')
        return
    if not ensure_backup(exe_path):
        return
    try:
        with open(exe_path, 'rb') as f:
            data = bytearray(f.read())
    except Exception as e:
        add_log(f'Read error: {e}', 'error')
        return
    replacements = collect_color_replacements(data, profile, targets, enabled)
    replacements.sort(key=lambda x: x[0], reverse=True)
    if not replacements:
        add_log('No colors were changed', 'info')
        return
    for pos, length, rep in replacements:
        data[pos:pos+length] = rep
    try:
        with open(exe_path, 'wb') as f:
            f.write(data)
        for name, item in enabled:
            item['current_hex'] = rgb_to_hex(item['color'])
        cache = load_color_cache()
        if profile not in cache:
            cache[profile] = {}
        for name, item in enabled:
            cache[profile][name] = item['current_hex']
        save_color_cache(cache)
        add_log(f'Colors applied ({len(replacements)} changes)', 'success')
    except Exception as e:
        add_log(f'Write error: {e}', 'error')

def apply_removals_only():
    exe_path = get_exe_path()
    if not os.path.exists(exe_path):
        add_log('EXE not found', 'error')
        return
    if not ensure_backup(exe_path):
        return
    try:
        with open(exe_path, 'rb') as f:
            data = bytearray(f.read())
    except Exception as e:
        add_log(f'Read error: {e}', 'error')
        return
    replacements = []
    for name, enabled in remove_state.items():
        if enabled:
            pat = REMOVE_STRINGS[name]
            idx = 0
            while (idx := data.find(pat, idx)) != -1:
                replacements.append((idx, len(pat), b'\x00' * len(pat)))
                idx += len(pat)
    for item in CONTEXTUAL_REMOVALS:
        if not contextual_remove_state[item['name']]:
            continue
        search_bytes = item['search_hex']
        target_bytes = item['target_hex']
        idx = data.find(search_bytes)
        if idx != -1:
            target_pos = data.find(target_bytes, idx + len(search_bytes))
            if target_pos != -1:
                if item.get('replace_with', 'null') == 'spaces':
                    replace = b' ' * len(target_bytes)
                else:
                    replace = b'\x00' * len(target_bytes)
                replacements.append((target_pos, len(target_bytes), replace))
    if not replacements:
        add_log('No removals selected or found', 'info')
        return
    replacements.sort(key=lambda x: x[0], reverse=True)
    for pos, length, rep in replacements:
        data[pos:pos+length] = rep
    try:
        with open(exe_path, 'wb') as f:
            f.write(data)
        add_log(f'Removals applied ({len(replacements)} changes)', 'success')
    except Exception as e:
        add_log(f'Write error: {e}', 'error')

def apply_all_selected():
    profile = active_profile
    exe_path = get_exe_path()
    if not os.path.exists(exe_path):
        add_log('EXE not found', 'error')
        return
    if not ensure_backup(exe_path):
        return
    try:
        with open(exe_path, 'rb') as f:
            data = bytearray(f.read())
    except Exception as e:
        add_log(f'Read error: {e}', 'error')
        return
    replacements = get_all_replacements(data)
    if not replacements:
        add_log('No changes selected', 'info')
        return
    for pos, length, rep in replacements:
        data[pos:pos+length] = rep
    try:
        with open(exe_path, 'wb') as f:
            f.write(data)
        enabled_colors = [(name, item) for name, item in color_state[profile].items() if item['enabled']]
        for name, item in enabled_colors:
            item['current_hex'] = rgb_to_hex(item['color'])
        cache = load_color_cache()
        if profile not in cache:
            cache[profile] = {}
        for name, item in enabled_colors:
            cache[profile][name] = item['current_hex']
        save_color_cache(cache)
        add_log(f'All changes applied ({len(replacements)} replacements)', 'success')
    except Exception as e:
        add_log(f'Write error: {e}', 'error')

# ----------------------------------------------------------------------
# Instance & Version Handling
# ----------------------------------------------------------------------
def detect_instances():
    config_path = profile_paths[active_profile]['conf']
    profile = active_profile
    available_instances[profile] = []
    if not os.path.exists(config_path):
        add_log('Config not found', 'error')
        return
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        for full_name, info in INSTANCE_PATTERNS.items():
            if full_name in content:
                available_instances[profile].append(full_name)
                if full_name not in instance_states[profile]:
                    instance_states[profile][full_name] = {
                        'display': info['display'],
                        'max_len': info['max_len'],
                        'current': info['pattern'],
                        'target': info['pattern'],
                        'conf_key': info['conf_key']
                    }
                    original_instance_names[profile][full_name] = info['pattern']
        if available_instances[profile]:
            add_log(f'Found {len(available_instances[profile])} instance(s) via config', 'success')
        else:
            add_log('No instances detected in config', 'info')
    except Exception as e:
        add_log(f'Error: {e}', 'error')

def scan_exe_for_instances():
    profile = active_profile
    exe_path = get_exe_path()
    if not os.path.exists(exe_path):
        add_log('EXE not found', 'error')
        return
    try:
        with open(exe_path, 'rb') as f:
            data = f.read()
        for full_name, info in INSTANCE_PATTERNS.items():
            pattern = info['pattern'].encode('ascii')
            count = data.count(pattern)
            if count > 0:
                if full_name not in instance_states[profile]:
                    instance_states[profile][full_name] = {
                        'display': info['display'],
                        'max_len': info['max_len'],
                        'current': info['pattern'],
                        'target': info['pattern'],
                        'conf_key': info['conf_key']
                    }
                    original_instance_names[profile][full_name] = info['pattern']
                add_log(f"Found {info['display']} at {count} location(s) in EXE", 'success')
            else:
                add_log(f"{info['display']} not found in EXE", 'info')
    except Exception as e:
        add_log(f'Error scanning EXE: {e}', 'error')

def apply_instance_exe(full_name, target_text):
    profile = active_profile
    if full_name not in instance_states[profile]:
        add_log(f'Unknown instance: {full_name}', 'error')
        return
    state = instance_states[profile][full_name]
    if len(target_text) > state['max_len']:
        target_text = target_text[:state['max_len']]
    padded = target_text + ' ' * (state['max_len'] - len(target_text))
    exe_path = get_exe_path()
    if not os.path.exists(exe_path):
        add_log('EXE not found', 'error')
        return
    if not ensure_backup(exe_path):
        return
    try:
        with open(exe_path, 'rb') as f:
            data = f.read()
        search_pattern = state['current'].encode('ascii')
        count = data.count(search_pattern)
        if count == 0:
            add_log(f"Pattern '{state['current']}' not found in EXE", 'error')
            return
        new_pattern = padded.encode('ascii')
        new_data = data.replace(search_pattern, new_pattern)
        if new_data == data:
            add_log('No changes were made', 'warning')
            return
        with open(exe_path, 'wb') as f:
            f.write(new_data)
        state['current'] = new_pattern.decode('ascii')
        state['target'] = target_text
        add_log(f"Changed {state['display']} EXE name to '{target_text}' ({count} occurrence(s))", 'success')
    except Exception as e:
        add_log(f'Error applying instance name: {e}', 'error')

def read_conf_display_names():
    conf_path = profile_paths[active_profile]['conf']
    names = {}
    if not os.path.exists(conf_path):
        return names
    try:
        with open(conf_path, 'r', encoding='utf-8') as f:
            for line in f:
                for full_name, info in INSTANCE_PATTERNS.items():
                    key = f"bst.instance.{info['conf_key']}.display_name"
                    if key in line:
                        match = re.search(r'=\"([^\"]*)\"', line)
                        if match:
                            names[full_name] = match.group(1)
                        else:
                            names[full_name] = ''
    except Exception as e:
        add_log(f'Error reading conf: {e}', 'error')
    return names

def write_conf_display_name(full_name, new_name):
    profile = active_profile
    conf_path = profile_paths[profile]['conf']
    if not os.path.exists(conf_path):
        add_log('Config file not found', 'error')
        return
    info = INSTANCE_PATTERNS.get(full_name)
    if not info:
        add_log('Unknown instance', 'error')
        return
    key = f"bst.instance.{info['conf_key']}.display_name"
    try:
        with open(conf_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        new_line = f'{key}=\"{new_name}\"\n'
        found = False
        with open(conf_path, 'w', encoding='utf-8') as f:
            for line in lines:
                if key in line:
                    f.write(new_line)
                    found = True
                else:
                    f.write(line)
            if not found:
                f.write(new_line)
        add_log(f"Display name for {info['display']} set to '{new_name}' in conf", 'success')
    except Exception as e:
        add_log(f'Error writing conf: {e}', 'error')

def find_version():
    profile = active_profile
    exe_path = get_exe_path()
    vs = version_state[profile]
    vs['found'] = ''
    vs['max_len'] = 0
    vs['original'] = ''
    if not exe_path or not os.path.exists(exe_path):
        add_log('Executable not found', 'error')
        return
    real_ver = get_file_version(exe_path)
    if real_ver:
        vs['found'] = real_ver
        vs['max_len'] = len(real_ver)
        vs['offset'] = 0
        vs['encoding'] = 'ascii'
        vs['text'] = real_ver
        vs['original'] = real_ver
        add_log(f'File version: {real_ver}', 'success')
        return
    try:
        with open(exe_path, 'rb') as f:
            data = f.read()
        for v in KNOWN_VERSIONS:
            idx = data.find(v.encode('ascii'))
            if idx != -1:
                vs['found'] = v
                vs['max_len'] = len(v)
                vs['offset'] = idx
                vs['encoding'] = 'ascii'
                vs['text'] = v
                vs['original'] = v
                add_log(f'Version string: {v}', 'success')
                return
            idx = data.find(v.encode('utf-16le'))
            if idx != -1:
                vs['found'] = v
                vs['max_len'] = len(v)
                vs['offset'] = idx
                vs['encoding'] = 'utf-16le'
                vs['text'] = v
                vs['original'] = v
                add_log(f'Version string: {v}', 'success')
                return
        add_log('Version not found', 'warning')
    except Exception as e:
        add_log(f'Error: {e}', 'error')

def apply_version(new_text):
    profile = active_profile
    vs = version_state[profile]
    if not vs['found']:
        add_log('Scan version first', 'error')
        return
    if len(new_text) > vs['max_len']:
        add_log(f"Max {vs['max_len']} chars", 'error')
        return
    exe_path = get_exe_path()
    if not ensure_backup(exe_path):
        return
    try:
        with open(exe_path, 'rb') as f:
            data = bytearray(f.read())
        old_bytes = vs['found'].encode(vs['encoding'])
        filler = ' ' * (vs['max_len'] - len(new_text))
        new_bytes = (new_text + filler).encode(vs['encoding'])
        idx = data.find(old_bytes)
        if idx == -1:
            add_log('Original version string no longer found', 'error')
            return
        data[idx:idx+len(old_bytes)] = new_bytes
        with open(exe_path, 'wb') as f:
            f.write(data)
        add_log(f'Version changed to {new_text}', 'success')
        vs['found'] = new_text + filler
        vs['text'] = new_text
    except Exception as e:
        add_log(f'Error: {e}', 'error')

def restore_version():
    global color_state
    profile = active_profile
    vs = version_state[profile]
    if vs['original'] and vs['max_len'] > 0:
        exe_path = get_exe_path()
        try:
            with open(exe_path, 'rb') as f:
                data = bytearray(f.read())
            current_ver_bytes = vs['found'].encode(vs['encoding'])
            original_bytes = vs['original'].encode(vs['encoding'])
            if len(original_bytes) < len(current_ver_bytes):
                original_bytes = original_bytes.ljust(len(current_ver_bytes), b' ')
            elif len(original_bytes) > len(current_ver_bytes):
                original_bytes = original_bytes[:len(current_ver_bytes)]
            idx = data.find(current_ver_bytes)
            if idx != -1:
                data[idx:idx+len(current_ver_bytes)] = original_bytes
                with open(exe_path, 'wb') as f:
                    f.write(data)
                vs['found'] = original_bytes.decode(vs['encoding'])
                vs['text'] = vs['original']
                add_log('Version restored to original string (smart)', 'success')
                return
        except Exception as e:
            add_log(f'Smart restore failed: {e}, trying full restore', 'warning')
    exe_path = get_exe_path()
    backup_name = f'{profile}_original_{os.path.basename(exe_path)}'
    backup = os.path.join(BACKUP_DIR, backup_name)
    if os.path.exists(backup):
        try:
            shutil.copy2(backup, exe_path)
            add_log('Original EXE restored (full)', 'success')
            clear_color_cache_file()
            color_state = init_color_state()
            find_version()
            add_log('Color cache cleared', 'info')
        except Exception as e:
            add_log(f'Error: {e}', 'error')
    else:
        add_log('No backup found for full restore', 'error')

# ----------------------------------------------------------------------
# FPS Text Changer
# ----------------------------------------------------------------------
def load_fps_cache():
    if os.path.exists(FPS_CACHE_FILE):
        with open(FPS_CACHE_FILE, 'r') as f:
            return json.load(f).get('text', '')
    return ''

def save_fps_cache(text):
    with open(FPS_CACHE_FILE, 'w') as f:
        json.dump({'text': text}, f)

def scan_fps_text():
    global fps_status, fps_text_user, fps_last_text
    fps_status = {'found': {}, 'custom': bool(fps_last_text)}
    exe_dir = os.path.dirname(get_exe_path())
    for dll_name in fps_dll_names:
        dll_path = os.path.join(exe_dir, dll_name)
        if not os.path.exists(dll_path):
            continue
        try:
            with open(dll_path, 'rb') as f:
                data = f.read()
            has_fps = b'FPS %3d' in data
            if not has_fps and fps_last_text:
                padded = fps_last_text.encode('ascii') + b' ' * (fps_max_len - len(fps_last_text))
                has_fps = padded in data
            fps_status['found'][dll_name] = has_fps
            if has_fps:
                add_log(f'FPS text found in {dll_name}', 'success')
            else:
                add_log(f'FPS text not found in {dll_name}', 'warning')
        except Exception as e:
            add_log(f'Error scanning {dll_name}: {e}', 'error')
    if any(fps_status['found'].values()):
        fps_text_user = fps_last_text if fps_last_text else ''

def apply_fps_text(new_text):
    global fps_text_user, fps_last_text
    exe_dir = os.path.dirname(get_exe_path())
    if is_process_running('HD-Player.exe'):
        add_log('Close app first', 'error')
        return
    if len(new_text) > fps_max_len:
        add_log(f'Max {fps_max_len} characters', 'error')
        return
    pad_len = fps_max_len - len(new_text)
    new_padded = new_text.encode('ascii') + b' ' * pad_len
    old_padded = b''
    if fps_last_text:
        old_padded = fps_last_text.encode('ascii') + b' ' * (fps_max_len - len(fps_last_text))
    any_change = False
    for dll_name in fps_dll_names:
        if not fps_status['found'].get(dll_name, False):
            continue
        dll_path = os.path.join(exe_dir, dll_name)
        if not os.path.exists(dll_path):
            continue
        ensure_dll_backup(dll_path)
        try:
            with open(dll_path, 'rb') as f:
                data = bytearray(f.read())
            positions = []
            if old_padded:
                idx = 0
                while (idx := data.find(old_padded, idx)) != -1:
                    positions.append((idx, len(old_padded), new_padded))
                    idx += len(old_padded)
            idx = 0
            while (idx := data.find(b'FPS %3d', idx)) != -1:
                if not any(p[0] <= idx < p[0]+p[1] for p in positions):
                    positions.append((idx, 7, new_padded))
                idx += 7
            if positions:
                positions.sort(key=lambda x: x[0], reverse=True)
                for pos, old_len, rep in positions:
                    data[pos:pos+old_len] = rep
                with open(dll_path, 'wb') as f:
                    f.write(data)
                add_log(f'Applied FPS text to {dll_name}', 'success')
                any_change = True
        except Exception as e:
            add_log(f'Error writing {dll_name}: {e}', 'error')
    if any_change:
        fps_status['custom'] = True
        fps_text_user = new_text
        fps_last_text = new_text
        save_fps_cache(new_text)
    else:
        add_log('FPS text was not changed', 'warning')

def restore_fps_text():
    global fps_text_user, fps_last_text
    exe_dir = os.path.dirname(get_exe_path())
    any_restore = False
    for dll_name in fps_dll_names:
        dll_path = os.path.join(exe_dir, dll_name)
        if not os.path.exists(dll_path):
            continue
        if not os.path.exists(DLL_BACKUP_DIR):
            continue
        backups = [f for f in os.listdir(DLL_BACKUP_DIR) if f.endswith('.bak')]
        if not backups:
            continue
        backups.sort(reverse=True)
        latest = os.path.join(DLL_BACKUP_DIR, backups[0])
        try:
            shutil.copy2(latest, dll_path)
            add_log(f'Restored {dll_name}', 'success')
            any_restore = True
        except:
            pass
    if any_restore:
        fps_status['custom'] = False
        fps_text_user = ''
        fps_last_text = ''
        save_fps_cache('')
        scan_fps_text()

# ----------------------------------------------------------------------
# OpenGL & Round Corners
# ----------------------------------------------------------------------
def apply_opengl_version(version):
    dll = get_opengl_dll_path()
    if not os.path.exists(dll):
        add_log(f'DLL not found: {dll}', 'error')
        return
    if not re.match(r'^\d+\.\d+$', version):
        add_log('Use format X.Y', 'error')
        return
    if is_process_running('HD-Player.exe'):
        add_log('Close app first', 'error')
        return
    backup = ensure_dll_backup(dll)
    if not backup:
        return
    try:
        with open(dll, 'rb') as f:
            data = bytearray(f.read())
        pattern = b'2.0\x003.0\x003.1\x003.2'
        pos = data.find(pattern)
        if pos != -1:
            old_ver = b'3.1'
            start_idx = pos + 8
            new_ver_bytes = version.encode()
            if len(new_ver_bytes) == len(old_ver):
                data[start_idx:start_idx+len(old_ver)] = new_ver_bytes
            else:
                data[start_idx:start_idx+len(old_ver)] = new_ver_bytes.ljust(len(old_ver), b'\x00')[:len(old_ver)]
            with open(dll, 'wb') as f:
                f.write(data)
            add_log(f'OpenGL version changed to {version}', 'success')
        else:
            add_log('Pattern 2.0 3.0 3.1 3.2 not found', 'warning')
    except Exception as e:
        add_log(f'Error: {e}', 'error')

def restore_opengl():
    dll = get_opengl_dll_path()
    if not os.path.exists(DLL_BACKUP_DIR):
        add_log('No backups', 'error')
        return
    backups = [f for f in os.listdir(DLL_BACKUP_DIR) if f.endswith('.bak')]
    if not backups:
        add_log('No backups', 'error')
        return
    backups.sort(reverse=True)
    latest = os.path.join(DLL_BACKUP_DIR, backups[0])
    try:
        shutil.copy2(latest, dll)
        add_log('OpenGL restored from backup', 'success')
    except Exception as e:
        add_log(f'Error: {e}', 'error')

def apply_round_corners(enable):
    global round_corners_status
    exe_path = get_exe_path()
    if not exe_path:
        return
    dll_dest = os.path.join(os.path.dirname(exe_path), ROUND_CORNER_DLL)
    if is_process_running('HD-Player.exe'):
        add_log('Close app first', 'error')
        return
    if enable:
        src = os.path.join(APP_DIR, ROUND_CORNER_DLL)
        if not os.path.exists(src):
            add_log(f'Place {ROUND_CORNER_DLL} in program directory', 'error')
            return
        try:
            shutil.copy2(src, dll_dest)
            round_corners_status = True
            add_log('Round corners enabled', 'success')
        except Exception as e:
            add_log(f'Error: {e}', 'error')
    else:
        if os.path.exists(dll_dest):
            try:
                os.remove(dll_dest)
                round_corners_status = False
                add_log('Round corners disabled', 'success')
            except Exception as e:
                add_log(f'Error: {e}', 'error')

def check_round_corners():
    exe_path = get_exe_path()
    if not exe_path:
        return False
    return os.path.exists(os.path.join(os.path.dirname(exe_path), ROUND_CORNER_DLL))

# ----------------------------------------------------------------------
# Settings Import/Export
# ----------------------------------------------------------------------
def export_settings():
    try:
        data = {
            'paths': profile_paths,
            'active_profile': active_profile,
            'theme': current_theme,
            'remove_state': remove_state,
            'color_state': {prof: {n: i['current_hex'] for n, i in items.items()} for prof, items in color_state.items()},
            'fps_text': fps_last_text
        }
        with open(SETTINGS_EXPORT_FILE, 'w') as f:
            json.dump(data, f, indent=2)
        add_log('Settings exported', 'success')
    except Exception as e:
        add_log(f'Export failed: {e}', 'error')

def import_settings():
    global current_theme, fps_text_user, profile_paths, active_profile, fps_last_text
    if not os.path.exists(SETTINGS_EXPORT_FILE):
        add_log('No settings file', 'error')
        return
    try:
        with open(SETTINGS_EXPORT_FILE, 'r') as f:
            data = json.load(f)
        if 'paths' in data:
            profile_paths = data['paths']
        active_profile = data.get('active_profile', active_profile)
        current_theme = data.get('theme', current_theme)
        apply_theme(current_theme)
        if 'remove_state' in data:
            remove_state.update(data['remove_state'])
        if 'color_state' in data:
            for prof, states in data['color_state'].items():
                for n, hex_val in states.items():
                    if prof in color_state and n in color_state[prof]:
                        color_state[prof][n]['current_hex'] = hex_val
        fps_last_text = data.get('fps_text', '')
        fps_text_user = fps_last_text
        save_fps_cache(fps_last_text)
        add_log('Settings imported', 'success')
    except Exception as e:
        add_log(f'Import failed: {e}', 'error')

# ----------------------------------------------------------------------
# UI Scale
# ----------------------------------------------------------------------
def read_ui_scale_from_config():
    conf_path = profile_paths[active_profile]['conf']
    if not os.path.exists(conf_path):
        return '1.00'
    try:
        with open(conf_path, 'r', encoding='utf-8') as f:
            for line in f:
                if 'bst.ui_scale_factor' in line:
                    match = re.search(r'=\"([^\"]*)\"', line)
                    if match:
                        return match.group(1)
    except:
        pass
    return '1.00'

def write_ui_scale_to_config(value):
    conf_path = profile_paths[active_profile]['conf']
    if not os.path.exists(conf_path):
        add_log('Config file not found', 'error')
        return
    try:
        with open(conf_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        found = False
        with open(conf_path, 'w', encoding='utf-8') as f:
            for line in lines:
                if 'bst.ui_scale_factor' in line:
                    f.write(f'bst.ui_scale_factor=\"{value}\"\n')
                    found = True
                else:
                    f.write(line)
            if not found:
                f.write(f'\nbst.ui_scale_factor=\"{value}\"\n')
        add_log(f'UI scale set to {value}', 'success')
    except Exception as e:
        add_log(f'Error writing conf: {e}', 'error')

# ----------------------------------------------------------------------
# Theme System (for Customizer GUI)
# ----------------------------------------------------------------------
def load_theme_cache():
    if os.path.exists(THEME_CACHE_FILE):
        with open(THEME_CACHE_FILE, 'r') as f:
            return json.load(f).get('theme', 'Glacier')
    return 'Glacier'

def save_theme_cache(theme):
    with open(THEME_CACHE_FILE, 'w') as f:
        json.dump({'theme': theme}, f)

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(c1, c2, t):
    return tuple(lerp(a, b, t) for a, b in zip(c1, c2))

def apply_theme_lerp(lerp_factor):
    if prev_theme not in THEMES or next_theme not in THEMES:
        return
    prev = THEMES[prev_theme]
    nxt = THEMES[next_theme]
    colors = imgui.get_style().colors
    for key, val in THEMES_KEY_MAP.items():
        colors[key] = lerp_color(prev[val], nxt[val], lerp_factor)

def apply_theme(theme_name):
    global theme_transition_time, prev_theme, next_theme, current_theme
    if theme_name not in THEMES or current_theme == theme_name:
        return
    prev_theme = current_theme
    next_theme = theme_name
    theme_transition_time = glfw.get_time()
    current_theme = theme_name

def setup_style():
    style = imgui.get_style()
    t = THEMES[current_theme]
    colors = style.colors
    for key, val in THEMES_KEY_MAP.items():
        colors[key] = t[val]
    style.window_rounding = 6.0
    style.child_rounding = 4.0
    style.frame_rounding = 4.0
    style.popup_rounding = 4.0
    style.scrollbar_rounding = 6.0
    style.grab_rounding = 4.0
    style.window_padding = (10, 10)
    style.frame_padding = (6, 4)
    style.item_spacing = (10, 8)
    style.item_inner_spacing = (6, 4)
    style.indent_spacing = 20
    style.scrollbar_size = 12

def load_custom_font(impl):
    font_paths = [r'C:\Windows\Fonts\ARIALUNI.TTF', r'C:\Windows\Fonts\seguiemj.ttf', r'C:\Windows\Fonts\arial.ttf']
    io = imgui.get_io()
    for font_path in font_paths:
        if os.path.exists(font_path):
            new_font = io.fonts.add_font_from_file_ttf(font_path, 16)
            if new_font is not None:
                impl.refresh_font_texture()
                return
    io.fonts.add_font_default()
    impl.refresh_font_texture()

def auto_detect_paths():
    found = False
    for profile in ['MSI5', 'NXT']:
        default_exe = DEFAULT_PATHS[profile]['exe']
        if os.path.exists(default_exe):
            profile_paths[profile]['exe'] = default_exe
            found = True
        else:
            search_folder = f'BlueStacks_{profile.lower()}'
            program_files = 'C:\\Program Files'
            if os.path.exists(program_files):
                try:
                    for folder in os.listdir(program_files):
                        if search_folder.lower() in folder.lower():
                            possible = os.path.join(program_files, folder, 'HD-Player.exe')
                            if os.path.exists(possible):
                                profile_paths[profile]['exe'] = possible
                                found = True
                                break
                except:
                    pass
    if found:
        add_log('Installation paths auto-detected', 'success')
    else:
        add_log('No BlueStacks installations found at default locations', 'warning')

def get_instances_for_info(conf_path):
    instances = []
    if not os.path.exists(conf_path):
        return instances
    try:
        with open(conf_path, 'r', encoding='utf-8') as f:
            content = f.read()
        checks = [
            ('Nougat32', 'N32', ANDROID_VERSIONS.get('N32', 'Android 7.1.2')),
            ('Nougat64', 'N64', ANDROID_VERSIONS.get('N64', 'Android 7.1.2 64 bit')),
            ('Pie64', 'P64', ANDROID_VERSIONS.get('P64', 'Android 9 Pie')),
            ('Rvc64', 'Rvc64', ANDROID_VERSIONS.get('Rvc64', 'Android 11')),
            ('Tiramisu64', 'Tiramisu64', ANDROID_VERSIONS.get('Tiramisu64', 'Android 13 (Beta)'))
        ]
        for conf_key, display, android_ver in checks:
            if conf_key in content:
                instances.append((display, android_ver))
    except Exception as e:
        add_log(f'Error reading instances from config: {e}', 'warning')
    return instances

# ----------------------------------------------------------------------
# Main GUI Loop
# ----------------------------------------------------------------------
def main():
    global current_theme, fps_text_user, drag_start_x, opengl_version, ui_scale_value
    global window_maximized, profile_paths, round_corners_status, log_filter_text
    global show_backup_manager, active_profile, current_tab, prev_theme, dragging, drag_start_y

    if not glfw.init():
        messagebox.showerror('OpenGL Error', 'Failed to initialize OpenGL. Please update graphics drivers.')
        return

    monitor = glfw.get_primary_monitor()
    mode = glfw.get_video_mode(monitor)
    window_width, window_height = 1100, 750
    win_x = (mode.size.width - window_width) // 2
    win_y = (mode.size.height - window_height) // 2

    glfw.window_hint(glfw.DECORATED, False)
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 2)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)

    window = glfw.create_window(window_width, window_height, f'{BRAND_NAME} BlueStacks Customizer', None, None)
    if not window:
        glfw.terminate()
        messagebox.showerror('OpenGL Error', 'Could not create window.')
        return

    glfw.set_window_pos(window, win_x, win_y)
    glfw.make_context_current(window)
    glfw.swap_interval(1)

    def framebuffer_size_callback(win, w, h):
        glViewport(0, 0, w, h)
    glfw.set_framebuffer_size_callback(window, framebuffer_size_callback)

    glClearColor(0.04, 0.04, 0.06, 1.0)

    imgui.create_context()
    setup_style()
    impl = GlfwRenderer(window)
    load_custom_font(impl)

    # Load paths and auto-detect
    profile_paths = {'MSI5': dict(DEFAULT_PATHS['MSI5']), 'NXT': dict(DEFAULT_PATHS['NXT'])}
    auto_detect_paths()
    msi5_exists = os.path.exists(profile_paths['MSI5']['exe'])
    nxt_exists = os.path.exists(profile_paths['NXT']['exe'])
    if nxt_exists and not msi5_exists:
        active_profile = 'NXT'
    elif msi5_exists and not nxt_exists:
        active_profile = 'MSI5'
    else:
        active_profile = 'NXT'

    add_log(f'Active profile set to {active_profile}', 'info')
    create_original_backup()
    for prof in ['MSI5', 'NXT']:
        exe = profile_paths[prof]['exe']
        if os.path.exists(exe):
            ensure_backup_for_profile(exe, prof)

    global fps_last_text, fps_status, fps_text_user
    fps_last_text = load_fps_cache()
    fps_text_user = fps_last_text
    scan_fps_text()
    ui_scale_value = read_ui_scale_from_config()
    add_log(f'{BRAND_NAME} BlueStacks Customizer started', 'info')
    detect_instances()

    color_preset_idx = 0

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()
        w, h = glfw.get_window_size(window)
        mouse_x, mouse_y = glfw.get_cursor_pos(window)
        mouse_pressed = glfw.get_mouse_button(window, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS

        # Theme transition
        now = glfw.get_time()
        if prev_theme != next_theme:
            elapsed = now - theme_transition_time
            lerp_factor = min(elapsed / transition_duration, 1.0)
            apply_theme_lerp(lerp_factor)
            if lerp_factor >= 1.0:
                prev_theme = next_theme
                current_theme = next_theme
                save_theme_cache(current_theme)

        # Window dragging
        nonlocal dragging, drag_start_x, drag_start_y
        if mouse_pressed and mouse_y < 40 and mouse_x < w - 160:
            if not dragging:
                dragging = True
                drag_start_x = mouse_x
                drag_start_y = mouse_y
        else:
            dragging = False
        if dragging:
            wx, wy = glfw.get_window_pos(window)
            glfw.set_window_pos(window, int(wx + mouse_x - drag_start_x), int(wy + mouse_y - drag_start_y))

        glViewport(0, 0, w, h)
        glClear(GL_COLOR_BUFFER_BIT)
        imgui.new_frame()

        # Main window (borderless, full size)
        imgui.set_next_window_size(w, h)
        imgui.set_next_window_position(0, 0)
        imgui.begin('Main', flags=imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE)

        # Custom title bar
        title_color = imgui.get_style().colors[imgui.COLOR_TITLE_BACKGROUND]
        draw_list = imgui.get_window_draw_list()
        draw_list.add_rect_filled(0, 0, w, 40, imgui.get_color_u32_rgba(*title_color))

        imgui.set_cursor_pos((15, 10))
        imgui.text_colored(f'{BRAND_NAME} BlueStacks Customizer', 0.7, 0.75, 0.85, 1.0)
        imgui.set_cursor_pos((15, 28))
        imgui.text_colored('All Pro features unlocked', 0.5, 0.5, 0.5, 1.0)

        # Social buttons
        imgui.set_cursor_pos((w // 2 - 80 - 150, 8))
        imgui.push_style_color(imgui.COLOR_BUTTON, 0.95, 0.6, 0.1, 1.0)
        imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 1.0, 0.7, 0.2, 1.0)
        if imgui.button('Discord', 80, 24):
            webbrowser.open(DISCORD_INVITE)
        imgui.same_line()
        if imgui.button('YouTube', 80, 24):
            webbrowser.open(YT_CHANNEL)
        imgui.pop_style_color(2)

        # Profile combo
        imgui.set_cursor_pos((w // 2 - 80, 10))
        imgui.push_item_width(100)
        _, new_prof = imgui.combo('##prof', 0 if active_profile == 'MSI5' else 1, ['MSI5', 'NXT'])
        if new_prof != (0 if active_profile == 'MSI5' else 1):
            active_profile = 'MSI5' if new_prof == 0 else 'NXT'
            round_corners_status = check_round_corners()
            scan_fps_text()
            ui_scale_value = read_ui_scale_from_config()
            detect_instances()
            add_log(f'Switched to {active_profile}', 'info')
        imgui.pop_item_width()

        # Window controls
        btn_size = 40
        imgui.set_cursor_pos((w - btn_size - 10, 10))
        imgui.push_style_color(imgui.COLOR_BUTTON, 0.6, 0.1, 0.1, 1.0)
        imgui.push_style_color(imgui.COLOR_BUTTON_HOVERED, 0.9, 0.1, 0.1, 1.0)
        if imgui.button('X', btn_size, 22):
            glfw.set_window_should_close(window, True)
        imgui.pop_style_color(2)

        imgui.set_cursor_pos((w - btn_size*2 - 15, 10))
        if imgui.button('[]', btn_size, 22):
            if window_maximized:
                glfw.set_window_size(window, window_width, window_height)
                glfw.set_window_pos(window, (mode.size.width - window_width)//2, (mode.size.height - window_height)//2)
                window_maximized = False
            else:
                glfw.set_window_size(window, mode.size.width, mode.size.height)
                glfw.set_window_pos(window, 0, 0)
                window_maximized = True

        imgui.set_cursor_pos((w - btn_size*3 - 20, 10))
        if imgui.button('_', btn_size, 22):
            glfw.iconify_window(window)

        # Tabs
        tabs = ['Colors', 'Remove', 'Titlebar', 'Extra', 'Settings', 'Info', 'Tutorial']
        tab_width = 85
        imgui.set_cursor_pos((15, 50))
        for i, tab_name in enumerate(tabs):
            if i > 0:
                imgui.same_line(15 + (tab_width + 6) * i)
            if imgui.button(tab_name, tab_width, 26):
                current_tab = i
        imgui.separator()
        imgui.spacing()

        # Content area + log area
        avail_y = imgui.get_content_region_available().y
        log_height = min(150, max(100, int(avail_y * 0.25)))
        content_height = avail_y - log_height - 10

        imgui.begin_child('Content', w - 30, content_height, border=True)

        # ----------------------------------------------------------
        # Tab 0: Colors
        # ----------------------------------------------------------
        if current_tab == 0:
            imgui.text_colored('COLORS', 0.7, 0.75, 0.85, 1.0)
            imgui.separator()
            # No Pro restriction – all colors editable
            presets_list = list(COLOR_PRESETS_MSI5.keys()) if active_profile == 'MSI5' else list(COLOR_PRESETS_NXT.keys())
            preset_options = ['Default (unchanged)'] + presets_list
            imgui.push_item_width(180)
            changed_preset, color_preset_idx = imgui.combo('##preset', color_preset_idx, preset_options)
            if imgui.is_item_hovered():
                imgui.set_tooltip('Apply a pre-defined color scheme')
            imgui.pop_item_width()
            if changed_preset and color_preset_idx > 0:
                apply_color_preset(presets_list[color_preset_idx - 1])
            imgui.same_line()
            if imgui.button('Reset All Colors', 120, 24):
                reset_colors_to_default()
                color_preset_idx = 0
            imgui.same_line()
            if imgui.button('Preview Changes', 120, 24):
                preview_all_selected()
            imgui.same_line()
            if imgui.button('Apply ALL Selected', 140, 24):
                apply_all_selected()

            imgui.spacing()
            targets = COLOR_TARGETS_MSI5 if active_profile == 'MSI5' else COLOR_TARGETS_NXT
            for name, item in color_state[active_profile].items():
                imgui.push_id(name)
                _, item['enabled'] = imgui.checkbox('##en', item['enabled'])
                imgui.same_line(40)
                imgui.text(name)
                if imgui.is_item_hovered():
                    imgui.set_tooltip(f'Default: {targets[name][0]}')
                if item['enabled']:
                    imgui.same_line(0, 0)
                    imgui.set_cursor_pos_x(360)
                    imgui.push_item_width(200)
                    _, new_col = imgui.color_edit3('##col', *item['color'])
                    item['color'] = list(new_col)
                    imgui.pop_item_width()
                imgui.same_line()
                if imgui.button('Reset', 50):
                    reset_single_color(name)
                imgui.pop_id()
                imgui.spacing()
            avail_width = imgui.get_content_region_available().x
            imgui.set_cursor_pos_x((avail_width - 140) / 2)
            if imgui.button('APPLY COLORS', 140, 34):
                apply_all_colors_safely()

        # ----------------------------------------------------------
        # Tab 1: Remove (all removals unlocked)
        # ----------------------------------------------------------
        elif current_tab == 1:
            imgui.text_colored('REMOVE', 0.7, 0.75, 0.85, 1.0)
            imgui.separator()
            imgui.text_colored('All removals unlocked (Pro features active)', 0.4, 0.9, 0.6, 1.0)
            if imgui.button('Select All', 100):
                for k in remove_state:
                    remove_state[k] = True
                for k in contextual_remove_state:
                    contextual_remove_state[k] = True
            imgui.same_line(120)
            if imgui.button('Deselect All', 100):
                for k in remove_state:
                    remove_state[k] = False
                for k in contextual_remove_state:
                    contextual_remove_state[k] = False
            imgui.spacing()
            for name in remove_state:
                imgui.push_id(name)
                _, remove_state[name] = imgui.checkbox(name, remove_state[name])
                imgui.pop_id()
                imgui.spacing()
            for item in CONTEXTUAL_REMOVALS:
                name = item['name']
                imgui.push_id(name)
                _, contextual_remove_state[name] = imgui.checkbox(name, contextual_remove_state[name])
                imgui.pop_id()
                imgui.spacing()
            avail_width = imgui.get_content_region_available().x
            imgui.set_cursor_pos_x((avail_width - 140) / 2)
            if imgui.button('APPLY REMOVALS', 140, 34):
                apply_removals_only()

        # ----------------------------------------------------------
        # Tab 2: Titlebar (Version & Instance Names)
        # ----------------------------------------------------------
        elif current_tab == 2:
            vs = version_state[active_profile]
            imgui.text_colored('VERSION NUMBER', 0.7, 0.75, 0.85, 1.0)
            if imgui.button('SCAN VERSION', 100):
                find_version()
            if vs['found']:
                imgui.same_line(120)
                imgui.text_colored(f"Current: {vs['found']}", 0.4, 0.9, 0.6, 1.0)
            imgui.text('New:')
            imgui.same_line(80)
            imgui.set_next_item_width(100)
            changed, user_t = imgui.input_text('##ver', vs['text'], 256)
            if changed and vs['max_len'] > 0 and len(user_t) > vs['max_len']:
                user_t = user_t[:vs['max_len']]
            vs['text'] = user_t
            if imgui.button('APPLY', 80):
                apply_version(vs['text'])
            imgui.same_line(100)
            if imgui.button('RESTORE', 80):
                restore_version()
            imgui.separator()

            # Instance names from config
            imgui.text_colored('INSTANCE NAMES (Config)', 0.7, 0.75, 0.85, 1.0)
            if imgui.button('DETECT INSTANCES', 140):
                detect_instances()
            conf_names = read_conf_display_names()
            for full_name, state in instance_states[active_profile].items():
                imgui.push_id(full_name + '_conf')
                imgui.text(f"{state['display']}:")
                imgui.same_line(150)
                imgui.push_item_width(150)
                cur_val = instance_conf_inputs.get(full_name, conf_names.get(full_name, ''))
                changed, new_val = imgui.input_text('##conf_name', cur_val, 256)
                if changed:
                    instance_conf_inputs[full_name] = new_val
                imgui.pop_item_width()
                imgui.same_line(310)
                if imgui.button('Set Name', 80):
                    write_conf_display_name(full_name, instance_conf_inputs.get(full_name, ''))
                imgui.same_line(400)
                if imgui.button('Remove Name', 110):
                    write_conf_display_name(full_name, '')
                imgui.pop_id()
                imgui.spacing()
            imgui.separator()

            # Instance names from EXE
            imgui.text_colored('INSTANCE NAMES (EXE)', 0.7, 0.75, 0.85, 1.0)
            if imgui.button('SCAN EXE', 100):
                scan_exe_for_instances()
            for full_name, state in instance_states[active_profile].items():
                imgui.push_id(full_name + '_exe')
                imgui.text(f"{state['display']}: [{state['current']}]")
                imgui.same_line(250)
                if imgui.button('Blank Name', 100):
                    apply_instance_exe(full_name, '')
                imgui.same_line(360)
                if imgui.button('Restore Name', 100):
                    orig = original_instance_names[active_profile].get(full_name)
                    if orig:
                        apply_instance_exe(full_name, orig)
                imgui.pop_id()

        # ----------------------------------------------------------
        # Tab 3: Extra (Round corners, OpenGL, FPS, Launcher, UI Scale)
        # ----------------------------------------------------------
        elif current_tab == 3:
            # Round corners
            imgui.text_colored('ROUND CORNERS', 0.7, 0.75, 0.85, 1.0)
            round_corners_status = check_round_corners()
            imgui.text(f"Status: {'Enabled' if round_corners_status else 'Disabled'}")
            if imgui.button('ENABLE', 70):
                apply_round_corners(True)
            imgui.same_line(90)
            if imgui.button('DISABLE', 70):
                apply_round_corners(False)
            imgui.separator()

            # OpenGL version
            imgui.text_colored('OPENGL VERSION', 0.7, 0.75, 0.85, 1.0)
            dll = get_opengl_dll_path()
            if os.path.exists(dll):
                try:
                    with open(dll, 'rb') as f:
                        data = f.read()
                    pattern = b'2.0\x003.0\x003.1\x003.2'
                    pos = data.find(pattern)
                    if pos != -1:
                        cur_ver = data[pos+8:pos+11].decode('ascii', errors='ignore').strip('\x00')
                        imgui.text_colored(f'Current OpenGL: {cur_ver}', 0.4, 0.9, 0.6, 1.0)
                    else:
                        imgui.text_colored('Pattern not found', 0.95, 0.3, 0.3, 1.0)
                except:
                    pass
            else:
                imgui.text_colored(f'DLL not found: {dll}', 0.95, 0.3, 0.3, 1.0)
            imgui.text('New:')
            imgui.same_line(40)
            imgui.set_next_item_width(50)
            _, opengl_version = imgui.input_text('##glver', opengl_version, 10)
            if imgui.button('APPLY', 60):
                apply_opengl_version(opengl_version)
            imgui.same_line(75)
            if imgui.button('RESTORE', 60):
                restore_opengl()
            imgui.separator()

            # FPS text changer
            imgui.text_colored('FPS TEXT CHANGER', 0.7, 0.75, 0.85, 1.0)
            if imgui.button('SCAN', 80):
                scan_fps_text()
            for dll_name in fps_dll_names:
                fnd = fps_status['found'].get(dll_name, None)
                if fnd:
                    imgui.text_colored(f'Found in {dll_name}', 0.4, 0.9, 0.6, 1.0)
                elif fnd is False:
                    imgui.text_colored(f'Not in {dll_name}', 0.95, 0.3, 0.3, 1.0)
            if any(fps_status['found'].values()):
                imgui.text('New (max 7):')
                imgui.same_line(120)
                imgui.set_next_item_width(80)
                changed, fps_text_user = imgui.input_text('##fps', fps_text_user, 10)
                if changed and len(fps_text_user) > fps_max_len:
                    fps_text_user = fps_text_user[:fps_max_len]
                if imgui.button('APPLY TEXT', 90):
                    apply_fps_text(fps_text_user)
                imgui.same_line(110)
                if imgui.button('RESTORE DEFAULT', 130):
                    restore_fps_text()
            imgui.separator()

            # Launcher
            imgui.text_colored('LAUNCHER', 0.7, 0.75, 0.85, 1.0)
            if is_process_running('HD-Player.exe'):
                if imgui.button('KILL BLUESTACKS', 140, 30):
                    os.system('taskkill /f /im HD-Player.exe')
                    add_log('Terminated', 'success')
            else:
                if imgui.button('LAUNCH BLUESTACKS', 140, 30):
                    subprocess.Popen(get_exe_path(), shell=True)
                    add_log('Launched', 'info')
            imgui.separator()

            # UI Scale
            imgui.text_colored('UI Scale', 0.7, 0.75, 0.85, 1.0)
            imgui.text('Current: ' + ui_scale_value)
            imgui.text('New: ')
            imgui.same_line()
            imgui.set_next_item_width(100)
            _, ui_scale_value = imgui.input_text('##uiscale', ui_scale_value, 10)
            if imgui.button('Set UI Scale', 100):
                write_ui_scale_to_config(ui_scale_value)

        # ----------------------------------------------------------
        # Tab 4: Settings (Paths, backups, import/export)
        # ----------------------------------------------------------
        elif current_tab == 4:
            imgui.text_colored('SETTINGS', 0.7, 0.75, 0.85, 1.0)
            imgui.spacing()
            imgui.text('UI Theme:')
            imgui.same_line(80)
            theme_list = list(THEMES.keys())
            current_idx = theme_list.index(current_theme) if current_theme in theme_list else 0
            changed_theme, new_idx = imgui.combo('##theme', current_idx, theme_list)
            if changed_theme:
                apply_theme(theme_list[new_idx])
            imgui.spacing()

            if imgui.button('Export Settings', 120):
                export_settings()
            imgui.same_line(140)
            if imgui.button('Import Settings', 120):
                import_settings()
            imgui.spacing()

            # Helper for path editing
            def edit_path(label, key, browse_func):
                cur_val = profile_paths[active_profile][key]
                imgui.text(label)
                imgui.same_line(150)
                _, new_val = imgui.input_text('##' + key, cur_val, 512)
                if new_val != cur_val:
                    profile_paths[active_profile][key] = new_val
                    if key == 'exe':
                        round_corners_status = check_round_corners()
                        scan_fps_text()
                imgui.same_line(w - 120)
                if imgui.button('Browse##' + key, 70):
                    sel = browse_func()
                    if sel:
                        profile_paths[active_profile][key] = sel
                        if key == 'exe':
                            round_corners_status = check_round_corners()
                            scan_fps_text()

            edit_path(f'{active_profile} Executable:', 'exe', browse_file)
            edit_path(f'{active_profile} Config:', 'conf', browse_conf_file)
            edit_path('OpenGL DLL:', 'opengl_dll', lambda: filedialog.askopenfilename(filetypes=[('DLL files', '*.dll')]))
            edit_path('Native DLL:', 'native_dll', lambda: filedialog.askopenfilename(filetypes=[('DLL files', '*.dll')]))

            imgui.separator()
            imgui.text(f'Backup EXE: {BACKUP_DIR}')
            imgui.text(f'Original Backup: {ORIG_BACKUP_DIR}')
            if imgui.button('Open Backup Folder', 140):
                os.startfile(BACKUP_DIR)
            if imgui.button('Create Backup Now', 140):
                create_backup_now()
            if imgui.button('Backup Manager', 140):
                show_backup_manager = not show_backup_manager
            if show_backup_manager:
                imgui.begin_child('backup_mgr', 0, 200, border=True)
                backups = list_backups()
                for b in backups:
                    imgui.text(b)
                    imgui.same_line(200)
                    if imgui.button(f'Restore##{b}', 60):
                        restore_backup(b)
                    imgui.same_line(270)
                    if imgui.button(f'Delete##{b}', 60):
                        delete_backup(b)
                imgui.end_child()
            if imgui.button('Restore All Original Files', 200):
                restore_all_original()

        # ----------------------------------------------------------
        # Tab 5: Info
        # ----------------------------------------------------------
        elif current_tab == 5:
            imgui.text_colored('SYSTEM INFORMATION', 0.7, 0.75, 0.85, 1.0)
            imgui.separator()
            for prof in ['MSI5', 'NXT']:
                exe = profile_paths[prof]['exe']
                if os.path.exists(exe):
                    imgui.text_colored(prof, 0.9, 0.5, 0.2, 1.0)
                    conf = profile_paths[prof]['conf']
                    imgui.text(f'Executable: {exe}')
                    ver = get_file_version(exe)
                    imgui.text(f'Version: {ver}')
                    if os.path.exists(conf):
                        inst = get_instances_for_info(conf)
                        if inst:
                            imgui.text(f'Instances ({len(inst)}):')
                            for disp, aver in inst:
                                imgui.text(f'  {disp} -> {aver}')
                        else:
                            imgui.text('No instances detected.')
                    else:
                        imgui.text('Config file not found.')
                    imgui.spacing()

        # ----------------------------------------------------------
        # Tab 6: Tutorial (customized with your branding)
        # ----------------------------------------------------------
        elif current_tab == 6:
            imgui.text_colored('TUTORIAL / FAQ', 0.7, 0.75, 0.85, 1.0)
            imgui.separator()
            imgui.text(f'Welcome to {BRAND_NAME} BlueStacks Customizer!')
            imgui.spacing()
            imgui.text('All Pro features are unlocked – enjoy!')
            imgui.spacing()
            imgui.text('Always make a backup first.\n')
            imgui.separator()
            imgui.text('COLORS TAB:')
            imgui.bullet_text('All colors (MSI5 & NXT) are fully editable.')
            imgui.bullet_text('Select colors, use presets, then click APPLY COLORS.')
            imgui.spacing()
            imgui.text('REMOVE TAB:')
            imgui.bullet_text('All removal options are available (no restrictions).')
            imgui.spacing()
            imgui.text('TITLEBAR TAB:')
            imgui.bullet_text('Version: scan, type new version, then APPLY. RESTORE reverts.')
            imgui.bullet_text('Instance Names: use Detect/Scan and then modify (config & EXE).')
            imgui.spacing()
            imgui.text('EXTRA TAB:')
            imgui.bullet_text('Round Corners, OpenGL Version, FPS Text, Launcher, UI Scale.')
            imgui.spacing()
            imgui.text('SETTINGS TAB:')
            imgui.bullet_text('Change theme, Export/Import settings, manage backups.')
            imgui.spacing()
            imgui.text('INFO TAB: shows installed emulators and instances.')
            imgui.spacing()
            imgui.text('If something goes wrong, use "Restore All Original Files" in Settings.')
            imgui.spacing()
            imgui.text_colored('FOLLOW US:', 0.9, 0.6, 0.1, 1.0)
            if imgui.button('Discord', 100):
                webbrowser.open(DISCORD_INVITE)
            imgui.same_line()
            if imgui.button('YouTube', 100):
                webbrowser.open(YT_CHANNEL)
            imgui.same_line()
            imgui.text(f'  {BRAND_NAME}')

        imgui.end_child()  # end Content

        # Log area
        imgui.set_cursor_pos((15, imgui.get_cursor_pos_y() + 5))
        imgui.begin_child('Log', w - 30, log_height, border=True)
        imgui.text_colored('LOG', 0.7, 0.75, 0.85, 1.0)
        imgui.same_line()
        imgui.text('Filter:')
        imgui.same_line()
        imgui.push_item_width(150)
        _, log_filter_text = imgui.input_text('##logfilter', log_filter_text, 100)
        imgui.pop_item_width()
        imgui.same_line(w - 200)
        if imgui.button('Copy Log', 70):
            try:
                import pyperclip
                pyperclip.copy('\n'.join(logs[-20:]))
                add_log('Log copied to clipboard', 'info')
            except:
                add_log('pyperclip not installed', 'warning')
        imgui.same_line(w - 120)
        if imgui.button('Clear', 50):
            logs.clear()
        imgui.separator()
        imgui.begin_child('LogScroll', w - 50, log_height - 40, border=False)
        for line in logs[-20:]:
            if log_filter_text and log_filter_text not in line:
                continue
            if '[OK]' in line:
                imgui.text_colored(line, 0.4, 0.9, 0.6, 1.0)
            elif '[ERROR]' in line:
                imgui.text_colored(line, 0.95, 0.3, 0.3, 1.0)
            else:
                imgui.text(line)
        imgui.end_child()
        imgui.end_child()  # end Log
        imgui.end()        # end Main

        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.destroy_window(window)
    glfw.terminate()

if __name__ == '__main__':
    # Request admin rights if not already
    if sys.platform == 'win32' and not is_admin():
        ctypes.windll.shell32.ShellExecuteW(None, 'runas', sys.executable, ' '.join(sys.argv), None, 1)
        sys.exit()
    main()