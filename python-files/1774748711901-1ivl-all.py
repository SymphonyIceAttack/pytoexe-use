# cook your dish here
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import subprocess
import os
import logging
from datetime import datetime
import threading
import pyttsx3
import pycdlib
import pathlib
import ffmpeg
from PIL import Image
import hashlib
import magic
import json

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('optimizer_log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class SimpleAntivirus:
    def __init__(self):
        # База сигнатур вирусов (хеши известных вредоносных файлов)
        self.virus_signatures = {
            'd41d8cd98f00b204e9800998ecf8427e': 'TestVirus_EmptyFile',  # Пустой файл (пример)
        }
        self.scanner_running = False

    def calculate_hash(self, file_path):
        """Вычисляет SHA-256 хеш файла"""
        try:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256()
                while chunk := f.read(8192):
                    file_hash.update(chunk)
            return file_hash.hexdigest()
        except Exception as e:
            print(f"Ошибка чтения файла {file_path}: {e}")
            return None

    def identify_file_type(self, file_path):
        """Определяет тип файла по содержимому"""
        try:
            file_type = magic.from_file(file_path)
            return file_type
        except Exception:
            return "Неизвестный тип"

    def scan_file(self, file_path):
        """Сканирует один файл на вирусы"""
        if not os.path.isfile(file_path):
            return False, "Файл не существует"

        file_hash = self.calculate_hash(file_path)
        if file_hash is None:
            return False, "Ошибка хеширования"

        file_type = self.identify_file_type(file_path)

        if file_hash in self.virus_signatures:
            virus_name = self.virus_signatures[file_hash]
            return True, f"Обнаружен вирус: {virus_name} (тип: {file_type})"
        else:
            return False, f"Файл чист (тип: {file_type}, хеш: {file_hash[:10]}...)"

    def scan_directory(self, directory_path):
        """Рекурсивно сканирует папку и все подпапки"""
        results = []
        if not os.path.isdir(directory_path):
            return results, "Папка не существует"

        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if self.scanner_running:
                    file_path = os.path.join(root, file)
                    is_virus, message = self.scan_file(file_path)
                    results.append((file_path, is_virus, message))
        return results, "Сканирование завершено"

class TweakerBackup:
    def __init__(self):
        self.backup_file = "tweaker_backup.json"
        self.changes_log = {}

    def create_backup(self):
        """Создаёт резервную копию текущих настроек перед изменениями"""
        try:
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                json.dump(self.changes_log, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка создания бэкапа: {e}")
            return False

    def load_backup(self):
        """Загружает резервную копию"""
        if os.path.exists(self.backup_file):
            try:
                with open(self.backup_file,