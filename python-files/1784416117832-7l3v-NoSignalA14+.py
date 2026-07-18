import sys
from PySide6.QtCore import Qt, QPoint
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QPushButton, QVBoxLayout, QLabel, QHBoxLayout, QFrame, QScrollArea
from PySide6.QtGui import QFont
from pymobiledevice3.lockdown import create_using_usbmux, NoDeviceConnectedError
from typing import Optional

class DeviceInfoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(720, 650)
        
        # Центральный виджет
        self.central_widget = QWidget()
        self.central_widget.setStyleSheet("""
            QWidget {
                background-color: #0a0a0a;
                border-radius: 16px;
                border: 1px solid #1a1a1a;
            }
        """)
        self.setCentralWidget(self.central_widget)
        
        # Основной layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # ==================== ВЕРХНЯЯ ПАНЕЛЬ ====================
        title_bar = QFrame()
        title_bar.setFixedHeight(55)
        title_bar.setStyleSheet("""
            QFrame {
                background-color: transparent;
                border-bottom: 1px solid #1a1a1a;
                border-top-left-radius: 16px;
                border-top-right-radius: 16px;
            }
        """)
        
        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(20, 0, 15, 0)
        
        # Заголовок
        title_label = QLabel("📱 Device Info")
        title_label.setStyleSheet("""
            color: #ffffff;
            font-size: 17px;
            font-weight: bold;
            background-color: transparent;
        """)
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # Кнопка свернуть
        self.btn_minimize = QPushButton("─")
        self.btn_minimize.setFixedSize(32, 32)
        self.btn_minimize.setCursor(Qt.PointingHandCursor)
        self.btn_minimize.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                border: none;
                border-radius: 8px;
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1a1a1a;
                color: #ffffff;
            }
        """)
        self.btn_minimize.clicked.connect(self.showMinimized)
        title_layout.addWidget(self.btn_minimize)
        
        # Кнопка закрыть
        self.btn_close = QPushButton("✕")
        self.btn_close.setFixedSize(32, 32)
        self.btn_close.setCursor(Qt.PointingHandCursor)
        self.btn_close.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #cc0000;
                color: #ffffff;
            }
        """)
        self.btn_close.clicked.connect(self.close)
        title_layout.addWidget(self.btn_close)
        
        title_bar.setLayout(title_layout)
        main_layout.addWidget(title_bar)
        
        # ==================== ОСНОВНОЙ КОНТЕНТ ====================
        content_widget = QWidget()
        content_widget.setStyleSheet("background-color: transparent;")
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(25, 20, 25, 25)
        content_layout.setSpacing(15)
        
        # Скролл-область
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: #0d0d0d;
                border: 1px solid #1a1a1a;
                border-radius: 12px;
            }
            QScrollBar:vertical {
                background-color: #0d0d0d;
                width: 10px;
                border-radius: 5px;
                margin: 2px;
            }
            QScrollBar::handle:vertical {
                background-color: #2a2a2a;
                border-radius: 5px;
                min-height: 30px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: #3a3a3a;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        # Контейнер для текста
        self.info_container = QWidget()
        self.info_container.setStyleSheet("background-color: transparent;")
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(20, 20, 20, 20)
        info_layout.setSpacing(2)
        
        self.label_info = QLabel("Нажмите кнопку для получения информации об устройстве")
        self.label_info.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.label_info.setWordWrap(True)
        self.label_info.setStyleSheet("""
            color: #aaaaaa;
            font-size: 13px;
            background-color: transparent;
            font-family: 'Segoe UI', 'Consolas', monospace;
            line-height: 1.8;
            padding: 5px;
        """)
        info_layout.addWidget(self.label_info)
        info_layout.addStretch()
        
        self.info_container.setLayout(info_layout)
        self.scroll_area.setWidget(self.info_container)
        content_layout.addWidget(self.scroll_area)
        
        # Кнопка
        self.btn_get_info = QPushButton("📱 Получить информацию об устройстве")
        self.btn_get_info.setFixedHeight(48)
        self.btn_get_info.setCursor(Qt.PointingHandCursor)
        self.btn_get_info.setStyleSheet("""
            QPushButton {
                background-color: #00d5ff;
                color: #000000;
                border: none;
                border-radius: 12px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #00e5ff;
            }
            QPushButton:pressed {
                background-color: #00b5dd;
            }
        """)
        self.btn_get_info.clicked.connect(self.get_full_device_info)
        content_layout.addWidget(self.btn_get_info)
        
        content_widget.setLayout(content_layout)
        main_layout.addWidget(content_widget)
        
        self.central_widget.setLayout(main_layout)
        
        # Для перетаскивания
        self.drag_position = None
        title_bar.mousePressEvent = self.mousePressEvent
        title_bar.mouseMoveEvent = self.mouseMoveEvent

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_position is not None:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

    def get_full_device_info(self) -> Optional[dict]:
        try:
            lockdown = create_using_usbmux()
            values = lockdown.all_values
            
            info = {
                "DeviceName": values.get("DeviceName", "Unknown"),
                "ProductType": values.get("ProductType", "Unknown"),
                "ProductVersion": values.get("ProductVersion", "Unknown"),
                "BuildVersion": values.get("BuildVersion", "Unknown"),
                "SerialNumber": values.get("SerialNumber", "Unknown"),
                "UniqueDeviceID": values.get("UniqueDeviceID", "Unknown"),
                "ActivationState": values.get("ActivationState", "Unknown"),
                "ModelNumber": values.get("ModelNumber", "Unknown"),
                "CPUArchitecture": values.get("CPUArchitecture", "Unknown"),
                "IntegratedCircuitCardIdentity": values.get("IntegratedCircuitCardIdentity", "Unknown"),
                "InternationalMobileEquipmentIdentity": values.get("InternationalMobileEquipmentIdentity", "Unknown"),
                "TotalDataCapacity": values.get("TotalDataCapacity", "Unknown"),
                "TotalDataAvailable": values.get("TotalDataAvailable", "Unknown"),
                "RegionInfo": values.get("RegionInfo", "Unknown"),
                "TimeZone": values.get("TimeZone", "Unknown"),
                "UserLanguage": values.get("UserLanguage", "Unknown"),
                "DeviceClass": values.get("DeviceClass", "Unknown"),
            }
            
            lockdown.close()
            
            # Красивый текст без кривых линий
            info_text = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            info_text += "          📱 ИНФОРМАЦИЯ ОБ УСТРОЙСТВЕ          \n"
            info_text += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
            
            info_text += f"  Имя:              {info['DeviceName']}\n"
            info_text += f"  Модель:           {info['ProductType']}\n"
            info_text += f"  iOS:              {info['ProductVersion']} (Build: {info['BuildVersion']})\n"
            info_text += f"  Серийный номер:   {info['SerialNumber']}\n"
            info_text += f"  UDID:             {info['UniqueDeviceID']}\n"
            info_text += f"  Активация:        {info['ActivationState']}\n"
            
            info_text += "\n  ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─\n\n"
            
            info_text += f"  Номер модели:     {info['ModelNumber']}\n"
            info_text += f"  Архитектура:      {info['CPUArchitecture']}\n"
            info_text += f"  Класс:            {info['DeviceClass']}\n"
            info_text += f"  Регион:           {info['RegionInfo']}\n"
            info_text += f"  Язык:             {info['UserLanguage']}\n"
            info_text += f"  Часовой пояс:     {info['TimeZone']}\n"
            info_text += f"  ICCID:            {info['IntegratedCircuitCardIdentity']}\n"
            info_text += f"  IMEI:             {info['InternationalMobileEquipmentIdentity']}\n"
            
            if info['TotalDataCapacity'] != "Unknown":
                try:
                    capacity_gb = int(info['TotalDataCapacity']) / (1024**3)
                    available_gb = int(info['TotalDataAvailable']) / (1024**3)
                    info_text += f"\n  💾 Хранилище:     {capacity_gb:.1f} GB (Доступно: {available_gb:.1f} GB)\n"
                except:
                    pass
            
            info_text += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            
            self.label_info.setText(info_text)
            self.scroll_area.verticalScrollBar().setValue(0)
            
            return info
            
        except NoDeviceConnectedError:
            error_msg = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            error_msg += "    ❌ УСТРОЙСТВО НЕ ПОДКЛЮЧЕНО!\n"
            error_msg += "    Подключите iPhone/iPad через USB\n"
            error_msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            self.label_info.setText(error_msg)
            return None
            
        except Exception as e:
            error_msg = "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            error_msg += f"    ❌ ОШИБКА: {str(e)[:40]}\n"
            error_msg += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            self.label_info.setText(error_msg)
            return None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DeviceInfoApp()
    window.show()
    sys.exit(app.exec())