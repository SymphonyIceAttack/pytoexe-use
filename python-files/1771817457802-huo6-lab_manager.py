import sys
import sqlite3
from datetime import datetime, timedelta
from PyQt6.QtWidgets import *
from PyQt6.QtCore import *
from PyQt6.QtGui import *

# Константы
APP_NAME = "Computer Lab Manager"
AUTHOR = "Кибильдис Сергей Петрович"
GROUP = "ИСиП-31"

# Список студентов
STUDENTS = [
    "Бухаров Данил Максимович", "Вербицкая Надежда Сергеевна", "Гельмель Александр Александрович",
    "Гуйо Максим Анатольевич", "Даутова Алина Раисовна", "Емцев Андрей Александрович",
    "Залевский Егор Алексеевич", "Ильчук Дмитрий Александрович", "Кибильдис Сергей Петрович",
    "Кичко Софья Евгеньевна", "Лексин Иван Владимирович", "Гельмель Максим Алексеевич",
    "Новосельев Алексей Александрович", "Онищенко Константин Владимирович", "Ордеров Ярослав Евгеньевич",
    "Польская Елизавета Николаевна", "Примин Владислав Иванович", "Разамаскин Артём Дмитриевич",
    "Ромашкин Михаил Романович", "Рыкунов Данил Артурович", "Старосвет Валерий Дмитриевич",
    "Темиева Тамина Эминовна", "Ушанёв Даниил Геннадьевич", "Федоренко Максим Дмитриевич",
    "Чиканов Данил Витальевич"
]

# Аудитории
LABS = [
    {"number": "101", "computers": 15, "description": "Лаборатория информатики"},
    {"number": "102", "computers": 12, "description": "Лаборатория программирования"},
    {"number": "103", "computers": 10, "description": "Лаборатория баз данных"},
    {"number": "104", "computers": 16, "description": "Лаборатория вычислительной техники"},
    {"number": "105", "computers": 14, "description": "Лаборатория системного администрирования"},
]


