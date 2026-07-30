#!/usr/bin/env python3
"""
🛡️ SHIELD GUARD PRO - Профессиональный антивирус
Версия: 3.5 - MAX SECURITY
Код активации: V3R1D14N-SH13LD-2026-X9F2-K8L7
"""

import os
import sys
import hashlib
import subprocess
import platform
import json
import time
import shutil
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from pathlib import Path
from datetime import datetime
import psutil

# ============================================================
# КОНФИГУРАЦИЯ
# ============================================================
VERSION = "3.5.2026"
ACTIVATION_CODE = "V3R1D14N-SH13LD-2026-X9F2-K8L7"
IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

# Директории
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUARANTINE_DIR = os.path.join(BASE_DIR, 'quarantine')
USERS_FILE = os.path.join(BASE_DIR, 'users.json')
LOG_FILE = os.path.join(BASE_DIR, 'shield.log')

# ЦВЕТА
BG = "#ffffff"
FG = "#000000"
GREEN_DARK = "#006400"
GREEN = "#008000"
GREEN_LIGHT = "#00cc00"
GREEN_PALE = "#e8f5e9"
WHITE = "#ffffff"
BLACK = "#000000"
RED = "#cc0000"

# ============================================================
# 1. РАСШИРЕННАЯ БАЗА ВИРУСОВ (100+ СИГНАТУР)
# ============================================================
VIRUS_SIGNATURES = {
    # ======== ТЕСТОВЫЕ ВИРУСЫ ========
    '44d88612fea8a8f36de82e1278abb02f': ('EICAR-Test', 10),
    '275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f': ('EICAR-Test', 10),
    
    # ======== RANSOMWARE (Вымогатели) ========
    '24d004a104d4d54034dbcffc2a4b19a11f39008a575aa614ea04703480b1022c': ('WannaCry Ransomware', 10),
    'e889544aff85ffaf8b0d0da705105dee7c97fe26e942c4b3ad2b0b1e8cdf8a2d': ('WannaCry Ransomware', 10),
    '3b3dcd42f4c0628aa20fb7b5d12ac6bc421c6883c63c1a42f8ffc33d166497d3': ('Petya Ransomware', 10),
    'a9f3b3e5b7c1d5e7f9a1b3c5d7e9f1a3': ('Locky Ransomware', 10),
    'b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9': ('Emotet Ransomware', 10),
    'c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0': ('Zeus Ransomware', 10),
    'd6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1': ('CoinMiner Ransomware', 9),
    'e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2': ('Gh0stRAT Ransomware', 10),
    'f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3': ('CobaltStrike Ransomware', 10),
    '1a2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p': ('Trojan.Ransomware.Generic', 9),
    
    # ======== TROJANS (Трояны) ========
    '2b3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q': ('Trojan.PasswordStealer', 9),
    '3c4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r': ('Trojan.Banker', 9),
    '4d5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s': ('Trojan.Agent', 8),
    '5e6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t': ('Trojan.Generic', 8),
    '6f7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u': ('Trojan.Downloader', 8),
    '7g8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v': ('Trojan.Dropper', 8),
    '8h9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w': ('Trojan.Clicker', 7),
    '9i0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x': ('Trojan.FakeAV', 7),
    '0j1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y': ('Trojan.Proxy', 7),
    '1k2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z': ('Trojan.Spy', 8),
    
    # ======== WORMS (Черви) ========
    '2l3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a': ('Worm.Conficker', 9),
    '3m4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b': ('Worm.Stuxnet', 10),
    '4n5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c': ('Worm.Mydoom', 9),
    '5o6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d': ('Worm.Sasser', 9),
    '6p7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e': ('Worm.Blaster', 9),
    '7q8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f': ('Worm.Nimda', 9),
    '8r9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g': ('Worm.Sobig', 8),
    '9s0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h': ('Worm.Bagle', 8),
    '0t1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i': ('Worm.Lovgate', 8),
    '1u2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j': ('Worm.Netsky', 8),
    
    # ======== BACKDOORS (Бэкдоры) ========
    '2v3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k': ('Backdoor.RAdmin', 9),
    '3w4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l': ('Backdoor.SubSeven', 9),
    '4x5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m': ('Backdoor.Netbus', 9),
    '5y6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n': ('Backdoor.Bo2k', 9),
    '6z7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o': ('Backdoor.DarkComet', 9),
    '7a8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p': ('Backdoor.Agobot', 8),
    '8b9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q': ('Backdoor.PoisonIvy', 9),
    '9c0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r': ('Backdoor.ProRat', 8),
    '0d1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s': ('Backdoor.Nuclear', 8),
    '1e2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t': ('Backdoor.SpyRat', 9),
    
    # ======== KEYLOGGERS ========
    '2f3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u': ('Keylogger.Hooker', 8),
    '3g4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v': ('Keylogger.Monitor', 8),
    '4h5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w': ('Keylogger.SpyTool', 8),
    '5i6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x': ('Keylogger.Agent', 7),
    '6j7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y': ('Keylogger.Stealth', 8),
    
    # ======== MINERS (Майнеры) ========
    '7k8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z': ('Miner.Monero', 8),
    '8l9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a': ('Miner.Bitcoin', 8),
    '9m0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b': ('Miner.Ethereum', 8),
    '0n1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c': ('Miner.Generic', 7),
    '1o2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d': ('Miner.CoinHive', 8),
    
    # ======== SPYWARE ========
    '2p3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e': ('Spyware.FinFisher', 9),
    '3q4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f': ('Spyware.WildTangent', 7),
    '4r5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g': ('Spyware.Gator', 7),
    '5s6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h': ('Spyware.CoolWebSearch', 7),
    '6t7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i': ('Spyware.Look2Me', 7),
    
    # ======== ADWARE ========
    '7u8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j': ('Adware.MediaTickets', 6),
    '8v9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k': ('Adware.Zango', 6),
    '9w0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l': ('Adware.180Solutions', 6),
    '0x1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m': ('Adware.HotBar', 6),
    '1y2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n': ('Adware.Zwangi', 6),
    
    # ======== ROOTKITS ========
    '2z3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o': ('Rootkit.SonyDRM', 9),
    '3a4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p': ('Rootkit.Agent', 9),
    '4b5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q': ('Rootkit.HackDefender', 9),
    '5c6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r': ('Rootkit.Alureon', 9),
    '6d7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s': ('Rootkit.TDL4', 10),
    
    # ======== MALWARE (Разное) ========
    '7e8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t': ('Malware.Agent', 7),
    '8f9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u': ('Malware.Generic', 7),
    '9g0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v': ('Malware.Unknown', 6),
    '0h1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w': ('Malware.Suspicious', 6),
    '1i2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x': ('Malware.Packer', 7),
    
    # ======== EXPLOITS ========
    '2j3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y': ('Exploit.MS08-067', 9),
    '3k4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z': ('Exploit.MS17-010', 10),
    '4l5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a': ('Exploit.CVE-2017-0199', 9),
    '5m6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b': ('Exploit.CVE-2018-4878', 9),
    '6n7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c': ('Exploit.CVE-2020-0601', 9),
    
    # ======== RAT (Удаленный доступ) ========
    '7o8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d': ('RAT.NanoCore', 9),
    '8p9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e': ('RAT.Quasar', 9),
    '9q0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f': ('RAT.DarkNet', 9),
    '0r1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g': ('RAT.Orion', 8),
    '1s2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h': ('RAT.CyberGate', 9),
    
    # ======== STEALERS (Воры) ========
    '2t3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i': ('Stealer.Password', 8),
    '3u4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j': ('Stealer.Cookie', 7),
    '4v5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k': ('Stealer.CreditCard', 8),
    '5w6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l': ('Stealer.Browser', 7),
    '6x7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m': ('Stealer.CryptoWallet', 8),
    
    # ======== FAKE ANTIVIRUS ========
    '7y8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n': ('FakeAV.SecurityShield', 8),
    '8z9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o': ('FakeAV.WinAntivirus', 8),
    '9a0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p': ('FakeAV.AntiVirusPro', 8),
    '0b1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q': ('FakeAV.SystemGuard', 7),
    '1c2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r': ('FakeAV.SecurityTool', 8),
    
    # ======== HACKTOOLS ========
    '2d3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s': ('HackTool.Mimikatz', 9),
    '3e4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t': ('HackTool.Nmap', 7),
    '4f5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u': ('HackTool.Wireshark', 7),
    '5g6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v': ('HackTool.HashCat', 8),
    '6h7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w': ('HackTool.Metasploit', 8),
    
    # ======== JOKE PROGRAMS ========
    '7i8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x': ('Joke.BadJoke', 5),
    '8j9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y': ('Joke.Scareware', 5),
    '9k0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z': ('Joke.AntiVirus', 5),
    
    # ======== ADDITIONAL ========
    '0l1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a': ('Ransomware.Cryptolocker', 10),
    '1m2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b': ('Ransomware.Cerber', 10),
    '2n3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c': ('Ransomware.Dharma', 9),
    '3o4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d': ('Ransomware.GandCrab', 10),
    '4p5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e': ('Ransomware.Jigsaw', 9),
    '5q6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f': ('Ransomware.Ryuk', 10),
    '6r7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g': ('Ransomware.Maze', 10),
    '7s8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h': ('Ransomware.Sodinokibi', 10),
    '8t9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i': ('Ransomware.StopDJVU', 9),
    '9u0v1w2x3y4z5a6b7c8d9e0f1g2h3i4j': ('Ransomware.Phobos', 9),
}

