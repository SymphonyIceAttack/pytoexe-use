#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Модуль загрузки, хранения и валидации файлов
Версия: 1.0.0
Автор: Курсовая работа
Дата: Декабрь 2024 г.

Описание:
    Программный модуль для загрузки, хранения и валидации файлов 
    с графическим пользовательским интерфейсом на Tkinter.
"""

import os
import sys
import hashlib
import json
import shutil
import mimetypes
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from pathlib import Path

# Попытка импорта Tkinter (для разных версий Python)
try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
except ImportError:
    print("Ошибка: Tkinter не установлен. Установите python3-tk")
    sys.exit(1)

# ============================================================
# НАСТРОЙКА ЛОГИРОВАНИЯ
# ============================================================

# Создание директории для логов
LOG_DIR = Path("./logs")
LOG_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'file_manager.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ============================================================
# КЛАСС ДЛЯ ХРАНЕНИЯ ИНФОРМАЦИИ О ФАЙЛЕ
# ============================================================

@dataclass
class FileInfo:
    """
    Класс для хранения информации о файле.
    Использует декоратор dataclass для автоматической генерации методов.
    """
    id: str                    # Уникальный идентификатор (UUID)
    original_name: str         # Оригинальное имя файла
    stored_name: str           # Имя для хранения (уникальное)
    size: int                  # Размер в байтах
    file_type: str             # MIME-тип файла
    upload_date: str           # Дата и время загрузки
    file_hash: str             # SHA-256 хеш-сумма файла
    
    def to_dict(self) -> dict:
        """Преобразование в словарь для JSON-сериализации"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'FileInfo':
        """Создание объекта из словаря"""
        return cls(**data)
    
    def get_size_str(self) -> str:
        """Возвращает размер в удобном для чтения формате"""
        if self.size < 1024:
            return f"{self.size} Б"
        elif self.size < 1024 * 1024:
            return f"{self.size / 1024:.2f} КБ"
        elif self.size < 1024 * 1024 * 1024:
            return f"{self.size / (1024 * 1024):.2f} МБ"
        else:
            return f"{self.size / (1024 * 1024 * 1024):.2f} ГБ"


# ============================================================
# КЛАСС ДЛЯ ВАЛИДАЦИИ ФАЙЛОВ
# ============================================================

