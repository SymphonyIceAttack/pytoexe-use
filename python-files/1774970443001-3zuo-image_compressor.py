import io
import logging
import os
import re
import threading
from dataclasses import dataclass
from pathlib import Path

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageTk, UnidentifiedImageError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

SUPPORTED_FILE_TYPES = ["*.png", "*.jpg", "*.jpeg", "*.bmp", "*.gif"]

@dataclass
class CompressionPolicy:
    min_quality: int = 20
    max_quality: int = 95
    quality_step: int = 5
    min_target_kb: int = 40
    max_target_kb: int = 5000


def sanitize_filename(filename: str) -> str:
    return re.sub(r"[\\/*?:\"<>|]", "", filename).strip()


def ensure_folder(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


class ImageCompressorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("图片压缩工具 by ke")
        self.root.geometry("980x640")
        self.root.configure(bg="#f0f0f0")

        self.policy = CompressionPolicy()
        self.image_path: Path | None = None
        self.output_location = Path.cwd()
        self.target_size_kb = tk.IntVar(value=400)
        self.new_filename = tk.StringVar()
        self.output_format = tk.StringVar(value="JPG")
        self.is_compressing = False

        self.create_widgets()

    def create_widgets(self):
        main_frame = tk.Frame(self.root, bg="#f0f0f0")
        main_frame.pack(expand=True, fill='both', padx=20, pady=20)

        img_frame = tk.LabelFrame(main_frame, text="预览", bg="#f0f0f0")
        img_frame.pack(fill='x', pady=(0, 10))

        self.img_label = tk.Label(img_frame, text="请加载一张图片", bg="#f0f0f0")
        self.img_label.pack(side=tk.LEFT, padx=10, pady=10)

        tk.Button(img_frame, text="选择图片...", command=self.browse_files).pack(side=tk.RIGHT, padx=10, pady=10)

        size_frame = tk.Frame(main_frame, bg="#f0f0f0")
        size_frame.pack(fill='x', pady=5)
        tk.Label(size_frame, text="目标大小 (KB):", bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        vcmd = (self.root.register(self.validate_target_size), "%P")
        tk.Entry(size_frame, textvariable=self.target_size_kb, width=12, validate="key", validatecommand=vcmd).pack(side=tk.LEFT, padx=5)

        filename_frame = tk.Frame(main_frame, bg="#f0f0f0")
        filename_frame.pack(fill='x', pady=5)
        tk.Label(filename_frame, text="新文件名:", bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        tk.Entry(filename_frame, textvariable=self.new_filename, width=30).pack(side=tk.LEFT, padx=5)

        format_frame = tk.Frame(main_frame, bg="#f0f0f0")
        format_frame.pack(fill='x', pady=5)
        tk.Label(format_frame, text="输出格式:", bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        format_combobox = ttk.Combobox(format_frame, textvariable=self.output_format,
                                       values=["JPG", "JPEG", "PNG", "BMP", "GIF"], width=10, state="readonly")
        format_combobox.current(0)
        format_combobox.pack(side=tk.LEFT, padx=5)

        output_frame = tk.Frame(main_frame, bg="#f0f0f0")
        output_frame.pack(fill='x', pady=10)
        tk.Label(output_frame, text="输出位置:", bg="#f0f0f0").pack(side=tk.LEFT, padx=5)
        self.output_location_var = tk.StringVar(value=str(self.output_location))
        tk.Entry(output_frame, textvariable=self.output_location_var, width=50).pack(side=tk.LEFT, padx=5)
        tk.Button(output_frame, text="选择...", command=self.select_output_location).pack(side=tk.LEFT, padx=5)

        bottom_frame = tk.Frame(self.root, bg="#f0f0f0")
        bottom_frame.pack(side=tk.BOTTOM, fill='x', pady=20)

        self.compress_button = tk.Button(bottom_frame, text="压缩并保存", command=self.start_compress_and_save)
        self.compress_button.pack(side=tk.LEFT, padx=10)

        self.progress = ttk.Progressbar(bottom_frame, orient="horizontal", length=600, mode="determinate")
        self.progress.pack(side=tk.RIGHT, padx=10)

    def validate_target_size(self, proposed: str) -> bool:
        if not proposed:
            return True
        if not proposed.isdigit():
            return False
        value = int(proposed)
        return self.policy.min_target_kb <= value <= self.policy.max_target_kb

    def browse_files(self):
        filename = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("Image files", " ".join(SUPPORTED_FILE_TYPES))]
        )
        if filename:
            self.load_image(Path(filename))

    def load_image(self, path: Path):
        try:
            self.image_path = path
            with Image.open(path) as img:
                img.thumbnail((320, 320))
                self.photo = ImageTk.PhotoImage(img)
                self.img_label.config(image=self.photo, text="")
        except UnidentifiedImageError:
            logging.error("无法识别的图片格式")
            self.show_message("错误", "无法识别的图片格式，请选择其他图片。")
        except Exception as exc:
            logging.error("加载图片失败: %s", exc)
            self.show_message("错误", f"加载图片失败: {exc}")

    def select_output_location(self):
        directory = filedialog.askdirectory(title="选择输出位置")
        if directory:
            self.output_location_var.set(directory)
            self.output_location = Path(directory)

    def start_compress_and_save(self):
        if self.is_compressing:
            return
        self.progress['value'] = 0
        self.compress_button.config(state="disabled")
        self.is_compressing = True
        threading.Thread(target=self.compress_and_save, daemon=True).start()

    def compress_and_save(self):
        try:
            if not self.image_path or not self.image_path.exists():
                self.show_message("警告", "请选择有效的图片再压缩。")
                return

            output_dir = Path(self.output_location_var.get() or self.output_location)
            ensure_folder(output_dir)

            if not os.access(output_dir, os.W_OK):
                self.show_message("错误", "没有足够的权限在该目录写入文件。")
                return

            filename = sanitize_filename(self.new_filename.get()) or self.image_path.stem
            filename = filename[:120]
            output_path = output_dir / f"{filename}.{self.get_output_extension()}"

            target_size_kb = max(self.policy.min_target_kb, self.target_size_kb.get())
            target_size_kb = min(self.policy.max_target_kb, target_size_kb)

            original_kb = self.image_path.stat().st_size / 1024
            if original_kb <= target_size_kb:
                self.show_message("提示", "原图已低于目标大小，无需压缩。")
                return

            compressed_bytes = self.compress_image(self.image_path, target_size_kb)
            with open(output_path, "wb") as outf:
                outf.write(compressed_bytes)

            self.set_progress_value(100)
            self.show_message("成功", f"图片已压缩并保存为 {output_path.name}")
        except Exception as exc:
            logging.error("压缩失败: %s", exc)
            self.show_message("错误", f"压缩失败: {exc}")
        finally:
            self.is_compressing = False
            self.root.after(0, lambda: self.compress_button.config(state="normal"))

    def compress_image(self, image_path: Path, target_size_kb: int) -> bytes:
        target_bytes = target_size_kb * 1024
        format_name = self.get_output_format()

        with Image.open(image_path) as img:
            img = img.convert("RGB")
            buffer = io.BytesIO()
            best_bytes = b""
            best_size = float('inf')
            quality = self.policy.max_quality
            initial_bytes = image_path.stat().st_size
            while quality >= self.policy.min_quality:
                buffer.seek(0)
                buffer.truncate()
                img.save(buffer, format=format_name, optimize=True, quality=quality)
                current_bytes = buffer.tell()
                if current_bytes <= target_bytes:
                    return buffer.getvalue()
                if current_bytes < best_size:
                    best_size = current_bytes
                    best_bytes = buffer.getvalue()
                self.update_progress_by_size(current_bytes, initial_bytes, target_bytes)
                quality -= self.policy.quality_step

            if not best_bytes:
                raise ValueError("无法将图片压缩到指定大小，请增加目标值或缩小图片。")
            return best_bytes

    def update_progress_by_size(self, current_bytes: int, initial_bytes: int, target_bytes: int) -> None:
        progress = (initial_bytes - current_bytes) / max(initial_bytes - target_bytes, 1) * 100
        progress = max(1, min(99, progress))
        self.root.after(0, lambda: self.set_progress_value(progress))

    def set_progress_value(self, value: float):
        self.progress['value'] = value

    def get_output_extension(self) -> str:
        fmt = self.output_format.get().upper()
        return {
            "JPG": "jpg",
            "JPEG": "jpg",
            "PNG": "png",
            "BMP": "bmp",
            "GIF": "gif",
        }.get(fmt, "jpg")

    def get_output_format(self) -> str:
        fmt = self.output_format.get().upper()
        return {
            "JPG": "JPEG",
            "JPEG": "JPEG",
            "PNG": "PNG",
            "BMP": "BMP",
            "GIF": "GIF",
        }.get(fmt, "JPEG")

    def show_message(self, title: str, message: str):
        self.root.after(0, lambda: messagebox.showinfo(title, message))


def main():
    root = tk.Tk()
    ImageCompressorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
