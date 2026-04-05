import subprocess
import sys

def install_package(package):
    """Автоматическая установка библиотеки, если её нет"""
    try:
        __import__(package)
        print(f"✅ {package} уже установлена")
    except ImportError:
        print(f"📦 Устанавливаю {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ {package} установлена!")

# Автоматическая установка всех нужных библиотек
install_package("requests")
install_package("pyinstaller")

print("✅ Все библиотеки проверены! Запускаю приложение...")
print("")
import subprocess
import sys

def install_package(package):
    """Автоматическая установка библиотеки, если её нет"""
    try:
        __import__(package)
    except ImportError:
        print(f"📦 Библиотека {package} не найдена. Устанавливаю...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Библиотека {package} установлена!")

# Проверяем и устанавливаем нужные библиотеки
install_package("requests")
import json
import os
import threading
import time
import logging
from datetime import datetime
from tkinter import *
from tkinter import ttk, messagebox, scrolledtext
import tkinter.font as tkFont
import requests

DATA_FILE = "funpay_data.json"
LOG_FILE = "funpay_history.log"


class FunPayApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FunPay Manager — Автовыдача PRO")
        self.root.geometry("1300x800")
        self.root.minsize(1000, 600)

        self.golden_key = ""
        self.session = None
        self.lots = []
        self.history = []
        self.auto_delivery_rules = {}
        self.auto_reply_review = True
        self.notifications_enabled = True
        self.monitoring_active = False
        self.monitor_thread = None

        self.load_data()

        self.setup_styles()
        self.create_widgets()

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s',
                            handlers=[logging.FileHandler(LOG_FILE, encoding='utf-8'),
                                      logging.StreamHandler()])
        self.log("Приложение запущено")

    def setup_styles(self):
        self.bg_dark = "#0a192f"
        self.bg_medium = "#112440"
        self.bg_light = "#233554"
        self.accent = "#64ffda"
        self.text_light = "#ccd6f6"
        self.text_gray = "#8892b0"
        self.error_color = "#ff6b6b"
        self.success_color = "#6bff6b"

        self.root.configure(bg=self.bg_dark)
        self.title_font = tkFont.Font(family="Segoe UI", size=14, weight="bold")
        self.normal_font = tkFont.Font(family="Segoe UI", size=10)

    def create_widgets(self):
        self.create_top_panel()
        self.create_tab_control()
        self.create_status_bar()

    def create_top_panel(self):
        top_frame = Frame(self.root, bg=self.bg_medium, height=80)
        top_frame.pack(fill=X, padx=10, pady=5)
        top_frame.pack_propagate(False)

        title = Label(top_frame, text="FunPay Manager PRO", font=self.title_font,
                      bg=self.bg_medium, fg=self.accent)
        title.pack(side=LEFT, padx=20, pady=20)

        key_label = Label(top_frame, text="Golden Key:", bg=self.bg_medium, fg=self.text_light, font=self.normal_font)
        key_label.pack(side=LEFT, padx=(50, 5), pady=20)

        self.key_entry = Entry(top_frame, width=40, bg=self.bg_light, fg=self.text_light,
                               insertbackground=self.text_light, font=self.normal_font)
        self.key_entry.pack(side=LEFT, padx=5, pady=20)
        self.key_entry.insert(0, self.golden_key)

        self.connect_btn = Button(top_frame, text="🔌 Подключиться", command=self.connect_funpay,
                                  bg=self.accent, fg=self.bg_dark, font=self.normal_font,
                                  activebackground="#4ecdc4", cursor="hand2")
        self.connect_btn.pack(side=LEFT, padx=10, pady=20)

        self.status_indicator = Label(top_frame, text="⚫ Не подключён", bg=self.bg_medium,
                                      fg=self.text_gray, font=self.normal_font)
        self.status_indicator.pack(side=LEFT, padx=20, pady=20)

        notify_btn = Button(top_frame, text="🔔 Уведомления", command=self.toggle_notifications,
                            bg=self.bg_light, fg=self.text_light, font=self.normal_font,
                            activebackground=self.bg_medium, cursor="hand2")
        notify_btn.pack(side=RIGHT, padx=10, pady=20)

        save_btn = Button(top_frame, text="💾 Сохранить всё", command=self.save_data,
                          bg=self.bg_light, fg=self.text_light, font=self.normal_font,
                          activebackground=self.bg_medium, cursor="hand2")
        save_btn.pack(side=RIGHT, padx=10, pady=20)

    def create_tab_control(self):
        self.tab_control = ttk.Notebook(self.root)
        self.tab_control.pack(fill=BOTH, expand=True, padx=10, pady=5)

        style = ttk.Style()
        style.configure("TNotebook", background=self.bg_dark)
        style.configure("TNotebook.Tab", background=self.bg_medium, foreground=self.text_light,
                        padding=[10, 5], font=self.normal_font)
        style.map("TNotebook.Tab", background=[("selected", self.accent), ("active", self.bg_light)])

        self.tab_auto = Frame(self.tab_control, bg=self.bg_dark)
        self.tab_control.add(self.tab_auto, text="🚀 Автовыдача")
        self.create_auto_tab()

        self.tab_lots = Frame(self.tab_control, bg=self.bg_dark)
        self.tab_control.add(self.tab_lots, text="📦 Мои лоты")
        self.create_lots_tab()

        self.tab_history = Frame(self.tab_control, bg=self.bg_dark)
        self.tab_control.add(self.tab_history, text="📜 История выдачи")
        self.create_history_tab()

        self.tab_settings = Frame(self.tab_control, bg=self.bg_dark)
        self.tab_control.add(self.tab_settings, text="⚙️ Настройки")
        self.create_settings_tab()

    def create_auto_tab(self):
        left_frame = Frame(self.tab_auto, bg=self.bg_dark)
        left_frame.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)

        Label(left_frame, text="📋 Правила автовыдачи", font=self.title_font,
              bg=self.bg_dark, fg=self.accent).pack(anchor=W, pady=5)

        rules_frame = Frame(left_frame, bg=self.bg_medium)
        rules_frame.pack(fill=BOTH, expand=True, pady=5)

        scroll_rules = Scrollbar(rules_frame)
        scroll_rules.pack(side=RIGHT, fill=Y)

        self.rules_listbox = Listbox(rules_frame, bg=self.bg_light, fg=self.text_light,
                                     selectbackground=self.accent, selectforeground=self.bg_dark,
                                     yscrollcommand=scroll_rules.set, font=self.normal_font,
                                     height=15)
        self.rules_listbox.pack(fill=BOTH, expand=True)
        scroll_rules.config(command=self.rules_listbox.yview)

        btn_frame = Frame(left_frame, bg=self.bg_dark)
        btn_frame.pack(fill=X, pady=5)

        Button(btn_frame, text="➕ Добавить правило", command=self.add_rule,
               bg=self.accent, fg=self.bg_dark, font=self.normal_font, cursor="hand2").pack(side=LEFT, padx=2)
        Button(btn_frame, text="✏️ Редактировать", command=self.edit_rule,
               bg=self.bg_light, fg=self.text_light, font=self.normal_font, cursor="hand2").pack(side=LEFT, padx=2)
        Button(btn_frame, text="🗑 Удалить", command=self.delete_rule,
               bg=self.error_color, fg=self.bg_dark, font=self.normal_font, cursor="hand2").pack(side=LEFT, padx=2)

        right_frame = Frame(self.tab_auto, bg=self.bg_medium, width=400)
        right_frame.pack(side=RIGHT, fill=Y, padx=5, pady=5)
        right_frame.pack_propagate(False)

        Label(right_frame, text="✏️ Редактор правила", font=self.title_font,
              bg=self.bg_medium, fg=self.accent).pack(pady=10)

        Label(right_frame, text="Название лота (точное совпадение):", bg=self.bg_medium, fg=self.text_light).pack(anchor=W, padx=10)
        self.rule_lot_name = Entry(right_frame, width=40, bg=self.bg_light, fg=self.text_light, insertbackground=self.text_light)
        self.rule_lot_name.pack(padx=10, pady=5, fill=X)

        Label(right_frame, text="Текст для выдачи клиенту:", bg=self.bg_medium, fg=self.text_light).pack(anchor=W, padx=10)
        self.rule_delivery_text = scrolledtext.ScrolledText(right_frame, height=10, width=40,
                                                            bg=self.bg_light, fg=self.text_light,
                                                            insertbackground=self.text_light)
        self.rule_delivery_text.pack(padx=10, pady=5, fill=BOTH, expand=True)

        Button(right_frame, text="💾 Сохранить правило", command=self.save_current_rule,
               bg=self.accent, fg=self.bg_dark, font=self.normal_font, cursor="hand2").pack(pady=10)

        self.update_rules_list()

    def create_lots_tab(self):
        control_frame = Frame(self.tab_lots, bg=self.bg_medium)
        control_frame.pack(fill=X, padx=5, pady=5)

        Button(control_frame, text="🔄 Загрузить лоты", command=self.load_lots_from_funpay,
               bg=self.accent, fg=self.bg_dark, font=self.normal_font, cursor="hand2").pack(side=LEFT, padx=5, pady=5)
        Button(control_frame, text="🗑 Очистить список", command=self.clear_lots,
               bg=self.error_color, fg=self.bg_dark, font=self.normal_font, cursor="hand2").pack(side=LEFT, padx=5, pady=5)

        columns = ("ID", "Название", "Цена", "Остаток", "Статус")
        self.lots_tree = ttk.Treeview(self.tab_lots, columns=columns, show="headings", height=20)

        for col in columns:
            self.lots_tree.heading(col, text=col)
            self.lots_tree.column(col, width=150)

        self.lots_tree.pack(fill=BOTH, expand=True, padx=5, pady=5)

        scroll_lots = Scrollbar(self.tab_lots, orient=VERTICAL, command=self.lots_tree.yview)
        self.lots_tree.configure(yscrollcommand=scroll_lots.set)
        scroll_lots.pack(side=RIGHT, fill=Y)

    def create_history_tab(self):
        hist_control = Frame(self.tab_history, bg=self.bg_medium)
        hist_control.pack(fill=X, padx=5, pady=5)

        Button(hist_control, text="🗑 Очистить историю", command=self.clear_history,
               bg=self.error_color, fg=self.bg_dark, font=self.normal_font, cursor="hand2").pack(side=LEFT, padx=5, pady=5)
        Button(hist_control, text="📋 Экспорт в JSON", command=self.export_history_json,
               bg=self.bg_light, fg=self.text_light, font=self.normal_font, cursor="hand2").pack(side=LEFT, padx=5, pady=5)

        self.history_text = scrolledtext.ScrolledText(self.tab_history, wrap=WORD,
                                                      bg=self.bg_light, fg=self.text_light,
                                                      insertbackground=self.text_light,
                                                      font=self.normal_font)
        self.history_text.pack(fill=BOTH, expand=True, padx=5, pady=5)

        self.refresh_history_display()

    def create_settings_tab(self):
        general_frame = LabelFrame(self.tab_settings, text="Общие настройки", bg=self.bg_medium,
                                   fg=self.accent, font=self.title_font)
        general_frame.pack(fill=X, padx=10, pady=10, ipady=5)

        self.auto_confirm_var = BooleanVar(value=True)
        Checkbutton(general_frame, text="Автоматически подтверждать заказы после выдачи",
                    variable=self.auto_confirm_var, bg=self.bg_medium, fg=self.text_light,
                    selectcolor=self.bg_medium).pack(anchor=W, padx=10, pady=5)

        self.ask_review_var = BooleanVar(value=self.auto_reply_review)
        Checkbutton(general_frame, text="Просить клиента оставить отзыв после покупки",
                    variable=self.ask_review_var, bg=self.bg_medium, fg=self.text_light,
                    selectcolor=self.bg_medium, command=self.toggle_review_setting).pack(anchor=W, padx=10, pady=5)

        Label(general_frame, text="Текст запроса отзыва:", bg=self.bg_medium, fg=self.text_light).pack(anchor=W, padx=10)
        self.review_text = scrolledtext.ScrolledText(general_frame, height=4, width=70,
                                                     bg=self.bg_light, fg=self.text_light,
                                                     insertbackground=self.text_light)
        self.review_text.pack(padx=10, pady=5, fill=X)
        self.review_text.insert("1.0", "Спасибо за покупку! Если вам всё понравилось, пожалуйста, оставьте отзыв о продавце. Это очень поможет развитию сервиса!")

        monitor_frame = LabelFrame(self.tab_settings, text="Мониторинг заказов", bg=self.bg_medium,
                                   fg=self.accent, font=self.title_font)
        monitor_frame.pack(fill=X, padx=10, pady=10, ipady=5)

        Label(monitor_frame, text="Интервал проверки (секунд):", bg=self.bg_medium, fg=self.text_light).pack(anchor=W, padx=10)
        self.monitor_interval = Entry(monitor_frame, width=10, bg=self.bg_light, fg=self.text_light)
        self.monitor_interval.insert(0, "15")
        self.monitor_interval.pack(anchor=W, padx=10, pady=5)

        Button(monitor_frame, text="Применить интервал", command=self.update_monitor_interval,
               bg=self.accent, fg=self.bg_dark, cursor="hand2").pack(anchor=W, padx=10, pady=5)

        data_frame = LabelFrame(self.tab_settings, text="Управление данными", bg=self.bg_medium,
                                fg=self.accent, font=self.title_font)
        data_frame.pack(fill=X, padx=10, pady=10, ipady=5)

        Button(data_frame, text="💾 Сохранить данные", command=self.save_data,
               bg=self.bg_light, fg=self.text_light, cursor="hand2").pack(side=LEFT, padx=10, pady=5)
        Button(data_frame, text="⚠️ Сбросить все данные", command=self.reset_all_data,
               bg=self.error_color, fg=self.bg_dark, cursor="hand2").pack(side=LEFT, padx=10, pady=5)

    def create_status_bar(self):
        self.status_bar = Frame(self.root, bg=self.bg_medium, height=30)
        self.status_bar.pack(fill=X, side=BOTTOM)

        self.status_label = Label(self.status_bar, text="Готов к работе", bg=self.bg_medium, fg=self.text_gray, font=self.normal_font)
        self.status_label.pack(side=LEFT, padx=10)

        self.time_label = Label(self.status_bar, text="", bg=self.bg_medium, fg=self.text_gray, font=self.normal_font)
        self.time_label.pack(side=RIGHT, padx=10)
        self.update_clock()

    def connect_funpay(self):
        self.golden_key = self.key_entry.get().strip()
        if not self.golden_key:
            messagebox.showerror("Ошибка", "Введите Golden Key")
            return

        try:
            self.session = requests.Session()
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json, text/plain, */*',
                'Authorization': f'Bearer {self.golden_key}',
            })

            response = self.session.get('https://funpay.com/api/account/', timeout=10)

            if response.status_code == 200:
                data = response.json()
                self.status_indicator.config(text="🟢 Подключён", fg=self.success_color)
                self.log(f"Успешно подключён. Аккаунт: {data.get('username', 'N/A')}")
                self.start_monitoring()
                messagebox.showinfo("Успех", f"Подключение выполнено!\nАккаунт: {data.get('username', 'N/A')}")
            else:
                self.status_indicator.config(text="🔴 Ошибка авторизации", fg=self.error_color)
                self.log(f"Ошибка подключения: статус {response.status_code}")
                messagebox.showerror("Ошибка", "Неверный Golden Key")
        except Exception as e:
            self.status_indicator.config(text="🔴 Ошибка", fg=self.error_color)
            self.log(f"Ошибка: {e}")
            messagebox.showerror("Ошибка", str(e))

    def load_lots_from_funpay(self):
        if not self.session:
            messagebox.showwarning("Предупреждение", "Сначала подключитесь")
            return

        try:
            response = self.session.get('https://funpay.com/api/lots/')
            if response.status_code == 200:
                data = response.json()
                self.lots = []
                if 'lots' in data:
                    for lot in data['lots']:
                        self.lots.append({
                            "id": lot.get('id'),
                            "name": lot.get('name'),
                            "price": lot.get('price'),
                            "stock": lot.get('stock', 0),
                            "status": "Активен" if lot.get('active') else "Неактивен"
                        })
                self.update_lots_display()
                self.log(f"Загружено {len(self.lots)} лотов")
                messagebox.showinfo("Успех", f"Загружено {len(self.lots)} лотов")
        except Exception as e:
            self.log(f"Ошибка: {e}")

    def update_lots_display(self):
        for row in self.lots_tree.get_children():
            self.lots_tree.delete(row)
        for lot in self.lots:
            self.lots_tree.insert("", END, values=(
                lot.get("id", ""), lot.get("name", ""), lot.get("price", ""),
                lot.get("stock", ""), lot.get("status", "")
            ))

    def get_orders(self):
        if not self.session:
            return []
        try:
            response = self.session.get('https://funpay.com/api/orders/')
            if response.status_code == 200:
                data = response.json()
                return data.get('orders', [])
        except Exception as e:
            self.log(f"Ошибка получения заказов: {e}")
        return []

    def send_message_to_chat(self, chat_id, message):
        if not self.session:
            return False
        try:
            response = self.session.post('https://funpay.com/api/chat/send/', json={
                'chat_id': chat_id,
                'message': message
            })
            return response.status_code == 200
        except Exception as e:
            self.log(f"Ошибка отправки: {e}")
            return False

    def confirm_order(self, order_id):
        if not self.session:
            return False
        try:
            response = self.session.post(f'https://funpay.com/api/order/{order_id}/confirm/')
            return response.status_code == 200
        except Exception:
            return False

    def auto_deliver(self, order):
        lot_name = order.get('lot_name', '')
        for rule_lot_name, delivery_text in self.auto_delivery_rules.items():
            if rule_lot_name.lower() in lot_name.lower() or lot_name.lower() in rule_lot_name.lower():
                chat_id = order.get('chat_id')
                if chat_id:
                    success = self.send_message_to_chat(chat_id, delivery_text)
                    if success:
                        history_entry = {
                            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "lot": lot_name,
                            "order_id": order.get('id'),
                            "delivered": delivery_text[:100],
                            "status": "Успешно"
                        }
                        self.history.append(history_entry)
                        self.save_history()
                        self.refresh_history_display()
                        self.log(f"✅ Автовыдача для '{lot_name}'")

                        if self.ask_review_var.get():
                            review_msg = self.review_text.get("1.0", END).strip()
                            self.send_message_to_chat(chat_id, review_msg)
                            self.log(f"📝 Запрос отзыва отправлен")

                        if self.auto_confirm_var.get():
                            self.confirm_order(order.get('id'))
                        return True
        return False

    def monitor_orders(self):
        processed_orders = set()
        for entry in self.history:
            if 'order_id' in entry:
                processed_orders.add(entry['order_id'])

        while self.monitoring_active:
            try:
                orders = self.get_orders()
                for order in orders:
                    order_id = order.get('id')
                    if order_id in processed_orders:
                        continue
                    status = order.get('status', '')
                    if 'waiting' in status.lower() or 'pending' in status.lower():
                        self.log(f"🆕 Новый заказ: {order.get('lot_name')}")
                        if self.auto_deliver(order):
                            processed_orders.add(order_id)
                time.sleep(int(self.monitor_interval.get()))
            except Exception as e:
                self.log(f"Ошибка мониторинга: {e}")
                time.sleep(30)

    def start_monitoring(self):
        if self.monitoring_active:
            return
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self.monitor_orders, daemon=True)
        self.monitor_thread.start()
        self.log("🟢 Мониторинг запущен")

    def stop_monitoring(self):
        self.monitoring_active = False
        self.log("🔴 Мониторинг остановлен")

    def update_rules_list(self):
        self.rules_listbox.delete(0, END)
        for lot_name, delivery_text in self.auto_delivery_rules.items():
            self.rules_listbox.insert(END, f"{lot_name} → {delivery_text[:30]}...")

    def add_rule(self):
        self.rule_lot_name.delete(0, END)
        self.rule_delivery_text.delete("1.0", END)
        self.current_edit_rule = None

    def edit_rule(self):
        selection = self.rules_listbox.curselection()
        if not selection:
            messagebox.showwarning("Предупреждение", "Выберите правило")
            return
        rule_text = self.rules_listbox.get(selection[0])
        lot_name = rule_text.split(" → ")[0]
        delivery_text = self.auto_delivery_rules.get(lot_name, "")
        self.rule_lot_name.delete(0, END)
        self.rule_lot_name.insert(0, lot_name)
        self.rule_delivery_text.delete("1.0", END)
        self.rule_delivery_text.insert("1.0", delivery_text)
        self.current_edit_rule = lot_name

    def delete_rule(self):
        selection = self.rules_listbox.curselection()
        if not selection:
            return
        rule_text = self.rules_listbox.get(selection[0])
        lot_name = rule_text.split(" → ")[0]
        if lot_name in self.auto_delivery_rules:
            del self.auto_delivery_rules[lot_name]
            self.update_rules_list()
            self.log(f"Правило удалено: {lot_name}")

    def save_current_rule(self):
        lot_name = self.rule_lot_name.get().strip()
        delivery_text = self.rule_delivery_text.get("1.0", END).strip()
        if not lot_name or not delivery_text:
            messagebox.showwarning("Ошибка", "Заполните все поля")
            return
        self.auto_delivery_rules[lot_name] = delivery_text
        self.update_rules_list()
        self.log(f"Правило сохранено: {lot_name}")
        messagebox.showinfo("Успех", "Правило сохранено!")

    def refresh_history_display(self):
        self.history_text.delete("1.0", END)
        for entry in reversed(self.history[-100:]):
            self.history_text.insert(END, f"[{entry['time']}] {entry['lot']}\n")
            self.history_text.insert(END, f"   Выдано: {entry['delivered']}\n\n")

    def clear_history(self):
        if messagebox.askyesno("Подтверждение", "Очистить историю?"):
            self.history = []
            self.save_history()
            self.refresh_history_display()
            self.log("История очищена")

    def export_history_json(self):
        try:
            with open("history_export.json", "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
            messagebox.showinfo("Успех", "Экспорт завершён")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def save_data(self):
        data = {
            "golden_key": self.golden_key,
            "auto_delivery_rules": self.auto_delivery_rules,
            "history": self.history,
            "ask_review": self.ask_review_var.get(),
            "review_text": self.review_text.get("1.0", END).strip()
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.log("Данные сохранены")
        messagebox.showinfo("Успех", "Данные сохранены!")

    def load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.golden_key = data.get("golden_key", "")
                self.auto_delivery_rules = data.get("auto_delivery_rules", {})
                self.history = data.get("history", [])
                self.auto_reply_review = data.get("ask_review", True)
                review_text = data.get("review_text", "")
                if hasattr(self, "review_text") and review_text:
                    self.review_text.delete("1.0", END)
                    self.review_text.insert("1.0", review_text)
            except Exception as e:
                print(f"Ошибка загрузки: {e}")

    def save_history(self):
        data = {
            "golden_key": self.golden_key,
            "auto_delivery_rules": self.auto_delivery_rules,
            "history": self.history,
            "ask_review": self.ask_review_var.get(),
            "review_text": self.review_text.get("1.0", END).strip()
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def reset_all_data(self):
        if messagebox.askyesno("⚠️ ВНИМАНИЕ", "Сбросить все данные?"):
            self.auto_delivery_rules = {}
            self.history = []
            self.golden_key = ""
            self.key_entry.delete(0, END)
            self.update_rules_list()
            self.refresh_history_display()
            self.save_data()
            self.log("Все данные сброшены")
            messagebox.showinfo("Готово", "Данные сброшены")

    def clear_lots(self):
        if messagebox.askyesno("Подтверждение", "Очистить список лотов?"):
            self.lots = []
            self.update_lots_display()
            self.log("Список лотов очищен")

    def toggle_notifications(self):
        self.notifications_enabled = not self.notifications_enabled
        self.log(f"Уведомления {'включены' if self.notifications_enabled else 'выключены'}")

    def toggle_review_setting(self):
        self.auto_reply_review = self.ask_review_var.get()
        self.log(f"Запрос отзыва {'включён' if self.auto_reply_review else 'выключён'}")

    def update_monitor_interval(self):
        try:
            val = int(self.monitor_interval.get())
            if val < 5:
                messagebox.showwarning("Предупреждение", "Интервал не может быть меньше 5 секунд")
                self.monitor_interval.delete(0, END)
                self.monitor_interval.insert(0, "5")
            self.log(f"Интервал мониторинга: {val} сек")
        except ValueError:
            messagebox.showerror("Ошибка", "Введите число")

    def log(self, message):
        logging.info(message)
        self.status_label.config(text=f"📌 {message[:60]}")
        print(f"[LOG] {message}")

    def update_clock(self):
        self.time_label.config(text=datetime.now().strftime("%H:%M:%S"))
        self.root.after(1000, self.update_clock)


if __name__ == "__main__":
    root = Tk()
    app = FunPayApp(root)
    root.mainloop()