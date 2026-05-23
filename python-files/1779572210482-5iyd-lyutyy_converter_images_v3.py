from __future__ import annotations

import os
import shutil
import tempfile
import threading
import zipfile
from pathlib import Path
from typing import Iterable, Tuple

try:
    import customtkinter as ctk
    from PIL import Image, UnidentifiedImageError
    from tkinter import filedialog, messagebox
    import tkinter as tk
except ModuleNotFoundError as error:
    missing = error.name
    print()
    print("Не хватает зависимости:", missing)
    print()
    print("Установи зависимости командой:")
    print("    py -m pip install customtkinter pillow")
    print()
    print("Если команда py не работает, попробуй:")
    print("    python -m pip install customtkinter pillow")
    print()
    input("Нажми Enter, чтобы закрыть окно...")
    raise SystemExit(1)


APP_TITLE = "Лютый конвертер изображений"
WATERMARK = "привет от Николаса"

FORMAT_ALIASES = {
    "WEBP": {".webp"},
    "PNG": {".png"},
    "JPEG": {".jpg", ".jpeg"},
    "JPG": {".jpg", ".jpeg"},
    "BMP": {".bmp"},
    "TIFF": {".tif", ".tiff"},
}

OUTPUT_EXT = {
    "WEBP": ".webp",
    "PNG": ".png",
    "JPEG": ".jpg",
    "JPG": ".jpg",
    "BMP": ".bmp",
    "TIFF": ".tiff",
}

PIL_FORMAT = {
    "WEBP": "WEBP",
    "PNG": "PNG",
    "JPEG": "JPEG",
    "JPG": "JPEG",
    "BMP": "BMP",
    "TIFF": "TIFF",
}


class ImageConverterApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        self.title(APP_TITLE)
        self.geometry("660x560")
        self.minsize(620, 540)
        self.resizable(False, False)

        self.selected_path: Path | None = None
        self.selected_kind: str | None = None
        self.is_working = False

        self._build_ui()

    def _build_ui(self):
        self.bg_canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg="#080d1d")
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)

        # Спокойный фон без лишних рамок.
        self.bg_canvas.create_oval(430, -135, 835, 280, fill="#152d5c", outline="")
        self.bg_canvas.create_oval(-185, 360, 250, 780, fill="#23164e", outline="")

        # Подпись перенесена вниз, в свободную область под основным блоком.
        self.bg_canvas.create_text(
            330,
            535,
            text=WATERMARK,
            fill="#41537f",
            font=("Segoe UI", 24, "bold italic"),
            angle=-4,
        )

        # Один основной красивый блок, без внешних прямоугольных рамок.
        self.main = ctk.CTkFrame(self, corner_radius=30, fg_color="#101827")
        self.main.place(relx=0.5, rely=0.465, anchor="center", relwidth=0.80, relheight=0.79)

        self.title_label = ctk.CTkLabel(
            self.main,
            text=APP_TITLE,
            font=ctk.CTkFont(family="Segoe UI", size=27, weight="bold"),
            text_color="#f7f8ff",
        )
        self.title_label.pack(pady=(24, 4))

        self.subtitle_label = ctk.CTkLabel(
            self.main,
            text="Выбери данные → проверь форматы → нажми большую зелёную кнопку",
            font=ctk.CTkFont(family="Segoe UI", size=13),
            text_color="#9aa7c7",
        )
        self.subtitle_label.pack(pady=(0, 16))

        self.choose_button = ctk.CTkButton(
            self.main,
            text="1. Выбрать данные",
            width=250,
            height=52,
            corner_radius=18,
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            fg_color="#6d5dfc",
            hover_color="#8377ff",
            command=self.open_picker,
        )
        self.choose_button.pack(pady=(0, 14))

        self.path_box = ctk.CTkFrame(self.main, corner_radius=16, fg_color="#0a1022")
        self.path_box.pack(fill="x", padx=34, pady=(0, 12))

        self.path_label = ctk.CTkLabel(
            self.path_box,
            text="Путь пока не выбран",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#7d89aa",
            wraplength=430,
            justify="center",
        )
        self.path_label.pack(padx=16, pady=11)

        self.convert_button = ctk.CTkButton(
            self.main,
            text="🔥 КОНВЕРТИРОВАТЬ СЕЙЧАС",
            width=320,
            height=58,
            corner_radius=20,
            font=ctk.CTkFont(family="Segoe UI", size=17, weight="bold"),
            fg_color="#20c997",
            hover_color="#2ee6ae",
            text_color="#07111f",
            command=self.start_conversion,
            state="disabled",
        )
        self.convert_button.pack(pady=(0, 16))

        self.format_frame = ctk.CTkFrame(self.main, corner_radius=20, fg_color="#0a1022")
        self.format_frame.pack(fill="x", padx=34, pady=(0, 14))
        self.format_frame.grid_columnconfigure((0, 2), weight=1)

        self.from_label = ctk.CTkLabel(
            self.format_frame,
            text="Из формата",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#9aa7c7",
        )
        self.from_label.grid(row=0, column=0, pady=(14, 5))

        self.arrow_label = ctk.CTkLabel(
            self.format_frame,
            text="→",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#6d5dfc",
        )
        self.arrow_label.grid(row=1, column=1, padx=10)

        self.to_label = ctk.CTkLabel(
            self.format_frame,
            text="В формат",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#9aa7c7",
        )
        self.to_label.grid(row=0, column=2, pady=(14, 5))

        formats = list(FORMAT_ALIASES.keys())
        self.from_combo = ctk.CTkComboBox(
            self.format_frame,
            values=formats,
            width=160,
            height=40,
            corner_radius=14,
            justify="center",
            font=ctk.CTkFont(size=14, weight="bold"),
            dropdown_font=ctk.CTkFont(size=13),
        )
        self.from_combo.set("WEBP")
        self.from_combo.grid(row=1, column=0, padx=(18, 0), pady=(0, 16))

        self.to_combo = ctk.CTkComboBox(
            self.format_frame,
            values=formats,
            width=160,
            height=40,
            corner_radius=14,
            justify="center",
            font=ctk.CTkFont(size=14, weight="bold"),
            dropdown_font=ctk.CTkFont(size=13),
        )
        self.to_combo.set("PNG")
        self.to_combo.grid(row=1, column=2, padx=(0, 18), pady=(0, 16))

        self.progress = ctk.CTkProgressBar(self.main, width=370, height=12, corner_radius=10)
        self.progress.set(0)
        self.progress.pack(pady=(0, 8))

        self.status_label = ctk.CTkLabel(
            self.main,
            text="Сначала выбери файл, папку или ZIP-архив",
            font=ctk.CTkFont(family="Segoe UI", size=12),
            text_color="#9aa7c7",
            wraplength=450,
            justify="center",
        )
        self.status_label.pack(pady=(0, 10))

    def open_picker(self):
        if self.is_working:
            return

        picker = ctk.CTkToplevel(self)
        picker.title("Что выбираем?")
        picker.geometry("380x270")
        picker.resizable(False, False)
        picker.transient(self)
        picker.grab_set()

        title = ctk.CTkLabel(
            picker,
            text="Выбери источник",
            font=ctk.CTkFont(size=22, weight="bold"),
        )
        title.pack(pady=(24, 18))

        def select_file():
            picker.destroy()
            path = filedialog.askopenfilename(
                title="Выбери изображение",
                filetypes=[
                    ("Изображения", "*.webp *.png *.jpg *.jpeg *.bmp *.tif *.tiff"),
                    ("Все файлы", "*.*"),
                ],
            )
            if path:
                self.set_selected_path(Path(path), "file")

        def select_folder():
            picker.destroy()
            path = filedialog.askdirectory(title="Выбери папку")
            if path:
                self.set_selected_path(Path(path), "folder")

        def select_zip():
            picker.destroy()
            path = filedialog.askopenfilename(
                title="Выбери ZIP-архив",
                filetypes=[("ZIP-архив", "*.zip"), ("Все файлы", "*.*")],
            )
            if path:
                self.set_selected_path(Path(path), "zip")

        ctk.CTkButton(picker, text="Один файл", height=42, corner_radius=14, command=select_file).pack(fill="x", padx=46, pady=6)
        ctk.CTkButton(picker, text="Папка", height=42, corner_radius=14, command=select_folder).pack(fill="x", padx=46, pady=6)
        ctk.CTkButton(picker, text="ZIP-архив", height=42, corner_radius=14, command=select_zip).pack(fill="x", padx=46, pady=6)

    def set_selected_path(self, path: Path, kind: str):
        self.selected_path = path
        self.selected_kind = kind

        kind_text = {
            "file": "Файл",
            "folder": "Папка",
            "zip": "ZIP-архив",
        }.get(kind, "Данные")

        self.path_label.configure(text=f"{kind_text}: {path}", text_color="#dce5ff")
        self.status_label.configure(text="Теперь нажми большую зелёную кнопку «КОНВЕРТИРОВАТЬ СЕЙЧАС»")
        self.convert_button.configure(state="normal", text="🔥 КОНВЕРТИРОВАТЬ СЕЙЧАС")
        self.progress.set(0)

    def start_conversion(self):
        if self.is_working:
            return

        if not self.selected_path or not self.selected_kind:
            messagebox.showwarning("Нужно выбрать данные", "Сначала выбери файл, папку или ZIP-архив.")
            return

        source_format = self.from_combo.get().strip().upper()
        target_format = self.to_combo.get().strip().upper()

        if source_format == target_format:
            messagebox.showinfo("Форматы совпадают", "Выбери разные форматы: из какого и в какой конвертировать.")
            return

        self.is_working = True
        self._set_controls_state("disabled")
        self.status_label.configure(text="Работаю... ищу подходящие изображения")
        self.convert_button.configure(text="⏳ КОНВЕРТИРУЮ...")
        self.progress.set(0.05)

        thread = threading.Thread(
            target=self._run_conversion_safe,
            args=(source_format, target_format),
            daemon=True,
        )
        thread.start()

    def _run_conversion_safe(self, source_format: str, target_format: str):
        try:
            if self.selected_kind == "file":
                converted, skipped = self.convert_single_file(self.selected_path, source_format, target_format)
                message = self.build_result_message(converted, skipped, archive_backup=None)
            elif self.selected_kind == "folder":
                converted, skipped = self.convert_folder(self.selected_path, source_format, target_format)
                message = self.build_result_message(converted, skipped, archive_backup=None)
            elif self.selected_kind == "zip":
                converted, skipped, backup = self.convert_zip_archive(self.selected_path, source_format, target_format)
                message = self.build_result_message(converted, skipped, archive_backup=backup)
            else:
                raise RuntimeError("Неизвестный тип выбранных данных")

            self.after(0, self._conversion_done, message)
        except Exception as exc:
            self.after(0, self._conversion_failed, str(exc))

    def _conversion_done(self, message: str):
        self.is_working = False
        self.progress.set(1)
        self.status_label.configure(text=message)
        self._set_controls_state("normal")
        self.convert_button.configure(text="🔥 КОНВЕРТИРОВАТЬ СЕЙЧАС")
        messagebox.showinfo("Готово", message)

    def _conversion_failed(self, error_text: str):
        self.is_working = False
        self.progress.set(0)
        self.status_label.configure(text="Что-то пошло не так")
        self._set_controls_state("normal")
        self.convert_button.configure(text="🔥 КОНВЕРТИРОВАТЬ СЕЙЧАС")
        messagebox.showerror("Ошибка", error_text)

    def _set_controls_state(self, state: str):
        self.choose_button.configure(state=state)
        self.convert_button.configure(state=state if self.selected_path else "disabled")
        self.from_combo.configure(state=state)
        self.to_combo.configure(state=state)

    def convert_single_file(self, path: Path, source_format: str, target_format: str) -> Tuple[int, int]:
        if not path.exists():
            raise FileNotFoundError("Файл не найден")

        if path.suffix.lower() not in FORMAT_ALIASES[source_format]:
            return 0, 1

        self.convert_image(path, target_format)
        return 1, 0

    def convert_folder(self, folder: Path, source_format: str, target_format: str) -> Tuple[int, int]:
        if not folder.exists() or not folder.is_dir():
            raise NotADirectoryError("Папка не найдена")

        files = list(self.find_files(folder, FORMAT_ALIASES[source_format]))
        return self.convert_many(files, target_format)

    def convert_zip_archive(self, archive_path: Path, source_format: str, target_format: str) -> Tuple[int, int, Path | None]:
        if not archive_path.exists() or archive_path.suffix.lower() != ".zip":
            raise ValueError("Сейчас поддерживается только ZIP-архив")

        with tempfile.TemporaryDirectory() as temp_name:
            temp_dir = Path(temp_name)
            unpack_dir = temp_dir / "unpacked"
            unpack_dir.mkdir(parents=True, exist_ok=True)

            with zipfile.ZipFile(archive_path, "r") as zin:
                self.safe_extract_zip(zin, unpack_dir)

            files = list(self.find_files(unpack_dir, FORMAT_ALIASES[source_format]))
            converted, skipped = self.convert_many(files, target_format)

            backup_path = None
            if converted > 0:
                backup_path = archive_path.with_suffix(archive_path.suffix + ".bak")
                shutil.copy2(archive_path, backup_path)

                new_zip_path = temp_dir / archive_path.name
                with zipfile.ZipFile(new_zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zout:
                    for file_path in unpack_dir.rglob("*"):
                        if file_path.is_file():
                            zout.write(file_path, file_path.relative_to(unpack_dir).as_posix())

                shutil.move(str(new_zip_path), str(archive_path))

            return converted, skipped, backup_path

    def find_files(self, root: Path, source_exts: set[str]) -> Iterable[Path]:
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in source_exts:
                yield path

    def convert_many(self, files: list[Path], target_format: str) -> Tuple[int, int]:
        converted = 0
        skipped = 0
        total = max(len(files), 1)

        if len(files) == 0:
            return 0, 0

        for index, file_path in enumerate(files, start=1):
            try:
                self.convert_image(file_path, target_format)
                converted += 1
            except Exception:
                skipped += 1

            progress_value = 0.1 + 0.85 * (index / total)
            self.after(0, self.progress.set, progress_value)
            self.after(0, self.status_label.configure, {"text": f"Конвертация: {index}/{len(files)}"})

        return converted, skipped

    def convert_image(self, source_path: Path, target_format: str):
        target_ext = OUTPUT_EXT[target_format]
        target_path = source_path.with_suffix(target_ext)

        if target_path == source_path:
            raise ValueError("Исходный и целевой путь совпали")

        temp_target = target_path.with_name(target_path.stem + "__tmp_convert__" + target_path.suffix)

        try:
            with Image.open(source_path) as img:
                image = self.prepare_image_for_format(img, target_format)

                save_kwargs = {}
                if PIL_FORMAT[target_format] == "JPEG":
                    save_kwargs.update({"quality": 95, "optimize": True})
                elif PIL_FORMAT[target_format] == "PNG":
                    save_kwargs.update({"optimize": True})
                elif PIL_FORMAT[target_format] == "WEBP":
                    save_kwargs.update({"quality": 95, "method": 6})

                image.save(temp_target, PIL_FORMAT[target_format], **save_kwargs)

            os.replace(temp_target, target_path)
            source_path.unlink(missing_ok=True)
        except UnidentifiedImageError as exc:
            temp_target.unlink(missing_ok=True)
            raise RuntimeError(f"Не удалось открыть изображение: {source_path.name}") from exc
        except Exception:
            temp_target.unlink(missing_ok=True)
            raise

    def prepare_image_for_format(self, img: Image.Image, target_format: str) -> Image.Image:
        image = img.copy()

        if target_format in {"JPEG", "JPG", "BMP"}:
            if image.mode in {"RGBA", "LA", "P"}:
                background = Image.new("RGB", image.size, (255, 255, 255))
                if image.mode == "P":
                    image = image.convert("RGBA")
                alpha = image.getchannel("A") if "A" in image.getbands() else None
                background.paste(image, mask=alpha)
                image = background
            else:
                image = image.convert("RGB")

        return image

    def safe_extract_zip(self, zip_file: zipfile.ZipFile, destination: Path):
        destination = destination.resolve()

        for member in zip_file.infolist():
            target_path = (destination / member.filename).resolve()
            if not str(target_path).startswith(str(destination)):
                raise RuntimeError("В архиве найден небезопасный путь")

        zip_file.extractall(destination)

    def build_result_message(self, converted: int, skipped: int, archive_backup: Path | None) -> str:
        if converted == 0:
            return "Подходящих файлов не нашлось. Ничего не изменено."

        message = f"Готово: сконвертировано {converted} файл(ов)."
        if skipped:
            message += f" Пропущено с ошибками: {skipped}."
        if archive_backup:
            message += f" Резервная копия архива: {archive_backup.name}"
        return message


if __name__ == "__main__":
    app = ImageConverterApp()
    app.mainloop()
