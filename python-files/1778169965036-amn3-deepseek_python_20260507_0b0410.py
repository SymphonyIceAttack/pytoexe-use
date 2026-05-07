import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import scrolledtext
import re
import os
import csv
from datetime import datetime
from typing import List, Dict, Any
import traceback

# ----------------------------------------------------------------------
# Функции для определения кодировки (ручной метод)
# ----------------------------------------------------------------------

def detect_encoding_simple(filepath: str) -> str:
    encodings_to_try = ['utf-8-sig', 'utf-8', 'cp1251', 'windows-1251', 'cp866', 'koi8-r', 'latin-1']
    with open(filepath, 'rb') as f:
        raw_data = f.read(10000)
    for encoding in encodings_to_try:
        try:
            decoded = raw_data.decode(encoding)
            if re.search(r'[а-яА-ЯёЁ]', decoded):
                return encoding
            if encoding in ['utf-8-sig', 'utf-8']:
                continue
        except UnicodeDecodeError:
            continue
    if raw_data.startswith(b'\xef\xbb\xbf'):
        return 'utf-8-sig'
    try:
        raw_data.decode('cp1251')
        return 'cp1251'
    except:
        pass
    return 'utf-8'

def read_csv_safe(filepath: str, skip_header=True, delimiter=';') -> List[List[str]]:
    encoding = detect_encoding_simple(filepath)
    rows = []
    try:
        with open(filepath, 'r', encoding=encoding, newline='') as f:
            if delimiter is None:
                sample = f.read(1024)
                f.seek(0)
                if ';' in sample:
                    delimiter = ';'
                elif ',' in sample:
                    delimiter = ','
                elif '\t' in sample:
                    delimiter = '\t'
                else:
                    delimiter = ';'
            reader = csv.reader(f, delimiter=delimiter)
            for row in reader:
                rows.append([cell.strip() for cell in row])
    except UnicodeDecodeError:
        for enc in ['cp1251', 'windows-1251', 'utf-8', 'cp866', 'koi8-r']:
            try:
                with open(filepath, 'r', encoding=enc, newline='') as f:
                    reader = csv.reader(f, delimiter=delimiter)
                    rows = []
                    for row in reader:
                        rows.append([cell.strip() for cell in row])
                break
            except UnicodeDecodeError:
                continue
        else:
            raise Exception(f"Не удалось прочитать файл. Сохраните файл в кодировке UTF-8 или Windows-1251.")
    rows = [r for r in rows if any(cell for cell in r)]
    if skip_header and len(rows) > 1:
        rows = rows[1:]
    return rows

# ----------------------------------------------------------------------
# Базовые шаблоны для генерации XML (встроенные в код)
# ----------------------------------------------------------------------
DEFAULT_ARSHIN_XML_TEMPLATE = '''def generate_arshin_xml(data_rows):
    """Генерация XML для ФГИС «Аршин»."""
    xml_lines = ['<?xml version="1.0" encoding="utf-8"?>']
    xml_lines.append('<gost:application xmlns:gost="urn://fgis-arshin.gost.ru/module-verifications/import/2020-06-19">')
    for row in data_rows:
        if not row or not row[0]:
            continue
        values = row + [''] * (22 - len(row))
        num_grsi, serial_num, year, modification = values[0], values[1], values[2], values[3]
        sign_cipher, owner, vrf_date, valid_date = values[4], values[5], values[6], values[7]
        applicability, reason_unfit = values[8], values[9]
        doc_title, metrologist, etalon_num = values[10], values[11], values[12]
        mi_types = [values[13], values[14], values[15]]
        mi_serials = [values[16], values[17], values[18]]
        temperature, pressure, humidity = values[19], values[20], values[21]

        xml_lines.append('    <gost:result>')
        xml_lines.append('        <gost:miInfo>')
        xml_lines.append('            <gost:singleMI>')
        xml_lines.append(f'                <gost:mitypeNumber>{safe_xml(num_grsi)}</gost:mitypeNumber>')
        xml_lines.append(f'                <gost:manufactureNum>{safe_xml(serial_num)}</gost:manufactureNum>')
        if year:
            xml_lines.append(f'                <gost:manufactureYear>{safe_xml(year)}</gost:manufactureYear>')
        if modification:
            xml_lines.append(f'                <gost:modification>{safe_xml(modification)}</gost:modification>')
        xml_lines.append('            </gost:singleMI>')
        xml_lines.append('        </gost:miInfo>')
        if sign_cipher:
            xml_lines.append(f'        <gost:signCipher>{safe_xml(sign_cipher)}</gost:signCipher>')
        if owner:
            xml_lines.append(f'        <gost:miOwner>{safe_xml(owner)}</gost:miOwner>')
        xml_lines.append(f'        <gost:vrfDate>{format_date(vrf_date)}</gost:vrfDate>')
        if not is_unfit(applicability) and valid_date:
            xml_lines.append(f'        <gost:validDate>{format_date(valid_date)}</gost:validDate>')
        xml_lines.append('        <gost:type>2</gost:type>')
        xml_lines.append('        <gost:calibration>false</gost:calibration>')
        if is_unfit(applicability):
            xml_lines.append('        <gost:inapplicable>')
            reason = reason_unfit if reason_unfit else 'Причина не указана'
            xml_lines.append(f'            <gost:reasons>{safe_xml(reason)}</gost:reasons>')
            xml_lines.append('        </gost:inapplicable>')
        else:
            xml_lines.append('        <gost:applicable>')
            xml_lines.append('            <gost:signPass>true</gost:signPass>')
            xml_lines.append('            <gost:signMi>true</gost:signMi>')
            xml_lines.append('        </gost:applicable>')
        if doc_title:
            xml_lines.append(f'        <gost:docTitle>{safe_xml(doc_title)}</gost:docTitle>')
        if metrologist:
            xml_lines.append(f'        <gost:metrologist>{safe_xml(metrologist)}</gost:metrologist>')
        xml_lines.append('        <gost:means>')
        if etalon_num:
            xml_lines.append('            <gost:mieta>')
            xml_lines.append(f'                <gost:number>{safe_xml(etalon_num)}</gost:number>')
            xml_lines.append('            </gost:mieta>')
        has_extra = any(t and s for t, s in zip(mi_types, mi_serials))
        if has_extra:
            xml_lines.append('            <gost:mis>')
            for mt, ms in zip(mi_types, mi_serials):
                if mt and ms:
                    xml_lines.append('                <gost:mi>')
                    xml_lines.append(f'                    <gost:typeNum>{safe_xml(mt)}</gost:typeNum>')
                    xml_lines.append(f'                    <gost:manufactureNum>{safe_xml(ms)}</gost:manufactureNum>')
                    xml_lines.append('                </gost:mi>')
            xml_lines.append('            </gost:mis>')
        xml_lines.append('        </gost:means>')
        if temperature or pressure or humidity:
            xml_lines.append('        <gost:conditions>')
            if temperature:
                xml_lines.append(f'            <gost:temperature>{safe_xml(temperature.replace(".", ","))}</gost:temperature>')
            if pressure:
                xml_lines.append(f'            <gost:pressure>{safe_xml(pressure.replace(".", ","))}</gost:pressure>')
            if humidity:
                xml_lines.append(f'            <gost:hymidity>{safe_xml(humidity.replace(".", ","))}</gost:hymidity>')
            xml_lines.append('        </gost:conditions>')
        xml_lines.append('    </gost:result>')
    xml_lines.append('</gost:application>')
    return '\\n'.join(xml_lines)
'''

