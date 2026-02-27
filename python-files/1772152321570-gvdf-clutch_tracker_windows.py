#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Clutch Tracker для Windows
# Версия: 8.0 Windows Edition

import sys
import os
import json
import shutil
from datetime import datetime, date, timedelta
from collections import defaultdict
import subprocess

# Определяем пути для Windows
if getattr(sys, 'frozen', False):
    # Запуск из exe - данные в папке с программой
    BASE_DIR = os.path.dirname(sys.executable)
    DATA_DIR = os.path.join(BASE_DIR, 'data')
else:
    # Запуск из скрипта - данные в папке с программой
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, 'data')

CONFIG_DIR = os.path.join(DATA_DIR, 'config')
DOCS_DIR = os.path.join(DATA_DIR, 'documents')
DATA_FILE = os.path.join(CONFIG_DIR, 'cars.json')
ORGS_FILE = os.path.join(CONFIG_DIR, 'organizations.json')
FUEL_FILE = os.path.join(CONFIG_DIR, 'fuel.json')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'settings.json')

# Создаем директории
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

# Импортируем PyQt5
try:
    from PyQt5.QtWidgets import *
    from PyQt5.QtCore import *
    from PyQt5.QtGui import *
    from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
except ImportError:
    print("Ошибка: PyQt5 не установлен!")
    print("Установите: pip install PyQt5")
    input("Нажмите Enter для выхода...")
    sys.exit(1)

# Импортируем matplotlib для графиков
try:
    import matplotlib
    matplotlib.use('Qt5Agg')
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

# Для Windows уведомлений
try:
    from plyer import notification
    NOTIFICATIONS_AVAILABLE = True
except ImportError:
    NOTIFICATIONS_AVAILABLE = False

# Загружаем настройки
settings = {}
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except:
        settings = {}

DATA_DIR = settings.get('data_dir', DATA_DIR)
CONFIG_DIR = settings.get('config_dir', os.path.join(DATA_DIR, 'config'))
DOCS_DIR = settings.get('docs_dir', os.path.join(DATA_DIR, 'documents'))
DATA_FILE = os.path.join(CONFIG_DIR, "cars.json")
ORGS_FILE = os.path.join(CONFIG_DIR, "organizations.json")
FUEL_FILE = os.path.join(CONFIG_DIR, "fuel.json")

# Создаем директории снова
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)


# ============= КЛАССЫ ДАННЫХ =============
class MonthlyFuelRecord:
    def __init__(self, car_plate, year, month, liters, distance, notes=""):
        self.car_plate = car_plate
        self.year = year
        self.month = month
        self.liters = liters
        self.distance = distance
        self.notes = notes
    
    @property
    def consumption(self):
        if self.distance > 0:
            return (self.liters / self.distance) * 100
        return 0
    
    @property
    def period(self):
        return f"{self.year}-{self.month:02d}"
    
    def to_dict(self):
        return {
            'car_plate': self.car_plate,
            'year': self.year,
            'month': self.month,
            'liters': self.liters,
            'distance': self.distance,
            'notes': self.notes
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            data['car_plate'],
            data['year'],
            data['month'],
            data['liters'],
            data['distance'],
            data.get('notes', '')
        )


