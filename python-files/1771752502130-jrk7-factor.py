# sales_management_pro.py
# فروشگاه پیشرفته - سیستم مدیریت خرید و فروش با رابط کاربری مدرن

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime, timedelta
from tkinter import font
import calendar
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, inch
import jdatetime
from persiantools.jdatetime import JalaliDate
import arabic_reshaper
import bidi.algorithm as bidi
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

# ==================== کلاس راهنمای ابزار (Tooltip) ====================
class ToolTip:
    """کلاس ایجاد راهنمای ابزار برای دکمه‌ها"""
    
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip_window = None
        self.widget.bind('<Enter>', self.show_tip)
        self.widget.bind('<Leave>', self.hide_tip)
        self.widget.bind('<ButtonPress>', self.hide_tip)
    
    def show_tip(self, event=None):
        """نمایش راهنمای ابزار"""
        if self.tip_window or not self.text:
            return
        
        x, y, _, _ = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + self.widget.winfo_rooty() + 25
        
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        # استایل راهنما
        frame = tk.Frame(tw, bg="#ffffcc", relief=tk.SOLID, borderwidth=1)
        frame.pack()
        
        label = tk.Label(frame, text=self.text, justify=tk.RIGHT,
                        bg="#ffffcc", fg="#000000", font=("B Nazanin", 10),
                        padx=5, pady=3)
        label.pack()
    
    def hide_tip(self, event=None):
        """مخفی کردن راهنمای ابزار"""
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

