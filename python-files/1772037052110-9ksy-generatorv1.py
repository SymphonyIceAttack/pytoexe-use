import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import webbrowser
from datetime import datetime

class SberGeneratorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Генератор виджетов v.1")
        self.root.geometry("1920x1080")
        self.root.resizable(True, True)
        
        # Переменные для хранения данных
        self.org_name = tk.StringVar()
        self.inn = tk.StringVar()
        self.kpp = tk.StringVar()
        self.rs = tk.StringVar()
        self.ks = tk.StringVar()
        self.bik = tk.StringVar()
        self.bank_name = tk.StringVar()
        
        self.pay_key = tk.StringVar()
        self.pay_partner = tk.StringVar()
        
        self.ad_enabled = tk.BooleanVar(value=False)
        self.ad_key = tk.StringVar()
        self.ad_partner = tk.StringVar()
        self.erid = tk.StringVar()
        
        self.enable_number = tk.BooleanVar(value=True)
        self.enable_date = tk.BooleanVar(value=True)
        self.enable_preview = tk.BooleanVar(value=True)
        
        self.output_folder = tk.StringVar(value=os.path.expanduser("~/Desktop"))
        
        self.setup_ui()
        
    def setup_ui(self):
        # Заголовок
        header = tk.Frame(self.root, bg="#0B2A4A", height=80)
        header.pack(fill="x")
        header.pack_propagate(False)
        
        title = tk.Label(header, text="⚡ Генератор виджетов v.1.0 ⚡", 
                        font=("Arial", 20, "bold"), bg="#0B2A4A", fg="white")
        title.pack(expand=True)
        
        # Основной контейнер с прокруткой
        main_canvas = tk.Canvas(self.root, bg="#f0f7ff")
        main_canvas.pack(side="left", fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        scrollbar.pack(side="right", fill="y")
        
        main_canvas.configure(yscrollcommand=scrollbar.set)
        main_canvas.bind('<Configure>', lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        
        main_frame = tk.Frame(main_canvas, bg="#f0f7ff", padx=30, pady=20)
        main_canvas.create_window((0, 0), window=main_frame, anchor="nw")
        
        # Стили для виджетов
        style = ttk.Style()
        style.configure("Card.TFrame", background="white", relief="solid", borderwidth=1)
        
        # Левая колонка - Получатель
        left_frame = tk.Frame(main_frame, bg="white", relief="solid", borderwidth=1, padx=20, pady=20)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        tk.Label(left_frame, text="🏢 Получатель (юр.лицо)", font=("Arial", 14, "bold"), 
                bg="white", fg="black").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))
        
        # Поля получателя
             # Наименование организации
        tk.Label(left_frame, text="Наименование организации:", bg="white", fg="black", 
                font=("Arial", 10, "bold")).grid(row=1, column=0, columnspan=4, sticky="w", pady=(5,0))
        tk.Entry(left_frame, textvariable=self.org_name, font=("Arial", 11), 
                fg="black", bg="white", relief="solid", borderwidth=1).grid(row=2, column=0, columnspan=4, sticky="ew", padx=(0,0), pady=(0,10))
        
        # ИНН
        tk.Label(left_frame, text="ИНН:", bg="white", fg="black", 
                font=("Arial", 10, "bold")).grid(row=3, column=0, sticky="w", pady=(5,0))
        tk.Entry(left_frame, textvariable=self.inn, font=("Arial", 11), 
                width=20, fg="black", bg="white", relief="solid", borderwidth=1).grid(row=4, column=0, sticky="w", padx=(0,0), pady=(0,10))
        
        # КПП
        tk.Label(left_frame, text="КПП:", bg="white", fg="black", 
                font=("Arial", 10, "bold")).grid(row=3, column=2, sticky="w", pady=(5,0), padx=(20,0))
        tk.Entry(left_frame, textvariable=self.kpp, font=("Arial", 11), 
                width=20, fg="black", bg="white", relief="solid", borderwidth=1).grid(row=4, column=2, sticky="w", padx=(20,0), pady=(0,10))
        
        # Расчетный счет
        tk.Label(left_frame, text="Расчетный счет:", bg="white", fg="black", 
                font=("Arial", 10, "bold")).grid(row=5, column=0, columnspan=4, sticky="w", pady=(5,0))
        tk.Entry(left_frame, textvariable=self.rs, font=("Arial", 11), 
                width=40, fg="black", bg="white", relief="solid", borderwidth=1).grid(row=6, column=0, columnspan=4, sticky="ew", padx=(0,0), pady=(0,10))
        
        # БИК
        tk.Label(left_frame, text="БИК:", bg="white", fg="black", 
                font=("Arial", 10, "bold")).grid(row=7, column=0, sticky="w", pady=(5,0))
        tk.Entry(left_frame, textvariable=self.bik, font=("Arial", 11), 
                width=20, fg="black", bg="white", relief="solid", borderwidth=1).grid(row=8, column=0, sticky="w", padx=(0,0), pady=(0,10))
        
        # Корр. счет
        tk.Label(left_frame, text="Корр. счет:", bg="white", fg="black", 
                font=("Arial", 10, "bold")).grid(row=7, column=2, sticky="w", pady=(5,0), padx=(20,0))
        tk.Entry(left_frame, textvariable=self.ks, font=("Arial", 11), 
                width=20, fg="black", bg="white", relief="solid", borderwidth=1).grid(row=8, column=2, sticky="w", padx=(20,0), pady=(0,10))
        
        # Наименование банка
        tk.Label(left_frame, text="Наименование банка:", bg="white", fg="black", 
                font=("Arial", 10, "bold")).grid(row=9, column=0, columnspan=4, sticky="w", pady=(5,0))
        tk.Entry(left_frame, textvariable=self.bank_name, font=("Arial", 11), 
                width=40, fg="black", bg="white", relief="solid", borderwidth=1).grid(row=10, column=0, columnspan=4, sticky="ew", padx=(0,0), pady=(0,10))
                   
        # ПРАВАЯ ЧАСТЬ - теперь разделена на две колонки
        center_frame = tk.Frame(main_frame, bg="white", relief="solid", borderwidth=1, padx=20, pady=20)
        center_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        right_frame = tk.Frame(main_frame, bg="white", relief="solid", borderwidth=1, padx=20, pady=20)
        right_frame.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
        
        # ========== ЦЕНТРАЛЬНАЯ КОЛОНКА ==========
        # Кредитный виджет
        tk.Label(center_frame, text="🔑 Кредитный виджет", font=("Arial", 14, "bold"), 
                bg="white", fg="black").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))
        
        # Key
        tk.Label(center_frame, text="Key:", bg="white", fg="black", 
                font=("Arial", 10, "bold")).grid(row=1, column=0, columnspan=2, sticky="w", pady=(5,0))
        tk.Entry(center_frame, textvariable=self.pay_key, font=("Arial", 11), 
                width=30, fg="black", bg="white", relief="solid", borderwidth=1).grid(row=2, column=0, columnspan=2, sticky="ew", padx=(0,0), pady=(0,10))
        
        # PartnerID
        tk.Label(center_frame, text="PartnerID:", bg="white", fg="black", 
                font=("Arial", 10, "bold")).grid(row=3, column=0, columnspan=2, sticky="w", pady=(5,0))
        tk.Entry(center_frame, textvariable=self.pay_partner, font=("Arial", 11), 
                width=30, fg="black", bg="white", relief="solid", borderwidth=1).grid(row=4, column=0, columnspan=2, sticky="ew", padx=(0,0), pady=(0,10))
        
        # widgetId
        tk.Label(center_frame, text="widgetId: kvk", font=("Arial", 10, "bold"), 
                bg="white", fg="black").grid(row=5, column=0, columnspan=2, sticky="w", pady=(0,10))
        
        # Разделитель
        tk.Frame(center_frame, height=2, bg="#cccccc").grid(row=6, column=0, columnspan=2, sticky="ew", pady=20)
        
        # Рекламный виджет
        tk.Label(center_frame, text="📢 Рекламный виджет", font=("Arial", 14, "bold"), 
                bg="white", fg="black").grid(row=7, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        ad_check = tk.Checkbutton(center_frame, text="Добавить рекламный виджет", 
                                  variable=self.ad_enabled, command=self.toggle_ad_fields,
                                  bg="white", font=("Arial", 11), fg="black", activeforeground="black")
        ad_check.grid(row=8, column=0, columnspan=2, sticky="w", pady=(0, 10))
        
        # Блок рекламы (изначально скрыт)
        self.ad_frame = tk.Frame(center_frame, bg="#f8f9fa", relief="solid", borderwidth=1, padx=15, pady=15)
        self.ad_frame.grid(row=9, column=0, columnspan=2, sticky="ew", pady=(0, 20))
        self.ad_frame.grid_remove()
        
        # Key (рекламный)
        tk.Label(self.ad_frame, text="Key (рекламный):", bg="#f8f9fa", fg="black", 
                font=("Arial", 10, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(5,0))
        tk.Entry(self.ad_frame, textvariable=self.ad_key, font=("Arial", 11), 
                width=28, fg="black", bg="white", relief="solid", borderwidth=1).grid(row=1, column=0, columnspan=2, sticky="ew", padx=(0,0), pady=(0,10))
        
        # PartnerID (рекламный)
        tk.Label(self.ad_frame, text="PartnerID:", bg="#f8f9fa", fg="black", 
                font=("Arial", 10, "bold")).grid(row=2, column=0, columnspan=2, sticky="w", pady=(5,0))
        tk.Entry(self.ad_frame, textvariable=self.ad_partner, font=("Arial", 11), 
                width=28, fg="black", bg="white", relief="solid", borderwidth=1).grid(row=3, column=0, columnspan=2, sticky="ew", padx=(0,0), pady=(0,10))
        
        # widgetId (рекламный)
        tk.Label(self.ad_frame, text="widgetId: widgetAd", font=("Arial", 10, "bold"), 
                bg="#f8f9fa", fg="black").grid(row=4, column=0, columnspan=2, sticky="w", pady=(0,5))
        
        # ERID
        tk.Label(self.ad_frame, text="ERID:", bg="#f8f9fa", fg="black", 
                font=("Arial", 10, "bold")).grid(row=5, column=0, columnspan=2, sticky="w", pady=(5,0))
        tk.Entry(self.ad_frame, textvariable=self.erid, font=("Arial", 11), 
                width=28, fg="black", bg="white", relief="solid", borderwidth=1).grid(row=6, column=0, columnspan=2, sticky="ew", padx=(0,0), pady=(0,10))
        
        # ========== ПРАВАЯ КОЛОНКА ==========
        # Дополнительные поля
        tk.Label(right_frame, text="📋 Дополнительные поля", font=("Arial", 14, "bold"), 
                bg="white", fg="black").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 15))
        
        # Номер счета
        self.number_check = tk.Checkbutton(right_frame, text="Номер счета", variable=self.enable_number,
                                          bg="white", font=("Arial", 11), fg="black", activeforeground="black")
        self.number_check.grid(row=1, column=0, columnspan=2, sticky="w", pady=5)
        
        # Дата счета
        self.date_check = tk.Checkbutton(right_frame, text="Дата счета", variable=self.enable_date,
                                        bg="white", font=("Arial", 11), fg="black", activeforeground="black")
        self.date_check.grid(row=2, column=0, columnspan=2, sticky="w", pady=5)
        
        # Предпросмотр
        self.preview_check = tk.Checkbutton(right_frame, text="Показывать предпросмотр назначения платежа", 
                                           variable=self.enable_preview, bg="white", font=("Arial", 11), 
                                           fg="black", activeforeground="black", wraplength=200, justify="left")
        self.preview_check.grid(row=3, column=0, columnspan=2, sticky="w", pady=5)
        
        # Разделитель
        tk.Frame(right_frame, height=2, bg="#cccccc").grid(row=4, column=0, columnspan=2, sticky="ew", pady=20)
        
        # Информация
        tk.Label(right_frame, text="Эти поля появятся", bg="white", fg="black", 
                font=("Arial", 10, "italic")).grid(row=5, column=0, columnspan=2, sticky="w", pady=2)
        tk.Label(right_frame, text="на странице index.html", bg="white", fg="black", 
                font=("Arial", 10, "italic")).grid(row=6, column=0, columnspan=2, sticky="w", pady=2)
        
        # НАСТРОЙКА ВЕСОВ - чтобы колонки были одинаковой ширины
        main_frame.columnconfigure(0, weight=1, uniform="col")
        main_frame.columnconfigure(1, weight=1, uniform="col")
        main_frame.columnconfigure(2, weight=1, uniform="col")
        
        center_frame.columnconfigure(0, weight=1)
        right_frame.columnconfigure(0, weight=1)

        # Папка для сохранения
        folder_frame = tk.Frame(main_frame, bg="#f0f7ff")
        folder_frame.grid(row=3, column=0, columnspan=3, sticky="ew", padx=5, pady=10)
        folder_frame.columnconfigure(1, weight=1)
        
        tk.Label(folder_frame, text="Папка для сохранения:", bg="#f0f7ff", font=("Arial", 11)).grid(row=0, column=0, padx=(0,10))
        tk.Entry(folder_frame, textvariable=self.output_folder, font=("Arial", 11)).grid(row=0, column=1, sticky="ew", padx=(0,10))
        tk.Button(folder_frame, text="Обзор...", command=self.select_folder, 
                 bg="#6c757d", fg="white", font=("Arial", 10)).grid(row=0, column=2)
        
        # Статус (добавить после folder_frame)
        self.status_label = tk.Label(main_frame, text="✅ Готов к работе", bg="#f0f7ff", 
                                     fg="#28a745", font=("Arial", 11))
        self.status_label.grid(row=4, column=0, columnspan=3, pady=10)

        # Кнопки
        # Кнопки с фиксированной шириной в пикселях
        buttons_frame = tk.Frame(main_frame, bg="#f0f7ff")
        buttons_frame.grid(row=2, column=0, columnspan=3, pady=30)
        
        button_inner = tk.Frame(buttons_frame, bg="#f0f7ff")
        button_inner.pack(expand=True)
        
        btn_generate = tk.Button(button_inner, text="⚡ СГЕНЕРИРОВАТЬ ФАЙЛЫ", 
                                command=self.generate_files,
                                bg="#0B2A4A", fg="white", 
                                font=("Arial", 12),
                                width=25,  # Фиксированная ширина
                                height=2,
                                cursor="hand2")
        btn_generate.pack(side="left", padx=10)
        
        btn_clear = tk.Button(button_inner, text="🧹 ОЧИСТИТЬ ФОРМУ", 
                            command=self.clear_form,
                            bg="#6c757d", fg="white", 
                            font=("Arial", 12),
                            width=25,  # Такая же ширина
                            height=2,
                            cursor="hand2")
        btn_clear.pack(side="left", padx=10)
        
        # Настраиваем веса колонок
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
    def create_field(self, parent, label, variable, row, col, colspan=1):
        """Вспомогательная функция для создания поля ввода"""
        tk.Label(parent, text=label, bg=parent["bg"], font=("Arial", 9, "bold"), fg="black").grid(row=row, column=col, sticky="w", pady=(5,0))
        entry = tk.Entry(parent, textvariable=variable, font=("Arial", 11), width=20, fg="black", bg="white", relief="solid", borderwidth=1)
        entry.grid(row=row, column=col+1 if colspan==1 else col, columnspan=colspan, sticky="ew", padx=(5,0), pady=(5,0))
        return entry
    
    def toggle_ad_fields(self):
        """Показать/скрыть поля рекламного виджета"""
        if self.ad_enabled.get():
            self.ad_frame.grid()
        else:
            self.ad_frame.grid_remove()
    
    def select_folder(self):
        """Выбрать папку для сохранения"""
        folder = filedialog.askdirectory(title="Выберите папку для сохранения файлов")
        if folder:
            self.output_folder.set(folder)
    
    def clear_form(self):
        """Очистить все поля"""
        self.org_name.set("")
        self.inn.set("")
        self.kpp.set("")
        self.rs.set("")
        self.ks.set("")
        self.bik.set("")
        self.bank_name.set("")
        self.pay_key.set("")
        self.pay_partner.set("")
        self.ad_key.set("")
        self.ad_partner.set("")
        self.erid.set("")
        self.ad_enabled.set(False)
        self.ad_frame.grid_remove()
        self.enable_number.set(True)
        self.enable_date.set(True)
        self.enable_preview.set(True)
        self.status_label.config(text="✅ Форма очищена", fg="#28a745")
    
    def validate_data(self):
        """Проверить заполнение обязательных полей"""
        if not self.org_name.get().strip():
            messagebox.showerror("Ошибка", "Заполните наименование организации")
            return False
        if not self.inn.get().strip():
            messagebox.showerror("Ошибка", "Заполните ИНН")
            return False
        if not self.pay_key.get().strip():
            messagebox.showerror("Ошибка", "Заполните Key для кредитного виджета")
            return False
        if not self.pay_partner.get().strip():
            messagebox.showerror("Ошибка", "Заполните PartnerID для кредитного виджета")
            return False
        if self.ad_enabled.get() and not self.erid.get().strip():
            messagebox.showerror("Ошибка", "Заполните ERID для рекламного виджета")
            return False
        return True
    
    def generate_files(self):
        """Генерация файлов index.html и order.html"""
        if not self.validate_data():
            return
        
        try:
            # Собираем данные
            data = {
                'orgName': self.org_name.get().strip(),
                'inn': self.inn.get().strip(),
                'kpp': self.kpp.get().strip(),
                'rs': self.rs.get().strip(),
                'ks': self.ks.get().strip(),
                'bik': self.bik.get().strip(),
                'bankName': self.bank_name.get().strip(),
                'payKey': self.pay_key.get().strip(),
                'payPartner': self.pay_partner.get().strip(),
                'adEnabled': self.ad_enabled.get(),
                'adKey': self.ad_key.get().strip() if self.ad_enabled.get() else '',
                'adPartner': self.ad_partner.get().strip() if self.ad_enabled.get() else '',
                'erid': self.erid.get().strip() if self.ad_enabled.get() else '',
                'enableNumber': self.enable_number.get(),
                'enableDate': self.enable_date.get(),
                'enablePreview': self.enable_preview.get()
            }
            
            # Создаем файлы
            self.create_index_file(data)
            self.create_order_file(data)
            
            # Показываем успех
            folder = self.output_folder.get()
            self.status_label.config(text=f"✅ Файлы созданы: {folder}", fg="#28a745")
            messagebox.showinfo("Успех", f"Файлы успешно созданы в папке:\n{folder}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать файлы:\n{str(e)}")
            self.status_label.config(text="❌ Ошибка создания файлов", fg="#dc3545")
    
    def create_index_file(self, data):
        """Создание index.html"""
        # Формируем дополнительные поля
        extra_fields = ""
        if data['enableNumber'] and data['enableDate']:
            extra_fields = '''
        <div class="form-row">
            <div class="form-group">
                <label for="payment-purpose-number">Номер счета:</label>
                <input type="text" id="payment-purpose-number" placeholder="Например: УП-12345" oninput="updatePurposePreview()">
                <span class="hint">Введите номер счета плательщика</span>
            </div>
            <div class="form-group">
                <label for="invoice-date">Дата счета:</label>
                <input type="text" id="invoice-date" placeholder="ДД.ММ.ГГГГ" oninput="formatInvoiceDate(this); updatePurposePreview()">
                <span class="hint">Введите дату</span>
            </div>
        </div>'''
        elif data['enableNumber']:
            extra_fields = '''
        <div class="form-group">
            <label for="payment-purpose-number">Номер счета:</label>
            <input type="text" id="payment-purpose-number" placeholder="Например: УП-12345" oninput="updatePurposePreview()">
            <span class="hint">Введите номер счета плательщика</span>
        </div>'''
        elif data['enableDate']:
            extra_fields = '''
        <div class="form-group">
            <label for="invoice-date">Дата счета:</label>
            <input type="text" id="invoice-date" placeholder="ДД.ММ.ГГГГ" oninput="formatInvoiceDate(this); updatePurposePreview()">
            <span class="hint">Введите дату</span>
        </div>'''
        
        # Блок предпросмотра
        preview_block = '''
        <div class="purpose-preview">
            <h3>📄 Назначение платежа (информационно):</h3>
            <div id="purpose-preview-text" class="purpose-text">
                Оплата по счету № от . год. Сумма 0 руб. в т.ч НДС (22%) 0 руб.
            </div>
        </div>''' if data['enablePreview'] else ''
        
        index_content = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Создание заказа для Оплаты в кредит</title>
    <script src="https://widgetecom.ru/widgets-sdk.js"></script>
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        
        body {{
            font-family: Arial, sans-serif;
            max-width: 1000px;
            margin: 50px auto;
            padding: 0 20px;
            background: #f5f5f5;
        }}
        
        .container {{
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #007bff;
            margin-bottom: 10px;
            text-align: center;
            font-size: 24px;
        }}
        
        .description {{
            color: #666;
            text-align: center;
            margin-bottom: 30px;
            line-height: 1.5;
        }}
        
        .form-row {{
            display: flex;
            gap: 15px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }}
        
        .form-group {{
            flex: 1;
            min-width: 120px;
        }}
        
        .form-group.full-width {{
            flex: 0 0 100%;
        }}
        
        label {{
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #333;
            font-size: 14px;
        }}
        
        input {{
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 16px;
            font-family: Arial, sans-serif;
        }}
        
        input:focus {{
            outline: none;
            border-color: #007bff;
        }}
        
        .hint {{
            display: block;
            margin-top: 5px;
            color: #666;
            font-size: 13px;
        }}
        
        button {{
            width: 100%;
            padding: 14px;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: background 0.3s;
            font-family: Arial, sans-serif;
        }}
        
        button:hover {{
            background: #0056b3;
        }}
        
        .result {{
            margin-top: 20px;
            padding: 15px;
            background: #e9ecef;
            border-radius: 6px;
            display: none;
        }}
        
        .result.active {{
            display: block;
        }}
        
        .link {{
            word-break: break-all;
            background: white;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px;
            border: 1px solid #ddd;
            font-size: 14px;
            font-family: Arial, sans-serif;
        }}
        
        .copy-btn {{
            margin-top: 10px;
            background: #28a745;
        }}
        
        .copy-btn:hover {{
            background: #1e7e34;
        }}
        
        .note {{
            margin-top: 20px;
            padding: 10px;
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 4px;
            color: #856404;
            font-size: 14px;
        }}
        
        .purpose-preview {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 15px;
            margin: 20px 0;
        }}
        
        .purpose-preview h3 {{
            color: #495057;
            font-size: 16px;
            margin-bottom: 10px;
            font-family: Arial, sans-serif;
        }}
        
        .purpose-text {{
            background: white;
            padding: 12px;
            border-radius: 4px;
            border-left: 4px solid #007bff;
            font-size: 14px;
            font-family: Arial, sans-serif;
            word-break: break-word;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Создание заказа для Оплаты в кредит</h1>
        <p class="description">Введите данные для формирования ссылки клиенту</p>
        
        <div class="form-group full-width">
            <label for="order-amount">Сумма заказа (рубли):</label>
            <input 
                type="number" 
                id="order-amount" 
                placeholder="Например: 100000"
                min="1"
                step="1"              
                oninput="updatePurposePreview()"
            >
            <span class="hint">Введите сумму в рублях</span>
        </div>
        {extra_fields}
        {preview_block}
        <button id="generate-btn" onclick="generateLink()">Сформировать ссылку</button>
        
        <div id="result" class="result">
            <p><strong>Ссылка на оплату сформирована:</strong></p>
            <div id="order-link" class="link"></div>
            <button id="copy-btn" class="copy-btn" onclick="copyLink()">Копировать ссылку</button>
            <p style="margin-top: 10px; font-size: 14px; color: #666;">
                Отправьте эту ссылку клиенту или <a href="#" id="open-link" target="_blank">откройте для проверки</a>
            </p>
        </div>
        
        <div class="note">
            <strong>Примечание:</strong> Ссылка содержит уникальный идентификатор заказа. 
            Каждой сумме соответствует отдельная ссылка для оплаты.
        </div>
    </div>

    <script>
    // Глобальные функции для обработки
    window.generateLink = function() {{
        const amount = document.getElementById('order-amount').value.trim();
        if (!amount || parseInt(amount) < 1) {{
            alert('Введите корректную сумму (не менее 1 рубля)');
            document.getElementById('order-amount').focus();
            return;
        }}
        
        // Генерируем UUID
        function generateUUID() {{
            return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {{
                const r = Math.random() * 16 | 0;
                const v = c === 'x' ? r : (r & 0x3 | 0x8);
                return v.toString(16);
            }});
        }}
        
        // Получаем номер следующего заказа
        function getNextOrderNumber() {{
            let orderNumber = 1;
            const saved = localStorage.getItem('sberOrderCounter');
            if (saved) {{
                orderNumber = parseInt(saved) + 1;
            }}
            localStorage.setItem('sberOrderCounter', orderNumber.toString());
            return orderNumber;
        }}
        
        const extDataId = generateUUID();
        const internalOrderNumber = getNextOrderNumber();
        const purposeNum = document.getElementById('payment-purpose-number')?.value.trim() || '';
        const invDate = document.getElementById('invoice-date')?.value.trim() || '';
        
        // Формируем URL
        const baseUrl = window.location.href.substring(0, window.location.href.lastIndexOf('/') + 1);
        let orderUrl = baseUrl + 'order.html?amount=' + amount + '&id=' + extDataId + '&order=' + internalOrderNumber;
        if (purposeNum) orderUrl += '&purposeNum=' + encodeURIComponent(purposeNum);
        if (invDate) orderUrl += '&invoiceDate=' + encodeURIComponent(invDate);
        
        // Показываем результат
        document.getElementById('order-link').textContent = orderUrl;
        document.getElementById('open-link').href = orderUrl;
        document.getElementById('result').classList.add('active');
    }};
    
    window.copyLink = function() {{
        const linkText = document.getElementById('order-link').textContent;
        navigator.clipboard.writeText(linkText).then(function() {{
            const copyBtn = document.getElementById('copy-btn');
            copyBtn.textContent = 'Скопировано!';
            copyBtn.style.background = '#6c757d';
            setTimeout(function() {{
                copyBtn.textContent = 'Копировать ссылку';
                copyBtn.style.background = '#28a745';
            }}, 2000);
        }}).catch(function(err) {{
            console.error('Ошибка копирования:', err);
            alert('Не удалось скопировать ссылку');
        }});
    }};
    
    function formatInvoiceDate(input) {{
        let value = input.value.replace(/[^\\d]/g, '');
        if (value.length > 8) value = value.slice(0, 8);
        if (value.length >= 3 && value.length <= 4) value = value.slice(0, 2) + '.' + value.slice(2);
        else if (value.length >= 5) value = value.slice(0, 2) + '.' + value.slice(2, 4) + '.' + value.slice(4, 8);
        input.value = value;
    }}
    
    function formatDateForPurpose(dateStr) {{
        if (!dateStr) return {{ day: '', month: '', year: '' }};
        const parts = dateStr.split('.');
        if (parts.length === 3) {{
            const day = parts[0];
            let month = parts[1];
            const year = parts[2];
            const monthNames = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря'];
            const monthNum = parseInt(month, 10);
            const monthName = (monthNum >= 1 && monthNum <= 12) ? monthNames[monthNum - 1] : month;
            return {{ day, month: monthName, year }};
        }}
        return {{ day: '', month: '', year: '' }};
    }}
    
    function calculateVAT(amount) {{
        const amountNum = parseFloat(amount);
        if (isNaN(amountNum) || amountNum < 1) return 0;
        return Math.round(amountNum * 22 / 122);
    }}
    
    function formatAmount(amount) {{
        const num = parseFloat(amount);
        if (isNaN(num)) return '0';
        return num.toString().replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ' ');
    }}
    
    window.updatePurposePreview = function() {{
        const amount = document.getElementById('order-amount').value.trim();
        const invoiceNumber = document.getElementById('payment-purpose-number')?.value.trim() || '';
        const invoiceDate = document.getElementById('invoice-date')?.value.trim() || '';
        
        const vatAmount = calculateVAT(amount);
        const formattedAmount = formatAmount(amount);
        const formattedVat = formatAmount(vatAmount.toString());
        
        const {{ day, month, year }} = formatDateForPurpose(invoiceDate);
        
        let purposeText = '';
        if (invoiceNumber && day && month && year) {{
            purposeText = `Оплата по счету №${{invoiceNumber}} от ${{day}} ${{month}} ${{year}}г. Сумма ${{formattedAmount}} руб. в т.ч НДС (22%) ${{formattedVat}} руб.`;
        }} else if (invoiceNumber) {{
            purposeText = `Оплата по счету №${{invoiceNumber}}. Сумма ${{formattedAmount}} руб. в т.ч НДС (22%) ${{formattedVat}} руб.`;
        }} else {{
            purposeText = `Оплата. Сумма ${{formattedAmount}} руб. в т.ч НДС (22%) ${{formattedVat}} руб.`;
        }}
        
        const previewEl = document.getElementById('purpose-preview-text');
        if (previewEl) previewEl.textContent = purposeText;
    }};
    
    // Инициализация при загрузке
    document.addEventListener('DOMContentLoaded', function() {{
        // Обновляем предпросмотр при загрузке
        if (typeof updatePurposePreview === 'function') {{
            updatePurposePreview();
        }}
        
        // Фокус на поле ввода
        const amountInput = document.getElementById('order-amount');
        if (amountInput) {{
            amountInput.focus();
            amountInput.select();
        }}
    }});
    </script>
