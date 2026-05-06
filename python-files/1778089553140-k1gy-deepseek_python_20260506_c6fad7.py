import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter import scrolledtext
import re
import os
import csv
from datetime import datetime
from typing import List, Dict, Any
import sys
import traceback

# ----------------------------------------------------------------------
# Базовые шаблоны для генерации XML (могут быть отредактированы пользователем)
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
# Вспомогательные функции (не изменяются пользователем)
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
# Класс для управления пользовательскими шаблонами (с возможностью восстановления)
# ----------------------------------------------------------------------
class TemplateManager:
    def __init__(self):
        self.arshin_func = None
        self.accreditation_func = None
        self.load_defaults()
    
    def load_defaults(self):
        # Загружаем стандартные функции
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
    
    def restore_defaults(self):
        """Восстанавливает стандартные шаблоны для обеих функций."""
        self.load_defaults()
        return True, "Стандартные шаблоны успешно восстановлены."
    
    def update_arshin_template(self, code_text):
        """Обновить функцию генерации для Аршин."""
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

# ----------------------------------------------------------------------
# Работа с CSV (шаблоны для загрузки данных)
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

def read_csv_data(filepath: str, skip_header=True) -> List[List[str]]:
    rows = []
    with open(filepath, 'r', encoding='utf-8-sig', newline='') as f:
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            rows.append([cell.strip() for cell in row])
    if skip_header and len(rows) > 1:
        rows = rows[1:]
    rows = [r for r in rows if any(cell for cell in r)]
    return rows

