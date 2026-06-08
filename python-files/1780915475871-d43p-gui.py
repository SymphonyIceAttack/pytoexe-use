import sys
import re
import time
import csv
from datetime import datetime
from collections import deque
from pathlib import Path

import serial
import serial.tools.list_ports
import pyqtgraph as pg
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox, QGroupBox,
    QMessageBox, QCheckBox, QFileDialog, QSplitter, QTextEdit
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QPalette, QColor, QTextCursor


# ==========================================
# КОНФИГУРАЦИЯ
# ==========================================
MAX_HISTORY_POINTS = 120
MAX_UART_LOG_LINES = 500
FONT_SIZE_LARGE = 18
FONT_SIZE_MEDIUM = 14
FONT_SIZE_SMALL = 12
WARNING_THRESHOLD_DEFAULT = 15.0


# ==========================================
# ФОНОВЫЙ ПОТОК ДЛЯ UART
# ==========================================
class SerialWorker(QThread):
    data_received = pyqtSignal(float, float)
    raw_uart_line = pyqtSignal(str)  # НОВАЯ: сырая строка от UART
    log_message = pyqtSignal(str)
    connection_status = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    settings_received = pyqtSignal(str, str, str)

    def __init__(self):
        super().__init__()
        self.port_name = None
        self.baudrate = 115200
        self.serial_port = None
        self.running = False
        self.command_queue = []
        self.waiting_for_settings = False

    def connect(self, port_name, baudrate):
        self.port_name = port_name
        self.baudrate = baudrate
        try:
            self.serial_port = serial.Serial(
                port=port_name,
                baudrate=baudrate,
                timeout=0.1,
                write_timeout=1
            )
            self.running = True
            self.connection_status.emit(True)
            self.log_message.emit(f"Подключено к {port_name} @ {baudrate}")
            self.start()
        except Exception as e:
            self.error_occurred.emit(f"Ошибка подключения: {e}")

    def disconnect(self):
        self.running = False
        if self.serial_port and self.serial_port.is_open:
            self.serial_port.close()
        self.wait(2000)
        self.connection_status.emit(False)
        self.log_message.emit("Отключено")

    def send_command(self, cmd):
        if self.serial_port and self.serial_port.is_open:
            self.command_queue.append(cmd)
            if cmd == 'G':
                self.waiting_for_settings = True

    def run(self):
        buffer = ""
        settings_buffer = ""
        while self.running:
            while self.command_queue and self.serial_port and self.serial_port.is_open:
                cmd = self.command_queue.pop(0)
                try:
                    self.serial_port.write((cmd + "\r\n").encode())
                    self.log_message.emit(f"Отправлено: {cmd}")
                except Exception as e:
                    self.error_occurred.emit(f"Ошибка отправки: {e}")

            if self.serial_port and self.serial_port.is_open:
                try:
                    if self.serial_port.in_waiting > 0:
                        data = self.serial_port.read(self.serial_port.in_waiting).decode('utf-8', errors='ignore')
                        buffer += data
                        
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()
                            if line:
                                self.raw_uart_line.emit(line)  # НОВАЯ: отправляем сырую строку
                            
                            if self.waiting_for_settings:
                                settings_buffer += line + "\n"
                                if "INTERVAL:" in line or "ms" in line:
                                    # Парсим ответ
                                    scale_match = re.search(r'SCALE:\s+([eE\d.+-]+)', settings_buffer)
                                    offset_match = re.search(r'OFFSET:\s+([eE\d.+-]+)', settings_buffer)
                                    interval_match = re.search(r'INTERVAL:\s+(\d+)', settings_buffer)
                                    
                                    if scale_match and offset_match and interval_match:
                                        scale = scale_match.group(1)
                                        offset = offset_match.group(1)
                                        interval = interval_match.group(1)
                                        self.settings_received.emit(scale, offset, interval)
                                        self.log_message.emit(f"Настройки получены: SCALE={scale}, OFFSET={offset}, INTERVAL={interval}ms")
                                    
                                    self.waiting_for_settings = False
                                    settings_buffer = ""


                            match = re.search(r'Vrms:([eE\d.+-]+)\s+Vpk:([eE\d.+-]+)\s+St:(\d+)', line)
                            if match:
                                try:
                                    rms = float(match.group(1))
                                    peak = float(match.group(2))
                                    status = int(match.group(3))
                                    self.data_received.emit(rms, peak)
                                    if status == 1:
                                        self.log_message.emit("⚠ Пропуск кадра (очередь переполнена)")
                                except ValueError:
                                    pass
                except Exception as e:
                    self.error_occurred.emit(f"Ошибка чтения: {e}")
            
            time.sleep(0.01)


