import os
import sys
import zipfile
import requests
import tempfile
import shutil
import subprocess
import platform
import time
import psutil
import threading
from pathlib import Path

class MinecraftCheatLoader:
    def __init__(self):
        self.temp_dir = None
        self.cheat_dir = None
        self.process = None
        self.monitoring = True
        self.http_debugger_detected = False
        self.ram_options = {
            '1': '512M',
            '2': '1G',
            '3': '2G',
            '4': '3G',
            '5': '4G',
            '6': '6G',
            '7': '8G'
        }
        
    def check_httpdebugger(self):
        """Проверяет наличие процесса HTTPDebuggerUI.exe"""
        while self.monitoring:
            try:
                for proc in psutil.process_iter(['name']):
                    try:
                        if proc.info['name'] and 'HTTPDebuggerUI.exe' in proc.info['name']:
                            self.http_debugger_detected = True
                            self.monitoring = False
                            print("\n⚠ Обнаружен HTTPDebuggerUI.exe! Завершение работы...")
                            return
                    except:
                        pass
            except:
                pass
            time.sleep(1)
    
    def start_monitoring(self):
        """Запускает мониторинг в фоновом режиме"""
        monitor_thread = threading.Thread(target=self.check_httpdebugger, daemon=True)
        monitor_thread.start()
        return monitor_thread
    
    def download_archive(self, url):
        """Скачивает архив по указанному URL"""
        print("Скачивание архива...")
        
        try:
            self.temp_dir = tempfile.mkdtemp()
            archive_path = os.path.join(self.temp_dir, 'archive.zip')
            
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            block_size = 8192
            downloaded = 0
            
            with open(archive_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=block_size):
                    if chunk:
                        file.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"\rПрогресс: {percent:.1f}%", end='')
                        
                        if self.http_debugger_detected:
                            return None
            
            print("\nАрхив успешно скачан!")
            return archive_path
            
        except:
            print("\nНе удалось скачать архив")
            return None
    
    def extract_archive(self, archive_path):
        """Распаковывает архив во временную папку"""
        print("Распаковка архива...")
        
        try:
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(self.temp_dir)
            print("Архив успешно распакован!")
            
            if self.http_debugger_detected:
                return None
            
            items = os.listdir(self.temp_dir)
            
            for item in items:
                item_path = os.path.join(self.temp_dir, item)
                if os.path.isdir(item_path) and item.lower() == 'minecraft':
                    self.cheat_dir = item_path
                    print(f"Найдена папка minecraft")
                    return self.cheat_dir
            
            for item in items:
                item_path = os.path.join(self.temp_dir, item)
                if os.path.isdir(item_path) and item != '__MACOSX':
                    self.cheat_dir = item_path
                    print(f"Найдена папка: {item}")
                    return self.cheat_dir
            
            self.cheat_dir = self.temp_dir
            print("Используется корневая папка")
            return self.cheat_dir
            
        except:
            print("Не удалось распаковать архив")
            return None
    
    def select_ram(self):
        """Позволяет пользователю выбрать количество оперативной памяти"""
        print("\nВыберите количество оперативной памяти:")
        for key, value in self.ram_options.items():
            print(f"{key}. {value}")
        
        while self.monitoring and not self.http_debugger_detected:
            try:
                choice = input("Ваш выбор (1-7): ").strip()
                if choice in self.ram_options:
                    return self.ram_options[choice]
                else:
                    print("Пожалуйста, выберите правильную опцию (1-7)")
            except:
                return None
            
            if self.http_debugger_detected:
                return None
        
        return None
    
    def find_minecraft_process(self):
        """Ищет запущенный процесс Minecraft"""
        minecraft_processes = ['javaw.exe', 'java.exe', 'minecraft.exe', 'Minecraft.exe']
        
        for proc in psutil.process_iter(['name', 'pid']):
            try:
                proc_name = proc.info['name'].lower()
                if any(mc_proc.lower() in proc_name for mc_proc in minecraft_processes):
                    return proc
            except:
                pass
        return None
    
    def wait_for_minecraft_close(self):
        """Ожидает закрытия Minecraft"""
        print("\nОжидание закрытия Minecraft...")
        print("(Папка будет автоматически удалена после закрытия игры)")
        
        minecraft_proc = self.find_minecraft_process()
        
        if minecraft_proc:
            print("Слежу за процессом...")
            
            while self.monitoring and not self.http_debugger_detected:
                try:
                    if not minecraft_proc.is_running():
                        print("\nMinecraft закрыт!")
                        break
                    
                    current_mc = self.find_minecraft_process()
                    if current_mc and current_mc.pid != minecraft_proc.pid:
                        minecraft_proc = current_mc
                    
                    time.sleep(2)
                    
                except:
                    print("\nMinecraft закрыт!")
                    break
        else:
            print("Процесс Minecraft не найден.")
            print("Ожидание 5 секунд перед удалением...")
            time.sleep(5)
    
    def run_cheat(self, cheat_dir, ram_amount):
        """Запускает чит с указанным количеством RAM"""
        
        jar_path = os.path.join(cheat_dir, 'wade.jar')
        
        if not os.path.exists(jar_path):
            jar_files = list(Path(cheat_dir).glob('*.jar'))
            if jar_files:
                jar_path = str(jar_files[0])
            else:
                parent_dir = os.path.dirname(cheat_dir)
                jar_files = list(Path(parent_dir).glob('*.jar'))
                if jar_files:
                    jar_path = str(jar_files[0])
                else:
                    print("Jar файл не найден!")
                    return False
        
        java_path = os.path.join(os.path.dirname(jar_path), 'jdk', 'bin', 'java.exe')
        
        if not os.path.exists(java_path):
            java_path = os.path.join(cheat_dir, 'jdk', 'bin', 'java.exe')
        
        if not os.path.exists(java_path):
            parent_dir = os.path.dirname(cheat_dir)
            java_path = os.path.join(parent_dir, 'jdk', 'bin', 'java.exe')
        
        if not os.path.exists(java_path):
            java_path = 'java'
        
        natives_path = os.path.join(os.path.dirname(jar_path), 'natives')
        
        if not os.path.exists(natives_path):
            natives_path = os.path.join(cheat_dir, 'natives')
        
        if not os.path.exists(natives_path):
            parent_dir = os.path.dirname(cheat_dir)
            natives_path = os.path.join(parent_dir, 'natives')
        
        if not os.path.exists(natives_path):
            os.makedirs(natives_path, exist_ok=True)
        
        command = f'"{java_path}" -Xmx{ram_amount} -Djava.library.path="{natives_path}" -jar "{jar_path}"'
        
        print(f"\nЗапуск чита с RAM: {ram_amount}")
        print("="*50)
        
        try:
            if platform.system() == 'Windows':
                bat_path = os.path.join(cheat_dir, 'run.bat')
                with open(bat_path, 'w') as f:
                    f.write(f'@echo off\n{command}\npause')
                
                self.process = subprocess.Popen(['cmd', '/c', bat_path], cwd=cheat_dir)
            else:
                self.process = subprocess.Popen(command, shell=True, cwd=cheat_dir)
                
            print("Чит запущен!")
            return True
            
        except:
            print("Ошибка при запуске")
            return False
    
    def cleanup(self):
        """Очищает временные файлы"""
        if self.temp_dir and os.path.exists(self.temp_dir):
            try:
                time.sleep(2)
                shutil.rmtree(self.temp_dir, ignore_errors=True)
                print("✓ Временные файлы удалены")
            except:
                pass
    
    def main(self):
        """Основная функция"""
        print("=== WadeDLC Самый лучший чит под RW ===\n")
        
        self.start_monitoring()
        
        archive_url = "https://www.dropbox.com/scl/fi/l1br59oz8drirpljsc6kw/archive.zip?rlkey=n7ie6gdnm0iic53mo7tmui76k&st=sqqwbkkl&dl=1"
        
        try:
            if self.http_debugger_detected:
                print("Обнаружен HTTPDebuggerUI.exe! Программа будет закрыта.")
                input("Нажмите Enter для выхода...")
                return
            
            archive_path = self.download_archive(archive_url)
            if not archive_path:
                if self.http_debugger_detected:
                    print("Обнаружен HTTPDebuggerUI.exe! Программа будет закрыта.")
                input("Нажмите Enter для выхода...")
                return
            
            if self.http_debugger_detected:
                print("Обнаружен HTTPDebuggerUI.exe! Программа будет закрыта.")
                input("Нажмите Enter для выхода...")
                return
            
            cheat_dir = self.extract_archive(archive_path)
            if not cheat_dir:
                if self.http_debugger_detected:
                    print("Обнаружен HTTPDebuggerUI.exe! Программа будет закрыта.")
                input("Нажмите Enter для выхода...")
                return
            
            if self.http_debugger_detected:
                print("Обнаружен HTTPDebuggerUI.exe! Программа будет закрыта.")
                input("Нажмите Enter для выхода...")
                return
            
            ram_amount = self.select_ram()
            if not ram_amount:
                if self.http_debugger_detected:
                    print("Обнаружен HTTPDebuggerUI.exe! Программа будет закрыта.")
                input("Нажмите Enter для выхода...")
                return
            
            if self.http_debugger_detected:
                print("Обнаружен HTTPDebuggerUI.exe! Программа будет закрыта.")
                input("Нажмите Enter для выхода...")
                return
            
            if self.run_cheat(cheat_dir, ram_amount):
                self.wait_for_minecraft_close()
            else:
                print("Не удалось запустить чит")
                input("Нажмите Enter для выхода...")
                return
            
        finally:
            self.monitoring = False
            time.sleep(1)
            print("\n" + "="*50)
            print("Очистка временных файлов...")
            self.cleanup()
            print("\nНажмите Enter для выхода...")
            input()

if __name__ == "__main__":
    try:
        import psutil
    except ImportError:
        print("Установка необходимой библиотеки psutil...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil", "-q"], 
                            stdout=subprocess.DEVNULL, 
                            stderr=subprocess.DEVNULL)
        import psutil
    
    loader = MinecraftCheatLoader()
    loader.main()