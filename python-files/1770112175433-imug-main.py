import sys
import sqlite3
import csv
import re
from datetime import date as dt, datetime
from PyQt6 import uic
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLineEdit, QMessageBox,
                             QDateEdit, QInputDialog, QFileDialog, QHeaderView)
from PyQt6.QtGui import QStandardItem, QStandardItemModel, QIcon
from PyQt6.QtCore import QDate
from email_validator import validate_email, EmailNotValidError
from pathlib import Path
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle
import matplotlib.pyplot as plt
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from io import BytesIO

# окно авторизации
class Auth(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('auth.ui', self)
        self.setWindowTitle('Авторизация')
        self.setWindowIcon(QIcon('icon.ico'))

        self.loginBtn.clicked.connect(self.loginbtn)
        self.registerBtn.clicked.connect(self.regBtn)
        self.PswdLine.setEchoMode(QLineEdit.EchoMode.Password)

    # функция входа в систему
    def loginbtn(self):
        global mail
        global password

        mail = self.MailLine.text()
        password = self.PswdLine.text()
        triggers = []

        if mail == '':
            triggers.append("Введите почту")
        if password == '':
            triggers.append("Введите пароль")
        if triggers:
            QMessageBox.warning(self, "Ошибка", "\n".join(triggers))
            triggers.clear()

        result = self.login(mail, password)

        if result is True:
            self.menu_open()
        elif result is False:
            QMessageBox.warning(self, "Ошибка", "Неверный пароль.")
        else:
            QMessageBox.warning(self, "Ошибка", "Пользователь не найден.")

    # функция открытия меню
    def menu_open(self):
        self.close()
        self.menu_window = Menu()
        self.menu_window.show()

    # функция обращения к бд с целью проверки правильности введённых данных
    def login(self, mail, password):
        try:
            con = sqlite3.connect("database.sqlite")
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE mail = ?", (mail,))
            user = cur.fetchone()

            if user is None:
                con.close()
                return None

            cur.execute("SELECT * FROM users WHERE mail = ? AND password = ?",
                        (mail, password))
            user = cur.fetchone()

        except sqlite3.Error as e:
            print("[INFO] SQLITE3 ERROR:", str(e))
        finally:
            con.close()

        if user:
            return True
        else:
            return False

    # функция регистрации
    def regBtn(self):
        global mail
        global password

        mail = self.MailLine.text()
        password = self.PswdLine.text()
        triggers = []

        if mail == '':
            triggers.append("Введите почту")

        if password == '':
            triggers.append("Введите пароль")

        if triggers:
            QMessageBox.warning(self, "Ошибка", "\n".join(triggers))
            return

        triggers.clear()
        # проверка почты на валидность через email-validator
        try:
            valid = validate_email(mail)
            mail = valid.normalized
        except EmailNotValidError:
            triggers.append("Введите верную почту.")

        if len(password) < 8:
            triggers.append("Пароль должен содержать минимум 8 символов.")

        if not re.search(r"[A-Z]", password):
            triggers.append("Пароль должен содержать заглавные буквы.")

        if not re.search(r"[a-z]", password):
            triggers.append("Пароль должен содержать строчные буквы.")

        if not re.search(r"[0-9]", password):
            triggers.append("Пароль должен содержать хотя бы одну цифру.")

        if re.search(r"\s", password):
            triggers.append("Пароль не должен содержать пробелы.")

        if triggers:
            QMessageBox.warning(self, "Ошибка", "\n".join(triggers))
            return

        try:
            con = sqlite3.connect("database.sqlite")
            cur = con.cursor()
            cur.execute("SELECT * FROM users WHERE mail = ?", (mail,))
            user = cur.fetchone()

            if user is None:
                self.open_register_form()
            else:
                QMessageBox.warning(self, "Ошибка", "Почта уже используется.")
        except sqlite3.Error as e:
            print("[INFO] SQLITE3 ERROR:", str(e))
        finally:
            con.close()

    def open_register_form(self):
        self.close()
        self.register_window = Register()
        self.register_window.show()


# окно регистрации
class Register(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('register.ui', self)
        self.setWindowTitle('Регистрация')
        self.setWindowIcon(QIcon('icon.ico'))

        self.registerBtn.clicked.connect(self.register)
        self.balanceLine.setText('0')
        self.nameLine.setPlaceholderText('Введите имя')

    # функция регистрации
    def register(self):
        name = self.nameLine.text()
        balance = self.balanceLine.text()
        triggers = []

        if name == '':
            triggers.append("Введите имя")

        if balance == '':
            triggers.append("Введите баланс или поставьте 0")

        if triggers:
            QMessageBox.warning(self, "Ошибка", "\n".join(triggers))
            return
        triggers.clear()

        if name.isalpha() is False:
            triggers.append("Имя должно содержать только буквы")
        elif re.search(r'[^\d\s.]', balance):
            triggers.append('Баланс может содержать только цифры и "."')

        if triggers:
            QMessageBox.warning(self, "Ошибка", "\n".join(triggers))
            triggers.clear()
            return
        else:
            self.adduser(name, balance, mail, password)
            self.success_message()

    # вывод сообщения об успешной регистрации и открытия окна авторизации
    def success_message(self):
        registration_message = "Успешно! Теперь Вы можете войти в систему."
        answer = QMessageBox.information(self, "Успех",
                                         registration_message,
                                         QMessageBox.StandardButton.Ok)
        if answer == QMessageBox.StandardButton.Ok:
            self.close()
            self.open_window = Auth()
            self.open_window.show()

    # обращение к бд для регистрации пользователя
    def adduser(self, name, balance, mail, password):
        try:
            con = sqlite3.connect("database.sqlite")
            cur = con.cursor()

            cur.execute("INSERT INTO users (mail, password, name, balance) VALUES (?, ?, ?, ?)",
                        (mail, password, name, float(balance)))
        except sqlite3.Error as e:
            print("[INFO_adduser] SQLITE3 ERROR:", str(e))
        finally:
            con.commit()
            con.close()

# окно меню
class Menu(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('menu.ui', self)
        self.setWindowTitle('Меню')
        self.setWindowIcon(QIcon('icon.ico'))

        global name, balance, user_id

        con = sqlite3.connect("database.sqlite")
        cur = con.cursor()
        cur.execute("SELECT name FROM users WHERE mail = ?", (mail,))
        name = cur.fetchone()[0]
        cur.execute("SELECT balance FROM users WHERE mail = ?", (mail,))
        balance = cur.fetchone()[0]
        cur.execute("SELECT id FROM users WHERE mail = ?", (mail,))
        user_id = cur.fetchone()[0]
        con.close()

        date_now = dt.today()

        self.amountLine.setPlaceholderText('Сумма')
        self.commentLine.setPlaceholderText('Комментарий')
        self.balance.setText(f'Баланс: {balance}')
        self.dateEdit.setDate(QDate(date_now))
        self.dateEdit.setButtonSymbols(QDateEdit.ButtonSymbols.NoButtons)
        self.searchLine.setPlaceholderText('Запрос')
        self.searchbtn.clicked.connect(self.search)
        self.updateBtn.clicked.connect(self.update_data)
        self.addIncome.clicked.connect(self.add_income)
        self.addExp.clicked.connect(self.add_expenses)
        self.cfg.clicked.connect(self.open_settings)
        self.analyz.clicked.connect(self.open_analytics)
        self.operations.setSortingEnabled(True)
        self.model = QStandardItemModel(self.operations)
        self.operations.setModel(self.model)
        self.operations.setAlternatingRowColors(True)
        self.operations.verticalHeader().setVisible(False)
        self.operations.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.model.setHorizontalHeaderLabels(['Тип', 'Сумма', 'Категория', 'Дата', 'Комментарий'])

        self.update_data()

    # функция обновления данных
    def update_data(self):
        con = sqlite3.connect("database.sqlite")
        cur = con.cursor()
        try:
            cur.execute(
                "SELECT type, amount, category, date, comment FROM operations WHERE user_id = ? ORDER BY date DESC",
                (user_id,))
            records = cur.fetchall()
            self.operations.doubleClicked.connect(self.delete_record)
            self.model.clear()
            self.model.setHorizontalHeaderLabels(['Тип', 'Сумма', 'Категория', 'Дата', 'Комментарий'])
            if records:
                for record in records:
                    row = [QStandardItem(str(field)) for field in record]
                    self.model.appendRow(row)
            else:
                self.model.appendRow([QStandardItem("Записей нету :(")])
                self.operations.doubleClicked.disconnect()
            cur.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
            balance = cur.fetchone()[0]
            self.balance.setText(f'Баланс: {balance} ₽')
        except sqlite3.Error as e:
            print("[INFO] SQLITE3 ERROR:", str(e))
        finally:
            con.close()
            self.commentLine.setText('')
            self.amountLine.setText('')

    # функция удаления записи
    def delete_record(self, index):
        global balance
        con = sqlite3.connect("database.sqlite")
        cur = con.cursor()
        item_type = self.model.item(index.row(), 0)
        self.amount = float(self.model.item(index.row(), 1).text())
        item_category = self.model.item(index.row(), 2)
        item_date = self.model.item(index.row(), 3)
        self.type = item_type.text()
        self.category = item_category.text()
        self.date = item_date.text()

        balance = float(cur.execute('SELECT balance FROM users WHERE id=?', (user_id,)).fetchone()[0])

        if self.type == 'Доход' and (balance < float(self.amount)):
            QMessageBox.warning(self, 'Ошибка',
                                'При удалении данной записи баланс станет отрицательным.\nУдаление невозможно!',
                                QMessageBox.StandardButton.Ok)
            con.close()
            return

        self.reply = QMessageBox.question(self, 'Подтверждение удаления',
                                          'Вы уверены, что хотите удалить эту запись?',
                                          QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if self.reply == QMessageBox.StandardButton.Yes:
            try:
                cur.execute('DELETE FROM operations WHERE user_id=? AND type=? AND amount=? AND category=? AND date=?',
                            (user_id, self.type, self.amount, self.category, self.date))

                if self.type == 'Расход':
                    balance += float(self.amount)
                elif self.type == 'Доход':
                    balance -= float(self.amount)

                cur.execute('UPDATE users SET balance = ? WHERE id = ?', (balance, user_id))
                con.commit()

            except sqlite3.Error as e:
                print("[INFO_delete_record] SQLITE3 ERROR:", str(e))
                QMessageBox.warning(self, 'Ошибка', 'Произошла ошибка при удалении записи.')

            finally:
                con.close()
                self.update_data()

    # функция поиска информации
    def search(self):
        search_text = self.searchLine.text()
        search_type = self.searchInfo.currentText()

        if len(search_text) == 0:
            QMessageBox.warning(self, "Ошибка", 'Строка "запрос" не может быть пустой')
            return
        if search_type == 'Дата':
            self.search_request = 'SELECT type, amount, category, date, comment FROM operations WHERE user_id = ? and date = ? ORDER BY date DESC'
            self.args = (user_id, str(search_text))
        elif search_type == 'Категория':
            self.search_request = 'SELECT type, amount, category, date, comment FROM operations WHERE user_id = ? and category = ? ORDER BY date DESC'
            self.args = (user_id, str(search_text))
        elif search_type == 'Сумма':
            self.search_request = 'SELECT type, amount, category, date, comment FROM operations WHERE user_id = ? and amount = ? ORDER BY date DESC'
            self.args = (user_id, float(search_text))
        elif search_type == 'Тип':
            self.search_request = 'SELECT type, amount, category, date, comment FROM operations WHERE user_id = ? and type = ? ORDER BY date DESC'
            self.args = (user_id, str(search_text))
        elif search_type == 'Комментарий':
            self.search_request = 'SELECT type, amount, category, date, comment FROM operations WHERE user_id = ? and comment = ? ORDER BY date DESC'
            self.args = (user_id, str(search_text))

        con = sqlite3.connect("database.sqlite")
        cur = con.cursor()
        try:
            cur.execute(self.search_request, self.args)
            self.model.clear()
            self.model.setHorizontalHeaderLabels(['Тип', 'Сумма', 'Категория', 'Дата', 'Комментарий'])
            records = cur.fetchall()

            if records:
                for record in records:
                    row = [QStandardItem(str(field)) for field in record]
                    self.model.appendRow(row)
            else:
                self.model.appendRow([QStandardItem("Тут пусто(")])
        except sqlite3.Error as e:
            print("[INFO] SQLITE3 ERROR:", str(e))
        finally:
            con.close()
            self.searchLine.setText('')

    # валидатор перед добавлением операции
    def checker(self):
        triggers = []
        global amount, comment, date, balance
        amount = self.amountLine.text()
        comment = self.commentLine.text()
        date = self.dateEdit.date().toString("dd.MM.yyyy")
        con = sqlite3.connect("database.sqlite")
        cur = con.cursor()
        cur.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
        balance = cur.fetchone()[0]
        if re.search(r'[^\d\s.]', amount) or amount == '':
            triggers.append('Сумма может содержать только число')
        if comment == '':
            triggers.append('Введите комментарий')

        if triggers:
            QMessageBox.warning(self, "Ошибка", "\n".join(triggers))
            triggers.clear()
            return False

        if float(amount) <= 0:
            QMessageBox.warning(self, "Ошибка", "Сумма операции не может быть меньше или равна нулю.")
            return False

    # добавление дохода
    def add_income(self):
        if self.checker() is False:
            return

        try:
            with open("category_income.txt", "r", encoding="utf-8") as file:
                categories = [category.strip() for category in file.readlines()]
        except Exception as e:
            print("[INFO] FILE ERROR:", str(e))
        finally:
            file.close()

        category, status = QInputDialog.getItem(
            self, "Выбор категории", "Выберите категорию", categories, 1, False)
        if status:
            self.operations_request(float(amount), comment, 'Доход', category, date, balance)

    # добавление расхода
    def add_expenses(self):
        if self.checker() is False:
            return

        if balance < float(amount):
            QMessageBox.warning(self, "Ошибка", "Сумма операции не может быть больше баланса.")
            return

        try:
            with open("category_exp.txt", "r", encoding="utf-8") as file:
                categories = [category.strip() for category in file.readlines()]
        except Exception as e:
            print("[INFO] FILE ERROR:", str(e))
        finally:
            file.close()

        category, status = QInputDialog.getItem(
            self, "Выбор категории", "Выберите категорию", categories, 1, False)
        if status:
            self.operations_request(float(amount), comment, 'Расход', category, date, balance)

    # функция, запрос к бд на добавление операции
    def operations_request(self, amount, comment, type, categories, date, balance):
        con = sqlite3.connect("database.sqlite")
        cur = con.cursor()
        try:
            cur.execute(
                'INSERT INTO operations(amount, comment, type, category, date, user_id) VALUES(?, ?, ?, ?, ?, ?)',
                (amount, comment, type, categories, date, user_id))
            if type == 'Доход':
                balance += amount
            elif type == 'Расход':
                balance -= amount
            cur.execute('UPDATE users SET balance = ? WHERE id = ?', (balance, user_id))
        except sqlite3.Error as e:
            print("[INFO] SQLITE3 ERROR:", str(e))
        finally:
            con.commit()
            con.close()
            self.update_data()

    # открытие настроек
    def open_settings(self):
        self.close()
        self.settings = Settings()
        self.settings.show()

    # открытие аналитики
    def open_analytics(self):
        self.close()
        self.analytics = Analytics()
        self.analytics.show()

# окно настроек
class Settings(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('settings.ui', self)
        self.setWindowTitle('Настройки')
        self.setWindowIcon(QIcon('icon.ico'))

        self.saveBtn.clicked.connect(self.save)
        self.backBtn.clicked.connect(self.open_menu)
        self.exportBtn.clicked.connect(self.export)
        self.ImportBtn.clicked.connect(self.import_sqlite)
        # открытие категорий трат и расходов
        try:
            categories_income_file = open('category_income.txt', 'r', encoding='utf8')
            categories_income = categories_income_file.read()
            self.Text_income.setPlainText(categories_income)
            categories_exp_file = open('category_exp.txt', 'r', encoding='utf8')
            categories_exp = categories_exp_file.read()
            self.Text_exp.setPlainText(categories_exp)
        except Exception as e:
            print("[INFO] FILE ERROR:", str(e))

    # функция открытия меню
    def open_menu(self):
        self.close()
        self.menu_wind = Menu()
        self.menu_wind.show()

    # экспорт в csv
    def export(self):
        con = sqlite3.connect('database.sqlite')
        cur = con.cursor()

        cur.execute("SELECT type, amount, category, date, comment FROM operations WHERE user_id = ?",
                    (user_id,))

        column_names = [description[0] for description in cur.description]

        default_dir = str(Path.home() / "Documents")
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить CSV файл",
            default_dir,
            "CSV Files (*.csv);;All Files (*)",
            options=QFileDialog.Option.DontUseNativeDialog
        )

        if file_name:
            if not file_name.lower().endswith('.csv'):
                file_name += '.csv'

            with open(file_name, 'w', newline='', encoding='cp1251') as csv_file:
                writer = csv.writer(csv_file, delimiter=';')
                writer.writerow(column_names)
                for row in cur.fetchall():
                    writer.writerow(row)

        con.close()
        QMessageBox.information(self, "Успех",
                                "Экспорт завершён!")

    # импорт из csv в бд
    def import_sqlite(self):
        con = sqlite3.connect('database.sqlite')
        cur = con.cursor()

        options = QFileDialog.Option.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(None, "Выберите CSV файл", "",
                                                   "CSV Files (*.csv);;All Files (*)",
                                                   options=options)

        if file_name:
            with open(file_name, 'r', encoding='cp1251') as csv_file:
                reader = csv.reader(csv_file, delimiter=';')
                next(reader)

                for row in reader:
                    cur.execute(
                        "INSERT INTO operations (type, amount, category, date, comment, user_id) VALUES (?, ?, ?, ?, ?, ?)",
                        (*row, user_id))

        con.commit()
        con.close()
        QMessageBox.information(self, "Успех",
                                "Импорт завершён!")

    # запись категорий
    def save(self):
        expenses = self.Text_exp.toPlainText()
        incomes = self.Text_income.toPlainText()
        try:
            with open('category_exp.txt', 'w', encoding='utf-8') as file:
                file.write(expenses)
            with open('category_income.txt', 'w', encoding='utf-8') as file:
                file.write(incomes)
        except Exception as e:
            print("[ERROR] Ошибка при записи в файл:", str(e))

# аналитика
class Analytics(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi('analytics.ui', self)
        self.setWindowTitle('Авторизация')
        self.setWindowIcon(QIcon('icon.ico'))

        self.backBtn.clicked.connect(self.menu_open)
        self.pdfBtn.clicked.connect(self.generate_pdf)
        self.figure = Figure()
        self.canvas = FigureCanvas(self.figure)

        self.graph.addWidget(self.canvas)
        self.select_period()

# выбор периода
    def select_period(self):
        periods = [
            "Текущий месяц",
            "Прошлый месяц",
            "Весь период"
        ]

        period, ok = QInputDialog.getItem(
            self,
            "Период аналитики",
            "Выберите период:",
            periods,
            0,
            False
        )

        if not ok:
            self.close()
            self.deleteLater()
            self.menu_open()
            return

        if period == "Текущий месяц":
            self.period_sql = "AND substr(date,4,7)=strftime('%m.%Y')"

        elif period == "Прошлый месяц":
            self.period_sql = """
            AND substr(date,4,7)=strftime('%m.%Y','now','-1 month')
            """

        else:
            self.period_sql = ""

        self.load_stats()
        self.show_pie()

# возврат в меню
    def menu_open(self):
        self.close()
        self.menu_window = Menu()
        self.menu_window.show()

# загрузка информации
    def load_stats(self):
        con = sqlite3.connect("database.sqlite")
        cur = con.cursor()

        query = f"""
        SELECT
        SUM(CASE WHEN type='Доход' THEN amount ELSE 0 END),
        SUM(CASE WHEN type='Расход' THEN amount ELSE 0 END)
        FROM operations
        WHERE user_id=? {self.period_sql}
        """

        cur.execute(query, (user_id,))
        income, expense = cur.fetchone()
        con.close()

        income = income or None
        expense = expense or None

        if income is None and expense is None:
            self.analytics_show.setText(
                f"Информация не надена!"
            )
        else:
            self.analytics_show.setText(
                f"Доход: {round(income, 2)} ₽    \n"
                f"Расход: {round(expense, 2)} ₽    \n"
                f"Итог: {round(income - expense, 2)} ₽"
            )

# создание диаграммы
    def show_pie(self):
        con = sqlite3.connect("database.sqlite")
        cur = con.cursor()

        query = f"""
        SELECT category, SUM(amount)
        FROM operations
        WHERE user_id=? AND type='Расход' {self.period_sql}
        GROUP BY category
        """

        cur.execute(query, (user_id,))
        data = cur.fetchall()
        con.close()

        if not data or all(v[1] == 0 for v in data):
            self.figure.clear()
            ax = self.figure.add_subplot(111)
            ax.text(0.5, 0.5, "Нет расходов за выбранный период :(\nПора тратить!",
                    horizontalalignment='center',
                    verticalalignment='center',
                    fontsize=14, color='gray', transform=ax.transAxes)
            ax.axis('off')
            self.canvas.draw()
            return

        labels = [i[0] for i in data]
        values = [i[1] for i in data]

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        ax.pie(values, labels=labels, autopct="%1.1f%%")
        ax.set_title("Расходы по категориям")

        self.canvas.draw()

# генерация пдф отчёт
    def generate_pdf(self):
        con = sqlite3.connect("database.sqlite")
        cur = con.cursor()

        cur.execute("SELECT type, amount, category, date, comment FROM operations WHERE user_id = ?", (user_id,))
        records = cur.fetchall()
        cur.execute("SELECT name FROM users WHERE id = ?", (user_id,))
        username = cur.fetchone()[0]
        con.close()

        if not records:
            QMessageBox.warning(self, "Ошибка", "Нет данных для отчёта!")
            return

        default_dir = str(Path.home() / "Documents")
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            "Сохранить PDF файл",
            default_dir,
            "PDF Files (*.pdf);;All Files (*)",
            options=QFileDialog.Option.DontUseNativeDialog
        )
        if not file_name:
            return
        if not file_name.lower().endswith('.pdf'):
            file_name += '.pdf'

        pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))

        # параметры файла
        c = canvas.Canvas(file_name, pagesize=A4)
        width, height = A4
        c.setFont("DejaVu", 12)
        c.setTitle(f"Финансовый отчёт")
        c.setAuthor(username)
        c.drawString(50, height - 50, f"Аналитика пользователя: {username}")

        dates = [datetime.strptime(r[3], "%d.%m.%Y") for r in records]
        start_date = min(dates).strftime("%d.%m.%Y")
        end_date = max(dates).strftime("%d.%m.%Y")
        period_str = f"Отчёт за период: {start_date} - {end_date}"
        c.drawString(50, height - 70, period_str)

        max_rows = 25
        data_chunks = [records[i:i + max_rows] for i in range(0, len(records), max_rows)]
        y_start = height - 80
        for chunk_index, chunk in enumerate(data_chunks):
            if chunk_index > 0:
                c.showPage()
                c.setFont("DejaVu", 12)
                y_start = height - 50

            data = [["Тип", "Сумма", "Категория", "Дата", "Комментарий"]]
            for row in chunk:
                data.append([str(x) for x in row])

            table = Table(data, colWidths=[70, 70, 100, 80, 180])
            table.setStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, -1), 'DejaVu'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.black)
            ])

            table.wrapOn(c, width, height)
            table_height = 20 * len(data)
            table.drawOn(c, 50, y_start - table_height)

        c.showPage()
        c.setFont("DejaVu", 12)
        c.drawString(50, height - 50, f"Аналитика пользователя: {username}")

        income_data = {}
        expense_data = {}
        total_income = 0
        total_expense = 0

        for r in records:
            amount = float(r[1])
            if r[0] == 'Доход':
                income_data[r[2]] = income_data.get(r[2], 0) + amount
                total_income += amount
            elif r[0] == 'Расход':
                expense_data[r[2]] = expense_data.get(r[2], 0) + amount
                total_expense += amount

        y_pos = height - 80
        graph_width = 220
        graph_height = 220

        if income_data:
            plt.figure(figsize=(6, 6))
            plt.pie(income_data.values(), labels=income_data.keys(), autopct="%1.1f%%")
            plt.title("Доходы по категориям")
            img_buf = BytesIO()
            plt.savefig(img_buf, format='png', dpi=150, bbox_inches='tight')
            plt.close()
            img_buf.seek(0)
            c.drawImage(ImageReader(img_buf), 50, y_pos - graph_height, width=graph_width, height=graph_height)
            y_pos -= graph_height + 20

        if expense_data:
            plt.figure(figsize=(6, 6))
            plt.pie(expense_data.values(), labels=expense_data.keys(), autopct="%1.1f%%")
            plt.title("Расходы по категориям")
            img_buf = BytesIO()
            plt.savefig(img_buf, format='png', dpi=150, bbox_inches='tight')
            plt.close()
            img_buf.seek(0)
            if y_pos - graph_height < 100:
                c.showPage()
                y_pos = height - 50
            c.drawImage(ImageReader(img_buf), 50, y_pos - graph_height, width=graph_width, height=graph_height)
            y_pos -= graph_height + 20

        plt.figure(figsize=(6, 6))
        plt.bar(["Доход", "Расход"], [total_income, total_expense], color=['green', 'red'])
        plt.title("Сравнение доходов и расходов")
        img_buf = BytesIO()
        plt.savefig(img_buf, format='png', dpi=150, bbox_inches='tight')
        plt.close()
        img_buf.seek(0)
        if y_pos - graph_height < 50:
            c.showPage()
            y_pos = height - 50
        c.drawImage(ImageReader(img_buf), 50, y_pos - graph_height, width=graph_width, height=graph_height)

        date_time = datetime.now().strftime("%d.%m.%Y %H:%M")
        c.setFont("DejaVu", 14)
        c.drawString(50, 50, f"Подписано: {username} {date_time}")
        c.drawString(50, 30, f"Отчёт создан программой Financial Accounting System")

        c.save()
        QMessageBox.information(self, "Успех", "PDF отчёт создан!")


# перехват ошибок
def except_hook(cls, exception, traceback):
    sys.__excepthook__(cls, exception, traceback)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    ex = Auth()
    ex.show()
    sys.excepthook = except_hook
    sys.exit(app.exec())
