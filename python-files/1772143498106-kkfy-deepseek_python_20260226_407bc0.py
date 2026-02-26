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
import ctypes

# Определяем, запущены ли мы из exe
if getattr(sys, 'frozen', False):
    # Запуск из exe
    BASE_DIR = os.path.dirname(sys.executable)
    # Данные храним в AppData
    DATA_DIR = os.path.join(os.environ['APPDATA'], 'ClutchTracker')
else:
    # Запуск из скрипта
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
except ImportError:
    print("Ошибка: PyQt5 не установлен!")
    print("Установите: pip install PyQt5")
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

# Загружаем настройки или используем значения по умолчанию
settings = {}
if os.path.exists(CONFIG_FILE):
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            settings = json.load(f)
    except:
        settings = {}

# Пути из настроек или по умолчанию
DATA_DIR = settings.get('data_dir', DATA_DIR)
CONFIG_DIR = settings.get('config_dir', os.path.join(DATA_DIR, 'config'))
DOCS_DIR = settings.get('docs_dir', os.path.join(DATA_DIR, 'documents'))
DATA_FILE = os.path.join(CONFIG_DIR, "cars.json")
ORGS_FILE = os.path.join(CONFIG_DIR, "organizations.json")
FUEL_FILE = os.path.join(CONFIG_DIR, "fuel.json")

# Создаем директории снова (на случай изменения путей)
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(DOCS_DIR, exist_ok=True)

# ============= ВСЕ КЛАССЫ ИЗ ВАШЕГО КОДА =============
# Сюда вставляем все классы: MonthlyFuelRecord, FuelManager,
# DocumentClickableLabel, SettingsDialog, DocumentsFilterDialog,
# DocumentsManagerDialog, Organizations, OrganizationManagerDialog,
# Document, VehicleInfo, ServiceItem, InsuranceItem, DiagnosticCard,
# TachographItem, PermitItem, RepairItem, Car, DateEdit, MonthYearEdit,
# OrganizationComboBox, CarHistoryDialog, VehicleDialog, VehiclesTab,
# FuelTab, StatisticsTab, ServiceTab, TachographTab, PermitTab,
# InsuranceTab, DiagnosticTab, RepairsTab
# 
# ВАЖНО: В классе MainWindow нужно изменить метод check_all для Windows-уведомлений

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
        
        # Устанавливаем иконку для окна
        if os.path.exists(os.path.join(BASE_DIR, 'icon.ico')):
            self.setWindowIcon(QIcon(os.path.join(BASE_DIR, 'icon.ico')))
        
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
        dialog = DocumentsManagerDialog(self)
        dialog.exec_()
    
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
            
            # Показываем диалог
            QMessageBox.information(self, "Уведомления", msg)
            
            # Показываем системное уведомление Windows
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
    
    # Устанавливаем иконку приложения
    icon_path = os.path.join(BASE_DIR, 'icon.ico')
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()