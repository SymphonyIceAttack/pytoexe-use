"""
DefLauncher - Пиратский лаунчер для Minecraft Java Edition
"""

import os
import sys
import json
import subprocess
import threading
import time
import requests
import zipfile
import tarfile
import shutil
import platform
from pathlib import Path
from datetime import datetime

# Графика
try:
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.textinput import TextInput
    from kivy.uix.progressbar import ProgressBar
    from kivy.uix.popup import Popup
    from kivy.uix.dropdown import DropDown
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.graphics import Color, Rectangle
except ImportError:
    print("Устанавливаю Kivy...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "kivy"])
    from kivy.app import App
    from kivy.uix.boxlayout import BoxLayout
    from kivy.uix.gridlayout import GridLayout
    from kivy.uix.scrollview import ScrollView
    from kivy.uix.button import Button
    from kivy.uix.label import Label
    from kivy.uix.textinput import TextInput
    from kivy.uix.progressbar import ProgressBar
    from kivy.uix.popup import Popup
    from kivy.uix.dropdown import DropDown
    from kivy.clock import Clock
    from kivy.core.window import Window
    from kivy.graphics import Color, Rectangle

# Настройки окна
Window.size = (600, 700)
Window.title = "DefLauncher"

class JavaManager:
    """Управление установкой Java"""
    
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir) / 'java'
        self.base_dir.mkdir(exist_ok=True)
        self.system = platform.system().lower()
        self.arch = platform.machine()
        
    def get_java_path(self, version):
        """Получить путь к установленной Java"""
        java_dir = self.base_dir / f'java{version}'
        if self.system == 'windows':
            java_path = java_dir / 'bin' / 'java.exe'
        else:
            java_path = java_dir / 'bin' / 'java'
        
        if java_path.exists():
            return str(java_path)
        return None
    
    def is_java_installed(self, version):
        """Проверка, установлена ли Java"""
        return self.get_java_path(version) is not None
    
    def download_java(self, version, progress_callback=None):
        """Скачивание и установка Java"""
        try:
            java_dir = self.base_dir / f'java{version}'
            java_dir.mkdir(exist_ok=True)
            
            # Определяем URL для скачивания Java
            if self.system == 'windows':
                if version == "8":
                    url = "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u422-b05/OpenJDK8U-jre_x64_windows_hotspot_8u422b05.zip"
                elif version == "11":
                    url = "https://github.com/adoptium/temurin11-binaries/releases/download/jdk11.0.24%2B8/OpenJDK11U-jre_x64_windows_hotspot_11.0.24_8.zip"
                elif version == "17":
                    url = "https://github.com/adoptium/temurin17-binaries/releases/download/jdk17.0.12%2B7/OpenJDK17U-jre_x64_windows_hotspot_17.0.12_7.zip"
                else:
                    url = f"https://github.com/adoptium/temurin{version}-binaries/releases/latest/download/OpenJDK{version}U-jre_x64_windows_hotspot_latest.zip"
            else:  # Linux/Mac
                if version == "8":
                    url = "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u422-b05/OpenJDK8U-jre_x64_linux_hotspot_8u422b05.tar.gz"
                elif version == "11":
                    url = "https://github.com/adoptium/temurin11-binaries/releases/download/jdk11.0.24%2B8/OpenJDK11U-jre_x64_linux_hotspot_11.0.24_8.tar.gz"
                elif version == "17":
                    url = "https://github.com/adoptium/temurin17-binaries/releases/download/jdk17.0.12%2B7/OpenJDK17U-jre_x64_linux_hotspot_17.0.12_7.tar.gz"
                else:
                    url = f"https://github.com/adoptium/temurin{version}-binaries/releases/latest/download/OpenJDK{version}U-jre_x64_linux_hotspot_latest.tar.gz"
            
            if progress_callback:
                progress_callback(f"📥 Скачиваю Java {version}...")
            
            # Скачиваем файл
            response = requests.get(url, stream=True)
            total_size = int(response.headers.get('content-length', 0))
            
            filename = url.split('/')[-1]
            filepath = self.base_dir / filename
            
            with open(filepath, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            percent = (downloaded / total_size) * 100
                            progress_callback(f"📥 Java {version}: {percent:.1f}%")
            
            if progress_callback:
                progress_callback(f"📦 Распаковываю Java {version}...")
            
            # Распаковываем
            if filename.endswith('.zip'):
                with zipfile.ZipFile(filepath, 'r') as zip_ref:
                    zip_ref.extractall(java_dir)
            else:
                with tarfile.open(filepath, 'r:gz') as tar_ref:
                    tar_ref.extractall(java_dir)
            
            # Перемещаем файлы из вложенной папки
            extracted_dirs = list(java_dir.glob('jdk*')) + list(java_dir.glob('OpenJDK*'))
            if extracted_dirs:
                for item in extracted_dirs[0].iterdir():
                    shutil.move(str(item), str(java_dir / item.name))
                shutil.rmtree(extracted_dirs[0])
            
            # Удаляем архив
            filepath.unlink()
            
            if progress_callback:
                progress_callback(f"✅ Java {version} установлена")
            
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"❌ Ошибка установки Java: {str(e)}")
            return False

