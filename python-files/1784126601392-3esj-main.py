import sys
import os
import json
import csv
import socket
import sqlite3
from datetime import datetime
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QTabWidget, QTableWidget, QTableWidgetItem, QPushButton, QLabel, QLineEdit,
    QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox, QMessageBox, QDialog,
    QDialogButtonBox, QFormLayout, QGroupBox, QHeaderView, QAbstractItemView,
    QFileDialog, QTextEdit, QCheckBox, QSplitter, QStyle, QStyleFactory
)
from PyQt5.QtCore import Qt, QDate, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette, QIcon

# ============================ КОНФИГУРАЦИЯ ============================
DB_FILE = 'kkm_data.db'
INECRMAN_HOST = '127.0.0.1'
INECRMAN_PORT = 50009

# ============================ БАЗА ДАННЫХ ============================
class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE)
        self.cursor = self.conn.cursor()
        self.init_db()

    def init_db(self):
        # Таблица товаров
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS goods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL CHECK(type IN ('товар','услуга')),
                unit TEXT NOT NULL,
                price REAL NOT NULL,
                tax_code INTEGER NOT NULL
            )
        ''')
        # Таблица налоговых ставок (код фиксирован)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tax_rates (
                code INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                rate REAL NOT NULL
            )
        ''')
        # Заполним ставки по умолчанию, если их нет
        default_rates = [(0, 'Без НДС', 0.0), (1, 'НДС 20%', 20.0), (2, 'НДС 10%', 10.0), (3, 'НДС 0%', 0.0)]
        self.cursor.execute('SELECT COUNT(*) FROM tax_rates')
        if self.cursor.fetchone()[0] == 0:
            self.cursor.executemany('INSERT INTO tax_rates (code, name, rate) VALUES (?,?,?)', default_rates)

        # Таблица продаж
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS sales (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sale_date TEXT NOT NULL,
                goods_id INTEGER,
                goods_name TEXT NOT NULL,
                quantity REAL NOT NULL,
                unit TEXT NOT NULL,
                price REAL NOT NULL,
                total REAL NOT NULL,
                tax_code INTEGER NOT NULL,
                payment_type TEXT NOT NULL CHECK(payment_type IN ('наличные','безналичные')),
                check_number INTEGER,
                shift_number INTEGER,
                cashier_name TEXT
            )
        ''')
        # Таблица настроек (ключ-значение)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        # Настройки по умолчанию
        default_settings = [
            ('org_name', 'ООО "Ромашка"'),
            ('org_inn', '1234567890'),
            ('default_cashier_name', 'Иванов И.И.'),
            ('default_cashier_inn', '123456789012'),
            ('com_port', 'COM1'),
            ('model', '185F'),
        ]
        for key, val in default_settings:
            self.cursor.execute('INSERT OR IGNORE INTO settings (key, value) VALUES (?,?)', (key, val))
        self.conn.commit()

    # --- НАСТРОЙКИ ---
    def get_setting(self, key):
        self.cursor.execute('SELECT value FROM settings WHERE key=?', (key,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    def set_setting(self, key, value):
        self.cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)', (key, value))
        self.conn.commit()

    # --- НАЛОГОВЫЕ СТАВКИ ---
    def get_tax_rates(self):
        self.cursor.execute('SELECT code, name, rate FROM tax_rates ORDER BY code')
        return [{'code': r[0], 'name': r[1], 'rate': r[2]} for r in self.cursor.fetchall()]

    def update_tax_rate(self, code, name, rate):
        self.cursor.execute('UPDATE tax_rates SET name=?, rate=? WHERE code=?', (name, rate, code))
        self.conn.commit()

    # --- ТОВАРЫ ---
    def get_goods(self, type_filter=None, search=None):
        sql = 'SELECT id, name, type, unit, price, tax_code FROM goods'
        params = []
        conditions = []
        if type_filter:
            conditions.append('type=?')
            params.append(type_filter)
        if search:
            conditions.append('name LIKE ?')
            params.append('%' + search + '%')
        if conditions:
            sql += ' WHERE ' + ' AND '.join(conditions)
        sql += ' ORDER BY name'
        self.cursor.execute(sql, params)
        rows = self.cursor.fetchall()
        return [{'id': r[0], 'name': r[1], 'type': r[2], 'unit': r[3], 'price': r[4], 'tax_code': r[5]} for r in rows]

    def add_goods(self, name, type_, unit, price, tax_code):
        self.cursor.execute('INSERT INTO goods (name, type, unit, price, tax_code) VALUES (?,?,?,?,?)',
                            (name, type_, unit, price, tax_code))
        self.conn.commit()
        return self.cursor.lastrowid

    def update_goods(self, id_, name, type_, unit, price, tax_code):
        self.cursor.execute('UPDATE goods SET name=?, type=?, unit=?, price=?, tax_code=? WHERE id=?',
                            (name, type_, unit, price, tax_code, id_))
        self.conn.commit()

    def delete_goods(self, id_):
        self.cursor.execute('DELETE FROM goods WHERE id=?', (id_,))
        self.conn.commit()

    # --- ПРОДАЖИ ---
    def add_sale(self, data):
        cols = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        sql = f'INSERT INTO sales ({cols}) VALUES ({placeholders})'
        self.cursor.execute(sql, list(data.values()))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_sales(self, filters=None):
        sql = 'SELECT s.*, g.type as goods_type FROM sales s LEFT JOIN goods g ON s.goods_id = g.id WHERE 1=1'
        params = []
        if filters:
            if filters.get('goods_type'):
                sql += ' AND g.type = ?'
                params.append(filters['goods_type'])
            if filters.get('date_from'):
                sql += ' AND s.sale_date >= ?'
                params.append(filters['date_from'])
            if filters.get('date_to'):
                sql += ' AND s.sale_date <= ?'
                params.append(filters['date_to'])
            if filters.get('sum_from') is not None:
                sql += ' AND s.total >= ?'
                params.append(filters['sum_from'])
            if filters.get('sum_to') is not None:
                sql += ' AND s.total <= ?'
                params.append(filters['sum_to'])
            if filters.get('payment_type'):
                sql += ' AND s.payment_type = ?'
                params.append(filters['payment_type'])
        sql += ' ORDER BY s.sale_date DESC'
        self.cursor.execute(sql, params)
        rows = self.cursor.fetchall()
        # Получаем имена колонок
        col_names = [desc[0] for desc in self.cursor.description]
        return [dict(zip(col_names, row)) for row in rows]

    def get_sales_summary(self, filters=None):
        sales = self.get_sales(filters)
        total_count = len(sales)
        total_sum = sum(s['total'] for s in sales)
        total_cash = sum(s['total'] for s in sales if s['payment_type'] == 'наличные')
        total_non_cash = sum(s['total'] for s in sales if s['payment_type'] == 'безналичные')
        return {'count': total_count, 'sum': total_sum, 'cash': total_cash, 'non_cash': total_non_cash}

    # --- ИМПОРТ/ЭКСПОРТ CSV (товары) ---
    def export_goods_csv(self, type_filter=None):
        goods = self.get_goods(type_filter)
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output, delimiter=';')
        writer.writerow(['Наименование', 'Тип', 'Ед.изм.', 'Цена', 'КодНДС'])
        for g in goods:
            writer.writerow([g['name'], g['type'], g['unit'], g['price'], g['tax_code']])
        return output.getvalue()

    def import_goods_csv(self, content):
        import csv, io
        reader = csv.reader(io.StringIO(content), delimiter=';')
        header = next(reader, None)
        count = 0
        for row in reader:
            if len(row) >= 5:
                name, type_, unit, price, tax_code = row[0], row[1], row[2], float(row[3]), int(row[4])
                self.add_goods(name, type_, unit, price, tax_code)
                count += 1
        return count

    def close(self):
        self.conn.close()

# ============================ КЛИЕНТ INECRMAN ============================
class KKMClient:
    @staticmethod
    def send_command(cmd):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(30)
            sock.connect((INECRMAN_HOST, INECRMAN_PORT))
            msg = json.dumps(cmd, ensure_ascii=False) + '\n'
            sock.sendall(msg.encode('utf-8'))
            response = b''
            while True:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                response += chunk
                if response.endswith(b'\n'):
                    break
            sock.close()
            return json.loads(response.decode('utf-8'))
        except Exception as e:
            return {'result': -1, 'errorDescription': str(e)}

    @staticmethod
    def open_session(port, model):
        cmd = {'sessionKey': None, 'command': 'OpenSession', 'portName': port, 'model': model}
        return KKMClient.send_command(cmd)

    @staticmethod
    def open_shift(session_key, cashier_name, cashier_inn):
        cmd = {
            'sessionKey': session_key,
            'command': 'OpenShift',
            'printDoc': True,
            'cashierInfo': {'cashierName': cashier_name, 'cashierINN': cashier_inn}
        }
        return KKMClient.send_command(cmd)

    @staticmethod
    def close_shift(session_key, cashier_name, cashier_inn):
        cmd = {
            'sessionKey': session_key,
            'command': 'CloseShift',
            'printDoc': True,
            'cashierInfo': {'cashierName': cashier_name, 'cashierINN': cashier_inn}
        }
        return KKMClient.send_command(cmd)

    @staticmethod
    def get_status(session_key):
        cmd = {'sessionKey': session_key, 'command': 'GetStatus'}
        return KKMClient.send_command(cmd)

    @staticmethod
    def open_check(session_key, check_type=0, auto_print=True):
        cmd = {'sessionKey': session_key, 'command': 'OpenCheck', 'checkType': check_type, 'autoPrint': auto_print}
        return KKMClient.send_command(cmd)

    @staticmethod
    def add_goods(session_key, name, price, quantity=1, tax=0):
        cmd = {
            'sessionKey': session_key,
            'command': 'AddGoods',
            'goodsName': name,
            'price': int(price * 100),  # копейки
            'quantity': quantity,
            'tax': tax
        }
        return KKMClient.send_command(cmd)

    @staticmethod
    def close_check(session_key, payment_type=0, payment_sum=0):
        cmd = {
            'sessionKey': session_key,
            'command': 'CloseCheck',
            'paymentType': payment_type,
            'paymentSum': int(payment_sum * 100)
        }
        return KKMClient.send_command(cmd)

    @staticmethod
    def reset_check(session_key):
        cmd = {'sessionKey': session_key, 'command': 'ResetCheck'}
        return KKMClient.send_command(cmd)

    @staticmethod
    def print_text(session_key, text):
        cmd = {'sessionKey': session_key, 'command': 'PrintText', 'text': text}
        return KKMClient.send_command(cmd)

# ============================ ГЛАВНОЕ ОКНО ============================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.session_key = None
        self.shift_open = False
        self.cashier_name = ''
        self.cashier_inn = ''
        self.shift_number = None
        self.current_check_open = False
        self.cart = []  # список словарей {id, name, unit, price, tax_code, quantity}
        self.init_ui()
        self.load_settings()
        self.update_status()

    def init_ui(self):
        self.setWindowTitle('ККТ Меркурий-115Ф by Aks.Leks')
        self.setMinimumSize(1100, 750)
        # Центральный виджет и вкладки
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Создаём вкладки
        self.tab_cash = QWidget()
        self.tab_goods = QWidget()
        self.tab_sales = QWidget()
        self.tab_settings = QWidget()
        self.tabs.addTab(self.tab_cash, 'Касса')
        self.tabs.addTab(self.tab_goods, 'Товары')
        self.tabs.addTab(self.tab_sales, 'Продажи')
        self.tabs.addTab(self.tab_settings, 'Настройки')

        self.setup_tab_cash()
        self.setup_tab_goods()
        self.setup_tab_sales()
        self.setup_tab_settings()

        # Применяем стиль
        self.apply_style()

    # ---------------- ВКЛАДКА "КАССА" ----------------
    def setup_tab_cash(self):
        layout = QVBoxLayout(self.tab_cash)
        # Верхняя панель статуса
        status_group = QGroupBox('Статус')
        status_layout = QHBoxLayout()
        self.lbl_session = QLabel('Сессия: не открыта')
        self.lbl_shift = QLabel('Смена: закрыта')
        self.lbl_cashier = QLabel('Кассир: не задан')
        self.btn_refresh_status = QPushButton('Обновить статус')
        self.btn_refresh_status.clicked.connect(self.refresh_status)
        status_layout.addWidget(self.lbl_session)
        status_layout.addWidget(self.lbl_shift)
        status_layout.addWidget(self.lbl_cashier)
        status_layout.addStretch()
        status_layout.addWidget(self.btn_refresh_status)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        # Панель управления сменой
        shift_group = QGroupBox('Управление сменой')
        shift_layout = QHBoxLayout()
        self.btn_open_shift = QPushButton('Открыть смену')
        self.btn_close_shift = QPushButton('Закрыть смену')
        self.btn_open_shift.clicked.connect(self.open_shift)
        self.btn_close_shift.clicked.connect(self.close_shift)
        shift_layout.addWidget(self.btn_open_shift)
        shift_layout.addWidget(self.btn_close_shift)
        shift_layout.addStretch()
        shift_group.setLayout(shift_layout)
        layout.addWidget(shift_group)

        # Таблица корзины чека
        cart_group = QGroupBox('Текущий чек')
        cart_layout = QVBoxLayout()
        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)
        self.cart_table.setHorizontalHeaderLabels(['ID', 'Наименование', 'Кол-во', 'Ед.', 'Цена', 'Сумма'])
        self.cart_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.cart_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.cart_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        cart_layout.addWidget(self.cart_table)
        cart_group.setLayout(cart_layout)
        layout.addWidget(cart_group, 1)

        # Кнопки работы с чеком
        check_buttons = QHBoxLayout()
        self.btn_add_goods = QPushButton('Добавить товар')
        self.btn_remove_goods = QPushButton('Удалить позицию')
        self.btn_clear_cart = QPushButton('Очистить чек')
        self.btn_open_check = QPushButton('Открыть чек (фискальный)')
        self.btn_close_check = QPushButton('Закрыть чек (оплата)')
        self.btn_reset_check = QPushButton('Аннулировать чек')
        self.btn_print_text = QPushButton('Печать текста')
        self.btn_add_goods.clicked.connect(self.add_goods_to_cart)
        self.btn_remove_goods.clicked.connect(self.remove_cart_item)
        self.btn_clear_cart.clicked.connect(self.clear_cart)
        self.btn_open_check.clicked.connect(self.open_fiscal_check)
        self.btn_close_check.clicked.connect(self.close_fiscal_check)
        self.btn_reset_check.clicked.connect(self.reset_fiscal_check)
        self.btn_print_text.clicked.connect(self.print_text)
        check_buttons.addWidget(self.btn_add_goods)
        check_buttons.addWidget(self.btn_remove_goods)
        check_buttons.addWidget(self.btn_clear_cart)
        check_buttons.addWidget(self.btn_open_check)
        check_buttons.addWidget(self.btn_close_check)
        check_buttons.addWidget(self.btn_reset_check)
        check_buttons.addWidget(self.btn_print_text)
        layout.addLayout(check_buttons)

        # Обновим состояние кнопок
        self.update_cart_buttons()

    # ---------------- ВКЛАДКА "ТОВАРЫ" ----------------
    def setup_tab_goods(self):
        layout = QVBoxLayout(self.tab_goods)
        # Фильтры
        filter_layout = QHBoxLayout()
        self.goods_filter_type = QComboBox()
        self.goods_filter_type.addItem('Все', '')
        self.goods_filter_type.addItem('Товары', 'товар')
        self.goods_filter_type.addItem('Услуги', 'услуга')
        self.goods_filter_search = QLineEdit()
        self.goods_filter_search.setPlaceholderText('Поиск по названию...')
        self.btn_goods_filter = QPushButton('Применить')
        self.btn_goods_filter.clicked.connect(self.load_goods)
        self.btn_goods_add = QPushButton('Добавить')
        self.btn_goods_edit = QPushButton('Редактировать')
        self.btn_goods_delete = QPushButton('Удалить')
        self.btn_goods_import = QPushButton('Импорт CSV')
        self.btn_goods_export = QPushButton('Экспорт CSV')
        self.btn_goods_add.clicked.connect(self.add_goods_dialog)
        self.btn_goods_edit.clicked.connect(self.edit_goods_dialog)
        self.btn_goods_delete.clicked.connect(self.delete_goods)
        self.btn_goods_import.clicked.connect(self.import_goods_csv)
        self.btn_goods_export.clicked.connect(self.export_goods_csv)
        filter_layout.addWidget(QLabel('Тип:'))
        filter_layout.addWidget(self.goods_filter_type)
        filter_layout.addWidget(QLabel('Поиск:'))
        filter_layout.addWidget(self.goods_filter_search)
        filter_layout.addWidget(self.btn_goods_filter)
        filter_layout.addStretch()
        filter_layout.addWidget(self.btn_goods_add)
        filter_layout.addWidget(self.btn_goods_edit)
        filter_layout.addWidget(self.btn_goods_delete)
        filter_layout.addWidget(self.btn_goods_import)
        filter_layout.addWidget(self.btn_goods_export)
        layout.addLayout(filter_layout)

        # Таблица товаров
        self.goods_table = QTableWidget()
        self.goods_table.setColumnCount(6)
        self.goods_table.setHorizontalHeaderLabels(['ID', 'Наименование', 'Тип', 'Ед.изм.', 'Цена', 'КодНДС'])
        self.goods_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.goods_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.goods_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.goods_table)
        self.load_goods()

    # ---------------- ВКЛАДКА "ПРОДАЖИ" ----------------
    def setup_tab_sales(self):
        layout = QVBoxLayout(self.tab_sales)
        # Фильтры
        filter_layout = QGridLayout()
        self.sales_filter_type = QComboBox()
        self.sales_filter_type.addItem('Все', '')
        self.sales_filter_type.addItem('Товары', 'товар')
        self.sales_filter_type.addItem('Услуги', 'услуга')
        self.sales_filter_date_from = QDateEdit()
        self.sales_filter_date_from.setCalendarPopup(True)
        self.sales_filter_date_from.setDate(QDate.currentDate().addDays(-30))
        self.sales_filter_date_to = QDateEdit()
        self.sales_filter_date_to.setCalendarPopup(True)
        self.sales_filter_date_to.setDate(QDate.currentDate())
        self.sales_filter_sum_from = QDoubleSpinBox()
        self.sales_filter_sum_from.setRange(0, 999999)
        self.sales_filter_sum_from.setPrefix('от ')
        self.sales_filter_sum_to = QDoubleSpinBox()
        self.sales_filter_sum_to.setRange(0, 999999)
        self.sales_filter_sum_to.setPrefix('до ')
        self.sales_filter_payment = QComboBox()
        self.sales_filter_payment.addItem('Все', '')
        self.sales_filter_payment.addItem('Наличные', 'наличные')
        self.sales_filter_payment.addItem('Безналичные', 'безналичные')
        self.btn_sales_filter = QPushButton('Применить')
        self.btn_sales_filter.clicked.connect(self.load_sales)
        self.btn_sales_export = QPushButton('Экспорт CSV')
        self.btn_sales_export.clicked.connect(self.export_sales_csv)

        filter_layout.addWidget(QLabel('Тип товара:'), 0, 0)
        filter_layout.addWidget(self.sales_filter_type, 0, 1)
        filter_layout.addWidget(QLabel('Дата с:'), 0, 2)
        filter_layout.addWidget(self.sales_filter_date_from, 0, 3)
        filter_layout.addWidget(QLabel('по:'), 0, 4)
        filter_layout.addWidget(self.sales_filter_date_to, 0, 5)
        filter_layout.addWidget(QLabel('Сумма:'), 1, 0)
        filter_layout.addWidget(self.sales_filter_sum_from, 1, 1)
        filter_layout.addWidget(self.sales_filter_sum_to, 1, 2)
        filter_layout.addWidget(QLabel('Оплата:'), 1, 3)
        filter_layout.addWidget(self.sales_filter_payment, 1, 4)
        filter_layout.addWidget(self.btn_sales_filter, 1, 5)
        filter_layout.addWidget(self.btn_sales_export, 1, 6)
        layout.addLayout(filter_layout)

        # Сводка
        summary_layout = QHBoxLayout()
        self.lbl_sales_count = QLabel('Кол-во: 0')
        self.lbl_sales_sum = QLabel('Сумма: 0.00')
        self.lbl_sales_cash = QLabel('Наличные: 0.00')
        self.lbl_sales_non_cash = QLabel('Безналичные: 0.00')
        summary_layout.addWidget(self.lbl_sales_count)
        summary_layout.addWidget(self.lbl_sales_sum)
        summary_layout.addWidget(self.lbl_sales_cash)
        summary_layout.addWidget(self.lbl_sales_non_cash)
        summary_layout.addStretch()
        layout.addLayout(summary_layout)

        # Таблица продаж
        self.sales_table = QTableWidget()
        self.sales_table.setColumnCount(9)
        self.sales_table.setHorizontalHeaderLabels(
            ['Дата', 'Товар', 'Тип', 'Кол-во', 'Ед.', 'Цена', 'Сумма', 'Оплата', 'Кассир']
        )
        self.sales_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.sales_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.sales_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.sales_table)
        self.load_sales()

    # ---------------- ВКЛАДКА "НАСТРОЙКИ" ----------------
    def setup_tab_settings(self):
        layout = QVBoxLayout(self.tab_settings)
        # Реквизиты
        group_org = QGroupBox('Реквизиты организации')
        form = QFormLayout()
        self.setting_org_name = QLineEdit()
        self.setting_org_inn = QLineEdit()
        self.setting_cashier_name = QLineEdit()
        self.setting_cashier_inn = QLineEdit()
        self.setting_com_port = QLineEdit()
        self.setting_model = QLineEdit()
        form.addRow('Наименование:', self.setting_org_name)
        form.addRow('ИНН:', self.setting_org_inn)
        form.addRow('Кассир (по умолчанию):', self.setting_cashier_name)
        form.addRow('ИНН кассира:', self.setting_cashier_inn)
        form.addRow('COM-порт:', self.setting_com_port)
        form.addRow('Модель ККТ:', self.setting_model)
        group_org.setLayout(form)
        layout.addWidget(group_org)

        # Налоговые ставки
        group_tax = QGroupBox('Налоговые ставки')
        tax_layout = QVBoxLayout()
        self.tax_table = QTableWidget()
        self.tax_table.setColumnCount(3)
        self.tax_table.setHorizontalHeaderLabels(['Код', 'Название', 'Ставка (%)'])
        self.tax_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tax_table.setEditTriggers(QAbstractItemView.DoubleClicked | QAbstractItemView.EditKeyPressed)
        tax_layout.addWidget(self.tax_table)
        btn_save_tax = QPushButton('Сохранить ставки')
        btn_save_tax.clicked.connect(self.save_tax_rates)
        tax_layout.addWidget(btn_save_tax)
        group_tax.setLayout(tax_layout)
        layout.addWidget(group_tax)

        # Кнопка сохранения всех настроек
        btn_save_all = QPushButton('Сохранить все настройки')
        btn_save_all.clicked.connect(self.save_all_settings)
        layout.addWidget(btn_save_all)

        self.load_settings_to_ui()

    # ==================== МЕТОДЫ ЛОГИКИ ====================

    def load_settings(self):
        # Загружаем настройки из БД
        self.cashier_name = self.db.get_setting('default_cashier_name') or ''
        self.cashier_inn = self.db.get_setting('default_cashier_inn') or ''
        # Обновим статус

    def load_settings_to_ui(self):
        self.setting_org_name.setText(self.db.get_setting('org_name') or '')
        self.setting_org_inn.setText(self.db.get_setting('org_inn') or '')
        self.setting_cashier_name.setText(self.db.get_setting('default_cashier_name') or '')
        self.setting_cashier_inn.setText(self.db.get_setting('default_cashier_inn') or '')
        self.setting_com_port.setText(self.db.get_setting('com_port') or 'COM1')
        self.setting_model.setText(self.db.get_setting('model') or '185F')
        # Загружаем налоговые ставки
        rates = self.db.get_tax_rates()
        self.tax_table.setRowCount(len(rates))
        for i, r in enumerate(rates):
            self.tax_table.setItem(i, 0, QTableWidgetItem(str(r['code'])))
            self.tax_table.setItem(i, 1, QTableWidgetItem(r['name']))
            self.tax_table.setItem(i, 2, QTableWidgetItem(str(r['rate'])))
        # Запретим редактирование кода
        for i in range(len(rates)):
            self.tax_table.item(i, 0).setFlags(Qt.ItemIsSelectable | Qt.ItemIsEnabled)

    def save_all_settings(self):
        self.db.set_setting('org_name', self.setting_org_name.text())
        self.db.set_setting('org_inn', self.setting_org_inn.text())
        self.db.set_setting('default_cashier_name', self.setting_cashier_name.text())
        self.db.set_setting('default_cashier_inn', self.setting_cashier_inn.text())
        self.db.set_setting('com_port', self.setting_com_port.text())
        self.db.set_setting('model', self.setting_model.text())
        self.load_settings()
        QMessageBox.information(self, 'Успех', 'Настройки сохранены')

    def save_tax_rates(self):
        row_count = self.tax_table.rowCount()
        for i in range(row_count):
            code = int(self.tax_table.item(i, 0).text())
            name = self.tax_table.item(i, 1).text()
            rate = float(self.tax_table.item(i, 2).text())
            self.db.update_tax_rate(code, name, rate)
        QMessageBox.information(self, 'Успех', 'Ставки НДС сохранены')

    # ---------- СТАТУС ----------
    def update_status(self):
        if self.session_key:
            self.lbl_session.setText(f'Сессия: активна (ключ: {self.session_key[:8]}...)')
        else:
            self.lbl_session.setText('Сессия: не открыта')
        self.lbl_shift.setText(f'Смена: {"открыта" if self.shift_open else "закрыта"}')
        self.lbl_cashier.setText(f'Кассир: {self.cashier_name or "не задан"}')
        # Состояние кнопок
        self.btn_open_shift.setEnabled(not self.shift_open and self.session_key is not None)
        self.btn_close_shift.setEnabled(self.shift_open)
        self.btn_open_check.setEnabled(self.shift_open and not self.current_check_open)
        self.btn_close_check.setEnabled(self.shift_open and self.current_check_open and len(self.cart) > 0)
        self.btn_reset_check.setEnabled(self.shift_open and self.current_check_open)
        self.btn_add_goods.setEnabled(self.shift_open and self.current_check_open)
        self.btn_remove_goods.setEnabled(self.shift_open and self.current_check_open and len(self.cart) > 0)
        self.btn_clear_cart.setEnabled(self.shift_open and self.current_check_open and len(self.cart) > 0)
        self.btn_print_text.setEnabled(self.session_key is not None)

    def refresh_status(self):
        if self.session_key:
            resp = KKMClient.get_status(self.session_key)
            if resp.get('result') == 0:
                self.shift_open = resp.get('shiftOpen', False)
                # Обновим номер смены
                self.shift_number = resp.get('shiftNumber')
                QMessageBox.information(self, 'Статус', 'Статус обновлён')
            else:
                QMessageBox.warning(self, 'Ошибка', f"Не удалось получить статус: {resp.get('errorDescription')}")
        else:
            QMessageBox.information(self, 'Информация', 'Сессия не открыта. Откройте смену для автоматического открытия сессии.')
        self.update_status()

    # ---------- СМЕНА ----------
    def ensure_session(self):
        if self.session_key is None:
            port = self.db.get_setting('com_port') or 'COM1'
            model = self.db.get_setting('model') or '185F'
            resp = KKMClient.open_session(port, model)
            if resp.get('result') == 0:
                self.session_key = resp.get('sessionKey')
                return True
            else:
                QMessageBox.critical(self, 'Ошибка', f"Не удалось открыть сессию: {resp.get('errorDescription')}")
                return False
        return True

    def open_shift(self):
        if not self.ensure_session():
            return
        # Запросим кассира (можно из настроек)
        cashier_name = self.db.get_setting('default_cashier_name') or ''
        cashier_inn = self.db.get_setting('default_cashier_inn') or ''
        resp = KKMClient.open_shift(self.session_key, cashier_name, cashier_inn)
        if resp.get('result') == 0:
            self.shift_open = True
            self.shift_number = resp.get('shiftNumber')
            self.cashier_name = cashier_name
            self.cashier_inn = cashier_inn
            QMessageBox.information(self, 'Успех', 'Смена открыта')
        else:
            QMessageBox.critical(self, 'Ошибка', f"Не удалось открыть смену: {resp.get('errorDescription')}")
        self.update_status()

    def close_shift(self):
        if not self.ensure_session():
            return
        cashier_name = self.db.get_setting('default_cashier_name') or ''
        cashier_inn = self.db.get_setting('default_cashier_inn') or ''
        resp = KKMClient.close_shift(self.session_key, cashier_name, cashier_inn)
        if resp.get('result') == 0:
            self.shift_open = False
            self.shift_number = None
            QMessageBox.information(self, 'Успех', 'Смена закрыта')
        else:
            QMessageBox.critical(self, 'Ошибка', f"Не удалось закрыть смену: {resp.get('errorDescription')}")
        self.update_status()

    # ---------- ЧЕК ----------
    def open_fiscal_check(self):
        if not self.shift_open:
            QMessageBox.warning(self, 'Предупреждение', 'Смена не открыта')
            return
        if self.current_check_open:
            QMessageBox.warning(self, 'Предупреждение', 'Чек уже открыт')
            return
        # Выбор типа чека
        types = ['Приход', 'Возврат прихода', 'Расход', 'Возврат расхода', 'Коррекция прихода', 'Коррекция расхода']
        item, ok = QInputDialog.getItem(self, 'Тип чека', 'Выберите тип:', types, 0, False)
        if not ok:
            return
        check_type = types.index(item)
        resp = KKMClient.open_check(self.session_key, check_type, True)
        if resp.get('result') == 0:
            self.current_check_open = True
            self.cart = []
            self.update_cart_table()
            QMessageBox.information(self, 'Успех', 'Чек открыт')
        else:
            QMessageBox.critical(self, 'Ошибка', f"Не удалось открыть чек: {resp.get('errorDescription')}")
        self.update_status()

    def add_goods_to_cart(self):
        if not self.current_check_open:
            QMessageBox.warning(self, 'Предупреждение', 'Чек не открыт')
            return
        # Диалог выбора товара из базы
        goods_list = self.db.get_goods()
        if not goods_list:
            QMessageBox.information(self, 'Информация', 'Нет товаров в базе. Добавьте товары во вкладке "Товары".')
            return
        names = [f"{g['name']} ({g['unit']}) - {g['price']} руб." for g in goods_list]
        item, ok = QInputDialog.getItem(self, 'Выбор товара', 'Выберите товар:', names, 0, False)
        if not ok:
            return
        idx = names.index(item)
        goods = goods_list[idx]
        # Запросим количество
        quantity, ok = QInputDialog.getDouble(self, 'Количество', 'Введите количество:', 1, 0.001, 9999, 3)
        if not ok:
            return
        # Добавляем в корзину
        self.cart.append({
            'id': goods['id'],
            'name': goods['name'],
            'unit': goods['unit'],
            'price': goods['price'],
            'tax_code': goods['tax_code'],
            'quantity': quantity
        })
        self.update_cart_table()
        # Отправляем в ККТ
        try:
            resp = KKMClient.add_goods(
                self.session_key,
                goods['name'],
                goods['price'],
                quantity,
                goods['tax_code']
            )
            if resp.get('result') != 0:
                QMessageBox.warning(self, 'Ошибка ККТ', f"Не удалось добавить товар: {resp.get('errorDescription')}")
        except Exception as e:
            QMessageBox.critical(self, 'Ошибка', str(e))

    def remove_cart_item(self):
        row = self.cart_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите позицию для удаления')
            return
        # Удаляем из корзины
        del self.cart[row]
        self.update_cart_table()
        # ККТ не поддерживает удаление позиций, поэтому просто аннулируем чек и открываем заново? 
        # В протоколе нет команды удаления позиции, но можно использовать ResetCheck и начать заново.
        # Предложим пользователю переоткрыть чек.
        reply = QMessageBox.question(self, 'Внимание', 'Удаление позиции возможно только путём аннулирования чека. Переоткрыть чек?',
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.reset_fiscal_check()
            self.open_fiscal_check()
            # После переоткрытия нужно заново добавить оставшиеся позиции
            for item in self.cart:
                KKMClient.add_goods(self.session_key, item['name'], item['price'], item['quantity'], item['tax_code'])
        self.update_status()

    def clear_cart(self):
        if not self.cart:
            return
        reply = QMessageBox.question(self, 'Очистка', 'Очистить весь чек? Это аннулирует текущий чек.',
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.reset_fiscal_check()
            self.cart = []
            self.update_cart_table()
            self.current_check_open = False
            self.update_status()

    def close_fiscal_check(self):
        if not self.current_check_open or len(self.cart) == 0:
            QMessageBox.warning(self, 'Предупреждение', 'Нет открытого чека или он пуст')
            return
        # Запросим сумму и тип оплаты
        total = sum(item['price'] * item['quantity'] for item in self.cart)
        payment_type, ok = QInputDialog.getItem(self, 'Тип оплаты', 'Выберите способ:', ['Наличные', 'Безналичные'], 0, False)
        if not ok:
            return
        pay_type = 0 if payment_type == 'Наличные' else 1
        resp = KKMClient.close_check(self.session_key, pay_type, total)
        if resp.get('result') == 0:
            # Записываем продажи в БД
            for item in self.cart:
                self.db.add_sale({
                    'sale_date': datetime.now().isoformat(),
                    'goods_id': item['id'],
                    'goods_name': item['name'],
                    'quantity': item['quantity'],
                    'unit': item['unit'],
                    'price': item['price'],
                    'total': item['price'] * item['quantity'],
                    'tax_code': item['tax_code'],
                    'payment_type': 'наличные' if pay_type == 0 else 'безналичные',
                    'check_number': resp.get('checkNumber'),
                    'shift_number': self.shift_number,
                    'cashier_name': self.cashier_name
                })
            self.current_check_open = False
            self.cart = []
            self.update_cart_table()
            QMessageBox.information(self, 'Успех', 'Чек закрыт, оплата принята')
        else:
            QMessageBox.critical(self, 'Ошибка', f"Не удалось закрыть чек: {resp.get('errorDescription')}")
        self.update_status()

    def reset_fiscal_check(self):
        if not self.current_check_open:
            return
        resp = KKMClient.reset_check(self.session_key)
        if resp.get('result') == 0:
            self.current_check_open = False
            self.cart = []
            self.update_cart_table()
            QMessageBox.information(self, 'Успех', 'Чек аннулирован')
        else:
            QMessageBox.critical(self, 'Ошибка', f"Не удалось аннулировать чек: {resp.get('errorDescription')}")
        self.update_status()

    def print_text(self):
        if not self.ensure_session():
            return
        text, ok = QInputDialog.getMultiLineText(self, 'Печать текста', 'Введите текст для печати:')
        if ok and text:
            resp = KKMClient.print_text(self.session_key, text)
            if resp.get('result') == 0:
                QMessageBox.information(self, 'Успех', 'Текст напечатан')
            else:
                QMessageBox.critical(self, 'Ошибка', f"Не удалось напечатать текст: {resp.get('errorDescription')}")

    # ---------- ТАБЛИЦА КОРЗИНЫ ----------
    def update_cart_table(self):
        self.cart_table.setRowCount(len(self.cart))
        for i, item in enumerate(self.cart):
            self.cart_table.setItem(i, 0, QTableWidgetItem(str(item['id'])))
            self.cart_table.setItem(i, 1, QTableWidgetItem(item['name']))
            self.cart_table.setItem(i, 2, QTableWidgetItem(str(item['quantity'])))
            self.cart_table.setItem(i, 3, QTableWidgetItem(item['unit']))
            self.cart_table.setItem(i, 4, QTableWidgetItem(f"{item['price']:.2f}"))
            self.cart_table.setItem(i, 5, QTableWidgetItem(f"{item['price'] * item['quantity']:.2f}"))
        self.update_status()

    def update_cart_buttons(self):
        self.update_status()

    # ---------- ТОВАРЫ ----------
    def load_goods(self):
        type_filter = self.goods_filter_type.currentData()
        search = self.goods_filter_search.text().strip()
        goods = self.db.get_goods(type_filter, search)
        self.goods_table.setRowCount(len(goods))
        for i, g in enumerate(goods):
            self.goods_table.setItem(i, 0, QTableWidgetItem(str(g['id'])))
            self.goods_table.setItem(i, 1, QTableWidgetItem(g['name']))
            self.goods_table.setItem(i, 2, QTableWidgetItem(g['type']))
            self.goods_table.setItem(i, 3, QTableWidgetItem(g['unit']))
            self.goods_table.setItem(i, 4, QTableWidgetItem(f"{g['price']:.2f}"))
            self.goods_table.setItem(i, 5, QTableWidgetItem(str(g['tax_code'])))

    def add_goods_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle('Добавить товар')
        layout = QFormLayout(dialog)
        name_edit = QLineEdit()
        type_combo = QComboBox()
        type_combo.addItems(['товар', 'услуга'])
        unit_combo = QComboBox()
        units = ['шт', 'кг', 'г', 'л', 'мл', 'м', 'см', 'упак', 'набор', 'усл_ед']
        unit_combo.addItems(units)
        price_edit = QDoubleSpinBox()
        price_edit.setRange(0, 999999)
        price_edit.setPrefix('₽ ')
        tax_combo = QComboBox()
        rates = self.db.get_tax_rates()
        for r in rates:
            tax_combo.addItem(f"{r['name']} ({r['rate']}%)", r['code'])
        layout.addRow('Наименование:', name_edit)
        layout.addRow('Тип:', type_combo)
        layout.addRow('Ед.изм.:', unit_combo)
        layout.addRow('Цена:', price_edit)
        layout.addRow('Ставка НДС:', tax_combo)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        if dialog.exec_() == QDialog.Accepted:
            name = name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, 'Ошибка', 'Введите наименование')
                return
            type_ = type_combo.currentText()
            unit = unit_combo.currentText()
            price = price_edit.value()
            tax_code = tax_combo.currentData()
            self.db.add_goods(name, type_, unit, price, tax_code)
            self.load_goods()
            QMessageBox.information(self, 'Успех', 'Товар добавлен')

    def edit_goods_dialog(self):
        row = self.goods_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите товар для редактирования')
            return
        id_ = int(self.goods_table.item(row, 0).text())
        goods = self.db.get_goods()[row]  # упрощённо, лучше по id
        # Найдём товар по id
        goods = next((g for g in self.db.get_goods() if g['id'] == id_), None)
        if not goods:
            return
        dialog = QDialog(self)
        dialog.setWindowTitle('Редактировать товар')
        layout = QFormLayout(dialog)
        name_edit = QLineEdit(goods['name'])
        type_combo = QComboBox()
        type_combo.addItems(['товар', 'услуга'])
        type_combo.setCurrentText(goods['type'])
        unit_combo = QComboBox()
        units = ['шт', 'кг', 'г', 'л', 'мл', 'м', 'см', 'упак', 'набор', 'усл_ед']
        unit_combo.addItems(units)
        unit_combo.setCurrentText(goods['unit'])
        price_edit = QDoubleSpinBox()
        price_edit.setRange(0, 999999)
        price_edit.setPrefix('₽ ')
        price_edit.setValue(goods['price'])
        tax_combo = QComboBox()
        rates = self.db.get_tax_rates()
        for r in rates:
            tax_combo.addItem(f"{r['name']} ({r['rate']}%)", r['code'])
        tax_combo.setCurrentIndex(tax_combo.findData(goods['tax_code']))
        layout.addRow('Наименование:', name_edit)
        layout.addRow('Тип:', type_combo)
        layout.addRow('Ед.изм.:', unit_combo)
        layout.addRow('Цена:', price_edit)
        layout.addRow('Ставка НДС:', tax_combo)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        if dialog.exec_() == QDialog.Accepted:
            name = name_edit.text().strip()
            if not name:
                QMessageBox.warning(self, 'Ошибка', 'Введите наименование')
                return
            type_ = type_combo.currentText()
            unit = unit_combo.currentText()
            price = price_edit.value()
            tax_code = tax_combo.currentData()
            self.db.update_goods(id_, name, type_, unit, price, tax_code)
            self.load_goods()
            QMessageBox.information(self, 'Успех', 'Товар обновлён')

    def delete_goods(self):
        row = self.goods_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, 'Предупреждение', 'Выберите товар для удаления')
            return
        id_ = int(self.goods_table.item(row, 0).text())
        reply = QMessageBox.question(self, 'Удаление', 'Удалить выбранный товар?',
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.delete_goods(id_)
            self.load_goods()
            QMessageBox.information(self, 'Успех', 'Товар удалён')

    def import_goods_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, 'Выберите CSV-файл', '', 'CSV files (*.csv)')
        if not file_path:
            return
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        count = self.db.import_goods_csv(content)
        self.load_goods()
        QMessageBox.information(self, 'Успех', f'Импортировано {count} товаров')

    def export_goods_csv(self):
        type_filter = self.goods_filter_type.currentData()
        csv_data = self.db.export_goods_csv(type_filter)
        file_path, _ = QFileDialog.getSaveFileName(self, 'Сохранить CSV', 'goods.csv', 'CSV files (*.csv)')
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(csv_data)
            QMessageBox.information(self, 'Успех', 'Экспорт выполнен')

    # ---------- ПРОДАЖИ ----------
    def load_sales(self):
        filters = {}
        type_filter = self.sales_filter_type.currentData()
        if type_filter:
            filters['goods_type'] = type_filter
        date_from = self.sales_filter_date_from.date().toString('yyyy-MM-dd')
        date_to = self.sales_filter_date_to.date().toString('yyyy-MM-dd')
        filters['date_from'] = date_from
        filters['date_to'] = date_to
        sum_from = self.sales_filter_sum_from.value()
        if sum_from > 0:
            filters['sum_from'] = sum_from
        sum_to = self.sales_filter_sum_to.value()
        if sum_to > 0:
            filters['sum_to'] = sum_to
        payment = self.sales_filter_payment.currentData()
        if payment:
            filters['payment_type'] = payment
        sales = self.db.get_sales(filters)
        summary = self.db.get_sales_summary(filters)
        # Обновим сводку
        self.lbl_sales_count.setText(f'Кол-во: {summary["count"]}')
        self.lbl_sales_sum.setText(f'Сумма: {summary["sum"]:.2f}')
        self.lbl_sales_cash.setText(f'Наличные: {summary["cash"]:.2f}')
        self.lbl_sales_non_cash.setText(f'Безналичные: {summary["non_cash"]:.2f}')
        # Таблица
        self.sales_table.setRowCount(len(sales))
        for i, s in enumerate(sales):
            self.sales_table.setItem(i, 0, QTableWidgetItem(s['sale_date']))
            self.sales_table.setItem(i, 1, QTableWidgetItem(s['goods_name']))
            self.sales_table.setItem(i, 2, QTableWidgetItem(s.get('goods_type', '')))
            self.sales_table.setItem(i, 3, QTableWidgetItem(str(s['quantity'])))
            self.sales_table.setItem(i, 4, QTableWidgetItem(s['unit']))
            self.sales_table.setItem(i, 5, QTableWidgetItem(f"{s['price']:.2f}"))
            self.sales_table.setItem(i, 6, QTableWidgetItem(f"{s['total']:.2f}"))
            self.sales_table.setItem(i, 7, QTableWidgetItem(s['payment_type']))
            self.sales_table.setItem(i, 8, QTableWidgetItem(s['cashier_name'] or ''))

    def export_sales_csv(self):
        # Формируем фильтры аналогично load_sales
        filters = {}
        type_filter = self.sales_filter_type.currentData()
        if type_filter:
            filters['goods_type'] = type_filter
        date_from = self.sales_filter_date_from.date().toString('yyyy-MM-dd')
        date_to = self.sales_filter_date_to.date().toString('yyyy-MM-dd')
        filters['date_from'] = date_from
        filters['date_to'] = date_to
        sum_from = self.sales_filter_sum_from.value()
        if sum_from > 0:
            filters['sum_from'] = sum_from
        sum_to = self.sales_filter_sum_to.value()
        if sum_to > 0:
            filters['sum_to'] = sum_to
        payment = self.sales_filter_payment.currentData()
        if payment:
            filters['payment_type'] = payment
        sales = self.db.get_sales(filters)
        if not sales:
            QMessageBox.information(self, 'Информация', 'Нет данных для экспорта')
            return
        file_path, _ = QFileDialog.getSaveFileName(self, 'Сохранить CSV', 'sales.csv', 'CSV files (*.csv)')
        if not file_path:
            return
        import csv
        with open(file_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.writer(f, delimiter=';')
            writer.writerow(['Дата', 'Товар', 'Тип', 'Кол-во', 'Ед.', 'Цена', 'Сумма', 'Оплата', 'Кассир'])
            for s in sales:
                writer.writerow([
                    s['sale_date'],
                    s['goods_name'],
                    s.get('goods_type', ''),
                    s['quantity'],
                    s['unit'],
                    f"{s['price']:.2f}",
                    f"{s['total']:.2f}",
                    s['payment_type'],
                    s['cashier_name'] or ''
                ])
        QMessageBox.information(self, 'Успех', 'Экспорт выполнен')

    # ---------- СТИЛЬ ----------
    def apply_style(self):
        style = """
        QMainWindow {
            background-color: #f5f6fa;
        }
        QGroupBox {
            font-weight: bold;
            border: 1px solid #d0d3d9;
            border-radius: 6px;
            margin-top: 10px;
            padding-top: 10px;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 10px;
            padding: 0 5px 0 5px;
            background-color: #f5f6fa;
        }
        QPushButton {
            background-color: #3498db;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 12px;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
        QPushButton:pressed {
            background-color: #1f618d;
        }
        QPushButton:disabled {
            background-color: #bdc3c7;
            color: #7f8c8d;
        }
        QTableWidget {
            background-color: white;
            alternate-background-color: #f8f9fa;
            selection-background-color: #d6eaf8;
            gridline-color: #d0d3d9;
        }
        QTableWidget::item {
            padding: 4px;
        }
        QHeaderView::section {
            background-color: #e8ecf1;
            padding: 4px;
            border: 1px solid #d0d3d9;
            font-weight: bold;
        }
        QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit {
            border: 1px solid #d0d3d9;
            border-radius: 4px;
            padding: 4px;
            background-color: white;
        }
        QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus, QDateEdit:focus {
            border-color: #3498db;
        }
        QTabWidget::pane {
            border: 1px solid #d0d3d9;
            border-radius: 4px;
            background-color: white;
        }
        QTabBar::tab {
            background-color: #e8ecf1;
            padding: 6px 12px;
            margin-right: 2px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
        }
        QTabBar::tab:selected {
            background-color: #3498db;
            color: white;
        }
        QTabBar::tab:hover:!selected {
            background-color: #d0d3d9;
        }
        """
        self.setStyleSheet(style)

    def closeEvent(self, event):
        self.db.close()
        event.accept()

# ============================ ЗАПУСК ============================
def main():
    app = QApplication(sys.argv)
    app.setStyle(QStyleFactory.create('Fusion'))
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()