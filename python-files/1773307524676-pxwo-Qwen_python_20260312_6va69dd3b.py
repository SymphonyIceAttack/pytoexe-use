import sys
import os
import json
from datetime import datetime
# Импорты PyQt5
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QComboBox, QTextEdit, QVBoxLayout, QHBoxLayout, QGroupBox,
    QMessageBox, QCheckBox, QSpinBox, QShortcut
)
from PyQt5.QtGui import QPixmap, QPainter, QColor, QPen, QKeySequence
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal, QSettings
# Импорты для захвата экрана и OCR
from PIL import ImageGrab
import mss
import numpy as np
import cv2
import pytesseract
# Импорты для перевода
from googletrans import Translator, LANGUAGES

# Глобальный импорт для PyInstaller
try:
    from PIL.ImageQt import ImageQt
except ImportError:
    # PyInstaller может автоматически найти это
    pass


class RegionSelectionWindow(QWidget):
    """Окно для выбора области экрана"""
    region_selected = pyqtSignal(int, int, int, int)

    def __init__(self):
        super().__init__()
        self.setWindowState(Qt.WindowFullScreen)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setStyleSheet("background-color: rgba(0, 0, 0, 100);")
        
        # Переменные для рисования
        self.start_pos = None
        self.end_pos = None
        self.drawing = False
        
        self.show()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_pos = event.pos()
            self.end_pos = event.pos()
            self.drawing = True

    def mouseMoveEvent(self, event):
        if self.drawing:
            self.end_pos = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.drawing:
            self.end_pos = event.pos()
            self.drawing = False
            
            # Получаем координаты области
            x1, y1 = self.start_pos.x(), self.start_pos.y()
            x2, y2 = self.end_pos.x(), self.end_pos.y()
            
            left = min(x1, x2)
            top = min(y1, y2)
            width = abs(x2 - x1)
            height = abs(y2 - y1)
            
            # Отправляем сигнал с координатами
            self.region_selected.emit(left, top, width, height)
            self.close()

    def paintEvent(self, event):
        if self.start_pos and self.end_pos and self.drawing:
            painter = QPainter(self)
(QPen(QColor(255, 255, 0), 2))
            rect = self.start_pos - self.end_pos
            painter.drawRect(
                min(self.start_pos.x(), self.end_pos.x()),
                min(self.start_pos.y(), self.end_pos.y()),
                abs(rect.x()), abs(rect.y())
            )