DEFAULT_ACCREDITATION_XML_TEMPLATE = '''def generate_accreditation_xml(data_rows):
    """Генерация XML для Росаккредитации."""
    xml_lines = ["<?xml version='1.0' encoding='UTF-8'?>"]
    xml_lines.append('<Message xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="schema.xsd">')
    xml_lines.append('  <VerificationMeasuringInstrumentData>')
    for row in data_rows:
        if not row or not row[0]:
            continue
        values = row + [''] * (7 - len(row))
        number_verif = values[0]
        type_mi = values[1]
        date_verif = format_date(values[2])
        date_end = format_date(values[3])
        result_raw = values[4]
        snils = values[5]
        full_name = values[6]
        result_code = '1' if normalize_verification_result(result_raw) == 'пригодно' else '2'
        name_parts = split_full_name(full_name)

        xml_lines.append('    <VerificationMeasuringInstrument>')
        xml_lines.append(f'      <NumberVerification>{safe_xml(number_verif)}</NumberVerification>')
        xml_lines.append(f'      <DateVerification>{date_verif}</DateVerification>')
        xml_lines.append(f'      <DateEndVerification>{date_end}</DateEndVerification>')
        xml_lines.append(f'      <TypeMeasuringInstrument>{safe_xml(type_mi)}</TypeMeasuringInstrument>')
        xml_lines.append('      <ApprovedEmployees>')
        xml_lines.append('        <Name>')
        xml_lines.append(f'          <Last>{safe_xml(name_parts["lastName"])}</Last>')
        xml_lines.append(f'          <First>{safe_xml(name_parts["firstName"])}</First>')
        xml_lines.append('        </Name>')
        xml_lines.append(f'        <SNILS>{safe_xml(snils)}</SNILS>')
        xml_lines.append('      </ApprovedEmployees>')
        xml_lines.append(f'      <ResultVerification>{result_code}</ResultVerification>')
        xml_lines.append('    </VerificationMeasuringInstrument>')
    xml_lines.append('  </VerificationMeasuringInstrumentData>')
    xml_lines.append('  <SaveMethod>1</SaveMethod>')
    xml_lines.append('</Message>')
    return '\\n'.join(xml_lines)
'''

# ----------------------------------------------------------------------
# Вспомогательные функции
# ----------------------------------------------------------------------
def safe_xml(text: str) -> str:
    if not isinstance(text, str):
        text = str(text)
    replacements = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&apos;'}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def format_date(date_value: Any) -> str:
    if not date_value:
        return ""
    if isinstance(date_value, str):
        date_str = date_value.strip()
        if not date_str:
            return ""
        cleaned = re.sub(r'[./]', '-', date_str)
        patterns = [
            (r'^(\d{4})-(\d{1,2})-(\d{1,2})$', False),
            (r'^(\d{1,2})-(\d{1,2})-(\d{4})$', True),
        ]
        for pattern, is_dmy in patterns:
            match = re.match(pattern, cleaned)
            if match:
                if is_dmy:
                    day, month, year = match.group(1), match.group(2), match.group(3)
                else:
                    year, month, day = match.group(1), match.group(2), match.group(3)
                try:
                    dt = datetime(int(year), int(month), int(day))
                    return dt.strftime("%Y-%m-%d")
                except:
                    continue
        for fmt in ("%d.%m.%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%Y", "%Y/%m/%d"):
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime("%Y-%m-%d")
            except:
                continue
        return date_str
    if isinstance(date_value, (int, float)):
        try:
            from datetime import timedelta
            excel_base = datetime(1899, 12, 30)
            dt = excel_base + timedelta(days=date_value)
            return dt.strftime("%Y-%m-%d")
        except:
            return str(date_value)
    if isinstance(date_value, datetime):
        return date_value.strftime("%Y-%m-%d")
    return str(date_value)

