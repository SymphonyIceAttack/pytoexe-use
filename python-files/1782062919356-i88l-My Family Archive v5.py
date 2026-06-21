import os
import time
import shutil
import hashlib
import queue
import threading
import tkinter as tk

from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from tkinter import ttk, filedialog, messagebox


APP_NAME = "My Family Archive v5"
APP_VERSION = "v5"

APP_FOLDERS = [
    "Фото",
    "Видео",
    "Музыка",
    "Документы",
    "Прочее",
    "Сейф",
    "Рабочий",
]

DUPLICATES_FOLDER_NAME = "Дубли"
LEGACY_DUPLICATE_ROOT_NAMES = {"дубль", "дубли"}


# Папки, которые часто автоматически создают телевизоры, телефоны, планшеты,
# медиаплееры, Windows/macOS/Linux. Их можно безопасно удалять кнопкой проверки,
# если они находятся в корне выбранного архива/накопителя.
AUTO_JUNK_ROOT_NAMES = {
    "$recycle.bin",
    "system volume information",
    "lost.dir",
    "android",
    ".thumbnails",
    ".trash",
    ".trashes",
    ".spotlight-v100",
    ".fseventsd",
    ".temporaryitems",
    "recycled",
    "found.000",
    "found.001",
}

APP_FOLDER_NAMES_LOWER = {name.lower() for name in APP_FOLDERS}

SYSTEM_DIR_NAMES = {
    "$recycle.bin",
    "system volume information",
    "windows",
    "program files",
    "program files (x86)",
    "programdata",
    "appdata",
    ".git",
    ".svn",
    "__pycache__",
}

TEMP_EXTENSIONS = {
    ".tmp", ".temp", ".part", ".crdownload", ".download",
    ".lnk", ".ini", ".db", ".sys",
}

PHOTO_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tif", ".webp",
    ".heic", ".raw", ".cr2", ".nef", ".arw", ".dng"
}

VIDEO_EXTENSIONS = {
    ".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv",
    ".mpeg", ".mpg", ".3gp", ".webm", ".m4v"
}

MUSIC_EXTENSIONS = {
    ".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".wma", ".alac"
}

DOCUMENT_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".txt", ".rtf", ".odt", ".ods", ".odp", ".csv", ".epub", ".fb2"
}


def get_app_dir() -> Path:
    return Path(__file__).resolve().parent


def get_icon_path() -> Path | None:
    app_dir = get_app_dir()
    candidates = [
        app_dir / "Icon.ico",
        app_dir / "icon.ico",
        app_dir / "ICON.ico",
    ]
    for path in candidates:
        if path.exists() and path.is_file():
            return path
    return None


def set_hidden_windows(path: Path):
    """Скрывает папку в Windows. На других системах просто ничего не делает."""
    try:
        if os.name == "nt" and path.exists():
            import ctypes
            FILE_ATTRIBUTE_HIDDEN = 0x02
            FILE_ATTRIBUTE_NOT_CONTENT_INDEXED = 0x2000
            attrs = ctypes.windll.kernel32.GetFileAttributesW(str(path))
            if attrs != -1:
                ctypes.windll.kernel32.SetFileAttributesW(
                    str(path),
                    attrs | FILE_ATTRIBUTE_HIDDEN | FILE_ATTRIBUTE_NOT_CONTENT_INDEXED
                )
    except Exception:
        pass


def unique_path(folder: Path, name: str) -> Path:
    candidate = folder / name
    if not candidate.exists():
        return candidate

    stem = candidate.stem
    suffix = candidate.suffix
    i = 1

    while True:
        new_candidate = folder / f"{stem}__{i}{suffix}"
        if not new_candidate.exists():
            return new_candidate
        i += 1


class FileStatus(str, Enum):
    FOUND = "FOUND"
    VERIFIED = "VERIFIED"
    SORTED = "SORTED"
    DUPLICATE = "DUPLICATE"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


@dataclass
class FileRecord:
    source_path: Path
    file_name: str
    extension: str
    size: int
    created_time: float
    modified_time: float
    category: str
    copied_path: Path | None = None
    final_path: Path | None = None
    status: FileStatus = FileStatus.FOUND
    error: str = ""


def classify_file(path: Path) -> str:
    ext = path.suffix.lower()

    if ext in PHOTO_EXTENSIONS:
        return "Фото"
    if ext in VIDEO_EXTENSIONS:
        return "Видео"
    if ext in MUSIC_EXTENSIONS:
        return "Музыка"
    if ext in DOCUMENT_EXTENSIONS:
        return "Документы"

    return "Прочее"


def sha256_file(path: Path, stop_event: threading.Event) -> str:
    h = hashlib.sha256()

    with open(path, "rb") as f:
        while True:
            if stop_event.is_set():
                raise RuntimeError("Операция остановлена пользователем.")

            chunk = f.read(1024 * 1024)
            if not chunk:
                break

            h.update(chunk)

    return h.hexdigest()


def verify_copy(source: Path, destination: Path, stop_event: threading.Event, deep_hash: bool) -> bool:
    if not destination.exists():
        return False

    if source.stat().st_size != destination.stat().st_size:
        return False

    if deep_hash:
        return sha256_file(source, stop_event) == sha256_file(destination, stop_event)

    return True


def format_size(size: int) -> str:
    value = float(size)
    for unit in ["Б", "КБ", "МБ", "ГБ", "ТБ"]:
        if value < 1024:
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} ПБ"