class TranslationWorker(QThread):
    """Поток для выполнения OCR и перевода"""
    result_ready = pyqtSignal(str, str)  # original_text, translated_text
    error_occurred = pyqtSignal(str)

    def __init__(self, region, lang_code, translator):
        super().__init__()
        self.region = region
        self.lang_code = lang_code
        self.translator = translator
        self.running = True

    def run(self):
        while self.running:
            try:
                with mss.mss() as sct:
                    screenshot = sct.grab({
                        "top": self.region[1],
                        "left": self.region[0],
                        "width": self.region[2],
                        "height": self.region[3]
                    })
                
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                
                # Повышаем качество изображения перед OCR
                img = img.convert('L')
                img_array = np.array(img)
                _, img_thresh = cv2.threshold(img_array, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                img = Image.fromarray(img_thresh)
                
                text = pytesseract.image_to_string(img, lang='eng+rus').strip()
                
                if text:
                    translation = self.translator.translate(text, dest=self.lang_code)
                    self.result_ready.emit(text, translation.text)
                else:
                    self.error_occurred.emit("Текст не найден в области")
                    
            except Exception as e:
                self.error_occurred.emit(f"Ошибка при обработке: {str(e)}")
                
            self.msleep(2000)  # Задержка между скриншотами

    def stop(self):
        self.running = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Автоматический перевод текста с экрана")
        self.setGeometry(100, 100, 800, 600)
        
        # Инициализация
        self.region = None
        self.translation_thread = None
        self.translator = Translator()
        self.history = []
        
        # Настройки
        self.settings = QSettings("TranslatorApp", "ScreenTranslator")
        
        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной layout
        main_layout = QVBoxLayout()
        
        # Группировка элементов
        selection_group = QGroupBox("Выбор области")
        selection_layout = QHBoxLayout()
        
        self.preview_label = QLabel()
        self.preview_label.setMinimumSize(300, 200)
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setText("Предварительный просмотр")
        self.preview_label.setStyleSheet("border: 1px solid gray;")
        
        btn_layout = QVBoxLayout()
        self.select_btn = QPushButton("Выбрать область")
        self.select_btn.clicked.connect(self.select_region)
        btn_layout.addWidget(self.select_btn)
        
        self.start_btn = QPushButton("Запустить перевод")
        self.start_btn.clicked.connect(self.start_translation)
        self.start_btn.setEnabled(False)
        btn_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Остановить")
        self.stop_btn.clicked.connect(self.stop_translation)
        self.stop_btn.setEnabled(False)
        btn_layout.addWidget(self.stop_btn)
        
        selection_layout.addWidget(self.preview_label)
        selection_layout.addLayout(btn_layout)
        selection_group.setLayout(selection_layout)
        
        # Настройки
        settings_group = QGroupBox("Настройки")
        settings_layout = QVBoxLayout()
        
        # Выбор языка
        lang_layout = QHBoxLayout()
        lang_layout.addWidget(QLabel("Язык перевода:"))
        self.lang_combo = QComboBox()
        for code, name in sorted(LANGUAGES.items()):
            self.lang_combo.addItem(f"{name.title()} ({code})", code)
        self.lang_combo.setCurrentText("English (en)")
        lang_layout.addWidget(self.lang_combo)
        settings_layout.addLayout(lang_layout)
        
        # Интервал обновления
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Интервал (сек):"))
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(1, 60)
        self.interval_spinbox.setValue(2)
        self.interval_spinbox.valueChanged.connect(self.update_interval)
        interval_layout.addWidget(self.interval_spinbox)
        settings_layout.addLayout(interval_layout)
        
        # Чекбоксы
        self.history_checkbox = QCheckBox("Сохранять историю")
        self.history_checkbox.setChecked(True)
        settings_layout.addWidget(self.history_checkbox)
        
        settings_group.setLayout(settings_layout)
        
        # Вывод текста
        output_group = QGroupBox("Переведённый текст")
        output_layout = QVBoxLayout()
        
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        output_layout.addWidget(self.output_text)
        
        output_group.setLayout(output_layout)
        
        # Добавляем все в основной layout
        main_layout.addWidget(selection_group)
        main_layout.addWidget(settings_group)
        main_layout.addWidget(output_group)
        
        central_widget.setLayout(main_layout)
        
        # Горячие клавиши
        self.start_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        self.start_shortcut.activated.connect(self.start_translation)
        self.stop_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.stop_shortcut.activated.connect(self.stop_translation)
        
        # Восстанавливаем настройки
        self.restore_settings()

    def select_region(self):
        self.region_selector = RegionSelectionWindow()
        self.region_selector.region_selected.connect(self.on_region_selected)

    def on_region_selected(self, left, top, width, height):
        self.region = (left, top, width, height)
        self.start_btn.setEnabled(True)
        
        # Обновляем предварительный просмотр
        self.update_preview()
        
        # Сохраняем настройки
        self.save_settings()

    def update_preview(self):
        if self.region:
            with mss.mss() as sct:
                screenshot = sct.grab({
                    "top": self.region[1],
                    "left": self.region[0],
                    "width": self.region[2],
                    "height": self.region[3]
                })
            
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            img.thumbnail((300, 200))  # Масштабируем для отображения
            pixmap = QPixmap.fromImage(ImageQt(img))
            self.preview_label.setPixmap(pixmap)

    def start_translation(self):
        if not self.region:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите область!")
            return
            
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        
        # Создаем поток для перевода
        lang_code = self.lang_combo.currentData()
        self.translation_thread = TranslationWorker(self.region, lang_code, self.translator)
        self.translation_thread.result_ready.connect(self.on_translation_result)
        self.translation_thread.error_occurred.connect(self.on_error)
        self.translation_thread.start()

    def stop_translation(self):
        if self.translation_thread:
            self.translation_thread.stop()
            self.translation_thread.wait()
            self.translation_thread = None
            
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def on_translation_result(self, original_text, translated_text):
        self.output_text.setPlainText(translated_text)
        
        if self.history_checkbox.isChecked():
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            entry = {
                "timestamp": timestamp,
                "original": original_text,
                "translated": translated_text,
                "language": self.lang_combo.currentText()
            }
            self.history.append(entry)
            self.save_history()

    def on_error(self, error_msg):
        self.output_text.setPlainText(f"Ошибка: {error_msg}")

    def update_interval(self):
        if self.translation_thread:
            # Перезапускаем поток с новым интервалом
            self.stop_translation()
            self.start_translation()

    def save_settings(self):
        if self.region:
            self.settings.setValue("region", self.region)
        self.settings.setValue("language", self.lang_combo.currentIndex())
        self.settings.setValue("interval", self.interval_spinbox.value())

    def restore_settings(self):
        region = self.settings.value("region")
        if region:
            self.region = tuple(region)
            self.start_btn.setEnabled(True)
            self.update_preview()
            
        lang_index = self.settings.value("language", type=int)
        if lang_index is not None:
            self.lang_combo.setCurrentIndex(lang_index)
            
        interval = self.settings.value("interval", type=int)
        if interval:
            self.interval_spinbox.setValue(interval)

    def save_history(self):
        with open("translation_history.json", "w", encoding="utf-8") as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)

    def closeEvent(self, event):
        self.stop_translation()
        self.save_settings()
        event.accept()


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()