def is_unfit(value: Any) -> bool:
    if not value:
        return False
    val = str(value).strip().lower()
    return val in ('непригодно', 'непригоден', 'брак', 'false', 'нет', '0')

def normalize_verification_result(value: Any) -> str:
    if not value:
        return 'пригодно'
    val = str(value).strip().lower()
    if val in ('не пригоден', 'непригоден', 'непригодно', 'брак', 'false', 'нет', '0'):
        return 'непригодно'
    if val in ('пригодно', 'годен', 'true', 'да', '1', '+'):
        return 'пригодно'
    return val

def split_full_name(full_name: str) -> Dict[str, str]:
    if not full_name:
        return {'lastName': 'Неизвестно', 'firstName': 'Неизвестно'}
    parts = str(full_name).strip().split()
    if len(parts) >= 2:
        return {'lastName': parts[0], 'firstName': parts[1]}
    return {'lastName': 'Неизвестно', 'firstName': 'Неизвестно'}

# ----------------------------------------------------------------------
# Работа с CSV (шаблоны создаются в UTF-8 с BOM)
# ----------------------------------------------------------------------
def create_arshin_template_csv(filepath: str):
    headers = [
        "Номер в ГРСИ", "Заводской номер", "Год выпуска", "Модификация",
        "Шифр знака", "Владелец СИ", "Дата поверки", "Дата действия",
        "Пригодность", "Причина непригодности", "Наименование документа", "ФИО метролога",
        "Номер СИ/эталона", "Тип СИ 1", "Тип СИ 2", "Тип СИ 3",
        "Заводской номер СИ 1", "Заводской номер СИ 2", "Заводской номер СИ 3",
        "Температура", "Давление", "Влажность"
    ]
    example = [
        "47957-11", "3026171", "2013", "ТОП-0,66 У3", "ГЗО",
        "Восточное производственное отделение", "18.07.2025", "17.07.2030",
        "пригодно", "", "ГОСТ 8.217-2024", "Наседкин Дмитрий Александрович",
        "27007.04.2Р.00564940", "14883-95", "46434-11", "59851-15",
        "99936", "ОВ-51", "52719", "21,4", "101,8", "30,7"
    ]
    unfit = [
        "2746-71", "327567", "1975", "М416", "ГЗС",
        'филиал ПАО "Россети Волга" - "Самарские РС", Самарское ПО, Красноярский РЭС',
        "17.11.2025", "", "непригодно", "Превышение допустимой погрешности", "ГОСТ 8.409-81",
        "Кондрашин Дмитрий Витальевич", "6332.77.4Р.00304693", "46434-11", "", "",
        "ОВ-51", "", "", "22,9", "756,5", "32,8"
    ]
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(headers)
        writer.writerow(example)
        writer.writerow(unfit)

def create_accreditation_template_csv(filepath: str):
    headers = ["Номер Аршин", "Тип поверяемого СИ", "Дата результатов поверки", "Дата действия", "Результат поверки", "СНИЛС", "Фамилия и Имя"]
    example = ["С-ГЗО/18-07-2025/462546997", "ЗНОМ-35-65 У1", "18.07.2025", "17.07.2030", "пригодно", "10786907691", "Наседкин Дмитрий"]
    unfit = ["С-ГЗО/18-07-2025/462546998", "ЗНОМ-35-65 У1", "18.07.2025", "", "непригодно", "10786907692", "Иванов Петр"]
    with open(filepath, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f, delimiter=';')
        writer.writerow(headers)
        writer.writerow(example)
        writer.writerow(unfit)