# ==========================================
# ГЛАВНОЕ ОКНО
# ==========================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("STPMS2 Sigma-Delta Измеритель")
        self.resize(1600, 900)
        
        self.serial_worker = SerialWorker()
        self.serial_worker.data_received.connect(self.update_plot)
        self.serial_worker.raw_uart_line.connect(self.append_uart_log)  # НОВАЯ
        self.serial_worker.log_message.connect(self.add_log)
        self.serial_worker.connection_status.connect(self.update_connection_status)
        self.serial_worker.error_occurred.connect(self.show_error)
        self.serial_worker.settings_received.connect(self.update_settings_fields)
        
        self.rms_history = deque(maxlen=MAX_HISTORY_POINTS)
        self.peak_history = deque(maxlen=MAX_HISTORY_POINTS)
        self.time_history = deque(maxlen=MAX_HISTORY_POINTS)
        
        self.warning_threshold = WARNING_THRESHOLD_DEFAULT
        self.is_warning = False
        
        # НОВАЯ: Переменные для логирования
        self.logging_enabled = False
        self.log_file = None
        self.log_writer = None
        self.log_file_path = None

        self.log_list = [] 
        
        self.init_ui()
        self.refresh_ports()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # ==========================================
        # ВЕРХНЯЯ ЧАСТЬ: ГРАФИК И УПРАВЛЕНИЕ
        # ==========================================
        top_splitter = QSplitter(Qt.Horizontal)
        
        # Левая часть: График
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)

        values_group = QGroupBox("Текущие значения")
        values_group.setFont(QFont("Arial", FONT_SIZE_MEDIUM, QFont.Bold))
        values_layout = QHBoxLayout()
        
        self.rms_label = QLabel("Vrms: ---")
        self.rms_label.setFont(QFont("Arial", FONT_SIZE_LARGE, QFont.Bold))
        self.rms_label.setAlignment(Qt.AlignCenter)
        self.rms_label.setStyleSheet("QLabel { color: #2196F3; padding: 10px; }")
        
        self.peak_label = QLabel("Vpk: ---")
        self.peak_label.setFont(QFont("Arial", FONT_SIZE_LARGE, QFont.Bold))
        self.peak_label.setAlignment(Qt.AlignCenter)
        self.peak_label.setStyleSheet("QLabel { color: #4CAF50; padding: 10px; }")
        
        values_layout.addWidget(self.rms_label)
        values_layout.addWidget(self.peak_label)
        values_group.setLayout(values_layout)
        left_layout.addWidget(values_group)

        self.plot_widget = pg.PlotWidget()
        self.plot_widget.setBackground('#1e1e1e')
        self.plot_widget.setLabel('left', 'Напряжение', units='В')
        self.plot_widget.setLabel('bottom', 'Время', units='с')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.addLegend()
        
        self.rms_curve = self.plot_widget.plot(name='Vrms', pen=pg.mkPen(color='#2196F3', width=2))
        self.peak_curve = self.plot_widget.plot(name='Vpk', pen=pg.mkPen(color='#4CAF50', width=2))
        self.warning_line = self.plot_widget.addLine(
            y=self.warning_threshold,
            pen=pg.mkPen(color='#FF5722', width=2, style=Qt.DashLine),
            label=f'Порог: {self.warning_threshold}В'
        )
        
        left_layout.addWidget(self.plot_widget, stretch=1)
        top_splitter.addWidget(left_panel)

        # Правая часть: Управление
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        conn_group = QGroupBox("Подключение")
        conn_group.setFont(QFont("Arial", FONT_SIZE_MEDIUM, QFont.Bold))
        conn_layout = QVBoxLayout()
        
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("COM-порт:"))
        self.port_combo = QComboBox()
        self.port_combo.setFont(QFont("Arial", FONT_SIZE_MEDIUM))
        self.port_combo.setMinimumHeight(40)
        port_layout.addWidget(self.port_combo)
        
        self.refresh_btn = QPushButton("🔄")
        self.refresh_btn.setFont(QFont("Arial", FONT_SIZE_MEDIUM))
        self.refresh_btn.setMinimumHeight(40)
        self.refresh_btn.setMaximumWidth(60)
        self.refresh_btn.clicked.connect(self.refresh_ports)
        port_layout.addWidget(self.refresh_btn)
        conn_layout.addLayout(port_layout)
        
        self.connect_btn = QPushButton("Подключиться")
        self.connect_btn.setFont(QFont("Arial", FONT_SIZE_MEDIUM, QFont.Bold))
        self.connect_btn.setMinimumHeight(50)
        self.connect_btn.setStyleSheet("""
            QPushButton { background-color: #4CAF50; color: white; border-radius: 5px; }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #cccccc; }
        """)
        self.connect_btn.clicked.connect(self.toggle_connection)
        conn_layout.addWidget(self.connect_btn)
        conn_group.setLayout(conn_layout)
        right_layout.addWidget(conn_group)

        calib_group = QGroupBox("Калибровка")
        calib_group.setFont(QFont("Arial", FONT_SIZE_MEDIUM, QFont.Bold))
        calib_layout = QVBoxLayout()
        calib_layout.setSpacing(10)
        
        scale_layout = QHBoxLayout()
        scale_layout.addWidget(QLabel("SCALE:"), 1)
        self.scale_input = QLineEdit("7.45e-9")
        self.scale_input.setFont(QFont("Arial", FONT_SIZE_MEDIUM))
        self.scale_input.setMinimumHeight(40)
        scale_layout.addWidget(self.scale_input, 2)
        self.scale_btn = QPushButton("Применить")
        self.scale_btn.setFont(QFont("Arial", FONT_SIZE_MEDIUM))
        self.scale_btn.setMinimumHeight(40)
        self.scale_btn.clicked.connect(lambda: self.send_calib_command('S', self.scale_input.text()))
        scale_layout.addWidget(self.scale_btn, 1)
        calib_layout.addLayout(scale_layout)
        
        offset_layout = QHBoxLayout()
        offset_layout.addWidget(QLabel("OFFSET:"), 1)
        self.offset_input = QLineEdit("0.0")
        self.offset_input.setFont(QFont("Arial", FONT_SIZE_MEDIUM))
        self.offset_input.setMinimumHeight(40)
        offset_layout.addWidget(self.offset_input, 2)
        self.offset_btn = QPushButton("Применить")
        self.offset_btn.setFont(QFont("Arial", FONT_SIZE_MEDIUM))
        self.offset_btn.setMinimumHeight(40)
        self.offset_btn.clicked.connect(lambda: self.send_calib_command('O', self.offset_input.text()))
        offset_layout.addWidget(self.offset_btn, 1)
        calib_layout.addLayout(offset_layout)
        calib_group.setLayout(calib_layout)
        right_layout.addWidget(calib_group)

        interval_group = QGroupBox("Интервал измерения")
        interval_group.setFont(QFont("Arial", FONT_SIZE_MEDIUM, QFont.Bold))
        interval_layout = QHBoxLayout()
        interval_layout.addWidget(QLabel("Период (мс):"), 1)
        self.interval_input = QLineEdit("1000")
        self.interval_input.setFont(QFont("Arial", FONT_SIZE_MEDIUM))
        self.interval_input.setMinimumHeight(40)
        interval_layout.addWidget(self.interval_input, 2)
        self.interval_btn = QPushButton("Применить")
        self.interval_btn.setFont(QFont("Arial", FONT_SIZE_MEDIUM))
        self.interval_btn.setMinimumHeight(40)
        self.interval_btn.clicked.connect(lambda: self.send_calib_command('I', self.interval_input.text()))
        interval_layout.addWidget(self.interval_btn, 1)
        interval_group.setLayout(interval_layout)
        right_layout.addWidget(interval_group)

        warning_group = QGroupBox("Порог предупреждения")
        warning_group.setFont(QFont("Arial", FONT_SIZE_MEDIUM, QFont.Bold))
        warning_layout = QVBoxLayout()
        warning_layout.setSpacing(10)
        
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("Порог (В):"), 1)
        self.threshold_input = QLineEdit(str(self.warning_threshold))
        self.threshold_input.setFont(QFont("Arial", FONT_SIZE_MEDIUM))
        self.threshold_input.setMinimumHeight(40)
        threshold_layout.addWidget(self.threshold_input, 2)
        self.threshold_btn = QPushButton("Установить")
        self.threshold_btn.setFont(QFont("Arial", FONT_SIZE_MEDIUM))
        self.threshold_btn.setMinimumHeight(40)
        self.threshold_btn.clicked.connect(self.set_warning_threshold)
        threshold_layout.addWidget(self.threshold_btn, 1)
        warning_layout.addLayout(threshold_layout)
        
        self.warning_indicator = QLabel("СТАТУС: НОРМА")
        self.warning_indicator.setFont(QFont("Arial", FONT_SIZE_LARGE, QFont.Bold))
        self.warning_indicator.setAlignment(Qt.AlignCenter)
        
        self.warning_indicator.setWordWrap(True)   # Разрешаем перенос текста
        self.warning_indicator.setFixedHeight(70)  # Жестко фиксируем высоту (с запасом на 2 строки)
        
        self.warning_indicator.setStyleSheet("""
            QLabel { background-color: #4CAF50; color: white; border-radius: 5px; padding: 10px; }
        """)
        warning_layout.addWidget(self.warning_indicator)
        warning_group.setLayout(warning_layout)
        right_layout.addWidget(warning_group)

        self.get_settings_btn = QPushButton("📋 Запросить настройки с устройства")
        self.get_settings_btn.setFont(QFont("Arial", FONT_SIZE_MEDIUM))
        self.get_settings_btn.setMinimumHeight(50)
        self.get_settings_btn.clicked.connect(lambda: self.serial_worker.send_command('G'))
        right_layout.addWidget(self.get_settings_btn)

        right_layout.addStretch()
        top_splitter.addWidget(right_panel)
        
        top_splitter.setSizes([1000, 400])
        main_layout.addWidget(top_splitter, stretch=2)

        # ==========================================
        # НОВАЯ: НИЖНЯЯ ЧАСТЬ - ЛОГИ
        # ==========================================
        bottom_splitter = QSplitter(Qt.Horizontal)
        
        # Сырой вывод UART
        uart_log_group = QGroupBox("Сырой вывод UART")
        uart_log_group.setFont(QFont("Arial", FONT_SIZE_MEDIUM, QFont.Bold))
        uart_log_layout = QVBoxLayout()
        
        uart_controls = QHBoxLayout()
        self.clear_uart_btn = QPushButton("Очистить")
        self.clear_uart_btn.setFont(QFont("Arial", FONT_SIZE_SMALL))
        self.clear_uart_btn.setMinimumHeight(35)
        self.clear_uart_btn.clicked.connect(self.clear_uart_log)
        uart_controls.addWidget(self.clear_uart_btn)
        
        self.auto_scroll_checkbox = QCheckBox("Автопрокрутка")
        self.auto_scroll_checkbox.setFont(QFont("Arial", FONT_SIZE_SMALL))
        self.auto_scroll_checkbox.setChecked(True)
        uart_controls.addWidget(self.auto_scroll_checkbox)
        
        uart_controls.addStretch()
        uart_log_layout.addLayout(uart_controls)
        
        self.uart_log_text = QTextEdit()
        self.uart_log_text.setFont(QFont("Consolas", FONT_SIZE_SMALL))
        self.uart_log_text.setStyleSheet("""
            QTextEdit { 
                background-color: #1e1e1e; 
                color: #00ff00; 
                border: 1px solid #555;
                padding: 5px;
            }
        """)
        self.uart_log_text.setReadOnly(True)
        self.uart_log_text.setMaximumHeight(200)
        uart_log_layout.addWidget(self.uart_log_text)
        
        uart_log_group.setLayout(uart_log_layout)
        bottom_splitter.addWidget(uart_log_group)

        # Журнал событий приложения
        app_log_group = QGroupBox("Журнал событий")
        app_log_group.setFont(QFont("Arial", FONT_SIZE_MEDIUM, QFont.Bold))
        app_log_layout = QVBoxLayout()
        
        self.event_log_text = QTextEdit()
        self.event_log_text.setFont(QFont("Consolas", FONT_SIZE_SMALL))
        self.event_log_text.setStyleSheet("QTextEdit { background: #2d2d2d; color: #00ff00; padding: 5px; }")
        
        self.event_log_text.setReadOnly(True)
        self.event_log_text.setMaximumHeight(200)
        app_log_layout.addWidget(self.event_log_text)
        
        app_log_group.setLayout(app_log_layout)
        bottom_splitter.addWidget(app_log_group)
        
        bottom_splitter.setSizes([800, 400])
        main_layout.addWidget(bottom_splitter, stretch=1)

        # ==========================================
        # НОВАЯ: ПАНЕЛЬ ЛОГИРОВАНИЯ
        # ==========================================
        logging_group = QGroupBox("Логирование данных")
        logging_group.setFont(QFont("Arial", FONT_SIZE_MEDIUM, QFont.Bold))
        logging_layout = QHBoxLayout()
        
        self.enable_logging_checkbox = QCheckBox("Включить логирование")
        self.enable_logging_checkbox.setFont(QFont("Arial", FONT_SIZE_MEDIUM))
        self.enable_logging_checkbox.stateChanged.connect(self.toggle_logging)
        logging_layout.addWidget(self.enable_logging_checkbox)
        
        self.log_path_label = QLabel("Файл не выбран")
        self.log_path_label.setFont(QFont("Arial", FONT_SIZE_SMALL))
        self.log_path_label.setStyleSheet("QLabel { color: #aaa; }")
        logging_layout.addWidget(self.log_path_label, stretch=1)
        
        self.choose_log_path_btn = QPushButton("Выбрать файл")
        self.choose_log_path_btn.setFont(QFont("Arial", FONT_SIZE_MEDIUM))
        self.choose_log_path_btn.setMinimumHeight(40)
        self.choose_log_path_btn.clicked.connect(self.choose_log_file)
        logging_layout.addWidget(self.choose_log_path_btn)
        
        self.log_stats_label = QLabel("Записей: 0")
        self.log_stats_label.setFont(QFont("Arial", FONT_SIZE_MEDIUM))
        self.log_stats_label.setStyleSheet("QLabel { color: #2196F3; }")
        logging_layout.addWidget(self.log_stats_label)
        
        logging_group.setLayout(logging_layout)
        main_layout.addWidget(logging_group)

    def refresh_ports(self):
        self.port_combo.clear()
        ports = serial.tools.list_ports.comports()
        for port in ports:
            self.port_combo.addItem(f"{port.device} - {port.description}")
        if not ports:
            self.port_combo.addItem("Нет доступных портов")

    def toggle_connection(self):
        if self.serial_worker.isRunning():
            self.serial_worker.disconnect()
            self.connect_btn.setText("Подключиться")
            self.connect_btn.setStyleSheet("""
                QPushButton { background-color: #4CAF50; color: white; border-radius: 5px; }
                QPushButton:hover { background-color: #45a049; }
            """)
        else:
            selected = self.port_combo.currentText()
            if not selected or selected == "Нет доступных портов":
                QMessageBox.warning(self, "Ошибка", "Выберите COM-порт")
                return
            port_name = selected.split(' - ')[0]
            self.serial_worker.connect(port_name, 115200)
            self.connect_btn.setText("Отключиться")
            self.connect_btn.setStyleSheet("""
                QPushButton { background-color: #f44336; color: white; border-radius: 5px; }
                QPushButton:hover { background-color: #da190b; }
            """)

    def update_connection_status(self, connected):
        self.port_combo.setEnabled(not connected)
        self.refresh_btn.setEnabled(not connected)
        self.scale_btn.setEnabled(connected)
        self.offset_btn.setEnabled(connected)
        self.interval_btn.setEnabled(connected)
        self.threshold_btn.setEnabled(connected)
        self.get_settings_btn.setEnabled(connected)
        self.enable_logging_checkbox.setEnabled(connected)
        if not connected:
            self.enable_logging_checkbox.setChecked(False)

    def send_calib_command(self, cmd_type, value):
        if not self.serial_worker.isRunning():
            QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к устройству")
            return
        try:
            if cmd_type in ['S', 'O']:
                float(value)
            elif cmd_type == 'I':
                val = int(value)
                if not (100 <= val <= 60000):
                    raise ValueError("Интервал должен быть от 100 до 60000 мс")
            self.serial_worker.send_command(f"{cmd_type} {value}")
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка ввода", str(e))
    
    def update_settings_fields(self, scale, offset, interval):
        """Обновить поля настроек значениями с устройства"""
        self.scale_input.setText(scale)
        self.offset_input.setText(offset)
        self.interval_input.setText(interval)
        self.add_log(f"Поля обновлены: SCALE={scale}, OFFSET={offset}, INTERVAL={interval}ms")

    def set_warning_threshold(self):
        """Установить порог предупреждения"""
        try:
            threshold = float(self.threshold_input.text())
            if threshold <= 0:
                raise ValueError("Порог должен быть положительным")
            
            self.warning_threshold = threshold
            
            # Удаляем старую линию порога
            self.plot_widget.removeItem(self.warning_line)
            
            # Создаем новую линию с обновленной подписью
            self.warning_line = self.plot_widget.addLine(
                y=threshold,
                pen=pg.mkPen(color='#FF5722', width=2, style=Qt.DashLine),
                label=f'Порог: {threshold}В'
            )
            
            self.add_log(f"Порог установлен: {threshold}В")
            
            # Проверить текущие значения
            if self.rms_history:
                self.check_warning(self.rms_history[-1], self.peak_history[-1])
        except ValueError as e:
            QMessageBox.warning(self, "Ошибка", str(e))

    def update_plot(self, rms, peak):
        current_time = time.time()
        
        self.rms_history.append(rms)
        self.peak_history.append(peak)
        self.time_history.append(current_time)
        
        self.rms_label.setText(f"Vrms: {rms:.4e} В")
        self.peak_label.setText(f"Vpk: {peak:.4e} В")
        
        times = [t - self.time_history[0] for t in self.time_history]
        self.rms_curve.setData(times, list(self.rms_history))
        self.peak_curve.setData(times, list(self.peak_history))
        
        self.check_warning(rms, peak)
        
        # НОВАЯ: Запись в лог-файл
        if self.logging_enabled and self.log_writer:
            try:
                self.log_writer.writerow([
                    datetime.now().isoformat(),
                    f"{rms:.6e}",
                    f"{peak:.6e}"
                ])
                self.log_file.flush()
                
                # Обновить счётчик записей
                current_count = int(self.log_stats_label.text().split(": ")[1])
                self.log_stats_label.setText(f"Записей: {current_count + 1}")
            except Exception as e:
                self.add_log(f"Ошибка записи в файл: {e}")

    def check_warning(self, rms, peak):
        if peak > self.warning_threshold or rms > self.warning_threshold:
            if not self.is_warning:
                self.is_warning = True
                self.warning_indicator.setText("ПРЕВЫШЕНИЕ ПОРОГА!")
                self.warning_indicator.setStyleSheet("""
                    QLabel { 
                        background-color: #f44336; 
                        color: white; 
                        border-radius: 5px; 
                        padding: 10px;
                        font-weight: bold;
                    }
                """)
                self.add_log(f"⚠ ПРЕВЫШЕНИЕ ПОРОГА! Vpk={peak:.4e}В")
        else:
            if self.is_warning:
                self.is_warning = False
                self.warning_indicator.setText("СТАТУС: НОРМА")
                self.warning_indicator.setStyleSheet("""
                    QLabel { background-color: #4CAF50; color: white; border-radius: 5px; padding: 10px; }
                """)

    # ==========================================
    # НОВЫЕ ФУНКЦИИ: ЛОГИРОВАНИЕ И UART ЛОГ
    # ==========================================
    
    def choose_log_file(self):
        """Выбрать файл для логирования"""
        default_name = f"stpm2_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_path, _ = QFileDialog.getSaveFileName(
        self,
        "Выбрать файл для логирования",
        default_name,
        "Текстовые файлы (*.txt);;CSV файлы (*.csv);;Все файлы (*)"
        )
        
        if file_path:
            self.log_file_path = file_path
            self.log_path_label.setText(file_path)
            self.log_path_label.setStyleSheet("QLabel { color: #4CAF50; }")
            self.add_log(f"Файл для логирования выбран: {file_path}")

    def toggle_logging(self, state):
        """Включить/выключить логирование"""
        if state == Qt.Checked:
            if not self.log_file_path:
                QMessageBox.warning(self, "Ошибка", "Сначала выберите файл для логирования")
                self.enable_logging_checkbox.setChecked(False)
                return
            
            try:
                self.log_file = open(self.log_file_path, 'w', newline='', encoding='utf-8')
                self.log_writer = csv.writer(self.log_file, delimiter=' ')
                self.log_writer.writerow(['Время', 'Vrms (В)', 'Vpk (В)'])
                self.logging_enabled = True
                self.log_stats_label.setText("Записей: 0")
                self.add_log(f"Логирование начато: {self.log_file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось открыть файл: {e}")
                self.enable_logging_checkbox.setChecked(False)
        else:
            if self.log_file:
                self.log_file.close()
                self.log_file = None
                self.log_writer = None
            self.logging_enabled = False
            self.add_log("Логирование остановлено")

    def append_uart_log(self, line):
        """Добавить строку в лог UART"""
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        formatted_line = f"[{timestamp}] {line}\n"
        
        self.uart_log_text.moveCursor(QTextCursor.End)
        self.uart_log_text.insertPlainText(formatted_line)
        
        # Ограничить количество строк
        doc = self.uart_log_text.document()
        if doc.blockCount() > MAX_UART_LOG_LINES:
            cursor = self.uart_log_text.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 50)
            cursor.removeSelectedText()
        
        # Автопрокрутка
        if self.auto_scroll_checkbox.isChecked():
            self.uart_log_text.moveCursor(QTextCursor.End)
            self.uart_log_text.ensureCursorVisible()

    def clear_uart_log(self):
        """Очистить лог UART"""
        self.uart_log_text.clear()
        self.add_log("Лог UART очищен")

    def add_log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] {message}\n"
        
        # 1. Запоминаем текущее положение ползунка прокрутки
        scrollbar = self.event_log_text.verticalScrollBar()
        current_scroll_value = scrollbar.value()
        
        # 2. Вставляем новый текст в конец документа
        cursor = self.event_log_text.textCursor()
        cursor.movePosition(QTextCursor.End)
        cursor.insertText(formatted_message)
        
        # 3. Ограничиваем количество строк (удаляем самые старые, если их > 500)
        doc = self.event_log_text.document()
        if doc.blockCount() > 500:
            cursor = self.event_log_text.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.KeepAnchor, 100)
            cursor.removeSelectedText()
        
        # 4. Возвращаем ползунок на то место, где он был до вставки текста
        # Это полностью отключает "прыжки" экрана вниз
        scrollbar.setValue(current_scroll_value)

    def show_error(self, error_msg):
        QMessageBox.critical(self, "Ошибка", error_msg)
        self.add_log(f"ОШИБКА: {error_msg}")

    def closeEvent(self, event):
        if self.serial_worker.isRunning():
            self.serial_worker.disconnect()
        if self.log_file:
            self.log_file.close()
        event.accept()


# ==========================================
# ЗАПУСК
# ==========================================
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53, 53, 53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(25, 25, 25))
    palette.setColor(QPalette.AlternateBase, QColor(53, 53, 53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53, 53, 53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())