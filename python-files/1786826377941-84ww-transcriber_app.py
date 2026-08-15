import os
import sys
import time
import threading

from PySide6.QtCore import Qt, Signal, QObject
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QTextEdit,
    QFileDialog,
    QComboBox,
    QProgressBar,
    QMessageBox,
    QGroupBox,
    QSpinBox,
)

MODEL_SIZES = [
    "tiny",
    "base",
    "small",
    "medium",
    "large-v3",
]

LANGUAGES = {
    "Auto Detect": None,
    "English": "en",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Italian": "it",
    "Portuguese": "pt",
    "Swahili": "sw",
    "Arabic": "ar",
    "Chinese": "zh",
    "Japanese": "ja",
    "Korean": "ko",
}

AUDIO_FILETYPES = (
    "Audio/Video Files "
    "(*.mp3 *.wav *.m4a *.flac *.ogg *.aac *.wma "
    "*.mp4 *.mkv *.webm);;"
    "Audio Files (*.mp3 *.wav *.m4a *.flac *.ogg *.aac *.wma);;"
    "Video Files (*.mp4 *.mkv *.webm);;"
    "All Files (*.*)"
)


class WorkerSignals(QObject):
    status = Signal(str)
    progress = Signal(int)
    transcript = Signal(str)
    finished = Signal()
    error = Signal(str)


