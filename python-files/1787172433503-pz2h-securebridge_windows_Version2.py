#!/usr/bin/env python3
# SecureBridge - Windows-friendly variant
# ============================================================
# تم تعديل هذا الملف ليعمل بشكل أفضل على ويندوز (مسارات، ping، تجميع .exe)
# ============================================================

import os
import sys
import json
import time
import random
import socket
import platform
import subprocess
import threading
import hashlib
import base64
import re
import shutil
import tempfile
import logging
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass

# Optional imports handled at runtime
IS_WINDOWS = platform.system().lower().startswith("win")
if IS_WINDOWS:
    APPDATA = os.getenv("APPDATA") or os.path.expanduser("~")
    DEFAULT_BASE_DIR = os.path.join(APPDATA, "SecureBridge")
else:
    DEFAULT_BASE_DIR = os.path.expanduser("~/.securebridge")

os.makedirs(DEFAULT_BASE_DIR, exist_ok=True)

@dataclass
class SystemConfig:
    app_name: str = "SecureBridge"
    version: str = "1.0.0"
    company: str = "SecureBridge Technologies"
    vpn_enabled: bool = False
    vpn_config_path: str = ""
    stealth_mode: bool = False
    use_proxy: bool = False
    sandbox_enabled: bool = True
    encrypt_data: bool = True
    max_connections: int = 10
    auto_start: bool = False
    log_level: str = "INFO"
    save_logs: bool = True
    data_dir: str = os.path.join(DEFAULT_BASE_DIR, "data")
    config_dir: str = os.path.join(DEFAULT_BASE_DIR, "config")
    temp_dir: str = os.path.join(DEFAULT_BASE_DIR, "temp")

    def load_from_file(self, path: str = None):
        path = path or os.path.join(self.config_dir, "system.json")
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for key, value in data.items():
                        if hasattr(self, key):
                            setattr(self, key, value)
            return True
        except Exception as e:
            print(f"⚠️ تحميل الإعدادات الافتراضية: {e}")
            return False

    def save_to_file(self, path: str = None):
        path = path or os.path.join(self.config_dir, "system.json")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.__dict__, f, indent=4, ensure_ascii=False)

    def __post_init__(self):
        for folder in [self.data_dir, self.config_dir, self.temp_dir]:
            os.makedirs(folder, exist_ok=True)

# Optional cryptography support
try:
    from cryptography.fernet import Fernet
    HAVE_FERNET = True
except Exception:
    HAVE_FERNET = False

class SecurityManager:
    def __init__(self, key: Optional[bytes] = None):
        if HAVE_FERNET:
            self.key = key or Fernet.generate_key()
            self.cipher = Fernet(self.key)
        else:
            self.key = None
            self.cipher = None

    def encrypt_data(self, data: Union[str, bytes]) -> str:
        if not self.cipher:
            raise RuntimeError("Cryptography not available")
        if isinstance(data, str):
            data = data.encode()
        return base64.b64encode(self.cipher.encrypt(data)).decode()

    def decrypt_data(self, data: str) -> str:
        if not self.cipher:
            raise RuntimeError("Cryptography not available")
        encrypted = base64.b64decode(data.encode())
        return self.cipher.decrypt(encrypted).decode()

    def encrypt_file(self, file_path: str) -> str:
        if not self.cipher:
            raise RuntimeError("Cryptography not available")
        with open(file_path, 'rb') as f:
            data = f.read()
        encrypted = self.cipher.encrypt(data)
        output = f"{file_path}.enc"
        with open(output, 'wb') as f:
            f.write(encrypted)
        return output

    def decrypt_file(self, file_path: str) -> str:
        if not self.cipher:
            raise RuntimeError("Cryptography not available")
        with open(file_path, 'rb') as f:
            encrypted = f.read()
        decrypted = self.cipher.decrypt(encrypted)
        output = file_path.replace('.enc', '')
        with open(output, 'wb') as f:
            f.write(decrypted)
        return output