# ----------------------------------------------------------------------
# GUI-класс
# ----------------------------------------------------------------------
class App:
    def __init__(self, root):
        self.root = root
        root.title("Генератор XML для Аршин и Росаккредитации")
        root.geometry("1350x850")
        root.configure(bg="#f0f0f0")
        
        # Менеджер шаблонов
        self.tm = TemplateManager()
        
        # Верхняя панель с информацией о разработчике
        top_frame = tk.Frame(root, bg="#2c3e50", height=40)
        top_frame.pack(fill=tk.X, side=tk.TOP)
        dev_label = tk.Label(top_frame, text="Разработчик: Омельченко Алексей | Версия 2.1 (с восстановлением шаблонов)", 
                             bg="#2c3e50", fg="white", font=("Arial", 10))
        dev_label.pack(pady=5)
        
        # Основной блок с вкладками
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.arshin_frame = ttk.Frame(self.notebook)
        self.accred_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.arshin_frame, text="🏭 Генератор XML для Аршин")
        self.notebook.add(self.accred_frame, text="⚡ Конфигуратор аккредитации")
        
        self.init_arshin_tab()
        self.init_accreditation_tab()
        
        # Статусная строка
        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе (CSV формат)")
        status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    # --------------------------------------------------------------
    # Вкладка Аршин
    # --------------------------------------------------------------
    def init_arshin_tab(self):
        # Панель кнопок
        btn_frame = ttk.Frame(self.arshin_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="➕ Добавить строку", command=self.arshin_add_row).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="➖ Удалить строку", command=self.arshin_remove_row).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📥 Скачать шаблон CSV", command=self.arshin_download_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📂 Загрузить CSV", command=self.arshin_load_csv).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="⚡ Сгенерировать XML", command=self.arshin_generate_xml).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="💾 Сохранить XML", command=self.arshin_save_xml).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="✏ Редактировать шаблон XML", command=self.arshin_edit_template).pack(side=tk.LEFT, padx=2)
        # Новая кнопка восстановления
        ttk.Button(btn_frame, text="🔄 Восстановить стандартный шаблон", command=self.arshin_restore_template).pack(side=tk.LEFT, padx=2)
        
        # Таблица
        self.arshin_columns = [
            "Номер в ГРСИ*", "Зав. номер*", "Год*", "Модификация", "Шифр знака*", "Владелец*",
            "Дата поверки*", "Дата действия", "Пригодность*", "Причина непригодности",
            "Документ*", "Метролог*", "Эталон*", "Тип СИ1", "Тип СИ2", "Тип СИ3",
            "№ СИ1", "№ СИ2", "№ СИ3", "Температура", "Давление", "Влажность"
        ]
        self.arshin_tree = ttk.Treeview(self.arshin_frame, columns=self.arshin_columns, show="headings", height=12)
        for col in self.arshin_columns:
            self.arshin_tree.heading(col, text=col)
            self.arshin_tree.column(col, width=120, anchor="center")
        
        v_scroll = ttk.Scrollbar(self.arshin_frame, orient="vertical", command=self.arshin_tree.yview)
        h_scroll = ttk.Scrollbar(self.arshin_frame, orient="horizontal", command=self.arshin_tree.xview)
        self.arshin_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.arshin_tree.pack(fill='both', expand=True, padx=5, pady=5)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.arshin_tree.bind("<Double-1>", self.arshin_edit_cell)
        
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
        xml_frame = ttk.LabelFrame(self.arshin_frame, text="Результат XML для Аршин")
        xml_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.arshin_xml_text = scrolledtext.ScrolledText(xml_frame, wrap=tk.NONE, font=("Courier New", 10))
        self.arshin_xml_text.pack(fill=tk.BOTH, expand=True)
    
    def arshin_add_row(self, data=None):
        if data is None:
            empty_vals = {col: "" for col in self.arshin_columns}
            empty_vals["Пригодность*"] = "пригодно"
            values = [empty_vals[col] for col in self.arshin_columns]
        else:
            data_full = list(data) + [''] * (22 - len(data))
            values = data_full[:22]
        self.arshin_tree.insert("", tk.END, values=values)
    
    def arshin_remove_row(self):
        selected = self.arshin_tree.selection()
        if not selected:
            messagebox.showwarning("Удаление", "Выберите строку для удаления.")
            return
        for item in selected:
            self.arshin_tree.delete(item)
    
    def arshin_edit_cell(self, event):
        item = self.arshin_tree.selection()[0]
        col = self.arshin_tree.identify_column(event.x)
        col_index = int(col[1:]) - 1
        col_name = self.arshin_columns[col_index]
        current_value = self.arshin_tree.item(item, "values")[col_index]
        
        popup = tk.Toplevel(self.root)
        popup.title(f"Редактировать {col_name}")
        popup.geometry("400x100")
        popup.grab_set()
        
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
            ttk.Button(popup, text="Сохранить", command=save).pack(pady=10)
        else:
            entry = ttk.Entry(popup)
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
            ttk.Button(popup, text="Сохранить", command=save).pack(pady=10)
    
    def arshin_download_template(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if filepath:
            try:
                create_arshin_template_csv(filepath)
                self.status_var.set(f"Шаблон CSV сохранён: {filepath}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
    
    def arshin_load_csv(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not filepath:
            return
        try:
            rows = read_csv_data(filepath, skip_header=True)
            for item in self.arshin_tree.get_children():
                self.arshin_tree.delete(item)
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
                self.arshin_tree.insert("", tk.END, values=row_ext[:22])
            self.status_var.set(f"Загружено {len(rows)} строк из {filepath}")
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
            self.status_var.set(f"XML сохранён: {filepath}")
    
    def arshin_edit_template(self):
        """Открыть окно редактирования шаблона для Аршин."""
        # Для удобства, в редакторе всегда показываем стандартный шаблон,
        # чтобы пользователь мог вернуться к нему, но на самом деле применяет текущий код.
        # Однако лучше показывать текущий активный шаблон, но его сложно извлечь из функции.
        # Для простоты показываем DEFAULT_ARSHIN_XML_TEMPLATE.
        current_code = DEFAULT_ARSHIN_XML_TEMPLATE
        self.open_template_editor("Аршин", current_code, self.tm.update_arshin_template)
    
    def arshin_restore_template(self):
        """Восстановить стандартный шаблон для Аршин."""
        # Восстанавливаем только для Аршин, но можно и оба. Сделаем выборочно.
        # Загружаем заново DEFAULT_ARSHIN_XML_TEMPLATE
        exec_globals = {
            'safe_xml': safe_xml,
            'format_date': format_date,
            'is_unfit': is_unfit,
            'normalize_verification_result': normalize_verification_result,
            'split_full_name': split_full_name,
        }
        try:
            exec(DEFAULT_ARSHIN_XML_TEMPLATE, exec_globals)
            self.tm.arshin_func = exec_globals['generate_arshin_xml']
            messagebox.showinfo("Восстановление", "Шаблон для Аршин успешно восстановлен до стандартного.")
            self.status_var.set("Шаблон Аршин восстановлен.")
        except Exception as e:
            messagebox.showerror("Ошибка восстановления", str(e))
    
    # --------------------------------------------------------------
    # Вкладка аккредитации
    # --------------------------------------------------------------
    def init_accreditation_tab(self):
        btn_frame = ttk.Frame(self.accred_frame)
        btn_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(btn_frame, text="➕ Добавить строку", command=self.accred_add_row).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="➖ Удалить строку", command=self.accred_remove_row).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📥 Скачать шаблон CSV", command=self.accred_download_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="📂 Загрузить CSV", command=self.accred_load_csv).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="⚡ Сгенерировать XML", command=self.accred_generate_xml).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="💾 Сохранить XML", command=self.accred_save_xml).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="✏ Редактировать шаблон XML", command=self.accred_edit_template).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="🔄 Восстановить стандартный шаблон", command=self.accred_restore_template).pack(side=tk.LEFT, padx=2)
        
        self.accred_columns = [
            "Номер Аршин*", "Тип СИ*", "Дата поверки*", "Дата действия*",
            "Результат*", "СНИЛС*", "ФИО*"
        ]
        self.accred_tree = ttk.Treeview(self.accred_frame, columns=self.accred_columns, show="headings", height=12)
        for col in self.accred_columns:
            self.accred_tree.heading(col, text=col)
            self.accred_tree.column(col, width=150, anchor="center")
        
        v_scroll = ttk.Scrollbar(self.accred_frame, orient="vertical", command=self.accred_tree.yview)
        h_scroll = ttk.Scrollbar(self.accred_frame, orient="horizontal", command=self.accred_tree.xview)
        self.accred_tree.configure(yscrollcommand=v_scroll.set, xscrollcommand=h_scroll.set)
        self.accred_tree.pack(fill='both', expand=True, padx=5, pady=5)
        v_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        h_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.accred_tree.bind("<Double-1>", self.accred_edit_cell)
        
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
        
        xml_frame = ttk.LabelFrame(self.accred_frame, text="Результат XML для аккредитации")
        xml_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.accred_xml_text = scrolledtext.ScrolledText(xml_frame, wrap=tk.NONE, font=("Courier New", 10))
        self.accred_xml_text.pack(fill=tk.BOTH, expand=True)
    
    def accred_add_row(self, data=None):
        if data is None:
            empty = {col: "" for col in self.accred_columns}
            empty["Результат*"] = "пригодно"
            values = [empty[col] for col in self.accred_columns]
        else:
            data_full = list(data) + [''] * (7 - len(data))
            values = data_full[:7]
        self.accred_tree.insert("", tk.END, values=values)
    
    def accred_remove_row(self):
        selected = self.accred_tree.selection()
        if not selected:
            messagebox.showwarning("Удаление", "Выберите строку для удаления.")
            return
        for item in selected:
            self.accred_tree.delete(item)
    
    def accred_edit_cell(self, event):
        item = self.accred_tree.selection()[0]
        col = self.accred_tree.identify_column(event.x)
        col_index = int(col[1:]) - 1
        col_name = self.accred_columns[col_index]
        current = self.accred_tree.item(item, "values")[col_index]
        
        popup = tk.Toplevel(self.root)
        popup.title(f"Редактировать {col_name}")
        popup.geometry("400x100")
        popup.grab_set()
        
        if col_name == "Результат*":
            var = tk.StringVar(value=current)
            combo = ttk.Combobox(popup, textvariable=var, values=["пригодно", "непригодно"], state="readonly")
            combo.pack(pady=20, fill=tk.X, padx=20)
            def save():
                values = list(self.accred_tree.item(item, "values"))
                values[col_index] = var.get()
                self.accred_tree.item(item, values=values)
                popup.destroy()
            ttk.Button(popup, text="Сохранить", command=save).pack(pady=10)
        else:
            entry = ttk.Entry(popup)
            entry.insert(0, current)
            entry.pack(pady=20, fill=tk.X, padx=20)
            entry.focus()
            def save():
                values = list(self.accred_tree.item(item, "values"))
                values[col_index] = entry.get()
                self.accred_tree.item(item, values=values)
                popup.destroy()
            popup.bind("<Return>", lambda e: save())
            ttk.Button(popup, text="Сохранить", command=save).pack(pady=10)
    
    def accred_download_template(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if filepath:
            try:
                create_accreditation_template_csv(filepath)
                self.status_var.set(f"Шаблон CSV для аккредитации сохранён: {filepath}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))
    
    def accred_load_csv(self):
        filepath = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if not filepath:
            return
        try:
            rows = read_csv_data(filepath, skip_header=True)
            for item in self.accred_tree.get_children():
                self.accred_tree.delete(item)
            for row in rows:
                row_ext = list(row) + [''] * (7 - len(row))
                if len(row_ext) > 2:
                    row_ext[2] = format_date(row_ext[2])
                if len(row_ext) > 3:
                    row_ext[3] = format_date(row_ext[3])
                if len(row_ext) > 4:
                    row_ext[4] = normalize_verification_result(row_ext[4])
                self.accred_tree.insert("", tk.END, values=row_ext[:7])
            self.status_var.set(f"Загружено {len(rows)} строк для аккредитации")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))
    
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
            self.status_var.set(f"XML сохранён: {filepath}")
    
    def accred_edit_template(self):
        current_code = DEFAULT_ACCREDITATION_XML_TEMPLATE
        self.open_template_editor("аккредитации", current_code, self.tm.update_accreditation_template)
    
    def accred_restore_template(self):
        """Восстановить стандартный шаблон для аккредитации."""
        exec_globals = {
            'safe_xml': safe_xml,
            'format_date': format_date,
            'is_unfit': is_unfit,
            'normalize_verification_result': normalize_verification_result,
            'split_full_name': split_full_name,
        }
        try:
            exec(DEFAULT_ACCREDITATION_XML_TEMPLATE, exec_globals)
            self.tm.accreditation_func = exec_globals['generate_accreditation_xml']
            messagebox.showinfo("Восстановление", "Шаблон для аккредитации успешно восстановлен до стандартного.")
            self.status_var.set("Шаблон аккредитации восстановлен.")
        except Exception as e:
            messagebox.showerror("Ошибка восстановления", str(e))
    
    # ------------------------------------------------------------------
    # Общий редактор шаблонов
    # ------------------------------------------------------------------
    def open_template_editor(self, name, initial_code, update_callback):
        editor = tk.Toplevel(self.root)
        editor.title(f"Редактирование шаблона XML для {name}")
        editor.geometry("900x600")
        
        # Предупреждение
        warn_frame = tk.Frame(editor, bg="#ffcccc")
        warn_frame.pack(fill=tk.X, padx=5, pady=5)
        warn_label = tk.Label(warn_frame, text="ВНИМАНИЕ: Редактирование кода может привести к ошибкам. Будьте осторожны!\nЕсли что-то сломается, используйте кнопку «Восстановить стандартный шаблон».",
                              bg="#ffcccc", fg="#990000", font=("Arial", 10, "bold"))
        warn_label.pack(pady=5)
        
        # Текстовое поле с кодом
        text_area = scrolledtext.ScrolledText(editor, wrap=tk.NONE, font=("Courier New", 10))
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        text_area.insert(tk.END, initial_code)
        
        # Кнопки
        btn_frame = tk.Frame(editor)
        btn_frame.pack(fill=tk.X, pady=5)
        
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
        
        ttk.Button(btn_frame, text="Сохранить и применить", command=save_and_close).pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Отмена", command=editor.destroy).pack(side=tk.LEFT, padx=10)

# ----------------------------------------------------------------------
# Запуск
# ----------------------------------------------------------------------
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()