class MinecraftManager:
    """Управление установкой Minecraft"""
    
    def __init__(self, base_dir):
        self.base_dir = Path(base_dir)
        self.versions_dir = self.base_dir / 'versions'
        self.versions_dir.mkdir(exist_ok=True)
        
    def get_java_version_for_minecraft(self, minecraft_version):
        """Определяет нужную версию Java для Minecraft"""
        try:
            # Парсим версию Minecraft
            parts = minecraft_version.split('.')
            major = int(parts[1])
            
            if major >= 18:
                return "17"
            elif major == 17:
                return "16"
            elif major >= 9:
                return "11"
            else:
                return "8"
        except:
            return "8"  # По умолчанию Java 8
    
    def get_available_versions(self):
        """Получение списка доступных версий"""
        versions = []
        try:
            response = requests.get(
                'https://bmclapi2.bangbang93.com/versions',
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                for v in data['versions']:
                    if v['type'] == 'release':
                        versions.append({
                            'id': v['id'],
                            'url': v['url']
                        })
        except:
            # Заглушка если нет интернета
            versions = [
                {'id': '1.20.4', 'url': ''},
                {'id': '1.20.2', 'url': ''},
                {'id': '1.19.4', 'url': ''},
                {'id': '1.18.2', 'url': ''},
                {'id': '1.17.1', 'url': ''},
                {'id': '1.16.5', 'url': ''},
                {'id': '1.15.2', 'url': ''},
                {'id': '1.12.2', 'url': ''},
                {'id': '1.8.9', 'url': ''},
            ]
        
        # Добавляем информацию о том, скачана ли версия
        for v in versions:
            v['downloaded'] = self.is_downloaded(v['id'])
        
        return versions
    
    def is_downloaded(self, version):
        """Проверка, скачана ли версия"""
        version_dir = self.versions_dir / version
        client_path = version_dir / f'{version}.jar'
        return client_path.exists()
    
    def download_minecraft(self, version, progress_callback=None):
        """Скачивание Minecraft"""
        try:
            version_dir = self.versions_dir / version
            version_dir.mkdir(exist_ok=True)
            
            client_path = version_dir / f'{version}.jar'
            
            if client_path.exists():
                if progress_callback:
                    progress_callback(f"✅ Minecraft {version} уже скачан")
                return True
            
            if progress_callback:
                progress_callback(f"📥 Получаю информацию о {version}...")
            
            # Получаем информацию о версии
            response = requests.get(
                f'https://bmclapi2.bangbang93.com/version/{version}/json',
                timeout=10
            )
            
            if response.status_code != 200:
                if progress_callback:
                    progress_callback(f"❌ Не удалось получить информацию о версии")
                return False
            
            data = response.json()
            
            # Скачиваем клиент
            client_url = data['downloads']['client']['url']
            if progress_callback:
                progress_callback(f"📥 Скачиваю Minecraft {version}...")
            
            client_response = requests.get(client_url, stream=True)
            total_size = int(client_response.headers.get('content-length', 0))
            
            with open(client_path, 'wb') as f:
                downloaded = 0
                for chunk in client_response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback and total_size > 0:
                            percent = (downloaded / total_size) * 100
                            progress_callback(f"📥 Minecraft {version}: {percent:.1f}%")
            
            if progress_callback:
                progress_callback(f"✅ Minecraft {version} скачан")
            
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"❌ Ошибка: {str(e)}")
            return False