class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect('computer_labs.db')
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.insert_data()

    def create_tables(self):
        # Таблица аудиторий
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS labs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                number TEXT UNIQUE NOT NULL,
                computers_count INTEGER NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'available'
            )
        ''')

        # Таблица студентов
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                group_name TEXT NOT NULL,
                phone TEXT,
                email TEXT
            )
        ''')

        # Таблица компьютеров
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS computers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lab_id INTEGER NOT NULL,
                computer_number INTEGER NOT NULL,
                status TEXT DEFAULT 'working',
                specs TEXT,
                last_maintenance TEXT,
                FOREIGN KEY (lab_id) REFERENCES labs (id)
            )
        ''')

        # Таблица занятий
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS classes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lab_id INTEGER NOT NULL,
                teacher_name TEXT NOT NULL,
                subject TEXT NOT NULL,
                group_name TEXT NOT NULL,
                start_time TEXT NOT NULL,
                end_time TEXT NOT NULL,
                FOREIGN KEY (lab_id) REFERENCES labs (id)
            )
        ''')

        # Таблица бронирований
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lab_id INTEGER NOT NULL,
                student_name TEXT NOT NULL,
                purpose TEXT,
                date TEXT NOT NULL,
                time_start TEXT NOT NULL,
                time_end TEXT NOT NULL,
                status TEXT DEFAULT 'active',
                FOREIGN KEY (lab_id) REFERENCES labs (id)
            )
        ''')

        self.conn.commit()

    def insert_data(self):
        # Проверяем, есть ли данные
        self.cursor.execute("SELECT COUNT(*) FROM labs")
        if self.cursor.fetchone()[0] == 0:
            # Добавляем аудитории
            for lab in LABS:
                self.cursor.execute(
                    "INSERT INTO labs (number, computers_count, description) VALUES (?, ?, ?)",
                    (lab["number"], lab["computers"], lab["description"])
                )

            # Добавляем студентов
            for student in STUDENTS:
                self.cursor.execute(
                    "INSERT INTO students (full_name, group_name, phone, email) VALUES (?, ?, ?, ?)",
                    (student, "ИСиП-31",
                     f"+7 (999) {hash(student) % 1000:03d}-{hash(student) % 100:02d}-{hash(student) % 10:02d}",
                     f"{student.split()[0].lower()}@mail.ru")
                )

            # Добавляем компьютеры
            self.cursor.execute("SELECT id, computers_count FROM labs")
            for lab_id, count in self.cursor.fetchall():
                for i in range(1, count + 1):
                    self.cursor.execute(
                        "INSERT INTO computers (lab_id, computer_number, specs, last_maintenance) VALUES (?, ?, ?, ?)",
                        (lab_id, i, "Intel Core i5, 8GB RAM, 256GB SSD",
                         (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"))
                    )

            # Добавляем тестовые занятия
            today = datetime.now().strftime("%Y-%m-%d")
            tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

            classes_data = [
                (1, "Иванов И.И.", "Программирование", "ИСиП-31", f"{today} 09:00", f"{today} 10:30"),
                (2, "Петрова А.С.", "Базы данных", "ИСиП-32", f"{today} 11:00", f"{today} 12:30"),
            ]

            for data in classes_data:
                self.cursor.execute(
                    "INSERT INTO classes (lab_id, teacher_name, subject, group_name, start_time, end_time) VALUES (?, ?, ?, ?, ?, ?)",
                    data
                )

            self.conn.commit()

    def get_all(self, query, params=None):
        if params:
            self.cursor.execute(query, params)
        else:
            self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_one(self, query, params):
        self.cursor.execute(query, params)
        return self.cursor.fetchone()

    def execute(self, query, params=()):
        self.cursor.execute(query, params)
        self.conn.commit()

    def close(self):
        self.conn.close()


class LoginWindow(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Вход в систему")
        self.setFixedSize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # Заголовок
        title = QLabel(APP_NAME)
        title.setStyleSheet("font-size: 20px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Автор
        author = QLabel(f"{AUTHOR}\n{GROUP}")
        author.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(author)

        layout.addSpacing(20)

        # Поля ввода
        self.login_input = QLineEdit()
        self.login_input.setPlaceholderText("Логин")
        layout.addWidget(self.login_input)

        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Пароль")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password_input)

        layout.addSpacing(20)

        # Кнопки
        btn_layout = QHBoxLayout()

        login_btn = QPushButton("Войти")
        login_btn.clicked.connect(self.login)
        btn_layout.addWidget(login_btn)

        demo_btn = QPushButton("Демо-доступ")
        demo_btn.clicked.connect(self.demo_login)
        btn_layout.addWidget(demo_btn)

        layout.addLayout(btn_layout)

        # Подсказка
        hint = QLabel("admin / admin")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: gray;")
        layout.addWidget(hint)

        self.setLayout(layout)

    def login(self):
        if self.login_input.text() == "admin" and self.password_input.text() == "admin":
            self.open_main_window()
        else:
            QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")

    def demo_login(self):
        self.open_main_window()

    def open_main_window(self):
        self.main_window = MainWindow(self.db)
        self.main_window.show()
        self.close()


class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle(f"{APP_NAME} - {AUTHOR}")
        self.setGeometry(100, 100, 1200, 700)
        self.setup_ui()

    def setup_ui(self):
        # Создаем вкладки
        tabs = QTabWidget()

        # Добавляем вкладки
        tabs.addTab(DashboardWidget(self.db), "Дашборд")
        tabs.addTab(LabsWidget(self.db), "Аудитории")
        tabs.addTab(ComputersWidget(self.db), "Компьютеры")
        tabs.addTab(StudentsWidget(self.db), "Студенты")
        tabs.addTab(ClassesWidget(self.db), "Занятия")
        tabs.addTab(BookingsWidget(self.db), "Бронирования")

        self.setCentralWidget(tabs)

        # Статус бар
        status = QStatusBar()
        status.showMessage(f"Автор: {AUTHOR} | Группа: {GROUP} | {datetime.now().strftime('%d.%m.%Y')}")
        self.setStatusBar(status)


class DashboardWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setup_ui()
        self.update_stats()

    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)

        # Заголовок
        title = QLabel("Статистика системы")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Создаем группу для статистики
        stats_group = QGroupBox("Общая информация")
        stats_layout = QGridLayout()
        stats_layout.setVerticalSpacing(15)
        stats_layout.setHorizontalSpacing(30)

        # Словарь для хранения меток со значениями
        self.stats_labels = {}

        # Список статистики
        stats_items = [
            ("Всего аудиторий:", "labs_count"),
            ("Всего компьютеров:", "comps_count"),
            ("Всего студентов:", "students_count"),
            ("Занятий сегодня:", "classes_today"),
            ("Свободных аудиторий:", "free_labs"),
            ("Компьютеров в ремонте:", "broken_comps"),
        ]

        # Размещаем в сетке (2 колонки)
        for i, (label_text, key) in enumerate(stats_items):
            row = i // 2
            col = (i % 2) * 2

            # Название
            name_label = QLabel(label_text)
            name_label.setStyleSheet("font-size: 12px;")
            stats_layout.addWidget(name_label, row, col)

            # Значение
            value_label = QLabel("0")
            value_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    font-weight: bold;
                    background-color: #f5f5f5;
                    padding: 5px 15px;
                    border-radius: 3px;
                    min-width: 80px;
                }
            """)
            value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            stats_layout.addWidget(value_label, row, col + 1)

            self.stats_labels[key] = value_label

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # Группа для дополнительной информации
        info_group = QGroupBox("Информация о системе")
        info_layout = QVBoxLayout()

        # Текущая дата и время
        self.datetime_label = QLabel()
        self.datetime_label.setStyleSheet("font-size: 12px; padding: 5px;")
        info_layout.addWidget(self.datetime_label)

        # Версия и автор
        version_label = QLabel(f"Версия: 1.0 | Автор: {AUTHOR}")
        version_label.setStyleSheet("font-size: 12px; padding: 5px;")
        info_layout.addWidget(version_label)

        info_group.setLayout(info_layout)
        layout.addWidget(info_group)

        # Кнопка обновления
        refresh_btn = QPushButton("Обновить статистику")
        refresh_btn.clicked.connect(self.update_stats)
        refresh_btn.setFixedHeight(30)
        layout.addWidget(refresh_btn)

        layout.addStretch()
        self.setLayout(layout)

        # Таймер для обновления времени
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)

    def update_datetime(self):
        """Обновление даты и времени"""
        current = QDateTime.currentDateTime()
        self.datetime_label.setText(f"Текущая дата и время: {current.toString('dd.MM.yyyy HH:mm:ss')}")

    def update_stats(self):
        """Обновление статистики"""
        # Получаем данные из базы
        labs_count = len(self.db.get_all("SELECT * FROM labs"))
        comps_count = len(self.db.get_all("SELECT * FROM computers"))
        students_count = len(self.db.get_all("SELECT * FROM students"))

        today = datetime.now().strftime("%Y-%m-%d")
        classes_today = len(self.db.get_all(
            "SELECT * FROM classes WHERE date(start_time) = ?", (today,)
        ))

        free_labs = len(self.db.get_all(
            "SELECT * FROM labs WHERE status = 'available'"
        ))

        broken_comps = len(self.db.get_all(
            "SELECT * FROM computers WHERE status = 'broken'"
        ))

        # Обновляем значения
        self.stats_labels["labs_count"].setText(str(labs_count))
        self.stats_labels["comps_count"].setText(str(comps_count))
        self.stats_labels["students_count"].setText(str(students_count))
        self.stats_labels["classes_today"].setText(str(classes_today))
        self.stats_labels["free_labs"].setText(str(free_labs))
        self.stats_labels["broken_comps"].setText(str(broken_comps))


class LabsWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Кнопки
        btn_layout = QHBoxLayout()

        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self.add_lab)
        btn_layout.addWidget(add_btn)

        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(self.edit_lab)
        btn_layout.addWidget(edit_btn)

        delete_btn = QPushButton("Удалить")
        delete_btn.clicked.connect(self.delete_lab)
        btn_layout.addWidget(delete_btn)

        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_data)
        btn_layout.addWidget(refresh_btn)

        btn_layout.addStretch()
        layout.addLayout(btn_layout)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Номер", "Компьютеров", "Описание", "Статус"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addWidget(self.table)

        self.setLayout(layout)

    def load_data(self):
        labs = self.db.get_all("SELECT * FROM labs ORDER BY number")
        self.table.setRowCount(len(labs))

        for i, lab in enumerate(labs):
            for j, value in enumerate(lab):
                if j == 4:
                    value = "Доступна" if value == "available" else "Занята"
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, j, item)

        self.table.resizeColumnsToContents()

    def add_lab(self):
        dialog = LabDialog(self.db)
        if dialog.exec():
            self.load_data()

    def edit_lab(self):
        current = self.table.currentRow()
        if current < 0:
            QMessageBox.warning(self, "Внимание", "Выберите аудиторию")
            return

        lab_id = int(self.table.item(current, 0).text())
        dialog = LabDialog(self.db, lab_id)
        if dialog.exec():
            self.load_data()

    def delete_lab(self):
        current = self.table.currentRow()
        if current < 0:
            QMessageBox.warning(self, "Внимание", "Выберите аудиторию")
            return

        reply = QMessageBox.question(self, "Подтверждение", "Удалить аудиторию?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            lab_id = int(self.table.item(current, 0).text())
            self.db.execute("DELETE FROM labs WHERE id = ?", (lab_id,))
            self.load_data()


class LabDialog(QDialog):
    def __init__(self, db, lab_id=None):
        super().__init__()
        self.db = db
        self.lab_id = lab_id
        self.setWindowTitle("Редактирование" if lab_id else "Новая аудитория")
        self.setFixedSize(400, 300)
        self.setup_ui()

        if lab_id:
            self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Поля ввода
        layout.addWidget(QLabel("Номер:"))
        self.number = QLineEdit()
        layout.addWidget(self.number)

        layout.addWidget(QLabel("Компьютеров:"))
        self.computers = QSpinBox()
        self.computers.setRange(1, 50)
        self.computers.setValue(15)
        layout.addWidget(self.computers)

        layout.addWidget(QLabel("Описание:"))
        self.desc = QTextEdit()
        self.desc.setMaximumHeight(60)
        layout.addWidget(self.desc)

        layout.addWidget(QLabel("Статус:"))
        self.status = QComboBox()
        self.status.addItems(["Доступна", "Занята"])
        layout.addWidget(self.status)

        # Кнопки
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_data(self):
        lab = self.db.get_one("SELECT * FROM labs WHERE id = ?", (self.lab_id,))
        if lab:
            self.number.setText(lab[1])
            self.computers.setValue(lab[2])
            self.desc.setText(lab[3] if lab[3] else "")
            self.status.setCurrentIndex(0 if lab[4] == "available" else 1)

    def save(self):
        if not self.number.text():
            QMessageBox.warning(self, "Ошибка", "Введите номер")
            return

        status = "available" if self.status.currentIndex() == 0 else "busy"

        if self.lab_id:
            self.db.execute(
                "UPDATE labs SET number = ?, computers_count = ?, description = ?, status = ? WHERE id = ?",
                (self.number.text(), self.computers.value(), self.desc.toPlainText(), status, self.lab_id)
            )
        else:
            self.db.execute(
                "INSERT INTO labs (number, computers_count, description, status) VALUES (?, ?, ?, ?)",
                (self.number.text(), self.computers.value(), self.desc.toPlainText(), status)
            )

        self.accept()


class ComputersWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Фильтр
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Аудитория:"))

        self.filter = QComboBox()
        self.filter.addItem("Все", "all")
        labs = self.db.get_all("SELECT id, number FROM labs")
        for lab_id, number in labs:
            self.filter.addItem(f"Ауд. {number}", lab_id)
        self.filter.currentIndexChanged.connect(self.load_data)
        filter_layout.addWidget(self.filter)

        filter_layout.addStretch()

        edit_btn = QPushButton("Изменить статус")
        edit_btn.clicked.connect(self.edit_computer)
        filter_layout.addWidget(edit_btn)

        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_data)
        filter_layout.addWidget(refresh_btn)

        layout.addLayout(filter_layout)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Аудитория", "№ ПК", "Статус", "Характеристики", "Последнее ТО"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        layout.addWidget(self.table)

        self.setLayout(layout)

    def load_data(self):
        filter_val = self.filter.currentData()

        if filter_val == "all":
            query = """
                SELECT c.id, l.number, c.computer_number, c.status, c.specs, c.last_maintenance
                FROM computers c
                JOIN labs l ON c.lab_id = l.id
                ORDER BY l.number, c.computer_number
            """
            params = None
        else:
            query = """
                SELECT c.id, l.number, c.computer_number, c.status, c.specs, c.last_maintenance
                FROM computers c
                JOIN labs l ON c.lab_id = l.id
                WHERE l.id = ?
                ORDER BY c.computer_number
            """
            params = (filter_val,)

        if params:
            computers = self.db.get_all(query, params)
        else:
            computers = self.db.get_all(query)

        self.table.setRowCount(len(computers))
        for i, comp in enumerate(computers):
            for j, value in enumerate(comp):
                if j == 3:
                    status_text = {
                        "working": "Работает",
                        "broken": "Сломан",
                        "maintenance": "Обслуживание"
                    }.get(value, value)
                    item = QTableWidgetItem(status_text)
                else:
                    item = QTableWidgetItem(str(value) if value else "")
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, j, item)

        self.table.resizeColumnsToContents()

    def edit_computer(self):
        current = self.table.currentRow()
        if current < 0:
            QMessageBox.warning(self, "Внимание", "Выберите компьютер")
            return

        comp_id = int(self.table.item(current, 0).text())
        dialog = ComputerDialog(self.db, comp_id)
        if dialog.exec():
            self.load_data()


class ComputerDialog(QDialog):
    def __init__(self, db, comp_id):
        super().__init__()
        self.db = db
        self.comp_id = comp_id
        self.setWindowTitle("Изменить статус")
        self.setFixedSize(300, 200)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Информация
        self.info_label = QLabel()
        layout.addWidget(self.info_label)

        layout.addSpacing(10)

        # Статус
        layout.addWidget(QLabel("Статус:"))

        self.status = QComboBox()
        self.status.addItems(["Работает", "Сломан", "На обслуживании"])
        layout.addWidget(self.status)

        # Кнопки
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def load_data(self):
        comp = self.db.get_one("""
            SELECT c.id, l.number, c.computer_number, c.status
            FROM computers c
            JOIN labs l ON c.lab_id = l.id
            WHERE c.id = ?
        """, (self.comp_id,))

        if comp:
            self.info_label.setText(f"Компьютер №{comp[2]}, ауд. {comp[1]}")

            status_map = {"working": 0, "broken": 1, "maintenance": 2}
            self.status.setCurrentIndex(status_map.get(comp[3], 0))

    def save(self):
        status_map = {0: "working", 1: "broken", 2: "maintenance"}
        new_status = status_map[self.status.currentIndex()]

        self.db.execute(
            "UPDATE computers SET status = ? WHERE id = ?",
            (new_status, self.comp_id)
        )

        self.accept()


class StudentsWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Заголовок
        title = QLabel(f"Студенты группы {GROUP}")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Кнопки
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_data)
        layout.addWidget(refresh_btn)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "ФИО", "Группа", "Телефон", "Email"])

        layout.addWidget(self.table)

        # Статистика
        self.stats = QLabel()
        layout.addWidget(self.stats)

        self.setLayout(layout)

    def load_data(self):
        students = self.db.get_all("SELECT * FROM students ORDER BY full_name")

        self.table.setRowCount(len(students))
        for i, student in enumerate(students):
            for j, value in enumerate(student):
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, j, item)

        self.table.resizeColumnsToContents()
        self.stats.setText(f"Всего студентов: {len(students)}")


class ClassesWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Фильтр
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Дата:"))

        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        self.date.setCalendarPopup(True)
        self.date.dateChanged.connect(self.load_data)
        filter_layout.addWidget(self.date)

        filter_layout.addStretch()

        add_btn = QPushButton("Добавить")
        add_btn.clicked.connect(self.add_class)
        filter_layout.addWidget(add_btn)

        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_data)
        filter_layout.addWidget(refresh_btn)

        layout.addLayout(filter_layout)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["Аудитория", "Преподаватель", "Предмет", "Группа", "Начало", "Конец"])

        layout.addWidget(self.table)

        self.setLayout(layout)

    def load_data(self):
        date = self.date.date().toString("yyyy-MM-dd")

        query = """
            SELECT l.number, c.teacher_name, c.subject, c.group_name,
                   c.start_time, c.end_time
            FROM classes c
            JOIN labs l ON c.lab_id = l.id
            WHERE date(c.start_time) = ?
            ORDER BY c.start_time
        """

        classes = self.db.get_all(query, (date,))

        self.table.setRowCount(len(classes))
        for i, class_item in enumerate(classes):
            for j, value in enumerate(class_item):
                if j >= 4 and value:
                    value = value.split()[1] if ' ' in value else value
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, j, item)

        self.table.resizeColumnsToContents()

    def add_class(self):
        dialog = ClassDialog(self.db)
        if dialog.exec():
            self.load_data()


class ClassDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Новое занятие")
        self.setFixedSize(400, 350)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Аудитория
        layout.addWidget(QLabel("Аудитория:"))
        self.lab = QComboBox()
        labs = self.db.get_all("SELECT id, number FROM labs ORDER BY number")
        for lab_id, number in labs:
            self.lab.addItem(f"Ауд. {number}", lab_id)
        layout.addWidget(self.lab)

        # Преподаватель
        layout.addWidget(QLabel("Преподаватель:"))
        self.teacher = QLineEdit()
        layout.addWidget(self.teacher)

        # Предмет
        layout.addWidget(QLabel("Предмет:"))
        self.subject = QLineEdit()
        layout.addWidget(self.subject)

        # Группа
        layout.addWidget(QLabel("Группа:"))
        self.group = QLineEdit()
        self.group.setText(GROUP)
        layout.addWidget(self.group)

        # Дата и время
        layout.addWidget(QLabel("Дата:"))
        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate())
        self.date.setCalendarPopup(True)
        layout.addWidget(self.date)

        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("с"))

        self.time_start = QTimeEdit()
        self.time_start.setTime(QTime(9, 0))
        time_layout.addWidget(self.time_start)

        time_layout.addWidget(QLabel("до"))

        self.time_end = QTimeEdit()
        self.time_end.setTime(QTime(10, 30))
        time_layout.addWidget(self.time_end)

        layout.addLayout(time_layout)

        # Кнопки
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Сохранить")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def save(self):
        if not all([self.teacher.text(), self.subject.text(), self.group.text()]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return

        date = self.date.date().toString("yyyy-MM-dd")
        start = self.time_start.time().toString("HH:mm")
        end = self.time_end.time().toString("HH:mm")

        self.db.execute(
            "INSERT INTO classes (lab_id, teacher_name, subject, group_name, start_time, end_time) VALUES (?, ?, ?, ?, ?, ?)",
            (self.lab.currentData(), self.teacher.text(), self.subject.text(),
             self.group.text(), f"{date} {start}", f"{date} {end}")
        )

        self.accept()


class BookingsWidget(QWidget):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Заголовок
        title = QLabel("Бронирование аудиторий")
        title.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(title)

        # Кнопки
        add_btn = QPushButton("Забронировать")
        add_btn.clicked.connect(self.add_booking)
        layout.addWidget(add_btn)

        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.load_data)
        layout.addWidget(refresh_btn)

        # Таблица
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Аудитория", "Студент", "Цель", "Дата", "Время", "Статус"])

        layout.addWidget(self.table)

        self.setLayout(layout)

    def load_data(self):
        query = """
            SELECT b.id, l.number, b.student_name, b.purpose, b.date, 
                   b.time_start || ' - ' || b.time_end, b.status
            FROM bookings b
            JOIN labs l ON b.lab_id = l.id
            ORDER BY b.date, b.time_start
        """

        bookings = self.db.get_all(query)

        self.table.setRowCount(len(bookings))
        for i, booking in enumerate(bookings):
            for j, value in enumerate(booking):
                if j == 6:
                    value = "Активно" if value == "active" else "Завершено"
                item = QTableWidgetItem(str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(i, j, item)

        self.table.resizeColumnsToContents()

    def add_booking(self):
        dialog = BookingDialog(self.db)
        if dialog.exec():
            self.load_data()


class BookingDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Новое бронирование")
        self.setFixedSize(400, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Аудитория
        layout.addWidget(QLabel("Аудитория:"))
        self.lab = QComboBox()
        labs = self.db.get_all("SELECT id, number FROM labs WHERE status = 'available' ORDER BY number")
        for lab_id, number in labs:
            self.lab.addItem(f"Ауд. {number}", lab_id)
        layout.addWidget(self.lab)

        # Студент
        layout.addWidget(QLabel("Студент:"))
        self.student = QComboBox()
        students = self.db.get_all("SELECT full_name FROM students ORDER BY full_name")
        for student in students:
            self.student.addItem(student[0])
        layout.addWidget(self.student)

        # Цель
        layout.addWidget(QLabel("Цель:"))
        self.purpose = QTextEdit()
        self.purpose.setMaximumHeight(60)
        layout.addWidget(self.purpose)

        # Дата
        layout.addWidget(QLabel("Дата:"))
        self.date = QDateEdit()
        self.date.setDate(QDate.currentDate().addDays(1))
        self.date.setCalendarPopup(True)
        layout.addWidget(self.date)

        # Время
        time_layout = QHBoxLayout()
        time_layout.addWidget(QLabel("с"))

        self.time_start = QTimeEdit()
        self.time_start.setTime(QTime(9, 0))
        time_layout.addWidget(self.time_start)

        time_layout.addWidget(QLabel("до"))

        self.time_end = QTimeEdit()
        self.time_end.setTime(QTime(11, 0))
        time_layout.addWidget(self.time_end)

        layout.addLayout(time_layout)

        # Кнопки
        btn_layout = QHBoxLayout()

        save_btn = QPushButton("Забронировать")
        save_btn.clicked.connect(self.save)
        btn_layout.addWidget(save_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def save(self):
        date = self.date.date().toString("yyyy-MM-dd")
        start = self.time_start.time().toString("HH:mm")
        end = self.time_end.time().toString("HH:mm")

        self.db.execute(
            "INSERT INTO bookings (lab_id, student_name, purpose, date, time_start, time_end) VALUES (?, ?, ?, ?, ?, ?)",
            (self.lab.currentData(), self.student.currentText(), self.purpose.toPlainText(), date, start, end)
        )

        self.db.execute("UPDATE labs SET status = 'busy' WHERE id = ?", (self.lab.currentData(),))

        self.accept()


def main():
    app = QApplication(sys.argv)

    db = DatabaseManager()

    login = LoginWindow(db)
    login.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()