class AppEngine:
    def __init__(self, ui_queue: queue.Queue):
        self.ui_queue = ui_queue
        self.stop_event = threading.Event()
        self.records: list[FileRecord] = []
        self.source_path: Path | None = None
        self.target_path: Path | None = None
        self.deep_hash = False
        self.max_workers = 4
        self.allowed_categories: set[str] | None = None
        self.category_filter_enabled = False
        self.selected_categories: set[str] = set()
        self.start_time = 0
        self.last_log_time = 0

    def log(self, text: str):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.ui_queue.put(("log", f"{timestamp} — {text}"))

    def ui(self, kind: str, data):
        self.ui_queue.put((kind, data))

    def request_stop(self):
        self.stop_event.set()
        self.log("⛔ Запрошена безопасная остановка.")

    def start(
        self,
        source: str,
        target: str,
        deep_hash: bool,
        max_workers: int,
        category_filter_enabled: bool = False,
        selected_categories: set[str] | None = None,
    ):
        self.source_path = Path(source)
        self.target_path = Path(target)
        self.deep_hash = deep_hash
        self.max_workers = max_workers
        self.category_filter_enabled = category_filter_enabled
        self.selected_categories = selected_categories or set()
        self.stop_event.clear()

        thread = threading.Thread(target=self._run_scan_stage, daemon=True)
        thread.start()

    def continue_after_scan(self):
        thread = threading.Thread(target=self._run_copy_sort_stage, daemon=True)
        thread.start()

    def cancel_after_scan(self):
        self.records = []
        self.log("Копирование отменено. Список найденных файлов очищен.")
        self.ui("finished", "Готово")

    def ensure_structure(self):
        assert self.target_path is not None

        if not self.target_path.exists():
            raise FileNotFoundError(f"Папка назначения не найдена: {self.target_path}")

        if not self.target_path.is_dir():
            raise NotADirectoryError(f"Назначение не является папкой: {self.target_path}")

        test_file = self.target_path / ".mfa_write_test.tmp"

        try:
            test_file.write_text("test", encoding="utf-8")
            test_file.unlink(missing_ok=True)
        except Exception as e:
            raise PermissionError(f"Нет прав записи в папку назначения: {e}")

        for folder in APP_FOLDERS:
            (self.target_path / folder).mkdir(parents=True, exist_ok=True)

        work_dir = self.target_path / "Рабочий"
        work_dir.mkdir(parents=True, exist_ok=True)
        set_hidden_windows(work_dir)

        duplicate_dir = self.target_path / "Прочее" / DUPLICATES_FOLDER_NAME
        duplicate_dir.mkdir(parents=True, exist_ok=True)

        self.log("✅ Структура каталогов проверена/создана. Папка Рабочий скрыта, дубли хранятся в Прочее/Дубли.")

    def migrate_legacy_duplicates(self):
        """Переносит старые корневые папки Дубль/Дубли в Прочее/Дубли без удаления содержимого."""
        assert self.target_path is not None

        target_duplicate_dir = self.target_path / "Прочее" / DUPLICATES_FOLDER_NAME
        target_duplicate_dir.mkdir(parents=True, exist_ok=True)

        moved = 0
        errors = 0

        for legacy_name in ("Дубль", "Дубли"):
            legacy_dir = self.target_path / legacy_name

            if not legacy_dir.exists() or not legacy_dir.is_dir():
                continue

            # Если это уже та же папка по пути — ничего не делаем.
            if legacy_dir.resolve() == target_duplicate_dir.resolve():
                continue

            self.log(f"Найдена старая папка дублей в корне: {legacy_dir.name}. Перенос в Прочее/{DUPLICATES_FOLDER_NAME}.")

            for child in list(legacy_dir.iterdir()):
                try:
                    target = unique_path(target_duplicate_dir, child.name)
                    shutil.move(str(child), str(target))
                    moved += 1
                except Exception as e:
                    errors += 1
                    self.log(f"⚠ Не удалось перенести {child}: {e}")

            try:
                legacy_dir.rmdir()
                self.log(f"Пустая корневая папка {legacy_dir.name} удалена.")
            except OSError:
                self.log(f"⚠ Корневая папка {legacy_dir.name} не удалена, потому что она не пустая.")
            except Exception as e:
                errors += 1
                self.log(f"⚠ Не удалось удалить пустую папку {legacy_dir.name}: {e}")

        return moved, errors

    def clean_root_structure(self):
        """
        Проверяет структуру архива и очищает корень выбранного накопителя.
        После очистки в корне остаются только проектные папки:
        Фото, Видео, Музыка, Документы, Прочее, Сейф, Рабочий.

        ВАЖНО:
        - очистка работает только в корне выбранного назначения;
        - проектные папки не удаляются;
        - старые корневые папки Дубль/Дубли не удаляются, а переносятся в Прочее/Дубли;
        - всё остальное в корне удаляется: лишние папки, файлы, ярлыки;
        - внутри проектных папок очистка не выполняется.
        """
        assert self.target_path is not None

        self.ensure_structure()
        migrated_duplicates, migration_errors = self.migrate_legacy_duplicates()

        removed = 0
        skipped = 0
        errors = 0

        self.log("🧹 Проверка и очистка корня архива начата.")
        self.log("В корне останутся только папки проекта: Фото, Видео, Музыка, Документы, Прочее, Сейф, Рабочий.")
        if migrated_duplicates:
            self.log(f"Перенесено элементов из старой папки дублей: {migrated_duplicates}")

        for item in self.target_path.iterdir():
            name_lower = item.name.lower()

            if name_lower in APP_FOLDER_NAMES_LOWER:
                continue

            try:
                if item.is_file() or item.is_symlink():
                    item.unlink()
                    removed += 1
                    self.log(f"Удалён лишний файл из корня: {item.name}")
                    continue

                if item.is_dir():
                    shutil.rmtree(item)
                    removed += 1
                    self.log(f"Удалена лишняя папка из корня: {item.name}")
                    continue

                skipped += 1
                self.log(f"Пропущен неизвестный объект: {item.name}")

            except Exception as e:
                errors += 1
                self.log(f"⚠ Не удалось удалить {item.name}: {e}")

        errors += migration_errors
        self.log(f"✅ Очистка завершена. Удалено: {removed}, пропущено: {skipped}, ошибок: {errors}")
        return removed, skipped, errors

    def run_structure_check_only(self, target: str):
        self.target_path = Path(target)
        self.stop_event.clear()
        thread = threading.Thread(target=self._run_structure_check_only_stage, daemon=True)
        thread.start()

    def _run_structure_check_only_stage(self):
        try:
            self.ui("state", "Проверка структуры")
            result = self.clean_root_structure()
            self.ui("structure_checked", result)
        except Exception as e:
            self.log(f"❌ Ошибка проверки структуры: {e}")
            self.ui("error", str(e))

    def _should_skip_dir(self, path: Path) -> bool:
        name = path.name.lower()
        return name in SYSTEM_DIR_NAMES or name.startswith(".")

    def _should_skip_file(self, path: Path) -> bool:
        if path.name.startswith("~$"):
            return True

        if path.suffix.lower() in TEMP_EXTENSIONS:
            return True

        return False

    def scan_files(self) -> list[FileRecord]:
        assert self.source_path is not None

        records = []
        count = 0
        total_size = 0
        last_log = time.time()

        self.log(f"🔎 Сканирование источника: {self.source_path}")

        for root, dirs, files in os.walk(self.source_path):
            if self.stop_event.is_set():
                self.log("Сканирование остановлено.")
                break

            root_path = Path(root)
            dirs[:] = [d for d in dirs if not self._should_skip_dir(root_path / d)]

            now = time.time()
            if now - last_log >= 1:
                self.log(f"Сканирование папки: {root_path}")
                last_log = now

            for file_name in files:
                if self.stop_event.is_set():
                    break

                path = root_path / file_name

                if self._should_skip_file(path):
                    continue

                try:
                    stat = path.stat()

                    if stat.st_size <= 0:
                        continue

                    record = FileRecord(
                        source_path=path,
                        file_name=path.name,
                        extension=path.suffix.lower(),
                        size=stat.st_size,
                        created_time=stat.st_ctime,
                        modified_time=stat.st_mtime,
                        category=classify_file(path),
                    )

                    if self.category_filter_enabled and record.category not in self.selected_categories:
                        continue

                    if self.allowed_categories is not None and record.category not in self.allowed_categories:
                        continue

                    records.append(record)
                    count += 1
                    total_size += stat.st_size

                    if count % 25 == 0:
                        self.ui("scan_progress", (count, str(path), format_size(total_size)))

                    if count % 250 == 0:
                        self.log(f"Найдено файлов: {count}, общий размер: {format_size(total_size)}")

                except PermissionError:
                    self.log(f"⚠ Нет доступа к файлу, пропущен: {path}")
                except Exception as e:
                    self.log(f"⚠ Ошибка сканирования файла {path}: {e}")

        self.log(f"✅ Сканирование завершено. Найдено файлов: {len(records)}, размер: {format_size(total_size)}")
        return records

    def _unique_path(self, folder: Path, name: str) -> Path:
        candidate = folder / name

        if not candidate.exists():
            return candidate

        stem = candidate.stem
        suffix = candidate.suffix
        i = 1

        while True:
            new_candidate = folder / f"{stem}__{i}{suffix}"
            if not new_candidate.exists():
                return new_candidate
            i += 1

    def copy_one(self, record: FileRecord) -> FileRecord:
        assert self.target_path is not None

        if self.stop_event.is_set():
            record.status = FileStatus.SKIPPED
            return record

        work_dir = self.target_path / "Рабочий"
        duplicate_dir = self.target_path / "Прочее" / DUPLICATES_FOLDER_NAME

        work_dir.mkdir(parents=True, exist_ok=True)
        set_hidden_windows(work_dir)
        duplicate_dir.mkdir(parents=True, exist_ok=True)

        try:
            normal_target = work_dir / record.file_name

            if normal_target.exists():
                target = self._unique_path(duplicate_dir, record.file_name)
                record.status = FileStatus.DUPLICATE
            else:
                target = normal_target

            temp_target = target.with_name(target.name + ".copying")

            shutil.copy2(record.source_path, temp_target)

            if not verify_copy(record.source_path, temp_target, self.stop_event, self.deep_hash):
                temp_target.unlink(missing_ok=True)
                raise RuntimeError("Проверка копии не пройдена.")

            temp_target.replace(target)

            record.copied_path = target

            if record.status != FileStatus.DUPLICATE:
                record.status = FileStatus.VERIFIED

            return record

        except Exception as e:
            record.status = FileStatus.ERROR
            record.error = str(e)
            return record

    def copy_files(self) -> list[FileRecord]:
        total = len(self.records)
        done = 0
        results = []
        copied_bytes = 0
        last_log = time.time()

        self.log(f"📦 Копирование начато. Файлов: {total}")

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self.copy_one, record) for record in self.records]

            for future in as_completed(futures):
                record = future.result()
                results.append(record)
                done += 1

                if record.copied_path:
                    copied_bytes += record.size

                if record.status == FileStatus.ERROR:
                    self.log(f"❌ Ошибка копирования: {record.source_path} — {record.error}")

                now = time.time()
                if now - last_log >= 1 or done == total:
                    self.log(f"Копирование: {done}/{total}, обработано {format_size(copied_bytes)}")
                    last_log = now

                self.ui("copy_progress", (done, total, str(record.source_path), format_size(copied_bytes)))

                if self.stop_event.is_set():
                    self.log("Остановка: текущие копирования завершаются.")
                    break

        self.log("✅ Копирование завершено.")
        return results

    def get_sort_target(self, record: FileRecord) -> Path:
        assert self.target_path is not None

        year = datetime.fromtimestamp(record.modified_time).year
        ext_folder = record.extension.lower().lstrip(".") or "no_extension"

        if record.category in ("Фото", "Видео", "Музыка"):
            folder = self.target_path / record.category / str(year)
        elif record.category == "Документы":
            folder = self.target_path / "Документы" / ext_folder / str(year)
        else:
            folder = self.target_path / "Прочее" / ext_folder

        folder.mkdir(parents=True, exist_ok=True)

        return self._unique_path(folder, record.file_name)

    def sort_files(self):
        total = len(self.records)
        sorted_count = 0
        last_log = time.time()

        self.log("🗂 Сортировка начата.")

        for index, record in enumerate(self.records, start=1):
            if self.stop_event.is_set():
                self.log("Сортировка остановлена.")
                break

            if not record.copied_path:
                continue

            if record.status in (FileStatus.DUPLICATE, FileStatus.ERROR, FileStatus.SKIPPED):
                continue

            try:
                target = self.get_sort_target(record)
                shutil.move(str(record.copied_path), str(target))

                record.final_path = target
                record.status = FileStatus.SORTED
                sorted_count += 1

                now = time.time()
                if now - last_log >= 1 or index == total:
                    self.log(f"Сортировка: {index}/{total}, отсортировано {sorted_count}")
                    last_log = now

                self.ui("sort_progress", (index, total, record.file_name))

            except Exception as e:
                record.status = FileStatus.ERROR
                record.error = str(e)
                self.log(f"❌ Ошибка сортировки: {record.copied_path} — {e}")

        self.log(f"✅ Сортировка завершена. Отсортировано: {sorted_count}")

    def cleanup_work_dir(self):
        assert self.target_path is not None

        work_dir = self.target_path / "Рабочий"

        if not work_dir.exists():
            return

        for item in work_dir.iterdir():
            try:
                if item.is_file() or item.is_symlink():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception as e:
                self.log(f"⚠ Не удалось очистить Рабочий: {item} — {e}")

        self.log("✅ Папка Рабочий очищена.")

    def build_report(self) -> tuple[str, Path]:
        assert self.target_path is not None

        elapsed = time.time() - self.start_time

        found = len(self.records)
        copied = sum(1 for r in self.records if r.copied_path is not None)
        sorted_count = sum(1 for r in self.records if r.status == FileStatus.SORTED)
        duplicates = sum(1 for r in self.records if r.status == FileStatus.DUPLICATE)
        skipped = sum(1 for r in self.records if r.status == FileStatus.SKIPPED)
        errors = sum(1 for r in self.records if r.status == FileStatus.ERROR)

        text = "\n".join([
            "My Family Archive версии 5 — отчёт",
            "=" * 40,
            f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Найдено файлов: {found}",
            f"Скопировано: {copied}",
            f"Отсортировано: {sorted_count}",
            f"Дублей: {duplicates}",
            f"Пропущено: {skipped}",
            f"Ошибок: {errors}",
            f"Время выполнения: {elapsed:.1f} сек.",
        ])

        if errors:
            text += "\n\nОшибки:\n"
            for r in self.records:
                if r.status == FileStatus.ERROR:
                    text += f"- {r.source_path}: {r.error}\n"

        report_dir = self.target_path / "Сейф" / "Reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        report_path = report_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        report_path.write_text(text, encoding="utf-8")

        return text, report_path

    def _run_scan_stage(self):
        try:
            self.start_time = time.time()

            self.ui("state", "Проверка накопителя")
            self.ensure_structure()

            if self.stop_event.is_set():
                self.ui("finished", "Остановлено")
                return

            self.ui("state", "Сканирование")
            self.records = self.scan_files()

            if self.stop_event.is_set():
                self.ui("finished", "Остановлено")
                return

            self.ui("confirm_copy", len(self.records))

        except Exception as e:
            self.log(f"❌ Ошибка: {e}")
            self.ui("error", str(e))

    def _run_copy_sort_stage(self):
        try:
            if not self.records:
                self.ui("finished", "Нет файлов для обработки")
                return

            self.ui("state", "Копирование")
            self.records = self.copy_files()

            if self.stop_event.is_set():
                self.ui("finished", "Остановлено")
                return

            self.ui("state", "Сортировка")
            self.sort_files()

            if self.stop_event.is_set():
                self.ui("finished", "Остановлено")
                return

            self.ui("state", "Отчёт")
            report_text, report_path = self.build_report()

            self.cleanup_work_dir()

            self.ui("report", (report_text, str(report_path)))

        except Exception as e:
            self.log(f"❌ Ошибка: {e}")
            self.ui("error", str(e))


