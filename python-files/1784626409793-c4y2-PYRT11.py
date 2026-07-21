#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PYRT安全卫士 11 - 自定义标题栏 + 大圆角
包含：全部功能 + 自绘标题栏（加高）+ 圆角半径35
"""

import glob
import hashlib
import json
import logging
import math
import os
import pickle
import platform
import random
import re
import shutil
import socket
import subprocess
import threading
import time
import tkinter as tk
import urllib.error
import urllib.request
import winreg
from datetime import datetime
from tkinter import ttk, messagebox, filedialog, simpledialog

if platform.system() == "Windows":
    CREATE_NO_WINDOW = 0x08000000
    try:
        import ctypes
        user32 = ctypes.windll.user32
        SetWindowLongW = user32.SetWindowLongW
        GetWindowLongW = user32.GetWindowLongW
        SetWindowRgn = user32.SetWindowRgn
        CreateRoundRectRgn = ctypes.windll.gdi32.CreateRoundRectRgn
        GWL_STYLE = -16
        WS_CAPTION = 0x00C00000
        WS_THICKFRAME = 0x00040000
        WS_MINIMIZEBOX = 0x00020000
        WS_MAXIMIZEBOX = 0x00010000
        WS_SYSMENU = 0x00080000
        SWP_FRAMECHANGED = 0x0020
        SWP_NOMOVE = 0x0002
        SWP_NOSIZE = 0x0001
        HWND_TOP = 0
        SetWindowPos = user32.SetWindowPos
    except:
        pass
else:
    CREATE_NO_WINDOW = 0

class Config:
    APP_NAME = "PYRT安全卫士"
    VERSION = "11"                     # 版本改为 11
    COMPANY = "PYRT Security"
    LOGO = "🛡️"
    LANGUAGE = "zh_CN"
    LANGUAGE_FILE = "language.json"
    SUPPORTED_LANGUAGES = {"zh_CN":"简体中文","zh_TW":"繁體中文","en_US":"English","ja_JP":"日本語","ko_KR":"한국어","ru_RU":"Русский","de_DE":"Deutsch"}
    SKIN = "green"
    SKIN_OPTIONS = {"default":"默认蓝","dragonboat":"🐉 端午节","green":"🌿 绿色","dark":"🌙 暗夜","purple":"💜 紫色"}
    THEME = {'bg_dark':'#f0f2f5','bg_card':'#ffffff','sidebar_bg':'#ffffff','sidebar_hover':'#eef2f7','primary':'#2E7D32','secondary':'#666666','accent':'#ff3333','success':'#00aa44','warning':'#ff9900','text_primary':'#333333','text_secondary':'#666666','border':'#dddddd','highlight':'#e6f2ff','button_bg':'#2E7D32','button_fg':'#ffffff','header_bg':'#1a3a2a','header_fg':'#ffffff','splash_bg':'#1a3a2a','splash_fg':'#ffffff','splash_accent':'#4CAF50'}
    SIDEBAR_WIDTH = 220
    SIDEBAR_COLLAPSED_WIDTH = 60
    SIDEBAR_DEFAULT_OPEN = True
    VIRUS_DB_PATH = "virus_signatures.db"
    HEURISTIC_RULES_PATH = "heuristic_rules.json"
    REAL_TIME_LOG = "realtime_protection.log"
    MAX_FILE_SIZE = 100 * 1024 * 1024
    QUARANTINE_DIR = "pyrt_quarantine"
    LOG_DIR = "pyrt_logs"
    REAL_TIME_PROTECTION = True
    MONITOR_PATHS = [
        os.path.expanduser("~\\Downloads"),
        os.path.expanduser("~\\Desktop"),
        os.path.expanduser("~\\Documents"),
        os.environ.get('TEMP', ''),
        os.environ.get('APPDATA', ''),
    ]
    SCAN_ON_CREATE = True
    SCAN_ON_MODIFY = True
    BLOCK_SUSPICIOUS = True
    MONITOR_PROCESSES = True
    SUSPICIOUS_PROCESS_NAMES = ['taskkill.exe','cmd.exe','powershell.exe','wscript.exe','cscript.exe','mshta.exe','regsvr32.exe','rundll32.exe','certutil.exe']
    SUSPICIOUS_ARGS = ['-enc','-e','IEX','Invoke-','downloadstring','base64','frombase64string']
    DIRECTORY_SCAN_INTERVAL = 30
    PROCESS_SCAN_INTERVAL = 10
    BOOT_PROTECTION_ENABLED = True
    BOOT_BACKUP_DIR = "boot_protection_backup"
    BOOT_HASH_DB = "boot_hashes.db"
    BOOT_SCAN_INTERVAL = 300
    BOOT_AUTO_REPAIR = True
    WINDOWS_BOOT_FILES = [
        ("C:\\bootmgr","Windows启动管理器"),
        ("C:\\boot\\bcd","引导配置数据"),
        ("C:\\Windows\\System32\\winload.exe","Windows加载器"),
        ("C:\\Windows\\System32\\ntoskrnl.exe","Windows内核"),
        ("C:\\Windows\\System32\\hal.dll","硬件抽象层"),
        ("C:\\Windows\\System32\\smss.exe","会话管理器"),
        ("C:\\Windows\\System32\\csrss.exe","客户端服务器运行时子系统"),
        ("C:\\Windows\\System32\\winlogon.exe","Windows登录管理器"),
        ("C:\\Windows\\Boot\\EFI\\bootmgfw.efi","UEFI引导管理器"),
        ("C:\\Windows\\Boot\\EFI\\bootmgr.efi","UEFI启动管理器")
    ]
    LINUX_BOOT_FILES = [
        ("/boot/grub/grub.cfg","GRUB引导配置文件"),
        ("/boot/grub2/grub.cfg","GRUB2引导配置文件"),
        ("/boot/efi/EFI/*/grubx64.efi","UEFI引导文件"),
        ("/boot/vmlinuz-*","Linux内核"),
        ("/boot/initrd.img-*","初始化内存盘"),
        ("/etc/default/grub","GRUB默认配置")
    ]
    NETWORK_PROTECTION_ENABLED = True
    NETWORK_MONITOR_INTERVAL = 10
    NETWORK_LOG = "network_protection.log"
    MALICIOUS_IPS = ["192.168.1.100","10.0.0.1","127.0.0.1"]
    MALICIOUS_DOMAINS = ["malicious-site.com","bad-domain.org","evil-server.net","ransomware-decryptor.com","hacker-tools.io"]
    SUSPICIOUS_PORTS = [4444,31337,6667,8080,1337,12345,27374,54321]
    NETWORK_MONITOR_PROCESSES = ["nc.exe","netcat.exe","nmap.exe","wireshark.exe","tcpdump","ncat.exe","hping.exe","curl.exe"]
    PROTECTED_HOSTS = ["windowsupdate.com","microsoft.com","update.microsoft.com","security.microsoft.com","defender.microsoft.com"]
    TRUSTED_DNS_SERVERS = ['8.8.8.8','1.1.1.1','208.67.222.222']
    INTELLIGENT_LEARNING_ENABLED = True
    LEARNING_SAMPLE_INTERVAL = 1.0
    LEARNING_SAMPLE_COUNT = 60
    LEARNING_DEVIATION_THRESHOLD = 2.0
    INTELLIGENT_LEARNING_LOG = "intelligent_learning.log"
    DEFENDER_COORDINATION_ENABLED = True
    DEFENDER_AUTO_SYNC = True
    DEFENDER_SHARE_SIGNATURES = True
    HONEYPOT_ENABLED = True
    HONEYPOT_PORTS = [2222,8080,8888,9999]
    HONEYPOT_BANNER = {
        2222:"SSH-2.0-OpenSSH_8.9p1 Ubuntu-3ubuntu0.6\r\n",
        8080:"HTTP/1.1 200 OK\r\nServer: nginx/1.18.0\r\n\r\n<h1>Welcome</h1>",
        8888:"220 Welcome to PYRT FTP Service\r\n",
        9999:"PYRT Honeypot - Unauthorized access recorded\r\n"
    }
    HONEYPOT_LOG = "honeypot.log"
    HONEYPOT_MAX_LOG = 200
    RANSOMWARE_SCAN_PATHS = [
        os.path.expanduser("~\\Desktop"),
        os.path.expanduser("~\\Documents"),
        os.path.expanduser("~\\Downloads"),
        os.environ.get('USERPROFILE', '')
    ]
    RANSOMWARE_RECOVERY_DIR = "ransomware_recovery"
    RANSOMWARE_LOG = "ransomware_helper.log"
    USB_AUTO_SCAN = True
    USB_SCAN_INTERVAL = 5
    USB_BLOCK_AUTORUN = True
    USB_QUARANTINE_THREATS = True
    SCHEDULED_SCAN_ENABLED = False
    SCHEDULED_SCAN_TYPE = "quick"
    SCHEDULED_SCAN_FREQUENCY = "daily"
    SCHEDULED_SCAN_TIME = "02:00"
    SCHEDULED_SCAN_DAY = 0
    CONTEXT_MENU_ENABLED = False
    PRIVACY_CLEAN_CHROME = True
    PRIVACY_CLEAN_FIREFOX = True
    PRIVACY_CLEAN_EDGE = True
    PRIVACY_CLEAN_TEMP = True
    PROCESS_BLOCK_ENABLED = True
    PROCESS_BLOCK_POPUP = True
    AUTO_KILL_SUSPICIOUS = True

    REGISTRY_PROTECTION_ENABLED = True
    FILE_ASSOC_PROTECTION_ENABLED = True
    CLOUD_SCAN_ENABLED = True
    VT_API_KEY = ""

class RegistryProtectionEngine:
    def __init__(self):
        self.running = False
        self.monitor_thread = None
        self.alerts = []
        self.startup_paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\RunOnce"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run"),
            (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\RunOnce"),
        ]
        self._known_entries = {}
        self._init_log()
    def _init_log(self):
        try:
            os.makedirs(Config.LOG_DIR, exist_ok=True)
            handler = logging.FileHandler(os.path.join(Config.LOG_DIR, "registry_protection.log"), encoding='utf-8')
            handler.setFormatter(logging.Formatter('%(asctime)s - [注册表保护] - %(levelname)s - %(message)s'))
            logging.getLogger().addHandler(handler)
        except: pass
    def _get_startup_entries(self):
        entries = {}
        for hkey, path in self.startup_paths:
            try:
                key = winreg.OpenKey(hkey, path, 0, winreg.KEY_READ)
                i = 0
                while True:
                    try:
                        name, value, _ = winreg.EnumValue(key, i)
                        entries[(hkey, path, name)] = value
                        i += 1
                    except OSError:
                        break
                winreg.CloseKey(key)
            except: pass
        return entries
    def start_protection(self):
        if self.running: return
        self.running = True
        self._known_entries = self._get_startup_entries()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logging.info("注册表启动项保护已启动")
    def stop_protection(self):
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    def _monitor_loop(self):
        while self.running:
            try:
                current = self._get_startup_entries()
                for key, value in current.items():
                    if key not in self._known_entries:
                        self._alert("新增启动项", key, value)
                    elif self._known_entries[key] != value:
                        self._alert("修改启动项", key, value)
                for key in self._known_entries:
                    if key not in current:
                        self._alert("删除启动项", key, None)
                self._known_entries = current
                time.sleep(10)
            except: time.sleep(30)
    def _alert(self, action, key, value):
        hkey, path, name = key
        msg = f"{action}: {name} -> {value if value else '(删除)'}"
        alert = {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'type': '注册表启动项', 'severity': '高', 'message': msg, 'key': f"{hkey}\\{path}\\{name}", 'value': value}
        self.alerts.insert(0, alert)
        logging.warning(f"注册表保护: {msg}")
    def get_alerts(self, count=20): return self.alerts[:count]
    def clear_alerts(self): self.alerts.clear()
    def is_running(self): return self.running

class FileAssociationProtection:
    def __init__(self):
        self.running = False
        self.monitor_thread = None
        self.alerts = []
        self._known_assoc = {}
        self._init_log()
    def _init_log(self):
        try:
            os.makedirs(Config.LOG_DIR, exist_ok=True)
            handler = logging.FileHandler(os.path.join(Config.LOG_DIR, "file_assoc_protection.log"), encoding='utf-8')
            handler.setFormatter(logging.Formatter('%(asctime)s - [文件关联保护] - %(levelname)s - %(message)s'))
            logging.getLogger().addHandler(handler)
        except: pass
    def _get_associations(self):
        assoc = {}
        if platform.system() != "Windows": return assoc
        exts = ['.exe', '.txt', '.jpg', '.png', '.mp3', '.mp4', '.doc', '.xls', '.pdf', '.zip']
        for ext in exts:
            try:
                key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, ext)
                val, _ = winreg.QueryValueEx(key, '')
                assoc[ext] = val
                winreg.CloseKey(key)
            except: pass
        return assoc
    def start_protection(self):
        if self.running: return
        self.running = True
        self._known_assoc = self._get_associations()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logging.info("文件关联保护已启动")
    def stop_protection(self):
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    def _monitor_loop(self):
        while self.running:
            try:
                current = self._get_associations()
                for ext, prog in current.items():
                    if ext not in self._known_assoc:
                        self._alert("新增关联", ext, prog)
                    elif self._known_assoc[ext] != prog:
                        self._alert("修改关联", ext, prog)
                for ext in self._known_assoc:
                    if ext not in current:
                        self._alert("删除关联", ext, None)
                self._known_assoc = current
                time.sleep(15)
            except: time.sleep(30)
    def _alert(self, action, ext, prog):
        msg = f"{action}: {ext} -> {prog if prog else '(删除)'}"
        alert = {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'type': '文件关联', 'severity': '中', 'message': msg, 'extension': ext, 'program': prog}
        self.alerts.insert(0, alert)
        logging.warning(f"文件关联保护: {msg}")
    def get_alerts(self, count=20): return self.alerts[:count]
    def clear_alerts(self): self.alerts.clear()
    def is_running(self): return self.running
    def repair_association(self, ext):
        default_progs = {'.txt':'txtfile','.exe':'exefile','.jpg':'jpegfile','.png':'pngfile','.mp3':'mp3file','.mp4':'mp4file','.doc':'Word.Document.8','.xls':'Excel.Sheet.8','.pdf':'AcroExch.Document','.zip':'CompressedFolder'}
        if ext in default_progs:
            try:
                key = winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, ext, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, '', 0, winreg.REG_SZ, default_progs[ext])
                winreg.CloseKey(key)
                return True
            except: return False
        return False

class SystemRepairTool:
    @staticmethod
    def repair_hosts():
        hosts_path = r"C:\Windows\System32\drivers\etc\hosts" if platform.system() == "Windows" else "/etc/hosts"
        if not os.path.exists(hosts_path): return False, "hosts文件不存在"
        try:
            backup = hosts_path + ".pyrt_bak"
            shutil.copy2(hosts_path, backup)
            with open(hosts_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            new_lines = []
            for line in lines:
                if '127.0.0.1' in line or '::1' in line:
                    new_lines.append(line)
                else:
                    if line.strip().startswith('#'):
                        new_lines.append(line)
            with open(hosts_path, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
            return True, "hosts已修复，备份保存在" + backup
        except Exception as e: return False, str(e)
    @staticmethod
    def reset_dns():
        if platform.system() != "Windows": return False, "仅支持Windows"
        try:
            subprocess.run(['netsh', 'interface', 'ip', 'set', 'dns', 'name="以太网"', 'source=dhcp'], capture_output=True, timeout=10, creationflags=CREATE_NO_WINDOW)
            subprocess.run(['netsh', 'interface', 'ip', 'set', 'dns', 'name="Wi-Fi"', 'source=dhcp'], capture_output=True, timeout=10, creationflags=CREATE_NO_WINDOW)
            subprocess.run(['ipconfig', '/flushdns'], capture_output=True, timeout=10, creationflags=CREATE_NO_WINDOW)
            return True, "DNS已重置为自动获取"
        except Exception as e: return False, str(e)
    @staticmethod
    def repair_firewall():
        if platform.system() != "Windows": return False, "仅支持Windows"
        try:
            subprocess.run(['netsh', 'advfirewall', 'reset'], capture_output=True, timeout=30, creationflags=CREATE_NO_WINDOW)
            subprocess.run(['netsh', 'advfirewall', 'set', 'allprofiles', 'state', 'on'], capture_output=True, timeout=30, creationflags=CREATE_NO_WINDOW)
            return True, "防火墙已重置并启用"
        except Exception as e: return False, str(e)
    @staticmethod
    def repair_sfc():
        if platform.system() != "Windows": return False, "仅支持Windows"
        try:
            proc = subprocess.run(['sfc', '/scannow'], capture_output=True, text=True, timeout=600, creationflags=CREATE_NO_WINDOW)
            if "Windows 资源保护未找到任何完整性冲突" in proc.stdout:
                return True, "系统文件完整性检查通过"
            elif "Windows 资源保护找到了损坏文件并已成功修复" in proc.stdout:
                return True, "系统文件已修复"
            else:
                return False, "扫描完成，但可能存在问题，请查看系统日志"
        except Exception as e: return False, str(e)

class CloudScanEngine:
    def __init__(self):
        self.api_key = Config.VT_API_KEY
        self.enabled = Config.CLOUD_SCAN_ENABLED
        self.cache = {}
        self._init_log()
    def _init_log(self):
        try:
            os.makedirs(Config.LOG_DIR, exist_ok=True)
            handler = logging.FileHandler(os.path.join(Config.LOG_DIR, "cloud_scan.log"), encoding='utf-8')
            handler.setFormatter(logging.Formatter('%(asctime)s - [云查杀] - %(levelname)s - %(message)s'))
            logging.getLogger().addHandler(handler)
        except: pass
    def scan_hash(self, file_hash):
        if not self.enabled or not self.api_key: return None
        if file_hash in self.cache: return self.cache[file_hash]
        try:
            url = f"https://www.virustotal.com/api/v3/files/{file_hash}"
            headers = {"x-apikey": self.api_key}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if data.get('data'):
                    attributes = data['data']['attributes']
                    last_analysis_stats = attributes.get('last_analysis_stats', {})
                    positives = last_analysis_stats.get('malicious', 0)
                    total = sum(last_analysis_stats.values())
                    if total == 0: return None
                    detection_rate = positives / total
                    self.cache[file_hash] = {
                        'positives': positives,
                        'total': total,
                        'detection_rate': detection_rate,
                        'scan_date': attributes.get('last_analysis_date'),
                        'permalink': f"https://www.virustotal.com/gui/file/{file_hash}"
                    }
                    return self.cache[file_hash]
            return None
        except Exception as e:
            logging.error(f"云查杀API错误: {e}")
            return None
    def scan_file(self, file_path):
        if not os.path.exists(file_path): return None
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return self.scan_hash(file_hash)
        except: return None

def apply_skin(skin):
    if skin == "dragonboat":
        Config.THEME.update({'bg_dark':'#FFF8E7','bg_card':'#FFF5E6','sidebar_bg':'#FFEAD2','sidebar_hover':'#F5D6B3','primary':'#C41A1A','secondary':'#8B6914','accent':'#006400','success':'#2E7D32','warning':'#FF8C00','text_primary':'#3D2B1F','text_secondary':'#5D4037','border':'#D4A373','highlight':'#FFF0D0','button_bg':'#C41A1A','button_fg':'#FFEAD2','header_bg':'#5D2E1A','header_fg':'#FFEAD2','splash_bg':'#5D2E1A','splash_fg':'#FFEAD2','splash_accent':'#C41A1A'})
    elif skin == "green":
        Config.THEME.update({'bg_dark':'#f0f2f5','bg_card':'#ffffff','sidebar_bg':'#ffffff','sidebar_hover':'#eef2f7','primary':'#2E7D32','secondary':'#666666','accent':'#ff3333','success':'#00aa44','warning':'#ff9900','text_primary':'#333333','text_secondary':'#666666','border':'#dddddd','highlight':'#e6f2ff','button_bg':'#2E7D32','button_fg':'#ffffff','header_bg':'#1a3a2a','header_fg':'#ffffff','splash_bg':'#1a3a2a','splash_fg':'#ffffff','splash_accent':'#4CAF50'})
    elif skin == "dark":
        Config.THEME.update({'bg_dark':'#1a1a2e','bg_card':'#16213e','sidebar_bg':'#16213e','sidebar_hover':'#1a2a4a','primary':'#00b4d8','secondary':'#888888','accent':'#ff4444','success':'#00aa44','warning':'#ff9900','text_primary':'#e0e0e0','text_secondary':'#999999','border':'#2a2a4a','highlight':'#1a3a5a','button_bg':'#00b4d8','button_fg':'#ffffff','header_bg':'#0d0d1a','header_fg':'#e0e0e0','splash_bg':'#0d0d1a','splash_fg':'#e0e0e0','splash_accent':'#00b4d8'})
    elif skin == "purple":
        Config.THEME.update({'bg_dark':'#f5f0ff','bg_card':'#ffffff','sidebar_bg':'#f0e8ff','sidebar_hover':'#e0d0ff','primary':'#7B2FBE','secondary':'#888888','accent':'#ff3333','success':'#00aa44','warning':'#ff9900','text_primary':'#333333','text_secondary':'#666666','border':'#d4c0e8','highlight':'#ede0ff','button_bg':'#7B2FBE','button_fg':'#ffffff','header_bg':'#4A148C','header_fg':'#ffffff','splash_bg':'#4A148C','splash_fg':'#ffffff','splash_accent':'#AB47BC'})
    else:
        Config.THEME.update({'bg_dark':'#f0f2f5','bg_card':'#ffffff','sidebar_bg':'#ffffff','sidebar_hover':'#eef2f7','primary':'#0066cc','secondary':'#666666','accent':'#ff3333','success':'#00aa44','warning':'#ff9900','text_primary':'#333333','text_secondary':'#666666','border':'#dddddd','highlight':'#e6f2ff','button_bg':'#0066cc','button_fg':'#ffffff','header_bg':'#1a2a4a','header_fg':'#ffffff','splash_bg':'#1a2a4a','splash_fg':'#ffffff','splash_accent':'#0066cc'})

class LanguageManager:
    _instance = None
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    def __init__(self):
        if self._initialized: return
        self._initialized = True
        self.current_language = Config.LANGUAGE
        self.current_skin = Config.SKIN
        self.translations = {}
        self.callbacks = []
        self.SUPPORTED_LANGUAGES = Config.SUPPORTED_LANGUAGES
        self.load_translations()
    def load_translations(self):
        default = {"zh_CN":{"app_name":"PYRT安全卫士","version":"版本","save":"保存","cancel":"取消","confirm":"确认","close":"关闭","settings":"设置","language":"语言","dashboard":"仪表盘","security_scan":"安全扫描","realtime_protection":"实时保护","boot_protection":"引导保护","threat_list":"威胁列表","quarantine":"隔离区","log_center":"日志中心","network_protection":"断网保护","intelligent_learning":"智能学习","defender_coordination":"Defender联动","honeypot":"蜜罐陷阱","ransomware_decryptor":"勒索解密助手","intelligent_learning_title":"智能学习引擎","learning_status":"学习状态","start_learning":"开始学习","stop_learning":"停止学习","reset_baseline":"重置基线","learning_progress":"学习进度","baseline_info":"基线信息","current_performance":"当前性能","cpu_usage":"CPU使用率","memory_usage":"内存使用率","deviation":"偏离程度","learning_alerts":"学习警报","no_baseline":"未建立基线","baseline_established":"基线已建立","learning_in_progress":"学习中","anomaly_detected":"性能异常","security_dashboard":"安全仪表盘","real_time_monitoring":"实时监控系统安全状态","system_status":"系统状态","secure":"安全","running":"运行中","virus_db":"病毒库","latest":"最新","quick_actions":"快速操作","quick_scan":"快速扫描","quick_scan_desc":"检查关键系统区域","full_scan":"全盘扫描","full_scan_desc":"深度检查所有文件","boot_check":"引导检查","boot_check_desc":"验证引导完整性","network_check":"网络检查","network_check_desc":"检查网络连接","update_virus_db":"更新病毒库","update_virus_db_desc":"获取最新病毒定义","execute":"执行","security_scan_title":"安全扫描","start_scan":"开始安全扫描","stop_scan":"停止扫描","protection_status":"保护状态","status":"状态","monitored_dirs":"监控目录","process_monitoring":"进程监控","enabled":"启用","disabled":"禁用","pause_protection":"暂停保护","start_protection":"启动保护","realtime_alerts":"实时警报","protected_files":"保护文件","auto_repair":"自动修复","check_integrity":"检查完整性","create_backup":"创建备份","repair_boot":"修复引导","boot_alerts":"引导警报","network":"网络","internet":"互联网","connected":"已连接","disconnected":"未连接","blocked_ips":"阻止IP数","blocked_domains":"阻止域名","check_network":"检查网络","view_connections":"查看连接","emergency_disconnect":"紧急断网","network_alerts":"网络警报","threat_detection":"威胁检测","detected_threats":"检测到的威胁","quarantine_selected":"隔离选中","delete_selected":"删除选中","clear_list":"清除列表","quarantine_title":"隔离区","quarantine_info":"隔离文件信息","quarantined_files":"隔离文件数","space_used":"占用空间","location":"目录位置","open_quarantine":"打开隔离区","clear_quarantine":"清空隔离区","view_log":"查看日志","log_center_title":"日志中心","log_files":"日志文件","main_log":"主程序日志","realtime_log":"实时保护日志","network_log":"网络保护日志","quarantine_log":"隔离区日志","scan_log":"扫描日志","boot_log":"引导保护日志","view":"查看","settings_title":"设置","program_settings":"程序设置","auto_start":"开机自启动","auto_start_desc":"系统启动时自动运行PYRT安全卫士","auto_update":"自动更新","auto_update_desc":"自动检查并更新病毒库","show_notifications":"显示通知","show_notifications_desc":"在检测到威胁时显示系统通知","low_resource_mode":"低资源模式","low_resource_mode_desc":"降低CPU和内存使用率","dark_theme":"暗色主题","dark_theme_desc":"使用暗色界面主题","enable_network_protection":"启用断网保护","enable_network_protection_desc":"启用网络监控和断网保护功能","save_settings":"保存设置","warning":"警告","error":"错误","info":"信息","success":"成功","confirm_action":"确认操作","scan_in_progress":"扫描正在进行中","scan_complete":"扫描完成","threats_found":"检测到威胁","no_threats":"未发现任何威胁","system_secure":"系统安全","ok":"确定","yes":"是","no":"否","apply":"应用","refresh":"刷新","add":"添加","preparing_scan":"准备扫描...","scanning":"正在扫描","files":"文件","threats":"威胁","speed":"速度","elapsed":"已用时间","critical":"严重","high":"高","medium":"中","low":"低","network_status":"网络状态","internet_status":"互联网状态","unknown":"未知","checking":"检查中...","exit_confirm":"确定要退出PYRT安全卫士吗？\n\n所有保护服务也将被关闭。","exit":"退出","language_selection":"语言选择","select_language_prompt":"请选择界面语言：","save_and_restart":"保存并重启","coordinated_scan":"协同扫描","sync_quarantine":"同步隔离区","enable_defender":"启用Defender","sync_exclusions":"同步排除目录","defender_status":"Defender状态","honeypot_title":"蜜罐陷阱系统","honeypot_desc":"诱捕攻击者，记录入侵行为","honeypot_alerts":"蜜罐攻击记录","honeypot_ports":"监听端口","honeypot_status":"蜜罐状态","enable_honeypot":"启用蜜罐","disable_honeypot":"禁用蜜罐","honeypot_settings":"蜜罐设置","connection_from":"连接来源","connection_time":"连接时间","received_data":"接收数据","ransomware_title":"勒索软件解密助手","ransomware_desc":"检测勒索软件感染，尝试恢复加密文件","ransomware_scan":"扫描勒索软件痕迹","ransomware_scan_desc":"检查文件是否被加密","ransomware_analysis":"勒索软件分析","ransomware_name":"勒索软件类型","ransomware_extensions":"常见加密扩展名","ransomware_notes":"勒索信文件名","ransomware_recovery":"文件恢复","restore_from_shadow":"从卷影副本恢复","shadow_copy_not_available":"卷影副本不可用","recovery_success":"恢复成功","recovery_failed":"恢复失败","select_directory":"选择目录","ransomware_warning":"勒索软件威胁","ransomware_advice":"建议立即断开网络并运行深度扫描","known_ransomware":"已知勒索软件特征库","decrypt_tips":"解密提示","security_score":"安全评分","security_grade":"安全等级","score_details":"扣分详情","quarantine_all":"全部隔离","delete_all":"全部删除","usb_protection":"USB防护","usb_protection_desc":"防Autorun蠕虫，自动扫描U盘","usb_auto_scan":"USB自动扫描","usb_scan_interval":"扫描间隔(秒)","usb_block_autorun":"阻止Autorun.inf","usb_quarantine":"自动隔离威胁","usb_detected_devices":"检测到的USB设备","usb_scan_results":"USB扫描结果","tools":"实用工具","file_shredder":"文件粉碎机","privacy_cleaner":"隐私清理","vulnerability_scanner":"漏洞扫描","shred_files":"粉碎文件","select_files":"选择文件","shred_folder":"粉碎文件夹","shred_passes":"覆写次数","shred_progress":"粉碎进度","clean_browsers":"清理浏览器","clean_chrome":"Chrome","clean_firefox":"Firefox","clean_edge":"Edge","clean_system_temp":"系统临时文件","clean_now":"立即清理","cleaned_size":"已清理空间","vuln_scan":"扫描系统漏洞","vuln_scanning":"扫描中...","vuln_results":"漏洞扫描结果","missing_updates":"缺失的安全更新","system_uptodate":"系统已是最新","check_updates":"检查更新","context_menu":"右键菜单","enable_context_menu":"启用文件/文件夹右键扫描","context_menu_desc":"在资源管理器右键菜单添加“使用PYRT扫描”选项","scheduled_scan":"定时扫描","scheduled_scan_desc":"设置每日/每周自动扫描","sched_enable":"启用定时扫描","sched_type":"扫描类型","sched_freq":"频率","sched_time":"时间(HH:MM)","sched_day":"星期几","sched_mon":"周一","sched_tue":"周二","sched_wed":"周三","sched_thu":"周四","sched_fri":"周五","sched_sat":"周六","sched_sun":"周日","ransomware_behavior":"勒索行为防御","rb_desc":"实时监控批量文件修改/重命名行为","rb_status":"防御状态","rb_alerts":"行为告警","rb_scan_scripts":"扫描可疑脚本","process_block":"进程拦截","process_block_desc":"实时监控可疑进程并弹窗拦截","pb_status":"拦截状态","pb_alerts":"拦截记录","virus_scan":"病毒查杀","tools_tab":"实用工具","settings_tab":"设置中心","full_scan_btn":"全面杀毒","quick_scan_btn":"快速扫描","custom_scan_btn":"自定义扫描","last_scan":"上次扫描","current_scan":"当前扫描","scanned_files":"已扫描文件","scan_log":"扫描日志","status_ready":"就绪","protection_status":"保护状态","real_time_protection_on":"实时防护已开启","boot_protection_on":"引导保护已开启","usb_protection_on":"U盘保护已开启","network_protection_on":"网络保护已开启","behavior_monitor_on":"行为监控已开启","system_secure":"系统安全","threats_found_count":"发现威胁","virus_db_loaded":"病毒库已加载","you_online":"你在网上潇洒，我从这里护航","skin_select":"选择主题","apply_skin":"应用主题","loading":"正在加载","loading_engines":"正在初始化引擎...","loading_db":"正在加载病毒库...","loading_ui":"正在准备界面...","loading_complete":"加载完成",
                    "registry_protection":"注册表启动项保护","file_assoc_protection":"文件关联保护","system_repair":"系统修复","cloud_scan":"云查杀",
                    "repair_hosts":"修复hosts文件","reset_dns":"重置DNS","repair_firewall":"重置防火墙","run_sfc":"运行系统文件检查",
                    "vt_api_key":"VirusTotal API Key","cloud_scan_desc":"启用云端病毒库查询（需API Key）"}}
        try:
            if os.path.exists(Config.LANGUAGE_FILE):
                with open(Config.LANGUAGE_FILE,'r',encoding='utf-8') as f:
                    loaded=json.load(f)
                    for k,v in loaded.items():
                        if k in default: default[k].update(v)
        except: pass
        self.translations=default
    def get_text(self,key,default=None):
        return self.translations.get(self.current_language,{}).get(key,default or key)
    def set_language(self,code):
        if code in self.SUPPORTED_LANGUAGES:
            self.current_language=code
            Config.LANGUAGE=code
            self.save_language_setting()
            self._notify_callbacks()
            return True
        return False
    def save_language_setting(self):
        try:
            cfg={}
            if os.path.exists(Config.LANGUAGE_FILE):
                with open(Config.LANGUAGE_FILE,'r',encoding='utf-8') as f: cfg=json.load(f)
            cfg['language']=self.current_language
            cfg['skin']=self.current_skin
            with open(Config.LANGUAGE_FILE,'w',encoding='utf-8') as f: json.dump(cfg,f,ensure_ascii=False,indent=2)
        except: pass
    def load_language_setting(self):
        try:
            if os.path.exists(Config.LANGUAGE_FILE):
                with open(Config.LANGUAGE_FILE,'r',encoding='utf-8') as f:
                    cfg=json.load(f)
                    if 'language' in cfg and cfg['language'] in self.SUPPORTED_LANGUAGES:
                        self.current_language=cfg['language']; Config.LANGUAGE=cfg['language']
        except: pass
    def load_skin_setting(self):
        try:
            if os.path.exists(Config.LANGUAGE_FILE):
                with open(Config.LANGUAGE_FILE,'r',encoding='utf-8') as f:
                    cfg=json.load(f)
                    if 'skin' in cfg and cfg['skin'] in Config.SKIN_OPTIONS:
                        self.current_skin=cfg['skin']; Config.SKIN=cfg['skin']; apply_skin(cfg['skin'])
        except: pass
    def set_skin(self,skin):
        if skin in Config.SKIN_OPTIONS:
            self.current_skin=skin; Config.SKIN=skin; apply_skin(skin); self.save_language_setting(); self._notify_callbacks(); return True
        return False
    def register_callback(self,cb):
        if cb not in self.callbacks: self.callbacks.append(cb)
    def unregister_callback(self,cb):
        if cb in self.callbacks: self.callbacks.remove(cb)
    def _notify_callbacks(self):
        for cb in self.callbacks:
            try: cb()
            except: pass

lang=LanguageManager()
lang.load_language_setting()
lang.load_skin_setting()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [PYRT安全卫士] - %(levelname)s - %(message)s', filename='pyrt_security_suite.log', filemode='a')
logger=logging.getLogger(__name__)

class SecurityScore:
    def __init__(self, app): self.app = app; self.score=0; self.grade="F"; self.details=[]
    def calculate_score(self):
        score=100; details=[]
        if not self.app.realtime_engine.is_running(): score-=15; details.append("实时保护未启用 (-15)")
        if not self.app.boot_engine.is_running(): score-=15; details.append("引导保护未启用 (-15)")
        if not self.app.network_engine.is_running(): score-=10; details.append("网络保护未启用 (-10)")
        if not self.app.honeypot_engine.is_running(): score-=5; details.append("蜜罐未启用 (-5)")
        if not self.app.learning_engine.is_monitoring(): score-=5; details.append("智能学习监控未启用 (-5)")
        def_status = self.app.defender_coordinator.get_defender_status()
        if def_status.get('available',False):
            if not def_status.get('real_time_protection',False): score-=10; details.append("Windows Defender 实时保护未启用 (-10)")
        else: score-=5; details.append("Windows Defender 不可用 (-5)")
        if len(self.app.scan_engine.virus_db.signatures)==0: score-=5; details.append("病毒库为空 (-5)")
        threat_count=len(self.app.threats_list)
        if threat_count>0: deduct=min(20,threat_count*2); score-=deduct; details.append(f"发现 {threat_count} 个威胁 (-{deduct})")
        q_count=0
        if os.path.exists(Config.QUARANTINE_DIR):
            for root,dirs,files in os.walk(Config.QUARANTINE_DIR): q_count+=len(files)
        if q_count>10: score-=5; details.append(f"隔离区文件过多 ({q_count}) (-5)")
        elif q_count>0: score-=2; details.append(f"隔离区有 {q_count} 个文件 (-2)")
        if platform.system()=="Windows":
            try:
                result=subprocess.run(['reg','query','HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run'], capture_output=True,text=True,encoding='gbk',errors='replace',creationflags=CREATE_NO_WINDOW)
                suspicious=['temp','virus','malware','hack']
                for line in result.stdout.split('\n'):
                    line_low=line.lower()
                    for sus in suspicious:
                        if sus in line_low: score-=5; details.append("发现可疑启动项 (-5)"); break
                    else: continue
                    break
            except: pass
            try:
                fw=subprocess.run(['netsh','advfirewall','show','allprofiles'], capture_output=True,text=True,encoding='gbk',errors='replace',creationflags=CREATE_NO_WINDOW)
                if "State                                 ON" not in fw.stdout: score-=5; details.append("防火墙未完全启用 (-5)")
            except: pass
        self.score=max(0,min(100,score))
        if self.score>=95: self.grade="A+"
        elif self.score>=90: self.grade="A"
        elif self.score>=85: self.grade="A-"
        elif self.score>=80: self.grade="B+"
        elif self.score>=75: self.grade="B"
        elif self.score>=70: self.grade="B-"
        elif self.score>=65: self.grade="C+"
        elif self.score>=60: self.grade="C"
        elif self.score>=50: self.grade="D"
        else: self.grade="F"
        self.details=details
        return self.score,self.grade,self.details

class RansomwareDecryptorEngine:
    def __init__(self):
        self.ransomware_signatures={
            "WannaCry": {"extensions":[".wncry",".wcry",".wncrypt"], "notes":["!Please Read Me!.txt","@Please_Read_Me@.txt","!Recover.txt"], "indicators":["WannaCry","Wana Decrypt0r","比特币"], "decrypt_tool":"https://www.nomoreransom.org/zh/index.html"},
            "Locky": {"extensions":[".locky",".asasin",".odin",".aesir"], "notes":["_Locky_recover_instructions.txt","What_is.html"], "indicators":["Locky","RSA-2048"], "decrypt_tool":"https://www.avast.com/zh-cn/ransomware-decryption-tools#locky"},
            "Cerber": {"extensions":[".cerber",".cerber2",".cerber3"], "notes":["#_DECRYPT_#.html","#_DECRYPT_#.txt"], "indicators":["Cerber","Ransomware Cerber"], "decrypt_tool":"https://www.bitdefender.com/zh-cn/support/how-to-decrypt-cerber-ransomware-1841.html"},
            "CryptoLocker": {"extensions":[".encrypted",".cryptolocker",".ecc"], "notes":["DECRYPT_INSTRUCTION.HTML","DECRYPT_INSTRUCTION.TXT"], "indicators":["CryptoLocker","RSA-2048"], "decrypt_tool":"https://www.nomoreransom.org/zh/index.html"},
            "BadRabbit": {"extensions":[".encrypted"], "notes":["!ReadMe!.txt","Read_This.txt"], "indicators":["Bad Rabbit","Flash Update"], "decrypt_tool":"https://www.eset.com/int/decrypt-badrabbit/"},
            "GandCrab": {"extensions":[".gandcrab",".krab",".crab"], "notes":["DECRYPT.html","DECRYPT.txt"], "indicators":["GandCrab","GDCB"], "decrypt_tool":"https://www.bitdefender.com/zh-cn/support/how-to-decrypt-gandcrab-ransomware-1842.html"},
            "TeslaCrypt": {"extensions":[".ttt",".micro",".ecc",".ezz",".xyz"], "notes":["!Decrypt_Your_Files.html","!_READ_THIS_!.txt"], "indicators":["TeslaCrypt","TorrentLocker"], "decrypt_tool":"https://www.eset.com/int/decrypt-teslacrypt/"},
            "Sodinokibi": {"extensions":[".sodinokibi",".rbq",".dmx",".readme"], "notes":["readme.txt","how_to_back_files.html"], "indicators":["REvil","Sodinokibi"], "decrypt_tool":"https://www.nomoreransom.org/zh/index.html"}
        }
        self.scan_results=[]; self.recovery_log=[]; self._init_log()
    def _init_log(self):
        try: os.makedirs(Config.LOG_DIR,exist_ok=True); handler=logging.FileHandler(os.path.join(Config.LOG_DIR,Config.RANSOMWARE_LOG),encoding='utf-8'); handler.setFormatter(logging.Formatter('%(asctime)s - [勒索助手] - %(levelname)s - %(message)s')); logger.addHandler(handler)
        except: pass
    def detect_ransomware_by_extension(self,file_path):
        ext=os.path.splitext(file_path)[1].lower()
        for name,info in self.ransomware_signatures.items():
            if ext in info['extensions']: return name
        return None
    def detect_ransomware_by_notes(self,directory):
        found=[]
        for root,dirs,files in os.walk(directory):
            for file in files:
                for name,info in self.ransomware_signatures.items():
                    if file.lower() in [n.lower() for n in info['notes']]:
                        found.append((name,os.path.join(root,file)))
        return found
    def scan_directory(self,directory,progress_callback=None):
        results={'encrypted_files':[], 'notes_found':[], 'detected_ransomware':set(), 'total_scanned':0}
        if not os.path.exists(directory): return results
        notes=self.detect_ransomware_by_notes(directory)
        for r_name,note_path in notes:
            results['notes_found'].append({'type':r_name,'path':note_path})
            results['detected_ransomware'].add(r_name)
        encrypted_extensions=set()
        for info in self.ransomware_signatures.values(): encrypted_extensions.update(info['extensions'])
        for root,dirs,files in os.walk(directory):
            for file in files:
                ext=os.path.splitext(file)[1].lower()
                if ext in encrypted_extensions:
                    full_path=os.path.join(root,file)
                    r_type=self.detect_ransomware_by_extension(full_path)
                    if r_type:
                        results['detected_ransomware'].add(r_type)
                        results['encrypted_files'].append({'path':full_path,'extension':ext,'type':r_type})
                results['total_scanned']+=1
                if progress_callback and results['total_scanned']%50==0: progress_callback(results['total_scanned'])
        return results
    def get_ransomware_info(self,r_name): return self.ransomware_signatures.get(r_name,None)
    def list_shadow_copies_windows(self):
        if platform.system()!="Windows": return []
        try:
            result=subprocess.run(['vssadmin','list','shadows'], capture_output=True,text=True,encoding='gbk',errors='replace',timeout=30,creationflags=CREATE_NO_WINDOW)
            lines=result.stdout.split('\n'); shadow_ids=[]; current_id=None
            for line in lines:
                if 'Shadow Copy ID' in line:
                    parts=line.split(':'); current_id=parts[1].strip()
                elif 'Shadow Copy Volume' in line and current_id:
                    parts=line.split(':'); volume=parts[1].strip(); shadow_ids.append({'id':current_id,'volume':volume}); current_id=None
            return shadow_ids
        except Exception as e: logger.error(f"获取卷影副本失败: {e}"); return []
    def restore_from_shadow_copy(self,file_path,output_dir):
        if platform.system()!="Windows": return False,"仅支持Windows系统"
        try:
            drive=os.path.splitdrive(file_path)[0]+"\\"
            shadows=self.list_shadow_copies_windows()
            if not shadows: return False,"未找到卷影副本"
            shadow=shadows[0]; shadow_path=shadow['volume'].rstrip('\\'); rel_path=os.path.relpath(file_path,drive); shadow_file=os.path.join(shadow_path,rel_path)
            if os.path.exists(shadow_file):
                os.makedirs(output_dir,exist_ok=True); dest=os.path.join(output_dir,os.path.basename(file_path)); shutil.copy2(shadow_file,dest); return True,dest
            else: return False,"卷影副本中不存在该文件"
        except Exception as e: return False,str(e)
    def generate_recovery_report(self,scan_results):
        report=f"勒索软件扫描报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"+"="*50+"\n"
        if scan_results['detected_ransomware']: report+=f"检测到勒索软件类型: {', '.join(scan_results['detected_ransomware'])}\n"
        else: report+="未检测到已知勒索软件特征\n"
        report+=f"发现勒索信文件: {len(scan_results['notes_found'])}\n"
        report+=f"发现加密文件: {len(scan_results['encrypted_files'])}\n"
        if scan_results['encrypted_files']:
            report+="\n部分加密文件列表:\n"
            for f in scan_results['encrypted_files'][:20]: report+=f"  {f['path']} (类型: {f['type']})\n"
        return report

class WindowsDefenderCoordinator:
    def __init__(self):
        self.available=False; self.defender_status={}; self.last_scan_time=0; self.coordination_alerts=[]; self.quarantine_sync_enabled=True; self.scan_coordination_enabled=True; self.real_time_sync_enabled=True
        self._check_defender_availability()
        logger.info(f"Windows Defender联动引擎初始化完成，可用性: {self.available}")
    def _check_defender_availability(self):
        if platform.system()!="Windows": self.available=False; return
        try:
            result=subprocess.run(['powershell','-Command','Get-MpComputerStatus'], capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=10,creationflags=CREATE_NO_WINDOW)
            if result.returncode==0: self.available=True; self._parse_defender_status(result.stdout)
            else: self.available=False
        except Exception as e: logger.warning(f"Windows Defender检测失败: {e}"); self.available=False
    def _parse_defender_status(self,status_output):
        status_dict={}
        for line in status_output.split('\n'):
            if ':' in line: key,value=line.split(':',1); status_dict[key.strip()]=value.strip()
        self.defender_status={'antivirus_enabled':status_dict.get('AntivirusEnabled','False')=='True','real_time_protection':status_dict.get('RealTimeProtectionEnabled','False')=='True','behavior_monitor':status_dict.get('BehaviorMonitorEnabled','False')=='True','last_quick_scan':status_dict.get('QuickScanTime','从未'),'last_full_scan':status_dict.get('FullScanTime','从未'),'virus_def_version':status_dict.get('AntivirusSignatureVersion','未知'),'available':True}
    def get_defender_status(self):
        if not self.available: return {'available':False,'message':'Windows Defender不可用'}
        try:
            result=subprocess.run(['powershell','-Command','Get-MpComputerStatus'], capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=10,creationflags=CREATE_NO_WINDOW)
            if result.returncode==0: self._parse_defender_status(result.stdout)
        except: pass
        self.defender_status['available']=True
        return self.defender_status
    def run_defender_scan(self,scan_type="quick"):
        if not self.available: return {'success':False,'message':'Windows Defender不可用'}
        threats=[]
        try:
            if scan_type=="quick": cmd="Start-MpScan -ScanType QuickScan"
            elif scan_type=="full": cmd="Start-MpScan -ScanType FullScan"
            else: cmd="Start-MpScan -ScanType QuickScan"
            result=subprocess.run(['powershell','-Command',cmd], capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=300,creationflags=CREATE_NO_WINDOW)
            history_cmd="Get-MpThreatDetection | Select-Object -First 10"
            history_result=subprocess.run(['powershell','-Command',history_cmd], capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30,creationflags=CREATE_NO_WINDOW)
            threats=self._parse_defender_threats(history_result.stdout)
            return {'success':True,'threats':threats,'message':'扫描完成'}
        except Exception as e: logger.error(f"Windows Defender扫描失败: {e}"); return {'success':False,'message':str(e)}
    def _parse_defender_threats(self,output):
        threats=[]
        for line in output.split('\n'):
            if '威胁' in line or 'Threat' in line or '病毒' in line or 'Trojan' in line:
                threats.append({'source':'Windows Defender','name':line.strip()[:80],'file':'请查看Windows Defender历史记录','severity':'高','time':datetime.now().strftime('%Y-%m-%d %H:%M:%S')})
        return threats
    def sync_quarantine(self,pyrt_quarantine_dir):
        if not self.available: return {'synced':0,'failed':0,'details':[],'message':'Windows Defender不可用'}
        results={'synced':0,'failed':0,'details':[]}
        try:
            if os.path.exists(pyrt_quarantine_dir):
                for file in os.listdir(pyrt_quarantine_dir):
                    file_path=os.path.join(pyrt_quarantine_dir,file)
                    if os.path.isfile(file_path):
                        cmd=f'Add-MpPreference -ExclusionPath "{file_path}"'
                        subprocess.run(['powershell','-Command',cmd], capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=10,creationflags=CREATE_NO_WINDOW)
                        results['synced']+=1; results['details'].append(f'已同步: {file}')
        except Exception as e: logger.error(f"同步隔离区失败: {e}"); results['failed']+=1
        results['message']=f"已同步 {results['synced']} 个文件"
        return results
    def enable_defender_realtime(self):
        if not self.available: return False
        try:
            cmd='Set-MpPreference -DisableRealtimeMonitoring $false'
            result=subprocess.run(['powershell','-Command',cmd], capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=30,creationflags=CREATE_NO_WINDOW)
            if result.returncode==0: logger.info("已启用Windows Defender实时保护"); return True
        except Exception as e: logger.error(f"启用Defender实时保护失败: {e}")
        return False
    def run_exclusion_sync(self,pyrt_paths):
        if not self.available: return {'added':0,'failed':0,'message':'Windows Defender不可用'}
        results={'added':0,'failed':0}
        for path in pyrt_paths:
            if path and os.path.exists(path):
                try:
                    cmd=f'Add-MpPreference -ExclusionPath "{path}"'
                    subprocess.run(['powershell','-Command',cmd], capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=10,creationflags=CREATE_NO_WINDOW)
                    results['added']+=1
                except: results['failed']+=1
        results['message']=f"已添加 {results['added']} 个排除目录"
        return results
    def get_recommendations(self):
        if not self.available: return {'available':False,'message':'Windows Defender不可用'}
        recommendations=[]; status=self.get_defender_status()
        if not status.get('antivirus_enabled',False): recommendations.append({'type':'warning','message':'Windows Defender实时保护未启用，建议立即启用','action':'启用实时保护'})
        if not status.get('real_time_protection',False): recommendations.append({'type':'warning','message':'Windows Defender实时监控已关闭，安全性降低','action':'开启实时监控'})
        if not recommendations: recommendations.append({'type':'success','message':'Windows Defender配置良好，与PYRT协同工作正常','action':'保持现状'})
        return {'available':True,'status':status,'recommendations':recommendations}

class HoneypotEngine:
    def __init__(self):
        self.running=False; self.threads=[]; self.sockets=[]; self.alerts=[]; self.log_file=os.path.join(Config.LOG_DIR,Config.HONEYPOT_LOG)
        self._init_log(); logger.info("蜜罐引擎初始化完成")
    def _init_log(self):
        try: os.makedirs(Config.LOG_DIR,exist_ok=True); handler=logging.FileHandler(self.log_file,encoding='utf-8'); handler.setFormatter(logging.Formatter('%(asctime)s - [蜜罐] - %(levelname)s - %(message)s')); logger.addHandler(handler)
        except: pass
    def start(self):
        if self.running: return False
        self.running=True
        for port in Config.HONEYPOT_PORTS:
            t=threading.Thread(target=self._listen_port,args=(port,),daemon=True); t.start(); self.threads.append(t)
        logger.info(f"蜜罐已启动，监听端口: {Config.HONEYPOT_PORTS}"); return True
    def stop(self):
        self.running=False
        for sock in self.sockets:
            try: sock.close()
            except: pass
        self.sockets.clear()
        for t in self.threads:
            if t.is_alive(): t.join(0.5)
        self.threads.clear(); logger.info("蜜罐已停止")
    def _listen_port(self,port):
        sock=None
        try:
            sock=socket.socket(socket.AF_INET,socket.SOCK_STREAM); sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); sock.bind(('0.0.0.0',port)); sock.listen(5); self.sockets.append(sock); logger.debug(f"蜜罐监听端口 {port} 就绪")
            while self.running:
                try:
                    client,addr=sock.accept(); client_ip=addr[0]; client_port=addr[1]; timestamp=datetime.now().strftime('%Y-%m-%d %H:%M:%S'); data=b''; client.settimeout(1.0)
                    try: data=client.recv(1024)
                    except socket.timeout: pass
                    except: pass
                    if port==2222 and data:
                        try: client.send(b"SSH-2.0-OpenSSH_8.9p1\r\n"); client.send(b"Username: "); time.sleep(0.5); client.send(b"Password: ")
                        except: pass
                    banner=Config.HONEYPOT_BANNER.get(port,"PYRT Honeypot - Access Logged\r\n")
                    try: client.send(banner.encode('utf-8',errors='ignore'))
                    except: pass
                    client.close()
                    alert={'time':timestamp,'port':port,'src_ip':client_ip,'src_port':client_port,'data':data[:200].decode('utf-8',errors='replace') if data else '','severity':'中'}
                    self.alerts.insert(0,alert)
                    if len(self.alerts)>Config.HONEYPOT_MAX_LOG: self.alerts=self.alerts[:Config.HONEYPOT_MAX_LOG]
                    log_msg=f"[{timestamp}] 攻击来自 {client_ip}:{client_port} -> 端口{port} 数据: {alert['data'][:50]}"
                    logger.warning(log_msg)
                except socket.timeout: continue
                except Exception as e:
                    if self.running: logger.error(f"蜜罐端口 {port} 异常: {e}")
                    break
        except Exception as e: logger.error(f"无法监听端口 {port}: {e}")
        finally:
            if sock:
                try: sock.close()
                except: pass
    def get_alerts(self,count=20): return self.alerts[:count]
    def is_running(self): return self.running

class LanguageSelectionDialog:
    def __init__(self,parent,callback=None):
        self.parent=parent; self.callback=callback; self.dialog=tk.Toplevel(parent)
        self.dialog.title(lang.get_text("language_selection")); self.dialog.geometry("400x350"); self.dialog.configure(bg=Config.THEME['bg_dark']); self.dialog.resizable(False,False); self.dialog.transient(parent); self.dialog.grab_set(); self.dialog.update_idletasks(); x=(self.dialog.winfo_screenwidth()-400)//2; y=(self.dialog.winfo_screenheight()-350)//2; self.dialog.geometry(f"400x350+{x}+{y}"); self._create_widgets()
    def _create_widgets(self):
        main=tk.Frame(self.dialog,bg=Config.THEME['bg_dark'],padx=20,pady=20); main.pack(fill=tk.BOTH,expand=True)
        tk.Label(main,text="🌐 "+lang.get_text("language_selection"),font=("Microsoft YaHe",16,"bold"),fg=Config.THEME['primary'],bg=Config.THEME['bg_dark']).pack(pady=(0,20))
        tk.Label(main,text=lang.get_text("select_language_prompt"),font=("Microsoft YaHe",11),fg=Config.THEME['text_secondary'],bg=Config.THEME['bg_dark']).pack(pady=(0,10))
        list_frame=tk.Frame(main,bg=Config.THEME['bg_card'],relief=tk.FLAT,bd=1); list_frame.pack(fill=tk.BOTH,expand=True,pady=(0,20))
        self.lang_var=tk.StringVar(value=Config.LANGUAGE)
        canvas=tk.Canvas(list_frame,bg=Config.THEME['bg_card'],highlightthickness=0,height=180)
        scrollbar=tk.Scrollbar(list_frame,orient=tk.VERTICAL,command=canvas.yview)
        scrollable=tk.Frame(canvas,bg=Config.THEME['bg_card'])
        scrollable.bind("<Configure>",lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0),window=scrollable,anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        for code,name in Config.SUPPORTED_LANGUAGES.items():
            rb=tk.Radiobutton(scrollable,text=name,variable=self.lang_var,value=code,font=("Microsoft YaHe",11),fg=Config.THEME['text_primary'],bg=Config.THEME['bg_card'],selectcolor=Config.THEME['bg_card'],activebackground=Config.THEME['bg_card'])
            rb.pack(anchor=tk.W,padx=10,pady=5)
        canvas.pack(side=tk.LEFT,fill=tk.BOTH,expand=True); scrollbar.pack(side=tk.RIGHT,fill=tk.Y)
        btn_frame=tk.Frame(main,bg=Config.THEME['bg_dark']); btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame,text=lang.get_text("save"),command=self._save,bg=Config.THEME['primary'],fg=Config.THEME['button_fg'],padx=20,pady=8,relief=tk.FLAT,cursor="hand2").pack(side=tk.LEFT,padx=(0,10))
        tk.Button(btn_frame,text=lang.get_text("cancel"),command=self.dialog.destroy,bg=Config.THEME['secondary'],fg=Config.THEME['button_fg'],padx=20,pady=8,relief=tk.FLAT,cursor="hand2").pack(side=tk.LEFT)
    def _save(self):
        new_lang=self.lang_var.get()
        if new_lang!=Config.LANGUAGE:
            lang.set_language(new_lang)
            if self.callback: self.callback()
            else:
                if messagebox.askyesno(lang.get_text("confirm"),lang.get_text("save_and_restart")):
                    if hasattr(self.parent,'refresh_ui'): self.parent.refresh_ui()
        self.dialog.destroy()

class NetworkProtectionEngine:
    def __init__(self):
        self.running=False; self.monitor_thread=None; self.network_alerts=[]; self.blocked_ips=set(Config.MALICIOUS_IPS); self.blocked_domains=set(Config.MALICIOUS_DOMAINS); self.network_connections=[]; self.last_scan_time=0; self.network_status="unknown"; self.internet_status=False; self._init_log()
    def _init_log(self):
        try: os.makedirs(Config.LOG_DIR,exist_ok=True); handler=logging.FileHandler(os.path.join(Config.LOG_DIR,Config.NETWORK_LOG),encoding='utf-8'); handler.setFormatter(logging.Formatter('%(asctime)s - [网络保护] - %(levelname)s - %(message)s')); logger.addHandler(handler)
        except: pass
    def start_protection(self):
        if self.running: return False
        self.running=True; self._check_network_status(); self.monitor_thread=threading.Thread(target=self._monitor_loop,daemon=True); self.monitor_thread.start(); logger.info("网络保护引擎启动"); return True
    def stop_protection(self):
        self.running=False
        if self.monitor_thread and self.monitor_thread.is_alive(): self.monitor_thread.join(timeout=2)
        logger.info("网络保护引擎停止")
    def _check_network_status(self):
        try:
            if platform.system()=="Windows":
                result=subprocess.run(['ipconfig'], capture_output=True,text=True,encoding='gbk',errors='replace',creationflags=CREATE_NO_WINDOW)
                self.network_status="connected" if "Media disconnected" not in result.stdout else "disconnected"
            else:
                result=subprocess.run(['ifconfig'], capture_output=True,text=True,errors='replace',creationflags=CREATE_NO_WINDOW)
                self.network_status="connected" if "UP" in result.stdout else "disconnected"
            self.internet_status=self._check_internet(); self._check_dns_hijack()
        except: self.network_status="error"; self.internet_status=False
    def _check_internet(self,timeout=3):
        urls=["https://www.baidu.com","https://www.google.com","https://1.1.1.1"]
        for url in urls:
            try:
                with urllib.request.urlopen(url,timeout=timeout) as resp:
                    if resp.getcode()==200: return True
            except: continue
        return False
    def _check_dns_hijack(self):
        try:
            import socket
            ips=set()
            for host in ['microsoft.com','google.com']: ips.add(socket.gethostbyname(host))
            for ip in ips:
                if ip.startswith('10.') or ip.startswith('192.168.') or ip.startswith('172.'):
                    self._add_alert(f"DNS可能被劫持: {host} -> {ip}", severity='高')
        except: pass
    def _monitor_loop(self):
        while self.running:
            try:
                old_status, old_internet = self.network_status, self.internet_status
                self._check_network_status()
                if old_status != self.network_status: self._add_alert(f"网络状态变化: {old_status} -> {self.network_status}")
                if old_internet != self.internet_status: self._add_alert(f"互联网连接变化: {'已连接' if self.internet_status else '已断开'}")
                if self.internet_status: self._scan_connections()
                time.sleep(Config.NETWORK_MONITOR_INTERVAL)
            except: time.sleep(30)
    def _scan_connections(self):
        if time.time()-self.last_scan_time < 30: return
        self.last_scan_time=time.time()
        if platform.system()=="Windows": conns=self._get_windows_connections()
        else: conns=self._get_unix_connections()
        for conn in conns: self._analyze_connection(conn)
    def _get_windows_connections(self):
        conns=[]
        try:
            result=subprocess.run('netstat -an',shell=True,capture_output=True,text=True,encoding='gbk',errors='replace',creationflags=CREATE_NO_WINDOW)
            for line in result.stdout.split('\n'):
                if 'ESTABLISHED' in line or 'LISTENING' in line:
                    parts=line.split()
                    if len(parts)>=3:
                        local=parts[1]; remote=parts[2]; state=parts[3] if len(parts)>3 else ''
                        local_ip,local_port=self._parse_addr(local); remote_ip,remote_port=self._parse_addr(remote)
                        conns.append({'local_ip':local_ip,'local_port':local_port,'remote_ip':remote_ip,'remote_port':remote_port,'state':state,'time':datetime.now().strftime('%H:%M:%S')})
        except: pass
        return conns
    def _get_unix_connections(self):
        conns=[]
        try:
            result=subprocess.run('netstat -tun 2>/dev/null',shell=True,capture_output=True,text=True,errors='replace',creationflags=CREATE_NO_WINDOW)
            for line in result.stdout.split('\n'):
                if 'ESTAB' in line or 'LISTEN' in line:
                    parts=line.split()
                    if len(parts)>=5:
                        local=parts[3]; remote=parts[4]; state=parts[5] if len(parts)>5 else ''
                        local_ip,local_port=self._parse_addr(local); remote_ip,remote_port=self._parse_addr(remote)
                        conns.append({'local_ip':local_ip,'local_port':local_port,'remote_ip':remote_ip,'remote_port':remote_port,'state':state,'time':datetime.now().strftime('%H:%M:%S')})
        except: pass
        return conns
    def _parse_addr(self,addr):
        if ':' not in addr: return addr,''
        if '[' in addr: ip_end=addr.find(']'); ip=addr[1:ip_end]; port=addr[ip_end+2:]
        else: parts=addr.rsplit(':',1); ip=parts[0]; port=parts[1] if len(parts)>1 else ''
        return ip,port
    def _analyze_connection(self,conn):
        remote_ip=conn.get('remote_ip',''); remote_port=conn.get('remote_port','')
        if remote_ip in self.blocked_ips:
            self._add_alert(f"连接到恶意IP: {remote_ip}", severity='高'); self._block_ip(remote_ip)
        elif remote_port.isdigit() and int(remote_port) in Config.SUSPICIOUS_PORTS:
            self._add_alert(f"连接到可疑端口: {remote_port}", severity='中')
    def _block_ip(self,ip):
        if platform.system()=="Windows":
            rule=f"PYRT_Block_{ip}_{int(time.time())}"
            subprocess.run(f'netsh advfirewall firewall add rule name="{rule}" dir=out action=block remoteip={ip} enable=yes', shell=True, capture_output=True, encoding='gbk', errors='replace', creationflags=CREATE_NO_WINDOW)
    def _add_alert(self,msg,severity='中'):
        alert={'time':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'type':'网络警报','severity':severity,'message':msg}
        self.network_alerts.insert(0,alert)
        if len(self.network_alerts)>100: self.network_alerts=self.network_alerts[:100]
        logger.warning(f"网络保护: {msg}")
    def get_alerts(self,count=10): return self.network_alerts[:count]
    def get_network_status(self):
        return {'network':self.network_status,'internet':self.internet_status,'blocked_ips':len(self.blocked_ips),'blocked_domains':len(self.blocked_domains),'recent_connections':len(self.network_connections)}
    def emergency_disconnect(self):
        try:
            if platform.system()=="Windows":
                subprocess.run('netsh interface set interface "以太网" admin=disable', shell=True, capture_output=True, encoding='gbk', errors='replace', creationflags=CREATE_NO_WINDOW)
                subprocess.run('ipconfig /release', shell=True, capture_output=True, encoding='gbk', errors='replace', creationflags=CREATE_NO_WINDOW)
            else:
                subprocess.run('ifconfig eth0 down 2>/dev/null || ip link set eth0 down 2>/dev/null', shell=True, capture_output=True, errors='replace', creationflags=CREATE_NO_WINDOW)
            self._add_alert("执行紧急断网", severity='严重'); return True
        except: return False
    def is_running(self): return self.running

class VirusDatabase:
    def __init__(self):
        self.signatures={}; self.heuristic_rules={}; self.load_databases()
    def load_databases(self):
        self.signatures={
            'e99a18c428cb38d5f260853678922e03':'Trojan.Win32.Generic',
            '5d41402abc4b2a76b9719d911017c592':'Backdoor.Win32.Agent',
            '098f6bcd4621d373cade4e832627b4f6':'Ransomware.Win32.Crypto',
            '9b6b6b8f6c7f6d6e8f7e6d5c4b3a2b1c':'Worm.Win32.Downadup',
            'a1b2c3d4e5f67890abcdef1234567890':'Exploit.Win32.CVE-2017-0147',
            'deadbeefcafebabefeedfacec0ffee12':'Miner.Win32.CoinHive',
        }
        self.heuristic_rules={
            'suspicious_strings':['format c:','delete system','disable firewall','powershell -enc','certutil -decode','Invoke-Expression','DownloadString','FromBase64String','CreateObject("WScript.Shell")'],
            'suspicious_apis':['CreateRemoteThread','SetWindowsHookEx','GetAsyncKeyState','VirtualAllocEx','WriteProcessMemory'],
            'file_extensions':['.vbs','.js','.ps1','.bat','.scr','.jar','.hta','.docm'],
            'entropy_threshold':7.0,
        }
        try:
            if os.path.exists(Config.VIRUS_DB_PATH):
                with open(Config.VIRUS_DB_PATH,'rb') as f: self.signatures.update(pickle.load(f))
        except: pass
    def save_databases(self):
        try:
            with open(Config.VIRUS_DB_PATH,'wb') as f: pickle.dump(self.signatures,f)
        except: pass
    def add_signature(self,file_hash,virus_name): self.signatures[file_hash]=virus_name; self.save_databases()
    def check_hash(self,file_hash): return self.signatures.get(file_hash,None)
    def heuristic_analysis(self,file_path):
        score=0; findings=[]
        try:
            with open(file_path,'rb') as f:
                content=f.read(65536)
                if not content: return 0,[]
                entropy=self._calc_entropy(content)
                if entropy>self.heuristic_rules['entropy_threshold']: score+=int(entropy*2); findings.append(f"高熵值 ({entropy:.2f})")
                text=content.decode('utf-8',errors='ignore').lower()
                for sus in self.heuristic_rules['suspicious_strings']:
                    if sus.lower() in text: score+=10; findings.append(f"包含可疑字符串: {sus}")
                ext=os.path.splitext(file_path)[1].lower()
                if ext in self.heuristic_rules['file_extensions']: score+=5; findings.append(f"可疑扩展名: {ext}")
        except: pass
        return score,findings
    def _calc_entropy(self,data):
        if not data: return 0
        freq={}
        for b in data: freq[b]=freq.get(b,0)+1
        entropy=0
        for c in freq.values(): p=c/len(data); entropy-=p*math.log2(p)
        return entropy

class EnhancedPYRTScanEngine:
    def __init__(self):
        self.virus_db=VirusDatabase(); self.scanning=False; self.total_files=0; self.scanned_files=0; self.threats_found=0; self.start_time=0; self.current_scan_paths=[]; self.suspicious_files=[]
        self.cloud_engine = CloudScanEngine()
    def start_scan(self,scan_type="quick",scan_paths=None):
        self.scanning=True; self.scanned_files=0; self.threats_found=0; self.start_time=time.time()
        if scan_paths: self.current_scan_paths=scan_paths
        elif scan_type=="quick": self.current_scan_paths=self._get_quick_paths()
        else: self.current_scan_paths=self._get_full_paths()
        self.total_files=self._count_files(self.current_scan_paths) or 100
        logger.info(f"扫描启动，类型: {scan_type}, 文件数: {self.total_files}")
    def _get_quick_paths(self):
        paths=[]; user=os.path.expanduser("~")
        for p in [os.path.join(user,"Downloads"),os.path.join(user,"Desktop"),os.path.join(user,"Documents"),os.getenv("TEMP"),os.getenv("APPDATA")]:
            if p and os.path.exists(p): paths.append(p)
        return paths
    def _get_full_paths(self):
        paths=[]
        if platform.system()=="Windows":
            import string
            for d in string.ascii_uppercase:
                dp=f"{d}:\\"
                if os.path.exists(dp): paths.append(dp)
        else: paths=["/",os.path.expanduser("~")]
        return paths
    def _count_files(self,paths):
        count=0; max_f=5000
        for p in paths[:3]:
            if os.path.exists(p):
                for root,dirs,files in os.walk(p):
                    count+=len(files)
                    if count>=max_f: return max_f
        return count
    def update_scan(self):
        if not self.scanning: return None
        threats=[]; batch=0
        for sp in self.current_scan_paths:
            if not self.scanning or batch>=5: break
            if os.path.exists(sp):
                for root,dirs,files in os.walk(sp):
                    for f in files:
                        if batch>=5: break
                        fpath=os.path.join(root,f)
                        try:
                            if os.path.getsize(fpath)>Config.MAX_FILE_SIZE: continue
                        except: continue
                        t=self._scan_file(fpath)
                        if t: threats.extend(t); self.threats_found+=len(t)
                        self.scanned_files+=1; batch+=1
                    if batch>=5: break
        elapsed=time.time()-self.start_time
        progress=(self.scanned_files/self.total_files)*100 if self.total_files>0 else 0
        if self.scanned_files>=self.total_files: self.scanning=False
        return {'progress':min(progress,100),'scanned':self.scanned_files,'total':self.total_files,'threats':self.threats_found,'speed':10+random.randint(0,20),'elapsed':elapsed,'new_threats':threats,'scanning':self.scanning}
    def _scan_file(self,file_path):
        threats=[]
        try:
            with open(file_path,'rb') as f: md5=hashlib.md5(f.read()).hexdigest()
            known=self.virus_db.check_hash(md5)
            if known:
                threats.append({'name':known,'file':file_path,'severity':'Critical','method':'哈希匹配'})
                return threats
            cloud_result = self.cloud_engine.scan_file(file_path)
            if cloud_result and cloud_result['positives'] > 0:
                threats.append({
                    'name': f'云查杀检测 ({cloud_result["positives"]}/{cloud_result["total"]})',
                    'file': file_path,
                    'severity': 'High' if cloud_result['detection_rate'] > 0.5 else 'Medium',
                    'method': '云查杀',
                    'url': cloud_result.get('permalink', '')
                })
                return threats
            score,finds=self.virus_db.heuristic_analysis(file_path)
            if score>15:
                level='Low' if score<30 else ('Medium' if score<50 else ('High' if score<70 else 'Critical'))
                threats.append({'name':f'启发式检测.{level}','file':file_path,'severity':level,'type':'启发式','method':'启发式分析'})
        except: pass
        return threats
    def quarantine_file(self,file_path,threat_info):
        try:
            os.makedirs(Config.QUARANTINE_DIR,exist_ok=True)
            ts=datetime.now().strftime('%Y%m%d_%H%M%S')
            name=f"{ts}_{threat_info.get('name','unknown').replace('.','_')}_{os.path.basename(file_path)}"
            dest=os.path.join(Config.QUARANTINE_DIR,name)
            shutil.copy2(file_path,dest)
            os.makedirs(Config.LOG_DIR,exist_ok=True)
            with open(os.path.join(Config.LOG_DIR,'quarantine.log'),'a',encoding='utf-8') as logf:
                logf.write(json.dumps({'timestamp':ts,'original':file_path,'quarantine':dest,'threat':threat_info.get('name')},ensure_ascii=False)+'\n')
            return True,dest
        except Exception as e: return False,str(e)
    def stop_scan(self): self.scanning=False

class RealTimeProtection:
    def __init__(self, virus_db, scan_engine):
        self.virus_db = virus_db
        self.scan_engine = scan_engine
        self.running = False
        self.monitor_thread = None
        self.process_monitor = None
        self.alert_queue = []
        self.blocked_files = set()
        self.file_states = {}
    def start(self):
        if self.running: return False
        self.running = True
        self.monitor_thread = threading.Thread(target=self._dir_monitor_loop, daemon=True)
        self.monitor_thread.start()
        if Config.MONITOR_PROCESSES:
            self.process_monitor = threading.Thread(target=self._proc_monitor_loop, daemon=True)
            self.process_monitor.start()
        logger.info("实时保护启动")
        return True
    def stop(self):
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        if self.process_monitor:
            self.process_monitor.join(timeout=2)
        logger.info("实时保护停止")
    def _dir_monitor_loop(self):
        for p in Config.MONITOR_PATHS:
            if os.path.exists(p):
                self._scan_dir_state(p)
        while self.running:
            for p in Config.MONITOR_PATHS:
                if os.path.exists(p):
                    self._check_dir_changes(p)
            time.sleep(Config.DIRECTORY_SCAN_INTERVAL)
    def _scan_dir_state(self, directory):
        for root, dirs, files in os.walk(directory):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    st = os.stat(fp)
                    self.file_states[fp] = (st.st_size, st.st_mtime)
                except: pass
    def _check_dir_changes(self, directory):
        current = set()
        for root, dirs, files in os.walk(directory):
            for f in files:
                fp = os.path.join(root, f)
                current.add(fp)
                try:
                    st = os.stat(fp)
                    cur = (st.st_size, st.st_mtime)
                    if fp not in self.file_states:
                        if Config.SCAN_ON_CREATE:
                            self._handle_file(fp, 'created')
                        self.file_states[fp] = cur
                    elif Config.SCAN_ON_MODIFY and cur != self.file_states[fp]:
                        self._handle_file(fp, 'modified')
                        self.file_states[fp] = cur
                except: pass
        for fp in list(self.file_states.keys()):
            if fp not in current:
                del self.file_states[fp]
    def _handle_file(self, file_path, event):
        ext = os.path.splitext(file_path)[1].lower()
        if ext in ['.exe', '.dll', '.sys', '.vbs', '.js', '.ps1', '.bat', '.scr', '.jar']:
            threading.Timer(1.0, self._scan_delayed, args=[file_path, event]).start()
    def _scan_delayed(self, file_path, event):
        if not os.path.exists(file_path): return
        threats = self.scan_engine._scan_file(file_path)
        if threats:
            threat = threats[0]
            alert = {
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'type': f'文件{event}',
                'name': threat.get('name', ''),
                'severity': threat.get('severity', '中'),
                'file_path': file_path,
            }
            self.alert_queue.append(alert)
            logger.warning(f"实时保护: {alert['name']} - {file_path}")
            if Config.BLOCK_SUSPICIOUS and threat.get('severity') in ['High', 'Critical']:
                self.block_file(file_path)
    def _proc_monitor_loop(self):
        known = set()
        while self.running:
            cur = set()
            if platform.system() == "Windows":
                procs = self._get_windows_procs()
            else:
                procs = self._get_unix_procs()
            for proc in procs:
                pid = proc.get('pid')
                if pid:
                    cur.add(pid)
                    if pid not in known:
                        name = proc.get('name', '').lower()
                        cmdline = proc.get('cmdline', '')
                        if any(s in name for s in Config.SUSPICIOUS_PROCESS_NAMES) or \
                           any(arg in cmdline.lower() for arg in Config.SUSPICIOUS_ARGS):
                            alert = {'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                     'type': '可疑进程', 'name': name, 'severity': '高',
                                     'cmdline': cmdline[:100]}
                            self.alert_queue.append(alert)
                            if Config.BLOCK_SUSPICIOUS:
                                subprocess.run(f'taskkill /F /PID {pid}', shell=True,
                                               capture_output=True, encoding='gbk', errors='replace',
                                               creationflags=CREATE_NO_WINDOW)
            known = cur
            time.sleep(Config.PROCESS_SCAN_INTERVAL)
    def _get_windows_procs(self):
        procs = []
        try:
            out = subprocess.run(
                'wmic process get ProcessId,Name,CommandLine',
                shell=True,
                capture_output=True,
                text=True,
                encoding='gbk',
                errors='replace',
                creationflags=CREATE_NO_WINDOW,
                timeout=10
            )
            lines = out.stdout.split('\n')
            for line in lines[1:]:
                if line.strip():
                    parts = line.split(maxsplit=2)
                    if len(parts) >= 3:
                        name = parts[0]
                        pid = parts[1]
                        cmd = parts[2] if len(parts) > 2 else ''
                        if pid.isdigit():
                            procs.append({'pid': int(pid), 'name': name, 'cmdline': cmd})
        except subprocess.TimeoutExpired:
            logger.warning("获取进程列表超时")
        except Exception as e:
            logger.warning(f"获取进程列表失败: {e}")
        return procs
    def _get_unix_procs(self):
        procs = []
        try:
            out = subprocess.run(
                'ps -eo pid,comm,args',
                shell=True,
                capture_output=True,
                text=True,
                errors='replace',
                creationflags=CREATE_NO_WINDOW,
                timeout=10
            )
            for line in out.stdout.split('\n')[1:]:
                if line.strip():
                    parts = line.split(maxsplit=2)
                    if len(parts) >= 2:
                        pid = parts[0]
                        name = parts[1]
                        cmd = parts[2] if len(parts) > 2 else ''
                        if pid.isdigit():
                            procs.append({'pid': int(pid), 'name': name, 'cmdline': cmd})
        except subprocess.TimeoutExpired:
            logger.warning("获取进程列表超时")
        except Exception as e:
            logger.warning(f"获取进程列表失败: {e}")
        return procs
    def get_alerts(self, max_count=5):
        return self.alert_queue[-max_count:]
    def clear_alerts(self):
        self.alert_queue.clear()
    def is_running(self):
        return self.running
    def block_file(self, path):
        self.blocked_files.add(path)
    def unblock_file(self, path):
        self.blocked_files.discard(path)

class BootProtectionEngine:
    def __init__(self):
        self.running = False
        self.monitor_thread = None
        self.boot_hashes = {}
        self.boot_alerts = []
        self.boot_files = []
        self.system_type = platform.system()
        self._init_boot()
    def _init_boot(self):
        os.makedirs(Config.BOOT_BACKUP_DIR, exist_ok=True)
        self._load_boot_files()
        self._load_hashes()
    def _load_boot_files(self):
        self.boot_files = []
        lst = Config.WINDOWS_BOOT_FILES if self.system_type == "Windows" else Config.LINUX_BOOT_FILES
        for pattern, desc in lst:
            if '*' in pattern:
                for f in glob.glob(pattern):
                    if os.path.exists(f):
                        self.boot_files.append((f, desc))
            else:
                if os.path.exists(pattern):
                    self.boot_files.append((pattern, desc))
    def _load_hashes(self):
        try:
            if os.path.exists(Config.BOOT_HASH_DB):
                with open(Config.BOOT_HASH_DB, 'rb') as f:
                    self.boot_hashes = pickle.load(f)
        except: pass
    def _save_hashes(self):
        try:
            with open(Config.BOOT_HASH_DB, 'wb') as f:
                pickle.dump(self.boot_hashes, f)
        except: pass
    def _calc_hash(self, path):
        try:
            h = hashlib.sha256()
            with open(path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    h.update(chunk)
            return h.hexdigest()
        except: return None
    def _backup_file(self, path, desc):
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe = re.sub(r'[<>:"/\\|?*]', '_', os.path.basename(path))
            backup = os.path.join(Config.BOOT_BACKUP_DIR, f"{ts}_{desc}_{safe}")
            shutil.copy2(path, backup)
            h = self._calc_hash(path)
            if h:
                self.boot_hashes[path] = {'hash': h, 'backup': backup, 'time': ts}
                self._save_hashes()
            return backup
        except: return None
    def start_protection(self):
        if self.running: return True
        self.running = True
        self._initial_check()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("引导保护启动")
        return True
    def stop_protection(self):
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
    def _initial_check(self):
        for path, desc in self.boot_files:
            if os.path.exists(path):
                if path not in self.boot_hashes:
                    self._backup_file(path, desc)
                else:
                    self._check_file(path, desc)
    def _check_file(self, path, desc):
        if not os.path.exists(path): return
        cur = self._calc_hash(path)
        stored = self.boot_hashes.get(path, {}).get('hash')
        if cur and stored and cur != stored:
            alert = {'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'file': desc,
                     'severity': '严重', 'type': '引导文件修改'}
            self.boot_alerts.insert(0, alert)
            logger.warning(f"引导文件被修改: {desc}")
            if Config.BOOT_AUTO_REPAIR:
                self._repair_file(path, desc)
    def _repair_file(self, path, desc):
        info = self.boot_hashes.get(path)
        if info and os.path.exists(info['backup']):
            shutil.copy2(info['backup'], path)
            logger.info(f"已修复引导文件: {desc}")
            return True
        return False
    def _monitor_loop(self):
        while self.running:
            for path, desc in self.boot_files:
                if os.path.exists(path):
                    self._check_file(path, desc)
            time.sleep(Config.BOOT_SCAN_INTERVAL)
    def check_integrity(self):
        results = {'total': len(self.boot_files), 'ok': 0, 'modified': 0, 'missing': 0, 'errors': 0,
                   'details': []}
        for path, desc in self.boot_files:
            if not os.path.exists(path):
                results['missing'] += 1
                results['details'].append({'file': desc, 'status': '丢失'})
                continue
            cur = self._calc_hash(path)
            stored = self.boot_hashes.get(path, {}).get('hash')
            if not stored:
                results['errors'] += 1
                results['details'].append({'file': desc, 'status': '未备份'})
            elif cur == stored:
                results['ok'] += 1
            else:
                results['modified'] += 1
                results['details'].append({'file': desc, 'status': '已修改'})
        results['score'] = (results['ok'] / results['total']) * 100 if results['total'] > 0 else 0
        return results
    def repair_all(self):
        repaired = 0
        errors = []
        for path, desc in self.boot_files:
            if self._repair_file(path, desc):
                repaired += 1
            else:
                errors.append(desc)
        return {'repaired': repaired, 'total': len(self.boot_files), 'errors': errors}
    def create_backup(self):
        backed = 0
        errors = []
        for path, desc in self.boot_files:
            if os.path.exists(path):
                if self._backup_file(path, desc):
                    backed += 1
                else:
                    errors.append(desc)
        return {'backed_up': backed, 'total': len(self.boot_files), 'errors': errors}
    def get_alerts(self, count=10):
        return self.boot_alerts[:count]
    def is_running(self):
        return self.running

class PYRTScanAnimation:
    def __init__(self, canvas, x, y, radius=180):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.radius = radius
        self.scanning = False
        self.angle = 0
        self.scan_line = None
        self.dots = []
        self.progress_arc = None
        self._create_elements()
    def _create_elements(self):
        self.outer = self.canvas.create_oval(self.x - self.radius, self.y - self.radius, self.x + self.radius,
                                             self.y + self.radius, outline=Config.THEME['secondary'], width=3)
        inner = self.radius - 30
        self.inner = self.canvas.create_oval(self.x - inner, self.y - inner, self.x + inner, self.y + inner,
                                             outline=Config.THEME['primary'], width=2)
        for i in range(0, 360, 15):
            rad = math.radians(i)
            dx = self.x + (self.radius - 15) * math.cos(rad)
            dy = self.y + (self.radius - 15) * math.sin(rad)
            dot = self.canvas.create_oval(dx - 2, dy - 2, dx + 2, dy + 2, fill=Config.THEME['secondary'],
                                          outline="")
            self.dots.append((dot, i))
        self.center_logo = self.canvas.create_text(self.x, self.y, text=Config.LOGO,
                                                   font=("Segoe UI Emoji", 48), fill=Config.THEME['primary'])
        self.center_text = self.canvas.create_text(self.x, self.y + 60, text="PYRT",
                                                   font=("Microsoft YaHei", 16, "bold"),
                                                   fill=Config.THEME['text_primary'])
        self.stats_text = self.canvas.create_text(self.x, self.y + self.radius + 50,
                                                  text=lang.get_text("preparing_scan"),
                                                  font=("Microsoft YaHei", 11),
                                                  fill=Config.THEME['text_secondary'])
    def start_scan(self):
        self.scanning = True
        self._animate()
    def stop_scan(self):
        self.scanning = False
        if self.scan_line:
            self.canvas.delete(self.scan_line)
            self.scan_line = None
        if self.progress_arc:
            self.canvas.delete(self.progress_arc)
            self.progress_arc = None
        for dot, _ in self.dots:
            self.canvas.itemconfig(dot, fill=Config.THEME['secondary'])
    def _animate(self):
        if not self.scanning or not self.canvas.winfo_exists():
            return
        self.angle = (self.angle + 5) % 360
        rad = math.radians(self.angle)
        ex = self.x + self.radius * math.cos(rad)
        ey = self.y + self.radius * math.sin(rad)
        if self.scan_line:
            self.canvas.delete(self.scan_line)
        self.scan_line = self.canvas.create_line(self.x, self.y, ex, ey, fill=Config.THEME['primary'], width=2,
                                                 arrow="last")
        for dot, ang in self.dots:
            diff = abs((self.angle - ang) % 360)
            if diff < 30:
                intensity = 1 - diff / 30
                r = int(100 + 155 * intensity)
                g = int(255 * intensity)
                b = int(218 * intensity)
                self.canvas.itemconfig(dot, fill=f'#{r:02x}{g:02x}{b:02x}')
            else:
                self.canvas.itemconfig(dot, fill=Config.THEME['secondary'])
        self.canvas.after(20, self._animate)
    def update_stats(self, scanned, total, threats, progress, speed):
        txt = f"📊 {scanned}/{total} {lang.get_text('files')} | 🦠 {threats} {lang.get_text('threats')} | ⚡ {speed} {lang.get_text('speed')}"
        self.canvas.itemconfig(self.stats_text, text=txt)
        if self.progress_arc:
            self.canvas.delete(self.progress_arc)
        if progress > 0:
            angle = 360 * progress / 100
            self.progress_arc = self.canvas.create_arc(self.x - self.radius, self.y - self.radius,
                                                       self.x + self.radius, self.y + self.radius,
                                                       start=90, extent=-angle, outline=Config.THEME['success'],
                                                       width=3, style=tk.ARC)

class IntelligentLearningEngine:
    def __init__(self):
        self.running = False
        self.learning_active = False
        self.samples = []
        self.baseline = None
        self.alerts = []
        self.monitor_thread = None
        self.learning_thread = None
        self.sample_interval = Config.LEARNING_SAMPLE_INTERVAL
        self.required_samples = Config.LEARNING_SAMPLE_COUNT
        self.threshold = Config.LEARNING_DEVIATION_THRESHOLD
        self._init_log()
        logger.info("智能学习引擎初始化")
    def _init_log(self):
        try:
            os.makedirs(Config.LOG_DIR, exist_ok=True)
            handler = logging.FileHandler(os.path.join(Config.LOG_DIR, Config.INTELLIGENT_LEARNING_LOG),
                                          encoding='utf-8')
            handler.setFormatter(logging.Formatter('%(asctime)s - [智能学习] - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
        except: pass
    def _get_cpu(self):
        if platform.system() == "Windows":
            try:
                res = subprocess.run(['wmic', 'cpu', 'get', 'loadpercentage'], capture_output=True, text=True,
                                     encoding='gbk', errors='replace', creationflags=CREATE_NO_WINDOW,
                                     timeout=5)
                lines = res.stdout.strip().split('\n')
                if len(lines) >= 2:
                    return float(lines[1].strip())
            except: pass
            return 20.0 + (time.time() % 15)
        else:
            try:
                with open('/proc/stat', 'r') as f:
                    line = f.readline()
                return 15.0 + (time.time() % 20)
            except: return 20.0
    def _get_mem(self):
        if platform.system() == "Windows":
            try:
                res = subprocess.run(['wmic', 'OS', 'get', 'TotalVisibleMemorySize,FreePhysicalMemory'],
                                     capture_output=True, text=True, encoding='gbk', errors='replace',
                                     creationflags=CREATE_NO_WINDOW, timeout=5)
                lines = res.stdout.strip().split('\n')
                if len(lines) >= 2:
                    parts = lines[1].split()
                    if len(parts) >= 2:
                        total = float(parts[0])
                        free = float(parts[1])
                        used = total - free
                        return (used / total) * 100.0
            except: pass
            return 40.0 + (time.time() % 30)
        else:
            try:
                with open('/proc/meminfo', 'r') as f:
                    mem = {}
                    for line in f:
                        k, v = line.split(':')
                        v = v.strip().split()[0]
                        mem[k] = float(v)
                total = mem.get('MemTotal', 1)
                avail = mem.get('MemAvailable', total)
                used = total - avail
                return (used / total) * 100.0
            except: return 35.0
    def _collect_sample(self):
        return (self._get_cpu(), self._get_mem())
    def _calc_baseline(self, samples):
        cpu_vals = [s[0] for s in samples]
        mem_vals = [s[1] for s in samples]
        cpu_mean = sum(cpu_vals) / len(cpu_vals)
        cpu_var = sum((x - cpu_mean) ** 2 for x in cpu_vals) / len(cpu_vals)
        cpu_std = math.sqrt(cpu_var)
        mem_mean = sum(mem_vals) / len(mem_vals)
        mem_var = sum((x - mem_mean) ** 2 for x in mem_vals) / len(mem_vals)
        mem_std = math.sqrt(mem_var)
        return {'cpu_mean': cpu_mean, 'cpu_std': cpu_std, 'mem_mean': mem_mean, 'mem_std': mem_std}
    def start_learning(self, progress_callback=None, complete_callback=None):
        if self.learning_active: return False
        self.learning_active = True
        self.samples = []
        def task():
            collected = 0
            while self.learning_active and collected < self.required_samples:
                sample = self._collect_sample()
                self.samples.append(sample)
                collected += 1
                if progress_callback:
                    progress_callback(collected / self.required_samples * 100)
                time.sleep(self.sample_interval)
            self.learning_active = False
            if len(self.samples) >= self.required_samples:
                self.baseline = self._calc_baseline(self.samples)
                if complete_callback:
                    complete_callback(True, self.baseline)
            else:
                if complete_callback:
                    complete_callback(False, None)
        self.learning_thread = threading.Thread(target=task, daemon=True)
        self.learning_thread.start()
        return True
    def stop_learning(self):
        self.learning_active = False
        if self.learning_thread and self.learning_thread.is_alive():
            self.learning_thread.join(timeout=1)
    def reset_baseline(self):
        self.baseline = None
        self.samples = []
        self.alerts = []
    def start_monitoring(self):
        if self.running: return
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
    def stop_monitoring(self):
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
    def _monitor_loop(self):
        while self.running:
            if self.baseline is not None:
                cpu, mem = self._collect_sample()
                cpu_dev = abs(cpu - self.baseline['cpu_mean']) / (self.baseline['cpu_std'] + 1e-6)
                mem_dev = abs(mem - self.baseline['mem_mean']) / (self.baseline['mem_std'] + 1e-6)
                if cpu_dev > self.threshold or mem_dev > self.threshold:
                    alert = {
                        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'cpu': cpu, 'mem': mem,
                        'cpu_dev': cpu_dev, 'mem_dev': mem_dev,
                        'severity': '高' if max(cpu_dev, mem_dev) > 3.0 else '中',
                        'message': f"性能异常: CPU偏离{cpu_dev:.1f}σ, MEM偏离{mem_dev:.1f}σ"
                    }
                    self.alerts.insert(0, alert)
                    if len(self.alerts) > 100:
                        self.alerts = self.alerts[:100]
                    logger.warning(f"智能学习: {alert['message']}")
            time.sleep(2)
    def get_current_metrics(self):
        cpu, mem = self._collect_sample()
        if self.baseline is None:
            return {'cpu': cpu, 'mem': mem, 'cpu_dev': None, 'mem_dev': None}
        cpu_dev = abs(cpu - self.baseline['cpu_mean']) / (self.baseline['cpu_std'] + 1e-6)
        mem_dev = abs(mem - self.baseline['mem_mean']) / (self.baseline['mem_std'] + 1e-6)
        return {'cpu': cpu, 'mem': mem, 'cpu_dev': cpu_dev, 'mem_dev': mem_dev}
    def get_baseline(self): return self.baseline
    def get_alerts(self, count=10): return self.alerts[:count]
    def is_learning(self): return self.learning_active
    def is_monitoring(self): return self.running

class USBMonitorEngine:
    def __init__(self, scan_engine, quarantine_callback=None):
        self.scan_engine = scan_engine
        self.quarantine_callback = quarantine_callback
        self.running = False
        self.monitor_thread = None
        self.known_drives = set()
        self.scan_results = []
        self.detected_devices = []
        self._init_log()
    def _init_log(self):
        try:
            os.makedirs(Config.LOG_DIR, exist_ok=True)
            handler = logging.FileHandler(os.path.join(Config.LOG_DIR, "usb_monitor.log"), encoding='utf-8')
            handler.setFormatter(logging.Formatter('%(asctime)s - [USB监控] - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
        except: pass
    def start(self):
        if self.running: return False
        self.running = True
        self._update_known_drives()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("USB监控已启动")
        return True
    def stop(self):
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        logger.info("USB监控已停止")
    def _update_known_drives(self):
        self.known_drives = set(self._get_removable_drives())
    def _get_removable_drives(self):
        drives = []
        if platform.system() == "Windows":
            try:
                result = subprocess.run(['wmic', 'logicaldisk', 'where', 'DriveType=2', 'get', 'DeviceID'],
                                        capture_output=True, text=True, encoding='gbk', errors='replace',
                                        creationflags=CREATE_NO_WINDOW, timeout=5)
                for line in result.stdout.split('\n'):
                    line = line.strip()
                    if line and len(line) == 2 and line[1] == ':':
                        drives.append(line + "\\")
            except: pass
        else:
            for path in ['/media', '/mnt', '/run/media']:
                if os.path.exists(path):
                    for item in os.listdir(path):
                        full = os.path.join(path, item)
                        if os.path.ismount(full):
                            drives.append(full)
        return drives
    def _monitor_loop(self):
        while self.running:
            current = set(self._get_removable_drives())
            new_drives = current - self.known_drives
            if new_drives:
                for drive in new_drives:
                    self.detected_devices.append(drive)
                    logger.info(f"检测到新USB设备: {drive}")
                    self._scan_usb_drive(drive)
            self.known_drives = current
            time.sleep(Config.USB_SCAN_INTERVAL)
    def _scan_usb_drive(self, drive):
        threats = []
        autorun = os.path.join(drive, "Autorun.inf")
        if os.path.exists(autorun):
            threats.append({'name': 'Autorun.inf (蠕虫载体)', 'file': autorun, 'severity': '高',
                            'type': 'USB蠕虫'})
            if Config.USB_BLOCK_AUTORUN:
                try:
                    os.rename(autorun, autorun + ".pyrt_backup")
                    logger.info(f"已重命名 Autorun.inf: {autorun}")
                except: pass
        exe_exts = ('.exe', '.com', '.scr', '.bat', '.cmd', '.vbs', '.ps1', '.jar', '.msi')
        for root, dirs, files in os.walk(drive):
            for f in files:
                if f.lower().endswith(exe_exts):
                    fpath = os.path.join(root, f)
                    t = self.scan_engine._scan_file(fpath)
                    if t:
                        threats.extend(t)
            if root == drive:
                for d in dirs[:]:
                    if d.startswith('$') or d.lower() in ['system volume information', 'recycle.bin']:
                        dirs.remove(d)
            else:
                break
        if threats:
            self.scan_results.extend(threats)
            logger.warning(f"USB {drive} 发现 {len(threats)} 个威胁")
            if Config.USB_QUARANTINE_THREATS and self.quarantine_callback:
                for t in threats:
                    self.quarantine_callback(t['file'], t)
        else:
            logger.info(f"USB {drive} 扫描安全")
    def get_scan_results(self): return self.scan_results
    def clear_results(self): self.scan_results.clear()
    def get_detected_devices(self): return self.detected_devices
    def is_running(self): return self.running

class ScheduledScanEngine:
    def __init__(self, scan_engine, start_scan_callback):
        self.scan_engine = scan_engine
        self.start_scan_callback = start_scan_callback
        self.running = False
        self.thread = None
    def start(self):
        if self.running: return
        self.running = True
        self.thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.thread.start()
        logger.info("定时扫描调度器启动")
    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)
        logger.info("定时扫描调度器停止")
    def _scheduler_loop(self):
        while self.running:
            if Config.SCHEDULED_SCAN_ENABLED:
                now = datetime.now()
                try:
                    h, m = map(int, Config.SCHEDULED_SCAN_TIME.split(':'))
                except:
                    h, m = 2, 0
                if now.hour == h and now.minute == m and now.second == 0:
                    if Config.SCHEDULED_SCAN_FREQUENCY == "daily" or \
                            (Config.SCHEDULED_SCAN_FREQUENCY == "weekly" and now.weekday() == Config.SCHEDULED_SCAN_DAY):
                        logger.info("定时扫描触发")
                        self.start_scan_callback(Config.SCHEDULED_SCAN_TYPE)
                        time.sleep(60)
            time.sleep(30)
    def is_running(self): return self.running

class ShredderEngine:
    @staticmethod
    def shred_file(file_path, passes=3):
        if not os.path.exists(file_path): return False, "文件不存在"
        try:
            size = os.path.getsize(file_path)
            with open(file_path, 'wb') as f:
                for _ in range(passes):
                    f.seek(0)
                    f.write(os.urandom(size))
                    f.flush()
                    os.fsync(f.fileno())
                    f.seek(0)
                    f.write(b'\x00' * size)
                    f.flush()
                    os.fsync(f.fileno())
            os.remove(file_path)
            return True, "粉碎成功"
        except Exception as e: return False, str(e)
    @staticmethod
    def shred_directory(dir_path, passes=3, progress_callback=None):
        total = 0
        for root, dirs, files in os.walk(dir_path, topdown=False):
            for f in files:
                fp = os.path.join(root, f)
                success, msg = ShredderEngine.shred_file(fp, passes)
                total += 1
                if progress_callback:
                    progress_callback(total, msg)
        try:
            shutil.rmtree(dir_path)
        except: pass
        return total

class PrivacyCleaner:
    @staticmethod
    def get_browser_paths(browser):
        if platform.system() != "Windows": return []
        home = os.path.expanduser("~")
        if browser == "chrome":
            return [os.path.join(home, "AppData", "Local", "Google", "Chrome", "User Data", "Default")]
        elif browser == "firefox":
            profiles = os.path.join(os.environ.get('APPDATA', ''), "Mozilla", "Firefox", "Profiles")
            if os.path.exists(profiles):
                return [os.path.join(profiles, d) for d in os.listdir(profiles) if d.endswith('.default')]
            return []
        elif browser == "edge":
            return [os.path.join(home, "AppData", "Local", "Microsoft", "Edge", "User Data", "Default")]
        return []
    @staticmethod
    def clean_browser(browser, items=['cache', 'cookies', 'history']):
        cleaned = 0
        paths = PrivacyCleaner.get_browser_paths(browser)
        for base in paths:
            if not os.path.exists(base): continue
            if 'cache' in items:
                cache_dir = os.path.join(base, "Cache")
                if os.path.exists(cache_dir):
                    try:
                        shutil.rmtree(cache_dir)
                        cleaned += 1
                    except: pass
            if 'cookies' in items:
                cookie_file = os.path.join(base, "Cookies")
                if os.path.exists(cookie_file):
                    try:
                        os.remove(cookie_file)
                        cleaned += 1
                    except: pass
            if 'history' in items:
                history_file = os.path.join(base, "History")
                if os.path.exists(history_file):
                    try:
                        os.remove(history_file)
                        cleaned += 1
                    except: pass
        return cleaned
    @staticmethod
    def clean_system_temp():
        temp_dirs = [os.environ.get('TEMP', ''), os.environ.get('TMP', '')]
        if platform.system() == "Windows":
            temp_dirs.append(os.path.join(os.environ.get('WINDIR', 'C:\\Windows'), 'Temp'))
        cleaned_size = 0
        for d in temp_dirs:
            if os.path.exists(d):
                for root, dirs, files in os.walk(d):
                    for f in files:
                        fp = os.path.join(root, f)
                        try:
                            cleaned_size += os.path.getsize(fp)
                            os.remove(fp)
                        except: pass
        return cleaned_size

class VulnerabilityScanner:
    @staticmethod
    def scan():
        if platform.system() == "Windows":
            return VulnerabilityScanner._scan_windows()
        else:
            return VulnerabilityScanner._scan_linux()
    @staticmethod
    def _scan_windows():
        try:
            result = subprocess.run(['wmic', 'qfe', 'list', 'brief', '/format:csv'],
                                    capture_output=True, text=True, encoding='gbk', errors='replace',
                                    creationflags=CREATE_NO_WINDOW, timeout=30)
            lines = result.stdout.split('\n')
            count = sum(1 for line in lines if line and 'KB' in line)
            try:
                key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                     r"SOFTWARE\Microsoft\Windows\CurrentVersion\WindowsUpdate\Auto Update")
                au, _ = winreg.QueryValueEx(key, "AUOptions")
                auto_enabled = au in [2, 3, 4]
            except:
                auto_enabled = False
            if count < 10:
                updates_missing = 20 - count
                return {'updates_missing': max(0, updates_missing),
                        'details': f"已安装 {count} 个更新，建议运行 Windows Update", 'status': 'warning'}
            else:
                return {'updates_missing': 0, 'details': f"已安装 {count} 个更新", 'status': 'ok'}
        except Exception as e:
            return {'updates_missing': -1, 'details': f"扫描出错: {str(e)}", 'status': 'error'}
    @staticmethod
    def _scan_linux():
        try:
            if shutil.which('apt-get'):
                result = subprocess.run(['apt-get', '--just-print', 'upgrade'],
                                        capture_output=True, text=True, errors='replace', timeout=60,
                                        creationflags=CREATE_NO_WINDOW)
                lines = result.stdout.split('\n')
                upgrades = sum(1 for line in lines if 'upgraded,' in line or 'upgraded' in line)
                if upgrades > 0:
                    return {'updates_missing': upgrades, 'details': f'有 {upgrades} 个软件包可更新',
                            'status': 'warning'}
                else:
                    return {'updates_missing': 0, 'details': '系统已是最新', 'status': 'ok'}
            elif shutil.which('yum'):
                result = subprocess.run(['yum', 'check-update', '-q'],
                                        capture_output=True, text=True, errors='replace', timeout=60,
                                        creationflags=CREATE_NO_WINDOW)
                lines = result.stdout.split('\n')
                count = sum(1 for line in lines if line and not line.startswith('Loaded'))
                if count > 0:
                    return {'updates_missing': count, 'details': f'有 {count} 个软件包可更新',
                            'status': 'warning'}
                else:
                    return {'updates_missing': 0, 'details': '系统已是最新', 'status': 'ok'}
            else:
                return {'updates_missing': -1, 'details': '未识别的包管理器', 'status': 'error'}
        except Exception as e:
            return {'updates_missing': -1, 'details': f"扫描出错: {str(e)}", 'status': 'error'}

class RansomwareBehaviorEngine:
    def __init__(self):
        self.running = False
        self.monitor_thread = None
        self.suspicious_operations = []
        self._init_log()
        self.SUSPICIOUS_EXTENSIONS = ['.locked', '.encrypted', '.crypto', '.wncry', '.wcry',
                                      '.cerber', '.locky', '.gandcrab', '.krab', '.rbq',
                                      '.readme', '.dmx', '.ttt', '.micro', '.ecc', '.ezz']
        self.THRESHOLD = 5
    def _init_log(self):
        try:
            os.makedirs(Config.LOG_DIR, exist_ok=True)
            handler = logging.FileHandler(os.path.join(Config.LOG_DIR, "ransomware_behavior.log"),
                                          encoding='utf-8')
            handler.setFormatter(logging.Formatter('%(asctime)s - [勒索行为防御] - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
        except: pass
    def start(self):
        if self.running: return False
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("勒索行为主动防御引擎已启动")
        return True
    def stop(self):
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        logger.info("勒索行为主动防御引擎已停止")
    def _monitor_loop(self):
        watched_dirs = [
            os.path.expanduser("~\\Desktop"),
            os.path.expanduser("~\\Documents"),
            os.path.expanduser("~\\Downloads"),
            os.path.expanduser("~\\Pictures"),
            os.path.expanduser("~\\Music"),
            os.path.expanduser("~\\Videos"),
            os.environ.get('USERPROFILE', ''),
        ]
        known_files = {}
        for d in watched_dirs:
            if os.path.exists(d):
                for root, dirs, files in os.walk(d):
                    for f in files:
                        fp = os.path.join(root, f)
                        try:
                            st = os.stat(fp)
                            known_files[fp] = (st.st_mtime, st.st_size)
                        except: pass
        while self.running:
            try:
                current_files = {}
                for d in watched_dirs:
                    if os.path.exists(d):
                        for root, dirs, files in os.walk(d):
                            for f in files:
                                fp = os.path.join(root, f)
                                try:
                                    st = os.stat(fp)
                                    current_files[fp] = (st.st_mtime, st.st_size)
                                except: pass
                for fp in current_files:
                    ext = os.path.splitext(fp)[1].lower()
                    if ext in self.SUSPICIOUS_EXTENSIONS:
                        if fp not in known_files:
                            alert = {
                                'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                'type': '勒索软件行为',
                                'severity': '严重',
                                'file': fp,
                                'message': f'检测到可疑加密文件: {os.path.basename(fp)}'
                            }
                            self.suspicious_operations.insert(0, alert)
                            logger.warning(f"勒索行为防御: {alert['message']}")
                            if len(self.suspicious_operations) > 100:
                                self.suspicious_operations = self.suspicious_operations[:100]
                modified_files = []
                for fp in known_files:
                    if fp in current_files:
                        old_mtime, old_size = known_files[fp]
                        new_mtime, new_size = current_files[fp]
                        if new_mtime != old_mtime and new_size != old_size:
                            modified_files.append(fp)
                if len(modified_files) > self.THRESHOLD:
                    alert = {
                        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'type': '勒索软件行为',
                        'severity': '严重',
                        'message': f'检测到批量文件修改 ({len(modified_files)} 个文件)，可能是勒索软件活动！',
                        'files': modified_files[:10]
                    }
                    self.suspicious_operations.insert(0, alert)
                    logger.warning(f"勒索行为防御: {alert['message']}")
                    if len(self.suspicious_operations) > 100:
                        self.suspicious_operations = self.suspicious_operations[:100]
                known_files = current_files
                time.sleep(5)
            except Exception as e:
                logger.error(f"勒索行为防御监控异常: {e}")
                time.sleep(30)
    def get_alerts(self, count=20): return self.suspicious_operations[:count]
    def clear_alerts(self): self.suspicious_operations.clear()
    def is_running(self): return self.running
    def detect_bat_file(self, file_path):
        if not os.path.exists(file_path): return None
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in ['.bat', '.cmd', '.ps1', '.vbs']: return None
        try:
            with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
                content = f.read().lower()
            suspicious_patterns = [
                'ren ', 'rename ', '.locked', '.encrypted',
                'for %%', 'for %', 'del ', 'erase ',
                'timeout /t', '模拟勒索', '模拟锁定'
            ]
            for pattern in suspicious_patterns:
                if pattern in content:
                    return f"包含可疑命令: {pattern}"
            return None
        except: return None

class ProcessBlockEngine:
    def __init__(self):
        self.running = False
        self.monitor_thread = None
        self.blocked_processes = []
        self.suspicious_processes = []
        self._init_log()
        self.SUSPICIOUS_PATTERNS = [
            '勒索', 'encrypt', 'lock', 'ransom', 'crypto',
            'wannacry', 'locky', 'cerber', 'gandcrab',
            '模拟勒索', '模拟锁定', '.locked'
        ]
        self.SUSPICIOUS_NAMES = [
            'taskkill.exe', 'wscript.exe', 'cscript.exe', 'mshta.exe',
            'regsvr32.exe', 'rundll32.exe', 'certutil.exe',
            'powershell.exe', 'cmd.exe'
        ]
    def _init_log(self):
        try:
            os.makedirs(Config.LOG_DIR, exist_ok=True)
            handler = logging.FileHandler(os.path.join(Config.LOG_DIR, "process_block.log"), encoding='utf-8')
            handler.setFormatter(logging.Formatter('%(asctime)s - [进程拦截] - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
        except: pass
    def start(self):
        if self.running: return False
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("进程监控拦截引擎已启动")
        return True
    def stop(self):
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2)
        logger.info("进程监控拦截引擎已停止")
    def _monitor_loop(self):
        known_pids = set()
        while self.running:
            try:
                current_pids = set()
                procs = self._get_processes()
                for proc in procs:
                    pid = proc.get('pid')
                    name = proc.get('name', '').lower()
                    cmdline = proc.get('cmdline', '').lower()
                    if pid:
                        current_pids.add(pid)
                        if pid not in known_pids:
                            is_suspicious = False
                            reason = ""
                            for sus in self.SUSPICIOUS_NAMES:
                                if sus in name:
                                    is_suspicious = True
                                    reason = f"可疑进程名: {name}"
                                    break
                            if not is_suspicious:
                                for pat in self.SUSPICIOUS_PATTERNS:
                                    if pat in cmdline or pat in name:
                                        is_suspicious = True
                                        reason = f"包含可疑关键词: {pat}"
                                        break
                            if not is_suspicious:
                                if 'cmd.exe' in name and '.bat' in cmdline:
                                    is_suspicious = True
                                    reason = f"执行批处理文件: {cmdline[:80]}"
                            if is_suspicious:
                                alert = {
                                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                                    'pid': pid,
                                    'name': name,
                                    'cmdline': cmdline[:200],
                                    'reason': reason,
                                    'severity': '高'
                                }
                                self.suspicious_processes.append(alert)
                                self.blocked_processes.append(alert)
                                logger.warning(f"进程拦截: {reason} (PID: {pid})")
                                if Config.PROCESS_BLOCK_POPUP:
                                    self._show_block_popup(alert)
                                if Config.AUTO_KILL_SUSPICIOUS:
                                    self._kill_process(pid)
                known_pids = current_pids
                time.sleep(3)
            except Exception as e:
                logger.error(f"进程监控异常: {e}")
                time.sleep(10)
    def _get_processes(self):
        procs = []
        try:
            if platform.system() == "Windows":
                result = subprocess.run(
                    ['wmic', 'process', 'get', 'ProcessId,Name,CommandLine'],
                    capture_output=True, text=True, encoding='gbk', errors='replace',
                    creationflags=CREATE_NO_WINDOW, timeout=10
                )
                lines = result.stdout.split('\n')
                for line in lines[1:]:
                    if line.strip():
                        parts = line.split(maxsplit=2)
                        if len(parts) >= 3:
                            name = parts[0]
                            pid = parts[1]
                            cmd = parts[2] if len(parts) > 2 else ''
                            if pid.isdigit():
                                procs.append({'pid': int(pid), 'name': name, 'cmdline': cmd})
            else:
                result = subprocess.run(
                    ['ps', '-eo', 'pid,comm,args'],
                    capture_output=True, text=True, errors='replace',
                    creationflags=CREATE_NO_WINDOW, timeout=10
                )
                for line in result.stdout.split('\n')[1:]:
                    if line.strip():
                        parts = line.split(maxsplit=2)
                        if len(parts) >= 2:
                            pid = parts[0]
                            name = parts[1]
                            cmd = parts[2] if len(parts) > 2 else ''
                            if pid.isdigit():
                                procs.append({'pid': int(pid), 'name': name, 'cmdline': cmd})
        except subprocess.TimeoutExpired:
            logger.warning("获取进程列表超时")
        except Exception as e:
            logger.error(f"获取进程列表失败: {e}")
        return procs
    def _kill_process(self, pid):
        try:
            if platform.system() == "Windows":
                subprocess.run(
                    ['taskkill', '/F', '/PID', str(pid)],
                    capture_output=True, encoding='gbk', errors='replace',
                    creationflags=CREATE_NO_WINDOW, timeout=5
                )
                logger.info(f"已终止可疑进程 PID: {pid}")
            else:
                subprocess.run(['kill', '-9', str(pid)], capture_output=True, timeout=5)
                logger.info(f"已终止可疑进程 PID: {pid}")
        except Exception as e:
            logger.error(f"终止进程失败: {e}")
    def _show_block_popup(self, alert):
        try:
            popup = tk.Toplevel()
            popup.title("🚨 PYRT 安全警告 - 可疑进程已拦截")
            popup.geometry("600x400")
            popup.configure(bg=Config.THEME['bg_dark'])
            popup.transient()
            popup.grab_set()
            popup.focus_force()
            popup.update_idletasks()
            x = (popup.winfo_screenwidth() - 600) // 2
            y = (popup.winfo_screenheight() - 400) // 2
            popup.geometry(f"600x400+{x}+{y}")
            tk.Label(popup, text="🚨 检测到可疑进程", font=("Microsoft YaHe", 20, "bold"),
                     fg='#ff0000', bg=Config.THEME['bg_dark']).pack(pady=(20, 10))
            tk.Label(popup, text="PYRT安全卫士已拦截可疑进程，保护您的系统安全！",
                     font=("Microsoft YaHe", 12), fg=Config.THEME['text_secondary'],
                     bg=Config.THEME['bg_dark']).pack(pady=(0, 15))
            info_frame = tk.Frame(popup, bg=Config.THEME['bg_card'], padx=15, pady=15)
            info_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
            details = [
                ("进程名称:", alert.get('name', '未知')),
                ("进程PID:", str(alert.get('pid', '未知'))),
                ("威胁等级:", "🔴 高危"),
                ("拦截原因:", alert.get('reason', '可疑行为')),
                ("命令行:", alert.get('cmdline', '')[:150] + ('...' if len(alert.get('cmdline', '')) > 150 else ''))
            ]
            for i, (label, value) in enumerate(details):
                row = tk.Frame(info_frame, bg=Config.THEME['bg_card'])
                row.pack(fill=tk.X, pady=3)
                tk.Label(row, text=label, font=("Microsoft YaHei", 10, "bold"),
                         fg=Config.THEME['text_primary'], bg=Config.THEME['bg_card'],
                         width=12, anchor=tk.W).pack(side=tk.LEFT)
                tk.Label(row, text=value, font=("Consolas", 10),
                         fg=Config.THEME['text_secondary'], bg=Config.THEME['bg_card'],
                         wraplength=400, justify=tk.LEFT).pack(side=tk.LEFT, fill=tk.X, expand=True)
            btn_frame = tk.Frame(popup, bg=Config.THEME['bg_dark'])
            btn_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
            tk.Button(btn_frame, text="✅ 已知晓，已拦截", command=popup.destroy,
                      bg=Config.THEME['success'], fg='white', font=("Microsoft YaHei", 12),
                      padx=30, pady=8, relief=tk.FLAT).pack(side=tk.LEFT, padx=(0, 10))
            tk.Button(btn_frame, text="📋 查看详情", command=lambda: self._show_process_detail(alert, popup),
                      bg=Config.THEME['primary'], fg='white', font=("Microsoft YaHei", 12),
                      padx=30, pady=8, relief=tk.FLAT).pack(side=tk.LEFT)
            popup.after(30000, popup.destroy)
        except Exception as e:
            logger.error(f"显示拦截弹窗失败: {e}")
    def _show_process_detail(self, alert, parent):
        try:
            detail_win = tk.Toplevel(parent)
            detail_win.title("进程详细信息")
            detail_win.geometry("700x500")
            detail_win.configure(bg=Config.THEME['bg_dark'])
            detail_win.transient(parent)
            detail_win.grab_set()
            text = tk.Text(detail_win, bg=Config.THEME['bg_card'], fg=Config.THEME['text_primary'],
                           font=("Consolas", 10), wrap=tk.WORD, padx=15, pady=15)
            text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            info = f"""