# ----------------------------------------------------------------------
# Класс для управления пользовательскими шаблонами
# ----------------------------------------------------------------------
class TemplateManager:
    def __init__(self):
        self.arshin_func = None
        self.accreditation_func = None
        self.load_defaults()
    
    def load_defaults(self):
        exec_globals = {
            'safe_xml': safe_xml,
            'format_date': format_date,
            'is_unfit': is_unfit,
            'normalize_verification_result': normalize_verification_result,
            'split_full_name': split_full_name,
        }
        try:
            exec(DEFAULT_ARSHIN_XML_TEMPLATE, exec_globals)
            self.arshin_func = exec_globals['generate_arshin_xml']
        except Exception as e:
            print(f"Ошибка загрузки шаблона Аршин: {e}")
            self.arshin_func = None
        try:
            exec(DEFAULT_ACCREDITATION_XML_TEMPLATE, exec_globals)
            self.accreditation_func = exec_globals['generate_accreditation_xml']
        except Exception as e:
            print(f"Ошибка загрузки шаблона аккредитации: {e}")
            self.accreditation_func = None
    
    def update_arshin_template(self, code_text):
        exec_globals = {
            'safe_xml': safe_xml,
            'format_date': format_date,
            'is_unfit': is_unfit,
            'normalize_verification_result': normalize_verification_result,
            'split_full_name': split_full_name,
        }
        try:
            exec(code_text, exec_globals)
            if 'generate_arshin_xml' in exec_globals:
                self.arshin_func = exec_globals['generate_arshin_xml']
                return True, "Шаблон Аршин успешно обновлён."
            else:
                return False, "Код не содержит функцию generate_arshin_xml"
        except Exception as e:
            return False, f"Ошибка в коде: {str(e)}"
    
    def update_accreditation_template(self, code_text):
        exec_globals = {
            'safe_xml': safe_xml,
            'format_date': format_date,
            'is_unfit': is_unfit,
            'normalize_verification_result': normalize_verification_result,
            'split_full_name': split_full_name,
        }
        try:
            exec(code_text, exec_globals)
            if 'generate_accreditation_xml' in exec_globals:
                self.accreditation_func = exec_globals['generate_accreditation_xml']
                return True, "Шаблон аккредитации успешно обновлён."
            else:
                return False, "Код не содержит функцию generate_accreditation_xml"
        except Exception as e:
            return False, f"Ошибка в коде: {str(e)}"
    
    def restore_arshin(self):
        exec_globals = {
            'safe_xml': safe_xml,
            'format_date': format_date,
            'is_unfit': is_unfit,
            'normalize_verification_result': normalize_verification_result,
            'split_full_name': split_full_name,
        }
        try:
            exec(DEFAULT_ARSHIN_XML_TEMPLATE, exec_globals)
            self.arshin_func = exec_globals['generate_arshin_xml']
            return True, "Шаблон Аршин восстановлен"
        except Exception as e:
            return False, str(e)
    
    def restore_accreditation(self):
        exec_globals = {
            'safe_xml': safe_xml,
            'format_date': format_date,
            'is_unfit': is_unfit,
            'normalize_verification_result': normalize_verification_result,
            'split_full_name': split_full_name,
        }
        try:
            exec(DEFAULT_ACCREDITATION_XML_TEMPLATE, exec_globals)
            self.accreditation_func = exec_globals['generate_accreditation_xml']
            return True, "Шаблон аккредитации восстановлен"
        except Exception as e:
            return False, str(e)