class FileValidator:
    """
    Класс для валидации файлов.
    Проверяет тип файла (MIME) и размер.
    """
    
    # Белый список допустимых MIME-типов
    ALLOWED_TYPES = {
        # Изображения
        'image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp',
        'image/svg+xml', 'image/tiff',
        
        # Документы
        'application/pdf',
        'text/plain', 'text/csv', 'text/html', 'text/css', 'text/xml',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel',
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'application/vnd.ms-powerpoint',
        'application/vnd.openxmlformats-officedocument.presentationml.presentation',
        'application/rtf',
        
        # Архивы
        'application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed',
        'application/x-tar', 'application/gzip',
        
        # Данные
        'application/json', 'application/xml',
        
        # Аудио
        'audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/midi',
        
        # Видео (с ограничениями по размеру)
        'video/mp4', 'video/mpeg', 'video/quicktime',
    }
    
    # Максимальный размер файла по умолчанию (50 МБ)
    DEFAULT_MAX_SIZE = 50 * 1024 * 1024
    
    # Максимальный размер для видео (200 МБ)
    VIDEO_MAX_SIZE = 200 * 1024 * 1024
    
    def __init__(self, allowed_types: set = None, max_size: int = None):
        """
        Инициализация валидатора.
        
        Args:
            allowed_types: Множество допустимых MIME-типов
            max_size: Максимальный размер файла в байтах
        """
        self.allowed_types = allowed_types or self.ALLOWED_TYPES
        self.max_size = max_size or self.DEFAULT_MAX_SIZE
    
    def get_mime_type(self, file_path: str) -> str:
        """
        Определение MIME-типа файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            MIME-тип файла
        """
        # Попытка определить через mimetypes
        mime_type, encoding = mimetypes.guess_type(file_path)
        
        if mime_type is None:
            # Fallback по расширению файла
            ext = os.path.splitext(file_path)[1].lower()
            mime_map = {
                '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                '.png': 'image/png', '.gif': 'image/gif',
                '.bmp': 'image/bmp', '.webp': 'image/webp',
                '.pdf': 'application/pdf', '.txt': 'text/plain',
                '.csv': 'text/csv', '.html': 'text/html',
                '.css': 'text/css', '.xml': 'application/xml',
                '.json': 'application/json', '.zip': 'application/zip',
                '.rar': 'application/x-rar-compressed', '.7z': 'application/x-7z-compressed',
                '.doc': 'application/msword', '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                '.xls': 'application/vnd.ms-excel', '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                '.ppt': 'application/vnd.ms-powerpoint', '.pptx': 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
                '.mp3': 'audio/mpeg', '.wav': 'audio/wav', '.ogg': 'audio/ogg',
                '.mp4': 'video/mp4', '.mpeg': 'video/mpeg', '.mov': 'video/quicktime',
            }
            mime_type = mime_map.get(ext, 'application/octet-stream')
        
        return mime_type
    
    def validate_size(self, file_path: str) -> Tuple[bool, str, int]:
        """
        Проверка размера файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Кортеж (успех, сообщение, размер)
        """
        try:
            size = os.path.getsize(file_path)
            
            # Для видеофайлов используем больший лимит
            mime_type = self.get_mime_type(file_path)
            max_size_for_file = self.VIDEO_MAX_SIZE if mime_type.startswith('video/') else self.max_size
            
            if size > max_size_for_file:
                return False, f"Файл слишком большой. Максимальный размер: {max_size_for_file // (1024*1024)} МБ", size
            
            # Форматирование размера для сообщения
            if size < 1024:
                size_str = f"{size} Б"
            elif size < 1024 * 1024:
                size_str = f"{size / 1024:.2f} КБ"
            else:
                size_str = f"{size / (1024*1024):.2f} МБ"
            
            return True, f"Размер: {size_str}", size
            
        except OSError as e:
            return False, f"Ошибка получения размера файла: {e}", 0
    
    def validate_type(self, file_path: str) -> Tuple[bool, str, str]:
        """
        Проверка типа файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Кортеж (успех, сообщение, MIME-тип)
        """
        mime_type = self.get_mime_type(file_path)
        
        if mime_type not in self.allowed_types:
            # Более детальное сообщение
            if mime_type.startswith('application/'):
                type_name = mime_type.split('/')[1]
                return False, f"Тип файла '{type_name}' не разрешён. Разрешены: изображения, PDF, документы, архивы", mime_type
            else:
                return False, f"Тип файла '{mime_type}' не разрешён", mime_type
        
        return True, f"Тип файла разрешён: {mime_type}", mime_type
    
    def validate_file(self, file_path: str) -> Tuple[bool, str, dict]:
        """
        Полная валидация файла.
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            Кортеж (успех, сообщение, детали проверки)
        """
        results = {
            'valid': False,
            'exists': False,
            'size_valid': False,
            'type_valid': False,
            'mime_type': None,
            'size': 0,
            'size_message': '',
            'type_message': ''
        }
        
        # Проверка существования файла
        if not os.path.exists(file_path):
            return False, "Файл не существует", results
        
        results['exists'] = True
        
        # Проверка размера
        size_valid, size_msg, size = self.validate_size(file_path)
        results['size_valid'] = size_valid
        results['size'] = size
        results['size_message'] = size_msg
        
        # Проверка типа
        type_valid, type_msg, mime_type = self.validate_type(file_path)
        results['type_valid'] = type_valid
        results['type_message'] = type_msg
        results['mime_type'] = mime_type
        
        # Итоговая проверка
        if not size_valid:
            return False, size_msg, results
        if not type_valid:
            return False, type_msg, results
        
        results['valid'] = True
        return True, "Файл прошёл валидацию", results


# ============================================================
# КЛАСС ДЛЯ ХРАНЕНИЯ ФАЙЛОВ
# ============================================================

