import sys
import bcrypt
from datetime import datetime
import os
import re

import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.platypus import Table, TableStyle

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit, QLabel, QFormLayout,
    QDialog, QComboBox, QDateEdit, QSpinBox, QTextEdit, QDoubleSpinBox,
    QMessageBox, QGroupBox, QFrame, QAbstractItemView, QScrollArea
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QPixmap

import psycopg

# ========== КОНФИГУРАЦИЯ БД ==========
DB_CONFIG = {
    'dbname': 'insurance_broker',
    'user': 'postgres',
    'password': '03012006NiKiTa',   # ИЗМЕНИТЕ НА ВАШ ПАРОЛЬ
    'host': 'localhost',
    'port': 5432
}

# ========== РАБОТА С БД ==========
class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.connect()

    def connect(self):
        try:
            self.conn = psycopg.connect(**DB_CONFIG)
            self.conn.autocommit = False
        except Exception as e:
            QMessageBox.critical(None, "Ошибка БД", f"Не удалось подключиться:\n{e}")
            sys.exit(1)

    def execute_query(self, query, params=None, fetch=False, commit=True):
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, params)
                if fetch:
                    return cur.fetchall()
                if commit:
                    self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e

    def close(self):
        if self.conn:
            self.conn.close()

# ========== ИНИЦИАЛИЗАЦИЯ БД ==========
def init_database(db):
    # Таблица клиентов
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS clients (
            id SERIAL PRIMARY KEY,
            first_name TEXT NOT NULL,
            last_name TEXT NOT NULL,
            passport_number TEXT UNIQUE,
            phone TEXT,
            email TEXT,
            address TEXT
        )
    """, commit=True)

    # Таблица страховых компаний
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS insurance_companies (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            registration_number TEXT,
            phone TEXT,
            address TEXT
        )
    """, commit=True)

    # Таблица брокеров
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS brokers (
            id SERIAL PRIMARY KEY,
            name TEXT,
            phone TEXT UNIQUE,
            email TEXT UNIQUE,
            company_id INTEGER REFERENCES insurance_companies(id) ON DELETE CASCADE,
            password_hash TEXT NOT NULL
        )
    """, commit=True)
    for old_col in ['full_name', 'old_full_name', 'old_name']:
        try:
            db.execute_query(f"ALTER TABLE brokers DROP COLUMN IF EXISTS {old_col} CASCADE", commit=True)
        except:
            pass
    db.execute_query("ALTER TABLE brokers ADD COLUMN IF NOT EXISTS name TEXT", commit=True)
    db.execute_query("UPDATE brokers SET name = COALESCE(phone, email) WHERE name IS NULL", commit=True)
    db.execute_query("ALTER TABLE brokers ALTER COLUMN name SET NOT NULL", commit=True)

    # Таблица полисов
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS insurance_policies (
            id SERIAL PRIMARY KEY,
            policy_number TEXT UNIQUE NOT NULL,
            client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
            company_id INTEGER REFERENCES insurance_companies(id) ON DELETE CASCADE,
            type TEXT NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            sum_insured NUMERIC(12,2) NOT NULL,
            status TEXT DEFAULT 'active'
        )
    """, commit=True)
    try:
        db.execute_query("ALTER TABLE insurance_policies ADD COLUMN broker_id INTEGER REFERENCES brokers(id) ON DELETE SET NULL", commit=True)
    except:
        pass
    try:
        db.execute_query("ALTER TABLE insurance_policies ADD COLUMN broker_id INTEGER REFERENCES brokers(id) ON DELETE SET NULL", commit=True)
    except:
        pass

    # Таблица отзывов
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS reviews (
            id SERIAL PRIMARY KEY,
            client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE,
            company_id INTEGER REFERENCES insurance_companies(id) ON DELETE CASCADE,
            review_text TEXT,
            professionalism_score INTEGER CHECK (professionalism_score BETWEEN 1 AND 5),
            review_date DATE NOT NULL
        )
    """, commit=True)

    # Таблица убытков
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS losses (
            id SERIAL PRIMARY KEY,
            policy_id INTEGER REFERENCES insurance_policies(id) ON DELETE CASCADE,
            description TEXT NOT NULL,
            amount NUMERIC(12,2) NOT NULL,
            loss_date DATE NOT NULL
        )
    """, commit=True)

    # Таблица пользователей
    db.execute_query("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'client'
        )
    """, commit=True)

    try:
        db.execute_query("ALTER TABLE users ADD COLUMN client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE", commit=True)
    except:
        pass

    admin_pw = bcrypt.hashpw(b"admin", bcrypt.gensalt()).decode('utf-8')
    db.execute_query(
        "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'admin') ON CONFLICT (username) DO UPDATE SET role='admin'",
        ("admin", admin_pw)
    )

    clients = db.execute_query("SELECT id, passport_number FROM clients WHERE passport_number IS NOT NULL", fetch=True)
    for c in clients:
        cid, passport = c[0], c[1]
        if passport:
            exist = db.execute_query("SELECT id FROM users WHERE username=%s", (passport,), fetch=True)
            if not exist:
                pw_hash = bcrypt.hashpw(b"client", bcrypt.gensalt()).decode('utf-8')
                db.execute_query(
                    "INSERT INTO users (username, password_hash, role, client_id) VALUES (%s, %s, 'client', %s)",
                    (passport, pw_hash, cid)
                )

    brokers = db.execute_query("SELECT id, phone, email FROM brokers", fetch=True)
    for b in brokers:
        phone, email = b[1], b[2]
        username = phone if phone else email
        if username:
            exist = db.execute_query("SELECT id FROM users WHERE username=%s", (username,), fetch=True)
            if not exist:
                pw = db.execute_query("SELECT password_hash FROM brokers WHERE id=%s", (b[0],), fetch=True)
                pw_hash = pw[0][0] if pw else bcrypt.hashpw(b"broker", bcrypt.gensalt()).decode('utf-8')
                db.execute_query(
                    "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'broker')",
                    (username, pw_hash)
                )

# ========== РАСШИФРОВКА НАЗВАНИЙ КОМПАНИЙ ==========
def expand_company_name(short_name):
    if not short_name:
        return short_name
    patterns = {
        r'^ООО\s+': 'Общество с ограниченной ответственностью ',
        r'^ЗАО\s+': 'Закрытое акционерное общество ',
        r'^ПАО\s+': 'Публичное акционерное общество ',
        r'^АО\s+': 'Акционерное общество ',
        r'^ОАО\s+': 'Открытое акционерное общество ',
        r'^ИП\s+': 'Индивидуальный предприниматель ',
    }
    for abbr, full in patterns.items():
        if re.match(abbr, short_name, re.IGNORECASE):
            return re.sub(abbr, full, short_name, flags=re.IGNORECASE)
    return short_name

# ========== ШРИФТ ДЛЯ PDF ==========
font_path = "C:/Windows/Fonts/arial.ttf"
if os.path.exists(font_path):
    try:
        pdfmetrics.registerFont(TTFont('Arial', font_path))
        print("Зарегистрирован шрифт для PDF из", font_path)
    except:
        pass


def print_contract(policy_id, db):
    row = db.execute_query("""
        SELECT p.policy_number, p.type, p.start_date, p.end_date, p.sum_insured, p.status,
               c.first_name, c.last_name, c.passport_number, c.phone, c.email, c.address,
               ic.name, ic.registration_number, ic.phone, ic.address,
               b.name as broker_name
        FROM insurance_policies p
        JOIN clients c ON p.client_id = c.id
        JOIN insurance_companies ic ON p.company_id = ic.id
        LEFT JOIN brokers b ON p.broker_id = b.id
        WHERE p.id = %s
    """, (policy_id,), fetch=True)
    if not row:
        QMessageBox.warning(None, "Ошибка", "Полис не найден")
        return
    r = row[0]
    policy_num = r[0]
    policy_type = r[1]
    start_date = r[2]
    end_date = r[3]
    sum_insured = float(r[4])
    status = r[5]
    client_first = r[6]
    client_last = r[7]
    client_full = f"{client_first} {client_last}"
    passport = r[8] if r[8] else "не указан"
    client_phone = r[9] if r[9] else "не указан"
    client_email = r[10] if r[10] else "не указан"
    client_address = r[11] if r[11] else "не указан"
    company_name = r[12]
    company_full = expand_company_name(company_name)
    company_reg = r[13] if r[13] else "не указан"
    company_phone = r[14] if r[14] else "не указан"
    company_address = r[15] if r[15] else "не указан"
    broker_name = r[16] if r[16] else "брокер не указан"

    # Страховая премия (5% от страховой суммы)
    premium = sum_insured * 0.05

    # Формируем текст в зависимости от типа страхования
    if policy_type == "Авто":
        obj_desc = "транспортное средство"
    elif policy_type == "Медицина":
        obj_desc = "расходы на медицинские услуги"
    elif policy_type == "Имущество":
        obj_desc = "имущество"
    elif policy_type == "Жизнь":
        obj_desc = "жизнь и здоровье"
    else:
        obj_desc = "риски, предусмотренные договором"

    filename = f"contract_{policy_num}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    try:
        c.setFont('Arial', 12)
    except:
        c.setFont('Helvetica', 12)

    # Функция для разбивки длинного текста на строки
    def draw_text_lines(c, text, x, y, max_width, font_size=10, line_spacing=15):
        c.setFont('Arial', font_size)
        words = text.split(' ')
        lines = []
        current_line = ""
        for w in words:
            test_line = current_line + (" " if current_line else "") + w
            if c.stringWidth(test_line, 'Arial', font_size) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = w
        if current_line:
            lines.append(current_line)
        for line in lines:
            c.drawString(x, y, line)
            y -= line_spacing
        return y

    # Функция для создания новой страницы при необходимости
    def new_page_if_needed(y, margin=50):
        if y < margin:
            c.showPage()
            c.setFont('Arial', 12)
            # Нижний колонтитул на новой странице
            c.setFont('Arial', 8)
            c.setFillColor(colors.grey)
            c.drawString(50, 30, f"Страница {c.getPageNumber()} • {datetime.now().strftime('%d.%m.%Y')}")
            c.setFillColor(colors.black)
            return height - 100
        return y

    # ---- Шапка ----
    c.setFillColor(colors.HexColor('#1e466e'))
    c.setFont('Arial', 16)
    c.drawString(50, height-50, "ДОГОВОР СТРАХОВАНИЯ")
    c.setFont('Arial', 12)
    c.setFillColor(colors.black)
    c.drawString(50, height-80, f"№ {policy_num} от {datetime.now().strftime('%d.%m.%Y')}")
    c.line(50, height-90, width-50, height-90)

    y = height - 120

    # ---- 1. СТОРОНЫ ДОГОВОРА ----
    c.setFont('Arial', 12)
    c.drawString(50, y, "1. СТОРОНЫ ДОГОВОРА")
    y -= 25
    text1 = (f"Страховщик: {company_full}, в лице {broker_name}, действующего на основании доверенности, "
             f"именуемый в дальнейшем «Страховщик», с одной стороны, и")
    y = draw_text_lines(c, text1, 70, y, width-100, font_size=10, line_spacing=15)
    y = new_page_if_needed(y)
    text2 = (f"Страхователь: {client_full}, паспорт {passport}, зарегистрированный по адресу: {client_address}, "
             f"телефон {client_phone}, email {client_email}, именуемый в дальнейшем «Страхователь», с другой стороны, "
             f"заключили настоящий Договор о нижеследующем.")
    y = draw_text_lines(c, text2, 70, y, width-100, font_size=10, line_spacing=15)
    y -= 10
    y = new_page_if_needed(y)

    # ---- 2. ПРЕДМЕТ ДОГОВОРА ----
    c.drawString(50, y, "2. ПРЕДМЕТ ДОГОВОРА")
    y -= 25
    text3 = (f"Страховщик обязуется за обусловленную договором плату (страховую премию) при наступлении страхового "
             f"случая выплатить страховое возмещение в пределах страховой суммы, а Страхователь обязуется уплатить "
             f"страховую премию в порядке и сроки, установленные договором.")
    y = draw_text_lines(c, text3, 70, y, width-100, font_size=10, line_spacing=15)
    y = new_page_if_needed(y)
    obj_text = f"Объект страхования: {obj_desc} при наступлении страхового случая: {sum_insured:,.2f} ₽."
    y = draw_text_lines(c, obj_text, 70, y, width-100, font_size=10, line_spacing=15)
    period_text = f"Срок действия договора: с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}."
    y = draw_text_lines(c, period_text, 70, y, width-100, font_size=10, line_spacing=15)
    y -= 10
    y = new_page_if_needed(y)

    # ---- 3. ОБЯЗАННОСТИ И ПРАВА СТРАХОВЩИКА ----
    c.drawString(50, y, "3. ОБЯЗАННОСТИ И ПРАВА СТРАХОВЩИКА")
    y -= 25
    duties1 = [
        "- произвести страховую выплату при наступлении страхового случая;",
        "- не разглашать сведения о Страхователе без его согласия;",
        "- ознакомить Страхователя с условиями страхования."
    ]
    for d in duties1:
        c.drawString(70, y, d)
        y -= 15
        y = new_page_if_needed(y, 60)
    y -= 5
    c.drawString(50, y, "3.2. Страховщик имеет право:")
    y -= 20
    rights1 = [
        "- проверять представленную Страхователем информацию;",
        "- отказать в выплате при наличии умысла Страхователя;",
        "- досрочно расторгнуть договор при неисполнении Страхователем обязательств."
    ]
    for r in rights1:
        c.drawString(70, y, r)
        y -= 15
        y = new_page_if_needed(y, 60)
    y -= 10

    # ---- 4. ОБЯЗАННОСТИ И ПРАВА СТРАХОВАТЕЛЯ ----
    y = new_page_if_needed(y)
    c.drawString(50, y, "4. ОБЯЗАННОСТИ И ПРАВА СТРАХОВАТЕЛЯ")
    y -= 25
    duties2 = [
        "- уплатить страховую премию в размере и сроки, указанные в договоре;",
        "- незамедлительно уведомить Страховщика о наступлении страхового случая;",
        "- предоставить достоверные сведения при заключении договора."
    ]
    for d in duties2:
        c.drawString(70, y, d)
        y -= 15
        y = new_page_if_needed(y, 60)
    y -= 5
    c.drawString(50, y, "4.2. Страхователь имеет право:")
    y -= 20
    rights2 = [
        "- получить страховую выплату при наступлении страхового случая;",
        "- досрочно расторгнуть договор по соглашению сторон;",
        "- требовать изменения условий договора."
    ]
    for r in rights2:
        c.drawString(70, y, r)
        y -= 15
        y = new_page_if_needed(y, 60)
    y -= 10

    # ---- 5. ПЛАТЕЖИ И ПОРЯДОК РАСЧЁТОВ ----
    y = new_page_if_needed(y)
    c.drawString(50, y, "5. ПЛАТЕЖИ И ПОРЯДОК РАСЧЁТОВ")
    y -= 25
    pay_text = (f"Страховая премия составляет {premium:,.2f} ₽ и уплачивается единовременно в течение 5 дней с даты "
                f"подписания договора. Оплата производится на расчётный счёт Страховщика.")
    y = draw_text_lines(c, pay_text, 70, y, width-100, font_size=10, line_spacing=15)
    y -= 15

    # ---- 6. ОТВЕТСТВЕННОСТЬ СТОРОН ----
    y = new_page_if_needed(y)
    c.drawString(50, y, "6. ОТВЕТСТВЕННОСТЬ СТОРОН И ПОРЯДОК ДОСРОЧНОГО ПРЕКРАЩЕНИЯ")
    y -= 25
    resp_text = ("6.1. За неисполнение или ненадлежащее исполнение обязательств стороны несут ответственность "
                 "в соответствии с законодательством РФ.\n6.2. Договор может быть расторгнут досрочно по соглашению "
                 "сторон или в одностороннем порядке при существенном нарушении условий другой стороной.")
    y = draw_text_lines(c, resp_text, 70, y, width-100, font_size=10, line_spacing=15)
    y -= 15

    # ---- 7. ОСОБЫЕ УСЛОВИЯ ----
    y = new_page_if_needed(y)
    c.drawString(50, y, "7. ОСОБЫЕ УСЛОВИЯ")
    y -= 25
    special_text = ("7.1. Все споры по договору решаются путём переговоров, а при недостижении соглашения – в судебном порядке "
                    "по месту нахождения Страховщика.\n7.2. Изменения и дополнения к договору действительны только в письменной форме.")
    y = draw_text_lines(c, special_text, 70, y, width-100, font_size=10, line_spacing=15)
    y -= 15

    # ---- 8. ЗАКЛЮЧИТЕЛЬНЫЕ ПОЛОЖЕНИЯ ----
    y = new_page_if_needed(y)
    c.drawString(50, y, "8. ЗАКЛЮЧИТЕЛЬНЫЕ ПОЛОЖЕНИЯ")
    y -= 25
    final_text = ("8.1. Настоящий договор составлен в двух экземплярах, имеющих равную юридическую силу, по одному для каждой стороны.\n"
                  "8.2. Договор вступает в силу с даты его подписания обеими сторонами.")
    y = draw_text_lines(c, final_text, 70, y, width-100, font_size=10, line_spacing=15)
    y -= 20

    # ---- 9. ДАННЫЕ СТОРОН И ПОДПИСИ ----
    y = new_page_if_needed(y)
    c.drawString(50, y, "9. ДАННЫЕ СТОРОН И ПОДПИСИ")
    y -= 25
    # Левая колонка (Страховщик)
    c.drawString(70, y, f"Страховщик:")
    y -= 15
    c.drawString(70, y, f"{company_full}")
    y -= 15
    c.drawString(70, y, f"Рег. номер: {company_reg}")
    y -= 15
    c.drawString(70, y, f"Телефон: {company_phone}")
    y -= 15
    c.drawString(70, y, f"Адрес: {company_address}")
    y -= 15
    c.drawString(70, y, f"Подпись: ___________")
    y -= 15
    c.drawString(70, y, f"М.П.")
    y -= 25

    # Правая колонка (Страхователь)
    c.drawString(width-250, y+120, f"Страхователь:")
    c.drawString(width-250, y+105, f"{client_full}")
    c.drawString(width-250, y+90, f"Паспорт: {passport}")
    c.drawString(width-250, y+75, f"Телефон: {client_phone}")
    c.drawString(width-250, y+60, f"Email: {client_email}")
    c.drawString(width-250, y+45, f"Подпись: ___________")
    c.drawString(width-250, y+30, f"Дата: ___________")

    # Нижний колонтитул на последней странице
    c.setFont('Arial', 8)
    c.setFillColor(colors.grey)
    c.drawString(50, 30, f"Страница {c.getPageNumber()} • Сформировано автоматически • {datetime.now().strftime('%d.%m.%Y')}")

    c.save()
    QMessageBox.information(None, "Готово", f"Договор сохранён в {filename}")





def generate_loss_act(policy_id, db, loss_ids=None):
    """
    Создаёт PDF-документ "Акт о страховом случае" по полису.
    Если loss_ids не указаны, берутся все убытки по полису.
    """
    # Получаем данные полиса и связанных сторон
    pol_data = db.execute_query("""
        SELECT p.policy_number, p.type, p.start_date, p.end_date, p.sum_insured, p.status,
               c.first_name, c.last_name, c.passport_number, c.phone, c.email, c.address,
               ic.name, ic.registration_number, ic.phone, ic.address,
               b.name as broker_name
        FROM insurance_policies p
        JOIN clients c ON p.client_id = c.id
        JOIN insurance_companies ic ON p.company_id = ic.id
        LEFT JOIN brokers b ON p.broker_id = b.id
        WHERE p.id = %s
    """, (policy_id,), fetch=True)
    if not pol_data:
        QMessageBox.warning(None, "Ошибка", "Полис не найден")
        return None
    r = pol_data[0]
    policy_num = r[0]
    policy_type = r[1]
    start_date = r[2]
    end_date = r[3]
    sum_insured = float(r[4])
    status = r[5]
    client_first = r[6]
    client_last = r[7]
    client_full = f"{client_first} {client_last}"
    passport = r[8] if r[8] else "не указан"
    client_phone = r[9] if r[9] else "не указан"
    client_email = r[10] if r[10] else "не указан"
    client_address = r[11] if r[11] else "не указан"
    company_name = r[12]
    company_full = expand_company_name(company_name)
    company_reg = r[13] if r[13] else "не указан"
    company_phone = r[14] if r[14] else "не указан"
    company_address = r[15] if r[15] else "не указан"
    broker_name = r[16] if r[16] else "брокер не указан"

    # Получаем убытки
    if loss_ids:
        placeholders = ','.join(['%s'] * len(loss_ids))
        losses = db.execute_query(f"""
            SELECT description, amount, loss_date FROM losses WHERE policy_id=%s AND id IN ({placeholders})
            ORDER BY loss_date DESC
        """, (policy_id, *loss_ids), fetch=True)
    else:
        losses = db.execute_query("""
            SELECT description, amount, loss_date FROM losses WHERE policy_id=%s
            ORDER BY loss_date DESC
        """, (policy_id,), fetch=True)
    if not losses:
        QMessageBox.warning(None, "Ошибка", "Нет убытков по данному полису")
        return None

    total_loss = sum(float(l[1]) for l in losses)
    filename = f"loss_act_{policy_num}.pdf"
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4
    try:
        c.setFont('Arial', 12)
    except:
        c.setFont('Helvetica', 12)

    def draw_text_lines(c, text, x, y, max_width, font_size=10, line_spacing=15):
        c.setFont('Arial', font_size)
        words = text.split(' ')
        lines = []
        current_line = ""
        for w in words:
            test_line = current_line + (" " if current_line else "") + w
            if c.stringWidth(test_line, 'Arial', font_size) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = w
        if current_line:
            lines.append(current_line)
        for line in lines:
            c.drawString(x, y, line)
            y -= line_spacing
        return y

    def new_page_if_needed(y, margin=50):
        if y < margin:
            c.showPage()
            c.setFont('Arial', 12)
            c.setFont('Arial', 8)
            c.setFillColor(colors.grey)
            c.drawString(50, 30, f"Страница {c.getPageNumber()} • {datetime.now().strftime('%d.%m.%Y')}")
            c.setFillColor(colors.black)
            return height - 100
        return y

    # Шапка
    c.setFillColor(colors.HexColor('#1e466e'))
    c.setFont('Arial', 16)
    c.drawString(50, height-50, "АКТ О СТРАХОВОМ СЛУЧАЕ")
    c.setFont('Arial', 12)
    c.setFillColor(colors.black)
    c.drawString(50, height-80, f"№ {policy_num} от {datetime.now().strftime('%d.%m.%Y')}")
    c.line(50, height-90, width-50, height-90)

    y = height - 120

    # 1. Стороны
    c.drawString(50, y, "1. СТОРОНЫ")
    y -= 25
    text1 = (f"Страховщик: {company_full}, в лице {broker_name}, действующего на основании доверенности, "
             f"именуемый в дальнейшем «Страховщик»")
    y = draw_text_lines(c, text1, 70, y, width-100, font_size=10, line_spacing=15)
    y = new_page_if_needed(y)
    text2 = (f"Страхователь: {client_full}, паспорт {passport}, зарегистрированный по адресу: {client_address}, "
             f"телефон {client_phone}, email {client_email}, именуемый в дальнейшем «Страхователь»")
    y = draw_text_lines(c, text2, 70, y, width-100, font_size=10, line_spacing=15)
    y -= 10
    y = new_page_if_needed(y)

    # 2. Информация о полисе
    c.drawString(50, y, "2. ИНФОРМАЦИЯ О ПОЛИСЕ")
    y -= 25
    pol_info = f"Номер полиса: {policy_num}, Тип: {policy_type}, Срок действия: с {start_date.strftime('%d.%m.%Y')} по {end_date.strftime('%d.%m.%Y')}, Страховая сумма: {sum_insured:,.2f} ₽"
    y = draw_text_lines(c, pol_info, 70, y, width-100, font_size=10, line_spacing=15)
    y -= 10
    y = new_page_if_needed(y)

    # 3. Описание страхового случая
    c.drawString(50, y, "3. СТРАХОВОЙ СЛУЧАЙ")
    y -= 25
    c.drawString(70, y, "Страховщик обязуется выплатить Страхователю сумму в размере:")
    y -= 20
    c.setFont('Arial', 12)
    c.drawString(90, y, f"{total_loss:,.2f} ₽")
    y -= 25
    c.setFont('Arial', 10)
    c.drawString(70, y, "в связи с наступлением следующих страховых случаев:")
    y -= 20

    for loss in losses:
        desc = loss[0]
        amount = float(loss[1])
        loss_date = loss[2].strftime("%d.%m.%Y") if hasattr(loss[2], 'strftime') else str(loss[2])
        y = draw_text_lines(c, f"- Дата: {loss_date}, Описание: {desc}, Сумма: {amount:,.2f} ₽", 90, y, width-120, font_size=9, line_spacing=15)
        y = new_page_if_needed(y)

    y -= 10
    c.drawString(70, y, f"Общая сумма выплаты: {total_loss:,.2f} ₽")
    y -= 30

    # 4. Подписи
    y = new_page_if_needed(y)
    c.line(100, y, 250, y)
    c.drawString(100, y-10, "Страховщик")
    c.line(width-250, y, width-100, y)
    c.drawString(width-250, y-10, "Страхователь")
    y -= 30
    c.setFont('Arial', 8)
    c.setFillColor(colors.grey)
    c.drawString(50, 30, f"Страница {c.getPageNumber()} • Сформировано автоматически • {datetime.now().strftime('%d.%m.%Y')}")

    c.save()
    return filename



# ========== ОКНО ВХОДА ==========
class LoginDialog(QDialog):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.setWindowTitle("Вход в систему")
        self.setFixedSize(450, 320)
        self.setModal(True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setAttribute(Qt.WA_TranslucentBackground)

        container = QFrame()
        container.setObjectName("loginContainer")
        layout = QVBoxLayout(self)
        layout.addWidget(container)
        layout.setContentsMargins(10, 10, 10, 10)

        inner = QVBoxLayout(container)
        inner.setSpacing(20)
        inner.setContentsMargins(30, 30, 30, 30)

        title = QLabel("🔐 Вход в систему")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("loginTitle")
        inner.addWidget(title)

        form = QFormLayout()
        form.setSpacing(15)
        self.username = QLineEdit()
        self.username.setPlaceholderText("admin / номер паспорта / телефон / email")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.Password)
        self.password.setPlaceholderText("пароль")
        form.addRow("Логин:", self.username)
        form.addRow("Пароль:", self.password)
        inner.addLayout(form)

        self.btn = QPushButton("Войти")
        self.btn.setObjectName("loginButton")
        self.btn.clicked.connect(self.check)
        inner.addWidget(self.btn, alignment=Qt.AlignCenter)

        close_btn = QPushButton("✕")
        close_btn.setObjectName("closeButton")
        close_btn.clicked.connect(self.reject)
        close_btn.setFixedSize(30, 30)
        close_btn.setParent(container)
        close_btn.move(container.width() - 40, 10)

    def resizeEvent(self, event):
        btn = self.findChild(QPushButton, "closeButton")
        if btn:
            btn.move(self.container().width() - 40, 10)
        super().resizeEvent(event)

    def container(self):
        return self.findChild(QFrame, "loginContainer")

    def check(self):
        uname = self.username.text().strip()
        pwd = self.password.text().strip()
        if not uname or not pwd:
            QMessageBox.warning(self, "Ошибка", "Введите логин и пароль")
            return
        res = self.db.execute_query(
            "SELECT id, password_hash, role, client_id FROM users WHERE username = %s",
            (uname,), fetch=True
        )
        if res and bcrypt.checkpw(pwd.encode('utf-8'), res[0][1].encode('utf-8')):
            role = res[0][2]
            client_id = res[0][3]
            company_id = None
            if role == 'broker':
                broker = self.db.execute_query("SELECT company_id FROM brokers WHERE phone=%s OR email=%s", (uname, uname), fetch=True)
                if broker:
                    company_id = broker[0][0]
            self.accept()
            app = QApplication.instance()
            app.user_role = role
            app.user_client_id = client_id
            app.user_company_id = company_id
            return
        broker = self.db.execute_query("SELECT id, phone, email, company_id, password_hash FROM brokers WHERE phone=%s OR email=%s", (uname, uname), fetch=True)
        if broker and bcrypt.checkpw(pwd.encode('utf-8'), broker[0][4].encode('utf-8')):
            exist = self.db.execute_query("SELECT id FROM users WHERE username=%s", (uname,), fetch=True)
            if not exist:
                self.db.execute_query(
                    "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'broker')",
                    (uname, broker[0][4])
                )
            self.accept()
            app = QApplication.instance()
            app.user_role = 'broker'
            app.user_client_id = None
            app.user_company_id = broker[0][3]
            return
        QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль")

# ========== ГЛАВНОЕ ОКНО ==========
class MainWindow(QMainWindow):
    def __init__(self, db, role, client_id, company_id):
        super().__init__()
        self.db = db
        self.role = role
        self.client_id = client_id
        self.company_id = company_id
        self.setWindowTitle("AIS Страховой брокер - " +
            ("Администратор" if role == "admin" else "Брокер" if role == "broker" else "Личный кабинет клиента"))
        self.setGeometry(100, 100, 1300, 800)
        self.setMinimumSize(1000, 600)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)

        central = QFrame()
        central.setObjectName("mainFrame")
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)

        title_bar = QFrame()
        title_bar.setObjectName("titleBar")
        title_bar.setFixedHeight(40)
        title_layout = QHBoxLayout(title_bar)
        title_layout.setContentsMargins(10, 0, 10, 0)
        logo = QLabel("🏢 AIS Страховой брокер")
        logo.setObjectName("logoLabel")
        title_layout.addWidget(logo)
        title_layout.addStretch()
        self.min_btn = QPushButton("─")
        self.min_btn.setFixedSize(30, 30)
        self.min_btn.setObjectName("titleButton")
        self.min_btn.clicked.connect(self.showMinimized)
        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setObjectName("titleCloseButton")
        self.close_btn.clicked.connect(self.close)
        title_layout.addWidget(self.min_btn)
        title_layout.addWidget(self.close_btn)
        main_layout.addWidget(title_bar)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("mainTabWidget")
        main_layout.addWidget(self.tabs)

        if role == "admin":
            self.client_tab = ClientTab(db)
            self.company_tab = CompanyTab(db)
            self.broker_tab = BrokerTab(db)
            self.policy_tab = PolicyTab(db, client_id=None, company_id=None)
            self.review_tab = ReviewTab(db, client_id=None, company_id=None)
            self.loss_tab = LossTab(db, client_id=None, company_id=None)
            self.report_tab = ReportTab(db, client_id=None, company_id=None)
            self.tabs.addTab(self.client_tab, "👥 Клиенты")
            self.tabs.addTab(self.company_tab, "🏢 Компании")
            self.tabs.addTab(self.broker_tab, "👨‍💼 Брокеры")
            self.tabs.addTab(self.policy_tab, "📄 Полисы")
            self.tabs.addTab(self.review_tab, "⭐ Отзывы")
            self.tabs.addTab(self.loss_tab, "⚠️ Убытки")
            self.tabs.addTab(self.report_tab, "📊 Отчёты")
        elif role == "broker":
            self.policy_tab = PolicyTab(db, client_id=None, company_id=company_id)
            self.review_tab = ReviewTab(db, client_id=None, company_id=company_id)
            self.loss_tab = LossTab(db, client_id=None, company_id=company_id)
            self.report_tab = ReportTab(db, client_id=None, company_id=company_id)
            self.tabs.addTab(self.policy_tab, "📄 Полисы компании")
            self.tabs.addTab(self.review_tab, "⭐ Отзывы о компании")
            self.tabs.addTab(self.loss_tab, "⚠️ Убытки")
            self.tabs.addTab(self.report_tab, "📊 Отчёты")
        else:
            # Для клиента – карточки вместо таблиц, без кнопок добавления/удаления
            self.policy_tab = ClientPolicyCardTab(db, client_id)
            self.review_tab = ClientReviewCardTab(db, client_id)
            self.loss_tab = ClientLossCardTab(db, client_id)  # только просмотр
            self.report_tab = ReportTab(db, client_id=client_id, company_id=None)
            self.companies_tab = CompaniesForClientTab(db)
            self.tabs.addTab(self.policy_tab, "📄 Мои полисы")
            self.tabs.addTab(self.review_tab, "⭐ Мои отзывы")
            self.tabs.addTab(self.loss_tab, "⚠️ Мои убытки")
            self.tabs.addTab(self.report_tab, "📊 Мои отчёты")
            self.tabs.addTab(self.companies_tab, "🏢 Страховые компании")

        self.tabs.currentChanged.connect(self.on_tab_changed)
        self.statusBar().setStyleSheet("background-color: #2c2c2c; color: #aaa; padding: 5px;")
        self.statusBar().showMessage("Система готова к работе")

    def on_tab_changed(self, index):
        if self.role == "admin" and self.tabs.tabText(index) == "📊 Отчёты":
            self.report_tab.refresh_selectors()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and hasattr(self, 'drag_pos'):
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

# ========== БАЗОВЫЙ КЛАСС ТАБА ==========
class BaseTab(QWidget):
    def __init__(self, db, client_id=None, company_id=None):
        super().__init__()
        self.db = db
        self.client_id = client_id
        self.company_id = company_id
        self.init_ui()
        self.refresh()

    def init_ui(self):
        pass

    def refresh(self):
        pass

# ---------- КЛИЕНТЫ (АДМИН) ----------
class ClientTab(BaseTab):
    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        search_card = QGroupBox("🔍 Поиск клиентов")
        search_card.setObjectName("card")
        search_layout = QHBoxLayout(search_card)
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Имя, фамилия или паспорт...")
        self.search_btn = QPushButton("🔎 Найти")
        self.search_btn.clicked.connect(self.refresh)
        self.clear_btn = QPushButton("🗑️ Сброс")
        self.clear_btn.clicked.connect(self.clear_search)
        search_layout.addWidget(self.search_edit)
        search_layout.addWidget(self.search_btn)
        search_layout.addWidget(self.clear_btn)
        layout.addWidget(search_card)

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        layout.addWidget(self.table)

        btn_card = QGroupBox("⚙️ Действия")
        btn_card.setObjectName("card")
        btn_layout = QHBoxLayout(btn_card)
        self.add_btn = QPushButton("➕ Добавить")
        self.edit_btn = QPushButton("✏️ Редактировать")
        self.del_btn = QPushButton("🗑️ Удалить")
        self.add_btn.clicked.connect(self.add)
        self.edit_btn.clicked.connect(self.edit)
        self.del_btn.clicked.connect(self.delete)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.del_btn)
        layout.addWidget(btn_card)

    def clear_search(self):
        self.search_edit.clear()
        self.refresh()

    def refresh(self):
        search = self.search_edit.text().strip()
        if search:
            like = f"%{search}%"
            rows = self.db.execute_query(
                "SELECT id, first_name, last_name, passport_number, phone, email FROM clients "
                "WHERE first_name ILIKE %s OR last_name ILIKE %s OR passport_number ILIKE %s "
                "ORDER BY last_name",
                (like, like, like), fetch=True
            )
        else:
            rows = self.db.execute_query(
                "SELECT id, first_name, last_name, passport_number, phone, email FROM clients ORDER BY last_name",
                fetch=True
            )
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Имя", "Фамилия", "Паспорт", "Телефон", "Email"])
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(val) if val else ""))
        self.table.resizeColumnsToContents()

    def get_selected_id(self):
        items = self.table.selectedItems()
        if not items:
            return None
        return int(self.table.item(items[0].row(), 0).text())

    def add(self):
        dlg = ClientDialog(self.db)
        if dlg.exec_():
            self.refresh()

    def edit(self):
        cid = self.get_selected_id()
        if not cid:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента")
            return
        dlg = ClientDialog(self.db, cid)
        if dlg.exec_():
            self.refresh()

    def delete(self):
        cid = self.get_selected_id()
        if not cid:
            return
        if QMessageBox.question(self, "Удаление", "Удалить клиента? Будут удалены все его полисы, отзывы и пользователь.", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.execute_query("DELETE FROM clients WHERE id=%s", (cid,))
            self.refresh()

class ClientDialog(QDialog):
    def __init__(self, db, client_id=None):
        super().__init__()
        self.db = db
        self.client_id = client_id
        self.setWindowTitle("Клиент")
        self.setMinimumWidth(400)
        layout = QFormLayout(self)
        self.first = QLineEdit()
        self.last = QLineEdit()
        self.passport = QLineEdit()
        self.phone = QLineEdit()
        self.email = QLineEdit()
        self.address = QTextEdit()
        self.address.setMaximumHeight(80)
        layout.addRow("Имя:", self.first)
        layout.addRow("Фамилия:", self.last)
        layout.addRow("Паспорт (уникальный):", self.passport)
        layout.addRow("Телефон:", self.phone)
        layout.addRow("Email:", self.email)
        layout.addRow("Адрес:", self.address)
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save)
        layout.addRow(self.save_btn)

        if client_id:
            row = self.db.execute_query(
                "SELECT first_name, last_name, passport_number, phone, email, address FROM clients WHERE id=%s",
                (client_id,), fetch=True
            )
            if row:
                r = row[0]
                self.first.setText(r[0])
                self.last.setText(r[1])
                self.passport.setText(r[2] or "")
                self.phone.setText(r[3] or "")
                self.email.setText(r[4] or "")
                self.address.setPlainText(r[5] or "")

    def save(self):
        if not self.first.text().strip() or not self.last.text().strip():
            QMessageBox.warning(self, "Ошибка", "Имя и фамилия обязательны")
            return
        passport_val = self.passport.text().strip() or None
        if passport_val:
            if self.client_id:
                chk = self.db.execute_query("SELECT id FROM clients WHERE passport_number=%s AND id!=%s", (passport_val, self.client_id), fetch=True)
            else:
                chk = self.db.execute_query("SELECT id FROM clients WHERE passport_number=%s", (passport_val,), fetch=True)
            if chk:
                QMessageBox.warning(self, "Ошибка", "Клиент с таким паспортом уже существует")
                return

        if self.client_id:
            q = """
                UPDATE clients SET first_name=%s, last_name=%s, passport_number=%s,
                phone=%s, email=%s, address=%s WHERE id=%s
            """
            params = (self.first.text().strip(), self.last.text().strip(),
                      passport_val, self.phone.text().strip() or None,
                      self.email.text().strip() or None, self.address.toPlainText().strip() or None,
                      self.client_id)
            self.db.execute_query(q, params)
            if passport_val:
                self.db.execute_query("UPDATE users SET username=%s WHERE client_id=%s", (passport_val, self.client_id))
        else:
            q = """
                INSERT INTO clients (first_name, last_name, passport_number, phone, email, address)
                VALUES (%s,%s,%s,%s,%s,%s)
            """
            params = (self.first.text().strip(), self.last.text().strip(),
                      passport_val, self.phone.text().strip() or None,
                      self.email.text().strip() or None, self.address.toPlainText().strip() or None)
            self.db.execute_query(q, params)
            if passport_val:
                new_id = self.db.execute_query("SELECT id FROM clients WHERE passport_number=%s", (passport_val,), fetch=True)
                if new_id:
                    pw_hash = bcrypt.hashpw(b"client", bcrypt.gensalt()).decode('utf-8')
                    self.db.execute_query(
                        "INSERT INTO users (username, password_hash, role, client_id) VALUES (%s, %s, 'client', %s)",
                        (passport_val, pw_hash, new_id[0][0])
                    )
        self.accept()

# ---------- КОМПАНИИ (АДМИН) ----------
class CompanyTab(BaseTab):
    def init_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ Добавить")
        self.edit_btn = QPushButton("✏️ Редактировать")
        self.del_btn = QPushButton("🗑️ Удалить")
        self.add_btn.clicked.connect(self.add)
        self.edit_btn.clicked.connect(self.edit)
        self.del_btn.clicked.connect(self.delete)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.del_btn)
        layout.addLayout(btn_layout)

    def refresh(self):
        rows = self.db.execute_query("""
            SELECT c.id, c.name, c.registration_number, c.phone, c.address,
                   COALESCE(AVG(r.professionalism_score), 0)
            FROM insurance_companies c
            LEFT JOIN reviews r ON c.id = r.company_id
            GROUP BY c.id ORDER BY c.name
        """, fetch=True)
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Название", "Рег.номер", "Телефон", "Адрес", "Рейтинг"])
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(val) if val else ""))
        self.table.resizeColumnsToContents()

    def get_selected_id(self):
        items = self.table.selectedItems()
        if not items:
            return None
        return int(self.table.item(items[0].row(), 0).text())

    def add(self):
        dlg = CompanyDialog(self.db)
        if dlg.exec_():
            self.refresh()

    def edit(self):
        cid = self.get_selected_id()
        if not cid:
            QMessageBox.warning(self, "Ошибка", "Выберите компанию")
            return
        dlg = CompanyDialog(self.db, cid)
        if dlg.exec_():
            self.refresh()

    def delete(self):
        cid = self.get_selected_id()
        if not cid:
            return
        if QMessageBox.question(self, "Удаление", "Удалить компанию? Будут удалены все связанные полисы, отзывы и брокеры.", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.execute_query("DELETE FROM insurance_companies WHERE id=%s", (cid,))
            self.refresh()

class CompanyDialog(QDialog):
    def __init__(self, db, company_id=None):
        super().__init__()
        self.db = db
        self.company_id = company_id
        self.setWindowTitle("Компания")
        self.setMinimumWidth(400)
        layout = QFormLayout(self)
        self.name = QLineEdit()
        self.reg = QLineEdit()
        self.phone = QLineEdit()
        self.address = QTextEdit()
        self.address.setMaximumHeight(80)
        layout.addRow("Название:", self.name)
        layout.addRow("Рег.номер:", self.reg)
        layout.addRow("Телефон:", self.phone)
        layout.addRow("Адрес:", self.address)
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save)
        layout.addRow(self.save_btn)
        if company_id:
            row = self.db.execute_query(
                "SELECT name, registration_number, phone, address FROM insurance_companies WHERE id=%s",
                (company_id,), fetch=True
            )
            if row:
                r = row[0]
                self.name.setText(r[0])
                self.reg.setText(r[1] or "")
                self.phone.setText(r[2] or "")
                self.address.setPlainText(r[3] or "")

    def save(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "Ошибка", "Название обязательно")
            return
        if self.company_id:
            q = "UPDATE insurance_companies SET name=%s, registration_number=%s, phone=%s, address=%s WHERE id=%s"
            params = (self.name.text().strip(), self.reg.text().strip() or None,
                      self.phone.text().strip() or None, self.address.toPlainText().strip() or None,
                      self.company_id)
        else:
            q = "INSERT INTO insurance_companies (name, registration_number, phone, address) VALUES (%s,%s,%s,%s)"
            params = (self.name.text().strip(), self.reg.text().strip() or None,
                      self.phone.text().strip() or None, self.address.toPlainText().strip() or None)
        self.db.execute_query(q, params)
        self.accept()

# ---------- БРОКЕРЫ (АДМИН) ----------
class BrokerTab(BaseTab):
    def init_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ Добавить брокера")
        self.edit_btn = QPushButton("✏️ Редактировать")
        self.del_btn = QPushButton("🗑️ Удалить")
        self.add_btn.clicked.connect(self.add)
        self.edit_btn.clicked.connect(self.edit)
        self.del_btn.clicked.connect(self.delete)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.del_btn)
        layout.addLayout(btn_layout)

    def refresh(self):
        rows = self.db.execute_query("""
            SELECT b.id, b.name, b.phone, b.email, ic.name, b.company_id
            FROM brokers b
            JOIN insurance_companies ic ON b.company_id = ic.id
            ORDER BY b.name
        """, fetch=True)
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Имя", "Телефон", "Email", "Компания", "Company ID"])
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(val) if val else ""))
        self.table.resizeColumnsToContents()

    def get_selected_id(self):
        items = self.table.selectedItems()
        if not items:
            return None
        return int(self.table.item(items[0].row(), 0).text())

    def add(self):
        dlg = BrokerDialog(self.db)
        if dlg.exec_():
            self.refresh()

    def edit(self):
        bid = self.get_selected_id()
        if not bid:
            QMessageBox.warning(self, "Ошибка", "Выберите брокера")
            return
        dlg = BrokerDialog(self.db, bid)
        if dlg.exec_():
            self.refresh()

    def delete(self):
        bid = self.get_selected_id()
        if not bid:
            return
        if QMessageBox.question(self, "Удаление", "Удалить брокера?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            broker = self.db.execute_query("SELECT phone, email FROM brokers WHERE id=%s", (bid,), fetch=True)
            if broker:
                username = broker[0][0] if broker[0][0] else broker[0][1]
                if username:
                    self.db.execute_query("DELETE FROM users WHERE username=%s", (username,))
            self.db.execute_query("DELETE FROM brokers WHERE id=%s", (bid,))
            self.refresh()

class BrokerDialog(QDialog):
    def __init__(self, db, broker_id=None):
        super().__init__()
        self.db = db
        self.broker_id = broker_id
        self.setWindowTitle("Брокер")
        self.setMinimumWidth(400)
        layout = QFormLayout(self)
        self.name = QLineEdit()
        self.phone = QLineEdit()
        self.email = QLineEdit()
        self.company = QComboBox()
        companies = self.db.execute_query("SELECT id, name FROM insurance_companies ORDER BY name", fetch=True)
        for c in companies:
            self.company.addItem(c[1], c[0])
        layout.addRow("Имя:", self.name)
        layout.addRow("Телефон (логин):", self.phone)
        layout.addRow("Email (логин):", self.email)
        layout.addRow("Компания:", self.company)
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save)
        layout.addRow(self.save_btn)

        if broker_id:
            row = self.db.execute_query("SELECT name, phone, email, company_id FROM brokers WHERE id=%s", (broker_id,), fetch=True)
            if row:
                r = row[0]
                self.name.setText(r[0])
                self.phone.setText(r[1] or "")
                self.email.setText(r[2] or "")
                self.company.setCurrentIndex(self.company.findData(r[3]))

    def save(self):
        if not self.name.text().strip():
            QMessageBox.warning(self, "Ошибка", "Имя обязательно")
            return
        phone_val = self.phone.text().strip() or None
        email_val = self.email.text().strip() or None
        if not phone_val and not email_val:
            QMessageBox.warning(self, "Ошибка", "Укажите телефон или email для входа")
            return
        company_id = self.company.currentData()
        if not company_id:
            QMessageBox.warning(self, "Ошибка", "Выберите компанию")
            return

        if phone_val:
            chk = self.db.execute_query("SELECT id FROM brokers WHERE phone=%s AND id!=%s", (phone_val, self.broker_id if self.broker_id else -1), fetch=True)
            if chk:
                QMessageBox.warning(self, "Ошибка", "Брокер с таким телефоном уже существует")
                return
        if email_val:
            chk = self.db.execute_query("SELECT id FROM brokers WHERE email=%s AND id!=%s", (email_val, self.broker_id if self.broker_id else -1), fetch=True)
            if chk:
                QMessageBox.warning(self, "Ошибка", "Брокер с таким email уже существует")
                return

        if self.broker_id:
            q = "UPDATE brokers SET name=%s, phone=%s, email=%s, company_id=%s WHERE id=%s"
            params = (self.name.text().strip(), phone_val, email_val, company_id, self.broker_id)
            self.db.execute_query(q, params)
            old = self.db.execute_query("SELECT phone, email FROM brokers WHERE id=%s", (self.broker_id,), fetch=True)
            if old:
                old_user = old[0][0] if old[0][0] else old[0][1]
                new_user = phone_val if phone_val else email_val
                if old_user and new_user and old_user != new_user:
                    self.db.execute_query("UPDATE users SET username=%s WHERE username=%s", (new_user, old_user))
        else:
            pw_hash = bcrypt.hashpw(b"broker", bcrypt.gensalt()).decode('utf-8')
            q = "INSERT INTO brokers (name, phone, email, company_id, password_hash) VALUES (%s,%s,%s,%s,%s)"
            params = (self.name.text().strip(), phone_val, email_val, company_id, pw_hash)
            self.db.execute_query(q, params)
            username = phone_val if phone_val else email_val
            if username:
                self.db.execute_query(
                    "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, 'broker') ON CONFLICT (username) DO NOTHING",
                    (username, pw_hash)
                )
        self.accept()

# ---------- ПОЛИСЫ (ДЛЯ АДМИНА И БРОКЕРА) ----------
class PolicyTab(BaseTab):
    def __init__(self, db, client_id, company_id):
        super().__init__(db, client_id, company_id)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(15)

        if self.client_id is None and self.company_id is None:
            search_card = QGroupBox("🔍 Поиск полисов")
            search_card.setObjectName("card")
            search_layout = QHBoxLayout(search_card)
            self.search_edit = QLineEdit()
            self.search_edit.setPlaceholderText("Номер полиса или фамилия клиента...")
            self.search_btn = QPushButton("🔎 Найти")
            self.search_btn.clicked.connect(self.refresh)
            self.clear_btn = QPushButton("🗑️ Сброс")
            self.clear_btn.clicked.connect(self.clear_search)
            search_layout.addWidget(self.search_edit)
            search_layout.addWidget(self.search_btn)
            search_layout.addWidget(self.clear_btn)
            layout.addWidget(search_card)
        else:
            self.search_edit = None

        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

        btn_card = QGroupBox("⚙️ Действия")
        btn_card.setObjectName("card")
        btn_layout = QHBoxLayout(btn_card)
        self.add_btn = QPushButton("➕ Добавить полис")
        self.edit_btn = QPushButton("✏️ Редактировать")
        self.del_btn = QPushButton("🗑️ Удалить")
        self.qr_btn = QPushButton("📱 QR-код")
        self.contract_btn = QPushButton("📄 Договор страхования")
        self.add_btn.clicked.connect(self.add)
        self.edit_btn.clicked.connect(self.edit)
        self.del_btn.clicked.connect(self.delete)
        self.qr_btn.clicked.connect(self.qr)
        self.contract_btn.clicked.connect(self.contract)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.del_btn)
        btn_layout.addWidget(self.qr_btn)
        btn_layout.addWidget(self.contract_btn)
        layout.addWidget(btn_card)

    def clear_search(self):
        if self.search_edit:
            self.search_edit.clear()
            self.refresh()

    def refresh(self):
        if self.client_id is not None:
            rows = self.db.execute_query("""
                SELECT p.id, p.policy_number, c.last_name||' '||c.first_name, ic.name,
                       p.type, p.start_date, p.end_date, p.sum_insured, p.status
                FROM insurance_policies p
                JOIN clients c ON p.client_id = c.id
                JOIN insurance_companies ic ON p.company_id = ic.id
                WHERE p.client_id = %s
                ORDER BY p.id DESC
            """, (self.client_id,), fetch=True)
        elif self.company_id is not None:
            rows = self.db.execute_query("""
                SELECT p.id, p.policy_number, c.last_name||' '||c.first_name, ic.name,
                       p.type, p.start_date, p.end_date, p.sum_insured, p.status
                FROM insurance_policies p
                JOIN clients c ON p.client_id = c.id
                JOIN insurance_companies ic ON p.company_id = ic.id
                WHERE p.company_id = %s
                ORDER BY p.id DESC
            """, (self.company_id,), fetch=True)
        else:
            search = self.search_edit.text().strip() if self.search_edit else ""
            if search:
                like = f"%{search}%"
                rows = self.db.execute_query("""
                    SELECT p.id, p.policy_number, c.last_name||' '||c.first_name, ic.name,
                           p.type, p.start_date, p.end_date, p.sum_insured, p.status
                    FROM insurance_policies p
                    JOIN clients c ON p.client_id = c.id
                    JOIN insurance_companies ic ON p.company_id = ic.id
                    WHERE p.policy_number ILIKE %s OR c.last_name ILIKE %s
                    ORDER BY p.id DESC
                """, (like, like), fetch=True)
            else:
                rows = self.db.execute_query("""
                    SELECT p.id, p.policy_number, c.last_name||' '||c.first_name, ic.name,
                           p.type, p.start_date, p.end_date, p.sum_insured, p.status
                    FROM insurance_policies p
                    JOIN clients c ON p.client_id = c.id
                    JOIN insurance_companies ic ON p.company_id = ic.id
                    ORDER BY p.id DESC
                """, fetch=True)
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(9)
        headers = ["ID", "Номер", "Клиент", "Компания", "Тип", "Начало", "Конец", "Сумма", "Статус"]
        self.table.setHorizontalHeaderLabels(headers)
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))
        self.table.resizeColumnsToContents()

    def get_selected_id(self):
        items = self.table.selectedItems()
        if not items:
            return None
        return int(self.table.item(items[0].row(), 0).text())

    def add(self):
        current_broker_id = None
        if self.company_id is not None:
            # Получаем broker_id текущего пользователя (если он брокер)
            # Для этого нужно в MainWindow при входе брокера сохранять его broker_id
            # Сейчас оставим без автоматической подстановки – брокер выберет себя из списка
            pass
        if self.company_id is not None:
            dlg = PolicyDialog(self.db, client_id=None, company_id=self.company_id, current_broker_id=current_broker_id)
        else:
            dlg = PolicyDialog(self.db, client_id=None, company_id=None, current_broker_id=current_broker_id)
        if dlg.exec_():
            self.refresh()

    def edit(self):
        pid = self.get_selected_id()
        if not pid:
            QMessageBox.warning(self, "Ошибка", "Выберите полис")
            return
        dlg = PolicyDialog(self.db, policy_id=pid, client_id=self.client_id, company_id=self.company_id)
        if dlg.exec_():
            self.refresh()

    def delete(self):
        pid = self.get_selected_id()
        if not pid:
            return
        if QMessageBox.question(self, "Удаление", "Удалить полис?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.execute_query("DELETE FROM insurance_policies WHERE id=%s", (pid,))
            self.refresh()

    def qr(self):
        pid = self.get_selected_id()
        if not pid:
            QMessageBox.warning(self, "Ошибка", "Выберите полис")
            return
        row = self.db.execute_query("""
            SELECT p.policy_number, c.first_name, c.last_name, ic.name, p.type, p.start_date, p.end_date, p.sum_insured
            FROM insurance_policies p
            JOIN clients c ON p.client_id = c.id
            JOIN insurance_companies ic ON p.company_id = ic.id
            WHERE p.id=%s
        """, (pid,), fetch=True)
        if not row:
            return
        r = row[0]
        info = f"Полис: {r[0]}\nКлиент: {r[1]} {r[2]}\nКомпания: {r[3]}\nТип: {r[4]}\nСрок: {r[5]} - {r[6]}\nСумма: {r[7]}"
        img = qrcode.make(info)
        path = "temp_qr.png"
        img.save(path)
        dlg = QDialog(self)
        dlg.setWindowTitle("QR-код")
        layout = QVBoxLayout(dlg)
        pix = QPixmap(path)
        lbl = QLabel()
        lbl.setPixmap(pix.scaled(300, 300, Qt.KeepAspectRatio))
        layout.addWidget(lbl)
        btn = QPushButton("Закрыть")
        btn.clicked.connect(dlg.accept)
        layout.addWidget(btn)
        dlg.exec_()
        os.remove(path)

    def contract(self):
        pid = self.get_selected_id()
        if not pid:
            QMessageBox.warning(self, "Ошибка", "Выберите полис")
            return
        print_contract(pid, self.db)


class PolicyDialog(QDialog):
    def __init__(self, db, policy_id=None, client_id=None, company_id=None, current_broker_id=None):
        super().__init__()
        self.db = db
        self.policy_id = policy_id
        self.client_id = client_id          # фиксированный клиент (для клиентского режима)
        self.company_id = company_id        # фиксированная компания (для брокера)
        self.current_broker_id = current_broker_id
        self.setWindowTitle("Полис")
        self.setMinimumWidth(500)
        layout = QFormLayout(self)
        self.number = QLineEdit()
        self.client_combo = QComboBox()
        self.company_combo = QComboBox()
        self.broker_combo = QComboBox()      # новый комбобокс
        self.type = QComboBox()
        self.type.addItems(["Авто", "Медицина", "Имущество", "Жизнь", "Путешествия"])
        self.start = QDateEdit()
        self.start.setCalendarPopup(True)
        self.start.setDate(QDate.currentDate())
        self.end = QDateEdit()
        self.end.setCalendarPopup(True)
        self.end.setDate(QDate.currentDate().addYears(1))
        self.sum = QDoubleSpinBox()
        self.sum.setMaximum(1e9)
        self.sum.setPrefix("₽ ")
        self.status = QComboBox()
        self.status.addItems(["active", "expired", "cancelled"])

        layout.addRow("Номер полиса:", self.number)
        if client_id is None:
            layout.addRow("Клиент:", self.client_combo)
        if company_id is None:
            layout.addRow("Страховая компания:", self.company_combo)
        layout.addRow("Брокер (заключивший договор):", self.broker_combo)
        layout.addRow("Тип страхования:", self.type)
        layout.addRow("Дата начала:", self.start)
        layout.addRow("Дата окончания:", self.end)
        layout.addRow("Страховая сумма:", self.sum)
        layout.addRow("Статус:", self.status)
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save)
        layout.addRow(self.save_btn)

        # Загрузка клиентов (только для админа)
        if client_id is None:
            clients = self.db.execute_query("SELECT id, first_name, last_name FROM clients ORDER BY last_name", fetch=True)
            for c in clients:
                self.client_combo.addItem(f"{c[1]} {c[2]}", c[0])

        # Загрузка компаний (если не фиксирована)
        if company_id is None:
            companies = self.db.execute_query("SELECT id, name FROM insurance_companies ORDER BY name", fetch=True)
            for comp in companies:
                self.company_combo.addItem(comp[1], comp[0])
            self.company_combo.currentIndexChanged.connect(self.update_brokers_by_company)
        else:
            # Если компания фиксирована, загружаем брокеров этой компании
            brokers = self.db.execute_query("SELECT id, name FROM brokers WHERE company_id=%s ORDER BY name", (company_id,), fetch=True)
            for b in brokers:
                self.broker_combo.addItem(b[1], b[0])
            if self.broker_combo.count() == 0:
                self.broker_combo.addItem("Нет брокеров в этой компании", None)

        # Если редактируем существующий полис
        if policy_id:
            row = self.db.execute_query("""
                SELECT policy_number, client_id, company_id, broker_id, type, start_date, end_date, sum_insured, status
                FROM insurance_policies WHERE id=%s
            """, (policy_id,), fetch=True)
            if row:
                r = row[0]
                self.number.setText(r[0])
                if client_id is None:
                    self.client_combo.setCurrentIndex(self.client_combo.findData(r[1]))
                if company_id is None:
                    self.company_combo.setCurrentIndex(self.company_combo.findData(r[2]))
                # Устанавливаем брокера, если он есть
                if r[3]:
                    idx = self.broker_combo.findData(r[3])
                    if idx >= 0:
                        self.broker_combo.setCurrentIndex(idx)
                self.type.setCurrentText(r[4])
                self.start.setDate(QDate.fromString(str(r[5]), "yyyy-MM-dd"))
                self.end.setDate(QDate.fromString(str(r[6]), "yyyy-MM-dd"))
                self.sum.setValue(float(r[7]))
                self.status.setCurrentText(r[8])

        # Если создаётся новый полис и передан current_broker_id (например, брокер создаёт полис)
        if not policy_id and self.current_broker_id:
            idx = self.broker_combo.findData(self.current_broker_id)
            if idx >= 0:
                self.broker_combo.setCurrentIndex(idx)

        # Если компания уже выбрана (после загрузки данных), обновим брокеров
        if company_id is None and self.company_combo.count() > 0:
            self.update_brokers_by_company()

    def update_brokers_by_company(self):
        company_id = self.company_combo.currentData()
        self.broker_combo.clear()
        if company_id:
            brokers = self.db.execute_query("SELECT id, name FROM brokers WHERE company_id=%s ORDER BY name", (company_id,), fetch=True)
            for b in brokers:
                self.broker_combo.addItem(b[1], b[0])
        if self.broker_combo.count() == 0:
            self.broker_combo.addItem("Нет брокеров в этой компании", None)

    def save(self):
        if not self.number.text().strip():
            QMessageBox.warning(self, "Ошибка", "Номер полиса обязателен")
            return
        if self.client_id is None:
            client_id = self.client_combo.currentData()
            if not client_id:
                QMessageBox.warning(self, "Ошибка", "Выберите клиента")
                return
        else:
            client_id = self.client_id

        if self.company_id is None:
            company_id = self.company_combo.currentData()
            if not company_id:
                QMessageBox.warning(self, "Ошибка", "Выберите страховую компанию")
                return
        else:
            company_id = self.company_id

        broker_id = self.broker_combo.currentData()
        if broker_id is None:
            # Можно оставить NULL, но предупредим
            reply = QMessageBox.question(self, "Брокер не выбран", "Вы не выбрали брокера. Продолжить?", QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return

        if self.start.date() > self.end.date():
            QMessageBox.warning(self, "Ошибка", "Дата окончания должна быть позже даты начала")
            return

        if self.policy_id:
            q = """
                UPDATE insurance_policies SET policy_number=%s, client_id=%s, company_id=%s, broker_id=%s,
                type=%s, start_date=%s, end_date=%s, sum_insured=%s, status=%s WHERE id=%s
            """
            params = (self.number.text().strip(), client_id, company_id, broker_id, self.type.currentText(),
                      self.start.date().toString("yyyy-MM-dd"), self.end.date().toString("yyyy-MM-dd"),
                      self.sum.value(), self.status.currentText(), self.policy_id)
        else:
            q = """
                INSERT INTO insurance_policies (policy_number, client_id, company_id, broker_id, type, start_date, end_date, sum_insured, status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """
            params = (self.number.text().strip(), client_id, company_id, broker_id, self.type.currentText(),
                      self.start.date().toString("yyyy-MM-dd"), self.end.date().toString("yyyy-MM-dd"),
                      self.sum.value(), self.status.currentText())
        self.db.execute_query(q, params)
        self.accept()

# ---------- ОТЗЫВЫ (ДЛЯ АДМИНА И БРОКЕРА) ----------
class ReviewTab(BaseTab):
    def __init__(self, db, client_id, company_id):
        super().__init__(db, client_id, company_id)

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ Добавить отзыв")
        self.del_btn = QPushButton("🗑️ Удалить")
        self.add_btn.clicked.connect(self.add)
        self.del_btn.clicked.connect(self.delete)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.del_btn)
        layout.addLayout(btn_layout)

    def refresh(self):
        if self.client_id is not None:
            rows = self.db.execute_query("""
                SELECT r.id, c.last_name||' '||c.first_name, ic.name, r.professionalism_score, r.review_text, r.review_date
                FROM reviews r
                JOIN clients c ON r.client_id = c.id
                JOIN insurance_companies ic ON r.company_id = ic.id
                WHERE r.client_id = %s
                ORDER BY r.review_date DESC
            """, (self.client_id,), fetch=True)
        elif self.company_id is not None:
            rows = self.db.execute_query("""
                SELECT r.id, c.last_name||' '||c.first_name, ic.name, r.professionalism_score, r.review_text, r.review_date
                FROM reviews r
                JOIN clients c ON r.client_id = c.id
                JOIN insurance_companies ic ON r.company_id = ic.id
                WHERE r.company_id = %s
                ORDER BY r.review_date DESC
            """, (self.company_id,), fetch=True)
        else:
            rows = self.db.execute_query("""
                SELECT r.id, c.last_name||' '||c.first_name, ic.name, r.professionalism_score, r.review_text, r.review_date
                FROM reviews r
                JOIN clients c ON r.client_id = c.id
                JOIN insurance_companies ic ON r.company_id = ic.id
                ORDER BY r.review_date DESC
            """, fetch=True)
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Клиент", "Компания", "Оценка", "Отзыв", "Дата"])
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))
        self.table.resizeColumnsToContents()

    def get_selected_id(self):
        items = self.table.selectedItems()
        if not items:
            return None
        return int(self.table.item(items[0].row(), 0).text())

    def add(self):
        dlg = ReviewDialog(self.db, client_id=self.client_id, company_id=self.company_id)
        if dlg.exec_():
            self.refresh()

    def delete(self):
        rid = self.get_selected_id()
        if not rid:
            return
        if QMessageBox.question(self, "Удаление", "Удалить отзыв?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.execute_query("DELETE FROM reviews WHERE id=%s", (rid,))
            self.refresh()

class ReviewDialog(QDialog):
    def __init__(self, db, client_id=None, company_id=None):
        super().__init__()
        self.db = db
        self.client_id = client_id
        self.company_id = company_id
        self.setWindowTitle("Новый отзыв")
        self.setMinimumWidth(400)
        layout = QFormLayout(self)
        self.client_combo = QComboBox()
        self.company_combo = QComboBox()
        self.score = QSpinBox()
        self.score.setRange(1,5)
        self.text = QTextEdit()
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(QDate.currentDate())

        if client_id is None:
            layout.addRow("Клиент:", self.client_combo)
            clients = self.db.execute_query("SELECT id, first_name, last_name FROM clients", fetch=True)
            for c in clients:
                self.client_combo.addItem(f"{c[1]} {c[2]}", c[0])
        if company_id is None:
            layout.addRow("Компания:", self.company_combo)
            companies = self.db.execute_query("SELECT id, name FROM insurance_companies", fetch=True)
            for comp in companies:
                self.company_combo.addItem(comp[1], comp[0])
        layout.addRow("Оценка (1-5):", self.score)
        layout.addRow("Текст отзыва:", self.text)
        layout.addRow("Дата:", self.date)
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save)
        layout.addRow(self.save_btn)

    def save(self):
        if self.client_id is None:
            client_id = self.client_combo.currentData()
            if not client_id:
                QMessageBox.warning(self, "Ошибка", "Выберите клиента")
                return
        else:
            client_id = self.client_id
        if self.company_id is None:
            company_id = self.company_combo.currentData()
            if not company_id:
                QMessageBox.warning(self, "Ошибка", "Выберите компанию")
                return
        else:
            company_id = self.company_id
        q = "INSERT INTO reviews (client_id, company_id, professionalism_score, review_text, review_date) VALUES (%s,%s,%s,%s,%s)"
        params = (client_id, company_id, self.score.value(), self.text.toPlainText(),
                  self.date.date().toString("yyyy-MM-dd"))
        self.db.execute_query(q, params)
        self.accept()

# ---------- УБЫТКИ (ДЛЯ АДМИНА И БРОКЕРА) ----------
class LossTab(BaseTab):
    def __init__(self, db, client_id, company_id):
        super().__init__(db, client_id, company_id)

    def init_ui(self):
        layout = QVBoxLayout(self)
        self.table = QTableWidget()
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("➕ Добавить убыток")
        self.del_btn = QPushButton("🗑️ Удалить")
        self.add_btn.clicked.connect(self.add)
        self.del_btn.clicked.connect(self.delete)
        btn_layout.addWidget(self.add_btn)
        btn_layout.addWidget(self.del_btn)
        layout.addLayout(btn_layout)

    def refresh(self):
        if self.client_id is not None:
            rows = self.db.execute_query("""
                SELECT l.id, p.policy_number, l.description, l.amount, l.loss_date
                FROM losses l
                JOIN insurance_policies p ON l.policy_id = p.id
                WHERE p.client_id = %s
                ORDER BY l.loss_date DESC
            """, (self.client_id,), fetch=True)
        elif self.company_id is not None:
            rows = self.db.execute_query("""
                SELECT l.id, p.policy_number, l.description, l.amount, l.loss_date
                FROM losses l
                JOIN insurance_policies p ON l.policy_id = p.id
                WHERE p.company_id = %s
                ORDER BY l.loss_date DESC
            """, (self.company_id,), fetch=True)
        else:
            rows = self.db.execute_query("""
                SELECT l.id, p.policy_number, l.description, l.amount, l.loss_date
                FROM losses l
                JOIN insurance_policies p ON l.policy_id = p.id
                ORDER BY l.loss_date DESC
            """, fetch=True)
        self.table.setRowCount(len(rows))
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Полис", "Описание", "Сумма", "Дата"])
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))
        self.table.resizeColumnsToContents()

    def get_selected_id(self):
        items = self.table.selectedItems()
        if not items:
            return None
        return int(self.table.item(items[0].row(), 0).text())

    def add(self):
        dlg = LossDialog(self.db, client_id=self.client_id, company_id=self.company_id)
        if dlg.exec_():
            self.refresh()

    def delete(self):
        lid = self.get_selected_id()
        if not lid:
            return
        if QMessageBox.question(self, "Удаление", "Удалить убыток?", QMessageBox.Yes | QMessageBox.No) == QMessageBox.Yes:
            self.db.execute_query("DELETE FROM losses WHERE id=%s", (lid,))
            self.refresh()

class LossDialog(QDialog):
    def __init__(self, db, client_id=None, company_id=None):
        super().__init__()
        self.db = db
        self.client_id = client_id
        self.company_id = company_id
        self.setWindowTitle("Убыток")
        self.setMinimumWidth(400)
        layout = QFormLayout(self)
        self.policy_combo = QComboBox()
        if client_id is not None:
            policies = self.db.execute_query("SELECT id, policy_number FROM insurance_policies WHERE client_id=%s", (client_id,), fetch=True)
        elif company_id is not None:
            policies = self.db.execute_query("SELECT id, policy_number FROM insurance_policies WHERE company_id=%s", (company_id,), fetch=True)
        else:
            policies = self.db.execute_query("SELECT id, policy_number FROM insurance_policies", fetch=True)
        for p in policies:
            self.policy_combo.addItem(p[1], p[0])
        self.desc = QTextEdit()
        self.amount = QDoubleSpinBox()
        self.amount.setMaximum(1e9)
        self.amount.setPrefix("₽ ")
        self.date = QDateEdit()
        self.date.setCalendarPopup(True)
        self.date.setDate(QDate.currentDate())
        layout.addRow("Полис:", self.policy_combo)
        layout.addRow("Описание:", self.desc)
        layout.addRow("Сумма:", self.amount)
        layout.addRow("Дата убытка:", self.date)
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save)
        layout.addRow(self.save_btn)

    def save(self):
        policy_id = self.policy_combo.currentData()
        if not policy_id:
            QMessageBox.warning(self, "Ошибка", "Выберите полис")
            return
        q = "INSERT INTO losses (policy_id, description, amount, loss_date) VALUES (%s,%s,%s,%s)"
        params = (policy_id, self.desc.toPlainText(), self.amount.value(),
                  self.date.date().toString("yyyy-MM-dd"))
        self.db.execute_query(q, params)
        self.accept()

# ---------- КАРТОЧКИ ПОЛИСОВ ДЛЯ КЛИЕНТА ----------
class ClientPolicyCardTab(BaseTab):
    def __init__(self, db, client_id):
        super().__init__(db, client_id=client_id)

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(15)
        self.scroll.setWidget(self.container)
        self.layout.addWidget(self.scroll)
        self.refresh()

    def refresh(self):
        # Очищаем контейнер
        for i in reversed(range(self.container_layout.count())):
            self.container_layout.itemAt(i).widget().deleteLater()
        rows = self.db.execute_query("""
            SELECT p.id, p.policy_number, ic.name, p.type, p.start_date, p.end_date, p.sum_insured, p.status
            FROM insurance_policies p
            JOIN insurance_companies ic ON p.company_id = ic.id
            WHERE p.client_id = %s
            ORDER BY p.id DESC
        """, (self.client_id,), fetch=True)
        if not rows:
            label = QLabel("У вас нет ни одного полиса")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 14pt; color: #888; padding: 20px;")
            self.container_layout.addWidget(label)
            return
        for pol in rows:
            card = QGroupBox(f"📄 Полис № {pol[1]}")
            card.setObjectName("card")
            card_layout = QFormLayout(card)
            card_layout.addRow("Компания:", QLabel(expand_company_name(pol[2])))
            card_layout.addRow("Тип:", QLabel(pol[3]))
            card_layout.addRow("Дата начала:", QLabel(pol[4].strftime("%d.%m.%Y") if hasattr(pol[4], 'strftime') else str(pol[4])))
            card_layout.addRow("Дата окончания:", QLabel(pol[5].strftime("%d.%m.%Y") if hasattr(pol[5], 'strftime') else str(pol[5])))
            card_layout.addRow("Страховая сумма:", QLabel(f"{float(pol[6]):,.2f} ₽"))
            card_layout.addRow("Статус:", QLabel(pol[7]))
            btn_qr = QPushButton("📱 QR-код")
            btn_qr.clicked.connect(lambda _, pid=pol[0]: self.show_qr(pid))
            btn_contract = QPushButton("📄 Договор страхования")
            btn_contract.clicked.connect(lambda _, pid=pol[0]: print_contract(pid, self.db))
            btn_layout = QHBoxLayout()
            btn_layout.addWidget(btn_qr)
            btn_layout.addWidget(btn_contract)
            card_layout.addRow(btn_layout)
            self.container_layout.addWidget(card)

    def show_qr(self, pid):
        row = self.db.execute_query("""
            SELECT p.policy_number, c.first_name, c.last_name, ic.name, p.type, p.start_date, p.end_date, p.sum_insured
            FROM insurance_policies p
            JOIN clients c ON p.client_id = c.id
            JOIN insurance_companies ic ON p.company_id = ic.id
            WHERE p.id=%s
        """, (pid,), fetch=True)
        if not row:
            return
        r = row[0]
        info = f"Полис: {r[0]}\nКлиент: {r[1]} {r[2]}\nКомпания: {r[3]}\nТип: {r[4]}\nСрок: {r[5]} - {r[6]}\nСумма: {r[7]}"
        img = qrcode.make(info)
        path = "temp_qr.png"
        img.save(path)
        dlg = QDialog(self)
        dlg.setWindowTitle("QR-код")
        layout = QVBoxLayout(dlg)
        pix = QPixmap(path)
        lbl = QLabel()
        lbl.setPixmap(pix.scaled(300, 300, Qt.KeepAspectRatio))
        layout.addWidget(lbl)
        btn = QPushButton("Закрыть")
        btn.clicked.connect(dlg.accept)
        layout.addWidget(btn)
        dlg.exec_()
        os.remove(path)

# ---------- КАРТОЧКИ ОТЗЫВОВ ДЛЯ КЛИЕНТА ----------


class ClientReviewCardTab(BaseTab):
    def __init__(self, db, client_id):
        super().__init__(db, client_id=client_id)

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(15)
        self.scroll.setWidget(self.container)
        self.layout.addWidget(self.scroll)

        add_btn = QPushButton("➕ Добавить отзыв")
        add_btn.clicked.connect(self.add_review)
        self.layout.addWidget(add_btn)

        self.refresh()

    def refresh(self):
        for i in reversed(range(self.container_layout.count())):
            self.container_layout.itemAt(i).widget().deleteLater()
        rows = self.db.execute_query("""
            SELECT r.id, ic.name, r.professionalism_score, r.review_text, r.review_date
            FROM reviews r
            JOIN insurance_companies ic ON r.company_id = ic.id
            WHERE r.client_id = %s
            ORDER BY r.review_date DESC
        """, (self.client_id,), fetch=True)
        if not rows:
            label = QLabel("Вы ещё не оставили ни одного отзыва")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 14pt; color: #888; padding: 20px;")
            self.container_layout.addWidget(label)
            return
        for rev in rows:
            rev_id, company_name, score, text, rev_date = rev
            card = QGroupBox(f"⭐ Отзыв о компании {company_name}")
            card.setObjectName("card")
            card_layout = QFormLayout(card)
            card_layout.addRow("Оценка:", QLabel(f"{score} / 5"))
            card_layout.addRow("Текст отзыва:", QLabel(text if text else "(нет текста)"))
            card_layout.addRow("Дата:", QLabel(rev_date.strftime("%d.%m.%Y") if hasattr(rev_date, 'strftime') else str(rev_date)))
            
            btn_layout = QHBoxLayout()
            edit_btn = QPushButton("✏️ Редактировать")
            edit_btn.clicked.connect(lambda _, rid=rev_id, cur_score=score, cur_text=text: self.edit_review(rid, cur_score, cur_text))
            del_btn = QPushButton("🗑️ Удалить")
            del_btn.clicked.connect(lambda _, rid=rev_id: self.delete_review(rid))
            btn_layout.addWidget(edit_btn)
            btn_layout.addWidget(del_btn)
            card_layout.addRow(btn_layout)
            
            self.container_layout.addWidget(card)

    def edit_review(self, review_id, current_score, current_text):
        dlg = QDialog(self)
        dlg.setWindowTitle("Редактирование отзыва")
        dlg.setMinimumWidth(400)
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        score_spin = QSpinBox()
        score_spin.setRange(1,5)
        score_spin.setValue(current_score)
        text_edit = QTextEdit()
        text_edit.setPlainText(current_text if current_text else "")
        form.addRow("Оценка (1-5):", score_spin)
        form.addRow("Текст отзыва:", text_edit)
        layout.addLayout(form)
        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(lambda: self.save_review(review_id, score_spin.value(), text_edit.toPlainText(), dlg))
        layout.addWidget(btn_save)
        dlg.exec_()

    def save_review(self, review_id, new_score, new_text, dialog):
        self.db.execute_query(
            "UPDATE reviews SET professionalism_score=%s, review_text=%s, review_date=CURRENT_DATE WHERE id=%s",
            (new_score, new_text, review_id)
        )
        dialog.accept()
        self.refresh()
        QMessageBox.information(self, "Успех", "Отзыв обновлён")

    def delete_review(self, review_id):
        reply = QMessageBox.question(self, "Удаление", "Удалить этот отзыв?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.db.execute_query("DELETE FROM reviews WHERE id=%s", (review_id,))
            self.refresh()
            QMessageBox.information(self, "Успех", "Отзыв удалён")

    def add_review(self):
        # Получаем список компаний, на которых у клиента ещё нет отзыва
        companies = self.db.execute_query("""
            SELECT ic.id, ic.name
            FROM insurance_companies ic
            WHERE ic.id NOT IN (
                SELECT company_id FROM reviews WHERE client_id = %s
            )
            ORDER BY ic.name
        """, (self.client_id,), fetch=True)
        if not companies:
            QMessageBox.information(self, "Информация", "Вы уже оставили отзывы на все доступные компании")
            return

        dlg = QDialog(self)
        dlg.setWindowTitle("Новый отзыв")
        dlg.setMinimumWidth(400)
        layout = QVBoxLayout(dlg)
        form = QFormLayout()
        company_combo = QComboBox()
        for comp in companies:
            company_combo.addItem(comp[1], comp[0])
        score_spin = QSpinBox()
        score_spin.setRange(1,5)
        text_edit = QTextEdit()
        form.addRow("Компания:", company_combo)
        form.addRow("Оценка (1-5):", score_spin)
        form.addRow("Текст отзыва:", text_edit)
        layout.addLayout(form)
        btn_save = QPushButton("Сохранить")
        btn_save.clicked.connect(lambda: self.save_new_review(company_combo.currentData(), score_spin.value(), text_edit.toPlainText(), dlg))
        layout.addWidget(btn_save)
        dlg.exec_()

    def save_new_review(self, company_id, score, text, dialog):
        # Дополнительная проверка на случай, если отзыв уже появился за время диалога
        exist = self.db.execute_query("SELECT id FROM reviews WHERE client_id=%s AND company_id=%s", (self.client_id, company_id), fetch=True)
        if exist:
            QMessageBox.warning(self, "Ошибка", "Вы уже оставили отзыв на эту компанию")
            dialog.accept()
            return
        self.db.execute_query(
            "INSERT INTO reviews (client_id, company_id, professionalism_score, review_text, review_date) VALUES (%s,%s,%s,%s,CURRENT_DATE)",
            (self.client_id, company_id, score, text)
        )
        dialog.accept()
        self.refresh()
        QMessageBox.information(self, "Успех", "Отзыв добавлен")

# ---------- КАРТОЧКИ УБЫТКОВ ДЛЯ КЛИЕНТА (ТОЛЬКО ПРОСМОТР) ----------
class ClientLossCardTab(BaseTab):
    def __init__(self, db, client_id):
        super().__init__(db, client_id=client_id)

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(15)
        self.scroll.setWidget(self.container)
        self.layout.addWidget(self.scroll)
        self.refresh()

    def refresh(self):
        for i in reversed(range(self.container_layout.count())):
            self.container_layout.itemAt(i).widget().deleteLater()
        rows = self.db.execute_query("""
            SELECT l.id, p.policy_number, l.description, l.amount, l.loss_date
            FROM losses l
            JOIN insurance_policies p ON l.policy_id = p.id
            WHERE p.client_id = %s
            ORDER BY l.loss_date DESC
        """, (self.client_id,), fetch=True)
        if not rows:
            label = QLabel("У вас нет зарегистрированных убытков")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 14pt; color: #888; padding: 20px;")
            self.container_layout.addWidget(label)
            return
        for loss in rows:
            card = QGroupBox(f"⚠️ Убыток по полису № {loss[1]}")
            card.setObjectName("card")
            card_layout = QFormLayout(card)
            card_layout.addRow("Описание:", QLabel(loss[2]))
            card_layout.addRow("Сумма:", QLabel(f"{float(loss[3]):,.2f} ₽"))
            card_layout.addRow("Дата убытка:", QLabel(loss[4].strftime("%d.%m.%Y") if hasattr(loss[4], 'strftime') else str(loss[4])))
            self.container_layout.addWidget(card)

# ---------- ПРОСМОТР КОМПАНИЙ (ДЛЯ КЛИЕНТА) ----------
class CompaniesForClientTab(BaseTab):
    def __init__(self, db):
        super().__init__(db)

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setSpacing(15)
        self.scroll.setWidget(self.container)
        self.layout.addWidget(self.scroll)
        self.refresh()

    def refresh(self):
        for i in reversed(range(self.container_layout.count())):
            self.container_layout.itemAt(i).widget().deleteLater()
        rows = self.db.execute_query("""
            SELECT c.id, c.name, c.registration_number, c.phone, c.address,
                   COALESCE(AVG(r.professionalism_score), 0) as rating
            FROM insurance_companies c
            LEFT JOIN reviews r ON c.id = r.company_id
            GROUP BY c.id
            ORDER BY c.name
        """, fetch=True)
        if not rows:
            label = QLabel("Нет зарегистрированных страховых компаний")
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet("font-size: 14pt; color: #888; padding: 20px;")
            self.container_layout.addWidget(label)
            return
        for comp in rows:
            card = QGroupBox(f"🏢 {comp[1]}")
            card.setObjectName("card")
            card_layout = QFormLayout(card)
            card_layout.addRow("Регистрационный номер:", QLabel(comp[2] or "—"))
            card_layout.addRow("Телефон:", QLabel(comp[3] or "—"))
            card_layout.addRow("Адрес:", QLabel(comp[4] or "—"))
            card_layout.addRow("Рейтинг:", QLabel(f"{float(comp[5]):.2f} / 5"))
            btn_brokers = QPushButton("👨‍💼 Показать брокеров компании")
            btn_brokers.clicked.connect(lambda _, cid=comp[0], cname=comp[1]: self.show_brokers(cid, cname))
            card_layout.addRow(btn_brokers)
            self.container_layout.addWidget(card)

    def show_brokers(self, company_id, company_name):
        brokers = self.db.execute_query("SELECT name, phone, email FROM brokers WHERE company_id=%s", (company_id,), fetch=True)
        if not brokers:
            QMessageBox.information(self, "Брокеры", f"У компании {company_name} нет закреплённых брокеров")
            return
        dialog = BrokersDialog(brokers, company_name, self)
        dialog.exec_()


class BrokersDialog(QDialog):
    def __init__(self, brokers_data, company_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Брокеры компании {company_name}")
        self.setMinimumSize(600, 400)
        self.setModal(True)
        layout = QVBoxLayout(self)

        title = QLabel(f"👨‍💼 Брокеры компании: {company_name}")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 16pt; font-weight: bold; margin: 10px;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(15)
        scroll.setWidget(container)
        layout.addWidget(scroll)

        if not brokers_data:
            label = QLabel("Нет брокеров")
            label.setAlignment(Qt.AlignCenter)
            container_layout.addWidget(label)
        else:
            for b in brokers_data:
                name, phone, email = b
                card = QGroupBox(f"👤 {name}")
                card.setObjectName("card")
                card_layout = QFormLayout(card)
                if phone:
                    card_layout.addRow("Телефон:", QLabel(phone))
                if email:
                    card_layout.addRow("Email:", QLabel(email))
                container_layout.addWidget(card)

        close_btn = QPushButton("Закрыть")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn, alignment=Qt.AlignCenter)

# ---------- ОТЧЁТЫ (УНИВЕРСАЛЬНЫЕ) ----------
class ReportTab(BaseTab):
    def __init__(self, db, client_id, company_id):
        super().__init__(db, client_id, company_id)

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        if self.client_id is not None:
            self.gen_self_btn = QPushButton("📥 Сформировать сводный отчёт по моим полисам")
            self.gen_self_btn.clicked.connect(self.gen_self_report)
            layout.addWidget(self.gen_self_btn, alignment=Qt.AlignCenter)
            self.gen_self_losses_btn = QPushButton("📥 Сформировать акт о страховых случаях (по всем убыткам)")
            self.gen_self_losses_btn.clicked.connect(self.gen_self_losses_report)
            layout.addWidget(self.gen_self_losses_btn, alignment=Qt.AlignCenter)
        elif self.company_id is not None:
            self.gen_company_btn = QPushButton("📥 Отчёт по всем полисам компании")
            self.gen_company_btn.clicked.connect(self.gen_company_report)
            layout.addWidget(self.gen_company_btn, alignment=Qt.AlignCenter)
            self.gen_company_losses_btn = QPushButton("📥 Отчёт по убыткам компании")
            self.gen_company_losses_btn.clicked.connect(self.gen_company_losses_report)
            layout.addWidget(self.gen_company_losses_btn, alignment=Qt.AlignCenter)
        else:
            self.client_combo = QComboBox()
            self.policy_combo = QComboBox()
            client_card = QGroupBox("📄 Отчёт по клиенту")
            client_card.setObjectName("card")
            client_layout = QVBoxLayout(client_card)
            self.gen_client_btn = QPushButton("Сформировать PDF для клиента")
            self.gen_client_btn.clicked.connect(lambda: self.gen_client_report(None))
            client_layout.addWidget(QLabel("Выберите клиента:"))
            client_layout.addWidget(self.client_combo)
            client_layout.addWidget(self.gen_client_btn)
            layout.addWidget(client_card)

            policy_card = QGroupBox("📑 Акт о страховом случае (по полису)")
            policy_card.setObjectName("card")
            policy_layout = QVBoxLayout(policy_card)
            self.gen_policy_btn = QPushButton("Сформировать акт о страховом случае")
            self.gen_policy_btn.clicked.connect(self.gen_policy_report)
            policy_layout.addWidget(QLabel("Выберите полис:"))
            policy_layout.addWidget(self.policy_combo)
            policy_layout.addWidget(self.gen_policy_btn)
            layout.addWidget(policy_card)

            refresh_btn = QPushButton("🔄 Обновить списки")
            refresh_btn.clicked.connect(self.refresh_selectors)
            layout.addWidget(refresh_btn, alignment=Qt.AlignCenter)
            self.refresh_selectors()

        layout.addStretch()

    def refresh_selectors(self):
        if self.client_id is not None or self.company_id is not None:
            return
        self.client_combo.clear()
        clients = self.db.execute_query("SELECT id, first_name, last_name FROM clients", fetch=True)
        for c in clients:
            self.client_combo.addItem(f"{c[1]} {c[2]}", c[0])
        if len(clients) == 0:
            self.client_combo.addItem("--- нет клиентов ---", None)
        self.policy_combo.clear()
        policies = self.db.execute_query("SELECT id, policy_number FROM insurance_policies", fetch=True)
        for p in policies:
            self.policy_combo.addItem(p[1], p[0])
        if len(policies) == 0:
            self.policy_combo.addItem("--- нет полисов ---", None)

    def _draw_pdf_header_footer(self, pdf, title, subtitle):
        w, h = A4
        try:
            pdf.setFont('Arial', 16)
        except:
            pdf.setFont('Helvetica', 16)
        pdf.setFillColor(colors.HexColor('#1e466e'))
        pdf.drawString(50, h-50, title)
        pdf.setFont('Arial', 14)
        pdf.drawString(50, h-70, subtitle)
        pdf.setFont('Arial', 10)
        pdf.setFillColor(colors.black)
        pdf.drawString(50, h-90, f"Дата формирования: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
        pdf.line(50, h-100, w-50, h-100)
        pdf.setFont('Arial', 8)
        pdf.setFillColor(colors.grey)
        pdf.drawString(50, 30, f"Страница {pdf.getPageNumber()} • Сформировано автоматически • {datetime.now().strftime('%d.%m.%Y')}")

    # ----- Отчёт по клиенту (сводный по всем полисам) -----
    def gen_client_report(self, client_id):
        if client_id is None:
            client_id = self.client_combo.currentData()
        if not client_id:
            QMessageBox.warning(self, "Ошибка", "Выберите клиента")
            return
        client = self.db.execute_query("SELECT first_name, last_name FROM clients WHERE id=%s", (client_id,), fetch=True)
        if not client:
            return
        name = f"{client[0][0]} {client[0][1]}"
        policies = self.db.execute_query("""
            SELECT p.policy_number, ic.name, p.type, p.start_date, p.end_date, p.sum_insured, p.status
            FROM insurance_policies p
            JOIN insurance_companies ic ON p.company_id = ic.id
            WHERE p.client_id=%s
        """, (client_id,), fetch=True)
        filename = f"report_client_{client_id}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        self._draw_pdf_header_footer(c, "СВОДНЫЙ СТРАХОВОЙ ОТЧЁТ", f"по клиенту: {name}")
        w, h = A4
        data = [["№ полиса", "Компания", "Тип", "Начало", "Окончание", "Сумма (₽)", "Статус"]]
        total = 0
        for pol in policies:
            data.append([
                str(pol[0]), expand_company_name(pol[1]), str(pol[2]),
                pol[3].strftime("%d.%m.%Y") if hasattr(pol[3], 'strftime') else pol[3],
                pol[4].strftime("%d.%m.%Y") if hasattr(pol[4], 'strftime') else pol[4],
                f"{float(pol[5]):,.2f}", str(pol[6])
            ])
            total += float(pol[5])
        table = Table(data, colWidths=[55,130,55,65,65,70,50])
        table.setStyle(TableStyle([
            ('FONTNAME',(0,0),(-1,-1),'Arial'),('FONTSIZE',(0,0),(-1,-1),8),
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#d0e4f5')),
            ('GRID',(0,0),(-1,-1),0.5,colors.grey),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f9f9f9')]),
        ]))
        table.wrapOn(c, w-100, h-200)
        table.drawOn(c, 50, h-240 - len(policies)*12)
        y = h-260 - len(policies)*12
        c.setFont('Arial', 10)
        c.drawString(50, y, f"Общая страховая сумма: {total:,.2f} ₽")
        c.save()
        QMessageBox.information(self, "Готово", f"Отчёт сохранён в {filename}")

    # ----- Акт о страховом случае по конкретному полису (для админа/брокера) -----
    def gen_policy_report(self):
        policy_id = self.policy_combo.currentData()
        if not policy_id:
            QMessageBox.warning(self, "Ошибка", "Выберите полис")
            return
        # Получаем данные полиса, компании, клиента, брокера
        pol_data = self.db.execute_query("""
            SELECT p.policy_number, p.type, p.start_date, p.end_date, p.sum_insured,
                   c.first_name, c.last_name, c.passport_number, c.phone, c.email, c.address,
                   ic.name, ic.registration_number, ic.phone, ic.address,
                   b.name as broker_name
            FROM insurance_policies p
            JOIN clients c ON p.client_id = c.id
            JOIN insurance_companies ic ON p.company_id = ic.id
            LEFT JOIN brokers b ON p.broker_id = b.id
            WHERE p.id = %s
        """, (policy_id,), fetch=True)
        if not pol_data:
            QMessageBox.warning(self, "Ошибка", "Данные полиса не найдены")
            return
        r = pol_data[0]
        policy_num = r[0]
        policy_type = r[1]
        sum_insured = float(r[4])
        client_full = f"{r[5]} {r[6]}"
        passport = r[7] if r[7] else "не указан"
        client_phone = r[8] if r[8] else "не указан"
        client_email = r[9] if r[9] else "не указан"
        client_address = r[10] if r[10] else "не указан"
        company_full = expand_company_name(r[11])
        company_reg = r[12] if r[12] else "не указан"
        company_phone = r[13] if r[13] else "не указан"
        company_address = r[14] if r[14] else "не указан"
        broker_name = r[15] if r[15] else "не указан"

        # Загружаем убытки по полису
        losses = self.db.execute_query("""
            SELECT description, amount, loss_date FROM losses WHERE policy_id=%s ORDER BY loss_date DESC
        """, (policy_id,), fetch=True)
        if not losses:
            QMessageBox.warning(self, "Ошибка", "По данному полису нет зарегистрированных убытков")
            return

        filename = f"insurance_act_{policy_num}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        w, h = A4
        self._draw_pdf_header_footer(c, "АКТ № " + str(datetime.now().strftime("%Y%m%d%H%M%S")), "О СТРАХОВОМ СЛУЧАЕ")
        y = h - 120

        # ---- 1. Стороны ----
        c.setFont('Arial', 12)
        c.drawString(50, y, "1. СТОРОНЫ")
        y -= 25
        text1 = (f"Страховщик: {company_full}, в лице {broker_name}, действующего на основании доверенности, "
                 f"именуемый в дальнейшем «Страховщик», с одной стороны, и")
        y = self._draw_text_lines(c, text1, 70, y, w-100, font_size=10, line_spacing=15)
        y = self._new_page_if_needed(c, y)
        text2 = (f"Страхователь: {client_full}, паспорт {passport}, зарегистрированный по адресу: {client_address}, "
                 f"телефон {client_phone}, email {client_email}, именуемый в дальнейшем «Страхователь», с другой стороны, "
                 f"составили настоящий Акт о нижеследующем.")
        y = self._draw_text_lines(c, text2, 70, y, w-100, font_size=10, line_spacing=15)
        y -= 10
        y = self._new_page_if_needed(c, y)

        # ---- 2. Предмет акта ----
        c.drawString(50, y, "2. ПРЕДМЕТ АКТА")
        y -= 25
        obj_desc = self._get_object_description(policy_type)
        subject_text = (f"В связи с наступлением события, имеющего признаки страхового случая по Договору страхования "
                        f"№ {policy_num} от {datetime.now().strftime('%d.%m.%Y')} (далее – Договор), Страховщик обязуется "
                        f"выплатить Страхователю страховое возмещение в размерах, указанных в п. 3 настоящего Акта, "
                        f"в пределах страховой суммы {sum_insured:,.2f} ₽. Объект страхования по Договору: {obj_desc}.")
        y = self._draw_text_lines(c, subject_text, 70, y, w-100, font_size=10, line_spacing=15)
        y -= 10
        y = self._new_page_if_needed(c, y)

        # ---- 3. Перечень страховых случаев и размер выплат ----
        c.drawString(50, y, "3. ЗАРЕГИСТРИРОВАННЫЕ СТРАХОВЫЕ СЛУЧАИ")
        y -= 25
        c.drawString(70, y, "№ п/п")
        c.drawString(120, y, "Дата события")
        c.drawString(220, y, "Описание")
        c.drawString(420, y, "Сумма выплаты (₽)")
        y -= 20
        total_payout = 0
        for idx, loss in enumerate(losses, 1):
            desc = loss[0]
            amount = float(loss[1])
            loss_date = loss[2].strftime("%d.%m.%Y") if hasattr(loss[2], 'strftime') else str(loss[2])
            total_payout += amount
            c.drawString(70, y, str(idx))
            c.drawString(120, y, loss_date)
            # Обрезаем длинное описание
            short_desc = (desc[:50] + '...') if len(desc) > 50 else desc
            c.drawString(220, y, short_desc)
            c.drawString(420, y, f"{amount:,.2f}")
            y -= 15
            if y < 60:
                c.showPage()
                self._draw_pdf_header_footer(c, "АКТ О СТРАХОВОМ СЛУЧАЕ (продолжение)", f"по полису № {policy_num}")
                y = h - 120
                c.drawString(70, y, "№ п/п")
                c.drawString(120, y, "Дата события")
                c.drawString(220, y, "Описание")
                c.drawString(420, y, "Сумма выплаты (₽)")
                y -= 20
        y -= 10
        c.drawString(70, y, f"ИТОГО к выплате: {total_payout:,.2f} ₽")
        y -= 30
        y = self._new_page_if_needed(c, y)

        # ---- 4. Подписи ----
        c.drawString(50, y, "4. ПОДПИСИ СТОРОН")
        y -= 25
        c.line(100, y, 200, y)
        c.drawString(100, y-10, "Страховщик")
        c.line(w-200, y, w-100, y)
        c.drawString(w-200, y-10, "Страхователь")
        c.drawString(100, y-25, f"{company_full}")
        c.drawString(w-200, y-25, f"{client_full}")

        c.save()
        QMessageBox.information(self, "Готово", f"Акт о страховом случае сохранён в {filename}")

    # ----- Для клиента: сводный отчёт по всем полисам -----
    def gen_self_report(self):
        self.gen_client_report(self.client_id)

    # ----- Для клиента: акт о страховых случаях по всем его убыткам (сводный) -----
    def gen_self_losses_report(self):
        # Собираем все убытки клиента по всем его полисам
        losses = self.db.execute_query("""
            SELECT l.id, l.description, l.amount, l.loss_date, p.policy_number, p.type,
                   ic.name as company_name, b.name as broker_name, p.sum_insured
            FROM losses l
            JOIN insurance_policies p ON l.policy_id = p.id
            JOIN insurance_companies ic ON p.company_id = ic.id
            LEFT JOIN brokers b ON p.broker_id = b.id
            WHERE p.client_id = %s
            ORDER BY l.loss_date DESC
        """, (self.client_id,), fetch=True)
        if not losses:
            QMessageBox.warning(self, "Ошибка", "У вас нет зарегистрированных убытков")
            return

        client = self.db.execute_query("SELECT first_name, last_name, passport_number, phone, email, address FROM clients WHERE id=%s", (self.client_id,), fetch=True)
        if not client:
            return
        r = client[0]
        client_full = f"{r[0]} {r[1]}"
        client_passport = r[2] if r[2] else "не указан"
        client_phone = r[3] if r[3] else "не указан"
        client_email = r[4] if r[4] else "не указан"
        client_address = r[5] if r[5] else "не указан"

        filename = f"client_insurance_cases_{self.client_id}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        w, h = A4
        self._draw_pdf_header_footer(c, "СВОДНЫЙ АКТ", "О СТРАХОВЫХ СЛУЧАЯХ")
        y = h - 120

        # 1. Стороны
        c.drawString(50, y, "1. СТОРОНЫ")
        y -= 25
        # Для сводного акта нужно указать, что страховщики могут быть разными – упростим: первый попавшийся полис
        first_loss = losses[0]
        company_name = first_loss[5]
        broker_name = first_loss[6] if first_loss[6] else "не указан"
        company_full_name = expand_company_name(company_name)

        text1 = (f"Настоящий Акт составлен в отношении Страхователя: {client_full}, паспорт {client_passport}, "
                 f"адрес: {client_address}, телефон {client_phone}, email {client_email}, именуемый далее «Страхователь», "
                 f"и Страховщиков, с которыми у Страхователя заключены договоры страхования (далее – Договоры).")
        y = self._draw_text_lines(c, text1, 70, y, w-100, font_size=10, line_spacing=15)
        y -= 10
        y = self._new_page_if_needed(c, y)

        # 2. Перечень страховых случаев
        c.drawString(50, y, "2. ЗАРЕГИСТРИРОВАННЫЕ СТРАХОВЫЕ СЛУЧАИ ПО ДОГОВОРАМ")
        y -= 25
        c.drawString(70, y, "№")
        c.drawString(100, y, "Полис")
        c.drawString(180, y, "Страховщик")
        c.drawString(300, y, "Дата события")
        c.drawString(380, y, "Описание")
        c.drawString(500, y, "Сумма (₽)")
        y -= 20
        total_payout = 0
        for idx, loss in enumerate(losses, 1):
            policy_num = loss[4]
            company = loss[5]
            loss_date = loss[3].strftime("%d.%m.%Y") if hasattr(loss[3], 'strftime') else str(loss[3])
            desc = loss[1]
            amount = float(loss[2])
            total_payout += amount
            c.drawString(70, y, str(idx))
            c.drawString(100, y, policy_num)
            c.drawString(180, y, company[:25])
            c.drawString(300, y, loss_date)
            short_desc = (desc[:40] + '...') if len(desc) > 40 else desc
            c.drawString(380, y, short_desc)
            c.drawString(500, y, f"{amount:,.2f}")
            y -= 15
            if y < 60:
                c.showPage()
                self._draw_pdf_header_footer(c, "СВОДНЫЙ АКТ О СТРАХОВЫХ СЛУЧАЯХ (продолжение)", client_full)
                y = h - 120
                c.drawString(70, y, "№")
                c.drawString(100, y, "Полис")
                c.drawString(180, y, "Страховщик")
                c.drawString(300, y, "Дата события")
                c.drawString(380, y, "Описание")
                c.drawString(500, y, "Сумма (₽)")
                y -= 20
        y -= 10
        c.drawString(70, y, f"ИТОГО к выплате по всем страховым случаям: {total_payout:,.2f} ₽")
        y -= 30
        y = self._new_page_if_needed(c, y)

        # 3. Подписи
        c.drawString(50, y, "3. ПОДПИСИ СТОРОН")
        y -= 25
        c.line(100, y, 200, y)
        c.drawString(100, y-10, "Страхователь")
        c.line(w-200, y, w-100, y)
        c.drawString(w-200, y-10, "Страховщик (уполномоченный представитель)")
        c.drawString(100, y-25, f"{client_full}")
        c.drawString(w-200, y-25, f"{company_full_name} / {broker_name}")

        c.save()
        QMessageBox.information(self, "Готово", f"Акт о страховых случаях сохранён в {filename}")

    # ----- Отчёты по компании (для брокера) -----
    def gen_company_report(self):
        policies = self.db.execute_query("""
            SELECT p.policy_number, c.first_name||' '||c.last_name, p.type, p.start_date, p.end_date, p.sum_insured, p.status
            FROM insurance_policies p
            JOIN clients c ON p.client_id = c.id
            WHERE p.company_id=%s
        """, (self.company_id,), fetch=True)
        company = self.db.execute_query("SELECT name FROM insurance_companies WHERE id=%s", (self.company_id,), fetch=True)
        comp_name = company[0][0] if company else "Компания"
        filename = f"company_policies_{self.company_id}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        self._draw_pdf_header_footer(c, "ПОЛИСЫ КОМПАНИИ", expand_company_name(comp_name))
        w, h = A4
        data = [["№ полиса", "Клиент", "Тип", "Начало", "Окончание", "Сумма (₽)", "Статус"]]
        total = 0
        for pol in policies:
            data.append([
                str(pol[0]), str(pol[1]), str(pol[2]),
                pol[3].strftime("%d.%m.%Y") if hasattr(pol[3], 'strftime') else pol[3],
                pol[4].strftime("%d.%m.%Y") if hasattr(pol[4], 'strftime') else pol[4],
                f"{float(pol[5]):,.2f}", str(pol[6])
            ])
            total += float(pol[5])
        table = Table(data, colWidths=[55,100,55,65,65,70,50])
        table.setStyle(TableStyle([
            ('FONTNAME',(0,0),(-1,-1),'Arial'),('FONTSIZE',(0,0),(-1,-1),8),
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#d0e4f5')),
            ('GRID',(0,0),(-1,-1),0.5,colors.grey),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f9f9f9')]),
        ]))
        table.wrapOn(c, w-100, h-200)
        table.drawOn(c, 50, h-240 - len(policies)*12)
        y = h-260 - len(policies)*12
        c.setFont('Arial', 10)
        c.drawString(50, y, f"Общая страховая сумма: {total:,.2f} ₽")
        c.save()
        QMessageBox.information(self, "Готово", f"Отчёт сохранён в {filename}")

    def gen_company_losses_report(self):
        losses = self.db.execute_query("""
            SELECT l.description, l.amount, l.loss_date, p.policy_number
            FROM losses l
            JOIN insurance_policies p ON l.policy_id = p.id
            WHERE p.company_id=%s
            ORDER BY l.loss_date DESC
        """, (self.company_id,), fetch=True)
        company = self.db.execute_query("SELECT name FROM insurance_companies WHERE id=%s", (self.company_id,), fetch=True)
        comp_name = company[0][0] if company else "Компания"
        filename = f"company_losses_{self.company_id}.pdf"
        c = canvas.Canvas(filename, pagesize=A4)
        self._draw_pdf_header_footer(c, "УБЫТКИ КОМПАНИИ", expand_company_name(comp_name))
        w, h = A4
        data = [["Полис", "Описание", "Сумма (₽)", "Дата"]]
        total = 0
        for loss in losses:
            data.append([str(loss[3]), str(loss[0]), f"{float(loss[1]):,.2f}", loss[2].strftime("%d.%m.%Y") if hasattr(loss[2], 'strftime') else loss[2]])
            total += float(loss[1])
        if len(losses) == 0:
            data.append(["Нет убытков", "-", "0,00", "-"])
        table = Table(data, colWidths=[80,200,80,80])
        table.setStyle(TableStyle([
            ('FONTNAME',(0,0),(-1,-1),'Arial'),('FONTSIZE',(0,0),(-1,-1),9),
            ('BACKGROUND',(0,0),(-1,0),colors.HexColor('#d0e4f5')),
            ('GRID',(0,0),(-1,-1),0.5,colors.grey),
            ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f9f9f9')]),
        ]))
        table.wrapOn(c, w-100, h-200)
        table.drawOn(c, 50, h-220 - len(losses)*18)
        y = h-240 - len(losses)*18
        c.setFont('Arial', 10)
        c.drawString(50, y, f"Общая сумма убытков: {total:,.2f} ₽")
        c.save()
        QMessageBox.information(self, "Готово", f"Отчёт сохранён в {filename}")

    # ---------- Вспомогательные методы ----------
    def _draw_text_lines(self, c, text, x, y, max_width, font_size=10, line_spacing=15):
        c.setFont('Arial', font_size)
        words = text.split(' ')
        lines = []
        current_line = ""
        for w in words:
            test_line = current_line + (" " if current_line else "") + w
            if c.stringWidth(test_line, 'Arial', font_size) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = w
        if current_line:
            lines.append(current_line)
        for line in lines:
            c.drawString(x, y, line)
            y -= line_spacing
        return y

    def _new_page_if_needed(self, c, y, margin=50):
        if y < margin:
            c.showPage()
            self._draw_pdf_header_footer(c, "ПРОДОЛЖЕНИЕ", "")
            return c._pagesize[1] - 100
        return y

    def _get_object_description(self, policy_type):
        if policy_type == "Авто":
            return "транспортное средство"
        elif policy_type == "Медицина":
            return "расходы на медицинские услуги"
        elif policy_type == "Имущество":
            return "имущество"
        elif policy_type == "Жизнь":
            return "жизнь и здоровье"
        else:
            return "риски, предусмотренные договором"
# ========== ЗАПУСК ==========
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 9))

    app.setStyleSheet("""
        QWidget { background-color: #1e1e2f; color: #e0e0e0; font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif; }
        QMainWindow { background-color: transparent; }
        QFrame#mainFrame { background-color: #1e1e2f; border-radius: 12px; border: 1px solid #3a3a4a; }
        QFrame#titleBar { background-color: #2a2a3a; border-top-left-radius: 12px; border-top-right-radius: 12px; }
        QLabel#logoLabel { font-size: 14pt; font-weight: bold; color: #dcdcdc; }
        QPushButton#titleButton, QPushButton#titleCloseButton { background-color: #3a3a4a; border: none; border-radius: 4px; font-size: 12pt; font-weight: bold; }
        QPushButton#titleButton:hover { background-color: #5a5a6a; }
        QPushButton#titleCloseButton:hover { background-color: #e05a5a; color: white; }
        QTabWidget::pane { border: 1px solid #3a3a4a; background-color: #1e1e2f; border-radius: 8px; }
        QTabBar::tab { background-color: #2a2a3a; padding: 8px 20px; margin-right: 4px; border-top-left-radius: 6px; border-top-right-radius: 6px; }
        QTabBar::tab:selected { background-color: #3c7e5a; color: white; }
        QTabBar::tab:hover:!selected { background-color: #3a3a4a; }
        QGroupBox#card { background-color: #2a2a3a; border: 1px solid #3c7e5a; border-radius: 12px; margin-top: 12px; padding-top: 12px; }
        QGroupBox#card::title { subcontrol-origin: margin; left: 15px; padding: 0 8px; color: #3c7e5a; font-weight: bold; }
        QGroupBox { background-color: #2a2a3a; border: 1px solid #3a3a4a; border-radius: 8px; margin-top: 12px; }
        QPushButton { background-color: #3c7e5a; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; font-size: 10pt; }
        QPushButton:hover { background-color: #4e9e72; }
        QPushButton:pressed { background-color: #2d5e44; }
        QTableWidget { background-color: #25253a; alternate-background-color: #2a2a3a; gridline-color: #3a3a4a; selection-background-color: #3c7e5a; border-radius: 6px; }
        QHeaderView::section { background-color: #1e1e2f; padding: 6px; border: 1px solid #3a3a4a; font-weight: bold; }
        QLineEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit { background-color: #25253a; border: 1px solid #3c7e5a; border-radius: 6px; padding: 5px; }
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus { border: 2px solid #3c7e5a; }
        QDialog { background-color: #2a2a3a; border-radius: 12px; }
        QMessageBox { background-color: #2a2a3a; }
        QScrollBar:vertical { background: #2a2a3a; width: 10px; border-radius: 5px; }
        QScrollBar::handle:vertical { background: #5a5a6a; border-radius: 5px; min-height: 20px; }
        QScrollBar::handle:vertical:hover { background: #3c7e5a; }
        QFrame#loginContainer { background-color: #2a2a3a; border-radius: 16px; border: 1px solid #3c7e5a; }
        QLabel#loginTitle { font-size: 18pt; font-weight: bold; color: #3c7e5a; }
        QPushButton#loginButton { background-color: #3c7e5a; font-size: 12pt; padding: 8px 30px; }
        QPushButton#closeButton { background-color: #4a4a5a; border-radius: 15px; font-size: 12pt; font-weight: bold; }
        QPushButton#closeButton:hover { background-color: #e05a5a; }
    """)

    db = DatabaseManager()
    init_database(db)

    login = LoginDialog(db)
    if login.exec_() == QDialog.Accepted:
        app = QApplication.instance()
        role = getattr(app, 'user_role', 'client')
        client_id = getattr(app, 'user_client_id', None)
        company_id = getattr(app, 'user_company_id', None)
        win = MainWindow(db, role, client_id, company_id)
        win.show()
        sys.exit(app.exec_())
    else:
        db.close()
        sys.exit(0)