# ----------------------------------------------------------------------
# GUI-класс с улучшенным стилем и исправленным позиционированием
# ----------------------------------------------------------------------
class App:
    def __init__(self, root):
        self.root = root
        root.title("Генератор XML для Аршин и Росаккредитации")
        root.geometry("1400x900")
        root.configure(bg="#f0f4f8")
        
        # Настройка стилей ttk
        self.setup_styles()
        
        self.tm = TemplateManager()
        
        # Верхняя панель с логотипом
        self.create_header()
        
        # Основной блок с вкладками
        self.notebook = ttk.Notebook(root, style="Custom.TNotebook")
        self.notebook.pack(fill='both', expand=True, padx=15, pady=(5, 15))
        
        self.arshin_frame = ttk.Frame(self.notebook)
        self.accred_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.arshin_frame, text="🏭 Генератор XML для Аршин")
        self.notebook.add(self.accred_frame, text="⚡ Конфигуратор аккредитации")
        
        self.init_arshin_tab()
        self.init_accreditation_tab()
        
        # Статусная строка
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе (CSV, автоопределение кодировки)")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W,
                               font=("Segoe UI", 9))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 5))
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Цветовая схема
        bg_color = "#f0f4f8"
        fg_color = "#2c3e50"
        accent_color = "#3498db"
        success_color = "#27ae60"
        warning_color = "#e67e22"
        danger_color = "#e74c3c"
        
        # Настройка вкладок
        style.configure("Custom.TNotebook", background=bg_color, borderwidth=0)
        style.configure("Custom.TNotebook.Tab", background="#ecf0f1", padding=[12, 6],
                        font=("Segoe UI", 10, "bold"))
        style.map("Custom.TNotebook.Tab", background=[("selected", accent_color)],
                  foreground=[("selected", "white")])
        
        # Общие кнопки
        style.configure("TButton", font=("Segoe UI", 9), padding=6, relief="flat")
        style.map("TButton", background=[("active", "#2980b9")])
        
        # Специальные кнопки
        style.configure("Success.TButton", background=success_color)
        style.map("Success.TButton", background=[("active", "#229954")])
        style.configure("Warning.TButton", background=warning_color)
        style.map("Warning.TButton", background=[("active", "#d35400")])
        style.configure("Danger.TButton", background=danger_color)
        style.map("Danger.TButton", background=[("active", "#c0392b")])
        style.configure("Primary.TButton", background=accent_color)
        style.map("Primary.TButton", background=[("active", "#2980b9")])
        style.configure("Purple.TButton", background="#9b59b6")
        style.map("Purple.TButton", background=[("active", "#8e44ad")])
        
        # Treeview с улучшенной читаемостью
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=28,
                        fieldbackground="white", background="white", foreground=fg_color,
                        bordercolor="#d0d7de", borderwidth=1)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"),
                        background=accent_color, foreground="white", relief="flat")
        style.map("Treeview.Heading", background=[("active", "#2980b9")])
        
        # Настройка тегов для чередования строк (будет применено при вставке)
        
        # LabelFrame
        style.configure("TLabelframe", background=bg_color, relief="solid", borderwidth=1)
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"), foreground=fg_color)
        
        # Entry, Combobox
        style.configure("TEntry", fieldbackground="white", borderwidth=1, relief="solid")
        style.configure("TCombobox", fieldbackground="white")
    
    def create_header(self):
        header = tk.Frame(self.root, bg="#2c3e50", height=70)
        header.pack(fill=tk.X, side=tk.TOP)
        
        logo_label = tk.Label(header, text="📊 МЕТРОКОМБАЙН", font=("Segoe UI", 18, "bold"),
                              bg="#2c3e50", fg="white")
        logo_label.place(x=20, y=15)
        
        sub_label = tk.Label(header, text="Генератор XML для Аршин и Росаккредитации",
                             font=("Segoe UI", 9), bg="#2c3e50", fg="#bdc3c7")
        sub_label.place(x=20, y=45)
        
        dev_label = tk.Label(header, text="Разработчик: Омельченко Алексей | Версия 3.0",
                             font=("Segoe UI", 9), bg="#2c3e50", fg="#bdc3c7")
        dev_label.place(relx=0.95, y=25, anchor="ne")
    
    # --------------------------------------------------------------
    # Вкладка Аршин
    # --------------------------------------------------------------
    def init_arshin_tab(self):
        btn_frame = ttk.Frame(self.arshin_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Button(btn_frame, text="➕ Добавить строку", command=self.arshin_add_row,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="➖ Удалить строку", command=self.arshin_remove_row,
                   style="Danger.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📥 Скачать шаблон CSV", command=self.arshin_download_template,
                   style="Warning.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📂 Загрузить CSV", command=self.arshin_load_csv,
                   style="Success.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="⚡ Сгенерировать XML", command=self.arshin_generate_xml,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="💾 Сохранить XML", command=self.arshin_save_xml,
                   style="Success.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="✏ Редактировать шаблон", command=self.arshin_edit_template,
                   style="Purple.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🔄 Восстановить шаблон", command=self.arshin_restore_template,
                   style="Warning.TButton").pack(side=tk.LEFT, padx=2)
        
        # Таблица
        self.arshin_columns = [
            "Номер в ГРСИ*", "Зав. номер*", "Год*", "Модификация", "Шифр знака*", "Владелец*",
            "Дата поверки*", "Дата действия", "Пригодность*", "Причина непригодности",
            "Документ*", "Метролог*", "Эталон*", "Тип СИ1", "Тип СИ2", "Тип СИ3",
            "№ СИ1", "№ СИ2", "№ СИ3", "Температура", "Давление", "Влажность"
        ]
        self.arshin_tree = ttk.Treeview(self.arshin_frame, columns=self.arshin_columns,
                                        show="headings", height=12, style="Treeview")
        for col in self.arshin_columns:
            self.arshin_tree.heading(col, text=col)
            self.arshin_tree.column(col, width=110, anchor="center")
        
        # Скроллы
        v_scroll = ttk.Scrollbar(self.arshin_frame, orient="vertical", command=self.arshin_tree.yview)
        h_scroll = ttk.Scrollbar(self.arshin_frame, orient="horizontal", command=self.arshin_tree.xview)
        self.arshin_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.arshin_tree.pack(fill='both', expand=True, padx=10, pady=5)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.arshin_tree.bind("<Double-1>", self.arshin_edit_cell)
        
        # Добавляем чередование цветов строк
        self.arshin_tree.tag_configure('oddrow', background='#f8f9fa')
        self.arshin_tree.tag_configure('evenrow', background='#ffffff')
        
        # Примеры данных
        example_row = [
            "47957-11", "3026171", "2013", "ТОП-0,66 У3", "ГЗО",
            "Восточное производственное отделение", "18.07.2025", "17.07.2030",
            "пригодно", "", "ГОСТ 8.217-2024", "Наседкин Дмитрий Александрович",
            "27007.04.2Р.00564940", "14883-95", "46434-11", "59851-15",
            "99936", "ОВ-51", "52719", "21,4", "101,8", "30,7"
        ]
        self.arshin_add_row(example_row)
        
        unfit_example = [
            "2746-71", "327567", "1975", "М416", "ГЗС",
            'филиал ПАО "Россети Волга" - "Самарские РС", Самарское ПО, Красноярский РЭС',
            "17.11.2025", "", "непригодно", "Превышение допустимой погрешности", "ГОСТ 8.409-81",
            "Кондрашин Дмитрий Витальевич", "6332.77.4Р.00304693", "46434-11", "", "",
            "ОВ-51", "", "", "22,9", "756,5", "32,8"
        ]
        self.arshin_add_row(unfit_example)
        
        # Поле вывода XML
        xml_frame = ttk.LabelFrame(self.arshin_frame, text="Результат XML для Аршин", padding=5)
        xml_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.arshin_xml_text = scrolledtext.ScrolledText(xml_frame, wrap=tk.NONE,
                                                         font=("Courier New", 10), bg="#fef9e4")
        self.arshin_xml_text.pack(fill=tk.BOTH, expand=True)
    
    def arshin_add_row(self, data=None):
        if data is None:
            empty_vals = {col: "" for col in self.arshin_columns}
            empty_vals["Пригодность*"] = "пригодно"
            values = [empty_vals[col] for col in self.arshin_columns]
        else:
            data_full = list(data) + [''] * (22 - len(data))
            values = data_full[:22]
        row_count = len(self.arshin_tree.get_children())
        tag = 'evenrow' if row_count % 2 == 0 else 'oddrow'
        self.arshin_tree.insert("", tk.END, values=values, tags=(tag,))
    
    def arshin_remove_row(self):
        selected = self.arshin_tree.selection()
        if not selected:
            messagebox.showwarning("Удаление", "Выберите строку для удаления.")
            return
        for item in selected:
            self.arshin_tree.delete(item)
        # Перекрашиваем строки после удаления
        self.recolor_arshin_rows()
    
    def recolor_arshin_rows(self):
        children = self.arshin_tree.get_children()
        for i, child in enumerate(children):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.arshin_tree.item(child, tags=(tag,))
    
    def arshin_edit_cell(self, event):
        item = self.arshin_tree.selection()[0]
        col = self.arshin_tree.identify_column(event.x)
        col_index = int(col[1:]) - 1
        col_name = self.arshin_columns[col_index]
        current_value = self.arshin_tree.item(item, "values")[col_index]
        
        popup = tk.Toplevel(self.root)
        popup.title(f"Редактировать {col_name}")
        popup.geometry("450x130")
        popup.resizable(False, False)
        popup.grab_set()
        popup.configure(bg="#f0f4f8")
        
        # Центрируем окно относительно главного окна
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 225
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 65
        popup.geometry(f"+{x}+{y}")
        
        if col_name == "Пригодность*":
            var = tk.StringVar(value=current_value)
            combo = ttk.Combobox(popup, textvariable=var, values=["пригодно", "непригодно"], state="readonly")
            combo.pack(pady=20, padx=20, fill=tk.X)
            def save():
                new_val = var.get()
                values = list(self.arshin_tree.item(item, "values"))
                values[col_index] = new_val
                self.arshin_tree.item(item, values=values)
                popup.destroy()
            ttk.Button(popup, text="Сохранить", command=save, style="Success.TButton").pack(pady=10)
        else:
            entry = ttk.Entry(popup, font=("Segoe UI", 10))
            entry.insert(0, current_value)
            entry.pack(pady=20, padx=20, fill=tk.X)
            entry.focus()
            def save():
                new_val = entry.get()
                values = list(self.arshin_tree.item(item, "values"))
                values[col_index] = new_val
                self.arshin_tree.item(item, values=values)
                popup.destroy()
            popup.bind("<Return>", lambda e: save())
            ttk.Button(popup, text="Сохранить", command=save, style="Success.TButton").pack(pady=10)
    
    def arshin_download_template(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if filepath:
            try:
                create_arshin_template_csv(filepath)
                self.status_var.set(f"Шаблон CSV сохранён: {os.path.basename(filepath)}")
                messagebox.showinfo("Успех", f"Шаблон сохранён в кодировке UTF-8 с BOM\n{filepath}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
    
    def arshin_load_csv(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not filepath:
            return
        try:
            rows = read_csv_safe(filepath, skip_header=True)
            if not rows:
                messagebox.showwarning("Нет данных", "В файле нет данных для загрузки.")
                return
            for item in self.arshin_tree.get_children():
                self.arshin_tree.delete(item)
            loaded_count = 0
            for row in rows:
                row_ext = list(row) + [''] * (22 - len(row))
                if len(row_ext) > 6:
                    row_ext[6] = format_date(row_ext[6])
                if len(row_ext) > 7:
                    row_ext[7] = format_date(row_ext[7])
                if len(row_ext) > 8:
                    if is_unfit(row_ext[8]):
                        row_ext[8] = "непригодно"
                    else:
                        row_ext[8] = "пригодно"
                self.arshin_add_row(row_ext[:22])
                loaded_count += 1
            self.recolor_arshin_rows()
            self.status_var.set(f"Загружено {loaded_count} строк из {os.path.basename(filepath)}")
            messagebox.showinfo("Успех", f"Загружено {loaded_count} строк из файла\n{os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить CSV:\n{str(e)}")
    
    def arshin_generate_xml(self):
        if self.tm.arshin_func is None:
            messagebox.showerror("Ошибка", "Функция генерации XML для Аршин не загружена.")
            return
        data_rows = []
        for item in self.arshin_tree.get_children():
            values = list(self.arshin_tree.item(item, "values"))
            values = [str(v) if v is not None else "" for v in values]
            data_rows.append(values)
        if not data_rows:
            messagebox.showwarning("Нет данных", "Таблица пуста. Добавьте данные или загрузите CSV.")
            return
        try:
            xml_str = self.tm.arshin_func(data_rows)
            self.arshin_xml_text.delete(1.0, tk.END)
            self.arshin_xml_text.insert(tk.END, xml_str)
            self.status_var.set("XML для Аршин сгенерирован")
        except Exception as e:
            messagebox.showerror("Ошибка генерации", f"{str(e)}\n\n{traceback.format_exc()}")
    
    def arshin_save_xml(self):
        content = self.arshin_xml_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("Нет XML", "Сначала сгенерируйте XML.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("XML files", "*.xml")])
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            self.status_var.set(f"XML сохранён: {os.path.basename(filepath)}")
    
    def arshin_edit_template(self):
        self.open_template_editor("Аршин", DEFAULT_ARSHIN_XML_TEMPLATE, self.tm.update_arshin_template)
    
    def arshin_restore_template(self):
        success, msg = self.tm.restore_arshin()
        if success:
            messagebox.showinfo("Восстановление", "Шаблон для Аршин успешно восстановлен до стандартного.")
            self.status_var.set("Шаблон Аршин восстановлен.")
        else:
            messagebox.showerror("Ошибка", msg)
    
    # --------------------------------------------------------------
    # Вкладка аккредитации (аналогично)
    # --------------------------------------------------------------
    def init_accreditation_tab(self):
        btn_frame = ttk.Frame(self.accred_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        ttk.Button(btn_frame, text="➕ Добавить строку", command=self.accred_add_row,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="➖ Удалить строку", command=self.accred_remove_row,
                   style="Danger.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📥 Скачать шаблон CSV", command=self.accred_download_template,
                   style="Warning.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📂 Загрузить CSV", command=self.accred_load_csv,
                   style="Success.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="⚡ Сгенерировать XML", command=self.accred_generate_xml,
                   style="Primary.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="💾 Сохранить XML", command=self.accred_save_xml,
                   style="Success.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="✏ Редактировать шаблон", command=self.accred_edit_template,
                   style="Purple.TButton").pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🔄 Восстановить шаблон", command=self.accred_restore_template,
                   style="Warning.TButton").pack(side=tk.LEFT, padx=2)
        
        self.accred_columns = [
            "Номер Аршин*", "Тип СИ*", "Дата поверки*", "Дата действия*",
            "Результат*", "СНИЛС*", "ФИО*"
        ]
        self.accred_tree = ttk.Treeview(self.accred_frame, columns=self.accred_columns,
                                        show="headings", height=12, style="Treeview")
        for col in self.accred_columns:
            self.accred_tree.heading(col, text=col)
            self.accred_tree.column(col, width=160, anchor="center")
        
        v_scroll = ttk.Scrollbar(self.accred_frame, orient="vertical", command=self.accred_tree.yview)
        h_scroll = ttk.Scrollbar(self.accred_frame, orient="horizontal", command=self.accred_tree.xview)
        self.accred_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.accred_tree.pack(fill='both', expand=True, padx=10, pady=5)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.accred_tree.bind("<Double-1>", self.accred_edit_cell)
        
        self.accred_tree.tag_configure('oddrow', background='#f8f9fa')
        self.accred_tree.tag_configure('evenrow', background='#ffffff')
        
        example_row = [
            "С-ГЗО/18-07-2025/462546997", "ЗНОМ-35-65 У1", "18.07.2025", "17.07.2030",
            "пригодно", "10786907691", "Наседкин Дмитрий"
        ]
        self.accred_add_row(example_row)
        
        unfit_example = [
            "С-ГЗО/18-07-2025/462546998", "ЗНОМ-35-65 У1", "18.07.2025", "",
            "непригодно", "10786907692", "Иванов Петр"
        ]
        self.accred_add_row(unfit_example)
        
        xml_frame = ttk.LabelFrame(self.accred_frame, text="Результат XML для аккредитации", padding=5)
        xml_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        self.accred_xml_text = scrolledtext.ScrolledText(xml_frame, wrap=tk.NONE,
                                                         font=("Courier New", 10), bg="#fef9e4")
        self.accred_xml_text.pack(fill=tk.BOTH, expand=True)
    
    def accred_add_row(self, data=None):
        if data is None:
            empty = {col: "" for col in self.accred_columns}
            empty["Результат*"] = "пригодно"
            values = [empty[col] for col in self.accred_columns]
        else:
            data_full = list(data) + [''] * (7 - len(data))
            values = data_full[:7]
        row_count = len(self.accred_tree.get_children())
        tag = 'evenrow' if row_count % 2 == 0 else 'oddrow'
        self.accred_tree.insert("", tk.END, values=values, tags=(tag,))
    
    def accred_remove_row(self):
        selected = self.accred_tree.selection()
        if not selected:
            messagebox.showwarning("Удаление", "Выберите строку для удаления.")
            return
        for item in selected:
            self.accred_tree.delete(item)
        self.recolor_accred_rows()
    
    def recolor_accred_rows(self):
        children = self.accred_tree.get_children()
        for i, child in enumerate(children):
            tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            self.accred_tree.item(child, tags=(tag,))
    
    def accred_edit_cell(self, event):
        item = self.accred_tree.selection()[0]
        col = self.accred_tree.identify_column(event.x)
        col_index = int(col[1:]) - 1
        col_name = self.accred_columns[col_index]
        current = self.accred_tree.item(item, "values")[col_index]
        
        popup = tk.Toplevel(self.root)
        popup.title(f"Редактировать {col_name}")
        popup.geometry("450x130")
        popup.resizable(False, False)
        popup.grab_set()
        popup.configure(bg="#f0f4f8")
        
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 225
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 65
        popup.geometry(f"+{x}+{y}")
        
        if col_name == "Результат*":
            var = tk.StringVar(value=current)
            combo = ttk.Combobox(popup, textvariable=var, values=["пригодно", "непригодно"], state="readonly")
            combo.pack(pady=20, padx=20, fill=tk.X)
            def save():
                new_val = var.get()
                values = list(self.accred_tree.item(item, "values"))
                values[col_index] = new_val
                self.accred_tree.item(item, values=values)
                popup.destroy()
            ttk.Button(popup, text="Сохранить", command=save, style="Success.TButton").pack(pady=10)
        else:
            entry = ttk.Entry(popup, font=("Segoe UI", 10))
            entry.insert(0, current)
            entry.pack(pady=20, padx=20, fill=tk.X)
            entry.focus()
            def save():
                new_val = entry.get()
                values = list(self.accred_tree.item(item, "values"))
                values[col_index] = new_val
                self.accred_tree.item(item, values=values)
                popup.destroy()
            popup.bind("<Return>", lambda e: save())
            ttk.Button(popup, text="Сохранить", command=save, style="Success.TButton").pack(pady=10)
    
    def accred_download_template(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if filepath:
            try:
                create_accreditation_template_csv(filepath)
                self.status_var.set(f"Шаблон CSV для аккредитации сохранён: {os.path.basename(filepath)}")
                messagebox.showinfo("Успех", f"Шаблон сохранён в кодировке UTF-8 с BOM\n{filepath}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
    
    def accred_load_csv(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not filepath:
            return
        try:
            rows = read_csv_safe(filepath, skip_header=True)
            if not rows:
                messagebox.showwarning("Нет данных", "В файле нет данных для загрузки.")
                return
            for item in self.accred_tree.get_children():
                self.accred_tree.delete(item)
            loaded_count = 0
            for row in rows:
                row_ext = list(row) + [''] * (7 - len(row))
                if len(row_ext) > 2:
                    row_ext[2] = format_date(row_ext[2])
                if len(row_ext) > 3:
                    row_ext[3] = format_date(row_ext[3])
                if len(row_ext) > 4:
                    row_ext[4] = normalize_verification_result(row_ext[4])
                self.accred_add_row(row_ext[:7])
                loaded_count += 1
            self.recolor_accred_rows()
            self.status_var.set(f"Загружено {loaded_count} строк для аккредитации из {os.path.basename(filepath)}")
            messagebox.showinfo("Успех", f"Загружено {loaded_count} строк из файла\n{os.path.basename(filepath)}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить CSV:\n{str(e)}")
    
    def accred_generate_xml(self):
        if self.tm.accreditation_func is None:
            messagebox.showerror("Ошибка", "Функция генерации XML для аккредитации не загружена.")
            return
        data_rows = []
        for item in self.accred_tree.get_children():
            values = list(self.accred_tree.item(item, "values"))
            values = [str(v) if v is not None else "" for v in values]
            data_rows.append(values)
        if not data_rows:
            messagebox.showwarning("Нет данных", "Таблица аккредитации пуста.")
            return
        try:
            xml_str = self.tm.accreditation_func(data_rows)
            self.accred_xml_text.delete(1.0, tk.END)
            self.accred_xml_text.insert(tk.END, xml_str)
            self.status_var.set("XML для аккредитации сгенерирован")
        except Exception as e:
            messagebox.showerror("Ошибка генерации", f"{str(e)}\n\n{traceback.format_exc()}")
    
    def accred_save_xml(self):
        content = self.accred_xml_text.get(1.0, tk.END).strip()
        if not content:
            messagebox.showwarning("Нет XML", "Сначала сгенерируйте XML.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".xml", filetypes=[("XML files", "*.xml")])
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            self.status_var.set(f"XML сохранён: {os.path.basename(filepath)}")
    
    def accred_edit_template(self):
        self.open_template_editor("аккредитации", DEFAULT_ACCREDITATION_XML_TEMPLATE, self.tm.update_accreditation_template)
    
    def accred_restore_template(self):
        success, msg = self.tm.restore_accreditation()
        if success:
            messagebox.showinfo("Восстановление", "Шаблон для аккредитации успешно восстановлен до стандартного.")
            self.status_var.set("Шаблон аккредитации восстановлен.")
        else:
            messagebox.showerror("Ошибка", msg)
    
    # ------------------------------------------------------------------
    # Редактор шаблонов
    # ------------------------------------------------------------------
    def open_template_editor(self, name, initial_code, update_callback):
        editor = tk.Toplevel(self.root)
        editor.title(f"Редактирование шаблона XML для {name}")
        editor.geometry("950x650")
        editor.configure(bg="#2c3e50")
        
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 475
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 325
        editor.geometry(f"+{x}+{y}")
        
        warn_frame = tk.Frame(editor, bg="#e74c3c")
        warn_frame.pack(fill=tk.X, padx=10, pady=10)
        warn_label = tk.Label(warn_frame,
            text="⚠ ВНИМАНИЕ: Редактирование кода может привести к ошибкам. Будьте осторожны!\nЕсли что-то сломается, используйте кнопку «Восстановить стандартный шаблон».",
            bg="#e74c3c", fg="white", font=("Segoe UI", 10, "bold"), justify=tk.CENTER)
        warn_label.pack(pady=10)
        
        text_area = scrolledtext.ScrolledText(editor, wrap=tk.NONE, font=("Courier New", 10),
                                              bg="#fef9e4", fg="#2c3e50")
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        text_area.insert(tk.END, initial_code)
        
        btn_frame = tk.Frame(editor, bg="#2c3e50")
        btn_frame.pack(fill=tk.X, pady=10)
        
        def save_and_close():
            new_code = text_area.get(1.0, tk.END).strip()
            if not new_code:
                messagebox.showerror("Ошибка", "Код не может быть пустым.")
                return
            success, msg = update_callback(new_code)
            if success:
                messagebox.showinfo("Успех", msg)
                editor.destroy()
            else:
                messagebox.showerror("Ошибка", msg)
        
        ttk.Button(btn_frame, text="💾 Сохранить и применить", command=save_and_close,
                   style="Success.TButton").pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="❌ Отмена", command=editor.destroy,
                   style="Danger.TButton").pack(side=tk.LEFT, padx=10)

# ----------------------------------------------------------------------
# Запуск
# ----------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()