</body>
</html>'''.replace('{extra_fields}', extra_fields).replace('{preview_block}', preview_block)
        
        # Сохраняем файл
        filepath = os.path.join(self.output_folder.get(), 'index.html')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(index_content)
    
    def create_order_file(self, data):
        """Создание order.html"""
        # Блок рекламы
        ad_html = ''
        ad_init = ''
        if data['adEnabled']:
            ad_html = '<div class="ad-container"><div id="ad-widget"><div class="loading" style="padding:20px;"><div class="loading-spinner" style="width:30px;height:30px;"></div><p>Загрузка рекламы...</p></div></div></div>'
            ad_init = f'''
    function initAdWidget() {{
        if(!window.SberWidgetsSDK) {{ setTimeout(initAdWidget,100); return; }}
        var c = document.getElementById('ad-widget');
        if(!c) return;
        try {{
            window.SberWidgetsSDK.create({{
                widgetId: 'widgetAd',
                key: '{data['adKey']}',
                partnerId: '{data['adPartner']}',
                container: c,
                erid: '{data['erid']}',
                debugMode: true
            }});
        }} catch(e){{ console.error(e); }}
    }}'''
        
        order_content = f'''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Оплата в кредит</title>
    <script src="https://widgetecom.ru/widgets-sdk.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: Arial, sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        .page-wrapper {{
            background: white;
            width: 100%;
            max-width: 600px;
            padding: 30px 20px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            margin: 20px;
        }}
        
        .ad-container {{
            background: white;
            padding: 15px;
            border: 1px solid #eee;
            border-radius: 8px;
            margin-bottom: 25px;
        }}
        
        .payment-container {{
            padding: 20px;
            min-height: 300px;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        
        #payment-widget {{
            width: 100%;
            text-align: center;
        }}
        
        .loading {{
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }}
        
        .loading-spinner {{
            border: 4px solid #f3f3f3;
            border-top: 4px solid #007bff;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        .error {{
            text-align: center;
            padding: 60px 20px;
            color: #721c24;
        }}
        
        .error h3 {{
            margin-bottom: 15px;
        }}
    </style>