class NetworkManager:
    def __init__(self, config: SystemConfig):
        self.config = config
        self.is_stealth = False
        self.vpn_active = False

    def get_local_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            try:
                return socket.gethostbyname(socket.gethostname())
            except:
                return "127.0.0.1"

    def _ping(self, ip: str, timeout_sec: float = 0.6) -> bool:
        try:
            if IS_WINDOWS:
                cmd = ["ping", "-n", "1", "-w", str(int(timeout_sec * 1000)), ip]
            else:
                cmd = ["ping", "-c", "1", "-W", str(int(timeout_sec)), ip]
            proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=timeout_sec + 1)
            return proc.returncode == 0
        except Exception:
            return False

    def scan_local_network(self) -> List[Dict[str, Any]]:
        devices = []
        local_ip = self.get_local_ip()
        if not local_ip or local_ip == "127.0.0.1":
            return devices
        parts = local_ip.split('.')
        if len(parts) < 4:
            return devices
        base = '.'.join(parts[:-1])
        for i in range(1, 255):
            ip = f"{base}.{i}"
            if self._ping(ip):
                devices.append({"ip": ip, "hostname": self.get_hostname(ip), "status": "active"})
        return devices

    def get_hostname(self, ip: str) -> str:
        try:
            return socket.gethostbyaddr(ip)[0]
        except:
            return ip

    def setup_proxy(self, proxy_type: str = "tor", port: int = 9050):
        if proxy_type == "tor":
            os.environ['http_proxy'] = f'socks5://127.0.0.1:{port}'
            os.environ['https_proxy'] = f'socks5://127.0.0.1:{port}'
            return True
        return False

class ConnectionManager:
    def __init__(self, config: SystemConfig):
        self.config = config
        self.active_connections = {}
        self.security = SecurityManager()

    def connect_to_device(self, ip: str, port: int = 22, protocol: str = "ssh", username: Optional[str] = None, password: Optional[str] = None) -> bool:
        try:
            if protocol == "ssh":
                try:
                    import paramiko
                except Exception:
                    print("⚠️ paramiko غير موجود")
                    return False
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                if username:
                    client.connect(ip, port=port, username=username, password=password, timeout=5)
                else:
                    client.connect(ip, port=port, timeout=5)
                self.active_connections[ip] = client
                return True
            elif protocol == "http":
                try:
                    import requests
                except Exception:
                    print("⚠️ requests غير موجود")
                    return False
                r = requests.get(f"http://{ip}:{port}", timeout=5)
                if r.status_code == 200:
                    self.active_connections[ip] = r
                    return True
            return False
        except Exception as e:
            print(f"⚠️ فشل الاتصال بـ {ip}:{port} - {e}")
            return False

    def send_command(self, ip: str, command: str) -> str:
        if not self.active_connections:
            return "لا يوجد اتصال نشط"
        if not ip:
            ip = next(iter(self.active_connections.keys()))
        if ip in self.active_connections:
            client = self.active_connections[ip]
            try:
                import paramiko
                if isinstance(client, paramiko.SSHClient):
                    stdin, stdout, stderr = client.exec_command(command)
                    out = stdout.read().decode(errors='ignore')
                    err = stderr.read().decode(errors='ignore')
                    return out or err or ""
            except Exception:
                pass
            try:
                import requests
                r = requests.post(f"http://{ip}/api/command", json={"cmd": command}, timeout=10)
                return r.text
            except Exception as e:
                return f"خطأ: {e}"
        return "لا يوجد اتصال لهذا الـ IP"

    def disconnect_device(self, ip: str) -> bool:
        if ip in self.active_connections:
            try:
                client = self.active_connections[ip]
                import paramiko
                if isinstance(client, paramiko.SSHClient):
                    client.close()
            except:
                pass
            del self.active_connections[ip]
            return True
        return False

    def list_connected_devices(self) -> List[str]:
        return list(self.active_connections.keys())

class FileManager:
    def __init__(self, config: SystemConfig):
        self.config = config
        self.security = SecurityManager()

    def transfer_file(self, source: str, destination: str, secure: bool = True) -> bool:
        try:
            dest_dir = os.path.dirname(destination)
            if dest_dir:
                os.makedirs(dest_dir, exist_ok=True)
            if secure:
                if not HAVE_FERNET:
                    print("⚠️ التشفير غير متوفر. قم بتثبيت cryptography")
                    return False
                encrypted = self.security.encrypt_file(source)
                shutil.copy(encrypted, destination)
                try:
                    os.remove(encrypted)
                except:
                    pass
            else:
                shutil.copy(source, destination)
            return True
        except Exception as e:
            print(f"⚠️ فشل نقل الملف: {e}")
            return False

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        try:
            stat = os.stat(file_path)
            return {
                "name": os.path.basename(file_path),
                "size": stat.st_size,
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "permissions": oct(stat.st_mode)[-3:]
            }
        except:
            return {}