class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title(APP_NAME)
        self.geometry("1060x740")
        self.minsize(940, 650)

        self.set_window_icon()

        self.ui_queue = queue.Queue()
        self.engine = AppEngine(self.ui_queue)

        self.source_var = tk.StringVar()
        self.target_var = tk.StringVar()
        self.state_var = tk.StringVar(value="Готово")
        self.current_file_var = tk.StringVar(value="-")
        self.progress_var = tk.DoubleVar(value=0)
        self.deep_hash_var = tk.BooleanVar(value=False)
        self.workers_var = tk.IntVar(value=4)
        self.pc_power_var = tk.StringVar(value="medium")
        self.category_scan_var = tk.BooleanVar(value=False)
        self.scan_photo_var = tk.BooleanVar(value=True)
        self.scan_video_var = tk.BooleanVar(value=True)
        self.scan_music_var = tk.BooleanVar(value=True)
        self.scan_documents_var = tk.BooleanVar(value=True)
        self.category_filter_var = tk.BooleanVar(value=False)
        self.category_photo_var = tk.BooleanVar(value=True)
        self.category_video_var = tk.BooleanVar(value=True)
        self.category_music_var = tk.BooleanVar(value=True)
        self.category_docs_var = tk.BooleanVar(value=True)
        self.threads_info_var = tk.StringVar(value="Сейчас: 4 потока")

        self.setup_style()
        self.build_ui()
        self.workers_var.trace_add("write", self.update_threads_info)
        self.update_threads_info()

        self.after(100, self.poll_queue)

    def set_window_icon(self):
        icon_path = get_icon_path()
        if icon_path is None:
            return
        try:
            self.iconbitmap(str(icon_path))
        except Exception:
            pass

    def setup_style(self):
        self.colors = {
            "bg": "#1e1f24",
            "panel": "#2a2d34",
            "panel2": "#30343d",
            "text": "#f2f5f7",
            "muted": "#aeb6c2",
            "accent": "#4cc9f0",
            "accent2": "#7c3aed",
            "green": "#22c55e",
            "red": "#ef4444",
            "yellow": "#f59e0b",
            "entry": "#f8fafc",
            "entry_text": "#111827",
            "log_bg": "#0f172a",
            "log_text": "#dbeafe",
        }

        self.configure(bg=self.colors["bg"])

        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=self.colors["bg"], foreground=self.colors["text"])
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("Panel.TFrame", background=self.colors["panel"])
        style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["text"], font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=self.colors["bg"], foreground=self.colors["muted"], font=("Segoe UI", 9))
        style.configure("Panel.TLabel", background=self.colors["panel"], foreground=self.colors["text"], font=("Segoe UI", 10))
        style.configure("Title.TLabel", background=self.colors["bg"], foreground=self.colors["accent"], font=("Segoe UI", 20, "bold"))
        style.configure("Stage.TLabel", background=self.colors["panel"], foreground=self.colors["green"], font=("Segoe UI", 11, "bold"))

        style.configure(
            "TEntry",
            fieldbackground=self.colors["entry"],
            foreground=self.colors["entry_text"],
            insertcolor=self.colors["entry_text"],
            bordercolor=self.colors["accent"],
            lightcolor=self.colors["accent"],
            darkcolor=self.colors["accent"],
            padding=6,
        )

        style.configure(
            "TSpinbox",
            fieldbackground=self.colors["entry"],
            foreground=self.colors["entry_text"],
            insertcolor=self.colors["entry_text"],
            arrowsize=14,
        )

        style.map(
            "TSpinbox",
            fieldbackground=[("readonly", self.colors["entry"]), ("disabled", self.colors["entry"])],
            foreground=[("readonly", self.colors["entry_text"]), ("disabled", self.colors["entry_text"])],
        )

        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=8)
        style.configure("Big.TButton", font=("Segoe UI", 12, "bold"), padding=12)
        style.configure("Accent.TButton", background=self.colors["accent"], foreground="#07111f")
        style.map("Accent.TButton", background=[("active", "#67e8f9")])
        style.configure("Stop.TButton", background=self.colors["red"], foreground="#ffffff")
        style.map("Stop.TButton", background=[("active", "#f87171")])

        style.configure("TCheckbutton", background=self.colors["bg"], foreground=self.colors["text"])
        style.map("TCheckbutton", background=[("active", self.colors["bg"])], foreground=[("active", self.colors["text"])])
        style.configure("TRadiobutton", background=self.colors["bg"], foreground=self.colors["text"])
        style.map("TRadiobutton", background=[("active", self.colors["bg"])], foreground=[("active", self.colors["text"])])
        style.configure(
            "TSpinbox",
            fieldbackground=self.colors["entry"],
            foreground=self.colors["entry_text"],
            insertcolor=self.colors["entry_text"],
            arrowsize=14,
            padding=4,
        )
        style.map(
            "TSpinbox",
            fieldbackground=[("readonly", self.colors["entry"]), ("focus", self.colors["entry"])],
            foreground=[("readonly", self.colors["entry_text"]), ("focus", self.colors["entry_text"])],
        )
        style.configure("Horizontal.TProgressbar", thickness=20, troughcolor=self.colors["panel2"], background=self.colors["green"])

    def make_path_card(self, parent, title, var, button_text, command):
        card = ttk.Frame(parent, style="Panel.TFrame", padding=10)
        card.pack(fill="x", pady=6)

        ttk.Label(card, text=title, style="Panel.TLabel").pack(anchor="w")

        row = ttk.Frame(card, style="Panel.TFrame")
        row.pack(fill="x", pady=(6, 0))

        entry = ttk.Entry(row, textvariable=var, font=("Segoe UI", 10))
        entry.pack(side="left", fill="x", expand=True, ipady=3)
        entry.configure(state="readonly")

        btn = ttk.Button(row, text=button_text, command=command, style="Accent.TButton")
        btn.pack(side="left", padx=(8, 0))

        return entry

    def build_ui(self):
        root = ttk.Frame(self, padding=16)
        root.pack(fill="both", expand=True)

        title = ttk.Label(root, text=APP_NAME, style="Title.TLabel")
        title.pack(anchor="w")

        subtitle = ttk.Label(
            root,
            text="Удобный архиватор для своих семейных архивов",
            style="Muted.TLabel",
        )
        subtitle.pack(anchor="w", pady=(2, 14))

        self.make_path_card(root, "Источник данных", self.source_var, "Выбрать источник", self.choose_source)
        self.make_path_card(root, "Накопитель / папка назначения", self.target_var, "Выбрать назначение", self.choose_target)

        category_main = ttk.Frame(root)
        category_main.pack(fill="x", pady=(8, 4))


        self.category_frame = ttk.Frame(root)

        ttk.Checkbutton(self.category_frame, text="Фото", variable=self.category_photo_var).pack(side="left", padx=(24, 12))
        ttk.Checkbutton(self.category_frame, text="Видео", variable=self.category_video_var).pack(side="left", padx=(0, 12))
        ttk.Checkbutton(self.category_frame, text="Музыка", variable=self.category_music_var).pack(side="left", padx=(0, 12))
        ttk.Checkbutton(self.category_frame, text="Документы", variable=self.category_docs_var).pack(side="left", padx=(0, 12))

        options = ttk.Frame(root)
        options.pack(fill="x", pady=(4, 8))

        category_panel = ttk.Frame(root, style="Panel.TFrame", padding=10)
        category_panel.pack(fill="x", pady=(0, 8))

        ttk.Checkbutton(
            category_panel,
            text="Сканирование по категориям",
            variable=self.category_scan_var,
            command=self.toggle_category_options,
        ).pack(anchor="w")

        self.category_options_frame = ttk.Frame(category_panel, style="Panel.TFrame")

        self.photo_check = ttk.Checkbutton(
            self.category_options_frame,
            text="Фото",
            variable=self.scan_photo_var,
        )
        self.photo_check.pack(side="left", padx=(0, 14))

        self.video_check = ttk.Checkbutton(
            self.category_options_frame,
            text="Видео",
            variable=self.scan_video_var,
        )
        self.video_check.pack(side="left", padx=(0, 14))

        self.music_check = ttk.Checkbutton(
            self.category_options_frame,
            text="Музыка",
            variable=self.scan_music_var,
        )
        self.music_check.pack(side="left", padx=(0, 14))

        self.documents_check = ttk.Checkbutton(
            self.category_options_frame,
            text="Документы",
            variable=self.scan_documents_var,
        )
        self.documents_check.pack(side="left", padx=(0, 14))

        self.toggle_category_options()

        ttk.Checkbutton(
            options,
            text="Более точная проверка на дубли",
            variable=self.deep_hash_var,
        ).pack(side="left")

        ttk.Label(options, text="Потоков:").pack(side="left", padx=(20, 6))

        self.workers_spinbox = tk.Spinbox(
            options,
            from_=1,
            to=16,
            width=5,
            textvariable=self.workers_var,
            command=self.update_threads_info,
            bg=self.colors["entry"],
            fg=self.colors["entry_text"],
            insertbackground=self.colors["entry_text"],
            buttonbackground=self.colors["panel2"],
            relief="flat",
            font=("Segoe UI", 10),
        )
        self.workers_spinbox.pack(side="left")
        self.workers_spinbox.bind("<KeyRelease>", lambda event: self.update_threads_info())
        self.workers_spinbox.bind("<ButtonRelease-1>", lambda event: self.after(50, self.update_threads_info))

        presets = ttk.Frame(root)
        presets.pack(fill="x", pady=(0, 8))

        ttk.Label(presets, text="Мощность компьютера:").pack(side="left", padx=(0, 8))

        ttk.Radiobutton(
            presets,
            text="Слабый / старый ПК",
            variable=self.pc_power_var,
            value="weak",
            command=self.apply_thread_preset,
        ).pack(side="left", padx=(0, 10))

        ttk.Radiobutton(
            presets,
            text="Средний ПК",
            variable=self.pc_power_var,
            value="medium",
            command=self.apply_thread_preset,
        ).pack(side="left", padx=(0, 10))

        ttk.Radiobutton(
            presets,
            text="Современный ПК",
            variable=self.pc_power_var,
            value="modern",
            command=self.apply_thread_preset,
        ).pack(side="left", padx=(0, 10))

        ttk.Label(
            presets,
            textvariable=self.threads_info_var,
            style="Muted.TLabel",
        ).pack(side="left", padx=(8, 0))

        buttons = ttk.Frame(root)
        buttons.pack(fill="x", pady=12)

        self.start_btn = ttk.Button(buttons, text="▶ Старт", style="Big.TButton", width=24, command=self.start)
        self.start_btn.pack(side="left", padx=(0, 10))

        self.check_structure_btn = ttk.Button(
            buttons,
            text="🧹 Проверить структуру",
            style="Accent.TButton",
            width=24,
            command=self.check_structure_only,
        )
        self.check_structure_btn.pack(side="left", padx=(0, 10))

        self.stop_btn = ttk.Button(buttons, text="■ Стоп", style="Stop.TButton", width=24, command=self.stop, state="disabled")
        self.stop_btn.pack(side="left")

        info = ttk.Frame(root, style="Panel.TFrame", padding=10)
        info.pack(fill="x", pady=8)

        ttk.Label(info, text="Текущий этап:", style="Panel.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(info, textvariable=self.state_var, style="Stage.TLabel").grid(row=0, column=1, sticky="w", padx=10)

        ttk.Label(info, text="Текущий файл:", style="Panel.TLabel").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Label(info, textvariable=self.current_file_var, style="Panel.TLabel").grid(row=1, column=1, sticky="w", padx=10, pady=(6, 0))

        info.columnconfigure(1, weight=1)

        self.progress = ttk.Progressbar(root, variable=self.progress_var, maximum=100)
        self.progress.pack(fill="x", pady=8)

        ttk.Label(root, text="Логи:").pack(anchor="w", pady=(10, 4))

        log_frame = ttk.Frame(root)
        log_frame.pack(fill="both", expand=True)

        self.log_text = tk.Text(
            log_frame,
            bg=self.colors["log_bg"],
            fg=self.colors["log_text"],
            insertbackground=self.colors["log_text"],
            relief="flat",
            wrap="word",
            font=("Consolas", 10),
            padx=10,
            pady=10,
        )

        self.log_text.pack(side="left", fill="both", expand=True)

        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scroll.pack(side="right", fill="y")

        self.log_text.configure(yscrollcommand=scroll.set)

    def update_threads_info(self, *args):
        try:
            count = int(self.workers_var.get())
        except Exception:
            count = 0

        if count == 1:
            text = "Сейчас: 1 поток"
        elif 2 <= count <= 4:
            text = f"Сейчас: {count} потока"
        else:
            text = f"Сейчас: {count} потоков"

        self.threads_info_var.set(text)

    def toggle_category_filters(self):
        if self.category_filter_var.get():
            self.category_frame.pack(fill="x", pady=(0, 8))
        else:
            self.category_frame.pack_forget()

    def get_selected_categories(self) -> set[str]:
        selected = set()

        if self.category_photo_var.get():
            selected.add("Фото")
        if self.category_video_var.get():
            selected.add("Видео")
        if self.category_music_var.get():
            selected.add("Музыка")
        if self.category_docs_var.get():
            selected.add("Документы")

        return selected

    def toggle_category_options(self):
        if self.category_scan_var.get():
            self.category_options_frame.pack(fill="x", pady=(8, 0))
            self.photo_check.configure(state="normal")
            self.video_check.configure(state="normal")
            self.music_check.configure(state="normal")
            self.documents_check.configure(state="normal")
        else:
            self.category_options_frame.pack_forget()

    def get_allowed_categories(self):
        if not self.category_scan_var.get():
            return None

        selected = set()

        if self.scan_photo_var.get():
            selected.add("Фото")
        if self.scan_video_var.get():
            selected.add("Видео")
        if self.scan_music_var.get():
            selected.add("Музыка")
        if self.scan_documents_var.get():
            selected.add("Документы")

        return selected

    def apply_thread_preset(self):
        preset = self.pc_power_var.get()

        if preset == "weak":
            self.workers_var.set(2)
            self.append_log("Выбран пресет: слабый / старый ПК — 2 потока.")
        elif preset == "medium":
            self.workers_var.set(4)
            self.append_log("Выбран пресет: средний ПК — 4 потока.")
        elif preset == "modern":
            self.workers_var.set(8)
            self.append_log("Выбран пресет: современный ПК — 8 потоков.")

    def check_structure_only(self):
        target = self.target_var.get().strip()

        if not target or not os.path.isdir(target):
            messagebox.showerror("Ошибка", "Сначала выберите существующую папку назначения.")
            return

        answer = messagebox.askyesno(
            "Проверить структуру?",
            "Программа проверит системные папки архива и очистит корень выбранного накопителя.\n\n"
            "В корне останутся только папки проекта:\n"
            "Фото, Видео, Музыка, Документы, Прочее, Сейф, Рабочий.\n\n"
            "Все остальные файлы и папки в корне будут удалены.\n"
            "Внутри проектных папок очистка не выполняется.\n\n"
            "Продолжить?"
        )

        if not answer:
            return

        self.start_btn.configure(state="disabled")
        self.check_structure_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        self.append_log("🧹 Запущена ручная проверка структуры.")
        self.engine.run_structure_check_only(target)

    def choose_source(self):
        path = filedialog.askdirectory(title="Выберите источник")
        if path:
            self.source_var.set(path)
            self.append_log(f"Источник выбран: {path}")

    def choose_target(self):
        path = filedialog.askdirectory(title="Выберите накопитель/папку назначения")
        if path:
            self.target_var.set(path)
            self.append_log(f"Назначение выбрано: {path}")

    def start(self):
        source = self.source_var.get().strip()
        target = self.target_var.get().strip()

        if not source or not os.path.isdir(source):
            messagebox.showerror("Ошибка", "Выберите существующую папку-источник.")
            return

        if not target or not os.path.isdir(target):
            messagebox.showerror("Ошибка", "Выберите существующую папку назначения.")
            return

        if os.path.abspath(source) == os.path.abspath(target):
            messagebox.showerror("Ошибка", "Источник и назначение не должны быть одной и той же папкой.")
            return

        allowed_categories = self.get_allowed_categories()
        if self.category_scan_var.get() and not allowed_categories:
            messagebox.showerror("Ошибка", "Вы включили сканирование по категориям, но не выбрали ни одну категорию.")
            return

        selected_categories = self.get_selected_categories()

        if self.category_filter_var.get() and not selected_categories:
            messagebox.showerror("Ошибка", "Вы включили сканировку по категориям, но не выбрали ни одну категорию.")
            return

        self.progress_var.set(0)
        self.current_file_var.set("-")
        self.log_text.delete("1.0", "end")

        self.start_btn.configure(state="disabled")
        self.check_structure_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")

        self.append_log("▶ Запуск обработки.")
        self.append_log(f"Источник: {source}")
        self.append_log(f"Назначение: {target}")

        if self.category_filter_var.get():
            self.append_log("Сканировка по категориям: " + ", ".join(sorted(selected_categories)))
        else:
            self.append_log("Сканировка по категориям: выключена, будут обработаны все поддерживаемые типы файлов.")

        self.engine.start(
            source=source,
            target=target,
            deep_hash=self.deep_hash_var.get(),
            max_workers=max(1, int(self.workers_var.get())),
            category_filter_enabled=self.category_filter_var.get(),
            selected_categories=selected_categories,
        )

    def stop(self):
        self.engine.request_stop()
        self.state_var.set("Остановка...")

    def append_log(self, text: str):
        self.log_text.insert("end", text + "\n")
        self.log_text.see("end")

    def poll_queue(self):
        try:
            while True:
                kind, data = self.ui_queue.get_nowait()

                if kind == "log":
                    self.append_log(data)

                elif kind == "state":
                    self.state_var.set(str(data))

                elif kind == "scan_progress":
                    count, current, total_size = data
                    self.state_var.set(f"Сканирование: найдено {count}, размер {total_size}")
                    self.current_file_var.set(current)

                elif kind == "confirm_copy":
                    count = data

                    if count == 0:
                        messagebox.showinfo("Сканирование", "Файлы не найдены.")
                        self.engine.cancel_after_scan()
                        self.start_btn.configure(state="normal")
                        self.check_structure_btn.configure(state="normal")
                        self.stop_btn.configure(state="disabled")
                    else:
                        answer = messagebox.askyesno(
                            "Начать копирование?",
                            f"Сканирование завершено.\nНайдено файлов: {count}\n\nНачать безопасное копирование?"
                        )

                        if answer:
                            self.engine.continue_after_scan()
                        else:
                            self.engine.cancel_after_scan()
                            self.start_btn.configure(state="normal")
                            self.check_structure_btn.configure(state="normal")
                            self.stop_btn.configure(state="disabled")

                elif kind == "copy_progress":
                    done, total, current, copied_size = data
                    self.state_var.set(f"Копирование: {done}/{total}, {copied_size}")
                    self.current_file_var.set(current)

                    if total:
                        self.progress_var.set(done / total * 100)

                elif kind == "sort_progress":
                    done, total, current = data
                    self.state_var.set(f"Сортировка: {done}/{total}")
                    self.current_file_var.set(current)

                    if total:
                        self.progress_var.set(done / total * 100)

                elif kind == "report":
                    report_text, report_path = data

                    self.progress_var.set(100)
                    self.state_var.set("Готово")
                    self.current_file_var.set("-")
                    self.start_btn.configure(state="normal")
                    self.check_structure_btn.configure(state="normal")
                    self.stop_btn.configure(state="disabled")

                    messagebox.showinfo(
                        "Готово",
                        report_text + f"\n\nФайл отчёта:\n{report_path}"
                    )

                elif kind == "finished":
                    self.state_var.set(str(data))
                    self.start_btn.configure(state="normal")
                    self.check_structure_btn.configure(state="normal")
                    self.stop_btn.configure(state="disabled")

                elif kind == "structure_checked":
                    removed, skipped, errors = data
                    self.progress_var.set(0)
                    self.state_var.set("Структура проверена")
                    self.current_file_var.set("-")
                    self.start_btn.configure(state="normal")
                    self.check_structure_btn.configure(state="normal")
                    self.stop_btn.configure(state="disabled")
                    messagebox.showinfo(
                        "Структура проверена",
                        f"Проверка завершена.\n\nУдалено: {removed}\nПропущено: {skipped}\nОшибок: {errors}"
                    )

                elif kind == "error":
                    self.start_btn.configure(state="normal")
                    self.check_structure_btn.configure(state="normal")
                    self.stop_btn.configure(state="disabled")
                    messagebox.showerror("Ошибка", str(data))

        except queue.Empty:
            pass

        self.after(100, self.poll_queue)


def main():
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