class FileStorage:
    """
    Класс для хранения файлов и управления метаданными.
    """
    
    def __init__(self, storage_path: str = "./storage"):
        """
        Инициализация хранилища.
        
        Args:
            storage_path: Путь к директории хранилища
        """
        self.storage_path = Path(storage_path)
        self.metadata_file = self.storage_path / "metadata.json"
        self.files_path = self.storage_path / "files"
        self._init_storage()
    
    def _init_storage(self):
        """Инициализация структуры хранилища."""
        try:
            self.storage_path.mkdir(exist_ok=True, parents=True)
            self.files_path.mkdir(exist_ok=True)
            
            if not self.metadata_file.exists():
                self._save_metadata({
                    "files": [],
                    "stats": {
                        "total_files": 0,
                        "total_size": 0,
                        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                })
                logger.info(f"Хранилище инициализировано: {self.storage_path}")
        except Exception as e:
            logger.error(f"Ошибка инициализации хранилища: {e}")
            raise
    
    def _load_metadata(self) -> dict:
        """
        Загрузка метаданных из JSON-файла.
        
        Returns:
            Словарь с метаданными
        """
        try:
            with open(self.metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError) as e:
            logger.warning(f"Ошибка загрузки метаданных: {e}. Создание новых метаданных.")
            return {"files": [], "stats": {"total_files": 0, "total_size": 0}}
    
    def _save_metadata(self, metadata: dict):
        """
        Сохранение метаданных в JSON-файл.
        
        Args:
            metadata: Словарь с метаданными
        """
        try:
            # Обновление времени последнего изменения
            if "stats" in metadata:
                metadata["stats"]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Создание резервной копии перед записью
            if self.metadata_file.exists():
                backup_file = self.metadata_file.with_suffix('.json.bak')
                shutil.copy2(self.metadata_file, backup_file)
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Ошибка сохранения метаданных: {e}")
            raise
    
    def _calculate_file_hash(self, file_path: str, chunk_size: int = 8192) -> str:
        """
        Вычисление SHA-256 хеша файла.
        
        Args:
            file_path: Путь к файлу
            chunk_size: Размер чанка для чтения
            
        Returns:
            SHA-256 хеш в шестнадцатеричном формате
        """
        sha256_hash = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for byte_block in iter(lambda: f.read(chunk_size), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Ошибка вычисления хеша: {e}")
            return ""
    
    def _generate_unique_filename(self, original_name: str, file_hash: str = None) -> str:
        """
        Генерация уникального имени для хранения.
        
        Args:
            original_name: Оригинальное имя файла
            file_hash: Хеш файла (опционально)
            
        Returns:
            Уникальное имя файла
        """
        ext = os.path.splitext(original_name)[1].lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if file_hash:
            short_hash = file_hash[:8]
            return f"{short_hash}_{timestamp}{ext}"
        else:
            unique_id = str(uuid.uuid4())[:8]
            return f"{unique_id}_{timestamp}{ext}"
    
    def save_file(self, source_path: str, original_name: str = None) -> Optional[FileInfo]:
        """
        Сохранение файла в хранилище.
        
        Args:
            source_path: Путь к исходному файлу
            original_name: Оригинальное имя файла (опционально)
            
        Returns:
            Объект FileInfo или None при ошибке
        """
        try:
            # Проверка существования исходного файла
            if not os.path.exists(source_path):
                logger.error(f"Файл не найден: {source_path}")
                return None
            
            # Определение оригинального имени
            if original_name is None:
                original_name = os.path.basename(source_path)
            
            # Очистка имени файла от недопустимых символов
            original_name = self._sanitize_filename(original_name)
            
            # Вычисление хеша
            file_hash = self._calculate_file_hash(source_path)
            if not file_hash:
                logger.warning("Не удалось вычислить хеш файла")
            
            # Генерация уникального имени
            stored_name = self._generate_unique_filename(original_name, file_hash)
            dest_path = self.files_path / stored_name
            
            # Копирование файла с сохранением метаданных
            shutil.copy2(source_path, dest_path)
            
            # Получение информации о файле
            file_size = os.path.getsize(dest_path)
            mime_type = mimetypes.guess_type(source_path)[0] or "unknown"
            
            # Создание объекта FileInfo
            file_info = FileInfo(
                id=str(uuid.uuid4()),
                original_name=original_name,
                stored_name=stored_name,
                size=file_size,
                file_type=mime_type,
                upload_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                file_hash=file_hash
            )
            
            # Обновление метаданных
            metadata = self._load_metadata()
            metadata["files"].append(file_info.to_dict())
            metadata["stats"]["total_files"] += 1
            metadata["stats"]["total_size"] += file_size
            self._save_metadata(metadata)
            
            logger.info(f"Файл сохранён: {original_name} -> {stored_name} (ID: {file_info.id[:8]})")
            return file_info
            
        except Exception as e:
            logger.error(f"Ошибка сохранения файла: {e}")
            return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Очистка имени файла от недопустимых символов.
        
        Args:
            filename: Исходное имя файла
            
        Returns:
            Очищенное имя файла
        """
        # Замена недопустимых символов на _
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Ограничение длины имени
        max_length = 200
        if len(filename) > max_length:
            name, ext = os.path.splitext(filename)
            filename = name[:max_length - len(ext) - 10] + "..." + ext
        
        return filename
    
    def delete_file(self, file_id: str) -> Tuple[bool, str]:
        """
        Удаление файла из хранилища.
        
        Args:
            file_id: ID файла для удаления
            
        Returns:
            Кортеж (успех, сообщение)
        """
        try:
            metadata = self._load_metadata()
            
            for i, file_data in enumerate(metadata["files"]):
                if file_data["id"] == file_id:
                    file_info = FileInfo.from_dict(file_data)
                    
                    # Удаление физического файла
                    file_path = self.files_path / file_info.stored_name
                    if file_path.exists():
                        file_path.unlink()
                        logger.info(f"Физический файл удалён: {file_info.stored_name}")
                    else:
                        logger.warning(f"Физический файл не найден: {file_info.stored_name}")
                    
                    # Обновление статистики
                    metadata["stats"]["total_files"] -= 1
                    metadata["stats"]["total_size"] -= file_info.size
                    
                    # Удаление из списка
                    metadata["files"].pop(i)
                    self._save_metadata(metadata)
                    
                    logger.info(f"Файл удалён: {file_info.original_name}")
                    return True, f"Файл '{file_info.original_name}' удалён"
            
            return False, "Файл не найден"
            
        except Exception as e:
            logger.error(f"Ошибка удаления файла: {e}")
            return False, f"Ошибка удаления: {e}"
    
    def get_all_files(self) -> List[FileInfo]:
        """
        Получение списка всех файлов.
        
        Returns:
            Список объектов FileInfo
        """
        metadata = self._load_metadata()
        files = []
        for file_data in metadata["files"]:
            try:
                files.append(FileInfo.from_dict(file_data))
            except Exception as e:
                logger.error(f"Ошибка загрузки файла из метаданных: {e}")
        return files
    
    def get_file(self, file_id: str) -> Optional[FileInfo]:
        """
        Получение информации о файле по ID.
        
        Args:
            file_id: ID файла
            
        Returns:
            Объект FileInfo или None
        """
        for file_info in self.get_all_files():
            if file_info.id == file_id:
                return file_info
        return None
    
    def get_file_by_original_name(self, name: str) -> Optional[FileInfo]:
        """
        Поиск файла по оригинальному имени.
        
        Args:
            name: Оригинальное имя файла
            
        Returns:
            Объект FileInfo или None
        """
        name_lower = name.lower()
        for file_info in self.get_all_files():
            if file_info.original_name.lower() == name_lower:
                return file_info
        return None
    
    def get_file_path(self, file_info: FileInfo) -> Path:
        """
        Получение пути к физическому файлу.
        
        Args:
            file_info: Объект FileInfo
            
        Returns:
            Путь к файлу
        """
        return self.files_path / file_info.stored_name
    
    def get_stats(self) -> dict:
        """
        Получение статистики хранилища.
        
        Returns:
            Словарь со статистикой
        """
        metadata = self._load_metadata()
        stats = metadata.get("stats", {"total_files": 0, "total_size": 0})
        
        # Добавление форматированного размера
        total_size = stats.get("total_size", 0)
        if total_size < 1024:
            stats["total_size_str"] = f"{total_size} Б"
        elif total_size < 1024 * 1024:
            stats["total_size_str"] = f"{total_size / 1024:.2f} КБ"
        else:
            stats["total_size_str"] = f"{total_size / (1024 * 1024):.2f} МБ"
        
        return stats
    
    def search_files(self, query: str) -> List[FileInfo]:
        """
        Поиск файлов по имени.
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Список найденных файлов
        """
        query_lower = query.lower()
        results = []
        for file_info in self.get_all_files():
            if query_lower in file_info.original_name.lower():
                results.append(file_info)
        return results
    
    def export_metadata(self, export_path: str) -> bool:
        """
        Экспорт метаданных в JSON-файл.
        
        Args:
            export_path: Путь для экспорта
            
        Returns:
            True при успехе, False при ошибке
        """
        try:
            metadata = self._load_metadata()
            export_file = Path(export_path)
            export_file.parent.mkdir(exist_ok=True, parents=True)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Метаданные экспортированы: {export_path}")
            return True
        except Exception as e:
            logger.error(f"Ошибка экспорта метаданных: {e}")
            return False


# ============================================================
# ГЛАВНОЕ ПРИЛОЖЕНИЕ С ГРАФИЧЕСКИМ ИНТЕРФЕЙСОМ
# ============================================================

class FileManagerApp:
    """Главное приложение с графическим интерфейсом."""
    
    def __init__(self):
        """Инициализация приложения."""
        self.root = tk.Tk()
        self.root.title("Менеджер файлов - Загрузка, хранение и валидация файлов")
        self.root.geometry("1100x750")
        self.root.minsize(800, 600)
        
        # Установка иконки (если есть)
        try:
            self.root.iconbitmap(default='icon.ico')
        except:
            pass
        
        # Инициализация компонентов
        self.validator = FileValidator()
        self.storage = FileStorage()
        
        # Переменные для хранения состояния
        self.current_filter = tk.StringVar(value="")
        self.current_sort_column = "date"
        self.current_sort_reverse = True
        
        # Настройка стилей
        self._setup_styles()
        
        # Создание интерфейса
        self._create_menu()
        self._create_widgets()
        
        # Загрузка списка файлов
        self.refresh_file_list()
        
        # Привязка горячих клавиш
        self._setup_hotkeys()
        
        # Обработка закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _setup_styles(self):
        """Настройка стилей интерфейса."""
        style = ttk.Style()
        
        # Попытка использования темы
        try:
            style.theme_use('clam')
        except:
            pass
        
        # Настройка цветов
        self.root.configure(bg='#f5f5f5')
        
        # Стили для кнопок
        style.configure('Action.TButton', font=('Segoe UI', 10, 'bold'), padding=8)
        style.configure('Danger.TButton', foreground='#c0392b', font=('Segoe UI', 10))
        style.configure('Success.TButton', foreground='#27ae60', font=('Segoe UI', 10, 'bold'))
        
        # Стили для фреймов
        style.configure('Card.TLabelframe', relief='ridge', borderwidth=1)
        style.configure('Card.TLabelframe.Label', font=('Segoe UI', 10, 'bold'))
    
    def _create_menu(self):
        """Создание главного меню."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Загрузить файл", command=self.upload_file, accelerator="Ctrl+O")
        file_menu.add_separator()
        file_menu.add_command(label="Экспорт метаданных", command=self.export_metadata)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.on_closing, accelerator="Ctrl+Q")
        
        # Меню "Правка"
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Правка", menu=edit_menu)
        edit_menu.add_command(label="Обновить список", command=self.refresh_file_list, accelerator="F5")
        edit_menu.add_command(label="Очистить лог", command=self.clear_logs, accelerator="Ctrl+L")
        
        # Меню "Вид"
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Вид", menu=view_menu)
        view_menu.add_command(label="Показать статистику", command=self.show_stats)
        
        # Меню "Помощь"
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Помощь", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)
    
    def _setup_hotkeys(self):
        """Настройка горячих клавиш."""
        self.root.bind('<Control-o>', lambda e: self.upload_file())
        self.root.bind('<Control-q>', lambda e: self.on_closing())
        self.root.bind('<F5>', lambda e: self.refresh_file_list())
        self.root.bind('<Control-l>', lambda e: self.clear_logs())
        self.root.bind('<Delete>', lambda e: self.delete_file())
    
    def _create_widgets(self):
        """Создание всех виджетов интерфейса."""
        # Основной контейнер
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Верхняя панель с кнопками действий
        self._create_action_panel(main_frame)
        
        # Панель поиска и фильтрации
        self._create_search_panel(main_frame)
        
        # Панель информации о валидации
        self._create_validation_panel(main_frame)
        
        # Разделитель
        ttk.Separator(main_frame, orient='horizontal').pack(fill=tk.X, pady=10)
        
        # Панель со списком файлов
        self._create_file_list_panel(main_frame)
        
        # Нижняя панель со статусом
        self._create_status_panel(main_frame)
    
    def _create_action_panel(self, parent):
        """Панель с кнопками действий."""
        action_frame = ttk.LabelFrame(parent, text="Действия с файлами", padding="10", style='Card.TLabelframe')
        action_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Контейнер для кнопок
        btn_frame = ttk.Frame(action_frame)
        btn_frame.pack(fill=tk.X)
        
        # Кнопки
        self.upload_btn = ttk.Button(
            btn_frame, text="📁 Загрузить файл", 
            command=self.upload_file, style='Success.TButton',
            width=18
        )
        self.upload_btn.pack(side=tk.LEFT, padx=5)
        
        self.delete_btn = ttk.Button(
            btn_frame, text="🗑 Удалить выбранный", 
            command=self.delete_file, style='Danger.TButton',
            width=18
        )
        self.delete_btn.pack(side=tk.LEFT, padx=5)
        
        self.refresh_btn = ttk.Button(
            btn_frame, text="🔄 Обновить список", 
            command=self.refresh_file_list,
            width=18
        )
        self.refresh_btn.pack(side=tk.LEFT, padx=5)
        
        self.export_btn = ttk.Button(
            btn_frame, text="💾 Экспорт метаданных", 
            command=self.export_metadata,
            width=18
        )
        self.export_btn.pack(side=tk.LEFT, padx=5)
        
        self.clear_log_btn = ttk.Button(
            btn_frame, text="🗑 Очистить логи", 
            command=self.clear_logs,
            width=18
        )
        self.clear_log_btn.pack(side=tk.LEFT, padx=5)
        
        # Статистика
        stats_frame = ttk.Frame(action_frame)
        stats_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.stats_label = ttk.Label(stats_frame, text="Статистика: загрузка...", font=('Segoe UI', 9))
        self.stats_label.pack(side=tk.LEFT)
        
        # Кнопка показа детальной статистики
        self.detail_stats_btn = ttk.Button(
            stats_frame, text="Подробнее", 
            command=self.show_stats,
            width=10
        )
        self.detail_stats_btn.pack(side=tk.RIGHT)
    
    def _create_search_panel(self, parent):
        """Панель поиска и фильтрации."""
        search_frame = ttk.Frame(parent)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="🔍 Поиск:").pack(side=tk.LEFT, padx=(0, 5))
        
        self.search_entry = ttk.Entry(search_frame, textvariable=self.current_filter, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=(0, 10))
        self.search_entry.bind('<KeyRelease>', lambda e: self.refresh_file_list())
        
        self.search_clear_btn = ttk.Button(
            search_frame, text="✖ Очистить", 
            command=self.clear_search,
            width=10
        )
        self.search_clear_btn.pack(side=tk.LEFT)
        
        # Информация о сортировке
        self.sort_info_label = ttk.Label(search_frame, text="Сортировка: по дате (новые сверху)", font=('Segoe UI', 8))
        self.sort_info_label.pack(side=tk.RIGHT, padx=10)
    
    def _create_validation_panel(self, parent):
        """Панель с информацией о валидации."""
        validation_frame = ttk.LabelFrame(parent, text="Параметры валидации", padding="10", style='Card.TLabelframe')
        validation_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Информация о допустимых типах
        types_count = len(self.validator.allowed_types)
        types_text = f"Допустимые типы: {types_count} типов (изображения, PDF, документы, архивы, аудио, видео)"
        ttk.Label(validation_frame, text=types_text, font=('Segoe UI', 9)).pack(anchor=tk.W)
        
        # Информация о размере
        size_text = f"Максимальный размер: {self.validator.max_size // (1024*1024)} МБ (для видео: {self.validator.VIDEO_MAX_SIZE // (1024*1024)} МБ)"
        ttk.Label(validation_frame, text=size_text, font=('Segoe UI', 9)).pack(anchor=tk.W)
        
        # Дополнительная информация
        ttk.Label(validation_frame, text="✓ Проверка MIME-типа | ✓ Проверка размера | ✓ SHA-256 хеширование", 
                 font=('Segoe UI', 8), foreground='#27ae60').pack(anchor=tk.W, pady=(5, 0))
    
    def _create_file_list_panel(self, parent):
        """Панель со списком файлов."""
        list_frame = ttk.LabelFrame(parent, text="Список загруженных файлов", padding="10", style='Card.TLabelframe')
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # Создание таблицы с возможностью сортировки
        columns = ("name", "size", "type", "date")
        column_headers = {
            "name": "Имя файла",
            "size": "Размер",
            "type": "Тип",
            "date": "Дата загрузки"
        }
        
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # Настройка колонок
        for col in columns:
            self.tree.heading(col, text=column_headers[col], 
                            command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=250 if col == "name" else 120)
        
        # Полосы прокрутки
        scrollbar_y = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        scrollbar_x = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # Размещение
        self.tree.grid(row=0, column=0, sticky="nsew")
        scrollbar_y.grid(row=0, column=1, sticky="ns")
        scrollbar_x.grid(row=1, column=0, sticky="ew")
        
        list_frame.grid_rowconfigure(0, weight=1)
        list_frame.grid_columnconfigure(0, weight=1)
        
        # Привязка событий
        self.tree.bind('<<TreeviewSelect>>', self.on_file_select)
        self.tree.bind('<Double-1>', self.on_file_double_click)
        self.tree.bind('<Button-3>', self.show_context_menu)  # Правая кнопка мыши
    
    def _create_status_panel(self, parent):
        """Нижняя панель с логами и статусом."""
        # Панель с логами
        log_frame = ttk.LabelFrame(parent, text="Лог операций", padding="10", style='Card.TLabelframe')
        log_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Текстовое поле для логов
        self.log_text = scrolledtext.ScrolledText(
            log_frame, height=6, wrap=tk.WORD,
            font=('Consolas', 9), bg='#1e1e1e', fg='#d4d4d4'
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Настройка тегов для цветов
        self.log_text.tag_config("error", foreground="#f48771")
        self.log_text.tag_config("success", foreground="#6a9955")
        self.log_text.tag_config("warning", foreground="#dcdcaa")
        self.log_text.tag_config("info", foreground="#9cdcfe")
        
        # Статусбар
        status_frame = ttk.Frame(parent)
        status_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.status_var = tk.StringVar(value="Готов к работе")
        status_bar = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Индикатор количества файлов
        self.count_label = ttk.Label(status_frame, text="", font=('Segoe UI', 9))
        self.count_label.pack(side=tk.RIGHT, padx=10)
    
    def sort_by_column(self, column: str):
        """Сортировка таблицы по колонке."""
        # Инвертирование направления сортировки при повторном клике
        if self.current_sort_column == column:
            self.current_sort_reverse = not self.current_sort_reverse
        else:
            self.current_sort_column = column
            self.current_sort_reverse = False
        
        # Обновление информации о сортировке
        sort_direction = "по убыванию" if self.current_sort_reverse else "по возрастанию"
        self.sort_info_label.config(text=f"Сортировка: по {column} ({sort_direction})")
        
        # Обновление списка
        self.refresh_file_list()
    
    def clear_search(self):
        """Очистка поискового запроса."""
        self.current_filter.set("")
        self.search_entry.delete(0, tk.END)
        self.refresh_file_list()
    
    def show_context_menu(self, event):
        """Показ контекстного меню."""
        # Выделение элемента под курсором
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            
            context_menu = tk.Menu(self.root, tearoff=0)
            context_menu.add_command(label="Удалить файл", command=self.delete_file)
            context_menu.add_command(label="Информация о файле", command=lambda: self.show_file_info())
            context_menu.add_separator()
            context_menu.add_command(label="Обновить список", command=self.refresh_file_list)
            
            context_menu.post(event.x_root, event.y_root)
    
    def show_file_info(self):
        """Отображение подробной информации о файле."""
        selection = self.tree.selection()
        if not selection:
            return
        
        item = self.tree.item(selection[0])
        file_id = item.get('tags', [''])[0] if item.get('tags') else None
        
        if file_id:
            file_info = self.storage.get_file(file_id)
            if file_info:
                info_text = f"""
╔══════════════════════════════════════════════════════════════╗
║                    ИНФОРМАЦИЯ О ФАЙЛЕ                        ║
╠══════════════════════════════════════════════════════════════╣
║ Оригинальное имя: {file_info.original_name}
║ Уникальный ID:    {file_info.id}
║ Размер:           {file_info.get_size_str()}
║ Тип файла:        {file_info.file_type}
║ Дата загрузки:    {file_info.upload_date}
║ Хеш (SHA-256):    {file_info.file_hash[:32]}...
╚══════════════════════════════════════════════════════════════╝
"""
                messagebox.showinfo("Информация о файле", info_text)
    
    def log_message(self, message: str, level: str = "INFO"):
        """
        Добавление сообщения в лог.
        
        Args:
            message: Текст сообщения
            level: Уровень сообщения (INFO, SUCCESS, ERROR, WARNING)
        """
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Определение символа для уровня
        level_symbols = {
            "INFO": "ℹ",
            "SUCCESS": "✓",
            "ERROR": "✗",
            "WARNING": "⚠"
        }
        symbol = level_symbols.get(level, "•")
        
        log_entry = f"[{timestamp}] [{symbol}] {message}\n"
        
        self.log_text.insert(tk.END, log_entry)
        self.log_text.see(tk.END)
        
        # Применение цвета
        tag = level.lower()
        if tag in self.log_text.tag_names():
            line_start = f"end-{len(log_entry)}c"
            line_end = "end-1c"
            self.log_text.tag_add(tag, line_start, line_end)
        
        logger.info(message)
    
    def clear_logs(self):
        """Очистка лога."""
        self.log_text.delete(1.0, tk.END)
        self.log_message("Лог очищен", "INFO")
    
    def update_stats(self):
        """Обновление статистики."""
        stats = self.storage.get_stats()
        self.stats_label.config(
            text=f"📊 Статистика: {stats['total_files']} файлов, {stats['total_size_str']}"
        )
        self.count_label.config(text=f"Всего файлов: {stats['total_files']}")
    
    def show_stats(self):
        """Отображение детальной статистики."""
        stats = self.storage.get_stats()
        files = self.storage.get_all_files()
        
        # Подсчёт типов файлов
        type_counts = {}
        for f in files:
            file_type = f.file_type.split('/')[-1] if '/' in f.file_type else f.file_type
            type_counts[file_type] = type_counts.get(file_type, 0) + 1
        
        type_stats = "\n".join([f"   • {t}: {c} шт." for t, c in sorted(type_counts.items(), key=lambda x: -x[1])[:10]])
        
        stats_text = f"""
╔══════════════════════════════════════════════════════════════╗
║                    СТАТИСТИКА ХРАНИЛИЩА                      ║
╠══════════════════════════════════════════════════════════════╣
║ Всего файлов:      {stats['total_files']}
║ Общий размер:      {stats['total_size_str']}
║ Дата создания:     {stats.get('created_at', 'Н/Д')}
║ Последнее обновление: {stats.get('last_updated', 'Н/Д')}
╠══════════════════════════════════════════════════════════════╣
║ РАСПРЕДЕЛЕНИЕ ПО ТИПАМ:
{type_stats if type_stats else '   • Нет файлов'}
╚══════════════════════════════════════════════════════════════╝
"""
        messagebox.showinfo("Статистика хранилища", stats_text)
    
    def refresh_file_list(self):
        """Обновление списка файлов."""
        # Очистка таблицы
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Получение и фильтрация файлов
        files = self.storage.get_all_files()
        
        # Поисковая фильтрация
        search_query = self.current_filter.get().strip().lower()
        if search_query:
            files = [f for f in files if search_query in f.original_name.lower()]
            self.log_message(f"Найдено {len(files)} файлов по запросу '{search_query}'", "INFO")
        
        # Сортировка
        if self.current_sort_column == "name":
            files.sort(key=lambda x: x.original_name.lower(), reverse=self.current_sort_reverse)
        elif self.current_sort_column == "size":
            files.sort(key=lambda x: x.size, reverse=self.current_sort_reverse)
        elif self.current_sort_column == "type":
            files.sort(key=lambda x: x.file_type, reverse=self.current_sort_reverse)
        elif self.current_sort_column == "date":
            files.sort(key=lambda x: x.upload_date, reverse=self.current_sort_reverse)
        
        # Заполнение таблицы
        for file_info in files:
            self.tree.insert("", tk.END, values=(
                file_info.original_name,
                file_info.get_size_str(),
                file_info.file_type.split('/')[-1] if '/' in file_info.file_type else file_info.file_type[:10],
                file_info.upload_date
            ), tags=(file_info.id,))
        
        self.update_stats()
        
        # Информация о фильтрации
        if search_query:
            self.status_var.set(f"Найдено {len(files)} файлов по запросу '{search_query}'")
        else:
            self.status_var.set(f"Загружено {len(files)} файлов")
    
    def upload_file(self):
        """Загрузка файла."""
        file_path = filedialog.askopenfilename(
            title="Выберите файл для загрузки",
            filetypes=[
                ("Все поддерживаемые файлы", "*.*"),
                ("Изображения", "*.jpg *.jpeg *.png *.gif *.bmp *.webp"),
                ("Документы", "*.pdf *.doc *.docx *.txt *.rtf"),
                ("Архивы", "*.zip *.rar *.7z"),
                ("Аудио", "*.mp3 *.wav *.ogg"),
                ("Видео", "*.mp4 *.avi *.mov")
            ]
        )
        
        if not file_path:
            return
        
        self.status_var.set("Проверка файла...")
        self.root.update()
        
        # Валидация файла
        is_valid, message, details = self.validator.validate_file(file_path)
        
        if not is_valid:
            self.log_message(f"Ошибка валидации: {message}", "ERROR")
            messagebox.showerror("Ошибка валидации", message)
            self.status_var.set("Ошибка валидации")
            return
        
        # Детальный вывод результатов валидации
        self.log_message(f"Валидация пройдена: {message}", "SUCCESS")
        self.log_message(f"  - Тип файла: {details['mime_type']}")
        self.log_message(f"  - Размер: {details['size_message']}")
        
        self.status_var.set("Сохранение файла...")
        self.root.update()
        
        # Сохранение файла
        file_info = self.storage.save_file(file_path)
        
        if file_info:
            self.log_message(f"Файл успешно загружен: {file_info.original_name}", "SUCCESS")
            self.status_var.set(f"Файл '{file_info.original_name}' загружен")
            self.refresh_file_list()
            messagebox.showinfo("Успех", f"Файл '{os.path.basename(file_path)}' успешно загружен!")
        else:
            self.log_message(f"Ошибка сохранения файла", "ERROR")
            self.status_var.set("Ошибка сохранения")
            messagebox.showerror("Ошибка", "Не удалось сохранить файл")
    
    def delete_file(self):
        """Удаление выбранного файла."""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Внимание", "Выберите файл для удаления")
            return
        
        # Получение ID файла из тегов
        item = self.tree.item(selection[0])
        file_id = item['tags'][0] if item['tags'] else None
        
        if file_id:
            file_info = self.storage.get_file(file_id)
            if file_info:
                confirm = messagebox.askyesno(
                    "Подтверждение удаления",
                    f"Вы действительно хотите удалить файл '{file_info.original_name}'?\n\n"
                    f"Размер: {file_info.get_size_str()}\n"
                    f"Дата загрузки: {file_info.upload_date}"
                )
                if confirm:
                    success, msg = self.storage.delete_file(file_id)
                    if success:
                        self.log_message(msg, "SUCCESS")
                        self.refresh_file_list()
                        self.status_var.set(f"Файл удалён")
                    else:
                        self.log_message(f"Ошибка удаления: {msg}", "ERROR")
                        messagebox.showerror("Ошибка", msg)
    
    def export_metadata(self):
        """Экспорт метаданных."""
        file_path = filedialog.asksaveasfilename(
            title="Сохранить метаданные",
            defaultextension=".json",
            filetypes=[("JSON файлы", "*.json"), ("Все файлы", "*.*")]
        )
        
        if file_path:
            if self.storage.export_metadata(file_path):
                self.log_message(f"Метаданные экспортированы: {file_path}", "SUCCESS")
                messagebox.showinfo("Успех", f"Метаданные сохранены в:\n{file_path}")
            else:
                self.log_message("Ошибка экспорта метаданных", "ERROR")
                messagebox.showerror("Ошибка", "Не удалось экспортировать метаданные")
    
    def on_file_select(self, event):
        """Обработка выбора файла."""
        selection = self.tree.selection()
        if selection:
            self.status_var.set("Файл выбран. Нажмите 'Удалить' для удаления или дважды кликните для просмотра информации")
    
    def on_file_double_click(self, event):
        """Обработка двойного клика по файлу."""
        self.show_file_info()
    
    def show_about(self):
        """Отображение информации о программе."""
        about_text = """
╔══════════════════════════════════════════════════════════════╗
║              МЕНЕДЖЕР ФАЙЛОВ v1.0.0                         ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Разработка модуля загрузки, хранения и валидации файлов    ║
║                                                              ║
║  Функции:                                                    ║
║    • Загрузка файлов с валидацией типа и размера            ║
║    • Хранение файлов с уникальными именами                  ║
║    • Сохранение метаданных в JSON                           ║
║    • SHA-256 хеширование файлов                             ║
║    • Поиск и фильтрация                                     ║
║    • Сортировка по столбцам                                 ║
║    • Экспорт метаданных                                     ║
║                                                              ║
║  Технологии: Python 3.11+, Tkinter, JSON, SHA-256           ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
        messagebox.showinfo("О программе", about_text)
    
    def on_closing(self):
        """Обработка закрытия приложения."""
        if messagebox.askokcancel("Выход", "Вы уверены, что хотите выйти?"):
            self.log_message("Приложение закрыто", "INFO")
            self.root.destroy()
    
    def run(self):
        """Запуск приложения."""
        self.log_message("Приложение запущено. Модуль готов к работе.", "SUCCESS")
        self.log_message(f"Хранилище: {self.storage.storage_path.absolute()}", "INFO")
        self.root.mainloop()


# ============================================================
# ТОЧКА ВХОДА
# ============================================================

def main():
    """Точка входа в приложение."""
    try:
        app = FileManagerApp()
        app.run()
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        messagebox.showerror("Критическая ошибка", f"Произошла ошибка при запуске приложения:\n{e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
