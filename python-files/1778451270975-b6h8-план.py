import sys
import math
import json
import csv
import traceback
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QSpinBox, QFileDialog, QGroupBox, QListWidget,
    QMessageBox, QTabWidget, QDoubleSpinBox, QCheckBox, QComboBox,
    QSlider, QColorDialog, QTextEdit, QSplitter, QTreeWidget, 
    QTreeWidgetItem, QProgressBar, QInputDialog, QLineEdit
)
from PyQt5.QtCore import Qt, QPointF, pyqtSignal, QRect, QTimer, QSize
from PyQt5.QtGui import (
    QPainter, QPen, QColor, QBrush, QPixmap, QPolygonF, QWheelEvent,
    QImage, QFont, QTransform, QPainterPath, QRadialGradient
)

class Camera:
    def __init__(self, x, y, angle=0, view_angle=90, range_length=200, 
                 sensitivity=50, name="", color=None):
        self.x = x
        self.y = y
        self.angle = angle
        self.view_angle = view_angle
        self.range = range_length
        self.sensitivity = sensitivity  # Чувствительность (0-100)
        self.name = name or f"Камера {id(self)}"
        self.color = color or QColor(100, 100, 255)
        self.id = None
        self.connections = []  # Соединения с другими камерами
        self.enabled = True
        self.recording = False
    
    def get_view_polygon(self):
        start_angle = self.angle - self.view_angle / 2
        end_angle = self.angle + self.view_angle / 2
        start_rad = math.radians(start_angle)
        end_rad = math.radians(end_angle)
        
        points = []
        center = QPointF(self.x, self.y)
        num_segments = 30
        
        for i in range(num_segments + 1):
            t = i / num_segments
            angle_rad = start_rad + (end_rad - start_rad) * t
            x = self.x + self.range * math.cos(angle_rad)
            y = self.y - self.range * math.sin(angle_rad)
            points.append(QPointF(x, y))
        
        points.append(center)
        return QPolygonF(points)
    
    def get_coverage_area(self):
        """Вычисляет площадь покрытия"""
        return (math.pi * (self.range ** 2) * (self.view_angle / 360))