# ==================== کلاس پیشرفته سیستم فروش ====================
class AdvancedSalesManagementSystem:
    def __init__(self, root):
        self.root = root
        self.root.title("🌟 سیستم مدیریت خرید و فروش پیشرفته")
        self.root.geometry("1400x750+50+50")
        
        # تنظیم رنگ‌های مدرن
        self.colors = {
            'primary': '#2196F3',      # آبی
            'success': '#4CAF50',       # سبز
            'danger': '#F44336',        # قرمز
            'warning': '#FFC107',        # زرد
            'info': '#00BCD4',           # فیروزه‌ای
            'dark': '#2C3E50',            # سرمه‌ای
            'light': '#F5F5F5',           # خاکستری روشن
            'white': '#FFFFFF',            # سفید
            'gold': '#FFD700',              # طلایی
            'purple': '#9C27B0',             # بنفش
            'orange': '#FF9800',              # نارنجی
            'teal': '#009688',                 # سبز فیروزه‌ای
        }
        
        # تنظیم فونت فارسی
        self.setup_persian_fonts()
        
        # تنظیم استایل
        self.setup_styles()
        
        # تنظیم راست به چپ
        self.root.tk.call('encoding', 'system', 'utf-8')
        
        # متغیرها
        self.items = []
        self.report_start_time = datetime.now()
        self.saved_data = {}
        self.load_saved_data()
        self.current_theme = 'light'
        
        # ایجاد منوها
        self.create_menu()
        
        # ایجاد فریم‌های اصلی
        self.create_main_frames()
        
        # ایجاد ویجت‌ها
        self.create_widgets()
        
        # ایجاد نوار وضعیت
        self.create_status_bar()
        
        # به‌روزرسانی زمان گزارش
        self.update_report_time()
        
    def setup_persian_fonts(self):
        """تنظیم فونت‌های فارسی"""
        try:
            self.font_title = font.Font(family="B Nazanin", size=18, weight="bold")
            self.font_normal = font.Font(family="B Nazanin", size=11)
            self.font_small = font.Font(family="B Nazanin", size=9)
            self.font_awesome = font.Font(family="Segoe UI", size=12)  # برای آیکون‌ها
        except:
            self.font_title = font.Font(family="Tahoma", size=16, weight="bold")
            self.font_normal = font.Font(family="Tahoma", size=10)
            self.font_small = font.Font(family="Tahoma", size=8)
            self.font_awesome = font.Font(family="Segoe UI", size=11)
    
    def setup_styles(self):
        """تنظیم استایل‌های پیشرفته"""
        style = ttk.Style()
        
        # استایل دکمه‌های مدرن
        style.configure('Primary.TButton', 
                       background=self.colors['primary'],
                       foreground='white',
                       font=self.font_normal,
                       padding=(20, 10))
        
        style.configure('Success.TButton',
                       background=self.colors['success'],
                       foreground='white',
                       font=self.font_normal,
                       padding=(20, 10))
        
        style.configure('Danger.TButton',
                       background=self.colors['danger'],
                       foreground='white',
                       font=self.font_normal,
                       padding=(20, 10))
        
        style.configure('Warning.TButton',
                       background=self.colors['warning'],
                       foreground='black',
                       font=self.font_normal,
                       padding=(20, 10))
        
        style.configure('Gold.TButton',
                       background=self.colors['gold'],
                       foreground='black',
                       font=self.font_normal,
                       padding=(20, 10))
    
    def create_menu(self):
        """ایجاد منوی پیشرفته"""
        menubar = tk.Menu(self.root, bg=self.colors['dark'], fg='white')
        self.root.config(menu=menubar)
        
        # منوی فایل
        file_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['dark'], fg='white')
        menubar.add_cascade(label="📁 فایل", menu=file_menu, font=self.font_normal)
        file_menu.add_command(label="🆕 گزارش جدید", command=self.new_report, 
                             font=self.font_normal, accelerator="Ctrl+N")
        file_menu.add_command(label="💾 ذخیره داده‌ها", command=self.save_current_data, 
                             font=self.font_normal, accelerator="Ctrl+S")
        file_menu.add_separator()
        file_menu.add_command(label="📤 خروجی Excel", command=self.export_to_excel, 
                             font=self.font_normal)
        file_menu.add_command(label="📥 ورود Excel", command=self.import_from_excel, 
                             font=self.font_normal)
        file_menu.add_separator()
        file_menu.add_command(label="🚪 خروج", command=self.root.quit, 
                             font=self.font_normal, accelerator="Alt+F4")
        
        # منوی گزارشات
        report_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['dark'], fg='white')
        menubar.add_cascade(label="📊 گزارشات", menu=report_menu, font=self.font_normal)
        report_menu.add_command(label="📅 گزارش روزانه", command=self.daily_report, 
                               font=self.font_normal)
        report_menu.add_command(label="📆 گزارش هفتگی", command=self.weekly_report, 
                               font=self.font_normal)
        report_menu.add_command(label="📅 گزارش ماهانه", command=self.monthly_report, 
                               font=self.font_normal)
        report_menu.add_command(label="📈 گزارش سود و زیان", command=self.profit_loss_report, 
                               font=self.font_normal)
        report_menu.add_command(label="📊 نمودار فروش", command=self.show_sales_chart, 
                               font=self.font_normal)
        
        # منوی تنظیمات
        settings_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['dark'], fg='white')
        menubar.add_cascade(label="⚙️ تنظیمات", menu=settings_menu, font=self.font_normal)
        settings_menu.add_command(label="🏪 اطلاعات فروشگاه", command=self.shop_info, 
                                 font=self.font_normal)
        settings_menu.add_command(label="💾 پشتیبان گیری", command=self.backup_data, 
                                 font=self.font_normal)
        settings_menu.add_command(label="🔄 بازیابی اطلاعات", command=self.restore_data, 
                                 font=self.font_normal)
        settings_menu.add_separator()
        settings_menu.add_command(label="🎨 تغییر تم", command=self.toggle_theme, 
                                 font=self.font_normal)
        
        # منوی راهنما
        help_menu = tk.Menu(menubar, tearoff=0, bg=self.colors['dark'], fg='white')
        menubar.add_cascade(label="❓ راهنما", menu=help_menu, font=self.font_normal)
        help_menu.add_command(label="📖 راهنمای استفاده", command=self.show_help, 
                             font=self.font_normal)
        help_menu.add_command(label="ℹ️ درباره", command=self.show_about, 
                             font=self.font_normal)
        
        # اتصال کلیدهای میانبر
        self.root.bind('<Control-n>', lambda e: self.new_report())
        self.root.bind('<Control-s>', lambda e: self.save_current_data())
    
    def create_main_frames(self):
        """ایجاد فریم‌های اصلی با طراحی مدرن"""
        # فریم اصلی با حاشیه و سایه
        self.main_frame = tk.Frame(self.root, bg=self.colors['light'])
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # فریم هدر با گرادینت رنگی
        self.header_frame = tk.Frame(self.main_frame, bg=self.colors['primary'], height=80)
        self.header_frame.pack(fill=tk.X, pady=(0, 10))
        self.header_frame.pack_propagate(False)
        
        # فریم اطلاعات محصول با حاشیه زیبا
        self.input_frame = tk.Frame(self.main_frame, bg=self.colors['white'], 
                                   relief=tk.RAISED, borderwidth=2)
        self.input_frame.pack(fill=tk.X, pady=(0, 10), padx=5)
        
        # فریم لیست محصولات
        self.list_frame = tk.Frame(self.main_frame, bg=self.colors['white'],
                                  relief=tk.RAISED, borderwidth=2)
        self.list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10), padx=5)
        
        # فریم دکمه‌های عملیات
        self.button_frame = tk.Frame(self.main_frame, bg=self.colors['light'])
        self.button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # فریم خلاصه و آمار
        self.summary_frame = tk.Frame(self.main_frame, bg=self.colors['white'],
                                     relief=tk.RAISED, borderwidth=2)
        self.summary_frame.pack(fill=tk.X, pady=(0, 10), padx=5)
        
        # فریم نمودار (مخفی در ابتدا)
        self.chart_frame = tk.Frame(self.main_frame, bg=self.colors['white'],
                                   relief=tk.RAISED, borderwidth=2)
    
    def create_widgets(self):
        """ایجاد ویجت‌ها با طراحی مدرن و توضیحات"""
        
        # ========== هدر ==========
        # عنوان اصلی
        title_label = tk.Label(self.header_frame, 
                              text="🌟 فروشگاه آنلاین پیشرفته 🌟", 
                              font=("B Nazanin", 24, "bold"),
                              bg=self.colors['primary'], fg='white')
        title_label.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # تاریخ و زمان
        self.datetime_label = tk.Label(self.header_frame,
                                      text=self.get_persian_datetime(),
                                      font=self.font_normal,
                                      bg=self.colors['primary'], fg='white')
        self.datetime_label.pack(side=tk.LEFT, padx=20, pady=15)
        
        # به‌روزرسانی زمان هر ثانیه
        self.update_datetime()
        
        # ========== فریم ورودی اطلاعات ==========
        # عنوان فریم
        input_title = tk.Label(self.input_frame, text="➕ افزودن محصول جدید",
                              font=self.font_title, bg=self.colors['white'],
                              fg=self.colors['dark'])
        input_title.grid(row=0, column=0, columnspan=8, pady=10, sticky='w', padx=10)
        
        # خط جداکننده
        separator = ttk.Separator(self.input_frame, orient='horizontal')
        separator.grid(row=1, column=0, columnspan=8, sticky='ew', pady=5, padx=10)
        
        # کد محصول
        tk.Label(self.input_frame, text="🔖 کد محصول:", font=self.font_normal,
                bg=self.colors['white']).grid(row=2, column=0, padx=5, pady=8, sticky='e')
        self.code_entry = ttk.Entry(self.input_frame, font=self.font_normal, width=15)
        self.code_entry.grid(row=2, column=1, padx=5, pady=8, sticky='w')
        ToolTip(self.code_entry, "کد یکتای محصول را وارد کنید")
        
        # نام محصول
        tk.Label(self.input_frame, text="📦 نام محصول:", font=self.font_normal,
                bg=self.colors['white']).grid(row=2, column=2, padx=20, pady=8, sticky='e')
        self.name_entry = ttk.Entry(self.input_frame, font=self.font_normal, width=25)
        self.name_entry.grid(row=2, column=3, padx=5, pady=8, sticky='w')
        ToolTip(self.name_entry, "نام کامل محصول را وارد کنید")
        
        # دسته‌بندی
        tk.Label(self.input_frame, text="📂 دسته‌بندی:", font=self.font_normal,
                bg=self.colors['white']).grid(row=2, column=4, padx=20, pady=8, sticky='e')
        self.category_combo = ttk.Combobox(self.input_frame, font=self.font_normal,
                                          values=['الکترونیک', 'پوشاک', 'خوراکی', 'آرایشی', 'کتاب', 'سایر'],
                                          width=15)
        self.category_combo.grid(row=2, column=5, padx=5, pady=8, sticky='w')
        self.category_combo.set('سایر')
        ToolTip(self.category_combo, "دسته‌بندی محصول را انتخاب کنید")
        
        # قیمت خرید
        tk.Label(self.input_frame, text="💰 قیمت خرید (ریال):", font=self.font_normal,
                bg=self.colors['white'], fg=self.colors['danger']).grid(row=3, column=0, padx=5, pady=8, sticky='e')
        self.buy_price_entry = ttk.Entry(self.input_frame, font=self.font_normal, width=15)
        self.buy_price_entry.grid(row=3, column=1, padx=5, pady=8, sticky='w')
        ToolTip(self.buy_price_entry, "قیمت خرید محصول را به ریال وارد کنید")
        
        # قیمت فروش
        tk.Label(self.input_frame, text="💵 قیمت فروش (ریال):", font=self.font_normal,
                bg=self.colors['white'], fg=self.colors['success']).grid(row=3, column=2, padx=20, pady=8, sticky='e')
        self.sell_price_entry = ttk.Entry(self.input_frame, font=self.font_normal, width=15)
        self.sell_price_entry.grid(row=3, column=3, padx=5, pady=8, sticky='w')
        ToolTip(self.sell_price_entry, "قیمت فروش محصول را به ریال وارد کنید")
        
        # تعداد
        tk.Label(self.input_frame, text="🔢 تعداد:", font=self.font_normal,
                bg=self.colors['white']).grid(row=3, column=4, padx=20, pady=8, sticky='e')
        self.quantity_entry = ttk.Entry(self.input_frame, font=self.font_normal, width=10)
        self.quantity_entry.grid(row=3, column=5, padx=5, pady=8, sticky='w')
        ToolTip(self.quantity_entry, "تعداد محصول را وارد کنید (عدد صحیح)")
        
        # واحد
        tk.Label(self.input_frame, text="⚖️ واحد:", font=self.font_normal,
                bg=self.colors['white']).grid(row=3, column=6, padx=20, pady=8, sticky='e')
        self.unit_combo = ttk.Combobox(self.input_frame, font=self.font_normal,
                                      values=['عدد', 'کیلوگرم', 'گرم', 'متر', 'لیتر', 'بسته'],
                                      width=10)
        self.unit_combo.grid(row=3, column=7, padx=5, pady=8, sticky='w')
        self.unit_combo.set('عدد')
        ToolTip(self.unit_combo, "واحد اندازه‌گیری محصول را انتخاب کنید")
        
        # تاریخ
        tk.Label(self.input_frame, text="📅 تاریخ:", font=self.font_normal,
                bg=self.colors['white']).grid(row=4, column=0, padx=5, pady=8, sticky='e')
        self.date_label = tk.Label(self.input_frame, text=self.get_persian_date(),
                                  font=self.font_normal, bg=self.colors['white'],
                                  fg=self.colors['info'])
        self.date_label.grid(row=4, column=1, padx=5, pady=8, sticky='w')
        
        # توضیحات
        tk.Label(self.input_frame, text="📝 توضیحات:", font=self.font_normal,
                bg=self.colors['white']).grid(row=4, column=2, padx=20, pady=8, sticky='e')
        self.description_entry = ttk.Entry(self.input_frame, font=self.font_normal, width=30)
        self.description_entry.grid(row=4, column=3, columnspan=2, padx=5, pady=8, sticky='w')
        ToolTip(self.description_entry, "توضیحات اضافی درباره محصول (اختیاری)")
        
        # دکمه‌های اصلی با آیکون
        button_style = {'font': self.font_normal, 'borderwidth': 0, 'cursor': 'hand2'}
        
        # دکمه افزودن
        self.add_button = tk.Button(self.input_frame, text="✅ افزودن به لیست",
                                   bg=self.colors['success'], fg='white',
                                   command=self.add_item,
                                   **button_style)
        self.add_button.grid(row=5, column=0, columnspan=2, padx=5, pady=15, sticky='ew')
        ToolTip(self.add_button, "افزودن محصول به لیست فعلی")
        
        # دکمه ویرایش
        self.update_button = tk.Button(self.input_frame, text="✏️ ویرایش محصول",
                                      bg=self.colors['warning'], fg='black',
                                      command=self.update_item, state='disabled',
                                      **button_style)
        self.update_button.grid(row=5, column=2, columnspan=2, padx=5, pady=15, sticky='ew')
        ToolTip(self.update_button, "ویرایش اطلاعات محصول انتخاب شده")
        
        # دکمه پاک کردن
        self.clear_button = tk.Button(self.input_frame, text="🔄 پاک کردن فرم",
                                     bg=self.colors['info'], fg='white',
                                     command=self.clear_entries,
                                     **button_style)
        self.clear_button.grid(row=5, column=4, columnspan=2, padx=5, pady=15, sticky='ew')
        ToolTip(self.clear_button, "پاک کردن تمام فیلدهای ورودی")
        
        # ========== لیست محصولات ==========
        # عنوان لیست
        list_title = tk.Label(self.list_frame, text="📋 لیست محصولات",
                             font=self.font_title, bg=self.colors['white'],
                             fg=self.colors['dark'])
        list_title.pack(anchor='w', padx=10, pady=5)
        
        # ایجاد Treeview با رنگ‌بندی
        self.create_colored_treeview()
        
        # ========== دکمه‌های عملیات ==========
        # ایجاد دکمه‌ها در دو ردیف
        buttons_row1 = [
            ("❌ حذف از لیست", self.colors['danger'], self.remove_item, "حذف محصول انتخاب شده از لیست"),
            ("📊 گزارش فعالیت", self.colors['purple'], self.show_activity_report, "نمایش گزارش کامل فعالیت"),
            ("💾 ذخیره داده‌ها", self.colors['primary'], self.save_current_data, "ذخیره اطلاعات در حافظه"),
            ("🖨️ چاپ رسید", self.colors['orange'], self.print_receipt, "چاپ رسید فروش"),
            ("📂 داده‌های ذخیره شده", self.colors['teal'], self.view_saved_data, "مشاهده اطلاعات روزهای قبل"),
        ]
        
        buttons_row2 = [
            ("📈 نمودار فروش", self.colors['info'], self.show_sales_chart, "نمایش نمودار آماری فروش"),
            ("📊 گزارش سود و زیان", self.colors['gold'], self.profit_loss_report, "مشاهده گزارش سود و زیان"),
            ("📤 خروجی Excel", self.colors['success'], self.export_to_excel, "خروجی گرفتن از داده‌ها"),
            ("⚙️ تنظیمات", self.colors['dark'], self.show_settings, "تنظیمات برنامه"),
        ]
        
        # ردیف اول دکمه‌ها
        row1_frame = tk.Frame(self.button_frame, bg=self.colors['light'])
        row1_frame.pack(fill=tk.X, pady=2)
        
        for text, color, command, tooltip in buttons_row1:
            btn = tk.Button(row1_frame, text=text, bg=color, fg='white',
                          font=self.font_normal, command=command,
                          borderwidth=0, cursor='hand2', padx=10, pady=5)
            btn.pack(side=tk.RIGHT, padx=3)
            ToolTip(btn, tooltip)
        
        # ردیف دوم دکمه‌ها
        row2_frame = tk.Frame(self.button_frame, bg=self.colors['light'])
        row2_frame.pack(fill=tk.X, pady=2)
        
        for text, color, command, tooltip in buttons_row2:
            btn = tk.Button(row2_frame, text=text, bg=color, fg='white',
                          font=self.font_normal, command=command,
                          borderwidth=0, cursor='hand2', padx=10, pady=5)
            btn.pack(side=tk.RIGHT, padx=3)
            ToolTip(btn, tooltip)
        
        # ========== فریم خلاصه ==========
        self.create_summary_widgets()
    
    def create_colored_treeview(self):
        """ایجاد Treeview با رنگ‌بندی حرفه‌ای"""
        # فریم برای Treeview و اسکرول بار
        tree_frame = tk.Frame(self.list_frame, bg=self.colors['white'])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # اسکرول بار عمودی
        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.pack(side=tk.LEFT, fill=tk.Y)
        
        # اسکرول بار افقی
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal")
        hsb.pack(side=tk.BOTTOM, fill=tk.X)
        
        # ستون‌ها
        columns = ('کد', 'نام محصول', 'دسته‌بندی', 'قیمت خرید', 'قیمت فروش',
                  'تعداد', 'واحد', 'جمع خرید', 'جمع فروش', 'سود', 'تاریخ')
        
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                                 yscrollcommand=vsb.set, xscrollcommand=hsb.set,
                                 height=15)
        
        vsb.config(command=self.tree.yview)
        hsb.config(command=self.tree.xview)
        
        # تنظیم عرض و عنوان ستون‌ها
        column_widths = [80, 150, 100, 100, 100, 70, 70, 120, 120, 100, 100]
        for col, width in zip(columns, column_widths):
            self.tree.heading(col, text=col)
            self.tree.column(col, width=width, anchor='center')
        
        self.tree.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # رنگ‌بندی ردیف‌ها
        self.tree.tag_configure('evenrow', background='#E8F5E9')  # سبز خیلی روشن
        self.tree.tag_configure('oddrow', background='#FFF3E0')   # نارنجی خیلی روشن
        self.tree.tag_configure('profithigh', background='#C8E6C9')  # سبز برای سود بالا
        self.tree.tag_configure('profitlow', background='#FFCDD2')   # قرمز برای سود کم
        
        # اتصال رویداد کلیک
        self.tree.bind('<ButtonRelease-1>', self.select_item)
    
    def create_summary_widgets(self):
        """ایجاد ویجت‌های خلاصه با طراحی زیبا"""
        # عنوان خلاصه
        summary_title = tk.Label(self.summary_frame, text="📊 خلاصه و آمار",
                                font=self.font_title, bg=self.colors['white'],
                                fg=self.colors['dark'])
        summary_title.pack(anchor='w', padx=10, pady=5)
        
        # فریم آمار
        stats_frame = tk.Frame(self.summary_frame, bg=self.colors['white'])
        stats_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # سطر اول آمار
        row1_frame = tk.Frame(stats_frame, bg=self.colors['white'])
        row1_frame.pack(fill=tk.X, pady=3)
        
        # جمع کل خرید
        tk.Label(row1_frame, text="💰 جمع کل خرید:", font=self.font_normal,
                bg=self.colors['white'], fg=self.colors['danger']).pack(side=tk.RIGHT, padx=5)
        self.total_buy_label = tk.Label(row1_frame, text="0 ریال",
                                       font=self.font_normal, bg=self.colors['white'],
                                       fg=self.colors['danger'])
        self.total_buy_label.pack(side=tk.RIGHT, padx=10)
        
        # جمع کل فروش
        tk.Label(row1_frame, text="💵 جمع کل فروش:", font=self.font_normal,
                bg=self.colors['white'], fg=self.colors['success']).pack(side=tk.RIGHT, padx=20)
        self.total_sell_label = tk.Label(row1_frame, text="0 ریال",
                                        font=self.font_normal, bg=self.colors['white'],
                                        fg=self.colors['success'])
        self.total_sell_label.pack(side=tk.RIGHT, padx=10)
        
        # سود کل
        tk.Label(row1_frame, text="📈 سود کل:", font=self.font_normal,
                bg=self.colors['white'], fg=self.colors['info']).pack(side=tk.RIGHT, padx=20)
        self.total_profit_label = tk.Label(row1_frame, text="0 ریال",
                                          font=self.font_normal, bg=self.colors['white'],
                                          fg=self.colors['info'])
        self.total_profit_label.pack(side=tk.RIGHT, padx=10)
        
        # سطر دوم آمار
        row2_frame = tk.Frame(stats_frame, bg=self.colors['white'])
        row2_frame.pack(fill=tk.X, pady=3)
        
        # تعداد اقلام
        tk.Label(row2_frame, text="📦 تعداد اقلام:", font=self.font_normal,
                bg=self.colors['white']).pack(side=tk.RIGHT, padx=5)
        self.item_count_label = tk.Label(row2_frame, text="0",
                                        font=self.font_normal, bg=self.colors['white'])
        self.item_count_label.pack(side=tk.RIGHT, padx=10)
        
        # میانگین قیمت
        tk.Label(row2_frame, text="📊 میانگین قیمت:", font=self.font_normal,
                bg=self.colors['white']).pack(side=tk.RIGHT, padx=20)
        self.avg_price_label = tk.Label(row2_frame, text="0 ریال",
                                       font=self.font_normal, bg=self.colors['white'])
        self.avg_price_label.pack(side=tk.RIGHT, padx=10)
        
        # بیشترین فروش
        tk.Label(row2_frame, text="🏆 بیشترین فروش:", font=self.font_normal,
                bg=self.colors['white'], fg=self.colors['gold']).pack(side=tk.RIGHT, padx=20)
        self.max_sell_label = tk.Label(row2_frame, text="-",
                                      font=self.font_normal, bg=self.colors['white'])
        self.max_sell_label.pack(side=tk.RIGHT, padx=10)
    
    def create_status_bar(self):
        """ایجاد نوار وضعیت در پایین صفحه"""
        self.status_bar = tk.Frame(self.root, bg=self.colors['dark'], height=25)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # وضعیت
        self.status_label = tk.Label(self.status_bar, text="✅ آماده به کار",
                                     bg=self.colors['dark'], fg='white',
                                     font=self.font_small)
        self.status_label.pack(side=tk.RIGHT, padx=10)
        
        # زمان سپری شده
        self.report_label = tk.Label(self.status_bar, text="",
                                     bg=self.colors['dark'], fg=self.colors['gold'],
                                     font=self.font_small)
        self.report_label.pack(side=tk.LEFT, padx=10)
    
    def update_datetime(self):
        """به‌روزرسانی تاریخ و زمان"""
        self.datetime_label.config(text=self.get_persian_datetime())
        self.root.after(1000, self.update_datetime)
    
    def get_persian_datetime(self):
        """دریافت تاریخ و زمان شمسی"""
        now = jdatetime.datetime.now()
        persian_months = [
            'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
            'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
        ]
        time_str = now.strftime("%H:%M:%S")
        return f"{now.day} {persian_months[now.month-1]} {now.year} - {time_str}"
    
    def get_persian_date(self):
        """دریافت تاریخ شمسی"""
        now = jdatetime.datetime.now()
        persian_months = [
            'فروردین', 'اردیبهشت', 'خرداد', 'تیر', 'مرداد', 'شهریور',
            'مهر', 'آبان', 'آذر', 'دی', 'بهمن', 'اسفند'
        ]
        return f"{now.day} {persian_months[now.month-1]} {now.year}"
    
    def add_item(self):
        """افزودن محصول به لیست"""
        try:
            code = self.code_entry.get()
            name = self.name_entry.get()
            category = self.category_combo.get()
            buy_price = float(self.buy_price_entry.get() or 0)
            sell_price = float(self.sell_price_entry.get() or 0)
            quantity = int(self.quantity_entry.get() or 1)
            unit = self.unit_combo.get()
            description = self.description_entry.get()
            
            if not code or not name:
                messagebox.showwarning("⚠️ خطا", "لطفا کد و نام محصول را وارد کنید")
                return
            
            if buy_price <= 0 or sell_price <= 0:
                messagebox.showwarning("⚠️ خطا", "قیمت باید بزرگتر از صفر باشد")
                return
            
            total_buy = buy_price * quantity
            total_sell = sell_price * quantity
            profit = total_sell - total_buy
            
            item = {
                'code': code,
                'name': name,
                'category': category,
                'buy_price': buy_price,
                'sell_price': sell_price,
                'quantity': quantity,
                'unit': unit,
                'description': description,
                'total_buy': total_buy,
                'total_sell': total_sell,
                'profit': profit,
                'date': self.get_persian_date(),
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.items.append(item)
            self.update_treeview()
            self.clear_entries()
            self.calculate_totals()
            
            # به‌روزرسانی وضعیت
            self.status_label.config(text=f"✅ محصول '{name}' با موفقیت اضافه شد")
            
        except ValueError:
            messagebox.showerror("❌ خطا", "لطفا مقادیر عددی را به درستی وارد کنید")
    
    def update_treeview(self):
        """به‌روزرسانی نمایش لیست با رنگ‌بندی"""
        for row in self.tree.get_children():
            self.tree.delete(row)
        
        for i, item in enumerate(self.items):
            # انتخاب رنگ بر اساس سود
            if item['profit'] > 1000000:
                tag = 'profithigh'
            elif item['profit'] < 0:
                tag = 'profitlow'
            else:
                tag = 'evenrow' if i % 2 == 0 else 'oddrow'
            
            self.tree.insert('', 'end', values=(
                item['code'],
                item['name'],
                item['category'],
                f"{item['buy_price']:,.0f}",
                f"{item['sell_price']:,.0f}",
                item['quantity'],
                item['unit'],
                f"{item['total_buy']:,.0f}",
                f"{item['total_sell']:,.0f}",
                f"{item['profit']:,.0f}",
                item['date']
            ), tags=(tag,))
    
    def select_item(self, event):
        """انتخاب آیتم از لیست"""
        selected = self.tree.selection()
        if selected:
            item = self.tree.item(selected[0])['values']
            
            # پر کردن فیلدها
            self.code_entry.delete(0, tk.END)
            self.code_entry.insert(0, item[0])
            
            self.name_entry.delete(0, tk.END)
            self.name_entry.insert(0, item[1])
            
            self.category_combo.set(item[2])
            
            self.buy_price_entry.delete(0, tk.END)
            self.buy_price_entry.insert(0, item[3].replace(',', ''))
            
            self.sell_price_entry.delete(0, tk.END)
            self.sell_price_entry.insert(0, item[4].replace(',', ''))
            
            self.quantity_entry.delete(0, tk.END)
            self.quantity_entry.insert(0, item[5])
            
            self.unit_combo.set(item[6])
            
            # فعال کردن دکمه ویرایش
            self.update_button.config(state='normal', bg=self.colors['warning'])
            
            # به‌روزرسانی وضعیت
            self.status_label.config(text=f"✏️ محصول '{item[1]}' انتخاب شد")
    
    def update_item(self):
        """ویرایش محصول"""
        selected = self.tree.selection()
        if selected:
            index = self.tree.index(selected[0])
            
            try:
                code = self.code_entry.get()
                name = self.name_entry.get()
                category = self.category_combo.get()
                buy_price = float(self.buy_price_entry.get() or 0)
                sell_price = float(self.sell_price_entry.get() or 0)
                quantity = int(self.quantity_entry.get() or 1)
                unit = self.unit_combo.get()
                description = self.description_entry.get()
                
                total_buy = buy_price * quantity
                total_sell = sell_price * quantity
                profit = total_sell - total_buy
                
                self.items[index] = {
                    'code': code,
                    'name': name,
                    'category': category,
                    'buy_price': buy_price,
                    'sell_price': sell_price,
                    'quantity': quantity,
                    'unit': unit,
                    'description': description,
                    'total_buy': total_buy,
                    'total_sell': total_sell,
                    'profit': profit,
                    'date': self.get_persian_date(),
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                self.update_treeview()
                self.clear_entries()
                self.calculate_totals()
                self.update_button.config(state='disabled', bg=self.colors['warning'])
                
                self.status_label.config(text=f"✅ محصول '{name}' با موفقیت ویرایش شد")
                
            except ValueError:
                messagebox.showerror("❌ خطا", "لطفا مقادیر عددی را به درستی وارد کنید")
    
    def remove_item(self):
        """حذف محصول از لیست"""
        selected = self.tree.selection()
        if selected:
            item_name = self.tree.item(selected[0])['values'][1]
            if messagebox.askyesno("⚠️ تایید حذف", f"آیا از حذف محصول '{item_name}' اطمینان دارید؟"):
                for item in selected:
                    self.tree.delete(item)
                    index = self.tree.index(item)
                    self.items.pop(index)
                
                self.calculate_totals()
                self.clear_entries()
                self.update_button.config(state='disabled')
                
                self.status_label.config(text=f"✅ محصول '{item_name}' حذف شد")
    
    def clear_entries(self):
        """پاک کردن فیلدهای ورودی"""
        self.code_entry.delete(0, tk.END)
        self.name_entry.delete(0, tk.END)
        self.category_combo.set('سایر')
        self.buy_price_entry.delete(0, tk.END)
        self.sell_price_entry.delete(0, tk.END)
        self.quantity_entry.delete(0, tk.END)
        self.unit_combo.set('عدد')
        self.description_entry.delete(0, tk.END)
        self.code_entry.focus()
        
        self.status_label.config(text="✅ فرم پاک شد")
    
    def calculate_totals(self):
        """محاسبه مجموع‌ها"""
        if not self.items:
            self.total_buy_label.config(text="0 ریال")
            self.total_sell_label.config(text="0 ریال")
            self.total_profit_label.config(text="0 ریال")
            self.item_count_label.config(text="0")
            self.avg_price_label.config(text="0 ریال")
            self.max_sell_label.config(text="-")
            return
        
        total_buy = sum(item['total_buy'] for item in self.items)
        total_sell = sum(item['total_sell'] for item in self.items)
        total_profit = sum(item['profit'] for item in self.items)
        avg_price = total_sell / len(self.items) if self.items else 0
        
        # بیشترین فروش
        max_item = max(self.items, key=lambda x: x['total_sell'])
        max_sell_text = f"{max_item['name']} ({max_item['total_sell']:,.0f} ریال)"
        
        self.total_buy_label.config(text=f"{total_buy:,.0f} ریال")
        self.total_sell_label.config(text=f"{total_sell:,.0f} ریال")
        self.total_profit_label.config(text=f"{total_profit:,.0f} ریال")
        self.item_count_label.config(text=str(len(self.items)))
        self.avg_price_label.config(text=f"{avg_price:,.0f} ریال")
        self.max_sell_label.config(text=max_sell_text)
        
        # تغییر رنگ سود بر اساس مثبت یا منفی بودن
        if total_profit > 0:
            self.total_profit_label.config(fg=self.colors['success'])
        elif total_profit < 0:
            self.total_profit_label.config(fg=self.colors['danger'])
    
    def update_report_time(self):
        """به‌روزرسانی زمان گزارش"""
        elapsed = datetime.now() - self.report_start_time
        hours = elapsed.seconds // 3600
        minutes = (elapsed.seconds % 3600) // 60
        seconds = elapsed.seconds % 60
        
        time_text = f"⏱️ زمان فعالیت: {hours:02d}:{minutes:02d}:{seconds:02d}"
        self.report_label.config(text=time_text)
        
        self.root.after(1000, self.update_report_time)
    
    def show_activity_report(self):
        """نمایش گزارش فعالیت"""
        report_window = tk.Toplevel(self.root)
        report_window.title("📊 گزارش فعالیت")
        report_window.geometry("700x500")
        report_window.configure(bg=self.colors['white'])
        
        # عنوان
        title = tk.Label(report_window, text="📊 گزارش کامل فعالیت",
                        font=self.font_title, bg=self.colors['white'],
                        fg=self.colors['primary'])
        title.pack(pady=10)
        
        # متن گزارش
        report_frame = tk.Frame(report_window, bg=self.colors['white'])
        report_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        report_text = tk.Text(report_frame, font=("B Nazanin", 11), wrap=tk.WORD,
                             bg=self.colors['light'], relief=tk.FLAT)
        scrollbar = ttk.Scrollbar(report_frame, orient=tk.VERTICAL, command=report_text.yview)
        report_text.configure(yscrollcommand=scrollbar.set)
        
        report_text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        
        # محاسبه زمان
        elapsed = datetime.now() - self.report_start_time
        hours = elapsed.seconds // 3600
        minutes = (elapsed.seconds % 3600) // 60
        seconds = elapsed.seconds % 60
        
        # آمار
        total_buy = sum(item['total_buy'] for item in self.items)
        total_sell = sum(item['total_sell'] for item in self.items)
        total_profit = sum(item['profit'] for item in self.items)
        
        report = f"""
        ╔══════════════════════════════════════════════════════════╗
        ║                    📊 گزارش فعالیت برنامه                 ║
        ╠══════════════════════════════════════════════════════════╣
        ║                                                          ║
        ║   📅 تاریخ شروع: {self.report_start_time.strftime('%Y/%m/%d %H:%M:%S')}              ║
        ║   📅 تاریخ پایان: {datetime.now().strftime('%Y/%m/%d %H:%M:%S')}               ║
        ║   ⏱️ مدت زمان: {hours} ساعت و {minutes} دقیقه و {seconds} ثانیه                    ║
        ║                                                          ║
        ╠══════════════════════════════════════════════════════════╣
        ║                    📈 آمار کلی فروش                       ║
        ╠══════════════════════════════════════════════════════════╣
        ║                                                          ║
        ║   📦 تعداد تراکنش‌ها: {len(self.items)}                                     ║
        ║   💰 جمع کل خرید: {total_buy:,.0f} ریال                         ║
        ║   💵 جمع کل فروش: {total_sell:,.0f} ریال                         ║
        ║   📈 سود خالص: {total_profit:,.0f} ریال                           ║
        ║                                                          ║
        ╚══════════════════════════════════════════════════════════╝
        """
        
        report_text.insert('1.0', report)
        report_text.config(state='disabled')
        
        # دکمه بستن
        close_btn = tk.Button(report_window, text="❌ بستن",
                             bg=self.colors['danger'], fg='white',
                             font=self.font_normal, command=report_window.destroy,
                             borderwidth=0, cursor='hand2', padx=20, pady=5)
        close_btn.pack(pady=10)
    
    def save_current_data(self):
        """ذخیره داده‌های فعلی"""
        if not self.items:
            messagebox.showwarning("⚠️ خطا", "هیچ داده‌ای برای ذخیره وجود ندارد")
            return
        
        date_key = datetime.now().strftime("%Y-%m-%d")
        
        if date_key not in self.saved_data:
            self.saved_data[date_key] = []
        
        data_entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'items': self.items.copy(),
            'total_buy': sum(item['total_buy'] for item in self.items),
            'total_sell': sum(item['total_sell'] for item in self.items),
            'total_profit': sum(item['profit'] for item in self.items),
            'item_count': len(self.items)
        }
        
        self.saved_data[date_key].append(data_entry)
        
        # ذخیره در فایل
        try:
            with open('sales_data.json', 'w', encoding='utf-8') as f:
                json.dump(self.saved_data, f, ensure_ascii=False, indent=2)
            
            messagebox.showinfo("✅ موفق", "داده‌ها با موفقیت ذخیره شدند")
            self.status_label.config(text="💾 داده‌ها ذخیره شدند")
            
        except Exception as e:
            messagebox.showerror("❌ خطا", f"خطا در ذخیره سازی: {str(e)}")
    
    def load_saved_data(self):
        """بارگذاری داده‌های ذخیره شده"""
        try:
            if os.path.exists('sales_data.json'):
                with open('sales_data.json', 'r', encoding='utf-8') as f:
                    self.saved_data = json.load(f)
        except:
            self.saved_data = {}
    
    def view_saved_data(self):
        """مشاهده داده‌های ذخیره شده"""
        if not self.saved_data:
            messagebox.showinfo("📂 اطلاعات", "هیچ داده‌ای ذخیره نشده است")
            return
        
        view_window = tk.Toplevel(self.root)
        view_window.title("📂 داده‌های ذخیره شده")
        view_window.geometry("900x600")
        view_window.configure(bg=self.colors['white'])
        
        # عنوان
        title = tk.Label(view_window, text="📂 داده‌های ذخیره شده",
                        font=self.font_title, bg=self.colors['white'],
                        fg=self.colors['primary'])
        title.pack(pady=10)
        
        # فریم انتخاب تاریخ
        date_frame = tk.Frame(view_window, bg=self.colors['white'])
        date_frame.pack(fill=tk.X, padx=20, pady=5)
        
        tk.Label(date_frame, text="📅 انتخاب تاریخ:", font=self.font_normal,
                bg=self.colors['white']).pack(side=tk.RIGHT, padx=5)
        
        dates = list(self.saved_data.keys())
        date_var = tk.StringVar()
        date_combo = ttk.Combobox(date_frame, textvariable=date_var, values=dates,
                                  font=self.font_normal, width=20)
        date_combo.pack(side=tk.RIGHT, padx=5)
        ToolTip(date_combo, "تاریخ مورد نظر را انتخاب کنید")
        
        # فریم نمایش
        display_frame = tk.Frame(view_window, bg=self.colors['white'])
        display_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # ایجاد Treeview برای نمایش
        columns = ('زمان', 'تعداد اقلام', 'جمع خرید', 'جمع فروش', 'سود')
        tree = ttk.Treeview(display_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150, anchor='center')
        
        scrollbar = ttk.Scrollbar(display_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        
        def show_selected():
            tree.delete(*tree.get_children())
            selected_date = date_var.get()
            if selected_date and selected_date in self.saved_data:
                for entry in self.saved_data[selected_date]:
                    tree.insert('', 'end', values=(
                        entry['timestamp'][11:],  # فقط ساعت
                        entry['item_count'],
                        f"{entry['total_buy']:,.0f}",
                        f"{entry['total_sell']:,.0f}",
                        f"{entry['total_profit']:,.0f}"
                    ))
        
        # دکمه نمایش
        show_btn = tk.Button(view_window, text="🔍 نمایش",
                            bg=self.colors['primary'], fg='white',
                            font=self.font_normal, command=show_selected,
                            borderwidth=0, cursor='hand2', padx=20, pady=5)
        show_btn.pack(pady=5)
        ToolTip(show_btn, "نمایش داده‌های تاریخ انتخاب شده")
        
        # دکمه بستن
        close_btn = tk.Button(view_window, text="❌ بستن",
                             bg=self.colors['danger'], fg='white',
                             font=self.font_normal, command=view_window.destroy,
                             borderwidth=0, cursor='hand2', padx=20, pady=5)
        close_btn.pack(pady=10)
    
    def print_receipt(self):
        """چاپ رسید فروش"""
        if not self.items:
            messagebox.showwarning("⚠️ خطا", "هیچ آیتمی برای چاپ وجود ندارد")
            return
        
        receipt_window = tk.Toplevel(self.root)
        receipt_window.title("🖨️ رسید فروش")
        receipt_window.geometry("450x700")
        receipt_window.configure(bg=self.colors['white'])
        
        # عنوان
        title = tk.Label(receipt_window, text="🖨️ رسید فروش",
                        font=self.font_title, bg=self.colors['white'],
                        fg=self.colors['primary'])
        title.pack(pady=10)
        
        # متن رسید
        receipt_frame = tk.Frame(receipt_window, bg=self.colors['white'])
        receipt_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        receipt_text = tk.Text(receipt_frame, font=("B Nazanin", 10), wrap=tk.WORD,
                              bg=self.colors['light'], relief=tk.FLAT)
        scrollbar = ttk.Scrollbar(receipt_frame, orient=tk.VERTICAL, command=receipt_text.yview)
        receipt_text.configure(yscrollcommand=scrollbar.set)
        
        receipt_text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        
        # ایجاد رسید زیبا
        receipt = f"""
        ╔════════════════════════════════════════╗
        ║            🏪 فروشگاه آنلاین             ║
        ╠════════════════════════════════════════╣
        ║  تاریخ: {self.get_persian_date():<25} ║
        ║  ساعت: {datetime.now().strftime('%H:%M:%S'):<25} ║
        ╠════════════════════════════════════════╣
        ║           📋 لیست خرید شما              ║
        ╠════════════════════════════════════════╣
        """
        
        for i, item in enumerate(self.items, 1):
            receipt += f"""
        ║ {i}. {item['name']:<30} ║
        ║    📦 تعداد: {item['quantity']} {item['unit']:<15} ║
        ║    💵 قیمت واحد: {item['sell_price']:,.0f} ریال     ║
        ║    💰 جمع: {item['total_sell']:,.0f} ریال          ║
        ╟────────────────────────────────────────╢
        """
        
        total = sum(item['total_sell'] for item in self.items)
        receipt += f"""
        ╠════════════════════════════════════════╣
        ║  💰 جمع کل: {total:,.0f} ریال              ║
        ╠════════════════════════════════════════╣
        ║  🤝 با تشکر از خرید شما                 ║
        ║  🌟 منتظر حضور مجدد شما هستیم           ║
        ╚════════════════════════════════════════╝
        """
        
        receipt_text.insert('1.0', receipt)
        receipt_text.config(state='disabled')
        
        # دکمه‌ها
        button_frame = tk.Frame(receipt_window, bg=self.colors['white'])
        button_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # دکمه چاپ
        print_btn = tk.Button(button_frame, text="🖨️ چاپ",
                             bg=self.colors['success'], fg='white',
                             font=self.font_normal,
                             command=lambda: self.print_text(receipt),
                             borderwidth=0, cursor='hand2', padx=20, pady=5)
        print_btn.pack(side=tk.RIGHT, padx=5)
        ToolTip(print_btn, "چاپ رسید")
        
        # دکمه بستن
        close_btn = tk.Button(button_frame, text="❌ بستن",
                             bg=self.colors['danger'], fg='white',
                             font=self.font_normal, command=receipt_window.destroy,
                             borderwidth=0, cursor='hand2', padx=20, pady=5)
        close_btn.pack(side=tk.RIGHT, padx=5)
    
    def print_text(self, text):
        """چاپ متن"""
        # اینجا می‌توانید کد چاپ واقعی را اضافه کنید
        messagebox.showinfo("🖨️ چاپ", "رسید برای چاپ آماده شد")
        self.status_label.config(text="🖨️ رسید چاپ شد")
    
    def show_sales_chart(self):
        """نمایش نمودار فروش"""
        if not self.items:
            messagebox.showwarning("⚠️ خطا", "داده‌ای برای نمایش نمودار وجود ندارد")
            return
        
        chart_window = tk.Toplevel(self.root)
        chart_window.title("📈 نمودار فروش")
        chart_window.geometry("800x600")
        
        # ایجاد شکل
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8))
        fig.patch.set_facecolor('#f0f0f0')
        
        # داده‌ها
        names = [item['name'][:10] for item in self.items]  # کوتاه کردن نام
        sells = [item['total_sell'] for item in self.items]
        profits = [item['profit'] for item in self.items]
        
        # نمودار فروش
        colors1 = plt.cm.Greens(np.linspace(0.3, 0.9, len(names)))
        bars1 = ax1.bar(names, sells, color=colors1)
        ax1.set_title('💰 نمودار فروش محصولات', fontsize=14, fontfamily='B Nazanin')
        ax1.set_ylabel('ریال', fontsize=12, fontfamily='B Nazanin')
        ax1.tick_params(axis='x', rotation=45)
        
        # اضافه کردن مقادیر روی نمودار
        for bar, val in zip(bars1, sells):
            height = bar.get_height()
            ax1.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:,.0f}', ha='center', va='bottom', fontsize=8)
        
        # نمودار سود
        colors2 = ['green' if p > 0 else 'red' for p in profits]
        bars2 = ax2.bar(names, profits, color=colors2)
        ax2.set_title('📊 نمودار سود محصولات', fontsize=14, fontfamily='B Nazanin')
        ax2.set_ylabel('ریال', fontsize=12, fontfamily='B Nazanin')
        ax2.tick_params(axis='x', rotation=45)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        # اضافه کردن مقادیر روی نمودار
        for bar, val in zip(bars2, profits):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{val:,.0f}', ha='center', va='bottom' if height > 0 else 'top',
                    fontsize=8)
        
        plt.tight_layout()
        
        # نمایش در tkinter
        canvas = FigureCanvasTkAgg(fig, master=chart_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # دکمه بستن
        close_btn = tk.Button(chart_window, text="❌ بستن",
                             bg=self.colors['danger'], fg='white',
                             font=self.font_normal,
                             command=chart_window.destroy,
                             borderwidth=0, cursor='hand2', padx=20, pady=5)
        close_btn.pack(pady=10)
    
    def profit_loss_report(self):
        """گزارش سود و زیان"""
        if not self.items:
            messagebox.showwarning("⚠️ خطا", "داده‌ای برای نمایش گزارش وجود ندارد")
            return
        
        report_window = tk.Toplevel(self.root)
        report_window.title("📊 گزارش سود و زیان")
        report_window.geometry("800x600")
        report_window.configure(bg=self.colors['white'])
        
        # عنوان
        title = tk.Label(report_window, text="📊 گزارش سود و زیان",
                        font=self.font_title, bg=self.colors['white'],
                        fg=self.colors['primary'])
        title.pack(pady=10)
        
        # ایجاد تب‌ها
        notebook = ttk.Notebook(report_window)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # تب خلاصه
        summary_frame = tk.Frame(notebook, bg=self.colors['white'])
        notebook.add(summary_frame, text="📋 خلاصه")
        
        # تب جزئیات
        details_frame = tk.Frame(notebook, bg=self.colors['white'])
        notebook.add(details_frame, text="📝 جزئیات")
        
        # تب نمودار
        chart_frame = tk.Frame(notebook, bg=self.colors['white'])
        notebook.add(chart_frame, text="📊 نمودار")
        
        # ========== خلاصه ==========
        total_buy = sum(item['total_buy'] for item in self.items)
        total_sell = sum(item['total_sell'] for item in self.items)
        total_profit = sum(item['profit'] for item in self.items)
        profit_margin = (total_profit / total_sell * 100) if total_sell > 0 else 0
        
        # کارت‌های آماری
        stats = [
            ("💰 جمع خرید", f"{total_buy:,.0f} ریال", self.colors['danger']),
            ("💵 جمع فروش", f"{total_sell:,.0f} ریال", self.colors['success']),
            ("📈 سود خالص", f"{total_profit:,.0f} ریال", 
             self.colors['success'] if total_profit > 0 else self.colors['danger']),
            ("📊 حاشیه سود", f"{profit_margin:.1f}%", self.colors['info']),
        ]
        
        row, col = 0, 0
        for label, value, color in stats:
            card = tk.Frame(summary_frame, bg=color, width=200, height=150)
            card.grid(row=row, column=col, padx=10, pady=10)
            card.grid_propagate(False)
            
            tk.Label(card, text=label, font=self.font_normal,
                    bg=color, fg='white').pack(pady=10)
            tk.Label(card, text=value, font=("B Nazanin", 16, "bold"),
                    bg=color, fg='white').pack()
            
            col += 1
            if col > 1:
                col = 0
                row += 1
        
        # ========== جزئیات ==========
        # Treeview برای نمایش جزئیات
        columns = ('نام محصول', 'قیمت خرید', 'قیمت فروش', 'تعداد', 'جمع خرید', 'جمع فروش', 'سود')
        tree = ttk.Treeview(details_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=100, anchor='center')
        
        for item in self.items:
            tree.insert('', 'end', values=(
                item['name'],
                f"{item['buy_price']:,.0f}",
                f"{item['sell_price']:,.0f}",
                item['quantity'],
                f"{item['total_buy']:,.0f}",
                f"{item['total_sell']:,.0f}",
                f"{item['profit']:,.0f}"
            ))
        
        scrollbar = ttk.Scrollbar(details_frame, orient=tk.VERTICAL, command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        
        tree.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        
        # ========== نمودار ==========
        # ایجاد نمودار دایره‌ای سود
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 5))
        fig.patch.set_facecolor('#f0f0f0')
        
        # نمودار دایره‌ای فروش
        names = [item['name'][:10] for item in self.items]
        sells = [item['total_sell'] for item in self.items]
        
        colors1 = plt.cm.Set3(np.linspace(0, 1, len(names)))
        ax1.pie(sells, labels=names, autopct='%1.1f%%', colors=colors1)
        ax1.set_title('توزیع فروش', fontsize=12, fontfamily='B Nazanin')
        
        # نمودار میله‌ای سود
        colors2 = ['green' if p > 0 else 'red' for p in profits]
        bars = ax2.bar(names, profits, color=colors2)
        ax2.set_title('سود هر محصول', fontsize=12, fontfamily='B Nazanin')
        ax2.tick_params(axis='x', rotation=45)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        
        plt.tight_layout()
        
        canvas = FigureCanvasTkAgg(fig, master=chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # دکمه بستن
        close_btn = tk.Button(report_window, text="❌ بستن",
                             bg=self.colors['danger'], fg='white',
                             font=self.font_normal,
                             command=report_window.destroy,
                             borderwidth=0, cursor='hand2', padx=20, pady=5)
        close_btn.pack(pady=10)
    
    def export_to_excel(self):
        """خروجی گرفتن به Excel"""
        if not self.items:
            messagebox.showwarning("⚠️ خطا", "داده‌ای برای خروجی وجود ندارد")
            return
        
        try:
            import pandas as pd
            
            # تبدیل به DataFrame
            df = pd.DataFrame(self.items)
            
            # انتخاب فایل
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                initialfile=f"sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            )
            
            if filename:
                df.to_excel(filename, index=False)
                messagebox.showinfo("✅ موفق", f"خروجی با موفقیت در {filename} ذخیره شد")
                self.status_label.config(text="📤 خروجی Excel گرفته شد")
                
        except ImportError:
            messagebox.showerror("❌ خطا", "لطفا کتابخانه pandas را نصب کنید:\npip install pandas openpyxl")
    
    def import_from_excel(self):
        """ورود از Excel"""
        try:
            import pandas as pd
            
            filename = filedialog.askopenfilename(
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
            )
            
            if filename:
                df = pd.read_excel(filename)
                
                # تبدیل به فرمت مورد نظر
                self.items = []
                for _, row in df.iterrows():
                    item = {
                        'code': str(row.get('code', '')),
                        'name': str(row.get('name', '')),
                        'category': str(row.get('category', 'سایر')),
                        'buy_price': float(row.get('buy_price', 0)),
                        'sell_price': float(row.get('sell_price', 0)),
                        'quantity': int(row.get('quantity', 1)),
                        'unit': str(row.get('unit', 'عدد')),
                        'description': str(row.get('description', '')),
                        'total_buy': float(row.get('buy_price', 0)) * int(row.get('quantity', 1)),
                        'total_sell': float(row.get('sell_price', 0)) * int(row.get('quantity', 1)),
                        'profit': (float(row.get('sell_price', 0)) - float(row.get('buy_price', 0))) * int(row.get('quantity', 1)),
                        'date': self.get_persian_date(),
                        'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    }
                    self.items.append(item)
                
                self.update_treeview()
                self.calculate_totals()
                messagebox.showinfo("✅ موفق", f"{len(self.items)} محصول با موفقیت وارد شد")
                self.status_label.config(text=f"📥 {len(self.items)} محصول وارد شد")
                
        except ImportError:
            messagebox.showerror("❌ خطا", "لطفا کتابخانه pandas را نصب کنید:\npip install pandas openpyxl")
        except Exception as e:
            messagebox.showerror("❌ خطا", f"خطا در ورود فایل: {str(e)}")
    
    def new_report(self):
        """شروع گزارش جدید"""
        if self.items:
            if messagebox.askyesno("🆕 شروع گزارش جدید", 
                                  "آیا می‌خواهید گزارش جدیدی شروع کنید؟ داده‌های فعلی پاک خواهند شد."):
                self.items = []
                self.update_treeview()
                self.calculate_totals()
                self.report_start_time = datetime.now()
                self.status_label.config(text="🆕 گزارش جدید شروع شد")
    
    def daily_report(self):
        self.generate_period_report('روزانه', 1)
    
    def weekly_report(self):
        self.generate_period_report('هفتگی', 7)
    
    def monthly_report(self):
        self.generate_period_report('ماهانه', 30)
    
    def generate_period_report(self, period_name, days):
        """تولید گزارش دوره‌ای"""
        report_window = tk.Toplevel(self.root)
        report_window.title(f"📅 گزارش {period_name}")
        report_window.geometry("800x600")
        report_window.configure(bg=self.colors['white'])
        
        # عنوان
        title = tk.Label(report_window, text=f"📅 گزارش {period_name}",
                        font=self.font_title, bg=self.colors['white'],
                        fg=self.colors['primary'])
        title.pack(pady=10)
        
        # محاسبه تاریخ
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # جمع‌آوری داده‌ها
        total_buy = 0
        total_sell = 0
        total_profit = 0
        transaction_count = 0
        
        for date, entries in self.saved_data.items():
            entry_date = datetime.strptime(date, '%Y-%m-%d')
            if entry_date >= start_date:
                for entry in entries:
                    total_buy += entry['total_buy']
                    total_sell += entry['total_sell']
                    total_profit += entry['total_profit']
                    transaction_count += entry['item_count']
        
        # نمایش گزارش
        report_frame = tk.Frame(report_window, bg=self.colors['white'])
        report_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        report_text = tk.Text(report_frame, font=("B Nazanin", 12), wrap=tk.WORD,
                             bg=self.colors['light'], relief=tk.FLAT)
        scrollbar = ttk.Scrollbar(report_frame, orient=tk.VERTICAL, command=report_text.yview)
        report_text.configure(yscrollcommand=scrollbar.set)
        
        report_text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        
        report = f"""
        ╔══════════════════════════════════════════════════════════╗
        ║                    📅 گزارش {period_name}                  ║
        ╠══════════════════════════════════════════════════════════╣
        ║                                                          ║
        ║   📅 از تاریخ: {start_date.strftime('%Y/%m/%d')}                              ║
        ║   📅 تا تاریخ: {end_date.strftime('%Y/%m/%d')}                               ║
        ║                                                          ║
        ╠══════════════════════════════════════════════════════════╣
        ║                    📊 آمار دوره                           ║
        ╠══════════════════════════════════════════════════════════╣
        ║                                                          ║
        ║   📦 تعداد تراکنش‌ها: {transaction_count}                                     ║
        ║   💰 جمع خرید: {total_buy:,.0f} ریال                         ║
        ║   💵 جمع فروش: {total_sell:,.0f} ریال                         ║
        ║   📈 سود خالص: {total_profit:,.0f} ریال                           ║
        ║                                                          ║
        ╚══════════════════════════════════════════════════════════╝
        """
        
        report_text.insert('1.0', report)
        report_text.config(state='disabled')
        
        # دکمه بستن
        close_btn = tk.Button(report_window, text="❌ بستن",
                             bg=self.colors['danger'], fg='white',
                             font=self.font_normal, command=report_window.destroy,
                             borderwidth=0, cursor='hand2', padx=20, pady=5)
        close_btn.pack(pady=10)
    
    def shop_info(self):
        """اطلاعات فروشگاه"""
        info_window = tk.Toplevel(self.root)
        info_window.title("🏪 اطلاعات فروشگاه")
        info_window.geometry("600x500")
        info_window.configure(bg=self.colors['white'])
        
        # عنوان
        title = tk.Label(info_window, text="🏪 اطلاعات فروشگاه",
                        font=self.font_title, bg=self.colors['white'],
                        fg=self.colors['primary'])
        title.pack(pady=20)
        
        # فرم اطلاعات
        form_frame = tk.Frame(info_window, bg=self.colors['white'])
        form_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=10)
        
        fields = [
            ("🏢 نام فروشگاه:", "فروشگاه آنلاین پیشرفته"),
            ("👤 مدیر فروشگاه:", "کاربر گرامی"),
            ("📞 تلفن:", "۰۲۱-۱۲۳۴۵۶۷۸"),
            ("📱 موبایل:", "۰۹۱۲-۳۴۵-۶۷۸۹"),
            ("📧 ایمیل:", "info@shop.ir"),
            ("🌐 وبسایت:", "www.shop.ir"),
            ("📍 آدرس:", "تهران - خیابان آزادی - پلاک ۱۲۳"),
            ("📮 کد پستی:", "۱۲۳۴۵۶۷۸۹۰"),
            ("🆔 کد اقتصادی:", "۱۲۳۴۵۶۷۸۹"),
        ]
        
        for i, (label, value) in enumerate(fields):
            row_frame = tk.Frame(form_frame, bg=self.colors['white'])
            row_frame.pack(fill=tk.X, pady=5)
            
            tk.Label(row_frame, text=label, font=self.font_normal,
                    bg=self.colors['white'], width=15, anchor='e').pack(side=tk.RIGHT)
            tk.Label(row_frame, text=value, font=self.font_normal,
                    bg=self.colors['white'], fg=self.colors['dark']).pack(side=tk.RIGHT, padx=5)
        
        # دکمه ویرایش
        edit_btn = tk.Button(info_window, text="✏️ ویرایش اطلاعات",
                            bg=self.colors['warning'], fg='black',
                            font=self.font_normal,
                            command=lambda: messagebox.showinfo("اطلاعات", "این بخش در حال توسعه است"),
                            borderwidth=0, cursor='hand2', padx=20, pady=5)
        edit_btn.pack(pady=10)
        
        # دکمه بستن
        close_btn = tk.Button(info_window, text="❌ بستن",
                             bg=self.colors['danger'], fg='white',
                             font=self.font_normal, command=info_window.destroy,
                             borderwidth=0, cursor='hand2', padx=20, pady=5)
        close_btn.pack(pady=10)
    
    def backup_data(self):
        """پشتیبان گیری از داده‌ها"""
        if messagebox.askyesno("💾 پشتیبان گیری", "آیا می‌خواهید از داده‌ها پشتیبان بگیرید؟"):
            try:
                # ایجاد نام فایل با تاریخ
                backup_name = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                
                # کپی فایل داده
                if os.path.exists('sales_data.json'):
                    import shutil
                    shutil.copy2('sales_data.json', backup_name)
                    messagebox.showinfo("✅ موفق", f"پشتیبان با نام {backup_name} ایجاد شد")
                    self.status_label.config(text=f"💾 پشتیبان {backup_name} ایجاد شد")
                else:
                    # ایجاد فایل پشتیبان از داده‌های فعلی
                    with open(backup_name, 'w', encoding='utf-8') as f:
                        json.dump(self.saved_data, f, ensure_ascii=False, indent=2)
                    messagebox.showinfo("✅ موفق", f"پشتیبان با نام {backup_name} ایجاد شد")
                    
            except Exception as e:
                messagebox.showerror("❌ خطا", f"خطا در پشتیبان گیری: {str(e)}")
    
    def restore_data(self):
        """بازیابی اطلاعات از پشتیبان"""
        filename = filedialog.askopenfilename(
            title="انتخاب فایل پشتیبان",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                if messagebox.askyesno("🔄 بازیابی", 
                                      "آیا می‌خواهید داده‌های فعلی با داده‌های پشتیبان جایگزین شوند؟"):
                    self.saved_data = data
                    
                    # ذخیره در فایل اصلی
                    with open('sales_data.json', 'w', encoding='utf-8') as f:
                        json.dump(self.saved_data, f, ensure_ascii=False, indent=2)
                    
                    messagebox.showinfo("✅ موفق", "داده‌ها با موفقیت بازیابی شدند")
                    self.status_label.config(text="🔄 داده‌ها بازیابی شدند")
                    
            except Exception as e:
                messagebox.showerror("❌ خطا", f"خطا در بازیابی: {str(e)}")
    
    def toggle_theme(self):
        """تغییر تم برنامه"""
        if self.current_theme == 'light':
            # تم تیره
            self.root.configure(bg='#2C3E50')
            self.colors = {
                'primary': '#3498DB',
                'success': '#2ECC71',
                'danger': '#E74C3C',
                'warning': '#F1C40F',
                'info': '#1ABC9C',
                'dark': '#2C3E50',
                'light': '#34495E',
                'white': '#ECF0F1',
                'gold': '#F39C12',
            }
            self.current_theme = 'dark'
        else:
            # تم روشن
            self.root.configure(bg='SystemButtonFace')
            self.colors = {
                'primary': '#2196F3',
                'success': '#4CAF50',
                'danger': '#F44336',
                'warning': '#FFC107',
                'info': '#00BCD4',
                'dark': '#2C3E50',
                'light': '#F5F5F5',
                'white': '#FFFFFF',
                'gold': '#FFD700',
            }
            self.current_theme = 'light'
        
        self.status_label.config(text="🎨 تم تغییر کرد")
    
    def show_settings(self):
        """نمایش تنظیمات"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("⚙️ تنظیمات")
        settings_window.geometry("500x400")
        settings_window.configure(bg=self.colors['white'])
        
        # عنوان
        title = tk.Label(settings_window, text="⚙️ تنظیمات برنامه",
                        font=self.font_title, bg=self.colors['white'],
                        fg=self.colors['primary'])
        title.pack(pady=20)
        
        # گزینه‌های تنظیمات
        settings_frame = tk.Frame(settings_window, bg=self.colors['white'])
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=40, pady=10)
        
        # نمایش اعداد با جداکننده
        self.separator_var = tk.BooleanVar(value=True)
        tk.Checkbutton(settings_frame, text="نمایش اعداد با جداکننده هزارگان",
                      variable=self.separator_var,
                      bg=self.colors['white'], font=self.font_normal).pack(anchor='w', pady=5)
        
        # ذخیره خودکار
        self.auto_save_var = tk.BooleanVar(value=False)
        tk.Checkbutton(settings_frame, text="ذخیره خودکار هر ۵ دقیقه",
                      variable=self.auto_save_var,
                      bg=self.colors['white'], font=self.font_normal).pack(anchor='w', pady=5)
        
        # تم
        tk.Label(settings_frame, text="تم برنامه:", font=self.font_normal,
                bg=self.colors['white']).pack(anchor='w', pady=5)
        
        theme_frame = tk.Frame(settings_frame, bg=self.colors['white'])
        theme_frame.pack(anchor='w', pady=5)
        
        tk.Button(theme_frame, text="🌞 روشن", bg=self.colors['primary'],
                 fg='white', font=self.font_small,
                 command=lambda: self.change_theme('light'),
                 borderwidth=0, cursor='hand2', padx=10).pack(side=tk.RIGHT, padx=2)
        
        tk.Button(theme_frame, text="🌙 تیره", bg=self.colors['dark'],
                 fg='white', font=self.font_small,
                 command=lambda: self.change_theme('dark'),
                 borderwidth=0, cursor='hand2', padx=10).pack(side=tk.RIGHT, padx=2)
        
        # دکمه ذخیره
        save_btn = tk.Button(settings_window, text="💾 ذخیره تنظیمات",
                            bg=self.colors['success'], fg='white',
                            font=self.font_normal,
                            command=lambda: messagebox.showinfo("✅ موفق", "تنظیمات ذخیره شد"),
                            borderwidth=0, cursor='hand2', padx=20, pady=5)
        save_btn.pack(pady=10)
    
    def change_theme(self, theme):
        """تغییر تم"""
        if theme == 'dark' and self.current_theme != 'dark':
            self.toggle_theme()
        elif theme == 'light' and self.current_theme != 'light':
            self.toggle_theme()
    
    def show_help(self):
        """نمایش راهنما"""
        help_window = tk.Toplevel(self.root)
        help_window.title("📖 راهنمای استفاده")
        help_window.geometry("600x500")
        help_window.configure(bg=self.colors['white'])
        
        # عنوان
        title = tk.Label(help_window, text="📖 راهنمای استفاده از برنامه",
                        font=self.font_title, bg=self.colors['white'],
                        fg=self.colors['primary'])
        title.pack(pady=20)
        
        # متن راهنما
        help_frame = tk.Frame(help_window, bg=self.colors['white'])
        help_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        help_text = tk.Text(help_frame, font=("B Nazanin", 11), wrap=tk.WORD,
                           bg=self.colors['light'], relief=tk.FLAT)
        scrollbar = ttk.Scrollbar(help_frame, orient=tk.VERTICAL, command=help_text.yview)
        help_text.configure(yscrollcommand=scrollbar.set)
        
        help_text.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        
        help_content = """
        🌟 راهنمای استفاده از سیستم مدیریت خرید و فروش 🌟
        
        ════════════════════════════════════════
        
        🔹 افزودن محصول:
           - کد، نام، قیمت و تعداد را وارد کنید
           - روی دکمه "افزودن به لیست" کلیک کنید
        
        🔹 ویرایش محصول:
           - روی محصول در لیست کلیک کنید
           - اطلاعات را تغییر دهید
           - روی دکمه "ویرایش محصول" کلیک کنید
        
        🔹 حذف محصول:
           - محصول مورد نظر را انتخاب کنید
           - روی دکمه "حذف از لیست" کلیک کنید
        
        🔹 ذخیره داده‌ها:
           - برای ذخیره داده‌های روز جاری
           - روی دکمه "ذخیره داده‌ها" کلیک کنید
        
        🔹 مشاهده داده‌های قبلی:
           - روی دکمه "داده‌های ذخیره شده" کلیک کنید
           - تاریخ مورد نظر را انتخاب کنید
        
        🔹 گزارشات:
           - از منوی "گزارشات" می‌توانید انواع گزارش را مشاهده کنید
           - گزارش روزانه، هفتگی، ماهانه و سود و زیان
        
        🔹 چاپ رسید:
           - پس از ثبت محصولات
           - روی دکمه "چاپ رسید" کلیک کنید
        
        🔹 کلیدهای میانبر:
           - Ctrl+N: گزارش جدید
           - Ctrl+S: ذخیره داده‌ها
        
        برای اطلاعات بیشتر با پشتیبانی تماس بگیرید.
        """
        
        help_text.insert('1.0', help_content)
        help_text.config(state='disabled')
        
        # دکمه بستن
        close_btn = tk.Button(help_window, text="❌ بستن",
                             bg=self.colors['danger'], fg='white',
                             font=self.font_normal, command=help_window.destroy,
                             borderwidth=0, cursor='hand2', padx=20, pady=5)
        close_btn.pack(pady=10)
    
    def show_about(self):
        """نمایش درباره برنامه"""
        about_window = tk.Toplevel(self.root)
        about_window.title("ℹ️ درباره برنامه")
        about_window.geometry("400x300")
        about_window.configure(bg=self.colors['white'])
        
        about_text = f"""
        ╔══════════════════════════════╗
        ║    🌟 سیستم مدیریت فروش 🌟    ║
        ╠══════════════════════════════╣
        ║                              ║
        ║   نسخه: ۲.۰ پیشرفته           ║
        ║   تاریخ: {self.get_persian_date()}   ║
        ║                              ║
        ║   توسعه داده شده با ❤️         ║
        ║   برای کسب و کارهای ایرانی     ║
        ║                              ║
        ║   کلیه حقوق محفوظ است         ║
        ║   © ۲۰۲۴                     ║
        ║                              ║
        ╚══════════════════════════════╝
        """
        
        label = tk.Label(about_window, text=about_text,
                        font=("B Nazanin", 12), bg=self.colors['white'],
                        justify=tk.CENTER)
        label.pack(expand=True)
        
        # دکمه بستن
        close_btn = tk.Button(about_window, text="❌ بستن",
                             bg=self.colors['danger'], fg='white',
                             font=self.font_normal, command=about_window.destroy,
                             borderwidth=0, cursor='hand2', padx=20, pady=5)
        close_btn.pack(pady=10)

# ==================== اجرای برنامه ====================
def main():
    root = tk.Tk()
    
    # تنظیم آیکون (اختیاری)
    try:
        root.iconbitmap(default='icon.ico')
    except:
        pass
    
    # تنظیم اندازه پنجره
    root.geometry("1400x750")
    
    # مرکزیت پنجره
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    # اجرای برنامه
    app = AdvancedSalesManagementSystem(root) # ← Fixed: added indentation
    
    # نمایش پیام خوش آمدگویی
    # نمایش پیام خوش آمدگویی
    messagebox.showinfo("🎉 خوش آمدید", 
                       "به سیستم مدیریت خرید و فروش پیشرفته خوش آمدید\n"
                       "برای راهنمایی بیشتر به منوی راهنما مراجعه کنید")
    
    root.mainloop()

if __name__ == "__main__":
    main()