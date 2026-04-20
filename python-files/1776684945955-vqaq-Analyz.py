import os
import sys
import warnings
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import gc
import ffmpeg
import torch
import torchaudio
from faster_whisper import WhisperModel
from diarize import diarize as diarize_func

# Подавляем предупреждения (если остались)
warnings.filterwarnings("ignore", category=UserWarning, module="torchcodec")
warnings.filterwarnings("ignore", message=".*torchcodec.*")
warnings.filterwarnings("ignore", category=FutureWarning)

# Для обхода проблем с Hugging Face Hub
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"


class TranscriptionApp:
    def __init__(self, root):
        self.root = root
        root.title("Расшифровка видео (Faster-Whisper + Diarize)")
        root.geometry("650x600")
        root.resizable(True, True)

        # Переменные
        self.video_path = tk.StringVar()
        self.model_size = tk.StringVar(value="large-v3")
        self.device = tk.StringVar(value="cuda" if torch.cuda.is_available() else "cpu")
        self.compute_type = tk.StringVar(value="float16" if torch.cuda.is_available() else "int8")
        self.language = tk.StringVar(value="auto")
        self.enable_diarization = tk.BooleanVar(value=True)
        self.output_file = tk.StringVar(value="")
        self.progress = tk.StringVar(value="Готов к работе")

        self.create_widgets()

    def create_widgets(self):
        # Фрейм для выбора файла
        frame_file = ttk.LabelFrame(self.root, text="Видеофайл", padding=5)
        frame_file.pack(fill="x", padx=10, pady=5)

        ttk.Entry(frame_file, textvariable=self.video_path, width=50).pack(side="left", fill="x", expand=True, padx=(0,5))
        ttk.Button(frame_file, text="Обзор", command=self.browse_video).pack(side="right")

        # Фрейм настроек модели Whisper
        frame_model = ttk.LabelFrame(self.root, text="Параметры Faster-Whisper", padding=5)
        frame_model.pack(fill="x", padx=10, pady=5)

        ttk.Label(frame_model, text="Модель:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        models = ["tiny", "base", "small", "medium", "large-v2", "large-v3"]
        ttk.Combobox(frame_model, textvariable=self.model_size, values=models, state="readonly", width=15).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Label(frame_model, text="Устройство:").grid(row=0, column=2, sticky="w", padx=5, pady=2)
        devices = ["cpu", "cuda"] if torch.cuda.is_available() else ["cpu"]
        ttk.Combobox(frame_model, textvariable=self.device, values=devices, state="readonly", width=10).grid(row=0, column=3, sticky="w", padx=5)

        ttk.Label(frame_model, text="Тип вычислений:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        comp_types = ["float16", "int8_float16", "int8"] if self.device.get() == "cuda" else ["int8", "float32"]
        ttk.Combobox(frame_model, textvariable=self.compute_type, values=comp_types, state="readonly", width=15).grid(row=1, column=1, sticky="w", padx=5)

        ttk.Label(frame_model, text="Язык:").grid(row=1, column=2, sticky="w", padx=5, pady=2)
        langs = ["auto", "ru", "en", "de", "fr", "es", "it", "zh"]
        ttk.Combobox(frame_model, textvariable=self.language, values=langs, state="readonly", width=10).grid(row=1, column=3, sticky="w", padx=5)

        # Фрейм диаризации
        frame_diar = ttk.LabelFrame(self.root, text="Диаризация (Diarize)", padding=5)
        frame_diar.pack(fill="x", padx=10, pady=5)

        ttk.Checkbutton(frame_diar, text="Включить диаризацию", variable=self.enable_diarization).grid(row=0, column=0, sticky="w", padx=5, pady=2)

        # Фрейм вывода
        frame_output = ttk.LabelFrame(self.root, text="Сохранение результата", padding=5)
        frame_output.pack(fill="x", padx=10, pady=5)

        ttk.Entry(frame_output, textvariable=self.output_file, width=50).pack(side="left", fill="x", expand=True, padx=(0,5))
        ttk.Button(frame_output, text="Выбрать", command=self.browse_output).pack(side="right")

        # Прогресс и кнопка запуска
        ttk.Label(self.root, textvariable=self.progress, relief="sunken", anchor="w").pack(fill="x", padx=10, pady=5)
        self.run_button = ttk.Button(self.root, text="Запустить расшифровку", command=self.start_processing)
        self.run_button.pack(pady=10)

    def browse_video(self):
        filename = filedialog.askopenfilename(
            title="Выберите видеофайл",
            filetypes=[("Видео файлы", "*.mp4 *.avi *.mov *.mkv *.webm *.flv"), ("Все файлы", "*.*")]
        )
        if filename:
            self.video_path.set(filename)
            base = os.path.splitext(filename)[0]
            self.output_file.set(base + "_transcript.txt")

    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            title="Сохранить расшифровку как",
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")]
        )
        if filename:
            self.output_file.set(filename)

    def start_processing(self):
        if not self.video_path.get():
            messagebox.showerror("Ошибка", "Выберите видеофайл")
            return
        if not self.output_file.get():
            messagebox.showerror("Ошибка", "Укажите путь для сохранения результата")
            return

        self.run_button.config(state="disabled")
        self.progress.set("Идёт подготовка...")

        thread = threading.Thread(target=self.process_video, daemon=True)
        thread.start()

    def process_video(self):
        audio_path = "temp_audio.wav"
        try:
            # 1. Извлечение аудио
            self.update_progress("Извлечение аудио из видео...")
            self.extract_audio(self.video_path.get(), audio_path)

            # 2. Транскрипция через Faster-Whisper
            self.update_progress(f"Загрузка модели {self.model_size.get()}...")
            model = WhisperModel(
                self.model_size.get(),
                device=self.device.get(),
                compute_type=self.compute_type.get()
            )

            self.update_progress("Транскрипция аудио...")
            lang = None if self.language.get() == "auto" else self.language.get()
            segments_iter, info = model.transcribe(
                audio_path,
                language=lang,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(min_silence_duration_ms=500)
            )
            segments = list(segments_iter)

            # 3. Диаризация (если включена)
            speaker_segments = None
            if self.enable_diarization.get():
                self.update_progress("Диаризация (определение говорящих)...")
                speaker_segments = self._diarize(audio_path)

            # 4. Объединение результатов
            self.update_progress("Формирование расшифровки...")
            lines = []

            if speaker_segments:
                for seg in segments:
                    seg_start = seg.start
                    seg_end = seg.end
                    text = seg.text.strip()

                    # Находим пересекающиеся диаризационные сегменты
                    speakers_in_seg = set()
                    for spk_seg in speaker_segments:
                        if max(seg_start, spk_seg["start"]) < min(seg_end, spk_seg["end"]):
                            speakers_in_seg.add(spk_seg["speaker"])

                    speaker_label = ", ".join(sorted(speakers_in_seg)) if speakers_in_seg else "UNKNOWN"
                    timestamp = f"[{self._format_time(seg_start)} - {self._format_time(seg_end)}]"
                    lines.append(f"{timestamp} {speaker_label}: {text}")
            else:
                for seg in segments:
                    timestamp = f"[{self._format_time(seg.start)} - {self._format_time(seg.end)}]"
                    lines.append(f"{timestamp} SPEAKER: {seg.text.strip()}")

            # 5. Сохранение в один файл
            with open(self.output_file.get(), "w", encoding="utf-8") as f:
                f.write("\n".join(lines))

            self.update_progress("Готово! Расшифровка сохранена.")
            messagebox.showinfo("Успех", f"Расшифровка сохранена в:\n{self.output_file.get()}")

        except Exception as e:
            import traceback
            error_traceback = traceback.format_exc()
            self.update_progress(f"Ошибка: {str(e)}")
            self.show_error_dialog(str(e), error_traceback)
        finally:
            if os.path.exists(audio_path):
                os.remove(audio_path)
            gc.collect()
            self.run_button.config(state="normal")

    def extract_audio(self, video_path, audio_path):
        """Извлечение аудио в WAV 16kHz mono"""
        (
            ffmpeg
            .input(video_path)
            .output(audio_path, acodec='pcm_s16le', ac=1, ar='16000')
            .overwrite_output()
            .run(quiet=True)
        )

    def _diarize(self, audio_path):
        """Выполняет диаризацию с помощью библиотеки diarize."""
        try:
            # diarize возвращает объект с атрибутом segments
            result = diarize_func(audio_path)
            speaker_segments = []
            for seg in result.segments:
                speaker_segments.append({
                    "start": seg.start,
                    "end": seg.end,
                    "speaker": seg.speaker
                })
            return speaker_segments
        except Exception as e:
            # Если diarize не сработал, возвращаем None (продолжим без разделения)
            self.update_progress(f"Ошибка диаризации: {e}. Продолжаем без разделения говорящих.")
            return None

    def _format_time(self, seconds):
        """Формат MM:SS или HH:MM:SS"""
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        if h > 0:
            return f"{h:02d}:{m:02d}:{s:02d}"
        else:
            return f"{m:02d}:{s:02d}"

    def update_progress(self, message):
        self.progress.set(message)
        self.root.update_idletasks()

    def show_error_dialog(self, error_message, detailed_traceback):
        """Отображает окно ошибки с возможностью скопировать детали."""
        error_window = tk.Toplevel(self.root)
        error_window.title("Ошибка")
        error_window.geometry("500x350")
        error_window.transient(self.root)
        error_window.grab_set()

        main_frame = ttk.Frame(error_window, padding=10)
        main_frame.pack(fill="both", expand=True)

        ttk.Label(main_frame, text="Произошла ошибка:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0,5))

        text_widget = tk.Text(main_frame, wrap="word", height=10)
        text_widget.pack(fill="both", expand=True, pady=(0,10))
        text_widget.insert("1.0", detailed_traceback)
        text_widget.config(state="disabled")

        def copy_to_clipboard():
            self.root.clipboard_clear()
            self.root.clipboard_append(detailed_traceback)
            messagebox.showinfo("Успех", "Текст ошибки скопирован в буфер обмена.", parent=error_window)

        ttk.Button(main_frame, text="Копировать ошибку", command=copy_to_clipboard).pack(side="left", padx=(0,10))
        ttk.Button(main_frame, text="Закрыть", command=error_window.destroy).pack(side="left")


if __name__ == "__main__":
    root = tk.Tk()
    app = TranscriptionApp(root)
    root.mainloop()