class DrawingArea(QWidget):
    camera_selected = pyqtSignal(object)
    coverage_updated = pyqtSignal(float)
    
    def __init__(self):
        super().__init__()
        self.background_image = None
        self.cameras = []
        self.selected_camera = None
        self.dragging_camera = None
        self.drag_offset = None
        self.scale_factor = 1.0
        self.pan_x = 0
        self.pan_y = 0
        self.show_coverage = True
        self.show_connections = True
        self.show_shadows = True
        self.show_grid = False
        self.grid_size = 50
        self.zoom_timer = QTimer()
        self.zoom_timer.setSingleShot(True)
        
        self.setMinimumSize(800, 600)
        self.setMouseTracking(True)
        self.setStyleSheet("background-color: #1e1e1e;")
        
        # Для панорамирования
        self.last_pan_point = None
        self.panning = False
    
    def load_background(self, filename):
        try:
            pixmap = QPixmap(filename)
            if not pixmap.isNull():
                self.background_image = pixmap
                self.update()
                return True
            return False
        except Exception as e:
            print(f"Ошибка загрузки: {e}")
            return False
    
    def paintEvent(self, event):
        try:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            
            painter.translate(self.pan_x, self.pan_y)
            painter.scale(self.scale_factor, self.scale_factor)
            
            # Рисуем фон
            if self.background_image and not self.background_image.isNull():
                painter.drawPixmap(0, 0, self.background_image)
            else:
                painter.fillRect(0, 0, self.width(), self.height(), 
                               QBrush(QColor(30, 30, 30)))
                painter.setPen(QPen(QColor(200, 200, 200)))
                painter.drawText(QRect(0, 0, self.width(), self.height()), 
                               Qt.AlignCenter, 
                               "📷 Планировщик камер наблюдения\n\n"
                               "1. Загрузите план (Файл → Загрузить план)\n"
                               "2. Добавьте камеры\n"
                               "3. Настройте зоны обзора")
            
            # Рисуем сетку
            if self.show_grid:
                self.draw_grid(painter)
            
            # Рисуем соединения между камерами
            if self.show_connections:
                self.draw_connections(painter)
            
            # Рисуем камеры
            for camera in self.cameras:
                if camera.enabled:
                    self.draw_camera(painter, camera)
            
            painter.resetTransform()
            
            # Рисуем HUD
            self.draw_hud(painter)
            
            painter.end()
        except Exception as e:
            print(f"Ошибка paintEvent: {e}")
    
    def draw_grid(self, painter):
        """Рисует координатную сетку"""
        painter.setPen(QPen(QColor(80, 80, 80, 100), 1, Qt.DashLine))
        
        width = self.background_image.width() if self.background_image else 2000
        height = self.background_image.height() if self.background_image else 2000
        
        for x in range(0, width, self.grid_size):
            painter.drawLine(x, 0, x, height)
        
        for y in range(0, height, self.grid_size):
            painter.drawLine(0, y, width, y)
    
    def draw_connections(self, painter):
        """Рисует соединения между камерами"""
        for camera in self.cameras:
            for conn in camera.connections:
                if conn in self.cameras and conn.enabled:
                    painter.setPen(QPen(QColor(255, 200, 0, 150), 2, Qt.DashLine))
                    painter.drawLine(QPointF(camera.x, camera.y), 
                                   QPointF(conn.x, conn.y))
    
    def draw_camera(self, painter, camera):
        try:
            # Тень
            if self.show_shadows:
                painter.save()
                painter.setBrush(QBrush(QColor(0, 0, 0, 50)))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(camera.x + 3, camera.y + 3), 10, 10)
                painter.restore()
            
            # Сектор обзора
            if self.show_coverage:
                alpha = int(80 * (camera.sensitivity / 100))
                view_polygon = camera.get_view_polygon()
                
                if camera == self.selected_camera:
                    brush_color = QColor(255, 100, 100, alpha)
                    border_color = QColor(255, 0, 0)
                else:
                    brush_color = QColor(camera.color.red(), camera.color.green(),
                                       camera.color.blue(), alpha)
                    border_color = camera.color
                
                painter.setBrush(QBrush(brush_color))
                painter.setPen(QPen(border_color, 2))
                painter.drawPolygon(view_polygon)
            
            # Центр камеры с градиентом
            gradient = QRadialGradient(camera.x, camera.y, 15)
            if camera == self.selected_camera:
                gradient.setColorAt(0, QColor(255, 100, 100))
                gradient.setColorAt(1, QColor(200, 0, 0))
            else:
                gradient.setColorAt(0, QColor(camera.color.red(), camera.color.green(),
                                            camera.color.blue()))
                gradient.setColorAt(1, QColor(camera.color.red() // 2,
                                            camera.color.green() // 2,
                                            camera.color.blue() // 2))
            
            painter.setBrush(QBrush(gradient))
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawEllipse(QPointF(camera.x, camera.y), 10, 10)
            
            # Индикатор записи
            if camera.recording:
                painter.setBrush(QBrush(QColor(255, 0, 0)))
                painter.setPen(Qt.NoPen)
                painter.drawEllipse(QPointF(camera.x + 12, camera.y - 12), 4, 4)
            
            # Линия направления
            end_x = camera.x + 45 * math.cos(math.radians(camera.angle))
            end_y = camera.y - 45 * math.sin(math.radians(camera.angle))
            painter.setPen(QPen(QColor(255, 255, 0), 3))
            painter.drawLine(QPointF(camera.x, camera.y), QPointF(end_x, end_y))
            
            # ID или имя камеры
            painter.setFont(QFont("Arial", 10, QFont.Bold))
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            text = camera.name if len(camera.name) < 15 else camera.name[:12] + "..."
            painter.drawText(QPointF(camera.x - 20, camera.y - 15), text)
            
            # Угол обзора текстом
            painter.setFont(QFont("Arial", 8))
            painter.setPen(QPen(QColor(200, 200, 200), 1))
            painter.drawText(QPointF(camera.x - 15, camera.y + 20), 
                           f"{camera.view_angle}°")
            
        except Exception as e:
            print(f"Ошибка draw_camera: {e}")
    
    def draw_hud(self, painter):
        """Рисует интерфейс поверх сцены"""
        painter.resetTransform()
        
        # Информация о масштабе
        info_text = f"Масштаб: {self.scale_factor:.1f}x | Камер: {len(self.cameras)}"
        if self.selected_camera:
            info_text += f" | Выбрана: {self.selected_camera.name}"
        
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
        painter.drawRect(10, 10, 300, 30)
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawText(20, 32, info_text)
        
        # Легенда
        if self.show_coverage:
            legend_y = self.height() - 100
            painter.setBrush(QBrush(QColor(0, 0, 0, 150)))
            painter.drawRect(10, legend_y - 30, 200, 80)
            painter.setPen(QPen(QColor(255, 255, 255), 1))
            painter.drawText(20, legend_y, "📷 Зоны обзора")
            painter.drawText(20, legend_y + 20, "🟡 Линии связи")
            painter.drawText(20, legend_y + 40, "🔴 Индикатор записи")
    
    def mousePressEvent(self, event):
        try:
            # Средняя кнопка для панорамирования
            if event.button() == Qt.MiddleButton:
                self.panning = True
                self.last_pan_point = event.pos()
                return
            
            pos = self.transform_to_scene_coords(event.pos())
            
            # Проверяем попадание в камеру
            for camera in reversed(self.cameras):
                distance = math.sqrt((camera.x - pos.x())**2 + (camera.y - pos.y())**2)
                if distance < 15:
                    self.selected_camera = camera
                    self.camera_selected.emit(camera)
                    self.dragging_camera = camera
                    self.drag_offset = (pos.x() - camera.x, pos.y() - camera.y)
                    self.update()
                    return
            
            self.selected_camera = None
            self.camera_selected.emit(None)
            self.update()
        except Exception as e:
            print(f"Ошибка mousePress: {e}")
    
    def mouseMoveEvent(self, event):
        try:
            if self.panning and self.last_pan_point:
                delta = event.pos() - self.last_pan_point
                self.pan_x += delta.x()
                self.pan_y += delta.y()
                self.last_pan_point = event.pos()
                self.update()
            
            elif self.dragging_camera:
                pos = self.transform_to_scene_coords(event.pos())
                new_x = pos.x() - self.drag_offset[0]
                new_y = pos.y() - self.drag_offset[1]
                
                if self.background_image and not self.background_image.isNull():
                    new_x = max(10, min(new_x, self.background_image.width() - 10))
                    new_y = max(10, min(new_y, self.background_image.height() - 10))
                
                self.dragging_camera.x = new_x
                self.dragging_camera.y = new_y
                self.update()
                self.calculate_coverage()  # Пересчитываем покрытие
        except Exception as e:
            print(f"Ошибка mouseMove: {e}")
    
    def mouseReleaseEvent(self, event):
        self.dragging_camera = None
        self.drag_offset = None
        self.panning = False
        self.last_pan_point = None
        self.update()
    
    def wheelEvent(self, event):
        try:
            # Масштабирование относительно курсора
            old_pos = self.transform_to_scene_coords(event.pos())
            
            delta = event.angleDelta().y()
            if delta > 0:
                self.scale_factor *= 1.1
            else:
                self.scale_factor /= 1.1
            
            self.scale_factor = max(0.1, min(self.scale_factor, 10.0))
            
            # Корректируем панорамирование
            new_pos = self.transform_to_scene_coords(event.pos())
            self.pan_x += (new_pos.x() - old_pos.x()) * self.scale_factor
            self.pan_y += (new_pos.y() - old_pos.y()) * self.scale_factor
            
            self.update()
        except Exception as e:
            print(f"Ошибка wheel: {e}")
    
    def transform_to_scene_coords(self, pos):
        try:
            x = (pos.x() - self.pan_x) / self.scale_factor
            y = (pos.y() - self.pan_y) / self.scale_factor
            return QPointF(x, y)
        except:
            return QPointF(0, 0)
    
    def calculate_coverage(self):
        """Расчет процента покрытия площади"""
        if not self.background_image:
            return 0
        
        total_area = self.background_image.width() * self.background_image.height()
        covered_area = sum(c.get_coverage_area() for c in self.cameras if c.enabled)
        
        # Избегаем двойного подсчета перекрытий
        coverage_percent = min(100, (covered_area / total_area) * 100)
        self.coverage_updated.emit(coverage_percent)
        return coverage_percent
    
    def export_to_image(self, filename):
        """Экспорт текущего вида в изображение"""
        try:
            pixmap = QPixmap(self.size())
            self.render(pixmap)
            pixmap.save(filename)
            return True
        except Exception as e:
            print(f"Ошибка экспорта: {e}")
            return False

class ExtendedCameraPlanner(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Расширенный планировщик камер наблюдения v2.0")
        self.setGeometry(100, 100, 1400, 900)
        
        # Центральный виджет с разделителем
        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)
        
        # Область рисования
        self.drawing_area = DrawingArea()
        self.drawing_area.camera_selected.connect(self.on_camera_selected)
        self.drawing_area.coverage_updated.connect(self.update_coverage_display)
        splitter.addWidget(self.drawing_area)
        
        # Правая панель с вкладками
        self.right_panel = QTabWidget()
        self.right_panel.setMaximumWidth(350)
        splitter.addWidget(self.right_panel)
        
        # Создаем вкладки
        self.setup_camera_tab()
        self.setup_visual_tab()
        self.setup_stats_tab()
        self.setup_file_tab()
        
        # Переменные
        self.current_camera = None
        self.clipboard = None
        
        # Создаем меню
        self.create_menu()
        
        # Статусбар
        self.statusBar().showMessage("Готов к работе | Используйте среднюю кнопку мыши для панорамирования")
    
    def setup_camera_tab(self):
        """Настройка вкладки управления камерами"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Загрузка плана
        load_group = QGroupBox("1. Загрузка плана")
        load_layout = QVBoxLayout()
        self.load_btn = QPushButton("📁 Загрузить план")
        self.load_btn.clicked.connect(self.load_background)
        self.load_btn.setStyleSheet("padding: 10px; font-size: 12px;")
        load_layout.addWidget(self.load_btn)
        
        self.load_sample_btn = QPushButton("🎨 Создать пустой план")
        self.load_sample_btn.clicked.connect(self.create_empty_plan)
        load_layout.addWidget(self.load_sample_btn)
        
        load_group.setLayout(load_layout)
        layout.addWidget(load_group)
        
        # Список камер
        layout.addWidget(QLabel("📋 Список камер:"))
        self.camera_tree = QTreeWidget()
        self.camera_tree.setHeaderLabels(["Камера", "Статус"])
        self.camera_tree.setMaximumHeight(200)
        self.camera_tree.itemClicked.connect(self.select_camera_from_tree)
        layout.addWidget(self.camera_tree)
        
        # Добавление камеры
        add_group = QGroupBox("2. Добавление камеры")
        add_layout = QVBoxLayout()
        
        self.camera_name_input = QLineEdit()
        self.camera_name_input.setPlaceholderText("Имя камеры (опционально)")
        add_layout.addWidget(self.camera_name_input)
        
        self.add_camera_btn = QPushButton("➕ Добавить новую камеру")
        self.add_camera_btn.clicked.connect(self.add_camera)
        self.add_camera_btn.setEnabled(False)
        self.add_camera_btn.setStyleSheet("padding: 10px; background-color: #4CAF50;")
        add_layout.addWidget(self.add_camera_btn)
        
        add_group.setLayout(add_layout)
        layout.addWidget(add_group)
        
        # Настройки камеры
        settings_group = QGroupBox("3. Настройки камеры")
        settings_layout = QVBoxLayout()
        
        # Имя камеры
        name_layout = QHBoxLayout()
        name_layout.addWidget(QLabel("Имя:"))
        self.camera_name_edit = QLineEdit()
        self.camera_name_edit.textChanged.connect(self.update_camera_name)
        name_layout.addWidget(self.camera_name_edit)
        settings_layout.addLayout(name_layout)
        
        # Направление
        angle_layout = QHBoxLayout()
        angle_layout.addWidget(QLabel("Направление:"))
        self.angle_spin = QSpinBox()
        self.angle_spin.setRange(0, 359)
        self.angle_spin.valueChanged.connect(self.update_camera_angle)
        angle_layout.addWidget(self.angle_spin)
        angle_layout.addWidget(QLabel("°"))
        settings_layout.addLayout(angle_layout)
        
        # Угол обзора
        view_layout = QHBoxLayout()
        view_layout.addWidget(QLabel("Угол обзора:"))
        self.view_angle_spin = QSpinBox()
        self.view_angle_spin.setRange(10, 180)
        self.view_angle_spin.valueChanged.connect(self.update_camera_view_angle)
        view_layout.addWidget(self.view_angle_spin)
        view_layout.addWidget(QLabel("°"))
        settings_layout.addLayout(view_layout)
        
        # Дальность
        range_layout = QHBoxLayout()
        range_layout.addWidget(QLabel("Дальность:"))
        self.range_spin = QSpinBox()
        self.range_spin.setRange(50, 800)
        self.range_spin.valueChanged.connect(self.update_camera_range)
        range_layout.addWidget(self.range_spin)
        range_layout.addWidget(QLabel("px"))
        settings_layout.addLayout(range_layout)
        
        # Чувствительность
        sens_layout = QHBoxLayout()
        sens_layout.addWidget(QLabel("Чувствительность:"))
        self.sensitivity_slider = QSlider(Qt.Horizontal)
        self.sensitivity_slider.setRange(0, 100)
        self.sensitivity_slider.valueChanged.connect(self.update_camera_sensitivity)
        sens_layout.addWidget(self.sensitivity_slider)
        self.sensitivity_label = QLabel("50%")
        sens_layout.addWidget(self.sensitivity_label)
        settings_layout.addLayout(sens_layout)
        
        # Цвет камеры
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Цвет:"))
        self.color_btn = QPushButton("Выбрать цвет")
        self.color_btn.clicked.connect(self.choose_camera_color)
        color_layout.addWidget(self.color_btn)
        settings_layout.addLayout(color_layout)
        
        # Включение/выключение
        self.enable_check = QCheckBox("Камера активна")
        self.enable_check.toggled.connect(self.toggle_camera_enabled)
        settings_layout.addWidget(self.enable_check)
        
        self.recording_check = QCheckBox("Запись видео")
        self.recording_check.toggled.connect(self.toggle_camera_recording)
        settings_layout.addWidget(self.recording_check)
        
        settings_group.setLayout(settings_layout)
        layout.addWidget(settings_group)
        
        # Кнопки управления
        control_group = QGroupBox("Управление")
        control_layout = QVBoxLayout()
        
        btn_layout = QHBoxLayout()
        self.remove_camera_btn = QPushButton("❌ Удалить")
        self.remove_camera_btn.clicked.connect(self.remove_camera)
        btn_layout.addWidget(self.remove_camera_btn)
        
        self.duplicate_btn = QPushButton("📋 Дублировать")
        self.duplicate_btn.clicked.connect(self.duplicate_camera)
        btn_layout.addWidget(self.duplicate_btn)
        control_layout.addLayout(btn_layout)
        
        self.clear_cameras_btn = QPushButton("🗑 Очистить все")
        self.clear_cameras_btn.clicked.connect(self.clear_cameras)
        control_layout.addWidget(self.clear_cameras_btn)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        self.right_panel.addTab(tab, "Камеры")
    
    def setup_visual_tab(self):
        """Настройка вкладки визуализации"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Настройки отображения
        display_group = QGroupBox("Отображение")
        display_layout = QVBoxLayout()
        
        self.show_coverage_check = QCheckBox("Показывать зоны обзора")
        self.show_coverage_check.setChecked(True)
        self.show_coverage_check.toggled.connect(lambda: setattr(self.drawing_area, 'show_coverage', self.show_coverage_check.isChecked()))
        display_layout.addWidget(self.show_coverage_check)
        
        self.show_connections_check = QCheckBox("Показывать связи между камерами")
        self.show_connections_check.setChecked(True)
        self.show_connections_check.toggled.connect(lambda: setattr(self.drawing_area, 'show_connections', self.show_connections_check.isChecked()))
        display_layout.addWidget(self.show_connections_check)
        
        self.show_shadows_check = QCheckBox("Показывать тени")
        self.show_shadows_check.setChecked(True)
        self.show_shadows_check.toggled.connect(lambda: setattr(self.drawing_area, 'show_shadows', self.show_shadows_check.isChecked()))
        display_layout.addWidget(self.show_shadows_check)
        
        self.show_grid_check = QCheckBox("Показывать сетку")
        self.show_grid_check.toggled.connect(lambda: setattr(self.drawing_area, 'show_grid', self.show_grid_check.isChecked()))
        display_layout.addWidget(self.show_grid_check)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        # Сетка
        grid_group = QGroupBox("Настройки сетки")
        grid_layout = QVBoxLayout()
        
        grid_size_layout = QHBoxLayout()
        grid_size_layout.addWidget(QLabel("Размер ячейки:"))
        self.grid_size_spin = QSpinBox()
        self.grid_size_spin.setRange(20, 200)
        self.grid_size_spin.setValue(50)
        self.grid_size_spin.valueChanged.connect(lambda v: setattr(self.drawing_area, 'grid_size', v))
        grid_size_layout.addWidget(self.grid_size_spin)
        grid_layout.addLayout(grid_size_layout)
        
        grid_group.setLayout(grid_layout)
        layout.addWidget(grid_group)
        
        # Экспорт
        export_group = QGroupBox("Экспорт изображения")
        export_layout = QVBoxLayout()
        
        self.export_image_btn = QPushButton("📸 Сохранить как изображение")
        self.export_image_btn.clicked.connect(self.export_as_image)
        export_layout.addWidget(self.export_image_btn)
        
        export_group.setLayout(export_layout)
        layout.addWidget(export_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        self.right_panel.addTab(tab, "Визуализация")
    
    def setup_stats_tab(self):
        """Настройка вкладки статистики"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Общая статистика
        stats_group = QGroupBox("Общая статистика")
        stats_layout = QVBoxLayout()
        
        self.total_cameras_label = QLabel("Всего камер: 0")
        stats_layout.addWidget(self.total_cameras_label)
        
        self.active_cameras_label = QLabel("Активных камер: 0")
        stats_layout.addWidget(self.active_cameras_label)
        
        self.coverage_label = QLabel("Покрытие площади: 0%")
        stats_layout.addWidget(self.coverage_label)
        
        self.coverage_bar = QProgressBar()
        self.coverage_bar.setRange(0, 100)
        stats_layout.addWidget(self.coverage_bar)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Детальная статистика
        detail_group = QGroupBox("Детальная информация")
        detail_layout = QVBoxLayout()
        
        self.stats_text = QTextEdit()
        self.stats_text.setReadOnly(True)
        self.stats_text.setMaximumHeight(300)
        detail_layout.addWidget(self.stats_text)
        
        detail_group.setLayout(detail_layout)
        layout.addWidget(detail_group)
        
        # Кнопка обновления
        self.refresh_stats_btn = QPushButton("🔄 Обновить статистику")
        self.refresh_stats_btn.clicked.connect(self.update_statistics)
        layout.addWidget(self.refresh_stats_btn)
        
        layout.addStretch()
        tab.setLayout(layout)
        self.right_panel.addTab(tab, "Статистика")
    
    def setup_file_tab(self):
        """Настройка вкладки файлов"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        # Сохранение/загрузка
        file_group = QGroupBox("Сохранение и загрузка")
        file_layout = QVBoxLayout()
        
        self.save_json_btn = QPushButton("💾 Сохранить как JSON")
        self.save_json_btn.clicked.connect(self.save_json_config)
        file_layout.addWidget(self.save_json_btn)
        
        self.load_json_btn = QPushButton("📂 Загрузить JSON")
        self.load_json_btn.clicked.connect(self.load_json_config)
        file_layout.addWidget(self.load_json_btn)
        
        self.export_csv_btn = QPushButton("📊 Экспорт в CSV")
        self.export_csv_btn.clicked.connect(self.export_to_csv)
        file_layout.addWidget(self.export_csv_btn)
        
        self.import_csv_btn = QPushButton("📥 Импорт из CSV")
        self.import_csv_btn.clicked.connect(self.import_from_csv)
        file_layout.addWidget(self.import_csv_btn)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Отчеты
        report_group = QGroupBox("Отчеты")
        report_layout = QVBoxLayout()
        
        self.generate_report_btn = QPushButton("📄 Сгенерировать отчет")
        self.generate_report_btn.clicked.connect(self.generate_report)
        report_layout.addWidget(self.generate_report_btn)
        
        report_group.setLayout(report_layout)
        layout.addWidget(report_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        self.right_panel.addTab(tab, "Файлы")
    
    def create_menu(self):
        """Создание главного меню"""
        menubar = self.menuBar()
        
        # Меню Файл
        file_menu = menubar.addMenu("Файл")
        
        load_action = file_menu.addAction("Загрузить план")
        load_action.triggered.connect(self.load_background)
        
        file_menu.addSeparator()
        
        save_action = file_menu.addAction("Сохранить конфигурацию")
        save_action.triggered.connect(self.save_json_config)
        
        load_config_action = file_menu.addAction("Загрузить конфигурацию")
        load_config_action.triggered.connect(self.load_json_config)
        
        file_menu.addSeparator()
        
        exit_action = file_menu.addAction("Выход")
        exit_action.triggered.connect(self.close)
        
        # Меню Вид
        view_menu = menubar.addMenu("Вид")
        
        reset_view_action = view_menu.addAction("Сбросить масштаб")
        reset_view_action.triggered.connect(self.reset_view)
        
        # Меню Камера
        camera_menu = menubar.addMenu("Камера")
        
        add_camera_action = camera_menu.addAction("Добавить камеру")
        add_camera_action.triggered.connect(self.add_camera)
        
        remove_camera_action = camera_menu.addAction("Удалить выбранную камеру")
        remove_camera_action.triggered.connect(self.remove_camera)
        
        # Меню Справка
        help_menu = menubar.addMenu("Справка")
        
        about_action = help_menu.addAction("О программе")
        about_action.triggered.connect(self.show_about)
    
    def load_background(self):
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self, "Выберите план местности", "", 
                "Изображения (*.png *.jpg *.jpeg *.bmp);;Все файлы (*.*)"
            )
            if filename and filename.strip():
                if self.drawing_area.load_background(filename):
                    self.add_camera_btn.setEnabled(True)
                    self.statusBar().showMessage(f"Загружен план: {filename.split('/')[-1]}")
                    QMessageBox.information(self, "Успех", "План успешно загружен!")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось загрузить изображение.")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка загрузки: {str(e)}")
    
    def create_empty_plan(self):
        """Создание пустого плана с заданным размером"""
        width, ok1 = QInputDialog.getInt(self, "Размер плана", "Ширина (пиксели):", 1920, 800, 3840)
        if not ok1:
            return
        height, ok2 = QInputDialog.getInt(self, "Размер плана", "Высота (пиксели):", 1080, 600, 2160)
        if not ok2:
            return
        
        # Создаем пустое изображение
        pixmap = QPixmap(width, height)
        pixmap.fill(QColor(40, 40, 40))
        self.drawing_area.background_image = pixmap
        self.add_camera_btn.setEnabled(True)
        self.statusBar().showMessage(f"Создан пустой план {width}x{height}")
    
    def add_camera(self):
        try:
            if not self.drawing_area.background_image:
                QMessageBox.warning(self, "Предупреждение", "Сначала загрузите или создайте план!")
                return
            
            # Определяем позицию
            if self.drawing_area.background_image:
                center_x = self.drawing_area.background_image.width() / 2
                center_y = self.drawing_area.background_image.height() / 2
            else:
                center_x = 400
                center_y = 300
            
            name = self.camera_name_input.text().strip()
            if not name:
                name = f"Камера {len(self.drawing_area.cameras) + 1}"
            
            camera = Camera(center_x, center_y,
                           angle=self.angle_spin.value(),
                           view_angle=self.view_angle_spin.value(),
                           range_length=self.range_spin.value(),
                           sensitivity=self.sensitivity_slider.value(),
                           name=name)
            
            self.drawing_area.cameras.append(camera)
            self.update_camera_list()
            self.drawing_area.update()
            
            self.drawing_area.selected_camera = camera
            self.on_camera_selected(camera)
            self.update_statistics()
            
            self.statusBar().showMessage(f"Добавлена {name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось добавить камеру: {str(e)}")
    
    def duplicate_camera(self):
        """Дублирование выбранной камеры"""
        if self.current_camera:
            new_camera = Camera(
                self.current_camera.x + 50,
                self.current_camera.y + 50,
                self.current_camera.angle,
                self.current_camera.view_angle,
                self.current_camera.range,
                self.current_camera.sensitivity,
                f"{self.current_camera.name} (копия)"
            )
            self.drawing_area.cameras.append(new_camera)
            self.update_camera_list()
            self.drawing_area.update()
            self.statusBar().showMessage(f"Камера дублирована")
    
    def update_camera_list(self):
        """Обновление дерева камер"""
        self.camera_tree.clear()
        for i, camera in enumerate(self.drawing_area.cameras, 1):
            camera.id = i
            item = QTreeWidgetItem([camera.name, "🟢 Активна" if camera.enabled else "🔴 Отключена"])
            item.setData(0, Qt.UserRole, camera)
            self.camera_tree.addTopLevelItem(item)
    
    def select_camera_from_tree(self, item):
        """Выбор камеры из дерева"""
        camera = item.data(0, Qt.UserRole)
        if camera:
            self.drawing_area.selected_camera = camera
            self.on_camera_selected(camera)
            self.drawing_area.update()
    
    def on_camera_selected(self, camera):
        self.current_camera = camera
        if camera:
            # Блокируем сигналы
            self.angle_spin.blockSignals(True)
            self.view_angle_spin.blockSignals(True)
            self.range_spin.blockSignals(True)
            self.sensitivity_slider.blockSignals(True)
            self.enable_check.blockSignals(True)
            self.recording_check.blockSignals(True)
            self.camera_name_edit.blockSignals(True)
            
            # Устанавливаем значения
            self.angle_spin.setValue(int(camera.angle))
            self.view_angle_spin.setValue(int(camera.view_angle))
            self.range_spin.setValue(int(camera.range))
            self.sensitivity_slider.setValue(camera.sensitivity)
            self.sensitivity_label.setText(f"{camera.sensitivity}%")
            self.enable_check.setChecked(camera.enabled)
            self.recording_check.setChecked(camera.recording)
            self.camera_name_edit.setText(camera.name)
            
            # Разблокируем
            self.angle_spin.blockSignals(False)
            self.view_angle_spin.blockSignals(False)
            self.range_spin.blockSignals(False)
            self.sensitivity_slider.blockSignals(False)
            self.enable_check.blockSignals(False)
            self.recording_check.blockSignals(False)
            self.camera_name_edit.blockSignals(False)
    
    def update_camera_angle(self):
        if self.current_camera:
            self.current_camera.angle = self.angle_spin.value()
            self.drawing_area.update()
    
    def update_camera_view_angle(self):
        if self.current_camera:
            self.current_camera.view_angle = self.view_angle_spin.value()
            self.drawing_area.update()
            self.drawing_area.calculate_coverage()
    
    def update_camera_range(self):
        if self.current_camera:
            self.current_camera.range = self.range_spin.value()
            self.drawing_area.update()
            self.drawing_area.calculate_coverage()
    
    def update_camera_sensitivity(self):
        if self.current_camera:
            value = self.sensitivity_slider.value()
            self.current_camera.sensitivity = value
            self.sensitivity_label.setText(f"{value}%")
            self.drawing_area.update()
    
    def update_camera_name(self):
        if self.current_camera:
            self.current_camera.name = self.camera_name_edit.text()
            self.update_camera_list()
            self.drawing_area.update()
    
    def choose_camera_color(self):
        if self.current_camera:
            color = QColorDialog.getColor(self.current_camera.color, self, "Выберите цвет камеры")
            if color.isValid():
                self.current_camera.color = color
                self.drawing_area.update()
    
    def toggle_camera_enabled(self):
        if self.current_camera:
            self.current_camera.enabled = self.enable_check.isChecked()
            self.update_camera_list()
            self.drawing_area.update()
            self.update_statistics()
    
    def toggle_camera_recording(self):
        if self.current_camera:
            self.current_camera.recording = self.recording_check.isChecked()
            self.drawing_area.update()
    
    def remove_camera(self):
        if self.current_camera:
            self.drawing_area.cameras.remove(self.current_camera)
            self.current_camera = None
            self.update_camera_list()
            self.drawing_area.update()
            self.update_statistics()
            self.statusBar().showMessage("Камера удалена")
    
    def clear_cameras(self):
        if self.drawing_area.cameras:
            reply = QMessageBox.question(self, "Подтверждение", 
                                        "Удалить все камеры?",
                                        QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.drawing_area.cameras.clear()
                self.current_camera = None
                self.update_camera_list()
                self.drawing_area.update()
                self.update_statistics()
                self.statusBar().showMessage("Все камеры удалены")
    
    def update_statistics(self):
        """Обновление статистики"""
        total = len(self.drawing_area.cameras)
        active = sum(1 for c in self.drawing_area.cameras if c.enabled)
        
        self.total_cameras_label.setText(f"Всего камер: {total}")
        self.active_cameras_label.setText(f"Активных камер: {active}")
        
        coverage = self.drawing_area.calculate_coverage()
        self.coverage_label.setText(f"Покрытие площади: {coverage:.1f}%")
        self.coverage_bar.setValue(int(coverage))
        
        # Детальная статистика
        stats_text = "📊 Детальная информация:\n\n"
        for i, camera in enumerate(self.drawing_area.cameras, 1):
            stats_text += f"{i}. {camera.name}\n"
            stats_text += f"   📍 Позиция: ({int(camera.x)}, {int(camera.y)})\n"
            stats_text += f"   🎯 Направление: {camera.angle}°\n"
            stats_text += f"   👁 Угол обзора: {camera.view_angle}°\n"
            stats_text += f"   📏 Дальность: {camera.range}px\n"
            stats_text += f"   ⚡ Чувствительность: {camera.sensitivity}%\n"
            stats_text += f"   📐 Площадь покрытия: {camera.get_coverage_area():.0f} px²\n"
            stats_text += f"   {'🟢 Активна' if camera.enabled else '🔴 Отключена'}\n"
            stats_text += f"   {'🔴 Запись' if camera.recording else '⏹ Запись выкл'}\n\n"
        
        self.stats_text.setText(stats_text)
    
    def update_coverage_display(self, coverage):
        """Обновление отображения покрытия"""
        self.coverage_label.setText(f"Покрытие площади: {coverage:.1f}%")
        self.coverage_bar.setValue(int(coverage))
    
    def reset_view(self):
        """Сброс масштаба и позиции"""
        self.drawing_area.scale_factor = 1.0
        self.drawing_area.pan_x = 0
        self.drawing_area.pan_y = 0
        self.drawing_area.update()
        self.statusBar().showMessage("Вид сброшен")
    
    def export_as_image(self):
        """Экспорт текущего вида в изображение"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить изображение", f"plan_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            "PNG (*.png);;JPEG (*.jpg);;BMP (*.bmp)"
        )
        if filename:
            if self.drawing_area.export_to_image(filename):
                QMessageBox.information(self, "Успех", f"Изображение сохранено:\n{filename}")
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось сохранить изображение")
    
    def save_json_config(self):
        """Сохранение конфигурации в JSON"""
        if not self.drawing_area.cameras:
            QMessageBox.information(self, "Информация", "Нет камер для сохранения")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить конфигурацию", f"cameras_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON файлы (*.json)"
        )
        if filename:
            config = {
                'version': '2.0',
                'date': datetime.now().isoformat(),
                'cameras': [
                    {
                        'name': c.name,
                        'x': c.x,
                        'y': c.y,
                        'angle': c.angle,
                        'view_angle': c.view_angle,
                        'range': c.range,
                        'sensitivity': c.sensitivity,
                        'color': [c.color.red(), c.color.green(), c.color.blue()],
                        'enabled': c.enabled
                    }
                    for c in self.drawing_area.cameras
                ]
            }
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                QMessageBox.information(self, "Успех", f"Конфигурация сохранена:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить: {str(e)}")
    
    def load_json_config(self):
        """Загрузка конфигурации из JSON"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Загрузить конфигурацию", "", "JSON файлы (*.json)"
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.drawing_area.cameras = []
                for cam_data in config['cameras']:
                    camera = Camera(
                        cam_data['x'], cam_data['y'],
                        cam_data['angle'], cam_data['view_angle'],
                        cam_data['range'],
                        cam_data.get('sensitivity', 50),
                        cam_data.get('name', '')
                    )
                    if 'color' in cam_data:
                        camera.color = QColor(*cam_data['color'])
                    camera.enabled = cam_data.get('enabled', True)
                    self.drawing_area.cameras.append(camera)
                
                self.update_camera_list()
                self.drawing_area.update()
                self.update_statistics()
                QMessageBox.information(self, "Успех", f"Загружено {len(self.drawing_area.cameras)} камер")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить: {str(e)}")
    
    def export_to_csv(self):
        """Экспорт в CSV"""
        if not self.drawing_area.cameras:
            QMessageBox.information(self, "Информация", "Нет данных для экспорта")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Экспорт в CSV", f"cameras_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV файлы (*.csv)"
        )
        if filename:
            try:
                with open(filename, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Имя', 'X', 'Y', 'Направление', 'Угол обзора', 
                                   'Дальность', 'Чувствительность', 'Активна'])
                    for camera in self.drawing_area.cameras:
                        writer.writerow([
                            camera.name, int(camera.x), int(camera.y),
                            camera.angle, camera.view_angle, camera.range,
                            camera.sensitivity, camera.enabled
                        ])
                QMessageBox.information(self, "Успех", f"Данные экспортированы:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка экспорта: {str(e)}")
    
    def import_from_csv(self):
        """Импорт из CSV"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Импорт из CSV", "", "CSV файлы (*.csv)"
        )
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        camera = Camera(
                            float(row['X']), float(row['Y']),
                            float(row['Направление']),
                            float(row['Угол обзора']),
                            float(row['Дальность']),
                            int(row.get('Чувствительность', 50)),
                            row['Имя']
                        )
                        camera.enabled = row.get('Активна', 'True') == 'True'
                        self.drawing_area.cameras.append(camera)
                
                self.update_camera_list()
                self.drawing_area.update()
                self.update_statistics()
                QMessageBox.information(self, "Успех", f"Импортировано {len(self.drawing_area.cameras)} камер")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка импорта: {str(e)}")
    
    def generate_report(self):
        """Генерация отчета"""
        if not self.drawing_area.cameras:
            QMessageBox.information(self, "Информация", "Нет камер для генерации отчета")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить отчет", f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Текстовые файлы (*.txt)"
        )
        if filename:
            try:
                coverage = self.drawing_area.calculate_coverage()
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("=" * 60 + "\n")
                    f.write("ОТЧЕТ ПО СИСТЕМЕ ВИДЕОНАБЛЮДЕНИЯ\n")
                    f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 60 + "\n\n")
                    
                    f.write("ОБЩАЯ СТАТИСТИКА:\n")
                    f.write(f"Всего камер: {len(self.drawing_area.cameras)}\n")
                    f.write(f"Активных камер: {sum(1 for c in self.drawing_area.cameras if c.enabled)}\n")
                    f.write(f"Покрытие площади: {coverage:.1f}%\n\n")
                    
                    f.write("ДЕТАЛЬНАЯ ИНФОРМАЦИЯ ПО КАМЕРАМ:\n")
                    f.write("-" * 60 + "\n")
                    for i, camera in enumerate(self.drawing_area.cameras, 1):
                        f.write(f"\n{i}. {camera.name}\n")
                        f.write(f"   Позиция: ({int(camera.x)}, {int(camera.y)})\n")
                        f.write(f"   Направление: {camera.angle}°\n")
                        f.write(f"   Угол обзора: {camera.view_angle}°\n")
                        f.write(f"   Дальность: {camera.range} пикселей\n")
                        f.write(f"   Чувствительность: {camera.sensitivity}%\n")
                        f.write(f"   Площадь покрытия: {camera.get_coverage_area():.0f} px²\n")
                        f.write(f"   Статус: {'Активна' if camera.enabled else 'Отключена'}\n")
                        if camera.recording:
                            f.write(f"   Запись: Включена\n")
                    
                    f.write("\n" + "=" * 60 + "\n")
                    f.write("КОНЕЦ ОТЧЕТА\n")
                
                QMessageBox.information(self, "Успех", f"Отчет сохранен:\n{filename}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Ошибка создания отчета: {str(e)}")
    
    def show_about(self):
        """О программе"""
        QMessageBox.about(self, "О программе",
                         "📷 Расширенный планировщик камер наблюдения\n\n"
                         "Версия 2.0\n\n"
                         "Возможности:\n"
                         "• Визуальное планирование камер\n"
                         "• Расчет покрытия территории\n"
                         "• Экспорт в различные форматы\n"
                         "• Статистика и отчеты\n"
                         "• Интерактивное управление\n\n"
                         "Управление:\n"
                         "• Левая кнопка - выбор/перемещение камер\n"
                         "• Средняя кнопка - панорамирование\n"
                         "• Колесико - масштабирование\n\n"
                         "© 2024")

def main():
    try:
        app = QApplication(sys.argv)
        app.setStyle('Fusion')
        
        # Устанавливаем иконку приложения (опционально)
        app.setApplicationName("Camera Planner Pro")
        
        window = ExtendedCameraPlanner()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        traceback.print_exc()
        input("Нажмите Enter для выхода...")

if __name__ == '__main__':
    main()