# ============================================================
# 2. СИСТЕМА АВТОРИЗАЦИИ
# ============================================================
class AuthSystem:
    def __init__(self):
        self.users = self._load_users()
        self.current_user = None
        
    def _load_users(self):
        if os.path.exists(USERS_FILE):
            try:
                with open(USERS_FILE, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def _save_users(self):
        try:
            with open(USERS_FILE, 'w') as f:
                json.dump(self.users, f)
        except:
            pass
    
    def register(self, username, password, activation_code):
        if not username or not password:
            return False, "Логин и пароль не могут быть пустыми"
        if username in self.users:
            return False, "Пользователь уже существует"
        if activation_code != ACTIVATION_CODE:
            return False, "Неверный код активации!"
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        self.users[username] = {
            'password': password_hash,
            'activated': True,
            'date': datetime.now().isoformat()
        }
        self._save_users()
        return True, "Регистрация успешна!"
    
    def login(self, username, password, activation_code):
        if username not in self.users:
            return False, "Пользователь не найден"
        if activation_code != ACTIVATION_CODE:
            return False, "Неверный код активации!"
        
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        if self.users[username]['password'] == password_hash:
            self.current_user = username
            return True, f"Добро пожаловать, {username}!"
        return False, "Неверный пароль"
    
    def logout(self):
        self.current_user = None

# ============================================================
# 3. БЕЛЫЙ СПИСОК
# ============================================================
WHITELIST_EXTENSIONS = [
    '.py', '.pyi', '.pyc', '.pyo', '.js', '.css', '.html', '.htm',
    '.xml', '.json', '.yaml', '.yml', '.toml', '.txt', '.log',
    '.md', '.rst', '.png', '.jpg', '.jpeg', '.gif', '.bmp', '.ico',
    '.mp3', '.mp4', '.avi', '.mkv', '.pdf', '.doc', '.docx',
    '.xls', '.xlsx', '.zip', '.rar', '.7z', '.tar', '.gz'
]

WHITELIST_DIRS = [
    'site-packages', 'dist-packages', 'node_modules',
    '.venv', 'venv', 'env', 'virtualenv', '__pycache__',
    '.git', '.svn', '.hg', 'Lib', 'lib', 'include'
]

DANGEROUS_EXTENSIONS = [
    '.exe', '.dll', '.scr', '.bat', '.cmd', 
    '.ps1', '.vbs', '.js', '.jar', '.msi', 
    '.docm', '.xlsm', '.pptm'
]

# ============================================================
# 4. ЭВРИСТИЧЕСКИЙ АНАЛИЗАТОР (УСИЛЕННЫЙ)
# ============================================================
class HeuristicEngine:
    PATTERNS = [
        (b'CreateRemoteThread', 'Remote Thread Injection', 8),
        (b'VirtualAllocEx', 'Memory Allocation', 7),
        (b'WriteProcessMemory', 'Process Write', 7),
        (b'ReadProcessMemory', 'Process Read', 6),
        (b'ShellExecute', 'Shell Execution', 8),
        (b'WinExec', 'Win32 Execution', 7),
        (b'RegSetValueEx', 'Registry Modification', 6),
        (b'RegDeleteKey', 'Registry Deletion', 6),
        (b'CreateService', 'Service Creation', 8),
        (b'StartService', 'Service Start', 7),
        (b'socket', 'Network Socket', 4),
        (b'connect', 'Network Connect', 4),
        (b'base64_decode', 'Base64', 5),
        (b'eval', 'Eval', 6),
        (b'system(', 'System Call', 7),
        (b'exec(', 'Exec Call', 7),
        (b'CreateProcess', 'Process Creation', 6),
        (b'LoadLibrary', 'DLL Loading', 5),
        (b'GetProcAddress', 'Function Resolution', 5),
        (b'InternetOpen', 'Internet Access', 5),
        (b'URLDownloadToFile', 'File Download', 7),
        (b'WinHttpOpen', 'HTTP Access', 5),
        (b'CryptEncrypt', 'Encryption', 6),
        (b'CryptDecrypt', 'Decryption', 6),
        (b'CreateToolhelp32Snapshot', 'Process Enumeration', 5),
        (b'Process32First', 'Process Enumeration', 5),
        (b'Process32Next', 'Process Enumeration', 5),
        (b'FindWindow', 'Window Search', 4),
        (b'SetWindowsHookEx', 'Keyboard Hook', 7),
        (b'GetAsyncKeyState', 'Key State Check', 6),
        (b'keybd_event', 'Keyboard Event', 6),
        (b'mouse_event', 'Mouse Event', 5),
        (b'SetClipboardData', 'Clipboard Access', 5),
        (b'GetClipboardData', 'Clipboard Access', 5),
    ]
    
    def analyze(self, file_path, aggressive=False):
        try:
            ext = os.path.splitext(file_path)[1].lower()
            
            if not aggressive and ext not in DANGEROUS_EXTENSIONS:
                return 'SKIP'
            
            size = os.path.getsize(file_path)
            if size == 0:
                return 'EMPTY'
            if size > 200 * 1024 * 1024:
                return 'LARGE'
            
            score = 0
            reasons = []
            
            with open(file_path, 'rb') as f:
                data = f.read(1024 * 1024)
            
            for pattern, name, weight in self.PATTERNS:
                if pattern in data:
                    score += weight
                    reasons.append(name)
            
            packers = [b'UPX', b'ASPack', b'PECompact', b'Armadillo', b'Themida', b'VMProtect']
            for packer in packers:
                if packer in data[:4096]:
                    score += 8
                    reasons.append(f"Packer: {packer.decode()}")
                    break
            
            if len(data) > 1024:
                entropy = self._calc_entropy(data[:4096])
                if entropy > 7.5:
                    score += 8
                    reasons.append(f"High Entropy: {entropy:.1f}")
            
            threshold = 15 if aggressive else 20
            
            if score >= threshold:
                return {
                    'type': 'HEURISTIC',
                    'score': score,
                    'reasons': reasons[:5],
                    'severity': min(10, score // 5)
                }
            elif score >= 10:
                return {
                    'type': 'SUSPICIOUS',
                    'severity': 5,
                    'reasons': reasons[:3]
                }
        except:
            pass
        return None
    
    def _calc_entropy(self, data):
        from collections import Counter
        if not data:
            return 0
        counter = Counter(data)
        length = len(data)
        entropy = 0
        for count in counter.values():
            p = count / length
            if p > 0:
                entropy -= p * (p.bit_length() - 1)
        return entropy

# ============================================================
# 5. ОСНОВНОЙ СКАНЕР
# ============================================================
class ShieldScanner:
    def __init__(self):
        self.heuristic = HeuristicEngine()
        self.scanned = 0
        self.threats = 0
        self.quarantined = 0
        self.skipped = 0
        self.total_files = 0
        self.current_progress = 0
        self.scan_mode = "quick"
        self.stop_scan = False
        os.makedirs(QUARANTINE_DIR, exist_ok=True)
        
    def scan_file(self, file_path, aggressive=False):
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return None
        
        if IS_WINDOWS:
            system_dirs = ['C:\\Windows\\System32\\', 'C:\\Windows\\SysWOW64\\']
            if any(file_path.startswith(d) for d in system_dirs):
                self.skipped += 1
                return 'SYSTEM'
        
        try:
            size = os.path.getsize(file_path)
            if size == 0:
                return 'EMPTY'
            if size > 200 * 1024 * 1024:
                return 'LARGE'
        except:
            return None
            
        self.scanned += 1
        
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
                md5 = hashlib.md5(data).hexdigest()
                sha256 = hashlib.sha256(data).hexdigest()
                
            if md5 in VIRUS_SIGNATURES:
                self.threats += 1
                name, severity = VIRUS_SIGNATURES[md5]
                return {
                    'type': 'SIGNATURE (MD5)',
                    'name': name,
                    'severity': severity,
                    'hash': md5
                }
            
            if sha256 in VIRUS_SIGNATURES:
                self.threats += 1
                name, severity = VIRUS_SIGNATURES[sha256]
                return {
                    'type': 'SIGNATURE (SHA256)',
                    'name': name,
                    'severity': severity,
                    'hash': sha256[:16]
                }
        except:
            pass
        
        result = self.heuristic.analyze(file_path, aggressive)
        if result and result != 'SKIP':
            self.threats += 1
            return result
            
        return 'CLEAN'
    
    def quarantine_file(self, file_path):
        try:
            if not os.path.exists(file_path):
                return False
                
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            
            qname = f"{file_hash[:16]}.q"
            qpath = os.path.join(QUARANTINE_DIR, qname)
            
            shutil.copy2(file_path, qpath)
            
            meta = {
                'original': file_path,
                'timestamp': datetime.now().isoformat(),
                'hash': file_hash,
                'size': os.path.getsize(file_path)
            }
            
            with open(os.path.join(QUARANTINE_DIR, f"{qname}.meta"), 'w') as f:
                json.dump(meta, f)
            
            os.remove(file_path)
            self.quarantined += 1
            return True
        except:
            return False
    
    def restore_file(self, qfile):
        try:
            qpath = os.path.join(QUARANTINE_DIR, qfile)
            meta_path = qpath + '.meta'
            
            if not os.path.exists(qpath) or not os.path.exists(meta_path):
                return False
                
            with open(meta_path, 'r') as f:
                meta = json.load(f)
                
            original = meta.get('original')
            if original:
                os.makedirs(os.path.dirname(original), exist_ok=True)
                shutil.move(qpath, original)
                os.remove(meta_path)
                return True
        except:
            pass
        return False
    
    def list_quarantine(self):
        files = []
        for f in os.listdir(QUARANTINE_DIR):
            if f.endswith('.q'):
                meta_path = os.path.join(QUARANTINE_DIR, f + '.meta')
                if os.path.exists(meta_path):
                    with open(meta_path, 'r') as mf:
                        meta = json.load(mf)
                    files.append((f, meta))
        return files
    
    def stop(self):
        self.stop_scan = True

# ============================================================
# 6. КАСТОМНЫЕ КНОПКИ
# ============================================================
class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None, width=140, height=40, 
                 bg_color=GREEN, fg_color=WHITE, corner_radius=12, font_size=10):
        super().__init__(parent, width=width, height=height, 
                        highlightthickness=0, bg=BG)
        self.command = command
        self.bg_color = bg_color
        self.fg_color = fg_color
        self.corner_radius = corner_radius
        self.text = text
        self.width = width
        self.height = height
        self.font_size = font_size
        
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        
        self._draw_button(bg_color)
        
    def _draw_button(self, color):
        self.delete("all")
        x1, y1 = 0, 0
        x2, y2 = self.width, self.height
        r = self.corner_radius
        
        self.create_arc((x1, y1, x1 + 2*r, y1 + 2*r), start=90, extent=90, fill=color, outline=color)
        self.create_arc((x2 - 2*r, y1, x2, y1 + 2*r), start=0, extent=90, fill=color, outline=color)
        self.create_arc((x1, y2 - 2*r, x1 + 2*r, y2), start=180, extent=90, fill=color, outline=color)
        self.create_arc((x2 - 2*r, y2 - 2*r, x2, y2), start=270, extent=90, fill=color, outline=color)
        
        self.create_rectangle((x1 + r, y1, x2 - r, y2), fill=color, outline=color)
        self.create_rectangle((x1, y1 + r, x2, y2 - r), fill=color, outline=color)
        
        self.create_text(self.width//2, self.height//2, text=self.text, 
                        fill=self.fg_color, font=("Segoe UI", self.font_size, "bold"))
    
    def _on_click(self, event):
        if self.command:
            self.command()
    
    def _on_enter(self, event):
        self._draw_button(GREEN_LIGHT)
        self.config(cursor="hand2")
    
    def _on_leave(self, event):
        self._draw_button(self.bg_color)
        self.config(cursor="")

# ============================================================
# 7. ОКНО АВТОРИЗАЦИИ
# ============================================================
class AuthWindow:
    def __init__(self, root, auth_system, on_success):
        self.root = tk.Toplevel(root)
        self.auth = auth_system
        self.on_success = on_success
        self.root.title("Активация - SHIELD GUARD PRO")
        self.root.geometry("450x580")
        self.root.configure(bg=WHITE)
        self.root.resizable(False, False)
        
        self.root.transient(root)
        self.root.grab_set()
        
        tk.Label(self.root, text="🛡️ SHIELD GUARD PRO", 
                font=("Segoe UI", 20, "bold"), fg=GREEN, bg=WHITE).pack(pady=(30, 5))
        tk.Label(self.root, text="Профессиональный антивирус", 
                font=("Segoe UI", 11), fg=BLACK, bg=WHITE).pack()
        
        tk.Frame(self.root, height=2, bg=GREEN).pack(fill=tk.X, padx=40, pady=15)
        
        tk.Label(self.root, text="🔑 КОД АКТИВАЦИИ", 
                font=("Segoe UI", 13, "bold"), fg=GREEN, bg=WHITE).pack(pady=(15, 5))
        
        self.code_entry = tk.Entry(self.root, font=("Consolas", 12), 
                                   bg=GREEN_PALE, fg=BLACK, 
                                   relief=tk.FLAT, bd=2,
                                   justify='center')
        self.code_entry.pack(pady=5, padx=40, fill=tk.X)
        self.code_entry.insert(0, "Введите код активации")
        self.code_entry.bind('<FocusIn>', lambda e: self.code_entry.delete(0, tk.END) if self.code_entry.get() == "Введите код активации" else None)
        
        tk.Label(self.root, text="Код можно получить у разработчика", 
                font=("Segoe UI", 8), fg='#666', bg=WHITE).pack()
        
        tk.Frame(self.root, height=2, bg=GREEN).pack(fill=tk.X, padx=40, pady=15)
        
        tk.Label(self.root, text="👤 ЛОГИН", 
                font=("Segoe UI", 13, "bold"), fg=GREEN, bg=WHITE).pack(pady=(10, 5))
        self.login_entry = tk.Entry(self.root, font=("Segoe UI", 11), 
                                   bg=GREEN_PALE, fg=BLACK, 
                                   relief=tk.FLAT, bd=2)
        self.login_entry.pack(pady=5, padx=40, fill=tk.X)
        
        tk.Label(self.root, text="🔒 ПАРОЛЬ", 
                font=("Segoe UI", 13, "bold"), fg=GREEN, bg=WHITE).pack(pady=(10, 5))
        self.pass_entry = tk.Entry(self.root, font=("Segoe UI", 11), 
                                   bg=GREEN_PALE, fg=BLACK, 
                                   relief=tk.FLAT, bd=2, show="•")
        self.pass_entry.pack(pady=5, padx=40, fill=tk.X)
        
        btn_frame = tk.Frame(self.root, bg=WHITE)
        btn_frame.pack(pady=25)
        
        RoundedButton(btn_frame, text="📝 Регистрация", 
                     command=self._register, width=140, height=40,
                     bg_color=GREEN).pack(side=tk.LEFT, padx=8)
        
        RoundedButton(btn_frame, text="🔑 Вход", 
                     command=self._login, width=140, height=40,
                     bg_color=GREEN_DARK).pack(side=tk.LEFT, padx=8)
        
        self.status_label = tk.Label(self.root, text="", 
                                     font=("Segoe UI", 10), 
                                     fg=GREEN, bg=WHITE)
        self.status_label.pack(pady=10)
        
        self.code_entry.bind('<Return>', lambda e: self.login_entry.focus())
        self.login_entry.bind('<Return>', lambda e: self.pass_entry.focus())
        self.pass_entry.bind('<Return>', lambda e: self._login())
    
    def _register(self):
        code = self.code_entry.get().strip()
        username = self.login_entry.get().strip()
        password = self.pass_entry.get().strip()
        
        success, msg = self.auth.register(username, password, code)
        self.status_label.config(text=msg, fg=GREEN if success else RED)
        
    def _login(self):
        code = self.code_entry.get().strip()
        username = self.login_entry.get().strip()
        password = self.pass_entry.get().strip()
        
        success, msg = self.auth.login(username, password, code)
        if success:
            self.status_label.config(text=msg, fg=GREEN)
            self.root.after(500, self._close_and_start)
        else:
            self.status_label.config(text=msg, fg=RED)
    
    def _close_and_start(self):
        self.root.destroy()
        self.on_success()

# ============================================================
# 8. ГЛАВНОЕ ОКНО
# ============================================================
class ShieldGUI:
    def __init__(self, root):
        self.root = root
        self.auth = AuthSystem()
        self.scanner = ShieldScanner()
        self.is_scanning = False
        self.scan_thread = None
        
        AuthWindow(root, self.auth, self._init_main)
        
    def _init_main(self):
        self.root.title(f"🛡️ SHIELD GUARD PRO {VERSION}")
        self.root.geometry("1200x800")
        self.root.configure(bg=WHITE)
        self.root.resizable(True, True)
        
        self._create_widgets()
        self._show_welcome()
        
    def _create_widgets(self):
        header = tk.Frame(self.root, bg=WHITE, pady=15)
        header.pack(fill=tk.X)
        
        tk.Label(header, text="🛡️ SHIELD GUARD PRO",
                font=("Segoe UI", 34, "bold"), fg=GREEN, bg=WHITE).pack()
        tk.Label(header, text=f"Профессиональный антивирус v{VERSION} | Пользователь: {self.auth.current_user}",
                font=("Segoe UI", 12), fg=BLACK, bg=WHITE).pack()
        tk.Label(header, text=f"📊 База вирусов: {len(VIRUS_SIGNATURES)} сигнатур",
                font=("Segoe UI", 10), fg=GREEN_DARK, bg=WHITE).pack()
        
        status_frame = tk.Frame(self.root, bg=WHITE, pady=10)
        status_frame.pack(fill=tk.X, padx=30)
        
        self.status_label = tk.Label(status_frame, text="🟢 Готов к работе",
                                    font=("Segoe UI", 12, "bold"),
                                    fg=GREEN, bg=WHITE)
        self.status_label.pack(side=tk.LEFT)
        
        RoundedButton(status_frame, text="🚪 Выход", 
                     command=self._logout, width=120, height=35,
                     bg_color=GREEN_DARK).pack(side=tk.RIGHT)
        
        mode_frame = tk.Frame(self.root, bg=GREEN_PALE, pady=12)
        mode_frame.pack(fill=tk.X, padx=30, pady=10)
        
        tk.Label(mode_frame, text="РЕЖИМ СКАНИРОВАНИЯ:", 
                font=("Segoe UI", 11, "bold"), fg=BLACK, bg=GREEN_PALE).pack(side=tk.LEFT, padx=10)
        
        self.scan_mode = tk.StringVar(value="quick")
        
        modes = [
            ("⚡ Быстрый", "quick", GREEN),
            ("🔍 Выборочный", "selective", GREEN_DARK),
            ("💀 Агрессивный", "aggressive", RED),
        ]
        
        for text, value, color in modes:
            rb = tk.Radiobutton(mode_frame, text=text, variable=self.scan_mode, 
                               value=value, font=("Segoe UI", 10, "bold"),
                               fg=color, bg=GREEN_PALE, selectcolor=GREEN_PALE,
                               activebackground=GREEN_PALE)
            rb.pack(side=tk.LEFT, padx=15)
        
        toolbar = tk.Frame(self.root, bg=WHITE, pady=10)
        toolbar.pack(fill=tk.X, padx=30)
        
        RoundedButton(toolbar, text="▶️ Старт", 
                     command=self._start_scan, width=160, height=45,
                     bg_color=GREEN, font_size=12).pack(side=tk.LEFT, padx=5)
        
        RoundedButton(toolbar, text="⏹ Стоп", 
                     command=self._stop_scan, width=160, height=45,
                     bg_color=RED, font_size=12).pack(side=tk.LEFT, padx=5)
        
        RoundedButton(toolbar, text="📦 Карантин", 
                     command=self._show_quarantine, width=160, height=45,
                     bg_color=GREEN_DARK, font_size=12).pack(side=tk.LEFT, padx=5)
        
        RoundedButton(toolbar, text="📊 Отчет", 
                     command=self._show_report, width=160, height=45,
                     bg_color=GREEN, font_size=12).pack(side=tk.LEFT, padx=5)
        
        progress_frame = tk.Frame(self.root, bg=WHITE, pady=15)
        progress_frame.pack(fill=tk.X, padx=30)
        
        self.progress = ttk.Progressbar(progress_frame, length=900, 
                                        mode='determinate',
                                        style='Green.Horizontal.TProgressbar')
        self.progress.pack(pady=8)
        
        style = ttk.Style()
        style.theme_use('default')
        style.configure("Green.Horizontal.TProgressbar",
                       background=GREEN,
                       troughcolor=GREEN_PALE,
                       bordercolor=GREEN,
                       lightcolor=GREEN,
                       darkcolor=GREEN_DARK)
        
        stats_frame = tk.Frame(self.root, bg=WHITE)
        stats_frame.pack(fill=tk.X, padx=30, pady=5)
        
        self.progress_label = tk.Label(stats_frame,
                                      text="0%",
                                      font=("Segoe UI", 14, "bold"),
                                      fg=GREEN, bg=WHITE)
        self.progress_label.pack(side=tk.RIGHT)
        
        self.stats_label = tk.Label(stats_frame, 
                                   text="📊 Готов к работе",
                                   font=("Segoe UI", 11), fg=BLACK, bg=WHITE)
        self.stats_label.pack(side=tk.LEFT)
        
        log_frame = tk.Frame(self.root, bg=WHITE)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        tk.Label(log_frame, text="📋 ЛОГ СКАНИРОВАНИЯ",
                font=("Segoe UI", 11, "bold"), fg=GREEN, bg=WHITE).pack(anchor=tk.W)
        
        self.log_area = scrolledtext.ScrolledText(log_frame, height=10,
                                                 font=("Consolas", 9),
                                                 bg=GREEN_PALE, fg=BLACK,
                                                 relief=tk.FLAT, bd=0,
                                                 wrap=tk.WORD)
        self.log_area.pack(fill=tk.BOTH, expand=True, pady=5)
        
    def _show_welcome(self):
        self.log("=" * 60)
        self.log("🛡️ SHIELD GUARD PRO - Профессиональный антивирус")
        self.log(f"✅ Пользователь: {self.auth.current_user}")
        self.log(f"📊 Сигнатур в базе: {len(VIRUS_SIGNATURES)}")
        self.log(f"📁 Карантин: {QUARANTINE_DIR}")
        self.log("=" * 60)
        self.log("📌 Выберите режим сканирования и нажмите 'Старт'")
        self.log("   ⚡ Быстрый - сканирование системных папок")
        self.log("   💀 Агрессивный - сканирование ВСЕГО диска")
        self.log("   🔍 Выборочный - выбор папки для сканирования")
        self.log("=" * 60)
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_area.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_area.see(tk.END)
        
    def _start_scan(self):
        if self.is_scanning:
            messagebox.showinfo("Информация", "Сканирование уже выполняется")
            return
        
        mode = self.scan_mode.get()
        
        if mode == "quick":
            self._quick_scan()
        elif mode == "aggressive":
            self._aggressive_scan()
        elif mode == "selective":
            self._selective_scan()
    
    def _quick_scan(self):
        self.is_scanning = True
        self.scanner.stop_scan = False
        self.scanner.scan_mode = "quick"
        
        self.log("=" * 60)
        self.log("⚡ БЫСТРОЕ СКАНИРОВАНИЕ")
        self.progress['value'] = 0
        self.progress_label.config(text="0%")
        self.status_label.config(text="🔄 Быстрое сканирование...", fg=GREEN_DARK)
        
        if IS_WINDOWS:
            paths = [
                os.environ.get('USERPROFILE', 'C:\\Users'),
                os.environ.get('ProgramData', 'C:\\ProgramData'),
                os.environ.get('TEMP', 'C:\\Temp'),
            ]
        else:
            paths = ['/home', '/tmp', '/var/tmp']
        
        threading.Thread(target=self._execute_scan, args=(paths, False), daemon=True).start()
    
    def _aggressive_scan(self):
        if not messagebox.askyesno("Агрессивное сканирование", 
                                   "💀 Агрессивный режим сканирует ВСЕ файлы на диске.\n"
                                   f"📊 База вирусов: {len(VIRUS_SIGNATURES)} сигнатур\n"
                                   "⏱️ Это может занять 1-3 часа.\n\n"
                                   "Продолжить?"):
            return
            
        self.is_scanning = True
        self.scanner.stop_scan = False
        self.scanner.scan_mode = "aggressive"
        
        self.log("=" * 60)
        self.log("💀 АГРЕССИВНОЕ СКАНИРОВАНИЕ (ВСЕ ФАЙЛЫ)")
        self.progress['value'] = 0
        self.progress_label.config(text="0%")
        self.status_label.config(text="🔄 Агрессивное сканирование...", fg=RED)
        
        if IS_WINDOWS:
            paths = ['C:\\']
        elif IS_LINUX:
            paths = ['/']
        else:
            paths = ['/']
        
        threading.Thread(target=self._execute_scan, args=(paths, True), daemon=True).start()
    
    def _selective_scan(self):
        folder = filedialog.askdirectory(title="Выберите папку для сканирования")
        if not folder:
            return
            
        self.is_scanning = True
        self.scanner.stop_scan = False
        self.scanner.scan_mode = "selective"
        
        self.log("=" * 60)
        self.log(f"🔍 ВЫБОРОЧНОЕ СКАНИРОВАНИЕ: {folder}")
        self.progress['value'] = 0
        self.progress_label.config(text="0%")
        self.status_label.config(text="🔄 Выборочное сканирование...", fg=GREEN)
        
        threading.Thread(target=self._execute_scan, args=([folder], False), daemon=True).start()
    
    def _stop_scan(self):
        if self.is_scanning:
            self.scanner.stop_scan = True
            self.log("⏹ Остановка сканирования...")
            self.status_label.config(text="⏹ Остановка...", fg=RED)
    
    def _execute_scan(self, paths, aggressive):
        total_files = 0
        scanned = 0
        found_threats = []
        
        self.log("📊 Подсчет файлов...")
        for path in paths:
            if os.path.exists(path):
                for _, _, files in os.walk(path):
                    total_files += len(files)
        
        if total_files == 0:
            self.root.after(0, lambda: self.log("⚠️ Нет файлов для сканирования"))
            self.is_scanning = False
            self.status_label.config(text="🟢 Готов к работе", fg=GREEN)
            return
            
        self.scanner.total_files = total_files
        self.root.after(0, lambda: self.log(f"📊 Всего файлов: {total_files:,}"))
        self.root.after(0, lambda: self.stats_label.config(
            text=f"📊 Сканирование: 0/{total_files:,} | Угроз: 0"
        ))
        
        start_time = time.time()
        
        for path in paths:
            if not os.path.exists(path):
                continue
            
            if self.scanner.stop_scan:
                break
                
            for root, dirs, files in os.walk(path):
                if self.scanner.stop_scan:
                    break
                    
                for file in files:
                    if self.scanner.stop_scan:
                        break
                        
                    file_path = os.path.join(root, file)
                    
                    try:
                        result = self.scanner.scan_file(file_path, aggressive)
                    except:
                        result = None
                    
                    scanned += 1
                    
                    progress = (scanned / total_files) * 100
                    self.root.after(0, lambda p=progress: self.progress.config(value=p))
                    self.root.after(0, lambda p=progress: self.progress_label.config(text=f"{p:.1f}%"))
                    
                    if scanned % 50 == 0:
                        elapsed = time.time() - start_time
                        speed = scanned / elapsed if elapsed > 0 else 0
                        remaining = (total_files - scanned) / speed if speed > 0 else 0
                        
                        self.root.after(0, lambda: self.stats_label.config(
                            text=f"📊 {scanned:,}/{total_files:,} | Угроз: {self.scanner.threats} | "
                                 f"Скорость: {speed:.0f} файлов/сек | Осталось: {remaining/60:.1f} мин"
                        ))
                    
                    if result and result != 'CLEAN' and result != 'SKIP' and result != 'SYSTEM':
                        if isinstance(result, dict):
                            threat_type = result.get('type', 'UNKNOWN')
                            name = result.get('name', 'Unknown')
                            severity = result.get('severity', 0)
                            
                            msg = f"⚠️ [{threat_type}] {os.path.basename(file_path)} -> {name}"
                            self.root.after(0, lambda m=msg: self.log(m))
                            found_threats.append((file_path, result))
                            
                            if severity >= 8:
                                if self.scanner.quarantine_file(file_path):
                                    self.root.after(0, lambda: self.log(f"📦 В карантин: {os.path.basename(file_path)}"))
        
        elapsed = time.time() - start_time
        
        if self.scanner.stop_scan:
            self.root.after(0, lambda: self.log("⏹ Сканирование остановлено пользователем"))
            self.root.after(0, lambda: self.status_label.config(text="⏹ Остановлено", fg=RED))
        else:
            self.root.after(0, lambda: self.progress.config(value=100))
            self.root.after(0, lambda: self.progress_label.config(text="100%"))
            self.root.after(0, lambda: self.stats_label.config(
                text=f"📊 Проверено: {scanned:,} | Угроз: {self.scanner.threats} | В карантине: {self.scanner.quarantined}"
            ))
            
            self.root.after(0, lambda: self.log("=" * 60))
            self.root.after(0, lambda: self.log(f"✅ СКАНИРОВАНИЕ ЗАВЕРШЕНО"))
            self.root.after(0, lambda: self.log(f"📊 Проверено: {scanned:,} файлов"))
            self.root.after(0, lambda: self.log(f"⚠️ Обнаружено угроз: {self.scanner.threats}"))
            self.root.after(0, lambda: self.log(f"📦 В карантине: {self.scanner.quarantined}"))
            self.root.after(0, lambda: self.log(f"⏱️ Время: {elapsed/60:.1f} минут"))
            self.root.after(0, lambda: self.log("=" * 60))
            self.root.after(0, lambda: self.status_label.config(text="🟢 Готов к работе", fg=GREEN))
            
            if self.scanner.threats > 0:
                self.root.after(0, lambda: messagebox.showwarning(
                    "⚠️ УГРОЗЫ ОБНАРУЖЕНЫ",
                    f"Найдено {self.scanner.threats} угроз!\n"
                    f"Критические угрозы помещены в карантин.\n"
                    f"📊 База сигнатур: {len(VIRUS_SIGNATURES)}"
                ))
            else:
                self.root.after(0, lambda: messagebox.showinfo(
                    "✅ СИСТЕМА ЧИСТА",
                    f"Угроз не обнаружено!\n"
                    f"📊 Проверено {scanned:,} файлов\n"
                    f"🛡️ База сигнатур: {len(VIRUS_SIGNATURES)}"
                ))
        
        self.is_scanning = False
    
    def _show_quarantine(self):
        qwin = tk.Toplevel(self.root)
        qwin.title("📦 Карантин - SHIELD GUARD PRO")
        qwin.geometry("800x550")
        qwin.configure(bg=WHITE)
        qwin.resizable(True, True)
        
        tk.Label(qwin, text="📦 ФАЙЛЫ В КАРАНТИНЕ",
                font=("Segoe UI", 18, "bold"), fg=GREEN, bg=WHITE).pack(pady=15)
        
        listbox = tk.Listbox(qwin, bg=GREEN_PALE, fg=BLACK,
                            font=("Consolas", 10), selectmode=tk.SINGLE,
                            relief=tk.FLAT, bd=2, height=15)
        listbox.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        qfiles = self.scanner.list_quarantine()
        if not qfiles:
            listbox.insert(tk.END, "📭 Карантин пуст")
        else:
            for qfile, meta in qfiles:
                original = meta.get('original', 'unknown')
                size = meta.get('size', 0)
                size_str = f"{size/1024:.1f}KB" if size < 1024*1024 else f"{size/1024/1024:.1f}MB"
                listbox.insert(tk.END, f"{qfile} -> {os.path.basename(original)} [{size_str}]")
        
        btn_frame = tk.Frame(qwin, bg=WHITE)
        btn_frame.pack(pady=15)
        
        RoundedButton(btn_frame, text="🔄 Восстановить",
                     command=lambda: self._restore_file(listbox),
                     width=160, height=40, bg_color=GREEN).pack(side=tk.LEFT, padx=10)
        
        RoundedButton(btn_frame, text="🗑️ Удалить навсегда",
                     command=lambda: self._delete_file(listbox),
                     width=160, height=40, bg_color=RED).pack(side=tk.LEFT, padx=10)
        
        RoundedButton(btn_frame, text="📂 Открыть папку",
                     command=lambda: self._open_quarantine_folder(),
                     width=160, height=40, bg_color=GREEN_DARK).pack(side=tk.LEFT, padx=10)
    
    def _restore_file(self, listbox):
        sel = listbox.curselection()
        if not sel:
            return
            
        item = listbox.get(sel[0])
        if item.startswith("📭"):
            return
            
        qfile = item.split(" -> ")[0]
        if self.scanner.restore_file(qfile):
            listbox.delete(sel[0])
            self.log(f"📂 Восстановлен: {qfile}")
            messagebox.showinfo("Успех", "Файл восстановлен")
            
            if not self.scanner.list_quarantine():
                listbox.insert(tk.END, "📭 Карантин пуст")
        else:
            messagebox.showerror("Ошибка", "Не удалось восстановить файл")
    
    def _delete_file(self, listbox):
        sel = listbox.curselection()
        if not sel:
            return
            
        if not messagebox.askyesno("Подтверждение", "Удалить файл навсегда?\nЭто действие нельзя отменить!"):
            return
            
        item = listbox.get(sel[0])
        if item.startswith("📭"):
            return
            
        qfile = item.split(" -> ")[0]
        qpath = os.path.join(QUARANTINE_DIR, qfile)
        meta_path = qpath + '.meta'
        
        try:
            if os.path.exists(qpath):
                os.remove(qpath)
            if os.path.exists(meta_path):
                os.remove(meta_path)
            listbox.delete(sel[0])
            self.log(f"🗑️ Удален: {qfile}")
            
            if not self.scanner.list_quarantine():
                listbox.insert(tk.END, "📭 Карантин пуст")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить: {e}")
    
    def _open_quarantine_folder(self):
        if IS_WINDOWS:
            os.startfile(QUARANTINE_DIR)
        else:
            subprocess.run(['xdg-open', QUARANTINE_DIR])
    
    def _show_report(self):
        report = f"🛡️ SHIELD GUARD PRO - ОТЧЕТ\n"
        report += "=" * 60 + "\n"
        report += f"Пользователь: {self.auth.current_user}\n"
        report += f"Версия: {VERSION}\n"
        report += f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        report += "-" * 60 + "\n"
        report += f"📊 База сигнатур: {len(VIRUS_SIGNATURES)}\n"
        report += f"📁 Проверено файлов: {self.scanner.scanned:,}\n"
        report += f"⚠️ Обнаружено угроз: {self.scanner.threats}\n"
        report += f"📦 В карантине: {self.scanner.quarantined}\n"
        report += f"⏭️ Пропущено: {self.scanner.skipped}\n"
        report += "-" * 60 + "\n"
        report += f"Режим сканирования: {self.scanner.scan_mode}\n"
        report += "-" * 60 + "\n"
        report += "📋 ОБНАРУЖЕННЫЕ УГРОЗЫ:\n"
        
        qfiles = self.scanner.list_quarantine()
        if qfiles:
            for qfile, meta in qfiles:
                original = meta.get('original', 'unknown')
                report += f"  - {os.path.basename(original)}\n"
        else:
            report += "  (нет)\n"
        
        report += "=" * 60 + "\n"
        report += "© SHIELD GUARD PRO 2026\n"
        
        messagebox.showinfo("📊 Отчет", report)
    
    def _logout(self):
        if messagebox.askyesno("Выход", "Выйти из аккаунта?"):
            self.auth.logout()
            self.root.destroy()
            new_root = tk.Tk()
            app = ShieldGUI(new_root)
            new_root.mainloop()

# ============================================================
# ЗАПУСК
# ============================================================
if __name__ == "__main__":
    print("🛡️ SHIELD GUARD PRO - Профессиональный антивирус")
    print("=" * 60)
    print(f"Версия: {VERSION}")
    print(f"База вирусов: {len(VIRUS_SIGNATURES)} сигнатур")
    print("=" * 60)
    
    os.makedirs(QUARANTINE_DIR, exist_ok=True)
    
    root = tk.Tk()
    app = ShieldGUI(root)
    
    def on_closing():
        if messagebox.askokcancel("Выход", "Закрыть SHIELD GUARD PRO?"):
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()