class DefLauncherGUI(App):
    """Графический интерфейс лаунчера"""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.base_dir = Path.home() / 'DefLauncher'
        self.base_dir.mkdir(exist_ok=True)
        
        self.java_manager = JavaManager(self.base_dir)
        self.minecraft_manager = MinecraftManager(self.base_dir)
        
        self.versions = []
        self.selected_version = None
        self.username = "Player"
        self.ram = "2G"
        
    def build(self):
        main_layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Заголовок
        title = Label(
            text="DefLauncher",
            size_hint_y=0.1,
            font_size='24sp',
            bold=True
        )
        main_layout.add_widget(title)
        
        # Настройки
        settings_layout = GridLayout(cols=2, size_hint_y=0.15, spacing=5)
        
        settings_layout.add_widget(Label(text="Ник:"))
        self.username_input = TextInput(text=self.username, multiline=False)
        settings_layout.add_widget(self.username_input)
        
        settings_layout.add_widget(Label(text="ОЗУ:"))
        self.ram_input = TextInput(text=self.ram, multiline=False)
        settings_layout.add_widget(self.ram_input)
        
        main_layout.add_widget(settings_layout)
        
        # Список версий
        versions_label = Label(
            text="Доступные версии:",
            size_hint_y=0.05,
            halign='left'
        )
        versions_label.bind(size=lambda s, w: s.setter('text_size')(s, (w, None)))
        main_layout.add_widget(versions_label)
        
        # ScrollView для версий
        scroll = ScrollView(size_hint_y=0.5)
        self.versions_layout = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.versions_layout.bind(minimum_height=self.versions_layout.setter('height'))
        scroll.add_widget(self.versions_layout)
        main_layout.add_widget(scroll)
        
        # Информация о выбранной версии
        self.info_label = Label(
            text="Выберите версию",
            size_hint_y=0.1,
            color=(0.7, 0.7, 0.7, 1)
        )
        main_layout.add_widget(self.info_label)
        
        # Кнопки управления
        buttons_layout = BoxLayout(size_hint_y=0.1, spacing=10)
        
        self.install_btn = Button(text="Установить")
        self.install_btn.bind(on_press=self.install_version)
        buttons_layout.add_widget(self.install_btn)
        
        self.play_btn = Button(text="Играть")
        self.play_btn.bind(on_press=self.play_minecraft)
        buttons_layout.add_widget(self.play_btn)
        
        main_layout.add_widget(buttons_layout)
        
        # Статус бар
        self.status_bar = Label(
            text="Готов к работе",
            size_hint_y=0.05,
            color=(0.5, 0.5, 0.5, 1)
        )
        main_layout.add_widget(self.status_bar)
        
        # Загружаем версии
        Clock.schedule_once(lambda dt: self.load_versions(), 0.1)
        
        return main_layout
    
    def load_versions(self):
        """Загрузка списка версий"""
        self.status_bar.text = "⏳ Загрузка списка версий..."
        
        def load():
            versions = self.minecraft_manager.get_available_versions()
            Clock.schedule_once(lambda dt: self.display_versions(versions))
        
        threading.Thread(target=load).start()
    
    def display_versions(self, versions):
        """Отображение списка версий"""
        self.versions_layout.clear_widgets()
        self.versions = versions
        
        for v in versions:
            btn = Button(
                text=f"{v['id']} {'✅' if v['downloaded'] else '📥'}",
                size_hint_y=None,
                height=40,
                background_color=(0.2, 0.2, 0.2, 1) if not v['downloaded'] else (0.1, 0.5, 0.1, 1)
            )
            btn.version_data = v
            btn.bind(on_press=self.select_version)
            self.versions_layout.add_widget(btn)
        
        self.status_bar.text = f"✅ Загружено {len(versions)} версий"
    
    def select_version(self, instance):
        """Выбор версии"""
        self.selected_version = instance.version_data
        
        java_version = self.minecraft_manager.get_java_version_for_minecraft(
            self.selected_version['id']
        )
        
        if self.selected_version['downloaded']:
            status = "✅ Установлена"
            java_status = f"Java {java_version} " + ("✅" if self.java_manager.is_java_installed(java_version) else "❌")
        else:
            status = "📥 Не установлена"
            java_status = f"Потребуется Java {java_version}"
        
        self.info_label.text = f"{self.selected_version['id']}\n{status}\n{java_status}"
    
    def install_version(self, instance):
        """Установка выбранной версии"""
        if not self.selected_version:
            self.show_popup("Ошибка", "Сначала выберите версию")
            return
        
        self.install_btn.disabled = True
        self.play_btn.disabled = True
        
        def install():
            # Определяем нужную Java
            java_version = self.minecraft_manager.get_java_version_for_minecraft(
                self.selected_version['id']
            )
            
            # Устанавливаем Java если нужно
            if not self.java_manager.is_java_installed(java_version):
                def java_progress(msg):
                    Clock.schedule_once(lambda dt: self.update_status(msg))
                
                success = self.java_manager.download_java(java_version, java_progress)
                if not success:
                    Clock.schedule_once(lambda dt: self.install_complete(False))
                    return
            
            # Устанавливаем Minecraft
            def mc_progress(msg):
                Clock.schedule_once(lambda dt: self.update_status(msg))
            
            success = self.minecraft_manager.download_minecraft(
                self.selected_version['id'],
                mc_progress
            )
            
            Clock.schedule_once(lambda dt: self.install_complete(success))
        
        threading.Thread(target=install).start()
    
    def play_minecraft(self, instance):
        """Запуск Minecraft"""
        if not self.selected_version:
            self.show_popup("Ошибка", "Сначала выберите версию")
            return
        
        if not self.selected_version['downloaded']:
            self.show_popup("Ошибка", "Сначала установите версию")
            return
        
        self.play_btn.disabled = True
        self.install_btn.disabled = True
        
        def play():
            java_version = self.minecraft_manager.get_java_version_for_minecraft(
                self.selected_version['id']
            )
            
            java_path = self.java_manager.get_java_path(java_version)
            if not java_path:
                Clock.schedule_once(lambda dt: self.update_status("❌ Java не найдена"))
                Clock.schedule_once(lambda dt: self.play_complete(False))
                return
            
            version_dir = self.minecraft_manager.versions_dir / self.selected_version['id']
            client_path = version_dir / f"{self.selected_version['id']}.jar"
            
            if not client_path.exists():
                Clock.schedule_once(lambda dt: self.update_status("❌ Minecraft не найден"))
                Clock.schedule_once(lambda dt: self.play_complete(False))
                return
            
            # Создаем инстанс для запуска
            instance_dir = self.base_dir / 'instances' / f"{self.selected_version['id']}_{int(time.time())}"
            instance_dir.mkdir(parents=True, exist_ok=True)
            
            # Копируем клиент
            shutil.copy2(client_path, instance_dir / 'minecraft.jar')
            
            # Получаем ник
            username = self.username_input.text.strip() or "Player"
            ram = self.ram_input.text.strip() or "2G"
            
            # Формируем команду
            cmd = [
                java_path,
                f'-Xmx{ram}',
                f'-Xms{ram}',
                '-Djava.library.path=natives',
                '-cp', f'minecraft.jar',
                'net.minecraft.client.main.Main',
                '--username', username,
                '--version', self.selected_version['id'],
                '--gameDir', str(instance_dir),
                '--assetsDir', str(self.base_dir / 'assets'),
                '--accessToken', '0',
                '--userProperties', '{}'
            ]
            
            Clock.schedule_once(lambda dt: self.update_status("🚀 Запуск Minecraft..."))
            
            # Создаем папку для логов
            logs_dir = self.base_dir / 'logs'
            logs_dir.mkdir(exist_ok=True)
            
            # Запускаем
            try:
                subprocess.Popen(
                    cmd,
                    cwd=str(instance_dir),
                    stdout=open(logs_dir / f'log_{self.selected_version["id"]}_{int(time.time())}.txt', 'w'),
                    stderr=subprocess.STDOUT
                )
                Clock.schedule_once(lambda dt: self.update_status("✅ Minecraft запущен"))
            except Exception as e:
                Clock.schedule_once(lambda dt: self.update_status(f"❌ Ошибка: {str(e)}"))
            
            Clock.schedule_once(lambda dt: self.play_complete(True))
        
        threading.Thread(target=play).start()
    
    def install_complete(self, success):
        """Завершение установки"""
        self.install_btn.disabled = False
        self.play_btn.disabled = False
        
        if success:
            self.update_status("✅ Установка завершена")
            # Обновляем список версий
            self.load_versions()
        else:
            self.update_status("❌ Ошибка установки")
    
    def play_complete(self, success):
        """Завершение запуска"""
        self.play_btn.disabled = False
        self.install_btn.disabled = False
    
    def update_status(self, message):
        """Обновление статуса"""
        self.status_bar.text = message
    
    def show_popup(self, title, message):
        """Показ всплывающего окна"""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.3)
        )
        popup.open()

if __name__ == '__main__':
    DefLauncherGUI().run()