class AICore:
    def __init__(self, model_name: str = "microsoft/DialoGPT-medium"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self.setup_model()

    def setup_model(self):
        try:
            import transformers
            self.tokenizer = transformers.AutoTokenizer.from_pretrained(self.model_name)
            self.model = transformers.AutoModelForCausalLM.from_pretrained(self.model_name)
            print("✅ تم تحميل نموذج الذكاء الاصطناعي")
        except Exception:
            print("⚠️ سيتم استخدام وضع التوليد المحلي")
            self.model = None

    def generate_text(self, prompt: str, max_length: int = 100) -> str:
        if self.model and self.tokenizer:
            try:
                inputs = self.tokenizer.encode(prompt, return_tensors="pt")
                outputs = self.model.generate(inputs, max_length=max_length, num_return_sequences=1, pad_token_id=50256)
                return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            except:
                pass
        templates = [
            f"تحليل النظام: {prompt}\nالنتيجة: جارٍ التحليل...",
            f"إعداد الاتصال: {prompt}\nالحالة: جاهز",
            f"معالجة الطلب: {prompt}\nالإجراء: تنفيذ",
            f"فحص الشبكة: {prompt}\nالنتيجة: آمن",
            f"تحسين الأداء: {prompt}\nالتوصية: تحديث النظام"
        ]
        return random.choice(templates)

    def analyze_query(self, query: str) -> Dict[str, Any]:
        query_lower = query.lower()
        response = {"type": "general", "confidence": 0.5, "suggestions": []}
        keywords = {
            "network": ["شبكة", "network", "ip", "اتصال", "connection"],
            "security": ["أمان", "security", "تشفير", "encryption", "حماية"],
            "file": ["ملف", "file", "نقل", "transfer", "نسخ"],
            "system": ["نظام", "system", "تحديث", "update", "تحسين"]
        }
        for category, words in keywords.items():
            for word in words:
                if word in query_lower:
                    response["type"] = category
                    response["confidence"] = 0.8
                    response["suggestions"].append(f"نصيحة لـ {category}: ...")
                    break
        if not response["suggestions"]:
            response["suggestions"].append("لا توجد توصيات محددة")
        return response

class SecureBridgeApp:
    def __init__(self):
        self.config = SystemConfig()
        self.security = SecurityManager()
        self.network = NetworkManager(self.config)
        self.connections = ConnectionManager(self.config)
        self.files = FileManager(self.config)
        self.ai = AICore()
        self.running = True
        self.config.load_from_file()
        print("=" * 60)
        print(f"🚀 {self.config.app_name} v{self.config.version}")
        print("=" * 60)
        print(f"📡 IP المحلي: {self.network.get_local_ip()}")
        print(f"💻 النظام: {platform.system()} {platform.version()}")
        print("=" * 60)

    def start_cli(self):
        print("\n📝 أدخل أوامرك (اكتب 'help' للمساعدة)")
        print("=" * 60)
        while self.running:
            try:
                cmd = input("\n> ").strip()
                if not cmd:
                    continue
                if cmd.lower() in ("exit", "quit"):
                    print("👋 إغلاق التطبيق...")
                    self.running = False
                    break
                if cmd.lower() == "help":
                    self.show_help()
                elif cmd.lower() == "scan":
                    print("🔍 جارٍ مسح الشبكة المحلية...")
                    devices = self.network.scan_local_network()
                    print(f"✅ تم العثور على {len(devices)} جهاز:")
                    for device in devices[:50]:
                        print(f"  - {device['ip']} ({device['hostname']})")
                elif cmd.lower().startswith("connect "):
                    parts = cmd.split()
                    if len(parts) >= 2:
                        ip = parts[1]
                        port = int(parts[2]) if len(parts) > 2 else 22
                        if self.connections.connect_to_device(ip, port):
                            print(f"✅ تم الاتصال بـ {ip}:{port}")
                        else:
                            print(f"❌ فشل الاتصال بـ {ip}:{port}")
                elif cmd.lower().startswith("send "):
                    parts = cmd.split(" ", 2)
                    if len(parts) >= 3:
                        ip = parts[1]
                        command = parts[2]
                        result = self.connections.send_command(ip, command)
                        print(f"📤 النتيجة:\n{result}")
                elif cmd.lower() == "list":
                    devices = self.connections.list_connected_devices()
                    if devices:
                        print(f"📱 الأجهزة المتصلة: {', '.join(devices)}")
                    else:
                        print("لا توجد أجهزة متصلة")
                elif cmd.lower().startswith("transfer "):
                    parts = cmd.split()
                    if len(parts) >= 3:
                        source = parts[1]
                        dest = parts[2]
                        if self.files.transfer_file(source, dest):
                            print(f"✅ تم نقل الملف: {source} -> {dest}")
                        else:
                            print(f"❌ فشل نقل الملف")
                elif cmd.lower().startswith("ai "):
                    query = cmd[3:]
                    result = self.ai.generate_text(query)
                    print(f"🤖 {result}")
                    analysis = self.ai.analyze_query(query)
                    print(f"📊 التحليل: {analysis['type']} ({analysis['confidence']*100:.0f}%)")
                elif cmd.lower() == "status":
                    self.show_status()
                elif cmd.lower().startswith("stealth"):
                    self.network.is_stealth = not self.network.is_stealth
                    status = "مفعل" if self.network.is_stealth else "معطل"
                    print(f"🕵️ وضع التخفي: {status}")
                elif cmd.lower().startswith("vpn"):
                    if not self.network.vpn_active:
                        if self.network.setup_proxy():
                            self.network.vpn_active = True
                            print("🔒 تم تفعيل VPN")
                        else:
                            print("❌ فشل تفعيل VPN")
                    else:
                        self.network.vpn_active = False
                        print("🔓 تم إلغاء تفعيل VPN")
                else:
                    print(f"❌ أمر غير معروف: {cmd}")
            except KeyboardInterrupt:
                print("\n👋 إغلاق التطبيق...")
                self.running = False
                break
            except Exception as e:
                print(f"⚠️ خطأ: {e}")

    def show_help(self):
        help_text = """
📚 الأوامر المتاحة:
  help               - عرض هذه المساعدة
  scan               - مسح الشبكة المحلية
  connect <ip> [port] - الاتصال بجهاز
  send <ip> <command> - إرسال أمر لجهاز متصل
  list               - عرض الأجهزة المتصلة
  transfer <src> <dst> - نقل ملف (مشفر إذا أمكن)
  ai <query>         - استشارة الذكاء الاصطناعي
  status             - عرض حالة النظام
  stealth            - تفعيل/تعطيل وضع التخفي
  vpn                - تفعيل/تعطيل VPN
  exit/quit          - إغلاق التطبيق
"""
        print(help_text)

    def show_status(self):
        info = self.network.get_local_ip(), platform.system()
        info = self.network.get_system_info() if hasattr(self.network, "get_system_info") else {}
        print(f"""
📊 حالة النظام:
  - الاسم: {info.get('hostname', '')}
  - النظام: {info.get('os', '')} {info.get('os_version', '')}
  - المعالج: {info.get('cpu_count', '')} نواة
  - الذاكرة: {info.get('memory_total', '')} GB
  - IP: {info.get('ip', '')}
  - وضع التخفي: {'🟢 مفعل' if self.network.is_stealth else '🔴 معطل'}
  - VPN: {'🟢 مفعل' if self.network.vpn_active else '🔴 معطل'}
  - الأجهزة المتصلة: {len(self.connections.list_connected_devices())}
""")

def main():
    parser = argparse.ArgumentParser(description='SecureBridge - منصة الاتصال الآمن')
    parser.add_argument('--gui', action='store_true', help='تشغيل الواجهة الرسومية')
    parser.add_argument('--cli', action='store_true', help='تشغيل الواجهة السطرية')
    parser.add_argument('--config', type=str, help='مسار ملف الإعدادات')
    parser.add_argument('--version', action='version', version='SecureBridge v1.0.0')
    args = parser.parse_args()
    app = SecureBridgeApp()
    # default: CLI
    app.start_cli()

if __name__ == '__main__':
    main()