class TranscriberApp(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Offline Audio Transcriber")
        self.resize(900, 700)

        self.audio_path = None
        self.model = None
        self.loaded_model_size = None

        self.cancel_requested = False
        self.start_time = None

        self.signals = WorkerSignals()

        self.signals.status.connect(self.update_status)
        self.signals.progress.connect(self.update_progress)
        self.signals.transcript.connect(self.append_transcript)
        self.signals.finished.connect(self.transcription_finished)
        self.signals.error.connect(self.transcription_error)

        self.build_ui()
        self.apply_style()

    # ==========================================================
    # UI
    # ==========================================================

    def build_ui(self):

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(12)

        # Title
        title = QLabel("Offline Audio Transcriber")
        title.setObjectName("title")

        subtitle = QLabel(
            "Fast, private transcription powered by faster-whisper"
        )
        subtitle.setObjectName("subtitle")

        main_layout.addWidget(title)
        main_layout.addWidget(subtitle)

        # File section
        file_group = QGroupBox("Audio / Video")
        file_layout = QHBoxLayout(file_group)

        self.file_label = QLabel("No file selected")
        self.file_label.setWordWrap(True)

        self.choose_button = QPushButton("Choose File")
        self.choose_button.clicked.connect(self.choose_file)

        file_layout.addWidget(self.file_label, 1)
        file_layout.addWidget(self.choose_button)

        main_layout.addWidget(file_group)

        # Settings
        settings_group = QGroupBox("Transcription Settings")
        settings_layout = QHBoxLayout(settings_group)

        # Model
        model_layout = QVBoxLayout()

        model_label = QLabel("Model")

        self.model_combo = QComboBox()
        self.model_combo.addItems(MODEL_SIZES)
        self.model_combo.setCurrentText("base")

        model_layout.addWidget(model_label)
        model_layout.addWidget(self.model_combo)

        # Language
        language_layout = QVBoxLayout()

        language_label = QLabel("Language")

        self.language_combo = QComboBox()
        self.language_combo.addItems(LANGUAGES.keys())

        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combo)

        # Beam size
        beam_layout = QVBoxLayout()

        beam_label = QLabel("Accuracy")

        self.beam_spin = QSpinBox()
        self.beam_spin.setRange(1, 10)
        self.beam_spin.setValue(5)
        self.beam_spin.setToolTip(
            "Higher values can improve accuracy but increase processing time."
        )

        beam_layout.addWidget(beam_label)
        beam_layout.addWidget(self.beam_spin)

        settings_layout.addLayout(model_layout)
        settings_layout.addLayout(language_layout)
        settings_layout.addLayout(beam_layout)

        main_layout.addWidget(settings_group)

        # Buttons
        button_layout = QHBoxLayout()

        self.transcribe_button = QPushButton("▶  Transcribe")
        self.transcribe_button.setObjectName("primaryButton")
        self.transcribe_button.clicked.connect(
            self.start_transcription
        )

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(
            self.cancel_transcription
        )

        button_layout.addWidget(self.transcribe_button)
        button_layout.addWidget(self.cancel_button)

        main_layout.addLayout(button_layout)

        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        main_layout.addWidget(self.progress_bar)

        # Status
        self.status_label = QLabel("Ready.")
        self.status_label.setObjectName("status")

        main_layout.addWidget(self.status_label)

        # Transcript
        transcript_group = QGroupBox("Transcript")
        transcript_layout = QVBoxLayout(transcript_group)

        self.text_box = QTextEdit()
        self.text_box.setPlaceholderText(
            "Your transcript will appear here..."
        )

        transcript_layout.addWidget(self.text_box)

        main_layout.addWidget(transcript_group, 1)

        # Save buttons
        save_layout = QHBoxLayout()

        self.save_txt_button = QPushButton("Save TXT")
        self.save_txt_button.setEnabled(False)
        self.save_txt_button.clicked.connect(
            self.save_txt
        )

        self.save_srt_button = QPushButton("Save SRT")
        self.save_srt_button.setEnabled(False)
        self.save_srt_button.clicked.connect(
            self.save_srt
        )

        self.save_vtt_button = QPushButton("Save VTT")
        self.save_vtt_button.setEnabled(False)
        self.save_vtt_button.clicked.connect(
            self.save_vtt
        )

        save_layout.addWidget(self.save_txt_button)
        save_layout.addWidget(self.save_srt_button)
        save_layout.addWidget(self.save_vtt_button)

        main_layout.addLayout(save_layout)

        # Data for subtitle exports
        self.segments_data = []

    # ==========================================================
    # STYLE
    # ==========================================================

    def apply_style(self):

        self.setStyleSheet("""
            QMainWindow {
                background-color: #111318;
            }

            QWidget {
                color: #eeeeee;
                font-size: 14px;
            }

            QLabel#title {
                font-size: 28px;
                font-weight: bold;
            }

            QLabel#subtitle {
                color: #888888;
                font-size: 14px;
                margin-bottom: 8px;
            }

            QLabel#status {
                color: #aaaaaa;
            }

            QGroupBox {
                border: 1px solid #30343b;
                border-radius: 8px;
                margin-top: 8px;
                padding: 12px;
                font-weight: bold;
            }

            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 5px;
            }

            QPushButton {
                background-color: #252a31;
                border: 1px solid #3b414a;
                border-radius: 6px;
                padding: 9px 16px;
            }

            QPushButton:hover {
                background-color: #30363f;
            }

            QPushButton:disabled {
                color: #666666;
                background-color: #1b1e23;
            }

            QPushButton#primaryButton {
                background-color: #2563eb;
                border: none;
                font-weight: bold;
            }

            QPushButton#primaryButton:hover {
                background-color: #3574f0;
            }

            QComboBox,
            QSpinBox {
                background-color: #1b1e23;
                border: 1px solid #3b414a;
                border-radius: 5px;
                padding: 7px;
            }

            QTextEdit {
                background-color: #0d0f12;
                border: 1px solid #30343b;
                border-radius: 6px;
                padding: 10px;
                font-size: 14px;
            }

            QProgressBar {
                border: 1px solid #30343b;
                border-radius: 5px;
                text-align: center;
                background-color: #181b20;
            }

            QProgressBar::chunk {
                background-color: #2563eb;
                border-radius: 4px;
            }
        """)

    # ==========================================================
    # FILE SELECTION
    # ==========================================================

    def choose_file(self):

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Audio or Video File",
            "",
            AUDIO_FILETYPES
        )

        if not path:
            return

        self.audio_path = path

        self.file_label.setText(
            os.path.basename(path)
        )

        self.status_label.setText(
            "File selected. Ready to transcribe."
        )

    # ==========================================================
    # TRANSCRIPTION
    # ==========================================================

    def start_transcription(self):

        if not self.audio_path:

            QMessageBox.warning(
                self,
                "No File",
                "Please choose an audio or video file first."
            )

            return

        self.cancel_requested = False
        self.start_time = time.time()

        self.text_box.clear()
        self.segments_data.clear()

        self.progress_bar.setValue(0)

        self.transcribe_button.setEnabled(False)
        self.choose_button.setEnabled(False)
        self.cancel_button.setEnabled(True)

        self.save_txt_button.setEnabled(False)
        self.save_srt_button.setEnabled(False)
        self.save_vtt_button.setEnabled(False)

        thread = threading.Thread(
            target=self.transcription_worker,
            daemon=True
        )

        thread.start()

    def cancel_transcription(self):

        self.cancel_requested = True

        self.status_label.setText(
            "Cancelling transcription..."
        )

        self.cancel_button.setEnabled(False)

    def transcription_worker(self):

        try:

            from faster_whisper import WhisperModel

        except ImportError:

            self.signals.error.emit(
                "faster-whisper is not installed.\n\n"
                "Run:\n\n"
                "pip install faster-whisper"
            )

            return

        try:

            model_size = self.model_combo.currentText()

            beam_size = self.beam_spin.value()

            language_name = (
                self.language_combo.currentText()
            )

            language = LANGUAGES[language_name]

            # --------------------------------------------------
            # Load model
            # --------------------------------------------------

            if (
                self.model is None
                or self.loaded_model_size != model_size
            ):

                self.signals.status.emit(
                    f"Loading {model_size} model..."
                )

                self.model = WhisperModel(
                    model_size,
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=4,
                    num_workers=1
                )

                self.loaded_model_size = model_size

            # --------------------------------------------------
            # Transcribe
            # --------------------------------------------------

            self.signals.status.emit(
                "Transcribing..."
            )

            segments, info = self.model.transcribe(
                self.audio_path,
                language=language,
                beam_size=beam_size,
                vad_filter=True,
                condition_on_previous_text=True
            )

            duration = info.duration

            for segment in segments:

                if self.cancel_requested:

                    self.signals.status.emit(
                        "Transcription cancelled."
                    )

                    self.signals.finished.emit()
                    return

                text = segment.text.strip()

                if not text:
                    continue

                self.segments_data.append({
                    "start": segment.start,
                    "end": segment.end,
                    "text": text
                })

                # Add timestamp to transcript
                timestamp = self.format_time(
                    segment.start
                )

                display_text = (
                    f"[{timestamp}] {text}\n"
                )

                self.signals.transcript.emit(
                    display_text
                )

                # Progress
                if duration and duration > 0:

                    percent = int(
                        (segment.end / duration) * 100
                    )

                    percent = max(
                        0,
                        min(100, percent)
                    )

                    self.signals.progress.emit(
                        percent
                    )

                    elapsed = (
                        time.time()
                        - self.start_time
                    )

                    self.signals.status.emit(
                        f"Transcribing... "
                        f"{percent}% | "
                        f"Elapsed: "
                        f"{self.format_duration(elapsed)}"
                    )

            self.signals.progress.emit(100)

            self.signals.finished.emit()

        except Exception as e:

            self.signals.error.emit(
                f"Transcription failed:\n\n{str(e)}"
            )

    # ==========================================================
    # UI SIGNAL HANDLERS
    # ==========================================================

    def update_status(self, text):

        self.status_label.setText(text)

    def update_progress(self, value):

        self.progress_bar.setValue(value)

    def append_transcript(self, text):

        self.text_box.moveCursor(
            self.text_box.textCursor().MoveOperation.End
        )

        self.text_box.insertPlainText(text)

        self.text_box.ensureCursorVisible()

    def transcription_finished(self):

        self.transcribe_button.setEnabled(True)
        self.choose_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

        if self.cancel_requested:

            self.status_label.setText(
                "Transcription cancelled."
            )

            return

        elapsed = (
            time.time() - self.start_time
            if self.start_time
            else 0
        )

        self.status_label.setText(
            f"Done. "
            f"Completed in "
            f"{self.format_duration(elapsed)}."
        )

        self.save_txt_button.setEnabled(True)

        if self.segments_data:

            self.save_srt_button.setEnabled(True)
            self.save_vtt_button.setEnabled(True)

    def transcription_error(self, message):

        self.transcribe_button.setEnabled(True)
        self.choose_button.setEnabled(True)
        self.cancel_button.setEnabled(False)

        self.progress_bar.setValue(0)

        self.status_label.setText(
            "Error."
        )

        QMessageBox.critical(
            self,
            "Transcription Error",
            message
        )

    # ==========================================================
    # TIME FORMATTING
    # ==========================================================

    @staticmethod
    def format_time(seconds):

        seconds = int(seconds)

        hours = seconds // 3600

        minutes = (
            seconds % 3600
        ) // 60

        secs = seconds % 60

        if hours > 0:

            return (
                f"{hours:02d}:"
                f"{minutes:02d}:"
                f"{secs:02d}"
            )

        return (
            f"{minutes:02d}:"
            f"{secs:02d}"
        )

    @staticmethod
    def format_duration(seconds):

        seconds = int(seconds)

        hours = seconds // 3600

        minutes = (
            seconds % 3600
        ) // 60

        secs = seconds % 60

        if hours:

            return (
                f"{hours:02d}:"
                f"{minutes:02d}:"
                f"{secs:02d}"
            )

        return (
            f"{minutes:02d}:"
            f"{secs:02d}"
        )

    @staticmethod
    def format_srt_time(seconds):

        milliseconds = int(
            (seconds % 1) * 1000
        )

        total_seconds = int(seconds)

        hours = total_seconds // 3600

        minutes = (
            total_seconds % 3600
        ) // 60

        secs = total_seconds % 60

        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{secs:02d},"
            f"{milliseconds:03d}"
        )

    @staticmethod
    def format_vtt_time(seconds):

        milliseconds = int(
            (seconds % 1) * 1000
        )

        total_seconds = int(seconds)

        hours = total_seconds // 3600

        minutes = (
            total_seconds % 3600
        ) // 60

        secs = total_seconds % 60

        return (
            f"{hours:02d}:"
            f"{minutes:02d}:"
            f"{secs:02d}."
            f"{milliseconds:03d}"
        )

    # ==========================================================
    # SAVE TXT
    # ==========================================================

    def save_txt(self):

        if not self.segments_data:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Transcript",
            "transcript.txt",
            "Text Files (*.txt)"
        )

        if not path:
            return

        try:

            with open(
                path,
                "w",
                encoding="utf-8"
            ) as file:

                for segment in self.segments_data:

                    timestamp = self.format_time(
                        segment["start"]
                    )

                    file.write(
                        f"[{timestamp}] "
                        f"{segment['text']}\n"
                    )

            QMessageBox.information(
                self,
                "Saved",
                f"Transcript saved to:\n{path}"
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Save Error",
                str(e)
            )

    # ==========================================================
    # SAVE SRT
    # ==========================================================

    def save_srt(self):

        if not self.segments_data:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Subtitles",
            "subtitles.srt",
            "SRT Subtitles (*.srt)"
        )

        if not path:
            return

        try:

            with open(
                path,
                "w",
                encoding="utf-8"
            ) as file:

                for index, segment in enumerate(
                    self.segments_data,
                    start=1
                ):

                    start = self.format_srt_time(
                        segment["start"]
                    )

                    end = self.format_srt_time(
                        segment["end"]
                    )

                    file.write(
                        f"{index}\n"
                        f"{start} --> {end}\n"
                        f"{segment['text']}\n\n"
                    )

            QMessageBox.information(
                self,
                "Saved",
                f"SRT subtitles saved to:\n{path}"
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Save Error",
                str(e)
            )

    # ==========================================================
    # SAVE VTT
    # ==========================================================

    def save_vtt(self):

        if not self.segments_data:
            return

        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save WebVTT",
            "subtitles.vtt",
            "WebVTT Files (*.vtt)"
        )

        if not path:
            return

        try:

            with open(
                path,
                "w",
                encoding="utf-8"
            ) as file:

                file.write("WEBVTT\n\n")

                for segment in self.segments_data:

                    start = self.format_vtt_time(
                        segment["start"]
                    )

                    end = self.format_vtt_time(
                        segment["end"]
                    )

                    file.write(
                        f"{start} --> {end}\n"
                        f"{segment['text']}\n\n"
                    )

            QMessageBox.information(
                self,
                "Saved",
                f"VTT subtitles saved to:\n{path}"
            )

        except Exception as e:

            QMessageBox.critical(
                self,
                "Save Error",
                str(e)
            )


# ==============================================================
# MAIN
# ==============================================================

def main():

    app = QApplication(sys.argv)

    app.setApplicationName(
        "Offline Audio Transcriber"
    )

    window = TranscriberApp()
    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()