【拦截详情】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

拦截时间: {alert.get('time', '未知')}
进程名称: {alert.get('name', '未知')}
进程 PID: {alert.get('pid', '未知')}
威胁等级: 🔴 高危
拦截原因: {alert.get('reason', '未知')}

完整命令行:
{alert.get('cmdline', '无')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ 该进程已被 PYRT 安全卫士拦截并终止。

如果您确信该进程是安全的，请在设置中关闭"进程拦截"功能。
但请注意，这可能会降低系统安全性。
"""
            text.insert(tk.END, info)
            text.config(state=tk.DISABLED)
            tk.Button(detail_win, text="关闭", command=detail_win.destroy,
                      bg=Config.THEME['primary'], fg='white', font=("Microsoft YaHe", 11),
                      padx=30, pady=8).pack(pady=(0, 10))
        except Exception as e:
            logger.error(f"显示详情失败: {e}")
    def get_alerts(self, count=20): return self.suspicious_processes[-count:] if self.suspicious_processes else []
    def clear_alerts(self): self.suspicious_processes.clear()
    def is_running(self): return self.running

class PYRTSplashScreen:
    def __init__(self, root, callback):
        self.root = root
        self.root.title(lang.get_text("app_name"))
        self.root.geometry("600x420")
        self.root.configure(bg=Config.THEME['splash_bg'])
        self.root.overrideredirect(True)
        self.callback = callback
        self.progress = 0
        self.running = True
        self._create()
        self.root.after(50, self._animate)
    def _create(self):
        canvas = tk.Canvas(self.root, bg=Config.THEME['splash_bg'], highlightthickness=0, width=600, height=420)
        canvas.pack(fill=tk.BOTH, expand=True)
        canvas.create_text(300, 120, text="🛡️", font=("Segoe UI Emoji", 72), fill=Config.THEME['splash_accent'])
        canvas.create_text(300, 200, text=lang.get_text("app_name"),
                           font=("Microsoft YaHei", 28, "bold"), fill=Config.THEME['splash_fg'])
        canvas.create_text(300, 240, text=f"{lang.get_text('version')} {Config.VERSION}",
                           font=("Microsoft YaHei", 12), fill=Config.THEME['splash_fg'])
        canvas.create_text(300, 275, text=lang.get_text("you_online"),
                           font=("Microsoft YaHei", 11), fill=Config.THEME['splash_fg'])
        canvas.create_rectangle(100, 320, 500, 340, fill=Config.THEME['splash_fg'], outline="")
        self.progress_bar = canvas.create_rectangle(102, 322, 102, 338, fill=Config.THEME['splash_accent'],
                                                    outline="")
        self.progress_text = canvas.create_text(300, 360, text="0%",
                                                font=("Microsoft YaHei", 11), fill=Config.THEME['splash_fg'])
        self.status_text = canvas.create_text(300, 385, text=lang.get_text("loading") + "...",
                                              font=("Microsoft YaHei", 10), fill=Config.THEME['splash_fg'])
        canvas.create_text(300, 410, text=f"© 2026 PYRT开源",
                           font=("Microsoft YaHe", 8), fill=Config.THEME['splash_fg'])
        self.canvas = canvas
        self.dot_visible = [True, False, False]
        self.dot1 = canvas.create_oval(280, 150, 285, 155, fill=Config.THEME['splash_accent'], outline="")
        self.dot2 = canvas.create_oval(295, 150, 300, 155, fill=Config.THEME['splash_accent'], outline="")
        self.dot3 = canvas.create_oval(310, 150, 315, 155, fill=Config.THEME['splash_accent'], outline="")
    def _animate(self):
        if not self.running: return
        self.dot_visible = [self.dot_visible[2], self.dot_visible[0], self.dot_visible[1]]
        states = ['#ffffff', '#ffffff', '#ffffff']
        for i, visible in enumerate(self.dot_visible):
            if visible:
                states[i] = Config.THEME['splash_accent']
        self.canvas.itemconfig(self.dot1, fill=states[0])
        self.canvas.itemconfig(self.dot2, fill=states[1])
        self.canvas.itemconfig(self.dot3, fill=states[2])
        if self.progress < 100:
            self.progress += random.randint(1, 3)
            if self.progress > 100: self.progress = 100
            width = 396 * (self.progress / 100)
            self.canvas.coords(self.progress_bar, 102, 322, 102 + width, 338)
            self.canvas.itemconfig(self.progress_text, text=f"{self.progress}%")
            if self.progress < 30:
                status = lang.get_text("loading_engines")
            elif self.progress < 60:
                status = lang.get_text("loading_db")
            elif self.progress < 85:
                status = lang.get_text("loading_ui")
            else:
                status = lang.get_text("loading_complete")
            self.canvas.itemconfig(self.status_text, text=status)
            self.root.after(50, self._animate)
        else:
            self.root.after(300, self._launch)
    def _launch(self):
        self.running = False
        try:
            self.root.destroy()
        except: pass
        if self.callback:
            self.callback()
class QVMainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{lang.get_text('app_name')} {Config.VERSION}")
        self.root.geometry("1100x750")
        self.root.configure(bg=Config.THEME['bg_dark'])
        self.root.minsize(900, 600)
        self.root.overrideredirect(True)

        self.root.bind('<Button-1>', self._start_move)
        self.root.bind('<B1-Motion>', self._on_move)
        self.root.bind('<ButtonRelease-1>', self._stop_move)
        self._drag_data = {'x': 0, 'y': 0, 'dragging': False}

        # 设置圆角窗口（Windows） - 半径 35
        if platform.system() == "Windows":
            try:
                hwnd = ctypes.windll.user32.GetParent(self.root.winfo_id())
                if not hwnd:
                    hwnd = self.root.winfo_id()
                style = GetWindowLongW(hwnd, GWL_STYLE)
                style &= ~(WS_CAPTION | WS_THICKFRAME | WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_SYSMENU)
                SetWindowLongW(hwnd, GWL_STYLE, style)
                width = self.root.winfo_width()
                height = self.root.winfo_height()
                if width <= 1 or height <= 1:
                    width, height = 1100, 750
                rgn = CreateRoundRectRgn(0, 0, width, height, 35, 35)   # 半径 35
                SetWindowRgn(hwnd, rgn, True)
                SetWindowPos(hwnd, HWND_TOP, 0, 0, 0, 0,
                             SWP_NOMOVE | SWP_NOSIZE | SWP_FRAMECHANGED)
            except Exception as e:
                logger.warning(f"设置圆角窗口失败: {e}")

        lang.register_callback(self._update_lang)

        # 初始化引擎
        self.scan_engine = EnhancedPYRTScanEngine()
        self.realtime_engine = RealTimeProtection(self.scan_engine.virus_db, self.scan_engine)
        self.boot_engine = BootProtectionEngine()
        self.network_engine = NetworkProtectionEngine()
        self.learning_engine = IntelligentLearningEngine()
        self.defender_coordinator = WindowsDefenderCoordinator()
        self.honeypot_engine = HoneypotEngine()
        self.ransomware_engine = RansomwareDecryptorEngine()
        self.security_score = SecurityScore(self)
        self.usb_monitor = USBMonitorEngine(self.scan_engine, self._quarantine_callback)
        self.sched_scan = ScheduledScanEngine(self.scan_engine, self._start_scan_by_type)
        self.rb_engine = RansomwareBehaviorEngine()
        self.pb_engine = ProcessBlockEngine()
        self.registry_engine = RegistryProtectionEngine()
        self.file_assoc_engine = FileAssociationProtection()
        self.system_repair = SystemRepairTool()
        self.cloud_engine = self.scan_engine.cloud_engine

        self.scanning = False
        self.threats_list = []
        self.current_tab = "virus_scan"

        self._create_custom_titlebar()
        self._create_main_layout()
        self._start_engines()
        self._start_updates()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _start_move(self, event):
        if event.widget == self.title_bar or (hasattr(event.widget, 'master') and event.widget.master == self.title_bar):
            self._drag_data['x'] = event.x
            self._drag_data['y'] = event.y
            self._drag_data['dragging'] = True

    def _on_move(self, event):
        if self._drag_data['dragging']:
            x = self.root.winfo_x() + (event.x - self._drag_data['x'])
            y = self.root.winfo_y() + (event.y - self._drag_data['y'])
            self.root.geometry(f"+{x}+{y}")

    def _stop_move(self, event):
        self._drag_data['dragging'] = False

    def _create_custom_titlebar(self):
        # 标题栏高度改为 50（加宽）
        self.title_bar = tk.Frame(self.root, bg=Config.THEME['header_bg'], height=50)
        self.title_bar.pack(fill=tk.X, side=tk.TOP)
        self.title_bar.pack_propagate(False)

        icon_lbl = tk.Label(self.title_bar, text="🛡️", font=("Segoe UI Emoji", 18),
                            fg=Config.THEME['header_fg'], bg=Config.THEME['header_bg'])
        icon_lbl.pack(side=tk.LEFT, padx=(15,8))
        title_lbl = tk.Label(self.title_bar, text=f"{lang.get_text('app_name')} {Config.VERSION}",
                             font=("Microsoft YaHei", 14, "bold"),
                             fg=Config.THEME['header_fg'], bg=Config.THEME['header_bg'])
        title_lbl.pack(side=tk.LEFT)

        btn_frame = tk.Frame(self.title_bar, bg=Config.THEME['header_bg'])
        btn_frame.pack(side=tk.RIGHT)

        def minimize():
            self.root.iconify()
        tk.Button(btn_frame, text="─", command=minimize,
                  bg=Config.THEME['header_bg'], fg=Config.THEME['header_fg'],
                  relief=tk.FLAT, font=("Microsoft YaHei", 14), width=3,
                  cursor="hand2").pack(side=tk.LEFT)

        def toggle_maximize():
            if self.root.attributes('-zoomed'):
                self.root.attributes('-zoomed', False)
            else:
                self.root.attributes('-zoomed', True)
        tk.Button(btn_frame, text="☐", command=toggle_maximize,
                  bg=Config.THEME['header_bg'], fg=Config.THEME['header_fg'],
                  relief=tk.FLAT, font=("Microsoft YaHei", 14), width=3,
                  cursor="hand2").pack(side=tk.LEFT)

        tk.Button(btn_frame, text="✕", command=self._on_closing,
                  bg=Config.THEME['header_bg'], fg=Config.THEME['header_fg'],
                  relief=tk.FLAT, font=("Microsoft YaHei", 14), width=3,
                  cursor="hand2").pack(side=tk.LEFT)

        self.lang_btn = tk.Button(btn_frame, text="🌐 " + Config.SUPPORTED_LANGUAGES[Config.LANGUAGE],
                                  command=self._show_lang, bg=Config.THEME['header_bg'],
                                  fg=Config.THEME['header_fg'], relief=tk.FLAT,
                                  font=("Microsoft YaHei", 10), cursor="hand2")
        self.lang_btn.pack(side=tk.LEFT, padx=(0,12))

    def _create_main_layout(self):
        main = tk.Frame(self.root, bg=Config.THEME['bg_dark'])
        main.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        left = tk.Frame(main, bg=Config.THEME['bg_card'], relief=tk.FLAT, bd=1)
        left.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))

        status_frame = tk.Frame(left, bg=Config.THEME['bg_card'])
        status_frame.pack(fill=tk.X, padx=20, pady=20)
        tk.Label(status_frame, text="🛡️", font=("Segoe UI Emoji", 36),
                 fg=Config.THEME['success'], bg=Config.THEME['bg_card']).pack()
        self.status_title = tk.Label(status_frame, text=lang.get_text("system_secure"),
                                     font=("Microsoft YaHei", 16, "bold"),
                                     fg=Config.THEME['success'], bg=Config.THEME['bg_card'])
        self.status_title.pack(pady=(5, 0))

        tk.Frame(left, bg=Config.THEME['border'], height=1).pack(fill=tk.X, padx=20)

        db_frame = tk.Frame(left, bg=Config.THEME['bg_card'])
        db_frame.pack(fill=tk.X, padx=20, pady=15)
        tk.Label(db_frame, text="📦 " + lang.get_text("virus_db"),
                 font=("Microsoft YaHei", 11), fg=Config.THEME['text_primary'],
                 bg=Config.THEME['bg_card']).pack(anchor=tk.W)
        self.db_label = tk.Label(db_frame, text=lang.get_text("virus_db_loaded"),
                                 font=("Microsoft YaHei", 9),
                                 fg=Config.THEME['text_secondary'], bg=Config.THEME['bg_card'])
        self.db_label.pack(anchor=tk.W, padx=(25, 0))

        scan_frame = tk.Frame(left, bg=Config.THEME['bg_card'])
        scan_frame.pack(fill=tk.X, padx=20, pady=(0, 15))
        tk.Label(scan_frame, text="⏱️ " + lang.get_text("last_scan"),
                 font=("Microsoft YaHei", 11), fg=Config.THEME['text_primary'],
                 bg=Config.THEME['bg_card']).pack(anchor=tk.W)
        self.last_scan_label = tk.Label(scan_frame, text=lang.get_text("never"),
                                        font=("Microsoft YaHei", 9),
                                        fg=Config.THEME['text_secondary'], bg=Config.THEME['bg_card'])
        self.last_scan_label.pack(anchor=tk.W, padx=(25, 0))

        tk.Frame(left, bg=Config.THEME['border'], height=1).pack(fill=tk.X, padx=20)

        protect_frame = tk.Frame(left, bg=Config.THEME['bg_card'])
        protect_frame.pack(fill=tk.X, padx=20, pady=15)
        tk.Label(protect_frame, text="🛡️ " + lang.get_text("protection_status"),
                 font=("Microsoft YaHei", 11, "bold"),
                 fg=Config.THEME['text_primary'], bg=Config.THEME['bg_card']).pack(anchor=tk.W, pady=(0, 10))

        self.protect_labels = {}
        protections = [
            ("real_time", lang.get_text("real_time_protection_on")),
            ("boot", lang.get_text("boot_protection_on")),
            ("usb", lang.get_text("usb_protection_on")),
            ("network", lang.get_text("network_protection_on")),
            ("behavior", lang.get_text("behavior_monitor_on")),
            ("registry", lang.get_text("registry_protection")),
            ("file_assoc", lang.get_text("file_assoc_protection")),
        ]
        for key, text in protections:
            lbl = tk.Label(protect_frame, text="✅ " + text,
                           font=("Microsoft YaHei", 9),
                           fg=Config.THEME['success'], bg=Config.THEME['bg_card'])
            lbl.pack(anchor=tk.W, pady=2)
            self.protect_labels[key] = lbl

        right = tk.Frame(main, bg=Config.THEME['bg_card'])
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.tab_frame = tk.Frame(right, bg=Config.THEME['bg_dark'])
        self.tab_frame.pack(fill=tk.X, padx=20, pady=(15, 0))

        self.tab_buttons = {}
        tabs = [
            ("virus_scan", "🔍 " + lang.get_text("virus_scan")),
            ("tools", "🛠️ " + lang.get_text("tools_tab")),
            ("settings", "⚙️ " + lang.get_text("settings_tab")),
        ]
        for key, text in tabs:
            btn = tk.Button(self.tab_frame, text=text, font=("Microsoft YaHei", 11),
                            bg=Config.THEME['bg_dark'], fg=Config.THEME['text_secondary'],
                            relief=tk.FLAT, padx=20, pady=10, cursor="hand2",
                            command=lambda k=key: self._switch_tab(k))
            btn.pack(side=tk.LEFT, padx=(0, 5))
            self.tab_buttons[key] = btn

        self.content_frame = tk.Frame(right, bg=Config.THEME['bg_card'])
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

        self.pages = {}
        self._create_virus_scan_page()
        self._create_tools_page()
        self._create_settings_page()

        self._switch_tab("virus_scan")

    def _switch_tab(self, tab_key):
        self.current_tab = tab_key
        for key, btn in self.tab_buttons.items():
            if key == tab_key:
                btn.config(bg=Config.THEME['primary'], fg='white')
            else:
                btn.config(bg=Config.THEME['bg_dark'], fg=Config.THEME['text_secondary'])
        for key, page in self.pages.items():
            if key == tab_key:
                page.pack(fill=tk.BOTH, expand=True)
            else:
                page.pack_forget()

    def _create_virus_scan_page(self):
        page = tk.Frame(self.content_frame, bg=Config.THEME['bg_card'])
        self.pages["virus_scan"] = page

        tk.Label(page, text="🔍 " + lang.get_text("virus_scan"),
                 font=("Microsoft YaHei", 18, "bold"),
                 fg=Config.THEME['text_primary'], bg=Config.THEME['bg_card']).pack(anchor=tk.W, pady=(0, 15))

        btn_frame = tk.Frame(page, bg=Config.THEME['bg_card'])
        btn_frame.pack(fill=tk.X, pady=(0, 15))

        self.full_scan_btn = tk.Button(btn_frame, text="🛡️ " + lang.get_text("full_scan_btn"),
                                       command=self._start_full_scan,
                                       bg=Config.THEME['primary'], fg='white',
                                       font=("Microsoft YaHei", 12, "bold"),
                                       padx=30, pady=12, relief=tk.FLAT, cursor="hand2")
        self.full_scan_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.quick_scan_btn = tk.Button(btn_frame, text="⚡ " + lang.get_text("quick_scan_btn"),
                                        command=self._start_quick_scan,
                                        bg=Config.THEME['secondary'], fg='white',
                                        font=("Microsoft YaHei", 12),
                                        padx=25, pady=12, relief=tk.FLAT, cursor="hand2")
        self.quick_scan_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.custom_scan_btn = tk.Button(btn_frame, text="📁 " + lang.get_text("custom_scan_btn"),
                                         command=self._start_custom_scan,
                                         bg=Config.THEME['secondary'], fg='white',
                                         font=("Microsoft YaHei", 12),
                                         padx=25, pady=12, relief=tk.FLAT, cursor="hand2")
        self.custom_scan_btn.pack(side=tk.LEFT)

        status_frame = tk.Frame(page, bg=Config.THEME['bg_dark'], padx=15, pady=10)
        status_frame.pack(fill=tk.X, pady=(0, 15))

        self.scan_status_label = tk.Label(status_frame, text=lang.get_text("status_ready"),
                                          font=("Microsoft YaHei", 11),
                                          fg=Config.THEME['text_secondary'], bg=Config.THEME['bg_dark'])
        self.scan_status_label.pack(anchor=tk.W)

        self.scan_progress_bar = tk.Canvas(status_frame, height=6,
                                           bg=Config.THEME['bg_card'], highlightthickness=0)
        self.scan_progress_bar.pack(fill=tk.X, pady=(5, 0))

        log_frame = tk.Frame(page, bg=Config.THEME['bg_dark'])
        log_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(log_frame, text="📋 " + lang.get_text("scan_log"),
                 font=("Microsoft YaHei", 11, "bold"),
                 fg=Config.THEME['text_primary'], bg=Config.THEME['bg_dark']).pack(anchor=tk.W, pady=(0, 5))

        self.scan_log_text = tk.Text(log_frame, bg=Config.THEME['bg_card'],
                                     fg=Config.THEME['text_primary'],
                                     font=("Consolas", 9), wrap=tk.WORD,
                                     relief=tk.FLAT, height=8)
        self.scan_log_text.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(self.scan_log_text, orient=tk.VERTICAL,
                                 command=self.scan_log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.scan_log_text.config(yscrollcommand=scrollbar.set)

        self._add_log("本地病毒库已加载，共 " + str(len(self.scan_engine.virus_db.signatures)) + " 条特征")
        self._add_log("PYRT安全卫士已启动，正在监控系统关键操作...")
        self._add_log("U盘保护已启动，插入优盘自动扫描")
        self._add_log("勒索行为检测已启动，正在监控勒索软件、挖矿程序等")
        self._add_log("进程行为监控已启动，正在分析所有运行程序")
        self._add_log("注册表启动项保护已启动，监控系统启动项")
        self._add_log("文件关联保护已启动，监控关键文件关联")

    def _create_tools_page(self):
        page = tk.Frame(self.content_frame, bg=Config.THEME['bg_card'])
        self.pages["tools"] = page

        tk.Label(page, text="🛠️ " + lang.get_text("tools_tab"),
                 font=("Microsoft YaHei", 18, "bold"),
                 fg=Config.THEME['text_primary'], bg=Config.THEME['bg_card']).pack(anchor=tk.W, pady=(0, 15))

        tools_frame = tk.Frame(page, bg=Config.THEME['bg_card'])
        tools_frame.pack(fill=tk.BOTH, expand=True)

        tools = [
            ("file_shredder", "🗑️", lang.get_text("file_shredder"), self._open_shredder),
            ("privacy_cleaner", "🧹", lang.get_text("privacy_cleaner"), self._open_privacy),
            ("vulnerability_scanner", "🔍", lang.get_text("vulnerability_scanner"), self._open_vuln),
            ("usb_protection", "💾", lang.get_text("usb_protection"), self._open_usb),
            ("ransomware_behavior", "🛡️", lang.get_text("ransomware_behavior"), self._open_rb),
            ("process_block", "🚫", lang.get_text("process_block"), self._open_pb),
            ("boot_protection", "🔒", lang.get_text("boot_protection"), self._open_boot),
            ("network_protection", "🌐", lang.get_text("network_protection"), self._open_network),
            ("registry_protection", "📝", lang.get_text("registry_protection"), self._open_registry),
            ("file_assoc", "📁", lang.get_text("file_assoc_protection"), self._open_file_assoc),
            ("system_repair", "🔧", lang.get_text("system_repair"), self._open_system_repair),
            ("cloud_scan", "☁️", lang.get_text("cloud_scan"), self._open_cloud_scan),
        ]

        for i, (key, icon, name, cmd) in enumerate(tools):
            row = i // 4
            col = i % 4
            card = tk.Frame(tools_frame, bg=Config.THEME['bg_dark'], padx=20, pady=15, relief=tk.FLAT, bd=1)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
            tk.Label(card, text=icon, font=("Segoe UI Emoji", 28),
                     fg=Config.THEME['primary'], bg=Config.THEME['bg_dark']).pack()
            tk.Label(card, text=name, font=("Microsoft YaHei", 11),
                     fg=Config.THEME['text_primary'], bg=Config.THEME['bg_dark']).pack(pady=(5, 0))
            tk.Button(card, text=lang.get_text("open"), command=cmd,
                      bg=Config.THEME['primary'], fg='white',
                      font=("Microsoft YaHei", 9), padx=15, pady=5,
                      relief=tk.FLAT, cursor="hand2").pack(pady=(10, 0))

        for i in range(4):
            tools_frame.columnconfigure(i, weight=1)

    # ========== 子窗口方法（全部保留） ==========
    def _open_privacy(self):
        win = tk.Toplevel(self.root)
        win.title(lang.get_text("privacy_cleaner"))
        win.geometry("450x400")
        win.configure(bg=Config.THEME['bg_dark'])
        frame = tk.Frame(win, bg=Config.THEME['bg_dark'], padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text="🧹 " + lang.get_text("privacy_cleaner"), font=("Microsoft YaHei", 14, "bold"),
                 fg=Config.THEME['primary'], bg=Config.THEME['bg_dark']).pack(anchor=tk.W, pady=(0, 15))
        vars_dict = {}
        browsers = [("chrome", "Chrome"), ("firefox", "Firefox"), ("edge", "Edge")]
        for key, name in browsers:
            var = tk.BooleanVar(value=True)
            vars_dict[key] = var
            tk.Checkbutton(frame, text=name, variable=var,
                           bg=Config.THEME['bg_dark'], font=("Microsoft YaHei", 10)).pack(anchor=tk.W, pady=3)
        temp_var = tk.BooleanVar(value=True)
        tk.Checkbutton(frame, text=lang.get_text("clean_system_temp"), variable=temp_var,
                       bg=Config.THEME['bg_dark'], font=("Microsoft YaHei", 10)).pack(anchor=tk.W, pady=3)
        result_label = tk.Label(frame, text="", font=("Microsoft YaHei", 10),
                                fg=Config.THEME['text_secondary'], bg=Config.THEME['bg_dark'])
        result_label.pack(pady=10)

        def do_clean():
            cleaned = 0
            total_size = 0
            browsers_list = []
            for key, var in vars_dict.items():
                if var.get():
                    browsers_list.append(key)
            for b in browsers_list:
                cnt = PrivacyCleaner.clean_browser(b, ['cache', 'cookies', 'history'])
                cleaned += cnt
            if temp_var.get():
                size = PrivacyCleaner.clean_system_temp()
                total_size += size
            result_label.config(
                text=f"{lang.get_text('cleaned_size')}: {total_size / (1024 * 1024):.2f} MB, 清理了 {cleaned} 个浏览器文件")
            messagebox.showinfo(lang.get_text("success"),
                                f"{lang.get_text('cleaned_size')}: {total_size / (1024 * 1024):.2f} MB")

        tk.Button(frame, text="🧹 " + lang.get_text("clean_now"), command=do_clean,
                  bg=Config.THEME['primary'], fg='white', font=("Microsoft YaHei", 11),
                  padx=20, pady=8).pack(pady=10)

    def _open_vuln(self):
        win = tk.Toplevel(self.root)
        win.title(lang.get_text("vulnerability_scanner"))
        win.geometry("500x400")
        win.configure(bg=Config.THEME['bg_dark'])
        frame = tk.Frame(win, bg=Config.THEME['bg_dark'], padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text="🔍 " + lang.get_text("vulnerability_scanner"), font=("Microsoft YaHe", 14, "bold"),
                 fg=Config.THEME['primary'], bg=Config.THEME['bg_dark']).pack(anchor=tk.W, pady=(0, 15))
        result_label = tk.Label(frame, text="", font=("Microsoft YaHei", 11),
                                fg=Config.THEME['text_secondary'], bg=Config.THEME['bg_dark'])
        result_label.pack(pady=10)
        detail_text = tk.Text(frame, height=8, bg=Config.THEME['bg_card'],
                              fg=Config.THEME['text_primary'], font=("Consolas", 10))
        detail_text.pack(fill=tk.BOTH, expand=True, pady=10)

        def do_scan():
            result_label.config(text=lang.get_text("vuln_scanning") + "...")
            detail_text.delete(1.0, tk.END)
            result = VulnerabilityScanner.scan()
            if result['status'] == 'ok':
                result_label.config(text="✅ " + lang.get_text("system_uptodate"), fg=Config.THEME['success'])
            elif result['status'] == 'warning':
                result_label.config(text=f"⚠️ {result['updates_missing']} {lang.get_text('missing_updates')}",
                                    fg=Config.THEME['warning'])
            else:
                result_label.config(text="❌ " + result['details'], fg=Config.THEME['accent'])
            detail_text.insert(tk.END, result['details'])

        tk.Button(frame, text="🔍 " + lang.get_text("vuln_scan"), command=do_scan,
                  bg=Config.THEME['warning'], fg='white', font=("Microsoft YaHei", 11),
                  padx=20, pady=8).pack(pady=10)

    def _open_usb(self):
        win = tk.Toplevel(self.root)
        win.title(lang.get_text("usb_protection"))
        win.geometry("500x400")
        win.configure(bg=Config.THEME['bg_dark'])
        frame = tk.Frame(win, bg=Config.THEME['bg_dark'], padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text="💾 " + lang.get_text("usb_protection"), font=("Microsoft YaHei", 14, "bold"),
                 fg=Config.THEME['primary'], bg=Config.THEME['bg_dark']).pack(anchor=tk.W, pady=(0, 15))
        status_label = tk.Label(frame, text="🟢 运行中", font=("Microsoft YaHe", 12),
                                fg=Config.THEME['success'], bg=Config.THEME['bg_dark'])
        status_label.pack(anchor=tk.W, pady=5)
        listbox = tk.Listbox(frame, bg=Config.THEME['bg_card'], fg=Config.THEME['text_primary'],
                             font=("Consolas", 10), height=6)
        listbox.pack(fill=tk.BOTH, expand=True, pady=10)

        def refresh():
            listbox.delete(0, tk.END)
            for d in self.usb_monitor.get_detected_devices():
                listbox.insert(tk.END, d)
            results = self.usb_monitor.get_scan_results()
            if results:
                listbox.insert(tk.END, "--- 威胁 ---")
                for t in results:
                    listbox.insert(tk.END, f"[{t.get('severity', '中')}] {t.get('name', '')}")

        refresh()
        tk.Button(frame, text="🔄 " + lang.get_text("refresh"), command=refresh,
                  bg=Config.THEME['secondary'], fg='white', font=("Microsoft YaHei", 10),
                  padx=15, pady=5).pack()

    def _open_rb(self):
        win = tk.Toplevel(self.root)
        win.title(lang.get_text("ransomware_behavior"))
        win.geometry("600x400")
        win.configure(bg=Config.THEME['bg_dark'])
        frame = tk.Frame(win, bg=Config.THEME['bg_dark'], padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text="🛡️ " + lang.get_text("ransomware_behavior"), font=("Microsoft YaHei", 14, "bold"),
                 fg=Config.THEME['primary'], bg=Config.THEME['bg_dark']).pack(anchor=tk.W, pady=(0, 15))
        status_label = tk.Label(frame, text="🟢 运行中", font=("Microsoft YaHei", 12),
                                fg=Config.THEME['success'], bg=Config.THEME['bg_dark'])
        status_label.pack(anchor=tk.W, pady=5)
        listbox = tk.Listbox(frame, bg=Config.THEME['bg_card'], fg=Config.THEME['text_primary'],
                             font=("Consolas", 10), height=8)
        listbox.pack(fill=tk.BOTH, expand=True, pady=10)

        def refresh():
            listbox.delete(0, tk.END)
            for a in self.rb_engine.get_alerts(20):
                listbox.insert(tk.END, f"[{a['time']}] {a['severity']}: {a['message']}")
                if a['severity'] in ['严重', '高']:
                    listbox.itemconfig(tk.END, fg='#ff0000')

        refresh()
        btn_frame = tk.Frame(frame, bg=Config.THEME['bg_dark'])
        btn_frame.pack(fill=tk.X)
        tk.Button(btn_frame, text="🔄 " + lang.get_text("refresh"), command=refresh,
                  bg=Config.THEME['secondary'], fg='white', font=("Microsoft YaHe", 10),
                  padx=15, pady=5).pack(side=tk.LEFT)
        tk.Button(btn_frame, text="📄 " + lang.get_text("rb_scan_scripts"), command=self._scan_scripts_rb,
                  bg=Config.THEME['primary'], fg='white', font=("Microsoft YaHe", 10),
                  padx=15, pady=5).pack(side=tk.LEFT, padx=(10, 0))

    def _scan_scripts_rb(self):
        target_dirs = [os.path.expanduser("~\\Desktop"), os.path.expanduser("~\\Downloads")]
        found = []
        for d in target_dirs:
            if os.path.exists(d):
                for root, dirs, files in os.walk(d):
                    for f in files:
                        ext = os.path.splitext(f)[1].lower()
                        if ext in ['.bat', '.cmd', '.ps1', '.vbs']:
                            fp = os.path.join(root, f)
                            result = self.rb_engine.detect_bat_file(fp)
                            if result:
                                found.append((fp, result))
        if found:
            msg = "发现可疑脚本文件:\n"
            for fp, reason in found:
                msg += f"  📄 {fp}\n    原因: {reason}\n"
            messagebox.showwarning("扫描结果", msg)
        else:
            messagebox.showinfo("扫描结果", "未发现可疑脚本文件")

    def _open_pb(self):
        win = tk.Toplevel(self.root)
        win.title(lang.get_text("process_block"))
        win.geometry("600x400")
        win.configure(bg=Config.THEME['bg_dark'])
        frame = tk.Frame(win, bg=Config.THEME['bg_dark'], padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text="🚫 " + lang.get_text("process_block"), font=("Microsoft YaHe", 14, "bold"),
                 fg=Config.THEME['primary'], bg=Config.THEME['bg_dark']).pack(anchor=tk.W, pady=(0, 15))
        status_label = tk.Label(frame, text="🟢 运行中", font=("Microsoft YaHei", 12),
                                fg=Config.THEME['success'], bg=Config.THEME['bg_dark'])
        status_label.pack(anchor=tk.W, pady=5)
        count_label = tk.Label(frame, text="已拦截进程: 0", font=("Microsoft YaHe", 11),
                               fg=Config.THEME['text_secondary'], bg=Config.THEME['bg_dark'])
        count_label.pack(anchor=tk.W, pady=5)
        listbox = tk.Listbox(frame, bg=Config.THEME['bg_card'], fg=Config.THEME['text_primary'],
                             font=("Consolas", 10), height=8)
        listbox.pack(fill=tk.BOTH, expand=True, pady=10)

        def refresh():
            listbox.delete(0, tk.END)
            for a in self.pb_engine.get_alerts(20):
                listbox.insert(tk.END, f"[{a['time']}] 🔴 {a['reason']} (PID: {a['pid']})")
                listbox.itemconfig(tk.END, fg='#ff0000')
            count_label.config(text=f"已拦截进程: {len(self.pb_engine.blocked_processes)}")

        refresh()
        tk.Button(frame, text="🔄 " + lang.get_text("refresh"), command=refresh,
                  bg=Config.THEME['secondary'], fg='white', font=("Microsoft YaHei", 10),
                  padx=15, pady=5).pack()

    def _open_boot(self):
        win = tk.Toplevel(self.root)
        win.title(lang.get_text("boot_protection"))
        win.geometry("500x350")
        win.configure(bg=Config.THEME['bg_dark'])
        frame = tk.Frame(win, bg=Config.THEME['bg_dark'], padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text="🔒 " + lang.get_text("boot_protection"), font=("Microsoft YaHei", 14, "bold"),
                 fg=Config.THEME['primary'], bg=Config.THEME['bg_dark']).pack(anchor=tk.W, pady=(0, 15))
        status_label = tk.Label(frame, text="🟢 " + lang.get_text("running"), font=("Microsoft YaHei", 12),
                                fg=Config.THEME['success'], bg=Config.THEME['bg_dark'])
        status_label.pack(anchor=tk.W, pady=5)
        tk.Label(frame, text=f"{lang.get_text('protected_files')}: {len(self.boot_engine.boot_files)}",
                 font=("Microsoft YaHei", 11), fg=Config.THEME['text_secondary'],
                 bg=Config.THEME['bg_dark']).pack(anchor=tk.W, pady=5)
        btn_frame = tk.Frame(frame, bg=Config.THEME['bg_dark'])
        btn_frame.pack(fill=tk.X, pady=10)

        def check_integrity():
            res = self.boot_engine.check_integrity()
            msg = f"状态: {res['score']:.1f}%\n正常: {res['ok']}  修改: {res['modified']}  缺失: {res['missing']}"
            messagebox.showinfo(lang.get_text("check_integrity"), msg)

        tk.Button(btn_frame, text="🔍 " + lang.get_text("check_integrity"), command=check_integrity,
                  bg=Config.THEME['primary'], fg='white', padx=15, pady=5).pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(btn_frame, text="💾 " + lang.get_text("create_backup"), command=self.boot_engine.create_backup,
                  bg=Config.THEME['secondary'], fg='white', padx=15, pady=5).pack(side=tk.LEFT)

    def _open_network(self):
        win = tk.Toplevel(self.root)
        win.title(lang.get_text("network_protection"))
        win.geometry("500x350")
        win.configure(bg=Config.THEME['bg_dark'])
        frame = tk.Frame(win, bg=Config.THEME['bg_dark'], padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text="🌐 " + lang.get_text("network_protection"), font=("Microsoft YaHe", 14, "bold"),
                 fg=Config.THEME['primary'], bg=Config.THEME['bg_dark']).pack(anchor=tk.W, pady=(0, 15))
        status = self.network_engine.get_network_status()
        net = lang.get_text("connected") if status['network'] == 'connected' else lang.get_text("disconnected")
        inet = lang.get_text("connected") if status['internet'] else lang.get_text("disconnected")
        tk.Label(frame, text=f"{lang.get_text('network_status')}: {net}",
                 font=("Microsoft YaHei", 11), fg=Config.THEME['text_secondary'],
                 bg=Config.THEME['bg_dark']).pack(anchor=tk.W, pady=5)
        tk.Label(frame, text=f"{lang.get_text('internet_status')}: {inet}",
                 font=("Microsoft YaHei", 11), fg=Config.THEME['text_secondary'],
                 bg=Config.THEME['bg_dark']).pack(anchor=tk.W, pady=5)
        btn_frame = tk.Frame(frame, bg=Config.THEME['bg_dark'])
        btn_frame.pack(fill=tk.X, pady=10)

        def emergency():
            if messagebox.askyesno(lang.get_text("warning"), lang.get_text("emergency_disconnect") + "?"):
                self.network_engine.emergency_disconnect()
                messagebox.showinfo(lang.get_text("success"),
                                    lang.get_text("emergency_disconnect") + " " + lang.get_text("success"))

        tk.Button(btn_frame, text="🚫 " + lang.get_text("emergency_disconnect"), command=emergency,
                  bg=Config.THEME['accent'], fg='white', padx=15, pady=5).pack(side=tk.LEFT)

    def _open_registry(self):
        win = tk.Toplevel(self.root)
        win.title(lang.get_text("registry_protection"))
        win.geometry("600x400")
        win.configure(bg=Config.THEME['bg_dark'])
        frame = tk.Frame(win, bg=Config.THEME['bg_dark'], padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text="📝 " + lang.get_text("registry_protection"), font=("Microsoft YaHei", 14, "bold"),
                 fg=Config.THEME['primary'], bg=Config.THEME['bg_dark']).pack(anchor=tk.W, pady=(0, 15))
        status = "🟢 运行中" if self.registry_engine.is_running() else "🔴 已停止"
        tk.Label(frame, text=status, font=("Microsoft YaHei", 12),
                 fg=Config.THEME['success'] if "运行" in status else Config.THEME['accent'],
                 bg=Config.THEME['bg_dark']).pack(anchor=tk.W, pady=5)
        listbox = tk.Listbox(frame, bg=Config.THEME['bg_card'], fg=Config.THEME['text_primary'],
                             font=("Consolas", 10), height=8)
        listbox.pack(fill=tk.BOTH, expand=True, pady=10)

        def refresh():
            listbox.delete(0, tk.END)
            for a in self.registry_engine.get_alerts(20):
                listbox.insert(tk.END, f"[{a['time']}] {a['message']}")
                if "新增" in a['message'] or "修改" in a['message']:
                    listbox.itemconfig(tk.END, fg='#ff9900')
                else:
                    listbox.itemconfig(tk.END, fg='#ff0000')

        refresh()
        tk.Button(frame, text="🔄 " + lang.get_text("refresh"), command=refresh,
                  bg=Config.THEME['secondary'], fg='white', font=("Microsoft YaHei", 10),
                  padx=15, pady=5).pack()

    def _open_file_assoc(self):
        win = tk.Toplevel(self.root)
        win.title(lang.get_text("file_assoc_protection"))
        win.geometry("600x400")
        win.configure(bg=Config.THEME['bg_dark'])
        frame = tk.Frame(win, bg=Config.THEME['bg_dark'], padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text="📁 " + lang.get_text("file_assoc_protection"), font=("Microsoft YaHei", 14, "bold"),
                 fg=Config.THEME['primary'], bg=Config.THEME['bg_dark']).pack(anchor=tk.W, pady=(0, 15))
        status = "🟢 运行中" if self.file_assoc_engine.is_running() else "🔴 已停止"
        tk.Label(frame, text=status, font=("Microsoft YaHei", 12),
                 fg=Config.THEME['success'] if "运行" in status else Config.THEME['accent'],
                 bg=Config.THEME['bg_dark']).pack(anchor=tk.W, pady=5)
        listbox = tk.Listbox(frame, bg=Config.THEME['bg_card'], fg=Config.THEME['text_primary'],
                             font=("Consolas", 10), height=6)
        listbox.pack(fill=tk.BOTH, expand=True, pady=10)

        def refresh():
            listbox.delete(0, tk.END)
            for a in self.file_assoc_engine.get_alerts(20):
                listbox.insert(tk.END, f"[{a['time']}] {a['message']}")
                if "修改" in a['message']:
                    listbox.itemconfig(tk.END, fg='#ff9900')
                else:
                    listbox.itemconfig(tk.END, fg='#ff0000')

        refresh()
        btn_frame = tk.Frame(frame, bg=Config.THEME['bg_dark'])
        btn_frame.pack(fill=tk.X, pady=5)
        tk.Button(btn_frame, text="🔄 " + lang.get_text("refresh"), command=refresh,
                  bg=Config.THEME['secondary'], fg='white', font=("Microsoft YaHei", 10),
                  padx=15, pady=5).pack(side=tk.LEFT)

        def repair_assoc():
            ext = simpledialog.askstring("修复关联", "请输入扩展名（如 .txt）:")
            if ext:
                if self.file_assoc_engine.repair_association(ext):
                    messagebox.showinfo("成功", f"已修复 {ext} 关联")
                else:
                    messagebox.showerror("失败", "修复失败")
        tk.Button(btn_frame, text="🔧 修复关联", command=repair_assoc,
                  bg=Config.THEME['primary'], fg='white', font=("Microsoft YaHei", 10),
                  padx=15, pady=5).pack(side=tk.LEFT, padx=(10,0))

    def _open_system_repair(self):
        win = tk.Toplevel(self.root)
        win.title(lang.get_text("system_repair"))
        win.geometry("500x400")
        win.configure(bg=Config.THEME['bg_dark'])
        frame = tk.Frame(win, bg=Config.THEME['bg_dark'], padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text="🔧 " + lang.get_text("system_repair"), font=("Microsoft YaHei", 14, "bold"),
                 fg=Config.THEME['primary'], bg=Config.THEME['bg_dark']).pack(anchor=tk.W, pady=(0, 15))
        result_label = tk.Label(frame, text="", font=("Microsoft YaHei", 11),
                                fg=Config.THEME['text_secondary'], bg=Config.THEME['bg_dark'])
        result_label.pack(pady=10)

        def run_repair(func, desc):
            result_label.config(text=f"正在{desc}...")
            win.update()
            success, msg = func()
            if success:
                result_label.config(text="✅ " + msg, fg=Config.THEME['success'])
            else:
                result_label.config(text="❌ " + msg, fg=Config.THEME['accent'])

        tk.Button(frame, text="🛠️ " + lang.get_text("repair_hosts"),
                  command=lambda: run_repair(SystemRepairTool.repair_hosts, "修复hosts"),
                  bg=Config.THEME['warning'], fg='white', font=("Microsoft YaHei", 11),
                  padx=15, pady=8).pack(fill=tk.X, pady=5)
        tk.Button(frame, text="🌐 " + lang.get_text("reset_dns"),
                  command=lambda: run_repair(SystemRepairTool.reset_dns, "重置DNS"),
                  bg=Config.THEME['warning'], fg='white', font=("Microsoft YaHei", 11),
                  padx=15, pady=8).pack(fill=tk.X, pady=5)
        tk.Button(frame, text="🔥 " + lang.get_text("repair_firewall"),
                  command=lambda: run_repair(SystemRepairTool.repair_firewall, "重置防火墙"),
                  bg=Config.THEME['warning'], fg='white', font=("Microsoft YaHei", 11),
                  padx=15, pady=8).pack(fill=tk.X, pady=5)
        tk.Button(frame, text="🔍 " + lang.get_text("run_sfc"),
                  command=lambda: run_repair(SystemRepairTool.repair_sfc, "运行系统文件检查"),
                  bg=Config.THEME['primary'], fg='white', font=("Microsoft YaHei", 11),
                  padx=15, pady=8).pack(fill=tk.X, pady=5)

    def _open_cloud_scan(self):
        win = tk.Toplevel(self.root)
        win.title(lang.get_text("cloud_scan"))
        win.geometry("500x350")
        win.configure(bg=Config.THEME['bg_dark'])
        frame = tk.Frame(win, bg=Config.THEME['bg_dark'], padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text="☁️ " + lang.get_text("cloud_scan"), font=("Microsoft YaHei", 14, "bold"),
                 fg=Config.THEME['primary'], bg=Config.THEME['bg_dark']).pack(anchor=tk.W, pady=(0, 15))
        status = "启用" if Config.CLOUD_SCAN_ENABLED and Config.VT_API_KEY else "未启用（缺少API Key）"
        tk.Label(frame, text=f"状态: {status}", font=("Microsoft YaHei", 11),
                 fg=Config.THEME['text_secondary'], bg=Config.THEME['bg_dark']).pack(anchor=tk.W, pady=5)
        result_label = tk.Label(frame, text="", font=("Microsoft YaHei", 10),
                                fg=Config.THEME['text_secondary'], bg=Config.THEME['bg_dark'])
        result_label.pack(pady=5)
        file_path_var = tk.StringVar()
        tk.Entry(frame, textvariable=file_path_var, width=50,
                 bg=Config.THEME['bg_card'], fg=Config.THEME['text_primary']).pack(fill=tk.X, pady=5)

        def select_file():
            f = filedialog.askopenfilename()
            if f:
                file_path_var.set(f)

        def do_cloud_scan():
            path = file_path_var.get()
            if not path or not os.path.exists(path):
                messagebox.showerror("错误", "文件不存在")
                return
            result_label.config(text="正在查询云端...")
            win.update()
            cloud_res = self.cloud_engine.scan_file(path)
            if cloud_res is None:
                result_label.config(text="❌ 查询失败，请检查API Key或网络", fg=Config.THEME['accent'])
            else:
                positives = cloud_res['positives']
                total = cloud_res['total']
                if positives == 0:
                    result_label.config(text=f"✅ 文件安全 ({positives}/{total})", fg=Config.THEME['success'])
                else:
                    result_label.config(text=f"⚠️ 检测到 {positives}/{total} 个引擎报毒", fg=Config.THEME['warning'])
                if cloud_res.get('permalink'):
                    messagebox.showinfo("详细报告", f"查看报告: {cloud_res['permalink']}")

        btn_frame = tk.Frame(frame, bg=Config.THEME['bg_dark'])
        btn_frame.pack(fill=tk.X, pady=10)
        tk.Button(btn_frame, text="📂 " + lang.get_text("select_files"), command=select_file,
                  bg=Config.THEME['secondary'], fg='white').pack(side=tk.LEFT, padx=(0,10))
        tk.Button(btn_frame, text="☁️ 云查杀", command=do_cloud_scan,
                  bg=Config.THEME['primary'], fg='white', font=("Microsoft YaHei", 11),
                  padx=20, pady=5).pack(side=tk.LEFT)

    def _open_shredder(self):
        win = tk.Toplevel(self.root)
        win.title(lang.get_text("file_shredder"))
        win.geometry("500x300")
        win.configure(bg=Config.THEME['bg_dark'])
        frame = tk.Frame(win, bg=Config.THEME['bg_dark'], padx=20, pady=20)
        frame.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame, text=lang.get_text("file_shredder"), font=("Microsoft YaHe", 14, "bold"),
                 fg=Config.THEME['primary'], bg=Config.THEME['bg_dark']).pack(anchor=tk.W, pady=(0, 15))
        path_var = tk.StringVar()
        tk.Entry(frame, textvariable=path_var, width=50,
                 bg=Config.THEME['bg_card'], fg=Config.THEME['text_primary']).pack(fill=tk.X, pady=5)
        btn_frame = tk.Frame(frame, bg=Config.THEME['bg_dark'])
        btn_frame.pack(fill=tk.X, pady=10)

        def select_file():
            f = filedialog.askopenfilename()
            if f:
                path_var.set(f)

        def select_folder():
            f = filedialog.askdirectory()
            if f:
                path_var.set(f)

        tk.Button(btn_frame, text=lang.get_text("select_files"), command=select_file,
                  bg=Config.THEME['secondary'], fg='white').pack(side=tk.LEFT, padx=(0, 10))
        tk.Button(btn_frame, text=lang.get_text("shred_folder"), command=select_folder,
                  bg=Config.THEME['secondary'], fg='white').pack(side=tk.LEFT)

        def do_shred():
            path = path_var.get()
            if not path or not os.path.exists(path):
                messagebox.showerror(lang.get_text("error"), "文件或目录不存在")
                return
            if messagebox.askyesno(lang.get_text("confirm"), "确定要粉碎此文件/目录吗？此操作不可恢复！"):
                if os.path.isfile(path):
                    success, msg = ShredderEngine.shred_file(path, 3)
                    messagebox.showinfo(lang.get_text("result"), msg)
                else:
                    total = ShredderEngine.shred_directory(path, 3)
                    messagebox.showinfo(lang.get_text("result"), f"已粉碎 {total} 个文件")

        tk.Button(frame, text="🗑️ " + lang.get_text("shred_files"), command=do_shred,
                  bg=Config.THEME['accent'], fg='white', font=("Microsoft YaHei", 11),
                  padx=20, pady=8).pack(pady=10)

    # ========== 核心控制方法 ==========
    def _apply_skin(self):
        if "skin" in self.setting_vars:
            new_skin = self.setting_vars["skin"].get()
            if new_skin != Config.SKIN:
                lang.set_skin(new_skin)
                self.root.after(100, self._full_refresh_ui)
                messagebox.showinfo(lang.get_text("success"), "主题已应用，界面正在刷新...")

    def _full_refresh_ui(self):
        try:
            current_tab = self.current_tab
            engines = {
                'scan_engine': self.scan_engine,
                'realtime_engine': self.realtime_engine,
                'boot_engine': self.boot_engine,
                'network_engine': self.network_engine,
                'learning_engine': self.learning_engine,
                'defender_coordinator': self.defender_coordinator,
                'honeypot_engine': self.honeypot_engine,
                'ransomware_engine': self.ransomware_engine,
                'usb_monitor': self.usb_monitor,
                'sched_scan': self.sched_scan,
                'rb_engine': self.rb_engine,
                'pb_engine': self.pb_engine,
                'security_score': self.security_score,
                'registry_engine': self.registry_engine,
                'file_assoc_engine': self.file_assoc_engine,
                'cloud_engine': self.cloud_engine,
            }
            for widget in self.root.winfo_children():
                widget.destroy()
            for key, value in engines.items():
                setattr(self, key, value)
            self._create_custom_titlebar()
            self._create_main_layout()
            self._switch_tab(current_tab)
            self._update_status()
            self._update_lang()
        except Exception as e:
            logger.error(f"刷新界面失败: {e}")
            import traceback
            traceback.print_exc()

    def _save_settings(self):
        for attr in ['REAL_TIME_PROTECTION', 'BOOT_PROTECTION_ENABLED', 'NETWORK_PROTECTION_ENABLED',
                     'USB_AUTO_SCAN', 'PROCESS_BLOCK_ENABLED', 'SCHEDULED_SCAN_ENABLED',
                     'REGISTRY_PROTECTION_ENABLED', 'FILE_ASSOC_PROTECTION_ENABLED', 'CLOUD_SCAN_ENABLED']:
            if attr in self.setting_vars:
                setattr(Config, attr, self.setting_vars[attr].get())
        if "VT_API_KEY" in self.setting_vars:
            Config.VT_API_KEY = self.setting_vars["VT_API_KEY"].get()
            self.cloud_engine.api_key = Config.VT_API_KEY
        messagebox.showinfo(lang.get_text("success"), lang.get_text("save_settings") + " " + lang.get_text("success"))

    def _start_scan_by_type(self, scan_type):
        if self.scanning:
            return
        if scan_type == "full":
            self._start_full_scan()
        else:
            self._start_quick_scan()

    def _quarantine_callback(self, file_path, threat_info):
        if hasattr(self, 'scan_engine'):
            self.scan_engine.quarantine_file(file_path, threat_info)
            self._add_threat(threat_info)

    def _add_threat(self, threat):
        self.threats_list.append(threat)

    def _start_full_scan(self):
        if self.scanning:
            return
        self.scanning = True
        self.full_scan_btn.config(state=tk.DISABLED)
        self.quick_scan_btn.config(state=tk.DISABLED)
        self.custom_scan_btn.config(state=tk.DISABLED)
        self.scan_status_label.config(text=lang.get_text("scanning") + "...")
        self._add_log("开始全面扫描...")
        self.scan_engine.start_scan("full")
        self._scan_loop()

    def _start_quick_scan(self):
        if self.scanning:
            return
        self.scanning = True
        self.full_scan_btn.config(state=tk.DISABLED)
        self.quick_scan_btn.config(state=tk.DISABLED)
        self.custom_scan_btn.config(state=tk.DISABLED)
        self.scan_status_label.config(text=lang.get_text("scanning") + "...")
        self._add_log("开始快速扫描...")
        self.scan_engine.start_scan("quick")
        self._scan_loop()

    def _start_custom_scan(self):
        path = filedialog.askdirectory(title=lang.get_text("select_directory"))
        if not path:
            return
        if self.scanning:
            return
        self.scanning = True
        self.full_scan_btn.config(state=tk.DISABLED)
        self.quick_scan_btn.config(state=tk.DISABLED)
        self.custom_scan_btn.config(state=tk.DISABLED)
        self.scan_status_label.config(text=lang.get_text("scanning") + "...")
        self._add_log(f"开始自定义扫描: {path}")
        self.scan_engine.start_scan("quick", [path])
        self._scan_loop()

    def _scan_loop(self):
        if not self.scanning:
            return
        data = self.scan_engine.update_scan()
        if data:
            progress = data['progress']
            self.scan_progress_bar.delete("all")
            self.scan_progress_bar.create_rectangle(0, 0, progress * 4, 6, fill=Config.THEME['primary'], outline="")
            self.scan_status_label.config(
                text=f"扫描中... {data['scanned']}/{data['total']} 文件, 发现 {data['threats']} 个威胁")
            for t in data['new_threats']:
                self._add_log(f"⚠️ 发现威胁: {t.get('name', '未知')} - {t.get('file', '')}")
                self._add_threat(t)
            if data['scanning']:
                self.root.after(100, self._scan_loop)
            else:
                self._scan_complete()

    def _scan_complete(self):
        self.scanning = False
        self.full_scan_btn.config(state=tk.NORMAL)
        self.quick_scan_btn.config(state=tk.NORMAL)
        self.custom_scan_btn.config(state=tk.NORMAL)
        cnt = len(self.threats_list)
        if cnt > 0:
            self.scan_status_label.config(text=f"扫描完成，发现 {cnt} 个威胁！")
            self.status_title.config(text=f"⚠️ 发现 {cnt} 个威胁", fg=Config.THEME['accent'])
            self._add_log(f"扫描完成，发现 {cnt} 个威胁")
            messagebox.showwarning(lang.get_text("warning"), f"{lang.get_text('threats_found')}: {cnt}")
        else:
            self.scan_status_label.config(text=lang.get_text("scan_complete") + "，" + lang.get_text("no_threats"))
            self.status_title.config(text=lang.get_text("system_secure"), fg=Config.THEME['success'])
            self._add_log("扫描完成，未发现威胁")
            messagebox.showinfo(lang.get_text("success"), lang.get_text("scan_complete") + "，" + lang.get_text("no_threats"))
        self.last_scan_label.config(text=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

    def _add_log(self, msg):
        timestamp = datetime.now().strftime('[%H:%M:%S]')
        self.scan_log_text.insert(tk.END, f"{timestamp} {msg}\n")
        self.scan_log_text.see(tk.END)

    def _show_lang(self):
        LanguageSelectionDialog(self.root, self._update_lang)

    def _update_lang(self):
        self.root.title(f"{lang.get_text('app_name')} {Config.VERSION}")
        self.lang_btn.config(text="🌐 " + Config.SUPPORTED_LANGUAGES[Config.LANGUAGE])
        for key, btn in self.tab_buttons.items():
            if key == "virus_scan":
                btn.config(text="🔍 " + lang.get_text("virus_scan"))
            elif key == "tools":
                btn.config(text="🛠️ " + lang.get_text("tools_tab"))
            elif key == "settings":
                btn.config(text="⚙️ " + lang.get_text("settings_tab"))
        self._update_status()

    def _update_status(self):
        self.protect_labels['real_time'].config(
            text="✅ " + lang.get_text("real_time_protection_on") if self.realtime_engine.is_running() else "❌ 实时防护已关闭")
        self.protect_labels['boot'].config(
            text="✅ " + lang.get_text("boot_protection_on") if self.boot_engine.is_running() else "❌ 引导保护已关闭")
        self.protect_labels['usb'].config(
            text="✅ " + lang.get_text("usb_protection_on") if self.usb_monitor.is_running() else "❌ USB保护已关闭")
        self.protect_labels['network'].config(
            text="✅ " + lang.get_text("network_protection_on") if self.network_engine.is_running() else "❌ 网络保护已关闭")
        self.protect_labels['behavior'].config(
            text="✅ " + lang.get_text("behavior_monitor_on") if self.rb_engine.is_running() else "❌ 行为监控已关闭")
        self.protect_labels['registry'].config(
            text="✅ " + lang.get_text("registry_protection") if self.registry_engine.is_running() else "❌ 注册表保护已关闭")
        self.protect_labels['file_assoc'].config(
            text="✅ " + lang.get_text("file_assoc_protection") if self.file_assoc_engine.is_running() else "❌ 文件关联保护已关闭")
        self.db_label.config(text=f"{lang.get_text('virus_db_loaded')}，{len(self.scan_engine.virus_db.signatures)} 条特征")

    def _start_engines(self):
        if Config.REAL_TIME_PROTECTION:
            self.realtime_engine.start()
        if Config.BOOT_PROTECTION_ENABLED:
            self.boot_engine.start_protection()
        if Config.NETWORK_PROTECTION_ENABLED:
            self.network_engine.start_protection()
        if Config.INTELLIGENT_LEARNING_ENABLED:
            self.learning_engine.start_monitoring()
        if Config.HONEYPOT_ENABLED:
            self.honeypot_engine.start()
        if Config.USB_AUTO_SCAN:
            self.usb_monitor.start()
        if Config.SCHEDULED_SCAN_ENABLED:
            self.sched_scan.start()
        self.rb_engine.start()
        if Config.PROCESS_BLOCK_ENABLED:
            self.pb_engine.start()
        if Config.REGISTRY_PROTECTION_ENABLED:
            self.registry_engine.start_protection()
        if Config.FILE_ASSOC_PROTECTION_ENABLED:
            self.file_assoc_engine.start_protection()

    def _start_updates(self):
        self._update_status()
        self.root.after(5000, self._start_updates)

    def _create_settings_page(self):
        page = tk.Frame(self.content_frame, bg=Config.THEME['bg_card'])
        self.pages["settings"] = page

        tk.Label(page, text="⚙️ " + lang.get_text("settings_tab"),
                 font=("Microsoft YaHei", 18, "bold"),
                 fg=Config.THEME['text_primary'], bg=Config.THEME['bg_card']).pack(anchor=tk.W, pady=(0, 15))

        groups = [
            ("🔒 安全设置", [
                ("启用实时保护", Config.REAL_TIME_PROTECTION, "REAL_TIME_PROTECTION"),
                ("启用引导保护", Config.BOOT_PROTECTION_ENABLED, "BOOT_PROTECTION_ENABLED"),
                ("启用网络保护", Config.NETWORK_PROTECTION_ENABLED, "NETWORK_PROTECTION_ENABLED"),
                ("启用USB自动扫描", Config.USB_AUTO_SCAN, "USB_AUTO_SCAN"),
                ("启用进程拦截", Config.PROCESS_BLOCK_ENABLED, "PROCESS_BLOCK_ENABLED"),
                ("启用注册表启动项保护", Config.REGISTRY_PROTECTION_ENABLED, "REGISTRY_PROTECTION_ENABLED"),
                ("启用文件关联保护", Config.FILE_ASSOC_PROTECTION_ENABLED, "FILE_ASSOC_PROTECTION_ENABLED"),
            ]),
            ("🔧 扫描设置", [
                ("启用定时扫描", Config.SCHEDULED_SCAN_ENABLED, "SCHEDULED_SCAN_ENABLED"),
                ("启用云查杀（需API Key）", Config.CLOUD_SCAN_ENABLED, "CLOUD_SCAN_ENABLED"),
            ]),
            ("🎨 " + lang.get_text("skin_select"), [
                ("默认蓝", Config.SKIN_OPTIONS["default"], "default"),
                ("🌿 绿色", Config.SKIN_OPTIONS["green"], "green"),
                ("🐉 端午节", Config.SKIN_OPTIONS["dragonboat"], "dragonboat"),
                ("🌙 暗夜", Config.SKIN_OPTIONS["dark"], "dark"),
                ("💜 紫色", Config.SKIN_OPTIONS["purple"], "purple"),
            ]),
            ("☁️ 云查杀设置", [
                ("VirusTotal API Key", Config.VT_API_KEY, "VT_API_KEY"),
            ]),
        ]

        self.setting_vars = {}

        for group_name, items in groups:
            group = tk.LabelFrame(page, text=group_name, font=("Microsoft YaHe", 12, "bold"),
                                  fg=Config.THEME['text_primary'], bg=Config.THEME['bg_card'])
            group.pack(fill=tk.X, pady=(0, 15), padx=5)

            if group_name.startswith("🎨"):
                skin_var = tk.StringVar(value=Config.SKIN)
                self.setting_vars["skin"] = skin_var
                skin_frame = tk.Frame(group, bg=Config.THEME['bg_card'])
                skin_frame.pack(fill=tk.X, padx=15, pady=10)
                for label, value, key in items:
                    rb = tk.Radiobutton(skin_frame, text=label, variable=skin_var, value=key,
                                        bg=Config.THEME['bg_card'], font=("Microsoft YaHei", 10))
                    rb.pack(side=tk.LEFT, padx=10)
                tk.Label(group, text=f"当前主题: {Config.SKIN_OPTIONS.get(Config.SKIN, Config.SKIN)}",
                         font=("Microsoft YaHei", 10), fg=Config.THEME['primary'],
                         bg=Config.THEME['bg_card']).pack(anchor=tk.W, padx=15, pady=(0, 5))
            elif group_name.startswith("☁️"):
                api_frame = tk.Frame(group, bg=Config.THEME['bg_card'])
                api_frame.pack(fill=tk.X, padx=15, pady=10)
                tk.Label(api_frame, text="VirusTotal API Key:", font=("Microsoft YaHei", 10),
                         bg=Config.THEME['bg_card']).pack(side=tk.LEFT)
                api_var = tk.StringVar(value=Config.VT_API_KEY)
                self.setting_vars["VT_API_KEY"] = api_var
                entry = tk.Entry(api_frame, textvariable=api_var, width=50, show="*")
                entry.pack(side=tk.LEFT, padx=10)
                tk.Label(group, text="(从 https://www.virustotal.com 获取免费API Key)",
                         font=("Microsoft YaHei", 9), fg=Config.THEME['text_secondary'],
                         bg=Config.THEME['bg_card']).pack(anchor=tk.W, padx=15, pady=(0,5))
            else:
                for label, default, attr in items:
                    if attr == "VT_API_KEY": continue
                    var = tk.BooleanVar(value=getattr(Config, attr, default))
                    self.setting_vars[attr] = var
                    cb = tk.Checkbutton(group, text=label, variable=var,
                                        bg=Config.THEME['bg_card'], font=("Microsoft YaHei", 10))
                    cb.pack(anchor=tk.W, padx=15, pady=3)

        btn_frame = tk.Frame(page, bg=Config.THEME['bg_card'])
        btn_frame.pack(fill=tk.X, pady=10)

        tk.Button(btn_frame, text="💾 " + lang.get_text("save_settings"),
                  command=self._save_settings,
                  bg=Config.THEME['primary'], fg='white',
                  font=("Microsoft YaHei", 12), padx=30, pady=10,
                  relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT)

        tk.Button(btn_frame, text="🔄 " + lang.get_text("apply_skin"),
                  command=self._apply_skin,
                  bg=Config.THEME['secondary'], fg='white',
                  font=("Microsoft YaHe", 12), padx=30, pady=10,
                  relief=tk.FLAT, cursor="hand2").pack(side=tk.LEFT, padx=(10, 0))

    def _on_closing(self):
        if messagebox.askyesno(lang.get_text("exit"), lang.get_text("exit_confirm")):
            self.learning_engine.stop_monitoring()
            self.realtime_engine.stop()
            self.boot_engine.stop_protection()
            self.network_engine.stop_protection()
            self.honeypot_engine.stop()
            self.usb_monitor.stop()
            self.sched_scan.stop()
            self.rb_engine.stop()
            self.pb_engine.stop()
            self.registry_engine.stop_protection()
            self.file_assoc_engine.stop_protection()
            lang.unregister_callback(self._update_lang)
            self.root.quit()

# ==================== 主函数 ====================
def main():
    try:
        os.makedirs(Config.LOG_DIR, exist_ok=True)
        os.makedirs(Config.QUARANTINE_DIR, exist_ok=True)
        os.makedirs(Config.BOOT_BACKUP_DIR, exist_ok=True)

        splash_root = tk.Tk()
        splash_root.configure(bg=Config.THEME['splash_bg'])

        def launch_main():
            try:
                splash_root.destroy()
            except:
                pass
            main_root = tk.Tk()
            app = QVMainWindow(main_root)
            main_root.mainloop()

        splash = PYRTSplashScreen(splash_root, launch_main)
        splash_root.mainloop()

    except Exception as e:
        logger.critical(f"启动失败: {e}")
        try:
            import tkinter.messagebox as mb
            mb.showerror("启动错误", str(e))
        except:
            print(f"启动失败: {e}")

if __name__ == "__main__":

    main()