class FuelManager:
    def __init__(self):
        self.records = []
        self.norm_consumption = {}
        self.load()
    
    def load(self):
        if os.path.exists(FUEL_FILE):
            try:
                with open(FUEL_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.records = [MonthlyFuelRecord.from_dict(r) for r in data.get('records', [])]
                    self.norm_consumption = data.get('norm_consumption', {})
            except:
                self.records = []
                self.norm_consumption = {}
    
    def save(self):
        try:
            data = {
                'records': [r.to_dict() for r in self.records],
                'norm_consumption': self.norm_consumption
            }
            with open(FUEL_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def add_record(self, record):
        for i, r in enumerate(self.records):
            if r.car_plate == record.car_plate and r.year == record.year and r.month == record.month:
                self.records[i] = record
                self.save()
                return
        
        self.records.append(record)
        self.records.sort(key=lambda x: (x.car_plate, x.year, x.month))
        self.save()
    
    def delete_record(self, record):
        self.records = [r for r in self.records if not (r.car_plate == record.car_plate and 
                                                         r.year == record.year and 
                                                         r.month == record.month)]
        self.save()
    
    def get_records_for_car(self, plate):
        return [r for r in self.records if r.car_plate == plate]
    
    def set_norm(self, plate, liters_per_100km):
        self.norm_consumption[plate] = liters_per_100km
        self.save()
    
    def get_norm(self, plate):
        return self.norm_consumption.get(plate, 0)
    
    def get_average_consumption(self, plate, months=3):
        records = self.get_records_for_car(plate)
        if len(records) < 1:
            return 0
        
        records.sort(key=lambda x: (x.year, x.month), reverse=True)
        recent = records[:months]
        
        total_liters = sum(r.liters for r in recent)
        total_distance = sum(r.distance for r in recent)
        
        if total_distance == 0:
            return 0
        
        return (total_liters / total_distance) * 100
    
    def get_stats(self, plate):
        records = self.get_records_for_car(plate)
        if not records:
            return {'total_liters': 0, 'total_distance': 0, 'avg_consumption': 0, 'norm': 0}
        
        total_liters = sum(r.liters for r in records)
        total_distance = sum(r.distance for r in records)
        avg_consumption = (total_liters / total_distance * 100) if total_distance > 0 else 0
        norm = self.get_norm(plate)
        
        return {
            'total_liters': total_liters,
            'total_distance': total_distance,
            'avg_consumption': avg_consumption,
            'norm': norm,
            'deviation': avg_consumption - norm if norm > 0 else 0
        }


class DocumentClickableLabel(QLabel):
    clicked = pyqtSignal(str)
    
    def __init__(self, text, file_paths=None, parent=None):
        super().__init__(text, parent)
        self.file_paths = file_paths or []
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Нажмите для просмотра документов")
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.file_paths:
                self.show_documents_list()
            else:
                self.clicked.emit("")
    
    def show_documents_list(self):
        if not self.file_paths:
            QMessageBox.information(self, "Информация", "Нет прикрепленных документов")
            return
        
        items = []
        file_map = {}
        
        for file_path in self.file_paths:
            if os.path.exists(file_path):
                filename = os.path.basename(file_path)
                size = os.path.getsize(file_path)
                size_str = self.format_size(size)
                items.append(f"{filename} ({size_str})")
                file_map[f"{filename} ({size_str})"] = file_path
        
        if not items:
            QMessageBox.information(self, "Информация", "Файлы не найдены")
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Выберите документ")
        dialog.setModal(True)
        dialog.resize(500, 300)
        
        layout = QVBoxLayout()
        
        list_widget = QListWidget()
        list_widget.addItems(items)
        list_widget.setSelectionMode(QListWidget.SingleSelection)
        layout.addWidget(list_widget)
        
        btn_layout = QHBoxLayout()
        
        open_btn = QPushButton("Открыть")
        open_btn.clicked.connect(lambda: self.open_selected(list_widget, file_map, dialog))
        btn_layout.addWidget(open_btn)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def open_selected(self, list_widget, file_map, dialog):
        current = list_widget.currentItem()
        if current:
            file_path = file_map.get(current.text())
            if file_path and os.path.exists(file_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
                dialog.accept()
    
    def format_size(self, size):
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} ТБ"


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle("Настройки программы")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        storage_group = QGroupBox("Хранение данных")
        storage_layout = QFormLayout()
        
        self.data_dir_edit = QLineEdit()
        self.data_dir_edit.setText(DATA_DIR)
        self.data_dir_edit.setReadOnly(True)
        
        data_dir_btn = QPushButton("Обзор...")
        data_dir_btn.clicked.connect(lambda: self.browse_folder(self.data_dir_edit))
        
        data_dir_layout = QHBoxLayout()
        data_dir_layout.addWidget(self.data_dir_edit)
        data_dir_layout.addWidget(data_dir_btn)
        storage_layout.addRow("Директория данных:", data_dir_layout)
        
        self.docs_dir_edit = QLineEdit()
        self.docs_dir_edit.setText(DOCS_DIR)
        self.docs_dir_edit.setReadOnly(True)
        
        docs_dir_btn = QPushButton("Обзор...")
        docs_dir_btn.clicked.connect(lambda: self.browse_folder(self.docs_dir_edit))
        
        docs_dir_layout = QHBoxLayout()
        docs_dir_layout.addWidget(self.docs_dir_edit)
        docs_dir_layout.addWidget(docs_dir_btn)
        storage_layout.addRow("Директория документов:", docs_dir_layout)
        
        storage_group.setLayout(storage_layout)
        layout.addWidget(storage_group)
        
        info_group = QGroupBox("Информация")
        info_layout = QFormLayout()
        
        total_size = self.get_folder_size(DOCS_DIR)
        info_layout.addRow("Размер документов:", QLabel(self.format_size(total_size)))
        
        doc_count = self.count_documents()
        info_layout.addRow("Количество документов:", QLabel(str(doc_count)))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        btn_layout = QHBoxLayout()
        
        reset_btn = QPushButton("Сбросить")
        reset_btn.clicked.connect(self.reset_settings)
        btn_layout.addWidget(reset_btn)
        
        btn_layout.addStretch()
        
        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save_settings)
        save_btn.setDefault(True)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def browse_folder(self, line_edit):
        folder = QFileDialog.getExistingDirectory(
            self, "Выберите папку", line_edit.text()
        )
        if folder:
            line_edit.setText(folder)
    
    def get_folder_size(self, folder):
        total = 0
        if os.path.exists(folder):
            for root, dirs, files in os.walk(folder):
                for f in files:
                    fp = os.path.join(root, f)
                    if os.path.exists(fp):
                        total += os.path.getsize(fp)
        return total
    
    def format_size(self, size):
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} ТБ"
    
    def count_documents(self):
        count = 0
        if os.path.exists(DOCS_DIR):
            for root, dirs, files in os.walk(DOCS_DIR):
                count += len(files)
        return count
    
    def reset_settings(self):
        self.data_dir_edit.setText(os.path.join(BASE_DIR, 'data'))
        self.docs_dir_edit.setText(os.path.join(BASE_DIR, 'data', 'documents'))
    
    def save_settings(self):
        new_data_dir = self.data_dir_edit.text()
        new_docs_dir = self.docs_dir_edit.text()
        
        os.makedirs(new_data_dir, exist_ok=True)
        os.makedirs(new_docs_dir, exist_ok=True)
        
        if new_docs_dir != DOCS_DIR and os.path.exists(DOCS_DIR):
            reply = QMessageBox.question(
                self, "Перемещение файлов",
                "Копировать существующие документы в новую папку?\n"
                "Файлы будут скопированы, оригиналы останутся на старом месте.",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    for item in os.listdir(DOCS_DIR):
                        src = os.path.join(DOCS_DIR, item)
                        dst = os.path.join(new_docs_dir, item)
                        if os.path.isfile(src):
                            shutil.copy2(src, dst)
                except Exception as e:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось копировать файлы:\n{str(e)}")
        
        settings = {
            'data_dir': new_data_dir,
            'config_dir': CONFIG_DIR,
            'docs_dir': new_docs_dir
        }
        
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
            
            QMessageBox.information(
                self, "Успех",
                "Настройки сохранены. Перезапустите программу для применения изменений."
            )
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить настройки:\n{str(e)}")


class Organizations:
    def __init__(self):
        self.orgs = []
        self.org_types = {}
        self.load()
    
    def load(self):
        if os.path.exists(ORGS_FILE):
            try:
                with open(ORGS_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.orgs = data
                        self.org_types = {}
                    else:
                        self.orgs = data.get('orgs', [])
                        self.org_types = data.get('org_types', {})
            except:
                self.orgs = []
                self.org_types = {}
    
    def save(self):
        try:
            data = {
                'orgs': self.orgs,
                'org_types': self.org_types
            }
            with open(ORGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except:
            pass
    
    def add(self, name, org_type='all'):
        if name and name not in self.orgs:
            self.orgs.append(name)
            self.org_types[name] = org_type
            self.save()
            return True
        elif name in self.orgs:
            self.org_types[name] = org_type
            self.save()
            return True
        return False
    
    def remove(self, name):
        if name in self.orgs:
            self.orgs.remove(name)
            if name in self.org_types:
                del self.org_types[name]
            self.save()
            return True
        return False
    
    def get_list(self, org_type=None):
        if org_type:
            return sorted([o for o in self.orgs if self.org_types.get(o, 'all') == org_type or self.org_types.get(o, 'all') == 'all'])
        return sorted(self.orgs)
    
    def get_type(self, name):
        return self.org_types.get(name, 'all')


class OrganizationManagerDialog(QDialog):
    def __init__(self, org_manager, parent=None):
        super().__init__(parent)
        self.org_manager = org_manager
        self.setWindowTitle("Управление организациями")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        layout = QVBoxLayout()
        
        top_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Добавить")
        self.add_btn.clicked.connect(self.add_organization)
        top_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("✏️ Редактировать")
        self.edit_btn.clicked.connect(self.edit_organization)
        top_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("❌ Удалить")
        self.delete_btn.clicked.connect(self.delete_organization)
        top_layout.addWidget(self.delete_btn)
        
        top_layout.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск...")
        self.search_input.textChanged.connect(self.filter_table)
        top_layout.addWidget(self.search_input)
        
        layout.addLayout(top_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Организация", "Тип", "Используется в"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.table)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        self.load_table()
    
    def load_table(self):
        self.table.setRowCount(0)
        
        type_names = {
            'insurance': 'Страхование',
            'service': 'ТО/Ремонт',
            'diagnostic': 'Диагностика',
            'tachograph': 'Тахограф',
            'all': 'Универсальная'
        }
        
        for org in sorted(self.org_manager.orgs):
            row = self.table.rowCount()
            self.table.insertRow(row)
            
            org_item = QTableWidgetItem(org)
            org_item.setFlags(org_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, org_item)
            
            org_type = self.org_manager.get_type(org)
            type_item = QTableWidgetItem(type_names.get(org_type, org_type))
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, type_item)
            
            usage_item = QTableWidgetItem("")
            usage_item.setFlags(usage_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, usage_item)
    
    def filter_table(self):
        search_text = self.search_input.text().lower()
        
        for row in range(self.table.rowCount()):
            org_item = self.table.item(row, 0)
            if org_item:
                match = search_text in org_item.text().lower()
                self.table.setRowHidden(row, not match)
    
    def add_organization(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Добавить организацию")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        name = QLineEdit()
        name.setPlaceholderText("Название организации")
        form.addRow("Название:", name)
        
        type_combo = QComboBox()
        type_combo.addItem("Универсальная", 'all')
        type_combo.addItem("Страхование", 'insurance')
        type_combo.addItem("ТО/Ремонт", 'service')
        type_combo.addItem("Диагностика", 'diagnostic')
        type_combo.addItem("Тахограф", 'tachograph')
        form.addRow("Тип:", type_combo)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            org_name = name.text().strip()
            if org_name:
                org_type = type_combo.currentData()
                if self.org_manager.add(org_name, org_type):
                    self.load_table()
                    QMessageBox.information(self, "Успех", f"Организация {org_name} добавлена!")
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось добавить организацию!")
    
    def edit_organization(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите организацию!")
            return
        
        old_name = self.table.item(row, 0).text()
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Редактировать {old_name}")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        name = QLineEdit()
        name.setText(old_name)
        form.addRow("Название:", name)
        
        type_combo = QComboBox()
        type_combo.addItem("Универсальная", 'all')
        type_combo.addItem("Страхование", 'insurance')
        type_combo.addItem("ТО/Ремонт", 'service')
        type_combo.addItem("Диагностика", 'diagnostic')
        type_combo.addItem("Тахограф", 'tachograph')
        
        current_type = self.org_manager.get_type(old_name)
        index = type_combo.findData(current_type)
        if index >= 0:
            type_combo.setCurrentIndex(index)
        
        form.addRow("Тип:", type_combo)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            new_name = name.text().strip()
            if new_name and new_name != old_name:
                self.org_manager.remove(old_name)
                self.org_manager.add(new_name, type_combo.currentData())
            elif new_name:
                self.org_manager.add(old_name, type_combo.currentData())
            
            self.load_table()
            QMessageBox.information(self, "Успех", "Организация обновлена!")
    
    def delete_organization(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Ошибка", "Выберите организацию!")
            return
        
        name = self.table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить организацию {name}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.org_manager.remove(name):
                self.load_table()
                QMessageBox.information(self, "Успех", "Организация удалена!")


class Document:
    def __init__(self, file_path, description=""):
        self.file_path = file_path
        self.description = description
        self.added_date = date.today().isoformat()
    
    def to_dict(self):
        return {
            'file_path': self.file_path,
            'description': self.description,
            'added_date': self.added_date
        }
    
    @classmethod
    def from_dict(cls, data):
        doc = cls(data['file_path'], data['description'])
        doc.added_date = data['added_date']
        return doc


class VehicleInfo:
    def __init__(self, plate, brand="", model="", year=0, vin="", vehicle_type="passenger",
                 cargo_length=0, cargo_width=0, cargo_height=0, cargo_capacity=0):
        self.plate = plate
        self.brand = brand
        self.model = model
        self.year = year
        self.vin = vin
        self.vehicle_type = vehicle_type
        self.cargo_length = cargo_length
        self.cargo_width = cargo_width
        self.cargo_height = cargo_height
        self.cargo_capacity = cargo_capacity
    
    def get_cargo_volume(self):
        if self.vehicle_type == 'cargo' and self.cargo_length and self.cargo_width and self.cargo_height:
            return (self.cargo_length * self.cargo_width * self.cargo_height) / 1000000
        return 0
    
    def to_dict(self):
        return {
            'plate': self.plate,
            'brand': self.brand,
            'model': self.model,
            'year': self.year,
            'vin': self.vin,
            'vehicle_type': self.vehicle_type,
            'cargo_length': self.cargo_length,
            'cargo_width': self.cargo_width,
            'cargo_height': self.cargo_height,
            'cargo_capacity': self.cargo_capacity
        }
    
    @classmethod
    def from_dict(cls, data):
        return cls(
            data['plate'],
            data.get('brand', ''),
            data.get('model', ''),
            data.get('year', 0),
            data.get('vin', ''),
            data.get('vehicle_type', 'passenger'),
            data.get('cargo_length', 0),
            data.get('cargo_width', 0),
            data.get('cargo_height', 0),
            data.get('cargo_capacity', 0)
        )


class ServiceItem:
    def __init__(self, car_plate, service_type, last_mileage, interval, last_date=None, org_name=""):
        self.car_plate = car_plate
        self.service_type = service_type
        self.last_mileage = last_mileage
        self.interval = interval
        self.last_date = last_date or date.today().isoformat()
        self.current_mileage = last_mileage
        self.org_name = org_name
        self.notified = False
        self.documents = []
        self.history = []
    
    def update_mileage(self, new_mileage):
        self.current_mileage = new_mileage
        self.notified = False
    
    def service_done(self, mileage, service_date=None, notes="", org_name=""):
        self.history.append({
            'date': service_date or date.today().isoformat(),
            'mileage': mileage,
            'notes': notes,
            'org': org_name
        })
        self.last_mileage = mileage
        self.current_mileage = mileage
        self.last_date = service_date or date.today().isoformat()
        self.org_name = org_name
        self.notified = False
    
    def remaining(self):
        return self.interval - (self.current_mileage - self.last_mileage)
    
    def add_document(self, file_path, description=""):
        filename = os.path.basename(file_path)
        dest_path = os.path.join(DOCS_DIR, f"{self.car_plate}_{self.service_type}_{filename}")
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(filename)
            dest_path = os.path.join(DOCS_DIR, f"{self.car_plate}_{self.service_type}_{base}_{int(datetime.now().timestamp())}{ext}")
        shutil.copy2(file_path, dest_path)
        self.documents.append(Document(dest_path, description))
    
    def to_dict(self):
        return {
            'car_plate': self.car_plate,
            'service_type': self.service_type,
            'last_mileage': self.last_mileage,
            'interval': self.interval,
            'last_date': self.last_date,
            'current_mileage': self.current_mileage,
            'org_name': self.org_name,
            'history': self.history,
            'documents': [d.to_dict() for d in self.documents]
        }
    
    @classmethod
    def from_dict(cls, data):
        item = cls(
            data['car_plate'],
            data['service_type'],
            data['last_mileage'],
            data['interval'],
            data.get('last_date'),
            data.get('org_name', '')
        )
        item.current_mileage = data['current_mileage']
        item.history = data.get('history', [])
        if 'documents' in data:
            item.documents = [Document.from_dict(d) for d in data['documents']]
        return item


class InsuranceItem:
    def __init__(self, car_plate, company_name, policy_number, start_date, end_date, cost):
        self.car_plate = car_plate
        self.company_name = company_name
        self.policy_number = policy_number
        self.start_date = start_date
        self.end_date = end_date
        self.cost = cost
        self.notified = False
        self.documents = []
        self.history = []
    
    def days_until_expiry(self):
        today = date.today()
        end = date.fromisoformat(self.end_date)
        return (end - today).days
    
    def add_document(self, file_path, description=""):
        filename = os.path.basename(file_path)
        dest_path = os.path.join(DOCS_DIR, f"{self.car_plate}_insurance_{filename}")
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(filename)
            dest_path = os.path.join(DOCS_DIR, f"{self.car_plate}_insurance_{base}_{int(datetime.now().timestamp())}{ext}")
        shutil.copy2(file_path, dest_path)
        self.documents.append(Document(dest_path, description))
    
    def to_dict(self):
        return {
            'car_plate': self.car_plate,
            'company_name': self.company_name,
            'policy_number': self.policy_number,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'cost': self.cost,
            'history': self.history,
            'documents': [d.to_dict() for d in self.documents]
        }
    
    @classmethod
    def from_dict(cls, data):
        item = cls(
            data['car_plate'],
            data['company_name'],
            data['policy_number'],
            data['start_date'],
            data['end_date'],
            data['cost']
        )
        item.history = data.get('history', [])
        if 'documents' in data:
            item.documents = [Document.from_dict(d) for d in data['documents']]
        return item


class DiagnosticCard:
    def __init__(self, car_plate, station_name, card_number, issue_date, expiry_date, cost):
        self.car_plate = car_plate
        self.station_name = station_name
        self.card_number = card_number
        self.issue_date = issue_date
        self.expiry_date = expiry_date
        self.cost = cost
        self.notified = False
        self.documents = []
        self.history = []
    
    def days_until_expiry(self):
        today = date.today()
        end = date.fromisoformat(self.expiry_date)
        return (end - today).days
    
    def add_document(self, file_path, description=""):
        filename = os.path.basename(file_path)
        dest_path = os.path.join(DOCS_DIR, f"{self.car_plate}_diagnostic_{filename}")
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(filename)
            dest_path = os.path.join(DOCS_DIR, f"{self.car_plate}_diagnostic_{base}_{int(datetime.now().timestamp())}{ext}")
        shutil.copy2(file_path, dest_path)
        self.documents.append(Document(dest_path, description))
    
    def to_dict(self):
        return {
            'car_plate': self.car_plate,
            'station_name': self.station_name,
            'card_number': self.card_number,
            'issue_date': self.issue_date,
            'expiry_date': self.expiry_date,
            'cost': self.cost,
            'history': self.history,
            'documents': [d.to_dict() for d in self.documents]
        }
    
    @classmethod
    def from_dict(cls, data):
        item = cls(
            data['car_plate'],
            data['station_name'],
            data['card_number'],
            data['issue_date'],
            data['expiry_date'],
            data['cost']
        )
        item.history = data.get('history', [])
        if 'documents' in data:
            item.documents = [Document.from_dict(d) for d in data['documents']]
        return item


class TachographItem:
    def __init__(self, car_plate, device_number, calibration_date, expiry_date, cost, company_name=""):
        self.car_plate = car_plate
        self.device_number = device_number
        self.calibration_date = calibration_date
        self.expiry_date = expiry_date
        self.cost = cost
        self.company_name = company_name
        self.notified = False
        self.documents = []
        self.history = []
    
    def days_until_expiry(self):
        today = date.today()
        end = date.fromisoformat(self.expiry_date)
        return (end - today).days
    
    def add_calibration(self, calibration_date, expiry_date, cost, company_name=""):
        self.history.append({
            'calibration_date': calibration_date,
            'expiry_date': expiry_date,
            'cost': cost,
            'company': company_name
        })
        self.calibration_date = calibration_date
        self.expiry_date = expiry_date
        self.cost = cost
        self.company_name = company_name
        self.notified = False
    
    def add_document(self, file_path, description=""):
        filename = os.path.basename(file_path)
        dest_path = os.path.join(DOCS_DIR, f"{self.car_plate}_tachograph_{filename}")
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(filename)
            dest_path = os.path.join(DOCS_DIR, f"{self.car_plate}_tachograph_{base}_{int(datetime.now().timestamp())}{ext}")
        shutil.copy2(file_path, dest_path)
        self.documents.append(Document(dest_path, description))
    
    def to_dict(self):
        return {
            'car_plate': self.car_plate,
            'device_number': self.device_number,
            'calibration_date': self.calibration_date,
            'expiry_date': self.expiry_date,
            'cost': self.cost,
            'company_name': self.company_name,
            'history': self.history,
            'documents': [d.to_dict() for d in self.documents]
        }
    
    @classmethod
    def from_dict(cls, data):
        item = cls(
            data['car_plate'],
            data['device_number'],
            data['calibration_date'],
            data['expiry_date'],
            data['cost'],
            data.get('company_name', '')
        )
        item.history = data.get('history', [])
        if 'documents' in data:
            item.documents = [Document.from_dict(d) for d in data['documents']]
        return item


class PermitItem:
    def __init__(self, car_plate, permit_number, start_date, end_date, cost, zone=""):
        self.car_plate = car_plate
        self.permit_type = "moscow"
        self.permit_number = permit_number
        self.start_date = start_date
        self.end_date = end_date
        self.cost = cost
        self.zone = zone
        self.notified = False
        self.documents = []
        self.history = []
    
    def days_until_expiry(self):
        today = date.today()
        end = date.fromisoformat(self.end_date)
        return (end - today).days
    
    def add_document(self, file_path, description=""):
        filename = os.path.basename(file_path)
        dest_path = os.path.join(DOCS_DIR, f"{self.car_plate}_permit_{filename}")
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(filename)
            dest_path = os.path.join(DOCS_DIR, f"{self.car_plate}_permit_{base}_{int(datetime.now().timestamp())}{ext}")
        shutil.copy2(file_path, dest_path)
        self.documents.append(Document(dest_path, description))
    
    def to_dict(self):
        return {
            'car_plate': self.car_plate,
            'permit_type': self.permit_type,
            'permit_number': self.permit_number,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'cost': self.cost,
            'zone': self.zone,
            'history': self.history,
            'documents': [d.to_dict() for d in self.documents]
        }
    
    @classmethod
    def from_dict(cls, data):
        item = cls(
            data['car_plate'],
            data['permit_number'],
            data['start_date'],
            data['end_date'],
            data.get('cost', 0),
            data.get('zone', '')
        )
        item.history = data.get('history', [])
        if 'documents' in data:
            item.documents = [Document.from_dict(d) for d in data['documents']]
        return item


class RepairItem:
    def __init__(self, car_plate, date_performed, mileage, description, cost, workshop=""):
        self.car_plate = car_plate
        self.date_performed = date_performed
        self.mileage = mileage
        self.description = description
        self.cost = cost
        self.workshop = workshop
        self.documents = []
    
    def add_document(self, file_path, description=""):
        filename = os.path.basename(file_path)
        dest_path = os.path.join(DOCS_DIR, f"{self.car_plate}_repair_{filename}")
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(filename)
            dest_path = os.path.join(DOCS_DIR, f"{self.car_plate}_repair_{base}_{int(datetime.now().timestamp())}{ext}")
        shutil.copy2(file_path, dest_path)
        self.documents.append(Document(dest_path, description))
    
    def to_dict(self):
        return {
            'car_plate': self.car_plate,
            'date_performed': self.date_performed,
            'mileage': self.mileage,
            'description': self.description,
            'cost': self.cost,
            'workshop': self.workshop,
            'documents': [d.to_dict() for d in self.documents]
        }
    
    @classmethod
    def from_dict(cls, data):
        item = cls(
            data['car_plate'],
            data['date_performed'],
            data['mileage'],
            data['description'],
            data['cost'],
            data.get('workshop', '')
        )
        if 'documents' in data:
            item.documents = [Document.from_dict(d) for d in data['documents']]
        return item


class Car:
    def __init__(self, plate):
        self.plate = plate
        self.vehicle_info = VehicleInfo(plate)
        self.services = []
        self.insurances = []
        self.diagnostic_cards = []
        self.repairs = []
        self.permits = []
        self.tachographs = []
    
    def set_vehicle_info(self, vehicle_info):
        self.vehicle_info = vehicle_info
    
    def add_service(self, service_item):
        self.services.append(service_item)
    
    def get_service(self, service_type):
        for service in self.services:
            if service.service_type == service_type:
                return service
        return None
    
    def add_insurance(self, insurance):
        self.insurances.append(insurance)
    
    def get_current_insurance(self):
        today = date.today()
        for ins in self.insurances:
            start = date.fromisoformat(ins.start_date)
            end = date.fromisoformat(ins.end_date)
            if start <= today <= end:
                return ins
        return None
    
    def get_insurance_days_left(self):
        ins = self.get_current_insurance()
        if ins:
            return ins.days_until_expiry()
        return None
    
    def add_diagnostic_card(self, card):
        self.diagnostic_cards.append(card)
    
    def get_current_diagnostic_card(self):
        today = date.today()
        for card in self.diagnostic_cards:
            issue = date.fromisoformat(card.issue_date)
            expiry = date.fromisoformat(card.expiry_date)
            if issue <= today <= expiry:
                return card
        return None
    
    def get_diagnostic_days_left(self):
        card = self.get_current_diagnostic_card()
        if card:
            return card.days_until_expiry()
        return None
    
    def add_permit(self, permit):
        self.permits.append(permit)
    
    def get_current_permits(self):
        today = date.today()
        current = []
        for permit in self.permits:
            start = date.fromisoformat(permit.start_date)
            end = date.fromisoformat(permit.end_date)
            if start <= today <= end:
                current.append(permit)
        return current
    
    def get_permit_days_left(self):
        permits = self.get_current_permits()
        if permits:
            return min(p.days_until_expiry() for p in permits)
        return None
    
    def add_tachograph(self, tachograph):
        self.tachographs.append(tachograph)
    
    def get_current_tachograph(self):
        today = date.today()
        for tach in self.tachographs:
            calib = date.fromisoformat(tach.calibration_date)
            expiry = date.fromisoformat(tach.expiry_date)
            if calib <= today <= expiry:
                return tach
        return None
    
    def get_tachograph_days_left(self):
        tach = self.get_current_tachograph()
        if tach:
            return tach.days_until_expiry()
        return None
    
    def add_repair(self, repair):
        self.repairs.append(repair)
    
    def get_current_mileage(self):
        mileage = 0
        for service in self.services:
            if service.current_mileage > mileage:
                mileage = service.current_mileage
        return mileage
    
    def get_all_documents_for_car(self):
        documents = []
        
        type_names = {
            'clutch': 'Сцепление',
            'maintenance': 'ТО',
            'brakes': 'Колодки'
        }
        
        tab_names = {
            'clutch': '🔧 Сцепление',
            'maintenance': '🔧 ТО',
            'brakes': '🔧 Колодки'
        }
        
        for service in self.services:
            org_name = service.org_name
            type_name = type_names.get(service.service_type, service.service_type)
            tab_name = tab_names.get(service.service_type, 'Обслуживание')
            
            for doc in service.documents:
                documents.append({
                    'type': service.service_type,
                    'type_name': type_name,
                    'org': org_name,
                    'tab': tab_name,
                    'file_path': doc.file_path,
                    'filename': os.path.basename(doc.file_path),
                    'description': doc.description,
                    'added_date': doc.added_date,
                    'size': os.path.getsize(doc.file_path) if os.path.exists(doc.file_path) else 0
                })
        
        for ins in self.insurances:
            for doc in ins.documents:
                documents.append({
                    'type': 'insurance',
                    'type_name': 'Страховка',
                    'org': ins.company_name,
                    'tab': '📄 Страховки',
                    'file_path': doc.file_path,
                    'filename': os.path.basename(doc.file_path),
                    'description': doc.description,
                    'added_date': doc.added_date,
                    'size': os.path.getsize(doc.file_path) if os.path.exists(doc.file_path) else 0
                })
        
        for card in self.diagnostic_cards:
            for doc in card.documents:
                documents.append({
                    'type': 'diagnostic',
                    'type_name': 'Диагностика',
                    'org': card.station_name,
                    'tab': '📋 Диагностика',
                    'file_path': doc.file_path,
                    'filename': os.path.basename(doc.file_path),
                    'description': doc.description,
                    'added_date': doc.added_date,
                    'size': os.path.getsize(doc.file_path) if os.path.exists(doc.file_path) else 0
                })
        
        for permit in self.permits:
            for doc in permit.documents:
                documents.append({
                    'type': 'permit',
                    'type_name': 'Пропуск',
                    'org': 'Мэрия Москвы',
                    'tab': '🎫 Пропуска',
                    'file_path': doc.file_path,
                    'filename': os.path.basename(doc.file_path),
                    'description': doc.description,
                    'added_date': doc.added_date,
                    'size': os.path.getsize(doc.file_path) if os.path.exists(doc.file_path) else 0
                })
        
        for tach in self.tachographs:
            for doc in tach.documents:
                documents.append({
                    'type': 'tachograph',
                    'type_name': 'Тахограф',
                    'org': tach.company_name,
                    'tab': '📊 Тахограф',
                    'file_path': doc.file_path,
                    'filename': os.path.basename(doc.file_path),
                    'description': doc.description,
                    'added_date': doc.added_date,
                    'size': os.path.getsize(doc.file_path) if os.path.exists(doc.file_path) else 0
                })
        
        for repair in self.repairs:
            for doc in repair.documents:
                documents.append({
                    'type': 'repair',
                    'type_name': 'Ремонт',
                    'org': repair.workshop,
                    'tab': '🔨 Ремонты',
                    'file_path': doc.file_path,
                    'filename': os.path.basename(doc.file_path),
                    'description': doc.description,
                    'added_date': doc.added_date,
                    'size': os.path.getsize(doc.file_path) if os.path.exists(doc.file_path) else 0
                })
        
        return documents
    
    def get_all_history(self):
        history = []
        
        for service in self.services:
            for event in service.history:
                history.append({
                    'date': event['date'],
                    'type': service.service_type,
                    'type_name': self.get_type_name(service.service_type),
                    'mileage': event['mileage'],
                    'description': event.get('notes', 'Замена'),
                    'cost': 0,
                    'org': event.get('org', service.org_name),
                    'days_left': None,
                    'expiry': None,
                    'tab': self.get_tab_name(service.service_type)
                })
        
        for repair in self.repairs:
            history.append({
                'date': repair.date_performed,
                'type': 'repair',
                'type_name': 'Ремонт',
                'mileage': repair.mileage,
                'description': repair.description,
                'cost': repair.cost,
                'workshop': repair.workshop,
                'org': repair.workshop,
                'days_left': None,
                'expiry': None,
                'tab': '🔨 Ремонты'
            })
        
        for ins in self.insurances:
            days = ins.days_until_expiry()
            history.append({
                'date': ins.start_date,
                'type': 'insurance',
                'type_name': 'Страховка',
                'description': f"Страховка {ins.company_name}",
                'cost': ins.cost,
                'end_date': ins.end_date,
                'org': ins.company_name,
                'days_left': days,
                'expiry': ins.end_date,
                'tab': '📄 Страховки'
            })
        
        for card in self.diagnostic_cards:
            days = card.days_until_expiry()
            history.append({
                'date': card.issue_date,
                'type': 'diagnostic',
                'type_name': 'Диагностика',
                'description': f"Диагностика {card.station_name}",
                'cost': card.cost,
                'end_date': card.expiry_date,
                'org': card.station_name,
                'days_left': days,
                'expiry': card.expiry_date,
                'tab': '📋 Диагностика'
            })
        
        for permit in self.permits:
            days = permit.days_until_expiry()
            history.append({
                'date': permit.start_date,
                'type': 'permit',
                'type_name': 'Пропуск',
                'description': f"Пропуск в Москву",
                'cost': permit.cost,
                'end_date': permit.end_date,
                'zone': permit.zone,
                'org': "Мэрия Москвы",
                'days_left': days,
                'expiry': permit.end_date,
                'tab': '🎫 Пропуска'
            })
        
        for tach in self.tachographs:
            days = tach.days_until_expiry()
            for event in tach.history:
                history.append({
                    'date': event['calibration_date'],
                    'type': 'tachograph',
                    'type_name': 'Тахограф',
                    'description': f"Калибровка тахографа",
                    'cost': event['cost'],
                    'end_date': event['expiry_date'],
                    'org': event.get('company', tach.company_name),
                    'days_left': days,
                    'expiry': event['expiry_date'],
                    'device': tach.device_number,
                    'tab': '📊 Тахограф'
                })
        
        history.sort(key=lambda x: x['date'], reverse=True)
        return history
    
    def get_type_name(self, service_type):
        names = {
            'clutch': 'Сцепление',
            'maintenance': 'ТО',
            'brakes': 'Колодки'
        }
        return names.get(service_type, service_type)
    
    def get_tab_name(self, service_type):
        tabs = {
            'clutch': '🔧 Сцепление',
            'maintenance': '🔧 ТО',
            'brakes': '🔧 Колодки'
        }
        return tabs.get(service_type, 'Обслуживание')
    
    def to_dict(self):
        return {
            'plate': self.plate,
            'vehicle_info': self.vehicle_info.to_dict(),
            'services': [s.to_dict() for s in self.services],
            'insurances': [i.to_dict() for i in self.insurances],
            'diagnostic_cards': [c.to_dict() for c in self.diagnostic_cards],
            'repairs': [r.to_dict() for r in self.repairs],
            'permits': [p.to_dict() for p in self.permits],
            'tachographs': [t.to_dict() for t in self.tachographs]
        }
    
    @classmethod
    def from_dict(cls, data):
        car = cls(data['plate'])
        if 'vehicle_info' in data:
            car.vehicle_info = VehicleInfo.from_dict(data['vehicle_info'])
        if 'services' in data:
            for s_data in data['services']:
                car.services.append(ServiceItem.from_dict(s_data))
        if 'insurances' in data:
            for i_data in data['insurances']:
                car.insurances.append(InsuranceItem.from_dict(i_data))
        if 'diagnostic_cards' in data:
            for c_data in data['diagnostic_cards']:
                car.diagnostic_cards.append(DiagnosticCard.from_dict(c_data))
        if 'repairs' in data:
            for r_data in data['repairs']:
                car.repairs.append(RepairItem.from_dict(r_data))
        if 'permits' in data:
            for p_data in data['permits']:
                car.permits.append(PermitItem.from_dict(p_data))
        if 'tachographs' in data:
            for t_data in data['tachographs']:
                car.tachographs.append(TachographItem.from_dict(t_data))
        return car


class DateEdit(QDateEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCalendarPopup(True)
        self.setDateRange(QDate(2000, 1, 1), QDate(2050, 12, 31))
        self.setDisplayFormat("yyyy-MM-dd")


class MonthYearEdit(QWidget):
    month_changed = pyqtSignal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.month_combo = QComboBox()
        months = [
            "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ]
        for i, month in enumerate(months, 1):
            self.month_combo.addItem(month, i)
        self.month_combo.currentIndexChanged.connect(self.month_changed)
        layout.addWidget(self.month_combo)
        
        self.year_spin = QSpinBox()
        self.year_spin.setRange(2000, 2050)
        self.year_spin.setValue(date.today().year)
        self.year_spin.valueChanged.connect(self.month_changed)
        layout.addWidget(self.year_spin)
        
        self.setLayout(layout)
    
    def get_year(self):
        return self.year_spin.value()
    
    def get_month(self):
        return self.month_combo.currentData()
    
    def set_date(self, year, month):
        self.year_spin.setValue(year)
        index = self.month_combo.findData(month)
        if index >= 0:
            self.month_combo.setCurrentIndex(index)
    
    def current_text(self):
        return f"{self.year_spin.value()}-{self.month_combo.currentData():02d}"


class OrganizationComboBox(QComboBox):
    def __init__(self, org_manager, org_type=None, parent=None):
        super().__init__(parent)
        self.org_manager = org_manager
        self.org_type = org_type
        self.setEditable(True)
        self.setInsertPolicy(QComboBox.InsertAtTop)
        self.update_list()
    
    def update_list(self):
        self.clear()
        self.addItems(self.org_manager.get_list(self.org_type))
        self.setCurrentIndex(-1)
    
    def get_org(self):
        text = self.currentText().strip()
        if text:
            self.org_manager.add(text, self.org_type or 'all')
        return text


# ============= ДИАЛОГ ИСТОРИИ АВТОМОБИЛЯ =============
class CarHistoryDialog(QDialog):
    def __init__(self, car, org_manager, fuel_manager, parent=None):
        super().__init__(parent)
        self.car = car
        self.org_manager = org_manager
        self.fuel_manager = fuel_manager
        self.setWindowTitle(f"История автомобиля {car.plate}")
        self.setModal(True)
        self.resize(1300, 800)
        
        layout = QVBoxLayout()
        
        info_group = QGroupBox("Информация об автомобиле")
        info_layout = QGridLayout()
        
        row = 0
        info_layout.addWidget(QLabel("Марка/Модель:"), row, 0)
        info_layout.addWidget(QLabel(f"{car.vehicle_info.brand} {car.vehicle_info.model}"), row, 1)
        
        info_layout.addWidget(QLabel("Год выпуска:"), row, 2)
        info_layout.addWidget(QLabel(str(car.vehicle_info.year) if car.vehicle_info.year else "-"), row, 3)
        
        row += 1
        info_layout.addWidget(QLabel("VIN:"), row, 0)
        info_layout.addWidget(QLabel(car.vehicle_info.vin if car.vehicle_info.vin else "-"), row, 1)
        
        info_layout.addWidget(QLabel("Тип ТС:"), row, 2)
        vehicle_type = "Легковой" if car.vehicle_info.vehicle_type == 'passenger' else "Грузовой"
        info_layout.addWidget(QLabel(vehicle_type), row, 3)
        
        row += 1
        info_layout.addWidget(QLabel("Текущий пробег:"), row, 0)
        current_mileage = car.get_current_mileage()
        info_layout.addWidget(QLabel(f"{current_mileage} км"), row, 1)
        
        info_layout.addWidget(QLabel("Страховка:"), row, 2)
        ins_days = car.get_insurance_days_left()
        if ins_days is not None:
            ins_text = f"{ins_days} дн."
            ins_label = QLabel(ins_text)
            if ins_days <= 0:
                ins_label.setStyleSheet("color: #ff3b30; font-weight: bold;")
            elif ins_days <= 30:
                ins_label.setStyleSheet("color: #ff9f0a; font-weight: bold;")
            info_layout.addWidget(ins_label, row, 3)
        else:
            info_layout.addWidget(QLabel("-"), row, 3)
        
        row += 1
        info_layout.addWidget(QLabel("Диагностика:"), row, 0)
        diag_days = car.get_diagnostic_days_left()
        if diag_days is not None:
            diag_text = f"{diag_days} дн."
            diag_label = QLabel(diag_text)
            if diag_days <= 0:
                diag_label.setStyleSheet("color: #ff3b30; font-weight: bold;")
            elif diag_days <= 30:
                diag_label.setStyleSheet("color: #ff9f0a; font-weight: bold;")
            info_layout.addWidget(diag_label, row, 1)
        else:
            info_layout.addWidget(QLabel("-"), row, 1)
        
        info_layout.addWidget(QLabel("Тахограф:"), row, 2)
        tach_days = car.get_tachograph_days_left()
        if tach_days is not None:
            tach_text = f"{tach_days} дн."
            tach_label = QLabel(tach_text)
            if tach_days <= 0:
                tach_label.setStyleSheet("color: #ff3b30; font-weight: bold;")
            elif tach_days <= 30:
                tach_label.setStyleSheet("color: #ff9f0a; font-weight: bold;")
            info_layout.addWidget(tach_label, row, 3)
        else:
            info_layout.addWidget(QLabel("-"), row, 3)
        
        row += 1
        info_layout.addWidget(QLabel("Пропуск:"), row, 0)
        permit_days = car.get_permit_days_left()
        if permit_days is not None:
            permit_text = f"{permit_days} дн."
            permit_label = QLabel(permit_text)
            if permit_days <= 0:
                permit_label.setStyleSheet("color: #ff3b30; font-weight: bold;")
            elif permit_days <= 30:
                permit_label.setStyleSheet("color: #ff9f0a; font-weight: bold;")
            info_layout.addWidget(permit_label, row, 1)
        else:
            info_layout.addWidget(QLabel("-"), row, 1)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        tab_widget = QTabWidget()
        
        history_tab = QWidget()
        history_layout = QVBoxLayout(history_tab)
        
        history_filter_layout = QHBoxLayout()
        
        self.history_filter_btn = QPushButton("🔍 Фильтр истории")
        self.history_filter_btn.clicked.connect(self.show_history_filter)
        history_filter_layout.addWidget(self.history_filter_btn)
        
        self.history_filter_label = QLabel("")
        self.history_filter_label.setStyleSheet("QLabel { color: #4a90e2; }")
        history_filter_layout.addWidget(self.history_filter_label)
        
        history_filter_layout.addStretch()
        
        self.history_search = QLineEdit()
        self.history_search.setPlaceholderText("🔍 Поиск по описанию...")
        self.history_search.textChanged.connect(self.filter_history)
        history_filter_layout.addWidget(self.history_search)
        
        history_layout.addLayout(history_filter_layout)
        
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(8)
        self.history_table.setHorizontalHeaderLabels([
            "Дата", "Тип", "Вкладка", "Пробег", "Описание", 
            "Организация", "Стоимость", "Дней до окончания"
        ])
        self.history_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.history_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        history_layout.addWidget(self.history_table)
        tab_widget.addTab(history_tab, "📜 История")
        
        docs_tab = QWidget()
        docs_layout = QVBoxLayout(docs_tab)
        
        docs_filter_layout = QHBoxLayout()
        
        self.docs_filter_btn = QPushButton("🔍 Фильтр документов")
        self.docs_filter_btn.clicked.connect(self.show_docs_filter)
        docs_filter_layout.addWidget(self.docs_filter_btn)
        
        self.docs_filter_label = QLabel("")
        self.docs_filter_label.setStyleSheet("QLabel { color: #4a90e2; }")
        docs_filter_layout.addWidget(self.docs_filter_label)
        
        docs_filter_layout.addStretch()
        
        self.docs_search = QLineEdit()
        self.docs_search.setPlaceholderText("🔍 Поиск по имени файла или описанию...")
        self.docs_search.textChanged.connect(self.filter_documents)
        docs_filter_layout.addWidget(self.docs_search)
        
        docs_layout.addLayout(docs_filter_layout)
        
        self.docs_table = QTableWidget()
        self.docs_table.setColumnCount(8)
        self.docs_table.setHorizontalHeaderLabels([
            "Тип", "Вкладка", "Организация", "Файл", 
            "Описание", "Дата добавления", "Размер", "Путь"
        ])
        self.docs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.docs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.docs_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.docs_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.docs_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        self.docs_table.setAlternatingRowColors(True)
        self.docs_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.docs_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        self.docs_table.itemDoubleClicked.connect(self.open_document)
        
        docs_layout.addWidget(self.docs_table)
        tab_widget.addTab(docs_tab, "📎 Документы")
        
        layout.addWidget(tab_widget)
        
        btn_layout = QHBoxLayout()
        
        export_btn = QPushButton("📤 Экспорт истории")
        export_btn.clicked.connect(self.export_history)
        btn_layout.addWidget(export_btn)
        
        btn_layout.addStretch()
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        
        self.history_filters = {'type': None, 'org': None}
        self.docs_filters = {'type': None, 'org': None}
        self.all_history = []
        self.all_documents = []
        
        self.load_history()
        self.load_documents()
    
    def show_history_filter(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Фильтр истории")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        type_combo = QComboBox()
        type_combo.addItem("Все типы", None)
        type_combo.addItem("Сцепление", 'clutch')
        type_combo.addItem("ТО", 'maintenance')
        type_combo.addItem("Колодки", 'brakes')
        type_combo.addItem("Ремонт", 'repair')
        type_combo.addItem("Страховка", 'insurance')
        type_combo.addItem("Диагностика", 'diagnostic')
        type_combo.addItem("Пропуск", 'permit')
        type_combo.addItem("Тахограф", 'tachograph')
        if self.history_filters['type']:
            index = type_combo.findData(self.history_filters['type'])
            if index >= 0:
                type_combo.setCurrentIndex(index)
        form.addRow("Тип:", type_combo)
        
        org_combo = QComboBox()
        org_combo.addItem("Все организации", None)
        for org in self.org_manager.get_list():
            org_combo.addItem(org, org)
        if self.history_filters['org']:
            index = org_combo.findData(self.history_filters['org'])
            if index >= 0:
                org_combo.setCurrentIndex(index)
        form.addRow("Организация:", org_combo)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        
        apply_btn = QPushButton("Применить")
        apply_btn.clicked.connect(lambda: self.apply_history_filter(type_combo.currentData(), org_combo.currentData(), dialog))
        btn_layout.addWidget(apply_btn)
        
        clear_btn = QPushButton("Сбросить")
        clear_btn.clicked.connect(lambda: self.clear_history_filter(dialog))
        btn_layout.addWidget(clear_btn)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def apply_history_filter(self, type_filter, org_filter, dialog):
        self.history_filters['type'] = type_filter
        self.history_filters['org'] = org_filter
        self.update_history_filter_label()
        self.load_history()
        dialog.accept()
    
    def clear_history_filter(self, dialog):
        self.history_filters = {'type': None, 'org': None}
        self.history_filter_label.setText("")
        self.load_history()
        dialog.accept()
    
    def update_history_filter_label(self):
        filters = []
        type_names = {
            'clutch': 'Сцепление',
            'maintenance': 'ТО',
            'brakes': 'Колодки',
            'repair': 'Ремонт',
            'insurance': 'Страховка',
            'diagnostic': 'Диагностика',
            'permit': 'Пропуск',
            'tachograph': 'Тахограф'
        }
        
        if self.history_filters['type']:
            filters.append(f"Тип: {type_names.get(self.history_filters['type'], self.history_filters['type'])}")
        if self.history_filters['org']:
            filters.append(f"Орг: {self.history_filters['org']}")
        
        if filters:
            self.history_filter_label.setText(" | ".join(filters))
        else:
            self.history_filter_label.setText("")
    
    def show_docs_filter(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Фильтр документов")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        type_combo = QComboBox()
        type_combo.addItem("Все типы", None)
        type_combo.addItem("Сцепление", 'clutch')
        type_combo.addItem("ТО", 'maintenance')
        type_combo.addItem("Колодки", 'brakes')
        type_combo.addItem("Страховка", 'insurance')
        type_combo.addItem("Диагностика", 'diagnostic')
        type_combo.addItem("Пропуск", 'permit')
        type_combo.addItem("Тахограф", 'tachograph')
        type_combo.addItem("Ремонт", 'repair')
        if self.docs_filters['type']:
            index = type_combo.findData(self.docs_filters['type'])
            if index >= 0:
                type_combo.setCurrentIndex(index)
        form.addRow("Тип:", type_combo)
        
        org_combo = QComboBox()
        org_combo.addItem("Все организации", None)
        for org in self.org_manager.get_list():
            org_combo.addItem(org, org)
        if self.docs_filters['org']:
            index = org_combo.findData(self.docs_filters['org'])
            if index >= 0:
                org_combo.setCurrentIndex(index)
        form.addRow("Организация:", org_combo)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        
        apply_btn = QPushButton("Применить")
        apply_btn.clicked.connect(lambda: self.apply_docs_filter(type_combo.currentData(), org_combo.currentData(), dialog))
        btn_layout.addWidget(apply_btn)
        
        clear_btn = QPushButton("Сбросить")
        clear_btn.clicked.connect(lambda: self.clear_docs_filter(dialog))
        btn_layout.addWidget(clear_btn)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(dialog.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def apply_docs_filter(self, type_filter, org_filter, dialog):
        self.docs_filters['type'] = type_filter
        self.docs_filters['org'] = org_filter
        self.update_docs_filter_label()
        self.load_documents()
        dialog.accept()
    
    def clear_docs_filter(self, dialog):
        self.docs_filters = {'type': None, 'org': None}
        self.docs_filter_label.setText("")
        self.load_documents()
        dialog.accept()
    
    def update_docs_filter_label(self):
        filters = []
        type_names = {
            'clutch': 'Сцепление',
            'maintenance': 'ТО',
            'brakes': 'Колодки',
            'insurance': 'Страховка',
            'diagnostic': 'Диагностика',
            'permit': 'Пропуск',
            'tachograph': 'Тахограф',
            'repair': 'Ремонт'
        }
        
        if self.docs_filters['type']:
            filters.append(f"Тип: {type_names.get(self.docs_filters['type'], self.docs_filters['type'])}")
        if self.docs_filters['org']:
            filters.append(f"Орг: {self.docs_filters['org']}")
        
        if filters:
            self.docs_filter_label.setText(" | ".join(filters))
        else:
            self.docs_filter_label.setText("")
    
    def load_history(self):
        self.all_history = self.car.get_all_history()
        
        filtered_history = self.all_history
        if self.history_filters['type']:
            filtered_history = [h for h in filtered_history if h['type'] == self.history_filters['type']]
        if self.history_filters['org']:
            filtered_history = [h for h in filtered_history if h['org'] == self.history_filters['org']]
        
        self.history_table.setRowCount(len(filtered_history))
        
        for row, event in enumerate(filtered_history):
            date_item = QTableWidgetItem(event['date'])
            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            self.history_table.setItem(row, 0, date_item)
            
            type_item = QTableWidgetItem(event['type_name'])
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.history_table.setItem(row, 1, type_item)
            
            tab_item = QTableWidgetItem(event.get('tab', '-'))
            tab_item.setFlags(tab_item.flags() & ~Qt.ItemIsEditable)
            self.history_table.setItem(row, 2, tab_item)
            
            mileage_text = f"{event.get('mileage', '')} км" if event.get('mileage') else "-"
            mileage_item = QTableWidgetItem(mileage_text)
            mileage_item.setFlags(mileage_item.flags() & ~Qt.ItemIsEditable)
            self.history_table.setItem(row, 3, mileage_item)
            
            desc_item = QTableWidgetItem(event['description'])
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
            self.history_table.setItem(row, 4, desc_item)
            
            org = event.get('org', '')
            if not org and 'workshop' in event:
                org = event['workshop']
            org_item = QTableWidgetItem(org)
            org_item.setFlags(org_item.flags() & ~Qt.ItemIsEditable)
            self.history_table.setItem(row, 5, org_item)
            
            cost = event.get('cost', 0)
            cost_item = QTableWidgetItem(f"{cost:,.0f} ₽".replace(",", " ") if cost else "-")
            cost_item.setFlags(cost_item.flags() & ~Qt.ItemIsEditable)
            cost_item.setTextAlignment(Qt.AlignRight)
            self.history_table.setItem(row, 6, cost_item)
            
            days_left = event.get('days_left')
            if days_left is not None:
                days_item = QTableWidgetItem(str(days_left))
                if days_left <= 0:
                    days_item.setForeground(QBrush(QColor(255, 59, 48)))
                elif days_left <= 30:
                    days_item.setForeground(QBrush(QColor(255, 159, 10)))
                days_item.setFlags(days_item.flags() & ~Qt.ItemIsEditable)
                days_item.setTextAlignment(Qt.AlignCenter)
                self.history_table.setItem(row, 7, days_item)
            else:
                days_item = QTableWidgetItem("-")
                days_item.setFlags(days_item.flags() & ~Qt.ItemIsEditable)
                self.history_table.setItem(row, 7, days_item)
        
        self.history_table.resizeColumnsToContents()
    
    def filter_history(self):
        search_text = self.history_search.text().lower()
        
        for row in range(self.history_table.rowCount()):
            desc_item = self.history_table.item(row, 4)
            if desc_item:
                match = search_text in desc_item.text().lower()
                self.history_table.setRowHidden(row, not match)
    
    def load_documents(self):
        self.all_documents = self.car.get_all_documents_for_car()
        
        filtered_docs = self.all_documents
        if self.docs_filters['type']:
            filtered_docs = [d for d in filtered_docs if d['type'] == self.docs_filters['type']]
        if self.docs_filters['org']:
            filtered_docs = [d for d in filtered_docs if d['org'] == self.docs_filters['org']]
        
        self.docs_table.setRowCount(len(filtered_docs))
        
        for row, doc in enumerate(filtered_docs):
            type_item = QTableWidgetItem(doc['type_name'])
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.docs_table.setItem(row, 0, type_item)
            
            tab_item = QTableWidgetItem(doc['tab'])
            tab_item.setFlags(tab_item.flags() & ~Qt.ItemIsEditable)
            self.docs_table.setItem(row, 1, tab_item)
            
            org_item = QTableWidgetItem(doc['org'])
            org_item.setFlags(org_item.flags() & ~Qt.ItemIsEditable)
            self.docs_table.setItem(row, 2, org_item)
            
            file_item = QTableWidgetItem(doc['filename'])
            file_item.setFlags(file_item.flags() & ~Qt.ItemIsEditable)
            self.docs_table.setItem(row, 3, file_item)
            
            desc_item = QTableWidgetItem(doc['description'])
            desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
            self.docs_table.setItem(row, 4, desc_item)
            
            date_item = QTableWidgetItem(doc['added_date'])
            date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
            date_item.setTextAlignment(Qt.AlignCenter)
            self.docs_table.setItem(row, 5, date_item)
            
            size_str = self.format_size(doc['size'])
            size_item = QTableWidgetItem(size_str)
            size_item.setFlags(size_item.flags() & ~Qt.ItemIsEditable)
            size_item.setTextAlignment(Qt.AlignRight)
            self.docs_table.setItem(row, 6, size_item)
            
            path_item = QTableWidgetItem(doc['file_path'])
            path_item.setFlags(path_item.flags() & ~Qt.ItemIsEditable)
            self.docs_table.setItem(row, 7, path_item)
        
        self.docs_table.resizeColumnsToContents()
        self.docs_table.setColumnHidden(7, True)
    
    def filter_documents(self):
        search_text = self.docs_search.text().lower()
        
        for row in range(self.docs_table.rowCount()):
            filename = self.docs_table.item(row, 3).text().lower()
            description = self.docs_table.item(row, 4).text().lower()
            
            match = (search_text in filename or search_text in description)
            
            self.docs_table.setRowHidden(row, not match)
    
    def format_size(self, size):
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} ТБ"
    
    def open_document(self, item):
        row = item.row()
        file_path = self.docs_table.item(row, 7).text()
        if os.path.exists(file_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
        else:
            QMessageBox.warning(self, "Ошибка", "Файл не найден!")
    
    def export_history(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Сохранить историю", 
            f"history_{self.car.plate}_{date.today().isoformat()}.txt",
            "Текстовые файлы (*.txt);;Все файлы (*.*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"История автомобиля {self.car.plate}\n")
                    f.write(f"Дата экспорта: {date.today().isoformat()}\n")
                    f.write("="*80 + "\n\n")
                    
                    history = self.car.get_all_history()
                    for event in history:
                        f.write(f"Дата: {event['date']}\n")
                        f.write(f"Тип: {event['type_name']}\n")
                        f.write(f"Вкладка: {event.get('tab', '-')}\n")
                        if event.get('mileage'):
                            f.write(f"Пробег: {event['mileage']} км\n")
                        f.write(f"Описание: {event['description']}\n")
                        if event.get('org'):
                            f.write(f"Организация: {event['org']}\n")
                        if event.get('cost'):
                            f.write(f"Стоимость: {event['cost']} ₽\n")
                        if event.get('end_date'):
                            f.write(f"Действителен до: {event['end_date']}\n")
                            if event.get('days_left') is not None:
                                f.write(f"Осталось дней: {event['days_left']}\n")
                        f.write("-"*40 + "\n")
                
                QMessageBox.information(self, "Успех", f"История сохранена в {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить историю:\n{str(e)}")


class VehicleDialog(QDialog):
    def __init__(self, org_manager, parent=None, car=None):
        super().__init__(parent)
        self.org_manager = org_manager
        self.car = car
        self.setWindowTitle("Добавить автомобиль" if not car else "Редактировать автомобиль")
        self.setModal(True)
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        main_group = QGroupBox("Основная информация")
        main_layout = QFormLayout()
        
        self.plate = QLineEdit()
        self.plate.setPlaceholderText("А123ВС777")
        if car:
            self.plate.setText(car.plate)
            self.plate.setEnabled(False)
        main_layout.addRow("Госномер:", self.plate)
        
        self.brand = QLineEdit()
        self.brand.setPlaceholderText("Марка")
        if car:
            self.brand.setText(car.vehicle_info.brand)
        main_layout.addRow("Марка:", self.brand)
        
        self.model = QLineEdit()
        self.model.setPlaceholderText("Модель")
        if car:
            self.model.setText(car.vehicle_info.model)
        main_layout.addRow("Модель:", self.model)
        
        self.year = QSpinBox()
        self.year.setRange(1900, 2050)
        self.year.setSpecialValueText("Не указан")
        if car and car.vehicle_info.year:
            self.year.setValue(car.vehicle_info.year)
        main_layout.addRow("Год выпуска:", self.year)
        
        self.vin = QLineEdit()
        self.vin.setPlaceholderText("VIN номер")
        self.vin.setMaxLength(17)
        if car:
            self.vin.setText(car.vehicle_info.vin)
        main_layout.addRow("VIN:", self.vin)
        
        main_group.setLayout(main_layout)
        layout.addWidget(main_group)
        
        type_group = QGroupBox("Тип транспортного средства")
        type_layout = QVBoxLayout()
        
        self.vehicle_type = QComboBox()
        self.vehicle_type.addItem("Легковой", 'passenger')
        self.vehicle_type.addItem("Грузовой", 'cargo')
        if car:
            index = self.vehicle_type.findData(car.vehicle_info.vehicle_type)
            if index >= 0:
                self.vehicle_type.setCurrentIndex(index)
        type_layout.addWidget(self.vehicle_type)
        
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        self.cargo_group = QGroupBox("Грузовой отсек")
        cargo_layout = QFormLayout()
        
        self.cargo_length = QSpinBox()
        self.cargo_length.setRange(0, 2000)
        self.cargo_length.setSuffix(" см")
        self.cargo_length.setSpecialValueText("Не указано")
        if car and car.vehicle_info.cargo_length:
            self.cargo_length.setValue(car.vehicle_info.cargo_length)
        cargo_layout.addRow("Длина:", self.cargo_length)
        
        self.cargo_width = QSpinBox()
        self.cargo_width.setRange(0, 2000)
        self.cargo_width.setSuffix(" см")
        self.cargo_width.setSpecialValueText("Не указано")
        if car and car.vehicle_info.cargo_width:
            self.cargo_width.setValue(car.vehicle_info.cargo_width)
        cargo_layout.addRow("Ширина:", self.cargo_width)
        
        self.cargo_height = QSpinBox()
        self.cargo_height.setRange(0, 2000)
        self.cargo_height.setSuffix(" см")
        self.cargo_height.setSpecialValueText("Не указано")
        if car and car.vehicle_info.cargo_height:
            self.cargo_height.setValue(car.vehicle_info.cargo_height)
        cargo_layout.addRow("Высота:", self.cargo_height)
        
        self.cargo_capacity = QSpinBox()
        self.cargo_capacity.setRange(0, 100000)
        self.cargo_capacity.setSuffix(" кг")
        self.cargo_capacity.setSpecialValueText("Не указано")
        if car and car.vehicle_info.cargo_capacity:
            self.cargo_capacity.setValue(car.vehicle_info.cargo_capacity)
        cargo_layout.addRow("Грузоподъемность:", self.cargo_capacity)
        
        self.cargo_group.setLayout(cargo_layout)
        layout.addWidget(self.cargo_group)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
        
        self.vehicle_type.currentIndexChanged.connect(self.on_type_changed)
        self.on_type_changed()
    
    def on_type_changed(self):
        if hasattr(self, 'cargo_group'):
            is_cargo = self.vehicle_type.currentData() == 'cargo'
            self.cargo_group.setVisible(is_cargo)
    
    def get_car(self):
        plate = self.plate.text().upper().strip()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Введите госномер!")
            return None
        
        if self.car:
            car = self.car
        else:
            car = Car(plate)
        
        vehicle_info = VehicleInfo(
            plate,
            self.brand.text().strip(),
            self.model.text().strip(),
            self.year.value() if self.year.value() > 0 else 0,
            self.vin.text().strip().upper(),
            self.vehicle_type.currentData(),
            self.cargo_length.value() if self.cargo_length.value() > 0 else 0,
            self.cargo_width.value() if self.cargo_width.value() > 0 else 0,
            self.cargo_height.value() if self.cargo_height.value() > 0 else 0,
            self.cargo_capacity.value() if self.cargo_capacity.value() > 0 else 0
        )
        
        car.set_vehicle_info(vehicle_info)
        return car


class VehiclesTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        top_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Добавить автомобиль")
        self.add_btn.clicked.connect(self.add_vehicle)
        self.add_btn.setFixedHeight(35)
        top_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("✏️ Редактировать")
        self.edit_btn.clicked.connect(self.edit_vehicle)
        self.edit_btn.setFixedHeight(35)
        top_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("❌ Удалить")
        self.delete_btn.clicked.connect(self.delete_vehicle)
        self.delete_btn.setFixedHeight(35)
        top_layout.addWidget(self.delete_btn)
        
        self.history_btn = QPushButton("📜 История")
        self.history_btn.clicked.connect(self.show_history)
        self.history_btn.setFixedHeight(35)
        top_layout.addWidget(self.history_btn)
        
        top_layout.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск по номеру, марке...")
        self.search_input.textChanged.connect(self.filter_table)
        self.search_input.setFixedHeight(35)
        self.search_input.setFixedWidth(250)
        top_layout.addWidget(self.search_input)
        
        layout.addLayout(top_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(13)
        self.table.setHorizontalHeaderLabels([
            "Госномер", "Марка", "Модель", "Год", "VIN", "Тип",
            "Пробег", "Страховка", "Диагностика", "Тахограф", "Пропуск", "Документы", "Статусы"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.table.itemDoubleClicked.connect(self.show_history_from_item)
        
        layout.addWidget(self.table)
        
        self.update_table()
    
    def update_table(self):
        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)
        
        row = 0
        for plate, car in sorted(self.parent.cars.items()):
            self.table.insertRow(row)
            
            plate_item = QTableWidgetItem(plate)
            plate_item.setFlags(plate_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, plate_item)
            
            brand_item = QTableWidgetItem(car.vehicle_info.brand)
            brand_item.setFlags(brand_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, brand_item)
            
            model_item = QTableWidgetItem(car.vehicle_info.model)
            model_item.setFlags(model_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 2, model_item)
            
            year_item = QTableWidgetItem(str(car.vehicle_info.year) if car.vehicle_info.year else "-")
            year_item.setFlags(year_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 3, year_item)
            
            vin_item = QTableWidgetItem(car.vehicle_info.vin if car.vehicle_info.vin else "-")
            vin_item.setFlags(vin_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 4, vin_item)
            
            vehicle_type = "Легковой" if car.vehicle_info.vehicle_type == 'passenger' else "Грузовой"
            type_item = QTableWidgetItem(vehicle_type)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 5, type_item)
            
            mileage = car.get_current_mileage()
            mileage_item = QTableWidgetItem(f"{mileage} км" if mileage else "-")
            mileage_item.setFlags(mileage_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 6, mileage_item)
            
            ins_days = car.get_insurance_days_left()
            if ins_days is not None:
                ins_text = f"{ins_days} дн."
                ins_item = QTableWidgetItem(ins_text)
                if ins_days <= 0:
                    ins_item.setForeground(QBrush(QColor(255, 59, 48)))
                elif ins_days <= 30:
                    ins_item.setForeground(QBrush(QColor(255, 159, 10)))
                ins_item.setFlags(ins_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, 7, ins_item)
            else:
                ins_item = QTableWidgetItem("-")
                ins_item.setFlags(ins_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, 7, ins_item)
            
            diag_days = car.get_diagnostic_days_left()
            if diag_days is not None:
                diag_text = f"{diag_days} дн."
                diag_item = QTableWidgetItem(diag_text)
                if diag_days <= 0:
                    diag_item.setForeground(QBrush(QColor(255, 59, 48)))
                elif diag_days <= 30:
                    diag_item.setForeground(QBrush(QColor(255, 159, 10)))
                diag_item.setFlags(diag_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, 8, diag_item)
            else:
                diag_item = QTableWidgetItem("-")
                diag_item.setFlags(diag_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, 8, diag_item)
            
            tach_days = car.get_tachograph_days_left()
            if tach_days is not None:
                tach_text = f"{tach_days} дн."
                tach_item = QTableWidgetItem(tach_text)
                if tach_days <= 0:
                    tach_item.setForeground(QBrush(QColor(255, 59, 48)))
                elif tach_days <= 30:
                    tach_item.setForeground(QBrush(QColor(255, 159, 10)))
                tach_item.setFlags(tach_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, 9, tach_item)
            else:
                tach_item = QTableWidgetItem("-")
                tach_item.setFlags(tach_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, 9, tach_item)
            
            permit_days = car.get_permit_days_left()
            if permit_days is not None:
                permit_text = f"{permit_days} дн."
                permit_item = QTableWidgetItem(permit_text)
                if permit_days <= 0:
                    permit_item.setForeground(QBrush(QColor(255, 59, 48)))
                elif permit_days <= 30:
                    permit_item.setForeground(QBrush(QColor(255, 159, 10)))
                permit_item.setFlags(permit_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, 10, permit_item)
            else:
                permit_item = QTableWidgetItem("-")
                permit_item.setFlags(permit_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, 10, permit_item)
            
            doc_paths = []
            for service in car.services:
                doc_paths.extend([d.file_path for d in service.documents])
            for ins in car.insurances:
                doc_paths.extend([d.file_path for d in ins.documents])
            for card in car.diagnostic_cards:
                doc_paths.extend([d.file_path for d in card.documents])
            for repair in car.repairs:
                doc_paths.extend([d.file_path for d in repair.documents])
            for permit in car.permits:
                doc_paths.extend([d.file_path for d in permit.documents])
            for tach in car.tachographs:
                doc_paths.extend([d.file_path for d in tach.documents])
            
            doc_count = len(doc_paths)
            doc_label = DocumentClickableLabel(f"📎 {doc_count}" if doc_count > 0 else "", doc_paths)
            self.table.setCellWidget(row, 11, doc_label)
            
            status_text = ""
            status_color = "#28cd41"
            
            if (ins_days is not None and ins_days <= 0) or \
               (diag_days is not None and diag_days <= 0) or \
               (tach_days is not None and tach_days <= 0) or \
               (permit_days is not None and permit_days <= 0):
                status_text = "⚠️ Срочно!"
                status_color = "#ff3b30"
            elif (ins_days is not None and ins_days <= 30) or \
                 (diag_days is not None and diag_days <= 30) or \
                 (tach_days is not None and tach_days <= 30) or \
                 (permit_days is not None and permit_days <= 30):
                status_text = "⚠️ Скоро"
                status_color = "#ff9f0a"
            
            status_item = QTableWidgetItem(status_text)
            status_item.setForeground(QBrush(QColor(status_color)))
            status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 12, status_item)
            
            row += 1
        
        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()
    
    def filter_table(self):
        search_text = self.search_input.text().lower()
        
        for row in range(self.table.rowCount()):
            plate_item = self.table.item(row, 0)
            brand_item = self.table.item(row, 1)
            model_item = self.table.item(row, 2)
            if plate_item and brand_item and model_item:
                match = (search_text in plate_item.text().lower() or 
                        search_text in brand_item.text().lower() or
                        search_text in model_item.text().lower())
                self.table.setRowHidden(row, not match)
    
    def get_selected_plate(self):
        row = self.table.currentRow()
        if row >= 0:
            return self.table.item(row, 0).text()
        return None
    
    def show_history_from_item(self, item):
        row = item.row()
        plate = self.table.item(row, 0).text()
        if plate in self.parent.cars:
            dialog = CarHistoryDialog(self.parent.cars[plate], self.parent.org_manager, self.parent.fuel_manager, self)
            dialog.exec_()
    
    def show_history(self):
        plate = self.get_selected_plate()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите автомобиль!")
            return
        
        if plate in self.parent.cars:
            dialog = CarHistoryDialog(self.parent.cars[plate], self.parent.org_manager, self.parent.fuel_manager, self)
            dialog.exec_()
    
    def add_vehicle(self):
        dialog = VehicleDialog(self.parent.org_manager, self)
        if dialog.exec_() == QDialog.Accepted:
            car = dialog.get_car()
            if car and car.plate:
                if car.plate in self.parent.cars:
                    QMessageBox.warning(self, "Ошибка", "Автомобиль уже существует!")
                    return
                
                self.parent.cars[car.plate] = car
                self.parent.save_data()
                self.parent.update_all_tables()
                self.update_table()
                self.parent.status_label.setText(f"✓ Автомобиль {car.plate} добавлен")
    
    def edit_vehicle(self):
        plate = self.get_selected_plate()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите автомобиль!")
            return
        
        if plate in self.parent.cars:
            car = self.parent.cars[plate]
            dialog = VehicleDialog(self.parent.org_manager, self, car)
            if dialog.exec_() == QDialog.Accepted:
                updated_car = dialog.get_car()
                if updated_car and updated_car.plate != plate:
                    if updated_car.plate in self.parent.cars:
                        QMessageBox.warning(self, "Ошибка", "Автомобиль с таким номером уже существует!")
                        return
                    updated_car.services = car.services
                    updated_car.insurances = car.insurances
                    updated_car.diagnostic_cards = car.diagnostic_cards
                    updated_car.repairs = car.repairs
                    updated_car.permits = car.permits
                    updated_car.tachographs = car.tachographs
                    
                    del self.parent.cars[plate]
                    self.parent.cars[updated_car.plate] = updated_car
                else:
                    car.vehicle_info = updated_car.vehicle_info
                
                self.parent.save_data()
                self.parent.update_all_tables()
                self.update_table()
                self.parent.status_label.setText(f"✓ Автомобиль обновлен")
    
    def delete_vehicle(self):
        plate = self.get_selected_plate()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите автомобиль!")
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить автомобиль {plate}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            del self.parent.cars[plate]
            self.parent.save_data()
            self.parent.update_all_tables()
            self.update_table()
            self.parent.status_label.setText(f"✓ Автомобиль {plate} удален")


class FuelTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.fuel_manager = parent.fuel_manager
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        top_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Добавить месяц")
        self.add_btn.clicked.connect(self.add_monthly_record)
        self.add_btn.setFixedHeight(35)
        top_layout.addWidget(self.add_btn)
        
        self.set_norm_btn = QPushButton("📊 Установить норму")
        self.set_norm_btn.clicked.connect(self.set_norm)
        self.set_norm_btn.setFixedHeight(35)
        top_layout.addWidget(self.set_norm_btn)
        
        self.delete_btn = QPushButton("❌ Удалить")
        self.delete_btn.clicked.connect(self.delete_record)
        self.delete_btn.setFixedHeight(35)
        top_layout.addWidget(self.delete_btn)
        
        top_layout.addStretch()
        
        self.car_filter = QComboBox()
        self.car_filter.addItem("Все автомобили", None)
        self.car_filter.currentIndexChanged.connect(self.update_table)
        self.car_filter.setFixedHeight(35)
        self.car_filter.setFixedWidth(150)
        top_layout.addWidget(QLabel("Автомобиль:"))
        top_layout.addWidget(self.car_filter)
        
        layout.addLayout(top_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels([
            "Автомобиль", "Период", "Литры", "Пробег (км)", 
            "Расход (л/100км)", "Норма", "Отклонение"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.table.itemDoubleClicked.connect(self.show_car_history)
        
        layout.addWidget(self.table)
        
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }")
        self.stats_label.setFixedHeight(60)
        layout.addWidget(self.stats_label)
        
        self.update_table()
        self.update_car_filter()
    
    def update_car_filter(self):
        self.car_filter.clear()
        self.car_filter.addItem("Все автомобили", None)
        for plate in sorted(self.parent.cars.keys()):
            self.car_filter.addItem(plate, plate)
    
    def get_selected_record(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        
        plate = self.table.item(row, 0).text()
        period = self.table.item(row, 1).text()
        
        year, month = map(int, period.split('-'))
        
        for record in self.fuel_manager.records:
            if (record.car_plate == plate and 
                record.year == year and 
                record.month == month):
                return record
        return None
    
    def show_car_history(self, item):
        row = item.row()
        plate = self.table.item(row, 0).text()
        if plate in self.parent.cars:
            dialog = CarHistoryDialog(self.parent.cars[plate], self.parent.org_manager, self.parent.fuel_manager, self)
            dialog.exec_()
    
    def add_monthly_record(self):
        plates = list(self.parent.cars.keys())
        if not plates:
            QMessageBox.warning(self, "Ошибка", "Сначала добавьте автомобиль!")
            return
        
        plate, ok = QInputDialog.getItem(
            self, "Выберите автомобиль", 
            "Автомобиль:", plates, 0, False
        )
        
        if not ok or not plate:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Добавить данные за месяц для {plate}")
        dialog.setModal(True)
        dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        form = QFormLayout()
        
        month_year = MonthYearEdit()
        form.addRow("Месяц:", month_year)
        
        liters = QDoubleSpinBox()
        liters.setRange(0, 10000)
        liters.setSuffix(" л")
        liters.setDecimals(2)
        liters.setValue(0)
        form.addRow("Заправлено литров:", liters)
        
        distance = QSpinBox()
        distance.setRange(0, 999999)
        distance.setSuffix(" км")
        distance.setValue(0)
        form.addRow("Пробег за месяц:", distance)
        
        notes = QLineEdit()
        notes.setPlaceholderText("Примечания")
        form.addRow("Примечания:", notes)
        
        layout.addLayout(form)
        
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            record = MonthlyFuelRecord(
                plate,
                month_year.get_year(),
                month_year.get_month(),
                liters.value(),
                distance.value(),
                notes.text()
            )
            self.fuel_manager.add_record(record)
            self.update_table()
            self.parent.status_label.setText(f"✓ Данные за {month_year.current_text()} добавлены для {plate}")
    
    def set_norm(self):
        plates = list(self.parent.cars.keys())
        if not plates:
            QMessageBox.warning(self, "Ошибка", "Сначала добавьте автомобиль!")
            return
        
        plate, ok = QInputDialog.getItem(
            self, "Выберите автомобиль", 
            "Автомобиль:", plates, 0, False
        )
        
        if not ok or not plate:
            return
        
        current_norm = self.fuel_manager.get_norm(plate)
        
        norm, ok = QInputDialog.getDouble(
            self, "Норма расхода",
            f"Введите норму расхода для {plate} (л/100км):",
            current_norm, 0, 50, 1
        )
        
        if ok:
            self.fuel_manager.set_norm(plate, norm)
            self.update_table()
            self.parent.status_label.setText(f"✓ Норма расхода установлена для {plate}")
    
    def delete_record(self):
        record = self.get_selected_record()
        if not record:
            QMessageBox.warning(self, "Ошибка", "Выберите запись для удаления!")
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить данные за {record.period}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.fuel_manager.delete_record(record)
            self.update_table()
            self.parent.status_label.setText(f"✓ Данные удалены")
    
    def update_table(self):
        self.table.setRowCount(0)
        self.table.setSortingEnabled(False)
        
        selected_plate = self.car_filter.currentData()
        
        records = self.fuel_manager.records
        if selected_plate:
            records = [r for r in records if r.car_plate == selected_plate]
        
        records.sort(key=lambda x: (x.car_plate, x.year, x.month), reverse=True)
        
        row = 0
        for record in records:
            self.table.insertRow(row)
            
            plate_item = QTableWidgetItem(record.car_plate)
            plate_item.setFlags(plate_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, plate_item)
            
            period_item = QTableWidgetItem(record.period)
            period_item.setFlags(period_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, period_item)
            
            liters_item = QTableWidgetItem(f"{record.liters:.2f} л")
            liters_item.setFlags(liters_item.flags() & ~Qt.ItemIsEditable)
            liters_item.setTextAlignment(Qt.AlignRight)
            self.table.setItem(row, 2, liters_item)
            
            distance_item = QTableWidgetItem(f"{record.distance} км")
            distance_item.setFlags(distance_item.flags() & ~Qt.ItemIsEditable)
            distance_item.setTextAlignment(Qt.AlignRight)
            self.table.setItem(row, 3, distance_item)
            
            consumption = record.consumption
            consumption_item = QTableWidgetItem(f"{consumption:.2f}" if consumption > 0 else "-")
            consumption_item.setFlags(consumption_item.flags() & ~Qt.ItemIsEditable)
            consumption_item.setTextAlignment(Qt.AlignRight)
            if consumption > 0:
                norm = self.fuel_manager.get_norm(record.car_plate)
                if norm > 0 and consumption > norm * 1.1:
                    consumption_item.setForeground(QBrush(QColor(255, 59, 48)))
                elif norm > 0 and consumption < norm * 0.9:
                    consumption_item.setForeground(QBrush(QColor(40, 205, 65)))
            self.table.setItem(row, 4, consumption_item)
            
            norm = self.fuel_manager.get_norm(record.car_plate)
            norm_item = QTableWidgetItem(f"{norm:.2f}" if norm > 0 else "-")
            norm_item.setFlags(norm_item.flags() & ~Qt.ItemIsEditable)
            norm_item.setTextAlignment(Qt.AlignRight)
            self.table.setItem(row, 5, norm_item)
            
            if norm > 0 and consumption > 0:
                deviation = consumption - norm
                deviation_item = QTableWidgetItem(f"{deviation:+.2f}")
                deviation_item.setFlags(deviation_item.flags() & ~Qt.ItemIsEditable)
                deviation_item.setTextAlignment(Qt.AlignRight)
                if deviation > 1:
                    deviation_item.setForeground(QBrush(QColor(255, 59, 48)))
                elif deviation < -1:
                    deviation_item.setForeground(QBrush(QColor(40, 205, 65)))
                self.table.setItem(row, 6, deviation_item)
            else:
                deviation_item = QTableWidgetItem("-")
                deviation_item.setFlags(deviation_item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row, 6, deviation_item)
            
            row += 1
        
        self.table.setSortingEnabled(True)
        self.table.resizeColumnsToContents()
        
        self.update_stats()
    
    def update_stats(self):
        selected_plate = self.car_filter.currentData()
        
        if selected_plate:
            stats = self.fuel_manager.get_stats(selected_plate)
            avg_consumption = self.fuel_manager.get_average_consumption(selected_plate, 3)
            
            self.stats_label.setText(
                f"<b>{selected_plate}</b><br>"
                f"Всего: {stats['total_liters']:.2f} л | Пробег: {stats['total_distance']} км<br>"
                f"Средний расход (всего): {stats['avg_consumption']:.2f} л/100км | "
                f"Средний расход (3 мес): {avg_consumption:.2f} л/100км | "
                f"Норма: {stats['norm']:.2f} л/100км"
            )
        else:
            total_liters = sum(r.liters for r in self.fuel_manager.records)
            total_distance = sum(r.distance for r in self.fuel_manager.records)
            avg_consumption = (total_liters / total_distance * 100) if total_distance > 0 else 0
            
            self.stats_label.setText(
                f"<b>Общая статистика</b><br>"
                f"Всего записей: {len(self.fuel_manager.records)} | "
                f"Всего литров: {total_liters:.2f} л | Всего пробег: {total_distance} км<br>"
                f"Средний расход: {avg_consumption:.2f} л/100км"
            )


class StatisticsTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        control_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск по автомобилю или описанию...")
        self.search_input.textChanged.connect(self.update_stats)
        control_layout.addWidget(self.search_input)
        
        self.year_combo = QComboBox()
        self.year_combo.addItem("Все годы")
        current_year = date.today().year
        for year in range(current_year - 5, current_year + 1):
            self.year_combo.addItem(str(year))
        self.year_combo.currentTextChanged.connect(self.update_stats)
        control_layout.addWidget(self.year_combo)
        
        self.month_combo = QComboBox()
        self.month_combo.addItem("Все месяцы")
        months = [
            "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
            "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
        ]
        for i, month in enumerate(months, 1):
            self.month_combo.addItem(month, i)
        self.month_combo.currentTextChanged.connect(self.update_stats)
        control_layout.addWidget(self.month_combo)
        
        refresh_btn = QPushButton("🔄 Обновить")
        refresh_btn.clicked.connect(self.update_stats)
        control_layout.addWidget(refresh_btn)
        
        control_layout.addStretch()
        
        layout.addLayout(control_layout)
        
        self.stats_table = QTableWidget()
        headers = ["Категория"] + [month[:3] for month in months] + ["Всего"]
        self.stats_table.setColumnCount(len(headers))
        self.stats_table.setHorizontalHeaderLabels(headers)
        self.stats_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.stats_table.setAlternatingRowColors(True)
        self.stats_table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        layout.addWidget(self.stats_table)
        
        if MATPLOTLIB_AVAILABLE:
            self.figure = Figure(figsize=(10, 4))
            self.canvas = FigureCanvas(self.figure)
            layout.addWidget(self.canvas)
        
        self.update_stats()
    
    def update_stats(self):
        search_text = self.search_input.text().lower()
        selected_year = self.year_combo.currentText()
        selected_month = self.month_combo.currentData()
        
        categories = {
            'Сцепление': [],
            'ТО': [],
            'Колодки': [],
            'Ремонт': [],
            'Страховка': [],
            'Диагностика': [],
            'Пропуск': [],
            'Тахограф': [],
            'Топливо': []
        }
        
        monthly_totals = defaultdict(float)
        category_monthly = {cat: [0]*12 for cat in categories}
        
        for car in self.parent.cars.values():
            if search_text and search_text not in car.plate.lower():
                has_match = False
                for repair in car.repairs:
                    if search_text in repair.description.lower():
                        has_match = True
                        break
                if not has_match:
                    continue
            
            service = car.get_service('clutch')
            if service:
                for event in service.history:
                    if 'date' in event:
                        try:
                            event_date = date.fromisoformat(event['date'])
                            if self.filter_date(event_date, selected_year, selected_month):
                                month = event_date.month - 1
                                category_monthly['Сцепление'][month] += 0
                                monthly_totals[month] += 0
                        except:
                            pass
            
            service = car.get_service('maintenance')
            if service:
                for event in service.history:
                    if 'date' in event:
                        try:
                            event_date = date.fromisoformat(event['date'])
                            if self.filter_date(event_date, selected_year, selected_month):
                                month = event_date.month - 1
                                category_monthly['ТО'][month] += 0
                        except:
                            pass
            
            service = car.get_service('brakes')
            if service:
                for event in service.history:
                    if 'date' in event:
                        try:
                            event_date = date.fromisoformat(event['date'])
                            if self.filter_date(event_date, selected_year, selected_month):
                                month = event_date.month - 1
                                category_monthly['Колодки'][month] += 0
                        except:
                            pass
            
            for repair in car.repairs:
                try:
                    event_date = date.fromisoformat(repair.date_performed)
                    if self.filter_date(event_date, selected_year, selected_month):
                        month = event_date.month - 1
                        category_monthly['Ремонт'][month] += repair.cost
                        monthly_totals[month] += repair.cost
                except:
                    pass
            
            for ins in car.insurances:
                try:
                    event_date = date.fromisoformat(ins.start_date)
                    if self.filter_date(event_date, selected_year, selected_month):
                        month = event_date.month - 1
                        category_monthly['Страховка'][month] += ins.cost
                        monthly_totals[month] += ins.cost
                except:
                    pass
            
            for card in car.diagnostic_cards:
                try:
                    event_date = date.fromisoformat(card.issue_date)
                    if self.filter_date(event_date, selected_year, selected_month):
                        month = event_date.month - 1
                        category_monthly['Диагностика'][month] += card.cost
                        monthly_totals[month] += card.cost
                except:
                    pass
            
            for permit in car.permits:
                try:
                    event_date = date.fromisoformat(permit.start_date)
                    if self.filter_date(event_date, selected_year, selected_month):
                        month = event_date.month - 1
                        category_monthly['Пропуск'][month] += permit.cost
                        monthly_totals[month] += permit.cost
                except:
                    pass
            
            for tach in car.tachographs:
                for event in tach.history:
                    if 'calibration_date' in event:
                        try:
                            event_date = date.fromisoformat(event['calibration_date'])
                            if self.filter_date(event_date, selected_year, selected_month):
                                month = event_date.month - 1
                                category_monthly['Тахограф'][month] += event.get('cost', 0)
                                monthly_totals[month] += event.get('cost', 0)
                        except:
                            pass
            
            for record in self.parent.fuel_manager.get_records_for_car(car.plate):
                try:
                    event_date = date(record.year, record.month, 1)
                    if self.filter_date(event_date, selected_year, selected_month):
                        month = event_date.month - 1
                        cost = record.liters * 50
                        category_monthly['Топливо'][month] += cost
                        monthly_totals[month] += cost
                except:
                    pass
        
        self.stats_table.setRowCount(len(categories) + 1)
        
        row = 0
        for category, months in category_monthly.items():
            cat_item = QTableWidgetItem(category)
            cat_item.setFlags(cat_item.flags() & ~Qt.ItemIsEditable)
            self.stats_table.setItem(row, 0, cat_item)
            
            total = 0
            for col in range(12):
                value = months[col]
                total += value
                item = QTableWidgetItem(f"{value:,.0f} ₽".replace(",", " ") if value > 0 else "-")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                item.setTextAlignment(Qt.AlignRight)
                self.stats_table.setItem(row, col + 1, item)
            
            total_item = QTableWidgetItem(f"{total:,.0f} ₽".replace(",", " ") if total > 0 else "-")
            total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
            total_item.setTextAlignment(Qt.AlignRight)
            self.stats_table.setItem(row, 13, total_item)
            
            row += 1
        
        total_item = QTableWidgetItem("ВСЕГО")
        total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
        self.stats_table.setItem(row, 0, total_item)
        
        grand_total = 0
        for col in range(12):
            col_total = monthly_totals[col]
            grand_total += col_total
            item = QTableWidgetItem(f"{col_total:,.0f} ₽".replace(",", " ") if col_total > 0 else "-")
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            item.setTextAlignment(Qt.AlignRight)
            self.stats_table.setItem(row, col + 1, item)
        
        total_item = QTableWidgetItem(f"{grand_total:,.0f} ₽".replace(",", " "))
        total_item.setFlags(total_item.flags() & ~Qt.ItemIsEditable)
        total_item.setTextAlignment(Qt.AlignRight)
        self.stats_table.setItem(row, 13, total_item)
        
        self.stats_table.resizeColumnsToContents()
        
        self.update_chart(monthly_totals)
    
    def filter_date(self, event_date, selected_year, selected_month):
        if selected_year != "Все годы" and str(event_date.year) != selected_year:
            return False
        if selected_month and event_date.month != selected_month:
            return False
        return True
    
    def update_chart(self, monthly_totals):
        if not MATPLOTLIB_AVAILABLE:
            return
        
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        months = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн',
                  'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']
        
        values = [monthly_totals[i] for i in range(12)]
        
        ax.bar(months, values, color='#4a90e2')
        ax.set_ylabel('Расходы (₽)')
        ax.set_title('Расходы по месяцам')
        
        for tick in ax.get_xticklabels():
            tick.set_rotation(45)
        
        self.figure.tight_layout()
        self.canvas.draw()


class ServiceTab(QWidget):
    def __init__(self, parent, service_type, title):
        super().__init__()
        self.parent = parent
        self.service_type = service_type
        self.title = title
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        top_layout = QHBoxLayout()
        
        self.update_btn = QPushButton("📊 Обновить пробег")
        self.update_btn.clicked.connect(self.update_mileage)
        self.update_btn.setFixedHeight(35)
        top_layout.addWidget(self.update_btn)
        
        self.service_btn = QPushButton("🔧 Зарегистрировать замену")
        self.service_btn.clicked.connect(self.service_done)
        self.service_btn.setFixedHeight(35)
        top_layout.addWidget(self.service_btn)
        
        self.history_btn = QPushButton("📜 История")
        self.history_btn.clicked.connect(self.show_history)
        self.history_btn.setFixedHeight(35)
        top_layout.addWidget(self.history_btn)
        
        self.doc_btn = QPushButton("📎 Прикрепить документ")
        self.doc_btn.clicked.connect(self.add_document)
        self.doc_btn.setFixedHeight(35)
        top_layout.addWidget(self.doc_btn)
        
        top_layout.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск по номеру...")
        self.search_input.textChanged.connect(self.filter_table)
        self.search_input.setFixedHeight(35)
        self.search_input.setFixedWidth(200)
        top_layout.addWidget(self.search_input)
        
        layout.addLayout(top_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Госномер", "Тек. пробег", "Последняя замена",
            "Интервал", "Осталось", "Дата замены", "Организация", "Статус", "Документы"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 9):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.table.itemDoubleClicked.connect(self.show_car_history)
        
        layout.addWidget(self.table)
    
    def get_selected_car(self):
        row = self.table.currentRow()
        if row >= 0:
            return self.table.item(row, 0).text()
        return None
    
    def filter_table(self):
        search_text = self.search_input.text().lower()
        
        for row in range(self.table.rowCount()):
            plate_item = self.table.item(row, 0)
            if plate_item:
                match = search_text in plate_item.text().lower()
                self.table.setRowHidden(row, not match)
    
    def show_car_history(self, item):
        row = item.row()
        plate = self.table.item(row, 0).text()
        if plate in self.parent.cars:
            dialog = CarHistoryDialog(self.parent.cars[plate], self.parent.org_manager, self.parent.fuel_manager, self)
            dialog.exec_()
    
    def update_mileage(self):
        plate = self.get_selected_car()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите автомобиль!")
            return
        
        if plate in self.parent.cars:
            car = self.parent.cars[plate]
            service = car.get_service(self.service_type)
            
            if service:
                dialog = QDialog(self)
                dialog.setWindowTitle("Обновить пробег")
                dialog.setModal(True)
                
                layout = QVBoxLayout()
                
                form = QFormLayout()
                
                spin = QSpinBox()
                spin.setRange(service.current_mileage, 9999999)
                spin.setValue(service.current_mileage)
                spin.setSuffix(" км")
                form.addRow("Новый пробег:", spin)
                
                layout.addLayout(form)
                
                buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)
                
                dialog.setLayout(layout)
                
                if dialog.exec_() == QDialog.Accepted:
                    new_mileage = spin.value()
                    service.update_mileage(new_mileage)
                    self.parent.save_data()
                    self.parent.update_all_tables()
                    self.parent.status_label.setText(f"✓ {plate}: пробег обновлен до {new_mileage} км")
    
    def service_done(self):
        plate = self.get_selected_car()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите автомобиль!")
            return
        
        if plate in self.parent.cars:
            car = self.parent.cars[plate]
            service = car.get_service(self.service_type)
            
            if service:
                dialog = QDialog(self)
                dialog.setWindowTitle(f"Замена {self.title}")
                dialog.setModal(True)
                dialog.setMinimumWidth(500)
                
                layout = QVBoxLayout()
                
                form = QFormLayout()
                
                mileage = QSpinBox()
                mileage.setRange(service.current_mileage, 9999999)
                mileage.setValue(service.current_mileage)
                mileage.setSuffix(" км")
                form.addRow("Пробег:", mileage)
                
                date_edit = DateEdit()
                date_edit.setDate(QDate.currentDate())
                form.addRow("Дата:", date_edit)
                
                org_type = None
                if self.service_type == 'maintenance':
                    org_type = 'service'
                elif self.service_type == 'clutch' or self.service_type == 'brakes':
                    org_type = 'service'
                
                org_combo = OrganizationComboBox(self.parent.org_manager, org_type)
                org_combo.setCurrentText(service.org_name)
                form.addRow("Организация:", org_combo)
                
                notes = QLineEdit()
                notes.setPlaceholderText("Примечания (необязательно)")
                form.addRow("Примечания:", notes)
                
                layout.addLayout(form)
                
                buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)
                
                dialog.setLayout(layout)
                
                if dialog.exec_() == QDialog.Accepted:
                    org = org_combo.get_org()
                    service.service_done(
                        mileage.value(),
                        date_edit.date().toString("yyyy-MM-dd"),
                        notes.text(),
                        org
                    )
                    self.parent.save_data()
                    self.parent.update_all_tables()
                    self.parent.status_label.setText(f"✓ {plate}: замена зарегистрирована")
    
    def show_history(self):
        plate = self.get_selected_car()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите автомобиль!")
            return
        
        if plate in self.parent.cars:
            car = self.parent.cars[plate]
            service = car.get_service(self.service_type)
            
            if service and service.history:
                dialog = QDialog(self)
                dialog.setWindowTitle(f"История замен {self.title} - {plate}")
                dialog.setModal(True)
                dialog.resize(800, 400)
                
                layout = QVBoxLayout()
                
                table = QTableWidget()
                table.setColumnCount(5)
                table.setHorizontalHeaderLabels(["Дата", "Пробег", "Организация", "Примечания", "Дней до след."])
                table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
                table.setAlternatingRowColors(True)
                table.setEditTriggers(QTableWidget.NoEditTriggers)
                
                table.setRowCount(len(service.history))
                for row, event in enumerate(service.history):
                    date_item = QTableWidgetItem(event['date'])
                    date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
                    table.setItem(row, 0, date_item)
                    
                    mileage_item = QTableWidgetItem(f"{event['mileage']} км")
                    mileage_item.setFlags(mileage_item.flags() & ~Qt.ItemIsEditable)
                    table.setItem(row, 1, mileage_item)
                    
                    org_item = QTableWidgetItem(event.get('org', ''))
                    org_item.setFlags(org_item.flags() & ~Qt.ItemIsEditable)
                    table.setItem(row, 2, org_item)
                    
                    notes_item = QTableWidgetItem(event.get('notes', ''))
                    notes_item.setFlags(notes_item.flags() & ~Qt.ItemIsEditable)
                    table.setItem(row, 3, notes_item)
                    
                    days_item = QTableWidgetItem("-")
                    days_item.setFlags(days_item.flags() & ~Qt.ItemIsEditable)
                    table.setItem(row, 4, days_item)
                
                layout.addWidget(table)
                
                close_btn = QPushButton("Закрыть")
                close_btn.clicked.connect(dialog.accept)
                layout.addWidget(close_btn)
                
                dialog.setLayout(layout)
                dialog.exec_()
            else:
                QMessageBox.information(self, "Информация", "История пуста")
    
    def add_document(self):
        plate = self.get_selected_car()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите автомобиль!")
            return
        
        if plate in self.parent.cars:
            car = self.parent.cars[plate]
            service = car.get_service(self.service_type)
            
            if service:
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "Выберите файл", DOCS_DIR, 
                    "Все файлы (*.*);;PDF файлы (*.pdf);;Изображения (*.png *.jpg *.jpeg)"
                )
                if file_path:
                    description, ok = QInputDialog.getText(
                        self, "Описание", "Введите описание документа:"
                    )
                    if ok:
                        try:
                            service.add_document(file_path, description)
                            self.parent.save_data()
                            self.parent.update_all_tables()
                            QMessageBox.information(self, "Успех", "Документ прикреплен!")
                        except Exception as e:
                            QMessageBox.critical(self, "Ошибка", f"Не удалось прикрепить документ:\n{str(e)}")


class TachographTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        top_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Добавить тахограф")
        self.add_btn.clicked.connect(self.add_tachograph)
        self.add_btn.setFixedHeight(35)
        top_layout.addWidget(self.add_btn)
        
        self.calibrate_btn = QPushButton("🔧 Калибровка")
        self.calibrate_btn.clicked.connect(self.add_calibration)
        self.calibrate_btn.setFixedHeight(35)
        top_layout.addWidget(self.calibrate_btn)
        
        self.history_btn = QPushButton("📜 История")
        self.history_btn.clicked.connect(self.show_history)
        self.history_btn.setFixedHeight(35)
        top_layout.addWidget(self.history_btn)
        
        self.doc_btn = QPushButton("📎 Прикрепить документ")
        self.doc_btn.clicked.connect(self.add_document)
        self.doc_btn.setFixedHeight(35)
        top_layout.addWidget(self.doc_btn)
        
        self.delete_btn = QPushButton("❌ Удалить")
        self.delete_btn.clicked.connect(self.delete_tachograph)
        self.delete_btn.setFixedHeight(35)
        top_layout.addWidget(self.delete_btn)
        
        top_layout.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск по номеру...")
        self.search_input.textChanged.connect(self.filter_table)
        self.search_input.setFixedHeight(35)
        self.search_input.setFixedWidth(200)
        top_layout.addWidget(self.search_input)
        
        layout.addLayout(top_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Госномер", "Номер прибора", "Дата калибровки",
            "Действителен до", "Дней осталось", "Организация",
            "Стоимость", "Статус", "Документы"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 9):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.table.itemDoubleClicked.connect(self.show_car_history)
        
        layout.addWidget(self.table)
    
    def get_selected(self):
        row = self.table.currentRow()
        if row >= 0:
            plate = self.table.item(row, 0).text()
            device = self.table.item(row, 1).text()
            return plate, device
        return None, None
    
    def filter_table(self):
        search_text = self.search_input.text().lower()
        
        for row in range(self.table.rowCount()):
            plate_item = self.table.item(row, 0)
            if plate_item:
                match = search_text in plate_item.text().lower()
                self.table.setRowHidden(row, not match)
    
    def show_car_history(self, item):
        row = item.row()
        plate = self.table.item(row, 0).text()
        if plate in self.parent.cars:
            dialog = CarHistoryDialog(self.parent.cars[plate], self.parent.org_manager, self.parent.fuel_manager, self)
            dialog.exec_()
    
    def add_tachograph(self):
        plates = list(self.parent.cars.keys())
        if not plates:
            QMessageBox.warning(self, "Ошибка", "Сначала добавьте автомобиль!")
            return
        
        plate, ok = QInputDialog.getItem(
            self, "Выберите автомобиль", 
            "Автомобиль:", plates, 0, False
        )
        
        if ok and plate:
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Добавить тахограф для {plate}")
            dialog.setModal(True)
            dialog.setMinimumWidth(500)
            
            layout = QVBoxLayout()
            
            form = QFormLayout()
            
            device = QLineEdit()
            device.setPlaceholderText("Номер прибора")
            form.addRow("Номер прибора:", device)
            
            calib_date = DateEdit()
            calib_date.setDate(QDate.currentDate())
            form.addRow("Дата калибровки:", calib_date)
            
            expiry_date = DateEdit()
            expiry_date.setDate(QDate.currentDate().addYears(2))
            form.addRow("Действителен до:", expiry_date)
            
            org_combo = OrganizationComboBox(self.parent.org_manager, 'tachograph')
            form.addRow("Организация:", org_combo)
            
            cost = QDoubleSpinBox()
            cost.setRange(0, 1000000)
            cost.setSuffix(" ₽")
            cost.setValue(0)
            form.addRow("Стоимость:", cost)
            
            layout.addLayout(form)
            
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            dialog.setLayout(layout)
            
            if dialog.exec_() == QDialog.Accepted:
                tach = TachographItem(
                    plate,
                    device.text(),
                    calib_date.date().toString("yyyy-MM-dd"),
                    expiry_date.date().toString("yyyy-MM-dd"),
                    cost.value(),
                    org_combo.get_org()
                )
                self.parent.cars[plate].add_tachograph(tach)
                self.parent.save_data()
                self.parent.update_all_tables()
                self.parent.status_label.setText(f"✓ Тахограф добавлен для {plate}")
    
    def add_calibration(self):
        plate, device = self.get_selected()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите тахограф!")
            return
        
        car = self.parent.cars[plate]
        for tach in car.tachographs:
            if tach.device_number == device:
                dialog = QDialog(self)
                dialog.setWindowTitle(f"Калибровка тахографа {device}")
                dialog.setModal(True)
                dialog.setMinimumWidth(500)
                
                layout = QVBoxLayout()
                
                form = QFormLayout()
                
                calib_date = DateEdit()
                calib_date.setDate(QDate.currentDate())
                form.addRow("Дата калибровки:", calib_date)
                
                expiry_date = DateEdit()
                expiry_date.setDate(QDate.currentDate().addYears(2))
                form.addRow("Действителен до:", expiry_date)
                
                org_combo = OrganizationComboBox(self.parent.org_manager, 'tachograph')
                org_combo.setCurrentText(tach.company_name)
                form.addRow("Организация:", org_combo)
                
                cost = QDoubleSpinBox()
                cost.setRange(0, 1000000)
                cost.setSuffix(" ₽")
                cost.setValue(tach.cost)
                form.addRow("Стоимость:", cost)
                
                layout.addLayout(form)
                
                buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
                buttons.accepted.connect(dialog.accept)
                buttons.rejected.connect(dialog.reject)
                layout.addWidget(buttons)
                
                dialog.setLayout(layout)
                
                if dialog.exec_() == QDialog.Accepted:
                    tach.add_calibration(
                        calib_date.date().toString("yyyy-MM-dd"),
                        expiry_date.date().toString("yyyy-MM-dd"),
                        cost.value(),
                        org_combo.get_org()
                    )
                    self.parent.save_data()
                    self.parent.update_all_tables()
                    self.parent.status_label.setText(f"✓ Калибровка зарегистрирована")
                return
    
    def show_history(self):
        plate, device = self.get_selected()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите тахограф!")
            return
        
        car = self.parent.cars[plate]
        for tach in car.tachographs:
            if tach.device_number == device and tach.history:
                dialog = QDialog(self)
                dialog.setWindowTitle(f"История калибровок - {device}")
                dialog.setModal(True)
                dialog.resize(700, 400)
                
                layout = QVBoxLayout()
                
                table = QTableWidget()
                table.setColumnCount(5)
                table.setHorizontalHeaderLabels([
                    "Дата калибровки", "Действителен до", 
                    "Организация", "Стоимость", "Дней осталось"
                ])
                table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
                table.setAlternatingRowColors(True)
                table.setEditTriggers(QTableWidget.NoEditTriggers)
                
                table.setRowCount(len(tach.history))
                for row, event in enumerate(tach.history):
                    date_item = QTableWidgetItem(event['calibration_date'])
                    date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
                    table.setItem(row, 0, date_item)
                    
                    expiry_item = QTableWidgetItem(event['expiry_date'])
                    expiry_item.setFlags(expiry_item.flags() & ~Qt.ItemIsEditable)
                    table.setItem(row, 1, expiry_item)
                    
                    org_item = QTableWidgetItem(event.get('company', ''))
                    org_item.setFlags(org_item.flags() & ~Qt.ItemIsEditable)
                    table.setItem(row, 2, org_item)
                    
                    cost_item = QTableWidgetItem(f"{event['cost']:,.0f} ₽".replace(",", " "))
                    cost_item.setFlags(cost_item.flags() & ~Qt.ItemIsEditable)
                    cost_item.setTextAlignment(Qt.AlignRight)
                    table.setItem(row, 3, cost_item)
                    
                    try:
                        expiry = date.fromisoformat(event['expiry_date'])
                        today = date.today()
                        days = (expiry - today).days
                        days_item = QTableWidgetItem(str(days))
                        days_item.setFlags(days_item.flags() & ~Qt.ItemIsEditable)
                        if days <= 0:
                            days_item.setForeground(QBrush(QColor(255, 59, 48)))
                        elif days <= 30:
                            days_item.setForeground(QBrush(QColor(255, 159, 10)))
                        days_item.setTextAlignment(Qt.AlignCenter)
                        table.setItem(row, 4, days_item)
                    except:
                        days_item = QTableWidgetItem("-")
                        days_item.setFlags(days_item.flags() & ~Qt.ItemIsEditable)
                        table.setItem(row, 4, days_item)
                
                layout.addWidget(table)
                
                close_btn = QPushButton("Закрыть")
                close_btn.clicked.connect(dialog.accept)
                layout.addWidget(close_btn)
                
                dialog.setLayout(layout)
                dialog.exec_()
                return
        
        QMessageBox.information(self, "Информация", "История пуста")
    
    def add_document(self):
        plate, device = self.get_selected()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите тахограф!")
            return
        
        car = self.parent.cars[plate]
        for tach in car.tachographs:
            if tach.device_number == device:
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "Выберите файл", DOCS_DIR, 
                    "Все файлы (*.*);;PDF файлы (*.pdf);;Изображения (*.png *.jpg *.jpeg)"
                )
                if file_path:
                    description, ok = QInputDialog.getText(
                        self, "Описание", "Введите описание документа:"
                    )
                    if ok:
                        try:
                            tach.add_document(file_path, description)
                            self.parent.save_data()
                            self.parent.update_all_tables()
                            QMessageBox.information(self, "Успех", "Документ прикреплен!")
                        except Exception as e:
                            QMessageBox.critical(self, "Ошибка", f"Не удалось прикрепить документ:\n{str(e)}")
                return
    
    def delete_tachograph(self):
        plate, device = self.get_selected()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите тахограф!")
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить тахограф {device} для {plate}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            car = self.parent.cars[plate]
            car.tachographs = [t for t in car.tachographs if t.device_number != device]
            self.parent.save_data()
            self.parent.update_all_tables()
            self.parent.status_label.setText(f"✓ Тахограф удален")


class PermitTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        top_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Добавить пропуск в Москву")
        self.add_btn.clicked.connect(self.add_permit)
        self.add_btn.setFixedHeight(35)
        top_layout.addWidget(self.add_btn)
        
        self.history_btn = QPushButton("📜 История")
        self.history_btn.clicked.connect(self.show_history)
        self.history_btn.setFixedHeight(35)
        top_layout.addWidget(self.history_btn)
        
        self.doc_btn = QPushButton("📎 Прикрепить документ")
        self.doc_btn.clicked.connect(self.add_document)
        self.doc_btn.setFixedHeight(35)
        top_layout.addWidget(self.doc_btn)
        
        self.delete_btn = QPushButton("❌ Удалить")
        self.delete_btn.clicked.connect(self.delete_permit)
        self.delete_btn.setFixedHeight(35)
        top_layout.addWidget(self.delete_btn)
        
        top_layout.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск по номеру...")
        self.search_input.textChanged.connect(self.filter_table)
        self.search_input.setFixedHeight(35)
        self.search_input.setFixedWidth(200)
        top_layout.addWidget(self.search_input)
        
        layout.addLayout(top_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Госномер", "Номер пропуска", "Зона",
            "Дата начала", "Дата окончания", "Дней осталось",
            "Стоимость", "Документы"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 8):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.table.itemDoubleClicked.connect(self.show_car_history)
        
        layout.addWidget(self.table)
    
    def get_selected(self):
        row = self.table.currentRow()
        if row >= 0:
            plate = self.table.item(row, 0).text()
            number = self.table.item(row, 1).text()
            return plate, number
        return None, None
    
    def filter_table(self):
        search_text = self.search_input.text().lower()
        
        for row in range(self.table.rowCount()):
            plate_item = self.table.item(row, 0)
            if plate_item:
                match = search_text in plate_item.text().lower()
                self.table.setRowHidden(row, not match)
    
    def show_car_history(self, item):
        row = item.row()
        plate = self.table.item(row, 0).text()
        if plate in self.parent.cars:
            dialog = CarHistoryDialog(self.parent.cars[plate], self.parent.org_manager, self.parent.fuel_manager, self)
            dialog.exec_()
    
    def add_permit(self):
        plates = list(self.parent.cars.keys())
        if not plates:
            QMessageBox.warning(self, "Ошибка", "Сначала добавьте автомобиль!")
            return
        
        plate, ok = QInputDialog.getItem(
            self, "Выберите автомобиль", 
            "Автомобиль:", plates, 0, False
        )
        
        if ok and plate:
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Добавить пропуск в Москву для {plate}")
            dialog.setModal(True)
            dialog.setMinimumWidth(450)
            
            layout = QVBoxLayout()
            
            form = QFormLayout()
            
            number = QLineEdit()
            number.setPlaceholderText("Номер пропуска")
            form.addRow("Номер пропуска:", number)
            
            zone = QLineEdit()
            zone.setPlaceholderText("Зона действия (ТТК, МКАД и т.д.)")
            form.addRow("Зона действия:", zone)
            
            start_date = DateEdit()
            start_date.setDate(QDate.currentDate())
            form.addRow("Дата начала:", start_date)
            
            end_date = DateEdit()
            end_date.setDate(QDate.currentDate().addMonths(6))
            form.addRow("Дата окончания:", end_date)
            
            cost = QDoubleSpinBox()
            cost.setRange(0, 1000000)
            cost.setSuffix(" ₽")
            cost.setValue(0)
            form.addRow("Стоимость:", cost)
            
            layout.addLayout(form)
            
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            dialog.setLayout(layout)
            
            if dialog.exec_() == QDialog.Accepted:
                permit = PermitItem(
                    plate,
                    number.text(),
                    start_date.date().toString("yyyy-MM-dd"),
                    end_date.date().toString("yyyy-MM-dd"),
                    cost.value(),
                    zone.text()
                )
                self.parent.cars[plate].add_permit(permit)
                self.parent.save_data()
                self.parent.update_all_tables()
                self.parent.status_label.setText(f"✓ Пропуск добавлен для {plate}")
    
    def show_history(self):
        plate, number = self.get_selected()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите пропуск!")
            return
        
        car = self.parent.cars[plate]
        dialog = QDialog(self)
        dialog.setWindowTitle(f"История пропусков - {plate}")
        dialog.setModal(True)
        dialog.resize(700, 400)
        
        layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setColumnCount(5)
        table.setHorizontalHeaderLabels([
            "Номер", "Зона", "Дата начала", "Дата окончания", "Стоимость"
        ])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        table.setRowCount(len(car.permits))
        for row, permit in enumerate(car.permits):
            num_item = QTableWidgetItem(permit.permit_number)
            num_item.setFlags(num_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 0, num_item)
            
            zone_item = QTableWidgetItem(permit.zone)
            zone_item.setFlags(zone_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 1, zone_item)
            
            start_item = QTableWidgetItem(permit.start_date)
            start_item.setFlags(start_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 2, start_item)
            
            end_item = QTableWidgetItem(permit.end_date)
            end_item.setFlags(end_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 3, end_item)
            
            cost_item = QTableWidgetItem(f"{permit.cost:,.0f} ₽".replace(",", " "))
            cost_item.setFlags(cost_item.flags() & ~Qt.ItemIsEditable)
            cost_item.setTextAlignment(Qt.AlignRight)
            table.setItem(row, 4, cost_item)
        
        layout.addWidget(table)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def add_document(self):
        plate, number = self.get_selected()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите пропуск!")
            return
        
        car = self.parent.cars[plate]
        for permit in car.permits:
            if permit.permit_number == number:
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "Выберите файл", DOCS_DIR, 
                    "Все файлы (*.*);;PDF файлы (*.pdf);;Изображения (*.png *.jpg *.jpeg)"
                )
                if file_path:
                    description, ok = QInputDialog.getText(
                        self, "Описание", "Введите описание документа:"
                    )
                    if ok:
                        try:
                            permit.add_document(file_path, description)
                            self.parent.save_data()
                            self.parent.update_all_tables()
                            QMessageBox.information(self, "Успех", "Документ прикреплен!")
                        except Exception as e:
                            QMessageBox.critical(self, "Ошибка", f"Не удалось прикрепить документ:\n{str(e)}")
                return
    
    def delete_permit(self):
        plate, number = self.get_selected()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите пропуск!")
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить пропуск {number} для {plate}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            car = self.parent.cars[plate]
            car.permits = [p for p in car.permits if p.permit_number != number]
            self.parent.save_data()
            self.parent.update_all_tables()
            self.parent.status_label.setText(f"✓ Пропуск удален")


class InsuranceTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        top_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Добавить страховку")
        self.add_btn.clicked.connect(self.add_insurance)
        self.add_btn.setFixedHeight(35)
        top_layout.addWidget(self.add_btn)
        
        self.history_btn = QPushButton("📜 История")
        self.history_btn.clicked.connect(self.show_history)
        self.history_btn.setFixedHeight(35)
        top_layout.addWidget(self.history_btn)
        
        self.doc_btn = QPushButton("📎 Прикрепить документ")
        self.doc_btn.clicked.connect(self.add_document)
        self.doc_btn.setFixedHeight(35)
        top_layout.addWidget(self.doc_btn)
        
        self.delete_btn = QPushButton("❌ Удалить")
        self.delete_btn.clicked.connect(self.delete_insurance)
        self.delete_btn.setFixedHeight(35)
        top_layout.addWidget(self.delete_btn)
        
        top_layout.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск по номеру или компании...")
        self.search_input.textChanged.connect(self.filter_table)
        self.search_input.setFixedHeight(35)
        self.search_input.setFixedWidth(250)
        top_layout.addWidget(self.search_input)
        
        layout.addLayout(top_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Госномер", "Компания", "Номер полиса",
            "Дата начала", "Дата окончания", "Дней осталось",
            "Стоимость", "Статус", "Документы"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        for i in range(2, 9):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.table.itemDoubleClicked.connect(self.show_car_history)
        
        layout.addWidget(self.table)
    
    def get_selected(self):
        row = self.table.currentRow()
        if row >= 0:
            plate = self.table.item(row, 0).text()
            company = self.table.item(row, 1).text()
            return plate, company
        return None, None
    
    def filter_table(self):
        search_text = self.search_input.text().lower()
        
        for row in range(self.table.rowCount()):
            plate_item = self.table.item(row, 0)
            company_item = self.table.item(row, 1)
            if plate_item and company_item:
                match = (search_text in plate_item.text().lower() or 
                        search_text in company_item.text().lower())
                self.table.setRowHidden(row, not match)
    
    def show_car_history(self, item):
        row = item.row()
        plate = self.table.item(row, 0).text()
        if plate in self.parent.cars:
            dialog = CarHistoryDialog(self.parent.cars[plate], self.parent.org_manager, self.parent.fuel_manager, self)
            dialog.exec_()
    
    def add_insurance(self):
        plates = list(self.parent.cars.keys())
        if not plates:
            QMessageBox.warning(self, "Ошибка", "Сначала добавьте автомобиль!")
            return
        
        plate, ok = QInputDialog.getItem(
            self, "Выберите автомобиль", 
            "Автомобиль:", plates, 0, False
        )
        
        if ok and plate:
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Добавить страховку для {plate}")
            dialog.setModal(True)
            dialog.setMinimumWidth(500)
            
            layout = QVBoxLayout()
            
            form = QFormLayout()
            
            company = OrganizationComboBox(self.parent.org_manager, 'insurance')
            company.setEditable(True)
            form.addRow("Компания:", company)
            
            policy = QLineEdit()
            policy.setPlaceholderText("Номер полиса")
            form.addRow("Номер полиса:", policy)
            
            start_date = DateEdit()
            start_date.setDate(QDate.currentDate())
            form.addRow("Дата начала:", start_date)
            
            end_date = DateEdit()
            end_date.setDate(QDate.currentDate().addYears(1))
            form.addRow("Дата окончания:", end_date)
            
            cost = QDoubleSpinBox()
            cost.setRange(0, 1000000)
            cost.setSuffix(" ₽")
            cost.setValue(0)
            form.addRow("Стоимость:", cost)
            
            layout.addLayout(form)
            
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            dialog.setLayout(layout)
            
            if dialog.exec_() == QDialog.Accepted:
                insurance = InsuranceItem(
                    plate,
                    company.get_org(),
                    policy.text(),
                    start_date.date().toString("yyyy-MM-dd"),
                    end_date.date().toString("yyyy-MM-dd"),
                    cost.value()
                )
                self.parent.cars[plate].add_insurance(insurance)
                self.parent.save_data()
                self.parent.update_all_tables()
                self.parent.status_label.setText(f"✓ Страховка добавлена для {plate}")
    
    def show_history(self):
        plate, company = self.get_selected()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите страховку!")
            return
        
        car = self.parent.cars[plate]
        dialog = QDialog(self)
        dialog.setWindowTitle(f"История страховок - {plate}")
        dialog.setModal(True)
        dialog.resize(700, 400)
        
        layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Компания", "Номер полиса", "Дата начала", 
            "Дата окончания", "Дней осталось", "Стоимость"
        ])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        table.setRowCount(len(car.insurances))
        for row, ins in enumerate(car.insurances):
            days = ins.days_until_expiry()
            
            company_item = QTableWidgetItem(ins.company_name)
            company_item.setFlags(company_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 0, company_item)
            
            policy_item = QTableWidgetItem(ins.policy_number)
            policy_item.setFlags(policy_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 1, policy_item)
            
            start_item = QTableWidgetItem(ins.start_date)
            start_item.setFlags(start_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 2, start_item)
            
            end_item = QTableWidgetItem(ins.end_date)
            end_item.setFlags(end_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 3, end_item)
            
            days_item = QTableWidgetItem(str(days))
            days_item.setFlags(days_item.flags() & ~Qt.ItemIsEditable)
            if days <= 0:
                days_item.setForeground(QBrush(QColor(255, 59, 48)))
            elif days <= 30:
                days_item.setForeground(QBrush(QColor(255, 159, 10)))
            days_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 4, days_item)
            
            cost_item = QTableWidgetItem(f"{ins.cost:,.0f} ₽".replace(",", " "))
            cost_item.setFlags(cost_item.flags() & ~Qt.ItemIsEditable)
            cost_item.setTextAlignment(Qt.AlignRight)
            table.setItem(row, 5, cost_item)
        
        layout.addWidget(table)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def add_document(self):
        plate, company = self.get_selected()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите страховку!")
            return
        
        car = self.parent.cars[plate]
        for ins in car.insurances:
            if ins.company_name == company:
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "Выберите файл", DOCS_DIR, 
                    "Все файлы (*.*);;PDF файлы (*.pdf);;Изображения (*.png *.jpg *.jpeg)"
                )
                if file_path:
                    description, ok = QInputDialog.getText(
                        self, "Описание", "Введите описание документа:"
                    )
                    if ok:
                        try:
                            ins.add_document(file_path, description)
                            self.parent.save_data()
                            self.parent.update_all_tables()
                            QMessageBox.information(self, "Успех", "Документ прикреплен!")
                        except Exception as e:
                            QMessageBox.critical(self, "Ошибка", f"Не удалось прикрепить документ:\n{str(e)}")
                return
    
    def delete_insurance(self):
        plate, company = self.get_selected()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите страховку!")
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить страховку {company} для {plate}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            car = self.parent.cars[plate]
            car.insurances = [i for i in car.insurances if i.company_name != company]
            self.parent.save_data()
            self.parent.update_all_tables()
            self.parent.status_label.setText(f"✓ Страховка удалена")


class DiagnosticTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        top_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Добавить диагностическую карту")
        self.add_btn.clicked.connect(self.add_card)
        self.add_btn.setFixedHeight(35)
        top_layout.addWidget(self.add_btn)
        
        self.history_btn = QPushButton("📜 История")
        self.history_btn.clicked.connect(self.show_history)
        self.history_btn.setFixedHeight(35)
        top_layout.addWidget(self.history_btn)
        
        self.doc_btn = QPushButton("📎 Прикрепить документ")
        self.doc_btn.clicked.connect(self.add_document)
        self.doc_btn.setFixedHeight(35)
        top_layout.addWidget(self.doc_btn)
        
        self.delete_btn = QPushButton("❌ Удалить")
        self.delete_btn.clicked.connect(self.delete_card)
        self.delete_btn.setFixedHeight(35)
        top_layout.addWidget(self.delete_btn)
        
        top_layout.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск по номеру или станции...")
        self.search_input.textChanged.connect(self.filter_table)
        self.search_input.setFixedHeight(35)
        self.search_input.setFixedWidth(250)
        top_layout.addWidget(self.search_input)
        
        layout.addLayout(top_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "Госномер", "Станция", "Номер карты",
            "Дата выдачи", "Действительна до", "Дней осталось",
            "Стоимость", "Статус", "Документы"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        for i in range(2, 9):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.table.itemDoubleClicked.connect(self.show_car_history)
        
        layout.addWidget(self.table)
    
    def get_selected(self):
        row = self.table.currentRow()
        if row >= 0:
            plate = self.table.item(row, 0).text()
            station = self.table.item(row, 1).text()
            return plate, station
        return None, None
    
    def filter_table(self):
        search_text = self.search_input.text().lower()
        
        for row in range(self.table.rowCount()):
            plate_item = self.table.item(row, 0)
            station_item = self.table.item(row, 1)
            if plate_item and station_item:
                match = (search_text in plate_item.text().lower() or 
                        search_text in station_item.text().lower())
                self.table.setRowHidden(row, not match)
    
    def show_car_history(self, item):
        row = item.row()
        plate = self.table.item(row, 0).text()
        if plate in self.parent.cars:
            dialog = CarHistoryDialog(self.parent.cars[plate], self.parent.org_manager, self.parent.fuel_manager, self)
            dialog.exec_()
    
    def add_card(self):
        plates = list(self.parent.cars.keys())
        if not plates:
            QMessageBox.warning(self, "Ошибка", "Сначала добавьте автомобиль!")
            return
        
        plate, ok = QInputDialog.getItem(
            self, "Выберите автомобиль", 
            "Автомобиль:", plates, 0, False
        )
        
        if ok and plate:
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Добавить диагностическую карту для {plate}")
            dialog.setModal(True)
            dialog.setMinimumWidth(500)
            
            layout = QVBoxLayout()
            
            form = QFormLayout()
            
            station = OrganizationComboBox(self.parent.org_manager, 'diagnostic')
            station.setEditable(True)
            form.addRow("Станция:", station)
            
            card_number = QLineEdit()
            card_number.setPlaceholderText("Номер карты")
            form.addRow("Номер карты:", card_number)
            
            issue_date = DateEdit()
            issue_date.setDate(QDate.currentDate())
            form.addRow("Дата выдачи:", issue_date)
            
            expiry_date = DateEdit()
            expiry_date.setDate(QDate.currentDate().addYears(1))
            form.addRow("Действительна до:", expiry_date)
            
            cost = QDoubleSpinBox()
            cost.setRange(0, 1000000)
            cost.setSuffix(" ₽")
            cost.setValue(0)
            form.addRow("Стоимость:", cost)
            
            layout.addLayout(form)
            
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            dialog.setLayout(layout)
            
            if dialog.exec_() == QDialog.Accepted:
                card = DiagnosticCard(
                    plate,
                    station.get_org(),
                    card_number.text(),
                    issue_date.date().toString("yyyy-MM-dd"),
                    expiry_date.date().toString("yyyy-MM-dd"),
                    cost.value()
                )
                self.parent.cars[plate].add_diagnostic_card(card)
                self.parent.save_data()
                self.parent.update_all_tables()
                self.parent.status_label.setText(f"✓ Диагностическая карта добавлена для {plate}")
    
    def show_history(self):
        plate, station = self.get_selected()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите диагностическую карту!")
            return
        
        car = self.parent.cars[plate]
        dialog = QDialog(self)
        dialog.setWindowTitle(f"История диагностических карт - {plate}")
        dialog.setModal(True)
        dialog.resize(700, 400)
        
        layout = QVBoxLayout()
        
        table = QTableWidget()
        table.setColumnCount(6)
        table.setHorizontalHeaderLabels([
            "Станция", "Номер карты", "Дата выдачи", 
            "Действительна до", "Дней осталось", "Стоимость"
        ])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.setAlternatingRowColors(True)
        table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        table.setRowCount(len(car.diagnostic_cards))
        for row, card in enumerate(car.diagnostic_cards):
            days = card.days_until_expiry()
            
            station_item = QTableWidgetItem(card.station_name)
            station_item.setFlags(station_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 0, station_item)
            
            card_item = QTableWidgetItem(card.card_number)
            card_item.setFlags(card_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 1, card_item)
            
            issue_item = QTableWidgetItem(card.issue_date)
            issue_item.setFlags(issue_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 2, issue_item)
            
            expiry_item = QTableWidgetItem(card.expiry_date)
            expiry_item.setFlags(expiry_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(row, 3, expiry_item)
            
            days_item = QTableWidgetItem(str(days))
            days_item.setFlags(days_item.flags() & ~Qt.ItemIsEditable)
            if days <= 0:
                days_item.setForeground(QBrush(QColor(255, 59, 48)))
            elif days <= 30:
                days_item.setForeground(QBrush(QColor(255, 159, 10)))
            days_item.setTextAlignment(Qt.AlignCenter)
            table.setItem(row, 4, days_item)
            
            cost_item = QTableWidgetItem(f"{card.cost:,.0f} ₽".replace(",", " "))
            cost_item.setFlags(cost_item.flags() & ~Qt.ItemIsEditable)
            cost_item.setTextAlignment(Qt.AlignRight)
            table.setItem(row, 5, cost_item)
        
        layout.addWidget(table)
        
        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def add_document(self):
        plate, station = self.get_selected()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите диагностическую карту!")
            return
        
        car = self.parent.cars[plate]
        for card in car.diagnostic_cards:
            if card.station_name == station:
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "Выберите файл", DOCS_DIR, 
                    "Все файлы (*.*);;PDF файлы (*.pdf);;Изображения (*.png *.jpg *.jpeg)"
                )
                if file_path:
                    description, ok = QInputDialog.getText(
                        self, "Описание", "Введите описание документа:"
                    )
                    if ok:
                        try:
                            card.add_document(file_path, description)
                            self.parent.save_data()
                            self.parent.update_all_tables()
                            QMessageBox.information(self, "Успех", "Документ прикреплен!")
                        except Exception as e:
                            QMessageBox.critical(self, "Ошибка", f"Не удалось прикрепить документ:\n{str(e)}")
                return
    
    def delete_card(self):
        plate, station = self.get_selected()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите диагностическую карту!")
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить диагностическую карту от {station} для {plate}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            car = self.parent.cars[plate]
            car.diagnostic_cards = [c for c in car.diagnostic_cards if c.station_name != station]
            self.parent.save_data()
            self.parent.update_all_tables()
            self.parent.status_label.setText(f"✓ Диагностическая карта удалена")


class RepairsTab(QWidget):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        top_layout = QHBoxLayout()
        
        self.add_btn = QPushButton("➕ Добавить ремонт")
        self.add_btn.clicked.connect(self.add_repair)
        self.add_btn.setFixedHeight(35)
        top_layout.addWidget(self.add_btn)
        
        self.doc_btn = QPushButton("📎 Прикрепить документ")
        self.doc_btn.clicked.connect(self.add_document)
        self.doc_btn.setFixedHeight(35)
        top_layout.addWidget(self.doc_btn)
        
        self.view_docs_btn = QPushButton("📂 Документы")
        self.view_docs_btn.clicked.connect(self.view_documents)
        self.view_docs_btn.setFixedHeight(35)
        top_layout.addWidget(self.view_docs_btn)
        
        self.delete_btn = QPushButton("❌ Удалить")
        self.delete_btn.clicked.connect(self.delete_repair)
        self.delete_btn.setFixedHeight(35)
        top_layout.addWidget(self.delete_btn)
        
        top_layout.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Поиск по номеру или описанию...")
        self.search_input.textChanged.connect(self.filter_table)
        self.search_input.setFixedHeight(35)
        self.search_input.setFixedWidth(250)
        top_layout.addWidget(self.search_input)
        
        self.total_cost_label = QLabel("Общие расходы: 0 ₽")
        self.total_cost_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }")
        self.total_cost_label.setFixedHeight(35)
        top_layout.addWidget(self.total_cost_label)
        
        layout.addLayout(top_layout)
        
        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels([
            "Госномер", "Дата", "Пробег", "Организация",
            "Описание", "Стоимость", "Статус", "Документы"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.Stretch)
        for i in range(1, 8):
            if i != 4:
                self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        
        self.table.itemDoubleClicked.connect(self.show_car_history)
        
        layout.addWidget(self.table)
    
    def get_selected(self):
        row = self.table.currentRow()
        if row >= 0:
            plate = self.table.item(row, 0).text()
            date = self.table.item(row, 1).text()
            desc = self.table.item(row, 4).text()
            return plate, date, desc
        return None, None, None
    
    def filter_table(self):
        search_text = self.search_input.text().lower()
        
        for row in range(self.table.rowCount()):
            plate_item = self.table.item(row, 0)
            desc_item = self.table.item(row, 4)
            if plate_item and desc_item:
                match = (search_text in plate_item.text().lower() or 
                        search_text in desc_item.text().lower())
                self.table.setRowHidden(row, not match)
    
    def show_car_history(self, item):
        row = item.row()
        plate = self.table.item(row, 0).text()
        if plate in self.parent.cars:
            dialog = CarHistoryDialog(self.parent.cars[plate], self.parent.org_manager, self.parent.fuel_manager, self)
            dialog.exec_()
    
    def add_repair(self):
        plates = list(self.parent.cars.keys())
        if not plates:
            QMessageBox.warning(self, "Ошибка", "Сначала добавьте автомобиль!")
            return
        
        plate, ok = QInputDialog.getItem(
            self, "Выберите автомобиль", 
            "Автомобиль:", plates, 0, False
        )
        
        if ok and plate:
            car = self.parent.cars[plate]
            current_mileage = car.get_current_mileage()
            
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Добавить ремонт для {plate}")
            dialog.setModal(True)
            dialog.setMinimumWidth(500)
            
            layout = QVBoxLayout()
            
            form = QFormLayout()
            
            date_edit = DateEdit()
            date_edit.setDate(QDate.currentDate())
            form.addRow("Дата:", date_edit)
            
            mileage = QSpinBox()
            mileage.setRange(0, 9999999)
            mileage.setValue(current_mileage)
            mileage.setSuffix(" км")
            form.addRow("Пробег:", mileage)
            
            org_combo = OrganizationComboBox(self.parent.org_manager, 'service')
            form.addRow("Организация:", org_combo)
            
            description = QTextEdit()
            description.setPlaceholderText("Описание выполненных работ")
            description.setMaximumHeight(100)
            form.addRow("Описание:", description)
            
            cost = QDoubleSpinBox()
            cost.setRange(0, 1000000)
            cost.setSuffix(" ₽")
            cost.setValue(0)
            form.addRow("Стоимость:", cost)
            
            layout.addLayout(form)
            
            buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            layout.addWidget(buttons)
            
            dialog.setLayout(layout)
            
            if dialog.exec_() == QDialog.Accepted:
                repair = RepairItem(
                    plate,
                    date_edit.date().toString("yyyy-MM-dd"),
                    mileage.value(),
                    description.toPlainText(),
                    cost.value(),
                    org_combo.get_org()
                )
                self.parent.cars[plate].add_repair(repair)
                self.parent.save_data()
                self.parent.update_all_tables()
                self.parent.status_label.setText(f"✓ Ремонт добавлен для {plate}")
    
    def add_document(self):
        plate, date, desc = self.get_selected()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите ремонт!")
            return
        
        car = self.parent.cars[plate]
        for repair in car.repairs:
            if repair.date_performed == date and repair.description == desc:
                file_path, _ = QFileDialog.getOpenFileName(
                    self, "Выберите файл", DOCS_DIR, 
                    "Все файлы (*.*);;PDF файлы (*.pdf);;Изображения (*.png *.jpg *.jpeg)"
                )
                if file_path:
                    description, ok = QInputDialog.getText(
                        self, "Описание", "Введите описание документа:"
                    )
                    if ok:
                        try:
                            repair.add_document(file_path, description)
                            self.parent.save_data()
                            self.parent.update_all_tables()
                            QMessageBox.information(self, "Успех", "Документ прикреплен!")
                        except Exception as e:
                            QMessageBox.critical(self, "Ошибка", f"Не удалось прикрепить документ:\n{str(e)}")
                return
    
    def view_documents(self):
        plate, date, desc = self.get_selected()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите ремонт!")
            return
        
        car = self.parent.cars[plate]
        for repair in car.repairs:
            if repair.date_performed == date and repair.description == desc and repair.documents:
                items = [f"{d.description} ({os.path.basename(d.file_path)})" for d in repair.documents]
                item, ok = QInputDialog.getItem(
                    self, "Выберите документ", 
                    "Документы:", items, 0, False
                )
                if ok and item:
                    idx = items.index(item)
                    if os.path.exists(repair.documents[idx].file_path):
                        QDesktopServices.openUrl(QUrl.fromLocalFile(repair.documents[idx].file_path))
                    else:
                        QMessageBox.warning(self, "Ошибка", "Файл не найден!")
                return
        
        QMessageBox.information(self, "Информация", "Нет прикрепленных документов")
    
    def delete_repair(self):
        plate, date, desc = self.get_selected()
        if not plate:
            QMessageBox.warning(self, "Ошибка", "Выберите ремонт!")
            return
        
        reply = QMessageBox.question(
            self, "Подтверждение",
            f"Удалить запись о ремонте от {date}?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            car = self.parent.cars[plate]
            car.repairs = [r for r in car.repairs 
                          if not (r.date_performed == date and r.description == desc)]
            self.parent.save_data()
            self.parent.update_all_tables()
            self.parent.status_label.setText(f"✓ Ремонт удален")
    
    def update_total_cost(self):
        total = 0
        for car in self.parent.cars.values():
            for repair in car.repairs:
                total += repair.cost
        self.total_cost_label.setText(f"Общие расходы: {total:,.0f} ₽".replace(",", " "))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.cars = {}
        self.org_manager = Organizations()
        self.fuel_manager = FuelManager()
        self.load_data()
        self.init_ui()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.check_all)
        self.timer.start(1800000)  # 30 минут
        
        QTimer.singleShot(2000, self.check_all)
    
    def init_ui(self):
        self.setWindowTitle("Clutch Tracker - Полный учет автомобилей")
        self.setGeometry(100, 100, 1400, 800)
        
        # Устанавливаем иконку, если есть
        icon_path = os.path.join(BASE_DIR, 'icon.ico')
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        
        top_layout = QHBoxLayout()
        
        self.org_btn = QPushButton("🏢 Организации")
        self.org_btn.clicked.connect(self.manage_organizations)
        self.org_btn.setFixedHeight(40)
        top_layout.addWidget(self.org_btn)
        
        self.docs_btn = QPushButton("📁 Все документы")
        self.docs_btn.clicked.connect(self.show_all_documents)
        self.docs_btn.setFixedHeight(40)
        top_layout.addWidget(self.docs_btn)
        
        self.settings_btn = QPushButton("⚙️ Настройки")
        self.settings_btn.clicked.connect(self.show_settings)
        self.settings_btn.setFixedHeight(40)
        top_layout.addWidget(self.settings_btn)
        
        self.backup_btn = QPushButton("💾 Резервное копирование")
        self.backup_btn.clicked.connect(self.create_backup)
        self.backup_btn.setFixedHeight(40)
        top_layout.addWidget(self.backup_btn)
        
        top_layout.addStretch()
        
        self.stats_label = QLabel()
        self.stats_label.setFixedHeight(40)
        self.stats_label.setStyleSheet("QLabel { background-color: #f0f0f0; padding: 10px; border-radius: 5px; }")
        top_layout.addWidget(self.stats_label)
        
        layout.addLayout(top_layout)
        
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        self.vehicles_tab = VehiclesTab(self)
        self.tabs.addTab(self.vehicles_tab, "🚗 Автомобили")
        
        self.clutch_tab = ServiceTab(self, 'clutch', "сцепление")
        self.tabs.addTab(self.clutch_tab, "🔧 Сцепление")
        
        self.maintenance_tab = ServiceTab(self, 'maintenance', "ТО")
        self.tabs.addTab(self.maintenance_tab, "🔧 ТО")
        
        self.brakes_tab = ServiceTab(self, 'brakes', "колодки")
        self.tabs.addTab(self.brakes_tab, "🔧 Колодки")
        
        self.insurance_tab = InsuranceTab(self)
        self.tabs.addTab(self.insurance_tab, "📄 Страховки")
        
        self.diagnostic_tab = DiagnosticTab(self)
        self.tabs.addTab(self.diagnostic_tab, "📋 Диагностика")
        
        self.permit_tab = PermitTab(self)
        self.tabs.addTab(self.permit_tab, "🎫 Пропуска Москва")
        
        self.tachograph_tab = TachographTab(self)
        self.tabs.addTab(self.tachograph_tab, "📊 Тахограф")
        
        self.repairs_tab = RepairsTab(self)
        self.tabs.addTab(self.repairs_tab, "🔨 Ремонты")
        
        self.fuel_tab = FuelTab(self)
        self.tabs.addTab(self.fuel_tab, "⛽ Топливо")
        
        self.stats_tab = StatisticsTab(self)
        self.tabs.addTab(self.stats_tab, "📊 Статистика")
        
        layout.addWidget(self.tabs)
        
        self.status_label = QLabel("Готов к работе")
        self.status_label.setStyleSheet("QLabel { color: #666666; }")
        layout.addWidget(self.status_label)
        
        self.update_all_tables()
        self.update_stats()
    
    def create_backup(self):
        """Создание резервной копии данных"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = os.path.join(DATA_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        backup_file = os.path.join(backup_dir, f'backup_{timestamp}.zip')
        
        try:
            import zipfile
            with zipfile.ZipFile(backup_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Добавляем файлы конфигурации
                if os.path.exists(CONFIG_DIR):
                    for root, dirs, files in os.walk(CONFIG_DIR):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, DATA_DIR)
                            zipf.write(file_path, arcname)
                
                # Добавляем документы
                if os.path.exists(DOCS_DIR):
                    for root, dirs, files in os.walk(DOCS_DIR):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, DATA_DIR)
                            zipf.write(file_path, arcname)
            
            QMessageBox.information(self, "Успех", f"Резервная копия создана:\n{backup_file}")
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось создать резервную копию:\n{str(e)}")
    
    def show_all_documents(self):
        # Для полной функциональности нужен класс DocumentsManagerDialog
        # Я его не включил для краткости, но вы можете добавить
        QMessageBox.information(self, "Информация", "Управление документами будет доступно в следующей версии")
    
    def show_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            QMessageBox.information(
                self, "Перезапуск",
                "Пожалуйста, перезапустите программу для применения изменений."
            )
    
    def manage_organizations(self):
        dialog = OrganizationManagerDialog(self.org_manager, self)
        dialog.exec_()
        self.update_all_tables()
    
    def check_all(self):
        """Проверка всех уведомлений"""
        notifications = []
        
        for plate, car in self.cars.items():
            # Проверка сервисных интервалов
            for service in car.services:
                rem = service.remaining()
                if 0 < rem <= 5000 and not service.notified:
                    service.notified = True
                    service_name = {
                        'clutch': 'сцепление',
                        'maintenance': 'ТО',
                        'brakes': 'колодки'
                    }.get(service.service_type, service.service_type)
                    notifications.append(f"{plate} - {service_name}: {rem} км")
            
            # Проверка страховок
            for ins in car.insurances:
                days = ins.days_until_expiry()
                if 0 < days <= 30 and not ins.notified:
                    ins.notified = True
                    notifications.append(f"{plate} - Страховка: {days} дней")
                elif days <= 0 and not ins.notified:
                    ins.notified = True
                    notifications.append(f"{plate} - Страховка ПРОСРОЧЕНА!")
            
            # Проверка диагностических карт
            for card in car.diagnostic_cards:
                days = card.days_until_expiry()
                if 0 < days <= 30 and not card.notified:
                    card.notified = True
                    notifications.append(f"{plate} - Диагностика: {days} дней")
                elif days <= 0 and not card.notified:
                    card.notified = True
                    notifications.append(f"{plate} - Диагностика ПРОСРОЧЕНА!")
            
            # Проверка пропусков
            for permit in car.permits:
                days = permit.days_until_expiry()
                if 0 < days <= 30 and not permit.notified:
                    permit.notified = True
                    notifications.append(f"{plate} - Пропуск в Москву: {days} дней")
                elif days <= 0 and not permit.notified:
                    permit.notified = True
                    notifications.append(f"{plate} - Пропуск ПРОСРОЧЕН!")
            
            # Проверка тахографов
            for tach in car.tachographs:
                days = tach.days_until_expiry()
                if 0 < days <= 30 and not tach.notified:
                    tach.notified = True
                    notifications.append(f"{plate} - Тахограф: {days} дней")
                elif days <= 0 and not tach.notified:
                    tach.notified = True
                    notifications.append(f"{plate} - Тахограф ПРОСРОЧЕН!")
        
        if notifications:
            msg = "Требуют внимания:\n\n" + "\n".join(notifications[:5])
            if len(notifications) > 5:
                msg += f"\n\n... и еще {len(notifications) - 5} уведомлений"
            
            QMessageBox.information(self, "Уведомления", msg)
            
            # Windows уведомление
            if NOTIFICATIONS_AVAILABLE:
                try:
                    notification.notify(
                        title='Clutch Tracker',
                        message=f'{len(notifications)} требуют внимания',
                        app_name='Clutch Tracker',
                        timeout=5
                    )
                except:
                    pass
            
            self.save_data()
            self.update_all_tables()
    
    def update_all_tables(self):
        self.vehicles_tab.update_table()
        self.update_service_table('clutch', self.clutch_tab.table)
        self.update_service_table('maintenance', self.maintenance_tab.table)
        self.update_service_table('brakes', self.brakes_tab.table)
        self.update_insurance_table()
        self.update_diagnostic_table()
        self.update_permit_table()
        self.update_tachograph_table()
        self.update_repairs_table()
        self.fuel_tab.update_table()
        self.fuel_tab.update_car_filter()
        self.stats_tab.update_stats()
    
    def update_service_table(self, service_type, table):
        table.setRowCount(0)
        table.setSortingEnabled(False)
        
        row = 0
        for plate, car in sorted(self.cars.items()):
            service = car.get_service(service_type)
            if service:
                table.insertRow(row)
                
                rem = service.remaining()
                
                plate_item = QTableWidgetItem(plate)
                plate_item.setFlags(plate_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 0, plate_item)
                
                mileage_item = QTableWidgetItem(f"{service.current_mileage} км")
                mileage_item.setFlags(mileage_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 1, mileage_item)
                
                last_item = QTableWidgetItem(f"{service.last_mileage} км")
                last_item.setFlags(last_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 2, last_item)
                
                interval_item = QTableWidgetItem(f"{service.interval} км")
                interval_item.setFlags(interval_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 3, interval_item)
                
                rem_item = QTableWidgetItem(f"{rem} км")
                rem_item.setFlags(rem_item.flags() & ~Qt.ItemIsEditable)
                if rem <= 0:
                    rem_item.setForeground(QBrush(QColor(255, 59, 48)))
                    rem_item.setFont(QFont("", 10, QFont.Bold))
                elif rem <= 5000:
                    rem_item.setForeground(QBrush(QColor(255, 159, 10)))
                table.setItem(row, 4, rem_item)
                
                date_item = QTableWidgetItem(service.last_date if service.last_date else "-")
                date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 5, date_item)
                
                org_item = QTableWidgetItem(service.org_name)
                org_item.setFlags(org_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 6, org_item)
                
                status_item = QTableWidgetItem()
                if rem <= 0:
                    status_item.setText("⚠️ СРОЧНО!")
                    status_item.setForeground(QBrush(QColor(255, 59, 48)))
                elif rem <= 5000:
                    status_item.setText(f"⚠️ {rem} км")
                    status_item.setForeground(QBrush(QColor(255, 159, 10)))
                else:
                    status_item.setText("✅ OK")
                    status_item.setForeground(QBrush(QColor(40, 205, 65)))
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 7, status_item)
                
                doc_paths = [d.file_path for d in service.documents]
                doc_count = len(doc_paths)
                doc_label = DocumentClickableLabel(f"📎 {doc_count}" if doc_count > 0 else "", doc_paths)
                table.setCellWidget(row, 8, doc_label)
                
                row += 1
        
        table.setSortingEnabled(True)
        table.resizeColumnsToContents()
    
    def update_insurance_table(self):
        table = self.insurance_tab.table
        table.setRowCount(0)
        table.setSortingEnabled(False)
        
        row = 0
        for plate, car in sorted(self.cars.items()):
            for ins in car.insurances:
                table.insertRow(row)
                
                days = ins.days_until_expiry()
                
                plate_item = QTableWidgetItem(plate)
                plate_item.setFlags(plate_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 0, plate_item)
                
                company_item = QTableWidgetItem(ins.company_name)
                company_item.setFlags(company_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 1, company_item)
                
                policy_item = QTableWidgetItem(ins.policy_number)
                policy_item.setFlags(policy_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 2, policy_item)
                
                start_item = QTableWidgetItem(ins.start_date)
                start_item.setFlags(start_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 3, start_item)
                
                end_item = QTableWidgetItem(ins.end_date)
                end_item.setFlags(end_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 4, end_item)
                
                days_item = QTableWidgetItem(str(days) if days > 0 else "ПРОСРОЧЕНО")
                days_item.setFlags(days_item.flags() & ~Qt.ItemIsEditable)
                if days <= 0:
                    days_item.setForeground(QBrush(QColor(255, 59, 48)))
                elif days <= 30:
                    days_item.setForeground(QBrush(QColor(255, 159, 10)))
                table.setItem(row, 5, days_item)
                
                cost_item = QTableWidgetItem(f"{ins.cost:,.0f} ₽".replace(",", " "))
                cost_item.setFlags(cost_item.flags() & ~Qt.ItemIsEditable)
                cost_item.setTextAlignment(Qt.AlignRight)
                table.setItem(row, 6, cost_item)
                
                status_item = QTableWidgetItem()
                if days <= 0:
                    status_item.setText("⚠️ ПРОСРОЧЕНО")
                    status_item.setForeground(QBrush(QColor(255, 59, 48)))
                elif days <= 30:
                    status_item.setText(f"⚠️ {days} дн.")
                    status_item.setForeground(QBrush(QColor(255, 159, 10)))
                else:
                    status_item.setText("✅ OK")
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 7, status_item)
                
                doc_paths = [d.file_path for d in ins.documents]
                doc_count = len(doc_paths)
                doc_label = DocumentClickableLabel(f"📎 {doc_count}" if doc_count > 0 else "", doc_paths)
                table.setCellWidget(row, 8, doc_label)
                
                row += 1
        
        table.setSortingEnabled(True)
        table.resizeColumnsToContents()
    
    def update_diagnostic_table(self):
        table = self.diagnostic_tab.table
        table.setRowCount(0)
        table.setSortingEnabled(False)
        
        row = 0
        for plate, car in sorted(self.cars.items()):
            for card in car.diagnostic_cards:
                table.insertRow(row)
                
                days = card.days_until_expiry()
                
                plate_item = QTableWidgetItem(plate)
                plate_item.setFlags(plate_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 0, plate_item)
                
                station_item = QTableWidgetItem(card.station_name)
                station_item.setFlags(station_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 1, station_item)
                
                card_item = QTableWidgetItem(card.card_number)
                card_item.setFlags(card_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 2, card_item)
                
                issue_item = QTableWidgetItem(card.issue_date)
                issue_item.setFlags(issue_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 3, issue_item)
                
                expiry_item = QTableWidgetItem(card.expiry_date)
                expiry_item.setFlags(expiry_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 4, expiry_item)
                
                days_item = QTableWidgetItem(str(days) if days > 0 else "ПРОСРОЧЕНО")
                days_item.setFlags(days_item.flags() & ~Qt.ItemIsEditable)
                if days <= 0:
                    days_item.setForeground(QBrush(QColor(255, 59, 48)))
                elif days <= 30:
                    days_item.setForeground(QBrush(QColor(255, 159, 10)))
                table.setItem(row, 5, days_item)
                
                cost_item = QTableWidgetItem(f"{card.cost:,.0f} ₽".replace(",", " "))
                cost_item.setFlags(cost_item.flags() & ~Qt.ItemIsEditable)
                cost_item.setTextAlignment(Qt.AlignRight)
                table.setItem(row, 6, cost_item)
                
                status_item = QTableWidgetItem()
                if days <= 0:
                    status_item.setText("⚠️ ПРОСРОЧЕНО")
                    status_item.setForeground(QBrush(QColor(255, 59, 48)))
                elif days <= 30:
                    status_item.setText(f"⚠️ {days} дн.")
                    status_item.setForeground(QBrush(QColor(255, 159, 10)))
                else:
                    status_item.setText("✅ OK")
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 7, status_item)
                
                doc_paths = [d.file_path for d in card.documents]
                doc_count = len(doc_paths)
                doc_label = DocumentClickableLabel(f"📎 {doc_count}" if doc_count > 0 else "", doc_paths)
                table.setCellWidget(row, 8, doc_label)
                
                row += 1
        
        table.setSortingEnabled(True)
        table.resizeColumnsToContents()
    
    def update_permit_table(self):
        table = self.permit_tab.table
        table.setRowCount(0)
        table.setSortingEnabled(False)
        
        row = 0
        for plate, car in sorted(self.cars.items()):
            for permit in car.permits:
                table.insertRow(row)
                
                days = permit.days_until_expiry()
                
                plate_item = QTableWidgetItem(plate)
                plate_item.setFlags(plate_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 0, plate_item)
                
                num_item = QTableWidgetItem(permit.permit_number)
                num_item.setFlags(num_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 1, num_item)
                
                zone_item = QTableWidgetItem(permit.zone)
                zone_item.setFlags(zone_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 2, zone_item)
                
                start_item = QTableWidgetItem(permit.start_date)
                start_item.setFlags(start_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 3, start_item)
                
                end_item = QTableWidgetItem(permit.end_date)
                end_item.setFlags(end_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 4, end_item)
                
                days_item = QTableWidgetItem(str(days) if days > 0 else "ПРОСРОЧЕНО")
                days_item.setFlags(days_item.flags() & ~Qt.ItemIsEditable)
                if days <= 0:
                    days_item.setForeground(QBrush(QColor(255, 59, 48)))
                elif days <= 30:
                    days_item.setForeground(QBrush(QColor(255, 159, 10)))
                table.setItem(row, 5, days_item)
                
                cost_item = QTableWidgetItem(f"{permit.cost:,.0f} ₽".replace(",", " ") if permit.cost > 0 else "-")
                cost_item.setFlags(cost_item.flags() & ~Qt.ItemIsEditable)
                cost_item.setTextAlignment(Qt.AlignRight)
                table.setItem(row, 6, cost_item)
                
                doc_paths = [d.file_path for d in permit.documents]
                doc_count = len(doc_paths)
                doc_label = DocumentClickableLabel(f"📎 {doc_count}" if doc_count > 0 else "", doc_paths)
                table.setCellWidget(row, 7, doc_label)
                
                row += 1
        
        table.setSortingEnabled(True)
        table.resizeColumnsToContents()
    
    def update_tachograph_table(self):
        table = self.tachograph_tab.table
        table.setRowCount(0)
        table.setSortingEnabled(False)
        
        row = 0
        for plate, car in sorted(self.cars.items()):
            for tach in car.tachographs:
                table.insertRow(row)
                
                days = tach.days_until_expiry()
                
                plate_item = QTableWidgetItem(plate)
                plate_item.setFlags(plate_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 0, plate_item)
                
                device_item = QTableWidgetItem(tach.device_number)
                device_item.setFlags(device_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 1, device_item)
                
                calib_item = QTableWidgetItem(tach.calibration_date)
                calib_item.setFlags(calib_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 2, calib_item)
                
                expiry_item = QTableWidgetItem(tach.expiry_date)
                expiry_item.setFlags(expiry_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 3, expiry_item)
                
                days_item = QTableWidgetItem(str(days) if days > 0 else "ПРОСРОЧЕНО")
                days_item.setFlags(days_item.flags() & ~Qt.ItemIsEditable)
                if days <= 0:
                    days_item.setForeground(QBrush(QColor(255, 59, 48)))
                elif days <= 30:
                    days_item.setForeground(QBrush(QColor(255, 159, 10)))
                table.setItem(row, 4, days_item)
                
                company_item = QTableWidgetItem(tach.company_name)
                company_item.setFlags(company_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 5, company_item)
                
                cost_item = QTableWidgetItem(f"{tach.cost:,.0f} ₽".replace(",", " ") if tach.cost > 0 else "-")
                cost_item.setFlags(cost_item.flags() & ~Qt.ItemIsEditable)
                cost_item.setTextAlignment(Qt.AlignRight)
                table.setItem(row, 6, cost_item)
                
                status_item = QTableWidgetItem()
                if days <= 0:
                    status_item.setText("⚠️ ПРОСРОЧЕНО")
                    status_item.setForeground(QBrush(QColor(255, 59, 48)))
                elif days <= 30:
                    status_item.setText(f"⚠️ {days} дн.")
                    status_item.setForeground(QBrush(QColor(255, 159, 10)))
                else:
                    status_item.setText("✅ OK")
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 7, status_item)
                
                doc_paths = [d.file_path for d in tach.documents]
                doc_count = len(doc_paths)
                doc_label = DocumentClickableLabel(f"📎 {doc_count}" if doc_count > 0 else "", doc_paths)
                table.setCellWidget(row, 8, doc_label)
                
                row += 1
        
        table.setSortingEnabled(True)
        table.resizeColumnsToContents()
    
    def update_repairs_table(self):
        table = self.repairs_tab.table
        table.setRowCount(0)
        table.setSortingEnabled(False)
        
        row = 0
        total_cost = 0
        for plate, car in sorted(self.cars.items()):
            for repair in sorted(car.repairs, key=lambda x: x.date_performed, reverse=True):
                table.insertRow(row)
                
                plate_item = QTableWidgetItem(plate)
                plate_item.setFlags(plate_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 0, plate_item)
                
                date_item = QTableWidgetItem(repair.date_performed)
                date_item.setFlags(date_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 1, date_item)
                
                mileage_item = QTableWidgetItem(f"{repair.mileage} км" if repair.mileage else "-")
                mileage_item.setFlags(mileage_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 2, mileage_item)
                
                workshop_item = QTableWidgetItem(repair.workshop)
                workshop_item.setFlags(workshop_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 3, workshop_item)
                
                desc_item = QTableWidgetItem(repair.description)
                desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row, 4, desc_item)
                
                cost_item = QTableWidgetItem(f"{repair.cost:,.0f} ₽".replace(",", " "))
                cost_item.setFlags(cost_item.flags() & ~Qt.ItemIsEditable)
                cost_item.setTextAlignment(Qt.AlignRight)
                table.setItem(row, 5, cost_item)
                total_cost += repair.cost
                
                status_item = QTableWidgetItem("✅ Выполнено")
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)
                status_item.setForeground(QBrush(QColor(40, 205, 65)))
                table.setItem(row, 6, status_item)
                
                doc_paths = [d.file_path for d in repair.documents]
                doc_count = len(doc_paths)
                doc_label = DocumentClickableLabel(f"📎 {doc_count}" if doc_count > 0 else "", doc_paths)
                table.setCellWidget(row, 7, doc_label)
                
                row += 1
        
        table.setSortingEnabled(True)
        table.resizeColumnsToContents()
        
        self.repairs_tab.update_total_cost()
    
    def update_stats(self):
        total_cars = len(self.cars)
        
        urgent = 0
        warning = 0
        
        for car in self.cars.values():
            for service in car.services:
                rem = service.remaining()
                if rem <= 0:
                    urgent += 1
                elif rem <= 5000:
                    warning += 1
            
            for ins in car.insurances:
                days = ins.days_until_expiry()
                if days <= 0:
                    urgent += 1
                elif days <= 30:
                    warning += 1
            
            for card in car.diagnostic_cards:
                days = card.days_until_expiry()
                if days <= 0:
                    urgent += 1
                elif days <= 30:
                    warning += 1
            
            for permit in car.permits:
                days = permit.days_until_expiry()
                if days <= 0:
                    urgent += 1
                elif days <= 30:
                    warning += 1
            
            for tach in car.tachographs:
                days = tach.days_until_expiry()
                if days <= 0:
                    urgent += 1
                elif days <= 30:
                    warning += 1
        
        self.stats_label.setText(
            f"Всего авто: {total_cars}  |  "
            f'<span style="color: #ff3b30;">⚠️ Срочно: {urgent}</span>  |  '
            f'<span style="color: #ff9f0a;">⚠️ Скоро: {warning}</span>'
        )
    
    def save_data(self):
        try:
            data = [car.to_dict() for car in self.cars.values()]
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.org_manager.save()
            self.fuel_manager.save()
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
    
    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        car = Car.from_dict(item)
                        self.cars[car.plate] = car
            except Exception as e:
                print(f"Ошибка загрузки: {e}")
        self.org_manager.load()
        self.fuel_manager.load()
    
    def closeEvent(self, event):
        self.save_data()
        event.accept()


def main():
    """Главная функция запуска"""
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Устанавливаем иконку, если есть
    icon_path = os.path.join(BASE_DIR, 'icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    # Проверяем, не запущена ли уже программа (только для Windows)
    if os.name == 'nt':
        try:
            import win32event
            import win32api
            import winerror
            mutex = win32event.CreateMutex(None, False, 'ClutchTrackerMutex')
            if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
                QMessageBox.warning(None, "Внимание", "Программа уже запущена!")
                return
        except:
            pass
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()