</head>
<body>
    <div class="page-wrapper">
        {ad_html}
        
        <div class="payment-container">
            <div id="payment-widget">
                <div class="loading">
                    <div class="loading-spinner"></div>
                    <p>Загрузка формы оплаты...</p>
                </div>
            </div>
        </div>
    </div>

    <script>
    // Данные заказа
    let currentOrder = {{
        extDataId: null,
        orderNumber: null,
        amount: null,
        purposeNumber: null,
        invoiceDate: null
    }};
    
    // Данные получателя
    const PARTNER_CONFIG = {{
        payment: {{ key: '{data['payKey']}', partnerId: '{data['payPartner']}', widgetId: 'kvk' }},
        recipient: {{
            name: '{data['orgName']}',
            accountNumber: '{data['rs']}',
            inn: '{data['inn']}',
            kpp: '{data['kpp']}',
            corrAccount: '{data['ks']}',
            bic: '{data['bik']}',
            nameBank: '{data['bankName']}'
        }}
    }};
    
    {ad_init}
    
    function getUrlParams() {{
        const params = new URLSearchParams(window.location.search);
        return {{
            amount: params.get('amount'),
            id: params.get('id'),
            order: params.get('order'),
            purposeNum: params.get('purposeNum'),
            invoiceDate: params.get('invoiceDate')
        }};
    }}
    
    function formatDateForPurpose(dateStr) {{
        if (!dateStr) return {{ day: '', month: '', year: '' }};
        const parts = dateStr.split('.');
        if (parts.length === 3) {{
            const day = parts[0];
            let month = parts[1];
            const year = parts[2];
            const monthNames = ['января','февраля','марта','апреля','мая','июня','июля','августа','сентября','октября','ноября','декабря'];
            const monthNum = parseInt(month, 10);
            const monthName = (monthNum >= 1 && monthNum <= 12) ? monthNames[monthNum - 1] : month;
            return {{ day, month: monthName, year }};
        }}
        return {{ day: '', month: '', year: '' }};
    }}
    
    function formatAmount(amount) {{
        const num = parseFloat(amount);
        if (isNaN(num)) return '0';
        return num.toString().replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, ' ');
    }}
    
    function calculateVAT(amount) {{
        const amountNum = parseFloat(amount);
        if (isNaN(amountNum)) return '0';
        return Math.round(amountNum * 22 / 122).toString();
    }}
    
    function loadOrderData() {{
        const urlParams = getUrlParams();
        
        if (urlParams.amount && urlParams.id && urlParams.order) {{
            currentOrder = {{
                amount: urlParams.amount,
                extDataId: urlParams.id,
                orderNumber: parseInt(urlParams.order) || 1,
                purposeNumber: urlParams.purposeNum || '',
                invoiceDate: urlParams.invoiceDate || ''
            }};
            localStorage.setItem('sberCurrentOrder', JSON.stringify(currentOrder));
            return true;
        }}
        
        const saved = localStorage.getItem('sberCurrentOrder');
        if (saved) {{
            try {{
                const parsed = JSON.parse(saved);
                if (parsed.amount && parsed.extDataId && parsed.orderNumber) {{
                    currentOrder = parsed;
                    return true;
                }}
            }} catch (e) {{
                console.error('Ошибка загрузки:', e);
            }}
        }}
        return false;
    }}
    
    function initPaymentWidget() {{
        if (!currentOrder.extDataId || !currentOrder.amount || !currentOrder.orderNumber) {{
            document.getElementById('payment-widget').innerHTML = '<div class="error"><h3>Ошибка загрузки данных заказа</h3></div>';
            return;
        }}
        
        if (!window.SberWidgetsSDK) {{
            setTimeout(initPaymentWidget, 100);
            return;
        }}
        
        const container = document.getElementById('payment-widget');
        if (!container) return;
        
        const formattedAmount = currentOrder.amount.includes('.') ? currentOrder.amount : currentOrder.amount + '.00';
        const vatAmount = calculateVAT(currentOrder.amount) + '.00';
        
        let purposeText = 'Оплата';
        if (currentOrder.purposeNumber) purposeText += ' по счету №' + currentOrder.purposeNumber;
        if (currentOrder.invoiceDate) {{
            const {{ day, month, year }} = formatDateForPurpose(currentOrder.invoiceDate);
            if (day && month && year) purposeText += ' от ' + day + ' ' + month + ' ' + year + 'г.';
        }}
        purposeText += '. Сумма ' + formatAmount(currentOrder.amount) + ' руб. в т.ч НДС (22%) ' + formatAmount(calculateVAT(currentOrder.amount)) + ' руб.';
        
        const orderData = {{
            extDataId: currentOrder.extDataId,
            orderNumber: currentOrder.orderNumber.toString(),
            amount: formattedAmount,
            isPartPayment: true,
            purpose: purposeText,
            name: PARTNER_CONFIG.recipient.name,
            accountData: {{
                accountNumber: PARTNER_CONFIG.recipient.accountNumber,
                inn: PARTNER_CONFIG.recipient.inn,
                kpp: PARTNER_CONFIG.recipient.kpp,
                corrAccount: PARTNER_CONFIG.recipient.corrAccount,
                bic: PARTNER_CONFIG.recipient.bic,
                nameBank: PARTNER_CONFIG.recipient.nameBank
            }},
            vatData: {{
                amount: vatAmount,
                calcMethod: 'ONTOP',
                rate: 22
            }}
        }};
        
        try {{
            container.innerHTML = '';
            window.SberWidgetsSDK.create({{
                widgetId: PARTNER_CONFIG.payment.widgetId,
                key: PARTNER_CONFIG.payment.key,
                partnerId: PARTNER_CONFIG.payment.partnerId,
                container: container,
                orderData: orderData,
                debugMode: true,
                onReceivedOrderDataStatuses: async function(data) {{
                    console.log('Получены статусы:', data);
                    return Promise.resolve();
                }}
            }});
        }} catch (error) {{
            console.error('Ошибка виджета:', error);
            container.innerHTML = '<div class="error"><h3>Не удалось загрузить форму оплаты</h3></div>';
        }}
    }}
    
    document.addEventListener('DOMContentLoaded', function() {{
        if (!loadOrderData()) {{
            document.getElementById('payment-widget').innerHTML = '<div class="error"><h3>Ссылка на оплату недействительна</h3></div>';
            return;
        }}
        
        { 'setTimeout(initAdWidget, 500);' if data['adEnabled'] else '' }
        setTimeout(initPaymentWidget, 800);
    }});
    
    window.addEventListener('beforeunload', function() {{
        if (currentOrder.extDataId && currentOrder.amount) {{
            localStorage.setItem('sberCurrentOrder', JSON.stringify(currentOrder));
        }}
    }});
    </script>
</body>
</html>'''
        
        # Сохраняем файл
        filepath = os.path.join(self.output_folder.get(), 'order.html')
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(order_content)

if __name__ == "__main__":
    root = tk.Tk()
    app = SberGeneratorGUI(root)
    root.mainloop()